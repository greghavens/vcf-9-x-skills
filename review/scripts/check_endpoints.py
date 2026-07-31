#!/usr/bin/env python3
"""
Phase-3 adversarial check: hallucinated endpoints & wrong-version claims.

Ground truth: /home/claude/vcf-skills/research/spec-inventory/*.ops.json
  each = {meta:{...}, operations:[{method,path,operationId,deprecated,...}]}
  extracted from git tags 9.0.0.0 / 9.1.0.0 of github.com/vmware/vcf-api-specs

Method
------
1. For each skill reference file, record the *version context* from its path
   (references/9.0/ -> "9.0", references/9.1/ -> "9.1", references/*.md -> "both").
2. Extract two claim classes:
     a) PATH claims: `METHOD /path` appearing in prose/backticks/code.
     b) OPERATIONID claims: backticked CamelCase / dotted tokens that look like
        operationIds.
3. Normalise the path by stripping every known product base-path prefix, then
   look it up in every product inventory for the applicable version(s).
   A claim is a MISS only if it resolves in NO product at that version.
4. Path templates are matched structurally: `{anything}` and `<anything>` and
   concrete-looking ids are collapsed to a `*` segment so
   `/v1/domains/{domain-id}` == `/v1/domains/{id}`.
"""
import json, os, re, sys, glob
from collections import defaultdict

INV = "/home/claude/vcf-skills/research/spec-inventory"
SKILLS = "/home/claude/vcf-skills/skills"

TARGETS = ["vcf-domains-clusters","vcf-installer-bringup","vcf-certificates-credentials",
 "nsx-segments-routing","nsx-network-services","vsphere-inventory-vm-lifecycle",
 "vsphere-content-tags-policies","vsphere-lifecycle-vlcm","vsan-storage",
 "vcf-operations-monitoring","vcf-operations-logs-and-networks","vcf-automation-vmapps",
 "vcf-automation-allapps-k8s","vks-supervisor","powercli-vcf"]

# products with NO spec at all -> evidence-tag check instead
NOSPEC_SKILLS = {"vcf-automation-vmapps","vcf-automation-allapps-k8s","vks-supervisor","powercli-vcf"}

# base-path prefixes to strip before comparison (longest first)
PREFIXES = ["/policy/api/v1","/global-manager/api/v1","/suite-api/api","/suite-api",
            "/api/ni","/api/v2","/api/v1","/rest/api","/sdk/vim25","/fleet-lcm","/sddc-lcm",
            "/api","/v1"]

# ---------------------------------------------------------------- ground truth
def load():
    prod = {}   # (ver, product) -> {"ops":set((m,normpath)), "byid":{opid:(m,path)}, "raw":[...]}
    for f in sorted(glob.glob(os.path.join(INV,"*.ops.json"))):
        base = os.path.basename(f)[:-len(".ops.json")]
        ver, product = base.split("__",1)
        d = json.load(open(f))
        ops = d.get("operations",[])
        e = {"ops":set(),"byid":{},"paths":set(),"raw":ops,"meta":d.get("meta",{})}
        for o in ops:
            m = o["method"].upper(); p = o["path"]
            for np in norm_variants(p):
                e["ops"].add((m,np)); e["paths"].add(np)
            if o.get("operationId"): e["byid"].setdefault(o["operationId"],(m,p))
        prod[(ver,product)] = e
    return prod

SEG_PARAM = re.compile(r"^(\{[^}]*\}|<[^>]*>|:[A-Za-z_].*)$")

def structural(p):
    """collapse parameter segments to '*'"""
    segs = p.strip("/").split("/")
    out=[]
    for s in segs:
        if SEG_PARAM.match(s): out.append("*")
        else: out.append(s)
    return "/"+"/".join(out)

def strip_prefixes(p):
    """yield p and p with each known base prefix removed"""
    res={p}
    for pref in PREFIXES:
        if p.startswith(pref+"/") or p==pref:
            res.add(p[len(pref):] or "/")
    # sdk/vim25/{release}
    m=re.match(r"^/sdk/vim25/[^/]+(/.*)$",p)
    if m: res.add(m.group(1))
    return res

def norm_variants(p):
    """all normalised forms of a spec path (for the index)"""
    out=set()
    for q in strip_prefixes(p):
        out.add(structural(q))
    return out

def claim_variants(p):
    """all normalised forms of a claimed path (for lookup)"""
    p = p.split("?")[0].split("#")[0]
    p = p.rstrip("/.,;:)`\"'")
    if not p.startswith("/"): p="/"+p
    out=set()
    for q in strip_prefixes(p):
        out.add(structural(q))
        # also try adding /v1 or /api back on, for files that quote bare paths
    return out

# ---------------------------------------------------------------- extraction
METHODS = r"GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS"
# METHOD /path  (in backticks, code fences, tables, prose)
RE_MP = re.compile(r"\b(" + METHODS + r")\s+(/[A-Za-z0-9_\-\.\{\}<>:/\*\$~,%\[\]]*)")
# curl -X METHOD ... url
RE_URL = re.compile(r"https?://[^\s`'\")]+")
# backticked bare paths starting with a known-ish prefix
RE_BAREPATH = re.compile(r"`(/(?:v1|api|policy|global-manager|suite-api|sdk|rest|fleet-lcm|sddc-lcm)[A-Za-z0-9_\-\.\{\}<>:/]*)`")
RE_OPID = re.compile(r"`([A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9_]*)+|[a-z][a-zA-Z0-9]{4,}|[A-Z][a-zA-Z0-9]{4,})`")

def version_of(path):
    if "/references/9.0/" in path: return ["9.0"]
    if "/references/9.1/" in path: return ["9.1"]
    return ["9.0","9.1"]   # deltas.md, SKILL.md, lookup.md -> either version acceptable

def extract(fp):
    txt=open(fp,encoding="utf-8").read()
    lines=txt.split("\n")
    paths=[]   # (line_no, method, path, linetext)
    for i,l in enumerate(lines,1):
        for m in RE_MP.finditer(l):
            paths.append((i,m.group(1).upper(),m.group(2),l.strip()))
        for m in RE_BAREPATH.finditer(l):
            paths.append((i,"ANY",m.group(1),l.strip()))
        for m in RE_URL.finditer(l):
            u=m.group(0)
            mm=re.match(r"https?://[^/]+(/.*)$",u)
            if mm: paths.append((i,"ANY",mm.group(1),l.strip()))
    opids=[]
    for i,l in enumerate(lines,1):
        for m in RE_OPID.finditer(l):
            opids.append((i,m.group(1),l.strip()))
    return paths,opids,lines

# ---------------------------------------------------------------- lookup
def lookup_path(prod, method, p, versions):
    """return list of (ver,product,operationId) hits"""
    hits=[]
    cv=claim_variants(p)
    for (ver,product),e in prod.items():
        if ver not in versions: continue
        for o in e["raw"]:
            if method!="ANY" and o["method"].upper()!=method: continue
            for np in norm_variants(o["path"]):
                if np in cv:
                    hits.append((ver,product,o.get("operationId"),o["method"],o["path"]))
                    break
    return hits

def lookup_path_anyver(prod, method, p):
    return lookup_path(prod, method, p, {"9.0","9.1"})

def lookup_opid(prod, oid, versions):
    hits=[]
    for (ver,product),e in prod.items():
        if ver not in versions: continue
        if oid in e["byid"]:
            hits.append((ver,product)+e["byid"][oid])
    return hits

# ---------------------------------------------------------------- main
def main():
    prod=load()
    all_opids=set()
    for e in prod.values(): all_opids|=set(e["byid"].keys())

    report={"path_misses":[], "path_wrongver":[], "opid_misses":[], "stats":defaultdict(lambda: defaultdict(int))}
    seen_pathclaim=set()

    for skill in TARGETS:
        sdir=os.path.join(SKILLS,skill)
        for fp in sorted(glob.glob(sdir+"/**/*.md",recursive=True)):
            rel=os.path.relpath(fp,SKILLS)
            vers=version_of(fp)
            paths,opids,lines=extract(fp)
            for (ln,meth,p,ctx) in paths:
                if len(p)<3: continue
                report["stats"][skill]["path_claims"]+=1
                if skill in NOSPEC_SKILLS:
                    continue
                hits=lookup_path(prod,meth,p,set(vers))
                if hits:
                    report["stats"][skill]["path_ok"]+=1
                    continue
                # try other version
                other=lookup_path_anyver(prod,meth,p)
                key=(skill,rel,meth,p)
                if key in seen_pathclaim:
                    continue
                seen_pathclaim.add(key)
                if other:
                    report["stats"][skill]["path_wrongver"]+=1
                    report["path_wrongver"].append(dict(skill=skill,file=rel,line=ln,method=meth,path=p,
                        claimed_ver=",".join(vers),found=[f"{h[0]}/{h[1]} {h[3]} {h[4]} ({h[2]})" for h in other][:4],ctx=ctx[:220]))
                else:
                    report["stats"][skill]["path_miss"]+=1
                    report["path_misses"].append(dict(skill=skill,file=rel,line=ln,method=meth,path=p,
                        claimed_ver=",".join(vers),ctx=ctx[:220]))
            # opids
            for (ln,tok,ctx) in opids:
                if tok in all_opids:
                    report["stats"][skill]["opid_ok"]+=1
                    hits=lookup_opid(prod,tok,set(vers))
                    if not hits:
                        other=lookup_opid(prod,tok,{"9.0","9.1"})
                        report["stats"][skill]["opid_wrongver"]+=1
                        report["opid_misses"].append(dict(skill=skill,file=rel,line=ln,opid=tok,kind="WRONG-VERSION",
                            claimed_ver=",".join(vers),found=[f"{h[0]}/{h[1]}" for h in other][:4],ctx=ctx[:200]))
    out="/home/claude/vcf-skills/review/scripts/out-endpoints.json"
    json.dump({k:(dict(v) if k=="stats" else v) for k,v in report.items()},open(out,"w"),indent=1,default=lambda o:dict(o))
    # print summary
    print("SKILL                              claims  ok  wrongver  MISS")
    for s in TARGETS:
        st=report["stats"][s]
        print(f"{s:34} {st['path_claims']:5} {st['path_ok']:5} {st['path_wrongver']:5} {st['path_miss']:5}")
    print("\n=== WRONG-VERSION path claims:",len(report["path_wrongver"]))
    print("=== MISS path claims:",len(report["path_misses"]))
    print("=== opid wrong-version:",len(report["opid_misses"]))

main()
