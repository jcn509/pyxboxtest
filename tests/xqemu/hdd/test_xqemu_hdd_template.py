"""Tests for :py:class:`~pyxboxtest.xqemu.hdd.XQEMUHDDTemplate`"""
import os
import subprocess
from typing import Tuple

import pytest

from pyxboxtest.xqemu._xqemu_temporary_directories import get_temp_dirs
from pyxboxtest.xqemu.hdd import (
    XQEMUHDDTemplate,
    AddFile,
    DeleteFile,
    HDDModification,
    RenameFile,
)

# Has to be done unfortuneately
# pylint: disable=import-outside-toplevel

# Grouped into classes as a way to organise the tests
# pylint: disable=no-self-use

# Note: there are deliberately spaces in the name, just to make sure that is OK.
# This is seperate from the main image to avoid bugs in the code affecting the
# main image without anyone realising.
_TEST_BLANK_HDD_IMAGE = os.path.join(
    os.path.dirname(__file__), "blank hdd image for tests.qcow2"
)


@pytest.fixture(autouse=True)
def mock_xqemu_hdd_template_modifier(mocker):
    """We don't want to launch an instance of XQEMU and actually modify a HDD
    """
    return mocker.patch(
        "pyxboxtest.xqemu.hdd.xqemu_hdd_template._XQEMUHDDTemplateModifier"
    )


@pytest.fixture(autouse=True)
def mock_xqemu_hdd_modification_for_use_in_this_moduke(mocker):
    """Mock all instances of subclasses of
    :py:class:`~`pyxboxtest.xqemu.hdd.HDDModification` for instantiation in
    these tests
    """
    mocker.patch.object(AddFile, "perform_modification")
    mocker.patch.object(DeleteFile, "perform_modification")
    mocker.patch.object(RenameFile, "perform_modification")


def _get_calls_to_qemu_img():
    """Get all sub process calls to qemu-img"""
    return [
        call
        for call in subprocess.Popen.call_args_list  # pytype: disable=attribute-error # pylint: disable=no-member
        if "qemu-img" in call.args[0]
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
    return os.path.join(get_temp_dirs().hdd_templates_dir, template_name + ".qcow2")


def _get_hdd_image_path(template_name: str, hdd_number: int) -> str:
    """Get the full path to a HDD file (after creating it from a template
    :param hdd_number: 1 for the first image created from the template, \
        2 for the second etc.
    """
    return os.path.join(
        get_temp_dirs().hdd_images_dir,
        str(hdd_number) + "-" + template_name + ".qcow2",
    )


@pytest.mark.usefixtures("mocked_subprocess_popen")
class TestWithoutCreatingImage:
    """Mock away the actual creation of the image
    subprocess.popen is mocked so qemu-img can't actually be called
    """

    @pytest.mark.parametrize(
        "template_name", ("template1", "sdfdsf", "template2", "test", "thing",),
    )
    def test_cant_create_2_templates_with_same_name(self, template_name: str, mocker):
        """Tests that it is not possible to create 2 templates with the same name"""
        mocker.patch("os.path.isfile", lambda file: True)
        with pytest.raises(ValueError):
            XQEMUHDDTemplate(template_name, "whatever")

    def test_no_modifications_no_modifier_created(
        self, mock_xqemu_hdd_template_modifier
    ):
        """Ensure that if no modifications are wanted, we do not bother
        instantiating a modifer
        """
        XQEMUHDDTemplate("any template name", "whatever")
        mock_xqemu_hdd_template_modifier.assert_not_called()

    @pytest.mark.parametrize(
        "template_name, hdd_modifications",
        (
            ("template1", (AddFile("test1", "test2"),)),
            ("asdasd", (RenameFile("old", "new"),)),
            ("template2", (RenameFile("old", "new"), DeleteFile("test"))),
            ("testtesttest", (AddFile("one", "two"), DeleteFile("3"))),
        ),
    )
    def test_modifications_applied_correctly(
        self,
        template_name: str,
        hdd_modifications: Tuple[HDDModification],
        mock_xqemu_hdd_template_modifier,
    ):
        """Ensure that a modifier for the template is created if we want
        modifications to be made
        """
        XQEMUHDDTemplate(template_name, "whatever", hdd_modifications)
        print(
            dir(mock_xqemu_hdd_template_modifier),
            mock_xqemu_hdd_template_modifier.method_calls,
        )
        mock_xqemu_hdd_template_modifier.assert_called_once_with(
            _get_hdd_template_path(template_name)
        )
        for hdd_modification in hdd_modifications:
            # pytype: disable=attribute-error # pylint: disable=no-member
            hdd_modification.perform_modification.assert_called_once_with(
                mock_xqemu_hdd_template_modifier.return_value.__enter__.return_value
            )
            # pytype: enable=attribute-error # pylint: enable=no-member

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
        the base image to the child and that the correct modifications are
        applied to the child.
        """
        parent_template_name = "parent template"
        parent_template = XQEMUHDDTemplate(
            parent_template_name,
            "ignored hdd image name.qcow2",
            parent_hdd_modifications,
        )
        parent_template_path = _get_hdd_template_path(parent_template_name)

        mock_init = mocker.patch.object(XQEMUHDDTemplate, "__init__", return_value=None)
        parent_template.create_child_template(
            child_template_name, child_hdd_modifications
        )
        # The child should only recieve the child_hdd_modifications as the
        # parent_hdd_modifications havs already been applied to the image
        # that it recieves.
        mock_init.assert_called_once_with(
            child_template_name, parent_template_path, child_hdd_modifications,
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
    def test_cant_create_2_templates_with_same_name(self, template_name: str):
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
