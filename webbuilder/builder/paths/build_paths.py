"""
The names of the files and folders the builder reads and writes, in one place.

What the user writes, in the websites folder:
    <website>/website_settings.yml
    <website>/versions/<version>.yml

What a build writes there:
    <website>/preparation/version_builds/<version>/
        version_clone/        the clone of the version, deleted once it is built
        version_pages/        the pages the site generator reads, with versions.json
        version_site/         the site it writes
    build/<path of site_url>/
        index.html            redirects to latest/
        latest/               the latest version, with website_search.json
        <version>/            each earlier version
"""

# -- Website configuration ------------------------------------------------------------------------------
WEBSITE_SETTINGS_FILE_NAME: str = "website_settings.yml"
VERSIONS_FOLDER_NAME: str = "versions"  # one <version name>.yml per version

# -- data preparation -----------------------------------------------------------------------------------
PREPARATION_FOLDER_NAME: str = "preparation"
VERSION_BUILDS_FOLDER_NAME: str = "version_builds"  # one work folder per version
VERSION_CLONE_FOLDER_NAME: str = "version_clone"
PAGES_FOLDER_NAME: str = "version_pages"  # the pages the site generator reads
VERSION_MENU_FILE_NAME: str = "versions.json"  # in the pages folder, read by the menu of versions
VERSION_SITE_FOLDER_NAME: str = "version_site"  # the site the site generator writes

# -- Build configuration --------------------------------------------------------------------------------
BUILT_WEBSITES_FOLDER_NAME: str = "build"  # in the websites folder
REDIRECTION_FILE_NAME: str = "index.html"  # at the root of a website, sends the reader to the latest version
LATEST_VERSION_FOLDER_NAME: str = "latest"
WEBSITE_SEARCH_INDEX_FILE_NAME: str = "website_search.json"  # the pages of a website alone, kept to merge again
