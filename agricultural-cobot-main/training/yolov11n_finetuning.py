#!/usr/bin/env python3
"""
YOLOv11n Fine-tuning Script

This script performs fine-tuning, evaluation, and inference on custom datasets
for agricultural berry detection using YOLOv11n model.

Usage:
    python yolov11n_finetuning.py --cam_id 1 --epochs 5 --batch_size 8 --image_size 1280

Help message:
    python yolov11n_finetuning.py --help
"""

import argparse
import os
import subprocess
import sys
from tqdm import tqdm


def write_yolov11n_config(dataset_path, filepath):
    """
    Write a YOLOv11n dataset config YAML file.

    Args:
        dataset_path (str): Path to the dataset root.
        filepath (str): Output YAML filename.
    """
    content = f"""path: {dataset_path}
train: 'train/images'
val: 'valid/images'

# class names
names:
  0: 'Riped berries'
"""
    with open(filepath, "w") as f:
        f.write(content)


def run_yolo_command(command, description="Processing"):
    """
    Run a YOLO command using subprocess with progress bar and real-time output.

    Args:
        command (str): The YOLO command to execute.
        description (str): Description for the progress bar.
    """
    print(f"Executing: {command}")
    print("-" * 60)
    
    try:
        # Start the process
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,  # Merge stderr with stdout
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Create a progress bar
        with tqdm(desc=description, unit="step", dynamic_ncols=True, leave=True) as pbar:
            output_lines = []
            
            # Read output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    output_lines.append(line)
                    
                    # Print the line immediately for real-time feedback
                    tqdm.write(line)
                    
                    # Update progress bar based on YOLO output patterns
                    if "Epoch" in line or "epoch" in line:
                        # Extract epoch info for progress bar
                        epoch_info = line[:80] if len(line) > 80 else line
                        pbar.set_postfix_str(epoch_info)
                        pbar.update(1)
                    elif "val" in line.lower() or "Valid" in line:
                        pbar.set_postfix_str("Validating...")
                        pbar.update(1)
                    elif "Predict" in line or "predict" in line or "inference" in line.lower():
                        pbar.set_postfix_str("Running predictions...")
                        pbar.update(1)
                    elif "image" in line.lower() and ("/" in line or "%" in line):
                        # For inference progress
                        pbar.set_postfix_str("Processing images...")
                        pbar.update(1)
                    elif line.strip() and not line.startswith(" "):
                        # Update for any significant output
                        pbar.update(1)
        
        # Check return code
        return_code = process.poll()
        
        if return_code != 0:
            print(f"\nError: Command failed with return code: {return_code}")
            sys.exit(1)
            
        print(f"\n{description} completed successfully!")
        print("-" * 60)
            
    except Exception as e:
        print(f"Exception while executing command: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="YOLOv11n Fine-tuning for Agricultural Cobot")
    parser.add_argument("--cam_id", type=int, required=True, 
                        help="Camera ID (1 or 2)")
    parser.add_argument("--epochs", type=int, default=5,
                        help="Number of training epochs (default: 5)")
    parser.add_argument("--batch_size", type=int, default=8,
                        help="Batch size for training (default: 8)")
    parser.add_argument("--image_size", type=int, default=1280,
                        help="Image size for training (default: 1280)")
    
    args = parser.parse_args()
    
    # Define global variables for image and label paths
    cam_id = args.cam_id
    epochs = args.epochs
    batch_size = args.batch_size
    image_size = args.image_size
    
    DATASET_PATH = f"../data/camera_{cam_id}"
    
    # Check if dataset path exists
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset path {DATASET_PATH} does not exist!")
        sys.exit(1)
    
    print(f"Starting YOLOv11n fine-tuning for camera {cam_id}")
    print(f"Parameters: epochs={epochs}, batch_size={batch_size}, image_size={image_size}")
    
    # Create dataset configuration file
    DATA_CONFIG = f"yolov11n_config_camera_{cam_id}.yaml"
    write_yolov11n_config(DATASET_PATH, DATA_CONFIG)
    print(f"Created dataset config: {DATA_CONFIG}")
    
    # Define model paths
    BASE_MODEL = "yolo11n.pt"
    BEST_MODEL = f"runs/detect/camera_{cam_id}/yolov11n_train/weights/best.pt"
    
    # Fine-tuning
    print("\n" + "="*50)
    print("STARTING FINE-TUNING")
    print("="*50)
    
    train_command = f"""yolo task=detect mode=train model={BASE_MODEL} imgsz={image_size} epochs={epochs} batch={batch_size} data={DATA_CONFIG} name="camera_{cam_id}/yolov11n_train" """
    run_yolo_command(train_command, f"Training YOLOv11n (Camera {cam_id})")
    
    # Evaluation
    print("\n" + "="*50)
    print("STARTING EVALUATION")
    print("="*50)
    
    eval_command = f"""yolo task=detect mode=val model={BEST_MODEL} data={DATA_CONFIG} name="camera_{cam_id}/yolov11n_eval" """
    run_yolo_command(eval_command, f"Evaluating Model (Camera {cam_id})")
    
    # Inference
    print("\n" + "="*50)
    print("STARTING INFERENCE")
    print("="*50)
    
    inference_command = f"""yolo task=detect mode=predict model={BEST_MODEL} source="../data/camera_{cam_id}/valid/images" imgsz={image_size} name="camera_{cam_id}/yolov11n_inference" hide_labels=True"""
    run_yolo_command(inference_command, f"Running Inference (Camera {cam_id})")
    
    print("\n" + "="*50)
    print("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*50)
    print(f"Best model saved at: {BEST_MODEL}")
    print(f"Evaluation results saved in: runs/detect/camera_{cam_id}/yolov11n_eval/")
    print(f"Inference results saved in: runs/detect/camera_{cam_id}/yolov11n_inference/")


if __name__ == "__main__":
    main()
