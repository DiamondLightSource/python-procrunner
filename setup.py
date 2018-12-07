#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "six",
    # PyWin32 is only supported on 2.7 and 3.5+
    'pywin32; sys_platform=="win32" and python_version=="2.7"',
    'pywin32; sys_platform=="win32" and python_version>="3.5"',
]

setup_requirements = []
needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
if needs_pytest:
    setup_requirements.append("pytest-runner")

test_requirements = ["mock", "pytest"]

setup(
    author="Markus Gerstel",
    author_email="scientificsoftware@diamond.ac.uk",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    description="Versatile utility function to run external processes",
    install_requires=requirements,
    license="BSD license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="procrunner",
    name="procrunner",
    packages=find_packages(include=["procrunner"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/DiamondLightSource/python-procrunner",
    version="0.9.0",
    zip_safe=False,
)
