from django.test import TestCase
from tasks-runner.tasks import cleanup

# Create your tests here.
def test_cleanup():
    arg = "some_argument"
    result = cleanup(arg)
    expected_result = None
    assert result == expected_result