from __future__ import print_function

import commonmark
import os

_dir_base = os.path.dirname(__file__)

fname_md = os.path.join(_dir_base, '00-data-source_markdown.md')
with open(fname_md, 'r') as fh:
    example_text_markdown = fh.read()

fname_html = os.path.join(_dir_base, '00-data-as_html.html')
with open(fname_html, 'r') as fh:
    example_text_html = fh.read()

markdown_as_html = commonmark.commonmark(example_text_markdown)
try:
    assert example_text_html == markdown_as_html
    print("ok!")
except:
    print ("example_text_html")
    print ("=" * 30)
    print (example_text_html)
    print ("=" * 30)
    print ("=" * 30)
    print ("markdown_as_html")
    print ("=" * 30)
    print (markdown_as_html)
    print ("=" * 30)
    print ("boo")