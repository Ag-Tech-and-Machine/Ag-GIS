"""Assemble one pinned private existing-QGIS kit without executing shipped code."""
import argparse
import binascii
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

from verify import PLUGIN_SHA, LAUNCHER_SHA, ICON_SHA, REVISION, inventory, privacy_scan, read_archive, require, safe_name, sha, source_mapping

TEAM = Path('C:/Users/Michael/AppData/Local/hermes/ag-gis-team')
SOURCE = Path('C:/Users/Michael/Documents/Projects/repos/Ag-GIS')
WORK = TEAM / 'worktrees/launcher-kit-b2-doc-sanitised'
FREEZE = TEAM / 'evidence/launcher-kit-b2-freeze.json'
MAINTAINER = TEAM / 'evidence/launcher-kit-doc-sanitise/2cd9895b26b553cfdb883ac4'
PLUGIN = MAINTAINER / 'ag_tech_tooling-0.12.2-doc-sanitised.zip'
ALLOWLIST = MAINTAINER / 'corresponding-source-proposal.json'
LAUNCHER = SOURCE / '.aggis-agent/evidence/20261020-deere-branded/launcher/Ag-GIS.exe'
DEFAULT_OUTPUT = TEAM / 'evidence/launcher-kit-b2/candidate'

README = r'''Ag-GIS experimental existing-QGIS launcher kit
Farming in view. Built on open source tools.

This private candidate requires an ALREADY installed, permitted Windows QGIS
3.44.14 LTR with bin\qgis-ltr.bat and its normal bundled components. No runtime,
installer, Start Menu shortcut, MSI, bootstrap or installation-policy override
is included. It is not a standalone or clean-machine Windows installer.
The retained unsigned launcher has not been recompiled. Treat it as experimental.

Configuration and intended-profile plugin installation
1. Extract the whole kit into a new local folder you control. Keep Ag-GIS.exe,
   Ag-GIS.ico and launch.txt together. Do not copy over a running installation.
2. Using the existing permitted QGIS application, deliberately create/select a
   separate named profile, for example AgGIS_Experimental, through QGIS's native
   Settings > User Profiles controls. Check the actual intended profile before
   installing anything. Do not use another person's existing profile or farm.
3. In THAT profile use Plugins > Manage and Install Plugins > Install from ZIP.
   Select the enclosed ag_tech_tooling-0.12.2.zip and enable Ag-GIS. This is the
   native Plugin Manager path; no Python/profile installer script is included.
   Close that test-profile application cleanly before using the launcher.
4. Edit launch.txt as plain text with EXACTLY two lines, no quotes or comments:
      C:\Program Files\QGIS 3.44.14
      AgGIS_Experimental
   The first line is the actual permitted installed QGIS root (not its bin folder).
   It must contain bin\qgis-ltr.bat. Change it if your existing installation is
   elsewhere. The second is the intended profile name, using letters, digits,
   underscore and hyphen only. The supplied lines are a TEMPLATE, not discovery
   of your installed runtime or settings. No user farm path is configured here.
5. Start this kit's Ag-GIS.exe with no arguments. The existing launcher reads
   launch.txt and delegates to native bin\qgis-ltr.bat --nologo --profile NAME.
   It cannot install a runtime, accept a project argument or configure profile
   storage roots. Native batch execution remains subject to your current policy.
   If denied or missing, STOP; do not change policy, bypass it or run an installer.
6. Keep any isolated settings/auth/temp/config-root environment overrides outside
   this kit. A profile name alone does not prove full process/settings isolation.
   Establish and verify the intended locations before test workspace writes.
   Use New Project with Options for an explicit synthetic location. Do not use
   real farm data for qualification. Save Map and native close precede reopening.

The packaged guide describes current behaviour. Native About, QGIS controls,
credits and licences remain available. No cloud/sign-in or paid imagery entitlement
is granted; optional background services have their own terms and attribution.
Keep source and workspaces together when deliberately backing up your own data.

Sources and licence
LICENSE contains GPL v2; Ag-GIS source is GPL-2.0-or-later. Enclosed
corresponding-source.zip contains the exact proposed source/resource subset for
this kit plus BUILDING.txt and a member manifest. CREDITS.txt records upstream and
artwork provenance. The source subset is NOT the whole development repository.
Retained binary reuse is not a reproducible-build or compiler-output claim.

Acceptance boundaries
Static packaging/CRC/source equality is not native branded workflow acceptance,
unassisted farmer acceptance, clean-machine support, release approval or public
availability. Independent exact-kit workflow qualification and final independent
source/licence/privacy review remain required before any publication decision.
Do not redistribute this private candidate as an approved release.
'''

BUILDING = r'''Corresponding source candidate - existing-QGIS Ag-GIS kit

Source and resource names preserve the existing project layout. Ordinary plugin
ZIP entries map from plugins/ag_tech_tooling/<name>. USER_GUIDE.txt maps from
docs/USER_GUIDE.md; START_HERE.txt maps from START_HERE.md. The exact shipped ZIP
is retained unchanged; no plugin source or runtime behaviour was rebuilt here.

Existing plugin packaging source: tools/build_plugin.py imports
check_plugin.py from the same tools directory. With ordinary Python, from the
source root, its documented interface is:
  python tools/build_plugin.py --output <new-plugin.zip>
The helper copies source files and guides into the QGIS plugin layout and checks
CRC. Running it on a future compiler/library environment does not guarantee ZIP
byte identity to the retained shipped archive. Install the shipped exact ZIP
through native QGIS Plugin Manager into the deliberately intended profile.

Launcher: installer/Launch.cs is GPL-2.0-or-later source for the retained
Ag-GIS.exe. It requires Windows .NET Framework System, System.Drawing and
System.Windows.Forms and the Windows Segoe UI font for its existing splash.
A conventional developer C# compiler invocation, from a separate writable copy,
is (adjust csc location to an already available permitted compiler):
  csc /nologo /target:winexe /out:Ag-GIS.exe /win32icon:installer/Ag-GIS.ico /reference:System.Drawing.dll /reference:System.Windows.Forms.dll installer/Launch.cs
No compiler was executed for this kit. This instruction is not proof that a new
compiler output equals the retained binary. Retained source/executable binding
was checked privately against the historical run receipt, not recreated here.
Native bin\qgis-ltr.bat remains an existing QGIS prerequisite, not redistributed.
No Setup.exe, MSI, installer script or policy-changing command is needed here.

Artwork: plugins/ag_tech_tooling/icon.svg is the editable original field/survey
symbol. tools/build_brand_assets.py is the existing Qt/QGIS renderer and icon/
outlined-wordmark recipe. It reads the existing Windows Segoe UI fonts and uses
bundled QGIS/PyQt/QtSvg. Run only in a separate writable source copy because it
writes installer/Ag-GIS.ico, app_icon.ico, brand_lockup.svg and dist/branding.
Its runtime and fonts are prerequisites, not included or licensed by this kit.
Existing outlined SVG and ICO bytes are preserved; no assets regenerated here.
The enclosed original icon/source and generator are proposed corresponding
materials, subject to final independent licence/provenance review.

The exact 63 source/resource paths were selected separately from the complete
private baseline. SOURCE_MANIFEST.json records their bytes plus this build note.
No development history, local configuration, operations, farm data or transcripts
are included. No claim of full-repository completeness or publication clearance.
'''

CREDITS = '''Ag-GIS - Farming in view. Built on open source tools.
Ag-GIS code is GPL-2.0-or-later; full GPL v2 text is in LICENSE. Preserve existing
source copyright, licence and author notices, including plugin metadata credit.
The field/survey symbol and outlined Ag-GIS wordmark are original project artwork;
editable icon.svg, existing ICO, outlined SVG and generator accompany this kit.
No trademark clearance or upstream endorsement is claimed.

The existing desktop foundation is QGIS/PyQGIS and its bundled Qt/geospatial
providers. They are separately installed prerequisites, not redistributed here.
Retain native QGIS About, upstream credits/licences and service attribution.
QGIS: https://qgis.org/  GNU GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
Windows/.NET Framework and Segoe UI are existing platform prerequisites, not
redistributed fonts or runtime components. No rights to third-party trademarks,
paid imagery or upstream services are granted by this kit.

Optional user-facing agent examples, public service URLs, existing author credit
and standard GPL sample attribution remain verbatim in the shipped components.
Final independent corresponding-source, artwork, licence and privacy review is
pending before any public release. This is a private packaging candidate only.
'''


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def zip_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            safe_name(name)
            item = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            item.create_system = 3
            item.external_attr = (stat.S_IFREG | 0o444) << 16
            item.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(item, data, compresslevel=9)
    return buffer.getvalue()


def archive_record(data):
    return {'sha256': sha(data), 'size': len(data), 'members': inventory(read_archive(data))}


def preflight():
    freeze = json.loads(FREEZE.read_bytes())
    require(freeze['base_revision'] == REVISION and len(freeze['files']) == 210, 'freeze identity/count')
    actual = {n: sha((WORK / n).read_bytes()) for n in freeze['files']}
    require(actual == freeze['files'], 'private210 source mismatch')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=WORK, capture_output=True, text=True)
    revision.check_returncode()
    require(revision.stdout.strip() == REVISION, 'assigned source revision changed')
    proposal = json.loads(ALLOWLIST.read_bytes())
    require(proposal['commit'] == REVISION and len(proposal['files']) == 63, 'allowlist identity/count')
    source_files = {}
    for item in proposal['files']:
        name = safe_name(item['path'])
        require(name not in source_files, 'duplicate allowlist')
        data = (WORK / name).read_bytes()
        require(sha(data) == item['sha256'] and len(data) == item['size'], 'allowlist bytes mismatch')
        source_files[name] = data
    plugin_bytes = PLUGIN.read_bytes()
    launcher_bytes = LAUNCHER.read_bytes()
    icon = (WORK / 'installer/Ag-GIS.ico').read_bytes()
    require(sha(plugin_bytes) == PLUGIN_SHA, 'successor plugin mismatch')
    require(sha(launcher_bytes) == LAUNCHER_SHA, 'launcher mismatch')
    require(sha(icon) == ICON_SHA, 'icon mismatch')
    require(sha(source_files['installer/Launch.cs']) == 'f26c7aa46b3a10fd7afc0ff8e921d2b2ca86843120793301c83313e8e798ceb5', 'launcher source mismatch')
    retained = json.loads((SOURCE / '.aggis-agent/evidence/20261020-deere-branded/journey-process.json').read_bytes())
    require(retained['launcher_sha256'] == LAUNCHER_SHA and retained['launcher_source_sha256'] == sha(source_files['installer/Launch.cs']), 'retained executable/source binding mismatch')
    require(retained['exit'] == retained['wait'] == retained['launcher_exit'] == 0, 'historical binding receipt')
    plugin = read_archive(plugin_bytes)
    require(len(plugin) == 57, 'plugin count')
    mappings = {}
    for name, data in plugin.items():
        source_name = source_mapping(name)
        require(source_name in source_files and data == source_files[source_name], 'plugin/source mismatch: ' + name)
        mappings[name] = source_name
    findings = privacy_scan(source_files)
    require(not findings, 'new privacy finding: ' + json.dumps(findings))
    return source_files, plugin_bytes, launcher_bytes, icon, {'private210': actual, 'plugin_mappings': mappings, 'source_allowlist': sorted(source_files), 'freeze_sha256': sha(FREEZE.read_bytes()), 'allowlist_sha256': sha(ALLOWLIST.read_bytes()), 'retained_binding_receipt_sha256': sha((SOURCE / '.aggis-agent/evidence/20261020-deere-branded/journey-process.json').read_bytes()), 'contextual_triage': json.loads((MAINTAINER / 'privacy-triage.json').read_bytes()), 'publication_review_pending': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    allowed_parent = (TEAM / 'evidence/launcher-kit-b2').resolve()
    require(args.output.resolve().parent == allowed_parent, 'output must be a fresh immediate launcher-kit-b2 subdirectory')
    require(not args.output.exists(), 'output already exists; refusing replacement')
    source, plugin, launcher, icon, provenance = preflight()
    source['BUILDING.txt'] = BUILDING.encode('utf-8')
    source['SOURCE_MANIFEST.json'] = encoded({'source_revision': REVISION, 'publication_review_pending': True, 'members': inventory(source)})
    source_zip = zip_bytes(source)
    kit = {'Ag-GIS.exe': launcher, 'Ag-GIS.ico': icon, 'ag_tech_tooling-0.12.2.zip': plugin, 'launch.txt': b'C:\\Program Files\\QGIS 3.44.14\r\nAgGIS_Experimental\r\n', 'README.txt': README.encode('utf-8'), 'CREDITS.txt': CREDITS.encode('utf-8'), 'LICENSE': source['LICENSE'], 'corresponding-source.zip': source_zip}
    kit['manifest.json'] = encoded({'source_revision': REVISION, 'publication_review_pending': True, 'members': inventory(kit)})
    require(not privacy_scan(source) and not privacy_scan(kit), 'generated text privacy finding')
    kit_zip = zip_bytes(kit)
    manifest = {'source_revision': REVISION, 'kit': archive_record(kit_zip), 'source': archive_record(source_zip), 'plugin': archive_record(plugin), 'publication_review_pending': True}
    # Exclusive directory creation prevents replacing a prior candidate/evidence set.
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in {'Ag-GIS-existing-QGIS-kit.zip': kit_zip, 'corresponding-source.zip': source_zip, 'member-manifests.json': encoded(manifest), 'provenance-private.json': encoded(provenance)}.items():
        with (args.output / name).open('xb') as stream:
            stream.write(data)
    # Content-addressed receipts and read-only attributes: future work uses new dirs.
    for name in ('Ag-GIS-existing-QGIS-kit.zip', 'corresponding-source.zip', 'member-manifests.json'):
        (args.output / name).chmod(stat.S_IREAD)
    print(json.dumps({'output': str(args.output), 'source_revision': REVISION, 'kit_sha256': manifest['kit']['sha256'], 'source_sha256': manifest['source']['sha256'], 'plugin_sha256': PLUGIN_SHA, 'counts': {'kit': len(kit), 'source': len(source), 'allowlist': len(provenance['source_allowlist']), 'plugin': len(provenance['plugin_mappings']), 'private_baseline': len(provenance['private210'])}, 'publication_review_pending': True, 'runtime_executed': False}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(1)
