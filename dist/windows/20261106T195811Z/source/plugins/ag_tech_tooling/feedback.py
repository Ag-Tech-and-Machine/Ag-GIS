# SPDX-License-Identifier: GPL-2.0-or-later
"""Reviewable reports using Qt, the user's browser/mail app and native GitHub Issues."""
import configparser
from datetime import datetime, timezone
from pathlib import Path
import platform
from urllib.parse import quote, urlencode
import uuid

from qgis.core import Qgis
from qgis.PyQt.QtCore import QIODevice, QSaveFile, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QPushButton, QTabWidget, QVBoxLayout, QWidget)

ISSUES_URL = "https://github.com/JamRov/Ag-GIS-Feedback/issues"
SUPPORT_EMAIL = "[user identity]"
KINDS = {"Something went wrong": "bug_report.yml",
         "An idea or improvement": "suggestion.yml",
         "I need help": "help.yml"}
MAX_URL_BYTES = 1800  # Keep Windows browser/mail launches short; never truncate a report.


def environment_summary():
    metadata = configparser.ConfigParser()
    metadata.read(Path(__file__).with_name("metadata.txt"), encoding="utf-8")
    return (f"Ag-GIS: {metadata.get('general', 'version', fallback='unknown')}\n"
            f"QGIS: {Qgis.QGIS_VERSION}\nPython: {platform.python_version()}\n"
            f"System: {platform.system()} {platform.release()}")


def report_text(kind, title, area, impact, details, steps, expected, environment, report_id):
    title = " ".join(title.splitlines()).strip() or "Untitled feedback"
    return (f"# {title}\n\nType: {kind}\nArea: {area}\nImpact: {impact}\n\n"
            f"## What happened or would help\n{details.strip()}\n\n"
            f"## How to see it\n{steps.strip() or 'Not provided'}\n\n"
            f"## Expected result\n{expected.strip() or 'Not provided'}\n\n"
            f"## App versions\n{environment or 'Not included'}\n\n"
            f"Report ID: {report_id}\n")


def issue_url(kind, title, report):
    """GitHub's form field ID 'report' supports URL prefills; return lossless fallback."""
    base = {"template": KINDS[kind], "title": title}
    url = ISSUES_URL + "/new?" + urlencode({**base, "report": report})
    if len(url.encode("utf-8")) <= MAX_URL_BYTES:
        return url, False
    return ISSUES_URL + "/new?" + urlencode(base), True


def save_text(path, text):
    file = QSaveFile(str(path))
    data = text.encode("utf-8")
    if not file.open(QIODevice.WriteOnly):
        raise OSError(file.errorString())
    if file.write(data) != len(data):
        file.cancelWriting()
        raise OSError(file.errorString())
    if not file.commit():
        raise OSError(file.errorString())


class FeedbackDialog(QDialog):
    def __init__(self, iface):
        super().__init__(iface.mainWindow())
        self.setWindowTitle("Ag-GIS — Feedback and help")
        from .branding import brand_dialog
        brand_dialog(self)
        self.resize(700, 700)
        self.report_id = str(uuid.uuid4())
        self.created = datetime.now(timezone.utc).isoformat(timespec="seconds")
        layout = QVBoxLayout(self)
        intro = QLabel("Tell us what went wrong, what is confusing, or what would make the job easier. "
                       "Nothing is sent automatically. Review your report before sharing it.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.tabs = QTabWidget()
        form_page = QWidget()
        form = QFormLayout(form_page)
        self.kind = QComboBox()
        self.kind.addItems(KINDS)
        self.title = QLineEdit()
        self.title.setMaxLength(140)
        self.title.setPlaceholderText("A short description")
        self.area = QComboBox()
        self.area.addItems(["Map and screen", "Farm data", "Data imports", "Installation and updates", "Other"])
        self.impact = QComboBox()
        self.impact.addItems(["I can keep working", "It slows me down", "I cannot finish the job"])
        self.details = QPlainTextEdit()
        self.details.setPlaceholderText("What happened? What would help? Do not include private farm data or passwords.")
        self.steps = QPlainTextEdit()
        self.steps.setPlaceholderText("Which buttons or steps led to this? (optional)")
        self.expected = QPlainTextEdit()
        self.expected.setPlaceholderText("What did you expect to happen? (optional)")
        self.include_versions = QCheckBox("Include app, mapping tools and system versions")
        self.include_versions.setChecked(True)
        for label, widget in (("Type", self.kind), ("Summary", self.title), ("Where", self.area),
                              ("Effect on your work", self.impact), ("Details", self.details),
                              ("Steps", self.steps), ("Expected result", self.expected)):
            form.addRow(label, widget)
        form.addRow(self.include_versions)
        self.tabs.addTab(form_page, "Describe")
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.tabs.addTab(self.preview, "Review report")
        agent_page = QWidget()
        agent_layout = QVBoxLayout(agent_page)
        self.agent_guide = QPlainTextEdit()
        self.agent_guide.setReadOnly(True)
        # One canonical source; builds ship a byte-identical offline copy.
        guide = Path(__file__).with_name("START_HERE.txt")
        if not guide.is_file():
            guide = Path(__file__).resolve().parents[2] / "START_HERE.md"
        try:
            instructions = guide.read_text(encoding="utf-8")
        except OSError:
            instructions = ("Agent instructions are missing from this installation. "
                            "Use START_HERE.md in a trusted Ag-GIS source checkout. "
                            "Nothing has been sent; local Ag-GIS still works.")
        self.agent_guide.setPlainText(instructions)
        agent_layout.addWidget(self.agent_guide)
        copy_agent = QPushButton("Copy agent instructions")
        copy_agent.clicked.connect(
            lambda: QApplication.clipboard().setText(self.agent_guide.toPlainText()))
        agent_layout.addWidget(copy_agent)
        self.tabs.addTab(agent_page, "Connect your agent")
        layout.addWidget(self.tabs)
        notice = QLabel("GitHub reports and attachments are public. Only the text shown in Review report is shared. No map, farm files, file paths, "
                        "logs or account details are collected automatically. A long report is copied "
                        "for you to paste into GitHub or email. GitHub needs a signed-in account; "
                        "Save report and Email draft also work without repository access.")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        actions = QHBoxLayout()
        for label, callback in (("Open GitHub form…", self.open_issue), ("Save report…", self.save_report),
                                ("Copy report", self.copy_report), ("Email draft…", self.email_report)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        footer = QHBoxLayout()
        tracker = QPushButton("View reported issues")
        tracker.clicked.connect(lambda: self.open_url(ISSUES_URL))
        footer.addWidget(tracker)
        footer.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.reject)
        footer.addWidget(close)
        layout.addLayout(footer)
        self.status = QLabel("A report is tracked only after GitHub gives it an issue number. Saved/email drafts are not submitted issues.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        for widget in (self.details, self.steps, self.expected):
            widget.textChanged.connect(self.update_preview)
        self.title.textChanged.connect(self.update_preview)
        for widget in (self.kind, self.area, self.impact):
            widget.currentIndexChanged.connect(self.update_preview)
        self.include_versions.toggled.connect(self.update_preview)
        self.update_preview()

    def body(self):
        return report_text(self.kind.currentText(), self.title.text(), self.area.currentText(),
                           self.impact.currentText(), self.details.toPlainText(), self.steps.toPlainText(),
                           self.expected.toPlainText(), environment_summary() if self.include_versions.isChecked() else "",
                           self.report_id) + f"Created (UTC): {self.created}\n"

    def update_preview(self, *_):
        self.preview.setPlainText(self.body())

    def ready(self):
        if not self.title.text().strip() or not self.details.toPlainText().strip():
            self.status.setText("Add a summary and details first. You can still save or copy an unfinished draft.")
            self.tabs.setCurrentIndex(0)
            return False
        return True

    def copy_report(self):
        QApplication.clipboard().setText(self.body())
        self.status.setText("Report copied. Review it before pasting it into GitHub or email.")

    def save_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save feedback report", f"Ag-GIS-feedback-{self.report_id[:8]}.md", "Report (*.md)")
        if not path:
            return
        try:
            save_text(path, self.body())
            self.status.setText("Report saved. Send it to support or paste it into GitHub to have it tracked.")
        except OSError as error:
            self.status.setText(f"Could not save the report: {error}. Your text is still here; try another folder or Copy report.")

    def open_url(self, url):
        if not QDesktopServices.openUrl(QUrl(url)):
            self.status.setText("Could not open that application. Use Copy report or Save report, then open GitHub/email yourself.")
            return False
        return True

    def open_issue(self):
        if not self.ready():
            return
        url, copy_needed = issue_url(self.kind.currentText(), self.title.text(), self.body())
        self.tabs.setCurrentIndex(1)
        if copy_needed:
            self.copy_report()
            QMessageBox.information(self, "Report copied", "Your report is too long for a browser address. "
                                    "It has been copied in full. Paste it into the Report field on GitHub.")
        if self.open_url(url):
            self.status.setText("GitHub opened. " + ("Paste the copied report, then " if copy_needed else "Review the form, then ") +
                                "choose Submit new issue. Keep its issue number to follow progress. Your draft stays here.")

    def email_report(self):
        if not self.ready():
            return
        subject = "Ag-GIS feedback: " + self.title.text()
        url = "mailto:" + SUPPORT_EMAIL + "?" + urlencode({"subject": subject, "body": self.body()}, quote_via=quote)
        if len(url.encode("utf-8")) > MAX_URL_BYTES:
            self.copy_report()
            url = "mailto:" + SUPPORT_EMAIL + "?" + urlencode({"subject": subject, "body": "Paste your copied Ag-GIS report here, or attach the saved report."}, quote_via=quote)
        if self.open_url(url):
            self.status.setText("Email draft opened. Review and send it yourself. If the body is short, paste the copied report or attach a saved report. Support will return an issue number after logging it.")


class FeedbackActions:
    def __init__(self, iface):
        self.iface, self.dialog = iface, None

    def open(self):
        if self.dialog is None:
            self.dialog = FeedbackDialog(self.iface)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def close(self):
        if self.dialog is not None:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None
