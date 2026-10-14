# QGIS plugin development

- Plugin source is in `plugins/qgis_plugin_work`; keep GIS datasets outside this repository.
- Import Qt classes through `qgis.PyQt`, and use the Python runtime supplied with QGIS for integration checks.
- Keep `initGui()` and `unload()` paired so reloading leaves no duplicate actions or signal connections.
- Run `tools/check_plugin.py`, the PyQGIS smoke check and `tools/build_plugin.py` after changing plugin behaviour.
- Do not add passwords, tokens, local account caches or machine-specific settings to Git.
- Keep the isolated development profile and generated ZIPs out of commits.

## Management and documentation

- Act as the tooling manager: keep implementation, installation steps, operating instructions and verification status aligned.
- Update `docs/INSTALL.md` and `docs/TOOLING.md` in the same change as any feature, dependency, setup or workflow change. Do not defer documentation until release.
- Write numbered steps with prerequisites, exact commands or UI controls, expected results and recovery steps for known failures.
- Record dated changes, completed checks, limitations and next steps in `docs/WORK_LOG.md`. Distinguish verified behaviour from proposed or untested behaviour.
- Before reporting a change complete, ensure the relevant instructions describe the actual implementation. Run checks appropriate to code changes; documentation-only edits do not need a repeated integration test.
- Keep one canonical set of instructions in this repository. Export user-facing copies when useful; update them from the canonical sources.
