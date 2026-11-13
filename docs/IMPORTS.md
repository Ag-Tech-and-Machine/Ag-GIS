# Data In

## Reviewed job import (development, 19 October 2026)

1. Select a supported native layer row with an existing field destination and
   click **Preview Job Season…**. Pending new fields have no saved timeline yet.
2. Read the original source/attribute sample, then supply the recorded job date
   and an explicit type. No automatic date/type interpretation is claimed.
3. A preview match requires every season in that field to have valid dates and a
   gap-free, nonoverlapping timeline. Dates are inclusive: 31 March belongs to the
   ending season; 1 April to the adjacent next season. Cross-year ranges work.
4. For a file containing one job, choose **Other data**, then **Use for Import**
   in the preview. This stages a date/type/season decision only for that row; no
   disk write occurs until **Import to Field**. Do not label mixed jobs with one
   date/type: split them first with native tools. No per-feature splitting exists.
5. **Close** cancels changes to the review; **Keep Whole Field** clears its staged
   job binding. Changing destination clears that row's review. Normal imports and
   reference types remain **Whole Field → Imported Data**. Reviewed jobs appear
   under **Seasons → matched season → Operations** and restore there from either
   the saved map or catalogue. Reference data is not moved or reclassified.
6. Import revalidates exact source identity and the full field timeline immediately
   before the metadata transaction commits. A changed source/timeline, unknown type,
   invalid date or conflicting saved duplicate is rejected without reassignment.
   Close/rescan and review again; never invent dates just to satisfy validation.
   Stop keeps prior completed datasets and cleans up the incomplete copy.

The database stores the exact entered job date, source URI/hash, inclusive timeline
snapshot and explicit-selection-v1 rule; unknown units/source attributes remain raw.
No vendor mapping or numerical conversion is claimed. Linked boundary editing and
impacted-history preview remain unfinished. GS3 metadata is not decoded operations.


## File or folder workflow (version 0.12.2)

1. Click **Data In** on the top Ag-GIS toolbar (also available in the
   plugin menu). Choose File or Choose Folder. Selection starts the scan; a pasted
   path can be scanned with Enter or Scan. Local disks and accessible NAS shares
   use the same control.
2. Wait for the results. Folders are searched recursively; no format choice is
   required. Native QGIS vector/raster providers discover layers, including
   separate layers inside GeoPackages. Common GIS files such as shapefiles,
   GeoJSON, KML, GPX, GeoTIFF and supported CSV geometry are candidates. QGIS
   determines actual readability; not every extension contains map geometry.
3. Create or open an Ag-GIS workspace before scanning. Results show **Data → Type →
   Destination → Status**. **Detected** means the complete geometry fits exactly
   one known field boundary using native geometry/CRS operations. Partial or
   overlapping matches, missing CRS and tables say **Please set**. Hover over
   Status for the matching explanation.
4. Open a row's **Destination** dropdown. Existing fields show their full
   Organisation / Client / Farm / Field path and apply immediately. Select
   **Add new field…** to open the inline hierarchy controls with a blank field
   name. Select existing parents or type new ones, then click **Use for This File**
   or **Apply to Checked Files**. Pending new fields appear in the other dropdowns
   before import. Each file keeps its Type. Confirm missing CRS individually in
   this editor; choosing a field cannot establish the file's coordinate system.
5. Manual destinations show **Ready**. Apply pending edits before importing.
   Switching rows preserves drafts. Every checked file needs a destination before
   **Import to Field** enables; untick files to defer them. No destination popups
   are used. Closing/configuration saves no data. Import creates missing hierarchy
   paths transactionally, reusing names only within the right parent. Workspace
   changes require another review before import.
6. Find normal saved copies under Field → Whole Field → Imported Data, or reviewed
   jobs under Seasons → matched season → Operations. Vectors save
   into the GeoPackage; rasters into Data/Rasters. The catalogue retains field/type
   assignments and source details. The map saves automatically after imports.
   Re-import older linked sources to migrate them into managed storage. Unchanged
   source/assignment combinations reuse saved data. Failures remain in the results.
7. Recognised Deere exports show the client/farm/field structure and catalogue
   items. These are inspection results, not imported hierarchy records. Proprietary
   guidance geometry still needs a verified decoder and cannot be selected for
   Import to Field.
8. Stop Scan cancels discovery. Close also cancels without adding data. A missing
   or inaccessible path reports an error; select another source or retry once the
   NAS is connected. A fresh scan clears old selections.

Data In now saves managed copies without moving/deleting originals. See
[Managed saving and filtering](MANAGED_DATA.md) for exact storage, type/field
filters, progress cancellation and recovery steps. Automatic operation decoding,
linked season editing and per-feature splitting remain subsequent stages. Cross-field data requires an
explicit destination, never a majority-based guess. Closing before importing adds nothing; stopping during copying retains earlier completed datasets.

Matching checks complete geometries against unfiltered stored boundaries and
previous imports explicitly marked Field boundary. Empty, invalid, ambiguous or
missing-coordinate data requires a destination. Vector matching is limited to
10,000 features; raster matching uses a densified extent. Placement matching runs
on the UI thread during preview. Saved boundary copies remain available without their originals.

ZIP contents are checked for native GIS candidates using QGIS virtual archive
paths; nothing is extracted during discovery. Successful managed imports no longer
depend on their ZIP. Deere GS3 ZIP archives now preview client/farm/field identifiers
and spatial catalogue directly in Data In without unpacking. Profiles remain separate;
this is metadata inspection, never a geometry import. Nested archives are reported
for manual unpacking; encrypted, linked or unsafe archives are skipped. Limits:
10,000 files per folder scan, 10,000 archive entries and 512 MiB declared
uncompressed bytes per ZIP, with 10 MiB per XML metadata member. Select a smaller
folder/archive if a limit is hit. ZIP archives are checked before and after preview
by SHA-256, and never extracted or modified. These are bounded safeguards, not a
claim that arbitrary hostile ZIPs are safe to open elsewhere.
Folder links/junctions are skipped to avoid wandering outside the selection.

The native GIS and Deere ZIP paths now share `archive_sources.validated_members`.
The complete archive directory is checked before provider inspection. Duplicate
(including case-ambiguous), normalized/backslash, empty/dot-component names are
rejected rather than silently selecting an alias. Catalogue-only GS3 exports are
recognised even without setup.fds; unresolved hierarchy references remain visible.
Synthetic checks cover nested mixed GIS/Deere ZIPs and retain original IDs/units.

## Extension design

### PCT GDP project inspection — 16 October 2026

Data In now recognises `.pctgdp` files selected directly or found in folders.
Expand the identified project to inspect elevation, boundary, region and polygon
layer names. Status remains **Decoder verification needed**; these are not
selectable map imports. The bounded streaming inspector preserves the source and
does not assume a coordinate datum from UTM metadata. See [PCTGDP.md](PCTGDP.md)
for recovered structure, limits, commands and the remaining conversion checks.

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
