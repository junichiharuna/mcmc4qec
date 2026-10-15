# Step timing data, 2026-10-15

`before.csv` records the unchanged `35ed7f3` source. `trial1.csv` records the
intermediate optimization while parallel work was active; it is retained as
exploratory timing, not the acceptance result. `final.csv` and `final.log` record
the integrated source after the other agents' CPU experiments ended.

All three invocations use seed 731, 10,000 steps, two repeats, p=0.01,
Z/H=0.7/0.3, k=2, lazy=0, one chain, and the existing `bench_step.py` setup.
The first two invocations also profile a separate library run after the first
timed run of each case. The final invocation does not profile.

`environment.json` contains the final package fingerprint, research runner
fingerprint and revision, dependency versions, and measurement boundaries.
The research checkout has advanced since dev5, but its `run_rimc_mixed` function
used here is unchanged from the dev5 reference; changes to `runners.py` concern
the depolarizing runner. Unrelated untracked research-paper files were left
untouched.

Both final toric repetitions are below the 2x time target. These are short
same-seed timing repeats, not a statistical performance guarantee or a mixing
or coverage experiment. See [the performance record](../../performance_ja.md)
and [independent correctness review](../speed_review_2026-10-15_ja.md).
