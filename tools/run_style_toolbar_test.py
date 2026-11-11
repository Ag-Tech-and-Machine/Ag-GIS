# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
    """Launch one real isolated native desktop; no normal app inputs."""
import os,sys,json,hashlib,shutil,subprocess,tempfile
from pathlib import Path
import psutil
import argparse
R=Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    a=argparse.ArgumentParser();a.add_argument('--plugin-root',type=Path,default=R/'plugins/ag_tech_tooling');a.add_argument('--evidence',type=Path,required=True);a.add_argument('--name',required=True);args=a.parse_args()
    name=args.name;source=args.plugin_root.resolve();out=args.evidence.resolve()/name;out.mkdir(parents=True,exist_ok=False)
    H=Path(tempfile.mkdtemp(prefix='aggis-overflow-'+name+'-',dir='C:/Users/Michael/AppData/Local/hermes/cache/scratch'))
    shutil.copytree(source,H/'payload/ag_tech_tooling',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copy2(R/'tools/style_toolbar_test.py',out/'executed-native_test.py')
    profile=H/'config/profiles/style';(profile/'QGIS').mkdir(parents=True)
    (profile/'QGIS/QGIS3.ini').write_text('[Qgis]\ncheckVersion=false\nprojOpenAtLaunch=0\n[core]\nfonts\\downloadMissingFonts=false\n[PythonPlugins]\nag_tech_tooling=false\n')
    for p in ['auth','runtime']:(H/p).mkdir()
    env=os.environ.copy()
    for line in Path('C:/Program Files/QGIS 3.44.14/bin/qgis-ltr-bin.env').read_text().splitlines():
     if '=' in line:k,v=line.split('=',1);env[k]=v
    for k in ['PYQGIS_STARTUP','QT_QPA_PLATFORM','QGIS_AUTH_DB_URI','QGIS_AUTH_PASSWORD_FILE','QGIS_CUSTOM_CONFIG_PATH']:env.pop(k,None)
    env.update(STYLE_TEST_HOME=str(H),STYLE_TEST_OUTPUT=str(out),QGIS_CUSTOM_CONFIG_PATH=str(H/'config'),QGIS_AUTH_DB_DIR_PATH=str(H/'auth'),TEMP=str(H/'runtime'),TMP=str(H/'runtime'),TMPDIR=str(H/'runtime'),PYTHONDONTWRITEBYTECODE='1')
    cmd=['C:/Program Files/QGIS 3.44.14/bin/qgis-ltr-bin.exe','--nologo','--noversioncheck','--noplugins','--profiles-path',str(H/'config'),'--profile','style','--code',str(out/'executed-native_test.py')]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    r={'scratch':str(H),'command':cmd,'harness_sha256':sha(out/'executed-native_test.py'),'payload':{p.relative_to(H/'payload').as_posix():sha(p) for p in (H/'payload').rglob('*') if p.is_file()},'preserved_pids':[17900,26804,23516]}
    with (out/'stdout').open('w') as stdout,(out/'stderr').open('w') as stderr:
     proc=subprocess.Popen(cmd,env=env,stdout=stdout,stderr=stderr);r['pid']=proc.pid;(out/'launch.json').write_text(json.dumps(r,indent=2))
     try:r['native_exit']=proc.wait(timeout=100)
     except subprocess.TimeoutExpired:r['native_exit']=None;r['live_handle']=proc.pid
    r['preserved_present']={str(p):psutil.pid_exists(p) for p in r['preserved_pids']}
    result=json.loads((out/'result.json').read_text()) if (out/'result.json').exists() else {}
    r['runner_exit']=0 if r['native_exit']==0 and result.get('passed') is True and result.get('exceptions')==[] else 1
    (out/'process.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='payload'},indent=2));print(json.dumps(result,indent=2));sys.exit(r['runner_exit'])
except ImportError:
    pass  # QGIS not available, skip this test