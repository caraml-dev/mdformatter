import argparse
import json
import logging
import os
import typing

from pathlib import Path

from .confluence.api import preprocess, publish
from .merge import merge_markdowns
from .substitute import OutputFormat, substitute_variables


def parse_args(parser):
    parser.add_argument(
        "templates_dir", help="Path to the Markdown templates root folder."
    )
    parser.add_argument(
        "overrides_dir", help="Path to the Markdown overrides root folder."
    )
    parser.add_argument(
        "results_dir",
        help="Path to the folder where the resulting markdowns should be stored.",
    )
    parser.add_argument(
        "values_file",
        help="Path to the values file to be applied to the variables in the Markdown templates.",
    )
    parser.add_argument(
        "output_format",
        choices=[OutputFormat.GITBOOK.name, OutputFormat.CONFLUENCE.name],
        default=OutputFormat.GITBOOK.name,
        help="Output format. One of {GITBOOK, CONFLUENCE}",
    )
    # Logging configurations
    parser.add_argument(
        "-l",
        "--loglevel",
        choices=[
            typing.cast(str, logging.getLevelName(level)).lower()
            for level in (
                logging.DEBUG,
                logging.INFO,
                logging.WARN,
                logging.ERROR,
                logging.CRITICAL,
            )
        ],
        default=logging.getLevelName(logging.INFO),
        help="Use this option to set the log verbosity.",
    )
    # Confluence configurations
    parser.add_argument("-d", "--domain", help="Confluence organization domain.")
    parser.add_argument("-p", "--path", help="Base path for Confluece wiki.")
    parser.add_argument("-u", "--username", help="Confluence user name.")
    parser.add_argument(
        "-a",
        "--apikey",
        help="Confluence API key. Refer to documentation how to obtain one.",
    )
    parser.add_argument(
        "-s",
        "--space",
        help="Confluence space key for pages to be published. If omitted, will default to user space.",
    )
    parser.add_argument(
        "-r",
        "--rootpage",
        help="Confluence root page title under which the docs should be published.",
    )
    return parser.parse_args()


parser = argparse.ArgumentParser()
args = parse_args(parser)

FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(
    format=FORMAT, level=getattr(logging, args.loglevel.upper(), logging.INFO)
)

if __name__ == "__main__":
    # Init variables
    templates_dir, overrides_dir, results_dir = (
        args.templates_dir,
        args.overrides_dir,
        args.results_dir,
    )
    values_file = args.values_file
    output_format = OutputFormat(OutputFormat[args.output_format].value)

    # Read values file
    values = {}
    with open(values_file) as f:
        values = json.load(f)

    # Merge markdowns
    logging.info("Merging markdowns ...")
    for root, _dirs, files in os.walk(templates_dir):
        for file in files:
            template_path = os.path.join(root, file)
            logging.debug(f"Processing {template_path}")

            file_contents = ""
            with open(template_path) as t:
                file_contents = t.read()

            # Merge the contents of the templates with the overrides
            override_path = overrides_dir / Path(template_path).relative_to(
                templates_dir
            )
            if os.path.exists(override_path):
                logging.info(f"Applying override at {override_path}")
                with open(override_path) as o:
                    file_contents = merge_markdowns(file_contents, o.read())

            # Output to the desired format
            result_path = results_dir / Path(template_path).relative_to(templates_dir)
            os.makedirs(os.path.dirname(result_path), exist_ok=True)
            with open(result_path, "w") as f:
                f.write(file_contents)

    if output_format == OutputFormat.CONFLUENCE:
        # Preprocess files
        preprocess(
            results_dir,
            confluence_domain=args.domain,
            confluence_path=args.path,
            confluence_space=args.space,
            confluence_username=args.username,
            confluence_apikey=args.apikey,
            confluence_rootpage=args.rootpage,
        )

    # Substitute variables
    logging.info("Substituting variables ...")
    substitute_variables(
        results_dir,
        values,
        output_format,
        additional_context={
            "confluence_domain": args.domain,
            "confluence_path": args.path,
            "confluence_space": args.space,
        },
    )

    if output_format == OutputFormat.CONFLUENCE:
        # Publish the processed files to Confluence
        publish(
            results_dir,
            confluence_domain=args.domain,
            confluence_path=args.path,
            confluence_space=args.space,
            confluence_username=args.username,
            confluence_apikey=args.apikey,
        )

    logging.info("Done.")
