"""
Module for generating Anki decks from translated words.

This module provides functionality to create Anki decks from translated Russian words,
with customizable card templates and styling.
"""
import random
import logging
from pathlib import Path
from typing import List, Dict, Union
import genanki

from src.utils import AnkiGenerationError

# Logger for this module
logger = logging.getLogger(__name__)

# Card CSS styles
CARD_STYLE = """
.card {
    font-family: Arial, sans-serif;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}
.russian, .german { 
    font-size: 28px;
    color: #2196F3;
    margin-bottom: 10px;
}
.translation {
    font-size: 24px;
    color: #4CAF50;
    margin-bottom: 8px;
}
.part-of-speech {
    color: #9E9E9E;
    margin-bottom: 5px;
}
.grammar {
    color: #757575;
    margin-bottom: 15px;
}
.example {
    color: #666;
    margin-top: 15px;
}
.example-ru, .example-de {
    margin-bottom: 5px;
}
hr {
    border: none;
    border-top: 1px solid #E0E0E0;
    margin: 10px 0;
}
"""

# Card templates
RUSSIAN_TO_GERMAN_TEMPLATE = {
    "name": "Russian -> German",
    "qfmt": """
        <div class="russian">{{Russian}}</div>
    """,
    "afmt": """
        <div class="russian">{{Russian}}</div>
        <hr>
        <div class="translation">{{German}}</div>
        <div class="part-of-speech"><i>{{PartOfSpeech}}</i></div>
        <div class="grammar"><small>{{Grammar}}</small></div>
        <hr>
        <div class="example">
            <div class="example-ru">{{Example_RU}}</div>
            <div class="example-de">{{Example_DE}}</div>
        </div>
        <style>
        {style}
        </style>
    """.format(style=CARD_STYLE)
}

GERMAN_TO_RUSSIAN_TEMPLATE = {
    "name": "German -> Russian",
    "qfmt": """
        <div class="german">{{German}}</div>
    """,
    "afmt": """
        <div class="german">{{German}}</div>
        <hr>
        <div class="translation">{{Russian}}</div>
        <div class="part-of-speech"><i>{{PartOfSpeech}}</i></div>
        <div class="grammar"><small>{{Grammar}}</small></div>
        <hr>
        <div class="example">
            <div class="example-de">{{Example_DE}}</div>
            <div class="example-ru">{{Example_RU}}</div>
        </div>
        <style>
        {style}
        </style>
    """.format(style=CARD_STYLE)
}

# Field definitions
CARD_FIELDS = [
    {"name": "Russian"},
    {"name": "German"},
    {"name": "PartOfSpeech"},
    {"name": "Grammar"},
    {"name": "Example_DE"},
    {"name": "Example_RU"}
]

class AnkiDeckGenerator:
    """Class for generating Anki decks from translated words."""
    
    def __init__(self, deck_name: str = "Russian Vocabulary"):
        """
        Initialize the Anki deck generator.
        
        Args:
            deck_name: Name of the Anki deck to create
        """
        self.deck_name = deck_name
        self.deck_id = random.randint(1 << 30, 1 << 31)
        self.model_id = random.randint(1 << 30, 1 << 31)
        logger.debug(f"Initialized AnkiDeckGenerator with Deck ID: {self.deck_id}, Model ID: {self.model_id}")
    
    def create_model(self) -> genanki.Model:
        """
        Create an Anki note model with templates.
        
        Returns:
            A genanki.Model instance with configured templates
        """
        return genanki.Model(
            self.model_id,
            "Russian <-> German",
            fields=CARD_FIELDS,
            templates=[
                RUSSIAN_TO_GERMAN_TEMPLATE,
                GERMAN_TO_RUSSIAN_TEMPLATE
            ]
        )
    
    def add_notes_to_deck(self, 
                         deck: genanki.Deck, 
                         model: genanki.Model, 
                         translations: List[Dict[str, str]]) -> int:
        """
        Add notes to the Anki deck from translations.
        
        Args:
            deck: The genanki.Deck to add notes to
            model: The genanki.Model to use for notes
            translations: List of translation dictionaries
            
        Returns:
            Number of successfully added notes
        """
        added_count = 0
        
        for i, trans in enumerate(translations, 1):
            try:
                # Map translation fields to Anki fields
                note = genanki.Note(
                    model=model,
                    fields=[
                        str(trans.get("original", "") or ""),
                        str(trans.get("translation", "") or ""),
                        str(trans.get("part_of_speech", "") or ""),
                        str(trans.get("grammatical case", "") or ""),
                        str(trans.get("example_de", "") or ""),
                        str(trans.get("example_ru", "") or "")   
                    ]
                )
                deck.add_note(note)
                added_count += 1
                logger.info(f"Card {i} added: {trans.get('original', '')} -> {trans.get('translation', '')} (Russian <-> German)")
                
            except Exception as e:
                logger.error(f"Error adding card {i}: {str(e)}")
        
        return added_count


def create_anki_deck(translations: List[Dict[str, str]], output_file: Union[str, Path]) -> bool:
    """
    Create an Anki deck from translated words.
    
    Args:
        translations: List of translation dictionaries
        output_file: Path to save the Anki deck
        
    Returns:
        True if deck was created successfully, False otherwise
        
    Raises:
        AnkiGenerationError: If there's an error creating the deck
    """
    logger.info(f"Creating Anki deck with {len(translations)} cards")
    
    try:
        # Create generator, deck and model
        generator = AnkiDeckGenerator("Russian Vocabulary")
        deck = genanki.Deck(generator.deck_id, generator.deck_name)
        model = generator.create_model()
        
        # Add notes to deck
        added_count = generator.add_notes_to_deck(deck, model, translations)
        
        if added_count == 0:
            logger.warning("No cards were added to the deck")
            return False
            
        # Save the deck
        output_path = Path(output_file)
        genanki.Package(deck).write_to_file(str(output_path))
        logger.info(f"Anki deck successfully created: {output_path}")
        return True
        
    except Exception as e:
        error_msg = f"Error creating Anki deck: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise AnkiGenerationError(error_msg) from e
