# -*- coding: utf-8 -*-
import sys
import io
from src.translator import RussianTranslator

# Setze UTF-8 Encoding für stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_translator():
    translator = RussianTranslator()
    test_words = ['привет', 'книга', 'привет', 'книга', 'здравствуйте']  # Absichtlich doppelte Wörter
    print('\nStarte Test mit Wörtern:', test_words)
    print(f'Anzahl Wörter gesamt: {len(test_words)}')
    print(f'Anzahl einzigartige Wörter: {len(set(test_words))}')
    
    translations = translator.batch_translate(test_words, max_workers=2)
    print('\nÜbersetzungen:')
    for t in translations:
        print(f'\nOriginal: {t["original"]}')
        print(f'Übersetzung: {t["translation"]}')
        print(f'Wortart: {t["part_of_speech"]}')
        print(f'Beispiel DE: {t["example_de"]}')
        print(f'Beispiel RU: {t["example_ru"]}')
        print(f'Grammatik: {t["grammar_info"]}')

if __name__ == '__main__':
    test_translator()
