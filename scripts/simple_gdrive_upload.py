#!/usr/bin/env python3
"""
Simple Google Drive Upload Script
Upload a single image file to Google Drive
"""

import os
import sys
from pathlib import Path

def install_google_drive_packages():
    """Install required packages"""
    print("Installing Google Drive packages...")
    import subprocess
    
    packages = [
        "google-api-python-client",
        "google-auth-httplib2", 
        "google-auth-oauthlib"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except:
            print(f"❌ Failed to install {package}")
            return False
    return True

def create_sample_image():
    """Create a sample random.png file"""
    try:
        from PIL import Image
        import numpy as np
        
        # Create a random image
        random_data = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
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

def setup_google_drive():
    """Setup Google Drive API"""
    print("\n🔧 Setting up Google Drive API...")
    
    # Install packages
    if not install_google_drive_packages():
        return False
    
    # Create credentials template
    credentials_template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id", 
        "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
    }
    
    # Create config directory
    os.makedirs("robot_config", exist_ok=True)
    
    # Save credentials template
    import json
    with open("robot_config/gdrive_credentials.json", "w") as f:
        json.dump(credentials_template, f, indent=2)
    
    print("✅ Created credentials template: robot_config/gdrive_credentials.json")
    
    print("\n📝 Next steps:")
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create new project or select existing")
    print("3. Enable Google Drive API")
    print("4. Go to Credentials → Create Credentials → Service Account")
    print("5. Create service account and download JSON key")
    print("6. Replace content in robot_config/gdrive_credentials.json with your downloaded file")
    print("7. Run this script again to test upload")
    
    return True

def upload_to_google_drive():
    """Upload random.png to Google Drive"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        print("🔄 Uploading random.png to Google Drive...")
        
        # Check if credentials file exists
        credentials_file = "robot_config/gdrive_credentials.json"
        if not os.path.exists(credentials_file):
            print("❌ Credentials file not found!")
            print("Run setup first or check if file exists at:", credentials_file)
            return False
        
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        # Build service
        service = build('drive', 'v3', credentials=credentials)
        
        # Test authentication
        about = service.about().get(fields='user').execute()
        print(f"✅ Connected as: {about['user']['displayName']}")
        
        # Upload file
        file_metadata = {
            'name': 'random.png',
            'description': 'Test upload from Raspberry Pi robot'
        }
        
        media = MediaFileUpload('random.png', resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        print(f"✅ Upload successful!")
        print(f"📁 File ID: {file['id']}")
        print(f"🔗 View link: {file['webViewLink']}")
        
        return True
        
    except ImportError:
        print("❌ Google APIs not installed. Run setup first.")
        return False
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        return False

def main():
    print("🤖 Simple Google Drive Upload Test")
    print("=" * 40)
    
    # Check if random.png exists, create if not
    if not os.path.exists("random.png"):
        print("Creating sample image...")
        create_sample_image()
    
    # Check if credentials exist
    if not os.path.exists("robot_config/gdrive_credentials.json"):
        print("Credentials not found. Setting up...")
        setup_google_drive()
        return
    
    # Try to upload
    if upload_to_google_drive():
        print("\n🎉 Success! Your image is now in Google Drive!")
    else:
        print("\n💡 Tips:")
        print("- Make sure you've replaced the credentials template with your actual Google Drive API key")
        print("- Check that Google Drive API is enabled in your Google Cloud project")
        print("- Verify the service account has proper permissions")

if __name__ == "__main__":
    main()


