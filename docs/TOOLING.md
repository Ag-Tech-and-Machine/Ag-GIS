# Development and tooling

Last updated: 15 October 2026.

## What exists now

| Item | Purpose |
| --- | --- |
| `plugins/ag_tech_tooling/__init__.py` | QGIS `classFactory` entry point |
| `plugins/ag_tech_tooling/plugin.py` | Starter action and clean load/unload lifecycle |
| `plugins/ag_tech_tooling/simple_view.py` | Bottom-right Simple view control, profile preference and full-layout restoration |
| `plugins/ag_tech_tooling/metadata.txt` | Name, version, author and compatibility metadata |
| `plugins/ag_tech_tooling/icon.svg` | Toolbar/menu icon |
| `scripts/launch-qgis.ps1` | Start QGIS with source plugin discovery and an isolated profile |
| `scripts/check.ps1` | Run syntax/metadata checks, Qt/PyQGIS smoke check and ZIP build |
| `tools/check_plugin.py` | Check Python syntax and mandatory metadata |
| `tools/smoke_test.py` | Exercise entry point, action, duplicate-init prevention and unload using Qt/PyQGIS |
| `tools/build_plugin.py` | Produce and validate a QGIS plugin ZIP |
| `scripts/install-plugin.ps1` | Check, build, install and enable the packaged plugin in an existing normal QGIS profile |
| `tools/install_plugin.py` | Validate ZIP paths, back up existing files/settings and install the built package |

The interface foundation provides optional Simple view and reports a layer count. No domain-specific tools, processing algorithms, automatic updater or remote Git repository exist yet.

## Use Simple view

1. Install/enable Ag Tech Tooling as described in `INSTALL.md`.
2. Check **Simple view** in QGIS's bottom-right status bar.
3. Use the Project toolbar to create/open/save maps, the Map Navigation toolbar to move/zoom, and Layers to control visible data. The main area contains only the map and Layers. Add data through **Layer → Add Layer**, or turn Simple view off if you need Browser. QGIS menus remain available.
4. Uncheck **Simple view** when you need the previous full workspace. Its toolbar/panel layout is restored.
5. The profile remembers your choice. Turning off the plugin restores the workspace and removes the switch.

The setting is stored in the QGIS profile, outside Git. A saved full-layout snapshot supports restoration across plugin reloads and restarts. Simple view keeps Layers available and prevents other dock panels and welcome pages from reappearing. It does not simplify individual dialog contents or remove advanced features from QGIS; turn it off to use the full workspace.

## Work through each tooling change

1. State the user's task, inputs and expected result. Record consequential scope or dependency decisions in the work log.
2. Implement the smallest useful feature in the plugin source. Use `qgis.PyQt` for Qt integration and retain a matching unload path for every GUI registration.
3. Update this guide with the feature's exact controls, input requirements, output location and operating steps. Update the installation guide when prerequisites, installation or launch behaviour changes.
4. Run the relevant checks. For changes to the plugin lifecycle or functionality, start with:

   ```powershell
   .\scripts\check.ps1
   ```

5. Test the changed behaviour in QGIS using a suitable small dataset. Record expected versus actual results, including any data-specific limitations. Restart QGIS after source changes.
6. When packaging changes, test the ZIP in a separate profile as described in the installation guide.
7. Review and commit the code and documentation together:

   ```powershell
   git diff
   git status
   git add <explicit changed files>
   git commit -m "Describe the completed tooling change"
   ```

   Replace the angle-bracket placeholder with the reviewed file paths. Do not stage datasets, credentials or generated profile files.

8. Update the work log with checks completed, remaining issues and the next useful step. Report verified behaviour separately from planned features.

## Run the current starter

1. Follow `INSTALL.md` to launch the development profile and enable the plugin.
2. Open a QGIS project or add layers.
3. Run **Ag Tech Tooling** from its menu or toolbar.
4. Read the layer-count message. The starter does not alter the project or layer data.

## Build an installable ZIP

1. Run `scripts\check.ps1` from the repository root.
2. Find the ZIP in `dist`. Its version comes from `metadata.txt`.
3. Confirm the check command succeeds before distributing the ZIP.
4. Use QGIS's **Install from ZIP** control and perform a manual action check.

## Version and release changes

1. Change the version in `metadata.txt` when preparing a release.
2. Document new behaviour and any migration/install changes.
3. Run automated and manual checks appropriate to that release.
4. Retain the GPL-2.0-or-later license in source and plugin packages. Confirm public project/support URLs and QGIS version compatibility before publishing to the public plugin repository. Public hosting and publishing decisions are not yet complete.
5. Create a release tag only after a release has been verified. Publication, GitHub remote creation and release automation are not implemented in this starter.

## Documentation responsibilities

The manager maintains installation instructions, tool usage, verification evidence, known failures and next steps during development. A feature is not complete until its relevant instructions match the implementation. Documentation-only edits need editorial review and link/path checks; they do not require rerunning unchanged code tests.

Reference: https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html

## Ready for the first tool

1. Describe the farming task in the user's words.
2. Identify the sample input files or layers, units and coordinate reference system where relevant.
3. Agree the expected output and where to save it.
4. Specify what an acceptable result looks like and which inputs should produce helpful errors.
5. Implement, test on the sample data and document the workflow together.

The default-profile installation is for using the built plugin. The isolated development launcher is for editing the repository source. Rebuild/reinstall after changes to refresh the normal-profile copy.
