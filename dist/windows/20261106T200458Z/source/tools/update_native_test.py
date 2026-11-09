"""Offline integration: real QGIS ZIP replacement, plugin lifecycle and recovery.

Run with QGIS's python-qgis-ltr.bat. Only a unique Hermes scratch directory is
written. AGTECH_TEST_PLUGIN_ROOT selects the packaged/extracted plugins parent.
The next-version ZIP is an explicit test fixture, never a release: metadata alone
changes; all shipped Python/runtime bytes remain the selected package's bytes.
GUI adaptation reuses only the AST Interface class from smoke_test (never imports
or executes its application). Native install/extraction/lifecycle are not mocked.
"""
import ast
from collections import Counter
from contextlib import ExitStack
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[1]
PLUGIN_ID = "ag_tech_tooling"
SOURCE = Path(os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(REPO / "plugins"))) / PLUGIN_ID


def runtime_files(directory):
    """Match the flat shipping format; omit generated Python caches."""
    return {p.name: p.read_bytes() for p in directory.iterdir()
            if p.is_file() and (p.suffix in {".py", ".txt", ".svg", ".ico"} or p.name == "LICENSE")}


def hashes(files):
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def write_zip(path, files):
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(PLUGIN_ID + "/" + name, data)
    return path


def interface_class():
    from qgis.PyQt import QtWidgets
    from qgis.PyQt.QtCore import Qt
    namespace = {name: getattr(QtWidgets, name) for name in
                 ("QMainWindow", "QDockWidget", "QToolBar", "QLabel", "QStackedWidget", "QWidget", "QAction", "QToolButton")}
    namespace["Qt"] = Qt
    smoke = REPO / "tools" / "smoke_test.py"
    tree = ast.parse(smoke.read_text(encoding="utf-8"), filename=str(smoke))
    definition = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Interface")
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(smoke), "exec"), namespace)
    return namespace["Interface"]


def main():
    # QGIS's Windows bootstrap can reset TMPDIR to the system Temp directory.
    # Always choose Hermes scratch explicitly, then redirect all three variables.
    scratch = Path.home() / "AppData/Local/hermes/cache/scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    home = Path(tempfile.mkdtemp(prefix="aggis-native-update-", dir=scratch)).resolve()
    print("Native update isolated evidence: " + str(home), flush=True)
    for name in ("TEMP", "TMP", "TMPDIR"):
        os.environ[name] = str(home)
    from qgis.core import QgsApplication, QgsSettings, QgsProject
    from qgis.PyQt.QtCore import QSettings, QObject
    from qgis.PyQt.QtNetwork import QNetworkAccessManager

    settings_root = home / "settings"
    settings_root.mkdir()
    QSettings.setDefaultFormat(QSettings.IniFormat)
    for scope in (QSettings.UserScope, QSettings.SystemScope):
        for fmt in (QSettings.IniFormat, QSettings.NativeFormat):
            QSettings.setPath(fmt, scope, str(settings_root))
            # QgsSettings delegates to QSettings in QGIS 3.44 (no setPath API).
            # Both formats/scopes are configured before creating QgsApplication.
    profile = home / "profile"
    profile.mkdir()
    # QGIS 3.44's own qgis.testing.start_app uses this variable: initQgis()
    # lazily creates the profile and otherwise ignores the constructor path.
    os.environ["QGIS_CUSTOM_CONFIG_PATH"] = str(profile)
    app = QgsApplication([], False, str(profile))
    # Do not change application identity after creation: QGIS then recomputes
    # its profile from the new identity instead of retaining customConfigPath.
    app.initQgis()
    assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(home), QgsApplication.qgisSettingsDirPath()
    assert Path(QgsSettings().fileName()).resolve().is_relative_to(home), QgsSettings().fileName()
    assert Path(QSettings().fileName()).resolve().is_relative_to(home), QSettings().fileName()

    import qgis.utils as utils
    from qgis.core import QgsSettingsTree, QgsSettingsEntryString, QgsSettingsEntryBool, QgsSettingsEntryStringList
    # These settings are normally registered by QGIS Desktop's plugin manager,
    # absent from a standalone QgsApplication. Use real scratch-backed entries.
    manager_node = QgsSettingsTree.treeRoot().createChildNode("plugin-manager")
    manager_settings = [
        QgsSettingsEntryString("last-zip-directory", manager_node, ""),
        QgsSettingsEntryBool("allow-experimental", manager_node, True),
        QgsSettingsEntryBool("allow-deprecated", manager_node, False),
        QgsSettingsEntryStringList("seen-plugins", manager_node, []),
    ]
    import pyplugin_installer
    import pyplugin_installer.installer as native
    import pyplugin_installer.installer_data as native_data

    files = runtime_files(SOURCE)
    if "USER_GUIDE.txt" not in files:
        files["USER_GUIDE.txt"] = (REPO / "docs" / "USER_GUIDE.md").read_bytes()
    assert {"plugin.py", "updates.py", "metadata.txt", "__init__.py"} <= files.keys()
    metadata = files["metadata.txt"].decode("utf-8")
    old_version = re.search(r"(?m)^version\s*=\s*(\S+)", metadata).group(1)
    parts = old_version.split(".")
    assert len(parts) == 3 and all(part.isdigit() for part in parts), old_version
    new_version = ".".join(parts[:2] + [str(int(parts[2]) + 1)])
    candidate = dict(files)
    candidate["metadata.txt"] = re.sub(r"(?m)^(version\s*=\s*)\S+", lambda m: m[1] + new_version, metadata).encode("utf-8")
    assert {name for name in files if files[name] != candidate[name]} == {"metadata.txt"}
    next_zip = write_zip(home / "synthetic-next-version.zip", candidate)
    plugins_path = Path(QgsApplication.qgisSettingsDirPath()) / "python" / "plugins"
    prior_zip = write_zip(home / "initial-package.zip", files)
    with ZipFile(prior_zip) as archive:
        archive.extractall(plugins_path)
    installed_dir = plugins_path / PLUGIN_ID
    old_only = installed_dir / "native_test_old_only.py"
    old_only.write_text('VALUE = "prior installation only"\n', encoding="utf-8")
    before = runtime_files(installed_dir)
    data_dir = home / "separate-farm-data"
    data_dir.mkdir()
    sentinel = data_dir / "saved-farm-record.bin"
    sentinel.write_bytes(b"synthetic local farm data\x00not plugin data\xff")
    data_before = {p.relative_to(data_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in data_dir.rglob("*") if p.is_file()}
    # Binary sentinel deliberately falls outside the plugin recovery allowlist.
    sentinel_hash = hashlib.sha256(sentinel.read_bytes()).hexdigest()
    iface = interface_class()()
    iface.pluginManagerInterface = lambda: iface
    errors = []
    network_attempts = []
    installer = native.QgsPluginInstaller.__new__(native.QgsPluginInstaller)
    QObject.__init__(installer)
    # No repository constructor or catalogue requests. Native dependency handling
    # remains real; this package declares no dependencies. Only GUI export adapts.
    installer.exportPluginsToManager = lambda: None
    sys.path.insert(0, str(plugins_path))
    utils.plugin_paths[:] = [str(plugins_path)]
    utils.iface = iface
    native.iface = iface
    native_data.iface = iface
    native.HOME_PLUGIN_PATH = str(plugins_path)
    utils.HOME_PLUGIN_PATH = str(plugins_path)
    native_data.HOME_PLUGIN_PATH = str(plugins_path)
    QgsSettings().setValue("/PythonPlugins/" + PLUGIN_ID, True)

    def forbidden_network(*args, **kwargs):
        network_attempts.append("network request")
        raise AssertionError("Native integration must remain offline")

    def fail_exception(*args, **kwargs):
        errors.append((str(args), str(kwargs)))
        raise AssertionError("QGIS plugin lifecycle exception: " + repr(args))

    report = {"source": str(SOURCE.resolve()), "prior_version": old_version,
              "fixture_version": new_version, "profile": str(plugins_path), "phases": []}
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(pyplugin_installer, "instance", return_value=installer))
            stack.enter_context(patch.object(native.QMessageBox, "question", return_value=native.QMessageBox.Yes))
            stack.enter_context(patch.object(utils, "showException", side_effect=fail_exception))
            stack.enter_context(patch.object(socket.socket, "connect", side_effect=forbidden_network))
            for method in ("get", "post", "put", "deleteResource", "sendCustomRequest", "head"):
                stack.enter_context(patch.object(QNetworkAccessManager, method, side_effect=forbidden_network))
            utils.updateAvailablePlugins()
            assert utils.loadPlugin(PLUGIN_ID)
            assert utils.startPlugin(PLUGIN_ID), errors
            prior_plugin = utils.plugins[PLUGIN_ID]
            old_module = importlib.import_module(PLUGIN_ID + ".plugin")
            old_extra_module = __import__(PLUGIN_ID + ".native_test_old_only", fromlist=["VALUE"])
            assert PLUGIN_ID + ".native_test_old_only" in utils._plugin_modules[PLUGIN_ID]
            assert Path(old_module.__file__).resolve().parent == installed_dir.resolve()
            prior_plugin.updates.cache_root = home / "cache"
            # Defaults must resolve into the custom profile, not a normal profile.
            assert prior_plugin.updates.recovery_root.resolve().is_relative_to(home)
            prior_plugin.updates.channel = "preview"
            prior_plugin.updates.settings.setValue("AgTechTooling/updates/channel", "preview")
            QgsProject.instance().setDirty(False)

            def perform(package, expected_version, expected_files, label):
                source_plugin = utils.plugins[PLUGIN_ID]
                controller = source_plugin.updates
                controller.cache_root = home / "cache"
                controller.channel = "preview"  # deliberate opt-in for experimental fixtures/recovery
                controller.open()
                source_module = sys.modules[PLUGIN_ID + ".plugin"]
                calls, returns, extraction = [], [], []
                codes = {native.QgsPluginInstaller.installFromZipFile.__code__: "installFromZipFile",
                         native.unzip.__code__: "unzip", native.removeDir.__code__: "removeDir",
                         utils.unloadPlugin.__code__: "unloadPlugin", utils.loadPlugin.__code__: "loadPlugin",
                         utils.startPlugin.__code__: "startPlugin"}
                handed = []
                handoff_status = []

                def trace(frame, event, value):
                    name = codes.get(frame.f_code)
                    if name is None:
                        return
                    if event == "call":
                        calls.append(name)
                        if name == "installFromZipFile":
                            handed.append(Path(frame.f_locals["filePath"]))
                            handoff_status.append(controller.status_text)
                        if name == "unzip":
                            extraction.append(dict(controller_closed=controller.closed,
                                                   zip_exists=bool(handed and handed[0].is_file()),
                                                   old_inactive=not utils.isPluginLoaded(PLUGIN_ID)))
                    elif event == "return":
                        returns.append((name, value if isinstance(value, bool) else None))

                native_errors = []

                def exception_trace(frame, event, value):
                    if frame.f_code is native.QgsPluginInstaller.installFromZipFile.__code__:
                        if event == "exception":
                            native_errors.append(repr(value[1]))
                        return exception_trace
                    return None

                previous_profiler = sys.getprofile()
                previous_trace = sys.gettrace()
                sys.setprofile(trace)
                sys.settrace(exception_trace)
                try:
                    controller.install_package(package)
                finally:
                    sys.setprofile(previous_profiler)
                    sys.settrace(previous_trace)
                assert handed, controller.status_text
                assert ("installFromZipFile", True) in returns, (calls, returns, native_errors, controller.status_text)
                assert controller.closed and source_plugin.updates is None
                assert handed[0].is_file(), "Source controller unload deleted the handed ZIP"
                assert hashlib.sha256(handed[0].read_bytes()).digest() == hashlib.sha256(package.read_bytes()).digest()
                assert extraction == [dict(controller_closed=True, zip_exists=True, old_inactive=True)] * 2, extraction
                counts = Counter(calls)
                assert counts["unzip"] == 2 and counts["removeDir"] == 1, counts
                assert counts["unloadPlugin"] >= 1 and counts["loadPlugin"] >= 1 and counts["startPlugin"] == 1, counts
                assert handoff_status and "Restart" in handoff_status[0]
                running = utils.plugins[PLUGIN_ID]
                assert utils.isPluginLoaded(PLUGIN_ID) and running is not source_plugin
                loaded_module = sys.modules[PLUGIN_ID + ".plugin"]
                assert loaded_module is not source_module, "Native lifecycle reused old Python code"
                assert Path(loaded_module.__file__).resolve().parent == installed_dir.resolve()
                assert loaded_module.AgTechTooling is type(running)
                assert hashes(runtime_files(installed_dir)) == hashes(expected_files), "Native replacement left stale or changed files"
                assert running.updates.installed["version"] == expected_version
                assert utils.pluginMetadata(PLUGIN_ID, "version") == expected_version
                assert running.updates is not controller and not running.updates.closed
                pending = json.loads(controller.pending_path.read_text(encoding="utf-8"))
                assert pending["status"] == "acknowledged", pending
                assert pending["expected_version"] == expected_version
                assert "confirmed" in running.updates.status_text and "Restart QGIS" in running.updates.status_text
                assert any("confirmed" in str(message) and "Restart QGIS" in str(message) for message in iface.messages)
                backup = Path(pending["backup"])
                assert backup.resolve().is_relative_to(home)
                assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == sentinel_hash
                assert not (backup / sentinel.name).exists()
                assert not errors and not network_attempts
                phase = dict(label=label, version=expected_version, native_calls=dict(counts),
                             handoff_zip=str(handed[0]), snapshot=str(backup), pending=pending,
                             restart_message=running.updates.status_text)
                report["phases"].append(phase)
                print(label + ": native replacement/load/start, retained ZIP, confirmed pending and restart instruction passed", flush=True)
                return backup

            snapshot = perform(next_zip, new_version, candidate, "UPDATE")
            assert not old_only.exists() and PLUGIN_ID + ".native_test_old_only" not in sys.modules
            assert hashes(runtime_files(snapshot)) == hashes(before), "Recovery snapshot differs from prior runtime files"
            assert old_extra_module is not None
            recovery_zip = write_zip(home / "explicit-prior-snapshot-recovery.zip", runtime_files(snapshot))
            recovery_snapshot = perform(recovery_zip, old_version, before, "EXPLICIT RECOVERY")
            assert hashes(runtime_files(recovery_snapshot)) == hashes(candidate)
            assert hashes(runtime_files(snapshot)) == hashes(before), "Recovery altered its input snapshot"
            assert {p.relative_to(data_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in data_dir.rglob("*") if p.is_file()} == data_before
            assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == sentinel_hash
            assert utils.unloadPlugin(PLUGIN_ID)
            assert not iface.menu_actions and not iface.toolbar_actions
            assert not utils.isPluginLoaded(PLUGIN_ID)
            assert not errors and not network_attempts
            report["result"] = "passed"
            report["farm_data_sha256"] = sentinel_hash
            (home / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            print("PASS: actual native installer update and explicit snapshot recovery; isolated settings/profile; no network; separate data unchanged", flush=True)
            print("Evidence JSON: " + str(home / "result.json"), flush=True)
    finally:
        if utils.isPluginLoaded(PLUGIN_ID):
            utils.unloadPlugin(PLUGIN_ID)
        iface.window.close()
        QgsProject.instance().clear()
        app.processEvents()
        app.exitQgis()


if __name__ == "__main__":
    main()
