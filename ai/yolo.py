from ultralytics import YOLO


def load_yolo(model_path: str) -> YOLO:
    return YOLO(model=model_path)
