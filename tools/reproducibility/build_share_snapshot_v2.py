"""PBS-only pinned build of a documentary candidate and generic builder sidecar."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile


def require(ok,message):
    if not ok:raise ValueError(message)


def read(pin,limit=32*1024**2):
    require(set(pin)=={'path','sha256'} and Path(pin['path']).is_absolute(),'Exact private input pin required')
    with Path(pin['path']).open('rb') as stream:raw=stream.read(limit+1)
    require(len(raw)<=limit and hashlib.sha256(raw).hexdigest()==pin['sha256'],'Private input pin or limit differs')
    return raw


def pin(path):
    return dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def load(name,descriptor):
    raw=read(descriptor);spec=importlib.util.spec_from_file_location(name,descriptor['path'])
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    exec(compile(raw,descriptor['path'],'exec'),module.__dict__)
    return module


def save(path,value):
    with Path(path).open('x',encoding='utf8',newline='\n') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,ensure_ascii=False)
        stream.write('\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args();job=os.environ.get('PBS_JOBID','');require(job,'qsub allocation required')
    request_pin=dict(path=args.request,sha256=args.sha256);request=json.loads(read(request_pin))
    stage=Path(args.request).parent
    require(request['purpose']=='finite_v2_revision2_sharing_candidate_build','Exact native sharing request required')
    sources=request['sources']
    required={'snapshot_v2.py','share_snapshot_v2_revision2.py','test_share_snapshot_v2_revision2.py','share_policy_v2.py',
              'test_share_policy_v2.py','build_share_snapshot_v2.py','deploy_share_snapshot_v2.py'}
    require(set(sources)==required and sources['build_share_snapshot_v2.py']==pin(Path(__file__).resolve()),
            'Exact pinned candidate builder closure required')
    for source in sources.values():read(source)
    library=load('share_snapshot_v2_revision2',sources['share_snapshot_v2_revision2.py'])
    policy_builder=load('share_policy_v2',sources['share_policy_v2.py'])
    fixture=json.loads(read(request['exporter_fixture']))
    require(fixture['tests_passed']==29 and fixture['sources']['share_snapshot_v2_revision2.py']==sources['share_snapshot_v2_revision2.py'],
            'Separate accepted 29-fixture revision2 exporter required')
    original=json.loads(read(request['snapshot_acceptance']))
    require(original['purpose']=='actual_v8_finite_snapshot_collection' and original['snapshot_receipt']==request['snapshot_receipt']
            and original['full_dependency_closure_complete'] is False and original['scientific_reproduction_verified'] is False,
            'Original finite v8 snapshot receipt required')
    authority_jobs=[fixture['pbs_job_id'],original['pbs_job_id']]
    observed=json.loads(subprocess.check_output(['qstat','-xf','-F','json',*authority_jobs],timeout=30))
    require(set(observed['Jobs'])==set(authority_jobs),'Exact authority PBS census required')
    require(all(v['job_state']=='F' and v['Exit_status']==0 and v['run_count']==1 for v in observed['Jobs'].values()),
            'Accepted fixture and snapshot PBS terminal required')
    save(stage/'authority-terminal.json',observed)
    response=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(Path(__file__).parent),
        '-p','test_share_policy_v2.py','-v'],capture_output=True,text=True,timeout=60)
    (stage/'policy-fixtures.stdout').write_text(response.stdout);(stage/'policy-fixtures.stderr').write_text(response.stderr)
    require(response.returncode==0 and re.search(r'Ran 3 tests in .*\n\nOK\s*$',response.stderr),'Policy fixtures failed')
    receipt=library.parse(read(request['snapshot_receipt']))
    root=Path(request['snapshot_receipt']['path']).parent
    require(set(receipt['artifacts'])==library.PRIVATE_ARTIFACTS,'Original finite artifact set required')
    raw={name:library.file_bytes(root/name,library.DEFAULT_LIMITS['archive_bytes'] if name.endswith('.zip')
         else library.DEFAULT_LIMITS['member_bytes'],record['sha256'],record['bytes']) for name,record in receipt['artifacts'].items()}
    indexes={name:library.parse(raw[name]) for name in library.INDEX_CATEGORIES}
    containers={name:library.zip_members(raw[name],library.DEFAULT_LIMITS) for name in ('private-source.zip','private-metadata.zip')}
    library.validate_original_indexes(receipt,indexes,containers)
    documents=[receipt,*indexes.values(),*[library.parse(content) for content in containers['private-metadata.zip'].values()]]
    policy=policy_builder.derive_policy(documents,[content.decode('utf8') for content in containers['private-source.zip'].values()])
    # Fixed policy is private; it never enters the shareable directory.
    save(stage/'private-redaction-policy.json',policy)
    shareable=stage/'shareable';shareable.mkdir()
    archive=shareable/'finite-v8-sharing-candidate.zip'
    result=library.build(root,request['snapshot_receipt'],policy,archive)
    verified=library.verify(archive,result['archive_sha256'])
    require(verified['public_bytes_verified'] is True and verified['execution_ready'] is False,'Candidate public-byte verification failed')
    # Preserve newly created generic tooling as a separate, reproducible sidecar.
    sidecar=shareable/'builder-source.zip';sidecar_rows=[]
    with zipfile.ZipFile(sidecar,'x',compression=zipfile.ZIP_DEFLATED) as bundle:
        for name,source in sorted(sources.items()):
            content=read(source)
            # Preserve exact generic tooling, including explicitly synthetic
            # fixture names. Sidecar identifier review is recorded separately.
            content.decode('utf8')
            info=zipfile.ZipInfo('tools/reproducibility/'+name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;bundle.writestr(info,content)
            sidecar_rows.append(dict(member=info.filename,sha256=source['sha256'],bytes=len(content)))
    sidecar_manifest=dict(schema=1,purpose='exact_generic_candidate_builder_sources',files=sidecar_rows,
        private_policy_included=False,private_policy_canonical_sha256=library.digest(library.encode(policy)),
        original_snapshot_receipt_sha256=request['snapshot_receipt']['sha256'],
        original_execution_script_sha256=pin(stage/'job.sh')['sha256'],
        fixture_identifiers_are_synthetic=True,independent_identifier_review_complete=False,
        execution_ready=False,scientific_reproduction_verified=False,publication_review_required=True)
    save(shareable/'builder-source-manifest.json',sidecar_manifest)
    for source in sources.values():read(source)
    read(request['snapshot_receipt'])
    summary=dict(schema=1,purpose='finite_v8_documentary_sharing_candidate',
        archive=dict(name=archive.name,sha256=result['archive_sha256'],bytes=archive.stat().st_size),
        builder_sources=dict(name=sidecar.name,sha256=pin(sidecar)['sha256'],bytes=sidecar.stat().st_size),
        original_snapshot_receipt_sha256=request['snapshot_receipt']['sha256'],
        redaction_policy_canonical_sha256=library.digest(library.encode(policy)),
        artifacts=result['artifacts'],public_bytes_verified=True,
        raw_native_content_read=False,original_private_artifacts_unchanged=True,
        execution_ready=False,scientific_reproduction_verified=False,full_dependency_closure_complete=False,
        final_proofs_complete=False,publicly_distributable=False,publication_review_required=True,
        independent_identifier_review_complete=False,uploaded=False)
    save(shareable/'candidate-summary.json',summary)
    accepted=dict(schema=1,purpose='actual_finite_v8_sharing_candidate_build',pbs_job_id=job,request=request_pin,
        sources=sources,exporter_fixture=request['exporter_fixture'],snapshot_receipt=request['snapshot_receipt'],
        execution_script=pin(stage/'job.sh'),
        policy=pin(stage/'private-redaction-policy.json'),policy_fixture_tests=3,
        archive=pin(archive),builder_source_archive=pin(sidecar),candidate_summary=pin(shareable/'candidate-summary.json'),
        public_bytes_verified=True,raw_native_content_read=False,original_private_artifacts_unchanged=True,
        independent_identifier_review_complete=False,execution_ready=False,scientific_reproduction_verified=False,uploaded=False)
    save(stage/'accepted.json',accepted)
    print(json.dumps(dict(archive_sha256=result['archive_sha256'],artifacts=result['artifacts'],uploaded=False)))


if __name__=='__main__':main()
