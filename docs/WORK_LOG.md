# Work log and verification status

## 15 October 2026 — Initial development environment

### Completed

- Configured Git author Michael `<admin@agtechandmachine.com>` and default branch `main`.
- Created the local `qgis-plugin-work` repository and committed the starter.
- Installed QGIS 3.44.14 LTR using WinGet; installer hash verification and installation succeeded.
- Added source discovery through `QGIS_PLUGINPATH` and an isolated development profile launcher.
- Added syntax/metadata checks, Qt/PyQGIS smoke checking and ZIP packaging.
- Established installation, tooling and work-log documents, with upkeep required in `AGENTS.md`.

### Verified

- `scripts\check.ps1 -QgisRoot 'C:\Program Files\QGIS 3.44.14'` passed.
- The smoke check created the plugin through `classFactory`, exercised its action, prevented duplicate registration, and removed registrations on unload using real Qt/PyQGIS and an interface adapter.
- Plugin ZIP structure and integrity checks passed.
- Development launcher started the QGIS GUI and created the isolated profile.
- Git author matched the requested identity; repository integrity check passed.

### Pending

- Manual enable/disable and toolbar/menu checks in QGIS's plugin manager.
- ZIP installation check in a separate QGIS profile.
- Definition of the first useful domain-specific tool.
- Remote Git repository and backup/publication workflow, if requested.
- Licensing and public project/support URLs before public release.

### Known setup findings

- Old QGIS 3.36 folders contained only remnants and were not usable runtimes.
- WinGet's command alias was absent, but its installed App Installer executable worked.
- Installing QGIS required the user to approve the Windows administrator prompt.

### Next step

Confirm the starter's manual QGIS action check, then define and implement the first real tool. Add its operating instructions and validation evidence with the implementation.
