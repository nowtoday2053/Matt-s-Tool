import os
import time
import random
import pandas as pd
from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm
import logging
from selenium.webdriver.common.action_chains import ActionChains
import threading
import json
from datetime import datetime
from validator import PhoneValidator

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store jobs in memory (in production, use a proper database)
jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def setup_driver():
    """Setup Chrome driver in headless mode with error handling"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            service = Service('/usr/bin/chromedriver')
            chrome_options.binary_location = '/usr/bin/chromium-browser'
        else:
            service = Service()
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Failed to create driver: {e}")
        raise e

def get_carrier_info(phone_number, driver):
    """Get carrier information for a phone number using phonevalidator.com"""
    try:
        logger.info(f"Checking phone number: {phone_number}")
        
        # Navigate to the website
        driver.get("https://www.phonevalidator.com/")
        wait = WebDriverWait(driver, 20)
        
        # Wait for page to fully load
        time.sleep(3)
        
        # Try multiple selectors to find the input field
        input_field = None
        input_selectors = [
            (By.ID, "phone"),
            (By.NAME, "phone"),
            (By.XPATH, "//input[@type='text']"),
            (By.XPATH, "//input[@placeholder]"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input"),
            (By.XPATH, "//input[contains(@placeholder, '555')]"),
            (By.XPATH, "//input[contains(@placeholder, 'phone')]"),
            (By.XPATH, "//input[contains(@class, 'form')]"),
            (By.CSS_SELECTOR, "input.form-control"),
            (By.CSS_SELECTOR, ".form-control"),
        ]
        
        for selector_type, selector in input_selectors:
            try:
                input_field = wait.until(EC.element_to_be_clickable((selector_type, selector)))
                if input_field.is_displayed() and input_field.is_enabled():
                    logger.info(f"Found input field using: {selector_type} = {selector}")
                    break
            except:
                continue
        
        if not input_field:
            raise Exception("Could not find input field")
        
        # Clear and enter the phone number
        input_field.clear()
        time.sleep(1)
        input_field.send_keys(phone_number)
        logger.info(f"Entered phone number: {phone_number}")
        time.sleep(2)
        
        # Find and click the submit button
        submit_button = None
        button_selectors = [
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[contains(@class, 'btn')]"),
            (By.XPATH, "//button[contains(text(), 'Submit')]"),
            (By.XPATH, "//button[contains(text(), 'Validate')]"),
            (By.XPATH, "//button[contains(text(), 'Check')]"),
            (By.XPATH, "//button"),
            (By.XPATH, "//input[@value='Submit']"),
        ]
        
        for selector_type, selector in button_selectors:
            try:
                submit_button = wait.until(EC.element_to_be_clickable((selector_type, selector)))
                if submit_button.is_displayed() and submit_button.is_enabled():
                    logger.info(f"Found submit button using: {selector_type} = {selector}")
                    break
            except:
                continue
        
        if submit_button:
            submit_button.click()
            logger.info("Clicked submit button")
        else:
            # Try pressing Enter on the input field
            input_field.send_keys(Keys.ENTER)
            logger.info("Pressed Enter on input field")
        
        # Wait for results to load
        time.sleep(5)
        
        # Try to find carrier information in various possible locations
        carrier = "Unknown"
        
        # Look for carrier information in different possible selectors
        possible_selectors = [
            "//td[contains(text(), 'Carrier')]/following-sibling::td",
            "//span[contains(@class, 'carrier')]",
            "//div[contains(@class, 'carrier')]",
            "//*[contains(text(), 'Carrier:')]/following-sibling::*",
            "//*[contains(text(), 'Network:')]/following-sibling::*",
            "//table//td[contains(text(), 'Carrier')]/following-sibling::td",
            "//table//td[contains(text(), 'carrier')]/following-sibling::td",
            "//div[contains(@class, 'result')]//text()[contains(., 'Carrier')]",
        ]
        
        for selector in possible_selectors:
            try:
                carrier_element = driver.find_element(By.XPATH, selector)
                if carrier_element.text.strip():
                    carrier = carrier_element.text.strip()
                    logger.info(f"Found carrier: {carrier}")
                    break
            except:
                continue
        
        # If still unknown, try to find any text that might contain carrier names
        if carrier == "Unknown":
            try:
                page_text = driver.page_source.lower()
                carriers = ['verizon', 'at&t', 'att', 't-mobile', 'tmobile', 'sprint', 'boost', 'cricket', 'metro', 'straight talk', 'tracfone', 'mint mobile']
                for c in carriers:
                    if c in page_text:
                        carrier = c.title()
                        logger.info(f"Found carrier in text: {carrier}")
                        break
            except:
                pass
        
        logger.info(f"Final result - Phone: {phone_number}, Carrier: {carrier}")
        return carrier
        
    except TimeoutException:
        logger.error(f"Timeout for phone number: {phone_number}")
        return "Timeout"
    except Exception as e:
        logger.error(f"Error processing {phone_number}: {str(e)}")
        return "Error"

def process_phone_numbers(file_path):
    """Process phone numbers from uploaded file"""
    try:
        # Read the file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Check for phone number column with flexible naming
        phone_column = None
        possible_column_names = [
            'number', 'Number', 'NUMBER',
            'phone', 'Phone', 'PHONE',
            'phone_number', 'Phone_Number', 'PHONE_NUMBER',
            'phone number', 'Phone Number', 'PHONE NUMBER',
            'telephone', 'Telephone', 'TELEPHONE',
            'mobile', 'Mobile', 'MOBILE',
            'cell', 'Cell', 'CELL'
        ]
        
        for col_name in possible_column_names:
            if col_name in df.columns:
                phone_column = col_name
                break
        
        if phone_column is None:
            available_columns = ', '.join(df.columns.tolist())
            raise ValueError(f"Phone number column not found. Please use one of these column names: 'number', 'phone', 'Phone Number', 'phone_number', etc. Available columns: {available_columns}")
        
        # Setup the driver
        print("\n🚀 Setting up Chrome browser...")
        print("📋 A Chrome browser window will open to check phone numbers")
        print("✋ Please don't close the browser window during processing!")
        driver = setup_driver()
        print("✅ Chrome browser is ready!\n")
        
        results = []
        phone_numbers = df[phone_column].astype(str).tolist()
        
        try:
            # Process each phone number with progress bar
            for phone_number in tqdm(phone_numbers, desc="Processing phone numbers"):
                # Clean the phone number
                clean_number = ''.join(filter(str.isdigit, phone_number))
                
                if len(clean_number) >= 10:  # Valid phone number length
                    carrier = get_carrier_info(clean_number, driver)
                    results.append({
                        'number': phone_number,
                        'carrier': carrier
                    })
                else:
                    results.append({
                        'number': phone_number,
                        'carrier': 'Invalid Number'
                    })
                
                # Random delay between requests
                delay = random.uniform(2, 4)
                time.sleep(delay)
        
        finally:
            driver.quit()
        
        # Create results DataFrame and save to CSV
        results_df = pd.DataFrame(results)
        output_path = os.path.join(RESULTS_FOLDER, 'output.csv')
        results_df.to_csv(output_path, index=False)
        
        return output_path, len(results)
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file type. Please upload CSV or Excel file.'}), 400
    
    # Generate unique job ID
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
    file.save(file_path)
    
    # Initialize job status
    jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'results': [],
        'file_path': file_path
    }
    
    # Start processing in background
    thread = threading.Thread(target=process_file, args=(job_id, file_path))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'message': 'File uploaded successfully. Processing started.'
    })

@app.route('/status/<job_id>')
def get_status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id])

@app.route('/download/<job_id>')
def download_results(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    if jobs[job_id]['status'] != 'completed':
        return jsonify({'error': 'Results not ready'}), 400
    
    # Create results CSV
    results_file = os.path.join(app.config['RESULTS_FOLDER'], f"results_{job_id}.csv")
    df = pd.DataFrame(jobs[job_id]['results'])
    df.to_csv(results_file, index=False)
    
    return send_file(
        results_file,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'phone_validation_results_{job_id}.csv'
    )

def process_file(job_id, file_path):
    try:
        # Read the input file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        phone_numbers = df.iloc[:, 0].astype(str).tolist()
        total = len(phone_numbers)
        
        # Initialize validator
        validator = PhoneValidator()
        
        # Process each number
        for i, phone in enumerate(phone_numbers):
            try:
                result = validator.validate_single_number(phone)
                jobs[job_id]['results'].append(result)
            except Exception as e:
                jobs[job_id]['results'].append({
                    'phone': phone,
                    'error': str(e)
                })
            
            # Update progress
            jobs[job_id]['progress'] = int((i + 1) / total * 100)
        
        jobs[job_id]['status'] = 'completed'
        
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
    
    finally:
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass

if __name__ == '__main__':
    print("Starting Phone Validator Tool...")
    # Use Railway's PORT environment variable if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    # In Railway, host should be 0.0.0.0
    app.run(host='0.0.0.0', port=port) 