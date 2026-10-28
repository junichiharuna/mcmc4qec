"""Redact a finite private v2 snapshot into a documentary sharing candidate.

Only the pinned snapshot directory is read. External declarations are never
opened, resolved, or stat'ed. Build/compression belongs in a PBS allocation.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import unicodedata
import zipfile

HEX = re.compile(r'[0-9a-f]{64}\Z')
HASH_PART = re.compile(r'([0-9a-f]{64})')
DEFAULT_LIMITS = dict(archive_bytes=128*1024**2, member_bytes=32*1024**2,
                      total_bytes=256*1024**2, files=4096)
PRIVATE_ARTIFACTS = {'private-source.zip', 'private-metadata.zip', 'source-members.json',
                     'metadata-members.json', 'one-hop-edges.json', 'external-index.json', 'envelope-index.json'}
INDEX_CATEGORIES = {'source-members.json':'source_index', 'metadata-members.json':'metadata_index',
                    'one-hop-edges.json':'edge', 'external-index.json':'external', 'envelope-index.json':'envelope'}
FALSE_FLAGS = ('execution_ready', 'scientific_reproduction_verified', 'full_dependency_closure_complete',
               'final_proofs_complete', 'raw_or_native_rehashed', 'publicly_distributable')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf8')


def parse(raw):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))


def valid_hash(value):
    return isinstance(value,str) and HEX.fullmatch(value) is not None


def limits_checked(limits):
    require(set(limits)==set(DEFAULT_LIMITS) and all(type(v) is int and v>0 for v in limits.values()),
            'Positive exact archive limits required')
    require(all(limits[k]<=DEFAULT_LIMITS[k] for k in limits), 'Limits may narrow, not enlarge, the fixed ceiling')
    return limits


def safe_name(name):
    require(isinstance(name,str) and name and '\\' not in name and ':' not in name
            and not any(ord(c)<32 or ord(c)==127 for c in name), 'Unsafe ZIP member name')
    require(not PurePosixPath(name).is_absolute() and all(part not in ('','.','..') for part in name.split('/')),
            'ZIP path traversal or empty component')
    return name


def file_bytes(path, limit, expected=None, expected_size=None):
    path=Path(path)
    require(not path.is_symlink() and path.is_file(), 'Regular non-symlink snapshot artifact required')
    before=path.stat()
    require(before.st_size<=limit, 'Snapshot artifact byte limit exceeded')
    with path.open('rb') as stream:
        raw=stream.read(limit+1)
    after=path.stat()
    identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_mode)
    require(identity(before)==identity(after) and not path.is_symlink() and len(raw)<=limit,
            'Snapshot artifact changed or exceeds byte limit')
    require(expected is None or valid_hash(expected) and digest(raw)==expected, 'Original artifact bytes differ')
    require(expected_size is None or type(expected_size) is int and len(raw)==expected_size, 'Artifact size differs')
    return raw


def zip_members(raw, limits):
    require(len(raw)<=limits['archive_bytes'], 'Compressed archive byte limit exceeded')
    result={}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos=archive.infolist()
            require(len(infos)<=limits['files'], 'ZIP member count limit exceeded')
            require(sum(i.file_size for i in infos)<=limits['total_bytes'], 'Uncompressed ZIP total limit exceeded')
            normalized=set()
            for info in infos:
                name=safe_name(info.filename)
                identity=unicodedata.normalize('NFC',name).casefold()
                require(name not in result and identity not in normalized, 'Duplicate or normalized ZIP member collision')
                normalized.add(identity)
                mode=stat.S_IFMT(info.external_attr>>16)
                require(mode in (0,stat.S_IFREG) and not info.is_dir(), 'Only regular ZIP members permitted')
                require(not info.flag_bits&1 and info.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),
                        'Encrypted or unsupported compressed ZIP member')
                require(0<=info.file_size<=limits['member_bytes'], 'ZIP member byte limit exceeded')
                with archive.open(info) as stream:
                    content=stream.read(limits['member_bytes']+1)
                require(len(content)==info.file_size and len(content)<=limits['member_bytes'], 'ZIP member size differs')
                result[name]=content
    except (zipfile.BadZipFile,RuntimeError,NotImplementedError) as error:
        raise ValueError('Invalid or unsupported ZIP archive') from error
    return result


class Redactor:
    """Explicit literal policy with structural JSON and fail-closed residual scans."""
    def __init__(self,policy):
        require(set(policy)=={'schema','path_prefixes','identifiers','forbidden_patterns'} and policy['schema']==1,
                'Exact redaction policy schema required')
        require(isinstance(policy['path_prefixes'],list) and policy['path_prefixes'], 'Explicit private path prefixes required')
        require(isinstance(policy['identifiers'],list) and isinstance(policy['forbidden_patterns'],list), 'Redaction lists required')
        paths={}; identifiers={}
        for kind,destination in [('path_prefixes',paths),('identifiers',identifiers)]:
            for row in policy[kind]:
                require(set(row)=={'private','public'} and all(isinstance(v,str) and v for v in row.values()),
                        'Explicit private/public redaction pair required')
                private,public=row['private'],row['public']
                require(len(private)>=3 and private!=public and not valid_hash(private)
                        and not any(ord(c)<32 for c in private+public), 'Invalid redaction literal')
                if kind=='path_prefixes':
                    require(PurePosixPath(private).is_absolute() or PureWindowsPath(private).is_absolute(),
                            'Absolute private path prefix required')
                    require(not (PurePosixPath(public).is_absolute() or PureWindowsPath(public).is_absolute()),
                            'Public path must be a symbolic placeholder')
                variants={private,json.dumps(private,ensure_ascii=False)[1:-1]}
                if '\\' in private:variants.add(private.replace('\\','/'))
                for variant in variants:
                    require(variant not in destination or destination[variant]==public, 'Conflicting redaction literal')
                    destination[variant]=public
        self.paths=paths;self.identifiers=identifiers
        self.patterns=[re.compile(pattern,re.IGNORECASE) for pattern in policy['forbidden_patterns']]
        self.patterns += [re.compile(r'/(?:home|Users)/[^\s/"\']+',re.IGNORECASE),
                          re.compile(r'(?<![A-Za-z0-9_])[A-Za-z]:(?:\\+|/)',re.IGNORECASE)]
        self.path_re=re.compile('|'.join(re.escape(k) for k in sorted(paths,key=len,reverse=True)))
        self.identifier_re=(re.compile('|'.join(re.escape(k) for k in sorted(identifiers,key=len,reverse=True)),re.IGNORECASE)
                            if identifiers else None)
        self.identifier_fold={k.casefold():v for k,v in identifiers.items()}
        require(len(self.identifier_fold)==len(identifiers), 'Casefold identifier collision')
        self.summary=dict(path_rules=len(policy['path_prefixes']),identifier_rules=len(policy['identifiers']),
            additional_residual_patterns=len(policy['forbidden_patterns']),
            placeholders=sorted({r['public'] for group in ('path_prefixes','identifiers') for r in policy[group]}))
        for value in self.summary['placeholders']:
            require(self._replace(value)==value, 'Redaction replacements must not cascade')

    def _replace(self,text):
        pieces=HASH_PART.split(text)
        for i,part in enumerate(pieces):
            if valid_hash(part):continue
            part=self.path_re.sub(lambda m:self.paths[m.group(0)],part)
            if self.identifier_re:
                part=self.identifier_re.sub(lambda m:self.identifier_fold[m.group(0).casefold()],part)
            pieces[i]=part
        return ''.join(pieces)

    def check(self,text):
        require(self._replace(text)==text, 'Known private identifier remains or redaction cascades')
        for part in HASH_PART.split(text):
            if not valid_hash(part):
                require(not any(p.search(part) for p in self.patterns), 'Forbidden private path or identifier remains')

    def text(self,text):
        require(isinstance(text,str), 'UTF-8 text required')
        result=self._replace(text)
        self.check(result)
        return result

    def value(self,value):
        if isinstance(value,str):return value if valid_hash(value) else self.text(value)
        if isinstance(value,list):return [self.value(x) for x in value]
        if isinstance(value,dict):
            result={}
            for key,item in value.items():
                renamed=self.text(key)
                require(renamed not in result, 'Redaction creates JSON key collision')
                result[renamed]=self.value(item)
            return result
        return value


def validate_original_indexes(receipt,indexes,containers):
    sources=indexes['source-members.json'];metadata=indexes['metadata-members.json']
    edges=indexes['one-hop-edges.json'];externals=indexes['external-index.json'];envelope=indexes['envelope-index.json']
    require(all(isinstance(x,list) for x in indexes.values()), 'Index arrays required')
    for key,rows in [('source_references',sources),('metadata_documents',metadata),('one_hop_edges',edges),
                     ('external_records',externals),('envelope_references',envelope)]:
        require(type(receipt[key]) is int and receipt[key]==len(rows), 'Index denominator differs')
    internal={};metadata_by_path={}
    for rows,container,category in [(sources,containers['private-source.zip'],'source'),
                                    (metadata,containers['private-metadata.zip'],'metadata')]:
        members=set()
        for row in rows:
            require(isinstance(row,dict) and isinstance(row.get('path'),str) and valid_hash(row.get('sha256'))
                    and type(row.get('bytes')) is int and row['bytes']>=0, 'Original source/metadata index invalid')
            absolute=lambda p:isinstance(p,str) and (PurePosixPath(p).is_absolute() or PureWindowsPath(p).is_absolute())
            require(absolute(row['path']), 'Original absolute declaration required')
            if category=='source':
                require(absolute(row.get('resolved_path')) and type(row.get('alias')) is bool
                        and row['alias']==(row['path']!=row['resolved_path']), 'Original source alias declaration differs')
            else:
                require(row.get('relative_base') is None or absolute(row['relative_base']), 'Original relative base declaration differs')
            require(row['path'] not in internal and row['member'] not in members, 'Duplicate original source/metadata entry')
            name=safe_name(row['member']);members.add(name)
            require(name in container and digest(container[name])==row['sha256'] and len(container[name])==row['bytes'],
                    'Original source/metadata member pin differs')
            require(PurePosixPath(name).suffix in ({'.py','.sh','.pbs'} if category=='source' else {'.json'}),
                    'Unexpected original source/metadata suffix')
            internal[row['path']]=row
            if category=='metadata':metadata_by_path[row['path']]=row
        require(set(container)==members, 'Missing or unlisted private ZIP member')
    for edge in edges:
        document=edge.get('document',{})
        require(document.get('path') in metadata_by_path and document.get('sha256')==metadata_by_path[document['path']]['sha256'],
                'Original edge document pin differs')
        require(isinstance(edge.get('pointer'),str), 'Original edge pointer required')
        if edge.get('collection')=='explicit_scope':
            target=edge.get('resolved_declaration')
            require(edge.get('kind')=='pin' and target in internal and edge.get('sha256')==internal[target]['sha256'],
                    'Internal original edge pin differs')
        else:require(edge.get('collection')=='external', 'Explicit edge boundary required')
    for external in externals:
        require(external.get('original_hash_verified') is False and external.get('bytes_collected') is False,
                'External content must remain unverified and uncollected')
    for row in envelope:
        require(isinstance(row.get('path'),str) and valid_hash(row.get('sha256')), 'Original envelope declaration required')
        if row['path'] in internal:
            require(row['sha256']==internal[row['path']]['sha256'], 'Original envelope pin differs')
        if row.get('category')=='source':require(row['path'] in {s['path'] for s in sources}, 'Envelope source missing')
    require(type(receipt['original_text_bytes']) is int
            and receipt['original_text_bytes']==sum(row['bytes'] for row in sources+metadata), 'Original text byte census differs')


def build(snapshot_directory,receipt_pin,policy,archive_path,*,limits=None):
    limits=limits_checked(DEFAULT_LIMITS if limits is None else limits)
    root=Path(snapshot_directory).absolute();output=Path(archive_path)
    require(root.is_dir() and root.resolve()==root and not root.is_symlink(), 'Canonical snapshot directory required')
    require(not output.exists() and not output.is_symlink(), 'New archive destination required')
    require(set(receipt_pin)=={'path','sha256'} and receipt_pin['path']==str(root/'receipt.json')
            and valid_hash(receipt_pin['sha256']), 'Exact external private receipt pin required')
    receipt_raw=file_bytes(root/'receipt.json',limits['member_bytes'],receipt_pin['sha256'])
    receipt=parse(receipt_raw)
    require(receipt.get('schema')==2 and receipt.get('purpose')=='private_finite_reproduction_snapshot'
            and receipt.get('explicit_source_bytes_verified') is True and receipt.get('explicit_metadata_bytes_verified') is True,
            'Verified finite private snapshot v2 required')
    require(all(receipt.get(k) is False for k in FALSE_FLAGS if k!='execution_ready'), 'Partial documentary scope required')
    require(set(receipt['artifacts'])==PRIVATE_ARTIFACTS, 'Exact private artifact census required')
    private={}
    for name,record in receipt['artifacts'].items():
        require(set(record)=={'sha256','bytes'} and valid_hash(record['sha256']) and type(record['bytes']) is int,
                'Original private artifact pin required')
        private[name]=file_bytes(root/name,limits['archive_bytes'] if name.endswith('.zip') else limits['member_bytes'],
                                 record['sha256'],record['bytes'])
    require(sum(map(len,private.values()))+len(receipt_raw)<=limits['total_bytes'], 'Total private artifact limit exceeded')
    indexes={name:parse(private[name]) for name in INDEX_CATEGORIES}
    containers={name:zip_members(private[name],limits) for name in ('private-source.zip','private-metadata.zip')}
    total=sum(len(raw) for container in containers.values() for raw in container.values())
    require(total+sum(len(private[k]) for k in INDEX_CATEGORIES)<=limits['total_bytes'], 'Total inflated snapshot limit exceeded')
    require(sum(len(c) for c in containers.values())+len(indexes)+3<=limits['files'], 'Total member count limit exceeded')
    validate_original_indexes(receipt,indexes,containers)
    redactor=Redactor(policy);files={};rows=[]
    def add(category,name,original_raw,public_raw,original_member):
        require(name not in files and len(public_raw)<=limits['member_bytes'], 'Public member collision or size exceeded')
        redactor.check(public_raw.decode('utf8'))
        files[name]=public_raw
        rows.append(dict(category=category,member=name,original_member=redactor.text(original_member),
            original_sha256=digest(original_raw),public_sha256=digest(public_raw),original_bytes=len(original_raw),
            public_bytes=len(public_raw),modified_for_sharing=original_raw!=public_raw,original_bytes_verified_during_build=True))
    for category,index,container in [('source','source-members.json','private-source.zip'),
                                      ('metadata','metadata-members.json','private-metadata.zip')]:
        for i,row in enumerate(indexes[index]):
            raw=containers[container][row['member']]
            public=(encode(redactor.value(parse(raw))) if category=='metadata' else redactor.text(raw.decode('utf8')).encode('utf8'))
            name=category+'/'+str(i).zfill(6)+PurePosixPath(row['member']).suffix
            add(category,name,raw,public,row['member'])
    for name,category in INDEX_CATEGORIES.items():
        add(category,'indexes/'+name,private[name],encode(redactor.value(indexes[name])),name)
    add('receipt','indexes/private-receipt.json',receipt_raw,encode(redactor.value(receipt)),'receipt.json')
    manifest=dict(schema=2,purpose='finite_snapshot_sharing_candidate',artifacts=rows,
        original_snapshot_receipt_sha256=receipt_pin['sha256'],original_container_pins=receipt['artifacts'],
        redaction_policy_canonical_sha256=digest(encode(policy)),redaction_policy=redactor.summary,
        known_identifiers_redacted=True,publication_review_required=True,
        **{key:False for key in FALSE_FLAGS},
        warnings=['Embedded original hashes identify private bytes; public hashes are recorded separately.',
                  'Do not pass redacted declarations to original frozen validators.',
                  'External raw/native declarations were not opened, stat-ed, collected, or rehashed.',
                  'This documentary candidate is not a relocated or executable scientific environment.',
                  'Unknown, encoded, or undeclared identifiers and sensitive contents still require manual review.'])
    files['manifest.json']=encode(manifest)
    files['README.txt']=b'Documentary sharing candidate only. Embedded pins identify private original bytes.\nExecution and scientific reproduction are not verified.\n'
    require(sum(map(len,files.values()))<=limits['total_bytes'] and len(files)<=limits['files'], 'Public archive limit exceeded')
    for raw in files.values():redactor.check(raw.decode('utf8'))
    # Verify the fixed private artifacts again; do not follow embedded paths.
    file_bytes(root/'receipt.json',limits['member_bytes'],receipt_pin['sha256'])
    for name,record in receipt['artifacts'].items():
        file_bytes(root/name,limits['archive_bytes'] if name.endswith('.zip') else limits['member_bytes'],record['sha256'],record['bytes'])
    require(output.parent.is_dir(), 'Existing output parent required')
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,raw in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;archive.writestr(info,raw)
    archive_raw=file_bytes(output,limits['archive_bytes'])
    return dict(archive_sha256=digest(archive_raw),manifest_sha256=digest(files['manifest.json']),artifacts=len(rows),
                private_original_bytes_verified_during_build=True,execution_ready=False,
                scientific_reproduction_verified=False,publication_review_required=True)


def verify(archive_path,expected_archive_sha256,*,limits=None):
    limits=limits_checked(DEFAULT_LIMITS if limits is None else limits)
    require(valid_hash(expected_archive_sha256), 'External public archive hash required')
    raw=file_bytes(archive_path,limits['archive_bytes'],expected_archive_sha256)
    files=zip_members(raw,limits)
    require('manifest.json' in files and 'README.txt' in files, 'Public manifest/readme required')
    manifest=parse(files['manifest.json'])
    require(manifest.get('schema')==2 and manifest.get('purpose')=='finite_snapshot_sharing_candidate'
            and all(manifest.get(k) is False for k in FALSE_FLAGS)
            and manifest.get('publication_review_required') is True, 'Documentary sharing scope required')
    require(valid_hash(manifest.get('original_snapshot_receipt_sha256'))
            and valid_hash(manifest.get('redaction_policy_canonical_sha256')), 'Original receipt/policy hashes required')
    expected={'manifest.json','README.txt'}
    for row in manifest['artifacts']:
        name=safe_name(row['member'])
        require(name not in expected and name in files, 'Duplicate or missing public artifact')
        expected.add(name)
        require(valid_hash(row['original_sha256']) and valid_hash(row['public_sha256'])
                and digest(files[name])==row['public_sha256'] and len(files[name])==row['public_bytes'], 'Public artifact bytes differ')
        require(row['modified_for_sharing']==(row['original_sha256']!=row['public_sha256'])
                and row['original_bytes_verified_during_build'] is True, 'Original/public hash distinction differs')
    require(set(files)==expected, 'Missing or unlisted public ZIP member')
    return dict(public_bytes_verified=True,original_private_bytes_reverified=False,external_hashes_reverified=False,
                artifacts=len(manifest['artifacts']),execution_ready=False,scientific_reproduction_verified=False,
                publication_review_required=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    package=sub.add_parser('build');package.add_argument('--snapshot',required=True);package.add_argument('--receipt-sha256',required=True)
    package.add_argument('--policy',required=True);package.add_argument('--archive',required=True)
    check=sub.add_parser('verify');check.add_argument('--archive',required=True);check.add_argument('--sha256',required=True)
    args=parser.parse_args()
    if args.command=='build':
        require(__import__('os').environ.get('PBS_JOBID'), 'Build and compression require qsub')
        policy=parse(file_bytes(args.policy,DEFAULT_LIMITS['member_bytes']))
        result=build(args.snapshot,dict(path=str(Path(args.snapshot).absolute()/'receipt.json'),sha256=args.receipt_sha256),policy,args.archive)
    else:result=verify(args.archive,args.sha256)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
