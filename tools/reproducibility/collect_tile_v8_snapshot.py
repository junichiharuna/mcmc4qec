"""Finite PBS-only v8 preservation; no raw/native bytes or mutable logs."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

FLOW_SHA='6130af78e5924a299e044195e584b7419affedeecdda393f7842de1bb19c0e43'
FRONT_SHA='22eedcbfb42b9ef6ce3d286b539630491efeb80fd0317287fb31fc6ca8c3e058'
TAIL_SHA='e91b41145b18198161bf8f877af176b9512f943ec9ac52d56dcfc08cf553bb5f'
FLOW_SOURCE_SHA='e18f50818747993c9262ce7d32d3b20eb64bd094a0113f51ea2b09ba3e5c725d'
OLD_REQUEST_SHA='b61ac2c6c2ee2c6880c2c85b63bdf00dac30bc3292eab1961caa18fb9ff0d78d'
OLD_ACCEPTED_SHA='0880492a7f5ec2707d5f00c2327fd3c2aa324bbe1833edf3b9116013a235b049'
FIXTURE_SHA='2d9d10f6b3e6b27d927e3ce3a8f7afa2d1b55806517334f47f30bf2c7462852b'
LIBRARY_SHA='053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a'
READY_SHA='333974f87302894d9075ab3fb6e5f7a3e5cdd5738110400773fd336856a3acd6'
NATIVE_FLOW_SHA='a7afb7a65c38428d87efe6eb8e69e02951217a3cbc38c87588bc3ee3cebdd08a'
SOURCE_SUFFIXES={'.py','.sh','.pbs'}


def require(ok,message):
    if not ok:raise ValueError(message)


def bounded(path):
    path=Path(path)
    require(path.suffix in SOURCE_SUFFIXES|{'.json'},'Collector cannot read raw/native content')
    with path.open('rb') as stream:raw=stream.read(4194305)
    require(len(raw)<=4194304,'Explicit source/metadata size bound exceeded')
    return raw


def pin(path):return dict(path=str(path),sha256=hashlib.sha256(bounded(path)).hexdigest())
def read(p):
    require(Path(p['path']).suffix=='.json','Only explicit JSON metadata may be parsed')
    raw=bounded(p['path']);require(hashlib.sha256(raw).hexdigest()==p['sha256'],'Metadata authority changed')
    return json.loads(raw)


def actual_request(work,stage,lib):
    remote=work/'20261024-c3t2-index-relocation-v1';old_stage=remote/'pipeline-submissions/reproduction-snapshot-v2-actual-v2'
    old_pin=dict(path=str(old_stage/'private-request.json'),sha256=OLD_REQUEST_SHA)
    accepted_pin=dict(path=str(old_stage/'accepted.json'),sha256=OLD_ACCEPTED_SHA)
    old=read(old_pin);accepted=read(accepted_pin)
    require(accepted['request']==old_pin and len(old['sources'])==1031 and len(old['metadata'])==75
        and len(old['envelope'])==1223,'Accepted v5 baseline differs')
    sources={r['path']:deepcopy(r) for r in old['sources']}
    metadata={r['path']:dict(r,category='historical_v5_baseline:'+r['category']) for r in old['metadata']}
    external={r['path']:deepcopy(r) for r in old['external']};bindings=deepcopy(old['bindings']);reasons=[];current=set()
    def source(p,reason,target=None):
        name=p['path'];require(Path(name).is_absolute() and Path(name).suffix in SOURCE_SUFFIXES,'Absolute source required')
        row=dict(p,resolved_path=target or sources.get(name,{}).get('resolved_path',name))
        require(name not in sources or sources[name]==row,'Current/historical source or alias conflict')
        sources[name]=row;current.add(name);reasons.append(dict(p,reason=reason))
    def document(p,role):
        name=p['path'];require(Path(name).suffix=='.json' and Path(name).name!='state-latest.json','Immutable JSON required')
        value=read(p);require(name not in metadata or metadata[name]['sha256']==p['sha256'],'Metadata conflict')
        metadata[name]=dict(p,category=role,relative_base=metadata.get(name,{}).get('relative_base'));return value
    def source_edges(value,role):
        aliases={}
        def declared_aliases(node):
            if isinstance(node,dict):
                for name,target in node.get('resolved_sources',{}).items():
                    require(name not in aliases or aliases[name]==target,'Embedded source alias authorities conflict')
                    aliases[name]=target
                for child in node.values():declared_aliases(child)
            elif isinstance(node,list):
                for child in node:declared_aliases(child)
        declared_aliases(value)
        for edge in lib.scan_references(value):
            target=edge.get('target')
            if edge['kind']=='pin' and isinstance(target,str) and Path(target).suffix in SOURCE_SUFFIXES:
                source(dict(path=target,sha256=edge['sha256']),role+edge['pointer'],aliases.get(target))
    def environment(value,role):
        for name,checksum in value['source_sha256'].items():source(dict(path=name,sha256=checksum),role,value['resolved_sources'][name])
        native=dict(value['native_binding']);native[value['python_path']]=value['python_sha256']
        for name,checksum in native.items():
            require(name not in external or external[name]['sha256']==checksum,'Native pin conflict')
            external[name]=dict(path=name,sha256=checksum,category='native_binary_or_python',reason='Runtime pin; content not read or rehashed')
        for module,name in value['import_origins'].items():
            if name in value['source_sha256']:
                checksum=value['source_sha256'][name];target=value['resolved_sources'][name]
            else:
                require(name in value['native_binding'],'Unaccounted import origin')
                checksum=value['native_binding'][name];target=str(Path(name).resolve(strict=False))
            row=dict(module=module,origin=name,resolved=target,sha256=checksum)
            if row not in bindings:bindings.append(row)
    def env(p,role):
        value=document(p,role);environment(value,role);return value
    document(old_pin,'historical_v5_scope_authority');document(accepted_pin,'historical_v5_collection_acceptance')
    fixture_pin=dict(path=str(remote/'pipeline-submissions/reproduction-snapshot-v2-tests-v2/accepted.json'),sha256=FIXTURE_SHA)
    source_edges(document(fixture_pin,'current_snapshot_library_fixture_authority'),'current_preservation_library_and_tests')
    source_edges(document(pin(stage/'staging-authority.json'),'current_preservation_staging_authority'),'current_preservation_deployment')
    source(pin(stage/'job.sh'),'Current preservation PBS script')
    flow_pin=dict(path=str(work/'20261025-low-parallel-controller-v8/flow-config.json'),sha256=FLOW_SHA)
    flow=document(flow_pin,'current_controller_config')
    require(flow['worker_preparation']['sha256']==FRONT_SHA and flow['tail']['config']['sha256']==TAIL_SHA,'Actual v8 input pins differ')
    prep=document(flow['worker_preparation'],'current_worker_preparation');tail=document(flow['tail']['config'],'current_tail_config')
    tail_prepared=document(pin(work/'20261025-low-parallel-tail-config-v8/prepared-receipt.json'),'current_tail_configuration_preparation')
    require(tail_prepared['config']==flow['tail']['config'] and tail_prepared['runner']==flow['tail']['runner'],'Tail preparation differs')
    source_edges(tail_prepared,'current_tail_configuration_generator')
    source_edges(document(pin(work/'20261025-low-parallel-controller-v8/main-evidence-binding.json'),
                          'current_main_evidence_binding'),'current_main_evidence_binding')
    policy=document(flow['dispatch_policy'],'current_dispatch_policy')
    for value,role in ((flow,'current_flow'),(prep,'current_preparation'),(tail,'current_tail'),(policy,'current_dispatch')):source_edges(value,role)
    env(prep['environment'],'current_parent_environment');env(tail['report_environment'],'current_report_environment')
    document(tail['basis'],'current_census_basis')
    native_report=document(tail['environment_acceptance'],'current_report_native_acceptance')
    source_edges(document(native_report['request'],'current_report_native_request'),'current_report_native_helpers')
    for key,p in tail['parallel_merge'].items():
        if Path(p['path']).suffix=='.json':source_edges(document(p,'current_tail_parallel_binding:'+key),'current_tail_binding:'+key)
    for key in ('prior_preparation','effective_manifest','resource_plan','environment'):
        source_edges(document(flow['merge_inputs'][key],'current_merge_input:'+key),'current_merge_input:'+key)
    ready_pin=dict(path=str(remote/'output/low_parallel_recovery_merge_v6/production-ready.json'),sha256=READY_SHA)
    ready=document(ready_pin,'current_parallel_merge_production_ready')
    ready_origin=document(dict(path=str(remote/'output/reproduction_snapshot_v8/production-ready-origin-verification.json'),
        sha256='e0e2f4874cb53d6f02a49c74dd1bb736cae68c3d414a9b8bbab3e2abc4f0e3bf'),'original_production_ready_authority_verification')
    require(ready_origin['ready']==ready_pin and ready_origin['exact_ready_derivation_verified'] is True,'Original ready authority differs')
    require(ready['actual_execution_cli_bootstrap_verified'] is True and ready['parallel_hash']==flow['merge_inputs']['parallel_hash']
        and ready['execution']['runner']==flow['helpers']['merge_runner'],'Actual parallel execution differs')
    source_edges(ready,'current_parallel_merge_validator')
    for key in ('native_execution_acceptance','native_execution_terminal','native_execution_request','original_deployment'):
        source_edges(document(ready[key],'current_parallel_merge_acceptance:'+key),'current_parallel_merge_acceptance:'+key)
    native=remote/'pipeline-submissions/parallel-flow-native-v8';launch=remote/'pipeline-state/parallel-flow-v8-launch'
    native_flow=document(dict(path=str(native/'accepted.json'),sha256=NATIVE_FLOW_SHA),'current_controller_native_acceptance')
    for name in ('prepared.json','request.json','submission-intent.json','submission.json','qsub-response.json','physical-admission.json'):
        source_edges(document(pin(native/name),'current_controller_native_'+name),'current_controller_native_source:'+name)
    source(pin(native/'job.sh'),'Current controller native PBS entrypoint')
    started=document(pin(launch/'started.json'),'current_controller_immutable_launch')
    require(native_flow['config']==started['config']==flow_pin and native_flow['flow']==started['controller']
        and started['controller']['sha256']==FLOW_SOURCE_SHA,'Actual controller entrypoint/config differs')
    source(started['controller'],'Actual controller entrypoint')
    for name in ('intent.json','process.json'):source_edges(document(pin(launch/name),'current_controller_immutable_launch'),'current_launch_helper')
    jobs=[];manifests=set()
    for worker in prep['workers']:
        prepared=document(worker['prepared'],'current_actual_worker_prepared');source(worker['script'],'Actual immutable worker qsub script')
        source_edges(prepared,'current_actual_worker_prepared')
        for key in ('manifest','resource_plan','environment'):
            value=document(prepared[key],'current_actual_worker_'+key)
            if key=='environment':environment(value,'current_actual_worker_environment')
            if key=='manifest' and prepared[key]['path'] not in manifests:
                manifests.add(prepared[key]['path']);source_edges(value,'current_actual_worker_manifest')
                for condition in value['conditions']:
                    if 'reader_process' in condition:environment(condition['reader_process']['environment'],'current_embedded_reader_environment')
        directory=Path(worker['script']['path']).parent;ledger=document(pin(directory/'submission.json'),'current_actual_worker_submission')
        for name in ('submission-intent.json','qsub-response.json'):document(pin(directory/name),'current_actual_worker_submission')
        require(ledger['command']==['qsub',worker['script']['path']] and ledger['script_sha256']==worker['script']['sha256'],'Worker qsub/script binding differs')
        jobs.append(dict(index=worker['index'],job_id=ledger['job_id'],prepared=worker['prepared']))
    require([r['index'] for r in jobs]==list(range(12)) and len({r['job_id'] for r in jobs})==12,'Actual twelve-worker census differs')
    observed=json.loads(subprocess.check_output(['qstat','-x','-f','-F','json',*[r['job_id'] for r in jobs]],timeout=30))
    require(set(observed['Jobs'])=={r['job_id'] for r in jobs},'Observation census differs')
    lib.save_new(stage/'worker-observation-at-collection.json',lib.encode(observed))
    document(pin(stage/'worker-observation-at-collection.json'),'point_in_time_observation_not_final_proof')
    source(pin(Path(__file__).resolve()),'Executed finite v8 collector')
    request=dict(schema=2,roots=dict(workspace=str(work)),sources=sorted(sources.values(),key=lambda r:r['path']),
        metadata=sorted(metadata.values(),key=lambda r:r['path']),external=sorted(external.values(),key=lambda r:r['path']),
        bindings=bindings,envelope=old['envelope'],expected_source_count=len(sources),expected_envelope_count=1223,
        limits=dict(file_bytes=4194304,total_bytes=33554432),final_proofs_complete=False)
    authority=dict(schema=1,purpose='finite_v8_snapshot_scope',baseline_request=old_pin,baseline_acceptance=accepted_pin,
        flow=flow_pin,front=flow['worker_preparation'],tail=flow['tail']['config'],parallel_merge_ready=ready_pin,
        controller=started['controller'],baseline_historical_source_references=1031,current_explicit_source_references=len(current),
        archive_source_references=len(sources),current_source_reasons=reasons,worker_bindings=jobs,
        current_source_count_meaning='Sources referenced by current authority documents, including historical validation and unassigned manifest slots; not a claim that every source was executed',
        metadata_documents=len(metadata),mutable_observation_logs_read=False,
        metadata_traversal='Explicit documents only; all recognized one-hop edges indexed',
        observation_is_point_in_time_only=True,final_proofs_complete=False,scientific_reproduction_verified=False)
    return request,authority


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',required=True);parser.add_argument('--self-sha256',required=True)
    args=parser.parse_args();require(os.environ.get('PBS_JOBID') and pin(Path(__file__))['sha256']==args.self_sha256,'Pinned PBS collector required')
    work=Path.home()/'workspace/mcmc4qec';fixture=work/'20261024-c3t2-index-relocation-v1/pipeline-submissions/reproduction-snapshot-v2-tests-v2'
    fixture_pin=dict(path=str(fixture/'accepted.json'),sha256=FIXTURE_SHA);accepted=read(fixture_pin)
    require(accepted['tests_passed']==25 and accepted['sources']['snapshot_v2.py']['sha256']==LIBRARY_SHA,'Accepted 25-test library required')
    observed=json.loads(subprocess.check_output(['qstat','-x','-f','-F','json',accepted['pbs_job_id']],timeout=30))['Jobs'][accepted['pbs_job_id']]
    require(observed['job_state']=='F' and observed['Exit_status']==0 and observed['run_count']==1,'Original fixture terminal differs')
    library_pin=accepted['sources']['snapshot_v2.py'];raw=bounded(library_pin['path'])
    require(hashlib.sha256(raw).hexdigest()==LIBRARY_SHA,'Immutable library differs')
    spec=importlib.util.spec_from_file_location('accepted_v8_snapshot_library',library_pin['path']);lib=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=lib;exec(compile(raw,library_pin['path'],'exec'),lib.__dict__)
    stage=Path(args.stage);request,authority=actual_request(work,stage,lib)
    lib.save_new(stage/'private-request.json',lib.encode(request));lib.save_new(stage/'private-authority.json',lib.encode(authority))
    receipt=lib.snapshot(request,stage/'snapshot');require(pin(Path(__file__))['sha256']==args.self_sha256,'Collector changed during collection')
    result=dict(schema=1,purpose='actual_v8_finite_snapshot_collection',pbs_job_id=os.environ['PBS_JOBID'],collector=pin(Path(__file__).resolve()),
        library=library_pin,fixture=fixture_pin,request=pin(stage/'private-request.json'),authority=pin(stage/'private-authority.json'),
        snapshot_receipt=pin(stage/'snapshot/receipt.json'),counts={k:receipt[k] for k in
            ('source_references','metadata_documents','envelope_references','one_hop_edges','external_records','original_text_bytes')},
        public_archive_created=False,full_dependency_closure_complete=False,scientific_reproduction_verified=False,final_proofs_complete=False)
    lib.save_new(stage/'accepted.json',lib.encode(result));print(json.dumps(result['counts']))


if __name__=='__main__':main()
