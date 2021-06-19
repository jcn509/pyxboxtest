"""For internal use only. Used to modify HDD templates after their initial creation"""
from contextlib import AbstractContextManager
from io import BytesIO
from typing import IO, List

from ._xqemu_ftp_app import _XQEMUFTPApp
from pyxboxtest._utils import (
    remove_ftp_dir,
    validate_xbox_directory_path,
    validate_xbox_file_path,
)

# TODO: split into read and read/write classes?
class XQEMUHDDImageModifer(AbstractContextManager):
    """For internal use only. Used to modify HDD templates after their initial creation
    
    Note: all paths must be of the form /<Drive letter/<path> e.g. /C/test/file.txt
    """

    def __init__(self, hdd_template_image_file_path: str):
        """:param hdd_template_image_file_path: base image to copy for this
        template
        """
        self._app = _XQEMUFTPApp(hdd_template_image_file_path)
        self._ftp_client = None

    def __enter__(self):
        self._app.__enter__()
        # TODO: Maybe I should read KD output or something to know when the server is ready?
        self._ftp_client = self._app.get_ftp_client("xbox", "xbox")
        return self

    def add_file_to_xbox(self, xbox_file_path: str, to_upload: IO) -> None:
        """:param xbox_file_path: file_path on the Xbox
        :param to_upload: provides the file contents e.g. an open file or BytesIO
        """
        validate_xbox_file_path(xbox_file_path)
        self._ftp_client.storbinary(f"STOR {xbox_file_path}", to_upload)

    def copy_file_on_xbox(self, file_path: str, copy_to_file_path: str) -> None:
        # Note: FTP server does not currently support multiple simultaneous users
        validate_xbox_file_path(file_path)
        validate_xbox_file_path(copy_to_file_path)
        self.add_file_to_xbox(copy_to_file_path, self.get_xbox_file_contents(file_path))

    def add_directory_to_xbox(self, directory_path: str) -> None:
        """:param directory_path: the name of the directory
        """
        validate_xbox_directory_path(directory_path)
        self._ftp_client.mkd(directory_path)

    def delete_directory_from_xbox(self, directory_path: str) -> None:
        """:param directory_path: the name of the directory
        """
        validate_xbox_directory_path(directory_path)
        remove_ftp_dir(self._ftp_client, directory_path)

    def rename_directory_on_xbox(
        self, old_directory_path: str, new_directory_path: str
    ) -> None:
        """Rename (or move) a directory on the Xbox
        :param old_directory_path: file_path on the Xbox of the file to be renamed
        :param new_directory_path: file_path after the renaming
        """
        validate_xbox_directory_path(old_directory_path)
        validate_xbox_directory_path(new_directory_path)
        # Have to check if drive is the same as NXDK move only works in the same drive
        on_same_drive = old_directory_path[1] == new_directory_path[1]
        if on_same_drive:
            # Can't include the / on the end?
            # Should any directory paths include the /?
            self._ftp_client.rename(old_directory_path[:-1], new_directory_path[:-1])
        else:
            # FTP server doesn't support this properly right now :/
            raise RuntimeError("Need to patch in support for moving accross drives")
            # Need to recursively copy all files/subdirs and then delete the old dir
            self.copy_file_on_xbox(old_directory_path, new_directory_path)
            self.delete_file_from_xbox(old_directory_path)

    def get_xbox_directory_contents(self, directory_path: str) -> List[str]:
        validate_xbox_directory_path(directory_path)
        return self._ftp_client.nlst(directory_path)

    def get_xbox_drives(self) -> List[str]:
        return self._ftp_client.nlst("/")

    def get_xbox_file_contents(self, file_path: str) -> BytesIO:
        validate_xbox_file_path(file_path)
        data = BytesIO()
        self._ftp_client.retrbinary(f"RETR {file_path}", data.write)
        data.seek(0)
        return data

    def delete_file_from_xbox(self, file_path: str) -> None:
        """:param file_path: file_path on the Xbox"""
        validate_xbox_file_path(file_path)
        self._ftp_client.delete(file_path)

    def rename_file_on_xbox(self, old_file_path: str, new_file_path: str) -> None:
        """Rename (or move) a file on the Xbox
        :param old_file_path: file_path on the Xbox of the file to be renamed
        :param new_file_path: file_path after the renaming
        """
        validate_xbox_file_path(old_file_path)
        validate_xbox_file_path(new_file_path)
        # Have to check if drive is the same as NXDK move only works in the same drive
        on_same_drive = old_file_path[1] == new_file_path[1]
        if on_same_drive:
            self._ftp_client.rename(old_file_path, new_file_path)
        else:
            # FTP server doesn't support this properly right now :/
            self.copy_file_on_xbox(old_file_path, new_file_path)
            self.delete_file_from_xbox(old_file_path)

    def __exit__(self, exc_type, exc_value, traceback):
        self._app.__exit__(exc_type, exc_value, traceback)
