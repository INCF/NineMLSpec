#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="9ML",
    version="0.3dev",
    package_data={'nineml': ['examples/AL/demos/*.py',
                             'examples/AL/sample_components/*.py']},
    packages=find_packages(),
    author="Andrew P. Davison, Eilif Muller, Mike Hull, Thomas G. Close",
    # add your name here if you contribute to the code
    author_email="nineml-users@incf.org",
    description=(
        "A tool for reading, writing and generally working with 9ML files."),
    long_description=open("README").read(),
    license="BSD 3 License",
    keywords="computational neuroscience modeling interoperability XML",
    url="http://nineml.incf.org",
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2',
                 'Topic :: Scientific/Engineering'],
    install_requires=['lxml', 'ply', 'numpy', 'quantities'],
    tests_require=['nose']
)
