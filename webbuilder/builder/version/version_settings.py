"""
These classes represent the versions of a website (e.g. 1.6 and 1.6.1) read from their version files.

VersionSettings represents one version and VersionList represents all the versions of one website.
A version is made of the git reference it is built from, the folders of the repository to copy, and an optional
menu. The latest version is the one named in the website settings (extra.latest_version).
A wrong file stops the build with one line naming it.

Created at step 1 (read the settings), asked by every later step. The built versions are the folders of BuiltWebsite.
"""

import copy
import re

from webbuilder.builder.paths.build_paths import LATEST_VERSION_FOLDER_NAME

VERSION_NAME_PATTERN: re.Pattern = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
DECLARED_VERSION_KEYS: tuple[str, ...] = ("git_ref", "side_menu", "documentation_sources")


class VersionSettings:
    """This class reads and checks the settings of one version."""

    # == Public ====================================================================================

    # -- Initialization ----------------------------------------------------------------------------

    def __init__(self, name: str, declared_version: dict) -> None:
        """This constructor reads and checks the settings of the version declared in its version file."""
        self._check_declared_version_keys(declared_version)
        self._name: str = name
        self._git_ref: str = self._extract_required_text(declared_version, "git_ref")
        self._side_menu: list | None = self._extract_optional_list(declared_version, "side_menu")
        self._documentation_sources: list[dict] = self._extract_documentation_sources(declared_version)
        self._check_versions_names()


    # -- Getters -----------------------------------------------------------------------------------

    def get_name(self) -> str:
        """This method returns the name of the version."""
        return self._name


    def get_git_ref(self) -> str:
        """This method returns the branch or tag the version is built from."""
        return self._git_ref


    def get_side_menu(self) -> list | None:
        """This method returns the menu of the version, or None to let Zensical build it from the pages."""
        return self._side_menu


    def get_documentation_sources(self) -> list[dict]:
        """This method returns a copy of the folders of the repository to copy into the website, each with its 'source' and 'destination'."""
        return copy.deepcopy(self._documentation_sources)


    # == Private ===================================================================================

    # -- Data extraction ---------------------------------------------------------------------------

    @staticmethod
    def _extract_required_text(declared_version: dict, key: str) -> str:
        """This method returns the text written for a key, or raises an error if the key is missing or is not text."""
        declared_value: object = declared_version.get(key)
        if not isinstance(declared_value, str):
            raise ValueError(f"version {declared_version}: '{key}' is required and must be text (quote it: \"1.6\")")
        return declared_value


    @staticmethod
    def _extract_documentation_sources(declared_version: dict) -> list[dict]:
        """This method returns the list of folders to copy, or raises an error if it is missing or an entry has no 'source' or 'destination'."""
        documentation_sources: object = declared_version.get("documentation_sources")
        if not isinstance(documentation_sources, list) or not all(
            isinstance(entry, dict) and isinstance(entry.get("source"), str) and isinstance(entry.get("destination"), str)
            for entry in documentation_sources
        ):
            raise ValueError(f"version {declared_version}: 'documentation_sources' is required and must be a list of "
                             "entries with a 'source' and a 'destination' folder")
        return documentation_sources


    @staticmethod
    def _extract_optional_list(declared_version: dict, key: str) -> list | None:
        """This method returns the list written for a key, None if the key is missing or empty, or raises an error for any other value."""
        declared_value: object = declared_version.get(key)
        if declared_value is None:
            return None
        if not isinstance(declared_value, list):
            raise ValueError(f"version {declared_version}: '{key}' must be a list")
        return declared_value
    
    
    # -- Verification ------------------------------------------------------------------------------
    
    @staticmethod
    def _check_declared_version_keys(declared_version: dict) -> None:
        """This method raises an error if the version file is not made of 'key: value' lines or holds an unknown key."""
        if not isinstance(declared_version, dict):
            raise ValueError(f"a version must be 'key: value' lines ({', '.join(DECLARED_VERSION_KEYS)}), "
                             f"not {declared_version!r}")
        unknown_keys: list[str] = []
        for key in declared_version:
            if key not in DECLARED_VERSION_KEYS:
                unknown_keys.append(key)
        if unknown_keys:
            hint: str = " (is_latest is replaced by extra.latest_version in website_settings.yml)" if "is_latest" in unknown_keys else ""
            raise ValueError(f"version {declared_version}: unknown key(s) {unknown_keys}{hint}, "
                             f"known keys: {', '.join(DECLARED_VERSION_KEYS)}")


    def _check_versions_names(self) -> None:
        """This method raises an error if the name of the version holds a character other than letters, digits, '.', '_' and '-'."""
        if not VERSION_NAME_PATTERN.fullmatch(self._name):
            raise ValueError(f"version name '{self._name}' may only contain letters, digits, '.', '_' and '-'")


class VersionList:
    """This class holds the versions of one website and tells where each one is."""

    # == Public ====================================================================================

    # -- Initialization ----------------------------------------------------------------------------

    def __init__(self, declared_versions: dict[str, dict], site_url: str, latest_version_name: str) -> None:
        """This constructor creates the versions from their declared settings, given by name, and checks them."""
        self._site_url: str = site_url.rstrip("/") + "/"  # ends with "/" to add a folder name
        self._latest_version_name: str = latest_version_name
        self._versions: list[VersionSettings] = self._create_versions(declared_versions)
        self._check_latest_version()
        self._check_versions_names()


    # -- Getters -----------------------------------------------------------------------------------

    def get_all_versions(self) -> list[VersionSettings]:
        """This method returns a copy of the list of the versions, in the order they are declared."""
        return list(self._versions)


    def get_latest_version(self) -> VersionSettings:
        """This method returns the version that is copied in the folder "latest"."""
        return next(version for version in self._versions if version.get_name() == self._latest_version_name)  # checked at creation


    def get_earlier_versions(self) -> list[VersionSettings]:
        """This method returns the versions served in a folder named after them, in the order they are declared."""
        earlier_versions: list[VersionSettings] = []
        for version in self._versions:
            if version.get_name() != self._latest_version_name:
                earlier_versions.append(version)
        return earlier_versions


    # -- Locations ---------------------------------------------------------------------------------

    def folder_in_website_of(self, version: VersionSettings) -> str:
        """This method returns the folder of a version in the website, which is its name."""
        return version.get_name()


    def site_url_of(self, version: VersionSettings) -> str:
        """This method returns the address of a version: the website URL followed by the folder of the version."""
        return f"{self._site_url}{self.folder_in_website_of(version)}/"


    # == Private ===================================================================================

    # -- Creation ----------------------------------------------------------------------------------

    @staticmethod
    def _create_versions(declared_versions: dict[str, dict]) -> list[VersionSettings]:
        """This method creates one version per declared version, and names the file of the version in any error."""
        versions: list[VersionSettings] = []
        for name, declared_version in declared_versions.items():
            try:
                versions.append(VersionSettings(name, declared_version))
            except ValueError as error:
                raise ValueError(f"{name}.yml: {error}") from error

        return versions


    # -- Verification ------------------------------------------------------------------------------

    def _check_latest_version(self) -> None:
        """This method raises an error unless the latest version named in the website settings is one of the versions."""
        version_names: list[str] = [version.get_name() for version in self._versions]
        if self._latest_version_name not in version_names:
            raise ValueError(f"extra.latest_version '{self._latest_version_name}' is not a version of this website "
                             f"(found: {', '.join(version_names)})")


    def _check_versions_names(self) -> None:
        """This method raises an error if a version is named "latest", the folder kept for the copy of the latest version."""
        for version in self._versions:
            if version.get_name() == LATEST_VERSION_FOLDER_NAME:
                raise ValueError(f"no version may be named '{LATEST_VERSION_FOLDER_NAME}': it is the folder of the latest version in the website")
