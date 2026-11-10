"""Tests that the HTML templates only read what the builder or the settings of a website give them."""

import re
from pathlib import Path

import pytest
from webbuilder.builder.config.shared_config import SHARED_HTML_TEMPLATES_FOLDER
from webbuilder.builder.website.website_settings import WebsiteSettings

from tests.test_examples import SETTINGS_FILES
from webbuilder.builder.version.version_builder import template_values_of
from webbuilder.builder.version.version_settings import VersionList

EXTRA_KEY: re.Pattern = re.compile(r"config\.extra\.(\w+)")


def _extra_keys_read_by_templates() -> set[str]:
    template_texts: list[str] = [file.read_text(encoding="utf-8") for file in SHARED_HTML_TEMPLATES_FOLDER.rglob("*.html")]
    return {key for text in template_texts for key in EXTRA_KEY.findall(text)}


@pytest.mark.parametrize("settings_file", SETTINGS_FILES, ids=lambda settings_file: settings_file.parent.name)
def test_every_extra_key_read_by_the_templates_is_given(settings_file: Path) -> None:
    website: WebsiteSettings = WebsiteSettings(settings_file)
    website_version_list: VersionList = website.get_website_version_list()
    given_keys: set[str] = set(website.get_zensical_settings()["extra"]) | set(
        template_values_of(website_version_list.get_latest_version(), website_version_list)
    )

    assert _extra_keys_read_by_templates() <= given_keys


def test_every_value_given_by_the_builder_is_read_by_a_template() -> None:
    website: WebsiteSettings = WebsiteSettings(SETTINGS_FILES[0])
    website_version_list: VersionList = website.get_website_version_list()
    template_values: dict = template_values_of(website_version_list.get_latest_version(), website_version_list)

    assert set(template_values) <= _extra_keys_read_by_templates()
