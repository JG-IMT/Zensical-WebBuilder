"""Tests of the build of a website: where each version is put, without git and without Zensical."""

import json
import sys
from pathlib import Path

import pytest
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.builder.website.built_website import BuiltWebsite
from webbuilder.builder.version.version_settings import VersionSettings
from webbuilder.builder.website.website_builder import WebsiteBuilder
from webbuilder.common.helper.clone_git_repository import CloneGitRepository

import main
from tests.website_files import LATEST_VERSION, OLD_VERSION, write_website
from webbuilder.builder.website import website_builder
from webbuilder.common.openflexo_interfaces import SiteGeneratorInterface
from webbuilder.zensical.zensical_site_generator import ZensicalSiteGenerator


class FakeVersionBuild:
    """Stands for VersionBuild: its site is one page holding the name of the version, or the build fails."""

    failing_version_name: str = ""

    def __init__(self, website: WebsiteSettings, git_repository: CloneGitRepository, site_generator: SiteGeneratorInterface,
                 version: VersionSettings, version_build_folder: Path) -> None:
        self._version: VersionSettings = version
        self._site_folder: Path = version_build_folder.joinpath("version_site")

    def build(self) -> Path:
        if self._version.get_name() == self.failing_version_name:
            raise SystemExit("Zensical failed")
        self._site_folder.mkdir(parents=True)
        self._site_folder.joinpath("index.html").write_text(f"built {self._version.get_name()}", encoding="utf-8")
        return self._site_folder


@pytest.fixture(autouse=True)
def fake_version_build(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(website_builder, "VersionBuilder", FakeVersionBuild)
    FakeVersionBuild.failing_version_name = ""


def _create_build(tmp_path: Path, versions: dict[str, str] | None = None) -> WebsiteBuilder:
    """A website with the given versions, by default an earlier version "1.5" and a latest version "1.6"."""
    website: WebsiteSettings = WebsiteSettings(write_website(tmp_path, versions or {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}))
    site_generator: SiteGeneratorInterface = ZensicalSiteGenerator(tmp_path)  # not used: the version builds are faked
    built_website: BuiltWebsite = BuiltWebsite(tmp_path.joinpath("build"), website)
    return WebsiteBuilder(website, CloneGitRepository("unused"), site_generator, tmp_path.joinpath("preparation"), built_website)


def _site_folder(tmp_path: Path) -> Path:
    """The folder of the built website: the site_url of the tests is https://example.org/demo/docs/."""
    return tmp_path.joinpath("build", "demo", "docs")


def _page(tmp_path: Path, *path: str) -> str:
    return _site_folder(tmp_path).joinpath(*path).read_text(encoding="utf-8")


def test_builds_every_version_in_its_folder_and_latest_as_a_copy_of_the_latest_version(tmp_path: Path) -> None:
    _create_build(tmp_path).build([])

    assert _page(tmp_path, "1.6", "index.html") == "built 1.6"
    assert _page(tmp_path, "latest", "index.html") == "built 1.6"
    assert _page(tmp_path, "1.5", "index.html") == "built 1.5"
    assert sorted(entry.name for entry in _site_folder(tmp_path).iterdir()) == ["1.5", "1.6", "index.html", "latest", "versions.json"]


def test_the_root_of_the_website_redirects_to_the_latest_version(tmp_path: Path) -> None:
    _create_build(tmp_path).build([])

    assert 'url=latest/"' in _page(tmp_path, "index.html")


def test_building_a_version_replaces_only_its_folder_and_the_copy_of_latest(tmp_path: Path) -> None:
    website_build_of_site: WebsiteBuilder = _create_build(tmp_path)
    website_build_of_site.build([])
    _site_folder(tmp_path).joinpath("1.6", "old_page.html").write_text("old", encoding="utf-8")
    _site_folder(tmp_path).joinpath("latest", "old_page.html").write_text("old", encoding="utf-8")
    _site_folder(tmp_path).joinpath("1.5", "index.html").write_text("kept", encoding="utf-8")

    website_build_of_site.build(["1.6"])

    assert _page(tmp_path, "1.6", "index.html") == "built 1.6"
    assert not _site_folder(tmp_path).joinpath("1.6", "old_page.html").exists()
    assert not _site_folder(tmp_path).joinpath("latest", "old_page.html").exists()
    assert _page(tmp_path, "1.5", "index.html") == "kept"


def test_the_versions_file_lists_the_built_versions_latest_first(tmp_path: Path) -> None:
    _create_build(tmp_path).build([])

    assert [entry["name"] for entry in json.loads(_page(tmp_path, "versions.json"))] == ["1.6", "1.5"]


def test_a_new_latest_version_built_alone_keeps_the_former_latest_version(tmp_path: Path) -> None:
    _create_build(tmp_path).build([])
    versions: dict[str, str] = {"1.5": OLD_VERSION, "1.6": OLD_VERSION, "1.7": LATEST_VERSION}  # 1.7 is the new latest

    _create_build(tmp_path, versions).build(["1.7"])

    assert _page(tmp_path, "1.6", "index.html") == "built 1.6"
    assert _page(tmp_path, "latest", "index.html") == "built 1.7"
    assert [entry["name"] for entry in json.loads(_page(tmp_path, "versions.json"))] == ["1.7", "1.5", "1.6"]


def test_stops_on_unknown_version(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="No version named 9.9"):
        _create_build(tmp_path).build(["9.9"])


def test_a_failed_version_leaves_the_previous_website(tmp_path: Path) -> None:
    website_build_of_site: WebsiteBuilder = _create_build(tmp_path)
    website_build_of_site.build([])
    FakeVersionBuild.failing_version_name = "1.6"
    _site_folder(tmp_path).joinpath("1.5", "index.html").write_text("previous", encoding="utf-8")

    with pytest.raises(SystemExit, match="Zensical failed"):
        website_build_of_site.build([])

    assert _page(tmp_path, "1.5", "index.html") == "previous"  # 1.5, built before 1.6 failed, was not put in the website


def test_build_versions_needs_exactly_one_website(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "--websites-folder", str(tmp_path), "--build-websites", "a", "b", "--build-versions", "1.6"])

    with pytest.raises(SystemExit):
        main._parse_arguments()
