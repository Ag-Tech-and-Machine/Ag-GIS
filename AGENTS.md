# QGIS plugin development

- Plugin source is in `plugins/qgis_plugin_work`; keep GIS datasets outside this repository.
- Import Qt classes through `qgis.PyQt`, and use the Python runtime supplied with QGIS for integration checks.
- Keep `initGui()` and `unload()` paired so reloading leaves no duplicate actions or signal connections.
- Run `tools/check_plugin.py`, the PyQGIS smoke check and `tools/build_plugin.py` after changing plugin behaviour.
- Do not add passwords, tokens, local account caches or machine-specific settings to Git.
- Keep the isolated development profile and generated ZIPs out of commits.
