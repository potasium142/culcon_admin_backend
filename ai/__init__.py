from . import yolo


def load_all_model() -> dict:
    models = dict()

    models["yolo"] = yolo.load_yolo("./ai/weights/yolo11m-cls.pt")

    return models
