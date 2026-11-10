"""Synthetic encrypted pre-request binding, NEVER expand/send APIHeader values."""
from contextlib import closing
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3

from auth_refresh_fence import RefreshFence
from auth_refresh_readback import start_bound_fixture_refresh

BIND_CASES = ('exact', 'changed-original', 'wrong-pair', 'wrong-attempt', 'write-locked', 'expired-after-write')
CRASH_CASES = ('crash-before-write', 'crash-after-write', 'crash-after-readback', 'crash-after-request')
CASES = BIND_CASES + CRASH_CASES
CRASH_EXITS = {case: 41 + index for index, case in enumerate(CRASH_CASES)}


def main():
    scratch = Path(os.environ['AGGIS_SYNTHETIC_AUTH_ROOT']).resolve()
    allowed = Path('C:/temp/AppData/Local/hermes/cache/scratch').resolve()
    assert scratch.is_relative_to(allowed) and scratch.name.startswith('aggis-pre-bind-')
    assert (scratch / 'SYNTHETIC-ONLY').read_text() == 'fresh-synthetic-pre-bind-v1'
    phase = os.environ['AGGIS_SYNTHETIC_AUTH_PHASE']
    assert phase in ('seed', 'bind', 'cold', 'cleanup') + CRASH_CASES
    marker = os.environ['AGGIS_SYNTHETIC_AUTH_VALUE']
    password = os.environ['AGGIS_SYNTHETIC_AUTH_PASSWORD']
    assert marker.startswith('AGGIS-SYNTHETIC-NOT-A-TOKEN-')
    assert password.startswith('AGGIS-SYNTHETIC-PASSWORD-')
    authdir = scratch / 'auth'
    authdir.mkdir(exist_ok=True)
    os.environ['QGIS_AUTH_DB_DIR_PATH'] = str(authdir)
    os.environ['QGIS_CUSTOM_CONFIG_PATH'] = str(scratch / 'profile')
    os.environ.pop('QGIS_AUTH_PASSWORD_FILE', None)
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    from qgis.PyQt.QtCore import QSettings
    from qgis.core import QgsApplication, QgsAuthMethodConfig, Qgis
    QSettings.setDefaultFormat(QSettings.IniFormat)
    for scope in (QSettings.UserScope, QSettings.SystemScope):
        QSettings.setPath(QSettings.IniFormat, scope, str(scratch / 'settings'))
    app = QgsApplication([], False, str(scratch / 'profile'))
    app.initQgis()
    manager = QgsApplication.authManager()
    ids = tuple('agpre' + str(index).zfill(2) for index in range(1, len(CASES) + 1))
    sentinel = 'agpresn'
    result = dict(phase=phase, pid=os.getpid(), qgis=Qgis.QGIS_VERSION,
                  synthetic_only=True, network_used=False, product_adapter=False,
                  native_settings_path=str(Path(QgsApplication.qgisSettingsDirPath()).resolve()),
                  qt_settings_path=str(Path(QSettings().fileName()).resolve()))
    for key in ('native_settings_path', 'qt_settings_path'):
        assert Path(result[key]).is_relative_to(scratch)

    def fence(ident):
        return RefreshFence(scratch / (ident + '.sqlite3'), ident)

    def pair(ident, suffix='old'):
        return dict(access_token=marker + '-access-' + ident + suffix,
                    refresh_token=marker + '-refresh-' + ident + suffix,
                    token_type='bearer', expires_in=60, refresh_token_expires_in=100)

    def original(ident):
        return dict(slot=ident, revision='fixture-old', expires_at=200, attempt='', pair=pair(ident))

    def load(ident):
        manager.clearAllCachedConfigs()
        ok, config = manager.loadAuthenticationConfig(ident, QgsAuthMethodConfig(), True)
        assert ok is True
        values = config.configMap()
        assert set(values) == {'Authorization'}
        return json.loads(values['Authorization'])

    def store(ident, record, update):
        config = QgsAuthMethodConfig()
        config.setId(ident)
        config.setName('Synthetic pre-request fixture')
        config.setMethod('APIHeader')
        config.setVersion(2)
        config.setUri('https://example.invalid')
        config.setConfig('Authorization', json.dumps(record, sort_keys=True))
        ok, returned = manager.storeAuthenticationConfig(config, update)
        assert returned.id() == ident
        return ok

    def row(ident):
        with closing(sqlite3.connect(fence(ident).path)) as conn:
            return conn.execute('SELECT state,attempt,revision,expires_at FROM refresh_fence').fetchone()

    try:
        assert Path(manager.authenticationDatabasePath()).resolve() == authdir / 'qgis-auth.db'
        assert not manager.isDisabled()
        manager.setPasswordHelperEnabled(False)
        assert manager.setMasterPassword(password, True)
        if phase == 'seed':
            assert not manager.availableAuthMethodConfigs()
            for ident in ids + (sentinel,):
                assert store(ident, original(ident), False) is True
                if ident != sentinel:
                    RefreshFence.create(fence(ident).path, ident, revision='fixture-old', expires_at=200)
            result['seeded'] = len(ids) + 1
        assert set(manager.availableAuthMethodConfigs()) == set(ids) | {sentinel}
        if phase == 'bind':
            receipts = []
            for ident, case in zip(ids, BIND_CASES):
                reads, writes, now = [], [], [100]
                def read():
                    reads.append(True)
                    if len(reads) == 2 and case == 'changed-original':
                        changed = original(ident)
                        changed['pair'] = pair(ident, 'independent')
                        assert store(ident, changed, True) is True
                    return load(ident)
                def write(record):
                    writes.append(True)
                    assert row(ident) == ('uncertain', record['attempt'], 'fixture-old', 200)
                    with closing(sqlite3.connect(fence(ident).path, timeout=0)) as conn:
                        try:
                            conn.execute('BEGIN IMMEDIATE')
                        except sqlite3.OperationalError:
                            pass
                        else:
                            raise AssertionError('Ledger writer reservation not held')
                    record = deepcopy(record)
                    if case == 'wrong-pair':
                        record['pair'] = pair(ident, 'wrong')
                    if case == 'wrong-attempt':
                        record['attempt'] = '0' * 32
                    if case == 'write-locked':
                        before = (authdir / 'qgis-auth.db').read_bytes()
                        with closing(sqlite3.connect(authdir / 'qgis-auth.db')) as conn:
                            conn.execute('BEGIN IMMEDIATE')
                            ok = store(ident, record, True)
                        assert ok is False
                        assert (authdir / 'qgis-auth.db').read_bytes() == before
                        return False
                    assert store(ident, record, True) is True
                    if case == 'expired-after-write':
                        now[0] = 200
                    return True
                outcome = start_bound_fixture_refresh(
                    fence=fence(ident), revision='fixture-old', expires_at=200,
                    now=lambda: now[0], clock=lambda: 0, client_id='SYNTHETIC-CLIENT',
                    readback=read, write_bound=write)
                assert (outcome is not None) is (case == 'exact')
                assert len(writes) == (0 if case == 'changed-original' else 1)
                assert row(ident)[0] == 'uncertain'
                if outcome is not None:
                    attempt, flow, request = outcome
                    assert load(ident) == dict(original(ident), attempt=attempt)
                    assert request.payload['refresh_token'] == pair(ident)['refresh_token']
                    assert row(ident)[1] == attempt
                    flow.cancel()
                    assert flow.take_tokens() is None
                assert load(sentinel) == original(sentinel)
                receipts.append(dict(case=case, request_created=outcome is not None,
                                     native_writes=len(writes), uncertain=True, sentinel_exact=True))
            result['cases'] = receipts
        if phase in CRASH_CASES:
            ident = ids[CASES.index(phase)]
            reads = []

            def crash():
                state, attempt, revision, expiry = row(ident)
                assert (state, revision, expiry) == ('uncertain', 'fixture-old', 200)
                assert len(attempt) == 32
                assert load(sentinel) == original(sentinel)
                for path in authdir.iterdir():
                    if path.is_file():
                        data = path.read_bytes()
                        assert marker.encode() not in data and password.encode() not in data
                result.update(abrupt_exit=CRASH_EXITS[phase], sentinel_exact=True,
                              scratch_plaintext_absent=True, uncertain_before_exit=True)
                print(json.dumps(result, sort_keys=True), flush=True)
                os._exit(CRASH_EXITS[phase])

            def read_crash():
                record = load(ident)
                reads.append(True)
                if len(reads) == 3 and phase == 'crash-after-readback':
                    assert record == dict(original(ident), attempt=row(ident)[1])
                    crash()
                return record

            def write_crash(record):
                assert row(ident) == ('uncertain', record['attempt'], 'fixture-old', 200)
                if phase == 'crash-before-write':
                    assert load(ident) == original(ident)
                    crash()
                assert store(ident, record, True) is True
                if phase == 'crash-after-write':
                    crash()
                return True

            outcome = start_bound_fixture_refresh(
                fence=fence(ident), revision='fixture-old', expires_at=200,
                now=lambda: 100, clock=lambda: 0, client_id='SYNTHETIC-CLIENT',
                readback=read_crash, write_bound=write_crash)
            assert phase == 'crash-after-request' and outcome is not None
            attempt, flow, request = outcome
            assert request.payload['refresh_token'] == pair(ident)['refresh_token']
            assert load(ident) == dict(original(ident), attempt=attempt)
            crash()
        if phase in ('cold', 'cleanup'):
            for ident, case in zip(ids, CASES):
                state, attempt, revision, expiry = row(ident)
                assert (state, revision, expiry) == ('uncertain', 'fixture-old', 200)
                expected = dict(original(ident), attempt=attempt)
                if case == 'changed-original':
                    expected = original(ident)
                    expected['pair'] = pair(ident, 'independent')
                elif case == 'wrong-pair':
                    expected['pair'] = pair(ident, 'wrong')
                elif case == 'wrong-attempt':
                    expected['attempt'] = '0' * 32
                elif case in ('write-locked', 'crash-before-write'):
                    expected = original(ident)
                assert load(ident) == expected
                before = fence(ident).path.read_bytes()
                assert fence(ident).begin_bound('fixture-old', expires_at=200, now=100) is None
                callbacks = []
                assert start_bound_fixture_refresh(
                    fence=fence(ident), revision='fixture-old', expires_at=200,
                    now=lambda: 100, clock=lambda: 0, client_id='SYNTHETIC-CLIENT',
                    readback=lambda: load(ident), write_bound=lambda record: callbacks.append(True)) is None
                assert callbacks == [] and fence(ident).path.read_bytes() == before
                with closing(sqlite3.connect(fence(ident).path)) as conn:
                    assert conn.execute('SELECT * FROM refresh_replacement').fetchall() == []
            result['cold_exact_records_and_no_retry'] = True
            result['cold_crash_cases'] = list(CRASH_CASES)
        assert load(sentinel) == original(sentinel)
        result['sentinel_exact'] = True
        if phase == 'cleanup':
            for ident in ids:
                assert manager.removeAuthenticationConfig(ident)
            assert load(sentinel) == original(sentinel)
            assert manager.removeAuthenticationConfig(sentinel)
            assert not manager.availableAuthMethodConfigs()
            result['zero_configs'] = True
        for path in authdir.iterdir():
            if path.is_file():
                data = path.read_bytes()
                assert marker.encode() not in data and password.encode() not in data
        result['scratch_plaintext_absent'] = True
        print(json.dumps(result, sort_keys=True), flush=True)
    finally:
        manager = None
        app.exitQgis()
        del app


if __name__ == '__main__':
    main()
