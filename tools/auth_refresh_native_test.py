"""Synthetic native late-write characterization, NOT a product credential adapter.

APIHeader is encrypted fixture storage only, NEVER request/header expansion.
Timers order cancellation/expiry before a handed-off write; this does NOT cancel
an in-progress synchronous native store operation or contact an OAuth provider.
"""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from auth_flow_model import RefreshFlow
from auth_refresh_fence import RefreshFence
from auth_refresh_readback import (acknowledge_attempt_fixture_readback,
                                   acknowledge_committed_fixture_readback)


def main():
    scratch = Path(os.environ['AGGIS_SYNTHETIC_AUTH_ROOT']).resolve()
    allowed = Path('C:/Users/[Maintainer]/AppData/Local/hermes/cache/scratch').resolve()
    assert scratch.is_relative_to(allowed) and scratch.name.startswith('aggis-auth-late-')
    assert (scratch / 'SYNTHETIC-ONLY').read_text() == 'fresh-synthetic-auth-late-v1'
    phase = os.environ['AGGIS_SYNTHETIC_AUTH_PHASE']
    assert phase in ('seed', 'cancel-write', 'cold-cancel', 'expire-write', 'cold-expire',
                     'bound-admission', 'readback-ack', 'cold-ack', 'record-replacement', 'cold-replacement', 'committed-handoff', 'cleanup')
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
    from qgis.PyQt.QtCore import QEventLoop, QSettings, QTimer
    from qgis.core import QgsApplication, QgsAuthMethodConfig, Qgis
    QSettings.setDefaultFormat(QSettings.IniFormat)
    for scope in (QSettings.UserScope, QSettings.SystemScope):
        QSettings.setPath(QSettings.IniFormat, scope, str(scratch / 'settings'))
    app = QgsApplication([], False, str(scratch / 'profile'))
    app.initQgis()
    assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(scratch)
    assert Path(QSettings().fileName()).resolve().is_relative_to(scratch)
    manager = QgsApplication.authManager()
    result = {'phase': phase, 'pid': os.getpid(), 'qgis': Qgis.QGIS_VERSION,
              'synthetic_only': True, 'product_adapter': False, 'network_used': False,
              'native_settings_path': str(Path(QgsApplication.qgisSettingsDirPath()).resolve()),
              'qt_settings_path': str(Path(QSettings().fileName()).resolve())}
    ids = ('agglat1', 'agglat2', 'agglat3')

    def pair(ident, revision):
        return {'access_token': marker + '-access-' + ident + '-' + revision,
                'refresh_token': marker + '-refresh-' + ident + '-' + revision,
                'token_type': 'bearer', 'expires_in': 60, 'refresh_token_expires_in': 100}

    def load(ident):
        ok, config = manager.loadAuthenticationConfig(ident, QgsAuthMethodConfig(), True)
        assert ok is True
        return config

    def assert_record(ident, revision):
        config = load(ident)
        expected = {'Authorization': json.dumps(pair(ident, revision), sort_keys=True),
                    'fixture_revision': revision, 'fixture_expires_at': '200'}
        if ident == 'agack01':
            with closing(sqlite3.connect(fence(ident).path)) as conn:
                attempt = conn.execute('SELECT attempt FROM refresh_fence').fetchone()[0]
            expected.update(fixture_slot=ident, fixture_attempt=attempt, fixture_old_revision='fixture-old')
        assert config.configMap() == expected
        ok, metadata = manager.loadAuthenticationConfig(ident, QgsAuthMethodConfig(), False)
        assert ok is True and not metadata.configMap()
        return config.configMap()

    def fence(ident):
        return RefreshFence(scratch / (ident + '.sqlite3'), ident)

    try:
        assert Path(manager.authenticationDatabasePath()).resolve() == authdir / 'qgis-auth.db'
        assert not manager.isDisabled()
        manager.setPasswordHelperEnabled(False)
        assert manager.setMasterPassword(password, True)
        if phase == 'seed':
            assert not manager.availableAuthMethodConfigs()
            for ident in ids:
                config = QgsAuthMethodConfig()
                config.setId(ident)
                config.setName('Synthetic late-write fixture ' + ident)
                config.setMethod('APIHeader')
                config.setVersion(2)
                config.setUri('https://example.invalid')
                config.setConfig('Authorization', json.dumps(pair(ident, 'fixture-old'), sort_keys=True))
                config.setConfig('fixture_revision', 'fixture-old')
                config.setConfig('fixture_expires_at', '200')
                ok, returned = manager.storeAuthenticationConfig(config, False)
                assert ok is True and returned.id() == ident
                if ident != ids[2]:
                    RefreshFence.create(scratch / (ident + '.sqlite3'), ident,
                                        revision='fixture-old', expires_at=200)
            result['seeded_three'] = True
        expected_ids = set(ids) | ({'agack01'} if phase in ('cold-ack', 'record-replacement', 'cold-replacement', 'committed-handoff', 'cleanup') else set())
        assert set(manager.availableAuthMethodConfigs()) == expected_ids
        if phase == 'bound-admission':
            cases = ('exact', 'wrong-revision', 'wrong-expiry', 'expired',
                     'missing-record', 'malformed-expiry')
            case_results = []
            for index, case in enumerate(cases, 1):
                ident = 'agbnd' + str(index).zfill(2)
                config = QgsAuthMethodConfig()
                config.setId(ident)
                config.setName('Synthetic bound admission fixture')
                config.setMethod('APIHeader')
                config.setVersion(2)
                config.setUri('https://example.invalid')
                config.setConfig('Authorization', json.dumps(pair(ident, 'fixture-old'), sort_keys=True))
                config.setConfig('fixture_revision', 'other' if case == 'wrong-revision' else 'fixture-old')
                config.setConfig('fixture_expires_at',
                                 'invalid' if case == 'malformed-expiry' else
                                 '201' if case == 'wrong-expiry' else '200')
                ok, stored = manager.storeAuthenticationConfig(config, False)
                assert ok is True and stored.id() == ident
                RefreshFence.create(fence(ident).path, ident, revision='fixture-old', expires_at=200)
                before = fence(ident).path.read_bytes()
                if case == 'missing-record':
                    assert manager.removeAuthenticationConfig(ident)
                manager.clearAllCachedConfigs()
                loaded, recovered = manager.loadAuthenticationConfig(ident, QgsAuthMethodConfig(), True)
                attempt, request = None, None
                if loaded is True:
                    values = recovered.configMap()
                    try:
                        expiry = int(values['fixture_expires_at'])
                    except ValueError:
                        expiry = None
                    attempt = fence(ident).begin_bound(
                        values['fixture_revision'], expires_at=expiry,
                        now=200 if case == 'expired' else 100)
                    if attempt is not None:
                        # Only fixture metadata is bound. The protected record is
                        # not locked atomically with SQLite; NOT a product adapter.
                        flow = RefreshFlow(lambda: 0, json.loads(values['Authorization']))
                        request = flow.start('SYNTHETIC-CLIENT')
                        assert request is not None
                        assert request.payload['refresh_token'] == pair(ident, 'fixture-old')['refresh_token']
                        flow.cancel()
                        assert flow.take_tokens() is None
                assert loaded is (case != 'missing-record')
                assert (attempt is not None) is (case == 'exact')
                assert (request is not None) is (case == 'exact')
                with closing(sqlite3.connect(fence(ident).path)) as conn:
                    row = conn.execute('SELECT state,attempt,revision,expires_at FROM refresh_fence').fetchone()
                expected_state = 'uncertain' if case == 'exact' else 'expired' if case == 'expired' else 'ready'
                assert row == (expected_state, attempt or '', 'fixture-old', 200)
                if case not in ('exact', 'expired'):
                    assert fence(ident).path.read_bytes() == before
                else:
                    assert fence(ident).begin_bound('fixture-old', expires_at=200, now=100) is None
                assert_record(ids[2], 'fixture-old')
                if case != 'missing-record':
                    assert manager.removeAuthenticationConfig(ident)
                case_results.append({'case': case, 'native_loaded': loaded,
                                     'request_created': request is not None,
                                     'fence_state': expected_state, 'sentinel_exact': True})
            assert set(manager.availableAuthMethodConfigs()) == set(ids)
            result['bound_admission_cases'] = case_results
        if phase == 'readback-ack':
            cases = ('exact', 'stale-pair', 'wrong-revision', 'wrong-expiry',
                     'missing-record', 'cancel-in-readback', 'expire-in-readback',
                     'wrong-attempt', 'wrong-fence-revision', 'expired-fence',
                     'wrong-protected-slot', 'wrong-protected-attempt',
                     'wrong-protected-old-revision', 'missing-protected-attempt')
            case_results = []
            for index, case in enumerate(cases, 1):
                ident = 'agack' + str(index).zfill(2)
                config = QgsAuthMethodConfig()
                config.setId(ident)
                config.setName('Synthetic readback fixture')
                config.setMethod('APIHeader')
                config.setVersion(2)
                config.setUri('https://example.invalid')
                config.setConfig('Authorization', json.dumps(pair(ident, 'fixture-old'), sort_keys=True))
                config.setConfig('fixture_revision', 'fixture-old')
                config.setConfig('fixture_expires_at', '200')
                ok, stored = manager.storeAuthenticationConfig(config, False)
                assert ok is True and stored.id() == ident
                RefreshFence.create(fence(ident).path, ident, revision='fixture-old', expires_at=200)
                attempt = fence(ident).begin_bound('fixture-old', expires_at=200, now=100)
                assert attempt is not None
                before = fence(ident).path.read_bytes()
                clock = [0]
                flow = RefreshFlow(lambda: clock[0], pair(ident, 'fixture-old'))
                request = flow.start('SYNTHETIC-CLIENT')
                assert request is not None
                replacement = pair(ident, 'fixture-new')
                assert flow.receive(request.key, 200, replacement)
                assert flow.take_tokens() is None
                config = load(ident)
                config.setConfig('Authorization', json.dumps(
                    pair(ident, 'fixture-old') if case == 'stale-pair' else replacement, sort_keys=True))
                config.setConfig('fixture_revision', 'fixture-old' if case == 'wrong-revision' else 'fixture-new')
                config.setConfig('fixture_expires_at', '201' if case == 'wrong-expiry' else '200')
                config.setConfig('fixture_slot', 'other' if case == 'wrong-protected-slot' else ident)
                config.setConfig('fixture_attempt', '0' * 32 if case == 'wrong-protected-attempt' else attempt)
                config.setConfig('fixture_old_revision',
                                 'other' if case == 'wrong-protected-old-revision' else 'fixture-old')
                if case == 'missing-protected-attempt':
                    config.removeConfig('fixture_attempt')
                native_ok = manager.updateAuthenticationConfig(config)
                assert native_ok is True
                if case == 'missing-record':
                    assert manager.removeAuthenticationConfig(ident)
                reads = []

                def native_readback():
                    assert flow.take_tokens() is None
                    manager.clearAllCachedConfigs()
                    ok, recovered = manager.loadAuthenticationConfig(ident, QgsAuthMethodConfig(), True)
                    reads.append(ok)
                    if ok is not True:
                        return None
                    values = recovered.configMap()
                    if case == 'cancel-in-readback':
                        flow.cancel()
                    elif case == 'expire-in-readback':
                        clock[0] = 30
                    return {'slot': values.get('fixture_slot'),
                            'attempt': values.get('fixture_attempt'),
                            'old_revision': values.get('fixture_old_revision'),
                            'revision': values['fixture_revision'],
                            'expires_at': int(values['fixture_expires_at']),
                            'pair': json.loads(values['Authorization'])}

                ack = acknowledge_attempt_fixture_readback(
                    flow, request.key, write_ok=native_ok, revision='fixture-new',
                    binding={'slot': ident, 'attempt': attempt, 'old_revision': 'fixture-old'},
                    expires_at=200, readback=lambda: fence(ident).read_attempt(
                        '0' * 32 if case == 'wrong-attempt' else attempt,
                        revision='other' if case == 'wrong-fence-revision' else 'fixture-old',
                        expires_at=200, now=200 if case == 'expired-fence' else 100,
                        readback=native_readback))
                blocked = case in ('wrong-attempt', 'wrong-fence-revision', 'expired-fence')
                assert reads == ([] if blocked else [case != 'missing-record'])
                assert ack is (case == 'exact')
                assert flow.take_tokens() == (replacement if case == 'exact' else None)
                assert flow.state == ('ready' if case == 'exact' else 'reauth_required')
                assert fence(ident).path.read_bytes() == before
                for revision in ('fixture-old', 'fixture-new'):
                    assert fence(ident).begin(revision, now=100) is None
                assert_record(ids[2], 'fixture-old')
                case_results.append({'case': case, 'native_update': True, 'ack': ack,
                                     'fence_uncertain_unchanged': True, 'sentinel_exact': True,
                                     'native_read_called': bool(reads), 'attempt_gate': True,
                                     'protected_attempt_gate': True})
                if case not in ('exact', 'missing-record'):
                    assert manager.removeAuthenticationConfig(ident)
            assert set(manager.availableAuthMethodConfigs()) == set(ids) | {'agack01'}
            result['readback_cases'] = case_results
        if phase in ('cold-ack', 'cleanup'):
            manager.clearAllCachedConfigs()
            assert_record('agack01', 'fixture-new')
            before = fence('agack01').path.read_bytes()
            for revision in ('fixture-old', 'fixture-new'):
                assert fence('agack01').begin(revision, now=100) is None
            assert fence('agack01').path.read_bytes() == before
            result['cold_exact_replacement_no_rearm'] = True
        if phase in ('record-replacement', 'cold-replacement', 'committed-handoff', 'cleanup'):
            ident = 'agack01'
            manager.clearAllCachedConfigs()
            assert_record(ident, 'fixture-new')
            with closing(sqlite3.connect(fence(ident).path)) as conn:
                attempt = conn.execute('SELECT attempt FROM refresh_fence').fetchone()[0]
            reads = []

            def replacement_metadata():
                manager.clearAllCachedConfigs()
                values = assert_record(ident, 'fixture-new')  # Same full pair/envelope snapshot.
                reads.append(True)
                return dict(slot=values['fixture_slot'], attempt=values['fixture_attempt'],
                            old_revision=values['fixture_old_revision'],
                            revision=values['fixture_revision'], expires_at=int(values['fixture_expires_at']))

            args = dict(revision='fixture-old', expires_at=200, now=100,
                        replacement_revision='fixture-new', replacement_expires_at=200,
                        readback=replacement_metadata)
            if phase == 'record-replacement':
                before = fence(ident).path.read_bytes()
                assert fence(ident).record_replacement('0' * 32, **args) is False
                assert not reads and fence(ident).path.read_bytes() == before
                assert fence(ident).record_replacement(attempt, **args) is True
                assert reads == [True]
                result['native_exact_readback_then_terminal_commit'] = True
            else:
                before = fence(ident).path.read_bytes()
                assert fence(ident).record_replacement(attempt, **args) is False
                assert not reads and fence(ident).path.read_bytes() == before
                result['cold_terminal_receipt_no_read_replay'] = True
            with closing(sqlite3.connect(fence(ident).path)) as conn:
                assert conn.execute('SELECT * FROM refresh_replacement').fetchone() == (
                    ident, attempt, 'fixture-old', 200, 'fixture-new', 200)
                assert conn.execute('SELECT state FROM refresh_fence').fetchone() == ('reconciled',)
            for revision in ('fixture-old', 'fixture-new'):
                assert fence(ident).begin(revision, now=100) is None
            assert_record(ids[2], 'fixture-old')
            result.update(terminal_receipt_exact=True, terminal_no_rearm=True,
                          terminal_no_model_handoff=True)
        if phase == 'committed-handoff':
            case_results = []
            for index, case in enumerate(('exact', 'cancel-after-commit', 'expire-after-commit', 'commit-busy'), 1):
                ident = 'aghnd' + str(index).zfill(2)
                RefreshFence.create(fence(ident).path, ident, revision='fixture-old', expires_at=200)
                attempt = fence(ident).begin_bound('fixture-old', expires_at=200, now=100)
                assert attempt is not None
                config = QgsAuthMethodConfig()
                config.setId(ident)
                config.setName('Synthetic commit handoff fixture')
                config.setMethod('APIHeader')
                config.setVersion(2)
                config.setUri('https://example.invalid')
                config.setConfig('Authorization', json.dumps(pair(ident, 'fixture-new'), sort_keys=True))
                for name, value in dict(slot=ident, attempt=attempt, old_revision='fixture-old',
                                        revision='fixture-new', expires_at='300').items():
                    config.setConfig('fixture_' + name, value)
                ok, stored = manager.storeAuthenticationConfig(config, False)
                assert ok is True and stored.id() == ident
                clock = [0]
                flow = RefreshFlow(lambda: clock[0], pair(ident, 'fixture-old'))
                request = flow.start('SYNTHETIC-CLIENT')
                assert request is not None
                assert flow.receive(request.key, 200, pair(ident, 'fixture-new'))
                observations = []
                saved = flow.saved

                def observe_saved(key, success):
                    if success is True:
                        with closing(sqlite3.connect(fence(ident).path)) as conn:
                            assert conn.execute('SELECT state FROM refresh_fence').fetchone() == ('reconciled',)
                            assert conn.execute('SELECT * FROM refresh_replacement').fetchone() == (
                                ident, attempt, 'fixture-old', 200, 'fixture-new', 300)
                        observations.append(True)
                    return saved(key, success)

                flow.saved = observe_saved

                class AfterCommit:
                    def record_replacement(self, *args, **kwargs):
                        committed = fence(ident).record_replacement(*args, **kwargs)
                        if case == 'cancel-after-commit':
                            flow.cancel()
                        elif case == 'expire-after-commit':
                            clock[0] = 30
                        return committed

                reads = []
                def native_handoff_readback():
                    assert flow.take_tokens() is None
                    manager.clearAllCachedConfigs()
                    values = load(ident).configMap()
                    reads.append(True)
                    return dict(slot=values['fixture_slot'], attempt=values['fixture_attempt'],
                                old_revision=values['fixture_old_revision'], revision=values['fixture_revision'],
                                expires_at=int(values['fixture_expires_at']), pair=json.loads(values['Authorization']))

                with closing(sqlite3.connect(fence(ident).path, timeout=0)) as reader:
                    if case == 'commit-busy':
                        reader.execute('BEGIN')
                        reader.execute('SELECT * FROM refresh_fence').fetchall()
                    ack = acknowledge_committed_fixture_readback(
                        flow, request.key, fence=AfterCommit(), write_ok=ok,
                        revision='fixture-new', expires_at=300, old_expires_at=200, now=100,
                        binding=dict(slot=ident, attempt=attempt, old_revision='fixture-old'),
                        readback=native_handoff_readback)
                assert reads == [True]
                assert ack is (case == 'exact')
                assert observations == ([] if case == 'commit-busy' else [True])
                assert flow.take_tokens() == (pair(ident, 'fixture-new') if case == 'exact' else None)
                with closing(sqlite3.connect(fence(ident).path)) as conn:
                    assert conn.execute('SELECT state FROM refresh_fence').fetchone() == (
                        'uncertain' if case == 'commit-busy' else 'reconciled',)
                    assert conn.execute('SELECT count(*) FROM refresh_replacement').fetchone() == (
                        0 if case == 'commit-busy' else 1,)
                for revision in ('fixture-old', 'fixture-new'):
                    assert fence(ident).begin(revision, now=100) is None
                assert_record(ids[2], 'fixture-old')
                assert manager.removeAuthenticationConfig(ident)
                case_results.append(dict(case=case, ack=ack, native_readback=True,
                                         committed=case != 'commit-busy', no_rearm=True,
                                         commit_before_ack=True, sentinel_exact=True))
            assert set(manager.availableAuthMethodConfigs()) == expected_ids
            result['committed_handoff_cases'] = case_results
        if phase in ('cancel-write', 'expire-write'):
            ident = ids[0] if phase == 'cancel-write' else ids[1]
            assert_record(ident, 'fixture-old')
            assert fence(ident).begin('fixture-old', now=100) is not None
            fence_before = hashlib.sha256(fence(ident).path.read_bytes()).hexdigest()
            clock = [0]
            flow = RefreshFlow(lambda: clock[0], pair(ident, 'fixture-old'))
            request = flow.start('SYNTHETIC-CLIENT')
            assert request is not None
            replacement = pair(ident, 'fixture-new')
            assert flow.receive(request.key, 200, replacement)
            handed = flow.pending_save(request.key)
            assert handed == replacement and flow.take_tokens() is None
            events, failures = [], []
            loop = QEventLoop()

            def stop_consumer():
                try:
                    if phase == 'cancel-write':
                        flow.cancel()
                    else:
                        clock[0] = 30
                        assert flow.pending_save(request.key) is None
                    assert flow.state == 'reauth_required'
                    events.append('consumer-stopped')
                except BaseException as error:
                    failures.append(error)
                    loop.quit()

            def late_native_write():
                try:
                    assert events == ['consumer-stopped']
                    config = load(ident)
                    config.setConfig('Authorization', json.dumps(handed, sort_keys=True))
                    config.setConfig('fixture_revision', 'fixture-new')
                    assert manager.updateAuthenticationConfig(config) is True
                    manager.clearAllCachedConfigs()
                    assert_record(ident, 'fixture-new')
                    events.append('native-write-and-readback')
                    assert flow.saved(request.key, True) is False
                    assert flow.take_tokens() is None and flow.pending_save(request.key) is None
                    assert flow.state == 'reauth_required'
                    assert flow.start('SYNTHETIC-CLIENT') is None
                    assert hashlib.sha256(fence(ident).path.read_bytes()).hexdigest() == fence_before
                    for revision in ('fixture-old', 'fixture-new'):
                        assert fence(ident).begin(revision, now=100) is None
                    assert_record(ids[2], 'fixture-old')
                    events.append('late-ack-and-retry-refused')
                except BaseException as error:
                    failures.append(error)
                finally:
                    loop.quit()

            QTimer.singleShot(0, stop_consumer)
            QTimer.singleShot(25, late_native_write)
            watchdog = QTimer()
            watchdog.setSingleShot(True)
            watchdog.timeout.connect(loop.quit)
            watchdog.start(5000)
            loop.exec()
            watchdog.stop()
            if failures:
                raise failures[0]
            assert events == ['consumer-stopped', 'native-write-and-readback', 'late-ack-and-retry-refused']
            result.update(events=events, native_replacement_readback=True,
                          late_ack_refused=True, uncertain_fence_unchanged=True)
        revisions = {ids[0]: 'fixture-new' if phase != 'seed' else 'fixture-old',
                     ids[1]: 'fixture-new' if phase in ('expire-write', 'cold-expire', 'bound-admission', 'readback-ack', 'cold-ack', 'record-replacement', 'cold-replacement', 'committed-handoff', 'cleanup') else 'fixture-old',
                     ids[2]: 'fixture-old'}
        for ident, revision in revisions.items():
            assert_record(ident, revision)
        result['exact_target_and_sentinel'] = True
        if phase in ('cold-cancel', 'cold-expire', 'cleanup'):
            targets = ids[:1] if phase == 'cold-cancel' else ids[:2]
            for ident in targets:
                before = fence(ident).path.read_bytes()
                for revision in ('fixture-old', 'fixture-new'):
                    assert fence(ident).begin(revision, now=100) is None
                assert fence(ident).path.read_bytes() == before
                with closing(sqlite3.connect(fence(ident).path)) as conn:
                    state, attempt, revision, expiry = conn.execute(
                        'SELECT state,attempt,revision,expires_at FROM refresh_fence').fetchone()
                assert state == 'uncertain' and len(attempt) == 32
                assert revision == 'fixture-old' and expiry == 200
            result['cold_replacement_readback_and_retry_refusal'] = True
        if phase == 'cleanup':
            for ident in (*ids, 'agack01'):
                assert manager.removeAuthenticationConfig(ident)
            assert not manager.availableAuthMethodConfigs()
            result['zero_configs'] = True
        for path in scratch.rglob('*'):
            if path.is_file():
                data = path.read_bytes()
                assert marker.encode() not in data and password.encode() not in data
        result['scratch_plaintext_absent'] = True
    finally:
        manager.clearAllCachedConfigs()
        manager.clearMasterPassword()
        app.exitQgis()
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
