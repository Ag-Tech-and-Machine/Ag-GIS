# Farm projects — structure proposal

Status: GeoPackage selected as the core farm data format, 15 October 2026. Version 0.3.0 implements the minimal New/Open foundation below. Agricultural schemas, imports, exports, conversions, editable settings and backup/restore remain proposed. No existing farm data has been moved.

**Current release: 0.6.0.** The [data model](FARM_DATA_MODEL.md) now documents implemented schema 2 hierarchy tables, season/crop records, native field reference layers, icon-labelled management controls and a separate-copy schema 1 upgrade. Follow [USER_GUIDE.md](USER_GUIDE.md) for current operation. The 0.3.x foundation and directory illustration below are retained as earlier design context. Current New Project needs no form: it creates My Farm Data (or the next free numbered name) in system Documents/Ag-GIS/Projects, with the full starter Organisation/Client/Farm/Field/Season tree. Rename and add records through Manage Data. New Project with Options remains available in the plugin menu.

## Implemented foundation — 0.3.0

Version 0.3.1 keeps this farm schema and file layout unchanged, and writes the GeoPackage through native PyQGIS layers/features and `QgsVectorFileWriter`, using QGIS's bundled provider. All farm runtime code and the user guide ship inside the plugin ZIP. No standalone GIS runtime or companion program is required.

New Farm Project creates only `<Farm name>/Farm.qgz` and `<Farm name>/Data/farm.gpkg`. The map starts empty; no paddock geometry schema is assumed. The GeoPackage contains a registered nonspatial attributes table, `agtech_farm`, with one row: integer `fid` primary key plus text fields `farm_id` (UUID), `farm_name`, `schema_version` (`1`), `crs_authid` and `created_utc` (UTC ISO timestamp). Farm settings are recorded at creation; editing them through the plugin is not yet available.

The QGZ stores the same farm ID and schema version, the relative database location and the selected working CRS. Open Farm Project selects `Data/farm.gpkg`, validates its table, schema, matching map settings and map-layer availability, then opens the companion map. This opens Ag Tech farm workspaces only; it is not a general GeoPackage importer. The database is the core store, but the current workspace requires both files. Keep/copy the whole farm folder together.

Creation uses a temporary sibling directory and validates before renaming it into place. Existing destinations are refused. Validation opens the database read-only; unsupported schemas are rejected without migration. Switching requires layer editing to be finished and offers Save/Discard/Cancel for unsaved map changes. Cancelling after creation retains the new farm and the current map.

The minimal empty workspace has been tested for creation, validation, duplicate protection, failed-creation cleanup and unsupported-schema rejection. A real temporary spatial layer was added for move/reopen testing, and switch cancellation/edit-session protection were checked with real Qt/PyQGIS. This does not establish portability for arbitrary external datasets or a safe multi-user locking/backup system.

## Confirmed direction

The user selected GeoPackage for farm data. The next design work covers the file/data structure, import and export setups, settings and conversion tooling. Do not treat the illustrative folder layout below as a final schema or assume all supporting files must be embedded in one database. Decide QGIS project storage and supporting-file packaging during that design work.

Plan the following connected areas:

1. **Data structure**: farm/job relationships, layer and table definitions, stable IDs, required fields, units, CRS and schema versions.
2. **Settings**: distinguish application preferences, farm/project settings and reusable import/export presets. Define precedence and portability before implementation.
3. **Imports**: supported source formats, field mapping, validation, duplicate handling, provenance and preservation of originals.
4. **Conversions**: coordinate and unit transformations, geometry/raster operations and explicit output destinations. Preview consequential changes and preserve source data.
5. **Exports**: target formats and machine requirements, reusable presets, validation and clear reports of any information lost in conversion.

Develop these incrementally using representative source files and expected output examples. Supported formats and machine compatibility are not yet agreed or implemented.

## Recommendation

The newer [Organisation/Client/Farm/Field model](FARM_DATA_MODEL.md) revises the initial one-directory-per-farm assumption below: a workspace should be able to contain an organisation with multiple clients, farms and fields. The current implementation is unchanged, and the following directory tree remains an earlier illustration rather than the agreed future schema.

Present one **Farm Project** to the farmer. Use one managed directory per farm, with permanent records and dated jobs inside it. Use standard formats accessible without Ag-GIS, and an ordinary ZIP for backup/transfer. Unpack before editing.

A QGIS `.qgz` stores map setup and references to datasets; it does not normally embed those datasets. GeoPackage is an open SQLite container for features and attributes, with raster tile support. QGIS can also store its project inside a GeoPackage, which is useful for a contained vector workflow. For general mixed farm data, recommend a separate QGZ entry point, GeoPackage records and supporting files for original imports, imagery, elevation, LiDAR and documents.

```text
Greenfields Farm/
  Greenfields Farm.qgz          Map, styles, layouts and relative paths
  farm.json                    Stable ID, name, schema version, CRS, entry point
  Data/
    farm.gpkg                  Managed paddocks, boundaries, assets and records
    Imagery/                   Raster imagery
    Terrain/                   Elevation rasters and point clouds
  Originals/                   Unmodified imported source files
  Jobs/
    2026-10-15 Drainage plan/
      job.json                 Stable ID, purpose, inputs, processing history
      working.gpkg             Job-specific layers
      Results/                 Generated outputs
  Exports/                     PDFs and machine/share files
  Documents/                   Notes, photos and supporting documents
```

Create optional directories only when needed. Job results must not silently replace permanent farm records. Choose the working CRS from location and intended work; do not assume one zone for every farm. Record explicit units and, for elevation, the vertical datum.

## Planned farmer-facing steps

The following describes the broader target workflow. New/Open have the limited foundation described above; other controls are proposed.

1. **New Farm Project**: enter a farm name, choose a local destination and confirm location/working units. Expected result: validated project, standard empty layers and sensible styles. Reject duplicate destinations without altering existing data; clean up incomplete creation on failure.
2. **Add Data**: copy complete source datasets into Originals, check type/CRS/units, then create managed layers where appropriate. Expected result: local data with provenance and unchanged originals. Missing CRS and invalid inputs need actionable errors and no half-imported layers.
3. **New Job**: name the task and record its inputs; save working data and results inside its job directory. Applying results to permanent records must be deliberate and recoverable.
4. **Open Farm Project**: select a known farm or its project file. Validate schema and paths before editing. Report missing files and support recovery; never silently discard unavailable layers.
5. **Back Up / Share**: finish edits and release database connections before taking a consistent snapshot. Create a dated ZIP with all managed files and a checksum manifest, then verify it. Exclude locks, disposable caches and recursive backups. Live web services must be listed as online dependencies or replaced with permitted offline data before claiming the package works fully offline.
6. **Restore**: extract to a new local directory, validate checksums and reopen. Retain the original project and archive on failure. Never overwrite an existing farm without an explicit choice.

## Controls to build

- All managed local data stays within the farm root, referenced by relative paths. Detect external dependencies and offer to copy them inside before packaging.
- Stable farm, job and feature IDs survive display-name changes. Validate table names, geometry types, required fields and units.
- Record schema versions; back up before validated migrations. Keep provenance and processing parameters without secrets.
- Use supported database transactions and staged output files. Check before replacing results; do not imply a transaction spans the whole directory.
- Preserve originals and prevent accidental overwrites/deletion.
- Start with one editing session per farm. A plugin lock helps cooperating sessions but cannot control arbitrary external applications.
- Edit locally; store versioned backups outside the farm directory, such as on the NAS. Avoid shared GeoPackage editing over SMB or live synchronisation folders as the default. Evaluate PostGIS separately if simultaneous multi-user editing becomes necessary.
- Storage permissions and backup protection provide access control; GeoPackage itself does not.

## Development sequence and acceptance

Build New/Open Farm Project first, managed import second, verified backup/restore third. Keep the controls compatible with Simple view's map-and-Layers workspace.

Verify sample creation, reopening, folder rename/move and reopening with every layer valid. Exercise cancellation, invalid names, duplicate destinations and missing files. Before shipping import or backup, verify unchanged originals, path containment, database consistency, checksum validation and complete restore to another local path. Test real raster and point-cloud samples before claiming those workflows are supported.

## Primary references checked

- [QGIS 3.44 project files](https://docs.qgis.org/3.44/en/docs/user_manual/introduction/project_files.html): project contents, QGZ and GeoPackage project storage.
- [OGC GeoPackage](https://www.geopackage.org/): open container capabilities and lack of built-in security controls.
- [SQLite over a network](https://sqlite.org/useovernet.html): network filesystem reliability and client/server alternatives.

The broader layout and controls remain a design proposal. Only the foundation explicitly described above is implemented.
