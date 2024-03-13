import csv

from django.core.management.base import BaseCommand

from wagtail_content_audit.query import BlockUsageQuerySet
from wagtail_content_audit.utils import get_page_models_and_fields


class Command(BaseCommand):
    help = (
        "Search for a string or regular expression through page fields."
        "Pass a list in the form of app_name.page_type.field for each page "
        "type and field you want to report on. "
        "By default the report will include all page types and all text-based "
        "fields on the page."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-p",
            "--pagetype",
            action="append",
            help=(
                "Specify the page type(s) and field to check."
                "This should be given in the form app_name.page_type.field "
                "to include a page type in the given app with the given field."
                "For example, v1.BrowsePage.content."
            ),
        )

    def handle(self, *args, **options):
        pagetypes = options["pagetype"]

        audited_blocks_qs = BlockUsageQuerySet()

        if pagetypes is not None:
            for page_model, field_name in get_page_models_and_fields(
                pagetypes
            ):
                audited_blocks_qs = audited_blocks_qs.filter(
                    page_model=page_model, field=field_name
                )

        writer = csv.writer(self.stdout)
        writer.writerow(
            [
                "Page Type",
                "Field",
                "Path",
                "Block",
                "Occurrences",
                "Pages",
                "Live",
                "In Default Site",
            ]
        )
        for audited_block in audited_blocks_qs.all():
            writer.writerow(
                [
                    audited_block.page_model,
                    audited_block.field,
                    audited_block.path,
                    audited_block.block,
                    audited_block.total_occurrences,
                    audited_block.pages_count,
                    audited_block.pages_live_count,
                    audited_block.pages_in_default_site_count,
                ]
            )
