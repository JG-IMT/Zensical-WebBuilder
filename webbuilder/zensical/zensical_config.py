"""
This class writes the config file that Zensical reads to build the site of one version.

The config is the settings of the website, completed with what is specific to the version: its address, the folder of
its pages, the folder of its site, the HTML templates, its menu and the values the templates read. It only knows the
options of Zensical; what the values mean is decided by the caller.

Used at step 4 (build the HTML of a version), by ZensicalSiteGenerator.
"""

import copy
import os
from pathlib import Path

import yaml


class ZensicalConfig:
    """This class writes the config file of Zensical for one version of a website."""

    # == Public ====================================================================================

    # -- Initialization ----------------------------------------------------------------------------

    def __init__(self, config_file: Path) -> None:
        """This constructor sets the file where the config is written."""
        self._config_file: Path = config_file


    # -- Entry point -------------------------------------------------------------------------------

    def write(
        self,
        base_settings: dict,
        site_url: str,
        docs_dir: str,
        site_dir: str,
        templates_folder: Path,
        nav: list | None,
        extra: dict,
    ) -> Path:
        """
        This method writes the base settings completed with: the address of the site (site_url), the folder Zensical
        reads the pages from (docs_dir) and the one it writes the site in (site_dir) - both relative to the config
        file -, the folder of the HTML templates, the menu (nav, if any) and the keys added to 'extra'.
        It returns the config file.
        """
        config: dict = copy.deepcopy(base_settings)
        config["site_url"] = site_url
        config["docs_dir"] = docs_dir
        config["site_dir"] = site_dir
        config["theme"]["custom_dir"] = Path(os.path.relpath(templates_folder, self._config_file.parent)).as_posix()
        config.setdefault("extra", {}).update(extra)
        if nav:
            config["nav"] = nav

        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return self._config_file
