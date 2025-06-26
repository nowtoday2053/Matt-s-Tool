import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class PhoneValidator:
    def validate_single_number(self, phone):
        # Configure Chrome
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-dev-shm-usage')  # Required for Docker/Railway
        
        # Create driver
        driver = uc.Chrome(
            options=chrome_options,
            version_main=137
        )
        wait = WebDriverWait(driver, 10)
        
        try:
            # Navigate to website
            driver.get("https://www.phonevalidator.com/")
            time.sleep(2)
            
            # Try multiple methods to find and interact with the input field
            try:
                input_field = wait.until(
                    EC.presence_of_element_located((By.ID, "GpofOvnvs"))
                )
            except:
                try:
                    input_field = wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "phone-input"))
                    )
                except:
                    input_field = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-b.phone-input.a-form"))
                    )
            
            # Wait for element to be clickable
            wait.until(EC.element_to_be_clickable((By.ID, "GpofOvnvs")))
            
            # Use JavaScript to ensure element is visible and clickable
            driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
            driver.execute_script("arguments[0].click();", input_field)
            time.sleep(0.5)
            
            # Clear existing value and type new number
            input_field.clear()
            driver.execute_script(f'arguments[0].value = "{phone}";', input_field)
            input_field.send_keys(Keys.TAB)
            
            # Find and click the search button using its specific ID
            try:
                search_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "CaptchaCheck"))
                )
            except:
                try:
                    search_button = wait.until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
                    )
                except:
                    search_button = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input#CaptchaCheck.btn.btn-primary[type='submit']"))
                    )
            
            # Ensure button is visible and click it
            driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", search_button)
            
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

            # Get Phone Number
            phone_element = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_NumberLabel")))
            result['phone'] = phone_element.text.strip()
            
            # Get Date
            date_element = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_ReportDateLabel")))
            result['date'] = date_element.text.strip()
            
            # Get Phone Line Type
            type_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Line Type:')]]/span")))
            result['type'] = type_element.text.strip()
            
            # Get Phone Company
            company_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Company:')]]/span")))
            result['company'] = company_element.text.strip()
            
            # Get Phone Location
            location_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Location:')]]/span")))
            result['location'] = location_element.text.strip()
            
            return result
            
        except Exception as e:
            return {
                'phone': phone,
                'error': str(e)
            }
        
        finally:
            driver.quit() 