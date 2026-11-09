[CmdletBinding()]
param([string]$QgisRoot)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
if(-not $QgisRoot){
    $qgisCandidates=@(Get-ChildItem -LiteralPath 'C:\Program Files' -Directory | Where-Object Name -like 'QGIS*' | Sort-Object LastWriteTime -Descending)
    $QgisRoot=($qgisCandidates | Where-Object {(Test-Path -LiteralPath (Join-Path $_.FullName 'bin\qgis-ltr.bat')) -or (Test-Path -LiteralPath (Join-Path $_.FullName 'bin\qgis.bat'))} | Select-Object -First 1).FullName
}
if(-not $QgisRoot){throw 'QGIS runtime not found. Install QGIS LTR from https://qgis.org/download/ or pass -QgisRoot.'}
$launcher=Join-Path $QgisRoot 'bin\qgis-ltr.bat'
if(-not(Test-Path -LiteralPath $launcher)){$launcher=Join-Path $QgisRoot 'bin\qgis.bat'}
if(-not(Test-Path -LiteralPath $launcher)){throw 'QGIS launcher not found in the supplied installation.'}
$previousPluginPath=$env:QGIS_PLUGINPATH
try{
    $env:QGIS_PLUGINPATH=Join-Path $repoRoot 'plugins'
    & $launcher --profiles-path (Join-Path $repoRoot '.dev-profiles') --profile ag-tech-tooling-dev
}finally{$env:QGIS_PLUGINPATH=$previousPluginPath}
