from collections import defaultdict
import json
import os
from pathlib import Path
import re
import shutil

from colorthief import ColorThief
from PIL import (
    Image,
    # ImageDraw,
    ImageChops,
)
# import webcolors

from utils.constants import (
    INPUT_PORTRAIT_PATH,
    INPUT_STOCK_ICON_PATH,
    OUTPUT_TOP8ER_ICONS,
    OUTPUT_TOP8ER_JSON,
    OUTPUT_TOP8ER_PORTRAITS,
    REF_TOP8ER_PORTRAIT,
)
from utils.helpers import (
    ensure_path,
    get_closest_css3_color,
    # most_frequent_color
)


def bundle_portraits_top8er():
    print('Cropping and structuring portraits for Top8er...')
    ensure_path(OUTPUT_TOP8ER_PORTRAITS)
    portrait_list = [f for f in Path(f'{INPUT_PORTRAIT_PATH}/full/').iterdir()
                     if f.is_file() and f.name.endswith('.png')]

    with open(REF_TOP8ER_PORTRAIT, 'r', encoding='utf-8') as f:
        portrait_metadata = json.load(f)

    eye_levels = portrait_metadata['eyesights']
    for portrait in portrait_list:
        format_portrait_top8er(portrait, eye_levels)

    print('Done.')


def format_portrait_top8er(portrait, eye_levels):
    # Get character/color metadata
    character_match = re.search(r'^(.*)_', portrait.name)
    character_name = character_match.group(1)
    color_match = re.search(r'_([^._]+)\.[^.]*$', portrait.name)
    color_number = color_match.group(1)
    snakecase_character_name = character_name.lower()
    normalized_character_name = character_name.replace('_', ' ').title()
    eye_offsets = eye_levels.get(snakecase_character_name, {}).get(str(color_number))
    if eye_offsets is None:
        eye_offsets = eye_levels[snakecase_character_name]['0']

    ensure_path(f'{OUTPUT_TOP8ER_PORTRAITS}/{normalized_character_name}')

    # Crop into a square or very close, so we don't have any aspect ratio-related black bars and save in dest.
    # Use the width as the main driver for size, but with a minimum of 512.
    # We do this all relative to the eye level of the character if it's low enough, so we don't end up with just Lanky's
    # hands above his head or something.  I'm aiming to put the eyes about 1/3 of the way down the image, which works
    # well for most characters.  For some like Falcon/Yoshi/Slippy, I recommend editing the JSON to target lower
    # instead, as otherwise we'll have quite a bit of space above his head.
    # TODO: just define custom square bounds for all the characters instead.
    img = Image.open(portrait)
    bbox = img.getbbox()
    width = bbox[2] - bbox[0]
    if width < 512:
        width = 512

    eye_y = eye_offsets['y']
    left_bound = bbox[0]
    right_bound = bbox[0] + width
    upper_bound = eye_y - (width // 3)
    if upper_bound < 0:
        upper_bound = 0
        lower_bound = width
    else:
        lower_bound = eye_y + ((width // 3) * 2)

    box = (left_bound, upper_bound, right_bound, lower_bound)
    cropped_img = img.crop(box)
    cropped_img.save(f'{OUTPUT_TOP8ER_PORTRAITS}/{normalized_character_name}/{color_number}.png')


def bundle_icons_top8er():
    print('Structuring icons for Top8er...')
    ensure_path(OUTPUT_TOP8ER_ICONS)
    # Notice that we're dropping random since it doesn't have a portrait (for now at least)
    icon_list = [f for f in Path(f'{INPUT_STOCK_ICON_PATH}/base_files/icon/').iterdir() if
                 f.is_file() and f.name.endswith('.png') and not f.name.startswith('random_')]

    for icon in icon_list:
        format_icon(icon)

    print('Done.')


def format_icon(icon):
    # Get character/color metadata
    match = re.search(r'^(.*)_', icon.name)
    character_name = match.group(1)
    color_match = re.search(r'_([^._]+)\.[^.]*$', icon.name)
    color_number = color_match.group(1)
    normalized_character_name = character_name.replace('_', ' ').title()

    ensure_path(f'{OUTPUT_TOP8ER_ICONS}/{normalized_character_name}')
    shutil.copy(icon, f'{OUTPUT_TOP8ER_ICONS}/{normalized_character_name}/{color_number}.png')


def create_top8er_json():
    print('Creating JSON file for Top8er...')
    character_name_list = [
        x.name for x in Path(OUTPUT_TOP8ER_PORTRAITS).iterdir() if x.is_dir()
    ]
    colors_by_character = defaultdict(list)
    for char in sorted(character_name_list):
        icons = sorted([x for x in Path(f'{OUTPUT_TOP8ER_ICONS}/{char}').iterdir() if x.is_file()])
        for icon in icons:
            icon_num = int(icon.name.split('.')[0])
            if icon_num == 0:
                color = 'Default'
            else:
                # Find dominant color
                # img = Image.open(icon).convert('RGB')
                # quantized = img.quantize(colors=1)
                # palette = quantized.getpalette()
                # color = webcolors.rgb_to_name(palette)

                # Find dominant color difference between this and main icon, and use that to "seed" a color name
                # that we'll probably overwrite
                original_img = Image.open(f'{OUTPUT_TOP8ER_ICONS}/{char}/0.png').convert('RGB')
                img = Image.open(icon).convert('RGB')
                diff = ImageChops.difference(original_img, img)
                # palette = most_frequent_color(diff)
                # color = webcolors.rgb_to_name(palette)
                diff.save('temp.png')
                palette = ColorThief('temp.png').get_color(quality=1)
                color = get_closest_css3_color(palette)
                os.remove('temp.png')

            if color not in colors_by_character.get(char, []):
                colors_by_character[char].append(color)
            else:
                # Add a number afterwards to make the color names unique
                existing_colors = colors_by_character[char]
                max_matched_number = 1
                for existing_color in existing_colors:
                    match = re.search(r'^(.*?) ?\d*$', existing_color)
                    existing_color_name = match.group(1)
                    if color == existing_color_name:
                        match = re.search(r'^.* ?(\d+)$', existing_color)
                        if match is not None:
                            _num = match.group(1)
                            if _num != '':
                                _num = int(match.group(1))
                                if _num > max_matched_number:
                                    max_matched_number = _num

                colors_by_character[char].append(f'{color} {max_matched_number + 1}')

    json_data = {
        "name": "Smash Remix",
        "characters": sorted(character_name_list),
        "hasIcons": True,
        "colors": colors_by_character,
        # "iconColors": colors_by_character,
        "blackSquares": True,
        "defaultLayoutColors": [
            "#1f0141",
            "#ffff11"
        ],
        "colorGuide": None
    }
    with open(f'{OUTPUT_TOP8ER_JSON}', 'w') as outfile:
        json.dump(json_data, outfile, indent=2)

    print('Done.')
