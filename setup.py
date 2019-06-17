#!/usr/bin/env python3
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

from tauhka import __version__; print(__version__)

setuptools.setup(
    name="tauhka",
    version=__version__,
    python_requires='>=3',
    install_requires=['selenium'],
    author="CSC - IT Center for Science Ltd.",
    author_email="servicedesk@csc.fi",
    description="Tauhka is a web application testing framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CSCfi/tauhka",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
