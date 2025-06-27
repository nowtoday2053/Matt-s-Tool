from flask import Flask, render_template, request, jsonify, send_file, Response
import os
from validator import PhoneValidator
import logging
from werkzeug.utils import secure_filename
import json
import queue
import threading
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('results', exist_ok=True)

# Create a validator instance
validator = PhoneValidator()

# Queue for real-time results
results_queues = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    try:
        phone = request.form.get('phone')
        if not phone:
            return jsonify({'error': 'No phone number provided'}), 400

        result = validator.validate_single_number(phone)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in validation: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_file(file_path, phone_column, session_id):
    try:
        def result_callback(result):
            # Put each result in the queue
            if session_id in results_queues:
                results_queues[session_id].put(result)

        # Process the file with callback
        output_path = validator.validate_file(file_path, phone_column, result_callback)
        
        # Signal completion
        if session_id in results_queues:
            results_queues[session_id].put({
                'status': 'complete',
                'output_file': os.path.basename(output_path)
            })
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        if session_id in results_queues:
            results_queues[session_id].put({
                'status': 'error',
                'error': str(e)
            })
    finally:
        # Clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/validate-file', methods=['POST'])
def validate_file():
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload a CSV or Excel file'}), 400

        # Generate a unique session ID
        session_id = str(hash(file.filename + str(time.time())))
        
        # Create a new queue for this session
        results_queues[session_id] = queue.Queue()

        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Get the phone column name if specified
        phone_column = request.form.get('phone_column')
        
        # Start processing in a separate thread
        thread = threading.Thread(
            target=process_file,
            args=(file_path, phone_column, session_id)
        )
        thread.start()

        return jsonify({
            'session_id': session_id,
            'message': 'File upload successful, processing started'
        })

    except Exception as e:
        logger.error(f"Error in validate_file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stream-results/<session_id>')
def stream_results(session_id):
    def generate():
        if session_id not in results_queues:
            yield f"data: {json.dumps({'error': 'Invalid session ID'})}\n\n"
            return

        q = results_queues[session_id]
        try:
            while True:
                try:
                    result = q.get(timeout=30)  # 30 second timeout
                    yield f"data: {json.dumps(result)}\n\n"
                    
                    # If processing is complete, break the loop
                    if isinstance(result, dict) and result.get('status') in ['complete', 'error']:
                        break
                except queue.Empty:
                    # Timeout occurred, send keepalive
                    yield f"data: {json.dumps({'status': 'processing'})}\n\n"
        finally:
            # Clean up the queue
            if session_id in results_queues:
                del results_queues[session_id]

    return Response(generate(), mimetype='text/event-stream')

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(
            os.path.join('results', filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=8080)
 