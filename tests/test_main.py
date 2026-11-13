"""Test of the whole run of main.py on two websites, with a fake git repository and a fake site generator."""

import argparse
import json
from pathlib import Path

import pytest
from webbuilder.common.helper.clone_git_repository import CloneGitRepository

import main
from tests.website_files import LATEST_VERSION, write_website
from webbuilder.common.openflexo_interfaces import SearchIndexInterface, SiteGeneratorInterface
from webbuilder.zensical.zensical_search_index import ZensicalSearchIndex


class FakeGitRepository(CloneGitRepository):
    """Clones nothing: the clone is a folder with one page."""

    def clone_at(self, git_ref: str, destination_folder: Path) -> None:
        destination_folder.joinpath("docs").mkdir(parents=True)
        destination_folder.joinpath("docs", "index.md").write_text("# Home\n", encoding="utf-8")


class FakeSiteGenerator(SiteGeneratorInterface):
    """Writes a site of one page and its search index, as Zensical does."""

    def build_site(self, **arguments: object) -> bool:  # type: ignore[override]
        site_folder: Path = arguments["site_folder"]  # type: ignore[assignment]
        site_folder.mkdir(parents=True)
        site_folder.joinpath("index.html").write_text("page", encoding="utf-8")
        items: list[dict] = [{"location": "index.html", "title": arguments["settings"]["site_name"]}]  # type: ignore[index]
        site_folder.joinpath("search.json").write_text(json.dumps({"config": {}, "items": items}), encoding="utf-8")
        return True

    def get_search_index_file_name(self) -> str:
        return "search.json"

    def read_search_index(self, file: Path) -> SearchIndexInterface:
        return ZensicalSearchIndex.read(file)


def _write_websites(websites_folder: Path) -> None:
    for name in ("a", "b"):
        site_settings: str = f"site_name: {name.upper()}\nsite_url: https://example.org/{name}/docs/\nextra:\n  repository_url: x\n  latest_version: \"1.0\"\n"
        website_folder: Path = websites_folder.joinpath(name)
        website_folder.mkdir(parents=True)
        write_website(website_folder, {"1.0": LATEST_VERSION}, site_settings)


def test_builds_every_website_and_gives_each_one_the_search_of_the_others(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(main, "CloneGitRepository", FakeGitRepository)
    _write_websites(tmp_path)

    main.run(argparse.Namespace(websites_folder=tmp_path, build_websites=[], build_versions=[]), FakeSiteGenerator())

    website_a: Path = tmp_path.joinpath("build", "a", "docs")
    assert website_a.joinpath("latest", "index.html").read_text(encoding="utf-8") == "page"
    assert 'url=latest/"' in website_a.joinpath("index.html").read_text(encoding="utf-8")
    search: dict = json.loads(website_a.joinpath("latest", "search.json").read_text(encoding="utf-8"))
    assert [(item["location"], item["title"]) for item in search["items"]] == [
        ("index.html", "A"),
        ("../../../b/docs/latest/index.html", "B · B"),
    ]


def test_builds_only_the_websites_named_and_keeps_the_search_of_the_others(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(main, "CloneGitRepository", FakeGitRepository)
    _write_websites(tmp_path)
    main.run(argparse.Namespace(websites_folder=tmp_path, build_websites=[], build_versions=[]), FakeSiteGenerator())
    tmp_path.joinpath("build", "b", "docs", "latest", "index.html").write_text("kept", encoding="utf-8")

    main.run(argparse.Namespace(websites_folder=tmp_path, build_websites=["a"], build_versions=[]), FakeSiteGenerator())

    assert tmp_path.joinpath("build", "b", "docs", "latest", "index.html").read_text(encoding="utf-8") == "kept"
    search: dict = json.loads(tmp_path.joinpath("build", "a", "docs", "latest", "search.json").read_text(encoding="utf-8"))
    assert len(search["items"]) == 2
