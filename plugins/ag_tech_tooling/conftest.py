# SPDX-License-Identifier: GPL-2.0-or-later
"""Pytest configuration for Ag-GIS plugin tests."""
import sys
from pathlib import Path

# Try to import qgis - if it fails, skip QGIS-dependent tests
QGIS_AVAILABLE = False
QGIS_ERROR = None

try:
    import qgis
    QGIS_AVAILABLE = True
except ImportError as e:
    QGIS_ERROR = str(e)

def pytest_configure(config):
    """Register markers for QGIS-dependent tests."""
    config.addinivalue_line(
        "markers", "qgis_only: mark tests that require QGIS to be installed"
    )
    
def pytest_collection_modifyitems(config, items):
    """Skip QGIS-dependent tests if QGIS is not available."""
    if not QGIS_AVAILABLE:
        skip_msg = f"QGIS not installed: {QGIS_ERROR}"
        for item in items:
            if "qgis_only" in item.keywords:
                item.add_marker(pytest.mark.skip(reason=skip_msg))
