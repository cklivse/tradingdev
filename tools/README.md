# Session tools

Scripts written during the 2026-10-24 sessions, kept so they survive the
per-session scratchpad. Run them from `/workspaces/tradingdev` with
`uv run --no-sync python <script>`.

- `mcp_call.py <tool> <args.json | 'json'> [out.json]`: calls one tool on the
  real tradingdev MCP server over stdio, spawned as `.mcp.json` does. Used
  when the session's native MCP connection had timed out.
- `read_scopes.py <run_id> <out.json>`: reads `trial/0..14/train` and `test`
  through `get_run_metrics` in one session.
- `verify.py <out_dir>`: re-runs both demos into `<out_dir>` and prints the
  five verified figures at full precision. It predates the pinned KD input
  and monkeypatches the old `latest_cache()`, so on
  `feat/stats-pinned-fixtures` it needs adjusting to call
  `resolve_kd_source()` instead.

Added 2026-11-01 (rounds 15b–16):

- `check_full_launcher.sh <worktree>`: runs `scripts/check-full.sh` in a clean
  worktree (needs its own `.venv`: `uv sync --locked --all-extras`). Asserts
  the cwd, unsets `PYTEST_ADDOPTS`, prints HEAD, dates and `EXIT <rc>`.
  Launch it as a background Bash-tool command with output redirected to a
  log; do not use bash `&`, which leaves SIGINT ignored in the children.
- `default_signals_exec.py <cmd...>`: forks; the child calls `setsid`, resets
  SIGINT and SIGQUIT to `SIG_DFL` and execs the command; the parent ignores
  SIGINT, waits and exits with the child's code. The tests that send SIGINT
  to workers need the default disposition.
- Known incident: on 2026-11-01 one run was killed by SIGTERM at 76%
  (`tests/e2e/test_workflow_verifier.py`, exit 241) with no failures before
  it; the sender was not found. A rerun of the same commit passed (7480).
