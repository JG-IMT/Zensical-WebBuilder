# Architecture

## What this tool does
The OpenFlexo projects (Pamela, Connie, ...) keep their documentation as Markdown files in their git
repositories, and release several versions of it (1.6.1, 1.6, 1.5.0.1, ...). Zensical-WebBuilder builds, for each
project, the documentation website published on openflexo.org: every version is built from its own git tag, the latest
one is shown by default, and a menu on every page leads to the other versions. The search box of a website
also finds the pages of the other websites.

The HTML itself is produced by Zensical, an external tool that turns Markdown into a website. This tool
prepares what Zensical needs, and puts together what it produces.

## What goes in, what comes out
```text
IN                                                OUT (websites/build/)
git repository of Pamela (tags 1.6.1, 1.6, ...)   pamela/docs/            version 1.6.1, the latest
websites/pamela/website_settings.yml              pamela/docs/1.6/        version 1.6
websites/pamela/versions/1.6.1.yml, 1.6.yml, ...  pamela/docs/1.5.0.1/    version 1.5.0.1
```

## What you write for a website
Each website is a folder in the websites folder. Its name is the name of the website (`websites/pamela/` is
built with `--build-websites pamela`). The folder holds:
- `website_settings.yml`: what is the same for every version: name, public address, git repository, links of
  the top bar.
- `versions/<name>.yml`: one file per version, the name of the file is the name of the version.
  ```yaml
  git_ref: "1.5.0.1"                  # the git tag (or branch) this version is built from
  documentation_sources:              # where the Markdown is in the repository
    - source: src/site/markdown       #   folder in the repository
      destination: .                  #   folder in the website
  ```
  `git_ref` and `documentation_sources` are required. `is_latest: true` is required on exactly one version of
  the website. `side_menu` (the menu on the left) is optional: without it, the menu is generated from the pages.

## What happens during a build
`python main.py --websites-folder websites --build-websites pamela`
1. **Find and read the websites.** Each folder of `websites/` with a `website_settings.yml` is a website.
2. **Build each version**, one after the other:
   1. clone that version from git, since a website must show the documentation as it was released;
   2. gather its Markdown in one folder and fix the links starting with `/`, which would point to the
      server root instead of the website;
   3. ask Zensical to build the HTML;
   4. delete the clone.
3. **Put the results in place**, only when every version asked for has been built, so that a failure never
   leaves a website half updated. The latest version goes at the root, the others in a folder named after them.
4. **Rewrite the search file** of every website already built, so that each one also finds the pages of the
   other websites.

| Step | Code |
|---|---|
| 1 | `WebsiteScanner`, `WebsiteSettings` |
| 2 | `WebsiteBuild` (loops over the versions), `VersionBuild`, `GitRepository`, `VersionPages`, the site generator |
| 3 | `WebsiteBuild` |
| 4 | `SharedSearch` |

## Who is responsible for what
The code is in three packages, split by what each one knows:
- `webbuilder/zensical/` knows how Zensical works: its config file, its command, its search file. To use
  another tool, start here, then see "What depends on Zensical" in the README: the settings and the HTML
  templates are also written for Zensical.
- `webbuilder/builder/` holds the rules of OpenFlexo: versions, assembling the websites, the shared search,
  fixing the links. It talks to the tool only through `SiteGeneratorInterface`.
- `webbuilder/common/` holds generic helpers (copy a folder, clone a repository) and the two contracts
  between the builder and the tool.

`shared/zensical/` holds what Zensical reads (default settings, HTML templates), `shared/openflexo/` the look
of the websites (style, icon).

## Where to start reading the code
1. `main.py`: the command line, and the order of the steps of a build.
2. `builder/website_build.py`: builds the versions asked for and puts them in the built website.
3. `builder/version/version_build.py`: the steps for one version (clone, pages, site).
4. `zensical/zensical_site_generator.py`: how Zensical is called to build a site.
5. `builder/shared_search.py`: how the websites search each other.

## Words used
| Word | Meaning |
|---|---|
| website | The documentation of one project, with all its versions (e.g. Pamela). |
| version | One release of a website (1.6.1). |
| latest version | The version shown by default. Exactly one per website. |
| pages folder | `version_pages/`: the Markdown of one version, gathered and fixed, which Zensical reads. |
| version site | The HTML Zensical writes for one version (`version_site/`). |
| built website | The versions put together in `websites/build/`. |
| site generator | The tool that turns a pages folder into a site. Today: Zensical. |
| shared search | The search that finds the pages of the latest version of every website. |

## Rules to keep, and why
- `zensical/` imports nothing from `builder/`, and `common/` imports neither `builder/` nor `zensical/`: the
  calls to the tool stay in one place.
- Only `main.py` creates the site generator: the builder stays independent of the tool.
- All the versions asked for are built before the first one is put in place: a failed build never damages a
  published website.
- The Markdown of the repositories is never changed: the links are fixed in the copies.
- The websites stay side by side in `websites/build/`: the shared search points from one to the other with
  relative paths.
- What the HTML templates read is checked by `tests/test_template_contract.py`: a renamed key would otherwise
  break the pages silently.
