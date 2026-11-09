"""
Prepares the input folder Zensical reads to build one version of the website: the shared style and icon,
the Markdown pages and images of the version, the menu of versions. The folder holding the sources of the
version (its clone) is given.
"""

import json
import os
import posixpath
from pathlib import Path

from webbuilder.common.folder_helper import FolderHelper
from webbuilder.openflexo.preparation.page_url_resolver import PageUrlResolver
from webbuilder.openflexo.preparation.page_url_rewriter import PageUrlRewriter
from webbuilder.openflexo.settings.website_settings import WebsiteSettings
from webbuilder.openflexo.settings.website_version import WebsiteVersion
from webbuilder.openflexo.settings.website_version_catalog import WebsiteVersionCatalog
from webbuilder.openflexo.shared_paths import SHARED_STYLE_AND_ICON_FOLDER

MARKDOWN_EXTENSION: str = ".md"
VERSION_MENU_FILE_NAME: str = "versions.json"


class VersionInput:
    """Prepares the input folder from which Zensical builds the site of one version."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self,
        website_settings: WebsiteSettings,
        version_clone_folder: Path,
        zensical_input_folder: Path,
        version: WebsiteVersion,
    ) -> None:
        self._website_settings: WebsiteSettings = website_settings
        self._version_clone_folder: Path = version_clone_folder  # the clone of the version: its sources
        self._zensical_input_folder: Path = zensical_input_folder  # the folder Zensical reads the pages from
        self._version: WebsiteVersion = version
        self._version_catalog: WebsiteVersionCatalog = website_settings.get_version_catalog()


    # -- Public: preparation -------------------------------------------------------------------------

    def prepare_input(self) -> None:
        """Prepares the input folder with data: style and icon, pages of the version, menu of versions."""
        # The input folder does not exist yet: WebsiteBuild empties the build folders of the versions first.
        self._copy_style_and_icon()
        self._copy_documentation_sources()

        markdown_page_files: list[Path] = self._find_markdown_pages()
        self._rewrite_urls(markdown_page_files)
        print(f"Prepared {len(markdown_page_files)} Markdown pages in {self._zensical_input_folder}")

        self._write_version_menu_file()


    # -- Private: input folder -----------------------------------------------------------------------

    def _copy_style_and_icon(self) -> None:
        """Copies the style and the icon shared by every website."""
        FolderHelper.copy_folder(SHARED_STYLE_AND_ICON_FOLDER, self._zensical_input_folder)


    def _copy_documentation_sources(self) -> None:
        """Copies each documentation source of the clone to its destination. Throws an error if a source is missing."""
        for documentation_source in self._version.get_documentation_sources():
            source_folder: Path = self._version_clone_folder.joinpath(documentation_source["source"])
            if not source_folder.is_dir():
                raise SystemExit(f"Version {self._version.get_name()}: folder '{documentation_source['source']}' not found")
            FolderHelper.copy_folder(source_folder, self._zensical_input_folder.joinpath(documentation_source["destination"]))


    def _find_markdown_pages(self) -> list[Path]:
        """The Markdown pages in the input folder. Throws an error if there is none."""
        markdown_page_files: list[Path] = []
        for walked_folder, subfolder_names, file_names in os.walk(self._zensical_input_folder):
            for file_name in file_names:
                if file_name.endswith(MARKDOWN_EXTENSION):
                    markdown_page_files.append(Path(walked_folder).joinpath(file_name))
        if not markdown_page_files:
            raise SystemExit(f"Version {self._version.get_name()}: no Markdown page in the documentation sources")
        return markdown_page_files


    def _rewrite_urls(self, markdown_page_files: list[Path]) -> None:
        """Rewrites the URLs starting with "/" in the copies of the pages."""
        url_resolver: PageUrlResolver = PageUrlResolver(
            self._zensical_input_folder, self._website_settings.get_homepage_url_path()
        )
        PageUrlRewriter(url_resolver).rewrite_urls_in(markdown_page_files)


    # -- Private: menu of versions -------------------------------------------------------------------

    def _write_version_menu_file(self) -> None:
        """Read by the version menu of every page: the latest version first, then the earlier ones."""
        versions: list[WebsiteVersion] = (
            [self._version_catalog.get_latest_version()] + self._version_catalog.get_earlier_versions()
        )
        menu_entries: list[dict] = []
        for version in versions:
            menu_entries.append({
                "name": version.get_name(),
                "link": self._url_to_root_of(version),
                "current": version.get_name() == self._version.get_name(),
            })
        versions_file: Path = self._zensical_input_folder.joinpath(VERSION_MENU_FILE_NAME)
        versions_file.write_text(json.dumps(menu_entries, indent=2), encoding="utf-8")


    def _url_to_root_of(self, target_version: WebsiteVersion) -> str:
        """From the root of this version: "." for itself, "../1.6" for the folder of another version."""
        return posixpath.relpath(
            self._version_catalog.folder_in_website_of(target_version), start=self._version_catalog.folder_in_website_of(self._version)
        )
