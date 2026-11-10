"""Tests of the places of the files of a built website."""

from pathlib import Path

from tests.website_files import LATEST_VERSION, OLD_VERSION, write_website
from webbuilder.builder.settings.website import Website
from webbuilder.builder.website.built_website import BuiltWebsite


def _built_website(tmp_path: Path, name: str = "demo") -> BuiltWebsite:
    """A website with an earlier version "1.5" and a latest version "1.6", published at https://example.org/<name>/docs/."""
    site_settings: str = f"site_name: {name}\nsite_url: https://example.org/{name}/docs/\nextra:\n  repository_url: x\n"
    settings_folder: Path = tmp_path.joinpath("settings", name)
    settings_folder.mkdir(parents=True)
    website: Website = Website(write_website(settings_folder, {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}, site_settings))
    return BuiltWebsite(tmp_path.joinpath("build"), website)


def test_the_folder_of_the_website_is_named_after_its_site_url(tmp_path: Path) -> None:
    assert _built_website(tmp_path).get_folder() == tmp_path.joinpath("build", "demo", "docs")


def test_the_latest_version_is_in_latest_and_the_others_in_their_folder(tmp_path: Path) -> None:
    built_website: BuiltWebsite = _built_website(tmp_path)

    assert built_website.get_latest_version_folder() == built_website.get_folder().joinpath("latest")
    assert built_website.get_search_index_file("search.json") == built_website.get_folder().joinpath("latest", "search.json")


def test_the_path_to_another_website_goes_from_latest_to_latest(tmp_path: Path) -> None:
    assert _built_website(tmp_path, "a").get_path_to_latest_version_of(_built_website(tmp_path, "b")) == "../../../b/docs/latest"


def test_the_root_of_the_website_redirects_to_latest(tmp_path: Path) -> None:
    built_website: BuiltWebsite = _built_website(tmp_path)
    built_website.get_folder().mkdir(parents=True)

    built_website.write_redirection_to_latest_version()

    assert 'url=latest/"' in built_website.get_folder().joinpath("index.html").read_text(encoding="utf-8")
