"""
This class represents a website (e.g. pamela) read from its settings file and its versions folder.

A website is composed of one or multiple versions, each with its own settings. It combines three sources of
configuration files: the default settings shared by every website, the project settings (website_settings.yml)
and one file per version. A wrong file stops the build with one line naming it.

Created at step 1 (read the settings), asked by every later step. BuiltWebsite is the same website once built.
"""

import copy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from webbuilder.builder.paths.build_paths import VERSIONS_FOLDER_NAME
from webbuilder.builder.paths.shared_paths import SHARED_DEFAULT_SETTINGS_FILE

from webbuilder.builder.version.version_settings import VersionList

REPOSITORY_URL_KEY: str = "repository_url"
ZENSICAL_NAVIGATION_KEY: str = "nav"


class WebsiteSettings:
    """This class reads the settings and the versions of one website and checks them."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, project_settings_file: Path) -> None:
        """This constructor reads, merges and checks the settings and the versions of the website."""
        self._project_settings_file: Path = project_settings_file

        # What Zensical receives: the default settings overridden by the project settings.
        default_settings: dict = self._read_settings_file(SHARED_DEFAULT_SETTINGS_FILE)
        project_settings: dict = self._read_settings_file(self._project_settings_file)
        self._zensical_settings: dict = self._merge_settings(default_settings, project_settings)
        self._check_zensical_settings()

        # What only the website builder needs (not Zensical): taken out of the settings above.
        self._repository_url: str = self._extract_repository_url()
        self._website_version_list: VersionList = self._extract_website_version_list()


    # -- Public: get settings ------------------------------------------------------------------------

    def get_zensical_settings(self) -> dict:
        """This method returns a copy of the settings given to Zensical, without the repository URL."""
        return copy.deepcopy(self._zensical_settings)


    def get_repository_url(self) -> str:
        """This method returns the address of the git repository the versions are cloned from."""
        return self._repository_url


    def get_settings_folder(self) -> Path:
        """This method returns the folder that holds the website_settings.yml of the website."""
        return self._project_settings_file.parent


    def get_site_url_path(self) -> str:
        """This method returns the path of the website in its address, for example "pamela/docs" for https://openflexo.org/pamela/docs/."""
        return urlparse(self._zensical_settings["site_url"]).path.strip("/")


    def get_site_name(self) -> str:
        """This method returns the name of the website."""
        return self._zensical_settings["site_name"]


    def get_website_version_list(self) -> VersionList:
        """This method returns the list of the versions of the website."""
        return self._website_version_list


    def get_homepage_url_path(self) -> str:
        """This method returns the path of the project home page, for example "my_project" for https://openflexo.org/my_project/."""
        homepage_url: str = self._zensical_settings["extra"].get("homepage", "")
        return urlparse(homepage_url).path.strip("/")


    # -- Private: reading ----------------------------------------------------------------------------

    @staticmethod
    def _read_settings_file(file: Path) -> dict:
        """This method reads a settings file and stops the build if it is not valid YAML or has no 'key: value' line."""
        try:
            file_settings: object = yaml.safe_load(file.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise SystemExit(f"{file}: not valid YAML ({error})")
        if not isinstance(file_settings, dict):
            raise SystemExit(f"{file}: no settings (the file is empty or has no 'key: value')")
        return file_settings


    @staticmethod
    def _merge_settings(default_settings: dict, project_settings: dict) -> dict:
        """This method overrides the default settings with the project settings, key by key."""
        merged_settings: dict = dict(default_settings)
        for key, project_value in project_settings.items():
            default_value: object = default_settings.get(key)
            if isinstance(default_value, dict) and isinstance(project_value, dict):
                merged_settings[key] = WebsiteSettings._merge_settings(default_value, project_value)
            else:
                merged_settings[key] = project_value
        return merged_settings


    # -- Private: website builder settings -----------------------------------------------------------

    def _extract_repository_url(self) -> str:
        """This method takes the address of the git repository out of the settings."""
        return self._extract_key_from_extra(REPOSITORY_URL_KEY, "repository to clone")


    def _extract_website_version_list(self) -> VersionList:
        """This method reads the version files and builds the list of the versions."""
        versions_folder: Path = self.get_settings_folder().joinpath(VERSIONS_FOLDER_NAME)
        version_files: list[Path] = sorted(versions_folder.glob("*.yml"))  # the menu lists them in this order
        if not version_files:
            raise SystemExit(f"{versions_folder}: no version file (one <version name>.yml per version)")
        declared_versions: dict[str, dict] = {file.stem: self._read_settings_file(file) for file in version_files}
        try:
            return VersionList(declared_versions, self._zensical_settings["site_url"])
        except ValueError as error:
            raise SystemExit(f"{versions_folder}: {error}")


    def _extract_key_from_extra(self, key: str, purpose: str) -> Any:
        """This method removes a key from 'extra' and returns its value, or stops the build if the key is missing."""
        extra: dict = self._zensical_settings["extra"]
        if key not in extra:
            raise SystemExit(f"{self._project_settings_file}: no '{key}' under 'extra:' ({purpose})")
        return extra.pop(key)


    # -- Private: input verification -----------------------------------------------------------------

    def _check_zensical_settings(self) -> None:
        """This method runs the checks on the settings given to Zensical."""
        self._check_site_url()
        self._check_extra()
        self._check_no_global_navigation()


    def _check_site_url(self) -> None:
        """This method stops the build if site_url is missing or is not text."""
        if not isinstance(self._zensical_settings.get("site_url"), str):
            raise SystemExit(f"{self._project_settings_file}: 'site_url' is required and must be text")


    def _check_extra(self) -> None:
        """This method stops the build if 'extra' is not made of 'key: value' lines."""
        if not isinstance(self._zensical_settings.get("extra"), dict):
            raise SystemExit(f"{self._project_settings_file}: 'extra' must contain 'key: value' lines")


    def _check_no_global_navigation(self) -> None:
        """This method stops the build if the settings hold a 'nav' key, which would apply to every version."""
        if ZENSICAL_NAVIGATION_KEY in self._zensical_settings:
            raise SystemExit(f"{self._project_settings_file}: '{ZENSICAL_NAVIGATION_KEY}' would apply to every version; "
                             "put it in 'side_menu' of the version it belongs to")

