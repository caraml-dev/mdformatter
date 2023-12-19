import json
import logging
import os
import sys
import requests

from .doctree import build_tree, Node

from md2conf.api import build_url, ConfluenceAPI, ConfluenceError, ConfluenceSession
from md2conf.application import Application
from md2conf.converter import ConfluenceDocumentOptions, DocumentError, extract_value


def preprocess(
    markdowns_dir,
    confluence_domain,
    confluence_path,
    confluence_space,
    confluence_username,
    confluence_apikey,
    confluence_rootpage,
):
    """
    Preprocess all the pages and create missing ones. The page id will be added to the
    documents for publishing later.
    """
    with ConfluenceAPI(
        domain=confluence_domain,
        base_path=confluence_path,
        space_key=confluence_space,
        user_name=confluence_username,
        api_key=confluence_apikey,
    ) as session:
        logging.info(f"Preprocessing files at {markdowns_dir}")

        # Build a tree of pages: id is the page title and parent_id is the parent page title.
        # Note: For a given Confluence space, the page titles are unique which allows us to
        # treat the page title like an id.
        nodes = [Node(id=confluence_rootpage, parent_id=None)]
        for root, _dirs, files in os.walk(markdowns_dir):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    file_contents = f.read()
                    page_title = parse_page_title(file_contents)
                    parent_page_title = parse_parent_page_title(file_contents)
                    nodes.append(
                        Node(
                            id=page_title,
                            parent_id=parent_page_title or confluence_rootpage,
                        )
                    )
        parsed_nodes = build_tree(nodes)

        # Create the missing pages
        page_id_map = {}  # map of page-title to Confluence page-id
        for node in parsed_nodes:
            parent_id = (
                page_id_map[node.parent_id] if node.parent_id in page_id_map else None
            )
            page_id = _get_or_create_page(session, node.id, parent_id)
            page_id_map[node.id] = page_id

        # Add the page id to the docs as a comment as well as the Table of Contents
        for root, _dirs, files in os.walk(markdowns_dir):
            for file in files:
                file_path = os.path.join(root, file)
                updated_contents = ""
                with open(file_path, "r") as f:
                    file_contents = f.read()
                    page_title = parse_page_title(file_contents)
                    updated_contents = _add_page_id(
                        file_contents, page_id_map[page_title]
                    )
                    updated_contents = _add_toc(updated_contents)
                with open(file_path, "w") as f:
                    f.write(updated_contents)


def publish(
    markdowns_dir,
    confluence_domain,
    confluence_path,
    confluence_space,
    confluence_username,
    confluence_apikey,
):
    """
    Publish the pages to Confluence
    """
    with ConfluenceAPI(
        domain=confluence_domain,
        base_path=confluence_path,
        space_key=confluence_space,
        user_name=confluence_username,
        api_key=confluence_apikey,
    ) as session:
        logging.info(f"Publishing files at {markdowns_dir}")
        try:
            Application(session, ConfluenceDocumentOptions()).synchronize(markdowns_dir)
        except requests.exceptions.HTTPError as err:
            logging.error(err)
            # Print details for a response with JSON body
            if err.response is not None:
                try:
                    logging.error(err.response.json())
                except requests.exceptions.JSONDecodeError:
                    pass
            sys.exit(1)


def parse_page_id(text: str) -> str:
    """
    Returns the page id from the given text.
    Page title is expected to be of the format, enclosed in comments:
    <!-- confluence-page-id: value -->
    """
    page_id, _ = extract_value(r"<!--\s+confluence-page-id:\s*(.+)\s+-->", text)
    if page_id is None:
        raise DocumentError(
            "Markdown document has no Confluence page id associated with it"
        )
    return page_id


def parse_page_title(text: str) -> str:
    """
    Returns the page title from the given text.
    Page title is expected to be of the format, enclosed in comments:
    <!-- page-title: value -->
    """
    page_title, _ = extract_value(r"<!--\s+page-title:\s*(.+)\s+-->", text)
    if page_title is None:
        raise DocumentError(
            "Markdown document has no Confluence page title associated with it"
        )
    return page_title


def parse_parent_page_title(text: str) -> str:
    """
    Returns the parent page title from the given text.
    Parent page title is expected to be of the format, enclosed in comments:
    <!-- parent-page-title: value -->
    """
    parent_page_title, _ = extract_value(
        r"<!--\s+parent-page-title:\s*(.+)\s+-->", text
    )
    return parent_page_title


def _add_page_id(text: str, page_id: str) -> str:
    return f"<!-- confluence-page-id: {page_id} -->\n" + text


def _add_toc(text: str) -> str:
    return "[TOC]\n" + text


def _get_or_create_page(
    session: ConfluenceSession, page_title: str, parent_page_id: str
) -> str:
    """
    Finds a page with the given title and returns its id.
    If such a page cannot be found, a new one will be created under the given parent page id.

    Parameters
    ----------
    session: ConfluenceSession
        The active Confluence session
    page_title: str
        The title of the page
    parent_page_id: str
        The id of the parent page

    Returns
    -------
    Page id of the given page under the given parent page.
    """
    try:
        return session.get_page_id_by_title(page_title)
    except ConfluenceError:
        # Page doesn't exist, create it. Ref:
        # https://developer.atlassian.com/server/confluence/confluence-rest-api-examples/#create-a-new-page-as-a-child-of-another-page
        data = {
            "type": "page",
            "title": page_title,
            "space": {"key": session.space_key},
            "ancestors": [{"id": parent_page_id}],
            "body": {"storage": {"value": "", "representation": "storage"}},
        }
        url = build_url(f"https://{session.domain}{session.base_path}rest/api/content")
        response = session.session.post(
            url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        # Get the page again, it should succeed.
        return session.get_page_id_by_title(page_title)
