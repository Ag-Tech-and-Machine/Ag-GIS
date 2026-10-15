# Ag-GIS

Farmer-friendly tools powered by QGIS to simplify agricultural mapping and data workflows. People should own and control their data, understand what the software does, and be able to help improve it.

This repository and its releases are public under **GPL-2.0-or-later**. Forks and pull requests are welcome; maintainers review proposed changes.

## Downloads and current status

Get installers, plugin ZIPs, exact source and verification evidence from [Releases](https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases). The latest published installer is **v0.8.1**, an experimental Windows distribution using QGIS 3.44.14 LTR. Extract the complete Windows bundle before running Setup.exe. Existing QGIS users can install the plugin ZIP with Plugins → Manage and Install Plugins → Install from ZIP.

Read release notes for limitations, including the unsigned launcher and pending clean-machine acceptance checks. Local development can be ahead of published source and installers; public visibility does not publish every in-progress feature.

Cloud backups, mobile access, team synchronisation and hosted workspaces are future candidates. No paid cloud service has launched.

## Help improve Ag-GIS

Report problems and ideas in [Ag-GIS Feedback](https://github.com/JamRov/Ag-GIS-Feedback/issues), which remains separate so existing report links work. Code and documentation pull requests belong here.

Use synthetic examples. Reports, pull requests and attachments are public: never include private farm/customer datasets or credentials. Discuss substantial changes first, read AGENTS.md, use native QGIS APIs, and include relevant tests and documentation. Submit only material you have the right to share under the project licence; contributors retain their copyright. Community input informs priorities without guaranteeing a feature or delivery date.

## Development

Read [AGENTS.md](AGENTS.md), [installation](docs/INSTALL.md), [tooling](docs/TOOLING.md), [user guide](docs/USER_GUIDE.md) and [work log](docs/WORK_LOG.md). Older documents describe the earlier private setup; the current owner is Ag-Tech-and-Machine and public downloads require no repository membership.

Use QGIS bundled Python/PyQGIS and run scripts/check.ps1 for source and extracted-package checks. Ordinary Python can run tools/check_plugin.py and tools/build_plugin.py for syntax/packaging, but does not replace PyQGIS integration testing. Keep datasets, local profiles and generated packages outside commits.

Ag-GIS retains upstream credits and licences. It is a separate project, not an official QGIS distribution.
