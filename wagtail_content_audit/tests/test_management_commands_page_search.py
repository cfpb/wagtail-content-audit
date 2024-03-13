from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class PageSearchCommandTestCase(TestCase):
    fixtures = ["wagtail_content_audit_testapp_fixture.json"]

    def test_search_streamfield(self):
        output = StringIO()
        call_command("page_search", "-s", "Test", stdout=output)
        self.assertIn(",struct.givenname", output.getvalue())
        self.assertIn(",0.struct.givenname", output.getvalue())

    def test_search_regular_field(self):
        output = StringIO()
        call_command("page_search", "-s", "text", stdout=output)
        self.assertIn(
            "text",
            output.getvalue(),
        )

    def test_search_with_page_type_and_field(self):
        output = StringIO()
        call_command(
            "page_search",
            "-s",
            "Test",
            "-p",
            "testapp.SearchTestPage.streamfield_with_block",
            "-p",
            "testapp.SearchTestPage.streamfield_with_list",
            stdout=output,
        )
        self.assertIn("0.block", output.getvalue())
        self.assertIn("0.list.item.0", output.getvalue())
        self.assertNotIn("0.struct.givenname", output.getvalue())
