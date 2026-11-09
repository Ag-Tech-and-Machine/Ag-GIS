"""Bounded, read-only GS3 ZIP metadata adapter; no member extraction."""
import hashlib
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from .deere_preview import SETUP_NS, CATALOG_NS, XML_LIMIT, _xml_data

LIMIT_ENTRIES = 10000
LIMIT_BYTES = 512 * 1024 * 1024


def inspect_zip(source, probe_native=False, cancelled=None):
    source = Path(source).resolve(strict=True)
    def check():
        if cancelled and cancelled():
            raise RuntimeError('Inspection cancelled')
    def sha():
        digest = hashlib.sha256()
        with source.open('rb') as stream:
            while True:
                check()
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        return digest.hexdigest()
    original = (source.stat().st_size, source.stat().st_mtime_ns, sha())
    report = dict(format='unrecognised', files=[], profiles=[], entities=[], spatial_items=[],
                  issues=[], native_probe='not_applicable_zip' if probe_native else 'not_run',
                  source_unchanged=False, geometry_import_supported=False, archive_sha256=original[2])
    entities = {}
    with ZipFile(source) as archive:
        from .archive_sources import validated_members
        members = validated_members(archive, check, max_entries=LIMIT_ENTRIES,
                                    max_bytes=LIMIT_BYTES)
        def issue(message, name):
            report['issues'].append(dict(path=name, message=message))
        for name, info in sorted(members.items()):
            check()
            report['files'].append(dict(path=name, bytes=info.file_size, crc32=info.CRC))
            parts = PurePosixPath(name).parts
            if PurePosixPath(name).suffix.lower() not in ('.fds', '.spatialcatalog'):
                continue
            index = next((j for j in range(1, len(parts) - 1)
                          if parts[j].lower() == 'eic' and parts[j-1].lower() == 'rcd'), None)
            if index is None:
                continue
            try:
                if info.file_size > XML_LIMIT:
                    raise ValueError('XML metadata exceeds the 10 MiB preview limit')
                with archive.open(info) as stream:
                    data = stream.read(XML_LIMIT + 1)
                tree = _xml_data(data)
            except (ValueError, ET.ParseError, OSError, RuntimeError) as error:
                issue(f'Cannot read metadata: {error}', name)
                continue
            if tree.tag not in (f'{{{SETUP_NS}}}SetupFile', f'{{{CATALOG_NS}}}SpatialCatalog'):
                issue('Unrecognised metadata namespace or root', name)
                continue
            report['format'] = 'deere_gs3_rcd'
            profile = '/'.join(parts[:index-1]) or '.'
            if profile not in report['profiles']:
                report['profiles'].append(profile)
            for node in tree.iter():
                kind = node.tag.rsplit('}', 1)[-1].lower()
                if node.tag not in {f'{{{SETUP_NS}}}{k}' for k in ('Client', 'Farm', 'Field')}:
                    continue
                identifier = node.get('erid', '')
                if not identifier:
                    issue(f'{kind} has no machine identifier', name)
                    continue
                parent = node.get('clientRef' if kind == 'farm' else 'farmRef', '') if kind != 'client' else ''
                record = dict(profile=profile, kind=kind, id=identifier, name=node.get('name', ''),
                              parent_id=parent, attributes=dict(node.attrib))
                key = (profile, kind, identifier.casefold())
                if key in entities and entities[key] != record:
                    issue(f'Conflicting {kind} metadata for the same machine identifier', name)
                else:
                    entities[key] = record
            for group in tree.iter():
                if group.tag.rsplit('}', 1)[-1] != 'SpatialItems':
                    continue
                for item in group:
                    filename = item.get('fileName', '')
                    resource = None
                    if not filename or '/' in filename or '\\' in filename or ':' in filename or filename in ('.', '..'):
                        issue('Unsafe or missing spatial resource filename', name)
                    else:
                        candidate = str(PurePosixPath(name).parent / (filename if filename.lower().endswith('.fdshape') else filename + '.fdShape'))
                        if candidate in members:
                            resource = candidate
                        else:
                            issue('Referenced spatial resource is missing', name)
                    report['spatial_items'].append(dict(profile=profile, kind=item.tag.rsplit('}', 1)[-1],
                        id=item.get('erid', ''), name=item.get('name', ''), field_id=group.get('eridFieldRef', ''),
                        resource=resource, catalog=name, attributes=dict(item.attrib),
                        properties=[dict(tag=c.tag, attributes=dict(c.attrib), text=c.text) for c in item],
                        native_layers=[], geometry_status='not_decoded'))
    report['entities'] = list(entities.values())
    for entity in report['entities']:
        parent_kind = {'farm': 'client', 'field': 'farm'}.get(entity['kind'])
        if parent_kind and (entity['profile'], parent_kind, entity['parent_id'].casefold()) not in entities:
            report['issues'].append(dict(message=f"{entity['kind']} has an unresolved parent", id=entity['id']))
    for item in report['spatial_items']:
        if (item['profile'], 'field', item['field_id'].casefold()) not in entities:
            report['issues'].append(dict(message='Spatial item has an unresolved field', id=item['id']))
    check()
    if (source.stat().st_size, source.stat().st_mtime_ns, sha()) != original:
        raise RuntimeError('Source changed during preview; discard this result and retry')
    report['source_unchanged'] = True
    return report
