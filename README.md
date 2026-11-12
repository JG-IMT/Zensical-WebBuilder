# Website builder

This tool builds the documentation websites of the OpenFlexo projects (Pamela, Connie, ...), with all their versions, from the Markdown of their git repositories, using [Zensical](https://zensical.org). The tool, the theme and the OpenFlexo footer are the same for every project, and a project only brings a `website_settings.yml` and one file per version.

## How it works

For each website, the tool clones every version from git, builds its HTML with Zensical, puts the versions side by side in one folder, then gives each website the search of the others.

The steps of a build, with their files and classes, are listed in the README of [webbuilder](webbuilder/README.md).

## Structure of the tool

```text
Zensical-WebBuilder/
├── main.py                 starts a build from the command line
├── pyproject.toml          sets pytest, ruff and mypy
├── requirements.txt        lists the Python dependencies (requirements-dev.txt adds pytest, ruff and mypy)
├── CHANGELOG.md            lists the changes of the tool
├── webbuilder/             holds the code, in three packages
│   ├── builder/            applies the rules of OpenFlexo to the websites and their versions
│   ├── zensical/           talks to Zensical
│   └── common/             gives the tools that both packages share
├── shared/                 holds what every website shares
│   ├── zensical/           holds what Zensical reads: the default settings and the HTML templates
│   └── openflexo/          holds the look of OpenFlexo: the style and the icon
├── examples/               holds the templates of the settings and a demo (Pamela, Connie)
└── tests/                  holds the pytest tests
```

Each folder of `webbuilder/` has its own README that describes its files.

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
version in `latest/`, each earlier version in a folder named after it, and a page at the root that redirects to
`latest/`. The search of the latest version covers the latest version of every website built there.

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
| `site_url` | Address where the website is published. It redirects to the latest version, served in `site_url/latest/`; the others are in `site_url/<name>/`. Its path is the folder of the website in `websites/build` |
| `theme.logo` | Optional. Logo of the top bar, Openflexo's by default: a path inside the website, or an address |
| `extra.brand` | Optional. `name` and `link` behind the logo, Openflexo's by default |
| `extra.footer_columns` | Optional. The columns of the footer, shared by default. A list here replaces them |
| `extra.repository_url` | The git repository to clone |
| `extra.homepage` | Home page of the project. Its path completes the URLs starting with `/` that lead outside the website (`/javadoc/...` becomes `/<path>/javadoc/...`) |
| `extra.navbar_links` | Optional. The links of the top bar, shared by default. A list here replaces them |

## Versions

Each version is a file `versions/<name>.yml` next to `website_settings.yml`. The name of the file is the name of
the version (shown in the menu, used as folder name); the menu lists the versions in alphabetical order, the latest first.

| Key | Role |
|---|---|
| `git_ref` | The branch or the tag the version is built from |
| `documentation_sources` | The folders of the repository copied into the website. `source` is relative to the repository root, `destination` is the folder in the website (`.` for its root). A later entry overwrites an earlier one |
| `side_menu` | Optional. The menu of the version, written by hand: each line is a page of the website (a file copied by `documentation_sources`). Without it the menu is generated from the pages |
| `is_latest` | `true` on exactly one version: it is served in `site_url/latest/`, the others in `site_url/<name>/`. No earlier version may be named `latest` |

The keys are in the order of the build: clone, copy, menu, place.

## Tests

```powershell
pip install -r requirements-dev.txt    # once: pytest, ruff, mypy
python -m pytest
python -m ruff check .
python -m mypy main.py webbuilder tests
```

## What depends on Zensical

The builder knows the tool only through `SiteGeneratorInterface` (`webbuilder/common/`): build a site from a
folder of pages, and read the search index of a site. `ZensicalSiteGenerator` (`webbuilder/zensical/`) is the only
implementation, and `main.py` is the only place that creates it.

Replacing Zensical takes more than another implementation. Zensical also shapes:

- the settings: `website_settings.yml` and `shared/zensical/default_settings.yml` use Zensical and Material
  options, and `WebsiteSettings` knows the `nav` key;
- the templates: `shared/zensical/html_templates/` override the Material theme, including the menu of
  versions and the "no longer maintained" banner. `header.html` and `nav.html` copy the theme's files, and
  `header.html` adds a cross to the search: compare them with the theme when Zensical is updated;
- the folders of a version (`VersionBuilder`, `VersionPreparer`): a folder of Markdown pages read by the tool and a folder
  where it writes the site.

A close tool (MkDocs, Material for MkDocs) needs a new implementation and a check of the options and templates.
A different tool also means redoing the settings, the templates and the search.

## Good to know

- Links starting with `/` that lead to a file of the documentation are made relative in the build; the
  Markdown of your repository is not changed.
- A build that fails keeps the previous website: the versions are all built before the first one is put in it.
- A version built alone replaces only its own folder. The folder of a version that is no longer declared stays
  until you delete it.
- After adding a version or moving `is_latest`, build every version: the menu of versions and the "no longer
  maintained" banner of the others are written when they are built.
- Deploy `websites/build` as it is: the search links between websites are relative.
