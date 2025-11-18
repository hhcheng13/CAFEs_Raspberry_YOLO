#!/usr/bin/env python3
"""
Simple Google Drive Upload using rclone (FREE - No Google Cloud billing required!)
This is much easier than Google Cloud API setup
"""

import os
import sys
import subprocess
from pathlib import Path

def check_rclone():
    """Check if rclone is installed"""
    try:
        result = subprocess.run(['rclone', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ rclone is already installed!")
            print(f"Version: {result.stdout.split()[1]}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ rclone not found")
    return False

def install_rclone_windows():
    """Install rclone on Windows"""
    print("📥 Installing rclone for Windows...")
    
    try:
        # Download rclone installer
        import urllib.request
        import zipfile
        import shutil
        
        print("Downloading rclone...")
        url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
        urllib.request.urlretrieve(url, "rclone.zip")
        
        print("Extracting rclone...")
        with zipfile.ZipFile("rclone.zip", 'r') as zip_ref:
            zip_ref.extractall("rclone_temp")
        
        # Find the extracted folder
        for item in os.listdir("rclone_temp"):
            if item.startswith("rclone-"):
                rclone_folder = os.path.join("rclone_temp", item)
                break
        
        # Copy rclone.exe to a location in PATH or current directory
        shutil.copy(os.path.join(rclone_folder, "rclone.exe"), "rclone.exe")
        
        # Cleanup
        os.remove("rclone.zip")
        shutil.rmtree("rclone_temp")
        
        print("✅ rclone installed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to install rclone: {e}")
        print("Please download manually from: https://rclone.org/downloads/")
        return False

def create_sample_image():
    """Create a sample random.png file"""
    try:
        from PIL import Image
        import numpy as np
        
        # Create a random colorful image
        random_data = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        img = Image.fromarray(random_data)
        img.save("random.png")
        print("✅ Created random.png")
        return True
    except ImportError:
        # If PIL not available, create a simple text file
        with open("random.png", "w") as f:
            f.write("This is a sample file for Google Drive upload test")
        print("✅ Created random.png (text file)")
        return True

def setup_google_drive_rclone():
    """Setup Google Drive with rclone (interactive)"""
    print("\n🔧 Setting up Google Drive with rclone...")
    print("This will open an interactive setup process.")
    print("You'll need to:")
    print("1. Choose 'Google Drive' as remote type")
    print("2. Leave client_id and client_secret empty (press Enter)")
    print("3. Choose 'Full access' for scope")
    print("4. Leave service_account_file empty (press Enter)")
    print("5. Choose 'Yes' to use auto config")
    print("6. Your browser will open for Google authentication")
    print("7. Login to your Google account and allow access")
    print("8. Copy the authorization code back to the terminal")
    print("9. Choose 'Yes' to keep this remote")
    print("10. Give it a name like 'gdrive'")
    
    input("\nPress Enter when ready to start setup...")
    
    try:
        # Run rclone config
        result = subprocess.run(['rclone', 'config'], input='', text=True)
        if result.returncode == 0:
            print("✅ rclone configuration completed!")
            return True
        else:
            print("❌ rclone configuration failed")
            return False
    except Exception as e:
        print(f"❌ Error during rclone setup: {e}")
        return False

def upload_with_rclone():
    """Upload random.png using rclone"""
    print("🔄 Uploading random.png to Google Drive using rclone...")
    
    try:
        # List configured remotes
        result = subprocess.run(['rclone', 'listremotes'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ No rclone remotes configured")
            return False
        
        remotes = result.stdout.strip().split('\n')
        print(f"Available remotes: {remotes}")
        
        # Use the first Google Drive remote (usually 'gdrive:')
        gdrive_remote = None
        for remote in remotes:
            if 'gdrive' in remote.lower():
                gdrive_remote = remote
                break
        
        if not gdrive_remote:
            print("❌ No Google Drive remote found")
            print("Available remotes:", remotes)
            return False
        
        print(f"Using remote: {gdrive_remote}")
        
        # Upload the file
        upload_command = ['rclone', 'copy', 'random.png', f'{gdrive_remote}robot_images/', '--progress']
        result = subprocess.run(upload_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Upload successful!")
            print("📁 File uploaded to Google Drive in 'robot_images' folder")
            
            # Show file info
            list_command = ['rclone', 'ls', f'{gdrive_remote}robot_images/']
            list_result = subprocess.run(list_command, capture_output=True, text=True)
            if list_result.returncode == 0:
                print("📋 Files in Google Drive:")
                print(list_result.stdout)
            
            return True
        else:
            print(f"❌ Upload failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return False

def show_manual_setup():
    """Show manual setup instructions"""
    print("""
📚 Manual rclone Setup Instructions
==================================

If the automatic setup didn't work, here's how to do it manually:

1. Download rclone:
   - Go to: https://rclone.org/downloads/
   - Download for Windows
   - Extract and run rclone.exe

2. Configure Google Drive:
   - Run: rclone config
   - Choose: n (new remote)
   - Name: gdrive
   - Type: drive (Google Drive)
   - Client ID: (press Enter to leave empty)
   - Client Secret: (press Enter to leave empty)
   - Scope: 1 (Full access)
   - Service Account: (press Enter to leave empty)
   - Use auto config: y
   - Your browser will open for authentication
   - Login and allow access
   - Copy the code back to terminal
   - Keep this remote: y

3. Test upload:
   - Run: rclone copy random.png gdrive:robot_images/ --progress

4. List files:
   - Run: rclone ls gdrive:robot_images/
""")

def main():
    print("🤖 Simple Google Drive Upload with rclone (FREE!)")
    print("=" * 50)
    print("✅ No Google Cloud billing required!")
    print("✅ No API keys needed!")
    print("✅ Just your regular Google account!")
    print()
    
    # Check if random.png exists, create if not
    if not os.path.exists("random.png"):
        print("Creating sample image...")
        create_sample_image()
    
    # Check if rclone is installed
    if not check_rclone():
        print("\nInstalling rclone...")
        if not install_rclone_windows():
            print("\n❌ Could not install rclone automatically")
            show_manual_setup()
            return
    
    # Check if Google Drive is configured
    try:
        result = subprocess.run(['rclone', 'listremotes'], capture_output=True, text=True)
        if result.returncode != 0 or not result.stdout.strip():
            print("\n🔧 Google Drive not configured yet")
            if not setup_google_drive_rclone():
                print("\n❌ Setup failed. Try manual setup:")
                show_manual_setup()
                return
    except:
        print("\n❌ Error checking rclone configuration")
        return
    
    # Try to upload
    if upload_with_rclone():
        print("\n🎉 Success! Your image is now in Google Drive!")
        print("🔗 You can view it at: https://drive.google.com/")
    else:
        print("\n💡 Tips:")
        print("- Make sure you completed the rclone setup")
        print("- Check that you're logged into the correct Google account")
        print("- Try running: rclone config to reconfigure")

if __name__ == "__main__":
    main()

