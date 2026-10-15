[CmdletBinding()]
param([string]$QgisRoot,[string]$Profile='default')
$ErrorActionPreference='Stop'
if(Get-Process -Name qgis-bin,qgis-ltr-bin -ErrorAction SilentlyContinue){throw 'Close QGIS first so its settings cannot overwrite the installation.'}
if(-not $QgisRoot){
    $roots=@(Get-ChildItem -LiteralPath 'C:\Program Files' -Directory | Where-Object Name -like 'QGIS*' | Sort-Object LastWriteTime -Descending)
    $QgisRoot=($roots | Where-Object {Test-Path -LiteralPath (Join-Path $_.FullName 'bin\python-qgis-ltr.bat')} | Select-Object -First 1).FullName
}
if(-not $QgisRoot){throw 'Install QGIS LTR or supply -QgisRoot.'}
& (Join-Path $PSScriptRoot 'check.ps1') -QgisRoot $QgisRoot
& (Join-Path $QgisRoot 'bin\python-qgis-ltr.bat') (Join-Path (Split-Path -Parent $PSScriptRoot) 'tools\install_plugin.py') --profile $Profile
if($LASTEXITCODE -ne 0){throw 'Plugin installation failed.'}
