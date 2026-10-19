# Tile code-capacity validation records

`observe_low_analysis_capacity_case0_target1_v1.py` is bound to actual job 265318.
The derivation changes fixed literals and byte pins only; 16 tests passed in
0.91 s. The real `running1` observation also passed source and small-artifact
snapshot checks, but the job was running and no measured profile was available.
Terminal collection remains pending; do not reuse the consumed `running1` label.

`low_partition_0_0_sample_0_terminal_acceptance_v2.json` accepts frozen-reader
metadata for job 265313: 61,440 tasks, zero recorded failures, F/exit0/run1,
04:28:24 PBS walltime. The first observer's missing-run_count failure is retained
as v1; v2 checks that field directly against actual qstat.
`low_partition_dispatch_20261019_0822.json` records the next anchor job 265317
(192 tasks, zero recorded failures, F/exit0/run1, 30 s) and running jobs 265316
and 265318, with two total requested nodes. Job 265318 is synthetic analysis
capacity, not scientific calibration evidence. Both new submissions used qsub.

`low_review_input_sources_v1/` preserves the sealed-report-bound production-plan
and BAR-row transfer entry point (15 tests each on Windows and Linux).
`low_final_case2_target2_review_inputs_v1/collection.json` records the actual scp
of a 2,362-byte plan and 330,061,028-byte row file, both matching the final report.
Its SHA256 is `c598ab0bbfa2f75452216521d3fd0a239ecc13e41fdd29a8662a6eec29a02e6d`.
No scheduler mutation or numerical recomputation was performed.

`low_final_arithmetic_sources_v1/` preserves the independent standard-library
reviewer and its 17 boundary tests (Windows 0.37 s, Linux 0.04 s).
`low_final_case2_target2_arithmetic_general_v1/` contains the actual C2 T2 review
of 67,584 rows and 352 settings: 11,968 scalar checks, maximum absolute arithmetic
difference 1.6940658945086007e-21.
This is saved-cohort arithmetic consistency, not a new decoder/trace/reference
validation or a coverage guarantee. The remaining nine conditions are pending.

`partition_final_recovery_transport_v1/` preserves 84 source files and external
evidence for assembly, final execution and sealed-result recovery.
Its manifest SHA256 is `024bb8fc40a775c59dde8d1532779047f7ee35162dd4a7a7002e9543a5419cbe`.
`low_partition_final_recovery_linux_acceptance_v1.json` records 46 passing Linux
tests using synthetic PBS and transfer responses; Windows passed 24 remote and
22 local tests.
`low_partition_final_recovery_existing_v1/verification.json` separately verifies
the reader against all 14 real C2 T2 artifacts and the current successful PBS
record, matching the previously recovered bytes and hashes.
That read-only check performs no numerical recomputation or qsub and does not
claim production recovery of the remaining nine conditions.

`low_partition_sampling_observation_20261019_0758.json` is a read-only live
observation taken at 07:57 JST: 58,016 and 30,173 marker names out of 61,440 planned
tasks per partition. Both jobs were running and neither partition summary existed.
No marker/record/raw payload was read, so these are not verified successful task
counts, scientific completion, or an ETA.

`partition_final_invocation_transport_v1/` preserves the fixed final-v3 phase
transport and all 80 source dependencies. Its 24 Windows/Linux tests reconstruct
actual-format assembly/phase records using synthetic SSH responses. Prepare,
preflight, qsub execution and seal require their accepted predecessors; ambiguous
execution is never automatically retried. Production use remains unexecuted.
The Japanese runbook is `../low_partition_final_runbook_2026-10-19_ja.md`.

`partition_final_assembly_transport_v1/` preserves the actual assembly entry and
one-shot local CLI (78 sources). Its 17 transport tests pass on Windows/Linux;
the real Linux native bootstrap/science also passes before an intentionally
invalid root is rejected. Actual incomplete C0T0 evidence is rejected by the CLI
with zero process calls and zero production intents. Production assembly/config
creation and the subsequent final invocation transport remain unexecuted.

`partition_final_config_v1/` preserves metadata entry/config construction and its
dependencies (75 sources). Its 21 Windows/Linux tests call the real final-v3
metadata, provenance, upstream, selector and resource validators with synthetic
plans/PBS and mocked native bootstrap/controller state. Rows and WSS payloads are
deferred to final compute. Actual assembly invocation and production config
generation/submission remain unexecuted.

`partition_final_upstream_v1/` preserves exact upstream job membership using the
existing final-v3 selector and PBS validators (71 source files). Synthetic-fixture
acceptance: 26 tests on Windows/Linux; failed sampling exits remain explicit.
`partition_final_resource_v1/` adds the initial serial resource policy (73 sources).
Its 13 tests pass on Windows/Linux. The 24-hour request ceiling is not an ETA or
a measured hash-time bound. Production resource confirmation, config assembly,
and final submission remain unexecuted for the nine remaining conditions.

`partition_final_assemble_inputs_v1/` preserves remote completed-input validation
(69 source files and external authorities). Its 19 tests pass on Windows/Linux,
using the real final-v3 Evidence reader with synthetic scientific readers/PBS.
No current raw payload or production final comparison was accepted by this step.

`partition_final_join_inputs_v1/` preserves the local BAR/full-trace completion
join, 66 source files and two external source-authority records. Windows checks:
6 BAR record tests, 6 trace record tests, 17 join tests; Linux: 17 join tests.
Incomplete production C0T0 inputs are rejected before any process call.
Remote final-input assembly and actual final submission remain unexecuted.

`low_partition_final_source_bridge_v2.json` records the real-cluster source bridge:
analysis (24), trace (24), and collection (42) file identities match the original
environment under final-v3 imports. One supplemental submitter is checked against
the frozen acceptance manifest. The earlier v1 rejected an overly strict subset
assumption and remains preserved. No final cohort or raw payload was accepted.

`partition_bar_collection_completion_transport_v1/` adds collector completion
acceptance (38 preserved files). Remote: 17 tests on Windows and Linux; local:
11 on Windows. Actual PBS metadata, worker inputs and counters are checked;
large rows/group/trace/anchor payloads still require the final PBS reader.
Production collector completion has not run.

`partition_bar_collection_submit_transport_v1/` adds collector preflight and
one-shot qsub transports (34 preserved files). Remote guard acceptance: 23 tests
on Windows and Linux; local transport: 14 on Windows. Ambiguous responses retain
the shared lock and evidence. No production collector submission has run.

`partition_bar_collection_prepare_transport_v1/` adds remote and local
preparation from every accepted partition completion (30 preserved files).
Remote preparation: 18 fixture tests on Windows and Linux; local: 16 on Windows.
The incomplete production C0T0 collector was rejected before any process call.
Production prepare remains unexecuted; qsub and final completion adapters remain.

`partition_bar_collection_components_v1/` preserves the BAR collector input
validator and compute worker plus their dependencies (26 files).
Windows fixture acceptance: 21 input checks and 13 worker checks; Linux: 34.
The worker calls the frozen scientific collector and records wall/CPU/RSS.
Production collection is unexecuted; preparation, qsub transport, completion
acceptance and the final-v3 evidence adapter remain to be connected.

`partition_analysis_completion_transport_v1/` preserves the tested parent
completion transport and its dependencies for partitioned BAR jobs.
Acceptance checks metadata and every group marker; full JSON/NPZ validation
remains a PBS collector responsibility. Production completion is not yet run.
`partition_trace_local_prepare_transport_v1/` preserves the independent trace
capacity preparation transport and dependencies. Remote fixture acceptance is
15 tests on both Windows and Linux; local acceptance is 12 Windows tests.
The real incomplete-sampling gate rejected preparation before SSH.
`partition_trace_submit_transport_v1/` adds the tested trace-capacity preflight
and one-shot qsub transports (28 remote fixture tests on Windows/Linux and
13 local tests on Windows). Production preparation/submission has not run.
`partition_trace_completion_transport_v1/` adds capacity completion acceptance
(16 remote fixture tests on Windows/Linux and 11 local tests on Windows).
It invokes the fixed capacity reader for two replicates; this is not completion
of the full 192-replicate audit. Production completion remains unexecuted.
Measured full-audit and audited-collection connections remain pending.
`partition_trace_full_prepare_transport_v1/` preserves the remote preparation
of the measured full audit (13 fixture tests on both Windows and Linux).
`partition_trace_full_local_prepare_transport_v1/` adds the local evidence entry
(12 Windows tests and rejection of the real incomplete input before SSH).
`partition_trace_full_submit_transport_v1/` adds the remote one-shot qsub guard
(20 fixture tests on Windows and Linux).
`partition_trace_full_local_submit_transport_v1/` adds the local submission
entry with 13 passing Windows tests.
`partition_trace_full_completion_transport_v1/` adds full audit job completion
acceptance (18 remote tests on Windows/Linux and 11 local tests on Windows).
It validates metadata, measurements, and done markers; full audit payload and
current raw trace validation remain the PBS collector's responsibility.
Production full preparation/submission has not run;
the fixture tests do not establish production-data success.
See the Japanese parent reviews and the dispatch ledger for hashes and action state.

The third low-noise formal comparison (tile72 depolarizing, p=.001) is accepted
and recovered in `low_final_case2_target2_evidence_v1/`.
`low_final_case2_target2_scientific_review_v1/` contains all 352 settings,
the fixed long-trace slice, an independent arithmetic check of 67,584 saved rows,
and the Japanese findings and limits. This brings formal low-noise comparisons
to 3/12; independent low-noise timing and raw-archive recovery remain incomplete.
`figures_low_case2_target2_v1/` contains the checked trace-length comparison.
`low_case2_three_targets_v1/` joins the accepted long-trace slices for p=.01,
.003 and .001 into a 12-row CSV and Japanese comparison with input/output hashes.
The decoder prior differs across targets; identical failure sets are not assumed.
The one-shot trace-full waiter finished successfully and submitted job265311;
do not restart it or repeat the consumed trace-full execute action.
The latest target2 readiness is r8. Collection job265314 completed successfully
in 46m23s and its completion was accepted. The four collection files were
recovered and checked (455,697,306 bytes) in `low_collection_case2_target2_evidence_v1/`.
The fixed v3 final comparison job265315 completed successfully in 47m24s.
Its seal, 14-file recovery (127,333,574 bytes), and 10,208-value arithmetic review
are complete. All target2 final actions are consumed; do not repeat them.
Case0 target0 sample partition1 was submitted as job265316 and is running alongside
partition0 job265313, with two requested nodes in total. All generator jobs for
this case/target have been submitted; collection must wait for both sample jobs.
Consult the dispatch ledger before acting.

The analysis archive exporter and dedicated PBS worker are now implemented.
`low_noise_archive_linux_acceptance_v8.json` records the 62 passing tests for
the analysis archive, worker and metadata gate; the submitter passed 10 tests.
`low_analysis_export_case2_target0_inputs_v1/` contains the externally accepted
index for all 768 groups (2,307 archive members including packaging metadata).
The separate analysis recovery stage and preflight succeeded; its qsub execution
and local payload recovery remain unperformed. Sampling recovery is also pending.
See the latest entries in `low_noise_pending_dispatch_ledger_v5_ja.md` before
using any single-use entry point. `local_orchestration_sources_v15.zip` preserves
21 source files and an index with 11 reference hashes; it contains no raw traces.

The low-noise sampling archive exporter/verifier passed 36 tests on Windows and
the isolated Linux v3 deployment. The current acceptance is
`low_noise_archive_linux_acceptance_v3.json`; v1/v2 cover earlier source versions.
The specification, source hashes, limits and pending real-data export are in
[the Japanese archive review](../tile_low_noise_archive_review_2026-10-19_ja.md).
These small tests do not constitute production archive recovery or a numerical
trace audit. The test transport's saved `.remote.py` contains the exact deployed
four-file snapshot; production export submission and analysis archive support
remain unfinished.

The subsequent metadata gate and PBS worker passed all 56 archive-related tests
on both Windows and Linux v6 (`low_noise_archive_linux_acceptance_v6.json`).
The export uses the accepted final report's complete 184,897-file hash index,
preserved in `low_sampling_export_case2_target0_inputs_v1/`; this is a metadata
extraction, not raw-data recovery. The fixed stage and successful cluster
preflight are saved in `low_sampling_export_case2_target0_stage_v1/` and
`low_sampling_export_case2_target0_preflight_v1_stdout.txt`.
The adapted one-shot submitter passed 10 additional tests and preserves the
existing lock/qsub/ambiguity state machine. Export qsub remains unexecuted.

`local_orchestration_sources_v14.zip` preserves 20 tested/source/specification
files and an index of 17 evidence references; every ZIP member was byte-checked.
Its index SHA256 is `9ac34cc82fb0e56a95d69a29a5a39a928cc7b7d32f79b4cee4c42dfaf84471c5`
and ZIP SHA256 is `e94ceab858a2ff98342417cf78a26afe05dd019b1706cc419d67d721b4e91d98`.
Restore the indexed original paths after checking hashes; snapshots are not
alternative execution locations and do not authorize repeating consumed actions.

This is a new study based on commit `d78377e`; it does not modify the preceding
46,080-trace calibration. The scientific plan is
[tile_validation_plan_2026-10-17_ja.md](../tile_validation_plan_2026-10-17_ja.md).

## Main calibration, mixing comparison and independent timing completed (2026-10-18)

The current interpretation is in the [Japanese report](../tile_validation_report_2026-10-18_ja.md),
and live phase updates are recorded in the [status document](../tile_validation_status_2026-10-17_ja.md).
Dated sections below retain the state at their stated observation time.

The first of twelve low-noise comparisons is accepted: tile72 depolarizing at
p=0.01, job 265299, with 352 settings and all 192 replicates per setting.
`low_final_case2_target0_evidence_v4/` contains the verified final metadata;
`low_final_case2_target0_scientific_review_v1/` contains the full CSV, a fixed
long-trace slice, an independent arithmetic check, and a Japanese interpretation.
The finite WSS interval is not an exact point reference, and the results do not
establish nominal coverage or convergence.
`figures_low_case2_target0_v1/` provides PNG/SVG plots, the 12 saved input rows,
provenance, and a Japanese caption for the fixed cross-chain trace-length slice.
Its bands describe finite-reference sensitivity and containment/intersection,
not confidence bands or independently replicated trace-length comparisons.
The subsequent selector/evaluation portability fixes passed 307 fixture tests
on both Windows and Linux. Their binding is
`low_noise_timing_portability_source_binding_v1.json`, and exact sources and
test harnesses are preserved in `local_orchestration_sources_v12.zip`.
The failed harness attempts remain recorded; no formal low-noise timing
selection or timing job was submitted as part of that acceptance.

`final_reaggregation_case{0,1,2,3}_evidence_v1/` contains the verified final
reports for all four cases, including every planned 192-replicate cohort.
The descriptive scientific comparison and its reproducible script are
`final_reaggregation_four_case_scientific_summary_v1{.json,_ja.md}` and
`summarize_final_reaggregation_four_cases_v1.py`.
The result does not establish nominal coverage or convergence.
`figures_main_calibration_v1/` contains a reproducible PNG/SVG comparison of
the fixed ZH/rejection slice, its 12-row CSV/JSON, Japanese caption and input
hashes. The plotted coverage uses the finite MC reference point; containment
and intersection with the reference interval remain separate saved quantities.

`mc_timing_main_evidence_v1/` contains the verified 1,536-task independent MC
benchmark. `BAR_TIMING_PREPARATION_v1_ja.md` records the fixed-policy BAR
candidates; these are not recommended settings. Their additional seed census
completed as job 265253 (F/exit 0), with evidence in `bar_seed_census_evidence_v1/`.
All 3,963,562 planned entries across 56 namespaces were checked, including stages
140/141, with no unexpected collisions or unchecked entries. This does not prove
statistical independence of random streams.
All four BAR timing capacities completed and were independently checked.
Independent main cases 0, 1, 2 and 3 completed as jobs 265263, 265266, 265267 and 265268;
each has 384 point estimates and intervals, with no failed or unavailable tasks.
Their recovered files and saved chain metadata were independently checked in
`bar_main_case{0,1,2,3}_evidence_v1/`. These artifact checks alone do not establish achieved precision.
The exact parent invocations and receipts are `bar_main_caseN_{preflight,submission}_v1_*`.
The formal assessment completed as job 265277 and was recovered in
`main_timing_report_result_evidence_v1/`. The independent scientific review is
`main_timing_scientific_review_v1/`: all eight conditions retain 192 replicates,
and only three meet the finite-reference precision rule for both methods.
Their mean task wall MC/BAR ratios are 0.0208–0.0455; the other five ratios remain
null. Host differences are uncorrected, and precision acceptance does not imply
nominal interval coverage or convergence.
`timing_mc_achieved_precision_v1{.json,_ja.md}` and `reassess_mc_timing_summary_v1.py`
reassess the fixed MC cohort: four conditions are empirically within target, two
above, and two reference-sensitive. The last four retain null time ratios under
the fixed rule, independently of BAR's outcome. No threshold, seed or cohort was changed.
These timing manifests cover the main physical error rates only; independent
low-noise timing remains separate work and is outside the present seed census.

## Local orchestration source snapshots

`local_orchestration_sources_v1/index.json` records immutable copies and existing
artifact references for local orchestration helpers, including helpers whose
original `output/` paths are ignored by Git. The associated Japanese README
describes restoration to the original paths without overwriting changed files.
Accepted source hashes, observed current copies without established historical
identity, and superseded implementations are explicitly distinguished.
Saved remote scripts, fixed inputs and receipts remain the evidence for actual
past submissions; a current helper snapshot does not establish its past identity.
`local_orchestration_sources_v2_main_report/index.json` adds the accepted Windows
remote-path fix (`d7048777...`) and its runbook as a separate immutable delta.
The superseded `072d2359...` copy remains in v1 for historical inspection.
`local_orchestration_sources_v3/index.json` adds the independently accepted staged
readiness builder (`9021c0d...`) and selector parent wrapper v2 (`70554a1...`),
with their tests, contracts, CLI forms and pinned review evidence.
Its seven source snapshots and seven existing references preserve v1/v2 unchanged;
`local_orchestration_sources_v3.zip` and the separate verification record bind
the archived and extracted bytes. No helper, new test, remote operation or qsub
was executed during preservation, and the unaccepted final WSS wrapper is excluded.
`local_orchestration_sources_v4/index.json` subsequently adds the accepted final
WSS parent wrapper v3 (`3a2a82ab...`), its test/spec and pinned review/runbook.
Its formal scope is three staged conditions plus nine partitioned conditions;
old single inputs remain unsupported and explicitly rejected in formal use.
The v4 archive has three snapshots and four existing references, with actual
extraction byte checks recorded separately; v1/v2/v3 remain unchanged.
Unaccepted copy-wrapper v2 and readiness revisions are outside this delta.
`local_orchestration_sources_v5/index.json` subsequently adds the accepted v2
copy, staged-phase and readiness entries, four tests and the source-origin contract.
Its eight snapshots and eight existing references retain the old three entries
and the old prepare-failure evidence; all v1–v4 files remain unchanged.
The pinned independent 142-test acceptance and source-only bindings check are
historical evidence, not rerun during preservation. The v5 ZIP and separate
verification record confirm actual extraction and byte equality for all ten
archive members. No helper, new test, remote operation or qsub was executed.
`local_orchestration_sources_v6/index.json` adds the independently accepted
readiness builder v3 (`4bf1412f...`), its tests/contract and an observed CLI note.
It also preserves two current main-report parent one-offs as observed snapshots,
without claiming their historical source identity. Separate references bind the
saved prepare/preflight/submit programs, intents and receipts to accepted inputs
and previously archived execution sources. The seven snapshots and 39 references
exclude the final collector under revision. Actual extraction verified all nine
archive members; all v1–v5 files and original inputs remained unchanged, with no
helper execution, new tests, remote operation or qsub during preservation.
`local_orchestration_sources_v7/index.json` adds the accepted main timing-report
collector (`7219ab0d...`), test and specification as three snapshots, with 23
references to independent acceptance and actual job-265277 recovery evidence.
All 15 transferred metadata-file hashes and five extracted archive members were
verified. No raw dataset was copied, and v1–v6 and original evidence remain
unchanged. Preservation did not rerun the collector, tests, remote calls or qsub.
`local_orchestration_sources_v8/index.json` preserves eleven case-2 target-1/2
entry, test and specification files. Its twelve archive members were byte-checked.
The snapshot retains its original candidate label; subsequent parent review is
`low_noise_case2_entries_parent_review_v1_ja.md`, and real target-1 authority and
copy submission are recorded separately.
`local_orchestration_sources_v9/index.json` preserves three additional ignored
helper/test files with eighteen evidence references. Its four archive members
and all source/reference hashes were checked. The final config assembler was
syntax-checked but remained unexecuted when this snapshot was saved; the snapshot
does not imply completed WSS comparison or scientific acceptance.

All twelve low-noise sampling capacity jobs completed and their 1,240 task artifacts were verified.
Individual terminal evidence is `low_sampling_capacity_C_T_terminal_v1.json`.
The complete resource-gate table is `low_sampling_capacity_all12_summary_v1_ja.md`.
The three tile72-depolarizing production plans are prepared in
`low_sampling_production_2_T_preparation_v1.json`; case 2 / targets 0 and 1
production completed as jobs 265259 and 265281. Their complete saved summary
task censuses were checked; target 2 is running as job 265287.
Other conditions requiring more than the single-job wall limit use the separate
accepted partition implementation and prepared plans, without changing the fixed
tasks; their nine anchor and seventeen sample jobs remain unsubmitted.
As of 23:12 JST, target-0 collection 265284 and target-1 verified copy 265286
completed successfully. Target-1 BAR analysis was submitted as job 265290.
Target-0 final comparison 265288 failed before scientific computation because
persisted device IDs differed between login and compute hosts. Diagnostic job
265289 verified that all 141 hashes matched; only device IDs differed.
`low_final_case2_target0_identity_failure_evidence_v2/collection.json` preserves
the failed job and diagnostic evidence. The isolated v2 wrapper passed 82 local
and 82 Linux tests. Its new production config, prepare and preflight completed;
qsub is pending an available node. `low_final_cross_host_identity_acceptance_v2_ja.md`
records the boundaries and pins. `local_orchestration_sources_v10/` preserves
the three ignored source/test/deployment files and eighteen evidence references.
Low-noise BAR/WSS comparisons and independent timing remain incomplete.

`low_collection_case2_target0_evidence_v1/` contains the recovered target-0
sampling plan, complete 67,584-row collection, input evidence and producer
completion: 269,835,386 bytes across four files. `collection_verification.json`
binds the transferred bytes to the previously accepted producer hashes and stable
terminal PBS observations. `local_census.json` verifies all 352 settings with
192 replicates each and 768 groups, without filtering or recalculating statistics.
The source trace payloads remain in the recorded cluster roots; this recovery
does not claim a complete local trace archive or a completed WSS comparison.

The WSS raw/audit archive is fully recovered in `weight_reference_recovered_v1/`;
`weight_reference_recovery_terminal_validation_v1.json` binds all 71,904 members
to audited inputs, source/runtime, the export job, and transferred bytes.
Mixing-inventory capacity jobs 265255–265258 and full jobs 265271–265274 completed.
`mixing_full_collection_index_v1.json` binds all 48 recovered files, and
`mixing_comparison_four_case_v1/` contains the complete saved-cohort comparison.
Undefined diagnostics and flagged cohorts remain in the denominators; these
diagnostics do not prove ergodicity or convergence.

## All main archives recovered; final reaggregation started (2026-10-18 15:33 JST)

`production_analysis_recovery_case0_20261018-v2-tile-case0-analysis-recovery.json`
and `sampling_case2_collection_stage_binding_v1.json` complete recovery of all four
main sampling/analysis archives. `main_mc_wss_summary_comparison_v1.json` records
the four main MC/WSS interval comparisons without changing the primary reference.
Final reaggregation case 1 (265236) completed with exit 0; output verification is
in progress. Case 3 (265238) and main MC timing (265237) are running.
Preparation records v1/v2/v3 bind all four final reaggregation plans.

`low_sampling_capacity_0_0_terminal_v1.json` records successful low-noise capacity
job 265235 and the existing full-job resource rejection: 31h30m exceeds 24h.
The full fixed cohort is retained; a partition specification with explicit
multiple-job evidence and downstream audit compatibility is being reviewed.

## Timing and low-noise capacity started (2026-10-18 15:26 JST)

`mc_timing_capacity_submission_v1_stdout.txt` records qsub 265234 for the fixed
stage-122 cohort (768 tasks, 5,179,392 trials).
`low_sampling_capacity_0_0_submission_v1_stdout.txt` records qsub 265235 for
tile72 bit-flip at target p=0.01 (80 sampling tasks and two anchors).
Both are capacity measurements, not completed full-cohort scientific validation.
The initial limits are respectively 1 node/96 CPU/32 GB/30 minutes and
1 node/96 CPU/340 GB/24 hours; these limits do not predict completion time.
The two jobs were confirmed running. Exports 265231 and 265232 had completed
successfully and their local transfer/verification was still underway.

## Full trace audits and WSS audit completed (2026-10-18 15:22 JST)

`main_trace_audit_completion_v1.json` binds all eight capacity/full jobs and the
four complete 768-group cohorts to exact recovered summaries, native evidence,
scripts, and selected PBS fields in `trace_audit_evidence_v1/`.
Full audits cover 190,464 compact traces and 7,747,584 saved checkpoints;
all four jobs report zero audit failures. `summarize_main_trace_audits_v1.py`
reproduces the metadata aggregation. Full group payload binding to final BAR
results remains a subsequent adapter step, not a claim made by recovery.

`seed_census_evidence_v1/REPORT_ja.md` records completed job 265220, all
3,855,274 planned entries checked, zero unexpected collisions, and 8,448
prespecified shared entries. Timing stages 140/141 remain reserved and unenumerated.
`weight_reference_summary_v1.json` and
`weight_reference_audit_summary_v1.json`, with their terminal validation records,
preserve all 16 WSS conditions and the independent raw-draw/count audit of
97,857,608 trials. Only fixed checkpoint labels were re-decoded; neither full
label re-decoding nor nominal coverage is claimed.

Jobs 265231 and 265232 export the remaining case-0 analysis and case-2 sampling
archives. `low_analysis_*_v10.*` preserves deployment and 46 passing Linux
acceptance tests for the new diagnostic inventory and final reaggregation runner.
Final scientific reaggregation, independent timing, and low-noise production are
still unfinished.

## Latest execution update (2026-10-18 15:00 JST)

All four main sampling and BAR jobs have completed. Full numerical trace audits,
independent timing, and low-noise production remain unfinished.
`sampling_case0_collection_stage_binding_v1.json` records recovery of the
7,866,545,400-byte case-0 sampling archive, verification of all 86,208 artifacts
and 258,630 files, and worker/script binding to the accepted stage.
`weight_reference_pre_submission_recheck_v1.json` records the independent
read-only check of the fixed 16-condition weight-stratified reference.
`weight_reference_submission_stdout_v1.txt` records actual qsub job 265221;
`weight_reference_submission_receipt_v1.json` and
`weight_reference_native_preflight_run_v1.json` preserve the receipt and compute-node
preflight. This job and seed census 265220 use the two permitted nodes.
No reference result or full trace audit conclusion is implied by submission.

## Completed case-3 sampling and weight pilot (2026-10-18)

`case3_weight_pilot_completion.json` records completion and its limits.
PBS evidence is in `completed_jobs_case3_weight_pilot.json` (selected job
fields only). Job 265200 completed with exit 0 in 07:16:10; all 30,720 trace
records report success. Sampling phase time was 26,049.337 seconds, excluding
the anchor phase and analysis. The archive includes 30,720 traces and 192
anchors, plus the manifest, summaries, job script and logs.

- Local archive: `output/tile_validation_recovery/production-sampling-3.tar.gz`
- Remote archive: `/home/user/workspace/mcmc4qec/20261018-tile-recovery-v1/production-sampling-3.tar.gz`
- SHA-256: `d9da46720bd4571ca2f6c8e45b5e00930f78df3d0be29e48eb66c80190cb95b8`
- Verification: `production_sampling_archive_verification-3.json`, all
  30,912 artifact identities and payload hashes checked.

This establishes transfer integrity, not numeric trace audit, mixing or BAR
coverage. Full numeric audit and analysis remain pending.

Job 265201 completed the weight pilot with exit 0 in 13 seconds (sampling
phase 8.941703 seconds). All 1,536 tasks / 721,024 trials were recovered.
`weight_pilot_audit.json` verifies raw draw regeneration, metadata, counts,
weight/alphabet and consistent failure labels for identical saved states;
it does not independently re-decode every failure label. All 192 strata have
complete resource records. The production driver's `validate_pilot` accepted
this actual audit in the pinned Linux environment. The maximum worker RSS
was 89.5625 MiB and the maximum task duration was 2.301052 seconds.

- Local archive: `output/tile_weight_pilot_recovery_v2/weight-pilot.tar.gz`
- Remote archive: `/home/user/workspace/mcmc4qec/20261018-tile-recovery-v1/weight-pilot.tar.gz`
- SHA-256: `5711d3d96c9e91624e50c795f56ed1f3c8c073324d0c2c0f3f2c802e5f7964bf`
- Transfer verification: `weight_pilot_archive_verification.json`
- Pilot summary and audit: `weight_pilot_summary.json`, `weight_pilot_audit.json`

The pilot is allocation evidence, not a logical-error reference. Independent
production allocation and omitted-tail choices are still pending.
Reproduce the raw audit with the immutable v3 bundle and pinned production
venv on Linux:

```sh
venv/bin/python cluster_scripts/audit_tile_weight_pilot.py --root /home/user/workspace/mcmc4qec/20261017-tile-weight-pilot-v2/runs/weight-pilot --output NEW_OUTPUT_PATH/weight-pilot-audit.json
```

The existing coordinator subsequently submitted case 0 as job 265209 and
case 1 as job 265210 via qsub. Their ledgers are
`production_submission-0.json` and `production_submission-1.json`; the observed
states were running/queued, requesting two nodes in total. No manual
submission competed with the running coordinator.

## Fixed independent weight-reference allocation (v4)

`weight_reference_allocation.json` freezes 16 conditions, 97,857,608 trials
and 23,938 chunks using only the audited pilot. It includes policy/source
digests, per-layer budgets, measured/unmeasured layers and design costs.
Layers with at most 4,000,000 patterns are enumerated; other layers use fixed
independent MC, with at least 4,096 and at most 4,194,304 trials per layer.
The allocation uses smoothed pilot rates solely for budgeting; pseudo-counts
and pilot samples never enter production counts or confidence intervals.
The omitted binomial mass is at most 1e-14 per condition. This absolute bound
does not guarantee relative accuracy in the lowest-noise tile288 cases.

The new immutable deployment is
`/home/user/workspace/mcmc4qec/20261018-tile-weight-reference-v4`, with the
prepared run in `runs/reference`. Linux reproduced the allocation byte for
byte. Related tests passed 30/30 in 2.94 s on Windows and 1.11 s on Linux.
The actual driver plan and login-node native preflight passed using the real
pilot audit. Evidence is saved in:

- `weight_reference_deployment_v4.json` and `weight_reference_bundle_v4.json`
- `weight_reference_manifest_v4.json`
- `weight_reference_native_preflight_plan_v4.json`
- `weight_reference_dry_run_v4.json` and `weight_reference_v4.sh`

The fixed allocation canonical digest is
`ef74585904f2e1d51a82f99de534bb6cebfb0cce38fd8ba8f6926006d2b09132`;
the production context digest is
`be77f2bcafef28ca846a3982a33eaec47a3028d43d099301b987a4f9d907b4ae`.
The request is one node, 96 CPUs, 32 GiB, 04:30:00. It is a resource
extrapolation with an unmeasured aggregation allowance, not a measured
production runtime or precision guarantee. Use v4 for future submission;
v1/v2/v3 remain immutable historical deployments.

Reproduce the allocation from the v4 bundle with its pinned venv:

```sh
venv/bin/python cluster_scripts/tile_weight_allocation.py --pilot-manifest /home/user/workspace/mcmc4qec/20261017-tile-weight-pilot-v2/runs/weight-pilot/manifest.json --pilot-audit /home/user/workspace/mcmc4qec/20261018-tile-recovery-v1/weight-pilot-audit.json --platform-profile docs/wp/data_tile_validation_2026-10-17/decoder_platform_linux.json --output NEW_OUTPUT_PATH/allocation.json
```

After the existing coordinator has stopped and a requested-node slot is free,
the guarded submitter can submit the already prepared plan via qsub:

```sh
venv/bin/python cluster_scripts/submit_tile_weight_reference.py --bundle /home/user/workspace/mcmc4qec/20261018-tile-weight-reference-v4 --root /home/user/workspace/mcmc4qec/20261018-tile-weight-reference-v4/runs/reference --execute
```

No production qsub, compute-node preflight or independent weight-reference
measurement has been performed yet.

## Completed pilot

PBS job `265196.node-PRISM` completed with exit 0 in 34 seconds.
Its 96 tasks cover tile72/288, bit-flip/depolarizing, four physical noise rates,
and six independent seeds. Each has 512 direct-MC trials, 32 paired decoder
probe errors, and four 512-step chains (ZH/ZHS × rejection/logical starts).
Initialization failures are recorded separately; no failed seed is replaced.
All task-level reproducibility and correction-equation checks passed.
This is not a coverage experiment.

`pilot_manifest.json`, `pilot_submission.json`, `pilot_summary.json`, `pilot.out`,
`bundle.json`, and `environment.lock.txt` preserve the exact inputs and evidence.
The dedicated bundle is
`/home/user/workspace/mcmc4qec/20261017-tile-study-v1`.
Its archive SHA-256 is
`267e9597597d0881a4f23d25f08a179e0f8ae419928f64ea8e9a1c02e08c2e8c`.
Full pilot artifacts were recovered to
`output/tile_validation_recovery/pilot-artifacts.tar.gz`, SHA-256
`f65c9883c722d30d0d5f92fccb3f96f73e68c02b45e50365134e9804d48fbb50`.
`pilot_archive_verification.json` verifies all 96 task identities and both payload
hashes per artifact. `pilot_decoder_counts.json` gives compact paired prior
comparisons and zero mismatches in the repeated/reversed/fresh-instance checks
on 3,072 probe errors. These finite checks do not prove universal determinism.

### Paired prior effects from the same completed pilot

`pilot_prior_effects.json` derives all 64 comparisons after checking the original
manifest, full pilot summary, compact counts and producer hash. Four-cell paired
tables separate success-to-failure, failure-to-success, both failure and both
success. The net failure-rate difference is distinct from the probability mass
of states whose failure classification changes.

At physical p=0.1, changing physical decoder prior from 0.1 to 0.0001 changes
23/192 classifications for tile288 bit-flip (16 new failures, 7 recoveries),
and 15/192 for tile288 depolarizing (7 new failures, 8 recoveries). The observed
net differences are +4.6875 and -0.5208 percentage points, respectively; small
net change does not establish an unchanged failure set. These are pilot effects,
not BAR bias or low-noise relative-error measurements. The alternative-prior
grid did not include 0.05, so it does not measure all rung comparisons against
the tile288 production target prior.

Three marginal Clopper-Pearson intervals per comparison use Bonferroni alpha
0.05/192 across the complete 64-comparison family. Their differences bound the
paired failure-rate difference, conditional on iid probe errors and fixed decoder
decisions. Shared samples across prior comparisons do not require independence
for that union bound. The simultaneous disagreement upper bound for 0/192 is
4.55%, not zero. The familywise construction is unrelated to BAR interval coverage.

Related tests passed 18/18 on Windows (1.96 s) and Linux (0.98 s).
`pilot_prior_effects_linux.json` reproduces the derivation on Linux from the same
Linux pilot. Integer counts and point effects match; 33 interval endpoints differ
by at most 6.94e-17. `prior_effect_validation.json` preserves every numeric
difference and source/input/output hashes. This postprocessing agreement does
not assert cross-platform decoder agreement. No new decoder calls or qsub jobs
were performed.

The immutable bundle is
`/home/user/workspace/mcmc4qec/20261018-tile-prior-effect-v1`, SHA-256
`f028f192d4c3302f8cf203e7a0b4201538053c99984cfefa8e618240a2a20cfd`;
`prior_effect_bundle_v1.json` records its contents.
See [the Japanese interpretation and reproduction command](../tile_decoder_prior_effect_2026-10-18_ja.md).

## Independent reference and capacity stages

Operational observation `live_jobs_2026-10-18_0356.json` records both bit-flip
production jobs running: 265209 (tile72) and 265210 (tile288, started at
03:53:40 JST on 2026-10-18), one 96-CPU node each. The actual coordinator
process was live. Trace marker counts increased over the observation interval
from 8,791 to 9,056 for tile72 and from zero to 96 for tile288. Both had 192
anchor markers and an anchor summary; neither had a completed sampling summary.
These are operational counts, not completed artifact/numerical audit results.

- Reference job `265197`: 1,248 fixed chunks, 81,788,928 total direct-MC trials;
  one 96-core node, 32 GB, two-hour limit. Reference uncertainty is retained.
  Bundle: `/home/user/workspace/mcmc4qec/20261017-tile-reference-v1`.
- Capacity job `265198`: 384 full-length timing traces, separate seed namespace;
  one 96-core node, 64 GB, 30-minute limit. These samples do not enter calibration.
  Bundle: `/home/user/workspace/mcmc4qec/20261017-tile-capacity-v1`.

Both stages completed with PBS exit 0: reference walltime 28:38 and sampling
capacity walltime 3:11. The summaries, terminal PBS records, archive verification,
and reference seed/model/count audit are saved here. All 1,248 reference and
384 sampling-capacity artifact pairs passed the recovery checks.
Recovered archives live under `output/tile_validation_recovery/`; their exact
SHA-256 values are in `reference_archive_verification.json` and
`capacity_archive_verification.json`. Production BAR coverage remains outstanding.

## Reproduction

Use the archived wheel and pinned requirements in an isolated Python 3.11 venv.
For each new deployment directory, create its plan before any submission:

```sh
venv/bin/python cluster_scripts/tile_study.py plan --root runs/tile-pilot
venv/bin/python cluster_scripts/submit_tile_pilot.py --bundle . --execute
```

After a successful pilot, the independent reference stage is:

```sh
venv/bin/python cluster_scripts/tile_reference.py plan --root runs/reference
venv/bin/python cluster_scripts/submit_tile_reference.py --bundle . --execute
```

For the capacity stage, include the completed `pilot_summary.json` at the bundle
root and run:

```sh
venv/bin/python cluster_scripts/tile_bar_study.py plan --root runs/capacity --capacity
venv/bin/python cluster_scripts/submit_tile_capacity.py --bundle . --execute
```

Submission scripts use qsub only, save the returned ID immediately, and refuse
duplicate ledgers. Capacity submission counts existing requested nodes against
the two-node limit. The production sampler retains rejected and lazy steps and
independently decodes every saved state before writing compact traces.
The separate analysis driver records uncertain-reference coverage bounds,
anchor variance, paired windows, numerical ACFs and undefined diagnostics.
Its finite tests are not a substitute for completed production calibration.

Analysis capacity uses explicitly artificial arrays in a separate manifest and
bundle; it measures the actual analysis functions at production array sizes.
It is never included in scientific calibration. The deployment provenance is
`analysis_capacity_bundle.json` and `analysis_capacity_manifest.json`.
Job `265199` completed analysis capacity: all 96 groups succeeded, PBS exit 0,
walltime 20:14, and all recovered artifacts passed hash/identity verification.
The measured production allocation is in `production_analysis_resource_plan.json`.
Submission (only when the
total requested nodes remain at most two):

```sh
venv/bin/python cluster_scripts/submit_tile_analysis_capacity.py --bundle . --execute
```

After sampling capacity completes, copy its pinned manifest and summary into a
new production bundle as `capacity_manifest.json` and `capacity_summary.json`:

```sh
venv/bin/python cluster_scripts/tile_bar_study.py plan --root runs/production
venv/bin/python cluster_scripts/submit_tile_production.py plan --bundle .
venv/bin/python cluster_scripts/submit_tile_production.py next --bundle . --execute
```

Each `next` submits one case, ranked by measured predicted duration, and refuses
to exceed two requested nodes including queued jobs. An existing ledger is never
treated as permission to restart a job. Analysis and final calibration are still
outstanding.

Production uses `/home/user/workspace/mcmc4qec/20261017-tile-production-v1`.
The fixed manifests and resource plan are `production_manifest.json`,
`production_analysis_manifest.json`, and `production_resource_plan.json`.
Case 3 was submitted as job `265200`; its ledger is
`production_submission-3.json`. Further submissions must inspect these existing
jobs and the node count first.

The additional weight-stratified work follows
[its separate specification](../tile_weight_stratified_spec_2026-10-17_ja.md).
Its allocation/timing pilot is isolated from all existing data and was submitted
as job `265201`. It covers selected weights only and cannot be used as a
logical-error reference. Complete production strata and fixed budgets must be
planned after the pilot.
Use `/home/user/workspace/mcmc4qec/20261017-tile-weight-pilot-v2` for this pilot.
Version v1 was only prepared/dry-run and is superseded before any submission by
v2, which includes a probability-boundary roundoff regression fix. The sampling
algorithm is unchanged. Both bundles retain their own immutable manifests.

```sh
venv/bin/python cluster_scripts/submit_tile_weight_pilot.py --bundle . --execute
```

Do not resubmit job `265201`; inspect its current PBS state and existing ledger.
The submission script also checks the actual queue against the two-node budget.

The raw-state allocation audit is separately deployed at
`/home/user/workspace/mcmc4qec/20261017-tile-audit-v1`.
`weight_pilot_audit_bundle.json` pins its files and archive, and
`weight_pilot_audit_validation.json` records 11 passing acceptance tests on both
Windows and the production Linux venv. This is not an audit of the queued pilot.
After job `265201` is terminal and its artifact set is complete, run:

```sh
/home/user/workspace/mcmc4qec/20261017-tile-production-v1/venv/bin/python /home/user/workspace/mcmc4qec/20261017-tile-audit-v1/cluster_scripts/audit_tile_weight_pilot.py --root /home/user/workspace/mcmc4qec/20261017-tile-weight-pilot-v2/runs/weight-pilot --output /home/user/workspace/mcmc4qec/20261017-tile-audit-v1/weight_pilot_audit.json
```

It checks all artifact identities/hashes, fixed-prior metadata, seeds, regenerated
raw draws, observed counts, and duplicate-state failure consistency. It retains
failed tasks and never produces a logical-error reference from this incomplete
weight grid. Per-layer confidence intervals are exploratory, not simultaneous.
RSS unavailable on a platform remains `null` and cannot size production memory.

The analysis controller is separately deployed at
`/home/user/workspace/mcmc4qec/20261017-tile-control-v1` (`control_bundle.json`).
It uses the production bundle's pinned venv and refuses analysis until the case's
sampling job is terminal and all planned sampling/anchor tasks are recorded.
Failed task records are retained in the subsequent analysis. Production bundle
sources and manifests were not replaced to add this controller.

## Public API workflow checks

Run from the repository root with the installed wheel or `PYTHONPATH=src`:

```sh
python examples/workflows/tile_capacity_fixed_prior.py --quick --seed 7 --out output/tile_fixed_prior_example/bit
python examples/workflows/tile_capacity_fixed_prior.py --quick --seed 7 --noise depolarizing --out output/tile_fixed_prior_example/depol72
python examples/workflows/tile_capacity_fixed_prior.py --quick --seed 7 --size 12 --initialization logical --kernel ZHS --uncertainty cross_chain --out output/tile_fixed_prior_example/bit288
python examples/workflows/tile_capacity_fixed_prior.py --quick --seed 7 --size 12 --noise depolarizing --uncertainty cross_chain --out output/tile_fixed_prior_example/depol288
python cluster_scripts/verify_tile_workflow_examples.py
```

`workflow_example_checks.json` records decoder-prior identity checks, numeric
results, the independent-reference comparison, and the output archive hash.
All four commands completed. The tile72-depolarizing short BAR interval missed
the high-budget independent reference interval; these examples are not calibrated
precision settings. They do not enter the fixed production cohorts.
These Windows examples and the Linux reference also cross native decoder
environments; a later tile288 counterexample establishes that matching version
strings and priors do not ensure identical failure decisions. The numerical
interval comparison is retained as historical data, not evidence isolating BAR
bias or poor mixing.

## Paired one-factor comparisons

`cluster_scripts/tile_comparisons.py` consumes the completed case's checked
`rows-N.jsonl`, summary and fixed analysis context. It checks every planned
condition and replicate, then enumerates all one-factor pairs. Differences are
right minus left; log ratios are log(right/left). Missing intervals count as
noncoverage, and missing estimates prohibit a full-cohort point contrast.
Available-only statistics remain explicitly labelled. Shared-reference
uncertainty is retained in the squared-error difference range.

```sh
python cluster_scripts/tile_comparisons.py --root PATH_TO_COMPLETE_PRODUCTION --case 0 --output NEW_OUTPUT_PATH/comparisons-0.json
```

Repeat for cases 1, 2 and 3 after each case's analysis completes. This separate
postprocessing does not change pinned jobs or sampling. It has not yet been run
on production results. `comparison_validation.json` records its 10 acceptance
tests and the 71-test integration result for the tile drivers;
`driver_integration_validation.txt` is the execution log. Standard errors are
descriptive, not simultaneous tests or evidence of convergence.

## Live submission coordinator

The separate coordinator bundle is
`/home/user/workspace/mcmc4qec/20261017-tile-coordinator-v1`.
`coordinator_bundle.json`, `coordinator_config.json`, and `coordinator_process.json`
pin its deployment, immutable inputs, and recorded process identity.
The Linux process was started at `2026-10-17T11:18:09Z` with PID `3756042`;
its command and liveness were verified using `ps` after launch.
Check the current process rather than treating these recorded files as liveness:

```sh
ps -p 3756042 -o pid=,etimes=,stat=,args=
/home/user/workspace/mcmc4qec/20261017-tile-production-v1/venv/bin/python /home/user/workspace/mcmc4qec/20261017-tile-coordinator-v1/cluster_scripts/tile_coordinator.py status --config /home/user/workspace/mcmc4qec/20261017-tile-coordinator-v1/runs/controller/config.json
```

Do not manually submit production cases or start a second coordinator while it
is live. It counts all own queued/running requested nodes, submits at most one job
per observation, and calls the existing qsub submitters. Sampling order remains
3, 0, 1, 2; eligible analyses follow after all sampling cases have been submitted.
It polls once per minute for at most 72 hours and does not cancel existing jobs.

`runs/controller/status.json` and `events.jsonl` retain observations and decisions.
Each submission has separate `intent-STAGE-CASE.json` and
`receipt-STAGE-CASE.json`. An unacknowledged intent stops continuation and must be
reconciled with the actual queue and production ledger before any manual retry.
Transient queue observations lead to waiting, never replacement jobs. Production
ledgers remain under the original production root. The coordinator's `finished`
state means only that these eight fixed jobs completed their checked stages;
recovery, scientific audits, low-noise work and the final report remain separate.

Local coordinator/submitter tests: 13 passed in 1.31 s.
Pinned Linux tests: 13 passed in 0.55 s.
The initial real queue observation found jobs 265200 and 265201 requesting two
nodes and correctly made no new submission.

## Structural and stabilizer-fiber audit

`structure_audit/` contains checked NPZ/JSON artifacts for all four code/noise
cases and their summary, source hash, runtime and decoder metadata. It records
rank(S)=nullity([H;L]) as 32/140/64/280 for tile72-bit, tile288-bit,
tile72-depolarizing and tile288-depolarizing. This proves only the stated
linear-map fiber property, under the assumptions in
[the support note](../tile_kernel_support_2026-10-17_ja.md), not global mixing.
Local acceptance: 4 passed in 2.23 s. Reproduce into a new output directory:

```sh
python cluster_scripts/audit_tile_structure.py --out NEW_STRUCTURE_AUDIT_DIRECTORY
```

This uses the source package with `PYTHONPATH=src` or the installed wheel.
The audit did not modify the pinned production/coordinator deployments.
The source review also identified alternating X-basis/Z-basis logical starts by
replicate parity in the depolarizing cases; retain the full 192-replicate primary
cohort and additionally report the two 96-replicate initialization strata.

The separate postprocessor `cluster_scripts/tile_initialization_strata.py`
implements these supplemental strata for cases 2 and 3. It checks the pinned
initialization/sampling source, all conditions and replicate IDs, and reproduces
every full-cohort primary summary before producing the supplementary tables.
Rejection initialization has matching even/odd seed controls, explicitly not
labelled as X/Z starts. Original replicate IDs are retained in each stratum.

```sh
python cluster_scripts/tile_initialization_strata.py --root PATH_TO_COMPLETE_PRODUCTION --case 2 --output NEW_OUTPUT_PATH/initialization-2.json
python cluster_scripts/tile_initialization_strata.py --root PATH_TO_COMPLETE_PRODUCTION --case 3 --output NEW_OUTPUT_PATH/initialization-3.json
```

`initialization_validation.json` records 6 passing acceptance tests (1.30 s),
including the actual tile72/288 initializers. It also records the updated
90-test driver integration (6.56 s), whose log is
`driver_integration_initialization_validation.txt`. The earlier 71-test log is
preserved. Production initialization-stratum reports are not yet executed.

## Completed production anchor phase, case 3

The 192 anchors of running job 265200 completed before its sampling phase.
`production_anchors-3.json` is the unmodified phase summary.
`production_anchor_archive_verification-3.json` verifies all 192 artifacts;
`production_anchor_audit-3.json` checks the recorded seeds, fixed Problem hash,
trial budgets, count/estimate/interval consistency and exact summary reproduction.
Related tests: 9 passed in 0.50 s.

Archive: `output/tile_validation_recovery/production-anchors-3.tar.gz`, SHA-256
`0c87c608a7116ea046281cb4fb1bc373568f1a46015cecee8850dc344dc011ee`.
The remote archive is under the original production bundle's
`exports/anchors-3.tar.gz`; source/manifest files were not modified.

```sh
python cluster_scripts/artifact_archive.py --archive output/tile_validation_recovery/production-anchors-3.tar.gz --manifest docs/wp/data_tile_validation_2026-10-17/production_manifest.json --stage production-anchors --case 3 --output NEW_OUTPUT_PATH/anchor-transfer-3.json
python cluster_scripts/audit_tile_anchors.py --archive output/tile_validation_recovery/production-anchors-3.tar.gz --manifest docs/wp/data_tile_validation_2026-10-17/production_manifest.json --summary docs/wp/data_tile_validation_2026-10-17/production_anchors-3.json --verification NEW_OUTPUT_PATH/anchor-transfer-3.json --output NEW_OUTPUT_PATH/anchor-audit-3.json
```

All 3,145,728 fixed trials and 743,334 failures are at physical p=.1 with a
decoder fixed to target p=.05 (sector prior 2p/3). This is not the target-p
reference. Each BAR replicate retains its own 16,384-trial anchor; the pooled
audit estimate is never substituted. No anchor has zero observed failures.
The per-replicate binomial delta log-SE term ranges from .013735 to .014397.
Anchor phase walltime is 118.14 s; summed individual direct-MC elapsed time is
10,843.90 s, not measured CPU time. Raw physical errors/full direct-MC RNG metadata
were not saved by this frozen driver; the audit states this provenance boundary.

## Planned direct-MC precision benchmark (not executed)

`direct_mc_precision_budget.json` fixes direct-MC budgets for relative RMSE .2
and .1 using the lower endpoint of the independent reference's .999 interval,
rounded up to 64 trials. This is an MSE criterion, not a confidence-interval
half-width. The plan reserves seed stage 121 and 192 new replicates per condition,
totalling 10,358,784 trials. It does not alter the running scientific cohorts.

```sh
python cluster_scripts/tile_mc_precision_budget.py --reference docs/wp/data_tile_validation_2026-10-17/reference_summary.json --output NEW_OUTPUT_PATH/direct_mc_precision_budget.json
```

Budget acceptance: 7 passed in 0.40 s, including finite binomial MSE.
The benchmark driver is implemented; driver and budget acceptance passed
14 tests in 2.38 s. Its fixed-budget runs, resource smoke, submission and runtime
comparison have not been executed. See [the precision/time protocol](../tile_time_to_accuracy_plan_2026-10-17_ja.md)
for the separate treatment of actual standalone BAR runtime, prefix extrapolation,
reference uncertainty, unavailable estimates and configurations missing the target.

`tile_mc_time_benchmark.py` records actual Result RNG/decoder/noise metadata,
construction and task walltime, MC elapsed time, and task process CPU time.
Capacity uses 96 replicates per condition in seed stage 122; production uses
192 replicates in stage 121. These samples must remain separate.
Full runs require PBS and the fixed 96-worker single-thread environment.
The current coordinator does not schedule these additional timing jobs.
Do not submit them concurrently with that coordinator without coordinating the
global two-node limit.

```sh
python cluster_scripts/tile_mc_time_benchmark.py plan --budget docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json --root NEW_CAPACITY_ROOT --capacity
python cluster_scripts/tile_mc_time_benchmark.py plan --budget docs/wp/data_tile_validation_2026-10-17/direct_mc_precision_budget.json --root NEW_BENCHMARK_ROOT
```

Plan creation is lightweight. The `run` command belongs inside a measured-resource
qsub job. A dedicated submitter has now been deployed as described below.

The immutable bundle is
`/home/user/workspace/mcmc4qec/20261017-tile-mc-timing-v1`, with archive SHA-256
`24feea91300d774c627193c497b60b83b1a4904951d294dabc8464c77861c02d`.
It uses the existing pinned production venv. Driver, budget and submitter tests
passed locally (21 tests, 2.75 s) and on Linux (21 tests, 1.69 s).
The capacity dry-run requests one 96-CPU node, 32 GB, and 30 minutes.
Both capacity and benchmark manifests are saved here, along with the dry-run
receipt. Neither cohort has been submitted or measured.

After the existing coordinator terminates, and after checking its final state
and all current user jobs, the prepared capacity submission command is:

```sh
cd /home/user/workspace/mcmc4qec/20261017-tile-mc-timing-v1
venv/bin/python cluster_scripts/submit_tile_mc_time.py --bundle . --root runs/mc-capacity --execute
```

The submitter refuses a live tile coordinator, requests exceeding two nodes,
or existing submission/intent records. It writes a durable intent before qsub;
ambiguous responses are not automatically retried. It does not establish an
atomic lock with unrelated external submitters, so do not launch another
submission process concurrently. Benchmark submission additionally requires
the complete successful capacity summary from the same runtime:

```sh
venv/bin/python cluster_scripts/submit_tile_mc_time.py --bundle . --root runs/mc-benchmark --capacity-root runs/mc-capacity --execute
```

The capacity samples remain excluded from scientific benchmark replicates.
Predicted resource use is not measured benchmark runtime or achieved precision.

## Production archive recovery checks

`artifact_archive.py` now accepts `production-sampling` (all traces and anchors
for one explicit case) and `production-analysis` (all analysis groups for that
case). Sampling archives must include `manifest.json`; analysis archives must
also include `analysis_manifest.json` and `reference_summary.json`.
Archive member names are relative to the production run directory.
Each artifact includes its `.npz`, `.json`, and `.done.json` files, including
recorded failures. No task may be omitted because it failed a diagnostic.

```sh
python cluster_scripts/artifact_archive.py --archive RECOVERED_SAMPLE_CASE_3.tar.gz --manifest docs/wp/data_tile_validation_2026-10-17/production_manifest.json --stage production-sampling --case 3 --output NEW_OUTPUT_PATH/sample-transfer-3.json
python cluster_scripts/artifact_archive.py --archive RECOVERED_ANALYSIS_CASE_3.tar.gz --manifest docs/wp/data_tile_validation_2026-10-17/production_manifest.json --analysis-manifest docs/wp/data_tile_validation_2026-10-17/production_analysis_manifest.json --stage production-analysis --case 3 --output NEW_OUTPUT_PATH/analysis-transfer-3.json
```

Acceptance: 13 passed in 1.32 s, including the existing anchor audit.
Expected task sets were also compared with the actual frozen sampling and
analysis generators using the pinned production manifests: 86,016 / 30,720 /
43,008 / 30,720 traces for cases 0–3, plus 192 anchors and 768 analysis groups
per case. `production_archive_validation.json` records the checked sources.
Complete production archives have not yet been recovered or verified.
This verifies transfer integrity and study identity, not numerical trace
correctness, independent re-decoding, mixing, or nominal coverage.

## Numeric trace audit driver (full cohort not executed)

`audit_tile_traces.py` checks every saved compact value's shape, dtype and range,
recorded seeds, fixed model/decoder/configuration, initialization and proposal
counts. Every stored physical checkpoint and initial state is decoded again;
checkpoint weight, syndrome weight and residual logical sector must reproduce
the corresponding compact values. Logical initialization uses the original
replicate/chain basis index, including the depolarizing X/Z parity split.

Missing trace artifacts stop the audit. Recorded sampling failures are retained
as failures, not omitted. Resuming an audited group rechecks the source artifact
markers and payload hashes before reusing its audit record.

Acceptance: 26 passed in 5.01 s across trace audit, sampler and archive tests.
Tests use actual short traces for all four code/noise cases and deliberate
metadata/array corruptions. `trace_audit_validation.json` pins checked sources.
The initial driver was deployed for the two-trace Linux check described below.
The subsequent native-environment guard is deployed separately; full production
cohort audits have not run.
Its full-cohort command requires a 96-worker qsub job with single-thread BLAS:

```sh
python cluster_scripts/audit_tile_traces.py --source-root PINNED_PRODUCTION_RUN --root NEW_AUDIT_ROOT_CASE_3 --case 3 --workers 96 --platform-profile docs/wp/data_tile_validation_2026-10-17/decoder_platform_linux.json --platform-fixture docs/wp/data_tile_validation_2026-10-17/decoder_platform_fixture.json
```

This command belongs inside a separately sized PBS job after sampling completes;
it must obey the existing coordinator and two-node submission constraints.
The audit uses the same BP-OSD implementation. It does not independently certify
decoder correctness, replay all MCMC random draws, or recover unsaved physical
states between checkpoints. It does not prove mixing or interval coverage.

## Observed native decoder environment discrepancy

`decoder_platform_fixture.json` preserves one weight-24 tile288 depolarizing
checkpoint from task `[3,0,0,0,4,0]`, saved index 8000. The Linux decoder yields
residual sector 94 (failure), while Windows yields 0 (success), with the same
package versions, fixed priors/settings, source hash and Problem metadata hash.
Both use one thread. Ten repeated calls and four fresh decoder instances agree
within each environment. Full records include native ldpc binary hashes:
`decoder_platform_linux.json` and `decoder_platform_windows.json`.
The mechanism and error-rate impact have not been isolated.
The independent reference venv's native ldpc binary hashes and platform match
the production profile (`reference_native_environment.json`). Version metadata
alone was insufficient to detect the Windows/Linux difference.

```sh
python cluster_scripts/probe_tile_decoder_platform.py --fixture docs/wp/data_tile_validation_2026-10-17/decoder_platform_fixture.json --output NEW_PLATFORM_OUTPUT.json
```

The generating Linux environment passed the two selected trace audits
(36,000 compact entries, 38 checkpoints and two initial states), recorded in
`production_trace_checkpoint_smoke_linux.json`. Raw selected trace artifacts
were copied to `output/tile_trace_audit_smoke_v1/` and retain their original
identities and hashes. This is not a random cohort or full-cohort audit.
See [the interpretation and limits](../tile_decoder_platform_2026-10-17_ja.md).

The updated full-cohort trace auditor requires the saved Linux profile and
fixture, checks native hashes/environment and reproduces the fixture decisions
before processing traces. Its related acceptance is 27 passed in 5.38 s;
`trace_audit_platform_validation.json` records this revision separately from
the original 26-test acceptance.

The guarded revision is now deployed at
`/home/user/workspace/mcmc4qec/20261017-tile-trace-audit-v1` (bundle SHA-256
`730166cfbb1dda4ebcd29de83c9e01f1bdca03300db4a87713e8a1c2397376e0`).
Linux acceptance passed 27 tests in 1.92 s. The actual native profile and
fixture preflight passed on the login node using the pinned production venv;
`trace_audit_native_preflight.json` records the full observation, and
`trace_audit_deployment.json` records the deployment.
These login-node observations do not establish identical compute-node OS/CPU
behavior. The full audit must pass its own preflight inside the qsub job.
Full-cohort resource measurement and execution remain unperformed.

### Standalone BAR timing driver (2026-10-18, v1)

`tile_bar_time_benchmark.py` runs one explicitly selected calibration setting
per fresh replicate, with separate anchor, initialization, sampling and bootstrap
seeds. Benchmark stage 140 uses 192 replicates; capacity stage 141 uses 96.
All eight case/precision choices must be represented as selected or unmet.
The settings input records selection-evidence hashes and must stay within the
calibration grid. These hashes do not by themselves certify selection or accuracy.
Actual choices and corresponding scientific manifests have not been fixed.

The driver uses the target-prior decoder across the ladder, generates a new
16,384-trial anchor, and executes exactly the selected burn plus saved length.
It retains rejections and verifies every saved state's failure while compacting.
Logical initialization retains the original maximum-chain stride, including
the X/Z assignment when fewer chains are selected. Failed chains remain recorded;
zero-failure anchors produce unavailable estimates rather than asserted zeros.
Construction, anchor, initialization, sampling, compact validation and estimation
each have separate wall/CPU clocks. Task total includes validation work and
excludes artifact writes; phase time includes worker startup and persistence.
Cached results are counted separately and their historical task times cannot be
interpreted as new execution time. No long-trace time is prorated to a prefix.

Acceptance used actual short traces for all four code/noise cases, public
same-seed sampler replay, fixed-prior metadata, burn removal, both uncertainty
methods, independent anchor variance, failed-task retention and native guards.
Related tests passed 32/32 on Windows (9.46 s) and Linux (7.57 s).
The immutable bundle is
`/home/user/workspace/mcmc4qec/20261018-tile-bar-timing-v1`, SHA-256
`d7739d18c30e8870ac55cf99aa46950c9e8497cb73c15548d2003f7324775125`.
The login native check passed. Evidence is in `bar_timing_deployment_v1.json`,
`bar_timing_bundle_v1.json` and `bar_timing_native_preflight_v1.json`.
Actual setting selection, compute-node verification, capacity measurements,
the dedicated guarded qsub submitter and independent accuracy/time comparisons
remain pending. No timing job was submitted.

### Full-cohort empirical relative precision assessment

`tile_precision_assessment.py` adds a separate report for complete BAR rows.
It verifies the sampling/analysis/reference/summary/raw-row hash bindings,
the full condition grid and every fixed replicate, and reconstructs the saved
absolute-error summaries before assessing relative precision. It does not modify
the deployed BAR analysis or existing results.

For estimates `x_i` and candidate reference probability `P`, empirical relative
RMSE is `sqrt(mean((x_i/P - 1)^2))`. Over a positive reference interval its
minimum occurs at `mean(x_i^2)/mean(x_i)`, clipped to the interval, and its maximum
is at an endpoint. Absolute-RMSE bounds divided by the reference point do not
provide these bounds. Scaled moments and `hypot` avoid squaring tiny unscaled
probabilities. Missing point estimates, a zero reference lower bound or numerical
overflow cannot qualify as an empirical precision pass. Interval availability
and diagnostic flags stay in the original cohort denominator and remain separate
from point-estimate precision.

Threshold classifications (`empirical_within_target`, `empirical_above_target`,
`reference_sensitive`, or explicitly unassessable) describe this finite cohort.
They are not confidence intervals for population RMSE or guarantees of nominal
coverage, and do not make an automatic recommendation.

Related tests passed 26/26 on Windows (0.85 s) and Linux (0.19 s), including
interior extrema, scale invariance down to 1e-300, missing data, reference-zero
boundaries, numeric overflow and persisted-artifact mismatch refusal.
The immutable deployment is
`/home/user/workspace/mcmc4qec/20261018-tile-precision-assessment-v1`, SHA-256
`bf5dbc0f02183f4dfe0603e3170f646974f817db55d3b842767d2746b988245d`.
Provenance is in `precision_assessment_deployment_v1.json` and
`precision_assessment_bundle_v1.json`.
Production BAR assessment and setting selection have not run.

After a complete production BAR case summary is available:

```sh
cd /home/user/workspace/mcmc4qec/20261018-tile-precision-assessment-v1
venv/bin/python cluster_scripts/tile_precision_assessment.py --root /home/user/workspace/mcmc4qec/20261017-tile-production-v1/runs/production --case 3 --output runs/precision-3.json
```

### Measured audit wrapper prepared (2026-10-18, v2)

`tile_trace_audit_run.py` adds separate fixed capacity (96 groups: both kernels,
both initializations, replicates 0--23) and full (768 groups) runs. It preserves
the existing numerical auditor and binds the observed compute-node native
profile, hostname and PBS ID to the summary. Group wall/CPU time and peak RSS
are persisted. Failed audits remain recorded and prevent using capacity as a
resource basis. Sampling failures remain a separate count. Unordered worker
completion is sorted before verifying the complete fixed cohort.

`submit_tile_trace_audit.py` requires complete sampling/anchor summaries and a
terminal sampling PBS job, refuses a live tile coordinator or more than two
requested nodes, and records an exclusive intent before qsub. An ambiguous
response is never retried automatically. Capacity requests 96 CPUs, 32 GiB and
30 minutes; full resources require completed, hash-verified capacity records.
The initial capacity request and measured extrapolation do not guarantee runtime.

The immutable deployment is
`/home/user/workspace/mcmc4qec/20261018-tile-trace-audit-v2`, archive SHA-256
`8531c174f3e67917a2233b9552a5882692aed252d1e447ebd11b91d050ef611e`.
Related tests passed 41/41 on Windows (7.36 s) and Linux (2.35 s).
Real case-3 plans exist at `runs/capacity-3` and `runs/full-3`; the capacity
dry-run accepted the completed production summaries. The login-node native
profile matches the pinned Linux profile. Neither capacity nor full was
submitted, and compute-node native verification remains pending.

Evidence files are `trace_audit_execution_deployment_v2.json`,
`trace_audit_bundle_v2.json`, `trace_audit_capacity_manifest_v2_case3.json`,
`trace_audit_full_manifest_v2_case3.json`,
`trace_audit_capacity_dry_run_v2_case3.json`, `trace_audit_capacity_v2_case3.sh`
and `trace_audit_native_preflight_v2.json`.

Only after the current coordinator stops and a node slot is available:

```sh
cd /home/user/workspace/mcmc4qec/20261018-tile-trace-audit-v2
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
venv/bin/python cluster_scripts/submit_tile_trace_audit.py --bundle "$PWD" --root runs/capacity-3 --source-root /home/user/workspace/mcmc4qec/20261017-tile-production-v1/runs/production --execute
# After terminal successful capacity; inspect its actual records first:
venv/bin/python cluster_scripts/submit_tile_trace_audit.py --bundle "$PWD" --root runs/full-3 --capacity-root runs/capacity-3 --source-root /home/user/workspace/mcmc4qec/20261017-tile-production-v1/runs/production --execute
```

The same wrapper can plan other cases after their sampling completes. Capacity
timing is not a BAR efficiency benchmark, and checkpoint auditing does not
prove convergence, full trajectory correctness or nominal coverage.

## Weight-reference chunk primitives (production not executed)

`tile_weight_reference.py` implements fixed-budget enumeration/independent-MC
chunks and per-condition aggregation. MC uses seed stage 130, separate from
pilot stage 110 and all prior study stages. Each condition must include every
weight from zero to its cutoff; enumeration budgets must equal full class sizes.
Chunks retain raw states and failure masks. Aggregation regenerates their
declared random draws or enumeration ranges, checks metadata and counts, and
refuses missing/extra/duplicate chunks. Recorded failed chunks make the
condition's reference unavailable without reducing the planned budget.

Successful conditions use the existing CP/Bonferroni intervals and explicit
omitted-mass upper bound. A partial point estimate is not the full error rate
when the tail is material; zero MC failures do not establish an exact zero.

Acceptance: 14 passed in 16.15 s, including actual small chunks for all four
code/noise cases, split complete weight-1 enumeration, corruptions and failures.
`weight_reference_chunk_validation.json` pins these sources.
No production allocation or reference has been generated. The planner records
pilot/profile digests but does not itself authenticate the complete pilot audit
or authorize execution. A production driver must verify the completed pilot,
perform native preflight, fix the actual allocation and resources, and submit
through qsub within the global two-node budget. Actual production preparation
and execution remain unperformed.

`tile_weight_reference_driver.py` now supplies the `plan`/`run` workflow.
It verifies the pinned pilot manifest, all 1,536 audited tasks and 192 strata,
successful audit flags, counts, source hashes and measured resource fields.
The allocation must cover the pilot's sixteen code/prior pairs and bind the
audit and native profile by canonical digest. `plan` copies all five inputs
and freezes their digests plus the driver and chunk runtime/source hashes.
Both commands perform native-profile/fixture preflight. `run` additionally
requires PBS, 96 workers and single-thread BLAS. It retains failed chunks and
unavailable conditions, writing summaries before reporting failure.

The allocation JSON has `conditions`, `chunk_size`, `pilot_audit_digest` and
`platform_profile_digest`. Each condition supplies `case`,
`physical_decoder_prior` and contiguous `layers` of `{w, mode, trials}`.
Actual trial budgets have not been selected; do not replace the pilot audit
with the synthetic acceptance fixtures.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
python cluster_scripts/tile_weight_reference_driver.py plan --root NEW_REFERENCE_ROOT --allocation FIXED_ALLOCATION.json --pilot-manifest PINNED_PILOT_MANIFEST.json --pilot-audit COMPLETED_PILOT_AUDIT.json --platform-profile docs/wp/data_tile_validation_2026-10-17/decoder_platform_linux.json --platform-fixture docs/wp/data_tile_validation_2026-10-17/decoder_platform_fixture.json
# Only inside a resource-checked qsub job:
python cluster_scripts/tile_weight_reference_driver.py run --root NEW_REFERENCE_ROOT --workers 96
```

Related driver/chunk acceptance: 20 passed in 21.99 s.
`weight_reference_driver_validation.json` records the checked sources.
Driver orchestration tests use synthetic audit reports and mocked workers;
chunk tests use actual small tile samples. No completed real pilot, production
allocation, resource sizing, submission or reference result is implied by these
tests. A suitable qsub submitter and actual production preparation remain pending.

The reference driver is now deployed at
`/home/user/workspace/mcmc4qec/20261017-tile-weight-reference-v1` with bundle
SHA-256 `67c58ff3c6adcaa1c020ad9ef35444c89c7b9d7227fb1a279b4d97ad25fc2a41`.
Linux driver/chunk/stratification acceptance passed 27 tests in 6.66 s.
The login-node native preflight using the pinned production venv also passed;
see `weight_reference_native_preflight.json` and
`weight_reference_deployment.json`. This does not replace compute-node
preflight or the still-pending real pilot audit, allocation, resource sizing,
qsub submission and production reference measurement.

MC timing v2 pins the native profile and discrepancy fixture, rejects altered
inputs or mismatched decoding before starting workers, and persists the actual
preflight separately from phase timing. Related acceptance passed 24 tests in
9.34 s on Windows and 1.75 s on Linux; orchestration tests use mocked probes and
workers, while the existing small direct-MC tests use real decoders.
The actual login-node preflight is in `mc_timing_native_preflight_v2.json`.
The capacity/benchmark manifests and capacity dry-run are recorded as
`mc_timing_capacity_manifest_v2.json`, `mc_timing_benchmark_manifest_v2.json`
and `mc_timing_dry_run_v2.json`; deployment details are in
`mc_timing_deployment_v2.json`. The v1 bundle is retained unchanged but future
submission must use v2. No v2 qsub, compute-node preflight or timing measurement
has been performed.

Weight-reference v2 persists separate plan/run native-preflight evidence with
the actual profile, hostname, PBS job ID, elapsed time and manifest digest.
Both chunk and condition summaries bind the run evidence by file hash.
Acceptance passed 27 tests in 17.24 s on Windows and 6.87 s on Linux; the driver
orchestration acceptance uses mocked probes/workers. The actual login-node
profile check is `weight_reference_native_preflight_v2.json`, with deployment
and bundle records in `weight_reference_deployment_v2.json` and
`weight_reference_bundle_v2.json`. Use the immutable v2 deployment for future
production preparation. No real-pilot-based plan/run, production allocation,
compute-node preflight, resource sizing or qsub has been performed.

The local `submit_tile_weight_reference.py` adds pilot-based resource
extrapolation and guarded qsub submission. Related Windows acceptance passed
39 tests in 10.43 s; resource/submission tests use synthetic pilot evidence and
mocked qsub. See `weight_reference_submit_validation.json` for source hashes.
No real-pilot resource estimate, Linux deployment of this submitter, or actual
submission has been performed. Existing immutable v2 deployments are unchanged.

The submitter was subsequently deployed in the new immutable
`20261018-tile-weight-reference-v3` bundle. Linux acceptance passed the same
39 tests in 7.24 s, and the actual login-node native probe matched the pinned
Linux profile. See `weight_reference_deployment_v3.json`,
`weight_reference_bundle_v3.json` and `weight_reference_native_preflight_v3.json`.
Use v3 for future reference preparation and submission; v1/v2 remain unchanged.
Real-pilot allocation, resource sizing, compute-node preflight and qsub are
still pending.


## Decoder stage observation, 2026-10-18

Windows and pinned Linux final BP LLRs/hard decisions and OSD-0 agree
on the selected platform counterexample. X OSD-W corrections differ
by 26 bits and logical predictions by 5 bits. Both X corrections have
weight 22 and satisfy the syndrome. Z results agree.
This is one selected state, not an error-rate comparison.
Raw Cython source hashes differ only by CRLF/LF normalization.
The published 2.4.1 sdist was hash-checked for source inspection only;
its missing sort.hpp prevents inspecting that dependency in this archive.
No native binary was rebuilt or installed.

See decoder_stages_windows.json, decoder_stages_linux.json,
decoder_stages_comparison.json, decoder_cython_sources_windows.json,
decoder_cython_sources_linux.json and decoder_osd_source_provenance.json.
decoder_stages_validation.json binds input/source hashes, deployment
and acceptance results (3 passed, Windows 2.47 s / Linux 1.72 s).
decoder_stages_bundle_v1.json records the immutable deployment.
live_jobs_2026-10-18_0408.json records process/PBS status at 04:08:59 JST.


## Standalone BAR timing deployment v2

bar_timing_deployment_v2.json records the case-partitioned driver, new guarded
qsub submitter, source hashes and 42 passing tests on Windows (12.47 s) and
Linux (8.49 s). bar_timing_bundle_v2.json records the immutable archive.
Resource and qsub acceptance uses synthetic capacity and mocked submission;
related short sampler acceptance uses real tile decoders.
bar_timing_native_preflight_v2.json records the actual pinned login profile.
bar_timing_unpinned_probe_v2.json records a manual probe rejected without
explicit thread exports; its canonical difference is only thread_environment.
No settings have been selected and no real timing plan, capacity or qsub
execution has occurred. Use v2 for future selected-setting timing preparation.
bar_timing_v2_live_jobs.json records the live coordinator and two running
production jobs at 2026-10-18 04:15:09 JST.


## Independent timing candidate selection

timing_selection_deployment_v1.json and timing_selection_bundle_v1.json record
the fixed selection rule, source hashes, immutable deployment and 30 passing
tests (Windows 2.14 s / Linux 0.99 s).
Tests use synthetic full cohorts and persisted raw rows on a reduced grid.
The selector recomputes every calibration condition, keeps all 192 replicates,
and requires the empirical relative RMSE bound to meet the target over the
reference interval. Candidate ranking uses proposed-step count and fixed ties,
not measured time. Diagnostics, unavailable intervals and coverage are retained.
Actual calibration application, setting selection, full numerical audits and
independent timing/precision confirmation remain pending.
timing_selection_v1_live_jobs.json records the live controller and two running
production jobs at 2026-10-18 04:20:15 JST.


## Consolidated interim report

The Japanese report ../tile_validation_report_2026-10-18_ja.md consolidates
the verified construction/failure definition, decoder limitations, direct-MC
reference and outstanding calibration work. interim_report_validation.json
records document hash, 16 local-link checks, count/interval table agreement,
reference-audit binding and the example source hash match.
This is document/evidence consistency checking, not new scientific calibration.


## Conditional-weight comparison

weight_comparison_deployment_v1.json and weight_comparison_bundle_v1.json
record the added target-weight comparison helper and its immutable deployment.
Acceptance passed 13 tests on Windows (2.61 s) and Linux (1.42 s), including
a short actual tile trace/analysis comparison and synthetic missing-cohort,
reference-binding and metadata-corruption cases.
The helper retains every replicate, reports weight means and reference
differences separately from BAR probability uncertainty, and checks JSON
metadata identities/hashes. It does not re-audit unused ACF NPZ or physical
traces. Full production application remains pending.
weight_comparison_live_jobs_v1.json records the live jobs/controller and
marker counts at 2026-10-18 04:49:31 JST.

## MC timing execution and capacity evidence v3

`mc_timing_deployment_v3.json` records the immutable v3 bundle, source and input hashes, 59 passing tests on Windows and Linux, and the scope of verification.
`mc_timing_bundle_v3.json`, `mc_timing_capacity_manifest_v3.json`, `mc_timing_benchmark_manifest_v3.json`, `mc_timing_native_preflight_v3.json`, and `mc_timing_dry_run_v3.json` contain the bundle index and prepared inputs.
The preflight ran on the login node; compute-node validation and capacity/benchmark measurements remain pending.
`mc_timing_live_jobs_v3.json` records the actual controller and two running PBS jobs at 05:07 JST; no new qsub was issued.

## Independent timing cohort metrics

`timing_metrics_deployment_v1.json` and `timing_metrics_bundle_v1.json` record the statistical comparison module and 32 passing tests on Windows and Linux.
It retains failures and missing costs, and withholds cost ratios unless both complete cohorts meet the empirical precision target over the reference interval.
BAR mixing diagnostics are explicitly uncollected. Artifact-ingestion auditing and actual timing comparisons remain pending.

## Timing artifact comparison adapter

`timing_comparison_deployment_v1.json` and `timing_comparison_bundle_v1.json` record the artifact adapter and 36 passing tests on Windows and Linux.
It checks complete independent cohorts, JSON/NPZ hashes, recorded native/execution evidence, task seeds and model metadata, and reference bindings before applying timing metrics.
Existing MC v3 manifests were confirmed compatible. Future BAR timing plans should use the new comparison bundle; older deployments remain immutable.
`timing_comparison_live_jobs_v1.json` records the two live PBS jobs and controller at 05:28 JST.
Actual timing comparisons, comparison-job resource measurements and qsub remain pending. Stored-state re-decoding and selection-cohort reanalysis are separate requirements.

## Completed bit-flip anchor phases, cases 0 and 1

`production_anchors-0.json` and `production_anchors-1.json` are unmodified phase summaries recovered while their later sampling phases remain live.
The corresponding `production_anchor_archive_verification-{case}.json` and `production_anchor_audit-{case}.json` verify all 192 artifacts, recorded seeds, 16,384-trial budgets, model hashes, counts, Wilson intervals and exact phase-summary reproduction.
Each cohort has 3,145,728 trials. Case 0 has 1,838,748 failures; case 1 has 2,114,117 failures. Both have no failed task and no zero-failure anchor.
These anchors sample at physical p=.1 with decoder priors .03 and .05 respectively; they are not target-p references. Pooled audit estimates never replace the separate replicate anchors.
Raw physical trials and full direct_mc RNG metadata were not saved. Sampling p and RNG calls are verified through pinned source/manifest, not raw-trial recounting or independent decoder replay.

`production_anchor_recovery_01.json` records unchanged remote inputs and the archive hashes:

- `output/tile_validation_recovery/production-anchors-0.tar.gz`: `1d85868b849b23c197cd34b382194833d80d46ff2f7fcce0e1b4cea308512192`.
- `output/tile_validation_recovery/production-anchors-1.tar.gz`: `6ae4bc850785236b129a00cfae47534c52b5040501c4c3bc08a68e69156c4384`.

The case-3 recovery commands above apply with the case and filenames changed to 0 or 1 and fresh output paths.

## Finite seed-namespace census

`seed_namespace_audit.json` records 382,944 unique planned seeds: 1,248 reference, 768 anchor, 190,464 initialization and 190,464 sampling seeds, with no collision across these groups.
All 576 recovered anchor records from cases 0, 1 and 3 matched their planned case/replicate seeds. Reference recorded-seed checks reuse the bound completed reference audit.
This is not a full sampling-metadata audit, does not include bootstrap or timing namespaces, and does not prove statistical independence of pseudorandom streams.
`audit_seed_namespaces.py` reproduces the census with pinned source and input hashes; `seed_namespace_environment.json` records the Windows environment and 10.73-second execution result binding.

```sh
python docs/wp/data_tile_validation_2026-10-17/audit_seed_namespaces.py --output NEW_OUTPUT_PATH/seed_namespace_audit.json
```

## Completed anchors and later execution evidence

`production_anchor_audit-2.json` adds the 192 tile72-depolarizing anchors: 3,145,728 trials and 1,480,773 failures at physical p=.1 with target decoder prior=.03.
All four anchor cohorts now have saved audits, with 768 recorded seeds verified in total.
`interim_anchor_update_validation_v1.json` rechecks each saved audit against its exact phase-summary hash and counts; this is not a fresh raw-trial re-decoding.
`production_case1_recovery_validation_2026-10-18.json` records recovery of the completed tile288 bit-flip cohort.

`early_mixing_summary_v1.json`, `early_mixing_group_records_v1.json`, and `early_mixing_report_validation_v1.json` describe the preregistered 16-group tile288 inspection and its limited checkpoint re-decoding scope.
They do not replace the 192-replicate BAR calibration.
`low_analysis_cluster_observation_v4.json` records two live one-node sampling jobs and the live coordinator at 09:38 JST.

`low_analysis_*_v7` records isolated deployment of the full-audit runners and WSS audit submitter, with 48 Linux acceptance tests and the unchanged baseline core/native profile.
`full_audit_windows_acceptance_v1.json` records the corresponding per-file Windows tests and optional-dependency skips.
These are execution preparation and fixture tests; full production audits, low-noise sampling, BAR calibration, and independent timing remain pending.

## Analysis and audit integration (2026-10-18)

`audited_results_windows_acceptance_v1.json` records 17 main and 10 low-noise acceptance tests, final source hashes, and independent reviews.
`low_analysis_*_v9.*` records 27 Linux tests, strict native validation, archive/source hashes, and the environment with the unchanged baseline core.
These use small saved artifacts and explicit full-census fixtures; they are not full production audit results.
`low_analysis_cluster_observation_v6.json`, `v7.json`, and `v8.json` record jobs and trace counts at 09:55, 10:02, and 10:05 JST.
Historical consumed-input hashes are absent from the main analysis and are distinct from later checks of current inputs against saved audits.

## Completed case-0 sampling and pending archive export (2026-10-18)

`production_case0_completion_2026-10-18.json` records PBS exit 0, all 86,016 planned tasks with no recorded sampling failures, the downloaded summary hash, and the coordinator's qsub receipt for BAR job 265212.
`production_sample-0.json` is the complete sampling phase summary; it does not replace raw payload recovery or numerical trace audit.
`production_sampling_export_stage_case0_v1_hash_failure.json` preserves a failed staging attempt caused by Windows CRLF conversion of the PBS script; no job was submitted.
The v2 gate/stage records bind 8,074,369,747 input bytes and the fresh remote export root, with no export job submitted yet.
`recover_completed_tile_sampling_v2.py` preserves the exact staged recovery helper; `production_sampling_export_preparation_v2.json` binds its hash and the successful PBS script syntax check.
Compression must run through qsub after the existing controller terminates and within the global two-node limit.
Archive integrity, numerical trace validation, and scientific calibration remain separate requirements.

## All main sampling jobs completed (2026-10-18 10:28 JST)

`production_sampling_complete_2026-10-18.json` verifies all four sampling PBS exits and the full 190,464-task summary census, with zero recorded sampling failures.
Case1/3 summary hashes are linked to the earlier verified archives; case0/2 hashes are linked to the downloaded summaries.
The record also binds the coordinator's qsub receipt for case3 BAR analysis job 265213, running alongside case0 analysis job 265212.
`production_sample-2.json` preserves the 43,008-task case2 phase summary.
Case2 export gate/stage records bind the 1,245,641,312-byte input and fresh `20261018-v2-tile-case2-recovery` root; `production_sampling_export_script_validation_case2_v2.json` records source/script hash and bash syntax verification.
Neither case0 nor case2 archive export has been submitted; full numerical audits and BAR calibration remain pending.

## Initial BAR artifacts (2026-10-18 10:40 JST)

`bar_analysis_live_observation_v1.json` and `v2.json` record running jobs, resource usage and group counts; v2 observed 96 completed case3 groups out of 768.
`bar_analysis_first_artifact_validation_v1.json` validates only the fixed group `(3,0,0,0)`: all 88 planned rows, 1,224 diagnostic/ACF references and artifact hashes.
That group's intervals were available without recorded estimation exceptions, but this is not a convergence, accuracy, or coverage result.

# Additional capacity preparation, 2026-10-18 10:56 JST

- `bar_analysis_first_artifact_case0_validation_v1.json`: fixed case-0 group `(0,0,0,0)` checked at 11:03 JST; 88 planned rows and 1,056 diagnostics/ACF arrays with source/context/runtime/manifest and before/after payload hashes. Single-artifact integrity only; no full-cohort calibration or bootstrap replay.
- `trace_audit_remaining_plans_preparation_v1.json`: new capacity/full plans for main cases 0, 1, and 2; existing case 3 preserved. No audit execution or qsub.
- `low_sampling_capacity_preparation_v1.json`: remaining 11 sampling capacity plans, completing all 12 fixed conditions; per-condition evidence includes original generated bytes and hashes. No sampling, anchors, or qsub.
- `low_analysis_capacity_remaining_preparation_v1.json` and `low_analysis_capacity_remaining_preparation_validation_v1.json`: remaining 11 synthetic BAR capacity plans, completing all 12 fixed conditions. No profiling run or qsub.
- `bar_analysis_live_observation_v3.json`: main BAR jobs 265212 and 265213 running on one node each; 96/768 and 192/768 completed groups, respectively. Progress only, not full-cohort calibration evidence.


## Main analysis recovery helper

`analysis_recovery_preparation_v2.json` binds the fixed helper/spec/tests, Windows and Linux synthetic acceptance (27 tests each), and final independent review. The collector binds recovered worker/script bytes to prior stage evidence. See [execution instructions](../tile_full_audit_execution_2026-10-18_ja.md).

## Case 3 BAR completion and preliminary reading (2026-10-18 12:13 JST)

`production_bar_case3_completion_v1.json` records PBS job 265213 ending with exit 0 and binds the downloaded phase summary, cohort summary, submission ledger, script and logs.
`production_bar_summary-3.json` contains all 352 planned settings with 192 replicates each; the phase summary reports 768 groups and 67,584 rows.
`case3_bar_summary_read_v1.json` and its Japanese companion record independent summary-level arithmetic and provenance checks, including all 16 prespecified longest-window/fine-ladder settings.
All settings retain high-R-hat and low-ESS flags for every replicate; available intervals do not establish convergence or nominal coverage.
Raw-row recomputation, full analysis-archive validation and full numerical trace audits remain pending.
`production_analysis_export_gate_case3_20261018-v2-tile-case3-analysis-recovery.json`, the corresponding stage record, and `production_analysis_export_script_validation_case3_v2.json` record the fresh export staging of 2,315 files (3,890,389,474 bytes).
The export has not been submitted, compressed or collected; the existing controller still owns the two-node allocation.
`production_bar_case1_submission_observation_v1.json` records replacement BAR job 265214 and the live two-node census at 12:12:48 JST, with exact ledger/script copies.
`production_bar_case1_submission_runtime_binding_v1.json` explains the preserved whole-dictionary comparison failure: the analysis runtime adds a source-hash field, while all shared native fields and that additional fixed-source hash match.
`bar_analysis_first_artifact_case1_validation_v1.json` records the fixed group `(1,0,0,0)` at 12:30 JST: 88 planned unique rows, 744 diagnostics and ACF arrays, and unchanged provenance/payload hashes.
This group has no missing intervals or recorded estimation failures, but all 88 rows carry diagnostic flags; the check does not establish full-cohort accuracy, coverage or mixing.
# Case 1 BAR completion and recovery staging (2026-10-18 13:50 JST)

The final main BAR job (case 0, 265212) completed with exit 0 and PBS wall time 4h30m34s. `production_bar_case0_completion_v1.json` and exact small files preserve completion; `case0_bar_summary_read_v1.json` and its Japanese report check all 352 conditions and the 16 prespecified 60,000-sample/16-chain settings. `production_controller_finished_status_v1.json` and `production_controller_finished_observation_v1.json` bind finished state to observed PID absence. After that confirmation, `seed_census_submission_stdout_v1.txt` and `seed_census_submission_invocation_v1.py` record actual qsub job 265220 for all 3,855,274 planned seed entries; reserved timing stages 140/141 remain outside that census. Census results and full numerical trace audits were pending at submission.

`production_analysis_recovery_case2_20261018-v2-tile-case2-analysis-recovery.json` and `analysis_export_case2_collection_observation_v1.json` record successful case-2 collection and all-member verification: 4,477,986,977 bytes, archive SHA256 `3431a5a84aa13ca0773ed8ebd92dab34feb3840b357496a7e614264183707410`, 2,315 files and 768 artifacts. Case-1/2/3 raw rows are now recovered within their verified archives; independent row reaggregation and scientific trace audits remain pending.

Case-3 recovery is now recorded by `production_analysis_recovery_case3_20261018-v2-tile-case3-analysis-recovery.json`: 3,087,175,636 bytes, SHA256 `d213d22dbbf34c52790b3955c9731ffc75901f5727edc857e124a728ca0089e1`, all 2,315 member hashes and 768 artifacts verified. `sampling_export_stages_readonly_check_v1.json` independently checks the unused case-0/2 sampling export stages. After case-2 analysis export 265218 finished, `sampling_export_case0_submission_stdout_v1.txt` records the guarded qsub of sampling export 265219. Its collect must additionally bind downloaded worker/script hashes to the fixed accepted stage, beyond the frozen sampling helper's self-reported worker hash check.

`production_analysis_recovery_case1_20261018-v2-tile-case1-analysis-recovery.json` records successful recovery and all-member integrity verification of the 1,943,166,818-byte archive (SHA256 `19ccf9223b94a8e1178bafbb460ca21d94c1256be77ad5b6fa9f49084f944b2f`). `analysis_export_case1_collection_observation_v1.json` retains the worker/PBS clock discrepancy without altering original timestamps. This does not perform scientific trace re-decode or BAR recomputation. Subsequent case-3 and case-2 exports were submitted sequentially as 265217 and 265218 after repeating the same fixed-ledger and node-budget checks; their `analysis_export_case{3,2}_submission_stdout_v1.txt` and matching scripts preserve each receipt. Case 3 finished with exit 0 before case 2 was submitted.

At 14:29 JST, case-1 export was submitted once as PBS job 265216. `production_controller_submission_exhaustion_v1.json` and its exact-byte `controller_submission_exhaustion_v1/` inputs establish that all eight fixed ledgers exist and the controller has no pending submission. `analysis_export_case1_submission_script_v1.py` revalidates those inputs, all pins, stage hashes and global node count before qsub; `analysis_export_case1_submission_stdout_v1.txt` records its receipt. This explicitly supersedes terminal-controller wording for this export only, while preserving the two-node limit. Collection and archive verification were pending at submission time.

Later case-2 completion is recorded in `production_bar_case2_completion_v1.json` (job 265215, exit 0, 37m39s). `case2_bar_summary_read_v1.json` and `case2_bar_summary_read_v1_ja.md` contain the independent summary-level checks and all 16 prespecified comparisons. Full raw-row and trace audits remain pending. The staged analysis recovery evidence is `production_analysis_export_stage_case2_20261018-v2-tile-case2-analysis-recovery.json` with `production_analysis_export_script_validation_case2_v2.json`; 2,315 files and 5,593,125,982 bytes, export not yet submitted at staging time.

`bar_analysis_first_artifact_case2_validation_v1.json` records the subsequent fixed case-2 artifact check at 13:54 JST: all 88 planned rows and 1,728 diagnostic/ACF references, unchanged hashes, zero missing intervals, 88 flagged rows and 12 rows containing undefined diagnostics. This is not a full-cohort or trace audit.

- `production_bar_case1_completion_v1.json`: terminal PBS evidence and exact-byte metadata recovery for job 265214; 768 groups and 67,584 rows.
- `case1_bar_summary_read_v1.json` and `case1_bar_summary_read_v1_ja.md`: independent summary-level checks and all 16 prespecified long-trace comparisons; raw-row reaggregation and full trace audits remain pending.
- `production_analysis_export_stage_case1_20261018-v2-tile-case1-analysis-recovery.json` and `production_analysis_export_script_validation_case1_v2.json`: staged recovery script for 2,315 files, 2,492,080,765 bytes; no export qsub or collection yet.
- `production_bar_case2_submission_observation_v1.json`: replacement job 265215 and fixed source/runtime/context binding, with two total active nodes.

