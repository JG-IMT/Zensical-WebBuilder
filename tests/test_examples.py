"""Tests that the examples (the template and the demo websites) are valid websites."""

from pathlib import Path

import pytest

from webbuilder.openflexo.settings.website_settings import WebsiteSettings

EXAMPLES_FOLDER: Path = Path(__file__).resolve().parents[1].joinpath("examples")
DEMO_WEBSITES_FOLDER: Path = EXAMPLES_FOLDER.joinpath("demo", "components", "websites")
SETTINGS_FILES: list[Path] = [EXAMPLES_FOLDER.joinpath("website_settings.yml")] + sorted(DEMO_WEBSITES_FOLDER.glob("*/website_settings.yml"))


@pytest.mark.parametrize("settings_file", SETTINGS_FILES, ids=lambda settings_file: settings_file.parent.name)
def test_example_is_a_valid_website(settings_file: Path) -> None:
    WebsiteSettings(settings_file)
