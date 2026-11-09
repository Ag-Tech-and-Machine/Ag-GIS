# Data dictionary and classification mapping — revision 6

Inspected 19 October 2026 against the shared development checkout. This is an
implementation dictionary, not a claim about an installed build or certified
standards support. Core workspace schema remains **2**, dataset catalogue **1**.
The explicit classification contract is independently versioned **1**. Optional
registry storage and the `registered-source-v1` provenance envelope are implemented
as developer APIs; Data In now commits explicitly reviewed whole-dataset job
classification/context using the independent `reviewed-import-v1` envelope.
Core schema 2 and catalogue 1 are unchanged. No automatic manufacturer classifier.

## 1. Actual storage and keys

A workspace contains `Farm.qgz` (native QGIS project, renderer state, layer custom
properties and relative references), `Data/farm.gpkg` (native GeoPackage) and,
when imported, `Data/Rasters/<dataset-id>.tif` plus preserved companion files.
Workspace location comes from the user-selected/default Documents folder; no
machine-specific absolute path is a database contract. Source files stay outside
the managed copy and are not rewritten.

`farm_project.py`, `hierarchy.py`, `managed_data.py` and `dataset_styles.py` are
authoritative writers for their respective native data/application metadata.
`tools/data_dictionary_test.py` creates a synthetic workspace through those real
writers, imports a synthetic vector through the native writer and inspects actual
`PRAGMA table_info`, trigger names and version rows. Core hierarchy/catalogue
application fields below are TEXT, including dates and version numbers; the optional
saved-style table's integer revision is described separately. Native OGR adds an INTEGER `fid`
primary key; this provider row identity is **not** the application's UUID `id`.
Spatial tables also have native `geom` geometry columns with the declared CRS.

| Table | Application columns (all TEXT) | Relationship / meaning |
| --- | --- | --- |
| `agtech_farm` | `farm_id`, `farm_name`, `schema_version`, `crs_authid`, `created_utc` | Single workspace metadata row. `farm_id` is also the initially created farm ID; it is the stable workspace identity, not a current selected-field identity. Validated against QGIS project entries. |
| `agtech_organisations` | `id`, `name` | Root entities. |
| `agtech_clients` | `id`, `name`, `organisation_id` | `organisation_id` → organisations `id`. |
| `agtech_farms` | `id`, `name`, `client_id` | `client_id` → clients `id`. |
| `agtech_fields` | `id`, `name`, `farm_id` | `farm_id` → farms `id`. |
| `agtech_seasons` | `id`, `name`, `field_id`, `start_date`, `end_date` | `field_id` → fields `id`. Dates are ISO dates when supplied; blanks allowed. Existing validation only checks parseability/order, not contiguous adjacent seasons. |
| `agtech_crops` | `id`, `name`, `season_id` | `season_id` → seasons `id`. |
| `agtech_boundaries` | `id`, `field_id`, `name`, `revision` | MultiPolygon reference features → fields `id`. |
| `agtech_guidance` | `id`, `field_id`, `name`, `revision` | MultiLineString reference features → fields `id`. |
| `agtech_infrastructure` | `id`, `field_id`, `name`, `revision` | Point reference features → fields `id`. |
| `agtech_datasets` | See catalogue detail below | Lazily created on first managed import; field-linked; optional classification pointer for deliberately reviewed jobs. |
| `agtech_dataset_styles` | See saved-style detail below | Optional append-only native saved-style recovery, created on verified supported map save with managed datasets present; independent contract v1. |
| `agtech_data_<dataset-id>` | Original vector attributes and native managed identity/geometry | One native provider table per managed vector. Dataset ID is `uuid4().hex`, separate from each feature's original identifiers. |

Hierarchy unique indexes enforce `id` and case-insensitive names within each
parent (organisation names globally). INSERT/UPDATE triggers reject missing
identity/name/parent; parent DELETE/id-update triggers protect child hierarchy
and native reference data. Reference features require valid field links on
INSERT/UPDATE. These are trigger-enforced relationships, not declared SQLite
foreign keys. `revision` is a text field, not an implemented history engine.

The dataset catalogue has a unique `id` index, an INSERT trigger requiring a
valid field and a field DELETE guard. It does **not** currently enforce the same
UPDATE/id-change constraints as the hierarchy. Do not infer stronger integrity
from the logical relationships in this document.

### Catalogue v1 columns

| Columns | Meaning / source mapping |
| --- | --- |
| `id`, `field_id` | Generated dataset UUID hex; explicitly reviewed destination field UUID. |
| `name`, `role` | Source layer name (renameable); reviewed legacy role from `data_types.TYPES`. Roles are reference purpose, not operation families or measured variables. |
| `layer_type`, `provider` | `vector`/`raster`; managed `ogr`/`gdal` provider, not the original manufacturer. |
| `uri` | Relative `Data/farm.gpkg\|layername=agtech_data_<id>\|option:NOLOCK=NO`, or relative raster path. Separators are vertical bars; table-markup escaping is not part of the stored URI. |
| `crs_wkt` | Original layer CRS WKT; not inferred from a filename or operation type. |
| `source_uri`, `source_hash` | Original provider URI; existing source bundle/content SHA-256 identity (includes CRS). Empty when no verified raster content identity exists. Not a manufacturer signature. Source URI may be private: do not publish actual records. |
| `created_utc` | Import time; **not** recorded operation/job time. |
| `style_xml` | Immutable native import-style snapshot. Catalogue recovery prefers the latest supported `agtech_dataset_styles` revision when present, otherwise this original snapshot. Saving native style edits never replaces this import provenance. |
| `catalog_version` | Literal text `1`; reader rejects other row versions. |
| Optional `classification_id TEXT` | Added on deliberate reviewed import, points at that dataset's exact `agtech_classifications.id`. No declared pointer FK; the transaction writer and binding reader validate it. Existing/unreviewed rows remain NULL. |

For vector copies, `QgsVectorFileWriter` retains original attribute names and
adds `_agtech_fid` / `_agtech_geometry` (trailing underscores if those names are
already taken). Original vendor IDs remain attributes, not overwritten primary
keys. Vector attribute **names and counts** are checked at import; that alone is
not an exhaustive assertion of every value/type across every driver.
For rasters the existing copy path preserves GeoTIFF bytes/companions when
possible and checks band/georeferencing metadata for supported conversion.
No new numeric conversion or unit coercion is introduced.

Native GeoPackage support tables (`gpkg_*`, `sqlite_*`, spatial indexes and
provider metadata) are maintained by the native writer. Their presence can vary
with QGIS/GDAL versions and geometry; they are not new agronomic entities.

## 2. New opt-in classification v1 (implemented foundation)

`classification.classify(source, ...)` returns a detached provenance dictionary.
It does not guess meaning from geometry, rate-like columns, filename, date of
import or technical transport type. Caller supplies JSON-compatible source data
and explicit selections; this is not yet a schema-validation or vendor adapter API.

| JSON field | Rule / examples / limitations |
| --- | --- |
| `version` | Integer `1`, separate from core schema and catalogue version. |
| `mapping_rule` | Literal `explicit-selection-v1`: caller-selected meaning, not verified manufacturer decoding. |
| `purpose` | Caller-supplied, default `unknown`; `operation` is required for the new style helper. Existing `role` remains unchanged. |
| `operation_subtype` | Exact supplied token; known local tokens `tillage`, `planting`, `spraying`, `spreading`, `harvesting`; anything else remains verbatim. |
| `operation_family` | `spraying`/`spreading` → `application`; tillage/planting/harvesting → same family; unrecognised token → `unknown`. This is a local explicit-selection mapping, not a universal industry code list. |
| `measurement`, `unit` | Exact supplied strings; defaults blank (not established). No dimensional compatibility check/conversion; a unit alone does not identify rate, yield, depth, product or moisture basis. |
| `semantics` | Caller-supplied, default `unknown`; intended target/actual distinction remains explicit. No target/result inference is implemented. |
| `field_id`, `season_id` | Exact supplied context identifiers, default blank; not validated foreign keys in this API and not automatically assigned. |
| `source` | Deep copy of original JSON-compatible source values/codes; unknown fields retained. Do not put private payloads in public fixtures. |

For the native style foundation, the developer/caller serializes this object to
the QGIS layer custom property `AgTechTooling/classification_v1` in `Farm.qgz`.
This explicit layer property is still separate from the optional durable registry
below: classification rows do not manufacture native styles. Reviewed Data In assigns a
catalogue pointer/context but does not populate this styling property. The saved-style
contract below now preserves native styling/custom properties after a verified map save;
edits never successfully synchronized remain in the saved project only.
Measurement/band bindings and reviewed context edits remain work. New reviewed
imports validate context as described next; low-level classification APIs do not.

`operation_style.apply_operation_style` is a callable developer foundation, not
a new farmer-facing command. It requires an owned vector layer with classification
version 1/purpose `operation`. It builds a native `QgsSingleSymbolRenderer` for a
homogeneous operation dataset, not a per-feature classifier. Local defaults:
tillage brown, planting green, spraying blue, spreading purple, harvesting gold,
unknown grey. Unclassified legacy/reference layers are untouched. Raster styles
and mixed-operation layers are not handled by this helper.

The first explicit application stores `AgTechTooling/operation_style_backup`
(native XML) and `AgTechTooling/operation_style_initialised`. Subsequent calls
preserve native user styling unless `reset=True` is explicitly requested. Native
QGIS Layer Properties/Styling remains available for edits; project save/reopen
retains the renderer. Reset replaces the renderer, so it must only be exposed
behind a deliberate user action. No buttons, automatic import hookup, last-field-
activity selection, graduated measurement view or side-by-side map UI is added.

## 2a. Explicit Data In context and durable reviewed binding — 19 October 2026

The actual **Preview Job Season…** button receives the selected supported native
layer record and its existing field destination. `review_job_season` reads
`agtech_fields`/`agtech_seasons` through `hierarchy.records`; it returns an ephemeral
`season-review-v1` object with field ID, exact entered job date, explicit local
operation subtype/family, matched season ID/name and date-ordered timeline.
Preview alone writes nothing. **Use for Import** stages that object plus source
URI/hash/provider/CRS on the selected row; **Keep Whole Field** clears it, and Close
cancels modal changes. Destination changes clear the draft. No source column is
interpreted; dates/types are an explicit user assertion for the entire dataset.

Matching uses strict `YYYY-MM-DD` calendar dates, inclusive start/end, and requires
every season of the selected field to be fully dated with next-start = previous-end
+ one day. Summer ranges may cross calendar years. Unknown types, missing/invalid
or outside dates, gaps and overlaps prevent matching. Another field's timeline is
never used. The legacy hierarchy writer still permits blank/noncontiguous dates;
this preview does not migrate them or implement linked boundary editing.

The UI reads at most five vector features with native `QgsFeatureRequest`, showing
original attributes without guessing their date/type meaning. Raster preview has
no decoded job metadata. GS3 metadata-only rows are not selectable layer previews.
Closing writes nothing. **Import to Field** passes `review=` into `save_dataset`.
Only legacy role `data` (Other data) permits a job binding; reference types and
unreviewed data remain Whole Field. Mixed jobs require prior separation; there is
no per-feature date/type classification or unsupported proprietary decoding.

The native vector/raster writer creates and validates the managed copy. A SQLite
`BEGIN IMMEDIATE` metadata transaction with foreign keys enabled then validates
the complete current field timeline against the reviewed snapshot and hashes the
source again, inserts the catalogue row, adds optional classification tables/column,
appends the decision and sets its pointer. Source/timeline validation repeats
immediately before commit without Qt event pumping. No source hash means review
cannot be committed (for example unverified virtual raster identity). A source
change while the modal is open also rejects Use for Import.

The decision uses existing classification columns: purpose `operation`, exact local
subtype/family, field/season IDs, blank measurement/unit, semantics `unknown`,
mapping_version `1`, vendor_source `reviewed-import-v1`. This is **explicit local
selection**, not a registered vendor mapping. `source_value` is JSON:

- `contract`: `reviewed-import-v1`.
- `review`: exact `season-review-v1` object, including strict job date, field/season
  IDs, subtype/family, season name and full chronological inclusive timeline.
- `source`: original `source_uri`, `source_hash`, `provider`, `crs_wkt`. Complete raw
  attributes/geometry or pixels/units remain in the managed copy; the sample is not
  substituted for the original dataset.
- `mapping_rule`: `explicit-selection-v1`, `mapping_version`: integer `1`.
- `vendor_mapping`, `unit_mapping`: NULL, explicitly not inferred or converted.

Normal SQL UPDATE/DELETE triggers protect reviewed rows (`agtech_review_no_update`,
`agtech_review_no_delete`), separately from append-only vendor/unit rule guards.
They are integrity aids, not access control against the database owner. Field and
season links are transaction-validated, not new declared FKs. Legacy hierarchy
date edits are still possible; they do not automatically rewrite/import history.

`open_dataset`/`restore_datasets` read the exact catalogue pointer and stored
context, never today's latest rule/timeline. Layers carry `dataset_id`,
`classification_id`, `import_season` custom properties and go under the native
`operations:<season-id>` tree group. Normal project save/reopen and catalogue-only
recovery retain this context. Existing duplicates with different reviewed context
are rejected, not silently reclassified. No default style or latest activity is
applied by reviewed binding; saved native styling uses the independent contract below.

Ordinary failure rolls back the metadata transaction and removes the partial
native table/raster through the existing provider cleanup. Prior completed datasets
and Whole Field references survive. This is not crash/power-loss atomicity across
the native writer and metadata connection; an empty catalogue may remain after a
failed first import. Linked date application with explicit retained history is
implemented as described below; historical reassignment remains unsupported.

Import/export reference: native data exports retain the copied source attributes/
values but do **not** automatically carry classification metadata/timeline/rule
snapshots. No classification export UI is supplied. Keep Farm.qgz and the entire
workspace/Data catalogue together for context preservation; consumers must retain
the contract envelope and exact pointer rather than resolve history again.

## 2b. Native saved-style recovery v1 — 19 October 2026

`dataset_styles.py` uses native `QgsMapLayerStyle.readFromLayer/writeToLayer` for
managed vector/raster styles. `FarmActions.attach/detach` pairs its write/read/save/
clear signal connections. Ordinary project reopen retains the project's own edits;
`restore_datasets` skips layers already present, never replaces them with catalogue
styling. Missing-layer/catalogue-only reconstruction prefers the latest supported
saved-style revision and marks its presentation initialized so generic themes cannot
replace it. Legacy catalogues without this optional table retain their old behavior.

| Table / column | Type and actual meaning |
| --- | --- |
| `agtech_dataset_styles.dataset_id` | TEXT NOT NULL; catalogue dataset ID, declared FK to `agtech_datasets(id)`. Writer enables foreign keys. |
| `revision` | INTEGER NOT NULL; increasing per dataset, composite primary key `(dataset_id,revision)`. |
| `contract` | TEXT NOT NULL; literal `native-saved-style-v1`, independent of schema 2/catalogue 1/classification 1. Unknown latest contracts refuse recovery/sync rather than fall back silently. |
| `style_xml` | TEXT NOT NULL; opaque native XML from the saved managed layer, including native serialized style/custom properties. Source/import snapshot and classification provenance rows remain unchanged. |
| `project_sha256` | TEXT NOT NULL; SHA-256 of the verified final Farm.qgz archive associated with the revision; not a signature or source-data hash. |
| `saved_utc` | TEXT NOT NULL; UTC synchronization timestamp, not job/operation time. |

1. Native `writeProject` captures style snapshots and adds a unique `aggisStyleSave`
   attribute to the QGIS document root. `projectSaved` queues synchronization for
   the next event-loop turn: on QGIS 3.44 this signal occurs before the outer QGZ
   replacement has finished. The final archive must contain exactly one QGS with
   that receipt before any metadata is committed. A receipt-only prepared document
   is not proof of a save. An unsaved edit after capture cannot leak into recovery.
2. A SQLite `BEGIN IMMEDIATE` transaction appends revisions for present managed
   dataset layers only. Workspace ID, native decoded provider path/table and unique
   dataset occurrence must match. Unrelated/native reference layers are untouched.
   Duplicate layer copies, changed identities, locked storage and stale revisions
   warn and retain previous recovery styling; the native map is not silently restyled.
3. At project read/attach the controller observes latest revisions only when their
   recorded project hash matches this map. An older, externally saved or unobserved
   map is not consent to supersede newer history. Compare-and-append under the
   transaction rejects a competing session advancing history after observation.
   This protects recovery styling, **not** concurrent editing of the map file itself.
4. `agtech_styles_no_update/no_delete` guard ordinary SQL history mutation; these are
   integrity aids, not security against the database owner. Every supported save
   appends a snapshot, including unchanged styles; no pruning, history-selection or
   conflict-resolution UI is implemented. After a conflict keep both the saved map
   and complete workspace for review; do not delete rows or force a replacement.
5. Plugin unload flushes any finalized pending receipt then disconnects all signals.
   Invalid/failed archive saves never advance styling. The QGZ save and GeoPackage
   synchronization are **not crash-atomic**; a warning means the project can contain
   newer styling than recovery. Edits made/saved without this build must not be
   advertised as catalogue-protected. External SVG/fonts and other native style
   dependencies are not bundled by serializing XML; keep required assets separately.

This adds no unit conversion, vendor interpretation, source geometry/attribute edit,
new farmer style controls or automatic operation theme. Existing explicit operation
reset stays deliberate; once saved, its native result is durable too. Broader mixed/
measurement styling and historical reassignment remain unfinished. Restore
requires the entire supported workspace and dependencies, not merely an exported
spatial layer. Test through QGIS Python: `tools/dataset_style_test.py` in source and
extracted packages; visible branded acceptance and artifact identity are separate.

## 2c. Linked season boundary review and decision v1 — 19 October 2026

Manage Data → **Preview Season Boundary…** uses native Qt date/calendar/trees.
Preview remains read-only: `season-boundary-preview-v1`, strict field-local dated
chronological timeline, inclusive endpoints, following start = selected end + one
day, fixed outer endpoints, at least one day each. Unknown/missing history and
stale/gapped/overlapping/undated timelines refuse. Whole Field/unreviewed datasets
are counted/excluded, never assigned dates by filename or import timestamp.

Preview fields: `field_id`, `workspace_id` (agtech_farm.farm_id), `left_season_id`,
`end_date`, `timeline`, `proposed_timeline`, `history`, `affected_count`,
`date_match_changed_count`, `unreviewed_count`, `read_only: true`, `snapshot_sha256`.
History retains classification/dataset IDs/name, original job date/type, immutable
recorded season, current date match, proposed match and independent `affected`
(proposed versus recorded) / `date_match_changed` (proposed versus current) flags.
The SHA-256 covers the complete field catalogue, classification and earlier boundary
receipt rows plus workspace identity; full timeline equality is checked separately.
It is an internal stale-review guard, not an authentication signature.

**Apply Both Dates…** requires an unchecked retain-history acknowledgement and a
Cancel-default confirmation. Date/refresh changes clear acknowledgement. The only
supported decision is literal `retain-recorded`; historical reassignment is NOT
implemented. On apply, `BEGIN IMMEDIATE` + foreign keys establishes one metadata
transaction. Recompute/compare the exact reviewed preview including old receipts;
reject stale/replayed/altered consent. Reopen all reviewed original local ogr/gdal
sources using native QGIS, apply their recorded CRS interpretation, and recompute
the existing managed source/bundle hash. Changed, missing, virtual/non-local or
unsupported sources refuse application, not preview. Restore the original files
at their recorded locations and review again. No source/provider write is issued.
There is no external filesystem lock or distributed/multi-user transaction claim.

Both aspatial `agtech_seasons` date updates and the audit insert commit together.
A failed second date or audit write rolls back both; busy storage refuses. Core
schema2/catalogue1/classification1 stay unchanged. Preview/Close/Cancel create no
table and preserve full GeoPackage/project/source bytes. Successful application
writes only the two metadata rows and optional audit schema/row; it does NOT save
Farm.qgz, rewrite source/geometry/attributes/classification/import provenance,
append styles or move historic jobs/native layers. Metadata dates survive native
save/reopen, cold restart and catalogue-only reconstruction independently of QGZ.

| Optional table / column | Actual type, keys and meaning |
| --- | --- |
| `agtech_season_boundary_decisions.id` | TEXT PRIMARY KEY, generated UUID; one accepted boundary decision. |
| `contract` | TEXT NOT NULL; literal `season-boundary-decision-v1`, independent version. Unknown field decision contracts refuse further preview/application. |
| `field_id` | TEXT NOT NULL; validated field identity, not a declared FK. |
| `created_utc` | TEXT NOT NULL; ISO timestamp with UTC offset, decision time not job date. |
| `decision_json` | TEXT NOT NULL; sorted JSON `{id,contract,created_utc,history_decision,review,verified_sources}`. `review` is the exact complete preview with old/new timeline, job impacts and stale fingerprint. `verified_sources` contains each classification ID and freshly verified original source hash. Immutable original source URIs/raw values/rules remain in reviewed-import rows, not replaced by this receipt. |

`agtech_boundary_no_update/no_delete` guard ordinary SQL history mutation, not
security against a database owner. Reversing dates requires a fresh compensating
review/decision; no delete/undo-history control. Keep the complete GeoPackage,
project and dependencies for recovery/export; spatial layer exports alone do not
carry the decision history. No crash-atomic guarantee across map/style/external
files. Reassignment, general history/conflict UI and broader style/latest activity
acceptance remain open. Tests: `tools/season_boundary_test.py`, both source and
extracted packages; actual branded desktop evidence is separate from native APIs.

## 3. Durable classification registry and audit contract (19 October 2026)

`classification_registry.ensure_classification_tables(connection)` explicitly adds
three nonspatial SQLite tables to the native `Data/farm.gpkg`. It does not run on
ordinary preview/unreviewed import, seed mappings, change original attributes or bump core/
catalogue versions. Native QGIS remains the GIS writer/provider and renderer engine;
Python sqlite3 accesses these application metadata tables only, not spatial data.
The tables are not registered as separate GeoPackage feature layers.

| Table | Actual columns/types and keys | Semantics |
| --- | --- | --- |
| `agtech_classifications` | `id TEXT PRIMARY KEY`, `dataset_id TEXT NOT NULL`, `purpose TEXT NOT NULL DEFAULT 'operation'`, `operation_family TEXT NOT NULL`, `operation_subtype TEXT NOT NULL`, `measurement TEXT`, `unit TEXT`, `semantics TEXT NOT NULL DEFAULT 'unknown'`, `field_id TEXT`, `season_id TEXT`, `source_value TEXT`, `created_utc TEXT NOT NULL`, `updated_utc TEXT`, `mapping_version INTEGER NOT NULL DEFAULT 1`, `vendor_source TEXT` | Dataset history, generated UUID string. Declared dataset FK → `agtech_datasets.id`; enforced only when the connection enables `PRAGMA foreign_keys=ON`. Field/season strings are not validated FKs. Dataset/field/semantics indexes exist. |
| `agtech_vendor_mappings` | `id INTEGER PRIMARY KEY AUTOINCREMENT`, `name TEXT NOT NULL`, `version INTEGER NOT NULL DEFAULT 1`, `source_type TEXT NOT NULL`, `rules_json TEXT NOT NULL`, `created_utc TEXT NOT NULL`; UNIQUE `(name,version,source_type)` | Exact vendor token → `{operation_family,operation_subtype}`. Nonempty string keys/values validated on registration. No manufacturer list is preloaded. |
| `agtech_unit_registry` | `id INTEGER PRIMARY KEY AUTOINCREMENT`, `name TEXT NOT NULL`, `version INTEGER NOT NULL DEFAULT 1`, `vendor_source TEXT NOT NULL`, `unit_token TEXT NOT NULL`, `standard_name TEXT NOT NULL`, `category TEXT`, `description TEXT`, `created_utc TEXT NOT NULL`; UNIQUE `(name,version,vendor_source,unit_token)` | Registered interpretation label, not a conversion. Current registration uses name `default`; exact token/vendor isolation. |

`ensure_catalogue_has_classification_column` adds nullable `classification_id TEXT`
to an existing dataset catalogue when explicitly called. Existing rows stay NULL;
there is no FK; the reviewed import writer now assigns/validates that pointer in
its own transaction. The normal native writer still
writes catalogue version `1`. The low-level `classify_with_storage` preserves its
existing explicit-selection signature: caller values, caller `mapping_version`
(default 1), and raw source text are stored without checking a rule. Its version
must not be mistaken for a verified registry rule or the classification contract.
`apply_classification_to_style` remains a stub returning False, not a supported
style restoration path.

### Rule selection, correction and provenance

1. Register with `register_vendor_mapping(conn,name,source_type,rules)` or
   `register_unit(conn,vendor_source,unit_token,standard_name,category,description)`.
   Registration appends `MAX(version)+1` independently per named vendor rule-set,
   or per named vendor unit token. Existing IDs, versions and rows are not replaced.
   UPDATE/DELETE triggers reject rewriting registry history through ordinary SQL;
   these are integrity aids, not a security boundary against a database owner.
   Registration/storage APIs commit their changes; caller-owned outer transaction
   composition is not supported by this helper contract yet.
2. `lookup_vendor_mapping(token,vendor,conn=...,name='default',version=None)`
   reads only that database/vendor/name. Omitted version selects the latest entire
   rule-set; a token removed in that version stays unknown (no older-rule fallback).
   Supplying `version` pins the historical rule. Tokens are case/whitespace exact;
   source tokens are never lowercased. Unit lookup uses the same keywords, selects
   the latest version of that vendor/name/token and returns `standard` (the stored
   `standard_name`), category and description. Both return mapping row ID, name,
   version, vendor and original token. Missing connection/table/token/version/vendor
   returns None, never a global hardcoded fallback or an inferred meaning.
3. `classify_source_with_storage` accepts caller-reviewed source, operation token,
   unit token and optional context. It resolves both registries, storing the exact
   JSON source plus original tokens and detached resolution snapshots in
   `source_value`: `{contract:'registered-source-v1',source,operation_token,
   unit_token,operation_mapping,unit_mapping}` (JSON uses double-quoted keys).
   Each snapshot retains its own rule ID/name/version/vendor/token plus resolved
   meaning; later registrations do not reclassify saved records. `mapping_version`
   column is the operation rule version, or 0 if unresolved; the unit's independent
   version lives in the JSON snapshot. Unresolved family is `unknown`, subtype/unit
   preserve the exact supplied token, absent subtype becomes `unknown` and absent
   unit is blank. Full missing/unknown source information remains in the envelope.
   No source numeric value is rewritten. This is a reviewed-metadata storage API,
   **not** evidence of a Deere operation decoder or a farmer-facing import UI.
4. Export consumers must retain both raw source and snapshots and distinguish raw
   low-level source text from this contract-tagged JSON. Never resolve saved records
   again against today's latest rules to describe their original interpretation.
   No classification export UI/writer is implemented; this is the auditable contract
   for future import/export work, not an available export feature.

### Units, styling and conversion ledger

| Contract / version | Implemented transformation | Preserved / limitations |
| --- | --- | --- |
| `explicit-selection-v1`, classification JSON version 1 | Explicit local subtype → family as listed above | No vendor/measurement/unit inference; source deep-copied. |
| Registered database rules, integer versions per vendor/name | Exact registered token → reviewed family/subtype or unit label | Rule identity and source in `registered-source-v1`; no cross-vendor fallback, arithmetic, dimensional validation or numeric conversion. |
| Ambiguous `gal1ac-1`, `gal1ha-1` | **No bundled mapping or conversion** | Preserve token. US/Imperial gallon basis cannot be guessed; even a registered label supplies no conversion factor. |
| Native homogeneous operation style, classification v1 gate | `QgsSingleSymbolRenderer`, tillage `#a6763e`, planting `#2e8b57`, spraying `#2878b5`, spreading `#9b59b6`, harvesting `#d99b19`, unknown `#777777` | Opt-in helper only. Original native XML backed up once; user edits respected until explicit reset. Project and supported saved-style recovery revisions retain native styles, not classification registry rows. No mixed-feature/measurement view, latest activity or automatic operation-theme import hook. |
| Native managed vector/raster copy, catalogue v1 | Existing native provider/writer path only, as above | Original attributes/CRS retained under existing supported-copy checks. This increment adds no reprojection, resampling, rate/yield/moisture conversion or supported proprietary geometry. |

## 4. Source contracts and primary-source investigation

Retrieved 19 October 2026 using official-source search content after the configured
URL extraction backend reported unsupported extraction. These are documented
contracts, not hands-on imports, endorsements or conformance claims. Code tokens
below are copied exactly; candidate mappings are **not implemented**.

| Source | Verified documentation distinction | Current storage / mapping status |
| --- | --- | --- |
| Existing Deere GS3 preview (`deere_preview.py`, `deere_zip.py`) | Local parser recognises setup/catalogue namespaces. Entity `erid`, `clientRef`/`farmRef`, original attributes; spatial `eridFieldRef`, resource, original properties are preview evidence. | Read-only report only. No insertion into hierarchy/classification tables; proprietary geometry remains unsupported. Do not equate this with Operations Center API support. |
| Deere Field Operations | Operations and measurement types are separate; target and result measurements differ. Official examples include `seeding`, `application`, `harvest`, `tillage`, `SeedingRateTarget`/`SeedingRateResult` and unit tokens `l1ha-1`, `gal1ac-1`. | Candidate: seeding → planting; harvest → harvesting. `application` **does not establish spraying versus spreading**. Preserve exact measurement code/unit and require documented units/product basis before conversion. No API/cloud client or automatic mapping exists. |
| AgGateway ADAPT Standard Operation / Variable | Operation includes Operation Type Code, Variables and Time Scopes. Variable has Definition Code and GeoParquet Column Name / GeoTIFF Band Index. | Candidate separate operation + definition + band/column binding, not a single flat type. No ADAPT decoder or code-list crosswalk implemented. Legacy ADAPT Framework and current Standard must not be treated as interchangeable support claims. |
| AEF TC-BAS / TC-GEO | TC-BAS documents totals exchanged using ISO-XML; TC-GEO adds location-dependent/as-applied and prescription handling. The AEF FMIS test describes ISOXML processing/creation and map handling. | Task-controller capability is not an agronomic subtype. Need actual payload and authoritative data-dictionary/units to interpret source process codes. No ISOXML decoder, DDI mapping or AEF certification claimed. |
| agrirouter Message Types | Technical message types identify payload contracts; endpoint capabilities use TMTs, routing uses broader information types. Examples: `iso:11783:-10:taskdata:zip`, `iso:11783:-10:device_description:protobuf`, `iso:11783:-10:time_log:protobuf`, `shp:shape:zip`. | Routing/container type is not spraying/planting/rate/yield classification. Inspect content separately. No connection, upload, protocol implementation or compatibility certification added. |

Primary references (retrieved observation date above; follow current official
versions before implementing adapters):

- Deere: <https://developer.deere.com/dev-docs/field-operations>
- ADAPT Operation: <https://adaptstandard.org/docs/operation>
- ADAPT Variable: <https://adaptstandard.org/docs/variable>
- AEF functionalities: <https://www.aef-online.org/aef-tour/>
- AEF FMIS TC-GEO: <https://www.aef-online.org/aef-news/tc-geo-conformance-test-fmis.html>
- agrirouter payload types: <https://agrirouter.com/en/docs/message-types>

These sources support separating transport, operation and variable semantics;
they do not establish a universal cross-vendor mapping or grant implementation
rights for proprietary formats. Licences, full code lists, unit bases and actual
payload interpretation remain to verify before adapters are enabled.

## 5. Verification and next steps

1. Run `py tools/classification_test.py`, `py tools/classification_registry_test.py`
   and `py tools/classification_resolution_test.py` for explicit classification,
   additive storage, exact database resolution, immutable registry history and raw
   source/version preservation. Portable tests do not validate QGIS.
2. Through QGIS's bundled Python run `tools/operation_style_test.py` and
   `tools/data_dictionary_test.py` and `tools/data_in_test.py`. The dictionary test
   exercises the registry against a real native-writer GeoPackage and reopened
   database, not just a hand-built fixture. Data In asserts actual folder/ZIP Deere
   metadata has no operations and retains source IDs/unknown units; it does not
   invent an operation decoder. Set TEMP/TMP/TMPDIR to an isolated scratch
   location. The latter can write synthetic schema JSON with
   `AGTECH_DICTIONARY_REPORT`; no user database is needed.
3. Build with `tools/build_plugin.py`; run the same tests against extracted ZIP
   contents using `AGTECH_TEST_PLUGIN_ROOT`. Both source/package inventories
   include these checks. See WORK_LOG for this run's actual results.
4. Next: deliberate historic reassignment/history-conflict review;
   reviewed vendor payload/measurement bindings; deliberate native style/edit/
   reset controls; raster/mixed-operation/measurement views and latest activity.
   Preserve original attributes, custom styles and legacy catalogue readers.

A passing helper test is not evidence of a discoverable farmer workflow, cold
restart, installed EXE parity or the still-open desktop acceptance task.
