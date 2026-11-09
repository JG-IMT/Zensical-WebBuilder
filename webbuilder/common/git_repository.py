"""
The git operations of the website builder, run with the git command of the machine: cloning one version of a
repository at its git reference. A failure stops the build with one line, naming what failed.
"""

import os
import subprocess
from pathlib import Path


class GitRepository:
    """Git operations on a repository: cloning it at a git reference."""

    # -- Public: initialization ----------------------------------------------------------------------

    def __init__(self, repository_url: str) -> None:
        self._repository_url: str = repository_url  # an address, or a folder on this machine


    # -- Public: clone -------------------------------------------------------------------------------

    def clone_at(self, git_ref: str, destination_folder: Path) -> None:
        """Clones only the latest state of a branch or a tag (shallow), which is all the build needs."""
        clone_arguments: list[str] = [
            "clone",
            "--quiet",            # git prints nothing, the build prints what matters
            "--depth", "1",       # only the latest state of the git reference, not the whole history
            "--branch", git_ref,  # a branch or a tag
            self._repository_url,
            str(destination_folder),
        ]
        clone_result: subprocess.CompletedProcess = self._run_git(clone_arguments)
        if clone_result.returncode != 0:
            raise SystemExit(f"Cannot clone {self._repository_url} at '{git_ref}': {clone_result.stderr.strip()}")


    # -- Private: git --------------------------------------------------------------------------------

    @staticmethod
    def _run_git(arguments: list[str]) -> subprocess.CompletedProcess:
        """Runs git with the arguments and gives its result. Stops the build if git is not installed."""
        git_environment: dict = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}  # fail instead of waiting for a password
        git_command: list[str] = ["git", "-c", "core.longpaths=true"] + arguments  # longpaths: Windows paths over 260
        try:
            return subprocess.run(git_command, capture_output=True, text=True, env=git_environment)
        except FileNotFoundError:
            raise SystemExit("git is not installed or not in the PATH")
