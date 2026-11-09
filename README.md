# Website builder

Builds the documentation websites of the OpenFlexo projects (Pamela, Connie, ...), with all their versions,
from the Markdown of their git repositories, using [Zensical](https://zensical.org). The tool, the theme and
the OpenFlexo footer are the same for every project, a project only brings a `website_settings.yml`.

To understand how the tool works, start with [ARCHITECTURE.md](ARCHITECTURE.md).

## What a project needs

- a git repository holding its documentation as Markdown files.
- a `website_settings.yml` saying where the repository is and how the website looks, and a `versions/` folder
  next to it with one file per version to build. Start from `examples/website_settings.yml` and
  `examples/versions/`, for now the name of the folder is the name of the website.

## Install (once)

Needs Python 3.11 or later and git.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Linux and macOS: `source .venv/bin/activate`.

## Build

```powershell
python main.py --websites-folder websites --build-websites
python main.py --websites-folder websites --build-websites pamela
python main.py --websites-folder websites --build-websites pamela --build-versions 1.6 1.6.1
python main.py --websites-folder examples\demo\components\websites --build-websites
```

Without a name, every website of the folder is built. `--build-versions` builds only some versions of one
website; what is not built is left as it is.

The websites are in `websites/build`, each in the folder of its `site_url` (`build/pamela/docs/`): the latest
version at its root, each earlier version in a folder named after it. The search of a website covers the latest
version of every website built there.

To look at it, serve that folder with any web server, for example
`python -m http.server 8000 --directory websites\build`, then open http://localhost:8000/pamela/docs/.
For the demo, serve `examples\demo\components\websites\build`.

The demo in `examples/demo/components` does all of this with Gradle:

```powershell
./gradlew buildDocumentationSites                      # every website (-Pwebsites=pamela,connie to build one site)
./gradlew buildDocumentationSites -Pwebsites=pamela -Pversions=1.6.1,1.6    # only these versions of one website
./gradlew serveDocumentationSites                      # http://localhost:8000
```

## Settings

| Key | Role |
|---|---|
| `site_name` | Name of the website |
| `site_description` | One sentence describing the project |
| `site_url` | Address where the website is published. The latest version is served there, the others in `site_url/<name>/`. Its path is the folder of the website in `websites/build` |
| `theme.logo` | Logo of the website: a path inside the website, or an address |
| `extra.repository_url` | The git repository to clone |
| `extra.homepage` | Home page of the project. Its path completes the URLs starting with `/` that lead outside the website (`/javadoc/...` becomes `/<path>/javadoc/...`) |
| `extra.navbar_links` | The links of the top bar |

## Versions

Each version is a file `versions/<name>.yml` next to `website_settings.yml`. The name of the file is the name of
the version (shown in the menu, used as folder name); the menu lists the versions in alphabetical order, the latest first.

| Key | Role |
|---|---|
| `git_ref` | The branch or the tag the version is built from |
| `is_latest` | `true` on exactly one version: it is served at `site_url`, the others in `site_url/<name>/` |
| `side_menu` | Optional. The menu of the version; without it the menu is generated from the pages |
| `documentation_sources` | The folders of the repository copied into the website. `source` is relative to the repository root, `destination` is the folder in the website (`.` for its root). A later entry overwrites an earlier one |

## Tests

```powershell
pip install -r requirements-dev.txt    # once: pytest, ruff, mypy
python -m pytest
python -m ruff check .
python -m mypy main.py webbuilder tests
```

## Structure of the tool

```text
Zensical-WebBuilder/
├── main.py                 The command line: builds the websites
├── requirements.txt        Python dependencies (requirements-dev.txt: pytest, ruff, mypy)
├── pyproject.toml          Settings of pytest, ruff and mypy
├── CHANGELOG.md
├── tests/                  pytest tests
├── examples/               Templates of website_settings.yml and versions/, and the demo (Pamela, Connie)
├── shared/                 What every website shares
│   ├── zensical/           What Zensical reads: default settings, HTML templates (html_templates/)
│   └── openflexo/          The look of OpenFlexo: style and icon
└── webbuilder/             The code
    ├── common/             Generic tools, and the two contracts with the tool that builds the sites
    ├── zensical/           What speaks Zensical's language; it knows nothing of OpenFlexo
    └── builder/            OpenFlexo's rules: building a website, the shared search, and two sub-folders
        ├── website/        Reading and checking the settings and the versions
        └── version/        Building one version: clone, pages, links
```

Each file is described in the reading order of [ARCHITECTURE.md](ARCHITECTURE.md). After a build, a
`preparation/` folder next to each `website_settings.yml` keeps what Zensical was given and what it produced.

## What depends on Zensical

The builder knows the tool only through `SiteGeneratorInterface` (`webbuilder/common/`): build a site from a
folder of pages, and read the search index of a site. `ZensicalSiteGenerator` (`webbuilder/zensical/`) is the only
implementation, and `main.py` is the only place that creates it.

Replacing Zensical takes more than another implementation. Zensical also shapes:

- the settings: `website_settings.yml` and `shared/zensical/default_settings.yml` use Zensical and Material
  options, and `WebsiteSettings` knows the `nav` key;
- the templates: `shared/zensical/html_templates/` override the Material theme, including the menu of
  versions and the "no longer maintained" banner;
- the folders of a version (`VersionBuild`, `VersionPages`): a folder of pages read by the tool and a folder
  where it writes the site.

A close tool (MkDocs, Material for MkDocs) needs a new implementation and a check of the options and templates.
A different tool also means redoing the settings, the templates and the search.

## Good to know

- Links starting with `/` that lead to a file of the documentation are made relative in the build; the
  Markdown of your repository is not changed.
- A build that fails keeps the previous website: the versions are all built before the first one is put in it.
- A version built alone replaces only its own folder. The latest version is at the root: building it deletes
  what is at the root except the folders of the earlier versions.
- After adding a version or moving `is_latest`, build every version: the menu of versions and the "no longer
  maintained" banner of the others are written when they are built.
- Deploy `websites/build` as it is: the search links between websites are relative.
