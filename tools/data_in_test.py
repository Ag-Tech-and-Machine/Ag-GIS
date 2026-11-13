"""Exercise discovery, background cancellation and map opening with real QGIS."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
from zipfile import ZipFile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsVectorFileWriter,
                       QgsFeedback, QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMainWindow, QPushButton
from osgeo import gdal
gdal.UseExceptions()
from ag_tech_tooling.import_sources import scan_local, ScanCancelled
from ag_tech_tooling.import_dialog import ImportDialog, ImportActions
from ag_tech_tooling.farm_project import create_farm
from ag_tech_tooling.background_maps import PROVIDERS
from ag_tech_tooling import hierarchy as store


def wait_until(callback):
    deadline = time.monotonic() + 15
    while not callback() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert callback(), "Background task did not finish"


class Interface:
    def __init__(self):
        self.window = QMainWindow()
        self.refreshed, self.zoomed = 0, 0

    def mainWindow(self):
        return self.window

    def mapCanvas(self):
        return self

    def refresh(self):
        self.refreshed += 1

    def zoomToFullExtent(self):
        self.zoomed += 1


if os.environ.get("AGTECH_TEST_CONFIG_PATH"):
    from qgis.PyQt.QtCore import QSettings
    config = os.environ["AGTECH_TEST_CONFIG_PATH"]
    os.environ["QGIS_CUSTOM_CONFIG_PATH"] = config
    QSettings.setDefaultFormat(QSettings.IniFormat)
    for scope in (QSettings.UserScope, QSettings.SystemScope):
        QSettings.setPath(QSettings.IniFormat, scope, config)
app = QgsApplication([], False, os.environ.get("AGTECH_TEST_CONFIG_PATH", ""))
app.initQgis()
if os.environ.get("AGTECH_TEST_CONFIG_PATH"):
    print('ISOLATED_QGIS_SETTINGS', QgsApplication.qgisSettingsDirPath())
    assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(Path(os.environ["AGTECH_TEST_CONFIG_PATH"]).resolve()), QgsApplication.qgisSettingsDirPath()
# The desktop save action reports success only after QgsProject.projectSaved.
# A cancelled/failed action must not fall back to a direct write or leak callbacks.
from qgis.PyQt.QtWidgets import QAction
class SaveInterface(Interface):
    def __init__(self):
        super().__init__()
        self.save_action = QAction(self.window)
    def actionSaveProject(self):
        return self.save_action
save_iface = SaveInterface()
save_dialog = ImportDialog(save_iface)
project = QgsProject.instance()
receivers = project.receivers(project.projectSaved)
assert not save_dialog.save_map(project), "Cancelled native action is not a saved map"
assert project.receivers(project.projectSaved) == receivers
with tempfile.TemporaryDirectory(prefix="agtech-save-map-") as save_root:
    project.setFileName(str(Path(save_root) / "Farm.qgz"))
    save_iface.save_action.triggered.connect(lambda: project.write())
    assert save_dialog.save_map(project)
    assert project.receivers(project.projectSaved) == receivers
    assert Path(project.fileName()).is_file()
    project.clear()
save_dialog.close()
with tempfile.TemporaryDirectory(prefix="agtech-data-in-") as temporary:
    root = Path(temporary)
    source = root / "Paddock.geojson"
    source.write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"name": "North"},
         "geometry": {"type": "Point", "coordinates": [145, -36]}}]}))
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    # Real multi-layer container: discovery must expose each sublayer separately.
    database = root / "Farm.gpkg"
    layer = QgsVectorLayer(str(source), "North", "ogr")
    for index, name in enumerate(("Boundaries", "Guidance")):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName, options.layerName = "GPKG", name
        if index:
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        outcome = QgsVectorFileWriter.writeAsVectorFormatV3(layer, str(database), QgsProject.instance().transformContext(), options)
        assert outcome[0] == QgsVectorFileWriter.NoError, outcome
    del layer
    result = scan_local(root)
    assert len([item for item in result["items"] if item["kind"] == "layer"]) == 3, result
    assert len(scan_local(database)["items"]) == 2
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    raster = root / "Elevation.tif"
    dataset = gdal.GetDriverByName("GTiff").Create(str(raster), 2, 2, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform((145, .01, 0, -36, 0, -.01))
    dataset.SetProjection(QgsCoordinateReferenceSystem("EPSG:4326").toWkt())
    dataset.GetRasterBand(1).Fill(10)
    dataset = None
    raster_result = scan_local(raster)
    assert len(raster_result["items"]) == 1 and raster_result["items"][0]["layer_type"] == "raster"
    archive_path = root / "Maps.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.write(source, "Maps/Paddock.geojson")
    zip_result = scan_local(archive_path)
    assert len(zip_result["items"]) == 1, zip_result
    assert zip_result["items"][0]["uri"].startswith("/vsizip/")
    archived = zip_result["items"][0]
    zip_layer = QgsVectorLayer(archived["uri"], archived["name"], archived["provider"])
    assert zip_layer.isValid() and zip_layer.featureCount() == 1
    del zip_layer
    unsafe = root / "Unsafe.zip"
    with ZipFile(unsafe, "w") as archive:
        archive.writestr("../outside.geojson", source.read_text())
    assert not scan_local(unsafe)["items"]
    assert "Unsafe" in scan_local(unsafe)["warnings"][0]
    ambiguous_zip = root / "Ambiguous.zip"
    with ZipFile(ambiguous_zip, "w") as archive:
        archive.writestr("Maps/Paddock.geojson", source.read_text())
        archive.writestr("maps/PADDOCK.geojson", source.read_text())
    ambiguous_result = scan_local(ambiguous_zip)
    assert not ambiguous_result["items"], "Reject ambiguous members before native provider discovery"
    assert any("duplicate" in message.lower() for message in ambiguous_result["warnings"])
    # Real-scanner rejection must not leak a valid first member as a ready row.
    import io
    import struct
    from contextlib import nullcontext
    from ag_tech_tooling import import_sources
    valid_name, poison_name = b'Maps/Poison.geojson', b'Maps/Poison\x00geojson'
    archive_cases = []
    for label in ('encrypted', 'nul-name', 'byte-limit', 'entry-limit'):
        path = root / ('Rejected-' + label + '.zip')
        with ZipFile(path, 'w') as archive:
            archive.writestr('Maps/Ready.geojson', source.read_bytes())
            archive.writestr(valid_name.decode(), source.read_bytes())
        raw = bytearray(path.read_bytes())
        if label == 'encrypted':
            # Only the second member is flagged: the whole archive must refuse.
            local = raw.index(b'PK\x03\x04', 4)
            central = raw.index(b'PK\x01\x02')
            central = raw.index(b'PK\x01\x02', central + 4)
            struct.pack_into('<H', raw, local + 6, 1)
            struct.pack_into('<H', raw, central + 8, 1)
        elif label == 'nul-name':
            assert raw.count(valid_name) == 2
            raw = raw.replace(valid_name, poison_name)
        path.write_bytes(raw)
        limits = ({'MAX_ARCHIVE_BYTES': len(source.read_bytes())} if label == 'byte-limit'
                  else {'MAX_FILES': 1} if label == 'entry-limit' else {})
        original = path.read_bytes()
        with patch.multiple(import_sources, **limits) if limits else nullcontext():
            rejected = scan_local(path)
        assert rejected['items'] == [], (label, rejected)
        expected = 'limits' if limits else 'Unsafe'
        assert len(rejected['warnings']) == 1 and expected in rejected['warnings'][0], (label, rejected)
        assert path.read_bytes() == original, label
        archive_cases.append(label)
    # A readable nested ZIP is opaque, even with a supported GIS member inside.
    inner = io.BytesIO()
    with ZipFile(inner, 'w') as archive:
        archive.writestr('Inner.geojson', source.read_bytes())
    nested_only = root / 'NestedOnly.zip'
    with ZipFile(nested_only, 'w') as archive:
        archive.writestr('Folder/Inner.zip', inner.getvalue())
    nested_original = nested_only.read_bytes()
    nested_only_result = scan_local(nested_only)
    assert nested_only_result['items'] == [], nested_only_result
    assert len(nested_only_result['warnings']) == 1
    assert 'Nested archive' in nested_only_result['warnings'][0]
    assert nested_only.read_bytes() == nested_original
    archive_cases.append('real-nested-only')
    print('Scanner archive refusal/no-partial-rows/source-unchanged:', ', '.join(archive_cases))
    eic = root / "GS3_2630" / "default" / "RCD" / "EIC"
    eic.mkdir(parents=True)
    (eic / "setup.fds").write_text('''<SetupFile xmlns="urn:schemas-johndeere-com:RCD:Setup">
      <Setup><Client erid="client-1" name="Grower"/>
      <Farm erid="farm-1" name="Home" clientRef="client-1"/>
      <Field erid="field-1" name="North" farmRef="farm-1"/></Setup></SetupFile>''')
    machine_result = scan_local(root / "GS3_2630")
    assert len(machine_result["items"]) == 1
    assert len(machine_result["items"][0]["metadata"]["entities"]) == 3
    machine_zip = root / "Machine.zip"
    with ZipFile(machine_zip, "w") as archive:
        archive.write(eic / "setup.fds", "RCD/EIC/setup.fds")
    machine_zip_result = scan_local(machine_zip)
    assert machine_zip_result['items'][0]['kind'] == 'deere'
    assert len(machine_zip_result['items'][0]['metadata']['entities']) == 3
    assert not machine_zip_result['items'][0]['metadata']['geometry_import_supported']
    # Real GS3 adapter produces setup/catalogue metadata, never decoded operations.
    for preview in (machine_result, machine_zip_result):
        metadata = preview['items'][0]['metadata']
        assert 'operations' not in metadata
        assert '_mapped_operations' not in metadata, 'Do not fabricate operation mappings from an absent adapter contract'
        assert not metadata['geometry_import_supported']
    # Catalogue-only machine exports are metadata previews too, not native maps.
    catalog_zip = root / "CatalogueOnly.zip"
    with ZipFile(catalog_zip, "w") as archive:
        archive.writestr("nested/profile/RCD/EIC/Fields/F1/ImportExport.SpatialCatalog",
            '<SpatialCatalog xmlns="urn:schemas-johndeere-com:RCD:SpatialCatalog:FieldImportExport">'
            '<SpatialItems eridFieldRef="unknown"><CurvedTrackLine erid="Track-A" '
            'fileName="Track" name="Original Track"><Reference sourceUOM="arcdeg" value="12"/>'
            '</CurvedTrackLine></SpatialItems></SpatialCatalog>')
        archive.writestr("nested/profile/RCD/EIC/Fields/F1/Track.fdShape", b"not geometry")
    catalog_result = scan_local(catalog_zip)
    assert len(catalog_result["items"]) == 1, catalog_result
    assert catalog_result["items"][0]["metadata"]["spatial_items"][0]["id"] == "Track-A"
    assert not catalog_result["items"][0]["metadata"]["geometry_import_supported"]
    with patch("ag_tech_tooling.import_sources.MAX_FILES", 1):
        try:
            scan_local(root)
            raise AssertionError("Expected scan limit")
        except ValueError:
            pass
    feedback = QgsFeedback()
    feedback.cancel()
    try:
        scan_local(source, feedback)
        raise AssertionError("Expected cancellation")
    except ScanCancelled:
        pass
    iface = Interface()
    dialog = ImportDialog(iface)
    dialog.show()
    dialog.path.setText(str(source))
    dialog.start_scan()
    wait_until(lambda: dialog.task is None)
    assert dialog.tree.topLevelItemCount() == 1
    assert not dialog.add_button.isEnabled()
    dialog.add_selected()
    assert not QgsProject.instance().mapLayers(), "No loose imports without a workspace"
    assert "Create or open" in dialog.status.text()
    farm_root = create_farm(root, "Workspace", QgsCoordinateReferenceSystem("EPSG:4326"),
                            organisation="Org", client="Grower", farm="Home", field="North")
    project = QgsProject.instance()
    assert project.read(str(farm_root / "Farm.qgz"))
    field_id = store.records(farm_root)["field"][0]["id"]
    boundary = QgsVectorLayer(store.layer_uri(farm_root, "agtech_boundaries"), "Boundary", "ogr")
    feature = QgsFeature(boundary.fields())
    feature["id"], feature["field_id"], feature["name"] = "test-boundary", field_id, "North"
    feature.setGeometry(QgsGeometry.fromWkt("MULTIPOLYGON(((144.9 -36.1,145.1 -36.1,145.1 -35.9,144.9 -35.9,144.9 -36.1)))"))
    assert boundary.dataProvider().addFeatures([feature])[0]
    del feature, boundary
    dialog.show_result(scan_local(source))
    # Click the actual native Stop button at the writer boundary, before writes.
    from qgis.PyQt.QtWidgets import QProgressDialog
    from ag_tech_tooling import managed_data
    real_save = managed_data.save_dataset
    before_cancel = store.database(farm_root).read_bytes(), (farm_root / 'Farm.qgz').read_bytes()
    def stop_writer(*args, **kwargs):
        progress = dialog.findChild(QProgressDialog)
        assert progress is not None
        next(button for button in progress.findChildren(QPushButton) if button.text() == 'Stop').click()
        return real_save(*args, **kwargs)
    with patch.object(managed_data, 'save_dataset', stop_writer):
        dialog.add_button.click()
    assert dialog.status.text() == 'Import stopped. 0 datasets saved. 0 already saved. 1 could not import. Save Map to keep this view.', dialog.status.text()
    assert (store.database(farm_root).read_bytes(), (farm_root / 'Farm.qgz').read_bytes()) == before_cancel
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    dialog.add_button.click()
    assert dialog.status.text() == '1 datasets saved. 0 already saved. 0 could not import. Map saved.', dialog.status.text()
    assert len(QgsProject.instance().mapLayers()) == len(PROVIDERS) + 1
    assert all(layer.readOnly() for layer in QgsProject.instance().mapLayers().values() if isinstance(layer, QgsVectorLayer))
    assert iface.refreshed == 1 and iface.zoomed == 1
    dialog.tree.topLevelItem(0).setCheckState(0, Qt.Checked)
    dialog.add_selected()
    assert len(QgsProject.instance().mapLayers()) == len(PROVIDERS) + 1, "Repeated add must not duplicate layers"
    assert "1 already saved" in dialog.status.text(), dialog.status.text()
    placed = next(layer for layer in project.mapLayers().values() if layer.customProperty("AgTechTooling/import_field"))
    assert placed.customProperty("AgTechTooling/import_field") == field_id
    node = project.layerTreeRoot().findLayer(placed.id())
    assert node.parent().name() == "Imported Data" and node.parent().parent().name() == "Whole Field"
    del node, placed
    assert all(not b.icon().isNull() for b in dialog.findChildren(QPushButton))
    dialog.show_result(machine_result)
    assert not dialog.add_button.isEnabled()
    assert dialog.tree.topLevelItem(0).child(0).child(0).child(0).text(0) == "North"
    dialog.show_result(machine_zip_result)
    assert not dialog.add_button.isEnabled(), "Machine ZIP metadata is not importable geometry"
    assert dialog.tree.topLevelItem(0).child(0).child(0).child(0).text(0) == "North"
    # A nested folder scan finds the same ZIP once, retaining catalogue units/IDs.
    nested = root / "NestedSelection" / "exports" / "2026"
    nested.mkdir(parents=True)
    nested_zip = nested / "Machine.zip"
    with ZipFile(nested_zip, "w") as archive:
        archive.write(eic / "setup.fds", "profile/RCD/EIC/setup.fds")
        archive.writestr("profile/RCD/EIC/Fields/F1/ImportExport.SpatialCatalog",
            '<SpatialCatalog xmlns="urn:schemas-johndeere-com:RCD:SpatialCatalog:FieldImportExport">'
            '<SpatialItems eridFieldRef="field-1"><CurvedTrackLine erid="Track-A" fileName="Track">'
            '<Reference sourceUOM="arcdeg" value="12"/></CurvedTrackLine></SpatialItems></SpatialCatalog>')
        archive.writestr("profile/RCD/EIC/Fields/F1/Track.fdShape", b"not decoded")
        archive.writestr("maps/Native.geojson", source.read_text())
        archive.writestr("inner.zip", b"opaque nested archive")
    zip_before = nested_zip.read_bytes()
    nested_result = scan_local(root / "NestedSelection")
    assert len(nested_result["items"]) == 2, nested_result
    machine = next(row for row in nested_result["items"] if row["kind"] == "deere")
    track = machine["metadata"]["spatial_items"][0]
    assert track["id"] == "Track-A" and track["field_id"] == "field-1"
    assert track["properties"][0]["attributes"] == {"sourceUOM": "arcdeg", "value": "12"}
    assert track["geometry_status"] == "not_decoded"
    assert any("Nested archive" in warning for warning in nested_result["warnings"])
    assert nested_zip.read_bytes() == zip_before
    dialog.show_result(raster_result)
    dialog.add_selected()
    assert len(QgsProject.instance().mapLayers()) == len(PROVIDERS) + 2
    # One real native write plus a deterministic second-item writer failure.
    batch = root / 'Partial batch'
    batch.mkdir()
    for name in ('A-good.geojson', 'B-fails.geojson'):
        (batch / name).write_bytes(source.read_bytes())
    dialog.show_result(scan_local(batch))
    def partial_writer(root_arg, layer, *args, **kwargs):
        if Path(layer.source()).name == 'B-fails.geojson':
            raise ValueError('Injected second-item writer failure')
        return real_save(root_arg, layer, *args, **kwargs)
    before_count = len(managed_data.records(farm_root))
    with patch.object(managed_data, 'save_dataset', partial_writer):
        dialog.add_button.click()
    assert dialog.status.text() == '1 datasets saved. 0 already saved. 1 could not import. Map saved.', dialog.status.text()
    assert len(managed_data.records(farm_root)) == before_count + 1
    assert any(row.text(3) == 'Injected second-item writer failure' for row in dialog.rows())
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == before for p in batch.iterdir())
    # Gate scheduling at the real archive validator, not its results/feedback.
    import threading
    from ag_tech_tooling import archive_sources
    entered, release = threading.Event(), threading.Event()
    real_inventory = archive_sources.validated_members
    cancel_observed = []
    def gated_inventory(archive, check, **limits):
        entered.set()
        if not release.wait(10):
            raise AssertionError('UI did not release the archive scan gate')
        def checked():
            try:
                check()
            except ScanCancelled:
                cancel_observed.append(True)
                raise
        return real_inventory(archive, checked, **limits)
    before_scan = (store.database(farm_root).read_bytes(), (farm_root / 'Farm.qgz').read_bytes())
    before_layers = set(project.mapLayers())
    dialog.path.setText(str(root / 'NestedSelection'))
    with patch.object(archive_sources, 'validated_members', gated_inventory):
        try:
            dialog.scan_button.click()
            wait_until(entered.is_set)
            assert dialog.task is not None and dialog.stop_button.isEnabled()
            assert not dialog.scan_button.isEnabled() and not dialog.path.isEnabled()
            assert not dialog.rows() and not dialog.add_button.isEnabled(), 'Discard stale selection while scanning'
            dialog.stop_button.click()
            assert dialog.task.feedback.isCanceled(), 'Real Stop Scan must cancel QgsFeedback'
        finally:
            release.set()
        wait_until(lambda: dialog.task is None)
    assert cancel_observed == [True], 'Real archive validator must observe cancellation'
    assert dialog.status.text() == 'Scan stopped. No data was added.', dialog.status.text()
    assert not dialog.rows() and not dialog.add_button.isEnabled()
    assert dialog.scan_button.isEnabled() and dialog.path.isEnabled()
    assert not dialog.stop_button.isEnabled()
    assert set(project.mapLayers()) == before_layers
    assert (store.database(farm_root).read_bytes(), (farm_root / 'Farm.qgz').read_bytes()) == before_scan
    assert nested_zip.read_bytes() == zip_before

    # Retry real Scan/Import; only native GIS in the mixed ZIP is importable.
    dialog.scan_button.click()
    wait_until(lambda: dialog.task is None)
    assert len(dialog.rows()) == 1 and dialog.add_button.isEnabled()
    machine_rows = [dialog.tree.topLevelItem(i) for i in range(dialog.tree.topLevelItemCount())
                    if dialog.tree.topLevelItem(i).text(1) == 'Deere GS3 RCD ZIP']
    assert len(machine_rows) == 1, 'Retry must not duplicate the machine container'
    stack, labels, item = list(machine_rows), [], None
    while stack:
        item = stack.pop()
        labels.append(item.text(0))
        # QTreeWidgetItem defaults include ItemIsUserCheckable; a checkbox is
        # presented only with CheckStateRole. The import contract is UserRole.
        assert item.data(0, Qt.CheckStateRole) is None, 'Undecoded machine resources have no checkbox'
        assert item.data(0, Qt.UserRole) is None
        stack.extend(item.child(i) for i in range(item.childCount()))
    assert all(name in labels for name in ('Grower', 'Home', 'North'))
    assert any('Nested archive' in dialog.tree.topLevelItem(i).text(3)
               for i in range(dialog.tree.topLevelItemCount()))
    before_zip_count = len(managed_data.records(farm_root))
    dialog.add_button.click()
    assert dialog.status.text() == '1 datasets saved. 0 already saved. 0 could not import. Map saved.', dialog.status.text()
    assert len(managed_data.records(farm_root)) == before_zip_count + 1
    assert len(project.mapLayers()) == len(before_layers) + 1
    assert nested_zip.read_bytes() == zip_before
    dialog.scan_button.click()
    wait_until(lambda: dialog.task is None)
    assert len(dialog.rows()) == 1
    before_duplicate = (store.database(farm_root).read_bytes(), (farm_root / 'Farm.qgz').read_bytes())
    dialog.add_button.click()
    assert dialog.status.text() == '0 datasets saved. 1 already saved. 0 could not import. Save Map to keep this view.', dialog.status.text()
    assert (store.database(farm_root).read_bytes(), (farm_root / 'Farm.qgz').read_bytes()) == before_duplicate
    assert len(managed_data.records(farm_root)) == before_zip_count + 1
    assert len(project.mapLayers()) == len(before_layers) + 1
    assert nested_zip.read_bytes() == zip_before
    del item, machine_rows, labels, stack
    print('Mixed Deere ZIP: live Stop Scan/no-write, retry/import, preview-only hierarchy and duplicate rejection passed')
    dialog.path.setText(str(root / "Missing"))
    dialog.start_scan()
    wait_until(lambda: dialog.task is None)
    assert "Could not scan" in dialog.status.text()
    assert not dialog.add_button.isEnabled(), "Failed rescan must discard stale selection"
    # Close during a task; queued completion must not touch a closed/deleted dialog.
    dialog.path.setText(str(source))
    dialog.start_scan()
    dialog.reject()
    assert dialog.path.isEnabled()
    wait_until(lambda: QgsApplication.taskManager().countActiveTasks() == 0)
    actions = ImportActions(iface)
    actions.open()
    opened = actions.dialog
    actions.open()
    assert actions.dialog is opened
    actions.close()
    assert actions.dialog is None
    dialog.deleteLater()
    app.processEvents()
    QgsProject.instance().clear()
    app.exitQgis()  # Release native provider pools before deleting Windows fixtures.
print("Data In native discovery, ZIP, source safety, async UI, map add and lifecycle checks passed")
