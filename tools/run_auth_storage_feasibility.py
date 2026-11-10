"""Run only synthetic protected-storage checks in a new isolated Windows directory."""
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
BASE = Path('C:/temp/AppData/Local/tool/cache/scratch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qgis-root', type=Path, default=Path('C:/Program Files/QGIS 3.44.14'))
    args = parser.parse_args()
    bootstrap = args.qgis_root / 'bin/python-qgis-ltr.bat'
    if os.name != 'nt' or not bootstrap.is_file() or not BASE.is_dir():
        raise SystemExit('Requires Windows, the existing QGIS runtime and your agent scratch; nothing installed.')
    out = ROOT / '.aggis-agent/evidence' / ('auth-storage-' + uuid.uuid4().hex)
    out.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix='aggis-auth-feasibility-', dir=BASE))
    (scratch / 'SYNTHETIC-ONLY').write_text('fresh-synthetic-auth-feasibility-v1')
    temp = scratch / 'runtime-temp'
    temp.mkdir()
    shim = scratch / 'run_qgis.py'
    shim.write_text(
        'import os,sys,tempfile,runpy\nfrom pathlib import Path\np=Path(' + repr(str(temp)) + ')\n'
        'for k in ("TEMP","TMP","TMPDIR"):os.environ[k]=str(p)\n'
        'tempfile.tempdir=str(p)\ns=sys.argv[1];sys.path.insert(0,str(Path(s).parent));'
        'sys.argv=[s];runpy.run_path(s,run_name="__main__")\n', encoding='utf-8')
    script = ROOT / 'tools/auth_storage_feasibility_test.py'
    value = 'AGGIS-SYNTHETIC-NOT-A-TOKEN-' + secrets.token_hex(24)
    password = 'AGGIS-SYNTHETIC-PASSWORD-' + secrets.token_hex(24)
    env = dict(os.environ, AGGIS_SYNTHETIC_AUTH_ROOT=str(scratch),
               AGGIS_SYNTHETIC_AUTH_VALUE=value, AGGIS_SYNTHETIC_AUTH_PASSWORD=password)
    for key in ('QGIS_AUTH_PASSWORD_FILE', 'QGIS_AUTH_DB_URI', 'QGIS_CUSTOM_CONFIG_PATH'):
        env.pop(key, None)
    receipts = []
    for phase in ('seed', 'reopen', 'delete', 'absent'):
        env['AGGIS_SYNTHETIC_AUTH_PHASE'] = phase
        command = [str(bootstrap), str(shim), str(script)]
        process = subprocess.run(command, env=env, cwd=scratch, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=90)
        if value.encode() in process.stdout or password.encode() in process.stdout:
            raise RuntimeError('Synthetic value leaked to process output; output not saved')
        log = out / (phase + '.log')
        log.write_bytes(process.stdout)
        receipts.append({'phase': phase, 'exit_code': process.returncode, 'command': command,
                         'log': str(log), 'sha256': hashlib.sha256(process.stdout).hexdigest()})
        report = {'created': datetime.now().astimezone().isoformat(), 'scratch': str(scratch),
                  'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(), 'receipts': receipts}
        (out / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(phase, 'exit', process.returncode, flush=True)
        if process.returncode:
            raise SystemExit('Synthetic check failed; retain receipts at ' + str(out))
    print('Four native processes passed. Synthetic auth configs deleted, not provider revocation.')
    print('Readback:', out / 'results.json')


if __name__ == '__main__':
    main()
