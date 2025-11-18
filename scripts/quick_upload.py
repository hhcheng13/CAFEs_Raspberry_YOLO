#!/usr/bin/env python3
"""
Quick Google Drive Upload
Simple one-liner script for quick uploads
"""

import sys
from pathlib import Path

# Add the scripts directory to path so we can import our uploader
sys.path.append(str(Path(__file__).parent))

from auto_gdrive_upload import AutoGDriveUploader

def quick_upload(file_or_folder_path: str):
    """Quick upload function"""
    uploader = AutoGDriveUploader()
    
    if not uploader.authenticate():
        print("❌ Authentication failed. Run setup first:")
        print("python setup_gdrive.py")
        return False
    
    path = Path(file_or_folder_path)
    
    if path.is_file():
        print(f"📄 Uploading file: {path.name}")
        return uploader.upload_file(path)
    elif path.is_dir():
        print(f"📂 Uploading folder: {path.name}")
        return uploader.upload_folder(path)
    else:
        print(f"❌ Path not found: {path}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_upload.py <file_or_folder_path>")
        print("Example: python quick_upload.py my_image.jpg")
        print("Example: python quick_upload.py ./my_folder")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = quick_upload(file_path)
    
    if success:
        print("✅ Upload completed!")
    else:
        print("❌ Upload failed!")
        sys.exit(1)

