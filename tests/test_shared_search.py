"""Tests of the search shared by the websites, on two websites built in a folder, without Zensical."""

import json
from pathlib import Path

from tests.website_files import LATEST_VERSION, write_website
from webbuilder.builder.shared_search import SharedSearch
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.zensical.zensical_site_generator import ZensicalSiteGenerator


def _website_settings(tmp_path: Path, name: str) -> WebsiteSettings:
    """A website called name, published at https://example.org/<name>/docs/."""
    site_settings: str = f"site_name: {name.upper()}\nsite_url: https://example.org/{name}/docs/\nextra:\n  repository_url: x\n"
    settings_folder: Path = tmp_path.joinpath("settings", name)
    settings_folder.mkdir(parents=True, exist_ok=True)
    return WebsiteSettings(write_website(settings_folder, {"1.0": LATEST_VERSION}, site_settings))


def _write_index(built_folder: Path, name: str, title: str) -> None:
    index_file: Path = built_folder.joinpath(name, "docs", "search.json")
    index_file.parent.mkdir(parents=True)
    index_file.write_text(json.dumps({"config": {"lang": ["en"]}, "items": [{"location": "index.html", "title": title}]}), encoding="utf-8")


def _titles(built_folder: Path, name: str) -> list[tuple[str, str]]:
    index: dict = json.loads(built_folder.joinpath(name, "docs", "search.json").read_text(encoding="utf-8"))
    return [(item["location"], item["title"]) for item in index["items"]]


def _merge(built_folder: Path, tmp_path: Path) -> None:
    settings_by_name: dict[str, WebsiteSettings] = {name: _website_settings(tmp_path, name) for name in ("a", "b")}
    SharedSearch(built_folder, ZensicalSiteGenerator(tmp_path), "website_search.json").merge(settings_by_name)


def test_each_website_searches_the_pages_of_the_others(tmp_path: Path) -> None:
    built_folder: Path = tmp_path.joinpath("build")
    _write_index(built_folder, "a", "Home of a")
    _write_index(built_folder, "b", "Home of b")

    _merge(built_folder, tmp_path)

    assert _titles(built_folder, "a") == [("index.html", "Home of a"), ("../../b/docs/index.html", "B · Home of b")]
    assert _titles(built_folder, "b") == [("index.html", "Home of b"), ("../../a/docs/index.html", "A · Home of a")]


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
