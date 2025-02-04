# Russian to Anki

A Python-based tool that automatically extracts Russian vocabulary from various document formats and creates Anki flashcards. Perfect for language learners who want to efficiently build their vocabulary from study materials.

## Key Features

- **Advanced Text Extraction:**
  - Multi-format support:
    - PDFs (text-based and scanned)
    - Word documents (`.docx`)
    - Images (`.png`, `.jpg`, `.jpeg`, `.bmp`)
    - Text files (`.txt`)
  - Smart OCR with image preprocessing:
    - Automatic contrast enhancement
    - Sharpness adjustment
    - Optimized for Cyrillic characters
  - Intelligent Russian word detection and filtering

- **Professional Translation:**
  - OpenRouter API integration
  - Batch translation processing (configurable batch size)
  - Smart word cleaning and preprocessing
  - Comprehensive translation logging

- **Anki Integration:**
  - Automatic deck creation with custom templates
  - Built-in duplicate detection
  - Direct `.apkg` export format

- **Robust Data Management:**
  - SQLite database (primary storage)
  - Optional CSV export
  - Automatic deduplication
  - Structured logging system:
    - Translation logs
    - Extraction logs
    - Application logs

## Prerequisites

- Python 3.x
- Tesseract OCR with Russian language support
- Poppler (for PDF processing)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Auron040/russian_anki.git
cd russian_anki
```

### 2. Install System Dependencies

#### Tesseract OCR
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install with Russian language support
3. Add to system PATH

#### Poppler
1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extract to the project directory as `poppler-windows`

### 3. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the project root with your API key:
```env
OPENROUTER_API_KEY=your_api_key_here
```

All other configuration settings (paths, defaults, batch sizes, etc.) can be found in `src/config.py`.

## Usage

### GUI Mode (Recommended)
```bash
python run.py
```
1. Select files or directories to process
2. Choose storage method (SQLite/CSV)
3. Click "Process" to start

### Command Line Mode
```bash
python run.py --files path/to/files/* --storage sqlite --log-level INFO
```

## Project Structure

- `src/`
  - `gui.py`: GUI implementation
  - `text_extraction.py`: Multi-format text extraction
  - `translator.py`: OpenRouter translation integration
  - `anki_generator.py`: Anki deck creation
  - `storage.py`: Data persistence
  - `utils.py`: Utility functions
  - `config.py`: Configuration settings

- `run.py`: Application entry point

## Dependencies

### Python Packages
- `genanki`: Anki deck creation
- `pdfminer.six`: PDF text extraction
- `pytesseract`: OCR functionality
- `Pillow`: Image processing
- `python-docx`: Word document processing
- `pdf2image`: PDF to image conversion
- `python-dotenv`: Environment management

## Troubleshooting

- **OCR Issues**: 
  - Verify Tesseract installation and PATH
  - Check Russian language pack installation
  - Try adjusting image preprocessing parameters

- **PDF Processing Errors**: 
  - Ensure Poppler is in the correct location
  - Check if PDF is text-based or scanned
  - Try different extraction methods

- **Translation Errors**:
  - Verify OpenRouter API key
  - Check network connection
  - Monitor API rate limits
  - Review translation logs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
