# Changelog

All notable changes to this tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Changed

- The latest version of a website is in the folder `latest/` (it was at the root of the website) and the root
  redirects to it: a built website holds one folder per version. No earlier version may be named `latest`.
  Delete `websites/build` once before the first build, to remove the pages of the former layout.
- Building the latest version no longer deletes the folder of a version that is no longer declared.
- Packages: `common/` (generic tools), `zensical/` (what speaks Zensical's language) and `builder/` (the rules of
  OpenFlexo); `shared/` is split in `shared/zensical/` and `shared/openflexo/`.
- `builder/` is grouped by domain: `website/` (settings, versions, scanner), `version/` (build of one version, pages,
  URL rewriting), and `website_build.py` and `shared_search.py` at its root.
- The builder reaches the tool that builds the sites through `SiteGeneratorInterface`; `ZensicalSiteGenerator`
  is its implementation, created by `main.py` only.
- Names: `WebsiteVersionCatalog` is `WebsiteVersions`, `ZensicalBuild` is `ZensicalRunner`, `ZensicalInput` is
  `VersionPages`, `ScanWebsite` is `WebsiteScanner` and `MergeSearchIndex` is `SharedSearch`; the folder
  `zensical_input` of a version is `version_pages`; the key `navigation` of a version file is `side_menu`.

## [0.3.0] 05/11/2026

### Added

- One file per version in `versions/<name>.yml`, next to `website_settings.yml`: `git_ref`, `is_latest`,
  `navigation` and `documentation_sources`. The name of the file is the name of the version.
- `--build-versions` builds only the versions named, of one website. A version replaces only its own place
  in the website.
- Tests (pytest) with `requirements-dev.txt` and `pyproject.toml` for pytest, ruff and mypy.
- `-Pversions=` for the gradle task `buildDocumentationSites`.

### Changed

- `website_settings.yml` keeps what is common to every version: name, address, repository, links.
- The versions are put in the website one by one: all the versions to build are built before the first one
  is put in it, so a failed build keeps the previous website.
- The examples and the demo use the new format; the menu lists the versions in alphabetical order.

### Removed

- `extra.versions` and `extra.documentation_sources` in `website_settings.yml`.

## [0.2.0] 23/10/2026

### Added

- `--build-websites` builds the websites found in `websites/`: all of them, or only the ones named.
- Global search : the search of a website finds the pages of the other websites.
- A demo with gradle tasks in `examples/demo/` : `buildDocumentationSites` and `serveDocumentationSites`.

### Changed

- A website is assembled in `websites/build/<path of its site_url>`, as it is on the server.
- The work of a website is in the `preparation` folder next to its `website_settings.yml`.

### Removed

- `--settings`: use `--build-websites <name>`.

## [0.1.1] 22/10/2026

### Added

- A breadcrumb.

### Changed

- The header, the side menu, the table of contents, the pagination and the footer have the sizes and the
  spacing of the former website. The footer columns are equal and centred.
- The colour toggle shows an outlined sun and moon.
- The style sheet has variables for the colours and the sizes of the page.

### Fixed

- The table of contents no longer shows a scroll bar.
- The footer links have the colour of the footer text: the theme dimmed them.
- The page highlighted in the side menu can be seen in the dark scheme.

## [0.1.0] 22/10/2026

### Added

- The README describes the structure of the tool, file by file, and the folders a build creates.

### Changed

- The settings shared by every website are in `shared/default_settings.yml` (it was `shared/site_settings.yml`)
  and the settings of the project override them.
- The code follows one structure: the classes keep their data private, the settings, the version and the
  catalog of versions give it through `get_*` methods, a version and the catalog of versions are two classes
  in two files, and folders are copied and deleted by one helper.

## [0.0.0] 20/10/2026

Initial development version.

### Added

- Builds the documentation website of a project from the Markdown of its git repository, with
  Zensical: `python main.py --settings website_settings.yml`.
- Several versions per website, each one cloned from a branch or a tag. The latest version is served at
  the root of the website, the others in a folder named after them.
- One `website_settings.yml` per project, completed by the settings shared by every website.
- URLs starting with `/` are rewritten in the copies of the Markdown pages.
- A build that fails keeps the previous website, and the clones are deleted once each version is built.
