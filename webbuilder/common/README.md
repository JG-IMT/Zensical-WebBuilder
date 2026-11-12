# common

This package gives the tools that `builder/` and `zensical/` share. It knows neither Zensical nor the rules of OpenFlexo.

- `helper/clone_git_repository.py` holds `CloneGitRepository`, which clones a version of a repository at its git reference.
- `helper/folder_helper.py` holds `FolderHelper`, which copies and deletes folders. It is the only code that uses `shutil`.
- `openflexo_interfaces.py` holds two interfaces: `SiteGeneratorInterface` builds a site from a folder of pages, and `SearchIndexInterface` describes the search index of one site.

The package `builder/` knows the site generator only through these two interfaces, and the package `zensical/` implements them.
