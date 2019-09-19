from __future__ import print_function

import os
import html5lib_to_markdown
from html5lib_to_markdown.transformer import Transformer


_dir_base = os.path.dirname(__file__)

fname_md = os.path.join(_dir_base, "00-data-source_markdown.md")
with open(fname_md, "r") as fh:
    example_text_markdown = fh.read()

fname_html = os.path.join(_dir_base, "00-data-as_html.html")
with open(fname_html, "r") as fh:
    example_text_html = fh.read()


transformer = Transformer(
    a_as_tag=False,
    img_as_tag=False,
    strip_comments=False,
    strip_scripts=True,
    reference_style_link=False,
)

html_as_markdown = transformer.transform(example_text_html)
print("html_as_markdown")
print("=" * 30)
print(html_as_markdown)
print("=" * 30)
try:
    assert html_as_markdown == example_text_markdown
    print("ok!")
except:
    print("boo")
