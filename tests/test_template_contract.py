"""Tests that the HTML templates only read what the builder or the settings of a website give them."""

import re
from pathlib import Path

import pytest

from tests.test_examples import SETTINGS_FILES
from webbuilder.builder.building.version_build import template_values_of
from webbuilder.builder.settings.website_settings import WebsiteSettings
from webbuilder.builder.settings.website_version_catalog import WebsiteVersionCatalog
from webbuilder.builder.shared_paths import SHARED_HTML_TEMPLATES_FOLDER

EXTRA_KEY: re.Pattern = re.compile(r"config\.extra\.(\w+)")


def _extra_keys_read_by_templates() -> set[str]:
    template_texts: list[str] = [file.read_text(encoding="utf-8") for file in SHARED_HTML_TEMPLATES_FOLDER.rglob("*.html")]
    return {key for text in template_texts for key in EXTRA_KEY.findall(text)}


@pytest.mark.parametrize("settings_file", SETTINGS_FILES, ids=lambda settings_file: settings_file.parent.name)
def test_every_extra_key_read_by_the_templates_is_given(settings_file: Path) -> None:
    website_settings: WebsiteSettings = WebsiteSettings(settings_file)
    catalog: WebsiteVersionCatalog = website_settings.get_version_catalog()
    given_keys: set[str] = set(website_settings.get_zensical_settings()["extra"]) | set(
        template_values_of(catalog.get_latest_version(), catalog)
    )

    assert _extra_keys_read_by_templates() <= given_keys


def test_every_value_given_by_the_builder_is_read_by_a_template() -> None:
    website_settings: WebsiteSettings = WebsiteSettings(SETTINGS_FILES[0])
    catalog: WebsiteVersionCatalog = website_settings.get_version_catalog()

    assert set(template_values_of(catalog.get_latest_version(), catalog)) <= _extra_keys_read_by_templates()
