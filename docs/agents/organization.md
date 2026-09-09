# Linro

Maintained in `linro-io/linro-io` at `docs/agents/organization.md`.
In other repositories this is a generated snapshot: update the metarepo source
and refresh with its `bin/sync-agent-guidance`; do not edit the copy independently.

Cloud inventory and security enforcement platform -- discovers cloud resources, stores them in a columnar data pipeline, and evaluates security checks against the inventory.

In the metarepo, each repository sub-directory is an independently cloned Git repository. Before working in another repository, read its `AGENTS.md` (or `CLAUDE.md` during rollout). Repository names and cross-repo paths below are relative to the metarepo checkout, not this document or a standalone child clone. In a standalone clone or isolated worktree, locate the owning repository explicitly; never assume `../` contains it.

## Cross-Repo Data Flow

Protobuf definitions in `idl/` are the source of truth. Generation targets in `idl/` produce `.proto` files in `api/` (public) and `api-internal/` (internal), Go bindings in `api-go/` / `api-internal-go/`, and TypeScript types in `api-ts/` / `api-internal-ts/`. Generated repos are auto-built from `idl/` commits — never edit them by hand.

```
idl/ (protos)  ──make gen──▶  api/, api-internal/    (generated .proto)
                              api-go/, api-internal-go/   ──go module──▶  service/, agent/, plugin-*
                              api-ts/, api-internal-ts/   ──npm──▶        app-frontend/

                              local-dev/ ──tilt──▶ infra + selected products
```

`local-dev/` runs one Tilt session, scoped by two orthogonal choices:

- **run mode** — *where*: `local` (laptop, Docker Desktop) or `coder` (a remote
  workspace on k3d). Detected, then verified against the cluster you are
  actually pointed at.
- **stack** — *what*: `infra` | `linro` | `summoner` | `full`.

`cd local-dev && make dev` is the front door; `make doctor` says what is wrong
before a forty-minute build rather than during one. See `local-dev/AGENTS.md`.

**`cd local-dev && make guide`** opens `local-dev/docs/local-development.html`
— the single human-facing reference for local development on both legs:
addresses, stacks, the Coder bootstrap, code structure, commands. It is
hand-maintained, so any PR that changes a mode, a stack, an address, the
workspace bootstrap or the command surface updates it too.

`linro-coder/` holds the remote half: the GCP estate that runs Coder and the
workspace template developers build from. A workspace is one VM running this
same Tilt stack, tailnet-only, on its own hostname with its own Let's Encrypt
certificate. It provisions **no credentials** — deliberately, since the box
runs agents over arbitrary code. See `linro-coder/AGENTS.md`, and note the one
invariant that bites: a terragrunt unit's state key is its directory
*basename*, so renaming one orphans live state.

### Changing the API

1. Edit `.proto` files in `idl/public/` (or `idl/internal/` for internal-only APIs)
2. Run `make lint` from `idl/` (see `idl/AGENTS.md` for full workflow)
3. Run `make gen` from `idl/` to regenerate downstream repos
4. Commit + push `idl/`. The downstream `api*` and `api-go*`/`api-ts*` repos rebuild automatically; do not commit generated code there manually.
5. Update `app-frontend/` if TS types changed

### Go Module Dependency Chain

```
api-go  (go.linro.dev/api)
    ↓
plugin-sdk → plugin-host → plugin-aws
    ↓                           ↓
service ←──────────────────────┘
    ↓
agent
```

Local development uses a `go.work` workspace to resolve inter-module dependencies. Published modules like `go.linro.dev/api` use tagged versions in `go.mod`; unpublished modules (`plugin-sdk`, `plugin-host`) use `replace` directives.

## Summoner — admin tool for Linro installations

`summoner/` (Go backend) + `summoner-frontend/` (Next.js) compose the
internal admin tool the linro.io team uses to **summon** and **dismiss**
Linro installations on behalf of customers. Each installation gets its
own `linro-<slug>` namespace and `<slug>.linro.localhost` host in the
local Tilt cluster (or `<slug>.instance.linro.dev` on leeroy-dev — not
wired in the PoC).

- Lifecycle is Temporal-driven: `SummonInstallationWorkflow` (helm
  install linro-infra → linro) and `DismissInstallationWorkflow`
  (uninstall linro → linro-infra → delete namespace).
- Permissions are flat: `viewer` < `operator` < `admin`. Login is real
  OIDC (authz-code + PKCE) against Dex — `--auth-provider google` (or
  `mock` for dev); the dummy operator-picker is gone.
- The summoner depends on the CNPG operator + Traefik being
  resident in the cluster — `local-dev` installs both as part of `tilt up`.

Tracking ticket: **ENG-139 — Linro Summoner PoC**. See
`summoner/AGENTS.md` for the architecture overview.

## Adding a new plugin

**Always use `/init-plugin <slug>`.** Plugin repos share a tight set of
conventions (`.marketplace` schema, reusable release workflow in
`linro-io/workflows`, ECR push for the demo service, `dev` GitHub
Environment, the `skip-release` label, the matching infra terraform
entries). Scaffolding by hand drifts — the skill writes every file
from the latest canonical templates and prints the remote-wiring
checklist (GitHub repo, `repos.yaml`, `go.work`, infra terraform PR)
so nothing is forgotten.

See `.claude/skills/init-plugin/SKILL.md` for the full template set
and the remote-wiring steps.

## Regression tests

`regression-test/` holds the Playwright end-to-end suite. Two legs share one
spec dir: a **Tilt** leg (disposable local-dev stack, mock login) and a
preflight-gated **live** leg against the persistent `regression-test.linro.app`
install. Almost all new coverage is the live leg's event-sourcing specs —
create a cloud resource, assert it flows into the Linro inventory / a check /
the UI.

**Always read `regression-test/AGENTS.md` before writing specs**, and use
**`/add-live-regression-spec`** to add one. The live leg has tight conventions
that drift when hand-rolled: a manifest-driven preflight gate, four
definition-driven test-type harnesses (`defineInventoryRoundTrip` /
`defineResourceUpdateLoop` / `defineViolationLoop` / `defineUpdateScenario`), an
IAM permission fence on every GCP resource (`linro-regr-*` name prefix; only
name-embedding resource types are fenceable), a park-on-known-bug pattern
(`fixme` + `LIVE_RUN_FIXME=1` to verify a deployed fix), and a shared-env rule
(read-only or self-cleaning, per-run unique names, janitors). The skill encodes
the harness-choice decision tree, the fence wiring, and the local verification
loop.

## Release baseline

Every ECR-image-publishing service (`service`, `app-frontend`,
`marketplace`, `marketplace-{admin-,}frontend`, `simulator-service`,
`sensor`), every plugin (`plugin-aws`, `plugin-azure`, `plugin-gcp`,
`plugin-hetzner`, `plugin-kubernetes`), and every plugin-tooling
library (`plugin-host`, `plugin-sdk`) share one release-flow
contract:

| Trigger                       | Behaviour                                                      |
|-------------------------------|----------------------------------------------------------------|
| `push` to `main`              | Auto-release. Bump component from the merged PR's `release:bump_*` label, default patch. |
| `push` with `.github`-only diff | Suppressed via `paths-ignore: ['.github/**']`.               |
| PR label `skip-release`       | Suppressed.                                                    |
| PR label `release:bump_minor` | Minor bump on merge.                                           |
| PR label `release:bump_major` | Major bump on merge. Major beats minor when both labels present. |
| `workflow_dispatch`           | Always releases. `version` input: `vX.Y.Z`, `BUMP`, `BUMP_PATCH`, `BUMP_MINOR`, or `BUMP_MAJOR`. |

Services and plugin-tooling libraries delegate to
`linro-io/workflows/.github/workflows/service-release.yml@main`
(generic "create-a-tagged-release"). Plugins delegate to
`plugin-release.yml` in the same hub repo (cross-compile per
platform from `.marketplace`, attach tarballs atomically, Slack
notify). Each caller repo's `cut-release.yml` is a thin wrapper. The
release itself is created with a GitHub App token so
`release: published` fires the caller's `staging-ecr-release.yml` (which
builds + pushes the ECR image) — GITHUB_TOKEN-created releases are
silently filtered by GitHub.

Sensor is the only hybrid: it ships cross-compiled tarballs **and** an
ECR image. It keeps an inline `cut-release.yml` (it can't call
`service-release.yml` because the atomic-release-with-binaries
constraint of Immutable Releases requires its own `release-binaries.yml`)
but follows the same trigger + label contract.

See `linro-io/workflows/README.md` for the workflow contracts.

## UUIDs -- Always UUIDv7

Every UUID generated in this codebase MUST be UUIDv7 unless one of these exceptions applies:

1. **`_linro_id`** -- generated via `linroid/v1.GenerateResource` / `GenerateComponent`. These are deterministic UUIDv8s derived from plugin/service/type/scope/key. Never replace with UUIDv7.
2. The user explicitly requests a different version with a documented reason.

UUIDv7 is time-ordered: natural creation-time ordering, monotonic primary keys, better B-tree locality, easier debugging. Random UUIDs (v4) hurt index performance and lose the temporal signal.

**Go usage:**
- `github.com/gofrs/uuid/v5` -- `uuid.NewV7()` (returns `(UUID, error)`)
- `github.com/google/uuid` v1.6+ -- `uuid.NewV7()` (returns `(UUID, error)`)
- **Never** use `uuid.New()`, `uuid.NewRandom()`, `uuid.Must(uuid.NewRandom())`, `uuid.NewV4()` -- these all produce UUIDv4.

**SQL defaults:** PostgreSQL columns must use `DEFAULT uuidv7()`, never `gen_random_uuid()` or `uuid_generate_v4()`.

**When reviewing new code, treat any non-v7 UUID generation as a bug.**

## CI runners — GitHub-hosted (cloud) is the default

New and migrated workflows run on **GitHub-hosted** runners
(`ubuntu-latest`, or `ubuntu-24.04` / `ubuntu-24.04-arm` for the
per-arch ECR build legs). Go caching uses `actions/setup-go` with
`cache: true` — the action keys the cache by `go.sum`, so no
per-runner path juggling. This is the policy the `init-plugin`
templates encode; follow them as the canonical reference.

Rationale: the self-hosted `linro-ghr-*` fleet ("leeroy") is a single
point of failure — when it went down (2026-07 power outage) every CI
and release job hung `queued`, blocking builds during a demo. Cloud
runners decouple CI from that fleet. The shared reusable workflows in
`linro-io/workflows` (`service-release.yml`, `plugin-release.yml`,
`license-check.yml`) are already `ubuntu-latest`, so every caller's
release path runs on cloud regardless of the caller's own CI runner.

**Do NOT reintroduce the retired self-hosted per-runner Go cache step**
(`GOCACHE`/`GOMODCACHE=/opt/actions-runner/cache/...$RUNNER_NAME`). It
only made sense on the shared-disk `linro-ghr-*` hosts (4 runners per
host racing one GOMODCACHE root) and is dead weight — and unwritable —
on hosted runners.

### Migration status + the exceptions that STAY self-hosted

Migration to cloud is in progress (many repos still carry
`runs-on: self-hosted` and are being converted repo-by-repo). Three
categories legitimately remain self-hosted — do not blind-flip them:

- **`regression-test`** — its Tilt-based jobs need `[self-hosted, big]`;
  they OOM on a standard hosted runner.
- **`chart` `deploy-*.yml` / `demolish.yml` / `rebuild.yml`** — they
  `helm upgrade` against k3s/EKS apiservers reachable only over the
  tailnet (`*.ts.net`). Cloud-migrating these needs a
  `tailscale/github-action` connect step + a Tailscale OAuth/auth-key
  secret first.
- **Anything that touches a PRIVATE repo or the GitHub API** — including
  `actions/checkout`, `actions/download-artifact`, and any `gh` call. The
  org's **IP allow list** refuses hosted runners:

  ```
  Although you appear to have the correct authorization credentials, the
  `linro-io` organization has an IP allow list enabled, and your IP address
  is not permitted to access this resource.
  ```

  This is the exception most likely to be missed, because the obvious test
  — "does this job need cloud credentials or the tailnet?" — returns *no*
  and is the wrong question. The allow list gates **GitHub itself**, so a
  job holding nothing but `secrets.GITHUB_TOKEN` still cannot read its own
  repo's artifacts from `ubuntu-latest`. It has been missed twice in
  `linro-io/infra` (`terraform.yml`'s checkout, then
  `terraform-pr-comment.yml`, which failed on **every run** from the day it
  was added and never once posted a comment). The public-repo release
  workflows below are fine only because their targets are public.
- Anything else that reaches a tailnet-only host or a runner-local tool.

Before migrating anything to hosted, check it against the allow list
exception first: scan the workflow with
`rg 'checkout|download-artifact|gh ' .github/workflows`. If any of them touches a private repo, it stays self-hosted.

When you DO migrate a Go workflow: `self-hosted`→`ubuntu-latest`,
per-arch ECR legs→`ubuntu-24.04` / `ubuntu-24.04-arm`, drop the
per-runner cache step, set `actions/setup-go` `cache: true`, and watch
the first CI run — hosted module-mode builds surface any incomplete
`go.sum` (missing `/go.mod` hash lines) that a warm self-hosted cache
was masking (`GOWORK=off go mod download all` to repair).

## Linear

Work is tracked in Linear, and **the convention is not obvious from the
workspace** — it has drifted before. Read `docs/agents/org-rules/linear.md` before
filing, restructuring or closing anything.

The short version: Linear has no "epic". A workstream is a **Project**, its
phases are **Project Milestones** (each carrying its gate), and sequencing is
**blocking relations** — never a parent issue, which encodes containment and
nothing else. Every issue carries the problem with `file:line` evidence,
acceptance criteria, and a *not in scope* line where the boundary matters.
Cancel superseded issues, never delete them.

`/file-workstream` scaffolds a multi-ticket workstream to that shape. The rule
file is canonical; the Linear Agent Skill and the Engineering issue/project
templates are copies of it and change in the same PR.

## `.entire/` never reaches a PR or main

Every sub-repo working tree grows an untracked `.entire/` directory: the
Entire session recorder's local metadata. (The `entire/checkpoints/v1` ref it
pushes alongside every `git push` is its own ref and is fine.) The directory
is local tooling state, not project content. **It must never be staged, never
appear in a PR, and never be merged to main.** It has slipped in twice through
a bare `git add -A` (the simulator-service#29 squash, idl#152), each needing a
scrub commit afterwards.

Do NOT add it to any repo's `.gitignore` either — it stays untracked and
visible, not ignored. Hygiene instead:

- Stage by path (`git add <files>`); never `git add -A` / `git add .` in a
  sub-repo.
- Before every commit, `git status --short` must show `.entire/` only as `??`.
- Before opening or merging a PR, `gh pr diff <n> --name-only` must contain
  no `.entire/` path. A PR that carries one is not mergeable until the paths
  are removed from the branch.

The one PR that may name `.entire/` is a **cleanup PR for a repo that already
tracks it**: its whole diff is the removal, adding nothing and changing
nothing. It carries no `.gitignore` entry — after it lands the directory is
untracked and visible again, which is the state being restored. Everything
above is about a PR that adds or changes those paths.

**That cleanup untracks; it never deletes.** The directory holds the local
session recordings, which are worth keeping and are read by tooling — so the
only command is

```bash
git rm -r --cached .entire      # index only; the files stay on disk
```

Never `git rm -r .entire`, `rm -rf .entire`, or a `git clean` that reaches it:
those destroy session history that exists nowhere else. "Remove it from the
repo" always means remove it from the INDEX.

## Tool Usage

- Always use Context7 MCP for library/API documentation
- Always use `rg` (ripgrep) instead of `grep`
- Always use `fd` instead of `find`
- Never use `grep`, `find -exec`, `find -delete`, `xargs`, or shell pipes that execute commands
