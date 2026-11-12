# paths

This folder gives the names of the files and folders that the builder reads and writes.

- `build_paths.py` holds the names of the files and folders of the websites, of the work of a build and of the built websites.
- `shared_paths.py` holds the folders of `shared/`: the default settings, the HTML templates, the style and the icon.

The names of `build_paths.py` give this layout in the websites folder:

```text
<websites folder>/
├── <website>/
│   ├── website_settings.yml                 written by the user
│   ├── versions/<version>.yml               written by the user, one file per version
│   └── preparation/version_builds/<version>/
│       ├── version_clone/                   the clone of the version, deleted once it is built
│       ├── version_pages/                   the pages the site generator reads, with versions.json
│       ├── zensical_config.yml              the config that Zensical reads
│       └── version_site/                    the site that Zensical writes
└── build/<path of site_url>/
    ├── index.html                           redirects to latest/
    ├── latest/                              the latest version, with website_search.json
    └── <version>/                           each earlier version
```
