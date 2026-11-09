"""Build a local catalogue candidate; never upload, publish, install or network.

Existing --output entries are preserved. A new output is a separate candidate,
not an implicit replacement for updates/catalog.json: copy the reviewed existing
catalogue to --output first to merge with its history. Duplicate versions fail.
Offline structural verification cannot establish the origin of the input ZIP.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('update_catalog', ROOT / 'plugins/ag_tech_tooling/update_catalog.py')
assert SPEC is not None and SPEC.loader is not None
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--channel', choices=('stable', 'preview'), required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--notes', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--data-upgrade', action='store_true',
                        help='Warn that this release requires a separately reviewed data upgrade')
    args = parser.parse_args()
    try:
        if args.output.resolve() in (args.package.resolve(), args.notes.resolve()):
            raise ValueError('Output must not overwrite package or notes')
        if args.package.stat().st_size > API.MAX_PACKAGE_BYTES:
            raise ValueError('Package too large')
        # Bounded initial metadata read chooses a compatible verification version.
        # Full archive safety/CRC validation still runs before creating any output.
        with zipfile.ZipFile(args.package) as archive:
            with archive.open('ag_tech_tooling/metadata.txt') as source:
                minimum = API._metadata(source.read(65537))['qgis_minimum']
        metadata = API.verify_package(args.package, None, minimum)
        with args.notes.open('r', encoding='utf-8') as source:
            notes = source.read(20001)
        digest = hashlib.sha256()
        with args.package.open('rb') as source:
            for block in iter(lambda: source.read(1048576), b''):
                digest.update(block)
        release = dict(version=metadata['version'], channel=args.channel,
                       qgis_minimum=metadata['qgis_minimum'], qgis_maximum=metadata['qgis_maximum'],
                       url=args.url, sha256=digest.hexdigest(), size=args.package.stat().st_size,
                       notes=notes, restart_required=True, data_upgrade=args.data_upgrade)
        API.verify_package(args.package, release, minimum)
        document: dict = dict(schema_version=1, releases=[])
        if args.output.exists():
            with args.output.open('rb') as source:
                existing = source.read(API.MAX_CATALOG_BYTES + 1)
            API.parse_catalog(existing, 'preview', metadata['version'], minimum)
            document = json.loads(existing)
        document['releases'].append(release)
        data = (json.dumps(document, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
        API.parse_catalog(data, 'preview', metadata['version'], minimum)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', prefix='.catalog-', suffix='.json', dir=args.output.parent, delete=False) as target:
                name = target.name
                target.write(data)
                target.flush()
                os.fsync(target.fileno())
            os.replace(name, args.output)
        finally:
            if name and Path(name).exists():
                Path(name).unlink()
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
        parser.exit(1, f'Catalogue not written: {exc}\n')
    print(f'Local catalogue candidate ready (not published): {args.output}')
    print(f'{release["version"]} {args.channel}: {release["size"]} bytes, SHA-256 {release["sha256"]}')
    print('Review release notes, retained entries and data-upgrade implications before publication.')


if __name__ == '__main__':
    main()
