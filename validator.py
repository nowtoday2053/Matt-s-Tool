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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneValidator:
    def validate_single_number(self, phone):
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
        
        try:
            # Set up ChromeDriver service
            if os.environ.get('RAILWAY_ENVIRONMENT'):
                service = Service('/usr/bin/chromedriver')
                chrome_options.binary_location = '/usr/bin/chromium-browser'
            else:
                service = Service()  # Let Selenium find ChromeDriver automatically
            
            # Create driver
            driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            
            wait = WebDriverWait(driver, 15)  # Increased timeout for better reliability
            logger.info(f"Starting validation for phone: {phone}")
            
            try:
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
                logger.error(f"Error during validation: {str(e)}")
                return {
                    'phone': phone,
                    'error': str(e)
                }
            
        except Exception as e:
            logger.error(f"Driver initialization error: {str(e)}")
            return {
                'phone': phone,
                'error': f"Driver initialization error: {str(e)}"
            }
        
        finally:
            try:
                driver.quit()
                logger.info("Browser closed successfully")
            except:
                pass 