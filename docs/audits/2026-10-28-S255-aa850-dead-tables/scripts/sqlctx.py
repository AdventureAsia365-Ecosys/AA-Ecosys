import json,re,subprocess
ROOT='/home/nghiep/projects/AA-Ecosys/'
REPO={'CIS':'apps/AA-CIS-App','Booking':'apps/AA-Booking','TripPlanner':'apps/AA-TripPlanner-Web','Partner':'apps/AA-Partner','Infra':'infra/AA-CIS-Infra'}
CAT={'services/erasure/inventory.py','services/erasure/plan.py','api/services/data_coverage/queries.py','api/services/data_coverage/registry.py','db/rls_catalogue_rules.py','db/isolation_probe.py','db/owners.yaml','db/schema_drift_decisions.json'}
o=json.load(open('scan.json'))
cache={}
def lines(repo,path):
    k=(repo,path)
    if k not in cache:
        cache[k]=subprocess.run(['git','-C',ROOT+REPO[repo],'show',f'origin/main:{path}'],capture_output=True,text=True,errors='replace').stdout.splitlines()
    return cache[k]
res={}
for fq,x in o.items():
    pat=re.compile(r'(from|join|into|update|delete\s+from|table|on|exists|regclass|copy|truncate)\s+"?'+re.escape(fq)+r'\b',re.I)
    pat2=re.compile(r'["\'`][^"\'`]*\b'+re.escape(fq)+r'\b')
    sql=[];other=[]
    for k,v in x['hits']['qualified'].items():
        repo,cat=k.split(':')
        if cat not in('runtime','script','infra-tool','frozen'): continue
        for p in v:
            if p in CAT: continue
            for i,l in enumerate(lines(repo,p)):
                if fq not in l.lower(): continue
                s=l.strip()
                if s.startswith(('#','--','//','*')): other.append(f'{repo}:{p}:{i+1}'); continue
                if pat.search(l) or pat2.search(l): sql.append(f'{repo}:{p}:{i+1}')
                else: other.append(f'{repo}:{p}:{i+1}')
    res[fq]={'sql':sql,'other':other}
json.dump(res,open('sqlctx.json','w'),indent=1)
for fq in sorted(res):
    if not res[fq]['sql'] and (res[fq]['other']):
        print(fq, o[fq]['kind'], res[fq]['other'][:4])
