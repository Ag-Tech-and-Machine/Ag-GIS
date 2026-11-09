# Repository presentation

## Purpose and scope

The README is the farmer-facing introduction to Ag-GIS: **Farming in view**,
**Built on open source tools**. It uses original field-green, sage and harvest
artwork, a real development screenshot, and direct links to experimental downloads,
installation, the user guide and public feedback. Technical attribution remains
below the introduction. This is a documentation/artwork change, not a product
release, installer update or new GIS capability.

## Assets and provenance

- `assets/brand/ag-gis-symbol.svg`: original field-A symbol, copied from the
  existing Ag-GIS identity. Preserve its proportions and upstream notices.
- `assets/brand/ag-gis-banner.svg`: outlined editable vector banner, generated
  from the symbol and the text/layout recipe in `tools/build_repository_artwork.py`.
  Its abstract field lines are brand artwork, not a map or product screenshot.
- `assets/brand/ag-gis-banner.png`: 1600 × 640 README export.
- `assets/brand/ag-gis-social-preview.png`: 1280 × 640 export prepared for a
  GitHub repository social preview. Committing it does not set GitHub's preview.
- `assets/brand/ag-gis-desktop.png`: actual QGIS 3.44.14 desktop running current
  local Ag-GIS development code, captured on 19 October 2026. Four labelled
  paddocks were generated as in-memory polygon layers in a scratch-only profile.
  No customer records, normal profile, farm workspace or online basemap was used.
  This image is not evidence that the public base or an older installer contains
  the same interface. Existing application attribution remains intact.

No new artwork licence or trademark clearance is claimed here. Repository licence
and existing upstream notices remain unchanged.

## Rebuild and verify

1. Prerequisites: Windows, QGIS 3.44.14 with bundled Python/Qt, the repository
   symbol above, and the Windows Segoe UI regular/semibold fonts. No extra Python
   package, JavaScript frontend, network service or GIS engine is required.
2. From the repository root in PowerShell run:

   ```powershell
   & 'C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat' tools/build_repository_artwork.py
   ```

   Expected: the outlined SVG and two PNG exports are regenerated; each PNG's
   dimensions are printed. If QGIS or fonts are missing, correct the prerequisite
   rather than installing `qgis` from pip or silently substituting fonts.
3. Open both PNGs and inspect readability, clear space and clipping. Confirm the
   SVG contains no scripts, external image/font references or active HTML.
4. For a replacement screenshot, start a separate scratch QGIS profile and use
   generated demonstration data only. Wait until layout and rendering settle,
   frame every field, and inspect the actual captured pixels before copying the
   PNG here. Do not restart the user's application or capture private farm data.
   Keep the visible development caption and update the provenance above.
5. Check every README relative link and image against the exact publication
   checkout. Run `git diff --check`; run `python tools/check_repository.py` in
   the development checkout when that tool exists. An older public base may not
   include the full development check inventory; do not add unrelated source just
   to make a branding branch resemble the shared checkout.
6. Review the allowlisted diff before publishing. Confirm remote branch SHA and
   asset bytes by reading them back from GitHub. A local commit, clean working
   tree or unconditional `echo DONE` does not prove a successful push.

## GitHub settings

Approved product wording: **Farmer-friendly mapping and farm-data workflows.
Built on open source tools. In development.** Suggested topics: `agriculture`,
`farm-management`, `gis`, `mapping`, `open-source`, `desktop-application`.

About/topics/social-preview settings are separate from README commits and may
require additional repository permissions. Read back each changed setting; if
permissions prevent an update, report that limit rather than claiming the
committed social image is already configured. Do not change the organisation
avatar, repository visibility, feedback destination, releases or infrastructure
as a side effect.
