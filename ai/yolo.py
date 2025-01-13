from ultralytics import YOLO
from numpy import ndarray


class YOLOEmbed:
    model: YOLO

    def __init__(self, model_path: str) -> None:
        self.model = self.__load_yolo(model_path)
        pass

    def __load_yolo(self, model_path: str) -> YOLO:
        return YOLO(model=model_path)

    def embed(self, image: any) -> ndarray:
        return self.model.embed(image, stream=False)
