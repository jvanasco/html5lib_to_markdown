import os
import re
from setuptools import setup
from setuptools import find_packages

import six

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md")) as fp:
    README = fp.read()
README = README.split("\n\n", 1)[0] + "\n"

# store version in the init.py
with open(
    os.path.join(os.path.dirname(__file__), "html5lib_to_markdown", "__init__.py")
) as v_file:
    VERSION = re.compile(r".*__VERSION__ = '(.*?)'", re.S).match(v_file.read()).group(1)


install_requires = [
    "html5lib",
    "bleach",
    # 'frozendict',
    # 'six',
]
tests_require = []

setup(
    name="html5lib_to_markdown",
    author="Jonathan Vanasco",
    author_email="jonathan@findmeon.com",
    version=VERSION,
    py_modules=["html5lib_to_markdown"],
    description="extract markdown flavored text from html",
    long_description=README,
    zip_safe=False,
    keywords="",
    test_suite="tests_unit.test_transformations",
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
    ],
)
