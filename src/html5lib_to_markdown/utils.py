# stdlib
import re


# ==============================================================================


RE_newlines_1p__full = re.compile(r"^\n+$")
RE_newlines_2p__full = re.compile(r"^\n\n+$")
RE_newlines_3p = re.compile(r"\n\n\n+")
RE_space_tab_only = re.compile(r"^[\ \t]+$")
RE_space_tab_p = re.compile(r"[\ \t]+")
RE_whitespace_meh = re.compile(r"\n[\ \t]+(?![\d\*])")
_MARKDOWN_PUNCTUATION = "\\!#*[]_`|~"
_MARKDOWN_TEXT_ESCAPES = str.maketrans(
    {character: "\\" + character for character in _MARKDOWN_PUNCTUATION}
)
_MARKDOWN_HTML_ESCAPES = str.maketrans(
    {character: f"&#{ord(character)};" for character in _MARKDOWN_PUNCTUATION}
    | {"&": "&amp;", "<": "&lt;", ">": "&gt;"}
)
_MARKDOWN_BLOCK_MARKER = re.compile(
    r"^([ \t]*(?:[0-9]{1,9})?)([.)]|(?<![0-9])[+=-])", re.MULTILINE
)


# ------------------------------------------------------------------------------


def escape_markdown_text(text: str, *, in_html: bool = False) -> str:
    """Escape Markdown punctuation in text extracted from ordinary HTML nodes."""
    if in_html:
        text = text.translate(_MARKDOWN_HTML_ESCAPES)
        return _MARKDOWN_BLOCK_MARKER.sub(
            lambda match: f"{match[1]}&#{ord(match[2])};", text
        )
    text = text.translate(_MARKDOWN_TEXT_ESCAPES)
    return _MARKDOWN_BLOCK_MARKER.sub(r"\1\\\2", text)


# escaping attributes
def safe_title(title: str) -> str:
    """Escape a title for Markdown's double-quoted title syntax."""
    return " ".join(title.splitlines()).replace("\\", "\\\\").replace('"', '\\"')


def is_token_newlines_1p(token):
    if token["type"] == "SpaceCharacters":
        if RE_newlines_1p__full.match(token["data"]):
            return True
    return False


def is_token_newlines_2p(token):
    if token["type"] == "SpaceCharacters":
        if RE_newlines_2p__full.match(token["data"]):
            return True
    return False


def is_list_upcoming(tokens):
    # ???: maybe iterate the raw tokens/idx and keep looking across multiple spaces?
    # tokens: token_next, token_next1
    if tokens[0]:
        if tokens[0].get("name") in ("ul", "ol"):
            return True
        if tokens[0]["type"] == "SpaceCharacters":
            if tokens[1]:
                if tokens[1].get("name") in ("ul", "ol"):
                    return True
    return False


def clean_token_attributes(token, name=None, allowed_attributes=None):
    if name is None:
        name = token.get("name")
    if "data" in token:
        if name in allowed_attributes:
            _data = token["data"]
            for _key in list(_data.keys()):
                # _key = `(namespace, name)`
                # usually this is `(None, name)`
                if _key[1] not in allowed_attributes[name]:
                    del _data[_key]
                else:
                    _data[_key] = _data[_key].strip()
        else:
            token["data"] = {}
    return token


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
