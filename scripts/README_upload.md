# Google Drive Auto Upload Scripts

Simple scripts to automatically upload files to Google Drive from your robot.

## Quick Start

### 1. Setup (One-time)
```bash
python setup_gdrive.py
```
This will:
- Install required packages
- Create credentials template
- Show detailed setup instructions

### 2. Upload Files

**Upload a single file:**
```bash
python quick_upload.py my_image.jpg
```

**Upload a folder:**
```bash
python quick_upload.py ./my_folder
```

**Advanced options:**
```bash
# Upload single file
python auto_gdrive_upload.py --file my_image.jpg

# Upload all files from folder
python auto_gdrive_upload.py --folder ./my_folder

# Monitor folder and auto-upload new files
python auto_gdrive_upload.py --watch ./my_folder --interval 30

# Interactive mode
python auto_gdrive_upload.py
```

## Setup Instructions

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create new project

2. **Enable Google Drive API**
   - Go to APIs & Services → Library
   - Search "Google Drive API" and enable it

3. **Create Service Account**
   - Go to APIs & Services → Credentials
   - Create Credentials → Service Account
   - Create and download JSON key

4. **Configure Credentials**
   - Replace content in `gdrive_credentials.json` with your downloaded file

## Features

- ✅ **Simple Setup**: One-time configuration
- ✅ **Auto Upload**: Monitor folders and upload new files automatically
- ✅ **Batch Upload**: Upload entire folders at once
- ✅ **Error Handling**: Robust error handling and logging
- ✅ **File Management**: Organizes uploads in Google Drive folders
- ✅ **Progress Tracking**: Shows upload progress and status

## File Organization

All uploads go to a "Robot_Uploads" folder in your Google Drive by default. You can change this with the `--gdrive-folder` option.

## Logs

Upload logs are saved to `gdrive_upload.log` for troubleshooting.

## Troubleshooting

**Authentication Error:**
- Make sure you've completed the Google Cloud setup
- Check that `gdrive_credentials.json` contains your actual API key (not template)

**Upload Fails:**
- Check internet connection
- Verify file permissions
- Check log file for detailed error messages

**Package Installation Issues:**
- Try: `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`

