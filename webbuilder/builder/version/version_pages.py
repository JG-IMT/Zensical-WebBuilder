"""
Prepares the folder of pages the site generator reads to build one version of the website: the shared style and icon,
the Markdown pages and images of the version, the menu of versions. The folder holding the sources of the
version (its clone) is given.
"""

import json
import os
import posixpath
from pathlib import Path

from webbuilder.builder.files.file_and_folder_names import VERSION_MENU_FILE_NAME
from webbuilder.builder.files.shared_paths import SHARED_STYLE_AND_ICON_FOLDER
from webbuilder.builder.settings.website import Website
from webbuilder.builder.settings.website_version import WebsiteVersion
from webbuilder.builder.settings.website_version_list import WebsiteVersionList
from webbuilder.builder.version.page_url_resolver import PageUrlResolver
from webbuilder.builder.version.page_url_rewriter import PageUrlRewriter
from webbuilder.common.folder_helper import FolderHelper

MARKDOWN_EXTENSION: str = ".md"


class VersionPages:
    """Prepares the folder of pages from which the site generator builds the site of one version."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self,
        website: Website,
        version_clone_folder: Path,
        pages_folder: Path,
        version: WebsiteVersion,
    ) -> None:
        self._website: Website = website
        self._version_clone_folder: Path = version_clone_folder  # the clone of the version: its sources
        self._pages_folder: Path = pages_folder  # the folder Zensical reads the pages from
        self._version: WebsiteVersion = version
        self._website_version_list: WebsiteVersionList = website.get_website_version_list()


    # -- Public: preparation -------------------------------------------------------------------------

    def prepare_pages(self) -> None:
        """Prepares the pages folder with data: style and icon, pages of the version, menu of versions."""
        # The pages folder does not exist yet: WebsiteBuild empties the build folders of the versions first.
        self._copy_style_and_icon()
        self._copy_documentation_sources()

        markdown_page_files: list[Path] = self._find_markdown_pages()
        self._rewrite_urls(markdown_page_files)
        print(f"Prepared {len(markdown_page_files)} Markdown pages in {self._pages_folder}")

        self._write_version_menu_file()


    # -- Private: pages folder -----------------------------------------------------------------------

    def _copy_style_and_icon(self) -> None:
        """Copies the style and the icon shared by every website."""
        FolderHelper.copy_folder(SHARED_STYLE_AND_ICON_FOLDER, self._pages_folder)


    def _copy_documentation_sources(self) -> None:
        """Copies each documentation source of the clone to its destination. Throws an error if a source is missing."""
        for documentation_source in self._version.get_documentation_sources():
            source_folder: Path = self._version_clone_folder.joinpath(documentation_source["source"])
            if not source_folder.is_dir():
                raise SystemExit(f"Version {self._version.get_name()}: folder '{documentation_source['source']}' not found")
            FolderHelper.copy_folder(source_folder, self._pages_folder.joinpath(documentation_source["destination"]))


    def _find_markdown_pages(self) -> list[Path]:
        """The Markdown pages in the pages folder. Throws an error if there is none."""
        markdown_page_files: list[Path] = []
        for walked_folder, subfolder_names, file_names in os.walk(self._pages_folder):
            for file_name in file_names:
                if file_name.endswith(MARKDOWN_EXTENSION):
                    markdown_page_files.append(Path(walked_folder).joinpath(file_name))
        if not markdown_page_files:
            raise SystemExit(f"Version {self._version.get_name()}: no Markdown page in the documentation sources")
        return markdown_page_files


    def _rewrite_urls(self, markdown_page_files: list[Path]) -> None:
        """Rewrites the URLs starting with "/" in the copies of the pages."""
        url_resolver: PageUrlResolver = PageUrlResolver(
            self._pages_folder, self._website.get_homepage_url_path()
        )
        PageUrlRewriter(url_resolver).rewrite_urls_in(markdown_page_files)


    # -- Private: menu of versions -------------------------------------------------------------------

    def _write_version_menu_file(self) -> None:
        """Read by the version menu of every page: the latest version first, then the earlier ones."""
        versions: list[WebsiteVersion] = (
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


    def _url_to_root_of(self, target_version: WebsiteVersion) -> str:
        """From the root of this version: "." for itself, "../1.6" for the folder of another version."""
        return posixpath.relpath(
            self._website_version_list.folder_in_website_of(target_version), start=self._website_version_list.folder_in_website_of(self._version)
        )
