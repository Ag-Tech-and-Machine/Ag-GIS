# SPDX-License-Identifier: GPL-2.0-or-later
"""Direct GitHub issue submission using OAuth token persistence.

This module allows users to submit issues without logging into GitHub,
by storing OAuth tokens in the plugin's settings directory.
"""
import configparser
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import uuid
from typing import Optional, Tuple

from qgis.core import Qgis
from qgis.PyQt.QtCore import QUrl, Qt, QIODevice
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (QApplication, QDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget)

# GitHub API settings - these must match the GitHub App configuration
GITHUB_API_BASE = "https://api.github.com"
AG_GIS_FEEDBACK_REPO = "JamRov/Ag-GIS-Feedback"
ISSUES_URL = f"https://github.com/{AG_GIS_FEEDBACK_REPO}/issues"
SUPPORT_EMAIL = "[user identity]"

# Template mappings
KINDS = {
    "Something went wrong": "bug_report.yml",
    "An idea or improvement": "suggestion.yml",
    "I need help": "help.yml"
}

# Token storage paths
PLUGIN_DIR = Path.home() / ".qgis2" / "plugins" / "ag_tech_tooling"
TOKEN_FILE = PLUGIN_DIR / "github_oauth_token.ini"


def ensure_plugin_dir():
    """Create plugin settings directory if it doesn't exist."""
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)


def load_oauth_token() -> Optional[dict]:
    """Load stored OAuth token from config file."""
    ensure_plugin_dir()
    if not TOKEN_FILE.exists():
        return None
    
    try:
        config = configparser.ConfigParser()
        config.read(TOKEN_FILE, encoding="utf-8")
        if "github" not in config or "token" not in config["github"]:
            return None
        
        token = config["github"]["token"]
        expiry = config.get("github", "expiry", fallback="")
        
        # Parse expiry timestamp
        if expiry:
            try:
                expiry_time = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                if expiry_time < datetime.now(timezone.utc):
                    return None
            except ValueError:
                return None
        
        # Validate token format (should be 40 hex chars for OAuth token)
        if len(token) != 40 or not all(c in "0123456789abcdefABCDEF" for c in token):
            return None
        
        return {"token": token, "expiry": expiry}
    except Exception:
        return None


def save_oauth_token(token: str, expiry: str = "") -> bool:
    """Save OAuth token to config file."""
    ensure_plugin_dir()
    
    try:
        config = configparser.ConfigParser()
        config["github"] = {
            "token": token,
            "expiry": expiry or ""
        }
        TOKEN_FILE.write_text(config.read_string(config["github"]), encoding="utf-8")
        return True
    except Exception:
        return False


def delete_oauth_token():
    """Delete stored OAuth token."""
    ensure_plugin_dir()
    TOKEN_FILE.unlink(missing_ok=True)


def make_auth_header(token: str) -> str:
    """Create GitHub API authentication header."""
    return f"Bearer {token}"


def generate_report_id() -> str:
    """Generate a unique report ID."""
    return str(uuid.uuid4())


def report_text(kind: str, title: str, area: str, impact: str,
                details: str, steps: str, expected: str, environment: str,
                report_id: str, created: str) -> str:
    """Format report text for GitHub."""
    title_clean = " ".join(title.splitlines()).strip() or "Untitled feedback"
    return (f"# {title_clean}\n\n"
            f"Type: {kind}\n"
            f"Area: {area}\n"
            f"Impact: {impact}\n\n"
            f"## What happened or would help\n{details.strip()}\n\n"
            f"## How to see it\n{steps.strip() or 'Not provided'}\n\n"
            f"## Expected result\n{expected.strip() or 'Not provided'}\n\n"
            f"## App versions\n{environment or 'Not included'}\n\n"
            f"Report ID: {report_id}\n"
            f"Created (UTC): {created}\n")


def environment_summary(include_versions: bool, qgis_version: str,
                        python_version: str, system_info: str) -> str:
    """Generate environment information string."""
    if not include_versions:
        return "Not included"
    
    return (f"Ag-GIS: {qgis_version}\n"
            f"QGIS: {qgis_version}\n"
            f"Python: {python_version}\n"
            f"System: {system_info}")


def hash_report_body(body: str) -> str:
    """Generate a short hash of the report body for deduplication."""
    return hashlib.md5(body.encode("utf-8")).hexdigest()[:8]


class FeedbackSubmissionDialog(QDialog):
    """Dialog for submitting feedback directly via GitHub API."""
    
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.setWindowTitle("Ag-GIS — Submit report")
        from .branding import brand_dialog
        brand_dialog(self)
        self.resize(750, 700)
        
        self.report_id = generate_report_id()
        self.created = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.github_token: Optional[str] = None
        
        # Load stored token
        token_data = load_oauth_token()
        if token_data:
            self.github_token = token_data["token"]
            self.status.setText("GitHub token found. Report can be submitted without login.")
            self.status.setStyleSheet("color: green;")
        else:
            self.github_token = None
            self.status.setText("No GitHub token stored. Login to create a token or use Copy/Email.")
            self.status.setStyleSheet("color: orange;")
        
        layout = QVBoxLayout(self)
        
        # Intro text
        intro = QLabel(
            "Submit your report directly to GitHub without logging in. "
            "This uses a stored GitHub token for API submission. "
            "Your report is public once submitted."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        
        # Form page
        self.tabs = QWidget()
        form_layout = QFormLayout(self.tabs)
        
        # Report fields
        self.kind = QComboBox()
        self.kind.addItems(KINDS)
        self.kind.currentTextChanged.connect(self.update_preview)
        
        self.title = QLineEdit()
        self.title.setMaxLength(140)
        self.title.setPlaceholderText("A short description")
        self.title.textChanged.connect(self.update_preview)
        
        self.area = QComboBox()
        self.area.addItems(["Map and screen", "Farm data", "Data imports", 
                           "Installation and updates", "Other"])
        self.area.currentTextChanged.connect(self.update_preview)
        
        self.impact = QComboBox()
        self.impact.addItems([
            "I can keep working",
            "It slows me down",
            "I cannot finish the job"
        ])
        self.impact.currentTextChanged.connect(self.update_preview)
        
        self.details = QPlainTextEdit()
        self.details.setPlaceholderText(
            "What happened? What would help? Do not include private farm data or passwords."
        )
        self.details.textChanged.connect(self.update_preview)
        
        self.steps = QPlainTextEdit()
        self.steps.setPlaceholderText("Which buttons or steps led to this? (optional)")
        self.steps.textChanged.connect(self.update_preview)
        
        self.expected = QPlainTextEdit()
        self.expected.setPlaceholderText("What did you expect to happen? (optional)")
        self.expected.textChanged.connect(self.update_preview)
        
        self.include_versions = QCheckBox("Include app, mapping tools and system versions")
        self.include_versions.setChecked(True)
        self.include_versions.toggled.connect(self.update_preview)
        
        # Add fields to form
        for label, widget in (
            ("Type", self.kind),
            ("Summary", self.title),
            ("Where", self.area),
            ("Effect on your work", self.impact),
            ("Details", self.details),
            ("Steps", self.steps),
            ("Expected result", self.expected)
        ):
            form_layout.addRow(label, widget)
        form_layout.addRow(self.include_versions)
        
        self.tabs.setLayout(form_layout)
        layout.addWidget(self.tabs)
        
        # Preview tab
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.tabs.addTab(self.preview, "Review report")
        layout.addWidget(self.tabs)
        
        # Notice
        notice = QLabel(
            "GitHub reports and attachments are public. Only the text shown in Review report "
            "is shared. No map, farm files, file paths, logs or account details are collected "
            "automatically. Remove sensitive information you typed yourself before sharing."
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        
        # Action buttons
        self.submit_btn = QPushButton("Submit report")
        self.submit_btn.setEnabled(self.github_token is not None)
        self.submit_btn.clicked.connect(self.submit_report)
        self.submit_btn.setStyleSheet("font-weight: bold;")
        
        self.copy_btn = QPushButton("Copy report")
        self.copy_btn.clicked.connect(self.copy_report)
        
        self.email_btn = QPushButton("Email draft…")
        self.email_btn.clicked.connect(self.email_report)
        
        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.submit_btn)
        actions_layout.addWidget(self.copy_btn)
        actions_layout.addWidget(self.email_btn)
        layout.addLayout(actions_layout)
        
        # Footer
        footer_layout = QHBoxLayout()
        tracker_btn = QPushButton("View reported issues")
        tracker_btn.clicked.connect(lambda: self.open_url(ISSUES_URL))
        footer_layout.addWidget(tracker_btn)
        footer_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        footer_layout.addWidget(close_btn)
        layout.addLayout(footer_layout)
        
        # Status label
        self.status = QLabel("A report is tracked only after GitHub gives it an issue number.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        
        # Connect previews
        for widget in (self.details, self.steps, self.expected):
            widget.textChanged.connect(self.update_preview)
        self.title.textChanged.connect(self.update_preview)
        for widget in (self.kind, self.area, self.impact):
            widget.currentIndexChanged.connect(self.update_preview)
        
        self.update_preview()
    
    def body(self) -> str:
        """Generate the full report body."""
        return report_text(
            self.kind.currentText(),
            self.title.text(),
            self.area.currentText(),
            self.impact.currentText(),
            self.details.toPlainText(),
            self.steps.toPlainText(),
            self.expected.toPlainText(),
            environment_summary(
                self.include_versions.isChecked(),
                Qgis.QGIS_VERSION,
                QApplication.applicationVersion() if hasattr(QApplication, 'applicationVersion') else str(Qgis.QGIS_VERSION),
                f"{QApplication.applicationName()} {QApplication.applicationVersion()}"
            ),
            self.report_id,
            self.created
        )
    
    def update_preview(self):
        """Update the preview text."""
        self.preview.setPlainText(self.body())
    
    def is_ready(self) -> bool:
        """Check if the report has required fields."""
        return bool(self.title.text().strip() and self.details.toPlainText().strip())
    
    def copy_report(self):
        """Copy report to clipboard."""
        QApplication.clipboard().setText(self.body())
        self.status.setText("Report copied. Review it before pasting it into GitHub or email.")
    
    def email_report(self):
        """Open email client with draft."""
        if not self.is_ready():
            return
        
        subject = f"Ag-GIS feedback: {self.title.text()}"
        body = self.body()
        
        # Try to open mailto link
        try:
            from urllib.parse import quote, urlencode
            url = f"mailto:{SUPPORT_EMAIL}?subject={quote(subject)}&body={quote(body)}"
            QDesktopServices.openUrl(QUrl.fromLocalFile("mailto:" + SUPPORT_EMAIL + "?" + urlencode(
                {"subject": subject, "body": body}, quote_via=quote)))
            self.status.setText("Email draft opened. Review and send it yourself.")
            return
        except Exception:
            pass
        
        # Fallback: copy and instruct
        self.copy_report()
        self.status.setText(
            "Email could not be opened. Paste the copied report into your email client "
            f"to: {SUPPORT_EMAIL}"
        )
    
    def open_url(self, url: str) -> bool:
        """Open URL in default browser."""
        try:
            QDesktopServices.openUrl(QUrl(url))
            return True
        except Exception:
            self.status.setText("Could not open that application. Use Copy or Email instead.")
            return False
    
    def submit_report(self):
        """Submit the report via GitHub API."""
        if not self.is_ready():
            QMessageBox.warning(self, "Incomplete report",
                               "Please add a summary and details before submitting.")
            return
        
        if not self.github_token:
            QMessageBox.information(self, "No GitHub token",
                                   "No GitHub token is stored. "
                                   "You need to login first to create a token, "
                                   "then use Copy report or Email draft.")
            return
        
        # Generate report body
        body = self.body()
        report_hash = hash_report_body(body)
        
        # Prepare API data
        issue_data = {
            "title": " ".join(self.title.text().splitlines()).strip(),
            "body": body,
            "labels": ["feedback"]
        }
        
        # Try to add type-specific labels
        kind = self.kind.currentText()
        if kind in KINDS:
            template = KINDS[kind]
            issue_data["labels"].append("type:" + template.replace(".yml", "").replace("-", " "))
        
        # Make API call
        try:
            import requests
            
            headers = {
                "Authorization": make_auth_header(self.github_token),
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            # Create the issue
            response = requests.post(
                f"{GITHUB_API_BASE}/repos/{AG_GIS_FEEDBACK_REPO}/issues",
                headers=headers,
                json=issue_data,
                timeout=30
            )
            
            if response.status_code == 201:
                # Success - get the issue number
                issue_data = response.json()
                issue_number = issue_data.get("number")
                
                if issue_number:
                    issue_url = f"https://github.com/{AG_GIS_FEEDBACK_REPO}/issues/{issue_number}"
                    
                    self.status.setText(
                        f"✓ Report submitted! Issue #{issue_number} created at {issue_url}\n\n"
                        f"Report ID: {self.report_id}\n"
                        f"Hash: {report_hash}\n\n"
                        f"You can view, edit, or close this issue at the link above."
                    )
                    self.status.setStyleSheet("color: green; font-weight: bold;")
                    self.submit_btn.setEnabled(False)
                    self.submit_btn.setText("Submitted")
                    
                    # Update preview to show issue link
                    self.preview.setPlainText(
                        self.body() + f"\n\n---\n\n**✓ Submitted!**\n\n"
                        f"Your issue has been created: {issue_url}\n\n"
                        f"Report ID: {self.report_id}\n"
                        f"Hash: {report_hash}"
                    )
                    
                    QMessageBox.information(
                        self,
                        "Report Submitted",
                        f"Issue #{issue_number} has been created.\n\n"
                        f"You can view it at: {issue_url}\n\n"
                        f"Report ID: {self.report_id}"
                    )
                else:
                    raise Exception("No issue number in response")
            
            elif response.status_code == 401:
                QMessageBox.critical(self, "Authentication failed",
                                   "Your GitHub token is invalid or expired.\n\n"
                                   "1. Go to GitHub Settings → Developer settings → Personal access tokens\n"
                                   "2. Create a new token with 'repo' scope\n"
                                   "3. Login to re-create the token or use Copy/Email instead.")
                delete_oauth_token()
                self.github_token = None
                self.submit_btn.setEnabled(False)
                self.status.setText("GitHub token invalid. Login to create a new token.")
                self.status.setStyleSheet("color: red;")
            
            elif response.status_code == 403:
                QMessageBox.critical(self, "Access denied",
                                   "Your GitHub token does not have permission to create issues.\n\n"
                                   "Please ensure the token has 'repo' scope (full control of private repositories).")
            
            else:
                error_msg = response.json().get("message", f"HTTP {response.status_code}")
                QMessageBox.critical(self, "Submission failed",
                                   f"Failed to submit report: {error_msg}")
                
        except ImportError:
            QMessageBox.critical(self, "Missing dependency",
                               "The requests library is not installed.\n\n"
                               "Install it with: pip install requests")
        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to submit: {str(e)}")
    
    def login_to_create_token(self):
        """Guide user to create a GitHub OAuth token."""
        from qgis.PyQt.QtWidgets import QInputDialog, QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Create GitHub token",
            "No GitHub token is stored.\n\n"
            "To submit issues directly without logging in each time:\n\n"
            "1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)\n"
            "2. Click 'Generate new token (classic)'\n"
            "3. Give it a note: 'Ag-GIS issue submission'\n"
            "4. Select scopes:\n   - ☑ repo (full control of private repositories)\n"
            "5. Generate the token and COPY IT (you won't see it again!)\n\n"
            "Paste the token below:",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            token, ok = QInputDialog.getText(self, "GitHub token",
                                             "Paste your GitHub personal access token here:")
            if ok and token:
                # Save the token
                if save_oauth_token(token):
                    self.github_token = token
                    self.status.setText("GitHub token saved. You can now submit reports.")
                    self.status.setStyleSheet("color: green;")
                    self.submit_btn.setEnabled(True)
                    QMessageBox.information(self, "Token saved",
                                           "Your GitHub token has been saved. "
                                           "You can now submit reports directly.")
                else:
                    QMessageBox.warning(self, "Save failed",
                                       "Could not save the token. "
                                       "Try again or use Copy/Email instead.")
            else:
                QMessageBox.information(self, "Token required",
                                       "A token is required for direct submission. "
                                       "Please try again or use Copy/Email.")


class SubmissionActions:
    """Actions for the feedback submission dialog."""
    
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None
    
    def open(self):
        """Open the submission dialog."""
        if self.dialog is None:
            self.dialog = FeedbackSubmissionDialog(self.iface)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
    
    def close(self):
        """Close the submission dialog."""
        if self.dialog is not None:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None
