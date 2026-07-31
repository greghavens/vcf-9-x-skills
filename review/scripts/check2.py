#!/usr/bin/env python3
"""Phase-3 endpoint/version verification, v2 (noise-suppressed)."""
import json,os,re,glob,itertools
from collections import defaultdict

INV="/home/claude/vcf-skills/research/spec-inventory"; SKILLS="/home/claude/vcf-skills/skills"
TARGETS=["vcf-domains-clusters","vcf-installer-bringup","vcf-certificates-credentials",
 "nsx-segments-routing","nsx-network-services","vsphere-inventory-vm-lifecycle",
 "vsphere-content-tags-policies","vsphere-lifecycle-vlcm","vsan-storage",
 "vcf-operations-monitoring","vcf-operations-logs-and-networks","vcf-automation-vmapps",
 "vcf-automation-allapps-k8s","vks-supervisor","powercli-vcf"]
NOSPEC={"vcf-automation-vmapps","vcf-automation-allapps-k8s","vks-supervisor","powercli-vcf"}
NSX_SKILLS={"nsx-segments-routing","nsx-network-services"}
PREFIXES=["/policy/api/v1","/global-manager/api/v1","/suite-api/api","/suite-api","/api/ni",
          "/api/v2","/api/v1","/rest/api","/fleet-lcm","/sddc-lcm","/api","/v1"]
BASE_ONLY={ "/"+x.strip("/") for x in PREFIXES}|{"/policy","/api","/v1","/api/v1","/suite-api",
   "/policy/api/v1","/api/ni","/api/v2","/sdk/vim25","/global-manager/api/v1","/suite-api/api"}

SEG=re.compile(r"^(\{[^}]*\}|<[^>]*>|:[A-Za-z_].*|\.\.\.|\*|\$[A-Za-z_].*|[A-Za-z_]*\$[A-Za-z_{].*)$")
def structural(p):
    return "/"+"/".join("*" if SEG.match(s) else s for s in p.strip("/").split("/"))
def strip_pref(p):
    p=p.split("?")[0].split("#")[0]
    r={p}
    for pref in PREFIXES:
        if p.startswith(pref+"/"): r.add(p[len(pref):])
    m=re.match(r"^/sdk/vim25/[^/]+(/.*)$",p)
    if m: r.add(m.group(1))
    return r
def variants(p):
    return {structural(q) for q in strip_pref(p)}

def expand(p):
    """expand [/{x}] optional and {a,b} alternation notation into concrete candidates"""
    outs=[p]
    # {a,b} alternation  e.g. tier-{0,1}s ; nsx_policy_api.{json,yaml}
    while True:
        new=[]
        changed=False
        for s in outs:
            m=re.search(r"\{([^{}/]*,[^{}]*)\}",s)
            if m:
                changed=True
                for alt in m.group(1).split(","):
                    new.append(s[:m.start()]+alt.strip()+s[m.end():])
            else: new.append(s)
        outs=new
        if not changed: break
    # [/...] optional
    res=[]
    for s in outs:
        m=re.search(r"\[(/[^\]]*)\]",s)
        if m:
            res.append(s[:m.start()]+s[m.end():]); res.append(s[:m.start()]+m.group(1)+s[m.end():])
        else: res.append(s)
    return [r for r in res if r]

def load():
    prod={}
    for f in sorted(glob.glob(INV+"/*.ops.json")):
        ver,product=os.path.basename(f)[:-9].split("__",1)
        d=json.load(open(f)); e={"byid":{},"raw":d["operations"],"idx":defaultdict(list)}
        for o in d["operations"]:
            for np in variants(o["path"]): e["idx"][(o["method"].upper(),np)].append(o); e["idx"][("ANY",np)].append(o)
            if o.get("operationId"): e["byid"].setdefault(o["operationId"],o)
        prod[(ver,product)]=e
    return prod
PROD=load()
ALLIDS=set(); 
for e in PROD.values(): ALLIDS|=set(e["byid"])

def lookup(meth,p,vers):
    hits=[]
    cands=set()
    for cp in expand(p): cands|=variants(cp)
    for (ver,product),e in PROD.items():
        if ver not in vers: continue
        for c in cands:
            for o in e["idx"].get((meth,c),[]):
                hits.append((ver,product,o.get("operationId"),o["method"],o["path"]))
            if meth!="ANY":
                pass
    return hits


ALLPATHS=set()
for e in PROD.values():
    for o in e["raw"]:
        for np in variants(o["path"]): ALLPATHS.add(np)
def is_suffix(p):
    cands=set()
    for cp in expand(p): cands|=variants(cp)
    for c in cands:
        for ap in ALLPATHS:
            if ap.endswith(c) and ap!=c: return True
    return False
def is_prefix(p):
    cands=set()
    for cp in expand(p): cands|=variants(cp)
    for c in cands:
        c2=c.rstrip("/")
        for ap in ALLPATHS:
            if ap.startswith(c2+"/"): return True
    return False

METHODS=r"GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS"
RE_MP=re.compile(r"\b("+METHODS+r")\s+(/[A-Za-z0-9_\-\.\{\}<>:/\*\$~,%\[\]]{2,})")
RE_BARE=re.compile(r"`(/(?:v1|api|policy|global-manager|suite-api|sdk|rest|fleet-lcm|sddc-lcm)/[A-Za-z0-9_\-\.\{\}<>:/,\[\]]{2,})`")
RE_URL=re.compile(r"https?://[^\s`'\")\]]+")
TAG=re.compile(r"\[(SPEC[^\]]*|DOC-9\.[01][^\]]*|UNVERIFIED[^\]]*|INFERRED[^\]]*|9\.1-ONLY[^\]]*|ASYMMETRIC[^\]]*)\]",re.I)
SPECCONF=re.compile(r"spec[- ]confirmed|\[SPEC\b",re.I)

def vers_of(fp):
    if "/references/9.0/" in fp: return ["9.0"]
    if "/references/9.1/" in fp: return ["9.1"]
    return ["9.0","9.1"]

def junk(p):
    q=p.rstrip("/.,;:)`\"'")
    if q in BASE_ONLY: return True
    if "..." in q: return True
    if q.count("/")<2: return True
    if re.search(r"\.(json|yaml|html|zip|ova|iso)$",q) and "spec/openapi" in q: return True
    return False

rows=[];stats=defaultdict(lambda:defaultdict(int));opidrows=[]
for skill in TARGETS:
    for fp in sorted(glob.glob(SKILLS+"/"+skill+"/**/*.md",recursive=True)):
        rel=os.path.relpath(fp,SKILLS); V=vers_of(fp); lines=open(fp).read().split("\n")
        for i,l in enumerate(lines,1):
            claims=[]
            for m in RE_MP.finditer(l): claims.append((m.group(1).upper(),m.group(2)))
            for m in RE_BARE.finditer(l): claims.append(("ANY",m.group(1)))
            for m in RE_URL.finditer(l):
                mm=re.match(r"https?://[^/]+(/.+)$",m.group(0))
                if mm: claims.append(("ANY",mm.group(1)))
            for meth,p in claims:
                p=p.rstrip("/.,;:)`\"'|")
                if junk(p): continue
                stats[skill]["claims"]+=1
                tags=TAG.findall(l); spec=bool(SPECCONF.search(l))
                if skill in NOSPEC:
                    stats[skill]["nospec"]+=1
                    if spec: rows.append(dict(skill=skill,file=rel,line=i,meth=meth,path=p,ver=",".join(V),
                        verdict="SPEC-GRADED-BUT-NO-SPEC-EXISTS",ev="; ".join(tags),ctx=l.strip()[:200]))
                    continue
                if skill in NSX_SKILLS and V==["9.0"]:
                    stats[skill]["nsx90"]+=1
                    if spec: rows.append(dict(skill=skill,file=rel,line=i,meth=meth,path=p,ver="9.0",
                        verdict="NSX-9.0-SPEC-GRADED (no NSX spec at 9.0 tag)",ev="; ".join(tags),ctx=l.strip()[:200]))
                    # still check it exists in 9.1 nsx at all
                    h91=lookup(meth,p,{"9.1"})
                    if not h91:
                        rows.append(dict(skill=skill,file=rel,line=i,meth=meth,path=p,ver="9.0",
                          verdict="NOT-IN-ANY-SPEC (incl. 9.1 NSX)",ev="; ".join(tags),ctx=l.strip()[:200]))
                        stats[skill]["miss"]+=1
                    continue
                h=lookup(meth,p,set(V))
                if h: stats[skill]["ok"]+=1; continue
                other=lookup(meth,p,{"9.0","9.1"})
                if other:
                    stats[skill]["wrongver"]+=1
                    rows.append(dict(skill=skill,file=rel,line=i,meth=meth,path=p,ver=",".join(V),
                      verdict="WRONG-VERSION",ev="; ".join(tags),found=sorted({f"{x[0]}/{x[1]}" for x in other}),
                      foundpath=other[0][4],opid=other[0][2],ctx=l.strip()[:200]))
                else:
                    # try ignoring method
                    anym=lookup("ANY",p,set(V))
                    if anym:
                        stats[skill]["wrongmethod"]+=1
                        rows.append(dict(skill=skill,file=rel,line=i,meth=meth,path=p,ver=",".join(V),
                          verdict="WRONG-METHOD",ev="; ".join(tags),
                          found=sorted({f"{x[3]} {x[4]} ({x[2]})" for x in anym})[:4],ctx=l.strip()[:200]))
                    else:
                        pref=is_prefix(p); suf=is_suffix(p)
                        if (meth=="ANY" and pref) or (suf and p.count("/")<=3 and not p.startswith(("/v1","/api","/policy","/suite-api","/sdk"))):
                            stats[skill]["prefix"]+=1
                        else:
                            stats[skill]["miss"]+=1
                            rows.append(dict(skill=skill,file=rel,line=i,meth=meth,path=p,ver=",".join(V),verdict="NOT-FOUND",ev="; ".join(tags),prefix_of_real=pref,suffix_of_real=suf,ctx=l.strip()[:200]))
        # operationIds
        RE_OPID=re.compile(r"`([A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9_]*)+|[a-z][a-zA-Z0-9]{6,}|[A-Z][a-zA-Z0-9]{6,})`")
        for i,l in enumerate(lines,1):
            for m in RE_OPID.finditer(l):
                tok=m.group(1)
                if tok not in ALLIDS: continue
                stats[skill]["opid"]+=1
                if skill in NOSPEC: continue
                hv=[k for k,e in PROD.items() if k[0] in V and tok in e["byid"]]
                if not hv:
                    allv=[k for k,e in PROD.items() if tok in e["byid"]]
                    stats[skill]["opid_wrongver"]+=1
                    opidrows.append(dict(skill=skill,file=rel,line=i,opid=tok,ver=",".join(V),
                      verdict="OPID-WRONG-VERSION",found=[f"{a}/{b}" for a,b in allv],ctx=l.strip()[:180]))
json.dump(dict(rows=rows,opid=opidrows,stats={k:dict(v) for k,v in stats.items()}),open("/home/claude/vcf-skills/review/scripts/out2.json","w"),indent=1)
print(f"{'SKILL':34}{'claims':>7}{'ok':>6}{'MISS':>6}{'wmeth':>7}{'wver':>6}{'nsx9.0':>8}{'nospec':>7}{'opids':>7}{'opidWV':>7}")
for s in TARGETS:
    st=stats[s]
    print(f"{s:34}{st['claims']:>7}{st['ok']:>6}{st['miss']:>6}{st['wrongmethod']:>7}{st['wrongver']:>6}{st['nsx90']:>8}{st['nospec']:>7}{st['opid']:>7}{st['opid_wrongver']:>7}")
print("\nrows:",len(rows),"opidrows:",len(opidrows))
