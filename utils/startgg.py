import json
from pathlib import Path
import re
import shutil

from utils.constants import (
    INPUT_CSS_PORTRAIT_PATH,
    INPUT_STAGE_ICON_PATH,
    INPUT_STOCK_ICON_PATH,
    OUTPUT_STARTGG_CSS_PORTRAITS,
    OUTPUT_STARTGG_JSON,
    OUTPUT_STARTGG_STOCK_ICONS,
)
from utils.helpers import ensure_path


def bundle_startgg_css_portraits():
    print('Copying CSS icons to startgg folder...')

    ensure_path(OUTPUT_STARTGG_CSS_PORTRAITS)
    css_portrait_list = [f for f in Path(f'{INPUT_CSS_PORTRAIT_PATH}/portrait').iterdir() if f.is_file() and f.name.endswith('.png')]
    for css_portrait in css_portrait_list:
        character_match = re.search(r'^(.*)\.png$', css_portrait.name)
        character_name = character_match.group(1)
        if character_name.lower() != 'random':
            shutil.copy(css_portrait, f'{OUTPUT_STARTGG_CSS_PORTRAITS}/{css_portrait.name}')

    print('Done.')


def bundle_startgg_stock_icons():
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
