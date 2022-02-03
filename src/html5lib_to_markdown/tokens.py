from __future__ import print_function
from __future__ import unicode_literals

"""
This file contains replacement html5lib Tokens.
Tokens are just Python dicts.

Note:
   1. they are implemented by functions, because we may need to alter their contents
   2. the private attribute `_md_type` stores their type for post-processing

Several custom keys are in each token:


* _md_type
    - the Token type
    - instead of storing as STR, store as INT via lookup table `mdTokenTypes`

* _md_prefix
    - if present, the token is in a blockquote and should be prefixed with this string

* _md_bq
    - if present, the token is in a blockquote of this level

* _md_cb
    - if present, the token is in a codeblock


"Block Elements" should be wrapped in:

    TokenStartBlockElement
        BlockElement
    TokenEndBlockElement

What is a BlockElement?

A Block Element is something that should be surrounded by two newlines in markdown
currently these tags are considered block elements:

    p
    div
    hn(h1-h6)
    hr
    pre
    code
    script
    blockquote

"""

# stdlib
from collections import OrderedDict
import os

# local
from .utils import safe_title


# ==============================================================================


DEBUG_TOKENS = bool(int(os.getenv("MD_DEBUG_TOKENS", 0)))


# ------------------------------------------------------------------------------


# use INTs for faster comparison of our '_md_type'
# unless `export MD_DEBUG_TOKENS=1` is set
mdTokenTypes = {
    "TokenAMarkdown": 1,
    "TokenAMarkdownReference": 2,
    "TokenAMarkdownSimple": 3,
    "TokenBoldItalic": 4,
    "TokenCharactersAdded": 5,
    "TokenCharactersSplit": 6,
    "TokenDebug": 7,
    "TokenEmphasis": 8,
    "TokenEndBlockElement": 9,
    "TokenEndBlockquote": 10,
    "TokenEndBlockNative": 11,
    "TokenEndCode": 12,
    "TokenHNStart": 13,
    "TokenHR": 14,
    "TokenImgMarkdown": 15,
    "TokenLiStart": 16,
    "TokenNewline": 17,
    "TokenNewlineBR": 18,
    "TokenNewlines": 19,
    "TokenSpace": 20,
    "TokenStartBlockElement": 21,
    "TokenStartBlockquote": 22,
    "TokenStartBlockNative": 23,
    "TokenStartCode": 24,
    "TokenStrong": 25,
    "TokenTab": 26,
}
if DEBUG_TOKENS:
    for k in list(mdTokenTypes.keys()):
        mdTokenTypes[k] = k

# ==============================================================================


def TokenAEndTag(href):
    return {"type": "EndTag", "name": "a"}


def TokenAMarkdown(href, _link_text, title=None, reference=None):
    title = safe_title(title)
    title = ' "%s"' % title if title else ""
    if reference is not None:
        data = "[%s][%s]" % (_link_text, reference)
    else:
        data = "[%s](%s%s)" % (_link_text, href, title)
    token = {
        "type": "Characters",
        "data": data,
        "_md_type": mdTokenTypes["TokenAMarkdown"],
    }
    return token


def TokenAMarkdownReference(href, reference, title=None):
    """
    [link text][1]
    [1]: <https://example.com> "Title"

    <a href="https://example.com" title="Title">link text</a>
    """
    title = ' "%s"' % title if title else ""
    data = "[%s]: %s%s" % (reference, href, title)

    token = {
        "type": "Characters",
        "data": data,
        "_md_type": mdTokenTypes["TokenAMarkdownReference"],
    }
    return token


def TokenAMarkdownSimple(href):
    """
    <https://example.com>
    """
    token = {
        "type": "EmptyTag",
        "name": href,
        "data": {},
        "_md_type": mdTokenTypes["TokenAMarkdownSimple"],
    }
    return token


def TokenAStartTag(href):
    return {
        "type": "StartTag",
        "name": "a",
        "data": OrderedDict([((None, "href"), href)]),
    }


def TokenBoldItalic(character="_"):
    """
    Bold & Italic (`<i><b>`, `<em><strong>`) text is rendered with three underscores or asterisks
    """
    assert character in ("_", "*")
    return {
        "type": "Characters",
        "data": character * 3,
        "_md_type": mdTokenTypes["TokenBoldItalic"],
    }


def TokenCharactersAdded(data=""):
    return {
        "type": "Characters",
        "data": data,
        "_md_type": mdTokenTypes["TokenCharactersAdded"],
    }


def TokenCharactersSplit(data=""):
    return {
        "type": "Characters",
        "data": data,
        "_md_type": mdTokenTypes["TokenCharactersSplit"],
    }


def TokenDebug(_debug=None):
    """used to place debug info; this will not render"""
    return {
        "type": "SpaceCharacters",
        "data": "",
        "_md_type": mdTokenTypes["TokenDebug"],
        "_md_debug": _debug,
    }


def TokenEmphasis(character="_"):
    """
    Italic (`<i>`, `<em>`) text is rendered with one asterisk or underscore
    """
    assert character in ("_", "*")
    return {
        "type": "Characters",
        "data": character,
        "_md_type": mdTokenTypes["TokenEmphasis"],
    }


def TokenEndBlockElement(block):
    """
    `TokenEndBlockElement` is used to denote that we are ending a block element.
    Under most circumstances, this token will not render anything.
    """
    return {
        "type": "SpaceCharacters",
        "data": "",
        "_md_type": mdTokenTypes["TokenEndBlockElement"],
        "_md_debug": block,
    }


def TokenEndBlockquote(depth=1):
    """
    `TokenEndBlockquote` is used to denote that we are ending a blockquote.
    This token will not render anything.
    """
    return {
        "type": "SpaceCharacters",
        "data": "",
        "_md_type": mdTokenTypes["TokenEndBlockquote"],
        "_md_depth": depth,
    }


def TokenEndCode():
    """
    `TokenEndCode` is used to denote that we are ending a `code` tag.
    The render type (inline, indented) is unknown
    """
    return {
        "type": "SpaceCharacters",
        "data": "",
        "_md_type": mdTokenTypes["TokenEndCode"],
    }


def TokenHNStart(h_num):
    token = {
        "type": "Characters",
        "data": "\n%s " % ("#" * h_num),
        "_md_hn": h_num,
        "_md_type": mdTokenTypes["TokenHNStart"],
    }
    return token


def TokenHR():
    return {
        "type": "Characters",
        "data": "\n---\n",
        "_md_type": mdTokenTypes["TokenHR"],
    }


def TokenImgMarkdown(src, alt=None, title=None, reference=None):
    alt = alt or "Image"
    title = ' "%s"' % title if title else ""
    if reference is not None:
        data = "[%s][%s]" % (alt, reference)
    else:
        data = "![%s](%s%s)" % (alt, src, title)
    token = {
        "type": "Characters",
        "data": data,
        "_md_type": mdTokenTypes["TokenImgMarkdown"],
    }
    return token


def TokenLiStart(depth=0, bullet="*"):
    if bullet in ("*", "+", "-"):
        pass
    else:
        if type(bullet) != int:
            raise ValueError("invalid bullet")
        bullet = "%s." % bullet
    indent = depth - 1 if depth >= 1 else 0
    token = {
        "type": "Characters",
        "data": "\n%s%s " % ("  " * indent, bullet),
        "_md_type": mdTokenTypes["TokenLiStart"],
        "_md_list_depth": indent,
    }
    return token


def TokenNewline(blockquoted=None, codeblocked=None):
    return {
        "type": "SpaceCharacters",
        "data": "\n",
        "_md_type": mdTokenTypes["TokenNewline"],
        "_md_bq": blockquoted,
        "_md_cb": codeblocked,
    }


def TokenNewlineBR():
    return {
        "type": "SpaceCharacters",
        "data": "\n",
        "_md_type": mdTokenTypes["TokenNewlineBR"],
    }


def TokenNewlines(blockquoted=None, codeblocked=None):
    return {
        "type": "SpaceCharacters",
        "data": "\n\n",
        "_md_type": mdTokenTypes["TokenNewlines"],
        "_md_bq": blockquoted,
        "_md_cb": codeblocked,
    }


def TokenSpace():
    return {
        "type": "SpaceCharacters",
        "data": " ",
        "_md_type": mdTokenTypes["TokenSpace"],
    }


def TokenStartBlockElement(block):
    """
    `TokenStartBlockElement` is used to denote that we are starting a new block element.
    Under most circumstances, this token will not render anything.
    """
    return {
        "type": "SpaceCharacters",
        "data": "",
        "_md_type": mdTokenTypes["TokenStartBlockElement"],
        "_md_block": block,
    }


def TokenStartBlockquote(depth=1):
    """
    `TokenStartBlockquote` is used to denote that we are starting a new blockquote
    Under most circumstances, this token will not render anything.
    """
    return {
        "type": "SpaceCharacters",
        "data": "",
        "_md_type": mdTokenTypes["TokenStartBlockquote"],
        "_md_depth": depth,
    }


def TokenStartCode():
    """
    `TokenStartCode` is used to denote that we are starting a new `code` tag.
    The render type (inline, indented) is unknown
    """
    return {
        "type": "Characters",
        "data": "",
        "_md_type": mdTokenTypes["TokenStartCode"],
    }


def TokenStrong(character="*"):
    """
    Bold (`<b>`, `<strong>`) text is rendered with two asterisks or underscores
    """
    assert character in ("*", "_")
    return {
        "type": "Characters",
        "data": "*" * 2,
        "_md_type": mdTokenTypes["TokenStrong"],
    }


def TokenTab():
    return {
        "type": "SpaceCharacters",
        "data": "\t",
        "_md_type": mdTokenTypes["TokenTab"],
    }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


__all__ = (
    "mdTokenTypes",
    "TokenAEndTag",
    "TokenAMarkdown",
    "TokenAMarkdownReference",
    "TokenAMarkdownSimple",
    "TokenAStartTag",
    "TokenCharactersAdded",
    "TokenCharactersSplit",
    "TokenDebug",
    "TokenEmphasis",
    "TokenEndBlockElement",
    "TokenEndBlockquote",
    "TokenEndCode",
    "TokenHNStart",
    "TokenHR",
    "TokenImgMarkdown",
    "TokenLiStart",
    "TokenNewline",
    "TokenNewlineBR",
    "TokenNewlines",
    "TokenSpace",
    "TokenStartBlockElement",
    "TokenStartBlockquote",
    "TokenStartCode",
    "TokenStrong",
    "TokenTab",
)
