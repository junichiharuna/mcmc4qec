"""Eight PBS fixtures for a bounded delta over an unchanged historical baseline."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import collect


def pin(path):return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


class DeltaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        self.new=self.root/'new';self.new.mkdir();self.old=self.root/'old';self.old.mkdir()
        self.base=collect.module('fixture_delta_base',pin(Path(os.environ['DELTA_SCOPE_SOURCE'])))
        self.lib=collect.module('fixture_delta_lib',pin(Path(os.environ['DELTA_SNAPSHOT_LIBRARY'])))
        self.inventory=dict(roots={'workspace':str(self.root)},source_prefixes=[str(self.new)],explicit_sources=[],external=[],
            limits=dict(file_bytes=collect.MAX,total_bytes=16*1024**2))
        self.scope=collect.delta_scope(self.base,self.lib,self.inventory)

    def test_old_source_declaration_remains_external(self):
        self.scope.source(dict(path=str(self.old/'unread.py'),sha256='a'*64),'old')
        self.assertEqual(self.scope.sources,{})

    def test_new_source_declaration_included(self):
        p=self.new/'x.py';self.scope.source(dict(path=str(p),sha256='a'*64),'new')
        self.assertEqual(self.scope.sources[str(p)]['sha256'],'a'*64)

    def test_relative_source_uses_explicit_document_base(self):
        p=self.root/'sources.json';p.write_text(json.dumps({'x.py':'a'*64}))
        self.scope.document(dict(pin(p),relative_base=str(self.new)),'fixture')
        self.assertIn(str(self.new/'x.py'),self.scope.sources)
        self.assertEqual(self.scope.metadata[str(p)]['relative_base'],str(self.new))

    def test_unbound_relative_source_not_guessed(self):
        self.scope.source(dict(path='x.py',sha256='a'*64),'unresolved')
        self.assertEqual(self.scope.sources,{})

    def test_original_hash_mutation_and_large_metadata_rejected(self):
        p=self.root/'meta.json';p.write_bytes(b'{}');fixed=pin(p);p.write_bytes(b'[]')
        with self.assertRaises(ValueError):collect.raw(fixed)
        p.write_bytes(b'x'*(collect.MAX+1))
        with self.assertRaises(ValueError):collect.pin(p)

    def test_nested_relative_fixture_source(self):
        p=self.root/'sources.json';p.write_text(json.dumps({'output/merge/contract.py':'b'*64}))
        self.scope.document(dict(pin(p),relative_base=str(self.new)),'fixture')
        self.assertEqual(self.scope.sources[str(self.new/'output/merge/contract.py')]['sha256'],'b'*64)

    def test_document_reregistration_keeps_existing_base(self):
        p=self.root/'sources.json';p.write_text(json.dumps({'x.py':'a'*64}));fixed=pin(p)
        self.scope.document(dict(fixed,relative_base=str(self.new)),'fixture')
        self.scope.document(fixed,'again')
        self.assertEqual(self.scope.metadata[str(p)]['relative_base'],str(self.new))
        with self.assertRaises(ValueError):self.scope.document(dict(fixed,relative_base=str(self.old)),'changed')

    def test_both_alias_source_maps_require_correct_absolute_expansion(self):
        records=[]
        for name in ('parent-alias-merge-tests-v1','worker-alias-merge-tests-v1'):
            stage=self.new/name;stage.mkdir();base=stage/'test-root';base.mkdir()
            path=stage/'sources.json';path.write_text(json.dumps({'output/merge/contract.py':'b'*64}))
            row=dict(pin(path),relative_base=str(base));self.scope.document(row,'actual-map');records.append(row)
        verified=collect.verify_relative_maps(self.scope,dict(metadata=records));self.assertEqual(len(verified),2)
        del self.scope.sources[str(self.new/'parent-alias-merge-tests-v1/test-root/output/merge/contract.py')]
        with self.assertRaises(ValueError):collect.verify_relative_maps(self.scope,dict(metadata=records))


if __name__=='__main__':unittest.main()
