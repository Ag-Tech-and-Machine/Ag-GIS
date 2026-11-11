"""Exercise real Windows property stores, reversible ownership and shortcut persistence."""

import os

import sys

from pathlib import Path

import subprocess

import tempfile

os.environ["QT_QPA_PLATFORM"] = "windows"

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

    pass  # QGIS not available, skip this test

except ImportError:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.PyQt.QtWidgets import QApplication, QMainWindow
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

from ag_tech_tooling.windows_taskbar import (PropertyStore, TaskbarIdentity, APP_ID, ICON, COMMAND, NAME,

                                            application_id, set_shortcut_identity)

app = QApplication([])

window = QMainWindow()

store = PropertyStore(hwnd=int(window.winId()))

initial = {APP_ID: "Original.App", ICON: "original.ico,0", NAME: "Original", COMMAND: '"original.exe"'}

for pid, text in initial.items():

    store.write(pid, text)

with tempfile.TemporaryDirectory(prefix="aggis-shell-test-") as temporary:

    root = Path(temporary)

    launcher = root / "Ag-GIS.exe"

    launcher.touch()

    icon = Path(__file__).resolve().parents[1] / "installer/Ag-GIS.ico"

    # The runtime asset must also be present in an extracted package.

    import ag_tech_tooling.windows_taskbar as module

    assert Path(module.__file__).with_name("app_icon.ico").read_bytes() == icon.read_bytes()

    identity = TaskbarIdentity(int(window.winId()), "shell_test", launcher=launcher)

    assert store.read(APP_ID) == application_id("shell_test")

    assert store.read(ICON).endswith("app_icon.ico,0")

    assert store.read(COMMAND).strip('"') == str(launcher)

    assert store.read(NAME) == "Ag-GIS"

    identity.close()

    identity.close()

    assert {pid: store.read(pid) for pid in initial} == initial

    identity = TaskbarIdentity(int(window.winId()), "shell_test", launcher=launcher)

    store.write(ICON, "later-owner.ico,0")

    identity.close()

    assert store.read(ICON) == "later-owner.ico,0"

    assert store.read(APP_ID) == initial[APP_ID]

    try:

        TaskbarIdentity(int(window.winId()), "shell_test", icon=root / "missing.ico")

        raise AssertionError("Missing icon accepted")

    except OSError:

        pass

    assert store.read(APP_ID) == initial[APP_ID]

    create = root / "create.ps1"

    create.write_text("$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $env:AGGIS_TEST_DIR 'Ag-GIS.lnk'))\n"

                      "$s.TargetPath=Join-Path $env:AGGIS_TEST_DIR 'Ag-GIS.exe'\n$s.Save()\n")

    environment = os.environ.copy()

    environment["AGGIS_TEST_DIR"] = str(root)

    environment.pop("PSModulePath", None)

    subprocess.run([str(Path(os.environ["WINDIR"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(create)], env=environment, check=True)

    shortcut = root / "Ag-GIS.lnk"

    set_shortcut_identity(shortcut, "shell_test")

    link = PropertyStore(shortcut=shortcut)

    assert link.read(APP_ID) == application_id("shell_test")

    link.close()

for pid in initial:

    store.write(pid, None)

store.close()

window.close()

print("Windows taskbar ID/icon/command, rollback, later-owner preservation and shortcut persistence passed")


