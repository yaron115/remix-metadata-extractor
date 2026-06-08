import json
from pathlib import Path
import re
import shutil

from PIL import Image

from utils.constants import (
    INPUT_CSS_PORTRAIT_PATH,
    INPUT_STAGE_ICON_PATH,
    INPUT_STOCK_ICON_PATH,
    OUTPUT_STARTGG_CHARACTERS,
    OUTPUT_STARTGG_JSON,
    OUTPUT_TOP8ER_PORTRAITS,
)
from utils.helpers import ensure_path


def bundle_startgg_full_character_portraits():
    print('Copying full character portraits to startgg folder...')

    ensure_path(OUTPUT_STARTGG_CHARACTERS)
    character_dirs = [f for f in Path(OUTPUT_TOP8ER_PORTRAITS).iterdir() if f.is_dir()]
    for character_dir in character_dirs:
        icon = Path(f'{character_dir}/0.png')
        character_name = icon.parent.name
        ensure_path(f'{OUTPUT_STARTGG_CHARACTERS}/{character_name}')
        shutil.copy(icon, f'{OUTPUT_STARTGG_CHARACTERS}/{character_name}/icon.png')

    print('Done.')


def bundle_startgg_stock_icons():
    print('Resizing stock icons and saving to startgg folder...')
    ensure_path(OUTPUT_STARTGG_CHARACTERS)
    # Only copy the default stock icons; startgg doesn't support alt colors yet
    stock_icon_list = [
        f for f in Path(f'{INPUT_STOCK_ICON_PATH}/base_files/icon').iterdir()
        if f.is_file() and f.name.endswith('_0.png')
    ]
    for stock_icon in stock_icon_list:
        character_match = re.search(r'^(.*)_0\.png$', stock_icon.name)
        character_name = character_match.group(1)
        normalized_character_name = character_name.replace('_', ' ').title()
        if character_name.lower() != 'random':
            ensure_path(f'{OUTPUT_STARTGG_CHARACTERS}/{normalized_character_name}')
            img = Image.open(stock_icon).convert('RGBA')
            # start.gg requires square icons that are at least 30x30.  The originals are 8x10.  We'll add two blank rows
            # of width, one on each side; and then simply 3x scale the image.
            canvas = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
            canvas.paste(img, (1, 0))
            resized = canvas.resize((30, 30), Image.NEAREST)
            resized.save(f'{OUTPUT_STARTGG_CHARACTERS}/{normalized_character_name}/stock_icon.png')

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
