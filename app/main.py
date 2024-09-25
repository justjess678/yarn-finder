# main.py
import json
import os

from matplotlib.font_manager import json_load

import color_selector
import image_tools
from color_selector import ColorSelector, color_difference, show_colors
from image_tools import IceYarnsScraper


def main():

    image_tools.make_data()

    reference_color = color_selector.get_reference_color()

    yarn_data = image_tools.read_data()
    print(yarn_data)

    results = []
    for yarn in yarn_data:
        image = yarn_data[yarn].get('image_url', None)
        if image:
            image_exists = image_tools.get_image_by_url(image)
            if image_exists:
                dominant_color = color_selector.get_color_from_image(image_tools.SAVE_PATH)
                if dominant_color:
                    print(f"The most common color in the image (excluding white) is: {dominant_color}")
                    diff = color_difference(reference_color, dominant_color)
                    results.append({
                        "title": yarn_data[yarn]["name"],
                        "link": yarn,
                        "image_url": yarn_data[yarn]["image_url"],
                        "similarity_score": diff
                    })
                else:
                    print("No dominant color found, all pixels might be white or near-white.")

    sorted_results = sorted(results, key=lambda x: x["similarity_score"])

    # Display the sorted results
    for result in sorted_results:
        print(
            f"Title: {result['title']}, Link: {result['link']}, Image URL: {result['image_url']}, Similarity Score: {result['similarity_score']}")

    #show_colors(reference_color, dominant_color)

if __name__ == "__main__":
    main()
