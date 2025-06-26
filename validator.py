from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

    def _get_chrome_binary_location(self):
        """Get the Chrome binary location based on the operating system"""
        # First check environment variable
        chrome_binary = os.environ.get('CHROME_BINARY_PATH')
        if chrome_binary and os.path.exists(chrome_binary):
            logger.info(f"Using Chrome binary from environment: {chrome_binary}")
            return chrome_binary

        system = platform.system().lower()
        if system == "windows":
            possible_paths = [
                os.path.expandvars("%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"),
                os.path.expandvars("%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"),
                os.path.expandvars("%LocalAppData%\\Google\\Chrome\\Application\\chrome.exe")
            ]
        else:
            possible_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/snap/bin/chromium'
            ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found Chrome binary at: {path}")
                return path

        logger.error("Chrome binary not found in common locations")
        return None

    def _ensure_chromedriver(self):
        """Ensure ChromeDriver is available and executable"""
        try:
            # First check environment variable
            chromedriver_path = os.environ.get('CHROME_DRIVER_PATH')
            if chromedriver_path and os.path.exists(chromedriver_path):
                logger.info(f"Using ChromeDriver from environment: {chromedriver_path}")
                return chromedriver_path

            system = platform.system().lower()
            if system == "windows":
                possible_paths = [
                    os.path.join(os.getcwd(), 'chromedriver.exe'),
                    os.path.expandvars("%ProgramFiles%\\chromedriver.exe"),
                    os.path.expandvars("%ProgramFiles(x86)%\\chromedriver.exe")
                ]
            else:
                possible_paths = [
                    '/usr/local/bin/chromedriver',
                    '/usr/bin/chromedriver',
                    '/snap/bin/chromedriver'
                ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    logger.info(f"Found ChromeDriver at {path}")
                    return path

            logger.error("ChromeDriver not found in any location")
            return None

        except Exception as e:
            logger.error(f"Error in _ensure_chromedriver: {e}")
            return None

    def validate_single_number(self, phone):
        """Validate a single phone number"""
        # Set up Xvfb if needed
        self._setup_xvfb()

        # Configure Chrome options
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
        
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--single-process')
            
        driver = None
        try:
            # Get Chrome binary location
            chrome_binary = self._get_chrome_binary_location()
            if not chrome_binary:
                raise Exception("Could not locate Chrome binary")
            chrome_options.binary_location = chrome_binary
            
            # Get ChromeDriver path
            chromedriver_path = self._ensure_chromedriver()
            if not chromedriver_path:
                raise Exception("Could not locate ChromeDriver")
            
            service = Service(executable_path=chromedriver_path)
            logger.info(f"Initializing Chrome with driver at {chromedriver_path} and binary at {chrome_binary}")
            
            # Create driver with explicit wait for initialization
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("Successfully initialized Chrome driver")
                    break
                except WebDriverException as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed, retrying... Error: {e}")
                        time.sleep(2)
                    else:
                        raise
            
            if not driver:
                raise Exception("Failed to initialize Chrome driver after all retries")
            
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
                
                logger.info("Successfully extracted all information")
            except Exception as e:
                logger.error(f"Error extracting information: {str(e)}")
                result['error'] = f"Error extracting information: {str(e)}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in validate_single_number: {str(e)}")
            return {
                'phone': phone,
                'error': f"Driver initialization error: {str(e)}"
            }
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("Browser closed successfully")
                except:
                    pass 