"""
Builds the versions of the website and puts each one in the website folder: the latest version at its root,
each earlier version in a folder named after it. A version replaces only its own place in the website. Every
version to build is built before the first one is put in the website, so a failed build never changes the
previous website.
"""

from pathlib import Path

from webbuilder.building.version_build import VersionBuild
from webbuilder.helper.folder_helper import FolderHelper
from webbuilder.repository.git_repository import GitRepository
from webbuilder.settings.website_settings import WebsiteSettings
from webbuilder.settings.website_version import WebsiteVersion
from webbuilder.settings.website_version_catalog import WebsiteVersionCatalog

VERSION_BUILDS_FOLDER_NAME: str = "version_builds"


class WebsiteBuild:
    """Builds the versions of the website and puts them in a single website folder."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self, website_settings: WebsiteSettings, git_repository: GitRepository, build_folder: Path, website_folder: Path
    ) -> None:
        self._website_settings: WebsiteSettings = website_settings
        self._git_repository: GitRepository = git_repository

        self._version_builds_folder: Path = build_folder.joinpath(VERSION_BUILDS_FOLDER_NAME)  # one work folder per version
        self._website_folder: Path = website_folder


    # -- Public: entry point -------------------------------------------------------------------------

    def build(self, version_names: list[str]) -> Path:
        """
        Builds the named versions - every version if none is named - then puts each one in the website folder.
        Stops at the first version that fails, before the website is changed. Returns the website folder.
        """
        version_site_folders: dict[WebsiteVersion, Path] = {}
        for version in self._select_versions(version_names):
            version_site_folders[version] = self._build_version(version)

        for version, version_site_folder in version_site_folders.items():
            self._put_version_in_website(version, version_site_folder)

        print(f"Website built in {self._website_folder}")
        return self._website_folder


    # -- Private: build steps ------------------------------------------------------------------------

    def _select_versions(self, version_names: list[str]) -> list[WebsiteVersion]:
        """The versions with the names given, or every version if no name is given. Throws an error for an unknown name."""
        all_versions: list[WebsiteVersion] = self._website_settings.get_version_catalog().get_all_versions()
        if not version_names:
            return all_versions

        version_by_name: dict[str, WebsiteVersion] = {version.get_name(): version for version in all_versions}
        for version_name in version_names:
            if version_name not in version_by_name:
                raise SystemExit(f"No version named {version_name} in {self._website_settings.get_site_name()} "
                                 f"(found: {', '.join(version_by_name)})")
        return [version_by_name[version_name] for version_name in version_names]


    def _build_version(self, version: WebsiteVersion) -> Path:
        """Builds the version in its own work folder, emptied first. Returns the folder of the site of the version."""
        version_build_folder: Path = self._version_builds_folder.joinpath(version.get_name())
        FolderHelper.delete_folder(version_build_folder)

        version_build: VersionBuild = VersionBuild(self._website_settings, self._git_repository, version, version_build_folder)
        return version_build.build()


    def _put_version_in_website(self, version: WebsiteVersion, version_site_folder: Path) -> None:
        """Replaces the place of the version in the website by its site: the root for the latest, else its folder."""
        version_folder: Path = self._website_folder.joinpath(self._website_settings.get_version_catalog().folder_of(version))
        if version.is_latest():
            self._empty_website_root()
        else:
            FolderHelper.delete_folder(version_folder)
        FolderHelper.copy_folder(version_site_folder, version_folder)


    def _empty_website_root(self) -> None:
        """Deletes all that is at the root of the website except the folders of the earlier versions."""
        catalog: WebsiteVersionCatalog = self._website_settings.get_version_catalog()
        earlier_folders: set[str] = {catalog.folder_of(version) for version in catalog.get_earlier_versions()}
        if not self._website_folder.is_dir():
            return
        for entry in self._website_folder.iterdir():
            if entry.name in earlier_folders:
                continue
            if entry.is_dir():
                FolderHelper.delete_folder(entry)
            else:
                entry.unlink()
