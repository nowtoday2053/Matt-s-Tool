from flask import Flask, render_template, request, jsonify
import os
from validator import PhoneValidator
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

validator = PhoneValidator()

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 