# Hermes Operations for Ag-GIS

## Overview

Hermes manages ongoing execution through Hermes Bot Chat. This document covers the owner's scope, approval gates, local journal, native schedules and learning workflow.

## Scope

- Execute bug-engineer assignments for the private Ag-GIS team
- Handle bounded work: small reproduced bug fixes, tests, one- or two-file refactors, docs and tidy-ups
- Self-assign from BACKLOG.md when team_queue has no READY tasks (per James's continuous-work instruction)
- Keep the latest test build installed and working on the Omen development machine
- Maintain automated checks (GitHub Actions) and run real GUI checks with pywinauto
- Work on the local Qwen model (ag-gis-bugs role)

## Approval Gates

### Owner Approval Required

- Adding features or pursuing new functionality goals
- Roadmap or competitor entries
- Publication, outreach, pricing, spending or release
- Marketing drafts before publication

### Autonomy (No Owner Approval Needed)

- Bounded bug fixes with clear repro
- Tests, small refactors, docs and tidy-ups
- Self-improvement within existing scope
- Preparing marketing drafts (obtain approval before publication)

### Approved Reliability Work

The owner has approved reliability work on:
- Install → create farm → import → save/reopen workflow

## Local Journal

- Evidence directories under `.aggis-agent/evidence/`
- Private team queue at `C:/Users/Michael/AppData/Local/hermes/ag-gis-team/team_queue.json`
- BACKLOG.md at `C:/Users/Michael/AppData/Local/hermes/ag-gis-team/BACKLOG.md`
- Knowledge pages at `C:/Users/Michael/AppData/Local/hermes/ag-gis-team/knowledge/`
- Test install records in `C:/Users/Michael/AppData/Local/hermes/ag-gis-team/TEST-INSTALL.md`

## Native Schedules

### Continuous Work Loop
- Agents should work constantly until out of tasks
- Take next task in priority order (bugs, then features/build, then financial recovery)
- Complete tasks to finish, then move to next
- Self-serve from BACKLOG.md when queue is empty

### Build & Install Schedule
- After every change that passes QA, build and install new test version
- Keep test build installed on Omen at all times
- Record commit/version and date in TEST-INSTALL.md
- Push every task branch to GitHub (verify with `git ls-remote`)

### Weekly Demo
- Every Friday afternoon: post screenshots of weekly demo thread
- Use topic helper `--file <png>` for screenshots
- Plain lines on what changed and what's next

## Learning Workflow

- Hindsight now learns from work automatically every few turns
- Team knowledge pages remain the place for facts
- Before task: read pages it touches
- After task: did I learn/confirm something durable?
  - If yes: add dated line with source to right page or `_inbox.md`
  - GAPs go in `_inbox.md`
- Never: secrets, personal data, whole logs

## Task Handling

### Claiming Tasks
- Use `claim <task-id>` with worker handle and role bug-engineer
- Keep same worker handle for heartbeat, block and finish
- Reconcile existing claims rather than duplicating

### Completion
- Write private evidence JSON with `checks` (each command and exit_code)
- Include `acceptance_met` boolean, observed results, artifacts, limits
- Final result starts with `ACCEPTED <task-id>` to acknowledge assignment
- Update team_queue with status (claim, passed, blocked)

### Blocking
- Use `block <task-id>` with reason and next action
- Block only for real technical failures, safety problems or genuine James decision
- Don't block on missing session/lease/receipt (KEEP-GOING rule)

## Repository Structure

- Main source: `E:/hermes/ag-gis`
- Team folder: `E:/hermes/ag-gis-team`
- Worktrees in `E:/hermes/ag-gis-team/worktrees/`
- Archive: `D:/HermesArchive/` for safety copies

## Public Face Rules

- Never mention financial gain, revenue, pricing strategy, costs publicly
- Only money topics: clear ask for help/donations or plain paid service description
- Base build is open and community-driven
- Write public text for outside contributors

## Push Verification

- After every push: verify with `git ls-remote origin <branch>`
- Only say "pushed" after GitHub confirms
- If push fails with auth error: report "GitHub login missing or expired" once
- Before pushing to public repo: ensure PUBLIC-COMMUNITY and privacy rules
