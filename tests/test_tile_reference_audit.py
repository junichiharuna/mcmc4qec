"""Independent-chunk uncertainty of a conditional ratio statistic."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import audit_tile_reference as a


def test_conditional_weight_chunk_delta_uses_count_weighting():
    records=[dict(trials=10,failures=2,conditional_weight=2.),
             dict(trials=10,failures=4,conditional_weight=4.)]
    result=a.conditional_weight_reference(records)
    assert result["mean"]==pytest.approx(10/3)
    assert result["chunk_delta_standard_error"]==pytest.approx(8/9)
    assert a.conditional_weight_reference([dict(trials=10,failures=0,conditional_weight=None)]*2)["mean"] is None
