"""
Where the files shared by every website are: shared/zensical/ holds what Zensical reads (the default settings,
the HTML templates of the theme), shared/openflexo/ what gives the websites the look of OpenFlexo.
"""

from pathlib import Path

SHARED_FOLDER: Path = Path(__file__).resolve().parents[3].joinpath("shared")
SHARED_ZENSICAL_FOLDER: Path = SHARED_FOLDER.joinpath("zensical")
SHARED_OPENFLEXO_FOLDER: Path = SHARED_FOLDER.joinpath("openflexo")

SHARED_DEFAULT_SETTINGS_FILE: Path = SHARED_ZENSICAL_FOLDER.joinpath("default_settings.yml")
SHARED_HTML_TEMPLATES_FOLDER: Path = SHARED_ZENSICAL_FOLDER.joinpath("html_templates")
SHARED_STYLE_AND_ICON_FOLDER: Path = SHARED_OPENFLEXO_FOLDER.joinpath("style_and_icon")
