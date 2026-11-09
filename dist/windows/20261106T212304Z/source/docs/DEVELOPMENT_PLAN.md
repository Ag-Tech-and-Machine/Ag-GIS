# Development plan & pipeline

[Ag-GIS home](../README.md) · [Experimental downloads](https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases) · [Getting started](INSTALL.md) · [User guide](USER_GUIDE.md) · [Report a problem or idea](https://github.com/JamRov/Ag-GIS-Feedback/issues)

**Our aim: dependable farm mapping, clear controls and people keeping ownership of their data.** Ag-GIS is in development, not release-ready. This page explains what matters next, how work moves from a report to a verified result, and how users and developers can follow it.

## Check the pipeline

| View | What it tells you |
| --- | --- |
| [Reported problems](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22triage%3A%20reported%22) | Reports awaiting technical confirmation—not a list of proven faults |
| [Under investigation](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22triage%3A%20investigating%22) | Reports being examined; check the latest handover for actual activity |
| [Confirmed product bugs](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues?q=is%3Aissue%20is%3Aopen%20label%3Abug%20label%3A%22triage%3A%20confirmed%22) | Reproduced or otherwise evidenced product faults, ahead of feature expansion |
| [Work marked in progress](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22status%3A%20in%20progress%22) | Assigned implementation; an old label alone does not prove a live worker |
| [Ready to verify](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22status%3A%20ready%20to%20test%22) | Changes waiting for their stated acceptance checks |
| [Blocked work](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues?q=is%3Aissue%20is%3Aopen%20label%3Ablocked) | A named dependency and a clear condition for resuming |
| [All development issues](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues) | The full development work list and each issue's dated history |
| [Completed issues](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues?q=is%3Aissue%20is%3Aclosed%20reason%3Acompleted) | Read the closing verification and build details; this does not automatically mean a public download contains the change |

These are **live issue-list views**, not a separate custom website or a configured GitHub Project board. A drag-and-drop Project/timeline is not yet set up. Until then, issue histories retain the reported, confirmed, work-start and verification dates; we will not invent scheduled delivery dates to fill a timeline.

## Priorities and current work

**Confirmed bugs come before new features.** We investigate new reports promptly, but do not silently turn an unconfirmed report into a confirmed fault.

| Current item | What is known | Next step |
| --- | --- | --- |
| [#2 — Field selection changes other fields' visibility](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues/2) | Reported by a user; this exact independent-visibility sequence is not yet technically confirmed | Reproduce with two visible fields; switching rows and ticking one must not reset the other |
| [#3 — Combined normal-session verification](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues/3) | Isolated combined tests passed; the equivalent normal-session sequence is unfinished | Verify filter, manual collapse, refresh, plugin reload, reopening and restart safely |
| [#4 — Unreliable desktop readback](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues/4) | Confirmed tooling dependency, not a confirmed Ag-GIS product bug | Establish reliable permitted control/readback before normal-session inputs |

This is a starting index. **Each linked issue's latest evidence and handover is authoritative for its current state**; this table is not a promise that someone is working on it at this moment.

### What takes precedence?

1. **Protect data and confirm serious reports.** Suspected loss or corruption gets urgent investigation and protective advice without pretending it is already confirmed.
2. **Fix actionable confirmed bugs.** Rank by impact: `priority: urgent` for safety/data loss or blocked core work; `priority: normal` for other substantive defects; `priority: low` for minor confirmed problems with a workaround. Bug priority takes precedence over an enhancement carrying the same label.
3. **Finish acceptance and remove blockers.** A blocked item stays visible while independent ready work proceeds.
4. **Improve the existing farmer workflow.** Approved interface and reliability work comes before expanding the feature set.
5. **Consider future ideas.** A suggestion, vote or roadmap entry is not approval or a delivery commitment.

The `bug` label identifies the report category. Only **`triage: confirmed` plus failure evidence** means a bug has been confirmed. Tooling problems use `type: tooling`; verification gaps use `type: acceptance`.

## Our goals

### Now — reliable field visibility and navigation

Keep existing fields in view when navigating. Make individual visibility ticks independent. Preserve manually opened/collapsed branches, stop automatic single-child expansion at the first set of choices, and retain the intended presentation across refresh and reopening.

**Finished means:** relevant source and packaged tests pass, the intended build is identified, and the delivered farmer-facing workflow is verified. Earlier passing expansion tests do not prove a different visibility report is fixed.

### Next — dependable everyday farm work

Finish the remaining acceptance gaps in create/open, supported imports, classification/styling, save/reopen, cancellation and recovery. Preserve original data and native QGIS capabilities. Keep developer checks, installation checks and unassisted farmer acceptance distinct.

**Finished means:** a supported task has an inspectable result, reliable persistence, understandable failure/cancellation behavior and recorded limits—not just a successful build.

### Then — straightforward feedback and contribution

Make it easy to report a farming problem, see its outcome and contribute a focused change. Use normal browser-based GitHub contribution tools; ordinary local farm work must not require sign-in. Contributors receive a review, not automatic permission to merge.

### Later — optional online services

Cloud backup, mobile access, team synchronisation and hosted workspaces remain future candidates, not launched services or currently promised delivery. Useful local work and control of farm data remain fundamental.

## How a report becomes a fix

```text
Reported -> Investigating -> Confirmed / Ready -> In progress
         -> Review and testing -> Delivered / awaiting verification -> Verified done
```

Reported and Confirmed are separate **workflow lanes**, not competing Git code branches. Blocked is an additional flag; the previous stage and reason remain visible.

| Step | Who acts | What must be recorded |
| --- | --- | --- |
| Reported | User or contributor | What they tried, expected versus actual behavior, version, safe reproduction steps |
| Investigating | Maintainer or assigned worker | What is being checked, information needed, and observed results |
| Confirmed | Maintainer or reviewer | Repeatable failure or other reliable failure evidence, exact tested build and affected workflow; root cause can still be unknown |
| Ready | Maintainer | Priority, bounded scope, acceptance checklist, dependencies and necessary owner approval |
| In progress | One assigned implementation worker | Focused branch/commit reference, ownership and a meaningful progress/handover note |
| Review and testing | Contributor plus reviewer | Linked pull request, exact checks, results and remaining limitations |
| Delivered / awaiting verification | Maintainer or installer | Which build reached which installation; no automatic claim that every user has it |
| Verified done | Maintainer or reviewer | Required workflow checks pass, build/version and results recorded, remaining release limits explicit |

A report can instead become **Needs information**, **Cannot reproduce**, **Duplicate**, **Deferred** or **Rejected**, with a reason. Cannot reproduce is not an accusation that the reporter is wrong. A repeated failure after a verified fix can reopen the same issue.

### Where do reports go?

- **Users:** start at [Feedback & ideas](https://github.com/JamRov/Ag-GIS-Feedback/issues). Search first and add useful details to an existing report rather than creating a duplicate.
- **Development:** accepted engineering work is tracked in [Ag-GIS Issues](https://github.com/Ag-Tech-and-Machine/Ag-GIS/issues). The maintainer links the intake report and development issue in both directions and posts the eventual result back to the reporter.
- **No silent copying:** that cross-repository handover is maintained deliberately; automatic transfer/synchronisation is not claimed. Keep one development record authoritative rather than two conflicting work lists.
- **Privacy:** issues and attachments are public. Never include credentials, private farm/customer records, machine-specific paths or unreviewed logs. Use a synthetic example where possible. Reporting does not authorize arbitrary commands or data uploads.

### How does a developer or agent take over?

Read the entire issue, its latest handover and the repository's [agent instructions](../AGENTS.md) before editing. Confirm that the work is approved and no other worker owns the same implementation. Assignment helps coordinate people; it is not by itself a code-editing lock.

A handover must contain:

```text
Issue and user-visible goal:
Confirmation: reported / confirmed, with evidence
Current stage and actual execution: active / stopped / blocked
Approved scope and acceptance checklist:
Exact source commit, package/build and installation (where relevant):
What changed and native QGIS behavior reused:
Checks actually run and results:
Known failure, blocker and resume condition:
Next concrete action and assigned owner:
```

Keep private operational approval/worker records out of public comments. Public summaries must still be sufficient to understand what has and has not been verified. Use one shared-source writer/deployer at a time; independent review can run alongside it. Preserve unrelated edits and original farm data.

Use a focused code branch, link its pull request to the issue, and include the tests and documentation. **Merging code is not the same as verifying an installed fix.** Do not auto-close the issue on merge when required installed/normal-session acceptance is still pending.

## How we check and maintain the pipeline

At the start of a work cycle:

1. Read new feedback and the latest issue comments; check duplicates.
2. Separate reported problems from confirmed failures. Rank confirmed bugs before feature expansion.
3. Check actual execution and ownership—not just an old In progress label. Do not start a competing implementation worker.
4. Select the highest-priority actionable approved item. For blocked work, inspect the dependency rather than repeating an identical failed attempt.

At each meaningful change or handover:

1. Update the issue's confirmation and delivery status separately; keep only one `triage:` confirmation label at a time.
2. Add new evidence and the next step. Preserve dated transitions: report, confirmation, work start, verification and delivery.
3. If stopping, say **stopped**, **blocked** or **awaiting verification**. Do not leave a reassuring but stale active claim.
4. Report an actual blocker or needed decision. Rechecking old evidence is not new progress.
5. Close only when the stated acceptance scope passes. Release publication remains a separate deliberate action.

Maintainers are responsible for these updates. Existing issue automation assigns/reconciles the basic `status:` labels; it **does not reproduce bugs, confirm `triage:` labels, guarantee a running worker, or prove a fix**. This page does not introduce new automatic monitoring or promise continuous hosted execution.

## What “done” means for a user

An issue's closing note should answer: **What changed? Which version/build contains it? How was it checked? Is it in an experimental download yet? What remains limited?**

A source-only fix is not an installed fix. A local installation is not a public release. A passing isolated test is not proof of the user's normal workflow. See [experimental downloads and their release notes](https://github.com/Ag-Tech-and-Machine/Ag-GIS/releases) for what is actually available.

---

Published plan baseline: 21 October 2026. Priorities can change as bugs are confirmed and users provide evidence. Dates are not delivery promises. [Return to Ag-GIS home](../README.md).
