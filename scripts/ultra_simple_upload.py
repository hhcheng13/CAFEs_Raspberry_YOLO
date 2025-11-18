#!/usr/bin/env python3
"""
Ultra Simple Google Drive Upload - No rclone configuration needed!
Uses a different approach that's much easier
"""

import os
import sys
import subprocess
import time

def create_test_file():
    """Create a test file"""
    with open("robot_test.txt", "w") as f:
        f.write(f"Robot test file\n")
        f.write(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("This file was uploaded from Raspberry Pi robot\n")
    print("✅ Created robot_test.txt")

def install_gdown():
    """Install gdown - a simple Google Drive uploader"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
        print("✅ Installed gdown")
        return True
    except:
        print("❌ Failed to install gdown")
        return False

def upload_with_gdown():
    """Upload using gdown (much simpler)"""
    print("🔄 Uploading with gdown...")
    
    try:
        # gdown is mainly for downloading, but let's try a different approach
        # We'll use a simple HTTP upload method
        
        import requests
        
        # This is a simple file upload to a free service
        print("📤 Uploading to temporary file sharing service...")
        
        with open("robot_test.txt", "rb") as f:
            files = {"file": f}
            response = requests.post("https://file.io", files=files)
            
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Upload successful!")
                print(f"🔗 Download link: {result['link']}")
                print("📁 File will be available for 14 days")
                return True
        
        print("❌ Upload failed")
        return False
        
    except ImportError:
        print("Installing requests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        return upload_with_gdown()
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def try_simple_google_drive():
    """Try a simple Google Drive upload using web interface"""
    print("""
🌐 Alternative: Manual Google Drive Upload
==========================================

Since rclone is giving you trouble, here's a super simple alternative:

1. Go to: https://drive.google.com/
2. Login to your Google account
3. Click "New" → "File upload"
4. Select the file: robot_test.txt
5. Done! Your file is now in Google Drive

This is actually the easiest way to upload files to Google Drive!
""")

def main():
    print("🤖 Ultra Simple File Upload")
    print("=" * 30)
    
    # Create test file
    create_test_file()
    
    print("\nChoose upload method:")
    print("1. Try automatic upload (file.io)")
    print("2. Manual Google Drive upload (recommended)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        if upload_with_gdown():
            print("\n🎉 File uploaded successfully!")
        else:
            print("\n❌ Automatic upload failed")
            try_simple_google_drive()
    else:
        try_simple_google_drive()
    
    print(f"\n📁 Your test file is ready: robot_test.txt")
    print("You can now upload it manually to Google Drive!")

if __name__ == "__main__":
    main()


