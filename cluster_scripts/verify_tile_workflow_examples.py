"""Verify the four documented quick example outputs and archive their evidence.

Run from the repository root after the seed-7 quick commands documented in
docs/wp/data_tile_validation_2026-10-17/README.md.
"""
import hashlib
import json
from pathlib import Path
import tarfile

root=Path('output/tile_fixed_prior_example')
data=Path('docs/wp/data_tile_validation_2026-10-17')
reference=json.loads((data/'reference_summary.json').read_text())
rows=[]
for case,name in enumerate(('bit','bit288','depol72','depol288')):
    path=root/name
    summary=json.loads((path/'summary.json').read_text())
    bar=json.loads((path/'bar.json').read_text())
    decoders=[r['metadata']['decoder'] for r in bar['metadata']['rungs']]
    assert all(decoder==decoders[0] for decoder in decoders)
    desired=summary['sector_decoder_prior']
    children=[decoders[0]] if summary['noise']=='bit' else [decoders[0]['x_decoder'],decoders[0]['z_decoder']]
    assert all(d['settings']['error_rate']==desired for d in children)
    ref=next(r for r in reference['records'] if r['case']==case)
    interval=summary['bar_interval']
    overlap=interval is not None and interval[0]<=ref['interval_95'][1] and ref['interval_95'][0]<=interval[1]
    rows.append(dict(case=case,folder=name,summary=summary,all_rung_decoders_identical=True,
                     sector_priors_verified=True,reference_interval95=ref['interval_95'],
                     bar_reference_intervals_overlap=overlap,bar_seconds=bar['elapsed_seconds']))
archive=root/'quick_examples.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for name in ('bit','bit288','depol72','depol288'):
        for path in sorted((root/name).glob('*')):
            tar.add(path,arcname=path.relative_to(root).as_posix())
record=dict(seed=7,quick=True,records=rows,archive_path=str(archive),
            archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            example_source_sha256=hashlib.sha256(Path('examples/workflows/tile_capacity_fixed_prior.py').read_bytes()).hexdigest(),
            reference_summary_sha256=hashlib.sha256((data/'reference_summary.json').read_bytes()).hexdigest(),
            warning='Workflow execution checks only. Four examples do not calibrate bias or coverage.')
(data/'workflow_example_checks.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(cases=len(rows),all_fixed_prior=True,archive_sha256=record['archive_sha256'],
                     nonoverlap_cases=[r['case'] for r in rows if not r['bar_reference_intervals_overlap']])))
