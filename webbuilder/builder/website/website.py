"""
Represents a website once built :
- one folder for the website, named after the path of its site_url, holding one folder per version ("latest" for the latest
version). 
- a page that redirects to the latest version. 
This layout is decided here only, with the names of file_and_folder_names.py; every other class asks.
"""

import os
from pathlib import Path

from webbuilder.builder.files.file_and_folder_names import REDIRECTION_FILE_NAME
from webbuilder.builder.settings.website import Website

from webbuilder.builder.website.settings.website_versions import WebsiteVersion

REDIRECTION_PAGE: str = (
    '<!DOCTYPE html>\n<meta charset="utf-8">\n<meta http-equiv="refresh" content="0; url={folder}/">\n'
    '<a href="{folder}/">Latest version</a>\n'
)


class Website:
    """The places of the files of one website in the folder of the built websites."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, built_websites_folder: Path, website: Website) -> None:
        self._website: Website = website
        self._folder: Path = built_websites_folder.joinpath(website.get_site_url_path())  # as on the server


    # -- Public: places ------------------------------------------------------------------------------

    def get_folder(self) -> Path:
        """The folder of the website."""
        return self._folder


    def get_site_name(self) -> str:
        """The name of the website."""
        return self._website.get_site_name()


    def get_version_folder(self, version: WebsiteVersion) -> Path:
        """The folder of a version in the website."""
        return self._folder.joinpath(self._website.get_website_version_list().folder_in_website_of(version))


    def get_latest_version_folder(self) -> Path:
        """The folder of the latest version in the website."""
        return self.get_version_folder(self._website.get_website_version_list().get_latest_version())


    def get_search_index_file(self, search_index_file_name: str) -> Path:
        """The search index of the latest version, the only one shared between the websites."""
        return self.get_latest_version_folder().joinpath(search_index_file_name)


    def get_path_to_latest_version_of(self, other: "BuiltWebsite") -> str:
        """The relative path from the latest version of this website to the latest version of another one."""
        relative_path: str = os.path.relpath(other.get_latest_version_folder(), start=self.get_latest_version_folder())
        return Path(relative_path).as_posix()


    # -- Public: redirection -------------------------------------------------------------------------

    def write_redirection_to_latest_version(self) -> None:
        """Writes the page at the root of the website, which sends the reader to the latest version."""
        redirection_file: Path = self._folder.joinpath(REDIRECTION_FILE_NAME)
        redirection_file.write_text(REDIRECTION_PAGE.format(folder=self.get_latest_version_folder().name), encoding="utf-8")
