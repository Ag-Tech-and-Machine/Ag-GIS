"""Real Data In season preview: field-scoped, dated, read-only and conservative."""

import gc

import json

import os

from pathlib import Path

import sys

import tempfile



os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

    pass  # QGIS not available, skip this test

except ImportError:

            from qgis.PyQt.QtCore import QCoreApplication, QEvent

            project.clear()

            del preview, dialog, window

            sip.delete(window)

            sip.delete(dialog)

            from qgis.PyQt import sip

            # Parent-owned Qt editors retain native layer wrappers until deletion.

            dialog.reject()

            assert not any(layer.customProperty('AgTechTooling/dataset_id') for layer in project.mapLayers().values())

            assert source.read_bytes() == original

            assert (root / 'Farm.qgz').read_bytes() == project_bytes

            assert store.database(root).read_bytes() == db_bytes

            assert before == store.records(root), 'Review must not modify hierarchy'

            assert not dialog.season_preview_button.isEnabled(), 'Metadata-only rows must not retain a native-layer season action'

            dialog.tree.setCurrentItem(metadata_row)

            metadata_row = QTreeWidgetItem(dialog.tree, ['Unsupported machine metadata'])

            from qgis.PyQt.QtWidgets import QTreeWidgetItem

            assert dialog.season_preview_button.isEnabled()

            dialog.update_add()

            dialog.set_plan(row, {'field_id': field}, 'Ready')

            assert dialog.create_season_preview() is None

            assert not dialog.season_preview_button.isEnabled()

            dialog.update_add()

            row.setData(0, Qt.UserRole + 1, {'names': dict(organisation='Org', client='Client', farm='Home', field='New')})

            # A pending new field has no persisted timeline: never borrow another one.

            assert opened == [True]

            dialog.season_preview_button.click()

            QTimer.singleShot(0, close_modal)

                modal.reject()

                opened.append(True)

                assert modal is not None and modal.windowTitle() == 'Ag-GIS — Preview Job Season'

                modal = QApplication.activeModalWidget()

                from qgis.PyQt.QtWidgets import QApplication

            def close_modal():

            opened = []

            from qgis.PyQt.QtCore import QTimer

            # The actual button opens the same modal, and Close has no write action.

            preview.reject()

            assert preview.review is None and 'YYYY-MM-DD' in preview.result.text(), 'Invalid edit must clear earlier matching result'

            preview.refresh_preview()

            preview.job_date.setText('2027-02-30')

            assert 'Preview only' in preview.notice.text()

            assert preview.timeline.topLevelItem(0).text(0) == 'Z Summer 2026/27'

            assert preview.review['season_id'] == summer

            preview.refresh_preview()

            preview.operation.setCurrentIndex(preview.operation.findData('planting'))

            preview.job_date.setText('2027-01-15')

            assert 'gal?' in preview.attributes.toPlainText()

            assert 'Raw Vendor JOB' in preview.attributes.toPlainText()

            assert preview.operation.currentData() == 'unknown'

            assert preview.job_date.text() == '', 'Do not infer a date from file, arbitrary column or import time'

            assert preview.source.text() == row.data(0, Qt.UserRole)['uri']

            assert preview is not None

            preview = dialog.create_season_preview()

            assert dialog.season_preview_button.isEnabled()

            assert hasattr(dialog, 'season_preview_button'), 'Actual Data In must expose its read-only season preview'

            db_bytes = store.database(root).read_bytes()

            project_bytes = (root / 'Farm.qgz').read_bytes()

            before = store.records(root)

            dialog.tree.setCurrentItem(row)

            dialog.set_plan(row, {'field_id': field}, 'Ready')

            row = dialog.rows()[0]

            dialog.show_result(scan_local(source))

            dialog = ImportDialog(Interface())

                def mainWindow(self): return window

            class Interface:

            window = QMainWindow()

            original = source.read_bytes()

                 'properties': {'job_token': ' Raw Vendor JOB ', 'date_token': '20270115', 'units': 'gal?'}}]}))

                {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [145, -36]},

            source.write_text(json.dumps({'type': 'FeatureCollection', 'features': [

            source = Path(temporary) / 'Operation.geojson'

            # Supported adapter is the real native GeoJSON scanner, not GS3 metadata.

            dates(winter, '2027-04-01', '2027-09-30')

            dates(summer, '2026-10-01', '2027-03-31')

            rejected('9999-01-15', contains='gap or overlap')

            dates(winter, '9999-12-31', '9999-12-31')

            dates(summer, '9999-01-01', '9999-12-31')

            rejected('2027-01-15', contains='valid start and end')

            dates(winter, '', '')

            rejected('2027-01-15', contains='gap or overlap')

            dates(winter, '2027-03-31', '2027-09-30')

            rejected('2027-01-15', contains='gap or overlap')

            dates(winter, '2027-04-02', '2027-09-30')

                        conn.execute('UPDATE agtech_seasons SET start_date=?,end_date=? WHERE id=?', (start, end, identifier))

                    with conn:

                with closing(sqlite3.connect(store.database(root))) as conn:

            def dates(identifier, start, end):

            from contextlib import closing

            import sqlite3

            assert placement.review_job_season(root, field, '2027-01-15', 'tillage')['season_id'] == summer

            store.add_record(root, 'season', 'Undated elsewhere', unrelated)

            unrelated = placement.ensure_field(root, dict(organisation='Org', client='Client', farm='Home', field='Other'))

            rejected('2027-10-01', contains='outside')

            rejected('2026-09-30', contains='outside')

            rejected('2027-01-15', target='missing', contains='existing field')

            rejected('2027-01-15', operation=' VendorX ', contains='Unknown')

                rejected(day, contains='YYYY-MM-DD')

            for day in ('', '20270230', '2027-02-30', '2027-1-15', ' 2027-01-15', '2027-01-15T12:00:00'):

                    raise AssertionError('Unsafe season review accepted')

                else:

                    assert contains in str(error), str(error)

                except ValueError as error:

                    placement.review_job_season(root, target, day, operation)

                try:

            def rejected(day, operation='planting', target=field, contains=''):

            # Full-field timeline must be safe, not merely the matching interval.

            assert placement.review_job_season(root, field, '2027-04-01', 'spraying')['season_id'] == winter

            assert placement.review_job_season(root, field, '2027-03-31', 'spraying')['season_id'] == summer

            assert [r['id'] for r in result['timeline']] == [summer, winter]

            assert result['season_id'] == summer and result['operation_subtype'] == 'planting'

            result = placement.review_job_season(root, field, '2027-01-15', 'planting')

            winter = store.add_record(root, 'season', 'A Winter 2027', field, start='2027-04-01', end='2027-09-30')

            summer = store.add_record(root, 'season', 'Z Summer 2026/27', field, start='2026-10-01', end='2027-03-31')

            # Reverse name order must not change chronological matching across New Year.

            field = store.records(root)['field'][0]['id']

            assert project.read(str(root / 'Farm.qgz'))

            project = QgsProject.instance()

                               organisation='Org', client='Client', farm='Home', field='North')

            root = create_farm(Path(temporary), 'Synthetic', QgsCoordinateReferenceSystem('EPSG:4326'),

        with tempfile.TemporaryDirectory(prefix='aggis-season-review-') as temporary:

        assert hasattr(placement, 'review_job_season'), 'Data In needs a field-scoped date/type season review, not guessed placement'

    def check():

    

    

    app.initQgis()

    app = QgsApplication([], False)

    

    from ag_tech_tooling.import_sources import scan_local

    from ag_tech_tooling.import_dialog import ImportDialog

    from ag_tech_tooling.farm_project import create_farm

    from ag_tech_tooling import hierarchy as store, import_placement as placement

    from qgis.PyQt.QtWidgets import QMainWindow

    from qgis.PyQt.QtCore import Qt

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsProject
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

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


