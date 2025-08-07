#!/usr/bin/env bash

# yolo_models_download.sh
# Downloads specific YOLO model .pt files from Google Drive into the models directory.

set -e

MODEL_DIR="../models"
GDRIVE_IDS=(
    "1WDaEmPz8qNwHAiWK1fCJ-fAMCY8e2mwR?usp=drive_link"
    "1nQee4oUfDgPz_aQ2DbuugEGABTXhtAT4?usp=drive_link"
)
FOLDER_NAMES=(
    "camera_1"
    "camera_2"
)

echo "=== YOLO Model Downloader ==="

# Check for gdown installation
if ! command -v gdown &> /dev/null; then
    echo "gdown not found. Installing via pip..."
    pip install --user gdown
fi

# Create model directory if it doesn't exist
if [ ! -d "$MODEL_DIR" ]; then
    echo "Creating model directory at $MODEL_DIR"
    mkdir -p "$MODEL_DIR"
fi

# Download each model
for i in "${!GDRIVE_IDS[@]}"; do
    ID="${GDRIVE_IDS[$i]}"
    NAME="${FOLDER_NAMES[$i]}"
    DEST="$MODEL_DIR/$NAME"
    echo "----------------------------------------"
    echo "Downloading folder '$NAME' from Google Drive..."
    gdown --folder "https://drive.google.com/drive/folders/$ID" --remaining-ok -O "$DEST"
    echo "Downloaded '$NAME' to $DEST"
done

echo "=== All models downloaded successfully! ==="