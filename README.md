# mdformatter

Templating and formatting of `.md` files and optionally, publishing to Confluence. The script expects the input `.md` files to be of the Gitbook format (i.e., it supports the special Gitbook Nunjucks tags). The output format can be one of GITBOOK or CONFLUENCE. If the latter is chosen, the files will also be published to the specified Confluence space.

## Usage

To learn the usage, run `python -m mdformatter --help`:

```
usage: __main__.py [-h] [-l {debug,info,warning,error,critical}] [-d DOMAIN] [-p PATH] [-u USERNAME] [-a APIKEY] [-s SPACE]
                   [-r ROOTPAGE]
                   templates_dir overrides_dir results_dir values_file {GITBOOK,CONFLUENCE}

positional arguments:
  templates_dir         Path to the Markdown templates root folder.
  overrides_dir         Path to the Markdown overrides root folder.
  results_dir           Path to the folder where the resulting markdowns should be stored.
  values_file           Path to the values file to be applied to the variables in the Markdown templates.
  {GITBOOK,CONFLUENCE}  Output format. One of {GITBOOK, CONFLUENCE}

options:
  -h, --help            show this help message and exit
  -l {debug,info,warning,error,critical}, --loglevel {debug,info,warning,error,critical}
                        Use this option to set the log verbosity.
  -d DOMAIN, --domain DOMAIN
                        Confluence organization domain.
  -p PATH, --path PATH  Base path for Confluece wiki.
  -u USERNAME, --username USERNAME
                        Confluence user name.
  -a APIKEY, --apikey APIKEY
                        Confluence API key. Refer to documentation how to obtain one.
  -s SPACE, --space SPACE
                        Confluence space key for pages to be published. If omitted, will default to user space.
  -r ROOTPAGE, --rootpage ROOTPAGE
                        Confluence root page title under which the docs should be published.
```

## Formatting

* **Merging**: The script merges markdown files in the specified `templates_dir` with similarly located / named files in the `overrides_dir`. Sections are identified by the headings based on which the merging is done as well (eg: to override the contents of a heading at level 2, it must be placed under the same level 1 heading in the override file; see: `sample/overrides/dir/basic/candy.md` and the corresponding result files in the `results_*` directories).
* **Template Substitution**: After this, the template variables (using Jinja2 templating language) will be substituted by values supplied in the `values_file`. Values MUST be provided for all variables, either as default values in the templates or in the `values_file`. Missing values will raise an exception. Eg:

```
jinja2.exceptions.UndefinedError: 'caramel_boiling_point' is undefined
```

### Gitbook Format

Example usage:

```sh
python -m mdformatter sample/templates sample/overrides sample/results_gitbook \
    sample/input.json GITBOOK
```

The formatted files will be saved to the provided `results_dir` (`sample/results_gitbook` in this case).

### Confluence Format

Example usage:

```sh
python -m mdformatter sample/templates sample/overrides sample/results_confluence \
    sample/input.json CONFLUENCE \
    --domain="example.atlassian.net" --path="/wiki/" --space="DOCSPACE" \
    --username="<username>" --apikey="<apikey>" \
    --rootpage="Dev Docs"
```

The merged files (i.e., at least one of the template markdown or override markdown must provide this value) are expected to have the following comments which capture the title of the Confluence page to be used for publishing and _optionally_, the parent Confluence page's title. If the `parent-page-title` is not provided, the value of the `--rootpage` argument will be used.
* `<!-- page-title: Confluence Page Title -->`
* `<!-- parent-page-title: Confluence Parent Page Title -->`

Missing `page-title` will raise an exception:

```
md2conf.converter.DocumentError: Markdown document has no Confluence page title associated with it
```

The merged files will first be saved to the provided `results_dir` (`sample/results_confluence` in this case). All missing Confluence pages will be created in the provided space according to the page title and parent page title; the created page's ID will be added to the merged file which will be used for publishing later: `<!-- confluence-page-id: 12345678 -->`.

Template substitution (as with the `GITBOOK` case) is done on the merged files. During this process, Gitbook specific tags will be converted to appropriate Confluence macros.

## Publishing to Confluence

When `CONFLUENCE` output format is used, the formatted files will also be published to the specified space, using the given API username and key.

## Limitations

1. So that the relative links (to images / pages) work consistenty, the `templates_dir`, `overrides_dir` and `results_dir` must all be under the same parent folder.
2. Only the following Gitbook tags are properly parsed and converted to Confluence compatible format: `hint`, `embed`, `page-ref`, `code`
3. When Confluence output format is used, the page-title / parent-page-title comments should be placed at the top of the file, to prevent the possibility of being merged into other sections.
4. Using URLs with a blank space character (`%20`) may interfere with the processing and substitution of Gitbook tags and is thus discouraged.

## Development

[Black](https://github.com/psf/black) is used to format the Python code:

```sh
black **/*.py
```

Tests are minimal, can be run with:

```sh
python -m pytest
```
