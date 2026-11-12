from .transformer import Transformer

# ==============================================================================

__VERSION__ = "1.0.0"

# ------------------------------------------------------------------------------


def transform(text: str, *, escape_text: bool = True) -> str:
    """Convert HTML to Markdown, escaping literal text by default."""
    transformer = Transformer(
        a_as_tag=False,
        img_as_tag=False,
        strip_comments=False,
        reference_style_link=False,
        reference_style_img=False,
        div_as_block=True,
        escape_text=escape_text,
    )
    return transformer.transform(text)


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        fname = sys.argv[1]
        with open(fname, "r") as fp:
            input = fp.read()
        print("=" * 80)
        print(transform(input))
        print("=" * 80)
