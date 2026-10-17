"""Separate detailed balance from irreducibility on the exact failure support."""
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
pytest.importorskip("pymatching")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import steane_components as s


def test_finite_default_components_and_stabilizer_bridge():
    result = s.analyze()
    assert result["failure_weight_counts"] == [0, 0, 21, 7, 28, 0, 7, 1]
    assert [x["size"] for x in result["components"]] == [56, 8]
    assert result["dispersed_component_ids"] == [0, 1, 0, 1]
    for check in result["checks"]:
        assert check["row_sum_error"] < 1e-12
        assert check["detailed_balance_error"] < 1e-12
        assert check["stationarity_error"] < 1e-12
        assert check["minimum_self_loop"] >= .05-1e-12
        assert check["components"] == (2 if check["mixture"] == "Z0.7_H0.3" else 1)
    assert all(x["relative_bias"] < -.9 for x in result["dispersed_bar_limits"])
