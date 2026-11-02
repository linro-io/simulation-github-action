#!/usr/bin/env bash
# expect-refusal.sh <case> <step outcome> <expected reason>
#
# A refusal must fail the step AND for its own reason: the action records
# each ::error:: in $RUNNER_TEMP/linro-simulation-error, so a stub 502 cannot
# stand in for the sha256 check. The file is removed so the next case starts
# clean.
set -euo pipefail
name=$1 outcome=$2 want=$3
file="${RUNNER_TEMP}/linro-simulation-error"
got=$(cat "$file" 2>/dev/null || true)
rm -f "$file"
if [ "$outcome" != "failure" ]; then
  echo "::error::${name} should have failed the step, got '${outcome}'"
  exit 1
fi
if ! printf '%s' "$got" | grep -qF -- "$want"; then
  echo "::error::${name} failed for another reason. Want '${want}', got: ${got:-<nothing recorded>}"
  exit 1
fi
echo "ok: ${name} → ${got}"
