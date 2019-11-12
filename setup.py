#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=7.0',
    'f90nml>=1.1.0',
    'appdirs>=1.4.0',
    'requests',
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Vulcan Technologies, LLC",
    author_email='jeremym@vulcan.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="FV3Config is used to configure and manipulate run directories for FV3GFS.",
    entry_points={
        'console_scripts': [
            'fv3config=fv3config.cli:main',
        ],
    },
    install_requires=requirements,
    extras_requires={'bucket-access': 'gsutil'},
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='fv3config',
    name='fv3config',
    packages=find_packages(include=['fv3config', 'fv3config.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/VulcanClimateModeling/fv3config',
    version='0.1.0',
    zip_safe=False,
)
