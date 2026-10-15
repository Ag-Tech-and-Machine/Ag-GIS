// SPDX-License-Identifier: GPL-2.0-or-later
// Native issue state is authoritative for closure; labels describe open work.
const statuses = ['status: new', 'status: needs information', 'status: planned',
  'status: in progress', 'status: ready to test'];
const labels = [
  ['feedback', '5319e7', 'User report, suggestion or request for help'],
  ['bug', 'd73a4a', 'Something is not working'],
  ['enhancement', 'a2eeef', 'An improvement or new idea'],
  ['question', 'd876e3', 'Help or clarification needed'],
  ['priority: urgent', 'b60205', 'Data loss or work blocked without a workaround'],
  ['priority: normal', 'fbca04', 'Useful fix or improvement to schedule'],
  ['priority: low', 'c5def5', 'Minor improvement with a workable alternative'],
  ['verification', 'ededed', 'Synthetic tooling check, not a real user problem'],
  ...statuses.map(name => [name, '1d76db', 'Current step for an open issue'])
];

async function manage({github, context, core}) {
  const repo = context.repo;
  // Only the explicit setup run creates missing labels; existing definitions are preserved.
  if (context.eventName === 'workflow_dispatch') {
    for (const [name, color, description] of labels) {
      try {
        await github.rest.issues.getLabel({...repo, name});
      } catch (error) {
        if (error.status !== 404) throw error;
        await github.rest.issues.createLabel({...repo, name, color, description});
      }
    }
    core.info('Feedback labels are ready.');
    return;
  }
  const issue = context.payload.issue;
  if (!issue || issue.pull_request) return;
  const issue_number = issue.number;
  // Read fresh state after waiting in the per-issue queue.
  const current = (await github.rest.issues.get({...repo, issue_number})).data;
  const present = current.labels.map(label => typeof label === 'string' ? label : label.name);
  const action = context.payload.action;
  let desired;
  if (current.state === 'closed') desired = null;
  else if (action === 'opened' || action === 'reopened') desired = 'status: new';
  else if (action === 'labeled' && statuses.includes(context.payload.label?.name)) {
    if (!present.includes(context.payload.label.name)) return; // superseded user action
    desired = context.payload.label.name;
  } else return;
  for (const name of present.filter(name => statuses.includes(name) && name !== desired)) {
    try { await github.rest.issues.removeLabel({...repo, issue_number, name}); }
    catch (error) { if (error.status !== 404) throw error; }
  }
  if (desired && !present.includes(desired)) {
    await github.rest.issues.addLabels({...repo, issue_number, labels:[desired]});
  }
  core.info('Issue status labels reconciled; unrelated labels preserved.');
}
module.exports = {manage, statuses, labels};
