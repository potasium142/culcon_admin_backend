from ultralytics import YOLO
import numpy as np


class YOLOEmbed:
    model: YOLO

    def __init__(self, model_path: str) -> None:
        self.model = self.__load_yolo(model_path)

    def __load_yolo(self, model_path: str) -> YOLO:
        return YOLO(model=model_path)

    def embed(self, image: any):
        return self.model.embed(image, stream=False)


class YOLOEmbedStub:
    def __init__(self) -> None:
        pass

    def embed(self, image: any):
        return [np.ones(512)]
