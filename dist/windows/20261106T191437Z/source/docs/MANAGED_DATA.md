# Save and filter farm data (0.9.0)

## Import

Prerequisites: a current Ag-GIS workspace, readable source data, sufficient free
local disk space, and no layers in editing mode. Sources are never moved/deleted.

1. Open/create a farm workspace, then click **Data In**.
2. Choose a file/folder or enter a local/NAS path. Scanning is cancellable.
3. Review the selected datasets. Each layer has a **Type** dropdown: Other data,
   Field boundaries, Guidance lines, Infrastructure, Sample points, Management
   zones, Elevation/terrain, Aerial imagery or Vegetation index, as appropriate for
   its geometry/raster representation. These are explicit roles, not automatic
   agronomic diagnoses. A polygon does not automatically become a boundary.
4. Review Destination before Status. Full geometry containment in one boundary
   shows **Detected**. Otherwise select the row and choose/create Organisation →
   Client → Farm → Field below the table. Supply unknown CRS individually. Click
   **Use for This File** or **Apply to Checked Files**; each Type is retained.
5. **Ready** means the manual destination is applied. Every checked row must have
   a destination before **Import to Field** enables. Untick files to defer them.
   No destination popups appear; closing before import adds nothing.
   A modal save-progress control supports **Stop**. Each dataset is completed
   independently: stopping/failing a later copy retains earlier completed datasets
   and any already-confirmed new hierarchy records. Failed copies are not catalogued;
   their partial output table/files are removed. Results identify failures.
6. Unreviewed/reference imports appear under Field → Whole Field → Imported Data;
   explicitly reviewed one-job imports use Seasons → matched season → Operations
   (see [Data In](IMPORTS.md)). Both have a
   managed copy and a catalogue entry. The map is saved automatically after imports.
   If the map write fails, the message says so: data remains saved, and the catalogue
   can restore the layer when the workspace next opens. Save Map for later changes
   to display/filter/style.

After import, all data types in the destination field are shown. A multi-field
batch shows all fields, so a prior restrictive filter cannot hide its new results.

Re-import an older linked layer to migrate it into managed storage. Its existing
field assignment is retained; its source link is replaced by the saved copy.
Unchanged source URI/content/CRS, field and type combinations reuse the existing
saved dataset rather than writing another copy. Different source content or a
different assignment creates a separate dataset; existing data is not overwritten.
Virtual raster sources with no local-file content hash are not deduplicated.

## Saved structure

```text
Farm workspace/
  Farm.qgz
  Data/
    farm.gpkg
    Rasters/
      <dataset-id>.tif
      <dataset-id>.tif.aux.xml   (when supplied)
      <dataset-id>.tfw          (when supplied)
```

Vectors are written by `QgsVectorFileWriter` into uniquely named tables in
`farm.gpkg`. Original attributes, CRS and geometry are retained; source fields
named `fid` or `field_id` are not repurposed. A separate internal feature key
avoids collisions with source IDs. Dataset tables represent heterogeneous imports,
not a table for every field/year; one catalogue tracks their shared identities.

The additive `agtech_datasets` attribute table has catalogue version 1, dataset ID,
field ID, role, layer type/provider, relative managed URI, CRS WKT, original URI,
source hash, UTC import time and native QGIS style XML. It is registered as a
GeoPackage attributes table through the native writer. Core farm schema remains 2.
Metadata reads use the existing sqlite3 pattern; catalogue writes use native QGIS
providers. Existing hierarchy/reference tables are not replaced.

Rasters remain numeric/image rasters in **Data/Rasters**, not rendered snapshots.
Complete local GeoTIFFs are copied byte-for-byte with known metadata/worldfile
companions. Other supported rasters use native raster writer/pipe with the same
dimensions, CRS and extent and lossless GeoTIFF compression. Numeric type, bands,
NoData, scale/offset and extent are checked before registration. QGIS's bundled
GDAL bindings transfer band units/descriptions/colour interpretation and metadata
that the writer API does not expose; see TOOLING.md for the bounded exception.

Unreferenced rasters need QGIS Georeferencer. Non-GeoTIFF conversions with rotation,
GCPs or nontrivial scale/offset are refused: prepare a georeferenced raw-data
GeoTIFF first, then retry. No implicit clipping, resampling or unit conversion is
performed during a supported import. Display styles remain native QGIS styles;
automatic semantic styling and measurement/unit mapping remain future work.

Keep the **entire workspace folder** together for moving, sharing or backing up.
The GeoPackage remains the central vector/metadata store; it is not the only file
when rasters are present. Managed URIs are relative to the workspace, so originals
and old workspace paths are no longer needed after a successful import.

## Filter

1. Click **Filter Data** on the top toolbar.
2. Choose **All fields** or a full field breadcrumb, then **All data types** or a
   specific type. Click **Apply**. Close leaves the chosen view applied.
3. Selecting a field in Farm Data also applies that field filter, retaining the
   current data-type filter. To see everything, choose both All fields and All data
   types. Selecting the previously active field after an All fields view restores
   its field filter.
4. Filters affect managed/assigned imports and native reference views. Other map
   layers retain their visibility. User-hidden datasets stay hidden when a filter
   is cleared. Native shared references show all records under **All Fields** when
   viewing all fields; these aggregate views are read-only. Choosing a field moves
   the shared references back under its Whole Field branch with valid field defaults.
5. Click **Save Map** to retain filter and visibility choices. Filtering does not
   crop features, change values or remove any dataset. Finish edits before switching
   filters. Seasonal and attribute/value-range filtering are not implemented here.

## Recovery and checks

- Failed source access: reconnect NAS/local disk, then rescan. Originals are unchanged.
- Unsupported raster conversion: use native QGIS raw-data GeoTIFF export and retry.
- Failed copy/catalogue registration: free disk space or resolve permissions, then
  retry; completed datasets remain available. Do not manually delete arbitrary tables.
- Lost map entry: opening the workspace reloads catalogue datasets missing from
  its map. Missing/corrupt managed files require restoring the full workspace backup;
  the catalogue is an index, not a second copy of the data.
- Never import the open workspace's own GeoPackage back into itself; use Open Project
  or Filter Data. Concurrent multi-user edits on a shared NAS are not supported.

`tools/managed_data_test.py` exercises real shapefile attributes and duplicate source
IDs, Z/M geometry, complete GeoTIFF preservation, numeric ASCII-grid conversion,
NoData/scale/offset, source preservation, duplicate handling, failed-copy cleanup,
name-collision protection, manual visibility, shared reference filtering, source
removal, workspace move and catalogue recovery in a fresh QGIS Python process.
Run `scripts/check.ps1` for the full source/extracted-plugin checks and packaging.
