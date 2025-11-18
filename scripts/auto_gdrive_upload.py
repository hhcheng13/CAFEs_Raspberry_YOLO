#!/usr/bin/env python3
"""
Auto Google Drive Upload Script
Automatically uploads files to Google Drive with simple setup
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Try to import Google Drive libraries
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

class AutoGDriveUploader:
    def __init__(self, credentials_file: str = "gdrive_credentials.json"):
        self.credentials_file = Path(credentials_file)
        self.service = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the uploader"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gdrive_upload.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def install_dependencies(self):
        """Install required Google Drive API packages"""
        if GOOGLE_APIS_AVAILABLE:
            self.logger.info("✅ Google Drive API packages already installed")
            return True
            
        self.logger.info("📦 Installing Google Drive API packages...")
        packages = [
            "google-api-python-client",
            "google-auth-httplib2",
            "google-auth-oauthlib"
        ]
        
        for package in packages:
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                self.logger.info(f"✅ Installed {package}")
            except Exception as e:
                self.logger.error(f"❌ Failed to install {package}: {e}")
                return False
                
        self.logger.info("🔄 Please restart the script after installation")
        return False
        
    def create_credentials_template(self):
        """Create a credentials template file"""
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
        
        with open(self.credentials_file, 'w') as f:
            json.dump(template, f, indent=2)
            
        self.logger.info(f"📝 Created credentials template: {self.credentials_file}")
        self.print_setup_instructions()
        
    def print_setup_instructions(self):
        """Print setup instructions for Google Drive API"""
        print("\n" + "="*60)
        print("🔧 GOOGLE DRIVE API SETUP INSTRUCTIONS")
        print("="*60)
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Drive API:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Google Drive API' and enable it")
        print("4. Create Service Account:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'Service Account'")
        print("   - Fill in details and create")
        print("5. Generate Key:")
        print("   - Click on your service account")
        print("   - Go to 'Keys' tab > 'Add Key' > 'Create new key'")
        print("   - Choose JSON format and download")
        print("6. Replace the content in gdrive_credentials.json with your downloaded file")
        print("7. Run this script again")
        print("="*60)
        
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API"""
        if not GOOGLE_APIS_AVAILABLE:
            self.logger.error("❌ Google APIs not available. Run install_dependencies() first.")
            return False
            
        if not self.credentials_file.exists():
            self.logger.error(f"❌ Credentials file not found: {self.credentials_file}")
            self.create_credentials_template()
            return False
            
        try:
            # Check if credentials are still template
            with open(self.credentials_file, 'r') as f:
                creds = json.load(f)
                if creds.get('project_id') == 'your-project-id':
                    self.logger.error("❌ Please replace template credentials with your actual Google Drive API key")
                    self.print_setup_instructions()
                    return False
            
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                str(self.credentials_file),
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            # Build service
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Test authentication
            about = self.service.about().get(fields='user').execute()
            self.logger.info(f"✅ Authenticated as: {about['user']['displayName']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            return False
            
    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create a folder in Google Drive"""
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
                
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            self.logger.info(f"📁 Created folder: {folder_name}")
            return folder_id
            
        except HttpError as e:
            self.logger.error(f"❌ Failed to create folder '{folder_name}': {e}")
            return None
            
    def upload_file(self, file_path: Path, folder_name: str = "Robot_Uploads") -> bool:
        """Upload a single file to Google Drive"""
        if not file_path.exists():
            self.logger.error(f"❌ File not found: {file_path}")
            return False
            
        try:
            # Create or find folder
            folder_id = self.find_or_create_folder(folder_name)
            if not folder_id:
                return False
                
            file_name = file_path.name
            self.logger.info(f"🔄 Uploading: {file_name}")
            
            # Check if file already exists
            existing_file_id = self.find_file(file_name, folder_id)
            if existing_file_id:
                self.logger.info(f"⚠️  File already exists, updating: {file_name}")
                # Update existing file
                media = MediaFileUpload(str(file_path), resumable=True)
                file = self.service.files().update(
                    fileId=existing_file_id,
                    media_body=media
                ).execute()
            else:
                # Create new file
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id],
                    'description': f'Uploaded on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                }
                
                media = MediaFileUpload(str(file_path), resumable=True)
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,webViewLink'
                ).execute()
                
            self.logger.info(f"✅ Uploaded successfully: {file_name}")
            if 'webViewLink' in file:
                self.logger.info(f"🔗 View link: {file['webViewLink']}")
            return True
            
        except HttpError as e:
            self.logger.error(f"❌ Upload failed for '{file_name}': {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error uploading '{file_name}': {e}")
            return False
            
    def find_or_create_folder(self, folder_name: str) -> Optional[str]:
        """Find existing folder or create new one"""
        try:
            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                return folders[0]['id']
            else:
                return self.create_folder(folder_name)
                
        except Exception as e:
            self.logger.error(f"❌ Error finding/creating folder: {e}")
            return None
            
    def find_file(self, file_name: str, folder_id: str) -> Optional[str]:
        """Find existing file in folder"""
        try:
            results = self.service.files().list(
                q=f"name='{file_name}' and parents in '{folder_id}'",
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            return files[0]['id'] if files else None
            
        except Exception as e:
            self.logger.error(f"❌ Error finding file: {e}")
            return None
            
    def upload_folder(self, folder_path: Path, gdrive_folder_name: str = "Robot_Uploads") -> bool:
        """Upload all files from a local folder"""
        if not folder_path.exists() or not folder_path.is_dir():
            self.logger.error(f"❌ Folder not found: {folder_path}")
            return False
            
        self.logger.info(f"📂 Uploading folder: {folder_path.name}")
        
        # Get all files in folder
        files = [f for f in folder_path.iterdir() if f.is_file()]
        if not files:
            self.logger.warning(f"⚠️  No files found in {folder_path}")
            return True
            
        success_count = 0
        for file_path in files:
            if self.upload_file(file_path, gdrive_folder_name):
                success_count += 1
                
        self.logger.info(f"✅ Uploaded {success_count}/{len(files)} files successfully")
        return success_count == len(files)
        
    def monitor_and_upload(self, watch_folder: Path, gdrive_folder_name: str = "Robot_Uploads", 
                          interval: int = 30):
        """Monitor a folder and automatically upload new files"""
        if not watch_folder.exists():
            self.logger.error(f"❌ Watch folder not found: {watch_folder}")
            return
            
        self.logger.info(f"👀 Monitoring folder: {watch_folder}")
        self.logger.info(f"⏰ Check interval: {interval} seconds")
        self.logger.info("Press Ctrl+C to stop monitoring")
        
        uploaded_files = set()
        
        try:
            while True:
                # Get current files
                current_files = {f.name for f in watch_folder.iterdir() if f.is_file()}
                
                # Find new files
                new_files = current_files - uploaded_files
                
                if new_files:
                    self.logger.info(f"🆕 Found {len(new_files)} new files")
                    for file_name in new_files:
                        file_path = watch_folder / file_name
                        if self.upload_file(file_path, gdrive_folder_name):
                            uploaded_files.add(file_name)
                        time.sleep(1)  # Small delay between uploads
                else:
                    self.logger.debug("No new files found")
                    
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Monitoring error: {e}")

def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto Google Drive Uploader')
    parser.add_argument('--file', type=str, help='Upload a single file')
    parser.add_argument('--folder', type=str, help='Upload all files from a folder')
    parser.add_argument('--watch', type=str, help='Monitor folder and auto-upload new files')
    parser.add_argument('--gdrive-folder', type=str, default='Robot_Uploads', 
                       help='Google Drive folder name (default: Robot_Uploads)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Monitoring interval in seconds (default: 30)')
    parser.add_argument('--setup', action='store_true', help='Setup Google Drive API credentials')
    
    args = parser.parse_args()
    
    # Create uploader
    uploader = AutoGDriveUploader()
    
    # Setup mode
    if args.setup:
        if not GOOGLE_APIS_AVAILABLE:
            uploader.install_dependencies()
        else:
            uploader.create_credentials_template()
        return
    
    # Check authentication
    if not uploader.authenticate():
        print("\n❌ Authentication failed. Run with --setup to configure credentials.")
        return
    
    # Upload modes
    if args.file:
        file_path = Path(args.file)
        uploader.upload_file(file_path, args.gdrive_folder)
        
    elif args.folder:
        folder_path = Path(args.folder)
        uploader.upload_folder(folder_path, args.gdrive_folder)
        
    elif args.watch:
        watch_folder = Path(args.watch)
        uploader.monitor_and_upload(watch_folder, args.gdrive_folder, args.interval)
        
    else:
        # Interactive mode
        print("\n🤖 Auto Google Drive Uploader")
        print("=" * 40)
        print("1. Upload single file")
        print("2. Upload folder contents")
        print("3. Monitor folder (auto-upload)")
        print("4. Setup credentials")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            file_path = input("Enter file path: ").strip()
            uploader.upload_file(Path(file_path))
            
        elif choice == '2':
            folder_path = input("Enter folder path: ").strip()
            uploader.upload_folder(Path(folder_path))
            
        elif choice == '3':
            watch_folder = input("Enter folder to monitor: ").strip()
            interval = int(input("Check interval (seconds, default 30): ") or "30")
            uploader.monitor_and_upload(Path(watch_folder), interval=interval)
            
        elif choice == '4':
            uploader.create_credentials_template()
            
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()

