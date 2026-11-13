# website

This folder reads a website, builds it from its versions and tells where its built files are.

- `website_settings.py` holds `WebsiteSettings`, which reads the settings and the versions of a website and checks them.
- `website_builder.py` holds `WebsiteBuilder`, which builds the versions of a website and puts each one in its folder.
- `built_website.py` holds `BuiltWebsite`, which gives the place of each file of a built website and writes its redirection page.
- `helper/website_scanner.py` holds `WebsiteScanner`, which finds the websites of the websites folder.

The classes work together in three steps:

1. `WebsiteScanner` finds one folder per website, and `WebsiteSettings` reads the settings file and the version files of each one (step 1 of a build).
2. `WebsiteBuilder` asks `VersionBuilder`, from the folder `version/`, to build each version (steps 2 to 4).
3. `WebsiteBuilder` copies each built version into the folder that `BuiltWebsite` gives, then the latest version into `latest/`, and `BuiltWebsite` writes `versions.json` and the page that redirects to the latest version (step 5).

`WebsiteSettings` represents a website before its build, and `BuiltWebsite` represents the same website after it.
