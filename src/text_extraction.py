"""
Text extraction module for handling various file formats.
"""
import os
import re
import logging
import docx
from PIL import Image, ImageEnhance
import pytesseract
from pdfminer.high_level import extract_text as extract_text_pdfminer
from pdf2image import convert_from_path

from src.storage import get_vocab
from src.config import TESSERACT_PATH, POPPLER_PATH, EXTRACTION_LOG_FILE

# Konfiguriere Extraction Logger
extraction_logger = logging.getLogger('Extraction')
extraction_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File Handler für Textextraktion
fh = logging.FileHandler(EXTRACTION_LOG_FILE, encoding='utf-8')
fh.setFormatter(formatter)
extraction_logger.addHandler(fh)

# Set Tesseract and Poppler paths
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def clean_and_split_text(text):
    """Bereinigt Text und extrahiert russische Wörter."""
    if not text:
        return set()
    
    # Entferne alle nicht-russischen Zeichen außer Leerzeichen
    cleaned = re.sub(r'[^а-яА-ЯёЁ\s]', ' ', text)
    
    # Normalisiere Leerzeichen
    cleaned = ' '.join(cleaned.split())
    
    # Teile in Wörter und filtere
    words = set()
    for word in cleaned.split():
        # Prüfe Mindestlänge (2 Zeichen) und ob es russische Zeichen enthält
        if len(word) >= 2 and re.search(r'[а-яА-ЯёЁ]{2,}', word):
            words.add(word.lower())
    
    extraction_logger.debug(f"Extrahierte {len(words)} russische Wörter")
    return words

def extract_text_from_docx(filepath):
    """Extract text from a .docx file."""
    extraction_logger.info(f"Starte DOCX-Extraktion: {filepath}")
    try:
        doc = docx.Document(filepath)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        extraction_logger.info(f"Text successfully extracted from DOCX: {filepath}")
        return text
    except Exception as e:
        extraction_logger.error(f"Fehler bei DOCX-Extraktion von {filepath}: {str(e)}")
        return ""

def extract_text_from_image(image_path):
    """Extrahiert Text aus einem Bild mit verbesserter Vorverarbeitung."""
    extraction_logger.info(f"Starte OCR für: {image_path}")
    try:
        # Setze Tesseract-Pfad
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        # Öffne das Bild
        image = Image.open(image_path)
        
        # Konvertiere zu Graustufen
        image = image.convert('L')
        
        # Verbessere den Kontrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Extrahiere Text mit Tesseract (Russisch)
        text = pytesseract.image_to_string(image, lang='rus')
        extraction_logger.info(f"Text aus Bild extrahiert: {image_path}")
        
        return text
        
    except Exception as e:
        extraction_logger.error(f"Fehler bei OCR von {image_path}: {str(e)}")
        return ""

def extract_text_from_pdf_ocr(pdf_path):
    """Extrahiert Text aus einem PDF mittels OCR."""
    extraction_logger.info(f"Starte PDF OCR für: {pdf_path}")
    try:
        # Konvertiere PDF zu Bildern
        pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        text = ""
        
        # Verarbeite jede Seite
        for i, page in enumerate(pages):
            # Speichere temporär als PNG
            temp_image = f"temp_page_{i}.png"
            page.save(temp_image, 'PNG')
            
            # Extrahiere Text aus dem Bild
            page_text = extract_text_from_image(temp_image)
            text += page_text + "\n"
            
            # Lösche temporäre Datei
            os.remove(temp_image)
            
        return text
        
    except Exception as e:
        extraction_logger.error(f"Fehler bei PDF OCR von {pdf_path}: {str(e)}")
        return ""

def extract_text_from_pdf(filepath):
    """Extract text from PDF using both pdfminer and OCR if needed."""
    extraction_logger.info(f"Starte PDF-Extraktion: {filepath}")
    try:
        # Versuche erst normalen Text zu extrahieren
        text = extract_text_pdfminer(filepath)
        extraction_logger.debug(f"PDFMiner Extraktion: {len(text)} Zeichen")
        
        # Wenn wenig Text gefunden wurde, versuche OCR
        if len(text.strip()) < 100:
            extraction_logger.info("Wenig Text gefunden, versuche OCR...")
            text = extract_text_from_pdf_ocr(filepath)
            
        return text
        
    except Exception as e:
        extraction_logger.error(f"Fehler bei der PDF-Verarbeitung von {filepath}: {str(e)}")
        return ""

def extract_text_from_file(filepath):
    """Extract text from a single file based on its extension."""
    extraction_logger.info(f"Starte Textextraktion aus: {filepath}")
    if not os.path.exists(filepath):
        extraction_logger.error(f"Datei nicht gefunden: {filepath}")
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
        else:
            extraction_logger.warning(f"Unsupported file type {ext}: {filepath}")
            return ""
    except Exception as e:
        extraction_logger.error(f"Fehler bei der Textextraktion aus {filepath}: {str(e)}")
        return ""

def extract_text_from_input(input_path, storage='sqlite', storage_path='vocab.db'):
    """Extrahiert Text aus verschiedenen Dateiformaten."""
    extraction_logger.info(f"Starte Textextraktion aus: {input_path}")
    
    try:
        # Hole existierende Wörter aus der Datenbank am Anfang
        existing_words = get_vocab(storage, storage_path)
        extraction_logger.info(f"{len(existing_words)} existierende Wörter in {storage} {storage_path} gefunden.")
        
        if not os.path.exists(input_path):
            extraction_logger.error(f"Datei nicht gefunden: {input_path}")
            return set()

        # Wenn es ein Verzeichnis ist
        if os.path.isdir(input_path):
            new_words = set()
            total_words = set()
            
            for root, dirs, files in os.walk(input_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in [".txt", ".pdf", ".docx", ".png", ".jpg", ".jpeg"]:
                        file_path = os.path.join(root, file)
                        text = extract_text_from_file(file_path)
                        words = clean_and_split_text(text)
                        total_words.update(words)
                        
                        # Filtere Duplikate
                        new_words_from_file = {word for word in words 
                                             if word.lower() not in existing_words}
                        if new_words_from_file:
                            new_words.update(new_words_from_file)
                            extraction_logger.info(f"Datei {file}: {len(words)} Wörter gefunden, "
                                       f"davon {len(new_words_from_file)} neu")
            
            extraction_logger.info(f"Verzeichnis gesamt: {len(total_words)} Wörter gefunden, "
                        f"davon {len(new_words)} neu")
            return new_words

        # Wenn es eine einzelne Datei ist
        text = extract_text_from_file(input_path)
        words = clean_and_split_text(text)
        # Filtere Duplikate
        new_words = {word for word in words if word.lower() not in existing_words}
        
        extraction_logger.info(f"Datei gesamt: {len(words)} Wörter gefunden, "
                    f"davon {len(new_words)} neu")
        return new_words
            
    except Exception as e:
        extraction_logger.error(f"Unerwarteter Fehler: {str(e)}", exc_info=True)
        return set()
