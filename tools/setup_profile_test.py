"""Check Setup profile argument forwarding without installing anything (Windows)."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
with tempfile.TemporaryDirectory(prefix='ag-gis-setup-profile-') as temporary:
    directory = Path(temporary)
    exe = directory / 'Setup.exe'
    subprocess.run([str(compiler), '/nologo', '/target:exe', '/out:' + str(exe),
                    str(root / 'installer/Setup.cs')], check=True)
    (directory / 'Install.ps1').write_text(
        "param([string]$Profile)\nSet-Content -LiteralPath "
        "(Join-Path $PSScriptRoot 'profile.txt') -Value $Profile\n", encoding='ascii')
    for args, expected in [([], 'default'), (['--profile', 'aggis_test_123'], 'aggis_test_123')]:
        result = subprocess.run([str(exe), *args], input='\n', text=True,
                                capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr
        assert (directory / 'profile.txt').read_text().strip() == expected
        (directory / 'profile.txt').unlink()
    for args in [['--profile'], ['--profile', '../default'],
                 ['--profile', 'default;foo'], ['--other', 'x']]:
        result = subprocess.run([str(exe), *args], input='\n', text=True,
                                capture_output=True, timeout=30)
        assert result.returncode != 0 and not (directory / 'profile.txt').exists()
print('Setup profile argument tests passed; no installation performed')
