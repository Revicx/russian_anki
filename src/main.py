"""
Main entry point for the Russian Vocabulary Extractor application.
"""
import os
import sys
import argparse
import logging
import csv
from pathlib import Path

# Add src directory to Python path
src_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(src_dir)
if src_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.config import DEFAULT_DB_PATH, DEFAULT_OUTPUT_FILE, DEFAULT_LOG_FILE
from src.utils import setup_logging, check_dependencies
from src.text_extraction import extract_text_from_input
from src.translator import RussianTranslator
from src.anki_generator import create_anki_deck
from src.storage import store_new_words, init_db_sqlite
from src.gui import create_gui

def process_files(input_paths, storage='sqlite', storage_path=DEFAULT_DB_PATH, 
                 output_file=DEFAULT_OUTPUT_FILE):
    """Process files and create Anki deck."""
    try:
        # Sammle Wörter aus allen Dateien
        all_words = set()
        for path in input_paths:
            extracted_words = extract_text_from_input(path, storage, storage_path)
            all_words.update(word.lower() for word in extracted_words)
            
        if not all_words:
            logging.info("Keine neuen Wörter gefunden")
            return
            
        # Übersetze Wörter
        translator = RussianTranslator()
        translations = translator.batch_translate(sorted(list(all_words)))
        
        # Speichere neue Wörter
        store_new_words(storage, storage_path, all_words)
        
        # Erstelle Anki Deck
        create_anki_deck(translations, output_file)
        
        logging.info(f"Verarbeitung abgeschlossen. {len(all_words)} neue Wörter verarbeitet.")
        
    except Exception as e:
        logging.error(f"Fehler bei der Verarbeitung: {str(e)}", exc_info=True)
        raise

def init_app(storage, storage_path):
    """Initialize application."""
    if storage == 'sqlite':
        init_db_sqlite(storage_path)
    elif storage == 'csv' and not os.path.exists(storage_path):
        # Erstelle leere CSV mit Header
        with open(storage_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'translation', 'context'])

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Russische Vokabel Extraktion und Anki Deck Erstellung')
    parser.add_argument('--gui', action='store_true', help='Starte die grafische Benutzeroberfläche')
    parser.add_argument('--files', nargs='*', help='Zu verarbeitende Dateien oder Ordner')
    parser.add_argument('--storage', choices=['sqlite', 'csv'], default='sqlite',
                      help='Speichermethode (sqlite oder csv)')
    parser.add_argument('--storage-path', default=DEFAULT_DB_PATH,
                      help='Pfad zur Datenbank/CSV-Datei')
    parser.add_argument('--output', default=DEFAULT_OUTPUT_FILE,
                      help='Ausgabedatei für das Anki-Deck')
    parser.add_argument('--log-level', default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Log-Level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(getattr(logging, args.log_level), DEFAULT_LOG_FILE)
    
    # Check dependencies
    check_dependencies()
    
    # Initialize application
    init_app(args.storage, args.storage_path)
    
    try:
        if args.gui:
            create_gui()
        elif args.files:
            process_files(args.files, args.storage, args.storage_path, args.output)
        else:
            parser.print_help()
            
    except Exception as e:
        logging.error(f"Unerwarteter Fehler: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
