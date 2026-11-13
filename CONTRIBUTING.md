# Contributing to Ag-GIS

Ag-GIS welcomes farming workflow ideas, reproducible bug reports, documentation and code contributions. Public feedback is maintained in [Ag-GIS Feedback](https://github.com/JamRov/Ag-GIS-Feedback/issues). Do not include original farm/customer datasets, credentials or private screenshots in reports or pull requests.

Start with [Start Here](START_HERE.md) for farmer-first agent prompts: describe the problem, let your agent prepare a draft, then review before sharing. No mandatory login for local use.

## Propose a change

1. Search the feedback tracker for an existing report. Explain the farming task, what happens today and the outcome that would help. Use a synthetic example and identify the affected version.
2. Discuss substantial changes before investing in them. Maintainers assess user control, usability, data integrity, compatibility, maintenance and service cost. Feedback and votes inform priorities but do not guarantee acceptance or delivery dates.
3. Fork the repository, create a focused branch and read AGENTS.md and the relevant docs before editing. Keep generated packages, user settings and GIS datasets outside commits. Never include credentials.
4. Reuse native QGIS APIs and qgis.PyQt. Preserve original user data, useful local operation and portable export. Keep initGui/unload paired and preserve the internal ag_tech_tooling plugin ID for compatibility.
5. Update canonical installation/tooling/user instructions for changed behaviour. Run scripts/check.ps1 with the installed QGIS Python environment for source and extracted-package verification; ordinary Python cannot validate PyQGIS workflows. Record exact checks and any limitations.
6. Open a pull request describing the problem, result and evidence. Link the feedback issue with Related issue; avoid auto-closing a user problem before its acceptance is verified. Code changes require maintainer review; a pull request does not grant direct repository write access.

## Licensing and credit

Ag-GIS code is GPL-2.0-or-later. Submit code you have the right to share under the project's licence, retain relevant copyright/licence notices and identify third-party material and its licence. Contributors retain their copyright; no exclusive assignment is requested by this guide. Maintainers may request changes or decline work and should explain the reason respectfully.

## Current release and development state

Use a release's exact source/tag when reproducing its behaviour. The latest published installer and the active development checkout can differ. A feature mentioned in a roadmap is not necessarily implemented, tested or available for purchase. Read release notes and WORK_LOG.md for verification limits.

Optional cloud backup, mobile access, synchronisation and hosted workspaces are future candidates, not currently supplied paid services. Local data ownership/control and honest communication govern these plans. See docs/USER_COMMITMENTS.md when present in the source version you are using.
