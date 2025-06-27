from flask import Flask, render_template, request, jsonify, send_file
import os
from validator import PhoneValidator
import logging
from werkzeug.utils import secure_filename

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

validator = PhoneValidator()

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

        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Get the phone column name if specified
        phone_column = request.form.get('phone_column')
        
        # Process the file
        try:
            output_path = validator.validate_file(file_path, phone_column)
            
            # Return the path to download results
            return jsonify({
                'success': True,
                'message': 'File processed successfully',
                'result_file': os.path.basename(output_path)
            })
        finally:
            # Clean up the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
    app.run(host='0.0.0.0', port=port) 