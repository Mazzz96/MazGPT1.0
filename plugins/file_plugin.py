"""
File Plugin
-----------
Handles file upload and download for MazGPT CLI.
"""
import os
import shutil

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def register():
    return FilePlugin()

class FilePlugin:
    meta = {
        "description": "Handles file upload and download for MazGPT.",
        "version": "1.0.0",
        "author": "MazGPT Team"
    }

    def handle(self, text):
        parts = text.strip().split(maxsplit=1)
        if not parts:
            return None
        cmd = parts[0].lower()
        if cmd == '/upload' and len(parts) == 2:
            filepath = parts[1]
            if not os.path.isfile(filepath):
                return f"File not found: {filepath}"
            dest = os.path.join(UPLOAD_DIR, os.path.basename(filepath))
            shutil.copy(filepath, dest)
            return f"File uploaded: {os.path.basename(filepath)}"
        elif cmd == '/download' and len(parts) == 2:
            filename = parts[1]
            src = os.path.join(UPLOAD_DIR, filename)
            if not os.path.isfile(src):
                return f"File not found in uploads: {filename}"
            dest = os.path.join(os.getcwd(), filename)
            shutil.copy(src, dest)
            return f"File downloaded to: {dest}"
        elif cmd == '/listfiles':
            files = os.listdir(UPLOAD_DIR)
            return "Uploaded files: " + ", ".join(files) if files else "No files uploaded."
        return None
