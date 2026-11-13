[CmdletBinding()]
param([string]$QgisRoot)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
if(-not $QgisRoot){
    $roots=@(Get-ChildItem -LiteralPath 'C:\Program Files' -Directory | Where-Object Name -like 'QGIS*' | Sort-Object LastWriteTime -Descending)
    $QgisRoot=($roots | Where-Object {(Test-Path -LiteralPath (Join-Path $_.FullName 'bin\python-qgis-ltr.bat')) -or (Test-Path -LiteralPath (Join-Path $_.FullName 'bin\python-qgis.bat'))} | Select-Object -First 1).FullName
}
if(-not $QgisRoot){throw 'Install QGIS LTR or supply -QgisRoot.'}
$pythonRunner=Join-Path $QgisRoot 'bin\python-qgis-ltr.bat'
if(-not(Test-Path -LiteralPath $pythonRunner)){$pythonRunner=Join-Path $QgisRoot 'bin\python-qgis.bat'}
foreach($checkScript in @('check_plugin.py','github_session_test.py','run_github_connection_test.py','branding_test.py','windows_taskbar_test.py','feedback_test.py','feedback_intake_test.py','update_catalog_test.py','updates_test.py','update_native_test.py','smoke_test.py','classification_test.py','classification_registry_test.py','classification_resolution_test.py','operation_style_test.py','dataset_style_test.py','data_dictionary_test.py','farm_project_test.py','hierarchy_test.py','default_workspace_test.py','farm_browser_test.py','farmer_view_test.py','background_maps_test.py','esri_background_test.py','background_checkbox_paint_test.py','background_render_test.py','archive_sources_test.py','deere_preview_test.py','pctgdp_test.py','data_in_test.py','season_review_test.py','season_boundary_test.py','reviewed_import_test.py','import_placement_test.py','managed_data_test.py','build_plugin.py','installer_test.py','launcher_test.py','package_test.py')){
    & $pythonRunner (Join-Path $repoRoot ('tools\'+$checkScript))
    if($LASTEXITCODE -ne 0){throw "$checkScript failed with exit code $LASTEXITCODE"}
}
