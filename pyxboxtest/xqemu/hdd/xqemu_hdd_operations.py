"""A collection of modification operations to be applied to a HDD template
when it is created
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple

from overrides import overrides

from ._xqemu_hdd_template_modifier import _XQEMUHDDTemplateModifier


@dataclass(frozen=True)
class HDDModification(ABC):
    """Perform some modification to a HDD template"""

    @abstractmethod
    def perform_modification(self, hdd_modifier: _XQEMUHDDTemplateModifier) -> None:
        """Carry out the modification"""
        raise NotImplementedError


@dataclass(frozen=True)
class AddFile(HDDModification):
    """Add a file to a HDD template"""

    local_filename: str
    xbox_filename: str

    @overrides
    def perform_modification(self, hdd_modifier: _XQEMUHDDTemplateModifier) -> None:
        """Add the file"""
        hdd_modifier.add_file(self.local_filename, self.xbox_filename)


@dataclass(frozen=True)
class DeleteFile(HDDModification):
    """Delete a file from a HDD template"""

    filename: str

    @overrides
    def perform_modification(self, hdd_modifier: _XQEMUHDDTemplateModifier) -> None:
        """Delete the file"""
        hdd_modifier.delete_file(self.filename)


@dataclass(frozen=True)
class RenameFile(HDDModification):
    """Rename (or move) a file on a HDD template"""

    old_filename: str
    new_filename: str

    @overrides
    def perform_modification(self, hdd_modifier: _XQEMUHDDTemplateModifier) -> None:
        """Rename the file"""
        hdd_modifier.rename_file(self.old_filename, self.new_filename)


@dataclass(frozen=True)
class BatchModification(HDDModification):
    """Perform a sequence of operations on a HDD image.

    Useful if you want to reuse a sequence of operations on different
    templates that don't share a common parent, or if you want to give a
    meaninful name to the sequence
    """

    modifications: Tuple[HDDModification, ...]

    @overrides
    def perform_modification(self, hdd_modifier: _XQEMUHDDTemplateModifier) -> None:
        """Perform all the modifications in order"""
        for modification in self.modifications:
            modification.perform_modification(hdd_modifier)
