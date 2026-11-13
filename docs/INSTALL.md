# Installation and setup

## Follow development and fixes — 21 October 2026

The homepage now links to the [development plan & pipeline](DEVELOPMENT_PLAN.md).
Use it to follow reported and confirmed issues, handovers and verification. A fix
in source or a developer's local installation is not necessarily in your download;
check the selected release's notes. This documentation update changes no plugin,
installer, profile setting or installation prerequisite.

## Repository presentation — 19 October 2026

The README now separates the development screenshot from experimental downloads.
Choose a release and read its own installation notes; new repository artwork does
not update an installed application or rebuild an installer. See
[repository presentation](REPOSITORY_PRESENTATION.md) for asset provenance and
rebuild/recovery steps. No new installation dependency is introduced.

Last updated: 15 October 2026.

## Tested workstation

- Windows workstation, local account Michael.
- Git 2.55.0.windows.3.
- QGIS 3.44.14 LTR, installed in `C:\Program Files\QGIS 3.44.14`.
- Repository: `C:\Users\Michael\Documents\Projects\repos\ag-tech-tooling`.
- Git author: Michael `<admin@agtechandmachine.com>`.

QGIS includes the Python, Qt and PyQGIS runtime used by this project. A separate system Python is optional for syntax checks and packaging; it does not replace the QGIS runtime.

## 1. Install Git

1. Install Git for Windows from https://git-scm.com/downloads/win. If WinGet is available, use:

   ```powershell
   winget install --id Git.Git --exact --source winget
   ```

2. Open a new PowerShell window and verify:

   ```powershell
   git --version
   ```

   Expected: a Git version, rather than a command-not-found error. Git was already installed on the tested workstation.

3. Configure the author for this workstation:

   ```powershell
   git config --global user.name "Michael"
   git config --global user.email "admin@agtechandmachine.com"
   git config --global init.defaultBranch main
   ```

   Another developer should use their own author identity. These commands set commit metadata; they do not sign in to GitHub or Microsoft.

4. Verify the identity:

   ```powershell
   git config --global --get user.name
   git config --global --get user.email
   ```

## 2. Install QGIS LTR

1. Use the official download page: https://qgis.org/download/. Choose the long-term release for the QGIS 3.x development target.
2. To reproduce the tested version with WinGet:

   ```powershell
   winget install --id OSGeo.QGIS_LTR --exact --version 3.44.14 --source winget
   ```

   Approve the Windows administrator prompt when the installer requests it. If this version is no longer listed, obtain a suitable LTR installer from QGIS and rerun the checks before declaring that version supported.

3. Wait for installation to finish. On the tested workstation WinGet reported `Successfully installed`.
4. Confirm the installation has a QGIS launcher and Python wrapper. For the tested version:

   ```powershell
   Test-Path 'C:\Program Files\QGIS 3.44.14\bin\qgis-ltr.bat'
   Test-Path 'C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat'
   ```

   Expected: `True` for both. A leftover folder named QGIS is not proof that QGIS is installed.

## 3. Open the repository

1. For this machine, open the existing repository; do not initialise it again:

   ```powershell
   Set-Location 'C:\Users\Michael\Documents\Projects\repos\ag-tech-tooling'
   git status
   ```

   Expected: branch `main`. After committed setup, the working tree is clean.

2. On another machine, transfer the repository or clone it once a remote has been created. The private release repository is https://github.com/JamRov/Ag-GIS; the existing checkout's origin now points there. See the published-install section below.
3. Keep datasets outside the repository. The `.gitignore` excludes development profiles, generated ZIPs and common GIS datasets.

## 4. Verify the tooling

1. From the repository root, run:

   ```powershell
   .\scripts\check.ps1
   ```

2. If automatic discovery picks the wrong installation, supply the root explicitly:

   ```powershell
   .\scripts\check.ps1 -QgisRoot 'C:\Program Files\QGIS 3.44.14'
   ```

3. Expected output includes:
   - `Plugin syntax and metadata OK`
   - `QGIS plugin action, simple-view restoration and reload checks passed`
   - `Plugin ZIP ready:` followed by the archive path.

The smoke check uses real Qt/PyQGIS with an interface adapter. It does not replace the manual QGIS interface check below.

## 5. Launch and enable the development plugin

1. Run:

   ```powershell
   .\scripts\launch-qgis.ps1
   ```

   Or pass `-QgisRoot 'C:\Program Files\QGIS 3.44.14'` to select that installation.

2. QGIS should open with the isolated `ag-tech-tooling-dev` profile. The profile is stored under `.dev-profiles`, outside Git tracking. The launcher exposes the repository's `plugins` directory using `QGIS_PLUGINPATH`.
3. In QGIS, open **Plugins → Manage and Install Plugins → Installed**.
4. Enable **Ag-GIS**.
5. Use its toolbar action or **Plugins → Ag-GIS** menu action.
6. Expected: a message reading `Starter plugin is running. Project layers: N.` where N is the number of layers in the project.
7. Disable the plugin and confirm its menu/toolbar action disappears. Re-enable it and confirm only one action is present.

QGIS startup and the automated smoke check were verified on 15 October 2026. The packaged plugin was subsequently installed in the normal `default` profile: automatic loading, the real toolbar action and its message, and plugin-manager unload/reload were verified through QGIS's APIs in the actual GUI session. These checks did not involve clicking the plugin-manager checkboxes manually.

## 6. Install a packaged plugin for use

For this workstation, close QGIS and run from the repository root:

```powershell
.\scripts\install-plugin.ps1
```

The script checks and builds the ZIP, verifies the extracted files, installs them into `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\ag_tech_tooling`, and enables the plugin. It backs up profile settings and any existing Ag-GIS installation under ignored `dist/install-backups`. It refuses to run while QGIS is open or overwrite an unrelated plugin. Restart QGIS normally after it finishes. To choose another existing profile, pass `-Profile profile_name`.

Alternatively, use QGIS's ZIP installation dialog:

1. Run the checks to build `dist\ag_tech_tooling-0.6.0.zip`.
2. Launch QGIS normally, using the profile in which you want the plugin installed.
3. Open **Plugins → Manage and Install Plugins → Install from ZIP**.
4. Select the generated ZIP and install it, then enable the plugin.
5. Repeat the action and disable/re-enable checks from step 5.

Use the isolated development profile for source development and a separate normal profile for ZIP installation checks. This avoids confusing an installed copy with the source copy.

Version 0.6.0 adds hierarchy management and schema 2 projects to the existing Simple view/top-toolbar foundation. See the work log for installation and verification status.

### Create, open and manage a project — 0.6.0

1. Install the current build using the local installation steps above, then restart QGIS. Use a local writable destination outside the source repository. No additional Python packages are needed; GDAL and PyQGIS come with QGIS.
2. Click **New Project** on the toolbar (also **Plugins → Ag-GIS → New Project…**).
3. No setup form appears. The plugin creates and opens **My Farm Data** under the operating system's **Documents → Ag Tech Tooling → Projects** folder. Subsequent projects use numbered names and preserve existing folders. On this workstation the parent is `C:\Users\Michael\Documents\Ag Tech Tooling\Projects`.
4. Expected result: `Farm.qgz` and `Data/farm.gpkg`, with **Farm Data → Organisation 1 → Client 1 → Farm 1 → Field 1** in Layers. Each field has **Whole Field** and **Seasons**; the starter season is **Season 1**, with **Plans / Operations / Results**. There is no invented crop, year or geometry. Select fields in Layers to reuse the three native reference views.
5. Finish layer edits before switching. Save/discard/cancel any unsaved current map when prompted; cancelling quick creation makes no new workspace. Use **Manage Data** to rename placeholders or add more clients, farms, fields and seasons within the same GeoPackage. For explicit location/names/CRS before creation, use **Plugins → Ag-GIS → New Project with Options…**. Quick creation inherits the map CRS or falls back to EPSG:4326; it does not determine a local survey projection or vertical datum.
6. Later click **Open Project** and select `Data/farm.gpkg`. Expected result: the matching `Farm.qgz` opens after validation. Other GeoPackages cannot yet be imported using this control.
7. Click **Manage Data**. Select the parent, then use the icon-labelled Organisation/Client/Farm/Field/Season/Crop add buttons. Select a named record to **Rename**. Changes save immediately; cancelling an Add/Rename dialog makes no change.
8. Select a field or a branch beneath it and click **Show Field on Map**. Expected result: native Boundaries, Guidance Lines and Infrastructure layers, filtered to that field, with unrelated map layers retained. Whole Field and Seasons remain separate in the management tree. Seasonal datasets and terrain imports are not yet implemented.
9. Save map changes using **Save Map**. Keep both files and their relative structure together when moving the project. The database alone is not the entire current workspace. Imports, exports, conversions, full settings editing and automated backup are not available yet.

For a schema 1 project, **Manage Data** opens **Upgrade Project Copy**. Confirm Organisation/Client names and a new destination outside the original. The plugin snapshots the database, copies supporting files, creates/validates schema 2 and opens the new copy. The original remains unchanged. If upgrading fails, correct the reported problem and retry; a failed staged copy is cleaned up and existing destinations are refused. Resolve any reserved-table name conflict in a separate reviewed copy; the upgrade does not overwrite those tables. This does not package external data dependencies.

If a folder already exists, open it or choose another name. If validation reports missing files, restore the whole farm folder from a known backup. If it reports a newer schema, use a compatible plugin; do not edit the version field to bypass the check. For a failed creation, resolve the reported path/permission problem and retry; no existing farm is replaced. Choose a local working location; NAS backup and shared-editing controls are not implemented.

### Choose Simple view

1. Find **Simple view** at the bottom right of QGIS, beside the existing scale/coordinate controls.
2. Check it to show only the map and Layers in the primary workspace. Browser, welcome/recent-project/news/template views and other main-window panels are hidden. The Ag-GIS top toolbar, QGIS menus and status controls remain available; other QGIS toolbars are hidden.
3. Uncheck it to restore the layout from before Simple view was selected, including panels that were previously hidden.
4. The choice is saved per QGIS profile. It is off until first selected; the current default profile has been switched on for review.
5. Disabling or reloading Ag-GIS restores the full layout while the plugin is absent. Re-enabling it remembers the selected mode.

Simple view changes interface layout only; it does not change project layers, coordinate reference systems, datasets or processing settings. Layers and the Ag-GIS toolbar stay visible while Simple view is on. Other dock panels and toolbars are hidden even if QGIS restores or you try to reopen them; new panels/toolbars are detected and hidden. Switch Simple view off to use Browser or advanced tools.

### Use the top toolbar — 0.6.0

1. After installing/restarting, find **Ag-GIS** at the top of QGIS.
2. Use **New Project**, **Open Project** and **Manage Data** for the controls described above. Input lines, hierarchy/grouping rows and plugin buttons have icons; toolbar icons are 28 pixels with text labels.
3. Use **Save Map** to invoke QGIS's native project save, **Move Map** to pan, **Zoom In / Zoom Out** for interactive zoom and **Whole Map** for full extent. The latter follows QGIS's layer extent and availability rules.
4. Expect clear labels beneath theme icons, with enabled/checked states inherited from QGIS. No GIS computations are duplicated by the toolbar.
5. In full view, recover a hidden toolbar using **View → Toolbars → Ag-GIS**. Simple view keeps it visible. Disable/re-enable the plugin to recover its registration if necessary; unloading removes only the plugin's widgets/actions and preserves borrowed native QGIS actions.

Switching off restores the previous central view only if the project has not changed. If you opened or changed a map while using Simple view, the map stays in front rather than returning to an old welcome screen.

## 7. Add the project to the desktop app

Creating a Git repository on disk does not register it in the desktop app's Projects sidebar.

1. Use the app's **Add new project** control and create a local project named **Ag-GIS**.
2. Attach `C:\Users\Michael\Documents\Projects\repos\ag-tech-tooling` as its primary folder. If needed, use the project's **Edit project → Add folder** controls and **Make primary** for this folder.
3. Move the ongoing tooling chat into that project, or start future tooling chats from it. Keep the installation and tooling documentation in the repository so all project chats can read it.
4. Confirm the project appears in the sidebar and that the attached primary folder is the repository above.

The Ag-GIS sidebar section and related chat titles are renamed. The saved local project is currently labelled Ag Tech QGIS and its own rename/primary-folder selection require the app settings. Current assistant tools can create sidebar sections and move chats into existing Projects, but cannot create a saved local Project; attaching the repository requires the app control.

Official guidance: https://learn.chatgpt.com/docs/projects

### What the plugin package includes

Version 0.6.0 includes Simple view, New/Open Project, Manage Data, all supporting Python modules, semantic SVG icons, metadata, license and `USER_GUIDE.txt`. Install the ZIP through QGIS; no repository checkout, standalone Python, pip packages or companion application is required for end users. QGIS supplies PyQGIS, Qt and its geospatial providers. Use QGIS 3.44.14 LTR for the currently verified environment. Detailed import/export and conversion controls remain under development.

The local installer and the QGIS **Install from ZIP** workflow both install the bundled guide beside the plugin modules. The source checks now also execute farm/lifecycle tests from the extracted release ZIP.

### Farm browser presentation — 0.8.0

1. Close QGIS after saving your map, then run `scripts/install-plugin.ps1` or install the current ZIP through QGIS's plugin manager and restart.
2. Open `Farm.qgz`. Expected result: the left-hand panel reads **Farm Data**, with matching Organisation/Client/Farm/Field/Season/Crop icons, larger rows and less indentation. Whole Field and Seasons remain separate.
3. Native checkboxes, map symbols and field selection work as before. Use Manage Data for persistent record renames. Unload/reload restores and reapplies the presentation without replacing the native layer-tree model.
4. If icons are missing after an update, restart QGIS and verify the installed ZIP includes `farm_browser.py`, `ui_icons.py` and all `agtech_*.svg` assets. Reinstall the complete ZIP if files are missing; no extra dependency is required.

## Known setup problems

- **`winget` is not recognised:** install or update Microsoft's App Installer, then reopen the shell, or use the official Git/QGIS installers. On the tested workstation the App Installer package executable was available even though the command alias was missing.
- **QGIS root not found:** use `-QgisRoot` and check the launcher/Python-wrapper files. The old 3.36 folders on this workstation contained remnants, not a working runtime.
- **`No module named qgis`:** run `scripts\check.ps1`, which uses QGIS's Python wrapper. Do not try to solve this by installing a package named `qgis` from pip.
- **PowerShell script execution is blocked:** retain the error and follow the machine's approved PowerShell policy. Do not disable security policy as a setup shortcut.
- **Plugin is missing from the manager:** launch using this repository's script and check the isolated profile. Review QGIS's Python error log if it still fails.
- **Changes are not appearing:** restart QGIS after changing Python source. Check that you are running the development profile rather than an installed ZIP copy.

## Data In component — 0.8.0 (15 October 2026)

The plugin package now also includes `deere_preview.py`, a read-only GS3 RCD
inspection service, local source scanner and **Data In** dialog. No additional
dependency is needed: native QGIS providers open map layers and ZIP members.
See [Data In](IMPORTS.md) for source selection, limits and recovery steps.
Managed GeoPackage copying and proprietary guidance decoding remain pending.

1. Build/check with `scripts/check.ps1`; expect `dist/ag_tech_tooling-0.8.0.zip`.
2. Save your work and close QGIS before running `scripts/install-plugin.ps1`, or
   install that ZIP through the native plugin manager and restart QGIS.
3. Find **Data In** on the top toolbar and in Plugins → Ag-GIS. Choose
   a file/folder, review results and use Import to Field in an Ag Tech workspace.
   Boundaries locate unambiguous datasets; otherwise choose or create the full
   Organisation/Client/Farm/Field path. A missing CRS requires an explicit choice.
4. Keep original source files/ZIPs in place, then save the map to retain links.
   This version does not move source data into the farm GeoPackage.

### Planned data-type assistance

The proposed type suggestions and raster/vector-specific import controls are
specified in DATA_TYPES.md. They introduce no new installation steps or dependencies
at this stage; current installed Data In behaviour remains as described above.

## Ag-GIS offline Windows installer and updates — 0.8.1

The product is now **Ag-GIS**. The internal plugin folder/ID `ag_tech_tooling`, source checkout `C:\Users\Michael\Documents\Projects\repos\ag-tech-tooling`, and existing Documents/Ag Tech Tooling data location remain stable for upgrades and saved work. The saved Codex project name is managed in the app; repository work does not rename that registration.

1. Prerequisite: Windows 64-bit. Obtain the complete `Ag-GIS-0.8.1-Windows-<timestamp>.zip` from the private `JamRov/Ag-GIS` GitHub release or your administrator. Repository access and GitHub sign-in are required for private downloads.
2. Extract **all** files to a local folder. Save your work and close QGIS. Run `Setup.exe` as your normal Windows user. Keep every payload beside it. This launcher is unsigned.
3. Setup verifies SHA-256 payload hashes. If the tested QGIS 3.44.14 LTR installation is absent, complete the bundled official QGIS MSI wizard and its administrator prompt. QGIS supplies Python, Qt, GDAL and providers; optional projection grids are not included. Cancellation stops setup; if a restart is requested, restart and rerun Setup.
4. Setup installs/enables Ag-GIS in the current Windows user's `default` QGIS profile, creating it if necessary. An existing plugin and profile INI are retained under `%APPDATA%\QGIS\QGIS3\profiles\default\ag-tech-install-backups\<timestamp>`. Open QGIS normally and find **Ag-GIS** on the top toolbar.
5. To choose a profile, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -Profile profile_name` from the extracted folder. Do not run the whole setup as a different administrator account; it would target that account's profile.
6. To verify payloads without installing, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1 -VerifyOnly`. If verification fails, extract a fresh copy. Hashes detect corruption; obtain the installer from your trusted administrator/release account.
7. To update, save the map and use **Plugins → Ag-GIS → Check for Updates… → Open latest release**. Download the plugin ZIP in your signed-in browser, then return to **Install downloaded ZIP…** and select it in QGIS's native ZIP installation dialog. Restart QGIS. Cancel leaves the current installation intact. A 404 may mean no published release or insufficient private-repository access; it is not proof you are up to date.
8. Recovery: close QGIS, move aside a failed `python\plugins\ag_tech_tooling`, restore the backed-up plugin folder and (if needed) `QGIS3.ini`, then reopen QGIS. To remove only the plugin, use QGIS's native plugin manager; keep farm workspaces separately.

The bundle includes plugin source, licenses, user guide, source file hashes, and official MSI provenance. `dist/windows/LATEST.txt` identifies the most recent built installer. Local automated verification does not substitute for clean-Windows-machine wizard/UAC and browser/private-access testing. Publication status is recorded in WORK_LOG.md.


## Published Ag-GIS 0.8.1 — 15 October 2026

Private release: https://github.com/JamRov/Ag-GIS/releases/tag/v0.8.1 . Download Ag-GIS-0.8.1-Windows-20261015T003810Z.zip (583,391,412 bytes), extract ALL files, save/close QGIS, then run Setup.exe as the normal user. SHA-256: `0d74f1f65960ba441aed03790952e0eb313baba6443ec981c38acb663cfa5157`.

The in-plugin Check for Updates runner opens the private releases/latest URL in the user's signed-in browser, then delegates ZIP installation to QGIS. Private repository access is required. Existing farm paths and the internal ag_tech_tooling ID remain stable after the Ag-GIS rename.

Source and extracted-package PyQGIS tests passed on the recorded source. Windows assembly run https://github.com/JamRov/Ag-GIS/actions/runs/38661044397 verified the identical source/plugin package, official QGIS MSI signature/checksum and offline bundle before uploading. Release tag v0.8.1 points to tested source commit 3f1f4ed000b5b5af9d01f308f7238f74494fd83d. Packaging reused those exact-input plugin tests; QGIS was not installed on the hosted runner.

Downloaded the published plugin and full installer through the current authorized browser account: plugin bytes, installer SHA-256/CRC, all payload hashes, VerifyOnly and the compiled launcher's open-QGIS refusal passed. Clean-machine Windows MSI wizard/UAC/reboot and another authorized user's install/update remain pending. The launcher is unsigned.

Local published archive: `dist/windows/Ag-GIS-0.8.1-Windows-20261015T003810Z.zip`; extracted launcher: `dist/windows/published-0.8.1/Ag-GIS-0.8.1-Windows/Setup.exe`. Fifteen obsolete generated files were removed (about 1.75 GB); source snapshots, recovery backups and farm data were retained. Exact cleanup paths/hashes and published-download evidence are in local ignored dist/windows/cleanup.json and published-verification.json. Newer in-progress feature edits remain in the shared local checkout and are excluded from this tested release.
