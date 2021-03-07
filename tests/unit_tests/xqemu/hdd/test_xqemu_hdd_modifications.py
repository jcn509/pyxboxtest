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
    AddFile,
    BatchModification,
    DeleteFile,
    RenameFile,
    XQEMUHDDImageModifer,
)


@pytest.fixture
def mockxqemu_hdd_image_modifier(mocker):
    """We don't want to launch an instance of XQEMU and actually modify a HDD
    so we need to mock out the class that does the actual modifications:
    :py:class:`pyxboxtest.xqemu.hdd.xqemu_hdd_image_modifier.XQEMUHDDImageModifer`
    """
    return mocker.Mock(XQEMUHDDImageModifer)


@pytest.mark.parametrize(
    "local_filename, file_contents",
    (("a", "b"), (StringIO("content"), StringIO("other"))),
)
def test_add_file(
    local_filename: str, file_contents: StringIO, mockxqemu_hdd_image_modifier
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.AddFile` actually adds the file
    to the HDD
    """
    AddFile(local_filename, file_contents).perform_modification(
        mockxqemu_hdd_image_modifier
    )
    mockxqemu_hdd_image_modifier.add_file_to_xbox.assert_called_once_with(
        local_filename, file_contents
    )


@pytest.mark.parametrize("filename", ("file1", "file2"))
def test_delete_file(filename: str, mockxqemu_hdd_image_modifier):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.DeleteFile` actually deletes the
    file from the HDD
    """
    DeleteFile(filename).perform_modification(mockxqemu_hdd_image_modifier)
    mockxqemu_hdd_image_modifier.delete_file_from_xbox.assert_called_once_with(filename)


@pytest.mark.parametrize("old_filename, new_filename", (("a", "b"), ("local", "xbox")))
def test_rename_file(
    old_filename: str, new_filename: str, mockxqemu_hdd_image_modifier
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.RenameFile` actually renames the
    file on the HDD
    """
    RenameFile(old_filename, new_filename).perform_modification(
        mockxqemu_hdd_image_modifier
    )
    mockxqemu_hdd_image_modifier.rename_file_on_xbox.assert_called_once_with(
        old_filename, new_filename
    )


@pytest.mark.parametrize("num_modifications", tuple(range(1, 10)))
def test_batch_modification(
    num_modifications: int, mockxqemu_hdd_image_modifier, mocker
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.BatchModifcation` actually
    performs the sequence of modifications that it was created for
    """
    modifications = tuple(
        mocker.Mock(HDDModification) for _ in range(num_modifications)
    )
    BatchModification(modifications).perform_modification(mockxqemu_hdd_image_modifier)
    for modification in modifications:
        modification.perform_modification.assert_called_once_with(
            mockxqemu_hdd_image_modifier
        )
