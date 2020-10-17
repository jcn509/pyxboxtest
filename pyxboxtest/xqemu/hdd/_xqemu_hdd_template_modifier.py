"""For internal use only. Used to modify HDD templates after their initial creation"""
from contextlib import AbstractContextManager
from ._xqemu_ftp_app import _XQEMUFTPApp


class _XQEMUHDDTemplateModifier(AbstractContextManager):
    """For internal use only. Used to modify HDD templates after their initial creation"""

    def __init__(self, hdd_template_image_file_name: str):
        self._app = _XQEMUFTPApp(hdd_template_image_file_name)

    def __enter__(self):
        self._app.__enter__()
        return self

    def add_file(self, local_filename: str, xbox_filename: str) -> None:
        pass

    def delete_file(self, filename: str) -> None:
        pass

    def rename_file(self, old_filename: str, new_filename: str) -> None:
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self._app.__exit__(exc_type, exc_value, traceback)
