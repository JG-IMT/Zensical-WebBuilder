# zensical

This package talks to Zensical, so that the rest of the code does not need to know it. It imports only `common/`.

- `zensical_site_generator.py` holds `ZensicalSiteGenerator`, which builds the site of a version with Zensical and reads the search index of a site.
- `zensical_config.py` holds `ZensicalConfig`, which writes the config file that Zensical reads.
- `zensical_search_index.py` holds `ZensicalSearchIndex`, which reads and writes the search file of Zensical, `search.json`.

`ZensicalSiteGenerator` builds a site in two steps (step 4 of a build):

1. `ZensicalConfig` writes `zensical_config.yml` in the work folder of the version, with the settings of the website, the address of the version, the folders of the pages and of the site, the HTML templates, the menu and the values that the templates read.
2. `ZensicalSiteGenerator` runs `python -m zensical build` on this config and reports whether Zensical succeeded.

`ZensicalSearchIndex` is the only code that knows the format of `search.json` (step 6 of a build).

To use another tool, replace this package and implement the two interfaces of `common/`. The settings and the HTML templates of `shared/zensical/` are also written for Zensical.
