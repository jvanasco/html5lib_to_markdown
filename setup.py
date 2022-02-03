# stdlib
import os
import re

# pypi
from setuptools import find_packages
from setuptools import setup

# ==============================================================================

HERE = os.path.abspath(os.path.dirname(__file__))

long_description = description = "extract markdown flavored text from html"
with open(os.path.join(HERE, "README.md")) as fp:
    long_description = fp.read()

# store version in the init.py
with open(os.path.join(HERE, "src", "html5lib_to_markdown", "__init__.py")) as v_file:
    VERSION = re.compile(r'.*__VERSION__ = "(.*?)"', re.S).match(v_file.read()).group(1)


install_requires = [
    "html5lib>=1.1",
    "six",
]
tests_require = []
testing_extras = (
    install_requires
    + tests_require
    + [
        "pytest",
    ]
)

setup(
    name="html5lib_to_markdown",
    author="Jonathan Vanasco",
    author_email="jonathan@findmeon.com",
    version=VERSION,
    py_modules=["html5lib_to_markdown"],
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    zip_safe=False,
    keywords="",
    test_suite="tests.tests_unit",
    packages=find_packages(
        where="src",
    ),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        "testing": testing_extras,
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
    ],
)
