# VCF 9.0 → 9.1 — vSphere Lifecycle Manager Delta

Scoped to vLCM: cluster images, image depots, hardware compatibility, remediation, and the
seam with VCF-level lifecycle. For the fleet-level upgrade delta (SDDC Manager, fleet
lifecycle, bundles) see `vcf-lifecycle-upgrade/references/deltas.md`.

**Source keys.** `DVS` = `research/vsphere-vcenter-vsan.md`; `D9.0` =
`research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of git tags
`9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`);
`SPEC9.0` / `SPEC9.1` = the `vsphere-automation` and `sddc-manager` `.ops.json` inventories
plus the raw `vcenter.yaml` at each tag.

---

## The headline: the endpoints did not move

`vsphere-automation` overall goes from **1,275 to 1,367 operations** (101 added, 9 removed,
28 newly deprecated) `[DELTA]`. **None of that touches vLCM.** The nine removals are the
entire `/hvc/*` Hybrid Linked Mode tree; none of the 28 new deprecations is under `/esx`.

Restricted to the `/esx/*` tree:

| | 9.0 | 9.1 |
|---|---|---|
| Operations under `/esx/` | **347** | **352** |
| Removed in 9.1 | — | **0** |
| Deprecated in 9.1 | 0 | **0** |
| Added in 9.1 | — | **5** |

Computed by filtering `SPEC9.0` and `SPEC9.1` on `path.startswith('/esx')`. Every 9.0
operation is present in 9.1 at the same method and path.

**The five additions, all spec-confirmed (9.1):**

| Method | Path | operationId |
|---|---|---|
| POST | `/esx/settings/clusters/{cluster}/configuration/drafts/{draft}?action=getAvailableValues&vmw-task=true` | `Esx.Settings.Clusters.Configuration.Drafts_getAvailableValues$Task` |
| POST | `/esx/settings/clusters/{cluster}/configuration/drafts/{draft}?action=importConfig&vmw-task=true` | `Esx.Settings.Clusters.Configuration.Drafts_importConfig$Task` |
| POST | `/esx/settings/clusters/{cluster}/vms/lifecycle-hooks?action=process-dynamic-update` | `Esx.Settings.Clusters.Vms.LifecycleHooks_processDynamicUpdate` |
| POST | `/esx/settings/clusters/{cluster}/vms/transition/{solution}?action=multi-source-enable&vmw-task=true` | `Esx.Settings.Clusters.Vms.Transition_multiSourceEnable$Task` |
| POST | `/esx/settings/clusters/{cluster}/vms/transition/{solution}?action=transition&vmw-task=true` | `Esx.Settings.Clusters.Vms.Transition_transition$Task` |

Two are **configuration profiles** (`/configuration/...`), which is a different
desired-state system that happens to share the `/esx/settings/clusters/{cluster}/` prefix —
not cluster images. Three are **solution VM transition / lifecycle hooks**. **None is in the
image, depot, HCL or remediation path.**

The practical consequence: an image/remediation script written against 9.0 paths does not
need path changes for 9.1. What changed is a *schema*, and it is the one below.

---

## The one change that bites: Live Patch and the apply policy

`Esx.Settings.Clusters.Policies.Apply.ConfiguredPolicySpec` — the body of
`PUT /esx/settings/clusters/{cluster}/policies/apply` — gains one property in 9.1 and
re-homes three others.

| Item | 9.0 | 9.1 |
|---|---|---|
| `software_policy_spec` | **Absent** | **New.** Type `Esx.Settings.ClusterSoftwarePolicySpec`, "added in vSphere API 9.1.0.0". Holds `enforce_hcl_validation`, `parallel_remediation_action`, `live_patch_action`, `skip_reserved_vibs_caching`. |
| `enforce_hcl_validation` (top level) | Present, no notice | Present, plus: "This field will be deprecated in the future. It is recommended to set the corresponding field in ... `software_policy_spec` instead." **Not deprecated in the 9.1 spec** — forward-looking only. |
| `parallel_remediation_action` (top level) | Present, no notice | Same forward-deprecation notice. |
| `enforce_quick_patch` (top level) | Present (added vSphere API 8.0.3.0), no notice | Same notice, **plus a documented two-way coupling with `live_patch_action`** — see below. |
| Live Patch | **Does not exist** | `Esx.Settings.ClusterLivePatchAction`, required `live_patch_mode` ∈ `DISABLE_LIVE_PATCH`, `AUTO_LIVE_PATCH`, `ENFORCE_LIVE_PATCH`. |
| `skip_reserved_vibs_caching` | Absent | New. Spec warns the extracted running image "will not be complete and that might lead to remediation failures. **NOTE: Use this option with caution.**" |

**The coupling, verbatim from the `9.1.0.0` spec** — the single most likely way to get 9.1
remediation wrong:

> `live_patch_action`: "This field should not be set together with `enforce_quick_patch`.
> When ... `livePatchMode` is set to `ENFORCE_LIVE_PATCH`, `enforce_quick_patch` will be set
> to `true` automatically. For other values, `enforce_quick_patch` will be set to `false`."

> `enforce_quick_patch`: "When this field is set to `true`, ... `livePatchMode` will be set
> to `ENFORCE_LIVE_PATCH` automatically. When this field is set to `false`, ...
> `livePatchMode` will be set to `DISABLE_LIVE_PATCH` automatically. Only one of these two
> fields should be set."

So a 9.0-era script that sets `enforce_quick_patch: false` — a perfectly ordinary thing to
carry forward — **silently disables Live Patch** on 9.1 rather than leaving it at the
cluster default. Set one field or the other, never both.

`Esx.Settings.ClusterParallelRemediationAction` is the 9.1 type behind the nested
`parallel_remediation_action`; the top-level 9.0 type
`Esx.Settings.Clusters.Policies.Apply.ParallelRemediationAction` remains.

**Corroborating prose** `[D9.1 §3.1]`: 9.1 vSphere Lifecycle Manager gains "global
remediation settings for Configuration Profile clusters; image integrity validation for
customized ESX images; optimized VIB transfer". The headline capability list adds "Live
Patching for ESX for TPM-enabled hosts covering up to 80% of patches" `[D9.1 §3.0]`.

> **UNVERIFIED.** *Which* patches are live-patchable and the full host preconditions are not
> enumerated in any source retrieved. "Image integrity validation for customized ESX images"
> and "optimized VIB transfer" appear only as What's New bullet text — **no API surface was
> identified for either**, and the `/esx` diff shows no new endpoint that obviously
> implements them. Do not attribute them to a specific call.

---

## Everything else in the vLCM API: unchanged

Verified identical (same method, same path, same operationId, not deprecated) across
`SPEC9.0` and `SPEC9.1`:

| Area | Representative operationIds |
|---|---|
| Online / offline / UMDS depots, sync, sync schedule | `Esx.Settings.Depots.Online_list`, `Esx.Settings.Depots.Offline_create$Task`, `Esx.Settings.Depots.Umds_get`, `Esx.Settings.Depots_sync$Task`, `Esx.Settings.Depots.SyncSchedule_get` |
| Depot content | `Esx.Settings.DepotContent.BaseImages_list`, `...AddOns_list`, `...Components_list` |
| Depot overrides | `Esx.Settings.Clusters.DepotOverrides_add`, `Esx.Settings.Hosts.DepotOverrides_add` |
| Cluster image read | `Esx.Settings.Clusters.Software_get`, `...Software.BaseImage_get`, `...Software.Compliance_get`, `...Software.SoftwareSpecMetadata_get` |
| Drafts | `Esx.Settings.Clusters.Software.Drafts_create`, `...Drafts.Software.BaseImage_set`, `...Drafts.Software.Components_update`, `...Drafts_validate$Task`, `...Drafts_commit$Task` |
| Remediation | `Esx.Settings.Clusters.Software_scan$Task`, `_check$Task`, `_stage$Task`, `_apply$Task` |
| Remediation reports | `...Software.Reports.LastCheckResult_get`, `...Reports.LastApplyResult_get`, `...Reports.ApplyImpact_get` |
| Hardware compatibility | all six `Esx.Hcl.*`; `...Reports.HardwareCompatibility_get` / `_check$Task` / `.Details_get`; the three override `PATCH`es |
| Hardware Support Managers (firmware) | `Esx.Settings.HardwareSupport.Managers_list` and children |
| Enablement (image vs baseline) | `Esx.Settings.Clusters.Enablement.Software_get` / `_check$Task` / `_enable$Task`; host equivalents |
| Standalone hosts | the whole `Esx.Settings.Hosts.Software*` family |
| Inventory-wide actions and reports | `Esx.Settings.Inventory_apply$Task`, `_scan$Task`, `_stage$Task`, `_check$Task`, `_transition$Task`, `Esx.Settings.Inventory.Reports.Summary.Clusters_get` |
| Image repository | `Esx.Settings.Repository.Software_list` and the `Repository.Software.Drafts.*` family |
| Task polling | `Cis.Tasks_get`, `Cis.Tasks_list`, `Cis.Tasks_cancel` |

Payload schemas verified identical property-for-property across the two tags:
`Esx.Settings.Clusters.Software.ApplySpec` (`commit`, `hosts`, `accept_eula`),
`Esx.Settings.Clusters.Software.CheckSpec`, `Esx.Settings.Clusters.Software.StageSpec`,
`Esx.Settings.Clusters.Software.Drafts.CommitSpec` (`message`, `orchestrator`),
`Esx.Settings.OrchestratorSpec` (`owner`, `owner_data`),
`Esx.Settings.BaseImageSpec`, `Esx.Settings.AddOnSpec`,
`Esx.Settings.Depots.Online.CreateSpec`, `Esx.Settings.Depots.SyncSpec`.

---

## The VCF seam: this is where 9.1 actually differs

The vCenter API stood still; the layer above it moved.

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| **Where VCF binaries live** | Split: the standalone *VCF Operations fleet management* appliance owns management-component binaries; SDDC Manager owns core-component binaries per VCF Instance. | **Software depot** is a distinct BOM component (`9.1.0.0`) inside VCF Management Services that "handles binaries for all VCF components". | `D9.0 §6.2` · `D9.1 §0.4, §3.4`; `DVS §8` |
| **Who orchestrates lifecycle** | VCF Operations is the LCM UI; SDDC Manager performs core-component upgrades. | "VCF Operations now uses the **fleet lifecycle**, **SDDC lifecycle**, and **software depot** components to orchestrate lifecycle operations on both fleet and instance-level components." | `D9.0 §6.1` · `D9.1 §0.4` |
| **Lifecycle service APIs** | `fleet-lcm` and `sddc-lcm` **do not exist** at the 9.0.0.0 tag. | Both new: `fleet-lcm` **51 ops**, `sddc-lcm` **26 ops**. | `DELTA` |
| **SDDC Manager image compliance** | Cluster-level only: `GET /v1/clusters/{id}/image-compliance` (`getClusterImageCompliance`). | Adds domain-level: `POST /v1/domains/{domainId}/image-compliance/queries` (`queryDomainImageCompliance`) and `GET /v1/domains/{domainId}/image-compliance/queries/{queryId}` (`getDomainImageComplianceQueryResponse`). | `SPEC9.0` / `SPEC9.1` `sddc-manager` |
| **SDDC Manager personalities** | `getPersonalities`, `getPersonality`, `uploadPersonality`, `uploadPersonalityFiles`, `deletePersonality`; `initiateRepositoryImagesQuery`, `getRepositoryImagesQueryResponse`. | **Identical — all seven present, none deprecated.** | `SPEC9.0` / `SPEC9.1` `sddc-manager` |
| **Orchestrator lock on cluster images** | `Esx.Settings.OrchestratorSpec` introduced at vSphere API 9.0.0.0; "used by vLCM orchestrators like SDDC Manager"; owner example `"SDDC-M"`. | **Byte-identical.** | `SPEC9.0` / `SPEC9.1` `vcenter.yaml` |
| **Cluster upgrade scale** | Baseline. | **256 simultaneous cluster upgrades**; 5,000 hosts per VCF Instance, "2x increase from VCF 9.0". | `D9.1 §3.5` |
| **ESX provisioning at scale** | Auto Deploy, **deprecated** in 9.0. | **Zero Touch Provisioning (ZTP)** — "secure UEFI and HTTPS-based network boot" — replaces it. Provisioning, not remediation, but it changes how hosts arrive at a cluster. | `DVS §5` · `D9.1 §3.1` |

> **UNVERIFIED.** How the VCF 9.1 **software depot** relates to the vCenter-level vLCM depot
> (`/esx/settings/depots/*`) is **not stated in any source consulted**. Both exist in a 9.1
> deployment. Do not assert that configuring one configures the other, and do not tell a
> user the vCenter depot endpoints are superseded — they are present and non-deprecated in
> `SPEC9.1`.

> **UNVERIFIED.** No source consulted enumerates which vCenter objects VCF claims exclusive
> lifecycle ownership over in either version. `OrchestratorSpec` is the mechanism; there is
> no documented policy behind it. Route the decision to the customer's VCF operating model.

---

## Baselines across the two versions

The conflict recorded in both version files is **9.0-era and unresolved**, and it is not
re-litigated by anything in 9.1:

- VCF 9.0 release notes `[DVS §5, S5]`: baselines and baseline groups for cluster management
  are "**no longer supported in vCenter 9.0**", listed under *removals*.
- vSphere 9.0 standalone guide `[DVS §8, S14]`: baselines are "**deprecated**", retained to
  "Update and patch ESX hosts only of version 8.x" and to update third-party software.

9.1 adds one data point that cuts neither way cleanly: a doc topic titled "**Transitioning
from vSphere Lifecycle Manager Baselines to vSphere Lifecycle Manager Images**" `[DVS S25]`
exists in the 9.1 upgrade documentation — its existence implies baseline-managed clusters
still show up at 9.1 upgrade time. **The page body was never fetched.** Do not reconstruct
its procedure.

**What the specs say, and it is the same in both versions:** the string `baseline` matches
**zero operations** in `SPEC9.0` and **zero** in `SPEC9.1`. Patch Manager APIs were removed
in vCenter 9.0 `[DVS §5, S5]` and did not return in 9.1. There is no baseline REST API to
automate against in either version — which settles the *automation* question while leaving
the *support* question open.

---

## Migration checklist for a 9.0 vLCM script moving to 9.1

1. **No path changes required.** All 347 `/esx/*` operations you could have used at 9.0 exist
   at 9.1, same method, same path, not deprecated.
2. **No `ApplySpec` / `CheckSpec` / `StageSpec` / `CommitSpec` changes.** Identical schemas.
3. **Audit every write to `policies/apply`.** If your script sets `enforce_quick_patch`,
   understand that on 9.1 it now also sets `live_patch_mode` — `false` maps to
   `DISABLE_LIVE_PATCH`. If you want Live Patch, move to
   `software_policy_spec.live_patch_action` and stop setting `enforce_quick_patch`.
4. **Decide where `enforce_hcl_validation` lives.** It exists top-level and inside
   `software_policy_spec` on 9.1. Read `/policies/apply/effective` after the change and
   confirm the value you expect — the default in both places is "will **not** prevent
   remediation".
5. **Re-check ownership.** If the estate moved to VCF 9.1, cluster images may now be tracked
   through fleet lifecycle / SDDC lifecycle. Query
   `POST /v1/domains/{domainId}/image-compliance/queries` on SDDC Manager (9.1-only) before
   assuming direct vCenter commits are yours to make.
