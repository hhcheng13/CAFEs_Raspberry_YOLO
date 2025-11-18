#!/usr/bin/env python3
"""
Google Drive Upload Script for Robot Images
This script uploads captured robot images to Google Drive
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

class GoogleDriveUploader:
    def __init__(self, credentials_path="robot_config/gdrive_credentials.json", 
                 log_path="robot_logs"):
        self.credentials_path = Path(credentials_path)
        self.log_path = Path(log_path)
        self.service = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        self.log_path.mkdir(exist_ok=True)
        
        log_file = self.log_path / f"gdrive_upload_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        if not GOOGLE_APIS_AVAILABLE:
            self.logger.error("Google APIs not available. Please install:")
            self.logger.error("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False
        return True
        
    def authenticate(self):
        """Authenticate with Google Drive API"""
        if not self.check_dependencies():
            return False
            
        try:
            self.logger.info("Authenticating with Google Drive...")
            
            if not self.credentials_path.exists():
                self.logger.error(f"Credentials file not found: {self.credentials_path}")
                self.logger.error("Please run setup_gdrive.py first to create credentials")
                return False
                
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            # Build service
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Test authentication
            about = self.service.about().get(fields='user').execute()
            self.logger.info(f"Successfully authenticated as: {about['user']['displayName']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
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
            self.logger.info(f"Created folder: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except HttpError as e:
            self.logger.error(f"Failed to create folder '{folder_name}': {str(e)}")
            return None
            
    def upload_file(self, file_path: Path, folder_id: Optional[str] = None, 
                   description: str = "") -> bool:
        """Upload a file to Google Drive"""
        try:
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False
                
            file_name = file_path.name
            self.logger.info(f"Uploading file: {file_name}")
            
            # Prepare file metadata
            file_metadata = {'name': file_name}
            if description:
                file_metadata['description'] = description
            if folder_id:
                file_metadata['parents'] = [folder_id]
                
            # Prepare media upload
            media = MediaFileUpload(str(file_path), resumable=True)
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size'
            ).execute()
            
            self.logger.info(f"Successfully uploaded: {file_name} (ID: {file['id']})")
            return True
            
        except HttpError as e:
            self.logger.error(f"Failed to upload file '{file_path}': {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error uploading file '{file_path}': {str(e)}")
            return False
            
    def upload_folder_contents(self, local_folder_path: Path, 
                              gdrive_folder_id: Optional[str] = None) -> bool:
        """Upload all contents of a local folder to Google Drive"""
        folder_name = local_folder_path.name
        self.logger.info(f"Processing folder: {folder_name}")
        
        # Create folder in Google Drive if not specified
        if not gdrive_folder_id:
            gdrive_folder_id = self.create_folder(folder_name)
            if not gdrive_folder_id:
                return False
                
        uploaded_count = 0
        failed_count = 0
        
        # Upload image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        for file_path in local_folder_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                if self.upload_file(file_path, gdrive_folder_id):
                    uploaded_count += 1
                else:
                    failed_count += 1
                    
        # Upload session summary if it exists
        summary_file = local_folder_path / "session_summary.txt"
        if summary_file.exists():
            if self.upload_file(summary_file, gdrive_folder_id, "Session summary"):
                uploaded_count += 1
            else:
                failed_count += 1
                
        self.logger.info(f"Folder upload completed. Uploaded: {uploaded_count}, Failed: {failed_count}")
        return failed_count == 0
        
    def upload_with_rclone(self, local_path: Path, remote_path: str = "gdrive:robot_images") -> bool:
        """Alternative upload method using rclone"""
        try:
            self.logger.info("Attempting upload with rclone...")
            
            # Check if rclone is available
            import shutil
            if not shutil.which('rclone'):
                self.logger.warning("rclone not found. Please install rclone for alternative upload method.")
                return False
                
            # Upload using rclone
            import subprocess
            result = subprocess.run(
                ['rclone', 'copy', str(local_path), remote_path, '--progress'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Successfully uploaded with rclone")
                return True
            else:
                self.logger.error(f"rclone upload failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("rclone upload timed out")
            return False
        except Exception as e:
            self.logger.error(f"rclone upload error: {str(e)}")
            return False

def get_folders_to_upload(base_path: Path, upload_all: bool = False, 
                         upload_latest: bool = False, specific_folder: str = "") -> List[Path]:
    """Determine which folders to upload based on arguments"""
    folders_to_upload = []
    
    if upload_all:
        folders_to_upload = [f for f in base_path.iterdir() if f.is_dir()]
        folders_to_upload.sort(key=lambda x: x.name)
        
    elif upload_latest:
        folders = [f for f in base_path.iterdir() if f.is_dir()]
        if folders:
            folders.sort(key=lambda x: x.name, reverse=True)
            folders_to_upload = [folders[0]]
            
    elif specific_folder:
        target_folder = base_path / specific_folder
        if target_folder.exists() and target_folder.is_dir():
            folders_to_upload = [target_folder]
        else:
            raise FileNotFoundError(f"Specified folder not found: {specific_folder}")
            
    return folders_to_upload

def main():
    parser = argparse.ArgumentParser(description='Google Drive Upload Script')
    parser.add_argument('--base-path', default='robot_images',
                       help='Base path containing image folders (default: robot_images)')
    parser.add_argument('--credentials', default='robot_config/gdrive_credentials.json',
                       help='Path to Google Drive credentials file')
    parser.add_argument('--log-path', default='robot_logs',
                       help='Path for log files (default: robot_logs)')
    parser.add_argument('--upload-all', action='store_true',
                       help='Upload all folders')
    parser.add_argument('--upload-latest', action='store_true',
                       help='Upload latest folder only')
    parser.add_argument('--specific-folder', type=str,
                       help='Upload specific folder by name')
    parser.add_argument('--use-rclone', action='store_true',
                       help='Use rclone instead of Google Drive API')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.upload_all, args.upload_latest, args.specific_folder]):
        print("Error: Must specify one of --upload-all, --upload-latest, or --specific-folder")
        sys.exit(1)
        
    # Create uploader instance
    uploader = GoogleDriveUploader(args.credentials, args.log_path)
    
    if args.verbose:
        uploader.logger.setLevel(logging.DEBUG)
        
    # Get folders to upload
    try:
        base_path = Path(args.base_path)
        if not base_path.exists():
            print(f"Error: Base path does not exist: {base_path}")
            sys.exit(1)
            
        folders_to_upload = get_folders_to_upload(
            base_path, args.upload_all, args.upload_latest, args.specific_folder
        )
        
        if not folders_to_upload:
            print("No folders found to upload")
            sys.exit(0)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
        
    # Upload folders
    success = True
    
    if args.use_rclone:
        # Use rclone method
        for folder in folders_to_upload:
            if not uploader.upload_with_rclone(folder):
                success = False
    else:
        # Use Google Drive API method
        if not uploader.authenticate():
            print("Failed to authenticate with Google Drive. Try --use-rclone for alternative method.")
            sys.exit(1)
            
        for folder in folders_to_upload:
            if not uploader.upload_folder_contents(folder):
                success = False
                
    if success:
        print(f"\n✅ All folders uploaded successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Some uploads failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

