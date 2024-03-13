from django.test import TestCase

from wagtail_content_audit.query.blockusage import (
    BlockUsageQuerySet,
    traverse_streamblock,
    traverse_streamvalue,
)
from wagtail_content_audit.tests.testapp.models import SearchTestPage


class BlockUsageTestCase(TestCase):
    fixtures = ["wagtail_content_audit_testapp_fixture.json"]

    def setUp(self):
        self.page_one = SearchTestPage.objects.get(id=3)
        self.page_two = SearchTestPage.objects.get(id=4)

    def test_traverse_streamblock_streamblock(self):
        streamfield = SearchTestPage._meta.get_field("streamfield_with_block")
        results = list(
            traverse_streamblock(
                SearchTestPage,
                next(iter(streamfield.stream_block.child_blocks.items()))[1],
            )
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].path, "block")

    def test_traverse_streamblock_listblock(self):
        streamfield = SearchTestPage._meta.get_field("streamfield_with_list")
        results = list(
            traverse_streamblock(
                SearchTestPage,
                next(iter(streamfield.stream_block.child_blocks.items()))[1],
            )
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].path, "list")
        self.assertEqual(results[1].path, "list.item")

    def test_traverse_streamblock_tableblock(self):
        streamfield = SearchTestPage._meta.get_field("streamfield_with_table")
        results = list(
            traverse_streamblock(
                SearchTestPage,
                next(iter(streamfield.stream_block.child_blocks.items()))[1],
            )
        )
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].path, "table")
        self.assertEqual(results[1].path, "table.text")
        self.assertEqual(results[2].path, "table.numeric")

    def test_traverse_streamvalue_boundblock(self):
        results = list(
            traverse_streamvalue(self.page_one.streamfield_with_block)
        )
        self.assertEqual(results, ["block"])

    def test_traverse_streamvalue_structvalue(self):
        results = traverse_streamvalue(self.page_one.streamfield_with_struct)
        self.assertEqual(
            list(results), ["struct", "struct.givenname", "struct.surname"]
        )

    def test_traverse_streamvalue_listvalue(self):
        results = traverse_streamvalue(self.page_one.streamfield_with_list)
        self.assertEqual(list(results), ["list", "list.item", "list.item"])

    def test_traverse_streamvalue_table(self):
        results = traverse_streamvalue(self.page_one.streamfield_with_table)
        self.assertEqual(
            list(results),
            [
                "table",
                "table.text",
                "table.numeric",
                "table.text",
                "table.numeric",
            ],
        )

    def test_blockusagequeryset_get_filtered_page_models_no_filter(self):
        queryset = BlockUsageQuerySet()
        page_models = queryset.get_filtered_page_models()
        self.assertEqual(len(page_models), 2)
        self.assertIn(SearchTestPage, page_models)

    def test_blockusagequeryset_get_filtered_page_models_with_filter(self):
        queryset = BlockUsageQuerySet().filter(page_model=SearchTestPage)
        page_models = queryset.get_filtered_page_models()
        self.assertEqual(len(page_models), 1)
        self.assertIn(SearchTestPage, page_models)

    def test_blockusagequeryset_get_filtered_page_models_with_filter_str(self):
        queryset = BlockUsageQuerySet().filter(page_model="SearchTestPage")
        page_models = queryset.get_filtered_page_models()
        self.assertEqual(len(page_models), 1)
        self.assertIn(SearchTestPage, page_models)

    def test_blockusagequeryset_get_filtered_page_models_filter_dne(self):
        queryset = BlockUsageQuerySet().filter(page_model="Foo")
        page_models = queryset.get_filtered_page_models()
        self.assertEqual(len(page_models), 0)

    def test_blockusagequeryset_get_filtered_streamfield_names_no_filter(self):
        queryset = BlockUsageQuerySet()
        field_names = list(
            queryset.get_filtered_streamfield_names(page_model=SearchTestPage)
        )
        self.assertEqual(len(field_names), 4)

    def test_blockusagequeryset_get_filtered_streamfield_names_with_filter(
        self,
    ):
        queryset = BlockUsageQuerySet().filter(field="streamfield_with_block")
        field_names = list(
            queryset.get_filtered_streamfield_names(page_model=SearchTestPage)
        )
        self.assertEqual(len(field_names), 1)

    def test_blockusagequeryset_get_filtered_streamfield_names_filter_dne(
        self,
    ):
        queryset = BlockUsageQuerySet().filter(field="nonexistent_field")
        field_names = list(
            queryset.get_filtered_streamfield_names(page_model=SearchTestPage)
        )
        self.assertEqual(len(field_names), 0)

    def test_blockusagequeryset_audit_blocks_for_page_model(self):
        queryset = BlockUsageQuerySet()
        results = queryset.audit_blocks_for_page_model(SearchTestPage)

        self.assertEqual(len(results), 4)
        self.assertIn("streamfield_with_block", results)
        self.assertIn("streamfield_with_list", results)
        self.assertIn("streamfield_with_table", results)
        self.assertIn("streamfield_with_struct", results)

        block = results["streamfield_with_block"]["block"]
        self.assertEqual(len(block.pages), 2)
        self.assertIn(self.page_one, block.pages)

    def test_blockusagequeryset_run_query(self):
        queryset = BlockUsageQuerySet()
        results = queryset
        self.assertEqual(len(results), 9)

        results = queryset[1:2]
        self.assertEqual(len(results), 1)
