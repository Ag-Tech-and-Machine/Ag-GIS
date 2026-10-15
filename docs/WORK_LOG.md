# Work log and verification status

## 15 October 2026 — Semantic icons in the left browser, 0.8.0

- Added farm-browser presentation over the existing QgsLayerTreeView, using the same Organisation/Client/Farm/Field/Season/Crop icons as Manage Data and distinct Whole Field/Plans/Operations/Results icons. Increased icon/row sizes, reduced indentation and added type/name tooltips. The panel is titled Farm Data for farm workspaces.
- Preserved the native model, selection, map symbols, visibility/editor handling and unrelated group/layer rendering. Plugin unload restores the original delegate/spacing/title and removes signal connections.
- Added a real Qt/PyQGIS presentation test covering icon identity, actual visibility clicks, native rename editor commit, unrelated layers, project changes and repeated restore/reapply. Source and extracted-ZIP checks passed, including the ongoing import-workstream checks.
- Verified exact source/package/installed bytes for 0.8.0. The installed files include the delegate and four new semantic SVG assets; the packaged guide is current. Existing QGIS settings/project files were retained.
- Verified the installed plugin in a separate native QGIS review profile: every hierarchy type had its icon, the Farm Data title/spacing applied, only the map/browser remained in Simple view, and unload/reload restored and reapplied the native delegate/title correctly. Captured and inspected the actual QGIS browser. The disposable review workspace was removed and that helper process exited.
- The user subsequently requested stopping the NAS scan and restarting. QGIS exited as the scan dialog was cancelled, before the map could be saved. Retained a copy of the last saved QGZ and reopened that saved map; previous unsaved map changes could not be confirmed as saved. The normal-profile restart check passed: Farm Data title/delegate/icons active, three valid map layers and no scan dialog. The saved QGZ remained byte-identical during verification; normal QGIS is open in Simple view.

## 15 October 2026 — Default workspace and full native tree, version 0.6.0

- Replaced the main New Project setup form with one-click generation in system Documents/Ag-GIS/Projects. Uses a free My Farm Data numbered folder and preserves existing destinations. Generates Organisation 1, Client 1, Farm 1, Field 1 and Season 1; no crop, dates or geometry are invented. Explicit setup remains menu-only.
- Reused Qt's known Documents location, native QGIS project/layer/provider/writer APIs, native layer tree groups and shared field-filtered layers. No schema bump or data migration is required. The workspace retains Farm.qgz plus Data/farm.gpkg.
- Native Layers now displays every organisation/client/farm/field/season at its own short level, with Whole Field and Seasons per field. Selecting a field switches the three shared reference views; Manage Data adds/renames records and refreshes the tree. Unrelated data and active edit sessions are protected.
- Fixed proxy-model selection mapping using QgsLayerTreeView.index2node. Traced database errors to native QGIS journal-mode transitions while pooled readers remained open. Managed native providers now carry option:NOLOCK=NO to prevent automatic WAL promotion on writes. Filters remain native subsets. Earlier staging-path and subset-only hypotheses did not resolve the issue; no cache-reset or SQLite-copy workaround remains.
- Added default-workspace checks for known location, missing Documents recovery, no-form creation, numbered collisions, saved multi-client hierarchy, empty reference queries, field navigation, edit-session refusal, cancellation and signal lifecycle. Checks also run against the extracted package. The completed Deere preview component is included and its synthetic checks are now part of both suites.
- Created the Ag-GIS sidebar section and moved both chats into it; renamed the main chat to Ag-GIS — Interface and Farm Structure. This groups chats visually. Saved local Project registration remains pending because the available app tools do not expose its creation.
- Updated the canonical installation, tooling, data-model and bundled user instructions. The data-import chat added Data In during integration; the combined tested/installed release is 0.7.0.
- Final source and extracted-ZIP checks passed on QGIS 3.44.14, including native-error-free default creation/navigation/save, lifecycle, legacy farm protection, schema 2 hierarchy, eight Deere preview cases and Data In discovery/cancellation/map linking. The invalid-parent hierarchy test deliberately emits a provider rejection.
- Installed 0.7.0 in the default profile, preserving the previous plugin/settings. Live GUI verification passed: a two-client disposable workspace navigated correctly, all three empty reference layers queried, unload/reload retained one toolbar, and the actual New Project action created and saved the real starter at C:\Users\Michael\Documents\Ag Tech Tooling\Projects\My Farm Data. Only Layers was visible beside the map; all nine toolbar buttons had icons. QGIS remains open there in Simple view. Live report and screenshot are exported with the guide/package.

## 15 October 2026 — Hierarchy and icon-labelled management, version 0.5.0

- Implemented Organisation → Client → Farm → Field, Season/Crop records and Whole Field/Seasons management grouping in GeoPackage schema 2, using native QGIS layers/writers/providers.
- Added Manage Data to the top toolbar, with persistent add/rename, parent-aware controls and field selection. Added icons to input lines, dialog buttons and all tree rows, and larger 28-pixel toolbar icons. Bundled six semantic SVG icons with QGIS theme/fallback support.
- Added native shared Boundaries/Guidance/Infrastructure layers filtered by field, retaining unrelated map data and stable workspace identities after move/reopen. Seasonal dataset, terrain, job and history tools remain future work; category rows do not represent implemented editors.
- Added separate-copy schema 1 upgrades with confirmed Organisation/Client names, consistent SQLite database snapshot, native schema updates, validation, original-file preservation and failed-stage cleanup. Reserved table conflicts and existing/nested destinations are refused.
- Foundation tests exercise persistence, duplicate names across clients, invalid parent rejection through a native provider, date validation, rename links, UI add/cancel, every row/button icon, native field filtering and move/reopen without duplicate layers. Copy-upgrade tests compare original file hashes and verify ID/supporting-file retention and failure cleanup.
- Updated canonical/bundled setup and operating instructions. Syntax/metadata, source lifecycle/farm/hierarchy checks, ZIP build and the same workflows against the extracted ZIP all passed on QGIS 3.44.14. The expected invalid-parent test emits a provider rejection and is asserted as a passing protection check.
- Installed 0.5.0 in the default profile, with prior plugin/settings backups. Actual QGIS GUI verification exercised New Project, Add Client/Farm/Field/Season/Crop dialogs, native Show Field and Save Map. Verified eight toolbar icons, 28-pixel sizing, all tree-row/button/input icons and Simple view. Captured and visually inspected the hierarchy and new-project dialog.
- Live verification used a temporary workspace, cleared it and removed its test data afterward. QGIS remains open with an empty map. Existing user projects were not migrated or changed. The first live test needed a timing adjustment to wait for the management dialog after project creation; this affected the verification harness only.

## 15 October 2026 — Four-level hierarchy confirmed

- User selected Organisation → Client → Farm → Field from the outset, superseding the earlier three-level default and deferred Client suggestion.
- Updated the model, developer rules and linked documentation: distinct Client entity, explicit parent relationships, same-name isolation, dependent selectors and confirmed ownership for migration. Whole Field/Seasons remains beneath Field.
- This records the agreed design only. Plugin 0.4.0 and schema version 1 remain unchanged; no runtime controls, access-control system or migration were implemented.
- Documentation diff check passed; unchanged runtime tests were not repeated.

## 15 October 2026 — Whole Field and seasonal data

- Recorded the user's direction to divide each field into Whole Field reference data and crop/season data.
- Documented master guidance lines, boundaries, terrain and infrastructure under Whole Field; plans, operations, observations and results under Seasons. Proposed handling for multiple crops/cycles and revision references preserves history without copying fields annually.
- Kept the toolbar/map-and-Layers interface priority. This is a model clarification only: installed plugin 0.4.0 and schema version 1 remain unchanged.
- Documentation diff check passed; no unchanged runtime tests were repeated.

## 15 October 2026 — Organisation/Farm/Field research

- Reviewed primary Deere, Ag Leader SMS and PTx FarmENGAGE documentation for organisation/client/grower/farm/field models, task/time views and unit preferences.
- Documented a proposed Organisation → Farm → Field interface, optional Client/Grower handling, stable identities, boundary revisions and separate season/job relationships. Proposed multi-farm organisation workspaces revise the earlier one-farm packaging illustration.
- Kept the installed 0.4.0 plugin and schema version 1 unchanged. No migrations, imports, production datasets or new hierarchy controls were created.
- Confirmed the live QGIS accessibility tree contains the dedicated toolbar and seven controls. The 0.4.0 installed-build capture shows native icons above their labels; fresh Windows screenshot capture timed out, so the capture is prior verification evidence, not a fresh screenshot.
- Reviewed documentation with `git diff --check`; unchanged plugin integration tests were not repeated.

## 15 October 2026 — Dedicated farmer toolbar, version 0.4.0

- Added the top Ag-GIS toolbar with labelled New Farm, Open Farm, Save Map, Move Map, Zoom In, Zoom Out and Whole Map buttons. New/Open share plugin-menu actions; save/navigation share native QGIS actions and enabled/checked states.
- Kept labels local to toolbar buttons, including when native QAction state/text changes. Toolbar is fixed at the top; no placeholder import/export/conversion controls were added.
- Simple view now keeps our toolbar instead of native Project/Navigation bars, plus map and Layers. Full-view restoration remains available. Toolbar is removed on unload, with native actions retained.
- Updated packaged user instructions and development guidance. Verification and installation results follow below.
- Source and extracted-ZIP checks passed on QGIS 3.44.14 for toolbar placement, seven labels, shared native save action, stable button labels after QAction changes, Simple view visibility, layout restoration and unload/reload without duplicate toolbars. Existing farm workflow tests also passed.
- Installed 0.4.0 in the default profile; the installer retained backups of the previous plugin/settings.
- The first live startup check exposed native toolbar restoration after Simple view applied. Added toolbar visibility guards and dynamic registration; source/extracted-package checks now cover attempted reopening and toolbars added later.
- Final live QGIS verification passed: all seven native icons/labels, top placement, shared native action identity, zoom/pan activation, native save, toolbar visibility restrictions, full-view toggle, farm identity/CRS and New Farm dialog/cancellation. Captured and inspected the toolbar; QGIS remains open in Simple view. Tests used disposable farm data only.

## 15 October 2026 — Interface-first priority confirmed

- Recorded the user's requirement to optimise the interface as priority one and use native QGIS tooling wherever possible.
- Updated AGENTS.md, purpose and development guidance to prioritise clear task flows, existing QGIS controls and reversible Simple view behaviour before feature expansion.
- Identified discoverable New/Open Farm controls as the next interface increment; no placement change has been implemented yet.
- Documentation-only change, reviewed with `git diff --check`. Installed plugin remains 0.3.1; no runtime/package changes or repeated integration tests were needed.

## 15 October 2026 — Native QGIS writer and complete plugin package, 0.3.1

- Replaced direct OGR farm-table creation with PyQGIS memory layers/features and `QgsVectorFileWriter.writeAsVectorFormatV3`, using QGIS's bundled provider and transform context. Read-only SQLite structural checks remain; no GIS operations are implemented through SQLite.
- Bundled the canonical user guide in the plugin ZIP and required every runtime module/resource in package validation.
- Added exact archive-byte/content checks and source-independent tests against an extracted ZIP. Source and extracted-package lifecycle, farm creation, move/reopen and rejection checks passed on QGIS 3.44.14.
- Recorded the packaging and native-QGIS requirement in AGENTS.md and tooling instructions. Planned import/export/conversion features must use native providers, coordinate transforms and Processing as appropriate; they are not implemented yet.
- Installed 0.3.1 in the default profile and reopened QGIS. Live GUI verification passed for plugin startup, bundled guide, action registration, native farm creation/opening, correct identity/CRS and New Farm dialog cancellation. Simple view remained selected. Existing farm data was not modified.

## 15 October 2026 — GeoPackage farm foundation, version 0.3.0

- Added New/Open Farm Project under Plugins → Ag-GIS. Creation writes a registered GeoPackage attributes table for UUID, name, schema version, CRS and creation time, plus a matching companion map.
- Kept agricultural layers unspecified. Added destination protection, staged creation/cleanup, read-only preflight, matching identity/CRS/schema checks, invalid-layer rejection and unsaved/edit-session protection.
- QGIS 3.44.14 checks passed: syntax/metadata, existing Simple view lifecycle, actual GDAL/PyQGIS farm creation, real spatial layer move/reopen, duplicate protection, failed-creation cleanup, newer-schema rejection, dialog construction, edit-session protection and cancelled switch. ZIP build passed.
- Fixed a Windows file-lock failure found by the first portability test by explicitly closing SQLite validation connections.
- Installed and enabled 0.3.0 in the normal default profile, with the previous plugin/settings backed up by the installer.
- Verified the installed copy in the actual QGIS GUI: New/Open actions registered, a disposable farm opened with the correct title/CRS/identity, Simple view kept the map visible, and the actual New Farm dialog opened and cancelled. Captured and visually checked its layout. Removed only disposable test data and returned QGIS to an empty map.
- Updated setup, operation, purpose and data-structure docs. Imports/exports, editable settings, conversions, agricultural schemas, database integrity repair, comprehensive external-path packaging, multi-user locks and automated backup remain future work. Only QGIS 3.44.14 was tested.

## 15 October 2026 — GeoPackage direction confirmed

- Recorded the user's choice of GeoPackage as the core farm data format.
- Captured upcoming design areas: file/data structure, import/export setups, settings and conversion tooling.
- Kept schema, supporting file layout, project storage and supported formats explicitly undecided. No data-management code or datasets changed.
- Reviewed documentation changes with `git diff --check`; unchanged plugin tests were not repeated.

## 15 October 2026 — Farm project structure proposal

- Documented a proposed directory per farm, with QGZ map setup, GeoPackage records, supporting data and job-specific work.
- Compared GeoPackage project storage with separate project/data storage; recommended a managed directory for mixed data and ZIP for transfer/backup.
- Defined planned import, path, schema, units, overwrite, local-editing and verified-restore controls, plus staged acceptance checks.
- Checked QGIS 3.44, OGC GeoPackage and SQLite primary documentation. No plugin code changed; integration tests were not repeated.
- Farm management remains proposed. No farm datasets were created, moved or modified. Next step: agree the initial structure and implement New/Open Farm Project.

## 15 October 2026 — Map and Layers only, version 0.2.1

- Restricted the Simple view primary workspace to the map and Layers, as requested. Browser, welcome/recent projects, news/templates and other dock panels are hidden.
- Guarded panel visibility: Layers remains available, other existing/new panels cannot reappear while Simple view is on.
- Found the map's central Qt page and kept it selected without creating, clearing or replacing the user's QGIS project.
- Preserved full-layout restoration. If the project changes while in Simple view, switching off leaves the map in front rather than returning to the old welcome page.
- Qt/PyQGIS checks passed for hidden/reopened/new panels, welcome-page exclusion, layout restoration, project-change handling and reload.
- Installed in the default profile; real-QGIS API verification confirmed a map-and-Layers workspace, hidden welcome page, Browser exclusion, unchanged layers and restoration. Captured and inspected the actual interface.

## 15 October 2026 — Simple view, version 0.2.0

- Added a single **Simple view** checkbox in the bottom-right status bar, alongside the existing scale/coordinate controls, as requested.
- Simple mode keeps Project and Map Navigation toolbars plus Layers/Browser, hiding advanced main-window toolbars and panels. QGIS menus and status controls remain available.
- Saved the previous full layout per profile and implemented restoration when the switch is turned off or the plugin is unloaded. The profile remembers the selected mode on reload/restart.
- Added Qt/PyQGIS checks for visibility, restoration of originally hidden panels, saved preference and removal of the switch during unload.
- Installed 0.2.0 in the normal default profile. Live QGIS API checks passed for control placement, essential controls, full-layout restoration, unchanged project layers and unload/reload with one visible switch.
- Restarted QGIS and verified that Simple view remains selected. Visually checked the bottom-right switch beside the coordinate, scale, rotation and CRS controls.
- Simple mode is enabled in the current QGIS session for review. This is interface simplification, not agricultural workflow automation.

## 15 October 2026 — Purpose and installed development foundation

- Recorded the purpose: build farmer-friendly, open-source tools that simplify agricultural workflows and automate GIS work.
- Added design principles in `PURPOSE.md` and required them in project working instructions.
- Selected GPL-2.0-or-later, included the full license in source and the installable ZIP, and added SPDX identifiers to plugin source.
- Added repeatable installation scripts with profile-settings backups and protection against overwriting unrelated plugins.
- Installed and enabled version 0.1.0 in the normal QGIS `default` profile.
- Verified in a real QGIS 3.44.14 GUI session: installed-module path, automatic loading, toolbar action, layer-count message and plugin-manager unload/reload without duplicate toolbar actions.
- The source remains local; no public remote or release has been published. Farmer-specific automation has not yet been implemented.
- Ready for the first tool's task description, sample inputs and expected outputs.

## 15 October 2026 — Naming update

- Adopted the temporary project and displayed plugin name **Ag-GIS**.
- Renamed the repository folder to `ag-tech-tooling` and the Python plugin package to `ag_tech_tooling`, retaining Git history.
- Updated the menu/action title, metadata, development profile name, build names, scripts and instructions together.
- Re-ran `scripts\check.ps1` on QGIS 3.44.14: syntax/metadata, Qt/PyQGIS lifecycle and ZIP checks passed.
- Desktop sidebar registration remains pending; use **Ag-GIS** as the app project name and attach the renamed repository folder.

## 15 October 2026 — Initial development environment

### Completed

- Configured Git author Michael `<admin@agtechandmachine.com>` and default branch `main`.
- Created the local `ag-tech-tooling` repository and committed the starter.
- Installed QGIS 3.44.14 LTR using WinGet; installer hash verification and installation succeeded.
- Added source discovery through `QGIS_PLUGINPATH` and an isolated development profile launcher.
- Added syntax/metadata checks, Qt/PyQGIS smoke checking and ZIP packaging.
- Established installation, tooling and work-log documents, with upkeep required in `AGENTS.md`.

### Verified

- `scripts\check.ps1 -QgisRoot 'C:\Program Files\QGIS 3.44.14'` passed.
- The smoke check created the plugin through `classFactory`, exercised its action, prevented duplicate registration, and removed registrations on unload using real Qt/PyQGIS and an interface adapter.
- Plugin ZIP structure and integrity checks passed.
- Development launcher started the QGIS GUI and created the isolated profile.
- Git author matched the requested identity; repository integrity check passed.

### Pending

- Add the local repository to the desktop app's Projects sidebar and move the tooling chat into it. The repository exists, but the app's saved project list was empty when checked.
- Manual interaction with the plugin-manager checkbox and ZIP-install dialog, if those UI workflows need separate acceptance testing. Installed ZIP content, enabled startup, actual toolbar action and lifecycle are now verified via QGIS APIs in the normal profile.
- Definition of the first useful domain-specific tool.
- Remote Git repository and backup/publication workflow, if requested.
- Public project/support URLs before public release. GPL-2.0-or-later is now selected and packaged.

### Known setup findings

- Old QGIS 3.36 folders contained only remnants and were not usable runtimes.
- WinGet's command alias was absent, but its installed App Installer executable worked.
- Installing QGIS required the user to approve the Windows administrator prompt.

### Next step

Define and implement the first real farming workflow. Add its operating instructions and validation evidence with the implementation.

## 15 October 2026 - Deere GS3 import inspection foundation

- Added isolated, packaged `deere_preview.py` service and developer CLI; no shared
  hierarchy/schema or GUI changes in this workstream.
- Inspected the supplied NAS export read-only: five files, one client/farm/field,
  one curved-track resource. Before/after SHA-256 inventory confirmed unchanged
  source content. Reports and actual farm data remain outside Git.
- QGIS 3.44.14 native provider probing returned no sublayers for all five source
  files; curved-track binary geometry requires a verified decoder. No boundary
  or recorded operation files were present in this sample.
- Passed plugin syntax/metadata checks and QGIS lifecycle smoke check. Eight
  synthetic inspection tests passed against the extracted build package; the
  extracted module also inspected the live NAS sample successfully with no
  metadata issues and unchanged hashes.
- Development package built outside the repository; not installed into QGIS.
  No Import button, GeoPackage writes, ZIP source support, Deere decoder or
  season-data import is implemented. See docs/IMPORTS.md for next steps.

## 15 October 2026 - Data In local source dialog (0.7.0)

- Added icon-labelled Data In to the top toolbar and plugin menu. Choose File or
  Choose Folder starts automatic recursive discovery; pasted paths and NAS shares
  use the same entry point. Background QgsTask scanning supports stop/close/unload.
- Native QGIS OGR/GDAL providers discover vector/raster sublayers, including GIS
  members in ZIPs. No extraction is performed. Unsafe/encrypted/nested archives,
  inaccessible paths and scan limits receive explicit results/messages.
- Readable selections open as native linked map layers; vectors are read-only.
  Repeat adds skip existing sources, and the map refreshes/zooms. Originals are
  retained; managed GeoPackage copying is not part of this version.
- Deere exports preview machine-ID relationships and guidance catalogue metadata.
  The supplied NAS sample passed the new scanner: five files, one export,
  client/farm/field/curved guidance hierarchy, no warnings, unchanged SHA-256
  inventory. The rendered native Qt dialog was visually checked against it.
- Cloud adapters, decoder integration and managed import mapping remain next
  stages. The source/preview record contract leaves these separate from the UI.
- Verification completed: scripts/check.ps1 passed syntax/metadata, plugin
  lifecycle/Simple view, farm workflows, hierarchy/default-workspace checks,
  eight Deere metadata tests and Data In integration checks. All workflow tests
  passed again against the extracted 0.7.0 ZIP; exact packaged bytes matched
  source, including the bundled user guide.
- Built dist/ag_tech_tooling-0.7.0.zip. The active QGIS session was left running;
  installation/reload of this package remains separate from these verified checks.

## 15 October 2026 - Field-aware Data In (0.8.0)

- Replaced loose Add to Map with Import to Field. All source geometry must fit
  inside exactly one known field boundary for automatic assignment. Stored
  boundary features and previously assigned boundary layers are checked without
  the active field's display filter, using native QGIS geometry/CRS operations.
- Ambiguous, cross-field, empty/invalid/large or unlocated data prompts for the
  full Organisation/Client/Farm/Field path. Editable parent-filtered selectors
  reuse existing records or create new ones within their correct parents. Unknown
  CRS requires an explicit choice. Polygons may be designated as field boundaries.
- Destination prompts prepare plans without writes. Cancelling any prompt cancels
  the selected batch before additions; each new hierarchy path commits atomically.
  Attribute-only sqlite3 transaction justification is recorded in TOOLING.md.
- Linked sources now live under the selected field's Whole Field / Imported Data;
  field/role properties save with the QGIS map. Source attributes stay intact and
  vectors read-only. Re-importing an old loose layer relocates it without a copy.
- Complete source-file copying, per-feature multi-field splitting and season-data
  mapping remain future work. Native farm reference layers are not overwritten.
- Full scripts/check.ps1 passed against source and the extracted 0.8.0 ZIP,
  including real generic shapefile routing, batch-cancel protection, existing
  loose-layer relocation, CRS transforms, shared-name hierarchy separation,
  hierarchy rollback and field assignment/boundary matching after project reopen.
- Installed the verified 0.8.0 runtime files into the existing default profile,
  with a full plugin-directory backup and exact package/source byte checks.
  Settings and project files were not changed. The current QGIS session retains
  unsaved work and was not restarted; save/restart is needed to load this update.

## 15 October 2026 - Intelligent raster/vector handling design

- Reviewed current Data In code: native raster/vector discovery and field placement
  exist, but farming-purpose handling is limited to generic data and explicit
  polygon boundaries. Automatic field matches currently bypass the type prompt.
- Added DATA_TYPES.md with proposed shared type registry, native metadata profiling,
  evidence-based suggestions, value/unit/date prompts, native styles, farm/field/
  season scope, precision-safe raster storage evaluation and acceptance cases.
- Confirmed native capability references against QGIS 3.44 and GDAL documentation.
  This is design work only: no feature, dependency, installation or runtime change;
  no integration test rerun was needed. Implementation remains a next increment.

## 15 October 2026 — Ag-GIS installer and rename (implementation)

- User selected the name Ag-GIS and private GitHub destination JamRov/Ag-GIS. Display names, canonical docs and installer labels updated; internal plugin ID, source checkout path and existing farm-data paths retained for compatibility. Other chats' uncommitted feature changes are preserved.
- Added Windows offline setup launcher, hash verification, official QGIS MSI payload, staged per-user plugin installation with recovery backups, and in-plugin browser/private-release plus native QGIS ZIP update runner. No credentials are bundled. Version 0.8.1 identifies this installer/updater build.
- Official QGIS 3.44.14 MSI downloaded from QGIS: 583,143,424 bytes; SHA-256 matches pinned upstream WinGet manifest; Authenticode reports Valid with THE OPEN SOURCE GEOSPATIAL FOUNDATION signer.
- Source/extracted-package validation, bundle path, cleanup evidence and publication result will be recorded after the snapshot build. Clean-machine MSI wizard/UAC/reboot and live private-release update acceptance are not yet verified. Existing open QGIS session is not restarted or modified by packaging.


## Published Ag-GIS 0.8.1 — 15 October 2026

Private release: https://github.com/JamRov/Ag-GIS/releases/tag/v0.8.1 . Download Ag-GIS-0.8.1-Windows-20261015T003810Z.zip (583,391,412 bytes), extract ALL files, save/close QGIS, then run Setup.exe as the normal user. SHA-256: `0d74f1f65960ba441aed03790952e0eb313baba6443ec981c38acb663cfa5157`.

The in-plugin Check for Updates runner opens the private releases/latest URL in the user's signed-in browser, then delegates ZIP installation to QGIS. Private repository access is required. Existing farm paths and the internal ag_tech_tooling ID remain stable after the Ag-GIS rename.

Source and extracted-package PyQGIS tests passed on the recorded source. Windows assembly run https://github.com/JamRov/Ag-GIS/actions/runs/38661044397 verified the identical source/plugin package, official QGIS MSI signature/checksum and offline bundle before uploading. Release tag v0.8.1 points to tested source commit 3f1f4ed000b5b5af9d01f308f7238f74494fd83d. Packaging reused those exact-input plugin tests; QGIS was not installed on the hosted runner.

Downloaded the published plugin and full installer through the current authorized browser account: plugin bytes, installer SHA-256/CRC, all payload hashes, VerifyOnly and the compiled launcher's open-QGIS refusal passed. Clean-machine Windows MSI wizard/UAC/reboot and another authorized user's install/update remain pending. The launcher is unsigned.

Local published archive: `dist/windows/Ag-GIS-0.8.1-Windows-20261015T003810Z.zip`; extracted launcher: `dist/windows/published-0.8.1/Ag-GIS-0.8.1-Windows/Setup.exe`. Fifteen obsolete generated files were removed (about 1.75 GB); source snapshots, recovery backups and farm data were retained. Exact cleanup paths/hashes and published-download evidence are in local ignored dist/windows/cleanup.json and published-verification.json. Newer in-progress feature edits remain in the shared local checkout and are excluded from this tested release.
