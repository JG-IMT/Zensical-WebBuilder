"""
Prepares what Zensical needs to build one version of the website: the input folder (the shared
style and icon, the Markdown pages and images of the version, the menu of versions) and the
Zensical config file. The folder holding the sources of the version (its clone) is given.
"""

import json
import os
import posixpath
from pathlib import Path

import yaml

from webbuilder.helper.folder_helper import FolderHelper
from webbuilder.preparation.page_url_resolver import PageUrlResolver
from webbuilder.preparation.page_url_rewriter import PageUrlRewriter
from webbuilder.settings.website_settings import WebsiteSettings
from webbuilder.settings.website_version import WebsiteVersion
from webbuilder.settings.website_version_catalog import WebsiteVersionCatalog
from webbuilder.shared_paths import SHARED_HTML_TEMPLATES_FOLDER, SHARED_STYLE_AND_ICON_FOLDER

MARKDOWN_EXTENSION: str = ".md"
ZENSICAL_INPUT_FOLDER_NAME: str = "zensical_input"
VERSION_SITE_FOLDER_NAME: str = "version_site"
ZENSICAL_CONFIG_FILE_NAME: str = "zensical_config.yml"
VERSION_MENU_FILE_NAME: str = "versions.json"


class ZensicalInput:
    """Prepares the input folder and the Zensical config file from which the site of one version is built."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self,
        website_settings: WebsiteSettings,
        version_clone_folder: Path,
        version_build_folder: Path,
        version: WebsiteVersion,
    ) -> None:
        self._website_settings: WebsiteSettings = website_settings
        self._version_clone_folder: Path = version_clone_folder  # the clone of the version: its sources
        self._version: WebsiteVersion = version
        self._version_catalog: WebsiteVersionCatalog = website_settings.get_version_catalog()

        self._zensical_input_folder: Path = version_build_folder.joinpath(ZENSICAL_INPUT_FOLDER_NAME)
        self._zensical_config_file: Path = version_build_folder.joinpath(ZENSICAL_CONFIG_FILE_NAME)


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


    def write_config(self) -> Path:
        """Writes the settings Zensical receives, completed with what is specific to this version. Returns the file."""
        zensical_config: dict = self._website_settings.get_zensical_settings()
        self._set_site_url(zensical_config)
        self._set_folders(zensical_config)
        self._set_displayed_versions(zensical_config)
        self._set_side_menu(zensical_config)

        self._write_yaml_file(self._zensical_config_file, zensical_config)
        return self._zensical_config_file


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


    # -- Private: Zensical config --------------------------------------------------------------------

    def _set_site_url(self, zensical_config: dict) -> None:
        """Sets the address of this version in the website."""
        zensical_config["site_url"] = self._version_catalog.site_url_of(self._version)


    def _set_folders(self, zensical_config: dict) -> None:
        """Sets the folder Zensical reads the pages from, the folder it writes the site in and the HTML templates folder."""
        # Paths are relative to the generated config file, which is where Zensical reads them from.
        templates_path: str = os.path.relpath(SHARED_HTML_TEMPLATES_FOLDER, self._zensical_config_file.parent)

        zensical_config["docs_dir"] = ZENSICAL_INPUT_FOLDER_NAME
        zensical_config["site_dir"] = VERSION_SITE_FOLDER_NAME
        zensical_config["theme"]["custom_dir"] = Path(templates_path).as_posix()


    def _set_displayed_versions(self, zensical_config: dict) -> None:
        """Sets the version displayed by the page templates, and the latest version its banner links to."""
        latest_version: WebsiteVersion = self._version_catalog.get_latest_version()

        # Read by the page templates (shared/html_templates): the version badge, and the banner of an
        # earlier version linking to the latest one.
        zensical_config["extra"]["displayed_version"] = self._version.get_name()
        zensical_config["extra"]["latest_version"] = latest_version.get_name()
        zensical_config["extra"]["latest_version_url"] = self._version_catalog.site_url_of(latest_version)


    def _set_side_menu(self, zensical_config: dict) -> None:
        """Sets the menu of the version, if it declares one."""
        if self._version.get_side_menu():
            zensical_config["nav"] = self._version.get_side_menu()


    # -- Private: YAML -------------------------------------------------------------------------------

    @staticmethod
    def _write_yaml_file(file: Path, content: dict) -> None:
        """Writes the content as a YAML file, creating its folder if needed."""
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(yaml.safe_dump(content, sort_keys=False, allow_unicode=True), encoding="utf-8")
