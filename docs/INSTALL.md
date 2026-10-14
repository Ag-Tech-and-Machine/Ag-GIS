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
   - `QGIS plugin load/action/unload smoke check passed`
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

QGIS startup and the automated smoke check were verified on 15 October 2026. Manual plugin-manager enable/disable and toolbar use are pending verification; record the result in the work log when completed.

## 6. Install a packaged plugin for use

1. Run the checks to build `dist\ag_tech_tooling-0.1.0.zip`.
2. Launch QGIS normally, using the profile in which you want the plugin installed.
3. Open **Plugins → Manage and Install Plugins → Install from ZIP**.
4. Select the generated ZIP and install it, then enable the plugin.
5. Repeat the action and disable/re-enable checks from step 5.

Use the isolated development profile for source development and a separate normal profile for ZIP installation checks. This avoids confusing an installed copy with the source copy.

## 7. Add the project to the desktop app

Creating a Git repository on disk does not register it in the desktop app's Projects sidebar.

1. Use the app's **Add new project** control and create a local project named **Ag Tech Tooling**.
2. Attach `C:\Users\Michael\Documents\Projects\repos\ag-tech-tooling` as its primary folder. If needed, use the project's **Edit project → Add folder** controls and **Make primary** for this folder.
3. Move the ongoing tooling chat into that project, or start future tooling chats from it. Keep the installation and tooling documentation in the repository so all project chats can read it.
4. Confirm the project appears in the sidebar and that the attached primary folder is the repository above.

Sidebar registration is pending. The current assistant tools can list and manage existing projects but do not expose creation of a local folder project, so adding it requires the app control.

Official guidance: https://learn.chatgpt.com/docs/projects

## Known setup problems

- **`winget` is not recognised:** install or update Microsoft's App Installer, then reopen the shell, or use the official Git/QGIS installers. On the tested workstation the App Installer package executable was available even though the command alias was missing.
- **QGIS root not found:** use `-QgisRoot` and check the launcher/Python-wrapper files. The old 3.36 folders on this workstation contained remnants, not a working runtime.
- **`No module named qgis`:** run `scripts\check.ps1`, which uses QGIS's Python wrapper. Do not try to solve this by installing a package named `qgis` from pip.
- **PowerShell script execution is blocked:** retain the error and follow the machine's approved PowerShell policy. Do not disable security policy as a setup shortcut.
- **Plugin is missing from the manager:** launch using this repository's script and check the isolated profile. Review QGIS's Python error log if it still fails.
- **Changes are not appearing:** restart QGIS after changing Python source. Check that you are running the development profile rather than an installed ZIP copy.
