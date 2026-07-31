# VCF 9.0 → 9.1 — vSphere inventory and VM lifecycle delta

Scoped to the vSphere Automation `/api` surface for inventory traversal and VM lifecycle.
For lifecycle/upgrade deltas see `vcf-lifecycle-upgrade`; for NSX see `nsx-security-policy`.

**Source keys.**
`SPEC9.0` / `SPEC9.1` = `research/spec-inventory/9.{0,1}__vsphere-automation.ops.json`,
machine-extracted from `specifications/vsphere/openapi/automation/vcenter.yaml` at git tags
`9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`.
`VIJSON9.0` / `VIJSON9.1` = the corresponding `*__vsphere-vi-json.ops.json`.
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed tag diff).
`DVS` = `research/vsphere-vcenter-vsan.md` (the dossier).
`[DOC]` = version-pinned Broadcom prose. `UNVERIFIED` = the research could not establish it.

---

## Headline: the surface barely moved

| | 9.0 | 9.1 |
|---|---|---|
| `vsphere-automation` operations | **1,275** | **1,367** |
| Base path | `https://{host}/api` | `https://{host}/api` — **unchanged** |
| Added / removed / newly deprecated | — | **+101 / −9 / 28** |
| VI-JSON operations (`/sdk/vim25/{release}`) | 2,195 | 2,243 |
| `vmw-task=true` operations | 144 | 151 |
| `/esx/settings/*` operations | 339 | 344 |
| `/content/*` operations | 72 | 83 |

[DELTA; SPEC9.0; SPEC9.1; VIJSON9.0; VIJSON9.1]

**Everything in the core inventory and VM surface is identical at both tags.** Session,
tasks, `/vcenter/vm` and its whole subtree, power, hardware, datacenter, cluster, host,
datastore, network, folder, resource-pool: same paths, same operationIds, same verbs.
The schemas people actually post — `Vcenter.VM.CreateSpec`, `Vcenter.VM.CloneSpec`,
`Vcenter.VM.PlacementSpec`, `Vcenter.VM.ClonePlacementSpec` — have **byte-identical property
sets and required lists** at both tags. [SPEC9.0; SPEC9.1]

That is the useful headline for anyone writing a client that must work against both: for
this scope, one client works, and the version question mostly reduces to auth and to the
`/hvc/*` removal below.

---

## Three premises to correct on contact

These all come from reading the 9.1 release notes without checking the spec.

**1. "The OAuth 2.0 token endpoint is new in 9.1."** No. The 9.1 release notes announce
*"OAuth 2.0 token support"* for vCenter **[DOC]**, and that is a real product statement. But
`POST /api/vcenter/authentication/token` (`Vcenter.Authentication.Token_issue`, RFC 8693
token exchange, `application/x-www-form-urlencoded`) is present at **both** tags, and its
own spec description says *"This operation was added in vSphere API 7.0.2.0."*
[SPEC9.0; SPEC9.1] What changed at 9.1 is capability or support posture, not the path. What
*is* 9.1-only is `POST /api/vcenter/registered-tokens`
(`Vcenter.RegisteredTokens_create`), for registering an Expanded Access Token so the
corresponding Overflow Access Token can be used. [SPEC9.1]

**2. "Live guest customization is new in 9.1."** No. The 9.1 what's-new page lists *"Live
Network Customization"* for powered-on VMs **[DOC]**, but
`GET /api/vcenter/vm/{vm}/guest/customization-live` and
`POST /api/vcenter/vm/{vm}/guest/customization-live?action=run&vmw-task=true` are in the
**9.0** spec, whose description states the operation *"was added in vSphere API 9.0.0.0."*
[SPEC9.0; SPEC9.1] Do not tell a 9.0 customer the API does not exist for them.

**3. "The Query API will fix my inventory pagination."** Not yet, not from documentation.
The 9.1 release notes announce a **Query API** for *"a fast, flexible, and scalable way to
retrieve vSphere inventory data"* with server-side filtering, pagination and entity counting
**[DOC]**. There is **no such path anywhere in `SPEC9.1`** — no `/vcenter/query`, no
`/query`; the only `/vcenter/inventory/*` operations are `Vcenter.Inventory.Datastore_find`
and `Vcenter.Inventory.Network_find`, both also in 9.0. Its paths, verbs and payloads are
`UNVERIFIED`. The dossier flags the same gap. Meanwhile the list caps below are unchanged.

---

## Delta table

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| **Base path** | `/api` on 443; `/rest` deprecated, pre-7.0.2 operations only; port 5480 subset | Identical wording in the 9.1 programming guide; identical `servers[0].url` in the spec | DVS; SPEC9.0; SPEC9.1 |
| **Session** | `POST·GET·DELETE /api/session` (`Cis.Session_create` / `_get` / `_delete`), `basic_auth` on create, 201, token in `vmware-api-session-id` | **Unchanged** — same three operations, same scheme, same header | SPEC9.0; SPEC9.1 |
| **Login gate** | **vCenter 9.0 blocks non-federated username/password logins** — verbatim removal statement | Not restated in the 9.1 support notes. A removal does not un-remove; assume still in force, but note the only verbatim source is 9.0-pinned | DVS `[DOC]` |
| **OAuth / federation** | `federated_identity_auth` bearer scheme declared; `POST /vcenter/authentication/token` present ("added in 7.0.2.0") | Same scheme, same token endpoint. **9.1 adds OAuth 2.0 support** as a product claim, plus `POST /vcenter/registered-tokens` | SPEC9.0; SPEC9.1; DVS `[DOC]` |
| **Tasks** | `GET /cis/tasks/{task}`, `POST /cis/tasks?action=list`, `POST /cis/tasks/{task}?action=cancel`; `Cis.Task.Status` = `PENDING\|RUNNING\|BLOCKED\|SUCCEEDED\|FAILED` | **Unchanged**. `vmw-task=true` operation count 144 → 151 | SPEC9.0; SPEC9.1 |
| **VM lifecycle** | 8 top-level VM operations + relocate/unregister; clone has a `$Task` form, instant-clone does not | **Byte-identical** | SPEC9.0; SPEC9.1 |
| **VM create / clone schemas** | `CreateSpec` (18 properties, `guest_os` required); `CloneSpec` (7 properties, `name` + `source` required); `PlacementSpec` / `ClonePlacementSpec` (5 properties, none required) | **Identical property sets and required lists** | SPEC9.0; SPEC9.1 |
| **VM power** | `GET` + `?action=start\|stop\|suspend\|reset`; guest `shutdown\|reboot\|standby` | **Unchanged** | SPEC9.0; SPEC9.1 |
| **VM hardware / reconfigure** | Full `/vm/{vm}/hardware/*` tree | **Unchanged** | SPEC9.0; SPEC9.1 |
| **Inventory list caps** | VM 4000; host 2500; datastore 2500; datacenter / cluster / folder / network / resource-pool 1000 each. No pagination cursor | **Identical caps, still no cursor.** The announced Query API is not in the spec | SPEC9.0; SPEC9.1; DVS `[DOC]` |
| **Filter parameters** | Flat, plural, `style: form` + `explode: true` (`names`, `folders`, `datacenters`, …). **No `filter.` prefix** | **Unchanged** | SPEC9.0; SPEC9.1 |
| **Enums** | `Folder.Type`, `Network.Type`, `Datastore.Type`, `Host.ConnectionState`, `Vm.Power.State`, `Task.Status` | **All identical** | SPEC9.0; SPEC9.1 |
| **`/vcenter/authorization`** | 18 operations incl. `Permissions_list` ("added in 9.0.0.0") and `PrivilegeChecks_list` | **18 operations, unchanged** | SPEC9.0; SPEC9.1 |
| **Host inventory** | `list`, `create`, `delete`, `connect`, `disconnect`, entropy pool | Adds `GET /vcenter/host/crypto/fips/modules`, `GET /vcenter/host/{host}/hardware/direct-path-devices`, `POST .../direct-path-devices?action=configure&vmw-task=true` | SPEC9.1 |
| **vCenter self-monitoring** | — | Adds `GET /vcenter/utilization/connections`, `GET /vcenter/utilization/proxies`, `GET /vcenter/capacity/usage`, `GET·PATCH /vcenter/deployment/size` (+ `/status`), `GET /vcenter/crypto/fips/modules` | SPEC9.1 |
| **Compute policies** | `GET` / `POST` / `DELETE` | Adds `PATCH /vcenter/compute/policies/{policy}` | SPEC9.1 |
| **Tagging** (routes to `vsphere-content-tags-policies`) | 30 ops under `/cis/tagging`; `GET /vcenter/tagging/{associations,categories,tags}` | Adds `PATCH /vcenter/tagging/associations` (atomic multi-tag update, rolls back on partial failure) | SPEC9.1 |
| **Content library** (routes away) | 72 operations | 83 — adds `DELETE /content/library/{id}`, `?action=convert\|enter-maintenance\|exit-maintenance\|force-delete`, `/content/library/{library}/usages*`, `force-delete` on local and subscribed libraries | DELTA; SPEC9.1 |
| **`/esx/settings/*`** (routes away) | 339 operations | 344 — adds configuration-draft `getAvailableValues` / `importConfig`, and `vms/transition` operations | DELTA; SPEC9.1 |
| **Hybrid Linked Mode `/hvc/*`** | **9 operations present** | **All 9 removed. No successor path.** See below | **DELTA** |
| **Newly deprecated in scope** | — | **None.** All 28 newly deprecated operations are under `/vcenter/namespace-management`, `/vcenter/namespaces` or `/appliance/health` | SPEC9.0; SPEC9.1 |
| **VI-JSON** | 2,195 ops, base `/sdk/vim25/{release}`, `Session` apiKey = `vmware-api-session-id` | 2,243 ops, same base, same scheme | VIJSON9.0; VIJSON9.1 |
| **Hypervisor name** | BOM row *"VMware ESX"*; 9.0 prose mixes ESX/ESXi | BOM row **"ESX"**; 9.1 what's-new uses ESX throughout. A formal "renamed from ESXi" statement is `UNVERIFIED` in both | DVS `[DOC]` |
| **VM hardware version** | **vmx-22** introduced with ESX 9.0 (960 logical processors, NVMe 1.4, 4KN VMDK, TDX, SEV-SNP) | No new VM hardware version announced. The *"vmx-10 to vmx-17"* line in the 9.1 notes is about the **vCenter appliance's own VM** | DVS `[DOC]` |
| **VM monitor** | (not stated) | **User-Level Monitor (ULM) is the default monitor for all VMs.** No API-surface effect this file can evidence | DVS `[DOC]` |
| **Confidential VMs** | SEV-SNP / TDX at limited availability | **General availability** | DVS `[DOC]` |
| **Snapshot consolidation** | *"more precise tracking of the progress of consolidation tasks"* | **Resumable Consolidation** for powered-on VMs. No spec-visible path change in this scope | DVS `[DOC]` |
| **ESX provisioning at scale** | Auto Deploy **deprecated** | **Zero Touch Provisioning (ZTP)** — secure UEFI + HTTPS network boot. Not an `/api/vcenter` surface | DVS `[DOC]` |

---

## The one breaking change: Hybrid Linked Mode `/hvc/*`

**Nine operations were removed from `vsphere-automation` between the two tags, and they are
all of `/hvc/*`.** Verbatim from `DELTA`:

```
DELETE /hvc/links/{link}                            Vcenter.Hvc.Links_delete
GET    /hvc/links                                   Vcenter.Hvc.Links_list
GET    /hvc/links/{link}                            Vcenter.Hvc.Links_get
GET    /hvc/management/administrators               Vcenter.Hvc.Management.Administrators_get
POST   /hvc/links                                   Vcenter.Hvc.Links_create
POST   /hvc/links/{link}?action=delete              Vcenter.Hvc.Links_deleteWithCredentials
POST   /hvc/management/administrators?action=add    Vcenter.Hvc.Management.Administrators_add
POST   /hvc/management/administrators?action=remove Vcenter.Hvc.Management.Administrators_remove
PUT    /hvc/management/administrators               Vcenter.Hvc.Management.Administrators_set
```

**Why it lands in inventory scope.** HLM linked a remote vCenter's SSO domain — and with it
its inventory — into the local vCenter. A script that enumerated VMs or hosts across an HLM
link, or that created or audited the links themselves, returns 404 after the upgrade. There
is no renamed successor path in `SPEC9.1`.

Of the seven products present at both tags, only two remove anything at all —
`vsphere-automation` (9, all `/hvc/*`) and `vcf-operations-for-networks` (1). That makes
`/hvc/*` the largest hard API breakage in the entire 9.0 → 9.1 delta. [DELTA]

> **`UNVERIFIED` on all three of the questions that actually matter:** whether **existing**
> HLM links keep functioning after the upgrade or are torn down; whether any replacement
> mechanism exists in 9.1; and whether the upgrade pre-checks for or blocks on HLM links.
> The removal is machine-confirmed from the two tags. The operational consequence is
> inferred and must be confirmed against Broadcom's 9.1 vCenter documentation before you
> upgrade an instance that uses HLM.

**Do not conflate HLM with Enhanced Linked Mode.** ELM was *deprecated* at 9.0 (use grouping
under VCF Operations instead) **[DOC]** — deprecated, not removed, and a different feature.
People merge the two because both are "linked mode".

---

## Announced in 9.1 but not in the spec

Three release-note features have no corresponding path in `SPEC9.1`. The dossier flags all
three as `UNVERIFIED — could not retrieve`, and the machine-extracted inventory independently
confirms their absence rather than resolving it.

| Feature, as announced **[DOC]** | Spec status |
|---|---|
| **Query API** — *"a fast, flexible, and scalable way to retrieve vSphere inventory data"*, server-side filtering, pagination, entity counting | **No path in `SPEC9.1`.** `UNVERIFIED` |
| **vCenter Group Federated API (VGFA)** — *"a single unified API endpoint for managing all vCenter instances in a vCenter group"* | **No path in `SPEC9.1`.** `UNVERIFIED` |
| **Utilization API** — *"monitors vCenter capacity and usage metrics"* | **Partly present**: `/vcenter/utilization/connections`, `/vcenter/utilization/proxies`, `/vcenter/capacity/usage` are spec-confirmed. Whether the announced API is larger than those three is `UNVERIFIED` |

Do not construct a path for the first two. The absence of a path in a spec that otherwise
enumerates 1,367 operations is weak evidence that the feature ships under a different
surface (in-product, SDK-only, or a spec not in this corpus), not evidence that you can
guess it.

---

## What did *not* change, restated for change records

- **`/api` base path, port 443, and the deprecated `/rest` restriction to pre-7.0.2
  operations.** Identical prose in both programming guides, identical `servers[0].url` in
  both specs.
- **Session mechanism.** `POST /api/session` with HTTP Basic → 201 → `vmware-api-session-id`.
  Three operations, both tags. And in both tags the specification declares them at
  **`/session`**, not `/cis/session` — the `cis` form is a portal rendering, not spec.
- **Every VM lifecycle, power and hardware operation**, and the create/clone/placement
  schemas.
- **Inventory list caps and the absence of pagination.**
- **Filter parameter encoding** — flat plural names, `style: form`, `explode: true`, repeat
  the parameter, no `filter.` prefix.
- **All six enums** used across this scope.
- **VI-JSON's base path, security scheme and role** as the fallback surface.

## Deltas this research could NOT establish

- **Query API and VGFA paths** — announced, absent from the spec, no reference page retrieved.
- **What specifically changed about OAuth 2.0 at 9.1**, given the token endpoint predates 9.x.
  `vcf-foundation` owns this.
- **Whether the 9.0 non-federated-login block is restated anywhere 9.1-pinned.** It is not on
  the pages retrieved; the assumption that it persists is reasoning, not a citation.
- **Fate of existing HLM links across the upgrade.** See above.
- **Session idle timeout** in either version — not in either spec, not on any page retrieved.
- **`Vcenter.Vm.Hardware.Version` enum member names** in either version — not extracted, so
  no statement about whether they changed.
- **Behavior when an inventory list exceeds its cap** in either version — silent truncation
  versus `UnableToAllocateResource` is not pinned down, so the *delta* is also unknown.
