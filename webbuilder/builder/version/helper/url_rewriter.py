"""
This class rewrites, in the copies of the Markdown pages, the URLs that start with "/".

It finds each URL, leaves the fenced code blocks alone, asks a UrlResolver where the URL must point, and writes the
page back only when a URL changed. Line endings and the BOM are kept. The sources are never changed, only the copies
it is given.

Used at step 3 (prepare the pages of a version), once per version.
"""

import re
from pathlib import Path

from webbuilder.builder.version.helper.url_resolver import UrlResolver

URL_STARTING_WITH_SLASH: re.Pattern = re.compile(r"""
    (?P<opening> \]\( | \b(?:src|href)=" )
    /(?!/)
    (?P<url_without_first_slash> [^)"\s]+ )
""", re.VERBOSE)
CODE_BLOCK_MARKER: re.Pattern = re.compile(r"^\s*(```|~~~)")


class UrlRewriter:
    """This class rewrites the URLs starting with "/" in Markdown page files, as decided by a UrlResolver."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, url_resolver: UrlResolver) -> None:
        """This constructor sets the UrlResolver that decides where each URL must point."""
        self._url_resolver: UrlResolver = url_resolver


    # -- Public: entry point -------------------------------------------------------------------------

    def rewrite_urls_in(self, page_files: list[Path]) -> None:
        """
        This method rewrites the URLs starting with "/" of each page file (links, images, src and href
        attributes). A page that is not a UTF-8 file stops the build, naming the page.
        """
        for page_file in page_files:
            self._rewrite_urls_in_file(page_file)


    # -- Private: one page file ----------------------------------------------------------------------

    def _rewrite_urls_in_file(self, page_file: Path) -> None:
        """This method rewrites the URLs of one page file, and writes the file back only if a URL changed."""
        page_text: str = self._read_page_text(page_file)
        page_text_with_rewritten_urls: str = self._page_text_with_rewritten_urls(page_text, page_file)
        if page_text_with_rewritten_urls != page_text:
            page_file.write_bytes(page_text_with_rewritten_urls.encode("utf-8"))


    @staticmethod
    def _read_page_text(page_file: Path) -> str:
        """This method returns the text of a page, and stops the build if the page is not a UTF-8 file."""
        try:
            return page_file.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            raise SystemExit(f"{page_file}: the page is not a UTF-8 file")


    def _page_text_with_rewritten_urls(self, page_text: str, page_file: Path) -> str:
        """This method returns the text of the page with its URLs rewritten, except inside fenced code blocks."""
        lines: list[str] = page_text.split("\n")
        inside_code_block: bool = False

        for line_index, line in enumerate(lines):
            if CODE_BLOCK_MARKER.match(line):
                inside_code_block = not inside_code_block
            elif not inside_code_block:
                lines[line_index] = self._line_with_rewritten_urls(line, page_file)

        return "\n".join(lines)


    # -- Private: one line ---------------------------------------------------------------------------

    def _line_with_rewritten_urls(self, line: str, page_file: Path) -> str:
        """This method returns the line with each URL starting with "/" replaced by the one the UrlResolver gives."""
        line_with_rewritten_urls: str = ""
        end_of_previous_url: int = 0

        for match in URL_STARTING_WITH_SLASH.finditer(line):
            resolved_url: str = self._url_resolver.resolve_url(match["url_without_first_slash"], page_file)
            text_before_url: str = line[end_of_previous_url:match.start()]
            line_with_rewritten_urls += text_before_url + match["opening"] + resolved_url
            end_of_previous_url = match.end()

        return line_with_rewritten_urls + line[end_of_previous_url:]
