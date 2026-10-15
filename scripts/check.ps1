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
foreach($checkScript in @('check_plugin.py','updates_test.py','smoke_test.py','farm_project_test.py','hierarchy_test.py','default_workspace_test.py','farm_browser_test.py','deere_preview_test.py','data_in_test.py','import_placement_test.py','build_plugin.py','installer_test.py','package_test.py')){
    & $pythonRunner (Join-Path $repoRoot ('tools\'+$checkScript))
    if($LASTEXITCODE -ne 0){throw "$checkScript failed with exit code $LASTEXITCODE"}
}
