# SPDX-License-Identifier: GPL-2.0-or-later
"""Run updates through QGIS's own repository and ZIP installer."""
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices

RELEASES_URL = "https://github.com/JamRov/Ag-GIS/releases/latest"


def run_updates(iface):
    """Keep installation, compatibility checks and reload ownership with QGIS."""
    import pyplugin_installer
    dialog = QMessageBox(iface.mainWindow())
    dialog.setWindowTitle("Ag-GIS updates")
    dialog.setText(
        "Save your map before updating.\n\n"
        "Open the latest GitHub release in your browser, sign in with an account "
        "that has access to JamRov/Ag-GIS, and download ag_tech_tooling-<version>.zip. "
        "Then return here and choose Install downloaded ZIP. QGIS checks and installs the package.\n\n"
        "A missing page can mean no release has been published or your account lacks access. "
        "Restart QGIS after updating. Your farm files remain in their current location.")
    download = dialog.addButton("Open latest release", QMessageBox.ActionRole)
    local = dialog.addButton("Install downloaded ZIP…", QMessageBox.ActionRole)
    dialog.addButton(QMessageBox.Cancel)
    dialog.exec()
    if dialog.clickedButton() is download:
        if not QDesktopServices.openUrl(QUrl(RELEASES_URL)):
            QMessageBox.warning(iface.mainWindow(), "Ag-GIS updates", "Could not open the browser. Visit " + RELEASES_URL)
    elif dialog.clickedButton() is local:
        pyplugin_installer.instance().showPluginManagerWhenReady(5)
