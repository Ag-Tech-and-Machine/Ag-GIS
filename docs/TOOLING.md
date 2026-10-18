# Development and tooling

## Repository artwork — 19 October 2026

`tools/build_repository_artwork.py` uses QGIS's bundled Qt and Windows Segoe UI
fonts to regenerate the outlined banner and PNG/social exports. It does not alter
plugin or installer assets. Follow [repository presentation](REPOSITORY_PRESENTATION.md)
for exact commands, screenshot privacy/provenance and remote read-back checks.
GitHub About/topics/social-preview settings are separate from committed files.

Last updated: 15 October 2026.

## What exists now

| Item | Purpose |
| --- | --- |
| `plugins/ag_tech_tooling/__init__.py` | QGIS `classFactory` entry point |
| `plugins/ag_tech_tooling/plugin.py` | Starter action and clean load/unload lifecycle |
| `plugins/ag_tech_tooling/simple_view.py` | Bottom-right Simple view control, profile preference and full-layout restoration |
| `plugins/ag_tech_tooling/metadata.txt` | Name, version, author and compatibility metadata |
| `plugins/ag_tech_tooling/icon.svg` | Toolbar/menu icon |
| `scripts/launch-qgis.ps1` | Start QGIS with source plugin discovery and an isolated profile |
| `scripts/check.ps1` | Run syntax/metadata checks, Qt/PyQGIS smoke check and ZIP build |
| `tools/check_plugin.py` | Check Python syntax and mandatory metadata |
| `tools/smoke_test.py` | Exercise entry point, action, duplicate-init prevention and unload using Qt/PyQGIS |
| `tools/build_plugin.py` | Produce and validate a QGIS plugin ZIP |
| `scripts/install-plugin.ps1` | Check, build, install and enable the packaged plugin in an existing normal QGIS profile |
| `tools/install_plugin.py` | Validate ZIP paths, back up existing files/settings and install the built package |

The plugin provides Simple view, the dedicated toolbar, one-click starter creation, full native Layers hierarchy and GeoPackage hierarchy management. Processing algorithms, automatic updates and a remote Git repository remain future work.

## Use Simple view

1. Install/enable Ag-GIS as described in `INSTALL.md`.
2. Check **Simple view** in QGIS's bottom-right status bar.
3. Use the Ag-GIS toolbar to create/open/save maps and move/zoom; use Layers to browse the complete farm hierarchy and control visible data. The main area contains only the map and Layers. Add data through **Layer → Add Layer**, or turn Simple view off if you need Browser. QGIS menus remain available.
4. Uncheck **Simple view** when you need the previous full workspace. Its toolbar/panel layout is restored.
5. The profile remembers your choice. Turning off the plugin restores the workspace and removes the switch.

The setting is stored in the QGIS profile, outside Git. A saved full-layout snapshot supports restoration across plugin reloads and restarts. Simple view keeps Layers available and prevents other dock panels and welcome pages from reappearing. It does not simplify individual dialog contents or remove advanced features from QGIS; turn it off to use the full workspace.

## Work through each tooling change

1. State the user's task, inputs and expected result. Record consequential scope or dependency decisions in the work log.
2. Implement the smallest useful feature in the plugin source. Use `qgis.PyQt` for Qt integration and retain a matching unload path for every GUI registration.
3. Update this guide with the feature's exact controls, input requirements, output location and operating steps. Update the installation guide when prerequisites, installation or launch behaviour changes.
4. Run the relevant checks. For changes to the plugin lifecycle or functionality, start with:

   ```powershell
   .\scripts\check.ps1
   ```

5. Test the changed behaviour in QGIS using a suitable small dataset. Record expected versus actual results, including any data-specific limitations. Restart QGIS after source changes.
6. When packaging changes, test the ZIP in a separate profile as described in the installation guide.
7. Review and commit the code and documentation together:

   ```powershell
   git diff
   git status
   git add <explicit changed files>
   git commit -m "Describe the completed tooling change"
   ```

   Replace the angle-bracket placeholder with the reviewed file paths. Do not stage datasets, credentials or generated profile files.

8. Update the work log with checks completed, remaining issues and the next useful step. Report verified behaviour separately from planned features.

## Run the current starter

1. Follow `INSTALL.md` to launch the development profile and enable the plugin.
2. Open a QGIS project or add layers.
3. Run **Ag-GIS** from its menu or toolbar.
4. Read the layer-count message. The starter does not alter the project or layer data.

## Build an installable ZIP

1. Run `scripts\check.ps1` from the repository root.
2. Find the ZIP in `dist`. Its version comes from `metadata.txt`.
3. Confirm the check command succeeds before distributing the ZIP.
4. Use QGIS's **Install from ZIP** control and perform a manual action check.

## Version and release changes

1. Change the version in `metadata.txt` when preparing a release.
2. Document new behaviour and any migration/install changes.
3. Run automated and manual checks appropriate to that release.
4. Retain the GPL-2.0-or-later license in source and plugin packages. Confirm public project/support URLs and QGIS version compatibility before publishing to the public plugin repository. Public hosting and publishing decisions are not yet complete.
5. Create a release tag only after a release has been verified. Publication, GitHub remote creation and release automation are not implemented in this starter.

## Native QGIS and packaging requirements

Every runtime control, module and resource ships in the Ag-GIS ZIP. `docs/USER_GUIDE.md` is bundled as `ag_tech_tooling/USER_GUIDE.txt`; source/development scripts are not required on a user's machine. Farm data remains outside the plugin directory and outside Git.

GeoPackage creation uses `QgsVectorLayer`, the memory provider, `QgsFeature` and `QgsVectorFileWriter.writeAsVectorFormatV3`, with QGIS's transform context and bundled OGR provider. Project IO uses `QgsProject`; interface controls use QGIS's `iface` and `qgis.PyQt`. Read-only Python SQLite queries check the farm database's structure and identity; they do not implement GIS transformations or writes.

Future imports/exports and conversions must use QGIS data providers/writers, `QgsCoordinateTransform` and the QGIS Processing framework as appropriate. Use processing context, feedback/cancellation and explicit output destinations. These workflows are planned; no Processing algorithm is currently run by the farm foundation. Do not introduce a separate GIS installation or shell utility when QGIS supports the operation.

1. Run `scripts/check.ps1` using the installed QGIS runtime.
2. Confirm source lifecycle/farm tests and ZIP build pass.
3. Confirm `tools/package_test.py` passes: it checks exact archive content/bytes and runs lifecycle and farm tests from an extracted ZIP.
4. Install the built ZIP, restart QGIS and verify the controls in the installed profile.
5. For missing modules or resources, fix the package and rebuild; do not ask users to copy files from the repository manually.

References: [QGIS vector writer API](https://api.qgis.org/api/classQgsVectorFileWriter.html), [QGIS 3.44 Processing](https://docs.qgis.org/3.44/en/docs/user_manual/processing/console.html).

## Documentation responsibilities

The manager maintains installation instructions, tool usage, verification evidence, known failures and next steps during development. A feature is not complete until its relevant instructions match the implementation. Documentation-only edits need editorial review and link/path checks; they do not require rerunning unchanged code tests.

Reference: https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html

## Ready for the first tool

Follow the [Organisation/Client/Farm/Field model](FARM_DATA_MODEL.md). Version 0.6.0 implements schema 2 hierarchy/season/crop records and the focused Manage Data tree, with native field-filtered reference layers. Schema 1 stays readable; upgrading creates a separate validated copy with confirmed ownership. Toolbar dropdown selectors, seasonal datasets, jobs and external Grower/Client mapping workflows remain future work. See INSTALL.md and USER_GUIDE.md for exact steps.

Within each field, the management tree implements **Whole Field / Seasons** grouping. Three shared native spatial tables store field reference features; season/crop records are nonspatial tables. Planning/operations/results and terrain rows are organisational categories, not implemented dataset editors. Automated revision history and historical job references remain to be built.

Interface optimisation takes precedence over expanding the feature set. For each increment:

1. Identify the farmer's task and the native QGIS capability to reuse.
2. Define where the control belongs, its plain-language wording and the shortest understandable task flow.
3. Prefer existing QGIS actions/widgets/dialogs; add focused controls where these improve usability.
4. Verify that Simple view retains map and Layers, advanced tools remain recoverable, and cancellation protects existing work.
5. Implement the underlying data/processing step using QGIS APIs and keep its instructions and packaging aligned.

Version 0.6.0 uses the dedicated top Ag-GIS toolbar as the main farmer-facing entry point. New/Open Project and Manage Data share actions with the plugin menu; Save Map, Move Map, zoom and Whole Map reuse QGIS's QAction instances with locally labelled buttons. Do not modify shared native QAction labels or ownership. Simple view keeps this toolbar and hides other existing QGIS toolbars; unloading removes the plugin toolbar and retains native actions. Further workflows should be added here when implemented, using clear task groups and native capabilities.

The data foundation is documented in [Farm projects](FARM_PROJECTS.md). GeoPackage is the selected core format. Version 0.6.0 creates/opens schema 2 workspaces and manages the four-level hierarchy, seasons/crops and reference layers. Follow `INSTALL.md` and `USER_GUIDE.md`. `scripts/check.ps1` includes both legacy farm checks and `tools/hierarchy_test.py` using disposable data and native QGIS providers.

1. Describe the farming task in the user's words.
2. Identify the sample input files or layers, units and coordinate reference system where relevant.
3. Agree the expected output and where to save it.
4. Specify what an acceptable result looks like and which inputs should produce helpful errors.
5. Implement, test on the sample data and document the workflow together.

The default-profile installation is for using the built plugin. The isolated development launcher is for editing the repository source. Rebuild/reinstall after changes to refresh the normal-profile copy.

## Deere export inspection

Use [Machine data imports](IMPORTS.md) for the GS3 folder inspection workflow.
Run `tools/deere_preview_test.py` with QGIS Python; then build a package and rerun
with `AGTECH_TEST_PLUGIN_ROOT` set to its extraction folder. The top-level runtime
module is included automatically by `tools/build_plugin.py`. Inspection uses
native `QgsProviderRegistry.querySublayers` for geometry discovery, retains XML
machine IDs/properties and verifies source file hashes. It never converts unknown
binary geometry or writes to the workspace. Data In now provides GUI discovery
and linked map-layer opening; decoded guidance and managed farm storage remain
pending. Do not present metadata preview as completed machine-data import.

## Farm browser presentation — 0.8.0

The main left-hand browser remains the native `QgsLayerTreeView` and its existing model/selection. `farm_browser.py` wraps its item delegate: managed hierarchy groups receive the same semantic icons as Manage Data, 20-pixel icons, a minimum 26-pixel row height and restrained bold headings. Indentation is 14 pixels to reduce clipped labels in a deep hierarchy. Full type/name tooltips identify each level. The panel title is Farm Data for schema 2 projects and Layers for ordinary QGIS projects.

Layer/symbol painting, visibility events and native editor methods forward to the original delegate. Editor signals are bridged and disconnected on teardown. Unloading restores the original delegate, spacing, icon size and panel title; project-read/clear connections are paired. This changes presentation only and does not create a second data model or alter geometry/style/ownership.

1. Run `tools/farm_browser_test.py` with the QGIS Python wrapper. It verifies each semantic icon, group row sizing, actual checkbox clicks, native editing, unrelated layers and restoration on project changes/reload.
2. Run `scripts/check.ps1` to repeat those checks against source and the extracted ZIP, alongside the existing farm/import checks.
3. Install/restart QGIS and visually check the left browser with a real farm project. Record the screenshot and installation status in WORK_LOG.md.

## Default workspace and native hierarchy — 0.6.0

1. Click **New Project**. `workspace_defaults.py` resolves the operating system Documents folder through Qt `QStandardPaths`, creates `Ag-GIS/Projects` if needed and chooses a free **My Farm Data** numbered folder. No ownership/path form is shown.
2. The native writer creates schema 2 with Organisation 1, Client 1, Farm 1, Field 1 and Season 1. Crops/dates/geometries stay empty. The current map CRS is used when recognised; otherwise EPSG:4326. Explicit settings remain in the menu-only **New Project with Options…** form.
3. `sync_tree` mirrors every stored organisation/client/farm/field/season/crop into native `QgsLayerTreeGroup` nodes keyed by stable IDs. Labels are short at each level; Whole Field and Seasons remain separate beneath every field. Plans/Operations/Results are categories only.
4. Selection uses the native `QgsLayerTreeView` proxy-aware `index2node` mapping. Field selection reuses three field-filtered native reference layers and keeps unrelated layers. Finish edit sessions before switching; errors restore the previous selection. Adds/renames in Manage Data refresh the native tree. Reopening/reloading synchronises it from GeoPackage.
5. Quick New checks Save/Discard/Cancel before creating anything. Queued refreshes are guarded on unload; attach/detach pairs all signal connections. Map view state saves with native QGIS Save Map; data-record changes save immediately.
6. Run `scripts/check.ps1`. `default_workspace_test.py` checks the known location, no-form action, collisions, full multi-client/field/season tree, zero-feature native queries, selection, edit protection and cancellation. It also runs from the extracted ZIP, alongside lifecycle, legacy farm and hierarchy tests.

Managed providers use `option:NOLOCK=NO` in their native OGR URI. In QGIS 3.44 this also prevents a write from automatically switching to WAL while existing pooled readers were opened in nolock mode. This resolved database-query failures during add/rename and field changes in the installed GUI. Filters use native subset strings; layer IDs/styles stay intact. No separate GIS runtime or global QGIS/GDAL configuration is introduced. Existing schema 2 data requires no migration. The default-workspace test fails on any native GDAL error, including errors emitted during map saving.

Implementation references: [QGIS 3.44 OGR open/WAL handling](https://github.com/qgis/QGIS/blob/final-3_44_14/src/core/providers/ogr/qgsogrproviderutils.cpp#L941) and [GDAL GeoPackage open options](https://gdal.org/en/stable/drivers/vector/gpkg.html#dataset-open-options).

## Data In — 0.7.0

The interface is `import_dialog.py`; local adapters and provider probing live in
`import_sources.py`. Scanning runs in a cancellable `QgsTask`; only its completion
callback touches widgets. Unload closes the dialog, detaches callbacks and cancels
active work. Native OGR/GDAL provider metadata discovers sublayers; native
QgsVectorLayer/QgsRasterLayer open selected sources. This avoids treating a
filename extension as proof of readable data. Vectors are read-only and existing
provider/source pairs are skipped. No farm schema changes or external GIS runtime
are involved. Future cloud adapters should produce the same plain preview records
without mixing account handling into the local scanner.

Run `scripts/check.ps1` for source and extracted-ZIP checks, including
`data_in_test.py`: real multi-layer GeoPackage/GeoJSON/raster/ZIP discovery, unsafe
archive rejection, Deere hierarchy, scan limits/cancel, async UI, duplicate
handling, read-only vector opening and close/reopen cleanup. See IMPORTS.md and
the bundled USER_GUIDE for the farmer workflow and current storage limitations.

## Import destination transactions

Field placement uses native PyQGIS geometry operations, transforms and layer-tree
APIs. Creating a new Organisation/Client/Farm/Field path must be atomic. The
verified QGIS 3.44 OGR provider connection does not retain SQL transaction state
across executeSql calls, and QgsTransaction.create(database, 'ogr') returns None.
For these attribute-only hierarchy rows, the import service uses Python's bundled
sqlite3 transaction with bound values, as the hierarchy service already does for
metadata reads. It performs no geometry, GeoPackage spatial or conversion writes
through sqlite3 and introduces no additional dependency or separate GIS engine.

## Proposed intelligent data types

See [Intelligent data handling](DATA_TYPES.md) for the next Data In design:
representation versus farming purpose, shared type registry, bounded native
metadata inspection, explicit measurement/units/date mapping, raster handling,
classification independent of field matching and staged storage work. This is a
design proposal; runtime classification/styling is not implemented by this note.

## Offline Windows release tooling — Ag-GIS 0.8.1

Native capabilities reused: the official standalone QGIS MSI supplies the complete supported GIS runtime; QSettings enables the user-profile plugin; QGIS's native plugin manager owns ZIP installation, compatibility checks and reload. A small in-plugin runner opens private GitHub releases in the user's authenticated browser and offers native ZIP installation. No tokens, anonymous private-feed assumptions, pip packages or second GIS engine are bundled.

1. Download the unmodified `https://download.qgis.org/downloads/QGIS-OSGeo4W-3.44.14-1.msi` to `dist/vendor/`. The pinned SHA-256 is `0a579f980dcec85be2ecb47c5f08234ca6ce7b625c3cb9543eded1f43d445b46`, from Microsoft's upstream WinGet manifest for OSGeo.QGIS_LTR 3.44.14. Verify the OSGeo Authenticode signature too.
2. Run `& 'C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat' tools/build_windows_installer.py`. It captures selected source/docs/tools, records Git HEAD plus hashes (including current uncommitted work), and compares before/copy/after bytes to reject an unstable capture. No repository commit/reset or live profile mutation is performed.
3. All required source checks and extracted-ZIP workflow checks run inside that snapshot. Installer checks exercise a new temporary profile, exact extracted bytes, stale-module removal, upgrade backup, rollback on settings failure, malicious archive rejection and unrelated-plugin protection. The real Qt updater dialog checks download, ZIP and cancellation branches with browser/installer boundaries substituted; no live release is claimed by those checks.
4. The Windows .NET Framework C# compiler builds `Setup.exe`. It invokes Windows PowerShell as the original user; only the QGIS MSI asks for elevation. Existing QGIS processes block setup. Recovery copies live in the target profile, independent of this checkout. The bundled profile installer stages and verifies a replacement before swapping, and recovers the previous plugin/settings on failure.
5. Output is a timestamped offline ZIP under `dist/windows`, with its SHA-256 beside it; the staging directory contains the immutable source, validation log and extracted installer. `manifest.json` records every bundled payload hash. The plugin ID stays `ag_tech_tooling` after the Ag-GIS display-name change. Existing data paths stay stable.
6. Private release target: `https://github.com/JamRov/Ag-GIS`. Publish the tested snapshot source, plugin ZIP, offline installer and checksum together. Users need private repository access; browser authentication handles downloads. Live private download/update and clean-machine installation remain separate acceptance checks. Never embed an access token in a plugin, archive, feed URL or Git remote.
7. Cleanup only obsolete generated files after a validated replacement; record each absolute path, old SHA-256 and replacement evidence in `dist/windows/cleanup.json`. Keep `dist/install-backups`, farm datasets and source. Keep snapshots required to reproduce the shipped artifact.


## Published Ag-GIS 0.8.1 — 15 October 2026

Private release: https://github.com/JamRov/Ag-GIS/releases/tag/v0.8.1 . Download Ag-GIS-0.8.1-Windows-20261015T003810Z.zip (583,391,412 bytes), extract ALL files, save/close QGIS, then run Setup.exe as the normal user. SHA-256: `0d74f1f65960ba441aed03790952e0eb313baba6443ec981c38acb663cfa5157`.

The in-plugin Check for Updates runner opens the private releases/latest URL in the user's signed-in browser, then delegates ZIP installation to QGIS. Private repository access is required. Existing farm paths and the internal ag_tech_tooling ID remain stable after the Ag-GIS rename.

Source and extracted-package PyQGIS tests passed on the recorded source. Windows assembly run https://github.com/JamRov/Ag-GIS/actions/runs/38661044397 verified the identical source/plugin package, official QGIS MSI signature/checksum and offline bundle before uploading. Release tag v0.8.1 points to tested source commit 3f1f4ed000b5b5af9d01f308f7238f74494fd83d. Packaging reused those exact-input plugin tests; QGIS was not installed on the hosted runner.

Downloaded the published plugin and full installer through the current authorized browser account: plugin bytes, installer SHA-256/CRC, all payload hashes, VerifyOnly and the compiled launcher's open-QGIS refusal passed. Clean-machine Windows MSI wizard/UAC/reboot and another authorized user's install/update remain pending. The launcher is unsigned.

Local published archive: `dist/windows/Ag-GIS-0.8.1-Windows-20261015T003810Z.zip`; extracted launcher: `dist/windows/published-0.8.1/Ag-GIS-0.8.1-Windows/Setup.exe`. Fifteen obsolete generated files were removed (about 1.75 GB); source snapshots, recovery backups and farm data were retained. Exact cleanup paths/hashes and published-download evidence are in local ignored dist/windows/cleanup.json and published-verification.json. Newer in-progress feature edits remain in the shared local checkout and are excluded from this tested release.


### Repeat hosted assembly for a future tested draft

1. First run the full source and extracted-plugin checks using QGIS Python and retain a recorded source snapshot plus validation.log. Commit that exact snapshot; upload its matching plugin ZIP and validation.log to an unpublished draft.
2. Open Actions → Assemble verified Windows installer → Run workflow. Supply the existing draft release ID and immutable tested source commit. The job preserves source bytes, verifies every source hash and ZIP entry, downloads/signature-checks the pinned official MSI, compiles/packages the launcher, verifies hashes/CRC and attaches the offline ZIP/checksum to that draft. It uses only the ephemeral repository-scoped Actions token.
3. Check the entire workflow succeeds and the assets are uploaded; publish the draft pinned to the tested source commit. Download the released artifacts and verify their checksums and payloads. A packaging pass reuses the existing exact-input plugin tests; it is not a new clean-machine acceptance test. A failure leaves the draft unpublished. The current workflow expects the 0.8.1 plugin asset name; update that filename when preparing another version.
4. Local packaging-only rebuilds may pass `--source-from dist/windows/<validated-build>/source --validation-from dist/windows/<validated-build>` to tools/build_windows_installer.py. Reuse rejects changed plugin/test/installer-Python inputs; only the builder and C# launcher may differ, and final launcher/package checks are still required. Run without reuse after any runtime/test change.
