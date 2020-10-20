import os
import re
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md")) as fp:
    README = fp.read()

# store version in the init.py
with open(
    os.path.join(os.path.dirname(__file__), "html5lib_to_markdown", "__init__.py")
) as v_file:
    VERSION = re.compile(r'.*__VERSION__ = "(.*?)"', re.S).match(v_file.read()).group(1)


install_requires = [
    "html5lib>=1.1",
    'six',
]
tests_require = []
testing_extras = install_requires + tests_require + [
    "pytest",
]

setup(
    name="html5lib_to_markdown",
    author="Jonathan Vanasco",
    author_email="jonathan@findmeon.com",
    version=VERSION,
    py_modules=["html5lib_to_markdown"],
    description="extract markdown flavored text from html",
    long_description=README,
    long_description_content_type="text/markdown",
    zip_safe=False,
    keywords="",
    test_suite="tests_unit.test_transformations",
    packages=find_packages(),
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
