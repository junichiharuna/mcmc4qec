"""A relative-RMSE budget is a Bernoulli MSE criterion, not a CI half-width."""
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_mc_precision_budget as b


def test_relative_rmse_matches_finite_binomial_distribution():
    n,p=7,.23
    mse=sum(math.comb(n,k)*p**k*(1-p)**(n-k)*(k/n-p)**2 for k in range(n+1))
    assert b.relative_rmse(n,p)==pytest.approx(math.sqrt(mse)/p)
    assert b.required_trials(.2,.1)==400


def test_reference_bounds_determine_ordered_budgets_and_fixed_rounding():
    row=dict(case=0,target_p=.03,estimate=.2,interval_999=[.18,.22])
    out=b.budget_row(row,.1)
    lo,hi=out["required_trials_reference_range"]
    assert lo<out["required_trials_reference_point"]<hi
    assert out["planned_trials"]%64==0 and out["planned_trials"]>=hi
    assert b.relative_rmse(out["planned_trials"],.18)<=.1
    assert out["metric"]=="relative_RMSE"


@pytest.mark.parametrize("p,epsilon",[(0,.1),(1.1,.1),(.2,0),(.2,-1),(float("nan"),.1)])
def test_invalid_probability_or_precision_rejected(p,epsilon):
    with pytest.raises(ValueError):
        b.required_trials(p,epsilon)
