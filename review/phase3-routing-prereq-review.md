# Phase 3 adversarial review — routing, prerequisites, delegation

Scope: 19 skills under `/home/claude/vcf-skills/skills/` (excluding `evals/`, `_shared/`).
Reviewer did not author these skills. Severity: **HIGH** (will produce a wrong answer or a
wrong skill choice on a realistic query) / **MEDIUM** (will produce an incomplete or
misleading answer) / **LOW** (cosmetic or structural only).

---

# Part 1 — Routing across 19 skills

## Method

All 19 `description` fields were read from frontmatter. 20 queries were written in the register
a VMware engineer actually types — hostnames, error strings, ticket-speak. For each, the
routing was predicted from the descriptions alone (the only thing an agent sees).

Description lengths run 672–1012 chars; all are under the 1024 limit. The two skills that most
need extra disambiguation wording — `vcf-foundation` (722) and `vcf-lifecycle-upgrade` (672) —
are the two with the most headroom, so every fix below is affordable.

## Scorecard

**11 clean / 5 ambiguous / 4 wrong out of 20.**

| # | Query | Predicted route | Correct route | Verdict |
|---|---|---|---|---|
| 1 | "sddc-mgr01.rainpole.io cert expires 14 Aug, need to CSR and reissue before the audit" | `vcf-certificates-credentials` (+ `vcf-foundation` co-fires) | `vcf-certificates-credentials` | AMBIGUOUS |
| 2 | "curl to sddc-mgr is throwing `SSL certificate problem: unable to get local issuer certificate`" | `vcf-foundation` | `vcf-foundation` | CLEAN |
| 3 | "whats the cmdlet to list workload domains, VCF.PowerCLI 9.1" | `powercli-vcf` **or** `vcf-api-discovery` | `powercli-vcf` | AMBIGUOUS |
| 4 | "is there a REST call that gives me the image per cluster on 9.1? cant find it in the broadcom docs" | `vcf-api-discovery` | `vsphere-lifecycle-vlcm` (answer is documented) | AMBIGUOUS |
| 5 | "going 9.0.1 → 9.1, what order do the components upgrade in" | `vcf-lifecycle-upgrade` | `vcf-lifecycle-upgrade` | CLEAN |
| 6 | "esx-04.sfo01 stuck remediating on cluster prod-01, image drift check keeps failing, `?action=apply` never returns" | `vcf-lifecycle-upgrade` | `vsphere-lifecycle-vlcm` | **WRONG** |
| 7 | "esx-05 is racked and burned in, need to add it to the mgmt cluster" | `vcf-domains-clusters` | `vcf-domains-clusters` | CLEAN |
| 8 | "we've got an existing vCenter 8.0U3 + NSX 4.1.2 with 12 hosts, customer wants it under VCF 9.1 — brownfield import, where do I start" | `vcf-domains-clusters` **or** `vcf-installer-bringup` | `vcf-installer-bringup` | **WRONG** |
| 9 | "block tcp/3389 from the web tier group to the db tier group" | `nsx-security-policy` | `nsx-security-policy` | CLEAN |
| 10 | "add seg-app-04 on tz-overlay-01 and hang it off t1-app-prod" | `nsx-segments-routing` | `nsx-segments-routing` | CLEAN |
| 11 | "need to publish app-web-07 to the internet, DNAT on t1-app-prod" | `nsx-network-services` | `nsx-network-services` | CLEAN |
| 12 | "403 from NSX when I POST a segment. session was fine 20 min ago" | `nsx-security-policy` | `nsx-segments-routing` (with NSX-403 knowledge) | AMBIGUOUS |
| 13 | "we're out of addresses — need another IP pool for the TEP range on the new cluster" | `nsx-network-services` | `vcf-domains-clusters` (SDDC Manager network pool) | **WRONG** |
| 14 | "pull 24h of cpu demand for web-prod-01 out of Ops, hourly buckets" | `vcf-operations-monitoring` | `vcf-operations-monitoring` | CLEAN |
| 15 | "log search for errors from esx-01 in the last hour, we're on 9.1" | `vcf-operations-logs-and-networks` | `vcf-operations-logs-and-networks` | CLEAN |
| 16 | "why is `/suite-api/api/dashboards` 404ing" | `vcf-operations-monitoring` | `vcf-operations-monitoring` | CLEAN |
| 17 | "request the 'Ubuntu 22 medium' catalog item into project fin-prod and poll the deployment" | `vcf-automation-vmapps` | `vcf-automation-vmapps` | CLEAN |
| 18 | "create a supervisor namespace for team-a, 200Gi quota" | `vcf-automation-allapps-k8s` **or** `vks-supervisor` | depends on org type | AMBIGUOUS |
| 19 | "spinning up a 3-node guest cluster, which ClusterClass do I reference on 9.1" | `vks-supervisor` | `vks-supervisor` | CLEAN |
| 20 | "need a storage policy, FTT=1 RAID-5, for the ESA cluster — and then check compliance" | `vsan-storage` | `vsphere-content-tags-policies` (PBM authoring) + `vsan-storage` (rule semantics) | **WRONG** |

## Findings

### R1 — `vcf-lifecycle-upgrade` swallows cluster-level ESX image work — HIGH

*Query 6. This is the worst mis-route in the set.*

`vcf-lifecycle-upgrade` says: *"Use this for any question about upgrading or patching VCF, SDDC
Manager, vCenter, **ESX**, NSX or vSAN"*, and names **no** sibling anywhere in its description.
`vsphere-lifecycle-vlcm` does the disambiguation work — but only from its own side
(*"Route fleet-level work … to `vcf-lifecycle-upgrade`"*). The routing is **asymmetric**, and
the query language a real engineer uses ("get esx-04 patched", "remediation is stuck") matches
the *broader* skill's literal words. The narrower, correct skill loses.

This matters more than a normal mis-route because the two skills point at genuinely different
APIs — `/v1/upgrades` on SDDC Manager versus `/api/esx/settings/clusters/{c}/software/...` on
vCenter. An agent routed to `vcf-lifecycle-upgrade` will not find a remediation draft API and
will either invent one or tell the user it does not exist.

**Fix (add to `vcf-lifecycle-upgrade`, ~130 chars, it has 350 spare):**
> "ESX host *images* at the vSphere cluster level — image drafts, base images, depots,
> `?action=check`/`apply` remediation and image drift — are `vsphere-lifecycle-vlcm`. This
> skill upgrades ESX only as a component of a VCF domain or fleet upgrade."

### R2 — "IP pool" is claimed by two skills with no cross-reference — HIGH

*Query 13.*

- `nsx-network-services`: *"IP pools, IP blocks and IP allocation (IPAM)"* — and, verbatim in
  its trigger-phrase list, ***"we're out of addresses in the pool"***.
- `vcf-domains-clusters`: *"creating or editing network pools and IP pools"*.

These are different objects: NSX Policy `IpAddressPool`/`IpAddressBlock` versus SDDC Manager
`NetworkPool`. In VCF the host TEP range is the SDDC Manager one. `nsx-network-services` will
win any query containing its own verbatim casual phrasing, and the agent will then be reading
the wrong API surface for the most common real instance of the question.

**Fix (add to `nsx-network-services`):**
> "IP pools here means NSX Policy `IpAddressPool` / `IpAddressBlock` objects. SDDC Manager
> *network pools* — the host TEP, vSAN and vMotion ranges consumed at commission time — are
> `vcf-domains-clusters`."

### R3 — "storage policies" is claimed by three skills; `vsan-storage` cross-links to neither owner — HIGH

*Query 20.*

- `vsphere-content-tags-policies`: *"storage policies including compliance"*, *"list storage
  policies"*, *"check storage-policy compliance"*, and explicitly owns the authoring split
  (*"create, update, delete — exists only on the VI-JSON PBM surface"*).
- `vsan-storage`: *"storage policies and compliance"* — routes to
  `vsphere-inventory-vm-lifecycle`, `vcf-domains-clusters` and `vcf-foundation`, but **not** to
  `vsphere-content-tags-policies`.
- `vks-supervisor`: *"VM classes, storage policies and Kubernetes releases"* — also silent.

A query naming a vSAN concept (FTT, RAID-5, ESA) plus the word "policy" routes to `vsan-storage`,
which is the skill *least* able to answer the authoring half of the question. The reference
files handle this correctly — both `vsan-storage/references/9.1/vsan.md` (`## Storage policies —
two surfaces, one concept`) and the content-tags file carry the PBM split — but the description
does not, and the description is what routes.

**Fix (add to `vsan-storage`):**
> "Creating, updating or deleting the storage-policy object itself is PBM authoring —
> `vsphere-content-tags-policies`. This skill covers what the vSAN rules in a policy mean and
> vSAN-side compliance and resync."

### R4 — `vcf-domains-clusters` and `vcf-installer-bringup` both claim brownfield vCenter import — MEDIUM

*Query 8.*

- `vcf-installer-bringup`: *"VCF Import and brownfield convergence … reusing an existing
  vCenter, NSX, vSAN or datastore"*.
- `vcf-domains-clusters`: *"brownfield vCenter import"*.

Both are correct in a narrow sense — Installer converges infrastructure into a *new* management
domain; SDDC Manager imports an existing vCenter as a *workload domain* into a *running* VCF
instance. Neither description states which. `vcf-installer-bringup` disambiguates only against
`vcf-lifecycle-upgrade`, never against `vcf-domains-clusters`.

**Fix (add to `vcf-domains-clusters`):** "…brownfield import of an existing vCenter as a
workload domain into a VCF instance that already exists — converging infrastructure into a
*new* management domain is `vcf-installer-bringup`."

### R5 — `vcf-api-discovery` and `powercli-vcf` both claim "before you state a cmdlet" — MEDIUM

*Query 3.*

`powercli-vcf` handles this correctly and explicitly: *"vcf-api-discovery finds REST operations
in the published OpenAPI specs; this skill finds and uses cmdlets"* and *"before you state any
cmdlet or parameter name in an answer"*. But `vcf-api-discovery` says *"whenever you are about
to state an endpoint, **cmdlet** or CRD you have not confirmed"* and *"whenever a VCF, vCenter,
NSX, vSAN or **PowerCLI** task needs a call"*. Both skills claim the same trigger, in the same
words, in opposite directions. The sibling that did the disambiguation work loses to the one
that did not.

**Fix (edit `vcf-api-discovery`):** change *"endpoint, cmdlet or CRD"* → *"endpoint or CRD —
for cmdlet and parameter names, `powercli-vcf` is the authority"*.

### R6 — `vcf-foundation`'s narrowing is real but incomplete on certificates — MEDIUM

*Query 1.* The narrowed description no longer swallows product operations — the clause
*"Product-specific skills (NSX, lifecycle) cover their own operations and call back here for
auth — consult this alongside them, not instead of them"* correctly turns it into a co-fire
rather than a takeover. That part works.

What does not work: `vcf-foundation` lists **"certificates"** flat, and names
`vcf-certificates-credentials` **nowhere**. `vcf-certificates-credentials` does all the boundary
work from its side (*"If instead a client is failing TLS verification … that is vcf-foundation —
go there first"*). Same asymmetry as R1. Combined with *"check here first whenever a VCF version
has not yet been established"* — which is true of nearly every real query — `vcf-foundation`
retains a broad first-strike claim over anything containing the word "certificate".

**Fix (add to `vcf-foundation`):** "Trusting a certificate is here. Replacing, rotating or
issuing one — CSRs, CA configuration, trust stores, password rotation — is
`vcf-certificates-credentials`."

### R7 — NSX 401/403 ownership is deliberate but costs a route — LOW (by design)

*Query 12.* `nsx-security-policy` claims *"any auth, 401 or 403 error encountered specifically
while calling NSX"*. A 403 hit while creating a **segment** therefore routes to the firewall
skill. This is a defensible design choice (NSX 403-on-expiry is a genuine cross-cutting trap)
and it is partly mitigated: all three NSX reference files carry the same 403 decode table, so
the wrong route still produces a right answer. Left as ambiguous rather than wrong. If it were
to be tightened, the phrase would become *"…for NSX auth mechanics themselves; a 403 hit during
segment or NAT work is decoded in those skills too."*

### R8 — Supervisor namespace is irreducibly ambiguous — LOW (handled)

*Query 18.* `vcf-automation-allapps-k8s` (*"creating or consuming supervisor namespaces with
kubectl"*) and `vks-supervisor` (*"vSphere Namespaces"*) genuinely overlap, because the answer
depends on whether VCF Automation is in the picture — a fact the user's query does not contain.
Both descriptions cross-link explicitly and in strong terms. This is as well handled as the
product allows; no fix proposed.

### Boundaries that came out clean

- **The three NSX skills against each other** (queries 9–11) are the best-disambiguated group in
  the set. Each names both siblings with the specific object families that belong to them.
- **`vcf-operations-monitoring` vs `vcf-operations-logs-and-networks`** (14–16) is the second
  best. The `Do NOT use it for…` clauses are bidirectional, specific, and name the sibling.
- **`vcf-automation-vmapps` vs `vcf-automation-allapps-k8s`** (17) is bidirectional and leads
  with the discriminator (*"establish which org type you are in before anything else"*).

---

# Part 2 — Prerequisites

## Structural compliance — per file

Rule under test: every version-scoped reference file opens with a `## Prerequisites` block
**before any endpoint**, each item stating (a) what must be true, (b) how to verify it, (c) the
version it applies to, (d) whether it exists in the other version; unverifiable items stated as
`UNVERIFIED`, not omitted.

**34 version-scoped files checked. 34 carry a `## Prerequisites` section. 32 fully compliant.**

| File | Prereq @ line | Items | Verdict |
|---|---|---|---|
| `nsx-network-services/references/9.0/services.md` | 82 | 8 (P1–P8) | PASS |
| `nsx-network-services/references/9.1/services.md` | 56 | 9 (P1–P9) | PASS |
| `nsx-security-policy/references/9.0/dfw.md` | 76 | 8 | PASS |
| `nsx-security-policy/references/9.1/dfw.md` | 54 | 8 | PASS |
| `nsx-segments-routing/references/9.0/networking.md` | 78 | 10 | PASS |
| `nsx-segments-routing/references/9.1/networking.md` | 53 | 10 | PASS |
| `vcf-automation-allapps-k8s/references/9.0/allapps.md` | 64 | 6 | PASS |
| `vcf-automation-allapps-k8s/references/9.1/allapps.md` | 58 | 7 | PASS |
| `vcf-automation-vmapps/references/9.0/vmapps.md` | 48 | 6 (P0–P5) | PASS |
| `vcf-automation-vmapps/references/9.1/vmapps.md` | 51 | 6 (P0–P5) | PASS |
| `vcf-certificates-credentials/references/9.0/certs-and-credentials.md` | 42 | 9 (table) | **PARTIAL — see P2-1** |
| `vcf-certificates-credentials/references/9.1/certs-and-credentials.md` | 45 | 12 (table) | **PARTIAL — see P2-1** |
| `vcf-domains-clusters/references/9.0/domains-clusters.md` | 60 | 10 | PASS |
| `vcf-domains-clusters/references/9.1/domains-clusters.md` | 65 | 11 | PASS |
| `vcf-foundation/references/9.0/auth-and-identity.md` | 38 | 11 | PASS |
| `vcf-foundation/references/9.1/auth-and-identity.md` | 41 | 14 (P0–P13) | PASS |
| `vcf-installer-bringup/references/9.0/bringup.md` | 74 | 10 | PASS |
| `vcf-installer-bringup/references/9.1/bringup.md` | 73 | 11 | PASS |
| `vcf-lifecycle-upgrade/references/9.0/lifecycle.md` | 47 | 9 | PASS |
| `vcf-lifecycle-upgrade/references/9.1/lifecycle.md` | 99 | 10 (P0–P9) | PASS |
| `vcf-operations-logs-and-networks/references/9.0/logs-and-networks.md` | 88 | 11 | **PARTIAL — see P2-2** |
| `vcf-operations-logs-and-networks/references/9.1/logs-and-networks.md` | 91 | 11 (T1–T6, N1–N4, P0) | PASS |
| `vcf-operations-monitoring/references/9.0/monitoring.md` | 61 | 9 | PASS |
| `vcf-operations-monitoring/references/9.1/monitoring.md` | 62 | 9 | PASS |
| `vks-supervisor/references/9.0/vks.md` | 63 | 9 | PASS |
| `vks-supervisor/references/9.1/vks.md` | 64 | 9 | PASS |
| `vsan-storage/references/9.0/vsan.md` | 80 | 8 (P0–P7) | PASS |
| `vsan-storage/references/9.1/vsan.md` | 81 | 8 (P0–P7) | PASS |
| `vsphere-content-tags-policies/references/9.0/content-tags-policies.md` | 53 | 9 | PASS |
| `vsphere-content-tags-policies/references/9.1/content-tags-policies.md` | 58 | 10 | PASS |
| `vsphere-inventory-vm-lifecycle/references/9.0/inventory-and-vms.md` | 53 | 8 | PASS |
| `vsphere-inventory-vm-lifecycle/references/9.1/inventory-and-vms.md` | 54 | 8 | PASS |
| `vsphere-lifecycle-vlcm/references/9.0/vlcm.md` | 57 | 8 | PASS |
| `vsphere-lifecycle-vlcm/references/9.1/vlcm.md` | 64 | 8 | PASS |

Content preceding the `## Prerequisites` heading in every file is provenance, a READ-THIS-FIRST
false-premise correction, or a table of contents. No file documents a *callable* endpoint before
its prerequisites except the one noted below.

### P2-1 — `vcf-certificates-credentials` omits the caller-privilege prerequisite from both prerequisite blocks — MEDIUM

`references/9.0/certs-and-credentials.md` lines 42–61 and `references/9.1/certs-and-credentials.md`
lines 45–66 contain **zero** occurrences of *role*, *privilege*, *permission* or *RBAC*. Every
one of the other 17 skills carries an explicit caller-authorisation prerequisite —
`vcf-domains-clusters` P10, `vcf-lifecycle-upgrade` P8, `vsan-storage` P6,
`vsphere-content-tags-policies` P10, `vsphere-inventory-vm-lifecycle` P4,
`vsphere-lifecycle-vlcm` P6, `vcf-operations-monitoring` P3, `vcf-automation-vmapps` P4 —
several of them explicitly tagged `UNVERIFIED`.

The skill *does* know the answer is unknown: `references/9.1/certs-and-credentials.md:533`
records under **Known unknowns** that the 9.1 doc set documents VCF Administrator / VCF Viewer /
SDDC Administrator / SDDC Viewer but does not map a role to an operation. That is the right
content in the wrong place. The project rule requires unverifiable prerequisites to be *stated
as UNVERIFIED in the prerequisites block*, not relegated to a gaps section a reader reaches
after they have already written the call.

This is the single highest-consequence instance of the omission in the set, because certificate
replacement and password rotation are precisely the operations most likely to be attempted by a
service account provisioned with less than administrator, and to fail at the last step of a
change window.

**Fix:** add a row to both tables — *"Caller holds a role permitting certificate/credential
writes. **UNVERIFIED** — the 9.x doc set names VCF Administrator / VCF Viewer / SDDC
Administrator / SDDC Viewer but maps no role to any of these operations; verify empirically with
a read before the change window. Same gap in the other version."*

### P2-2 — `vcf-operations-logs-and-networks/references/9.0/logs-and-networks.md` states two token endpoints before the Prerequisites heading — LOW

Lines 48 and 52 (an auth-summary block above `## Prerequisites` at line 88) give
`POST /api/v2/sessions` and `POST /api/ni/auth/token` as callable operations. This is a
technical breach of "no endpoint before prerequisites". Impact is near-zero — these are the auth
calls the prerequisites are about, and prerequisite L2/N1 restate them properly 40 lines later —
but it is the only file in the set that does it. The 9.1 sibling structures the same content as
prerequisite items T1/T2/N1 and does not have the problem; mirror that.

### P2-3 — Over-claiming: none found on ports and protocols — PASS (notable)

The specific over-claim the brief warned about is **not present**. Every skill that touches
network requirements marks the matrix unretrievable, by name, in the right place:

- `vcf-foundation/references/9.0/auth-and-identity.md:166`, `:567`, `:652` and the 9.1
  equivalents at `:221`, `:799`, `:911` — *"the per-service inbound port matrix could not be
  retrieved … ports.broadcom.com is a client-rendered tool"*, and it appears in the consolidated
  `UNVERIFIED` table, not only in prose.
- `vcf-foundation/references/9.1/auth-and-identity.md` P11 is titled, correctly, *"outbound
  HTTPS/443 allow-list is open, and the inbound side is **NOT** covered here"* — the prerequisite
  itself declares its own incompleteness. This is the model the rest should follow.
- `vcf-installer-bringup` 9.0:254 / 9.1:240 raise it to a blockquoted `UNVERIFIED` **inside** the
  prerequisites block (P4), which is where it does the most good, given bring-up is the one
  operation where the prerequisites *are* the work.
- `vcf-lifecycle-upgrade` 9.0:221, 9.1:233 and `references/upgrade-runbook.md:115` and `:445`
  quote Broadcom's own *"verify that all required ports are open"* and then immediately state
  that the referenced matrix was never retrieved — the correct handling of a prerequisite that
  points at a document you do not have.
- `vcf-domains-clusters` 9.0:232, 9.1:255 same treatment.

No skill's prerequisite list reads as a complete network-requirements statement. Skills that
name a specific port do so with a citation and a narrow claim —
`vsphere-inventory-vm-lifecycle` P1 quotes the vCenter 443 `/api` statement `[DOC]` and notes
the separate 5480 subset; `vcf-operations-logs-and-networks` 9.0 L3 pins 9543 with a verify
step; the 9.1 sibling's T4 is titled *"discover the real address and port; do not use 8787
blindly"*, which is the opposite of over-claiming. `vsan-storage` 9.0:260 / 9.1:258 scope their
one port claim to a single egress dependency (`vsanhealth.vmware.com:443`).

## Walk-back test — 12 worked examples

For each: what must already be true for this example to succeed, and does the skill say so?

| # | Worked example | Walk-back result |
|---|---|---|
| 1 | `vcf-domains-clusters/references/9.1/domains-clusters.md:666` — expand cluster by two hosts | **GAP — see W1** |
| 2 | `vsphere-inventory-vm-lifecycle/references/9.1/inventory-and-vms.md:721` — clone VM from template | **GAP — see W2** |
| 3 | `vsphere-content-tags-policies/references/9.1/content-tags-policies.md:825` — category, tag, attach | **GAP — see W3** |
| 4 | `nsx-network-services/references/9.1/services.md:655` — Tier-1 scoped SNAT | PASS |
| 5 | `nsx-security-policy/references/9.1/dfw.md:734` — block tcp/3389 between groups | PASS |
| 6 | `nsx-segments-routing/references/9.1/networking.md:763` — overlay segment on Tier-1 | PASS |
| 7 | `vsan-storage/references/9.1/vsan.md:381` — stretch a cluster | PASS (with declared gap) |
| 8 | `vsphere-lifecycle-vlcm/references/9.1/vlcm.md:603` — set base image and remediate | **MINOR GAP — see W4** |
| 9 | `vcf-operations-monitoring/references/9.1/monitoring.md:960` — CPU metrics over a range | PASS (exemplary) |
| 10 | `vcf-operations-logs-and-networks/references/9.1/logs-and-networks.md:647` — log query | PASS (exemplary) |
| 11 | `vcf-automation-allapps-k8s/references/9.1/allapps.md:362` — create supervisor namespace | PASS (exemplary) |
| 12 | `vsan-storage/references/9.0/vsan.md` + `vcf-installer-bringup/references/9.1/bringup.md:73` P0–P10 | PASS |

### W1 — Cluster-expansion example names a network profile and a VDS that nothing tells you how to find — MEDIUM

`vcf-domains-clusters/references/9.1/domains-clusters.md`, step 4, lines 725–733:

```json
"hostNetworkSpec": {
  "networkProfileName": "np-vsan-01",
  "vmNics": [ { "id": "vmnic0", "vdsName": "sfo-w01-cl01-vds01", "uplink": "uplink1" }, … ]
}
```

`networkProfileName` and `vdsName` appear **only** in these two payload blocks — six hits in the
whole file, all inside the example. They are not covered by any of P1–P11, and step 0 of the
example ("find the network pool and the target cluster") resolves `getNetworkPool` and
`getClusters` but not the network profile or the VDS.

Both are pre-existing objects on the target cluster whose *names* must match exactly. Getting
either wrong produces a validation failure at step 4 that names a field, not a cause. The file's
own discipline elsewhere is exactly the opposite of this — step 3 is a whole step devoted to
"capture their IDs … `HostSpec.id` for the expansion is the `id` returned here, not the FQDN".
The same rigour was not applied one step later.

This is the classic unstated dependency the walk-back test is designed to catch: **an object
that must pre-exist**, with **no prior call whose output feeds this one**.

**Fix:** add to step 0 a read that enumerates the cluster's existing network profiles and its
VDS names, or add a prerequisite stating that both are pre-existing names on the target cluster
that must be read, not composed — and mark the read `UNVERIFIED` if the research did not
establish which endpoint returns them.

### W2 — Clone example resolves an inventory *template* through the VM list operation — MEDIUM (PLAUSIBLE)

`vsphere-inventory-vm-lifecycle/references/9.1/inventory-and-vms.md`, step 2:

```bash
SRC=$(curl -sS "${AUTH[@]}" "$VC/api/vcenter/vm?names=$SOURCE_NAME" | jq -r '.[0].vm')
```

with `SOURCE_NAME=tmpl-rhel9` and the example titled *"clone a VM from a template in inventory"*.

The file does excellent work on the *other* template ambiguity — the blockquote at line 741
distinguishes an inventory template from a content-library VM template item and routes the
latter to `vsphere-content-tags-policies`. But it does not address whether a VM **marked as a
template** in vCenter inventory is returned by `Vcenter.VM_list` at all. If it is not, step 2's
guard fires `FATAL: SRC unresolved` and the reader is sent to P5/P6 — placement identifiers —
which is the wrong diagnosis entirely; the actual remedy is to convert the template to a VM
first, or use the `VmTemplate` family.

Marked **PLAUSIBLE** rather than CONFIRMED: the spec inventory in
`vcf-api-discovery/references/spec-inventory/9.1__vsphere-automation.ops.json` carries operation
lists, not the `VM_list` filter semantics, so this could not be settled from the corpus. That
itself is the point — if it cannot be settled, the rule requires it be stated as `UNVERIFIED`,
and it is not stated at all.

**Fix:** one line in the step-2 guard — *"if `tmpl-rhel9` is marked as a template rather than a
powered-off VM, whether `Vcenter.VM_list` returns it is **UNVERIFIED**; if `SRC` comes back
empty, convert to VM or use the `vm-template` family before assuming a naming error."*

### W3 — Tagging example's step 0 uses the exact login form its sibling documents as blocked — MEDIUM

`vsphere-content-tags-policies/references/9.1/content-tags-policies.md`, step 0:

```bash
TOKEN=$(curl -sS -u "$VC_USER:$VC_PASS" -X POST "$VC/api/session" | jq -r '.')
[ -z "$TOKEN" ] || [ "$TOKEN" = null ] && { echo "FATAL: no session — see vcf-foundation" >&2; exit 1; }
```

and P1 says only *"Obtaining the credential is `vcf-foundation`'s job. This file states the
mechanism and the base path and stops there."*

The delegation is correct in principle. The problem is that the *specific* failure this example
will hit is a known, documented, version-gated one, and this file does not name it.
`vsphere-inventory-vm-lifecycle`, which shares the identical step 0, gets it right: its P2 is
titled *"Your credential can actually create a session (the 9.0 gate still applies)"*, quotes
the removal note verbatim (*"Blocked non-federated username/password logins to vCenter"*), and
its failure-decode table (line 912) reads *"401 on step 0 with a credential you trust → **P2** …
Not a typo."*

A reader who lands in `vsphere-content-tags-policies` gets `FATAL: no session` and a pointer to
a skill with 1050 lines of auth material, rather than the one-line diagnosis. The unstated
dependency is a **version gate on a federated deployment** — exactly the category the walk-back
test targets.

**Fix:** add to P1 — *"On a federated vCenter the basic-auth form in step 0 is blocked (removal
introduced at 9.0, still applies at 9.1); a 401 there is the federation gate, not a wrong
password. See `vsphere-inventory-vm-lifecycle` P2 and `vcf-foundation` P4."* Cheap, and it makes
the two vCenter skills agree.

### W4 — vLCM example takes `$CL` as given — LOW

`vsphere-lifecycle-vlcm/references/9.1/vlcm.md:603` opens *"`$CL` a `ClusterComputeResource` id
such as `domain-c8`"* and never says how to obtain it. Every other identifier in the example is
resolved from a prior call (base-image `version` from step 1, with an explicit *"Do not invent
one"*), so the omission is conspicuous. One line routing to `vsphere-inventory-vm-lifecycle`'s
cluster list — or noting that VCF-managed clusters are correlated through SDDC Manager per P5 —
would close it.

### Walk-back passes worth naming

Three examples are models of the discipline and should be the template for fixing W1–W3:

- **`vcf-operations-monitoring` step 2→3→4→5** resolves name → identifier → collection state →
  stat key → query, with step 3 annotated *"This is P5, and it is the step people skip"* and
  step 4 *"guessing here is the difference between data and an empty array"*. Every input to
  every call is the output of a prior call.
- **`vcf-automation-allapps-k8s`** is subtitled *"discovery-first — four discovery steps before
  one write"*, refuses to hard-code the kubectl context (*"Do not assume the context is named
  'cci'"*) or the CRD version (*"replace with the served version from step 2"*), and closes with
  a failure map keyed to prerequisite numbers.
- **`vcf-operations-logs-and-networks`** discovers the log service's own address and port from
  the token-exchange response rather than assuming 8787, and then marks its own query field
  names `UNVERIFIED` with a `match_all` probe to learn the real ones — an example that honestly
  labels its weakest part.

---

# Part 3 — Delegation and duplication

## D1 — vCenter session auth is claimed by three skills, and they disagree about who owns the 401 — MEDIUM

This is the one genuine **cross-skill contradiction** in the set, and per the brief it is worse
than the duplication.

| Skill | What it says about a vCenter 401 |
|---|---|
| `vcf-foundation` (description) | owns *"Authentication … fixing certificate and TLS trust errors"*; `references/9.0/auth-and-identity.md:84` carries **P4 — vCenter 9.0 blocks non-federated username/password logins** |
| `vsphere-inventory-vm-lifecycle` (description) | *"use it whenever someone … is hitting 401/403 against vCenter, since vCenter 9.0 blocks non-federated username/password logins"* — claims the 401 for itself |
| `vsphere-content-tags-policies` (`9.1/…:841` step 0) | *"Credential acquisition, and any 401 here, belongs to `vcf-foundation` (P1)"* — routes the 401 away |

Two sibling skills sharing an identical `POST /api/session` step 0 send the same failure to two
different owners. The *facts* are consistent everywhere — the verbatim removal quote matches
across `vcf-foundation` 9.0:87, 9.1:245, `deltas.md:105` and `vsphere-inventory-vm-lifecycle`
9.0:89, 9.1:91, `deltas.md:81`, and `vsphere-lifecycle-vlcm/references/9.0/vlcm.md:24` correctly
defers the whole topic — so this is a routing contradiction, not a factual one. Pick one owner
and make the other two point at it. Given `vsphere-inventory-vm-lifecycle` carries the best
treatment (P2 plus a failure-decode row), it is the natural owner for the *vCenter-specific*
gate, with `vcf-foundation` owning credential acquisition generally.

## D2 — NSX session auth is re-derived in three skills instead of one — MEDIUM (duplication, no contradiction)

`nsx-security-policy`'s description claims NSX auth ownership (*"that skill also owns NSX auth
and 401/403 debugging"*, echoed by `nsx-segments-routing`). Despite that, the full flow —
`POST /api/session/create`, form fields `j_username`/`j_password`, `JSESSIONID` cookie **plus**
`X-XSRF-TOKEN` header, both required, 1800 s default, `PUT /api/v1/cluster/api-service` to
change it — is written out in **six** reference files plus **four** SKILL.md bodies plus
`vcf-api-discovery/references/live-discovery.md:39`, and a fourth time in
`vcf-foundation/references/9.0/auth-and-identity.md:253` and `9.1/…:372`.

Mitigating factors, and they are substantial:

- **Every statement agrees.** 1800 s, both headers, cookie name, `j_username`/`j_password`, and
  403-not-401 on expiry are identical everywhere checked. No contradiction.
- The 9.1 evidence grading is handled with more care than the duplication suggests:
  `nsx-security-policy/references/9.1/dfw.md:283–289` notes that `default: 1800` on
  `ApiServiceConfig` is the *only* spec evidence and that `GET /api/v1/cluster/api-service`
  returns no `session_timeout` key — a caveat the duplicates do **not** carry.
- `nsx-segments-routing/references/9.0/networking.md:317` explicitly says *"That is the whole
  flow at the depth this file needs. **Do not re-derive it here.**"* — the right instinct,
  stated immediately after re-deriving it.

The cost is a maintenance surface: eleven places must change together, and one of them
(`nsx-security-policy` 9.1) already carries a nuance the other ten do not. The
`nsx-network-services` worked example (line 686) and `nsx-segments-routing` worked example
(line 786) both need a runnable step 0, so a bare link is not sufficient — but the ~10-line
prose expansions in `9.0/services.md:295–297`, `9.1/services.md:301–304`,
`9.0/networking.md:308–317` and `9.1/networking.md:268–271` could collapse to a one-line
pointer plus the shell block.

## D3 — Delegation that works, and should be the pattern

Auth delegation is, on the whole, done properly. Evidence:

- **`powercli-vcf`** — description states it outright: *"Module install and Connect-* session
  setup live in vcf-foundation's powercli-session reference; this skill links there rather than
  restating it."* `vcf-foundation/references/powercli-session.md` exists and is the single copy.
  This is the cleanest delegation in the set.
- **`vsan-storage`** — `9.0/vsan.md:99` and `9.1/vsan.md:100` give one table row per surface
  with *"`POST /v1/tokens` — see `vcf-foundation`"* and stop. Six references to `vcf-foundation`
  in the 9.0 file, no re-derivation.
- **`vsphere-lifecycle-vlcm`** — `9.1/vlcm.md:605` opens the worked example with *"Auth headers
  omitted — see `vcf-foundation`"*, and `9.0/vlcm.md:739` hands `POST /v1/tokens` and all bundle
  and depot work to the correct siblings by name.
- **`vcf-certificates-credentials`** — prerequisite rows 1 and 2 in both files cite
  *"`vcf-foundation`, `references/9.x/auth-and-identity.md` `[R-auth §1]`"* with a section
  anchor rather than restating the flow.

## D4 — Facts checked across skills for contradiction: no others found

Hot facts were cross-checked in every file that states them. All agree:

| Fact | Files agreeing | Status |
|---|---|---|
| SDDC Manager access token 1 h / refresh 24 h | `vcf-foundation` 9.0:199,405,406 and 9.1:547,548; `vcf-lifecycle-upgrade` 9.0:169, `deltas.md:43,106`, `upgrade-runbook.md:197` | consistent |
| VCF Operations token 6 h, no refresh | `vcf-foundation` 9.0:407, 9.1:549; `vcf-operations-monitoring` 9.0:68,81 and 9.1 P1; `vcf-operations-logs-and-networks` 9.1:116 | consistent |
| SDDC Manager excluded from VCF SSO | `vcf-foundation` P6; `vcf-certificates-credentials` 9.0 row 1 / 9.1 row 2; `vcf-lifecycle-upgrade` `deltas.md:43` | consistent |
| NSX session 1800 s, `JSESSIONID` + `X-XSRF-TOKEN` both required, 403 on expiry | 11 locations (D2) | consistent |
| vCenter 9.0 blocks non-federated username/password login | `vcf-foundation` 9.0:84,87 / 9.1:245 / `deltas.md:105`; `vsphere-inventory-vm-lifecycle` 9.0:89 / 9.1:91 / `deltas.md:81`; `vsphere-lifecycle-vlcm` 9.0:24 | consistent |
| VM Apps token lifetimes | apparent conflict — `deltas.md:70` says 90 days / 1 hour, `9.1/vmapps.md:100` says 30 days / 30 minutes — **resolved correctly in the text**: two coexisting token systems, tenant flow (90 d / 1 h, unchanged) versus VIDB clients new at 9.1 (30 d / 30 min), with the failure mode called out (*"A script written against 90-day assumptions and issued a 30-day VIDB token will fail about a month in"*). Matches `vcf-foundation` 9.0:410 and 9.1:118,544. | consistent |

`_shared/answering.md` is not linked from any SKILL.md, but its content **is** inlined verbatim
in all 19 (the "Answer the question that was asked" block). No defect; noted only because the
file header's claim that it "is appended to every VCF skill's SKILL.md" is true and easily
mistaken for a dangling reference.

---

# Summary of findings by severity

**HIGH**
- R1 — `vcf-lifecycle-upgrade` claims "upgrading ESX" and names no sibling; swallows
  `vsphere-lifecycle-vlcm` cluster-image work.
- R2 — "IP pool" claimed by `nsx-network-services` (with the verbatim casual phrasing) and
  `vcf-domains-clusters`, no cross-reference either way.
- R3 — "storage policies" claimed by `vsan-storage`, `vsphere-content-tags-policies` and
  `vks-supervisor`; `vsan-storage` cross-links to neither owner of PBM authoring.

**MEDIUM**
- R4 — brownfield vCenter import claimed by both `vcf-domains-clusters` and
  `vcf-installer-bringup`.
- R5 — `vcf-api-discovery` and `powercli-vcf` both claim "before you state a cmdlet".
- R6 — `vcf-foundation` lists "certificates" flat and never names
  `vcf-certificates-credentials`.
- P2-1 — `vcf-certificates-credentials` omits the caller-privilege prerequisite from both
  prerequisite blocks; the `UNVERIFIED` statement exists but is buried in Known unknowns.
- W1 — cluster-expansion example depends on `networkProfileName` and `vdsName` with no
  prerequisite and no resolving call.
- W2 — clone example resolves a marked template via `Vcenter.VM_list`; unstated and
  unverified (PLAUSIBLE).
- W3 — tagging example's step 0 uses the login form its own sibling documents as blocked, and
  does not name the gate.
- D1 — vCenter 401 ownership contradicts between `vsphere-inventory-vm-lifecycle` and
  `vsphere-content-tags-policies`.
- D2 — NSX session flow re-derived in 11 places despite a declared single owner.

**LOW**
- R7 — NSX 401/403 ownership costs a route on segment work (by design, mitigated).
- R8 — supervisor-namespace ambiguity (irreducible, well handled).
- P2-2 — two token endpoints stated before `## Prerequisites` in
  `vcf-operations-logs-and-networks/references/9.0/logs-and-networks.md`.
- W4 — vLCM example takes `$CL` as given.

**Notable passes**
- P2-3 — the ports-and-protocols over-claim the brief warned about does not exist; all six
  skills that touch it mark the matrix unretrievable, by name, in the right place.
- 32 of 34 version-scoped files are fully prerequisite-compliant.
- The three NSX skills, and the two VCF Operations skills, are the best-disambiguated groups.
- Auth delegation to `vcf-foundation` is genuine in `powercli-vcf`, `vsan-storage`,
  `vsphere-lifecycle-vlcm` and `vcf-certificates-credentials`.
