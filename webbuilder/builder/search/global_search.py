"""
This class gives the search of each website the pages of all the websites.

The site generator writes one search index per version, which the search of the pages reads. The index of the latest
version of each website is replaced by the merge of the indexes of the latest versions of all the websites.

The pages of a website alone are kept next to its merged index, to merge again after another website is built.

Used at step 6 (merge the search), once all the websites are built.
"""

from pathlib import Path

from webbuilder.builder.website.website_settings import WebsiteSettings
from webbuilder.builder.website.built_website import BuiltWebsite

from webbuilder.common.openflexo_interfaces import SearchIndexInterface, SiteGeneratorInterface


class GlobalSearch:
    """This class replaces the search index of each built website by the merge of the indexes of all the built websites."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(
        self, built_websites_folder: Path, site_generator: SiteGeneratorInterface, website_search_index_file_name: str
    ) -> None:
        """This constructor sets where the websites are built, the site generator and the file name of each website's own pages."""
        self._built_websites_folder: Path = built_websites_folder  # holds the websites, one folder per address
        self._site_generator: SiteGeneratorInterface = site_generator  # tells the index file and reads it
        self._website_search_index_file_name: str = website_search_index_file_name  # the pages of the website alone


    # -- Public: entry point -------------------------------------------------------------------------

    def merge(self, website_by_name: dict[str, WebsiteSettings]) -> None:
        """This method writes the merged index in each built website, and skips a website that is not built yet."""
        built_website_by_name: dict[str, BuiltWebsite] = self._keep_built_websites(website_by_name)

        website_index_by_website_name: dict[str, SearchIndexInterface] = {
            website_name: self._read_website_index(built_website) for website_name, built_website in built_website_by_name.items()
        }

        for website_name, built_website in built_website_by_name.items():
            merged_index: SearchIndexInterface = self._merge_indexes(website_name, built_website_by_name, website_index_by_website_name)
            merged_index.write(self._find_search_index_file(built_website))
            print(f"Search: {website_name} searches {len(merged_index.get_items())} pages of {len(website_index_by_website_name)} websites")


    # -- Private: reading ----------------------------------------------------------------------------

    def _find_search_index_file(self, built_website: BuiltWebsite) -> Path:
        """This method returns the search index file of the latest version of a built website."""
        return built_website.get_search_index_file(self._site_generator.get_search_index_file_name())


    def _keep_built_websites(self, website_by_name: dict[str, WebsiteSettings]) -> dict[str, BuiltWebsite]:
        """This method returns the websites whose index exists in the build folder."""
        built_website_by_name: dict[str, BuiltWebsite] = {}
        for website_name, website in website_by_name.items():
            built_website: BuiltWebsite = BuiltWebsite(self._built_websites_folder, website)
            if self._find_search_index_file(built_website).is_file():
                built_website_by_name[website_name] = built_website
            else:
                print(f"Search: {website_name} is not built, skipped")
        return built_website_by_name


    def _read_website_index(self, built_website: BuiltWebsite) -> SearchIndexInterface:
        """
        This method returns the index with the pages of the website alone. A website just built has none yet: its
        index is the one the site generator wrote, which is kept before being replaced by the merged one.
        """
        index_file: Path = self._find_search_index_file(built_website)
        website_index_file: Path = index_file.with_name(self._website_search_index_file_name)
        if not website_index_file.is_file():
            website_index_file.write_text(index_file.read_text(encoding="utf-8"), encoding="utf-8")
        return self._site_generator.read_search_index(website_index_file)


    # -- Private: merging ----------------------------------------------------------------------------

    def _merge_indexes(
        self,
        website_name: str,
        built_website_by_name: dict[str, BuiltWebsite],
        website_index_by_website_name: dict[str, SearchIndexInterface],
    ) -> SearchIndexInterface:
        """This method returns the index of the website, completed by the pages of every other website."""
        other_websites_items: list[dict] = []
        for other_name, other_built_website in built_website_by_name.items():
            if other_name != website_name:
                other_websites_items += self._items_seen_from(
                    built_website_by_name[website_name], other_built_website, website_index_by_website_name[other_name]
                )
        return website_index_by_website_name[website_name].with_added_items(other_websites_items)


    @staticmethod
    def _items_seen_from(from_website: BuiltWebsite, to_website: BuiltWebsite, to_index: SearchIndexInterface) -> list[dict]:
        """This method returns the pages of a website for another one's search: relative paths, website name in the title."""
        path_to_site: str = from_website.get_path_to_latest_version_of(to_website)
        return to_index.get_items_prefixed(f"{path_to_site}/", f"{to_website.get_site_name()} · ")
