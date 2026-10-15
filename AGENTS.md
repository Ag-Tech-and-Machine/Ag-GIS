# QGIS plugin development

## Purpose

Build farmer-friendly, open-source tooling that simplifies agricultural workflows and automates GIS work. Follow `docs/PURPOSE.md`: use farming language, sensible defaults, visible results and safe handling of users' original data. Keep instructions in step with the tools.

## Development priority

- Interface optimisation is priority one. Refine the farmer-facing layout, navigation, wording and task flow before expanding the data/conversion feature set.
- Simple view keeps map and Layers as the primary workspace, with its switch in the bottom-right status rail. Keep advanced QGIS tools accessible through reversible full-view restoration.
- The left Farm Data browser reuses the native layer-tree model/selection and wraps its delegate for semantic hierarchy icons. Preserve native layer legends, visibility, editing and unrelated data; restore the original presentation on unload. Use the bundled icon system consistently with Manage Data.
- The dedicated Ag Tech Tooling toolbar at the top is the main entry point for farmer workflows. Keep it visible in Simple view, use clear labels and reuse native QGIS actions without altering their shared labels or ownership.
- Maintain Organisation → Client → Farm → Field with Client as a first-class entity. Within Field, keep Whole Field reference data separate from Seasons/crop work. Version 0.6.0 implements schema 2, one-click Documents workspace creation and the complete native Layers tree; distinguish those features from planned seasonal datasets/history in docs/FARM_DATA_MODEL.md. Upgrade legacy data through a validated copy, preserving the source.
- Prefer existing QGIS actions, widgets, dialogs and Processing tools wherever practical. Add a small farmer-friendly interface around native capabilities when their standard interface is too complex; avoid duplicating supported GIS behaviour.
- Quick New uses the operating system Documents location and editable starter names. Keep all organisation/client/farm/field/season levels separate and short in Layers; preserve existing workspace folders. Explicit path/CRS setup stays in the menu-only options form.
- Before each feature, identify the native QGIS capability to reuse and the interface simplification it provides. Verify discoverability, clear outcomes, cancellation, saved work and unload/reload behaviour with the implemented workflow.

- Plugin source is in `plugins/ag_tech_tooling`; keep GIS datasets outside this repository.
- Import Qt classes through `qgis.PyQt`, and use the Python runtime supplied with QGIS for integration checks.
- Ship every runtime feature inside the plugin ZIP, including its modules/resources and user guide. Verify workflows against the extracted package, not only the source checkout.
- Use native PyQGIS project/layer/provider/writer APIs and QGIS Processing/coordinate transforms for GIS operations. Use QGIS's bundled providers; do not add a separate GIS engine or external command-line dependency for an operation QGIS supports. Document any justified exception before introducing it.
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
