"""Tests of the build of one version, with a fake git repository and a fake site generator."""

from pathlib import Path

import pytest

from tests.website_files import LATEST_VERSION, write_website
from webbuilder.builder.building.version_build import VersionBuild
from webbuilder.builder.settings.website_settings import WebsiteSettings
from webbuilder.common.git_repository import GitRepository
from webbuilder.common.search_index_interface import SearchIndexInterface
from webbuilder.common.site_generator_interface import SiteGeneratorInterface


class FakeGitRepository(GitRepository):
    """Clones nothing: the clone is a folder with one page."""

    def clone_at(self, git_ref: str, destination_folder: Path) -> None:
        destination_folder.joinpath("docs").mkdir(parents=True)
        destination_folder.joinpath("docs", "index.md").write_text("# Home\n", encoding="utf-8")


class FakeSiteGenerator(SiteGeneratorInterface):
    """Remembers what it is asked to build."""

    def __init__(self, is_built: bool) -> None:
        self.is_built: bool = is_built
        self.calls: list[dict] = []

    def build_site(self, **arguments: object) -> bool:  # type: ignore[override]
        self.calls.append(arguments)
        return self.is_built

    def get_search_index_file_name(self) -> str:
        return "search.json"

    def read_search_index(self, file: Path) -> SearchIndexInterface:
        raise NotImplementedError


def _version_build(tmp_path: Path, site_generator: FakeSiteGenerator) -> VersionBuild:
    settings_folder: Path = tmp_path.joinpath("settings")
    settings_folder.mkdir()
    website_settings: WebsiteSettings = WebsiteSettings(write_website(settings_folder, {"1.6": LATEST_VERSION}))
    version = website_settings.get_website_versions().get_latest_version()
    return VersionBuild(website_settings, FakeGitRepository("unused"), site_generator, version, tmp_path.joinpath("work"))


def test_gives_the_site_generator_the_prepared_pages_and_the_values_of_the_version(tmp_path: Path) -> None:
    site_generator: FakeSiteGenerator = FakeSiteGenerator(is_built=True)

    site_folder: Path = _version_build(tmp_path, site_generator).build()

    arguments: dict = site_generator.calls[0]
    assert arguments["site_url"] == "https://example.org/demo/docs/"
    assert arguments["pages_folder"].joinpath("index.md").is_file()  # copied from the documentation sources of the clone
    assert arguments["side_menu"] == ["index.md"]
    assert arguments["template_values"]["displayed_version"] == "1.6"
    assert site_folder == arguments["site_folder"]
    assert not tmp_path.joinpath("work", "version_clone").exists()  # the clone is deleted


def test_stops_when_the_site_generator_fails(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="failed on version 1.6"):
        _version_build(tmp_path, FakeSiteGenerator(is_built=False)).build()

    assert not tmp_path.joinpath("work", "version_clone").exists()  # the clone is deleted also when the build fails
