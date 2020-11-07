#!/usr/bin/env python

from distutils.core import setup

setup(
    name="pyxboxtest",
    version="0.1",
    description="An XQEMU and pytest based end-to-end testing framework for original Xbox apps",
    author="Josh Neil",
    author_email="joshneil8@gmail.com",
    # url='https://www.python.org/sigs/distutils-sig/',
    install_requires=[
        "overrides",
        "pytest",
        "qmp",
        "install",
        "psutil",
        "cached-property",
    ],
    packages=["pyxboxtest"],
    dependency_links=[],
)
