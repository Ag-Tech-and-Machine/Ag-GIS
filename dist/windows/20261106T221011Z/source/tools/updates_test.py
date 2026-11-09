"""Offline real-QGIS/Qt update tests; never writes a normal profile."""
import os
from pathlib import Path
import sys
import tempfile
import zipfile
import hashlib
import subprocess
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication, QgsProject
from qgis.PyQt.QtCore import QSettings, QTimer, QEventLoop, QIODevice, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
import json


class FakeReply(QNetworkReply):
    """Real Qt signals/device, with controlled bytes and no sockets."""
    def __init__(self, request):
        super().__init__()
        self.setRequest(request)
        self.setUrl(request.url())
        self.open(QIODevice.ReadOnly | QIODevice.Unbuffered)
        self.data = b""
        self.aborted = False

    def bytesAvailable(self):
        return len(self.data) + super().bytesAvailable()

    def readData(self, count):
        result, self.data = self.data[:count], self.data[count:]
        return result

    def abort(self):
        self.aborted = True
        self.setError(QNetworkReply.OperationCanceledError, "Cancelled")
        self.finished.emit()

    def deliver(self, data=b"", status=200, error=None, redirect=None):
        self.setAttribute(QNetworkRequest.HttpStatusCodeAttribute, status)
        if redirect:
            self.setAttribute(QNetworkRequest.RedirectionTargetAttribute, QUrl(redirect))
        if error:
            self.setError(QNetworkReply.HostNotFoundError, error)
        self.data += data
        self.readyRead.emit()
        self.finished.emit()


def spin(milliseconds=5):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()
from qgis.PyQt.QtWidgets import QMainWindow
from ag_tech_tooling import updates

scratch = Path(os.environ.get("TMPDIR") or Path.home() / "AppData/Local/hermes/cache/scratch")
scratch.mkdir(parents=True, exist_ok=True)
suite_home = tempfile.TemporaryDirectory(prefix="aggis-updates-suite-", dir=scratch, ignore_cleanup_errors=True)
QSettings.setDefaultFormat(QSettings.IniFormat)
QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(Path(suite_home.name) / "settings"))
app = QgsApplication([], False, str(Path(suite_home.name) / "qgis-profile"))
app.initQgis()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aggis-update-test-", dir=suite_home.name)
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root / "settings.ini"), QSettings.IniFormat)
        self.window = QMainWindow()
        self.iface = Mock()
        self.iface.mainWindow.return_value = self.window
        self.network = Mock()
        self.controller = None

    def tearDown(self):
        if self.controller:
            self.controller.close()
        self.window.close()
        app.processEvents()
        self.temp.cleanup()

    def make_controller(self, **kwargs):
        self.controller = updates.UpdateActions(self.iface, settings=self.settings, network=self.network,
                                                cache_root=self.root / "cache", recovery_root=self.root / "recovery", **kwargs)
        return self.controller

    def test_manual_check_empty_error_retry_cancel_and_unload(self):
        replies = []
        def get(request):
            reply = FakeReply(request)
            replies.append(reply)
            return reply
        self.network.get.side_effect = get
        c = self.make_controller()
        c.open()
        c.dialog.check.click()
        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[-1].request().attribute(QNetworkRequest.RedirectPolicyAttribute), QNetworkRequest.ManualRedirectPolicy)
        QTimer.singleShot(0, lambda: replies[-1].deliver(b'{"schema_version":1,"releases":[]}'))
        spin()
        self.assertIn("unavailable", c.dialog.status.text().lower())
        self.assertNotIn("up to date", c.dialog.status.text().lower())
        c.dialog.check.click()
        replies[-1].deliver(error="Synthetic offline")
        self.assertIn("unavailable", c.dialog.status.text().lower())
        c.dialog.check.click()
        current = replies[-1]
        c.dialog.cancel.click()
        self.assertTrue(current.aborted)
        self.assertIsNone(c.reply)
        self.assertIn("Cancelled", c.dialog.status.text())
        c.dialog.check.click()
        current = replies[-1]
        c.close()
        self.assertTrue(current.aborted)
        current.finished.emit()
        self.assertIsNone(c.reply)
        self.assertIsNone(c.dialog)

    def test_network_bounds_tls_redirect_timeout(self):
        replies = []
        self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]
        c = self.make_controller()
        c.open()
        c.check_now()
        reply = replies[-1]
        reply.data = b"x" * (updates.MAX_CATALOG_BYTES + 1)
        reply.readyRead.emit()
        self.assertTrue(reply.aborted, "Oversize catalogue must abort before finish")
        self.assertLessEqual(len(c._buffer), updates.MAX_CATALOG_BYTES)
        self.assertIn("too large", c.status_text)
        c.check_now()
        replies[-1].sslErrors.emit([])
        self.assertTrue(replies[-1].aborted)
        self.assertIn("TLS", c.status_text)
        c.check_now()
        replies[-1].deliver(status=302, redirect="https://evil.invalid/catalog.json")
        self.assertEqual(len(replies), 3)
        self.assertIn("redirect", c.status_text)
        with patch.object(updates, "NETWORK_TIMEOUT_MS", 1):
            c.check_now()
            spin(10)
        self.assertTrue(replies[-1].aborted)
        self.assertIn("timed out", c.status_text)

    def test_background_result_opens_with_notes_later_and_disabled_selection(self):
        from qgis.gui import QgsMessageBar
        bar = QgsMessageBar(self.window)
        self.iface.messageBar.return_value = bar
        replies = []
        self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]
        self.settings.setValue(updates.PREFIX + "enabled", True)
        c = self.make_controller()
        c.check_now(background=True)
        release = dict(version="99.0.0", channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256="a" * 64, size=100, notes="Saved background notes", restart_required=True, data_upgrade=False)
        replies[-1].deliver(json.dumps(dict(schema_version=1, releases=[release])).encode())
        self.assertIsNone(c.dialog)
        self.assertIsNotNone(c.notice)
        buttons = c.notice.findChildren(updates.QPushButton)
        next(b for b in buttons if b.text() == "Later").click()
        self.assertIsNone(c.notice)
        c.open()
        self.assertEqual(c.dialog.notes.toPlainText(), release["notes"])
        self.assertTrue(c.dialog.download.isEnabled())
        c.dialog.channel.setCurrentIndex(1)
        self.assertFalse(c.dialog.download.isEnabled())
        c.check_now()
        self.assertFalse(c.dialog.offline.isEnabled())
        c.close()
        self.assertIsNone(c.parent(), "Closed controllers must not remain owned by main window")

    def test_channel_release_notes_and_opt_in_daily_notification(self):
        replies = []
        self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]
        c = self.make_controller()
        c.open()
        stable = dict(version="99.0.0", channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256="a" * 64, size=123, notes="Plain release notes", restart_required=True, data_upgrade=True)
        preview = dict(stable, version="100.0.0", channel="preview", notes="Preview notes")
        payload = json.dumps(dict(schema_version=1, releases=[stable, preview])).encode()
        c.check_now()
        replies[-1].deliver(payload)
        self.assertEqual(c.release["version"], "99.0.0")
        self.assertEqual(c.dialog.notes.toPlainText(), "Plain release notes")
        self.assertIn("data", c.status_text.lower())
        self.assertIn("restart", c.status_text.lower())
        self.assertIn("QGIS 3.28", c.status_text, "Explain the offered runtime requirement")
        self.assertIn(c.qgis_version, c.dialog.runtime.text())
        self.assertFalse(c.dialog.windowIcon().isNull(), "Use the product identity on update windows")
        c.dialog.channel.setCurrentIndex(1)
        self.assertIsNone(c.release)
        self.assertEqual(self.settings.value(updates.PREFIX + "channel"), "preview")
        c.check_now()
        replies[-1].deliver(payload)
        self.assertEqual(c.release["version"], "100.0.0")
        c.dialog.background.setChecked(True)
        self.assertTrue(self.settings.value(updates.PREFIX + "enabled", type=bool))
        self.assertTrue(c.daily_timer.isActive())
        c.dialog.reject()
        with patch.object(updates, "STARTUP_DELAY_MS", 1):
            c.start()
            spin(10)
        self.assertEqual(len(replies), 3)
        replies[-1].deliver(payload)
        self.assertFalse(c.dialog.isVisible(), "Background check must not pop a dialog")
        self.iface.messageBar().pushWidget.assert_called_once()
        c.daily_timer.timeout.emit()
        self.assertEqual(len(replies), 3, "No repeated checks within a day")
        c.open()
        c.dialog.background.setChecked(False)
        self.assertFalse(c.daily_timer.isActive())

    def test_default_offline_reuses_nonmodal_dialog(self):
        c = self.make_controller()
        c.start()
        c.start()
        c.open()
        dialog = c.dialog
        self.assertTrue(dialog.isVisible())
        self.assertFalse(dialog.isModal())
        self.assertEqual(dialog.parent(), self.window)
        self.assertFalse(dialog.background.isChecked())
        self.assertEqual(dialog.channel.currentData(), "stable")
        self.assertIn("Installed", dialog.installed.text())
        self.assertIn("IP", dialog.privacy.text())
        dialog.reject()
        c.open()
        self.assertIs(c.dialog, dialog)
        app.processEvents()
        self.network.get.assert_not_called()
        c.close()
        c.close()
        self.assertIsNone(c.dialog)
        self.assertFalse(c.daily_timer.isActive())


    def test_recheck_clears_stale_release_notes(self):
        self.network.get.side_effect = FakeReply
        c = self.make_controller()
        c.open()
        c.dialog.notes.setPlainText("Changes from a previous check")
        c.check_now()
        self.assertEqual(c.dialog.notes.toPlainText(), "")
        self.assertFalse(c.dialog.download.isEnabled())

    def package(self, version="99.0.0", experimental=False):
        path = self.root / "fixture.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("ag_tech_tooling/metadata.txt", "[general]\nversion=" + version + "\nqgisMinimumVersion=3.28\nexperimental=" + str(experimental).lower() + "\n")
            archive.writestr("ag_tech_tooling/__init__.py", "# synthetic fixture\n")
            archive.writestr("ag_tech_tooling/plugin.py", "# synthetic fixture\n")
        return path

    def test_install_rejects_unsafe_source_preview_dirty_and_editable(self):
        import pyplugin_installer
        from qgis.core import QgsVectorLayer
        c = self.make_controller()
        c.open()
        bad = self.root / "bad.zip"
        bad.write_bytes(b"not a ZIP")
        with patch.object(pyplugin_installer, "instance") as native:
            c.install_package(bad)
            self.assertIn("rejected", c.status_text)
            c.install_package(self.package())
            self.assertIn("profile", c.status_text)
            with patch.object(c, "_profile_plugin_dir", return_value=c.plugin_dir):
                c.install_package(self.package(experimental=True))
                self.assertIn("Preview", c.status_text)
                QgsProject.instance().setDirty(True)
                c.install_package(self.package())
                self.assertIn("Save", c.status_text)
                self.iface.actionSaveProject.assert_not_called()
                c.dialog.save.click()
                self.iface.actionSaveProject().trigger.assert_called_once()
                QgsProject.instance().setDirty(False)
                layer = QgsVectorLayer("Point?crs=EPSG:4326", "synthetic", "memory")
                QgsProject.instance().addMapLayer(layer)
                layer.startEditing()
                QgsProject.instance().setDirty(False)
                c.install_package(self.package())
                self.assertIn("editing", c.status_text)
                layer.rollBack()
                QgsProject.instance().removeMapLayer(layer.id())
                QgsProject.instance().setDirty(False)
            native.assert_not_called()
        self.assertFalse((self.root / "recovery").exists())


    def test_confirmed_native_handoff_snapshot_and_next_start_acknowledgement(self):
        import pyplugin_installer
        import pyplugin_installer.installer as native_module
        profile_plugins = self.root / "profile" / "python" / "plugins"
        with zipfile.ZipFile(self.package(version="1.0.0")) as archive:
            archive.extractall(profile_plugins)
        plugin = profile_plugins / "ag_tech_tooling"
        package = self.package()
        c = self.make_controller(plugin_dir=plugin)
        c.open()
        QgsProject.instance().setDirty(False)
        installer = Mock()
        with patch.object(native_module, "HOME_PLUGIN_PATH", str(profile_plugins)), patch.object(pyplugin_installer, "instance", return_value=installer), patch.object(updates.QMessageBox, "question", return_value=updates.QMessageBox.No) as confirm:
            c.install_package(package)
            installer.installFromZipFile.assert_not_called()
            self.assertFalse((self.root / "recovery").exists())
            self.assertIn("not authenticated", confirm.call_args.args[2])
            confirm.return_value = updates.QMessageBox.Yes
            installer.installFromZipFile.side_effect = lambda path: c.close() or True
            c.install_package(package)
            installer.installFromZipFile.assert_called_once()
            handed_path = Path(installer.installFromZipFile.call_args.args[0])
            self.assertTrue(handed_path.is_file(), "ZIP must survive native unload before extraction")
        pending_path = self.root / "recovery" / "pending.json"
        pending = json.loads(pending_path.read_text())
        self.assertEqual(pending["expected_version"], "99.0.0")
        backup = Path(pending["backup"])
        self.assertTrue((backup / "metadata.txt").is_file())
        self.assertEqual(updates.read_installed(backup)["version"], "1.0.0")
        self.assertTrue(c.closed)
        c = self.make_controller(plugin_dir=plugin)
        c.start()
        self.assertIn("not confirmed", c.status_text)
        c.close()
        metadata = plugin / "metadata.txt"
        metadata.write_text(metadata.read_text().replace("1.0.0", "99.0.0"))
        c = self.make_controller(plugin_dir=plugin)
        c.start()
        c.open()
        self.assertIn("99.0.0", c.status_text)
        self.assertIn(str(backup), c.status_text)
        self.assertEqual(json.loads(pending_path.read_text())["status"], "acknowledged")
        self.iface.messageBar().pushMessage.assert_called_once()
        self.network.get.assert_not_called()


    def test_current_incompatible_bad_catalogue_and_offline_cancel(self):
        replies = []
        self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]
        c = self.make_controller()
        c.open()
        release = dict(version=c.installed["version"], channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256="a" * 64, size=123, notes="Test", restart_required=True, data_upgrade=False)
        for item, expected in ((release, "current"), (dict(release, version="99.0.0", qgis_minimum="9.0"), "different QGIS")):
            c.check_now()
            replies[-1].deliver(json.dumps(dict(schema_version=1, releases=[item])).encode())
            self.assertIn(expected, c.status_text)
            self.assertFalse(c.dialog.download.isEnabled())
        c.check_now()
        replies[-1].deliver(b"invalid JSON")
        self.assertIn("invalid catalogue", c.status_text)
        with patch.object(updates.QFileDialog, "getOpenFileName", return_value=("", "ZIP")), patch.object(c, "install_package") as install:
            c.choose_zip()
            install.assert_not_called()
        c.close()

    def test_staging_is_cleaned_on_close_unless_native_handoff(self):
        c = self.make_controller()
        c.install_package(self.package())  # Refused source install, no modal.
        self.assertTrue(list(c.cache_root.rglob("*.zip")))
        c.close()
        self.assertFalse(list(c.cache_root.rglob("*.zip")))

    def test_download_headers_and_disk_close_failure_are_safe(self):
        replies = []
        self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]
        c = self.make_controller()
        c.release = dict(version="99.0.0", channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256="a" * 64, size=100, notes="Test", restart_required=True, data_upgrade=False)
        c.download()
        replies[-1].setHeader(QNetworkRequest.ContentLengthHeader, 101)
        replies[-1].metaDataChanged.emit()
        self.assertTrue(replies[-1].aborted)
        self.assertIn("too large", c.status_text)
        c.download()
        staged = c._download_path
        output = c._download_file
        failing = Mock(wraps=output)
        def failed_close():
            output.close()
            raise OSError("Synthetic disk close failure")
        failing.close.side_effect = failed_close
        c._download_file = failing
        c.cancel()
        self.assertIsNone(c._download_file)
        self.assertFalse(staged.exists())

    def test_open_mid_request_exposes_cancel_and_dismiss_cancels(self):
        replies = []
        self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]
        c = self.make_controller()
        c.check_now(background=True)
        c.open()
        self.assertTrue(c.dialog.cancel.isEnabled())
        self.assertFalse(c.dialog.check.isEnabled())
        c.dialog.reject()
        self.assertTrue(replies[-1].aborted)
        self.assertIsNone(c.reply)
        c.open()
        self.assertTrue(c.dialog.check.isEnabled())

    def test_unload_after_native_message_bar_dismissal(self):
        from qgis.gui import QgsMessageBar
        from qgis.PyQt import sip
        self.iface.messageBar.return_value = QgsMessageBar(self.window)
        c = self.make_controller()
        c._notify()
        sip.delete(c.notice)  # Native message bar can delete its own item.
        c.close()
        self.assertIsNone(c.notice)
        self.assertIsNone(c.dialog)

    @unittest.skipUnless(os.name == "nt", "Windows junction safety")
    def test_native_target_junction_is_refused_before_confirmation(self):
        import pyplugin_installer.installer as native_module
        plugins = self.root / "real-plugins"
        with zipfile.ZipFile(self.package(version="1.0.0")) as archive:
            archive.extractall(plugins)
        alias = self.root / "linked-plugins"
        process = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(plugins)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        try:
            c = self.make_controller(plugin_dir=plugins / "ag_tech_tooling")
            with patch.object(native_module, "HOME_PLUGIN_PATH", str(alias)), patch.object(updates.QMessageBox, "question", return_value=updates.QMessageBox.No) as question:
                c.install_package(self.package())
                question.assert_not_called()
                self.assertIn("profile", c.status_text)
        finally:
            os.rmdir(alias)  # Remove the junction itself, never its contents.

    def test_staging_precedes_confirmation_and_failed_backup_blocks_install(self):
        import pyplugin_installer
        import pyplugin_installer.installer as native_module
        plugins = self.root / "profile" / "python" / "plugins"
        with zipfile.ZipFile(self.package(version="1.0.0")) as archive:
            archive.extractall(plugins)
        c = self.make_controller(plugin_dir=plugins / "ag_tech_tooling")
        original = self.package()
        expected = original.read_bytes()
        captured = []
        def choose(*args):
            # The source changes while the user is reading the confirmation.
            original.write_bytes(b"changed after verification")
            captured.extend(c.cache_root.rglob("*.zip"))
            return updates.QMessageBox.Yes
        with patch.object(native_module, "HOME_PLUGIN_PATH", str(plugins)), patch.object(updates.QMessageBox, "question", side_effect=choose), patch.object(pyplugin_installer, "instance") as native, patch("ag_tech_tooling.update_catalog.snapshot_plugin", side_effect=OSError("synthetic backup failure")):
            QgsProject.instance().setDirty(False)
            c.install_package(original)
            self.assertTrue(captured, "Stage and verify immutable candidate before consent")
            self.assertEqual(captured[0].read_bytes(), expected)
            native.assert_not_called()
            self.assertIn("before installation", c.status_text)
            self.assertFalse(c.pending_path.exists())

    def test_package_download_trusted_redirect_stream_bounds_and_cancel(self):
        replies = []
        self.network.get.side_effect = lambda request: replies.append(FakeReply(request)) or replies[-1]
        c = self.make_controller()
        c.open()
        data = self.package().read_bytes()
        release = dict(version="99.0.0", channel="stable", qgis_minimum="3.28", qgis_maximum="", url="https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/v99/ag_tech_tooling-99.zip", sha256=hashlib.sha256(data).hexdigest(), size=len(data), notes="Notes", restart_required=True, data_upgrade=False)
        c.release = release
        c.download()
        self.assertEqual(replies[-1].url().toString(), release["url"])
        replies[-1].deliver(status=302, redirect="https://release-assets.githubusercontent.com/asset.zip?sig=synthetic")
        self.assertEqual(len(replies), 2)
        with patch.object(c, "install_package") as install:
            QTimer.singleShot(0, lambda: replies[-1].deliver(data))
            spin()
            path = Path(install.call_args.args[0])
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(install.call_args.args[1], release)
        c.release = release
        c.download()
        replies[-1].deliver(status=302, redirect="http://release-assets.githubusercontent.com/asset.zip")
        self.assertEqual(len(replies), 3)
        self.assertIn("redirect", c.status_text)
        c.download()
        current = replies[-1]
        staged = c._download_path
        current.deliver(data + b"extra")
        self.assertTrue(current.aborted)
        self.assertFalse(staged.exists())
        c.download()
        staged = c._download_path
        c.cancel()
        self.assertFalse(staged.exists())
        self.assertIsNone(c._download_file)
        with patch.object(updates.QFileDialog, "getOpenFileName", return_value=(str(self.package()), "ZIP")), patch.object(c, "install_package") as install:
            c.dialog.offline.click()
            self.assertEqual(Path(install.call_args.args[0]), self.root / "fixture.zip")
        self.assertIsNone(c.reply)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(UpdateTests))
    app.exitQgis()
    suite_home.cleanup()
    sys.exit(not result.wasSuccessful())
