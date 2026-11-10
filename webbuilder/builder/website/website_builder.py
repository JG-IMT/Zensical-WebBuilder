"""
Builds the versions of the website and puts each one in its folder of the website folder: "latest" for the
latest version, a folder named after it for each earlier version. A version replaces only its own folder.
Every version to build is built before the first one is put in the website, so a failed build never changes
the previous website. The root of the website only redirects to the latest version.
"""

from pathlib import Path

from webbuilder.builder.config.build_config import VERSION_BUILDS_FOLDER_NAME
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.builder.version.version_builder import VersionBuilder
from webbuilder.builder.website.built_website import BuiltWebsite
from webbuilder.builder.version.version_settings import VersionSettings
from webbuilder.common.helper.clone_git_repository import CloneGitRepository

from webbuilder.common.helper.folder_helper import FolderHelper
from webbuilder.common.openflexo_interfaces import SiteGeneratorInterface


class WebsiteBuilder:
    """Builds the versions of the website and puts them in a single website folder."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self,
        website: WebsiteSettings,
        git_repository: CloneGitRepository,
        site_generator: SiteGeneratorInterface,
        preparation_folder: Path,
        built_website: BuiltWebsite,
    ) -> None:
        self._website: WebsiteSettings = website
        self._git_repository: CloneGitRepository = git_repository
        self._site_generator: SiteGeneratorInterface = site_generator

        self._version_builds_folder: Path = preparation_folder.joinpath(VERSION_BUILDS_FOLDER_NAME)  # one work folder per version
        self._built_website: BuiltWebsite = built_website


    # -- Public: entry point -------------------------------------------------------------------------

    def build(self, version_names: list[str]) -> Path:
        """
        Builds the named versions - every version if none is named - then puts each one in the website folder.
        Stops at the first version that fails, before the website is changed. Returns the website folder.
        """
        version_site_folders: dict[VersionSettings, Path] = {}
        for version in self._select_versions(version_names):
            version_site_folders[version] = self._build_version(version)

        for version, version_site_folder in version_site_folders.items():
            self._put_version_in_website(version, version_site_folder)
        self._built_website.write_redirection_to_latest_version()

        print(f"Website built in {self._built_website.get_folder()}")
        return self._built_website.get_folder()


    # -- Private: build steps ------------------------------------------------------------------------

    def _select_versions(self, version_names: list[str]) -> list[VersionSettings]:
        """The versions with the names given, or every version if no name is given. Throws an error for an unknown name."""
        all_versions: list[VersionSettings] = self._website.get_website_version_list().get_all_versions()
        if not version_names:
            return all_versions

        version_by_name: dict[str, VersionSettings] = {version.get_name(): version for version in all_versions}
        for version_name in version_names:
            if version_name not in version_by_name:
                raise SystemExit(f"No version named {version_name} in {self._website.get_site_name()} "
                                 f"(found: {', '.join(version_by_name)})")
        return [version_by_name[version_name] for version_name in version_names]


    def _build_version(self, version: VersionSettings) -> Path:
        """Builds the version in its own work folder, emptied first. Returns the folder of the site of the version."""
        version_build_folder: Path = self._version_builds_folder.joinpath(version.get_name())
        FolderHelper.delete_folder(version_build_folder)

        version_build: VersionBuilder = VersionBuilder(
            self._website, self._git_repository, self._site_generator, version, version_build_folder
        )
        return version_build.build()


    def _put_version_in_website(self, version: VersionSettings, version_site_folder: Path) -> None:
        """Replaces the folder of the version in the website by its site."""
        version_folder: Path = self._built_website.get_version_folder(version)
        FolderHelper.delete_folder(version_folder)
        FolderHelper.copy_folder(version_site_folder, version_folder)
