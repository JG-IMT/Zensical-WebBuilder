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

The keys of these files are described in the README, "Settings" and "Versions".

## What a build does
`python main.py --websites-folder websites --build-websites pamela`

```text
website_settings.yml + versions/*.yml
      │
      ▼  once, at start
1. READ SETTINGS    WebsiteScanner, WebsiteSettings
   how: project settings over shared/zensical/default_settings.yml, one version per file
   why: a config error stops the tool before any clone
      │
      ▼  for each version asked (VersionBuild), in preparation/version_builds/<version>/
2. CLONE            GitRepository                        -> version_clone/
   how: git clone --depth 1 --branch <git_ref> <repository_url>
   why: a version shows the documentation as it was released
      │
      ▼
3. PREPARE PAGES    VersionPages                         -> version_pages/
   how: copies the style and each source to its destination, fixes the links starting with "/"
   why: Zensical reads one folder; the repository is never changed
      │
      ▼
4. BUILD THE HTML   ZensicalSiteGenerator                -> version_site/
   how: writes zensical_config.yml (side_menu becomes nav), runs `zensical build`; the clone is then deleted
   why: only this package knows Zensical
      │
      ▼  when every version asked is built
5. PUT IN PLACE     WebsiteBuild                         -> websites/build/<path of site_url>/
   how: the latest version in latest/, the others in <version>/; the root redirects to latest/
   why: a failed build never leaves a website half updated
      │
      ▼  once, at the end, for every built website
6. MERGE SEARCH     SharedSearch                         -> latest/search.json of each website
   how: adds the pages of the other websites, with a relative path
   why: the search of a website also finds the pages of the others
```

Each step shows who does it (the class) and what it writes (`->`); the arrows say when.
`preparation/` is next to the `website_settings.yml`; it is kept to see what Zensical was given and what it produced.

## Who is responsible for what
- `webbuilder/zensical/`: knows how Zensical works (its config, its command, its search file). To use another tool,
  start here, then see "What depends on Zensical" in the README.
- `webbuilder/builder/`: the rules of OpenFlexo (versions, assembling the websites, shared search, fixing links). It
  reaches the tool only through `SiteGeneratorInterface`.
- `webbuilder/common/`: generic helpers (copy a folder, clone a repository) and the two contracts between the
  builder and the tool.
- `shared/`: what the websites share: Zensical's default settings and HTML templates, and the OpenFlexo style and icon.

## The classes
In reading order. `Website*` read the settings, `Version*` and `Page*` build one version, the others assemble and search.

**builder/**
- `WebsiteScanner`: finds the websites of the `websites/` folder and checks the names asked.
- `WebsiteSettings`: reads `website_settings.yml` over the shared settings, then the versions, and checks them.
- `WebsiteVersions`: the versions of a website; checks them together (one latest) and gives each one its folder and address.
- `WebsiteVersion`: one declared version: name, git reference, latest or not, menu, sources.
- `WebsiteBuild`: builds the versions asked of a website, then puts them in `websites/build/`.
- `VersionBuild`: builds one version: clone, pages, site; deletes the clone.
- `VersionPages`: prepares the pages folder of a version: sources, style, menu of versions.
- `PageUrlRewriter`: rewrites in the Markdown pages the URLs starting with `/`.
- `PageUrlResolver`: decides what one such URL becomes.
- `SharedSearch`: gives each built website the pages of the others (next section).

**zensical/**
- `ZensicalSiteGenerator`: Zensical as a `SiteGeneratorInterface`: builds a site, reads its search index.
- `ZensicalConfig`: writes the config file Zensical reads.
- `ZensicalRunner`: runs `zensical build`.
- `ZensicalSearchIndex`: reads and writes the search file of Zensical (`search.json`); the only code that knows its format.

**common/**
- `SiteGeneratorInterface`: the contract of the tool that builds a site from a pages folder.
- `SearchIndexInterface`: the contract of the search index of one site.
- `GitRepository`: clones a repository at a branch or a tag.
- `FolderHelper`: copies and deletes folders (the only use of `shutil`).

## The shared search
Zensical gives each version its own search file (`search.json` at its root), with one entry per page: its
`location` and its `title`. The shared search adds to the one of the latest version (`latest/search.json`) the
entries of the latest version of the other websites, so that its search box finds the pages of all of them.
An earlier version only searches its own pages.

Once the builds are done, for each built website (`SharedSearch.merge`):
1. its own entries are copied once to `website_search.json`, next to `search.json`;
2. the entries of every other website are taken from their own `website_search.json`, with a path relative to
   this one (`../../../connie/docs/latest/page.html`) and the name of their website before the title (`Connie · Title`);
3. `search.json` is rewritten with its own entries followed by those of the others.

Things to know:
- Merging always starts from `website_search.json`, never from the merged `search.json`: merging again, for
  example after another website is built, never adds the same pages twice.
- Rebuilding the latest version replaces `latest/`, `website_search.json` included, and the next merge makes it
  again from the new `search.json`.
- A website not built yet is skipped. Relative paths only work if the websites stay side by side in `websites/build/`.

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
- **version**: one release of a website (1.6.1). **Latest version**: the one shown by default, in `latest/`; exactly one per website.
- **pages folder** (`version_pages/`): the Markdown of one version, gathered and fixed, which Zensical reads.
- **version site** (`version_site/`): the HTML Zensical writes for one version.
- **preparation folder** (`preparation/`): the work files of a website's builds.
- **site generator**: the tool that turns a pages folder into a site. Today: Zensical.
- **shared search**: the search that finds the pages of the latest version of every website.
- **`website_search.json`**: the pages of a website alone, kept next to its `search.json` to merge the search again.
