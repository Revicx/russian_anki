"""
Russian Anki Application - A tool for extracting and learning Russian vocabulary.

This package provides functionality for extracting Russian words from various file formats,
translating them, storing them in a database, and generating Anki decks for learning.
"""

from src.anki_generator import create_anki_deck
from src.config import (
    ROOT_DIR, SRC_DIR, TESSERACT_PATH, POPPLER_PATH,
    DEFAULT_DB_PATH, DEFAULT_OUTPUT_FILE, LOG_DIR,
    DEFAULT_LOG_FILE, TRANSLATION_LOG_FILE, EXTRACTION_LOG_FILE,
    BATCH_SIZE
)
from src.gui import VocabExtractorGUI, create_gui
from src.main import process_files, cli, AppContext
from src.storage import (
    init_db_sqlite, get_existing_words_sqlite, insert_new_words_sqlite,
    read_vocab_csv, append_new_words_csv, get_vocab, store_new_words
)
from src.text_extraction import (
    extract_text_from_input, extract_text_from_file, extract_text_from_docx,
    extract_text_from_image, extract_text_from_pdf, extract_text_from_pdf_ocr,
    extract_text_from_markdown, clean_and_split_text, is_valid_russian_word
)
from src.translator import RussianTranslator
from src.utils import setup_logging, check_dependencies

__all__ = [
    # anki_generator
    'create_anki_deck',
    
    # config
    'ROOT_DIR', 'SRC_DIR', 'TESSERACT_PATH', 'POPPLER_PATH',
    'DEFAULT_DB_PATH', 'DEFAULT_OUTPUT_FILE', 'LOG_DIR',
    'DEFAULT_LOG_FILE', 'TRANSLATION_LOG_FILE', 'EXTRACTION_LOG_FILE',
    'BATCH_SIZE',
    
    # gui
    'VocabExtractorGUI', 'create_gui',
    
    # main
    'process_files', 'cli', 'AppContext',
    
    # storage
    'init_db_sqlite', 'get_existing_words_sqlite', 'insert_new_words_sqlite',
    'read_vocab_csv', 'append_new_words_csv', 'get_vocab', 'store_new_words',
    
    # text_extraction
    'extract_text_from_input', 'extract_text_from_file', 'extract_text_from_docx',
    'extract_text_from_image', 'extract_text_from_pdf', 'extract_text_from_pdf_ocr',
    'extract_text_from_markdown', 'clean_and_split_text', 'is_valid_russian_word',
    
    # translator
    'RussianTranslator',
    
    # utils
    'setup_logging', 'check_dependencies'
]
