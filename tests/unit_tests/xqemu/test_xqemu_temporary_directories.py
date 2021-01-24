"""Some basic sanity checks to make sure that the directories are initialised correctly"""
import os

from pyxboxtest.xqemu._xqemu_temporary_directories import get_temp_dirs


def test_temp_directories_are_different():
    """Sanity check to make sure that the directories are all unique"""
    assert len(get_temp_dirs()) == len(set(get_temp_dirs()))


def test_temp_directories_exist():
    """Sanity check to make sure that the directories actually exist"""
    assert all(os.path.isdir(temp_dir) for temp_dir in get_temp_dirs())
