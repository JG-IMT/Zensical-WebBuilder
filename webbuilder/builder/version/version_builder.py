"""
These classes build one version of a website (e.g. 1.6.1) from a clone of its git reference.

VersionBuilder clones the version, has VersionPreparer fill the folder of pages, and has the site generator build the site.
VersionPreparer fills the folder of pages with the shared style and icon, the pages of the version and the menu of versions.
The clone is deleted once the version is built, or has failed; the pages and the site stay, to see what the site generator
was given and what it produced.

Used at steps 2 to 4 (clone a version, prepare its pages, build its HTML), once per version.
"""

import json
import os
import posixpath
from pathlib import Path

from webbuilder.builder.paths.build_paths import (
    PAGES_FOLDER_NAME,
    VERSION_CLONE_FOLDER_NAME,
    VERSION_MENU_FILE_NAME,
    VERSION_SITE_FOLDER_NAME,
)
from webbuilder.builder.paths.shared_paths import SHARED_STYLE_AND_ICON_FOLDER
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.builder.version.helper.url_resolver import UrlResolver
from webbuilder.builder.version.helper.url_rewriter import UrlRewriter
from webbuilder.builder.version.version_settings import VersionSettings, VersionList
from webbuilder.common.helper.clone_git_repository import CloneGitRepository

from webbuilder.common.helper.folder_helper import FolderHelper
from webbuilder.common.openflexo_interfaces import SiteGeneratorInterface

MARKDOWN_EXTENSION: str = ".md"


def template_values_of(version: VersionSettings, website_version_list: VersionList) -> dict:
    """This function returns the values that the HTML templates read in config.extra for a version: the displayed version, the latest version and its address."""
    latest_version: VersionSettings = website_version_list.get_latest_version()
    return {
        "displayed_version": version.get_name(),
        "latest_version": latest_version.get_name(),
        "latest_version_url": website_version_list.site_url_of(latest_version),
    }


class VersionBuilder:
    """This class builds one version of a website from a clone of its git reference."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self,
        website: WebsiteSettings,
        git_repository: CloneGitRepository,
        site_generator: SiteGeneratorInterface,
        version: VersionSettings,
        version_build_folder: Path,
    ) -> None:
        """This constructor sets the folders of the clone, of the pages and of the site in the work folder of the version."""
        self._website: WebsiteSettings = website
        self._git_repository: CloneGitRepository = git_repository
        self._site_generator: SiteGeneratorInterface = site_generator
        self._version: VersionSettings = version
        self._version_build_folder: Path = version_build_folder

        self._version_clone_folder: Path = version_build_folder.joinpath(VERSION_CLONE_FOLDER_NAME)
        self._pages_folder: Path = version_build_folder.joinpath(PAGES_FOLDER_NAME)
        self._version_site_folder: Path = version_build_folder.joinpath(VERSION_SITE_FOLDER_NAME)


    # -- Public: entry point -------------------------------------------------------------------------

    def build(self) -> Path:
        """This method clones the version, prepares its pages and builds its site, then returns the folder of the site."""
        print(f"Building version {self._version.get_name()} ({self._version.get_git_ref()})")
        self._clone_version()
        try:
            self._prepare_pages()
            self._build_site()
        finally:
            # The clone is deleted even if the build fails.
            FolderHelper.delete_folder(self._version_clone_folder)
        return self._version_site_folder


    # -- Private: build steps ------------------------------------------------------------------------

    def _clone_version(self) -> None:
        """This method clones the git reference of the version into the clone folder."""
        self._git_repository.clone_at(self._version.get_git_ref(), self._version_clone_folder)


    def _prepare_pages(self) -> None:
        """This method has VersionPreparer fill the folder of pages from the clone of the version."""
        # The pages folder does not exist yet: WebsiteBuild empties the build folders of the versions first.
        VersionPreparer(
            self._website, self._version_clone_folder, self._pages_folder, self._version
        ).prepare_pages()


    def _build_site(self) -> None:
        """This method has the site generator build the site of the version, and stops the build if it fails."""
        website_version_list: VersionList = self._website.get_website_version_list()
        is_built: bool = self._site_generator.build_site(
            settings=self._website.get_zensical_settings(),
            site_url=website_version_list.site_url_of(self._version),
            pages_folder=self._pages_folder,
            site_folder=self._version_site_folder,
            work_folder=self._version_build_folder,
            side_menu=self._version.get_side_menu(),
            template_values=template_values_of(self._version, website_version_list),
        )
        if not is_built:
            raise SystemExit(f"The site generator failed on version {self._version.get_name()}")


class VersionPreparer:
    """This class fills the folder of pages from which the site generator builds the site of one version."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self,
        website: WebsiteSettings,
        version_clone_folder: Path,
        pages_folder: Path,
        version: VersionSettings,
    ) -> None:
        """This constructor takes the clone of the version and the folder where its pages are prepared."""
        self._website: WebsiteSettings = website
        self._version_clone_folder: Path = version_clone_folder  # the clone of the version: its sources
        self._pages_folder: Path = pages_folder  # the folder Zensical reads the pages from
        self._version: VersionSettings = version
        self._website_version_list: VersionList = website.get_website_version_list()


    # -- Public: preparation -------------------------------------------------------------------------

    def prepare_pages(self) -> None:
        """This method copies the style and the sources, rewrites the links of the pages, and writes the menu of versions."""
        # The pages folder does not exist yet: WebsiteBuild empties the build folders of the versions first.
        self._copy_style_and_icon()
        self._copy_documentation_sources()

        markdown_page_files: list[Path] = self._find_markdown_pages()
        self._rewrite_urls(markdown_page_files)
        print(f"Prepared {len(markdown_page_files)} Markdown pages in {self._pages_folder}")

        self._write_version_menu_file()


    # -- Private: pages folder -----------------------------------------------------------------------

    def _copy_style_and_icon(self) -> None:
        """This method copies the style and the icon shared by every website into the pages folder."""
        FolderHelper.copy_folder(SHARED_STYLE_AND_ICON_FOLDER, self._pages_folder)


    def _copy_documentation_sources(self) -> None:
         """This method copies each documentation source of the clone to its destination, and stops the build if a source is missing."""
        for documentation_source in self._version.get_documentation_sources():
            source_folder: Path = self._version_clone_folder.joinpath(documentation_source["source"])
            if not source_folder.is_dir():
                raise SystemExit(f"Version {self._version.get_name()}: folder '{documentation_source['source']}' not found")
            FolderHelper.copy_folder(source_folder, self._pages_folder.joinpath(documentation_source["destination"]))


    def _find_markdown_pages(self) -> list[Path]:
        """This method returns the Markdown pages of the pages folder, and stops the build if there is none."""
        markdown_page_files: list[Path] = []
        for walked_folder, subfolder_names, file_names in os.walk(self._pages_folder):
            for file_name in file_names:
                if file_name.endswith(MARKDOWN_EXTENSION):
                    markdown_page_files.append(Path(walked_folder).joinpath(file_name))
        if not markdown_page_files:
            raise SystemExit(f"Version {self._version.get_name()}: no Markdown page in the documentation sources")
        return markdown_page_files


    def _rewrite_urls(self, markdown_page_files: list[Path]) -> None:
        """This method rewrites the URLs starting with "/" in the copies of the pages."""
        url_resolver: UrlResolver = UrlResolver(
            self._pages_folder, self._website.get_homepage_url_path()
        )
        UrlRewriter(url_resolver).rewrite_urls_in(markdown_page_files)


    # -- Private: menu of versions -------------------------------------------------------------------

    def _write_version_menu_file(self) -> None:
        """This method writes the list of versions that the version menu reads: the latest first, then the earlier ones."""
        versions: list[VersionSettings] = (
            [self._website_version_list.get_latest_version()] + self._website_version_list.get_earlier_versions()
        )
        menu_entries: list[dict] = []
        for version in versions:
            menu_entries.append({
                "name": version.get_name(),
                "link": self._url_to_root_of(version),
                "current": version.get_name() == self._version.get_name(),
            })
        versions_file: Path = self._pages_folder.joinpath(VERSION_MENU_FILE_NAME)
        versions_file.write_text(json.dumps(menu_entries, indent=2), encoding="utf-8")


    def _url_to_root_of(self, target_version: VersionSettings) -> str:
        """This method returns the path from the root of this version to the root of another: "." for itself, "../1.6" for another."""
        return posixpath.relpath(
            self._website_version_list.folder_in_website_of(target_version), start=self._website_version_list.folder_in_website_of(self._version)
        )
