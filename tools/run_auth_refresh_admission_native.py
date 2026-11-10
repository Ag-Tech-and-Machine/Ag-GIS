"""Run isolated native binding/crash processes, never product login or network."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('C:/Users/[Maintainer]/AppData/Local/hermes/cache/scratch')
CRASH_PHASES = ('crash-before-write', 'crash-after-write', 'crash-after-readback', 'crash-after-request')
PHASES = ('seed', 'bind') + CRASH_PHASES + ('cold', 'cleanup')


def main():
    bootstrap = Path('C:/Program Files/QGIS 3.44.14/bin/python-qgis-ltr.bat')
    assert os.name == 'nt' and bootstrap.is_file() and BASE.is_dir()
    out = ROOT / '.aggis-agent/evidence' / ('auth-pre-request-native-' + uuid.uuid4().hex)
    out.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix='aggis-pre-bind-', dir=BASE))
    (scratch / 'SYNTHETIC-ONLY').write_text('fresh-synthetic-pre-bind-v1')
    temp = scratch / 'runtime-temp'
    temp.mkdir()
    shim = scratch / 'run_qgis.py'
    shim.write_text(
        'import os,sys,tempfile,runpy\nfrom pathlib import Path\np=Path(' + repr(str(temp)) + ')\n'
        'for k in ("TEMP","TMP","TMPDIR"):os.environ[k]=str(p)\n'
        'tempfile.tempdir=str(p)\ns=sys.argv[1];sys.path.insert(0,str(Path(s).parent));'
        'sys.argv=[s];runpy.run_path(s,run_name="__main__")\n', encoding='utf-8')
    value = 'AGGIS-SYNTHETIC-NOT-A-TOKEN-' + secrets.token_hex(24)
    password = 'AGGIS-SYNTHETIC-PASSWORD-' + secrets.token_hex(24)
    env = dict(os.environ, AGGIS_SYNTHETIC_AUTH_ROOT=str(scratch),
               AGGIS_SYNTHETIC_AUTH_VALUE=value, AGGIS_SYNTHETIC_AUTH_PASSWORD=password,
               PYTHONDONTWRITEBYTECODE='1')
    for key in ('QGIS_AUTH_PASSWORD_FILE', 'QGIS_AUTH_DB_URI', 'QGIS_CUSTOM_CONFIG_PATH'):
        env.pop(key, None)
    inputs = {name: hashlib.sha256((ROOT / 'tools' / name).read_bytes()).hexdigest()
              for name in ('auth_refresh_admission_native_test.py', 'run_auth_refresh_admission_native.py',
                           'auth_flow_model.py', 'auth_refresh_fence.py', 'auth_refresh_readback.py')}
    receipts = []
    for phase in PHASES:
        env['AGGIS_SYNTHETIC_AUTH_PHASE'] = phase
        command = [str(bootstrap), str(shim), str(ROOT / 'tools/auth_refresh_admission_native_test.py')]
        p = subprocess.run(command, cwd=scratch, env=env, capture_output=True, timeout=90)
        raw = p.stdout + p.stderr
        if value.encode() in raw or password.encode() in raw:
            raise RuntimeError('Synthetic marker in output; output not retained')
        log = out / (phase + '.log')
        log.write_bytes(raw)
        rows = [json.loads(line) for line in raw.decode('utf-8', errors='replace').splitlines()
                if line.startswith('{')]
        row = rows[0] if len(rows) == 1 else None
        receipts.append(dict(phase=phase, exit_code=p.returncode, log=str(log),
                             sha256=hashlib.sha256(raw).hexdigest(), receipt=row))
        (out / 'results.json').write_text(json.dumps(dict(
            created=datetime.now().astimezone().isoformat(), scratch=str(scratch),
            input_sha256=inputs, receipts=receipts, product_login=False), indent=2))
        print(phase, 'exit', p.returncode, flush=True)
        expected_exit = 41 + CRASH_PHASES.index(phase) if phase in CRASH_PHASES else 0
        assert p.returncode == expected_exit and row is not None, str(out)
        assert row['phase'] == phase and row['scratch_plaintext_absent'] is True
        assert row['sentinel_exact'] is True and row['network_used'] is False
        if phase in CRASH_PHASES:
            assert row['abrupt_exit'] == expected_exit and row['uncertain_before_exit'] is True
        for key in ('native_settings_path', 'qt_settings_path'):
            assert Path(row[key]).resolve().is_relative_to(scratch)
        if phase == 'bind':
            assert tuple(c['case'] for c in row['cases']) == (
                'exact', 'changed-original', 'wrong-pair', 'wrong-attempt', 'write-locked', 'expired-after-write')
            for case in row['cases']:
                assert case['request_created'] is (case['case'] == 'exact')
                assert case['uncertain'] is True and case['sentinel_exact'] is True
        if phase in ('cold', 'cleanup'):
            assert row['cold_exact_records_and_no_retry'] is True
            assert tuple(row['cold_crash_cases']) == CRASH_PHASES
        if phase == 'cleanup':
            assert row['zero_configs'] is True
    assert len({r['receipt']['pid'] for r in receipts}) == len(PHASES)
    assert receipts[0]['receipt']['seeded'] == 11
    print('Eight fresh native processes/six binding and four abrupt-exit cases passed; eleven synthetic records removed.')
    print('Readback:', out / 'results.json')


if __name__ == '__main__':
    main()
