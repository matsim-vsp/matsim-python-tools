# -*- coding: utf-8 -*-

import pathlib

from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="matsim_tools",  # TODO: should be matsim-tools ?
    version="0.0.1",
    description="Tools for working with the MATSim Agent-Based Transportation Simulation framework",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/matsim-vsp/matsim-python-tools",
    author="VSP-Berlin",
    author_email="laudan@tu-berlin.de",
    license="GPLv3",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python :: 3",
    ],
    packages=["matsim"],
    install_requires=[
        "protobuf >= 3.10.0",
        "shapely",
        "xopen",
        "geopandas >= 0.6.0"
        # TODO: pandas, etc. missing as dependency
    ],
    tests_require=[
        "assertpy"
    ],
    entry_points={},
)
