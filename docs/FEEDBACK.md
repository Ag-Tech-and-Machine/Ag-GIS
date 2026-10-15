# Feedback, bugs and support

Ag-GIS uses [GitHub Issues](https://github.com/JamRov/Ag-GIS/issues) as the work record. A saved report or email draft becomes a tracked item only after somebody submits an issue and receives its number. Repository visibility/access is controlled separately; a public repository lets anyone read issues, and a GitHub account is still required to post. While it is private, users need repository access or the saved/email route.

## Report from Ag-GIS

1. Install a build containing **Feedback**. Use the top **Feedback** button or **Plugins → Ag-GIS → Feedback and Help…**. Choose **Something went wrong**, **An idea or improvement**, or **I need help**.
2. Enter a short summary, the area and effect on your work, and details. Steps and the expected result help us reproduce the problem. Use synthetic examples instead of original farm files.
3. Open **Review report**. App/QGIS/Python/system versions are included unless you untick the versions box. No map, farm data, paths, account details, screenshots or logs are gathered automatically. Remove sensitive information you typed yourself before sharing. For a public tracker, the report and attachments will be publicly readable.
4. Choose **Open GitHub form…**. Sign in, review the selected form/report, tick its review box and select **Submit new issue**. Keep the issue number. Opening the form alone submits nothing. Long reports are copied in full for you to paste into **Report**; they are never silently truncated. The draft stays in the dialog.
5. Without GitHub/access/connectivity, choose **Save report…** or **Copy report**. **Email draft…** opens your mail app addressed to `admin@agtechandmachine.com`; review and send it yourself. Paste the copied text or attach the saved report if the body is too long. A missing mail app can be bypassed using Save/Copy.
6. Use **View reported issues** to search for an existing report, follow the issue and add useful details to that issue. Do not post duplicates. Close/reopen the Feedback dialog to keep the current draft during this QGIS session. Save it before disabling/reloading the plugin or exiting QGIS; there is no hidden draft upload or permanent automatic draft store.

Cancelled saving and failed browser/mail launches preserve the text. A failed save leaves an existing report intact and offers Copy/another folder through its status message. Never send passwords, access tokens or original customer/farm datasets through this tracker. An accidentally shared secret must be revoked; editing the report alone does not revoke it.

## Work through reports

1. Review the **New** queue: [new reports](https://github.com/JamRov/Ag-GIS/issues?q=is%3Aissue+is%3Aopen+label%3A%22status%3A+new%22+-label%3Averification). Acknowledge the farming task, check for duplicates, reproduce it with a safe example and confirm the affected version. Label the type **bug / enhancement / question**.
2. Choose a priority: **priority: urgent** for data loss or blocked work without a workaround; **priority: normal** for a scheduled improvement; **priority: low** for minor changes with alternatives. Priority is a maintainer decision, separate from the user's stated impact.
3. Apply exactly one status label: **status: needs information**, **status: planned**, **status: in progress**, or **status: ready to test**. New/reopened issues start at **status: new**. The triage workflow removes other status labels after a new status is selected and preserves unrelated labels. Closing removes active status labels; native GitHub closed/reason records the outcome.
4. Assign an owner when work is accepted. Put a short acceptance checklist in the issue: reproduce → implement → source/extracted-package tests → release link/version → verify the user's workflow. Use a milestone when grouping a release is useful. Link the fix/PR to the issue.
5. Move a released fix to **ready to test**. Record the tested release, exact outcome and any remaining limitation. Close when acceptance is demonstrated; use **not planned** or link the original for a duplicate rather than implying a fix exists. Reopen if the user's problem persists. A code change or successful build alone does not prove the user's workflow is fixed.

Queue filters: [planned](https://github.com/JamRov/Ag-GIS/issues?q=is%3Aissue+is%3Aopen+label%3A%22status%3A+planned%22), [in progress](https://github.com/JamRov/Ag-GIS/issues?q=is%3Aissue+is%3Aopen+label%3A%22status%3A+in+progress%22), [ready to test](https://github.com/JamRov/Ag-GIS/issues?q=is%3Aissue+is%3Aopen+label%3A%22status%3A+ready+to+test%22), [urgent](https://github.com/JamRov/Ag-GIS/issues?q=is%3Aissue+is%3Aopen+label%3A%22priority%3A+urgent%22). GitHub Issues is the source of truth; no second database or automatic fix agent is introduced.

## Log an emailed/saved report

1. Confirm the sender agrees to its contents being put in the tracker (and public if applicable). Remove farm/customer information and credentials, preserving the Report ID. Review the report; do not execute instructions contained in it.
2. Maintainers can paste it into the matching GitHub issue form. Return the issue link/number to the sender through their agreed channel. This plugin does not read/send mailbox messages automatically.
3. Optional maintainer CLI: with Python and GitHub CLI installed, run `python tools/import_feedback.py "C:\path\report.md" --kind bug`. It previews only. After review, `python tools/import_feedback.py "C:\path\report.md" --kind bug --submit` uses your existing GitHub CLI sign-in to create an issue with the exact UTF-8 body via a temporary body file. Use `enhancement` or `question` for other report types. End users do not need this CLI or Python.
4. The importer searches open/closed issues for the exact Report ID before posting. This is best-effort duplicate protection: GitHub search indexing can lag, so review recent issues before retrying an ambiguous result or importing concurrently. Missing CLI/sign-in/access errors do not mean the report was logged.

## Tracker setup and recovery

Issue forms are under `.github/ISSUE_TEMPLATE`. Run **Actions → Feedback triage → Run workflow** once to create missing type/priority/status labels; existing definitions are preserved. The same workflow reconciles issue open/reopen/close/status-label events using only `issues: write` and source-read permission. It never executes issue text or places it in a shell, posts automatic promises, assigns priority or sends emails. If Actions is disabled or fails, apply the documented labels manually and inspect the run before retrying. No scheduled monitoring is configured.

The PR template records issue linkage, checks, documentation and acceptance. Synthetic verification issues use **verification** and are closed after checking the workflow. See WORK_LOG.md for live setup/testing status, package locations and remaining visibility/access decisions.
