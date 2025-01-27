from django.test import TestCase
from app.tasks import retriever

class RetrieverTestCase(TestCase):
    def test_retriever(self):
        arg = "some_argument"
        result = retriever(arg)
        print(f"Retriever result: {result}")
        expected_result = None
        self.assertEqual(result, expected_result)