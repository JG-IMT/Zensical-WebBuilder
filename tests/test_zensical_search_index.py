"""Tests of the search index of one site, as Zensical writes it."""

import json
from pathlib import Path

from webbuilder.zensical.zensical_search_index import ZensicalSearchIndex

INDEX: dict = {"config": {"lang": ["en"]}, "items": [{"location": "faq/", "title": "FAQ", "text": "t"}]}


def test_prefixes_the_location_and_the_title_of_the_pages() -> None:
    items: list[dict] = ZensicalSearchIndex(INDEX).get_items_prefixed("../b/", "B · ")

    assert items == [{"location": "../b/faq/", "title": "B · FAQ", "text": "t"}]


def test_adds_pages_and_keeps_the_config() -> None:
    index: ZensicalSearchIndex = ZensicalSearchIndex(INDEX).with_added_items([{"location": "x", "title": "X"}])

    assert [item["location"] for item in index.get_items()] == ["faq/", "x"]
    assert len(ZensicalSearchIndex(INDEX).get_items()) == 1  # the index added to is unchanged


def test_writes_and_reads_the_same_index(tmp_path: Path) -> None:
    file: Path = tmp_path.joinpath("search.json")
    ZensicalSearchIndex(INDEX).write(file)

    assert json.loads(file.read_text(encoding="utf-8")) == INDEX
    assert ZensicalSearchIndex.read(file).get_items() == INDEX["items"]
