"""These constants and functions write a fake website, made of its settings file and its version files, in a folder of the tests."""

from pathlib import Path

LATEST_VERSION_NAME: str = "1.6"
# website_settings.yml of the fake website: latest version "1.6", published at https://example.org/demo/docs/.
SITE_SETTINGS: str = f"""
site_name: Demo
site_url: https://example.org/demo/docs/
extra:
  repository_url: https://example.org/demo.git
  latest_version: "{LATEST_VERSION_NAME}"
"""
# Version file of the earlier version "1.5".
OLD_VERSION: str = """
git_ref: "1.5"
documentation_sources:
  - {source: docs, destination: .}
"""
# Version file of the latest version "1.6", with a menu.
LATEST_VERSION: str = """
git_ref: "1.6"
side_menu: [index.md]
documentation_sources:
  - {source: docs, destination: .}
"""


def site_settings_with_latest(latest_version: str) -> str:
    """This function returns SITE_SETTINGS with another latest version."""
    return SITE_SETTINGS.replace(f'"{LATEST_VERSION_NAME}"', f'"{latest_version}"')


def named_site_settings(name: str, latest_version: str) -> str:
    """This function returns the settings of a website called name, published at https://example.org/<name>/docs/."""
    return f"""
site_name: {name.upper()}
site_url: https://example.org/{name}/docs/
extra:
  repository_url: x
  latest_version: "{latest_version}"
"""


def write_website(folder: Path, versions: dict[str, str], site_settings: str = SITE_SETTINGS) -> Path:
    """This function writes website_settings.yml and one file per version in a folder, and returns website_settings.yml."""
    settings_file: Path = folder.joinpath("website_settings.yml")
    settings_file.write_text(site_settings, encoding="utf-8")
    for name, content in versions.items():
        version_file: Path = folder.joinpath("versions", f"{name}.yml")
        version_file.parent.mkdir(exist_ok=True)
        version_file.write_text(content, encoding="utf-8")
    return settings_file
