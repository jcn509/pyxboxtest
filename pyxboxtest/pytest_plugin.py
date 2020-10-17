"""Pytest specific setup, currently just adds the headless option to pytest"""
import pytest
from .xqemu.hdd.xqemu_hdd_template import _set_temp_dir
from .xqemu.xqemu_xbox_app_runner import _set_headless


@pytest.fixture(scope="session", autouse=True)
def _initial_framework_setup(request, tmp_path_factory):
    """Never use this fixture directly!"""
    _set_temp_dir(tmp_path_factory)
    _set_headless(request.config.getoption("--headless"))


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run without creating windows for each instance of XQEMU",
    )
