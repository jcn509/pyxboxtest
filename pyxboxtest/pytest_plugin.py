"""Pytest specific setup, currently just adds the headless option to pytest"""


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run without creating windows for each instance of XQEMU",
    )