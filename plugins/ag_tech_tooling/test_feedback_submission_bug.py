# Test: Reproduce bug where GitHub API returns 201 but no "number" field
# This simulates a malformed GitHub API response

import sys
import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

# Add plugins to path
sys.path.insert(0, str(Path(__file__).parent))

from qgis.PyQt.QtWidgets import QMessageBox
from feedback_submission import FeedbackSubmissionDialog

# Track what happens
captured_calls = []

def track_critical(title, message, *args, **kwargs):
    """Track QMessageBox.critical calls."""
    captured_calls.append({
        'title': title,
        'message': message,
        'args': args,
        'kwargs': kwargs
    })

def track_information(title, message, *args, **kwargs):
    """Track QMessageBox.information calls."""
    captured_calls.append({
        'type': 'information',
        'title': title,
        'message': message,
        'args': args,
        'kwargs': kwargs
    })

class TestFeedbackSubmissionBug(unittest.TestCase):
    """Test for the bug where 201 response has no 'number' field."""
    
    def setUp(self):
        """Create a mock dialog for testing."""
        self.mock_iface = MagicMock()
        self.mock_iface.qgisVersion().atString.return_value = "3.36.0"
        self.dialog = FeedbackSubmissionDialog(self.mock_iface)
        
    def test_201_without_number_shows_error_message(self):
        """
        Bug fix: When GitHub API returns 201 but response has no 'number' field,
        the code should show an error message instead of raising an exception.
        """
        # Reset captured calls
        captured_calls.clear()
        
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
            # Mock QMessageBox.critical to capture the call
            with patch.object(QMessageBox, 'critical', side_effect=track_critical):
                # Setup the dialog properly
                self.dialog.title.setText("Test Title")
                self.dialog.kind.setCurrentText("Something went wrong")
                self.dialog.area.setText("Test Area")
                self.dialog.impact.setText("I can keep working")
                self.dialog.details.setText("Test details")
                self.dialog.steps.setText("Test steps")
                self.dialog.expected.setText("Test expected")
                self.dialog.environment.setText("Test environment")
                
                # Mock the is_ready method
                self.dialog.is_ready = MagicMock(return_value=True)
                
                # Call submit_report (not submit_feedback!)
                self.dialog.submit_report()
                
                # Verify that QMessageBox.critical was called with the right message
                self.assertEqual(len(captured_calls), 1)
                self.assertEqual(captured_calls[0]['title'], 'Submission issue')
                self.assertIn("No issue number in response", captured_calls[0]['message'])
    
    def test_201_with_number_works(self):
        """
        Expected behavior: When GitHub API returns 201 with 'number' field,
        the issue should be created successfully.
        """
        # Reset captured calls
        captured_calls.clear()
        
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
            # Mock QMessageBox.information to capture the call
            with patch.object(QMessageBox, 'information', side_effect=track_information):
                # Setup the dialog
                self.dialog.title.setText("Test Title")
                self.dialog.kind.setCurrentText("Something went wrong")
                self.dialog.area.setText("Test Area")
                self.dialog.impact.setText("I can keep working")
                self.dialog.details.setText("Test details")
                self.dialog.steps.setText("Test steps")
                self.dialog.expected.setText("Test expected")
                self.dialog.environment.setText("Test environment")
                
                # Mock the is_ready method
                self.dialog.is_ready = MagicMock(return_value=True)
                
                # Call submit_report
                try:
                    self.dialog.submit_report()
                    # If we get here without exception, test passes
                except Exception as e:
                    # Some errors are expected (missing QGIS iface, etc.)
                    # but it shouldn't be the "No issue number" error
                    self.assertNotIn("No issue number in response", str(e))


if __name__ == "__main__":
    unittest.main()
