"""Tests for :py:class:`~pyxboxtest.xqemu.xqemu_hdd_cloner`"""
import os
import subprocess
from typing import Tuple

import pytest

from pyxboxtest.xqemu.hdd import (
    XQEMUHDDTemplate,
    AddFile,
    DeleteFile,
    HDDModification,
    RenameFile,
)

# Note: there are deliberately spaces in the name, just to make sure that is OK.
# This is seperate from the main image to avoid bugs in the code affecting the
# main image without anyone realising.
_TEST_BLANK_HDD_IMAGE = os.path.join(
    os.path.dirname(__file__), "blank hdd image for tests.qcow2"
)


@pytest.fixture
def mocked_subprocess_popen(mocker):
    """We don't really want to spawn new processes"""
    mocker.patch("subprocess.Popen")


def _get_calls_to_qemu_img():
    """Get all sub process calls to qemu-img"""
    return [
        call for call in subprocess.Popen.call_args_list if "qemu-img" in call.args[0]
    ]


def _get_qemu_img_cow_copy_command(
    original_filename: str, new_file_name: str
) -> Tuple[str, ...]:
    """:returns: the qemu-img command that is used to create a copy on write
    copy of a HDD image
    """
    return (
        "qemu-img",
        "create",
        "-F",
        "qcow2",
        "-f",
        "qcow2",
        "-b",
        original_filename,
        new_file_name,
    )


def _get_hdd_template_path(template_name: str) -> str:
    """Get the full file path to a HDD template file"""
    # Have to delay this import until now, as when this script is first read
    # it won't yet have a value
    from pyxboxtest.xqemu.hdd.xqemu_hdd_template import _HDD_TEMPLATE_STORAGE_DIR

    return os.path.join(_HDD_TEMPLATE_STORAGE_DIR, template_name + ".qcow2")


def _get_hdd_image_path(template_name: str, hdd_number: int) -> str:
    """Get the full path to a HDD file (after creating it from a template
    :param hdd_number: 1 for the first image created from the template, \
        2 for the second etc.
    """
    # Have to delay this import until now, as when this script is first read
    # it won't yet have a value
    from pyxboxtest.xqemu.hdd.xqemu_hdd_template import _HDD_STORAGE_DIR

    return os.path.join(
        _HDD_STORAGE_DIR, str(hdd_number) + "-" + template_name + ".qcow2",
    )


@pytest.mark.usefixtures("mocked_subprocess_popen")
class TestWithoutCreatingImage:
    """Mock away the actual creation of the image
    subprocess.popen is mocked so qemu-img can't actually be called
    """

    @pytest.mark.parametrize(
        "template_name", ("template1", "sdfdsf", "template2", "test", "thing",),
    )
    def test_cant_create_template_that_exists(self, template_name: str, mocker):
        mocker.patch("os.path.isfile", lambda file: True)
        with pytest.raises(ValueError):
            XQEMUHDDTemplate(template_name, "whatever")

    @pytest.mark.parametrize(
        "template_name, base_image_filename",
        (
            ("template1", "file1"),
            ("template2", "file2"),
            ("template3", "file1"),
            ("template4", "file1"),
            ("template5", "file2"),
        ),
    )
    def test_correct_qemu_img_command(
        self, template_name: str, base_image_filename: str
    ):
        """Test the the correct qemu-img command is executed when creating the template"""
        XQEMUHDDTemplate(template_name, base_image_filename)
        expected_new_hdd_name = _get_hdd_template_path(template_name)
        calls_to_qemu_img = _get_calls_to_qemu_img()
        assert len(calls_to_qemu_img) == 1, "only 1 copy made"
        assert calls_to_qemu_img[0].args[0] == _get_qemu_img_cow_copy_command(
            base_image_filename, expected_new_hdd_name
        ), "Correct command executed to create HDD template from base image"

    @pytest.mark.parametrize(
        "child_template_name", ("template1", "template2", "template3",),
    )
    def test_create_child_template_correct_qemu_img_command(
        self, child_template_name: str
    ):
        """Tests that the correct qemu-img command is ran to create
        the child template from the parent template when using
        :py:func:`~pyxboxtest.xqemu.hdd.XQEMUHDDTemplate.create_child_template`
        """
        parent_template_name = "parent template"
        parent_template = XQEMUHDDTemplate(
            parent_template_name, "ignored hdd image name.qcow2"
        )
        parent_template.create_child_template(child_template_name, tuple())

        parent_template_path = _get_hdd_template_path(parent_template_name)
        child_template_path = _get_hdd_template_path(child_template_name)
        calls_to_qemu_img = _get_calls_to_qemu_img()
        assert len(calls_to_qemu_img) == 2, "Called once for parent and once for child"
        assert calls_to_qemu_img[1].args[0] == _get_qemu_img_cow_copy_command(
            parent_template_path, child_template_path
        ), "Correct command executed to create child HDD template"

    @pytest.mark.parametrize(
        "child_template_name, parent_hdd_modifications, child_hdd_modifications",
        (
            ("child", tuple(), (AddFile("test1", "test2"),)),
            ("template", (RenameFile("old", "new"),), tuple()),
            (
                "adads",
                (RenameFile("old", "new"), DeleteFile("test")),
                (AddFile("one", "two"), DeleteFile("3")),
            ),
        ),
    )
    def test_create_child_template_correct_parameters(
        self,
        mocker,
        child_template_name: str,
        parent_hdd_modifications: Tuple[HDDModification, ...],
        child_hdd_modifications: Tuple[HDDModification, ...],
    ):
        """Tests that the correct parameters are used when using
        :py:func:`~pyxboxtest.xqemu.hdd.XQEMUHDDTemplate.create_child_template`

        Ensures that the parent template image is the one that is passed as
        the base image to the child and that the modifications passed to it
        are all the modifications made to the parent followed by the extra
        ones for the child.
        """
        parent_template_name = "parent template"
        parent_template = XQEMUHDDTemplate(
            parent_template_name,
            "ignored hdd image name.qcow2",
            parent_hdd_modifications,
        )
        parent_template_path = _get_hdd_template_path(parent_template_name)

        # There is no doubt a cleaner way of doing this...
        mock_init = mocker.Mock()

        def init_replacement(self, a, b, c):
            mock_init(a, b, c)
            return None

        mocker.patch.object(XQEMUHDDTemplate, "__init__", init_replacement)
        parent_template.create_child_template(
            child_template_name, child_hdd_modifications
        )
        mock_init.assert_called_once_with(
            child_template_name,
            parent_template_path,
            parent_hdd_modifications + child_hdd_modifications,
        )

    @pytest.mark.parametrize(
        "template_name",
        ("template1", "template2", "template3", "template4", "template5"),
    )
    def test_create_fresh_hdd_correct_image_path_returned(self, template_name: str):
        """Tests that the correct path to the new HDD image is returned when
        using
        :py:func:`~pyxboxtest.xqemu.hdd.XQEMUHDDTemplate.create_fresh_hdd`
        The correct path includes the template name and total number of images
        created so far and the image is located in a temporary folder that
        has been set up to store all the HDD images.
        """
        template = XQEMUHDDTemplate(template_name, "ignored hdd image name.qcow2",)

        for child_num in range(1, 5):
            assert (
                _get_hdd_image_path(template_name, child_num)
                == template.create_fresh_hdd()
            )

    @pytest.mark.parametrize(
        "template_name",
        ("template1", "template2", "template3", "template4", "template5"),
    )
    def test_create_fresh_hdd_correct_qemu_img_command(self, template_name: str):
        """Tests that the correct qemu-img command is executed to create the
        new HDD image when using
        :py:func:`~pyxboxtest.xqemu.hdd.XQEMUHDDTemplate.create_fresh_hdd`
        """
        template = XQEMUHDDTemplate(template_name, "ignored hdd image name.qcow2",)
        template_hdd_path = _get_hdd_template_path(template_name)

        for hdd_num in range(1, 5):
            template.create_fresh_hdd()
            assert _get_calls_to_qemu_img()[-1].args[
                0
            ] == _get_qemu_img_cow_copy_command(
                template_hdd_path, _get_hdd_image_path(template_name, hdd_num)
            ), f"Correct command executed to create child HDD template for child number {hdd_num}"


class TestAndActuallyCreateImages:
    """Actually create the HDD template images using qemu-img"""

    @pytest.mark.parametrize(
        # Note: these names cannot match any other names used in tests
        # that actually create image files!
        "template_name",
        ("templatealreadyexists1", "templatealreadyexists2", "asdfexists"),
    )
    def test_cant_create_template_that_exists(self, template_name: str):
        """Ensure that you cannot create 2 templates with the same name"""
        XQEMUHDDTemplate(template_name, _TEST_BLANK_HDD_IMAGE)
        with pytest.raises(ValueError):
            XQEMUHDDTemplate(template_name, _TEST_BLANK_HDD_IMAGE)

    @pytest.mark.parametrize(
        # Note: these names cannot match any other names used in tests
        # that actually create image files!
        "template_name",
        ("template1", "template2", "template3"),
    )
    def test_template_actually_created(self, template_name: str):
        """Ensure that the qemu-img command actually creates the image in the
        correct place
        """
        XQEMUHDDTemplate(template_name, _TEST_BLANK_HDD_IMAGE)
        assert os.path.isfile(
            _get_hdd_template_path(template_name)
        ), "template actually created"

    @pytest.mark.usefixtures("xqemu_blank_hdd_template")
    def test_blank_xbox_hdd_template_created(self):
        """Ensures that the blank_hdd image is created in this correct place
        for :py:func:`~pyxboxtest.xqemu.hdd.xqemu_blank_hdd_template`
        """
        assert os.path.isfile(
            _get_hdd_template_path("blank_hdd")
        ), "template actually created"

    @pytest.mark.parametrize(
        # Note: these names cannot match any other names used in tests
        # that actually create image files!
        "template_name",
        ("templatenew1", "templatenew2", "templatenew3"),
    )
    def test_create_fresh_hdd_image_actually_created(self, template_name: str):
        """Tests that HDD images are actually created in the correct place
        when using
        :py:func:`~pyxboxtest.xqemu.hdd.XQEMUHDDTemplate.create_fresh_hdd`
        """
        template = XQEMUHDDTemplate(template_name, _TEST_BLANK_HDD_IMAGE)
        for hdd_num in range(1, 5):
            template.create_fresh_hdd()
            assert os.path.isfile(
                _get_hdd_image_path(template_name, hdd_num)
            ), f"HDD number {hdd_num} actually created"