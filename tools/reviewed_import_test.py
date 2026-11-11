"""Assert actual reviewed Data In import, durable context and catalogue recovery."""

import gc

import json

import os

from pathlib import Path

import sqlite3

import sys

import tempfile

from contextlib import closing

from unittest.mock import patch



os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT', str(Path(__file__).resolve().parents[1] / 'plugins')))

    pass  # QGIS not available, skip this test

except ImportError:

        from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsRasterBlockFeedback

        from ag_tech_tooling import reviewed_import as binding, import_placement as placement

    def safety(temporary):

    

    

            gc.collect()

            project.clear()

            del layer

            assert source.read_bytes() == original

            assert layer.customProperty('AgTechTooling/import_season') == summer

            assert context(layer) == 'operations:' + summer

            layer = next(iter(project.mapLayers().values()))

            assert managed.restore_datasets(root) == []

            project.removeAllMapLayers()

            del layer

            assert context(layer) == 'operations:' + summer

            layer = next(layer for layer in project.mapLayers().values() if layer.customProperty('AgTechTooling/dataset_id') == record['id'])

            assert project.read(str(root / 'Farm.qgz'))

            gc.collect()

            project.clear()

            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

            del dialog, row, layer, feature, iface

            sip.delete(iface.window)

            sip.delete(dialog)

            dialog.reject()

            assert project.write()

            assert context(layer) == 'operations:' + summer

                return node.parent().customProperty('AgTechTooling/node')

                node = project.layerTreeRoot().findLayer(layer.id())

            def context(layer):

            assert layer.customProperty('AgTechTooling/import_season') == summer

            assert feature['job_token'] == ' Raw Vendor JOB ' and feature['units'] == 'gal?'

            feature = next(layer.getFeatures())

            layer = next(layer for layer in project.mapLayers().values() if layer.customProperty('AgTechTooling/dataset_id') == record['id'])

            assert provenance['vendor_mapping'] is None and provenance['unit_mapping'] is None

            assert provenance['mapping_rule'] == 'explicit-selection-v1' and provenance['mapping_version'] == 1

            assert provenance['source']['source_hash'] == record['source_hash']

            assert provenance['source']['source_uri'] == str(source)

            assert provenance['review']['job_date'] == '2027-01-15'

            assert provenance['contract'] == 'reviewed-import-v1'

            provenance = json.loads(classification['source_value'])

            assert classification['operation_subtype'] == 'planting' and classification['operation_family'] == 'planting'

            assert classification['field_id'] == field and classification['season_id'] == summer

            assert classification['dataset_id'] == record['id']

                classification = dict(conn.execute('SELECT * FROM agtech_classifications WHERE id=?', (record['classification_id'],)).fetchone())

                conn.row_factory = sqlite3.Row

            with closing(sqlite3.connect(store.database(root))) as conn:

            assert record['classification_id']

            record = rows[0]

            assert len(rows) == 1, row.text(3)

            rows = managed.records(root)

            assert dialog.status.text() == '1 datasets saved. 0 already saved. 0 could not import. Map saved.', dialog.status.text()

            dialog.add_button.click()

            if errors: raise errors[0]

            dialog.season_preview_button.click()

            QTimer.singleShot(0, review_modal)

            assert store.database(root).read_bytes() == before_db and (root / 'Farm.qgz').read_bytes() == before_map

            assert row.data(0, Qt.UserRole + 3) is None, 'Keep Whole Field clears only the staged job'

            dialog.season_preview_button.click()

            QTimer.singleShot(0, lambda: QApplication.activeModalWidget().clear_button.click())

            sip.delete(preview)

            preview.reject()

            source.write_bytes(original)

            assert preview.accepted_review is None and 'Source changed' in preview.result.text(), 'Do not accept a stale attribute preview'

            preview.use_button.click()

            source.write_bytes(original + b'\n')

            preview.operation.setCurrentIndex(preview.operation.findData('planting'))

            preview.job_date.setText('2027-01-15')

            preview = dialog.create_season_preview()

            assert row.data(0, Qt.UserRole + 3) == accepted, 'Cancel must retain the prior deliberate draft'

            dialog.season_preview_button.click()

            QTimer.singleShot(0, lambda: QApplication.activeModalWidget().reject())

            accepted = row.data(0, Qt.UserRole + 3)

            assert store.database(root).read_bytes() == before_db and (root / 'Farm.qgz').read_bytes() == before_map

            assert row.data(0, Qt.UserRole + 3)['season_id'] == summer

            if errors: raise errors[0]

            dialog.season_preview_button.click()

            QTimer.singleShot(0, review_modal)

                    QApplication.activeModalWidget().reject()

                    errors.append(error)

                except BaseException as error:

                    modal.use_button.click()

                    assert modal.use_button.isEnabled()

                    modal.operation.setCurrentIndex(modal.operation.findData('planting'))

                    modal.job_date.setText('2027-01-15')

                    assert not modal.use_button.isEnabled()

                    assert hasattr(modal, 'use_button'), 'Season preview must allow explicit reviewed import binding'

                    assert modal is not None

                    modal = QApplication.activeModalWidget()

                try:

            def review_modal():

            errors = []

            before_db, before_map = store.database(root).read_bytes(), (root / 'Farm.qgz').read_bytes()

            dialog.tree.setCurrentItem(row)

            dialog.set_plan(row, {'field_id': field}, 'Ready')

            row = dialog.rows()[0]

            dialog.show_result(scan_local(source))

            dialog = ImportDialog(iface)

            iface = Interface()

            original = source.read_bytes()

                 'properties': {'job_token': ' Raw Vendor JOB ', 'date_token': '20270115', 'units': 'gal?'}}]}))

                {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [145, -36]},

            source.write_text(json.dumps({'type': 'FeatureCollection', 'features': [

            source = Path(temporary) / 'Operation.geojson'

            store.add_record(root, 'season', 'Winter 2027', field, start='2027-04-01', end='2027-09-30')

            summer = store.add_record(root, 'season', 'Summer 2026/27', field, start='2026-10-01', end='2027-03-31')

            field = store.records(root)['field'][0]['id']

            assert project.read(str(root / 'Farm.qgz'))

            project = QgsProject.instance()

                               organisation='Org', client='Client', farm='Home', field='North')

            root = create_farm(Path(temporary), 'Synthetic', QgsCoordinateReferenceSystem('EPSG:4326'),

        if True:  # Keep native wrappers function-local before fixture cleanup.

    def exercise(temporary):

    

    

        def zoomToFullExtent(self): pass

        def refresh(self): pass

        def mapCanvas(self): return self

        def mainWindow(self): return self.window

        def __init__(self): self.window = QMainWindow()

    class Interface:

    

    app.initQgis()

    app = QgsApplication([], False)

    

    from ag_tech_tooling.import_sources import scan_local

    from ag_tech_tooling.import_dialog import ImportDialog

    from ag_tech_tooling.farm_project import create_farm

    from ag_tech_tooling import hierarchy as store, managed_data as managed

    from qgis.PyQt import sip

    from qgis.PyQt.QtWidgets import QMainWindow, QApplication

    from qgis.PyQt.QtCore import Qt, QTimer, QCoreApplication, QEvent

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsProject
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

    from osgeo import gdal

    root = create_farm(Path(temporary), 'Safety', QgsCoordinateReferenceSystem('EPSG:4326'),

                       organisation='Org', client='Client', farm='Home', field='North')

    project = QgsProject.instance()

    assert project.read(str(root / 'Farm.qgz'))

    field = store.records(root)['field'][0]['id']

    summer = store.add_record(root, 'season', 'Summer', field, start='2026-10-01', end='2027-03-31')

    winter = store.add_record(root, 'season', 'Winter', field, start='2027-04-01', end='2027-09-30')

    path = Path(temporary) / 'Safety.geojson'

    raw = json.dumps({'type': 'FeatureCollection', 'features': [{'type': 'Feature',

         'geometry': {'type': 'Point', 'coordinates': [145, -36]}, 'properties': {'raw': ' RAW ', 'units': 'gal?'}}]})

    path.write_text(raw)

    source = QgsVectorLayer(str(path), 'Safety', 'ogr')

    def review(day='2027-03-31', operation='spraying'):

        return binding.prepare_review(root, source, placement.review_job_season(root, field, day, operation))

    # Establish a Whole Field reference and catalogue before fault injection.

    reference, reference_layer, _ = managed.save_dataset(root, source, field, 'samples')

    placement.place_layer(root, reference_layer, field, 'samples')

    reference_node = project.layerTreeRoot().findLayer(reference_layer.id()).parent()

    assert reference_node.parent().customProperty('AgTechTooling/node') == 'whole:' + field

    def snapshot():

        with closing(sqlite3.connect(store.database(root))) as conn:

            tables = list(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'agtech_data_%' ORDER BY name"))

            contents = list(conn.execute('SELECT table_name FROM gpkg_contents ORDER BY table_name'))

            counts = conn.execute("SELECT 1 FROM sqlite_master WHERE name='agtech_classifications'").fetchone()

            history = list(conn.execute('SELECT * FROM agtech_classifications')) if counts else []

        return managed.records(root), tables, contents, history

    def reject(draft, contains, role='data', feedback=None):

        before = snapshot()

        try:

            managed.save_dataset(root, source, field, role, feedback, review=draft)

        except (ValueError, sqlite3.Error) as error:

            assert contains in str(error), str(error)

        else:

            raise AssertionError('Unsafe or failed binding was saved')

        assert snapshot() == before, 'Failure must preserve catalogue/history and remove partial native tables'

    draft = review()

    # Source may change after initial validation and immediately before commit.

    original_store = binding.store_review

    def mutate_before_commit(conn, record, accepted):

        identifier = original_store(conn, record, accepted)

        path.write_text(raw + '\n')

        return identifier

    with patch.object(binding, 'store_review', mutate_before_commit):

        reject(draft, 'Source changed')

    path.write_text(raw)

    # Valid but changed timeline must not silently redirect a reviewed job.

    with closing(sqlite3.connect(store.database(root))) as conn:

        with conn:

            conn.execute('UPDATE agtech_seasons SET end_date=? WHERE id=?', ('2027-03-30', summer))

            conn.execute('UPDATE agtech_seasons SET start_date=? WHERE id=?', ('2027-03-31', winter))

    reject(draft, 'timeline changed')

    draft = review()

    assert draft['season_id'] == winter

    reject(draft, 'Reference types', role='samples')

    feedback = QgsRasterBlockFeedback()

    feedback.cancel()

    reject(draft, 'stopped', feedback=feedback)

    def fail_after_metadata(conn, record, accepted):

        original_store(conn, record, accepted)

        raise ValueError('injected metadata failure')

    with patch.object(binding, 'store_review', fail_after_metadata):

        reject(draft, 'injected metadata failure')

    # A writer-side timeline change is revalidated after the native copy.

    original_catalogue = managed._catalogue

    def timeline_during_copy(root):

        result = original_catalogue(root)

        with closing(sqlite3.connect(store.database(root))) as conn:

            with conn:

                conn.execute('UPDATE agtech_seasons SET name=? WHERE id=?', ('Changed Winter', winter))

        return result

    with patch.object(managed, '_catalogue', timeline_during_copy):

        reject(draft, 'timeline changed')

    draft = review()

    record, saved, created = managed.save_dataset(root, source, field, review=draft)

    assert created and binding.read_binding(root, record) == draft

    identical, duplicate, created = managed.save_dataset(root, source, field, review=draft)

    assert not created and identical['id'] == record['id']

    del duplicate

    reject(review(operation='spreading'), 'different job context')

    reject(None, 'different job context')

    with closing(sqlite3.connect(store.database(root))) as conn:

        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []

        for statement in ('UPDATE agtech_classifications SET source_value=\'changed\'', 'DELETE FROM agtech_classifications'):

            try:

                conn.execute(statement)

            except sqlite3.IntegrityError as error:

                assert 'immutable' in str(error)

            else:

                raise AssertionError('Reviewed raw/rule provenance was mutable')

            conn.rollback()

    # GeoTIFF review uses the same storage contract; bytes and units stay raw.

    tif = Path(temporary) / 'Operation.tif'

    dataset = gdal.GetDriverByName('GTiff').Create(str(tif), 2, 2, 1, gdal.GDT_Byte)

    dataset.SetGeoTransform((145, .01, 0, -36, 0, -.01))

    dataset.SetProjection(source.crs().toWkt())

    dataset.GetRasterBand(1).SetUnitType('gal?')

    dataset = None

    raster = QgsRasterLayer(str(tif), 'Raster Job', 'gdal')

    raster_review = binding.prepare_review(root, raster, placement.review_job_season(root, field, '2027-04-01', 'spreading'))

    raster_record, raster_saved, _ = managed.save_dataset(root, raster, field, review=raster_review)

    assert Path(managed.dataset_uri(root, raster_record)).read_bytes() == tif.read_bytes()

    assert binding.read_binding(root, raster_record)['season_id'] == winter

    assert path.read_text() == raw

    del source, saved, raster, raster_saved, reference_layer, reference_node

    project.clear()

    gc.collect()



try:

    with tempfile.TemporaryDirectory(prefix='aggis-reviewed-import-') as temporary:

        exercise(temporary)

        safety(temporary)

        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        gc.collect()

finally:

    QgsProject.instance().clear()

    gc.collect()

    app.exitQgis()

print('Asserted reviewed Data In import, classification pointer and seasonal catalogue recovery passed')


