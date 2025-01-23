from django.test import TestCase
from app.tasks import cleanup

# Create your tests here.
def test_cleanup():
    result = cleanup()
    expected_result = None
    assert result == expected_result