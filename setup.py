#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "f90nml>=1.1.0",
    "appdirs>=1.4.0",
    "pyyaml>=5.0",
    "gcsfs>=0.7.0",
    "fsspec>=0.8.0",
    "dacite>=1.6.0",
]

setup_requirements = []

test_requirements = ["pytest"]

setup(
    author="Allen Institute of Artificial Intelligence",
    author_email="jeremym@allenai.org",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="FV3Config is used to configure and manipulate run directories for FV3GFS.",
    entry_points={
        "console_scripts": [
            "fv3run=fv3config.fv3run.__main__:main",
            "write_run_directory=fv3config.cli:write_run_directory",
            "enable_restart=fv3config.cli:enable_restart",
            "enable_nudging=fv3config.cli:enable_nudging",
            "scream_run=fv3config.scream.cli:scream_run",
        ]
    },
    install_requires=requirements,
    extras_require={
        "bucket-access": "gcsfs",
        "fv3run": "fv3gfs-python",
        "run_kubernetes": "kubernetes",
    },
    license="Apache 2.0 license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="fv3config",
    name="fv3config",
    packages=find_packages(include=["fv3config", "fv3config.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/ai2cm/fv3config",
    version="0.9.0",
    zip_safe=False,
)
