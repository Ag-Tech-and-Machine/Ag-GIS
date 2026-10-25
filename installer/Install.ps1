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
if(Get-Process -Name 'qgis*' -ErrorAction SilentlyContinue){throw 'Close all Ag-GIS and mapping windows before installing. Save your maps first.'}
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
# A per-profile product launcher leaves the native QGIS shortcuts untouched.
$launcherDir=Join-Path $env:LOCALAPPDATA ('Ag-GIS\'+$Profile)
New-Item -ItemType Directory -Path $launcherDir -Force | Out-Null
foreach($asset in @('Ag-GIS.exe','Ag-GIS.ico')){
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $asset) -Destination (Join-Path $launcherDir $asset) -Force
}
[IO.File]::WriteAllLines((Join-Path $launcherDir 'launch.txt'), @($qgisRoot,$Profile))
$programs=[Environment]::GetFolderPath('Programs')
$shortcutName=if($Profile -eq 'default'){'Ag-GIS.lnk'}else{'Ag-GIS ('+$Profile+').lnk'}
$shortcut=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $programs $shortcutName))
$shortcut.TargetPath=Join-Path $launcherDir 'Ag-GIS.exe'
$shortcut.WorkingDirectory=$launcherDir
$shortcut.IconLocation=(Join-Path $launcherDir 'Ag-GIS.ico')+',0'
$shortcut.Description='Ag-GIS - farming workflows built on open source tools'
$shortcut.Save()
$taskbarModule=Join-Path $env:APPDATA ('QGIS\QGIS3\profiles\'+$Profile+'\python\plugins\ag_tech_tooling\windows_taskbar.py')
& $python $taskbarModule --shortcut (Join-Path $programs $shortcutName) --profile $Profile
if($LASTEXITCODE -ne 0){throw 'Could not register the Ag-GIS taskbar shortcut identity. Run setup again.'}

Write-Output 'Installation complete. Open Ag-GIS from the Start menu.' 
