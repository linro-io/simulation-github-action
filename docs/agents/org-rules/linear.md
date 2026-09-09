# Linear

Maintained in `linro-io/linro-io` at `docs/agents/org-rules/linear.md`.
In other repositories this is a generated snapshot: update the metarepo source
and refresh with its `bin/sync-agent-guidance`; do not edit the copy independently.

How work is tracked. **This file is canonical.** Three derived copies exist so
the convention reaches surfaces the repo cannot:

| Copy | Reaches | Source |
|---|---|---|
| Linear Agent Skill "Issue handling" | agents on any machine, including ones that never open this repo | `linear-surfaces.md` |
| Engineering issue + project templates | humans and anything creating work in the Linear UI | `linear-surfaces.md` |
| `.claude/skills/file-workstream/` | the multi-ticket procedure, where the traps are | that skill |

**Change this file first, and update the copies in the same PR.** Three
independent copies of a convention drift — that is exactly how this workspace
ended up with three competing definitions of "epic".

The two Linear-side copies are pasted by hand: Linear's API is read-only for
agent skills and templates (`list_` / `get_`, no `save_`). Their exact text
lives in `linear-surfaces.md` in this directory, so the copy travels in the
same diff as the rule and re-pasting is mechanical.

## There is no "epic"

Linear has no epic object. The hierarchy is **Initiative → Project → Project
Milestone → Issue → sub-issue**. "Epic" is Jira vocabulary; filing one as a
parent issue titled `Epic: …` produces a permanent Backlog issue that is never
meaningfully done, a breadcrumb on every child pointing at a stub, and a second
container duplicating what a project already holds.

## Shape of a workstream

- **Project** — the workstream. Holds the write-up, the artifacts and links, a
  lead, a start and target date. Note that this workspace's projects mix
  long-lived *areas* (API, Frontend, Plugins, Infrastructure, Core Data
  Platform) with real *efforts* (PII Data Scrubbing, Marketplace v1, Estate
  Enrollment). A new workstream is an effort; do not file one under an area.
- **Project Milestones** — the phases. **Every milestone description carries
  its gate**: the observable condition that must hold before the next phase
  starts. A phase with no gate is a label, not a milestone.
- **Blocking relations** (`blocks` / `blockedBy`) — sequencing. This is the
  only thing that expresses order.
- **Sub-issues** — genuine decomposition of one issue into parts. Never an epic
  stand-in.

**Parent/sub-issue means containment, never order.** A tree cannot say "M1
gates everything downstream"; a blocking relation can, and it shows on both
issues.

## Anatomy of an issue

Every issue carries:

- **The problem**, with evidence — `file:line`, an error string, a measured
  number. Not a restatement of the title.
- **Acceptance criteria** — what is observably true when it is done.
- **Not in scope**, wherever the boundary is load-bearing. This is what stops a
  guard ticket quietly becoming a rewrite.

Titles say what the change is. **No phase prefixes** (`M0 — …`): the phase lives
in the milestone, and a title prefix duplicates it and then drifts from it.

## Lifecycle

- **Before filing, look for an existing ticket.** Link or comment on it rather
  than filing a near-duplicate; if an old ticket's design is superseded, say so
  in a comment on that ticket.
- Branch names come from Linear's `gitBranchName` (`istvandocsa/eng-627-…`), so
  the PR links itself to the issue. Do not invent your own.
- **In Review** when the PR opens. **Done** when it is merged — and, for
  anything that has to reach an environment to be true, when it is deployed.
- **Cancel, never delete.** A deleted issue breaks every reference to it from
  other issues, comments and PR bodies. Cancel it with a pointer to whatever
  superseded it.

## Traps, learned the hard way

- A parent issue looks like an epic and encodes nothing. If you catch yourself
  explaining the sequencing in prose, you wanted blocking relations.
- Structure encoded in a title (a phase prefix, a numbered option) becomes a
  second source of truth the moment the real field exists.
- A convention nobody can see at the point of creation decays. That is what the
  issue template is for; keep it in sync with this file.
