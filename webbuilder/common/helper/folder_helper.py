"""
The operations on folders the website builder needs: copying a folder and deleting a folder. This is
the only place that uses shutil, so every class works on folders the same way.
"""

import os
import shutil
import stat
from collections.abc import Callable
from pathlib import Path


class FolderHelper:
    """Copies and deletes folders."""

    # -- Public: folders -----------------------------------------------------------------------------

    @staticmethod
    def copy_folder(source_folder: Path, destination_folder: Path) -> None:
        """Copies the source folder and what it contains into the destination folder, replacing existing files."""
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)


    @staticmethod
    def delete_folder(folder: Path) -> None:
        """
        Deletes the folder and what it contains, if it exists. Git writes read-only files in a clone,
        which Windows refuses to delete as they are, so they are made writable first.
        """
        if folder.exists():
            shutil.rmtree(folder, onerror=FolderHelper._retry_after_making_writable)


    # -- Private: deleting ---------------------------------------------------------------------------

    @staticmethod
    def _retry_after_making_writable(delete_function: Callable[[str], None], path: str, _error: object) -> None:
        """Called by shutil.rmtree when it cannot delete a path: makes the path writable and deletes it again."""
        os.chmod(path, stat.S_IWRITE)
        delete_function(path)
