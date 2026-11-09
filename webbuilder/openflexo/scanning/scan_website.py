"""
Finds the websites to build: each sub-folder of the websites folder holding a website_settings.yml is one
website, named after its folder.
"""

from pathlib import Path


class ScanWebsite:
    """Scans the websites folder for the website_settings.yml of each website."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, websites_folder: Path, settings_file_name: str) -> None:
        self._websites_folder: Path = websites_folder
        self._settings_file_by_website_name: dict[str, Path] = {
            file.parent.name: file for file in sorted(websites_folder.glob(f"*/{settings_file_name}"))
        }


    # -- Public: get websites ------------------------------------------------------------------------

    def get_settings_files(self, selected_website_names: list[str]) -> dict[str, Path]:
        """
        The website_settings.yml of the selected websites, by website name; of every website if none is selected.
        Throws an error naming the first selected website that is not in the websites folder.
        """
        for website_name in selected_website_names:
            if website_name not in self._settings_file_by_website_name:
                raise SystemExit(
                    f"No website named {website_name} in {self._websites_folder} (found: {', '.join(self._settings_file_by_website_name)})"
                )
        if not selected_website_names:
            return dict(self._settings_file_by_website_name)
        return {name: self._settings_file_by_website_name[name] for name in selected_website_names}
