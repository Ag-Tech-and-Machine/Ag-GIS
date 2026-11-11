"""Native saved-map styles must survive catalogue-only recovery."""

import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import sys, tempfile, gc

from pathlib import Path

scratch = Path(os.environ.get('AGTECH_TEST_SCRATCH', str(Path.home() / 'AppData/Local/hermes/cache/scratch')))

if scratch.is_dir():

    tempfile.tempdir = str(scratch)

    for key in ('TEMP', 'TMP', 'TMPDIR'): os.environ[key] = tempfile.tempdir

sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT', str(Path(__file__).resolve().parents[1] / 'plugins')))

    pass  # QGIS not available, skip this test

except ImportError:

            from qgis.PyQt.QtXml import QDomDocument

            # A prepared XML document is not proof the final .qgz write succeeded.

            assert revision() == revision_before + 1

            recovered_check = None

            assert recovered_check.renderer().symbol().color().name() == '#667788'

            recovered_check = managed_data.open_dataset(root, managed_data.records(root)[0])

            QgsApplication.processEvents()

            recovered.renderer().symbol().setColor(QColor('#aabbcc'))

            assert project.write()

            recovered.renderer().symbol().setColor(QColor('#667788'))

            # Snapshot the saved style, not an unsaved edit made before queued sync.

            assert managed_data.records(root)[0]['style_xml'] == record['style_xml'], 'Import snapshot must stay immutable'

            assert revision() == revision_before

            QgsApplication.processEvents()

            recovered.renderer().symbol().setColor(QColor('#445566'))

            # Editing without Save Map must not change durable recovery styling.

            revision_before = revision()

            def revision(): return latest(root)[record['id']]['revision']

            import sqlite3

            from ag_tech_tooling.dataset_styles import latest, TABLE, SavedStyles

            assert recovered.renderer().symbol().color().name() == COLOURS['spraying'], 'Saved reset must be durable too'

            recovered = next(l for l in project.mapLayers().values() if l.customProperty('AgTechTooling/dataset_id') == record['id'])

            assert managed_data.restore_datasets(root, project) == []

            project.removeMapLayer(recovered.id()); recovered = None

            QgsApplication.processEvents()

            assert project.write()

            assert recovered.renderer().symbol().color().name() == COLOURS['spraying']

            assert apply_operation_style(recovered, reset=True)

            assert not apply_operation_style(recovered), 'Recovery must retain user style until deliberate reset'

            assert json.loads(recovered.customProperty(CLASSIFICATION_KEY, '{}')) == classification, 'Recovery lost explicit style classification'

            assert next(recovered.getFeatures())['raw_unit'] == 'gal?'

            assert hashlib.sha256(raster_path.read_bytes()).hexdigest() == raster_hash

            assert raster_recovered.renderer().opacity() == .37

            raster_recovered = next(l for l in project.mapLayers().values() if l.customProperty('AgTechTooling/dataset_id') == raster_record['id'])

            assert managed_data.restore_datasets(root, project) == []

            project.removeMapLayer(raster_reopened.id()); raster_reopened = None

            assert raster_reopened.renderer().opacity() == .37

            raster_reopened = next(l for l in project.mapLayers().values() if l.customProperty('AgTechTooling/dataset_id') == raster_record['id'])

            assert recovered.renderer().symbol().size() == 4.25

            assert recovered.renderer().symbol().color().name() == '#e12387', 'Catalogue-only recovery lost later native style edit'

            recovered = next(l for l in project.mapLayers().values() if l.customProperty('AgTechTooling/dataset_id') == record['id'])

            assert managed_data.restore_datasets(root, project) == []

            project.removeMapLayer(reopened.id()); reopened = None

            assert reopened.renderer().symbol().color().name() == '#e12387'

            reopened = next(l for l in project.mapLayers().values() if l.customProperty('AgTechTooling/dataset_id') == record['id'])

            project.clear(); assert project.read(str(root / 'Farm.qgz'))

            # Save-and-switch in one native callback must flush finalized styling.

            assert project.write()

            layer.renderer().symbol().setSize(4.25)

            layer.renderer().symbol().setColor(QColor('#e12387'))

            raster_layer.renderer().setOpacity(.37)

            place_layer(root, raster_layer, field, 'elevation')

            raster_record, raster_layer, _ = managed_data.save_dataset(root, raster_source, field, 'elevation')

            raster_source = QgsRasterLayer(str(raster_path), 'Original raster', 'gdal')

            raster_hash = hashlib.sha256(raster_path.read_bytes()).hexdigest()

            raster_data.GetRasterBand(1).WriteRaster(0, 0, 2, 2, bytes([1, 2, 3, 4])); raster_data = None

            raster_data.SetProjection(QgsCoordinateReferenceSystem('EPSG:4326').toWkt())

            raster_data.SetGeoTransform((0, 1, 0, 2, 0, -1))

            raster_data = gdal.GetDriverByName('GTiff').Create(str(raster_path), 2, 2, 1, gdal.GDT_Byte)

            raster_path = Path(directory) / 'original.tif'

            import hashlib

            from qgis.core import QgsRasterLayer

            gdal.UseExceptions()

            from osgeo import gdal

            assert apply_operation_style(layer)

            layer.setCustomProperty(CLASSIFICATION_KEY, json.dumps(classification))

            classification = classify({'unknown': 'exact:42'}, purpose='operation', operation='spraying')

            import json

            from ag_tech_tooling.operation_style import CLASSIFICATION_KEY, apply_operation_style, COLOURS

            from ag_tech_tooling.classification import classify

            place_layer(root, layer, field)

            record, layer, _ = managed_data.save_dataset(root, source, field)

            field = hierarchy.records(root)['field'][0]['id']

            assert source.dataProvider().addFeatures([feature])[0]

            feature = QgsFeature(source.fields()); feature['raw_unit']='gal?'; feature.setGeometry(QgsGeometry.fromWkt('POINT(1 1)'))

            source = QgsVectorLayer('Point?crs=EPSG:4326&field=raw_unit:string', 'raw', 'memory')

            actions.attach_styles()

            # Same lifecycle used by the plugin, without a desktop tree in this API test.

            assert project.read(str(root / 'Farm.qgz'))

            root = create_farm(directory, 'Style Farm', QgsCoordinateReferenceSystem('EPSG:4326'), organisation='Org', client='Client', farm='Farm', field='Field', build_tree=True)

        try:

        directory = tempfile.mkdtemp(prefix='aggis-durable-style-')

        actions = FarmActions(Iface())

        project = QgsProject.instance()

                warnings.append(args[-1]); print('Message:', args)

            def pushMessage(self, *args, **kwargs):

            def messageBar(self): return self

        class Iface:

        warnings = []

        from ag_tech_tooling.farm_dialog import FarmActions

        from ag_tech_tooling.import_placement import place_layer

        from ag_tech_tooling import hierarchy, managed_data

        from ag_tech_tooling.farm_project import create_farm

    def check():

    

    app = QgsApplication([], False); app.initQgis()

    from qgis.PyQt.QtGui import QColor

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication, QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsCoordinateReferenceSystem
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

        document = QDomDocument(); document.setContent('<qgis/>')

        actions.styles.prepare_save(document)

        actions.styles.flush()

        assert revision() == revision_before + 1

        assert 'save receipt' in warnings[-1]

        # Failed native save: no commit, original map retained.

        good_path = project.fileName()

        assert not project.write(str(root / 'missing-folder' / 'Farm.qgz'))

        project.setFileName(good_path)

        QgsApplication.processEvents()

        assert revision() == revision_before + 1

        # Storage failure is visible; a successful map save is not a style commit.

        lock = sqlite3.connect(hierarchy.database(root)); lock.execute('BEGIN IMMEDIATE')

        try:

            assert project.write(); QgsApplication.processEvents()

            assert revision() == revision_before + 1 and 'locked' in warnings[-1]

        finally:

            lock.rollback(); lock.close()

        # Duplicate copies are deliberately ambiguous, never last-layer-wins.

        copy = managed_data.open_dataset(root, managed_data.records(root)[0])

        place_layer(root, copy, field)

        assert project.write(); QgsApplication.processEvents()

        assert revision() == revision_before + 1

        assert 'Multiple map copies' in warnings[-1]

        project.removeMapLayer(copy.id()); copy = None

        # Two live style controllers (two sessions) share an optimistic revision guard.

        assert project.write(); QgsApplication.processEvents()

        other_project = QgsProject(); assert other_project.read(project.fileName())

        other = SavedStyles(warnings.append, other_project)

        before_conflict = revision()

        recovered.renderer().symbol().setColor(QColor('#224466'))

        assert project.write(); QgsApplication.processEvents()

        assert revision() == before_conflict + 1

        assert other_project.write(); QgsApplication.processEvents()

        assert revision() == before_conflict + 1, 'Stale session must not replace newer styling'

        assert 'Newer or unrecognized' in warnings[-1]

        other.close(); other_project.clear(); other_project = None

        # History is append-only under ordinary SQL, and dataset FK is valid.

        with sqlite3.connect(hierarchy.database(root)) as conn:

            assert conn.execute('PRAGMA foreign_key_check').fetchall() == []

            for sql in (f'UPDATE {TABLE} SET style_xml=style_xml', f'DELETE FROM {TABLE}'):

                try: conn.execute(sql)

                except sqlite3.IntegrityError: pass

                else: raise AssertionError('Style history guard missing')

        # Detach/reload does not duplicate callbacks or save while unloaded.

        actions.detach_styles(); frozen = revision()

        assert project.write(); QgsApplication.processEvents(); assert revision() == frozen

        # That unobserved map changed: reattach must refuse overriding history.

        actions.attach_styles(); assert project.write(); QgsApplication.processEvents()

        assert revision() == frozen and 'Newer or unrecognized' in warnings[-1]

        # Reopen the exact saved map associated with the latest style revision.

        # A stale project refusal retains its native edited style, not a silent restore.

        assert recovered.renderer().symbol().color().name() == '#224466'

        assert next(recovered.getFeatures())['raw_unit'] == 'gal?'

        with sqlite3.connect(hierarchy.database(root)) as conn:

            assert [r[1] for r in conn.execute(f'PRAGMA table_info({TABLE})')] == ['dataset_id', 'revision', 'contract', 'style_xml', 'project_sha256', 'saved_utc']

            conn.execute(f'INSERT INTO {TABLE} SELECT dataset_id,revision+1,?,style_xml,project_sha256,saved_utc FROM {TABLE} WHERE dataset_id=? AND revision=?', ('future-style-v99', record['id'], frozen))

        try: managed_data.open_dataset(root, managed_data.records(root)[0])

        except ValueError as error: assert 'compatible' in str(error)

        else: raise AssertionError('Unknown style contract silently fell back')

        actions.detach_styles()

        project.clear(); layer = recovered = source = None

    finally:

        actions.detach_styles()

        project.clear()

    print('Durable dataset styles: native project save/reopen and catalogue-only recovery passed')

try:

    check(); gc.collect()

finally:

    QgsProject.instance().clear(); app.exitQgis()


