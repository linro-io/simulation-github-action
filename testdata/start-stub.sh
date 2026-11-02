#!/usr/bin/env bash
# Start testdata/stub-install.py in the background and print its URL.
#   start-stub.sh <name> <mode>   (token: ci-token; log: $RUNNER_TEMP/<name>.log)
set -euo pipefail
name=$1 mode=$2
port_file="${RUNNER_TEMP}/${name}.port"
rm -f "$port_file"
STUB_TOKEN=ci-token STUB_MODE="$mode" nohup python3 "$(dirname "$0")/stub-install.py" \
  "$port_file" "${RUNNER_TEMP}/${name}.log" > "${RUNNER_TEMP}/${name}.out" 2>&1 &
for _ in $(seq 100); do
  if [ -s "$port_file" ]; then
    echo "http://127.0.0.1:$(cat "$port_file")"
    exit 0
  fi
  sleep 0.1
done
cat "${RUNNER_TEMP}/${name}.out" >&2
echo "the stub did not start" >&2
exit 1
