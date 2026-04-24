import os
import shutil
import hashlib
from datetime import datetime
from collections import defaultdict


FILE_CATEGORIES = {
    "Images": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".svg",
        ".webp",
        ".ico",
        ".raw",
        ".heic",
    ],
    "Documents": [
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".csv",
        ".md",
    ],
    "Videos": [
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
    ],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "Code": [
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
    ],
    "Executables": [".exe", ".msi", ".bat", ".cmd", ".sh", ".app", ".dmg"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
}


def get_file_category(filename):
    """Determine the category of a file based on its extension."""
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Others"


def get_file_hash(filepath, chunk_size=8192):
    """Calculate MD5 hash of a file for duplicate detection."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_files(folder_path, recursive=False):
    """Scan a folder and return list of all files with their details."""
    files = []
    if recursive:
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append(
                        {
                            "name": filename,
                            "path": filepath,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime),
                            "category": get_file_category(filename),
                            "extension": os.path.splitext(filename)[1].lower(),
                        }
                    )
    else:
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append(
                    {
                        "name": filename,
                        "path": filepath,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "category": get_file_category(filename),
                        "extension": os.path.splitext(filename)[1].lower(),
                    }
                )
    return files


def find_duplicates(folder_path, recursive=True):
    """Find duplicate files based on content hash."""
    files = scan_files(folder_path, recursive)
    hash_map = defaultdict(list)

    for file in files:
        try:
            file_hash = get_file_hash(file["path"])
            hash_map[file_hash].append(file)
        except (PermissionError, OSError):
            continue

    duplicates = {h: fl for h, fl in hash_map.items() if len(fl) > 1}
    return duplicates


def get_folder_suggestions(files):
    """Suggest folder structure based on files found."""
    categories = defaultdict(list)
    for file in files:
        categories[file["category"]].append(file)

    suggestions = {}
    for category, category_files in categories.items():
        suggestions[category] = {
            "count": len(category_files),
            "total_size": sum(f["size"] for f in category_files),
            "files": category_files[:5],
        }

    return suggestions


def organize_files(
    folder_path, dry_run=True, use_date=False, use_extension=False, custom_rules=None
):
    """Organize files into categorized folders."""
    files = scan_files(folder_path, recursive=False)
    operations = []

    for file in files:
        if use_date:
            date_str = file["modified"].strftime("%Y-%m")
            target_folder = os.path.join(folder_path, date_str)
        elif use_extension:
            ext = file["extension"].lstrip(".")
            target_folder = os.path.join(folder_path, ext)
        else:
            category = file["category"]
            if custom_rules and category in custom_rules:
                category = custom_rules[category]
            target_folder = os.path.join(folder_path, category)

        target_path = os.path.join(target_folder, file["name"])

        if file["path"] != target_path:
            operations.append(
                {
                    "source": file["path"],
                    "destination": target_path,
                    "folder": target_folder,
                    "file": file,
                }
            )

    if not dry_run:
        for op in operations:
            os.makedirs(op["folder"], exist_ok=True)
            if not os.path.exists(op["destination"]):
                shutil.move(op["source"], op["destination"])
            else:
                base, ext = os.path.splitext(op["destination"])
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                new_dest = f"{base}_{counter}{ext}"
                shutil.move(op["source"], new_dest)
                op["destination"] = new_dest

    return operations


def get_statistics(files):
    """Generate statistics about files."""
    stats = {
        "total_files": len(files),
        "total_size": sum(f["size"] for f in files),
        "by_category": defaultdict(lambda: {"count": 0, "size": 0}),
        "by_extension": defaultdict(lambda: {"count": 0, "size": 0}),
        "oldest_file": None,
        "newest_file": None,
        "largest_file": None,
    }

    if not files:
        return stats

    for file in files:
        stats["by_category"][file["category"]]["count"] += 1
        stats["by_category"][file["category"]]["size"] += file["size"]
        stats["by_extension"][file["extension"]]["count"] += 1
        stats["by_extension"][file["extension"]]["size"] += file["size"]

    stats["oldest_file"] = min(files, key=lambda f: f["modified"])
    stats["newest_file"] = max(files, key=lambda f: f["modified"])
    stats["largest_file"] = max(files, key=lambda f: f["size"])

    return stats


def format_size(size_bytes):
    """Format file size to human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
