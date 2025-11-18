#!/usr/bin/env python3
"""
Raspberry Pi Robot Automation Script
This script controls the robot, captures images via ROS2, and saves them in date/time folders
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import json

class RobotAutomation:
    def __init__(self, base_image_path="robot_images", log_path="robot_logs"):
        self.base_image_path = Path(base_image_path)
        self.log_path = Path(log_path)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        self.log_path.mkdir(exist_ok=True)
        
        log_file = self.log_path / f"robot_automation_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_timestamped_folder(self):
        """Create a folder with current timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_path = self.base_image_path / timestamp
        folder_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Created folder: {folder_path}")
        return folder_path
        
    def run_ros2_command(self, command, timeout=30):
        """Run a ROS2 command with timeout"""
        try:
            # Source ROS2 environment and run command
            full_command = f"source /opt/ros/humble/setup.bash && {command}"
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Command successful: {command}")
                return True, result.stdout
            else:
                self.logger.error(f"Command failed: {command}")
                self.logger.error(f"Error: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {command}")
            return False, "Command timed out"
        except Exception as e:
            self.logger.error(f"Error running command '{command}': {str(e)}")
            return False, str(e)
            
    def initialize_ros2_environment(self):
        """Initialize ROS2 environment"""
        self.logger.info("Initializing ROS2 environment...")
        
        # Check if ROS2 is available
        success, output = self.run_ros2_command("ros2 --version")
        if not success:
            self.logger.error("ROS2 not found or not properly installed")
            return False
            
        self.logger.info(f"ROS2 version: {output.strip()}")
        return True
        
    def launch_robot_nodes(self):
        """Launch robot control nodes"""
        self.logger.info("Launching robot control nodes...")
        
        # TODO: Replace with your actual robot launch command
        # Example: ros2 launch your_robot_package robot_control.launch.py
        launch_command = "ros2 launch your_robot_package robot_control.launch.py"
        
        # For now, just log the command (replace with actual implementation)
        self.logger.info(f"Would run: {launch_command}")
        
        # Uncomment when you have your actual launch file:
        # success, output = self.run_ros2_command(launch_command, timeout=60)
        # return success
        
        return True  # Placeholder
        
    def move_robot_to_positions(self):
        """Move robot to different capture positions"""
        self.logger.info("Moving robot to capture positions...")
        
        # TODO: Add your robot movement commands here
        positions = [
            "position_1",
            "position_2", 
            "position_3",
            "position_4",
            "position_5"
        ]
        
        for i, position in enumerate(positions, 1):
            self.logger.info(f"Moving to {position}...")
            
            # TODO: Replace with your actual movement commands
            # Example: ros2 topic pub /robot/cmd_vel geometry_msgs/msg/Twist ...
            move_command = f"ros2 topic pub /robot/cmd_vel geometry_msgs/msg/Twist '{{\"linear\": {{\"x\": 0.1}}, \"angular\": {{\"z\": 0.0}}}}'"
            
            # For now, just simulate movement
            self.logger.info(f"Would run: {move_command}")
            time.sleep(2)  # Simulate movement time
            
            # Uncomment when you have your actual movement commands:
            # success, output = self.run_ros2_command(move_command)
            # if not success:
            #     self.logger.error(f"Failed to move to {position}")
            #     return False
                
        return True
        
    def capture_images(self, output_folder):
        """Capture images at current positions"""
        self.logger.info("Capturing images...")
        
        image_count = 0
        capture_positions = 5  # Number of positions to capture
        
        for i in range(1, capture_positions + 1):
            timestamp = datetime.now().strftime("%H%M%S")
            image_name = f"image_{i:03d}_{timestamp}.jpg"
            image_path = output_folder / image_name
            
            self.logger.info(f"Capturing image {i}/{capture_positions}: {image_name}")
            
            # TODO: Replace with your actual image capture command
            # Example: ros2 run your_camera_package capture_image --output {image_path}
            capture_command = f"ros2 run your_camera_package capture_image --output {image_path}"
            
            # For now, create a placeholder file
            try:
                # Create a placeholder image file
                with open(image_path, 'w') as f:
                    f.write(f"Placeholder image captured at {datetime.now()}")
                
                self.logger.info(f"Captured image: {image_name}")
                image_count += 1
                
                # Uncomment when you have your actual capture command:
                # success, output = self.run_ros2_command(capture_command)
                # if success:
                #     self.logger.info(f"Successfully captured: {image_name}")
                #     image_count += 1
                # else:
                #     self.logger.error(f"Failed to capture: {image_name}")
                
            except Exception as e:
                self.logger.error(f"Error capturing image {image_name}: {str(e)}")
                
            # Wait between captures
            time.sleep(2)
            
        self.logger.info(f"Image capture completed. Captured {image_count} images.")
        return image_count
        
    def create_session_summary(self, output_folder, image_count, success):
        """Create a session summary file"""
        summary_file = output_folder / "session_summary.txt"
        
        summary = f"""Robot Automation Session Summary
===============================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {'SUCCESS' if success else 'FAILED'}
Output Folder: {output_folder}
Images Captured: {image_count}
Robot Type: Raspberry Pi Robot
ROS2 Version: Humble
"""
        
        try:
            with open(summary_file, 'w') as f:
                f.write(summary)
            self.logger.info(f"Created session summary: {summary_file}")
        except Exception as e:
            self.logger.error(f"Failed to create session summary: {str(e)}")
            
    def run_automation_session(self):
        """Run the complete automation session"""
        self.logger.info("Starting Robot Automation Session")
        
        # Ensure base directories exist
        self.base_image_path.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped folder for this session
        session_folder = self.create_timestamped_folder()
        
        try:
            # Initialize ROS2 environment
            if not self.initialize_ros2_environment():
                raise Exception("Failed to initialize ROS2 environment")
                
            # Launch robot nodes
            if not self.launch_robot_nodes():
                raise Exception("Failed to launch robot nodes")
                
            # Move robot to capture positions
            if not self.move_robot_to_positions():
                raise Exception("Failed to move robot to positions")
                
            # Capture images
            image_count = self.capture_images(session_folder)
            
            # Create session summary
            self.create_session_summary(session_folder, image_count, True)
            
            self.logger.info(f"Automation session completed successfully!")
            self.logger.info(f"Images saved to: {session_folder}")
            
            return True, session_folder, image_count
            
        except Exception as e:
            self.logger.error(f"Automation session failed: {str(e)}")
            self.create_session_summary(session_folder, 0, False)
            return False, session_folder, 0

def main():
    parser = argparse.ArgumentParser(description='Robot Automation Script')
    parser.add_argument('--base-path', default='robot_images', 
                       help='Base path for storing images (default: robot_images)')
    parser.add_argument('--log-path', default='robot_logs',
                       help='Path for log files (default: robot_logs)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Create automation instance
    automation = RobotAutomation(args.base_path, args.log_path)
    
    if args.verbose:
        automation.logger.setLevel(logging.DEBUG)
    
    # Run automation session
    success, session_folder, image_count = automation.run_automation_session()
    
    if success:
        print(f"\n✅ Automation completed successfully!")
        print(f"📁 Images saved to: {session_folder}")
        print(f"📸 Images captured: {image_count}")
        sys.exit(0)
    else:
        print(f"\n❌ Automation failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()

