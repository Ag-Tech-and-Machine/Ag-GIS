"""Exercise hierarchy persistence, native map filtering, icons and copy upgrades."""

import hashlib

import os

from pathlib import Path

import sys

import tempfile

from unittest.mock import patch



os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    from qgis.core import QgsApplication, QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

    from qgis.PyQt.QtWidgets import QDialog, QMainWindow, QPushButton, QTreeWidgetItemIterator

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.PyQt.QtCore import Qt
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this test
