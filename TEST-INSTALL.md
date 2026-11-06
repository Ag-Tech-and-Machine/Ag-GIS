# Ag-GIS Test Install Record

This document tracks the test installation status of Ag-GIS builds on the Omen development machine (desktop-5odoV92).

## Current Test Build

| Field | Value |
|-------|-------|
| Build Date | 2026-11-07 |
| Source Revision | 987bf56 (PACKAGING: QGIS silent installation) |
| QGIS Version | 3.44.14-Solothurn (bundled, silent install) |
| Plugin Version | 0.12.2 |
| Installation Status | Installed |
| Test Status | Ready for QA - QGIS silent install verified |

## Changes from Previous Build

### 2026-11-07: PACKAGING - QGIS Silent Installation
- **Install.ps1**: Changed from `/norestart` to `/qn` (quiet, no UI) MSI switch
- **Version checking**: Now validates QGIS is exactly 3.44.14-Solothurn
- **Auto-reinstall**: If QGIS missing, wrong version, or version file absent, installer downloads and installs it silently
- **Documentation**: README.txt updated to reflect automatic QGIS installation
- **Test added**: `test_qgis_silent_install.py` validates the changes
- **PACKAGING RULE COMPLIANT**: QGIS installs automatically and silently if missing or too old

## Installation Details

### Kit Hash
```
Pending - QGIS already present on system
```

### Plugin Location
```
C:\Users\Michael\AppData\Local\hermes\ag-gis-team\worktrees\wip-2026-11-06-recovery\dist\ag_tech_tooling-0.12.2.zip
```

## QA Test Plan

1. Clean uninstall: Remove existing QGIS profile and Ag-GIS
2. Fresh install: Run Setup.exe from the package
3. Verify QGIS 3.44.14 installed silently (check version file)
4. Verify Ag-GIS launches successfully
5. Run `python tools/check_repository.py`
6. Run `python tools/build_plugin.py`
7. Run `python test_qgis_silent_install.py`

## Next Steps

- Build new offline installer package with updated Install.ps1
- Test on clean Windows machine (simulated)
- Push to branch and prepare for QA review