"""Decoder internals are captured before another decode and stages are explicit."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import probe_tile_decoder_stages as p
import tile_study as t


def test_stage_snapshot_actual_syndrome_and_zero_bypass():
    code,problem=t.build_problem(6,"bit",.03)
    state=np.zeros(code.n,dtype=np.uint8)
    state[[0,1,2]]=1
    syndrome=problem.model.syndrome(state)
    result=p.snapshot(problem.decoder,code.hz,syndrome)
    assert result["returned_syndrome_valid"]
    assert np.array_equal(result["predicted_logical"],code.lz@np.asarray(result["returned_correction"])%2)
    assert result["bp_executed"]
    assert (result["osd0_correction"] is not None)==result["osd_executed"]
    zero=p.snapshot(problem.decoder,code.hz,np.zeros(len(code.hz),dtype=np.uint8))
    assert not zero["bp_executed"] and not zero["osd_executed"]
    assert zero["bp_correction"] is None and zero["log_prob_ratios"] is None
    assert zero["osd0_correction"] is None and zero["osdw_correction"] is None
    assert zero["returned_syndrome_valid"] and not any(zero["returned_correction"])


def test_fixed_fixture_public_failure_and_stage_comparison():
    fixture=json.loads((Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17/decoder_platform_fixture.json").read_text())
    observed=p.probe(fixture)
    assert observed["stage_matches_public"] and observed["public_matches_baseline"]
    assert all(row["returned_syndrome_valid"] for row in observed["sectors"])
    assert observed["cython_source_sha256"]
    same=p.compare(observed,deepcopy(observed))
    assert all(row["returned_correction_hamming"]==0 and row["log_prob_ratios_max_absolute_difference"]==0 for row in same["sectors"])
    changed=deepcopy(observed)
    changed["sectors"][0]["log_prob_ratios"][0]+=.25
    delta=p.compare(observed,changed)
    assert delta["sectors"][0]["log_prob_ratios_max_absolute_difference"]==pytest.approx(.25)
    changed["sectors"][0]["syndrome"][0]^=1
    with pytest.raises(ValueError,match="inputs"):p.compare(observed,changed)


def test_converged_nonzero_bp_does_not_report_osd_aliases_as_executed():
    from ldpc import BpOsdDecoder
    import mcmc4qec as qec
    checks=np.eye(3,dtype=np.uint8)
    native=BpOsdDecoder(checks,error_rate=.03,max_iter=10,bp_method="minimum_sum",osd_method="osd_cs",osd_order=0)
    adapter=qec.DecoderAdapter(native,output_kind="correction",identifier="stage-test",logical_map=checks)
    observed=p.snapshot(adapter,checks,np.array([1,0,0],dtype=np.uint8))
    assert observed["bp_executed"] and observed["bp_converged"] and not observed["osd_executed"]
    assert observed["bp_correction"]==[1,0,0] and observed["returned_syndrome_valid"]
    assert observed["osd0_correction"] is None and observed["osdw_correction"] is None
