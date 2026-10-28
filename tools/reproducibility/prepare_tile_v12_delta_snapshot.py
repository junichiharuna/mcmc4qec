"""Prepare only bounded immutable control inventory for the v12 delta."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

MAX=4*1024**2
FLOW='083a22ca37fe46eb31f2f1034554f76aeffa77e77c273e33627e14e67318838e'
READY='e498798f93748a0a9e07b04c520b04daba4b8c1b78f84b4e91e5f59cfdad5d21'
TAIL='9db38edad846a9f1321a4a4f102d7b402662856716611e7505f26e9eb56c54b6'
LIB='053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a'
STAGES=['finite-tail-binding-namespace-tests-v1','finite-tail-binding-namespace-tests-v2',
 'acceptance-observer-tests-v1','shared-home-witness-a-v1','acceptance-observer-native-v1',
 'finite-tail-namespace-joint-tests-v1','finite-tail-cross-host-build-v1',
 'finite-tail-namespace-joint-tests-v2','finite-tail-cross-host-build-v2',
 'parallel-flow-tests-v11','parallel-flow-native-v12','finite-tail-completed-merge-native-v1']
SUFFIX={'.py','.sh','.pbs'}


def bounded(path):
    p=Path(path);assert p.suffix in SUFFIX|{'.json'}
    with p.open('rb') as f:b=f.read(MAX+1)
    assert len(b)<=MAX
    return b


def pin(path,expected=None):
    value=dict(path=str(path),sha256=hashlib.sha256(bounded(path)).hexdigest())
    assert expected is None or value['sha256']==expected
    return value


def main():
    w=Path.home()/'workspace/mcmc4qec';r=w/'20261024-c3t2-index-relocation-v1'
    directory=Path(sys.argv[1]);assert directory.is_absolute() and not directory.exists();directory.mkdir()
    docs={};sources={};maps=[];absent=[]
    def doc(path,role,expected=None,base=None):
        p=pin(path,expected);old=docs.get(p['path']);assert old is None or old['sha256']==p['sha256']
        assert old is None or base is None or old.get('relative_base') in (None,str(base))
        docs[p['path']]=dict(p,category=role,relative_base=str(base) if base else (old or {}).get('relative_base'))
        return json.loads(bounded(path))
    def dp(p,role):return doc(p['path'],role,p['sha256'])
    def source(p,role):
        fixed=pin(p['path'],p['sha256']);assert Path(p['path']).suffix in SUFFIX
        sources[p['path']]=dict(fixed,resolved_path=str(Path(p['path']).resolve(strict=True)),reason=role)
    baseline_path=r/'pipeline-submissions/reproduction-v11-control-delta-v1/accepted.json'
    baseline=doc(baseline_path,'baseline_v11_acceptance','7b98b1637628e22759f9f83e1f4038cbbd4f019d5574c14501cdfe724d86edfb')
    receipt=dp(baseline['snapshot_receipt'],'baseline_v11_receipt')
    external=[dict(path=str(Path(baseline['snapshot_receipt']['path']).parent/name),sha256=receipt['artifacts'][name]['sha256'],
        category='unchanged_v11_baseline_archive',reason='Declared archive only; bytes not reopened') for name in ('private-source.zip','private-metadata.zip')]
    flow_path=w/'20261025-low-parallel-controller-v12/flow-config.json';flow=doc(flow_path,'actual_v12_config',FLOW)
    source(dict(path=str(r/'output/low_parallel_flow_v11/flow.py'),sha256='c08c21a859fccaaef227ed603f9aaf76a5403d0f7892e1a528dbaedaf27d088b'),'actual_v12_flow')
    migration=dp(flow['migration'],'actual_v12_migration')
    # Only named pinned control records, never the whole old or current journal.
    for key in ('predecessor_error','observer_authority'):
        if key in migration:dp(migration[key],'migration_'+key)
    for name,expected in [('started.json','aab0c28c442b3ae702264d9bba57ad3850a123ab6dfb19154dac0ae73517d932'),
                          ('process.json','74f1fddf3fb257a36d0ac8444ac5fcf5872dc5b1048ffac4d61a8a04fca2d6b9'),('intent.json',None)]:
        doc(r/'pipeline-state/parallel-flow-v12-launch'/name,'immutable_v12_launch',expected)
    observer=doc(r/'output/merge_terminal_acceptance_observer_v1/production-ready.json','observer_ready',READY)
    for key in ('authority','binding','namespace_authority','actual_native_acceptance','actual_native_request','actual_native_terminal',
                'fixture_acceptance','fixture_terminal','original_completion','original_prepared'):
        dp(observer[key],'observer_'+key)
    for key in ('observer','actual_native_worker','original_wrapper'):source(observer[key],'observer_'+key)
    completion=dp(observer['original_completion'],'original_acceptance_completion')
    for key in ('accepted','terminal'):
        dp(completion['artifacts'][key],'original_merge_'+key)
    for key in ('claim','native_preflight'):dp(completion[key],'original_acceptance_'+key)
    acceptance_root=Path(observer['original_prepared']['path']).parent
    for name in ('submission-intent.json','submission.json','qsub-response.json','actual-pbs-start.json','actual-pbs-end.json'):
        doc(acceptance_root/name,'original_acceptance_submission')
    source(pin(acceptance_root/'job.sh'),'original_acceptance_script')
    authority=dp(observer['authority'],'observer_authority')
    for key in ('controller_witness','producer_snapshot'):dp(authority[key],'observer_'+key)
    source(authority['namespace_helper'],'namespace_helper')
    namespace=dp(observer['namespace_authority'],'namespace_authority')
    dp(namespace['server'],'namespace_server_witness')
    for item in namespace['clients']:
        for key in ('terminal','witness'):dp(item[key],'namespace_client_'+key)
        source(item['script'],'namespace_client_script')
    tailready=doc(r/'pipeline-submissions/finite-tail-completed-merge-native-v1/ready.json','tail_ready',TAIL)
    tail=dp(tailready['configuration'],'actual_tail_config');assert tailready['configuration']==flow['tail']['config']
    for key in ('fixture','namespace_roundtrip','native_constructor','request','roundtrip_request','terminal'):dp(tailready[key],'tail_'+key)
    for key in ('binding','dispatch'):source(tail[key],'actual_tail_'+key)
    for name in ('authority.json','prepared-receipt.json','tail-binding.json'):
        p=Path(tailready['configuration']['path']).parent/name
        if p.is_file():doc(p,'tail_cross_host_control')
        else:absent.append(dict(stage='tail_config',name=name))
    names=('accepted.json','results/accepted.json','fixture-accepted.json','request.json','sources.json','source-pins.json',
           'terminal.json','submission-intent.json','submission.json','qsub-response.json','deployment.json','prepared-receipt.json','fixture-inputs.json')
    for name in STAGES:
        stage=r/'pipeline-submissions'/name;base=stage/'test-root' if name=='parallel-flow-tests-v11' else None
        for filename in names:
            p=stage/filename
            if p.is_file():
                doc(p,'historical_stage_'+name,base=base)
                if filename=='sources.json':maps.append(docs[str(p)])
            else:absent.append(dict(stage=name,name=filename))
        for filename in ('job.sh','worker.py','native_probe.py'):
            p=stage/filename
            if p.is_file():source(pin(p),'historical_stage_entrypoint')
    assert len(maps)==6
    observed=subprocess.run(['qstat','-x','-f','-F','json',*[str(i) for i in range(265663,265675)]],capture_output=True,check=True,timeout=30).stdout
    assert len(observed)<=MAX;rows=json.loads(observed)['Jobs'];assert {int(k.split('.')[0]) for k in rows}==set(range(265663,265675))
    for job,row in rows.items():
        number=int(job.split('.')[0]);assert row['job_state']=='F' and row['run_count']==1 and row['Exit_status']==(1 if number in (265663,265668,265669) else 0)
    with (directory/'historical-job-observation.json').open('xb') as f:f.write(observed)
    doc(directory/'historical-job-observation.json','actual_historical_job_observation')
    prefixes=[r/'pipeline-submissions'/name for name in STAGES]
    prefixes += [r/'output/low_parallel_flow_v11',r/'output/merge_terminal_acceptance_observer_v1',w/'20261025-finite-tail-cross-host-v2/sources']
    library=dict(path=str(r/'pipeline-submissions/reproduction-snapshot-v2-tests-v2/source/snapshot_v2.py'),sha256=LIB)
    value=dict(schema=1,purpose='finite_v12_control_delta_inventory',flow=pin(flow_path,FLOW),baseline=pin(baseline_path),
        library=library,metadata=list(docs.values()),explicit_sources=list(sources.values()),source_maps=maps,
        source_prefixes=list(map(str,prefixes)),external=external,absent_optional_control_files=absent,roots=dict(workspace=str(w)),
        limits=dict(file_bytes=MAX,total_bytes=16*1024**2),prepared_by=pin(Path(__file__).resolve()),
        actual_snapshot_created=False,qsub_executed=False,raw_native_content_read=False,scientific_reproduction_verified=False)
    with (directory/'inventory.json').open('x') as f:json.dump(value,f,indent=2)
    print(json.dumps(dict(inventory=pin(directory/'inventory.json'),metadata=len(docs),explicit_sources=len(sources),source_maps=len(maps),qsub_executed=False)))


if __name__=='__main__':main()
