#!/usr/bin/env python
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name = "primelib",
    version = "$VERSION$",
    description = "OpenNI2 and NiTE2 python bindings",
    author = "PrimeSense Inc",
    author_email = "primesense.com",
    license = "MIT",
    url = "http://www.openni.org/",
    packages = ["primelib"],
    platforms = ["POSIX", "Windows"],
    provides = ["primelib"],
    #requires = ["six"],
    #install_requires = ["six"],
    keywords = "PrimeSense, OpenNI, OpenNI2, Natural Interaction, NiTE, NiTE2",
    long_description = open(os.path.join(os.path.dirname(__file__), "README.rst"), "r").read(),
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
    ],
)

