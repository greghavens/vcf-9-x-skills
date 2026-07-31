import json,re,glob,os
exec(open('/home/claude/vcf-skills/review/scripts/check2.py').read().split('METHODS=r"GET|POST')[0])
DEP={}
for k,e in PROD.items():
    for oid,o in e["byid"].items(): DEP.setdefault(oid,{})[k]=o.get("deprecated",False)
SK="/home/claude/vcf-skills/skills"
T=["vcf-domains-clusters","vcf-installer-bringup","vcf-certificates-credentials","nsx-segments-routing",
"nsx-network-services","vsphere-inventory-vm-lifecycle","vsphere-content-tags-policies","vsphere-lifecycle-vlcm",
"vsan-storage","vcf-operations-monitoring","vcf-operations-logs-and-networks"]
n=0;bad=[]
for s in T:
    for fp in glob.glob(SK+"/"+s+"/**/*.md",recursive=True):
        V={"9.0"} if "/9.0/" in fp else ({"9.1"} if "/9.1/" in fp else {"9.0","9.1"})
        for i,l in enumerate(open(fp).read().split("\n"),1):
            if not re.search(r"deprecat",l,re.I): continue
            neg = re.search(r"not deprecated|never deprecated|no.{0,12}deprecat|un-?deprecat",l,re.I)
            for oid in re.findall(r"`([A-Za-z][A-Za-z0-9_$\.]{5,})`",l):
                if oid not in DEP: continue
                n+=1
                vals={v:d for (v,p),d in DEP[oid].items() if v in V}
                if not vals: continue
                isdep=any(vals.values())
                if neg and isdep: bad.append((s,os.path.relpath(fp,SK),i,oid,"claimed NOT deprecated but spec says deprecated",l.strip()[:130]))
                elif not neg and not isdep: bad.append((s,os.path.relpath(fp,SK),i,oid,"claimed deprecated but spec says NOT deprecated",l.strip()[:130]))
print("deprecation claims checked:",n,"suspect:",len(bad))
for b in bad: print(f"  {b[0][:22]:23}{b[1].split('/')[-2][:7]:8}L{b[2]:<5}{b[3][:34]:36}{b[4]}\n      {b[5]}")
