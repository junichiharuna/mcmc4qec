"""PBS-only v11 control delta, reusing the accepted v9 scope and snapshot library."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

MAX=4*1024**2
SCOPE_SHA='4c2f1d728feb635e3efe9eb76ccfe4e2793211d28040d3b050c3eab80655cd68'
LIB_SHA='053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a'


def require(ok,message):
    if not ok:raise ValueError(message)


def raw(pin):
    with Path(pin['path']).open('rb') as f:value=f.read(MAX+1)
    require(len(value)<=MAX and hashlib.sha256(value).hexdigest()==pin['sha256'],'Bounded pinned input differs')
    return value


def pin(path):
    with Path(path).open('rb') as f:value=f.read(MAX+1)
    require(len(value)<=MAX,'Source/control too large');return dict(path=str(path),sha256=hashlib.sha256(value).hexdigest())


def module(name,p):
    value=raw(p);spec=importlib.util.spec_from_file_location(name,p['path']);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;exec(compile(value,p['path'],'exec'),m.__dict__);return m


def delta_scope(base_module,library,inventory):
    prefixes=[Path(p) for p in inventory['source_prefixes']]
    explicit={p['path'] for p in inventory['explicit_sources']}
    class DeltaScope(base_module.Scope):
        relative_base=None
        def source(self,record,role,target=None):
            record=dict(record);path=Path(record['path'])
            if not path.is_absolute():
                if self.relative_base is None:return
                path=Path(self.relative_base)/path;record['path']=str(path)
                if target is not None and not Path(target).is_absolute():target=str(Path(self.relative_base)/target)
            if str(path) not in explicit and not any(path.is_relative_to(root) and path!=root for root in prefixes):return
            return super().source(record,role,target)
        def document(self,record,role):
            previous=self.metadata.get(record['path'],{}).get('relative_base')
            requested=record.get('relative_base')
            require(previous is None or requested is None or previous==requested,'Conflicting explicit document bases')
            self.relative_base=requested if requested is not None else previous
            try:
                value=super().document({k:record[k] for k in ('path','sha256')},role)
                self.metadata[record['path']]['relative_base']=self.relative_base
                return value
            finally:self.relative_base=None
    empty=dict(schema=2,roots=inventory['roots'],sources=[],metadata=[],external=inventory['external'],bindings=[],envelope=[],
        expected_source_count=0,expected_envelope_count=0,limits=inventory['limits'],final_proofs_complete=False)
    return DeltaScope(empty,library)


def verify_relative_maps(scope,inventory):
    verified=[]
    for name in ('parent-alias-merge-tests-v1','worker-alias-merge-tests-v1'):
        records=[p for p in inventory['metadata'] if Path(p['path']).parent.name==name and Path(p['path']).name=='sources.json']
        require(len(records)==1,'Exact alias fixture source map required')
        record=records[0];base=Path(record['path']).parent/'test-root'
        require(record['relative_base']==str(base),'Alias fixture map must use explicit test-root')
        values=json.loads(raw(record));count=0
        for relative,sha in values.items():
            if Path(relative).suffix not in {'.py','.sh','.pbs'}:continue
            require(not Path(relative).is_absolute(),'Expected relative fixture declaration')
            absolute=str(base/relative)
            require(scope.sources.get(absolute,{}).get('sha256')==sha,'Alias fixture source missing or resolved incorrectly')
            count+=1
        require(count>0,'Nonempty alias fixture source map required')
        verified.append(dict(map={k:record[k] for k in ('path','sha256')},relative_base=str(base),source_references=count))
    return verified


def main():
    require(os.environ.get('PBS_JOBID'),'Snapshot and fixtures are PBS-only')
    request_pin=dict(path=sys.argv[1],sha256=sys.argv[2]);request=json.loads(raw(request_pin))
    require(request['purpose']=='finite_v11_delta_collection','Exact finite delta request required')
    for p in request['sources'].values():raw(p)
    require(request['scope']['sha256']==SCOPE_SHA and request['library']['sha256']==LIB_SHA,'Accepted helper bytes required')
    old=module('accepted_v9_scope',request['scope']);library=module('accepted_snapshot_v2',request['library'])
    inventory=json.loads(raw(request['inventory']));require(inventory['purpose']=='finite_v11_control_delta_inventory','Exact inventory required')
    stage=Path(request['stage']);require(stage.is_absolute() and not (stage/'snapshot').exists(),'Fresh snapshot output required')
    os.environ['DELTA_SCOPE_SOURCE']=request['scope']['path'];os.environ['DELTA_SNAPSHOT_LIBRARY']=request['library']['path']
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),pattern='test_collect.py'))
    require(result.wasSuccessful() and result.testsRun==8,'Delta fixtures must pass')
    library.save_new(stage/'fixture-accepted.json',library.encode(dict(tests_passed=8,pbs_job_id=os.environ['PBS_JOBID'],
        sources=request['sources'],actual_snapshot_created=False,old_acceptance_not_inherited=True)))
    for p in request['sources'].values():raw(p)
    scope=delta_scope(old,library,inventory)
    for record in inventory['metadata']:scope.document(record,record['category'])
    relative_maps=verify_relative_maps(scope,inventory)
    for record in inventory['explicit_sources']:
        scope.source({k:record[k] for k in ('path','sha256')},record['reason'],record['resolved_path'])
    # Preserve exactly the new collection helpers, without changing the requested science scope.
    for p in [*request['sources'].values(),request['scope'],request['library'],inventory['prepared_by']]:
        old.Scope.source(scope,p,'executed_collection_helper')
    old.Scope.source(scope,pin(stage/'job.sh'),'executed_collection_job')
    for p,role in [(request_pin,'collection_request'),(request['inventory'],'explicit_delta_inventory'),
                   (pin(stage/'fixture-accepted.json'),'delta_fixture_acceptance')]:
        scope.document(p,role)
    final=scope.request();final['limits']=inventory['limits']
    library.save_new(stage/'private-request.json',library.encode(final))
    receipt=library.snapshot(final,stage/'snapshot')
    for p in request['sources'].values():raw(p)
    accepted=dict(schema=1,purpose='private_v11_control_delta_snapshot',pbs_job_id=os.environ['PBS_JOBID'],
        baseline_v9=inventory['baseline'],inventory=request['inventory'],request=pin(stage/'private-request.json'),
        snapshot_receipt=pin(stage/'snapshot/receipt.json'),fixture=pin(stage/'fixture-accepted.json'),sources=request['sources'],
        counts={k:receipt[k] for k in ('source_references','metadata_documents','envelope_references','one_hop_edges','external_records','original_text_bytes')},
        v9_archive_contents_reopened=False,raw_native_content_read=False,scientific_reproduction_verified=False,
        execution_ready=False,final_proofs_complete=False,publicly_distributable=False,relative_source_maps_verified=relative_maps)
    library.save_new(stage/'accepted.json',library.encode(accepted));print(json.dumps(accepted['counts']))


if __name__=='__main__':main()
