"""
The versions of a website, as declared in its settings and checked when they are read. The latest version
is served in the folder "latest" of the website, each earlier version in a folder named after it - this
layout is decided here only (folder_in_website_of, site_url_of); every other class asks.
"""

from webbuilder.builder.website.website_version import WebsiteVersion

LATEST_VERSION_FOLDER_NAME: str = "latest"


class WebsiteVersions:
    """
    All the versions of a website. The latest version (the one declared 'is_latest') is served in the folder
    "latest", each earlier version in a folder named after it.
    """

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, declared_versions: dict[str, dict], site_url: str) -> None:
        """The declared versions are given by name, in the order they are listed in the menu."""
        self._site_url: str = site_url.rstrip("/") + "/"  # ends with "/" to add a folder name
        self._versions: list[WebsiteVersion] = self._create_versions(declared_versions)
        self._check_latest_version()
        self._check_earlier_version_names()


    # -- Public: get versions ------------------------------------------------------------------------

    def get_all_versions(self) -> list[WebsiteVersion]:
        """A copy of the list of the versions, in the order they are declared."""
        return list(self._versions)


    def get_latest_version(self) -> WebsiteVersion:
        """The version served in the folder "latest"."""
        return next(version for version in self._versions if version.is_latest())  # exactly one, checked at creation


    def get_earlier_versions(self) -> list[WebsiteVersion]:
        """The versions served in a folder named after them, in the order they are declared."""
        earlier_versions: list[WebsiteVersion] = []
        for version in self._versions:
            if not version.is_latest():
                earlier_versions.append(version)
        return earlier_versions


    # -- Public: where a version is in the website ---------------------------------------------------

    def folder_in_website_of(self, version: WebsiteVersion) -> str:
        """The folder of the version in the website: "latest" for the latest, its name for the others."""
        return LATEST_VERSION_FOLDER_NAME if version.is_latest() else version.get_name()


    def site_url_of(self, version: WebsiteVersion) -> str:
        """The address of the version: the website URL followed by the folder of the version."""
        return f"{self._site_url}{self.folder_in_website_of(version)}/"


    # -- Private: creation ---------------------------------------------------------------------------

    @staticmethod
    def _create_versions(declared_versions: dict[str, dict]) -> list[WebsiteVersion]:
        """Creates one version per declared version. An error names the file of the version."""
        versions: list[WebsiteVersion] = []
        for name, declared_version in declared_versions.items():
            try:
                versions.append(WebsiteVersion(name, declared_version))
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
