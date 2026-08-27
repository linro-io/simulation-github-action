# Linro Simulation — GitHub Action

Run your Terraform plans and Pulumi previews through Linro's real policy engine
**before you apply**, and get the verdict as a check on the pull request.

Any number of sources, in any mix, become **one** simulation with one verdict.

Not a linter. The simulation goes through the same plugin normalization and the
same checks Linro runs against your live inventory, so a passing simulation
means a passing apply.

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

      - uses: linro-io/simulation-action@v1
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
`integration: cli`, which polls for the result and exits non-zero on failure,
at the cost of the check-run UI.

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
| `project` | | GCP project. |
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

A Terraform plan carries its provider configuration, so `account` and `region`
are often recoverable from the plan alone. A **Pulumi preview carries none** —
if you simulate a preview, pass `account`/`region` (and `project` for GCP), or
the resources are identified against the wrong scope.

## Several sources, one simulation

`plan` and `preview` are both repeatable — one path per line — and they
**combine**. Any mix of Terraform plans and Pulumi previews becomes ONE
simulation with one verdict, so a change spanning both tools gets a single
answer instead of one per tool:

```yaml
      - uses: linro-io/simulation-action@v1
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
      - run: pulumi preview --json > preview.json
        working-directory: infra
        env:
          PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_PASSPHRASE }}

      - uses: linro-io/simulation-action@v1
        with:
          preview: infra/preview.json
          server: ${{ vars.LINRO_SERVER }}
          token: ${{ secrets.LINRO_TOKEN }}
          account: "123456789012"
          region: eu-central-1
```

## Trying it without an install

```yaml
      - uses: linro-io/simulation-action@v1
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

Issues and feature requests: <https://github.com/linro-io/simulation-action/issues>.
If you find yourself leaning on `extra-args`, that is worth an issue — a
first-class input is better than a string.
