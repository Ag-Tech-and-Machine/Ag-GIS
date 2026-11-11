"""Synthetic PCTGDP container recognition; never includes customer data."""

import hashlib

import os

from pathlib import Path

import sys

import tempfile

from zipfile import ZipFile, ZIP_DEFLATED

from unittest.mock import patch



os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

    pass  # QGIS not available, skip this test

except ImportError:

    from qgis.PyQt.QtWidgets import QMainWindow

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

from ag_tech_tooling.import_sources import scan_local

from ag_tech_tooling.import_dialog import ImportDialog

from ag_tech_tooling.pctgdp_preview import inspect_project, PreviewCancelled



tempfile.tempdir = os.environ.get("TMPDIR", str(Path.home() / "AppData/Local/hermes/cache/scratch"))





def container(path, xml):

    path.write_bytes(b"PCTGDP" + bytes(32768 - 6))

    with ZipFile(path, "a", ZIP_DEFLATED) as archive:

        archive.writestr("Synthetic.pctgdp", xml)





def test_recognition(root):

    source = root / "Synthetic.pctgdp"

    container(source, '''<?xml version="1.0"?><ProjectVariables xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

    <ElevationLayers><LayerVariables xsi:type="ElevationLayerVariables"><Id>6</Id>

    <DisplayName>Test surface</DisplayName><GridLayer><UtmZone>55</UtmZone><UtmNS>S</UtmNS>

    <PixelSize>0.5</PixelSize><Origin><X>300000</X><Y>6000000</Y></Origin>

    <NullValue>1.7976931348623157E+308</NullValue><GridString>AAAA</GridString></GridLayer>

    <DataUnits>METERS</DataUnits></LayerVariables></ElevationLayers>

    <BoundaryLayers><LayerVariables xsi:type="BoundaryLayerVariables"><Id>7</Id>

    <DisplayName>Test boundary</DisplayName><UtmZone>55</UtmZone><UtmNs>S</UtmNs>

    </LayerVariables></BoundaryLayers></ProjectVariables>''')

    before = hashlib.sha256(source.read_bytes()).hexdigest()

    result = scan_local(source)

    assert len(result["items"]) == 1, result

    item = result["items"][0]

    assert item["kind"] == "pctgdp", item

    metadata = item["metadata"]

    assert metadata["source_unchanged"] and metadata["sha256"] == before

    assert [layer["name"] for layer in metadata["layers"]] == ["Test surface", "Test boundary"]

    grid = metadata["layers"][0]

    assert grid["pixel_size"] == "0.5" and grid["units"] == "METERS"

    assert grid["utm_zone"] == "55" and grid["hemisphere"] == "S"

    assert grid["grid_characters"] == 4

    assert "GridString" not in str(metadata)

    assert not any(row["kind"] == "layer" for row in result["items"])

    assert hashlib.sha256(source.read_bytes()).hexdigest() == before

    assert scan_local(root)["items"][0]["kind"] == "pctgdp"

    print("PCTGDP direct/folder recognition and source integrity passed")

    class Interface:

        def __init__(self):

            self.window = QMainWindow()



        def mainWindow(self):

            return self.window



    iface = Interface()

    dialog = ImportDialog(iface)

    dialog.show_result(result)

    row = dialog.tree.topLevelItem(0)

    assert row.childCount() == 2, "Project layers must be visible in Data In"

    assert row.child(0).text(0) == "Test surface"

    assert "datum" in row.child(0).toolTip(3).lower()

    assert not dialog.rows(), "Unverified project layers must not be importable"

    dialog.close()

    dialog.deleteLater()

    app.processEvents()

    print("PCTGDP inline layer preview passed")





def test_safety(root):

    source = root / "Invalid.pctgdp"

    for xml in ("<ProjectVariables>", '<!DOCTYPE x [<!ENTITY test "bad">]><ProjectVariables>&test;</ProjectVariables>',

                "<Other/>"):

        container(source, xml)

        result = scan_local(source)

        assert not result["items"] and "Cannot preview" in result["warnings"][0], result

    source.write_bytes(b"not a project")

    assert "signature" in scan_local(source)["warnings"][0]

    source.write_bytes(b"PCTGDP")

    with ZipFile(source, "a") as archive:

        archive.writestr("../Unsafe.pctgdp", "<ProjectVariables/>")

    assert "Unsafe" in scan_local(source)["warnings"][0]

    container(source, '<ProjectVariables><ElevationLayers><LayerVariables><DisplayName>Large grid</DisplayName>'

              '<GridLayer><GridString>' + "A" * 200000 + '</GridString></GridLayer></LayerVariables></ElevationLayers></ProjectVariables>')

    metadata = inspect_project(source)

    assert metadata["layers"][0]["grid_characters"] == 200000

    assert len(str(metadata)) < 2000

    with patch("ag_tech_tooling.pctgdp_preview.MAX_XML_BYTES", 100):

        assert "limit" in scan_local(source)["warnings"][0]

    checks = 0



    def cancelled():

        nonlocal checks

        checks += 1

        return checks > 8



    try:

        inspect_project(source, cancelled=cancelled)

        raise AssertionError("Expected cancellation during XML inspection")

    except PreviewCancelled:

        pass

    print("PCTGDP malformed XML, DTD, root, signature, path safety, bounded streaming, limit and cancellation passed")





if __name__ == "__main__":

    app = QgsApplication([], False)

    app.initQgis()

    try:

        with tempfile.TemporaryDirectory(prefix="aggis-pctgdp-") as temporary:

            test_recognition(Path(temporary))

            test_safety(Path(temporary))

    finally:

        app.exitQgis()


