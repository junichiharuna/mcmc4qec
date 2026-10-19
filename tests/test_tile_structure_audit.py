"""Rank evidence for stabilizer fibers, separate from full-support connectivity."""
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import audit_tile_structure as a
import tile_study as t


@pytest.mark.parametrize("size,noise,n,rank_s",[(6,"bit",72,32),(12,"bit",288,140),
                                             (6,"depolarizing",72,64),(12,"depolarizing",288,280)])
def test_complete_linear_fiber_rank_and_public_maps(size,noise,n,rank_s):
    record,arrays=a.audit_case(size,noise,.03 if size==6 else .05)
    assert record["n"]==n and record["k"]==8
    assert record["rank_stabilizers"]==rank_s
    assert record["nullity_joint_map"]==rank_s
    assert record["same_map_fiber_generated_by_stabilizers"]
    assert record["zero_syndrome_prediction_is_zero"]
    assert record["full_failure_support_connectivity"]=="not established"
    code,problem=t.build_problem(size,noise,.03 if size==6 else .05)
    rng=np.random.default_rng(381)
    states=rng.integers(0,2 if noise=="bit" else 4,size=(8,n),dtype=np.uint8)
    for state in states:
        binary=a.binary_components(state[None,:],noise)[0]
        assert np.array_equal(arrays["syndrome_map"]@binary%2,problem.model.syndrome(state))
        assert np.array_equal(arrays["logical_map"]@binary%2,problem.model.observables(state))
        # Every physical generator preserves both public linear maps.
        changed=state^problem.model.stabilizers
        binary_changed=a.binary_components(changed,noise)
        assert np.all(binary_changed@arrays["syndrome_map"].T%2==problem.model.syndrome(state))
        assert np.all(binary_changed@arrays["logical_map"].T%2==problem.model.observables(state))
