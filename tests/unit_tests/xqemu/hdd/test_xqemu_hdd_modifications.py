"""Test for the subclasses of :py:class:`pyxboxtest.xqemu.hdd.HDDModification`

Ensures that they actually perform the operations that they are designed
to perform (adding files, removing files, etc).

Note: these tests only ensure that they make the correct calls to the classes
that will actually perform the changes. They don't check the contents of any
HDDs...
"""
import pytest

from pyxboxtest.xqemu.hdd.xqemu_hdd_modifications import HDDModification
from pyxboxtest.xqemu.hdd._xqemu_hdd_template_modifier import _XQEMUHDDTemplateModifier
from pyxboxtest.xqemu.hdd import AddFile, BatchModification, DeleteFile, RenameFile


@pytest.fixture
def mock_xqemu_hdd_template_modifier(mocker):
    """We don't want to launch an instance of XQEMU and actually modify a HDD
    so we need to mock out the class that does the actual modifications:
    :py:class:`pyxboxtest.xqemu.hdd._xqemu_hdd_template_modifier._XQEMUHDDTemplateModifier`
    """
    return mocker.Mock(_XQEMUHDDTemplateModifier)


@pytest.mark.parametrize(
    "local_filename, xbox_filename", (("a", "b"), ("local", "xbox"))
)
def test_add_file(
    local_filename: str, xbox_filename: str, mock_xqemu_hdd_template_modifier
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.AddFile` actually adds the file
    to the HDD
    """
    AddFile(local_filename, xbox_filename).perform_modification(
        mock_xqemu_hdd_template_modifier
    )
    mock_xqemu_hdd_template_modifier.add_file.assert_called_once_with(
        local_filename, xbox_filename
    )


@pytest.mark.parametrize("filename", ("file1", "file2"))
def test_delete_file(filename: str, mock_xqemu_hdd_template_modifier):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.DeleteFile` actually deletes the
    file from the HDD
    """
    DeleteFile(filename).perform_modification(mock_xqemu_hdd_template_modifier)
    mock_xqemu_hdd_template_modifier.delete_file.assert_called_once_with(filename)


@pytest.mark.parametrize("old_filename, new_filename", (("a", "b"), ("local", "xbox")))
def test_rename_file(
    old_filename: str, new_filename: str, mock_xqemu_hdd_template_modifier
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.RenameFile` actually renames the
    file on the HDD
    """
    RenameFile(old_filename, new_filename).perform_modification(
        mock_xqemu_hdd_template_modifier
    )
    mock_xqemu_hdd_template_modifier.rename_file.assert_called_once_with(
        old_filename, new_filename
    )


@pytest.mark.parametrize("num_modifications", tuple(range(1, 10)))
def test_batch_modification(
    num_modifications: int, mock_xqemu_hdd_template_modifier, mocker
):
    """Ensures that :py:class:`pyxboxtest.xqemu.hdd.BatchModifcation` actually
    performs the sequence of modifications that it was created for
    """
    modifications = tuple(
        mocker.Mock(HDDModification) for _ in range(num_modifications)
    )
    BatchModification(modifications).perform_modification(
        mock_xqemu_hdd_template_modifier
    )
    for modification in modifications:
        modification.perform_modification.assert_called_once_with(
            mock_xqemu_hdd_template_modifier
        )
