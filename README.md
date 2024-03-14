# wagtail-content-audit

Content audit utilities for Wagtail. Still a work in progress.

For Wagtail sites with deeply-nested blocks and a large amount of potentially old content, it can be helpful to inspect block usage and be able to search through the content as it exists in the database. This library is intended to help with these and other challenges of auditing the content in Wagtail.

- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
  - [Block usage](#block-usage)
    - [Block usage management command](#block-usage-management-command)
    - [Block usage QuerySet](#block-usage-queryset)
  - [Page search](#page-search)
    - [Page search management command](#page-search-management-command)
    - [Page search QuerySet](#page-search-queryset)
- [Getting help](#getting-help)
- [Getting involved](#getting-involved)
- [Licensing](#licensing)

## Dependencies

- Python 3.8+
- Django 3.2 (LTS)+
- Wagtail 5.2 (LTS)+

It should be compatible at all intermediate versions, as well.
If you find that it is not, please [file an issue](https://github.com/cfpb/wagtail-flags/issues/new).

## Installation

1. Install wagtail-content-audit:

```shell
pip install wagtail-content-audit
```

2. Add `wagtail_content_audit` as an installed app in your Django `settings.py`:

 ```python
 INSTALLED_APPS = (
     ...
     "wagtail_content_audit",
     ...
 )
```

## Usage

wagtail-content-audit provides two primary audit tools at present:

- Block usage auditing
- Page field searching

For both, it provides a `QuerySet`-like object using [queryish](https://github.com/wagtail/queryish) that returns instances of a `dataclass` with relevant result data.

### Block usage

Block usage is intended to audit deeply-nested [Wagtail Blocks](https://docs.wagtail.org/en/stable/reference/streamfield/blocks.html) to discover how much these blocks might be used, and wwithin which other blocks and fields that usage occurs.

#### Block usage management command

wagtail-content-audit provides a management command to run the block usage audit and output CSV results:

```shell
./manage.py block_usage
```

The resulting CSV can be redirected to a file:

```shell
./manage.py block_usage > block_usage_audit.csv
```

The command takes the following arguments:

`--pagetype PAGETYPE_AND_FIELD`, `-p PAGETYPE_AND_FIELD`

Limits the audit to the particular page type(s) and Wagtail StreamField as a dotted path. For example,

```
./manage.py block_usage --pagetype myapp.PageWithContent.content
```

Will output the blocks used in all `myapp.PageWithContent` pages' `content` field.


#### Block usage QuerySet

```
from wagtail_content_audit.query import BlockUsageQuerySet
```

The underlying queryish QuerySet can be used outside of the management management command as well. This QuerySet behaves like any [queryish](https://github.com/wagtail/queryish) QuerySet, with a limited set of available options.

It can be filtered for page types:

```
filtered_queryset = BlockUsageQuerySet().filter(page_model="myapp.PageWithContent")
```

It can be filtered for Wagtail StreamFields:

```
filtered_queryset = BlockUsageQuerySet().filter(field="content")
```

And these can be combined:

```
filtered_queryset = BlockUsageQuerySet().filter(page_model="myapp.PageWithContent", field="content")
```

The queryset can also be sliced:

```
sliced_queryset = BlockUsageQuerySet()[:5]
```

The resulting objects in the queryset are `wagtail_content_audit.query.AuditedBlock` objects with the following schema:

```python
@dataclass
class AuditedBlock:
    page_model: type
    field: str
    path: str
    block: type
    pages: list
    total_occurrences: int = 0
    pages_count: int = 0
    pages_live_count: int = 0
    pages_in_default_site_count: int = 0
```

### Page search

Page search is intended to enable searching for specific patterns (using regular expressions) in text content in all Wagtail Page model fields.

For StreamFields specifically, it returns explicit block paths within a StreamField (i.e., `0.list.item.1.richtext` for a result found in the second child list item in the  first child block in the field) as well as the general block path (i.e., `list.item.richtext`) so that the blocks can be targetted using [Wagtail StreamField migrations](https://docs.wagtail.org/en/stable/advanced_topics/streamfield_migrations.html).

#### Page search management command

wagtail-content-audit provides a management command to run the page search audit and output CSV results:

```shell
./manage.py page_search -s '[tT]est'
```

The resulting CSV can be redirected to a file:

```shell
./manage.py page_search -s '[tT]est' > page_search_test.csv
```

The command takes the following arguments:

`--pagetype PAGETYPE_AND_FIELD`, `-p PAGETYPE_AND_FIELD`

Limits the search to the particular page type(s) and model field as a dotted path. For example,

```
./manage.py page_search -s '[tT]est' --pagetype myapp.PageWithContent.content
```

Will only search within the `content` field of `myapp.PageWithContent` pages.


#### Page search QuerySet

```
from wagtail_content_audit.query import PageSearchQuerySet
```

The underlying queryish QuerySet can be used outside of the management management command as well. This QuerySet behaves like any [queryish](https://github.com/wagtail/queryish) QuerySet, with a limited set of available options.

It can be searched with any regular expression string:

```
search_queryset = PageSearchQuerySet().filter(search=r"[tT]est")
```

It can be filtered for page types:

```
filtered_queryset = PageSearchQuerySet().filter(search=r"[tT]est", page_model="myapp.PageWithContent")
```

It can be filtered for model fields:

```
filtered_queryset = PageSearchQuerySet().filter(search=r"[tT]est", field="content")
```

And these can be combined:

```
filtered_queryset = PageSearchQuerySet().filter(search=r"[tT]est", page_model="myapp.PageWithContent", field="content")
```

The queryset can also be sliced:

```
sliced_queryset = BlockUsageQuerySet()[:5]
```

The resulting objects in the queryset are `wagtail_content_audit.query.pagesearch.PageMatch` objects with the following schema:

```python
@dataclass
class PageMatch:
    page_model: type
    page: Page
    field_name: str
    field_type: str
    stream_field_path: list
    block_type: type
    result_path: list
    matches: list
```

## Getting help

Please add issues to the [issue tracker](https://github.com/cfpb/wagtail-flags/issues).

## Getting involved

General instructions on _how_ to contribute can be found in [CONTRIBUTING](CONTRIBUTING.md).

## Licensing
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)
3. [CFPB Source Code Policy](https://github.com/cfpb/source-code-policy/)
