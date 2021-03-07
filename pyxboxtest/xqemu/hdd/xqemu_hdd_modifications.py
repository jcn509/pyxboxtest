"""A collection of modification operations to be applied to a HDD template
when it is created
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import IO, Tuple

from overrides import overrides

from .xqemu_hdd_image_modifier import XQEMUHDDImageModifer


@dataclass(frozen=True)
class HDDModification(ABC):
    """Perform some modification to a HDD template"""

    @abstractmethod
    def perform_modification(self, hdd_modifier: XQEMUHDDImageModifer) -> None:
        """Carry out the modification"""
        raise NotImplementedError


# TODO: support all other operations?


@dataclass(frozen=True)
class AddFile(HDDModification):
    """Add a file to a HDD template"""

    xbox_filename: str
    file_contents: IO

    @overrides
    def perform_modification(self, hdd_modifier: XQEMUHDDImageModifer) -> None:
        """Add the file"""
        hdd_modifier.add_file_to_xbox(self.xbox_filename, self.file_contents)


@dataclass(frozen=True)
class DeleteFile(HDDModification):
    """Delete a file from a HDD template"""

    filename: str

    @overrides
    def perform_modification(self, hdd_modifier: XQEMUHDDImageModifer) -> None:
        """Delete the file"""
        hdd_modifier.delete_file_from_xbox(self.filename)


@dataclass(frozen=True)
class RenameFile(HDDModification):
    """Rename (or move) a file on a HDD template"""

    old_filename: str
    new_filename: str

    @overrides
    def perform_modification(self, hdd_modifier: XQEMUHDDImageModifer) -> None:
        """Rename the file"""
        hdd_modifier.rename_file_on_xbox(self.old_filename, self.new_filename)


@dataclass(frozen=True)
class BatchModification(HDDModification):
    """Perform a sequence of operations on a HDD image.

    Useful if you want to reuse a sequence of operations on different
    templates that don't share a common parent, or if you want to give a
    meaninful name to the sequence
    """

    modifications: Tuple[HDDModification, ...]

    @overrides
    def perform_modification(self, hdd_modifier: XQEMUHDDImageModifer) -> None:
        """Perform all the modifications in order"""
        for modification in self.modifications:
            modification.perform_modification(hdd_modifier)
