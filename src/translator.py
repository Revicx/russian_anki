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
        """Translate a single word and return a dictionary with translation data."""
        if not word or not self.is_russian_word(word):
            translation_logger.warning(f"Skipping translation for non-Russian or empty word: {word}")
            return None
            
        word = self.clean_word(word)
        translation_logger.info(f"Translating word: {word}")
        
        # Updated prompt instructing a strict JSON response
        prompt = (
            "You are a professional Russian-to-German translator. Translate the given Russian word into German. When providing russian examples use stresses over the characters which indicate the stress position of the word.\n"
            "You MUST respond ONLY with a valid JSON object in the following format, and nothing else. Do not include any extra text or explanations before or after the JSON. Ensure the JSON is well-formed. The JSON object should be enclosed in an code block delimiters (triple backticks) and should not contain any other formatting.\n"
            "Example JSON Response:\n"
            '{"translation": "dein", "part_of_speech": "Possessivpronomen", "grammatical case": "Nominativ, Genitiv, Dativ, Akkusativ (abhängig von Fall, Geschlecht und Numerus des Bezugswortes)", "example_ru": "Э́то твой кот.","example_de": "Das ist deine Katze."}\n'
            f"Russian word: {word}"
        )
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [
                        {
                            "role": "system",
                            "content": prompt
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip()

                # Remove any leading characters before the JSON
                content = content[content.find('{'):]

                # Check if the response is encapsulated in a code block
                if content.startswith("```json"):
                    content = content[6:].strip()
                elif content.startswith("```"):
                    content = content[3:].strip()
                if content.endswith("```"):
                    content = content[:-3].strip()

                # Try to parse the response as JSON
                try:
                    translation_data = json.loads(content)
                    # Ensure the returned data includes the original word.
                    translation_data["original"] = word
                    translation_logger.info(f"Translation successful: {translation_data}")
                    return translation_data
                except json.JSONDecodeError:
                    translation_logger.error(f"Failed to parse JSON directly from response: {content}")

                    # Fallback: try to extract JSON-like text using boundaries
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = content[start:end]
                        try:
                            translation_data = json.loads(json_str)
                            translation_data["original"] = word
                            translation_logger.info(f"Fallback JSON parsing successful: {translation_data}")
                            return translation_data
                        except json.JSONDecodeError as e:
                            translation_logger.error(f"Fallback JSON parsing failed: {str(e)}")
                    # Final fallback: return raw text in a dictionary with the original word included.
                    fallback = {"translation": content, "part_of_speech": "", "grammatical case": "", "example_ru": "", "example_de": "", "original": word}
                    translation_logger.info("Returning fallback translation data as raw text.")
                    return fallback
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
