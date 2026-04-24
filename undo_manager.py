import os
import shutil
import json
from datetime import datetime


class UndoManager:
    """Manages undo operations for file movements."""

    def __init__(self, history_file=None):
        self.history_file = history_file or os.path.join(
            os.path.expanduser("~"), ".file_organizer_undo.json"
        )
        self.history = self._load_history()

    def _load_history(self):
        """Load undo history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save_history(self):
        """Save undo history to file."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"Error saving history: {e}")

    def record_operation(self, operations):
        """Record a file organization operation for undo."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operations": [
                {
                    "source": op["source"],
                    "destination": op["destination"],
                    "folder": op["folder"],
                }
                for op in operations
            ],
        }
        self.history.append(entry)
        self._save_history()

    def get_history(self):
        """Get all recorded operations."""
        return self.history

    def get_latest_operation(self):
        """Get the most recent operation."""
        if self.history:
            return self.history[-1]
        return None

    def undo_latest(self):
        """Undo the most recent operation."""
        if not self.history:
            return False, "No operations to undo"

        latest = self.history.pop()
        success_count = 0
        error_count = 0
        errors = []

        for op in reversed(latest["operations"]):
            try:
                if os.path.exists(op["destination"]):
                    source_dir = os.path.dirname(op["source"])
                    os.makedirs(source_dir, exist_ok=True)
                    shutil.move(op["destination"], op["source"])
                    success_count += 1

                    folder = op["folder"]
                    if os.path.exists(folder) and not os.listdir(folder):
                        os.rmdir(folder)
            except Exception as e:
                error_count += 1
                errors.append(f"Error moving {op['destination']}: {str(e)}")

        self._save_history()

        if error_count == 0:
            return True, f"Successfully undone {success_count} operations"
        else:
            return (
                False,
                f"Partially undone: {success_count} succeeded, {error_count} failed. Errors: {'; '.join(errors)}",
            )

    def clear_history(self):
        """Clear all undo history."""
        self.history = []
        self._save_history()

    def get_history_count(self):
        """Get number of recorded operations."""
        return len(self.history)
