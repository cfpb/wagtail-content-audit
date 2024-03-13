from django.test import TestCase

from wagtail.models import Page

from wagtail_content_audit.tests.testapp.models import SearchTestPage
from wagtail_content_audit.utils import dotted_name, get_page_models_and_fields


class UtilsTestCase(TestCase):

    def test_dotted_name(self):
        name = dotted_name(SearchTestPage)
        self.assertEqual(
            name, "wagtail_content_audit.tests.testapp.models.SearchTestPage"
        )

    def test_get_page_models_and_fields(self):
        page_models_and_fields = list(get_page_models_and_fields())
        self.assertIn((Page, "title"), page_models_and_fields)
        self.assertIn(
            (SearchTestPage, "streamfield_with_block"), page_models_and_fields
        )

        pagetypes = ["testapp.SearchTestPage.streamfield_with_block"]
        page_models_and_fields = list(get_page_models_and_fields(pagetypes))
        self.assertNotIn((Page, "title"), page_models_and_fields)
        self.assertIn(
            (SearchTestPage, "streamfield_with_block"), page_models_and_fields
        )
