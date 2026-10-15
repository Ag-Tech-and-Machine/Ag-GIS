"""Check native update delegation and cancellation without contacting a live feed."""
import os
from pathlib import Path
import sys
from unittest.mock import Mock, patch
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QMainWindow
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import QTimer
from ag_tech_tooling.updates import run_updates
import pyplugin_installer

app = QgsApplication([], False)
app.initQgis()
window = QMainWindow()
iface = Mock()
iface.mainWindow.return_value = window
for choice in ("Open latest release", "Install downloaded ZIP…", "Cancel"):
    installer = Mock()
    def choose():
        dialog = QApplication.activeModalWidget()
        next(button for button in dialog.buttons() if button.text().replace("&", "") == choice).click()
    with patch.object(pyplugin_installer, "instance", return_value=installer), patch(
            "ag_tech_tooling.updates.QDesktopServices.openUrl", return_value=True) as browser:
        QTimer.singleShot(0, choose)
        run_updates(iface)
        if choice == "Open latest release":
            assert browser.call_args.args[0].toString() == "https://github.com/JamRov/Ag-GIS/releases/latest"
            installer.showPluginManagerWhenReady.assert_not_called()
        elif choice == "Install downloaded ZIP…":
            installer.showPluginManagerWhenReady.assert_called_once_with(5)
            browser.assert_not_called()
        else:
            browser.assert_not_called()
            installer.showPluginManagerWhenReady.assert_not_called()
        installer.installPlugin.assert_not_called()
window.close()
app.exitQgis()
print("Private GitHub browser, native ZIP update, cancellation and no automatic installation passed")
