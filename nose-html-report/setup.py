import sys
from setuptools import setup

if len(sys.argv) == 1:
    sys.argv.append("bdist_egg")

setup(
    name = 'nosehtml',
    version = "1.0.0",
    author = "Tomer Filiba",
    author_email = "tomerfiliba@gmail.com",
    py_modules = ['nosehtml'],
    zip_safe = False,
    entry_points = {
        'nose.plugins.0.10': ['nosehtml = nosehtml:HtmlReportPlugin'],
    },
)
