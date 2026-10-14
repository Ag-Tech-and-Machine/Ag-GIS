# Organisation, Farm and Field — researched design proposal

15 October 2026. Proposed model, not a schema migration or implemented feature. Current plugin: 0.4.0, with one farm-information row in schema version 1. Existing data remains unchanged.

## Direction

Use **Organisation → Farm → Field** as the default farmer-facing hierarchy. Organisation means the farming business whose data is being managed. Farm means a named property or management grouping; Field means a persistent working land unit (which may be labelled Paddock for local users).

```text
Organisation: Smith Farming
  Farm: Home Farm
    Field: North 40
    Field: Creek Paddock
  Farm: River Block
    Field: East Pivot
```

One organisation can contain several farms; one farm can contain several fields. Do not equate a software project/package with one physical farm. A project is the workspace the farmer opens. The current one-farm workspace is a foundation and will need a deliberate, versioned migration before managing this hierarchy.

## What the reference platforms show

| Platform | Verified pattern | Lesson for Ag Tech Tooling |
| --- | --- | --- |
| John Deere Operations Center | The field API operates within an organisation and relates fields to clients and farms. Deere's display help documents Client → Farm → Field, with optional grouping levels. | Keep account/organisation identity distinct from the Client/Farm/Field names exchanged with machines. |
| Ag Leader SMS | Management items include Grower, Farm, Field and Year; SMS Advanced analysis filters include Grower, Farm, Field, Year and Operation. Its management tree also offers task/calendar views. | Familiar land hierarchy and alternate time/task views should access the same records. |
| PTx FarmENGAGE | Organisation setup is separate from field resources. The public API overview lists Client/Farm/Field, boundaries, guidance lines and landmarks. Organisation and user unit preferences have different roles. | Separate business context, land resources and user display preferences. |

This is a comparison of public documentation, not a reverse-engineered database schema or a claim that the three products have identical models.

## Client/Grower support

For a farmer managing their own business, three visible levels are enough. Treat Client/Grower as an optional later business relationship for contractors/advisers or external import/export mappings. Do not silently equate a Deere organisation ID with its client ID, or collapse several external growers into one record because names match.

If contractor multi-client work becomes an immediate requirement, settle whether a project contains separate client organisations or a distinct Client entity before creating production data. An Ag Tech workspace is not itself an authentication or permission boundary.

## Land, time and work are related dimensions

- Keep field identity independent of seasons and geometry. A renamed field retains its ID.
- Store boundary revisions against a field, with validity/source details. Splits and merges need lineage rather than silently reusing an old identity.
- Relate seasons/crop cycles to fields; do not duplicate field records every calendar year. Season labels and dates must allow local cropping practices.
- Relate jobs/tasks to one or more fields. A job can carry input datasets, processing parameters, outputs and status.
- Store permanent boundaries, guidance, terrain and assets separately from dated observations, operations and results. Organisation-wide or farm-wide datasets need not be forced onto a single field.

## Proposed GeoPackage approach

Use shared tables/layers with stable IDs and explicit relationships, rather than a table or file for every field or year. Candidate entities are organisations, farms, fields, field-boundary revisions, seasons/crop cycles, jobs, job-field links, datasets and external identifier mappings. These names and columns are provisional.

Use a single managed GeoPackage for the selected organisation workspace initially; allow multiple farms inside it. Keep the relationship model independent of later selected-farm sharing packages. Decide the final package name and supporting raster/LiDAR/original-file locations before migration. A GeoPackage can be the core store while the full workspace still contains QGZ and supporting files.

Store external platform IDs separately from internal UUIDs, keyed by platform, external account/organisation, entity type and external ID. Import matching must distinguish IDs, names and geometry; show unresolved or conflicting matches for review. Export presets must explicitly map Organisation/Client/Grower/Farm/Field terms and report unsupported content.

Use native QGIS layers/providers/writers, relations and forms for editing and presentation. Define database constraints and migrations deliberately; QGIS form validation alone is not protection against external edits. Use QGIS coordinate transformations and Processing for GIS operations. Record CRS, vertical datum where relevant and physical units with data; a user's display-unit preference must not reinterpret stored values. Organisation defaults, project settings and user preferences need explicit precedence.

## Interface first

Keep map and Layers as the primary workspace. Proposed controls belong in the existing top toolbar or focused dialogs:

1. Organisation selector, defaulted for single-business users.
2. Farm selector, including All farms.
3. Field selector/search, filtered by farm, including All fields.
4. A focused Manage Farms & Fields dialog for the hierarchy.
5. Separate season/job filters when those workflows exist.

Selection should make the active context clear and filter or zoom without changing source data. Use native QGIS controls where practical. Avoid creating a separate permanent management panel in Simple view or one QGIS layer per individual field. Use readable labels with appropriate icons; the current 0.4.0 toolbar already uses native QGIS icons above its action labels.

## Next increment and checks

Agree the three-level model and optional Client/Grower behaviour, then design the selectors/dialog before implementing schema version 2. Create and verify a backup before migrating any existing farm workspace. Preserve its farm ID and source files; do not invent organisation ownership without user input.

Acceptance examples: two farms with identically named fields remain distinct; renaming does not break links; a multi-field job works; historical boundary references survive changes; imported external names do not cause silent merging; a moved/restored package reopens; cancelled selection/import/migration leaves data unchanged. These behaviours are proposed and have not been implemented or tested.

## Primary sources reviewed

- [Deere field API](https://developer.deere.com/dev-docs/fields) and [client API](https://developer.deere.com/dev-docs/clients).
- [Deere: Manage Clients, Farms and Fields](https://displaysimulator.deere.com/onscreen_help/4640/current/en/fields/fields_manage.htm).
- [Ag Leader: Creating Management Items](https://portal.agleader.com/community/s/article/1606?language=en_US).
- [Ag Leader SMS Advanced: Agronomic Analysis](https://portal.agleader.com/community/s/article/6388?language=en_US).
- [Ag Leader: SMS Software Layout and Management Tree](https://portal.agleader.com/community/articles/en_US/Knowledge/6865).
- [PTx: FarmENGAGE APIs](https://www.ptxag.com/us/en/partners/developers/api/).
- [PTx: Initial Organization Creation and Management](https://www.ptxag.com/us/en/resources/product-resources/farmengage-initial-organization-creation-management.html).
