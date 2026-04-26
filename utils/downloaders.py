import os
from pathlib import Path
import requests
import shutil
import sys

import py7zr

from utils.constants import (
    INPUT_ARTWORK_PATH,
    INPUT_CSS_PORTRAIT_PATH,
    INPUT_PORTRAIT_PATH,
    INPUT_STAGE_ICON_PATH,
    INPUT_STOCK_ICON_PATH,
    REF_TOP8ER_PORTRAIT
)
from utils.helpers import ensure_path


# Asset URLs
FULL_PORTRAIT_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.full.7z.001'
ICON_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.base_files.7z.001'
CSS_PORTRAIT_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.portrait.7z.001'
STAGE_ICON_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.stage_icon.7z.001'
ARTWORK_URL = 'https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/ssb64.artwork.7z.001'


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
