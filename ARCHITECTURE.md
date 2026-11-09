# Architecture

## What it does
Each OpenFlexo project (Pamela, Connie, ...) keeps its documentation as Markdown in a git repository, and releases
several versions of it (1.6.1, 1.6, ...). This tool builds one website per project: each version is built from its
own git tag, the latest one is shown by default, a menu on every page leads to the other versions, and the search
box also finds the pages of the other websites. The HTML is produced by Zensical: this tool prepares what Zensical
needs and puts together what it produces.

## What you write
One folder per website in `websites/` (`websites/pamela/` is built with `--build-websites pamela`):
- `website_settings.yml`: what is the same for every version (name, public address, git repository, top bar links).
- `versions/<name>.yml`: one file per version. The name of the file is the name of the version.

The keys of these files are described in the README, "What a project needs".

## What a build does
`python main.py --websites-folder websites --build-websites pamela`
1. **Reads the websites**: each folder of `websites/` with a `website_settings.yml` (`WebsiteScanner`, `WebsiteSettings`).
2. **Builds each version** (`WebsiteBuild` loops, `VersionBuild` does one): clones its git tag (`GitRepository`),
   gathers its Markdown and fixes the links starting with `/` (`VersionPages`), has the site generator build the HTML,
   deletes the clone. The work files stay in `preparation/version_builds/<version>/`, next to the
   `website_settings.yml`, to see what Zensical was given and what it produced.
3. **Puts the versions in place** (`WebsiteBuild`), only when all are built, so a failure never leaves a website half
   updated: in `websites/build/<address>/`, the latest version at the root, the others in a folder named after them.
4. **Merges the search** (`SharedSearch`): the search file of every built website gets the pages of the others.

## Who is responsible for what
- `webbuilder/zensical/`: knows how Zensical works (its config, its command, its search file). To use another tool,
  start here, then see "What depends on Zensical" in the README.
- `webbuilder/builder/`: the rules of OpenFlexo (versions, assembling the websites, shared search, fixing links). It
  reaches the tool only through `SiteGeneratorInterface`.
- `webbuilder/common/`: generic helpers (copy a folder, clone a repository) and the two contracts between the
  builder and the tool.
- `shared/`: what the websites share: Zensical's default settings and HTML templates, and the OpenFlexo style and icon.

## Where to start reading
Read the code in the order a build runs it:
1. `main.py`: reads the command line, finds the websites, builds each one with `WebsiteBuild`, then merges the search.
2. `builder/website/`: how the settings of a website and of its versions are read and checked.
3. `builder/website_build.py`: builds the versions one by one, then puts them in place in `websites/build/`.
4. `builder/version/version_build.py`: builds one version: clone, pages, site.
5. `builder/version/version_pages.py` (and the two `page_url_*` files): turns the clone into the pages folder Zensical reads.
6. `zensical/zensical_site_generator.py` (and `zensical_config.py`, `zensical_runner.py`): writes the config of Zensical and runs it.
7. `builder/shared_search.py` (and `zensical/zensical_search_index.py`): back in `main.py`, gives each website the pages of the others.

`common/` is read when met: the helpers and the two contracts (`*_interface.py`).

## Words used
- **website**: the documentation of one project, with all its versions (e.g. Pamela).
- **version**: one release of a website (1.6.1). **Latest version**: the one shown by default, exactly one per website.
- **pages folder** (`version_pages/`): the Markdown of one version, gathered and fixed, which Zensical reads.
- **version site** (`version_site/`): the HTML Zensical writes for one version.
- **preparation folder** (`preparation/`): the work files of a website's builds.
- **site generator**: the tool that turns a pages folder into a site. Today: Zensical.
- **shared search**: the search that finds the pages of the latest version of every website.
