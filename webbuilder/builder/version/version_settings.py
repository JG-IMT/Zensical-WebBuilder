"""
The versions of a website, as declared in its version files and checked when they are read.
VersionSettings is one version: its name, the git reference it is built from, whether it is the latest, the
folders of the repository to copy and optionally its own menu. WebsiteVersionList is all the versions of a
website: the latest version is served in the folder "latest" of the website, each earlier version in a folder
named after it - this layout is decided here only (folder_in_website_of, site_url_of); every other class asks.
"""

import copy
import re

from webbuilder.builder.configs.build_config import LATEST_VERSION_FOLDER_NAME

VERSION_NAME_PATTERN: re.Pattern = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
DECLARED_VERSION_KEYS: tuple[str, ...] = ("git_ref", "is_latest", "side_menu", "documentation_sources")


class VersionSettings:
    """A version of the website: name, git reference to build it from, latest or not, folders to copy, optional menu."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, name: str, declared_version: dict) -> None:
        self._check_declared_version_keys(declared_version)
        self._name: str = name
        self._git_ref: str = self._extract_required_text(declared_version, "git_ref")
        self._is_latest: bool = self._extract_optional_boolean(declared_version, "is_latest")
        self._side_menu: list | None = self._extract_optional_list(declared_version, "side_menu")
        self._documentation_sources: list[dict] = self._extract_documentation_sources(declared_version)
        self._check_name()


    # -- Public: get version -------------------------------------------------------------------------

    def get_name(self) -> str:
        """The name of the version, also its folder in the website."""
        return self._name


    def get_git_ref(self) -> str:
        """The branch or tag the version is built from."""
        return self._git_ref


    def is_latest(self) -> bool:
        """True for the version served in the folder "latest" of the website."""
        return self._is_latest


    def get_side_menu(self) -> list | None:
        """The menu of this version, or None to let Zensical build it from the pages."""
        return self._side_menu


    def get_documentation_sources(self) -> list[dict]:
        """A copy of the folders of the repository to copy into the website, each with its 'source' and 'destination'."""
        return copy.deepcopy(self._documentation_sources)


    # -- Private: declared version -------------------------------------------------------------------

    @staticmethod
    def _check_declared_version_keys(declared_version: dict) -> None:
        if not isinstance(declared_version, dict):
            raise ValueError(f"a version must be 'key: value' lines ({', '.join(DECLARED_VERSION_KEYS)}), "
                             f"not {declared_version!r}")
        unknown_keys: list[str] = []
        for key in declared_version:
            if key not in DECLARED_VERSION_KEYS:
                unknown_keys.append(key)
        if unknown_keys:
            raise ValueError(f"version {declared_version}: unknown key(s) {unknown_keys}, "
                             f"known keys: {', '.join(DECLARED_VERSION_KEYS)}")


    def _check_name(self) -> None:
        """The name is also the folder of the version in the website."""
        if not VERSION_NAME_PATTERN.fullmatch(self._name):
            raise ValueError(f"version name '{self._name}' may only contain letters, digits, '.', '_' and '-'")


    @staticmethod
    def _extract_required_text(declared_version: dict, key: str) -> str:
        """The text for the key. Throws an error if the key is missing or is not text."""
        declared_value: object = declared_version.get(key)
        if not isinstance(declared_value, str):
            raise ValueError(f"version {declared_version}: '{key}' is required and must be text (quote it: \"1.6\")")
        return declared_value


    @staticmethod
    def _extract_documentation_sources(declared_version: dict) -> list[dict]:
        """The list of folders to copy. Throws an error if it is missing or an entry has no 'source' or 'destination'."""
        documentation_sources: object = declared_version.get("documentation_sources")
        if not isinstance(documentation_sources, list) or not all(
            isinstance(entry, dict) and isinstance(entry.get("source"), str) and isinstance(entry.get("destination"), str)
            for entry in documentation_sources
        ):
            raise ValueError(f"version {declared_version}: 'documentation_sources' is required and must be a list of "
                             "entries with a 'source' and a 'destination' folder")
        return documentation_sources


    @staticmethod
    def _extract_optional_boolean(declared_version: dict, key: str) -> bool:
        """The true or false written for the key, or False if the key is missing. Throws an error otherwise."""
        if key not in declared_version:
            return False
        declared_value: object = declared_version[key]
        if not isinstance(declared_value, bool):
            raise ValueError(f"version {declared_version}: '{key}' must be true or false")
        return declared_value


    @staticmethod
    def _extract_optional_list(declared_version: dict, key: str) -> list | None:
        """The list written for the key, or None if the key is missing or empty. Throws an error otherwise."""
        declared_value: object = declared_version.get(key)
        if declared_value is None:
            return None
        if not isinstance(declared_value, list):
            raise ValueError(f"version {declared_version}: '{key}' must be a list")
        return declared_value


class WebsiteVersionList:
    """
    All the versions of a website. The latest version (the one declared 'is_latest') is served in the folder
    "latest", each earlier version in a folder named after it.
    """

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, declared_versions: dict[str, dict], site_url: str) -> None:
        """The declared versions are given by name, in the order they are listed in the menu."""
        self._site_url: str = site_url.rstrip("/") + "/"  # ends with "/" to add a folder name
        self._versions: list[VersionSettings] = self._create_versions(declared_versions)
        self._check_latest_version()
        self._check_earlier_version_names()


    # -- Public: get versions ------------------------------------------------------------------------

    def get_all_versions(self) -> list[VersionSettings]:
        """A copy of the list of the versions, in the order they are declared."""
        return list(self._versions)


    def get_latest_version(self) -> VersionSettings:
        """The version served in the folder "latest"."""
        return next(version for version in self._versions if version.is_latest())  # exactly one, checked at creation


    def get_earlier_versions(self) -> list[VersionSettings]:
        """The versions served in a folder named after them, in the order they are declared."""
        earlier_versions: list[VersionSettings] = []
        for version in self._versions:
            if not version.is_latest():
                earlier_versions.append(version)
        return earlier_versions


    # -- Public: where a version is in the website ---------------------------------------------------

    def folder_in_website_of(self, version: VersionSettings) -> str:
        """The folder of the version in the website: "latest" for the latest, its name for the others."""
        return LATEST_VERSION_FOLDER_NAME if version.is_latest() else version.get_name()


    def site_url_of(self, version: VersionSettings) -> str:
        """The address of the version: the website URL followed by the folder of the version."""
        return f"{self._site_url}{self.folder_in_website_of(version)}/"


    # -- Private: creation ---------------------------------------------------------------------------

    @staticmethod
    def _create_versions(declared_versions: dict[str, dict]) -> list[VersionSettings]:
        """Creates one version per declared version. An error names the file of the version."""
        versions: list[VersionSettings] = []
        for name, declared_version in declared_versions.items():
            try:
                versions.append(VersionSettings(name, declared_version))
            except ValueError as error:
                raise ValueError(f"{name}.yml: {error}") from error

        return versions


    # -- Private: checks -----------------------------------------------------------------------------

    def _check_latest_version(self) -> None:
        latest_versions_count: int = 0
        for version in self._versions:
            if version.is_latest():
                latest_versions_count += 1
        if latest_versions_count != 1:
            raise ValueError(f"exactly one version must have 'is_latest: true' (found {latest_versions_count})")


    def _check_earlier_version_names(self) -> None:
        """The folder "latest" is kept for the latest version."""
        for version in self.get_earlier_versions():
            if version.get_name() == LATEST_VERSION_FOLDER_NAME:
                raise ValueError(f"only the latest version may be named '{LATEST_VERSION_FOLDER_NAME}': it is its folder in the website")
