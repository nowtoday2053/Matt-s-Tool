# 📱 Phone Carrier Checker Tool

A web-based tool that checks phone number carrier information by scraping phonevalidator.com using Flask, Selenium, and undetected Chrome driver.

## ✨ Features

- **Web Interface**: Clean, modern HTML interface with drag-and-drop file upload
- **File Support**: CSV and Excel (.xlsx, .xls) file formats
- **Batch Processing**: Process multiple phone numbers at once
- **Carrier Detection**: Automatically detects carriers like Verizon, AT&T, T-Mobile, etc.
- **Export Results**: Download results as CSV file
- **Progress Tracking**: Terminal progress bar using tqdm
- **Error Handling**: Comprehensive error handling and validation
- **Visible Browser**: Uses undetected_chromedriver with visible Chrome window
- **Rate Limiting**: Random delays (2-4 seconds) to avoid being banned

## 📋 Requirements

- Python 3.7+
- Google Chrome browser installed
- Internet connection

## 🚀 Installation

1. **Clone or download** this project to your local machine

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Make sure Google Chrome is installed** on your system

## 💻 Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://127.0.0.1:5000
   ```

3. **Prepare your file**:
   - Create a CSV or Excel file
   - **IMPORTANT**: The file must have a phone number column (accepts various names like `number`, `phone`, `Phone Number`, `phone_number`, etc.)
   - Phone numbers can be in any format (with or without formatting)

   Example CSV formats:
   ```csv
   number
   5551234567
   (555) 123-4568
   555-123-4569
   +1 555 123 4570
   ```
   
   OR
   
   ```csv
   Phone Number
   5551234567
   (555) 123-4568
   555-123-4569
   +1 555 123 4570
   ```

4. **Upload and process**:
   - Drag and drop your file or click to browse
   - Click "Process Phone Numbers"
   - Wait for processing to complete
   - Download the results file automatically

## 📂 File Structure

```
phone-checker-tool/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Web interface
├── uploads/              # Temporary upload folder (auto-created)
└── results/              # Results folder (auto-created)
    └── output.csv        # Generated results file
```

## 📊 Output Format

The tool generates a CSV file with the following columns:

| number | carrier |
|--------|---------|
| 5551234567 | Verizon |
| 5551234568 | AT&T |
| 5551234569 | T-Mobile |
| 5551234570 | Unknown |

## ⚠️ Important Notes

- **Column Name**: Your input file MUST have a phone number column (supports: `number`, `phone`, `Phone Number`, `phone_number`, `telephone`, `mobile`, `cell`, etc.)
- **Chrome Required**: Google Chrome browser must be installed
- **Rate Limiting**: The tool includes 2-4 second delays between requests
- **Internet Required**: Active internet connection needed
- **File Size**: Maximum upload size is 16MB

## 🔧 Troubleshooting

### Common Issues:

1. **"Phone number column not found"**
   - Make sure your file has a phone number column with one of these names: `number`, `phone`, `Phone Number`, `phone_number`, `telephone`, `mobile`, `cell`, etc.

2. **Chrome driver issues**
   - Ensure Google Chrome is installed and up-to-date
   - The tool will automatically download the appropriate driver

3. **Timeout errors**
   - Check your internet connection
   - Some numbers may timeout - they'll be marked as "Timeout" in results

4. **Permission errors**
   - Make sure you have write permissions in the project directory

### Getting Help:

If you encounter issues:
1. Check that all requirements are installed
2. Ensure Google Chrome is installed
3. Verify your file format and column names
4. Check the terminal output for detailed error messages

## 🛡️ Privacy & Security

- Files are temporarily stored locally and deleted after processing
- The tool uses phonevalidator.com for carrier lookup
- No phone numbers are stored permanently
- All processing happens locally on your machine

## ⚡ Performance

- Processing time depends on the number of phone numbers
- Approximately 3-5 seconds per phone number (including delays)
- Progress is shown in the terminal during processing

## 🔄 Updates

To update the tool:
1. Download the latest version
2. Run `pip install -r requirements.txt` to update dependencies
3. Restart the application

---

**Happy phone number checking! 📱✨** 