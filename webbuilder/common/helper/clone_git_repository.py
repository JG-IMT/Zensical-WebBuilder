"""
This class clones one version of a git repository at its git reference, with the git command of the machine.

A failure stops the build with one line, naming what failed.

Used at step 2 (clone a version), once per version.
"""

import os
import subprocess
from pathlib import Path


class CloneGitRepository:
    """This class clones a git repository at a git reference."""

    # == Public ====================================================================================

    # -- Initialization ----------------------------------------------------------------------------

    def __init__(self, repository_url: str) -> None:
        """This constructor sets the repository to clone: an address, or a folder on this machine."""
        self._repository_url: str = repository_url


    # -- Entry point -------------------------------------------------------------------------------

    def clone_at(self, git_ref: str, destination_folder: Path) -> None:
        """This method clones only the latest state of a branch or a tag, and stops the build if git fails."""
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


    # == Private ===================================================================================

    @staticmethod
    def _run_git(arguments: list[str]) -> subprocess.CompletedProcess:
        """This method runs git and returns its result, and stops the build if git is missing."""
        git_environment: dict = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}  # fail instead of waiting for a password
        git_command: list[str] = ["git", "-c", "core.longpaths=true"] + arguments  # longpaths: Windows paths over 260
        try:
            return subprocess.run(git_command, capture_output=True, text=True, env=git_environment)
        except FileNotFoundError:
            raise SystemExit("git is not installed or not in the PATH")
