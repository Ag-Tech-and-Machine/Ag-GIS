"""Linked boundary preview/application through real native managed imports and UI."""
import gc
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.environ.get('AGTECH_TEST_PLUGIN_ROOT', str(Path(__file__).resolve().parents[1] / 'plugins')))
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsProject, QgsVectorLayer
from ag_tech_tooling import hierarchy as store, managed_data as managed, import_placement as placement
from ag_tech_tooling.farm_project import create_farm

app = QgsApplication([], False)
app.initQgis()


def exercise(temporary):
    from ag_tech_tooling import hierarchy_dialog
    assert hasattr(hierarchy_dialog, 'SeasonBoundaryPreview'), 'Manage Farm Data needs a read-only linked boundary impact preview'
    from ag_tech_tooling.season_boundary import preview_boundary
    root = create_farm(Path(temporary), 'Synthetic', QgsCoordinateReferenceSystem('EPSG:4326'),
                       organisation='Org', client='Client', farm='Home', field='North')
    project = QgsProject.instance()
    assert project.read(str(root / 'Farm.qgz'))
    field = store.records(root)['field'][0]['id']
    summer = store.add_record(root, 'season', 'Z Summer 2026/27', field, start='2026-10-01', end='2027-03-31')
    winter = store.add_record(root, 'season', 'A Winter 2027', field, start='2027-04-01', end='2027-09-30')
    source = Path(temporary) / 'Job.geojson'
    source.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature',
        'geometry':{'type':'Point','coordinates':[145,-36]},'properties':{'units':'gal?','token':' Raw JOB '}}]}))
    original = source.read_bytes()
    layer = QgsVectorLayer(str(source), 'Job', 'ogr')
    from ag_tech_tooling.reviewed_import import prepare_review
    review = prepare_review(root, layer, placement.review_job_season(root, field, '2027-03-31', 'planting'))
    result = managed.save_dataset(root, layer, field, 'data', review=review)
    assert result
    before_db = store.database(root).read_bytes()
    before_map = (root / 'Farm.qgz').read_bytes()
    timeline = store.records(root)['season']
    impact = preview_boundary(root, summer, '2027-03-30', expected_timeline=timeline)
    assert [r['id'] for r in impact['proposed_timeline']] == [summer, winter]
    assert impact['proposed_timeline'][0]['end_date'] == '2027-03-30'
    assert impact['proposed_timeline'][1]['start_date'] == '2027-03-31'
    assert len(impact['history']) == 1
    job = impact['history'][0]
    assert job['recorded_season_id'] == summer and job['proposed_season_id'] == winter
    assert job['job_date'] == '2027-03-31' and job['operation_subtype'] == 'planting'
    assert job['affected'] is True
    assert impact['affected_count'] == 1
    assert store.records(root)['season'] == timeline
    assert store.database(root).read_bytes() == before_db
    assert (root / 'Farm.qgz').read_bytes() == before_map and source.read_bytes() == original
    # A real Manage Data selection/button/modal exposes the same read-only result.
    from qgis.PyQt.QtWidgets import QMainWindow, QTreeWidgetItemIterator, QApplication
    from qgis.PyQt.QtCore import QDate, Qt, QTimer
    from qgis.PyQt import sip
    window = QMainWindow()
    class Interface:
        def mainWindow(self): return window
    dialog = hierarchy_dialog.HierarchyDialog(root, Interface())
    assert hasattr(dialog, 'boundary_button'), 'Manage Farm Data must wire Preview Season Boundary to the selected season'
    assert not dialog.boundary_button.isEnabled()
    iterator = QTreeWidgetItemIterator(dialog.tree)
    while iterator.value():
        item = iterator.value()
        if item.data(0, Qt.UserRole) == ('season', summer):
            dialog.tree.setCurrentItem(item)
            break
        iterator += 1
    del iterator
    assert dialog.boundary_button.isEnabled()
    opened, errors = [], []
    def inspect_modal():
        modal = QApplication.activeModalWidget()
        try:
            assert isinstance(modal, hierarchy_dialog.SeasonBoundaryPreview)
            modal.end.setDate(QDate(2027, 3, 30))
            assert modal.preview['affected_count'] == 1
            assert modal.history.topLevelItem(0).text(3) == 'Z Summer 2026/27'
            assert modal.history.topLevelItem(0).text(4) == 'A Winter 2027'
            assert 'Preview only' in modal.notice.text()
            opened.append(True)
        except BaseException as error:
            errors.append(error)
        finally:
            modal.reject()
    QTimer.singleShot(0, inspect_modal)
    dialog.boundary_button.click()
    if errors: raise errors[0]
    assert opened == [True]
    assert store.database(root).read_bytes() == before_db and (root / 'Farm.qgz').read_bytes() == before_map
    dialog.reject()
    sip.delete(dialog)
    sip.delete(window)
    # Strict inclusive endpoints, cross-year boundaries, last/missing selection.
    def rejected(identifier, proposed, contains, expected=timeline):
        prior = store.database(root).read_bytes()
        try:
            preview_boundary(root, identifier, proposed, expected_timeline=expected)
        except ValueError as error:
            assert contains in str(error), str(error)
        else:
            raise AssertionError('Unsafe boundary preview accepted')
        assert store.database(root).read_bytes() == prior
    for proposed in ('20270330', '2027-3-30', '2027-02-30', '', None, ' 2027-03-30'):
        rejected(summer, proposed, 'YYYY-MM-DD')
    for proposed in ('2026-09-30', '2027-09-30', '9999-12-31'):
        rejected(summer, proposed, 'at least one day')
    rejected(winter, '2027-08-31', 'last season')
    rejected('missing', '2027-03-30', 'existing season')
    assert preview_boundary(root, summer, '2026-12-31', expected_timeline=timeline)['proposed_timeline'][1]['start_date'] == '2027-01-01'
    assert preview_boundary(root, summer, '2027-03-31', expected_timeline=timeline)['affected_count'] == 0
    assert preview_boundary(root, summer, '2026-10-01', expected_timeline=timeline)['proposed_timeline'][0]['start_date'] == '2026-10-01'
    # Another field's incomplete dates never contaminate this field's timeline.
    other = placement.ensure_field(root, dict(organisation='Org', client='Client', farm='Home', field='Other'))
    store.add_record(root, 'season', 'Other undated', other)
    assert preview_boundary(root, summer, '2027-03-30', expected_timeline=timeline)['affected_count'] == 1
    import sqlite3
    from contextlib import closing
    def set_start(value):
        with closing(sqlite3.connect(store.database(root))) as conn:
            with conn:
                conn.execute('UPDATE agtech_seasons SET start_date=? WHERE id=?', (value, winter))
    for start in ('2027-04-02', '2027-03-31', ''):
        set_start(start)
        rejected(summer, '2027-03-30', 'valid start and end' if not start else 'gap or overlap')
    set_start('2027-04-01')
    with closing(sqlite3.connect(store.database(root))) as conn:
        with conn:
            conn.execute('UPDATE agtech_seasons SET name=? WHERE id=?', ('Renamed Winter', winter))
    rejected(summer, '2027-03-30', 'timeline changed')
    # UI clears its previous rows/result on a stale timeline rather than retaining an estimate.
    modal = hierarchy_dialog.SeasonBoundaryPreview(root, summer)
    assert modal.preview is not None
    set_start('2027-04-02')
    modal.refresh_preview()
    assert modal.preview is None and modal.history.topLevelItemCount() == 0 and modal.timeline.topLevelItemCount() == 0
    modal.reject()
    sip.delete(modal)
    set_start('2027-04-01')
    # Unreviewed Whole Field data is counted explicitly, never assigned a date.
    reference = Path(temporary) / 'Reference.geojson'
    reference.write_bytes(original)
    reference_layer = QgsVectorLayer(str(reference), 'Reference', 'ogr')
    reference_result = managed.save_dataset(root, reference_layer, field, 'data')
    current_timeline = store.records(root)['season']
    impact = preview_boundary(root, summer, '2027-03-30', expected_timeline=current_timeline)
    assert impact['unreviewed_count'] == 1 and len(impact['history']) == 1
    # Applying a reviewed pair is explicit and durable; historic jobs stay pinned.
    import ag_tech_tooling.season_boundary as boundary_api
    assert hasattr(boundary_api, 'apply_boundary'), 'Reviewed paired season dates need a durable apply action'
    reviewed = preview_boundary(root, summer, '2027-03-30', expected_timeline=current_timeline)
    with closing(sqlite3.connect(store.database(root))) as conn:
        history_before = conn.execute('SELECT * FROM agtech_classifications').fetchall()
        catalogue_before = conn.execute('SELECT * FROM agtech_datasets').fetchall()
    receipt = boundary_api.apply_boundary(root, reviewed, history_decision='retain-recorded')
    saved = store.records(root)['season']
    assert next(r for r in saved if r['id'] == summer)['end_date'] == '2027-03-30'
    assert next(r for r in saved if r['id'] == winter)['start_date'] == '2027-03-31'
    assert receipt['contract'] == 'season-boundary-decision-v1' and receipt['history_decision'] == 'retain-recorded'
    with closing(sqlite3.connect(store.database(root))) as conn:
        audit = conn.execute('SELECT decision_json FROM agtech_season_boundary_decisions WHERE id=?', (receipt['id'],)).fetchone()
        assert json.loads(audit[0]) == receipt
        assert conn.execute('SELECT * FROM agtech_classifications').fetchall() == history_before
        assert conn.execute('SELECT * FROM agtech_datasets').fetchall() == catalogue_before
    assert (root / 'Farm.qgz').read_bytes() == before_map and source.read_bytes() == original
    # Restore only this synthetic fixture using another explicit audited review.
    boundary_api.apply_boundary(root, preview_boundary(root, summer, '2027-03-31', expected_timeline=saved), history_decision='retain-recorded')
    current_timeline = store.records(root)['season']
    # The real modal requires an unchecked retain-history acknowledgement.
    modal = hierarchy_dialog.SeasonBoundaryPreview(root, summer)
    assert hasattr(modal, 'apply_button'), 'Boundary review needs an explicit farmer-facing apply control'
    modal.end.setDate(QDate(2027, 3, 30))
    assert not modal.keep_jobs.isChecked() and not modal.apply_button.isEnabled()
    modal.keep_jobs.setChecked(True)
    assert modal.apply_button.isEnabled()
    before_cancel = store.database(root).read_bytes()
    def cancel_confirmation():
        box = QApplication.activeModalWidget()
        from qgis.PyQt.QtWidgets import QMessageBox
        assert isinstance(box, QMessageBox) and box.defaultButton() == box.button(QMessageBox.Cancel)
        box.button(QMessageBox.Cancel).click()
    QTimer.singleShot(0, cancel_confirmation)
    modal.apply_button.click()
    assert modal.isVisible() is False  # not exec'd by this direct API harness
    assert store.database(root).read_bytes() == before_cancel
    def accept_confirmation():
        box = QApplication.activeModalWidget()
        from qgis.PyQt.QtWidgets import QMessageBox
        assert 'recorded seasons' in box.text()
        box.button(QMessageBox.Yes).click()
    QTimer.singleShot(0, accept_confirmation)
    modal.apply_button.click()
    assert modal.decision['history_decision'] == 'retain-recorded'
    sip.delete(modal)
    boundary_api.apply_boundary(root, preview_boundary(root, summer, '2027-03-31', expected_timeline=store.records(root)['season']), history_decision='retain-recorded')
    current_timeline = store.records(root)['season']
    # Changing proposal clears acknowledgement; changing history during confirmation refuses.
    modal = hierarchy_dialog.SeasonBoundaryPreview(root, summer)
    modal.end.setDate(QDate(2027, 3, 30));modal.keep_jobs.setChecked(True)
    modal.end.setDate(QDate(2027, 3, 29))
    assert not modal.keep_jobs.isChecked() and not modal.apply_button.isEnabled()
    modal.keep_jobs.setChecked(True)
    confirm_snapshot = []
    def stale_confirmation():
        with closing(sqlite3.connect(store.database(root))) as conn:
            with conn: conn.execute('UPDATE agtech_datasets SET name=? WHERE id=?', ('Changed during confirmation', result[0]['id']))
        confirm_snapshot.append(store.database(root).read_bytes())
        from qgis.PyQt.QtWidgets import QMessageBox
        QApplication.activeModalWidget().button(QMessageBox.Yes).click()
    QTimer.singleShot(0, stale_confirmation)
    modal.apply_button.click()
    assert modal.decision is None and modal.preview is None and not modal.apply_button.isEnabled()
    assert 'Not applied' in modal.result.text() and store.database(root).read_bytes() == confirm_snapshot[0]
    sip.delete(modal)
    with closing(sqlite3.connect(store.database(root))) as conn:
        with conn: conn.execute('UPDATE agtech_datasets SET name=? WHERE id=?', (result[0]['name'], result[0]['id']))
    # Replay, missing acknowledgement, altered review and fresh identity refusals.
    def refuse_apply(reviewed, contains, decision='retain-recorded'):
        before = store.database(root).read_bytes()
        try:
            boundary_api.apply_boundary(root, reviewed, history_decision=decision)
        except (ValueError, sqlite3.Error) as error:
            assert contains in str(error), str(error)
        else:
            raise AssertionError('Unsafe boundary application accepted')
        assert store.database(root).read_bytes() == before
        assert source.read_bytes() == source_bytes[0]
    source_bytes = [original]
    fresh = preview_boundary(root, summer, '2027-03-30', expected_timeline=current_timeline)
    refuse_apply(fresh, 'Explicitly keep', '')
    refuse_apply(fresh, 'Explicitly keep', 'move-jobs')
    refuse_apply(reviewed, 'changed')  # prior decision invalidates old consent even after date restoration
    tampered = json.loads(json.dumps(fresh));tampered['history'][0]['recorded_season_id'] = winter
    refuse_apply(tampered, 'history or source identity changed')
    source.write_bytes(original + b' ');source_bytes[0] = source.read_bytes()
    refuse_apply(fresh, 'source changed')
    source.write_bytes(original);source_bytes[0] = original
    # Release the test-owned original provider before Windows file-absence probe.
    layer = None
    gc.collect()
    moved = source.with_suffix('.moved');source.rename(moved)
    before = store.database(root).read_bytes()
    try:
        boundary_api.apply_boundary(root, fresh, history_decision='retain-recorded')
    except ValueError as error:
        assert 'unavailable locally' in str(error)
    else: raise AssertionError('Missing source accepted')
    finally: moved.rename(source)
    assert store.database(root).read_bytes() == before
    with closing(sqlite3.connect(store.database(root))) as conn:
        with conn:
            conn.execute('UPDATE agtech_datasets SET name=? WHERE id=?', ('Changed job label', result[0]['id']))
    refuse_apply(fresh, 'history or source identity changed')
    with closing(sqlite3.connect(store.database(root))) as conn:
        with conn:
            conn.execute('UPDATE agtech_datasets SET name=? WHERE id=?', (result[0]['name'], result[0]['id']))
    # Fail the second date write and the final receipt separately: complete rollback.
    for trigger in (
        f"CREATE TRIGGER injected_boundary_failure BEFORE UPDATE ON agtech_seasons WHEN OLD.id='{winter}' BEGIN SELECT RAISE(ABORT,'Injected paired-date failure'); END",
        "CREATE TRIGGER injected_boundary_failure BEFORE INSERT ON agtech_season_boundary_decisions BEGIN SELECT RAISE(ABORT,'Injected audit failure'); END"):
        with closing(sqlite3.connect(store.database(root))) as conn:
            with conn: conn.execute(trigger)
        refuse_apply(fresh, 'Injected')
        with closing(sqlite3.connect(store.database(root))) as conn:
            with conn: conn.execute('DROP TRIGGER injected_boundary_failure')
    # Busy writer fails rather than overriding; keep the five-second SQLite timeout.
    with closing(sqlite3.connect(store.database(root))) as locked:
        locked.execute('BEGIN IMMEDIATE')
        refuse_apply(fresh, 'locked')
        locked.rollback()
    with closing(sqlite3.connect(store.database(root))) as conn:
        for sql in ('UPDATE agtech_season_boundary_decisions SET contract=contract', 'DELETE FROM agtech_season_boundary_decisions'):
            try:
                with conn: conn.execute(sql)
            except sqlite3.IntegrityError as error: assert 'immutable' in str(error)
            else: raise AssertionError('Audit history was mutable')
    # Unknown future audit contract refuses further previews/application.
    with closing(sqlite3.connect(store.database(root))) as conn:
        with conn:
            conn.execute("INSERT INTO agtech_season_boundary_decisions VALUES ('future','future',?,'now','{}')", (field,))
    rejected(summer, '2027-03-30', 'supported reader', expected=current_timeline)
    # Remove only this deliberately invalid synthetic audit through rollback-style fixture rebuild.
    with closing(sqlite3.connect(store.database(root))) as conn:
        with conn:
            conn.execute('DROP TRIGGER agtech_boundary_no_delete')
            conn.execute("DELETE FROM agtech_season_boundary_decisions WHERE id='future'")
            conn.execute("CREATE TRIGGER agtech_boundary_no_delete BEFORE DELETE ON agtech_season_boundary_decisions BEGIN SELECT RAISE(ABORT,'Season boundary decisions are immutable'); END")
    # A local OGR VRT is not a verified source bundle: referenced content may change
    # without changing its XML, or contact a service when reopened. Refuse Apply.
    from xml.sax.saxutils import escape
    vrt = Path(temporary) / 'Job.vrt'
    vrt.write_text('<OGRVRTDataSource><OGRVRTLayer name="Job"><SrcDataSource>' +
                   escape(str(source)) + '</SrcDataSource><SrcLayer>Job</SrcLayer></OGRVRTLayer></OGRVRTDataSource>')
    virtual = QgsVectorLayer(str(vrt), 'Virtual job', 'ogr')
    assert virtual.isValid()
    virtual_review = prepare_review(root, virtual, placement.review_job_season(root, field, '2027-03-31', 'planting'))
    virtual_result = managed.save_dataset(root, virtual, field, 'data', review=virtual_review)
    assert virtual_result
    virtual_impact = preview_boundary(root, summer, '2027-03-30', expected_timeline=current_timeline)
    refuse_apply(virtual_impact, 'unavailable locally')
    del virtual, virtual_result
    # Unsupported/missing classification pointers must not be advertised as zero impact.
    with closing(sqlite3.connect(store.database(root))) as conn:
        with conn:
            conn.execute('UPDATE agtech_datasets SET classification_id=? WHERE id=?', ('missing', reference_result[0]['id']))
    rejected(summer, '2027-03-30', 'missing or belongs', expected=current_timeline)
    assert source.read_bytes() == original
    del reference_layer, reference_result, layer, result
    project.clear()
    from qgis.PyQt.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    gc.collect()

temporary = tempfile.TemporaryDirectory(prefix='aggis-boundary-')
try:
    exercise(temporary.name)
finally:
    QgsProject.instance().clear()
    from qgis.PyQt.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    gc.collect()
    app.exitQgis()
    temporary.cleanup()
print('Asserted linked boundary preview/apply, keep-history, stale/source refusals and transactional rollback passed')
