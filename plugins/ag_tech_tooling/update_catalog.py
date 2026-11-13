# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline-safe update validation. Standard library only; never installs or networks.

An offline ZIP is structurally checked, NOT authenticated. A catalogue hash checks
integrity against the trusted catalogue, not a publisher's digital signature.
"""
import configparser
import os
from pathlib import Path
import re
import json
import hashlib
import zipfile
import zlib
import stat
import tempfile
import shutil

FEED_URL = 'https://raw.githubusercontent.com/Ag-Tech-and-Machine/Ag-GIS/main/updates/catalog.json'
MAX_CATALOG_BYTES = 1048576
MAX_PACKAGE_BYTES = 67108864


def version_key(value: str) -> tuple:
    """Compare dotted numeric versions, ignoring trailing zero components."""
    if not isinstance(value, str) or len(value) > 64 or not re.fullmatch(r'(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*)){1,7}', value):
        raise ValueError('Invalid dotted numeric version')
    parts = list(map(int, value.split('.')))
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def _metadata(data) -> dict:
    if len(data) > 65536:
        raise ValueError('Metadata too large')
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(data.decode('utf-8-sig'))
        if parser.defaults():
            raise ValueError('Metadata defaults are not accepted')
        section = parser['general']
        if section.get('plugin_dependencies', '').strip():
            raise ValueError('Plugin dependencies are not permitted in update packages')
        version = section['version'].strip()
        minimum = section['qgisMinimumVersion'].strip()
        maximum = section.get('qgisMaximumVersion', '').strip()
        experimental = section['experimental'].strip().lower()
        version_key(version)
        version_key(minimum)
        if maximum and version_key(maximum) < version_key(minimum):
            raise ValueError('Invalid QGIS version range')
        if experimental not in ('true', 'false'):
            raise ValueError('Invalid experimental metadata')
        return dict(version=version, experimental=experimental == 'true', qgis_minimum=minimum, qgis_maximum=maximum)
    except (configparser.Error, KeyError, UnicodeError) as exc:
        raise ValueError('Invalid plugin metadata') from exc


def read_installed(plugin_dir: Path) -> dict:
    """Read actual metadata; never infer a farm schema from the plugin version."""
    with (Path(plugin_dir) / 'metadata.txt').open('rb') as source:
        return _metadata(source.read(65537))


def _compatible(release, qgis_version):
    current = version_key(qgis_version)
    return (version_key(release['qgis_minimum']) <= current
            and (not release['qgis_maximum'] or current <= version_key(release['qgis_maximum'])))


def _validate_release(item):
    fields = {'version', 'channel', 'qgis_minimum', 'qgis_maximum', 'url', 'sha256', 'size', 'notes', 'restart_required', 'data_upgrade'}
    if not isinstance(item, dict) or set(item) != fields:
        raise ValueError('Invalid release fields')
    version_key(item['version'])
    version_key(item['qgis_minimum'])
    maximum = item['qgis_maximum']
    if not isinstance(maximum, str) or (maximum and version_key(maximum) < version_key(item['qgis_minimum'])):
        raise ValueError('Invalid QGIS range')
    if item['channel'] not in ('stable', 'preview'):
        raise ValueError('Invalid release channel')
    url = item['url']
    if not isinstance(url, str) or len(url) > 2048 or not re.fullmatch(
            r'https://github\.com/Ag-Tech-and-Machine/Ag-GIS/releases/download/[A-Za-z0-9][A-Za-z0-9_.-]{0,127}/ag_tech_tooling-[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.zip', url):
        raise ValueError('Only official GitHub plugin ZIP downloads are accepted')
    if not isinstance(item['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
        raise ValueError('Invalid SHA-256')
    if type(item['size']) is not int or not 0 < item['size'] <= MAX_PACKAGE_BYTES:
        raise ValueError('Invalid package size')
    notes = item['notes']
    if not isinstance(notes, str) or len(notes) > 20000 or '<' in notes or '>' in notes or any(ord(c) < 32 and c not in '\n\r\t' for c in notes):
        raise ValueError('Release notes must be bounded plain text')
    if type(item['restart_required']) is not bool or type(item['data_upgrade']) is not bool:
        raise ValueError('Invalid release flags')
    return item


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def parse_catalog(data: bytes, channel: str, installed_version: str, qgis_version: str) -> dict:
    """Select the highest compatible newer release; never silently change channel."""
    installed = version_key(installed_version)
    version_key(qgis_version)
    if channel not in ('stable', 'preview') or not isinstance(data, bytes) or len(data) > MAX_CATALOG_BYTES:
        raise ValueError('Invalid channel or catalogue size')
    try:
        document = json.loads(data.decode('utf-8'), object_pairs_hook=_unique_object)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('Invalid catalogue encoding or nesting') from exc
    if (not isinstance(document, dict) or set(document) != {'schema_version', 'releases'}
            or type(document['schema_version']) is not int or document['schema_version'] != 1
            or not isinstance(document['releases'], list) or len(document['releases']) > 256):
        raise ValueError('Invalid catalogue schema')
    seen = set()
    for item in document['releases']:
        _validate_release(item)
        identity = version_key(item['version'])
        if identity in seen:
            raise ValueError('Duplicate or mixed-channel release version')
        seen.add(identity)
    selected = [item for item in document['releases'] if channel == 'preview' or item['channel'] == 'stable']
    if not selected:
        return dict(status='empty', release=None)
    newer = [item for item in selected if version_key(item['version']) > installed]
    compatible = [item for item in newer if _compatible(item, qgis_version)]
    if compatible:
        return dict(status='available', release=max(compatible, key=lambda item: version_key(item['version'])))
    return dict(status='incompatible' if newer else 'current', release=None)


def _safe_parts(name):
    if not isinstance(name, str) or not name or len(name) > 240 or '\\' in name or '\x00' in name:
        raise ValueError('Unsafe plugin path')
    parts = name.rstrip('/').split('/')
    for part in parts:
        if (not re.fullmatch(r'[A-Za-z0-9_. -]+', part) or part in ('.', '..')
                or part.endswith(('.', ' ')) or part.startswith(' ')
                or part.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(10)), *(f'LPT{i}' for i in range(10))}):
            raise ValueError('Unsafe plugin path component')
    return parts


def _source_file(name):
    return Path(name).suffix.lower() in {'.py', '.txt', '.svg', '.ico', '.png', '.json', '.html', '.css', '.md'} or name == 'LICENSE'


def _check_archive(archive):
    entries = archive.infolist()
    if not entries or len(entries) > 4096:
        raise ValueError('Invalid ZIP entry count')
    seen = {}
    total = 0
    for entry in entries:
        if entry.orig_filename != entry.filename:
            raise ValueError('Invalid ZIP filename')
        parts = _safe_parts(entry.filename)
        if parts[0] != 'ag_tech_tooling' or (len(parts) == 1 and not entry.is_dir()):
            raise ValueError('Unexpected plugin root')
        # Current build format is flat. Refuse nested metadata/native installer
        # target ambiguity, implicit directory collisions and unreviewed layouts.
        if len(parts) > 2 or (len(parts) == 2 and entry.is_dir()):
            raise ValueError('Only the flat Ag-GIS runtime package layout is supported')
        mode = entry.external_attr >> 16
        kind = stat.S_IFMT(mode)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or (kind == stat.S_IFDIR and not entry.is_dir()):
            raise ValueError('ZIP links or special files are not supported')
        if entry.flag_bits & 1 or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise ValueError('Encrypted or unsupported ZIP member')
        canonical = '/'.join(parts).casefold()
        if canonical in seen:
            raise ValueError('Duplicate or case-colliding ZIP member')
        seen[canonical] = entry.is_dir()
        if not entry.is_dir() and not _source_file(parts[-1]):
            raise ValueError('Unexpected non-source file in plugin ZIP')
        total += entry.file_size
        if (entry.file_size > 16777216 or total > MAX_PACKAGE_BYTES
                or entry.file_size > max(1, entry.compress_size) * 200):
            raise ValueError('ZIP expansion limits exceeded')
    for name in seen:
        parts = name.split('/')
        if any(seen.get('/'.join(parts[:index])) is False for index in range(1, len(parts))):
            raise ValueError('ZIP file/directory collision')
    if not all(seen.get('ag_tech_tooling/' + name) is False for name in ('metadata.txt', '__init__.py', 'plugin.py')):
        raise ValueError('Missing required plugin files')
    if archive.getinfo('ag_tech_tooling/metadata.txt').file_size > 65536:
        raise ValueError('Metadata too large')
    # Stream every file to verify CRC and local-header consistency before QGIS sees it.
    for entry in entries:
        count = 0
        with archive.open(entry) as source:
            while True:
                block = source.read(1048576)
                if not block:
                    break
                count += len(block)
                if count > entry.file_size:
                    raise ValueError('ZIP member size mismatch')
        if count != entry.file_size:
            raise ValueError('Truncated ZIP member')


def verify_package(path: Path, release, qgis_version: str) -> dict:
    """Validate without extraction. Offline (release=None) does NOT authenticate."""
    version_key(qgis_version)
    path = Path(path)
    if release is not None:
        _validate_release(release)
    with path.open('rb') as source:
        digest = hashlib.sha256()
        size = 0
        while True:
            block = source.read(1048576)
            if not block:
                break
            size += len(block)
            if size > MAX_PACKAGE_BYTES:
                raise ValueError('Package too large')
            digest.update(block)
        if not size or (release is not None and (size != release['size'] or digest.hexdigest() != release['sha256'])):
            raise ValueError('Package integrity check failed')
        source.seek(0)
        if source.read(4) != b'PK\x03\x04':
            raise ValueError('Only ordinary ZIP packages are accepted, not executables')
        source.seek(0)
        try:
            with zipfile.ZipFile(source) as archive:
                _check_archive(archive)
                metadata = _metadata(archive.read('ag_tech_tooling/metadata.txt'))
        except (zipfile.BadZipFile, KeyError, RuntimeError, NotImplementedError, EOFError, zlib.error) as exc:
            raise ValueError('Invalid plugin ZIP') from exc
    if not _compatible(metadata, qgis_version):
        raise ValueError('Package is incompatible with this QGIS version')
    if release is not None:
        if any(metadata[key] != release[key] for key in ('version', 'qgis_minimum', 'qgis_maximum')):
            raise ValueError('Package metadata does not match catalogue')
        if metadata['experimental'] != (release['channel'] == 'preview'):
            raise ValueError('Package experimental flag does not match release channel')
    return metadata


def _linked(path):
    info = path.lstat()
    # Check for explicit symlinks first
    if stat.S_ISLNK(info.st_mode):
        return True
    # Also check using is_symlink() which handles Windows symlinks correctly
    try:
        is_link = path.is_symlink()
        # DEBUG: print for testing
        import sys
        sys.stderr.write(f"_DEBUG: path={path.name}, is_symlink={is_link}\n")
        if is_link:
            return True
    except (OSError, AttributeError):
        pass
    # Don't flag reparse points as links - is_symlink() is sufficient
    return False


def _hash_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        while True:
            block = source.read(1048576)
            if not block:
                return digest.hexdigest()
            digest.update(block)


def snapshot_plugin(plugin_dir: Path, recovery_root: Path) -> Path:
    """Verified source-only local recovery directory, NOT a farm-data backup.

    Call with a quiescent plugin directory. Only the current flat runtime format
    is copied; subdirectories, unknown/data files and caches are excluded. Root
    links/junctions fail closed. Nothing is installed or restored.
    """
    plugin_dir = Path(plugin_dir)
    recovery_root = Path(recovery_root)
    if _linked(plugin_dir) or not plugin_dir.is_dir():
        raise ValueError('Plugin source must be a real directory')
    source_root = plugin_dir.resolve()
    target_root = recovery_root.resolve()
    if target_root == source_root or source_root in target_root.parents:
        raise ValueError('Recovery must be outside the plugin directory')
    for ancestor in (recovery_root, *recovery_root.parents):
        if ancestor.exists() and _linked(ancestor):
            raise ValueError('Recovery path must not contain links')
    metadata = read_installed(source_root)
    sources = []
    total = 0
    for path in source_root.iterdir():
        if _linked(path):
            raise ValueError('Plugin source contains a link or junction')
        if path.is_dir() or not _source_file(path.name):
            continue
        relative = path.relative_to(source_root)
        _safe_parts(relative.as_posix())
        if not path.is_file():
            raise ValueError('Plugin source contains a special file')
        total += path.stat().st_size
        if total > MAX_PACKAGE_BYTES or len(sources) >= 4096:
            raise ValueError('Plugin recovery size limit exceeded')
        sources.append((path, relative, _hash_file(path)))
    if not {'metadata.txt', '__init__.py', 'plugin.py'}.issubset({relative.as_posix() for _, relative, _ in sources}):
        raise ValueError('Incomplete plugin source')
    recovery_root.mkdir(parents=True, exist_ok=True)
    snapshot = Path(tempfile.mkdtemp(prefix='ag_tech_tooling-' + metadata['version'] + '-', dir=recovery_root))
    try:
        for source, relative, digest in sources:
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if _linked(source):
                raise ValueError('Plugin source changed to a link')
            shutil.copyfile(source, target)
            if _hash_file(target) != digest or _hash_file(source) != digest:
                raise ValueError('Recovery snapshot verification failed')
    except BaseException:
        shutil.rmtree(snapshot)
        raise
    return snapshot
