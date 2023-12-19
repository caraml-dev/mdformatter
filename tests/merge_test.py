import difflib

from mdformatter.merge import merge_markdowns


def test_merge_markdowns_identity():
    base = ""

    with open("sample/templates/dir/basic/candy.md") as f:
        text = f.read()
        base = text

    # Merge onto self - should return original file
    merged = merge_markdowns(base, base)

    if base != merged:
        print(_unidiff_output(base, merged))
    assert base == merged


def _unidiff_output(expected, actual):
    """
    Helper function. Returns a string containing the unified diff of two multiline strings.
    """
    expected = expected.splitlines(1)
    actual = actual.splitlines(1)

    diff = difflib.unified_diff(expected, actual)

    return "".join(diff)
