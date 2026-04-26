import argparse

from utils.downloaders import download_all
from utils.parrygg import create_parrygg_character_json, create_parrygg_stage_json, get_parrygg_project_dir
from utils.startgg import create_startgg_json, bundle_startgg_css_portraits, bundle_startgg_stock_icons
from utils.top8er import create_top8er_json, bundle_icons_top8er, bundle_portraits_top8er


def main_top8er():
    bundle_portraits_top8er()
    bundle_icons_top8er()
    create_top8er_json()


def main_parrygg():
    project_dir = get_parrygg_project_dir()
    create_parrygg_character_json(project_dir)
    create_parrygg_stage_json(project_dir)


def main_startgg():
    bundle_startgg_css_portraits()
    bundle_startgg_stock_icons()
    create_startgg_json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-download', action='store_true')
    args = parser.parse_args()
    if not args.skip_download:
        download_all()

    main_top8er()
    main_startgg()
    main_parrygg()
