"""
The contract of the search index of one site, whatever the tool that builds the site: a list of pages, each
with the 'location' of the page relative to the site and its 'title'.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class SearchIndexInterface(ABC):
    """The search index of one site."""

    @abstractmethod
    def get_items(self) -> list[dict]:
        """A copy of the list of the pages."""


    @abstractmethod
    def get_items_prefixed(self, location_prefix: str, title_prefix: str) -> list[dict]:
        """The pages for the search of another site: each location and each title start with the prefix."""


    @abstractmethod
    def with_added_items(self, items: list[dict]) -> "SearchIndexInterface":
        """A new index with the pages of this one followed by the items given."""


    @abstractmethod
    def write(self, file: Path) -> None:
        """Writes the index in the file, in the format the search of the site reads."""
