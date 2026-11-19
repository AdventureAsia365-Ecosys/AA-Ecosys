// Tests for tools/workflows/lane.js (AA-1137 spec lanes). Run: node --test tools/workflows/test_lane.cjs
// The Workflow harness gives the script `args`, `agent`, `phase` and `parallel` and runs it as an async body; this
// test does the same with a scripted agent() that records each prompt and schema and returns canned results.
'use strict'
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const SRC = fs.readFileSync(path.join(__dirname, 'lane.js'), 'utf8').replace(/^export const meta/m, 'const meta')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

async function runLane(args, { implResult, reviewFindings = [] } = {}) {
  const calls = []
  const agent = async (prompt, opts) => {
    calls.push({ prompt, ...opts })
    if (opts.phase === 'Implement') return implResult
    if (opts.phase === 'Review') return { verdict: reviewFindings.length ? 'changes' : 'approve', findings: reviewFindings }
    return { ...implResult }
  }
  const parallel = async fns => Promise.all(fns.map(f => f()))
  const phase = () => {}
  const fn = new AsyncFunction('args', 'agent', 'phase', 'parallel', SRC)
  const out = await fn(args, agent, phase, parallel)
  return { out, calls }
}

const BASE = { key: 'l1-demo', goal: 'AA-900: demo slice', session: 'S285', date: '19/11/2026' }
const PR = { repo: 'AA-Ecosys', worktree: '/w', branch: 'b', pr_title: 't', pr_body: 'Refs AA-900', tests: [], live_steps: [] }
const IMPL = { ready: true, prs: [PR], summary: 's', notes_vi: 'n' }

test('a lane without spec keeps its schema, lenses and prompt', async () => {
  const { calls } = await runLane(BASE, { implResult: IMPL })
  const impl = calls.find(c => c.phase === 'Implement')
  assert.ok(!('trace' in impl.schema.properties))
  assert.ok(!impl.schema.required.includes('trace'))
  assert.ok(!impl.prompt.includes('SPEC (AA-1137)'))
  assert.equal(calls.filter(c => c.phase === 'Review').length, 2)
})

test('a spec lane requires trace, briefs the tasks and adds the spec lens', async () => {
  const trace = [{ task: 'T1', requirements: ['R1.1'], tests: ['tests/unit/test_bell.py'], live_steps: [], status: 'done' }]
  const { calls } = await runLane({ ...BASE, spec: '.kiro/specs/AA-900-demo', tasks: ['T1', 'T2'] },
    { implResult: { ...IMPL, trace } })
  const impl = calls.find(c => c.phase === 'Implement')
  assert.ok(impl.schema.required.includes('trace'))
  assert.deepEqual(impl.schema.properties.trace.items.required, ['task', 'requirements', 'tests', 'live_steps', 'status'])
  assert.match(impl.prompt, /implements ONLY tasks T1, T2 of the spec \.kiro\/specs\/AA-900-demo/)
  assert.match(impl.prompt, /trace_check\.py show \/home\/nghiep\/projects\/AA-Ecosys\/\.kiro\/specs\/AA-900-demo --tasks T1,T2/)
  const reviews = calls.filter(c => c.phase === 'Review')
  assert.equal(reviews.length, 3)
  assert.ok(reviews.some(r => /lens: spec \(tasks T1, T2/.test(r.prompt)))
  assert.ok(reviews.every(r => r.prompt.includes('"task":"T1"')))
})

test('custom lenses get the spec lens once', async () => {
  const lenses = ['ui kit', 'spec: my own wording']
  const { calls } = await runLane({ ...BASE, spec: 's', tasks: ['T1'], lenses }, { implResult: { ...IMPL, trace: [] } })
  assert.equal(calls.filter(c => c.phase === 'Review').length, 2)
  const { calls: c2 } = await runLane({ ...BASE, spec: 's', tasks: ['T1'], lenses: ['ui kit'] },
    { implResult: { ...IMPL, trace: [] } })
  assert.equal(c2.filter(c => c.phase === 'Review').length, 2)
})

test('the fix pass of a spec lane also returns trace', async () => {
  const finding = { severity: 'major', file: 'x', issue: 'y' }
  const { calls } = await runLane({ ...BASE, spec: 's', tasks: ['T1'] },
    { implResult: { ...IMPL, trace: [] }, reviewFindings: [finding] })
  const fix = calls.find(c => c.phase === 'Fix')
  assert.ok(fix.schema.required.includes('trace'))
  assert.match(fix.prompt, /full updated trace\[\]/)
  assert.ok(!fix.schema.required.includes('resumed_state'))
})

test('bad spec args are refused before any agent runs', async () => {
  await assert.rejects(runLane({ ...BASE, tasks: ['T1'] }, { implResult: IMPL }), /tasks needs args\.spec/)
  await assert.rejects(runLane({ ...BASE, spec: 's' }, { implResult: IMPL }), /non-empty list of task ids/)
  await assert.rejects(runLane({ ...BASE, spec: 's', tasks: [] }, { implResult: IMPL }), /non-empty list/)
  await assert.rejects(runLane({ ...BASE, spec: 7, tasks: ['T1'] }, { implResult: IMPL }), /folder path/)
})
