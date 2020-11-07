"""Pytest specific setup, currently just adds the headless option to pytest"""
import pytest

from .xqemu._xqemu_temporary_directories import _initialise_temp_dirs
from .xqemu.xqemu_xbox_app_runner import _set_headless


@pytest.fixture(scope="session", autouse=True)
def _initial_framework_setup(request, tmp_path_factory):
    """Never use this fixture directly!"""
    _initialise_temp_dirs(tmp_path_factory)
    _set_headless(request.config.getoption("--headless"))


def pytest_addoption(parser):
    """Add the headless option to pytests command line option parser"""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run without creating windows for each instance of XQEMU",
    )
