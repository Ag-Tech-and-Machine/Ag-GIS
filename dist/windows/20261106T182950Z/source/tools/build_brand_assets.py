"""Render the original SVG using QGIS Qt; create Windows icon and review image."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import struct
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import QByteArray, QBuffer, QIODevice, Qt, QRectF
from qgis.PyQt.QtGui import QImage, QPainter, QColor, QFont, QFontDatabase, QPainterPath
from qgis.PyQt.QtSvg import QSvgRenderer
ROOT = Path(__file__).resolve().parents[1]
app = QApplication([])
for name in ("segoeui.ttf", "seguisb.ttf"):
    assert QFontDatabase.addApplicationFont(str(Path(os.environ["WINDIR"]) / "Fonts" / name)) >= 0
# Outline the wordmark so deployment does not depend on installed fonts.
def outline(text, x, y, size, colour, weight=QFont.Normal):
    font = QFont("Segoe UI")
    font.setPixelSize(size)
    font.setWeight(weight)
    path = QPainterPath()
    path.addText(x, y, font, text)
    commands = []
    i = 0
    while i < path.elementCount():
        element = path.elementAt(i)
        if element.isMoveTo():
            commands.append(f"M{element.x:.3f},{element.y:.3f}")
        elif element.isLineTo():
            commands.append(f"L{element.x:.3f},{element.y:.3f}")
        else:
            b, c = path.elementAt(i+1), path.elementAt(i+2)
            commands.append(f"C{element.x:.3f},{element.y:.3f} {b.x:.3f},{b.y:.3f} {c.x:.3f},{c.y:.3f}")
            i += 2
        i += 1
    return '<path fill="' + colour + '" d="' + ' '.join(commands) + '"/>'
import xml.etree.ElementTree as ET
symbol = ET.parse(ROOT / "plugins/ag_tech_tooling/icon.svg").getroot()
mark = ''.join(ET.tostring(child, encoding="unicode") for child in symbol if not child.tag.endswith("title"))
lockup_source = ('<svg xmlns="http://www.w3.org/2000/svg" width="330" height="96" viewBox="0 0 330 96">'
                 '<title>Ag-GIS — Farming in view</title>' + mark
                 + outline("Ag-GIS", 110, 54, 44, "#173F35", QFont.DemiBold)
                 + outline("FARMING IN VIEW", 112, 77, 13, "#52665D") + '</svg>')
(ROOT / "plugins/ag_tech_tooling/brand_lockup.svg").write_text(lockup_source, encoding="utf-8")
renderer = QSvgRenderer(str(ROOT / "plugins/ag_tech_tooling/icon.svg"))
assert renderer.isValid()
images = []
for size in (16, 24, 32, 48, 64, 128, 256):
    bitmap = QImage(size, size, QImage.Format_ARGB32)
    bitmap.fill(Qt.transparent)
    painter = QPainter(bitmap)
    renderer.render(painter)
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    assert bitmap.save(buffer, "PNG")
    images.append((size, bytes(data)))
header = struct.pack("<HHH", 0, 1, len(images))
offset = 6 + 16 * len(images)
entries = []
for size, data in images:
    entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
    offset += len(data)
(ROOT / "installer/Ag-GIS.ico").write_bytes(header + b"".join(entries) + b"".join(data for _, data in images))
(ROOT / "plugins/ag_tech_tooling/app_icon.ico").write_bytes((ROOT / "installer/Ag-GIS.ico").read_bytes())
out = ROOT / "dist/branding"
out.mkdir(parents=True, exist_ok=True)
canvas = QImage(1200, 720, QImage.Format_ARGB32)
canvas.fill(QColor("#F5F2E8"))
painter = QPainter(canvas)
painter.setRenderHint(QPainter.Antialiasing)
lockup = QSvgRenderer(str(ROOT / "plugins/ag_tech_tooling/brand_lockup.svg"))
lockup.render(painter, QRectF(80, 100, 660, 192))
painter.setPen(QColor("#52665D"))
painter.setFont(QFont("Segoe UI", 19))
painter.drawText(84, 365, "Simple farming workflows. Built on open source tools.")
painter.setFont(QFont("Segoe UI", 14))
painter.drawText(84, 420, "An original field A, a survey point, and the line of the land.")
for i, (colour, label) in enumerate((("#173F35", "Field green"), ("#8DB59A", "Sage"), ("#D9AB55", "Harvest"), ("#52665D", "Slate"))):
    x = 84 + 260 * i
    painter.fillRect(x, 500, 210, 68, QColor(colour))
    painter.setPen(QColor("#173F35"))
    painter.drawText(x, 607, label + "  " + colour)
painter.end()
assert canvas.save(str(out / "Ag-GIS-brand.png"))
print(out / "Ag-GIS-brand.png")
