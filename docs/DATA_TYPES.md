# Intelligent data handling proposal

Status: proposed next increment, 15 October 2026. This document does not describe
additional implemented import behaviour. Current Data In discovers vector/raster
sources, places linked layers by field, and supports explicit polygon boundary
designation. It does not yet classify agronomic datasets, copy data into managed
storage, map measurement attributes or assign seasonal datasets.

## Farmer workflow

1. Choose a file or folder using Data In.
2. Preview each dataset with an icon, suggested farming type, destination and any
   missing details. Keep technical inspection under an expandable Details control.
3. Accept or override the suggested type. Explain its evidence; an extension or
   plausible value range alone is not proof of meaning. Unknown data remains Other.
4. Ask only for required missing metadata: value column/band, units, acquisition
   date, season/crop or CRS as applicable. Do not invent these from import time.
5. Locate/confirm the destination, then import and apply a suitable native QGIS
   style. Type identification must also run when a boundary match finds the field;
   location does not establish whether a layer is a boundary, prescription or yield.

## Initial catalogue

| Farming type | Possible representation | Handling to build |
| --- | --- | --- |
| Field boundary | Polygon/multipolygon | Deliberate boundary designation, validity/overlap checks, outline style |
| Guidance | Lines; machine-specific setup | Distinguish guidance from travelled tracks/drains; retain machine semantics |
| Assets and drainage | Points, lines, polygons | Asset categories and clear native symbols |
| Soil/survey samples | Points and attributes | Choose measurement/units; preserve other measurements, depths and dates |
| Management zones | Categorical polygons or raster | Keep class identities and labels; discrete colours |
| Prescription | Vector zones/points or raster | Product, target-rate field/band and units; season/plan context |
| Recorded operations | Points/lines/polygons or raster | Distinguish actual values from targets; operation date, units and season |
| Elevation/terrain | Numeric raster, surveyed points or contours | Confirm height units and vertical datum; elevation style, optional hillshade later |
| Aerial imagery | RGB/RGBA raster | Respect band/alpha metadata and NoData; natural-colour display |
| Multispectral/vegetation | Multiband or index raster | Require known band meaning/index; retain acquisition date and scale/offset |

These are roles, not exclusive file formats: yield and soil data, for example,
can be represented by points, zones or grids. Geometry constrains valid roles but
does not establish farming meaning. A generic polygon must not become a boundary
merely because it is a polygon. A single-band floating-point image is not proof
of elevation; three bands alone do not establish RGB imagery.

## Shared inspection and type registry

Add one packaged registry describing stable type IDs, labels/icons, permitted
geometry/raster representations, required metadata, allowed hierarchy scopes,
native style defaults and future validation/export rules. Keep proposed types
separate from types with implemented handlers; do not show unimplemented conversion
or machine export as available.

Inspect vectors with native layer/provider APIs: geometry (including Z/M), CRS,
attributes/types, counts and a bounded sample of values. Inspect rasters with
native raster providers: CRS/extent, dimensions/resolution, bands/colour roles,
sample type, NoData, scale/offset and available units/metadata. Statistics should
be labelled sampled versus exact. Keep expensive reads cancellable and in
background work; initial scans must not calculate full statistics on huge imagery.

Suggestions should record candidate type, evidence and certainty category
(identified from a supported schema, suggested from clues, unknown). Prefer known
vendor schemas and explicit metadata. Filenames/column names are weak clues;
do not present invented numeric confidence percentages as measured accuracy.

Record original measurement/band, units and any explicit conversion. Preserve
source attributes, machine IDs, acquisition dates, raw values and processing
history. Display preferences must not reinterpret stored units. Native QGIS handles
geometry operations, raster rendering, coordinate transforms and Processing.

## Placement and data quality

Reusable references belong to Whole Field; dated operations and prescriptions
need explicit season/plan/operation context. An observation can retain its actual
date without forcing it into a crop season. Farm-wide imagery/terrain should
eventually support shared scope or multiple field associations rather than being
forced into one field. These require deliberate dataset relationships beyond the
current single-field linked-layer implementation.

Report invalid geometry or uncertain CRS; any repair produces a derived result,
preserving the source. CRS assignment and coordinate transformation are separate
operations. Preserve Z/M and vertical reference where meaningful. Raster NoData
must not be treated as zero. Categorical resampling must not invent intermediate
classes; continuous-value resampling requires an explicit task-appropriate method.
Do not silently clip, resample, interpolate, calculate an index or change units
while merely classifying an import.

## Storage

GeoPackage remains the core vector/relationship/catalogue store. Raster storage
needs a tested policy for imagery versus numeric grids. Ordinary image tiles and
gridded coverage extensions have different capabilities. Test precision, NoData,
bands, units and interoperability before writing numeric elevation/rate rasters
into GeoPackage. Managed lossless GeoTIFFs within the packaged workspace are a
possible alternative for unsuitable/large raster types, not an adopted change to
the current storage choice. A farmer should still open/share one managed project.

## Delivery order and acceptance

1. Native metadata inspection and the shared type registry; editable type badges
   in Data In, including for automatically located layers. Preserve unknown types.
2. Targeted value/unit/date prompts and native styling. Route supported reference
   types into useful categories; implement season relationships before seasonal
   import becomes an active option.
3. Managed storage, provenance and multi-field relationships; then task-specific
   conversion and export adapters. Test numeric round trips before raster migration.

Use synthetic point/line/polygon/Z/M fixtures; ambiguous or misleading names;
RGB, scaled numeric, NoData and categorical rasters; unknown units/CRS; same type
in vector and raster forms; auto-located layers; cancellation and saved project
reopen. Verify handlers and icons from the extracted plugin package. No tests were
run for this design-only document and no runtime behaviour changed in this step.

## Primary references

- [QGIS raster properties and rendering](https://documentation.qgis.org/3.44/en/docs/user_manual/working_with_raster/raster_properties.html)
- [QGIS raster alignment and resampling](https://doc.qgis.org/3.44/en/docs/user_manual/processing_algs/qgis/rastertools.html)
- [QGIS native vector geometry tools](https://docs.qgis.org/3.44/en/docs/user_manual/processing_algs/qgis/vectorgeometry.html)
- [GDAL GeoPackage raster capabilities, including gridded coverage](https://gdal.org/en/stable/drivers/raster/gpkg.html)
