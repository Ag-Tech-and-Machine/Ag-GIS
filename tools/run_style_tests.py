"""
Run operation_style_test.py and dataset_style_test.py using QGIS Python runtime.
"""
import sys

# Set environment variables BEFORE importing anything
os = __import__('os')
sys.path.insert(0, r'C:\Program Files\QGIS 3.44.14\apps\qgis-ltr\python')

# Set environment
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['AGTECH_TEST_PLUGIN_ROOT'] = r'C:\temp\Documents\Projects\repos\ag-tech-tooling\plugins'
os.environ['AGTECH_TEST_SCRATCH'] = r'C:\temp\cache\scratch'
os.environ['OSGEO4W_ROOT'] = r'C:\Program Files\QGIS 3.44.14'
os.environ['QGIS_PREFIX_PATH'] = r'C:\Program Files\QGIS 3.44.14\apps\qgis-ltr'
os.environ['GDAL_FILENAME_IS_UTF8'] = 'YES'
os.environ['VSI_CACHE'] = 'TRUE'
os.environ['VSI_CACHE_SIZE'] = '1000000'
os.environ['QT_PLUGIN_PATH'] = r'C:\Program Files\QGIS 3.44.14\apps\qgis-ltr\qtplugins;C:\Program Files\QGIS 3.44.14\apps\qt5\plugins'
os.environ['PYTHONPATH'] = r'C:\Program Files\QGIS 3.44.14\apps\qgis-ltr\python'

# Import NumPy FIRST (to ensure we use QGIS's version)
import numpy as np
print(f"NumPy version: {np.__version__}")

# Import QGIS
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry

app = QgsApplication([], False)
app.initQgis()

# Set up test directories
test_dir = r'C:\temp\cache\scratch'
os.environ['AGTECH_TEST_SCRATCH'] = test_dir
import tempfile
tempfile.tempdir = test_dir
for key in ('TEMP', 'TMP', 'TMPDIR'):
    os.environ[key] = test_dir

print("=" * 60)
print("RUNNING operation_style_test.py")
print("=" * 60)
print()

# Run operation_style_test.py
import importlib.util
spec = importlib.util.spec_from_file_location("operation_style_test", r'C:\temp\Documents\Projects\repos\ag-tech-tooling\tools\operation_style_test.py')
op_style_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op_style_module)

try:
    op_style_module.check_styles()
    print("SUCCESS: operation_style_test.py passed!")
except Exception as e:
    print(f"FAILED: operation_style_test.py failed with: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("RUNNING dataset_style_test.py")
print("=" * 60)
print()

# Run dataset_style_test.py
spec2 = importlib.util.spec_from_file_location("dataset_style_test", r'C:\temp\Documents\Projects\repos\ag-tech-tooling\tools\dataset_style_test.py')
dataset_style_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(dataset_style_module)

try:
    dataset_style_module.check()
    print("SUCCESS: dataset_style_test.py passed!")
except Exception as e:
    print(f"FAILED: dataset_style_test.py failed with: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("ALL TESTS PASSED SUCCESSFULLY!")
print("=" * 60)

app.exitQgis()
