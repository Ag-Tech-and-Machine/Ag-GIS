"""Run synthetic native loopback checks with fresh isolated QGIS settings.

Developer experiment only. No product wiring, normal profile, OAuth endpoint,
credential store, global log suppression or certificate/trust-store installation.
OpenSSL is used solely to make a short-lived untrusted localhost test certificate.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('C:/temp/AppData/Local/tool/cache/scratch')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qgis-root', type=Path, default=Path('C:/Program Files/QGIS 3.44.14'))
    args = parser.parse_args()
    bootstrap = args.qgis_root / 'bin/python-qgis-ltr.bat'
    openssl = shutil.which('openssl')
    if os.name != 'nt' or not bootstrap.is_file() or not BASE.is_dir() or not openssl:
        raise SystemExit('Requires existing Windows QGIS, OpenSSL and your agent scratch; nothing installed.')
    out = ROOT / '.aggis-agent/evidence' / ('auth-network-' + uuid.uuid4().hex)
    out.mkdir(parents=True, exist_ok=False)
    script = ROOT / 'tools/auth_network_feasibility_test.py'
    runtime = ROOT / 'plugins/ag_tech_tooling'
    baseline = {p.relative_to(runtime).as_posix(): sha(p.read_bytes())
                for p in runtime.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    report = {'created': datetime.now().astimezone().isoformat(), 'script_sha256': sha(script.read_bytes()),
              'runner_sha256': sha(Path(__file__).read_bytes()), 'runtime_before': baseline, 'receipts': []}
    try:
        for number in (1, 2):
            scratch = Path(tempfile.mkdtemp(prefix='aggis-auth-network-', dir=BASE))
            (scratch / 'SYNTHETIC-ONLY').write_text('native-loopback-v1')
            temp = scratch / 'runtime-temp'
            temp.mkdir()
            cert_command = [openssl, 'req', '-x509', '-newkey', 'rsa:2048', '-noenc',
                            '-keyout', str(scratch / 'key.pem'), '-out', str(scratch / 'cert.pem'),
                            '-days', '1', '-subj', '/CN=localhost',
                            '-addext', 'subjectAltName=IP:127.0.0.1']
            cert = subprocess.run(cert_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  cwd=scratch, timeout=30)
            assert cert.returncode == 0, 'Test certificate generation failed'
            shim = scratch / 'run_qgis.py'
            shim.write_text(
                'import os,sys,tempfile,runpy\nfrom pathlib import Path\np=Path(' + repr(str(temp)) + ')\n'
                'for k in ("TEMP","TMP","TMPDIR"):os.environ[k]=str(p)\n'
                'tempfile.tempdir=str(p)\ns=sys.argv[1];sys.path.insert(0,str(Path(s).parent));'
                'sys.argv=[s];runpy.run_path(s,run_name="__main__")\n', encoding='utf-8')
            marker = 'AGGIS-SYNTHETIC-NETWORK-' + secrets.token_hex(24)
            env = dict(os.environ, AGGIS_SYNTHETIC_NETWORK_ROOT=str(scratch),
                       AGGIS_SYNTHETIC_NETWORK_MARKER=marker)
            for key in ('QGIS_AUTH_PASSWORD_FILE', 'QGIS_AUTH_DB_URI', 'QGIS_CUSTOM_CONFIG_PATH'):
                env.pop(key, None)
            command = [str(bootstrap), str(shim), str(script)]
            process = subprocess.run(command, env=env, cwd=scratch, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, timeout=45)
            leaked = marker.encode() in process.stdout
            receipt = {'run': number, 'scratch': str(scratch), 'command': command,
                       'exit_code': process.returncode, 'stdout_marker_absent': not leaked}
            if not leaked:
                log = out / (str(number) + '.log')
                log.write_bytes(process.stdout)
                receipt.update(log=str(log), log_sha256=sha(process.stdout))
            assertion = scratch / 'assertions.json'
            if assertion.is_file():
                raw = assertion.read_bytes()
                assert marker.encode() not in raw, 'Marker in structured report; not copied'
                saved = out / (str(number) + '-assertions.json')
                saved.write_bytes(raw)
                receipt.update(assertions=str(saved), assertions_sha256=sha(raw))
            report['receipts'].append(receipt)
            print('Native synthetic run', number, 'exit', process.returncode, 'marker absent', not leaked, flush=True)
            assert not leaked, 'Synthetic marker reached native stdout/stderr; output deliberately not persisted'
            assert process.returncode == 0 and assertion.is_file(), 'Native assertions failed; retain receipt'
    finally:
        current = {p.relative_to(runtime).as_posix(): sha(p.read_bytes())
                   for p in runtime.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        report['runtime_unchanged'] = current == baseline
        (out / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('Evidence:', out / 'results.json', flush=True)
    assert report['runtime_unchanged'], 'Runtime changed during test; reconcile before reporting'
    print('Two fresh native processes passed. Observer visibility is NOT leak-free authentication.')


if __name__ == '__main__':
    main()
