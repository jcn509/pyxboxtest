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

# TODO: expand the docstrings. Refactor duplicated code
# TODO: add tests around creating/deleting/renaming files when there are multiple files/directories on disk
# TODO: test rename/deletion/creation with nested directories
# TODO: test renaming directories that have content


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


@pytest.mark.parametrize("file_path", ("/C/test.txt", "/E/file"))
def test_file_deletion(xqemu_blank_hdd_template: XQEMUHDDTemplate, file_path: str):
    """Ensures that files can be deleted from the HDD"""
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

        modifier.delete_file_from_xbox(file_path)
        assert (
            modifier.get_xbox_directory_contents(parent_path) == []
        ), f"{file_path} empty"


@pytest.mark.parametrize(
    "original_file_path,new_file_path",
    (("/C/test.txt", "/X/other.bat"), ("/E/file", "/E/renamed.bat")),
)
def test_file_rename(
    xqemu_blank_hdd_template: XQEMUHDDTemplate,
    original_file_path: str,
    new_file_path: str,
):
    """Ensures that files can be renamed/moved on the same partition or to
    another partition
    """
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    file_contents_to_write = _create_random_string()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        modifier.add_file_to_xbox(
            original_file_path, BytesIO(file_contents_to_write.encode("utf8"))
        )

        original_parent_path, original_filename = _xbox_path_split(original_file_path)
        assert modifier.get_xbox_directory_contents(original_parent_path) == [
            original_filename
        ], f"original directory: {original_parent_path} contains only {original_filename}"

        new_parent_path, new_filename = _xbox_path_split(new_file_path)
        if new_parent_path != original_parent_path:
            assert (
                modifier.get_xbox_directory_contents(new_parent_path) == []
            ), f"new directory: {new_parent_path} contains nothing"

        modifier.rename_file_on_xbox(original_file_path, new_file_path)

        assert modifier.get_xbox_directory_contents(new_parent_path) == [
            new_filename
        ], f"new directory: {new_parent_path} contains only {new_filename}"

        if new_parent_path != original_parent_path:
            assert (
                modifier.get_xbox_directory_contents(original_parent_path) == []
            ), f"original directory: {original_parent_path} contains nothing"

        content = modifier.get_xbox_file_contents(new_file_path).read()
        file_contents_read = content.decode("utf8")
        assert (
            file_contents_to_write == file_contents_read
        ), "File contents unaffected by upload/download"


@pytest.mark.parametrize(
    "original_file_path,new_file_path",
    (("/C/test.txt", "/X/other.bat"), ("/E/file", "/E/renamed.bat")),
)
def test_file_copy(
    xqemu_blank_hdd_template: XQEMUHDDTemplate,
    original_file_path: str,
    new_file_path: str,
):
    """Ensures that files can be copied on the same partition or to
    another partition
    """
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    file_contents_to_write = _create_random_string()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        modifier.add_file_to_xbox(
            original_file_path, BytesIO(file_contents_to_write.encode("utf8"))
        )

        original_parent_path, original_filename = _xbox_path_split(original_file_path)
        assert modifier.get_xbox_directory_contents(original_parent_path) == [
            original_filename
        ], f"original directory: {original_parent_path} contains only {original_filename}"

        new_parent_path, new_filename = _xbox_path_split(new_file_path)
        if new_parent_path != original_parent_path:
            assert (
                modifier.get_xbox_directory_contents(new_parent_path) == []
            ), f"new directory: {new_parent_path} contains nothing"

        modifier.copy_file_on_xbox(original_file_path, new_file_path)

        assert modifier.get_xbox_directory_contents(new_parent_path) == [
            new_filename
        ], f"new directory: {new_parent_path} contains only {new_filename}"

        if new_parent_path != original_parent_path:
            assert modifier.get_xbox_directory_contents(original_parent_path) == [
                original_filename
            ], f"original directory: {original_parent_path} contains file still"

        new_file_content = modifier.get_xbox_file_contents(new_file_path).read()
        file_contents_read = new_file_content.decode("utf8")
        assert file_contents_to_write == file_contents_read, "New file contents correct"

        original_file_content = modifier.get_xbox_file_contents(
            original_file_path
        ).read()
        file_contents_read = original_file_content.decode("utf8")
        assert (
            file_contents_to_write == file_contents_read
        ), "'Original file contents unaffected'"


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

        assert modifier.get_xbox_directory_contents("/C/") == [
            "foo"
        ], "directory exists before"

        modifier.delete_directory_from_xbox("/C/foo/")

        assert (
            modifier.get_xbox_directory_contents("/C/") == []
        ), "directory was deleted"


def test_delete_directory_with_content(xqemu_blank_hdd_template: XQEMUHDDTemplate):
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        modifier.add_directory_to_xbox("/E/dir/")
        modifier.add_file_to_xbox(
            "/E/dir/file.txt", BytesIO(f"some content".encode("utf8"))
        )
        assert modifier.get_xbox_directory_contents("/E/") == [
            "dir"
        ], "directory exists before"
        assert modifier.get_xbox_directory_contents("/E/dir/") == [
            "file.txt"
        ], "file exists before"

        modifier.delete_directory_from_xbox("/E/dir/")

        assert (
            modifier.get_xbox_directory_contents("/E/") == []
        ), "directory and file were both deleted"


@pytest.mark.parametrize(
    "original_directory_path,new_directory_path",
    (
        pytest.param(
            "/C/test/",
            "/E/dir/",
            marks=pytest.mark.skip(reason="Can't currently move across drives"),
        ),
        ("/C/orig/", "/C/new/"),
    ),
)
def test_directory_rename(
    xqemu_blank_hdd_template: XQEMUHDDTemplate,
    original_directory_path: str,
    new_directory_path: str,
):
    """Ensures that directories can be renamed/moved on the same partition or
    to another partition
    """
    hdd_image = xqemu_blank_hdd_template.create_fresh_hdd()
    with XQEMUHDDImageModifer(hdd_image) as modifier:
        modifier.add_directory_to_xbox(original_directory_path)

        original_parent_path, original_directory = _xbox_path_split(
            original_directory_path
        )
        assert modifier.get_xbox_directory_contents(original_parent_path) == [
            original_directory
        ], f"original directory: {original_parent_path} contains only {original_directory}"

        new_parent_path, new_directory = _xbox_path_split(new_directory_path)
        if new_parent_path != original_parent_path:
            assert (
                modifier.get_xbox_directory_contents(new_parent_path) == []
            ), f"new directory: {new_parent_path} is empty"

        modifier.rename_directory_on_xbox(original_directory_path, new_directory_path)
        assert modifier.get_xbox_directory_contents(new_parent_path) == [
            new_directory
        ], f"new directory: {new_parent_path} contains only {new_directory}"

        if new_parent_path != original_parent_path:
            assert (
                modifier.get_xbox_directory_contents(new_parent_path) == []
            ), f"original directory: {original_parent_path} is empty"


def test_get_xbox_drives(xqemu_blank_hdd_template: XQEMUHDDTemplate):
    with XQEMUHDDImageModifer(xqemu_blank_hdd_template.create_fresh_hdd()) as modifier:
        assert modifier.get_xbox_drives() == ["C", "E", "F", "X", "Y", "Z"]
