"""
The contract of the tool that builds a site from a folder of Markdown pages. The code of OpenFlexo only knows
this contract; one class per tool implements it (webbuilder/zensical/ for Zensical).
"""

from abc import ABC, abstractmethod
from pathlib import Path

from webbuilder.common.search_index_interface import SearchIndexInterface


class SiteGeneratorInterface(ABC):
    """A tool that builds a site from a folder of Markdown pages."""

    @abstractmethod
    def build_site(
        self,
        settings: dict,
        site_url: str,
        pages_folder: Path,
        site_folder: Path,
        work_folder: Path,
        side_menu: list | None,
        template_values: dict,
    ) -> bool:
        """
        Builds the site of one version from the pages in pages_folder, written in site_folder. The settings are
        those of the website, site_url is the address of this version, side_menu its menu (None to generate it
        from the pages) and template_values the values its HTML templates read. The tool may write its own files
        in work_folder. Returns False if the tool fails.
        """


    @abstractmethod
    def get_search_index_file_name(self) -> str:
        """The name of the file the tool writes in each site, which the search of its pages reads."""


    @abstractmethod
    def read_search_index(self, file: Path) -> SearchIndexInterface:
        """Reads the search index of a site from its file."""
