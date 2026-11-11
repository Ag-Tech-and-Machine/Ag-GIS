# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    """UNWIRED synthetic native failed-update/cold-read experiment, not login.

    

    Only the matching runner's fresh marked scratch store is accepted. APIHeader is

    used solely as an encrypted storage fixture, NEVER expanded into any request.

    Cold old-value recovery characterizes an ambiguity hazard, NOT safe token reuse.

    """

    import hashlib

    import json

    import os

    from pathlib import Path

    import sqlite3

    import time

    

    

    def main():

        scratch = Path(os.environ['AGGIS_SYNTHETIC_AUTH_ROOT']).resolve()

        allowed = Path('C:/Users/Michael/AppData/Local/hermes/cache/scratch').resolve()

        assert scratch.is_relative_to(allowed) and scratch.name.startswith('aggis-auth-failure-')

        assert (scratch / 'SYNTHETIC-ONLY').read_text() == 'fresh-synthetic-auth-failure-v1'

        phase = os.environ['AGGIS_SYNTHETIC_AUTH_PHASE']

        assert phase in ('seed', 'locked-update', 'cold', 'unlocked-update', 'cold-new', 'cleanup')

        secret = os.environ['AGGIS_SYNTHETIC_AUTH_VALUE']

        password = os.environ['AGGIS_SYNTHETIC_AUTH_PASSWORD']

        assert secret.startswith('AGGIS-SYNTHETIC-NOT-A-TOKEN-')

        assert password.startswith('AGGIS-SYNTHETIC-PASSWORD-')

        authdir = scratch / 'auth'

        authdir.mkdir(exist_ok=True)

        os.environ['QGIS_AUTH_DB_DIR_PATH'] = str(authdir)

        # initQgis can replace the constructor path; pin before native initialization.

        os.environ['QGIS_CUSTOM_CONFIG_PATH'] = str(scratch / 'profile')

        os.environ.pop('QGIS_AUTH_PASSWORD_FILE', None)

        os.environ['QT_QPA_PLATFORM'] = 'offscreen'

        from qgis.PyQt.QtCore import QSettings

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
            from qgis.core import QgsApplication, QgsAuthMethodConfig, Qgis
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this test

    QSettings.setDefaultFormat(QSettings.IniFormat)

    for scope in (QSettings.UserScope, QSettings.SystemScope):

        QSettings.setPath(QSettings.IniFormat, scope, str(scratch / 'settings'))

    app = QgsApplication([], False, str(scratch / 'profile'))

    app.initQgis()

    assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(scratch), \

        'Native QGIS settings must resolve inside the marked scratch root'

    assert Path(QSettings().fileName()).resolve().is_relative_to(scratch), \

        'Qt settings must resolve inside the marked scratch root'

    manager = QgsApplication.authManager()

    result = {'phase': phase, 'qgis': Qgis.QGIS_VERSION, 'synthetic_only': True,

              'no_network_or_header_expansion': True, 'pid': os.getpid(),

              'native_settings_path': str(Path(QgsApplication.qgisSettingsDirPath()).resolve()),

              'qt_settings_path': str(Path(QSettings().fileName()).resolve())}

    try:

        dbpath = Path(manager.authenticationDatabasePath()).resolve()

        assert dbpath == authdir / 'qgis-auth.db' and not manager.isDisabled()

        manager.setPasswordHelperEnabled(False)

        assert manager.setMasterPassword(password, True)

        def load(ident):

            ok, config = manager.loadAuthenticationConfig(ident, QgsAuthMethodConfig(), True)

            assert ok is True

            return config

        if phase == 'seed':

            assert not manager.availableAuthMethodConfigs()

            for ident in ('aggisf1', 'aggisf2'):

                config = QgsAuthMethodConfig()

                config.setId(ident)

                config.setName('Synthetic failed-update fixture ' + ident)

                config.setMethod('APIHeader')

                config.setVersion(2)

                config.setUri('https://example.invalid')

                config.setConfig('Authorization', secret + '-old-' + ident)

                ok, returned = manager.storeAuthenticationConfig(config, False)

                assert ok is True and returned.id() == ident

            result['seeded_two'] = True

        assert set(manager.availableAuthMethodConfigs()) == {'aggisf1', 'aggisf2'}

        if phase == 'locked-update':

            config = load('aggisf1')

            config.setConfig('Authorization', secret + '-replacement')

            before = hashlib.sha256(dbpath.read_bytes()).hexdigest()

            lock = sqlite3.connect(dbpath, timeout=0)

            try:

                lock.execute('BEGIN IMMEDIATE')

                # An independent writer must also be refused: prove real contention.

                contender = sqlite3.connect(dbpath, timeout=0)

                try:

                    try:

                        contender.execute('BEGIN IMMEDIATE')

                    except sqlite3.OperationalError as error:

                        assert 'locked' in str(error).lower()

                    else:

                        raise AssertionError('Independent writer was not refused')

                finally:

                    contender.close()

                started = time.monotonic()

                ok = manager.updateAuthenticationConfig(config)

                result['update_seconds'] = round(time.monotonic() - started, 3)

                assert ok is False, 'Actual protected update must fail under held writer lock'

                assert hashlib.sha256(dbpath.read_bytes()).hexdigest() == before

                result['actual_update_refused'] = result['db_bytes_unchanged'] = True

            finally:

                lock.rollback()

                lock.close()

            manager.clearAllCachedConfigs()

        if phase == 'unlocked-update':

            config = load('aggisf1')

            config.setConfig('Authorization', secret + '-replacement')

            assert manager.updateAuthenticationConfig(config) is True

            manager.clearAllCachedConfigs()

            result['actual_unlocked_update_succeeded'] = True

        replacement = phase in ('unlocked-update', 'cold-new', 'cleanup')

        for ident in ('aggisf1', 'aggisf2'):

            expected = secret + '-replacement' if replacement and ident == 'aggisf1' else secret + '-old-' + ident

            assert load(ident).config('Authorization') == expected

            ok, metadata = manager.loadAuthenticationConfig(ident, QgsAuthMethodConfig(), False)

            assert ok is True and not metadata.configMap()

        result['exact_target_and_sentinel'] = result['metadata_excludes_secret'] = True

        result['target_is_replacement'] = replacement

        if phase == 'cold':

            # The encrypted store alone has no record of a remote refresh attempt.

            # Deliberately no request, retry, success ack or recovered-token handoff.

            result['old_value_survives_cold_failure'] = True

            result['safe_refresh_recovery_implemented'] = False

        if phase == 'cleanup':

            for ident in ('aggisf1', 'aggisf2'):

                assert manager.removeAuthenticationConfig(ident)

            assert not manager.availableAuthMethodConfigs()

            result['zero_configs'] = True

        for path in scratch.rglob('*'):

            if path.is_file():

                data = path.read_bytes()

                assert secret.encode() not in data and password.encode() not in data

        result['scratch_plaintext_absent'] = True

    finally:

        manager.clearAllCachedConfigs()

        manager.clearMasterPassword()

        app.exitQgis()

    print(json.dumps(result, sort_keys=True))





if __name__ == '__main__':

    main()


