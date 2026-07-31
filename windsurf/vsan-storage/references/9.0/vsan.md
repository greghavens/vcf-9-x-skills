# VCF 9.0 — vSAN Storage Reference

**Scope:** vSAN in VMware Cloud Foundation 9.0.x. Everything here is `[9.0]` unless
explicitly tagged otherwise.

**Sources.**
`DVS` = `research/vsphere-vcenter-vsan.md`; `DAUTH` = `research/foundation-auth-identity.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine diff of git tags `9.0.0.0`
and `9.1.0.0` of `github.com/vmware/vcf-api-specs`).
Machine-extracted operation inventories, all from the `9.0.0.0` tag:
`SPECSDDC` = `9.0__sddc-manager.ops.json` (**375** ops, spec version `9.0.0.0`);
`SPECVIJ` = `9.0__vsphere-vi-json.ops.json` (**2195** ops, of which **301** are vSAN);
`SPECDP` = `9.0__vsan-data-protection.ops.json` (**48** ops, spec version `9.0.0.0`);
`SPECAUTO` = `9.0__vsphere-automation.ops.json` (**1275** ops).

Every endpoint is cited with its **`operationId`** and marked **spec-confirmed (9.0)**
against the named inventory, or flagged.

> **Not validated live.** Storage-policy changes, RAID-level changes, disk-group operations
> and stretch/unstretch all move data and are production-affecting. Verify against the
> customer's build and free capacity before executing.

---

## Contents

- [Three surfaces, and which one owns what](#three-surfaces-and-which-one-owns-what)
- [Prerequisites](#prerequisites)
  - P0 — Authentication (defer to `vcf-foundation`)
  - P1 — Know the cluster's architecture and datastore type
  - P2 — Stretched clusters: witness host + exactly two fault domains
  - P3 — Capacity headroom before any policy, RAID or disk change
  - P4 — ESA hardware eligibility
  - P5 — vSAN health is clean, and the HCL database is current
  - P6 — Caller privilege — partially spec-declared, treat as indicative
  - P7 — Items the sources could not establish
- [SDDC Manager surface — vSAN operations](#sddc-manager-surface--vsan-operations)
- [Stretching a cluster in 9.0](#stretching-a-cluster-in-90)
- [VI-JSON surface — the vSAN management API](#vi-json-surface--the-vsan-management-api)
- [Storage policies — two surfaces, one concept](#storage-policies--two-surfaces-one-concept)
- [vSAN Data Protection (snapservice) surface](#vsan-data-protection-snapservice-surface)
- [What vSAN 9.0 shipped](#what-vsan-90-shipped)
- [Spec-vs-prose discrepancies found while writing this file](#spec-vs-prose-discrepancies-found-while-writing-this-file)

---

## Three surfaces, and which one owns what

```
SDDC Manager  https://<sddc-manager>/v1/...
  └── stretch / unstretch a cluster, remote-datastore (HCI mesh) mounts,
      domain-wide vSAN health checks, vSAN HCL database management
      REST. operationIds are camelCase verbs. Long work returns a Task.

VI-JSON       https://<vcenter>/sdk/vim25/{release}/vsan/{MO}/{moId}/{Operation}
  └── everything else on the vCenter side: cluster vSAN config, disks and
      storage pools, fault domains, witness hosts, health, performance,
      space reporting, file services, iSCSI, CNS, diagnostics
      POST-only RPC. moId is a singleton string like 'vsan-cluster-config-system'.
      Body schema is {Operation}RequestType.

vSAN Data Protection   https://<dp-appliance>/api/snapservice/...
  └── vSAN native snapshots, protection groups, snapshot/replication policies,
      cluster pairs, sites
      REST. operationIds are dotted (Snapservice.X_verb). ?vmw-task=true.

vSphere Automation     https://<vcenter>/api/vcenter/...
  └── ZERO vSAN operations. Spec-confirmed absence in SPECAUTO (9.0).
      Only relevant piece: the read/compliance half of storage policies.
```

**The absence is load-bearing.** `SPECAUTO` (9.0, 1275 ops) contains **no path or
operationId matching `vsan`**, and **no path matching `stretch`**. Its two `witness`
operations are `Vcenter.Vcha.Cluster.Witness_check` and
`Vcenter.Vcha.Cluster.Witness_redeploy$Task` — **vCenter High Availability**, unrelated to
vSAN. Do not offer them as vSAN witness management.

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what
must hold, **how to verify it**, the version it applies to, and whether 9.1 differs.

### P0 — Authentication `[9.0]`

**Must be true:** you hold a credential for each surface you will call. **vSAN has no
independent authentication of its own** — it reuses the vCenter session. The vSAN
Management APIs "depend on the vSphere Web Services API for login procedures"; authenticate
to vCenter and reuse that session [DAUTH]. `SPECVIJ` declares exactly one security scheme,
`Session`: an API key in the **`vmware-api-session-id`** header, *"returned by the `Login`
operation of the `SessionManager` interface"* — `POST /sdk/vim25/{release}/SessionManager/{moId}/Login`,
`operationId` `SessionManager_Login`, **spec-confirmed (9.0)**.

The other two surfaces have their own credentials:

| Surface | Scheme | Where the credential comes from |
|---|---|---|
| SDDC Manager | `Authorization: Bearer <accessToken>` | `POST /v1/tokens` — see `vcf-foundation` |
| VI-JSON (vSAN) | `vmware-api-session-id` header | vCenter session — see `vcf-foundation` |
| vSAN Data Protection | `SPECDP` declares three: `basic_auth`, `api_key_auth` (`vmware-api-session-id`), `federated_identity_auth` (HTTP bearer). Its own session op is `POST /api/snapservice/sessions`, `operationId` `Snapservice.Sessions_create`, **spec-confirmed (9.0)**. | see `vcf-foundation` |

One 9.0-specific hazard worth carrying: vCenter 9.0 **blocks non-federated
username/password logins** [DVS §5], which changes how a session is obtained. That is a
`vcf-foundation` problem, not a vSAN one — but it is the most likely reason a vSAN call
fails before it ever reaches vSAN.

**Do not build an auth flow from this file.** Go to `vcf-foundation`. The only vSAN-specific
fact is the one above: vSAN itself issues nothing.

**9.1 difference:** none. Identical security schemes at both tags in all three specs.

### P1 — Know the cluster's architecture and datastore type `[9.0]`

**Must be true:** you know whether the target cluster is ESA, OSA, vSAN Max, or a
compute-only client of a remote vSAN datastore, before you send anything that assumes one.
The payload fields differ — `failuresToTolerate` is documented as *"required for vSAN OSA
configuration"*, and `esaConfig` carries a **required** `enabled` boolean.

**How to verify:**
- SDDC Manager: `GET /v1/clusters` (`getClusters`) or `GET /v1/clusters/{id}` (`getCluster`),
  both **spec-confirmed (9.0)**. The `Cluster` schema returns `primaryDatastoreType`, whose
  documented example enumerates *"VSAN, VSAN_ESA, VSAN_MAX, NFS, FC, VVOL_FC, VVOL_ISCSI,
  VVOL_NFS, VSAN_REMOTE, VMFS, VVOL"*, plus `isStretched`, `failuresToTolerate`,
  `vsanClusterMode` and `hciMeshData`. In 9.0 `getClusters` accepts only three filters:
  `isStretched`, `isImageBased`, `domainId`.
- VI-JSON: `VsanVcClusterConfigSystem_VsanClusterGetConfig` (**spec-confirmed (9.0)**,
  privilege `System.Read`) on `moId` `vsan-cluster-config-system`.
- Capability probe: `VsanCapabilitySystem_VsanGetCapabilities` (**spec-confirmed (9.0)**),
  `moId` `vsan-vc-capability-system` at vCenter or `vsan-capability-system` on a host.
- Host inventory: `GET /v1/hosts?storageType=VSAN_ESA` (`getHosts`, **spec-confirmed
  (9.0)**); the `storageType` filter accepts `VSAN`, `VSAN_ESA`, `VSAN_REMOTE`, `VSAN_MAX`
  and the non-vSAN types.

> **UNVERIFIED — which architecture is the default for a new cluster.** No retrieved
> Broadcom page states it; both ESA Witness (`9.0.0.0` / build `24755427`) and OSA Witness
> (`9.0.0.0` / build `24755428`) appliances ship in the 9.0 BOM [DVS §1, §7; DVS gap 8]. The
> specs do not settle it either: `EsaConfig.enabled` is a required boolean with **no
> declared default**. Do not resolve this from memory.

**9.1 difference:** the `Cluster` schema and `primaryDatastoreType` enumeration are the
same. 9.1 adds `name`, `isDefault`, `isHciMeshEnabled`, `managedObjectReferenceId`,
`pageSize`, `pageNumber` and `useCache` filters to `getClusters`, and
`isVsanWitnessHost` / `isStandalone` / `isLifecycleManaged` to `getHosts`.

### P2 — Stretched clusters: witness host and exactly two fault domains `[9.0]`

**Must be true**, and both are stated in the specs rather than inferred:

1. **A witness host.** `ClusterStretchSpec` marks `witnessSpec` **required**, and
   `WitnessSpec` requires all three of `fqdn` ("Management ip of the witness host"),
   `vsanIp`, `vsanCidr`.
   On the VI-JSON path, `VSANVcConvertToStretchedClusterRequestType` marks `witnessHost`
   **required** and constrains it: *"This host must be connected and managed by the same
   vCenter server, and cannot be a part of target cluster"*. The target cluster itself is
   *"expected to enable vSAN, but not a vSAN stretched cluster"*.
2. **Exactly two fault domains.** `VimVsanReconfigSpec.faultDomainsSpec` is documented: *"If
   `VimClusterVsanWitnessSpec` is specified which indicates it a stretched cluster, the fault
   domain list needs to include exactly two fault domain items."*

**How to verify, before you commit:**
- Is it already stretched? `GET /v1/clusters?isStretched=true` (`getClusters`,
  **spec-confirmed (9.0)**), or `VimClusterVsanVcStretchedClusterSystem_VSANVcGetWitnessHosts`
  (**spec-confirmed (9.0)**) on `moId` `vsan-stretched-cluster-system`.
- Is a candidate host actually a witness? `..._VSANVcIsWitnessHost`; is it the virtual
  appliance form? `..._VSANIsWitnessVirtualAppliance`. Both **spec-confirmed (9.0)**.
- Does this vCenter support the topology you want?
  `..._VSANVcRetrieveStretchedClusterVcCapability` (**spec-confirmed (9.0)**).
- Shared witness across clusters: `..._QuerySharedWitnessCompatibility` and
  `..._QuerySharedWitnessClusterInfo` (**spec-confirmed (9.0)**) before
  `..._VsanVcAddWitnessHostForClusters`.
- Dry-run the whole SDDC Manager spec: `POST /v1/clusters/{id}/validations`
  (`validateClusterUpdateSpec`, **spec-confirmed (9.0)**).

**9.1 difference:** none material. All 13 `VimClusterVsanVcStretchedClusterSystem`
operations exist at both tags, and `ClusterStretchSpec` / `WitnessSpec` /
`ClusterStretchNetworkSpec` / `NsxStretchClusterSpec` / `StretchClusterNetworkProfile` are
byte-identical at both tags. The one schema change is `ClusterUnstretchSpec`: an **empty
object** in 9.0, gaining an optional `azToRemove` in 9.1.

> **UNVERIFIED — the operational prerequisite list for stretched clusters.** Witness sizing,
> supported host counts per site, latency and bandwidth limits between sites, and the
> supported witness placement topologies are **not present in any retrieved source**. The
> schema constraints above are real; a full stretched-cluster readiness checklist is not
> derivable from these sources. Point at Broadcom's vSAN stretched-cluster guide for the
> customer's build.

### P3 — Capacity headroom before any policy, RAID or disk change `[9.0]`

**Must be true:** the cluster has enough free capacity to absorb the resync that a policy,
RAID-level, FTT, dedup/compression or disk-group change will start. The API accepts these
operations and *then* resyncs; there is no "would this fit?" gate built into the write call.

**How to verify (all VI-JSON, all spec-confirmed (9.0)):**
- `VsanResourceCheckSystem_VsanPerformResourceCheck` and `..._VsanGetResourceCheckStatus`
  on `moId` `vsan-cluster-resource-check-system` — the purpose-built pre-flight. Host-level:
  `..._VsanHostPerformResourceCheck`, `..._VsanHostCancelResourceCheck`.
- `VsanSpaceReportSystem_VsanQuerySpaceUsage`, `..._VsanQueryEntitySpaceUsage`
  (privilege `System.Read`), `..._QueryVsanManagedStorageSpaceUsage` on `moId`
  `vsan-cluster-space-report-system`.
- `VsanVcClusterConfigSystem_VsanClusterGetClaimedCapacity`.
- `VimClusterVsanVcDiskManagementSystem_QueryClusterDataEfficiencyCapacityState` before
  changing dedup/compression.
- What is resyncing right now: `VsanObjectSystem_QuerySyncingVsanObjectsSummary`,
  `VsanSystemEx_VsanQuerySyncingVsanObjects`.
- What a host evacuation would cost: `VsanSystemEx_VsanQueryWhatIfEvacuationResult`.
- Validate a config spec without applying it: `VsanVcClusterConfigSystem_VsanValidateConfigSpec`
  (privilege `Global.Diagnostics`).

Note `VimVsanReconfigSpec.allowReducedRedundancy` exists and is documented as applying to
reconfigure operations that migrate data across the cluster. Setting it trades redundancy
for the ability to proceed on a cluster without slack space. That is a decision to surface
explicitly, not a flag to set to make an error go away.

> **UNVERIFIED — the numeric headroom threshold.** No retrieved source states a required
> free-capacity percentage or slack-space rule for these operations. The verification route
> above is spec-confirmed; the threshold is not. Do not quote a percentage.

**9.1 difference:** 9.1 adds `VsanVcClusterConfigSystem_VsanGetConfigurationLimits`
(*"Returns configuration limits and supported values"*), which has **no 9.0 equivalent**
[DELTA]. Everything else in this list exists at both versions.

### P4 — ESA hardware eligibility `[9.0]`

**Must be true:** for an ESA cluster, the devices are ESA-eligible.

**How to verify (all spec-confirmed (9.0)):**
- `VsanVcClusterHealthSystem_VsanGetHclInfoForEligibleDisks` — *"Fetch HCL information for
  all vSAN ESA eligible disks of the target"*.
- `VsanVcClusterHealthSystem_VsanGetDiskHclConstraints` and `..._VsanGetHclConstraints`.
- `VimClusterVsanVcDiskManagementSystem_QueryVsanManagedDisks`; the storage-pool API notes
  eligibility explicitly (`VsanAddStoragePoolDisk`).
- `VimClusterVsanVcDiskManagementSystem_RetrieveAllFlashCapabilities`.
- `VsanVcClusterHealthSystem_VsanGetReleaseRecommendation`.

> **UNVERIFIED — the ESA hardware requirement list itself.** No retrieved source enumerates
> ESA's device class, endurance, NVMe, count-per-host or networking requirements. The
> verification *route* above is spec-confirmed; the requirement list is not. State the route
> and point at the Broadcom vSAN ESA planning guide rather than producing a list.

**9.1 difference:** all five operations exist unchanged at 9.1.

### P5 — vSAN health is clean, and the HCL database is current `[9.0]`

**Must be true:** you have looked at vSAN health before changing anything, and the HCL data
the health checks compare against is not stale.

**How to verify:**
- **SDDC Manager, domain-wide** (all **spec-confirmed (9.0)**):
  `GET /v1/domains/{domainId}/health-checks` (`getVsanHealthCheckByDomain`, accepts a
  `status` filter, returns `202` with a `HealthCheckQueryResult`),
  `GET /v1/domains/{domainId}/health-checks/queries/{queryId}` (`getVsanHealthCheckByQueryID`),
  `GET /v1/domains/{domainId}/health-checks/tasks/{taskId}` (`getVsanHealthCheckByTaskID`),
  `PATCH /v1/domains/{domainId}/health-checks` (`updateVsanHealthCheckByDomain`).
- **SDDC Manager, HCL database** (all **spec-confirmed (9.0)**):
  `PATCH /v1/vsan-hcl` (`downloadVsanHcl`, returns a `Task`),
  `GET /v1/vsan-hcl/configuration` (`getVsanHclConfiguration`),
  `PATCH /v1/vsan-hcl/configuration` (`updateVsanHclConfiguration`),
  `GET /v1/vsan-hcl/attributes` (`getVsanHclAttributes`).
  Egress note: HCL data comes from `vsanhealth.vmware.com:443` [DAUTH].
- **VI-JSON, cluster-level** (all **spec-confirmed (9.0)**, `moId` `vsan-cluster-health-system`):
  `VsanVcClusterHealthSystem_VsanQueryVcClusterHealthSummary` (and the `...Task` variant),
  `..._VsanQueryAllSupportedHealthChecks`, `..._VsanQueryClusterHistoricalHealth`,
  `..._VsanHealthQueryVsanClusterHealthConfig`, `..._VsanHealthGetVsanClusterSilentChecks`
  / `..._VsanHealthSetVsanClusterSilentChecks` (silenced checks hide real failures — check
  what has been silenced before trusting a green summary),
  `..._VsanVcUpdateHclDbFromWeb` / `..._VsanVcUploadHclDb` / `..._VsanPurgeHclFiles`
  (online and air-gapped HCL refresh).

**9.1 difference:** every operation in this section exists in 9.1 with the same path and
`operationId`. 9.1 additionally introduces `DataProtectionHealthSystem` (`moId`
`dp-health-system`, 4 operations) for snapshot/replication health — **no 9.0 equivalent**.

### P6 — Caller privilege `[9.0]` — partially spec-declared, treat as indicative

`SPECVIJ` declares a `***Required privileges:***` line per operation. Verified samples
(identical annotations at both tags for operations that exist in both):

| Operation | Declared privilege |
|---|---|
| `VsanVcClusterConfigSystem_VsanClusterGetConfig` | `System.Read` |
| `VsanVcClusterConfigSystem_VsanValidateConfigSpec` | `Global.Diagnostics` |
| `VsanSpaceReportSystem_VsanQuerySpaceUsage` | `System.Read` |
| `VsanRemoteDatastoreSystem_RemoteVcMountPrecheck` | `Host.Config.Storage` |
| `VSANVcConvertToStretchedCluster` → `cluster` parameter | `Host.Inventory.EditCluster` |

> **Do not present this as an authoritative privilege model.** Several write operations —
> `VsanClusterReconfig`, `VosSetVsanObjectPolicy`, `VSANVcConvertToStretchedCluster` at the
> operation level, `VSANVcAddWitnessHost` — declare **no** privilege at all, and
> `VSANVcSetPreferredFaultDomain` declares `VApp.Clone`, which is implausible for a vSAN
> fault-domain operation and looks like a spec-generation artifact. Use the table to size a
> role request, then confirm empirically against a non-production vCenter.
>
> **The SDDC Manager side is `UNVERIFIED` entirely.** No retrieved source names the role
> required for SDDC Manager write operations such as `updateCluster`, and SDDC Manager is
> excluded from VCF SSO [DAUTH], so VCF roles do not govern it.

**9.1 difference:** the same annotations, plus new ones on the 9.1-only site-maintenance
operations (`System.Read` for the precheck, `Host.Config.Storage` to enter).

### P7 — Items the sources could not establish — state these as gaps

- **Which architecture (ESA or OSA) is the default.** See P1. Unresolved in docs and specs.
- **The ESA hardware requirement list.** See P4. Verification route only.
- **Numeric capacity headroom for policy / RAID / disk changes.** See P3.
- **Stretched-cluster operational limits** — witness sizing, inter-site latency and
  bandwidth, hosts per site. See P2.
- **Whether OSA is deprecated.** No retrieved page says so; both witness appliances ship in
  the 9.0 BOM [DVS gap 8]. Do not imply an OSA end-of-life.
- **`ClusterUpdateSpec.prepareForStretch`** — the field exists with a one-line description
  and no explanation of when it is required versus optional.
- **Which vSAN objects a given policy change will resync, and for how long.** No source
  models this. It is measurable at runtime (`QuerySyncingVsanObjectsSummary`), not
  predictable from these sources.

---

## SDDC Manager surface — vSAN operations

All **spec-confirmed (9.0)** against `SPECSDDC`. Base `https://<sddc-manager>/v1`. There are
exactly **10** operations whose path or `operationId` mentions vSAN, plus the cluster update
pair that carries the stretch spec.

**Stretch / unstretch — carried in the body of the generic cluster update:**
```
PATCH /v1/clusters/{id}                              updateCluster
POST  /v1/clusters/{id}/validations                  validateClusterUpdateSpec   (dry run)
GET   /v1/clusters/{id}/validations/{validationId}   getClusterUpdateValidation
GET   /v1/tasks/{id}                                 (poll)
```
`updateCluster`'s own summary names it: *"Update a Cluster by adding or removing Hosts,
**Stretching a standard vSAN cluster, Unstretching a stretched cluster** or by marking for
deletion."* There is no `/stretch` path — searching for one is the single most common wrong
turn here. `SPECSDDC` contains **zero** paths matching `stretch` at either version.

**Remote vSAN datastore (HCI mesh) mounts:**
```
GET    /v1/clusters/{id}/datastores                      getClusterDatastores
POST   /v1/clusters/{id}/datastores                      addDatastoreToCluster    (body DatastoreMountSpec, returns Task)
POST   /v1/clusters/{clusterId}/datastores/validations   validateVsanRemoteDatastoreMountSpec
DELETE /v1/clusters/{id}/datastores/{datastoreId}        removeDatastoreFromCluster
POST   /v1/clusters/{clusterId}/datastores/validation    validateVsanRemoteDatastoreSpec   <- DEPRECATED already in 9.0
GET    /v1/clusters/{clusterId}/datastores/queries/{queryId}   getDatastoreQueryResponse_1
POST   /v1/clusters/{id}/datastores/queries              postDatastoreQuery_1
GET    /v1/clusters/{id}/datastores/criteria[/{name}]    getDatastoresCriteria_1 / getDatastoreCriterion_1
```
The singular-`validation` form carries `deprecated: true` in `SPECSDDC` **9.0** — it was
already deprecated at this version, not deprecated later. Use the plural `validations`.
There is **no** `GET /v1/clusters/{id}/datastores/validations/{validationId}` in 9.0; that
retrieval operation (`getDatastoreMountValidation`) is **9.1-only** [DELTA], so in 9.0 the
mount-validation result comes back from the `POST` itself.

`DatastoreMountSpec` → `DatastoreSpec` → `vsanRemoteDatastoreClusterSpec`
(`isStretched`, `primaryAzName`, `vsanRemoteDatastoreSpec[]`), each entry carrying
`datastoreUuid` (required), `networkTopology` ("Symmetric/Asymmetric based on configuration
of stretched server/client cluster") and `siteAffinity[]` (`serverSite` required,
`clientSite`). **`encryptionConfig` does not exist at 9.0** — it is a 9.1 addition.

**vSAN health and HCL:** see P5 — `getVsanHealthCheckByDomain`,
`getVsanHealthCheckByQueryID`, `getVsanHealthCheckByTaskID`, `updateVsanHealthCheckByDomain`,
`downloadVsanHcl`, `getVsanHclConfiguration`, `updateVsanHclConfiguration`,
`getVsanHclAttributes`.

**vSAN configuration at cluster creation** (`POST /v1/clusters`, `createCluster`, and
`POST /v1/clusters/validations`, `validateClusterCreationSpec` — both **spec-confirmed
(9.0)**; cluster creation itself belongs to `vcf-domains-clusters`, listed here only because
the vSAN fields live in its body):
`DatastoreSpec.vsanDatastoreSpec` → `VsanDatastoreSpec` with `datastoreName`
(**required in 9.0**; 9.1 relaxes it to optional for management-domain deployment),
`failuresToTolerate` (*"required for vSAN OSA configuration"*), `licenseKey`,
`dedupAndCompressionEnabled` (*"only available for clusters in which the hosts are all
flash"*), and `esaConfig` (`enabled` **required**, optional `vsanMaxConfig` with
`enableVsanMax` / `enableVsanExternalNetwork`).

**Not available in 9.0** (all 9.1 additions [DELTA]): `PATCH /v1/clusters`
(`updateClusters`), `ClusterUpdateSpec.clusterPrimaryDatastoreUpdateSpec`,
`ClusterUpdateSpec.markAsDefault`, `ClusterUpdateSpec.dnsNtpUpdateSpec`,
`getDatastoreMountValidation`, `ClusterUnstretchSpec.azToRemove`,
`VsanDatastoreSpec.encryptionConfig`, `POST /v1/clusters/{clusterId}/remediations`.

---

## Stretching a cluster in 9.0

The sequence and the payload are the same as 9.1: **validate → execute → poll**, with
`clusterStretchSpec` in the body of `ClusterUpdateSpec`.

```
POST  /v1/clusters/{id}/validations                  validateClusterUpdateSpec
GET   /v1/clusters/{id}/validations/{validationId}   getClusterUpdateValidation
PATCH /v1/clusters/{id}                              updateCluster            -> Task
GET   /v1/tasks/{id}                                 poll to SUCCESSFUL
```
All four **spec-confirmed (9.0)**.

**The annotated payload, the field-by-field notes and the post-execution confirmation steps
are in `../9.1/vsan.md` → *Worked example — stretch a cluster via SDDC Manager*.** They apply
verbatim here: `ClusterStretchSpec`, `WitnessSpec`, `ClusterStretchNetworkSpec`,
`NsxStretchClusterSpec`, `StretchClusterNetworkProfile` and `HostSpec` are **byte-identical
at the 9.0.0.0 and 9.1.0.0 tags** (verified by diffing the two `sddc-manager-openapi.json`
schema blocks).

Two things that differ in 9.0, and only these two:
- **`ClusterUnstretchSpec` is an empty object** — there is no `azToRemove`. Unstretching in
  9.0 takes no parameters.
- **`getHosts` filters are narrower.** 9.0 offers `fqdn`, `status`, `domainId`, `clusterId`,
  `networkpoolId`, `storageType`, `datastoreName` and the deprecated `size` / `page` pair.
  There is **no** `isVsanWitnessHost` filter in 9.0 — find witness hosts through
  `VimClusterVsanVcStretchedClusterSystem_VSANVcIsWitnessHost` on the VI-JSON surface
  instead.

`validateClusterUpdateSpec` accepts `useAsyncValidation` in 9.0 as well.

---

## VI-JSON surface — the vSAN management API

Base: `https://<vcenter-host>/sdk/vim25/{release}`. Nearly every vSAN operation is a **POST**
to `/vsan/{ManagedObject}/{moId}/{Operation}` with a `{Operation}RequestType` body, plus a
handful of property GETs.

Counting precisely: **285** operations sit under the `/vsan/` prefix at 9.0, plus **15**
`HostVsanInternalSystem` operations at the top level (not under `/vsan/`) and one vSAN-named
`/pbm` operation — **301** vSAN-matching operations. All **spec-confirmed (9.0)** against
`SPECVIJ`.

**The `moId` is a well-known singleton, not something you look up.** From the spec's own
managed-object descriptions:

| Managed object | `moId` | Ops (9.0) |
|---|---|---|
| `VsanVcClusterConfigSystem` | `vsan-cluster-config-system` | 8 |
| `VsanVcClusterHealthSystem` | `vsan-cluster-health-system` | 44 |
| `VimClusterVsanVcStretchedClusterSystem` | `vsan-stretched-cluster-system` | 13 |
| `VimClusterVsanVcDiskManagementSystem` | `vsan-disk-management-system` | 12 |
| `VsanRemoteDatastoreSystem` | `vsan-remote-datastore-system` | 8 |
| `VsanSpaceReportSystem` | `vsan-cluster-space-report-system` | 3 |
| `VsanObjectSystem` | `vsan-cluster-object-system` | 7 |
| `VsanResourceCheckSystem` | `vsan-cluster-resource-check-system` (vCenter) / `vsan-resource-check-system` (host) | 4 |
| `VsanCapabilitySystem` | `vsan-vc-capability-system` (vCenter) / `vsan-capability-system` (host) | 1 |
| `VsanClusterPowerSystem` | `vsan-cluster-power-system` | 3 |
| `VsanFileServiceSystem` | `vsan-cluster-file-service-system` (vCenter) / `vsan-file-service-system` (host) | 17 |
| `VsanIscsiTargetSystem` | `vsan-cluster-iscsi-target-system` | 23 |
| `CnsVolumeManager` | `cns-volume-manager` | 13 |
| `VsanPerformanceManager` | `vsan-performance-manager` | 22 |
| `VsanDiagnosticsSystem` | `vsan-cluster-diagnostics-system` | 11 |
| `VsanIoInsightManager` | `vsan-cluster-ioinsight-manager` (vCenter) / `vsan-ioinsight-manager` (host) | 5 |
| `VsanUpgradeSystemEx` | `vsan-upgrade-systemex` | 5 |
| `VsanSystemEx` | `vsanSystemEx` (ESX host) | 10 |
| `HostVsanHealthSystem` | `ha-vsan-health-system` (ESX host) | 26 |

Also present without a spec-stated singleton `moId`: `HostVsanSystem` (11, host-level),
`VsanClusterHealthSystem` (11), `VsanUpgradeSystem` (3), `HostVsanInternalSystem` (15, not
under `/vsan/`), `VsanVdsSystem` (4), `VsanHostVdsSystem` (2), `VsanUpdateManager` (3),
`VsanVumSystem` (4), `VsanPhoneHomeSystem` (6), `VsanMassCollector` (1),
`VsanClusterMgmtInternalSystem` (2), `VsanVcsaDeployerSystem` (3,
`vsan-vcsa-deployer-system`).

**Two managed objects do NOT exist in 9.0** and are 9.1-only [DELTA]:
`VsanSiteMaintenanceSystem` (site maintenance mode) and `DataProtectionHealthSystem`. If a
9.0 caller asks for site maintenance mode, the answer is that the API does not exist at this
version.

### Cluster configuration — `VsanVcClusterConfigSystem` (8 ops in 9.0)

```
VsanClusterGetConfig            read the current vSAN config          System.Read
VsanClusterReconfig             apply a VimVsanReconfigSpec           (no privilege declared)
VsanValidateConfigSpec          validate a spec without applying      Global.Diagnostics
VsanClusterGetClaimedCapacity   claimed capacity
VsanClusterGetRuntimeStats      runtime stats
VsanQueryClusterDrsStats        DRS interaction stats
VsanEncryptedClusterRekey_Task  rekey an encrypted cluster
RunLifecycleCheck               lifecycle check
```
`VsanGetClusterRAIDInfo` and `VsanGetConfigurationLimits` are **9.1-only** — do not offer
them for 9.0.

`VsanClusterReconfigRequestType` requires `cluster` (a `ClusterComputeResource`
`ManagedObjectReference`) and `vsanReconfigSpec` (`VimVsanReconfigSpec`), whose members are
`vsanClusterConfig`, `dataEfficiencyConfig`, `diskMappingSpec`, `faultDomainsSpec`, `modify`
and `allowReducedRedundancy`.

`modify` is the field to get right: *"If `modify` is false and the operation succeeds, then
the configuration of the vSAN cluster matches the specification exactly; in this case any
unset portions of the specification will result in unset or default portions of the
configuration."* Sending a partial spec with `modify: false` resets everything you omitted.

**Dedup and compression** live in `VsanDataEfficiencyConfig` (`dedupEnabled` required,
`compressionEnabled`) and its extension `VsanDataEfficiencyConfigEx` (`dedupStoreUuid`,
`dedupPaused`). Both schemas already exist at 9.0. The 9.1 spec adds the sentence *"For vSAN
ESA, compression is enabled by default since 9.1.0 release, disabling compression is not
supported"* — **that sentence is absent at 9.0**, so do not carry the 9.1 compression
behavior backwards.

### Stretched clusters — `VimClusterVsanVcStretchedClusterSystem` (13 ops, `[9.0+9.1]`)

```
VSANVcConvertToStretchedCluster        convert a standard vSAN cluster to stretched
VSANVcAddWitnessHost                   add a witness
VSANVcRemoveWitnessHost                remove a witness
VSANVcGetWitnessHosts                  list witnesses
VSANVcIsWitnessHost                    is this host a witness?
VSANIsWitnessVirtualAppliance          is it the witness appliance form?
VSANVcGetPreferredFaultDomain          read the preferred FD
VSANVcSetPreferredFaultDomain          set the preferred FD
VSANVcRetrieveStretchedClusterVcCapability   what this vCenter supports
QuerySharedWitnessCompatibility        can these clusters share a witness?
QuerySharedWitnessClusterInfo          shared-witness cluster info
VsanVcAddWitnessHostForClusters        add one witness to several clusters
VsanVcReplaceWitnessHostForClusters    replace a shared witness
```

`VSANVcConvertToStretchedClusterRequestType` requires `cluster`, `faultDomainConfig`,
`witnessHost` and `preferredFd`; optional `diskMapping` (OSA-style, *"If disk claim is
configured as auto-mode on witness host, this parameter is not required"*) or
`storagePoolSpec` (ESA-style) — *"This parameter cannot be set together with `diskMapping`"*.

**Prefer the SDDC Manager path in a VCF estate.** SDDC Manager orchestrates host
commissioning and the NSX side that the raw VI-JSON call does not. Use VI-JSON for
inspection, for shared-witness queries, and for clusters SDDC Manager does not own.

### Disks, storage pools and fault domains — `VimClusterVsanVcDiskManagementSystem` (12)

```
InitializeDiskMappings            QueryDiskMappings              RebuildDiskMapping
RemoveDiskEx                      RemoveDiskMappingEx            UnmountDiskMappingEx
QueryVsanManagedDisks             RetrieveAllFlashCapabilities
QueryClusterDataEfficiencyCapacityState
VsanAddStoragePoolDisk            VsanDeleteStoragePoolDisk      VsanUnmountStoragePoolDisks
```
Disk *groups* (`...DiskMapping...`) are the OSA model; *storage pools*
(`Vsan*StoragePoolDisk*`) are the ESA model. Both families exist at 9.0. Host-level
equivalents are on `HostVsanSystem` (`AddDisks_Task`, `InitializeDisks_Task`,
`RemoveDisk_Task`, `RemoveDiskMapping_Task`, `UnmountDiskMapping_Task`,
`EvacuateVsanNode_Task`, `RecommissionVsanNode_Task`, `QueryDisksForVsan`,
`QueryHostStatus`, `UpdateVsan_Task`, `GET .../config`).

### Objects, health, performance, space

```
VsanObjectSystem       VosQueryVsanObjectInformation, VosSetVsanObjectPolicy,
                       RelayoutObjects, VsanDeleteObjects_Task, VsanQueryObjectIdentities,
                       QuerySyncingVsanObjectsSummary, VsanQueryInaccessibleVmSwapObjects
                       (VsanQueryPhysicalPlacements is 9.1-only)
VsanSpaceReportSystem  VsanQuerySpaceUsage, VsanQueryEntitySpaceUsage,
                       QueryVsanManagedStorageSpaceUsage
VsanPerformanceManager 22 ops incl. VsanPerfQueryPerf, VsanPerfDiagnose,
                       QueryVsanPerfTopEntities, QueryVsanPerfHotspotEntities
                       (VsanPerfGetSupportedHotspotEntityTypes is 9.1-only)
VsanClusterPowerSystem PerformClusterPowerAction, QueryClusterPowerContext,
                       UpdateClusterPowerStatus
VsanUpgradeSystemEx    PerformVsanUpgradeEx, PerformVsanUpgradePreflightCheckEx,
                       PerformVsanUpgradePreflightAsyncCheck_Task,
                       RetrieveSupportedVsanFormatVersion, VsanQueryUpgradeStatusEx
```
`VosSetVsanObjectPolicy` is the per-object policy override — it changes layout and starts a
resync. It declares no privilege in the spec.

### Remote datastores / HCI mesh — `VsanRemoteDatastoreSystem` (8, `[9.0+9.1]`)

```
VsanQueryHciMeshDatastores      VsanQueryDatastoreSource
VsanCreateDatastoreSource       VsanUpdateDatastoreSource      VsanDestroyDatastoreSource
VsanPrecheckDatastoreSource     MountPrecheck
RemoteVcMountPrecheck           Host.Config.Storage — mount across vCenter boundaries
```
Note `RemoteVcMountPrecheck` **already exists at 9.0**, which is why 9.1's "stretched storage
across vCenter instances" cannot be attributed to a new operation.

### File services, iSCSI, CNS

`VsanFileServiceSystem` (17): `VsanClusterCreateFsDomain`, `VsanClusterReconfigureFsDomain`,
`VsanClusterRemoveFsDomain`, `VsanCreateFileShare`, `VsanReconfigureFileShare`,
`VsanClusterRemoveShare`, `VsanClusterQueryFileShares`, share snapshots,
`VsanPerformFileServiceEnablePreflightCheck`, OVF discovery/download, `VsanUpgradeFsvm`,
`VsanRebalanceFileService`. vSAN 9.0 supports "up to 500 file shares per cluster" [DVS §7].

`VsanIscsiTargetSystem` (23): the `VsanVit*` target / LUN / initiator-group family.

`CnsVolumeManager` (13): `CnsCreateVolume`, `CnsDeleteVolume`, `CnsAttachVolume`,
`CnsDetachVolume`, `CnsExtendVolume`, `CnsRelocateVolume`, `CnsReconfigVolumePolicy`,
`CnsCreateSnapshots`, `CnsDeleteSnapshots`, `CnsQueryVolume`, `CnsQueryAsync`,
`CnsUpdateVolumeMetadata`, `CnsConfigureVolumeACLs`. `CnsSyncVolume`, `CnsUnregisterVolume`
and `CnsUpdateVolumeCrypto` are **9.1-only**.

---

## Storage policies — two surfaces, one concept

vSAN storage policies are SPBM policies. **Authoring is VI-JSON `/pbm/...`; reading and
compliance are split across VI-JSON and vSphere Automation.** Both are needed for most real
tasks, and neither is on the "vSAN" surface.

**Authoring / management — VI-JSON `/pbm/PbmProfileProfileManager/{moId}/...`**, all
**spec-confirmed (9.0)**:
```
PbmCreate                          PbmUpdate                     PbmDelete
PbmQueryProfile                    PbmRetrieveContent
PbmFetchCapabilityMetadata         PbmFetchCapabilitySchema      PbmFetchResourceType
PbmQueryAssociatedEntity(-ies)     PbmQueryAssociatedProfile(s)
PbmAssignDefaultRequirementProfile PbmQueryDefaultRequirementProfile(s)
PbmResetDefaultRequirementProfile  PbmResetVSanDefaultProfile
PbmFindApplicableDefaultProfile    PbmQuerySpaceStatsForStorageContainer
PbmFetchVendorInfo
```
`PbmResetVSanDefaultProfile` is the only `/pbm` operation whose name mentions vSAN.

**Compliance — VI-JSON `/pbm/PbmComplianceManager/{moId}/...`** (**spec-confirmed (9.0)**):
`PbmCheckCompliance`, `PbmCheckRollupCompliance`, `PbmFetchComplianceResult`,
`PbmFetchRollupComplianceResult`, `PbmQueryByRollupComplianceStatus`.

**Placement / compatibility — VI-JSON `/pbm/PbmPlacementSolver/{moId}/...`**:
`PbmCheckCompatibility`, `PbmCheckCompatibilityWithSpec`, `PbmCheckRequirements`,
`PbmQueryMatchingHub`, `PbmQueryMatchingHubWithSpec`. Entry point:
`PbmServiceInstance_PbmRetrieveServiceContent` / `GET /pbm/PbmServiceInstance/{moId}/content`.

**Read + per-VM assignment — vSphere Automation `/api/vcenter/...`**, all **spec-confirmed
(9.0)** against `SPECAUTO`:
```
GET   /api/vcenter/storage/policies                             Vcenter.Storage.Policies_list
POST  /api/vcenter/storage/policies/{policy}?action=check-compatibility
                                                                Vcenter.Storage.Policies_checkCompatibility
GET   /api/vcenter/storage/policies/{policy}/vm                 Vcenter.Storage.Policies.VM_list
GET   /api/vcenter/storage/policies/compliance/vm               Vcenter.Storage.Policies.Compliance.VM_list
GET   /api/vcenter/storage/policies/entities/compliance         Vcenter.Storage.Policies.Compliance_list
GET   /api/vcenter/vm/{vm}/storage/policy                       Vcenter.Vm.Storage.Policy_get
PATCH /api/vcenter/vm/{vm}/storage/policy                       Vcenter.Vm.Storage.Policy_update
GET   /api/vcenter/vm/{vm}/storage/policy/compliance            Vcenter.Vm.Storage.Policy.Compliance_get
POST  /api/vcenter/vm/{vm}/storage/policy/compliance?action=check
                                                                Vcenter.Vm.Storage.Policy.Compliance_check
GET   /api/vcenter/datastore/{datastore}/default-policy         Vcenter.Datastore.DefaultPolicy_get
```
Note the exact paths: `.../storage/policies/entities/compliance` and
`.../storage/policies/compliance/vm` — not `/storage/policies/compliance` on its own.

**Changing a policy on a populated vSAN cluster is a resync.** `PbmUpdate` on a profile
applies to every object bound to it. Run `PbmCheckCompatibility` / `checkCompatibility`
first, and P3's capacity checks before that.

**9.1 difference:** the `/pbm` families and these ten vSphere Automation operations are
identical in 9.1. 9.1 adds four Supervisor storage-policy operations under
`/api/vcenter/namespace-management/supervisors/{supervisor}/{control-plane,workloads}/storage/policies`
with no 9.0 equivalent.

---

## vSAN Data Protection (snapservice) surface

Base `https://<host>/api`, spec title *Snapshot Appliance API*, spec version `9.0.0.0`,
**48 operations**. The `{host}` is the Data Protection appliance, not vCenter:
`Snapservice.Sites.AddSpec` carries both a `vcenter_certificate` and a separate
`va_certificate` — *"Certificate of the remote Data Protection Virtual Appliance"*.

Conventions that differ from every other surface here: dotted `operationId`s
(`Snapservice.X_verb`), `?vmw-task=true` to run an operation as a task, `?action=<verb>` for
custom actions, and snake_case body properties.

**Sessions, info, tasks:**
```
POST   /api/snapservice/sessions          Snapservice.Sessions_create
GET    /api/snapservice/sessions          Snapservice.Sessions_get
DELETE /api/snapservice/sessions          Snapservice.Sessions_delete
GET    /api/snapservice/info/about        Snapservice.Info.About_get
GET    /api/snapservice/tasks             Snapservice.Tasks_list
GET    /api/snapservice/tasks/{task}      Snapservice.Tasks_get
```

**Sites:**
```
GET    /api/snapservice/sites                              Snapservice.Sites_list
GET    /api/snapservice/sites/{site}                       Snapservice.Sites_get
POST   /api/snapservice/sites?action=probe                 Snapservice.Sites_probe
POST   /api/snapservice/sites?action=add&vmw-task=true     Snapservice.Sites_add$Task
PATCH  /api/snapservice/sites/{site}?vmw-task=true         Snapservice.Sites_update$Task
DELETE /api/snapservice/sites/{site}?vmw-task=true         Snapservice.Sites_delete$Task
GET    /api/snapservice/sites/{site}/clusters              Snapservice.Sites.Clusters_list
GET    /api/snapservice/sites/{site}/licenses              Snapservice.Sites.Licenses_list
```
`Snapservice.Sites.AddSpec` requires `vcenter_connection_spec`; `vcenter_creds` is nominally
optional but the spec states *"API is expected to throw validation error if vCenter
credentials are not supplied"* — treat it as required. Probe first
(`Sites_probe` → `Snapservice.Sites.ProbeResult`) to obtain and check certificates.
**No `capabilities` or `datastores` sub-resources exist at 9.0** — all six are 9.1 additions.

**Cluster pairs:**
```
GET    /api/snapservice/cluster-pairs                      Snapservice.ClusterPairs_list
GET    /api/snapservice/cluster-pairs/{cp}                 Snapservice.ClusterPairs_get
POST   /api/snapservice/cluster-pairs?action=create-precheck            Snapservice.ClusterPairs_createPrecheck
POST   /api/snapservice/cluster-pairs?action=create-precheck&vmw-task=true
                                                           Snapservice.ClusterPairs_createPrecheck$Task
POST   /api/snapservice/cluster-pairs?vmw-task=true        Snapservice.ClusterPairs_create$Task
DELETE /api/snapservice/cluster-pairs/{cp}?vmw-task=true   Snapservice.ClusterPairs_delete$Task
```
`CreateSpec` requires `local_cluster` and `peer_cluster`; *"In the first release the peer
cluster must be from a remote site."* Note the precheck-then-create shape — the same
validate-first discipline as SDDC Manager.

**Protection groups** — note that in 9.0 **every** protection-group path is
cluster-scoped:
```
GET    /api/snapservice/clusters/{cluster}/protection-groups            Snapservice.Clusters.ProtectionGroups_list
GET    /api/snapservice/clusters/{cluster}/protection-groups/{pg}       ..._get
POST   /api/snapservice/clusters/{cluster}/protection-groups?vmw-task=true              ..._create$Task
PATCH  /api/snapservice/clusters/{cluster}/protection-groups/{pg}?vmw-task=true         ..._update$Task
DELETE /api/snapservice/clusters/{cluster}/protection-groups/{pg}?vmw-task=true         ..._delete$Task
POST   .../protection-groups/{pg}?action={pause|resume|activate|demote|promote}&vmw-task=true
```
The top-level `/api/snapservice/protection-groups/...` family — `computeMembers`,
`capabilities`, `startRansomwareRecovery`, `endRansomwareRecovery` — **does not exist in
9.0**. Ransomware recovery has no 9.0 API.

`Snapservice.ProtectionGroupSpec` requires `name` and `target_entities`; optional
`snapshot_policies[]` (*"if missing or null local protection will be skipped"*),
`replication_policies[]`, and `locked` (*"A locked protection group cannot be modified or
deleted by the user. All snapshots associated with the protection group will be secure and
cannot be deleted."* — a one-way door; the system deletes them on expiry).
`SnapshotPolicy` requires `name`, `schedule` and `retention`. In 9.0
`Snapservice.SnapshotSchedule.unit` and `RetentionPeriod.unit` accept `MINUTE`, `HOUR`,
`DAY`, `WEEK`, `MONTH` — **`YEAR` is 9.1-only**, as are the
`Daily`/`Weekly`/`Monthly`/`Hourly`/`LongTermRetention` schemas.

**Snapshots** — cluster-scoped only in 9.0:
```
GET    /api/snapservice/clusters/{cluster}/protection-groups/{pg}/snapshots            ..._list
GET|DELETE .../protection-groups/{pg}/snapshots/{snapshot}                             ..._get / ..._delete
POST   .../protection-groups/{pg}/snapshots?vmw-task=true                              ..._create$Task
GET    /api/snapservice/clusters/{cluster}/virtual-machines                            ..._list
GET    .../virtual-machines/{vm}/snapshots[/{snapshot}]                                ..._list / ..._get
POST   .../virtual-machines/{vm}?action={restore|revert|linked-clone}&vmw-task=true
```
The global `/api/snapservice/virtual-machines/snapshots` family with labels
(`add-label`, `delete-label`, `set-labels`) and
`/api/snapservice/virtual-machines/{vm}/protection-configuration` are **9.1-only**.

**Reports** (8 operations): `/api/snapservice/reports/clusters/{cluster}/...` for protection
groups, VMs, their snapshots, and `snapshot-status-counts` aggregated by
`?aggregateBy=protection-group`, `time-slice` or `virtual-machine`. Unchanged in 9.1.

---

## What vSAN 9.0 shipped

From the 9.0 vSAN what's-new page [DVS §7]:

- "Disaster Recovery for vSAN clusters using VMware Live Recovery" — host-based VM
  replication, RPO as low as 1 minute.
- "vSAN Licensing via VCF Operations" — allocate vSAN TiB entitlements through VCF Operations.
- "Support of Stretched Compute-only Clusters with vSAN storage clusters" — this is the
  9.0 capability behind `VsanRemoteDatastoreClusterSpec.isStretched` / `primaryAzName` on
  the SDDC Manager mount path.
- "Support for client traffic separation with vSAN storage clusters" — dedicated VMkernel
  ports separating external VM traffic from internal storage traffic.
- "Support of up to 500 file shares per cluster in vSAN File Services".
- "Dying Disk Handling (DDH) supports Cache Drives" — proactive detection in OSA, latency
  monitoring in ESA.

**The 9.0 what's-new page does not list global deduplication, storage-policy changes, or
capacity-reporting changes** [DVS §7]. Do not attribute 9.1 vSAN features to 9.0.

**Both architectures ship.** vSAN ESA Witness (`9.0.0.0` / `24755427`) and vSAN OSA Witness
(`9.0.0.0` / `24755428`) are both in the 9.0 BOM, along with vSAN File Services
(`9.0.0.0` / `24755229`) [DVS §1].

**vSAN-relevant 9.0 deprecations** [DVS §5]: the vSAN **.NET / Perl / Ruby management SDKs**
are "officially deprecated". Separately, `vVols` is deprecated and vSphere Lifecycle Manager
**baselines are removed for cluster management** in vCenter 9.0 — relevant because vSAN
clusters are vLCM-image-managed from 9.0 onward.

---

## Spec-vs-prose discrepancies found while writing this file

1. **`WitnessSpec.fqdn` is described as "Management ip of the witness host."** Field name and
   description disagree, at both 9.0 and 9.1. Supply the FQDN; note the ambiguity if a caller
   reports a validation failure on that field.
2. **Privilege annotations are inconsistent.** See P6 — several vSAN write operations declare
   none, and `VSANVcSetPreferredFaultDomain` declares `VApp.Clone`. The annotations are real
   spec content but are not a usable privilege model on their own.
3. **The SDDC Manager spec's declared base is `http://localhost:80`.** That is a build
   artifact in `SPECSDDC` at both versions. The load-bearing part is the `/v1` prefix;
   substitute the real SDDC Manager host over HTTPS.
4. **The vSAN Management API is documented as SOAP/vmodl.** The Broadcom reference describes
   it as a SOAP/vmodl web service on `/vsanHealth` (vCenter), `/vsan` (host) and `/sdk`
   (legacy MOs) [DVS §B]. The **VI-JSON spec exposes the same managed objects over HTTP/JSON**
   under `/sdk/vim25/{release}/vsan/...`, which is what this file documents because it is the
   machine-verifiable surface. Both descriptions are correct; they are two transports over
   one object model. Note the 9.0 release notes also state vCenter 9.0 "adds OpenAPI 3.0 to
   support all vCenter **and vSAN** APIs" [DVS §4], which is consistent with the VI-JSON spec
   carrying the whole vSAN object model.
5. **`validateVsanRemoteDatastoreSpec` is already deprecated at 9.0.** It is easy to read the
   9.0→9.1 delta and assume it was deprecated in 9.1; it was not. Both the singular and plural
   forms exist at 9.0, with the singular flagged.
6. **`prepareForStretch` is undocumented.** The field exists on `ClusterUpdateSpec` at 9.0 with
   a one-line description and no explanation of when it is required. `UNVERIFIED`.
