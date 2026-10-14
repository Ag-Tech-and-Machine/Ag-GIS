# Ag Tech Tooling — user guide

Version 0.3.1. Requires QGIS; tested with QGIS 3.44.14 LTR on Windows.

## Install

1. In QGIS, choose Plugins → Manage and Install Plugins → Install from ZIP.
2. Select ag_tech_tooling-0.3.1.zip and install it.
3. Under Installed, enable Ag Tech Tooling. Restart QGIS when updating an already loaded version.
4. Find the controls under Plugins → Ag Tech Tooling. No separate Python installation, pip packages or companion app is required.

The plugin ZIP includes all current runtime modules, icon, metadata, license and this guide. Farm datasets are created separately in a location you choose; they are not bundled with the plugin.

## Simple view

1. Check Simple view in the bottom-right status bar.
2. Use the map and Layers in the primary workspace.
3. Uncheck it to restore the full interface when you need advanced panels.

## New farm

1. Choose Plugins → Ag Tech Tooling → New Farm Project….
2. Enter the farm name and browse to an existing local parent folder outside the plugin/source directory.
3. Confirm the farm coordinate system. The initial value comes from the current map; choose one appropriate for the farm's location and intended work.
4. Choose Create Farm. A new farm folder contains Farm.qgz and Data/farm.gpkg. The map starts empty; the database records farm ID, name, schema version, coordinate system and creation time.
5. Finish layer edits before switching. Save, discard or cancel unsaved map changes when prompted. Cancelling after creation leaves the current map open and retains the new farm at the reported location.

Existing folders are not overwritten. If creation fails, resolve the reported name/path/permissions error and retry.

## Open farm

1. Choose Plugins → Ag Tech Tooling → Open Farm Project….
2. Select Data/farm.gpkg inside an Ag Tech farm folder.
3. The plugin validates the database and companion map, then opens Farm.qgz using QGIS.
4. Save map changes with QGIS's normal Save control. Keep the complete folder together when moving or manually backing it up.

This opens Ag Tech farm workspaces, not arbitrary GeoPackages. Restore missing files from a known backup. A newer schema requires a compatible plugin; do not alter version fields to bypass validation.

## Native QGIS foundation

The plugin uses PyQGIS for map/project handling, vector layers/providers, GeoPackage writing, coordinate systems and QGIS interface integration. QGIS uses its bundled GDAL/OGR provider underneath. Qt controls are imported through qgis.PyQt. Python SQLite is used only for read-only structural/identity checks.

Planned import/export and conversion controls will use QGIS providers, writers, coordinate transforms and Processing algorithms, with project transform context, explicit outputs and processing feedback where appropriate. Those controls do not exist yet.

## Current limits

The current workspace requires both the GeoPackage and QGZ. Agricultural schemas, imports/exports, editable settings, conversions, automatic backup and multi-user locking are not implemented. Work locally; shared database editing on a NAS is not the supported default.
