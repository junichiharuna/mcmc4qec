"""Observe BP and OSD stages of the selected native-platform counterexample."""
import argparse
import json
from pathlib import Path

import ldpc
import numpy as np
import calibration as c
import tile_study as t
import probe_tile_decoder_platform as baseline


WARNING="One previously selected counterexample, observed after the final BP iteration. Stage differences do not identify the first divergent iteration, floating-point instruction, tie rule or compiler cause. No error-rate, BAR-bias or population-frequency inference. Decoder settings and production jobs are unchanged."


def snapshot(adapter,checks,syndrome):
    if adapter.output_kind!="correction" or adapter.logical_map is None:
        raise ValueError("explicit physical-correction adapter required")
    syndrome=np.asarray(syndrome,dtype=np.uint8)
    decoder=adapter.decoder
    output=np.asarray(decoder.decode(syndrome)).copy()
    if output.shape!=(checks.shape[1],) or np.any((output!=0)&(output!=1)):
        raise ValueError("invalid physical correction")
    bp_executed=bool(np.any(syndrome))
    osd_executed=bp_executed and not decoder.converge
    settings={key:getattr(decoder,key) for key in ("bp_method","max_iter","schedule","ms_scaling_factor","omp_thread_count",
              "random_schedule_seed","random_serial_schedule","osd_order","osd_method")}
    channels=np.asarray(decoder.channel_probs).copy()
    values=dict(returned_correction=output,bp_correction=np.asarray(decoder.bp_decoding).copy() if bp_executed else None,
                osd0_correction=np.asarray(decoder.osd0_decoding).copy() if osd_executed else None,
                osdw_correction=np.asarray(decoder.osdw_decoding).copy() if osd_executed else None)
    llr=np.asarray(decoder.log_prob_ratios).copy() if bp_executed else None
    if not np.all(np.isfinite(channels)) or (llr is not None and not np.all(np.isfinite(llr))):
        raise ValueError("nonfinite native values in fixed fixture")
    result=dict(settings=settings,syndrome=syndrome.tolist(),channel_probs=channels.tolist(),
                bp_executed=bp_executed,osd_executed=osd_executed,bp_converged=bool(decoder.converge),
                bp_iterations=int(decoder.iter) if bp_executed else None,
                log_prob_ratios=None if llr is None else llr.tolist(),
                predicted_logical=(adapter.logical_map@output%2).tolist())
    for key,value in values.items():
        if value is not None and (value.shape!=output.shape or np.any((value!=0)&(value!=1))):
            raise ValueError("invalid native intermediate hard decision")
        result[key]=None if value is None else value.tolist()
        result[key+"_weight"]=None if value is None else int(value.sum())
        result[key+"_syndrome_violations"]=None if value is None else int(np.count_nonzero(checks@value%2!=syndrome))
    result["returned_syndrome_valid"]=result["returned_correction_syndrome_violations"]==0
    return result


def probe(fixture):
    profile=baseline.probe(fixture)
    code,problem=t.build_problem(12,"depolarizing",.05)
    state=np.asarray(fixture["state"],dtype=np.uint8)
    syndrome=problem.model.syndrome(state)
    sectors=[dict(name="X",**snapshot(problem.decoder.x_decoder,code.hz,syndrome[:len(code.hz)])),
             dict(name="Z",**snapshot(problem.decoder.z_decoder,code.hx,syndrome[len(code.hz):]))]
    predicted=np.concatenate([row["predicted_logical"] for row in sectors]).astype(np.uint8)
    residual=problem.model.observables(state)^predicted
    sector=sum(int(value)<<bit for bit,value in enumerate(residual))
    public=problem.decoder.predict(syndrome).copy()
    public_failure=bool(problem.is_faulty(state))
    source_root=Path(ldpc.__file__).parent
    sources={name:c.file_hash(source_root/name) for name in ("bp_decoder/_bp_decoder.pyx","bposd_decoder/_bposd_decoder.pyx")}
    return dict(fixture=c.digest(fixture),source_sha256=c.file_hash(__file__),platform_profile=profile,
                cython_source_sha256=sources,sectors=sectors,stage_predicted_logical=predicted.tolist(),
                stage_residual_sector=sector,public_predicted_logical=public.tolist(),public_failure=public_failure,
                stage_matches_public=bool(np.array_equal(predicted,public) and bool(sector)==public_failure),
                public_matches_baseline=bool(public.tolist()==profile["repeated"][0]["predicted"] and public_failure==profile["repeated"][0]["failure"]),
                warning=WARNING)


def compare(first,second):
    if (first["fixture"]!=second["fixture"] or first["platform_profile"]["problem_hash"]!=second["platform_profile"]["problem_hash"]
        or [row["name"] for row in first["sectors"]]!=[row["name"] for row in second["sectors"]]):
        raise ValueError("different fixed inputs or sector identities")
    rows=[]
    for left,right in zip(first["sectors"],second["sectors"]):
        if any(c.canonical(left[k])!=c.canonical(right[k]) for k in ("settings","syndrome","channel_probs")):
            raise ValueError("different decoder settings or physical inputs")
        row=dict(name=left["name"],bp_execution_agrees=left["bp_executed"]==right["bp_executed"],
                 osd_execution_agrees=left["osd_executed"]==right["osd_executed"],
                 bp_iterations=[left["bp_iterations"],right["bp_iterations"]],
                 log_prob_ratios_max_absolute_difference=None,log_prob_ratios_sign_disagreements=None)
        for key in ("returned_correction","bp_correction","osd0_correction","osdw_correction","predicted_logical"):
            a,b=left[key],right[key]
            row[key+"_hamming"]=None if a is None or b is None else int(np.count_nonzero(np.asarray(a)!=np.asarray(b)))
        a,b=left["log_prob_ratios"],right["log_prob_ratios"]
        if a is not None and b is not None:
            a,b=np.asarray(a),np.asarray(b)
            row.update(log_prob_ratios_max_absolute_difference=float(np.max(np.abs(a-b))),
                       log_prob_ratios_sign_disagreements=int(np.count_nonzero(np.signbit(a)!=np.signbit(b))))
        rows.append(row)
    return dict(fixture=first["fixture"],sectors=rows,stage_residual_sectors=[first["stage_residual_sector"],second["stage_residual_sector"]],
                cython_sources_equal=first["cython_source_sha256"]==second["cython_source_sha256"],warning=WARNING)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("use a new observation path")
    result=probe(json.loads(args.fixture.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as stream:stream.write(c.canonical(result)+b"\n")
    print(json.dumps(dict(stage_residual_sector=result["stage_residual_sector"],stage_matches_public=result["stage_matches_public"],
                         sectors=[{k:r[k] for k in ("name","bp_converged","bp_iterations","osd_executed","returned_correction_weight")} for r in result["sectors"]])))


if __name__=="__main__":
    main()
