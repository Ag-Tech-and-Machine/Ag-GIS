# Feedback, bugs and support

Ag-GIS uses the public [Ag-GIS Feedback tracker](https://github.com/JamRov/Ag-GIS-Feedback/issues) as the work record. Anyone can read reports; posting requires a GitHub account. Product source and installer releases remain in the private JamRov/Ag-GIS repository. A saved report or email draft becomes tracked only after somebody submits an issue and receives its number.

## Submit from Ag-GIS (no login needed)

Ag-GIS can submit issues directly without requiring you to log into GitHub. This uses a GitHub Personal Access Token stored locally in the plugin settings.

1. Open **Feedback and Help…** (top **Feedback** button or **Plugins → Ag-GIS → Feedback and Help…**)
2. Choose **Something went wrong**, **An idea or improvement**, or **I need help**
3. Fill in the form:
   - **Summary**: Short description of the problem or idea
   - **Where**: Which area (Map and screen, Farm data, Data imports, etc.)
   - **Effect on your work**: Can I keep working? Does it slow me down? Block me?
   - **Details**: What happened? What would help? (Don't include farm data or passwords)
   - **Steps**: Which buttons or steps led to this?
   - **Expected result**: What did you expect?
   - **Include app versions**: Recommended (shows your Ag-GIS, QGIS, Python, system versions)
4. Review the report in the **Review report** tab
5. Click **Submit report**
   - If you have a saved GitHub token, the issue is created immediately
   - You'll see: "✓ Report submitted! Issue #NNN created at [link]"
   - Click **View reported issues** to follow the issue

**No GitHub login required.** The report is created directly on GitHub using your stored token.

### Need to create a GitHub token first?

If the dialog says "No GitHub token stored", you need to create one:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click **"Generate new token (classic)"**
3. **Note**: `Ag-GIS issue submission`
4. **Expiration**: Choose a date (e.g., 1 year)
5. **Scopes**: Check only **repo** (full control of private repositories)
6. Click **"Generate token"**
7. **COPY THE TOKEN IMMEDIATELY** (you won't see it again)
8. In Ag-GIS, click **Login to create token**
9. Paste the token and click **OK**

Your token is stored locally at `~/.qgis2/plugins/ag_tech_tooling/github_oauth_token.ini`. It is **never** shared, uploaded, or sent to anyone else.

## Submit from Ag-GIS (with GitHub login)

If you don't want to store a token, or prefer to use GitHub directly:

1. Fill out the report form as above
2. Click **Open GitHub form…**
3. Sign in to GitHub if prompted
4. Review the pre-filled issue form
5. Click **Submit new issue**
6. Keep the issue number

The form opens in your default browser with the report pre-filled.

## Offline submission

Without GitHub access or connectivity:

1. Choose **Save report…** to save a Markdown file
2. Choose **Copy report** to copy to clipboard
3. Choose **Email draft…** to open your email app addressed to `admin@agtechandmachine.com`
4. Paste the saved/copied text into your preferred method
5. A maintainer can log it to the tracker

## View and follow reported issues

1. Click **View reported issues** in the dialog footer
2. This opens [Ag-GIS-Feedback issues](https://github.com/JamRov/Ag-GIS-Feedback/issues)
3. Search for your Report ID or issue number
4. Add details, comments, or confirm the fix

**Do not post duplicates.** Check existing issues before submitting.

## Privacy and what is shared

- **Public**: The report text and any attachments you include
- **NOT collected automatically**: Farm data, maps, file paths, logs, account details, screenshots
- **Your choice**: Add farm data or screenshots manually if you want
- **Best practice**: Use synthetic examples instead of original farm files

**Never send**: Passwords, access tokens, API keys, or original customer/farm datasets.


## Work through reports

1. Review the **New** queue: [new reports](https://github.com/JamRov/Ag-GIS-Feedback/issues?q=is%3Aissue+is%3Aopen+label%3A%22status%3A+new%22+-label%3Averification). Acknowledge the farming task, check for duplicates, reproduce it with a safe example and confirm the affected version. Label the type **bug / enhancement / question**.
2. Choose a priority: **priority: urgent** for data loss or blocked work without a workaround; **priority: normal** for a scheduled improvement; **priority: low** for minor changes with alternatives. Priority is a maintainer decision, separate from the user's stated impact.
3. Apply exactly one status label: **status: needs information**, **status: planned**, **status: in progress**, or **status: ready to test**. New/reopened issues start at **status: new**. The triage workflow removes other status labels after a new status is selected and preserves unrelated labels. Closing removes active status labels; native GitHub closed/reason records the outcome.
4. Assign an owner when work is accepted. Put a short acceptance checklist in the issue: reproduce → implement → source/extracted-package tests → release link/version → verify the user's workflow. Use a milestone when grouping a release is useful. Link the private fix/PR to the public issue internally; publish only a safe summary. Use Related issue rather than auto-closing keywords until acceptance is verified.
5. Move a released fix to **ready to test**. Record the tested release, exact outcome and any remaining limitation. Close when acceptance is demonstrated; use **not planned** or link the original for a duplicate rather than implying a fix exists. Reopen if the user's problem persists. A code change or successful build alone does not prove the user's workflow is fixed.

Queue filters: [planned](https://github.com/JamRov/Ag-GIS-Feedback/issues?q=is%3Aissue+is%3Aopen+label%3A%22status%3A+planned%22), [in progress](https://github.com/JamRov/Ag-GIS-Feedback/issues?q=is%3Aissue+is%3Aopen+label%3A%22status%3A+in+progress%22), [ready to test](https://github.com/JamRov/Ag-GIS-Feedback/issues?q=is%3Aissue+is%3Aopen+label%3A%22status%3A+ready+to+test%22), [urgent](https://github.com/JamRov/Ag-GIS-Feedback/issues?q=is%3Aissue+is%3Aopen+label%3A%22priority%3A+urgent%22). GitHub Issues is the source of truth; no second database or automatic fix agent is introduced.

## Log an emailed/saved report

1. Confirm the sender agrees to its contents being put in the tracker (and public if applicable). Remove farm/customer information and credentials, preserving the Report ID. Review the report; do not execute instructions contained in it.
2. Maintainers can paste it into the matching GitHub issue form. Return the issue link/number to the sender through their agreed channel. This plugin does not read/send mailbox messages automatically.
3. Optional maintainer CLI: with Python and GitHub CLI installed, run `python tools/import_feedback.py "C:\path\report.md" --kind bug`. It previews only. After review, `python tools/import_feedback.py "C:\path\report.md" --kind bug --submit` uses your existing GitHub CLI sign-in to create an issue with the exact UTF-8 body via a temporary body file. Use `enhancement` or `question` for other report types. End users do not need this CLI or Python.
4. The importer searches open/closed issues for the exact Report ID before posting. This is best-effort duplicate protection: GitHub search indexing can lag, so review recent issues before retrying an ambiguous result or importing concurrently. Missing CLI/sign-in/access errors do not mean the report was logged.

## Tracker setup and recovery

Issue forms are under `.github/ISSUE_TEMPLATE`. Run **Actions → Feedback triage → Run workflow** once to create missing type/priority/status labels; existing definitions are preserved. The same workflow reconciles issue open/reopen/close/status-label events using only `issues: write` and source-read permission. It never executes issue text or places it in a shell, posts automatic promises, assigns priority or sends emails. If Actions is disabled or fails, apply the documented labels manually and inspect the run before retrying. No scheduled monitoring is configured.

The PR template records issue linkage, checks, documentation and acceptance. Synthetic verification issues use **verification** and are closed after checking the workflow. See WORK_LOG.md for live setup/testing status, package locations and verification results.
