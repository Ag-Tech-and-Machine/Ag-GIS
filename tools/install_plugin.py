"""Install the built plugin into an existing QGIS user profile and enable it."""
import argparse
import configparser
import os
import re
import shutil
from datetime import datetime
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from qgis.PyQt.QtCore import QSettings
from check_plugin import ROOT, check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.profile):
        raise ValueError("Use a simple QGIS profile name")
    profile = Path(os.environ["APPDATA"]) / "QGIS/QGIS3/profiles" / args.profile
    if not profile.is_dir():
        raise ValueError(f"Profile does not exist: {profile}")
    version = check()
    package = ROOT / "dist" / f"ag_tech_tooling-{version}.zip"
    plugins = profile / "python/plugins"
    destination = plugins / "ag_tech_tooling"
    backup = ROOT / "dist/install-backups" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    if destination.is_symlink() or destination.resolve() != plugins.resolve() / "ag_tech_tooling":
        raise ValueError("Installed plugin destination is linked or unexpected")
    if destination.exists():
        metadata = configparser.ConfigParser()
        metadata.read(destination / "metadata.txt", encoding="utf-8")
        if metadata.get("general", "name", fallback="") not in {"Ag-GIS", "Ag Tech Tooling"}:
            raise ValueError("Refusing to overwrite an unrelated plugin")
        shutil.copytree(destination, backup / "ag_tech_tooling")
    settings_file = profile / "QGIS/QGIS3.ini"
    if settings_file.exists():
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(settings_file, backup / "QGIS3.ini")
    with ZipFile(package) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupt plugin archive")
        entries = archive.infolist()
        for entry in entries:
            parts = PurePosixPath(entry.filename).parts
            if len(parts) != 2 or parts[0] != "ag_tech_tooling" or parts[1] in {".", ".."} or "\\" in entry.filename:
                raise ValueError(f"Unexpected archive entry: {entry.filename}")
        destination.mkdir(parents=True, exist_ok=True)
        for entry in entries:
            target = destination / PurePosixPath(entry.filename).name
            target.write_bytes(archive.read(entry))
            if target.read_bytes() != archive.read(entry):
                raise ValueError(f"Installed file differs: {target.name}")
    settings = QSettings(str(settings_file), QSettings.IniFormat)
    settings.setValue("PythonPlugins/ag_tech_tooling", True)
    settings.sync()
    if settings.status() != QSettings.NoError:
        raise RuntimeError("Could not save the enabled-plugin setting")
    print(f"Installed and enabled Ag-GIS {version}: {destination}")
    print(f"Settings backup: {backup}")


if __name__ == "__main__":
    main()
