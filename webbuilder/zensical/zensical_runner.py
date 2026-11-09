"""
Runs Zensical on a config file: `zensical build`, with the Zensical installed for the Python running the
website builder.
"""

import subprocess
import sys
from pathlib import Path


class ZensicalRunner:
    """The build of one site by Zensical."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, config_file: Path) -> None:
        self._config_file: Path = config_file


    # -- Public: entry point -------------------------------------------------------------------------

    def run(self) -> bool:
        """Builds the site described by the config file. Returns False if Zensical fails."""
        zensical_result: subprocess.CompletedProcess = subprocess.run(
            [sys.executable, "-m", "zensical", "build", "--clean", "-f", str(self._config_file)]
        )
        return zensical_result.returncode == 0
