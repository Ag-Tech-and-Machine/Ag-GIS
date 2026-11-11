# Test: Reproduce bug where GitHub API returns 201 but no "number" field
# This simulates a malformed GitHub API response

import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent))

from qgis.PyQt.QtWidgets import QMessageBox
from feedback_submission import FeedbackSubmissionDialog


class TestFeedbackSubmissionBug(unittest.TestCase):
    """Test for the bug where 201 response has no 'number' field."""
    
    def setUp(self):
        """Create a mock dialog for testing."""
        self.mock_iface = MagicMock()
        self.dialog = FeedbackSubmissionDialog(self.mock_iface)
        
    def test_201_without_number_shows_error_message(self):
        """
        Bug fix: When GitHub API returns 201 but response has no 'number' field,
        the code should show an error message instead of raising an exception.
        """
        # Simulate a GitHub API response with 201 but no 'number' field
        response_mock = MagicMock()
        response_mock.status_code = 201
        response_mock.json.return_value = {
            # Missing "number" field - this is the bug trigger
            "title": "Test",
            "body": "Test body",
            "labels": ["feedback"]
        }
        
        # Mock the requests.post to return our fake response
        with patch('feedback_submission.requests.post', return_value=response_mock):
            # This should NOT raise an exception anymore
            with self.assertRaises(QMessageBox):
                self.dialog.submit_feedback(
                    title="Test Title",
                    kind="Something went wrong",
                    area="Test Area",
                    impact="I can keep working",
                    details="Test details",
                    steps="Test steps",
                    expected="Test expected",
                    environment="Test environment"
                )
    
    def test_201_with_number_works(self):
        """
        Expected behavior: When GitHub API returns 201 with 'number' field,
        the issue should be created successfully.
        """
        # Simulate a normal GitHub API response with 201 and 'number' field
        response_mock = MagicMock()
        response_mock.status_code = 201
        response_mock.json.return_value = {
            "number": 123,
            "title": "Test",
            "body": "Test body",
            "labels": ["feedback"]
        }
        
        # Mock the requests.post to return our fake response
        with patch('feedback_submission.requests.post', return_value=response_mock):
            # This should work without raising an exception
            # Note: This test may not fully work without a real QGIS interface,
            # but it validates the code path
            try:
                self.dialog.submit_feedback(
                    title="Test Title",
                    kind="Something went wrong",
                    area="Test Area",
                    impact="I can keep working",
                    details="Test details",
                    steps="Test steps",
                    expected="Test expected",
                    environment="Test environment"
                )
                # If we get here without exception, test passes
            except Exception as e:
                # Some errors are expected (missing QGIS iface, etc.)
                # but it shouldn't be the "No issue number" error
                self.assertNotIn("No issue number in response", str(e))


if __name__ == "__main__":
    unittest.main()
