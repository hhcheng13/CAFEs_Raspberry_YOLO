#!/usr/bin/env bash

# yolo_datasets_download.sh
# Downloads specific folders from Google Drive into the data directory.

set -e

DATA_DIR="../data"
GDRIVE_IDS=(
    "1NftHjOjW-JEAdxf4_9Uj9KlFBILeoFh9?usp=drive_link"
    "1VNMm-S_Z1kmz2iTfRNxQFFc92ma5Y2j0?usp=drive_link"
)
FOLDER_NAMES=(
    "camera_1"
    "camera_2"
)

echo "=== YOLO Dataset Downloader ==="

# Check for gdown installation
if ! command -v gdown &> /dev/null; then
    echo "gdown not found. Installing via pip..."
    pip install --user gdown
fi

# Create data directory if it doesn't exist
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating data directory at $DATA_DIR"
    mkdir -p "$DATA_DIR"
fi

# Download each folder
for i in "${!GDRIVE_IDS[@]}"; do
    ID="${GDRIVE_IDS[$i]}"
    NAME="${FOLDER_NAMES[$i]}"
    DEST="$DATA_DIR/$NAME"
    echo "----------------------------------------"
    echo "Downloading folder '$NAME' from Google Drive..."
    gdown --folder "https://drive.google.com/drive/folders/$ID" --remaining-ok -O "$DEST"
    echo "Downloaded '$NAME' to $DEST"
done

echo "=== All datasets downloaded successfully! ==="