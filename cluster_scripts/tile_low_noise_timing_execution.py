"""Fixed independent low-noise MC/BAR tasks and fail-closed execution evidence.

Scientific selection/seed plans are supplied by stage two. This module does not
produce a selector or run a seed census. A completed, pinned formal census is a
mandatory external dependency, including its native/PBS/current-input envelope.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import sys
import time
import traceback

import numpy as np
import mcmc4qec as qec
import calibration as c
import tile_study as t
import tile_bar_study as bar
import tile_bar_time_benchmark as old_bar
import tile_mc_time_benchmark as native
import tile_low_noise_study as low
import tile_low_noise_timing_plan as plans
import tile_low_noise_timing_seed_audit as seeds

THREADS=native.THREADS
WARNING="Independent fixed-budget task timing only; no precision, mixing, coverage or speedup certification. Capacity is two full estimators, not evaluation data. Resource extrapolation to 96 workers is unverified. All 24 selection outcomes and all planned tasks are retained."
OUTER_FIELDS={"inclusive_wall_seconds","inclusive_cpu_seconds","peak_rss_mb","artifact_marker_sha256"}


class ValidationError(ValueError):
    """Provenance violation, never a recorded scientific estimator failure."""


def require(value,message):
    if not value: raise ValidationError(message)


def number(value,*,positive=False):
    require(type(value) in (int,float) and math.isfinite(value) and (value>0 if positive else value>=0),"finite measured number required")
    return value


def resource(cpus,workers,memory,seconds):
    return dict(cpus=cpus,workers=workers,memory_gb=memory,wall_seconds=seconds,
                walltime=f"{seconds//3600:02}:{seconds%3600//60:02}:{seconds%60:02}",requested_nodes=1,max_nodes=2)


def capacity_resources():
    return resource(2,2,340,86400)


def resource_plan(measured):
    """Fixed conservative policy; never change any scientific trial/trace count."""
    rows=measured["records"]
    require(len(rows)==2,"exactly two full capacity estimators required")
    if measured.get('execution_infeasible_capacity_envelope') is True:
        return dict(status='execution_infeasible_capacity_envelope',partitions=[],warning=WARNING)
    if any(row["status"]!="ok" for row in rows): return dict(status="capacity_failed",partitions=[])
    if any(row.get("available") is not True for row in rows): return dict(status="capacity_unavailable",partitions=[])
    for row in rows:
        for key in ("task_wall_seconds","inclusive_wall_seconds","peak_rss_mb"):number(row[key],positive=True)
        for key in ("cpu_seconds","inclusive_cpu_seconds"):number(row[key])
        require(row["inclusive_wall_seconds"]>=row["task_wall_seconds"] and row["inclusive_cpu_seconds"]>=row["cpu_seconds"],"inclusive clock is smaller than task clock")
    phase=number(measured["pool_wall_seconds"],positive=True)
    require(phase>=max(row["inclusive_wall_seconds"] for row in rows),"pool clock shorter than a worker task")
    outside=number(measured["outside_pool_wall_seconds"])
    parent=number(measured["parent_peak_rss_mb"],positive=True)
    wall=max(row["task_wall_seconds"] for row in rows)
    artifact=max(row["inclusive_wall_seconds"]-row["task_wall_seconds"] for row in rows)
    peak=max(row["peak_rss_mb"] for row in rows)
    overhead=phase-max(row["inclusive_wall_seconds"] for row in rows)+outside
    memory=lambda w:max(32,math.ceil(2*w*peak/1024+1.5*parent/1024+8))
    allowed=[w for w in range(1,97) if memory(w)<=340]
    base=dict(policy="full_estimator_capacity_v1",measurement_digest=c.digest(measured),partitions=[],
              observed_task_seconds=wall,observed_additional_seconds=artifact,observed_job_overhead_seconds=overhead,
              observed_worker_rss_mb=peak,observed_parent_rss_mb=parent,warning=WARNING)
    if not allowed:return dict(base,status="execution_infeasible_memory_policy",workers_limit=0,partition_size=0)
    workers=max(allowed)
    def request(n):
        w=min(n,workers);prediction=math.ceil(n/w)*wall+n*artifact+overhead
        seconds=max(1800,1800*math.ceil((2*prediction+600)/1800))
        return resource(96,w,memory(w),seconds),prediction
    sizes=[n for n in range(1,193) if request(n)[0]["wall_seconds"]<=86400]
    if not sizes:return dict(base,status="execution_infeasible_wall_policy",workers_limit=workers,partition_size=0)
    size=max(sizes);parts=[]
    for start in range(0,192,size):
        reps=list(range(start,min(start+size,192)));res,prediction=request(len(reps))
        parts.append(dict(index=len(parts),replicates=reps,resource=res,predicted_seconds=prediction))
    require([rep for part in parts for rep in part["replicates"]]==list(range(192)),"partition union differs")
    return dict(base,status="ready",workers_limit=workers,partition_size=size,partitions=parts)


def task_row(plan,task):
    plans.seed_coordinates(plan,task,0,0,0)
    return next(row for row in plan["rows"] if tuple(row[k] for k in ("case","target_index","epsilon_index"))==tuple(task[:3]))


def metadata(result,problem,p,seed):
    try:old_bar.check_metadata(result,problem,p,seed)
    except Exception as error:raise ValidationError("actual fixed model/prior/p/RNG differs") from error


def run_task(args):
    """One fresh full estimator; only scientific exceptions become task failures."""
    root,plan,task=args;root=Path(root);task=tuple(task);row=task_row(plan,task)
    path=root/"tasks"/c.task_id(task)
    require(not any(path.with_suffix(suffix).exists() for suffix in (".json",".npz",".done.json")),"fresh task required; never reuse timing")
    identity=dict(manifest=c.digest(plan),task=list(task))
    started,cpu=time.perf_counter(),time.process_time();arrays={}
    timing={k:dict(wall_seconds=0.,cpu_seconds=0.) for k in ("construction","anchor","initialization","sampling","compact","analysis")}
    record=dict(task=list(task),role=plan["purpose"],status="ok",available=False,estimate=None,interval=None,
        physical_p=row["target_p"],decoder_prior=row["target_p"],condition=row.get("condition"),timing=timing,
        failure=None,failed_chains=0,chains=[],diagnostics="not_collected",warning=WARNING)
    try:
        with old_bar.clock(timing,"construction"):
            code,problem=t.build_problem(row["size"],row["noise"],row["target_p"])
        record["problem_hash"]=c.digest(problem.metadata())
        if ".mc." in plan["purpose"]:
            seed=plans.task_seed(plan,task,0,0,0);record["seed"]=seed
            with old_bar.clock(timing,"sampling"):
                result=qec.direct_mc(problem,row["target_p"],trials=row["mc_budget"]["trials"],seed=seed)
            metadata(result,problem,row["target_p"],seed)
            require(result.trials==row["mc_budget"]["trials"],"actual MC budget differs")
            record.update(trials=result.trials,failures=result.failures,estimate=result.estimate,
                interval=None if result.interval is None else list(result.interval),metadata=result.metadata,
                direct_mc_elapsed_seconds=result.elapsed_seconds,available=True,warnings=result.warnings)
        else:
            cfg=row["condition"];anchor_seed=plans.task_seed(plan,task,0,0,0);bootstrap_seed=plans.task_seed(plan,task,0,0,3)
            record.update(anchor_seed=anchor_seed,bootstrap_seed=bootstrap_seed,bootstrap_rng_consumed=False,
                          initialization_stride=row["initialization_stride"],fine_rung_indices=row["fine_rung_indices"])
            with old_bar.clock(timing,"anchor"):
                mc=qec.direct_mc(problem,row["rungs"][0],trials=row["anchor_trials"],seed=anchor_seed)
            metadata(mc,problem,row["rungs"][0],anchor_seed)
            require(mc.trials==row["anchor_trials"],"fresh anchor budget differs")
            record["anchor"]=dict(status="ok",seed=anchor_seed,trials=mc.trials,failures=mc.failures,
                estimate=mc.estimate,interval=None if mc.interval is None else list(mc.interval),metadata=mc.metadata)
            shape=(len(row["rungs"]),cfg["chains"],cfg["samples"])
            arrays={k:np.zeros(shape,dtype=dtype) for k,dtype in (("weight",np.uint16),("syndrome_weight",np.uint16),("sector",np.uint32))}
            arrays.update(initial=np.zeros((*shape[:2],code.n),dtype=np.uint8),final=np.zeros((*shape[:2],code.n),dtype=np.uint8),
                initial_coefficients=np.zeros((*shape[:2],len(code.lx)*(2 if row["noise"]=="depolarizing" else 1)),dtype=np.uint8),
                chain_ok=np.zeros(shape[:2],dtype=np.bool_))
            for rung,p in enumerate(row["rungs"]):
                for chain in range(cfg["chains"]):
                    entry=dict(rung=rung,fine_rung_index=row["fine_rung_indices"][rung],chain=chain,status="ok",
                        init_seed=plans.task_seed(plan,task,rung,chain,1),sample_seed=plans.task_seed(plan,task,rung,chain,2),
                        logical_index=plans.logical_index(row,task[3],chain),initialization_rng_consumed=cfg["init"]=="logical_combination")
                    record["chains"].append(entry)
                    try:
                        with old_bar.clock(timing,"initialization"):
                            state,coeff=low.logical_state(code,row["noise"],cfg["init"],entry["logical_index"],np.random.default_rng(entry["init_seed"]))
                            require(problem.is_faulty(state) and math.isfinite(problem.log_prob(state,p)),"initial state outside failure support")
                            entry["initial_sector"]=int(t.compact(problem,state[None,:])["sector"][0])
                            arrays["initial"][rung,chain]=state;arrays["initial_coefficients"][rung,chain]=coeff
                        with old_bar.clock(timing,"sampling"):
                            sampled=qec.sample_faulty(problem,p,config=qec.SamplingConfig(samples=cfg["burn"]+cfg["samples"],burn_in=0,
                                kernels=qec.KernelConfig(**row["kernels"][cfg["kernel"]]),cache_cap=row["cache_cap"],cache_policy="lru"),
                                initial_state=state,seed=entry["sample_seed"])
                        metadata(sampled,problem,p,entry["sample_seed"])
                        entry.update(metadata=sampled.metadata,acceptance=sampled.acceptance,warnings=sampled.warnings)
                        with old_bar.clock(timing,"compact"):
                            kept=sampled.states[0][cfg["burn"]:]
                            require(kept.shape==(cfg["samples"],code.n),"actual saved length differs")
                            compact=t.compact(problem,kept)
                            require(np.all(compact["sector"]>0),"compact independent decoding found nonfailure")
                            for key in ("weight","syndrome_weight","sector"):arrays[key][rung,chain]=compact[key]
                            arrays["final"][rung,chain]=kept[-1];arrays["chain_ok"][rung,chain]=True
                    except ValidationError:raise
                    except Exception as error:
                        entry.update(status="failed",error=repr(error));record["failed_chains"]+=1
            if record["failed_chains"]:record.update(status="failed",failure="sampling_failed")
            elif not mc.failures:record.update(status="unavailable",failure="anchor_unavailable")
            else:
                with old_bar.clock(timing,"analysis"):
                    record["bootstrap_rng_consumed"]=cfg["method"]=="block"
                    calculated=c.estimate_window(list(arrays["weight"]),code.n,row["rungs"],mc.estimate,
                        block=cfg["block"],replicates=row["bootstrap_replicates"],rng=np.random.default_rng(bootstrap_seed))
                    record.update(bar.with_anchor_variance(calculated,record["anchor"]))
                if not record["available"]:record["status"]="unavailable"
    except ValidationError as error:record.update(status="validation_failed",failure=repr(error),traceback=traceback.format_exc(),available=False)
    except Exception as error:record.update(status="failed",failure=repr(error),traceback=traceback.format_exc(),available=False)
    record.update(task_wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
                  task_peak_rss_mb=c.peak_rss_mb(),thread_environment={k:os.environ.get(k) for k in THREADS})
    c.save_artifact(path,identity,arrays,record)
    marker=c.file_hash(path.with_suffix(".done.json"))
    return dict(record,inclusive_wall_seconds=time.perf_counter()-started,inclusive_cpu_seconds=time.process_time()-cpu,
                peak_rss_mb=c.peak_rss_mb(),artifact_marker_sha256=marker)


class Evidence:
    def __init__(self):self.files={}
    def track(self,path,expected=None):
        path=Path(path).absolute();raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        value=[str(path.resolve()),digest]
        require(expected is None or digest==plans.require_hash(expected),"external input pin differs")
        require(self.files.setdefault(str(path),value)==value,"input changed between reads")
        return raw
    def read(self,path,expected=None):return json.loads(self.track(path,expected))
    def pin(self,value):return self.read(value["path"],value["sha256"])
    def finish(self):
        for path,(target,digest) in self.files.items():
            require(str(Path(path).resolve())==target and c.file_hash(path)==digest,"current input path/hash changed")


def source_files():
    pending=["tile_low_noise_timing_execution","submit_tile_low_noise_timing_execution"];found={}
    while pending:
        name=pending.pop()
        if name in found:continue
        spec=importlib.util.find_spec(name)
        require(spec is not None and spec.origin is not None,"missing source closure")
        path=Path(spec.origin).absolute();require(path.is_file(),"missing source closure")
        found[name]=path
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            modules=([item.name.split('.')[0] for item in node.names] if isinstance(node,ast.Import)
                     else [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else [])
            for module in modules:
                candidate=importlib.util.find_spec(module)
                if candidate and candidate.origin and Path(candidate.origin).parent.name=='cluster_scripts':pending.append(module)
    return found


def source_hashes():return {str(path):c.file_hash(path) for path in source_files().values()}


def memory_bytes(value):
    match=re.fullmatch(r'(\d+)(b|kb|mb|gb|tb)',str(value).lower())
    require(match is not None,"PBS memory units differ")
    return int(match[1])*1024**('b','kb','mb','gb','tb').index(match[2])


def check_pbs(ledger,job,*,terminal,hostname,allow_failure=False):
    res=ledger['resource'];actual=job.get('Resource_List',{})
    require(shlex.split(job.get('Submit_arguments',''))==ledger['command'][1:] and ledger['command'][0]=='qsub'
        and type(job.get('run_count')) is int and job['run_count']==1,"actual PBS script/run_count differs")
    require(actual.get('nodect')==1 and actual.get('ncpus')==res['cpus'] and res['requested_nodes']==1 and res['max_nodes']==2,"actual PBS node/CPU differs")
    require(memory_bytes(actual.get('mem'))==res['memory_gb']*1024**3 and actual.get('walltime')==res['walltime'],"actual PBS memory/time differs")
    parts=str(actual.get('select','')).split(':')
    require(parts[0]=='1' and '+' not in actual['select'],"actual PBS select count differs")
    fields=dict(part.split('=',1) for part in parts[1:])
    require(fields.get('ncpus')==str(res['cpus']) and memory_bytes(fields.get('mem'))==res['memory_gb']*1024**3,"PBS select resources differ")
    require({part.split('/')[0] for part in str(job.get('exec_host','')).split('+')}=={hostname},"actual PBS execution host differs")
    require(job.get('job_state')==('F' if terminal else 'R'),"actual PBS state differs")
    if terminal:require(type(job.get('Exit_status')) is int and (allow_failure or job['Exit_status']==0),"successful terminal PBS required")


def formal_census(config,bundle,proof):
    """Read a pinned completed census envelope, never the primitive gate alone.

The completion producer must record input_sha256/source_sha256 before and after,
native identity, result bytes, and formal scheduler evidence. Legacy completion
JSON lacking these bindings is deliberately insufficient for new timing stages.
"""
    required={'manifest','catalog','result','completion','submission','intent','execution','native','profile','fixture','script','terminal'}
    require(set(config)==required,"exact formal census descriptor required")
    values={key:proof.pin(pin) for key,pin in config.items() if key!='script'}
    proof.track(config['script']['path'],config['script']['sha256'])
    catalog=values['catalog'];result=values['result'];plan=values['manifest'];end=values['completion'];ledger=values['submission']
    seeds.complete_census_gate(result,catalog,expected_evidence_sha256=c.digest(catalog))
    require(catalog['timing_bundle_digest']==c.digest(bundle) and catalog['registry_digest']==c.digest(bundle['registry'])
        and catalog['selection_sha256']==bundle['selection_sha256'] and catalog['selection_digest']==c.digest(bundle['selection'])
        and catalog['new_plan_sha256']=={k:c.digest(v) for k,v in bundle['plans'].items()},"census covers a different scientific allocation")
    require(plan['catalog_evidence_digest']==c.digest(catalog) and plan['runtime']==t.runtime(),"census plan/runtime differs")
    digest=c.digest(plan);job=ledger['job_id'];execution=values['execution'];actual=values['native']
    require({k:v for k,v in ledger.items() if k!='job_id'}==values['intent'] and ledger['manifest']==digest
        and ledger['command']==['qsub',config['script']['path']] and ledger['script_sha256']==config['script']['sha256'],"census submission/intent/script differs")
    require(execution['manifest']==actual['manifest']==end['manifest']==digest
        and execution['pbs_job_id']==actual['pbs_job_id']==end['pbs_job_id']==job
        and execution['hostname']==actual['hostname']==end['hostname'],"census compute identity differs")
    check_pbs(ledger,values['terminal']['Jobs'][job],terminal=True,hostname=actual['hostname'])
    native.trace_audit.validate_platform(values['profile'],actual['profile'])
    require(values['profile']['fixture']==c.digest(values['fixture'])
        and plan['native_input_digests']=={k:c.digest(values[k]) for k in ('profile','fixture')},"census native input binding differs")
    require(end.get('complete') is True and end['result_sha256']==config['result']['sha256']
        and end['native_sha256']==config['native']['sha256'] and end['execution_sha256']==config['execution']['sha256'],"census terminal output binding differs")
    for label in ('input_sha256','source_sha256'):
        wanted=plan[label]
        require(wanted and end[label]==wanted and end[label+'_after']==wanted,"census before/after input binding differs")
        for path,sha in wanted.items():proof.track(path,sha)
    for path,sha in catalog['source_sha256'].items():proof.track(path,sha)
    require(all(plan['input_sha256'].get(path)==sha for path,sha in catalog['baseline_input_sha256'].items()),"census omitted legacy inputs")
    require(set(catalog['source_sha256']).issubset(plan['source_sha256'])
        and all(plan['source_sha256'][path]==sha for path,sha in catalog['source_sha256'].items()),"census omitted authority source")
    return dict(job_id=job,hostname=actual['hostname'],result_sha256=config['result']['sha256'],catalog_digest=c.digest(catalog),
                descriptors=config,scope='Full combined allocation and formal execution evidence; no mathematical stream-independence proof.')


def inputs(config):
    proof=Evidence();bundle=proof.pin(config['scientific_bundle'])
    plans.validate_plans(bundle,expected_registry_digest=config['registry_digest'])
    selection=proof.pin(config['selection'])
    require(c.digest(selection)==c.digest(bundle['selection']) and config['selection']['sha256']==bundle['selection_sha256'],"selection bytes differ")
    census=formal_census(config['census'],bundle,proof)
    inputs_native={key:proof.pin(config[key]) for key in ('platform_profile','platform_fixture')}
    expected=native.platform_inputs()
    require(inputs_native==expected,"current frozen native inputs differ")
    for path,sha in source_hashes().items():proof.track(path,sha)
    executable=Path(sys.executable).absolute();proof.track(executable)
    source=source_hashes();runtime=t.runtime()
    for plan in bundle['plans'].values():
        for row in plan['rows']:
            if row['planning_status']=='ready':
                require(row['runtime']==runtime,"scientific runtime differs")
                require(row['native_input_digests']=={k:c.digest(v) for k,v in expected.items()},"scientific native differs")
    proof.finish()
    return bundle,dict(files=proof.files,source_sha256=source,runtime=runtime,python_path=str(executable),
        python_sha256=c.file_hash(executable),pythonpath=os.environ.get('PYTHONPATH',''),core_path=str(Path(qec.__file__).absolute()),
        census=census,native_input_digests={k:c.digest(v) for k,v in expected.items()})


def json_read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def save_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(c.canonical(value)+b'\n')


def validate_record(plan,task,arrays,row):
    """Validate actual budgets, metadata and saved support, without BAR re-solving."""
    spec=task_row(plan,task);status=row['status']
    require(row['task']==list(task) and row['role']==plan['purpose'] and row['physical_p']==row['decoder_prior']==spec['target_p']
        and row['condition']==spec.get('condition') and status in ('ok','failed','unavailable','validation_failed'),"actual task identity/status differs")
    require(row['thread_environment']==THREADS,"actual worker threads differ")
    number(row['task_wall_seconds'],positive=True);number(row['cpu_seconds'])
    if status=='validation_failed':raise ValidationError('saved task provenance failure')
    code,problem=t.build_problem(spec['size'],spec['noise'],spec['target_p'])
    if 'problem_hash' in row:require(row['problem_hash']==c.digest(problem.metadata()),"actual Problem changed")
    if '.mc.' in plan['purpose']:
        if status!='ok':require(row.get('failure'),"failed MC lacks reason");return
        seed=plans.task_seed(plan,task,0,0,0)
        metadata(type('Saved',(),{'metadata':row['metadata']}),problem,spec['target_p'],seed)
        require(row['seed']==seed and type(row['trials']) is int and row['trials']==spec['mc_budget']['trials']
            and type(row['failures']) is int and 0<=row['failures']<=row['trials']
            and row['estimate']==row['failures']/row['trials'] and row['available'] is True,"fixed MC budget/count/estimate differs")
        return
    cfg=spec['condition']
    if 'anchor' not in row:require(status=='failed' and row.get('failure'),"missing fresh anchor without failure");return
    anchor=row['anchor'];aseed=plans.task_seed(plan,task,0,0,0)
    metadata(type('Saved',(),{'metadata':anchor['metadata']}),problem,spec['rungs'][0],aseed)
    require(row['anchor_seed']==anchor['seed']==aseed and anchor['trials']==spec['anchor_trials']
        and type(anchor['failures']) is int and 0<=anchor['failures']<=anchor['trials']
        and anchor['estimate']==anchor['failures']/anchor['trials']
        and row['bootstrap_seed']==plans.task_seed(plan,task,0,0,3),"fresh anchor/bootstrap binding differs")
    require(row['initialization_stride']==spec['initialization_stride'] and row['fine_rung_indices']==spec['fine_rung_indices'],"initialization/rung mapping differs")
    entries=row['chains'];expected=[(ri,ci) for ri in range(len(spec['rungs'])) for ci in range(cfg['chains'])]
    if len(entries)!=len(expected):require(status=='failed' and row.get('failure'),"unrecorded missing chain");return
    require([(entry['rung'],entry['chain']) for entry in entries]==expected,"chain census differs")
    shape=(len(spec['rungs']),cfg['chains'],cfg['samples'])
    dtypes={'weight':np.uint16,'syndrome_weight':np.uint16,'sector':np.uint32,'initial':np.uint8,'final':np.uint8,'initial_coefficients':np.uint8,'chain_ok':np.bool_}
    require(set(arrays)==set(dtypes) and all(arrays[key].dtype==dtype for key,dtype in dtypes.items()),'compact dtype/field differs')
    require(all(arrays[k].shape==shape for k in ('weight','syndrome_weight','sector'))
        and arrays['initial'].shape==arrays['final'].shape==(*shape[:2],code.n)
        and arrays['initial_coefficients'].shape==(*shape[:2],len(code.lx)*(2 if spec['noise']=='depolarizing' else 1))
        and arrays['chain_ok'].shape==shape[:2],"compact shape differs")
    zero=np.zeros(code.n,dtype=np.uint8)
    require(np.all(arrays['syndrome_weight']<=len(problem.model.syndrome(zero)))
        and np.all(arrays['sector']<2**len(problem.model.observables(zero)))
        and np.all(arrays['weight']<=code.n) and np.all(arrays['initial_coefficients']<=1),'compact range differs')
    for entry in entries:
        ri,ci=entry['rung'],entry['chain'];p=spec['rungs'][ri]
        require(entry['init_seed']==plans.task_seed(plan,task,ri,ci,1) and entry['sample_seed']==plans.task_seed(plan,task,ri,ci,2)
            and entry['logical_index']==plans.logical_index(spec,task[3],ci) and entry['fine_rung_index']==spec['fine_rung_indices'][ri]
            and entry['initialization_rng_consumed']==(cfg['init']=='logical_combination'),"chain seed/initialization differs")
        if entry['status']=='failed':require(entry.get('error') and not arrays['chain_ok'][ri,ci],"unrecorded chain failure");continue
        require(entry['status']=='ok' and arrays['chain_ok'][ri,ci],"chain status differs")
        state,coeff=low.logical_state(code,spec['noise'],cfg['init'],entry['logical_index'],np.random.default_rng(entry['init_seed']))
        require(np.array_equal(state,arrays['initial'][ri,ci]) and np.array_equal(coeff,arrays['initial_coefficients'][ri,ci]),"actual logical coefficients differ")
        require(problem.is_faulty(state) and math.isfinite(problem.log_prob(state,p)),"initial supported failure differs")
        final=arrays['final'][ri,ci]
        require(np.all(final<=(3 if spec['noise']=='depolarizing' else 1)) and problem.is_faulty(final)
            and math.isfinite(problem.log_prob(final,p)),'final supported failure differs')
        final_compact=t.compact(problem,final[None,:])
        require(all(arrays[key][ri,ci,-1]==final_compact[key][0] for key in ('weight','syndrome_weight','sector')),'final compact differs')
        metadata(type('Saved',(),{'metadata':entry['metadata']}),problem,p,entry['sample_seed'])
        actual=entry['metadata']['config']
        require(actual['samples']==cfg['burn']+cfg['samples'] and actual['burn_in']==0
            and actual['cache_cap']==spec['cache_cap'] and actual['cache_policy']=='lru'
            and c.canonical(actual['kernels'])==c.canonical(spec['kernels'][cfg['kernel']]),"actual sampling configuration differs")
        require(np.all(arrays['sector'][ri,ci]>0) and np.all(arrays['weight'][ri,ci]<=code.n),"saved compact support differs")
    failed=sum(entry['status']=='failed' for entry in entries)
    require(row['failed_chains']==failed and (not failed or status=='failed'),"chain failure count differs")
    if status=='ok':
        require(row['available'] is True and row['estimate'] is not None and row['interval'] is not None
            and row['bootstrap_rng_consumed']==(cfg['method']=='block'),"successful estimate/consumption differs")


def artifact_records(root,envelope,records,proof):
    root=Path(root);science=envelope['science'];expected=[tuple(task) for task in envelope['tasks']]
    require([tuple(row['task']) for row in records]==expected,"exact planned task denominator required")
    names={c.task_id(task)+ext for task in expected for ext in ('.json','.npz','.done.json')}
    require({p.name for p in (root/'tasks').iterdir()}==names,"missing or unexpected task artifact")
    for task,row in zip(expected,records):
        stem=root/'tasks'/c.task_id(task)
        require(stem.resolve().is_relative_to(root.resolve()),"task path escapes root")
        for suffix in ('.json','.npz','.done.json'):
            path=stem.with_suffix(suffix)
            require(path.resolve().is_relative_to(root.resolve()),"task payload escapes root")
            proof.track(path)
        saved=c.load_artifact(stem,dict(manifest=c.digest(science),task=list(task)))
        require(saved is not None,"task artifact missing")
        arrays,record=saved
        require(c.canonical(record)==c.canonical({k:v for k,v in row.items() if k not in OUTER_FIELDS})
            and row['artifact_marker_sha256']==c.file_hash(stem.with_suffix('.done.json')),"task summary/payload differs")
        validate_record(science,task,arrays,record)
        for key in ('inclusive_wall_seconds','peak_rss_mb'):number(row[key],positive=True)
        number(row['inclusive_cpu_seconds'])
        require(row['inclusive_wall_seconds']>=row['task_wall_seconds'] and row['inclusive_cpu_seconds']>=row['cpu_seconds'],"task clock contradiction")


def execution_binding(root,envelope,job=None):
    import submit_tile_low_noise_timing_execution as submitter
    root=Path(root);ledger=json_read(root/'submission.json');intent=json_read(root/'submission-intent.json')
    require({k:v for k,v in ledger.items() if k!='job_id'}==intent and ledger['job_id']==(job or os.environ.get('PBS_JOBID'))
        and ledger['manifest']==c.digest(envelope) and ledger['resource']==envelope['resource']
        and ledger['command']==['qsub',str(root/'timing.sh')]
        and ledger['script_sha256']==c.file_hash(root/'timing.sh')
        and ledger['upstream_completion_sha256']==c.file_hash(root/'upstream-completion-at-submit.json')
        and (root/'timing.sh').read_text()==submitter.script_text(Path(__file__).resolve().parents[1],root,envelope)
        and ledger['bundle_binding']==submitter.bundle_binding(Path(__file__).resolve().parents[1],envelope),"execution ledger/script/source differs")
    return dict(job_id=ledger['job_id'],submission_sha256=c.file_hash(root/'submission.json'),
        intent_sha256=c.file_hash(root/'submission-intent.json'),script_sha256=ledger['script_sha256'])


def recover_records(root,envelope,known,proof=None):
    """Recover valid finished artifacts after pool death; outer clocks stay unknown."""
    proof=proof or Evidence();by_task={tuple(row['task']):row for row in known};rows=[]
    for task in envelope['tasks']:
        key=tuple(task)
        if key in by_task:rows.append(by_task[key]);continue
        stem=Path(root)/'tasks'/c.task_id(task)
        row=dict(task=task,status='interrupted',started='unknown',available=False,task_wall_seconds=None,cpu_seconds=None)
        if stem.with_suffix('.done.json').exists():
            try:
                for suffix in ('.json','.npz','.done.json'):proof.track(stem.with_suffix(suffix))
                arrays,saved=c.load_artifact(stem,dict(manifest=c.digest(envelope['science']),task=task))
                validate_record(envelope['science'],key,arrays,saved)
                row=dict(saved,recovered_from_complete_artifact=True)
            except Exception as error:row.update(status='validation_failed',failure=repr(error))
        row.update(inclusive_wall_seconds=None,inclusive_cpu_seconds=None,peak_rss_mb=None)
        rows.append(row)
    proof.finish()
    return rows


def current_runtime(snapshot):
    require(snapshot['runtime']==t.runtime() and snapshot['source_sha256']==source_hashes()
        and snapshot['pythonpath']==os.environ.get('PYTHONPATH','') and snapshot['core_path']==str(Path(qec.__file__).absolute())
        and snapshot['python_path']==str(Path(sys.executable).absolute()) and snapshot['python_sha256']==c.file_hash(sys.executable),
        'terminal source/core/Python/import path changed')


def payload_evidence(root,envelope,files):
    """Exact historical validation map; this function performs no payload read."""
    root=Path(root).absolute()
    paths={str(root/'tasks'/(c.task_id(task)+suffix)) for task in envelope['tasks'] for suffix in ('.json','.npz','.done.json')}
    require(set(files)==paths,'exact task triple validation map required')
    for path,value in files.items():
        require(isinstance(value,list) and len(value)==2 and Path(value[0]).is_absolute()
            and Path(value[0]).is_relative_to(root.resolve()) and value[0]==str(Path(path).resolve()),'payload validation target differs')
        plans.require_hash(value[1])
    return dict(schema=1,verified=True,scope='exact_task_artifact_bytes_and_metadata',manifest=c.digest(envelope),
        snapshot_digest=c.digest(envelope['snapshot']),task_count=len(envelope['tasks']),tasks=envelope['tasks'],files=files)


def _completion(root,terminal,*,expected_manifest_sha256,payload=True,accepted=None):
    """Full task/PBS/current-source proof; failed tasks retain their costs."""
    root=Path(root).absolute();proof=Evidence();proof.track(root/'manifest.json',expected_manifest_sha256)
    envelope=read_plan(root)
    ledger=proof.read(root/'submission.json',None if payload else accepted['submission_sha256'])
    intent=proof.read(root/'execution-intent.json')
    for path,(target,sha) in envelope['snapshot'].get('files',{}).items():
        require(str(Path(path).resolve())==target,'current input target differs');proof.track(path,sha)
    pbs=proof.pin(terminal);job=ledger['job_id']
    terminal_job=pbs['Jobs'][job]
    if terminal_job.get('job_state')=='F' and terminal_job.get('Exit_status')!=0:
        require(envelope['mode']=='capacity','failed main execution is not capacity evidence')
        binding=execution_binding(root,envelope,job)
        check_pbs(ledger,terminal_job,terminal=True,hostname=intent['hostname'],allow_failure=True)
        require(intent['manifest']==c.digest(envelope) and intent['pbs_job_id']==job and intent['submission_binding']==binding,'failed capacity identity differs')
        actual=proof.read(root/'native_preflight.json');profile=proof.read(root/'platform_profile.json')
        native.trace_audit.validate_platform(profile,actual['profile'])
        require(actual['manifest']==c.digest(envelope) and actual['pbs_job_id']==job and actual['hostname']==intent['hostname'],'failed capacity native identity differs')
        if not payload:
            saved=proof.pin(accepted['failure_evidence'])
            require(saved['root']==str(root) and saved['manifest_sha256']==expected_manifest_sha256 and saved['terminal']==terminal
                and saved['job_id']==job and saved['summary']['execution_infeasible_capacity_envelope'] is True
                and saved['summary']['execution_complete'] is False
                and [row['task'] for row in saved['summary']['records']]==envelope['tasks'],'accepted failed capacity binding differs')
            for path,(target,sha) in saved['input_files'].items():
                if Path(path).is_relative_to(root/'tasks'):continue
                require(str(Path(path).resolve())==target,'accepted failure input target differs');proof.track(path,sha)
            proof.finish();current_runtime(envelope['snapshot'])
            return dict(saved,input_files=proof.files,payloads_rehashed_now=False,
                scope='Externally pinned failed-capacity full verification accepted; current raw payloads not reaudited.')
        recovered=recover_records(root,envelope,[],proof)
        require(all(row['status']!='validation_failed' for row in recovered),'capacity task provenance failed')
        for path in sorted(root.rglob('*')):
            if path.is_file():proof.track(path)
        proof.finish()
        current_runtime(envelope['snapshot'])
        # A killed estimator has unknown cost and no usable shorter substitute.
        # Any nonzero terminal exit blocks this declared 24-hour envelope.
        summary=dict(execution_complete=False,execution_infeasible_capacity_envelope=True,
            records=recovered,known_task_wall_seconds_lower_bound=sum(row['task_wall_seconds'] or 0 for row in recovered),
            known_task_cpu_seconds_lower_bound=sum(row['cpu_seconds'] or 0 for row in recovered),
            terminal_exit_status=terminal_job['Exit_status'],costs_complete=False,
            warning='The declared capacity execution failed; this is not a proof of fundamental computational impossibility or a diagnosis of timeout/OOM.')
        return dict(root=str(root),manifest_sha256=expected_manifest_sha256,terminal=terminal,summary=summary,
            input_files=proof.files,job_id=job,payloads_rehashed_now=True,scope='Failed declared capacity envelope; current artifacts retained, unknown estimator costs.')
    summary=proof.read(root/'summary.json',None if payload else accepted['summary_sha256']);actual=proof.read(root/'native_preflight.json')
    job=ledger['job_id'];binding=execution_binding(root,envelope,job)
    for name in ('submission-intent.json','timing.sh','upstream-completion-at-submit.json'):proof.track(root/name)
    require(ledger['upstream_completion_sha256']==c.file_hash(root/'upstream-completion-at-submit.json'),'upstream submission proof differs')
    scientific=proof.read(root/'scientific-summary.json')
    require(summary['scientific_summary_sha256']==c.file_hash(root/'scientific-summary.json')
        and all(summary.get(key)==value for key,value in scientific.items()),'scientific summary binding differs')
    require(summary['execution_complete'] is True and summary['terminal_binding_valid'] is True
        and summary['manifest']==intent['manifest']==actual['manifest']==c.digest(envelope)
        and summary['pbs_job_id']==intent['pbs_job_id']==actual['pbs_job_id']==job
        and summary['hostname']==intent['hostname']==actual['hostname']
        and summary['submission_binding']==intent['submission_binding']==binding,"complete execution identity differs")
    check_pbs(ledger,pbs['Jobs'][job],terminal=True,hostname=actual['hostname'])
    profile=proof.read(root/'platform_profile.json');fixture=proof.read(root/'platform_fixture.json')
    native.trace_audit.validate_platform(profile,actual['profile'])
    require(profile['fixture']==c.digest(fixture) and envelope['native_input_digests']=={
        'platform_profile':c.digest(profile),'platform_fixture':c.digest(fixture)},"actual native inputs differ")
    require(summary['native_sha256']==c.file_hash(root/'native_preflight.json')
        and summary['execution_intent_sha256']==c.file_hash(root/'execution-intent.json')
        and summary['snapshot_digest']==c.digest(envelope['snapshot']),"terminal native/intent/input binding differs")
    recorded=summary['payload_verification']
    require(c.canonical(recorded)==c.canonical(payload_evidence(root,envelope,recorded['files'])),'saved full payload validation proof differs')
    require([row['task'] for row in summary['records']]==envelope['tasks']
        and summary['planned_tasks']==summary['recorded_tasks']==len(envelope['tasks'])
        and all(row['status'] in ('ok','failed','unavailable') for row in summary['records']),'saved task census differs')
    if payload:
        artifact_records(root,envelope,summary['records'],proof)
        require(recorded['files']=={path:proof.files[path] for path in recorded['files']},'current payload differs from compute validation')
    require(summary['failed']==sum(row['status']=='failed' for row in summary['records'])
        and summary['unavailable']==sum(not row['available'] for row in summary['records']),"failure/availability denominator differs")
    proof.finish()
    current_runtime(envelope['snapshot'])
    return dict(root=str(root),manifest_sha256=expected_manifest_sha256,terminal=terminal,summary=summary,
        input_files=proof.files,job_id=job,payloads_rehashed_now=payload,
        scope='Full current task payloads and formal PBS/native/seed metadata, not a replay of all physical states.' if payload else
        'Externally pinned compute validation and terminal metadata accepted; current raw payloads not reaudited.')


def completed(root,terminal,*,expected_manifest_sha256):
    """Full current payload verification, including recorded failures and costs."""
    return _completion(root,terminal,expected_manifest_sha256=expected_manifest_sha256)


def accepted_capacity(reference):
    """Metadata-only acceptance of externally pinned compute validation evidence."""
    root=Path(reference['root']).absolute()
    envelope=read_plan(root)
    require(envelope['mode']=='capacity' and len(envelope['tasks'])==2,'two-estimator capacity authority required')
    plans.require_hash(reference['submission_sha256'])
    return _completion(root,reference['terminal'],expected_manifest_sha256=reference['manifest_sha256'],payload=False,accepted=reference)


def revalidate_capacity(envelope):
    """Re-read both measured estimators before starting any new estimator."""
    reference=envelope.get('capacity_reference')
    if reference is None:return
    actual=completed(reference['root'],reference['terminal'],expected_manifest_sha256=reference['manifest_sha256'])
    expected=envelope['capacity_proof']
    require(actual['summary']==expected['summary'] and actual['job_id']==expected['job_id']
        and all(actual['input_files'].get(path)==binding for path,binding in expected['input_files'].items()),'capacity payload or accepted proof changed before compute')


def envelope_value(config,role,identity,capacity=None,partition_index=None):
    require(role in plans.STAGES and len(identity)==3 and all(type(x) is int for x in identity),"fixed role/identity required")
    bundle,snapshot=inputs(config);science=bundle['plans'][role]
    selected=[tuple(task) for task in plans.tasks(science) if tuple(task[:3])==tuple(identity)]
    require(selected,"selected nonempty execution identity required")
    mode='capacity' if role.endswith('capacity') else 'benchmark';cap=None;decision=None;status='ready'
    if mode=='capacity':
        require(capacity is None and partition_index is None and len(selected)==2,"two-estimator capacity required")
        res=capacity_resources();tasks=selected
    else:
        require(capacity is not None,"verified full-dimensional capacity required")
        cap=accepted_capacity(capacity)
        previous=json_read(Path(capacity['root'])/'manifest.json')
        expected_role=role.rsplit('.',1)[0]+'.capacity'
        require(previous['role']==expected_role and previous['identity']==list(identity)
            and previous['snapshot']==snapshot and previous['science']==bundle['plans'][expected_role],"capacity configuration/source differs")
        decision=resource_plan(cap['summary']);status=decision['status']
        if status=='ready':
            require(type(partition_index) is int and 0<=partition_index<len(decision['partitions']),"fixed partition index required")
            part=decision['partitions'][partition_index];res=part['resource']
            tasks=[task for task in selected if task[3] in part['replicates']]
        else:require(partition_index is None,"infeasible outcome cannot select partition");res=None;tasks=[]
    return dict(schema=1,purpose='low_noise_independent_timing_execution',config=config,role=role,mode=mode,identity=list(identity),
        science=science,snapshot=snapshot,capacity_reference=capacity,capacity_proof=cap,partition_index=partition_index,
        resource_decision=decision,planning_status=status,resource=res,tasks=[list(task) for task in tasks],
        planned_replicates=192 if mode=='benchmark' else 2,
        unexecuted_replicates=list(range(192)) if mode=='benchmark' and status!='ready' else [],
        outcomes=[dict(identity=[row[k] for k in ('case','target_index','epsilon_index')],selection_status=row['status'],
            planning_status=status if tuple(row[k] for k in ('case','target_index','epsilon_index'))==tuple(identity) else row['planning_status']) for row in science['rows']],
        native_input_digests=snapshot['native_input_digests'],warning=WARNING)


def prepare(root,config,role,identity,capacity=None,partition_index=None):
    root=Path(root).absolute();require(not root.exists(),'new output root required')
    value=envelope_value(config,role,identity,capacity,partition_index)
    require(not any(Path(path).resolve().is_relative_to(root.resolve()) for path in value['snapshot']['files']),"execution root overlaps inputs")
    root.mkdir(parents=True,exist_ok=False);save_new(root/'manifest.json',value)
    for key in ('platform_profile','platform_fixture'):
        source=Path(config[key]['path']);raw=source.read_bytes();require(hashlib.sha256(raw).hexdigest()==config[key]['sha256'],'native input changed')
        with (root/(key+'.json')).open('xb') as stream:stream.write(raw)
    return value


def read_plan(root):
    root=Path(root).absolute();value=json_read(root/'manifest.json')
    expected=envelope_value(value['config'],value['role'],value['identity'],value['capacity_reference'],value['partition_index'])
    require(c.canonical(value)==c.canonical(expected),"execution envelope/source/current input differs")
    for key,sha in value['native_input_digests'].items():require(c.digest(json_read(root/(key+'.json')))==sha,'native fixture changed')
    require(str(Path(sys.executable).absolute())==value['snapshot']['python_path'],'actual Python invocation path differs')
    return value


def qstat(job,runner=subprocess.run):
    data=json.loads(runner(['qstat','-x','-f','-F','json',job],capture_output=True,text=True,check=True,timeout=30).stdout)
    keys={'job_state','Exit_status','run_count','Submit_arguments','Resource_List','resources_used','exec_host','exec_vnode','Job_Name','stime','obittime'}
    return {'Jobs':{job:{k:v for k,v in data['Jobs'][job].items() if k in keys}}}


def run(root,*,scheduler=subprocess.run):
    require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',os.environ.get('PBS_JOBID','')) and all(os.environ.get(k)==v for k,v in THREADS.items()),'qsub and fixed single-thread environment required')
    root=Path(root).absolute()
    require(not any((root/name).exists() for name in ('execution-intent.json','tasks','summary.json','scientific-summary.json','native_preflight.json')),'fresh standalone execution required')
    started=time.perf_counter();envelope=read_plan(root)
    require(envelope['planning_status']=='ready' and envelope['tasks'],'execution not ready')
    binding=execution_binding(root,envelope);job=os.environ['PBS_JOBID'];host=socket.gethostname()
    actual=qstat(job,scheduler);check_pbs(json_read(root/'submission.json'),actual['Jobs'][job],terminal=False,hostname=host)
    save_new(root/'actual-pbs-start.json',actual)
    intent=dict(manifest=c.digest(envelope),pbs_job_id=job,hostname=host,submission_binding=binding)
    save_new(root/'execution-intent.json',intent)
    records=[];pool_seconds=None;failure=None;complete=False;verified_payload=None
    try:
        revalidate_capacity(envelope)
        native.native_preflight(root,envelope)
        pool_start=time.perf_counter()
        records=c.parallel_map(run_task,[(str(root),envelope['science'],tuple(task)) for task in envelope['tasks']],envelope['resource']['workers'])
        pool_seconds=time.perf_counter()-pool_start;records.sort(key=lambda row:row['task'])
        proof=Evidence();artifact_records(root,envelope,records,proof);proof.finish()
        verified_payload=payload_evidence(root,envelope,proof.files)
        require(read_plan(root)==envelope and execution_binding(root,envelope)==binding,'terminal execution/source/input changed')
        current_runtime(envelope['snapshot'])
        actual_end=qstat(job,scheduler);check_pbs(json_read(root/'submission.json'),actual_end['Jobs'][job],terminal=False,hostname=host)
        save_new(root/'actual-pbs-end.json',actual_end)
        complete=True
    except Exception as error:failure=dict(error=repr(error),traceback=traceback.format_exc())
    # Record every planned identity, even when a broken worker/pool yielded no return.
    if not complete:
        records=recover_records(root,envelope,records)
    scientific=dict(outcomes=envelope['outcomes'],planned_tasks=len(envelope['tasks']),recorded_tasks=len(records),
                    failed=sum(row['status']=='failed' for row in records),unavailable=sum(not row['available'] for row in records),
                    execution_complete=complete,all_estimates_available=complete and all(row['available'] for row in records))
    save_new(root/'scientific-summary.json',scientific)
    elapsed=time.perf_counter()-started
    summary=dict(**intent,**scientific,records=records,terminal_binding_valid=complete,failure=failure,
        pool_wall_seconds=pool_seconds,outside_pool_wall_seconds=None if pool_seconds is None else elapsed-pool_seconds,
        parent_peak_rss_mb=c.peak_rss_mb(),execution_wall_seconds=elapsed,
        payload_verification=verified_payload if complete else None,
        costs_complete=complete,known_task_wall_seconds_lower_bound=sum(row['task_wall_seconds'] or 0 for row in records),
        known_task_cpu_seconds_lower_bound=sum(row['cpu_seconds'] or 0 for row in records),
        execution_intent_sha256=c.file_hash(root/'execution-intent.json'),snapshot_digest=c.digest(envelope['snapshot']),
        native_sha256=c.file_hash(root/'native_preflight.json') if (root/'native_preflight.json').exists() else None,
        scientific_summary_sha256=c.file_hash(root/'scientific-summary.json'),warning=WARNING)
    save_new(root/'summary.json',summary)
    if not complete:raise RuntimeError('incomplete/validation-failed timing execution; preserve all outputs')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','run','verify'));parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--config',type=Path);args=parser.parse_args()
    if args.command=='prepare':result=prepare(args.root,**json_read(args.config))
    elif args.command=='verify':
        require(os.environ.get('PBS_JOBID'),'full task verification requires a compute job')
        result=completed(args.root,**json_read(args.config))
    else:result=run(args.root)
    print(json.dumps({key:result[key] for key in ('role','identity','planning_status','execution_complete','job_id') if key in result}))


if __name__=='__main__':main()
