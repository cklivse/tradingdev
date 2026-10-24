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
