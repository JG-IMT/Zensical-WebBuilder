"""
Zensical as the tool that builds the sites: writes its config file, runs it, and reads its search index.
"""

import os
from pathlib import Path

from webbuilder.common.search_index_interface import SearchIndexInterface
from webbuilder.common.site_generator_interface import SiteGeneratorInterface
from webbuilder.zensical.zensical_build import ZensicalBuild
from webbuilder.zensical.zensical_config import ZensicalConfig
from webbuilder.zensical.zensical_search_index import ZensicalSearchIndex

ZENSICAL_CONFIG_FILE_NAME: str = "zensical_config.yml"
ZENSICAL_SEARCH_INDEX_FILE_NAME: str = "search.json"  # written by Zensical in each site, read by the search of its pages


class ZensicalSiteGenerator(SiteGeneratorInterface):
    """Builds the sites with Zensical."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, templates_folder: Path) -> None:
        self._templates_folder: Path = templates_folder  # the HTML templates overriding those of the theme


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
        """Writes the config of Zensical in the work folder, then runs Zensical. Returns False if it fails."""
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
        return ZensicalBuild(config_file).run()


    def get_search_index_file_name(self) -> str:
        return ZENSICAL_SEARCH_INDEX_FILE_NAME


    def read_search_index(self, file: Path) -> SearchIndexInterface:
        return ZensicalSearchIndex.read(file)
