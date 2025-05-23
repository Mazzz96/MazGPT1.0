"""
Image Plugin
------------
Handles image upload, basic info, and (optionally) vision model inference.
"""
import os
from PIL import Image

IMAGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'images')
os.makedirs(IMAGE_DIR, exist_ok=True)

def register():
    return ImagePlugin()

class ImagePlugin:
    meta = {
        "description": "Handles image upload and basic info for MazGPT.",
        "version": "1.0.0",
        "author": "MazGPT Team"
    }

    def handle(self, text):
        parts = text.strip().split(maxsplit=1)
        if not parts:
            return None
        cmd = parts[0].lower()
        if cmd == '/imgupload' and len(parts) == 2:
            filepath = parts[1]
            if not os.path.isfile(filepath):
                return f"Image not found: {filepath}"
            dest = os.path.join(IMAGE_DIR, os.path.basename(filepath))
            Image.open(filepath).save(dest)
            return f"Image uploaded: {os.path.basename(filepath)}"
        elif cmd == '/imginfo' and len(parts) == 2:
            filename = parts[1]
            img_path = os.path.join(IMAGE_DIR, filename)
            if not os.path.isfile(img_path):
                return f"Image not found in images: {filename}"
            with Image.open(img_path) as img:
                return f"{filename}: format={img.format}, size={img.size}, mode={img.mode}"
        elif cmd == '/listimages':
            files = os.listdir(IMAGE_DIR)
            return "Uploaded images: " + ", ".join(files) if files else "No images uploaded."
        return None
