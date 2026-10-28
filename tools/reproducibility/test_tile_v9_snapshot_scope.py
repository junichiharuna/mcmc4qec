"""Small scope-builder fixtures, run in PBS before any actual collection."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import collect


def load_library():
    path=os.environ['SNAPSHOT_FIXTURE_LIBRARY']
    spec=importlib.util.spec_from_file_location('scope_fixture_library',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        self.lib=load_library()
        self.base=dict(schema=2,roots=dict(workspace=str(self.root)),sources=[],metadata=[],external=[],bindings=[],envelope=[],
            expected_source_count=0,expected_envelope_count=0,limits=dict(file_bytes=collect.MAX,total_bytes=32*1024**2),final_proofs_complete=False)
        self.scope=collect.Scope(self.base,self.lib)

    def save(self,name,value):
        p=self.root/name;p.write_bytes(value if isinstance(value,bytes) else json.dumps(value).encode());return collect.pin(p)

    def test_baseline_immutable_and_old_metadata_role(self):
        p=self.save('old.json',{});self.base['metadata']=[dict(p,category='old',relative_base=None)]
        before=deepcopy(self.base);scope=collect.Scope(self.base,self.lib)
        self.assertEqual(scope.metadata[p['path']]['category'],'historical_v8:old');self.assertEqual(self.base,before)

    def test_conflicting_source_pin_rejected(self):
        p=self.save('a.py',b'x=1\n');self.scope.source(p,'one')
        with self.assertRaises(ValueError):self.scope.source(dict(p,sha256='a'*64),'two')

    def test_metadata_pin_and_mutable_name_rejected(self):
        p=self.save('data.json',{})
        with self.assertRaises(ValueError):self.scope.document(dict(p,sha256='a'*64),'changed')
        p=self.save('state-latest.json',{})
        with self.assertRaises(ValueError):self.scope.document(p,'mutable')

    def test_json_external_reference_not_followed(self):
        target=self.root/'not-opened.json';p=self.save('metadata.json',dict(raw=dict(path=str(target),sha256='a'*64)))
        self.scope.document(p,'explicit');self.assertNotIn(str(target),self.scope.metadata)

    def test_source_alias_declaration_preserved(self):
        p=self.save('a.py',b'pass\n');alias=str(self.root/'alias.py')
        value=dict(sources={alias:p['sha256']},resolved_sources={alias:p['path']})
        self.scope.source_edges(value,'declared')
        self.assertEqual(self.scope.sources[alias]['resolved_path'],p['path'])

    def test_raw_suffix_and_oversize_rejected(self):
        with self.assertRaises(ValueError):collect.bounded(self.root/'unread.bin')
        p=self.root/'big.json';p.write_bytes(b' '*(collect.MAX+1))
        with self.assertRaises(ValueError):collect.bounded(p)

    def test_snapshot_external_content_never_opened(self):
        native=self.root/'native.bin';native.write_bytes(b'fixture external bytes')
        source=self.save('source.py',b'pass\n');self.scope.source(source,'explicit')
        self.scope.external[str(native)]=dict(path=str(native),sha256='a'*64,category='native',reason='unread')
        real_open=Path.open
        def guarded(path,*args,**kwargs):
            if path==native:raise AssertionError('External content opened')
            return real_open(path,*args,**kwargs)
        with patch.object(Path,'open',guarded):receipt=self.lib.snapshot(self.scope.request(),self.root/'snapshot')
        self.assertFalse(receipt['scientific_reproduction_verified']);self.assertEqual(receipt['source_references'],1)

    def test_repeated_source_reasons_compact_but_roles_preserved(self):
        p=self.save('source.py',b'pass\n')
        for i in range(1000):self.scope.source(p,'document_role/sources/'+str(i))
        self.scope.source(p,'another_document/sources/0')
        self.assertEqual(len(self.scope.reasons),2);self.assertEqual(len(self.scope.sources),1)
        self.assertEqual({r['role'] for r in self.scope.reasons.values()},{'document_role','another_document'})

    def test_pbs_wrapper_bounded_read(self):
        spec=importlib.util.spec_from_file_location('snapshot_run_fixture',Path(__file__).with_name('run.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        p=self.root/'big.py';p.write_bytes(b'x'*(collect.MAX+1))
        with self.assertRaises(ValueError):module.bounded(p)


if __name__=='__main__':unittest.main()
