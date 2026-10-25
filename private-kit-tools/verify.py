"""Private static kit verification. Python stdlib only; never launches an app."""
import argparse
import binascii
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import warnings
import zipfile

REVISION = '721907819d12290048856fdc7396e804a3d82624'
PLUGIN_SHA = 'b8862304f27e6d9b0725a51e5c45fa8df0c9626771df1d142c69c85d0889bd42'
LAUNCHER_SHA = '8999056cc06004013593fc5285cddec1e81af4044ea36aee0aad2c38d34cc091'
ICON_SHA = '09ff8303c32f32f7dbf533a54e87bfb852dd1ed2c5a9c8c372360e944e4f5e9e'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs)


def safe_name(name):
    require(isinstance(name, str) and len(name) <= 220, 'invalid name')
    require(re.fullmatch(r'[A-Za-z0-9_./-]+', name) is not None, 'unsafe member characters')
    for part in name.split('/'):
        require(part not in ('', '.', '..') and not part.endswith(('.', ' ')), 'noncanonical member name')
        require(part.split('.')[0].upper() not in {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}, 'device member')
    return name


def read_archive(data):
    result = {}
    folded = set()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        require(0 < len(infos) <= 1000, 'member count limit')
        require(sum(i.file_size for i in infos) <= 64 * 1024 * 1024, 'expanded size limit')
        for info in infos:
            name = safe_name(info.orig_filename)
            require(name == info.filename and not info.is_dir(), 'directory or truncated name')
            require(name.casefold() not in folded, 'duplicate/case-ambiguous member')
            folded.add(name.casefold())
            mode = (info.external_attr >> 16) & 0o170000
            require(mode in (0, stat.S_IFREG), 'nonregular/symlink member')
            require(not info.flag_bits & 1, 'encrypted member')
            require(info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), 'unsupported compression')
            content = archive.read(info)  # zipfile checks the actual CRC.
            require(len(content) == info.file_size, 'member size mismatch')
            require(binascii.crc32(content) & 0xffffffff == info.CRC, 'CRC mismatch')
            result[name] = content
    names = set(result)
    for name in names:
        parts = name.split('/')
        require(not any('/'.join(parts[:i]) in names for i in range(1, len(parts))), 'file/directory collision')
    return result


def inventory(files):
    return {name: {'sha256': sha(data), 'size': len(data), 'crc32': binascii.crc32(data) & 0xffffffff} for name, data in sorted(files.items())}


def match_manifest(data, manifest):
    require(sha(data) == manifest['sha256'] and len(data) == manifest['size'], 'archive hash/size mismatch')
    files = read_archive(data)
    require(inventory(files) == manifest['members'], 'member manifest mismatch')
    return files


def source_mapping(name):
    require(name.startswith('ag_tech_tooling/') and name.count('/') == 1, 'unexpected plugin path')
    leaf = name.split('/')[-1]
    return {'USER_GUIDE.txt': 'docs/USER_GUIDE.md', 'START_HERE.txt': 'START_HERE.md'}.get(leaf, 'plugins/' + name)


def privacy_scan(files):
    findings = []
    patterns = {
        'user-specific-filesystem-path': r'(?i)(?:[a-z]:[/\\]+users[/\\]+(?!public\b|<)[^\s"\r\n<>]+|/Users/[^/\s]+/|(?<![A-Za-z0-9.:])/home/(?!item\.html)[^/\s]+/)',
        'operations-reference': r'(?i)\.aggis-agent|ag-gis-team|team_queue\.py|operations\.sqlite3|delivery:[0-9a-f]{20}',
        'credential-material': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}|\bAKIA[A-Z0-9]{16}',
        'unc-private-data': r'(?i)\\\\[a-z0-9][a-z0-9._-]*\\[a-z0-9][a-z0-9 _.$-]*',
    }
    for name, data in files.items():
        if not name.endswith(('.py', '.txt', '.md', '.cs', '.json', '.svg')) and not name.endswith('LICENSE'):
            continue
        text = data.decode('utf-8-sig')
        for number, line in enumerate(text.splitlines(), 1):
            for rule, pattern in patterns.items():
                if re.search(pattern, line):
                    findings.append({'member': name, 'line': number, 'rule': rule})
    return findings


def extract_and_compare(files, root):
    root.mkdir(parents=True, exist_ok=False)
    for name, data in sorted(files.items()):
        safe_name(name)
        dest = root.joinpath(*name.split('/'))
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as stream:
            stream.write(data)
    actual = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    require(actual == files, 're-extracted bytes differ')
    return inventory(actual)


def verify_kit(args):
    manifest = json_bytes(args.manifest.read_bytes())
    require(manifest['source_revision'] == REVISION, 'source revision mismatch')
    kit_bytes = args.kit.read_bytes()
    kit = match_manifest(kit_bytes, manifest['kit'])
    expected = {'Ag-GIS.exe', 'Ag-GIS.ico', 'ag_tech_tooling-0.12.2.zip', 'launch.txt', 'README.txt', 'LICENSE', 'CREDITS.txt', 'corresponding-source.zip', 'manifest.json'}
    require(set(kit) == expected, 'unexpected kit payload')
    require(sha(kit['Ag-GIS.exe']) == LAUNCHER_SHA, 'launcher pin mismatch')
    require(sha(kit['Ag-GIS.ico']) == ICON_SHA, 'icon pin mismatch')
    require(sha(kit['ag_tech_tooling-0.12.2.zip']) == PLUGIN_SHA, 'plugin pin mismatch')
    require(kit['launch.txt'] == b'C:\\Program Files\\QGIS 3.44.14\r\nAgGIS_Experimental\r\n', 'template mismatch')
    embedded = json_bytes(kit['manifest.json'])
    require(embedded['source_revision'] == REVISION, 'embedded revision mismatch')
    require(embedded['members'] == inventory({n: d for n, d in kit.items() if n != 'manifest.json'}), 'embedded manifest mismatch')
    source_bytes = args.source.read_bytes()
    require(kit['corresponding-source.zip'] == source_bytes, 'source asset/nested mismatch')
    source = match_manifest(source_bytes, manifest['source'])
    proposal = json_bytes(args.allowlist.read_bytes())
    require(proposal['commit'] == REVISION and len(proposal['files']) == 63, 'allowlist provenance mismatch')
    allow = {item['path']: item for item in proposal['files']}
    require(len(allow) == 63, 'duplicate allowlist path')
    require(set(source) == set(allow) | {'BUILDING.txt', 'SOURCE_MANIFEST.json'}, 'source allowlist mismatch')
    source_manifest = json_bytes(source['SOURCE_MANIFEST.json'])
    require(source_manifest['source_revision'] == REVISION, 'source manifest revision')
    require(source_manifest['members'] == inventory({n: d for n, d in source.items() if n != 'SOURCE_MANIFEST.json'}), 'source manifest mismatch')
    for name, item in allow.items():
        require(sha(source[name]) == item['sha256'] and len(source[name]) == item['size'], 'allowlisted source hash mismatch: ' + name)
        require(source[name] == (args.frozen_root / name).read_bytes(), 'live source mismatch: ' + name)
    plugin = match_manifest(kit['ag_tech_tooling-0.12.2.zip'], manifest['plugin'])
    require(len(plugin) == 57, 'plugin count mismatch')
    for name, data in plugin.items():
        mapped = source_mapping(name)
        require(mapped in allow and data == source[mapped] == (args.frozen_root / mapped).read_bytes(), 'plugin source mismatch: ' + name)
    freeze = json_bytes(args.freeze.read_bytes())
    require(freeze['base_revision'] == REVISION and len(freeze['files']) == 210, 'freeze provenance')
    for name, expected_hash in freeze['files'].items():
        require(sha((args.frozen_root / name).read_bytes()) == expected_hash, 'frozen baseline changed: ' + name)
    findings = privacy_scan({**{'kit/' + n: d for n, d in kit.items()}, **{'source/' + n: d for n, d in source.items()}, **{'plugin/' + n: d for n, d in plugin.items()}})
    require(not findings, 'new privacy finding: ' + json.dumps(findings))
    # All archive validation precedes any extraction. Each root is new and private.
    args.extract_root.mkdir(parents=True, exist_ok=False)
    extracted = {label: extract_and_compare(files, args.extract_root / label) for label, files in [('kit', kit), ('source', source), ('plugin', plugin)]}
    report = {'verified': True, 'source_revision': REVISION, 'kit_sha256': sha(kit_bytes), 'source_sha256': sha(source_bytes), 'plugin_sha256': PLUGIN_SHA, 'member_counts': {k: len(v) for k, v in extracted.items()}, 'frozen_source_count': 210, 'all_members_crc_hash_and_reextraction_match': True, 'privacy_scan_new_findings': findings, 'publication_clean_claim': False, 'runtime_executed': False, 'extracted_manifests': extracted}
    with (args.extract_root / 'verification.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != 'extracted_manifests'}, indent=2))


def self_test(root):
    root.mkdir(parents=True, exist_ok=False)
    helper_hash = sha(Path(__file__).read_bytes())
    def fixture(entries):
        buffer = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_STORED) as z:
                for name, data in entries:
                    # ZipInfo on Windows normalizes backslashes at construction;
                    # preserve the deliberately malformed on-disk fixture name.
                    if isinstance(name, str):
                        info = zipfile.ZipInfo('placeholder')
                        info.filename = name
                        info.orig_filename = name
                    else:
                        info = name
                    z.writestr(info, data)
        return buffer.getvalue()
    good = fixture([('safe/file.txt', b'known-content')])
    cases = {'valid': (good, 0)}
    for label, name in [('traversal', '../escape'), ('nested-traversal', 'a/../escape'), ('absolute', '/escape'), ('drive', 'C:/escape'), ('backslash', 'a\\escape'), ('empty-part', 'a//escape'), ('dot-part', './escape'), ('trailing-dot', 'a./escape'), ('device', 'NUL.txt'), ('directory', 'a/'), ('percent', '%2e%2e/escape')]:
        cases[label] = (fixture([(name, b'x')]), 1)
    cases['duplicate'] = (fixture([('a', b'1'), ('a', b'2')]), 1)
    cases['case-duplicate'] = (fixture([('a', b'1'), ('A', b'2')]), 1)
    cases['file-dir-collision'] = (fixture([('a', b'1'), ('a/b', b'2')]), 1)
    link = zipfile.ZipInfo('link')
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    cases['symlink'] = (fixture([(link, b'target')]), 1)
    broken = bytearray(good)
    start = 30 + struct.unpack_from('<H', broken, 26)[0] + struct.unpack_from('<H', broken, 28)[0]
    broken[start] ^= 1
    cases['bad-crc'] = (bytes(broken), 1)
    cases['truncated'] = (good[:-10], 1)
    results = []
    for name, (data, expected) in cases.items():
        path = root / (name + '.zip')
        path.write_bytes(data)
        command = [sys.executable, '-B', str(Path(__file__).resolve()), '--probe', str(path)]
        result = subprocess.run(command, capture_output=True, text=True)
        results.append({'case': name, 'command': subprocess.list2cmdline(command), 'exit_code': result.returncode, 'expected_exit_code': expected, 'stdout': result.stdout, 'stderr': result.stderr, 'fixture_sha256': sha(data)})
        require(result.returncode == expected, 'negative control failed: ' + name)
    files = read_archive(good)
    require(extract_and_compare(files, root / 'positive-extraction') == inventory(files), 'positive extraction')
    try:
        extract_and_compare(files, root / 'positive-extraction')
    except FileExistsError:
        pass
    else:
        raise ValueError('existing extraction root accepted')
    expected = {'sha256': sha(good), 'size': len(good), 'members': inventory(files)}
    require(match_manifest(good, expected) == files, 'valid manifest')
    for label, altered in [('hash', dict(expected, sha256='0' * 64)), ('member', dict(expected, members={}))]:
        try:
            match_manifest(good, altered)
        except ValueError:
            results.append({'case': 'manifest-' + label, 'expected_rejection_observed': True})
        else:
            raise ValueError('manifest mutation accepted')
    require(privacy_scan({'guide.txt': b'C:\\Users\\PrivatePerson\\Documents\\farm'}) != [], 'private-path detector')
    require(privacy_scan({'guide.txt': b'\\\\private-server\\farm-share'}) != [], 'UNC private-data detector')
    require(privacy_scan({'code.py': "re.search(r'[<>:\"/\\\\|?*\\x00-\\x1f]', name)".encode()}) == [], 'filename-validation regex is not a UNC path')
    require(privacy_scan({'code.py': b'https://www.arcgis.com/home/item.html?id=demo\nauthor=Michael\nCodex Claude Hermes'}) == [], 'context false-positive')
    require(sha(Path(__file__).read_bytes()) == helper_hash, 'helper changed during tests')
    report = {'passed': True, 'helper_sha256': helper_hash, 'subprocess_cases': len(cases), 'checks': results, 'additional_assertions': ['safe extraction bytes', 'existing extraction root refused', 'archive hash mutation refused', 'member manifest mutation refused', 'private path detected', 'contextual wording preserved']}
    (root / 'self-test.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', type=Path)
    parser.add_argument('--probe', type=Path)
    for name in ('kit', 'source', 'manifest', 'extract-root', 'frozen-root', 'freeze', 'allowlist'):
        parser.add_argument('--' + name, type=Path)
    args = parser.parse_args()
    if args.probe:
        files = read_archive(args.probe.read_bytes())
        print(json.dumps({'safe_members': len(files)}))
    elif args.self_test:
        self_test(args.self_test)
    else:
        require(all(getattr(args, n.replace('-', '_')) for n in ('kit', 'source', 'manifest', 'extract-root', 'frozen-root', 'freeze', 'allowlist')), 'missing required verification argument')
        verify_kit(args)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, RuntimeError) as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(1)
