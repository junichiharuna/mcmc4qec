"""Analysis archives retain all groups and bind every sampling input marker."""
import hashlib
import io
import itertools
import json
from pathlib import Path
import sys
import tarfile

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cluster_scripts'))
import tile_low_noise_archive as sampling
import tile_low_noise_analysis_archive as a


def raw(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def sha(value):return hashlib.sha256(value).hexdigest()


def fixture(tmp_path, *, omitted=None, corrupt=False, duplicate=False, extra=False):
    plan=dict(purpose='low_noise_production',case=2,target_index=1,replicates=2,
        kernels={'ZH':{},'ZHS':{}},initializations=['logical_basis','logical_combination'],
        stages={'analysis':153},condition=dict(chains=2,rungs=[.1,.003]))
    manifest=raw(plan)
    sample_index={'manifest.json':sha(manifest)}
    for stem in sampling.expected_sampling(plan,2,1):
        for ext in ('.json','.npz','.done.json'):sample_index[stem+ext]=sha((stem+ext).encode())
    context=dict(schema=1,purpose='low_noise_analysis',sampling_manifest=sha(manifest),replicates=2,seed_stage=153)
    expected=a.expected_analysis(plan,context,sample_index,2,1,sha(manifest))
    data={'manifest.json':manifest,'analysis_manifest.json':raw(context),'sampling-input-sha256.json':raw(sample_index)}
    for i,(stem,identity) in enumerate(expected.items()):
        payloads={'.npz':b'ACF payload','.json':raw({'status':'failed' if i==0 else 'ok','group':identity['group']})}
        data.update({stem+ext:value for ext,value in payloads.items()})
        data[stem+'.done.json']=raw(dict(identity=identity,sha256={ext:sha(value) for ext,value in payloads.items()}))
    index={name:sha(value) for name,value in data.items()}
    if omitted:del data[omitted]
    if corrupt:data['analysis/2-1-0-0-0.npz']=b'changed'
    if extra:data['extra.json']=b'{}'
    archive=tmp_path/'analysis.tar.gz'
    with tarfile.open(archive,'w:gz') as stream:
        entries=list(data.items())+([('manifest.json',manifest)] if duplicate else [])
        for name,value in entries:
            info=tarfile.TarInfo(name);info.size=len(value);stream.addfile(info,io.BytesIO(value))
    args=dict(archive=archive,archive_sha256=sha(archive.read_bytes()),case=2,target_index=1)
    for key,value in [('manifest',manifest),('analysis_manifest',raw(context)),('sampling_index',raw(sample_index)),('file_index',raw(index))]:
        path=tmp_path/(key+'.json');path.write_bytes(value)
        args[key]=path;args[key+'_sha256']=sha(value)
    return args


def test_complete_archive_and_failed_group_preserved(tmp_path):
    result=a.verify(**fixture(tmp_path))
    assert result['groups']==8 and result['files']==27
    assert result['sampling_payloads_rehashed'] is False
    assert result['numerical_reanalysis'] is False


def test_exact_group_input_census(tmp_path):
    args=fixture(tmp_path)
    plan=json.loads(args['manifest'].read_bytes());context=json.loads(args['analysis_manifest'].read_bytes())
    index=json.loads(args['sampling_index'].read_bytes())
    expected=a.expected_analysis(plan,context,index,2,1,args['manifest_sha256'])
    assert len(expected)==8
    for k,i,rep in itertools.product(range(2),range(2),range(2)):
        group=[2,1,k,i,rep]
        identity=expected['analysis/'+'-'.join(map(str,group))]
        wanted={f'sample/2-1-{k}-{i}-{rep}-{r}-{c}':index[f'traces/2-1-{k}-{i}-{rep}-{r}-{c}.done.json'] for r,c in itertools.product(range(2),range(2))}
        wanted[f'anchors/2-1-0-0-{rep}-0-0']=index[f'anchors/2-1-0-0-{rep}-0-0.done.json']
        assert identity==dict(analysis=sha(raw(context)),group=group,input_artifact_markers=wanted)


@pytest.mark.parametrize('option',['omitted','corrupt','duplicate','extra'])
def test_bad_archive_rejected(tmp_path,option):
    args=fixture(tmp_path,**{option:'analysis/2-1-1-1-1.done.json' if option=='omitted' else True})
    with pytest.raises(ValueError):a.verify(**args)


@pytest.mark.parametrize('key',['manifest','analysis_manifest','sampling_index','file_index','archive'])
def test_all_external_hashes_are_required(tmp_path,key):
    args=fixture(tmp_path);args[key+'_sha256']='0'*64
    with pytest.raises(ValueError):a.verify(**args)


@pytest.mark.parametrize('key,value',[('case',0),('target_index',0)])
def test_different_condition_rejected(tmp_path,key,value):
    args=fixture(tmp_path);args[key]=value
    with pytest.raises(ValueError):a.verify(**args)


@pytest.mark.parametrize('mode',['missing','extra','different_marker'])
def test_sampling_index_census_and_marker_links_are_external(tmp_path,mode):
    args=fixture(tmp_path);index=json.loads(args['sampling_index'].read_bytes())
    if mode=='missing':del index['traces/2-1-0-0-0-0-0.done.json']
    elif mode=='extra':index['traces/2-1-0-0-0-9-9.done.json']='0'*64
    else:index['traces/2-1-0-0-0-0-0.done.json']='0'*64
    args['sampling_index'].write_bytes(raw(index));args['sampling_index_sha256']=sha(raw(index))
    with pytest.raises(ValueError):a.verify(**args)


@pytest.mark.parametrize('key,value',[('sampling_manifest','0'*64),('purpose','capacity'),('seed_stage',155)])
def test_context_bound_to_production(tmp_path,key,value):
    args=fixture(tmp_path);context=json.loads(args['analysis_manifest'].read_bytes());context[key]=value
    args['analysis_manifest'].write_bytes(raw(context));args['analysis_manifest_sha256']=sha(raw(context))
    with pytest.raises(ValueError):a.verify(**args)


@pytest.mark.parametrize('key',['archive','manifest','analysis_manifest','sampling_index','file_index'])
def test_changed_input_during_stream_rejected(tmp_path,monkeypatch,key):
    args=fixture(tmp_path);original=sampling.archive_check.verify
    def mutate(*positional):
        result=original(*positional);args[key].write_bytes(args[key].read_bytes()+b' ');return result
    monkeypatch.setattr(sampling.archive_check,'verify',mutate)
    with pytest.raises(ValueError,match='changed'):a.verify(**args)


def test_group_census_matches_actual_analysis_driver(tmp_path):
    pytest.importorskip('ldpc')
    import tile_low_noise_analysis as driver
    args=fixture(tmp_path);plan=json.loads(args['manifest'].read_bytes())
    expected=a.expected_analysis(plan,json.loads(args['analysis_manifest'].read_bytes()),
        json.loads(args['sampling_index'].read_bytes()),2,1,args['manifest_sha256'])
    assert {tuple(row['group']) for row in expected.values()}==set(driver.groups(plan))


def test_cli_retains_existing_verification(tmp_path,monkeypatch):
    args=fixture(tmp_path);output=tmp_path/'verification.json'
    argv=['analysis_archive.py','--output',str(output)]
    for key,value in args.items():argv+=['--'+key.replace('_','-'),str(value)]
    monkeypatch.setattr(sys,'argv',argv);a.main();saved=output.read_bytes()
    with pytest.raises(ValueError,match='existing'):a.main()
    assert output.read_bytes()==saved


def source_fixture(tmp_path):
    args=fixture(tmp_path);root=tmp_path/'source';root.mkdir()
    with tarfile.open(args['archive'],'r:gz') as stream:
        for member in stream:
            if member.name=='sampling-input-sha256.json':continue
            target=root/member.name;target.parent.mkdir(exist_ok=True)
            target.write_bytes(stream.extractfile(member).read())
    return dict(root=root,output=tmp_path/'export',case=2,target_index=1,
        **{key:args[key] for key in ('manifest_sha256','analysis_manifest_sha256','sampling_index',
                                    'sampling_index_sha256','file_index','file_index_sha256')})


def test_export_requires_pbs_and_new_output(tmp_path,monkeypatch):
    args=source_fixture(tmp_path);monkeypatch.delenv('PBS_JOBID',raising=False)
    with pytest.raises(ValueError,match='PBS'):a.export_analysis(**args)
    monkeypatch.setenv('PBS_JOBID','123.test');args['output'].mkdir()
    with pytest.raises(ValueError,match='fresh'):a.export_analysis(**args)


def test_export_roundtrip_uses_accepted_index(tmp_path,monkeypatch):
    args=source_fixture(tmp_path);monkeypatch.setenv('PBS_JOBID','123.test')
    value=a.export_analysis(**args)
    assert value['verification']['groups']==8 and value['verification']['files']==27
    assert value['pbs_terminal_verified'] is False
    assert value['accepted_file_index_sha256']==args['file_index_sha256']
    assert json.loads((args['output']/'export.json').read_bytes())==value
    with pytest.raises(ValueError):a.export_analysis(**args)


@pytest.mark.parametrize('mode',['missing','extra','corrupt'])
def test_export_rejects_wrong_source(tmp_path,monkeypatch,mode):
    args=source_fixture(tmp_path);monkeypatch.setenv('PBS_JOBID','123.test')
    path=args['root']/'analysis/2-1-0-0-0.npz'
    if mode=='missing':path.unlink()
    elif mode=='extra':(args['root']/'analysis/extra.npz').write_bytes(b'extra')
    else:path.write_bytes(b'corrupt')
    with pytest.raises(ValueError):a.export_analysis(**args)
    assert not (args['output']/'export.json').exists()


def test_export_cannot_substitute_new_self_consistent_payloads(tmp_path,monkeypatch):
    args=source_fixture(tmp_path);monkeypatch.setenv('PBS_JOBID','123.test')
    stem=args['root']/'analysis/2-1-0-0-0'
    stem.with_suffix('.npz').write_bytes(b'new')
    marker=json.loads(stem.with_suffix('.done.json').read_bytes());marker['sha256']['.npz']=sha(b'new')
    stem.with_suffix('.done.json').write_bytes(raw(marker))
    with pytest.raises(ValueError):a.export_analysis(**args)
    assert not (args['output']/'export.json').exists()


@pytest.mark.parametrize('mode',['payload','new_file','worker'])
def test_export_changes_during_compression_rejected(tmp_path,monkeypatch,mode):
    args=source_fixture(tmp_path);monkeypatch.setenv('PBS_JOBID','123.test')
    worker=tmp_path/'worker.py';worker.write_bytes(Path(a.__file__).read_bytes());monkeypatch.setattr(a,'__file__',str(worker))
    original=tarfile.TarFile.add;changed=False
    def mutate(self,name,*positional,**keywords):
        nonlocal changed
        result=original(self,name,*positional,**keywords)
        if not changed:
            changed=True
            path=worker if mode=='worker' else args['root']/('analysis/extra.npz' if mode=='new_file' else 'analysis/2-1-0-0-0.npz')
            path.write_bytes(b'changed')
        return result
    monkeypatch.setattr(tarfile.TarFile,'add',mutate)
    with pytest.raises(ValueError):a.export_analysis(**args)
    assert changed and not (args['output']/'export.json').exists()


def test_export_changes_during_final_verification_rejected(tmp_path,monkeypatch):
    args=source_fixture(tmp_path);monkeypatch.setenv('PBS_JOBID','123.test')
    original=a.verify
    def mutate(**kwargs):
        result=original(**kwargs);(args['root']/'analysis/2-1-0-0-0.npz').write_bytes(b'changed');return result
    monkeypatch.setattr(a,'verify',mutate)
    with pytest.raises(ValueError):a.export_analysis(**args)
    assert not (args['output']/'export.json').exists()
