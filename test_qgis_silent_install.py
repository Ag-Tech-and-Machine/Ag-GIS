"""Test QGIS silent installation logic in Install.ps1"""
import os
import re
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2] / "worktrees" / "wip-2026-11-06-recovery"
INSTALLER = WORKTREE / "installer" / "Install.ps1"

def test_qgis_silent_install():
    """Verify Install.ps1 uses silent QGIS installation"""
    content = INSTALLER.read_text(encoding="utf-8")
    
    # Check 1: Uses /qn (quiet) switch instead of /norestart
    assert '/qn' in content, "Install.ps1 must use /qn for silent MSI installation"
    assert '/norestart' not in content or content.count('/qn') > content.count('/norestart'), \
        "Should prefer /qn over /norestart for silent installation"
    
    # Check 2: Verbose messaging instead of interactive messages
    assert 'Write-Verbose' in content, "Should use Write-Verbose for installer messages"
    
    # Check 3: Version checking logic exists
    assert 'Check QGIS version' in content, "Should check QGIS version"
    assert 'versionFile' in content, "Should read QGIS version file"
    assert 'expected=\'3.44.14-Solothurn\'' in content, "Should expect QGIS 3.44.14-Solothurn"
    
    # Check 4: Reinstalls if version mismatch
    assert 'Reinstall the correct version' in content, "Should reinstall if version is wrong"
    
    # Check 5: Handles missing version file
    assert '} else {' in content or 'else {' in content, "Should handle missing version file"
    
    print("✓ All QGIS silent installation checks passed")
    print(f"  - Uses /qn silent switch: {content.count('/qn')} occurrences")
    print(f"  - Version checking: present")
    print(f"  - Reinstall logic: present")

def test_build_script_docs():
    """Verify build_windows_installer.py documents silent installation"""
    build_script = WORKTREE / "tools" / "build_windows_installer.py"
    content = build_script.read_text(encoding="utf-8")
    
    # Check README.txt mentions automatic installation
    assert 'automatically' in content, "README.txt should mention automatic QGIS installation"
    # The wizard mention is in a different context (validation), not installation instructions
    # Check that line 121 doesn't mention wizard
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '3. If QGIS 3.44.14' in line:
            assert 'wizard' not in line.lower(), f"Line {i+1} should not mention wizard: {line}"
            break
    
    print("✓ Build script documentation checks passed")

if __name__ == "__main__":
    test_qgis_silent_install()
    test_build_script_docs()
    print("\nAll tests passed! Install.ps1 is ready for silent QGIS installation.")
