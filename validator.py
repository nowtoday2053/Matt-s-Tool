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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneValidator:
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