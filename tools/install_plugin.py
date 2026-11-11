"""Install the built plugin into an existing QGIS user profile and enable it."""

import argparse

import configparser

import os

import re

import shutil

from datetime import datetime

from pathlib import Path, PurePosixPath

from zipfile import ZipFile

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.PyQt.QtCore import QSettings
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this module
