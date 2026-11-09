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

Added 2026-11-09 (round 34):

- `marp_to_pptx.js <slides.md> <out.pptx>`: rebuilds a Marp deck that uses the
  tradingdev theme as an editable PowerPoint file (pptxgenjs 3.12.0). It keeps
  tables, links, headers, footers, page numbers and speaker notes, takes sizes
  and colors from `theme.css` at 96 px per inch, and shrinks a slide (to 80% at
  most) when its estimated height doesn't fit. Needs `pptxgenjs` on `NODE_PATH`
  and `PPTX_SKILL` pointing at the pptx skill directory (for `apply_theme.js`).
  It handles only what the statistics talk uses: no images, Mermaid or blockquotes.
  After writing, it keeps only the first `<a:pPr>` of each paragraph (pptxgenjs
  writes one per run, which hid the bullet of any item with bold or code) and
  sets bullet color to the body color. Round 35 added this fix.

Added 2026-11-09 (round 36):

- `font_widths.py <slides.md> <out.json>`: measures every character of the deck
  in the preview fonts (Noto Sans CJK TC regular and bold, Liberation Mono,
  found through fontconfig) and writes the advance widths in em. Run it with a
  Python that has Pillow.
- `marp_to_pptx.js` now reads that table through `WIDTHS=<out.json>`. Table
  column widths are tuned to avoid a stray character or bracket on its own line:
  a column is widened when that keeps the table no taller and leaves fewer such
  orphans. It also puts a zero-width space after 、，； etc. when Latin text or
  code follows, because LibreOffice otherwise breaks inside paths at "/".
