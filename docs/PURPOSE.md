# Project purpose

Ag-GIS exists to build **farmer-friendly, open-source tooling that simplifies agricultural workflows and automates GIS work**.

Farmers should be able to spend more time on the job they are trying to complete and less time repeating GIS setup, converting files or navigating specialist controls. We will build practical QGIS tools around real farming tasks, with clear steps and results that users can inspect.

## Design principles

**Interface optimisation is priority one.** Focus the next development work on a clear farmer-facing layout, understandable controls and short task flows. Expand data management and conversions in steps that fit that interface.

Use native QGIS tooling wherever practical: reuse its actions, widgets, dialogs, providers, writers, coordinate transformations and Processing algorithms. Ag-GIS supplies simple farming language, defaults and workflow guidance around those capabilities. Custom GIS implementations need a documented reason when QGIS already supports the operation.

- Describe tasks using language farmers use. Explain unavoidable GIS terms where they appear.
- Use sensible defaults, clear units and straightforward controls.
- Automate repetitive work while showing what will happen and where results will be saved.
- Preserve original data by default. Make any deliberate overwrite explicit.
- Validate inputs and report actionable errors rather than leaving users with partial or unexplained results.
- Keep tools small enough to understand, verify and maintain.
- Ship step-by-step installation and operating instructions with each useful feature.
- Use open-source licensing and keep the implementation inspectable. Avoid dependencies on paid services unless a later feature explicitly requires them.

## Current implementation

The QGIS plugin foundation, packaging, installation and development checks exist. Version 0.6.0 provides New/Open Project and Manage Data for Organisation → Client → Farm → Field, with Season/Crop records and Whole Field reference layers in GeoPackage schema 2. New Project generates editable starter records in Documents without a setup form; Layers displays the full hierarchy with separate short labels. A separate-copy upgrade preserves older projects. Icon-labelled controls use native QGIS data APIs; Simple view keeps our toolbar, map and Layers. Seasonal dataset editing, import/export, full settings editing, revision history and conversion automation remain future work.

The source is GPL-2.0-or-later, with the full GPL version 2 license text in the repository and plugin package. The source is currently in local Git; public hosting and release publication remain future work.

## First development cycle

The immediate priority is the interface. Version 0.6.0 makes New/Open Farm and native save/navigation tools discoverable in a dedicated top toolbar, including Simple view. Refine task grouping, wording and feedback while preserving the map-and-Layers workspace and users' work. Then develop imports, exports, settings and conversions around the agreed task flows.

For the first tool, agree the farming task, sample inputs, desired output and success criteria. Build and verify that workflow, document its exact operating steps, then improve it using feedback from practical use. Record decisions and checks in the work log.
