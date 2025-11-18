#!/usr/bin/env python3
"""
Robot Automation Launcher
Simple menu-driven interface to run robot automation and upload tasks
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print(f"\n⏹️ {description} cancelled by user")
        return False

def show_menu():
    """Display the main menu"""
    print("""
🤖 Raspberry Pi Robot Automation
================================

Please select an option:
1. Run robot automation (capture images)
2. Upload latest session to Google Drive
3. Upload all sessions to Google Drive
4. Upload specific folder to Google Drive
5. Setup Google Drive credentials
6. Test Google Drive connection
7. Show help
8. Exit
""")

def get_user_choice():
    """Get user choice from menu"""
    while True:
        try:
            choice = input("Enter your choice (1-8): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
                return choice
            else:
                print("Invalid choice. Please enter a number between 1-8.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)

def run_robot_automation():
    """Run the robot automation script"""
    command = "python robot_automation.py --verbose"
    return run_command(command, "Robot automation")

def upload_latest():
    """Upload latest session to Google Drive"""
    command = "python upload_to_gdrive.py --upload-latest --verbose"
    return run_command(command, "Upload latest session")

def upload_all():
    """Upload all sessions to Google Drive"""
    command = "python upload_to_gdrive.py --upload-all --verbose"
    return run_command(command, "Upload all sessions")

def upload_specific():
    """Upload specific folder to Google Drive"""
    # List available folders
    base_path = Path("robot_images")
    if not base_path.exists():
        print("❌ No robot_images directory found. Run automation first.")
        return False
        
    folders = [f for f in base_path.iterdir() if f.is_dir()]
    if not folders:
        print("❌ No folders found in robot_images directory.")
        return False
        
    print("\nAvailable folders:")
    for i, folder in enumerate(folders, 1):
        print(f"{i}. {folder.name}")
        
    try:
        choice = int(input("Enter folder number: ")) - 1
        if 0 <= choice < len(folders):
            folder_name = folders[choice].name
            command = f"python upload_to_gdrive.py --specific-folder '{folder_name}' --verbose"
            return run_command(command, f"Upload folder '{folder_name}'")
        else:
            print("Invalid folder number.")
            return False
    except (ValueError, KeyboardInterrupt):
        print("Invalid input or cancelled.")
        return False

def setup_gdrive():
    """Setup Google Drive credentials"""
    print("\n🔧 Setting up Google Drive...")
    
    # Install dependencies
    if not run_command("python setup_gdrive.py --install-deps", "Installing dependencies"):
        return False
        
    # Create credentials template
    if not run_command("python setup_gdrive.py --create-credentials", "Creating credentials template"):
        return False
        
    print("\n📝 Next steps:")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create/select project and enable Google Drive API")
    print("3. Create Service Account and download JSON key")
    print("4. Replace template content in robot_config/gdrive_credentials.json")
    print("5. Test connection using option 6")
    
    return True

def test_gdrive():
    """Test Google Drive connection"""
    command = "python setup_gdrive.py --test-connection"
    return run_command(command, "Testing Google Drive connection")

def show_help():
    """Show help information"""
    print("""
📚 Help - Robot Automation System
================================

This system consists of three main scripts:

1. 🤖 robot_automation.py
   - Controls robot movement via ROS2
   - Captures images at different positions
   - Saves images in timestamped folders
   - Creates session summaries

2. ☁️ upload_to_gdrive.py
   - Uploads captured images to Google Drive
   - Supports uploading latest, all, or specific folders
   - Uses Google Drive API or rclone as fallback

3. ⚙️ setup_gdrive.py
   - Installs required dependencies
   - Creates credentials template
   - Tests Google Drive connection

📁 File Structure:
   robot_images/           # Captured images
   ├── 2024-01-15_14-30-25/
   │   ├── image_001_143025.jpg
   │   ├── image_002_143027.jpg
   │   └── session_summary.txt
   └── 2024-01-15_15-45-12/
       ├── image_001_154512.jpg
       └── session_summary.txt
   
   robot_config/           # Configuration files
   └── gdrive_credentials.json
   
   robot_logs/             # Log files
   ├── robot_automation_2024-01-15.log
   └── gdrive_upload_2024-01-15.log

🔧 Setup Process:
   1. Run option 5 to setup Google Drive
   2. Follow the instructions to get API credentials
   3. Run option 6 to test connection
   4. Run option 1 to capture images
   5. Run option 2 to upload latest session

💡 Tips:
   - Check robot_logs/ for detailed logs
   - Use --verbose flag for detailed output
   - Consider using rclone for easier Google Drive setup
   - Make sure ROS2 is properly installed on your Raspberry Pi
""")

def main():
    """Main program loop"""
    print("🤖 Welcome to Raspberry Pi Robot Automation System!")
    
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == '1':
            run_robot_automation()
        elif choice == '2':
            upload_latest()
        elif choice == '3':
            upload_all()
        elif choice == '4':
            upload_specific()
        elif choice == '5':
            setup_gdrive()
        elif choice == '6':
            test_gdrive()
        elif choice == '7':
            show_help()
        elif choice == '8':
            print("\n👋 Goodbye!")
            break
            
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()


