"""Tests of the build of a website: where each version is put, without git and without Zensical."""

import sys
from pathlib import Path

import pytest

import main
from tests.website_files import LATEST_VERSION, OLD_VERSION, write_website
from webbuilder.builder import website_build
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.builder.website.website_version import WebsiteVersion
from webbuilder.builder.website_build import WebsiteBuild
from webbuilder.common.git_repository import GitRepository
from webbuilder.common.site_generator_interface import SiteGeneratorInterface
from webbuilder.zensical.zensical_site_generator import ZensicalSiteGenerator


class FakeVersionBuild:
    """Stands for VersionBuild: its site is one page holding the name of the version, or the build fails."""

    failing_version_name: str = ""

    def __init__(self, website_settings: WebsiteSettings, git_repository: GitRepository, site_generator: SiteGeneratorInterface,
                 version: WebsiteVersion, version_build_folder: Path) -> None:
        self._version: WebsiteVersion = version
        self._site_folder: Path = version_build_folder.joinpath("version_site")

    def build(self) -> Path:
        if self._version.get_name() == self.failing_version_name:
            raise SystemExit("Zensical failed")
        self._site_folder.mkdir(parents=True)
        self._site_folder.joinpath("index.html").write_text(f"built {self._version.get_name()}", encoding="utf-8")
        return self._site_folder


@pytest.fixture(autouse=True)
def fake_version_build(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(website_build, "VersionBuild", FakeVersionBuild)
    FakeVersionBuild.failing_version_name = ""


def _create_build(tmp_path: Path) -> WebsiteBuild:
    """A website with an earlier version "1.5" and a latest version "1.6"."""
    website_settings: WebsiteSettings = WebsiteSettings(write_website(tmp_path, {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}))
    site_generator: SiteGeneratorInterface = ZensicalSiteGenerator(tmp_path)  # not used: the version builds are faked
    return WebsiteBuild(website_settings, GitRepository("unused"), site_generator, tmp_path.joinpath("preparation"), tmp_path.joinpath("site"))


def _page(tmp_path: Path, *path: str) -> str:
    return tmp_path.joinpath("site", *path).read_text(encoding="utf-8")


def test_builds_the_latest_version_at_the_root_and_the_others_in_their_folder(tmp_path: Path) -> None:
    _create_build(tmp_path).build([])

    assert _page(tmp_path, "index.html") == "built 1.6"
    assert _page(tmp_path, "1.5", "index.html") == "built 1.5"


def test_building_an_earlier_version_replaces_only_its_folder(tmp_path: Path) -> None:
    website_build_of_site: WebsiteBuild = _create_build(tmp_path)
    website_build_of_site.build([])
    tmp_path.joinpath("site", "1.5", "old_page.html").write_text("old", encoding="utf-8")
    tmp_path.joinpath("site", "index.html").write_text("kept", encoding="utf-8")

    website_build_of_site.build(["1.5"])

    assert _page(tmp_path, "1.5", "index.html") == "built 1.5"
    assert not tmp_path.joinpath("site", "1.5", "old_page.html").exists()
    assert _page(tmp_path, "index.html") == "kept"


def test_building_the_latest_version_keeps_the_earlier_versions_and_deletes_the_rest(tmp_path: Path) -> None:
    website_build_of_site: WebsiteBuild = _create_build(tmp_path)
    website_build_of_site.build([])
    tmp_path.joinpath("site", "website_search.json").write_text("{}", encoding="utf-8")
    tmp_path.joinpath("site", "1.0").mkdir()  # the folder of a version that is no longer declared

    website_build_of_site.build(["1.6"])

    assert _page(tmp_path, "index.html") == "built 1.6"
    assert _page(tmp_path, "1.5", "index.html") == "built 1.5"
    assert not tmp_path.joinpath("site", "website_search.json").exists()
    assert not tmp_path.joinpath("site", "1.0").exists()


def test_stops_on_unknown_version(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="No version named 9.9"):
        _create_build(tmp_path).build(["9.9"])


def test_a_failed_version_leaves_the_previous_website(tmp_path: Path) -> None:
    website_build_of_site: WebsiteBuild = _create_build(tmp_path)
    website_build_of_site.build([])
    FakeVersionBuild.failing_version_name = "1.6"
    tmp_path.joinpath("site", "1.5", "index.html").write_text("previous", encoding="utf-8")

    with pytest.raises(SystemExit, match="Zensical failed"):
        website_build_of_site.build([])

    assert _page(tmp_path, "1.5", "index.html") == "previous"  # 1.5, built before 1.6 failed, was not put in the website


def test_build_versions_needs_exactly_one_website(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "--websites-folder", str(tmp_path), "--build-websites", "a", "b", "--build-versions", "1.6"])

    with pytest.raises(SystemExit):
        main._parse_arguments()
