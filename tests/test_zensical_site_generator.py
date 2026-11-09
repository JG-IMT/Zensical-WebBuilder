"""Tests of Zensical used as the tool that builds the sites, without running Zensical."""

from pathlib import Path

import pytest
import yaml

from webbuilder.common.search_index_interface import SearchIndexInterface
from webbuilder.zensical import zensical_site_generator
from webbuilder.zensical.zensical_site_generator import ZensicalSiteGenerator


def _build_site(generator: ZensicalSiteGenerator, work_folder: Path) -> bool:
    return generator.build_site(
        settings={"site_name": "Demo", "theme": {"name": "material"}},
        site_url="https://example.org/1.0/",
        pages_folder=work_folder.joinpath("pages"),
        site_folder=work_folder.joinpath("site"),
        work_folder=work_folder,
        side_menu=["index.md"],
        template_values={"displayed_version": "1.0"},
    )


class FakeZensicalBuild:
    """Stands for ZensicalBuild: succeeds or fails without running Zensical."""

    succeeds: bool = True

    def __init__(self, config_file: Path) -> None:
        pass

    def run(self) -> bool:
        return self.succeeds


@pytest.fixture(autouse=True)
def fake_zensical_build(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(zensical_site_generator, "ZensicalBuild", FakeZensicalBuild)
    FakeZensicalBuild.succeeds = True


def test_writes_the_config_of_zensical_next_to_the_work_folder(tmp_path: Path) -> None:
    assert _build_site(ZensicalSiteGenerator(tmp_path.joinpath("templates")), tmp_path.joinpath("work")) is True

    config: dict = yaml.safe_load(tmp_path.joinpath("work", "zensical_config.yml").read_text(encoding="utf-8"))
    assert (config["docs_dir"], config["site_dir"]) == ("pages", "site")  # relative to the config file
    assert config["theme"]["custom_dir"] == "../templates"
    assert (config["site_url"], config["nav"], config["extra"]) == ("https://example.org/1.0/", ["index.md"], {"displayed_version": "1.0"})


def test_reports_a_failure_of_zensical(tmp_path: Path) -> None:
    FakeZensicalBuild.succeeds = False

    assert _build_site(ZensicalSiteGenerator(tmp_path), tmp_path.joinpath("work")) is False


def test_reads_the_search_index_zensical_writes(tmp_path: Path) -> None:
    generator: ZensicalSiteGenerator = ZensicalSiteGenerator(tmp_path)
    index_file: Path = tmp_path.joinpath(generator.get_search_index_file_name())
    index_file.write_text('{"config": {}, "items": [{"location": "a/", "title": "A"}]}', encoding="utf-8")

    index: SearchIndexInterface = generator.read_search_index(index_file)

    assert generator.get_search_index_file_name() == "search.json"
    assert index.get_items() == [{"location": "a/", "title": "A"}]
