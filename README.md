# Phone Number Validator Tool

A tool to automatically validate phone numbers using phonevalidator.com. This tool can process multiple phone numbers from CSV or Excel files and save the validation results.

## Features

- 🔍 Validates phone numbers against phonevalidator.com
- 📊 Supports CSV and Excel input files
- 💾 Saves detailed validation results
- 📱 Gets carrier, line type, and location information
- 🚀 Fast batch processing with headless browser
- 📋 Export results to CSV

## Requirements

- Python 3.10 or higher
- Google Chrome browser (latest version)
- Windows 10/11

## Quick Start (Windows)

### Option 1: Download and Run

1. Download this repository as ZIP
2. Extract the ZIP file
3. Double-click `start_validator.bat`

### Option 2: Git Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/phone-validator
cd phone-validator

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## How to Use

1. Start the application using either method above

2. Click "Browse" to select your input file:
   - Supported formats: CSV or Excel (.xlsx)
   - File should have phone numbers in the first column
   - No specific header is required

3. Click "Start Validation" to begin the process

4. Results will be:
   - Displayed in the application window
   - Saved in the logs folder with timestamps
   - Can be exported to CSV using the "Export Results" button

## Input File Format

Your CSV or Excel file should have phone numbers in the first column:

Example CSV:
```
3463038880
9252061729
8064517374
```

## Results

The tool will provide the following information for each phone number:
- Phone Line Type (e.g., CELL PHONE, LANDLINE)
- Phone Company (e.g., T-MOBILE, AT&T)
- Phone Location (City, State)
- Date of Report

## Project Structure

```
phone-validator/
├── app.py                 # Main application file
├── phone_validator.py     # Core validation logic
├── requirements.txt       # Python dependencies
├── start_validator.bat    # Easy start script
├── templates/            
│   └── index.html        # GUI template
├── logs/                 # Validation logs
└── results/              # Exported results
```

## Troubleshooting

1. If you see Chrome version errors:
   - Update Google Chrome to the latest version
   - Update the tool by running: `pip install -r requirements.txt`

2. If the tool isn't starting:
   - Make sure Python is in your system PATH
   - Try running as administrator
   - Check that all requirements are installed

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For any issues:
1. Open an issue in this repository
2. Contact [Your Contact Information] 