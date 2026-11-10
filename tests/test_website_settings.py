"""Tests of the reading of a website: its website_settings.yml and its version files in versions/."""

from pathlib import Path

import pytest

from tests.website_files import LATEST_VERSION, OLD_VERSION, SITE_SETTINGS, write_website
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.builder.website.website_versions import WebsiteVersions


def test_reads_the_versions_from_their_files(tmp_path: Path) -> None:
    website_settings: WebsiteSettings = WebsiteSettings(write_website(tmp_path, {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}))

    website_versions: WebsiteVersions = website_settings.get_website_versions()
    assert [version.get_name() for version in website_versions.get_all_versions()] == ["1.5", "1.6"]
    assert website_versions.get_latest_version().get_name() == "1.6"
    assert website_versions.get_latest_version().get_side_menu() == ["index.md"]
    assert website_versions.get_earlier_versions()[0].get_git_ref() == "1.5"
    assert website_versions.get_earlier_versions()[0].get_documentation_sources() == [{"source": "docs", "destination": "."}]
    assert website_settings.get_repository_url() == "https://example.org/demo.git"


def test_lists_the_versions_in_alphabetical_order(tmp_path: Path) -> None:
    website_settings: WebsiteSettings = WebsiteSettings(write_website(tmp_path, {"2.0": LATEST_VERSION, "1.5": OLD_VERSION}))

    names: list[str] = [version.get_name() for version in website_settings.get_website_versions().get_all_versions()]
    assert names == ["1.5", "2.0"]


def test_puts_the_latest_version_in_the_latest_folder_and_the_others_in_their_folder(tmp_path: Path) -> None:
    website_settings: WebsiteSettings = WebsiteSettings(write_website(tmp_path, {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}))

    website_versions: WebsiteVersions = website_settings.get_website_versions()
    assert website_versions.folder_in_website_of(website_versions.get_latest_version()) == "latest"
    assert website_versions.site_url_of(website_versions.get_latest_version()) == "https://example.org/demo/docs/latest/"
    assert website_versions.site_url_of(website_versions.get_earlier_versions()[0]) == "https://example.org/demo/docs/1.5/"


def test_stops_on_an_earlier_version_named_latest(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="only the latest version may be named 'latest'"):
        WebsiteSettings(write_website(tmp_path, {"latest": OLD_VERSION, "1.6": LATEST_VERSION}))


def test_stops_without_version_file(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="no version file"):
        WebsiteSettings(write_website(tmp_path, {}))


def test_stops_without_exactly_one_latest_version(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="exactly one version"):
        WebsiteSettings(write_website(tmp_path, {"1.5": OLD_VERSION}))


def test_stops_on_unknown_key_in_a_version(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match=r"1\.6\.yml.*unknown key"):  # the error names the file
        WebsiteSettings(write_website(tmp_path, {"1.6": LATEST_VERSION + "colour: red\n"}))


def test_stops_on_invalid_version_name(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="may only contain"):
        WebsiteSettings(write_website(tmp_path, {"my version": LATEST_VERSION}))


def test_stops_without_documentation_sources(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="documentation_sources"):
        WebsiteSettings(write_website(tmp_path, {"1.6": 'git_ref: "1.6"\nis_latest: true\n'}))


def test_stops_on_navigation_in_site_settings(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="would apply to every version"):
        WebsiteSettings(write_website(tmp_path, {"1.6": LATEST_VERSION}, SITE_SETTINGS + "nav: [index.md]\n"))
