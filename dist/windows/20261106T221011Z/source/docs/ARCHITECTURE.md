# Repository map

Ag-GIS is a Python QGIS plugin with Windows packaging. It supplies farming-language workflows around native GIS capabilities. This is a navigation map, not a claim that every planned module is present in every older source/tag.

| Area | Entry point / location | Responsibility |
| --- | --- | --- |
|| Plugin lifecycle | `plugins/ag_tech_tooling/__init__.py`, `plugin.py` | Load actions and pair initGui/unload; preserve shared native actions; browser-reviewed feedback (unwired direct-token prototype is not secure sign-in) |
| Farm workspace | `farm_project.py`, `hierarchy.py`, their dialogs | Organisation → Client → Farm → Field → Season/Crop; consistent native GeoPackage operations |
| Farm presentation | `simple_view.py`, `farm_browser.py`, `ui_icons.py` | Reversible simplified layout, native tree behaviour and semantic icons |
| Data import | `import_sources.py`, `import_dialog.py`, `import_destination.py`, `import_placement.py` | Discover supported sources, choose destinations and preserve originals |
| Later development modules | Inspect current plugin directory and metadata | Managed data, backgrounds and branding may be ahead of the published base snapshot; verify the module exists before relying on it |
| Packaging | `tools/build_plugin.py`, `tools/install_plugin.py`, `installer/` | Complete plugin ZIP and Windows setup; installing changes a profile |
| Checks | `tools/*_test.py`, `scripts/check.ps1` | Synthetic fixtures, source and extracted-package integration |
| Repository automation | `.github/workflows/`, `.github/scripts/` | Basic CI and issue labels; release assembly stays manual |
| Product identity | `assets/brand/`, `docs/BRAND_ASSETS.md` | Repository logo exports; runtime branding is a separate code change |
| Instructions | Root AGENTS.md, CONTRIBUTING.md, docs/DEVELOPMENT.md | One canonical workflow shared by humans and agents |

Data flow: user source → explicit import/destination choice → native QGIS validation/writer → managed workspace → map/project. Keep user datasets outside this source repository. A project file can reference external assets: portable backup needs a dependency inventory and usable restore, not merely copying the project file.

No cloud backend, billing service, browser/mobile app or synchronisation service is supplied by this setup. Future plans are in ROADMAP.md and the business plan when present. Do not add service credentials or imply paid features exist.
