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
3. **Prepare its pages.** `VersionPreparer` copies the sources, the style and the menu of versions into one folder of pages, and `UrlRewriter` fixes the links starting with "/" in the copies.
   (`builder/version/version_builder.py`, `builder/version/helper/url_rewriter.py`, `builder/version/helper/url_resolver.py`)
4. **Build its HTML.** `ZensicalSiteGenerator` writes the config of Zensical and runs Zensical on the pages.
   (`zensical/zensical_site_generator.py`, `zensical/zensical_config.py`)
5. **Put the versions in place.** `WebsiteBuilder` copies each built version into the folder that `BuiltWebsite` gives, and `BuiltWebsite` writes the page that redirects to the latest version.
   (`builder/website/website_builder.py`, `builder/website/built_website.py`)
6. **Merge the search.** `GlobalSearch` gives the search of each website the pages of the others.
   (`builder/search/global_search.py`, `zensical/zensical_search_index.py`)

## Where to start reading

Read `main.py` first, then the files of the steps in their order. Each folder has its own README that describes its files.
