# Project purpose

Ag Tech Tooling exists to build **farmer-friendly, open-source tooling that simplifies agricultural workflows and automates GIS work**.

Farmers should be able to spend more time on the job they are trying to complete and less time repeating GIS setup, converting files or navigating specialist controls. We will build practical QGIS tools around real farming tasks, with clear steps and results that users can inspect.

## Design principles

- Describe tasks using language farmers use. Explain unavoidable GIS terms where they appear.
- Use sensible defaults, clear units and straightforward controls.
- Automate repetitive work while showing what will happen and where results will be saved.
- Preserve original data by default. Make any deliberate overwrite explicit.
- Validate inputs and report actionable errors rather than leaving users with partial or unexplained results.
- Keep tools small enough to understand, verify and maintain.
- Ship step-by-step installation and operating instructions with each useful feature.
- Use open-source licensing and keep the implementation inspectable. Avoid dependencies on paid services unless a later feature explicitly requires them.

## Current implementation

The QGIS plugin foundation, packaging, installation and development checks exist. Version 0.2.1 provides an optional Simple view switch in QGIS's bottom-right status bar: only the map and Layers occupy the primary workspace, with full-layout restoration available. The starter action also reports the number of project layers. It does not yet automate a farming workflow or modify GIS data.

The source is GPL-2.0-or-later, with the full GPL version 2 license text in the repository and plugin package. The source is currently in local Git; public hosting and release publication remain future work.

## First development cycle

For the first tool, agree the farming task, sample inputs, desired output and success criteria. Build and verify that workflow, document its exact operating steps, then improve it using feedback from practical use. Record decisions and checks in the work log.
