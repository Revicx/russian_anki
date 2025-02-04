import sqlite3
import os
import shutil
import zipfile
import tempfile
import json

def find_russian_field_index(model):
    """Finde den Index des russischen Feldes im Modell"""
    if not model or 'flds' not in model:
        return 0
        
    for i, field in enumerate(model['flds']):
        name = field.get('name', '').lower()
        if 'russisch' in name or 'russian' in name or 'русский' in name:
            return i
    return 0  # Fallback auf das erste Feld

def remove_duplicates_from_anki_deck(apkg_path):
    # Temporäres Verzeichnis erstellen
    temp_dir = tempfile.mkdtemp()
    
    try:
        print(f"\nEntpacke {apkg_path} nach {temp_dir}")
        # APKG-Datei entpacken
        with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            print("Dateien im Archiv:")
            for info in zip_ref.filelist:
                print(f"- {info.filename} ({info.file_size} bytes)")
        
        # Verbindung zur SQLite-Datenbank herstellen
        db_path = os.path.join(temp_dir, 'collection.anki21')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Zeige Tabellen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nVerfügbare Tabellen:")
        for table in tables:
            print(f"- {table[0]}")
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  Anzahl Einträge: {count}")

        # Hole die Modelle aus der Collection
        print("\nLese Collection-Daten...")
        cursor.execute("SELECT * FROM col")
        col_data = cursor.fetchone()
        if col_data:
            print("Collection gefunden:")
            cursor.execute("SELECT * FROM col")
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            for col, val in zip(columns, row):
                if col in ['conf', 'models', 'decks', 'dconf', 'tags']:
                    print(f"{col}: {val[:100]}...")  # Zeige nur die ersten 100 Zeichen
                else:
                    print(f"{col}: {val}")
        
        models_json = col_data[9] if col_data else "{}"  # models ist das 10. Feld
        try:
            models = json.loads(models_json)
        except json.JSONDecodeError as e:
            print(f"\nFehler beim Parsen der Modelle: {e}")
            print("Erste 100 Zeichen des JSON:", models_json[:100])
            models = {}

        print("\nVerfügbare Modelle:")
        for model_id, model in models.items():
            print(f"\nModel ID: {model_id}")
            print(f"Name: {model.get('name')}")
            field_names = [f.get('name') for f in model.get('flds', [])]
            print(f"Felder: {field_names}")
            russian_index = find_russian_field_index(model)
            print(f"Russisches Feld gefunden an Position: {russian_index} ({field_names[russian_index] if field_names else 'unbekannt'})")

        # Hole alle Notizen
        cursor.execute("""
            SELECT id, flds, mid FROM notes
            ORDER BY sfld
        """)
        
        notes = cursor.fetchall()
        print(f"\nGefundene Karten insgesamt: {len(notes)}")
        
        if len(notes) == 0:
            print("\nKeine Karten gefunden! Überprüfe andere Tabellen...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                print(f"\nInhalt von {table_name}:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                columns = [description[0] for description in cursor.description]
                print("Spalten:", columns)
                rows = cursor.fetchall()
                for row in rows:
                    print("Zeile:", row)
        else:
            # Zeige Beispielkarten
            print("\nBeispiel Karteninhalte:")
            for note in notes[:5]:
                note_id, fields, model_id = note
                model = models.get(str(model_id))
                field_names = [f.get('name') for f in model.get('flds', [])] if model else []
                russian_index = find_russian_field_index(model) if model else 0
                
                print(f"\nKarte ID {note_id} (Model: {model.get('name') if model else 'Unbekannt'}):")
                fields_split = fields.split('\x1f')
                for i, field in enumerate(fields_split):
                    field_name = field_names[i] if i < len(field_names) else f"Feld {i}"
                    is_russian = " (Russisches Wort)" if i == russian_index else ""
                    print(f"{field_name}{is_russian}: {field}")
            
            # Finde Duplikate
            seen_words = {}  # Wort -> (note_id, fields)
            notes_to_delete = []
            
            for note in notes:
                note_id, fields, model_id = note
                model = models.get(str(model_id))
                russian_index = find_russian_field_index(model) if model else 0
                
                fields_split = fields.split('\x1f')
                if len(fields_split) > russian_index:
                    # Hole das russische Wort aus dem korrekten Feld
                    russian_word = fields_split[russian_index].strip().lower()
                    
                    if russian_word and russian_word in seen_words:
                        # Wenn das Wort bereits existiert, behalte die ältere Karte
                        existing_id, existing_fields = seen_words[russian_word]
                        notes_to_delete.append(note_id)
                        print(f"\nDuplikat gefunden für '{russian_word}':")
                        print(f"Original (ID {existing_id}): {existing_fields}")
                        print(f"Duplikat (ID {note_id}): {fields}")
                    else:
                        seen_words[russian_word] = (note_id, fields)
            
            print(f"\nGefundene Duplikate: {len(notes_to_delete)}")
            
            if notes_to_delete:
                # Backup der originalen APKG-Datei erstellen
                backup_path = apkg_path + '.backup'
                shutil.copy2(apkg_path, backup_path)
                print(f"Backup erstellt: {backup_path}")
                
                # Lösche Duplikate
                placeholders = ','.join('?' * len(notes_to_delete))
                cursor.execute(f"DELETE FROM notes WHERE id IN ({placeholders})", notes_to_delete)
                cursor.execute(f"DELETE FROM cards WHERE nid IN ({placeholders})", notes_to_delete)
                
                # Änderungen speichern
                conn.commit()
                
                # Neue APKG-Datei erstellen
                output_path = os.path.splitext(apkg_path)[0] + '_no_duplicates.apkg'
                with zipfile.ZipFile(output_path, 'w') as zip_ref:
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        zip_ref.write(file_path, os.path.basename(file_path))
                
                print(f"Duplikate wurden erfolgreich entfernt.")
                print(f"Neues Deck wurde gespeichert als: {output_path}")
            else:
                print("Keine Duplikate gefunden.")
            
    finally:
        # Aufräumen
        try:
            conn.close()
        except:
            pass
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    deck_path = "Russische Vokabeln.apkg"
    if os.path.exists(deck_path):
        remove_duplicates_from_anki_deck(deck_path)
    else:
        print(f"Fehler: Die Datei {deck_path} wurde nicht gefunden.")
