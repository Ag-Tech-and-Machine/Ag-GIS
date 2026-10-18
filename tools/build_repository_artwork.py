"""Build repository-only Ag-GIS artwork with QGIS's bundled Qt (no network)."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import xml.etree.ElementTree as ET
from qgis.PyQt.QtCore import QRectF
from qgis.PyQt.QtGui import QColor, QFont, QFontDatabase, QImage, QPainter, QPainterPath
from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/brand"


def outlined(text, x, y, size, colour, weight=QFont.Normal):
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
            b, c = path.elementAt(i + 1), path.elementAt(i + 2)
            commands.append(f"C{element.x:.3f},{element.y:.3f} {b.x:.3f},{b.y:.3f} {c.x:.3f},{c.y:.3f}")
            i += 2
        i += 1
    return f'<path fill="{colour}" d="{" ".join(commands)}"/>'


def build():
    app = QApplication.instance() or QApplication([])
    fonts = Path(os.environ["WINDIR"]) / "Fonts"
    for name in ("segoeui.ttf", "seguisb.ttf"):
        assert QFontDatabase.addApplicationFont(str(fonts / name)) >= 0
    OUT.mkdir(parents=True, exist_ok=True)
    symbol = ET.parse(OUT / "ag-gis-symbol.svg").getroot()
    mark = "".join(ET.tostring(child, encoding="unicode") for child in symbol if not child.tag.endswith("title"))
    content = '<rect width="1600" height="640" fill="#F5F2E8"/>'
    content += '<path d="M1005 0H1600V640H1130L992 418 1095 227Z" fill="#173F35"/>'
    content += '<g fill="none" stroke="#8DB59A" stroke-width="2" opacity="0.5"><path d="M1105 44 1410 10 1510 220 1210 280Z"/><path d="M1218 305 1525 255 1635 440 1330 525Z"/><path d="M1080 452 1300 550 1270 660"/><path d="M1008 243 1180 315 1105 424"/></g>'
    content += '<circle cx="1210" cy="280" r="9" fill="#D9AB55"/><circle cx="1330" cy="525" r="6" fill="#D9AB55"/>'
    content += '<g transform="translate(70 54) scale(0.88)">' + mark + '</g>'
    content += outlined("Ag-GIS", 180, 117, 61, "#173F35", QFont.DemiBold)
    content += outlined("Farming", 76, 283, 102, "#173F35", QFont.DemiBold)
    content += outlined("in view.", 76, 394, 102, "#173F35", QFont.DemiBold)
    content += '<path d="M80 433H162" stroke="#D9AB55" stroke-width="5"/>'
    content += outlined("Your farm maps. Your data. Your control.", 78, 488, 29, "#52665D")
    content += outlined("Built on open source tools", 78, 564, 27, "#173F35", QFont.DemiBold)
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="640" viewBox="0 0 1600 640" role="img"><title>Ag-GIS — Farming in view</title><desc>Your farm maps. Your data. Your control. Built on open source tools. Abstract field-boundary brand artwork, not a product screenshot.</desc>' + content + '</svg>\n'
    target = OUT / "ag-gis-banner.svg"
    target.write_text(svg, encoding="utf-8")
    renderer = QSvgRenderer(str(target))
    assert renderer.isValid()
    for name, width, height, rect in (
        ("ag-gis-banner.png", 1600, 640, QRectF(0, 0, 1600, 640)),
        ("ag-gis-social-preview.png", 1280, 640, QRectF(0, 64, 1280, 512)),
    ):
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(QColor("#F5F2E8"))
        painter = QPainter(image)
        renderer.render(painter, rect)
        painter.end()
        assert image.save(str(OUT / name))
        print(f"Built {name}: {width} x {height}")
    return app


if __name__ == "__main__":
    application = build()
