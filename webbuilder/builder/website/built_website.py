"""
This class represents a website (e.g. pamela) once built: where its files are in the folder of the built websites.

A built website has one folder per version, a folder "latest" that copies the latest version, a list of its versions
(versions.json) and a page at its root that redirects to "latest".
This layout is decided here only; every other class asks.

Used at step 5 (put the versions in place) and step 6 (merge the search). WebsiteSettings is the same website before the build.
"""

import json
import os
from pathlib import Path

from webbuilder.builder.paths.build_paths import LATEST_VERSION_FOLDER_NAME, REDIRECTION_FILE_NAME, VERSION_MENU_FILE_NAME
from webbuilder.builder.website.website_settings import WebsiteSettings

from webbuilder.builder.version.version_settings import VersionList, VersionSettings

REDIRECTION_PAGE: str = (
    '<!DOCTYPE html>\n<meta charset="utf-8">\n<meta http-equiv="refresh" content="0; url={folder}/">\n'
    '<a href="{folder}/">Latest version</a>\n'
)


class BuiltWebsite:
    """This class gives the place of each file of one built website."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, built_websites_folder: Path, website: WebsiteSettings) -> None:
        """This constructor sets the folder of the website in the folder of the built websites."""
        self._website: WebsiteSettings = website
        self._folder: Path = built_websites_folder.joinpath(website.get_website_url_path())  # as on the server


    # -- Public: places ------------------------------------------------------------------------------

    def get_folder(self) -> Path:
        """This method returns the folder of the website."""
        return self._folder


    def get_website_name(self) -> str:
        """This method returns the name of the website."""
        return self._website.get_website_name()


    def get_version_folder(self, version: VersionSettings) -> Path:
        """This method returns the folder of a version in the website."""
        return self._folder.joinpath(self._website.get_website_version_list().folder_in_website_of(version))


    def get_latest_version_folder(self) -> Path:
        """This method returns the folder "latest", the copy of the latest version."""
        return self._folder.joinpath(LATEST_VERSION_FOLDER_NAME)


    def get_search_index_file(self, search_index_file_name: str) -> Path:
        """This method returns the search index file of the latest version, the only one shared between the websites."""
        return self.get_latest_version_folder().joinpath(search_index_file_name)


    def get_path_to_latest_version_of(self, other: "BuiltWebsite") -> str:
        """This method returns the relative path from this website's latest version to another website's."""
        relative_path: str = os.path.relpath(other.get_latest_version_folder(), start=self.get_latest_version_folder())
        return Path(relative_path).as_posix()


    # -- Public: redirection -------------------------------------------------------------------------

    def write_redirection_to_latest_version(self) -> None:
        """This method writes the page at the root of the website that sends the reader to the latest version."""
        redirection_file: Path = self._folder.joinpath(REDIRECTION_FILE_NAME)
        redirection_file.write_text(REDIRECTION_PAGE.format(folder=self.get_latest_version_folder().name), encoding="utf-8")


    # -- Public: list of the versions ----------------------------------------------------------------

    def write_versions_file(self) -> None:
        """This method writes at the root of the website the list of the built versions, for the versions menu."""
        version_list: VersionList = self._website.get_website_version_list()
        latest_version: VersionSettings = version_list.get_latest_version()
        versions: list[VersionSettings] = [latest_version] + version_list.get_earlier_versions()
        entries: list[dict] = [
            {
                "name": version.get_name(),
                "link": LATEST_VERSION_FOLDER_NAME if version is latest_version else version.get_name(),
                "is_latest": version is latest_version,
            }
            for version in versions
            if self.get_version_folder(version).is_dir()
        ]
        self._folder.joinpath(VERSION_MENU_FILE_NAME).write_text(json.dumps(entries, indent=2), encoding="utf-8")
