# webbuilder

This folder holds the code of the website builder. The file `main.py`, at the root of the repository, starts it.

## The three packages

- `builder/` applies the rules of OpenFlexo to the websites and their versions.
- `zensical/` talks to Zensical: it writes its config, runs its command and reads its search file.
- `common/` gives the tools and the two interfaces that both packages share.

The packages `builder/` and `zensical/` never import each other. They import `common/`, and only `main.py` links them.

## The steps of a build

A build has six steps, and steps 2 to 4 run once per version. Every version is built before the first one is put in place, so a failed build never damages a published website.

1. **Read the settings.** `WebsiteScanner` finds the websites, and `WebsiteSettings` reads the settings and the versions of each one.
   (`builder/website/helper/website_scanner.py`, `builder/website/website_settings.py`, `builder/version/version_settings.py`)
2. **Clone a version.** `WebsiteBuilder` asks `VersionBuilder` to clone the git reference of each version.
   (`builder/website/website_builder.py`, `builder/version/version_builder.py`, `common/helper/clone_git_repository.py`)
3. **Prepare its pages.** `VersionPreparer` copies the sources and the style into one folder of pages, and `UrlRewriter` fixes the links starting with "/" in the copies.
   (`builder/version/version_builder.py`, `builder/version/helper/url_rewriter.py`, `builder/version/helper/url_resolver.py`)
4. **Build its HTML.** `ZensicalSiteGenerator` writes the config of Zensical and runs Zensical on the pages.
   (`zensical/zensical_site_generator.py`, `zensical/zensical_config.py`)
5. **Put the versions in place.** `WebsiteBuilder` copies each built version into the folder that `BuiltWebsite` gives, then the latest version into `latest/`, and `BuiltWebsite` writes `versions.json` and the page that redirects to the latest version.
   (`builder/website/website_builder.py`, `builder/website/built_website.py`)
6. **Merge the search.** `GlobalSearch` gives the search of each website the pages of the others.
   (`builder/search/global_search.py`, `zensical/zensical_search_index.py`)

## Vocabulary

| Word | Meaning |
|---|---|
| **tool** | This program, the website builder. Not to be confused with the class `WebsiteBuilder`, which builds one website. |
| **project** | The software whose documentation is built (Pamela, Connie). Its website is its documentation. |
| **website** | The documentation of one project, with all its versions. One folder in the websites folder. |
| **version** | One state of a website, built from a git reference (1.6, 1.6.1). |
| **git reference** | The branch or tag a version is cloned from (`git_ref`). |
| **latest version** | The version named by `extra.latest_version` in `website_settings.yml` and copied in `latest/`. |
| **settings** | What a person writes in YAML: `website_settings.yml` for the website, `versions/<name>.yml` for a version. |
| **config** | The file `zensical_config.yml` that the tool writes for Zensical, from the settings. Nobody edits it. |
| **documentation source** | A folder of the cloned repository copied into the website (`source` and `destination`). |
| **work folder** | The folder of one version during its build: `preparation/version_builds/<version>/`. It holds the clone, the pages, the config and the site. |
| **clone** | The temporary copy of the repository at the git reference of a version (`version_clone/`). |
| **pages** | The Markdown files of a version once copied and fixed, in `version_pages/`. Zensical reads them. |
| **site** | The HTML that Zensical writes for one version (`version_site/`). Not to be confused with a website. |
| **built website** | The website once built: one folder per version in `build/`, with a page that redirects to the latest. |
| **site generator** | The tool that builds a site from pages. Zensical is the only one for now. |
| **side menu** | The menu of a version when written by hand in its settings (`side_menu`). Without it, Zensical builds it from the pages. |
| **search index** | The list of pages that the search reads (`search.json`). The merged index adds the pages of the other websites. |

The keys `site_name` and `site_url` of `website_settings.yml` are the name and the address of the website: Zensical calls them that way. The site generator receives a `site_url` too, which is then the address of one version.

## Where to start reading

Read `main.py` first, then the files of the steps in their order. Each folder has its own README that describes its files.
