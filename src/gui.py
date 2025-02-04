"""
GUI module for the application.
"""
import os
import logging
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from src.config import DEFAULT_DB_PATH, DEFAULT_OUTPUT_FILE
from src.text_extraction import extract_text_from_input
from src.translator import RussianTranslator
from src.anki_generator import create_anki_deck
from src.storage import store_new_words, init_db_sqlite

class VocabExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Russisch Vokabel Extraktor")
        self.setup_gui()
        
    def setup_gui(self):
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Dateiauswahl
        ttk.Label(main_frame, text="Dateien/Ordner:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Listbox für ausgewählte Dateien
        self.file_listbox = tk.Listbox(main_frame, width=60, height=10)
        self.file_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Scrollbar für Listbox
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Buttons für Dateiauswahl
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Button(button_frame, text="Dateien hinzufügen", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ordner hinzufügen", command=self.add_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Auswahl entfernen", command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Liste leeren", command=self.clear_list).pack(side=tk.LEFT, padx=5)
        
        # Speichermethode
        storage_frame = ttk.LabelFrame(main_frame, text="Speichermethode", padding="5")
        storage_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.storage_var = tk.StringVar(value="sqlite")
        ttk.Radiobutton(storage_frame, text="SQLite", variable=self.storage_var, 
                       value="sqlite").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(storage_frame, text="CSV", variable=self.storage_var,
                       value="csv").grid(row=0, column=1, padx=5)
        
        # Datenbankpfad
        self.db_path_var = tk.StringVar(value=DEFAULT_DB_PATH)
        ttk.Label(main_frame, text="Datenbank/CSV-Pfad:").grid(row=4, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.db_path_var, width=40).grid(row=4, column=1, sticky=tk.W)
        
        # Ausgabedatei für Anki
        self.output_var = tk.StringVar(value=DEFAULT_OUTPUT_FILE)
        ttk.Label(main_frame, text="Anki Ausgabedatei:").grid(row=5, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.output_var, width=40).grid(row=5, column=1, sticky=tk.W)
        
        # Start Button
        ttk.Button(main_frame, text="Start", command=self.start_processing).grid(row=6, column=0, columnspan=2, pady=10)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate', 
                                      variable=self.progress_var)
        self.progress.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Status Label
        self.status_var = tk.StringVar(value="Bereit")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=8, column=0, columnspan=2)
        
        # Initialize storage
        init_db_sqlite(self.db_path_var.get())
        
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Dateien auswählen",
            filetypes=[
                ("Unterstützte Dateien", "*.txt;*.pdf;*.docx;*.png;*.jpg;*.jpeg"),
                ("Text Dateien", "*.txt"),
                ("PDF Dateien", "*.pdf"),
                ("Word Dateien", "*.docx"),
                ("Bilder", "*.png;*.jpg;*.jpeg"),
                ("Alle Dateien", "*.*")
            ]
        )
        for file in files:
            if file not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, file)
                
    def add_directory(self):
        directory = filedialog.askdirectory(title="Ordner auswählen")
        if directory and directory not in self.file_listbox.get(0, tk.END):
            self.file_listbox.insert(tk.END, directory)
            
    def remove_selected(self):
        selection = self.file_listbox.curselection()
        for index in reversed(selection):
            self.file_listbox.delete(index)
            
    def clear_list(self):
        self.file_listbox.delete(0, tk.END)
        
    def start_processing(self):
        selected_items = self.file_listbox.get(0, tk.END)
        if not selected_items:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei oder einen Ordner aus.")
            return
            
        try:
            # Setze Progress Bar
            self.progress_var.set(0)
            total_steps = len(selected_items) + 2  # Dateien + Übersetzung + Anki
            step = 100.0 / total_steps
            current_progress = 0
            
            # Sammle Wörter aus allen ausgewählten Dateien
            all_words = set()
            for path in selected_items:
                self.status_var.set(f"Verarbeite: {os.path.basename(path)}")
                extracted_words = extract_text_from_input(path, self.storage_var.get(), self.db_path_var.get())
                all_words.update(word.lower() for word in extracted_words)
                current_progress += step
                self.progress_var.set(current_progress)
                self.root.update()
            
            if not all_words:
                messagebox.showinfo("Information", "Keine neuen russischen Wörter gefunden.")
                return
                
            # Übersetze Wörter
            self.status_var.set("Übersetze Wörter...")
            translator = RussianTranslator()
            translations = translator.batch_translate(sorted(list(all_words)))
            current_progress += step
            self.progress_var.set(current_progress)
            self.root.update()
            
            # Speichere neue Wörter
            store_new_words(self.storage_var.get(), self.db_path_var.get(), all_words)
            
            # Erstelle Anki Deck
            self.status_var.set("Erstelle Anki Deck...")
            create_anki_deck(translations, self.output_var.get())
            current_progress += step
            self.progress_var.set(100)
            self.root.update()
            
            self.status_var.set("Fertig!")
            messagebox.showinfo("Erfolg", 
                              f"{len(all_words)} neue Wörter verarbeitet.\n"
                              f"Anki Deck wurde erstellt: {self.output_var.get()}")
            
        except Exception as e:
            logging.error(f"Fehler bei der Verarbeitung: {str(e)}", exc_info=True)
            messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten:\n{str(e)}")
            self.status_var.set("Fehler aufgetreten")
        finally:
            self.progress_var.set(0)

def create_gui():
    """Create and run the GUI."""
    root = tk.Tk()
    app = VocabExtractorGUI(root)
    root.mainloop()
