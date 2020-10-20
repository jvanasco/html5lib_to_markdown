from __future__ import print_function

__VERSION__ = "0.0.4"


from .transformer import Transformer


# ==============================================================================


def transform(text):
    """
    This is a utility function that creates a Transformer with some defaults
    and then transforms text with it.
    Most users will want to create their own Transformer and utilize that instead.
    """
    transformer = Transformer(
        a_as_tag=False,
        img_as_tag=False,
        strip_comments=False,
        reference_style_link=False,
        reference_style_img=False,
        div_as_block=True,
    )
    return transformer.transform(text)


# ==============================================================================


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        fname = sys.argv[1]
        with open(fname, "r") as fp:
            input = fp.read()
        print("=" * 80)
        print(transform(input))
        print("=" * 80)
