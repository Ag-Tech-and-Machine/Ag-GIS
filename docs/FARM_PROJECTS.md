# Farm projects — structure proposal

Status: proposed, 15 October 2026. Farm management is not implemented. No existing farm data has been moved.

## Recommendation

Present one **Farm Project** to the farmer. Use one managed directory per farm, with permanent records and dated jobs inside it. Use standard formats accessible without Ag Tech Tooling, and an ordinary ZIP for backup/transfer. Unpack before editing.

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

These are proposed controls, not instructions for the current plugin.

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

This is a documented recommendation. The farm-management behaviours above have not been implemented or tested.
