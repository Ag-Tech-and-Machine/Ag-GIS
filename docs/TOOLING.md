# Development and tooling

Last updated: 15 October 2026.

## What exists now

| Item | Purpose |
| --- | --- |
| `plugins/qgis_plugin_work/__init__.py` | QGIS `classFactory` entry point |
| `plugins/qgis_plugin_work/plugin.py` | Starter action and clean load/unload lifecycle |
| `plugins/qgis_plugin_work/metadata.txt` | Name, version, author and compatibility metadata |
| `plugins/qgis_plugin_work/icon.svg` | Toolbar/menu icon |
| `scripts/launch-qgis.ps1` | Start QGIS with source plugin discovery and an isolated profile |
| `scripts/check.ps1` | Run syntax/metadata checks, Qt/PyQGIS smoke check and ZIP build |
| `tools/check_plugin.py` | Check Python syntax and mandatory metadata |
| `tools/smoke_test.py` | Exercise entry point, action, duplicate-init prevention and unload using Qt/PyQGIS |
| `tools/build_plugin.py` | Produce and validate a QGIS plugin ZIP |

The starter reports a layer count. No domain-specific tools, processing algorithms, automatic updater or remote Git repository exist yet.

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
3. Run **QGIS Plugin Work** from its menu or toolbar.
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
4. Confirm licensing, public project/support URLs and QGIS version compatibility before publishing to the public plugin repository. Those publishing decisions are not yet complete.
5. Create a release tag only after a release has been verified. Publication, GitHub remote creation and release automation are not implemented in this starter.

## Documentation responsibilities

The manager maintains installation instructions, tool usage, verification evidence, known failures and next steps during development. A feature is not complete until its relevant instructions match the implementation. Documentation-only edits need editorial review and link/path checks; they do not require rerunning unchanged code tests.

Reference: https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html
