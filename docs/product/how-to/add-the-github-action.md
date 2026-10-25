---
id: how-to/add-the-github-action
title: Add the GitHub Action
kind: how-to
audience: customer
reader: both
covers: []
verified: 2026.10.5
---

# Add the GitHub Action

Run a reviewed Terraform plan or Pulumi preview through Linro from a pull request. Read {{page:service/concepts/simulations}} for scope and coverage limits. The simulation check is separate from the Action step that submits the work.

## Prepare the workflow

Have the repository owner choose a reviewed Action revision and compatible published simulator version. Configure the Linro server variable and a simulation-scoped token in repository secrets. Do not paste a token into the workflow.

```yaml
name: Linro simulation
on: pull_request
permissions:
  contents: read
  id-token: write
jobs:
  simulate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # Produce and review plan.json with your normal Terraform workflow first.
      - uses: linro-io/simulation-github-action@REVIEWED_ACTION_REF
        with:
          version: REVIEWED_COMPATIBLE_CLI_VERSION
          plan: plan.json
          server: ${{ vars.LINRO_SERVER }}
          token: ${{ secrets.LINRO_TOKEN }}
          account: "AWS_ACCOUNT_ID"
          region: AWS_REGION
          strict: "true"
          label: linro-reviewed-plan
```

When it worked, the submission step is accepted and a separate simulation check appears with the configured label. Review its actual findings and coverage, and require that check in branch protection if it is your merge gate. A green submitting step does not mean a passing simulation.

Known gaps: this fragment assumes your preceding workflow produces plan.json and has its normal cloud permissions. It does not provide a complete Terraform pipeline. Pull-request OIDC permission is required for a gateway-backed check; a direct GitHub App deployment differs. Ask your installation operator which path is configured. A throwaway local App key cannot create real PR checks.

For Pulumi, generate the preview with unchanged resources included, then set preview to its file. For several plans or previews, put one path per line and use a distinct label for concurrent simulations. Do not use overlapping source files or mock scope values for a deployment gate.
