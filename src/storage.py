"""
Storage module for handling database operations (SQLite and CSV).
"""
import csv
import sqlite3
import logging

from src.config import DEFAULT_DB_PATH

def init_db_sqlite(db_path=DEFAULT_DB_PATH):
    """Initialize SQLite database with required schema."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS vocab (
                word TEXT PRIMARY KEY,
                translation TEXT,
                context TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        logging.error(f"Fehler bei der Initialisierung der SQLite DB {db_path}: {e}")
    finally:
        conn.close()

def get_existing_words_sqlite(db_path):
    """Get all existing words from SQLite database."""
    init_db_sqlite(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT DISTINCT lower(word) FROM vocab")  # Ensure we get lowercase unique words
        rows = c.fetchall()
        vocab = {row[0] for row in rows if row[0] is not None}  # Already lowercase from SQL
        logging.info(f"{len(vocab)} existierende Wörter in SQLite {db_path} gefunden.")
        return vocab
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Wörter aus SQLite {db_path}: {e}")
        return set()
    finally:
        conn.close()

def insert_new_words_sqlite(db_path, new_words):
    """Insert new words into SQLite database."""
    if not new_words:
        logging.info("Keine neuen Wörter zum Einfügen.")
        return
        
    init_db_sqlite(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Hole existierende Wörter für Duplikatscheck
        c.execute("SELECT DISTINCT lower(word) FROM vocab")
        existing = {row[0] for row in c.fetchall() if row[0] is not None}
        
        # Filtere und füge nur wirklich neue Wörter ein
        new_words_lower = {word.lower() for word in new_words}
        truly_new_words = new_words_lower - existing
        
        if not truly_new_words:
            logging.info("Alle Wörter existieren bereits in der Datenbank.")
            return
            
        # Füge neue Wörter ein
        for word in truly_new_words:
            try:
                c.execute("INSERT INTO vocab (word, translation, context) VALUES (?, ?, ?)",
                          (word, "", ""))
            except sqlite3.IntegrityError as e:
                logging.warning(f"Wort existiert bereits (Integrity Error): {word}")
                continue
            except Exception as e:
                logging.error(f"Fehler beim Einfügen von {word}: {e}")
                continue
                
        conn.commit()
        logging.info(f"{len(truly_new_words)} neue Wörter in SQLite {db_path} eingefügt.")
        
    except Exception as e:
        logging.error(f"Fehler beim Einfügen neuer Wörter: {e}")
        conn.rollback()
    finally:
        conn.close()

def read_vocab_csv(csv_path):
    """Read vocabulary from CSV file."""
    vocab = set()
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'word' in row and row['word']:
                    vocab.add(row['word'].lower())
    except FileNotFoundError:
        logging.warning(f"CSV-Datei nicht gefunden: {csv_path}")
    except Exception as e:
        logging.error(f"Fehler beim Lesen der CSV-Datei {csv_path}: {e}")
    return vocab

def append_new_words_csv(csv_path, new_words):
    """Append new words to CSV file."""
    try:
        # Prüfe, ob Datei existiert
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                pass
        except FileNotFoundError:
            # Erstelle neue Datei mit Header
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['word', 'translation', 'context'])
        
        # Füge neue Wörter hinzu
        with open(csv_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for word in new_words:
                writer.writerow([word.lower(), '', ''])
                
        logging.info(f"{len(new_words)} Wörter zur CSV-Datei {csv_path} hinzugefügt.")
        
    except Exception as e:
        logging.error(f"Fehler beim Schreiben in CSV-Datei {csv_path}: {e}")

def get_vocab(storage, storage_path):
    """Get vocabulary from specified storage."""
    if storage == 'csv':
        return read_vocab_csv(storage_path)
    elif storage == 'sqlite':
        return get_existing_words_sqlite(storage_path)
    else:
        logging.error("Ungültige Storage-Methode.")
        return set()

def store_new_words(storage, storage_path, new_words):
    """Store new words in specified storage."""
    if storage == 'csv':
        append_new_words_csv(storage_path, new_words)
    elif storage == 'sqlite':
        insert_new_words_sqlite(storage_path, new_words)
    else:
        logging.error("Ungültige Storage-Methode.")
