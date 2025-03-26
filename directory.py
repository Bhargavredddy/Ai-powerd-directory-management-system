import os
import shutil
import json
import logging
import PyPDF2
import hashlib
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import magic  # For MIME-type detection

logging.basicConfig(filename='file_organizer.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

CATEGORIES = {
    "Documents": {
        "keywords": ["report", "invoice", "letter", "contract"],
        "extensions": ["doc", "docx", "pdf", "txt"],
        "mime_types": ["application/pdf", "text/plain", "application/msword"]
    },
    "Images": {
        "keywords": ["photo", "image", "picture"],
        "extensions": ["jpg", "png", "jpeg", "gif"],
        "mime_types": ["image/jpeg", "image/png", "image/gif"]
    },
    "Media": {
        "keywords": ["video", "audio", "movie"],
        "extensions": ["mp4", "mp3", "wav"],
        "mime_types": ["video/mp4", "audio/mpeg", "audio/wav"]
    },
    "Code": {
        "keywords": ["script", "code", "program"],
        "extensions": ["py", "js", "html", "cpp"],
        "mime_types": ["text/x-python", "application/javascript", "text/html", "text/x-c++"]
    }
}

RESTORE_LOG = "restore_log.json"
mime = magic.Magic(mime=True)  # Initialize MIME-type detector

def get_file_hash(file_path):
    try:
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Error hashing {file_path}: {e}")
        return None

def extract_text_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.lower()
    except Exception as e:
        logging.error(f"Error reading PDF {file_path}: {e}")
        return ""

def analyze_content(text):
    """Analyze text content using NLP for better categorization."""
    tokens = word_tokenize(text[:2000])  # Limit to 2000 chars for speed
    tagged = pos_tag(tokens)  # Part-of-speech tagging
    nouns = [word for word, pos in tagged if pos.startswith('NN')]  # Focus on nouns
    return nouns

def categorize_file(file_path):
    file_name = file_path.name.lower()
    file_ext = file_path.suffix[1:].lower()
    mime_type = mime.from_file(str(file_path))

    # Step 1: Check MIME type first for accuracy
    for category, props in CATEGORIES.items():
        if mime_type in props["mime_types"]:
            return category

    # Step 2: Fallback to extension if MIME type is inconclusive
    for category, props in CATEGORIES.items():
        if file_ext in props["extensions"]:
            return category

    # Step 3: Content analysis for text-based files
    if mime_type in ["application/pdf", "text/plain"]:
        text = extract_text_from_pdf(file_path) if file_ext == "pdf" else ""
        if not text:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read().lower()
            except Exception as e:
                logging.error(f"Error reading text file {file_path}: {e}")
                return "Uncategorized"
        
        nouns = analyze_content(text)
        for category, props in CATEGORIES.items():
            if any(keyword in nouns for keyword in props["keywords"]):
                return category

    # Step 4: Fallback to Uncategorized
    return "Uncategorized"

def organize_files(source_dir, log_widget, move_log, progress_bar, status_label, root, skip_duplicates):
    source_path = Path(source_dir)
    if not source_path.exists():
        log_widget.insert(tk.END, f"Error: Directory {source_dir} does not exist.\n")
        logging.error(f"Directory {source_dir} does not exist.")
        return

    files = [f for f in source_path.iterdir() if f.is_file()]
    total_files = len(files)
    progress_bar["maximum"] = total_files
    status_label.config(text="Organizing...")

    log_widget.insert(tk.END, f"Scanning {source_dir} ({total_files} files)...\n")
    seen_hashes = {}
    for i, file_path in enumerate(files):
        file_hash = get_file_hash(file_path) if skip_duplicates else None
        if skip_duplicates and file_hash and file_hash in seen_hashes:
            log_widget.insert(tk.END, f"Skipping duplicate: {file_path.name}\n")
            continue

        category = categorize_file(file_path)
        target_dir = source_path / category
        target_dir.mkdir(exist_ok=True)
        target_path = target_dir / file_path.name

        try:
            shutil.move(str(file_path), str(target_path))
            move_log[str(target_path)] = str(file_path)
            if skip_duplicates and file_hash:
                seen_hashes[file_hash] = target_path
            msg = f"Moved {file_path.name} to {category}\n"
            log_widget.insert(tk.END, msg)
            logging.info(msg.strip())
        except Exception as e:
            msg = f"Error moving {file_path.name}: {e}\n"
            log_widget.insert(tk.END, msg)
            logging.error(msg.strip())
        
        progress_bar["value"] = i + 1
        log_widget.see(tk.END)
        root.update_idletasks()

    try:
        with open(RESTORE_LOG, 'w') as f:
            json.dump(move_log, f)
        log_widget.insert(tk.END, "Organization complete! Restore log saved.\n")
    except Exception as e:
        log_widget.insert(tk.END, f"Error saving restore log: {e}\n")
    status_label.config(text="Ready")

def restore_files(log_widget, progress_bar, status_label, root, cleanup_empty):
    if not os.path.exists(RESTORE_LOG):
        log_widget.insert(tk.END, "Error: No restore log found.\n")
        return

    try:
        with open(RESTORE_LOG, 'r') as f:
            move_log = json.load(f)
        if not move_log:
            log_widget.insert(tk.END, "Error: Restore log is empty.\n")
            return
    except Exception as e:
        log_widget.insert(tk.END, f"Error loading restore log: {e}\n")
        return

    total_files = len(move_log)
    progress_bar["maximum"] = total_files
    progress_bar["value"] = 0
    status_label.config(text="Restoring...")

    log_widget.insert(tk.END, f"Restoring {total_files} files...\n")
    source_path = Path(list(move_log.values())[0]).parent if move_log else None
    for i, (target_path, original_path) in enumerate(move_log.items()):
        if os.path.exists(target_path):
            try:
                shutil.move(target_path, original_path)
                msg = f"Restored {Path(target_path).name} to original location\n"
                log_widget.insert(tk.END, msg)
                logging.info(msg.strip())
            except Exception as e:
                msg = f"Error restoring {Path(target_path).name}: {e}\n"
                log_widget.insert(tk.END, msg)
                logging.error(msg.strip())
        else:
            log_widget.insert(tk.END, f"Skipping {Path(target_path).name}: File not found\n")
        
        progress_bar["value"] = i + 1
        log_widget.see(tk.END)
        root.update_idletasks()

    if cleanup_empty and source_path:
        for subdir in source_path.iterdir():
            if subdir.is_dir() and not any(subdir.iterdir()):
                try:
                    os.rmdir(subdir)
                    log_widget.insert(tk.END, f"Removed empty folder: {subdir.name}\n")
                except Exception as e:
                    log_widget.insert(tk.END, f"Error removing {subdir.name}: {e}\n")

    log_widget.insert(tk.END, "Restore complete!\n")
    status_label.config(text="Ready")

class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI File Organizer")
        self.root.geometry("700x500")
        
        self.style_states = [
            (False, "white"),  # Light mode, white text
            (False, "black"),  # Light mode, black text (default)
            (False, "yellow"), # Light mode, yellow text
            (True, "white"),   # Dark mode, white text
            (True, "black"),   # Dark mode, black text
            (True, "yellow")   # Dark mode, yellow text
        ]
        self.current_style_idx = 1  # Start with light mode, black text

        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self.dir_label = ttk.Label(main_frame, text="No directory selected", font=("Arial", 10))
        self.dir_label.grid(row=0, column=0, columnspan=3, pady=5)

        self.select_btn = ttk.Button(main_frame, text="Select Directory", command=self.select_directory, style="TButton")
        self.select_btn.grid(row=1, column=0, columnspan=3, pady=10)

        self.organize_btn = ttk.Button(main_frame, text="Start Organizing", command=self.start_organizing, 
                                      state="disabled", style="Accent.TButton")
        self.organize_btn.grid(row=2, column=0, padx=5, pady=10, sticky="ew")

        self.restore_btn = ttk.Button(main_frame, text="Restore Files", command=self.start_restoring, style="TButton")
        self.restore_btn.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

        self.settings_btn = ttk.Button(main_frame, text="Edit Categories", command=self.open_settings, style="TButton")
        self.settings_btn.grid(row=2, column=2, padx=5, pady=10, sticky="ew")

        self.skip_duplicates_var = tk.BooleanVar(value=False)
        self.skip_duplicates_check = ttk.Checkbutton(main_frame, text="Skip Duplicates", 
                                                    variable=self.skip_duplicates_var)
        self.skip_duplicates_check.grid(row=3, column=0, pady=5, sticky="w")

        self.cleanup_empty_var = tk.BooleanVar(value=True)
        self.cleanup_empty_check = ttk.Checkbutton(main_frame, text="Clean Up Empty Folders", 
                                                  variable=self.cleanup_empty_var)
        self.cleanup_empty_check.grid(row=3, column=1, pady=5, sticky="w")

        self.style_btn = ttk.Button(main_frame, text="Toggle Style", command=self.toggle_style, style="TButton")
        self.style_btn.grid(row=3, column=2, pady=5, sticky="e")

        self.progress_bar = ttk.Progressbar(main_frame, length=400, mode="determinate")
        self.progress_bar.grid(row=4, column=0, columnspan=3, pady=10)

        self.status_label = ttk.Label(main_frame, text="Ready", font=("Arial", 10, "italic"), foreground="green")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=5)

        self.log_area = scrolledtext.ScrolledText(main_frame, width=80, height=15, font=("Consolas", 9))
        self.log_area.grid(row=6, column=0, columnspan=3, pady=10)

        self.style = ttk.Style()
        self.set_theme()
        self.update_styles()

        self.move_log = {}

    def set_theme(self):
        is_dark_mode, _ = self.style_states[self.current_style_idx]
        if is_dark_mode:
            self.root.configure(bg="#2b2b2b")
            self.log_area.configure(bg="#333333", fg="white")
            self.dir_label.configure(foreground="white")
            self.status_label.configure(foreground="#90EE90")
        else:
            self.root.configure(bg="#f0f0f0")
            self.log_area.configure(bg="white", fg="black")
            self.dir_label.configure(foreground="black")
            self.status_label.configure(foreground="green")

    def update_styles(self):
        is_dark_mode, text_color = self.style_states[self.current_style_idx]
        if is_dark_mode:
            self.style.configure("TButton", font=("Arial", 10), padding=5)
            self.style.map("TButton", foreground=[("active", text_color), ("!active", text_color)], 
                          background=[("active", "#4169E1"), ("!active", "#1E90FF")])  # Dodger blue
            self.style.configure("Accent.TButton", font=("Arial", 10, "bold"))
            self.style.map("Accent.TButton", foreground=[("active", text_color), ("!active", text_color)], 
                          background=[("active", "#FF6347"), ("!active", "#FF4500")])  # Orange red
        else:
            self.style.configure("TButton", font=("Arial", 10), padding=5)
            self.style.map("TButton", foreground=[("active", text_color), ("!active", text_color)], 
                          background=[("active", "#5A9BD4"), ("!active", "#4682B4")])  # Steel blue
            self.style.configure("Accent.TButton", font=("Arial", 10, "bold"))
            self.style.map("Accent.TButton", foreground=[("active", text_color), ("!active", text_color)], 
                          background=[("active", "#FF7043"), ("!active", "#FF5722")])  # Deep orange

    def toggle_style(self):
        self.current_style_idx = (self.current_style_idx + 1) % len(self.style_states)
        is_dark_mode, text_color = self.style_states[self.current_style_idx]
        mode_str = "Dark" if is_dark_mode else "Light"
        self.log_area.insert(tk.END, f"Switched to {mode_str} mode with {text_color} text\n")
        self.set_theme()
        self.update_styles()
        self.root.update()

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Edit Categories")
        settings_win.geometry("500x400")
        settings_win.configure(bg=self.root.cget("bg"))

        frame = ttk.Frame(settings_win, padding="10")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Category Name:").grid(row=0, column=0, pady=5)
        category_entry = ttk.Entry(frame)
        category_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Keywords (comma-separated):").grid(row=1, column=0, pady=5)
        keywords_entry = ttk.Entry(frame)
        keywords_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Extensions (comma-separated):").grid(row=2, column=0, pady=5)
        extensions_entry = ttk.Entry(frame)
        extensions_entry.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="MIME Types (comma-separated):").grid(row=3, column=0, pady=5)
        mime_types_entry = ttk.Entry(frame)
        mime_types_entry.grid(row=3, column=1, pady=5)

        categories_listbox = tk.Listbox(frame, height=10, bg=self.log_area.cget("bg"), fg=self.log_area.cget("fg"))
        for cat in CATEGORIES.keys():
            categories_listbox.insert(tk.END, cat)
        categories_listbox.grid(row=4, column=0, columnspan=2, pady=10)

        def add_category():
            cat = category_entry.get().strip()
            keywords = [k.strip() for k in keywords_entry.get().split(",") if k.strip()]
            extensions = [e.strip() for e in extensions_entry.get().split(",") if e.strip()]
            mime_types = [m.strip() for m in mime_types_entry.get().split(",") if m.strip()]
            if not cat or not (keywords or extensions or mime_types):
                messagebox.showwarning("Input Error", "Category name and at least one field must be filled!")
                return
            if cat in CATEGORIES:
                messagebox.showwarning("Duplicate", f"Category '{cat}' already exists!")
                return
            CATEGORIES[cat] = {
                "keywords": keywords,
                "extensions": extensions,
                "mime_types": mime_types
            }
            categories_listbox.insert(tk.END, cat)
            category_entry.delete(0, tk.END)
            keywords_entry.delete(0, tk.END)
            extensions_entry.delete(0, tk.END)
            mime_types_entry.delete(0, tk.END)
            self.log_area.insert(tk.END, f"Added category: {cat}\n")

        def remove_category():
            selection = categories_listbox.curselection()
            if not selection:
                messagebox.showwarning("Selection Error", "Please select a category to remove!")
                return
            cat = categories_listbox.get(selection[0])
            del CATEGORIES[cat]
            categories_listbox.delete(selection[0])
            self.log_area.insert(tk.END, f"Removed category: {cat}\n")

        ttk.Button(frame, text="Add Category", command=add_category).grid(row=5, column=0, pady=5)
        ttk.Button(frame, text="Remove Category", command=remove_category).grid(row=5, column=1, pady=5)

    def select_directory(self):
        self.directory = filedialog.askdirectory(title="Select Directory to Organize")
        if self.directory:
            self.dir_label.config(text=f"Selected: {self.directory}")
            self.organize_btn.config(state="normal")
            self.log_area.delete(1.0, tk.END)
            self.log_area.insert(tk.END, f"Directory selected: {self.directory}\n")
            self.progress_bar["value"] = 0
            self.status_label.config(text="Ready")

    def start_organizing(self):
        if not hasattr(self, 'directory') or not self.directory:
            messagebox.showerror("Error", "Please select a directory first!")
            return
        self.move_log.clear()
        self.log_area.delete(1.0, tk.END)
        self.log_area.insert(tk.END, "Starting organization...\n")
        organize_files(self.directory, self.log_area, self.move_log, self.progress_bar, self.status_label, 
                      self.root, self.skip_duplicates_var.get())
        messagebox.showinfo("Done", "File organization completed!")

    def start_restoring(self):
        self.log_area.delete(1.0, tk.END)
        self.log_area.insert(tk.END, "Checking for restore log...\n")
        restore_files(self.log_area, self.progress_bar, self.status_label, self.root, self.cleanup_empty_var.get())
        messagebox.showinfo("Done", "File restoration completed!")

def main():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('averaged_perceptron_tagger')
    except LookupError:
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
    
    root = tk.Tk()
    app = FileOrganizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()