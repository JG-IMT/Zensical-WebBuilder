"""Tests of the search: the index of one site, and the search shared by the websites (without Zensical)."""

import json
from pathlib import Path

from tests.fake_website import LATEST_VERSION, named_site_settings, write_website
from webbuilder.builder.search.global_search import GlobalSearch
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.zensical.zensical_search_index import ZensicalSearchIndex
from webbuilder.zensical.zensical_site_generator import ZensicalSiteGenerator

INDEX: dict = {"config": {"lang": ["en"]}, "items": [{"location": "faq/", "title": "FAQ", "text": "t"}]}


# -- The index of one site ---------------------------------------------------------------------------

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


# -- The search shared by the websites ---------------------------------------------------------------

def _website(tmp_path: Path, name: str) -> WebsiteSettings:
    """A website called name, published at https://example.org/<name>/docs/."""
    settings_folder: Path = tmp_path.joinpath("settings", name)
    settings_folder.mkdir(parents=True, exist_ok=True)
    return WebsiteSettings(write_website(settings_folder, {"1.0": LATEST_VERSION}, named_site_settings(name, "1.0")))


def _write_index(built_folder: Path, name: str, title: str) -> None:
    index_file: Path = built_folder.joinpath(name, "docs", "latest", "search.json")
    index_file.parent.mkdir(parents=True)
    index_file.write_text(json.dumps({"config": {"lang": ["en"]}, "items": [{"location": "index.html", "title": title}]}), encoding="utf-8")


def _titles(built_folder: Path, name: str) -> list[tuple[str, str]]:
    index: dict = json.loads(built_folder.joinpath(name, "docs", "latest", "search.json").read_text(encoding="utf-8"))
    return [(item["location"], item["title"]) for item in index["items"]]


def _merge(built_folder: Path, tmp_path: Path) -> None:
    website_by_name: dict[str, WebsiteSettings] = {name: _website(tmp_path, name) for name in ("a", "b")}
    GlobalSearch(built_folder, ZensicalSiteGenerator(tmp_path), "website_search.json").merge(website_by_name)


def test_each_website_searches_the_pages_of_the_others(tmp_path: Path) -> None:
    built_folder: Path = tmp_path.joinpath("build")
    _write_index(built_folder, "a", "Home of a")
    _write_index(built_folder, "b", "Home of b")

    _merge(built_folder, tmp_path)

    assert _titles(built_folder, "a") == [("index.html", "Home of a"), ("../../../b/docs/latest/index.html", "B · Home of b")]
    assert _titles(built_folder, "b") == [("index.html", "Home of b"), ("../../../a/docs/latest/index.html", "A · Home of a")]


def test_merging_again_does_not_repeat_the_pages(tmp_path: Path) -> None:
    built_folder: Path = tmp_path.joinpath("build")
    _write_index(built_folder, "a", "Home of a")
    _write_index(built_folder, "b", "Home of b")

    _merge(built_folder, tmp_path)
    _merge(built_folder, tmp_path)

    assert len(_titles(built_folder, "a")) == 2


def test_a_website_not_built_is_skipped(tmp_path: Path) -> None:
    built_folder: Path = tmp_path.joinpath("build")
    _write_index(built_folder, "a", "Home of a")

    _merge(built_folder, tmp_path)

    assert _titles(built_folder, "a") == [("index.html", "Home of a")]
