from django.db import models

from wagtail import blocks as blocks
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock
from wagtail.fields import StreamField
from wagtail.models import Page


class SearchTestPage(Page):
    streamfield_with_block = StreamField(
        [
            ("block", blocks.CharBlock()),
        ],
        use_json_field=True,
    )

    streamfield_with_list = StreamField(
        [
            ("list", blocks.ListBlock(blocks.CharBlock())),
        ],
        use_json_field=True,
    )

    streamfield_with_struct = StreamField(
        [
            (
                "struct",
                blocks.StructBlock(
                    [
                        ("givenname", blocks.CharBlock()),
                        ("surname", blocks.CharBlock()),
                    ]
                ),
            ),
        ],
        use_json_field=True,
    )

    streamfield_with_table = StreamField(
        [
            (
                "table",
                TypedTableBlock(
                    [
                        ("text", blocks.CharBlock()),
                        ("numeric", blocks.FloatBlock()),
                    ]
                ),
            )
        ],
        use_json_field=True,
    )

    text = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("streamfield_with_block"),
        FieldPanel("streamfield_with_list"),
        FieldPanel("streamfield_with_struct"),
        FieldPanel("streamfield_with_table"),
        FieldPanel("text"),
    ]
