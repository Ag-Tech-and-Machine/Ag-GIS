# Installation and setup

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

2. On another machine, transfer the repository or clone it once a remote has been created. There is currently no GitHub remote or clone URL.
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
4. Enable **Ag Tech Tooling**.
5. Use its toolbar action or **Plugins → Ag Tech Tooling** menu action.
6. Expected: a message reading `Starter plugin is running. Project layers: N.` where N is the number of layers in the project.
7. Disable the plugin and confirm its menu/toolbar action disappears. Re-enable it and confirm only one action is present.

QGIS startup and the automated smoke check were verified on 15 October 2026. The packaged plugin was subsequently installed in the normal `default` profile: automatic loading, the real toolbar action and its message, and plugin-manager unload/reload were verified through QGIS's APIs in the actual GUI session. These checks did not involve clicking the plugin-manager checkboxes manually.

## 6. Install a packaged plugin for use

For this workstation, close QGIS and run from the repository root:

```powershell
.\scripts\install-plugin.ps1
```

The script checks and builds the ZIP, verifies the extracted files, installs them into `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\ag_tech_tooling`, and enables the plugin. It backs up profile settings and any existing Ag Tech Tooling installation under ignored `dist/install-backups`. It refuses to run while QGIS is open or overwrite an unrelated plugin. Restart QGIS normally after it finishes. To choose another existing profile, pass `-Profile profile_name`.

Alternatively, use QGIS's ZIP installation dialog:

1. Run the checks to build `dist\ag_tech_tooling-0.4.0.zip`.
2. Launch QGIS normally, using the profile in which you want the plugin installed.
3. Open **Plugins → Manage and Install Plugins → Install from ZIP**.
4. Select the generated ZIP and install it, then enable the plugin.
5. Repeat the action and disable/re-enable checks from step 5.

Use the isolated development profile for source development and a separate normal profile for ZIP installation checks. This avoids confusing an installed copy with the source copy.

Version 0.4.0 adds New/Open Farm Project to the existing Simple view foundation. See the work log for installation and verification status.

### Create and open a farm — 0.4.0

1. Install the current build using the local installation steps above, then restart QGIS. Use a local writable destination outside the source repository. No additional Python packages are needed; GDAL and PyQGIS come with QGIS.
2. Choose **Plugins → Ag Tech Tooling → New Farm Project…**.
3. Enter the farm name and choose an existing parent folder using **Browse…**. Confirm the **Farm coordinate system** for your location and intended work; its initial value comes from the current map and may need changing.
4. Click **Create Farm**. Expected result: a new farm folder containing `Farm.qgz` and `Data/farm.gpkg`, with farm identity, schema version and coordinate system recorded. The map starts empty. Existing farm folders are never overwritten.
5. Finish layer edits before switching maps. If prompted about unsaved map changes, choose **Save**, **Discard** or **Cancel**. Cancelling a switch keeps the current map; a newly created farm is retained at the reported location for later opening.
6. Later choose **Plugins → Ag Tech Tooling → Open Farm Project…** and select that farm's `Data/farm.gpkg`. Expected result: the matching `Farm.qgz` opens after validation. Other GeoPackages cannot yet be imported using this control.
7. Save map changes using QGIS's normal **Save** control. Keep both files and their relative structure together when moving the farm. The database alone is not the entire current workspace. Imports, exports, conversion tools, settings editing and automated backup are not available yet.

If a folder already exists, open it or choose another name. If validation reports missing files, restore the whole farm folder from a known backup. If it reports a newer schema, use a compatible plugin; do not edit the version field to bypass the check. For a failed creation, resolve the reported path/permission problem and retry; no existing farm is replaced. Choose a local working location; NAS backup and shared-editing controls are not implemented.

### Choose Simple view

1. Find **Simple view** at the bottom right of QGIS, beside the existing scale/coordinate controls.
2. Check it to show only the map and Layers in the primary workspace. Browser, welcome/recent-project/news/template views and other main-window panels are hidden. The Ag Tech Tooling top toolbar, QGIS menus and status controls remain available; other QGIS toolbars are hidden.
3. Uncheck it to restore the layout from before Simple view was selected, including panels that were previously hidden.
4. The choice is saved per QGIS profile. It is off until first selected; the current default profile has been switched on for review.
5. Disabling or reloading Ag Tech Tooling restores the full layout while the plugin is absent. Re-enabling it remembers the selected mode.

Simple view changes interface layout only; it does not change project layers, coordinate reference systems, datasets or processing settings. Layers and the Ag Tech Tooling toolbar stay visible while Simple view is on. Other dock panels and toolbars are hidden even if QGIS restores or you try to reopen them; new panels/toolbars are detected and hidden. Switch Simple view off to use Browser or advanced tools.

### Use the top toolbar — 0.4.0

1. After installing/restarting, find **Ag Tech Tooling** at the top of QGIS.
2. Use **New Farm** or **Open Farm** for the farm controls described above.
3. Use **Save Map** to invoke QGIS's native project save, **Move Map** to pan, **Zoom In / Zoom Out** for interactive zoom and **Whole Map** for full extent. The latter follows QGIS's layer extent and availability rules.
4. Expect clear labels beneath theme icons, with enabled/checked states inherited from QGIS. No GIS computations are duplicated by the toolbar.
5. In full view, recover a hidden toolbar using **View → Toolbars → Ag Tech Tooling**. Simple view keeps it visible. Disable/re-enable the plugin to recover its registration if necessary; unloading removes only the plugin's widgets/actions and preserves borrowed native QGIS actions.

Switching off restores the previous central view only if the project has not changed. If you opened or changed a map while using Simple view, the map stays in front rather than returning to an old welcome screen.

## 7. Add the project to the desktop app

Creating a Git repository on disk does not register it in the desktop app's Projects sidebar.

1. Use the app's **Add new project** control and create a local project named **Ag Tech Tooling**.
2. Attach `C:\Users\Michael\Documents\Projects\repos\ag-tech-tooling` as its primary folder. If needed, use the project's **Edit project → Add folder** controls and **Make primary** for this folder.
3. Move the ongoing tooling chat into that project, or start future tooling chats from it. Keep the installation and tooling documentation in the repository so all project chats can read it.
4. Confirm the project appears in the sidebar and that the attached primary folder is the repository above.

Sidebar registration is pending. The current assistant tools can list and manage existing projects but do not expose creation of a local folder project, so adding it requires the app control.

Official guidance: https://learn.chatgpt.com/docs/projects

### What the plugin package includes

Version 0.4.0 includes Simple view, New/Open Farm Project, all supporting Python modules, icon, metadata, license and `USER_GUIDE.txt`. Install the ZIP through QGIS; no repository checkout, standalone Python, pip packages or companion application is required for end users. QGIS supplies PyQGIS, Qt and its geospatial providers. Use QGIS 3.44.14 LTR for the currently verified environment. Detailed import/export and conversion controls remain under development.

The local installer and the QGIS **Install from ZIP** workflow both install the bundled guide beside the plugin modules. The source checks now also execute farm/lifecycle tests from the extracted release ZIP.

## Known setup problems

- **`winget` is not recognised:** install or update Microsoft's App Installer, then reopen the shell, or use the official Git/QGIS installers. On the tested workstation the App Installer package executable was available even though the command alias was missing.
- **QGIS root not found:** use `-QgisRoot` and check the launcher/Python-wrapper files. The old 3.36 folders on this workstation contained remnants, not a working runtime.
- **`No module named qgis`:** run `scripts\check.ps1`, which uses QGIS's Python wrapper. Do not try to solve this by installing a package named `qgis` from pip.
- **PowerShell script execution is blocked:** retain the error and follow the machine's approved PowerShell policy. Do not disable security policy as a setup shortcut.
- **Plugin is missing from the manager:** launch using this repository's script and check the isolated profile. Review QGIS's Python error log if it still fails.
- **Changes are not appearing:** restart QGIS after changing Python source. Check that you are running the development profile rather than an installed ZIP copy.
