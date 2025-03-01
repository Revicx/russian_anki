"""
Storage module for handling database operations (SQLite and CSV).

This module provides a data access layer for storing and retrieving
vocabulary words using either SQLite or CSV storage backends.
"""
import csv
import sqlite3
import logging
import os
import contextlib
from pathlib import Path
from typing import Set, List, Dict, Union, Iterator
from dataclasses import dataclass

from src.config import DEFAULT_DB_PATH
from src.utils import StorageError

# Logger for this module
logger = logging.getLogger(__name__)

# Connection pool for SQLite
_SQLITE_CONNECTIONS: Dict[str, sqlite3.Connection] = {}

@dataclass
class VocabEntry:
    """Data class representing a vocabulary entry."""
    word: str
    translation: str = ""
    context: str = ""
    
    def validate(self) -> bool:
        """
        Validate the vocabulary entry.
        
        Returns:
            True if the entry is valid, False otherwise
        """
        return bool(self.word and isinstance(self.word, str))


class BaseStorage:
    """Base class for storage implementations."""
    
    def __init__(self, storage_path: Union[str, Path]):
        """
        Initialize the storage.
        
        Args:
            storage_path: Path to the storage file
        """
        self.storage_path = Path(storage_path)
    
    def get_words(self) -> Set[str]:
        """
        Get all words from storage.
        
        Returns:
            Set of words
        """
        raise NotImplementedError("Subclasses must implement get_words")
    
    def add_words(self, words: Set[str]) -> int:
        """
        Add new words to storage.
        
        Args:
            words: Set of words to add
            
        Returns:
            Number of words added
        """
        raise NotImplementedError("Subclasses must implement add_words")
    
    def add_entries(self, entries: List[VocabEntry]) -> int:
        """
        Add vocabulary entries to storage.
        
        Args:
            entries: List of vocabulary entries to add
            
        Returns:
            Number of entries added
        """
        raise NotImplementedError("Subclasses must implement add_entries")


class SQLiteStorage(BaseStorage):
    """SQLite storage implementation."""
    
    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to the SQLite database file
        """
        super().__init__(db_path)
        self.init_db()
    
    def init_db(self) -> None:
        """Initialize SQLite database with required schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vocab (
                        word TEXT PRIMARY KEY,
                        translation TEXT,
                        context TEXT
                    )
                """)
                conn.commit()
            except Exception as e:
                error_msg = f"Error initializing SQLite database {self.storage_path}: {e}"
                logger.error(error_msg)
                raise StorageError(error_msg) from e
    
    @contextlib.contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """
        Get a SQLite connection from the pool or create a new one.
        
        Returns:
            SQLite connection
        """
        db_path_str = str(self.storage_path)
        
        # Check if connection exists in pool
        if db_path_str in _SQLITE_CONNECTIONS:
            conn = _SQLITE_CONNECTIONS[db_path_str]
            try:
                # Test if connection is still valid
                conn.execute("SELECT 1")
            except sqlite3.Error:
                # Connection is invalid, create a new one
                conn = sqlite3.connect(db_path_str)
                _SQLITE_CONNECTIONS[db_path_str] = conn
        else:
            # Create new connection and add to pool
            conn = sqlite3.connect(db_path_str)
            _SQLITE_CONNECTIONS[db_path_str] = conn
        
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise StorageError(f"SQLite operation failed: {e}") from e

    def get_words(self) -> Set[str]:
        """
        Get all existing words from SQLite database.
        
        Returns:
            Set of words
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT DISTINCT lower(word) FROM vocab")
                rows = cursor.fetchall()
                vocab = {row[0] for row in rows if row[0] is not None}
                logger.info(f"Found {len(vocab)} existing words in SQLite {self.storage_path}")
                return vocab
            except Exception as e:
                error_msg = f"Error retrieving words from SQLite {self.storage_path}: {e}"
                logger.error(error_msg)
                raise StorageError(error_msg) from e
    
    def add_words(self, words: Set[str]) -> int:
        """
        Add new words to SQLite database.
        
        Args:
            words: Set of words to add
            
        Returns:
            Number of words added
        """
        if not words:
            logger.info("No new words to insert.")
            return 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Get existing words for duplicate check
                cursor.execute("SELECT DISTINCT lower(word) FROM vocab")
                existing = {row[0] for row in cursor.fetchall() if row[0] is not None}
                
                # Filter and add only truly new words
                new_words_lower = {word.lower() for word in words}
                truly_new_words = new_words_lower - existing
                
                if not truly_new_words:
                    logger.info("All words already exist in the database.")
                    return 0
                
                # Add new words
                added_count = 0
                for word in truly_new_words:
                    try:
                        cursor.execute(
                            "INSERT INTO vocab (word, translation, context) VALUES (?, ?, ?)",
                            (word, "", "")
                        )
                        added_count += 1
                    except sqlite3.IntegrityError:
                        logger.warning(f"Word already exists (Integrity Error): {word}")
                    except Exception as e:
                        logger.error(f"Error inserting word {word}: {e}")
                
                conn.commit()
                logger.info(f"Added {added_count} new words to SQLite {self.storage_path}")
                return added_count
                
            except Exception as e:
                error_msg = f"Error adding new words: {e}"
                logger.error(error_msg)
                conn.rollback()
                raise StorageError(error_msg) from e
    
    def add_entries(self, entries: List[VocabEntry]) -> int:
        """
        Add vocabulary entries to SQLite database.
        
        Args:
            entries: List of vocabulary entries to add
            
        Returns:
            Number of entries added
        """
        if not entries:
            logger.info("No entries to add.")
            return 0
        
        # Validate entries
        valid_entries = [entry for entry in entries if entry.validate()]
        if len(valid_entries) < len(entries):
            logger.warning(f"Skipped {len(entries) - len(valid_entries)} invalid entries")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                added_count = 0
                for entry in valid_entries:
                    try:
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO vocab (word, translation, context)
                            VALUES (?, ?, ?)
                            """,
                            (entry.word.lower(), entry.translation, entry.context)
                        )
                        added_count += 1
                    except Exception as e:
                        logger.error(f"Error adding entry {entry.word}: {e}")
                
                conn.commit()
                logger.info(f"Added {added_count} entries to SQLite {self.storage_path}")
                return added_count
                
            except Exception as e:
                error_msg = f"Error adding entries: {e}"
                logger.error(error_msg)
                conn.rollback()
                raise StorageError(error_msg) from e


class CSVStorage(BaseStorage):
    """CSV storage implementation."""
    
    def __init__(self, csv_path: Union[str, Path]):
        """
        Initialize CSV storage.
        
        Args:
            csv_path: Path to the CSV file
        """
        super().__init__(csv_path)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Ensure the CSV file exists with proper headers."""
        if not self.storage_path.exists():
            os.makedirs(self.storage_path.parent, exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['word', 'translation', 'context'])
            logger.info(f"Created new CSV file: {self.storage_path}")
    
    def get_words(self) -> Set[str]:
        """
        Get all words from CSV file.
        
        Returns:
            Set of words
        """
        vocab = set()
        try:
            with open(self.storage_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'word' in row and row['word']:
                        vocab.add(row['word'].lower())
            logger.info(f"Found {len(vocab)} existing words in CSV {self.storage_path}")
            return vocab
        except FileNotFoundError:
            logger.warning(f"CSV file not found: {self.storage_path}")
            self._ensure_file_exists()
            return set()
        except Exception as e:
            error_msg = f"Error reading CSV file {self.storage_path}: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e
    
    def add_words(self, words: Set[str]) -> int:
        """
        Add new words to CSV file.
        
        Args:
            words: Set of words to add
            
        Returns:
            Number of words added
        """
        if not words:
            logger.info("No new words to add.")
            return 0
        
        try:
            # Get existing words to avoid duplicates
            existing_words = self.get_words()
            new_words = {word.lower() for word in words} - existing_words
            
            if not new_words:
                logger.info("All words already exist in the CSV file.")
                return 0
            
            # Add new words
            with open(self.storage_path, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                for word in new_words:
                    writer.writerow([word, '', ''])
            
            logger.info(f"Added {len(new_words)} words to CSV file {self.storage_path}")
            return len(new_words)
            
        except Exception as e:
            error_msg = f"Error writing to CSV file {self.storage_path}: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e
    
    def add_entries(self, entries: List[VocabEntry]) -> int:
        """
        Add vocabulary entries to CSV file.
        
        Args:
            entries: List of vocabulary entries to add
            
        Returns:
            Number of entries added
        """
        if not entries:
            logger.info("No entries to add.")
            return 0
        
        # Validate entries
        valid_entries = [entry for entry in entries if entry.validate()]
        if len(valid_entries) < len(entries):
            logger.warning(f"Skipped {len(entries) - len(valid_entries)} invalid entries")
        
        try:
            # Read existing entries to create a new file with updates
            existing_entries = {}
            try:
                with open(self.storage_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'word' in row and row['word']:
                            existing_entries[row['word'].lower()] = row
            except FileNotFoundError:
                self._ensure_file_exists()
            
            # Update with new entries
            for entry in valid_entries:
                existing_entries[entry.word.lower()] = {
                    'word': entry.word.lower(),
                    'translation': entry.translation,
                    'context': entry.context
                }
            
            # Write back all entries
            with open(self.storage_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['word', 'translation', 'context'])
                writer.writeheader()
                for entry_dict in existing_entries.values():
                    writer.writerow(entry_dict)
            
            logger.info(f"Added/updated {len(valid_entries)} entries in CSV file {self.storage_path}")
            return len(valid_entries)
            
        except Exception as e:
            error_msg = f"Error updating CSV file {self.storage_path}: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e


# Factory functions for backward compatibility
def get_storage(storage_type: str, storage_path: Union[str, Path]) -> BaseStorage:
    """
    Get a storage instance based on the specified type.
    
    Args:
        storage_type: Type of storage ('sqlite' or 'csv')
        storage_path: Path to the storage file
        
    Returns:
        Storage instance
    """
    if storage_type == 'sqlite':
        return SQLiteStorage(storage_path)
    elif storage_type == 'csv':
        return CSVStorage(storage_path)
    else:
        error_msg = f"Invalid storage type: {storage_type}"
        logger.error(error_msg)
        raise StorageError(error_msg)


# Compatibility functions for existing code
def init_db_sqlite(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> None:
    """Initialize SQLite database with required schema (compatibility function)."""
    SQLiteStorage(db_path).init_db()

def get_existing_words_sqlite(db_path: Union[str, Path]) -> Set[str]:
    """Get all existing words from SQLite database (compatibility function)."""
    return SQLiteStorage(db_path).get_words()

def insert_new_words_sqlite(db_path: Union[str, Path], new_words: Set[str]) -> int:
    """Insert new words into SQLite database (compatibility function)."""
    return SQLiteStorage(db_path).add_words(new_words)

def read_vocab_csv(csv_path: Union[str, Path]) -> Set[str]:
    """Read vocabulary from CSV file (compatibility function)."""
    return CSVStorage(csv_path).get_words()

def append_new_words_csv(csv_path: Union[str, Path], new_words: Set[str]) -> int:
    """Append new words to CSV file (compatibility function)."""
    return CSVStorage(csv_path).add_words(new_words)

def get_vocab(storage: str, storage_path: Union[str, Path]) -> Set[str]:
    """Get vocabulary from specified storage (compatibility function)."""
    return get_storage(storage, storage_path).get_words()

def store_new_words(storage: str, storage_path: Union[str, Path], new_words: Set[str]) -> int:
    """Store new words in specified storage (compatibility function)."""
    return get_storage(storage, storage_path).add_words(new_words)
