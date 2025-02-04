# Russian to Anki

A Python tool that extracts Russian text from various file formats and automatically creates Anki flashcards for vocabulary learning. Features an easy-to-use graphical interface for file selection and configuration.

## Features

- **User-Friendly GUI Interface:**
  - Simple file and directory selection
  - Multiple file selection support
  - Easy configuration of all options
  - Progress and status updates

- **Multiple Input Formats Support:**
  - Text files (`.txt`)
  - Word documents (`.docx`)
  - PDF documents with dual extraction methods:
    - Text extraction (using pdfminer.six)
    - OCR for scanned PDFs (using pdf2image and Tesseract)
  - Images (`.png`, `.jpg`, `.jpeg`, `.bmp`) with enhanced OCR:
    - Automatic image preprocessing
    - Contrast enhancement
    - Sharpness adjustment
  - Batch processing of multiple files and directories

- **Flexible Storage Options:**
  - SQLite database (default)
  - CSV file storage
  - Automatic duplicate detection

- **Anki Integration:**
  - Automatic deck creation
  - Custom card template with fields for:
    - Word
    - Translation
    - Context
  - Exports to `.apkg` format for direct import into Anki

## Setup

1. Make sure you have Python 3.x installed on your system

2. Install system dependencies:
   - **Tesseract OCR** (required for image and scanned PDF processing):
     - Download from: https://github.com/UB-Mannheim/tesseract/wiki
     - Add Tesseract to your system PATH
   
   - **Poppler** (required for PDF processing):
     - Download from: https://github.com/oschwartz10612/poppler-windows/releases/
     - Add the `bin` directory to your system PATH

3. Create a virtual environment by running:
   ```
   python -m venv venv
   ```

4. Run the `activate_venv.bat` script to activate the virtual environment

5. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Using the GUI:
   - Click "Select Files" to choose individual files
   - Click "Select Directory" to process an entire folder
   - Choose your storage method (SQLite or CSV)
   - Optionally customize:
     - Storage path
     - Deck name
     - Output file name
   - Click "Process Files" to start the extraction

The application will automatically:
- Check for required dependencies
- Extract text from all selected files
- Identify new words
- Create an Anki deck
- Show a success message with statistics

## Output Files

- `app.log`: Contains detailed logging information about the program's execution
- `wortschatz.db` or `wortschatz.csv`: Storage file for vocabulary (depending on storage method)
- `russisch_deck.apkg`: Generated Anki deck file (can be imported directly into Anki)

## Notes

- The program automatically detects and skips duplicate words
- OCR functionality requires Tesseract to be installed on your system
- PDF processing works in two modes:
  - Text extraction for normal PDFs
  - OCR for scanned PDFs (requires both Tesseract and Poppler)
- Word document processing requires no additional system dependencies
- All text processing is case-insensitive
- Words are stored with empty translation and context fields, which can be filled in Anki later

## Dependencies

Python packages (installed automatically via requirements.txt):
- genanki: For creating Anki decks
- pdfminer.six: For PDF text extraction
- pytesseract: For OCR functionality
- Pillow: For image processing
- python-docx: For Word document processing
- pdf2image: For converting PDFs to images for OCR
- tkinter: For the graphical interface (usually comes with Python)

System dependencies (must be installed manually):
- Tesseract OCR: For processing images and scanned PDFs
- Poppler: For PDF to image conversion
