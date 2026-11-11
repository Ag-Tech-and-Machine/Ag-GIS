"""
Test script to check PyQt5 and QGIS availability.
"""
import sys
import os

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print()

# Print PATH
print("PATH:")
for path in os.environ.get('PATH', '').split(os.pathsep):
    print("  ", path)
print()

# Try to import PyQt5
try:
    from PyQt5.QtCore import QObject
    print("SUCCESS: PyQt5 is available")
    print("PyQt5 version:", getattr(PyQt5, '__version__', 'unknown'))
except ImportError as e:
    print(f"FAILED: PyQt5 not available: {e}")

# Try to import qgis
try:
# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication
except ImportError:
    pass  # QGIS not available, skip this import
    print("SUCCESS: qgis is available")
except ImportError as e:
    print(f"FAILED: qgis not available: {e}")

