"""Run production connection UI checks in fresh isolated synthetic QGIS processes."""
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
BASE = Path('C:/temp/AppData/Local/tool/cache/scratch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin-root', type=Path, default=ROOT / 'plugins/ag_tech_tooling')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    plugin = args.plugin_root.resolve()
    out = (args.evidence or ROOT / '.aggis-agent/evidence' / ('connection-' + uuid.uuid4().hex)).resolve()
    out.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix='aggis-connection-', dir=BASE))
    (scratch / 'SYNTHETIC-ONLY').write_text('connection-v1')
    temp = scratch / 'runtime-temp'
    temp.mkdir()
    shim = scratch / 'run.py'
    script = ROOT / 'tools/github_connection_test.py'
    shim.write_text('import os,sys,tempfile,runpy\nfrom pathlib import Path\np=Path(' + repr(str(temp)) + ')\n'
                    'for k in ("TEMP","TMP","TMPDIR"):os.environ[k]=str(p)\n'
                    'tempfile.tempdir=str(p)\ns=sys.argv[1];sys.path.insert(0,str(Path(s).parent));'
                    'sys.argv=[s];runpy.run_path(s,run_name="__main__")\n')
    env = dict(os.environ, PYTHONFAULTHANDLER='1', PYTHONDONTWRITEBYTECODE='1',
               AGGIS_CONNECTION_SCRATCH=str(scratch), AGGIS_CONNECTION_PLUGIN=str(plugin))
    for key in ('QGIS_AUTH_PASSWORD_FILE', 'QGIS_AUTH_DB_URI', 'PYQGIS_STARTUP'):
        env.pop(key, None)
    command = ['C:/Program Files/QGIS 3.44.14/bin/python-qgis-ltr.bat', str(shim), str(script)]
    result = subprocess.run(command, env=env, cwd=scratch, capture_output=True, timeout=45)
    data = result.stdout + result.stderr
    assert not any(marker in data for marker in (b'SYNTHETIC-CONNECTION-ACCESS', b'ABCD-EFGH',
                   b'SYNTHETIC-CONNECTION-DEVICE', b'SYNTHETIC-UNRETAINED-REFRESH')), 'synthetic marker in diagnostics'
    (out / 'stdout.log').write_bytes(result.stdout)
    (out / 'stderr.log').write_bytes(result.stderr)
    receipt = dict(created=datetime.now().astimezone().isoformat(), exit_code=result.returncode,
                   command=command, plugin=str(plugin), scratch=str(scratch))
    if (scratch / 'assertions.json').is_file():
        raw = (scratch / 'assertions.json').read_bytes()
        (out / 'assertions.json').write_bytes(raw)
        receipt['assertions'] = json.loads(raw)
    receipt['inputs'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (Path(__file__), script, plugin / 'github_connection.py',
                                   plugin / 'github_session.py', plugin / 'github_transport.py') if p.is_file()}
    (out / 'process.json').write_text(json.dumps(receipt, indent=2))
    print(out / 'process.json')
    print('exit', result.returncode)
    if result.returncode:
        print(data.decode(errors='replace'))
    assert result.returncode == 0 and 'assertions' in receipt, 'native connection assertions failed'
    assert not result.stderr, 'unexpected native stderr'


if __name__ == '__main__':
    main()
