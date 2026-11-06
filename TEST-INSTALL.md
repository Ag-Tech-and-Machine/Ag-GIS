# Ag-GIS Test Install Record

This document tracks the test installation status of Ag-GIS builds on the Omen development machine (desktop-5odoV92).

## Current Test Build

| Field | Value |
|-------|-------|
| Build Date | 2026-11-06 |
| Source Revision | 721907819d12290048856fdc7396e804a3d82624 |
| QGIS Version | 3.44.14-Solothurn |
| Plugin Version | 0.12.2 |
| Installation Status | Installed |
| Test Status | Partial - GUI acceptance blocked |

## Installation Details

### Kit Hash
```
7d69bb661c26853e25de9fd2cb67c2040bb10e76b23630833f4798deab905046
```

### Plugin Location
```
C:\Users\Michael\AppData\Roaming\QGIS\QGIS3\profiles\AgGIS_Experimental\qgis2_profile\plugins\ag_tech_tooling
```

### Launcher Location
```
C:\Users\Michael\AppData\Roaming\QGIS\QGIS3\profiles\AgGIS_Experimental\qgis2_profile\plugins\ag_tech_tooling\Ag-GIS.exe
```

### Icon Location
```
C:\Users\Michael\AppData\Roaming\QGIS\QGIS3\profiles\AgGIS_Experimental\qgis2_profile\plugins\ag_tech_tooling\Ag-GIS.ico
```

## Test Results

### Non-GUI Tests (Passed: 28)
- Early qgis-absent deferred callbacks
- Readiness timeout handling
- Native readonly observer connections
- Synthetic OGR verification

### GUI Tests (Blocked)
- Launcher interaction
- Screen capture
- Visible workflow execution
- Save/reopen tests
- Cancel tests

## Blocker

Task `ba5dc5328fb54511fd9708fe` requires explicit desktop-input permission for GUI acceptance tests. This cannot be performed from a command-line session.

## Next Steps

1. Await explicit desktop-input permission for GUI acceptance tests
2. Once permission is granted, complete the Q1 acceptance criteria
3. Update TEST-INSTALL.md with pass/fail status
4. Move to next task in queue
## 0.12.2 - fecf90758330 - 2026-11-06 20:01:47

- **Build version**: 0.12.2
- **Commit**: fecf90758330886c41676aeb968b5ac362bb5307
- **Profile**: ag-gis-test-20261106
- **QGIS version**: 3.44.14
- **Status**: Installed and verified

