from dataclasses import dataclass

from wagtail.blocks import (
    BoundBlock,
    ListBlock,
    StreamBlock,
    StreamValue,
    StructBlock,
    StructValue,
)
from wagtail.blocks.list_block import ListValue
from wagtail.contrib.typed_table_block.blocks import (
    TypedTable,
    TypedTableBlock,
)
from wagtail.models import Site, get_page_models

from queryish import Queryish

from wagtail_content_audit.utils import dotted_name


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


# Traverse a stream field and yield back each available block type
def traverse_streamblock(page_model, block, parent=None):
    """Walk model stream block objects to get initial AuditedBlocks"""
    block_name = block.name if block.name != "" else "item"
    audited_block = AuditedBlock(
        page_model=dotted_name(page_model),
        field=None,
        path=(parent + "." + block_name if parent is not None else block_name),
        block=dotted_name(block.__class__),
        pages=[],
    )

    yield audited_block

    # If this is a StreamBlock or StructBlock it'll have child blocks
    if isinstance(block, (StreamBlock, StructBlock, TypedTableBlock)):
        for child_block_field_name in block.child_blocks:
            yield from traverse_streamblock(
                page_model,
                block.child_blocks[child_block_field_name],
                parent=audited_block.path,
            )

    elif isinstance(block, ListBlock):
        yield from traverse_streamblock(
            page_model,
            block.child_block,
            parent=audited_block.path,
        )

    else:
        pass


# Traverse a stream field's value and yield back each block type in use
def traverse_streamvalue(value, parent=None):
    """Walk model stream value objects to get AuditedBlocks in-use"""

    # This is a block type
    if isinstance(value, BoundBlock):
        block_name = value.block.name if value.block.name != "" else "item"
        path = parent + "." + block_name if parent is not None else block_name
        yield path
        yield from traverse_streamvalue(value.value, parent=path)

    # This is a StructValue
    elif isinstance(value, StructValue):
        for child in value.bound_blocks.values():
            yield from traverse_streamvalue(child, parent=parent)

    elif isinstance(value, ListValue):
        for child in value.bound_blocks:
            yield from traverse_streamvalue(child, parent=parent)

    elif isinstance(value, TypedTable):
        for row_index, row in enumerate(value.rows):
            for column_index, child in enumerate(row):
                yield from traverse_streamvalue(child, parent=parent)

    # This is a sequence of blocks
    elif isinstance(value, StreamValue):
        for child in value:
            yield from traverse_streamvalue(child, parent=parent)


class BlockUsageQuerySet(Queryish):
    """Return a QuerySet-like object for querying block type usage"""

    def get_filtered_page_models(self):
        global_page_models = get_page_models()
        filters = [val for key, val in self.filters if key == "page_model"]
        filtered_page_models = [
            page_model
            for page_model in global_page_models
            if page_model in filters or page_model.__name__ in filters
        ]
        return filtered_page_models if len(filters) > 0 else global_page_models

    def get_filtered_streamfield_names(self, page_model):
        all_streamfields = page_model.get_streamfield_names()
        filters = [val for key, val in self.filters if key == "field"]
        filtered_fields = [
            field_name
            for field_name in all_streamfields
            if field_name in filters
        ]
        return filtered_fields if len(filters) > 0 else all_streamfields

    def audit_blocks_for_page_model(self, page_model):
        # Get the StreamFields on the page model
        streamfields = self.get_filtered_streamfield_names(page_model)

        # A dictionary to hold counts of each block on a page
        page_blocks = {}

        # First populate all available blocks
        for streamfield_name in streamfields:
            streamfield = page_model._meta.get_field(streamfield_name)
            page_blocks[streamfield_name] = {}

            # Traverse child blocks of this stream field (this avpathoids capturing
            # the containing stream block, so we can line-up with stream values
            # below)
            for child_block_name in streamfield.stream_block.child_blocks:
                for audited_block in traverse_streamblock(
                    page_model,
                    streamfield.stream_block.child_blocks[child_block_name],
                ):
                    audited_block.field = streamfield_name
                    page_blocks[streamfield_name][
                        audited_block.path
                    ] = audited_block

        # Get the default Wagtail site (this avoids the Trash)
        site = Site.objects.get(is_default_site=True)

        # Get a queryset for all pages of this type
        page_queryset = page_model.objects.exact_type(page_model)

        # Loop through the queryset, and traverse each streamfield
        for page in page_queryset:
            for streamfield_name in streamfields:
                streamfield_value = getattr(page, streamfield_name)
                streamfield_dict = page_blocks[streamfield_name]

                for block_path in traverse_streamvalue(streamfield_value):
                    # Get the AuditedBlock object for this path
                    audited_block = streamfield_dict[block_path]

                    audited_block.total_occurrences += 1

                    if page not in audited_block.pages:
                        audited_block.pages.append(page)

                        audited_block.pages_count += 1

                        if page.live:
                            audited_block.pages_live_count += 1

                        if page.is_descendant_of(site.root_page):
                            audited_block.pages_in_default_site_count += 1

        return page_blocks

    def run_query(self):
        audited_blocks = []

        for page_model in self.get_filtered_page_models():
            page_blocks = self.audit_blocks_for_page_model(page_model)

            # Flatten the dictionary of dictionaries of blocks to a list and
            # extend the audited block list
            audited_blocks.extend(
                block
                for streamfield, blocks in page_blocks.items()
                for block in blocks.values()
            )

        # self.ordering

        # Slice based on queryset slicing offset/limit
        return audited_blocks[
            self.offset : self.offset + self.limit if self.limit else None
        ]
