# Project purpose

Ag-GIS exists to build **farmer-friendly, open-source tooling that simplifies agricultural workflows and automates GIS work**.

**Ag-GIS · Farming in view · Built on open source tools**

Farmers should be able to spend more time on the job they are trying to complete and less time repeating GIS setup, converting files or navigating specialist controls. We build practical workflows around real farming tasks, with clear steps and results that users can inspect. Ag-GIS is the product identity; individual open-source tools are implementation foundations, not the limit of the product's direction. The current desktop implementation uses QGIS. Other integrations must be explicitly implemented and verified before being described as supported.

## Design principles

**People own and control their data.** Transparency, honest feature/service claims and freedom to contribute and guide the product govern the business and implementation. Follow [user commitments](USER_COMMITMENTS.md). Keep local work useful without a cloud subscription, provide usable exports and deliberate sharing controls, and explain access/retention/limits before uploading or charging. Source contributions are available through forks and pull requests in the public Ag-Tech-and-Machine/Ag-GIS repository; maintainers review proposals, with no guaranteed acceptance or direct write access.

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

The current desktop implementation has a plugin foundation, Windows packaging and development checks. Local development includes Organisation → Client → Farm → Field, Season/Crop records, Whole Field reference layers, a simplified map workspace and managed imports of supported vector/raster data. Project creation supplies editable starter records; separate-copy upgrades preserve older projects. See the source-version user guide and work log for exact implemented workflows and evidence. Public main, installed applications and experimental downloads can differ. Seasonal dataset editing, complete portable export, automatic revision history and broader conversion automation are not claimed complete.

The source is GPL-2.0-or-later, with the full GPL version 2 license text in the repository and plugin package. Source and experimental releases are public in Ag-Tech-and-Machine/Ag-GIS. Public feedback stays in JamRov/Ag-GIS-Feedback. Public availability is not release readiness; no cloud/mobile/sync service is implied.

## First development cycle

The immediate development priority remains the interface: discoverable tasks, clear wording and feedback, a map-and-Farm-Data workspace and preservation of users' work. Product branding should describe this farming purpose and open-source direction consistently, without expanding the implemented feature claims. Build further tools around agreed farming tasks, not a list of underlying technologies.

For the first tool, agree the farming task, sample inputs, desired output and success criteria. Build and verify that workflow, document its exact operating steps, then improve it using feedback from practical use. Record decisions and checks in the work log.
