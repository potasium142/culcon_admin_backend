from typing import Any
from ultralytics import YOLO
import numpy as np

from PIL import ImageFile


class YOLOEmbed:
    model: YOLO

    def __init__(self, model_path: str) -> None:
        self.model = self.__load_yolo(model_path)

    def __load_yolo(self, model_path: str) -> YOLO:
        return YOLO(model=model_path)

    def embed(self, image: list[ImageFile.ImageFile]):
        return self.model.embed(image, stream=False)


class YOLOEmbedStub:
    def __init__(self) -> None:
        pass

    def embed(self, image: Any):
        return [np.ones(512)]
