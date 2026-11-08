# Tests that fail without the strategy-runtime image (clean `main` 741fd84)

Clean `main` 741fd84 (no statistics code), 7588 collected tests. 225 fail because this environment has no `tradingdev-strategy-runtime` image: 219 report `runtime_unavailable`, 6 fail at container start without a diagnostic code.

How the suite was run: the full suite is stopped by an external SIGTERM at test 4705 in this environment, so it was run in two parts in collection order. Tests 1-4711 ran under strace (2026-11-07); 6 Streamlit tests in `tests/adapters/test_dashboard_render.py` timed out only because of strace, pass without it, and are not listed. Tests 4712-7588 ran without strace (2026-11-08).

Evidence per test:

- A: the failure message or traceback locals contain `runtime_unavailable` or `Strategy runtime image 'tradingdev-strategy-runtime:0.1.0' is unavailable`.
- B: the message was truncated; a plugin wrapping every public `StrategyService` method saw `runtime_unavailable` in a return value or exception during the test.
- C: the service runs in a subprocess; its captured output (`pytest -l`) contains `runtime_unavailable`.
- D: no diagnostic code. The test waits for a Docker container unit to start and fails because none started; the local Docker daemon has no images.

Totals: A 103, B 108, C 8, D 6.

## By file

| File | Tests | Evidence |
| --- | ---: | --- |
| `tests/app/test_comparison_plans.py` | 4 | B 4 |
| `tests/app/test_comparison_preflight.py` | 9 | B 9 |
| `tests/app/test_execution_plan_service.py` | 2 | B 2 |
| `tests/app/test_generated_strategy_job.py` | 6 | B 6 |
| `tests/app/test_preflight_service.py` | 15 | B 15 |
| `tests/app/test_research_preparation.py` | 11 | B 11 |
| `tests/app/test_strategy_experiments.py` | 22 | A 22 |
| `tests/app/test_strategy_service.py` | 9 | A 6, B 3 |
| `tests/domain/strategies/test_loader_contract.py` | 11 | A 11 |
| `tests/domain/strategies/test_strategy_execution.py` | 9 | A 9 |
| `tests/domain/strategies/test_template_execution.py` | 9 | A 9 |
| `tests/e2e/test_cleanup_workflow_evidence.py` | 1 | A 1 |
| `tests/e2e/test_codex_verifier.py` | 3 | A 2, D 1 |
| `tests/e2e/test_llm_execution_plans.py` | 1 | B 1 |
| `tests/e2e/test_workflow_verifier.py` | 33 | B 33 |
| `tests/integration/test_generated_protocol.py` | 16 | A 16 |
| `tests/integration/test_generated_runtime.py` | 3 | A 3 |
| `tests/integration/test_generated_worker_cleanup.py` | 3 | D 3 |
| `tests/integration/test_mcp_cleanup.py` | 3 | B 3 |
| `tests/integration/test_mcp_optimization.py` | 2 | B 2 |
| `tests/integration/test_mcp_protocol.py` | 6 | A 6 |
| `tests/integration/test_mcp_research_intake.py` | 1 | B 1 |
| `tests/integration/test_parameter_experiments.py` | 2 | A 2 |
| `tests/integration/test_preflight_temporary_files.py` | 8 | B 8 |
| `tests/integration/test_preflight_workers.py` | 8 | B 8 |
| `tests/integration/test_strategy_check_workers.py` | 14 | A 4, C 8, D 2 |
| `tests/integration/test_strategy_isolation.py` | 9 | A 9 |
| `tests/mcp/test_strategy_contracts.py` | 5 | A 3, B 2 |
| **Total** | **225** | |

## Every test

Numbers are positions in the 741fd84 collection order.

| # | Test | Evidence |
| ---: | --- | --- |
| 605 | `tests/app/test_comparison_plans.py::test_parallel_approval_launches_one_comparison_with_every_reviewed_candidate` | B |
| 606 | `tests/app/test_comparison_plans.py::test_whole_comparison_rejection_launches_no_candidate[decline]` | B |
| 607 | `tests/app/test_comparison_plans.py::test_whole_comparison_rejection_launches_no_candidate[revise]` | B |
| 608 | `tests/app/test_comparison_plans.py::test_change_to_shared_source_after_review_blocks_all_candidates` | B |
| 619 | `tests/app/test_comparison_preflight.py::test_all_eight_candidates_check_actual_parameters_without_history_or_base_changes` | B |
| 621 | `tests/app/test_comparison_preflight.py::test_duplicate_candidates_fail_closed[effective_parameters]` | B |
| 622 | `tests/app/test_comparison_preflight.py::test_duplicate_candidates_fail_closed[label]` | B |
| 623 | `tests/app/test_comparison_preflight.py::test_later_candidate_contract_failure_produces_no_partial_success` | B |
| 624 | `tests/app/test_comparison_preflight.py::test_comparison_requires_each_child_and_bundle_serialization[child]` | B |
| 625 | `tests/app/test_comparison_preflight.py::test_comparison_requires_each_child_and_bundle_serialization[bundle]` | B |
| 628 | `tests/app/test_comparison_preflight.py::test_parent_uses_one_whole_comparison_budget_and_cleans_up[success]` | B |
| 629 | `tests/app/test_comparison_preflight.py::test_parent_uses_one_whole_comparison_budget_and_cleans_up[timeout]` | B |
| 630 | `tests/app/test_comparison_preflight.py::test_parent_uses_one_whole_comparison_budget_and_cleans_up[wrong_receipt]` | B |
| 842 | `tests/app/test_execution_plan_service.py::test_changed_generated_revision_after_question_cannot_start[source_path]` | B |
| 843 | `tests/app/test_execution_plan_service.py::test_changed_generated_revision_after_question_cannot_start[config_path]` | B |
| 885 | `tests/app/test_generated_strategy_job.py::test_generated_strategy_can_start_backtest_job` | B |
| 886 | `tests/app/test_generated_strategy_job.py::test_queued_revision_runs_after_new_draft_is_saved` | B |
| 887 | `tests/app/test_generated_strategy_job.py::test_execution_rejects_revision_identity_overrides[source_path-other.py]` | B |
| 888 | `tests/app/test_generated_strategy_job.py::test_execution_rejects_revision_identity_overrides[class_name-UnvalidatedStrategy]` | B |
| 889 | `tests/app/test_generated_strategy_job.py::test_execution_rejects_revision_identity_overrides[revision_id-None]` | B |
| 890 | `tests/app/test_generated_strategy_job.py::test_execution_rejects_revision_identity_overrides[fit-True]` | B |
| 1306 | `tests/app/test_preflight_service.py::test_preflight_checks_effective_program_without_market_training_or_engine[backtest]` | B |
| 1307 | `tests/app/test_preflight_service.py::test_preflight_checks_effective_program_without_market_training_or_engine[walk_forward]` | B |
| 1308 | `tests/app/test_preflight_service.py::test_preflight_checks_effective_program_without_market_training_or_engine[optimization]` | B |
| 1313 | `tests/app/test_preflight_service.py::test_preflight_rejects_invalid_generated_programs[exception]` | B |
| 1314 | `tests/app/test_preflight_service.py::test_preflight_rejects_invalid_generated_programs[invalid_signal]` | B |
| 1315 | `tests/app/test_preflight_service.py::test_preflight_rejects_invalid_generated_programs[input_mutated]` | B |
| 1316 | `tests/app/test_preflight_service.py::test_invalid_purged_configuration_is_rejected_without_splitting_data[invalid0]` | B |
| 1317 | `tests/app/test_preflight_service.py::test_invalid_purged_configuration_is_rejected_without_splitting_data[invalid1]` | B |
| 1318 | `tests/app/test_preflight_service.py::test_invalid_purged_configuration_is_rejected_without_splitting_data[invalid2]` | B |
| 1319 | `tests/app/test_preflight_service.py::test_preflight_requires_actual_fixture_evidence` | B |
| 1320 | `tests/app/test_preflight_service.py::test_preflight_requires_manifest_serialization` | B |
| 1321 | `tests/app/test_preflight_service.py::test_parent_cleans_temporary_files_after_verified_worker_cleanup[success]` | B |
| 1322 | `tests/app/test_preflight_service.py::test_parent_cleans_temporary_files_after_verified_worker_cleanup[exception]` | B |
| 1323 | `tests/app/test_preflight_service.py::test_parent_cleans_temporary_files_after_verified_worker_cleanup[timeout]` | B |
| 1324 | `tests/app/test_preflight_service.py::test_parent_cleans_temporary_files_after_verified_worker_cleanup[invalid_response]` | B |
| 1487 | `tests/app/test_research_preparation.py::test_selected_revision_research_and_origin_reach_captured_manifest` | B |
| 1488 | `tests/app/test_research_preparation.py::test_second_financial_setting_channel_cannot_replace_research[init_cash]` | B |
| 1489 | `tests/app/test_research_preparation.py::test_second_financial_setting_channel_cannot_replace_research[fees]` | B |
| 1490 | `tests/app/test_research_preparation.py::test_second_financial_setting_channel_cannot_replace_research[slippage]` | B |
| 1491 | `tests/app/test_research_preparation.py::test_second_financial_setting_channel_cannot_replace_research[periods_per_year]` | B |
| 1492 | `tests/app/test_research_preparation.py::test_optimization_cannot_rewrite_or_shrink_the_requested_period[start_date-2023-12-01]` | B |
| 1493 | `tests/app/test_research_preparation.py::test_optimization_cannot_rewrite_or_shrink_the_requested_period[end_date-2024-02-02]` | B |
| 1494 | `tests/app/test_research_preparation.py::test_optimization_cannot_rewrite_or_shrink_the_requested_period[end_date-2024-01-31]` | B |
| 1495 | `tests/app/test_research_preparation.py::test_optimization_cannot_rewrite_or_shrink_the_requested_period[end_date-2024-02-01T00:00:00Z]` | B |
| 1496 | `tests/app/test_research_preparation.py::test_programmatic_overrides_do_not_relabel_old_research_sources[backtest]` | B |
| 1497 | `tests/app/test_research_preparation.py::test_programmatic_overrides_do_not_relabel_old_research_sources[optimization]` | B |
| 1915 | `tests/app/test_strategy_experiments.py::test_two_experiments_share_revision_and_freeze_nested_parameters` | A |
| 1916 | `tests/app/test_strategy_experiments.py::test_cli_effective_parameters_execute_without_saving_revision[False]` | A |
| 1917 | `tests/app/test_strategy_experiments.py::test_cli_effective_parameters_execute_without_saving_revision[True]` | A |
| 1918 | `tests/app/test_strategy_experiments.py::test_cli_rejects_experiment_contract_failures_before_loading_data[False-constructor-selected constructor rejected]` | A |
| 1919 | `tests/app/test_strategy_experiments.py::test_cli_rejects_experiment_contract_failures_before_loading_data[False-mutation-input_mutated]` | A |
| 1920 | `tests/app/test_strategy_experiments.py::test_cli_rejects_experiment_contract_failures_before_loading_data[False-long_fixture-invalid_signal_values]` | A |
| 1921 | `tests/app/test_strategy_experiments.py::test_cli_rejects_experiment_contract_failures_before_loading_data[True-constructor-selected constructor rejected]` | A |
| 1922 | `tests/app/test_strategy_experiments.py::test_cli_rejects_experiment_contract_failures_before_loading_data[True-mutation-input_mutated]` | A |
| 1923 | `tests/app/test_strategy_experiments.py::test_cli_rejects_experiment_contract_failures_before_loading_data[True-long_fixture-invalid_signal_values]` | A |
| 1924 | `tests/app/test_strategy_experiments.py::test_submission_rejects_bad_parameters_without_job_or_revision[constructor-selected constructor rejected]` | A |
| 1925 | `tests/app/test_strategy_experiments.py::test_submission_rejects_bad_parameters_without_job_or_revision[mutation-input_mutated]` | A |
| 1926 | `tests/app/test_strategy_experiments.py::test_submission_rejects_bad_parameters_without_job_or_revision[long_fixture-invalid_signal_values]` | A |
| 1927 | `tests/app/test_strategy_experiments.py::test_submission_rejects_unknown_or_non_json_parameters[parameters0]` | A |
| 1928 | `tests/app/test_strategy_experiments.py::test_submission_rejects_unknown_or_non_json_parameters[parameters1]` | A |
| 1929 | `tests/app/test_strategy_experiments.py::test_submission_rejects_unknown_or_non_json_parameters[parameters2]` | A |
| 1930 | `tests/app/test_strategy_experiments.py::test_submission_rejects_unknown_or_non_json_parameters[parameters3]` | A |
| 1931 | `tests/app/test_strategy_experiments.py::test_worker_rechecks_captured_parameters_even_for_direct_manifest` | A |
| 1932 | `tests/app/test_strategy_experiments.py::test_manifest_uses_frozen_defaults_during_check_and_actual_execution` | A |
| 1933 | `tests/app/test_strategy_experiments.py::test_optimization_candidates_recheck_actual_parameters[constructor]` | A |
| 1934 | `tests/app/test_strategy_experiments.py::test_optimization_candidates_recheck_actual_parameters[mutation]` | A |
| 1935 | `tests/app/test_strategy_experiments.py::test_optimization_candidates_recheck_actual_parameters[long_fixture]` | A |
| 1936 | `tests/app/test_strategy_experiments.py::test_walk_forward_keeps_each_fitted_parameter_snapshot[fitted]` | A |
| 1937 | `tests/app/test_strategy_service.py::test_strategy_service_lifecycle` | A |
| 1956 | `tests/app/test_strategy_service.py::test_validation_and_dry_run_seed_constructor_and_signals` | A |
| 1962 | `tests/app/test_strategy_service.py::test_validate_rejects_runnable_strategy` | B |
| 1963 | `tests/app/test_strategy_service.py::test_dry_run_only_accepts_validated_strategy` | B |
| 1967 | `tests/app/test_strategy_service.py::test_strategy_service_rejects_invalid_signal_values` | A |
| 1968 | `tests/app/test_strategy_service.py::test_strategy_service_rejects_input_mutation` | A |
| 1969 | `tests/app/test_strategy_service.py::test_strategy_service_validates_and_dry_runs_direct_talib_strategy` | A |
| 1970 | `tests/app/test_strategy_service.py::test_validation_finishes_on_captured_revision_after_new_save` | A |
| 1975 | `tests/app/test_strategy_service.py::test_dry_run_cannot_replace_newer_validation_in_the_same_status` | B |
| 3686 | `tests/domain/strategies/test_loader_contract.py::test_loader_rejects_deprecated_strategy_class_and_file_fields` | A |
| 3688 | `tests/domain/strategies/test_loader_contract.py::test_loader_rejects_legacy_bundled_strategy_id` | A |
| 3692 | `tests/domain/strategies/test_loader_contract.py::test_generated_parameters_match_contract_and_execution` | A |
| 3693 | `tests/domain/strategies/test_loader_contract.py::test_bad_parameters_fail_contract_and_execution[parameters0-missing a required argument: 'threshold'-strategy_execution_failed-missing a required argument: 'threshold']` | A |
| 3694 | `tests/domain/strategies/test_loader_contract.py::test_bad_parameters_fail_contract_and_execution[parameters1-unexpected keyword argument-strategy_execution_failed-unexpected keyword argument]` | A |
| 3695 | `tests/domain/strategies/test_loader_contract.py::test_bad_parameters_fail_contract_and_execution[parameters2-cannot accept-strategy_execution_failed-cannot accept]` | A |
| 3697 | `tests/domain/strategies/test_loader_contract.py::test_signal_contract_rejects_application_service_injection` | A |
| 3698 | `tests/domain/strategies/test_loader_contract.py::test_signal_contract_rejects_unrecordable_constructor_defaults` | A |
| 3699 | `tests/domain/strategies/test_loader_contract.py::test_loader_honors_workspace_environment_and_explicit_override` | A |
| 3704 | `tests/domain/strategies/test_loader_contract.py::test_loader_reads_latest_source_after_same_size_same_timestamp_rewrite` | A |
| 3705 | `tests/domain/strategies/test_loader_contract.py::test_loader_rejects_modified_source_with_pinned_hash` | A |
| 3922 | `tests/domain/strategies/test_strategy_execution.py::test_generated_defaults_are_fixed_even_when_new_configuration_is_supplied` | A |
| 3923 | `tests/domain/strategies/test_strategy_execution.py::test_generated_added_constructor_default_requires_resubmission` | A |
| 3924 | `tests/domain/strategies/test_strategy_execution.py::test_generated_non_json_defaults_fail_before_submission[False-object()]` | A |
| 3925 | `tests/domain/strategies/test_strategy_execution.py::test_generated_non_json_defaults_fail_before_submission[False-float('nan')]` | A |
| 3926 | `tests/domain/strategies/test_strategy_execution.py::test_generated_non_json_defaults_fail_before_submission[False-(1, 2)]` | A |
| 3927 | `tests/domain/strategies/test_strategy_execution.py::test_generated_non_json_defaults_fail_before_submission[True-object()]` | A |
| 3928 | `tests/domain/strategies/test_strategy_execution.py::test_generated_non_json_defaults_fail_before_submission[True-float('nan')]` | A |
| 3929 | `tests/domain/strategies/test_strategy_execution.py::test_generated_non_json_defaults_fail_before_submission[True-(1, 2)]` | A |
| 3930 | `tests/domain/strategies/test_strategy_execution.py::test_generated_kwargs_keep_explicit_values` | A |
| 3933 | `tests/domain/strategies/test_template_execution.py::test_example_holds_long_until_flat_and_executes_at_next_open[False-exit-on-equality]` | A |
| 3934 | `tests/domain/strategies/test_template_execution.py::test_example_holds_long_until_flat_and_executes_at_next_open[False-exit-on-decline]` | A |
| 3935 | `tests/domain/strategies/test_template_execution.py::test_example_holds_long_until_flat_and_executes_at_next_open[True-exit-on-equality]` | A |
| 3936 | `tests/domain/strategies/test_template_execution.py::test_example_holds_long_until_flat_and_executes_at_next_open[True-exit-on-decline]` | A |
| 3937 | `tests/domain/strategies/test_template_execution.py::test_example_respects_changed_parameters_and_their_warmup` | A |
| 3938 | `tests/domain/strategies/test_template_execution.py::test_example_stays_flat_when_averages_are_equal` | A |
| 3939 | `tests/domain/strategies/test_template_execution.py::test_example_does_not_hold_when_an_average_is_missing` | A |
| 3940 | `tests/domain/strategies/test_template_execution.py::test_example_rejects_infinite_prices[inf]` | A |
| 3941 | `tests/domain/strategies/test_template_execution.py::test_example_rejects_infinite_prices[-inf]` | A |
| 4705 | `tests/e2e/test_cleanup_workflow_evidence.py::test_cleanup_seed_and_evidence_use_real_mcp_and_preserve_history` | A |
| 4812 | `tests/e2e/test_codex_verifier.py::test_verifier_checks_generated_strategy_in_a_separate_process` | A |
| 4813 | `tests/e2e/test_codex_verifier.py::test_novice_verifier_rejects_executed_short_revision_after_current_is_repaired` | A |
| 4814 | `tests/e2e/test_codex_verifier.py::test_verifier_terminates_hanging_generated_code_and_removes_artifacts` | D |
| 5021 | `tests/e2e/test_llm_execution_plans.py::test_execution_plan_live_fixtures_without_model[walk_forward]` | B |
| 5546 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_accepts_completed_backtest[sma]` | B |
| 5547 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_accepts_saved_custom_report[sma]` | B |
| 5548 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_registration_corruption[sma-path]` | B |
| 5549 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_registration_corruption[sma-report_id]` | B |
| 5550 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[sma-run_ids]` | B |
| 5551 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[sma-available_scopes]` | B |
| 5552 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[sma-html_sha256]` | B |
| 5553 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_signals[sma]` | B |
| 5554 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_yaml_parameters[sma]` | B |
| 5555 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_stored_metrics[sma]` | B |
| 5556 | `tests/e2e/test_workflow_verifier.py::test_workflow_evidence_requires_model_to_query_result[sma]` | B |
| 5557 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_accepts_completed_backtest[momentum]` | B |
| 5558 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_accepts_saved_custom_report[momentum]` | B |
| 5559 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_registration_corruption[momentum-path]` | B |
| 5560 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_registration_corruption[momentum-report_id]` | B |
| 5561 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[momentum-run_ids]` | B |
| 5562 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[momentum-available_scopes]` | B |
| 5563 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[momentum-html_sha256]` | B |
| 5564 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_signals[momentum]` | B |
| 5565 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_yaml_parameters[momentum]` | B |
| 5566 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_stored_metrics[momentum]` | B |
| 5567 | `tests/e2e/test_workflow_verifier.py::test_workflow_evidence_requires_model_to_query_result[momentum]` | B |
| 5568 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_accepts_completed_backtest[experiment]` | B |
| 5569 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_accepts_saved_custom_report[experiment]` | B |
| 5570 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_registration_corruption[experiment-path]` | B |
| 5571 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_registration_corruption[experiment-report_id]` | B |
| 5572 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[experiment-run_ids]` | B |
| 5573 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[experiment-available_scopes]` | B |
| 5574 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_report_manifest_corruption[experiment-html_sha256]` | B |
| 5575 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_signals[experiment]` | B |
| 5576 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_yaml_parameters[experiment]` | B |
| 5577 | `tests/e2e/test_workflow_verifier.py::test_workflow_verifier_rejects_incorrect_stored_metrics[experiment]` | B |
| 5578 | `tests/e2e/test_workflow_verifier.py::test_workflow_evidence_requires_model_to_query_result[experiment]` | B |
| 5604 | `tests/integration/test_generated_protocol.py::test_direct_calls_keep_training_rng_and_exact_frame_types` | A |
| 5605 | `tests/integration/test_generated_protocol.py::test_parameter_inspection_captures_and_validates_without_construction` | A |
| 5606 | `tests/integration/test_generated_protocol.py::test_parameter_inspection_rejects_non_data_constructor_contracts[python-default]` | A |
| 5607 | `tests/integration/test_generated_protocol.py::test_parameter_inspection_rejects_non_data_constructor_contracts[nonfinite-default]` | A |
| 5608 | `tests/integration/test_generated_protocol.py::test_parameter_inspection_rejects_non_data_constructor_contracts[service-injection]` | A |
| 5609 | `tests/integration/test_generated_protocol.py::test_parameter_inspection_rejects_non_data_constructor_contracts[wrong-base-class]` | A |
| 5610 | `tests/integration/test_generated_protocol.py::test_worker_rejects_source_identity_changes_and_reconstruction[hash]` | A |
| 5611 | `tests/integration/test_generated_protocol.py::test_worker_rejects_source_identity_changes_and_reconstruction[identity]` | A |
| 5612 | `tests/integration/test_generated_protocol.py::test_worker_rejects_source_identity_changes_and_reconstruction[source]` | A |
| 5613 | `tests/integration/test_generated_protocol.py::test_worker_rejects_source_identity_changes_and_reconstruction[reconstruct]` | A |
| 5614 | `tests/integration/test_generated_protocol.py::test_input_mutation_preserves_diagnostics_and_available_analysis` | A |
| 5615 | `tests/integration/test_generated_protocol.py::test_failed_or_timed_out_calls_clean_up_and_allow_the_next_session[import_exit]` | A |
| 5616 | `tests/integration/test_generated_protocol.py::test_failed_or_timed_out_calls_clean_up_and_allow_the_next_session[constructor_exit]` | A |
| 5617 | `tests/integration/test_generated_protocol.py::test_failed_or_timed_out_calls_clean_up_and_allow_the_next_session[signals_loop]` | A |
| 5618 | `tests/integration/test_generated_protocol.py::test_proxy_rejects_non_object_parameter_and_trace_values[parameters]` | A |
| 5619 | `tests/integration/test_generated_protocol.py::test_proxy_rejects_non_object_parameter_and_trace_values[trace]` | A |
| 5620 | `tests/integration/test_generated_runtime.py::test_factory_binds_saved_program_and_settings_to_a_managed_instance` | A |
| 5621 | `tests/integration/test_generated_runtime.py::test_source_drift_is_rejected_before_a_new_instance_is_opened` | A |
| 5622 | `tests/integration/test_generated_runtime.py::test_lazy_parameter_grid_reuses_one_unit_without_constructing_a_strategy` | A |
| 5623 | `tests/integration/test_generated_worker_cleanup.py::test_supervisor_removes_container_with_detached_generated_descendant[cancel_other_session]` | D |
| 5624 | `tests/integration/test_generated_worker_cleanup.py::test_supervisor_removes_container_with_detached_generated_descendant[timeout]` | D |
| 5625 | `tests/integration/test_generated_worker_cleanup.py::test_supervisor_removes_container_with_detached_generated_descendant[abrupt]` | D |
| 5645 | `tests/integration/test_mcp_cleanup.py::test_active_worker_and_files_are_removed_on_context_exit[success]` | B |
| 5646 | `tests/integration/test_mcp_cleanup.py::test_active_worker_and_files_are_removed_on_context_exit[failure]` | B |
| 5647 | `tests/integration/test_mcp_cleanup.py::test_active_worker_and_files_are_removed_on_context_exit[timeout]` | B |
| 5655 | `tests/integration/test_mcp_optimization.py::test_optimization_rejects_walk_forward_config_through_mcp` | B |
| 5656 | `tests/integration/test_mcp_optimization.py::test_optimization_confirmation_search_and_persisted_oos` | B |
| 5657 | `tests/integration/test_mcp_protocol.py::test_generated_strategy_full_mcp_workflow` | A |
| 5658 | `tests/integration/test_mcp_protocol.py::test_rejected_drafts_diagnostics_and_repair` | A |
| 5659 | `tests/integration/test_mcp_protocol.py::test_worker_failure_is_reported_and_cancelled_job_stops` | A |
| 5661 | `tests/integration/test_mcp_protocol.py::test_walk_forward_runs_through_real_worker[automatic]` | A |
| 5662 | `tests/integration/test_mcp_protocol.py::test_walk_forward_runs_through_real_worker[explicit_offset_dates]` | A |
| 5663 | `tests/integration/test_mcp_protocol.py::test_walk_forward_runs_through_real_worker[purged]` | A |
| 5664 | `tests/integration/test_mcp_research_intake.py::test_omitted_finances_and_inherited_choices_survive_worker_round_trip` | B |
| 5666 | `tests/integration/test_parameter_experiments.py::test_parameter_experiments_preserve_source_and_base_settings[False]` | A |
| 5667 | `tests/integration/test_parameter_experiments.py::test_parameter_experiments_preserve_source_and_base_settings[True]` | A |
| 5668 | `tests/integration/test_preflight_temporary_files.py::test_preflight_removes_worker_library_temporary_files_after_process_exit[success]` | B |
| 5669 | `tests/integration/test_preflight_temporary_files.py::test_preflight_removes_worker_library_temporary_files_after_process_exit[failure]` | B |
| 5670 | `tests/integration/test_preflight_temporary_files.py::test_preflight_removes_worker_library_temporary_files_after_process_exit[timeout]` | B |
| 5671 | `tests/integration/test_preflight_temporary_files.py::test_preflight_removes_worker_library_temporary_files_after_process_exit[library_failure]` | B |
| 5672 | `tests/integration/test_preflight_temporary_files.py::test_probe_teardown_stops_processes_after_assertion_failure` | B |
| 5673 | `tests/integration/test_preflight_temporary_files.py::test_probe_teardown_stops_processes_when_preflight_cleanup_fails` | B |
| 5674 | `tests/integration/test_preflight_temporary_files.py::test_probe_teardown_retains_files_when_its_cleanup_cannot_be_verified[exception]` | B |
| 5675 | `tests/integration/test_preflight_temporary_files.py::test_probe_teardown_retains_files_when_its_cleanup_cannot_be_verified[unverified_return]` | B |
| 5679 | `tests/integration/test_preflight_workers.py::test_real_preflight_parent_removes_validation_workspace_after_worker_exit[success-backtest]` | B |
| 5680 | `tests/integration/test_preflight_workers.py::test_real_preflight_parent_removes_validation_workspace_after_worker_exit[success-walk_forward]` | B |
| 5681 | `tests/integration/test_preflight_workers.py::test_real_preflight_parent_removes_validation_workspace_after_worker_exit[success-optimization]` | B |
| 5682 | `tests/integration/test_preflight_workers.py::test_real_preflight_parent_removes_validation_workspace_after_worker_exit[success-comparison]` | B |
| 5683 | `tests/integration/test_preflight_workers.py::test_real_preflight_parent_removes_validation_workspace_after_worker_exit[exception-backtest]` | B |
| 5684 | `tests/integration/test_preflight_workers.py::test_real_preflight_parent_removes_validation_workspace_after_worker_exit[exception-comparison]` | B |
| 5685 | `tests/integration/test_preflight_workers.py::test_real_preflight_parent_removes_validation_workspace_after_worker_exit[timeout-backtest]` | B |
| 5686 | `tests/integration/test_preflight_workers.py::test_real_preflight_parent_removes_validation_workspace_after_worker_exit[timeout-comparison]` | B |
| 5687 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[validate-success]` | C |
| 5688 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[validate-exception]` | C |
| 5689 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[validate-system_exit]` | C |
| 5690 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[validate-timeout]` | C |
| 5691 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[dry_run-success]` | A |
| 5692 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[dry_run-exception]` | A |
| 5693 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[dry_run-system_exit]` | A |
| 5694 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[dry_run-timeout]` | A |
| 5695 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[validate-import_system_exit]` | C |
| 5696 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[validate-constructor_system_exit]` | C |
| 5697 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[validate-import_timeout]` | C |
| 5698 | `tests/integration/test_strategy_check_workers.py::test_service_survives_runtime_failure[validate-constructor_timeout]` | C |
| 5699 | `tests/integration/test_strategy_check_workers.py::test_real_mcp_survives_exit_and_accepts_repaired_revision[validate_strategy]` | D |
| 5700 | `tests/integration/test_strategy_check_workers.py::test_real_mcp_survives_exit_and_accepts_repaired_revision[dry_run_strategy]` | D |
| 5701 | `tests/integration/test_strategy_isolation.py::test_kernel_enforces_identity_files_network_and_resource_limits` | A |
| 5702 | `tests/integration/test_strategy_isolation.py::test_detached_session_is_removed_for_each_completion_path[normal]` | A |
| 5703 | `tests/integration/test_strategy_isolation.py::test_detached_session_is_removed_for_each_completion_path[failure]` | A |
| 5704 | `tests/integration/test_strategy_isolation.py::test_detached_session_is_removed_for_each_completion_path[timeout]` | A |
| 5705 | `tests/integration/test_strategy_isolation.py::test_process_limit_contains_forking_and_close_does_not_stop_another_unit` | A |
| 5706 | `tests/integration/test_strategy_isolation.py::test_lost_host_controller_still_expires_and_control_record_is_recoverable` | A |
| 5707 | `tests/integration/test_strategy_isolation.py::test_memory_exhaustion_is_a_failed_execution_with_verified_cleanup` | A |
| 5708 | `tests/integration/test_strategy_isolation.py::test_undrained_output_does_not_block_explicit_cleanup[stdout]` | A |
| 5709 | `tests/integration/test_strategy_isolation.py::test_undrained_output_does_not_block_explicit_cleanup[stderr]` | A |
| 6232 | `tests/mcp/test_strategy_contracts.py::test_invalid_frame_diagnostics_survive_typed_mcp_response[        result["signal"] = np.nan\n        return result-invalid_signal_values]` | A |
| 6233 | `tests/mcp/test_strategy_contracts.py::test_invalid_frame_diagnostics_survive_typed_mcp_response[        return result.iloc[:-1].copy()-signal_row_count_mismatch]` | A |
| 6234 | `tests/mcp/test_strategy_contracts.py::test_invalid_frame_diagnostics_survive_typed_mcp_response[        result.index = result.index + 1000\n        return result-signal_index_mismatch]` | A |
| 6235 | `tests/mcp/test_strategy_contracts.py::test_typed_lifecycle_returns_signal_evidence_and_rejects_wrong_state` | B |
| 6245 | `tests/mcp/test_strategy_contracts.py::test_checking_an_older_revision_does_not_approve_current` | B |
