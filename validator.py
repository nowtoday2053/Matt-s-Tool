import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
import logging
import subprocess
import platform
from selenium.common.exceptions import WebDriverException
import pandas as pd
from datetime import datetime
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneValidator:
    def __init__(self):
        self.results_dir = "results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def _setup_xvfb(self):
        """Set up Xvfb for headless operation in Linux"""
        if platform.system().lower() != "windows" and os.environ.get('RAILWAY_ENVIRONMENT'):
            try:
                # Start Xvfb
                subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24', '-ac'])
                logger.info("Started Xvfb display")
                time.sleep(1)  # Give Xvfb time to start
            except Exception as e:
                logger.error(f"Failed to start Xvfb: {e}")

    def _get_driver(self):
        """Get an undetected Chrome driver instance"""
        options = uc.ChromeOptions()
        options.headless = True  # Change to False if you want to see the browser
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--single-process')

        try:
            driver = uc.Chrome(options=options)
            logger.info("Successfully initialized undetected Chrome driver")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise

    def validate_file(self, file_path, phone_column=None):
        """
        Validate phone numbers from a CSV or Excel file
        
        Args:
            file_path (str): Path to the input file (CSV or Excel)
            phone_column (str, optional): Name of the column containing phone numbers.
                                        If None, will try to auto-detect.
        
        Returns:
            str: Path to the output file with results
        """
        try:
            # Read the file
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Please use CSV or Excel file.")

            # Auto-detect phone column if not specified
            if phone_column is None:
                possible_columns = ['phone', 'phone_number', 'phonenumber', 'number', 'contact', 'mobile']
                for col in possible_columns:
                    if col in df.columns.str.lower():
                        phone_column = df.columns[df.columns.str.lower() == col][0]
                        break
                
                if phone_column is None:
                    phone_column = df.columns[0]  # Use first column as fallback
                    logger.warning(f"No phone column detected, using first column: {phone_column}")
                else:
                    logger.info(f"Auto-detected phone column: {phone_column}")

            # Create results list
            results = []
            
            # Process each phone number with progress bar
            logger.info(f"Processing {len(df)} phone numbers...")
            for _, row in tqdm(df.iterrows(), total=len(df), desc="Validating phone numbers"):
                phone = str(row[phone_column]).strip()
                result = self.validate_single_number(phone)
                results.append(result)
                time.sleep(1)  # Add delay between requests

            # Create results DataFrame
            results_df = pd.DataFrame(results)

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"validated_numbers_{timestamp}.csv"
            output_path = os.path.join(self.results_dir, output_filename)

            # Save results
            results_df.to_csv(output_path, index=False)
            logger.info(f"Results saved to: {output_path}")
            
            return output_path

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise

    def validate_single_number(self, phone):
        """Validate a single phone number"""
        # Set up Xvfb if needed
        self._setup_xvfb()

        driver = None
        try:
            # Create driver with undetected_chromedriver
            driver = self._get_driver()
            
            # Rest of the validation code...
            wait = WebDriverWait(driver, 15)
            logger.info(f"Starting validation for phone: {phone}")
            
            # Navigate to website
            driver.get("https://www.phonevalidator.com/")
            logger.info("Successfully loaded website")
            time.sleep(2)
            
            # Try multiple methods to find and interact with the input field
            input_field = None
            selectors = [
                (By.ID, "GpofOvnvs"),
                (By.CLASS_NAME, "phone-input"),
                (By.CSS_SELECTOR, "input.form-control.form-b.phone-input.a-form"),
                (By.TAG_NAME, "input"),
                (By.XPATH, "//input[@type='text']")
            ]
            
            for selector_type, selector in selectors:
                try:
                    input_field = wait.until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    if input_field.is_displayed() and input_field.is_enabled():
                        break
                except:
                    continue
            
            if not input_field:
                raise Exception("Could not find input field")
            
            logger.info("Found input field")
            
            # Use JavaScript to ensure element is visible and clickable
            driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
            time.sleep(0.5)
            
            # Clear existing value and type new number
            input_field.clear()
            driver.execute_script(f'arguments[0].value = "{phone}";', input_field)
            input_field.send_keys(Keys.TAB)
            logger.info("Entered phone number")
            
            # Find and click the search button
            search_button = None
            button_selectors = [
                (By.ID, "CaptchaCheck"),
                (By.CLASS_NAME, "btn-primary"),
                (By.CSS_SELECTOR, "input#CaptchaCheck.btn.btn-primary[type='submit']"),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//input[@type='submit']")
            ]
            
            for selector_type, selector in button_selectors:
                try:
                    search_button = wait.until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    if search_button.is_displayed() and search_button.is_enabled():
                        break
                except:
                    continue
            
            if not search_button:
                raise Exception("Could not find search button")
            
            # Click the button
            driver.execute_script("arguments[0].click();", search_button)
            logger.info("Clicked search button")
            
            # Wait for results to load
            time.sleep(3)
            
            # Initialize result dictionary
            result = {
                'phone': phone,
                'date': '',
                'type': '',
                'company': '',
                'location': ''
            }

            # Get results with better error handling
            try:
                phone_element = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_NumberLabel")))
                result['phone'] = phone_element.text.strip()
                
                date_element = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_ReportDateLabel")))
                result['date'] = date_element.text.strip()
                
                type_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Line Type:')]]/span")))
                result['type'] = type_element.text.strip()
                
                company_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Company:')]]/span")))
                result['company'] = company_element.text.strip()
                
                location_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Location:')]]/span")))
                result['location'] = location_element.text.strip()
                
                logger.info(f"Successfully retrieved results for {phone}")
                return result
                
            except Exception as e:
                logger.error(f"Error extracting results: {e}")
                return result
                
        except Exception as e:
            logger.error(f"Error in validate_single_number: {e}")
            return {
                'phone': phone,
                'date': '',
                'type': '',
                'company': '',
                'location': ''
            }
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass 