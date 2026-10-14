# QGIS Plugin Work

A fresh Python plugin project for QGIS 3.x LTR. The starter adds a toolbar/menu action that reports the current layer count. No previous project files or company sign-in settings are included.

## Maintained instructions

- [Installation and setup](docs/INSTALL.md)
- [Development and tooling](docs/TOOLING.md)
- [Work log and verification status](docs/WORK_LOG.md)

These instructions are updated alongside the tooling, rather than only at release time.

## Develop

Run `scripts/launch-qgis.ps1` in PowerShell. It finds an installed QGIS launcher, sets `QGIS_PLUGINPATH` to this repository's `plugins` directory, and opens the isolated `qgis-plugin-work-dev` profile.

In QGIS, open **Plugins → Manage and Install Plugins → Installed**, then enable **QGIS Plugin Work**. Use its toolbar or Plugins menu action. Restart QGIS after changing Python code, or use the optional Plugin Reloader plugin.

Edit `plugins/qgis_plugin_work/plugin.py` for functionality and `metadata.txt` for plugin details. Keep GIS datasets outside Git; this repository ignores common dataset formats.

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

The build produces `dist/qgis_plugin_work-0.1.0.zip`, suitable for **Plugins → Manage and Install Plugins → Install from ZIP**. Generated archives stay out of Git.

`tools/smoke_test.py` checks the actual Qt/PyQGIS plugin lifecycle. Run it with QGIS's Python interpreter after setting up the QGIS environment; ordinary system Python cannot import PyQGIS.

## Git

The repository starts on `main`. Commit identity is Michael `<admin@agtechandmachine.com>`. It is local: no GitHub repository or remote is created automatically.

## Publishing

The starter metadata marks this plugin experimental. Choose the final plugin name, description, licensing and public project/support URLs before publishing. It is not yet a public release.
