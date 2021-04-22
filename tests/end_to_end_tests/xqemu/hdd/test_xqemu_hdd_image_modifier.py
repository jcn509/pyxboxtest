"""Test for the subclasses of
:py:class:`pyxboxtest.xqemu.hdd.xqemu_hdd_image_modifier.XQEMUHDDImageModifer`

"""
from io import BytesIO
import random
import string
from typing import NamedTuple

import pytest

from pyxboxtest.xqemu.hdd import XQEMUHDDTemplate
from pyxboxtest.xqemu.hdd.xqemu_hdd_image_modifier import XQEMUHDDImageModifer


def _create_random_string() -> str:
    """Gives us some random string"""
    allowed_chars = string.ascii_letters + string.punctuation
    str_size = random.randint(1, 100)
    rand_str = r"".join(random.choice(allowed_chars) for x in range(str_size))

    return rand_str


class XboxSplitPath(NamedTuple):
    """"""

    parent_path: str
    child: str


def _xbox_path_split(path: str) -> XboxSplitPath:
    """Take an Xbox file path and split it into its parent and child e.g.
    /C/foo/txt -> (/C/foo, txt)
    """
    path_components = path.rstrip("/").split("/")

    parent_path = "/".join(path_components[:-1]) + "/"
    child = path_components[-1]

    return XboxSplitPath(parent_path, child)


def test_blank_hdd_is_empty(xqemu_blank_hdd_template: XQEMUHDDTemplate):
    """Ensure that the built in blank HDD is empty"""
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        for drive in ("C", "E", "X", "Y", "Z"):
            assert not modifier.get_xbox_directory_contents(
                f"/{drive}/"
            ), "Drive {drive} is empty"


@pytest.mark.parametrize("file_path", ("/C/test.txt", "/E/file"))
def test_file_creation(xqemu_blank_hdd_template: XQEMUHDDTemplate, file_path: str):
    """Ensures that files can be correctly created on the HDD"""
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    file_contents_to_write = _create_random_string()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        modifier.add_file_to_xbox(
            file_path, BytesIO(file_contents_to_write.encode("utf8"))
        )

        parent_path, filename = _xbox_path_split(file_path)
        assert modifier.get_xbox_directory_contents(parent_path) == [
            filename
        ], f"{parent_path} contains only {filename}"

        content = modifier.get_xbox_file_contents(file_path).read()
        file_contents_read = content.decode("utf8")
        assert (
            file_contents_to_write == file_contents_read
        ), "File contents unaffected by upload/download"


@pytest.mark.parametrize("directory_path", ("/C/test/", "/E/dir/"))
def test_directory_creation(
    xqemu_blank_hdd_template: XQEMUHDDTemplate, directory_path: str
):
    """Ensures that directories can be correctly created on the HDD"""
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        modifier.add_directory_to_xbox(directory_path)

        parent_path, directory = _xbox_path_split(directory_path)
        assert modifier.get_xbox_directory_contents(parent_path) == [
            directory
        ], f"{parent_path} contains only {directory}"

def test_delete_empty_directory(xqemu_blank_hdd_template: XQEMUHDDTemplate):
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        modifier.add_directory_to_xbox("/C/foo/")
 
        assert modifier.get_xbox_directory_contents("/C/") == ["foo"], "directory exists before"

        modifier.delete_directory_from_xbox("/C/foo/")

        assert modifier.get_xbox_directory_contents("/C/") == [], "directory was deleted"


def test_delete_directory_with_content(xqemu_blank_hdd_template: XQEMUHDDTemplate):
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        modifier.add_directory_to_xbox("/E/dir/")
        modifier.add_file_to_xbox(
            "/E/dir/file.txt", BytesIO(f"some content".encode("utf8"))
        )
        assert modifier.get_xbox_directory_contents("/E/") == ["dir"], "directory exists before"
        assert modifier.get_xbox_directory_contents("/E/dir/") == ["file.txt"], "file exists before"

        modifier.delete_directory_from_xbox("/E/dir/")

        assert modifier.get_xbox_directory_contents("/E/") == [], "directory and file were both deleted"

