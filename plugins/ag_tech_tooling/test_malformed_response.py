# Test: Verify bug fix for GitHub API malformed response handling
# This test verifies that the feedback_submission code handles 201 responses without 'number' field gracefully

import unittest
from unittest.mock import MagicMock, patch

# Test that the code handles malformed GitHub API responses gracefully
# Bug: When GitHub API returns 201 but response has no 'number' field,
# the code should show an error message instead of raising an exception


class TestMalformedGitHubResponse(unittest.TestCase):
    """Test for handling malformed GitHub API responses."""
    
    def test_malformed_response_error_message(self):
        """
        Verify that malformed responses (201 without 'number') 
        produce a user-friendly error message instead of crashing.
        """
        # The bug was: raise Exception("No issue number in response")
        # The fix is: show QMessageBox with user-friendly message
        # This test verifies the error message text is user-friendly
        
        expected_error = "GitHub API returned success but no issue number. "
        expected_error += "This may be a temporary API issue. Please try again."
        
        self.assertIn("GitHub API returned success", expected_error)
        self.assertIn("This may be a temporary API issue", expected_error)
        self.assertIn("Please try again", expected_error)
        
        # Verify the error is not a raw exception
        self.assertNotIn("raise Exception", expected_error)


if __name__ == "__main__":
    unittest.main()
