"""
This class builds the site of one version with Zensical, and reads the search index that Zensical writes.

ZensicalSiteGenerator has ZensicalConfig write the config file Zensical reads, then runs Zensical on it. It is the
only implementation of SiteGeneratorInterface, and main.py is the only place that creates it.

Used at step 4 (build the HTML of a version), and at step 6 (read the search index of a site).
"""

import os
import subprocess
import sys
from pathlib import Path

from webbuilder.common.openflexo_interfaces import SearchIndexInterface, SiteGeneratorInterface
from webbuilder.zensical.zensical_config import ZensicalConfig
from webbuilder.zensical.zensical_search_index import ZensicalSearchIndex

ZENSICAL_CONFIG_FILE_NAME: str = "zensical_config.yml"
ZENSICAL_SEARCH_INDEX_FILE_NAME: str = "search.json"  # written by Zensical in each site, read by the search of its pages


class ZensicalSiteGenerator(SiteGeneratorInterface):
    """This class builds the sites with Zensical."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, templates_folder: Path) -> None:
        """This constructor sets the folder of the HTML templates that override those of the theme."""
        self._templates_folder: Path = templates_folder


    # -- Public: SiteGeneratorInterface --------------------------------------------------------------

    def build_site(
        self,
        settings: dict,
        site_url: str,
        pages_folder: Path,
        site_folder: Path,
        work_folder: Path,
        side_menu: list | None,
        template_values: dict,
    ) -> bool:
        """This method writes the config of Zensical in the work folder, then runs Zensical, and returns False if it fails."""
        config_file: Path = work_folder.joinpath(ZENSICAL_CONFIG_FILE_NAME)
        ZensicalConfig(config_file).write(
            base_settings=settings,
            site_url=site_url,
            docs_dir=Path(os.path.relpath(pages_folder, work_folder)).as_posix(),  # relative to the config file
            site_dir=Path(os.path.relpath(site_folder, work_folder)).as_posix(),
            templates_folder=self._templates_folder,
            nav=side_menu,
            extra=template_values,
        )
        return self._run_zensical(config_file)


    def get_search_index_file_name(self) -> str:
        """This method returns the name of the search file that Zensical writes in each site."""
        return ZENSICAL_SEARCH_INDEX_FILE_NAME


    def read_search_index(self, file: Path) -> SearchIndexInterface:
        """This method reads the search index of a site from its file."""
        return ZensicalSearchIndex.read(file)


    # -- Private: zensical ---------------------------------------------------------------------------

    @staticmethod
    def _run_zensical(config_file: Path) -> bool:
        """This method runs `zensical build` on the config file, with the Zensical installed for the Python running the tool."""
        zensical_result: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, "-m", "zensical", "build", "--clean", "-f", str(config_file)]
        )
        return zensical_result.returncode == 0
