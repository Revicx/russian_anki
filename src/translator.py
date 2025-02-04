"""
Translation module for Russian words.
"""
import re
import os
import json
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from src.config import TRANSLATION_LOG_FILE

# Configure Translation Logger
translation_logger = logging.getLogger('Translator')
translation_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File Handler for translations
fh = logging.FileHandler(TRANSLATION_LOG_FILE, encoding='utf-8')
fh.setFormatter(formatter)
translation_logger.addHandler(fh)

# Load environment variables
load_dotenv()

class RussianTranslator:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            translation_logger.error("OpenRouter API Key not found!")
            raise ValueError("OpenRouter API Key not found. Please check .env file.")
        
        translation_logger.info("RussianTranslator initialized")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/OpenRouterTeam/openrouter",
            "X-Title": "Russian-Anki-Translator",
        }
        
    def is_russian_word(self, word):
        """Check if a word contains Russian characters."""
        russian_pattern = re.compile(r'[А-Яа-я]')
        is_russian = bool(russian_pattern.search(word))
        translation_logger.debug(f"Word check: '{word}' is{'' if is_russian else ' not'} Russian")
        return is_russian
    
    def clean_word(self, word):
        """Remove special characters and whitespace."""
        original = word
        cleaned = word.strip().lower()
        if original != cleaned:
            translation_logger.debug(f"Word cleaned: '{original}' -> '{cleaned}'")
        return cleaned
    
    def translate_word(self, word):
        """Translate a single word."""
        if not word or not self.is_russian_word(word):
            translation_logger.warning(f"Skipping translation for non-Russian or empty word: {word}")
            return None
            
        word = self.clean_word(word)
        translation_logger.info(f"Translating word: {word}")
        
        prompt = """You are a professional Russian to English translator. Translate the given Russian word to English. Respond with ONLY the English translation, nothing else.
        
Special instructions:
1. Correct typos in the Russian word silently
2. Do not provide any additional explanations outside of the translation
3. The example sentence should show the word in a typical context
4. Grammar information as a single string with \\n for new lines
5. Stick strictly to the translation format without line breaks in strings

Russian word: {word}"""
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": "anthropic/claude-3.5-haiku-20241022:beta",
                    "messages": [
                        {
                            "role": "system",
                            "content": prompt.format(word=word)
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                
                # Find the JSON part of the response
                try:
                    # Search for the first { and last }
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = content[start:end]
                        translation_data = json.loads(json_str)
                        translation_logger.info(f"Translation successful: {translation_data}")
                        return translation_data
                    else:
                        translation_logger.error("No JSON found in the response")
                        return None
                except json.JSONDecodeError as e:
                    translation_logger.error(f"JSON Parse Error: {str(e)}\nContent: {content}")
                    return None
            else:
                translation_logger.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            translation_logger.error(f"Error translating '{word}': {str(e)}")
            return None
            
    def batch_translate(self, words, batch_size=10, max_workers=5):
        """Translate a list of words in parallel."""
        if not words:
            return []
            
        # Deduplicate the words
        unique_words = list(set(words))
        translation_logger.info(f"Starting parallel batch translation of {len(unique_words)} unique words with {max_workers} workers")
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
                    translation_logger.error(f"Error translating '{word}': {str(e)}")
                    
        translation_logger.info(f"Parallel batch translation completed. {len(translations)}/{len(unique_words)} translations created.")
        return translations

# Example usage:
if __name__ == "__main__":
    translation_logger.info("Starting translator test")
    translator = RussianTranslator()
    
    test_words = ["привет", "книга", "test", "здравствуйте"]
    translation_logger.info(f"Testing with words: {test_words}")
    
    print("Testing translations:")
    for word in test_words:
        result = translator.translate_word(word)
        if result:
            print(f"\nOriginal: {word}")
            print(f"Translation: {result['translation']}")
        else:
            print(f"\nError translating '{word}'")
    
    translation_logger.info("Translator test completed")
