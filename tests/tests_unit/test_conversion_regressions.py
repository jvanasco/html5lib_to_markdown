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
