import logging
import os
import re

from enum import Enum
from typing import Dict

from jinja2 import (
    BaseLoader,
    Environment,
    StrictUndefined,
)


class OutputFormat(Enum):
    GITBOOK = "gitbook"
    CONFLUENCE = "confluence"


def substitute_variables(
    markdowns_dir,
    input: Dict,
    output_format: OutputFormat,
    additional_context: Dict,
) -> None:
    for root, _dirs, files in os.walk(markdowns_dir):
        for file in files:
            file_path = os.path.join(root, file)
            logging.debug(f"Processing {file_path}")
            updated_contents = ""
            with open(file_path, "r") as f:
                file_contents = f.read()
                updated_contents = _substitute_variables(
                    file_path, file_contents, input, output_format, additional_context
                )
            with open(file_path, "w") as f:
                f.write(updated_contents)


def _substitute_variables(
    file_path: str,
    text: str,
    input: Dict,
    output_format: OutputFormat,
    additional_context: Dict,
) -> str:
    extensions = []

    if output_format == OutputFormat.GITBOOK:
        # Wrap special tags with a "raw" Jinja tag so that subsequent processing with Jinja will
        # retain the tag.
        text = re.sub(r"({\% [^%]+ \%})", "{% raw %}\g<0>{% endraw %}", text)
    elif output_format == OutputFormat.CONFLUENCE:
        from .gitbooktags.confluence import (
            CodeTagExtension,
            EmbedTagExtension,
            HintTagExtension,
            PageRefTagExtension,
        )

        extensions.extend(
            [
                CodeTagExtension,
                EmbedTagExtension,
                HintTagExtension,
                PageRefTagExtension,
            ]
        )
        # Remove hyphens from Nunjucks tags as Jinja cannot handle them
        text = re.sub(r"{\% ([a-z]*)-([a-z]*)", r"{% \1\2", text)

    # Substitute variables
    env = Environment(
        extensions=extensions,
        loader=BaseLoader,
        undefined=StrictUndefined,
    )
    tpl = env.from_string(text)
    return tpl.render(input, file_path=file_path, additional_context=additional_context)
