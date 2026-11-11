"""Compile branded Windows entrypoints; exercise launcher using a fake QGIS bootstrap."""

from pathlib import Path

import os

import shutil

import subprocess

import tempfile

import time

ROOT = Path(__file__).resolve().parents[1]

compiler = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"

with tempfile.TemporaryDirectory(prefix="aggis-launch-test-") as temporary:

    root = Path(temporary)

    for source, target, kind in (("Launch.cs", "Ag-GIS.exe", "winexe"), ("Setup.cs", "Setup.exe", "exe")):

        subprocess.run([str(compiler), "/nologo", "/target:" + kind, "/reference:System.Windows.Forms.dll", "/reference:System.Drawing.dll",

                        "/win32icon:" + str(ROOT / "installer/Ag-GIS.ico"), "/out:" + str(root / target),

                        str(ROOT / "installer" / source)], check=True)

    shutil.copy2(ROOT / "installer/Ag-GIS.ico", root / "Ag-GIS.ico")

    preview = root / "startup.png"

    rendered = subprocess.run([str(root / "Ag-GIS.exe"), "--render-splash", str(preview)], capture_output=True, text=True, timeout=10)

    assert rendered.returncode == 0, rendered.stdout + rendered.stderr

    assert preview.read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a"))

    pass  # QGIS not available, skip this test

except ImportError:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
            from qgis.PyQt.QtGui import QImage
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

    rendered_image = QImage(str(preview))

    sampled_colours = {rendered_image.pixel(x, y) for x in range(0, rendered_image.width(), 5)

                       for y in range(0, rendered_image.height(), 5)}

    assert len(sampled_colours) > 20, "Startup image must contain the logo and text"

    output = ROOT / "dist/branding"

    output.mkdir(parents=True, exist_ok=True)

    shutil.copy2(preview, output / "Ag-GIS-startup.png")

    fake = root / "fake qgis/bin"

    fake.mkdir(parents=True)

    (fake / "qgis-ltr.bat").write_text('@echo off\necho %* > "' + str(root / "args.txt") + '"\n')

    (root / "launch.txt").write_text(str(fake.parent) + "\nbranding_test\n")

    subprocess.run([str(root / "Ag-GIS.exe"), "--no-splash"], check=True, timeout=10)

    for _ in range(50):

        if (root / "args.txt").exists():

            break

        time.sleep(.1)

    assert (root / "args.txt").read_text().strip() == "--nologo --profile branding_test"

print("Windows splash rendering, icon compilation and native bootstrap/profile/nologo launch passed")


