import sys
from setuptools import setup

if len(sys.argv) == 1:
    #sys.argv.append("bdist_egg")
    sys.argv.append("install")

setup(
    name = 'crayola',
    version = "1.0.0",
    author = "Tomer Filiba",
    author_email = "tomerfiliba@gmail.com",
    packages = ['crayola'],
    package_dir = {"crayola" : "."},
    zip_safe = False,
)
