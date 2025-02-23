"""
Configuration settings for the application.
"""
import os
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent

# External dependencies
TESSERACT_PATH = os.path.join('C:\\', 'Program Files', 'Tesseract-OCR', 'tesseract.exe')
POPPLER_PATH = os.path.join('C:\\', 'Program Files', 'poppler-24.08.0', 'Library', 'bin')

# Default paths
DEFAULT_DB_PATH = os.path.join(ROOT_DIR, 'wortschatz.db')
DEFAULT_OUTPUT_FILE = os.path.join(ROOT_DIR, 'russian_vocab.apkg')
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, 'app.log')
TRANSLATION_LOG_FILE = os.path.join(LOG_DIR, 'translation.log')
EXTRACTION_LOG_FILE = os.path.join(LOG_DIR, 'extraction.log')

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Translation settings
BATCH_SIZE = 50  # Number of words per translation batch
