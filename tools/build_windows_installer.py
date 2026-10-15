"""Build an offline Windows setup bundle from a hash-recorded source snapshot."""
import argparse
import configparser
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

ROOT = Path(__file__).resolve().parents[1]
QGIS_FILE = "QGIS-OSGeo4W-3.44.14-1.msi"
QGIS_SHA256 = "0a579f980dcec85be2ecb47c5f08234ca6ce7b625c3cb9543eded1f43d445b46"
POWERSHELL = str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qgis-root", type=Path, default=Path(r"C:\Program Files\QGIS 3.44.14"))
    parser.add_argument("--msi", type=Path, default=ROOT / "dist/vendor" / QGIS_FILE)
    parser.add_argument("--validation-from", type=Path, help="Reuse successful plugin checks only when every input except this builder and Setup.cs is byte-identical")
    parser.add_argument("--source-from", type=Path, help="Use a recorded source snapshot instead of the moving shared checkout; refresh only builder and launcher")
    args = parser.parse_args()
    if sha(args.msi) != QGIS_SHA256:
        raise ValueError("Official QGIS installer SHA-256 does not match the pinned upstream manifest")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    build = ROOT / "dist/windows" / stamp
    snapshot = build / "source"
    snapshot.mkdir(parents=True)
    source_root = args.source_from.resolve() if args.source_from else ROOT
    if args.source_from and not (source_root / "SOURCE-SNAPSHOT.json").is_file():
        raise ValueError("--source-from requires a recorded source snapshot")
    roots = [source_root / name for name in ("plugins", "tools", "scripts", "installer", "docs")]
    sources = sorted([p for directory in roots for p in directory.rglob("*")
                      if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
                     + [source_root / name for name in ("AGENTS.md", "README.md", "LICENSE", ".gitignore")])
    before = {str(p.relative_to(source_root)).replace("\\", "/"): sha(p) for p in sources}
    for source in sources:
        if source.is_symlink():
            raise ValueError(f"Linked source: {source}")
        target = snapshot / source.relative_to(source_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    copied = {name: sha(snapshot / name) for name in before}
    after = {name: sha(source_root / name) for name in before}
    if before != copied or before != after:
        raise RuntimeError("Source changed during capture. Retry; nothing was packaged.")
    if args.source_from:
        for name in ("installer/Setup.cs", "tools/build_windows_installer.py"):
            shutil.copy2(ROOT / name, snapshot / name)
            copied[name] = sha(snapshot / name)
    git = shutil.which("git") or str(Path(os.environ["LOCALAPPDATA"]) / "Programs/Git/cmd/git.exe")
    record = {"capturedUtc": stamp, "gitHead": subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "workingTreeIncluded": True, "sourceFiles": copied}
    if args.source_from:
        record["sourceSnapshotBase"] = str(source_root)
    (snapshot / "SOURCE-SNAPSHOT.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    # All checks run against the frozen files, including the extracted plugin package.
    environment = {key: value for key, value in os.environ.items() if key.upper() != "PSMODULEPATH"}
    if args.validation_from:
        prior = args.validation_from.resolve()
        prior_record = json.loads((prior / "source/SOURCE-SNAPSHOT.json").read_text(encoding="utf-8"))
        exclude = {"installer/Setup.cs", "tools/build_windows_installer.py"}
        relevant = lambda files: {name: digest for name, digest in files.items() if name not in exclude}
        if relevant(prior_record["sourceFiles"]) != relevant(copied):
            raise ValueError("Validation reuse refused: plugin or test inputs changed. Run without --validation-from.")
        prior_log = (prior / "validation.log").read_text(encoding="utf-8")
        if "Extracted plugin ZIP passed lifecycle and farm workflow checks" not in prior_log:
            raise ValueError("Previous plugin checks were not successful")
        record["pluginValidationReusedFrom"] = str(prior)
        (snapshot / "SOURCE-SNAPSHOT.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        (build / "validation.log").write_text("Identical plugin/test inputs; validation reused from " + str(prior) + "\n" + prior_log, encoding="utf-8")
        (snapshot / "dist").mkdir()
        for package in (prior / "source/dist").glob("ag_tech_tooling-*.zip"):
            shutil.copy2(package, snapshot / "dist" / package.name)
        print("Reused successful source/extracted-plugin checks: all plugin and test inputs are byte-identical", flush=True)
    else:
        result = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(snapshot / "scripts/check.ps1"),
                                 "-QgisRoot", str(args.qgis_root)], capture_output=True, text=True, env=environment)
        (build / "validation.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        print(result.stdout, flush=True)
        if result.returncode:
            raise RuntimeError(f"Snapshot validation failed. See {build / 'validation.log'}")
    meta = configparser.ConfigParser()
    meta.read(snapshot / "plugins/ag_tech_tooling/metadata.txt", encoding="utf-8")
    version = meta["general"]["version"]
    bundle = build / f"Ag-GIS-{version}-Windows"
    bundle.mkdir()
    plugin_file = f"ag_tech_tooling-{version}.zip"
    shutil.copy2(snapshot / "dist" / plugin_file, bundle / plugin_file)
    shutil.copy2(args.msi, bundle / QGIS_FILE)
    for name in ("Install.ps1", "install_profile.py", "Setup.cs"):
        shutil.copy2(snapshot / "installer" / name, bundle / name)
    compiler = Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")
    subprocess.run([str(compiler), "/nologo", "/target:exe", "/platform:anycpu", f"/out:{bundle / 'Setup.exe'}", str(bundle / "Setup.cs")], check=True)
    shutil.copy2(snapshot / "LICENSE", bundle / "LICENSE.txt")
    shutil.copy2(snapshot / "SOURCE-SNAPSHOT.json", bundle / "SOURCE-SNAPSHOT.json")
    with ZipFile(bundle / "Ag-GIS-source.zip", "w", ZIP_DEFLATED) as archive:
        for name in copied:
            archive.write(snapshot / name, name)
        archive.write(snapshot / "SOURCE-SNAPSHOT.json", "SOURCE-SNAPSHOT.json")
    (bundle / "README.txt").write_text(
        f"Ag-GIS {version} offline Windows installer\n\n"
        "1. Extract ALL files to a local folder. Keep Setup.exe beside the other files.\n"
        "2. Save your map and close QGIS. Double-click Setup.exe as your normal user.\n"
        "3. If QGIS 3.44.14 is missing, complete its official wizard and administrator prompt.\n"
        "4. Open QGIS normally. The Ag-GIS toolbar is enabled in the default profile.\n\n"
        "Other profile: powershell -NoProfile -ExecutionPolicy Bypass -File .\\Install.ps1 -Profile profile_name\n"
        "Verify without installing: powershell -NoProfile -ExecutionPolicy Bypass -File .\\Install.ps1 -VerifyOnly\n"
        "Recovery copies: %APPDATA%\\QGIS\\QGIS3\\profiles\\<profile>\\ag-tech-install-backups.\n"
        "Close QGIS before restoring the backed-up plugin folder and QGIS3.ini.\n"
        "To uninstall only this plugin use QGIS Manage and Install Plugins. Farm files remain separate.\n"
        "Updates: Plugins > Ag-GIS > Check for Updates. Open the private GitHub release, then Install downloaded ZIP.\n"
        "GitHub: https://github.com/JamRov/Ag-GIS/releases/latest (repository access required).\n"
        "This setup launcher is unsigned. No credentials are included.\n"
        "QGIS is unmodified and includes Python, Qt, GDAL and its providers. Optional projection grids are separate.\n"
        "QGIS installer: https://download.qgis.org/downloads/" + QGIS_FILE + "\n"
        "QGIS project/source and bundled component licensing: https://qgis.org/ and https://github.com/qgis/QGIS/tree/final-3_44_14\n"
        "Ag-GIS GPL-2.0-or-later source is included in Ag-GIS-source.zip.\n"
        "Validated on an existing QGIS workstation; clean-machine wizard/UAC checks remain pending.\n", encoding="utf-8")
    manifest = {"version": version, "qgisFile": QGIS_FILE, "pluginFile": plugin_file,
                "qgisUrl": "https://download.qgis.org/downloads/" + QGIS_FILE,
                "qgisHashSource": "https://github.com/microsoft/winget-pkgs/blob/master/manifests/o/OSGeo/QGIS_LTR/3.44.14/OSGeo.QGIS_LTR.installer.yaml",
                "files": [{"path": p.name, "sha256": sha(p)} for p in sorted(bundle.iterdir())]}
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(bundle / "Install.ps1"), "-VerifyOnly"], check=True, env=environment)
    output = build.parent / f"{bundle.name}-{stamp}.zip"
    with ZipFile(output, "w", ZIP_STORED) as archive:
        for path in sorted(bundle.iterdir()):
            archive.write(path, f"{bundle.name}/{path.name}")
    with ZipFile(output) as archive:
        if archive.testzip():
            raise ValueError("Offline bundle ZIP failed CRC check")
    output.with_suffix(".zip.sha256").write_text(f"{sha(output)}  {output.name}\n", encoding="ascii")
    (ROOT / "dist/windows/LATEST.txt").write_text(str(output) + "\n", encoding="utf-8")
    print(f"Offline installer: {output}", flush=True)


if __name__ == "__main__":
    main()
