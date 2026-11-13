"""
This script is the entry point of the tool: it builds the websites from the command line.

Usage:
    python main.py --websites-folder <folder> --build-websites
        Builds every website of the websites folder.
    python main.py --websites-folder <folder> --build-websites pamela connie
        Builds only the websites named.
    python main.py --websites-folder <folder> --build-websites pamela --build-versions 1.6 1.6.1
        Builds only the versions named of one website; the other versions of the website are left as they are.

A website is a sub-folder of the websites folder holding a website_settings.yml and a versions folder with one
file per version. Each version is cloned from git at its git_ref and built with Zensical. The website is in
<websites folder>/build/<path of its site_url>: each version in a folder named after it, and a copy of the latest
one in the folder "latest".

Runs every step of a build: it reads the settings (step 1), has WebsiteBuilder build each website (steps 2 to 5),
then has GlobalSearch merge the search of all the websites (step 6). The steps are listed in webbuilder/README.md.
"""

import argparse
from pathlib import Path

from webbuilder.builder.paths.build_paths import (
    BUILT_WEBSITES_FOLDER_NAME,
    PREPARATION_FOLDER_NAME,
    WEBSITE_SEARCH_INDEX_FILE_NAME,
    WEBSITE_SETTINGS_FILE_NAME,
)
from webbuilder.builder.paths.shared_paths import SHARED_HTML_TEMPLATES_FOLDER
from webbuilder.builder.search.global_search import GlobalSearch
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.builder.website.helper.website_scanner import WebsiteScanner
from webbuilder.builder.website.built_website import BuiltWebsite
from webbuilder.builder.website.website_builder import WebsiteBuilder
from webbuilder.common.helper.clone_git_repository import CloneGitRepository

from webbuilder.common.openflexo_interfaces import SiteGeneratorInterface
from webbuilder.zensical.zensical_site_generator import ZensicalSiteGenerator


# -- Public: entry point --------------------------------------------------------------------------------

def run(arguments: argparse.Namespace, site_generator: SiteGeneratorInterface) -> None:
    """This function builds the websites named in the arguments, then gives every built website the search of all the others."""
    
    # Step 1: read the settings of every website.
    website_scanner: WebsiteScanner = WebsiteScanner(arguments.websites_folder, WEBSITE_SETTINGS_FILE_NAME)
    website_by_name: dict[str, WebsiteSettings] = {
        website_name: WebsiteSettings(settings_file) for website_name, settings_file in website_scanner.get_settings_files([]).items()
    }
    
    # Steps 2 to 5: build each website named.
    built_websites_folder: Path = arguments.websites_folder.joinpath(BUILT_WEBSITES_FOLDER_NAME)
    for website_name in website_scanner.get_settings_files(arguments.build_websites):
        _build_website(website_name, website_by_name[website_name], site_generator, built_websites_folder, arguments.build_versions)

    # Step 6: merge the search of the websites.
    # The search covers every website, also the ones not rebuilt now.
    shared_search: GlobalSearch = GlobalSearch(built_websites_folder, site_generator, WEBSITE_SEARCH_INDEX_FILE_NAME)
    shared_search.merge(website_by_name)


# -- Private: build -------------------------------------------------------------------------------------

def _build_website(
    website_name: str,
    website: WebsiteSettings,
    site_generator: SiteGeneratorInterface,
    built_websites_folder: Path,
    version_names: list[str],
) -> None:
    """This function builds the named versions of one website (all if none is named) and puts them in the built websites folder."""
    print(f"== Website {website_name}")
    git_repository: CloneGitRepository = CloneGitRepository(website.get_repository_url())
    preparation_folder: Path = website.get_settings_folder().joinpath(PREPARATION_FOLDER_NAME)
    built_website: BuiltWebsite = BuiltWebsite(built_websites_folder, website)
    WebsiteBuilder(website, git_repository, site_generator, preparation_folder, built_website).build(version_names)


# -- Private: command line ------------------------------------------------------------------------------

def _existing_folder(argument: str) -> Path:
    """This function returns the folder given on the command line, and refuses a folder that does not exist."""
    folder: Path = Path(argument)
    if not folder.is_dir():
        raise argparse.ArgumentTypeError(f"{folder} is not an existing folder")
    return folder


def _parse_arguments() -> argparse.Namespace:
    """This function reads the command line, and refuses --build-versions unless exactly one website is named."""
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
    run(_parse_arguments(), ZensicalSiteGenerator(SHARED_HTML_TEMPLATES_FOLDER))  # Zensical is the tool that builds the sites
