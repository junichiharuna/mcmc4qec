"""Dedicated v2 public-candidate fixtures; execute through qsub only."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import snapshot_v2 as original
import share_snapshot_v2_revision2 as share


class ShareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.private = self.root / 'private'
        self.native = self.root / 'native.so'; self.native.write_bytes(b'NEVER OPEN EXTERNAL')
        self.source = self.root / 'source.py'
        self.source.write_text("ROOT = '/home/privateuser/work'\nHOST = 'private-host'\nPIN = '" + 'a'*64 + "'\n")
        self.meta = self.root / 'metadata.json'
        self.meta.write_bytes(original.encode(dict(source=self.pin(self.source), native=self.pin(self.native),
            owner='privateuser@private-host', original_hash='a'*64,
            windows=r'C:\Users\privateuser\work', escaped_source="C:\\Users\\privateuser\\work")))
        request=dict(schema=2,roots=dict(workspace=str(self.root)),
            sources=[dict(self.pin(self.source),resolved_path=str(self.source))],
            metadata=[dict(self.pin(self.meta),category='fixture',relative_base=None)],
            external=[dict(self.pin(self.native),category='native',reason='No bytes read')],bindings=[],
            envelope=[dict(self.pin(self.source),category='source'),dict(self.pin(self.native),category='native')],
            expected_source_count=1,expected_envelope_count=2,
            limits=dict(file_bytes=65536,total_bytes=1048576),final_proofs_complete=False)
        original.snapshot(request,self.private)
        self.receipt_pin=self.pin(self.private/'receipt.json')
        self.policy=dict(schema=1,path_prefixes=[dict(private=str(self.root),public='${FIXTURE_ROOT}'),
            dict(private='/home/privateuser',public='${HOME_ROOT}'),
            dict(private=r'C:\Users\privateuser',public='${WINDOWS_HOME}')],
            identifiers=[dict(private='privateuser',public='ACCOUNT_01'),dict(private='private-host',public='NODE_01')],
            forbidden_patterns=[r'privateuser',r'private-host'])
        self.output=self.root/'shared.zip'

    def pin(self,path):return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def build(self,**kwargs):
        return share.build(self.private,self.receipt_pin,self.policy,self.output,**kwargs)

    def repin(self,name):
        receipt=json.loads((self.private/'receipt.json').read_bytes())
        p=self.private/name
        receipt['artifacts'][name]=dict(sha256=self.pin(p)['sha256'],bytes=p.stat().st_size)
        (self.private/'receipt.json').write_bytes(original.encode(receipt))
        self.receipt_pin=self.pin(self.private/'receipt.json')

    def rewrite_zip(self,entries):
        p=self.private/'private-source.zip'
        with zipfile.ZipFile(p,'w') as archive:
            for name,raw in entries:archive.writestr(name,raw)
        self.repin('private-source.zip')

    def test_round_trip_separate_original_public_hashes_and_flags(self):
        result=self.build();verified=share.verify(self.output,result['archive_sha256'])
        self.assertTrue(verified['public_bytes_verified'])
        self.assertFalse(verified['original_private_bytes_reverified'])
        self.assertFalse(verified['execution_ready'])
        with zipfile.ZipFile(self.output) as archive:
            manifest=json.loads(archive.read('manifest.json'))
            self.assertFalse(manifest['scientific_reproduction_verified'])
            self.assertFalse(manifest['full_dependency_closure_complete'])
            self.assertTrue(manifest['publication_review_required'])
            rows=manifest['artifacts']; self.assertTrue(any(r['original_sha256'] != r['public_sha256'] for r in rows))
            for row in rows:
                self.assertEqual(hashlib.sha256(archive.read(row['member'])).hexdigest(),row['public_sha256'])
            payload=b'\n'.join(archive.read(n) for n in archive.namelist())
            for secret in (b'privateuser',b'private-host',str(self.root).encode(),b'/home/privateuser'):
                self.assertNotIn(secret,payload)
            self.assertIn(('a'*64).encode(),payload)
            metadata=json.loads(archive.read(next(r['member'] for r in rows if r['category']=='metadata')))
            self.assertEqual(metadata['source']['sha256'],self.pin(self.source)['sha256'])

    def test_no_external_source_or_native_open_stat_after_snapshot(self):
        old_open=Path.open; old_stat=Path.stat
        blocked={self.source,self.meta,self.native}
        def opened(path,*args,**kwargs):
            self.assertNotIn(path,blocked);return old_open(path,*args,**kwargs)
        def stated(path,*args,**kwargs):
            self.assertNotIn(path,blocked);return old_stat(path,*args,**kwargs)
        with patch.object(Path,'open',opened),patch.object(Path,'stat',stated):self.build()

    def test_bad_external_receipt_pin_rejected(self):
        self.receipt_pin['sha256']='0'*64
        with self.assertRaises(ValueError):self.build()

    def test_changed_private_artifact_rejected(self):
        (self.private/'external-index.json').write_bytes(b'[]')
        with self.assertRaises(ValueError):self.build()

    def test_member_original_hash_rejected_even_container_resealed(self):
        self.rewrite_zip([('workspace/source.py',b'changed')])
        with self.assertRaises(ValueError):self.build()

    def test_malicious_zip_names(self):
        for name in ('../escape.py','/absolute.py','a/../b.py',r'a\b.py','C:/escape.py','a//b.py','./x.py'):
            with self.subTest(name=name):
                self.rewrite_zip([(name,b'x')])
                with self.assertRaises(ValueError):self.build()

    def test_duplicate_zip_members(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');self.rewrite_zip([('workspace/source.py',b'x'),('workspace/source.py',b'x')])
        with self.assertRaises(ValueError):self.build()

    def test_casefold_member_collision(self):
        self.rewrite_zip([('workspace/source.py',b'x'),('WORKSPACE/source.py',b'x')])
        with self.assertRaises(ValueError):self.build()

    def test_symlink_member_rejected(self):
        info=zipfile.ZipInfo('workspace/source.py');info.create_system=3;info.external_attr=0o120777<<16
        self.rewrite_zip([(info,b'elsewhere')])
        with self.assertRaises(ValueError):self.build()

    def test_undeclared_member_rejected(self):
        self.rewrite_zip([('workspace/source.py',self.source.read_bytes()),('extra.py',b'x')])
        with self.assertRaises(ValueError):self.build()

    def test_unsupported_zip_compression_rejected(self):
        p=self.private/'private-source.zip'
        with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_BZIP2) as z:z.writestr('workspace/source.py',self.source.read_bytes())
        self.repin(p.name)
        with self.assertRaises(ValueError):self.build()

    def test_encrypted_member_flag_rejected(self):
        self.rewrite_zip([('workspace/source.py',self.source.read_bytes())])
        p=self.private/'private-source.zip';raw=bytearray(p.read_bytes())
        local=raw.index(b'PK\x03\x04');central=raw.index(b'PK\x01\x02')
        raw[local+6]|=1;raw[central+8]|=1;p.write_bytes(raw);self.repin(p.name)
        with self.assertRaises(ValueError):self.build()

    def test_snapshot_artifact_symlink_rejected(self):
        p=self.private/'external-index.json';other=self.private/'external-original.json';p.rename(other);p.symlink_to(other)
        with self.assertRaises(ValueError):self.build()

    def test_size_limits_apply_before_content(self):
        for key in ('member_bytes','total_bytes','archive_bytes','files'):
            with self.subTest(key=key):
                limits=dict(share.DEFAULT_LIMITS,**{key:1})
                with self.assertRaises(ValueError):self.build(limits=limits)

    def test_missing_identifier_policy_fails_residual_scan(self):
        self.policy['identifiers']=[]
        with self.assertRaises(ValueError):self.build()

    def test_unlisted_home_path_fails(self):
        self.policy['path_prefixes']=self.policy['path_prefixes'][:1]
        with self.assertRaises(ValueError):self.build()

    def test_redacted_key_collision_rejected(self):
        redactor=share.Redactor(self.policy)
        with self.assertRaises(ValueError):redactor.value({'privateuser':1,'ACCOUNT_01':2})

    def test_hash_values_never_rewritten(self):
        policy=deepcopy(self.policy);policy['identifiers'].append(dict(private='aaaaaaaa',public='ID_03'))
        redactor=share.Redactor(policy)
        self.assertEqual(redactor.text('"'+'a'*64+'"'),'"'+'a'*64+'"')
        self.assertEqual(redactor.value({'sha256':'a'*64}),{'sha256':'a'*64})

    def test_duplicate_json_key_rejected(self):
        (self.private/'external-index.json').write_bytes(b'[{"declared_path":"x","declared_path":"y"}]')
        self.repin('external-index.json')
        with self.assertRaises(ValueError):self.build()

    def test_envelope_pin_not_rebound(self):
        self.build()
        with zipfile.ZipFile(self.output) as archive:
            manifest=json.loads(archive.read('manifest.json'))
            row=next(r for r in manifest['artifacts'] if r['category']=='envelope')
            entries=json.loads(archive.read(row['member']))
            self.assertEqual(entries[0]['sha256'],self.pin(self.source)['sha256'])

    def test_external_false_flags_required(self):
        path=self.private/'external-index.json';value=json.loads(path.read_bytes());value[0]['original_hash_verified']=True
        path.write_bytes(original.encode(value));self.repin(path.name)
        with self.assertRaises(ValueError):self.build()

    def test_internal_edge_pin_mismatch_rejected(self):
        p=self.private/'one-hop-edges.json';rows=json.loads(p.read_bytes())
        edge=next(row for row in rows if row['collection']=='explicit_scope');edge['sha256']='0'*64
        p.write_bytes(original.encode(rows));self.repin(p.name)
        with self.assertRaises(ValueError):self.build()

    def test_source_denominator_mismatch_rejected(self):
        p=self.private/'receipt.json';receipt=json.loads(p.read_bytes());receipt['source_references']+=1
        p.write_bytes(original.encode(receipt));self.receipt_pin=self.pin(p)
        with self.assertRaises(ValueError):self.build()

    def test_existing_output_never_overwritten(self):
        self.output.write_bytes(b'preserve')
        with self.assertRaises(ValueError):self.build()
        self.assertEqual(self.output.read_bytes(),b'preserve')

    def test_public_hash_tampering_and_wrong_external_archive_pin(self):
        result=self.build()
        with self.assertRaises(ValueError):share.verify(self.output,'0'*64)
        raw=self.output.read_bytes();self.output.write_bytes(raw+b'changed')
        with self.assertRaises(ValueError):share.verify(self.output,result['archive_sha256'])

    def test_public_manifest_execution_promotion_rejected(self):
        self.build()
        with zipfile.ZipFile(self.output) as z:files={n:z.read(n) for n in z.namelist()}
        m=json.loads(files['manifest.json']);m['execution_ready']=True;files['manifest.json']=original.encode(m)
        self.output.unlink()
        with zipfile.ZipFile(self.output,'w') as z:
            for n,raw in files.items():z.writestr(n,raw)
        with self.assertRaises(ValueError):share.verify(self.output,self.pin(self.output)['sha256'])

    def test_drive_detector_preserves_urls_scp_posix_path_lists_and_source_escapes(self):
        redactor=share.Redactor(self.policy)
        for text in ('http://example.org/a','https://example.org/a','other:/tmp/a',
                     'cluster:/path/file','/old/cluster_scripts:/core','/science:/native',
                     r'else:\n', 'seed=12345; p=0.001; https://example.org'):
            with self.subTest(text=text):self.assertEqual(redactor.text(text),text)

    def test_drive_detector_still_rejects_unmapped_absolute_windows_paths(self):
        redactor=share.Redactor(self.policy)
        for text in ('Z:/private/file',r'Z:\private\file','"C:/Users/unknown/file"'):
            with self.subTest(text=text),self.assertRaises(ValueError):redactor.check(text)

    def test_url_private_identifier_remains_separately_rejected(self):
        redactor=share.Redactor(self.policy)
        for text in ('https://private-host.example/path','https://example.org/privateuser'):
            with self.subTest(text=text),self.assertRaises(ValueError):redactor.check(text)


if __name__=='__main__':unittest.main()
