import json
from pathlib import Path
import shutil

from utils.constants import REF_PARRYGG_VANILLA
from utils.helpers import ensure_path
from utils.parrygg import get_parrygg_project_dir


def parrygg_vanilla_json_copier():
    """
    To be run on https://github.com/parry-gg/game-metadata repo.  Copies all the vanilla Remix JSON to a separate
    vanilla folder.  Run this AFTER assets have been uploaded to CDN for re-use.
    """
    project_dir = get_parrygg_project_dir()
    ensure_path(f'{project_dir}/games/super-smash-bros/characters')
    ensure_path(f'{project_dir}/games/super-smash-bros/stages')

    with open(REF_PARRYGG_VANILLA, 'r', encoding='utf8') as f:
        vanilla_json = json.load(f)

    print('Copying vanilla characters...')
    for character in vanilla_json['characters']:
        shutil.copy(
            f'{project_dir}/games/smash-remix/characters/{character}.json',
            f'{project_dir}/games/super-smash-bros/characters/{character}.json'
        )

    print('Done.  Copying vanilla stages...')
    for stage in vanilla_json['stages']:
        shutil.copy(
            f'{project_dir}/games/smash-remix/stages/{stage}.json',
            f'{project_dir}/games/super-smash-bros/stages/{stage}.json'
        )

    print('Done.')


if __name__ == "__main__":
    parrygg_vanilla_json_copier()
