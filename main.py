import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import shutil
import sys

from colorthief import ColorThief
import numpy as np
from PIL import Image, ImageDraw, ImageChops
import py7zr
import requests
from sklearn.metrics import mean_squared_error
import webcolors

# Asset URLs
FULL_PORTRAIT_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.full.7z.001'
ICON_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.base_files.7z.001'
CSS_PORTRAIT_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.portrait.7z.001'
STAGE_ICON_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.stage_icon.7z.001'
ARTWORK_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.artwork.7z.001'

# Asset input paths
INPUT_PORTRAIT_PATH = 'input/remix_assets/remix_full_portraits'
INPUT_STOCK_ICON_PATH = 'input/remix_assets/remix_stock_icons'
INPUT_CSS_PORTRAIT_PATH = 'input/remix_assets/remix_css_portraits'
INPUT_STAGE_ICON_PATH = 'input/remix_assets/remix_stage_icons'
INPUT_ARTWORK_PATH = 'input/remix_assets/remix_character_artwork'

# Asset output paths
OUTPUT_TOP8ER_PORTRAITS = 'output/top8er/smash_remix/portraits'
OUTPUT_TOP8ER_ICONS = 'output/top8er/smash_remix/icons'
OUTPUT_TOP8ER_JSON = 'output/top8er/smash_remix/game.json'
OUTPUT_STARTGG_CSS_PORTRAITS = 'output/startgg/css_portraits'
OUTPUT_STARTGG_STOCK_ICONS = 'output/startgg/stock_icons'
OUTPUT_STARTGG_JSON = 'output/startgg/reference.json'

# Reference files used for overrides etc
REF_TOP8ER_PORTRAIT = 'reference/top8er_reference/portrait_config.json'


# --- Helpers ---
def ensure_path(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)


def download_chunked(url, dest_path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def extract_7zr(path, dest_path):
    with py7zr.SevenZipFile(path, mode='r') as archive:
        archive.extractall(path=dest_path)


def download_extract(download_url, temp_name, dest_path, object_name):
    print(f'Downloading {object_name} archive...')
    download_chunked(download_url, temp_name)

    print(f'Done. Extracting & deleting {object_name} archive...')
    extract_7zr(temp_name, dest_path)
    os.remove(temp_name)
    print('Done.')


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


# --- Downloaders ---
def check_character_image_counts():
    print('Checking that icon and portrait counts match...')
    portrait_list = [f for f in Path(f'{INPUT_PORTRAIT_PATH}/full/').iterdir()
                     if f.is_file() and f.name.endswith('.png')]
    icon_list = [f for f in Path(f'{INPUT_STOCK_ICON_PATH}/base_files/icon/').iterdir() if
                 f.is_file() and f.name.endswith('.png') and not f.name.startswith('random_')]

    if len(portrait_list) != len(icon_list):
        raise f'Portrait count: {len(portrait_list)} icon count: {len(icon_list)}'


def download_all():
    ensure_path('input/remix_assets')

    # Download image archives & extract
    download_extract(FULL_PORTRAIT_URL, 'remix_portraits.7z', INPUT_PORTRAIT_PATH, 'portraits')
    download_extract(ICON_URL, 'remix_icons.7z', INPUT_STOCK_ICON_PATH, 'stock icons')
    download_extract(CSS_PORTRAIT_URL, 'remix_css_portraits.7z', INPUT_CSS_PORTRAIT_PATH, 'CSS portraits')
    download_extract(STAGE_ICON_URL, 'remix_stages.7z', INPUT_STAGE_ICON_PATH, 'stage icons')
    download_extract(ARTWORK_URL, 'remix_artwork.7z', INPUT_ARTWORK_PATH, 'character artwork')

    # Sanity check for Top8er
    check_character_image_counts()

    # Copy eyesight reference to a file so any manual changes can be tracked
    shutil.copy(f'{INPUT_PORTRAIT_PATH}/full/config.json', REF_TOP8ER_PORTRAIT)
    confirmation = input('Portrait config copied; do you want to quit execution and make updates before formatting portraits? (y/n): ')
    if confirmation.lower() == 'y':
        sys.exit(0)


# --- Top8er asset bundling ---
def format_portraits_top8er():
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


def format_icons_top8er():
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
                color = color.strip()

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


def main_top8er():
    format_portraits_top8er()
    format_icons_top8er()
    create_top8er_json()


# --- startgg asset bundling ---
def format_startgg_css_portraits():
    print('Copying CSS icons to startgg folder...')

    ensure_path(OUTPUT_STARTGG_CSS_PORTRAITS)
    css_portrait_list = [f for f in Path(f'{INPUT_CSS_PORTRAIT_PATH}/portrait').iterdir() if f.is_file() and f.name.endswith('.png')]
    for css_portrait in css_portrait_list:
        character_match = re.search(r'^(.*)\.png$', css_portrait.name)
        character_name = character_match.group(1)
        if character_name.lower() != 'random':
            shutil.copy(css_portrait, f'{OUTPUT_STARTGG_CSS_PORTRAITS}/{css_portrait.name}')

    print('Done.')


def format_startgg_stock_icons():
    print('Copying CSS icons to startgg folder...')
    ensure_path(OUTPUT_STARTGG_STOCK_ICONS)
    # Only copy the default stock icons; startgg doesn't support alt colors yet
    stock_icon_list = [f for f in Path(f'{INPUT_STOCK_ICON_PATH}/base_files/icon').iterdir() if f.is_file() and f.name.endswith('_0.png')]
    for stock_icon in stock_icon_list:
        character_match = re.search(r'^(.*)_0\.png$', stock_icon.name)
        character_name = character_match.group(1)
        if character_name.lower() != 'random':
            shutil.copy(stock_icon, f'{OUTPUT_STARTGG_STOCK_ICONS}/{character_name}.png')

    print('Done.')


def create_startgg_json():
    print('Creating startgg character/stage list reference JSON...')
    character_list = []
    stage_list = []
    character_name_file_list = [
        x.name for x in Path(f'{INPUT_CSS_PORTRAIT_PATH}/portrait').iterdir() if x.is_file() and x.name.endswith('.png')
    ]
    for c in character_name_file_list:
        character_match = re.search(r'^(.*)\.png$', c)
        character_name = character_match.group(1)
        if character_name.lower() != 'random':
            this_name = character_name.title().replace('_', ' ')
            character_list.append(this_name)

    stage_name_file_list = [
        x.name for x in Path(f'{INPUT_STAGE_ICON_PATH}/stage_icon').iterdir() if x.is_file() and x.name.endswith('.png')
    ]
    for s in stage_name_file_list:
        stage_match = re.search(r'^(.*)\.png$', s)
        stage_name = stage_match.group(1)
        if stage_name.lower() != 'random':
            this_name = stage_name.title().replace('_', ' ')
            stage_list.append(this_name)

    json_data = {
        "characters": sorted(character_list),
        "stages": sorted(stage_list),
    }
    with open(OUTPUT_STARTGG_JSON, 'w') as outfile:
        json.dump(json_data, outfile, indent=2)

    print('Done.  May want to manually correct casing/apostrophes for some stage names.')


def main_startgg():
    format_startgg_css_portraits()
    format_startgg_stock_icons()
    create_startgg_json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-download', action='store_true')
    args = parser.parse_args()
    if not args.skip_download:
        download_all()

    main_top8er()
    main_startgg()
