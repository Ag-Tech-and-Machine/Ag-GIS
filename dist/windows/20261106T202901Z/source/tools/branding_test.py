"""Real Qt branding checks, also runnable against an extracted plugin ZIP."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
from pathlib import Path
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.PyQt.QtWidgets import QApplication, QMainWindow
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QPixmap, QFontDatabase
from qgis.PyQt.QtSvg import QSvgRenderer
from ag_tech_tooling.branding import Branding
import ag_tech_tooling.branding as module
app = QApplication([])
for name in ("segoeui.ttf", "seguisb.ttf"):
    QFontDatabase.addApplicationFont(str(Path(os.environ["WINDIR"]) / "Fonts" / name))
window = QMainWindow()
original = QPixmap(16, 16)
original.fill(Qt.blue)
window.setWindowIcon(QIcon(original))
old = window.windowIcon().cacheKey()
window.setWindowTitle("*North QGIS Paddock — QGIS")
brand = Branding(window)
assert window.windowTitle() == "Ag-GIS — *North QGIS Paddock"
window.setWindowTitle("*Saved project — QGIS 3.44.14")
assert window.windowTitle() == "Ag-GIS — *Saved project"
window.setWindowTitle("Untitled — QGIS")
assert window.windowTitle() == "Ag-GIS — Untitled"
assert window.windowIcon().cacheKey() == brand.icon.cacheKey()
assert not brand.icon.pixmap(16,16).isNull()
assert QSvgRenderer(str(Path(module.__file__).with_name("brand_lockup.svg"))).isValid()
brand.about()
first = brand.dialog
brand.about()
assert brand.dialog is first and first.isVisible()
app.processEvents()
out = Path(__file__).resolve().parents[1] / "dist/branding"
out.mkdir(parents=True, exist_ok=True)
assert first.grab().save(str(out / "Ag-GIS-about.png"))
brand.close()
assert window.windowIcon().cacheKey() == old and brand.dialog is None
assert window.windowTitle() == "Untitled — QGIS"
window.setWindowTitle("After unload — QGIS")
assert window.windowTitle() == "After unload — QGIS", "Title signal must be disconnected"
brand = Branding(window)
other = QIcon(original)
window.setWindowIcon(other)
brand.close()
assert window.windowIcon().cacheKey() == other.cacheKey()
assert window.windowTitle() == "After unload — QGIS"
from qgis.PyQt.QtWidgets import QDialog
owned = QDialog(window)
owned.setWindowTitle("Data In")
module.brand_dialog(owned)
module.brand_dialog(owned)
assert owned.windowTitle() == "Ag-GIS — Data In"
assert not owned.windowIcon().isNull()
owned.close()
window.close()
print("Brand assets, About reuse/cleanup, title updates/restoration, dialog identity and later-owner preservation passed")
