"""
Text extraction module for handling various file formats.
"""

import inspect
# Monkey-patch inspect.getargspec to use a four-value tuple from getfullargspec
if not hasattr(inspect, 'getargspec'):
    def getargspec(func):
        fullargspec = inspect.getfullargspec(func)
        return fullargspec.args, fullargspec.varargs, fullargspec.varkw, fullargspec.defaults
    inspect.getargspec = getargspec

import os
import re
import logging
import docx
from PIL import Image, ImageEnhance
import pytesseract
from pdfminer.high_level import extract_text as extract_text_pdfminer
from pdf2image import convert_from_path
import pymorphy2
import unicodedata

from src.storage import get_vocab
from src.config import TESSERACT_PATH, POPPLER_PATH, EXTRACTION_LOG_FILE

# Configure extraction logger
extraction_logger = logging.getLogger('Extraction')
extraction_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler for text extraction
fh = logging.FileHandler(EXTRACTION_LOG_FILE, encoding='utf-8')
fh.setFormatter(formatter)
extraction_logger.addHandler(fh)

# Set Tesseract and Poppler paths
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Initialize PyMorphy2 morphological analyzer
morph = pymorphy2.MorphAnalyzer()

def is_valid_russian_word(word):
    """
    Check if a word is a valid Russian word using PyMorphy2.
    The word is first normalized to NFC form so that combining diacritics
    (e.g. stress marks) are properly combined with the base letters.
    """
    normalized_word = unicodedata.normalize('NFC', word)
    parses = morph.parse(normalized_word)
    # A word is considered valid if any parse does not have the 'UNKN' flag.
    for p in parses:
        if 'UNKN' not in p.tag:
            return True
    return False

def clean_and_split_text(text):
    """Cleans text and extracts Russian words."""
    if not text:
        return set()
    
    # Remove all non-Russian characters except spaces and combining diacritics (stresses)
    cleaned = re.sub(r'[^а-яА-ЯёЁ\s\u0301\u0300]', ' ', text)
    
    # Normalize spaces
    cleaned = ' '.join(cleaned.split())
    
    # Split into words and filter based on Russian letters.
    words = set()
    for word in cleaned.split():
        if len(word) >= 1 and re.search(r'[а-яА-ЯёЁ\u0301\u0300]+', word):
            words.add(word.lower())
    
    extraction_logger.debug(f"Extracted {len(words)} potential Russian words")
    return words

def extract_text_from_docx(filepath):
    """Extract text from a .docx file."""
    extraction_logger.info(f"Starting DOCX extraction: {filepath}")
    try:
        doc = docx.Document(filepath)
        text = '\n'.join(paragraph.text for paragraph in doc.paragraphs)
        extraction_logger.info(f"Text successfully extracted from DOCX: {filepath}")
        return text
    except Exception as e:
        extraction_logger.error(f"Error during DOCX extraction from {filepath}: {str(e)}")
        return ""

def extract_text_from_image(image_path):
    """Extract text from an image with improved preprocessing."""
    extraction_logger.info(f"Starting OCR for: {image_path}")
    try:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        # Open the image
        image = Image.open(image_path)
        
        # Convert to grayscale and enhance contrast for better OCR performance
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Extract text using Tesseract (Russian language)
        text = pytesseract.image_to_string(image, lang='rus')
        extraction_logger.info(f"Text extracted from image: {image_path}")
        return text
    except Exception as e:
        extraction_logger.error(f"Error during OCR of {image_path}: {str(e)}")
        return ""

def extract_text_from_pdf_ocr(pdf_path):
    """Extract text from a PDF using OCR."""
    extraction_logger.info(f"Starting PDF OCR for: {pdf_path}")
    try:
        # Convert PDF pages to images using Poppler
        pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        text = ""
        for i, page in enumerate(pages):
            temp_image = f"temp_page_{i}.png"
            page.save(temp_image, 'PNG')
            page_text = extract_text_from_image(temp_image)
            text += page_text + "\n"
            os.remove(temp_image)
        return text
    except Exception as e:
        extraction_logger.error(f"Error during PDF OCR of {pdf_path}: {str(e)}")
        return ""

def extract_text_from_pdf(filepath):
    """Extract text from a PDF using both pdfminer and OCR if needed."""
    extraction_logger.info(f"Starting PDF extraction: {filepath}")
    try:
        text = extract_text_pdfminer(filepath)
        extraction_logger.debug(f"PDFMiner extraction: {len(text)} characters")
        if len(text.strip()) < 100:
            extraction_logger.info("Little text found, trying OCR...")
            text = extract_text_from_pdf_ocr(filepath)
        return text
    except Exception as e:
        extraction_logger.error(f"Error processing PDF {filepath}: {str(e)}")
        return ""

def extract_text_from_markdown(file_path):
    """Extracts text from a markdown file, stripping out common markdown formatting."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`.*?`', '', text)
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
        return text
    except Exception as e:
        extraction_logger.error(f"Error extracting text from markdown file '{file_path}': {e}")
        return ""

def extract_text_from_file(filepath):
    """Extract text from a single file based on its extension."""
    extraction_logger.info(f"Starting text extraction from: {filepath}")
    if not os.path.exists(filepath):
        extraction_logger.error(f"File not found: {filepath}")
        return ""
        
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.pdf':
            return extract_text_from_pdf(filepath)
        elif ext == '.docx':
            return extract_text_from_docx(filepath)
        elif ext in ['.png', '.jpg', '.jpeg']:
            return extract_text_from_image(filepath)
        elif ext == '.txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.md':
            return extract_text_from_markdown(filepath)
        else:
            extraction_logger.warning(f"Unsupported file type {ext}: {filepath}")
            return ""
    except Exception as e:
        extraction_logger.error(f"Error extracting text from {filepath}: {str(e)}")
        return ""

def extract_text_from_input(input_path, storage='sqlite', storage_path='vocab.db'):
    """
    Extracts text from a file or directory based on file type.
    Supports PDF, DOCX, Markdown (.md), plain text, and image files.
    Additionally, it checks each extracted word with PyMorphy2 (after normalization)
    to ensure that the word is a genuine Russian word.
    """
    extraction_logger.info(f"Starting text extraction from: {input_path}")
    try:
        # Get existing words from the database at the beginning
        existing_words = get_vocab(storage, storage_path)
        extraction_logger.info(f"{len(existing_words)} existing words found in {storage} {storage_path}.")
        
        if not os.path.exists(input_path):
            extraction_logger.error(f"File not found: {input_path}")
            return set()

        # If it's a directory, process all supported files
        if os.path.isdir(input_path):
            new_words = set()
            total_valid_words = set()
            for root, dirs, files in os.walk(input_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in [".txt", ".pdf", ".docx", ".png", ".jpg", ".jpeg", ".md"]:
                        file_path = os.path.join(root, file)
                        text = extract_text_from_file(file_path)
                        words = clean_and_split_text(text)
                        # Validate each word with PyMorphy2 (with normalization)
                        valid_words = {word for word in words if is_valid_russian_word(word)}
                        total_valid_words.update(valid_words)
                        new_words_from_file = {word for word in valid_words if word.lower() not in existing_words}
                        if new_words_from_file:
                            new_words.update(new_words_from_file)
                            extraction_logger.info(
                                f"File {file}: {len(valid_words)} valid words found, {len(new_words_from_file)} new"
                            )
            extraction_logger.info(
                f"Directory total: {len(total_valid_words)} valid words found, {len(new_words)} new"
            )
            return new_words

        # If it's a single file, extract and validate its content.
        text = extract_text_from_file(input_path)
        words = clean_and_split_text(text)
        valid_words = {word for word in words if is_valid_russian_word(word)}
        new_words = {word for word in valid_words if word.lower() not in existing_words}
        extraction_logger.info(
            f"File total: {len(valid_words)} valid words out of {len(words)} total found, {len(new_words)} new"
        )
        return new_words
            
    except Exception as e:
        extraction_logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return set()