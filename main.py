import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from datetime import datetime

from file_organizer import (
    scan_files,
    organize_files,
    get_statistics,
    find_duplicates,
    format_size,
)
from undo_manager import UndoManager
from folder_monitor import FolderMonitor


class FileOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("File Organizer Pro")
        self.geometry("1100x700")
        self.minsize(900, 550)

        self.selected_folder = None
        self.files = []
        self.undo_manager = UndoManager()
        self.monitor = None
        self.monitoring = False
        self._buttons = []
        self.is_dark = True

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._create_main_content()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        mode = "dark" if self.is_dark else "light"
        ctk.set_appearance_mode(mode)
        self._update_colors()
        self.theme_btn.configure(text="🌙 Dark" if self.is_dark else "☀️ Light")

    def _update_colors(self):
        if self.is_dark:
            bg = "#1a1a1a"
            card = "#222222"
            inner = "#1a1a1a"
            text = "#e0e0e0"
            text_dim = "#888888"
            text_muted = "#666666"
            border = "#333333"
        else:
            bg = "#f5f5f5"
            card = "#ffffff"
            inner = "#f0f0f0"
            text = "#1a1a1a"
            text_dim = "#555555"
            text_muted = "#888888"
            border = "#dddddd"

        self.container.configure(fg_color=bg)
        self.file_frame.configure(fg_color=card)
        self.sidebar_frame.configure(fg_color=card)
        self.list_frame.configure(fg_color=inner)
        self.toolbar.configure(fg_color="transparent")
        self.search_frame.configure(fg_color=inner)
        self.folder_frame.configure(fg_color=inner)
        self.actions_frame.configure(fg_color="transparent")
        self.opts_frame.configure(fg_color=inner)
        self.stats_frame.configure(fg_color=inner)
        self.status_label.configure(text_color=text_muted)
        self.file_count_label.configure(text_color=text_muted)
        self.folder_display.configure(text_color=text_dim, fg_color=inner)
        self.stats_text.configure(fg_color=inner)

        style = ttk.Style()
        if self.is_dark:
            style.configure(
                "Custom.Treeview",
                background="#2a2a2a",
                foreground="#e0e0e0",
                fieldbackground="#2a2a2a",
            )
            style.configure(
                "Custom.Treeview.Heading", background=card, foreground=text_dim
            )
        else:
            style.configure(
                "Custom.Treeview",
                background="#ffffff",
                foreground="#1a1a1a",
                fieldbackground="#ffffff",
            )
            style.configure(
                "Custom.Treeview.Heading", background=card, foreground=text_dim
            )

    def _create_main_content(self):
        self.container = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.container.grid_columnconfigure(0, weight=3)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self._create_file_area(self.container)
        self._create_sidebar(self.container)

    def _create_file_area(self, parent):
        self.file_frame = ctk.CTkFrame(
            parent,
            fg_color="#222222",
            corner_radius=12,
            border_width=1,
            border_color="#333333",
        )
        self.file_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.file_frame.grid_columnconfigure(0, weight=1)
        self.file_frame.grid_rowconfigure(1, weight=1)

        # Toolbar
        self.toolbar = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        self.toolbar.grid_columnconfigure(0, weight=1)

        # Theme toggle
        self.theme_btn = ctk.CTkButton(
            self.toolbar,
            text="🌙 Dark",
            command=self.toggle_theme,
            width=90,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color="#333333",
            hover_color="#444444",
        )
        self.theme_btn.grid(row=0, column=0, sticky="w")

        self.search_frame = ctk.CTkFrame(
            self.toolbar,
            fg_color="#1a1a1a",
            corner_radius=8,
            border_width=1,
            border_color="#444444",
        )
        self.search_frame.grid(row=0, column=1, sticky="ew", padx=10)
        self.search_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.search_frame, text="🔍", font=ctk.CTkFont(size=14)).grid(
            row=0, column=0, padx=(10, 0), sticky="e"
        )
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.filter_files)
        ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Search files...",
            textvariable=self.search_var,
            height=34,
            corner_radius=8,
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        self.filter_mode = ctk.CTkComboBox(
            self.toolbar,
            values=[
                "All",
                "Images",
                "Documents",
                "Videos",
                "Music",
                "Archives",
                "Code",
                "Others",
            ],
            command=self.filter_files,
            height=34,
            corner_radius=8,
            width=120,
            font=ctk.CTkFont(size=11),
        )
        self.filter_mode.set("All")
        self.filter_mode.grid(row=0, column=2, padx=10)

        # File list
        self.list_frame = ctk.CTkFrame(
            self.file_frame,
            fg_color="#1a1a1a",
            corner_radius=8,
            border_width=1,
            border_color="#444444",
        )
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background="#2a2a2a",
            foreground="#e0e0e0",
            fieldbackground="#2a2a2a",
            borderwidth=1,
            rowheight=36,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#222222",
            foreground="#888888",
            borderwidth=1,
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", "#4A90E2")],
            foreground=[("selected", "#fff")],
        )

        self.file_tree = ttk.Treeview(
            self.list_frame,
            columns=("name", "size"),
            show="headings",
            style="Custom.Treeview",
            height=15,
        )
        self.file_tree.heading("name", text="File Name", anchor="w")
        self.file_tree.heading("size", text="Size", anchor="w")
        self.file_tree.column("name", width=300, minwidth=150, stretch=True)
        self.file_tree.column("size", width=100, minwidth=80, stretch=False)

        sb = ctk.CTkScrollbar(
            self.list_frame, command=self.file_tree.yview, width=8, corner_radius=4
        )
        self.file_tree.configure(yscrollcommand=sb.set)
        self.file_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        sb.grid(row=0, column=1, sticky="ns", pady=4)

        self.file_count_label = ctk.CTkLabel(
            self.list_frame,
            text="0 files",
            font=ctk.CTkFont(size=11),
            text_color="#666",
        )
        self.file_count_label.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.filtered_files = []

    def _create_sidebar(self, parent):
        self.sidebar_frame = ctk.CTkFrame(
            parent,
            fg_color="#222222",
            corner_radius=12,
            border_width=1,
            border_color="#333333",
        )
        self.sidebar_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header.grid(row=0, column=0, padx=14, pady=(12, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text="📁 File Organizer", font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        # Folder
        self.folder_frame = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color="#1a1a1a",
            corner_radius=10,
            border_width=1,
            border_color="#333333",
        )
        self.folder_frame.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        self.folder_frame.grid_columnconfigure(0, weight=1)
        self.folder_display = ctk.CTkLabel(
            self.folder_frame,
            text="No folder selected",
            font=ctk.CTkFont(size=11),
            text_color="#888",
            wraplength=160,
            height=36,
            anchor="w",
            fg_color="#1a1a1a",
        )
        self.folder_display.grid(row=0, column=0, padx=10, pady=8, sticky="ew")
        self.folder_display.configure(anchor="w", padx=10)
        ctk.CTkButton(
            self.folder_frame,
            text="Select Folder",
            command=self.select_folder,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4A90E2",
            hover_color="#357ABD",
            border_width=0,
        ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        # Actions - 2 column grid
        self.actions_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.actions_frame.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")
        self.actions_frame.grid_columnconfigure(0, weight=1)
        self.actions_frame.grid_columnconfigure(1, weight=1)

        btns = [
            ("🔍 Scan", self.scan_files, "#4A90E2", 0, 0),
            ("✨ Organize", self.organize_files, "#4CAF50", 0, 1),
            ("👁️ Preview", self.preview_changes, "#9C27B0", 1, 0),
            ("↩️ Undo", self.undo_action, "#FF9800", 1, 1),
            ("🔎 Duplicates", self.find_duplicates, "#00BCD4", 2, 0),
        ]
        for text, cmd, fg, row, col in btns:
            b = ctk.CTkButton(
                self.actions_frame,
                text=text,
                command=cmd,
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=fg,
                hover_color=self._darken(fg),
                border_width=0,
            )
            b.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            if text == "🔍 Scan":
                self.scan_btn = b
            elif text == "✨ Organize":
                self.organize_btn = b
            elif text == "↩️ Undo":
                self.undo_btn = b
            elif text == "🔎 Duplicates":
                self.duplicate_btn = b

        # Options
        self.opts_frame = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color="#1a1a1a",
            corner_radius=10,
            border_width=1,
            border_color="#333333",
        )
        self.opts_frame.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")
        self.opts_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.opts_frame,
            text="Organize Mode:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(10, 6), sticky="w")
        self.organize_mode = ctk.CTkSegmentedButton(
            self.opts_frame,
            values=["Category", "Date", "Extension"],
            command=self.set_organize_mode,
            height=34,
            font=ctk.CTkFont(size=11),
        )
        self.organize_mode.set("Category")
        self.organize_mode.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")
        self.dry_run_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self.opts_frame,
            text="Preview Mode (Dry Run)",
            variable=self.dry_run_var,
            font=ctk.CTkFont(size=11),
        ).grid(row=2, column=0, padx=10, pady=4, sticky="w")
        self.recursive_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.opts_frame,
            text="Include Subfolders",
            variable=self.recursive_var,
            font=ctk.CTkFont(size=11),
        ).grid(row=3, column=0, padx=10, pady=(4, 10), sticky="w")

        # Stats & Monitor
        self.stats_frame = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color="#1a1a1a",
            corner_radius=10,
            border_width=1,
            border_color="#333333",
        )
        self.stats_frame.grid(row=4, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.stats_frame.grid_columnconfigure(0, weight=1)
        self.stats_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.stats_frame,
            text="Statistics:",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(10, 6), sticky="w")
        self.stats_text = ctk.CTkTextbox(
            self.stats_frame,
            font=ctk.CTkFont(size=11, family="Consolas"),
            fg_color="#1a1a1a",
            corner_radius=6,
            border_width=0,
            height=100,
        )
        self.stats_text.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="nsew")
        self.stats_text.insert("1.0", "Scan files to see statistics")
        self.stats_text.configure(state="disabled")
        self.monitor_btn = ctk.CTkButton(
            self.stats_frame,
            text="📡 Start Monitor",
            command=self.toggle_monitor,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2196F3",
            hover_color="#1976D2",
            border_width=0,
        )
        self.monitor_btn.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Status label
        self.status_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color="#666",
        )
        self.status_label.grid(row=5, column=0, padx=12, pady=(0, 10), sticky="w")

    def _darken(self, hex_color):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return f"#{max(0, int(r * 0.85)):02x}{max(0, int(g * 0.85)):02x}{max(0, int(b * 0.85)):02x}"

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.selected_folder = folder
            display = folder if len(folder) < 28 else "..." + folder[-25:]
            self.folder_display.configure(text=display)
            self.status_label.configure(text=f"✓ Folder selected: {display}")

    def scan_files(self):
        if not self.selected_folder:
            messagebox.showwarning("Warning", "Please select a folder first!")
            return
        self.scan_btn.configure(state="disabled")
        self.status_label.configure(text="⏳ Scanning files...")

        def task():
            try:
                self.files = scan_files(
                    self.selected_folder, recursive=self.recursive_var.get()
                )
                self.filtered_files = self.files.copy()
                self.after(0, self.update_file_list)
                self.after(0, self.update_stats)
                self.after(
                    0,
                    lambda: self.status_label.configure(
                        text=f"✓ Scanned {len(self.files)} files"
                    ),
                )
                self.after(0, lambda: self.scan_btn.configure(state="normal"))
            except Exception as e:
                self.after(0, lambda: self.scan_btn.configure(state="normal"))
                self.after(0, lambda: self.status_label.configure(text=f"✗ Error: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def update_file_list(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        colors = {
            "Images": "#4CAF50",
            "Documents": "#2196F3",
            "Videos": "#FF5722",
            "Music": "#9C27B0",
            "Archives": "#FF9800",
            "Code": "#00BCD4",
            "Executables": "#f44336",
            "Fonts": "#795548",
            "Others": "#888",
        }
        for f in self.filtered_files:
            self.file_tree.insert(
                "",
                "end",
                values=(f["name"], format_size(f["size"])),
                tags=(f["category"],),
            )
        for c, color in colors.items():
            self.file_tree.tag_configure(c, foreground=color)
        self.file_count_label.configure(
            text=f"{len(self.filtered_files)} of {len(self.files)} files"
        )

    def update_stats(self):
        if not self.files:
            self.stats_text.configure(state="normal")
            self.stats_text.delete("1.0", "end")
            self.stats_text.insert("1.0", "Scan files to see statistics")
            self.stats_text.configure(state="disabled")
            return
        s = get_statistics(self.files)
        txt = f"📊 Files: {s['total_files']}\n📦 Size: {format_size(s['total_size'])}\n🏷️ Categories: {len(s['by_category'])}\n\n"
        for c, d in sorted(s["by_category"].items()):
            txt += f"  {c}: {d['count']} files\n"
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", txt)
        self.stats_text.configure(state="disabled")

    def filter_files(self, *args):
        q = self.search_var.get().lower()
        fc = self.filter_mode.get()
        self.filtered_files = [
            f
            for f in self.files
            if (not q or q in f["name"].lower())
            and (fc == "All" or f["category"] == fc)
        ]
        self.update_file_list()

    def organize_files(self):
        if not self.selected_folder or not self.files:
            messagebox.showwarning(
                "Warning", "Please select folder and scan files first!"
            )
            return
        self.organize_btn.configure(state="disabled")
        self.status_label.configure(text="⏳ Organizing files...")

        def task():
            try:
                mode = self.organize_mode.get()
                dry = self.dry_run_var.get()
                ops = organize_files(
                    self.selected_folder,
                    dry_run=dry,
                    use_date=(mode == "Date"),
                    use_extension=(mode == "Extension"),
                )
                if dry:
                    self.after(0, lambda: self.show_preview(ops))
                    self.after(
                        0,
                        lambda: self.status_label.configure(
                            text=f"👁️ Preview: {len(ops)} files"
                        ),
                    )
                else:
                    self.undo_manager.record_operation(ops)
                    self.after(
                        0,
                        lambda: self.status_label.configure(
                            text=f"✓ Organized {len(ops)} files"
                        ),
                    )
                    self.after(0, self.scan_files)
                self.after(0, lambda: self.organize_btn.configure(state="normal"))
            except Exception as e:
                self.after(0, lambda: self.organize_btn.configure(state="normal"))
                self.after(0, lambda: self.status_label.configure(text=f"✗ Error: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def show_preview(self, operations):
        if not operations:
            return
        win = ctk.CTkToplevel(self)
        win.title("Preview Changes")
        win.geometry("700x500")
        win.transient(self)
        ctk.CTkLabel(
            win,
            text=f"👁️ {len(operations)} files will be moved",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=16)
        sf = ctk.CTkScrollableFrame(win, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=16, pady=8)
        for op in operations:
            row = ctk.CTkFrame(sf, fg_color="#2a2a2a", corner_radius=8)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row,
                text=f"📤 FROM: {op['source']}",
                font=ctk.CTkFont(size=10),
                text_color="#FF5722",
            ).pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(
                row,
                text=f"📥 TO: {op['destination']}",
                font=ctk.CTkFont(size=10),
                text_color="#4CAF50",
            ).pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(
            win, text="Close", command=win.destroy, height=36, fg_color="#4A90E2"
        ).pack(pady=12)

    def preview_changes(self):
        if not self.selected_folder or not self.files:
            messagebox.showwarning(
                "Warning", "Please select folder and scan files first!"
            )
            return
        mode = self.organize_mode.get()
        ops = organize_files(
            self.selected_folder,
            dry_run=True,
            use_date=(mode == "Date"),
            use_extension=(mode == "Extension"),
        )
        self.show_preview(ops)

    def undo_action(self):
        if self.undo_manager.get_history_count() == 0:
            messagebox.showinfo("Info", "No operations to undo")
            return
        if messagebox.askyesno("Undo", "Undo the last operation?"):
            ok, msg = self.undo_manager.undo_latest()
            messagebox.showinfo("Result", msg)
            if ok:
                self.scan_files()

    def find_duplicates(self):
        if not self.selected_folder:
            messagebox.showwarning("Warning", "Please select a folder first!")
            return
        self.duplicate_btn.configure(state="disabled")
        self.status_label.configure(text="⏳ Finding duplicates...")

        def task():
            try:
                dups = find_duplicates(self.selected_folder)
                self.after(0, lambda: self.show_duplicates(dups))
                self.after(
                    0,
                    lambda: self.status_label.configure(
                        text=f"✓ Found {len(dups)} groups"
                    ),
                )
                self.after(0, lambda: self.duplicate_btn.configure(state="normal"))
            except Exception as e:
                self.after(0, lambda: self.duplicate_btn.configure(state="normal"))
                self.after(0, lambda: self.status_label.configure(text=f"✗ Error: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def show_duplicates(self, duplicates):
        win = ctk.CTkToplevel(self)
        win.title("Duplicate Files")
        win.geometry("600x500")
        win.transient(self)
        ctk.CTkLabel(
            win,
            text=f"🔎 Found {len(duplicates)} duplicate groups",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=16)
        sf = ctk.CTkScrollableFrame(win, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=16, pady=8)
        for h, files in duplicates.items():
            gf = ctk.CTkFrame(sf, fg_color="#2a2a2a", corner_radius=8)
            gf.pack(fill="x", pady=5)
            ctk.CTkLabel(
                gf,
                text=f"⚠️ {len(files)} files ({format_size(files[0]['size'])} each)",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#FF9800",
            ).pack(fill="x", padx=12, pady=8)
            for f in files:
                ctk.CTkLabel(
                    gf,
                    text=f"📄 {f['path']}",
                    font=ctk.CTkFont(size=10),
                    text_color="#ccc",
                ).pack(fill="x", padx=16, pady=3)
        ctk.CTkButton(
            win, text="Close", command=win.destroy, height=36, fg_color="#4A90E2"
        ).pack(pady=12)

    def toggle_monitor(self):
        if not self.selected_folder:
            messagebox.showwarning("Warning", "Please select a folder first!")
            return
        if not self.monitoring:
            self.monitor = FolderMonitor(
                self.selected_folder, callback=self.monitor_callback
            )
            self.monitor.start()
            self.monitoring = True
            self.monitor_btn.configure(text="📡 Stop Monitor", fg_color="#f44336")
            self.status_label.configure(text="📡 Monitoring started")
        else:
            if self.monitor:
                self.monitor.stop()
            self.monitoring = False
            self.monitor_btn.configure(text="📡 Start Monitor", fg_color="#2196F3")
            self.status_label.configure(text="⏹️ Monitoring stopped")

    def monitor_callback(self, event_type, filepath):
        self.status_label.configure(
            text=f"📡 {event_type}: {os.path.basename(filepath)}"
        )

    def set_organize_mode(self, mode):
        self.status_label.configure(text=f"⚙️ Mode: {mode}")


if __name__ == "__main__":
    app = FileOrganizerApp()
    app.mainloop()
