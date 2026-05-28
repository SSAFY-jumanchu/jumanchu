from django.test import SimpleTestCase
from django.urls import reverse


class IndexPageTests(SimpleTestCase):
    def test_index_page_renders_stock_intro(self):
        response = self.client.get(reverse('pages-index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '주식도')
        self.assertContains(response, '투자 성향 기반 종목 매칭')
        self.assertContains(response, 'survey-questions')
