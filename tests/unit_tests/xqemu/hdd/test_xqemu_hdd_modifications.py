"""Test for the subclasses of :py:class:`pyxboxtest.xqemu.hdd.HDDModification`

Ensures that they actually perform the operations that they are designed
to perform (adding files, removing files, etc).

Note: these tests only ensure that they make the correct calls to the classes
that will actually perform the changes. They don't check the contents of any
HDDs...
"""
from io import StringIO

import pytest

from pyxboxtest.xqemu.hdd.xqemu_hdd_modifications import HDDModification
from pyxboxtest.xqemu.hdd import (
    AddDirectory,
    AddFile,
    BatchModification,
    CopyFile,
    DeleteDirectory,
    DeleteFile,
    RenameDirectory,
    RenameFile,
    XQEMUHDDImageModifer,
)


@pytest.fixture
def mock_xqemu_hdd_image_modifier(mocker):
    """We don't want to launch an instance of XQEMU and actually modify a HDD
    so we need to mock out the class that does the actual modifications:
    :py:class:`pyxboxtest.xqemu.hdd.xqemu_hdd_image_modifier.XQEMUHDDImageModifer`
    """
    return mocker.Mock(XQEMUHDDImageModifer)


@pytest.mark.parametrize(
    "local_filename, file_contents",
    (("a", StringIO("content")), ("b", StringIO("other"))),
)
def test_add_file(
    local_filename: str, file_contents: StringIO, mock_xqemu_hdd_image_modifier
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.AddFile` actually adds the file
    to the HDD
    """
    AddFile(local_filename, file_contents).perform_modification(
        mock_xqemu_hdd_image_modifier
    )
    mock_xqemu_hdd_image_modifier.add_file_to_xbox.assert_called_once_with(
        local_filename, file_contents
    )


@pytest.mark.parametrize(
    "directory_path", (("a", "b"), (StringIO("content"), StringIO("other"))),
)
def test_add_directory(directory_path: str, mock_xqemu_hdd_image_modifier):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.AddDirectory` actually adds the directory
    to the HDD
    """
    AddDirectory(directory_path).perform_modification(mock_xqemu_hdd_image_modifier)
    mock_xqemu_hdd_image_modifier.add_directory_to_xbox.assert_called_once_with(
        directory_path
    )


@pytest.mark.parametrize("directory_path", ("file1", "file2"))
def test_delete_directory(directory_path: str, mock_xqemu_hdd_image_modifier):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.DeleteDirectory` actually deletes the
    file from the HDD
    """
    DeleteDirectory(directory_path).perform_modification(mock_xqemu_hdd_image_modifier)
    mock_xqemu_hdd_image_modifier.delete_directory_from_xbox.assert_called_once_with(
        directory_path
    )


@pytest.mark.parametrize("filename", ("file1", "file2"))
def test_delete_file(filename: str, mock_xqemu_hdd_image_modifier):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.DeleteFile` actually deletes the
    file from the HDD
    """
    DeleteFile(filename).perform_modification(mock_xqemu_hdd_image_modifier)
    mock_xqemu_hdd_image_modifier.delete_file_from_xbox.assert_called_once_with(
        filename
    )


@pytest.mark.parametrize("old_filename, new_filename", (("a", "b"), ("local", "xbox")))
def test_copy_file(old_filename: str, new_filename: str, mock_xqemu_hdd_image_modifier):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.CopyFile` actually copies the
    file on the HDD
    """
    CopyFile(old_filename, new_filename).perform_modification(
        mock_xqemu_hdd_image_modifier
    )
    mock_xqemu_hdd_image_modifier.copy_file_on_xbox.assert_called_once_with(
        old_filename, new_filename
    )


@pytest.mark.parametrize("old_filename, new_filename", (("a", "b"), ("local", "xbox")))
def test_rename_file(
    old_filename: str, new_filename: str, mock_xqemu_hdd_image_modifier
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.RenameFile` actually renames the
    file on the HDD
    """
    RenameFile(old_filename, new_filename).perform_modification(
        mock_xqemu_hdd_image_modifier
    )
    mock_xqemu_hdd_image_modifier.rename_file_on_xbox.assert_called_once_with(
        old_filename, new_filename
    )


@pytest.mark.parametrize("old_directory_path, new_directory_path", (("a", "b"), ("local", "xbox")))
def test_rename_directory(
    old_directory_path: str, new_directory_path: str, mock_xqemu_hdd_image_modifier
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.RenameDirectory` actually renames the
    directory on the HDD
    """
    RenameDirectory(old_directory_path, new_directory_path).perform_modification(
        mock_xqemu_hdd_image_modifier
    )
    mock_xqemu_hdd_image_modifier.rename_directory_on_xbox.assert_called_once_with(
        old_directory_path, new_directory_path
    )


@pytest.mark.parametrize("num_modifications", tuple(range(1, 10)))
def test_batch_modification(
    num_modifications: int, mock_xqemu_hdd_image_modifier, mocker
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.BatchModifcation` actually
    performs the sequence of modifications that it was created for
    """
    modifications = tuple(
        mocker.Mock(HDDModification) for _ in range(num_modifications)
    )
    BatchModification(modifications).perform_modification(mock_xqemu_hdd_image_modifier)
    for modification in modifications:
        modification.perform_modification.assert_called_once_with(
            mock_xqemu_hdd_image_modifier
        )
