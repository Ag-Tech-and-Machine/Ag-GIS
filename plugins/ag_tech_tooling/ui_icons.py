# SPDX-License-Identifier: GPL-2.0-or-later
"""QGIS theme icons with a bundled fallback; no external resource dependency."""
from pathlib import Path
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialogButtonBox, QLineEdit
from qgis.core import QgsApplication

NAMES = {
    "import": "mActionAddOgrLayer.svg", "folder": "mIconFolder.svg",
    "search": "mActionSearch.svg", "notice": "mIconWarning.svg",
    "organisation": "mIconDbSchema.svg", "client": "mIconUser.svg",
    "farm": "mIconHome.svg", "field": "mActionAddPolygon.svg",
    "whole": "mActionZoomFullExtent.svg", "season": "mTemporal.svg",
    "crop": "mIconFieldText.svg", "guidance": "mActionAddPolyline.svg",
    "terrain": "mIconRaster.svg", "asset": "mActionAddPoint.svg",
    "plan": "mActionNewPrintLayout.svg", "job": "mIconTaskComplete.svg",
    "result": "mActionShowAllLayers.svg", "add": "symbologyAdd.svg",
    "edit": "mActionToggleEditing.svg", "open": "mActionFileOpen.svg",
    "ok": "mActionSaveEdits.svg", "cancel": "mActionCancelAllEdits.svg",
    "crs": "mIconProjectionEnabled.svg", "name": "mActionTextAnnotation.svg",
}


def icon(kind):
    bundled = Path(__file__).with_name(f"agtech_{kind}.svg")
    if bundled.is_file():
        return QIcon(str(bundled))
    result = QgsApplication.getThemeIcon("/" + NAMES.get(kind, "mIconFolder.svg"))
    return result if not result.isNull() else QIcon(str(Path(__file__).with_name("icon.svg")))


def decorate_input(control, kind):
    control.addAction(icon(kind), QLineEdit.LeadingPosition)


def decorate_buttons(buttons):
    for button in buttons.buttons():
        role = buttons.buttonRole(button)
        button.setIcon(icon("cancel" if role in (QDialogButtonBox.RejectRole, QDialogButtonBox.NoRole) else "ok"))
