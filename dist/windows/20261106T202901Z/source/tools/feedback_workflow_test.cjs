// Test the queued GitHub status transitions against fresh issue state, without network calls.
const assert = require('node:assert/strict');
const {manage, statuses} = require('../.github/scripts/feedback-triage.cjs');
async function transition(action, state, labels, eventLabel) {
  const current = new Set(labels);
  const github = {rest:{issues:{
    get: async()=>({data:{state,labels:[...current].map(name=>({name}))}}),
    removeLabel: async({name})=>current.delete(name),
    addLabels: async({labels})=>labels.forEach(name=>current.add(name))
  }}};
  await manage({github,core:{info:()=>{}},context:{eventName:'issues',repo:{owner:'test',repo:'test'},
    payload:{action,issue:{number:1},label:{name:eventLabel}}}});
  return [...current].sort();
}
(async()=>{
  assert.deepEqual(await transition('opened','open',['bug','area: imports']),['area: imports','bug','status: new']);
  assert.deepEqual(await transition('labeled','open',['bug','status: new','status: in progress'],'status: in progress'),['bug','status: in progress']);
  assert.deepEqual(await transition('closed','closed',['bug','status: in progress','priority: urgent']),['bug','priority: urgent']);
  assert.deepEqual(await transition('reopened','open',['bug']),['bug','status: new']);
  assert.deepEqual(await transition('labeled','open',['bug','status: ready to test'],'priority: urgent'),['bug','status: ready to test']);
  assert.deepEqual(await transition('labeled','open',['bug','status: planned'],'status: in progress'),['bug','status: planned']);
  assert.deepEqual(await transition('labeled','closed',['bug','status: planned'],'status: planned'),['bug']);
  const existing=new Set(['bug']); const created=[];
  const github={rest:{issues:{getLabel:async({name})=>{if(!existing.has(name))throw {status:404};},createLabel:async({name})=>created.push(name)}}};
  await manage({github,core:{info:()=>{}},context:{eventName:'workflow_dispatch',repo:{owner:'test',repo:'test'}}});
  assert(!created.includes('bug') && statuses.every(name=>created.includes(name)));
  console.log('Feedback triage open/plan/close/reopen/stale-event/label-preservation/setup checks passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
