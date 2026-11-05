"""
Entry point of the website builder.

Usage:
    python main.py --websites-folder <folder> --build-websites
        Builds every website of the websites folder.
    python main.py --websites-folder <folder> --build-websites pamela connie
        Builds only the websites named.
    python main.py --websites-folder <folder> --build-websites pamela --build-versions 1.6 1.6.1
        Builds only the versions named of one website; the other versions of the website are left as they are.

A website is a sub-folder of the websites folder holding a website_settings.yml and a versions folder with one
file per version. Each version is cloned from git at its git_ref and built with Zensical. The website is in
<websites folder>/build/<path of its site_url>: the latest version at its root, each earlier version in a folder
named after it.
"""

import argparse
from pathlib import Path

from webbuilder.building.merge_search_index import MergeSearchIndex
from webbuilder.building.website_build import WebsiteBuild
from webbuilder.repository.git_repository import GitRepository
from webbuilder.scanning.scan_website import ScanWebsite
from webbuilder.settings.website_settings import WebsiteSettings

SETTINGS_FILE_NAME: str = "website_settings.yml"
BUILD_FOLDER_NAME: str = "build"  # the websites as on the server, in the websites folder
PREPARATION_FOLDER_NAME: str = "preparation"  # the preparation of one website, next to its website_settings.yml
INDEX_FILE_NAME: str = "search.json"  # written by Zensical in each website, read by the search of its pages
OWN_INDEX_FILE_NAME: str = "website_search.json"  # the pages of a website alone, kept to merge again


# -- Build ----------------------------------------------------------------------------------------------

def _build_website(website_name: str, website_settings: WebsiteSettings, build_folder: Path, version_names: list[str]) -> None:
    print(f"== Website {website_name}")
    git_repository: GitRepository = GitRepository(website_settings.get_repository_url())
    preparation_folder: Path = website_settings.get_folder().joinpath(PREPARATION_FOLDER_NAME)
    website_folder: Path = build_folder.joinpath(website_settings.get_site_path())  # as on the server
    WebsiteBuild(website_settings, git_repository, preparation_folder, website_folder).build(version_names)


# -- Command line ---------------------------------------------------------------------------------------

def _existing_folder(argument: str) -> Path:
    folder: Path = Path(argument)
    if not folder.is_dir():
        raise argparse.ArgumentTypeError(f"{folder} is not an existing folder")
    return folder


def _parse_arguments() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Builds the websites, with all their versions, from the Markdown of their repositories, using Zensical."
    )
    # python main.py --websites-folder websites --build-websites pamela connie
    parser.add_argument(
        "--websites-folder", type=_existing_folder, required=True, help="folder whose sub-folders each hold a website_settings.yml"
    )
    parser.add_argument(
        "--build-websites", nargs="*", required=True, metavar="NAME", help="names of the websites to build; none means all"
    )
    parser.add_argument(
        "--build-versions", nargs="+", default=[], metavar="NAME", help="names of the versions to build, of one website only"
    )
    arguments: argparse.Namespace = parser.parse_args()
    if arguments.build_versions and len(arguments.build_websites) != 1:
        parser.error("--build-versions needs exactly one website in --build-websites")
    return arguments


if __name__ == "__main__":
    arguments: argparse.Namespace = _parse_arguments()
    scan_website: ScanWebsite = ScanWebsite(arguments.websites_folder, SETTINGS_FILE_NAME)
    website_settings_by_name: dict[str, WebsiteSettings] = {
        website_name: WebsiteSettings(settings_file) for website_name, settings_file in scan_website.get_settings_files([]).items()
    }
    build_folder: Path = arguments.websites_folder.joinpath(BUILD_FOLDER_NAME)
    for website_name in scan_website.get_settings_files(arguments.build_websites):
        _build_website(website_name, website_settings_by_name[website_name], build_folder, arguments.build_versions)

    # The search covers every website, also the ones not rebuilt now.
    merge_search_index: MergeSearchIndex = MergeSearchIndex(build_folder, INDEX_FILE_NAME, OWN_INDEX_FILE_NAME)
    merge_search_index.merge(website_settings_by_name)
