"""Developer-only native storage experiment; no login or existing credential access.

Run through QGIS Python via the isolated runner documented in TOOLING.md.
Only a newly created, explicitly marked your agent scratch directory is accepted.
No product imports, network requests, credential enumeration or OS vault entries.
"""
from pathlib import Path
import ctypes
from ctypes import wintypes
import json
import os
import sys


def dpapi_roundtrip(secret):
    class Blob(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_ubyte))]

    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    crypt.CryptProtectData.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptProtectData.restype = crypt.CryptUnprotectData.restype = wintypes.BOOL

    def call(data, protect):
        buf = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        source = Blob(len(data), buf)
        target = Blob()
        fn = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
        # UI_FORBIDDEN only; never LOCAL_MACHINE, prompts or named OS credentials.
        ok = fn(ctypes.byref(source), 'Ag-GIS synthetic feasibility' if protect else None,
                None, None, None, 1, ctypes.byref(target))
        try:
            if not ok:
                raise OSError(ctypes.get_last_error(), 'Synthetic DPAPI operation failed')
            return ctypes.string_at(target.pbData, target.cbData)
        finally:
            if target.pbData:
                ctypes.memset(target.pbData, 0, target.cbData)
                kernel.LocalFree(target.pbData)

    encrypted = call(secret, True)
    assert secret not in encrypted and encrypted != secret
    assert call(encrypted, False) == secret
    # An invalid/truncated envelope must not return usable plaintext. This is not
    # a general claim that every possible corrupted DPAPI blob is always rejected.
    try:
        call(encrypted[:12], False)
    except OSError:
        pass
    else:
        raise AssertionError('Truncated DPAPI envelope accepted')
    return {'roundtrip': True, 'plaintext_absent': True, 'truncated_refused': True,
            'scope': 'current-user', 'ui_forbidden': True, 'persisted': False}


def main():
    scratch = Path(os.environ['AGGIS_SYNTHETIC_AUTH_ROOT']).resolve()
    allowed = Path('C:/temp/AppData/Local/hermes/cache/scratch').resolve()
    assert scratch.is_relative_to(allowed) and scratch.name.startswith('aggis-auth-feasibility-')
    assert (scratch / 'SYNTHETIC-ONLY').read_text() == 'fresh-synthetic-auth-feasibility-v1'
    phase = os.environ['AGGIS_SYNTHETIC_AUTH_PHASE']
    assert phase in ('seed', 'reopen', 'delete', 'absent')
    authdir = scratch / 'auth'
    authdir.mkdir(exist_ok=True)
    # Set before importing/initializing the application. The runner also resets
    # tempfile after the vendor batch bootstrap, which can overwrite TEMP.
    os.environ['QGIS_AUTH_DB_DIR_PATH'] = str(authdir)
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
    result = {'phase': phase, 'qgis': Qgis.QGIS_VERSION, 'synthetic_only': True}
    try:
        assert not manager.isDisabled()
        assert Path(manager.authenticationDatabasePath()).resolve() == authdir / 'qgis-auth.db'
        # Disable OS password helper only in this isolated app's scratch settings.
        # No read/write of an existing Windows Credential Manager/keychain entry.
        manager.setPasswordHelperEnabled(False)
        secret = os.environ['AGGIS_SYNTHETIC_AUTH_VALUE']
        password = os.environ['AGGIS_SYNTHETIC_AUTH_PASSWORD']
        assert secret.startswith('AGGIS-SYNTHETIC-NOT-A-TOKEN-')
        assert password.startswith('AGGIS-SYNTHETIC-PASSWORD-')
        assert not manager.masterPasswordIsSet()
        if phase != 'seed':
            assert not manager.setMasterPassword(password + '-wrong', True)
            result['wrong_password_refused'] = True
        assert manager.setMasterPassword(password, True)
        target_id, sentinel_id = 'aggist1', 'aggist2'
        def load(ident, full):
            config = QgsAuthMethodConfig()
            ok, loaded = manager.loadAuthenticationConfig(ident, config, full)
            assert isinstance(ok, bool)
            return ok, loaded
        if phase == 'seed':
            assert not manager.availableAuthMethodConfigs()
            assert 'APIHeader' in manager.authMethodsKeys()
            for ident in (target_id, sentinel_id):
                config = QgsAuthMethodConfig()
                config.setId(ident)
                config.setName('Synthetic feasibility ' + ident)
                config.setMethod('APIHeader')
                config.setVersion(2)
                config.setUri('https://example.invalid')
                config.setConfig('Authorization', 'Bearer ' + secret + ident)
                assert config.isValid()
                stored, returned = manager.storeAuthenticationConfig(config, False)
                assert stored is True and returned.id() == ident
            result['created_two_configs'] = True
        if phase in ('seed', 'reopen', 'delete'):
            for ident in (target_id, sentinel_id):
                ok, config = load(ident, True)
                assert ok and config.config('Authorization') == 'Bearer ' + secret + ident
                ok, metadata = load(ident, False)
                assert ok and not metadata.configMap()
            result['native_full_load_exact'] = result['metadata_excludes_secret'] = True
        if phase == 'delete':
            assert manager.removeAuthenticationConfig(target_id)
            assert target_id not in manager.availableAuthMethodConfigs()
            assert not load(target_id, True)[0]
            assert load(sentinel_id, True)[0]
            result['target_deleted_sentinel_retained'] = True
        if phase == 'absent':
            assert target_id not in manager.availableAuthMethodConfigs()
            assert not load(target_id, True)[0]
            assert load(sentinel_id, True)[1].config('Authorization') == 'Bearer ' + secret + sentinel_id
            assert manager.removeAuthenticationConfig(sentinel_id)
            assert not manager.availableAuthMethodConfigs()
            result['cold_deleted_absent_cleanup'] = True
        # Read only this newly generated store/settings, never a normal profile.
        for path in scratch.rglob('*'):
            if path.is_file() and path.name != 'SYNTHETIC-ONLY':
                data = path.read_bytes()
                assert secret.encode() not in data and password.encode() not in data
        result['scratch_plaintext_absent'] = True
        if phase == 'seed':
            result['dpapi'] = dpapi_roundtrip(secret.encode())
        # APIHeader's native expansion logs header values at debug level 2.
        # Do NOT expand/send here or confuse storage with safe GitHub networking.
        result['no_header_expansion_or_network'] = True
    finally:
        manager.clearAllCachedConfigs()
        manager.clearMasterPassword()
        app.exitQgis()
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
