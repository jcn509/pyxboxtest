"""For internal use only! Provides a basic FTP connection to XQEMU for HDD read/write"""
from .. import XQEMUXboxAppRunner


class _XQEMUFTPApp(XQEMUXboxAppRunner):
    def __init__(self, hdd_template_image_file_name: str):
        super().__init__(
            dvd_filename="FTP DVD filename",
            hdd_filename=hdd_template_image_file_name,
            force_headless=True,
        )
