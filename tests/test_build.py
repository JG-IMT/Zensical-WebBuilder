"""Tests of the build, from main.py down to the places of the files, with a fake git repository and a fake site generator."""

import argparse
import json
import sys
from pathlib import Path

import pytest

import main
from tests.fake_website import LATEST_VERSION, OLD_VERSION, named_site_settings, site_settings_with_latest, write_website
from webbuilder.builder.version.version_builder import VersionBuilder
from webbuilder.builder.version.version_settings import VersionSettings
from webbuilder.builder.website import website_builder
from webbuilder.builder.website.built_website import BuiltWebsite
from webbuilder.builder.website.website_builder import WebsiteBuilder
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.common.helper.clone_git_repository import CloneGitRepository
from webbuilder.common.openflexo_interfaces import SearchIndexInterface, SiteGeneratorInterface
from webbuilder.zensical.zensical_search_index import ZensicalSearchIndex
from webbuilder.zensical.zensical_site_generator import ZensicalSiteGenerator


class FakeGitRepository(CloneGitRepository):
    """Clones nothing: the clone is a folder with one page."""

    def clone_at(self, git_ref: str, destination_folder: Path) -> None:
        destination_folder.joinpath("docs").mkdir(parents=True)
        destination_folder.joinpath("docs", "index.md").write_text("# Home\n", encoding="utf-8")


class RecordingSiteGenerator(SiteGeneratorInterface):
    """Remembers what it is asked to build, and succeeds or fails as asked."""

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


class WritingSiteGenerator(SiteGeneratorInterface):
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


class FakeVersionBuild:
    """Stands for VersionBuilder: its site is one page holding the name of the version, or the build fails."""

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


@pytest.fixture
def fake_version_build(monkeypatch: pytest.MonkeyPatch) -> None:
    """The versions of a WebsiteBuilder are built by FakeVersionBuild: no clone, no site generator."""
    monkeypatch.setattr(website_builder, "VersionBuilder", FakeVersionBuild)
    FakeVersionBuild.failing_version_name = ""


# -- The places of the files of a built website ------------------------------------------------------

def _website(tmp_path: Path, name: str = "demo") -> WebsiteSettings:
    """A website with an earlier version "1.5" and a latest version "1.6", published at https://example.org/<name>/docs/."""
    settings_folder: Path = tmp_path.joinpath("settings", name)
    settings_folder.mkdir(parents=True)
    return WebsiteSettings(write_website(settings_folder, {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}, named_site_settings(name, "1.6")))


def _built_website(tmp_path: Path, name: str = "demo") -> BuiltWebsite:
    return BuiltWebsite(tmp_path.joinpath("build"), _website(tmp_path, name))


def test_the_folder_of_the_website_is_named_after_its_site_url(tmp_path: Path) -> None:
    assert _built_website(tmp_path).get_folder() == tmp_path.joinpath("build", "demo", "docs")


def test_each_version_has_its_own_folder_and_latest_is_another_folder(tmp_path: Path) -> None:
    website: WebsiteSettings = _website(tmp_path)
    built_website: BuiltWebsite = BuiltWebsite(tmp_path.joinpath("build"), website)
    latest_version: VersionSettings = website.get_website_version_list().get_latest_version()

    assert built_website.get_version_folder(latest_version) == built_website.get_folder().joinpath("1.6")
    assert built_website.get_latest_version_folder() == built_website.get_folder().joinpath("latest")
    assert built_website.get_search_index_file("search.json") == built_website.get_folder().joinpath("latest", "search.json")


def test_the_versions_file_lists_the_built_versions_latest_first(tmp_path: Path) -> None:
    built_website: BuiltWebsite = _built_website(tmp_path)
    built_website.get_folder().joinpath("1.5").mkdir(parents=True)
    built_website.get_folder().joinpath("1.6").mkdir()

    built_website.write_versions_file()

    entries: list[dict] = json.loads(built_website.get_folder().joinpath("versions.json").read_text(encoding="utf-8"))
    assert entries == [
        {"name": "1.6", "link": "latest", "is_latest": True},
        {"name": "1.5", "link": "1.5", "is_latest": False},
    ]


def test_the_versions_file_leaves_out_a_version_that_is_not_built(tmp_path: Path) -> None:
    built_website: BuiltWebsite = _built_website(tmp_path)
    built_website.get_folder().joinpath("1.5").mkdir(parents=True)

    built_website.write_versions_file()

    entries: list[dict] = json.loads(built_website.get_folder().joinpath("versions.json").read_text(encoding="utf-8"))
    assert [entry["name"] for entry in entries] == ["1.5"]


def test_the_path_to_another_website_goes_from_latest_to_latest(tmp_path: Path) -> None:
    assert _built_website(tmp_path, "a").get_path_to_latest_version_of(_built_website(tmp_path, "b")) == "../../../b/docs/latest"


def test_the_root_of_the_website_redirects_to_latest(tmp_path: Path) -> None:
    built_website: BuiltWebsite = _built_website(tmp_path)
    built_website.get_folder().mkdir(parents=True)

    built_website.write_redirection_to_latest_version()

    assert 'url=latest/"' in built_website.get_folder().joinpath("index.html").read_text(encoding="utf-8")


# -- The build of one version ------------------------------------------------------------------------

def _version_build(tmp_path: Path, site_generator: RecordingSiteGenerator) -> VersionBuilder:
    settings_folder: Path = tmp_path.joinpath("settings")
    settings_folder.mkdir()
    website: WebsiteSettings = WebsiteSettings(write_website(settings_folder, {"1.6": LATEST_VERSION}))
    version: VersionSettings = website.get_website_version_list().get_latest_version()
    return VersionBuilder(website, FakeGitRepository("unused"), site_generator, version, tmp_path.joinpath("work"))


def test_gives_the_site_generator_the_prepared_pages_and_the_values_of_the_version(tmp_path: Path) -> None:
    site_generator: RecordingSiteGenerator = RecordingSiteGenerator(is_built=True)

    site_folder: Path = _version_build(tmp_path, site_generator).build()

    arguments: dict = site_generator.calls[0]
    assert arguments["site_url"] == "https://example.org/demo/docs/1.6/"
    assert arguments["pages_folder"].joinpath("index.md").is_file()  # copied from the documentation sources of the clone
    assert arguments["side_menu"] == ["index.md"]
    assert arguments["template_values"]["displayed_version"] == "1.6"
    assert site_folder == arguments["site_folder"]
    assert not tmp_path.joinpath("work", "version_clone").exists()  # the clone is deleted


def test_stops_when_the_site_generator_fails(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="failed on version 1.6"):
        _version_build(tmp_path, RecordingSiteGenerator(is_built=False)).build()

    assert not tmp_path.joinpath("work", "version_clone").exists()  # the clone is deleted also when the build fails


# -- The build of a website: where each version is put -----------------------------------------------

def _create_build(tmp_path: Path, versions: dict[str, str] | None = None, latest_version: str = "1.6") -> WebsiteBuilder:
    """A website with the given versions, by default an earlier version "1.5" and a latest version "1.6"."""
    settings_file: Path = write_website(tmp_path, versions or {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}, site_settings_with_latest(latest_version))
    website: WebsiteSettings = WebsiteSettings(settings_file)
    site_generator: SiteGeneratorInterface = ZensicalSiteGenerator(tmp_path)  # not used: the version builds are faked
    built_website: BuiltWebsite = BuiltWebsite(tmp_path.joinpath("build"), website)
    return WebsiteBuilder(website, CloneGitRepository("unused"), site_generator, tmp_path.joinpath("preparation"), built_website)


def _site_folder(tmp_path: Path) -> Path:
    """The folder of the built website: the site_url of the tests is https://example.org/demo/docs/."""
    return tmp_path.joinpath("build", "demo", "docs")


def _page(tmp_path: Path, *path: str) -> str:
    return _site_folder(tmp_path).joinpath(*path).read_text(encoding="utf-8")


@pytest.mark.usefixtures("fake_version_build")
def test_builds_every_version_in_its_folder_and_latest_as_a_copy_of_the_latest_version(tmp_path: Path) -> None:
    _create_build(tmp_path).build([])

    assert _page(tmp_path, "1.6", "index.html") == "built 1.6"
    assert _page(tmp_path, "latest", "index.html") == "built 1.6"
    assert _page(tmp_path, "1.5", "index.html") == "built 1.5"
    assert sorted(entry.name for entry in _site_folder(tmp_path).iterdir()) == ["1.5", "1.6", "index.html", "latest", "versions.json"]


@pytest.mark.usefixtures("fake_version_build")
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


@pytest.mark.usefixtures("fake_version_build")
def test_a_new_latest_version_built_alone_keeps_the_former_latest_version(tmp_path: Path) -> None:
    _create_build(tmp_path).build([])
    versions: dict[str, str] = {"1.5": OLD_VERSION, "1.6": OLD_VERSION, "1.7": LATEST_VERSION}

    _create_build(tmp_path, versions, latest_version="1.7").build(["1.7"])

    assert _page(tmp_path, "1.6", "index.html") == "built 1.6"
    assert _page(tmp_path, "latest", "index.html") == "built 1.7"
    assert [entry["name"] for entry in json.loads(_page(tmp_path, "versions.json"))] == ["1.7", "1.5", "1.6"]


@pytest.mark.usefixtures("fake_version_build")
def test_stops_on_unknown_version(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="No version named 9.9"):
        _create_build(tmp_path).build(["9.9"])


@pytest.mark.usefixtures("fake_version_build")
def test_a_failed_version_leaves_the_previous_website(tmp_path: Path) -> None:
    website_build_of_site: WebsiteBuilder = _create_build(tmp_path)
    website_build_of_site.build([])
    FakeVersionBuild.failing_version_name = "1.6"
    _site_folder(tmp_path).joinpath("1.5", "index.html").write_text("previous", encoding="utf-8")

    with pytest.raises(SystemExit, match="Zensical failed"):
        website_build_of_site.build([])

    assert _page(tmp_path, "1.5", "index.html") == "previous"  # 1.5, built before 1.6 failed, was not put in the website


# -- The run of main.py on two websites --------------------------------------------------------------

def _write_websites(websites_folder: Path) -> None:
    for name in ("a", "b"):
        website_folder: Path = websites_folder.joinpath(name)
        website_folder.mkdir(parents=True)
        write_website(website_folder, {"1.0": LATEST_VERSION}, named_site_settings(name, "1.0"))


def _run(websites_folder: Path, website_names: list[str]) -> None:
    arguments: argparse.Namespace = argparse.Namespace(websites_folder=websites_folder, build_websites=website_names, build_versions=[])
    main.run(arguments, WritingSiteGenerator())


def test_builds_every_website_and_gives_each_one_the_search_of_the_others(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(main, "CloneGitRepository", FakeGitRepository)
    _write_websites(tmp_path)

    _run(tmp_path, [])

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
    _run(tmp_path, [])
    tmp_path.joinpath("build", "b", "docs", "latest", "index.html").write_text("kept", encoding="utf-8")

    _run(tmp_path, ["a"])

    assert tmp_path.joinpath("build", "b", "docs", "latest", "index.html").read_text(encoding="utf-8") == "kept"
    search: dict = json.loads(tmp_path.joinpath("build", "a", "docs", "latest", "search.json").read_text(encoding="utf-8"))
    assert len(search["items"]) == 2


def test_build_versions_needs_exactly_one_website(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "--websites-folder", str(tmp_path), "--build-websites", "a", "b", "--build-versions", "1.6"])

    with pytest.raises(SystemExit):
        main._parse_arguments()
