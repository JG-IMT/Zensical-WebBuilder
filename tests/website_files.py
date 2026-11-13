"""The files of a website written in a folder, shared by the tests."""

from pathlib import Path

LATEST_VERSION_NAME: str = "1.6"
SITE_SETTINGS: str = f"""
site_name: Demo
site_url: https://example.org/demo/docs/
extra:
  repository_url: https://example.org/demo.git
  latest_version: "{LATEST_VERSION_NAME}"
"""
OLD_VERSION: str = """
git_ref: "1.5"
documentation_sources:
  - {source: docs, destination: .}
"""
LATEST_VERSION: str = """
git_ref: "1.6"
side_menu: [index.md]
documentation_sources:
  - {source: docs, destination: .}
"""


def site_settings(latest_version: str) -> str:
    """The settings of the website of SITE_SETTINGS, with another latest version."""
    return SITE_SETTINGS.replace(f'"{LATEST_VERSION_NAME}"', f'"{latest_version}"')


def write_website(folder: Path, versions: dict[str, str], site_settings: str = SITE_SETTINGS) -> Path:
    """Writes website_settings.yml and one file per version in the folder. Returns website_settings.yml."""
    settings_file: Path = folder.joinpath("website_settings.yml")
    settings_file.write_text(site_settings, encoding="utf-8")
    for name, content in versions.items():
        version_file: Path = folder.joinpath("versions", f"{name}.yml")
        version_file.parent.mkdir(exist_ok=True)
        version_file.write_text(content, encoding="utf-8")
    return settings_file
