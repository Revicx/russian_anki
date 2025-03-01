"""
Utility module providing common functionality for the Russian Anki application.

This module centralizes logging configuration, provides error handling utilities,
and includes functions to check external dependencies.
"""
import os
import logging
import sys
from typing import Optional, Dict, Any, Callable

from src.config import (
    TESSERACT_PATH, POPPLER_PATH, DEFAULT_LOG_FILE, 
    TRANSLATION_LOG_FILE, EXTRACTION_LOG_FILE
)

# Custom exception classes
class RussianAnkiError(Exception):
    """Base exception class for all application-specific errors."""
    pass

class ConfigurationError(RussianAnkiError):
    """Exception raised for errors in the application configuration."""
    pass

class TranslationError(RussianAnkiError):
    """Exception raised for errors during translation operations."""
    pass

class ExtractionError(RussianAnkiError):
    """Exception raised for errors during text extraction operations."""
    pass

class StorageError(RussianAnkiError):
    """Exception raised for errors during storage operations."""
    pass

class AnkiGenerationError(RussianAnkiError):
    """Exception raised for errors during Anki deck generation."""
    pass

# Centralized logging configuration
def setup_logging(log_level: int = logging.INFO, log_file: str = DEFAULT_LOG_FILE) -> logging.Logger:
    """
    Configure logging to both file and console.
    
    Args:
        log_level: The logging level to use (default: logging.INFO)
        log_file: Path to the log file (default: DEFAULT_LOG_FILE)
        
    Returns:
        The configured root logger
    """
    # Clear existing handlers to avoid duplicates
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    fh = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def get_module_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a logger for a specific module with optional file output.
    
    Args:
        name: The name of the logger (typically __name__)
        log_file: Optional path to a module-specific log file
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # If this logger already has handlers, return it
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console handler if not already present
    has_console_handler = any(isinstance(h, logging.StreamHandler) and 
                             h.stream == sys.stdout for h in logger.handlers)
    if not has_console_handler:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    
    # Add file handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

# Create module-specific loggers
extraction_logger = get_module_logger("extraction", EXTRACTION_LOG_FILE)
translation_logger = get_module_logger("translation", TRANSLATION_LOG_FILE)

def safe_execute(func: Callable, error_msg: str, 
                logger: Optional[logging.Logger] = None, 
                exception_type: type = RussianAnkiError, 
                **kwargs: Any) -> Any:
    """
    Execute a function safely with proper error handling.
    
    Args:
        func: The function to execute
        error_msg: Error message to log if the function fails
        logger: Logger to use (defaults to root logger)
        exception_type: Type of exception to raise if the function fails
        **kwargs: Arguments to pass to the function
        
    Returns:
        The result of the function call
        
    Raises:
        The specified exception_type with the error_msg
    """
    if logger is None:
        logger = logging.getLogger()
        
    try:
        return func(**kwargs)
    except Exception as e:
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        raise exception_type(f"{error_msg}: {str(e)}") from e

def check_dependencies() -> Dict[str, bool]:
    """
    Check if all required external dependencies are available.
    
    Returns:
        A dictionary with the availability status of each dependency
    """
    import pytesseract
    from pdf2image import convert_from_path
    import docx
    from pdfminer.high_level import extract_text
    
    # Global variables for dependency checks
    dependencies = {
        "tesseract": False,
        "pdf2image": False,
        "docx": False,
        "pdfminer": False
    }
    
    # Check Tesseract
    try:
        if os.path.exists(TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
            pytesseract.get_tesseract_version()
            dependencies["tesseract"] = True
            logging.info(f"Tesseract found at: {TESSERACT_PATH}")
        else:
            logging.warning(f"Tesseract not found at: {TESSERACT_PATH}")
    except Exception as e:
        logging.warning(f"Tesseract is not properly installed: {e}")
    
    # Check pdf2image and poppler
    try:
        if os.path.exists(POPPLER_PATH):
            # Test PDF conversion
            dependencies["pdf2image"] = True
            logging.info(f"Poppler found at: {POPPLER_PATH}")
        else:
            logging.warning(f"Poppler not found at: {POPPLER_PATH}")
    except Exception as e:
        logging.warning(f"pdf2image or poppler is not properly installed: {e}")

    # Check python-docx
    try:
        import docx
        dependencies["docx"] = True
        logging.info("python-docx is available")
    except ImportError:
        logging.warning("python-docx is not installed. DOCX support will be disabled.")
    
    # Check pdfminer
    try:
        from pdfminer.high_level import extract_text
        dependencies["pdfminer"] = True
        logging.info("pdfminer.six is available")
    except ImportError:
        logging.warning("pdfminer.six is not installed. PDF support will be disabled.")
        
    return dependencies
