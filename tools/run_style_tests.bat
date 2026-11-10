@echo off
REM Run operation_style_test.py and dataset_style_test.py using QGIS Python runtime

set "OSGEO4W_ROOT=C:\Program Files\QGIS 3.44.14"
set "PATH=%OSGEO4W_ROOT%\apps\Qt5\bin;%OSGEO4W_ROOT%\apps\qgis-ltr\bin;%OSGEO4W_ROOT%\apps\Python312;%PATH%"
set "AGTECH_TEST_PLUGIN_ROOT=C:\Users\[Maintainer]\Documents\Projects\repos\ag-tech-tooling\plugins"
set "AGTECH_TEST_SCRATCH=C:\Users\[Maintainer]\AppData\Local\hermes\cache\scratch"
set "QGIS_PREFIX_PATH=C:\Program Files\QGIS 3.44.14\apps\qgis-ltr"
set "PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis-ltr\python"
set "QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis-ltr\qtplugins;%OSGEO4W_ROOT%\apps\qt5\plugins"

"C:\Program Files\QGIS 3.44.14\apps\Python312\python.exe" "C:\Users\[Maintainer]\Documents\Projects\repos\ag-tech-tooling\tools\run_style_tests.py"
