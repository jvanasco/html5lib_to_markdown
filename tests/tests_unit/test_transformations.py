from __future__ import print_function
from __future__ import unicode_literals

# stdlib
import os
import unittest

# local
from html5lib_to_markdown.transformer import Transformer


# ==============================================================================


# if `True`, do not raise errors if the markdown file is missing.
# used for writing tests
ALLOW_MISSING = bool(int(os.getenv("MD_TEST_ALLOW_MISSING", 0)))

# print the markdown
PRINT_RESULTS = bool(int(os.getenv("MD_TEST_PRINT_RESULTS", 0)))


# ------------------------------------------------------------------------------


_dir_base = os.path.dirname(__file__)
_dir_fixtures = os.path.join(_dir_base, "fixtures-transformations")


def _get_test_data(filestring):
    _fpath_html = os.path.join(_dir_fixtures, "%s.html" % filestring)
    _fpath_md = os.path.join(_dir_fixtures, "%s.md" % filestring)
    _html = _md = ""
    with open(_fpath_html, "r") as fh:
        _html = fh.read()
    try:
        with open(_fpath_md, "r") as fh:
            _md = fh.read()
    except Exception:
        if not ALLOW_MISSING:
            raise
    return (_html, _md)


def _get_test_data_alt(filestring, alt):
    _fpath_md = os.path.join(_dir_fixtures, "%s--%s.md" % (filestring, alt))
    _md = ""
    try:
        with open(_fpath_md, "r") as fh:
            _md = fh.read()
    except Exception:
        if not ALLOW_MISSING:
            raise
    return _md


# ==============================================================================


class _TestTransformations(object):
    """
    to create a new test:

        1. create a matched md/html pairing in `./fixtures-transformations/`
        2. create a test stub in this class

    Example:

    html:  ./fixtures-transformations/0047-example.html
    md:    ./fixtures-transformations/0047-example.md
    stub:
            def test_0047(self):
                self._test_actual('0047-example')

    this will create a test for `html > markdown` and `markdown > html`

    """

    def _makeOne(self, **kwargs_override):
        kwargs_default = {
            "a_as_tag": False,
            "a_simple_links": False,
            "img_as_tag": False,
            "parse_markdown_simplelink": True,
            "strip_comments": False,
            "strip_scripts": True,
            "reference_style_link": False,
        }
        kwargs = dict(list(kwargs_default.items()) + list(kwargs_override.items()))
        transformer = Transformer(**kwargs)
        return transformer

    def _test_html_to_markdown(
        self, filename_base, extra_tests=None, fail_expected=None
    ):
        (_html, _md_expected) = _get_test_data(filename_base)
        transformer = self._makeOne()
        _result = transformer.transform(_html)
        if PRINT_RESULTS:
            print("=" * 80)
            print(filename_base)
            print("- " * 20, "_result")
            print(_result)
            print("- " * 20, "_expected")
            print(_md_expected)
            print("=" * 80)
        if fail_expected:
            self.assertNotEqual(_md_expected, _result)
        else:
            self.assertEqual(_md_expected, _result)
        if extra_tests:
            if "strip_scripts=False" in extra_tests:

                def _strip_scripts():
                    # run in a function for better traceback
                    _md_expected_2 = _get_test_data_alt(
                        filename_base, "strip_scripts=False"
                    )
                    _transformer = self._makeOne(strip_scripts=False)
                    _result = _transformer.transform(_html)
                    if PRINT_RESULTS:
                        print("=" * 80)
                        print(filename_base, "strip_scripts=False")
                        print("- " * 20)
                        print(_result)
                        print("=" * 80)
                    if fail_expected:
                        self.assertNotEqual(_md_expected_2, _result)
                    else:
                        self.assertEqual(_md_expected_2, _result)

                _strip_scripts()
            if "parse_markdown_simplelink=False" in extra_tests:

                def _parse_markdown_simplelink():
                    # run in a function for better traceback
                    _md_expected_2 = _get_test_data_alt(
                        filename_base, "parse_markdown_simplelink=False"
                    )
                    _transformer = self._makeOne(parse_markdown_simplelink=False)
                    _result = _transformer.transform(_html)
                    if PRINT_RESULTS:
                        print("=" * 80)
                        print(filename_base, "parse_markdown_simplelink=False")
                        print("- " * 20)
                        print(_result)
                        print("=" * 80)
                    if fail_expected:
                        self.assertNotEqual(_md_expected_2, _result)
                    else:
                        self.assertEqual(_md_expected_2, _result)

                _parse_markdown_simplelink()
            if "a_simple_links=True" in extra_tests:

                def _a_simple_links():
                    # run in a function for better traceback
                    _md_expected_2 = _get_test_data_alt(
                        filename_base, "a_simple_links=True"
                    )
                    _transformer = self._makeOne(a_simple_links=True)
                    _result = _transformer.transform(_html)
                    if PRINT_RESULTS:
                        print("=" * 80)
                        print(filename_base, "a_simple_links=True")
                        print("- " * 20)
                        print(_result)
                        print("=" * 80)
                    if fail_expected:
                        self.assertNotEqual(_md_expected_2, _result)
                    else:
                        self.assertEqual(_md_expected_2, _result)

                _a_simple_links()
            if "a_as_tag=True" in extra_tests:

                def _a_as_tag():
                    # run in a function for better traceback
                    _md_expected_2 = _get_test_data_alt(filename_base, "a_as_tag=True")
                    _transformer = self._makeOne(a_as_tag=True)
                    _result = _transformer.transform(_html)
                    if PRINT_RESULTS:
                        print("=" * 80)
                        print(filename_base, "a_as_tag=True")
                        print("- " * 20)
                        print(_result)
                        print("=" * 80)
                    if fail_expected:
                        self.assertNotEqual(_md_expected_2, _result)
                    else:
                        self.assertEqual(_md_expected_2, _result)

                _a_as_tag()
            if "img_as_tag=True" in extra_tests:

                def _img_as_tag():
                    # run in a function for better traceback
                    _md_expected_2 = _get_test_data_alt(
                        filename_base, "img_as_tag=True"
                    )
                    _transformer = self._makeOne(img_as_tag=True)
                    _result = _transformer.transform(_html)
                    if PRINT_RESULTS:
                        print("=" * 80)
                        print(filename_base, "img_as_tag=True")
                        print("- " * 20)
                        print(_result)
                        print("=" * 80)
                    if fail_expected:
                        self.assertNotEqual(_md_expected_2, _result)
                    else:
                        self.assertEqual(_md_expected_2, _result)

                _img_as_tag()

    def _test_markdown_to_markdown(
        self, filename_base, extra_tests=None, fail_expected=None
    ):
        (_html, _md_expected) = _get_test_data(filename_base)
        transformer = self._makeOne()
        _result = transformer.transform(_md_expected)
        self.assertEqual(_md_expected, _result)

    def test_0001(self):
        self._test_actual("0001-simple")

    def test_0002(self):
        self._test_actual("0002-p_header")

    def test_0003(self):
        self._test_actual("0003-p_header_alt")

    def test_0004(self):
        self._test_actual("0004-blockquote_nested_a")

    def test_0005(self):
        self._test_actual("0005-code")

    def test_0006(self):
        self._test_actual("0006-blockquote_nested_lists")

    def test_0007(self):
        self._test_actual("0007-ends_on_hr")

    def test_0008(self):
        self._test_actual("0008-ends_on_hr_br")

    def test_0009(self):
        self._test_actual("0009-pre_code_pre")

    def test_0010(self):
        self._test_actual("0010-whitespace")

    def test_0011(self):
        self._test_actual("0011-blockquote_spacing")

    def test_0012(self):
        self._test_actual("0012-heading")

    def test_0013(self):
        self._test_actual("0013-p_simple")

    def test_0014(self):
        self._test_actual("0014-hr_code")

    def test_0015(self):
        self._test_actual("0015-nest_list_simple")

    def test_0016(self):
        self._test_actual("0016-pre_code")

    def test_0017(self):
        self._test_actual("0017-script", ["strip_scripts=False"])

    def test_0018(self):
        self._test_actual("0018-blockquoted_things")

    def test_0019(self):
        self._test_actual("0019-improper_nests")

    def test_0020(self):
        self._test_actual("0020-blockquoted_things_alt")

    def test_0021(self):
        self._test_actual("0021-blockquoted_things_alt_2")

    def test_0022(self):
        self._test_actual("0022-nested")

    def test_0023(self):
        self._test_actual("0023-links", ["a_simple_links=True"])

    def test_0024(self):
        self._test_actual("0024-angled_link", fail_expected=True)

    # --

    # these tests are designed to debug/surface an issue regarding img tags
    # not properly transforming
    # the `25` section is for img tags
    # additinoal testing in the  `26` section is for `a` tags, which may behave similarly

    def test_0025_a_0(self):
        self._test_actual("0025-a-0-img_prefix_suffix", ["img_as_tag=True"])

    def test_0025_a_1(self):
        self._test_actual("0025-a-1-img_prefix_suffix_oneline", ["img_as_tag=True"])

    def test_0025_b_0(self):
        self._test_actual("0025-b-0-img_prefix", ["img_as_tag=True"])

    def test_0025_b_1(self):
        self._test_actual("0025-b-1-img_prefix_oneline", ["img_as_tag=True"])

    def test_0025_c_0(self):
        self._test_actual("0025-c-0-img_suffix", ["img_as_tag=True"])

    def test_0025_c_1(self):
        self._test_actual("0025-c-1-img_suffix_oneline", ["img_as_tag=True"])

    def test_0025_d(self):
        self._test_actual("0025-d-img_bare", ["img_as_tag=True"])

    def test_0026_d(self):
        self._test_actual(
            "0026-d-a_bare",
            ["a_as_tag=True", "a_simple_links=True", "parse_markdown_simplelink=False"],
        )

    # ---

    def test_0097(self):
        self._test_actual("0097-involved")

    def test_0098(self):
        self._test_actual("0098-involved")

    def test_0099(self):
        self._test_actual(
            "0099-involved", ["a_simple_links=True", "parse_markdown_simplelink=False"]
        )

    # ---

    def test_flow_0001(self):
        self._test_actual("flow_0001")


class TestHtmlToMarkdown(unittest.TestCase, _TestTransformations):
    _test_actual = _TestTransformations._test_html_to_markdown


if False:

    class TestMarkdownToMarkdown(unittest.TestCase, _TestTransformations):
        _test_actual = _TestTransformations._test_markdown_to_markdown
