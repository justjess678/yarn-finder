import math
from io import BytesIO

import numpy as np
import requests
from PIL import Image


class ColorSelector:

    def __init__(self, white_threshold: int = 200):
        self.white_threshold = white_threshold

    def get_color_from_url(self, url: str):
        response = requests.get(url, timeout=10)
        return self.get_color_from_bytes(response.content)

    def get_color_from_path(self, path: str):
        image = Image.open(path).convert("RGB")
        return self._dominant_non_white(image)

    def get_color_from_bytes(self, data: bytes):
        image = Image.open(BytesIO(data)).convert("RGB")
        return self._dominant_non_white(image)

    def _dominant_non_white(self, image: Image.Image):
        pixels = np.array(image).reshape(-1, 3)
        mask = np.all(pixels < self.white_threshold, axis=1)
        non_white = pixels[mask]
        if len(non_white) == 0:
            return None
        unique, counts = np.unique(non_white, axis=0, return_counts=True)
        return tuple(unique[counts.argmax()].tolist())


def color_difference(color1: tuple, color2: tuple) -> float:
    r1, g1, b1 = map(float, color1)
    r2, g2, b2 = map(float, color2)
    return math.sqrt((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2)
