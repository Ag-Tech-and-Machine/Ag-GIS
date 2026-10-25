"""Exercise reporting, privacy, lossless fallbacks and lifecycle with real Qt."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QApplication, QMainWindow
from ag_tech_tooling import feedback

app = QgsApplication([], False)
app.initQgis()
window = QMainWindow()
iface = Mock()
iface.mainWindow.return_value = window
controller = feedback.FeedbackActions(iface)
with patch.object(feedback.QDesktopServices, "openUrl") as no_browser, patch.object(
        feedback.Path, "home", side_effect=AssertionError("Onboarding must not inspect account files")):
    controller.open()
    no_browser.assert_not_called()
dialog = controller.dialog
assert dialog.isVisible()
# Discover onboarding without a network connection or credentials.
assert dialog.tabs.tabText(2) == "Connect your agent"
start_here = dialog.agent_guide.toPlainText()
assert "START HERE" in start_here and "JamRov/Ag-GIS-Feedback" in start_here
assert "Ag-Tech-and-Machine/Ag-GIS" in start_here
assert "Do not submit" in start_here and "native QGIS" in start_here
from qgis.PyQt.QtWidgets import QPushButton
copy_agent = next(button for button in dialog.findChildren(QPushButton)
                  if button.text() == "Copy agent instructions")
copy_agent.click()
assert QApplication.clipboard().text() == start_here
assert dialog.agent_guide.isReadOnly()
with patch.object(feedback.QDesktopServices, "openUrl", return_value=True) as browser:
    dialog.open_issue()
    browser.assert_not_called()
    assert "summary and details" in dialog.status.text()
    dialog.title.setText("Élévation & map? A=1")
    dialog.details.setPlainText("Synthetic example: a map button had no visible result.")
    dialog.steps.setPlainText("1. Open test map\n2. Click map button")
    dialog.expected.setPlainText("See the test field")
    report = dialog.body()
    assert dialog.preview.toPlainText() == report
    assert "QGIS:" in report and "Python:" in report
    assert str(Path.home()) not in feedback.environment_summary()
    assert "APPDATA" not in feedback.environment_summary()
    for kind, template in feedback.KINDS.items():
        dialog.kind.setCurrentText(kind)
        browser.reset_mock()
        dialog.open_issue()
        url = browser.call_args.args[0].toString()
        assert urlsplit(url).path == "/JamRov/Ag-GIS-Feedback/issues/new"
        query = parse_qs(urlsplit(url).query)
        assert query["template"] == [template]
        assert query["title"] == [dialog.title.text()]
        assert query["report"] == [dialog.body()]
        assert "Submit new issue" in dialog.status.text()
    dialog.copy_report()
    assert QApplication.clipboard().text() == dialog.body()
    dialog.include_versions.setChecked(False)
    assert "## App versions\nNot included" in dialog.body()
    assert "Python:" not in dialog.body()
    with tempfile.TemporaryDirectory(prefix="aggis-feedback-") as temporary:
        path = Path(temporary) / "report.md"
        with patch.object(feedback.QFileDialog, "getSaveFileName", return_value=(str(path), "Report (*.md)")):
            dialog.save_report()
        assert path.read_text(encoding="utf-8") == dialog.body()
        original = path.read_bytes()
        with patch.object(feedback.QFileDialog, "getSaveFileName", return_value=("", "")):
            dialog.save_report()
        assert path.read_bytes() == original
        with patch.object(feedback.QFileDialog, "getSaveFileName", return_value=(str(path), "")), patch.object(
                feedback, "save_text", side_effect=OSError("Synthetic write failure")):
            dialog.save_report()
        assert path.read_bytes() == original and dialog.details.toPlainText()
        assert "Could not save" in dialog.status.text()
    browser.reset_mock()
    dialog.email_report()
    query = parse_qs(urlsplit(browser.call_args.args[0].toString()).query)
    assert query["body"] == [dialog.body()]
    dialog.details.setPlainText("Long Unicode report: 農場 & test\n" * 500)
    long_body = dialog.body()
    with patch.object(feedback.QMessageBox, "information"):
        dialog.open_issue()
    assert QApplication.clipboard().text() == long_body
    assert "report=" not in browser.call_args.args[0].toString()
    assert len(browser.call_args.args[0].toEncoded()) <= feedback.MAX_URL_BYTES
    dialog.email_report()
    assert QApplication.clipboard().text() == long_body
    assert len(browser.call_args.args[0].toEncoded()) <= feedback.MAX_URL_BYTES
    assert "Paste your copied" in parse_qs(urlsplit(browser.call_args.args[0].toString()).query)["body"][0]
with patch.object(feedback.QDesktopServices, "openUrl", return_value=False):
    dialog.open_url(feedback.ISSUES_URL)
    assert "Could not open" in dialog.status.text()
    assert dialog.body() == long_body
dialog.reject()
controller.open()
assert controller.dialog is dialog and dialog.body() == long_body
controller.close()
assert controller.dialog is None
controller.close()
controller.open()
assert controller.dialog is not dialog
controller.close()
with patch.object(feedback.Path, "read_text", side_effect=OSError("Synthetic missing guide")):
    controller.open()
    assert "instructions are missing" in controller.dialog.agent_guide.toPlainText()
    assert "local Ag-GIS still works" in controller.dialog.agent_guide.toPlainText()
controller.close()
window.close()
app.exitQgis()
print("Feedback report, URL/email encoding, versions opt-out, lossless long reports, save/cancel/failure and lifecycle checks passed")
