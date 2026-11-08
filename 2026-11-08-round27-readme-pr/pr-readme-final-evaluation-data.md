Title: docs(readme): recommend reserving final evaluation data until the strategy is settled

## Summary

Adds one paragraph to the README, at the end of "使用樣本外驗證與最佳化", after the parameter optimization paragraph. It recommends setting aside a period of data as a final evaluation before development starts, and using it only after the rules, features and parameters are chosen. If the strategy is changed after looking at that period's results, the period is no longer an independent final test, and later results should be treated as part of development.

## This is advice to users, not a system rule

- The paragraph says so itself: the system does not check whether a user does this, and does not verify that any period of data has not been used.
- It also says that developing on the most recent data is fine, and that a reserved test period or out-of-sample evidence is not a condition for a result to be included in comparisons.
- No code, schema, tool description or check changes. The diff is five added lines in `README.md`.

## Why it is needed

The statistics integration document on #38 (`docs/statistics_leaderboard_integration.md`, "No holdout requirement for ranking") points to this recommendation by its README section, "使用樣本外驗證與最佳化". That section is on `main`, but the recommendation is not, so the reference only holds once this PR is merged. That document is not on `main` yet either; it arrives with #38.

This PR does not depend on #38 or on any of the statistics split PRs, and can be merged on its own.

## Verification

This repository has no CI, so nothing on GitHub runs these checks. Checks were run locally on this branch merged into `main`, verified at `main` c246355:

- `scripts/check-fast.sh`: passes (includes the Markdown and local link checks).
- Documentation only; no tests were run.

The branch is based on a77babf, and upstream has since revised the README substantially. With full history, the paragraph lands at the end of the same section, after the optimization paragraph and before "研究機器學習訊號".

🤖 Generated with [Claude Code](https://claude.com/claude-code)
