"""PBS-only bounded residual classification from preserved source ZIP bytes."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

assert os.environ.get('PBS_JOBID')
request=json.loads(Path(sys.argv[1]).read_bytes())
assert hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()==sys.argv[2]
def raw(pin):
    value=Path(pin['path']).read_bytes();assert hashlib.sha256(value).hexdigest()==pin['sha256'];return value
e=request['exporter'];source=raw(e);spec=importlib.util.spec_from_file_location('residual_exporter',e['path'])
module=importlib.util.module_from_spec(spec);exec(compile(source,e['path'],'exec'),module.__dict__)
policy=json.loads(raw(request['policy']));receipt=json.loads(raw(request['receipt']))
p=Path(request['receipt']['path']).parent/'private-source.zip';record=receipt['artifacts'][p.name]
contents=module.zip_members(module.file_bytes(p,module.DEFAULT_LIMITS['archive_bytes'],record['sha256'],record['bytes']),module.DEFAULT_LIMITS)
redactor=module.Redactor(policy);counts={};examples=[]
for index,(name,content) in enumerate(contents.items()):
    text=redactor._replace(content.decode('utf8'))
    for number,pattern in enumerate(redactor.patterns):
        for match in pattern.finditer(text):
            key=str(number);counts[key]=counts.get(key,0)+1
            if sum(x['pattern_index']==number for x in examples)<12:
                examples.append(dict(source_index=index,pattern_index=number,pattern=pattern.pattern,
                    match=match.group(0),context=text[max(0,match.start()-30):match.end()+50]))
result=dict(pbs_job_id=os.environ['PBS_JOBID'],counts=counts,examples=examples,
            private_policy_source=request['policy'],external_paths_followed=False,original_sources_modified=False)
Path(sys.argv[1]).with_name('diagnostic.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
