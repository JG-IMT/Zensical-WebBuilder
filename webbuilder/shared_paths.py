"""
Where the files shared by every website are: the default settings, the style and icon, the HTML templates.
"""

from pathlib import Path

SHARED_FOLDER: Path = Path(__file__).resolve().parents[1].joinpath("shared")
SHARED_DEFAULT_SETTINGS_FILE: Path = SHARED_FOLDER.joinpath("default_settings.yml")
SHARED_STYLE_AND_ICON_FOLDER: Path = SHARED_FOLDER.joinpath("style_and_icon")
SHARED_HTML_TEMPLATES_FOLDER: Path = SHARED_FOLDER.joinpath("html_templates")
