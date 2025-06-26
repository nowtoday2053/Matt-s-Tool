import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import threading
from datetime import datetime
import os
import logging
from tqdm import tqdm

class PhoneValidatorUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phone Number Validator")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('Custom.TFrame', background='#f0f0f0')
        self.style.configure('Custom.TButton', padding=5)
        
        # Configure logging
        self.setup_logging()
        
        self.create_widgets()
        
    def setup_logging(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Set up logging configuration
        log_file = f'logs/validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, style='Custom.TFrame', padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Phone Number Validator",
            font=('Helvetica', 24, 'bold'),
            bg='#f0f0f0'
        )
        title_label.pack(pady=20)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        self.file_path = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=60)
        file_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        
        browse_btn = ttk.Button(
            file_frame,
            text="Browse",
            command=self.browse_file,
            style='Custom.TButton'
        )
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        progress_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=300
        )
        self.progress_bar.pack(fill="x", pady=10)
        
        self.status_label = ttk.Label(progress_frame, text="Ready to start...")
        self.status_label.pack()
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create Treeview
        self.tree = ttk.Treeview(results_frame, columns=("Phone", "Type", "Carrier", "Location", "Date"), show="headings")
        self.tree.heading("Phone", text="Phone Number")
        self.tree.heading("Type", text="Line Type")
        self.tree.heading("Carrier", text="Carrier")
        self.tree.heading("Location", text="Location")
        self.tree.heading("Date", text="Date")
        
        # Add scrollbar to Treeview
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = ttk.Button(
            button_frame,
            text="Start Validation",
            command=self.start_validation,
            style='Custom.TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.export_button = ttk.Button(
            button_frame,
            text="Export Results",
            command=self.export_results,
            style='Custom.TButton',
            state='disabled'
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        quit_button = ttk.Button(
            button_frame,
            text="Quit",
            command=self.root.quit,
            style='Custom.TButton'
        )
        quit_button.pack(side=tk.RIGHT, padx=5)
        
        self.results = []
    
    def browse_file(self):
        filetypes = (
            ('CSV files', '*.csv'),
            ('Excel files', '*.xlsx'),
            ('All files', '*.*')
        )
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.file_path.set(filename)
    
    def validate_numbers(self):
        try:
            # Read the input file
            file_path = self.file_path.get()
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            phone_numbers = df.iloc[:, 0].astype(str).tolist()
            total = len(phone_numbers)
            
            # Configure Chrome
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--headless=new')  # Enable headless mode
            
            # Create driver with version-specific settings
            driver = uc.Chrome(
                options=chrome_options,
                version_main=137  # Match your Chrome version
            )
            wait = WebDriverWait(driver, 10)
            
            try:
                for i, phone in enumerate(phone_numbers):
                    try:
                        # Update progress
                        progress = (i + 1) / total * 100
                        self.progress_var.set(progress)
                        self.status_label.config(text=f"Processing number {i+1}/{total}")
                        self.root.update()
                        
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
                        
                        # Extract results using text content
                        try:
                            # Wait for results section to be present
                            wait.until(EC.presence_of_element_located((By.TAG_NAME, "ul")))
                            
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
                            
                            # Get Phone Line Type (using XPath since the ID might be dynamic)
                            type_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Line Type:')]]/span")))
                            result['type'] = type_element.text.strip()
                            
                            # Get Phone Company (using XPath since the ID might be dynamic)
                            company_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Company:')]]/span")))
                            result['company'] = company_element.text.strip()
                            
                            # Get Phone Location (using XPath since the ID might be dynamic)
                            location_element = wait.until(EC.presence_of_element_located((By.XPATH, "//li[strong[contains(text(), 'Phone Location:')]]/span")))
                            result['location'] = location_element.text.strip()
                            
                            # Add to results list and update treeview
                            self.results.append(result)
                            self.tree.insert('', 'end', values=(
                                result['phone'],
                                result['type'],
                                result['company'],
                                result['location'],
                                result['date']
                            ))
                            
                            # Log the result with exact formatting
                            log_file = os.path.join('logs', f'validation_{time.strftime("%Y%m%d_%H%M%S")}.log')
                            with open(log_file, 'a', encoding='utf-8') as f:
                                f.write("RESULTS:\n\n")
                                f.write(f"• Phone Number: {result['phone']}\n")
                                f.write(f"• Date of this Report: {result['date']}\n")
                                f.write(f"• Phone Line Type: {result['type']}\n")
                                f.write(f"• Phone Company: {result['company']}\n")
                                f.write(f"• Phone Location: {result['location']}\n")
                                f.write("\n" + "-" * 50 + "\n\n")
                            
                        except Exception as e:
                            print(f"Error extracting results for {phone}: {str(e)}")
                            self.tree.insert('', 'end', values=(phone, "Error extracting", str(e), "", ""))
                            continue
                        
                    except Exception as e:
                        print(f"Error processing {phone}: {str(e)}")
                        self.tree.insert('', 'end', values=(phone, "Error", str(e), "", ""))
                        continue
                        
            finally:
                driver.quit()
            
            self.status_label.config(text="Validation complete!")
            self.export_button.config(state='normal')
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_label.config(text="Error occurred during validation")
    
    def start_validation(self):
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select an input file first")
            return
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []
        
        # Start validation in a separate thread
        self.start_button.config(state='disabled')
        thread = threading.Thread(target=self.validate_numbers)
        thread.daemon = True
        thread.start()
    
    def export_results(self):
        if not self.results:
            messagebox.showwarning("Warning", "No results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"validated_numbers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            df = pd.DataFrame(self.results)
            df.to_csv(filename, index=False)
            messagebox.showinfo("Success", f"Results exported to {filename}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PhoneValidatorUI()
    app.run() 