"""
This class copies and deletes folders for the whole tool.

It is the only place that uses shutil, so every class works on folders the same way.

Used at steps 2 to 5, wherever a folder is copied or deleted.
"""

import os
import shutil
import stat
from collections.abc import Callable
from pathlib import Path


class FolderHelper:
    """This class copies and deletes folders."""

    # == Public ====================================================================================

    @staticmethod
    def copy_folder(source_folder: Path, destination_folder: Path) -> None:
        """This method copies the source folder and what it contains into the destination folder, replacing existing files."""
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)


    @staticmethod
    def delete_folder(folder: Path) -> None:
        """
        This method deletes the folder and what it contains, if it exists. Git writes read-only files in a clone,
        which Windows refuses to delete as they are, so they are made writable first.
        """
        if folder.exists():
            shutil.rmtree(folder, onerror=FolderHelper._retry_after_making_writable)


    # == Private ===================================================================================

    @staticmethod
    def _retry_after_making_writable(delete_function: Callable[[str], None], path: str, _error: object) -> None:
        """This method is called when shutil.rmtree cannot delete a path: it makes the path writable and retries."""
        os.chmod(path, stat.S_IWRITE)
        delete_function(path)
