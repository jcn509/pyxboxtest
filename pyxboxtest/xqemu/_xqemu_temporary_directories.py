"""Manages all the temporary directories used through this library

Uses the directory given by pytest as the root
"""
from typing import NamedTuple


class _TemporaryDirectories(NamedTuple):
    """Immutable storage for the temporary directories"""

    hdd_images_dir: str
    hdd_templates_dir: str
    screenshots_dir: str


def get_temp_dirs() -> _TemporaryDirectories:
    """Get the storage locations of all the temporary files created during
    test runs
    """
    if get_temp_dirs._temporary_directories is None:
        raise RuntimeError(
            "Tried to get temp dirs before the base directory was set!"
            "Are you doing something globally that should be done in a fixture?"
        )
    return get_temp_dirs._temporary_directories


get_temp_dirs._temporary_directories = None


def _initialise_temp_dirs(tmp_path_factory) -> None:
    """Never call this directly! It is for use by the pytest plugin only!

    Initialises the storage temporary storage directories used by pyxboxtest
    """
    get_temp_dirs._temporary_directories = _TemporaryDirectories(
        tmp_path_factory.mktemp("xqemu_hdd_images", numbered=False),
        tmp_path_factory.mktemp("xqemu_hdd_template_images", numbered=False),
        tmp_path_factory.mktemp("xqemu_screenshots", numbered=False),
    )
