"""
This class decides where a URL starting with "/" must point once the Markdown pages are in the website.

Such a URL leads to the root of the domain, not to the root of the website, so it needs fixing. The class knows the
folder holding the pages of the website and the homepage URL path, nothing about how the pages are read or written.

Used at step 3 (prepare the pages of a version), by UrlRewriter, once per URL.
"""

import posixpath
import re
from pathlib import Path
from urllib.parse import unquote


class UrlResolver:
    """This class decides where a URL starting with "/" must point."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, pages_folder: Path, homepage_url_path: str = "") -> None:
        """This constructor sets the folder of the pages and the homepage URL path of the project (empty if it has none)."""
        self._pages_folder: Path = pages_folder
        self._homepage_url_path: str = homepage_url_path

        self._reported_guesses: set[tuple[Path, str]] = set()  # one warning per guessed URL and per page


    # -- Public: entry point -------------------------------------------------------------------------

    def resolve_url(self, url_without_first_slash: str, page_file: Path) -> str:
        """
        This method returns the URL as it must be written in the page:
          1. the target is in the website: the URL becomes relative to the page
          2. the URL already starts with the homepage URL path (/my_project/javadoc/...), or there is none: unchanged
          3. otherwise the homepage URL path is put in front (/javadoc/... becomes /my_project/javadoc/...),
             and a warning names the page and the URL, once
        """
        if self._target_is_in_website(url_without_first_slash):
            return self._relative_to_page(url_without_first_slash, page_file)
        if not self._homepage_url_path or self._starts_with_homepage_url_path(url_without_first_slash):
            return "/" + url_without_first_slash
        return self._guess_with_homepage_url_path(url_without_first_slash, page_file)


    # -- Private: the three cases --------------------------------------------------------------------

    def _target_is_in_website(self, url_without_first_slash: str) -> bool:
        """This method tells whether the URL points to a file of the pages folder, ignoring its '#' and '?' parts."""
        url_without_fragment_or_query: str = re.split(r"[#?]", url_without_first_slash)[0]
        target_path: str = unquote(url_without_fragment_or_query)  # "my%20image.png" is the file "my image.png"
        return self._pages_folder.joinpath(target_path).exists()


    def _relative_to_page(self, url_without_first_slash: str, page_file: Path) -> str:
        """This method returns the path from the folder of the page to the target of the URL."""
        page_folder: str = page_file.parent.relative_to(self._pages_folder).as_posix()
        return posixpath.relpath(url_without_first_slash, start=page_folder)


    def _starts_with_homepage_url_path(self, url_without_first_slash: str) -> bool:
        """This method tells whether the URL already starts with the homepage URL path."""
        return url_without_first_slash.startswith(self._homepage_url_path + "/")


    def _guess_with_homepage_url_path(self, url_without_first_slash: str, page_file: Path) -> str:
        """This method puts the homepage URL path in front of the URL, and warns about this guess."""
        url_with_homepage_url_path: str = f"/{self._homepage_url_path}/{url_without_first_slash}"
        self._report_guess_once(url_without_first_slash, url_with_homepage_url_path, page_file)
        return url_with_homepage_url_path


    # -- Private: warning ----------------------------------------------------------------------------

    def _report_guess_once(self, url_without_first_slash: str, guessed_url: str, page_file: Path) -> None:
        """This method prints a warning naming the page and the URL, only the first time this URL is guessed in this page."""
        guess: tuple[Path, str] = (page_file, url_without_first_slash)
        if guess in self._reported_guesses:
            return
        self._reported_guesses.add(guess)

        page_path_in_website: str = page_file.relative_to(self._pages_folder).as_posix()
        original_url: str = "/" + url_without_first_slash
        print(f"Warning: {page_path_in_website}: {original_url} treated as {guessed_url}")
