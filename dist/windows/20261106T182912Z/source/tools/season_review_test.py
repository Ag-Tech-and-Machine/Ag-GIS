"""Real Data In season preview: field-scoped, dated, read-only and conservative."""
import gc
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMainWindow
from ag_tech_tooling import hierarchy as store, import_placement as placement
from ag_tech_tooling.farm_project import create_farm
from ag_tech_tooling.import_dialog import ImportDialog
from ag_tech_tooling.import_sources import scan_local

app = QgsApplication([], False)
app.initQgis()


def check():
    assert hasattr(placement, 'review_job_season'), 'Data In needs a field-scoped date/type season review, not guessed placement'
    with tempfile.TemporaryDirectory(prefix='aggis-season-review-') as temporary:
        root = create_farm(Path(temporary), 'Synthetic', QgsCoordinateReferenceSystem('EPSG:4326'),
                           organisation='Org', client='Client', farm='Home', field='North')
        project = QgsProject.instance()
        assert project.read(str(root / 'Farm.qgz'))
        field = store.records(root)['field'][0]['id']
        # Reverse name order must not change chronological matching across New Year.
        summer = store.add_record(root, 'season', 'Z Summer 2026/27', field, start='2026-10-01', end='2027-03-31')
        winter = store.add_record(root, 'season', 'A Winter 2027', field, start='2027-04-01', end='2027-09-30')
        result = placement.review_job_season(root, field, '2027-01-15', 'planting')
        assert result['season_id'] == summer and result['operation_subtype'] == 'planting'
        assert [r['id'] for r in result['timeline']] == [summer, winter]
        assert placement.review_job_season(root, field, '2027-03-31', 'spraying')['season_id'] == summer
        assert placement.review_job_season(root, field, '2027-04-01', 'spraying')['season_id'] == winter
        # Full-field timeline must be safe, not merely the matching interval.
        def rejected(day, operation='planting', target=field, contains=''):
            try:
                placement.review_job_season(root, target, day, operation)
            except ValueError as error:
                assert contains in str(error), str(error)
            else:
                raise AssertionError('Unsafe season review accepted')
        for day in ('', '20270230', '2027-02-30', '2027-1-15', ' 2027-01-15', '2027-01-15T12:00:00'):
            rejected(day, contains='YYYY-MM-DD')
        rejected('2027-01-15', operation=' VendorX ', contains='Unknown')
        rejected('2027-01-15', target='missing', contains='existing field')
        rejected('2026-09-30', contains='outside')
        rejected('2027-10-01', contains='outside')
        unrelated = placement.ensure_field(root, dict(organisation='Org', client='Client', farm='Home', field='Other'))
        store.add_record(root, 'season', 'Undated elsewhere', unrelated)
        assert placement.review_job_season(root, field, '2027-01-15', 'tillage')['season_id'] == summer
        import sqlite3
        from contextlib import closing
        def dates(identifier, start, end):
            with closing(sqlite3.connect(store.database(root))) as conn:
                with conn:
                    conn.execute('UPDATE agtech_seasons SET start_date=?,end_date=? WHERE id=?', (start, end, identifier))
        dates(winter, '2027-04-02', '2027-09-30')
        rejected('2027-01-15', contains='gap or overlap')
        dates(winter, '2027-03-31', '2027-09-30')
        rejected('2027-01-15', contains='gap or overlap')
        dates(winter, '', '')
        rejected('2027-01-15', contains='valid start and end')
        dates(summer, '9999-01-01', '9999-12-31')
        dates(winter, '9999-12-31', '9999-12-31')
        rejected('9999-01-15', contains='gap or overlap')
        dates(summer, '2026-10-01', '2027-03-31')
        dates(winter, '2027-04-01', '2027-09-30')
        # Supported adapter is the real native GeoJSON scanner, not GS3 metadata.
        source = Path(temporary) / 'Operation.geojson'
        source.write_text(json.dumps({'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [145, -36]},
             'properties': {'job_token': ' Raw Vendor JOB ', 'date_token': '20270115', 'units': 'gal?'}}]}))
        original = source.read_bytes()
        window = QMainWindow()
        class Interface:
            def mainWindow(self): return window
        dialog = ImportDialog(Interface())
        dialog.show_result(scan_local(source))
        row = dialog.rows()[0]
        dialog.set_plan(row, {'field_id': field}, 'Ready')
        dialog.tree.setCurrentItem(row)
        before = store.records(root)
        project_bytes = (root / 'Farm.qgz').read_bytes()
        db_bytes = store.database(root).read_bytes()
        assert hasattr(dialog, 'season_preview_button'), 'Actual Data In must expose its read-only season preview'
        assert dialog.season_preview_button.isEnabled()
        preview = dialog.create_season_preview()
        assert preview is not None
        assert preview.source.text() == row.data(0, Qt.UserRole)['uri']
        assert preview.job_date.text() == '', 'Do not infer a date from file, arbitrary column or import time'
        assert preview.operation.currentData() == 'unknown'
        assert 'Raw Vendor JOB' in preview.attributes.toPlainText()
        assert 'gal?' in preview.attributes.toPlainText()
        preview.job_date.setText('2027-01-15')
        preview.operation.setCurrentIndex(preview.operation.findData('planting'))
        preview.refresh_preview()
        assert preview.review['season_id'] == summer
        assert preview.timeline.topLevelItem(0).text(0) == 'Z Summer 2026/27'
        assert 'Preview only' in preview.notice.text()
        preview.job_date.setText('2027-02-30')
        preview.refresh_preview()
        assert preview.review is None and 'YYYY-MM-DD' in preview.result.text(), 'Invalid edit must clear earlier matching result'
        preview.reject()
        # The actual button opens the same modal, and Close has no write action.
        from qgis.PyQt.QtCore import QTimer
        opened = []
        def close_modal():
            from qgis.PyQt.QtWidgets import QApplication
            modal = QApplication.activeModalWidget()
            assert modal is not None and modal.windowTitle() == 'Ag-GIS — Preview Job Season'
            opened.append(True)
            modal.reject()
        QTimer.singleShot(0, close_modal)
        dialog.season_preview_button.click()
        assert opened == [True]
        # A pending new field has no persisted timeline: never borrow another one.
        row.setData(0, Qt.UserRole + 1, {'names': dict(organisation='Org', client='Client', farm='Home', field='New')})
        dialog.update_add()
        assert not dialog.season_preview_button.isEnabled()
        assert dialog.create_season_preview() is None
        dialog.set_plan(row, {'field_id': field}, 'Ready')
        dialog.update_add()
        assert dialog.season_preview_button.isEnabled()
        from qgis.PyQt.QtWidgets import QTreeWidgetItem
        metadata_row = QTreeWidgetItem(dialog.tree, ['Unsupported machine metadata'])
        dialog.tree.setCurrentItem(metadata_row)
        assert not dialog.season_preview_button.isEnabled(), 'Metadata-only rows must not retain a native-layer season action'
        assert before == store.records(root), 'Review must not modify hierarchy'
        assert store.database(root).read_bytes() == db_bytes
        assert (root / 'Farm.qgz').read_bytes() == project_bytes
        assert source.read_bytes() == original
        assert not any(layer.customProperty('AgTechTooling/dataset_id') for layer in project.mapLayers().values())
        dialog.reject()
        # Parent-owned Qt editors retain native layer wrappers until deletion.
        from qgis.PyQt import sip
        sip.delete(dialog)
        sip.delete(window)
        del preview, dialog, window
        project.clear()
        from qgis.PyQt.QtCore import QCoreApplication, QEvent
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        gc.collect()
    gc.collect()

try:
    check()
finally:
    QgsProject.instance().clear()
    gc.collect()
    app.exitQgis()
print('Asserted read-only cross-year Data In season review passed')
