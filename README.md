# Linro Simulation — GitHub Action

Run your Terraform plans and Pulumi previews through Linro's real policy engine
**before you apply**, and get the verdict as a check on the pull request.

Any number of sources, in any mix, become **one** simulation with one verdict.

Not a linter. The simulation goes through the same plugin normalization and the
same checks Linro runs against your live inventory, so the result reflects supported checks over the proposed inventory. It does not guarantee a passing apply or complete provider/check coverage.

```yaml
name: Linro
on: pull_request

permissions:
  contents: read
  id-token: write        # required — see Permissions below

jobs:
  simulate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_wrapper: false

      - run: |
          terraform init
          terraform plan -out=tfplan
          terraform show -json tfplan > plan.json

      - uses: linro-io/simulation-github-action@v1
        with:
          plan: plan.json
          server: ${{ vars.LINRO_SERVER }}      # https://acme.linro.app
          token: ${{ secrets.LINRO_TOKEN }}
```

## Permissions

`id-token: write` is **required**, and it is the setting people miss.

The action mints a short-lived GitHub OIDC token so your Linro install can
create the check run without holding any credential of its own. Without that
permission, GitHub injects no ID-token endpoint at all and the run fails with a
message about a missing token — which reads like a Linro problem, but is this
one line.

`contents: read` is enough for everything else.

## The verdict arrives as a check run, not as a failed step

On a pull request the action **returns as soon as the simulation is accepted**,
and the result appears moments later as a separate check run named after your
`label`. The action's own step stays green either way.

That surprises people, so it is worth being explicit: **a red simulation does
not fail this step.** Require the check run in your branch protection rules —
that is the gate. If you would rather block the job itself, set
`integration: cli`, which polls and prints the result without the check-run UI. A completed run can still exit zero with violations, so an explicit result-aware gate is required.

## Inputs

Everything is optional except a source (`plan` and/or `preview`) and — for a
real submission — `server` and `token`.

Every flag `linro-simulator simulate` accepts is a first-class input. `extra-args`
is for flags newer than your pinned action, not the normal way to reach anything
below.

**What to simulate.** `plan` and `preview` are repeatable and they combine.

| Input | Default | What it does |
|---|---|---|
| `plan` | | Path to a `terraform show -json` document. **One path per line** to pass several. |
| `preview` | | Path to a `pulumi preview --json` document. Same. |
| `opentofu` | `false` | Record every `plan` source as OpenTofu rather than Terraform. Same format; changes only what the simulation is reported under. |
| `native` | `false` | Force the aws-native (CloudFormation) dialect for every `preview`. |

**Where to send it.**

| Input | Default | What it does |
|---|---|---|
| `server` | | Your install, e.g. `https://acme.linro.app`. |
| `token` | | Linro PAT with `SCOPE_SIMULATIONS`. Always from a secret. |
| `ca-cert` | | PEM bundle for an install behind an internal CA. |
| `insecure` | `false` | Plaintext transport. The CLI allows this only for a **loopback** server — useful on a self-hosted runner beside an install, useless on a hosted one. |

**Scope.** How the resources are identified against your inventory.

| Input | Default | What it does |
|---|---|---|
| `account` | | AWS account the resources deploy to. |
| `region` | | AWS region. |
| `project` | | GCP project, for a GCP resource whose plan states none. A fallback, not an override: one that contradicts the project a provider states refuses the run. See [GCP](#gcp). |
| `organization` | | GCP organization (`123` or `organizations/123`), for an organization-level resource whose parent is a folder, a project, or unknown until apply. A fallback, not an override: one that contradicts the organization a resource states refuses the run. See [GCP](#gcp). |
| `domain` | | T Cloud Public domain: the 32-hex id or the account name. Must match your connector's spelling exactly — see below. |
| `stack-export` | | `pulumi stack export` document, to recover the account/region a preview cannot carry. A scope hint — its resources are **not** simulated. |
| `allow-mock-account` | `false` | Submit with no resolved account. Identities are then derived from a placeholder, so nothing matches your real inventory. Not for a gate. |

**Behaviour.**

| Input | Default | What it does |
|---|---|---|
| `label` | `linro-simulate` | Names the check run. Give each simulation in a workflow its own. |
| `integration` | `github-ci` | `github-ci` → check run. `cli` → poll and print (use on push/schedule). |
| `strict` | `false` | Fail if any resource could not be simulated. |
| `dry-run` | `false` | Print the payload instead of submitting. No server or token needed. |
| `poll-timeout` | | How long to wait for a result on `integration: cli`. |
| `allow-provider-mismatch` | `false` | Proceed past a Pulumi provider major skew. Attributes may be dropped, so a pass means less. |
| `gateway-oidc-audience` | | Override the OIDC audience. Leave unset — the install is asked for its own, so it cannot drift. |
| `debug` | `false` | Debug logging, including the full request/response trace. |
| `project-dir` | | Your IaC sources, for file/line attribution on each resource. Not the same as `working-directory`. |
| `working-directory` | `.` | Where the plan/preview paths resolve from. |
| `extra-args` | | Extra flags, space-separated. An escape hatch. |

**Which CLI runs.**

| Input | Default | What it does |
|---|---|---|
| `version` | `v0.2.1` | CLI version to run, or `latest`. |
| `marketplace-url` | `https://marketplace.linro.io` | Where the CLI is downloaded from. |

Outputs: `version` (the CLI version that ran) and `binary-path`.

Booleans are checked, not guessed: an input that is neither `true` nor `false`
fails the step naming itself. `strict: yes` would otherwise read as false and
quietly turn off the gate you added it for.

### Scope: what a plan knows about itself

Every resource is identified within a scope, and each plugin defines its own:
which values the scope is made of (an AWS account and region, a GCP project, a
T Cloud Public domain), and where a plan or a preview can state them. A
plugin's details in your Linro installation's Marketplace page list its
versions and the resources it collects; its scope is documented with the
plugin.

The scope inputs (`account`, `region`, `project`, `organization`, `domain`) supply what the
plan or preview does not state itself. A value the scope cannot do without, and
that nothing states, refuses the run, unless you allow a placeholder where the
plugin offers one; a placeholder matches nothing in your inventory. How much a
source states differs by tool as well as by provider: a Terraform plan carries
its provider configuration, while a Pulumi preview generally carries far less.

The current rules, per provider:

| Value | Where it can come from, in order |
|---|---|
| AWS region | the plan's provider config, a per-resource hint, then `region` |
| AWS account | an `assume_role` role ARN in the provider config, `stack-export`, then `account` |
| GCP project | the resource's own `project`, then a constant `project` in **its** provider block (a Pulumi preview: an explicit provider's `project` input; for a default provider only, the stack's `gcp:project` / `google-native:project`), then `project` |
| GCP organization | the resource's own `org_id` / `organization` / `organizations/…` parent, then `organization` |
| T Cloud Public domain | a constant `domain_id`/`domain_name` in the `opentelekomcloud` provider block, then `domain`. **That is all.** |

And only a value **written in the provider block** reaches the plan. A provider
configured from the environment — `AWS_REGION`, `OS_DOMAIN_NAME`, both commonly
repo secrets in CI — carries nothing into `terraform show -json`. AWS has two
other paths to fall back on; OTC has none, so an OTC plan in CI needs its input
more often than an AWS plan needs `account`.

### `domain` must match your connector, byte for byte

A T Cloud Public connector's `domain` scope holds **whatever you typed when you
created it** — the 32-hex domain id *or* the account name
(`OTC00000000001000000000`). Linro never rewrites one form into the other, and
every resource's identity is derived from the spelling it holds.

So a simulation passing the other spelling composes rows that shadow nothing:
every simulated resource lands *beside* its live twin instead of over it, the
diff shows everything as new, and **nothing errors**. The run succeeds and
describes a world that does not exist.

Read the value off the connector — do not retype what you think you configured:

```yaml
      - uses: linro-io/simulation-github-action@v1
        with:
          plan: infra/plan.json
          server: ${{ vars.LINRO_SERVER }}
          token: ${{ secrets.LINRO_TOKEN }}
          # Exactly as the connector shows it. `OS_DOMAIN_NAME` in the job's
          # environment configures the provider; it does NOT reach the plan.
          domain: ${{ vars.LINRO_OTC_DOMAIN }}
```

The CLI compares the value literally: it does not fold case and it does not
resolve a name to an id, because doing either would mean calling OTC.

## Several sources, one simulation

`plan` and `preview` are both repeatable — one path per line — and they
**combine**. Any mix of Terraform plans and Pulumi previews becomes ONE
simulation with one verdict, so a change spanning both tools gets a single
answer instead of one per tool:

```yaml
      - uses: linro-io/simulation-github-action@v1
        with:
          plan: |
            infra/plan.json
            data-platform/plan.json
          preview: services/api/preview.json
          server: ${{ vars.LINRO_SERVER }}
          token: ${{ secrets.LINRO_TOKEN }}
          account: "123456789012"
          region: eu-central-1
```

Each source becomes its own resource group, tagged with the tool that produced
it, and the whole set is submitted once. The example above sends three groups —
two Terraform, one Pulumi.

One caveat worth knowing: the sources should describe **different**
infrastructure. Passing the same *path* twice is refused outright, but two
different files describing the same resources are not detectable — they submit
each resource twice under the same identity, inflating the counts without
checking anything more.

## Pulumi

```yaml
      - run: pulumi preview --show-sames --json > preview.json
        working-directory: infra
        env:
          PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_PASSPHRASE }}

      - uses: linro-io/simulation-github-action@v1
        with:
          preview: infra/preview.json
          server: ${{ vars.LINRO_SERVER }}
          token: ${{ secrets.LINRO_TOKEN }}
          account: "123456789012"
          region: eu-central-1
```

## GCP

From CLI **v0.6.18**, GCP resources are simulated by **plugin-gcp**, in all three
dialects: Terraform (`google`, `google-beta`), Pulumi `gcp` and Pulumi
`google-native`. The action's default `version` predates this, so set it.

```yaml
      - uses: linro-io/simulation-github-action@v1
        with:
          version: v0.6.27
          plan: plan.json
          server: ${{ vars.LINRO_SERVER }}
          token: ${{ secrets.LINRO_TOKEN }}
          project: my-gcp-project            # only where the plan states none
          organization: "123456789012"       # only for organization-level resources
```

- **Project.** Read per resource, from the plan first (see the scope table
  above). `project` fills in only where nothing states one. With no project at
  all, the run is refused by name rather than submitted with a malformed
  identity. A resource whose own project the plan hides (a reference to
  something not yet created, a redacted value) is **skipped** with that reason;
  it is never guessed into another project.
- **Organization.** An organization-level resource (a folder, a tag key, an
  access policy, a Security Command Center config) takes the organization it
  states (`org_id`, `organization`, an `organizations/…` parent).
  `organization` fills in where the parent is a folder, a project, or unknown
  until apply, as for a sub-folder of a folder the same plan creates; without
  it such a resource is **skipped** with that reason. A contradiction refuses.
  Organization-level resources are simulated from CLI **v0.6.27**.
- **Pulumi auto-naming.** A Pulumi program that leaves `name` out gets a name
  the provider draws for the preview, and the apply draws a different one. The
  resource is simulated under the preview's name: its findings are real, but it
  can never match a live resource. An update keeps the live name. Set `name`
  explicitly if you want a create to line up with what lands. A resource whose
  name the plan cannot state at all (unknown until apply, redacted) is reported
  as skipped, and resources that reference it are still simulated.
- **Install version.** A resource the plan does not change is submitted with
  fallback columns, and the CLI refuses to send them to an install older than
  Linro Release **2026.10.1**: an older install composes those columns empty,
  which a check would read as compliant. The refusal says so; upgrade the
  install. This applies to every provider, not only GCP.

## Trying it without an install

```yaml
      - uses: linro-io/simulation-github-action@v1
        with:
          plan: plan.json
          account: "123456789012"
          region: eu-central-1
          dry-run: "true"
```

Prints exactly what would be submitted. No server, no token, no account of any
kind — useful for seeing what a simulation actually sends before wiring
credentials.

## Runners

Linux and macOS, `x64` and `arm64`. There is no Windows build of the CLI, and
the action says so rather than failing obscurely.

The CLI is downloaded from the Linro marketplace — the same place your install
gets it — so a version is only available here once it has been published to
your marketplace. If you pin a `version` the marketplace does not serve, the
action fails naming the version and the platform. A network failure says so
separately: the two need opposite fixes.

## Versioning

Pin the action to a major (`@v1`) for automatic fixes, or to an exact release
for full reproducibility. The `version` input pins the **CLI**, independently.
Both are pinned by default; `version: latest` tracks your marketplace, which is
convenient and means a green run stops being evidence about any particular
build.

## What this action is not

It does not create, modify or destroy any infrastructure, and it needs no cloud
credentials of its own — it reads a plan file your workflow already produced.
The only secret it takes is your Linro PAT.

## Licence

This repository — the action, its docs and its tests — is **Apache-2.0**. It is
a wrapper: it downloads a binary and assembles a command line, and you are free
to read, fork and adapt it under those terms.

The **Linro Simulator CLI it downloads is proprietary** and is not covered by
that licence. It is distributed under its own end-user terms and requires a
Linro install and a valid token. See [NOTICE](NOTICE).

## Support

Issues and feature requests: <https://github.com/linro-io/simulation-github-action/issues>.
If you find yourself leaning on `extra-args`, that is worth an issue — a
first-class input is better than a string.

Operator guide: [Add the GitHub Action](docs/product/how-to/add-the-github-action.md).
