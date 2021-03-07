"""For internal use only! Provides a basic FTP connection to XQEMU for HDD read/write"""
from pathlib import Path
from .. import XQEMUXboxAppRunner

_FTP_ISO_FILE_PATH = str(Path(__file__).parent / "OGXboxFTP.iso")


class _XQEMUFTPApp(XQEMUXboxAppRunner):
    def __init__(self, hdd_template_image_file_name: str):
        super().__init__(
            dvd_filename=_FTP_ISO_FILE_PATH,
            hdd_filename=hdd_template_image_file_name,
            force_headless=True,
        )
