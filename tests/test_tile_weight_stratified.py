"""Finite probability decomposition and honest uncertainty for weight strata."""
import itertools
import math
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("scipy")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_weight_stratified as s


@pytest.mark.parametrize("noise,alphabet",[("bit",2),("depolarizing",4)])
def test_complete_layers_match_direct_finite_sum(noise,alphabet):
    n,p=4,.17
    seen=set()
    strata=[]
    fail=lambda state:sum(int(x) for x in state)%3==1
    for w in range(n+1):
        states=list(s.enum_patterns(n,w,noise))
        assert len(states)==s.class_size(n,w,noise)
        assert all(np.count_nonzero(x)==w for x in states)
        assert len({tuple(x) for x in states})==len(states)
        seen.update(tuple(x) for x in states)
        strata.append(dict(w=w,mode="enum",trials=len(states),failures=sum(fail(x) for x in states)))
        middle=len(states)//2
        assert [tuple(x) for x in s.enum_patterns(n,w,noise,middle)]==[tuple(x) for x in states[middle:]]
    assert seen==set(itertools.product(range(alphabet),repeat=n))
    result=s.synthesize(n,noise,p,strata)
    expected,weighted=0.,0.
    for state in seen:
        w=np.count_nonzero(state)
        mass=(p/(alphabet-1))**w*(1-p)**(n-w)
        if fail(state):
            expected+=mass
            weighted+=mass*w
    assert math.fsum(s.binomial_mass(n,w,p) for w in range(n+1))==pytest.approx(1)
    assert result["partial_estimate"]==pytest.approx(expected)
    assert result["partial_conditional_weight"]==pytest.approx(weighted/expected)
    assert result["interval"]==pytest.approx([expected,expected])
    assert result["omitted_mass_upper"]==0


def test_zero_mc_and_omitted_layers_have_nonzero_upper_bounds():
    strata=[dict(w=0,mode="enum",trials=1,failures=0),dict(w=1,mode="mc",trials=100,failures=0)]
    result=s.synthesize(4,"bit",.1,strata)
    assert result["partial_estimate"]==0
    assert result["interval"][1]>result["omitted_mass_upper"]>0
    assert result["partial_conditional_weight"] is None
    for invalid in (strata[1:],strata+strata[:1],[dict(w=0,mode="enum",trials=2,failures=0)]):
        with pytest.raises(ValueError):
            s.synthesize(4,"bit",.1,invalid)


def test_binomial_intervals_have_finite_sample_coverage_on_small_grid():
    n,alpha=8,.05
    intervals=[s.clopper_pearson(k,n,alpha) for k in range(n+1)]
    for rate in np.linspace(0,1,101):
        covered=math.fsum(s.binomial_mass(n,k,float(rate)) for k,(lo,hi) in enumerate(intervals) if lo<=rate<=hi)
        assert covered>=1-alpha-1e-12


def test_roundoff_cannot_invert_unit_probability_interval():
    strata=[dict(w=w,mode="enum",trials=math.comb(288,w),failures=math.comb(288,w)) for w in range(289)]
    result=s.synthesize(288,"bit",.03,strata)
    assert result["partial_estimate"]<=1
    assert 0<=result["interval"][0]<=result["interval"][1]<=1


@pytest.mark.parametrize("noise",["bit","depolarizing"])
def test_uniform_layer_draws_reproducible_and_public_failure_matches(noise):
    pytest.importorskip("ldpc")
    import tile_study as t
    # Use the smallest study code; the study's fixed OSD order 10 is too large
    # for the 13-qubit factory example's check-matrix nullity.
    code,problem=t.build_problem(6,noise,.01)
    states=s.draw_patterns(code.n,3,noise,32,np.random.default_rng(941))
    assert np.array_equal(states,s.draw_patterns(code.n,3,noise,32,np.random.default_rng(941)))
    assert np.all(np.count_nonzero(states,axis=1)==3)
    assert set(np.unique(states))<=({0,1} if noise=="bit" else {0,1,2,3})
    assert np.array_equal(t.compact(problem,states)["sector"]!=0,[problem.is_faulty(x) for x in states])
