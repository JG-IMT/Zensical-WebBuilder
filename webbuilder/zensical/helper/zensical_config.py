import yaml
import copy

class ZensicalConfig:
    """The config file of Zensical for one site: the settings it is given, completed with the options of this site."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, config_file: Path) -> None:
        self._config_file: Path = config_file


    # -- Public: writing -----------------------------------------------------------------------------

    def write(
        self,
        base_settings: dict,
        site_url: str,
        docs_dir: str,
        site_dir: str,
        templates_folder: Path,
        nav: list | None,
        extra: dict,
    ) -> Path:
        """
        Writes the base settings completed with: the address of the site (site_url), the folder Zensical reads
        the pages from (docs_dir) and the one it writes the site in (site_dir) - both relative to the config file -,
        the folder of the HTML templates, the menu (nav, if any) and the keys added to 'extra'. Returns the file.
        """
        config: dict = copy.deepcopy(base_settings)
        config["site_url"] = site_url
        config["docs_dir"] = docs_dir
        config["site_dir"] = site_dir
        config["theme"]["custom_dir"] = Path(os.path.relpath(templates_folder, self._config_file.parent)).as_posix()
        config.setdefault("extra", {}).update(extra)
        if nav:
            config["nav"] = nav

        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        self._config_file.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return self._config_file