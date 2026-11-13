"""
These constants give the names of the files and folders the builder reads and writes, in one place.

Used at every step: each class reads the names it needs here instead of writing them itself.

The layout these names make in the websites folder is drawn in the README of this folder (paths/README.md).
"""

# -- Website settings ------------------------------------------------------------------------------
WEBSITE_SETTINGS_FILE_NAME: str = "website_settings.yml"
VERSIONS_FOLDER_NAME: str = "versions"  # one <version name>.yml per version

# -- Preparation -----------------------------------------------------------------------------------
PREPARATION_FOLDER_NAME: str = "preparation"
VERSION_BUILDS_FOLDER_NAME: str = "version_builds"  # one work folder per version
VERSION_CLONE_FOLDER_NAME: str = "version_clone"
PAGES_FOLDER_NAME: str = "version_pages"  # the pages the site generator reads
VERSION_MENU_FILE_NAME: str = "versions.json"  # at the root of a website, lists its built versions, read by the menu of versions
VERSION_SITE_FOLDER_NAME: str = "version_site"  # the site the site generator writes

# -- Built websites --------------------------------------------------------------------------------
BUILT_WEBSITES_FOLDER_NAME: str = "build"  # in the websites folder
REDIRECTION_FILE_NAME: str = "index.html"  # at the root of a website, sends the reader to the latest version
LATEST_VERSION_FOLDER_NAME: str = "latest"
WEBSITE_SEARCH_INDEX_FILE_NAME: str = "website_search.json"  # the pages of a website alone, kept to merge again
