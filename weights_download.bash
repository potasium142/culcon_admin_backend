#/bin/bas#!/bin/bash

# Default download directory
DOWNLOAD_DIR="weights"

# Parse command line arguments
while getopts "d:h" opt; do
  case $opt in
    d) DOWNLOAD_DIR="$OPTARG" ;;
    h) echo "Usage: $0 [-d download_directory]"; exit 0 ;;
    *) echo "Usage: $0 [-d download_directory]"; exit 1 ;;
  esac
done

# Create the main directory
mkdir -p "$DOWNLOAD_DIR"

# Create weights directory
mkdir -p "$DOWNLOAD_DIR/ai/weights"

echo "Using download directory: $DOWNLOAD_DIR"

# Download model files
curl  -L -o  /tmp/culcon-ml.tar.gz "https://www.kaggle.com/api/v1/models/letruonggiangk17ct/culcon-ml/scikitLearn/default/1/download" 

curl -L -o /tmp/model.tar.gz "https://www.kaggle.com/api/v1/models/letruonggiangk17ct/culcon_yolo/pyTorch/default/2/download"

curl -L -o  "$DOWNLOAD_DIR/ai/weights/ViT-L-14-336px.pt" "https://openaipublic.azureedge.net/clip/models/b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt" 

# Extract the downloaded model
tar -xf /tmp/model.tar.gz -C "$DOWNLOAD_DIR/ai/weights"
tar -xf /tmp/culcon-ml.tar.gz -C "$DOWNLOAD_DIR/ai/weights"

echo "Setup completed successfully in \"$DOWNLOAD_DIR\""
