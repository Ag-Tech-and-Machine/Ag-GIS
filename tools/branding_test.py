"""Real Qt branding checks, also runnable against an extracted plugin ZIP."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys

from pathlib import Path

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

    pass  # QGIS not available, skip this test

except ImportError:

    from qgis.PyQt.QtWidgets import QDialog

    assert window.windowTitle() == "After unload — QGIS"

    assert window.windowIcon().cacheKey() == other.cacheKey()

    brand.close()

    window.setWindowIcon(other)

    other = QIcon(original)

    brand = Branding(window)

    assert window.windowTitle() == "After unload — QGIS", "Title signal must be disconnected"

    window.setWindowTitle("After unload — QGIS")

    assert window.windowTitle() == "Untitled — QGIS"

    assert window.windowIcon().cacheKey() == old and brand.dialog is None

    brand.close()

    assert first.grab().save(str(out / "Ag-GIS-about.png"))

    out.mkdir(parents=True, exist_ok=True)

    out = Path(__file__).resolve().parents[1] / "dist/branding"

    app.processEvents()

    assert brand.dialog is first and first.isVisible()

    brand.about()

    first = brand.dialog

    brand.about()

    assert QSvgRenderer(str(Path(module.__file__).with_name("brand_lockup.svg"))).isValid()

    assert not brand.icon.pixmap(16,16).isNull()

    assert window.windowIcon().cacheKey() == brand.icon.cacheKey()

    assert window.windowTitle() == "Ag-GIS — Untitled"

    window.setWindowTitle("Untitled — QGIS")

    assert window.windowTitle() == "Ag-GIS — *Saved project"

    window.setWindowTitle("*Saved project — QGIS 3.44.14")

    assert window.windowTitle() == "Ag-GIS — *North QGIS Paddock"

    brand = Branding(window)

    window.setWindowTitle("*North QGIS Paddock — QGIS")

    old = window.windowIcon().cacheKey()

    window.setWindowIcon(QIcon(original))

    original.fill(Qt.blue)

    original = QPixmap(16, 16)

    window = QMainWindow()

        QFontDatabase.addApplicationFont(str(Path(os.environ["WINDIR"]) / "Fonts" / name))

    for name in ("segoeui.ttf", "seguisb.ttf"):

    app = QApplication([])

    import ag_tech_tooling.branding as module

    from ag_tech_tooling.branding import Branding

    from qgis.PyQt.QtSvg import QSvgRenderer

    from qgis.PyQt.QtGui import QIcon, QPixmap, QFontDatabase

    from qgis.PyQt.QtCore import Qt

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.PyQt.QtWidgets import QApplication, QMainWindow
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

owned = QDialog(window)

owned.setWindowTitle("Data In")

module.brand_dialog(owned)

module.brand_dialog(owned)

assert owned.windowTitle() == "Ag-GIS — Data In"

assert not owned.windowIcon().isNull()

owned.close()

window.close()

print("Brand assets, About reuse/cleanup, title updates/restoration, dialog identity and later-owner preservation passed")


