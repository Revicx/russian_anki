"""
Configuration module for the Russian Anki application.

This module provides centralized configuration settings for the application,
including paths, external dependencies, and application settings.
It uses pathlib.Path for platform-independent path handling and supports
environment variable overrides for sensitive values.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional

# Environment variable configuration
def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable value with a default fallback.
    
    Args:
        key: The environment variable name
        default: Default value if the environment variable is not set
        
    Returns:
        The environment variable value or the default
    """
    return os.environ.get(key, default)

# Base paths
ROOT_DIR: Path = Path(__file__).parent.parent
SRC_DIR: Path = Path(__file__).parent

# External dependencies
TESSERACT_PATH: Path = Path(get_env('TESSERACT_PATH', 
                                  r'C:\Program Files\Tesseract-OCR\tesseract.exe')
)
POPPLER_PATH: Path = Path(get_env('POPPLER_PATH', 
                                r'C:\Program Files\poppler-24.08.0\Library\bin'))

# Default paths
LOG_DIR: Path = ROOT_DIR / 'logs'
DEFAULT_DB_PATH: Path = ROOT_DIR / 'wortschatz.db'
DEFAULT_OUTPUT_FILE: Path = ROOT_DIR / 'russian_vocab.apkg'
DEFAULT_LOG_FILE: Path = LOG_DIR / 'app.log'
TRANSLATION_LOG_FILE: Path = LOG_DIR / 'translation.log'
EXTRACTION_LOG_FILE: Path = LOG_DIR / 'extraction.log'

# Create log directory if it doesn't exist
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Translation settings
BATCH_SIZE: int = int(get_env('BATCH_SIZE', '50'))  # Number of words per translation batch

# API Keys (from environment variables)
OPENROUTER_API_KEY: Optional[str] = get_env('OPENROUTER_API_KEY')

def validate_config() -> Dict[str, bool]:
    """
    Validate the configuration settings.
    
    Returns:
        A dictionary with validation results for each setting
    """
    validation = {
        "tesseract_path": TESSERACT_PATH.exists(),
        "poppler_path": POPPLER_PATH.exists(),
        "log_dir": LOG_DIR.exists(),
        "openrouter_api_key": bool(OPENROUTER_API_KEY)
    }
    
    # Log validation results
    for key, valid in validation.items():
        if not valid:
            logging.warning(f"Configuration validation failed for {key}")
    
    return validation
