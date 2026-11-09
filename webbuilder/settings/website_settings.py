"""
Reads the settings of one website: the settings shared by every website (shared/default_settings.yml)
completed by the settings of the project (website_settings.yml), then its versions (one file per version in
the versions folder next to it). The files are checked when they are read, so that a wrong file stops the
build with one line naming it.
"""

import copy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from webbuilder.settings.website_version_catalog import WebsiteVersionCatalog
from webbuilder.shared_paths import SHARED_DEFAULT_SETTINGS_FILE

REPOSITORY_URL_KEY: str = "repository_url"
VERSIONS_FOLDER_NAME: str = "versions"  # one <version name>.yml per version
ZENSICAL_NAVIGATION_KEY: str = "nav"


class WebsiteSettings:
    """Reads the settings shared by every website and completes them by the settings of one project."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, project_settings_file: Path) -> None:
        self._project_settings_file: Path = project_settings_file

        # What Zensical receives: the default settings overridden by the project settings.
        default_settings: dict = self._read_settings_file(SHARED_DEFAULT_SETTINGS_FILE)
        project_settings: dict = self._read_settings_file(self._project_settings_file)
        self._zensical_settings: dict = self._merge_settings(default_settings, project_settings)
        self._check_zensical_settings()

        # What only the website builder needs (not Zensical): taken out of the settings above.
        self._repository_url: str = self._extract_repository_url()
        self._version_catalog: WebsiteVersionCatalog = self._extract_version_catalog()


    # -- Public: get settings ------------------------------------------------------------------------

    def get_zensical_settings(self) -> dict:
        """
        A copy of the settings Zensical receives: the default settings overridden by the project settings,
        without the one only the website builder needs (repository URL).
        """
        return copy.deepcopy(self._zensical_settings)


    def get_repository_url(self) -> str:
        """The git repository the versions are cloned from."""
        return self._repository_url


    def get_settings_folder(self) -> Path:
        """The folder holding the website_settings.yml of the website."""
        return self._project_settings_file.parent


    def get_site_url_path(self) -> str:
        """The path of the website in its address: https://openflexo.org/pamela/docs/ gives "pamela/docs"."""
        return urlparse(self._zensical_settings["site_url"]).path.strip("/")


    def get_site_name(self) -> str:
        """The name of the website."""
        return self._zensical_settings["site_name"]


    def get_version_catalog(self) -> WebsiteVersionCatalog:
        """The versions of the website, and where each one is in the website."""
        return self._version_catalog


    def get_homepage_url_path(self) -> str:
        """The project path in URLs, from "homepage": https://openflexo.org/my_project/ gives "my_project"."""
        homepage_url: str = self._zensical_settings["extra"].get("homepage", "")
        return urlparse(homepage_url).path.strip("/")


    # -- Private: reading ----------------------------------------------------------------------------

    @staticmethod
    def _read_settings_file(file: Path) -> dict:
        """Reads a settings file. Throw an error if it is not valid YAML or has no 'key: value' settings."""
        try:
            file_settings: object = yaml.safe_load(file.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise SystemExit(f"{file}: not valid YAML ({error})")
        if not isinstance(file_settings, dict):
            raise SystemExit(f"{file}: no settings (the file is empty or has no 'key: value')")
        return file_settings


    @staticmethod
    def _merge_settings(default_settings: dict, project_settings: dict) -> dict:
        """Overrides default settings with project settings, key by key."""
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
        """The git repository the versions are cloned from."""
        return self._extract_key_from_extra(REPOSITORY_URL_KEY, "repository to clone")


    def _extract_version_catalog(self) -> WebsiteVersionCatalog:
        """The catalog of versions to build, from the version files: names, git references, which one is the latest."""
        versions_folder: Path = self.get_settings_folder().joinpath(VERSIONS_FOLDER_NAME)
        version_files: list[Path] = sorted(versions_folder.glob("*.yml"))  # the menu lists them in this order
        if not version_files:
            raise SystemExit(f"{versions_folder}: no version file (one <version name>.yml per version)")
        declared_versions: dict[str, dict] = {file.stem: self._read_settings_file(file) for file in version_files}
        try:
            return WebsiteVersionCatalog(declared_versions, self._zensical_settings["site_url"])
        except ValueError as error:
            raise SystemExit(f"{versions_folder}: {error}")


    def _extract_key_from_extra(self, key: str, purpose: str) -> Any:
        """Removes the key from 'extra' and returns its value. Throws an error if the key is missing."""
        extra: dict = self._zensical_settings["extra"]
        if key not in extra:
            raise SystemExit(f"{self._project_settings_file}: no '{key}' under 'extra:' ({purpose})")
        return extra.pop(key)


    # -- Private: input verification -----------------------------------------------------------------

    def _check_zensical_settings(self) -> None:
        self._check_site_url()
        self._check_extra()
        self._check_no_global_navigation()


    def _check_site_url(self) -> None:
        if not isinstance(self._zensical_settings.get("site_url"), str):
            raise SystemExit(f"{self._project_settings_file}: 'site_url' is required and must be text")


    def _check_extra(self) -> None:
        if not isinstance(self._zensical_settings.get("extra"), dict):
            raise SystemExit(f"{self._project_settings_file}: 'extra' must contain 'key: value' lines")


    def _check_no_global_navigation(self) -> None:
        if ZENSICAL_NAVIGATION_KEY in self._zensical_settings:
            raise SystemExit(f"{self._project_settings_file}: '{ZENSICAL_NAVIGATION_KEY}' would apply to every version; "
                             "put it in 'side_menu' of the version it belongs to")

