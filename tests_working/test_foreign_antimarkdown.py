from __future__ import print_function
from __future__ import unicode_literals

import unittest
import os
import pprint

import html5lib_to_markdown
from html5lib_to_markdown.transformer import Transformer


# ==============================================================================


_dir_base = os.path.dirname(__file__)
_dir_fixtures = os.path.join(os.path.join(_dir_base, 'antimarkdown'), 'data')

DEBUG_ERRORS = True


# ==============================================================================


class _TestAntimarkdown(object):
    """
    this reads the antimakrdown tests
    """

    _data = {'basic': {},
             }

    def _makeOne(self):
        transformer = Transformer(
            a_as_tag=False,
            img_as_tag=False,
            strip_comments=False,
            reference_style_link=False,
        )
        return transformer

    def _test_html_to_markdown(self, filename_base):
        (_html,
         _md
         ) = _get_test_data(filename_base)
        transformer = self._makeOne()
        _result = transformer.transform(_html)
        if PRINT_RESULTS:
            print("=" * 80)
            print(filename_base)
            print("- " * 20)
            print(_result)
            print("=" * 80)
        self.assertEqual(_md, _result)

    def _test_markdown_to_markdown(self, filename_base):
        (_html,
         _md
         ) = _get_test_data(filename_base)
        transformer = self._makeOne()
        _result = transformer.transform(_md)
        self.assertEqual(_md, _result)

    def _load_data__basic(self):
        if _TestAntimarkdown._data['basic']:
            # it's loaded!
            return
        _dir_basic = os.path.join(_dir_fixtures, 'basic')
        filesnames_all = os.listdir(_dir_basic)
        for _fname in filesnames_all:
            if not _fname.endswith('.html'):
                continue
            _fbase = _fname[:-5]
            _fpath_html = os.path.join(_dir_basic, "%s.html" % _fbase)
            _fpath_md = os.path.join(_dir_basic, "%s.txt" % _fbase)
            _html = _md = ''
            with open(_fpath_html, 'r') as fh:
                _html = fh.read()
            with open(_fpath_md, 'r') as fh:
                _md = fh.read()
            _TestAntimarkdown._data['basic'][_fbase] = {
                'html-path': _fpath_html,
                'md-path': _fpath_md,
                'html': _html,
                'md': _md,
            }

    def test_basic(self):
        self._load_data__basic()
        results = {'success': [],
                   'error': [],
                   }
        for test_name in _TestAntimarkdown._data['basic']:
            data_src = _TestAntimarkdown._data['basic'][test_name]['html']
            data_result = _TestAntimarkdown._data['basic'][test_name]['md']
            transformer = self._makeOne()
            _result = transformer.transform(data_src)
            if _result == data_result:
                results['success'].append(test_name)
            else:
                results['error'].append(test_name)
                if DEBUG_ERRORS:
                    print("=" * 30)
                    print(test_name)
                    print('-result')
                    print(">" * 30)
                    print(_result)
                    print("<" * 30)
                    print('-expected')
                    print(">" * 30)
                    print(data_result)
                    print("<" * 30)
                    print("=" * 30)


class TestHtmlToMarkdown(unittest.TestCase, _TestAntimarkdown):
    _test_source = 'html'


if False:
    class TestMarkdownToMarkdown(unittest.TestCase, _TestAntimarkdown):
        _test_source = 'md'
