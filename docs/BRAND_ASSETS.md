# Repository brand assets

The repository uses the original Ag-GIS field/survey identity developed in the branding chat. These are development assets; no trademark clearance is claimed. Runtime/installer branding work can be ahead of the public base source and is not silently integrated by adding repository artwork.

- `assets/brand/ag-gis-symbol.svg`: scalable square symbol.
- `assets/brand/ag-gis-lockup.svg`: outlined wordmark; no local font installation needed to display it.
- `assets/brand/ag-gis.ico`: Windows export.

Field green `#173F35`, sage `#8DB59A`, harvest `#D9AB55`, slate `#52665D`, warm white `#F5F2E8`. Preserve proportions and clear space; use the symbol at small sizes. Do not combine or alter QGIS's logo into ours. Lead product copy with **Ag-GIS**, **Farming in view** and **Built on open source tools**. Describe the current QGIS foundation in technical/credits sections, retain upstream credits/licences and do not imply endorsement. Broader toolkit direction is not a claim of implemented additional integrations.

## GitHub presentation

Keep the public repository's first impression aligned with the product rather than a single dependency. README source edits do not update GitHub's About fields, organisation avatar or social-preview image.

1. Use the original lockup at the top of README and the square symbol where a small icon is required. Include the exact supporting line **Built on open source tools** in readable text.
2. Proposed repository description: **Farmer-friendly mapping and farm-data workflows. Built on open source tools. In development.**
3. Proposed topics: `agriculture`, `farm-management`, `gis`, `mapping`, `open-source`, `desktop-application`. Keep QGIS in technical implementation documentation; a product topic list must not claim unimplemented integrations.
4. Keep source/releases at **Ag-Tech-and-Machine/Ag-GIS** and feedback at **Ag-Tech-and-Machine/Ag-GIS**. Do not move/rename the feedback tracker as a branding side effect; preserve existing links.
5. Review a dedicated social-preview export before uploading it. Changing repository metadata, social preview or an organisation avatar requires explicit approval and read-back verification. These are proposed settings, not changes already made.
6. Publish a focused branding/documentation change only after reviewing its diff and all linked-file dependencies. The shared checkout contains unrelated feature work; do not bulk-stage or publish it. Keep internal plugin IDs, existing farm-data paths, licences and technical requirements stable.

The editable source artwork is maintained by the branding work in plugin icon.svg/brand_lockup.svg and its generator. Repository exports are copies; refresh them deliberately after reviewed artwork changes and verify the README still displays them. Do not replace source assets with a screenshot or change the organisation avatar as a side effect.
