from pathlib import Path

import numpy as np
from sklearn.metrics import mean_squared_error
import webcolors


def ensure_path(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)


def most_frequent_color(image):
    w, h = image.size
    pixels = image.getcolors(w * h)
    most_frequent_pixel = pixels[0]
    for count, color in pixels:
        # Just skipping white since it's probably transparent in PNG; hopefully any white variants have some
        # off-white in there
        if count > most_frequent_pixel[0] and color != (0, 0, 0):
            most_frequent_pixel = (count, color)

    return most_frequent_pixel[1]


def get_closest_css3_color(rgb_palette):
    rms_lst = []
    # Iterate through all CSS3 named colors
    for img_clr, img_hex in webcolors._definitions._CSS3_NAMES_TO_HEX.items():
        cur_clr = webcolors.hex_to_rgb(img_hex)
        rmse = np.sqrt(mean_squared_error(rgb_palette, cur_clr))
        rms_lst.append(rmse)

    closest_color = rms_lst.index(min(rms_lst))
    return list(webcolors._definitions._CSS3_NAMES_TO_HEX.items())[closest_color][0]
