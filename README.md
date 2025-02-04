# Russian to Anki

Ein Python-Tool zur automatischen Erstellung von Anki-Karteikarten aus russischen Texten. Das Tool unterstützt verschiedene Dateiformate und bietet eine benutzerfreundliche grafische Oberfläche.

## Hauptfunktionen

- **Unterstützte Eingabeformate:**
  - PDF-Dokumente (Text und gescannte PDFs via OCR)
  - Word-Dokumente (`.docx`)
  - Bilder (`.png`, `.jpg`, `.jpeg`, `.bmp`)
  - Text-Dateien (`.txt`)

- **Automatische Texterkennung:**
  - Intelligente OCR für gescannte PDFs und Bilder
  - Automatische Bildvorverarbeitung für bessere Ergebnisse
  - Unterstützung für kyrillische Schrift

- **Anki-Integration:**
  - Automatische Deck-Erstellung
  - Erkennung und Entfernung von Duplikaten
  - Export im `.apkg`-Format
  - Anpassbare Kartenvorlagen

## Installation

### 1. Systemvoraussetzungen

- Python 3.x
- Tesseract OCR (für Bildverarbeitung)
- Poppler (für PDF-Verarbeitung)

### 2. Tesseract OCR Installation

1. Herunterladen von: https://github.com/UB-Mannheim/tesseract/wiki
2. Installation ausführen
3. Sicherstellen, dass Tesseract zum System-PATH hinzugefügt ist

### 3. Poppler Installation

1. Herunterladen von: https://github.com/oschwartz10612/poppler-windows/releases/
2. Archiv entpacken
3. Den `bin`-Ordner zum System-PATH hinzufügen

### 4. Python-Umgebung einrichten

1. Repository klonen:
   ```bash
   git clone https://github.com/Auron040/russian_anki.git
   cd russian_anki
   ```

2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

## Verwendung

1. Programm starten:
   ```bash
   python run.py
   ```

2. In der GUI:
   - Dateien oder Ordner auswählen
   - Gewünschte Einstellungen vornehmen
   - "Verarbeiten" klicken

3. Das generierte Anki-Deck (`russisch_deck.apkg`) in Anki importieren

## Projektstruktur

- `src/`: Hauptquellcode
  - `gui.py`: Grafische Benutzeroberfläche
  - `text_extraction.py`: Text- und OCR-Verarbeitung
  - `anki_generator.py`: Anki-Deck-Erstellung
  - `translator.py`: Übersetzungsfunktionen
  - `storage.py`: Datenbank-Management

- `requirements.txt`: Python-Abhängigkeiten
- `setup_dependencies.bat`: Hilfsskript für die Installation
- `.env`: Konfigurationsdatei (muss erstellt werden)

## Konfiguration

Erstellen Sie eine `.env`-Datei mit folgenden Einstellungen:
```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\Path\To\poppler-xx\bin
```

## Fehlerbehebung

- **OCR funktioniert nicht**: Überprüfen Sie die Tesseract-Installation und den PATH
- **PDF-Verarbeitung schlägt fehl**: Stellen Sie sicher, dass Poppler korrekt installiert ist
- **Encoding-Fehler**: Überprüfen Sie die Textcodierung der Eingabedateien (UTF-8 empfohlen)

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## Mitwirken

Beiträge sind willkommen! Bitte erstellen Sie einen Pull Request oder ein Issue für Verbesserungsvorschläge.
