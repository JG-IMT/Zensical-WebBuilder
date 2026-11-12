"""
These interfaces are the contracts between the builder and the tool that builds the sites, whatever that tool is.

SiteGeneratorInterface is the tool that builds a site from a folder of Markdown pages, and reads the search index it
writes. SearchIndexInterface is the search index of one site: a list of pages, each with the 'location' of the page
relative to the site and its 'title'. The builder only knows these contracts; one class per tool implements them
(webbuilder/zensical/ for Zensical).

Used at step 4 (build the HTML of a version) and at step 6 (merge the search).
"""

from abc import ABC, abstractmethod
from pathlib import Path


class SearchIndexInterface(ABC):
    """This interface describes the search index of one site."""

    @abstractmethod
    def get_items(self) -> list[dict]:
        """This method returns a copy of the list of the pages."""


    @abstractmethod
    def get_items_prefixed(self, location_prefix: str, title_prefix: str) -> list[dict]:
        """This method returns the pages for the search of another site: each location and each title start with the prefix."""


    @abstractmethod
    def with_added_items(self, items: list[dict]) -> "SearchIndexInterface":
        """This method returns a new index with the pages of this one followed by the items given."""


    @abstractmethod
    def write(self, file: Path) -> None:
        """This method writes the index in the file, in the format the search of the site reads."""


class SiteGeneratorInterface(ABC):
    """This interface describes a tool that builds a site from a folder of Markdown pages."""

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
        This method builds the site of one version from the pages in pages_folder, written in site_folder. The
        settings are those of the website, site_url is the address of this version, side_menu its menu (None to
        generate it from the pages) and template_values the values its HTML templates read. The tool may write its
        own files in work_folder. It returns False if the tool fails.
        """


    @abstractmethod
    def get_search_index_file_name(self) -> str:
        """This method returns the name of the file the tool writes in each site, which the search of its pages reads."""


    @abstractmethod
    def read_search_index(self, file: Path) -> SearchIndexInterface:
        """This method reads the search index of a site from its file."""
