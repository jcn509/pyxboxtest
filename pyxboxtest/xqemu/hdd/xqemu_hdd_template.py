"""Manage the use of XQEMU HDD images"""
from __future__ import (
    annotations,
)  # To allow a type hint on a method to be of the enclosing class
import logging
import os
import subprocess
from typing import Tuple

import pytest

from .._xqemu_temporary_directories import get_temp_dirs
from .xqemu_hdd_modifications import HDDModification
from .xqemu_hdd_image_modifier import XQEMUHDDImageModifer

# May use this later on, or maybe not
# Shareable disk for allowing file access during a test
# qemu-nbd --socket=/tmp/my_socket --share=2 ~/.xqemu_files/xbox_hdd.qcow2


_LOGGER = logging.getLogger(__name__)


def _copy_hdd_image(original_image_filename: str, new_copy_filename: str) -> None:
    """Use qemu-img to create a COW copy of a HDD image"""
    _LOGGER.debug("Copying HDD %s to %s", original_image_filename, new_copy_filename)
    subprocess.Popen(
        (
            "qemu-img",
            "create",
            "-F",
            "qcow2",
            "-f",
            "qcow2",
            "-b",
            original_image_filename,
            new_copy_filename,
        )
    ).wait()


class XQEMUHDDTemplate:
    """A template for a hard drive image that is based on some other base
    image with an optional sequence of modifications applied to it.

    This is used to create clean HDD images that can be used in tests so as to
    avoid the changes made in one test affecting any others (or the next run).
    """

    def __init__(
        self,
        template_name: str,
        base_image_file_path: str,
        hdd_modifications: Tuple[HDDModification, ...] = tuple(),
    ):
        _LOGGER.debug("Creating template for %s", template_name)
        self._template_file_path = os.path.join(
            get_temp_dirs().hdd_templates_dir, template_name + ".qcow2",
        )
        if os.path.isfile(self._template_file_path):
            raise ValueError(
                f"Cannot have more than one template called {template_name}. \
                    Have you returned a template from a fixture that is not \
                        session-scoped?"
            )
        _copy_hdd_image(base_image_file_path, self._template_file_path)
        # Make all the changes here
        if hdd_modifications:
            with XQEMUHDDImageModifer(self._template_file_path) as hdd_modifier:
                for change in hdd_modifications:
                    change.perform_modification(hdd_modifier)

        self._hdd_image_count = 0

    def _generate_fresh_hdd_file_path(self) -> str:
        """:returns: a unique filename for a new HDD image based on this template"""
        fresh_hdd_name = os.path.join(
            get_temp_dirs().hdd_images_dir,
            str(self._hdd_image_count)
            + "-"
            + os.path.basename(self._template_file_path),
        )
        return os.path.join(get_temp_dirs().hdd_images_dir, fresh_hdd_name)

    def create_fresh_hdd(self) -> str:
        """Create a copy of the HDD template for use with an instance of XQEMU
        :returns: the path to the image
        """
        self._hdd_image_count += 1
        new_hdd_file_path = self._generate_fresh_hdd_file_path()
        _copy_hdd_image(self._template_file_path, new_hdd_file_path)
        return new_hdd_file_path

    def create_child_template(
        self, template_name, additional_hdd_modifications: Tuple[HDDModification, ...]
    ) -> XQEMUHDDTemplate:
        """:returns: a template based off this one but with some extra changes
        """
        # Build a new template that uses the image for this template as its
        # base image.
        # We do not need to pass the changes made to the parent to the child
        # as they have already been applied to the image.
        return XQEMUHDDTemplate(
            template_name, self._template_file_path, additional_hdd_modifications,
        )


@pytest.fixture(scope="session")
def xqemu_blank_hdd_template() -> XQEMUHDDTemplate:
    """A totally blank HDD image template.

    Set up like the stock Xbox HDD but with no files or folders
    """
    dirname = os.path.dirname(__file__)
    blank_hdd_filename = os.path.join(dirname, "blank_xbox_hdd.qcow2")
    return XQEMUHDDTemplate("blank_hdd", blank_hdd_filename)
