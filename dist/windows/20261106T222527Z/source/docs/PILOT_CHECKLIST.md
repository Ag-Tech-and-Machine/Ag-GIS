# Controlled farmer-workflow pilot

Ag-GIS is experimental and **not release-ready**. This checklist prepares a small supervised pilot, not a public release or a claim of completed user acceptance.

## Scope and prerequisites

1. Use a separate test profile and a disposable local workspace outside the source repository. Do not overwrite the default profile or test recovery on real farm records. Save the user's current map before any installation or restart.
2. Use synthetic or explicitly approved non-sensitive datasets. Record the tested plugin version, source snapshot, package SHA-256, runtime version and Windows version. Version alone is insufficient: several local development snapshots can share a version.
3. Test the extracted plugin ZIP as well as source. The native project/layer/provider/writer, layer-tree, file-picker and save/load capabilities supply the implementation; this pilot tests the farmer-facing path around them.
4. Keep public feedback free of private map names, file paths, farm data, screenshots and logs. Sharing or publication needs a separate deliberate decision.

## 1. First-use workflow — hands-on acceptance

Record pass/fail, unexpected clicks, wording that needed explanation and recovery for each step. Do not mark these complete based only on automated tests.

- [ ] Launch the exact pilot package in the isolated profile; confirm the toolbar is visible in Simple view.
- [ ] Click **New Project**. Confirm a separate numbered workspace is created without replacing an existing folder.
- [ ] Rename organisation, client, farm and field using **Manage Data**. Confirm each remains a separate level and persists after closing the dialog.
- [ ] Add another field, then cancel an Add dialog. Confirm cancellation adds nothing.
- [ ] Use **Data In → Choose File**. Review type and explicitly select the first field when no boundary exists. Confirm nothing is imported before **Import to Field**.
- [ ] Import a supported vector file. Confirm **Saved**, **Whole Field → Imported Data**, correct field/type and a visible map result. Select the dataset and try **Whole Map**.
- [ ] Choose each background, then turn the selected background off. Confirm farm data remains visible. Do not mistake dated 10 m / 30 m imagery for detailed aerial photography.
- [ ] Use **Filter Data** for each field, then All fields / All data types. Confirm unrelated layers and manually hidden datasets are preserved.
- [ ] **Save Map**, open another disposable workspace, then **Open Project → Farm.qgz**. Confirm datasets, hierarchy, background choice, labels/styles and saved extent return. Repeat with **Data/farm.gpkg**.
- [ ] With unsaved map changes, try opening another farm and choose **Cancel**. Confirm the existing map and unsaved changes remain.
- [ ] Disable/re-enable the plugin in the test profile. Confirm native layout restoration and no duplicated toolbar/actions after re-enable.

Acceptance: a farmer completes this path without a support call or coaching. Record assistance as friction, not a pass.

## 2. Safety and recovery — disposable data only

- [ ] Hash the source file and its supporting files before/after import; expect identical bytes.
- [ ] Import the same dataset to the same field/type twice; expect an already-saved result, not a duplicate.
- [ ] Close Data In before importing, cancel a scan and rescan a missing path. Confirm no unintended data and no stale selectable rows.
- [ ] Test missing CRS, partial/overlapping field boundaries and ambiguous matches. Expect explicit review, not silent assignment. Before saving, correct a proposed destination and verify the final field. Post-import reassignment is not assumed implemented.
- [ ] Exercise simulated copy/catalogue failure with the automated test below; expect no partial new dataset and no damage to an existing one. Do not fill a real disk or cut power to simulate this.
- [ ] Stop a multi-item import; verify earlier completed copies remain and unfinished items are reported. This is not an all-items transaction.
- [ ] Close the disposable workspace, move its entire folder, make the original source unavailable without deleting it, and reopen. Confirm managed vectors/rasters remain valid. Restore the source afterwards.
- [ ] In a separate disposable copy, remove a required workspace file and attempt opening. Expect a clear refusal and unchanged current map; restore the file and retry.

Limits: these checks are not power-loss durability, general dependency-complete backup, multi-user/NAS editing or arbitrary hardware/format compatibility tests. No automated backup service is implied.

## 3. Local pilot candidate gate

- [ ] Review the dirty working tree by workstream. Preserve unrelated edits. Select and approve the exact pilot scope; do not bulk-stage or bulk-commit it.
- [ ] Record an immutable source snapshot and exact package hash, including untracked runtime modules/resources and the bundled user guide. Do not rely solely on the HEAD commit.
- [ ] Run the checks below on that snapshot. Review warnings; retain exact output locally, not in public feedback.
- [ ] Install only into a separate test profile; read back installed files and compare them to the selected package.
- [ ] Complete the hands-on and recovery checks above on the installed candidate, including startup/taskbar checks if shipping the Windows launcher.
- [ ] Agree a small pilot group, safe sample task and feedback route. Explain experimental status, limitations and how to return to the previous installation.
- [ ] Obtain separate approval before committing, publishing, tagging, releasing or distributing an installer. No such action is authorised by this checklist.

## Reproducible automated checks

From the source root:

```text
python tools/check_repository.py
python tools/check_plugin.py
node tools/feedback_workflow_test.cjs
```

In PowerShell with the installed runtime:

```powershell
.\scripts\check.ps1 -QgisRoot 'C:\Program Files\QGIS 3.44.14'
```

Expected: exit 0. The integration script builds the plugin ZIP and exercises the extracted package. Key evidence: `farm_project_test.py` and `default_workspace_test.py` (creation/open/cancel), `data_in_test.py` (scan/import/duplicates), `import_placement_test.py` (CRS/containment/ambiguity), `managed_data_test.py` (source hashes, copy failure, original-path removal and move/reopen), and the browser/presentation/lifecycle tests. These use synthetic fixtures and test interfaces; they do not prove an unassisted farmer can use the real desktop.

If a check fails, stop candidate promotion, preserve the error and fix/retest the cause. If the runtime is missing, report integration unavailable rather than passed.

## Evidence recorded 15 October 2026

- Baseline repository/plugin checks, feedback-workflow test and full native source/extracted-package suite passed on the current shared development checkout before the Open Project improvement.
- Live read-only inspection found an open Ag-GIS map with an unsaved marker. It was not modified, closed or used for testing.
- Open Project regression first failed because Farm.qgz was rejected; the implementation now accepts the map through the same validated project loader. Final post-change checks are recorded in WORK_LOG.md.
- Post-change source/extracted-package checks passed. A separate installed-package desktop automation also passed creation, explicit destination/import, duplicate protection, unchanged source hash and save/reopen. Its final Simple view screenshot shows the managed point and hierarchy. File selection was scripted; this does not mark the hands-on checklist complete. See `dist/workflow-review/20261015/` for local evidence.
- Hands-on isolated-profile acceptance, immutable pilot-snapshot selection, installed-candidate verification and farmer feedback remain unchecked. This checklist is preparation, not pilot sign-off.
