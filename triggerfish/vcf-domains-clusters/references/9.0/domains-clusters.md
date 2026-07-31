# VCF 9.0 — Workload Domains, Clusters, Hosts and Network Pools

**Scope:** topology management on VMware Cloud Foundation 9.0.x through the **SDDC Manager API**
(`https://<sddc-manager-fqdn>/v1`). Everything here is `[9.0]` unless explicitly tagged otherwise.
Upgrades and patching are **not** in scope — use the `vcf-lifecycle-upgrade` skill for those.

**Sources.**
`D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of git tags
`9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`).
`SPEC9.0` = `research/spec-inventory/9.0__sddc-manager.ops.json` — 375 operations, spec version
`9.0.0.0`, extracted from git tag `9.0.0.0`.
`RAW9.0` = `specifications/sddc-manager/sddc-manager-openapi.json` at git tag `9.0.0.0`, used for
request/response **schemas**. (The task brief pointed at a `/tmp/vcf-specs-90` checkout that was
not present in this environment; the file was read directly out of the `9.0.0.0` tag instead —
same artifact, same commit.)

**Verification rule.** Every path below was checked against `SPEC9.0` and is marked
**spec-confirmed (9.0)** with its `operationId`. Nothing is carried backwards from 9.1. Where 9.1
has something 9.0 does not, it is labeled **9.1-only** and cross-referenced, never listed as a
9.0 endpoint.

**Auth is out of scope here.** Obtaining and refreshing the SDDC Manager bearer token is the
`vcf-foundation` skill's job. This file assumes you already have one.

**Endpoint count.** 128 operations across the nine topology tags (`Domains` 32, `Clusters` 34,
`Hosts` 19, `NSX-T Clusters` 16, `Network Pools` 9, `NsxTEdgeClusters` 8, `BrownfieldImport` 6,
`PSCs` 2, `vCenters` 2), plus 26 supporting operations (`ALBClusters` 15, `vSANHealthCheck` 4,
`Tasks` 4, `ConfigReconciler` 3). All counted from `SPEC9.0`.

---

## Contents

- [Prerequisites](#prerequisites)
  - P1 — A valid SDDC Manager bearer token
  - P2 — Hosts are commissioned and sitting in the free pool
  - P3 — A network pool exists and carries the network types the cluster needs
  - P4 — Host storage type matches the cluster's datastore type
  - P5 — The target domain and cluster are in a stable state
  - P6 — A vLCM cluster image is chosen — mandatory on vCenter 9.0+
  - P7 — System DNS and NTP are configured
  - P8 — Licensing state permits the operation
  - P9 — Caller role and privilege — UNVERIFIED
  - P10 — Items the research could not verify
- [The topology object model](#the-topology-object-model)
- [The universal pattern: validate → execute → poll](#the-universal-pattern-validate--execute--poll)
- [Hosts and the free pool](#hosts-and-the-free-pool)
- [Network pools](#network-pools)
- [Workload domains](#workload-domains)
- [Clusters](#clusters)
- [vCenter, NSX, ALB and PSC association](#vcenter-nsx-alb-and-psc-association)
- [Brownfield import and configuration drift](#brownfield-import-and-configuration-drift)
- [Worked example — expand an existing cluster by two hosts](#worked-example--expand-an-existing-cluster-by-two-hosts)
- [Destructive operations and their gates](#destructive-operations-and-their-gates)
- [Discrepancies and UNVERIFIED items](#discrepancies-and-unverified-items)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what must
hold, **how to verify it**, the version it applies to, and whether 9.1 differs.

### P1 — A valid SDDC Manager bearer token `[9.0]`

**Must be true:** you hold an SDDC Manager access token and send it as
`Authorization: Bearer <accessToken>`. SDDC Manager is excluded from VCF SSO in both 9.0 and 9.1
and uses its own token flow.

**How to verify:** `GET /v1/domains` (`getDomains`, **spec-confirmed (9.0)**) returns `200` with a
`PageOfDomain`. A `401` means the token is absent, wrong-typed or expired.

**Do not restate the auth flow from here.** Route to the `vcf-foundation` skill — it owns token
acquisition, refresh, lifetimes and the identity-broker distinction.

**9.1 difference:** none for SDDC Manager itself. `vcf-foundation` covers the VIDB/OAuth changes
that apply to the *other* components.

### P2 — Hosts are commissioned and sitting in the free pool `[9.0]`

**Must be true:** every host you intend to place in a cluster must already be **commissioned** and
in an unassigned, usable state. `HostSpec.id` is documented in `RAW9.0` as *"ID of a vSphere host
in the free pool"* — a cluster create or expand consumes hosts that are already in inventory. You
cannot hand `POST /v1/clusters` an uncommissioned FQDN.

**How to verify:** `GET /v1/hosts?status=UNASSIGNED_USEABLE` (`getHosts`,
**spec-confirmed (9.0)**). The `status` query parameter documents
`ASSIGNED, UNASSIGNED_USEABLE`; the `Host.status` schema example additionally lists
`UNASSIGNED_UNUSEABLE`. A host in `UNASSIGNED_UNUSEABLE` is in inventory but not consumable —
treat it as a blocker, not a candidate.

**To get hosts there:** `POST /v1/hosts` (`commissionHosts`, **spec-confirmed (9.0)**) with a JSON
**array** of `HostCommissionSpec`. Required fields (from `RAW9.0`): `fqdn`, `username`, `password`,
`storageType`, `networkPoolId`.

**9.1 difference:** identical path, identical `HostCommissionSpec` required-field set. 9.1 adds
filter parameters (`isStandalone`, `isLifecycleManaged`, `isVsanWitnessHost`,
`ipAddressVersionForVmotion`) and `pageSize`/`pageNumber` to `getHosts` — see
`../9.1/domains-clusters.md`.

### P3 — A network pool exists and carries the network types the cluster needs `[9.0]`

**Must be true:** `HostCommissionSpec.networkPoolId` is **required**, so a network pool must exist
*before* the first host is commissioned. The pool supplies the vMotion/vSAN/NFS/etc. IP ranges the
host will consume.

**How to verify:** `GET /v1/network-pools` (`getNetworkPool`) and
`GET /v1/network-pools/{id}/networks` (`getNetworksOfNetworkPool`) — both
**spec-confirmed (9.0)**. Check that each required `Network` has free IPs: the `Network` schema
carries `freeIps` and `usedIps` arrays.

**To create one:** `POST /v1/network-pools` (`createNetworkPool`, **spec-confirmed (9.0)**), body
= `NetworkPool`. Required: `name`, `networks[]`. Each `Network` requires `type`, `vlanId`, `mtu`,
`subnet`, `mask`, `gateway`. The `Network.type` schema example gives
`VSAN, VMOTION, VXLAN, NFS, ISCSI, VSAN_EXTERNAL` — this is an **example string, not an `enum`**;
see P10.

**9.1 difference:** `subnet`, `mask` and `gateway` are **no longer required** on `Network` in 9.1,
and `ipAddressVersion` / `ipAddressAssignmentMode` are added (dual-stack). 9.1 also adds four
mutating network-pool operations that do not exist in 9.0.

### P4 — Host storage type matches the cluster's datastore type `[9.0]`

**Must be true:** the `storageType` a host was commissioned with must be consistent with the
`DatastoreSpec` of the cluster it joins. A vSAN cluster needs vSAN-commissioned hosts.

**How to verify:** `GET /v1/hosts?storageType=…` (`getHosts`); the parameter description documents
`VSAN, VSAN_ESA, VSAN_REMOTE` as filterable values. The broader set appears only as a schema
**example** on `HostCommissionSpec.storageType`:
`VSAN, VSAN_ESA, VSAN_REMOTE, VSAN_MAX, NFS, VMFS_FC, VVOL, VMFS`. For `VVOL`,
`vvolStorageProtocolType` is documented with example values `ISCSI, NFS, FC`.

**9.1 difference:** the 9.1 `storageType` example string is longer —
`VSAN, VSAN_ESA, VSAN_REMOTE, VSAN_MAX, NFS, NFS41, VMFS_FC, VVOL, VMFS, FC, VVOL` (note `NFS41`
and `FC`, and that `VVOL` is repeated in the source text). Do not use `NFS41` or a bare `FC`
against 9.0.

### P5 — The target domain and cluster are in a stable state `[9.0]`

**Must be true:** the domain and cluster you are modifying are not already mid-operation. The
`Domain.status` and `Cluster.status` schema examples both give
`ACTIVE, ACTIVATING, UPGRADING, DISABLED, ERROR, SKIPPED, DEACTIVATING, EXPANDING, SHRINKING,
CREATING`. Only `ACTIVE` is a safe starting point for an expansion or contraction.

**How to verify:** `GET /v1/domains/{id}` (`getDomain`) and `GET /v1/clusters/{id}` (`getCluster`),
both **spec-confirmed (9.0)**; plus `GET /v1/tasks?resourceId=<id>` (`getTasks`) to confirm no
in-flight task targets the resource.

**9.1 difference:** same status vocabulary. 9.1 adds `useCache` to `getClusters`/`getDomains`,
which means a cached read can be *stale* — for a pre-flight check pass `useCache=false` or omit it.

### P6 — A vLCM cluster image is chosen — mandatory on vCenter 9.0+ `[9.0]`

**Must be true:** `ClusterSpec.clusterImageId` is documented in `RAW9.0` as *"ID of the Cluster
Image to be used only with the Cluster managed by vSphere Lifecycle Manager Images. This is
required, if we want to create a cluster on vCenter 9.0 or above."* Since 9.0 removes vLCM
baselines and baseline groups from vCenter [D9.0 §9.2], in practice every new 9.0 cluster is
image-managed and needs this ID.

**How to verify:** `GET /v1/personalities` (`getPersonalities`, **spec-confirmed (9.0)**) to list
available cluster images; `GET /v1/clusters/{id}/image-compliance`
(`getClusterImageCompliance`, **spec-confirmed (9.0)**) for an existing cluster's compliance state.

**9.1 difference:** same requirement and same fields. 9.1 adds `ClusterSpec.hostIdForHostSeeding`
(extract the desired image from a nominated UNASSIGNED host) and a domain-wide image-compliance
query pair, neither of which exists in 9.0.

### P7 — System DNS and NTP are configured `[9.0]`

**Must be true:** DNS and NTP are set at the **system** level in 9.0 and inherited by everything
SDDC Manager deploys. Deploying a domain or cluster against wrong DNS/NTP is a classic late
failure.

**How to verify:** `GET /v1/system/dns-configuration` (`getDnsConfiguration`) and
`GET /v1/system/ntp-configuration` (`getNtpConfiguration`) — both **spec-confirmed (9.0)** and
**active** (not deprecated) in 9.0.

**9.1 difference — this one actually flips.** In 9.1 the whole
`/v1/system/dns-configuration` and `/v1/system/ntp-configuration` family is **deprecated**
(9 operations), and DNS/NTP move onto the topology specs themselves: `dnsServers` / `ntpServers`
appear on `DomainCreationSpec` and `ClusterCreationSpec`, and a `dnsNtpUpdateSpec` appears on
`DomainUpdateSpec` and `ClusterUpdateSpec`. None of those fields exist in the 9.0 schemas. This is
the "streamlined DNS and NTP management at scale" item in the 9.1 notes [D9.1 §3.5].

### P8 — Licensing state permits the operation `[9.0]`

**Must be true:** hosts joining a cluster are licensed, or the operation is explicitly run
unlicensed. `HostSpec.licenseKey` is documented as *"required except in cases where the ESXi host
has already been licensed outside of the VMware Cloud Foundation system."*
`ClusterCreationSpec.deployWithoutLicenseKeys` and `ClusterExpansionSpec.deployWithoutLicenseKeys`
are the explicit opt-outs.

**How to verify:** `GET /v1/license-keys` (**spec-confirmed (9.0)**) and the VCF Operations
licensing view. 9.0 replaced 25-character keys with subscription license files managed through VCF
Operations and the VCF Business Services console [D9.0 §5.1]; expiry triggers a 90-day grace
period after which **hosts disconnect from vCenter** [D9.0 §5.4].

**9.1 difference:** the same spec fields exist, but licenses move out of VCF Operations into a new
required **License server** component [D9.1 §6]. The API fields are unchanged; where the license
lives is not.

### P9 — Caller role and privilege for topology write operations `[9.0]` — UNVERIFIED

**Must be true:** the account behind the bearer token holds whatever role is required for topology
**writes** — `POST /v1/hosts`, `DELETE /v1/hosts`, `POST /v1/domains`, `PATCH /v1/domains/{id}`,
`DELETE /v1/domains/{id}`, `POST /v1/clusters`, `PATCH /v1/clusters/{id}`,
`DELETE /v1/clusters/{id}`, and the network-pool mutators.

> **UNVERIFIED. The required SDDC Manager role for these operations is not documented in any
> source consulted; verify before delegating credentials.** No retrieved 9.0 page names SDDC
> Manager role names, and no built-in-roles page exists anywhere in the 9.0 fleet-management tree
> — the page that defines VCF built-in roles is **9.1-only**, and its names must not be used for
> 9.0 [see `../../../vcf-foundation/references/9.0/auth-and-identity.md` P5]. `SPEC9.0` declares
> security *schemes* but carries **no per-operation privilege requirement**.
>
> Practical consequence: do not assume a token that can `GET /v1/hosts` can also
> `DELETE /v1/hosts`, and do not invent a role name for a runbook or a service-account request.
> Confirm against Broadcom's role documentation, or empirically against a non-production instance,
> **before** the account is provisioned.

**9.1 difference:** 9.1 documents VCF-level built-in roles (VCF Administrator, VCF Viewer, SDDC
Administrator, SDDC Viewer), but their published mapping covers vCenter, NSX, VCF Operations, VCF
Automation, HCX and Orchestrator — **not SDDC Manager**, which remains outside VCF SSO. The gap is
open in both versions.

### P10 — Items the research could not verify — state these as gaps, do not fill them in

- **Enumerated values for `storageType`, `vvolStorageProtocolType` and `Network.type`.** These are
  OpenAPI `example` strings, **not `enum` constraints**, in both 9.0 and 9.1. Treat them as
  strong hints, confirm against the live instance before hard-coding.
- **Ports and protocols matrix** for host commissioning and domain deployment — never retrieved,
  in either version.
- **Minimum and maximum host counts per cluster.** `ClusterCompactionSpec.forceByPassingSafeMinSize`
  implies a "safe minimum size" exists, but no source consulted states the number.
- **What SDDC Manager can and cannot do while a topology task is running.** A page titled "SDDC
  Manager Functionality During an Upgrade to VCF 9.0" was found by search but never fetched
  [D9.0 §11 item 13]. Treat concurrency limits as unknown, not as "none."
- **The mechanism for sharing an NSX Manager between domains.** `DomainCreationSpec.nsxTSpec` is
  optional in both versions, which is consistent with reuse, but no field in `RAW9.0` names an
  existing NSX cluster to attach to, and no 9.0 page describes the workflow. The 9.1 NSX notes
  advertise *"Sharing NSX Managers between Management and Workload Domains"* [D9.1 §3.3] without
  an API surface. UNVERIFIED in both.
- **The caller role for topology writes** — see P9.

---

## The topology object model

**Private Cloud → Fleet → VCF Instance → Domain (management | workload) → Cluster → Host**
[D9.0 §2.1].

- A **VCF Instance** is one management domain plus zero or more workload domains.
- A **domain** comprises one vCenter, one or more vSphere clusters with HA/DRS, distributed
  switches, an NSX Manager, and shared storage [D9.0 §2.1].
- The **management domain** is created at initial deployment and hosts SDDC Manager. For the first
  instance it also hosts the fleet-level management tools.
- A **host** enters the system through *commissioning*, lives in the free pool as
  `UNASSIGNED_USEABLE`, becomes `ASSIGNED` when placed in a cluster, and leaves through
  *decommissioning*.

**Which surface does what in 9.0.** The SDDC Manager **UI is deprecated** in 9.0 — workflows moved
to VCF Operations and the vSphere Client [D9.0 §3.1]. The **SDDC Manager API is not deprecated**
and remains the programmatic surface for topology [D9.0 §3.1, §3.3]. Notably, *stretched cluster
automation* is documented as SDDC Manager **API** specifically [D9.0 §3.5].

---

## The universal pattern: validate → execute → poll

Create and update operations in this API are paired with a `validations` sub-resource, and
long-running work returns a `Task` [D9.0 §3.4]. The shape is the same for hosts, domains and
clusters:

```
1. POST   <resource>/validations        →  200 Validation   (has an id)
2. GET    <resource>/validations/{id}   →  poll until executionStatus is terminal
3. POST | PATCH <resource>              →  202 Task         (has an id)
4. GET    /v1/tasks/{id}                →  poll until status is terminal
```

**Validation terminal states** (`Validation` schema, `RAW9.0`):
`executionStatus` ∈ `IN_PROGRESS, FAILED, COMPLETED, UNKNOWN, SKIPPED, CANCELLED,
CANCELLATION_IN_PROGRESS`; once `COMPLETED`, read `resultStatus` ∈ `SUCCEEDED, FAILED, WARNING,
UNKNOWN, CANCELLATION_IN_PROGRESS`. `COMPLETED` alone does **not** mean the spec is good — a
`COMPLETED` validation with `resultStatus: FAILED` is the common trap. Per-check detail is in
`validationChecks[]`.

**Task terminal states** (`Task` schema, `RAW9.0`): the `status` example lists
`PENDING, IN_PROGRESS, SUCCESSFUL, FAILED, CANCELLED, COMPLETED_WITH_WARNING, SKIPPED`, each also
in mixed case (`Pending`, `In Progress`, …). **Compare case-insensitively.** Failure detail is in
`errors[]` and `subTasks[]`.

**Task operations**, all **spec-confirmed (9.0)** (tag `Tasks`):

```
GET    /v1/tasks           getTasks     filters: resourceId, resourceType, taskStatus, taskType,
                                        taskName, completedAfter, pageNumber, pageSize (max 100)
GET    /v1/tasks/{id}      getTask
PATCH  /v1/tasks/{id}      retryTask    retry a failed task
DELETE /v1/tasks/{id}      cancelTask   cancel a running task
```

**9.1 difference:** the four task operations are unchanged, but the 9.1 `Task.status` example adds
`QUEUED` and `TIMED_OUT` (plus their mixed-case forms). A 9.0-era poller with a hard-coded state
list will mis-handle those after an upgrade.

---

## Hosts and the free pool

19 operations, tag `Hosts`. All **spec-confirmed (9.0)**.

```
GET    /v1/hosts                        getHosts
POST   /v1/hosts                        commissionHosts        body: HostCommissionSpec[]   → 202 Task
DELETE /v1/hosts                        decommissionHosts      body: HostDecommissionSpec[] → 202 Task
POST   /v1/hosts/validations            validateHostCommissionSpec  body: HostCommissionSpec[] → 202 Validation
GET    /v1/hosts/validations/{id}       getHostCommissionValidationByID
POST   /v1/hosts/prechecks              postHostsPrechecks_1   multipart: specFile
GET    /v1/hosts/prechecks/{id}         getHostsPrechecksResponse
GET    /v1/hosts/{id}                   getHost
GET    /v1/hosts/criteria               getCriteria
GET    /v1/hosts/criteria/{name}        getCriterion
GET    /v1/hosts/tags                   getTagsAssignedToHosts
GET|PUT|DELETE /v1/hosts/{id}/tags      getTagsAssignedToHost / assignTagsToHost / removeTagsFromHost
GET    /v1/hosts/{id}/tags/assignable-tags   getAssignableTagForHost
GET    /v1/hosts/{id}/tags/tag-manager       getHostTagManagerUrl
```

**Already deprecated in the 9.0 spec — do not use:**
`POST /v1/hosts/queries` (`postQuery`), `GET /v1/hosts/queries/{id}` (`getHostQueryResponse`),
and `POST /v1/hosts/validations/commissions` (`validateCommissionHosts`). Use
`POST /v1/hosts/validations` for commission validation.

**`HostCommissionSpec`** (`RAW9.0`) — **required**: `fqdn`, `username`, `password`, `storageType`,
`networkPoolId`. Optional: `networkPoolName`, `vvolStorageProtocolType`, `sshThumbprint`,
`sslThumbprint`. The body is an **array**, even for one host.

**`HostDecommissionSpec`** — a single required field, `fqdn`. Also an array body.

**9.1 difference:** `PATCH /v1/hosts` (`updateHosts`, body `HostsUpdateSpec`) and
`GET /v1/hosts/{id}/software` (`getSoftwareInfoForHost`) are **9.1-only**. Do not call them
against 9.0.

---

## Network pools

9 operations, tag `Network Pools`. All **spec-confirmed (9.0)**.

```
GET    /v1/network-pools                                       getNetworkPool
POST   /v1/network-pools                                       createNetworkPool    body: NetworkPool → 201 NetworkPool
GET    /v1/network-pools/{id}                                  getNetworkPoolByID
PATCH  /v1/network-pools/{id}                                  updateNetworkPool    body: NetworkPoolUpdateSpec (name only)
DELETE /v1/network-pools/{id}                                  deleteNetworkPool    only if unused
GET    /v1/network-pools/{id}/networks                         getNetworksOfNetworkPool
GET    /v1/network-pools/{id}/networks/{networkId}             getNetworkOfNetworkPool
POST   /v1/network-pools/{id}/networks/{networkId}/ip-pools    addIpPoolToNetworkOfNetworkPool     body: IpPool
DELETE /v1/network-pools/{id}/networks/{networkId}/ip-pools    deleteIpPoolFromNetworkOfNetworkPool body: IpPool
```

`NetworkPool` requires `name` and `networks[]`. Each `Network` requires `type`, `vlanId`, `mtu`,
`subnet`, `mask`, `gateway`; `ipPools[]` is optional at create time and can be added later.
`IpPool` requires `start` and `end`; in 9.0 both are constrained by an IPv4 `pattern` in the
schema.

**What 9.0 cannot do:** there is **no** way to change a network's VLAN, MTU, subnet or gateway
after creation, **no** way to edit an existing IP pool range in place, and **no** way to
mark individual IPs free/used. `PATCH /v1/network-pools/{id}` accepts **only** `name`. The
add/delete `ip-pools` pair is the entire mutation surface. Plan pools accordingly.

**9.1 difference — this is the largest gain in the whole topology area.** 9.1 adds four
operations that close exactly those gaps: `PATCH .../networks/{networkId}` (`NetworkUpdateSpec`:
vlan, mtu, subnet, gateway), `PATCH .../networks/{networkId}/ip-pools`
(`IpPoolUpdateSpec`: `oldIpPool` → `newIpPool`), `GET` and `PATCH .../networks/{networkId}/ips`
(`NetworkIpAddressesUpdateSpec`: `freeIps[]`, `usedIps[]`). All four are **9.1-only**.

---

## Workload domains

32 operations, tag `Domains`. All **spec-confirmed (9.0)**.

**Lifecycle of a domain**

```
GET    /v1/domains                          getDomains                filter: type
POST   /v1/domains/validations              validateDomainCreationSpec  body: DomainCreationSpec → 200 Validation
GET    /v1/domains/validations/{id}         domainCreateValidation
POST   /v1/domains                          createDomain              body: DomainCreationSpec → 202 Task
GET    /v1/domains/{id}                     getDomain
POST   /v1/domains/{id}/validations         validateDomainUpdateSpec  body: DomainUpdateSpec → 200 Validation
GET    /v1/domains/{id}/validations/{validationId}   getDomainUpdateValidation
PATCH  /v1/domains/{id}                     updateDomain              body: DomainUpdateSpec → 200 Task
DELETE /v1/domains/{id}                     deleteDomain              → 202 Task  (gated, see below)
```

**Inspection**

```
GET  /v1/domains/capabilities                       getDomainCapabilities
GET  /v1/domains/{id}/capabilities                  getDomainCapabilitiesByDomainId
GET  /v1/domains/{id}/endpoints                     getDomainEndpoints
GET  /v1/domains/{id}/datacenters                   getDomainDatacenters
PATCH /v1/domains/{id}/overlay                      enableOverlayOverManagementNetwork
POST /v1/domains/{domainId}/isolation-prechecks     performDomainIsolationPrecheck   body: IsolationSpec
GET  /v1/domains/{domainId}/isolation-prechecks/{precheckId}  getDomainIsolationPrecheckStatus
```

**Criteria/query pairs** — the asynchronous search idiom (POST a criterion, GET the result by
`queryId`), for clusters and datastores within a domain:
`GET /v1/domains/{domainId}/clusters/criteria` (`getClusterCriteria`), `…/criteria/{name}`
(`getClusterCriterion`), `POST …/clusters/queries` (`postClustersQuery`),
`GET …/clusters/queries/{queryId}` (`getClustersQueryResponse`),
`POST …/clusters/{clusterName}/queries` (`postClusterQuery`),
`GET …/clusters/{clusterName}/queries/{queryId}` (`getClusterQueryResponse`), and the four
matching `datastores` operations (`getDatastoresCriteria`, `getDatastoreCriterion`,
`postDatastoreQuery`, `getDatastoreQueryResponse`).

**Tags:** `GET /v1/domains/tags` (`getTagsAssignedToDomains`), `GET|PUT|DELETE
/v1/domains/{id}/tags`, `GET /v1/domains/{id}/tags/assignable-tags`,
`GET /v1/domains/{id}/tags/tag-manager`.

**`DomainCreationSpec`** (`RAW9.0`) — **required**: `vcenterSpec` **and `computeSpec`**.
Optional: `domainName`, `orgName`, `nsxTSpec`, `ssoDomainSpec`, `securitySpec`,
`existingDatastoreName`, `deployWithoutLicenseKeys`.

> **A 9.0 domain cannot be created without a cluster.** `computeSpec` is required, and
> `ComputeSpec.clusterSpecs[]` is required within it. In **9.1**, `computeSpec` is dropped from
> `DomainCreationSpec.required` — vCenter and NSX Manager can be deployed with no initial cluster
> — but **patching and upgrades are blocked until a cluster is added** [D9.1 §3.4]. That is a 9.1
> capability and a 9.1 trap; it does not apply here.

**`DomainUpdateSpec`** (`RAW9.0`) — all optional: `clusterSpec` (add a cluster to the domain),
`nsxTSpec`, `name`, `markForDeletion`, `isolationSpec`.

**9.1 difference:** `PATCH /v1/domains` (`updateDomains`, bulk refresh via `DomainsUpdateSpec`),
the `image-compliance` query pair, and the whole `hcx-managers` family are **9.1-only**.
`PATCH /v1/domains/{id}/overlay` becomes **deprecated** in 9.1.

---

## Clusters

34 operations, tag `Clusters`. All **spec-confirmed (9.0)** unless marked.

**Lifecycle of a cluster**

```
GET    /v1/clusters                              getClusters   filters: domainId, isStretched, isImageBased
POST   /v1/clusters/validations                  validateClusterCreationSpec  body: ClusterCreationSpec → 200 Validation
GET    /v1/clusters/validations/{id}             getClusterCreateValidation
POST   /v1/clusters                              createCluster                body: ClusterCreationSpec → 202 Task
GET    /v1/clusters/{id}                         getCluster
POST   /v1/clusters/{id}/validations             validateClusterUpdateSpec    body: ClusterUpdateSpec → 200 Validation
GET    /v1/clusters/{id}/validations/{validationId}   getClusterUpdateValidation
PATCH  /v1/clusters/{id}                         updateCluster                body: ClusterUpdateSpec → 200 Task
DELETE /v1/clusters/{id}                         deleteCluster                → 202 Task  (gated, see below)
```

`PATCH /v1/clusters/{id}` is the single door for **five different operations**, selected by which
field of `ClusterUpdateSpec` you populate. The spec summary says it plainly: *"Update a Cluster by
adding or removing Hosts, Stretching a standard vSAN cluster, Unstretching a stretched cluster or
by marking for deletion."*

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

**`ClusterCreationSpec`** — required: `domainId`, `computeSpec`. `ComputeSpec` requires
`clusterSpecs[]`; each `ClusterSpec` requires `hostSpecs[]`, `datastoreSpec`, `networkSpec`, and
in practice `clusterImageId` (see P6).

**`ClusterExpansionSpec`** — required: `hostSpecs[]`. Optional: `networkSpec`
(`ClusterExpansionNetworkSpec`, which itself requires `nsxClusterSpec` and `networkProfiles[]`),
`vsanNetworkSpecs[]`, `witnessSpec`, `witnessTrafficSharedWithVsanTraffic`,
`deployWithoutLicenseKeys`, `interRackExpansion`. `interRackExpansion` is documented as *"Required,
only if Cluster contains NSX Edge Cluster."* `forceHostAdditionInPresenceofDeadHosts` and
`skipThumbprintValidation` are **already deprecated in the 9.0 spec**;
`forceHostAdditionInPresenceofDeadHosts` is additionally documented as having *"no effect."*

**`ClusterCompactionSpec`** — required: `hosts[]` of `HostReference` (`id`, or `fqdn`). Optional:
`force`, and `forceByPassingSafeMinSize`, documented as *"Remove dead hosts from cluster, bypassing
validations. Forced removal may result in permanent data loss. Review recovery plan with VMware
Support before using."* Treat that sentence as a hard gate, not a caveat.

**Storage attached to a cluster**

```
GET    /v1/clusters/{id}/datastores                    getClusterDatastores
POST   /v1/clusters/{id}/datastores                    addDatastoreToCluster    body: DatastoreMountSpec → 202 Task
DELETE /v1/clusters/{id}/datastores/{datastoreId}      removeDatastoreFromCluster → 200 Task
POST   /v1/clusters/{clusterId}/datastores/validations validateVsanRemoteDatastoreMountSpec
GET|POST /v1/clusters/{id}/datastores/criteria|queries getDatastoresCriteria_1 / postDatastoreQuery_1
GET    /v1/clusters/{clusterId}/datastores/queries/{queryId}  getDatastoreQueryResponse_1
```

`POST /v1/clusters/{clusterId}/datastores/validation` (singular, `validateVsanRemoteDatastoreSpec`)
is **already deprecated in the 9.0 spec** — use the plural `validations`.

**Networking attached to a cluster**

```
GET  /v1/clusters/{clusterId}/vdses              getVdses
POST /v1/clusters/{clusterId}/vdses              importVdsToInventory   body: ImportVdsSpec → 202 Task
GET  /v1/clusters/{id}/network/criteria          getClusterNetworkConfigurationCriteria
POST /v1/clusters/{id}/network/queries           getClusterNetworkConfiguration
GET  /v1/clusters/{id}/network/queries/{queryId} getClusterNetworkConfigurationQueryResponse
```

**Images and tags**

```
GET /v1/clusters/{id}/image-compliance        getClusterImageCompliance
GET /v1/clusters/tags                         getTagsAssignedToClusters
GET|PUT|DELETE /v1/clusters/{id}/tags         getTagsAssignedToCluster / assignTagsToCluster / removeTagsFromCluster
GET /v1/clusters/{id}/tags/assignable-tags    getTagAssignableForCluster
GET /v1/clusters/{id}/tags/tag-manager        getClusterTagManagerUrl
```

**Already deprecated in the 9.0 spec:** `GET /v1/clusters/{id}/hosts/criteria`
(`getHostCriteria`), `GET /v1/clusters/{id}/hosts/criteria/{name}` (`getHostCriterion`),
`POST /v1/clusters/{id}/hosts/queries` (`postHostQuery`),
`GET /v1/clusters/{clusterId}/hosts/queries/{queryId}` (`getHostQueryResponse_1`), and the
singular datastore `validation` above.

**9.1 difference:** `PATCH /v1/clusters` (`updateClusters`, bulk refresh),
`POST /v1/clusters/{clusterId}/remediations` (`triggerRemediation`) with
`GET /v1/clusters/{clusterId}/remediations/{remediationId}` (`getRemediationById`) to poll it
(out-of-band drift remediation — there is no GET on the collection), and
`GET /v1/clusters/{id}/datastores/validations/{validationId}` are **9.1-only**. 9.1 also adds
`clusterPrimaryDatastoreUpdateSpec`, `dnsNtpUpdateSpec` and `markAsDefault` to
`ClusterUpdateSpec`.

---

## vCenter, NSX, ALB and PSC association

**vCenter** — read-only in 9.0. Two operations, tag `vCenters`:
`GET /v1/vcenters` (`getVcenters`), `GET /v1/vcenters/{id}` (`getVcenter`). A domain's vCenter is
created by `POST /v1/domains` via `DomainCreationSpec.vcenterSpec` (required:
`networkDetailsSpec`; optional: `name`, `rootPassword`, `datacenterName`, `vmSize`,
`storageSize`).

> `PATCH /v1/vcenters/{vcenterId}/fqdn` (`updateVcenterFqdn`) is **9.1-only** — there is no way to
> rename a vCenter's FQDN through the 9.0 SDDC Manager API.

**PSC** — read-only: `GET /v1/pscs` (`getPscs`), `GET /v1/pscs/{id}` (`getPsc`).

**NSX** — 16 operations, tag `NSX-T Clusters`, all **spec-confirmed (9.0)**:

```
GET  /v1/nsxt-clusters                                    getNsxClusters
GET  /v1/nsxt-clusters/{id}                               getNsxCluster
GET  /v1/nsxt-clusters/criteria                           getNsxCriteria
GET  /v1/nsxt-clusters/criteria/{name}                    getNsxCriterion
POST /v1/nsxt-clusters/queries                            startNsxCriteriaQuery
GET  /v1/nsxt-clusters/queries/{id}                       getNsxClusterQueryResponse
POST /v1/nsxt-clusters/{nsxt-cluster-id}/scale-out        scaleOutNsx
GET  /v1/nsxt-clusters/{nsxt-cluster-id}/transport-zones  getNsxTransportZones
GET  /v1/nsxt-clusters/{nsxt-cluster-id}/ip-address-pools getNsxIpAddressPools
GET  /v1/nsxt-clusters/{nsxt-cluster-id}/ip-address-pools/{name}  getNsxIpAddressPool
POST /v1/nsxt-clusters/ip-address-pools/validations       validateIpPool
GET  /v1/nsxt-clusters/ip-address-pools/validations/{id}  getValidationResult
POST /v1/nsxt-clusters/oidcs                              connectOpenId
GET  /v1/nsxt-clusters/{nsxt-cluster-id}/vpc-configuration    getVpcConfiguration
GET  /v1/nsxt-clusters/{nsxtClusterId}/projects               getProjects
GET  /v1/nsxt-clusters/{nsxtClusterId}/projects/{projectId}/vpc-connectivity-profiles  getVpcConnectivityProfiles
```

A domain's NSX is created by `DomainCreationSpec.nsxTSpec` (`NsxTSpec` requires `nsxManagerSpecs[]`
and `vipFqdn`; `ipAddressPoolSpec` is marked deprecated in the 9.0 schema in favour of the plural
form on `NsxTClusterSpec`).

**NSX Edge clusters** — 8 operations, tag `NsxTEdgeClusters`, **active (not deprecated) in 9.0**:
`GET|POST /v1/edge-clusters` (`getEdgeClusters` / `createEdgeCluster`),
`POST /v1/edge-clusters/validations` (`validateEdgeClusterCreationSpec`),
`GET /v1/edge-clusters/validations/{id}` (`getEdgeClusterValidationByID`),
`GET|PATCH /v1/edge-clusters/{id}` (`getEdgeCluster` / `updateEdgeCluster`),
`POST /v1/edge-clusters/{id}/validations` (`validateEdgeClusterUpdateSpec`),
`GET /v1/edge-clusters/{edgeClusterId}/criteria` (`getEdgeClusterQueryCriteria`).

> **9.1 difference:** all eight become **deprecated** in 9.1. Anything you build on
> `/v1/edge-clusters` in 9.0 is on a countdown. `SPEC9.0` marks none of them deprecated, so they
> are correct to use *today* on 9.0 — just do not treat them as long-lived.

**NSX ALB / Avi** — 15 operations, tag `ALBClusters`, of which **7 are already deprecated in
9.0**: the entire `/v1/nsx-alb-clusters` family. Use the `/v1/alb-clusters` family instead:
`GET|POST /v1/alb-clusters` (`getAviLBClusters` / `deployALBCluster`),
`GET|DELETE /v1/alb-clusters/{id}` (`getAviLBCluster` / `undeployALBCluster`),
`POST /v1/alb-clusters/validations` (`validateALBControllerClusterCreationSpec`),
`POST /v1/alb-clusters/compatibility/validations` (`validateALBCompatibility`),
`GET /v1/alb-clusters/form-factors` (`getALBClustersFormFactors_1`),
`GET /v1/alb-clusters/cluster-capacity` (`getClusterCapacityForALBDeployment`).

---

## Brownfield import and configuration drift

**Import an existing vCenter as a workload domain** — 6 operations, tag `BrownfieldImport`, all
**spec-confirmed (9.0)**:

```
POST /v1/sddcs/imports/validations                 validation                 → validate first
GET  /v1/sddcs/imports/validations/{taskId}        getBrownfieldCheckTaskById
POST /v1/sddcs/imports                             import                     → then import
GET  /v1/sddcs/imports/{taskId}                    getBrownfieldImportTaskById
POST /v1/domains/{domainId}/synchronizations       synchronization            body: BrownfieldSyncSpec → 202 BrownfieldTask
GET  /v1/domains/{domainId}/synchronizations/{taskId}  getBrownfieldSyncTaskById
```

Note these use their **own** task poller (`BrownfieldTask` via
`GET /v1/sddcs/imports/{taskId}`), not `/v1/tasks/{id}`.

**Configuration drift** — reconcile out-of-band vCenter/NSX changes back into SDDC Manager
inventory. Tag `ConfigReconciler`, all **spec-confirmed (9.0)**:
`GET /v1/config-drifts` (`getConfigs`), `POST /v1/config-drift-reconciliations`
(`reconcileConfigs`), `GET /v1/config-drift-reconciliations/{taskId}` (`getReconciliationTask`).

**vSAN health per domain** — tag `vSANHealthCheck`:
`GET|PATCH /v1/domains/{domainId}/health-checks` (`getVsanHealthCheckByDomain` /
`updateVsanHealthCheckByDomain`), `GET …/health-checks/tasks/{taskId}`
(`getVsanHealthCheckByTaskID`), `GET …/health-checks/queries/{queryId}`
(`getVsanHealthCheckByQueryID`).

**9.1 difference:** 9.1 adds four brownfield operations (`syncSshKnownHosts`,
`exportValidationsAsCsv`, and the validation-group pair) and the cluster `remediations` pair for
out-of-band changes. Config drift and vSAN health are identical in both.

---

## Worked example — expand an existing cluster by two hosts

Adds two already-racked ESX hosts to an existing vSAN cluster. Every path and field below is
**spec-confirmed (9.0)** / drawn from `RAW9.0` schemas. Values are placeholders.

**Step 0 — find the network pool and the target cluster.**

```http
GET /v1/network-pools                        → getNetworkPool
GET /v1/clusters?domainId=<domain-id>        → getClusters
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

→ `202` with a `Validation`. Poll:

```http
GET /v1/hosts/validations/{id}               → getHostCommissionValidationByID
```

until `executionStatus` is terminal, then **check `resultStatus == "SUCCEEDED"`**. A `COMPLETED`
validation with `resultStatus: FAILED` is a failure; read `validationChecks[]` for the reason.

**Step 2 — commission.** Same array body, different path.

```http
POST /v1/hosts                               → commissionHosts, 202 Task
GET  /v1/tasks/{id}                      → poll to SUCCESSFUL
```

**Step 3 — confirm the hosts landed in the free pool and capture their IDs.**

```http
GET /v1/hosts?status=UNASSIGNED_USEABLE      → getHosts
```

`HostSpec.id` for the expansion is the `id` returned here — not the FQDN.

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
(`getClusterUpdateValidation`) and again check **both** `executionStatus` and `resultStatus`.

Field notes, all from `RAW9.0`:
- `hostSpecs[].id` — **required**, the free-pool host ID.
- `hostSpecs[].licenseKey` — *"required except in cases where the ESXi host has already been
  licensed outside of the VMware Cloud Foundation system."* Set
  `clusterExpansionSpec.deployWithoutLicenseKeys: true` to run unlicensed deliberately.
- `hostSpecs[].sshThumbprint` — optional in 9.0, but the schema warns *"this field will be
  mandatory in future releases."* Populate it.
- `hostSpecs[].ipAddress` — **deprecated**; use `hostName`.
- `hostSpecs[].azName` — required only when expanding a **stretched** cluster.
- `clusterExpansionSpec.interRackExpansion` — *"Required, only if Cluster contains NSX Edge
  Cluster."*
- `clusterExpansionSpec.networkSpec` — needed when the new hosts require NSX uplink profiles or IP
  pools that the cluster does not already carry; it requires `nsxClusterSpec` **and**
  `networkProfiles[]` when present at all.

**Step 5 — execute.** Identical body, `PATCH` to the cluster itself.

```http
PATCH /v1/clusters/{id}               → updateCluster, 200 Task
```

**Step 6 — poll to completion.**

```http
GET /v1/tasks/{id}                       → getTask
```

Terminal when `status` (case-insensitively) is `SUCCESSFUL`, `FAILED`, `CANCELLED`,
`COMPLETED_WITH_WARNING` or `SKIPPED`. On failure read `errors[]` and `subTasks[]`;
`PATCH /v1/tasks/{id}` (`retryTask`) retries. Confirm the end state with
`GET /v1/clusters/{id}` — `status` back to `ACTIVE`, not `EXPANDING`.

**9.1 note:** this exact sequence works unchanged on 9.1 — `ClusterExpansionSpec` and `HostSpec`
have identical properties and required fields in both versions. Two differences to carry: the 9.1
poller must also accept `QUEUED` and `TIMED_OUT` task states, and 9.1 permits `NFS41`/`FC` as
`storageType` values that 9.0 does not.

---

## Destructive operations and their gates

Confirm before executing. These are not reversible by re-running them.

**Cluster deletion is two-phase.** `DELETE /v1/clusters/{id}` is summarized in the spec as
*"Delete a cluster from a domain **if it has been previously initialized for deletion**."* You must
first arm it:

```
PATCH  /v1/clusters/{id}   { "markForDeletion": true }   → updateCluster
DELETE /v1/clusters/{id}                                 → deleteCluster, 202 Task
```

**Domain deletion is the same shape.** `DELETE /v1/domains/{id}` — *"Remove a domain **if it has
been previously initialized for deletion**."* Arm with
`PATCH /v1/domains/{id} { "markForDeletion": true }` (`DomainUpdateSpec.markForDeletion`, *"Enable
deletion for the domain"*). Deleting a domain destroys its vCenter and its NSX Manager.

**Host decommissioning** — `DELETE /v1/hosts` with a `HostDecommissionSpec[]` body. Only hosts not
assigned to a cluster can be decommissioned; remove them from the cluster first via
`clusterCompactionSpec`.

**The two force flags are the dangerous ones.**
`ClusterCompactionSpec.forceByPassingSafeMinSize` is documented as *"Remove dead hosts from
cluster, bypassing validations. Forced removal may result in permanent data loss. Review recovery
plan with VMware Support before using."* `ClusterCompactionSpec.force` forces removal of a host.
Neither should appear in a runbook without an explicit, named decision to use it.

**Network pool deletion** — `DELETE /v1/network-pools/{id}` succeeds *"if it exists and is
unused."* Check `NetworkPool.hostsCount` and `GET /v1/hosts?networkpoolId=<id>` first.

**Everything destructive here is asynchronous.** The `202` means *accepted*, not *done*. Poll
`/v1/tasks/{id}` before reporting success.

---

## Discrepancies and UNVERIFIED items

1. **`storageType`, `vvolStorageProtocolType` and `Network.type` have no `enum`.** All three
   carry `example` strings only, in both 9.0 and 9.1. Any list of valid values you write down is
   copied from an example, not from a constraint. Say so when you pass it on.
2. **Spec base path.** `SPEC9.0` declares `http://localhost:80` as its server. That is a build
   placeholder. The real base is `https://<sddc-manager-fqdn>` with `/v1` carried in the path
   [D9.0 §3.3].
3. **API size.** Techdocs prose says *"about 280 interfaces in the SDDC Manager API"*
   [D9.0 §3.3]; `SPEC9.0` contains **375 operations**, of which **128** are topology. The prose is
   stale; prefer the spec.
4. **`ClusterExpansionSpec.forceHostAdditionInPresenceofDeadHosts`** is marked deprecated **and**
   documented as having *"no effect when using it"* — in the 9.0 spec, not just 9.1. If a runbook
   relies on it to add hosts alongside dead ones, that runbook is wrong today.
5. **Already deprecated in the 9.0 spec** (prose sources do not mention any of these):
   `POST /v1/hosts/queries`, `GET /v1/hosts/queries/{id}`, `POST /v1/hosts/validations/commissions`,
   `GET /v1/clusters/{id}/hosts/criteria[/{name}]`, `POST /v1/clusters/{id}/hosts/queries`,
   `GET /v1/clusters/{clusterId}/hosts/queries/{queryId}`,
   `POST /v1/clusters/{clusterId}/datastores/validation` (singular), and the seven
   `/v1/nsx-alb-clusters` operations.
6. **Domain deletion side-effects are not enumerated.** No source consulted states what happens to
   the hosts of a deleted domain — whether they return to the free pool as `UNASSIGNED_USEABLE` or
   must be re-commissioned. UNVERIFIED.
7. **Concurrency limits are unknown.** How many topology tasks SDDC Manager will run at once in
   9.0 is not documented in any source consulted. (9.1 advertises *256 simultaneous cluster
   upgrades* [D9.1 §3.5], but that is an upgrade figure, a 9.1 figure, and not a topology-task
   figure.) UNVERIFIED.
8. **Stretched-cluster prerequisites are not captured.** `clusterStretchSpec` requires
   `hostSpecs[]` and `witnessSpec` (`vsanIp`, `fqdn`, `vsanCidr`), and `prepareForStretch` exists
   as a separate flag — but the ordering, the witness-host commissioning requirements and the
   availability-zone prerequisites were not retrieved from any documentation source. The **fields**
   are spec-confirmed; the **procedure** is UNVERIFIED.
