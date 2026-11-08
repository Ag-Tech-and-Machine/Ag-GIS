# Ag-GIS repository context

Read root AGENTS.md first: it is the canonical engineering instruction source. Then read docs/DEVELOPMENT.md for checked commands, docs/ARCHITECTURE.md for the project map, docs/ROADMAP.md for current scope and docs/USER_COMMITMENTS.md for governing principles.

This is a Python QGIS plugin with Windows packaging, not a Node web application. Use qgis.PyQt/native PyQGIS; do not pip-install qgis. Plain Python basic CI is not integration or release acceptance. Preserve original farm data, local use, export and reversible unload. Do not include private data in public reports or commit credentials. Work on focused changes, preserve others' edits, update canonical docs and state exact test limits. Do not release, deploy or buy services as a side effect of a code change.
