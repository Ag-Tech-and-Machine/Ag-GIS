# Ag-GIS — Public User Guide

**Farming in view · Built on open source tools**

Source and releases are public at https://github.com/Ag-Tech-and-Machine/Ag-GIS . Public downloads do not require repository membership. Public feedback remains at https://github.com/JamRov/Ag-GIS-Feedback/issues .

## Overview

Ag-GIS is a farming workflow tool built on QGIS and native PyQGIS. It manages farm data, seasonal boundaries, and operational records with full local data ownership. No login, no cloud subscription required for core functionality.

## Install

1. In QGIS, choose **Plugins → Manage and Install Plugins → Install from ZIP**.
2. Select `ag_tech_tooling-<version>.zip` and install it.
3. Under **Installed**, enable **Ag-GIS**. Restart QGIS when updating an already loaded version.
4. Find the Ag-GIS toolbar at the top. Its project/data controls are also under **Plugins → Ag-GIS**. No separate Python installation, pip packages or companion app is required.

The ZIP contains all runtime modules, native/bundled icon support, licence and this guide. Farm data is saved separately in your Documents folder.

## Connect your agent: describe a problem or idea

1. Copy the agent instructions from **Feedback → Connect your agent → Copy agent instructions**.
2. Paste into your own agent (Codex, Claude Code, Hermes or another file-reading agent), then describe the farming job in ordinary words.
3. Give access to source and synthetic examples only, not your farm-data folder. An external AI provider may process what you paste; check its privacy controls.
4. **Review the draft, destination and attachments before explicitly choosing to share.** Bugs/ideas go to `JamRov/Ag-GIS-Feedback`; proposed code changes go as PRs to `Ag-Tech-and-Machine/Ag-GIS` for maintainer review. Nothing is sent by Copy.

Close to cancel. This reads the bundled guide locally; no account or agent connection is made.

## First farming workflow

Prerequisites: Ag-GIS enabled, a writable local Documents folder and a small supported dataset you can safely test. Finish layer edits and save any current map first. Use a separate test workspace, not your working farm, when trying this out.

1. Click **New Project**. A new numbered **My Farm Data** folder opens; existing folders are preserved.
2. Click **Manage Data** to rename Organisation 1, Client 1, Farm 1 and Field 1. Each rename saves immediately. Organisation is the managing business; Client is the grower, even if both have the same name.
3. Click **Data In**, then **Choose File**. Review Data, Type, Destination and Status. If the field has no boundary, choose its destination yourself; a missing automatic match is not an import failure.
4. Check only the wanted rows, confirm their destination and click **Import to Field**. Expect **Saved** and a copy under **Whole Field → Imported Data**. Original files stay where they were. Closing before import adds nothing; stopping during saving retains earlier completed imports.
5. Select the dataset in **Farm Data** to view it. Use **Whole Map** for the farm-data extent, not the worldwide background. Use **Filter Data → All fields / All data types** if a filter hides a dataset; also inspect its visibility checkbox.
6. Click **Save Map**. Finish and save layer edits separately before switching projects. Reopen with **Open Project → your project folder → Farm.qgz**; the existing **Data/farm.gpkg** route also works. Expect the saved hierarchy, managed datasets and map presentation to return.

Keep the complete workspace together, including Farm.qgz, Data and supporting files. If opening reports missing files, restore the complete workspace from a verified backup; do not create an empty replacement database or change its schema version.

## Keep your saved map styling

1. Edit a managed dataset using native layer styling, then click **Save Map**. This build saves a separate recovery snapshot of that native style, without changing original source data or the import-style record.
2. Reopening normally keeps the map's own styling. Reconstructing a missing managed layer from the catalogue uses the last successfully synchronized style, including deliberate reset results after saving. No new style or reset buttons are added.
3. If **Saved styling** reports a storage/conflict warning, preserve Farm.qgz and the complete workspace for review: recovery may have older styling than the map. Duplicate map copies or older/external saves are not silently chosen as winners. Do not delete style history to suppress the warning. Conflict-resolution controls and complete dependency/backup handling are not implemented.
4. Keep external symbols/fonts and other required assets. Unsaved edits, edits saved with older builds, and interrupted map/metadata writes are not guaranteed by this snapshot. Original fields, raw units and reviewed job history are unchanged.

## Browse Farm Data

Select datasets to view their records. Use filters to narrow by field, data type, or status. The whole map shows the farm-data extent, not the worldwide background.

## Review and apply season date changes (development build)

1. Open your workspace, choose **Manage Data**, and select the season immediately before the boundary under your field's Seasons. Choose **Preview Season Boundary…**.
2. Choose its proposed last day. The next season starts the next day. Compare the saved/proposed dates and each job's **Recorded season (kept)** against **Would match by date**. Whole Field/unreviewed data are excluded, not guessed.
3. **Close** leaves everything unchanged. To save the two dates, tick **I reviewed the job impacts: keep all jobs in their recorded seasons**, choose **Apply Both Dates…**, then confirm. Cancel is the default and changes nothing. The two dates and a keep-history audit save immediately; no additional Save Map is needed. Every job stays in its recorded season, including jobs whose dates now match a different season. Reassigning historic jobs is not available in this build.
4. Incomplete dates, gaps/overlaps, stale reviews or changed history refuse the edit. Close/reopen to review again. Applying requires reviewed original job files to remain available locally at their saved locations and match their original hashes. Restore them if missing; do not delete history to bypass a refusal. Reviewed .vrt virtual sources cannot authorize Apply in this build because their XML hash does not verify referenced data; keep the preview read-only. If storage is busy, finish other writes and retry a fresh review. Failed paired writes leave both dates unchanged. To reverse an applied boundary, review and confirm a new change; the earlier audit decision is retained.

## Privacy and data control

- Farm data is stored locally in your Documents folder.
- No cloud backup, synchronisation or hosted workspace is provided.
- External platform IDs are stored separately from internal UUIDs.
- Import matching distinguishes IDs, names and geometry; unresolved or conflicting matches are shown for review.
- Export presets explicitly map Organisation/Client/Grower/Farm/Field terms and report unsupported content.

## Background choices

This replaces the earlier single-background setup. New and existing farm maps include an expanded **Background** group beneath Farm Data.

1. Expand **Background** in the left panel if needed. Click a map name to select it, or tick **Roads — OpenStreetMap**, **Imagery — Esri World Imagery**, **Satellite — Australia 2025 (30 m)** or **Satellite — World 2016–17 (10 m)**. QGIS turns the other background off, keeping your farm layers above it. Untick the selected background for a plain map. No extra panel or plugin is required. While the map redraws, **Changing background…** covers the old image until the new choice is ready.
2. **Save Map** retains the checkbox choice. Turning the Background group off hides it; ordinary reopening respects existing checked/removed layers. Explicitly selecting a removed choice in View Settings restores it.
3. In **View Settings**, the same four options plus No automatic background are available. Tick **Also use these defaults for new projects** to start future workspaces with your preferred background.
4. The Australian satellite layer is a 2025 annual Landsat cloud-free composite from Digital Earth Australia at 30 m resolution. The worldwide layer is historical EOxCloudless Sentinel-2 imagery from 2016–17 at 10 m resolution. Their years/resolutions are in the layer names; neither is live or detailed aerial photography. Zooming closer does not add detail.
5. Esri World Imagery supplies worldwide aerial/satellite imagery with location-dependent detail and capture dates; it is not live or survey-grade. Existing maps receive this new choice unchecked without changing the saved selection, hidden groups or removed old options. Its credit links to Esri's official item and terms; no claim of an open-data licence or universal reuse permission is made.
6. All require internet access; visible tile requests reveal the requested map area to the selected provider. Credits switch with the selected background and appear in native canvas image exports; add required credit in print layouts and check permitted use before distributing imagery. No bulk/offline imagery download is provided. Outside Australia, choose Esri, World or Roads.

These providers require no API key for the supplied services. Offline work on local farm data remains possible with the background disabled.

## Updating Ag-GIS

1. Choose **Plugins → Ag-GIS → Check for Updates…**. Review your installed version and channel, then choose **Check now**. Checks are manual by default; background checks require your permission and never install an update automatically.
2. Read the available version, changes, compatibility and any data-upgrade warning. **Preview** is for explicit testing; the default **Stable** channel does not offer experimental packages. A connection error or missing catalogue means update information is unavailable, not that your installation is current.
3. Download a compatible offered update. Finish layer edits and save your map before confirming installation. Ag-GIS verifies the ZIP, retains a recovery copy of its plugin files and delegates installation to QGIS. Cancel or retry a failed download without changing the installed plugin.
4. Follow the native installation result and restart QGIS. The next load checks the installed version against the attempted update. A recovery copy protects plugin files only, not farm records; reverting software cannot undo a data-format change.
5. Offline ZIP selection remains available. Read its authenticity warning and use official packages: archive checks alone cannot identify the author of an arbitrary file.

Update checks contact GitHub, which receives connection metadata including your IP address; no farm files or project paths are included in the request. No paid account is required. Existing farm folders keep their location.

**Development status:** the approved catalogue is intentionally empty locally and this change has not published it. The new updater is not automatically present in older installed builds. See UPDATES.md in the source documentation for delivery and recovery details. Local source changes are not automatically part of a public download.

## Native QGIS foundation

Layer/table creation, hierarchy writes, constraint SQL and map layers use PyQGIS and QGIS's bundled providers/writers. Qt comes through qgis.PyQt. Python SQLite performs read-only structural queries and the storage snapshot during a copy upgrade. All actual GIS data/schema changes use QGIS.

Managed imports of supported native vector and raster data, map/browser settings and hierarchy editing are implemented. Complete portable export, conversion tools, seasonal dataset editors, automated history/backup and multi-user editing remain under development. The workspace still requires both QGZ and GeoPackage plus any referenced supporting files.

## Farmer view defaults

1. Create a project with **New Project**. Organisation, Client, Farm, Field and Season are ready in Documents; an **OpenStreetMap** background is already saved in the map. Existing farm maps receive the background on their first open with this version.
2. Select a farm/field in **Farm Data**. Other branches and their visibility checks stay unchanged. A field with mapped data can zoom when the Map & Browser Settings zoom option is enabled; disable that option to keep the map extent fixed while browsing. Selecting a dataset does not tick it on or clear a deliberate filter; only an already-visible dataset can auto-zoom. Use individual field checkboxes for independent visibility; visibility ticks (mouse or Space) do not zoom the map. With Filter Data set to All fields, shared All Fields native reference layers show features only from checked field/Whole Field branches, including parent-group visibility; their own layer checks are preserved. No features are deleted. Choose a specific field with Filter Data to edit native references; that deliberate filter remains separate from browsing.
3. Imported filenames start with spaces and a short label (up to 48 characters). Hover for the original full name. Use QGIS Rename or the panel's pencil button to choose your own label. Saved dataset renames update the GeoPackage catalogue; Save Map retains the map presentation. Source filenames and table names do not change.
4. Use the panel's **Add farm item** (+) menu. Select its parent, then choose Organisation, Client, Farm, Field, Season or Crop. Enter a name; Season also offers optional dates. Cancel leaves the data unchanged. Names save immediately to GeoPackage. Select an item and use the pencil button (or native Rename/F2) to rename it. Fixed headings such as Whole Field and Seasons stay fixed.
5. Plain default symbols start as green points, clear lines and light polygons; boundaries have an outline without fill. A newly prepared single-point dataset uses a readable 2 mm marker; multi-point datasets retain the compact 0.65 mm starting theme. This does not resize an existing saved map or custom-sized/source-authored marker. Thematic renderers and shaped/custom-sized symbols are retained. Raster pixel values and native raster styling are retained. Use native QGIS Layer Properties/Symbology for your own colours, sizes and thematic maps. Defaults apply once; later names/styles are preserved. The original starting vector style is retained in the map's layer custom properties.
6. Choose **View Settings** on the top toolbar (also Plugins → Ag-GIS → Map & Browser Settings). Override branch focus, selection zoom, starting names/symbols and background for this map. Tick **Also use these defaults for new projects** to change future setup. Cancel changes nothing. Save Map retains this map's overrides. Existing custom names/styles are not reset by this dialog.
7. Current background choices are **Roads — OpenStreetMap**, **Imagery — Esri World Imagery**, **Satellite — Australia 2025 (30 m)**, **Satellite — World 2016–17 (10 m)** and no automatic background. You can uncheck/remove backgrounds directly; ordinary reopening respects that choice. Use the native Data Source Manager for your own licensed imagery.

OpenStreetMap is an online road/place map, not aerial imagery. Internet access is required; normal QGIS HTTP caching is used and no offline/prefetch tool is provided. Attribution is visible on the map and drawn into native canvas image exports. For print layouts, include an attribution label using the background layer's rights metadata. Google tiles are not bundled as an unlicensed URL; Nearmap needs a subscription. Background service availability and coverage are outside the plugin.

## Toolbar and Simple view

- New Project / Open Project / Manage Data: project setup and data hierarchy.
- Save Map: native QGIS Save Project. Save layer edits through QGIS before switching context.
- Move Map / Zoom In / Zoom Out / Whole Map: native QGIS navigation and full extent, with native enabled/checked states.
- Simple view at the bottom right: keeps our toolbar, map and Layers. Turn it off to restore the full interface. In full view, recover a hidden toolbar through View → Toolbars → Ag-GIS.

Toolbar buttons have larger icons and text labels. Hierarchy rows, grouping rows, dialog buttons and input lines have icons. We use QGIS theme icons and bundled vector icons without changing global QGIS icon settings.

## Feedback and help

Use **Feedback** on the toolbar to report a problem, suggest an improvement or ask for help. Fill in the summary/details, then review the report. **Open GitHub form…** prepares a report for you to review and submit; keep its issue number to follow progress. Long reports are copied for pasting in full. You can also **Save report**, **Copy report** or open an **Email draft** if you do not use GitHub. Save before exiting/reloading QGIS. No farm files, map names, paths, account details or logs are collected automatically; app/QGIS/system versions can be unticked. Do not share private farm information, credentials or original datasets. Public GitHub issues are readable by everyone; private issues require access. A saved/email draft is not tracked until support creates an issue.

Whole Map and post-import zoom use native coordinate-aware extents of the farm datasets, excluding the world background. A new empty map starts at its coordinate system area of use (worldwide for a global CRS); selecting mapped field data zooms in. Existing saved map extents are retained.

## Current release and development state

Use a release's exact source/tag when reproducing its behaviour. The latest published installer and the active development checkout can differ. A feature mentioned in a roadmap is not necessarily implemented, tested or available for purchase. Read release notes and WORK_LOG.md for verification limits.

Optional cloud backup, mobile access, synchronisation and hosted workspaces are future candidates, not currently supplied paid services. Local data ownership/control and honest communication govern these plans. See USER_COMMITMENTS.md when present in the source version you are using.
