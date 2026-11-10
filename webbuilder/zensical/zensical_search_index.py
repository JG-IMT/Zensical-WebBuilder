"""
The search index Zensical writes for one site (search.json), which the search of its pages reads: a 'config'
and one item per page, with the 'location' of the page relative to the site and its 'title'. This is the only
place that knows this format.
"""

import json
from pathlib import Path

from webbuilder.common.openflexo_interface import SearchIndexInterface


class ZensicalSearchIndex(SearchIndexInterface):
    """The search index of one site."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, index: dict) -> None:
        self._index: dict = index  # as read from the file: {"config": {...}, "items": [{"location", "title", ...}]}


    @staticmethod
    def read(file: Path) -> "ZensicalSearchIndex":
        """Reads the index of a site from its search.json."""
        return ZensicalSearchIndex(json.loads(file.read_text(encoding="utf-8")))


    # -- Public: use ---------------------------------------------------------------------------------

    def write(self, file: Path) -> None:
        """Writes the index, as Zensical does, for the search of the pages."""
        file.write_text(json.dumps(self._index), encoding="utf-8")


    def get_items(self) -> list[dict]:
        """A copy of the list of the pages."""
        return list(self._index["items"])


    def get_items_prefixed(self, location_prefix: str, title_prefix: str) -> list[dict]:
        """The pages for the search of another site: each location and each title start with the prefix."""
        return [
            {**item, "location": location_prefix + item["location"], "title": title_prefix + item["title"]}
            for item in self._index["items"]
        ]


    def with_added_items(self, items: list[dict]) -> "ZensicalSearchIndex":
        """A new index with the same config and the pages of this one followed by the items given."""
        return ZensicalSearchIndex({"config": self._index["config"], "items": self.get_items() + items})
