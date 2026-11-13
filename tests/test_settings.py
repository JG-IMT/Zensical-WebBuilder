"""Tests of the reading of the settings: website_settings.yml, the version files in versions/, and the examples."""

from pathlib import Path

import pytest

from tests.fake_website import LATEST_VERSION, OLD_VERSION, SITE_SETTINGS, site_settings_with_latest, write_website
from webbuilder.builder.version.version_settings import VersionList, VersionSettings
from webbuilder.builder.website.website_settings import WebsiteSettings

EXAMPLES_FOLDER: Path = Path(__file__).resolve().parents[1].joinpath("examples")
DEMO_WEBSITES_FOLDER: Path = EXAMPLES_FOLDER.joinpath("demo", "components", "websites")
SETTINGS_FILES: list[Path] = [EXAMPLES_FOLDER.joinpath("website_settings.yml")] + sorted(DEMO_WEBSITES_FOLDER.glob("*/website_settings.yml"))


# -- What is read ------------------------------------------------------------------------------------

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
    website: WebsiteSettings = WebsiteSettings(write_website(tmp_path, {"2.0": LATEST_VERSION, "1.5": OLD_VERSION}, site_settings_with_latest("2.0")))

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


# -- What stops the build ----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "versions, website_settings, message",
    [
        pytest.param({"latest": OLD_VERSION, "1.6": LATEST_VERSION}, SITE_SETTINGS, "no version may be named 'latest'", id="version named latest"),
        pytest.param({}, SITE_SETTINGS, "no version file", id="no version file"),
        pytest.param({"1.5": OLD_VERSION}, SITE_SETTINGS, r"extra\.latest_version '1\.6' is not a version.*found: 1\.5", id="unknown latest version"),
        pytest.param({"1.6": LATEST_VERSION}, SITE_SETTINGS.replace('  latest_version: "1.6"\n', ""), "no 'latest_version' under 'extra:'",
                     id="no latest version"),
        pytest.param({"1.6": LATEST_VERSION}, SITE_SETTINGS.replace('"1.6"', "1.6"), "must be text", id="latest version not text"),
        pytest.param({"1.6": LATEST_VERSION + "is_latest: true\n"}, SITE_SETTINGS, "is_latest is replaced by extra.latest_version",
                     id="former is_latest key"),
        pytest.param({"1.6": LATEST_VERSION + "colour: red\n"}, SITE_SETTINGS, r"1\.6\.yml.*unknown key", id="unknown key"),
        pytest.param({"my version": LATEST_VERSION}, SITE_SETTINGS, "may only contain", id="invalid version name"),
        pytest.param({"1.6": 'git_ref: "1.6"\n'}, SITE_SETTINGS, "documentation_sources", id="no documentation sources"),
        pytest.param({"1.6": LATEST_VERSION}, SITE_SETTINGS + "nav: [index.md]\n", "would apply to every version", id="nav in website settings"),
    ],
)
def test_stops_on_wrong_settings(tmp_path: Path, versions: dict[str, str], website_settings: str, message: str) -> None:
    with pytest.raises(SystemExit, match=message):
        WebsiteSettings(write_website(tmp_path, versions, website_settings))


# -- The examples ------------------------------------------------------------------------------------

@pytest.mark.parametrize("settings_file", SETTINGS_FILES, ids=lambda settings_file: settings_file.parent.name)
def test_example_is_a_valid_website(settings_file: Path) -> None:
    WebsiteSettings(settings_file)
