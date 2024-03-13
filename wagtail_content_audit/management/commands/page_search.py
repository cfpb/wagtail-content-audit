import csv

from django.core.management.base import BaseCommand

from wagtail_content_audit.query import PageSearchQuerySet
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
        parser.add_argument(
            "-s",
            "--search",
            required=True,
            help=(
                "The search string to match. This can be a regular expression."
            ),
        )

    def handle(self, *args, **options):
        search_string = options["search"]
        pagetypes = options["pagetype"]

        search_qs = PageSearchQuerySet().filter(search=search_string)
        if pagetypes is not None:
            for page_model, field_name in get_page_models_and_fields(
                pagetypes
            ):
                search_qs = search_qs.filter(
                    page_model=page_model, field=field_name
                )

        writer = csv.writer(self.stdout)
        writer.writerow(
            (
                "Page ID",
                "Page Type",
                "Page Title",
                "Page URL",
                "Field",
                "Field Type",
                "Stream Field Path",
                "Block Type",
                "Result Path",
                "Stream Field Matches",
            )
        )
        for result in search_qs.all():
            writer.writerow(
                (
                    result.page.id,
                    result.page_model.__name__,
                    result.page.title,
                    result.page.url,
                    result.field_name,
                    result.field_type,
                    ".".join(result.stream_field_path),
                    result.block_type,
                    ".".join(result.result_path),
                    *result.matches,
                )
            )
