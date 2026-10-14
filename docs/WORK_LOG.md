# Work log and verification status

## 15 October 2026 — GeoPackage farm foundation, version 0.3.0

- Added New/Open Farm Project under Plugins → Ag Tech Tooling. Creation writes a registered GeoPackage attributes table for UUID, name, schema version, CRS and creation time, plus a matching companion map.
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

- Adopted the temporary project and displayed plugin name **Ag Tech Tooling**.
- Renamed the repository folder to `ag-tech-tooling` and the Python plugin package to `ag_tech_tooling`, retaining Git history.
- Updated the menu/action title, metadata, development profile name, build names, scripts and instructions together.
- Re-ran `scripts\check.ps1` on QGIS 3.44.14: syntax/metadata, Qt/PyQGIS lifecycle and ZIP checks passed.
- Desktop sidebar registration remains pending; use **Ag Tech Tooling** as the app project name and attach the renamed repository folder.

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
