#!/usr/bin/env python3
"""Verify (METHOD-list, path, operationId-list) triples cited on the same line.
Handles the docs' convention: `GET|POST /path` (`idA` / `idB`) and
`| GET.PATCH.PUT | /path | idA, idB, idC |` -> zip verbs to ids positionally.
A cited path may be RELATIVE to a section base, so an opId matches if its spec
path equals the cited path after prefix-stripping OR ends with it."""
import json,re,glob,os
exec(open('/home/claude/vcf-skills/review/scripts/check2.py').read().split('METHODS=r"GET|POST')[0])
SKILLS="/home/claude/vcf-skills/skills"
TARGETS=["vcf-domains-clusters","vcf-installer-bringup","vcf-certificates-credentials",
 "nsx-segments-routing","nsx-network-services","vsphere-inventory-vm-lifecycle",
 "vsphere-content-tags-policies","vsphere-lifecycle-vlcm","vsan-storage",
 "vcf-operations-monitoring","vcf-operations-logs-and-networks"]
ALLIDS={}
for k,e in PROD.items():
    for oid,o in e["byid"].items(): ALLIDS.setdefault(oid,[]).append((k[0],k[1],o["method"],o["path"]))
V_RE=r"(?:GET|POST|PUT|PATCH|DELETE|HEAD)"
# form A:  `GET|POST /path` (`id1` / `id2`)   or  `GET·PUT /path` (`id`)
A=re.compile(r"`((?:"+V_RE+r")(?:\s*[|·,]\s*(?:"+V_RE+r"))*)\s+(/[^`]+)`\s*\(?\s*((?:`[A-Za-z][A-Za-z0-9_$\.]+`(?:\s*[/,]\s*)?)+)")
# form B (table): | GET·POST | `/path` | `id1`, `id2` |
B=re.compile(r"^\|\s*`?((?:"+V_RE+r")(?:\s*[|·,]\s*(?:"+V_RE+r"))*)`?\s*\|\s*`([^`]+)`[^|]*\|\s*((?:`[A-Za-z][A-Za-z0-9_$\.]+`[,/\s]*)+)")
# form C (table, verbs inside the path cell): | `GET·POST /path` | `id1`, `id2` |
C=re.compile(r"^\|\s*`((?:"+V_RE+r")(?:\s*[|·,]\s*(?:"+V_RE+r"))*)\s+(/[^`]+)`\s*\|\s*((?:`[A-Za-z][A-Za-z0-9_$\.]+`[,/\s]*)+)")

def matches(oid,meth,path):
    if oid not in ALLIDS: return None
    path=re.sub(r"^\s*(?:\u2026|\.\.\.)","",path.strip())
    if not path.startswith("/"): path="/"+path.lstrip("/")
    cands={c for cp in expand(path.strip()) for c in variants(cp)}
    hits=[]
    for v,pr,m2,p2 in ALLIDS[oid]:
        if m2.upper()!=meth.upper(): continue
        for np in variants(p2):
            if np in cands or any(np.endswith(c) for c in cands): hits.append((v,pr,m2,p2)); break
    return hits or False

n=0;bad=[];skipped=0
for skill in TARGETS:
    for fp in sorted(glob.glob(SKILLS+"/"+skill+"/**/*.md",recursive=True)):
        rel=os.path.relpath(fp,SKILLS)
        V={"9.0"} if "/9.0/" in fp else ({"9.1"} if "/9.1/" in fp else {"9.0","9.1"})
        for i,l in enumerate(open(fp).read().split("\n"),1):
            got=[]
            for rx in (C,B,A):
                for m in rx.finditer(l):
                    verbs=[v.strip() for v in re.split(r"[|·,]",m.group(1)) if v.strip()]
                    path=m.group(2).strip()
                    ids=re.findall(r"`([A-Za-z][A-Za-z0-9_$\.]+)`",m.group(3))
                    ids=[x for x in ids if x in ALLIDS]
                    got.append((verbs,path,ids))
                if got: break
            for verbs,path,ids in got:
                if not ids: continue
                if len(verbs)!=len(ids):
                    if len(ids)==1 and len(verbs)>1: pairs=[(verbs[0],ids[0])]
                    else: skipped+=1; continue
                else: pairs=list(zip(verbs,ids))
                for meth,oid in pairs:
                    n+=1
                    r=matches(oid,meth,path)
                    if r and any(h[0] in V for h in r): continue
                    if r: bad.append(dict(skill=skill,file=rel,line=i,meth=meth,path=path,opid=oid,kind="WRONG-VERSION",spec=[f"{a}/{b} {c} {d}" for a,b,c,d in ALLIDS[oid]][:3],ctx=l.strip()[:170]))
                    else: bad.append(dict(skill=skill,file=rel,line=i,meth=meth,path=path,opid=oid,kind="MISMATCH",spec=[f"{a}/{b} {c} {d}" for a,b,c,d in ALLIDS[oid]][:3],ctx=l.strip()[:170]))
print("triples checked:",n," ambiguous-skipped:",skipped," suspect:",len(bad))
json.dump(bad,open('/home/claude/vcf-skills/review/scripts/pairs.json','w'),indent=1)
for b in bad:
    print(f"{b['kind'][:4]} {b['skill'][:20]:21}{b['file'].split('/')[-2][:7]:8}L{b['line']:<5}{b['meth']:6}{b['path'][:40]:42}{b['opid'][:34]:36}spec={b['spec']}")
