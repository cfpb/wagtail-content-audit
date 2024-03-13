from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class BlockUsageCommandTestCase(TestCase):
    fixtures = ["wagtail_content_audit_testapp_fixture.json"]

    def test_usage(self):
        output = StringIO()
        call_command("block_usage", stdout=output)
        self.assertIn("streamfield_with_block,block", output.getvalue())
        self.assertIn("streamfield_with_list,list.item", output.getvalue())
        self.assertIn("streamfield_with_table,table.text", output.getvalue())

    def test_usage_with_page_type_and_field(self):
        output = StringIO()
        call_command(
            "block_usage",
            "-p",
            "testapp.SearchTestPage.streamfield_with_block",
            "-p",
            "testapp.SearchTestPage.streamfield_with_list",
            stdout=output,
        )
        self.assertIn("streamfield_with_block,block", output.getvalue())
        self.assertIn("streamfield_with_list,list.item", output.getvalue())
        self.assertNotIn(
            "streamfield_with_table,table.text", output.getvalue()
        )
