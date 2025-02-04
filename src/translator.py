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

# Konfiguriere Translation Logger
translation_logger = logging.getLogger('Translator')
translation_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File Handler für Übersetzungen
fh = logging.FileHandler(TRANSLATION_LOG_FILE, encoding='utf-8')
fh.setFormatter(formatter)
translation_logger.addHandler(fh)

# Lade Umgebungsvariablen
load_dotenv()

class RussianTranslator:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            translation_logger.error("OpenRouter API Key nicht gefunden!")
            raise ValueError("OpenRouter API Key nicht gefunden. Bitte .env Datei überprüfen.")
        
        translation_logger.info("RussianTranslator initialisiert")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/OpenRouterTeam/openrouter",
            "X-Title": "Russian-Anki-Translator",
        }
        
    def is_russian_word(self, word):
        """Überprüft, ob ein Wort russische Zeichen enthält."""
        russian_pattern = re.compile(r'[А-Яа-я]')
        is_russian = bool(russian_pattern.search(word))
        translation_logger.debug(f"Wortprüfung: '{word}' ist{'' if is_russian else ' nicht'} russisch")
        return is_russian
    
    def clean_word(self, word):
        """Entfernt Sonderzeichen und Whitespace."""
        original = word
        cleaned = word.strip().lower()
        if original != cleaned:
            translation_logger.debug(f"Wort bereinigt: '{original}' -> '{cleaned}'")
        return cleaned
    
    def translate_word(self, word):
        """Übersetzt ein einzelnes Wort."""
        if not word or not self.is_russian_word(word):
            translation_logger.warning(f"Wort übersprungen (nicht russisch oder leer): {word}")
            return None
            
        word = self.clean_word(word)
        translation_logger.info(f"Übersetze Wort: {word}")
        
        prompt = f"""Du bist ein Russisch-Deutsch Übersetzer. Übersetze das folgende russische Wort ins Deutsche.
Gib die Antwort AUSSCHLIESSLICH im folgenden JSON-Format zurück, OHNE zusätzliche Erklärungen oder Hinweise:
{{
    "original": "das russische Wort",
    "translation": "die deutsche Übersetzung",
    "part_of_speech": "Wortart mit zusätzlichen Informationen",
    "example_de": "Ein Beispielsatz auf Deutsch",
    "example_ru": "Der gleiche Beispielsatz auf Russisch",
    "grammar_info": "Grammatikalische Informationen in einem einzelnen String mit \\n für neue Zeilen:\\n- Bei Verben: Konjugation in Präsens, Präteritum\\n- Bei Substantiven: Genus, Plural\\n- Bei Adjektiven: Deklination\\n- Bei Adverbien: Steigerungsformen wenn möglich"
}}

Spezielle Anweisungen:
1. Korrigiere Tippfehler im russischen Wort stillschweigend
2. Gib KEINE zusätzlichen Erklärungen außerhalb des JSON
3. Der Beispielsatz sollte das Wort in einem typischen Kontext zeigen
4. Grammatik-Info als einzelner String mit \\n für neue Zeilen
5. Halte dich STRIKT an das JSON-Format ohne Zeilenumbrüche in Strings

Russisches Wort: {word}"""
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": "anthropic/claude-3.5-haiku-20241022:beta",
                    "messages": [
                        {
                            "role": "system",
                            "content": prompt
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                
                # Finde den JSON-Teil der Antwort
                try:
                    # Suche nach dem ersten { und letzten }
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = content[start:end]
                        translation_data = json.loads(json_str)
                        translation_logger.info(f"Übersetzung erfolgreich: {translation_data}")
                        return translation_data
                    else:
                        translation_logger.error("Kein JSON in der Antwort gefunden")
                        return None
                except json.JSONDecodeError as e:
                    translation_logger.error(f"JSON Parse Error: {str(e)}\nContent: {content}")
                    return None
            else:
                translation_logger.error(f"API Fehler: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            translation_logger.error(f"Fehler bei der Übersetzung von '{word}': {str(e)}")
            return None
            
    def batch_translate(self, words, batch_size=10, max_workers=5):
        """Übersetzt eine Liste von Wörtern parallel."""
        if not words:
            return []
            
        # Dedupliziere die Wörter
        unique_words = list(set(words))
        translation_logger.info(f"Starte parallele Batch-Übersetzung von {len(unique_words)} einzigartigen Wörtern mit {max_workers} Workern")
        translations = []
        
        # Verarbeite Wörter in Batches parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Erstelle eine Liste von Futures für die Übersetzungen
            futures = {executor.submit(self.translate_word, word): word for word in unique_words}
            
            # Sammle die Ergebnisse ein
            for future in as_completed(futures):
                word = futures[future]
                try:
                    translation = future.result()
                    if translation:
                        translations.append(translation)
                except Exception as e:
                    translation_logger.error(f"Fehler bei der Übersetzung von '{word}': {str(e)}")
                    
        translation_logger.info(f"Parallele Batch-Übersetzung abgeschlossen. {len(translations)}/{len(unique_words)} Übersetzungen erstellt.")
        return translations

# Beispielnutzung:
if __name__ == "__main__":
    translation_logger.info("Starte Übersetzer-Test")
    translator = RussianTranslator()
    
    test_words = ["привет", "книга", "test", "здравствуйте"]
    translation_logger.info(f"Teste mit Wörtern: {test_words}")
    
    print("Teste Übersetzungen:")
    for word in test_words:
        result = translator.translate_word(word)
        if result:
            print(f"\nOriginal: {word}")
            print(f"Übersetzung: {result['translation']}")
        else:
            print(f"\nFehler bei '{word}'")
    
    translation_logger.info("Übersetzer-Test abgeschlossen")
