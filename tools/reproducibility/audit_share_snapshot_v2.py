"""PBS-only documentary candidate audit and bounded review samples."""
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import zipfile


def require(ok,message):
    if not ok:raise ValueError(message)


def raw(pin):
    data=Path(pin['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest()==pin['sha256'],'Audit input pin differs')
    return data


def save(path,value):
    with path.open('x',encoding='utf8',newline='\n') as stream:json.dump(value,stream,sort_keys=True,indent=2,ensure_ascii=False)


def main():
    require(os.environ.get('PBS_JOBID'),'Audit must run via qsub')
    request_pin=dict(path=sys.argv[1],sha256=sys.argv[2]);request=json.loads(raw(request_pin));stage=Path(sys.argv[1]).parent
    accepted=json.loads(raw(request['candidate_acceptance']));policy=json.loads(raw(accepted['policy']))
    descriptor=accepted['sources']['share_snapshot_v2_revision2.py'];source=raw(descriptor)
    spec=importlib.util.spec_from_file_location('reviewed_share_exporter',descriptor['path']);lib=importlib.util.module_from_spec(spec)
    exec(compile(source,descriptor['path'],'exec'),lib.__dict__)
    public=lib.zip_members(raw(accepted['archive']),lib.DEFAULT_LIMITS)
    verified=lib.verify(accepted['archive']['path'],accepted['archive']['sha256'])
    manifest=lib.parse(public['manifest.json']);receipt=lib.parse(raw(accepted['snapshot_receipt']))
    require(manifest['original_snapshot_receipt_sha256']==accepted['snapshot_receipt']['sha256'],'Original v8 receipt differs')
    require(manifest['redaction_policy_canonical_sha256']==lib.digest(lib.encode(policy)),'Private/public policy hash differs')
    redactor=lib.Redactor(policy)
    rules=[]
    for kind in ('path_prefixes','identifiers'):
        for index,row in enumerate(policy[kind]):
            variants={row['private'],json.dumps(row['private'],ensure_ascii=False)[1:-1]}
            if '\\' in row['private']:variants.add(row['private'].replace('\\','/'))
            rules.append((kind,index,[v.casefold() for v in variants]))
    def literal_hits(text):
        pieces=[p.casefold() for p in lib.HASH_PART.split(text) if not lib.valid_hash(p)]
        return [dict(kind=kind,index=index,matches=sum(p.count(v) for p in pieces for v in variants))
                for kind,index,variants in rules if any(v in p for p in pieces for v in variants)]
    candidate_hits=[]
    for member,data in public.items():
        text=member+'\n'+data.decode('utf8');redactor.check(text)
        found=literal_hits(text)
        if found:candidate_hits.append(dict(member=member,hits=found))
    require(not candidate_hits,'Known private policy literal remains in candidate')
    sidecar=lib.zip_members(raw(accepted['builder_source_archive']),lib.DEFAULT_LIMITS)
    expected={'tools/reproducibility/'+name:descriptor for name,descriptor in accepted['sources'].items()}
    require(set(sidecar)==set(expected) and len(sidecar)==7,'Exact seven-source sidecar required')
    sidecar_hits=[];actual_hits=[]
    for member,data in sidecar.items():
        require(data==raw(expected[member]),'Sidecar differs from pinned generic source')
        text=data.decode('utf8');hits=literal_hits(text)
        if hits:sidecar_hits.append(dict(member=member,policy_hits=hits))
        for i,literal in enumerate(request['actual_identifiers']):
            # Values stay private; reviewers get only IDs and bounded contexts.
            pattern=re.compile(re.escape(literal),re.IGNORECASE)
            matches=list(pattern.finditer(text))
            if matches:actual_hits.append(dict(member=member,identifier_index=i,count=len(matches),
                line_numbers=[text.count('\n',0,m.start())+1 for m in matches[:5]]))
    snapshot_root=Path(accepted['snapshot_receipt']['path']).parent
    originals={}
    for name in ('private-source.zip','private-metadata.zip'):
        record=receipt['artifacts'][name]
        originals[name]=lib.zip_members(lib.file_bytes(snapshot_root/name,lib.DEFAULT_LIMITS['archive_bytes'],
            record['sha256'],record['bytes']),lib.DEFAULT_LIMITS)
    def scalars(value):
        values=Counter()
        if isinstance(value,dict):
            for item in value.values():values.update(scalars(item))
        elif isinstance(value,list):
            for item in value:values.update(scalars(item))
        elif type(value) in (int,float,bool) or value is None:values[(type(value).__name__,repr(value))]+=1
        elif lib.valid_hash(value):values[('original_hash',value)]+=1
        return values
    checked_sources=checked_metadata=0
    for row in manifest['artifacts']:
        if row['category'] not in ('source','metadata'):continue
        # Redacted member names can differ, so locate the original by its index position.
        category=row['category'];index=int(Path(row['member']).stem)
        table_name='source-members.json' if category=='source' else 'metadata-members.json'
        record=receipt['artifacts'][table_name]
        if table_name not in originals:
            originals[table_name]=lib.parse(lib.file_bytes(snapshot_root/table_name,lib.DEFAULT_LIMITS['member_bytes'],record['sha256'],record['bytes']))
        origin=originals[table_name][index];container='private-source.zip' if category=='source' else 'private-metadata.zip'
        before=originals[container][origin['member']];after=public[row['member']]
        require(lib.digest(before)==row['original_sha256']==origin['sha256'],'Original member pin differs')
        require(Counter(re.findall(rb'[0-9a-f]{64}',before))==Counter(re.findall(rb'[0-9a-f]{64}',after)),
                'Embedded original hash census changed')
        if category=='metadata':
            require(scalars(lib.parse(before))==scalars(lib.parse(after)),'Numeric/boolean/seed/hash metadata scalar census changed')
            checked_metadata+=1
        else:checked_sources+=1
    samples={}
    for category in ('source','metadata','edge','external','envelope'):
        row=next(r for r in manifest['artifacts'] if r['category']==category)
        data=public[row['member']];samples[category]=dict(member=row['member'],text=data[:2000].decode('utf8',errors='ignore'),truncated=len(data)>2000)
    samples['README']=dict(member='README.txt',text=public['README.txt'].decode('utf8')[:2000],truncated=False)
    save(stage/'redacted-samples.json',samples)
    # Snapshot-afterwards helper sources are retained exactly in a separate supplement.
    supplement=stage/'operational-source-supplement.zip';supplement_rows=[]
    with zipfile.ZipFile(supplement,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,pin in sorted(request['supplement_sources'].items()):
            data=raw(pin);member='tools/reproducibility/'+name
            require('/' not in name and '\\' not in name,'Simple supplemental source name required')
            info=zipfile.ZipInfo(member,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;archive.writestr(info,data)
            supplement_rows.append(dict(member=member,sha256=pin['sha256'],bytes=len(data)))
    manifest_summary={k:v for k,v in manifest.items() if k not in ('artifacts','original_container_pins')}
    manifest_summary['artifact_categories']=dict(Counter(r['category'] for r in manifest['artifacts']))
    save(stage/'manifest-summary.json',manifest_summary)
    report=dict(schema=1,purpose='finite_v8_candidate_identifier_audit',pbs_job_number=os.environ['PBS_JOBID'].split('.')[0],
        candidate_acceptance_sha256=request['candidate_acceptance']['sha256'],archive_sha256=accepted['archive']['sha256'],public_byte_verification=verified,
        candidate_members_scanned=len(public),candidate_policy_literal_hits=candidate_hits,
        sidecar_source_count=len(sidecar),sidecar_pinned_bytes_match=True,sidecar_policy_hits=sidecar_hits,
        sidecar_actual_identifier_hits=actual_hits,sidecar_synthetic_fixture_review_required=True,
        source_original_hash_census_preserved=checked_sources,metadata_numeric_boolean_hash_census_preserved=checked_metadata,
        supplemental_source_manifest=supplement_rows,supplemental_archive_sha256=hashlib.sha256(supplement.read_bytes()).hexdigest(),
        raw_native_content_read=False,external_paths_followed=False,original_sources_modified=False,
        unknown_identifiers_absence_certified=False,independent_manual_review_complete=False,
        snapshot_scope='Saved v8 point-in-time; later controller changes are excluded',uploaded=False)
    save(stage/'audit-report.json',report)
    print(json.dumps(dict(candidate_members_scanned=len(public),candidate_policy_literal_hits=len(candidate_hits),
        sidecar_actual_identifier_hits=len(actual_hits),uploaded=False)))


if __name__=='__main__':main()
