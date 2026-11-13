# Organisation, Client, Farm and Field — data model

15 October 2026. Version 0.6.0 implements the hierarchy foundation in schema 2. Remaining workflow/history design is labelled below. Existing schema 1 projects stay readable and are upgraded through a separate copy, not an in-place migration.

## Implemented in 0.6.0

- Native QGIS attribute tables: `agtech_organisations`, `agtech_clients`, `agtech_farms`, `agtech_fields`, `agtech_seasons`, `agtech_crops`. Each has stable `id` and `name`; children carry their parent's ID. Seasons also have optional ISO start/end dates.
- Native shared spatial layers: `agtech_boundaries` (MultiPolygon), `agtech_guidance` (MultiLineString), `agtech_infrastructure` (Point), with `id`, `field_id`, `name` and `revision`. IDs have unique indexes; parent links and nonempty identities are guarded by database triggers installed via the QGIS provider connection. Hierarchy names are unique within their parent (case-insensitive checks).
- One-click New Project generates Organisation 1 → Client 1 → Farm 1 → Field 1 → Seasons → Season 1 in a Documents workspace, with editable starter labels. Native Layers shows the full hierarchy as separate short levels, including all clients/farms/fields/seasons. The menu-only options form retains explicit setup. Manage Data supports add/rename, a full icon-labelled hierarchy, Whole Field/Seasons grouping, season/crop records and selected-field native layer filtering.
- Schema 1 upgrade-copy support uses a SQLite storage snapshot, native QGIS schema creation/writes and validation. The original is retained unchanged; reserved table conflicts are refused. The original farm UUID becomes the first farm ID, and remains the workspace identity for compatibility.
- Unrelated map layers are retained; three shared reference layers are reused across fields and after moving/reopening the project. Map context is saved through QGIS Save Map. Hierarchy changes save immediately to GeoPackage.

Seasonal dataset editors, terrain storage/import, jobs/prescriptions, automatic revision history, external-ID mapping workflows, toolbar dropdown selectors, deletion/reparenting and multi-user locking are not implemented. Planning/operations/results rows currently organise the tree; they do not imply those dataset tools exist. Show Field displays Whole Field references, not a season-specific dataset filter.

## Direction

The user selected **Organisation → Client → Farm → Field** as the hierarchy to support from the outset. All four are first-class entities in the planned model. Organisation means the business managing the workspace; Client means the grower/customer whose farms are managed. Farm means a named property or management grouping; Field means a persistent working land unit (which may be labelled Paddock for local users).

```text
Organisation: Ag Tech
  Client: Smith Farming
    Farm: Home Farm
      Field: North 40
      Field: Creek Paddock
    Farm: River Block
      Field: East Pivot
  Client: Jones Farming
    Farm: Home Farm
      Field: North 40
```

One organisation can contain several clients; one client can contain several farms; one farm can contain several fields. Do not equate a software project/package with one physical farm. A project is the workspace the farmer opens. The current one-farm workspace is a foundation and will need a deliberate, versioned migration before managing this hierarchy.

## What the reference platforms show

| Platform | Verified pattern | Lesson for Ag-GIS |
| --- | --- | --- |
| John Deere Operations Center | The field API operates within an organisation and relates fields to clients and farms. Deere's display help documents Client → Farm → Field, with optional grouping levels. | Keep account/organisation identity distinct from the Client/Farm/Field names exchanged with machines. |
| Ag Leader SMS | Management items include Grower, Farm, Field and Year; SMS Advanced analysis filters include Grower, Farm, Field, Year and Operation. Its management tree also offers task/calendar views. | Familiar land hierarchy and alternate time/task views should access the same records. |
| PTx FarmENGAGE | Organisation setup is separate from field resources. The public API overview lists Client/Farm/Field, boundaries, guidance lines and landmarks. Organisation and user unit preferences have different roles. | Separate business context, land resources and user display preferences. |

This is a comparison of public documentation, not a reverse-engineered database schema or a claim that the three products have identical models.

## Client/Grower support

Client is required in the planned core model from the outset, rather than deferred to a contractor add-on. Grower is an external-platform term to map to Client as appropriate. Do not silently equate a Deere organisation ID with its client ID, or collapse several external growers into one record because names match.

For an owner-operator, Organisation and Client may have the same display name but remain separate records with stable IDs. A simplified setup can prefill the client name for confirmation; it must not remove this level or silently assign ownership. A default selection can save repeated navigation for single-client users. An Ag Tech workspace is not itself an authentication or permission boundary, and this local hierarchy does not implement user access controls.

Use explicit parent links: Client → Organisation, Farm → Client and Field → Farm. Names are labels rather than identifiers; farms/fields with identical names under different clients must remain distinct. Preserve external account/client identifiers separately. Client reassignment, sharing and transfers need deliberate rules before implementation so historical work is not silently reattributed.

## Land, time and work are related dimensions

### Within each field: Whole Field and Seasons

The user confirmed this organising direction: reusable field data belongs under **Whole Field**, while crop/season-specific data belongs under **Seasons**. These are interface groupings over related records, not separate copies of the field or a requirement for one database table per branch.

```text
Field: North 40
  Whole Field
    Boundaries
    Guidance Lines
    Terrain & Drainage
    Infrastructure & Reference Data
  Seasons
    2026 — Winter
      Wheat
        Plans & Prescriptions
        Operations & Jobs
        Observations & Results
    2027 — Winter
      Canola
        Plans & Prescriptions
        Operations & Jobs
        Observations & Results
```

**Whole Field** holds reusable spatial/reference data: boundary revisions, master AB/guidance lines and patterns, terrain/surveys, drainage/infrastructure and baseline reference layers. Whole Field describes the data's field-wide/reusable scope, not a promise that it never changes or covers every square metre. Preserve dates, sources and revisions where appropriate. A dated soil test or imagery capture can remain a dated observation even when used as a reference across seasons.

**Seasons** holds named crop cycles, associated crops or crop areas, plans/prescriptions, planting/application/harvest records, scouting/observations, jobs and results. Use season IDs plus dates/labels rather than making calendar year the only key. Support more than one crop cycle per year and more than one crop/crop area within a field; a single-crop field should still look simple. The illustrative crop branch can be collapsed for the common single-crop case. Field/season-level work need not be assigned to a crop when that would be misleading.

Master guidance lines belong to Whole Field. A season/job can select a particular guidance revision and record its working offset, implement width or other setup. Changes must not silently replace the master or alter historical work. Similarly, preserve which boundary revision was used for a prescription or operation. Make deliberate promotion of a season-specific improvement into reusable field data recoverable.

Whole Field/Seasons and season/crop records are implemented in the Manage Data tree. When seasonal dataset workflows are added, Whole Field references should remain available alongside the selected season. An **All seasons** comparison view and historical revision links remain planned. Keep the map central.

- Keep field identity independent of seasons and geometry. A renamed field retains its ID.
- Store boundary revisions against a field, with validity/source details. Splits and merges need lineage rather than silently reusing an old identity.
- Relate seasons/crop cycles to fields; do not duplicate field records every calendar year. Season labels and dates must allow local cropping practices.
- Relate jobs/tasks to one or more fields. A job can carry input datasets, processing parameters, outputs and status.
- Store permanent boundaries, guidance, terrain and assets separately from dated observations, operations and results. Organisation-wide or farm-wide datasets need not be forced onto a single field.

## Proposed GeoPackage approach

Use shared tables/layers with stable IDs and explicit relationships, rather than a table or file for every field or year. Candidate entities are organisations, clients, farms, fields, field-boundary revisions, seasons/crop cycles, jobs, job-field links, datasets and external identifier mappings. These names and columns are provisional.

Schema 2 uses one managed GeoPackage per workspace and can hold multiple organisations, each with clients, farms and fields. New Project starts with one organisation; Manage Data can add more. Keep this relationship model independent of later selected-organisation/client/farm sharing packages. The GeoPackage is the core store while the full workspace still contains QGZ and supporting files.

Store external platform IDs separately from internal UUIDs, keyed by platform, external account/organisation, entity type and external ID. Import matching must distinguish IDs, names and geometry; show unresolved or conflicting matches for review. Export presets must explicitly map Organisation/Client/Grower/Farm/Field terms and report unsupported content.

Use native QGIS layers/providers/writers, relations and forms for editing and presentation. Define database constraints and migrations deliberately; QGIS form validation alone is not protection against external edits. Use QGIS coordinate transformations and Processing for GIS operations. Record CRS, vertical datum where relevant and physical units with data; a user's display-unit preference must not reinterpret stored values. Organisation defaults, project settings and user preferences need explicit precedence.

## Interface first

Keep map and Layers as the primary workspace. Proposed controls belong in the existing top toolbar or focused dialogs:

1. Organisation selector, defaulted for single-business users.
2. Client selector/search, filtered by organisation, including All clients for overview tasks.
3. Farm selector, filtered by client, including All farms within the selected context.
4. Field selector/search, filtered by farm, including All fields within the selected context.
5. A focused management dialog for organisations, clients, farms and fields.
6. Separate season/job filters when those workflows exist. Whole Field and Seasons remain beneath Field.

All clients/farms/fields are viewing/filtering options, not database records. Require an explicit target for writes/imports rather than assigning new data to an aggregate selection. Changing a parent selection must reset incompatible child selections and make the active context visible.

Selection should make the active context clear and filter or zoom without changing source data. Use native QGIS controls where practical. Avoid creating a separate permanent management panel in Simple view or one QGIS layer per individual field. Version 0.6.0 implements the focused management dialog, with readable labels/icons and native field filtering; dropdown selectors remain a future interface refinement.

## Next increment and checks

Schema 2 and the management dialog now implement the four-level foundation. Future work should build import/export and season-data flows around this interface. Keep original workspaces and confirmed Organisation/Client assignments in the upgrade-copy workflow.

Verified automated foundation checks cover same-named farms/fields under different clients, duplicate/orphan rejection (including native provider writes), renamed parents retaining links, season dates/crops, add-dialog cancellation, icons, native field filtering without duplicate/unrelated layer removal, project move/reopen and upgrade-copy source preservation/failed-copy cleanup. Remaining acceptance work includes toolbar selectors, multi-field jobs, historical boundary links and import conflict resolution; those workflows are not implemented.

## Primary sources reviewed

- [Deere field API](https://developer.deere.com/dev-docs/fields) and [client API](https://developer.deere.com/dev-docs/clients).
- [Deere: Manage Clients, Farms and Fields](https://displaysimulator.deere.com/onscreen_help/4640/current/en/fields/fields_manage.htm).
- [Ag Leader: Creating Management Items](https://portal.agleader.com/community/s/article/1606?language=en_US).
- [Ag Leader SMS Advanced: Agronomic Analysis](https://portal.agleader.com/community/s/article/6388?language=en_US).
- [Ag Leader: SMS Software Layout and Management Tree](https://portal.agleader.com/community/articles/en_US/Knowledge/6865).
- [PTx: FarmENGAGE APIs](https://www.ptxag.com/us/en/partners/developers/api/).
- [PTx: Initial Organization Creation and Management](https://www.ptxag.com/us/en/resources/product-resources/farmengage-initial-organization-creation-management.html).

The 0.6.0 native Layers tree mirrors the complete management hierarchy using stable group properties. Selecting any field branch switches the shared reference views to that field; no table per field/season is created. Use Manage Data for persistent record renames. Default labels are placeholders, not inferred ownership or a real crop season.
