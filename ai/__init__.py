from typing import Any
from . import yolo, clip

weights_dir = "./ai/weights"


def load_all_model() -> dict[Any, Any]:
    return {
        "yolo": yolo.YOLOEmbed(f"{weights_dir}/yolo11m-cls.pt"),
        "clip": clip.OpenCLIP("ViT-L-14-336", "./ai/weights/ViT-L-14-336px.pt"),
    }


def load_all_stub_model() -> dict[Any, Any]:
    return {
        "yolo": yolo.YOLOEmbedStub(),
        "clip": clip.OpenCLIPStub(),
    }
