"""Select independent timing candidates only after complete audited calibration."""
import argparse
import ast
from collections import Counter
import itertools
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import sys
from types import SimpleNamespace

import calibration as c
import tile_low_noise_study as low
import tile_low_noise_summary as description
import tile_low_noise_reference_comparison as comparison
import tile_reference_source_binding as source_binding
from tile_low_noise_audited_collection import Evidence

EPSILONS=(.2,.1)
WARNING=("Independent evaluation candidates only, not recommended settings. All 192 replicates and all planned settings "
         "remain in the denominator. A finite WSS interval is not a full point reference. Empirical precision is not "
         "population precision or nominal coverage. No independent timing was performed; all speed ratios are null.")


def identities():
    return itertools.product(range(4),range(3),range(2))


def source_hashes():
    """Hash the actual local-import closure, preserving each resolved module path.

    Standalone deployments reuse immutable modules from multiple cluster_scripts
    roots. The input manifest pins this entire path-to-hash mapping; equal bytes
    at a different import location are not interchangeable.
    """
    roots={Path(value).resolve() for value in sys.path if value and Path(value).name=='cluster_scripts'}
    roots.update((Path(__file__).resolve().parent,Path(low.__file__).resolve().parent))
    pending=[Path(__file__).resolve()];result={}
    while pending:
        path=pending.pop()
        if str(path) in result:continue
        if path.parent not in roots or not path.is_file():raise ValueError('source outside resolved import roots')
        result[str(path)]=c.file_hash(path)
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            names=([item.name.split('.')[0] for item in node.names] if isinstance(node,ast.Import)
                   else [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else [])
            for name in names:
                if not any((root/(name+'.py')).is_file() for root in roots):continue
                spec=importlib.util.find_spec(name)
                if spec is None or spec.origin is None:raise ValueError('local source import cannot be resolved')
                target=Path(spec.origin).resolve()
                if target.parent not in roots:raise ValueError('local source import escaped pinned roots')
                pending.append(target)
    return result


def base_row(case,target,epsilon):
    return dict(case=case,target_index=target,target_p=low.TARGETS[target],epsilon_index=epsilon,
                epsilon=EPSILONS[epsilon],calibration_replicates=192,selected_condition=None,
                rank=None,reference_interval=None,speed_ratio=None)


def width_gate(interval,epsilon):
    if interval is None:return dict(status='ineligible_reference_unavailable',impossible=None)
    if (len(interval)!=2 or any(isinstance(x,bool) or not math.isfinite(x) for x in interval)
            or not 0<=interval[0]<=interval[1]<=1):raise ValueError('invalid full reference interval')
    lower,upper=interval
    left,right=upper*(1-epsilon),lower*(1+epsilon)
    # Decimal spelling avoids rejecting exact decimal equality due to rounding.
    from decimal import Decimal
    impossible=Decimal(str(upper))*(1-Decimal(str(epsilon)))>Decimal(str(lower))*(1+Decimal(str(epsilon)))
    status=('ineligible_reference_zero_boundary' if lower==0 else
            'ineligible_reference_width' if impossible else 'width_necessary_condition_satisfied')
    return dict(status=status,impossible=impossible,lower=lower,upper=upper,epsilon=epsilon,
                necessary_left=left,necessary_right=right,comparison='U*(1-epsilon) <= L*(1+epsilon)')


def rank(plan,condition):
    label=condition['ladder']
    if label not in ('coarse','fine'):raise ValueError('unknown ladder')
    rung_count=len(plan['condition']['coarse' if label=='coarse' else 'rungs'])
    work=rung_count*condition['chains']*(condition['burn']+condition['samples'])
    return (work,condition['method']!='cross_chain',condition['block'] or 0,
            condition['kernel']!='ZH',condition['init']!='logical_basis',c.canonical(condition).decode())


def choose(plan,compared):
    """Choose from validated bounded arithmetic; this does not validate artifacts."""
    if plan['purpose']!='low_noise_production' or plan['replicates']!=192 or compared['replicates']!=192:
        raise ValueError('complete fixed 192 replicate production cohort required')
    keys=list(description.expected_conditions(plan))
    actual=[tuple(row[k] for k in description.CONDITION) for row in compared['conditions']]
    if len(actual)!=len(keys) or set(actual)!=set(keys):raise ValueError('complete unique settings required')
    interval=None if compared['reference'] is None else compared['reference']['interval']
    if compared['reference_available']!=(interval is not None):raise ValueError('reference availability differs')
    candidates=[]
    for row in compared['conditions']:
        condition={key:row[key] for key in description.CONDITION}
        assessment=row['assessment']
        if assessment['metrics']['replicates']!=192:raise ValueError('candidate denominator differs')
        candidates.append(dict(condition=condition,rank=list(rank(plan,condition)),assessment=assessment))
    candidates.sort(key=lambda row:row['rank'])
    result=[]
    for ei,epsilon in enumerate(EPSILONS):
        gate=width_gate(interval,epsilon)
        counts=Counter();eligible=[]
        for candidate in candidates:
            a=candidate['assessment']
            entries=[item for item in a['precision'] if item['epsilon']==epsilon]
            if len(entries)!=1:raise ValueError('fixed precision classification missing')
            classification=entries[0]['classification'];counts[classification]+=1
            if classification=='empirical_within_target':
                bounds=a['relative_rmse_reference_range']
                if (a['metrics']['point_estimates']!=192 or bounds is None or
                        not all(math.isfinite(x) for x in bounds) or not 0<=bounds[0]<=bounds[1]<=epsilon):
                    raise ValueError('empirical eligibility arithmetic differs')
                eligible.append(candidate)
        row=base_row(plan['case'],plan['target_index'],ei)
        row.update(reference_interval=interval,width_gate=gate,candidates=candidates,
                   classification_counts=dict(sorted(counts.items())),planned_conditions=len(keys),
                   diagnostics_filter_applied=False,coverage_filter_applied=False)
        if gate['status']!='width_necessary_condition_satisfied':row['status']=gate['status']
        elif eligible:
            row.update(status='selected',selected_condition=eligible[0]['condition'],rank=eligible[0]['rank'])
        else:row['status']='unmet_empirical_precision'
        result.append(row)
    return result


def select_condition(plan,rows,condition):
    """Pure full-cohort numerical entry point, without a persisted-evidence claim."""
    if plan['purpose']!='low_noise_production' or plan['replicates']!=192:
        raise ValueError('complete fixed 192 replicate production cohort required')
    return choose(plan,comparison.compare_rows(plan,list(rows),condition))


def check_terminal(proof,terminal,ledger_path,job_id,manifest,allowed_exits):
    ledger=proof.read(ledger_path)
    command=ledger.get('command')
    if (not isinstance(job_id,str) or not re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',job_id)
            or ledger.get('job_id')!=job_id or ledger.get('manifest')!=manifest
            or not isinstance(command,list) or len(command)!=2 or command[0]!='qsub'):
        raise ValueError('terminal ledger/job/manifest differs')
    script=Path(command[1])
    if not script.is_absolute() or proof.track(script)!=ledger.get('script_sha256'):
        raise ValueError('terminal script hash differs')
    job=terminal.get('Jobs',{}).get(job_id,{})
    if (job.get('job_state')!='F' or type(job.get('Exit_status')) is not int
            or job['Exit_status'] not in allowed_exits
            or (job.get('Submit_arguments')!=str(script) and shlex.split(job.get('Submit_arguments',''))!=[str(script)])):
        raise ValueError('terminal PBS state/exit/script differs')
    return dict(job_id=job_id,exit_status=job['Exit_status'],ledger_sha256=proof.track(ledger_path))


def load_complete(entry,proof):
    """Compute-node-only persisted validation; no BAR solve or new sampling."""
    import audit_tile_weight_reference as audit
    import tile_weight_reference_audit_run as reference_run
    import tile_low_noise_audited_collection as single
    import tile_low_noise_partitioned_collection as partitioned
    import tile_low_noise_staging_control as staged_control
    root,audit_root,ref_root,ref_audit_root=[Path(entry[key]).resolve() for key in
        ('root','audit_root','reference_root','reference_audit_root')]
    pins=entry['input_sha256']
    if not pins or any(not Path(name).is_absolute() for name in pins):raise ValueError('absolute external input pins required')
    for name,digest in pins.items():
        if proof.track(name)!=digest:raise ValueError('external input pin differs')
    def read(path):
        if str(Path(path).absolute()) not in pins:raise ValueError('missing external metadata pin: '+str(path))
        return proof.read(path)
    saved=read(entry['final_report'])
    plan=read(root/'manifest.json')
    if (plan['case']!=entry['case'] or plan['target_index']!=entry['target_index']
            or c.canonical(plan)!=c.canonical(low.make_plan(entry['case'],entry['target_index'],capacity=False))):
        raise ValueError('fixed full calibration plan/runtime/source differs')
    context=read(root/'analysis_manifest.json')
    wrapper=read(root/'partition_analysis_manifest.json')
    audit_plan=read(audit_root/'manifest.json')
    final_summary=read(root/'partition-collection/summary.json')
    reference_plan=read(ref_audit_root/'manifest.json')
    reference_summary=read(ref_audit_root/'summary.json')
    native=read(ref_audit_root/'native_preflight.json')
    reference_intent=read(ref_audit_root/'execution-intent.json')
    ref_context=read(ref_root/'manifest.json')
    index=comparison.compatible_condition(plan,ref_context)
    reference_sources=source_binding.reference_context(reference_plan,ref_audit_root,ref_root,
        SimpleNamespace(reference=reference_run,audit=audit,c=c),proof)
    if (reference_summary.get('manifest')!=c.digest(reference_plan) or reference_summary.get('tasks')!=16
            or reference_summary.get('failed')!=0 or reference_summary.get('all_conditions_audited') is not True
            or reference_summary.get('terminal_binding_valid') is not True or reference_summary.get('phase_failure') is not None
            or reference_summary.get('phase_failures')!=[]
            or [item['condition'] for item in reference_summary['records']]!=list(range(16))
            or any(item['status']!='ok' for item in reference_summary['records'])
            or native['pbs_job_id']!=reference_summary['pbs_job_id']
            or reference_intent.get('manifest')!=c.digest(reference_plan)
            or reference_intent.get('reference_context')!=c.digest(ref_context)
            or reference_intent.get('conditions')!=list(range(16)) or reference_intent.get('workers')!=16
            or not reference_intent.get('hostname')
            or {key:value for key,value in native.items() if key not in ('profile','original_pbs_job_id')}!=reference_intent
            or c.digest(native['profile'])!=reference_plan['actual_native_profile_digest']
            or native['original_pbs_job_id']!=reference_plan['original_pbs_job_id']
            or reference_summary['execution_intent_sha256']!=proof.track(ref_audit_root/'execution-intent.json')
            or reference_summary['native_preflight_sha256']!=proof.track(ref_audit_root/'native_preflight.json')):
        raise ValueError('complete sixteen-condition WSS audit required')
    base=ref_audit_root/'conditions'/str(index)
    for ext in ('.done.json','.json','.npz'):
        if str(base.with_suffix(ext)) not in pins:raise ValueError('reference audit artifact pins required')
    arrays,record=proof.artifact(base,dict(manifest=c.digest(reference_plan),condition=index))
    if (arrays or record['status']!='ok' or
            reference_summary['condition_marker_sha256'][str(index)]!=proof.track(base.with_suffix('.done.json'))
            or c.canonical({key:value for key,value in record.items() if key!='report'})!=c.canonical(reference_summary['records'][index])):
        raise ValueError('saved reference audit outcome differs')
    reference=record['report']
    source_binding.reference_sources(reference['source_sha256'],reference_sources['sources'],
        reference_sources['saved_root'],reference_sources['current_root'],proof)
    reference_run.report_binding(reference_plan,index,dict(reference,source_sha256=reference_sources['sources']))
    audit.verify_unchanged(ref_root,reference['input_sha256'],reference_sources['sources'])
    for name,digest in reference['input_sha256'].items():
        if proof.track(ref_root/name)!=digest:raise ValueError('reference raw input changed')
    if c.canonical(saved.get('reference_audit'))!=c.canonical(reference):raise ValueError('final report reference audit differs')
    readers={'single':single.read_audited_collection,'partitioned':partitioned.read_audited_collection,
             'staged':lambda source,trace:staged_control.collect(source,trace,entry['staging_control_pins'])}
    if entry['reader'] not in readers:raise ValueError('explicit supported audited reader required')
    actual,rows,evidence=readers[entry['reader']](root,audit_root)
    if (c.canonical(actual)!=c.canonical(plan) or c.canonical(saved.get('audited_collection'))!=c.canonical(evidence)
            or saved.get('manifest')!=c.digest(plan) or evidence.get('groups')!=768 or evidence.get('anchors')!=192
            or evidence.get('native_platform_verified') is not True or evidence.get('current_trace_payloads_rehashed') is not True
            or saved.get('raw_reference_audited') is not True or saved.get('current_trace_payloads_rehashed') is not True):
        raise ValueError('final audited collection binding differs')
    if not saved.get('source_sha256'):raise ValueError('final report source closure required')
    directory=Path(comparison.__file__).resolve().parent
    if any(saved['source_sha256'].get(str(directory/name))!=digest for name,digest in comparison.source_hashes().items()):
        raise ValueError('final report numerical source closure incomplete or changed')
    for name,digest in saved['source_sha256'].items():
        if not Path(name).is_absolute() or proof.track(name)!=digest:raise ValueError('final report source differs')
    compared=comparison.compare_rows(plan,rows,reference['condition'])
    for key,value in compared.items():
        # Final audited report intentionally replaces these audit flags.
        if key in ('raw_reference_audited',):continue
        if c.canonical(saved.get(key))!=c.canonical(value):raise ValueError('final report arithmetic differs: '+key)
    for name,digest in evidence['evidence_sha256'].items():
        if str(Path(name).resolve())!=evidence['evidence_resolved_paths'][name] or proof.track(name)!=digest:
            raise ValueError('audited collection input changed')
    jobs={}
    def add(job,ledger,manifest,exits=(0,)):
        value=(str(Path(ledger).absolute()),manifest,exits)
        if job in jobs and jobs[job]!=value:raise ValueError('same PBS id has conflicting phase evidence')
        jobs[job]=value
    completed=context['completed_phase_evidence']
    if entry['reader']=='partitioned':
        for item in completed['pbs_jobs']:
            add(item['job_id'],root/f"sampling-submissions/{item['phase']}/{item['index']}/submission.json",
                completed['collection_manifest'],(item['exit_status'],))
        add(completed['collector_pbs_job']['job_id'],root/'sampling-collection-submission/submission.json',completed['collection_manifest'])
    else:
        source_root=Path(evidence.get('staging_origin',{}).get('original_source_root',root))
        failures=sum(completed[phase]['failed'] for phase in ('sample','anchors'))
        for phase in ('sample','anchors'):
            intent=read(root/(phase+'-execution-intent.json'))
            add(intent['pbs_job_id'],source_root/'submission.json',c.digest(plan),(0,1) if failures else (0,))
    for part in wrapper['resources']['partitions']:
        item=read(root/f"analysis-partitions/{part['index']}/summary.json")
        add(item['pbs_job_id'],root/f"analysis-submissions/{part['index']}/submission.json",c.digest(plan))
    add(evidence['pbs_job_id'],audit_root/'submission.json',c.digest(audit_plan))
    original_reference_summary=read(ref_root/'summary.json')
    add(reference['pbs_job_id'],ref_root/'submission.json',c.digest(ref_context),
        (0,1) if original_reference_summary['unavailable'] else (0,))
    add(reference_summary['pbs_job_id'],ref_audit_root/'submission.json',c.digest(reference_plan))
    add(saved['pbs_job_id'],entry['final_submission'],c.digest(plan))
    # Partitioned collection has its own execution identity; it cannot disappear
    # behind a later report job. Old single-PBS collection has no such field.
    if final_summary.get('pbs_job_id') and final_summary['pbs_job_id']!=saved['pbs_job_id']:
        add(final_summary['pbs_job_id'],entry['collection_submission'],c.digest(plan))
    terminal=read(entry['terminal_receipt'])
    if set(terminal.get('Jobs',{}))!=set(jobs):raise ValueError('exact completed upstream PBS census required')
    receipts=[]
    for job,(ledger,manifest,exits) in sorted(jobs.items()):
        if ledger not in pins:raise ValueError('external submission pin required')
        value=read(ledger)
        if value['command'][1] not in pins:raise ValueError('external script pin required')
        receipts.append(check_terminal(proof,terminal,ledger,job,manifest,exits))
    return choose(plan,compared),dict(manifest=c.digest(plan),analysis=c.digest(context),
        expected_conditions=list(description.expected_conditions(plan)),reference_context=c.digest(ref_context),
        reference_condition=index,reference_interval=None if compared['reference'] is None else compared['reference']['interval'],
        reference_audit_digest=c.digest(reference),audited_collection_digest=c.digest(evidence),terminals=receipts)


def run(input_path,expected_sha256,output):
    """Persist all 24 outcomes once; invalid evidence never becomes ineligible."""
    input_path,output=Path(input_path).absolute(),Path(output).absolute()
    if output.exists() or output.is_symlink():raise ValueError('selection output exists; no automatic replacement')
    output_target=output.resolve()
    proof=Evidence()
    if proof.track(input_path)!=expected_sha256:raise ValueError('selection external pin differs')
    manifest=proof.read(input_path)
    if (set(manifest)!={'schema','purpose','source_sha256','conditions'} or manifest['schema']!=1
            or manifest['purpose']!='low_noise_timing_selection_input' or manifest['source_sha256']!=source_hashes()):
        raise ValueError('fixed selection policy or source closure differs')
    entries=manifest['conditions']
    expected=list(itertools.product(range(4),range(3)))
    coordinates=[(entry['case'],entry['target_index']) for entry in entries]
    if (len(coordinates)!=12 or set(coordinates)!=set(expected)
            or any(type(x) is not int for pair in coordinates for x in pair)
            or any(entry['status'] not in ('pending','complete') for entry in entries)):
        raise ValueError('exact twelve input conditions and explicit state required')
    entries=sorted(entries,key=lambda item:(item['case'],item['target_index']))
    for entry in entries:
        for key in ('root','audit_root','reference_root','reference_audit_root'):
            if key in entry and output.resolve().is_relative_to(Path(entry[key]).resolve()):
                raise ValueError('selection output must be outside input roots')
    pending=[dict(case=x['case'],target_index=x['target_index'],reason=x.get('reason','not_complete')) for x in entries if x['status']=='pending']
    rows=[];bindings=[]
    if pending:
        # A partial ready declaration cannot hide known corrupt pinned inputs
        # behind another condition's pending state. Do not perform raw scans.
        for entry in entries:
            if entry['status']=='complete':
                required=('root','audit_root','reference_root','reference_audit_root','reader','final_report',
                          'final_submission','terminal_receipt','input_sha256')
                if any(key not in entry for key in required) or not entry['input_sha256']:
                    raise ValueError('complete declaration requires pinned metadata')
                for name,digest in entry['input_sha256'].items():
                    if not Path(name).is_absolute() or proof.track(name)!=digest:
                        raise ValueError('complete declaration external pin differs')
        rows=[base_row(case,target,epsilon)|dict(status='selection_pending',pending_conditions=pending) for case,target,epsilon in identities()]
    else:
        if (not re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',os.environ.get('PBS_JOBID',''))
                or any(os.environ.get(key)!=value for key,value in low.native.THREADS.items())):
            raise ValueError('PBS and pinned single-thread environment required before raw scanning')
        for entry in entries:
            selected,binding=load_complete(entry,proof);rows.extend(selected);bindings.append(binding)
    if [(row['case'],row['target_index'],row['epsilon_index']) for row in rows]!=list(identities()):
        raise ValueError('fixed 24 row output identity differs')
    proof.finish()
    if source_hashes()!=manifest['source_sha256']:raise ValueError('selector source changed during read')
    result=dict(schema=1,purpose='low_noise_independent_timing_selection',rows=rows,conditions=24,
        input_manifest_sha256=expected_sha256,input_sha256=proof.hashes,input_resolved=proof.targets,
        source_sha256=manifest['source_sha256'],calibration_bindings=bindings,
        production_selection_validated=not pending,independent_timing_performed=False,
        population_rmse_certified=False,nominal_coverage_certified=False,warning=WARNING)
    if output.resolve()!=output_target:raise ValueError('selection output target changed')
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.resolve()!=output_target:raise ValueError('selection output target changed before publication')
    for entry in entries:
        for key in ('root','audit_root','reference_root','reference_audit_root'):
            if key in entry and output.resolve().is_relative_to(Path(entry[key]).resolve()):
                raise ValueError('selection output must remain outside input roots')
    with output.open('xb') as stream:stream.write(c.canonical(result)+b'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.input,args.expected_sha256,args.output)
    print(json.dumps(dict(conditions=24,statuses=dict(Counter(row['status'] for row in result['rows'])))))


if __name__=='__main__':main()
