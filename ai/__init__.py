from . import yolo, clip

weights_dir = "./ai/weights"


def load_all_model() -> dict:
    return {
        "yolo": yolo.YOLOEmbed(f"{weights_dir}/yolo11m-cls.pt"),
        "clip": clip.OpenCLIP("ViT-L-14-336", "./ai/weights/ViT-L-14-336px.pt"),
    }
