# PCT GDP project inspection and recovery notes

Status: 16 October 2026 — **read-only inspection implemented; one elevation grid
validated against a licensed-software export; direct geometry import is not implemented**.
These are observations from one supplied project and synthetic tests, not a vendor
specification or evidence that every `.pctgdp` version is supported. No vendor SDK,
format specification or redistribution permission has been established by this work.
Customer names, coordinates, source paths and payloads are not stored in this document.

## Use Data In

Prerequisites: updated development package loaded in QGIS and an accessible original
project. Do not rename the extension or unpack the source in place.

1. Open **Data In**, then **Choose File** and select a `.pctgdp` project. Choosing
   its containing folder also discovers the project.
2. Wait for the cancellable scan. Recognised containers appear as **PCT GDP project**.
   Expand the project to see its elevation, boundary, region and polygon-overlay
   layer inventory. Hover over a layer's Status to see available units, grid spacing
   and UTM information, followed by the unresolved limitations.
3. Expect **Decoder verification needed**, not Ready or Saved. These rows cannot
   be checked for import. The scanner does not create fields, infer destinations,
   convert grids, write files or change the current map.
4. **Stop Scan** cancels streaming inspection. A malformed/unsupported container
   becomes a source warning. Retain the original and obtain an original-software
   export or additional format evidence; do not change the extension to force import.

No normal-profile installation is implied by changing source/building a ZIP.
Existing standard vector/raster managed import is unchanged.

## Recovered container structure

- The supplied file begins with the ASCII signature `PCTGDP`.
- A ZIP payload begins after a padded header; in the supplied example the first
  ZIP local entry begins at byte 32768. This offset is observed, not hardcoded.
- Its single compressed member has a `.pctgdp` name but contains XML rooted at
  `ProjectVariables`, rather than another project archive.
- The example has five `ElevationLayerVariables`, one `BoundaryLayerVariables`,
  one `RegionLayerVariables` and three `PolygonOverlay` records: ten layer records.
- Layer records retain `Id` and `DisplayName`. Repeated display names are not
  unique identities and must not cause layer merging or inferred field names.
- Grid metadata includes `GridLayer/UtmZone`, `UtmNS`, `PixelSize`, `Origin/X`,
  `Origin/Y`, `NullValue` and a very large `GridString`. Layer-level metadata
  includes `SurfaceType` and `DataUnits`. The sample records metre units and
  half-metre spacing. These are source statements, not independently validated
  horizontal/vertical references.
- Nested boundary records may contain zone zero even though their enclosing layer
  has a zone. Inspection retains the layer-level value rather than overwriting
  it with nested defaults.
- `GridString` contains base64-encoded binary data in this sample. One elevation
  layer's layout, dimensions, quantisation, row direction and NoData mask were
  independently validated below. Other layers/versions remain unverified; this is
  not a vendor decoder contract or an enabled runtime adapter.
- UTM zone and hemisphere alone do **not** establish a coordinate datum or EPSG code.
  Vertical datum is also unresolved. Do not assume WGS84, GDA94, GDA2020 or AHD.
- One boundary layer is not necessarily one field: nested boundaries, inner rings
  and polygon-index arrays require topology reconstruction and validation.

## Bounded inspection and integrity

The supplied compressed project expands to over one gigabyte of XML, so ordinary
whole-document XML parsing is unsuitable for preview. `pctgdp_preview.py` uses
stdlib ZIP streaming and Expat events, discards grid strings and keeps a small
metadata catalogue. It adds no GIS engine or runtime dependency. Native QGIS
provider discovery was exercised and found no readable map layers in this sample;
conversion therefore needs a separately verified format adapter before native
QGIS raster/vector writers can save it into the existing managed workspace.

Limits: one unencrypted safe ZIP member; 2 GiB uncompressed XML; 500 layer records;
one million elements; 64 levels of XML nesting; 64 KiB per non-grid text node.
DTD/entity declarations are refused. Grid text is counted, not retained/decoded.
This specialised preview limit does not relax the generic ZIP scanner's limits.
No archive member is extracted. SHA-256 is checked before and after inspection;
a changing source is rejected. Hash checks are not a backup.

## Developer reproduction

1. From the repository root, run the portable inspector:

   ```text
   python tools/pctgdp_preview.py "X:/exports/Example.pctgdp"
   ```

   Expect JSON with `format`, `layers`, `xml_bytes`, `sha256`,
   `source_unchanged: true` and explicit `limitations`. Reports contain farm data;
   keep them outside Git and public feedback. Errors exit nonzero.
2. Run the synthetic integration test with the installed QGIS Python:

   ```powershell
   & 'C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat' tools/pctgdp_test.py
   ```

   Expect direct/folder recognition, inline preview and safety/cancellation pass
   messages. `AGTECH_TEST_PLUGIN_ROOT` selects an extracted package for the same test.
3. Run `scripts/check.ps1` for the source and extracted-package regression suites.
   Keep test scratch under your tool's configured scratch directory.

## Independent elevation-grid validation — 16 October 2026

1. Export the selected surface with the licensed application's **Export → ESRI
   ASCII** controls to a separate private file. Do not save over the project.
   Retain export, scripts and SHA-256/provenance reports outside Git/public feedback.
2. The observed grid header is a little-endian int32 column count followed by
   three float64 values (base, span, source null marker). Remaining pixels are
   little-endian uint32, row-major, north-to-south. Zero is NoData. Valid heights
   in this sample match `base + (pixel - 1) * span / 4294967293`.
3. Compared every cell against original-software ASCII values: 99,642,532 cells,
   34,447,088 valid heights and 65,195,444 NoData cells. Zero mask mismatches;
   maximum valid-height difference approximately 1.42e-14 metres. Dimensions and
   half-cell placement agreed with the ASCII header, without flipping/reprojection.
4. QGIS 3.44.14 native discovery and the actual Data In dialog were exercised in
   isolation. Selecting a fixture field left the ASCII source at **Please set
   coordinate system**, Import disabled, with no catalogue entry. The existing
   managed raster-copy helper wrote a compressed GeoTIFF; all 99,642,532 cells,
   extent and NoData matched the native reader, and reopening passed.
5. ASCII has no projection. GeoTIFF represents the unknown reference as unnamed
   `LOCAL_CS`, which QGIS considers syntactically valid, but this establishes no
   geographic CRS/datum. The private copy is labelled CRS-unconfirmed; do not
   interpret native validity as permission for real field placement.

Scope: one elevation layer in one project, using private experiment scripts and
retained evidence. No production decoder, normal-profile installation, real field
import, polygon validation or release. Original-project SHA-256 was unchanged.
Agreement with the exporting application does not establish survey accuracy or
horizontal/vertical datum.

## Remaining acceptance before import

1. Extend the independently validated layout to other surfaces/versions and edge
   cases (constant grids, reserved values, malformed lengths and cancellation).
   Build a bounded adapter and regression tests before enabling direct import;
   one private experiment is not broad format support.
2. Establish horizontal and vertical references; when absent, request explicit
   user confirmation in the existing inline editor. Never infer datum from a filename.
3. Validate polygon/inner-ring/index semantics, including multi-part boundaries.
4. Offer verified sublayers through the existing Type/Destination/Status workflow;
   do not treat a project, surface name or boundary layer as a field automatically.
5. Save through native QGIS vector/raster APIs into managed storage, with original
   provenance, cancellation/failure cleanup, repeat-import and package/reopen tests.
