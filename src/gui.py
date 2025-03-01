import os
import logging
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading

from src.config import DEFAULT_DB_PATH, DEFAULT_OUTPUT_FILE
from src.text_extraction import extract_text_from_input
from src.translator import RussianTranslator
from src.anki_generator import create_anki_deck
from src.storage import store_new_words, init_db_sqlite

# Configure modern theme colors
COLORS = {
    "bg_dark": "#282c34",       # Dark background
    "bg_medium": "#353b48",     # Medium dark background
    "bg_light": "#3f4756",      # Light dark background
    "text": "#f5f6fa",          # Light text
    "text_dim": "#a4b0be",      # Dimmed text
    "primary": "#5dabf4",       # Blue accent
    "secondary": "#ff6b81",     # Orange/red secondary
    "success": "#2ed573",       # Success color
    "error": "#ff4757",         # Error color
    "border": "#576574",        # Border color
    "hover": "#4a5568"          # Hover color
}

class ModernTooltip:
    """Modern tooltip implementation for hover help text"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        
    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create a toplevel window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        frame = tk.Frame(self.tooltip, background=COLORS["bg_medium"], 
                      relief="solid", borderwidth=1)
        frame.pack()
        
        label = tk.Label(frame, text=self.text, background=COLORS["bg_medium"],
                      foreground=COLORS["text"], font=("Segoe UI", 9),
                      wraplength=250, justify="left", padx=8, pady=5)
        label.pack()
        
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class ScrollableFrame(tk.Frame):
    """Custom scrollable frame for file list"""
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, background=COLORS["bg_medium"], *args, **kwargs)
        
        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0,
                             background=COLORS["bg_medium"])
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", 
                                     command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, background=COLORS["bg_medium"])
        
        # Configure canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, 
                                                  anchor="nw")
        
        # Bind canvas resize to frame resize
        self.canvas.bind("<Configure>", self.resize_frame)
        
        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Configure scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def resize_frame(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
        
    def _on_mousewheel(self, event):
        if self.scrollbar.get() != (0.0, 1.0):  # Only scroll if there's content to scroll
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
    def destroy_bindings(self):
        self.canvas.unbind_all("<MouseWheel>")

class FileItemFrame(tk.Frame):
    """Frame representing a single file item in the list"""
    def __init__(self, parent, path, on_remove, *args, **kwargs):
        super().__init__(parent, background=COLORS["bg_light"], 
                        relief="solid", borderwidth=1, *args, **kwargs)
        self.path = path
        
        # File icon and name
        file_type = self.get_file_type_icon(path)
        file_name = os.path.basename(path) if os.path.isfile(path) else os.path.basename(path) + " (Folder)"
        
        # Container frame with padding
        content_frame = tk.Frame(self, background=COLORS["bg_light"], padx=10, pady=8)
        content_frame.pack(fill="both", expand=True)
        
        icon_label = tk.Label(content_frame, text=file_type, background=COLORS["bg_light"], 
                           foreground=COLORS["text"], font=("Segoe UI", 14))
        icon_label.pack(side="left", padx=(0, 10))
        
        # Truncate long names
        if len(file_name) > 40:
            display_name = file_name[:37] + "..."
        else:
            display_name = file_name
            
        name_label = tk.Label(content_frame, text=display_name, background=COLORS["bg_light"],
                           foreground=COLORS["text"], font=("Segoe UI", 10),
                           anchor="w")
        name_label.pack(side="left", fill="x", expand=True)
        
        # Show full path on hover
        ModernTooltip(name_label, path)
        
        # Remove button - using a modern rounded X button
        remove_btn = tk.Button(content_frame, text="×", font=("Segoe UI", 11, "bold"),
                            background=COLORS["bg_light"], foreground=COLORS["secondary"],
                            relief="flat", borderwidth=0, highlightthickness=0,
                            activebackground=COLORS["hover"], activeforeground=COLORS["secondary"],
                            command=lambda: on_remove(self))
        remove_btn.pack(side="right")
        
        # Add hover effect
        self.bind("<Enter>", lambda e: self.config(background=COLORS["hover"]))
        self.bind("<Leave>", lambda e: self.config(background=COLORS["bg_light"]))
        content_frame.bind("<Enter>", lambda e: self.config(background=COLORS["hover"]))
        content_frame.bind("<Leave>", lambda e: self.config(background=COLORS["bg_light"]))
        
    def get_file_type_icon(self, path):
        """Return an appropriate icon based on file type"""
        if os.path.isdir(path):
            return "📁"
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.txt', '.md']:
            return "📄"
        elif ext == '.pdf':
            return "📑"
        elif ext == '.docx':
            return "📝"
        elif ext in ['.png', '.jpg', '.jpeg']:
            return "🖼️"
        else:
            return "📋"

class ModernButton(tk.Button):
    """Custom modern button with hover effects"""
    def __init__(self, parent, text, command=None, primary=False, **kwargs):
        self.primary = primary
        
        if primary:
            bg_color = COLORS["primary"]
            fg_color = COLORS["text"]
            hover_bg = self.adjust_color(COLORS["primary"], 20)
            active_bg = self.adjust_color(COLORS["primary"], -20)
            font = ("Segoe UI", 11, "bold")
            padding = 12
        else:
            bg_color = COLORS["bg_light"]
            fg_color = COLORS["text"]
            hover_bg = COLORS["hover"]
            active_bg = self.adjust_color(COLORS["bg_light"], -10)
            font = ("Segoe UI", 9)
            padding = 7
            
        super().__init__(
            parent, text=text, command=command,
            background=bg_color, foreground=fg_color,
            activebackground=active_bg, activeforeground=fg_color,
            relief="flat", borderwidth=0, highlightthickness=0,
            font=font, padx=padding, pady=padding//2,
            **kwargs
        )
        
        self.hover_bg = hover_bg
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, e):
        self.config(background=self.hover_bg)
        
    def on_leave(self, e):
        if self.primary:
            self.config(background=COLORS["primary"])
        else:
            self.config(background=COLORS["bg_light"])
    
    @staticmethod
    def adjust_color(hex_color, amount):
        """Brighten or darken a color by the given amount"""
        r = max(0, min(255, int(hex_color[1:3], 16) + amount))
        g = max(0, min(255, int(hex_color[3:5], 16) + amount))
        b = max(0, min(255, int(hex_color[5:7], 16) + amount))
        return f"#{r:02x}{g:02x}{b:02x}"

class ModernEntry(tk.Entry):
    """Custom modern entry with better styling"""
    def __init__(self, parent, textvariable=None, **kwargs):
        super().__init__(
            parent, textvariable=textvariable,
            background=COLORS["bg_light"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat", borderwidth=8,
            highlightthickness=1, highlightbackground=COLORS["border"],
            highlightcolor=COLORS["primary"],
            font=("Segoe UI", 9),
            **kwargs
        )
        
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        
    def on_focus_in(self, event):
        self.config(highlightbackground=COLORS["primary"])
        
    def on_focus_out(self, event):
        self.config(highlightbackground=COLORS["border"])

class VocabExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Russian Vocabulary Extractor")
        self.root.geometry("900x1200")
        self.root.minsize(900, 1200)
        
        # Set window background
        self.root.configure(bg=COLORS["bg_dark"])
        
        # Variables
        self.file_items = []
        self.storage_var = tk.StringVar(value="sqlite")
        self.db_path_var = tk.StringVar(value=DEFAULT_DB_PATH)
        self.output_var = tk.StringVar(value=DEFAULT_OUTPUT_FILE)
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar()
        
        # Configure styles for ttk elements
        self.setup_styles()
        
        # Build GUI
        self.setup_gui()
        
        # Center window
        self.center_window()
        
        # Initialize database
        init_db_sqlite(self.db_path_var.get())
        
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        
        # Configure progress bar
        style.configure("TProgressbar", thickness=10, 
                       background=COLORS["primary"], troughcolor=COLORS["bg_light"])
        
        # Configure Radio buttons
        style.configure("TRadiobutton", 
                      background=COLORS["bg_dark"], 
                      foreground=COLORS["text"],
                      indicatorcolor=COLORS["primary"])
        style.map("TRadiobutton",
                background=[("active", COLORS["bg_dark"])],
                foreground=[("active", COLORS["text"])])
        
        # Configure Scrollbar
        style.configure("TScrollbar", 
                      background=COLORS["bg_light"], 
                      troughcolor=COLORS["bg_medium"],
                      arrowcolor=COLORS["text"])
        
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Main container with padding
        main_container = tk.Frame(self.root, background=COLORS["bg_dark"], padx=25, pady=25)
        main_container.pack(fill="both", expand=True)
        
        # App header
        header_frame = tk.Frame(main_container, background=COLORS["bg_dark"])
        header_frame.pack(fill="x", pady=(0, 20))
        
        # App icon/logo
        icon_label = tk.Label(header_frame, text="🇷🇺", font=("Segoe UI", 28), 
                           background=COLORS["bg_dark"], foreground=COLORS["text"])
        icon_label.pack(side="left", padx=(0, 15))
        
        # App title
        title_frame = tk.Frame(header_frame, background=COLORS["bg_dark"])
        title_frame.pack(side="left")
        
        title_label = tk.Label(title_frame, text="Russian Vocabulary Extractor", 
                            font=("Segoe UI", 20, "bold"), 
                            background=COLORS["bg_dark"], foreground=COLORS["primary"])
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(title_frame, text="Extract, translate, and create Anki decks", 
                               font=("Segoe UI", 10), 
                               background=COLORS["bg_dark"], foreground=COLORS["text_dim"])
        subtitle_label.pack(anchor="w")
        
        # Files section
        self.create_section_header(main_container, "Files & Folders", "📄")
        
        # Files list container
        files_container = tk.Frame(main_container, background=COLORS["bg_medium"], 
                                relief="flat", padx=2, pady=2)
        files_container.pack(fill="both", expand=True, pady=(0, 15))
        
        # Create scrollable file list
        self.files_scroll_frame = ScrollableFrame(files_container)
        self.files_scroll_frame.pack(fill="both", expand=True)
        
        # Empty state when no files
        self.empty_label = tk.Label(self.files_scroll_frame.scrollable_frame, 
                                  text="Add files or folders to begin", 
                                  background=COLORS["bg_medium"], foreground=COLORS["text_dim"],
                                  font=("Segoe UI", 10), pady=40)
        self.empty_label.pack(fill="both", expand=True)
        
        # File buttons
        files_button_frame = tk.Frame(main_container, background=COLORS["bg_dark"])
        files_button_frame.pack(fill="x", pady=(0, 20))
        
        add_file_btn = ModernButton(files_button_frame, text="Add Files", command=self.add_files)
        add_file_btn.pack(side="left", padx=(0, 8))
        ModernTooltip(add_file_btn, "Select text, PDF, Word, or image files containing Russian text")
        
        add_dir_btn = ModernButton(files_button_frame, text="Add Folder", command=self.add_directory)
        add_dir_btn.pack(side="left")
        ModernTooltip(add_dir_btn, "Select a folder containing supported files")
        
        clear_btn = ModernButton(files_button_frame, text="Clear All", command=self.clear_list)
        clear_btn.pack(side="right")
        
        # Storage options section
        self.create_section_header(main_container, "Storage Options", "💾")
        
        options_frame = tk.Frame(main_container, background=COLORS["bg_dark"])
        options_frame.pack(fill="x", pady=(0, 20))
        
        # First column: storage type
        storage_frame = tk.Frame(options_frame, background=COLORS["bg_dark"])
        storage_frame.pack(side="left", fill="y", padx=(0, 20))
        
        tk.Label(storage_frame, text="Storage Type:", background=COLORS["bg_dark"], 
               foreground=COLORS["text"], font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 8))
        
        radio_frame = tk.Frame(storage_frame, background=COLORS["bg_dark"])
        radio_frame.pack(fill="x")
        
        ttk.Radiobutton(radio_frame, text="SQLite Database", 
                      variable=self.storage_var, value="sqlite").pack(anchor="w", pady=2)
        ttk.Radiobutton(radio_frame, text="CSV File", 
                      variable=self.storage_var, value="csv").pack(anchor="w", pady=2)
        
        # Second column: file paths
        paths_frame = tk.Frame(options_frame, background=COLORS["bg_dark"])
        paths_frame.pack(side="left", fill="both", expand=True)
        
        # Database path
        db_frame = tk.Frame(paths_frame, background=COLORS["bg_dark"])
        db_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(db_frame, text="Database/CSV Path:", background=COLORS["bg_dark"], 
               foreground=COLORS["text"], font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 8))
        
        db_entry_frame = tk.Frame(db_frame, background=COLORS["bg_dark"])
        db_entry_frame.pack(fill="x")
        
        self.db_entry = ModernEntry(db_entry_frame, textvariable=self.db_path_var)
        self.db_entry.pack(side="left", fill="x", expand=True)
        
        browse_db_btn = ModernButton(db_entry_frame, text="Browse", command=self.browse_db_path)
        browse_db_btn.pack(side="right", padx=(8, 0))
        
        # Output file
        output_frame = tk.Frame(paths_frame, background=COLORS["bg_dark"])
        output_frame.pack(fill="x")
        
        tk.Label(output_frame, text="Anki Output File:", background=COLORS["bg_dark"], 
               foreground=COLORS["text"], font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 8))
        
        output_entry_frame = tk.Frame(output_frame, background=COLORS["bg_dark"])
        output_entry_frame.pack(fill="x")
        
        self.output_entry = ModernEntry(output_entry_frame, textvariable=self.output_var)
        self.output_entry.pack(side="left", fill="x", expand=True)
        
        browse_output_btn = ModernButton(output_entry_frame, text="Browse", command=self.browse_output_path)
        browse_output_btn.pack(side="right", padx=(8, 0))
        
        # Action buttons
        action_frame = tk.Frame(main_container, background=COLORS["bg_dark"])
        action_frame.pack(fill="x", pady=(15, 0))
        
        # Create a container to center the button
        center_frame = tk.Frame(action_frame, background=COLORS["bg_dark"])
        center_frame.pack(pady=15)
        
        # Start button
        self.start_button = ModernButton(center_frame, text="Extract Vocabulary", primary=True,
                                      command=self.start_processing)
        self.start_button.pack()
        
        # Progress section
        progress_frame = tk.Frame(main_container, background=COLORS["bg_dark"])
        progress_frame.pack(fill="x", pady=(15, 0))
        
        self.progress = ttk.Progressbar(progress_frame, length=400, mode='determinate', 
                                     variable=self.progress_var)
        self.progress.pack(fill="x", pady=(0, 10))
        
        status_frame = tk.Frame(progress_frame, background=COLORS["bg_dark"])
        status_frame.pack(fill="x")
        
        # Status indicator - dot + text
        self.status_indicator = tk.Label(status_frame, text="●", 
                                      background=COLORS["bg_dark"], foreground=COLORS["text_dim"],
                                      font=("Segoe UI", 10))
        self.status_indicator.pack(side="left", padx=(0, 5))
        
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, 
                                  background=COLORS["bg_dark"], foreground=COLORS["text_dim"],
                                  font=("Segoe UI", 10))
        self.status_label.pack(side="left")
        
    def create_section_header(self, parent, text, icon=None):
        """Create a section header with icon and text"""
        header_frame = tk.Frame(parent, background=COLORS["bg_dark"])
        header_frame.pack(fill="x", pady=(10, 10), anchor="w")
        
        if icon:
            icon_label = tk.Label(header_frame, text=icon, background=COLORS["bg_dark"], 
                               foreground=COLORS["text"], font=("Segoe UI", 14))
            icon_label.pack(side="left", padx=(0, 8))
        
        text_label = tk.Label(header_frame, text=text, background=COLORS["bg_dark"], 
                           foreground=COLORS["text"], font=("Segoe UI", 12, "bold"))
        text_label.pack(side="left")
        
        # Add separator line
        separator = tk.Frame(parent, height=1, background=COLORS["border"])
        separator.pack(fill="x", pady=(0, 15))
        
    def update_empty_state(self):
        """Show or hide the empty state based on file count"""
        if self.file_items:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(fill="both", expand=True)
    
    def add_files(self):
        """Add files to the list"""
        files = filedialog.askopenfilenames(
            title="Select Files",
            filetypes=[
                ("Supported Files", "*.txt;*.pdf;*.docx;*.png;*.jpg;*.jpeg;*.md"),
                ("Text Files", "*.txt;*.md"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx"),
                ("Image Files", "*.png;*.jpg;*.jpeg"),
                ("All Files", "*.*")
            ]
        )
        
        for file in files:
            if not any(item.path == file for item in self.file_items):
                self.add_file_item(file)
        
        self.update_empty_state()
                
    def add_directory(self):
        """Add a directory to the list"""
        directory = filedialog.askdirectory(title="Select Folder")
        if directory and not any(item.path == directory for item in self.file_items):
            self.add_file_item(directory)
            self.update_empty_state()
    
    def add_file_item(self, path):
        """Add a file item to the scrollable list"""
        file_item = FileItemFrame(
            self.files_scroll_frame.scrollable_frame, 
            path, 
            self.remove_file_item
        )
        file_item.pack(fill="x", padx=10, pady=5)
        self.file_items.append(file_item)
    
    def remove_file_item(self, item):
        """Remove a file item from the list"""
        if item in self.file_items:
            self.file_items.remove(item)
            item.destroy()
            self.update_empty_state()
    
    def clear_list(self):
        """Clear all items from the file list"""
        for item in self.file_items:
            item.destroy()
        self.file_items = []
        self.update_empty_state()
    
    def browse_db_path(self):
        """Browse for database/CSV path"""
        file_types = [("SQLite Database", "*.db")] if self.storage_var.get() == "sqlite" else [("CSV Files", "*.csv")]
        path = filedialog.asksaveasfilename(
            title="Select Database/CSV File",
            filetypes=file_types,
            defaultextension=".db" if self.storage_var.get() == "sqlite" else ".csv"
        )
        if path:
            self.db_path_var.set(path)
    
    def browse_output_path(self):
        """Browse for Anki output file"""
        path = filedialog.asksaveasfilename(
            title="Select Anki Output File",
            filetypes=[("Anki Package", "*.apkg")],
            defaultextension=".apkg"
        )
        if path:
            self.output_var.set(path)
    
    def update_progress(self, value, status=None):
        """Update progress bar and status safely from any thread"""
        self.root.after(0, lambda: self.progress_var.set(value))
        if status:
            self.root.after(0, lambda: self.status_var.set(status))
            
            # Update indicator color based on status
            if "Error" in status:
                self.root.after(0, lambda: self.status_indicator.config(foreground=COLORS["error"]))
            elif "Complete" in status:
                self.root.after(0, lambda: self.status_indicator.config(foreground=COLORS["success"]))
            elif "Ready" in status:
                self.root.after(0, lambda: self.status_indicator.config(foreground=COLORS["text_dim"]))
            else:
                self.root.after(0, lambda: self.status_indicator.config(foreground=COLORS["primary"]))
                
        self.root.update_idletasks()
    
    def start_processing(self):
        """Start the vocabulary extraction process in a separate thread"""
        if not self.file_items:
            messagebox.showwarning("Warning", "Please select at least one file or folder.")
            return
        
        # Disable the button while processing
        self.start_button.config(state="disabled")
        
        # Start processing in a separate thread
        self.update_progress(0, "Starting processing...")
        processing_thread = threading.Thread(target=self.process_files)
        processing_thread.daemon = True
        processing_thread.start()
    
    def process_files(self):
        """Process files in a separate thread"""
        try:
            paths = [item.path for item in self.file_items]
            total_steps = len(paths) + 2  # Files + Translation + Anki
            step = 100.0 / total_steps
            current_progress = 0
            
            # Collect words from all selected files
            all_words = set()
            for path in paths:
                file_name = os.path.basename(path)
                self.update_progress(current_progress, f"Processing: {file_name}")
                
                extracted_words = extract_text_from_input(path, self.storage_var.get(), self.db_path_var.get())
                all_words.update(word.lower() for word in extracted_words)
                
                current_progress += step
                self.update_progress(current_progress)
            
            if not all_words:
                self.root.after(0, lambda: messagebox.showinfo("Information", "No new Russian words found."))
                self.update_progress(0, "Ready")
                self.root.after(0, lambda: self.start_button.config(state="normal"))
                return
            
            # Translate words
            self.update_progress(current_progress, f"Translating {len(all_words)} words...")
            translator = RussianTranslator()
            translations = translator.batch_translate(sorted(list(all_words)))
            
            current_progress += step
            self.update_progress(current_progress)
            
            # Store new words
            self.update_progress(current_progress, "Storing words in database...")
            store_new_words(self.storage_var.get(), self.db_path_var.get(), all_words)
            
            # Create Anki deck
            self.update_progress(current_progress, "Creating Anki deck...")
            create_anki_deck(translations, self.output_var.get())
            
            self.update_progress(100, "Complete!")
            
            # Show success message in the main thread
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"{len(all_words)} new Russian words processed.\n"
                f"Anki deck created: {os.path.basename(self.output_var.get())}"
            ))
            
            # Reset progress
            self.root.after(2000, lambda: self.update_progress(0, "Ready"))
            
        except Exception as e:
            logging.error(f"Error in processing: {str(e)}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror(
                "Error", 
                f"An error occurred:\n{str(e)}"
            ))
            self.update_progress(0, "Error occurred")
        finally:
            self.root.after(0, lambda: self.start_button.config(state="normal"))
    
    def on_close(self):
        """Clean up before closing application"""
        self.files_scroll_frame.destroy_bindings()
        self.root.destroy()

def create_gui():
    """Create and run the GUI."""
    root = tk.Tk()
    app = VocabExtractorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()