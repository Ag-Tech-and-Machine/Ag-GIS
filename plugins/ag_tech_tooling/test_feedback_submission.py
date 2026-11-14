# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests for GitHub issue submission functionality."""
import unittest
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

# Import from conftest
import sys
sys.path.insert(0, str(Path(__file__).parent))
from conftest import QGIS_AVAILABLE

# Conditionally import from feedback_submission
if QGIS_AVAILABLE:
    from .feedback_submission import (
        load_oauth_token, save_oauth_token, delete_oauth_token,
        make_auth_header, generate_report_id, report_text,
        environment_summary, hash_report_body,
        FeedbackSubmissionDialog
    )
else:
    # When QGIS is not available, we can only test non-QGIS functions
    from .feedback_submission import (
        load_oauth_token, save_oauth_token, delete_oauth_token,
        make_auth_header, generate_report_id, report_text,
        environment_summary, hash_report_body
    )
    # FeedbackSubmissionDialog not available without QGIS


class TestTokenStorage(unittest.TestCase):
    """Test OAuth token storage."""
    
    def setUp(self):
        # Import the module to get TOKEN_FILE and PLUGIN_DIR
        from . import feedback_submission as fs
        self.module = fs
        # Use a temporary directory for testing
        self.test_dir = Path(tempfile.gettempdir()) / f"ag_gis_token_test_{self.id()}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        # Override both PLUGIN_DIR and TOKEN_FILE for testing
        self._original_plugin_dir = fs.PLUGIN_DIR
        self._original_token_file = fs.TOKEN_FILE
        self.test_plugin_dir = self.test_dir / "ag_tech_tooling"
        self.test_plugin_dir.mkdir(parents=True, exist_ok=True)
        self.test_token_file = self.test_dir / "github_oauth_token.ini"
        # Set the module's paths
        fs.PLUGIN_DIR = self.test_plugin_dir
        fs.TOKEN_FILE = self.test_token_file
        
    def tearDown(self):
        # Clean up
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)
        # Restore original
        self.module.PLUGIN_DIR = self._original_plugin_dir
        self.module.TOKEN_FILE = self._original_token_file

    def test_load_nonexistent_token(self):
        """Load returns None for nonexistent token file."""
        self.assertIsNone(load_oauth_token())

    def test_load_invalid_token(self):
        """Load returns None for invalid token."""
        self.module.TOKEN_FILE = self.test_token_file
        self.test_token_file.write_text("[github]\ntoken=invalid")
        self.assertIsNone(load_oauth_token())

    def test_load_valid_token(self):
        """Load returns valid token dict."""
        valid_token = "a" * 40
        self.module.TOKEN_FILE = self.test_token_file
        self.test_token_file.write_text(f"[github]\ntoken={valid_token}\nexpiry=2026-12-31T00:00:00Z")
        result = load_oauth_token()
        self.assertIsNotNone(result)
        self.assertEqual(result["token"], valid_token)

    def test_save_and_load_token(self):
        """Token saved and loaded correctly."""
        valid_token = "b" * 40
        self.module.TOKEN_FILE = self.test_token_file
        self.assertTrue(save_oauth_token(valid_token))
        result = load_oauth_token()
        self.assertIsNotNone(result)
        self.assertEqual(result["token"], valid_token)

    def test_delete_token(self):
        """Deleting token removes file."""
        valid_token = "c" * 40
        self.module.TOKEN_FILE = self.test_token_file
        save_oauth_token(valid_token)
        self.assertTrue(self.test_token_file.exists())
        delete_oauth_token()
        self.assertFalse(self.test_token_file.exists())


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
        self.assertIn("## How to see it", report)
        self.assertIn("## Expected result", report)


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


if __name__ == "__main__":
    unittest.main()
