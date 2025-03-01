"""
Main entry point for the Russian Vocabulary Extractor application.

This module provides the command-line interface and main application logic
for extracting Russian words from various file formats, translating them,
and generating Anki decks for learning.
"""
import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Union
import click

from src.config import (
    DEFAULT_DB_PATH, DEFAULT_OUTPUT_FILE, DEFAULT_LOG_FILE,
    validate_config
)
from src.utils import (
    setup_logging, check_dependencies, safe_execute,
    RussianAnkiError, ConfigurationError, StorageError
)
from src.text_extraction import extract_text_from_input
from src.translator import RussianTranslator
from src.anki_generator import create_anki_deck
from src.storage import store_new_words, init_db_sqlite, get_vocab
from src.gui import create_gui

# Logger for this module
logger = logging.getLogger(__name__)

class AppContext:
    """Application context for managing state and dependencies."""
    
    def __init__(self, 
                storage_type: str = 'sqlite', 
                storage_path: Union[str, Path] = DEFAULT_DB_PATH,
                output_file: Union[str, Path] = DEFAULT_OUTPUT_FILE,
                log_level: int = logging.INFO):
        """
        Initialize application context.
        
        Args:
            storage_type: Type of storage ('sqlite' or 'csv')
            storage_path: Path to the storage file
            output_file: Path to the output Anki deck file
            log_level: Logging level
        """
        self.storage_type = storage_type
        self.storage_path = Path(storage_path)
        self.output_file = Path(output_file)
        self.log_level = log_level
        self.translator = RussianTranslator()
        
        # Initialize logging
        setup_logging(log_level, DEFAULT_LOG_FILE)
        
        # Validate configuration
        self.config_valid = validate_config()
        
        # Initialize storage
        self._init_storage()
        
    def _init_storage(self) -> None:
        """Initialize the storage system based on the selected type."""
        if self.storage_type == 'sqlite':
            init_db_sqlite(self.storage_path)
        elif self.storage_type == 'csv' and not self.storage_path.exists():
            # Create empty CSV with header
            with open(self.storage_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['word', 'translation', 'context'])
        
        logger.info(f"Storage initialized: {self.storage_type} at {self.storage_path}")


def process_files(input_paths: List[Union[str, Path]], 
                 app_context: AppContext) -> bool:
    """
    Process files and create Anki deck.
    
    Args:
        input_paths: List of file or directory paths to process
        app_context: Application context with configuration
        
    Returns:
        True if processing was successful, False otherwise
        
    Raises:
        RussianAnkiError: If there's an error during processing
    """
    logger.info(f"Processing {len(input_paths)} input paths")
    
    try:
        # Collect words from all files
        all_words = set()
        for path in input_paths:
            extracted_words = extract_text_from_input(
                path, app_context.storage_type, app_context.storage_path
            )
            all_words.update(word.lower() for word in extracted_words)
            
        if not all_words:
            logger.info("No new words found")
            return False
            
        # Translate words
        translations = app_context.translator.batch_translate(sorted(list(all_words)))
        
        # Store new words
        store_new_words(app_context.storage_type, app_context.storage_path, all_words)
        
        # Create Anki deck
        create_anki_deck(translations, app_context.output_file)
        
        logger.info(f"Processing completed. {len(all_words)} new words processed.")
        return True
        
    except Exception as e:
        error_msg = f"Error during file processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RussianAnkiError(error_msg) from e


# Click command group
@click.group()
@click.option('--storage', type=click.Choice(['sqlite', 'csv']), default='sqlite',
              help='Storage method (sqlite or csv)')
@click.option('--storage-path', type=click.Path(), default=str(DEFAULT_DB_PATH),
              help='Path to database/CSV file')
@click.option('--output', type=click.Path(), default=str(DEFAULT_OUTPUT_FILE),
              help='Output file for Anki deck')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              default='INFO', help='Logging level')
@click.pass_context
def cli(ctx: click.Context, storage: str, storage_path: str, output: str, log_level: str) -> None:
    """Russian Vocabulary Extractor and Anki Deck Creator."""
    # Create application context
    ctx.obj = AppContext(
        storage_type=storage,
        storage_path=storage_path,
        output_file=output,
        log_level=getattr(logging, log_level)
    )
    
    # Check dependencies
    deps = check_dependencies()
    if not all(deps.values()):
        logger.warning("Some dependencies are missing. Functionality may be limited.")


@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.pass_obj
def process(app_context: AppContext, files: List[str]) -> None:
    """Process files and create Anki deck."""
    if not files:
        logger.error("No files specified")
        return
    
    try:
        process_files(files, app_context)
    except RussianAnkiError as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.pass_obj
def gui(app_context: AppContext) -> None:
    """Start the graphical user interface."""
    create_gui()


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
