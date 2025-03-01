"""
Translation module for Russian words.

This module provides functionality for translating Russian words to German,
with support for multiple translation providers and caching.
"""
import re
import os
import json
import time
import requests
import logging
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, TypedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from functools import wraps

from src.config import TRANSLATION_LOG_FILE, ROOT_DIR
from src.utils import TranslationError

# Logger for this module
logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = ROOT_DIR / 'cache'
CACHE_DB = CACHE_DIR / 'translation_cache.db'

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True, parents=True)


class TranslationResult(TypedDict, total=False):
    """Type definition for translation results."""
    original: str
    translation: str
    part_of_speech: str
    grammatical_case: str
    example_ru: str
    example_de: str


def retry_with_backoff(max_retries: int = 3, initial_backoff: float = 1.0, 
                      backoff_factor: float = 2.0):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        initial_backoff: Initial backoff time in seconds
        backoff_factor: Factor to increase backoff time with each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            backoff = initial_backoff
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded: {str(e)}")
                        raise
                    
                    logger.warning(f"Retry {retries}/{max_retries} after error: {str(e)}")
                    logger.warning(f"Backing off for {backoff:.2f} seconds")
                    time.sleep(backoff)
                    backoff *= backoff_factor
            
            # This should never be reached due to the raise in the except block
            return None
        return wrapper
    return decorator


class TranslationCache:
    """Cache for translation results to avoid redundant API calls."""
    
    def __init__(self, db_path: Union[str, Path] = CACHE_DB):
        """
        Initialize the translation cache.
        
        Args:
            db_path: Path to the SQLite database file for caching
        """
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the cache database."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    word TEXT PRIMARY KEY,
                    provider TEXT,
                    result TEXT,
                    timestamp INTEGER
                )
            """)
            conn.commit()
            logger.debug(f"Translation cache initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing translation cache: {e}")
        finally:
            conn.close()
    
    def get(self, word: str, provider: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached translation result.
        
        Args:
            word: The word to look up
            provider: The translation provider
            
        Returns:
            Cached translation result or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT result FROM translations WHERE word = ? AND provider = ?",
                (word.lower(), provider)
            )
            row = cursor.fetchone()
            if row:
                logger.debug(f"Cache hit for '{word}' using provider '{provider}'")
                return json.loads(row[0])
            logger.debug(f"Cache miss for '{word}' using provider '{provider}'")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
        finally:
            conn.close()
    
    def set(self, word: str, provider: str, result: Dict[str, Any]) -> None:
        """
        Store a translation result in the cache.
        
        Args:
            word: The word being translated
            provider: The translation provider
            result: The translation result
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO translations (word, provider, result, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (word.lower(), provider, json.dumps(result), int(time.time()))
            )
            conn.commit()
            logger.debug(f"Cached translation for '{word}' using provider '{provider}'")
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            conn.rollback()
        finally:
            conn.close()


class TranslationProvider(ABC):
    """Abstract base class for translation providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the translation provider."""
        pass
    
    @abstractmethod
    def translate(self, word: str) -> Optional[TranslationResult]:
        """
        Translate a word from Russian to German.
        
        Args:
            word: The Russian word to translate
            
        Returns:
            Translation result or None if translation failed
        """
        pass


class OpenRouterTranslationProvider(TranslationProvider):
    """Translation provider using OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "google/gemini-2.0-flash-lite-001an"):
        """
        Initialize the OpenRouter translation provider.
        
        Args:
            api_key: OpenRouter API key (defaults to environment variable)
            model: Model to use for translation
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise TranslationError("OpenRouter API Key not found. Please check .env file.")
        
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/OpenRouterTeam/openrouter",
            "X-Title": "Russian-Anki-Translator",
        }
        logger.info(f"OpenRouter translation provider initialized with model {model}")
    
    @property
    def name(self) -> str:
        """Get the name of the translation provider."""
        return "openrouter"
    
    @retry_with_backoff(max_retries=3, initial_backoff=2.0)
    def translate(self, word: str) -> Optional[TranslationResult]:
        """
        Translate a word from Russian to German using OpenRouter API.
        
        Args:
            word: The Russian word to translate
            
        Returns:
            Translation result or None if translation failed
        """
        logger.info(f"Translating '{word}' using OpenRouter")
        
        # Updated prompt instructing a strict JSON response
        prompt = (
            "You are a professional Russian-to-German translator. Translate the given Russian word into German. "
            "When providing Russian examples use stresses over the characters which indicate the stress position of the word.\n"
            "You MUST respond ONLY with a valid JSON object in the following format, and nothing else. "
            "Do not include any extra text or explanations before or after the JSON. Ensure the JSON is well-formed. "
            "The JSON object should be enclosed in code block delimiters (triple backticks) and should not contain any other formatting.\n"
            "Example JSON Response:\n"
            '{"translation": "dein", "part_of_speech": "Possessivpronomen", '
            '"grammatical_case": "Nominativ, Genitiv, Dativ, Akkusativ (abhängig von Fall, Geschlecht und Numerus des Bezugswortes)", '
            '"example_ru": "Э́то твой кот.", "example_de": "Das ist deine Katze."}\n'
            f"Russian word: {word}"
        )
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": prompt
                        }
                    ]
                },
                timeout=30  # Add timeout to prevent hanging requests
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip()
                return self._parse_response(content, word)
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise TranslationError(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"Request error translating '{word}': {str(e)}"
            logger.error(error_msg)
            raise TranslationError(error_msg) from e
    
    def _parse_response(self, content: str, word: str) -> TranslationResult:
        """
        Parse the API response to extract translation data.
        
        Args:
            content: The API response content
            word: The original word
            
        Returns:
            Parsed translation result
        """
        # Remove any leading characters before the JSON
        content = content[content.find('{'):]

        # Check if the response is encapsulated in a code block
        if content.startswith("```json"):
            content = content[7:].strip()
        elif content.startswith("```"):
            content = content[3:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()

        # Try to parse the response as JSON
        try:
            translation_data = json.loads(content)
            # Ensure the returned data includes the original word
            translation_data["original"] = word
            
            # Normalize keys (some models might return grammatical_case instead of grammatical case)
            if "grammatical_case" in translation_data and "grammatical case" not in translation_data:
                translation_data["grammatical case"] = translation_data.pop("grammatical_case")
                
            logger.info(f"Translation successful: {translation_data}")
            return translation_data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON directly from response: {content}")

            # Fallback: try to extract JSON-like text using boundaries
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                try:
                    translation_data = json.loads(json_str)
                    translation_data["original"] = word
                    logger.info(f"Fallback JSON parsing successful: {translation_data}")
                    return translation_data
                except json.JSONDecodeError as e:
                    logger.error(f"Fallback JSON parsing failed: {str(e)}")
            
            # Final fallback: return raw text in a dictionary
            fallback = {
                "translation": content, 
                "part_of_speech": "", 
                "grammatical case": "", 
                "example_ru": "", 
                "example_de": "", 
                "original": word
            }
            logger.info("Returning fallback translation data as raw text.")
            return fallback


class RussianTranslator:
    """Main translator class with support for multiple providers and caching."""
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize the Russian translator.
        
        Args:
            use_cache: Whether to use translation caching
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize cache
        self.use_cache = use_cache
        if use_cache:
            self.cache = TranslationCache()
        
        # Initialize providers (default to OpenRouter)
        self.providers: List[TranslationProvider] = [
            OpenRouterTranslationProvider()
        ]
        
        logger.info(f"RussianTranslator initialized with {len(self.providers)} providers")
        
    def is_russian_word(self, word: str) -> bool:
        """
        Check if a word contains Russian characters.
        
        Args:
            word: The word to check
            
        Returns:
            True if the word contains Russian characters, False otherwise
        """
        russian_pattern = re.compile(r'[А-Яа-я]')
        is_russian = bool(russian_pattern.search(word))
        logger.debug(f"Word check: '{word}' is{'' if is_russian else ' not'} Russian")
        return is_russian
    
    def clean_word(self, word: str) -> str:
        """
        Remove special characters and whitespace.
        
        Args:
            word: The word to clean
            
        Returns:
            Cleaned word
        """
        original = word
        cleaned = word.strip().lower()
        if original != cleaned:
            logger.debug(f"Word cleaned: '{original}' -> '{cleaned}'")
        return cleaned
    
    def translate_word(self, word: str) -> Optional[TranslationResult]:
        """
        Translate a single word and return a dictionary with translation data.
        
        Args:
            word: The Russian word to translate
            
        Returns:
            Translation result or None if translation failed
        """
        if not word or not self.is_russian_word(word):
            logger.warning(f"Skipping translation for non-Russian or empty word: {word}")
            return None
            
        word = self.clean_word(word)
        logger.info(f"Translating word: {word}")
        
        # Check cache first if enabled
        if self.use_cache:
            for provider in self.providers:
                cached_result = self.cache.get(word, provider.name)
                if cached_result:
                    logger.info(f"Using cached translation for '{word}'")
                    return cached_result
        
        # Try each provider in order
        for provider in self.providers:
            try:
                result = provider.translate(word)
                if result:
                    # Cache the result if caching is enabled
                    if self.use_cache:
                        self.cache.set(word, provider.name, result)
                    return result
            except Exception as e:
                logger.error(f"Provider {provider.name} failed to translate '{word}': {str(e)}")
        
        # If all providers failed, return None
        logger.error(f"All translation providers failed for '{word}'")
        return None
    
    def batch_translate(self, words: List[str], batch_size: int = 10, max_workers: int = 5) -> List[TranslationResult]:
        """
        Translate a list of words in parallel.
        
        Args:
            words: List of words to translate
            batch_size: Number of words per batch
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of translation results
        """
        if not words:
            return []
            
        # Deduplicate the words
        unique_words = list(set(words))
        logger.info(f"Starting parallel batch translation of {len(unique_words)} unique words with {max_workers} workers")
        translations = []
        
        # Process words in batches in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a list of futures for the translations
            futures = {executor.submit(self.translate_word, word): word for word in unique_words}
            
            # Collect the results
            for future in as_completed(futures):
                word = futures[future]
                try:
                    translation = future.result()
                    if translation:
                        translations.append(translation)
                except Exception as e:
                    logger.error(f"Error translating '{word}': {str(e)}")
                    
        logger.info(f"Parallel batch translation completed. {len(translations)}/{len(unique_words)} translations created.")
        return translations


# Example usage:
if __name__ == "__main__":
    # Configure logging for standalone execution
    log_handler = logging.FileHandler(TRANSLATION_LOG_FILE, encoding='utf-8')
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)
    
    # Test the translator
    logger.info("Starting translator test")
    translator = RussianTranslator()
    
    test_words = ["привет", "книга", "test", "здравствуйте"]
    logger.info(f"Testing with words: {test_words}")
    
    print("Testing translations:")
    for word in test_words:
        result = translator.translate_word(word)
        if result:
            print(f"\nOriginal: {word}")
            print(f"Translation: {result['translation']}")
        else:
            print(f"\nError translating '{word}'")
    
    logger.info("Translator test completed")

# Configure module logger when imported
if not logger.handlers:
    log_handler = logging.FileHandler(TRANSLATION_LOG_FILE, encoding='utf-8')
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)

# Load environment variables when imported
load_dotenv()

# Create cache directory when imported
CACHE_DIR.mkdir(exist_ok=True, parents=True)

# Initialize default translator instance for module-level access
default_translator = RussianTranslator()

def translate_word(word: str) -> Optional[TranslationResult]:
    """
    Module-level function to translate a single word.
    
    Args:
        word: The Russian word to translate
        
    Returns:
        Translation result or None if translation failed
    """
    return default_translator.translate_word(word)

def batch_translate(words: List[str], batch_size: int = 10, max_workers: int = 5) -> List[TranslationResult]:
    """
    Module-level function to translate a list of words in parallel.
    
    Args:
        words: List of words to translate
        batch_size: Number of words per batch
        max_workers: Maximum number of parallel workers
        
    Returns:
        List of translation results
    """
    return default_translator.batch_translate(words, batch_size, max_workers)

def is_russian_word(word: str) -> bool:
    """
    Module-level function to check if a word contains Russian characters.
    
    Args:
        word: The word to check
        
    Returns:
        True if the word contains Russian characters, False otherwise
    """
    return default_translator.is_russian_word(word)

def clean_word(word: str) -> str:
    """
    Module-level function to clean a word.
    
    Args:
        word: The word to clean
        
    Returns:
        Cleaned word
    """
    return default_translator.clean_word(word)

# Backward compatibility
RussianTranslator.translate = RussianTranslator.translate_word

# Cleanup translation_logger references for backward compatibility
translation_logger = logger

# Ensure cache directory exists
if not CACHE_DIR.exists():
    CACHE_DIR.mkdir(parents=True)

# Initialize cache database
if not CACHE_DB.exists():
    TranslationCache()._init_db()

# Load environment variables
if not os.getenv('OPENROUTER_API_KEY'):
    load_dotenv()
    if not os.getenv('OPENROUTER_API_KEY'):
        logger.warning("OPENROUTER_API_KEY not found in environment variables")

# Ensure backward compatibility
try:
    # Create a default translator instance
    default_translator = RussianTranslator()
except Exception as e:
    logger.error(f"Error initializing default translator: {str(e)}")
    default_translator = None

def translate_word_compat(word):
    """Backward compatibility function for translate_word."""
    if default_translator:
        try:
            return default_translator.translate_word(word)
        except Exception as e:
            logger.error(f"Error in translate_word_compat: {str(e)}")
    return None
