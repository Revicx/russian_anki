# Russian to Anki

A Python-based tool that automatically extracts Russian vocabulary from various document formats and creates Anki flashcards. Perfect for language learners who want to efficiently build their vocabulary from study materials.

## Key Features

- **Smart Text Extraction:**
  - Supports multiple input formats:
    - PDFs (both text-based and scanned)
    - Word documents (`.docx`)
    - Images (`.png`, `.jpg`, `.jpeg`, `.bmp`)
    - Text files (`.txt`)
  - Advanced OCR capabilities for images and scanned documents
  - Intelligent Russian text detection and extraction
  - Automatic preprocessing for better OCR results

- **Efficient Translation:**
  - Automatic Russian word detection
  - Batch translation processing
  - Configurable translation API (OpenRouter)
  - Smart word cleaning and preprocessing

- **Anki Integration:**
  - Automatic deck creation
  - Custom card templates
  - Duplicate detection and removal
  - Direct `.apkg` export format

- **Data Management:**
  - SQLite database for vocabulary storage
  - Optional CSV storage
  - Automatic word deduplication
  - Progress tracking and logging

## Prerequisites

- Python 3.x
- Tesseract OCR (for image processing)
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
2. Extract the archive
3. Add the `bin` directory to system PATH

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

All other configuration settings (paths, defaults, etc.) can be found in `src/config.py`.

## Usage

### GUI Mode
```bash
python run.py
```
1. Select files or directories to process
2. Choose storage method (SQLite/CSV)
3. Click "Process" to start

### Command Line Mode
```bash
python run.py --files path/to/files/* --storage sqlite
```

## Project Structure

- `src/`
  - `gui.py`: GUI implementation
  - `text_extraction.py`: Text extraction from various formats
  - `translator.py`: Translation functionality
  - `anki_generator.py`: Anki deck creation
  - `storage.py`: Data persistence
  - `utils.py`: Utility functions
  - `config.py`: Configuration settings

## Dependencies

### Python Packages
- `genanki`: Anki deck creation
- `pdfminer.six`: PDF text extraction
- `pytesseract`: OCR functionality
- `Pillow`: Image processing
- `python-docx`: Word document processing
- `pdf2image`: PDF to image conversion
- `openai`: Translation API interface
- `python-dotenv`: Environment management

## Troubleshooting

- **OCR Issues**: 
  - Verify Tesseract installation
  - Check PATH configuration
  - Ensure Russian language pack is installed

- **PDF Processing Errors**: 
  - Confirm Poppler installation
  - Verify PATH settings
  - Try different PDF processing modes

- **Translation Errors**:
  - Check API key in `.env`
  - Verify internet connection
  - Monitor API rate limits

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
