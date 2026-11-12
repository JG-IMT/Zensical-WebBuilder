# builder

This package applies the rules of OpenFlexo to the websites and their versions. It has four folders, one per kind of work:

- `website/` reads a website and builds it from its versions.
- `version/` reads one version and builds it.
- `search/` gives the search of each website the pages of the other websites.
- `paths/` gives the names of the files and folders.

A build starts in `website/`, which calls `version/` for each version, and ends in `search/`. Every folder reads the names of the files and folders in `paths/`.

The package `builder/` imports only `common/`, and it knows the site generator only through the interfaces of `common/`. The steps of a build are described in the README of `webbuilder/`.
