"""
Utility functions for the application.
"""
import os
import logging

from src.text_extraction import TESSERACT_PATH, POPPLER_PATH
from src.config import DEFAULT_LOG_FILE

def setup_logging(log_level=logging.INFO, log_file=DEFAULT_LOG_FILE):
    """Configure logging to both file and console."""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def check_dependencies():
    """Check if all required external dependencies are available."""
    import pytesseract
    from pdf2image import convert_from_path
    import docx
    from pdfminer.high_level import extract_text
    
    # Global variables for dependency checks
    TESSERACT_AVAILABLE = False
    PDF2IMAGE_AVAILABLE = False
    DOCX_AVAILABLE = False
    PDFMINER_AVAILABLE = False
    
    # Check Tesseract
    try:
        if os.path.exists(TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
            pytesseract.get_tesseract_version()
            TESSERACT_AVAILABLE = True
            logging.info(f"Tesseract found at: {TESSERACT_PATH}")
        else:
            logging.warning(f"Tesseract not found at: {TESSERACT_PATH}")
    except Exception as e:
        logging.warning(f"Tesseract is not properly installed: {e}")
    
    # Check pdf2image and poppler
    try:
        if os.path.exists(POPPLER_PATH):
            # Test PDF conversion
            PDF2IMAGE_AVAILABLE = True
            logging.info(f"Poppler found at: {POPPLER_PATH}")
        else:
            logging.warning(f"Poppler not found at: {POPPLER_PATH}")
    except Exception as e:
        logging.warning(f"pdf2image or poppler is not properly installed: {e}")

    # Check python-docx
    try:
        import docx
        DOCX_AVAILABLE = True
        logging.info("python-docx is available")
    except ImportError:
        logging.warning("python-docx is not installed. DOCX support will be disabled.")
    
    # Check pdfminer
    try:
        from pdfminer.high_level import extract_text
        PDFMINER_AVAILABLE = True
        logging.info("pdfminer.six is available")
    except ImportError:
        logging.warning("pdfminer.six is not installed. PDF support will be disabled.")
