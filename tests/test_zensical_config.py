"""Tests of the config file written for Zensical."""

from pathlib import Path

import yaml

from webbuilder.zensical.zensical_site_generator import ZensicalConfig

BASE_SETTINGS: dict = {"site_name": "Demo", "site_url": "https://example.org/", "theme": {"name": "material"}, "extra": {"a": 1}}


def _write(tmp_path: Path, nav: list | None) -> dict:
    config_file: Path = tmp_path.joinpath("work", "zensical_config.yml")
    ZensicalConfig(config_file).write(
        BASE_SETTINGS, "https://example.org/1.0/", "pages", "site", tmp_path.joinpath("templates"), nav, {"b": 2}
    )
    return yaml.safe_load(config_file.read_text(encoding="utf-8"))


def test_completes_the_base_settings_for_one_site(tmp_path: Path) -> None:
    config: dict = _write(tmp_path, ["index.md"])

    assert config["site_name"] == "Demo"
    assert config["site_url"] == "https://example.org/1.0/"
    assert (config["docs_dir"], config["site_dir"]) == ("pages", "site")
    assert config["theme"] == {"name": "material", "custom_dir": "../templates"}  # relative to the config file
    assert config["extra"] == {"a": 1, "b": 2}
    assert config["nav"] == ["index.md"]


def test_has_no_menu_without_nav(tmp_path: Path) -> None:
    assert "nav" not in _write(tmp_path, None)


def test_leaves_the_base_settings_unchanged(tmp_path: Path) -> None:
    _write(tmp_path, None)

    assert BASE_SETTINGS["theme"] == {"name": "material"}
    assert BASE_SETTINGS["extra"] == {"a": 1}
