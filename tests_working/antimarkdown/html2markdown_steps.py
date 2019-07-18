# -*- coding: utf-8 -*-
"""html2markdown_steps -- feature step implementations for the antimarkdown HTML-to-Markdown translator.
"""
from os import path
import difflib
from behave import *


DATA = path.join(path.dirname(path.abspath(__file__)), 'data')


@given('I have a {file_base_name},')
def step(context, file_base_name):
    base = context.file_base_path = path.join(DATA, file_base_name)
    context.markdown_path = base + '.txt'
    context.html_path = base + '.html'


@when('I translate the HTML file to Markdown using antimarkdown')
def step_translate(context):
    import antimarkdown
    with open(context.html_path, encoding='utf-8') as fi:
        html = context.html_text = fi.read()
    context.translated_markdown_text = antimarkdown.to_markdown(html).rstrip()


@then('the resulting Markdown should match the corresponding text in the Markdown file.')
def step_check_md(context):
    with open(context.markdown_path, encoding='utf-8') as fi:
        markdown = context.markdown_text = fi.read().rstrip()
    assert context.translated_markdown_text == markdown, '\nDifferences:\n' + '\n'.join(
        difflib.context_diff([n.replace(' ', '.') for n in context.translated_markdown_text.splitlines()],
                             [n.replace(' ', '.') for n in markdown.splitlines()],
                             fromfile='Got', tofile='Expected'))
