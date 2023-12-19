import os

from jinja2 import nodes
from jinja2.ext import Extension
from jinja2_simple_tags import ContainerTag, StandaloneTag

from ..confluence.api import parse_page_id, parse_page_title


# This extension is written from scratch because the ContainerTag expects
# a comma separator when there are multiple arguments to the tag while
# GitBook tags use a blank space.
class CodeTagExtension(Extension):
    """
    Ref:
    * https://docs.gitbook.com/content-editor/blocks/code-block

    We can simply ignore this tag and just extract its contents.
    """

    tags = {"code"}

    def __init__(self, environment):
        super(CodeTagExtension, self).__init__(environment)

    def parse(self, parser):
        # We need this for reporting errors
        lineno = next(parser.stream).lineno

        # Gather the arguments. We don't need to process them further.
        gathered = []
        while parser.stream.current.type != "block_end":
            gathered.append(next(parser.stream))

        body = parser.parse_statements(["name:endcode"], drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_render_code"),
            [],
            [],
            body,
        ).set_lineno(lineno)

    def _render_code(self, caller):
        return str(caller())


class EmbedTagExtension(StandaloneTag):
    """
    This extension converts Gitbook embed tags into external URLs.

    Ref:
    * https://docs.gitbook.com/content-editor/blocks/embed-a-url
    """

    safe_output = True
    tags = {"embed"}

    def render(self, url):
        return f"[External URL]({url})"


class HintTagExtension(ContainerTag):
    tags = {"hint"}

    def render(self, style, caller=None) -> str:
        """
        Ref:
        * https://docs.gitbook.com/content-editor/blocks/hint
        * https://github.com/hunyadi/md2conf/blob/master/sample/example.md#admonitions

        The Confluence plugin only supports info, note, tip and warning.
        """
        admonitions_map = {
            "info": "info",
            "success": "info",
            "warning": "warning",
            "danger": "warning",
        }
        converted_style = "note"  # Use "note" by default
        if style in admonitions_map:
            converted_style = admonitions_map[style]
        content = str(caller())
        return f'!!! {converted_style} ""\n\t' + content.strip().replace("\n", "<br/>")


class PageRefTagExtension(StandaloneTag):
    tags = {"pageref"}  # Gitbook tag without "-"

    def render(self, page) -> str:
        """
        Ref:
        * https://docs.gitbook.com/content-editor/blocks/page-link
        """
        current_file_path = self.context["file_path"]

        # Get the page_id of the referenced page
        page_path = os.path.join(os.path.dirname(current_file_path), page)
        text = ""
        with open(page_path, "r") as f:
            text = f.read()

        # Generate link
        page_id = parse_page_id(text)
        page_title = parse_page_title(text)
        additional_context = self.context["additional_context"]
        domain, path, space = (
            additional_context["confluence_domain"],
            additional_context["confluence_path"],
            additional_context["confluence_space"],
        )
        return f"[{page_title}](https://{domain}{path}spaces/{space}/pages/{page_id})"
