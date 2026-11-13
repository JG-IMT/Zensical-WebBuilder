"""
This class represents the search index that Zensical writes for one site (search.json), which the search of its pages reads.

The index is made of a 'config' and one item per page, with the 'location' of the page relative to the site and its
'title'. This is the only place that knows this format.

Used at step 6 (merge the search), through SearchIndexInterface.
"""

import json
from pathlib import Path

from webbuilder.common.openflexo_interfaces import SearchIndexInterface


class ZensicalSearchIndex(SearchIndexInterface):
    """This class holds the search index of one site."""

    # == Public ====================================================================================

    # -- Initialization ----------------------------------------------------------------------------

    def __init__(self, index: dict) -> None:
        """This constructor holds an index as read from the file: {"config": {...}, "items": [{"location", "title", ...}]}."""
        self._index: dict = index


    @staticmethod
    def read(file: Path) -> "ZensicalSearchIndex":
        """This method reads the index of a site from its search.json."""
        return ZensicalSearchIndex(json.loads(file.read_text(encoding="utf-8")))


    # -- Getters -----------------------------------------------------------------------------------

    def get_items(self) -> list[dict]:
        """This method returns a copy of the list of the pages."""
        return list(self._index["items"])


    def get_items_prefixed(self, location_prefix: str, title_prefix: str) -> list[dict]:
        """This method returns the pages for the search of another site: each location and each title start with the prefix."""
        return [
            {**item, "location": location_prefix + item["location"], "title": title_prefix + item["title"]}
            for item in self._index["items"]
        ]


    # -- Outputs -----------------------------------------------------------------------------------

    def with_added_items(self, items: list[dict]) -> "ZensicalSearchIndex":
        """This method returns a new index with the same config and the pages of this one followed by the items given."""
        return ZensicalSearchIndex({"config": self._index["config"], "items": self.get_items() + items})


    def write(self, file: Path) -> None:
        """This method writes the index in the format that the search of the pages reads."""
        file.write_text(json.dumps(self._index), encoding="utf-8")
