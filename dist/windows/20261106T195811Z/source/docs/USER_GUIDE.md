# Current repository status — 15 October 2026

**Farming in view · Built on open source tools**

Source and releases are public at https://github.com/Ag-Tech-and-Machine/Ag-GIS . Public downloads do not require repository membership. Older private-repository instructions below describe the earlier setup. Public feedback remains at https://github.com/JamRov/Ag-GIS-Feedback/issues .

# Ag-GIS — user guide

## Review and apply season date changes (development build)

1. Open your workspace, choose **Manage Data**, and select the season immediately
   before the boundary under your field’s Seasons. Choose **Preview Season Boundary…**.
2. Choose its proposed last day. The next season starts the next day. Compare the
   saved/proposed dates and each job’s **Recorded season (kept)** against **Would
   match by date**. Whole Field/unreviewed data are excluded, not guessed.
3. **Close** leaves everything unchanged. To save the two dates, tick **I reviewed
   the job impacts: keep all jobs in their recorded seasons**, choose **Apply Both
   Dates…**, then confirm. Cancel is the default and changes nothing. The two dates
   and a keep-history audit save immediately; no additional Save Map is needed.
   Every job stays in its recorded season, including jobs whose dates now match a
   different season. Reassigning historic jobs is not available in this build.
4. Incomplete dates, gaps/overlaps, stale reviews or changed history refuse the edit.
   Close/reopen to review again. Applying requires reviewed original job files to
   remain available locally at their saved locations and match their original
   hashes. Restore them if missing; do not delete history to bypass a refusal.
   Reviewed .vrt virtual sources cannot authorize Apply in this build because their
   XML hash does not verify referenced data; keep the preview read-only.
   If storage is busy, finish other writes and retry a fresh review. Failed paired
   writes leave both dates unchanged. To reverse an applied boundary, review and
   confirm a new change; the earlier audit decision is retained.


Version 0.12.2. Requires QGIS; tested with QGIS 3.44.14 LTR on Windows.

## Install

1. In QGIS, choose Plugins → Manage and Install Plugins → Install from ZIP.
2. Select ag_tech_tooling-0.12.2.zip and install it.
3. Under Installed, enable Ag-GIS. Restart QGIS when updating an already loaded version.
4. Find the Ag-GIS toolbar at the top. Its project/data controls are also under Plugins → Ag-GIS. No separate Python installation, pip packages or companion app is required.

The ZIP contains all runtime modules, native/bundled icon support, licence and this guide. Farm data is saved separately in Documents → Ag Tech Tooling → Projects.

## Optional GitHub connection (development build only)

1. Choose **Plugins → Ag-GIS → GitHub Connection…** to see connection status.
2. Sign-in is currently unavailable while app registration and safe diagnostic
   handling are unfinished. **Connect** is deliberately disabled. This is not a
   login, an account connection or a request for a personal access token.
3. Choose **Close** and keep working locally. Farm maps, agent instructions and
   local report drafts need no account; nothing is sent by this status window.

This development dialog has not been delivered to the normal installed build.

## Connect your agent: describe a problem or idea

1. Click **Feedback → Connect your agent → Copy agent instructions**.
2. Paste into your own agent (Codex, Claude Code, Hermes or another file-reading
   agent), then describe the farming job in ordinary words. The instructions are
   bundled locally as START_HERE.txt; reading/copying requires no login or internet.
3. Give access to source and synthetic examples only, not your farm-data folder.
   An external AI provider may process what you paste; check its privacy controls.
4. Review the draft, destination and attachments before explicitly choosing to
   share. Bugs/ideas go to JamRov/Ag-GIS-Feedback; proposed code changes go as PRs
   to Ag-Tech-and-Machine/Ag-GIS for maintainer review. Nothing is sent by Copy.

Close to cancel. If this tab is missing in an older build, use START_HERE.md in
   a trusted source checkout. In-app GitHub login is not implemented by this page.

## First farming workflow

Prerequisites: Ag-GIS enabled, a writable local Documents folder and a small supported dataset you can safely test. Finish layer edits and save any current map first. Use a separate test workspace, not your working farm, when trying this out.

1. Click **New Project**. A new numbered **My Farm Data** folder opens; existing folders are preserved.
2. Click **Manage Data** to rename Organisation 1, Client 1, Farm 1 and Field 1. Each rename saves immediately. Organisation is the managing business; Client is the grower, even if both have the same name.
3. Click **Data In**, then **Choose File**. Review Data, Type, Destination and Status. If the field has no boundary, choose its destination yourself; a missing automatic match is not an import failure.
4. Check only the wanted rows, confirm their destination and click **Import to Field**. Expect **Saved** and a copy under **Whole Field → Imported Data**. Original files stay where they were. Closing before import adds nothing; stopping during saving retains earlier completed imports.
5. Select the dataset in **Farm Data** to view it. Use **Whole Map** for the farm-data extent, not the worldwide background. Use **Filter Data → All fields / All data types** if a filter hides a dataset; also inspect its visibility checkbox.
6. Click **Save Map**. Finish and save layer edits separately before switching projects. Reopen with **Open Project → your project folder → Farm.qgz**; the existing **Data/farm.gpkg** route also works. Expect the saved hierarchy, managed datasets and map presentation to return.

Keep the complete workspace together, including Farm.qgz, Data and supporting files. If opening reports missing files, restore the complete workspace from a verified backup; do not create an empty replacement database or change its schema version. See [the pilot checklist](PILOT_CHECKLIST.md) in the source repository for controlled acceptance testing.

## Keep your saved map styling (development build)

1. Edit a managed dataset using native layer styling, then click **Save Map**.
   This build saves a separate recovery snapshot of that native style, without
   changing original source data or the import-style record.
2. Reopening normally keeps the map's own styling. Reconstructing a missing managed
   layer from the catalogue uses the last successfully synchronized style, including
   deliberate reset results after saving. No new style or reset buttons are added.
3. If **Saved styling** reports a storage/conflict warning, preserve Farm.qgz and
   the complete workspace for review: recovery may have older styling than the map.
   Duplicate map copies or older/external saves are not silently chosen as winners.
   Do not delete style history to suppress the warning. Conflict-resolution controls
   and complete dependency/backup handling are not implemented.
4. Keep external symbols/fonts and other required assets. Unsaved edits, edits saved
   with older builds, and interrupted map/metadata writes are not guaranteed by
   this snapshot. Original fields, raw units and reviewed job history are unchanged.

## Browse Farm Data

1. Open an Ag-GIS farm project. The existing left-hand Layers panel is labelled **Farm Data** for that project.
2. Expand Organisation → Client → Farm → Field, then Whole Field or Seasons → Season → Crop. Each level uses the same icon as Manage Data; Plans, Operations and Results also have their own icons. Larger icons, spaced rows and reduced indentation make the hierarchy easier to read.
3. Select a field to browse its branches without hiding other fields. Use the normal visibility checkboxes to show/hide its own data, and the map-layer symbols to read the map legend. Use Filter Data deliberately for a specific field/type. Hover over a hierarchy name to see its type and full name.
4. Use **Manage Data → Rename** for persistent organisation/client/farm/field/season names. A native map-group rename only changes its map label and can be reset by synchronising the farm records.
5. Disabling the plugin restores the original tree styling and panel title. Opening a general QGIS project restores the Layers title; unrelated groups/layers keep native rendering. Simple view continues to show only this browser and the map beside our toolbar.

## Data In workflow

### Review a job's season before import (development build only)

1. Select a supported file in Data In and choose an existing field destination.
2. Click **Preview Job Season…**, inspect its original attribute sample and enter
   the recorded job date (`YYYY-MM-DD`) and job type. These are explicit review
   inputs, not automatically decoded machine metadata.
3. Read the matching season and its chronological dates. First and last days are
   included. Missing dates, unknown job types, gaps, overlaps or a date outside
   the field's seasons report that review is needed; no history is changed.
4. For one whole-dataset job, set the row's Type to **Other data** and choose
   **Use for Import**, then **Import to Field**. The copy and reviewed context save
   under **Seasons → matched season → Operations**, including after reopen/recovery.
   Mixed jobs must be separated first: no per-feature job splitting is implemented.
5. **Close** cancels changes to the review; **Keep Whole Field** clears a staged job.
   No writes occur until import. Unreviewed/reference data still goes to
   **Whole Field → Imported Data**. Changing destination clears the job review.
6. If source or season dates changed, close/rescan and review again. Conflicting
   existing imports are not reassigned. Original attributes and units stay raw;
   this is explicit local classification, not automatic machine decoding or a
   unit conversion. Linked date editing and affected-history review remain unfinished.


1. Click Data In on the top toolbar. Choose File or Choose Folder; scanning starts
   automatically. You can also paste a local/NAS path and press Enter.
2. Create/open an Ag-GIS project before scanning. Review **Data → Type → Destination → Status**.
   **Detected** shows a field found from its boundary; **Please set** needs your choice.
3. Use each row's **Destination** dropdown to select an existing field. The full
   Organisation / Client / Farm / Field path distinguishes matching field names.
   Choose **Add new field…** to enter its hierarchy below the table, then click
   **Use for This File** or **Apply to Checked Files**. New planned fields are also
   available in the other row dropdowns before importing. Each file keeps its Type.
   Missing coordinate systems must be confirmed individually in the inline editor.
4. Manual choices show **Ready**. Apply edits and untick unwanted files. Once all
   checked rows have destinations, click **Import to Field**. Successful rows show
   **Saved**. No secondary destination popups appear. Closing before import leaves
   data unchanged; switching rows keeps unfinished hierarchy edits.
5. Normal copies appear under Field → Whole Field → Imported Data; explicitly
   reviewed jobs use Seasons → matched season → Operations. Vectors save into
   the GeoPackage; rasters into Data/Rasters. The map saves automatically. Deere
   setup metadata is previewed; proprietary guidance geometry still needs a decoder.
6. Stop Scan or Close cancels without adding data. If no data is found, choose the
   complete export folder. If access fails, reconnect the drive/NAS and retry.

Common GIS files and ZIP contents are detected by QGIS. Scans are limited to
10,000 files; ZIPs to 10,000 entries / 512 MiB uncompressed. Linked folders,
encrypted/unsafe ZIPs and nested archives are skipped or reported. A fresh scan
clears old selections. See below for managed saving and filtering.

PCT GDP (`.pctgdp`) projects are recognised when selected directly or found inside
folders. Expand the project to inspect its layer names. Hover Status for recorded
units/grid spacing and UTM metadata. **Decoder verification needed** means inspection
only: the layers cannot yet be checked for import and nothing is saved or assigned.
Keep the original; changing its extension will not make its geometry readable.

Managed saving is now implemented for native vector data and supported rasters.
Cloud, season-data mapping and proprietary Deere guidance decoding remain pending.
GeoTIFFs retain their complete data/metadata. Other raster conversions with uncertain
georeferencing or scale/offset need native raw-data GeoTIFF export first. Stop during
saving retains earlier completed imports; closing before import adds none.

## Filter saved data

1. Click Filter Data. Choose a field (or All fields) and a data type (or All data types),
   then Apply. Selecting a field in Farm Data does not apply or replace this filter.
2. Filters show/hide datasets and query native reference layers; they do not crop
   or delete data. Unrelated layers and manually hidden datasets are preserved.
3. All Fields reference views are read-only. Choose a specific field before editing
   native reference features. Finish edits before changing a filter.
4. Save Map to retain the view. If a catalogue dataset is missing from the map,
   reopening its workspace restores the entry from managed storage.

## Create a project

1. Click New Project. No setup form is required. Finish layer edits first and respond to any native Save/Discard/Cancel prompt for the current map. Cancel creates no new workspace.
2. The plugin creates My Farm Data under your system Documents → Ag Tech Tooling → Projects and opens its map. On this machine the parent is C:\Users\Michael\Documents\Ag Tech Tooling\Projects. Existing folders are preserved: subsequent projects use My Farm Data 2, My Farm Data 3 and so on.
3. In Layers, expand Farm Data → Organisation 1 → Client 1 → Farm 1 → Field 1. Whole Field contains native Boundaries, Guidance Lines and Infrastructure views. Seasons contains Season 1 with Plans, Operations and Results branches. These are starter names; no year, crop or geometry is invented.
4. Click Manage Data to rename the starter records and add further organisations, clients, farms, fields, seasons and crops as needed. All clients/farms/fields live within this workspace's GeoPackage; creating another workspace is optional.
5. Select a field or one of its branches in Layers to browse without changing other visibility checks. For the shared native reference editing view use Manage Data → Show Field on Map explicitly. Short labels stay at each separate hierarchy level.
6. Save Map saves the current map context. Keep Farm.qgz and Data/farm.gpkg together when moving a workspace. The database uses the existing schema 2.

The initial CRS comes from the current QGIS map, falling back to EPSG:4326 if it is unrecognised. It is a startup default, not a choice of local survey projection or elevation datum. For an explicit project name, destination, ownership and CRS before creation, use Plugins → Ag-GIS → New Project with Options…. That advanced form remains available off the main toolbar. If Documents cannot be found or written, the error reports it; use the options menu to choose another writable local location.

Organisation identifies the business managing the workspace; Client identifies the grower/customer. An owner-operator can use the same name for both. IDs and parent relationships remain separate.

## Manage the hierarchy

1. Click Manage Data. Select an organisation to add a Client; select a client to add a Farm; select a farm to add a Field.
2. Select a field to add a Season. Give it a descriptive name, such as 2026 Winter, and optional YYYY-MM-DD dates. Select a season to add a Crop. Multiple crops/cycles are supported.
3. Select a named record and click Rename to change its label while keeping its ID and child relationships.
4. Adds and renames save immediately to GeoPackage. Close leaves saved changes in place; cancelling an Add/Rename dialog makes no change. Duplicate names under the same parent and missing parent references are refused. Two clients can each have a Home Farm and North 40 field.
5. Every field has Whole Field and Seasons branches. Whole Field shows boundaries, guidance, terrain/drainage and infrastructure categories. Seasons/crops show planning, operations and results categories. These grouping rows have icons but are not separate database tables.
6. In Manage Data, select a field or any of its branches and click Show Field on Map. This explicit action displays shared native Boundaries, Guidance Lines and Infrastructure layers filtered to that field, reusing them rather than making copies. Unrelated map layers are retained. Finish layer edits first; a refused switch retains the previous editing field. Main Layers row selection is browsing only and does not invoke this exclusive reference view.
7. Save Map saves the map layout/layer context. Keep the complete project folder together when moving it.

The Manage Data tree is a focused dialog, leaving map and Layers as the primary workspace. Finish native layer edits before changing field context. Season/crop records and categories are implemented; importing/editing seasonal datasets, terrain and job/prescription workflows are future development. Show Field currently displays Whole Field reference layers, not a season-specific data filter. Revision fields exist on reference features, but automatic boundary/guidance history and historical job links are not yet implemented.

## Open or upgrade an older project

1. Click Open Project and select Farm.qgz inside your Ag-GIS project folder. Selecting Data/farm.gpkg is also supported. Both routes validate the complete workspace before opening its map; other maps/databases belong in Data In rather than this project picker.
2. Schema 1 projects remain readable. Click Manage Data to create an upgraded schema 2 copy.
3. In Upgrade Project Copy, confirm Organisation and Client names, a new project/folder name and an existing parent folder outside the original workspace. Click Create Upgrade Copy.
4. The plugin copies supporting files, takes a consistent SQLite database snapshot, builds the hierarchy with native QGIS and validates the result before publishing the new folder. The original stays unchanged, and its farm ID is retained in the upgraded farm record.
5. The upgraded copy opens and Manage Farm Data appears. If opening is cancelled, the completed copy remains at its reported location.

If creation/upgrade fails, correct the reported name/path/permission issue and retry. Existing destinations are refused; failed staged copies are cleaned up. For missing files, restore the full folder from a known backup. A newer unsupported schema needs a compatible plugin; do not alter version fields to bypass validation. This is not a general GeoPackage importer or a backup of external file dependencies. Work locally with one editing session; multi-user locking and NAS editing are not implemented.

## Toolbar and Simple view

- New Project / Open Project / Manage Data: project setup and data hierarchy.
- Save Map: native QGIS Save Project. Save layer edits through QGIS before switching context.
- Move Map / Zoom In / Zoom Out / Whole Map: native QGIS navigation and full extent, with native enabled/checked states.
- Simple view at the bottom right: keeps our toolbar, map and Layers. Turn it off to restore the full interface. In full view, recover a hidden toolbar through View → Toolbars → Ag-GIS.

Toolbar buttons have larger icons and text labels. Hierarchy rows, grouping rows, dialog buttons and input lines have icons. We use QGIS theme icons and bundled vector icons without changing global QGIS icon settings.

## Native QGIS foundation and limits

Layer/table creation, hierarchy writes, constraint SQL and map layers use PyQGIS and QGIS's bundled providers/writers. Qt comes through qgis.PyQt. Python SQLite performs read-only structural queries and the storage snapshot during a copy upgrade. All actual GIS data/schema changes use QGIS.

Managed imports of supported native vector and raster data, map/browser settings and hierarchy editing are implemented. Complete portable export, conversion tools, seasonal dataset editors, automated history/backup and multi-user editing remain under development. The workspace still requires both QGZ and GeoPackage plus any referenced supporting files.

## Updating Ag-GIS

1. Choose **Plugins → Ag-GIS → Check for Updates…**. Review your installed version and channel, then choose **Check now**. Checks are manual by default; background checks require your permission and never install an update automatically.
2. Read the available version, changes, compatibility and any data-upgrade warning. **Preview** is for explicit testing; the default **Stable** channel does not offer experimental packages. A connection error or missing catalogue means update information is unavailable, not that your installation is current.
3. Download a compatible offered update. Finish layer edits and save your map before confirming installation. Ag-GIS verifies the ZIP, retains a recovery copy of its plugin files and delegates installation to QGIS. Cancel or retry a failed download without changing the installed plugin.
4. Follow the native installation result and restart QGIS. The next load checks the installed version against the attempted update. A recovery copy protects plugin files only, not farm records; reverting software cannot undo a data-format change.
5. Offline ZIP selection remains available. Read its authenticity warning and use official packages: archive checks alone cannot identify the author of an arbitrary file.

Update checks contact GitHub, which receives connection metadata including your IP address; no farm files or project paths are included in the request. No paid account is required. Existing farm folders keep their location. QGIS/runtime upgrades remain a separate installer step.

**Development status:** the approved catalogue is intentionally empty locally and this change has not published it. The new updater is not automatically present in older installed builds. See [UPDATES.md](UPDATES.md) in the source documentation for delivery and recovery details. Local source changes are not automatically part of a public download.

Farm Data fills the available left panel below its small toolbar. Resize the panel by dragging the divider beside the map; the tree follows the panel size when QGIS is restored or maximised.

## Farmer view defaults — 0.10.0

1. Create a project with **New Project**. Organisation, Client, Farm, Field and Season are ready in Documents; an **OpenStreetMap** background is already saved in the map. Existing farm maps receive the background on their first open with this version.
2. Select a farm/field in **Farm Data**. Other branches and their visibility checks stay unchanged. A field with mapped data can zoom when the Map & Browser Settings zoom option is enabled; disable that option to keep the map extent fixed while browsing. Selecting a dataset does not tick it on or clear a deliberate filter; only an already-visible dataset can auto-zoom. Use individual field checkboxes for independent visibility; visibility ticks (mouse or Space) do not zoom the map. With Filter Data set to All fields, shared All Fields native reference layers show features only from checked field/Whole Field branches, including parent-group visibility; their own layer checks are preserved. No features are deleted. Choose a specific field with Filter Data to edit native references; that deliberate filter remains separate from browsing.
3. Imported filenames start with spaces and a short label (up to 48 characters). Hover for the original full name. Use QGIS Rename or the panel's pencil button to choose your own label. Saved dataset renames update the GeoPackage catalogue; Save Map retains the map presentation. Source filenames and table names do not change.
4. Use the panel's **Add farm item** (+) menu. Select its parent, then choose Organisation, Client, Farm, Field, Season or Crop. Enter a name; Season also offers optional dates. Cancel leaves the data unchanged. Names save immediately to GeoPackage. Select an item and use the pencil button (or native Rename/F2) to rename it. Fixed headings such as Whole Field and Seasons stay fixed.
5. Plain default symbols start as green points, clear lines and light polygons; boundaries have an outline without fill. A newly prepared single-point dataset uses a readable 2 mm marker; multi-point datasets retain the compact 0.65 mm starting theme. This does not resize an existing saved map or custom-sized/source-authored marker. Thematic renderers and shaped/custom-sized symbols are retained. Raster pixel values and native raster styling are retained. Use native QGIS Layer Properties/Symbology for your own colours, sizes and thematic maps. Defaults apply once; later names/styles are preserved. The original starting vector style is retained in the map's layer custom properties.
6. Choose **View Settings** on the top toolbar (also Plugins → Ag-GIS → Map & Browser Settings). Override branch focus, selection zoom, starting names/symbols and background for this map. Tick **Also use these defaults for new projects** to change future setup. Cancel changes nothing. Save Map retains this map's overrides. Existing custom names/styles are not reset by this dialog.
7. Current background choices are **Roads — OpenStreetMap**, **Imagery — Esri World Imagery**, **Satellite — Australia 2025 (30 m)**, **Satellite — World 2016–17 (10 m)** and no automatic background. See **Background choices on the left** below for switching, credits and resolution limits. You can uncheck/remove backgrounds directly; ordinary reopening respects that choice. Use the native Data Source Manager for your own licensed imagery.

OpenStreetMap is an online road/place map, not aerial imagery. Internet access is required; normal QGIS HTTP caching is used and no offline/prefetch tool is provided. Attribution is visible on the map and drawn into native canvas image exports. For print layouts, include an attribution label using the background layer's rights metadata. Google tiles are not bundled as an unlicensed URL; Nearmap needs a subscription. Background service availability and coverage are outside the plugin. Offline work on local farm data remains possible with the background disabled.

## Feedback and help

Use **Feedback** on the toolbar to report a problem, suggest an improvement or ask for help. Fill in the summary/details, then review the report. **Open GitHub form…** prepares a report for you to review and submit; keep its issue number to follow progress. Long reports are copied for pasting in full. You can also **Save report**, **Copy report** or open an **Email draft** if you do not use GitHub. Save before exiting/reloading QGIS. No farm files, map names, paths, account details or logs are collected automatically; app/QGIS/system versions can be unticked. Do not share private farm information, credentials or original datasets. Public GitHub issues are readable by everyone; private issues require access. A saved/email draft is not tracked until support creates an issue. See the reporting/triage guide for steps and known failures.

Whole Map and post-import zoom use native coordinate-aware extents of the farm datasets, excluding the world background. A new empty map starts at its coordinate system area of use (worldwide for a global CRS); selecting mapped field data zooms in. Existing saved map extents are retained.


Public feedback tracker: https://github.com/JamRov/Ag-GIS-Feedback/issues . Product source and release downloads are public in Ag-Tech-and-Machine/Ag-GIS. Anyone can read feedback; posting needs a GitHub account. Reports and attachments are public, so remove farm/customer details before sharing. Save/email remains available without GitHub.

## Background choices on the left — 0.12.0

This replaces the earlier single-background setup. New and existing farm maps now include an expanded **Background** group beneath Farm Data.

1. Expand **Background** in the left panel if needed. Click a map name to select it, or tick **Roads — OpenStreetMap**, **Imagery — Esri World Imagery**, **Satellite — Australia 2025 (30 m)** or **Satellite — World 2016–17 (10 m)**. QGIS turns the other background off, keeping your farm layers above it. Untick the selected background for a plain map. No extra panel or plugin is required. While the map redraws, **Changing background…** covers the old image until the new choice is ready.
2. **Save Map** retains the checkbox choice. Turning the Background group off hides it; ordinary reopening respects existing checked/removed layers. Explicitly selecting a removed choice in View Settings restores it.
3. In **View Settings**, the same four options plus No automatic background are available. Tick **Also use these defaults for new projects** to start future workspaces with your preferred background.
4. The Australian satellite layer is a 2025 annual Landsat cloud-free composite from Digital Earth Australia at 30 m resolution. The worldwide layer is historical EOxCloudless Sentinel-2 imagery from 2016–17 at 10 m resolution. Their years/resolutions are in the layer names; neither is live or detailed aerial photography. Zooming closer does not add detail.
5. Esri World Imagery supplies worldwide aerial/satellite imagery with location-dependent detail and capture dates; it is not live or survey-grade. Existing maps receive this new choice unchecked without changing the saved selection, hidden groups or removed old options. Its credit links to Esri's official item and terms; no claim of an open-data licence or universal reuse permission is made.
6. All require internet access; visible tile requests reveal the requested map area to the selected provider. Credits switch with the selected background and appear in native canvas image exports; add required credit in print layouts and check permitted use before distributing imagery. No bulk/offline imagery download is provided. Outside Australia, choose Esri, World or Roads.

These providers require no API key for the supplied services. Google was deferred at the user's request because no Maps Platform account is available; no unofficial Google tile endpoint or placeholder Google checkbox is shipped.

Background loading correction (15 October 2026): saved built-in satellite layers are repaired automatically on open. Closer views enlarge supported tiles, avoiding blank Australia imagery from unsupported zoom requests. Fine detail is limited by the stated 30 m / 10 m source resolution. Switching backgrounds cancels the previous render; unticking the active checkbox still gives a plain map.
