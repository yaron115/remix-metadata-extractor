import json
import os
import re
import shutil

from dotenv import load_dotenv
from pathlib import Path

from utils.constants import (
    INPUT_STAGE_ICON_PATH,
    INPUT_STOCK_ICON_PATH,
    OUTPUT_PARRYGG_CHARACTER_JSON,
    OUTPUT_PARRYGG_STAGE_JSON,
    OUTPUT_STARTGG_JSON,
    OUTPUT_TOP8ER_JSON
)
from utils.helpers import ensure_path


def create_parrygg_character_json(parry_project_dir):
    ensure_path(OUTPUT_PARRYGG_CHARACTER_JSON)
    with open(OUTPUT_TOP8ER_JSON, 'r', encoding='utf-8') as json_file:
        top8er_json_data = json.load(json_file)

    character_list = top8er_json_data['characters']
    for friendly_character_name in character_list:
        snakecase_name = friendly_character_name.replace(' ', '_').lower()
        # Remove any special characters like apostrophes or periods
        snakecase_name = re.sub(r'[^\w]', '', snakecase_name)
        kebab_name = snakecase_name.replace('_', '-')
        variants = []
        for idx, color_name in enumerate(top8er_json_data['colors'][friendly_character_name]):
            dest_path = Path(f'{parry_project_dir}/games/smash-remix/characters/{kebab_name}-{idx}.png')
            shutil.copy(f'{INPUT_STOCK_ICON_PATH}/base_files/icon/{snakecase_name}_{idx}.png', dest_path)
            color_data = {
                "images": {
                    "stock_icon": './' + os.path.relpath(dest_path, parry_project_dir),
                }
            }
            if color_name.lower() != 'default':
                color_data['metadata'] = {
                    "color": color_name.lower(),
                    "variant": idx
                }

            variants.append(color_data)

        with open(f'{OUTPUT_PARRYGG_CHARACTER_JSON}/{kebab_name}.json', 'w', encoding='utf-8') as outfile:
            character_json = {
                "name": friendly_character_name,
                "variants": variants,
            }
            json.dump(character_json, outfile, indent=2)


def create_parrygg_stage_json(parry_project_dir):
    ensure_path(OUTPUT_PARRYGG_STAGE_JSON)
    with open(OUTPUT_STARTGG_JSON, 'r', encoding='utf-8') as json_file:
        startgg_json_data = json.load(json_file)

    stage_list = startgg_json_data['stages']
    for friendly_stage_name in stage_list:
        snakecase_stage_name = friendly_stage_name.replace(' ', '_').lower()
        # Remove any special characters like apostrophes or periods, except for a few that need them in the filename
        if friendly_stage_name in ('N.Sanity Beach', 'World 1-1'):
            snakecase_stage_name = re.sub(r'\.', '_', snakecase_stage_name)
        else:
            snakecase_stage_name = re.sub(r'[^\w]', '', snakecase_stage_name)

        kebab_stage_name = snakecase_stage_name.replace('_', '-')
        dest_path = Path(f'{parry_project_dir}/games/smash-remix/stages/{kebab_stage_name}.png')
        shutil.copy(f'{INPUT_STAGE_ICON_PATH}/stage_icon/{snakecase_stage_name}.png', dest_path)
        with open(f'{OUTPUT_PARRYGG_STAGE_JSON}/{kebab_stage_name}.json', 'w', encoding='utf-8') as outfile:
            stage_json = {
                "name": friendly_stage_name,
                "variants": [
                    {
                        "images": {
                            "thumbnail": './' + os.path.relpath(dest_path, parry_project_dir)
                        }
                    }
                ]
            }
            json.dump(stage_json, outfile, indent=2)


def get_parrygg_project_dir():
    load_dotenv()
    parry_project_dir = os.getenv('PARRY_PROJECT_DIR')
    if parry_project_dir is None:
        raise(
            'Set PARRY_PROJECT_DIR to the directory of your local https://github.com/parry-gg/game-metadata repo.  You '
            'can store in .env file if you wish.'
        )

    return parry_project_dir
