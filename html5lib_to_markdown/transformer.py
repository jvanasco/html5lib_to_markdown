from __future__ import print_function
from __future__ import unicode_literals

"""

``to_markdown`` is a html5lib tree adapter that expects a compatible tree
``Transformer`` is a factory for generating objects that will invoke `to_markdown`

"""

# stdlib
if __debug__:
    import pprint
    import pdb
import os
import logging

log = logging.getLogger(__name__)

# pypi
import six
import html5lib
from html5lib import constants
from html5lib import HTMLParser
from html5lib import getTreeBuilder
from html5lib import getTreeWalker
from html5lib.serializer import HTMLSerializer
from html5lib.filters.base import Filter
from html5lib.constants import tokenTypes

# local
from .markdown_info import MARKDOWN_TAGS_CORE
from .markdown_info import MARKDOWN_TAGS_PASSTHROUGH
from .markdown_info import MARKDOWN_TAGS_PASSTHROUGH_BLOCKS
from .markdown_info import MARKDOWN_TAGS_ATTRIBUTES
from .tokens import *
from .utils import safe_title
from .utils import clean_token_attributes
from .utils import RE_newlines_2p__full
from .utils import RE_newlines_3p
from .utils import RE_space_tab_only
from .utils import RE_space_tab_p
from .utils import RE_whitespace_meh
from .utils import is_list_upcoming


# ==============================================================================


DEBUG_STACKS = bool(int(os.getenv("MD_DEBUG_STACKS", 0)))
DEBUG_STACKS_SIMPLE = bool(int(os.getenv("MD_DEBUG_STACKS_SIMPLE", 0)))


# ==============================================================================


# python-markdownify (http://github.com/matthewwithanm/python-markdownify) uses
# a technique where content is tossed into a div so BeautifulSoup will parse the
# fragment correctly.  the same trick works for html5lib
FRAGMENT_TYPE = "html5libmarkdown"
FRAGMENT_ID = "__CUSTOM_WRAPPER__"
wrapped = '<%s id="%s">%%s</%s>' % (FRAGMENT_TYPE, FRAGMENT_ID, FRAGMENT_TYPE)


# There will be a lot of comparisons to the TagType, so cast it to an `int`
# 1/2: this is our mapping. it is the `html5lib.constants.tokenTypes`
tt_Doctype = tokenTypes["Doctype"]
tt_Characters = tokenTypes["Characters"]
tt_SpaceCharacters = tokenTypes["SpaceCharacters"]
tt_StartTag = tokenTypes["StartTag"]
tt_EndTag = tokenTypes["EndTag"]
tt_EmptyTag = tokenTypes["EmptyTag"]
tt_Comment = tokenTypes["Comment"]
tt_ParseError = tokenTypes["ParseError"]

# mdTokenTypes is from `.tokens`
tt_md_TokenAMarkdown = mdTokenTypes["TokenAMarkdown"]
tt_md_TokenAMarkdownReference = mdTokenTypes["TokenAMarkdownReference"]
tt_md_TokenAMarkdownSimple = mdTokenTypes["TokenAMarkdownSimple"]
tt_md_TokenCharactersAdded = mdTokenTypes["TokenCharactersAdded"]
tt_md_TokenCharactersSplit = mdTokenTypes["TokenCharactersSplit"]
tt_md_TokenEmphasis = mdTokenTypes["TokenEmphasis"]
tt_md_TokenEndBlockElement = mdTokenTypes["TokenEndBlockElement"]
tt_md_TokenEndBlockquote = mdTokenTypes["TokenEndBlockquote"]
tt_md_TokenEndBlockNative = mdTokenTypes["TokenEndBlockNative"]
tt_md_TokenEndCode = mdTokenTypes["TokenEndCode"]
tt_md_TokenHNStart = mdTokenTypes["TokenHNStart"]
tt_md_TokenHR = mdTokenTypes["TokenHR"]
tt_md_TokenImgMarkdown = mdTokenTypes["TokenImgMarkdown"]
tt_md_TokenLiStart = mdTokenTypes["TokenLiStart"]
tt_md_TokenNewline = mdTokenTypes["TokenNewline"]
tt_md_TokenNewlineBR = mdTokenTypes["TokenNewlineBR"]
tt_md_TokenNewlines = mdTokenTypes["TokenNewlines"]
tt_md_TokenSpace = mdTokenTypes["TokenSpace"]
tt_md_TokenStartBlockElement = mdTokenTypes["TokenStartBlockElement"]
tt_md_TokenStartBlockquote = mdTokenTypes["TokenStartBlockquote"]
tt_md_TokenStartBlockNative = mdTokenTypes["TokenStartBlockNative"]
tt_md_TokenStartCode = mdTokenTypes["TokenStartCode"]
tt_md_TokenStrong = mdTokenTypes["TokenStrong"]
tt_md_TokenTab = mdTokenTypes["TokenTab"]

# these are tokens that will be filtered out of the final stack
_tts_md_filtered = [
    tt_md_TokenStartBlockElement,
    tt_md_TokenEndBlockElement,
    tt_md_TokenStartBlockquote,
    tt_md_TokenEndBlockquote,
]

# whitespace tokens
_tts_md_whitespace = [
    tt_md_TokenSpace,
    tt_md_TokenTab,
    tt_md_TokenNewline,
    tt_md_TokenNewlines,
    tt_md_TokenNewlineBR,
]

_tts_md_newlines_single = [tt_md_TokenNewline, tt_md_TokenNewlineBR]

_tts_md_newlines_all = [tt_md_TokenNewline, tt_md_TokenNewlineBR, tt_md_TokenNewlines]

_tts_md_startblocks = [tt_md_TokenStartBlockquote, tt_md_TokenStartBlockElement]
_tts_md_endblocks = [tt_md_TokenEndBlockquote, tt_md_TokenEndBlockElement]

_tts_md_blocksall = _tts_md_startblocks + _tts_md_endblocks

_tts_md_blockquotes = [tt_md_TokenStartBlockquote, tt_md_TokenEndBlockquote]

_tts_md_newlined_text_start = [tt_md_TokenHR, tt_md_TokenHNStart, tt_md_TokenLiStart]

_tts_md_newlined_text_end = [tt_md_TokenHR]

_tts_md_code = [tt_md_TokenStartCode, tt_md_TokenEndCode]

# these tags will render contents as-is
tag_names_sensitive__block = ("pre", "script")  # as a block
tag_names_sensitive__inline = ("code",)  # inline
tag_names_sensitive = tag_names_sensitive__block + tag_names_sensitive__inline


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def token_apply_prefix(token, blockquote=None, codeblock=None):
    """
    prefixes the lines

    old method
    token['data'] = token['data'].replace('\n', '\n%s' % prefix)
    """
    if (not blockquote) and (not codeblock):
        return
    try:
        if "\n" not in token["data"]:
            return
        _prefix = ""
        if blockquote:
            _prefix = (">" * blockquote) + " "
        if codeblock:
            _prefix += " " * codeblock * 4
        token["data"] = token["data"].replace("\n", "\n%s" % _prefix)
        if token["type"] == "SpaceCharacters":
            token["type"] = "Characters"
    except AttributeError as exc:
        # this triggers if the data is a dict
        # which happens on native tags
        # just ignore it!
        return
    except KeyError as exc:
        # this triggers if there is no data
        # which happens on native tags
        # just ignore it!
        return
    except Exception as exc:
        # this triggers if the data isn't a string. it's fine!
        print("xxxxx token_apply_prefix", type(exc), exc, token)
        # pdb.set_trace()
        return


def _contextual_TokenNewlines(newlines=2, blockquoted=None, codeblocked=None):
    """
    This function generates a TokenNewlines/TokenNewline
    and applies `token_apply_prefix` to it if necessary.
    """
    if newlines == 2:
        token = TokenNewlines(blockquoted=blockquoted, codeblocked=codeblocked)
    else:
        token = TokenNewline(blockquoted=blockquoted, codeblocked=codeblocked)

    token_apply_prefix(token, blockquote=blockquoted, codeblock=codeblocked)
    return token


def stack__last_token(stack):
    return stack[-1] if stack else None


def stack__first_token(stack):
    return stack[0] if stack else None


def _stack__print_simple(stack):
    """debugging tool; nicely formatted stack view"""
    print("----------------")
    for idx, i in enumerate(stack):
        print(
            "%04d" % idx,
            "%22s" % i.get("_md_type"),
            "%15s" % i.get("type"),
            ("%5s" % i.get("name", ""))[:5],
            "bq-%4s" % i.get("_md_bq", ""),
            "cb-%4s" % i.get("_md_cb", ""),
            "data-%30s" % i.get("data", "").__repr__(),
            i.get("_md_debug", ""),
        )
    print("----------------")


def _stack__print_full(stack):
    """debugging tool"""
    print("----------------")
    for idx, i in enumerate(stack):
        print("%04d" % idx, i)
    print("----------------")


def _stack__print(stack, stack_name="debug"):
    """debugging tool"""
    print("----------------")
    print("-> %s stack >-" % stack_name)
    if DEBUG_STACKS_SIMPLE:
        _stack__print_simple(stack)
    else:
        _stack__print_full(stack)
    print("-< %s stack <-" % stack_name)
    print("----------------")


def cleanup_space_backwards(
    stack, newlines_ensure=0, newline_blockquote=None, newline_codeblock=None, dbg=False
):
    """
    this functions rewinds a stack of tags to pop newline elements off the top
    """
    _discarded = None  # an iteration of this function inspected this token
    newline_prefix = (newline_blockquote,)
    while True:
        _lt = stack__last_token(stack)
        if _lt:
            _md_type = _lt.get("_md_type")
            if _md_type in _tts_md_whitespace:
                if _md_type in _tts_md_newlines_all:
                    _lt_blockquoted = _lt.get("_md_bq")
                    _lt_codeblocked = _lt.get("_md_cb")
                    _lt_prefix = (_lt_blockquoted,)
                    if newline_prefix != _lt_prefix:
                        newlines_ensure = 1
                        if _md_type == tt_md_TokenNewlines:
                            _discarded = stack.pop()
                            _lt2 = stack__last_token(stack)
                            if (
                                _lt2
                                and _lt2.get("_md_type") in _tts_md_newlined_text_end
                            ):
                                newlines_ensure = 0
                                _tok = _contextual_TokenNewlines(
                                    newlines=2,
                                    blockquoted=_lt_blockquoted,
                                    codeblocked=_lt_codeblocked,
                                )
                            else:
                                _tok = _contextual_TokenNewlines(
                                    newlines=1,
                                    blockquoted=_lt_blockquoted,
                                    codeblocked=_lt_codeblocked,
                                )
                            stack.append(_tok)
                        break
                _discarded = stack.pop()
            else:
                break
        else:
            break

    if newlines_ensure:
        # wait, is the last item a HR?
        _lt = stack__last_token(stack)
        if not _lt:
            newlines_ensure -= 1
        elif _lt and (_lt.get("_md_type") in _tts_md_newlined_text_end):
            newlines_ensure -= 1

        if newlines_ensure:
            _blockquoted = newline_blockquote
            _codeblocked = newline_codeblock
            _tok = _contextual_TokenNewlines(
                newlines_ensure, blockquoted=_blockquoted, codeblocked=_codeblocked
            )
            stack.append(_tok)

    # stack.extend(_discards)
    return stack


def _render_code_as_block_backwards(stack_post):
    """
    Given a post-processed stack `stack_post`, iterate backwards looking for tokens
    that will let us know if we are in a new block or not
    """
    idx = len(stack_post)
    while idx >= 1:
        idx -= 1
        tok = stack_post[idx]
        tok_mdtype = tok.get("_md_type")
        if not tok_mdtype:
            # likely `Characters` or a tag
            return False
        if tok_mdtype in _tts_md_newlines_all:
            continue
        elif tok_mdtype == tt_md_TokenStartBlockElement:
            return True
        elif tok_mdtype == tt_md_TokenStartBlockNative:
            if tok.get("name") == "pre":
                tok["_md_code_compress"] = 1
                return True
    return True


def _render_code_as_block_frontwards(stack, idx):
    """
    given a stack the postprocesser is currently looking at, iterate forwards
    looking for a token that indicates our codelblock type
    """
    maxlen = len(stack)
    _endcode_seen = False
    while idx <= maxlen:
        idx += 1
        tok = stack[idx]
        tok_mdtype = tok.get("_md_type")
        if not _endcode_seen:
            if tok_mdtype == tt_md_TokenEndCode:
                _endcode_seen = True
            continue
        if not tok_mdtype:
            # likely `Characters` or a tag
            return False
        if tok_mdtype in _tts_md_newlines_all:
            continue
        elif tok_mdtype == tt_md_TokenEndBlockElement:
            return True
        elif tok_mdtype == tt_md_TokenEndBlockNative:
            if tok.get("name") == "pre":
                tok["_md_code_compress"] = 1
                return True
    return True


def to_markdown(
    dom_walker,
    a_as_tag=True,
    a_simple_links=True,
    parse_markdown_simplelink=True,
    img_as_tag=True,
    strip_comments=False,
    strip_scripts=True,
    reference_style_link=False,
    reference_style_img=False,
    div_as_block=True,
    allowed_tags=None,
    allowed_tags_blocks=None,
    allowed_tags_attributes=None,
    character_italic=None,
    character_bold=None,
    character_italicbold=None,
    character_unordered_listitem=None,
    pre_behavior=None,
    is_fragment=None,
):
    """
    translate a html5lib iterable tree to markdown

    most users will not want to call this, and instead call `Transform.transform`

    :arg html5lib-tree dom_walker: a tree to walk

    :arg bool a_as_tag: Should links that wrap text be rendered as a HTML
    tag or in markdown syntax? Links that wrap elements will always be
    rendered as HTML. default ``True``

    :arg bool a_simple_links: Markdown has a syntax to simplify simple links, in
    which the target and text are the same, using a single empty tag like such:
    "<https://example.com/path/to>".  If ``True``, the simple link format will
    be utilized for self-linking links; otherwise they will be rendered based on
    the selected ``a_as_tag`` rule.  default ``True``
    
    :arg bool parse_markdown_simplelink: Allow a Markdown simplelink in the 
    parsed HTML.  These parse a bit oddly, but hey.  default ``True``.

    :arg bool img_as_tag: Should images be rendered as a HTML
    tag or in markdown syntax? default ``True``

    :arg bool strip_comments: Should comment tags be stripped? default ``False``

    :arg bool strip_scripts: Should script tags be stripped? default ``True``

    :arg bool reference_style_link: Should markdown links be rendered as
    reference style or shown inline? default ``False``. does nothing if
    `a_as_tag` is True.

    :arg bool reference_style_img: Should markdown images be rendered as
    reference style ors shown inline?  default ``False``.  does nothing if
    `img_as_tag` is True.

    :arg bool div_as_block: Should a `div` element be treated as a block like
    p tags?  default ``True``.  If ``False``, div tags will be ignored and stripped.

    :arg list allowed_tags:  list of allowed pass-through tags. default is
    ``None``, which will invoke  ``markdown_info.MARKDOWN_TAGS_PASSTHROUGH``.

    :arg list allowed_tags_blocks:  list of allowed pass-through tags to be treated
    as block elements. default is ``None``, which will invoke  ``markdown_info.MARKDOWN_TAGS_PASSTHROUGH_BLOCKS``.
    This must be a subset of ``allowed_tags```

    :arg dict allowed_tags_attributes:  keys are tags, values are a list of
    attributes for that tag.  default is ``None``, which will invoke
    ``markdown_info.MARKDOWN_TAGS_ATTRIBUTES``.

    :arg string character_italic: What character should be the default for italic text.
    Markdown supports an asterisk "*" or underscores "_"; and will render 1 of this character. Default: "_"

    :arg string character_bold: What character should be the default for bold text.
    Markdown supports an asterisk "*" or underscores "_"; and will render 2 of this character. Default: "*"

    :arg string character_italicbold: What character should be the default for italic+bold text.
    Markdown supports an asterisk "*" or underscores "_"; and will render 3 of this character. Default: "*"

    :arg string character_unordered_listitem: What character should be the default for unordered list items.
    Markdown supports an asterisk "*" or dash "-" or plus '+'; and will render 1 of this character. Default: "*"

    :arg INT pre_behavior: how should <pre> tags be handled?
    note: "pre -> code" ALWAYS becomes markdown 'code'
    option 1: non-code "pre" becomes markdown "code"
    option 2: non-code "pre" becomes a paragraph

    :arg bool is_fragment: is this being processed as a fragment? if so, we
    should pop out the container.
    """
    # defaults
    allowed_tags = MARKDOWN_TAGS_PASSTHROUGH if allowed_tags is None else allowed_tags
    allowed_tags_blocks = (
        MARKDOWN_TAGS_PASSTHROUGH_BLOCKS
        if allowed_tags_blocks is None
        else allowed_tags_blocks
    )
    allowed_tags_attributes = (
        MARKDOWN_TAGS_ATTRIBUTES
        if allowed_tags_attributes is None
        else allowed_tags_attributes
    )

    character_italic = character_italic if character_italic in ("*", "_") else "_"
    character_bold = character_bold if character_bold in ("*", "_") else "*"
    character_italicbold = (
        character_italicbold if character_italicbold in ("*", "_") else "*"
    )
    character_unordered_listitem = (
        character_unordered_listitem
        if character_unordered_listitem in ("*", "-", "+")
        else "*"
    )

    # for tracking depth
    _in = {
        "a": 0,
        "a__tag": 0,
        "p-div": 0,
        "_stack": [],
        "blockquote": 0,  # depth tracing
        "codeblock": None,  # True/False
        "_sensitive": 0,  # are we in a sensitive block? (code, pre, script)
        "_strip_script": 0,  # are we in a script? if so, we may be stripping it so this is treated separately
        "list": [],  # depth tracing, should be a list of lists, where main list is depth and inner list is a dict of type+count that we're on
    }
    _referenced_links__order = []
    _referenced_links__data = {}

    # this will be a list of nodes
    token_stack = []

    # an early version of this used a generator to iterate over tokens
    # however...
    # searching forwards and backwards was needed, so iterating over them is used
    list_walker = [i for i in dom_walker]
    len_walker = len(list_walker)

    def _handle_bare_link(name, token):
        """this logic can be invoked in multiple places"""
        _path_components = list(token.get("data").items())
        if len(_path_components) == 1:
            _path = _path_components
        else:
            # !!!: this bit is weird.
            if six.PY2:
                _path = [_path_components[1], _path_components[0]]
                if len(_path_components) > 2:
                    _path.extend(_path_components[2:])
            else:
                _path = _path_components
        _url_reconstructed = "%s//%s" % (
            name,
            "/".join(i[0][1] for i in _path),
        )
        if _path[-1][1]:
            _url_reconstructed += "=" + _path[-1][1]

        if a_simple_links:
            return TokenAMarkdownSimple(_url_reconstructed)

        if a_as_tag:
            return (TokenAStartTag, _url_reconstructed, TokenAEndTag)
        return TokenAMarkdown(_url_reconstructed, _url_reconstructed)


    def possibly_nested(func):
        """
        This is a decorator used to stash the blockquote depth and prefix into
        each processed token.  This function does not apply the prefix to the
        token's "data", but updates the token's dict with the prefix information.
        """

        def wrapper(*args):
            results_og = results = func(*args)
            if results is None:
                return None
            # it is possible to receive a tuple of nodes from the function
            if not isinstance(results, tuple):
                results = (results,)
            rval = []
            for _result in results:
                # result could be None
                if _result:
                    if _in["blockquote"]:
                        _result["_md_bq"] = _in["blockquote"]
                    if _in["codeblock"]:
                        _result["_md_cb"] = True
                    rval.append(_result)
            rval = tuple(rval) if rval else None
            return rval

        return wrapper

    @possibly_nested
    def _process_token_idx(token_idx):
        """
        ``_process_token_sequence``
        instead of __iter__ we use a `custom_slider_a`

        handling of nested blockquotes?
        instead of recursively calling a function on a tree, use a decorator
        """
        token = list_walker[token_idx]
        _token_idx__next = token_idx + 1
        _token_idx__next1 = token_idx + 2
        token_next = (
            list_walker[_token_idx__next] if _token_idx__next < len_walker else None
        )
        token_next1 = (
            list_walker[_token_idx__next1] if _token_idx__next1 < len_walker else None
        )

        ttype = token["type"]
        # There will be a lot of comparisons to the TagType, so cast it to an `int`
        # s/2: this is our casting
        ttype = tokenTypes.get(ttype, None)
        name = token.get("name")
        
        # are we stripping script tags?
        if strip_scripts:
            if _in["_strip_script"]:
                if name == "script":
                    if ttype == tt_StartTag:
                        _in["_strip_script"] += 1
                        return None
                    else:  # assume tt_EndTag
                        _in["_strip_script"] -= 1
                        return None
                return None

        # if we are in a sensitive block, check to see if it is eligible to get out of
        if _in["_sensitive"]:
            if name not in tag_names_sensitive:  # ('code', 'pre', 'script', )
                # if ttype == tt_SpaceCharacters:
                #    _last_sig = stack__last_token(token_stack)
                #    if _last_sig.get('_md_type') in (tt_md_TokenStartCode, ):
                #        # !!!: if we just started a codeblock, ignore newlines
                #        return None
                return token
            if ttype == tt_StartTag:
                _in["_sensitive"] += 1
                if name == "code":
                    return TokenStartCode()
                return token
            if ttype == tt_EndTag:
                if _in["_sensitive"] >= 2:
                    _in["_sensitive"] -= 1
                    if name == "code":
                        return TokenEndCode()
                    return token

        if ttype in (tt_StartTag, tt_EndTag):

            # remove empty tags, which can be an artifact of the html5lib parser
            # unless, they are a markdown link
            if ttype == tt_StartTag:
                if (
                    token_next
                    and (token_next.get("type") == "EndTag")
                    and (token_next.get("name") == name)
                ):
                    if name in ("http:", "https:"):
                        return _handle_bare_link(name, token)
                    return None
            elif ttype == tt_EndTag:
                token_prev = list_walker[token_idx - 1] if token_idx > 0 else None
                if (
                    token_prev
                    and (token_prev.get("type") == "StartTag")
                    and (token_prev.get("name") == name)
                ):
                    return None
            # end removal

            # note: tokenType StartTag/EndTag
            if name in ("p", "div"):
                # note: p, div
                if name == "div":
                    if not div_as_block:
                        return None
                if ttype == tt_StartTag:
                    _in["p-div"] += 1
                    _in["_stack"].append(name)
                    return TokenStartBlockElement(name)
                else:
                    _in["p-div"] -= 1
                    _in["_stack"].pop()
                    return TokenEndBlockElement(name)

            elif name in ("ul", "ol"):
                # note: ul, ol
                # only return a `TokenStartBlockElement` or `TokenEndBlockElement`
                # for a first-level list. otherwise the list items are part of
                # the encapsulating block; so return None
                if ttype == tt_StartTag:
                    # _in['list'] += 1  # old method
                    _list_tracker = {"type": name, "count": 0}
                    _in["list"].append(_list_tracker)
                    if len(_in["list"]) == 1:
                        return TokenStartBlockElement(name)
                    return None
                elif ttype == tt_EndTag:
                    # _in['list'] -= 1  # old method
                    _list_tracker = _in["list"].pop()
                    if is_list_upcoming((token_next, token_next1)):
                        return None
                    return TokenEndBlockElement(name)

            elif name == "li":
                # note: li
                if ttype == tt_StartTag:
                    _in["_stack"].append("li")
                    _list_depth = len(_in["list"])
                    _list_tracker = _in["list"][-1]
                    if _list_tracker["type"] == "ul":
                        _list_bullet = "*"
                    else:
                        _list_tracker["count"] += 1
                        _list_bullet = _list_tracker["count"]
                    return TokenLiStart(depth=_list_depth, bullet=_list_bullet)
                else:  # tt_EndTag
                    _in["_stack"].pop()
                    return None

            elif name in ("i", "em"):
                # note: i, em
                # StartTag/EndTag are the same
                return TokenEmphasis(character_italic)

            elif name in ("b", "strong"):
                # note: b, strong
                # StartTag/EndTag are the same
                return TokenStrong(character_bold)

            elif name == "a":
                # note: a
                if ttype == tt_StartTag:
                    _in["a"] += 1

                    def _render_tag__a():
                        if a_as_tag:
                            return True
                        if (
                            token_next
                            and ((token_next["type"] == "Characters"))
                            and token_next1
                            and (
                                (token_next1["type"] == "EndTag")
                                and (token_next1["name"] == "a")
                            )
                        ):
                            return False
                        return True

                    _render_tag = True if _render_tag__a() else False
                    if _render_tag:
                        _in["a__tag"] += 1
                        return clean_token_attributes(
                            token, "a", allowed_tags_attributes
                        )
                    else:
                        _href = None
                        # _link_text
                        _title = None
                        _reference = None

                        # grab the next token from
                        if token_next["type"] != "Characters":
                            raise ValueError("DEBUG!!!!! this should never happen!")
                        _link_text = token_next["data"]
                        token_next["data"] = ""
                        for _key, _value in token["data"].items():
                            if _key[1] == "href":
                                _href = _value
                            elif _key[1] == "title":
                                _title = safe_title(_value)

                        if a_simple_links:
                            if (not _link_text or (_link_text == _href)) and (
                                not _title
                            ):
                                return TokenAMarkdownSimple(_href)

                        if reference_style_link:
                            try:
                                _reference = _referenced_links__order.index(_href)
                            except ValueError:
                                _referenced_links__order.append(_href)
                                _referenced_links__data[_href] = (_title,)
                                _reference = len(_referenced_links__order)
                        return TokenAMarkdown(
                            _href, _link_text, title=_title, reference=_reference
                        )

                elif ttype == tt_EndTag:
                    _render_tag = False
                    _in["a"] -= 1
                    if _in["a__tag"]:
                        _in["a__tag"] -= 1
                        _render_tag = True
                    if _render_tag:
                        return clean_token_attributes(
                            token, "a", allowed_tags_attributes
                        )
                    else:
                        return None

            elif name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                # note: h1, h2, h3, h4, h5, h6
                if ttype == tt_StartTag:
                    _in["_stack"].append(name)
                    h_num = int(name[1])
                    return (TokenStartBlockElement(name), TokenHNStart(h_num))
                elif ttype == tt_EndTag:
                    _in["_stack"].pop()
                    return TokenEndBlockElement(name)

            elif name == "blockquote":
                # note: blockquote
                # fixme: handle blockquotes
                if ttype == tt_StartTag:
                    _in["blockquote"] += 1
                    return (
                        TokenStartBlockElement("blockquote"),
                        TokenStartBlockquote(_in["blockquote"]),
                    )
                elif ttype == tt_EndTag:
                    _in["blockquote"] -= 1
                    return (
                        TokenEndBlockquote(_in["blockquote"]),
                        TokenEndBlockElement("blockquote"),
                    )
                return None

            elif name in tag_names_sensitive:
                # note: code
                # note: pre
                # note: script
                # tag_names_sensitive = code, pre, script
                # tag_names_sensitive__block = pre, script
                # tag_names_sensitive__inline = code
                if strip_scripts:
                    if name == "script":
                        if ttype == tt_StartTag:
                            _in["_strip_script"] += 1
                            return None
                        else:  # assume tt_EndTag
                            _in["_strip_script"] -= 1
                            return None
                    # continue as normal
                _token = clean_token_attributes(token, name, allowed_tags_attributes)
                if ttype == tt_StartTag:
                    # _in[name] += 1
                    _in["_sensitive"] += 1
                    # code is special!
                    if name == "code":
                        _in["codeblock"] = True
                        return TokenStartCode()
                    if name in tag_names_sensitive__block:
                        # inject a markdown type so we can process this better
                        _token["_md_type"] = tt_md_TokenStartBlockNative
                        return (TokenStartBlockElement(name), _token)
                    return _token
                elif ttype == tt_EndTag:
                    # _in[name] -= 1
                    _in["_sensitive"] -= 1
                    # code is special!
                    if name == "code":
                        _in["codeblock"] = None
                        return TokenEndCode()
                    if name in tag_names_sensitive__block:
                        # inject a markdown type
                        _token["_md_type"] = tt_md_TokenEndBlockNative
                        return (_token, TokenEndBlockElement(name))
                    return _token

            elif name in ("https:", "http:"):
                if parse_markdown_simplelink:
                    # note: bare url, bug-ish
                    # note: the htmllib5 parser will pull this as-
                    #      `name``: domain
                    #      `data`: elements of the path in an OrderedDict
                    if ttype == tt_StartTag:
                        return _handle_bare_link(name, token)
                    else:
                        return None
                else:
                    return None

            else:
                if name.startswith("mailto:"):
                    if parse_markdown_simplelink:
                        # note: mailto link
                        # this is a bare mailto
                        if ttype == tt_StartTag:
                            _address = name
                            if a_simple_links:
                                return TokenAMarkdownSimple(_address)
                            if a_as_tag:
                                return (TokenAStartTag, _address, TokenAEndTag)
                            return TokenAMarkdown(_address, _address[7:])
                        else:
                            return None
                    else:
                        return None

                # debug:
                if name == FRAGMENT_TYPE:
                    return None
                elif name in MARKDOWN_TAGS_CORE:
                    # this should have been converted
                    raise ValueError("DEBUG!!!!! this should never happen!", token)
                elif name in allowed_tags:
                    # sanitize the token
                    token = clean_token_attributes(token, name, allowed_tags_attributes)
                    if name in allowed_tags_blocks:
                        if ttype == tt_StartTag:
                            return (TokenStartBlockElement(name), token)
                        elif ttype == tt_EndTag:
                            return (token, TokenEndBlockElement(name))
                    return token

                else:
                    log.debug("removing token: %s", token)
                    return None

        elif ttype == tt_EmptyTag:
            # note: tokenType EmptyTag

            name = token["name"]

            if name == "img":
                # note: img
                if img_as_tag:
                    token = clean_token_attributes(
                        token, "img", allowed_tags_attributes
                    )
                    return token
                else:
                    _href = None
                    _alt = None
                    _title = None
                    _reference = None
                    for _key, _value in token["data"].items():
                        if _key[1] == "src":
                            _href = _value
                        elif _key[1] == "alt":
                            _alt = _value
                        elif _key[1] == "title":
                            _title = safe_title(_value)
                    if reference_style_img:
                        try:
                            _reference = _referenced_links__order.index(_href)
                        except ValueError:
                            _referenced_links__order.append(_href)
                            _referenced_links__data[_href] = (_title,)
                            _reference = len(_referenced_links__order)

                    return TokenImgMarkdown(
                        _href, alt=_alt, title=_title, reference=_reference
                    )

            elif name == "br":
                # note: br
                # !!!: whitespace preventatitive
                # if _in['script'] or _in['pre'] or _in['code']:
                if _in["_sensitive"]:
                    return None
                elif _in["list"]:
                    return None
                if token_stack:
                    _lt = stack__last_token(token_stack)
                    _lt_md_type = _lt.get("_md_type")
                    if _lt_md_type:
                        if _lt_md_type == tt_md_TokenNewlines:
                            return None
                        elif _lt_md_type in _tts_md_newlines_single:
                            return None
                return TokenNewlineBR()

            elif name == "hr":
                # note: hr
                return (
                    TokenStartBlockElement(name),
                    TokenHR(),
                    TokenEndBlockElement(name),
                )

            else:
                return clean_token_attributes(token, None, allowed_tags_attributes)

        elif ttype == tt_Characters:
            # note: tokenType Characters

            # dereference this first
            _data = token["data"]

            # remove extraneous newlines
            _data = RE_newlines_3p.sub("\n\n", _data)

            # remove extraneous spaces/tabs
            _data = RE_space_tab_p.sub(" ", _data)

            # drop leading space, but avoid nested lists
            _data = RE_whitespace_meh.sub("\n", _data)

            if _in["p-div"]:
                # if we're in a p/div block, then we pretty much ignore whitespace
                # this is to pull the text out as if we are a browser
                _data = _data.replace("\n\n", " ")
                _data = _data.replace("\n", " ")
                _data = RE_space_tab_p.sub(" ", _data)

            # remove leading/trailing whitespace
            token["data"] = _data.strip()

            # so... this bit is FUN
            # in order to better process our blocks/newlines for nesting and
            # prefixing, we should split the data into a series of newlines
            # and characters
            _lines = _data.split("\n")
            if len(_lines) > 1:
                _stack = []
                for _line in _lines:
                    _stack.append(TokenCharactersSplit(_line))
                    _stack.append(TokenNewline())
                # pop the last off
                _stack.pop()
                return tuple(_stack)

            return token

        elif ttype == tt_SpaceCharacters:
            # note: tokenType SpaceCharacters
            # !!!: redundant whitespace preventative
            # standardize the token to something we can easily inspect
            _last_sig = stack__last_token(token_stack)

            # whitespace should not be collapsed here
            # if _in['script'] or _in['pre'] or _in['code']:
            if _in["_sensitive"]:
                return token

            # do we necessarily care about this?
            # check the last significant token
            _last_sig = stack__last_token(token_stack)
            if _last_sig:
                _last_sig_md = _last_sig.get("_md_type")
                if _last_sig_md in (tt_md_TokenLiStart, tt_md_TokenHR):
                    return None
                elif _last_sig_md in _tts_md_startblocks:
                    # did we just start a block element? great. ignore leading whitespace
                    return None
                elif _last_sig_md in _tts_md_endblocks:
                    # did we just end a block element?  if so, NEWLINES
                    token = TokenNewlines()
                    if __debug__:
                        token["_md_whitespace_standardized"] = 0
                    return token

            # ok, process it...
            _data = token["data"]
            _newlines = None
            if _data == "\n\n":
                token = TokenNewlines()
                if __debug__:
                    token["_md_whitespace_standardized"] = 1
                _newlines = 2
            elif _data == "\n":
                token = TokenNewline()
                if __debug__:
                    token["_md_whitespace_standardized"] = 2
                _newlines = 1
            else:
                # is the token just spaces/tabs?
                # or does it have newlines?
                if RE_space_tab_only.match(_data):
                    # if this is only space/tabs, collapse to a single space
                    token = TokenSpace()
                    token["data"] = _data = " "
                    if __debug__:
                        token["_md_whitespace_standardized"] = 3
                    _newlines = 0
                else:
                    # if there are mixed newlines in here, we're going to drop
                    # down to the newlines only
                    _newlines = _data.count("\n")
                    if not _newlines:
                        raise ValueError("DEBUG!!!! Not sure what to do: %s" % token)
                    if _newlines >= 2:
                        token = TokenNewlines()
                        if __debug__:
                            token["_md_whitespace_standardized"] = 4
                        _newlines = 2
                    elif _newlines == 1:
                        token = TokenNewline()
                        if __debug__:
                            token["_md_whitespace_standardized"] = 5
                        _newlines = 2

            # we don't respect newlines within a list
            if _in["list"]:
                if _newlines:
                    return None

            # originally this checked if the last token was a blockquote
            # now we want to check only significant (stack accepted) tokens
            # we also want to check against any block element
            if not token_stack:
                # do not recognize initial newlines/spaces
                return None

            # check the last significant token
            # last_sig = stack__last_token(token_stack)  # calculated above
            _last_sig_md = _last_sig.get("_md_type")
            _last_sig_type = _last_sig.get("type")

            if (
                _last_sig_md in _tts_md_startblocks
            ):  # (tt_md_TokenStartBlockElement, tt_md_TokenStartBlockquote)
                # ignore newlines immediately after we start a block element
                return None

            elif _last_sig_md == tt_md_TokenNewlines:
                return None

            elif _last_sig_md in _tts_md_newlines_single:
                if token.get("_md_type") in _tts_md_newlines_all:
                    _dicarded = token_stack.pop()
                    token = TokenNewlines()
                    if __debug__:
                        token["_md_whitespace_standardized"] = 6

            return token

        elif ttype == tt_Comment:
            # note: tokenType Comment

            if strip_comments:
                return None
            else:
                return token
        else:
            # note: tokenType Unknown

            # debug
            log.debug("process token; unknown case: %s, %s", ttype, token)
            # print(ttype, token)
            # pdb.set_trace()
            # raise ValueError('what is this?')
            return token

    # !!!: STEP 1- parse to a markdown tree
    """
    iterate through the tokens with `custom_slider_a`, which shows us what
    the previous/next tokens are.  an iterated window of tags is passed
    to the `_process_token_sequence` function.

    a multi-window view of tags is needed to correctly process <a> tags

    for example- this can be rendered as an html structure or a markdown link
        html: <a href="https://example.com">my link to example.com</a>

        token: StartTag: A
        token_next: Characters: my link to example.com
        token_next1: EndTag: A

    but this must be rendered as a html structure:

        html: <a href="https://example.com"><img src="/path/to/img.png"></a>

        token: StartTag: A
        token_next: StartTag: IMG

    actual processing of the iteration was pushed into a separate function,
    so we can keep track of the last yielded tag.
    """
    for idx in range(0, len_walker):
        tokens_converted = _process_token_idx(idx)
        if not tokens_converted:  # faster than checking for `None`
            continue
        # if we return a tuple, the first element should be a `TokenStartBlockElement`
        if isinstance(tokens_converted, tuple):
            token_stack.extend(tokens_converted)
        else:
            token_stack.append(tokens_converted)

    # !!!: STEP 2a- strip the temporary wrapper we added
    if is_fragment:
        if token_stack:
            _tok = token_stack[0]
            if (_tok.get("name") == FRAGMENT_TYPE) and (
                _tok.get("data", {}).get((None, "id")) == FRAGMENT_ID
            ):
                token_stack = token_stack[1:-1]

    # !!!: STEP 3- merge in any link references for img/a
    if _referenced_links__order:
        _last_sig = stack__last_token(token_stack)
        if _last_sig:
            _t_md = _last_sig.get("_md_type")
            if _t_md in _tts_md_whitespace:
                # drop a trailing newline/newlines/newlinebr/tab/space and
                # replace with newlines marked by 'reflinks'
                _discarded = token_stack.pop()
            token_stack.append(TokenNewlines())
            token_stack.append(TokenStartBlockElement("reflinks-start"))
            for (_idx, _href) in enumerate(_referenced_links__order):
                _reference = _idx + 1
                (_title,) = _referenced_links__data[_href]
                token_stack.append(TokenNewline())
                tok = TokenAMarkdownReference(_href, _reference, _title)
                token_stack.append(tok)
            token_stack.append(TokenEndBlockElement("reflinks-end"))

    # used for debugging
    if __debug__:
        if DEBUG_STACKS:
            _stack__print(token_stack, "raw")

    # !!!: STEP 4- postprocess the tree
    # - goal 1: correct whitespace
    # - goal 2: toggle blockquote
    token_stack__post = []
    if __debug__:
        _dbg = False
    _last_codeblock = None
    _codeblocked = None
    for (token_idx, token) in enumerate(token_stack):
        _t_md = token.get("_md_type")
        _t_md_blockquote = token.get("_md_bq", None)
        token_prev = token_stack[token_idx - 1] if token_idx else None
        _t_prev_md = token_prev.get("_md_type") if token_prev else None
        try:
            token_next = token_stack[token_idx + 1]
        except:
            token_next = None
        _t_next_md = token_next.get("_md_type") if token_next else None

        if (
            _t_md in _tts_md_startblocks
        ):  # (tt_md_TokenStartBlockquote, tt_md_TokenStartBlockElement, )
            # if we're going block-to-block, skip to the next block
            if _t_next_md in _tts_md_startblocks:
                continue

            # is the next line newlines? if so, stop!
            if _t_next_md in _tts_md_newlines_all:
                continue

            _newlines_ensure = 2
            _newline_blockquote = _t_md_blockquote if _newlines_ensure else None
            if _t_next_md in _tts_md_newlined_text_start:
                _newlines_ensure = 1
                _newline_blockquote = token_next.get("_md_bq") if token_next else None

            # needing a newline is now contingent on our last block...
            token_stack__post = cleanup_space_backwards(
                token_stack__post,
                newlines_ensure=_newlines_ensure,
                newline_blockquote=_newline_blockquote,
                dbg=True,
            )

        elif (
            _t_md in _tts_md_endblocks
        ):  # (tt_md_TokenEndBlockquote, tt_md_TokenEndBlockElement, )
            # if we're going block-to-block, skip to the next block
            if _t_next_md in _tts_md_endblocks:
                continue

            # is the next line newlines? if so, stop!
            if _t_next_md in _tts_md_newlines_all:
                continue

            _newlines_ensure = 2
            if _t_prev_md in _tts_md_newlined_text_end:
                _newlines_ensure = 1

            _newline_blockquote = _t_md_blockquote if _newlines_ensure else None
            token_stack__post = cleanup_space_backwards(
                token_stack__post,
                newlines_ensure=_newlines_ensure,
                newline_blockquote=_newline_blockquote,
            )
            continue

        elif _t_md in _tts_md_whitespace:
            if _t_next_md in _tts_md_endblocks:
                # if the next token is an endblock, ignore this token
                continue

            _last_sig = stack__last_token(token_stack__post)
            if _last_sig:
                _last_sig_md = _last_sig.get("_md_type") if _last_sig else None
                if _last_sig_md:
                    # optimize some whitespace here...
                    if _t_md in _tts_md_newlines_all:
                        if _last_sig_md in _tts_md_newlines_all:
                            _discarded = token_stack__post.pop()
                            _tok = _contextual_TokenNewlines(
                                newlines=2, blockquoted=None, codeblocked=None
                            )
                            token_stack__post.append(_tok)
                            continue
                        elif _last_sig_md in _tts_md_newlined_text_end:
                            if _t_next_md in _tts_md_startblocks:
                                # if the next token is an startblock, ignore this token; a cleanup will catch it
                                continue
                            elif _t_md == tt_md_TokenNewlines:
                                # replace 2 newlines with 1
                                _tok = _contextual_TokenNewlines(
                                    newlines=1, blockquoted=None, codeblocked=None
                                )
                                token_stack__post.append(_tok)
                                continue
                            elif _t_md in _tts_md_newlines_single:
                                # just ignore this newline
                                continue

        elif _t_md == tt_md_TokenStartBlockNative:
            # special case: native blocks MUST be rendered and have newline requirements
            _newlines_ensure = 2
            _newline_blockquote = _t_md_blockquote if _newlines_ensure else None
            token_stack__post = cleanup_space_backwards(
                token_stack__post,
                newlines_ensure=_newlines_ensure,
                newline_blockquote=_newline_blockquote,
            )

        elif _t_md == tt_md_TokenEndBlockNative:
            # this value gets set by our `code` handling
            if token.get("_md_code_compress"):
                continue

        elif _t_md == tt_md_TokenHR:
            _newlines_ensure = 1
            _newline_blockquote = _t_md_blockquote if _newlines_ensure else None
            token_stack__post = cleanup_space_backwards(
                token_stack__post,
                newlines_ensure=_newlines_ensure,
                newline_blockquote=_newline_blockquote,
            )

        elif _t_md in _tts_md_code:
            if _t_md == tt_md_TokenStartCode:
                if _render_code_as_block_backwards(
                    token_stack__post
                ) and _render_code_as_block_frontwards(token_stack, token_idx):
                    # token['type'] = 'Characters'
                    # token['data'] = '{{CODE}}'
                    _last_codeblock = "BLOCK"
                    _codeblocked = 1
                    # this value gets set by our `code` handling
                    if token_stack__post and token_stack__post[-1].get(
                        "_md_code_compress"
                    ):
                        _discarded_pre = token_stack__post.pop()
                    lt = token_stack__post[-1]
                    if lt.get("_md_type") in _tts_md_newlines_single:
                        token_apply_prefix(
                            lt, blockquote=_t_md_blockquote, codeblock=_codeblocked
                        )
                    elif lt.get("_md_type") == tt_md_TokenNewlines:
                        _discarded_lines = token_stack__post.pop()
                        tok = _contextual_TokenNewlines(
                            newlines=1, blockquoted=_t_md_blockquote, codeblocked=False
                        )
                        token_stack__post.append(tok)
                        tok = _contextual_TokenNewlines(
                            newlines=1,
                            blockquoted=_t_md_blockquote,
                            codeblocked=_codeblocked,
                        )
                        token_stack__post.append(tok)
                    else:
                        raise ValueError(
                            "DEBUG!!!! edge. this has never been triggered"
                        )
                else:
                    token["type"] = "Characters"
                    token["data"] = "`"  # INLINE CODE
                    _last_codeblock = "INLINE"
            elif _t_md == tt_md_TokenEndCode:
                if _last_codeblock == "BLOCK":
                    pass
                    # token['type'] = 'Characters'
                    # token['data'] = '{{/CODE}}'
                elif _last_codeblock == "INLINE":
                    token["type"] = "Characters"
                    token["data"] = "`"  # INLINE CODE
                _last_codeblock = None
                _codeblocked = None

        # add the token to the stack AS LONG AS it is not one that should be filtered out
        # only filter out the start/end block markers
        if _t_md not in _tts_md_filtered:

            if not _t_md:
                _last_sig = stack__last_token(token_stack__post)
                if _last_sig and (_last_sig.get("_md_type") == tt_md_TokenStartCode):
                    if token.get("type") == "SpaceCharacters":
                        if token.get("data") in ("\n", "\n\n"):
                            continue

            # if we have a prefix for this token
            if _t_md_blockquote or _codeblocked:
                token_apply_prefix(
                    token, blockquote=_t_md_blockquote, codeblock=_codeblocked
                )

            token_stack__post.append(token)

    token_stack = token_stack__post

    # step 4b
    # TODO: migrate this situation into the previous loop
    # TODO: probably handled by isolating this into a protected block
    token_stack__post = []
    for (token_idx, token) in enumerate(token_stack):
        _t_md = token.get("_md_type")
        if _t_md not in (tt_md_TokenHR,):
            token_stack__post.append(token)
        else:
            _bq = token.get("_md_bq")
            _cb = token.get("_md_cb")
            t1 = _contextual_TokenNewlines(newlines=1, blockquoted=_bq, codeblocked=_cb)
            token["data"] = TokenHR()[
                "data"
            ].strip()  # replace this with a raw TokenHR's data
            t3 = _contextual_TokenNewlines(newlines=1, blockquoted=_bq, codeblocked=_cb)
            token_stack__post.extend([t1, token, t3])

    token_stack = token_stack__post

    # !!!: STEP 5- last postprocess
    # a) strip off trailing spaces
    while True:
        _lt = stack__last_token(token_stack)
        if _lt:
            if _lt.get("type") == "SpaceCharacters":
                token_stack.pop()
            # elif _lt.get('_md_type') in _tts_md_whitespace:
            #    token_stack.pop()
            else:
                if _lt.get("data"):
                    _lt["data"] = _lt.get("data").rstrip("\n")
                break
        else:
            break
    # b) strip leading spaces
    while True:
        _ft = stack__first_token(token_stack)
        if _ft:
            if _ft.get("type") == "SpaceCharacters":
                token_stack.pop(0)
            else:
                if _ft.get("data"):
                    _ft["data"] = _ft.get("data").lstrip("\n")
                break
        else:
            break

    if __debug__:
        if DEBUG_STACKS:
            _stack__print(token_stack, "output")

    return token_stack


class MarkdownSerializer(HTMLSerializer):
    def serialize(self, domtree, encoding=None):
        """
        If the token starts with a newline, there may be prefixes.
        Our tokens are designed so prefixing only happens on the newline elements,
        so this should not normal affect text elements

        ``MarkdownSerializer`` unescapes the blockquote characters in markdown
        text from "&gt;" to ">", producing valid Markdown but invalid HTML.
        """
        for (idx, token) in enumerate(
            super(MarkdownSerializer, self).serialize(domtree, encoding)
        ):
            if token.startswith("\n") or (idx == 0):
                # html5lib encoded the leading '>' to '&gt'; we need to encode it back.
                # the most accurate way so far, is to split the token on a space char, and only transform the 0 element.
                # we may have a 'newlines=2' object, so try that.
                _token = token.split(" ")
                _token[0] = _token[0].replace("&gt;", ">")
                if len(_token) >= 2:
                    if _token[1].startswith("\n&gt;"):
                        _token[1] = _token[1].replace("&gt;", ">")
                token = " ".join(_token)
            yield token


class Transformer(object):
    """
    ``Transformer`` is basically a factory for creating configurable transformations

    The returned object has two methods:

    ``transform`` accepts text and returns text
    ``adapt`` accepts a html5lib tree and returns an adapted tree

    """

    _parser = None
    _walker = None
    _builder = None
    _serializer = None

    _a_as_tag = None
    _a_simple_links = None
    _parse_markdown_simplelink = None
    _img_as_tag = None
    _strip_comments = None
    _strip_scripts = None
    _reference_style_link = None
    _reference_style_img = None
    _div_as_block = None
    _character_italic = None
    _character_bold = None
    _character_italicbold = None
    _character_unordered_listitem = None

    def __init__(
        self,
        filters=None,
        a_as_tag=True,
        a_simple_links=True,
        parse_markdown_simplelink=True,
        img_as_tag=True,
        strip_comments=False,
        strip_scripts=True,
        character_italic=None,
        character_bold=None,
        character_italicbold=None,
        character_unordered_listitem=None,
        reference_style_link=False,
        reference_style_img=False,
        div_as_block=None,
        allowed_tags=None,
        allowed_tags_blocks=None,
        allowed_tags_attributes=None,
        serializer=None,
    ):
        """
        Initializes a ``Transformer``.

        This can be used as a Factory to centrally configure the markdown style.

        :arg list filters: list of html5lib filters to chain after converting to
        markdown format.

        :arg bool a_as_tag: see ``to_markdown``
        :arg bool a_simple_links: see ``to_markdown``
        :arg bool parse_markdown_simplelink: see ``to_markdown``
        :arg bool img_as_tag: see ``to_markdown``
        :arg bool strip_comments: see ``to_markdown``
        :arg bool strip_scripts: see ``to_markdown``
        :arg bool reference_style_link: see ``to_markdown``
        :arg bool reference_style_img: see ``to_markdown``
        :arg bool div_as_block: see ``to_markdown``
        :arg string character_italic: see ``to_markdown``
        :arg string character_bold: see ``to_markdown``
        :arg string character_italicbold: see ``to_markdown``
        :arg string character_unordered_listitem: see ``character_unordered_listitem```
        :arg list allowed_tags: see ``to_markdown``
        :arg list allowed_tags_blocks: see ``to_markdown``
        :arg dict allowed_tags_attributes: see ``to_markdown``

        :arg object serializer:  an instance of a ``html5lib.serializer.HTMLSerializer``
        object.  default is ``None``, which will create an instance of this
        package's ``MarkdownSerializer`` with some default values.
        ``MarkdownSerializer`` unescapes the blockquote characters in markdown
        text from "&gt;" to ">", producing valid Markdown but invalid HTML.
        """
        self.filters = filters or []

        self._a_as_tag = a_as_tag
        self._a_simple_links = a_simple_links
        self._parse_markdown_simplelink = parse_markdown_simplelink
        self._img_as_tag = img_as_tag
        self._reference_style_link = reference_style_link
        self._reference_style_img = reference_style_img
        self._div_as_block = div_as_block
        self._strip_comments = strip_comments
        self._strip_scripts = strip_scripts
        self._character_italic = character_italic
        self._character_bold = character_bold
        self._character_italicbold = character_italicbold
        self._character_unordered_listitem = character_unordered_listitem
        self.allowed_tags = allowed_tags
        self.allowed_tags_blocks = allowed_tags_blocks
        self.allowed_tags_attributes = allowed_tags_attributes

    
        self._builder = getTreeBuilder("etree")
        self._walker = getTreeWalker("etree")
        self._parser = HTMLParser(self._builder)
        if serializer is None:
            serializer = MarkdownSerializer(
                quote_attr_values="always",
                omit_optional_tags=False,
                escape_lt_in_attrs=True,
                # JV wants it to look like this
                use_trailing_solidus=True,
                space_before_trailing_solidus=True,
                quote_char="'",
                alphabetical_attributes=True,
                sanitize=False,
                # We want to leave entities as they are without escaping or
                # resolving or expanding
                resolve_entities=False,
            )
        self._serializer = serializer

    def transform(self, text):
        """
        Cleans text and returns sanitized result as unicode

        :arg str text: text to be cleaned

        :returns: sanitized text as unicode

        :raises TypeError: if ``text`` is not a text type

        """
        if not isinstance(text, six.string_types):
            message = "argument cannot be of '{name}' type, must be of text type".format(
                name=text.__class__.__name__
            )
            raise TypeError(message)

        if not text:
            return ""

        # bleach.utils.force_unicode
        if not isinstance(text, six.text_type):
            text = six.text_type(text, "utf-8", "strict")

        text = "\n".join(
            [i.rstrip() for i in text.split("\n")]
        )  # normalize trailing whitespace

        text = wrapped % text
        dom = self._parser.parseFragment(text)
        
        # reset the parser
        # TODO: is this needed? does `parseFragment` not reset first?
        self._parser.reset()
        
        # Apply any filters after the
        dom_markdown = to_markdown(
            self._walker(dom),
            a_as_tag=self._a_as_tag,
            a_simple_links=self._a_simple_links,
            parse_markdown_simplelink=self._parse_markdown_simplelink,
            img_as_tag=self._img_as_tag,
            strip_comments=self._strip_comments,
            strip_scripts=self._strip_scripts,
            reference_style_link=self._reference_style_link,
            reference_style_img=self._reference_style_img,
            div_as_block=self._div_as_block,
            allowed_tags=self.allowed_tags,
            allowed_tags_blocks=self.allowed_tags_blocks,
            allowed_tags_attributes=self.allowed_tags_attributes,
            character_italic=self._character_italic,
            character_bold=self._character_bold,
            character_italicbold=self._character_italicbold,
            character_unordered_listitem=self._character_unordered_listitem,
            is_fragment=True,
        )
        for filter_class in self.filters:
            dom_markdown = filter_class(source=dom_markdown)

        rendered = self._serializer.render(dom_markdown)
        
        return rendered

    def adapt(self, dom):
        """
        invokes the tree adapter to_markdown

        :arg str dom: text to be cleaned

        :returns: adapted tree text as unicode

        :raises TypeError: if ``text`` is not a text type

        """
        if not isinstance(dom, list):
            message = "argument cannot be of '{name}' type, must be of list type".format(
                name=dom.__class__.__name__
            )
            raise TypeError(message)

        if not dom:
            return []

        # Apply any filters after the
        dom_markdown = to_markdown(
            self._walker(dom),
            a_as_tag=self._a_as_tag,
            a_simple_links=self._a_simple_links,
            parse_markdown_simplelink=self._parse_markdown_simplelink,
            img_as_tag=self._img_as_tag,
            strip_comments=self._strip_comments,
            strip_scripts=self._strip_scripts,
            reference_style_link=self._reference_style_link,
            reference_style_img=self._reference_style_img,
            div_as_block=self._div_as_block,
            allowed_tags=self.allowed_tags,
            allowed_tags_blocks=self.allowed_tags_blocks,
            allowed_tags_attributes=self.allowed_tags_attributes,
            character_italic=self._character_italic,
            character_bold=self._character_bold,
            character_italicbold=self._character_italicbold,
            character_unordered_listitem=self._character_unordered_listitem,
            is_fragment=False,
        )
        return dom_markdown


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


__all__ = ("Transformer", "to_markdown")
