New-Item "weights" -ItemType Directory

Invoke-WebRequest https://www.kaggle.com/api/v1/models/letruonggiangk17ct/culcon_yolo/pyTorch/default/2/download -OutFile yolo.tar.gz

tar -xf yolo.tar.gz -C weights

Invoke-WebRequest https://openaipublic.azureedge.net/clip/models/3035c92b350959924f9f00213499208652fc7ea050643e8b385c2dac08641f02/ViT-L-14-336px.pt -OutFile weights/ViT-L-14-336px.pt

podman pull docker.io/giangltce/culcon_admin_backend:main

podman compose up
