#!/usr/bin/env python3
"""
Ag-GIS update catalog candidate builder.

Generates a preview of the update catalog from a plugin ZIP, release URL and notes.
Does NOT publish, upload or install anything - only creates local candidate files.

Usage:
    python build_update_catalog.py --package <path> --channel <preview|stable> \
        --url <github-release-url> --notes <notes-file> --output <output-json>
        [--data-upgrade]
"""
import argparse
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime

# Constants
VERSION_PATTERN = "v{version}/ag_tech_tooling-{version}.zip"
SCHEMA_VERSION = 1


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def parse_version(version_str: str) -> tuple:
    """Parse version string into tuple for comparison. Handles '0.12.3' and '0.12.3-preview'."""
    # Remove leading 'v' if present
    version_str = version_str.lstrip('v')
    
    # Split by common separators
    parts = version_str.replace('-', '.').replace('_', '.').split('.')
    
    # Extract major.minor.patch
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    
    return (major, minor, patch)


def get_plugin_info(zip_path: Path) -> dict:
    """Extract plugin info from ZIP file."""
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check if it's a valid plugin ZIP
            for name in zf.namelist():
                if name.startswith('ag_tech_tooling/'):
                    return {
                        'name': 'ag_tech_tooling',
                        'is_valid': True
                    }
            return {'is_valid': False}
    except Exception as e:
        print(f"Error reading plugin ZIP: {e}", file=sys.stderr)
        return {'is_valid': False}


def main():
    parser = argparse.ArgumentParser(
        description='Build an update catalog candidate from a plugin package'
    )
    parser.add_argument('--package', required=True, help='Path to plugin ZIP file')
    parser.add_argument('--channel', required=True, choices=['preview', 'stable'],
                        help='Release channel (preview or stable)')
    parser.add_argument('--url', required=True, help='GitHub release download URL')
    parser.add_argument('--notes', required=True, help='Path to release notes file')
    parser.add_argument('--output', required=True, help='Path for candidate JSON output')
    parser.add_argument('--data-upgrade', action='store_true',
                        help='Mark as requiring data schema upgrade')
    
    args = parser.parse_args()
    
    # Validate inputs
    package_path = Path(args.package)
    notes_path = Path(args.notes)
    
    if not package_path.exists():
        print(f"Error: Package file not found: {args.package}", file=sys.stderr)
        sys.exit(1)
    
    if not notes_path.exists():
        print(f"Error: Notes file not found: {args.notes}", file=sys.stderr)
        sys.exit(1)
    
    # Parse version from package path
    # Expected format: dist/ag_tech_tooling-0.12.3.zip
    package_name = package_path.stem  # e.g., "ag_tech_tooling-0.12.3"
    version_parts = package_name.split('-')
    if len(version_parts) < 2:
        print(f"Error: Invalid package name format: {package_name}", file=sys.stderr)
        sys.exit(1)
    
    version = version_parts[-1]  # Get the version number
    version_tuple = parse_version(version)
    
    # Compute hash and size
    file_size = package_path.stat().st_size
    sha256 = compute_sha256(package_path)
    
    # Extract plugin info
    plugin_info = get_plugin_info(package_path)
    if not plugin_info.get('is_valid'):
        print("Warning: Could not validate plugin ZIP structure", file=sys.stderr)
    
    # Read release notes
    try:
        notes = notes_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading notes: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Build release entry
    release = {
        'version': version,
        'version_tuple': list(version_tuple),
        'channel': args.channel,
        'qgis_min': '3.28.0',
        'qgis_max': None,
        'url': args.url,
        'sha256': sha256,
        'size': file_size,
        'notes': notes,
        'restart_required': True,
        'data_upgrade': args.data_upgrade,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Build candidate document
    candidate = {
        'schema_version': SCHEMA_VERSION,
        'channel': args.channel,
        'releases': [release]
    }
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write with metadata
    metadata = {
        'build_version': '.'.join(str(x) for x in version_tuple),
        'build_time': datetime.utcnow().isoformat() + 'Z',
        'input_package': str(package_path),
        'input_url': args.url,
        'input_notes': str(notes_path)
    }
    
    output_content = json.dumps({
        'metadata': metadata,
        'releases': candidate['releases']
    }, indent=2)
    
    output_path.write_text(output_content, encoding='utf-8')
    
    # Print summary
    print(f"Catalog candidate built: {output_path}")
    print(f"  Version: {version}")
    print(f"  Channel: {args.channel}")
    print(f"  SHA256: {sha256[:16]}...")
    print(f"  Size: {file_size:,} bytes")
    print(f"  Data upgrade: {'Yes' if args.data_upgrade else 'No'}")
    print(f"  Notes: {len(notes)} characters")
    
    print("\nNote: This is a candidate only. Publication requires owner approval.", file=sys.stderr)
    print("      Do NOT upload this file or use in production without review.", file=sys.stderr)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
