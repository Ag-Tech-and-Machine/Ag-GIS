# SPDX-License-Identifier: GPL-2.0-or-later
"""Owned product surfaces; never replace installed QGIS resources."""
from pathlib import Path
import os
import re
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout
from qgis.PyQt.QtSvg import QSvgWidget


def product_icon():
    return QIcon(str(Path(__file__).with_name("icon.svg")))


PRODUCT_NAME = "Ag-GIS"
PRODUCT_LINE = "Built on open source tools"


def brand_dialog(dialog):
    """Give owned workflow windows the same product identity, preserving task labels."""
    title = dialog.windowTitle()
    if PRODUCT_NAME not in title:
        dialog.setWindowTitle(PRODUCT_NAME + " — " + title)
    dialog.setWindowIcon(product_icon())


class Branding:
    def __init__(self, window):
        self.window = window
        self.previous_icon = QIcon(window.windowIcon())
        self.icon = product_icon()
        self.dialog = None
        window.setWindowIcon(self.icon)
        self.taskbar = None
        self.taskbar_error = None
        from qgis.PyQt.QtWidgets import QApplication
        if os.name == "nt" and QApplication.platformName() == "windows":
            from qgis.core import QgsApplication
            from .windows_taskbar import TaskbarIdentity
            profile = Path(QgsApplication.qgisSettingsDirPath()).name
            try:
                self.taskbar = TaskbarIdentity(int(window.winId()), profile)
            except (OSError, ValueError) as error:
                self.taskbar_error = str(error)
                from qgis.core import QgsMessageLog
                QgsMessageLog.logMessage("Could not apply Windows taskbar identity: " + str(error), "Ag-GIS")
        self.native_title = window.windowTitle()
        self.product_title = None
        self.setting_title = False
        window.windowTitleChanged.connect(self._title_changed)
        self._title_changed(self.native_title)

    def _title_changed(self, title):
        if self.setting_title:
            return
        self.native_title = title
        # Only remove a recognised application suffix, never QGIS in a farm name.
        task = re.sub(r"\s+[—–-]\s+QGIS(?:\s+\d[\w. -]*)?$", "", title)
        if re.fullmatch(r"QGIS(?:\s+\d[\w. -]*)?", task):
            task = ""
        self.product_title = "Ag-GIS" + (" — " + task if task else "")
        self.setting_title = True
        try:
            self.window.setWindowTitle(self.product_title)
        finally:
            self.setting_title = False

    def about(self):
        if self.dialog is None:
            self.dialog = QDialog(self.window)
            self.dialog.setWindowTitle("About Ag-GIS")
            self.dialog.setWindowIcon(self.icon)
            layout = QVBoxLayout(self.dialog)
            logo = QSvgWidget(str(Path(__file__).with_name("brand_lockup.svg")))
            logo.setFixedSize(330, 96)
            layout.addWidget(logo)
            text = QLabel("Simple farming workflows. Your maps and work stay local."
                          "<br><br>Built on open source tools."
                          "<br>Ag-GIS source: GPL-2.0-or-later. See the bundled LICENSE."
                          "<br>Third-party tools retain their own credits and licences.")
            text.setWordWrap(True)
            text.setOpenExternalLinks(True)
            text.setTextFormat(Qt.RichText)
            layout.addWidget(text)
            buttons = QDialogButtonBox(QDialogButtonBox.Close)
            buttons.rejected.connect(self.dialog.reject)
            layout.addWidget(buttons)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def close(self):
        if self.taskbar is not None:
            self.taskbar.close()
            self.taskbar = None
        self.window.windowTitleChanged.disconnect(self._title_changed)
        if self.window.windowTitle() == self.product_title:
            self.window.setWindowTitle(self.native_title)
        if self.dialog is not None:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None
        # Respect a later icon change made by QGIS or another plugin.
        if self.window.windowIcon().cacheKey() == self.icon.cacheKey():
            self.window.setWindowIcon(self.previous_icon)
