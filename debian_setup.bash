#/bin/bash

mkdir "/workdir/app" -p

wget -q https://openaipublic.azureedge.net/clip/models/b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt -P ./ai/weights

curl -sS -L -o /tmp/model.tar.gz "https://www.kaggle.com/api/v1/models/letruonggiangk17ct/culcon_yolo/pyTorch/default/2/download"

tar -xf /tmp/model.tar.gz -C ./ai/weights
