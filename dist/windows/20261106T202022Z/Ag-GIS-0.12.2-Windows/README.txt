Ag-GIS 0.12.2 offline Windows installer
Farming in view. Built on open source tools.

1. Extract ALL files to a local folder. Keep Setup.exe beside the other files.
2. Save your map and close QGIS. Double-click Setup.exe as your normal user.
3. If QGIS 3.44.14 is missing or has the wrong version, the installer will download and install it automatically (admin approval may be required).
4. Open Ag-GIS from Start, or open QGIS normally. Both use the selected QGIS profile (QGIS was installed silently if needed).
Other profile: powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -Profile profile_name
Verify without installing: powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -VerifyOnly
Recovery copies: %APPDATA%\QGIS\QGIS3\profiles\<profile>\ag-tech-install-backups.
Close QGIS before restoring the backed-up plugin folder and QGIS3.ini.
To uninstall only this plugin use QGIS Manage and Install Plugins. Farm files remain separate.
Updates: Plugins > Ag-GIS > Check for Updates. Open the private GitHub release, then Install downloaded ZIP.
GitHub: https://github.com/JamRov/Ag-GIS/releases/latest (repository access required).
This setup launcher is unsigned. No credentials are included.
QGIS is unmodified and includes Python, Qt, GDAL and its providers. Optional projection grids are separate.
QGIS installer: https://download.qgis.org/downloads/QGIS-OSGeo4W-3.44.14-1.msi
QGIS project/source and bundled component licensing: https://qgis.org/ and https://github.com/qgis/QGIS/tree/final-3_44_14
Ag-GIS GPL-2.0-or-later source is included in Ag-GIS-source.zip.
Validated on an existing QGIS workstation; clean-machine wizard/UAC checks remain pending.
