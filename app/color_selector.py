from PIL import Image
import math
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

import image_tools

REFERENCE_IMAGE_PATH = '../reference/ref.jpg'


def get_reference_color(white_threshold=200):
    color_selector = ColorSelector(white_threshold)  # You can adjust the threshold if needed

    reference_image_path = REFERENCE_IMAGE_PATH
    reference_color = color_selector.get_color_from_image(reference_image_path)
    if reference_color:
        return reference_color
    else:
        print("No dominant color found, all pixels might be white or near-white.")
        return None


def show_colors(color1, color2):
    """
    Display two colors side by side using matplotlib.

    :param color1: A tuple representing the first RGB color (e.g., (R, G, B))
    :param color2: A tuple representing the second RGB color (e.g., (R, G, B))
    """
    # Create a blank image (two squares) to display the colors
    color_array = np.zeros((100, 200, 3), dtype=np.uint8)

    # Assign color1 to the left half and color2 to the right half
    color_array[:, :100] = color1  # Left square
    color_array[:, 100:] = color2  # Right square

    # Display the colors
    plt.imshow(color_array)
    plt.axis('off')  # Turn off axes for better presentation
    plt.show()


def color_difference(color1, color2):
    """
    Calculates the Euclidean distance between two RGB colors,
    ensuring that the calculation does not overflow by using floating-point numbers.

    :param color1: A tuple of 3 integers representing the first RGB color (e.g., (R, G, B))
    :param color2: A tuple of 3 integers representing the second RGB color (e.g., (R, G, B))
    :return: The Euclidean distance between the two colors
    """
    # Convert RGB values to floats to avoid overflow
    r1, g1, b1 = map(float, color1)
    r2, g2, b2 = map(float, color2)

    # Calculate the Euclidean distance
    distance = math.sqrt((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2)

    return distance


class ColorSelector:

    def __init__(self, white_threshold:int=200):
        if 256 > white_threshold > -1:
            self.white_threshold = white_threshold

    def get_color_from_image(self, path_to_image:str):
        # Define what "white" is: you can adjust the threshold to be less strict

        image = Image.open(path_to_image)

        pixels = np.array(image)

        pixels = pixels.reshape((-1, 3))  # Each pixel is a tuple of RGB values

        non_white_pixels = [tuple(pixel) for pixel in pixels if all(value < self.white_threshold for value in pixel)]

        pixel_counts = Counter(non_white_pixels)

        if pixel_counts:
            most_common_color = pixel_counts.most_common(1)[0][0]
            return most_common_color
        else:
            return None

    def set_white_threshold(self, white_threshold:int):
        if 256 > white_threshold > -1:
            self.white_threshold = white_threshold

    def get_white_threshold(self):
        return self.white_threshold

    def compare_all_yarn_images(self):
        yarn_data = image_tools.read_data()
        if not yarn_data:
            return
        reference_color = self.get_color_from_image(REFERENCE_IMAGE_PATH)
        if not reference_color:
            return
        results = []
        for yarn in yarn_data:
            image = yarn_data[yarn].get('image_url', None)
            if image:
                image_exists = image_tools.get_image_by_url(image)
                if image_exists:
                    dominant_color = self.get_color_from_image(image_tools.SAVE_PATH)
                    if dominant_color:
                        diff = color_difference(reference_color, dominant_color)
                        results.append({
                            "title": yarn_data[yarn]["name"],
                            "link": yarn,
                            "image_url": yarn_data[yarn]["image_url"],
                            "similarity_score": diff
                        })
                    else:
                        print("No dominant color found, all pixels might be white or near-white.")

        return sorted(results, key=lambda x: x["similarity_score"])


