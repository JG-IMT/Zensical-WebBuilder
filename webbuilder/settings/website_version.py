"""
Represents one version of a website with declared elements in its version file: its name, the git reference
it is built from, whether it is the latest, the folders of the repository to copy and optionally its own menu.
The declared version is checked when it is read.
"""

import copy
import re

VERSION_NAME_PATTERN: re.Pattern = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
DECLARED_VERSION_KEYS: tuple[str, ...] = ("git_ref", "is_latest", "navigation", "documentation_sources")


class WebsiteVersion:
    """A version of the website: name, git reference to build it from, latest or not, folders to copy, optional menu."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, name: str, declared_version: dict) -> None:
        self._check_declared_version_keys(declared_version)
        self._name: str = name
        self._git_ref: str = self._extract_required_text(declared_version, "git_ref")
        self._is_latest: bool = self._extract_optional_boolean(declared_version, "is_latest")
        self._navigation: list | None = self._extract_optional_list(declared_version, "navigation")
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
        """True for the version served at the website URL."""
        return self._is_latest


    def get_navigation(self) -> list | None:
        """The menu of this version, or None to let Zensical build it from the pages."""
        return self._navigation


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
