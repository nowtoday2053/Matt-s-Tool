import os
import time
import random
import pandas as pd
from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def setup_driver():
    """Setup undetected Chrome driver in headless mode with error handling"""
    def create_options():
        """Create fresh ChromeOptions object"""
        options = uc.ChromeOptions()
        # Removed --headless to make browser visible
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        return options
    
    try:
        # Try to create driver with automatic version detection
        options = create_options()
        driver = uc.Chrome(options=options, version_main=None)
        return driver
    except Exception as e:
        logger.error(f"Failed to create driver with auto version: {e}")
        try:
            # Fallback 1: try with specific Chrome version 137
            options = create_options()
            driver = uc.Chrome(options=options, version_main=137)
            return driver
        except Exception as e2:
            logger.error(f"Failed with Chrome 137: {e2}")
            try:
                # Fallback 2: try with Chrome version 138
                options = create_options()
                driver = uc.Chrome(options=options, version_main=138)
                return driver
            except Exception as e3:
                logger.error(f"Failed with Chrome 138: {e3}")
                try:
                    # Final fallback: try without any version specification
                    options = create_options()
                    driver = uc.Chrome(options=options)
                    return driver
                except Exception as e4:
                    logger.error(f"All driver creation attempts failed: {e4}")
                    raise Exception(f"Could not create Chrome driver. Please update Chrome browser to the latest version or try again. Error: {e4}")

def get_carrier_info(phone_number, driver):
    """Get carrier information for a phone number using phonevalidator.com"""
    try:
        print(f"\n🔍 Checking phone number: {phone_number}")
        
        # Navigate to the website
        print("📱 Opening phonevalidator.com...")
        driver.get("https://www.phonevalidator.com/")
        
        # Wait for the page to load and find the input field
        wait = WebDriverWait(driver, 20)
        
        # Wait for page to fully load
        time.sleep(3)
        
        print("⌨️  Finding input field...")
        
        # First, let's debug what's actually on the page
        print("🔍 Debugging page content...")
        page_source = driver.page_source
        
        # Look for input tags in the source
        import re
        input_tags = re.findall(r'<input[^>]*>', page_source, re.IGNORECASE)
        print(f"📄 Found {len(input_tags)} input tags:")
        for i, tag in enumerate(input_tags[:5]):  # Show first 5
            print(f"  {i+1}: {tag}")
        
        # Look for any element with placeholder containing '555'
        if '555' in page_source:
            print("✅ Found '555' in page source")
        else:
            print("❌ '555' not found in page source")
            
        # Try multiple selectors to find the phone number input field
        phone_input = None
        input_selectors = [
            (By.ID, "phone"),
            (By.NAME, "phone"),
            (By.XPATH, "//input[@type='text']"),
            (By.XPATH, "//input[@placeholder]"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input"),
            (By.XPATH, "//input[contains(@placeholder, '555')]"),
            (By.XPATH, "//input[contains(@placeholder, 'phone')]"),
            (By.XPATH, "//input[contains(@placeholder, '123')]"),
            (By.XPATH, "//input[contains(@class, 'form')]"),
            (By.CSS_SELECTOR, "input.form-control"),
            (By.CSS_SELECTOR, ".form-control"),
        ]
        
        for selector_type, selector_value in input_selectors:
            try:
                # Try with a shorter wait for each selector
                short_wait = WebDriverWait(driver, 3)
                phone_input = short_wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
                print(f"✅ Found input field using: {selector_type} = {selector_value}")
                break
            except TimeoutException:
                print(f"❌ Failed with selector: {selector_type} = {selector_value}")
                continue
        
        if phone_input is None:
            print("❌ Could not find input field with any selector")
            return "Input Not Found"
        
        # Clear and enter the phone number
        phone_input.clear()
        time.sleep(1)
        phone_input.send_keys(phone_number)
        print(f"✅ Entered phone number: {phone_number}")
        time.sleep(2)
        
        # Find and click the submit button
        print("🔄 Looking for submit button...")
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
        
        for selector_type, selector_value in button_selectors:
            try:
                submit_button = driver.find_element(selector_type, selector_value)
                print(f"✅ Found submit button using: {selector_type} = {selector_value}")
                break
            except NoSuchElementException:
                print(f"❌ Failed with button selector: {selector_type} = {selector_value}")
                continue
        
        if submit_button:
            submit_button.click()
            print("✅ Clicked submit button")
        else:
            # Try pressing Enter on the input field
            print("🔄 Trying to press Enter on input field...")
            phone_input.send_keys(Keys.ENTER)
            print("✅ Pressed Enter")
        
        # Wait for results to load
        print("⏳ Waiting for results...")
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
        
        print("🔎 Searching for carrier information...")
        for selector in possible_selectors:
            try:
                carrier_element = driver.find_element(By.XPATH, selector)
                if carrier_element.text.strip():
                    carrier = carrier_element.text.strip()
                    print(f"✅ Found carrier: {carrier}")
                    break
            except NoSuchElementException:
                continue
        
        # If still unknown, try to find any text that might contain carrier names
        if carrier == "Unknown":
            print("🔍 Searching page content for carrier names...")
            try:
                page_text = driver.page_source.lower()
                carriers = ['verizon', 'at&t', 'att', 't-mobile', 'tmobile', 'sprint', 'boost', 'cricket', 'metro', 'straight talk', 'tracfone', 'mint mobile']
                for c in carriers:
                    if c in page_text:
                        carrier = c.title()
                        print(f"✅ Found carrier in text: {carrier}")
                        break
            except:
                pass
        
        if carrier == "Unknown":
            print("❓ Carrier not found")
        
        logger.info(f"Phone: {phone_number}, Carrier: {carrier}")
        return carrier
        
    except TimeoutException:
        print(f"⏰ Timeout for phone number: {phone_number}")
        logger.error(f"Timeout for phone number: {phone_number}")
        return "Timeout"
    except Exception as e:
        print(f"❌ Error processing {phone_number}: {str(e)}")
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        if phone_number:
            success = validate_phone_number(phone_number)
            return render_template('index.html', message="Phone number validated successfully" if success else "Failed to validate phone number")
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Process the file
            flash('File uploaded successfully! Processing phone numbers...')
            output_path, count = process_phone_numbers(file_path)
            
            # Clean up uploaded file
            os.remove(file_path)
            
            flash(f'Successfully processed {count} phone numbers!')
            return send_file(output_path, as_attachment=True, download_name='carrier_results.csv')
            
        except ValueError as e:
            flash(f'Error: {str(e)}')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'An error occurred while processing the file: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload a CSV or Excel file.')
        return redirect(url_for('index'))

@app.route('/download')
def download_results():
    output_path = os.path.join(RESULTS_FOLDER, 'output.csv')
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True, download_name='carrier_results.csv')
    else:
        flash('No results file found. Please process a file first.')
        return redirect(url_for('index'))

def validate_phone_number(phone_number):
    try:
        # Configure Chrome options
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--start-maximized')
        
        # Create driver with version-specific settings
        driver = uc.Chrome(
            options=chrome_options,
            version_main=137
        )
        
        try:
            # Navigate to the website
            driver.get("https://www.phonevalidator.com/")
            
            # Wait longer for the page to fully load
            time.sleep(5)
            
            # Wait for any input field to be present and visible
            wait = WebDriverWait(driver, 10)
            input_field = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "input"))
            )
            
            # Use JavaScript to modify the input field directly
            js_script = f"""
                var inputs = document.getElementsByTagName('input');
                for (var i = 0; i < inputs.length; i++) {{
                    if (inputs[i].placeholder && inputs[i].placeholder.includes('555-123')) {{
                        inputs[i].value = '{phone_number}';
                        inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                }}
                return false;
            """
            
            # Execute the JavaScript
            success = driver.execute_script(js_script)
            
            if success:
                print(f"Successfully entered phone number: {phone_number}")
            else:
                print("Could not find the input field")
            
            # Keep the browser window open for viewing
            time.sleep(30)
            
            return success
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

if __name__ == '__main__':
    print("Starting Phone Validator Tool...")
    app.run(debug=True) 