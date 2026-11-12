# search

This folder gives the search of each website the pages of the other websites.

- `global_search.py` holds `GlobalSearch`, which replaces the search index of each built website by the merge of the indexes of all the built websites.

For each built website, `GlobalSearch` works in three steps (step 6 of a build):

1. It copies the index of the latest version, `search.json`, to `website_search.json` next to it, unless this copy already exists.
2. It takes the pages of every other website from their `website_search.json`, with a path relative to this website and the name of their website before the title.
3. It rewrites `search.json` with the pages of the website followed by the pages of the others.

Only the latest version of each website is searched: an earlier version only searches its own pages.

`GlobalSearch` always starts from `website_search.json`, so merging again never adds the same pages twice. Rebuilding the latest version replaces its folder, and the next merge makes `website_search.json` again from the new `search.json`.

A website that is not built yet is skipped. The websites must stay side by side in the folder of the built websites, because the paths between them are relative.
