"""Pytest specific setup, currently just adds the headless option to pytest"""
import pytest

from .xqemu._xqemu_temporary_directories import _initialise_temp_dirs
from .xqemu.xqemu_params import XQEMUFirmware
from .xqemu.xqemu_xbox_app_runner import (
    XQEMUXboxAppRunner,
    _XQEMUXboxAppRunnerGlobalParams,
)


@pytest.fixture(scope="session", autouse=True)
def _initial_framework_setup(request, tmp_path_factory):
    """Never use this fixture directly!"""
    _initialise_temp_dirs(tmp_path_factory)
    XQEMUXboxAppRunner._global_params = _XQEMUXboxAppRunnerGlobalParams(
        XQEMUFirmware(
            request.config.getoption("--mcpx-rom"), request.config.getoption("--bios")
        ),
        request.config.getoption("--headless"),
    )


def pytest_addoption(parser):
    """Add the headless option to pytests command line option parser"""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run without creating windows for each instance of XQEMU",
    )
    parser.addoption(
        "--mcpx-rom", type=str, help="MCPX rom used to boot the xbox", required=True
    )
    parser.addoption("--bios", type=str, help="Xbox BIOS (kernel) image", required=True)
