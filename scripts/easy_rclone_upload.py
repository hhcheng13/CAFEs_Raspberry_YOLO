#!/usr/bin/env python3
"""
Easy Google Drive Upload with rclone - Step by Step
This version has better error handling and clearer instructions
"""

import os
import sys
import subprocess
import time

def create_sample_file():
    """Create a sample file to upload"""
    with open("test_upload.txt", "w") as f:
        f.write(f"Test upload from Raspberry Pi robot\n")
        f.write(f"Created at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("This is a test file for Google Drive upload\n")
    print("✅ Created test_upload.txt")

def check_rclone():
    """Check if rclone is installed"""
    try:
        result = subprocess.run(['rclone', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ rclone is installed")
            return True
    except:
        pass
    
    print("❌ rclone not found")
    return False

def install_rclone_simple():
    """Simple rclone installation"""
    print("📥 Installing rclone...")
    
    # Try to install via package manager first
    try:
        # Try pip install (sometimes works)
        subprocess.run([sys.executable, "-m", "pip", "install", "rclone"], check=True)
        print("✅ rclone installed via pip")
        return True
    except:
        pass
    
    # Manual download for Windows
    try:
        import urllib.request
        import zipfile
        import shutil
        
        print("Downloading rclone for Windows...")
        url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
        urllib.request.urlretrieve(url, "rclone.zip")
        
        with zipfile.ZipFile("rclone.zip", 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Find and move rclone.exe
        for item in os.listdir("."):
            if item.startswith("rclone-") and os.path.isdir(item):
                rclone_exe = os.path.join(item, "rclone.exe")
                if os.path.exists(rclone_exe):
                    shutil.copy(rclone_exe, "rclone.exe")
                    shutil.rmtree(item)
                    break
        
        os.remove("rclone.zip")
        print("✅ rclone installed")
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def manual_rclone_setup():
    """Manual rclone setup with clear instructions"""
    print("""
🔧 Manual rclone Setup Instructions
==================================

Since automatic setup failed, let's do it manually:

1. Open Command Prompt or PowerShell
2. Run: rclone config
3. Follow these exact steps:

   a) Type: n (for new remote)
   b) Name: gdrive
   c) Type: drive (or just press Enter)
   d) Client ID: (just press Enter - leave empty)
   e) Client Secret: (just press Enter - leave empty)
   f) Scope: 1 (for full access)
   g) Service Account: (just press Enter - leave empty)
   h) Use auto config: y (yes)
   i) Your browser will open
   j) Login to Google and allow access
   k) Copy the code back to terminal
   l) Keep this remote: y (yes)

4. Test with: rclone lsd gdrive:
5. If successful, come back and run this script again

Press Enter when you've completed the setup...
""")
    input()

def test_rclone_config():
    """Test if rclone is properly configured"""
    try:
        # List remotes
        result = subprocess.run(['rclone', 'listremotes'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            remotes = result.stdout.strip().split('\n')
            print(f"✅ Found remotes: {remotes}")
            
            # Check if gdrive remote exists
            for remote in remotes:
                if 'gdrive' in remote.lower():
                    print(f"✅ Google Drive remote found: {remote}")
                    return True
            
            print("❌ No Google Drive remote found")
            return False
        else:
            print("❌ No remotes configured")
            return False
            
    except Exception as e:
        print(f"❌ Error checking rclone: {e}")
        return False

def upload_file_simple():
    """Simple file upload"""
    print("🔄 Uploading test file...")
    
    try:
        # Find gdrive remote
        result = subprocess.run(['rclone', 'listremotes'], capture_output=True, text=True)
        remotes = result.stdout.strip().split('\n')
        
        gdrive_remote = None
        for remote in remotes:
            if 'gdrive' in remote.lower():
                gdrive_remote = remote
                break
        
        if not gdrive_remote:
            print("❌ No Google Drive remote found")
            return False
        
        print(f"Using remote: {gdrive_remote}")
        
        # Upload file
        cmd = ['rclone', 'copy', 'test_upload.txt', f'{gdrive_remote}robot_test/']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Upload successful!")
            
            # List files to confirm
            list_cmd = ['rclone', 'ls', f'{gdrive_remote}robot_test/']
            list_result = subprocess.run(list_cmd, capture_output=True, text=True)
            if list_result.returncode == 0:
                print("📁 Files in Google Drive:")
                print(list_result.stdout)
            
            return True
        else:
            print(f"❌ Upload failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def main():
    print("🤖 Easy Google Drive Upload with rclone")
    print("=" * 40)
    
    # Create test file
    create_sample_file()
    
    # Check rclone
    if not check_rclone():
        print("\nInstalling rclone...")
        if not install_rclone_simple():
            print("\n❌ Could not install rclone automatically")
            print("Please download manually from: https://rclone.org/downloads/")
            print("Extract rclone.exe to this folder and run again")
            return
    
    # Test configuration
    if not test_rclone_config():
        print("\n🔧 rclone not configured yet")
        manual_rclone_setup()
        
        # Test again
        if not test_rclone_config():
            print("\n❌ Configuration still not working")
            print("Try running these commands manually:")
            print("1. rclone config")
            print("2. Follow the setup steps")
            print("3. Test with: rclone lsd gdrive:")
            return
    
    # Upload file
    if upload_file_simple():
        print("\n🎉 Success! File uploaded to Google Drive!")
        print("🔗 Check your Google Drive at: https://drive.google.com/")
        print("📁 Look for 'robot_test' folder")
    else:
        print("\n❌ Upload failed")
        print("Try running: rclone copy test_upload.txt gdrive:robot_test/")

if __name__ == "__main__":
    main()


