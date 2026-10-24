# Evidence: trial scope verification (run f245f73b6ebb4c4b9c06b2ee08457339)

Raw material behind the "Plateau contract verified on real data" section of
PR #38.

- `prepare_args.json`: exact `prepare_optimization` arguments; the second,
  accepted attempt, with `oversold` reordered to `[20, 10, 0]` and the
  `/fit_config` description added.
- `submit_out.json`: the `submit_execution_decision(decision="approve")`
  response, sent after the user explicitly approved in conversation.
- `scopes_parsed.json.gz`: all 15 `trial/{i}/train` scopes plus `test`, as
  returned by `get_run_metrics` and parsed from the text content.
- `trial2_raw.json`: the condensed `trial/2/train` (k=9, oversold=0) quoted in
  the round 2 report.
