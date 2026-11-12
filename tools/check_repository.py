"""Portable repository checks only; no QGIS integration or release claim."""
import ast
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    'START_HERE.md', 'CONTRIBUTING.md', 'SECURITY.md', 'CODE_OF_CONDUCT.md',
    'LICENSE', '.editorconfig', '.github/copilot-instructions.md',
    'docs/DEVELOPMENT.md', 'docs/ARCHITECTURE.md', 'docs/ROADMAP.md',
    'docs/USER_COMMITMENTS.md', 'docs/BRAND_ASSETS.md',
    'assets/brand/ag-gis-symbol.svg', 'assets/brand/ag-gis-lockup.svg',
    'assets/brand/ag-gis.ico', '.github/workflows/repository-checks.yml',
)


def check():
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            raise ValueError('Missing repository entry: ' + name)
    # A green portable check must not conceal missing source/package test entrypoints.
    for inventory in ('scripts/check.ps1', 'tools/package_test.py'):
        scripts = re.findall(r"['\"]([^'\"\r\n]+\.py)['\"]",
                             (ROOT / inventory).read_text(encoding='utf-8'))
        if not scripts:
            raise ValueError('Empty test inventory: ' + inventory)
        for script in scripts:
            if not (ROOT / 'tools' / script).is_file():
                raise ValueError(f'{inventory} references missing test: {script}')
    for directory in ('plugins', 'tools'):
        for path in (ROOT / directory).rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    markdown = [ROOT / 'START_HERE.md', ROOT / 'README.md', ROOT / 'CONTRIBUTING.md',
                *(ROOT / 'docs').glob('*.md')]
    for path in markdown:
        text = path.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)', text):
            target = target.strip().strip('<>').split('#')[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            target = target.replace('%20', ' ')
            destination = (path.parent / target).resolve()
            if not destination.is_relative_to(ROOT) or not destination.exists():
                raise ValueError(f'{path.relative_to(ROOT)} has missing/escaping link: {target}')
    for path in (ROOT / 'assets/brand').glob('*.svg'):
        text = path.read_text(encoding='utf-8')
        if '<script' in text.lower() or '<foreignobject' in text.lower():
            raise ValueError('Unexpected active SVG content: ' + path.name)
        for node in ET.fromstring(text).iter():
            for key, value in node.attrib.items():
                if key.lower().endswith('href') and value and not value.startswith('#'):
                    raise ValueError('External SVG dependency: ' + path.name)
    if (ROOT / 'assets/brand/ag-gis.ico').read_bytes()[:4] != b'\x00\x00\x01\x00':
        raise ValueError('Invalid Windows icon header')
    # Only tracked paths: ignored local farm data must not become a source commit.
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    for name in paths:
        path = Path(name)
        if path.suffix.lower() in {'.gpkg', '.qgz', '.qgs', '.las', '.laz', '.tif', '.tiff', '.pem', '.key'} or path.name == '.env' or path.name.startswith('.env.'):
            raise ValueError('Review/remove tracked data or credential file: ' + name)
    print('Repository structure, local links, Python syntax and brand assets OK.')
    print('Basic checks only: PyQGIS integration, security and release readiness are not established.')


if __name__ == '__main__':
    check()
