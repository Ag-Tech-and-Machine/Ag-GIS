"""Linked boundary preview/application through real native managed imports and UI."""

import gc

import json

import os

from pathlib import Path

import sys

import tempfile



os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT', str(Path(__file__).resolve().parents[1] / 'plugins')))

    pass  # QGIS not available, skip this test

except ImportError:

        from qgis.PyQt.QtCore import QCoreApplication, QEvent

        QgsProject.instance().clear()

    finally:

        exercise(temporary.name)

    try:

    temporary = tempfile.TemporaryDirectory(prefix='aggis-boundary-')

    

        gc.collect()

        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        from qgis.PyQt.QtCore import QCoreApplication, QEvent

        project.clear()

        del reference_layer, reference_result, layer, result

        assert source.read_bytes() == original

        rejected(summer, '2027-03-30', 'missing or belongs', expected=current_timeline)

                conn.execute('UPDATE agtech_datasets SET classification_id=? WHERE id=?', ('missing', reference_result[0]['id']))

            with conn:

        with closing(sqlite3.connect(store.database(root))) as conn:

        # Unsupported/missing classification pointers must not be advertised as zero impact.

        del virtual, virtual_result

        refuse_apply(virtual_impact, 'unavailable locally')

        virtual_impact = preview_boundary(root, summer, '2027-03-30', expected_timeline=current_timeline)

        assert virtual_result

        virtual_result = managed.save_dataset(root, virtual, field, 'data', review=virtual_review)

        virtual_review = prepare_review(root, virtual, placement.review_job_season(root, field, '2027-03-31', 'planting'))

        assert virtual.isValid()

        virtual = QgsVectorLayer(str(vrt), 'Virtual job', 'ogr')

                       escape(str(source)) + '</SrcDataSource><SrcLayer>Job</SrcLayer></OGRVRTLayer></OGRVRTDataSource>')

        vrt.write_text('<OGRVRTDataSource><OGRVRTLayer name="Job"><SrcDataSource>' +

        vrt = Path(temporary) / 'Job.vrt'

        from xml.sax.saxutils import escape

        # without changing its XML, or contact a service when reopened. Refuse Apply.

        # A local OGR VRT is not a verified source bundle: referenced content may change

                conn.execute("CREATE TRIGGER agtech_boundary_no_delete BEFORE DELETE ON agtech_season_boundary_decisions BEGIN SELECT RAISE(ABORT,'Season boundary decisions are immutable'); END")

                conn.execute("DELETE FROM agtech_season_boundary_decisions WHERE id='future'")

                conn.execute('DROP TRIGGER agtech_boundary_no_delete')

            with conn:

        with closing(sqlite3.connect(store.database(root))) as conn:

        # Remove only this deliberately invalid synthetic audit through rollback-style fixture rebuild.

        rejected(summer, '2027-03-30', 'supported reader', expected=current_timeline)

                conn.execute("INSERT INTO agtech_season_boundary_decisions VALUES ('future','future',?,'now','{}')", (field,))

            with conn:

        with closing(sqlite3.connect(store.database(root))) as conn:

        # Unknown future audit contract refuses further previews/application.

                else: raise AssertionError('Audit history was mutable')

                except sqlite3.IntegrityError as error: assert 'immutable' in str(error)

                    with conn: conn.execute(sql)

                try:

            for sql in ('UPDATE agtech_season_boundary_decisions SET contract=contract', 'DELETE FROM agtech_season_boundary_decisions'):

        with closing(sqlite3.connect(store.database(root))) as conn:

            locked.rollback()

            refuse_apply(fresh, 'locked')

            locked.execute('BEGIN IMMEDIATE')

        with closing(sqlite3.connect(store.database(root))) as locked:

        # Busy writer fails rather than overriding; keep the five-second SQLite timeout.

                with conn: conn.execute('DROP TRIGGER injected_boundary_failure')

            with closing(sqlite3.connect(store.database(root))) as conn:

            refuse_apply(fresh, 'Injected')

                with conn: conn.execute(trigger)

            with closing(sqlite3.connect(store.database(root))) as conn:

            "CREATE TRIGGER injected_boundary_failure BEFORE INSERT ON agtech_season_boundary_decisions BEGIN SELECT RAISE(ABORT,'Injected audit failure'); END"):

            f"CREATE TRIGGER injected_boundary_failure BEFORE UPDATE ON agtech_seasons WHEN OLD.id='{winter}' BEGIN SELECT RAISE(ABORT,'Injected paired-date failure'); END",

        for trigger in (

        # Fail the second date write and the final receipt separately: complete rollback.

                conn.execute('UPDATE agtech_datasets SET name=? WHERE id=?', (result[0]['name'], result[0]['id']))

            with conn:

        with closing(sqlite3.connect(store.database(root))) as conn:

        refuse_apply(fresh, 'history or source identity changed')

                conn.execute('UPDATE agtech_datasets SET name=? WHERE id=?', ('Changed job label', result[0]['id']))

            with conn:

        with closing(sqlite3.connect(store.database(root))) as conn:

        assert store.database(root).read_bytes() == before

        finally: moved.rename(source)

        else: raise AssertionError('Missing source accepted')

            assert 'unavailable locally' in str(error)

        except ValueError as error:

            boundary_api.apply_boundary(root, fresh, history_decision='retain-recorded')

        try:

        before = store.database(root).read_bytes()

        moved = source.with_suffix('.moved');source.rename(moved)

        gc.collect()

        layer = None

        # Release the test-owned original provider before Windows file-absence probe.

        source.write_bytes(original);source_bytes[0] = original

        refuse_apply(fresh, 'source changed')

        source.write_bytes(original + b' ');source_bytes[0] = source.read_bytes()

        refuse_apply(tampered, 'history or source identity changed')

        tampered = json.loads(json.dumps(fresh));tampered['history'][0]['recorded_season_id'] = winter

        refuse_apply(reviewed, 'changed')  # prior decision invalidates old consent even after date restoration

        refuse_apply(fresh, 'Explicitly keep', 'move-jobs')

        refuse_apply(fresh, 'Explicitly keep', '')

        fresh = preview_boundary(root, summer, '2027-03-30', expected_timeline=current_timeline)

        source_bytes = [original]

            assert source.read_bytes() == source_bytes[0]

            assert store.database(root).read_bytes() == before

                raise AssertionError('Unsafe boundary application accepted')

            else:

                assert contains in str(error), str(error)

            except (ValueError, sqlite3.Error) as error:

                boundary_api.apply_boundary(root, reviewed, history_decision=decision)

            try:

            before = store.database(root).read_bytes()

        def refuse_apply(reviewed, contains, decision='retain-recorded'):

        # Replay, missing acknowledgement, altered review and fresh identity refusals.

            with conn: conn.execute('UPDATE agtech_datasets SET name=? WHERE id=?', (result[0]['name'], result[0]['id']))

        with closing(sqlite3.connect(store.database(root))) as conn:

        sip.delete(modal)

        assert 'Not applied' in modal.result.text() and store.database(root).read_bytes() == confirm_snapshot[0]

        assert modal.decision is None and modal.preview is None and not modal.apply_button.isEnabled()

        modal.apply_button.click()

        QTimer.singleShot(0, stale_confirmation)

            QApplication.activeModalWidget().button(QMessageBox.Yes).click()

            from qgis.PyQt.QtWidgets import QMessageBox

            confirm_snapshot.append(store.database(root).read_bytes())

                with conn: conn.execute('UPDATE agtech_datasets SET name=? WHERE id=?', ('Changed during confirmation', result[0]['id']))

            with closing(sqlite3.connect(store.database(root))) as conn:

        def stale_confirmation():

        confirm_snapshot = []

        modal.keep_jobs.setChecked(True)

        assert not modal.keep_jobs.isChecked() and not modal.apply_button.isEnabled()

        modal.end.setDate(QDate(2027, 3, 29))

        modal.end.setDate(QDate(2027, 3, 30));modal.keep_jobs.setChecked(True)

        modal = hierarchy_dialog.SeasonBoundaryPreview(root, summer)

        # Changing proposal clears acknowledgement; changing history during confirmation refuses.

        current_timeline = store.records(root)['season']

        boundary_api.apply_boundary(root, preview_boundary(root, summer, '2027-03-31', expected_timeline=store.records(root)['season']), history_decision='retain-recorded')

        sip.delete(modal)

        assert modal.decision['history_decision'] == 'retain-recorded'

        modal.apply_button.click()

        QTimer.singleShot(0, accept_confirmation)

            box.button(QMessageBox.Yes).click()

            assert 'recorded seasons' in box.text()

            from qgis.PyQt.QtWidgets import QMessageBox

            box = QApplication.activeModalWidget()

        def accept_confirmation():

        assert store.database(root).read_bytes() == before_cancel

        assert modal.isVisible() is False  # not exec'd by this direct API harness

        modal.apply_button.click()

        QTimer.singleShot(0, cancel_confirmation)

            box.button(QMessageBox.Cancel).click()

            assert isinstance(box, QMessageBox) and box.defaultButton() == box.button(QMessageBox.Cancel)

            from qgis.PyQt.QtWidgets import QMessageBox

            box = QApplication.activeModalWidget()

        def cancel_confirmation():

        before_cancel = store.database(root).read_bytes()

        assert modal.apply_button.isEnabled()

        modal.keep_jobs.setChecked(True)

        assert not modal.keep_jobs.isChecked() and not modal.apply_button.isEnabled()

        modal.end.setDate(QDate(2027, 3, 30))

        assert hasattr(modal, 'apply_button'), 'Boundary review needs an explicit farmer-facing apply control'

        modal = hierarchy_dialog.SeasonBoundaryPreview(root, summer)

        # The real modal requires an unchecked retain-history acknowledgement.

        current_timeline = store.records(root)['season']

        boundary_api.apply_boundary(root, preview_boundary(root, summer, '2027-03-31', expected_timeline=saved), history_decision='retain-recorded')

        # Restore only this synthetic fixture using another explicit audited review.

        assert (root / 'Farm.qgz').read_bytes() == before_map and source.read_bytes() == original

            assert conn.execute('SELECT * FROM agtech_datasets').fetchall() == catalogue_before

            assert conn.execute('SELECT * FROM agtech_classifications').fetchall() == history_before

            assert json.loads(audit[0]) == receipt

            audit = conn.execute('SELECT decision_json FROM agtech_season_boundary_decisions WHERE id=?', (receipt['id'],)).fetchone()

        with closing(sqlite3.connect(store.database(root))) as conn:

        assert receipt['contract'] == 'season-boundary-decision-v1' and receipt['history_decision'] == 'retain-recorded'

        assert next(r for r in saved if r['id'] == winter)['start_date'] == '2027-03-31'

        assert next(r for r in saved if r['id'] == summer)['end_date'] == '2027-03-30'

        saved = store.records(root)['season']

        receipt = boundary_api.apply_boundary(root, reviewed, history_decision='retain-recorded')

            catalogue_before = conn.execute('SELECT * FROM agtech_datasets').fetchall()

            history_before = conn.execute('SELECT * FROM agtech_classifications').fetchall()

        with closing(sqlite3.connect(store.database(root))) as conn:

        reviewed = preview_boundary(root, summer, '2027-03-30', expected_timeline=current_timeline)

        assert hasattr(boundary_api, 'apply_boundary'), 'Reviewed paired season dates need a durable apply action'

        import ag_tech_tooling.season_boundary as boundary_api

        # Applying a reviewed pair is explicit and durable; historic jobs stay pinned.

        assert impact['unreviewed_count'] == 1 and len(impact['history']) == 1

        impact = preview_boundary(root, summer, '2027-03-30', expected_timeline=current_timeline)

        current_timeline = store.records(root)['season']

        reference_result = managed.save_dataset(root, reference_layer, field, 'data')

        reference_layer = QgsVectorLayer(str(reference), 'Reference', 'ogr')

        reference.write_bytes(original)

        reference = Path(temporary) / 'Reference.geojson'

        # Unreviewed Whole Field data is counted explicitly, never assigned a date.

        set_start('2027-04-01')

        sip.delete(modal)

        modal.reject()

        assert modal.preview is None and modal.history.topLevelItemCount() == 0 and modal.timeline.topLevelItemCount() == 0

        modal.refresh_preview()

        set_start('2027-04-02')

        assert modal.preview is not None

        modal = hierarchy_dialog.SeasonBoundaryPreview(root, summer)

        # UI clears its previous rows/result on a stale timeline rather than retaining an estimate.

        rejected(summer, '2027-03-30', 'timeline changed')

                conn.execute('UPDATE agtech_seasons SET name=? WHERE id=?', ('Renamed Winter', winter))

            with conn:

        with closing(sqlite3.connect(store.database(root))) as conn:

        set_start('2027-04-01')

            rejected(summer, '2027-03-30', 'valid start and end' if not start else 'gap or overlap')

            set_start(start)

        for start in ('2027-04-02', '2027-03-31', ''):

                    conn.execute('UPDATE agtech_seasons SET start_date=? WHERE id=?', (value, winter))

                with conn:

            with closing(sqlite3.connect(store.database(root))) as conn:

        def set_start(value):

        from contextlib import closing

        import sqlite3

        assert preview_boundary(root, summer, '2027-03-30', expected_timeline=timeline)['affected_count'] == 1

        store.add_record(root, 'season', 'Other undated', other)

        other = placement.ensure_field(root, dict(organisation='Org', client='Client', farm='Home', field='Other'))

        # Another field's incomplete dates never contaminate this field's timeline.

        assert preview_boundary(root, summer, '2026-10-01', expected_timeline=timeline)['proposed_timeline'][0]['start_date'] == '2026-10-01'

        assert preview_boundary(root, summer, '2027-03-31', expected_timeline=timeline)['affected_count'] == 0

        assert preview_boundary(root, summer, '2026-12-31', expected_timeline=timeline)['proposed_timeline'][1]['start_date'] == '2027-01-01'

        rejected('missing', '2027-03-30', 'existing season')

        rejected(winter, '2027-08-31', 'last season')

            rejected(summer, proposed, 'at least one day')

        for proposed in ('2026-09-30', '2027-09-30', '9999-12-31'):

            rejected(summer, proposed, 'YYYY-MM-DD')

        for proposed in ('20270330', '2027-3-30', '2027-02-30', '', None, ' 2027-03-30'):

            assert store.database(root).read_bytes() == prior

                raise AssertionError('Unsafe boundary preview accepted')

            else:

                assert contains in str(error), str(error)

            except ValueError as error:

                preview_boundary(root, identifier, proposed, expected_timeline=expected)

            try:

            prior = store.database(root).read_bytes()

        def rejected(identifier, proposed, contains, expected=timeline):

        # Strict inclusive endpoints, cross-year boundaries, last/missing selection.

        sip.delete(window)

        sip.delete(dialog)

        dialog.reject()

        assert store.database(root).read_bytes() == before_db and (root / 'Farm.qgz').read_bytes() == before_map

        assert opened == [True]

        if errors: raise errors[0]

        dialog.boundary_button.click()

        QTimer.singleShot(0, inspect_modal)

                modal.reject()

            finally:

                errors.append(error)

            except BaseException as error:

                opened.append(True)

                assert 'Preview only' in modal.notice.text()

                assert modal.history.topLevelItem(0).text(4) == 'A Winter 2027'

                assert modal.history.topLevelItem(0).text(3) == 'Z Summer 2026/27'

                assert modal.preview['affected_count'] == 1

                modal.end.setDate(QDate(2027, 3, 30))

                assert isinstance(modal, hierarchy_dialog.SeasonBoundaryPreview)

            try:

            modal = QApplication.activeModalWidget()

        def inspect_modal():

        opened, errors = [], []

        assert dialog.boundary_button.isEnabled()

        del iterator

            iterator += 1

                break

                dialog.tree.setCurrentItem(item)

            if item.data(0, Qt.UserRole) == ('season', summer):

            item = iterator.value()

        while iterator.value():

        iterator = QTreeWidgetItemIterator(dialog.tree)

        assert not dialog.boundary_button.isEnabled()

        assert hasattr(dialog, 'boundary_button'), 'Manage Farm Data must wire Preview Season Boundary to the selected season'

        dialog = hierarchy_dialog.HierarchyDialog(root, Interface())

            def mainWindow(self): return window

        class Interface:

        window = QMainWindow()

        from qgis.PyQt import sip

        from qgis.PyQt.QtCore import QDate, Qt, QTimer

        from qgis.PyQt.QtWidgets import QMainWindow, QTreeWidgetItemIterator, QApplication

        # A real Manage Data selection/button/modal exposes the same read-only result.

        assert (root / 'Farm.qgz').read_bytes() == before_map and source.read_bytes() == original

        assert store.database(root).read_bytes() == before_db

        assert store.records(root)['season'] == timeline

        assert impact['affected_count'] == 1

        assert job['affected'] is True

        assert job['job_date'] == '2027-03-31' and job['operation_subtype'] == 'planting'

        assert job['recorded_season_id'] == summer and job['proposed_season_id'] == winter

        job = impact['history'][0]

        assert len(impact['history']) == 1

        assert impact['proposed_timeline'][1]['start_date'] == '2027-03-31'

        assert impact['proposed_timeline'][0]['end_date'] == '2027-03-30'

        assert [r['id'] for r in impact['proposed_timeline']] == [summer, winter]

        impact = preview_boundary(root, summer, '2027-03-30', expected_timeline=timeline)

        timeline = store.records(root)['season']

        before_map = (root / 'Farm.qgz').read_bytes()

        before_db = store.database(root).read_bytes()

        assert result

        result = managed.save_dataset(root, layer, field, 'data', review=review)

        review = prepare_review(root, layer, placement.review_job_season(root, field, '2027-03-31', 'planting'))

        from ag_tech_tooling.reviewed_import import prepare_review

        layer = QgsVectorLayer(str(source), 'Job', 'ogr')

        original = source.read_bytes()

            'geometry':{'type':'Point','coordinates':[145,-36]},'properties':{'units':'gal?','token':' Raw JOB '}}]}))

        source.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature',

        source = Path(temporary) / 'Job.geojson'

        winter = store.add_record(root, 'season', 'A Winter 2027', field, start='2027-04-01', end='2027-09-30')

        summer = store.add_record(root, 'season', 'Z Summer 2026/27', field, start='2026-10-01', end='2027-03-31')

        field = store.records(root)['field'][0]['id']

        assert project.read(str(root / 'Farm.qgz'))

        project = QgsProject.instance()

                           organisation='Org', client='Client', farm='Home', field='North')

        root = create_farm(Path(temporary), 'Synthetic', QgsCoordinateReferenceSystem('EPSG:4326'),

        from ag_tech_tooling.season_boundary import preview_boundary

        assert hasattr(hierarchy_dialog, 'SeasonBoundaryPreview'), 'Manage Farm Data needs a read-only linked boundary impact preview'

        from ag_tech_tooling import hierarchy_dialog

    def exercise(temporary):

    

    

    app.initQgis()

    app = QgsApplication([], False)

    

    from ag_tech_tooling.farm_project import create_farm

    from ag_tech_tooling import hierarchy as store, managed_data as managed, import_placement as placement

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsProject, QgsVectorLayer
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    gc.collect()

    app.exitQgis()

    temporary.cleanup()

print('Asserted linked boundary preview/apply, keep-history, stale/source refusals and transactional rollback passed')


