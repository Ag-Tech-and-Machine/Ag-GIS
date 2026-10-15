# Data In

## File or folder workflow (version 0.8.0)

1. Click **Data In** on the top Ag-GIS toolbar (also available in the
   plugin menu). Choose File or Choose Folder. Selection starts the scan; a pasted
   path can be scanned with Enter or Scan. Local disks and accessible NAS shares
   use the same control.
2. Wait for the results. Folders are searched recursively; no format choice is
   required. Native QGIS vector/raster providers discover layers, including
   separate layers inside GeoPackages. Common GIS files such as shapefiles,
   GeoJSON, KML, GPX, GeoTIFF and supported CSV geometry are candidates. QGIS
   determines actual readability; not every extension contains map geometry.
3. Create or open an Ag Tech workspace. Review the automatically selected readable
   layers, untick anything unwanted, then click **Import to Field**. All geometry
   must fit inside exactly one field boundary for automatic placement. Matching
   uses native geometry operations and CRS transforms, not centroids, filenames
   or bounding-box overlap. Partial/overlapping matches require a destination.
4. In **Where does this data belong?**, select Organisation → Client → Farm → Field
   or type new names. All four levels are required. Changing a parent refreshes
   its children. For a field outline choose **Field boundary — use to locate future
   imports**. Other polygons default to Other field data. If the CRS is missing,
   choose the file's actual coordinate system; field selection cannot establish it.
5. Confirm with **Use This Field**. Every destination prompt must be accepted before
   this batch adds anything. Cancelling a prompt leaves layers and records unchanged.
   Each new hierarchy path is created transactionally. Existing names are reused
   only within their correct parent, so same-name fields on different farms stay separate.
6. Find the linked native layers under Field → Whole Field → Imported Data.
   Vectors are read-only. Save Map to retain placement and source links. To organise
   a loose layer from 0.7, re-import its source: it is relocated without duplication.
   Already assigned sources are skipped. Failed imports remain in the results.
7. Recognised Deere exports show the client/farm/field structure and catalogue
   items. These are inspection results, not imported hierarchy records. Proprietary
   guidance geometry still needs a verified decoder and cannot be selected for
   Import to Field.
8. Stop Scan cancels discovery. Close also cancels without adding data. A missing
   or inaccessible path reports an error; select another source or retry once the
   NAS is connected. A fresh scan clears old selections.

Data In currently links map layers to their source files. It does not copy them
into the farm GeoPackage, assign seasons, automatically save the map or move/delete
originals. Newly confirmed hierarchy names save immediately to GeoPackage; layer
assignment saves with the QGIS project. Keep source files in place. Managed storage
and per-feature splitting across fields remain subsequent stages. Cross-field data
requires an explicit single destination, never a majority-based guess.

Matching checks complete geometries against unfiltered stored boundaries and
previous imports explicitly marked Field boundary. Empty, invalid, ambiguous or
missing-coordinate data requires a destination. Vector matching is limited to
10,000 features; raster matching uses a densified extent. Placement matching runs
on the UI thread. Linked boundary files must remain available for later matching.

ZIP contents are checked for native GIS candidates using QGIS virtual archive
paths; nothing is extracted. Keep the ZIP in place for linked layers. Deere setup
archives are identified but must be unpacked to preview the complete farm
structure. Nested archives are reported for manual unpacking; encrypted or unsafe
archives are skipped. Limits: 10,000 files per folder scan; 10,000 archive entries
and 512 MiB uncompressed per ZIP. Select a smaller folder/archive if a limit is hit.
Folder links/junctions are skipped to avoid wandering outside the selection.

## Extension design

`import_sources.scan_local` returns plain source/item/warning records; native
provider URIs remain separate from machine metadata. `ImportDialog` displays that
contract and opens validated layer candidates. A cancellable `QgsTask` keeps scans
off the UI thread. Closing/unloading detaches completion callbacks and cancels
the task. Cloud source adapters can feed the same preview later; no cloud login,
network API or synchronisation is implemented now.

`import_placement.py` handles native matching and field-specific layer-tree placement.
`import_destination.py` prepares a destination plan without writes. Generic imports
do not overwrite reference layers or the native workspace boundary tables.

## Current status: 15 October 2026

Deere GS3 2630 is the first target. The plugin includes a read-only inspection
module (`ag_tech_tooling.deere_preview`). It discovers unpacked profile/RCD/EIC
folders, previews XML client/farm/field records and spatial catalogue items,
and retains machine identifiers, parent references, resource references and
catalogue properties. It hashes every source file before and after inspection.
The same machine IDs in different export profiles remain separate.

The metadata inspection service is now used by Data In. It is not a
GeoPackage importer. It does not create organisations, seasons or crops that
are absent from the export. No source data is altered. Source hashes detect
changes during inspection; they are not a backup.

The first supplied NAS sample contained five files: setup XML, spatial catalogue
XML, one binary curved-track resource, a version file and a host file. Metadata
identified one client, one farm, one field and one curved-track item. The installed
QGIS 3.44.14 providers discovered no layers in any of these files. There were no
boundary or recorded operation files in that sample. This observation does not
establish support for every Deere export version.

## Run the inspection

Prerequisites: installed QGIS with its supplied Python runtime; an accessible,
complete export folder. Keep original folder names and all accompanying files.
The developer command below accepts unpacked folders; ZIP scanning belongs to
the Data In source adapter described above.

1. Open PowerShell in the repository root.
2. Run the following, replacing the example source with the complete export:

   ```powershell
   & 'C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat' tools\deere_preview.py '\\NAS\share\export\GS3_2630' --native
   ```

3. Expect JSON with `format: deere_gs3_rcd`, entities, spatial items, issues,
   SHA-256 file inventory and `source_unchanged: true`. Treat `issues` as review
   items. An empty list does not establish geometry import support.
4. If access fails, connect to the share in the same Windows session and rerun.
   If the source changes during inspection, wait until the export is finished,
   then rerun. Linked folders, unsafe resource paths, malformed XML, DTD/entity
   declarations and metadata larger than 10 MiB are rejected or reported.
5. Treat reports as farm data: keep any saved JSON outside this repository.

## Native QGIS and geometry

The optional native probe uses `QgsProviderRegistry.querySublayers`. Layer
discovery is recorded separately from successful conversion; inspection never
inserts geometry into the farm database. Binary `.fdShape` resources are not
standard ESRI shapefiles and this service does not attempt to infer coordinates
from their bytes. Catalogue bounds or reference positions must not be substituted
for the original guidance geometry.

[Deere's offline SDK documentation](https://developer.deere.com/offline-sdk)
describes licensed Deere ADAPT plugins for consuming GS3 display data. Adapter
access, redistribution terms and preserving guidance semantics require evaluation
before integrating that route. No SDK or decoder is included at this stage.

## Next integration work

1. Extend the implemented Data In selector/preview with additional machine adapters.
2. Map imported clients to a selected organisation, preserving machine IDs and
   profile identity. Resolve conflicts explicitly rather than merging by name.
3. Add verified guidance decoding and provenance storage before writing spatial
   data. Use native QGIS providers, transforms and GeoPackage writers wherever
   they support the operation. Retain original machine semantics for future export.
4. Add season mapping only when task dates and recorded operations are present.
5. Extend the existing cancel, retry, duplicate handling and extracted-package
   checks as managed storage and machine decoding are added.

## Checks

Run `tools/deere_preview_test.py` with QGIS Python for synthetic hierarchy,
multi-profile, invalid XML, unsafe/missing resources and source-change cases.
The test accepts `AGTECH_TEST_PLUGIN_ROOT` pointing at an extracted plugin's
parent folder. Keep real machine exports and identifiers out of Git fixtures.
