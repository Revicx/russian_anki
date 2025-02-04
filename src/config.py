"""
Configuration settings for the application.
"""
import os
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent

# External dependencies
TESSERACT_PATH = os.path.join(ROOT_DIR, 'Tesseract-OCR', 'tesseract.exe')
POPPLER_PATH = os.path.join(ROOT_DIR, 'poppler-windows', 'Library', 'bin')

# Default paths
DEFAULT_DB_PATH = os.path.join(ROOT_DIR, 'wortschatz.db')
DEFAULT_OUTPUT_FILE = os.path.join(ROOT_DIR, 'russisch_vokabeln.apkg')
LOG_DIR = os.path.join(ROOT_DIR, 'logs')
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, 'app.log')
TRANSLATION_LOG_FILE = os.path.join(LOG_DIR, 'translation.log')
EXTRACTION_LOG_FILE = os.path.join(LOG_DIR, 'extraction.log')

# Erstelle Log-Verzeichnis falls nicht vorhanden
os.makedirs(LOG_DIR, exist_ok=True)

# Translation settings
BATCH_SIZE = 50  # Anzahl der Wörter pro Übersetzungs-Batch
