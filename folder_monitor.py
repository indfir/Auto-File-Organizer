import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread


class FolderMonitorHandler(FileSystemEventHandler):
    """Handler for monitoring folder changes."""

    def __init__(self, callback=None):
        self.callback = callback
        self.new_files = []

    def on_created(self, event):
        if not event.is_directory:
            self.new_files.append(event.src_path)
            if self.callback:
                self.callback("new_file", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            if self.callback:
                self.callback("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            if self.callback:
                self.callback("deleted", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            if self.callback:
                self.callback("moved", event.src_path)

    def get_new_files(self):
        files = self.new_files.copy()
        self.new_files.clear()
        return files


class FolderMonitor:
    """Monitors a folder for changes."""

    def __init__(self, folder_path, callback=None):
        self.folder_path = folder_path
        self.handler = FolderMonitorHandler(callback)
        self.observer = Observer()
        self.observer.schedule(self.handler, folder_path, recursive=False)
        self.running = False

    def start(self):
        """Start monitoring the folder."""
        if not self.running:
            self.observer.start()
            self.running = True

    def stop(self):
        """Stop monitoring the folder."""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False

    def get_new_files(self):
        """Get list of new files detected since last check."""
        return self.handler.get_new_files()

    def __del__(self):
        if self.running:
            self.stop()
