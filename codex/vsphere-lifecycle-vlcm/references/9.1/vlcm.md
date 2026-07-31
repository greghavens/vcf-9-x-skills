# VCF 9.1 — vSphere Lifecycle Manager (vLCM) Reference

**Scope:** vCenter / ESX 9.1.0.0 as shipped in VMware Cloud Foundation 9.1. Everything here
is `[9.1]` unless explicitly tagged otherwise.

**Sources.** `DVS` = `research/vsphere-vcenter-vsan.md`; `D9.1` =
`research/vcf-core-9.1-and-deltas.md`; `D9.0` = `research/vcf-core-9.0.md`.
`SPEC9.1` = `research/spec-inventory/9.1__vsphere-automation.ops.json` (1,367 operations,
spec version `9.1.0.0`, from git tag `9.1.0.0` of `github.com/vmware/vcf-api-specs`) and the
raw `specifications/vsphere/openapi/automation/vcenter.yaml` at the same tag.
`SPECSDDC9.1` = `research/spec-inventory/9.1__sddc-manager.ops.json` (423 operations).
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md`.
Every endpoint below was matched in `SPEC9.1` (or `SPECSDDC9.1` where noted) by
`operationId` — each is marked **spec-confirmed (9.1)**. Schema fields and enum values are
quoted from `vcenter.yaml` at the `9.1.0.0` tag.

**Base path and separator.** `https://{host}/api` + `/esx/settings/...`. Full URL:
`https://vcenter.example.com/api/esx/settings/clusters/{cluster}/software`. The hyphenated
`/api/esx-settings/...` does **not** exist — zero operations in `SPEC9.1` contain the string
`esx-settings`. The hyphenated form is a documentation-site URL slug only.

**Authentication is out of scope here.** vCenter session handling and the `api_key_auth`
(`vmware-api-session-id`) scheme belong to `vcf-foundation`. 9.1 additionally offers OAuth
2.0 API tokens `[D9.1 §3.1]` — also `vcf-foundation`'s territory.

**How much moved from 9.0.** Almost nothing at this layer. The `/esx/*` tree goes from
**347 operations at 9.0 to 352 at 9.1 — 5 added, 0 removed, 0 deprecated.** All five
additions are in the *configuration profile* and *VM solution transition* areas, not in the
image, depot, HCL or remediation path. The behavioral change in 9.1 is in the **apply
policy schema** (Live Patch), not in the endpoints. See `../deltas.md`.

> **Documentation-derived, not live-validated** (captured 2026-07-31).
> **`POST .../software?action=apply` reboots hosts** and is production-affecting — except
> where Live Patch applies, which is new in 9.1 and has its own constraints. Read
> Prerequisites, and run `?action=check` before `?action=apply`.

---

## Contents

- [Prerequisites](#prerequisites)
  - P1 — An image depot is configured and synced
  - P2 — The cluster is image-managed, not baseline-managed
  - P3 — Hardware compatibility (HCL) data is present and the report is clean
  - P4 — The apply policy is what you think it is (and 9.1 moved the fields)
  - P5 — The cluster's image may be owned by SDDC Manager, not by you
  - P6 — Privileges for image and remediation operations
  - P7 — Host eligibility for image management
  - P8 — Items the research could not verify
- [Depots](#depots)
- [Cluster image: read the current state](#cluster-image-read-the-current-state)
- [Cluster image: drafts](#cluster-image-drafts)
- [Hardware compatibility](#hardware-compatibility)
- [Remediation: scan, check, stage, apply](#remediation-scan-check-stage-apply)
- [Apply policy — and what 9.1 changed](#apply-policy--and-what-91-changed)
- [Worked example — set a base image on a cluster and remediate](#worked-example--set-a-base-image-on-a-cluster-and-remediate)
- [Standalone hosts](#standalone-hosts)
- [Where VCF meets vLCM in 9.1](#where-vcf-meets-vlcm-in-91)
- [Baselines: the recorded conflict](#baselines-the-recorded-conflict)
- [Task polling](#task-polling)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what
must hold, **how to verify it**, the version it applies to, and whether 9.0 differs.

### P1 — An image depot is configured and synced `[9.1]`

**Must be true:** at least one depot supplying base images, add-ons and components is
registered and synced. Without content, a draft cannot be given a base image version.

**How to verify** (all **spec-confirmed (9.1)**):

| Purpose | Call | operationId |
|---|---|---|
| List online depots | `GET /api/esx/settings/depots/online` | `Esx.Settings.Depots.Online_list` |
| List offline depots | `GET /api/esx/settings/depots/offline` | `Esx.Settings.Depots.Offline_list` |
| Read UMDS depot config | `GET /api/esx/settings/depots/umds` | `Esx.Settings.Depots.Umds_get` |
| Read sync schedule | `GET /api/esx/settings/depots/sync-schedule` | `Esx.Settings.Depots.SyncSchedule_get` |
| Confirm content is present | `GET /api/esx/settings/depot-content/base-images` | `Esx.Settings.DepotContent.BaseImages_list` |

Listing base images is the real test. Force a sync with
`POST /api/esx/settings/depots?action=sync&vmw-task=true` (`Esx.Settings.Depots_sync$Task`).

**The VCF-level complication in 9.1.** VCF 9.1 introduces a **software depot** as a distinct
BOM component inside VCF Management Services, which "handles binaries for all VCF
components", and "VCF Operations now uses the fleet lifecycle, SDDC lifecycle, and software
depot components to orchestrate lifecycle operations on both fleet and instance-level
components" `[D9.1 §0.4, §3.4; DVS §8]`. That is a *different depot* from the vCenter-level
vLCM depot configured above. Both exist in a 9.1 VCF deployment.

> **UNVERIFIED.** Whether, and how, the VCF 9.1 software depot feeds or replaces the
> vCenter-level vLCM depot configuration is **not stated** in any source consulted. The
> vCenter endpoints above are unchanged and present in `SPEC9.1`; the relationship between
> the two depots is not documented in what was retrieved. Do not assert that configuring one
> configures the other.

**9.0 difference:** the vCenter endpoints are identical. The VCF-level software-depot
component does not exist in 9.0, where binaries are split between the fleet-management
appliance and SDDC Manager `[D9.0 §6.2]`.

### P2 — The cluster is image-managed, not baseline-managed `[9.1]`

**Must be true:** vLCM image management is enabled on the cluster. `apply` returns
`Vapi.Std.Errors.InvalidArgument` when "the cluster is not managed with a single software
specification" (verbatim, `9.1.0.0` spec).

**How to verify:** `GET /api/esx/settings/clusters/{cluster}/enablement/software`
(`Esx.Settings.Clusters.Enablement.Software_get`, **spec-confirmed (9.1)**). Response is
`Esx.Settings.Clusters.Enablement.Software.Info`; the required boolean **`enabled`** is the
answer.

**To transition a cluster that is not enabled:**
1. `POST /api/esx/settings/clusters/{cluster}/enablement/software?action=check&vmw-task=true`
   — `Esx.Settings.Clusters.Enablement.Software_check$Task`.
2. `PUT /api/esx/settings/clusters/{cluster}/enablement/software?vmw-task=true` —
   `Esx.Settings.Clusters.Enablement.Software_enable$Task`, body
   `Esx.Settings.Clusters.Enablement.Software.EnableSpec` whose one **required** property is
   `skip_software_check` (boolean). Both **spec-confirmed (9.1)**, both requiring
   `VcIntegrity.lifecycleSettings.Write`.

> **UNVERIFIED.** Reversibility of image enablement is not stated in the spec, and the 9.1
> doc topic "Transitioning from vSphere Lifecycle Manager Baselines to vSphere Lifecycle
> Manager Images" `[DVS S25]` was captured **by URL only — its body was never fetched**. If
> a user needs the transition procedure, route them to that page rather than paraphrasing a
> page nobody read.

**9.0 difference:** none. Identical paths and schemas.

### P3 — Hardware compatibility (HCL) data is present and the report is clean `[9.1]`

**Must be true:** HCL/BCG compatibility data has been downloaded, and the cluster's
hardware-compatibility report for the *target* image does not show `INCOMPATIBLE`.

**How to verify** (all **spec-confirmed (9.1)**):
- `GET /api/esx/settings/clusters/{cluster}/software/reports/hardware-compatibility` —
  `Esx.Settings.Clusters.Software.Reports.HardwareCompatibility_get`.
- `GET /api/esx/hcl/compatibility-data/status` — `Esx.Hcl.CompatibilityData_get`, returning
  `Esx.Hcl.CompatibilityData.Status` with required `updated_at` and `notifications`.

Report `status` values, verbatim: `COMPATIBLE`, `INCOMPATIBLE`, `HCL_DATA_UNAVAILABLE`,
`UNAVAILABLE`, `NO_FIRMWARE_PROVIDER`. The spec marks `HCL_DATA_UNAVAILABLE` and
`NO_FIRMWARE_PROVIDER` as "Never returned by the HCL compliance APIs" — `UNAVAILABLE` is the
real "cannot determine".

**Refresh:** `POST /api/esx/hcl/compatibility-data?action=download&vmw-task=true`
(`Esx.Hcl.CompatibilityData_update$Task`), then
`POST /api/esx/settings/clusters/{cluster}/software/reports/hardware-compatibility?action=check&vmw-task=true`
(`Esx.Settings.Clusters.Software.Reports.HardwareCompatibility_check$Task`, **no request
body**).

**The interaction with P4, and the 9.1 twist:** an `INCOMPATIBLE` report blocks remediation
only when `enforce_hcl_validation` is set. In 9.1 that flag exists in **two places** — the
legacy top-level field and the new `software_policy_spec.enforce_hcl_validation`. Both are
documented as "If missing or `null`, hardware compatibility issues will not prevent
remediation." Setting one and reading the other is a live way to believe you are protected
when you are not. See P4.

**9.0 difference:** the endpoints and enums are identical; 9.0 has only the single top-level
`enforce_hcl_validation`.

### P4 — The apply policy is what you think it is (and 9.1 moved the fields) `[9.1]`

**Must be true:** you know what remediation will do to running VMs, and you know **which**
copy of each duplicated policy field is in effect.

**How to verify** (all **spec-confirmed (9.1)**):
- `GET /api/esx/settings/clusters/{cluster}/policies/apply` —
  `Esx.Settings.Clusters.Policies.Apply_get` — configured on this cluster.
- `GET /api/esx/settings/clusters/{cluster}/policies/apply/effective` —
  `Esx.Settings.Clusters.Policies.Apply.Effective_get` — **read this one.** It folds in the
  vCenter defaults from `GET /api/esx/settings/defaults/clusters/policies/apply`
  (`Esx.Settings.Defaults.Clusters.Policies.Apply_get`).

Set with `PUT /api/esx/settings/clusters/{cluster}/policies/apply`
(`Esx.Settings.Clusters.Policies.Apply_set`).

**What 9.1 changed.** `Esx.Settings.Clusters.Policies.Apply.ConfiguredPolicySpec` gains a
nested `software_policy_spec` object (schema `Esx.Settings.ClusterSoftwarePolicySpec`, "added
in vSphere API 9.1.0.0"), and three existing top-level fields carry a new instruction in
their descriptions — verbatim: "This field will be deprecated in the future. It is
recommended to set the corresponding field in
`Esx.Settings.Clusters.Policies.Apply.ConfiguredPolicySpec.software_policy_spec` instead."
The three are `enforce_hcl_validation`, `parallel_remediation_action` and
`enforce_quick_patch`. **They are not deprecated in the 9.1 spec — the notice is
forward-looking.** Do not tell a user they are deprecated today; tell them where the
successor field lives.

Full field list in [Apply policy](#apply-policy--and-what-91-changed) below.

**9.0 difference:** 9.0 has no `software_policy_spec` and no Live Patch; the three fields
carry no deprecation notice there.

### P5 — The cluster's image may be owned by SDDC Manager, not by you `[9.1]` `[VCF boundary]`

**Must be true:** before committing a new desired image in a VCF deployment, you have
established whether the cluster's desired state is under SDDC Manager's control.

**Evidence, verbatim from the `9.1.0.0` spec.** `Esx.Settings.Clusters.Software.Drafts.CommitSpec`
carries an optional `orchestrator` object of type `Esx.Settings.OrchestratorSpec` (identical
to 9.0):

> "It is used by vLCM orchestrators like SDDC Manager to manage the desired state. For a
> non-orchestrator user i.e. a VC user, it must be unset."
>
> "Setting it prevents other users from modifying the committed desired state."

and on `OrchestratorSpec.owner`:

> "Owner of the desired state. It can be the name of the owner as set by orchestrator. For
> example, for a software specification created by SDDC manager, it could be `"SDDC-M"`."

**How to verify:**
- From vCenter: `GET /api/esx/settings/clusters/{cluster}/software`
  (`Esx.Settings.Clusters.Software_get`) and
  `GET /api/esx/settings/clusters/{cluster}/software/software-spec-metadata`
  (`Esx.Settings.Clusters.Software.SoftwareSpecMetadata_get`), both **spec-confirmed (9.1)**.
- From SDDC Manager, **spec-confirmed (9.1)** in `SPECSDDC9.1`:
  `GET /v1/clusters/{id}/image-compliance` (`getClusterImageCompliance`) and — **new in
  9.1** — the domain-scoped pair `POST /v1/domains/{domainId}/image-compliance/queries`
  (`queryDomainImageCompliance`) and
  `GET /v1/domains/{domainId}/image-compliance/queries/{queryId}`
  (`getDomainImageComplianceQueryResponse`). The domain query is the efficient way to ask
  "which clusters in this workload domain have drifted from their VCF-assigned image."

**If it is SDDC-Manager-owned**, drive the change through `vcf-lifecycle-upgrade`. In 9.1
the lifecycle orchestration story also runs through fleet lifecycle and SDDC lifecycle in
VCF Management Services `[D9.1 §0.2, §0.4]` — all of which is that skill's scope, not this
one's.

> **UNVERIFIED — say so when it matters.** No source consulted contains an authoritative,
> enumerated statement of which vCenter objects VCF claims exclusive lifecycle ownership
> over. `OrchestratorSpec` is a *mechanism* (an owner field that locks a committed desired
> state), not a *policy*. Present the check; route the decision to the customer's VCF
> operating model. Do not manufacture an ownership rule.

**9.0 difference:** `OrchestratorSpec` and `CommitSpec` are identical in 9.0. The domain-level
image-compliance pair is 9.1-only — 9.0 has cluster-level only.

### P6 — Privileges for image and remediation operations `[9.1]`

**Must be true:** the caller holds the right `VcIntegrity.*` privileges, both at operation
level and on the target `ClusterComputeResource`. Quoted from the operation descriptions in
`vcenter.yaml` at the `9.1.0.0` tag:

| Operation | Privileges required |
|---|---|
| `Esx.Settings.Clusters.Software_apply$Task` | `VcIntegrity.lifecycleSoftwareRemediation.Write` **and** `VcIntegrity.lifecycleHealth.Read` |
| `Esx.Settings.Clusters.Software_check$Task` | `VcIntegrity.lifecycleSoftwareRemediation.Read` **and** `VcIntegrity.lifecycleHealth.Read` |
| Draft writers (`Drafts_create`, `..._set`) | `VcIntegrity.lifecycleSoftwareSpecification.Write` |
| Draft/compliance readers | `VcIntegrity.lifecycleSoftwareSpecification.Read` |
| `Esx.Settings.Depots_sync$Task`, enablement enable/check | `VcIntegrity.lifecycleSettings.Write` |
| HCL data download, HCL report check | `VcIntegrity.HardwareCompatibility.Read` |

The spec states each requirement **twice** — once for operation execution and once for the
`ClusterComputeResource` referenced by the `cluster` parameter. A global grant without the
cluster-scoped grant still fails.

**9.0 difference:** the same privilege strings on the same operations.

### P7 — Host eligibility for image management `[9.0-sourced]`

**Must be true:** the hosts can be image-managed. The constraint list this skill has —
hosts must be **vSphere 7.0 or later, stateful, identical hardware from the same vendor, and
running only integrated solutions** (vSAN, vSphere Supervisor, NSX, vSphere HA) — comes from
the **VCF 9.0** programming guide `[DVS §8, S15]`. The research did **not** retrieve a 9.1
restatement.

**How to verify:** run `Esx.Settings.Clusters.Enablement.Software_check$Task`
(**spec-confirmed (9.1)**) rather than reasoning from the list. That operation exists to
report why a cluster cannot be enabled, and it reflects the running build.

**Also 9.0-sourced, verbatim:** "The only limitation for managing the life cycle of a
standalone host through the VMware Cloud Foundation API, is that you can't update the
firmware of the host." Not restated for 9.1 in anything retrieved. Label it 9.0-sourced when
you pass it on.

### P8 — Items the research could not verify `[9.1]`

1. **Relationship between the VCF 9.1 software depot and the vCenter vLCM depot** — see P1.
2. **Reversibility of image enablement**, and the contents of the 9.1 baselines→images
   transition topic — see P2; URL captured, body never fetched `[DVS S25]`.
3. **Which objects VCF exclusively owns** — see P5. No authoritative enumeration exists.
4. **Live Patch preconditions.** The 9.1 What's New says "Live Patching for ESX for
   TPM-enabled hosts covering up to 80% of patches" `[D9.1 §3.0]`. The spec defines the
   *modes* (below) but the research did **not** retrieve a source enumerating which patches
   are live-patchable or the full host preconditions beyond "TPM-enabled". Do not promise a
   reboot-free remediation.
5. **The vLCM reference pages.** `[DVS S37][S38]` records that
   `developer.broadcom.com/xapis/vsphere-automation-api/latest/esx/...` returned navigation
   only on repeated fetches. Everything here comes from the OpenAPI specification.

---

## Depots

All **spec-confirmed (9.1)**; identical to 9.0. Base path `https://{host}/api`.

| Method | Path | operationId |
|---|---|---|
| GET | `/esx/settings/depots/online` | `Esx.Settings.Depots.Online_list` |
| POST | `/esx/settings/depots/online` | `Esx.Settings.Depots.Online_create` |
| GET | `/esx/settings/depots/online/{depot}` | `Esx.Settings.Depots.Online_get` |
| PATCH | `/esx/settings/depots/online/{depot}` | `Esx.Settings.Depots.Online_update` |
| DELETE | `/esx/settings/depots/online/{depot}` | `Esx.Settings.Depots.Online_delete` |
| DELETE | `/esx/settings/depots/online/{depot}?vmw-task=true` | `Esx.Settings.Depots.Online_delete$Task` |
| GET | `/esx/settings/depots/online/{depot}/content` | `Esx.Settings.Depots.Online.Content_get` |
| POST | `/esx/settings/depots/online/{depot}?action=flush&vmw-task=true` | `Esx.Settings.Depots.Online_flush$Task` |
| GET | `/esx/settings/depots/offline` | `Esx.Settings.Depots.Offline_list` |
| POST | `/esx/settings/depots/offline?vmw-task=true` | `Esx.Settings.Depots.Offline_create$Task` |
| POST | `/esx/settings/depots/offline?action=createFromHost&vmw-task=true` | `Esx.Settings.Depots.Offline_createFromHost$Task` |
| GET | `/esx/settings/depots/offline/{depot}` | `Esx.Settings.Depots.Offline_get` |
| GET | `/esx/settings/depots/offline/{depot}/content` | `Esx.Settings.Depots.Offline.Content_get` |
| DELETE | `/esx/settings/depots/offline/{depot}?vmw-task=true` | `Esx.Settings.Depots.Offline_delete$Task` |
| GET/PUT/PATCH/DELETE | `/esx/settings/depots/umds` | `Esx.Settings.Depots.Umds_get` / `_set` / `_update` / `_delete` |
| GET | `/esx/settings/depots/umds/content` | `Esx.Settings.Depots.Umds.Content_get` |
| GET/PUT | `/esx/settings/depots/sync-schedule` | `Esx.Settings.Depots.SyncSchedule_get` / `_set` |
| POST | `/esx/settings/depots?action=sync&vmw-task=true` | `Esx.Settings.Depots_sync$Task` |

**Depot content:**

| Method | Path | operationId |
|---|---|---|
| GET | `/esx/settings/depot-content/base-images` | `Esx.Settings.DepotContent.BaseImages_list` |
| GET | `/esx/settings/depot-content/base-images/versions/{version}` | `Esx.Settings.DepotContent.BaseImages.Versions_get` |
| GET | `/esx/settings/depot-content/add-ons` | `Esx.Settings.DepotContent.AddOns_list` |
| GET | `/esx/settings/depot-content/add-ons/{name}/versions/{version}` | `Esx.Settings.DepotContent.AddOns.Versions_get` |
| GET | `/esx/settings/depot-content/components` | `Esx.Settings.DepotContent.Components_list` |
| GET | `/esx/settings/depot-content/components/{name}/versions/{version}` | `Esx.Settings.DepotContent.Components.Versions_get` |

**Overrides:** `GET|POST /esx/settings/clusters/{cluster}/depot-overrides[?action=add|remove]`
(`Esx.Settings.Clusters.DepotOverrides_get` / `_add` / `_remove`) and
`/esx/settings/hosts/{host}/depot-overrides` (`Esx.Settings.Hosts.DepotOverrides_get` /
`_add` / `_remove`).

**Bodies** (unchanged from 9.0):

`Esx.Settings.Depots.Online.CreateSpec` — **required: `location`**.

```json
{
  "location": "https://depot.example.com/vmw-depot/index.xml",
  "description": "corporate mirror",
  "enabled": true
}
```

`Esx.Settings.Depots.SyncSpec` — sole property `cleanup` (boolean). The spec warns "Depot
cleanup temporarily removes the online depot content which may be needed for image
operations" — do not sync with `cleanup: true` while an image operation is running.

**Hardware Support Managers (firmware):** `Esx.Settings.HardwareSupport.Managers_list`,
`Esx.Settings.HardwareSupport.Managers.Packages_list`,
`Esx.Settings.HardwareSupport.Managers.Packages.Versions_get` — all **spec-confirmed (9.1)**.

---

## Cluster image: read the current state

All **spec-confirmed (9.1)**, under `/esx/settings/clusters/{cluster}/software`.

| Purpose | Method + suffix | operationId |
|---|---|---|
| Whole desired image | `GET` (no suffix) | `Esx.Settings.Clusters.Software_get` |
| Base image | `GET /base-image` | `Esx.Settings.Clusters.Software.BaseImage_get` |
| OEM add-on | `GET /add-on` | `Esx.Settings.Clusters.Software.AddOn_get` |
| Components (explicit) | `GET /components` | `Esx.Settings.Clusters.Software.Components_list` |
| Components (resolved) | `GET /effective-components` | `Esx.Settings.Clusters.Software.EffectiveComponents_list` |
| Removed components | `GET /removed-components` | `Esx.Settings.Clusters.Software.RemovedComponents_list` |
| Firmware / HSP | `GET /hardware-support` | `Esx.Settings.Clusters.Software.HardwareSupport_get` |
| Solutions (vSAN, NSX…) | `GET /solutions` | `Esx.Settings.Clusters.Software.Solutions_list` |
| Compliance vs desired | `GET /compliance` | `Esx.Settings.Clusters.Software.Compliance_get` |
| A specific commit | `GET /commits/{commit}` | `Esx.Settings.Clusters.Software.Commits_get` |
| Image metadata (incl. ownership) | `GET /software-spec-metadata` | `Esx.Settings.Clusters.Software.SoftwareSpecMetadata_get` |
| Recommended images | `GET /recommendations` | `Esx.Settings.Clusters.Software.Recommendations_get` |
| Generate recommendations | `POST /recommendations?action=generate&vmw-task=true` | `Esx.Settings.Clusters.Software.Recommendations_generate$Task` |
| Export the image | `POST ?action=export` | `Esx.Settings.Clusters.Software_export` |
| Image installed on hosts | `GET /esx/settings/clusters/{cluster}/installed-images` | `Esx.Settings.Clusters.InstalledImages_get` |
| Extract installed image | `POST /esx/settings/clusters/{cluster}/installed-images?action=extract&vmw-task=true` | `Esx.Settings.Clusters.InstalledImages_extract$Task` |

**Reading compliance.** `GET .../software/compliance` returns
`Esx.Settings.ClusterCompliance`. Enums verbatim:

- `status`: `COMPLIANT`, `NON_COMPLIANT`, `INCOMPATIBLE`, `UNAVAILABLE` — where
  `NON_COMPLIANT` is "Target version is greater than current version" and `INCOMPATIBLE` is
  "Target state cannot be applied due to conflict or missing dependencies or the target
  state is lesser than the current version."
- `impact`: `NO_IMPACT`, `PARTIAL_MAINTENANCE_MODE_REQUIRED`, `MAINTENANCE_MODE_REQUIRED`,
  `REBOOT_REQUIRED`, `UNKNOWN`.
- `stage_status` (only meaningful when `status` is `NON_COMPLIANT`): `STAGED`, `NOT_STAGED`.

`impact` is the field to quote for "will this reboot my hosts" — and in 9.1 it is also the
field to check before assuming Live Patch will spare you the reboot.

**Alternative images** (per-host-group variants in one cluster) are under
`/software/alternative-images/{image}/...`, operationIds
`Esx.Settings.Clusters.Software.AlternativeImages.*`.

**Fleet-wide reporting:** `GET /esx/settings/inventory/reports/summary/clusters`
(`Esx.Settings.Inventory.Reports.Summary.Clusters_get`) and `.../summary/hosts`
(`...Summary.Hosts_get`), **spec-confirmed (9.1)** and also present in 9.0 — useful for "how
many clusters are image-managed across this vCenter".

---

## Cluster image: drafts

Committed images are not editable. Create a draft, edit, commit. All **spec-confirmed
(9.1)**.

| Step | Method + path | operationId |
|---|---|---|
| List drafts | `GET .../software/drafts` | `Esx.Settings.Clusters.Software.Drafts_list` |
| Create draft | `POST .../software/drafts` | `Esx.Settings.Clusters.Software.Drafts_create` |
| Import a spec as a draft | `POST .../software/drafts?action=import-software-spec` | `Esx.Settings.Clusters.Software.Drafts_importSoftwareSpec` |
| Read draft | `GET .../software/drafts/{draft}` | `Esx.Settings.Clusters.Software.Drafts_get` |
| Discard draft | `DELETE .../software/drafts/{draft}` | `Esx.Settings.Clusters.Software.Drafts_delete` |
| Set base image | `PUT .../drafts/{draft}/software/base-image` | `Esx.Settings.Clusters.Software.Drafts.Software.BaseImage_set` |
| Set / clear add-on | `PUT` / `DELETE .../drafts/{draft}/software/add-on` | `...Drafts.Software.AddOn_set` / `_delete` |
| Add or remove components | `PATCH .../drafts/{draft}/software/components` | `...Drafts.Software.Components_update` |
| Set one component | `PUT .../drafts/{draft}/software/components/{component}` | `...Drafts.Software.Components_set` |
| Set firmware / HSP | `PUT .../drafts/{draft}/software/hardware-support` | `...Drafts.Software.HardwareSupport_set` |
| Validate | `POST .../drafts/{draft}?action=validate&vmw-task=true` | `Esx.Settings.Clusters.Software.Drafts_validate$Task` |
| Scan against draft | `POST .../drafts/{draft}?action=scan&vmw-task=true` | `Esx.Settings.Clusters.Software.Drafts_scan$Task` |
| **Commit** | `POST .../drafts/{draft}?action=commit&vmw-task=true` | `Esx.Settings.Clusters.Software.Drafts_commit$Task` |

**Two spec behaviors to code against:**

- `Drafts_create` takes **no request body**, returns **201** with a bare JSON string (the
  draft id, resource type `com.vmware.esx.settings.draft`), and errors
  `Vapi.Std.Errors.AlreadyExists` "If there is already a draft created by this user" —
  **one draft per user per cluster.** Reuse or delete; retrying does not help.
- "It will be deleted, when the draft is committed successfully. If a desired document is
  missing, then this operation will create an empty draft."

**Bodies** (identical to 9.0):

`Esx.Settings.BaseImageSpec` — **required: `version`**. `{"version": "9.1.0-<build>"}`.

`Esx.Settings.AddOnSpec` — **required: `name`, `version`**.

`Esx.Settings.Clusters.Software.Drafts.Software.Components.UpdateSpec`:

```json
{
  "components_to_set": { "<component-name>": "<version>" },
  "components_to_delete": [ "<component-name>" ]
}
```

`Esx.Settings.HardwareSupportSpec` — **required: `packages`**, a map keyed by Hardware
Support Manager name to `Esx.Settings.HardwareSupportPackageSpec` (`pkg`, `version`).

`Esx.Settings.Clusters.Software.Drafts.CommitSpec`:

```json
{ "message": "9.1 patch baseline for cluster prod-01" }
```

**Leave `orchestrator` unset** — "For a non-orchestrator user i.e. a VC user, it must be
unset." See P5.

---

## Hardware compatibility

All **spec-confirmed (9.1)**; identical set to 9.0.

| Purpose | Method + path | operationId |
|---|---|---|
| HCL data freshness | `GET /esx/hcl/compatibility-data/status` | `Esx.Hcl.CompatibilityData_get` |
| Download HCL data | `POST /esx/hcl/compatibility-data?action=download&vmw-task=true` | `Esx.Hcl.CompatibilityData_update$Task` |
| Per-host report | `GET /esx/hcl/hosts/{host}/compatibility-report` | `Esx.Hcl.Hosts.CompatibilityReport_get` |
| Generate per-host report | `POST /esx/hcl/hosts/{host}/compatibility-report?vmw-task=true` | `Esx.Hcl.Hosts.CompatibilityReport_create$Task` |
| Releases a host supports | `GET /esx/hcl/hosts/{host}/compatibility-releases` | `Esx.Hcl.Hosts.CompatibilityReleases_list` |
| Fetch a generated report | `GET /esx/hcl/reports/{report}` | `Esx.Hcl.Reports_get` |
| Cluster report vs desired image | `GET .../software/reports/hardware-compatibility` | `Esx.Settings.Clusters.Software.Reports.HardwareCompatibility_get` |
| Cluster report detail | `GET .../software/reports/hardware-compatibility/details` | `...HardwareCompatibility.Details_get` |
| Re-run cluster check | `POST .../software/reports/hardware-compatibility?action=check&vmw-task=true` | `...HardwareCompatibility_check$Task` |
| Override PCI device VCG entry | `PATCH .../hardware-compatibility/pci-device-overrides/vcg-entries?vmw-task=true` | `...PciDeviceOverrides.VcgEntries_update$Task` |
| Override storage device VCG entry | `PATCH .../hardware-compatibility/storage-device-overrides/vcg-entries?vmw-task=true` | `...StorageDeviceOverrides.VcgEntries_update$Task` |
| Override storage compliance status | `PATCH .../hardware-compatibility/storage-device-overrides/compliance-status?vmw-task=true` | `...StorageDeviceOverrides.ComplianceStatus_update$Task` |

`Esx.Hcl.Hosts.CompatibilityReleases_list` answers "which ESX version can this host take"
directly. **When an override is appropriate is UNVERIFIED** — no doc prose on override
policy was retrieved; treat it as a support-visible decision.

---

## Remediation: scan, check, stage, apply

All **spec-confirmed (9.1)**, on `/esx/settings/clusters/{cluster}/software`, all
asynchronous (HTTP 202 with a bare task-id string).

| Step | Call | operationId | Body schema |
|---|---|---|---|
| Scan | `POST ?action=scan&vmw-task=true` | `Esx.Settings.Clusters.Software_scan$Task` | — |
| Check (readiness gate) | `POST ?action=check&vmw-task=true` | `Esx.Settings.Clusters.Software_check$Task` | `Esx.Settings.Clusters.Software.CheckSpec` |
| Stage (pre-download) | `POST ?action=stage&vmw-task=true` | `Esx.Settings.Clusters.Software_stage$Task` | `Esx.Settings.Clusters.Software.StageSpec` |
| **Apply (remediate)** | `POST ?action=apply&vmw-task=true` | `Esx.Settings.Clusters.Software_apply$Task` | `Esx.Settings.Clusters.Software.ApplySpec` |
| Last check result | `GET /reports/last-check-result` | `Esx.Settings.Clusters.Software.Reports.LastCheckResult_get` | — |
| Last apply result | `GET /reports/last-apply-result` | `Esx.Settings.Clusters.Software.Reports.LastApplyResult_get` | — |
| Predicted impact | `GET /reports/apply-impact` | `Esx.Settings.Clusters.Software.Reports.ApplyImpact_get` | — |

**`ApplySpec` — the whole schema, unchanged from 9.0, three optional properties:**

| Field | Type | Meaning (from the spec) |
|---|---|---|
| `commit` | string | "The minimum commit identifier of the desired software document to be used" — omitted means the **latest** commit. |
| `hosts` | array of `HostSystem` ids | "The specific hosts within the cluster to be considered" — omitted means apply "will remediate **all** hosts within the cluster." |
| `accept_eula` | boolean | If omitted, apply "could fail due to the EULA not being accepted." |

`CheckSpec` and `StageSpec` carry `commit` and `hosts` with the same meaning.

**`commit` is a floor, not a pin.** Verbatim: "if subsequent commits have been made to the
desired state document the apply operation will use the most recent desired state document."

**Errors that mean something specific** on `apply` (`9.1.0.0` spec):

- `400 Vapi.Std.Errors.AlreadyInDesiredState` — already at that commit. Treat as success.
- `400 Vapi.Std.Errors.InvalidArgument` — invalid commit or host, host not in the cluster,
  **or "the cluster is not managed with a single software specification"** (the
  baseline-managed case, P2).
- `400 Vapi.Std.Errors.NotAllowedInCurrentState` — "If there is another operation in
  progress." vLCM serializes per cluster.
- `500 Vapi.Std.Errors.Error` — "unknown internal error **or if the EULA has not been
  accepted**." Frequently a missing `accept_eula`.

---

## Apply policy — and what 9.1 changed

`Esx.Settings.Clusters.Policies.Apply.ConfiguredPolicySpec`, the body of
`PUT /esx/settings/clusters/{cluster}/policies/apply`. All fields optional; omitted means
"configured value would be unset" — so read `/effective`.

| Field | Type | Effect (from the `9.1.0.0` spec) |
|---|---|---|
| `failure_action` | object | Action if entering maintenance mode fails on a host. |
| `pre_remediation_power_action` | enum | `POWER_OFF_VMS`, `SUSPEND_VMS`, `DO_NOT_CHANGE_VMS_POWER_STATE`, `SUSPEND_VMS_TO_MEMORY`. |
| `enable_quick_boot` | boolean | Quick Boot during remediation. |
| `disable_dpm` | boolean | Disable DPM on the cluster. |
| `disable_hac` | boolean | Disable HA Admission Control. |
| `evacuate_offline_vms` | boolean | Evacuate powered-off/suspended VMs when entering maintenance mode. |
| `enforce_hcl_validation` | boolean | Blocks remediation on HCL issues. **If missing/null, HCL issues will not prevent remediation.** *9.1: "will be deprecated in the future"; prefer `software_policy_spec.enforce_hcl_validation`.* |
| `parallel_remediation_action` | object | Parallel remediation of hosts in maintenance mode. If missing, "parallel remediation will not happen." *9.1: same forward deprecation notice.* |
| `enforce_quick_patch` | boolean | "Enforce quick patch on the cluster for images that support it." *9.1: same notice; see the coupling below.* |
| **`software_policy_spec`** | object | **New in 9.1** — `Esx.Settings.ClusterSoftwarePolicySpec`. |
| `config_manager_policy_spec` | object | Settings for the *configuration* apply API, not the software one. |

**`Esx.Settings.ClusterSoftwarePolicySpec` — added in vSphere API 9.1.0.0:**

| Field | Type | Effect |
|---|---|---|
| `enforce_hcl_validation` | boolean | Successor to the top-level field. Same default: "If missing or `null`, hardware compatibility issues will not prevent remediation." |
| `parallel_remediation_action` | object | `Esx.Settings.ClusterParallelRemediationAction`. Successor to the top-level field. |
| `live_patch_action` | object | `Esx.Settings.ClusterLivePatchAction`. **New capability in 9.1.** |
| `skip_reserved_vibs_caching` | boolean | Skips caching reserved VIBs on the host. The spec warns the extracted running image "will not be complete and that might lead to remediation failures. **NOTE: Use this option with caution.**" |

**`Esx.Settings.ClusterLivePatchAction` — required `live_patch_mode`**, enum verbatim:

- `DISABLE_LIVE_PATCH` — "Disable Live Patch."
- `AUTO_LIVE_PATCH` — "Perform Live Patch when possible. Use full maintenance mode for hosts
  that cannot perform Live Patch."
- `ENFORCE_LIVE_PATCH` — "Enforce Live Patch. Disallow remediation if there is a host that
  cannot perform Live Patch."

**The coupling with `enforce_quick_patch`, verbatim from the spec** — this is the trap:

> "This field should not be set together with `enforce_quick_patch`. When ... `livePatchMode`
> is set to `ENFORCE_LIVE_PATCH`, `enforce_quick_patch` will be set to `true` automatically.
> For other values, `enforce_quick_patch` will be set to `false`."

and from the other direction:

> "When this field [`enforce_quick_patch`] is set to `true`, ... `livePatchMode` will be set
> to `ENFORCE_LIVE_PATCH` automatically. When this field is set to `false`, ...
> `livePatchMode` will be set to `DISABLE_LIVE_PATCH` automatically."

So setting `enforce_quick_patch: false` **silently disables Live Patch entirely** — it does
not merely decline to enforce it. **Set one field or the other, never both.**

`ENFORCE_LIVE_PATCH` is a gate: a single host that cannot live-patch fails the whole
remediation. `AUTO_LIVE_PATCH` is the safe default shape — live-patch what can be, full
maintenance mode for the rest.

> **UNVERIFIED.** Which patches are live-patchable, and the full host preconditions, are not
> enumerated in anything retrieved. The 9.1 What's New says "Live Patching for ESX for
> TPM-enabled hosts covering up to 80% of patches" `[D9.1 §3.0]` — that is a marketing
> figure, not a per-patch rule. Do not promise a reboot-free remediation window; check
> `impact` on the compliance report and the `check` result first.

Defaults live at `/esx/settings/defaults/clusters/policies/apply`
(`Esx.Settings.Defaults.Clusters.Policies.Apply_get` / `_set` / `...Effective_get`) and, for
standalone hosts, `/esx/settings/defaults/hosts/policies/apply`
(`Esx.Settings.Defaults.Hosts.Policies.Apply_get` / `_set` / `...Effective_get`). All
**spec-confirmed (9.1)**.

---

## Worked example — set a base image on a cluster and remediate

Every field below is quoted from a `9.1.0.0` schema. Auth headers omitted — see
`vcf-foundation`. `$VC` is the vCenter FQDN, `$CL` a `ClusterComputeResource` id such as
`domain-c8`.

**0. Confirm the cluster is image-managed** (P2) and check ownership (P5).

```
GET https://$VC/api/esx/settings/clusters/$CL/enablement/software
→ {"enabled": true}
GET https://$VC/api/esx/settings/clusters/$CL/software/software-spec-metadata
```

**1. Confirm the depot has the base image you want.**

```
GET https://$VC/api/esx/settings/depot-content/base-images
```

Take a `version` string from the response — base-image versions are depot content and the
spec does not enumerate them. Do not invent one.

**2. Create a draft.** No body; returns the draft id as a bare JSON string.

```
POST https://$VC/api/esx/settings/clusters/$CL/software/drafts
→ 201 "draft-3"
```

`AlreadyExists` means you already have one: `GET .../software/drafts`, then reuse or
`DELETE .../software/drafts/{draft}`.

**3. Set the base image on the draft.**

```
PUT https://$VC/api/esx/settings/clusters/$CL/software/drafts/draft-3/software/base-image
Content-Type: application/json

{"version": "<version from step 1>"}
```

Optionally `PUT .../software/add-on` with `{"name": "...", "version": "..."}` and
`PATCH .../software/components` with `{"components_to_set": {"<component>": "<version>"}}`.

**4. Validate the draft against the depot.**

```
POST https://$VC/api/esx/settings/clusters/$CL/software/drafts/draft-3?action=validate&vmw-task=true
→ 202 "52a1b0c4-..."
GET  https://$VC/api/cis/tasks/52a1b0c4-...
```

**5. Commit.** The draft is consumed on success. Leave `orchestrator` unset.

```
POST https://$VC/api/esx/settings/clusters/$CL/software/drafts/draft-3?action=commit&vmw-task=true
Content-Type: application/json

{"message": "9.1 patch baseline"}
```

**6. Decide the remediation policy before you remediate** — 9.1-specific step.

```
GET https://$VC/api/esx/settings/clusters/$CL/policies/apply/effective
```

If you want Live Patch, set it through the new nested object and **do not** also set
`enforce_quick_patch`:

```
PUT https://$VC/api/esx/settings/clusters/$CL/policies/apply
Content-Type: application/json

{
  "pre_remediation_power_action": "DO_NOT_CHANGE_VMS_POWER_STATE",
  "evacuate_offline_vms": true,
  "software_policy_spec": {
    "enforce_hcl_validation": true,
    "live_patch_action": { "live_patch_mode": "AUTO_LIVE_PATCH" }
  }
}
```

`enforce_hcl_validation: true` is what makes step 7 an actual gate rather than a report.

**7. Hardware compatibility.**

```
POST https://$VC/api/esx/settings/clusters/$CL/software/reports/hardware-compatibility?action=check&vmw-task=true
GET  https://$VC/api/esx/settings/clusters/$CL/software/reports/hardware-compatibility
```

Stop on `INCOMPATIBLE` unless the customer has explicitly accepted it.

**8. Scan, then check.**

```
POST https://$VC/api/esx/settings/clusters/$CL/software?action=scan&vmw-task=true
GET  https://$VC/api/esx/settings/clusters/$CL/software/compliance
POST https://$VC/api/esx/settings/clusters/$CL/software?action=check&vmw-task=true
Content-Type: application/json

{}

GET  https://$VC/api/esx/settings/clusters/$CL/software/reports/last-check-result
```

`{}` checks all hosts at the latest commit. Scope with `{"hosts": ["host-42"]}` for a canary.
Read `impact` on the compliance response — `REBOOT_REQUIRED` here means Live Patch is not
going to save you on those hosts.

**9. Optional — stage payloads.** No reboot.

```
POST https://$VC/api/esx/settings/clusters/$CL/software?action=stage&vmw-task=true
Content-Type: application/json

{}
```

**10. Apply. This reboots hosts** unless Live Patch applies to every host in scope.

```
POST https://$VC/api/esx/settings/clusters/$CL/software?action=apply&vmw-task=true
Content-Type: application/json

{
  "accept_eula": true,
  "hosts": ["host-42"]
}
```

`accept_eula: true` avoids the documented "500 ... if the EULA has not been accepted".
`hosts` restricts to a canary — **omit it and every host in the cluster is remediated.**
Poll `GET /api/cis/tasks/{task}` to a terminal state, then:

```
GET https://$VC/api/esx/settings/clusters/$CL/software/reports/last-apply-result
GET https://$VC/api/esx/settings/clusters/$CL/software/compliance
```

Expect `status: "COMPLIANT"` for the remediated hosts, then repeat step 10 without `hosts`.

---

## Standalone hosts

Same API shape under `/esx/settings/hosts/{host}/...`. All **spec-confirmed (9.1)**:

- Enablement: `Esx.Settings.Hosts.Enablement.Software_get` / `_check$Task` / `_enable$Task`.
- Image read: `Esx.Settings.Hosts.Software_get`, `...Software.BaseImage_get`,
  `...Software.AddOn_get`, `...Software.Components_list`,
  `...Software.EffectiveComponents_list`, `...Software.Compliance_get`,
  `...Software.SoftwareSpecMetadata_get`, `...Software.Solutions_list`.
- Drafts: `Esx.Settings.Hosts.Software.Drafts_list` / `_create` / `_importSoftwareSpec` plus
  the per-element setters under `/software/drafts/{draft}/software/...`.
- Remediation: `Esx.Settings.Hosts.Software_scan$Task` / `_check$Task` / `_stage$Task` /
  `_apply$Task`, with `...Software.Reports.LastCheckResult_get`,
  `...Software.Reports.LastApplyResult_get`, `...Software.Reports.ApplyImpact_get`.
- Policy: `Esx.Settings.Hosts.Policies.Apply_get` / `_set` / `...Effective_get`.
- Installed software: `GET /esx/hosts/{host}/software/installed-components`
  (`Esx.Hosts.Software.InstalledComponents_list`), `GET /esx/software`
  (`Esx.Hosts.Software_get`).

**Limitation, 9.0-sourced** `[DVS §8, S15]`, not restated for 9.1: "you can't update the
firmware of the host" when managing a standalone host through the VCF API.

---

## Where VCF meets vLCM in 9.1

SDDC Manager, **spec-confirmed (9.1)** in `SPECSDDC9.1`:

| Method | Path | operationId | Note |
|---|---|---|---|
| GET | `/v1/clusters/{id}/image-compliance` | `getClusterImageCompliance` | also in 9.0 |
| POST | `/v1/domains/{domainId}/image-compliance/queries` | `queryDomainImageCompliance` | **new in 9.1** |
| GET | `/v1/domains/{domainId}/image-compliance/queries/{queryId}` | `getDomainImageComplianceQueryResponse` | **new in 9.1** |
| GET | `/v1/personalities` | `getPersonalities` | also in 9.0 |
| GET | `/v1/personalities/{personalityId}` | `getPersonality` | also in 9.0 |
| POST | `/v1/personalities` | `uploadPersonality` | also in 9.0 |
| PUT | `/v1/personalities/files` | `uploadPersonalityFiles` | also in 9.0 |
| DELETE | `/v1/personalities` | `deletePersonality` | also in 9.0 |
| POST | `/v1/vcenters/repository-images/queries` | `initiateRepositoryImagesQuery` | also in 9.0 |
| GET | `/v1/vcenters/repository-images/queries/{queryId}` | `getRepositoryImagesQueryResponse` | also in 9.0 |

"Personality" is SDDC Manager's term for a cluster image.

**Above SDDC Manager in 9.1**, fleet-level lifecycle is driven by **fleet lifecycle** and
**SDDC lifecycle** services with the **software depot** component supplying binaries — "VCF
Operations now uses the fleet lifecycle, SDDC lifecycle, and software depot components to
orchestrate lifecycle operations on both fleet and instance-level components" `[D9.1 §0.4]`.
VCF Operations "can manage ESX components and vSphere Lifecycle Manager images" `[DVS §8,
S24]`. Those surfaces (`fleet-lcm`, 51 operations; `sddc-lcm`, 26 operations) belong to
`vcf-lifecycle-upgrade`, not here.

> **UNVERIFIED.** See P5. No source consulted enumerates which vCenter objects VCF claims
> exclusive lifecycle ownership over, and no source describes how the VCF software depot
> relates to the vCenter vLCM depot (P1). Both are mechanisms without a documented policy.

---

## Baselines: the recorded conflict

Two Broadcom sources disagree. This file records both and resolves neither.

| Source | Statement |
|---|---|
| VCF 9.0 release notes, product support notes for vSphere `[DVS §5, S5]` | "**Removal of vSphere Lifecycle Manager baselines:** Managing clusters with vSphere Lifecycle Manager baselines and baseline groups (legacy vSphere Update Manager (VUM) workflows) is **no longer supported in vCenter 9.0**." Listed under *removals*. |
| vSphere 9.0 standalone doc set, "vLCM baselines and images" `[DVS §8, S14]` | "With vSphere 9.0, using baselines to upgrade the clusters and standalone hosts in your vCenter instances of version 9.0 and later is **deprecated**"; baselines remain to "Update and patch ESX hosts only of version 8.x" and "Update third-party software on ESX hosts". |

The dossier records this explicitly as a conflict `[DVS "Gaps and Ambiguities" §2]`.
**Neither statement was withdrawn. Do not pick one.**

The conflict is 9.0-era but it lands on 9.1 too, because 9.1 ships a doc topic named
"Transitioning from vSphere Lifecycle Manager Baselines to vSphere Lifecycle Manager Images"
`[DVS S25]` — whose existence implies baseline-managed clusters still reach 9.1 upgrades.
**That page's body was never fetched**; do not paraphrase a procedure from its title.

**What is not in conflict, and settles the automation question:**

- The string `baseline` matches **zero** operations in `SPEC9.1` and zero in `SPEC9.0`.
  There is no baseline REST API in either version.
- **Patch Manager APIs were removed in vCenter 9.0** `[DVS §5, S5]` and did not return.
- VCF convergence and workload-domain lifecycle require images, not baselines `[D9.0 §4.3]`.

So: build on images. The *support* position for patching 8.x hosts with baselines is a
Broadcom question against the customer's exact build.

---

## Task polling

Every `?vmw-task=true` operation returns HTTP **202** with the task identifier as a bare
JSON string.

| Method | Path | operationId |
|---|---|---|
| GET | `/api/cis/tasks/{task}` | `Cis.Tasks_get` |
| POST | `/api/cis/tasks?action=list` | `Cis.Tasks_list` |
| POST | `/api/cis/tasks/{task}?action=cancel` | `Cis.Tasks_cancel` |

All three **spec-confirmed (9.1)** and identical to 9.0. From the apply description: "The
result of this operation can be queried by calling the `cis/tasks/{task-id}` where the
task-id is the response of this operation."

Canceling an in-flight `apply` is exposed. Whether it is safe mid-remediation is
**UNVERIFIED** — no source describes the state a canceled remediation leaves a host in.
