# Linear surfaces — the derived copies

Maintained in `linro-io/linro-io` at `docs/agents/org-rules/linear-surfaces.md`.
In other repositories this is a generated snapshot: update the metarepo source
and refresh with its `bin/sync-agent-guidance`; do not edit the copy independently.

`docs/agents/org-rules/linear.md` is canonical. This file holds the **exact text** of
the copies that live inside Linear, so a change to the convention is one diff
covering the rule and its copies instead of a rule change plus a promise to
update Linear later.

Linear's API is **read-only** for agent skills and templates (`list_` and
`get_` exist; there is no `save_`), so each of these is pasted once by a human.
When this file changes, re-paste the block that changed.

---

## 1. Linear Agent Skill — "Issue handling"

**Where:** Linear → Settings → Agents → Skills → New skill. Name it
`Issue handling`.

**Why it exists:** it reaches agents on any machine, including ones that never
open the meta repo. Keep it short — it is a pointer with enough substance to be
useful when the repo is not to hand.

```markdown
How work is tracked in this workspace. The full convention lives in
`docs/agents/org-rules/linear.md` in the linro-io/linro-io meta repo; this is the
short version for when that is not to hand.

**There is no "epic".** The hierarchy is Initiative → Project → Project
Milestone → Issue → sub-issue. Do not file a parent issue titled `Epic: …`:
it is never meaningfully done, and it duplicates what a project already holds.

**A workstream is a Project.** Its phases are **Project Milestones**, and every
milestone description states its **gate** — the observable condition that must
hold before the next phase starts. A phase with no gate is a label.

**Sequencing is blocking relations** (`blocks` / `blockedBy`). Parent/sub-issue
means containment, never order — a tree cannot say "this gates everything
downstream". Sub-issues are for decomposing one issue into parts.

**Every issue carries** the problem with evidence (`file:line`, an error
string, a measured number — not a restatement of the title), acceptance
criteria, and a *not in scope* line wherever the boundary is load-bearing.

**Titles say what the change is.** No phase prefixes (`M0 — …`): the phase
lives in the milestone, and a prefix duplicates it and then drifts from it.

**Before filing, look for an existing ticket.** Link or comment on it rather
than filing a near-duplicate. If an old ticket's design is superseded, say so
in a comment on it.

**Cancel, never delete.** Deleting breaks every reference from other issues,
comments and PR bodies. Cancel with a pointer to whatever superseded it.

Branch names come from Linear's `gitBranchName`, so PRs link themselves.
Move to In Review when the PR opens; Done when merged — and, where reaching an
environment is what makes it true, when deployed.
```

---

## 2. Issue template — Engineering

**Where:** Linear → Settings → Teams → Engineering → Templates → New issue
template. Name it `Issue`, and set it as the team default so it appears
without being chosen.

```markdown
## The problem

<!-- Evidence, not a restatement of the title: file:line, the error string,
     the measured number. What is broken or missing, and how you know. -->

## Acceptance

<!-- What is observably true when this is done. -->

## Not in scope

<!-- Delete this heading if the boundary is obvious. Keep it wherever the
     ticket could quietly grow — it is what stops a guard becoming a rewrite. -->
```

---

## 3. Project template — Engineering

**Where:** Linear → Settings → Teams → Engineering → Templates → New project
template. Name it `Workstream`.

Linear project templates carry a description and can pre-create milestones.
Create the description below, plus milestone placeholders `M0 · …` through
`M2 · …` (add or delete phases per workstream — the point is that each one
prompts for its gate).

```markdown
## The problem

<!-- What is wrong today, with evidence. If a measurement settled something,
     put the number here and link the ticket that measured it. -->

## The shape of the fix

<!-- The reframe, if there is one. What changes structurally. -->

## Decisions taken

<!-- Each with who took it, so nobody relitigates it in a month. -->

## Alternatives rejected

<!-- Each with the reason. A rejected option with no reason gets re-proposed. -->

## Milestones

<!-- Each milestone's description carries its GATE: the observable condition
     that must hold before the next phase starts. -->
```

---

## Keeping these in sync

The rule file and this file change in the same PR. After merging, re-paste any
block that changed — there is no API to do it for you, and a copy that has
drifted is worse than no copy, because it is quoted with confidence.
