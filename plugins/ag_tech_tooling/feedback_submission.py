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



    pass  # QGIS not available, skip this test

except ImportError:

            from qgis.PyQt.QtWidgets import QInputDialog, QMessageBox

            """Guide user to create a GitHub OAuth token."""

        def login_to_create_token(self):

        

                                   f"Failed to submit: {str(e)}")

                QMessageBox.critical(self, "Error",

            except Exception as e:

                                   "Install it with: pip install requests")

                                   "The requests library is not installed.\n\n"

                QMessageBox.critical(self, "Missing dependency",

            except ImportError:

                    

                                       f"Failed to submit report: {error_msg}")

                    QMessageBox.critical(self, "Submission failed",

                    error_msg = response.json().get("message", f"HTTP {response.status_code}")

                else:

                

                                       "Please ensure the token has 'repo' scope (full control of private repositories).")

                                       "Your GitHub token does not have permission to create issues.\n\n"

                    QMessageBox.critical(self, "Access denied",

                elif response.status_code == 403:

                

                    self.status.setStyleSheet("color: red;")

                    self.status.setText("GitHub token invalid. Login to create a new token.")

                    self.submit_btn.setEnabled(False)

                    self.github_token = None

                    delete_oauth_token()

                                       "3. Login to re-create the token or use Copy/Email instead.")

                                       "2. Create a new token with 'repo' scope\n"

                                       "1. Go to GitHub Settings → Developer settings → Personal access tokens\n"

                                       "Your GitHub token is invalid or expired.\n\n"

                    QMessageBox.critical(self, "Authentication failed",

                elif response.status_code == 401:

                

                        self.status.setStyleSheet("color: orange;")

                        self.status.setText("Submission failed: API returned malformed response.")

                        QMessageBox.critical(self, "Submission issue", error_msg)

                        error_msg += "This may be a temporary API issue. Please try again."

                        error_msg = "GitHub API returned success but no issue number. "

                        # Handle malformed GitHub API response (201 without 'number' field)

                    else:

                        )

                            f"Report ID: {self.report_id}"

                            f"You can view it at: {issue_url}\n\n"

                            f"Issue #{issue_number} has been created.\n\n"

                            "Report Submitted",

                            self,

                        QMessageBox.information(

                        

                        )

                            f"Hash: {report_hash}"

                            f"Report ID: {self.report_id}\n"

                            f"Your issue has been created: {issue_url}\n\n"

                            self.body() + f"\n\n---\n\n**✓ Submitted!**\n\n"

                        self.preview.setPlainText(

                        # Update preview to show issue link

                        

                        self.submit_btn.setText("Submitted")

                        self.submit_btn.setEnabled(False)

                        self.status.setStyleSheet("color: green; font-weight: bold;")

                        )

                            f"You can view, edit, or close this issue at the link above."

                            f"Hash: {report_hash}\n\n"

                            f"Report ID: {self.report_id}\n"

                            f"✓ Report submitted! Issue #{issue_number} created at {issue_url}\n\n"

                        self.status.setText(

                        

                        issue_url = f"https://github.com/{AG_GIS_FEEDBACK_REPO}/issues/{issue_number}"

                    if issue_number:

                    

                    issue_number = issue_data.get("number")

                    issue_data = response.json()

                    # Success - get the issue number

                if response.status_code == 201:

                

                )

                    timeout=30

                    json=issue_data,

                    headers=headers,

                    f"{GITHUB_API_BASE}/repos/{AG_GIS_FEEDBACK_REPO}/issues",

                response = requests.post(

                # Create the issue

                

                }

                    "X-GitHub-Api-Version": "2022-11-28"

                    "Accept": "application/vnd.github.v3+json",

                    "Authorization": make_auth_header(self.github_token),

                headers = {

                

                import requests

            try:

            # Make API call

            

                issue_data["labels"].append("type:" + template.replace(".yml", "").replace("-", " "))

                template = KINDS[kind]

            if kind in KINDS:

            kind = self.kind.currentText()

            # Try to add type-specific labels

            

            }

                "labels": ["feedback"]

                "body": body,

                "title": " ".join(self.title.text().splitlines()).strip(),

            issue_data = {

            # Prepare API data

            

            report_hash = hash_report_body(body)

            body = self.body()

            # Generate report body

            

                return

                                       "then use Copy report or Email draft.")

                                       "You need to login first to create a token, "

                                       "No GitHub token is stored. "

                QMessageBox.information(self, "No GitHub token",

            if not self.github_token:

            

                return

                                   "Please add a summary and details before submitting.")

                QMessageBox.warning(self, "Incomplete report",

            if not self.is_ready():

            """Submit the report via GitHub API."""

        def submit_report(self):

        

                return False

                self.status.setText("Could not open that application. Use Copy or Email instead.")

            except Exception:

                return True

                QDesktopServices.openUrl(QUrl(url))

            try:

            """Open URL in default browser."""

        def open_url(self, url: str) -> bool:

        

            )

                f"to: {SUPPORT_EMAIL}"

                "Email could not be opened. Paste the copied report into your email client "

            self.status.setText(

            self.copy_report()

            # Fallback: copy and instruct

            

                pass

            except Exception:

                return

                self.status.setText("Email draft opened. Review and send it yourself.")

                    {"subject": subject, "body": body}, quote_via=quote)))

                QDesktopServices.openUrl(QUrl.fromLocalFile("mailto:" + SUPPORT_EMAIL + "?" + urlencode(

                url = f"mailto:{SUPPORT_EMAIL}?subject={quote(subject)}&body={quote(body)}"

                from urllib.parse import quote, urlencode

            try:

            # Try to open mailto link

            

            body = self.body()

            subject = f"Ag-GIS feedback: {self.title.text()}"

            

                return

            if not self.is_ready():

            """Open email client with draft."""

        def email_report(self):

        

            self.status.setText("Report copied. Review it before pasting it into GitHub or email.")

            QApplication.clipboard().setText(self.body())

            """Copy report to clipboard."""

        def copy_report(self):

        

            return bool(self.title.text().strip() and self.details.toPlainText().strip())

            """Check if the report has required fields."""

        def is_ready(self) -> bool:

        

            self.preview.setPlainText(self.body())

            """Update the preview text."""

        def update_preview(self):

        

            )

                self.created

                self.report_id,

                ),

                    f"{QApplication.applicationName()} {QApplication.applicationVersion()}"

                    QApplication.applicationVersion() if hasattr(QApplication, 'applicationVersion') else str(Qgis.QGIS_VERSION),

                    Qgis.QGIS_VERSION,

                    self.include_versions.isChecked(),

                environment_summary(

                self.expected.toPlainText(),

                self.steps.toPlainText(),

                self.details.toPlainText(),

                self.impact.currentText(),

                self.area.currentText(),

                self.title.text(),

                self.kind.currentText(),

            return report_text(

            """Generate the full report body."""

        def body(self) -> str:

        

            self.update_preview()

            

                widget.currentIndexChanged.connect(self.update_preview)

            for widget in (self.kind, self.area, self.impact):

            self.title.textChanged.connect(self.update_preview)

                widget.textChanged.connect(self.update_preview)

            for widget in (self.details, self.steps, self.expected):

            # Connect previews

            

            layout.addWidget(self.status)

            self.status.setWordWrap(True)

            self.status = QLabel("A report is tracked only after GitHub gives it an issue number.")

            # Status label

            

            layout.addLayout(footer_layout)

            footer_layout.addWidget(close_btn)

            close_btn.clicked.connect(self.reject)

            close_btn = QPushButton("Close")

            

            footer_layout.addStretch()

            footer_layout.addWidget(tracker_btn)

            tracker_btn.clicked.connect(lambda: self.open_url(ISSUES_URL))

            tracker_btn = QPushButton("View reported issues")

            footer_layout = QHBoxLayout()

            # Footer

            

            layout.addLayout(actions_layout)

            actions_layout.addWidget(self.email_btn)

            actions_layout.addWidget(self.copy_btn)

            actions_layout.addWidget(self.submit_btn)

            actions_layout = QHBoxLayout()

            

            self.email_btn.clicked.connect(self.email_report)

            self.email_btn = QPushButton("Email draft…")

            

            self.copy_btn.clicked.connect(self.copy_report)

            self.copy_btn = QPushButton("Copy report")

            

            self.submit_btn.setStyleSheet("font-weight: bold;")

            self.submit_btn.clicked.connect(self.submit_report)

            self.submit_btn.setEnabled(self.github_token is not None)

            self.submit_btn = QPushButton("Submit report")

            # Action buttons

            

            layout.addWidget(notice)

            notice.setWordWrap(True)

            )

                "automatically. Remove sensitive information you typed yourself before sharing."

                "is shared. No map, farm files, file paths, logs or account details are collected "

                "GitHub reports and attachments are public. Only the text shown in Review report "

            notice = QLabel(

            # Notice

            

            layout.addWidget(self.tabs)

            self.tabs.addTab(self.preview, "Review report")

            self.preview.setReadOnly(True)

            self.preview = QPlainTextEdit()

            # Preview tab

            

            layout.addWidget(self.tabs)

            self.tabs.setLayout(form_layout)

            

            form_layout.addRow(self.include_versions)

                form_layout.addRow(label, widget)

            ):

                ("Expected result", self.expected)

                ("Steps", self.steps),

                ("Details", self.details),

                ("Effect on your work", self.impact),

                ("Where", self.area),

                ("Summary", self.title),

                ("Type", self.kind),

            for label, widget in (

            # Add fields to form

            

            self.include_versions.toggled.connect(self.update_preview)

            self.include_versions.setChecked(True)

            self.include_versions = QCheckBox("Include app, mapping tools and system versions")

            

            self.expected.textChanged.connect(self.update_preview)

            self.expected.setPlaceholderText("What did you expect to happen? (optional)")

            self.expected = QPlainTextEdit()

            

            self.steps.textChanged.connect(self.update_preview)

            self.steps.setPlaceholderText("Which buttons or steps led to this? (optional)")

            self.steps = QPlainTextEdit()

            

            self.details.textChanged.connect(self.update_preview)

            )

                "What happened? What would help? Do not include private farm data or passwords."

            self.details.setPlaceholderText(

            self.details = QPlainTextEdit()

            

            self.impact.currentTextChanged.connect(self.update_preview)

            ])

                "I cannot finish the job"

                "It slows me down",

                "I can keep working",

            self.impact.addItems([

            self.impact = QComboBox()

            

            self.area.currentTextChanged.connect(self.update_preview)

                               "Installation and updates", "Other"])

            self.area.addItems(["Map and screen", "Farm data", "Data imports", 

            self.area = QComboBox()

            

            self.title.textChanged.connect(self.update_preview)

            self.title.setPlaceholderText("A short description")

            self.title.setMaxLength(140)

            self.title = QLineEdit()

            

            self.kind.currentTextChanged.connect(self.update_preview)

            self.kind.addItems(KINDS)

            self.kind = QComboBox()

            # Report fields

            

            form_layout = QFormLayout(self.tabs)

            self.tabs = QWidget()

            # Form page

            

            layout.addWidget(intro)

            intro.setWordWrap(True)

            )

                "Your report is public once submitted."

                "This uses a stored GitHub token for API submission. "

                "Submit your report directly to GitHub without logging in. "

            intro = QLabel(

            # Intro text

            

            layout = QVBoxLayout(self)

            

                self.status.setStyleSheet("color: orange;")

                self.status.setText("No GitHub token stored. Login to create a token or use Copy/Email.")

                self.github_token = None

            else:

                self.status.setStyleSheet("color: green;")

                self.status.setText("GitHub token found. Report can be submitted without login.")

                self.github_token = token_data["token"]

            if token_data:

            token_data = load_oauth_token()

            # Load stored token

            

            self.github_token: Optional[str] = None

            self.created = datetime.now(timezone.utc).isoformat(timespec="seconds")

            self.report_id = generate_report_id()

            

            self.resize(750, 700)

            brand_dialog(self)

            from .branding import brand_dialog

            self.setWindowTitle("Ag-GIS — Submit report")

            super().__init__(iface.mainWindow())

        def __init__(self, iface):

        

        """Dialog for submitting feedback directly via GitHub API."""

    class FeedbackSubmissionDialog(QDialog):

    

    

        return hashlib.md5(body.encode("utf-8")).hexdigest()[:8]

        """Generate a short hash of the report body for deduplication."""

    def hash_report_body(body: str) -> str:

    

    

                f"System: {system_info}")

                f"Python: {python_version}\n"

                f"QGIS: {qgis_version}\n"

        return (f"Ag-GIS: {qgis_version}\n"

        

            return "Not included"

        if not include_versions:

        """Generate environment information string."""

                            python_version: str, system_info: str) -> str:

    def environment_summary(include_versions: bool, qgis_version: str,

    

    

                f"Created (UTC): {created}\n")

                f"Report ID: {report_id}\n"

                f"## App versions\n{environment or 'Not included'}\n\n"

                f"## Expected result\n{expected.strip() or 'Not provided'}\n\n"

                f"## How to see it\n{steps.strip() or 'Not provided'}\n\n"

                f"## What happened or would help\n{details.strip()}\n\n"

                f"Impact: {impact}\n\n"

                f"Area: {area}\n"

                f"Type: {kind}\n"

        return (f"# {title_clean}\n\n"

        title_clean = " ".join(title.splitlines()).strip() or "Untitled feedback"

        """Format report text for GitHub."""

                    report_id: str, created: str) -> str:

                    details: str, steps: str, expected: str, environment: str,

    def report_text(kind: str, title: str, area: str, impact: str,

    

    

        return str(uuid.uuid4())

        """Generate a unique report ID."""

    def generate_report_id() -> str:

    

    

        return f"Bearer {token}"

        """Create GitHub API authentication header."""

    def make_auth_header(token: str) -> str:

    

    

        TOKEN_FILE.unlink(missing_ok=True)

        ensure_plugin_dir()

        """Delete stored OAuth token."""

    def delete_oauth_token():

    

    

            return False

        except Exception:

            return True

            TOKEN_FILE.write_text(config.read_string(config["github"]), encoding="utf-8")

            }

                "expiry": expiry or ""

                "token": token,

            config["github"] = {

            config = configparser.ConfigParser()

        try:

        

        ensure_plugin_dir()

        """Save OAuth token to config file."""

    def save_oauth_token(token: str, expiry: str = "") -> bool:

    

    

            return None

        except Exception:

            return {"token": token, "expiry": expiry}

            

                return None

            if len(token) != 40 or not all(c in "0123456789abcdefABCDEF" for c in token):

            # Validate token format (should be 40 hex chars for OAuth token)

            

                    return None

                except ValueError:

                        return None

                    if expiry_time < datetime.now(timezone.utc):

                    expiry_time = datetime.fromisoformat(expiry.replace("Z", "+00:00"))

                try:

            if expiry:

            # Parse expiry timestamp

            

            expiry = config.get("github", "expiry", fallback="")

            token = config["github"]["token"]

            

                return None

            if "github" not in config or "token" not in config["github"]:

            config.read(TOKEN_FILE, encoding="utf-8")

            config = configparser.ConfigParser()

        try:

        

            return None

        if not TOKEN_FILE.exists():

        ensure_plugin_dir()

        """Load stored OAuth token from config file."""

    def load_oauth_token() -> Optional[dict]:

    

    

        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

        """Create plugin settings directory if it doesn't exist."""

    def ensure_plugin_dir():

    

    

    TOKEN_FILE = PLUGIN_DIR / "github_oauth_token.ini"

    PLUGIN_DIR = Path.home() / ".qgis2" / "plugins" / "ag_tech_tooling"

    # Token storage paths

    

    }

        "I need help": "help.yml"

        "An idea or improvement": "suggestion.yml",

        "Something went wrong": "bug_report.yml",

    KINDS = {

    # Template mappings

    

    SUPPORT_EMAIL = "admin@agtechandmachine.com"

    ISSUES_URL = f"https://github.com/{AG_GIS_FEEDBACK_REPO}/issues"

    AG_GIS_FEEDBACK_REPO = "JamRov/Ag-GIS-Feedback"

    GITHUB_API_BASE = "https://api.github.com"

    # GitHub API settings - these must match the GitHub App configuration

    

        QPushButton, QVBoxLayout, QWidget)

        QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,

    from qgis.PyQt.QtWidgets import (QApplication, QDialog, QFormLayout,

    from qgis.PyQt.QtGui import QDesktopServices

    from qgis.PyQt.QtCore import QUrl, Qt, QIODevice

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import Qgis
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

        

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


