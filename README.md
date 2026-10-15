# Ag-GIS

Ag-GIS builds farmer-friendly, open-source tools that simplify agricultural workflows and automate GIS work. We aim to turn repetitive mapping and data preparation into understandable, dependable steps that farmers can use without needing to become GIS specialists.

The project uses QGIS 3.x LTR. Version 0.7.0 provides a dedicated **Ag-GIS** toolbar with New Project, Open Project, Manage Data and Data In. New Project generates a starter workspace in Documents → Ag-GIS → Projects. Browse Organisation → Client → Farm → Field → Season as separate short levels in Layers. Manage these records in GeoPackage, with icon-labelled rows/controls and field-filtered native reference layers. Save/navigation reuse native QGIS actions. The bottom-right **Simple view** switch keeps our toolbar plus map and Layers. Schema 1 upgrades create a separate validated copy. Seasonal datasets, imports/exports, full settings editing, history and conversions remain under development. Source code is GPL-2.0-or-later. A public Git repository has not yet been created.

See [project purpose and design principles](docs/PURPOSE.md).

## Maintained instructions

- [Installation and setup](docs/INSTALL.md)
- [Bundled user guide](docs/USER_GUIDE.md)
- [Development and tooling](docs/TOOLING.md)
- [Farm data foundation and structure proposal](docs/FARM_PROJECTS.md) (minimal New/Open implemented)
- [Organisation, Client, Farm and Field model](docs/FARM_DATA_MODEL.md) (implemented foundation and remaining design)
- [Work log and verification status](docs/WORK_LOG.md)

These instructions are updated alongside the tooling, rather than only at release time.

## Install locally

Close QGIS and run `scripts/install-plugin.ps1`. It checks and builds the plugin, installs it into the existing `default` QGIS profile, backs up the profile settings, and enables Ag-GIS. Restart QGIS normally to use the installed copy. Use `-Profile` to choose another existing user profile.

## Develop

Run `scripts/launch-qgis.ps1` in PowerShell. It finds an installed QGIS launcher, sets `QGIS_PLUGINPATH` to this repository's `plugins` directory, and opens the isolated `ag-tech-tooling-dev` profile.

In QGIS, open **Plugins → Manage and Install Plugins → Installed**, then enable **Ag-GIS**. Use its toolbar or Plugins menu action. Restart QGIS after changing Python code, or use the optional Plugin Reloader plugin.

Edit `plugins/ag_tech_tooling/plugin.py` for functionality and `metadata.txt` for plugin details. Keep GIS datasets outside Git; this repository ignores common dataset formats.

## Check and package

Use the installed QGIS Python runtime to run all checks and build the ZIP:

```powershell
.\scripts\check.ps1
```

For syntax checks and packaging only, an ordinary Python 3 runtime also works:

```powershell
python tools/check_plugin.py
python tools/build_plugin.py
```

If the `python` command is a Windows Store alias, use the full path to an installed Python executable. PyQGIS is bundled with QGIS; do not install a package called `qgis` from pip.

The build produces `dist/ag_tech_tooling-0.7.0.zip`, suitable for **Plugins → Manage and Install Plugins → Install from ZIP**. Generated archives stay out of Git.

`tools/smoke_test.py` checks the actual Qt/PyQGIS plugin lifecycle. Run it with QGIS's Python interpreter after setting up the QGIS environment; ordinary system Python cannot import PyQGIS.

## Git

The repository starts on `main`. Commit identity is Michael `<admin@agtechandmachine.com>`. It is local: no GitHub repository or remote is created automatically.

## Publishing

The starter metadata marks this plugin experimental. The source uses GPL-2.0-or-later, with the license included in plugin ZIPs. Confirm the final plugin name, public project/support URLs and compatibility checks before publishing. It is not yet a public release.
