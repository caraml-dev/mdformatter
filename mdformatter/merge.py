from collections import OrderedDict
from typing import Dict, List
import re


class MarkDownContent:
    def __init__(self, level=0) -> None:
        self.level = level  # Heading level
        self.lines = []  # Newline separated lines
        self.subsections = OrderedDict()  # string -> MarkDownContent

    def to_text(self, delimiter="\n") -> str:
        """
        Creates a string representation of the markdown content.
        Markdown lines and subsections are joined using the given delimiter.

        Parameters
        ----------
        delimiter: str, default "\n"
            The delimiter to use, to join the individual lines of the markdown.

        Returns
        -------
        String representation of the markdown contents
        """
        subsections_text = []
        for heading in self.subsections:
            subsections_text.append(
                heading + delimiter + self.subsections[heading].to_text()
            )

        content = delimiter.join(self.lines)
        if len(self.lines) > 0 and len(self.subsections) > 0:
            content += delimiter
        content += delimiter.join(subsections_text)

        return content

    def to_dict(self) -> Dict:
        """
        Returns a dictionary representation of the markdown content.
        Useful for debugging.
        """
        return {
            "level": self.level,
            "lines": self.lines,
            "subsections": {
                heading: self.subsections[heading].to_dict()
                for heading in self.subsections
            },
        }

    def has_lines(self) -> bool:
        """
        Returns True if the object has at least one line that is not empty.
        """
        return len([x for x in self.lines if x != ""]) > 0


def parse_markdown(text, delimiter="\n") -> MarkDownContent:
    """
    Parses the markdown into sections by their heading.

    Parameters
    ----------
    text: str
        The markdown text
    delimiter: str, default "\n"
        The delimiter to use, to join the individual lines of the markdown.

    Returns
    -------
    A recursive representation of headings and contents (MarkDownContent)
    """
    lines = text.split("\n")
    _, parsed_markdown = _parse_markdown_recursive(lines, 0, MarkDownContent())
    return parsed_markdown


def _parse_markdown_recursive(
    lines: List[str], index: int, markdown: MarkDownContent
) -> (int, MarkDownContent):
    while index < len(lines):
        line = lines[index]
        if line.startswith("#"):
            match = re.search("^(#+)\s.*", line)
            new_heading_level = len(match.group(1))
            if new_heading_level > markdown.level:
                new_index, subsection = _parse_markdown_recursive(
                    lines,
                    index + 1,
                    MarkDownContent(level=new_heading_level),
                )
                markdown.subsections[line] = subsection
                index = new_index
            else:
                # Same heading level or higher, need to unfold
                return index, markdown
        else:
            markdown.lines.append(line)
            index += 1
    # End of lines
    return index, markdown


def merge_markdowns(base, *args):
    """
    Returns the result of merging 2 or more markdown files, by their heading.

    Parameters
    ----------
    base: str
        The base markdown text
    *args:
        One or more override markdown text

    Returns
    -------
    str
        Merged markdown contents
    """

    if len(args) < 1:
        raise ValueError("Must provide at least one override markdown text")

    # Read base markdown
    merged_content = parse_markdown(base)

    # Merge overrides
    for override in args:
        override_content = parse_markdown(override)
        merged_content = _merge_markdowns_recursive(merged_content, override_content)

    return merged_content.to_text()


def _merge_markdowns_recursive(
    base: MarkDownContent, override: MarkDownContent
) -> MarkDownContent:
    if base.level != override.level:
        return base

    if override.has_lines():
        base.lines = override.lines

    for heading in base.subsections:
        if heading in override.subsections:
            base.subsections[heading] = _merge_markdowns_recursive(
                base.subsections[heading], override.subsections[heading]
            )

    # Copy excess sections from the overrides
    for heading in override.subsections:
        if heading not in base.subsections:
            base.subsections[heading] = override.subsections[heading]

    return base
