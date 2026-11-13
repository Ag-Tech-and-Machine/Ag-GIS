"""Run real QGIS application recorder/export audit with synthetic loopback traffic."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
QGIS = Path('C:/Program Files/QGIS 3.44.14')
BASE = Path('C:/temp/AppData/Local/tool/cache/scratch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin-root', type=Path, default=ROOT / 'plugins/ag_tech_tooling')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    plugin = args.plugin_root.resolve()
    out = (args.evidence or ROOT / '.aggis-agent/evidence' / ('recorder-' + uuid.uuid4().hex)).resolve()
    out.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix='aggis-recorder-', dir=BASE))
    (scratch / 'SYNTHETIC-ONLY').write_text('recorder-v1')
    temp = scratch / 'runtime-temp'
    temp.mkdir()
    (scratch / 'auth').mkdir()
    raw = subprocess.check_output(
        f'cmd.exe /d /s /c ""{QGIS / "bin/o4w_env.bat"}" && set"', text=True)
    env = dict(os.environ)
    for line in raw.splitlines():
        if '=' in line and not line.startswith('='):
            key, value = line.split('=', 1)
            env[key] = value
    for key in ('PYQGIS_STARTUP', 'QGIS_AUTH_PASSWORD_FILE', 'QGIS_AUTH_DB_URI',
                'QGIS_DEBUG_FILE', 'QGIS_LOG_FILE'):
        env.pop(key, None)
    env.update(PATH=str(QGIS / 'apps/qgis-ltr/bin') + ';' + env['PATH'],
               QGIS_PREFIX_PATH=str(QGIS / 'apps/qgis-ltr'),
               QT_PLUGIN_PATH=str(QGIS / 'apps/qgis-ltr/qtplugins') + ';' + str(QGIS / 'apps/qt5/plugins'),
               PYTHONDONTWRITEBYTECODE='1', PYTHONFAULTHANDLER='1',
               AGGIS_RECORDER_SCRATCH=str(scratch), AGGIS_RECORDER_PLUGIN=str(plugin),
               QGIS_CUSTOM_CONFIG_PATH=str(scratch / 'config'), QGIS_AUTH_DB_DIR_PATH=str(scratch / 'auth'),
               TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    env.pop('QT_QPA_PLATFORM', None)
    script = ROOT / 'tools/github_recorder_test.py'
    command = [str(QGIS / 'bin/qgis-ltr-bin.exe'), '--nologo', '--noplugins',
               '--profiles-path', str(scratch / 'config'), '--profile', 'recorder', '--code', str(script)]
    # Files avoid a native crash reporter retaining the parent's stdout pipes.
    with (out / 'stdout.log').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(command, env=env, cwd=scratch, stdout=stdout, stderr=stderr)
        try:
            exit_code = process.wait(timeout=55)
        except subprocess.TimeoutExpired:
            # Never kill team's QGIS. Leave a handle and report the exact test PID.
            (out / 'timeout.json').write_text(json.dumps(dict(pid=process.pid, scratch=str(scratch))))
            raise RuntimeError('Synthetic recorder application did not close; inspect test PID ' + str(process.pid))
    receipt = dict(created=datetime.now().astimezone().isoformat(), exit_code=exit_code,
                   pid=process.pid, command=command, scratch=str(scratch), plugin=str(plugin))
    if (scratch / 'assertions.json').exists():
        data = (scratch / 'assertions.json').read_bytes()
        (out / 'assertions.json').write_bytes(data)
        receipt['assertions'] = json.loads(data)
    receipt['inputs'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (Path(__file__), script, plugin / 'github_transport.py', plugin / 'github_session.py')}
    (out / 'process.json').write_text(json.dumps(receipt, indent=2))
    print(out / 'process.json')
    assert exit_code == 0, 'native application did not exit normally'
    assert receipt.get('assertions', {}).get('passed') is True, receipt.get('assertions', {})
    for name in ('stdout.log', 'stderr.log'):
        data = (out / name).read_bytes()
        assert b'SYNTHETIC-RECORDER-' not in data and b'ABCD-EFGH' not in data, 'synthetic value in process diagnostics'
    print('PASS native recorder known exposure; NOT real-credential clearance')


if __name__ == '__main__':
    main()
