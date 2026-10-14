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
foreach($checkScript in @('check_plugin.py','smoke_test.py','build_plugin.py')){
    & $pythonRunner (Join-Path $repoRoot ('tools\'+$checkScript))
    if($LASTEXITCODE -ne 0){throw "$checkScript failed with exit code $LASTEXITCODE"}
}
