"""Prepare a small explicit control inventory; never collect ZIPs or scientific data."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

MAX=4*1024**2
FLOW_SHA='63b8b4d149fdbb56c043fb053e75bfabc73b0b38ea16b88b7dbbd820734d0f4b'
LIB_SHA='053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a'
SOURCE_SUFFIXES={'.py','.sh','.pbs'}
STAGES={
 265647:'parent-alias-merge-tests-v1',265648:'parent-alias-merge-native-v1',
 265649:'parallel-flow-tests-v9',265650:'parallel-flow-native-v10',
 265652:'worker-alias-merge-tests-v1',265653:'worker-alias-merge-native-v1',
 265654:'worker-alias-merge-native-v2',265655:'finite-tail-merge-relocation-tests-v1',
 265656:'finite-tail-merge-relocation-build-v1',265657:'parallel-flow-tests-v10',
 265658:'parallel-flow-native-v11',265659:'finite-tail-outer-relocated-native-v1'}


def require(ok,message):
    if not ok:raise ValueError(message)


def bounded(path):
    p=Path(path);require(p.suffix in SOURCE_SUFFIXES|{'.json'},'Only explicit source/metadata suffix allowed')
    with p.open('rb') as f:raw=f.read(MAX+1)
    require(len(raw)<=MAX,'Small control/source limit exceeded');return raw


def pin(path,expected=None):
    p=Path(path);raw=bounded(p);sha=hashlib.sha256(raw).hexdigest()
    require(expected is None or sha==expected,'Declared control authority changed')
    return dict(path=str(p),sha256=sha)


def load(pin_value):
    raw=bounded(pin_value['path']);require(hashlib.sha256(raw).hexdigest()==pin_value['sha256'],'Pinned metadata changed')
    require(Path(pin_value['path']).suffix=='.json','Only JSON control metadata can be parsed');return json.loads(raw)


def main():
    work=Path.home()/'workspace/mcmc4qec';remote=work/'20261024-c3t2-index-relocation-v1'
    directory=Path(sys.argv[1]);require(directory.is_absolute() and directory.resolve()==directory and not directory.exists(),'Fresh inventory directory required')
    directory.mkdir()
    metadata={};explicit_sources={};absent=[]
    def document(path,role,expected=None,relative_base=None):
        p=pin(path,expected);old=metadata.get(p['path'])
        require(old is None or old['sha256']==p['sha256'],'Conflicting metadata pin')
        metadata[p['path']]=dict(p,category=role,relative_base=str(relative_base) if relative_base else None)
        return load(p)
    def source(path,role,expected=None):
        p=pin(path,expected);require(Path(p['path']).suffix in SOURCE_SUFFIXES,'Explicit source required')
        require(p['path'] not in explicit_sources or explicit_sources[p['path']]['sha256']==p['sha256'],'Conflicting source pin')
        explicit_sources[p['path']]=dict(p,resolved_path=str(Path(p['path']).resolve(strict=True)),reason=role)
    baseline_path=remote/'pipeline-submissions/reproduction-v9-finite-snapshot-v2/accepted.json'
    baseline=document(baseline_path,'baseline_v9_acceptance','7c2bd3750529032d7e3d57429bfe379985129cd8741730ea6267ec3d2b74c45a')
    receipt=document(baseline['snapshot_receipt']['path'],'baseline_v9_receipt',baseline['snapshot_receipt']['sha256'])
    require(baseline['library']['sha256']==LIB_SHA,'Unchanged accepted snapshot library required')
    baseline_external=[]
    for name in ('private-source.zip','private-metadata.zip'):
        artifact=receipt['artifacts'][name]
        baseline_external.append(dict(path=str(Path(baseline['snapshot_receipt']['path']).parent/name),sha256=artifact['sha256'],
            category='unchanged_v9_baseline_archive',reason='Declared baseline only; archive content not read or rehashed'))
    flow_path=work/'20261025-low-parallel-controller-v11/flow-config.json'
    flow=document(flow_path,'current_v11_config',FLOW_SHA)
    source(remote/'output/low_parallel_flow_v10/flow.py','current_v11_executed_flow','1cc96b7bb6688f11471d019b443e7f26f84704036cca1e70a255bd8939e51075')
    for version in (10,11):
        config=flow if version==11 else document(work/f'20261025-low-parallel-controller-v{version}/flow-config.json','historical_v10_config',flow['predecessor']['config']['sha256'])
        migration=document(config['migration']['path'],f'migration_v{version}',config['migration']['sha256'])
        for key in ('predecessor_error','tail_authority'):
            if key in migration:document(migration[key]['path'],f'migration_v{version}_{key}',migration[key]['sha256'])
        for key,p in migration.get('failed_merge',{}).items():
            if Path(p['path']).suffix in SOURCE_SUFFIXES:source(p['path'],'failed_merge_'+key,p['sha256'])
            else:document(p['path'],'failed_merge_'+key,p['sha256'])
        launch=remote/f'pipeline-state/parallel-flow-v{version}-launch'
        for name in ('intent.json','process.json','started.json'):document(launch/name,f'actual_v{version}_launch')
    tail=document(flow['tail']['config']['path'],'current_relocated_outer',flow['tail']['config']['sha256'])
    document(tail['effective_config']['path'],'current_relocated_effective',tail['effective_config']['sha256'])
    for name in ('authority.json','prepared-receipt.json','tail-binding.json'):
        document(Path(flow['tail']['config']['path']).parent/name,'current_tail_relocation')
    # Only named control files are included. No directory recursion or result payload.
    names=('accepted.json','results/accepted.json','request.json','sources.json','test-result.json','terminal.json',
        'submission-intent.json','submission.json','qsub-response.json','deployment.json','prepared-receipt.json')
    for job,stage_name in STAGES.items():
        stage=remote/'pipeline-submissions'/stage_name
        relative=stage/'test-root' if job in (265647,265649,265652,265657) else None
        for name in names:
            path=stage/name
            if path.is_file():document(path,f'job_{job}_control',relative_base=relative)
            else:absent.append(dict(job_number=job,relative_name=name))
        for name in ('job.sh','worker.py','native_probe.py'):
            path=stage/name
            if path.is_file():source(path,f'job_{job}_entrypoint')
    for root,role in ((Path(flow['merge_root']),'current_merge_submission'),
                      (work/'20261025-low-parallel-front-v6/merge-parallel-v1','failed_merge_submission')):
        for name in ('prepared.json','prepared-receipt.json','submission-intent.json','submission.json','qsub-response.json'):
            document(root/name,role)
        source(root/'merge.sh',role)
    # Store genuine terminal observations for the historical acceptances and failures.
    observed=subprocess.run(['qstat','-x','-f','-F','json',*[str(i) for i in range(265647,265660)]],capture_output=True,check=True,timeout=30).stdout
    require(len(observed)<=MAX,'PBS history exceeds bound');rows=json.loads(observed)['Jobs']
    require({int(k.split('.')[0]) for k in rows}==set(range(265647,265660)),'Complete historical job census required')
    for job,row in rows.items():
        number=int(job.split('.')[0]);require(row['job_state']=='F' and row['run_count']==1
            and row['Exit_status']==(1 if number in (265651,265653) else 0),'Historical job outcome differs')
    with (directory/'historical-job-observation.json').open('xb') as f:f.write(observed)
    document(directory/'historical-job-observation.json','actual_historical_job_observation')
    prefix_folders=[remote/'output'/name for name in ('low_parallel_flow_v9','low_parallel_flow_v10',
        'low_parallel_recovery_merge_v7','low_parallel_recovery_merge_v8','finite_tail_merge_relocation_v1','finite_tail_outer_native_v2')]
    prefix_folders += [remote/'pipeline-submissions'/name for name in STAGES.values()]
    value=dict(schema=1,purpose='finite_v11_control_delta_inventory',flow=pin(flow_path,FLOW_SHA),
        baseline=pin(baseline_path),library=baseline['library'],metadata=list(metadata.values()),
        explicit_sources=list(explicit_sources.values()),source_prefixes=list(map(str,prefix_folders)),
        external=baseline_external,absent_optional_control_files=absent,roots=dict(workspace=str(work)),
        limits=dict(file_bytes=MAX,total_bytes=16*1024**2),
        prepared_by=pin(Path(__file__).resolve()),actual_snapshot_created=False,qsub_executed=False,
        raw_native_content_read=False,scientific_reproduction_verified=False)
    with (directory/'inventory.json').open('x') as f:json.dump(value,f,indent=2)
    print(json.dumps(dict(inventory=pin(directory/'inventory.json'),metadata=len(metadata),explicit_sources=len(explicit_sources),qsub_executed=False)))


if __name__=='__main__':main()
