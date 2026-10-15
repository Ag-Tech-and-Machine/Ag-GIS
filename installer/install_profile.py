"""Install the bundled plugin using QGIS Python; stage, verify and recover on failure."""
import argparse
import configparser
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from datetime import datetime
from zipfile import ZipFile
from qgis.PyQt.QtCore import QSettings


def install(package, profile):
    profile = Path(profile)
    plugins = profile / "python/plugins"
    destination = plugins / "ag_tech_tooling"
    # Refuse junctions/symlinks anywhere in the write path.
    for path in (profile, *profile.parents, plugins.parent, plugins, destination):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError(f"Linked installation path is not supported: {path}")
    if destination.exists():
        metadata = configparser.ConfigParser()
        metadata.read(destination / "metadata.txt", encoding="utf-8")
        if metadata.get("general", "name", fallback="") not in {"Ag-GIS", "Ag Tech Tooling"}:
            raise ValueError("Refusing to replace an unrelated plugin")
    plugins.mkdir(parents=True, exist_ok=True)
    settings_file = profile / "QGIS/QGIS3.ini"
    backup = profile / "ag-tech-install-backups" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True)
    if settings_file.exists():
        shutil.copy2(settings_file, backup / "QGIS3.ini")
    previous = destination.exists()
    installed = False
    moved = False
    with tempfile.TemporaryDirectory(prefix="agtech-stage-", dir=plugins) as temporary:
        staged = Path(temporary) / "ag_tech_tooling"
        staged.mkdir()
        with ZipFile(package) as archive:
            if archive.testzip():
                raise ValueError("Corrupt plugin ZIP")
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Duplicate ZIP entry")
            for name in names:
                parts = PurePosixPath(name).parts
                if (len(parts) != 2 or parts[0] != "ag_tech_tooling"
                        or not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[1])
                        or parts[1] in {".", ".."} or "\\" in name):
                    raise ValueError(f"Unsafe ZIP entry: {name}")
                target = staged / parts[1]
                target.write_bytes(archive.read(name))
                assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(archive.read(name)).digest()
        metadata = configparser.ConfigParser()
        metadata.read(staged / "metadata.txt", encoding="utf-8")
        if metadata.get("general", "name", fallback="") not in {"Ag-GIS", "Ag Tech Tooling"}:
            raise ValueError("Wrong plugin package")
        for name in ("__init__.py", "plugin.py", "updates.py", "LICENSE", "USER_GUIDE.txt"):
            if not (staged / name).is_file():
                raise ValueError(f"Missing runtime file: {name}")
        try:
            if previous:
                destination.rename(backup / "ag_tech_tooling")
                moved = True
            staged.rename(destination)
            installed = True
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            settings = QSettings(str(settings_file), QSettings.IniFormat)
            settings.setValue("PythonPlugins/ag_tech_tooling", True)
            settings.sync()
            if settings.status() != QSettings.NoError:
                raise RuntimeError("Cannot enable plugin in profile settings")
        except Exception:
            if installed:
                shutil.rmtree(destination)
            if moved:
                (backup / "ag_tech_tooling").rename(destination)
            if (backup / "QGIS3.ini").exists():
                shutil.copy2(backup / "QGIS3.ini", settings_file)
            elif settings_file.exists():
                settings_file.unlink()
            raise
    print(f"Installed Ag-GIS {metadata['general']['version']}: {destination}")
    print(f"Recovery backup: {backup}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.profile):
        raise ValueError("Use a simple profile name")
    install(args.package, Path(os.environ["APPDATA"]) / "QGIS/QGIS3/profiles" / args.profile)
