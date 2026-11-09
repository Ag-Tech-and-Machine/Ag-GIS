# SPDX-License-Identifier: GPL-2.0-or-later
"""Deliberate, asynchronous updates; native QGIS owns plugin replacement."""
from pathlib import Path
import json
import os
import tempfile
import shutil
import re
from urllib.parse import urlsplit

from qgis.core import Qgis, QgsApplication, QgsSettings, QgsNetworkAccessManager, QgsProject
from qgis.PyQt.QtCore import QObject, QTimer, Qt, QUrl, QDateTime, QStandardPaths
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QCheckBox, QComboBox, QPushButton, QProgressBar, QPlainTextEdit, QMessageBox, QFileDialog
from .update_catalog import read_installed, parse_catalog, FEED_URL, MAX_CATALOG_BYTES, MAX_PACKAGE_BYTES

NETWORK_TIMEOUT_MS = 30000
STARTUP_DELAY_MS = 1500

PREFIX = "AgTechTooling/updates/"


class UpdateActions(QObject):
    def __init__(self, iface, *, settings=None, network=None, plugin_dir=None,
                 cache_root=None, recovery_root=None):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.settings = settings if settings is not None else QgsSettings()
        self.network = network
        self.plugin_dir = Path(plugin_dir) if plugin_dir else Path(__file__).resolve().parent
        self.cache_root = Path(cache_root) if cache_root else Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation)) / "Ag-GIS" / "updates"
        self.recovery_root = Path(recovery_root) if recovery_root else Path(QgsApplication.qgisSettingsDirPath()) / "Ag-GIS" / "updates" / "recovery"
        self.pending_path = self.recovery_root / "pending.json"
        self._acknowledged = False
        self._handoff = False
        self._handoff_stage = None
        self._stages = set()
        self._download_file = None
        self._download_path = None
        self.installed = read_installed(self.plugin_dir)
        self.dialog = None
        self.reply = None
        self.closed = False
        self.daily_timer = QTimer(self)
        self.daily_timer.setInterval(24 * 60 * 60 * 1000)
        self.daily_timer.timeout.connect(self._check_due)
        self.startup_timer = QTimer(self)
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self._check_due)
        self.notice = None
        self.channel = self.settings.value(PREFIX + "channel", "stable")
        if self.channel not in ("stable", "preview"):
            self.channel = "stable"
        self.enabled = self.settings.value(PREFIX + "enabled", False, type=bool)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.timeout.connect(lambda: self.cancel("Update service unavailable: request timed out. Retry Check now."))
        self.release = None
        self.status_text = "Not checked. Choose Check now to contact GitHub, or use a downloaded ZIP."
        self.qgis_version = ".".join(str(Qgis.QGIS_VERSION_INT // n % 100) for n in (10000, 100, 1))

    def start(self):
        if self.closed:
            return
        if not self._acknowledged:
            self._acknowledged = True
            self._ack_pending()
        if self.enabled:
            self.daily_timer.start()
            if not self.startup_timer.isActive():
                self.startup_timer.start(STARTUP_DELAY_MS)

    def _check_due(self):
        if self.closed or not self.enabled:
            return
        last = self.settings.value(PREFIX + "last_check", 0, type=int)
        if QDateTime.currentSecsSinceEpoch() - last >= 86400:
            self.check_now(background=True)

    def _background_changed(self, enabled):
        self.enabled = enabled
        self.settings.setValue(PREFIX + "enabled", enabled)
        if enabled:
            self.daily_timer.start()
        else:
            self.daily_timer.stop()
            self.startup_timer.stop()
            if self.reply is not None and self._background:
                self.cancel()

    def _channel_changed(self):
        self.channel = self.dialog.channel.currentData()
        self.settings.setValue(PREFIX + "channel", self.channel)
        self.release = None
        self.dialog.notes.clear()
        self.dialog.download.setEnabled(False)
        self._status("Channel changed. Choose Check now. Preview is experimental; no automatic data migration.")

    def open(self, *args):
        if self.closed:
            return
        if self.dialog is None:
            self.dialog = QDialog(self.iface.mainWindow())
            self.dialog.setWindowTitle("Ag-GIS — Updates")
            from .branding import product_icon
            self.dialog.setWindowIcon(product_icon())
            self.dialog.setMinimumWidth(480)
            self.dialog.rejected.connect(self._dialog_dismissed)
            layout = QVBoxLayout(self.dialog)
            d = self.dialog
            d.installed = QLabel("Installed: " + self.installed["version"] +
                                (" (Preview)" if self.installed["experimental"] else " (Stable)"))
            d.runtime = QLabel("QGIS runtime: " + self.qgis_version + ". Runtime upgrades are separate.")
            d.privacy = QLabel("Checks contact GitHub, which receives your IP address and connection metadata. No farm data is sent.")
            d.privacy.setWordWrap(True)
            d.channel = QComboBox()
            d.channel.addItem("Stable", "stable")
            d.channel.addItem("Preview — experimental", "preview")
            d.channel.setCurrentIndex(d.channel.findData(self.channel))
            d.channel.currentIndexChanged.connect(self._channel_changed)
            d.background = QCheckBox("Check daily in the background (optional)")
            d.background.setChecked(self.enabled)
            d.background.toggled.connect(self._background_changed)
            d.status = QLabel(self.status_text)
            d.status.setTextFormat(Qt.PlainText)
            d.status.setWordWrap(True)
            d.notes = QPlainTextEdit()
            d.notes.setReadOnly(True)
            if self.release:
                d.notes.setPlainText(self.release["notes"])
            d.progress = QProgressBar()
            d.progress.hide()
            d.check = QPushButton("Check now / Retry")
            d.cancel = QPushButton("Cancel request")
            d.download = QPushButton("Download and install…")
            d.download.setEnabled(self.release is not None)
            d.download.clicked.connect(self.download)
            d.offline = QPushButton("Install offline ZIP…")
            d.offline.clicked.connect(self.choose_zip)
            d.save = QPushButton("Save project using QGIS")
            d.save.clicked.connect(lambda: self.iface.actionSaveProject().trigger())
            d.cancel.setEnabled(False)
            d.check.clicked.connect(self.check_now)
            d.cancel.clicked.connect(lambda: self.cancel())
            for widget in (d.installed, d.runtime, d.privacy, d.channel, d.background, d.status, d.notes, d.progress, d.check, d.cancel, d.download, d.offline, d.save):
                layout.addWidget(widget)
        self._busy(self.reply is not None)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def _dialog_dismissed(self):
        if self.reply is not None:
            self.cancel()

    def _status(self, text):
        self.status_text = text
        if self.dialog:
            self.dialog.status.setText(text)

    def _busy(self, busy):
        if self.dialog:
            self.dialog.check.setEnabled(not busy)
            self.dialog.download.setEnabled(not busy and self.release is not None)
            self.dialog.offline.setEnabled(not busy)
            self.dialog.channel.setEnabled(not busy)
            self.dialog.cancel.setEnabled(busy)
            self.dialog.progress.setVisible(busy)
            self.dialog.progress.setRange(0, 0)

    def check_now(self, *args, background=False):
        if self.closed or self.reply is not None:
            return
        self.release = None
        self._dismiss_notice()
        if self.dialog:
            self.dialog.notes.clear()
        self._buffer = bytearray()
        self._kind = "catalogue"
        self._limit = MAX_CATALOG_BYTES
        self._received = 0
        self._background = background
        if background:
            self.settings.setValue(PREFIX + "last_check", QDateTime.currentSecsSinceEpoch())
        self._status("Checking GitHub…")
        self._request(FEED_URL)

    def _request(self, url):
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.ManualRedirectPolicy)
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        manager = self.network if self.network is not None else QgsNetworkAccessManager.instance()
        self.reply = manager.get(request)
        reply = self.reply
        reply.readyRead.connect(lambda: self._read(reply))
        reply.finished.connect(lambda: self._finished(reply))
        reply.metaDataChanged.connect(lambda: self._headers(reply))
        reply.sslErrors.connect(lambda errors: self.cancel("Update service unavailable: TLS validation failed."))
        reply.setReadBufferSize(65536)
        self._busy(True)
        self.timeout.start(NETWORK_TIMEOUT_MS)

    def _headers(self, reply):
        if self.closed or reply is not self.reply:
            return
        length = reply.header(QNetworkRequest.ContentLengthHeader)
        if length is not None:
            try:
                if int(length) > self._limit or int(length) < 0:
                    self.cancel("Update service unavailable: " + self._kind + " too large.")
            except (TypeError, ValueError):
                self.cancel("Update service unavailable: invalid response length.")

    def _read(self, reply):
        if self.closed or reply is not self.reply:
            return
        # Do not stage response bodies from redirect/error pages.
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status is not None and status != 200:
            return
        try:
            while reply.bytesAvailable():
                remaining = self._limit - self._received
                chunk = bytes(reply.read(min(65536, remaining + 1)))
                if len(chunk) > remaining:
                    self.cancel("Update service unavailable: " + self._kind + " too large.")
                    return
                if not chunk:
                    break
                self._received += len(chunk)
                if self._kind == "package":
                    self._download_file.write(chunk)
                    if self.dialog:
                        self.dialog.progress.setRange(0, self._limit)
                        self.dialog.progress.setValue(self._received)
                else:
                    self._buffer.extend(chunk)
        except OSError:
            self.cancel("Could not stage update ZIP. Check available disk space, then retry.")

    def _detach(self):
        reply, self.reply = self.reply, None
        self.timeout.stop()
        self._busy(False)
        if reply:
            for signal in (reply.readyRead, reply.finished, reply.sslErrors, reply.metaDataChanged):
                try:
                    signal.disconnect()
                except (TypeError, RuntimeError):
                    pass
            reply.deleteLater()
        return reply

    def _finished(self, reply):
        if self.closed or reply is not self.reply:
            return
        self._read(reply)
        if reply is not self.reply:
            return
        error = reply.error() != QNetworkReply.NoError
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        redirect = reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
        source_url = reply.url().toString()
        self._detach()
        if redirect:
            if self._kind == "package" and self._redirects == 0 and self._safe_asset_redirect(source_url, redirect.toString()):
                self._redirects += 1
                self._request(redirect.toString())
                return
            self.cancel("Update service unavailable: unsafe " + self._kind + " redirect refused.")
            return
        if error or status != 200:
            self.cancel("Update service unavailable. Retry Check now or use an offline ZIP.")
            return
        if self._kind == "package":
            path = self._download_path
            try:
                self._download_file.close()
            except OSError:
                self.cancel("Could not finish staging update ZIP. Check disk space, then retry.")
                return
            self._download_file = None
            self.install_package(path, self.release)
            return
        try:
            result = parse_catalog(bytes(self._buffer), self.channel,
                                   self.installed["version"], self.qgis_version)
            self.release = result["release"]
            self._status({"empty": "Update information unavailable: no approved release is listed for this channel.",
                          "current": "The installed version is current for this channel.",
                          "incompatible": "A newer release needs a different QGIS version.",
                          "available": "A compatible update is available."}[result["status"]])
            if self.release:
                required = "QGIS " + self.release["qgis_minimum"] + (
                    "–" + self.release["qgis_maximum"] if self.release["qgis_maximum"] else " or newer")
                self._status("Version " + self.release["version"] + " available. Requires " + required + ". Restart required. " +
                             ("Data upgrade caution: no automatic migration; older versions may not read upgraded data. " if self.release["data_upgrade"] else "No automatic data migration. ") +
                             "Plugin recovery does not restore farm data.")
                if self.dialog:
                    self.dialog.notes.setPlainText(self.release["notes"])
                    self.dialog.download.setEnabled(True)
                if self._background:
                    self._notify()
        except (ValueError, KeyError, TypeError):
            self._status("Update service unavailable: invalid catalogue. Retry later or use an offline ZIP.")

    def cancel(self, message="Cancelled. No update installed."):
        reply = self._detach()
        if reply:
            reply.abort()
        if self._download_file is not None:
            try:
                self._download_file.close()
            except OSError:
                pass  # Best-effort cleanup must not interrupt plugin unload.
            self._download_file = None
            if self._download_path:
                shutil.rmtree(self._download_path.parent, ignore_errors=True)
        self._status(message)

    def choose_zip(self):
        path, _ = QFileDialog.getOpenFileName(self.iface.mainWindow(), "Choose an Ag-GIS plugin ZIP", "", "Plugin ZIP (*.zip)")
        if path and not self.closed:
            self.install_package(path)

    @staticmethod
    def _official_package_url(url):
        return bool(re.fullmatch(r"https://github\.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/[A-Za-z0-9][A-Za-z0-9_.-]{0,127}/ag_tech_tooling-[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.zip", url))

    @classmethod
    def _safe_asset_redirect(cls, source, target):
        try:
            parsed = urlsplit(target)
            return (cls._official_package_url(source) and parsed.scheme == "https" and
                    parsed.hostname == "release-assets.githubusercontent.com" and parsed.port in (None, 443)
                    and not parsed.username and not parsed.password and not parsed.fragment and bool(parsed.path))
        except ValueError:
            return False

    def download(self):
        if self.closed or self.reply is not None or not self.release:
            return
        if not self._official_package_url(self.release["url"]):
            self._status("Package rejected: untrusted download URL.")
            return
        self._kind = "package"
        self._limit = min(self.release["size"], MAX_PACKAGE_BYTES)
        self._received = 0
        self._redirects = 0
        self._background = False
        try:
            self._download_path = self._new_stage()
            self._download_file = self._download_path.open("xb")
            self._status("Downloading update ZIP… Cancel stops the download. Installation requires confirmation.")
            self._request(self.release["url"])
        except OSError:
            self.cancel("Could not stage update ZIP. Check available disk space, then retry.")

    def _profile_plugin_dir(self):
        # Match the exact target used by this QGIS build's native ZIP installer.
        from pyplugin_installer.installer import HOME_PLUGIN_PATH
        return Path(HOME_PLUGIN_PATH) / "ag_tech_tooling" if HOME_PLUGIN_PATH else None

    def _install_guard(self, metadata):
        target = self._profile_plugin_dir()
        if (target is None or self.plugin_dir.resolve() != target.resolve()
                or any(p.is_symlink() or getattr(p, "is_junction", lambda: False)()
                       for root in (self.plugin_dir, target) for p in (root, *root.parents))):
            self._status("Installation refused: this plugin is not loaded from the installed QGIS profile. Use a separately installed profile, not a source checkout.")
            return False
        if metadata["experimental"] and self.channel != "preview":
            self._status("Installation refused: explicitly select Preview before installing an experimental ZIP.")
            return False
        project = QgsProject.instance()
        if any(getattr(layer, "isEditable", lambda: False)() for layer in project.mapLayers().values()):
            self._status("Finish or cancel editing on every layer before updating, then save your project.")
            return False
        if project.isDirty():
            self._status("Save your project manually or choose Save project using QGIS, then try the update again.")
            return False
        return True

    def install_package(self, path, release=None):
        if self.closed:
            return
        from .update_catalog import verify_package
        try:
            # Consent applies to this private copy, never a mutable source ZIP.
            staged = self._stage_local(path)
            metadata = verify_package(staged, release, self.qgis_version)
        except (ValueError, OSError) as exc:
            self._status("Package rejected: " + str(exc))
            return
        if not self._install_guard(metadata):
            return
        warning = ("Offline ZIP: publisher not authenticated. Install only a package you trust.\n\n" if release is None else
                   "The package must match the SHA-256 in the GitHub catalogue; this is not a digital signature.\n\n")
        warning += ("Install Ag-GIS " + metadata["version"] + "?\nRestart required. " +
                    ("Preview is experimental. " if metadata["experimental"] else "") +
                    "No automatic data migration or rollback. Save and back up farm data separately. "
                    "A plugin-only recovery copy will be kept; an older plugin may not read newer farm data. "
                    "Recovery copies are never automatically deleted.")
        if QMessageBox.question(self.iface.mainWindow(), "Install Ag-GIS update?", warning,
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            self._status("Cancelled. No update installed.")
            return
        if self.closed or not self._install_guard(metadata):
            return
        from .update_catalog import snapshot_plugin
        try:
            # Verify again after the nested confirmation event loop.
            metadata = verify_package(staged, release, self.qgis_version)
            if not self._install_guard(metadata):
                return
            backup = snapshot_plugin(self.plugin_dir, self.recovery_root)
            self._write_pending(dict(expected_version=metadata["version"], previous_version=self.installed["version"],
                                     backup=str(backup), status="awaiting_restart"))
        except (ValueError, OSError) as exc:
            self._status("Update stopped before installation: " + str(exc))
            return
        self._status("Handing the verified ZIP to QGIS. Restart, then check the installed version. Plugin recovery: " + str(backup))
        # installFromZipFile unloads this controller BEFORE extracting. Retain
        # staging and do not touch dialog/reply state after calling it.
        self._handoff = True
        self._handoff_stage = staged.parent
        import pyplugin_installer
        try:
            pyplugin_installer.instance().installFromZipFile(str(staged))
        except Exception:
            # QGIS owns normal errors. If its handoff raises, recovery remains
            # durable and the next startup reports the unconfirmed update.
            if not self.closed:
                self._status("Native QGIS installation could not complete. Restart and review recovery: " + str(backup))

    def _new_stage(self):
        self.cache_root.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix="package-", dir=self.cache_root))
        self._stages.add(directory)
        return directory / "ag_tech_tooling.zip"

    def _stage_local(self, path):
        staged = self._new_stage()
        total = 0
        try:
            with Path(path).open("rb") as source, staged.open("xb") as target:
                while True:
                    block = source.read(1048576)
                    if not block:
                        break
                    total += len(block)
                    if total > MAX_PACKAGE_BYTES:
                        raise ValueError("Package too large")
                    target.write(block)
        except Exception:
            shutil.rmtree(staged.parent, ignore_errors=True)
            raise
        return staged

    def _write_pending(self, record):
        self.recovery_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.recovery_root,
                                         prefix="pending-", suffix=".tmp", delete=False) as target:
            json.dump(record, target)
            target.flush()
            os.fsync(target.fileno())
            temporary = target.name
        try:
            os.replace(temporary, self.pending_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _ack_pending(self):
        if not self.pending_path.exists():
            return
        try:
            with self.pending_path.open("rb") as source:
                payload = source.read(16385)
            if len(payload) > 16384:
                raise ValueError("Recovery record too large")
            record = json.loads(payload)
            if record["status"] == "acknowledged":
                return
            installed = read_installed(self.plugin_dir)
            if installed["version"] == record["expected_version"]:
                record["status"] = "acknowledged"
                self._write_pending(record)
                self._status("Installed version " + installed["version"] + " confirmed. Restart QGIS before continuing if not already restarted. Plugin-only recovery: " + record["backup"] + ". Farm data is not included; older versions may not read upgraded data.")
                self.iface.messageBar().pushMessage("Ag-GIS updates", self.status_text, level=Qgis.Info, duration=0)
            else:
                self._status("Update not confirmed: installed " + installed["version"] + "; expected " + record["expected_version"] + ". Plugin recovery: " + record["backup"] + ". No automatic rollback or farm-data recovery.")
        except (OSError, ValueError, TypeError, KeyError):
            self._status("Recovery record could not be read. No automatic rollback. Review plugin recovery copies in " + str(self.recovery_root))

    def _dismiss_notice(self):
        if self.notice is not None:
            try:
                self.iface.messageBar().popWidget(self.notice)
            except RuntimeError:
                pass  # The native message bar may already have deleted it.
            self.notice = None

    def _notify(self):
        self._dismiss_notice()
        bar = self.iface.messageBar()
        self.notice = bar.createMessage("Ag-GIS", "An update is available. Install only when you choose.")
        review = QPushButton("Review")
        later = QPushButton("Later")
        review.clicked.connect(self.open)
        later.clicked.connect(self._dismiss_notice)
        self.notice.layout().addWidget(review)
        self.notice.layout().addWidget(later)
        bar.pushWidget(self.notice, Qgis.Info)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.cancel()
        self.daily_timer.stop()
        self.startup_timer.stop()
        self._dismiss_notice()
        for timer in (self.daily_timer, self.startup_timer, self.timeout):
            timer.timeout.disconnect()
        for stage in self._stages:
            if stage != self._handoff_stage:
                shutil.rmtree(stage, ignore_errors=True)
        self._stages.clear()
        if self.dialog:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None
        self.setParent(None)


def run_updates(iface):
    """Compatibility wrapper: retain one nonmodal controller per interface."""
    controller = getattr(iface, "_aggis_updates_controller", None)
    if controller is None or controller.closed:
        controller = UpdateActions(iface)
        iface._aggis_updates_controller = controller
    controller.open()
