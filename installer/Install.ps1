[CmdletBinding()]
param([string]$Profile='default', [switch]$VerifyOnly)
$ErrorActionPreference='Stop'
if(-not [Environment]::Is64BitOperatingSystem){throw '64-bit Windows is required.'}
if($Profile -notmatch '^[A-Za-z0-9_-]+$'){throw 'Use a simple QGIS profile name.'}
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
foreach($file in $manifest.files){
    if($file.path -notmatch '^[A-Za-z0-9_.-]+$'){throw 'Unsafe manifest filename.'}
    $path=Join-Path $PSScriptRoot $file.path
    $stream=[IO.File]::OpenRead($path)
    $hasher=[Security.Cryptography.SHA256]::Create()
    try {$actual=([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
    finally {$stream.Dispose(); $hasher.Dispose()}
    if($actual -ne $file.sha256){throw "Damaged installer file: $($file.path). Extract the complete download again."}
}
if($VerifyOnly){Write-Output 'All installer payload hashes verified.'; exit 0}
if(Get-Process -Name 'qgis*' -ErrorAction SilentlyContinue){throw 'Close QGIS before installing. Save your map first.'}
$qgisRoot=Join-Path $env:ProgramFiles 'QGIS 3.44.14'
$python=Join-Path $qgisRoot 'bin\python-qgis-ltr.bat'
if(-not(Test-Path -LiteralPath $python)){
    $msi=Join-Path $PSScriptRoot $manifest.qgisFile
    $log=Join-Path $env:TEMP ('AgTech-QGIS-'+[guid]::NewGuid().ToString()+'.log')
    Write-Output 'Installing QGIS. Follow its setup wizard; Windows may request administrator approval.'
    $process=Start-Process msiexec.exe -ArgumentList @('/i',('"'+$msi+'"'),'/norestart','/L*v',('"'+$log+'"'),('INSTALLDIR="'+$qgisRoot+'"')) -Wait -PassThru
    if($process.ExitCode -eq 3010){throw "QGIS requires a restart. Restart Windows and run Setup.exe again. Log: $log"}
    if($process.ExitCode -ne 0){throw "QGIS installation cancelled or failed ($($process.ExitCode)). Log: $log"}
}
if(-not(Test-Path -LiteralPath $python)){throw 'QGIS Python was not found after setup. Repair QGIS and retry.'}
& $python (Join-Path $PSScriptRoot 'install_profile.py') --package (Join-Path $PSScriptRoot $manifest.pluginFile) --profile $Profile
if($LASTEXITCODE -ne 0){throw 'Plugin installation failed. See the error above; previous files are recovered automatically.'}
Write-Output 'Installation complete. Open QGIS normally and find the Ag-GIS toolbar.'
