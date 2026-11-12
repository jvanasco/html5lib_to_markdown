"""Regression tests for the public HTML-to-Markdown conversion paths."""

from xml.etree.ElementTree import ElementTree

import pytest
from html5lib import parse
from html5lib import parseFragment

from html5lib_to_markdown import transform
from html5lib_to_markdown import Transformer
from html5lib_to_markdown.transformer import MarkdownSerializer


def test_links_and_images_share_stable_reference_numbers() -> None:
    html = (
        '<a href="/first" title="First">A</a> <img src="/second" alt="B"> '
        '<img src="/first" alt="C" title="Ignored"> <a href="/second">D</a>'
    )
    transformer = Transformer(
        a_as_tag=False,
        img_as_tag=False,
        reference_style_link=True,
        reference_style_img=True,
    )

    assert transformer.transform(html) == (
        '[A][1] ![B][2] ![C][1] [D][2]\n\n[1]: /first "First"\n[2]: /second'
    )
    assert transformer.transform('<img src="/third" alt="E">') == (
        "![E][1]\n\n[1]: /third"
    )


@pytest.mark.parametrize("reference_style", [False, True])
def test_missing_destinations_keep_visible_text(reference_style: bool) -> None:
    transformer = Transformer(
        a_as_tag=False,
        img_as_tag=False,
        reference_style_link=reference_style,
        reference_style_img=reference_style,
    )
    html = '<a><em>label</em></a> <img alt="fallback"> <img src="" alt="empty"><img>'
    assert transformer.transform(html) == "_label_ fallback empty"
    assert transformer.transform('<a href="">This page</a>') == "[This page]()"


@pytest.mark.parametrize(
    ("reference_style", "expected"),
    [
        (
            False,
            r'[\[label\]](/a\)b%20c "say \"hi\"") ![\[alt\]](/a\(b "a \"b\"")',
        ),
        (
            True,
            r"[\[label\]][1] ![\[alt\]][2]"
            "\n\n"
            r'[1]: /a\)b%20c "say \"hi\""'
            "\n"
            r'[2]: /a\(b "a \"b\""',
        ),
    ],
)
def test_generated_links_escape_labels_destinations_and_titles(
    reference_style: bool, expected: str
) -> None:
    html = (
        '<a href="/a)b c" title="say &quot;hi&quot;">[label]</a> '
        '<img src="/a(b" alt="[alt]" title="a &quot;b&quot;">'
    )
    transformer = Transformer(
        a_as_tag=False,
        img_as_tag=False,
        reference_style_link=reference_style,
        reference_style_img=reference_style,
    )
    assert transformer.transform(html) == expected


def test_relative_link_does_not_become_an_autolink() -> None:
    assert transform('<a href="/same">/same</a>') == "[/same](/same)"


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<p><b>Bold<p>Next", "**Bold**\n\n**Next**"),
        ("<https:>", ""),
        ("<code>standalone", "`standalone`"),
        ("<pre>first   \nsecond\t  \n</pre>", "<pre>first   \nsecond\t  \n</pre>"),
        (
            "<pre><code>first   \nsecond\t  </code></pre>",
            "    first   \n    second\t  ",
        ),
    ],
)
def test_public_transform_handles_malformed_and_preformatted_html(
    html: str, expected: str
) -> None:
    assert transform(html) == expected


def test_bare_http_url_can_be_rendered_as_an_html_anchor() -> None:
    transformer = Transformer(a_simple_links=False)
    assert transformer.transform("<https://example.com>") == (
        '<a href="https://example.com">https://example.com</a>'
    )


def test_transform_still_requires_text() -> None:
    assert transform("") == ""
    with pytest.raises(TypeError, match="text type"):
        transform(b"<p>Body</p>")  # type: ignore[arg-type]


def test_adapt_accepts_etree_documents_and_fragments() -> None:
    transformer = Transformer()
    serializer = MarkdownSerializer()
    document = parse("<p>Body</p>", treebuilder="etree")
    fragment = parseFragment("Prefix <em>body</em>", treebuilder="etree")

    assert serializer.render(transformer.adapt(document)) == "Body"
    assert serializer.render(transformer.adapt(ElementTree(document))) == "Body"
    assert serializer.render(transformer.adapt(fragment)) == "Prefix _body_"
    assert transformer.adapt(parseFragment("", treebuilder="etree")) == []


def test_adapt_rejects_invalid_tree_input() -> None:
    with pytest.raises(TypeError, match="etree"):
        Transformer().adapt(ElementTree())


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<hr>", "---"),
        ("<hr>after", "---\nafter"),
        ("before<hr>after", "before\n\n---\nafter"),
        ("<p>before</p><hr><p>after</p>", "before\n\n---\n\nafter"),
        ("<hr><hr>", "---\n\n---"),
        ("<blockquote><hr></blockquote><p>outside</p>", "> ---\n> \noutside"),
        ("<pre><code>before</code></pre><hr>", "    before\n\n---"),
        ("<h2>Title</h2><hr><h3>Next</h3>", "## Title\n\n---\n\n### Next"),
    ],
)
def test_horizontal_rule_spacing(html: str, expected: str) -> None:
    assert transform(html) == expected


def test_adapt_keeps_rule_line_breaks_as_separate_tokens() -> None:
    fragment = parseFragment("<blockquote><hr></blockquote><p>outside</p>")
    tokens = Transformer().adapt(fragment)

    assert [(token["type"], token["data"], token.get("_md_bq")) for token in tokens] == [
        ("Characters", "> ", 1),
        ("Characters", "---", 1),
        ("Characters", "\n> ", 1),
        ("SpaceCharacters", "\n", None),
        ("Characters", "outside", None),
    ]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("a`b", "``a`b``"),
        ("``", "``` `` ```"),
        ("&lt;x&gt; &amp;", "`<x> &`"),
        (" padded ", "`  padded  `"),
        ("a\nb", "`a b`"),
    ],
)
def test_inline_code_preserves_literal_content(code: str, expected: str) -> None:
    assert transform(f"<p>Run <code>{code}</code> now</p>") == f"Run {expected} now"


def test_inline_code_preserves_escaping_inside_retained_html() -> None:
    html = "<table><tr><td>Run <code>&lt;x&gt;</code> now</td></tr></table>"
    assert "<code>&lt;x&gt;</code>" in transform(html)


def test_literal_greater_than_is_distinct_from_blockquote_prefixes() -> None:
    assert transform("<p>&gt; literal</p>") == "&gt; literal"
    assert transform("<blockquote><p>&gt; literal</p></blockquote>") == "> &gt; literal"


@pytest.mark.parametrize(
    ("html", "character", "expected"),
    [
        ("<strong><em>x</em></strong>", "*", "***x***"),
        ("<i><b>x</b></i>", "_", "___x___"),
        ("<strong>one <em>two</em> three</strong>", "*", "**one _two_ three**"),
        ("a<strong><em>b</em></strong>c", "_", "a**_b_**c"),
        ("a<strong><em>b</em></strong>c", "*", "a***b***c"),
        ("<strong><em> x </em></strong>", "_", "**_ x _**"),
    ],
)
def test_combined_emphasis_option(html: str, character: str, expected: str) -> None:
    assert Transformer(character_italicbold=character).transform(html) == expected


def test_default_keeps_separate_emphasis_markers() -> None:
    assert transform("<strong><em>x</em></strong>") == "**_x_**"
    assert transform("<em><strong>x</strong></em>") == "_**x**_"
