#!/usr/bin/env python3
"""
Google Drive Setup Script
Easy setup for Google Drive API credentials
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    packages = [
        "google-api-python-client",
        "google-auth-httplib2", 
        "google-auth-oauthlib"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except Exception as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def create_credentials_template():
    """Create credentials template file"""
    template = {
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
    
    credentials_file = "gdrive_credentials.json"
    
    with open(credentials_file, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"📝 Created credentials template: {credentials_file}")
    return credentials_file

def print_detailed_instructions():
    """Print detailed setup instructions"""
    print("\n" + "="*70)
    print("🔧 GOOGLE DRIVE API SETUP - STEP BY STEP")
    print("="*70)
    print()
    print("STEP 1: Create Google Cloud Project")
    print("-" * 40)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Click 'Select a project' → 'New Project'")
    print("3. Enter project name (e.g., 'Robot Drive Upload')")
    print("4. Click 'Create'")
    print()
    print("STEP 2: Enable Google Drive API")
    print("-" * 40)
    print("1. In your project, go to 'APIs & Services' → 'Library'")
    print("2. Search for 'Google Drive API'")
    print("3. Click on it and press 'Enable'")
    print()
    print("STEP 3: Create Service Account")
    print("-" * 40)
    print("1. Go to 'APIs & Services' → 'Credentials'")
    print("2. Click 'Create Credentials' → 'Service Account'")
    print("3. Fill in:")
    print("   - Service account name: 'robot-drive-upload'")
    print("   - Description: 'For robot file uploads'")
    print("4. Click 'Create and Continue'")
    print("5. Skip role assignment (click 'Continue')")
    print("6. Click 'Done'")
    print()
    print("STEP 4: Generate API Key")
    print("-" * 40)
    print("1. In Credentials page, find your service account")
    print("2. Click on the service account email")
    print("3. Go to 'Keys' tab")
    print("4. Click 'Add Key' → 'Create new key'")
    print("5. Choose 'JSON' format")
    print("6. Click 'Create' - file will download automatically")
    print()
    print("STEP 5: Configure Credentials")
    print("-" * 40)
    print("1. Open the downloaded JSON file")
    print("2. Copy ALL content from the file")
    print("3. Replace the content in 'gdrive_credentials.json' with your file content")
    print("4. Save the file")
    print()
    print("STEP 6: Test Upload")
    print("-" * 40)
    print("1. Run: python auto_gdrive_upload.py --setup")
    print("2. Or run: python auto_gdrive_upload.py --file your_file.txt")
    print()
    print("="*70)
    print("🎉 That's it! Your robot can now upload to Google Drive!")
    print("="*70)

def test_credentials():
    """Test if credentials are working"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        credentials_file = "gdrive_credentials.json"
        
        if not os.path.exists(credentials_file):
            print(f"❌ Credentials file not found: {credentials_file}")
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
        print(f"✅ Success! Connected as: {about['user']['displayName']}")
        return True
        
    except ImportError:
        print("❌ Google APIs not installed. Run setup first.")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def create_test_file():
    """Create a test file for upload"""
    test_content = f"""Test Upload File
Created: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
This is a test file to verify Google Drive upload functionality.
"""
    
    with open("test_upload.txt", "w") as f:
        f.write(test_content)
    
    print("📄 Created test file: test_upload.txt")

def main():
    print("🤖 Google Drive Setup for Robot")
    print("=" * 40)
    
    # Install packages
    if not install_requirements():
        print("❌ Failed to install packages")
        return
    
    # Create credentials template
    credentials_file = create_credentials_template()
    
    # Print instructions
    print_detailed_instructions()
    
    # Ask if user wants to test
    print("\n" + "="*50)
    response = input("Have you completed the setup? Test credentials now? (y/n): ").lower()
    
    if response == 'y':
        if test_credentials():
            print("\n🎉 Setup successful!")
            create_test_file()
            print("\nNext steps:")
            print("1. python auto_gdrive_upload.py --file test_upload.txt")
            print("2. Check your Google Drive for the uploaded file")
        else:
            print("\n❌ Setup incomplete. Please follow the instructions above.")
    else:
        print("\n📝 Remember to:")
        print("1. Complete the Google Cloud setup")
        print("2. Replace credentials in gdrive_credentials.json")
        print("3. Run: python auto_gdrive_upload.py --setup")

if __name__ == "__main__":
    main()

