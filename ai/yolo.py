from typing import Any
from ultralytics import YOLO
import numpy as np

from PIL import ImageFile


class YOLOEmbed:
    model_predict: YOLO
    model_embed: YOLO

    def __init__(self, model_path: str) -> None:
        self.model_predict = self.__load_yolo(model_path)
        self.model_embed = self.__load_yolo(model_path)

    def __load_yolo(self, model_path: str) -> YOLO:
        return YOLO(model=model_path, verbose=False)

    def embed(self, image: list[ImageFile.ImageFile]):
        return self.model_embed.embed(image, stream=False)

    def predict(self, image: list[ImageFile.ImageFile]):
        return self.model_predict.predict(image, stream=False, verbose=False)


class YOLOEmbedStub:
    def __init__(self) -> None:
        pass

    def embed(self, image: Any):
        return [np.ones(512)]

    def predict(self, image: Any):
        return [np.ones(512)]
