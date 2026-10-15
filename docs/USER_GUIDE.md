# Ag-GIS — user guide

Version 0.8.0. Requires QGIS; tested with QGIS 3.44.14 LTR on Windows.

## Install

1. In QGIS, choose Plugins → Manage and Install Plugins → Install from ZIP.
2. Select ag_tech_tooling-0.8.0.zip and install it.
3. Under Installed, enable Ag-GIS. Restart QGIS when updating an already loaded version.
4. Find the Ag-GIS toolbar at the top. Its project/data controls are also under Plugins → Ag-GIS. No separate Python installation, pip packages or companion app is required.

The ZIP contains all runtime modules, native/bundled icon support, licence and this guide. Farm data is saved separately in Documents → Ag Tech Tooling → Projects.

## Browse Farm Data

1. Open an Ag Tech farm project. The existing left-hand Layers panel is labelled **Farm Data** for that project.
2. Expand Organisation → Client → Farm → Field, then Whole Field or Seasons → Season → Crop. Each level uses the same icon as Manage Data; Plans, Operations and Results also have their own icons. Larger icons, spaced rows and reduced indentation make the hierarchy easier to read.
3. Select a field to view its reference layers. Use the normal visibility checkboxes to show/hide data, and the map-layer symbols to read the map legend. Hover over a hierarchy name to see its type and full name.
4. Use **Manage Data → Rename** for persistent organisation/client/farm/field/season names. A native map-group rename only changes its map label and can be reset by synchronising the farm records.
5. Disabling the plugin restores the original tree styling and panel title. Opening a general QGIS project restores the Layers title; unrelated groups/layers keep native rendering. Simple view continues to show only this browser and the map beside our toolbar.

## Data In workflow

1. Click Data In on the top toolbar. Choose File or Choose Folder; scanning starts
   automatically. You can also paste a local/NAS path and press Enter.
2. Create/open an Ag Tech project, review the data found, untick anything unwanted
   and click Import to Field. If all data fits within just one existing field's
   boundary, it is placed there automatically.
3. Otherwise choose Organisation → Client → Farm → Field in the destination form.
   Select existing names or type new ones. For a field outline, choose the Field
   boundary data type so it can help place later imports. Missing coordinate
   systems must be supplied explicitly. Cancel abandons the entire selected batch.
4. Find the data under that field's Whole Field → Imported Data. Save Map to retain
   placement and source links. Keep original files/ZIPs in place: data is still
   linked rather than copied into the workspace GeoPackage. New hierarchy records
   save immediately after confirming the import. To organise a loose layer added
   by an older version, re-import its source and choose its field.
5. Deere setup folders show their client/farm/field structure and guidance catalogue
   for review. Guidance marked Decoder needed cannot be added yet. Deere ZIPs
   must be unpacked to preview their farm structure.
6. Stop Scan or Close cancels without adding data. If no data is found, choose the
   complete export folder. If access fails, reconnect the drive/NAS and retry.

Common GIS files and ZIP contents are detected by QGIS. Scans are limited to
10,000 files; ZIPs to 10,000 entries / 512 MiB uncompressed. Linked folders,
encrypted/unsafe ZIPs and nested archives are skipped or reported. A fresh scan
clears old selections. Cloud sources and managed GeoPackage import are planned.

## Create a project

1. Click New Project. No setup form is required. Finish layer edits first and respond to any native Save/Discard/Cancel prompt for the current map. Cancel creates no new workspace.
2. The plugin creates My Farm Data under your system Documents → Ag Tech Tooling → Projects and opens its map. On this machine the parent is C:\Users\Michael\Documents\Ag Tech Tooling\Projects. Existing folders are preserved: subsequent projects use My Farm Data 2, My Farm Data 3 and so on.
3. In Layers, expand Farm Data → Organisation 1 → Client 1 → Farm 1 → Field 1. Whole Field contains native Boundaries, Guidance Lines and Infrastructure views. Seasons contains Season 1 with Plans, Operations and Results branches. These are starter names; no year, crop or geometry is invented.
4. Click Manage Data to rename the starter records and add further organisations, clients, farms, fields, seasons and crops as needed. All clients/farms/fields live within this workspace's GeoPackage; creating another workspace is optional.
5. Select a field or one of its branches in Layers to show that field's reference layers. The same three native layers are reused. Short labels stay at each separate hierarchy level.
6. Save Map saves the current map context. Keep Farm.qgz and Data/farm.gpkg together when moving a workspace. The database uses the existing schema 2.

The initial CRS comes from the current QGIS map, falling back to EPSG:4326 if it is unrecognised. It is a startup default, not a choice of local survey projection or elevation datum. For an explicit project name, destination, ownership and CRS before creation, use Plugins → Ag-GIS → New Project with Options…. That advanced form remains available off the main toolbar. If Documents cannot be found or written, the error reports it; use the options menu to choose another writable local location.

Organisation identifies the business managing the workspace; Client identifies the grower/customer. An owner-operator can use the same name for both. IDs and parent relationships remain separate.

## Manage the hierarchy

1. Click Manage Data. Select an organisation to add a Client; select a client to add a Farm; select a farm to add a Field.
2. Select a field to add a Season. Give it a descriptive name, such as 2026 Winter, and optional YYYY-MM-DD dates. Select a season to add a Crop. Multiple crops/cycles are supported.
3. Select a named record and click Rename to change its label while keeping its ID and child relationships.
4. Adds and renames save immediately to GeoPackage. Close leaves saved changes in place; cancelling an Add/Rename dialog makes no change. Duplicate names under the same parent and missing parent references are refused. Two clients can each have a Home Farm and North 40 field.
5. Every field has Whole Field and Seasons branches. Whole Field shows boundaries, guidance, terrain/drainage and infrastructure categories. Seasons/crops show planning, operations and results categories. These grouping rows have icons but are not separate database tables.
6. Select a field or any of its branches and click Show Field on Map. Alternatively select the field directly in the main Layers tree. QGIS displays shared native Boundaries, Guidance Lines and Infrastructure layers filtered to that field. Unrelated map layers are retained. Selecting another field reuses these layers rather than making copies. Finish layer edits first; a refused switch retains the previous field.
7. Save Map saves the map layout/layer context. Keep the complete project folder together when moving it.

The Manage Data tree is a focused dialog, leaving map and Layers as the primary workspace. Finish native layer edits before changing field context. Season/crop records and categories are implemented; importing/editing seasonal datasets, terrain and job/prescription workflows are future development. Show Field currently displays Whole Field reference layers, not a season-specific data filter. Revision fields exist on reference features, but automatic boundary/guidance history and historical job links are not yet implemented.

## Open or upgrade an older project

1. Click Open Project and select Data/farm.gpkg inside an Ag Tech project folder. The companion Farm.qgz is validated and opened.
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

Imports/exports, full settings editing, conversion tools, seasonal dataset editors, automated history/backup and multi-user editing remain under development. The workspace still requires both QGZ and GeoPackage plus any referenced supporting files.

## Updating Ag-GIS

Save your map, then choose Plugins → Ag-GIS → Check for Updates… . Open latest release uses your normal browser for the private JamRov/Ag-GIS GitHub repository. Sign in with an account that has access, download `ag_tech_tooling-<version>.zip`, then return and choose Install downloaded ZIP… . QGIS installs it through its native plugin manager. Restart QGIS after updating. Cancel makes no change. If GitHub shows a missing page, ask the administrator about repository access and release publication. Existing farm folders keep their location after the product rename.
