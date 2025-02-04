#!/usr/bin/env python
"""
Starter script for the Russian Vocabulary Extractor.
"""
import os
import sys
from pathlib import Path

def main():
    # Füge das Projektverzeichnis zum Python-Pfad hinzu
    project_dir = os.path.dirname(os.path.abspath(__file__))
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
        
    # Importiere und starte die Hauptanwendung
    from src.main import main
    main()

if __name__ == '__main__':
    main()
