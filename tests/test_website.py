"""Tests of the reading of a website: its website_settings.yml and its version files in versions/."""

from pathlib import Path

import pytest
from webbuilder.builder.website.website_settings import WebsiteSettings

from tests.website_files import LATEST_VERSION, OLD_VERSION, SITE_SETTINGS, site_settings, write_website
from webbuilder.builder.version.version_settings import VersionSettings, VersionList


def test_reads_the_versions_from_their_files(tmp_path: Path) -> None:
    website: WebsiteSettings = WebsiteSettings(write_website(tmp_path, {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}))

    website_version_list: VersionList = website.get_website_version_list()
    assert [version.get_name() for version in website_version_list.get_all_versions()] == ["1.5", "1.6"]
    assert website_version_list.get_latest_version().get_name() == "1.6"
    assert website_version_list.get_latest_version().get_side_menu() == ["index.md"]
    assert website_version_list.get_earlier_versions()[0].get_git_ref() == "1.5"
    assert website_version_list.get_earlier_versions()[0].get_documentation_sources() == [{"source": "docs", "destination": "."}]
    assert website.get_repository_url() == "https://example.org/demo.git"


def test_lists_the_versions_in_alphabetical_order(tmp_path: Path) -> None:
    website: WebsiteSettings = WebsiteSettings(write_website(tmp_path, {"2.0": LATEST_VERSION, "1.5": OLD_VERSION}, site_settings("2.0")))

    names: list[str] = [version.get_name() for version in website.get_website_version_list().get_all_versions()]
    assert names == ["1.5", "2.0"]


def test_gives_each_version_its_own_folder_and_address(tmp_path: Path) -> None:
    website: WebsiteSettings = WebsiteSettings(write_website(tmp_path, {"1.5": OLD_VERSION, "1.6": LATEST_VERSION}))

    website_version_list: VersionList = website.get_website_version_list()
    latest_version: VersionSettings = website_version_list.get_latest_version()
    earlier_version: VersionSettings = website_version_list.get_earlier_versions()[0]
    assert website_version_list.folder_in_website_of(latest_version) == "1.6"
    assert website_version_list.site_url_of(latest_version) == "https://example.org/demo/docs/1.6/"
    assert website_version_list.site_url_of(earlier_version) == "https://example.org/demo/docs/1.5/"


def test_stops_on_a_version_named_latest(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="no version may be named 'latest'"):
        WebsiteSettings(write_website(tmp_path, {"latest": OLD_VERSION, "1.6": LATEST_VERSION}))


def test_stops_without_version_file(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="no version file"):
        WebsiteSettings(write_website(tmp_path, {}))


def test_stops_when_the_latest_version_is_not_a_version_of_the_website(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match=r"extra\.latest_version '1\.6' is not a version.*found: 1\.5"):
        WebsiteSettings(write_website(tmp_path, {"1.5": OLD_VERSION}))


def test_stops_without_the_latest_version_in_the_website_settings(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="no 'latest_version' under 'extra:'"):
        WebsiteSettings(write_website(tmp_path, {"1.6": LATEST_VERSION}, SITE_SETTINGS.replace('  latest_version: "1.6"\n', "")))


def test_stops_when_the_latest_version_is_not_text(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="must be text"):
        WebsiteSettings(write_website(tmp_path, {"1.6": LATEST_VERSION}, SITE_SETTINGS.replace('"1.6"', "1.6")))


def test_stops_on_the_former_is_latest_key_and_says_what_replaces_it(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="is_latest is replaced by extra.latest_version"):
        WebsiteSettings(write_website(tmp_path, {"1.6": LATEST_VERSION + "is_latest: true\n"}))


def test_stops_on_unknown_key_in_a_version(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match=r"1\.6\.yml.*unknown key"):  # the error names the file
        WebsiteSettings(write_website(tmp_path, {"1.6": LATEST_VERSION + "colour: red\n"}))


def test_stops_on_invalid_version_name(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="may only contain"):
        WebsiteSettings(write_website(tmp_path, {"my version": LATEST_VERSION}))


def test_stops_without_documentation_sources(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="documentation_sources"):
        WebsiteSettings(write_website(tmp_path, {"1.6": 'git_ref: "1.6"\n'}))


def test_stops_on_navigation_in_site_settings(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="would apply to every version"):
        WebsiteSettings(write_website(tmp_path, {"1.6": LATEST_VERSION}, SITE_SETTINGS + "nav: [index.md]\n"))
