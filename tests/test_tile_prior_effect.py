"""Paired failure-boundary changes must not disappear through cancellation."""
import itertools
import math
from pathlib import Path
import sys

import pytest

pytest.importorskip("scipy")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_prior_effect as p


def comparison(n=192,a=55,b=54,d=15,logical=39):
    return dict(samples=n,baseline_failures=a,failures=b,failure_disagreements=d,logical_disagreements=logical,
                n=288,noise="depolarizing",physical_p=.1,baseline_physical_prior=.1,
                alternative_physical_prior=.0001,alternative_sector_prior=2*.0001/3,tasks=6)


def test_paired_depolarizing_cancellation_and_standard_error():
    result=p.paired_table(comparison())
    assert result["table"]==dict(both_success=130,baseline_success_alternative_failure=7,
                                 baseline_failure_alternative_success=8,both_failure=47)
    assert result["failure_rate_difference"]==pytest.approx(-1/192)
    assert result["failure_boundary_mass"]==pytest.approx(15/192)
    values=[1]*7+[-1]*8+[0]*177
    mean=sum(values)/len(values)
    se=math.sqrt(sum((x-mean)**2 for x in values)/(191*192))
    assert result["paired_difference_standard_error"]==pytest.approx(se)


@pytest.mark.parametrize("update",[{"failure_disagreements":14},{"failures":192},{"logical_disagreements":2},
                                   {"baseline_failures":-1},{"samples":0},{"failures":54.0}])
def test_impossible_or_noninteger_counts_refused(update):
    with pytest.raises(ValueError):p.paired_table(dict(comparison(),**update))


def test_zero_disagreements_have_positive_upper_bound_and_larger_family_is_wider():
    zero=comparison(a=55,b=55,d=0,logical=0)
    one=p.assess_rows([zero],alpha=.05)
    two=p.assess_rows([zero,dict(zero,alternative_physical_prior=.001)],alpha=.05)
    first=one["records"][0]
    assert first["failure_boundary_interval"][0]==0 and first["failure_boundary_interval"][1]>0
    assert two["records"][0]["failure_boundary_interval"][1]>first["failure_boundary_interval"][1]
    assert one["marginal_intervals"]==3 and two["marginal_intervals"]==6


def test_finite_multinomial_joint_coverage():
    # Exhaust the four paired outcomes, not independent baseline/alternative MCs.
    probabilities=(.5,.1,.2,.2)
    n=4
    covered=0.
    for cells in itertools.product(range(n+1),repeat=4):
        if sum(cells)!=n:continue
        n00,n01,n10,n11=cells
        row=comparison(n,n10+n11,n01+n11,n01+n10,n01+n10)
        result=p.assess_rows([row],alpha=.05)["records"][0]
        intervals=(result["new_failure_interval"],result["recovered_interval"],result["failure_boundary_interval"])
        true_values=(.1,.2,.3)
        mass=math.factorial(n)
        for count,prob in zip(cells,probabilities):mass*=prob**count/math.factorial(count)
        if all(lo<=value<=hi for (lo,hi),value in zip(intervals,true_values)):
            covered+=mass
            lo,hi=result["failure_rate_difference_interval"]
            assert lo<=-.1<=hi
    assert covered>=.95


def test_duplicate_comparison_and_bad_family_alpha_refused():
    with pytest.raises(ValueError):p.assess_rows([comparison(),comparison()])
    for alpha in (0.,1.,float('nan')):
        with pytest.raises(ValueError):p.assess_rows([comparison()],alpha=alpha)


def test_derivation_binds_raw_summary_and_producer(tmp_path):
    plan=dict(cases=[[6,"bit"]],probabilities=[.1],replicates=1)
    probe=dict.fromkeys(("repeat_mismatches","reverse_mismatches","fresh_mismatches","syndrome_violations","failure_definition_mismatches"),0)
    probe.update(samples=4,prior_comparisons=[dict(physical_target_prior=.03,sector_prior=.03,
        logical_disagreements=1,failure_disagreements=1,failures=2,baseline_failures=1)])
    data=dict(manifest=p.c.digest(plan),records=[dict(task=[0,0,0],status="ok",n=72,noise="bit",p=.1,decoder_probe=probe)])
    manifest,summary,counts=(tmp_path/name for name in ("manifest.json","summary.json","counts.json"))
    p.c.atomic_json(manifest,plan)
    p.c.atomic_json(summary,data)
    compact=p.compact.summarize(plan,data)
    compact.update(input_sha256=p.c.file_hash(summary),source_sha256=p.c.file_hash(p.compact.__file__))
    p.c.atomic_json(counts,compact)
    result=p.derive(manifest,summary,counts)
    assert result["comparisons"]==1 and result["distinct_probe_draws"]==4
    with summary.open("ab") as stream:stream.write(b"\n")
    with pytest.raises(ValueError,match="hash"):p.derive(manifest,summary,counts)
