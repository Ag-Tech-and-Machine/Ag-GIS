#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build/update release catalog from verified package.
Standard library only; never installs or networks.
"""
import argparse
import json
import sys
from pathlib import Path

# Import from the plugin's update_catalog module
PLUGIN_ROOT = Path(__file__).resolve().parents[1] / 'plugins' / 'ag_tech_tooling'
sys.path.insert(0, str(PLUGIN_ROOT))
import update_catalog


def main():
    parser = argparse.ArgumentParser(
        description='Build/update release catalog from verified package',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s --package plugin.zip --channel preview --url https://github.com/.../plugin-0.12.3.zip --notes "Fixed bug X" --output catalog.json
  %(prog)s --package plugin.zip --channel stable --url https://github.com/.../plugin-0.12.3.zip --notes "New features" --output catalog.json --data-upgrade
        '''
    )
    parser.add_argument('--package', required=True, help='Path to verified plugin ZIP file')
    parser.add_argument('--channel', required=True, choices=['stable', 'preview'],
                        help='Release channel (stable or preview)')
    parser.add_argument('--url', required=True,
                        help='GitHub release URL for the package')
    parser.add_argument('--notes', required=True,
                        help='Path to notes file containing release notes (plain text, max 20000 characters)')
    parser.add_argument('--output', required=True,
                        help='Output catalog JSON file path')
    parser.add_argument('--data-upgrade', action='store_true',
                        help='Mark this release as requiring data workspace upgrade')
    parser.add_argument('--qgis', default='3.44.14',
                        help='QGIS version for compatibility checking (default: 3.44.14)')
    parser.add_argument('--installed', default='0.12.2',
                        help='Currently installed version (default: 0.12.2)')
    
    args = parser.parse_args()
    
    # Validate package
    package_path = Path(args.package)
    notes_path = Path(args.notes)
    if not package_path.is_file():
        print(f"Error: Package file not found: {args.package}", file=sys.stderr)
        sys.exit(1)
    if not notes_path.is_file():
        print(f"Error: Notes file not found: {args.notes}", file=sys.stderr)
        sys.exit(1)
    
    # Read notes
    try:
        notes_text = notes_path.read_text(encoding='utf-8')
        if len(notes_text) > 20000:
            print(f"Error: Notes too long (max 20000 chars): {len(notes_text)}", file=sys.stderr)
            sys.exit(1)
        # Check for forbidden characters
        if '<' in notes_text or '>' in notes_text:
            print("Error: Release notes must not contain HTML tags", file=sys.stderr)
            sys.exit(1)
    except UnicodeError as e:
        print(f"Error: Invalid notes file encoding: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Create release metadata
    release = {
        'version': '0.12.3',  # Placeholder - will be set from verified package
        'channel': args.channel,
        'qgis_minimum': '3.28',
        'qgis_maximum': '3.99',
        'url': args.url,
        'sha256': 'placeholder',  # Will be computed
        'size': 0,  # Will be computed
        'notes': notes_text,
        'restart_required': True,
        'data_upgrade': args.data_upgrade
    }
    
    try:
        # Verify the package
        metadata = update_catalog.verify_package(package_path, None, args.qgis)
        release['version'] = metadata['version']
        # Compute actual SHA256
        release['sha256'] = update_catalog._hash_file(package_path)
        release['size'] = package_path.stat().st_size
        
    except ValueError as e:
        print(f"Error: Package verification failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Read or create catalog
    output_path = Path(args.output)
    existing_releases = []
    release_exists = False
    
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                catalog = json.load(f)
            if catalog.get('schema_version') == 1:
                existing_releases = catalog.get('releases', [])
                # Check if this release already exists (same version in same channel)
                for existing in existing_releases:
                    if existing.get('version') == release['version'] and existing.get('channel') == release['channel']:
                        print(f"Error: Release {release['version']} already exists in {release['channel']} channel", file=sys.stderr)
                        print("Not overwriting existing catalog", file=sys.stderr)
                        release_exists = True
                        break
                # Also check if this version exists in a different channel in the SAME catalog file
                for existing in existing_releases:
                    if existing.get('version') == release['version'] and existing.get('channel') != release['channel']:
                        print(f"Error: Release {release['version']} already exists in {existing['channel']} channel", file=sys.stderr)
                        print("A version can only appear once per channel", file=sys.stderr)
                        release_exists = True
                        break
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Could not read existing catalog: {e}", file=sys.stderr)
            catalog = {'schema_version': 1, 'releases': []}
    else:
        catalog = {'schema_version': 1, 'releases': []}
    
    # Check if this version already exists in ANY catalog file in the same directory
    # (This prevents adding the same version to multiple channels across different files)
    if not release_exists and output_path.parent.exists():
        for catalog_file in output_path.parent.glob('*.json'):
            if catalog_file == output_path:
                continue
            try:
                with open(catalog_file, 'r') as f:
                    other_catalog = json.load(f)
                if other_catalog.get('schema_version') == 1:
                    for existing in other_catalog.get('releases', []):
                        if existing.get('version') == release['version']:
                            print(f"Error: Release {release['version']} already exists in {catalog_file}", file=sys.stderr)
                            print("A version can only appear once across all catalog files", file=sys.stderr)
                            release_exists = True
                            break
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Warning: Could not read {catalog_file}: {e}", file=sys.stderr)
        
        if release_exists:
            print("Aborted: Would create duplicate version across catalog files", file=sys.stderr)
            sys.exit(1)
    
    # If release exists, exit with error (don't overwrite)
    if release_exists:
        print("Aborted: Would overwrite existing catalog", file=sys.stderr)
        sys.exit(1)
    
    # Add new release
    existing_releases.append(release)
    catalog['releases'] = existing_releases
    
    # Write catalog
    try:
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        print(f"Catalog written to: {args.output}")
        print(f"Release {release['version']} ({release['channel']}) added")
        if args.data_upgrade:
            print("  -> Marked as data upgrade")
        print(f"\nNote: This catalog is NOT published. Use proper publishing process for public releases.")
        
    except IOError as e:
        print(f"Error: Could not write catalog: {e}", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
