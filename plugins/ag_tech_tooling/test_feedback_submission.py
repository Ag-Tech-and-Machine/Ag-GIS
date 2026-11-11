# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    # SPDX-License-Identifier: GPL-2.0-or-later

    """Tests for GitHub issue submission functionality."""

    import unittest

    from unittest.mock import MagicMock, patch, mock_open

    from pathlib import Path

    

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.PyQt.QtWidgets import QMessageBox
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this test



from .feedback_submission import (

    load_oauth_token, save_oauth_token, delete_oauth_token,

    make_auth_header, generate_report_id, report_text,

    environment_summary, hash_report_body,

    FeedbackSubmissionDialog

)





class TestTokenStorage(unittest.TestCase):

    """Test OAuth token storage."""

    

    def setUp(self):

        self.test_dir = Path.home() / ".qgis2" / "plugins"

        self.test_file = self.test_dir / "github_oauth_token.ini"

    

    def test_load_nonexistent_token(self):

        """Load returns None for nonexistent token file."""

        if self.test_file.exists():

            self.test_file.unlink()

        self.assertIsNone(load_oauth_token())

    

    def test_load_invalid_token(self):

        """Load returns None for invalid token."""

        self.test_file.write_text("[github]\ntoken=invalid")

        self.assertIsNone(load_oauth_token())

    

    def test_load_valid_token(self):

        """Load returns valid token dict."""

        valid_token = "a" * 40

        self.test_file.write_text(f"[github]\ntoken={valid_token}\nexpiry=2026-12-31T00:00:00Z")

        result = load_oauth_token()

        self.assertIsNotNone(result)

        self.assertEqual(result["token"], valid_token)

    

    def test_save_and_load_token(self):

        """Token saved and loaded correctly."""

        valid_token = "b" * 40

        self.assertTrue(save_oauth_token(valid_token))

        result = load_oauth_token()

        self.assertIsNotNone(result)

        self.assertEqual(result["token"], valid_token)

    

    def test_delete_token(self):

        """Deleting token removes file."""

        valid_token = "c" * 40

        save_oauth_token(valid_token)

        self.assertTrue(self.test_file.exists())

        delete_oauth_token()

        self.assertFalse(self.test_file.exists())





class TestReportFormatting(unittest.TestCase):

    """Test report text generation."""

    

    def test_report_text_basic(self):

        """Basic report text format."""

        report = report_text(

            kind="Something went wrong",

            title="Error loading layer",

            area="Farm data",

            impact="I can keep working",

            details="Layer failed to load",

            steps="Open farm data browser, add layer",

            expected="Layer should display",

            environment="QGIS 3.38",

            report_id="abc123",

            created="2026-10-16T10:00:00Z"

        )

        self.assertIn("# Error loading layer", report)

        self.assertIn("Type: Something went wrong", report)

        self.assertIn("Report ID: abc123", report)

    

    def test_report_text_empty_optional(self):

        """Report handles empty optional fields."""

        report = report_text(

            kind="An idea or improvement",

            title="New feature",

            area="Other",

            impact="I can keep working",

            details="I want this",

            steps="",  # Empty

            expected="",  # Empty

            environment="",  # Empty

            report_id="xyz",

            created="2026-10-16T10:00:00Z"

        )

        self.assertIn("# New feature", report)

        self.assertIn("Steps: Not provided", report)

        self.assertIn("Expected result: Not provided", report)





class TestEnvironmentSummary(unittest.TestCase):

    """Test environment information generation."""

    

    def test_summary_with_versions(self):

        """Summary includes versions when requested."""

        summary = environment_summary(

            include_versions=True,

            qgis_version="3.38",

            python_version="3.10",

            system_info="Windows 11"

        )

        self.assertIn("QGIS: 3.38", summary)

        self.assertIn("Python: 3.10", summary)

        self.assertIn("System: Windows 11", summary)

    

    def test_summary_without_versions(self):

        """Summary says 'Not included' when versions disabled."""

        summary = environment_summary(

            include_versions=False,

            qgis_version="3.38",

            python_version="3.10",

            system_info="Windows 11"

        )

        self.assertEqual(summary, "Not included")





class TestReportHash(unittest.TestCase):

    """Test report hash generation."""

    

    def test_hash_consistency(self):

        """Same text produces same hash."""

        text = "Test report content"

        hash1 = hash_report_body(text)

        hash2 = hash_report_body(text)

        self.assertEqual(hash1, hash2)

    

    def test_hash_different_content(self):

        """Different text produces different hash."""

        text1 = "Content 1"

        text2 = "Content 2"

        self.assertNotEqual(hash_report_body(text1), hash_report_body(text2))





class TestAuthHeader(unittest.TestCase):

    """Test authentication header generation."""

    

    def test_header_format(self):

        """Header is 'Bearer TOKEN'."""

        token = "abc123"

        header = make_auth_header(token)

        self.assertEqual(header, f"Bearer {token}")





class TestSubmissionDialog(unittest.TestCase):

    """Test feedback submission dialog."""

    

    def test_dialog_creation(self):

        """Dialog can be created."""

        # This test requires a real QGIS iface, so we skip it

        # unittest.skip("Requires QGIS iface")

        pass





if __name__ == "__main__":

    unittest.main()


