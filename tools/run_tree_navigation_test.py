"""Run tree regression in isolated QGIS Python, retaining exact receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
BASE = Path('C:/Users/[Maintainer]/AppData/Local/hermes/cache/scratch')
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--plugin-root', type=Path, default=ROOT / 'plugins/ag_tech_tooling')
p.add_argument('--evidence', type=Path, required=True)
p.add_argument('--case', choices=['preserve', 'chain'], default='preserve')
a = p.parse_args()
out = a.evidence.resolve()
out.mkdir(parents=True, exist_ok=False)
scratch = Path(tempfile.mkdtemp(prefix='aggis-navigation-', dir=BASE))
temp = scratch / 'runtime-temp'
temp.mkdir()
shim = scratch / 'run.py'
shim.write_text('import os,sys,tempfile,runpy\nfrom pathlib import Path\np=Path(' + repr(str(temp)) + ')\n'
                'for k in ("TEMP","TMP","TMPDIR"):os.environ[k]=str(p)\n'
                'tempfile.tempdir=str(p)\ns=sys.argv[1];sys.path.insert(0,str(Path(s).parent));'
                'sys.argv=[s];runpy.run_path(s,run_name="__main__")\n')
script = ROOT / 'tools/tree_navigation_test.py'
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONFAULTHANDLER='1',
           AGGIS_NAV_SCRATCH=str(scratch), AGGIS_NAV_CASE=a.case,
           AGGIS_NAV_PLUGIN_PARENT=str(a.plugin_root.resolve().parent))
for key in ('PYQGIS_STARTUP', 'QGIS_AUTH_PASSWORD_FILE', 'QGIS_AUTH_DB_URI'):
    env.pop(key, None)
command = ['C:/Program Files/QGIS 3.44.14/bin/python-qgis-ltr.bat', str(shim), str(script)]
r = subprocess.run(command, env=env, cwd=scratch, capture_output=True, timeout=60)
(out / 'stdout.log').write_bytes(r.stdout)
(out / 'stderr.log').write_bytes(r.stderr)
receipt: dict = dict(exit_code=r.returncode, command=command, plugin=str(a.plugin_root.resolve()), scratch=str(scratch), case=a.case)
if (scratch / 'assertions.json').exists():
    raw = (scratch / 'assertions.json').read_bytes()
    (out / 'assertions.json').write_bytes(raw)
    receipt['assertions'] = json.loads(raw)
receipt['inputs'] = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(__file__), script, a.plugin_root / 'farm_browser.py', a.plugin_root / 'view_settings.py')}
(out / 'process.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt, indent=2))
assert r.returncode == 0 and receipt.get('assertions', {}).get('passed'), r.stderr.decode(errors='replace')
# Reopen the saved native project in a separate, independently isolated process.
cold = Path(tempfile.mkdtemp(prefix='aggis-navigation-cold-', dir=BASE))
cold_env = dict(env, AGGIS_NAV_SCRATCH=str(cold),
                AGGIS_NAV_REOPEN=receipt['assertions']['saved_project'])
cold_run = subprocess.run(command, env=cold_env, cwd=cold, capture_output=True, timeout=60)
(out / 'cold-stdout.log').write_bytes(cold_run.stdout)
(out / 'cold-stderr.log').write_bytes(cold_run.stderr)
cold_result = json.loads((cold / 'assertions.json').read_text()) if (cold / 'assertions.json').exists() else {}
(out / 'cold-process.json').write_text(json.dumps(dict(exit_code=cold_run.returncode,
    scratch=str(cold), assertions=cold_result, inputs=receipt['inputs']), indent=2))
assert cold_run.returncode == 0 and cold_result.get('passed') and cold_result.get('cold_process_native_reopen'), cold_result
print('Separate-process native expansion restore passed')
