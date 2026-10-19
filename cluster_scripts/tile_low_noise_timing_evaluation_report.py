"""Bounded-reference reports for all 24 fixed independent low-noise cohorts.

Numerical helpers do not certify input evidence. The saved-data entry point binds
selection, seed census, WSS audit and complete execution readers before assessing
any points. Missing cohorts remain explicit and never become successful subsets.
"""
import argparse
import ast
from collections import Counter
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import sys
import subprocess
from types import SimpleNamespace

import calibration as c
import tile_timing_metrics as metrics
import tile_weight_reference_comparison as bounded
import tile_low_noise_timing_execution as execution
import tile_low_noise_timing_plan as plans
import tile_low_noise_timing_selection as selector
import tile_low_noise_timing_census as census
import tile_weight_reference_audit_run as reference_run
import tile_reference_source_binding as source_binding
from tile_low_noise_audited_collection import Evidence

IDENTITIES = [(case, target, epsilon) for case in range(4) for target in range(3) for epsilon in range(2)]
CLOCKS = ("task_wall_seconds", "cpu_seconds", "inclusive_wall_seconds", "inclusive_cpu_seconds")
COMPLETE = {"completed", "completed_with_recorded_task_failures"}
REPORT_PURPOSE = "low_noise_independent_timing_evaluation"
WARNING = (bounded.WARNING + " Finite WSS bounds are shared by selection, budgeting and evaluation. "
    "Independent BAR mixing diagnostics were not collected; flagged/undefined placeholders are not measurements. "
    "Ratios are full-cohort mean MC / mean BAR costs, separately by clock, conditional on both empirical "
    "precision gates. Task clocks exclude artifact writes; inclusive clocks include them. Capacity and pool/PBS "
    "costs are separate, never apportioned. Host/partition differences are uncorrected. No fastest-setting, "
    "minimum-time-to-accuracy, population-time-ratio, population-RMSE or nominal-coverage certification.")
METADATA = ('manifest.json','submission-intent.json','submission.json','timing.sh','execution-intent.json',
    'native_preflight.json','platform_profile.json','platform_fixture.json','upstream-completion-at-submit.json',
    'scientific-summary.json','summary.json','actual-pbs-start.json','actual-pbs-end.json')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(row):
    return tuple(row[key] for key in ("case", "target_index", "epsilon_index"))


def read_pin(pin, proof):
    require(isinstance(pin, dict) and isinstance(pin.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]), "external SHA256 pin required")
    require(proof.track(pin["path"]) == pin["sha256"], "external input pin differs")
    return proof.read(pin["path"])


def runtime():
    from importlib.metadata import version
    return dict(runtime=c.runtime(),scipy=version('scipy'),python_path=str(Path(sys.executable).absolute()),
        python_sha256=c.file_hash(sys.executable))


def selector_evidence(descriptor, selection_pin, proof):
    """Bind the parent's one-shot selector envelope, not an invented native run."""
    require(set(descriptor) == {"prepared","intent","submission","script","execution","completion","terminal"},
        "exact selector execution descriptor required")
    values = {key:read_pin(pin,proof) for key,pin in descriptor.items() if key != "script"}
    script = descriptor["script"]
    require(proof.track(script["path"]) == script["sha256"], "selector script bytes differ")
    plan, intent, ledger, actual, end, pbs = (values[key] for key in
        ("prepared","intent","submission","execution","completion","terminal"))
    report = read_pin(selection_pin,proof)
    require(plan["schema"] == 1 and plan["purpose"] == "low_noise_timing_selector_execution", "wrong selector envelope")
    read_pin(plan["input"],proof)
    argv = [str(Path(sys.executable).absolute()),str(Path(selector.__file__).absolute()),"--input",plan["input"]["path"],
        "--expected-sha256",plan["input"]["sha256"],"--output",selection_pin["path"]]
    require(plan["report_path"] == selection_pin["path"] and plan["selector_argv"] == argv,
        "actual selector argv differs")
    require(Path(script["path"]).read_text().splitlines().count(shlex.join(argv)) == 1, "single pinned selector command required")
    require({key:value for key,value in ledger.items() if key != "job_id"} == intent
        and ledger["manifest"] == c.digest(plan) and ledger["script_sha256"] == script["sha256"]
        and ledger["command"] == ["qsub",script["path"]] and ledger["resource"] == plan["resource"],
        "selector submission/intent/script/resource differs")
    require(plan["source_sha256"] == selector.source_hashes() == report["source_sha256"]
        and plan["runtime"] == runtime() and plan["python_path"] == str(Path(sys.executable).absolute())
        and plan["python_sha256"] == proof.track(sys.executable), "selector source/runtime/Python differs")
    require(bool(plan["native_binding"]), "fixed selector native bindings required")
    for mapping in (plan["source_sha256"],plan["native_binding"]):
        for path,digest in mapping.items():require(proof.track(path) == digest, "selector fixed source/native input differs")
    wanted = dict(manifest=c.digest(plan),pbs_job_id=ledger["job_id"],hostname=actual["hostname"],
        input_sha256=plan["input"]["sha256"],selector_argv=argv,
        **{key:plan[key] for key in ("source_sha256","runtime","python_path","python_sha256","native_binding")})
    require(actual == wanted and end == dict(wanted,report_sha256=selection_pin["sha256"],complete=True)
        and report["input_manifest_sha256"] == plan["input"]["sha256"], "selector start/end/report binding differs")
    execution.check_pbs(ledger,pbs["Jobs"][ledger["job_id"]],terminal=True,hostname=actual["hostname"])
    return dict(job_id=ledger["job_id"],input_sha256=plan["input"]["sha256"],report_sha256=selection_pin["sha256"],
        descriptor=descriptor,resource=ledger["resource"],pbs=pbs["Jobs"][ledger["job_id"]],
        fresh_native_probe_claimed=False,scope="Pinned selector execution and recorded native bindings only.")


def census_evidence(descriptor, bundle, proof):
    """Accept a zero-allocation bridge without claiming a new full census."""
    selected = sum(row["status"] == "selected" for row in bundle["selection"]["rows"])
    allocations = sum(plan["planned_seed_entries"] for plan in bundle["plans"].values())
    if selected == 0 and allocations == 0:
        require(set(descriptor) == {"root","manifest"}, "zero-allocation bridge descriptor required")
        root = Path(descriptor["root"]).absolute()
        require(Path(descriptor["manifest"]["path"]).absolute() == root/"manifest.json", "bridge manifest path differs")
        pinned = read_pin(descriptor["manifest"],proof)
        checked = bridge_noop_state(root,pinned,proof)
        plan = pinned
        require(checked == census.state_only(plan) and plan["status"] == "not_required_no_allocations"
            and plan["selected_rows"] == plan["new_allocations"] == 0
            and plan["scientific_bundle_digest"] == c.digest(bundle)
            and plan["registry_digest"] == c.digest(bundle["registry"])
            and plan["selection_sha256"] == bundle["selection_sha256"]
            and plan["baseline_verified_namespaces"] == 56 and plan["new_namespaces_audited"] is False
            and plan["formal_census_descriptor"] is None, "zero-allocation bridge differs")
        # The bridge itself validates original externally pinned inputs; retain all
        # current before/after targets in this report too when present.
        for mapping in (plan.get("input_sha256",{}),plan.get("source_sha256",{})):
            for path,digest in mapping.items():require(proof.track(path) == digest, "bridge fixed input differs")
        return dict(census.state_only(plan),descriptor=descriptor)
    require(selected > 0 and allocations > 0, "selected allocation count contradicts census")
    foreign = execution.Evidence()
    accepted = execution.formal_census(descriptor,bundle,foreign)
    foreign.finish()
    adopt_files(foreign.files,proof)
    return dict(accepted,status="completed",new_namespaces_audited=True)


def bridge_noop_state(root, plan, proof):
    """Use the immutable bridge's own invocation environment, read-only."""
    config=read_pin(plan['config_pin'],proof)
    require(config['purpose']=='low_noise_timing_census_input','fixed bridge input required')
    executable=Path(config['python_path'])
    require(executable.is_absolute() and proof.track(executable)==config['python_sha256'],'bridge Python pin differs')
    source=Path(census.__file__).resolve()
    require(str(source) in config['source_sha256'],'bridge module not in accepted source map')
    for mapping in (config['source_sha256'],config['core_sha256']):
        for path,digest in mapping.items():require(proof.track(path)==digest,'bridge source/core pin differs')
    env=dict(os.environ,PYTHONPATH=config['pythonpath'],PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='0',**census.THREADS)
    code=('import json,sys; from pathlib import Path; import tile_low_noise_timing_census as b; '
        'assert Path(b.__file__).resolve()==Path(sys.argv[2]).resolve(); '
        'print(json.dumps(b.state_only(b.read_plan(Path(sys.argv[1])))))')
    result=subprocess.run([str(executable),'-c',code,str(root),str(source)],env=env,cwd=str(source.parent),
        check=True,capture_output=True,text=True,timeout=30)
    require(not result.stderr.strip(),'bridge validation emitted unexpected stderr')
    # Its accepted context is read-only; no run, seal, pilot or submit operation.
    proof.finish()
    return json.loads(result.stdout)


def adopt_files(files, proof):
    for path,(target,digest) in files.items():
        require(str(Path(path).resolve()) == target and proof.track(path) == digest, "reader input changed")


def source_files():
    pending=[Path(__file__).stem];found={}
    while pending:
        name=pending.pop()
        if name in found:continue
        spec=importlib.util.find_spec(name)
        require(spec is not None and spec.origin is not None,"missing report source closure")
        path=Path(spec.origin).absolute();found[name]=path
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            names=([a.name.split('.')[0] for a in node.names] if isinstance(node,ast.Import)
                else [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else [])
            for module in names:
                candidate=importlib.util.find_spec(module)
                if candidate and candidate.origin and Path(candidate.origin).parent.name=='cluster_scripts':pending.append(module)
    package=Path(c.qec.__file__).resolve().parent
    found.update({"package/"+path.relative_to(package).as_posix():path for path in package.rglob('*.py')})
    return found


def sources(proof):
    return {str(path):proof.track(path) for path in source_files().values()}


def chunk_census(root, expected=None):
    """Names/targets only, used around the PBS-only current raw hash pass."""
    require(bool(os.environ.get('PBS_JOBID')),'WSS chunk census requires PBS')
    root=Path(root).absolute();directory=root/'chunks'
    entries=[]
    for path in directory.iterdir():
        require(path.is_file() and path.resolve().is_relative_to(root.resolve()),'unsafe WSS chunk member')
        entries.append([path.relative_to(root).as_posix(),str(path.resolve())])
    entries.sort()
    if expected is not None:require({entry[0] for entry in entries}==set(expected),'WSS consumed chunk census differs')
    return dict(root=str(root),resolved_root=str(root.resolve()),files=len(entries),entries_digest=c.digest(entries))


def reference_evidence(config, selection, proof, *, full=False):
    """Join all saved audit reports; full mode rehashes their consumed raw bytes."""
    require(not full or bool(os.environ.get("PBS_JOBID")), "reference payload validation requires PBS")
    root=Path(config["root"]).absolute();audit_root=Path(config["audit_root"]).absolute()
    pins=config["input_sha256"]
    require(pins and root.resolve()!=audit_root.resolve(), "separate fixed reference roots required")
    def pinned(path):
        path=Path(path).absolute()
        require(str(path) in pins, "external WSS metadata pin missing")
        return read_pin(dict(path=str(path),sha256=pins[str(path)]),proof)
    context=pinned(root/'manifest.json');original=pinned(root/'summary.json')
    plan=pinned(audit_root/'manifest.json');summary=pinned(audit_root/'summary.json')
    actual=pinned(audit_root/'native_preflight.json');intent=pinned(audit_root/'execution-intent.json')
    require(plan['reference_root']==str(root.resolve()) and plan['reference_context']==context,
        "current WSS audit context differs")
    reference_sources=source_binding.reference_source_context(plan['source_sha256'],reference_run.source_hashes(),audit_root,
        SimpleNamespace(reference=reference_run,audit=reference_run.audit,c=c),proof)
    require(summary['manifest']==c.digest(plan) and summary['tasks']==16 and summary['failed']==0
        and summary['all_conditions_audited'] is True and summary['terminal_binding_valid'] is True
        and summary['phase_failure'] is None and summary['phase_failures']==[]
        and [row['condition'] for row in summary['records']]==list(range(16))
        and all(row['status']=='ok' for row in summary['records']), "complete sixteen-condition WSS audit required")
    require(intent['manifest']==c.digest(plan) and intent['reference_context']==c.digest(context)
        and intent['conditions']==list(range(16)) and intent['workers']==16 and intent['hostname']
        and {key:value for key,value in actual.items() if key not in ('profile','original_pbs_job_id')}==intent
        and actual['original_pbs_job_id']==plan['original_pbs_job_id']
        and actual['pbs_job_id']==summary['pbs_job_id']
        and c.digest(actual['profile'])==plan['actual_native_profile_digest']
        and summary['execution_intent_sha256']==proof.track(audit_root/'execution-intent.json')
        and summary['native_preflight_sha256']==proof.track(audit_root/'native_preflight.json'), "WSS native/execution binding differs")
    for path,digest in plan['source_sha256'].items():require(proof.track(path)==digest,"WSS current source differs")
    for name,digest in plan['input_sha256'].items():
        path=root/name
        require(path.resolve().is_relative_to(root.resolve()) and proof.track(path)==digest,"WSS current metadata differs")
    terminal=read_pin(config['terminal'],proof)
    jobs=[]
    for base,job,manifest,exits in ((root,plan['original_pbs_job_id'],c.digest(context),(0,1) if original['unavailable'] else (0,)),
        (audit_root,summary['pbs_job_id'],c.digest(plan),(0,))):
        ledger=pinned(base/'submission.json');submission_intent=pinned(base/'submission-intent.json')
        require({k:v for k,v in ledger.items() if k!='job_id'}==submission_intent,"WSS parent receipt/intent differs")
        require(ledger['command'][1] in pins,"WSS actual script external pin required")
        require(proof.track(ledger['command'][1])==pins[ledger['command'][1]],"WSS actual script pin differs")
        jobs.append(selector.check_terminal(proof,terminal,base/'submission.json',job,manifest,exits))
    require(set(terminal['Jobs'])=={item['job_id'] for item in jobs},"exact WSS generation/audit terminal set required")
    binding={item['reference_condition']:item for item in selection['calibration_bindings']}
    require(set(binding)=={4*case+target+1 for case in range(4) for target in range(3)},"twelve selector WSS bindings required")
    references={};audit_digests={};raw_pins={}
    for index in range(16):
        base=audit_root/'conditions'/str(index)
        for suffix in ('.json','.npz','.done.json'):
            path=base.with_suffix(suffix)
            require(str(path) in pins and proof.track(path)==pins[str(path)],"external WSS report artifact pin differs")
        arrays,record=proof.artifact(base,dict(manifest=c.digest(plan),condition=index))
        require(not arrays and record['status']=='ok'
            and summary['condition_marker_sha256'][str(index)]==proof.track(base.with_suffix('.done.json'))
            and {key:value for key,value in record.items() if key!='report'}==summary['records'][index],"WSS report/summary differs")
        report=record['report']
        source_binding.reference_sources(report['source_sha256'],reference_sources['sources'],
            reference_sources['saved_root'],reference_sources['current_root'],proof)
        reference_run.report_binding(plan,index,dict(report,source_sha256=reference_sources['sources']))
        audit_digests[str(index)]=c.digest(report)
        for name,digest in report['input_sha256'].items():
            require(name not in raw_pins or raw_pins[name]==digest,"inconsistent WSS consumed hashes")
            raw_pins[name]=digest
        if index in binding:
            chosen=binding[index]
            require(chosen['reference_context']==c.digest(context) and chosen['reference_audit_digest']==c.digest(report),
                "selection and evaluation WSS audit differ")
            case=index//4;target=index%4-1
            # Explicit missing rows satisfy the fixed-denominator numeric API.
            # This temporary assessment is discarded, never reported as execution.
            missing=[dict(replicate=i,estimate=None,interval=None,available=False,
                flagged=False,undefined=False,high_rhat=False,low_ess=False,failure=None) for i in range(192)]
            checked=bounded.compare_condition(missing,192,report['condition'],case=case,target_prior=(.01,.003,.001)[target])
            description=checked['reference'] or dict(interval=None,full_point_estimate=None)
            require(description['interval']==chosen['reference_interval'],"selector WSS interval differs")
            references[(case,target)]=dict(description,planned_trials=report['condition']['planned_trials'],
                available_trials=report['condition']['available_trials'],failed_chunks=report['condition']['failed_chunks'])
    census_value=None
    if full:
        census_value=chunk_census(root,{name for name in raw_pins if name.startswith('chunks/')})
        for name,digest in raw_pins.items():
            path=root/name
            require(path.resolve().is_relative_to(root.resolve()) and proof.track(path)==digest,"current WSS consumed payload differs")
    return references,dict(audit_reports=16,audit_report_digests=audit_digests,terminal=jobs,
        consumed_input_count=len(raw_pins),current_raw_payloads_rehashed=full,physical_states_redecoded=False,
        chunk_census=census_value,fresh_native_probe_executed=False,summary_sha256=proof.track(audit_root/'summary.json'))


def root_snapshot(item, role, key, bundle, proof):
    """Metadata only: main read_plan would recursively scan capacity payloads."""
    root=Path(item['root']).absolute()
    require(not root.exists() or root.is_dir(),'execution root must be a directory')
    files={name:proof.track(root/name) for name in METADATA if (root/name).exists()}
    tasks=root/'tasks'
    names=sorted(path.name for path in tasks.iterdir()) if tasks.exists() else None
    state='not_prepared';manifest=None;terminal=None
    if 'manifest.json' in files:
        require(files['manifest.json']==item.get('manifest_sha256'),'external execution manifest pin required')
        manifest=proof.read(root/'manifest.json')
        require(manifest['purpose']=='low_noise_independent_timing_execution'
            and manifest['role']==role and manifest['identity']==list(key)
            and manifest['science']==bundle['plans'][role], 'execution scientific plan/role/identity differs')
        state='not_started'
    if any(name in files for name in ('submission-intent.json','submission.json','execution-intent.json','summary.json')) or names is not None:
        require(manifest is not None,'execution without fixed manifest')
        state='incomplete'
    if 'submission.json' in files:
        require('submission' in item,'external parent receipt pin required')
        ledger=read_pin(item['submission'],proof)
        require(Path(item['submission']['path']).absolute()==root/'submission.json'
            and ledger==proof.read(root/'submission.json'),'parent receipt path differs')
        require('terminal' in item,'latest externally pinned PBS observation required')
        terminal=read_pin(item['terminal'],proof)
        require(set(terminal['Jobs'])=={ledger['job_id']},'exact execution PBS job observation required')
        job=terminal['Jobs'][ledger['job_id']]
        if job.get('job_state')=='F':
            require(type(job.get('Exit_status')) is int,'terminal exit must be an integer')
            if manifest['mode']=='capacity' and job['Exit_status']!=0:
                state='complete_candidate'
            elif job['Exit_status']==0 and 'summary.json' in files:
                summary=proof.read(root/'summary.json')
                if summary.get('execution_complete') is True:state='complete_candidate'
    return dict(root=str(root),resolved_root=str(root.resolve()),state=state,files=files,
        task_entries=names,manifest=manifest,terminal=terminal)


def inputs(config, proof):
    bundle=read_pin(config['scientific_bundle'],proof)
    plans.validate_plans(bundle,expected_registry_digest=config['registry_digest'])
    selection=read_pin(config['selection'],proof)
    require(selection==bundle['selection'] and config['selection']['sha256']==bundle['selection_sha256'],
        'immutable selection bytes differ from scientific plans')
    selector_proof=selector_evidence(config['selector_execution'],config['selection'],proof)
    census_proof=census_evidence(config['census'],bundle,proof)
    refs,reference_proof=reference_evidence(config['reference'],selection,proof)
    rows=bundle['plans']['low_timing.mc.benchmark']['rows']
    require([identity(row) for row in rows]==IDENTITIES and [tuple(item['identity']) for item in config['cohorts']]==IDENTITIES,
        'all 24 ordered planning and execution outcomes required')
    snapshots=[];roots=[]
    for row,item in zip(rows,config['cohorts']):
        key=identity(row);entry=dict(identity=list(key))
        for method in ('mc','bar'):
            values=item[method]
            require(set(values)=={'capacity','partitions'},'explicit capacity and all partition roots required')
            eligible=row['status']=='selected' and row['planning_status']=='ready'
            if not eligible:
                require(values==dict(capacity=None,partitions=[]),'unselected row cannot allocate execution roots')
                entry[method]=dict(capacity=None,partitions=[])
                continue
            require(values['capacity'] is not None,'selected row needs its fixed capacity root')
            cap=root_snapshot(values['capacity'],f'low_timing.{method}.capacity',key,bundle,proof)
            parts=[root_snapshot(part,f'low_timing.{method}.benchmark',key,bundle,proof) for part in values['partitions']]
            roots += [Path(cap['root']).resolve(),*[Path(part['root']).resolve() for part in parts]]
            entry[method]=dict(capacity=cap,partitions=parts)
        snapshots.append(entry)
    require(len(set(roots))==len(roots) and all(not a.is_relative_to(b) for a in roots for b in roots if a!=b),
        'execution roots must be disjoint')
    return dict(bundle=bundle,rows=rows,references=refs,selector=selector_proof,census=census_proof,
        reference_evidence=reference_proof,snapshots=snapshots)


def input_roots(config):
    roots=[Path(config['reference'][key]).resolve() for key in ('root','audit_root')]
    for row in config['cohorts']:
        for method in ('mc','bar'):
            values=row[method]
            roots.extend(Path(item['root']).resolve() for item in ([values['capacity']] if values['capacity'] else [])+values['partitions'])
    if 'root' in config['census']:roots.append(Path(config['census']['root']).resolve())
    return roots


def outside_inputs(output, config, proof):
    output=Path(output).resolve()
    require(all(not output.is_relative_to(root) and not root.is_relative_to(output) for root in input_roots(config)),
        'report output overlaps input roots')
    require(all(output!=Path(path).resolve() and not Path(path).resolve().is_relative_to(output) for path in proof.hashes),
        'report output overlaps pinned inputs')


def save_new(path, value):
    path=Path(path)
    with path.open('xb') as stream:stream.write(c.canonical(value)+b'\n')


def prepare(config_path, expected_sha256, output_plan):
    output_plan=Path(output_plan).absolute();target=output_plan.resolve()
    require(not output_plan.exists() and not output_plan.is_symlink(),'preserve existing report plan')
    proof=Evidence();config=read_pin(dict(path=str(config_path),sha256=expected_sha256),proof)
    source=sources(proof);context=inputs(config,proof);outside_inputs(output_plan,config,proof)
    result=dict(schema=1,purpose='low_noise_timing_report_plan',config=config,
        config_pin=dict(path=str(Path(config_path).absolute()),sha256=expected_sha256),
        snapshots=context['snapshots'],source_sha256=source,runtime=runtime(),
        input_sha256=proof.hashes,input_targets=proof.targets)
    proof.finish();require(output_plan.resolve()==target,'report plan target changed before publication')
    outside_inputs(output_plan,config,proof)
    output_plan.parent.mkdir(parents=True,exist_ok=True)
    require(output_plan.resolve()==target,'report plan target changed during directory creation')
    outside_inputs(output_plan,config,proof)
    save_new(output_plan,result)
    return result


def load_execution(item, snapshot, proof):
    require(bool(os.environ.get('PBS_JOBID')),'full execution reader requires PBS')
    require(snapshot['state']=='complete_candidate','complete candidate required')
    accepted=execution.completed(item['root'],item['terminal'],expected_manifest_sha256=item['manifest_sha256'])
    adopt_files(accepted['input_files'],proof)
    summary=accepted['summary']
    ledger=proof.read(Path(item['root'])/'submission.json')
    terminal=read_pin(item['terminal'],proof)['Jobs'][accepted['job_id']]
    return dict(status=('completed_with_recorded_task_failures' if summary.get('failed') else 'completed')
        if summary.get('execution_complete') else 'execution_infeasible_capacity_envelope',
        records=summary['records'],summary=summary,job_id=accepted['job_id'],
        resource=ledger['resource'],pbs=terminal,scope=accepted['scope'],
        hostname=proof.read(Path(item['root'])/'native_preflight.json')['hostname'],
        cpu_model='unknown',frequency='unknown',affinity='unknown',numa='unknown',concurrent_load='unknown',
        hardware_equivalence_certified=False)


def load_method(key, method, row, item, snapshot, proof):
    empty=dict(allocated_tasks=0,records=[],partitions=[],capacity={})
    if row['status']!='selected' or row['planning_status']!='ready':
        return dict(empty,status=row['planning_status'])
    cap=snapshot['capacity']
    if cap['state']!='complete_candidate':
        require(not snapshot['partitions'],'main roots without completed capacity')
        return dict(empty,status='capacity_'+cap['state'],capacity=dict(status=cap['state']))
    capacity=load_execution(item['capacity'],cap,proof)
    decision=execution.resource_plan(capacity['summary'])
    if decision['status']!='ready':
        require(not snapshot['partitions'],'resource-infeasible identity contains main partitions')
        return dict(empty,status=decision['status'],capacity=dict(capacity,resource_decision=decision))
    require(len(snapshot['partitions'])==len(decision['partitions']),'all fixed main partition roots required')
    partitions=[]
    for part_item,part,planned in zip(item['partitions'],snapshot['partitions'],decision['partitions']):
        manifest=part['manifest']
        if manifest is not None:
            wanted=[list((*key,rep)) for rep in planned['replicates']]
            require(manifest['partition_index']==planned['index'] and manifest['tasks']==wanted
                and manifest['resource']==planned['resource'] and manifest['resource_decision']==decision
                and manifest['capacity_reference']=={name:value for name,value in item['capacity'].items() if name!='submission'},
                'partition/resource/capacity allocation differs')
        if part['state']=='complete_candidate':
            loaded=load_execution(part_item,part,proof)
            require([record['task'] for record in loaded['records']]==[list((*key,rep)) for rep in planned['replicates']],
                'actual partition records differ')
        else:loaded=dict(status=part['state'],records=[],unknown_observed_tasks=True)
        partitions.append(loaded)
    complete=all(part['status'] in COMPLETE for part in partitions)
    records=merge_partitions(key,partitions) if complete else []
    status=('completed_with_recorded_task_failures' if any(record['status']=='failed' for record in records) else 'completed') if complete else 'incomplete'
    partial=[record for part in partitions if part['status'] in COMPLETE for record in part['records']]
    return dict(status=status,allocated_tasks=sum(len(part['manifest']['tasks']) for part in snapshot['partitions'] if part['manifest'] is not None),records=records,
        partitions=[{k:v for k,v in part.items() if k!='records' and k!='summary'} for part in partitions],
        job_costs=[{key:part['summary'].get(key) for key in ('pool_wall_seconds','outside_pool_wall_seconds','execution_wall_seconds',
            'known_task_wall_seconds_lower_bound','known_task_cpu_seconds_lower_bound','costs_complete')}
            if 'summary' in part else None for part in partitions],capacity=dict(capacity,resource_decision=decision),
        verified_partial=None if complete else dict(observed_tasks=len(partial),
            scope='Verified completed partitions only; remaining task outcomes and costs are unknown.',
            costs={clock:metrics.cost_summary([record.get(clock) for record in partial]) for clock in CLOCKS}))


def merge_partitions(key, partitions):
    """Require an exact full cohort after each partition's evidence was checked."""
    require(partitions and all(p["status"] in COMPLETE for p in partitions), "complete partitions required")
    records = [row for part in partitions for row in part["records"]]
    expected = [(*key, i) for i in range(192)]
    require(len(records) == 192 and sorted(tuple(row["task"]) for row in records) == expected,
        "exact disjoint replicate partition census required")
    return sorted(records, key=lambda row: row["task"])


def assess_cohort(method, key, cohort, reference, epsilon):
    """Pure descriptive assessment; callers separately verify saved artifacts."""
    require(method in ("mc", "bar"), "unknown method")
    complete = cohort["status"] in COMPLETE
    records = cohort["records"]
    result = dict(status=cohort["status"], planned_replicates=192,
        allocated_tasks=cohort["allocated_tasks"], observed_tasks=len(records) if complete else None,
        assessment=None, costs=None, status_counts=None,
        diagnostic_observation="not_applicable" if method == "mc" else "not_collected",
        partitions=cohort.get("partitions", []), capacity=cohort.get("capacity", {}),
        job_costs=cohort.get("job_costs",[]),
        verified_partial=cohort.get("verified_partial"), raw_artifacts_audited_here=False)
    if not complete:
        return result
    require(cohort["allocated_tasks"] == 192 and len(records) == 192
        and sorted(tuple(row["task"]) for row in records) == [(*key, i) for i in range(192)],
        "exact fixed replicate cohort required")
    normalized = []
    for record in records:
        require(record["status"] in ("ok", "failed", "unavailable"), "invalid completed task status")
        failed = record["status"] == "failed"
        interval = None if failed else record.get("interval")
        estimate = None if failed else record.get("estimate")
        require(type(record["available"]) is bool and (failed or record["available"] ==
            ((estimate is not None) if method=='mc' else (interval is not None))),
            "task interval availability differs")
        normalized.append(dict(replicate=record["task"][3], estimate=estimate, interval=interval,
            available=interval is not None, flagged=method == "bar", undefined=method == "bar",
            high_rhat=False, low_ess=False,
            failure=(record.get("failure") or "recorded task failure") if failed else record.get("failure")))
    result["assessment"] = bounded.assess_bounds(normalized,192,reference,(epsilon,))
    result["costs"] = {clock:metrics.cost_summary([record.get(clock) for record in records]) for clock in CLOCKS}
    result["phase_costs"] = {phase:{clock:metrics.cost_summary([
        record.get("timing",{}).get(phase,{}).get(clock) for record in records])
        for clock in ("wall_seconds", "cpu_seconds")} for phase in metrics.BAR_PHASES}
    result["status_counts"] = dict(Counter(record["status"] for record in records))
    return result


def cost_ratios(mc, bar, eligible):
    ratios = {}
    reason = None
    if not eligible:
        reason = "selection_or_planning_ineligible"
    elif any(value["assessment"] is None for value in (mc,bar)):
        reason = "independent_cohort_incomplete"
    elif any(value["assessment"]["precision"][0]["classification"] != "empirical_within_target" for value in (mc,bar)):
        reason = "both_empirical_precision_gates_required"
    for clock in CLOCKS:
        value = None
        why = reason
        if why is None:
            numerator, denominator = (item["costs"][clock]["mean"] for item in (mc,bar))
            if numerator is None or denominator is None:
                why = "incomplete_clock_costs"
            elif denominator == 0:
                why = "zero_bar_mean_cost"
            else:
                value = numerator/denominator
                if not math.isfinite(value):value,why = None,"numerical_range"
        ratios[clock] = dict(value=value,reason=why)
    return ratios


def assess_rows(rows, references, cohorts):
    """Preserve every planned outcome; references here are already validated."""
    require([identity(row) for row in rows] == IDENTITIES, "all 24 ordered identities required")
    require(set(cohorts) == set(IDENTITIES), "all 24 cohort states required")
    require(set(references) == {(case,target) for case in range(4) for target in range(3)},
        "all twelve fixed references required")
    results = []
    for row in rows:
        key = identity(row)
        reference = references[key[:2]]
        require(row["epsilon"] == (.2,.1)[key[2]] and row["target_p"] == (.01,.003,.001)[key[1]],
            "fixed target and epsilon required")
        require(reference["interval"] == row["reference_interval"], "selection/evaluation reference bounds differ")
        require(set(cohorts[key]) == {"mc","bar"}, "both method states required")
        eligible = row["status"] == "selected" and row["planning_status"] == "ready"
        if not eligible:
            require(all(item["allocated_tasks"] == 0 and not item["records"] for item in cohorts[key].values()),
                "unselected or unallocated identity contains tasks")
        assessed = {method:assess_cohort(method,key,cohorts[key][method],reference["interval"],row["epsilon"])
            for method in ("mc","bar")}
        results.append(dict(case=key[0],target_index=key[1],epsilon_index=key[2],epsilon=row["epsilon"],
            target_p=row["target_p"],planned_replicates=192,selection=row,reference=reference,
            **assessed,ratios_mc_over_bar=cost_ratios(assessed["mc"],assessed["bar"],eligible),
            diagnostic_observation=dict(mc="not_applicable",bar="not_collected"),
            bar_internal_flagged_undefined_are_unobserved_placeholders=True))
    return results


def report_text(report):
    require(report["purpose"] == REPORT_PURPOSE and len(report["records"]) == 24, "fixed 24-row report required")
    lines = ["# 低ノイズ独立計時の評価", "", "全24行・各192 replicateの比較目標を保持する。",
        "未割当0 task、未完了の観測数不明、記録済み失敗を区別する。",
        "有限WSS full区間を選択・MC予算・評価に共用し、partial estimateを真値としない。",
        "独立BARの混合診断は未取得であり、内部flagは実測R-hat/ESS失敗数ではない。",
        "seed census状態: " + report.get("census",{}).get("status","unknown") + "。",
        "追加allocationが0の場合の監査不要は、60 namespaceを新たに監査した主張ではない。", "",
        "|case|p|epsilon|選択|MC状態・点/区間・精度|BAR状態・点/区間・精度|wall比・理由|CPU比・理由|",
        "|---|---:|---:|---|---|---|---|---|"]
    for row in report["records"]:
        states = []
        for method in ("mc","bar"):
            value = row[method];assessment = value["assessment"]
            label = "未評価・観測数不明"
            if assessment:
                counts = assessment["metrics"]
                label = f"{counts['point_estimates']}/{192-counts['unavailable_intervals']}・" + assessment["precision"][0]["classification"]
            states.append(value["status"] + "・" + label)
        ratios = [str(row["ratios_mc_over_bar"][clock]["value"]) + "・" + str(row["ratios_mc_over_bar"][clock]["reason"])
            for clock in ("task_wall_seconds","cpu_seconds")]
        lines.append(f"|{row['case']}|{row['target_p']}|{row['epsilon']}|{row['selection']['status']}|{states[0]}|{states[1]}|{ratios[0]}|{ratios[1]}|")
    lines += ["", "## full reference区間に対する経験的評価", "",
        "|case|p|epsilon|手法|相対RMSE範囲|entire被覆/192|possible被覆/192|",
        "|---|---:|---:|---|---|---|---|"]
    for row in report["records"]:
        for method in ("mc","bar"):
            a = row[method]["assessment"]
            values = ["不明"]*3 if a is None else [str(a["relative_rmse_reference_range"]),
                str(a["metrics"]["covered_reference_entire"]),str(a["metrics"]["covered_reference_possible"])]
            lines.append(f"|{row['case']}|{row['target_p']}|{row['epsilon']}|{method}|{'|'.join(values)}|")
    lines += ["", "task wallとprocess CPUはartifact書込みを除き、inclusive clockは別の補助量としてJSONへ保存する。",
        "pool・phase・PBS費用は按分せず、capacity・seed監査・選択・報告処理の費用も主192標本と分離する。",
        "partitionとhostの差は未補正であり、CPU周波数・負荷等の未記録値はunknownとする。",
        "費用比は経験的精度gateを通過した固定設定の記述量であり、母精度・母時間比・最速設定・名目被覆を保証しない。",
        "各reference区間のconfidence levelは全条件同時保証ではなく、seed監査もstream独立性の数学的証明ではない。", ""]
    return "\n".join(lines)


def render(report_path, expected_sha256, output_path):
    proof = Evidence()
    report = read_pin(dict(path=str(report_path),sha256=expected_sha256),proof)
    text = report_text(report)
    proof.finish()
    with Path(output_path).open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(text)


def run(plan_path, expected_sha256, output_root):
    require(bool(os.environ.get("PBS_JOBID")), "full payload reporting requires PBS")
    require(all(os.environ.get(key)==value for key,value in execution.THREADS.items()),'fixed single-thread environment required')
    output_root=Path(output_root).absolute();target=output_root.resolve()
    require(not output_root.exists() and not output_root.is_symlink(),'preserve existing report root')
    proof=Evidence();plan=read_pin(dict(path=str(plan_path),sha256=expected_sha256),proof)
    require(plan['schema']==1 and plan['purpose']=='low_noise_timing_report_plan','wrong report plan')
    require(sources(proof)==plan['source_sha256'] and runtime()==plan['runtime'],'report source/runtime changed')
    for path,digest in plan['input_sha256'].items():
        require(proof.track(path)==digest and str(Path(path).resolve())==plan['input_targets'][path],'prepared input changed')
    config=read_pin(plan['config_pin'],proof)
    require(config==plan['config'],'report config changed')
    context=inputs(config,proof)
    require(context['snapshots']==plan['snapshots'],'execution state changed; prepare a new report plan')
    outside_inputs(output_root,config,proof)
    try:
        references,reference_proof=reference_evidence(config['reference'],context['bundle']['selection'],proof,full=True)
        require(references==context['references'],'reference changed before evaluation')
        cohorts={}
        for row,item,snapshot in zip(context['rows'],config['cohorts'],context['snapshots']):
            key=identity(row)
            cohorts[key]={method:load_method(key,method,row,item[method],snapshot[method],proof) for method in ('mc','bar')}
        result=dict(schema=1,purpose=REPORT_PURPOSE,records=assess_rows(context['rows'],references,cohorts),
            selection=context['bundle']['selection'],selector_execution=context['selector'],census=context['census'],
            reference_evidence=reference_proof,scientific_bundle_digest=c.digest(context['bundle']),
            registry_digest=c.digest(context['bundle']['registry']),source_sha256=plan['source_sha256'],runtime=plan['runtime'],
            report_pbs_job_id=os.environ['PBS_JOBID'],input_sha256=proof.hashes,input_targets=proof.targets,
            complete_partition_count=sum(part['status'] in COMPLETE for methods in cohorts.values()
                for value in methods.values() for part in value['partitions']),
            complete_partition_payloads_rehashed=True,incomplete_partition_payloads_audited=False,
            native_probe_reexecuted=False,all_physical_states_redecoded=False,
            timing_checkpoint_validation_scope='The existing completed reader re-decodes recorded initial/final states of successful BAR chains when present; no full trace replay. WSS inputs are only rehashed here.',
            phase_time_apportioned=False,
            report_terminal_externally_confirmed=False,warning=WARNING)
        after=inputs(config,proof)
        require(after['snapshots']==context['snapshots'] and after['census']==context['census']
            and after['selector']==context['selector'],'input state changed before report publication')
        if reference_proof.get('chunk_census') is not None:
            require(chunk_census(reference_proof['chunk_census']['root'])==reference_proof['chunk_census'],
                'WSS chunk census changed before publication')
        require(sources(proof)==plan['source_sha256'] and runtime()==plan['runtime'],'source/runtime changed before publication')
        proof.finish();require(output_root.resolve()==target,'report output target changed')
    except Exception as error:
        require(output_root.resolve()==target,'report failure output target changed')
        outside_inputs(output_root,config,proof)
        output_root.mkdir(parents=True,exist_ok=False)
        require(output_root.resolve()==target,'report failure output target changed during creation')
        outside_inputs(output_root,config,proof)
        save_new(output_root/'validation_failure.json',dict(error=str(error),success_report_published=False))
        raise
    output_root.mkdir(parents=True,exist_ok=False)
    require(output_root.resolve()==target,'report output target changed during creation')
    outside_inputs(output_root,config,proof)
    with (output_root/'report_ja.md').open('x',encoding='utf-8',newline='\n') as stream:stream.write(report_text(result))
    result['japanese_report_sha256']=c.file_hash(output_root/'report_ja.md')
    save_new(output_root/'report.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for name,field,out in (('prepare','config','output'),('run','plan','output-root'),('render','report','output')):
        cmd=sub.add_parser(name)
        cmd.add_argument('--'+field,type=Path,required=True)
        cmd.add_argument('--expected-sha256',required=True)
        cmd.add_argument('--'+out,type=Path,required=True)
    args=parser.parse_args()
    if args.command=='prepare':prepare(args.config,args.expected_sha256,args.output)
    elif args.command=='run':run(args.plan,args.expected_sha256,args.output_root)
    else:render(args.report,args.expected_sha256,args.output)


if __name__=='__main__':main()
