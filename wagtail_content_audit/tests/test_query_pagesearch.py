import re

from django.test import TestCase

from wagtail_content_audit.query.pagesearch import (
    PageSearchQuerySet,
    search_blocks,
)
from wagtail_content_audit.tests.testapp.models import SearchTestPage


class PageSearchTestCase(TestCase):
    fixtures = ["wagtail_content_audit_testapp_fixture.json"]

    def setUp(self):
        self.test_page = SearchTestPage.objects.get(id=3)
        self.notest_page = SearchTestPage.objects.get(id=4)

    def test_search_blocks_boundblock(self):
        pattern = re.compile("Test")

        result = list(
            search_blocks(pattern, self.test_page.streamfield_with_block)
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0][0]), 2)
        self.assertEqual(result[0][1], ["Test"])

        notest_result = list(
            search_blocks(pattern, self.notest_page.streamfield_with_block)
        )
        self.assertEqual(len(notest_result), 0)

    def test_search_blocks_structvalue(self):
        pattern = re.compile("Test")

        result = list(
            search_blocks(pattern, self.test_page.streamfield_with_struct)
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0][0]), 3)
        self.assertEqual(result[0][1], ["Test"])

        notest_result = list(
            search_blocks(pattern, self.notest_page.streamfield_with_struct)
        )
        self.assertEqual(len(notest_result), 0)

    def test_search_blocks_listvalue(self):
        pattern = re.compile("Test")

        result = list(
            search_blocks(pattern, self.test_page.streamfield_with_list)
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0][0]), 5)
        self.assertEqual(result[0][1], ["Test"])

        notest_result = list(
            search_blocks(pattern, self.notest_page.streamfield_with_list)
        )
        self.assertEqual(len(notest_result), 0)

    def test_search_blocks_typedtable(self):
        pattern = re.compile("Test")

        result = list(
            search_blocks(pattern, self.test_page.streamfield_with_table)
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0][0]), 5)
        self.assertEqual(result[0][1], ["Test"])

        notest_result = list(
            search_blocks(pattern, self.notest_page.streamfield_with_table)
        )
        self.assertEqual(len(notest_result), 0)

    def test_pagesearchqueryset_get_filtered_page_models_no_filter(self):
        queryset = PageSearchQuerySet()
        page_models = queryset.get_filtered_page_models()
        self.assertEqual(len(page_models), 2)
        self.assertIn(SearchTestPage, page_models)

    def test_pagesearchqueryset_get_filtered_page_models_with_filter(self):
        queryset = PageSearchQuerySet().filter(page_model=SearchTestPage)
        page_models = queryset.get_filtered_page_models()
        self.assertEqual(len(page_models), 1)
        self.assertIn(SearchTestPage, page_models)

    def test_pagesearchqueryset_get_filtered_page_models_with_filter_str(self):
        queryset = PageSearchQuerySet().filter(page_model="SearchTestPage")
        page_models = queryset.get_filtered_page_models()
        self.assertEqual(len(page_models), 1)
        self.assertIn(SearchTestPage, page_models)

    def test_pagesearchqueryset_get_filtered_page_models_filter_dne(self):
        queryset = PageSearchQuerySet().filter(page_model="Foo")
        page_models = queryset.get_filtered_page_models()
        self.assertEqual(len(page_models), 0)

    def test_pagesearchqueryset_get_filtered_field_names_no_filter(self):
        queryset = PageSearchQuerySet()
        field_names = list(
            queryset.get_filtered_field_names(page_model=SearchTestPage)
        )
        self.assertTrue(len(field_names) > 6)

    def test_pagesearchqueryset_get_filtered_field_names_with_filter(self):
        queryset = PageSearchQuerySet().filter(field="streamfield_with_block")
        field_names = list(
            queryset.get_filtered_field_names(page_model=SearchTestPage)
        )
        self.assertEqual(len(field_names), 1)

    def test_pagesearchqueryset_get_filtered_field_names_filter_dne(self):
        queryset = PageSearchQuerySet().filter(field="nonexistent_field")
        field_names = list(
            queryset.get_filtered_field_names(page_model=SearchTestPage)
        )
        self.assertEqual(len(field_names), 0)

    def test_pagesearchqueryset_get_search_re(self):
        queryset = PageSearchQuerySet().filter(search="Test")
        search_re = queryset.get_search_re()
        self.assertEqual(search_re.pattern, "Test")

    def test_pagesearchqueryset_prepare_pattern_for_json(self):
        queryset = PageSearchQuerySet()
        json_pattern = queryset.prepare_pattern_for_json(
            'pattern with "quotes"'
        )
        self.assertEqual(json_pattern, 'pattern with \\\\"quotes\\\\"')

    def test_pagesearchqueryset_get_matches_for_page_field_streamfield(self):
        queryset = PageSearchQuerySet().filter(search="Test")
        match = next(
            queryset.get_matches_for_page_field(
                SearchTestPage, "streamfield_with_block", self.test_page
            )
        )
        self.assertEqual(len(match.stream_field_path), 1)
        self.assertEqual(len(match.result_path), 2)
        self.assertEqual(len(match.matches), 1)

    def test_pagesearchqueryset_get_matches_for_page_field_nonstreamfield(
        self,
    ):
        queryset = PageSearchQuerySet().filter(search="Test")
        match = next(
            queryset.get_matches_for_page_field(
                SearchTestPage, "text", self.test_page
            )
        )
        self.assertEqual(len(match.stream_field_path), 0)
        self.assertEqual(len(match.result_path), 0)
        self.assertEqual(len(match.matches), 1)

    def test_pagesearchqueryset_get_matches_for_page_model_field(self):
        queryset = PageSearchQuerySet().filter(search="Test")
        match = next(
            queryset.get_matches_for_page_model_field(
                SearchTestPage,
                "text",
            )
        )
        self.assertEqual(len(match.stream_field_path), 0)
        self.assertEqual(len(match.result_path), 0)
        self.assertEqual(len(match.matches), 1)

    def test_pagesearchqueryset_get_matches_for_page_model_field_noiregex(
        self,
    ):
        queryset = PageSearchQuerySet().filter(search="Test")
        with self.assertRaises(StopIteration), self.assertLogs(
            level="INFO"
        ) as logging_context:
            next(
                queryset.get_matches_for_page_model_field(
                    SearchTestPage,
                    "latest_revision",
                )
            )
        self.assertEqual(len(logging_context.output), 1)
        self.assertIn(
            (
                "Cannot search wagtail_content_audit.tests.testapp.models."
                "SearchTestPage.latest_revision."
            ),
            logging_context.output[0],
        )

    def test_pagesearchqueryset_run_query(self):
        queryset = PageSearchQuerySet().filter(search="Test")
        self.assertEqual(queryset.count(), 11)
