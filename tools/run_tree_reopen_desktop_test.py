"""Run isolated branded tree/controller save/reopen and automatic cold-start checks."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import psutil

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--plugin-root', type=Path, default=ROOT / 'plugins/ag_tech_tooling')
parser.add_argument('--evidence', type=Path, required=True)
parser.add_argument('--scenario', choices=('all-fields', 'single-field-reload', 'independent-fields', 'reference-fields', 'checkbox-context'), default='all-fields')
args = parser.parse_args()
out = args.evidence.resolve()
out.mkdir(parents=True, exist_ok=False)
home = Path(os.environ['LOCALAPPDATA']) / 'hermes/cache/scratch'
scratch = Path(tempfile.mkdtemp(prefix='aggis-tree-reopen-', dir=home))
profile = scratch / 'config/profiles/reopen'
destination = profile / 'python/plugins/ag_tech_tooling'
source = args.plugin_root.resolve()
shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.fixed'))
manifest = {p.relative_to(destination).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in destination.rglob('*') if p.is_file()}
settings = profile / 'QGIS/QGIS3.ini'
settings.parent.mkdir(parents=True)
settings.write_text('[PythonPlugins]\nag_tech_tooling=true\n[AgTechTooling]\nsimple_view\\enabled=true\n[Qgis]\ncheckVersion=false\n')
launcher = scratch / 'launcher'
launcher.mkdir()
normal = Path(os.environ['LOCALAPPDATA']) / 'Ag-GIS/default'
for name in ('Ag-GIS.exe', 'Ag-GIS.ico'):
    shutil.copy2(normal / name, launcher / name)
    assert (normal / name).read_bytes() == (launcher / name).read_bytes()
(launcher / 'launch.txt').write_text('C:/Program Files/QGIS 3.44.14\nreopen\n')
probe = ROOT / 'tools/tree_reopen_desktop_test.py'
boot = scratch / 'startup.py'
    pass  # QGIS not available, skip this test
except ImportError:
    boot.write_text('import sys\nsys.path.insert(0,"C:/Program Files/QGIS 3.44.14/apps/qgis-ltr/python")\nfrom qgis.PyQt.QtCore import QTimer\nfrom pathlib import Path\ndef run():\n exec(compile(Path(' + repr(str(probe)) + ').read_text(),' + repr(str(probe)) + ',"exec"),{"H_PATH":' + repr(str(scratch)) + '})\ndef wait():\n from qgis import utils\n if utils.iface is None:QTimer.singleShot(50,wait);return\n utils.iface.initializationCompleted.connect(lambda:QTimer.singleShot(3000,run))\nQTimer.singleShot(0,wait)\n')
try:
# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
boot.write_text(boot.read_text().replace('{"H_PATH":', '{"REFERENCE_MODE":' + repr(args.scenario if args.scenario in ('reference-fields', 'checkbox-context') else '') + ',"INDEPENDENT":' + repr(args.scenario in ('independent-fields', 'reference-fields', 'checkbox-context')) + ',"COMBINED":' + repr(args.scenario != 'all-fields') + ',"H_PATH":'))
runtime = scratch / 'runtime-temp'
runtime.mkdir()
env = dict(os.environ, PYQGIS_STARTUP=str(boot), QGIS_CUSTOM_CONFIG_PATH=str(scratch / 'config'),
           QGIS_AUTH_DB_DIR_PATH=str(scratch / 'auth'), TEMP=str(runtime), TMP=str(runtime),
           TMPDIR=str(runtime), PYTHONDONTWRITEBYTECODE='1')
for key in ('QT_QPA_PLATFORM', 'QGIS_AUTH_DB_URI', 'QGIS_AUTH_PASSWORD_FILE'):
    env.pop(key, None)
qgis_pids = lambda: {p.pid for p in psutil.process_iter(['name']) if p.info['name'] == 'qgis-ltr-bin.exe'}
preserved = qgis_pids()
kernel = ctypes.WinDLL('kernel32')
kernel.OpenProcess.restype = ctypes.c_void_p
kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
kernel.CloseHandle.argtypes = [ctypes.c_void_p]
for phase in ('warm', 'cold'):
    if phase == 'cold':
        boot.write_text(boot.read_text().replace('{"REFERENCE_MODE":', '{"COLD":True,"REFERENCE_MODE":'))
    (scratch / 'result.json').unlink(missing_ok=True)
    process = subprocess.Popen([str(launcher / 'Ag-GIS.exe')], env=env)
    deadline = time.monotonic() + 25
    new = set()
    while not new and time.monotonic() < deadline:
        time.sleep(.25)
        new = qgis_pids() - preserved
    assert len(new) == 1, new
    pid = new.pop()
    handle = kernel.OpenProcess(0x100000 | 0x1000, False, pid)
    assert handle
    wait = kernel.WaitForSingleObject(handle, 110000)
    code = ctypes.c_uint32()
    kernel.GetExitCodeProcess(handle, ctypes.byref(code))
    kernel.CloseHandle(handle)
    result_path = scratch / 'result.json'
    result = json.loads(result_path.read_text()) if result_path.exists() else {}
    receipt = dict(phase=phase, pid=pid, exit_code=code.value, wait=wait, scratch=str(scratch),
                   source=str(source), result=result, installed_manifest=manifest,
                   preserved_pids=sorted(preserved & qgis_pids()))
    (out / (phase + '-process.json')).write_text(json.dumps(receipt, indent=2))
    for name in ('independent-fields.png','reopened.png','reloaded.png','cold-restored.png','failure.png','saved.png','cold-empty.png','result.json'):
        if (scratch / name).exists(): shutil.copy2(scratch / name, out / name)
    assert wait == 0 and code.value == 0 and result.get('passed'), receipt
    assert preserved <= qgis_pids(), 'An existing session terminated during isolated tests'
    assert result.get('same_session_reopen') if phase == 'warm' else result.get('cold_automatic_restore')
    process.wait(timeout=15)
    print(phase, 'native branded tree/filter/visibility preservation passed, exit 0')
