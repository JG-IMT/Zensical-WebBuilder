"""
Builds one version of the website: clones it at its git reference, prepares the folder of pages the site
generator reads and has it build the site. The clone is deleted once the version is built, or has failed;
the pages and the version site stay, to see what the site generator was given and what it produced.
"""

from pathlib import Path

from webbuilder.builder.preparation.version_input import VersionInput
from webbuilder.builder.settings.website_settings import WebsiteSettings
from webbuilder.builder.settings.website_version import WebsiteVersion
from webbuilder.builder.settings.website_version_catalog import WebsiteVersionCatalog
from webbuilder.common.folder_helper import FolderHelper
from webbuilder.common.git_repository import GitRepository
from webbuilder.common.site_generator_interface import SiteGeneratorInterface

VERSION_CLONE_FOLDER_NAME: str = "version_clone"
ZENSICAL_INPUT_FOLDER_NAME: str = "zensical_input"  # the pages the site generator reads
VERSION_SITE_FOLDER_NAME: str = "version_site"  # the site it writes


def template_values_of(version: WebsiteVersion, version_catalog: WebsiteVersionCatalog) -> dict:
    """
    The values specific to a version that the HTML templates (shared/zensical/html_templates) read in
    config.extra: the version displayed in the badge of each page, and the latest version, which the banner
    of an earlier version links to. A template reading another key of config.extra finds it in the settings
    of the website (tests/test_template_contract.py checks both).
    """
    latest_version: WebsiteVersion = version_catalog.get_latest_version()
    return {
        "displayed_version": version.get_name(),
        "latest_version": latest_version.get_name(),
        "latest_version_url": version_catalog.site_url_of(latest_version),
    }


class VersionBuild:
    """Builds one version of the website from a clone of its git reference."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self,
        website_settings: WebsiteSettings,
        git_repository: GitRepository,
        site_generator: SiteGeneratorInterface,
        version: WebsiteVersion,
        version_build_folder: Path,
    ) -> None:
        self._website_settings: WebsiteSettings = website_settings
        self._git_repository: GitRepository = git_repository
        self._site_generator: SiteGeneratorInterface = site_generator
        self._version: WebsiteVersion = version
        self._version_build_folder: Path = version_build_folder

        self._version_clone_folder: Path = version_build_folder.joinpath(VERSION_CLONE_FOLDER_NAME)
        self._zensical_input_folder: Path = version_build_folder.joinpath(ZENSICAL_INPUT_FOLDER_NAME)
        self._version_site_folder: Path = version_build_folder.joinpath(VERSION_SITE_FOLDER_NAME)


    # -- Public: entry point -------------------------------------------------------------------------

    def build(self) -> Path:
        """
        Clones the version, prepares its input folder, has the site generator build the site, then
        deletes the clone - also when the build fails. Returns the version site folder, which holds the pages of the version.
        """
        print(f"Building version {self._version.get_name()} ({self._version.get_git_ref()})")
        self._clone_version()
        try:
            self._prepare_zensical_input()
            self._build_site()
        finally:
            FolderHelper.delete_folder(self._version_clone_folder)
        return self._version_site_folder


    # -- Private: build steps ------------------------------------------------------------------------

    def _clone_version(self) -> None:
        """Clones the git reference of the version into the clone folder."""
        self._git_repository.clone_at(self._version.get_git_ref(), self._version_clone_folder)


    def _prepare_zensical_input(self) -> None:
        """Prepares the pages the site generator reads, from the clone of the version."""
        # The input folder does not exist yet: WebsiteBuild empties the build folders of the versions first.
        VersionInput(
            self._website_settings, self._version_clone_folder, self._zensical_input_folder, self._version
        ).prepare_input()


    def _build_site(self) -> None:
        """Has the site generator build the site of the version. Stops the build if it fails."""
        version_catalog: WebsiteVersionCatalog = self._website_settings.get_version_catalog()
        is_built: bool = self._site_generator.build_site(
            settings=self._website_settings.get_zensical_settings(),
            site_url=version_catalog.site_url_of(self._version),
            pages_folder=self._zensical_input_folder,
            site_folder=self._version_site_folder,
            work_folder=self._version_build_folder,
            side_menu=self._version.get_side_menu(),
            template_values=template_values_of(self._version, version_catalog),
        )
        if not is_built:
            raise SystemExit(f"The site generator failed on version {self._version.get_name()}")
