# Ag Tech Tooling — user guide

Version 0.5.0. Requires QGIS; tested with QGIS 3.44.14 LTR on Windows.

## Install

1. In QGIS, choose Plugins → Manage and Install Plugins → Install from ZIP.
2. Select ag_tech_tooling-0.5.0.zip and install it.
3. Under Installed, enable Ag Tech Tooling. Restart QGIS when updating an already loaded version.
4. Find the Ag Tech Tooling toolbar at the top. Its project/data controls are also under Plugins → Ag Tech Tooling. No separate Python installation, pip packages or companion app is required.

The ZIP contains all runtime modules, native/bundled icon support, licence and this guide. Your farm data is saved separately in a location you choose.

## Create a project

1. Click New Project. Enter a project name, Organisation, Client / Grower and First farm. Optionally enter a first field.
2. Browse to an existing local parent folder outside the plugin/source directory.
3. Confirm the coordinate system for the farm's location and intended work. Its initial value comes from the current map and may need changing.
4. Click Create Project. The new folder contains Farm.qgz and Data/farm.gpkg. GeoPackage schema 2 stores separate organisation, client, farm, field, season and crop records and native reference layers.
5. Finish native layer edits before switching. Save/discard/cancel unsaved map changes when prompted. Cancelling a switch retains the new project and your current map.
6. On successful opening, Manage Farm Data appears for further setup. Existing destination folders are never overwritten.

Organisation identifies the business managing the workspace; Client identifies the grower/customer. An owner-operator can use the same name for both. IDs and parent relationships remain separate.

## Manage the hierarchy

1. Click Manage Data. Select an organisation to add a Client; select a client to add a Farm; select a farm to add a Field.
2. Select a field to add a Season. Give it a descriptive name, such as 2026 Winter, and optional YYYY-MM-DD dates. Select a season to add a Crop. Multiple crops/cycles are supported.
3. Select a named record and click Rename to change its label while keeping its ID and child relationships.
4. Adds and renames save immediately to GeoPackage. Close leaves saved changes in place; cancelling an Add/Rename dialog makes no change. Duplicate names under the same parent and missing parent references are refused. Two clients can each have a Home Farm and North 40 field.
5. Every field has Whole Field and Seasons branches. Whole Field shows boundaries, guidance, terrain/drainage and infrastructure categories. Seasons/crops show planning, operations and results categories. These grouping rows have icons but are not separate database tables.
6. Select a field or any of its branches and click Show Field on Map. QGIS displays shared native Boundaries, Guidance Lines and Infrastructure layers filtered to that field. Unrelated map layers are retained. Selecting another field reuses these layers rather than making copies.
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
- Simple view at the bottom right: keeps our toolbar, map and Layers. Turn it off to restore the full interface. In full view, recover a hidden toolbar through View → Toolbars → Ag Tech Tooling.

Toolbar buttons have larger icons and text labels. Hierarchy rows, grouping rows, dialog buttons and input lines have icons. We use QGIS theme icons and bundled vector icons without changing global QGIS icon settings.

## Native QGIS foundation and limits

Layer/table creation, hierarchy writes, constraint SQL and map layers use PyQGIS and QGIS's bundled providers/writers. Qt comes through qgis.PyQt. Python SQLite performs read-only structural queries and the storage snapshot during a copy upgrade. All actual GIS data/schema changes use QGIS.

Imports/exports, full settings editing, conversion tools, seasonal dataset editors, automated history/backup and multi-user editing remain under development. The workspace still requires both QGZ and GeoPackage plus any referenced supporting files.
