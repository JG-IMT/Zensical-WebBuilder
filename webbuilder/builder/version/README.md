# version

This folder reads one version, builds it and fixes the links of its pages.

- `version_settings.py` holds two classes: `VersionSettings` reads and checks the settings of one version, and `VersionList` holds the versions of a website and tells where each one is.
- `version_builder.py` holds `VersionBuilder`, which builds one version from a clone of its git reference, and `VersionPreparer`, which fills the folder of pages. It also holds the function `template_values_of`, which returns the values that the HTML templates read.
- `helper/url_resolver.py` holds `UrlResolver`, which decides where a URL starting with "/" must point.
- `helper/url_rewriter.py` holds `UrlRewriter`, which rewrites the URLs starting with "/" in the copies of the Markdown pages.

`VersionBuilder` builds a version in three steps:

1. It clones the git reference of the version into `version_clone/` (step 2 of a build).
2. `VersionPreparer` copies the style and the sources into `version_pages/` and writes `versions.json`, the list of versions that the menu of every page reads. `UrlRewriter` fixes the links in the copies, with the help of `UrlResolver` (step 3).
3. `VersionBuilder` asks the site generator to build the site into `version_site/` (step 4), then deletes the clone, even if the build fails.

The pages and the site stay in `preparation/version_builds/<version>/`, so that you can see what the site generator was given and what it produced.
