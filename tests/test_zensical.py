"""Tests of what talks to Zensical: its config file, its site generator (without running Zensical), and the HTML templates."""

import re
from pathlib import Path

import pytest
import yaml

from tests.test_settings import SETTINGS_FILES
from webbuilder.builder.paths.shared_paths import SHARED_HTML_TEMPLATES_FOLDER
from webbuilder.builder.version.version_builder import template_values_of
from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.common.openflexo_interfaces import SearchIndexInterface
from webbuilder.zensical.zensical_config import ZensicalConfig
from webbuilder.zensical.zensical_site_generator import ZensicalSiteGenerator

BASE_SETTINGS: dict = {"site_name": "Demo", "site_url": "https://example.org/", "theme": {"name": "material"}, "extra": {"a": 1}}
EXTRA_KEY: re.Pattern = re.compile(r"config\.extra\.(\w+)")


# -- The config file ---------------------------------------------------------------------------------

def _write_config(tmp_path: Path, nav: list | None) -> dict:
    config_file: Path = tmp_path.joinpath("work", "zensical_config.yml")
    ZensicalConfig(config_file).write(
        BASE_SETTINGS, "https://example.org/1.0/", "pages", "site", tmp_path.joinpath("templates"), nav, {"b": 2}
    )
    return yaml.safe_load(config_file.read_text(encoding="utf-8"))


def test_completes_the_base_settings_for_one_site(tmp_path: Path) -> None:
    config: dict = _write_config(tmp_path, ["index.md"])

    assert config["site_name"] == "Demo"
    assert config["site_url"] == "https://example.org/1.0/"
    assert (config["docs_dir"], config["site_dir"]) == ("pages", "site")
    assert config["theme"] == {"name": "material", "custom_dir": "../templates"}  # relative to the config file
    assert config["extra"] == {"a": 1, "b": 2}
    assert config["nav"] == ["index.md"]


def test_has_no_menu_without_nav(tmp_path: Path) -> None:
    assert "nav" not in _write_config(tmp_path, None)


def test_leaves_the_base_settings_unchanged(tmp_path: Path) -> None:
    _write_config(tmp_path, None)

    assert BASE_SETTINGS["theme"] == {"name": "material"}
    assert BASE_SETTINGS["extra"] == {"a": 1}


# -- The site generator ------------------------------------------------------------------------------

def _build_site(generator: ZensicalSiteGenerator, work_folder: Path) -> bool:
    return generator.build_site(
        settings={"site_name": "Demo", "theme": {"name": "material"}},
        site_url="https://example.org/1.0/",
        pages_folder=work_folder.joinpath("pages"),
        site_folder=work_folder.joinpath("site"),
        work_folder=work_folder,
        side_menu=["index.md"],
        template_values={"displayed_version": "1.0"},
    )


def _fake_zensical(monkeypatch: pytest.MonkeyPatch, succeeds: bool) -> None:
    """Zensical is not run: its run succeeds or fails as asked."""
    monkeypatch.setattr(ZensicalSiteGenerator, "_run_zensical", staticmethod(lambda config_file: succeeds))


def test_writes_the_config_of_zensical_next_to_the_work_folder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _fake_zensical(monkeypatch, succeeds=True)

    assert _build_site(ZensicalSiteGenerator(tmp_path.joinpath("templates")), tmp_path.joinpath("work")) is True

    config: dict = yaml.safe_load(tmp_path.joinpath("work", "zensical_config.yml").read_text(encoding="utf-8"))
    assert (config["docs_dir"], config["site_dir"]) == ("pages", "site")  # relative to the config file
    assert config["theme"]["custom_dir"] == "../templates"
    assert (config["site_url"], config["nav"], config["extra"]) == ("https://example.org/1.0/", ["index.md"], {"displayed_version": "1.0"})


def test_reports_a_failure_of_zensical(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _fake_zensical(monkeypatch, succeeds=False)

    assert _build_site(ZensicalSiteGenerator(tmp_path), tmp_path.joinpath("work")) is False


def test_reads_the_search_index_zensical_writes(tmp_path: Path) -> None:
    generator: ZensicalSiteGenerator = ZensicalSiteGenerator(tmp_path)
    index_file: Path = tmp_path.joinpath(generator.get_search_index_file_name())
    index_file.write_text('{"config": {}, "items": [{"location": "a/", "title": "A"}]}', encoding="utf-8")

    index: SearchIndexInterface = generator.read_search_index(index_file)

    assert generator.get_search_index_file_name() == "search.json"
    assert index.get_items() == [{"location": "a/", "title": "A"}]


# -- The HTML templates ------------------------------------------------------------------------------

def _extra_keys_read_by_templates() -> set[str]:
    template_texts: list[str] = [file.read_text(encoding="utf-8") for file in SHARED_HTML_TEMPLATES_FOLDER.rglob("*.html")]
    return {key for text in template_texts for key in EXTRA_KEY.findall(text)}


@pytest.mark.parametrize("settings_file", SETTINGS_FILES, ids=lambda settings_file: settings_file.parent.name)
def test_every_extra_key_read_by_the_templates_is_given(settings_file: Path) -> None:
    website: WebsiteSettings = WebsiteSettings(settings_file)
    latest_version = website.get_website_version_list().get_latest_version()
    given_keys: set[str] = set(website.get_zensical_settings()["extra"]) | set(template_values_of(latest_version))

    assert _extra_keys_read_by_templates() <= given_keys


def test_every_value_given_by_the_builder_is_read_by_a_template() -> None:
    website: WebsiteSettings = WebsiteSettings(SETTINGS_FILES[0])
    template_values: dict = template_values_of(website.get_website_version_list().get_latest_version())

    assert set(template_values) <= _extra_keys_read_by_templates()
