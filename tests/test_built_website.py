"""Tests of the places of the files of a built website."""

import json
from pathlib import Path

from tests.website_files import LATEST_VERSION, OLD_VERSION, write_website
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.builder.version.version_settings import VersionSettings
from webbuilder.builder.website.built_website import BuiltWebsite


def _website(tmp_path: Path, name: str = "demo") -> WebsiteSettings:
    """A website with an earlier version "1.5" and a latest version "1.6", published at https://example.org/<name>/docs/."""
    site_settings: str = f"site_name: {name}\nsite_url: https://example.org/{name}/docs/\nextra:\n  repository_url: x\n"
    settings_folder: Path = tmp_path.joinpath("settings", name)
    settings_folder.mkdir(parents=True)
    return WebsiteSettings(write_website(settings_folder, {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}, site_settings))


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
