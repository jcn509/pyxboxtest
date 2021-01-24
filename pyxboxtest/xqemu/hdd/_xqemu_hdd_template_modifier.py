"""For internal use only. Used to modify HDD templates after their initial creation"""
from contextlib import AbstractContextManager
import re
from typing import IO

from ._xqemu_ftp_app import _XQEMUFTPApp
from pyxboxtest._utils import remove_ftp_dir

def _validate_path(path: str) -> None:
    """:raises IOError: if the path is not of the correct form"""
    if not re.match(r"/[CDEFGXYZ]/.+", path):
        raise ValueError(f"Path {path} must be of the form\
            /<Drive letter/<path> e.g. /C/test/file.txt")



class _XQEMUHDDTemplateModifier(AbstractContextManager):
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
        self._ftp_client = self._app.get_ftp_client()
        return self

    def add_file(self, to_upload: IO, xbox_file_path: str) -> None:
        """:param to_upload: provides the file contents e.g. an open file or BytesIO
        :param xbox_file_path: file_path on the Xbox
        """
        _validate_path(xbox_file_path)
        self._ftp_client.storbinary(f"STOR {xbox_file_path}", to_upload)

    def add_directory(self, directory_path: str) -> None:
        """:param directory_path: the name of the directory
        """
        _validate_path(directory_path)
        self._ftp_client.mkd(directory_path)
    
    def delete_directory(self, directory_path: str) -> None:
        """:param directory_path: the name of the directory
        """
        _validate_path(directory_path)
        remove_ftp_dir(self._ftp_client, directory_path)

    def delete_file(self, file_path: str) -> None:
        """:param file_path: file_path on the Xbox"""
        _validate_path(file_path)
        self._ftp_client.delete(file_path)

    def rename_file(self, old_file_path: str, new_file_path: str) -> None:
        """Rename (or move) a file on the Xbox
        :param old_file_path: file_path on the Xbox of the file to be renamed
        :param new_file_path: file_path after the renaming
        """
        _validate_path(old_file_path)
        _validate_path(new_file_path)
        # Have to check if drive is the same as NXDK move only works in the same drive
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        self._app.__exit__(exc_type, exc_value, traceback)
