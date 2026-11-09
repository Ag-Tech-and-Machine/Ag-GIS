# SPDX-License-Identifier: GPL-2.0-or-later
"""Explicit whole-dataset job review; metadata only, not a vendor decoder."""
import json
import uuid
from . import classification_registry as registry
from .classification import MAPPING_RULE, VERSION

CONTRACT = 'reviewed-import-v1'


def prepare_review(root, source, review):
    from . import managed_data
    from .import_placement import review_job_season
    current = review_job_season(root, review['field_id'], review['job_date'], review['operation_subtype'])
    if current != review:
        raise ValueError('Season timeline changed. Review the job again before importing.')
    digest = managed_data.source_hash(source)
    if not digest:
        raise ValueError('This source has no verifiable content identity. Keep it as Whole Field data.')
    return dict(current, source={'source_uri': source.source(), 'source_hash': digest,
                                'provider': source.providerType(), 'crs_wkt': source.crs().toWkt()})


def validate_review(root, source, field_id, role, review, *, connection=None):
    from . import managed_data
    from .import_placement import review_job_season
    if role != 'data':
        raise ValueError('Job imports use Other data. Reference types stay in Whole Field; review the type or clear the job review.')
    if not isinstance(review, dict) or review.get('field_id') != field_id or not isinstance(review.get('source'), dict):
        raise ValueError('Field or job review changed. Review the job again before importing.')
    current = review_job_season(root, field_id, review.get('job_date'), review.get('operation_subtype'), connection=connection)
    if current != {key: value for key, value in review.items() if key != 'source'}:
        raise ValueError('Season timeline changed. Review the job again before importing.')
    identity = review['source']
    if (not identity.get('source_hash') or identity.get('source_uri') != source.source()
            or identity.get('provider') != source.providerType() or identity.get('crs_wkt') != source.crs().toWkt()
            or managed_data.source_hash(source) != identity['source_hash']):
        raise ValueError('Source changed since job review. Rescan and review the job again.')
    return current


def store_review(connection, record, review):
    """Compose in the caller's transaction: no commit, source or spatial writes."""
    registry.ensure_classification_tables(connection)
    columns = {row[1] for row in connection.execute('PRAGMA table_info(agtech_datasets)')}
    if 'classification_id' not in columns:
        connection.execute('ALTER TABLE agtech_datasets ADD COLUMN classification_id TEXT')
    identifier = str(uuid.uuid4())
    snapshot = json.dumps({'contract': CONTRACT, 'review': {k: v for k, v in review.items() if k != 'source'},
                          'source': review['source'], 'mapping_rule': MAPPING_RULE, 'mapping_version': VERSION,
                          'vendor_mapping': None, 'unit_mapping': None}, sort_keys=True, ensure_ascii=False, allow_nan=False)
    connection.execute('''INSERT INTO agtech_classifications
        (id,dataset_id,purpose,operation_family,operation_subtype,measurement,unit,semantics,
         field_id,season_id,source_value,created_utc,mapping_version,vendor_source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (identifier, record['id'], 'operation', review['operation_family'], review['operation_subtype'],
         '', '', 'unknown', review['field_id'], review['season_id'], snapshot, record['created_utc'], VERSION, CONTRACT))
    connection.execute('UPDATE agtech_datasets SET classification_id=? WHERE id=?', (identifier, record['id']))
    for action in ('UPDATE', 'DELETE'):
        connection.execute(f'''CREATE TRIGGER IF NOT EXISTS agtech_review_no_{action.lower()}
            BEFORE {action} ON agtech_classifications WHEN OLD.vendor_source='{CONTRACT}'
            BEGIN SELECT RAISE(ABORT,'Reviewed import history is immutable'); END''')
    return identifier


def read_binding(root, record):
    """Restore only the catalogue's exact pointer, never today's rule or date match."""
    if not record.get('classification_id'):
        return None
    from contextlib import closing
    import sqlite3
    from . import hierarchy
    with closing(sqlite3.connect(hierarchy.database(root).resolve().as_uri() + '?mode=ro', uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute('SELECT * FROM agtech_classifications WHERE id=? AND dataset_id=?',
                                 (record['classification_id'], record['id'])).fetchone()
    if row is None:
        raise ValueError('Saved classification pointer is missing. No seasonal placement was guessed.')
    if row['vendor_source'] != CONTRACT:
        raise ValueError('This saved classification needs a supported binding reader; no placement was guessed.')
    snapshot = json.loads(row['source_value'])
    review = snapshot['review']
    if (snapshot.get('contract') != CONTRACT or row['field_id'] != record['field_id']
            or review['field_id'] != row['field_id'] or review['season_id'] != row['season_id']
            or review['operation_subtype'] != row['operation_subtype']
            or snapshot['source']['source_hash'] != record['source_hash']
            or snapshot['source']['source_uri'] != record['source_uri']):
        raise ValueError('Saved job context does not match its dataset. No placement was guessed.')
    return dict(review, source=snapshot['source'])
