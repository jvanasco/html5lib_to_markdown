from __future__ import print_function
from __future__ import unicode_literals


# ==============================================================================


MARKDOWN_TAGS_CORE = [
    "div",  # not core, but we treat it as such
    "p",
    "b",
    "i",
    "em",
    "strong",
    # lists
    "ul",
    "ol",
    "li",
    # quotes
    "blockquote",
    # headers
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    # misc
    "code",
    "hr",
    "a",
    "img",
    "pre",
    "code",
]


MARKDOWN_TAGS_PASSTHROUGH = ["table", "tr", "td", "th", "thead", "tbody"]

MARKDOWN_TAGS_PASSTHROUGH_BLOCKS = ["table"]


MARKDOWN_TAGS_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "title", "alt", "height", "width"],
}


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


__all__ = (
    "MARKDOWN_TAGS_CORE",
    "MARKDOWN_TAGS_PASSTHROUGH",
    "MARKDOWN_TAGS_PASSTHROUGH_BLOCKS",
    "MARKDOWN_TAGS_ATTRIBUTES",
)
