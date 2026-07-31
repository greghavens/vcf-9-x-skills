# VCF 9.0 → 9.1 — vSAN Delta

Scoped to vSAN: architectures, cluster and disk configuration, storage policies, stretched
clusters, health, and vSAN Data Protection. For the cross-product delta see the research
dossiers; this file is the vSAN slice.

**Source keys.** `DVS` = `research/vsphere-vcenter-vsan.md`;
`DAUTH` = `research/foundation-auth-identity.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of git tags
`9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`);
`SPEC*` = the per-product `.ops.json` inventories in `research/spec-inventory/`.
Schema quotations come from the raw specs at each tag.

---

## The headline: vSAN grew, and nothing was taken away

| Product spec | 9.0 ops | 9.1 ops | added | **removed** | newly deprecated |
|---|---|---|---|---|---|
| `vsphere-vi-json` (whole spec) | 2195 | 2243 | 48 | **0** | **0** |
| — of which vSAN-matching | **301** | **317** | 16 | **0** | **0** |
| `vsan-data-protection` | **48** | **65** | 17 | **0** | **0** |
| `sddc-manager` — vSAN-named ops | **10** | **10** | 0 | **0** | 0 *(one was already deprecated at 9.0)* |
| `vsphere-automation` — vSAN ops | **0** | **0** | — | — | — |

**The 9.1 product-support-notes vSAN section reads "None"** — no vSAN deprecations or
removals in 9.1 [DVS §5]. The specs agree exactly: zero vSAN operations removed and zero
newly deprecated across all three surfaces [DELTA]. This is the rare case where prose and
spec corroborate each other cleanly.

The one deprecated vSAN-named SDDC Manager operation,
`POST /v1/clusters/{clusterId}/datastores/validation` (`validateVsanRemoteDatastoreSpec`),
carries `deprecated: true` in **both** 9.0 and 9.1. It was **not** deprecated in 9.1. Use
the plural `.../datastores/validations` in both versions.

---

## Delta table

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| **Both architectures ship** | vSAN ESA Witness `9.0.0.0` / `24755427` and vSAN OSA Witness `9.0.0.0` / `24755428` both in the BOM. | vSAN ESA Witness `9.1.0.0` / `25370927` and vSAN OSA Witness `9.1.0.0` / `25370925` both in the BOM. Neither architecture is retired. | DVS §1 (both) |
| **Default architecture (ESA vs OSA)** | Not stated on any retrieved page. | Not stated on any retrieved page. `EsaConfig.enabled` is a required boolean with no declared default in either spec. | **`UNVERIFIED` in both versions** — DVS gap 8 |
| **Default RAID level** | Not stated. | **ESA Auto RAID-6** — "vSAN clusters use RAID-6 as the default RAID level" with automatic configuration. Spec-corroborated: `VsanVcClusterConfigSystem_VsanGetClusterRAIDInfo` is new, and schemas `VsanAutoRAIDConfig` (`assumeAutoManagedRAID`) and `VsanAutoRAIDInfo` are **absent from the 9.0 spec**. This is a statement about RAID **level**, not about **architecture**. | DVS §7; DELTA; raw specs both tags |
| **ESA compression** | `VsanDataEfficiencyConfig.compressionEnabled` with no ESA-specific note. | "ESA Compression Enhancements". Spec text added at 9.1: *"For vSAN ESA, compression is enabled by default since 9.1.0 release, disabling compression is not supported."* **That sentence does not exist at the 9.0 tag.** No new operation. | DVS §7; raw `vi-json.yaml` both tags |
| **ESA global deduplication** | Not listed as a 9.0 feature — but the **schema already exists**: `VsanDataEfficiencyConfigEx.dedupStoreUuid` ("UUID of the global deduplication store") and `dedupPaused` are present at the 9.0 tag. | Announced as "ESA Global Deduplication — a cluster-wide and post-processing setting with encryption support". **No new operation and no new schema.** Treat "new in 9.1" as product availability, not an API change. | DVS §7; raw `vi-json.yaml` both tags |
| **Site maintenance mode** | **Does not exist.** No `VsanSiteMaintenanceSystem` managed object at the 9.0 tag. | **New.** `VsanSiteMaintenanceSystem` (`moId` `vsan-cluster-site-maintenance-system`), 5 operations: `VsanPerformSiteMaintenancePrecheck` (`System.Read`), `VsanGetSiteMaintenancePrecheckStatus`, `VsanQueryClusterSiteMaintenanceState` (`System.Read`), `VsanEnterSiteMaintenanceMode` (`Host.Config.Storage`), `VsanExitSiteMaintenanceMode`. Enter requires `faultDomainName` + `cluster`. | **DELTA**; DVS §7 |
| **Data protection health** | Does not exist. | **New.** `DataProtectionHealthSystem` (`moId` `dp-health-system`), 4 operations: `VsanQueryHealthSummary`, `VsanQueryHistoricalHealth`, `VsanGetDpClusterSilentChecks`, `VsanSetDpClusterSilentChecks`. Snapshot/replication health surfaces through vSAN health on vCenter, not through the Data Protection REST API. | **DELTA** |
| **Stretched storage across vCenter instances** | Cross-vCenter mount pre-flight `VsanRemoteDatastoreSystem_RemoteVcMountPrecheck` **already present**; all 8 remote-datastore operations present. | Announced as "vSAN Stretched Storage Across vCenter Instances" — storage sharing "across vCenter boundaries" and "across multiple VCF deployments". **No new operation.** All 8 remote-datastore operations are unchanged, and all 13 stretched-cluster operations are unchanged. | DVS §7; **DELTA** — see the gap note below |
| **Cyber recovery vSAN storage cluster** | Not present. | Announced: deployable through vCenter with integrated EDR and network isolation; mirrored in the 9.1 vSAN planning TOC as "Creating a vSAN ESA Storage Cluster for Cyber Recovery". **No operation or schema identifies it in either `SPECVIJ` or `SPECDP`.** | DVS §7, §S23; **`UNVERIFIED` at the API level** |
| **Shared ESA + OSA mounts** | Not listed. | "Shared vSAN Storage Cluster Support" — mount ESA and OSA clusters simultaneously. **No distinct operation found**; the remote-datastore family is unchanged. | DVS §7; doc-sourced |
| **Stretched-cluster API surface** | 13 `VimClusterVsanVcStretchedClusterSystem` operations; `ClusterStretchSpec` / `WitnessSpec` / `ClusterStretchNetworkSpec` / `NsxStretchClusterSpec` / `StretchClusterNetworkProfile` on the SDDC Manager side. | **Identical.** All 13 operations present; those five schemas are **byte-identical at both tags**. | `SPECVIJ` both tags; raw `sddc-manager-openapi.json` both tags |
| **Unstretch spec** | `ClusterUnstretchSpec` is an **empty object** — unstretching takes no parameters. | Gains optional **`azToRemove`** — "Availability zone which needs to be removed from the compute stretch cluster." | raw specs both tags |
| **vSAN encryption in the SDDC Manager cluster spec** | No `encryptionConfig`. | **New**: `VsanDatastoreSpec.encryptionConfig` and `VsanRemoteDatastoreSpec.encryptionConfig` → `EncryptionConfig.dataInTransitConfig` → `DataInTransitConfig` (`enable` required, `rekeyInterval` in minutes). The `EncryptionConfig` and `DataInTransitConfig` schemas **do not exist at 9.0**. | raw specs both tags |
| **`VsanDatastoreSpec.datastoreName`** | **Required.** | **Optional** — "optional in case of management domain deployment (datastore name will be auto-generated) but it is required for all Day-N operations". | raw specs both tags |
| **Cluster config queries** | 8 `VsanVcClusterConfigSystem` operations. | **10.** Adds `VsanGetClusterRAIDInfo` (`System.Read`) and `VsanGetConfigurationLimits` ("Returns configuration limits and supported values"). | **DELTA** |
| **Object placement query** | — | Adds `VsanObjectSystem_VsanQueryPhysicalPlacements` — "physical disk placement detail for the backing vSAN objects". | **DELTA** |
| **Performance** | 22 `VsanPerformanceManager` operations. | **23.** Adds `VsanPerfGetSupportedHotspotEntityTypes` — "used to build hotspot performance dashboard in a data-driven and dynamic way". | **DELTA** |
| **CNS / container volumes** | 13 `CnsVolumeManager` operations. Scale statement: up to 500 file shares per cluster (File Services). | **16.** Adds `CnsSyncVolume`, `CnsUnregisterVolume`, `CnsUpdateVolumeCrypto` ("encrypt, deep recrypt, shallow recrypt, and decrypt for the container block volumes and all the disks in the chain"). Doc-stated scale: **50,000 volumes per vCenter**; RWX file volumes and fast clone volumes for VM Service. The 50,000 figure has **no spec artifact**. | **DELTA**; DVS §7 |
| **SDDC Manager mount-validation retrieval** | Only `POST .../datastores/validations`; no way to re-read a validation by ID. | Adds `GET /v1/clusters/{id}/datastores/validations/{validationId}` (`getDatastoreMountValidation`). | **DELTA** |
| **SDDC Manager cluster filters** | `getClusters`: `isStretched`, `isImageBased`, `domainId`. `getHosts`: `fqdn`, `status`, `domainId`, `clusterId`, `networkpoolId`, `storageType`, `datastoreName`, deprecated `size` / `page`. | `getClusters` adds `managedObjectReferenceId`, `name`, `isDefault`, `isHciMeshEnabled`, `pageSize`, `pageNumber`, `useCache`. `getHosts` adds **`isVsanWitnessHost`**, `isStandalone`, `isLifecycleManaged`, `pageSize`, `pageNumber`. | raw specs both tags |
| **Bulk cluster update / primary datastore** | Not available. | New: `PATCH /v1/clusters` (`updateClusters`, body `ClustersUpdateSpec` = `clusterIds[]` 1–100 + `clustersRefreshSpec.forceRefresh`); `ClusterUpdateSpec.clusterPrimaryDatastoreUpdateSpec` (change primary datastore by `datastoreId`); `markAsDefault`; `dnsNtpUpdateSpec`. | **DELTA**; raw 9.1 spec |
| **Out-of-band remediation** | Not available. | `POST /v1/clusters/{clusterId}/remediations` → `GET .../remediations/{remediationId}` — remediate a cluster for out-of-band changes (relevant when vSAN or datastore changes are made directly in vCenter). | **DELTA** |
| **vSAN health + HCL (SDDC Manager)** | `getVsanHealthCheckByDomain`, `getVsanHealthCheckByQueryID`, `getVsanHealthCheckByTaskID`, `updateVsanHealthCheckByDomain`, `downloadVsanHcl`, `getVsanHclConfiguration`, `updateVsanHclConfiguration`, `getVsanHclAttributes`. | **Identical — all eight, same paths and operationIds.** No change. | `SPECSDDC` both tags |
| **Storage policies** | `/pbm` families (profile manager, compliance manager, placement solver) + 9 vSphere Automation storage-policy operations + `Vcenter.Datastore.DefaultPolicy_get`. | **Identical for vSAN purposes.** 9.1 adds only four **Supervisor** storage-policy operations under `/api/vcenter/namespace-management/supervisors/{supervisor}/{control-plane,workloads}/storage/policies`. | `SPECAUTO` both tags; `SPECVIJ` both tags |
| **vSAN in the vCenter REST API** | **Zero operations.** | **Zero operations.** Still no vSAN, no stretched cluster, no witness. The two `witness` hits are `Vcenter.Vcha.Cluster.Witness_*` — vCenter HA, not vSAN. | `SPECAUTO` both tags |
| **Data Protection: retention schedules** | `SnapshotSchedule.unit` / `RetentionPeriod.unit` accept `MINUTE, HOUR, DAY, WEEK, MONTH`. Single `RetentionPolicy.short_term`. | "Multiple Retention Schedules for vSAN Snapshots — daily, weekly, monthly". Spec-corroborated: new schemas `HourlyRetention`, `DailyRetention`, `WeeklyRetention`, `MonthlyRetention`, `LongTermRetention`, `DayOfWeek`; `RetentionPolicy.long_term` added; `TimeUnit` gains **`YEAR`**. | DVS §7; raw specs both tags |
| **Data Protection: ransomware recovery** | Not available. | New: `POST /snapservice/protection-groups/{pg}?action=start-ransomware-recovery&vmw-task=true` and `...?action=end-ransomware-recovery&vmw-task=true`. Note the **top-level** `/snapservice/protection-groups/...` path shape — 9.0 has only the cluster-scoped `/snapservice/clusters/{cluster}/protection-groups/...` form. | **DELTA** |
| **Data Protection: dynamic membership** | Static `target_entities` only. | `POST /snapservice/protection-groups?action=compute-members` (`Snapservice.ProtectionGroups_computeMembers`) plus new schemas `TagRule`, `LogicalOperator`, `MemberEntities`, `MembershipChangeType`, `VmMembershipInfo` — preview which VMs a create/update spec would match before committing. | **DELTA**; raw specs |
| **Data Protection: VM-level snapshots and labels** | Snapshots reachable only through a cluster + protection group. | New global family: `GET /snapservice/virtual-machines/snapshots`, `PATCH|DELETE /snapservice/virtual-machines/snapshots/{snapshot}`, `?action=add-label` / `delete-label` / `set-labels`, plus `GET|PATCH /snapservice/virtual-machines/{vm}/protection-configuration` for per-VM overrides of protection-group settings. | **DELTA** |
| **Data Protection: capabilities discovery** | None. | Six new `capabilities` endpoints — site, cluster, datastore(s), protection group — plus `GET /snapservice/sites/{site}/datastores`. Feature-detect before assuming an operation is supported at a site. | **DELTA** |
| **Data Protection: replication seeding / any-storage replication** | — | Announced [DVS §7]; spec-corroborated by new schemas `TargetStorageSpec`, `VmTargetStorageSpec`, `TargetEntityReplicationSpec`, `ReplicationTargetConfiguration`, `VmReplicationConfigSpec`. | DVS §7; raw specs |
| **Authentication** | vSAN has **no independent auth**; reuses the vCenter session (`vmware-api-session-id`). VI-JSON declares one scheme (`Session`); vSAN DP declares `basic_auth`, `api_key_auth`, `federated_identity_auth`. | **Unchanged.** Identical security schemes at both tags in all three specs. | DAUTH; `SPECVIJ` / `SPECDP` both tags |
| **PowerCLI** | `VMware.PowerCLI` → **`VCF.PowerCLI`** at 9.0. | **VCF PowerCLI 9.1** adds vSAN cmdlets: **`Get-VsanEffectiveCapacity`** and remote-datastore management. | DVS §S6, §S20 |
| **SDK coverage** | Java + Python SDK 9.0.0.0 bundle vCenter, **vSAN Data Protection**, SDDC Manager, VCF Installer. vSAN **.NET / Perl / Ruby** management SDKs deprecated at 9.0. | Java + Python SDKs extend to NSX, VCF Operations, Log Management, Fleet/SDDC Lifecycle; VODAP OpenAPI specifications added. No further vSAN SDK deprecations. | DVS §4 (both), §5 |
| **vSAN deprecations** | vSAN .NET / Perl / Ruby management SDKs deprecated. | Product-support-notes vSAN section = **"None"**. Zero vSAN operations deprecated or removed in any spec. | DVS §5 (both); **DELTA** |

---

## What did *not* change

- **The three-surface split.** SDDC Manager for stretch / mounts / domain health / HCL,
  VI-JSON for the vSAN object model, vSAN Data Protection for snapshots. Same in both
  versions, and the vCenter REST API carries no vSAN in either.
- **The `moId` singletons.** Every well-known `moId` in the 9.1 file
  (`vsan-cluster-config-system`, `vsan-stretched-cluster-system`,
  `vsan-disk-management-system`, `vsan-remote-datastore-system`,
  `vsan-cluster-space-report-system`, `vsan-cluster-object-system`,
  `vsan-cluster-resource-check-system`, `vsan-vc-capability-system`,
  `vsan-cluster-power-system`, `vsan-cluster-file-service-system`,
  `vsan-cluster-iscsi-target-system`, `cns-volume-manager`, `vsan-performance-manager`,
  `vsan-cluster-diagnostics-system`, `vsan-cluster-ioinsight-manager`,
  `vsan-upgrade-systemex`, `vsanSystemEx`, `ha-vsan-health-system`,
  `vsan-cluster-health-system`, `vsan-vcsa-deployer-system`) is present at the 9.0 tag too.
  Only `vsan-cluster-site-maintenance-system` and `dp-health-system` are 9.1-only.
- **Stretch is a `PATCH /v1/clusters/{id}` body, not a `/stretch` path.** Zero paths matching
  `stretch` in `SPECSDDC` at either version. The validate-then-execute-then-poll shape is
  the same in both.
- **The disk-group (OSA) and storage-pool (ESA) API families.** Both present at both
  versions, unchanged.
- **`VimVsanReconfigSpec.modify` semantics.** `modify: false` means the resulting
  configuration matches the spec *exactly*, resetting anything you omitted. Same wording at
  both tags.
- **The `WitnessSpec.fqdn` description bug** — "Management ip of the witness host" — at both
  versions.
- **`http://localhost:80` as the declared SDDC Manager server** — a build artifact at both
  tags. Substitute the real host over HTTPS.

---

## Deltas the research could NOT establish

- **Whether ESA or OSA is the default architecture, in either version.** The single largest
  gap in this skill. Not stated in docs, not implied by the specs. Do not resolve from
  memory; do not infer it from "ESA Auto RAID-6".
- **What API delivers "stretched storage across vCenter instances."** The feature is
  documented for 9.1 [DVS §7], but every remote-datastore and stretched-cluster operation
  exists unchanged at 9.0, `RemoteVcMountPrecheck` included. Either it is delivered through
  unchanged operations with new backend behavior, or through a surface not in this corpus.
  **Do not attribute it to a specific new call.**
- **What API delivers the "cyber recovery vSAN storage cluster."** No matching operation or
  schema in any 9.1 spec here.
- **ESA hardware requirements, in either version.** The verification route is spec-confirmed
  (`VsanGetHclInfoForEligibleDisks`, `VsanGetDiskHclConstraints`, `QueryVsanManagedDisks`,
  `RetrieveAllFlashCapabilities`, `VsanGetReleaseRecommendation`); the requirement list is
  not documented anywhere retrieved.
- **Stretched-cluster operational limits** — witness sizing, inter-site latency and
  bandwidth, hosts per site — in either version.
- **Capacity headroom thresholds** for policy, RAID, FTT, dedup/compression or disk-group
  changes, in either version.
- **Whether OSA is deprecated or on a retirement path.** No retrieved page says so, and both
  witness appliances ship in both BOMs [DVS gap 8]. Do not imply an end-of-life.
- **`ClusterUpdateSpec.prepareForStretch`** — present at both versions, one-line description,
  no documented rule for when it is required.
- **Whether the vSAN privilege annotations in `vi-json.yaml` are authoritative.** Several
  write operations declare none and `VSANVcSetPreferredFaultDomain` declares `VApp.Clone`.
  Unchanged between versions, and unreliable in both.
