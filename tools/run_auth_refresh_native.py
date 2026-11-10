"""Run synthetic native late writes and cold refusal; NOT product login."""
import argparse
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
PHASES = ('seed', 'cancel-write', 'cold-cancel', 'expire-write', 'cold-expire',
          'bound-admission', 'readback-ack', 'cold-ack', 'record-replacement', 'cold-replacement', 'committed-handoff', 'cleanup')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qgis-root', type=Path, default=Path('C:/Program Files/QGIS 3.44.14'))
    args = parser.parse_args()
    bootstrap = args.qgis_root / 'bin/python-qgis-ltr.bat'
    if os.name != 'nt' or not bootstrap.is_file() or not BASE.is_dir():
        raise SystemExit('Requires existing Windows QGIS runtime and your agent scratch; nothing installed.')
    out = ROOT / '.aggis-agent/evidence' / ('auth-refresh-native-' + uuid.uuid4().hex)
    out.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix='aggis-auth-late-', dir=BASE))
    (scratch / 'SYNTHETIC-ONLY').write_text('fresh-synthetic-auth-late-v1')
    temp = scratch / 'runtime-temp'
    temp.mkdir()
    shim = scratch / 'run_qgis.py'
    shim.write_text(
        'import os,sys,tempfile,runpy\nfrom pathlib import Path\np=Path(' + repr(str(temp)) + ')\n'
        'for k in ("TEMP","TMP","TMPDIR"):os.environ[k]=str(p)\n'
        'tempfile.tempdir=str(p)\ns=sys.argv[1];sys.path.insert(0,str(Path(s).parent));'
        'sys.argv=[s];runpy.run_path(s,run_name="__main__")\n', encoding='utf-8')
    script = ROOT / 'tools/auth_refresh_native_test.py'
    value = 'AGGIS-SYNTHETIC-NOT-A-TOKEN-' + secrets.token_hex(24)
    password = 'AGGIS-SYNTHETIC-PASSWORD-' + secrets.token_hex(24)
    env = dict(os.environ, AGGIS_SYNTHETIC_AUTH_ROOT=str(scratch),
               AGGIS_SYNTHETIC_AUTH_VALUE=value, AGGIS_SYNTHETIC_AUTH_PASSWORD=password,
               PYTHONDONTWRITEBYTECODE='1')
    for key in ('QGIS_AUTH_PASSWORD_FILE', 'QGIS_AUTH_DB_URI', 'QGIS_CUSTOM_CONFIG_PATH'):
        env.pop(key, None)
    receipts = []
    inputs = {name: hashlib.sha256((ROOT / 'tools' / name).read_bytes()).hexdigest()
              for name in ('auth_refresh_native_test.py', 'run_auth_refresh_native.py',
                           'auth_flow_model.py', 'auth_refresh_fence.py', 'auth_refresh_readback.py')}
    for phase in PHASES:
        env['AGGIS_SYNTHETIC_AUTH_PHASE'] = phase
        command = [str(bootstrap), str(shim), str(script)]
        process = subprocess.run(command, env=env, cwd=scratch, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=90)
        if value.encode() in process.stdout or password.encode() in process.stdout:
            raise RuntimeError('Synthetic marker in output; output not persisted')
        rows = [json.loads(line) for line in process.stdout.decode('utf-8', errors='replace').splitlines()
                if line.startswith('{')]
        if process.returncode == 0:
            assert len(rows) == 1 and rows[0]['phase'] == phase
            row = rows[0]
            assert row['scratch_plaintext_absent'] is True
            assert row['exact_target_and_sentinel'] is True
            for key in ('native_settings_path', 'qt_settings_path'):
                assert Path(row[key]).resolve().is_relative_to(scratch)
            if phase in ('cancel-write', 'expire-write'):
                assert row['events'] == ['consumer-stopped', 'native-write-and-readback',
                                         'late-ack-and-retry-refused']
                assert row['late_ack_refused'] is True and row['native_replacement_readback'] is True
            if phase in ('cold-cancel', 'cold-expire', 'cleanup'):
                assert row['cold_replacement_readback_and_retry_refusal'] is True
            if phase == 'bound-admission':
                expected = ('exact', 'wrong-revision', 'wrong-expiry', 'expired',
                            'missing-record', 'malformed-expiry')
                assert tuple(case['case'] for case in row['bound_admission_cases']) == expected
                for case in row['bound_admission_cases']:
                    assert case['native_loaded'] is (case['case'] != 'missing-record')
                    assert case['request_created'] is (case['case'] == 'exact')
                    expected_state = ('uncertain' if case['case'] == 'exact' else
                                      'expired' if case['case'] == 'expired' else 'ready')
                    assert case['fence_state'] == expected_state and case['sentinel_exact'] is True
            if phase == 'readback-ack':
                expected_cases = ('exact', 'stale-pair', 'wrong-revision', 'wrong-expiry',
                                  'missing-record', 'cancel-in-readback', 'expire-in-readback',
                                  'wrong-attempt', 'wrong-fence-revision', 'expired-fence',
                                  'wrong-protected-slot', 'wrong-protected-attempt',
                                  'wrong-protected-old-revision', 'missing-protected-attempt')
                assert tuple(case['case'] for case in row['readback_cases']) == expected_cases
                for case in row['readback_cases']:
                    assert case['native_update'] is True
                    assert case['ack'] is (case['case'] == 'exact')
                    assert case['attempt_gate'] is True
                    assert case['protected_attempt_gate'] is True
                    assert case['native_read_called'] is (case['case'] not in
                        ('wrong-attempt', 'wrong-fence-revision', 'expired-fence'))
                    assert case['fence_uncertain_unchanged'] is True and case['sentinel_exact'] is True
            if phase in ('cold-ack', 'cleanup'):
                assert row['cold_exact_replacement_no_rearm'] is True
            if phase in ('record-replacement', 'cold-replacement', 'committed-handoff', 'cleanup'):
                assert row['terminal_receipt_exact'] is True
                assert row['terminal_no_rearm'] is True and row['terminal_no_model_handoff'] is True
                if phase == 'record-replacement':
                    assert row['native_exact_readback_then_terminal_commit'] is True
                else:
                    assert row['cold_terminal_receipt_no_read_replay'] is True
            if phase == 'committed-handoff':
                cases = row['committed_handoff_cases']
                assert tuple(case['case'] for case in cases) == (
                    'exact', 'cancel-after-commit', 'expire-after-commit', 'commit-busy')
                for case in cases:
                    assert case['ack'] is (case['case'] == 'exact')
                    assert case['committed'] is (case['case'] != 'commit-busy')
                    assert all(case[key] is True for key in (
                        'native_readback', 'no_rearm', 'commit_before_ack', 'sentinel_exact'))
            if phase == 'cleanup':
                assert row['zero_configs'] is True
        log = out / (phase + '.log')
        log.write_bytes(process.stdout)
        receipts.append({'phase': phase, 'exit_code': process.returncode, 'command': command,
                         'log': str(log), 'sha256': hashlib.sha256(process.stdout).hexdigest(),
                         'receipt': rows[0] if len(rows) == 1 else None})
        report = {'created': datetime.now().astimezone().isoformat(), 'scratch': str(scratch),
                  'input_sha256': inputs, 'receipts': receipts, 'product_login': False}
        (out / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(phase, 'exit', process.returncode, flush=True)
        if process.returncode:
            raise SystemExit('Native characterization failed; retain receipts at ' + str(out))
    assert len({row['receipt']['pid'] for row in receipts}) == len(PHASES)
    print('Twelve isolated native processes passed; synthetic commit-before-ack only, no product adapter, rearm or remote rotation.')
    print('Readback:', out / 'results.json')


if __name__ == '__main__':
    main()
