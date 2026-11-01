#!/usr/bin/env bash
# Usage: check_full_launcher.sh <clean-worktree-path> > log 2>&1
# Run it as the Bash tool's background command, never with bash `&`.
set -uo pipefail
wt=$(realpath "${1:?worktree path}") || exit 89
here=$(dirname "$(realpath "$0")")
cd "$wt" || exit 90
[ "$(pwd -P)" = "$wt" ] || { echo "wrong cwd $(pwd -P)"; exit 91; }
unset PYTEST_ADDOPTS
echo "HEAD $(git rev-parse HEAD)"
date
python3 "$here/default_signals_exec.py" scripts/check-full.sh
rc=$?
date
echo "EXIT $rc"
exit $rc
