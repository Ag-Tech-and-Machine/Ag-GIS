# SPDX-License-Identifier: GPL-2.0-or-later
"""Linked boundary review and explicit paired metadata edit; history stays immutable."""
from contextlib import closing
from datetime import date, timedelta
import json
import sqlite3
import hashlib
import uuid
from datetime import datetime, timezone

from . import hierarchy as store
from .import_placement import review_job_season
from .reviewed_import import CONTRACT


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def apply_boundary(root, reviewed, *, history_decision):
    """Commit paired metadata dates and an append-only retain-history receipt.

    No project, spatial, style, classification or original-source writes. A fresh
    review in the same write transaction rejects stale consent before changing dates.
    """
    if history_decision != 'retain-recorded':
        raise ValueError('Explicitly keep jobs in their recorded seasons. Reassignment is not supported.')
    if not isinstance(reviewed, dict) or reviewed.get('contract') != 'season-boundary-preview-v1':
        raise ValueError('Review the boundary again before applying.')
    with closing(sqlite3.connect(store.database(root).resolve().as_uri() + '?mode=rw', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            fresh = preview_boundary(root, reviewed.get('left_season_id'), reviewed.get('end_date'),
                                     expected_timeline=reviewed.get('timeline', []), connection=conn)
            if fresh != reviewed:
                raise ValueError('Saved history or source identity changed. Close and review again; nothing was applied.')
            changes = [(old, new) for old, new in zip(fresh['timeline'], fresh['proposed_timeline']) if old != new]
            if len(changes) != 2:
                raise ValueError('Choose a different boundary date before applying.')
            # Only original local supported files are re-opened. Never contact a
            # service or treat an unavailable source as verified unchanged.
            from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProviderRegistry, QgsCoordinateReferenceSystem
            from pathlib import Path
            from .managed_data import source_hash
            source_receipts = []
            for job in fresh['history']:
                row = conn.execute('SELECT * FROM agtech_classifications WHERE id=?', (job['classification_id'],)).fetchone()
                identity = json.loads(row['source_value'])['source']
                provider = identity['provider']
                decoded = QgsProviderRegistry.instance().decodeUri(provider, identity['source_uri'])
                path = Path(decoded.get('path') or '')
                if provider not in ('ogr', 'gdal') or not path.is_file() or path.suffix.lower() == '.vrt':
                    raise ValueError('A reviewed job source is unavailable locally or is virtual. Restore its original supported file and review again; no dates changed.')
                factory = QgsVectorLayer if provider == 'ogr' else QgsRasterLayer
                source = factory(identity['source_uri'], 'Boundary source verification', provider)
                if not source.isValid():
                    raise ValueError('A reviewed job source cannot be opened; no dates changed.')
                source.setCrs(QgsCoordinateReferenceSystem.fromWkt(identity['crs_wkt']))
                digest = source_hash(source)
                del source
                if not digest or digest != identity['source_hash']:
                    raise ValueError('A reviewed job source changed. Restore/review the source before applying; no dates changed.')
                source_receipts.append({'classification_id': job['classification_id'], 'source_hash': digest})
            decision = {'id': str(uuid.uuid4()), 'contract': 'season-boundary-decision-v1',
                        'created_utc': datetime.now(timezone.utc).isoformat(), 'history_decision': history_decision,
                        'review': fresh, 'verified_sources': source_receipts}
            conn.execute('''CREATE TABLE IF NOT EXISTS agtech_season_boundary_decisions
                (id TEXT PRIMARY KEY, contract TEXT NOT NULL, field_id TEXT NOT NULL,
                 created_utc TEXT NOT NULL, decision_json TEXT NOT NULL)''')
            for action in ('UPDATE', 'DELETE'):
                conn.execute(f'''CREATE TRIGGER IF NOT EXISTS agtech_boundary_no_{action.lower()}
                    BEFORE {action} ON agtech_season_boundary_decisions
                    BEGIN SELECT RAISE(ABORT,'Season boundary decisions are immutable'); END''')
            for old, new in changes:
                count = conn.execute('UPDATE agtech_seasons SET start_date=?,end_date=? WHERE id=? AND field_id=?',
                                     (new['start_date'], new['end_date'], old['id'], fresh['field_id'])).rowcount
                if count != 1:
                    raise ValueError('Season identity changed; no dates changed.')
            conn.execute('INSERT INTO agtech_season_boundary_decisions VALUES (?,?,?,?,?)',
                         (decision['id'], decision['contract'], fresh['field_id'], decision['created_utc'], _json(decision)))
    return decision



def preview_boundary(root, left_season_id, end_date, *, expected_timeline, connection=None):
    """Preview one shared boundary using a consistent, read-only metadata snapshot.

    Inclusive endpoints: the next season starts one day after the proposed end.
    The outer endpoints and all other seasons stay fixed. History remains pinned
    to its original reviewed context even when its hypothetical date match changes.
    """
    if connection is not None:
        return _preview(root, left_season_id, end_date, expected_timeline, connection)
    with closing(sqlite3.connect(store.database(root).resolve().as_uri() + '?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute('BEGIN')
        return _preview(root, left_season_id, end_date, expected_timeline, conn)


def _preview(root, left_season_id, end_date, expected_timeline, conn):
    seasons = [dict(row) for row in conn.execute('SELECT * FROM agtech_seasons')]
    left = next((row for row in seasons if row['id'] == left_season_id), None)
    if left is None:
        raise ValueError('Select an existing season with a following season.')
    field_id = left['field_id']
    timeline = review_job_season(root, field_id, left['start_date'], 'planting', connection=conn)['timeline']
    expected = sorted((row for row in expected_timeline if row['field_id'] == field_id),
                      key=lambda row: (row['start_date'], row['end_date'], row['id']))
    if timeline != expected:
        raise ValueError('Season timeline changed. Close and reopen the boundary preview; no dates or history were changed.')
    index = next(i for i, row in enumerate(timeline) if row['id'] == left_season_id)
    if index + 1 == len(timeline):
        raise ValueError('This is the last season. Select the season before the boundary you want to preview.')
    try:
        boundary = date.fromisoformat(end_date)
        if boundary.isoformat() != end_date:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('Enter the proposed end date as YYYY-MM-DD.') from None
    right = timeline[index + 1]
    if not left['start_date'] <= end_date < right['end_date']:
        raise ValueError('Keep at least one day in both seasons. Outer dates cannot change in this preview.')
    proposed = [dict(row) for row in timeline]
    proposed[index]['end_date'] = end_date
    proposed[index + 1]['start_date'] = (boundary + timedelta(days=1)).isoformat()
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    datasets = ([dict(row) for row in conn.execute('SELECT * FROM agtech_datasets WHERE field_id=? ORDER BY id', (field_id,))]
                if 'agtech_datasets' in tables else [])
    classifications = ([dict(row) for row in conn.execute('SELECT * FROM agtech_classifications WHERE field_id=? ORDER BY id', (field_id,))]
                       if 'agtech_classifications' in tables else [])
    by_dataset = {row['id']: row for row in datasets}
    by_season = {row['id']: row for row in timeline}
    history = []
    for row in classifications:
        record = by_dataset.get(row['dataset_id'])
        try:
            snapshot = json.loads(row['source_value'])
            review = snapshot['review']
            job_date = review['job_date']
            day = date.fromisoformat(job_date)
            valid = (row['vendor_source'] == CONTRACT and snapshot['contract'] == CONTRACT
                     and day.isoformat() == job_date and row['purpose'] == 'operation'
                     and review['field_id'] == field_id and review['season_id'] == row['season_id']
                     and review['operation_subtype'] == row['operation_subtype']
                     and row['season_id'] in by_season and record is not None
                     and record.get('classification_id') == row['id'] and record['role'] == 'data'
                     and snapshot['source']['source_hash'] == record['source_hash']
                     and snapshot['source']['source_uri'] == record['source_uri'])
            if not valid:
                raise ValueError()
        except (KeyError, ValueError, TypeError):
            raise ValueError('Some saved job history cannot be safely reviewed by this build. No impact estimate or reassignment was made.') from None
        current = next((r for r in timeline if r['start_date'] <= job_date <= r['end_date']), None)
        match = next((r for r in proposed if r['start_date'] <= job_date <= r['end_date']), None)
        history.append({'classification_id': row['id'], 'dataset_id': row['dataset_id'],
                        'dataset_name': record['name'], 'job_date': job_date,
                        'operation_subtype': row['operation_subtype'],
                        'recorded_season_id': row['season_id'], 'recorded_season_name': by_season[row['season_id']]['name'],
                        'current_season_id': current['id'] if current else None,
                        'proposed_season_id': match['id'] if match else None,
                        'proposed_season_name': match['name'] if match else 'Outside dated seasons',
                        'affected': (match['id'] if match else None) != row['season_id'],
                        'date_match_changed': (current['id'] if current else None) != (match['id'] if match else None)})
    reviewed_ids = {row['id'] for row in classifications}
    if any(row.get('classification_id') and row['classification_id'] not in reviewed_ids for row in datasets):
        raise ValueError('A saved job classification is missing or belongs to another field. No impact estimate was made.')
    decisions = ([dict(row) for row in conn.execute('SELECT * FROM agtech_season_boundary_decisions WHERE field_id=? ORDER BY id', (field_id,))]
                 if 'agtech_season_boundary_decisions' in tables else [])
    if any(row['contract'] != 'season-boundary-decision-v1' for row in decisions):
        raise ValueError('This boundary decision history needs a supported reader; no dates changed.')
    workspace = conn.execute('SELECT farm_id FROM agtech_farm').fetchone()[0]
    fingerprint = hashlib.sha256(_json({'workspace_id': workspace, 'datasets': datasets,
                                        'classifications': classifications, 'decisions': decisions}).encode()).hexdigest()
    return {'contract': 'season-boundary-preview-v1', 'field_id': field_id,
            'workspace_id': workspace, 'snapshot_sha256': fingerprint,
            'left_season_id': left_season_id, 'end_date': end_date,
            'timeline': timeline, 'proposed_timeline': proposed, 'history': history,
            'affected_count': sum(row['affected'] for row in history),
            'date_match_changed_count': sum(row['date_match_changed'] for row in history),
            'unreviewed_count': sum(not row.get('classification_id') for row in datasets),
            'read_only': True}
