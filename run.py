#!/usr/bin/env python
"""
Starter script for the Russian Vocabulary Extractor.

This script sets up the Python path and launches the application.
It serves as the main entry point for both CLI and GUI modes.
"""
import sys
from pathlib import Path

def main():
    """
    Set up the environment and start the application.
    
    This function adds the project directory to the Python path
    and then imports and runs the main application.
    """
    # Add project directory to Python path
    project_dir = Path(__file__).parent.absolute()
    if project_dir not in sys.path:
        sys.path.insert(0, str(project_dir))
        
    # Import and start main application
    from src.main import cli
    
    # Run the CLI with system arguments
    cli()

if __name__ == '__main__':
    main()
