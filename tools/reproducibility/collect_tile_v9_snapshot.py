"""Preserve fixed v9 control metadata using the accepted finite snapshot library."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

MAX=4*1024**2
LIBRARY='053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a'
OLD_ACCEPTED='7e702412d2fb054b0c351d3be8e971eeb4301cce43c88c8f89dacca39bd536a2'
FLOW='5b44a838edcf35f9d02d119c323530ef17bab880aeb8c29e74ff3fe81c4748ed'
OUTER='f4dc8a4b9ff57cbe2c1f6e8867fd2d31b4b1b6c09be57a812c353681a7cbf114'
SOURCE={'.py','.sh','.pbs'}


def require(value,message):
    if not value:raise ValueError(message)


def bounded(path):
    path=Path(path);require(path.suffix in SOURCE|{'.json'},'Only explicit source or metadata may be opened')
    with path.open('rb') as stream:value=stream.read(MAX+1)
    require(len(value)<=MAX,'Explicit source/metadata exceeds bound');return value


def pin(path,expected=None):
    path=Path(path);value=dict(path=str(path),sha256=hashlib.sha256(bounded(path)).hexdigest())
    require(expected is None or value['sha256']==expected,'Original authority differs');return value


def read(record):
    require(Path(record['path']).suffix=='.json','Explicit metadata JSON required')
    raw=bounded(record['path']);require(hashlib.sha256(raw).hexdigest()==record['sha256'],'Original metadata differs');return json.loads(raw)


class Scope:
    def __init__(self,baseline,library):
        self.base=deepcopy(baseline);self.lib=library
        self.sources={r['path']:deepcopy(r) for r in baseline['sources']}
        self.metadata={r['path']:dict(r,category='historical_v8:'+r['category']) for r in baseline['metadata']}
        self.external={r['path']:deepcopy(r) for r in baseline['external']}
        self.bindings=deepcopy(baseline['bindings']);self.reasons={};self.current_sources=set()

    def source(self,record,role,target=None):
        name=record['path'];require(Path(name).is_absolute() and Path(name).suffix in SOURCE,'Absolute source declaration required')
        value=dict(record,resolved_path=target or self.sources.get(name,{}).get('resolved_path',name))
        require(name not in self.sources or self.sources[name]==value,'Current/historical source conflict')
        require(name not in self.external,'Explicit source conflicts with old external scope')
        self.sources[name]=value;self.current_sources.add(name)
        # Full JSON pointers remain in the library's one-hop edge index.
        # The small authority only needs each source's distinct document-role attribution.
        compact_role=role.partition('/')[0]
        self.reasons[(name,compact_role)]=dict(record,role=compact_role)

    def source_edges(self,value,role):
        aliases={}
        def visit(node):
            if isinstance(node,dict):
                for name,target in node.get('resolved_sources',{}).items():
                    require(name not in aliases or aliases[name]==target,'Declared source alias conflict');aliases[name]=target
                for child in node.values():visit(child)
            elif isinstance(node,list):
                for child in node:visit(child)
        visit(value)
        for edge in self.lib.scan_references(value):
            target=edge.get('target')
            if edge['kind']=='pin' and isinstance(target,str) and Path(target).suffix in SOURCE:
                self.source(dict(path=target,sha256=edge['sha256']),role+edge['pointer'],aliases.get(target))

    def document(self,record,role):
        name=record['path'];require(Path(name).name!='state-latest.json','Mutable observation forbidden')
        require(name not in self.metadata or self.metadata[name]['sha256']==record['sha256'],'Metadata conflict')
        require(name not in self.external,'Explicit metadata conflicts with old external scope')
        value=read(record)
        self.metadata[name]=dict(record,category=role,relative_base=self.metadata.get(name,{}).get('relative_base'))
        self.source_edges(value,role)
        return value

    def environment(self,record,role):
        value=self.document(record,role)
        for name,checksum in value['source_sha256'].items():
            self.source(dict(path=name,sha256=checksum),role,value['resolved_sources'][name])
        native=dict(value['native_binding']);native[value['python_path']]=value['python_sha256']
        for name,checksum in native.items():
            require(name not in self.external or self.external[name]['sha256']==checksum,'Native declaration conflict')
            self.external[name]=dict(path=name,sha256=checksum,category='native_binary_or_python',reason='Runtime declaration only; never open content')
        for module,name in value['import_origins'].items():
            if name in value['source_sha256']:checksum=value['source_sha256'][name];target=value['resolved_sources'][name]
            else:
                require(name in native,'Import origin lacks declaration');checksum=native[name];target=str(Path(name).resolve(strict=False))
            row=dict(module=module,origin=name,resolved=target,sha256=checksum)
            if row not in self.bindings:self.bindings.append(row)
        return value

    def request(self):
        result=deepcopy(self.base)
        result.update(sources=sorted(self.sources.values(),key=lambda r:r['path']),
            metadata=sorted(self.metadata.values(),key=lambda r:r['path']),external=sorted(self.external.values(),key=lambda r:r['path']),
            bindings=self.bindings,expected_source_count=len(self.sources),expected_envelope_count=len(self.base['envelope']),
            limits=dict(file_bytes=MAX,total_bytes=32*1024**2),final_proofs_complete=False)
        return result


def collect(stage,library):
    work=Path.home()/'workspace/mcmc4qec';remote=work/'20261024-c3t2-index-relocation-v1'
    baseline_pin=pin(remote/'pipeline-submissions/reproduction-v8-finite-snapshot-v2/accepted.json',OLD_ACCEPTED)
    baseline=read(baseline_pin);require(baseline['library']['sha256']==LIBRARY,'Baseline library differs')
    old=read(baseline['request']);scope=Scope(old,library)
    scope.document(baseline_pin,'historical_v8_acceptance');scope.document(baseline['request'],'historical_v8_request')
    scope.document(baseline['authority'],'historical_v8_scope_authority')
    scope.document(baseline['fixture'],'snapshot_library_fixture_authority')
    staging=scope.document(pin(stage/'staging-authority.json'),'current_snapshot_staging')
    scope.document(pin(stage/'scope-fixture-accepted.json'),'current_snapshot_builder_fixture_acceptance')
    for p in staging['sources'].values():scope.source(p,'current_snapshot_builder_or_fixture')
    scope.source(pin(stage/'job.sh'),'current_snapshot_qsub_entrypoint')
    flow_pin=pin(work/'20261025-low-parallel-controller-v9/flow-config.json',FLOW)
    flow=scope.document(flow_pin,'current_flow_configuration')
    outer=scope.document(flow['tail']['config'],'current_outer_configuration')
    require(flow['tail']['config']['sha256']==OUTER,'Final outer binding differs')
    prepared=scope.document(pin(work/'20261025-finite-tail-outer-v9/prepared-receipt.json',
        'fb0be410d0393c42422b84a3cf89f4c5c04de65014517f144f4aed95106bf540'),'current_outer_assembly_receipt')
    require(prepared['configuration']==flow['tail']['config'] and prepared['runner']==flow['tail']['runner'],'Outer runner/config differs')
    direct_documents=[]
    for name,p in outer['source_pins'].items():
        if Path(p['path']).suffix=='.json':direct_documents.append((name,p,scope.document(p,'current_outer_closure:'+name)))
        else:scope.source(p,'current_outer_closure:'+name)
    # Only one explicit authority-request layer, not recursive arbitrary JSON traversal.
    for name,p,value in direct_documents:
        request=value.get('request') if isinstance(value,dict) else None
        if isinstance(request,dict) and set(request)=={'path','sha256'}:scope.document(request,'current_outer_authority_request:'+name)
    effective=scope.document(outer['effective_config'],'current_effective_tail')
    scope.environment(effective['parent_environment'],'current_parent_environment')
    scope.environment(effective['report_environment'],'current_report_environment')
    report=scope.document(effective['environment_acceptance'],'current_report_environment_acceptance')
    if isinstance(report.get('request'),dict):scope.document(report['request'],'current_report_environment_request')
    native_flow=scope.document(pin(remote/'pipeline-submissions/parallel-flow-native-v9/accepted.json',
        '1c95d2ed0ab6095cf2ef903f0fb18865a408f2e1b74387758791c83d2d0ad96d'),'current_flow_native_acceptance')
    require(native_flow['config']==flow_pin,'Native flow config differs')
    outer_native=scope.document(pin(remote/'pipeline-submissions/finite-tail-outer-constructor-native-v1/results/accepted.json',
        '95cf799d681479553f2817f21705df22585d539b68da2c12f03c7f3461c3d990'),'current_outer_native_acceptance')
    require(outer_native['configuration']==flow['tail']['config'],'Native outer differs')
    scope.document(outer_native['request'],'current_outer_native_request')
    for row in outer_native['results']:scope.document(row['accepted'],'current_outer_native_case_acceptance')
    launch=remote/'pipeline-state/parallel-flow-v9-launch'
    started=scope.document(pin(launch/'started.json','ff09c182ad53930668b8cd2a1d2a157b3ec459795702ced6b3ee9cc8386189ef'),'current_actual_launch')
    require(started['config']==flow_pin and started['controller']==native_flow['flow'],'Actual launched flow differs')
    scope.document(pin(launch/'process.json','2f670a0d080b822ad7c7c81210e29af0b0fbf9a36a0b9aa4cfdfcab2144ebb5c'),'current_actual_launch_process')
    scope.document(pin(launch/'intent.json'),'current_actual_launch_intent')
    cutover=remote/'pipeline-state/parallel-flow-v9-cutover'
    scope.document(pin(cutover/'stopped.json','fa52d841b85f4c97e6e80fe51943ffb4d1ae71885aabcd11dc741227ee06b26a'),'current_old_controller_stopped')
    scope.document(pin(cutover/'stop-intent.json'),'current_old_controller_stop_intent')
    submission_dirs=[remote/'pipeline-submissions'/name for name in
        ('parallel-flow-native-v9','finite-tail-outer-assembly-v1','finite-tail-outer-constructor-native-v1')]
    for directory in submission_dirs:
        ledger=None
        for name in ('request.json','submission-intent.json','submission.json','qsub-response.json','physical-admission.json'):
            value=scope.document(pin(directory/name),'current_native_or_assembly_submission:'+directory.name+':'+name)
            if name=='submission.json':ledger=value
        scope.source(pin(directory/'job.sh'),'current_native_or_assembly_script:'+directory.name)
        observed=subprocess.run(['qstat','-x','-f','-F','json',ledger['job_id']],capture_output=True,check=True,timeout=30).stdout
        require(len(observed)<=MAX,'Native terminal observation exceeds bound');snapshot=json.loads(observed)
        require(set(snapshot['Jobs'])=={ledger['job_id']},'Native terminal job differs')
        row=snapshot['Jobs'][ledger['job_id']]
        require(row['job_state']=='F' and row['Exit_status']==0 and row['run_count']==1,'Native/assembly F0 required')
        name='native-terminal-'+directory.name+'.json';library.save_new(stage/name,observed)
        scope.document(pin(stage/name),'current_native_or_assembly_terminal_observation')
    # Twelve old scientific worker IDs are retained exactly, without opening their results.
    old_authority=read(baseline['authority']);workers=old_authority['worker_bindings']
    require(flow['worker_preparation']==old_authority['front'] and len(workers)==12,'Worker preparation changed since baseline')
    observed=subprocess.run(['qstat','-x','-f','-F','json',*[row['job_id'] for row in workers]],capture_output=True,check=True,timeout=30).stdout
    require(len(observed)<=MAX,'Worker observation exceeds bound');observed_value=json.loads(observed)
    require(set(observed_value['Jobs'])=={row['job_id'] for row in workers},'Worker observation census differs')
    library.save_new(stage/'worker-observation-at-collection.json',observed)
    scope.document(pin(stage/'worker-observation-at-collection.json'),'point_in_time_worker_observation_not_final_proof')
    authority=dict(schema=1,purpose='finite_v9_snapshot_scope',baseline=baseline_pin,flow=flow_pin,
        outer=flow['tail']['config'],worker_bindings=workers,source_reasons=list(scope.reasons.values()),
        source_reason_detail='Unique path/document-role pairs; full declaration pointers retained in snapshot one-hop index',
        historical_source_references=len(old['sources']),current_explicit_source_references=len(scope.current_sources),
        metadata_traversal='Explicit selected metadata and one authority-request layer; no arbitrary recursive traversal',
        source_count_meaning='Current authority references plus historical and validation sources; not all are executed',
        raw_native_content_read=False,mutable_observation_logs_read=False,full_dependency_closure_complete=False,
        final_proofs_complete=False,scientific_reproduction_verified=False)
    return scope.request(),authority,baseline


def main():
    stage=Path(sys.argv[1]);self_sha=sys.argv[2]
    require(os.environ.get('PBS_JOBID') and pin(Path(__file__))['sha256']==self_sha,'Pinned PBS collector required')
    remote=Path.home()/'workspace/mcmc4qec/20261024-c3t2-index-relocation-v1'
    accepted=read(pin(remote/'pipeline-submissions/reproduction-v8-finite-snapshot-v2/accepted.json',OLD_ACCEPTED))
    library_pin=accepted['library'];require(library_pin['sha256']==LIBRARY,'Accepted snapshot library required')
    raw=bounded(library_pin['path']);require(hashlib.sha256(raw).hexdigest()==LIBRARY,'Library bytes changed')
    spec=importlib.util.spec_from_file_location('accepted_snapshot_library',library_pin['path']);library=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=library;exec(compile(raw,library_pin['path'],'exec'),library.__dict__)
    request,authority,baseline=collect(stage,library)
    library.save_new(stage/'private-request.json',library.encode(request));library.save_new(stage/'private-authority.json',library.encode(authority))
    receipt=library.snapshot(request,stage/'snapshot')
    require(pin(Path(__file__))['sha256']==self_sha,'Collector changed')
    result=dict(schema=1,purpose='actual_v9_finite_snapshot_collection',pbs_job_id=os.environ['PBS_JOBID'],collector=pin(Path(__file__)),
        library=library_pin,request=pin(stage/'private-request.json'),authority=pin(stage/'private-authority.json'),
        scope_fixture=pin(stage/'scope-fixture-accepted.json'),
        snapshot_receipt=pin(stage/'snapshot/receipt.json'),counts={k:receipt[k] for k in
            ('source_references','metadata_documents','envelope_references','one_hop_edges','external_records','original_text_bytes')},
        public_archive_created=False,full_dependency_closure_complete=False,scientific_reproduction_verified=False,final_proofs_complete=False)
    library.save_new(stage/'accepted.json',library.encode(result));print(json.dumps(result['counts']))


if __name__=='__main__':main()
