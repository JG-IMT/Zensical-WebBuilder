"""
Gives the search of each website the pages of all the websites. The site generator writes one search index per website,
which the search of the pages reads: the index of each website is replaced by the merge of the indexes of
all the websites. A page of another website is reached with a relative path, so the websites must be
side by side in the build folder as they are on the server: one folder per website, named after its address.
The pages of a website alone are kept next to its merged index, to merge again after another website is built.
"""

import posixpath
from pathlib import Path

from webbuilder.builder.settings.website_settings import WebsiteSettings
from webbuilder.common.search_index_interface import SearchIndexInterface
from webbuilder.common.site_generator_interface import SiteGeneratorInterface


class SharedSearch:
    """Replaces the search index of each built website by the merge of the indexes of all the built websites."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self, built_websites_folder: Path, site_generator: SiteGeneratorInterface, website_search_index_file_name: str
    ) -> None:
        self._built_websites_folder: Path = built_websites_folder  # holds the websites, one folder per address
        self._site_generator: SiteGeneratorInterface = site_generator  # tells the index file and reads it
        self._website_search_index_file_name: str = website_search_index_file_name  # the pages of the website alone


    # -- Public: entry point -------------------------------------------------------------------------

    def merge(self, settings_by_website_name: dict[str, WebsiteSettings]) -> None:
        """Writes in each built website the merged index. A website that is not built yet is skipped."""
        built_settings_by_website_name: dict[str, WebsiteSettings] = self._keep_built_websites(settings_by_website_name)
        website_index_by_website_name: dict[str, SearchIndexInterface] = {
            website_name: self._read_website_index(website_settings) for website_name, website_settings in built_settings_by_website_name.items()
        }
        for website_name in built_settings_by_website_name:
            merged_index: SearchIndexInterface = self._merge_indexes(website_name, built_settings_by_website_name, website_index_by_website_name)
            merged_index.write(self._find_search_index_file(built_settings_by_website_name[website_name]))
            print(f"Search: {website_name} searches {len(merged_index.get_items())} pages of {len(website_index_by_website_name)} websites")


    # -- Private: reading ----------------------------------------------------------------------------

    def _find_search_index_file(self, website_settings: WebsiteSettings) -> Path:
        return self._built_websites_folder.joinpath(website_settings.get_site_url_path(), self._site_generator.get_search_index_file_name())


    def _keep_built_websites(self, settings_by_website_name: dict[str, WebsiteSettings]) -> dict[str, WebsiteSettings]:
        """The websites whose index exists in the build folder."""
        built_settings_by_website_name: dict[str, WebsiteSettings] = {}
        for website_name, website_settings in settings_by_website_name.items():
            if self._find_search_index_file(website_settings).is_file():
                built_settings_by_website_name[website_name] = website_settings
            else:
                print(f"Search: {website_name} is not built, skipped")
        return built_settings_by_website_name


    def _read_website_index(self, website_settings: WebsiteSettings) -> SearchIndexInterface:
        """
        The index with the pages of the website alone. A website just built has none yet: its index is the one
        the site generator wrote, which is kept before being replaced by the merged one.
        """
        index_file: Path = self._find_search_index_file(website_settings)
        website_index_file: Path = index_file.with_name(self._website_search_index_file_name)
        if not website_index_file.is_file():
            website_index_file.write_text(index_file.read_text(encoding="utf-8"), encoding="utf-8")
        return self._site_generator.read_search_index(website_index_file)


    # -- Private: merging ----------------------------------------------------------------------------

    def _merge_indexes(
        self,
        website_name: str,
        settings_by_website_name: dict[str, WebsiteSettings],
        website_index_by_website_name: dict[str, SearchIndexInterface],
    ) -> SearchIndexInterface:
        """The index of the website, completed by the pages of every other website."""
        other_websites_items: list[dict] = []
        for other_name, other_settings in settings_by_website_name.items():
            if other_name != website_name:
                other_websites_items += self._items_seen_from(
                    settings_by_website_name[website_name], other_settings, website_index_by_website_name[other_name]
                )
        return website_index_by_website_name[website_name].with_added_items(other_websites_items)


    @staticmethod
    def _items_seen_from(from_settings: WebsiteSettings, to_settings: WebsiteSettings, to_index: SearchIndexInterface) -> list[dict]:
        """The pages of a website for the search of another one: a relative path to the pages, the website in the title."""
        # "." stands for a website at the root of the server, whose path is empty
        path_to_site: str = posixpath.relpath(to_settings.get_site_url_path() or ".", start=from_settings.get_site_url_path() or ".")
        return to_index.get_items_prefixed(f"{path_to_site}/", f"{to_settings.get_site_name()} · ")
