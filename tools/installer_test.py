"""Exercise bundled installation in temporary profiles; never touch the user's profile."""
import configparser
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
from zipfile import ZipFile
from check_plugin import ROOT, check
sys.path.insert(0, str(ROOT / "installer"))
import install_profile
from qgis.PyQt.QtCore import QSettings

version = check()
package = ROOT / "dist" / f"ag_tech_tooling-{version}.zip"
with tempfile.TemporaryDirectory(prefix="agtech-installer-test-") as temporary:
    root = Path(temporary)
    profile = root / "new-profile"
    install_profile.install(package, profile)
    target = profile / "python/plugins/ag_tech_tooling"
    with ZipFile(package) as archive:
        for name in archive.namelist():
            assert (target / Path(name).name).read_bytes() == archive.read(name)
    settings = QSettings(str(profile / "QGIS/QGIS3.ini"), QSettings.IniFormat)
    assert settings.value("PythonPlugins/ag_tech_tooling", False, type=bool)
    (target / "obsolete.py").write_text("old runtime", encoding="utf-8")
    install_profile.install(package, profile)
    assert not (target / "obsolete.py").exists()
    assert list((profile / "ag-tech-install-backups").glob("*/ag_tech_tooling/obsolete.py"))
    original = (target / "plugin.py").read_bytes()
    class FailedSettings:
        IniFormat = QSettings.IniFormat
        NoError = QSettings.NoError
        def __init__(self, *args): pass
        def setValue(self, *args): pass
        def sync(self): pass
        def status(self): return QSettings.AccessError
    with patch.object(install_profile, "QSettings", FailedSettings):
        try:
            install_profile.install(package, profile)
            raise AssertionError("Expected settings failure")
        except RuntimeError:
            pass
    assert (target / "plugin.py").read_bytes() == original
    bad = root / "unsafe.zip"
    with ZipFile(bad, "w") as archive:
        archive.writestr("ag_tech_tooling/../../escaped", "bad")
    try:
        install_profile.install(bad, profile)
        raise AssertionError("Unsafe archive accepted")
    except ValueError:
        pass
    assert (target / "plugin.py").read_bytes() == original
    unrelated = root / "unrelated/python/plugins/ag_tech_tooling"
    unrelated.mkdir(parents=True)
    (unrelated / "metadata.txt").write_text("[general]\nname=Other plugin\n", encoding="utf-8")
    try:
        install_profile.install(package, root / "unrelated")
        raise AssertionError("Unrelated plugin overwritten")
    except ValueError:
        pass
    assert "Other plugin" in (unrelated / "metadata.txt").read_text()
print("Installer fresh profile, exact bytes, upgrade, recovery, unsafe ZIP and unrelated-plugin checks passed")
