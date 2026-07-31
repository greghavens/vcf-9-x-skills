# VCF 9.1 — vSAN Storage Reference

**Scope:** vSAN in VMware Cloud Foundation 9.1.0.0 (release notes dated 12 MAY 2026).
Everything here is `[9.1]` unless explicitly tagged otherwise.

**Sources.**
`DVS` = `research/vsphere-vcenter-vsan.md`; `DAUTH` = `research/foundation-auth-identity.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine diff of git tags `9.0.0.0`
and `9.1.0.0` of `github.com/vmware/vcf-api-specs`).
Machine-extracted operation inventories:
`SPECSDDC` = `9.1__sddc-manager.ops.json` (**423** ops, spec version `9.1.0.0`);
`SPECVIJ` = `9.1__vsphere-vi-json.ops.json` (**2243** ops, of which **317** are vSAN);
`SPECDP` = `9.1__vsan-data-protection.ops.json` (**65** ops, spec version `9.1.0.0`);
`SPECAUTO` = `9.1__vsphere-automation.ops.json` (**1367** ops).
Raw schemas quoted below come from the `9.1.0.0` tag of the same repository.

Every endpoint is cited with its **`operationId`** and marked **spec-confirmed (9.1)**
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
- [Worked example — stretch a cluster via SDDC Manager](#worked-example--stretch-a-cluster-via-sddc-manager)
- [VI-JSON surface — the vSAN management API](#vi-json-surface--the-vsan-management-api)
- [Storage policies — two surfaces, one concept](#storage-policies--two-surfaces-one-concept)
- [vSAN Data Protection (snapservice) surface](#vsan-data-protection-snapservice-surface)
- [What 9.1 added, and how much of it is visible in the API](#what-91-added-and-how-much-of-it-is-visible-in-the-api)
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
      storage pools, fault domains, witness hosts, site maintenance, health,
      performance, space reporting, file services, iSCSI, CNS, diagnostics
      POST-only RPC. moId is a singleton string like 'vsan-cluster-config-system'.
      Body schema is {Operation}RequestType.

vSAN Data Protection   https://<dp-appliance>/api/snapservice/...
  └── vSAN native snapshots, protection groups, snapshot/replication policies,
      cluster pairs, sites, ransomware recovery
      REST. operationIds are dotted (Snapservice.X_verb). ?vmw-task=true.

vSphere Automation     https://<vcenter>/api/vcenter/...
  └── ZERO vSAN operations. Spec-confirmed absence in SPECAUTO (9.1).
      Only relevant piece: the read/compliance half of storage policies.
```

**The absence is load-bearing.** `SPECAUTO` (9.1, 1367 ops) contains **no path or
operationId matching `vsan`**, and **no path matching `stretch`**. Its two `witness`
operations are `Vcenter.Vcha.Cluster.Witness_check` and
`Vcenter.Vcha.Cluster.Witness_redeploy$Task` — **vCenter High Availability**, unrelated to
vSAN. Do not offer them as vSAN witness management.

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what
must hold, **how to verify it**, the version it applies to, and whether 9.0 differs.

### P0 — Authentication `[9.1]`

**Must be true:** you hold a credential for each surface you will call. **vSAN has no
independent authentication of its own** — it reuses the vCenter session. The vSAN
Management APIs "depend on the vSphere Web Services API for login procedures"; authenticate
to vCenter and reuse that session [DAUTH]. `SPECVIJ` declares exactly one security scheme,
`Session`: an API key in the **`vmware-api-session-id`** header, *"returned by the `Login`
operation of the `SessionManager` interface"* — `POST /sdk/vim25/{release}/SessionManager/{moId}/Login`,
`operationId` `SessionManager_Login`, **spec-confirmed (9.1)**.

The other two surfaces have their own credentials:

| Surface | Scheme | Where the credential comes from |
|---|---|---|
| SDDC Manager | `Authorization: Bearer <accessToken>` | `POST /v1/tokens` — see `vcf-foundation` |
| VI-JSON (vSAN) | `vmware-api-session-id` header | vCenter session — see `vcf-foundation` |
| vSAN Data Protection | `SPECDP` declares three: `basic_auth`, `api_key_auth` (`vmware-api-session-id`), `federated_identity_auth` (HTTP bearer). Its own session op is `POST /api/snapservice/sessions`, `operationId` `Snapservice.Sessions_create`, **spec-confirmed (9.1)** — "the equivalent of login … exchanges user credentials supplied in the security context for a session token", returned in `vmware-api-session-id`. | see `vcf-foundation` |

**Do not build an auth flow from this file.** Go to `vcf-foundation`. The only vSAN-specific
fact is the one above: vSAN itself issues nothing.

**9.0 difference:** none. Identical security schemes at both tags in all three specs.

### P1 — Know the cluster's architecture and datastore type `[9.1]`

**Must be true:** you know whether the target cluster is ESA, OSA, vSAN Max, or a
compute-only client of a remote vSAN datastore, before you send anything that assumes one.
The payload fields differ — `failuresToTolerate` is documented as *"required for vSAN OSA
configuration"*, and `esaConfig` carries a **required** `enabled` boolean.

**How to verify:**
- SDDC Manager: `GET /v1/clusters` (`getClusters`) or `GET /v1/clusters/{id}` (`getCluster`),
  both **spec-confirmed (9.1)**. The `Cluster` schema returns `primaryDatastoreType`, whose
  documented example enumerates *"VSAN, VSAN_ESA, VSAN_MAX, NFS, FC, VVOL_FC, VVOL_ISCSI,
  VVOL_NFS, VSAN_REMOTE, VMFS, VVOL"*, plus `isStretched`, `failuresToTolerate`,
  `vsanClusterMode` and `hciMeshData`. `getClusters` also takes an `isStretched` query
  filter (**9.1 adds** `name`, `isDefault`, `isHciMeshEnabled`, `pageSize`, `pageNumber`,
  `useCache`).
- VI-JSON: `VsanVcClusterConfigSystem_VsanClusterGetConfig` (**spec-confirmed (9.1)**,
  privilege `System.Read`) on `moId` `vsan-cluster-config-system`.
- Capability probe: `VsanCapabilitySystem_VsanGetCapabilities` (**spec-confirmed (9.1)**),
  `moId` `vsan-vc-capability-system` at vCenter or `vsan-capability-system` on a host.

> **UNVERIFIED — which architecture is the default for a new cluster.** No retrieved
> Broadcom page states it; both ESA Witness and OSA Witness appliances ship in the 9.1 BOM
> and 9.1 explicitly supports mounting ESA and OSA clusters simultaneously [DVS §7, §1;
> DVS gap 8]. The specs do not settle it either: `EsaConfig.enabled` is a required boolean
> with **no declared default**. 9.1's "ESA Auto RAID-6" sets the default **RAID level** for
> ESA — `VsanAutoRAIDConfig.assumeAutoManagedRAID` is documented *"By default, it will be
> set to true for enabling ESA cluster and false for disabling ESA cluster"* — which is a
> per-field default, **not** a statement that ESA is the default architecture. Do not
> resolve this from memory.

**9.0 difference:** the `Cluster` schema and `primaryDatastoreType` enumeration are the same
at 9.0. 9.0's `getClusters` has only `isStretched`, `isImageBased`, `domainId`.

### P2 — Stretched clusters: witness host and exactly two fault domains `[9.1]`

**Must be true**, and both are stated in the specs rather than inferred:

1. **A witness host.** On the SDDC Manager path, `ClusterStretchSpec` marks `witnessSpec`
   **required**, and `WitnessSpec` requires all three of `fqdn` ("Management ip of the
   witness host"), `vsanIp`, `vsanCidr`.
   On the VI-JSON path, `VSANVcConvertToStretchedClusterRequestType` marks `witnessHost`
   **required** and constrains it: *"This host must be connected and managed by the same
   vCenter server, and cannot be a part of target cluster"*. The target cluster itself is
   *"expected to enable vSAN, but not a vSAN stretched cluster"*.
2. **Exactly two fault domains.** `VimVsanReconfigSpec.faultDomainsSpec` is documented: *"If
   `VimClusterVsanWitnessSpec` is specified which indicates it a stretched cluster, the fault
   domain list needs to include exactly two fault domain items."*

**How to verify, before you commit:**
- Is it already stretched? `GET /v1/clusters?isStretched=true` (`getClusters`,
  **spec-confirmed (9.1)**), or `VimClusterVsanVcStretchedClusterSystem_VSANVcGetWitnessHosts`
  (**spec-confirmed (9.1)**) on `moId` `vsan-stretched-cluster-system`.
- Is a candidate host actually a witness? `..._VSANVcIsWitnessHost`; is it the virtual
  appliance form? `..._VSANIsWitnessVirtualAppliance`. Both **spec-confirmed (9.1)**.
- Does this vCenter support the topology you want?
  `..._VSANVcRetrieveStretchedClusterVcCapability` (**spec-confirmed (9.1)**).
- Shared witness across clusters: `..._QuerySharedWitnessCompatibility` and
  `..._QuerySharedWitnessClusterInfo` (**spec-confirmed (9.1)**) before
  `..._VsanVcAddWitnessHostForClusters`.
- Dry-run the whole SDDC Manager spec: `POST /v1/clusters/{id}/validations`
  (`validateClusterUpdateSpec`) — see the worked example.

**9.0 difference:** none material. All 13 `VimClusterVsanVcStretchedClusterSystem`
operations exist at both tags, and `ClusterStretchSpec` / `WitnessSpec` /
`ClusterStretchNetworkSpec` / `NsxStretchClusterSpec` / `StretchClusterNetworkProfile` are
byte-identical at both tags. The one schema change is `ClusterUnstretchSpec`, which is an
empty object in 9.0 and gains an optional `azToRemove` in 9.1.

> **UNVERIFIED — the operational prerequisite list for stretched clusters.** Witness sizing,
> supported host counts per site, latency and bandwidth limits between sites, and the
> supported witness placement topologies are **not present in any retrieved source**. The
> schema constraints above are real; a full stretched-cluster readiness checklist is not
> derivable from these sources. Point at Broadcom's vSAN stretched-cluster guide for the
> customer's build.

### P3 — Capacity headroom before any policy, RAID or disk change `[9.1]`

**Must be true:** the cluster has enough free capacity to absorb the resync that a policy,
RAID-level, FTT, dedup/compression or disk-group change will start. The API accepts these
operations and *then* resyncs; there is no "would this fit?" gate built into the write call.

**How to verify (all VI-JSON, all spec-confirmed (9.1)):**
- `VsanResourceCheckSystem_VsanPerformResourceCheck` and
  `..._VsanGetResourceCheckStatus` on `moId` `vsan-cluster-resource-check-system` — the
  purpose-built pre-flight. Host-level equivalents: `..._VsanHostPerformResourceCheck`,
  `..._VsanHostCancelResourceCheck`.
- `VsanSpaceReportSystem_VsanQuerySpaceUsage` and `..._VsanQueryEntitySpaceUsage`
  (privilege `System.Read`) on `moId` `vsan-cluster-space-report-system`;
  `..._QueryVsanManagedStorageSpaceUsage`.
- `VsanVcClusterConfigSystem_VsanClusterGetClaimedCapacity` and
  `..._VsanGetConfigurationLimits` (**new in 9.1** — *"Returns configuration limits and
  supported values"*).
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

**9.0 difference:** all of the above exist at 9.0 except `VsanGetConfigurationLimits`, which
is **9.1-only** [DELTA].

### P4 — ESA hardware eligibility `[9.1]`

**Must be true:** for an ESA cluster, the devices are ESA-eligible.

**How to verify (all spec-confirmed (9.1)):**
- `VsanVcClusterHealthSystem_VsanGetHclInfoForEligibleDisks` — *"Fetch HCL information for
  all vSAN ESA eligible disks of the target"*.
- `VsanVcClusterHealthSystem_VsanGetDiskHclConstraints` and `..._VsanGetHclConstraints`.
- `VimClusterVsanVcDiskManagementSystem_QueryVsanManagedDisks`; the storage-pool API notes
  eligibility explicitly (`VsanAddStoragePoolDisk`, "*pool is eligible for vSAN ESA*").
- `VimClusterVsanVcDiskManagementSystem_RetrieveAllFlashCapabilities`.
- `VsanVcClusterHealthSystem_VsanGetReleaseRecommendation`.

> **UNVERIFIED — the ESA hardware requirement list itself.** No retrieved source enumerates
> ESA's device class, endurance, NVMe, count-per-host or networking requirements. The
> verification *route* above is spec-confirmed; the requirement list is not. State the route
> and point at the Broadcom vSAN ESA planning guide rather than producing a list.

**9.0 difference:** all five verification operations exist at 9.0 as well.

### P5 — vSAN health is clean, and the HCL database is current `[9.1]`

**Must be true:** you have looked at vSAN health before changing anything, and the HCL data
the health checks compare against is not stale.

**How to verify:**
- **SDDC Manager, domain-wide** (all **spec-confirmed (9.1)**):
  `GET /v1/domains/{domainId}/health-checks` (`getVsanHealthCheckByDomain`, accepts a
  `status` filter, returns `202` with a `HealthCheckQueryResult`),
  `GET /v1/domains/{domainId}/health-checks/queries/{queryId}` (`getVsanHealthCheckByQueryID`),
  `GET /v1/domains/{domainId}/health-checks/tasks/{taskId}` (`getVsanHealthCheckByTaskID`),
  `PATCH /v1/domains/{domainId}/health-checks` (`updateVsanHealthCheckByDomain`).
- **SDDC Manager, HCL database** (all **spec-confirmed (9.1)**):
  `PATCH /v1/vsan-hcl` (`downloadVsanHcl`, returns a `Task`),
  `GET /v1/vsan-hcl/configuration` (`getVsanHclConfiguration`),
  `PATCH /v1/vsan-hcl/configuration` (`updateVsanHclConfiguration`),
  `GET /v1/vsan-hcl/attributes` (`getVsanHclAttributes`).
  Egress note: HCL data comes from `vsanhealth.vmware.com:443` [DAUTH].
- **VI-JSON, cluster-level** (all **spec-confirmed (9.1)**, `moId` `vsan-cluster-health-system`):
  `VsanVcClusterHealthSystem_VsanQueryVcClusterHealthSummary` (and the `...Task` variant),
  `..._VsanQueryAllSupportedHealthChecks`, `..._VsanQueryClusterHistoricalHealth`,
  `..._VsanHealthQueryVsanClusterHealthConfig`, `..._VsanHealthGetVsanClusterSilentChecks`
  / `..._VsanHealthSetVsanClusterSilentChecks` (silenced checks hide real failures — check
  what has been silenced before trusting a green summary),
  `..._VsanVcUpdateHclDbFromWeb` / `..._VsanVcUploadHclDb` / `..._VsanPurgeHclFiles`
  (online and air-gapped HCL refresh).

**9.0 difference:** every operation in this section exists at 9.0 with the same path and
`operationId`. The `/v1/vsan-hcl` family and the domain `health-checks` family are
unchanged between versions.

### P6 — Caller privilege `[9.1]` — partially spec-declared, treat as indicative

`SPECVIJ` declares a `***Required privileges:***` line per operation. Verified samples:

| Operation | Declared privilege |
|---|---|
| `VsanVcClusterConfigSystem_VsanClusterGetConfig` | `System.Read` |
| `VsanVcClusterConfigSystem_VsanGetClusterRAIDInfo` | `System.Read` |
| `VsanVcClusterConfigSystem_VsanValidateConfigSpec` | `Global.Diagnostics` |
| `VsanSpaceReportSystem_VsanQuerySpaceUsage` | `System.Read` |
| `VsanSiteMaintenanceSystem_VsanPerformSiteMaintenancePrecheck` | `System.Read` |
| `VsanSiteMaintenanceSystem_VsanEnterSiteMaintenanceMode` | `Host.Config.Storage` |
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
> excluded from VCF SSO [DAUTH], so the VCF built-in roles do not govern it. Same gap as
> `vcf-lifecycle-upgrade` P8.

**9.0 difference:** the same privilege annotations appear at 9.0 for the operations that
exist there.

### P7 — Items the sources could not establish — state these as gaps

- **Which architecture (ESA or OSA) is the default.** See P1. Unresolved in docs and specs.
- **The ESA hardware requirement list.** See P4. Verification route only.
- **Numeric capacity headroom for policy / RAID / disk changes.** See P3.
- **Stretched-cluster operational limits** — witness sizing, inter-site latency and
  bandwidth, hosts per site. See P2.
- **Whether OSA is deprecated.** No retrieved page says so; both witness appliances ship in
  the 9.1 BOM and 9.1 adds simultaneous ESA+OSA mounts [DVS gap 8]. Do not imply an OSA
  end-of-life.
- **The API surface behind "stretched storage across vCenter instances" and "cyber recovery
  vSAN cluster."** Both are 9.1 what's-new items [DVS §7]; neither produced a new spec
  operation. See *What 9.1 added*.
- **Which vSAN objects a given policy change will resync, and for how long.** No source
  models this. It is measurable at runtime (`QuerySyncingVsanObjectsSummary`), not
  predictable from these sources.

---

## SDDC Manager surface — vSAN operations

All **spec-confirmed (9.1)** against `SPECSDDC`. Base `https://<sddc-manager>/v1`. There
are exactly **10** operations whose path or `operationId` mentions vSAN, plus the cluster
update pair that carries the stretch spec.

**Stretch / unstretch — carried in the body of the generic cluster update:**
```
PATCH /v1/clusters/{id}                       updateCluster
POST  /v1/clusters/{id}/validations           validateClusterUpdateSpec     (dry run)
GET   /v1/clusters/{id}/validations/{validationId}   getClusterUpdateValidation
GET   /v1/tasks/{id}                          (poll)
```
`updateCluster`'s own summary names it: *"Update a Cluster by adding or removing Hosts,
**Stretching a standard vSAN cluster, Unstretching a stretched cluster** or by marking for
deletion."* There is no `/stretch` path — searching for one is the single most common
wrong turn here. `SPECSDDC` contains **zero** paths matching `stretch` at either version.

**Remote vSAN datastore (HCI mesh) mounts:**
```
GET    /v1/clusters/{id}/datastores                        getClusterDatastores
POST   /v1/clusters/{id}/datastores                        addDatastoreToCluster        (body DatastoreMountSpec, returns Task)
POST   /v1/clusters/{clusterId}/datastores/validations     validateVsanRemoteDatastoreMountSpec
GET    /v1/clusters/{id}/datastores/validations/{validationId}   getDatastoreMountValidation   <- new in 9.1
DELETE /v1/clusters/{id}/datastores/{datastoreId}          removeDatastoreFromCluster
POST   /v1/clusters/{clusterId}/datastores/validation      validateVsanRemoteDatastoreSpec   <- DEPRECATED (singular "validation")
```
The deprecated singular-`validation` form is `deprecated: true` in **both** `SPECSDDC` 9.0
and 9.1 — it was already deprecated at 9.0, not newly so. Use the plural `validations`.

`DatastoreMountSpec` → `DatastoreSpec` → `vsanRemoteDatastoreClusterSpec`
(`isStretched`, `primaryAzName`, `vsanRemoteDatastoreSpec[]`), each entry carrying
`datastoreUuid` (required), `networkTopology` ("Symmetric/Asymmetric based on configuration
of stretched server/client cluster"), `siteAffinity[]` (`serverSite` required,
`clientSite`), and **9.1-only** `encryptionConfig`.

**vSAN health and HCL:** see P5 — `getVsanHealthCheckByDomain`,
`getVsanHealthCheckByQueryID`, `getVsanHealthCheckByTaskID`, `updateVsanHealthCheckByDomain`,
`downloadVsanHcl`, `getVsanHclConfiguration`, `updateVsanHclConfiguration`,
`getVsanHclAttributes`.

**vSAN configuration at cluster creation** (`POST /v1/clusters`, `createCluster`, and
`POST /v1/clusters/validations`, `validateClusterCreationSpec` — both **spec-confirmed
(9.1)**; cluster creation itself belongs to `vcf-domains-clusters`, listed here only because
the vSAN fields live in its body):
`DatastoreSpec.vsanDatastoreSpec` → `VsanDatastoreSpec` with `datastoreName`,
`failuresToTolerate` (*"required for vSAN OSA configuration"*), `licenseKey`,
`dedupAndCompressionEnabled` (*"only available for clusters in which the hosts are all
flash"*), `esaConfig` (`enabled` **required**, optional `vsanMaxConfig` with
`enableVsanMax` / `enableVsanExternalNetwork`), and **9.1-only** `encryptionConfig` →
`dataInTransitConfig` (`enable` required, `rekeyInterval` in minutes).

**9.1-only additions on this surface:** `PATCH /v1/clusters` (`updateClusters`, body
`ClustersUpdateSpec` = `clusterIds[]` 1–100 plus `clustersRefreshSpec.forceRefresh`),
`ClusterUpdateSpec.clusterPrimaryDatastoreUpdateSpec` (change a cluster's primary datastore
by `datastoreId`), `ClusterUpdateSpec.markAsDefault`, `ClusterUpdateSpec.dnsNtpUpdateSpec`,
`getDatastoreMountValidation`, and `ClusterUnstretchSpec.azToRemove`.

---

## Worked example — stretch a cluster via SDDC Manager

**This is the reference sequence for the whole skill: validate → execute → poll.** It is
`[9.1]`; the `ClusterStretchSpec` payload is byte-identical at 9.0.

> Stretching moves a standard vSAN cluster to two availability zones. It commissions hosts,
> reconfigures NSX transport nodes, adds a witness and rebuilds object layout across two
> fault domains. It is a long, production-affecting change that triggers a full resync.
> Run step 1 and read the result before running step 2.

**Step 0 — confirm it is not already stretched, and that the hosts are free.**
```
GET /v1/clusters/{id}                          # getCluster -> Cluster.isStretched must be false
GET /v1/hosts?status=UNASSIGNED_USEABLE        # getHosts — free-pool host IDs for the second AZ
GET /v1/hosts?isVsanWitnessHost=true           # existing witness hosts SDDC Manager knows about
```
`ClusterStretchSpec.hostSpecs` is documented as *"List of vSphere host information from the
**free pool** to consume in the workload domain"* — hosts already in a cluster are not
eligible. `getHosts` `status` accepts `ASSIGNED`, `UNASSIGNED_USEABLE`,
`UNASSIGNED_UNUSEABLE`; `storageType` accepts `VSAN`, `VSAN_ESA`, `VSAN_REMOTE`, `VSAN_MAX`
and the non-vSAN types. The `isVsanWitnessHost`, `isStandalone`, `isLifecycleManaged`,
`pageSize` and `pageNumber` filters are **9.1-only** (9.0 has the deprecated `size` / `page`
pair and no witness filter).

**Step 1 — dry run.** Same body, different path.
```
POST /v1/clusters/{id}/validations          # validateClusterUpdateSpec
Authorization: Bearer <sddc-manager accessToken>
Content-Type: application/json
```
```json
{
  "clusterStretchSpec": {
    "hostSpecs": [
      {
        "id": "<free-pool host UUID>",
        "licenseKey": "<esx license key>",
        "hostName": "esx-az2-01.example.com",
        "username": "root",
        "password": "<password>",
        "sshThumbprint": "<ssh fingerprint>",
        "azName": "AZ2",
        "hostNetworkSpec": { }
      }
    ],
    "witnessSpec": {
      "fqdn": "vsan-witness-01.example.com",
      "vsanIp": "10.0.40.10",
      "vsanCidr": "10.0.40.0/24"
    },
    "witnessTrafficSharedWithVsanTraffic": false,
    "vsanNetworkSpecs": [
      { "vsanGatewayIP": "10.0.41.1", "vsanCidr": "10.0.41.0/24" }
    ],
    "networkSpec": {
      "nsxClusterSpec": {
        "uplinkProfiles": [ { } ],
        "ipAddressPoolsSpec": [ { } ]
      },
      "networkProfiles": [
        { "name": "az2-profile", "nsxtHostSwitchConfigs": [ { } ] }
      ]
    },
    "isEdgeClusterConfiguredForMultiAZ": false
  }
}
```
Field notes, all from the `9.1.0.0` `sddc-manager-openapi.json`:
- `hostSpecs` and `witnessSpec` are the **only** required members of `ClusterStretchSpec`.
- `HostSpec` requires `id`. `licenseKey` is required *"except in cases where the ESX host has
  already been licensed outside of the VMware Cloud Foundation system"*. `azName` is
  documented as *"required while performing a stretched cluster expand operation"*.
  `ipAddress` is **deprecated**; use `hostName`. `sshThumbprint` is currently optional with
  the note *"this field will be mandatory in future releases"*.
- `WitnessSpec` requires all three of `fqdn`, `vsanIp`, `vsanCidr`. Note the spec's own
  wording: `fqdn` is described as *"Management ip of the witness host"* — the field name and
  its description disagree. Supply the FQDN.
- `networkSpec` (`ClusterStretchNetworkSpec`) requires **both** `nsxClusterSpec` and
  `networkProfiles`. `NsxStretchClusterSpec` requires `uplinkProfiles`;
  `StretchClusterNetworkProfile` requires `name` and `nsxtHostSwitchConfigs`. The inner NSX
  objects are elided above — build them from `vcf-domains-clusters` / `nsx-security-policy`,
  not from guesswork.
- `secondaryAzOverlayVlanId` is **deprecated**: *"the secondary AZ overlay vlan id should be
  mentioned in the `uplinkProfile` field instead"*.
- Optional `useAsyncValidation=true` query parameter on the validations call.

Response is a `Validation`: `id`, `executionStatus` (one of `IN_PROGRESS`, `FAILED`,
`COMPLETED`, `UNKNOWN`, `SKIPPED`, `CANCELLED`, `CANCELLATION_IN_PROGRESS`), `resultStatus`
(`SUCCEEDED`, `FAILED`, `WARNING`, `UNKNOWN`, `CANCELLATION_IN_PROGRESS`) and
`validationChecks[]`.

**Step 1b — poll the validation** until `executionStatus` is `COMPLETED`:
```
GET /v1/clusters/{id}/validations/{validationId}     # getClusterUpdateValidation
```
Proceed only on `resultStatus: SUCCEEDED`. A `WARNING` is a decision, not a green light.

**Step 2 — execute.** Identical body, `PATCH` on the cluster:
```
PATCH /v1/clusters/{id}                              # updateCluster
```
Returns `200` or `202` with a `Task`.

**Step 3 — poll the task.**
```
GET /v1/tasks/{id}
```
`Task.status` is one of `PENDING`, `IN_PROGRESS`, `SUCCESSFUL`, `FAILED`, `CANCELLED`,
`COMPLETED_WITH_WARNING`, `SKIPPED`, `QUEUED`, `TIMED_OUT` (the schema lists both
upper-snake and title-case spellings — match case-insensitively). `subTasks[]` carries the
per-step detail; `errors[]` is populated on failure.

**Step 4 — confirm from the other surface.** SDDC Manager reporting `SUCCESSFUL` means the
workflow finished, not that vSAN has finished rebuilding:
```
GET /v1/clusters/{id}                                             # isStretched -> true
POST /sdk/vim25/9.1.0.0/vsan/VimClusterVsanVcStretchedClusterSystem/vsan-stretched-cluster-system/VSANVcGetWitnessHosts
POST /sdk/vim25/9.1.0.0/vsan/VsanObjectSystem/vsan-cluster-object-system/QuerySyncingVsanObjectsSummary
```
The resync is what determines when the cluster is actually protected across sites.

**Unstretching** uses the same three-step shape with `clusterUnstretchSpec` in place of
`clusterStretchSpec`. In 9.1 that spec takes an optional `azToRemove`; in 9.0 it is an empty
object. It is a separate destructive operation, not an undo — it removes an availability
zone and rebuilds object layout again.

**There is also a preparation flag.** `ClusterUpdateSpec.prepareForStretch` (boolean,
"Prepare the cluster for stretch") exists at both versions and is sent through the same
`updateCluster` call. No retrieved source explains when it is required versus optional —
`UNVERIFIED`.

---

## VI-JSON surface — the vSAN management API

Base: `https://<vcenter-host>/sdk/vim25/{release}`, where `{release}` is an enum whose 9.1
default is `9.1.0.0` and which also accepts `9.0.0.0` and older schemas back to `7.0.0.0`.
Nearly every vSAN operation is a **POST** to `/vsan/{ManagedObject}/{moId}/{Operation}` with
a `{Operation}RequestType` body, plus a handful of property GETs.

Counting precisely: **301** operations sit under the `/vsan/` prefix at 9.1 (285 at 9.0),
plus **15** `HostVsanInternalSystem` operations at the top level (not under `/vsan/`) and
one vSAN-named `/pbm` operation — **317** vSAN-matching operations at 9.1 against **301** at
9.0. All **spec-confirmed (9.1)** against `SPECVIJ`.

**The `moId` is a well-known singleton, not something you look up.** From the spec's own
managed-object descriptions:

| Managed object | `moId` | Ops (9.1) |
|---|---|---|
| `VsanVcClusterConfigSystem` | `vsan-cluster-config-system` | 10 |
| `VsanVcClusterHealthSystem` | `vsan-cluster-health-system` | 44 |
| `VimClusterVsanVcStretchedClusterSystem` | `vsan-stretched-cluster-system` | 13 |
| `VimClusterVsanVcDiskManagementSystem` | `vsan-disk-management-system` | 12 |
| `VsanSiteMaintenanceSystem` | `vsan-cluster-site-maintenance-system` | 5 (**9.1-only**) |
| `VsanRemoteDatastoreSystem` | `vsan-remote-datastore-system` | 8 |
| `VsanSpaceReportSystem` | `vsan-cluster-space-report-system` | 3 |
| `VsanObjectSystem` | `vsan-cluster-object-system` | 8 |
| `VsanResourceCheckSystem` | `vsan-cluster-resource-check-system` (vCenter) / `vsan-resource-check-system` (host) | 4 |
| `VsanCapabilitySystem` | `vsan-vc-capability-system` (vCenter) / `vsan-capability-system` (host) | 1 |
| `VsanClusterPowerSystem` | `vsan-cluster-power-system` | 3 |
| `VsanFileServiceSystem` | `vsan-cluster-file-service-system` (vCenter) / `vsan-file-service-system` (host) | 17 |
| `VsanIscsiTargetSystem` | `vsan-cluster-iscsi-target-system` | 23 |
| `CnsVolumeManager` | `cns-volume-manager` | 16 |
| `VsanPerformanceManager` | `vsan-performance-manager` | 23 |
| `VsanDiagnosticsSystem` | `vsan-cluster-diagnostics-system` | 11 |
| `VsanIoInsightManager` | `vsan-cluster-ioinsight-manager` (vCenter) / `vsan-ioinsight-manager` (host) | 5 |
| `DataProtectionHealthSystem` | `dp-health-system` | 4 (**9.1-only**) |
| `VsanUpgradeSystemEx` | `vsan-upgrade-systemex` | 5 |
| `VsanSystemEx` | `vsanSystemEx` (ESX host) | 10 |
| `HostVsanHealthSystem` | `ha-vsan-health-system` (ESX host) | 26 |

Also present without a spec-stated singleton `moId`: `HostVsanSystem` (11, host-level),
`VsanClusterHealthSystem` (11), `VsanUpgradeSystem` (3), `HostVsanInternalSystem` (15, not
under `/vsan/`), `VsanVdsSystem` (4), `VsanHostVdsSystem` (2), `VsanUpdateManager` (3),
`VsanVumSystem` (4), `VsanPhoneHomeSystem` (6), `VsanMassCollector` (1),
`VsanClusterMgmtInternalSystem` (2), `VsanVcsaDeployerSystem` (3,
`vsan-vcsa-deployer-system`).

### Cluster configuration — `VsanVcClusterConfigSystem`

```
VsanClusterGetConfig            read the current vSAN config          System.Read
VsanClusterReconfig             apply a VimVsanReconfigSpec           (no privilege declared)
VsanValidateConfigSpec          validate a spec without applying      Global.Diagnostics
VsanClusterGetClaimedCapacity   claimed capacity
VsanClusterGetRuntimeStats      runtime stats
VsanQueryClusterDrsStats        DRS interaction stats
VsanEncryptedClusterRekey_Task  rekey an encrypted cluster
RunLifecycleCheck               lifecycle check
VsanGetClusterRAIDInfo          actual RAID in use (ESA)     <- new in 9.1, System.Read
VsanGetConfigurationLimits      limits and supported values  <- new in 9.1
```

`VsanClusterReconfigRequestType` requires `cluster` (a `ClusterComputeResource`
`ManagedObjectReference`) and `vsanReconfigSpec` (`VimVsanReconfigSpec`), whose members are
`vsanClusterConfig`, `dataEfficiencyConfig`, `diskMappingSpec`, `faultDomainsSpec`,
`modify` and `allowReducedRedundancy`.

`modify` is the field to get right: *"If `modify` is false and the operation succeeds, then
the configuration of the vSAN cluster matches the specification exactly; in this case any
unset portions of the specification will result in unset or default portions of the
configuration."* Sending a partial spec with `modify: false` resets everything you omitted.

**Dedup and compression** live in `VsanDataEfficiencyConfig` (`dedupEnabled` required,
`compressionEnabled`) and its 9.1-visible extension `VsanDataEfficiencyConfigEx`
(`dedupStoreUuid` — *"The UUID of the global deduplication store"*, do not set it when
enabling global dedup, vSAN generates it — plus `dedupPaused`, which applies only to ESA).
The 9.1 spec adds the sentence: *"For vSAN ESA, compression is enabled by default since
9.1.0 release, disabling compression is not supported."* That sentence is **not present at
the 9.0 tag** — it is the strongest spec-level evidence for the 9.1 compression change.

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

**Prefer the SDDC Manager path in a VCF estate.** SDDC Manager's documented 9.1 role
explicitly includes *"configuration of vSAN stretched clusters"* [DVS via the 9.1 upgrade
guide], and it orchestrates host commissioning and the NSX side that the raw VI-JSON call
does not. Use VI-JSON for inspection, for shared-witness queries, and for clusters SDDC
Manager does not own.

### Site maintenance mode — `VsanSiteMaintenanceSystem` (**9.1-only**, 5 ops)

```
VsanPerformSiteMaintenancePrecheck      System.Read
VsanGetSiteMaintenancePrecheckStatus    result of the latest check
VsanQueryClusterSiteMaintenanceState    System.Read — state of all FDs in the cluster
VsanEnterSiteMaintenanceMode            Host.Config.Storage
VsanExitSiteMaintenanceMode
```
`VsanEnterSiteMaintenanceModeRequestType` requires `faultDomainName` and `cluster`. The
operation is documented as *"Put all hosts in a fault domain into maintenance mode"* — it is
a whole-site action, and the precheck is the documented gate
(*"Initiates a precheck to determine if the target fault domain can enter maintenance mode"*).
This entire managed object is **absent from the 9.0 spec** [DELTA] — it is the API behind
the 9.1 "site maintenance mode" feature.

### Disks, storage pools and fault domains — `VimClusterVsanVcDiskManagementSystem` (12)

```
InitializeDiskMappings            QueryDiskMappings              RebuildDiskMapping
RemoveDiskEx                      RemoveDiskMappingEx            UnmountDiskMappingEx
QueryVsanManagedDisks             RetrieveAllFlashCapabilities
QueryClusterDataEfficiencyCapacityState
VsanAddStoragePoolDisk            VsanDeleteStoragePoolDisk      VsanUnmountStoragePoolDisks
```
Disk *groups* (`...DiskMapping...`) are the OSA model; *storage pools*
(`Vsan*StoragePoolDisk*`) are the ESA model. Both families exist at both versions. Host-level
equivalents are on `HostVsanSystem` (`AddDisks_Task`, `InitializeDisks_Task`,
`RemoveDisk_Task`, `RemoveDiskMapping_Task`, `UnmountDiskMapping_Task`,
`EvacuateVsanNode_Task`, `RecommissionVsanNode_Task`, `QueryDisksForVsan`,
`QueryHostStatus`, `UpdateVsan_Task`, `GET .../config`).

### Objects, health, performance, space

```
VsanObjectSystem       VosQueryVsanObjectInformation, VosSetVsanObjectPolicy,
                       RelayoutObjects, VsanDeleteObjects_Task, VsanQueryObjectIdentities,
                       QuerySyncingVsanObjectsSummary, VsanQueryInaccessibleVmSwapObjects,
                       VsanQueryPhysicalPlacements                        <- new in 9.1
VsanSpaceReportSystem  VsanQuerySpaceUsage, VsanQueryEntitySpaceUsage,
                       QueryVsanManagedStorageSpaceUsage
VsanPerformanceManager 23 ops incl. VsanPerfQueryPerf, VsanPerfDiagnose,
                       QueryVsanPerfTopEntities, QueryVsanPerfHotspotEntities,
                       VsanPerfGetSupportedHotspotEntityTypes            <- new in 9.1
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
`RemoteVcMountPrecheck` is the cross-vCenter mount pre-flight. It exists at **both** 9.0 and
9.1 — see the discrepancies section for why that matters to the "stretched storage across
vCenter instances" claim.

### Data protection health — `DataProtectionHealthSystem` (**9.1-only**, 4 ops)

```
VsanQueryHealthSummary          VsanQueryHistoricalHealth
VsanGetDpClusterSilentChecks    VsanSetDpClusterSilentChecks
```
Health for the snapshot/replication layer, surfaced through the vSAN health system on
vCenter (`moId` `dp-health-system`) rather than through the Data Protection REST API.
Absent from the 9.0 spec [DELTA].

### File services, iSCSI, CNS

`VsanFileServiceSystem` (17): `VsanClusterCreateFsDomain`, `VsanClusterReconfigureFsDomain`,
`VsanClusterRemoveFsDomain`, `VsanCreateFileShare`, `VsanReconfigureFileShare`,
`VsanClusterRemoveShare`, `VsanClusterQueryFileShares`, share snapshots,
`VsanPerformFileServiceEnablePreflightCheck`, OVF discovery/download, `VsanUpgradeFsvm`,
`VsanRebalanceFileService`.

`VsanIscsiTargetSystem` (23): the `VsanVit*` target / LUN / initiator-group family.

`CnsVolumeManager` (16): `CnsCreateVolume`, `CnsDeleteVolume`, `CnsAttachVolume`,
`CnsDetachVolume`, `CnsExtendVolume`, `CnsRelocateVolume`, `CnsReconfigVolumePolicy`,
`CnsCreateSnapshots`, `CnsDeleteSnapshots`, `CnsQueryVolume`, `CnsQueryAsync`,
`CnsUpdateVolumeMetadata`, `CnsConfigureVolumeACLs`, plus **three new in 9.1**:
`CnsSyncVolume`, `CnsUnregisterVolume`, `CnsUpdateVolumeCrypto` (*"encrypt, deep recrypt,
shallow recrypt, and decrypt for the container block volumes and all the disks in the
chain"*).

---

## Storage policies — two surfaces, one concept

vSAN storage policies are SPBM policies. **Authoring is VI-JSON `/pbm/...`; reading and
compliance are split across VI-JSON and vSphere Automation.** Both are needed for most real
tasks, and neither is on the "vSAN" surface.

**Authoring / management — VI-JSON `/pbm/PbmProfileProfileManager/{moId}/...`**, all
**spec-confirmed (9.1)**:
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

**Compliance — VI-JSON `/pbm/PbmComplianceManager/{moId}/...`** (**spec-confirmed (9.1)**):
`PbmCheckCompliance`, `PbmCheckRollupCompliance`, `PbmFetchComplianceResult`,
`PbmFetchRollupComplianceResult`, `PbmQueryByRollupComplianceStatus`.

**Placement / compatibility — VI-JSON `/pbm/PbmPlacementSolver/{moId}/...`**:
`PbmCheckCompatibility`, `PbmCheckCompatibilityWithSpec`, `PbmCheckRequirements`,
`PbmQueryMatchingHub`, `PbmQueryMatchingHubWithSpec`. Entry point:
`PbmServiceInstance_PbmRetrieveServiceContent` / `GET /pbm/PbmServiceInstance/{moId}/content`.

**Read + per-VM assignment — vSphere Automation `/api/vcenter/...`**, all **spec-confirmed
(9.1)** against `SPECAUTO`:
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
`.../storage/policies/compliance/vm` — not `/storage/policies/compliance` on its own. The
9.1 spec adds four Supervisor storage-policy operations under
`/api/vcenter/namespace-management/supervisors/{supervisor}/{control-plane,workloads}/storage/policies`
(**new in 9.1**; not present at 9.0).

**Changing a policy on a populated vSAN cluster is a resync.** `PbmUpdate` on a profile
applies to every object bound to it. Run `PbmCheckCompatibility` / `checkCompatibility`
first, and P3's capacity checks before that.

**9.0 difference:** the `/pbm` families and the nine non-Supervisor vSphere Automation
operations are identical at both versions. Only the four Supervisor ones are 9.1-only.

---

## vSAN Data Protection (snapservice) surface

Base `https://<host>/api`, spec title *Snapshot Appliance API*, spec version `9.1.0.0`,
**65 operations** (48 at 9.0 — **17 added, 0 removed, 0 newly deprecated** [DELTA]). The
`{host}` is the Data Protection appliance, not vCenter: `Snapservice.Sites.AddSpec` carries
both a `vcenter_certificate` and a separate `va_certificate` — *"Certificate of the remote
Data Protection Virtual Appliance"*.

Conventions that differ from every other surface here: dotted `operationId`s
(`Snapservice.X_verb`), `?vmw-task=true` to run an operation as a task, `?action=<verb>` for
custom actions, and snake_case body properties (`vcenter_connection_spec`,
`target_entities`, `snapshot_policies`).

**Sessions and info** (`[9.0+9.1]`):
```
POST   /api/snapservice/sessions          Snapservice.Sessions_create
GET    /api/snapservice/sessions          Snapservice.Sessions_get
DELETE /api/snapservice/sessions          Snapservice.Sessions_delete
GET    /api/snapservice/info/about        Snapservice.Info.About_get
GET    /api/snapservice/tasks             Snapservice.Tasks_list
GET    /api/snapservice/tasks/{task}      Snapservice.Tasks_get
```

**Sites** (`[9.0+9.1]` unless marked):
```
GET    /api/snapservice/sites                              Snapservice.Sites_list
GET    /api/snapservice/sites/{site}                       Snapservice.Sites_get
POST   /api/snapservice/sites?action=probe                 Snapservice.Sites_probe
POST   /api/snapservice/sites?action=add&vmw-task=true     Snapservice.Sites_add$Task
PATCH  /api/snapservice/sites/{site}?vmw-task=true         Snapservice.Sites_update$Task
DELETE /api/snapservice/sites/{site}?vmw-task=true         Snapservice.Sites_delete$Task
GET    /api/snapservice/sites/{site}/clusters              Snapservice.Sites.Clusters_list
GET    /api/snapservice/sites/{site}/licenses              Snapservice.Sites.Licenses_list
GET    /api/snapservice/sites/{site}/capabilities          Snapservice.Sites.Capabilities_get              <- new in 9.1
GET    /api/snapservice/sites/{site}/clusters/{cluster}/capabilities
                                                           Snapservice.Sites.Clusters.Capabilities_get     <- new in 9.1
GET    /api/snapservice/sites/{site}/datastores            Snapservice.Sites.Datastores_list               <- new in 9.1
GET    /api/snapservice/sites/{site}/datastores/capabilities
                                                           Snapservice.Sites.Datastores.Capabilities_list  <- new in 9.1
GET    /api/snapservice/sites/{site}/datastores/{datastore}/capabilities
                                                           Snapservice.Sites.Datastores.Capabilities_get   <- new in 9.1
```
`Snapservice.Sites.AddSpec` requires `vcenter_connection_spec`; `vcenter_creds` is nominally
optional but the spec states *"API is expected to throw validation error if vCenter
credentials are not supplied"* — treat it as required. Probe first
(`Sites_probe` → `Snapservice.Sites.ProbeResult`) to obtain and check certificates.

**Cluster pairs** (`[9.0+9.1]`) — replication topology:
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

**Protection groups** (`[9.0+9.1]` unless marked):
```
GET    /api/snapservice/clusters/{cluster}/protection-groups            Snapservice.Clusters.ProtectionGroups_list
GET    /api/snapservice/clusters/{cluster}/protection-groups/{pg}       ..._get
POST   /api/snapservice/clusters/{cluster}/protection-groups?vmw-task=true              ..._create$Task
PATCH  /api/snapservice/clusters/{cluster}/protection-groups/{pg}?vmw-task=true         ..._update$Task
DELETE /api/snapservice/clusters/{cluster}/protection-groups/{pg}?vmw-task=true         ..._delete$Task
POST   .../protection-groups/{pg}?action={pause|resume|activate|demote|promote}&vmw-task=true
POST   /api/snapservice/protection-groups?action=compute-members        Snapservice.ProtectionGroups_computeMembers        <- new in 9.1
GET    /api/snapservice/protection-groups/{pg}/capabilities             Snapservice.ProtectionGroups.Capabilities_get      <- new in 9.1
POST   /api/snapservice/protection-groups/{pg}?action=start-ransomware-recovery&vmw-task=true
                                                                        Snapservice.ProtectionGroups_startRansomwareRecovery$Task  <- new in 9.1
POST   /api/snapservice/protection-groups/{pg}?action=end-ransomware-recovery&vmw-task=true
                                                                        Snapservice.ProtectionGroups_endRansomwareRecovery$Task    <- new in 9.1
```
Note the two 9.1 additions are on `/snapservice/protection-groups/{pg}` — **without** the
`/clusters/{cluster}` prefix. Both forms exist; do not assume one path shape.

`Snapservice.ProtectionGroupSpec` requires `name` and `target_entities`; optional
`snapshot_policies[]` (*"if missing or null local protection will be skipped"*),
`replication_policies[]`, and `locked` (*"A locked protection group cannot be modified or
deleted by the user. All snapshots associated with the protection group will be secure and
cannot be deleted."* — a one-way door; the system deletes them on expiry).
`SnapshotPolicy` requires `name`, `schedule` and `retention`.

**Snapshots** — two families. Cluster-scoped (`[9.0+9.1]`):
```
GET    /api/snapservice/clusters/{cluster}/protection-groups/{pg}/snapshots            ..._list
GET|DELETE .../protection-groups/{pg}/snapshots/{snapshot}                             ..._get / ..._delete
POST   .../protection-groups/{pg}/snapshots?vmw-task=true                              ..._create$Task
GET    /api/snapservice/clusters/{cluster}/virtual-machines                            ..._list
GET    .../virtual-machines/{vm}/snapshots[/{snapshot}]                                ..._list / ..._get
POST   .../virtual-machines/{vm}?action={restore|revert|linked-clone}&vmw-task=true
```
And a **9.1-only** global VM-snapshot family with labels:
```
GET    /api/snapservice/virtual-machines/snapshots                       Snapservice.VirtualMachines.Snapshots_list
PATCH  /api/snapservice/virtual-machines/snapshots/{snapshot}?vmw-task=true             ..._update$Task
DELETE /api/snapservice/virtual-machines/snapshots/{snapshot}?vmw-task=true             ..._delete$Task
PATCH  .../snapshots/{snapshot}?action=add-label&vmw-task=true                          ..._addLabel$Task
PATCH  .../snapshots/{snapshot}?action=delete-label&vmw-task=true                       ..._deleteLabel$Task
PUT    .../snapshots/{snapshot}?action=set-labels&vmw-task=true                         ..._setLabels$Task
GET    /api/snapservice/virtual-machines/{vm}/protection-configuration                  Snapservice.VirtualMachines.ProtectionConfiguration_get
PATCH  /api/snapservice/virtual-machines/{vm}/protection-configuration?vmw-task=true     ..._update$Task
```

**Reports** (`[9.0+9.1]`, 8 operations): `/api/snapservice/reports/clusters/{cluster}/...`
for protection groups, VMs, their snapshots, and `snapshot-status-counts` aggregated by
`?aggregateBy=protection-group`, `time-slice` or `virtual-machine`.

---

## What 9.1 added, and how much of it is visible in the API

| 9.1 what's-new item [DVS §7] | Spec evidence at the 9.1 tag |
|---|---|
| **ESA Auto RAID-6** — RAID-6 as the default RAID level | **Strong.** `VsanVcClusterConfigSystem_VsanGetClusterRAIDInfo` (*"Get Actual RAID used in vSAN ESA cluster"*) is new in 9.1; schemas `VsanAutoRAIDConfig` (`assumeAutoManagedRAID`) and `VsanAutoRAIDInfo` are **absent from the 9.0 spec**. |
| **ESA Global Deduplication** — cluster-wide, post-processing, encryption-compatible | **Partial.** `VsanDataEfficiencyConfigEx.dedupStoreUuid` ("global deduplication store") and `dedupPaused` exist at **both** tags — the schema predates the announced feature. No new operation. |
| **ESA compression enhancements** | **Textual.** The 9.1 spec adds *"For vSAN ESA, compression is enabled by default since 9.1.0 release, disabling compression is not supported"* to `VsanDataEfficiencyConfig.compressionEnabled`. Not present at 9.0. No new operation. |
| **Site maintenance mode** | **Strong.** `VsanSiteMaintenanceSystem` and its 5 operations are new in 9.1 [DELTA]. |
| **Stretched storage across vCenter instances / across VCF deployments** | **None found.** `VsanRemoteDatastoreSystem_RemoteVcMountPrecheck` and all 8 remote-datastore operations exist at **both** tags; no new stretched-cluster or remote-datastore operation appeared in 9.1. `UNVERIFIED` at the API level — the capability is doc-sourced only. |
| **Cyber recovery vSAN storage cluster** | **None found.** No operation or schema in `SPECVIJ` or `SPECDP` identifies it. Doc-sourced only. `UNVERIFIED` at the API level. |
| **Shared vSAN storage cluster support (mount ESA and OSA simultaneously)** | **None found** as a distinct operation; the existing remote-datastore family is unchanged. Doc-sourced. |
| **Multiple retention schedules for vSAN snapshots (daily / weekly / monthly)** | **Strong.** `SPECDP` gains `Snapservice.DailyRetention`, `WeeklyRetention`, `MonthlyRetention`, `HourlyRetention`, `LongTermRetention`, `DayOfWeek`; `RetentionPolicy.long_term` is 9.1-only; the `TimeUnit` enum gains `YEAR`. |
| **Seeding for vSAN replication; replication on any storage** | **Partial.** `Snapservice.TargetStorageSpec`, `VmTargetStorageSpec`, `TargetEntityReplicationSpec`, `ReplicationTargetConfiguration` and the per-VM `protection-configuration` family are all new in 9.1. |
| **Ransomware recovery** (not on the what's-new list but present) | **Strong.** `startRansomwareRecovery$Task` / `endRansomwareRecovery$Task` new in 9.1. |
| **RWX file volumes, fast clone volumes, 50,000 volumes per vCenter** | **Partial.** `CnsVolumeManager` gains `CnsSyncVolume`, `CnsUnregisterVolume`, `CnsUpdateVolumeCrypto`. The 50,000 figure is doc-sourced; no spec artifact states it. |
| **Data protection health in vSAN health** | **Strong.** `DataProtectionHealthSystem` (4 ops, `moId` `dp-health-system`) is new in 9.1. |
| **Dynamic protection-group membership** | **Strong.** `Snapservice.TagRule`, `LogicalOperator`, `MemberEntities`, `MembershipChangeType`, `VmMembershipInfo` are new in 9.1, alongside `ProtectionGroups_computeMembers`. |

**Deprecations:** the 9.1 product-support-notes **vSAN section reads "None"** [DVS §5] — no
vSAN deprecations or removals in 9.1. The specs agree: **zero** vSAN operations removed and
**zero** newly deprecated across `SPECVIJ`, `SPECDP` and the vSAN slice of `SPECSDDC`
[DELTA]. The one deprecated vSAN-named SDDC Manager operation,
`validateVsanRemoteDatastoreSpec`, was **already** `deprecated: true` at 9.0.

---

## Spec-vs-prose discrepancies found while writing this file

1. **"Stretched storage across vCenter instances" has no new API.** It is a headline 9.1
   vSAN feature [DVS §7], but every remote-datastore and stretched-cluster operation exists
   unchanged at 9.0, `RemoteVcMountPrecheck` included. Either the capability is delivered
   through unchanged operations with new backend behavior, or through a surface not in this
   corpus. Report the feature as documented; do not attribute it to a specific new call.
2. **Global deduplication's schema predates its announcement.** `dedupStoreUuid` and
   `dedupPaused` are present at the 9.0 tag. Treat "new in 9.1" for global dedup as a
   product-availability statement, not an API change.
3. **`WitnessSpec.fqdn` is described as "Management ip of the witness host."** Field name and
   description disagree in both 9.0 and 9.1. Supply the FQDN; note the ambiguity if a caller
   reports a validation failure on that field.
4. **Privilege annotations are inconsistent.** See P6 — several vSAN write operations declare
   none, and `VSANVcSetPreferredFaultDomain` declares `VApp.Clone`. The annotations are real
   spec content but are not a usable privilege model on their own.
5. **The SDDC Manager spec's declared base is `http://localhost:80`.** That is a build
   artifact in both `SPECSDDC` 9.0 and 9.1. The load-bearing part is the `/v1` prefix;
   substitute the real SDDC Manager host over HTTPS.
6. **The vSAN Management API is documented as SOAP/vmodl.** The Broadcom reference describes
   it as a SOAP/vmodl web service on `/vsanHealth` (vCenter), `/vsan` (host) and `/sdk`
   (legacy MOs) [DVS §B]. The **VI-JSON spec exposes the same managed objects over HTTP/JSON**
   under `/sdk/vim25/{release}/vsan/...`, which is what this file documents because it is the
   machine-verifiable surface. Both descriptions are correct; they are two transports over
   one object model. If a caller is using pyVmomi or the vSAN Management SDK, the managed
   object and operation names in this file are the same ones they need.
7. **`prepareForStretch` is undocumented.** The field exists on `ClusterUpdateSpec` at both
   versions with a one-line description and no explanation of when it is required.
   `UNVERIFIED`.
