from __future__ import print_function
from __future__ import unicode_literals

import unittest
import os
import re
import pdb

from html5lib_to_markdown.transformer import Transformer


# ==============================================================================


# python-markdownify/tests/test_conversions.py
nested_uls = re.sub('\s+', '', """
    <ul>
        <li>1
            <ul>
                <li>a
                    <ul>
                        <li>I</li>
                        <li>II</li>
                        <li>III</li>
                    </ul>
                </li>
                <li>b</li>
                <li>c</li>
            </ul>
        </li>
        <li>2</li>
        <li>3</li>
    </ul>""")


class _TestToMarkdownSpec(object):

    _transformer = None

    @property
    def transformer(self):
        if not self._transformer:
            self._transformer = Transformer(
                a_as_tag=False,
                img_as_tag=False,
                strip_comments=False,
                reference_style_link=False,
            )
        return self._transformer
    

    def _test_html_to_markdown(self, _html, _md):
        _result = self.transformer.transform(_html)
        self.assertEqual(_md, _result)

    def _test_markdown_to_markdown(self, _html, _md):
        _result = self.transformer.transform(_md)
        self.assertEqual(_md, _result)
        
    def test_advanced__nested(self):
        # python-markdownify/tests/test_advanced.py
        html = '''<p>This is an <a href="http://example.com/">example link</a>.</p>'''
        md = 'This is an [example link](http://example.com/).\n\n'
        self._test_actual(html, md)

    def test_basic__single_tag(self):
        # python-markdownify/tests/test_basic.py
        html = '<span>Hello</span>'
        md = 'Hello'
        self._test_actual(html, md)

    def test_basic__soup(self):
        # python-markdownify/tests/test_basic.py
        html = '<div><span>Hello</div></span>'
        md = 'Hello'
        self._test_actual(html, md)

    def test_basic__whitespace(self):
        # python-markdownify/tests/test_basic.py
        html = ' a  b \n\n c '
        md = ' a b c '
        self._test_actual(html, md)

    def test_basic__conversions__a(self):
        # python-markdownify/tests/test_conversions.py
        html = '<a href="http://google.com">Google</a>'
        md = '[Google](http://google.com)'

    def test_basic__a_with_title(self):
        # python-markdownify/tests/test_conversions.py
        html = '<a href="http://google.com" title="The &quot;Goog&quot;">Google</a>'
        md = r'[Google](http://google.com "The \"Goog\"")'

    def test_basic__a_shortcut(self):
        # python-markdownify/tests/test_conversions.py
        html = '<a href="http://google.com">http://google.com</a>'
        md = '<http://google.com>'

    @unittest.SkipTest
    def test_basic__a_no_autolinks(self):
        # python-markdownify/tests/test_conversions.py
        html = '<a href="http://google.com">http://google.com</a>'
        md = '[http://google.com](http://google.com)'

    def test_basic__b(self):
        # python-markdownify/tests/test_conversions.py
        html = '<b>Hello</b>'
        md = '**Hello**'

    def test_basic__blockquote(self):
        # python-markdownify/tests/test_conversions.py
        html = '<blockquote>Hello</blockquote>'
        md = '> Hello'

    def test_basic__nested_blockquote(self):
        # python-markdownify/tests/test_conversions.py
        html = '<blockquote>And she was like <blockquote>Hello</blockquote></blockquote>'
        md = '> And she was like \n> > Hello'

    def test_basic__br(self):
        # python-markdownify/tests/test_conversions.py
        html = 'a<br />b<br />c'
        md = 'a  \nb  \nc'

    def test_basic__em(self):
        # python-markdownify/tests/test_conversions.py
        html = '<em>Hello</em>'
        md = '*Hello*'

    def test_basic__h1(self):
        # python-markdownify/tests/test_conversions.py
        html = '<h1>Hello</h1>'
        md = 'Hello\n=====\n\n'

    def test_basic__h2(self):
        # python-markdownify/tests/test_conversions.py
        html = '<h2>Hello</h2>'
        md = 'Hello\n-----\n\n'

    def test_basic__hn__3(self):
        # python-markdownify/tests/test_conversions.py
        html = '<h3>Hello</h3>'
        md = '### Hello\n\n'

    def test_basic__hn__6(self):
        # python-markdownify/tests/test_conversions.py
        html = '<h6>Hello</h6>'
        md = '###### Hello\n\n'

    @unittest.SkipTest
    def test_basic__atx_headings__h1(self):
        # python-markdownify/tests/test_conversions.py
        # html = '<h1>Hello</h1>', heading_style=ATX
        md = '# Hello\n\n'

    @unittest.SkipTest
    def test_basic__atx_headings__h2(self):
        # python-markdownify/tests/test_conversions.py
        # html = '<h2>Hello</h2>', heading_style=ATX
        md = '## Hello\n\n'

    @unittest.SkipTest
    def test_basic__atx_closed_headings__h1(self):
        # python-markdownify/tests/test_conversions.py
        # html = '<h1>Hello</h1>', heading_style=ATX_CLOSED
        md = '# Hello #\n\n'

    @unittest.SkipTest
    def test_basic__atx_closed_headings__h2(self):
        # python-markdownify/tests/test_conversions.py
        # html = '<h2>Hello</h2>', heading_style=ATX_CLOSED
        md = '## Hello ##\n\n'

    def test_basic__i(self):
        # python-markdownify/tests/test_conversions.py
        html = '<i>Hello</i>'
        md = '*Hello*'

    def test_basic__ol(self):
        # python-markdownify/tests/test_conversions.py
        html = '<ol><li>a</li><li>b</li></ol>'
        md = '1. a\n2. b\n'

    def test_basic__p(self):
        # python-markdownify/tests/test_conversions.py
        html = '<p>hello</p>'
        md = 'hello\n\n'

    def test_basic__strong(self):
        # python-markdownify/tests/test_conversions.py
        html = '<strong>Hello</strong>'
        md = '**Hello**'

    def test_basic__ul(self):
        # python-markdownify/tests/test_conversions.py
        html = '<ul><li>a</li><li>b</li></ul>'
        md = '* a\n* b\n'

    def test_basic__nested_uls(self):
        """
        Nested ULs should alternate bullet characters.
        """
        # python-markdownify/tests/test_conversions.py
        html = nested_uls
        md = '* 1\n\t+ a\n\t\t- I\n\t\t- II\n\t\t- III\n\t\t\n\t+ b\n\t+ c\n\t\n* 2\n* 3\n'

    @unittest.SkipTest
    def test_basic__bullets(self):
        # python-markdownify/tests/test_conversions.py
        html = nested_uls
        md = '- 1\n\t- a\n\t\t- I\n\t\t- II\n\t\t- III\n\t\t\n\t- b\n\t- c\n\t\n- 2\n- 3\n'

    def test_basic__img__a(self):
        # python-markdownify/tests/test_conversions.py
        html = '<img src="/path/to/img.jpg" alt="Alt text" title="Optional title" />'
        md = '![Alt text](/path/to/img.jpg "Optional title")'

    def test_basic__img__b(self):
        # python-markdownify/tests/test_conversions.py
        html = '<img src="/path/to/img.jpg" alt="Alt text" />'
        md = '![Alt text](/path/to/img.jpg)'
        
    def test_basic__escaping__underscore(self):
        # python-markdownify/tests/test_escaping.py
        html = '_hey_dude_'
        md = '\_hey\_dude\_'

    def test_basic__escaping__xml_entities(self):
        # python-markdownify/tests/test_escaping.py
        html = '&amp;'
        md = '&'

    def test_basic__escaping__named_entities(self):
        # python-markdownify/tests/test_escaping.py
        html = '&raquo;'
        md = u'\xbb'

    def test_basic__escaping__hexadecimal_entities(self):
        # python-markdownify/tests/test_escaping.py
        # This looks to be a bug in BeautifulSoup (fixed in bs4) that we have to work around.
        html = '&#x27;'
        md = '\x27'

    def test_basic__escaping__single_escaping_entities(self):
        # python-markdownify/tests/test_escaping.py
        html = '&amp;amp;'
        md = '&amp;'


class TestHtmltoMarkdown(unittest.TestCase, _TestToMarkdownSpec):
    _test_actual = _TestToMarkdownSpec._test_html_to_markdown


class TestMarkdowntoMarkdown(unittest.TestCase, _TestToMarkdownSpec):
    _test_actual = _TestToMarkdownSpec._test_markdown_to_markdown
