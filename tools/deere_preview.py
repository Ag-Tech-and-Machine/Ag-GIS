"""Inspect an unpacked GS3 export without changing it; JSON goes to stdout."""

import argparse

import json

import os

from pathlib import Path

import sys



os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

from ag_tech_tooling.deere_preview import inspect_export





def main():

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("folder", type=Path)

    parser.add_argument("--native", action="store_true", help="Probe with QGIS providers")

    args = parser.parse_args()

    app = None

    try:

        if args.native:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
                    from qgis.core import QgsApplication
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this module
