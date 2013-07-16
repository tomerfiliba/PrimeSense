import sys
from setuptools import setup

if len(sys.argv) == 1:
    #sys.argv.append("bdist_egg")
    sys.argv.append("install")

setup(
    name = 'crayola_report',
    version = "1.0.0",
    author = "Tomer Filiba",
    author_email = "tomerfiliba@gmail.com",
    py_modules = ['crayola_report'],
    zip_safe = False,
    entry_points = {
        'nose.plugins.0.10': ['crayola-report = crayola_report:HtmlReportPlugin'],
    },
)
