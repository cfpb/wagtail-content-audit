import itertools
import logging
import re
from dataclasses import dataclass

from django.core.exceptions import FieldError

from wagtail.blocks import BoundBlock, StreamValue, StructValue
from wagtail.blocks.list_block import ListValue
from wagtail.contrib.typed_table_block.blocks import TypedTable
from wagtail.models import Page, Site, get_page_models

from queryish import Queryish

from wagtail_content_audit.utils import dotted_name


logger = logging.getLogger(__name__)


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


def search_blocks(pattern, value, path=None):
    if path is None:
        path = []

    if isinstance(value, BoundBlock):
        local_path = path + [value.block]
        yield from search_blocks(pattern, value.value, path=local_path)

    elif isinstance(value, StructValue):
        local_path = path
        for child in value.bound_blocks.values():
            yield from search_blocks(pattern, child, path=path)

    elif isinstance(value, ListValue):
        for index, child in enumerate(value.bound_blocks):
            local_path = path + ["item", index]
            yield from search_blocks(pattern, child, path=local_path)

    elif isinstance(value, StreamValue):
        for index, child in enumerate(value):
            local_path = path + [index]
            yield from search_blocks(pattern, child, path=local_path)

    elif isinstance(value, TypedTable):
        for row_index, row in enumerate(value.rows):
            local_path = path + [row_index]
            for column_index, child in enumerate(row):
                local_path = local_path + [column_index]
                yield from search_blocks(pattern, child, path=local_path)

    else:
        matches = pattern.findall(str(value))
        if len(matches) > 0:
            yield path, matches


class PageSearchQuerySet(Queryish):
    def get_filtered_page_models(self):
        global_page_models = get_page_models()
        filters = [val for key, val in self.filters if key == "page_model"]
        filtered_page_models = [
            page_model
            for page_model in global_page_models
            if page_model in filters or page_model.__name__ in filters
        ]
        return filtered_page_models if len(filters) > 0 else global_page_models

    def get_filtered_field_names(self, page_model):
        all_fields = [field.name for field in page_model._meta.concrete_fields]
        filters = [val for key, val in self.filters if key == "field"]
        filtered_fields = [
            field_name for field_name in all_fields if field_name in filters
        ]
        return filtered_fields if len(filters) > 0 else all_fields

    def get_search_re(self):
        search_str = next(
            (val for key, val in self.filters if key == "search"), ""
        )
        search_re = re.compile(search_str)
        return search_re

    def prepare_pattern_for_json(self, pattern):
        return pattern.replace('"', r'\\"')

    def get_matches_for_page_field(self, page_model, field_name, page):
        search_re = self.get_search_re()
        field = page_model._meta.get_field(field_name)
        field_type = dotted_name(field.__class__)
        field_value = getattr(page, field_name)

        page_match = PageMatch(
            page_model=page_model,
            page=page,
            field_name=field_name,
            field_type=field_type,
            stream_field_path=[],
            block_type=None,
            result_path=[],
            matches=[],
        )

        if isinstance(field_value, StreamValue):
            # If this field is a StreamField, dive into it to get paths
            # and matches
            for streamfield_path, matches in search_blocks(
                search_re, field_value
            ):
                # Construct a specific path (with list indexes) and then a
                # general path that follow the conventions of Wagtail's
                # StreamField migration pathing.
                formatted_path = [
                    (
                        (p.name if hasattr(p, "name") else p)
                        if p is not None
                        else "item"
                    )
                    for p in streamfield_path
                ]
                page_match.block_type = dotted_name(
                    streamfield_path[-1].__class__
                )
                page_match.result_path = [str(p) for p in formatted_path]
                page_match.stream_field_path = [
                    p for p in formatted_path if not isinstance(p, int)
                ]
                page_match.matches = matches
                yield page_match

        else:
            matches = search_re.findall(str(field_value))
            page_match.matches = matches
            yield page_match

    def get_matches_for_page_model_field(self, page_model, field_name):
        search_re = self.get_search_re()

        # Get the default site
        site = Site.objects.get(is_default_site=True)

        # Search for live pages in the default site
        queryset = page_model.objects.live().in_site(site)

        # Try to do in-database regular expression-matching of the search
        # string.
        try:
            queryset = queryset.filter(
                **{
                    f"{field_name}__iregex": self.prepare_pattern_for_json(
                        search_re.pattern
                    )
                }
            )
        except FieldError:
            logger.info(
                f"Cannot search {dotted_name(page_model)}.{field_name}."
            )
            return

        queryset = queryset.exact_type(page_model)
        for page in queryset:
            yield from self.get_matches_for_page_field(
                page_model, field_name, page
            )

    def run_query(self):
        search_matches = []

        for page_model in self.get_filtered_page_models():
            for field_name in self.get_filtered_field_names(page_model):
                search_matches = itertools.chain(
                    search_matches,
                    self.get_matches_for_page_model_field(
                        page_model, field_name
                    ),
                )

        # Slice based on queryset slicing offset/limit
        return itertools.islice(
            search_matches,
            self.offset,
            self.offset + self.limit if self.limit else None,
            self.limit,
        )
