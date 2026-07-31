# VCF 9.1 — Workload Domains, Clusters, Hosts and Network Pools

**Scope:** topology management on VMware Cloud Foundation 9.1 through the **SDDC Manager API**
(`https://<sddc-manager-fqdn>/v1`). Everything here is `[9.1]` unless explicitly tagged otherwise.
Upgrades and patching are **not** in scope — use the `vcf-lifecycle-upgrade` skill for those.

**SDDC Manager still owns this in 9.1.** Its **UI** is deprecated; its **API is not**, and it grew
from 375 to 423 operations with **zero removed** [DELTA; D9.1 §0.3]. The 9.1 components page
assigns it *"deployment of workload domains; import of vCenter instances; configuration of vSAN
stretched clusters"* [D9.1 §2]. Anyone who believes SDDC Manager was removed in 9.1 will
architect around an API that is present and expanded.

**Sources.**
`D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of git tags
`9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`).
`SPEC9.1` = `research/spec-inventory/9.1__sddc-manager.ops.json` — 423 operations, spec version
`9.1.0.0`, extracted from git tag `9.1.0.0`.
`RAW9.1` = `/tmp/vcf-api-specs/specifications/sddc-manager/sddc-manager-openapi.json` at git tag
`9.1.0.0`, used for request/response **schemas**.

**Verification rule.** Every path below was checked against `SPEC9.1` and is marked
**spec-confirmed (9.1)** with its `operationId`. Where an operation is new in 9.1 it is marked
**9.1-only** so it is never carried backwards to 9.0.

**Auth is out of scope here.** Obtaining and refreshing the SDDC Manager bearer token is the
`vcf-foundation` skill's job.

**Endpoint count.** 147 operations across the nine topology tags (`Clusters` 38, `Domains` 35,
`Hosts` 21, `NSX-T Clusters` 18, `Network Pools` 13, `BrownfieldImport` 10, `NsxTEdgeClusters` 8,
`PSCs` 2, `vCenters` 2) — **19 more than 9.0, none removed** — plus `HcxManagers` 6 and
`UpdateVcenterFqdn` 1, both entirely new, and 26 supporting operations (`ALBClusters` 15,
`vSANHealthCheck` 4, `Tasks` 4, `ConfigReconciler` 3). All counted from `SPEC9.1`.

---

## Contents

- [Prerequisites](#prerequisites)
  - P1 — A valid SDDC Manager bearer token
  - P2 — Hosts are commissioned and sitting in the free pool
  - P3 — A network pool exists and carries the network types the cluster needs
  - P4 — Host storage type matches the cluster's datastore type
  - P5 — The target domain and cluster are in a stable state — and cached reads can lie
  - P6 — A vLCM cluster image is chosen — mandatory on vCenter 9.0+
  - P7 — DNS and NTP are set on the domain or cluster, not on the system
  - P8 — Licensing state permits the operation
  - P9 — A clusterless domain cannot be patched or upgraded
  - P10 — Caller role and privilege — UNVERIFIED
  - P11 — Items the research could not verify
- [The topology object model](#the-topology-object-model)
- [The universal pattern: validate → execute → poll](#the-universal-pattern-validate--execute--poll)
- [Hosts and the free pool](#hosts-and-the-free-pool)
- [Network pools](#network-pools)
- [Workload domains](#workload-domains)
- [Clusters](#clusters)
- [vCenter, NSX, ALB, HCX and PSC association](#vcenter-nsx-alb-hcx-and-psc-association)
- [Brownfield import, drift and remediation](#brownfield-import-drift-and-remediation)
- [Worked example — expand an existing cluster by two hosts](#worked-example--expand-an-existing-cluster-by-two-hosts)
- [Destructive operations and their gates](#destructive-operations-and-their-gates)
- [Discrepancies and UNVERIFIED items](#discrepancies-and-unverified-items)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what must
hold, **how to verify it**, the version it applies to, and whether 9.0 differs.

### P1 — A valid SDDC Manager bearer token `[9.1]`

**Must be true:** you hold an SDDC Manager access token and send it as
`Authorization: Bearer <accessToken>`. SDDC Manager remains **excluded from VCF SSO** in 9.1 — the
VIDB OAuth flow that unifies the other components does not cover it.

**How to verify:** `GET /v1/domains` (`getDomains`, **spec-confirmed (9.1)**) returns `200` with a
`PageOfDomain`.

**Do not restate the auth flow from here.** Route to the `vcf-foundation` skill.

**9.0 difference:** none for SDDC Manager. The 9.1-only OAuth/API-token machinery applies to other
components; `vcf-foundation` owns that boundary.

### P2 — Hosts are commissioned and sitting in the free pool `[9.1]`

**Must be true:** every host you intend to place in a cluster must already be **commissioned** and
unassigned. `HostSpec.id` is documented in `RAW9.1` as *"ID of a vSphere host in the free pool."*

**How to verify:** `GET /v1/hosts?status=UNASSIGNED_USEABLE` (`getHosts`,
**spec-confirmed (9.1)**). `Host.status` example: `ASSIGNED, UNASSIGNED_USEABLE,
UNASSIGNED_UNUSEABLE`. `UNASSIGNED_UNUSEABLE` is a blocker, not a candidate.

**To get hosts there:** `POST /v1/hosts` (`commissionHosts`, **spec-confirmed (9.1)**), body a
JSON **array** of `HostCommissionSpec`. Required: `fqdn`, `username`, `password`, `storageType`,
`networkPoolId` — identical to 9.0.

**9.1-only filters on `getHosts`:** `isStandalone`, `isLifecycleManaged`, `isVsanWitnessHost`,
`ipAddressVersionForVmotion` (`IPv4`/`IPv6` — the dual-stack hook), plus `pageSize`/`pageNumber`.
The old `size`/`page` parameters still exist but are **marked deprecated in the 9.1 spec**.

**9.0 difference:** those four filters and the pagination rename do not exist in 9.0. The
`Host` schema also gains `isStandalone`, `isLifecycleManaged`, `isVsanWitnessHost` and
`managedObjectReferenceId` in 9.1 — support for imported standalone hosts and single-host clusters
is a 9.1 feature [D9.1 §3.5].

### P3 — A network pool exists and carries the network types the cluster needs `[9.1]`

**Must be true:** `HostCommissionSpec.networkPoolId` is **required**, so the pool must exist before
the first host is commissioned.

**How to verify:** `GET /v1/network-pools` (`getNetworkPool`),
`GET /v1/network-pools/{id}/networks` (`getNetworksOfNetworkPool`), and — **9.1-only** —
`GET /v1/network-pools/{networkPoolId}/networks/{networkId}/ips` (`getIpFromNetwork`) for the
per-IP view. The 9.1 `Network` schema also adds `freeIpCount` and `usedIpCount` alongside the
`freeIps`/`usedIps` arrays, which is the cheaper capacity check.

**To create one:** `POST /v1/network-pools` (`createNetworkPool`, **spec-confirmed (9.1)**), body
`NetworkPool`, required `name` and `networks[]`. Each `Network` requires `type`, `vlanId`, `mtu`.

**9.0 difference — the required set shrank.** `subnet`, `mask` and `gateway` are **required on
`Network` in 9.0 and optional in 9.1**. 9.1 adds `ipAddressVersion` (`IPv4`/`IPv6`, default
`IPv4`) and `ipAddressAssignmentMode` (`STATIC`/`DHCP`/`SLAAC`, default `STATIC`) — the dual-stack
support advertised in [D9.1 §3.4]. Neither field exists in 9.0. A pool spec written for 9.1 with
`ipAddressVersion: IPv6` and no `subnet` will be rejected by a 9.0 instance.

### P4 — Host storage type matches the cluster's datastore type `[9.1]`

**Must be true:** the `storageType` a host was commissioned with must be consistent with the
`DatastoreSpec` of the cluster it joins.

**How to verify:** `GET /v1/hosts?storageType=…` (`getHosts`); the parameter documents
`VSAN, VSAN_ESA, VSAN_REMOTE` as filterable. The broader set appears only as a schema **example**
on `HostCommissionSpec.storageType`:
`VSAN, VSAN_ESA, VSAN_REMOTE, VSAN_MAX, NFS, NFS41, VMFS_FC, VVOL, VMFS, FC, VVOL` (the source
text does repeat `VVOL`). `vvolStorageProtocolType` example: `ISCSI, NFS, FC`.

**9.0 difference:** the 9.0 example string omits `NFS41` and the bare `FC`. Do not send either to
a 9.0 instance. Note also that this is an `example`, not an `enum`, in **both** versions — see P11.

### P5 — The target domain and cluster are in a stable state — and cached reads can lie `[9.1]`

**Must be true:** the domain and cluster are not mid-operation. `Domain.status` and
`Cluster.status` examples: `ACTIVE, ACTIVATING, UPGRADING, DISABLED, ERROR, SKIPPED, DEACTIVATING,
EXPANDING, SHRINKING, CREATING`. Only `ACTIVE` is a safe starting point.

**How to verify:** `GET /v1/domains/{id}` (`getDomain`), `GET /v1/clusters/{id}` (`getCluster`),
and `GET /v1/tasks?resourceId=<id>` (`getTasks`).

> **9.1-only hazard.** `getClusters` and `getDomains` gain a `useCache` query parameter — *"get
> cluster details from cache"* / *"get domain details from cache"*. A cached read is exactly the
> wrong thing for a pre-flight state check. For a gate, omit `useCache` or set it `false`.

**9.0 difference:** `useCache` does not exist in 9.0, so 9.0 reads are always live. 9.1 also adds
`name`, `managedObjectReferenceId`, `isDefault`, `isHciMeshEnabled` and pagination to
`getClusters`, and `name`, `vcFqdn`, `vcInstanceId`, `isManagementSsoDomain` and pagination to
`getDomains`.

### P6 — A vLCM cluster image is chosen — mandatory on vCenter 9.0+ `[9.1]`

**Must be true:** `ClusterSpec.clusterImageId` is documented in `RAW9.1` (identical text to 9.0) as
*"required, if we want to create a cluster on vCenter 9.0 or above."*

**How to verify:** `GET /v1/personalities` (`getPersonalities`, **spec-confirmed (9.1)**);
`GET /v1/clusters/{id}/image-compliance` (`getClusterImageCompliance`); and — **9.1-only** —
`POST /v1/domains/{domainId}/image-compliance/queries` (`queryDomainImageCompliance`) →
`GET /v1/domains/{domainId}/image-compliance/queries/{queryId}`
(`getDomainImageComplianceQueryResponse`) for a whole-domain view.

**9.1-only alternative:** `ClusterSpec.hostIdForHostSeeding` — *"the identifier of the UNASSIGNED
host that will be used as the reference host to extract the image from when creating the desired
state for the cluster. It MUST NOT denote an ASSIGNED host."* Seed the image from a host instead
of naming a personality. **This field does not exist in 9.0.**

### P7 — DNS and NTP are set on the domain or cluster, not on the system `[9.1]`

**Must be true:** DNS and NTP reach the right place. In 9.1 they are **topology-scoped**:
`dnsServers[]` and `ntpServers[]` are properties of `DomainCreationSpec` and
`ClusterCreationSpec`, and `dnsNtpUpdateSpec` (a `DnsNtpUpdateSpec` with the same two arrays) is a
property of `DomainUpdateSpec` and `ClusterUpdateSpec`. `Domain` and `Cluster` responses carry
`dnsServers`/`ntpServers` back. This is the *"streamlined DNS and NTP management at scale"* item
[D9.1 §3.5].

**How to verify:** read `dnsServers`/`ntpServers` off `GET /v1/domains/{id}` and
`GET /v1/clusters/{id}`.

> **The old system-level surface is deprecated in 9.1.** All nine operations of
> `/v1/system/dns-configuration` and `/v1/system/ntp-configuration` carry `deprecated: true` in
> `SPEC9.1` — they are part of the documented *"21 APIs deprecated … edge cluster operations,
> domain overlays, and system DNS/NTP configurations"* [D9.1 §4]. They still respond; do not build
> on them.

**9.0 difference — this flips completely.** In 9.0 the system-level DNS/NTP operations are
**active and are the only surface**, and **none** of `dnsServers`, `ntpServers` or
`dnsNtpUpdateSpec` exists on any 9.0 topology schema. A 9.1 domain-creation body carrying
`dnsServers` will not do what you expect on 9.0.

### P8 — Licensing state permits the operation `[9.1]`

**Must be true:** hosts joining a cluster are licensed, or the operation is explicitly unlicensed.
`HostSpec.licenseKey` is documented as *"required except in cases where the ESXi host has already
been licensed outside of the VMware Cloud Foundation system"*;
`deployWithoutLicenseKeys` on `ClusterCreationSpec` / `ClusterExpansionSpec` /
`DomainCreationSpec` is the opt-out.

**How to verify:** `GET /v1/license-keys` (**spec-confirmed (9.1)**) plus the license-server view.

**9.0 difference:** the API fields are identical. What changed is where licenses live — 9.1 moves
them out of VCF Operations into a new **required License server** component, with automatic
license-file download every 24 hours and override licenses for individual assets (ESX hosts, vSAN
clusters) [D9.1 §3.5, §6].

### P9 — A clusterless domain cannot be patched or upgraded `[9.1]` — 9.1-only trap

**Must be true:** if you use the 9.1 workflow that deploys a domain's vCenter and NSX Manager
**without an initial cluster**, you must add a cluster before that domain can ever be patched or
upgraded.

**Spec evidence:** `DomainCreationSpec.required` is `["computeSpec", "vcenterSpec"]` in 9.0 and
**`["vcenterSpec"]` alone in 9.1** — the requirement was genuinely dropped. **Doc evidence:**
*"Workload Domain without vSphere Cluster: new workflow deploys vCenter and NSX Manager without an
initial cluster; **patching/upgrades blocked until a cluster is added**"* [D9.1 §3.4, delta #25].

**How to verify:** two steps —
`POST /v1/domains/{domainId}/clusters/queries` (`postClustersQuery`, body: `ClusterCriterion`),
then `GET /v1/domains/{domainId}/clusters/queries/{queryId}` (`getClustersQueryResponse`) for the
result. There is **no GET on the `/queries` collection itself.** Or, in one call,
`GET /v1/clusters?domainId=<id>` — an empty result on a live domain is the condition.

**9.0 difference:** cannot occur. `computeSpec` is required in 9.0, so a 9.0 domain always has at
least one cluster from birth.

### P10 — Caller role and privilege for topology write operations `[9.1]` — UNVERIFIED

**Must be true:** the account behind the bearer token holds whatever role is required for topology
**writes** — `POST|PATCH|DELETE /v1/hosts`, `POST|PATCH|DELETE /v1/domains[/{id}]`,
`POST|PATCH|DELETE /v1/clusters[/{id}]`, and the network-pool mutators.

> **UNVERIFIED. The required SDDC Manager role for these operations is not documented in any
> source consulted; verify before delegating credentials.** 9.1 *does* document VCF-level built-in
> roles — **VCF Administrator, VCF Viewer, SDDC Administrator, SDDC Viewer** — but the published
> role-to-component mapping covers vCenter, NSX, VCF Operations, VCF Automation, HCX and
> Orchestrator, **not SDDC Manager**, which remains outside VCF SSO
> [see `../../../vcf-foundation/references/9.1/auth-and-identity.md`]. `SPEC9.1` declares security
> *schemes* but carries **no per-operation privilege requirement**.
>
> Do not assume "SDDC Administrator" grants `DELETE /v1/domains/{id}` just because the name fits.
> Confirm against Broadcom's role documentation, or empirically against a non-production instance,
> **before** the account is provisioned.

**9.0 difference:** the gap is open in both versions, but worse in 9.0 — no built-in-roles page
exists anywhere in the 9.0 tree, so the 9.1 role names must not be quoted for 9.0 at all.

### P11 — Items the research could not verify — state these as gaps, do not fill them in

- **Enumerated values for `storageType`, `vvolStorageProtocolType` and `Network.type`.** OpenAPI
  `example` strings, **not `enum` constraints**, in both versions.
- **Ports and protocols matrix** for host commissioning and domain deployment — never retrieved.
  The 9.1 prerequisites do say *"verify that all required ports are open"* [D9.1 §5.2], but the
  matrix itself was never fetched.
- **Minimum and maximum host counts per cluster.** `ClusterCompactionSpec.forceByPassingSafeMinSize`
  implies a safe minimum exists; no source states it.
- **The API mechanism for sharing an NSX Manager between domains.** 9.1 advertises *"Sharing NSX
  Managers between Management and Workload Domains"* [D9.1 §3.3], but `DomainCreationSpec.nsxTSpec`
  in `RAW9.1` has no field naming an existing NSX cluster to attach to, and no retrieved page
  describes the workflow. UNVERIFIED.
- **Whether 256 simultaneous cluster upgrades implies any topology-task concurrency figure.** It
  does not, and no topology concurrency limit is documented.
- **The caller role for topology writes** — see P10.

---

## The topology object model

**Private Cloud → Fleet → VCF Instance → Domain (management | workload) → Cluster → Host**
[D9.0 §2.1; unchanged in 9.1].

A **VCF Instance** in 9.1 supports **5000 hosts — explicitly a 2x increase over 9.0** — reported
under the heading *"SDDC Manager Scale"* [D9.1 §3.5]. The 9.0 baseline number was never stated in
any retrieved source; do not assert 2500.

**Which surface does what in 9.1.** The SDDC Manager **UI** deprecation is restated and sharpened
— *"after your upgrade to VCF 9.1 completes, use VCF Operations to perform lifecycle management
activities"* [D9.1 §0.3]. The **API is the topology surface** and it grew. A 9.1-specific removal
to know about: *"All vCLS functionalities available in SDDC Manager UI and VCF Installer UI are
removed"*, and vCLS is *"deactivated by default and you cannot re-activate the capability"*
[D9.1 §4].

---

## The universal pattern: validate → execute → poll

Unchanged from 9.0. Create and update operations are paired with a `validations` sub-resource;
long-running work returns a `Task`.

```
1. POST   <resource>/validations        →  Validation   (has an id)
2. GET    <resource>/validations/{id}   →  poll until executionStatus is terminal
3. POST | PATCH <resource>              →  Task         (has an id)
4. GET    /v1/tasks/{id}                →  poll until status is terminal
```

**Validation terminal states** (`Validation` schema, `RAW9.1`, identical to 9.0):
`executionStatus` ∈ `IN_PROGRESS, FAILED, COMPLETED, UNKNOWN, SKIPPED, CANCELLED,
CANCELLATION_IN_PROGRESS`; then read `resultStatus` ∈ `SUCCEEDED, FAILED, WARNING, UNKNOWN,
CANCELLATION_IN_PROGRESS`. `COMPLETED` with `resultStatus: FAILED` is the common trap. Detail in
`validationChecks[]`.

**Task terminal states** (`Task` schema, `RAW9.1`): `PENDING, IN_PROGRESS, SUCCESSFUL, FAILED,
CANCELLED, COMPLETED_WITH_WARNING, SKIPPED`, **plus `QUEUED` and `TIMED_OUT`**, each also in mixed
case. **Compare case-insensitively.**

> **9.0 difference:** `QUEUED` and `TIMED_OUT` are **not** in the 9.0 `Task.status` example. A
> poller written against 9.0 with a closed state list will treat a 9.1 `QUEUED` task as unknown
> and a `TIMED_OUT` task as still running. Fix the poller before the upgrade, not after.

**Task operations**, all **spec-confirmed (9.1)** and unchanged from 9.0 (tag `Tasks`):
`GET /v1/tasks` (`getTasks`), `GET /v1/tasks/{id}` (`getTask`), `PATCH /v1/tasks/{id}`
(`retryTask`), `DELETE /v1/tasks/{id}` (`cancelTask`).

---

## Hosts and the free pool

21 operations, tag `Hosts`. All **spec-confirmed (9.1)**.

```
GET    /v1/hosts                        getHosts
POST   /v1/hosts                        commissionHosts        body: HostCommissionSpec[]   → 202 Task
DELETE /v1/hosts                        decommissionHosts      body: HostDecommissionSpec[] → 202 Task
PATCH  /v1/hosts                        updateHosts            body: HostsUpdateSpec        → 202 Task   [9.1-only]
POST   /v1/hosts/validations            validateHostCommissionSpec  body: HostCommissionSpec[] → 202 Validation
GET    /v1/hosts/validations/{id}       getHostCommissionValidationByID
POST   /v1/hosts/prechecks              postHostsPrechecks_1   multipart: specFile
GET    /v1/hosts/prechecks/{id}         getHostsPrechecksResponse
GET    /v1/hosts/{id}                   getHost
GET    /v1/hosts/{id}/software          getSoftwareInfoForHost                                            [9.1-only]
GET    /v1/hosts/criteria               getCriteria
GET    /v1/hosts/criteria/{name}        getCriterion
GET    /v1/hosts/tags                   getTagsAssignedToHosts
GET|PUT|DELETE /v1/hosts/{id}/tags      getTagsAssignedToHost / assignTagsToHost / removeTagsFromHost
GET    /v1/hosts/{id}/tags/assignable-tags   getAssignableTagForHost
GET    /v1/hosts/{id}/tags/tag-manager       getHostTagManagerUrl
```

**`HostsUpdateSpec`** (**9.1-only**) — required `hostIds[]`, optional `hostsRefreshSpec`
(`forceRefresh: boolean`). This is an **inventory refresh**, not a host reconfiguration. Do not
reach for it to change a host's network pool or storage type.

**Still deprecated in 9.1** (already deprecated in 9.0): `POST /v1/hosts/queries` (`postQuery`),
`GET /v1/hosts/queries/{id}` (`getHostQueryResponse`), `POST /v1/hosts/validations/commissions`
(`validateCommissionHosts`).

**`HostCommissionSpec`** — **required**: `fqdn`, `username`, `password`, `storageType`,
`networkPoolId`. Identical to 9.0. Array body.
**`HostDecommissionSpec`** — required `fqdn`. Array body.

**9.0 difference:** `PATCH /v1/hosts` and `GET /v1/hosts/{id}/software` do not exist in 9.0.

---

## Network pools

13 operations, tag `Network Pools`. All **spec-confirmed (9.1)**.

```
GET    /v1/network-pools                                                getNetworkPool
POST   /v1/network-pools                                                createNetworkPool  body: NetworkPool → 201
GET    /v1/network-pools/{id}                                           getNetworkPoolByID
PATCH  /v1/network-pools/{id}                                           updateNetworkPool  body: NetworkPoolUpdateSpec (name only)
DELETE /v1/network-pools/{id}                                           deleteNetworkPool  only if unused
GET    /v1/network-pools/{id}/networks                                  getNetworksOfNetworkPool
GET    /v1/network-pools/{id}/networks/{networkId}                      getNetworkOfNetworkPool
POST   /v1/network-pools/{id}/networks/{networkId}/ip-pools             addIpPoolToNetworkOfNetworkPool      body: IpPool
DELETE /v1/network-pools/{id}/networks/{networkId}/ip-pools             deleteIpPoolFromNetworkOfNetworkPool body: IpPool
PATCH  /v1/network-pools/{networkPoolId}/networks/{networkId}           updateNetworkOfNetworkPool     body: NetworkUpdateSpec        [9.1-only]
PATCH  /v1/network-pools/{networkPoolId}/networks/{networkId}/ip-pools  updateIpPoolToNetworkOfNetworkPool body: IpPoolUpdateSpec     [9.1-only]
GET    /v1/network-pools/{networkPoolId}/networks/{networkId}/ips       getIpFromNetwork                                              [9.1-only]
PATCH  /v1/network-pools/{networkPoolId}/networks/{networkId}/ips       updateIpsFromNetwork  body: NetworkIpAddressesUpdateSpec      [9.1-only]
```

**The four 9.1-only operations are the biggest functional gain in the topology area.** They make
a network pool editable in place, which 9.0 simply could not do:

- `NetworkUpdateSpec` — `vlan`, `mtu`, `subnet`, `gateway`, all optional. Change a network's
  addressing without recreating the pool.
- `IpPoolUpdateSpec` — `oldIpPool` → `newIpPool`, each an `IpPool` (`start`, `end`). Resize a
  range in place instead of delete-then-add.
- `NetworkIpAddressesUpdateSpec` — `freeIps[]`, `usedIps[]`. Mark individual addresses free or
  used; use `getIpFromNetwork` to read the current assignment first.

**`NetworkPool`** requires `name` and `networks[]`. Each `Network` requires `type`, `vlanId`,
`mtu` — and, unlike 9.0, **not** `subnet`, `mask` or `gateway`. 9.1 adds `ipAddressVersion`
(default `IPv4`), `ipAddressAssignmentMode` (default `STATIC`), `freeIpCount` and `usedIpCount`.
`IpPool` requires `start` and `end`; the IPv4 `pattern` constraint that 9.0 carried on those two
fields is **gone in 9.1**, consistent with IPv6 support.

**9.0 difference:** none of the four `PATCH`/`ips` operations exist in 9.0, where
`PATCH /v1/network-pools/{id}` (name only) and the add/delete `ip-pools` pair are the entire
mutation surface.

---

## Workload domains

35 operations, tag `Domains`. All **spec-confirmed (9.1)** unless marked.

**Lifecycle of a domain**

```
GET    /v1/domains                          getDomains   filters: type, name, vcFqdn, vcInstanceId,
                                                          isManagementSsoDomain, pageNumber, pageSize, useCache
PATCH  /v1/domains                          updateDomains  body: DomainsUpdateSpec → 202 Task        [9.1-only]
POST   /v1/domains/validations              validateDomainCreationSpec  body: DomainCreationSpec → 200 Validation
GET    /v1/domains/validations/{id}         domainCreateValidation
POST   /v1/domains                          createDomain                body: DomainCreationSpec → 202 Task
GET    /v1/domains/{id}                     getDomain
POST   /v1/domains/{id}/validations         validateDomainUpdateSpec    body: DomainUpdateSpec → 200 Validation
GET    /v1/domains/{id}/validations/{validationId}   getDomainUpdateValidation
PATCH  /v1/domains/{id}                     updateDomain                body: DomainUpdateSpec → 200 Task
DELETE /v1/domains/{id}                     deleteDomain                → 202 Task  (gated, see below)
```

**Inspection**

```
GET  /v1/domains/capabilities                       getDomainCapabilities
GET  /v1/domains/{id}/capabilities                  getDomainCapabilitiesByDomainId
GET  /v1/domains/{id}/endpoints                     getDomainEndpoints
GET  /v1/domains/{id}/datacenters                   getDomainDatacenters
POST /v1/domains/{domainId}/image-compliance/queries          queryDomainImageCompliance            [9.1-only]
GET  /v1/domains/{domainId}/image-compliance/queries/{queryId} getDomainImageComplianceQueryResponse [9.1-only]
POST /v1/domains/{domainId}/isolation-prechecks     performDomainIsolationPrecheck   body: IsolationSpec
GET  /v1/domains/{domainId}/isolation-prechecks/{precheckId}  getDomainIsolationPrecheckStatus
PATCH /v1/domains/{id}/overlay                      enableOverlayOverManagementNetwork   ** DEPRECATED in 9.1 **
```

**Criteria/query pairs** (unchanged from 9.0): `getClusterCriteria`, `getClusterCriterion`,
`postClustersQuery`, `getClustersQueryResponse`, `postClusterQuery`, `getClusterQueryResponse`,
and the four `datastores` equivalents (`getDatastoresCriteria`, `getDatastoreCriterion`,
`postDatastoreQuery`, `getDatastoreQueryResponse`).

**Tags** (unchanged): `getTagsAssignedToDomains`, `getTagsAssignedToDomain`, `assignTagsToDomain`,
`removeTagsFromDomain`, `getAssignableTagsForDomain`, `getDomainTagManagerUrl`.

**`DomainCreationSpec`** (`RAW9.1`) — **required: `vcenterSpec` only.** Optional: `computeSpec`,
`domainName`, `orgName`, `nsxTSpec`, `ssoDomainSpec`, `securitySpec`, `existingDatastoreName`,
`deployWithoutLicenseKeys`, and **9.1-only** `dnsServers[]`, `ntpServers[]`.

> **`computeSpec` moved from required to optional.** That is the API face of the *"Workload Domain
> without vSphere Cluster"* workflow — and of the trap in P9: **patching and upgrades are blocked
> until a cluster is added** [D9.1 §3.4].

**`DomainUpdateSpec`** (`RAW9.1`) — all optional: `clusterSpec`, `nsxTSpec`, `name`,
`markForDeletion`, `isolationSpec`, and **9.1-only** `dnsNtpUpdateSpec`, `acknowledgmentSpec`
(`ackThatOfflineBackupsTaken: boolean`), `transitionSpec`, `imageComplianceCheckSpec`.

**`DomainsUpdateSpec`** (**9.1-only**) — required `domainIds[]`, optional `domainsRefreshSpec`
(`forceRefresh`). An inventory refresh, not a reconfiguration.

**9.0 difference:** `PATCH /v1/domains`, the image-compliance query pair, and the four new
`DomainUpdateSpec` sub-specs do not exist in 9.0. `PATCH /v1/domains/{id}/overlay` is **active in
9.0 and deprecated in 9.1**.

---

## Clusters

38 operations, tag `Clusters`. All **spec-confirmed (9.1)** unless marked.

**Lifecycle of a cluster**

```
GET    /v1/clusters                              getClusters   filters: domainId, isStretched, isImageBased,
                                                                name, managedObjectReferenceId, isDefault,
                                                                isHciMeshEnabled, pageNumber, pageSize, useCache
PATCH  /v1/clusters                              updateClusters  body: ClustersUpdateSpec → 202 Task     [9.1-only]
POST   /v1/clusters/validations                  validateClusterCreationSpec  body: ClusterCreationSpec → 200 Validation
GET    /v1/clusters/validations/{id}             getClusterCreateValidation
POST   /v1/clusters                              createCluster                body: ClusterCreationSpec → 202 Task
GET    /v1/clusters/{id}                         getCluster
POST   /v1/clusters/{id}/validations             validateClusterUpdateSpec    body: ClusterUpdateSpec → 200 Validation
GET    /v1/clusters/{id}/validations/{validationId}   getClusterUpdateValidation
PATCH  /v1/clusters/{id}                         updateCluster                body: ClusterUpdateSpec → 200 Task
DELETE /v1/clusters/{id}                         deleteCluster                → 202 Task  (gated, see below)
```

`PATCH /v1/clusters/{id}` remains the single door for several operations, selected by which field
of `ClusterUpdateSpec` you populate: *"Update a Cluster by adding or removing Hosts, Stretching a
standard vSAN cluster, Unstretching a stretched cluster or by marking for deletion."*

| Intent | Field of `ClusterUpdateSpec` |
|---|---|
| Add hosts (expand) | `clusterExpansionSpec` |
| Remove hosts (contract) | `clusterCompactionSpec` |
| Stretch a standard vSAN cluster | `clusterStretchSpec` (and `prepareForStretch` beforehand) |
| Un-stretch a stretched cluster | `clusterUnstretchSpec` |
| Arm deletion | `markForDeletion: true` |
| Rename | `name` |
| Transition to vLCM images | `clusterTransitionSpec` |
| Pre-transition compliance check | `clusterImageComplianceCheckSpec` |
| Change the primary datastore | `clusterPrimaryDatastoreUpdateSpec` **[9.1-only]** |
| Set DNS/NTP | `dnsNtpUpdateSpec` **[9.1-only]** |
| Mark as the domain's default cluster | `markAsDefault` **[9.1-only]** |

**`ClusterCreationSpec`** — required `domainId`, `computeSpec`; **9.1-only** optional
`dnsServers[]`, `ntpServers[]`. Each `ClusterSpec` requires `hostSpecs[]`, `datastoreSpec`,
`networkSpec`, and in practice `clusterImageId` (P6); **9.1-only** optional
`hostIdForHostSeeding`.

**`ClusterExpansionSpec`** — **identical properties and required fields to 9.0**: required
`hostSpecs[]`; optional `networkSpec`, `vsanNetworkSpecs[]`, `witnessSpec`,
`witnessTrafficSharedWithVsanTraffic`, `deployWithoutLicenseKeys`, `interRackExpansion`
(*"Required, only if Cluster contains NSX Edge Cluster"*). `forceHostAdditionInPresenceofDeadHosts`
and `skipThumbprintValidation` are deprecated in both versions; the former is documented as having
*"no effect."*

**`ClusterCompactionSpec`** — required `hosts[]` of `HostReference`; optional `force` and
`forceByPassingSafeMinSize` (*"Forced removal may result in permanent data loss. Review recovery
plan with VMware Support before using."*). Identical to 9.0.

**`ClustersUpdateSpec`** (**9.1-only**) — required `clusterIds[]`, optional `clustersRefreshSpec`
(`forceRefresh`). Inventory refresh.

**`ClusterPrimaryDatastoreUpdateSpec`** (**9.1-only**) — required `datastoreId`. Changes which
datastore is primary for an existing cluster.

**Storage attached to a cluster**

```
GET    /v1/clusters/{id}/datastores                    getClusterDatastores
POST   /v1/clusters/{id}/datastores                    addDatastoreToCluster    body: DatastoreMountSpec → 202 Task
DELETE /v1/clusters/{id}/datastores/{datastoreId}      removeDatastoreFromCluster → 202 Task
POST   /v1/clusters/{clusterId}/datastores/validations validateVsanRemoteDatastoreMountSpec
GET    /v1/clusters/{id}/datastores/validations/{validationId}  getDatastoreMountValidation   [9.1-only]
GET|POST /v1/clusters/{id}/datastores/criteria|queries getDatastoresCriteria_1 / postDatastoreQuery_1
GET    /v1/clusters/{clusterId}/datastores/queries/{queryId}  getDatastoreQueryResponse_1
```

`POST /v1/clusters/{clusterId}/datastores/validation` (singular,
`validateVsanRemoteDatastoreSpec`) is deprecated in both versions.

> **9.0 gap worth noting:** 9.0 has the datastore-mount **validation POST** but **no** matching
> `GET .../datastores/validations/{validationId}` to poll it. 9.1 adds it
> (`getDatastoreMountValidation`), which is the first version where that particular
> validate-then-poll loop is actually closeable through a dedicated endpoint.

**Networking attached to a cluster** (unchanged from 9.0): `getVdses`, `importVdsToInventory`,
`getClusterNetworkConfigurationCriteria`, `getClusterNetworkConfiguration`,
`getClusterNetworkConfigurationQueryResponse`.

**Out-of-band remediation** — **9.1-only**:

```
POST /v1/clusters/{clusterId}/remediations                    triggerRemediation   body: ClusterRemediationCriterion
GET  /v1/clusters/{clusterId}/remediations/{remediationId}    getRemediationById
```

`ClusterRemediationCriterion` requires `name`, and the schema states *"currently, the only
supported value is `SDDC_NETWORKING_DATA_REMEDIATION`."* This is the API behind *"Out-of-band
networking changes to not impact SDDC Manager"* [D9.1 §3.3, §3.4].

**Images and tags** (unchanged): `getClusterImageCompliance`, `getTagsAssignedToClusters`,
`getTagsAssignedToCluster`, `assignTagsToCluster`, `removeTagsFromCluster`,
`getTagAssignableForCluster`, `getClusterTagManagerUrl`.

**Still deprecated in 9.1** (already deprecated in 9.0): `GET /v1/clusters/{id}/hosts/criteria`,
`GET /v1/clusters/{id}/hosts/criteria/{name}`, `POST /v1/clusters/{id}/hosts/queries`,
`GET /v1/clusters/{clusterId}/hosts/queries/{queryId}`, and the singular datastore `validation`.

**9.0 difference:** `PATCH /v1/clusters`, the `remediations` pair,
`GET /v1/clusters/{id}/datastores/validations/{validationId}`, and the three new
`ClusterUpdateSpec` fields do not exist in 9.0.

---

## vCenter, NSX, ALB, HCX and PSC association

**vCenter** — `GET /v1/vcenters` (`getVcenters`), `GET /v1/vcenters/{id}` (`getVcenter`), plus
**9.1-only** `PATCH /v1/vcenters/{vcenterId}/fqdn` (`updateVcenterFqdn`, tag `UpdateVcenterFqdn`)
— the first API-level way to change a managed vCenter's FQDN. **Does not exist in 9.0.**

**PSC** — read-only: `GET /v1/pscs` (`getPscs`), `GET /v1/pscs/{id}` (`getPsc`).

**NSX** — 18 operations, tag `NSX-T Clusters`. The 16 from 9.0 are all present
(`getNsxClusters`, `getNsxCluster`, `getNsxCriteria`, `getNsxCriterion`, `startNsxCriteriaQuery`,
`getNsxClusterQueryResponse`, `scaleOutNsx`, `getNsxTransportZones`, `getNsxIpAddressPools`,
`getNsxIpAddressPool`, `validateIpPool`, `getValidationResult`, `connectOpenId`,
`getVpcConfiguration`, `getProjects`, `getVpcConnectivityProfiles`), plus **9.1-only**
`GET /v1/nsxt-clusters/{nsxtClusterId}/projects/{projectId}` (`getProject`) and
`GET /v1/nsxt-clusters/{nsxtClusterId}/projects/{projectId}/vpc-connectivity-profiles/{vpcConnectivityProfileId}`
(`getVpcConnectivityProfile`) — single-item reads to match the existing list reads.

`NsxTSpec` requires `nsxManagerSpecs[]` and `vipFqdn`; 9.1 adds an optional `vnaSpec` (Virtual
Network Appliance, *"Introduction of Virtual Network Appliance in VCF 9.1"* [D9.1 §3.3]).
`ipAddressPoolSpec` is deprecated in both versions.

**NSX Edge clusters** — 8 operations, tag `NsxTEdgeClusters`. **All eight are deprecated in 9.1**
(`getEdgeClusters`, `createEdgeCluster`, `validateEdgeClusterCreationSpec`,
`getEdgeClusterValidationByID`, `getEdgeClusterQueryCriteria`, `getEdgeCluster`,
`updateEdgeCluster`, `validateEdgeClusterUpdateSpec`) — part of the documented *"21 APIs
deprecated"* [D9.1 §4]. They still respond. Do not build new automation on them; ask what the
replacement surface is before committing, because the research did not identify one.

**9.0 difference:** the same eight operations are **active, not deprecated,** in 9.0.

**NSX ALB / Avi** — 15 operations, tag `ALBClusters`, of which **7 remain deprecated** (the
`/v1/nsx-alb-clusters` family, deprecated already in 9.0). Use `/v1/alb-clusters`:
`getAviLBClusters`, `deployALBCluster`, `getAviLBCluster`, `undeployALBCluster`,
`validateALBControllerClusterCreationSpec`, `validateALBCompatibility`,
`getALBClustersFormFactors_1`, `getClusterCapacityForALBDeployment`.

**HCX Manager — 6 operations, tag `HcxManagers`, entirely 9.1-only:**

```
GET    /v1/domains/{domainId}/hcx-managers                          getHcxManagersByDomainId
POST   /v1/domains/{domainId}/hcx-managers                          deployOrImportHcxManager  body: HcxManagerDeploymentSpec → 202 Task
POST   /v1/domains/{domainId}/hcx-managers/validations              validateHcxManagerDeploymentOrImport → 202 Validation
GET    /v1/domains/{domainId}/hcx-managers/validations/{validationId} getHcxManagerDeploymentOrImportValidation
GET    /v1/domains/{domainId}/hcx-managers/versions                 getCompatibleHcxManagersVersionForDomain
DELETE /v1/domains/{domainId}/hcx-managers/{hcxManagerId}           undeployHcxManager
```

Same validate → execute → poll shape. **None of these exist in 9.0** — HCX is in the 9.0 BOM but
has no SDDC Manager API family and no lifecycle through VCF Operations [D9.1 §3.5].

---

## Brownfield import, drift and remediation

**Import an existing vCenter as a workload domain** — 10 operations, tag `BrownfieldImport`, all
**spec-confirmed (9.1)**:

```
POST /v1/sddcs/imports/validations                                       validation
GET  /v1/sddcs/imports/validations/{taskId}                              getBrownfieldCheckTaskById
GET  /v1/sddcs/imports/validations/{taskId}/report                       exportValidationsAsCsv                [9.1-only]
GET  /v1/sddcs/imports/validations/{taskId}/validation-groups            getBrownfieldValidationGroupTaskById  [9.1-only]
GET  /v1/sddcs/imports/validations/{taskId}/validation-groups/{validationGroupId}  retrieveResultsFromValidationGroup [9.1-only]
POST /v1/sddcs/imports                                                   import
GET  /v1/sddcs/imports/{taskId}                                          getBrownfieldImportTaskById
POST /v1/domains/{domainId}/synchronizations                             synchronization   body: BrownfieldSyncSpec
GET  /v1/domains/{domainId}/synchronizations/{taskId}                    getBrownfieldSyncTaskById
POST /v1/domains/{domainId}/synchronizations/ssh-known-hosts             syncSshKnownHosts                     [9.1-only]
```

These use their own `BrownfieldTask` poller, not `/v1/tasks/{id}`. The four 9.1-only additions are
the API face of *"revamped UI and API for brownfield imports and prechecks"* [D9.1 §3.5]; the
validation-group tree and CSV export make a large import's results actually readable.

9.1 import sources documented: existing vCenter 8.0 U2a+ with NSX Manager 4.1.2.1+; vCenter 8.0
U2a without NSX (requires manual vCenter upgrade to 9.1); vCenter with existing NSX Federation;
dual-stack IPv4/IPv6 environments [D9.1 §3.4].

**Configuration drift** (unchanged from 9.0): `GET /v1/config-drifts` (`getConfigs`),
`POST /v1/config-drift-reconciliations` (`reconcileConfigs`),
`GET /v1/config-drift-reconciliations/{taskId}` (`getReconciliationTask`).

**vSAN health per domain** (unchanged from 9.0): `getVsanHealthCheckByDomain`,
`updateVsanHealthCheckByDomain`, `getVsanHealthCheckByTaskID`, `getVsanHealthCheckByQueryID`.

**Version drift** — **9.1-only**: `GET /v1/version-drift` (`getComponentVersionDrift`, tag
`ComponentVersions`) backs the *"Component Versions tab shows current and target versions"*
feature [D9.1 §3.5]. It is a *lifecycle* read, not a topology one — route detailed questions about
it to `vcf-lifecycle-upgrade`.

---

## Worked example — expand an existing cluster by two hosts

Adds two already-racked ESX hosts to an existing vSAN cluster. Every path and field is
**spec-confirmed (9.1)** / drawn from `RAW9.1` schemas. Values are placeholders.

**Step 0 — find the network pool and the target cluster.** Use a live read, not the cache.

```http
GET /v1/network-pools                                     → getNetworkPool
GET /v1/clusters?domainId=<domain-id>&useCache=false      → getClusters
```

**Step 1 — validate the commission spec.** Body is an **array** of `HostCommissionSpec`.

```http
POST /v1/hosts/validations
Authorization: Bearer <accessToken>
Content-Type: application/json

[
  { "fqdn": "esx-11.rainpole.io", "username": "root", "password": "<pw>",
    "storageType": "VSAN", "networkPoolId": "5b7b4a2c-…", "sshThumbprint": "SHA256:…" },
  { "fqdn": "esx-12.rainpole.io", "username": "root", "password": "<pw>",
    "storageType": "VSAN", "networkPoolId": "5b7b4a2c-…", "sshThumbprint": "SHA256:…" }
]
```

→ `202` with a `Validation`. Poll `GET /v1/hosts/validations/{id}`
(`getHostCommissionValidationByID`) until `executionStatus` is terminal, then **check
`resultStatus == "SUCCEEDED"`**. Detail is in `validationChecks[]`.

**Step 2 — commission.** Same array body.

```http
POST /v1/hosts                               → commissionHosts, 202 Task
GET  /v1/tasks/{id}                      → poll to SUCCESSFUL
```

**Step 3 — confirm the hosts landed in the free pool and capture their IDs.**

```http
GET /v1/hosts?status=UNASSIGNED_USEABLE&pageSize=100   → getHosts
```

Use `pageSize`/`pageNumber` here — `size`/`page` still work but are deprecated in the 9.1 spec.
`HostSpec.id` for the expansion is the `id` returned here, not the FQDN.

**Step 3b — resolve the two pre-existing network objects the payload names.** `vdsName` and
`networkProfileName` below are **not values you invent** — they must match objects the cluster
already has, exactly as `hostSpecs[].id` must match a real free-pool host. Read them, do not type
them.

```http
GET  /v1/clusters/{clusterId}/vdses                     → getVdses
```

Returns `Vds` objects; take `name`. `VmNic` **requires** both `id` and `vdsName`, and the schema
states *"VDS name must match the cluster's VDS name"* — a mismatch is a validation failure at step
4, not a runtime surprise. `sfo-w01-cl01-vds01` in the payload is a placeholder for whatever this
call returns.

```http
POST /v1/clusters/{id}/network/queries                  → getClusterNetworkConfiguration
GET  /v1/clusters/{id}/network/queries/{queryId}        → getClusterNetworkConfigurationQueryResponse
```

Body is a `ClusterNetworkConfigurationCriterion`; the criterion names available for this cluster
come from `GET /v1/clusters/{id}/network/criteria` (`getClusterNetworkConfigurationCriteria`).
The `ClusterNetworkConfiguration` result carries **`networkProfiles[]`** alongside
`vdsConfigurations[]`, `uplinkProfiles[]` and `ipAddressPools[]` — `NetworkProfile.name` is the
value `hostNetworkSpec.networkProfileName` must equal. `np-vsan-01` below is likewise a
placeholder. All five operations **spec-confirmed (9.1)**.

> If the cluster has no matching network profile, you are not expanding into an existing
> configuration — you need `clusterExpansionSpec.networkSpec` (which itself requires
> `nsxClusterSpec` **and** `networkProfiles[]`), described in the field notes after step 4.

**Step 4 — validate the expansion.** `ClusterUpdateSpec` with only `clusterExpansionSpec` set.

```http
POST /v1/clusters/{id}/validations
Content-Type: application/json

{
  "clusterExpansionSpec": {
    "hostSpecs": [
      { "id": "<host-id-11>", "licenseKey": "<esx-key>", "hostName": "esx-11.rainpole.io",
        "sshThumbprint": "SHA256:…",
        "hostNetworkSpec": {
          "networkProfileName": "np-vsan-01",
          "vmNics": [ { "id": "vmnic0", "vdsName": "sfo-w01-cl01-vds01", "uplink": "uplink1" },
                      { "id": "vmnic1", "vdsName": "sfo-w01-cl01-vds01", "uplink": "uplink2" } ]
        } },
      { "id": "<host-id-12>", "licenseKey": "<esx-key>", "hostName": "esx-12.rainpole.io",
        "sshThumbprint": "SHA256:…",
        "hostNetworkSpec": { "networkProfileName": "np-vsan-01",
          "vmNics": [ { "id": "vmnic0", "vdsName": "sfo-w01-cl01-vds01", "uplink": "uplink1" },
                      { "id": "vmnic1", "vdsName": "sfo-w01-cl01-vds01", "uplink": "uplink2" } ] } }
    ]
  }
}
```

→ `200 Validation`. Poll `GET /v1/clusters/{id}/validations/{validationId}`
(`getClusterUpdateValidation`) and check **both** `executionStatus` and `resultStatus`.

Field notes, all from `RAW9.1`:
- `hostSpecs[].id` — **required**, the free-pool host ID.
- `hostSpecs[].licenseKey` — *"required except in cases where the ESXi host has already been
  licensed outside of the VMware Cloud Foundation system."* Set
  `clusterExpansionSpec.deployWithoutLicenseKeys: true` to run unlicensed deliberately.
- `hostSpecs[].sshThumbprint` — optional, but the schema warns *"this field will be mandatory in
  future releases."* Populate it.
- `hostSpecs[].ipAddress` — **deprecated**; use `hostName`.
- `hostSpecs[].azName` — required only when expanding a **stretched** cluster.
- `clusterExpansionSpec.interRackExpansion` — *"Required, only if Cluster contains NSX Edge
  Cluster."*
- `clusterExpansionSpec.networkSpec` — needed when the new hosts require NSX uplink profiles or IP
  pools the cluster does not already carry; when present it requires `nsxClusterSpec` **and**
  `networkProfiles[]`.

**Step 5 — execute.** Identical body, `PATCH` to the cluster.

```http
PATCH /v1/clusters/{id}               → updateCluster, 200 Task
```

**Step 6 — poll to completion.**

```http
GET /v1/tasks/{id}                       → getTask
```

Terminal when `status` (case-insensitively) is `SUCCESSFUL`, `FAILED`, `CANCELLED`,
`COMPLETED_WITH_WARNING`, `SKIPPED` or — **new in 9.1** — `TIMED_OUT`. `QUEUED` is **not**
terminal; it is a 9.1 pre-`IN_PROGRESS` state. On failure read `errors[]` and `subTasks[]`;
`PATCH /v1/tasks/{id}` (`retryTask`) retries. Confirm with `GET /v1/clusters/{id}` —
`status` back to `ACTIVE`, not `EXPANDING`.

**9.0 note:** this sequence is byte-for-byte portable to 9.0 — `ClusterExpansionSpec` and
`HostSpec` are identical in both versions. The three things to change going backwards: drop
`useCache`, use `size`/`page` instead of `pageSize`/`pageNumber` on `getHosts`, and remove
`QUEUED`/`TIMED_OUT` from the poller's state handling.

---

## Destructive operations and their gates

Confirm before executing. These are not reversible by re-running them.

**Cluster deletion is two-phase.** `DELETE /v1/clusters/{id}` — *"Delete a cluster from a domain
**if it has been previously initialized for deletion**."* Arm first:

```
PATCH  /v1/clusters/{id}   { "markForDeletion": true }   → updateCluster
DELETE /v1/clusters/{id}                                 → deleteCluster, 202 Task
```

**Domain deletion is the same shape.** `DELETE /v1/domains/{id}` — *"Remove a domain **if it has
been previously initialized for deletion**."* Arm with
`PATCH /v1/domains/{id} { "markForDeletion": true }`. Deleting a domain destroys its vCenter and
its NSX Manager.

> **9.1-only:** `DomainUpdateSpec.acknowledgmentSpec.ackThatOfflineBackupsTaken` exists — *"set to
> true, to acknowledge offline backups are taken."* Its presence is spec-confirmed; **which
> operations require it is not documented in any source consulted (UNVERIFIED).** If a domain
> update is rejected for a missing acknowledgment, this is the field. Do not set it reflexively —
> it is an assertion that backups exist.

**Host decommissioning** — `DELETE /v1/hosts` with a `HostDecommissionSpec[]` body. Remove hosts
from their cluster first via `clusterCompactionSpec`.

**The two force flags are the dangerous ones.**
`ClusterCompactionSpec.forceByPassingSafeMinSize` — *"Remove dead hosts from cluster, bypassing
validations. Forced removal may result in permanent data loss. Review recovery plan with VMware
Support before using."* `ClusterCompactionSpec.force` forces removal of a host. Neither belongs in
a runbook without an explicit, named decision.

**HCX undeploy** — `DELETE /v1/domains/{domainId}/hcx-managers/{hcxManagerId}`
(`undeployHcxManager`) has **no `markForDeletion` gate**. It is a direct destructive call. 9.1-only.

**Network pool deletion** — `DELETE /v1/network-pools/{id}` succeeds *"if it exists and is
unused."* Check `NetworkPool.hostsCount` and `GET /v1/hosts?networkpoolId=<id>` first.

**Everything destructive here is asynchronous.** The `202` means *accepted*, not *done*. Poll
`/v1/tasks/{id}` before reporting success.

---

## Discrepancies and UNVERIFIED items

1. **`storageType`, `vvolStorageProtocolType` and `Network.type` have no `enum`** in either
   version — `example` strings only. Any value list you pass on is copied from an example, not a
   constraint. Say so.
2. **Spec base path.** `SPEC9.1` declares a placeholder server, as `SPEC9.0` does. The real base is
   `https://<sddc-manager-fqdn>` with `/v1` in the path.
3. **`acknowledgmentSpec` trigger conditions are undocumented.** The field exists in `RAW9.1`;
   which `PATCH /v1/domains/{id}` operations demand it is UNVERIFIED.
4. **No replacement is documented for the deprecated `/v1/edge-clusters` family.** All eight
   operations are deprecated in `SPEC9.1`, and the 9.1 release notes confirm *"edge cluster
   operations"* among the 21 deprecations [D9.1 §4] — but no retrieved source names a successor
   API. If someone needs to create an NSX Edge cluster on 9.1 programmatically, the deprecated
   `POST /v1/edge-clusters` is still the only SDDC Manager path in the spec. Flag that, do not
   invent an alternative.
5. **`PATCH /v1/domains/{id}/overlay` is deprecated in 9.1** with no documented replacement either.
6. **`ClusterExpansionSpec.forceHostAdditionInPresenceofDeadHosts`** is deprecated **and**
   documented as having *"no effect when using it"* — in both versions.
7. **`ClusterRemediationCriterion` supports exactly one value.** The schema says *"currently, the
   only supported value is `SDDC_NETWORKING_DATA_REMEDIATION`."* The remediation API is real but
   narrow; it does not remediate arbitrary out-of-band drift.
8. **The NSX-Manager-sharing workflow has no visible API.** 9.1 advertises *"Sharing NSX Managers
   between Management and Workload Domains"* [D9.1 §3.3]; `RAW9.1`'s `NsxTSpec` has no field
   naming an existing NSX cluster to reuse. UNVERIFIED.
9. **Domain deletion side-effects are not enumerated** in either version — whether the hosts of a
   deleted domain return to the free pool or must be re-commissioned is undocumented. UNVERIFIED.
10. **Topology-task concurrency limits are undocumented.** The 9.1 figure of *256 simultaneous
    cluster upgrades* [D9.1 §3.5] is an upgrade figure and must not be reused as a topology-task
    limit.
11. **Stretched-cluster procedure is UNVERIFIED.** The fields (`clusterStretchSpec`,
    `witnessSpec` with `vsanIp`/`fqdn`/`vsanCidr`, `prepareForStretch`, `clusterUnstretchSpec`)
    are spec-confirmed in both versions; the ordering, witness-host commissioning requirements and
    availability-zone prerequisites were not retrieved from any documentation source.
