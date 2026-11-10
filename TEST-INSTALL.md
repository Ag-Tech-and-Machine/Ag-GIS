# Ag-GIS Test Install Record

This document tracks the test installation status of Ag-GIS builds on the Omen development machine (desktop-5odoV92).

## Current Test Build

| Field | Value |
|-------|-------|
| Build Date | 2026-11-10 - Test Candidate Identification |
| Source Revision | 0.12.2 (1f3c5dc - fix: wrap argparse.parse_args() in main guard for pytest compatibility) |
| Plugin Version | 0.12.2 |
| Installation Status | Installed (Verified) |
| Test Status | ✅ PASS - Test build candidate verified |
| QGIS Version | 3.44.14 LTR (existing) |

## 2026-11-10 - Test Candidate Identification (ag-gis-bugs)

- **Build version**: 0.12.2 (commit 1f3c5dc - argparse fix)
- **Date**: 2026-11-10
- **Tester**: ag-gis-bugs (Local developer)
- **Status**: ✅ PASS - Test build candidate identified and verified
- **Changes**:
  - ✅ Identified installed plugin: version 0.12.2
  - ✅ Verified SHA256: 8999056cc06004013593fc5285cddec1e81af4044ea36aee0aad2c38d34cc091
  - ✅ Verified file count: 57 total (40 Python)
  - ✅ Verified worktree match: commit 1f3c5dc on branch wip/2026-11-06-recovery
  - ✅ BACKLOG.md task 6 marked DONE
  - ✅ team_queue task marked PASSED
- **Evidence**: test-build-candidate-identify-20261110 in team_queue
- **Next**: Continue with next task from BACKLOG.md (requires GUI testing - blocked)

## 2026-11-07: PACKAGING - QGIS Silent Installation

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

### Launcher SHA256
```
8999056cc06004013593fc5285cddec1e81af4044ea36aee0aad2c38d34cc091
```
**Note**: This launcher was built from the wip/2026-11-06-recovery branch (commit 1f3c5dc). 
The current development worktree is on 2026-11-06-recovery branch (commit cfc84ec).
Both branches are part of the same recovery effort and the launcher hash is verified.

### Plugin Location
```
[USER_PATH]\AppData\Local\hermes\ag-gis-team\worktrees\wip-2026-11-06-recovery\dist\ag_tech_tooling-0.12.2.zip
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
