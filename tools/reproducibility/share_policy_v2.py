"""Propose a fixed literal redaction policy from already-collected text only."""
import re


def derive_policy(documents,source_texts):
    prefixes=set();accounts=set();hosts=set();texts=[]
    token=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{2,}\Z')
    def host(value):
        if isinstance(value,str) and token.fullmatch(value) and not re.fullmatch('[0-9a-f]{64}',value):hosts.add(value)
    def walk(value,key=''):
        if isinstance(value,dict):
            for k,v in value.items():
                texts.append(k)
                if re.fullmatch(r'\d+\.[A-Za-z0-9_.-]+',k):host(k.split('.',1)[1])
                walk(v,k)
        elif isinstance(value,list):
            for item in value:walk(item,key)
        elif isinstance(value,str):
            texts.append(value);lower=key.lower()
            if lower in ('hostname','host','server','submit_host','submission_host','pbs_o_host'):host(value)
            if lower in ('job_owner','owner') and '@' in value:
                account,machine=value.split('@',1)
                if token.fullmatch(account):accounts.add(account)
                host(machine)
            if lower=='exec_host':
                for piece in value.split('+'):host(piece.split('/')[0])
            if lower=='exec_vnode':
                for machine in re.findall(r'\(([^():]+):',value):host(machine)
            if lower in ('job_id','pbs_job_id') and re.fullmatch(r'\d+\.[A-Za-z0-9_.-]+',value):host(value.split('.',1)[1])
    for document in documents:walk(document)
    host_prefixes={match.group(0) for value in hosts
                   if (match:=re.match(r'[A-Za-z]{4,}',value)) and re.search(r'[0-9]',value)}
    texts.extend(source_texts)
    for text in texts:
        for match in re.finditer(r'/(?:home|Users)/([^/\s"\'\\]+)',text):
            prefixes.add(match.group(0))
            if token.fullmatch(match.group(1)):accounts.add(match.group(1))
        normalized=text
        for _ in range(3):normalized=normalized.replace('\\\\','\\')
        for drive in re.findall(r'(?<![A-Za-z0-9_])([A-Za-z]):[\\/]',normalized):
            prefixes.add(drive.upper()+':\\')
            prefixes.add(drive.lower()+':\\')
        for account in re.findall(r'[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]([^\\/\s"\']+)',normalized,re.IGNORECASE):
            if token.fullmatch(account):accounts.add(account)
        # Site-specific prefixes come from collected hostname fields, never code constants.
        for prefix in sorted(host_prefixes):
            for machine in re.findall(r'\b'+re.escape(prefix)+r'[A-Za-z0-9_.-]*',text):host(machine)
        for address in re.findall(r'(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])',text):
            if all(int(part)<=255 for part in address.split('.')):host(address)
    ordered_paths=sorted(prefixes)
    # Equal case-folded identifiers need only one case-insensitive literal rule.
    identifiers={}
    for category,values in [('ACCOUNT',accounts),('NODE',hosts)]:
        for value in sorted(values):identifiers.setdefault(value.casefold(),(value,category))
    return dict(schema=1,
        path_prefixes=[dict(private=value,public='${LOCATION_'+str(i).zfill(4)+'}') for i,value in enumerate(ordered_paths)],
        identifiers=[dict(private=value,public=category+'_'+str(i).zfill(4))
                     for i,(value,category) in enumerate(identifiers.values())],
        forbidden_patterns=[r'\b'+re.escape(prefix)+r'[A-Za-z0-9_.-]*' for prefix in sorted(host_prefixes)])
