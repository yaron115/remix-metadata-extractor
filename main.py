import argparse

from utils.downloaders import download_all
from utils.parrygg import create_parrygg_character_json, create_parrygg_stage_json, get_parrygg_project_dir
from utils.startgg import bundle_startgg_full_character_portraits, bundle_startgg_stock_icons
from utils.top8er import bundle_icons_top8er, bundle_portraits_top8er


def main_top8er():
    bundle_portraits_top8er()
    bundle_icons_top8er()


def main_parrygg():
    project_dir = get_parrygg_project_dir()
    create_parrygg_character_json(project_dir)
    create_parrygg_stage_json(project_dir)


def main_startgg():
    bundle_startgg_full_character_portraits()
    bundle_startgg_stock_icons()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Notice that these are expected to run in sequence right now, however you can manually run a subset if needed
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--top8er', action='store_true')
    parser.add_argument('--startgg', action='store_true')
    parser.add_argument('--parrygg', action='store_true')
    args = parser.parse_args()
    if args.download:
        print(f'{'=' * 25}\nDownloading assets from StreamHelperAssets...')
        download_all()

    if args.top8er:
        print(f'{'=' * 25}\nBundling Top8er files...')
        main_top8er()

    if args.startgg:
        print(f'{'=' * 25}\nBundling start.gg files...')
        main_startgg()

    if args.parrygg:
        print(f'{'=' * 25}\nBundling parry.gg files...')
        main_parrygg()
