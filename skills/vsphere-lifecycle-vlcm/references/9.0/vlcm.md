# VCF 9.0 — vSphere Lifecycle Manager (vLCM) Reference

**Scope:** vCenter / ESX 9.0.0.0 as shipped in VMware Cloud Foundation 9.0.x. Everything
here is `[9.0]` unless explicitly tagged otherwise.

**Sources.** `DVS` = `research/vsphere-vcenter-vsan.md`; `D9.0` = `research/vcf-core-9.0.md`;
`D9.1` = `research/vcf-core-9.1-and-deltas.md`.
`SPEC9.0` = `research/spec-inventory/9.0__vsphere-automation.ops.json` (1,275 operations,
spec version `9.0.0.0`, from git tag `9.0.0.0` of `github.com/vmware/vcf-api-specs`) and the
raw `specifications/vsphere/openapi/automation/vcenter.yaml` at the same tag.
`SPECSDDC9.0` = `research/spec-inventory/9.0__sddc-manager.ops.json` (375 operations).
Every endpoint below was matched in `SPEC9.0` (or `SPECSDDC9.0` where noted) by
`operationId` — each is marked **spec-confirmed (9.0)**. Schema field names and enum values
are quoted from `vcenter.yaml` at the `9.0.0.0` tag.

**Base path and separator.** `https://{host}/api` + `/esx/settings/...`. So the full URL is
`https://vcenter.example.com/api/esx/settings/clusters/{cluster}/software`. The hyphenated
form `/api/esx-settings/...` does **not** exist: zero operations in `SPEC9.0` contain the
string `esx-settings`. Earlier research left this unresolved because the rendered reference
pages would not load; the spec resolves it.

**Authentication is out of scope here.** vCenter session handling (`vmware-api-session-id`,
the `api_key_auth` scheme every operation below declares, and the 9.0 block on
non-federated username/password logins) belongs to `vcf-foundation`.

> **Documentation-derived, not live-validated** (captured 2026-07-31).
> **`POST .../software?action=apply` reboots hosts** and is production-affecting. Read the
> Prerequisites block and run `?action=check` before you run `?action=apply`.

---

## Contents

- [Prerequisites](#prerequisites)
  - P1 — An image depot is configured and synced
  - P2 — The cluster is image-managed, not baseline-managed
  - P3 — Hardware compatibility (HCL) data is present and the report is clean
  - P4 — The apply policy is what you think it is
  - P5 — The cluster's image may be owned by SDDC Manager, not by you
  - P6 — Privileges for image and remediation operations
  - P7 — Host eligibility for image management
  - P8 — Items the research could not verify
- [Depots](#depots)
- [Cluster image: read the current state](#cluster-image-read-the-current-state)
- [Cluster image: drafts](#cluster-image-drafts)
- [Hardware compatibility](#hardware-compatibility)
- [Remediation: scan, check, stage, apply](#remediation-scan-check-stage-apply)
- [Apply policy (remediation settings)](#apply-policy-remediation-settings)
- [Worked example — set a base image on a cluster and remediate](#worked-example--set-a-base-image-on-a-cluster-and-remediate)
- [Standalone hosts](#standalone-hosts)
- [Where VCF meets vLCM](#where-vcf-meets-vlcm)
- [Baselines: the recorded conflict](#baselines-the-recorded-conflict)
- [Task polling](#task-polling)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what
must hold, **how to verify it**, the version it applies to, and whether 9.1 differs.

### P1 — An image depot is configured and synced `[9.0]`

**Must be true:** at least one depot supplying base images, add-ons and components is
registered and its metadata has been synced. Without it, `depot-content` returns nothing to
select and a draft cannot be given a base image version.

**How to verify** (all **spec-confirmed (9.0)**):

| Purpose | Call | operationId |
|---|---|---|
| List online depots | `GET /api/esx/settings/depots/online` | `Esx.Settings.Depots.Online_list` |
| List offline (uploaded bundle) depots | `GET /api/esx/settings/depots/offline` | `Esx.Settings.Depots.Offline_list` |
| Read UMDS depot config | `GET /api/esx/settings/depots/umds` | `Esx.Settings.Depots.Umds_get` |
| Read sync schedule | `GET /api/esx/settings/depots/sync-schedule` | `Esx.Settings.Depots.SyncSchedule_get` |
| Confirm content is actually there | `GET /api/esx/settings/depot-content/base-images` | `Esx.Settings.DepotContent.BaseImages_list` |

Listing base images is the real test — a registered depot that has never synced lists no
content. Force a sync with `POST /api/esx/settings/depots?action=sync&vmw-task=true`
(`Esx.Settings.Depots_sync$Task`).

**9.1 difference:** none at the API level. All five paths, and `?action=sync`, are present
and non-deprecated in the 9.1 spec. What changes in 9.1 is *above* vCenter — VCF gains a
distinct **software depot** component in VCF Management Services. See `../deltas.md`.

### P2 — The cluster is image-managed, not baseline-managed `[9.0]`

**Must be true:** the cluster has vLCM image management enabled. Every `.../software`
operation in this file assumes a desired software document exists for the cluster; the
`apply` operation returns `Vapi.Std.Errors.InvalidArgument` when "the cluster is not managed
with a single software specification" (verbatim from the `9.0.0.0` spec).

**How to verify:** `GET /api/esx/settings/clusters/{cluster}/enablement/software`
(`Esx.Settings.Clusters.Enablement.Software_get`, **spec-confirmed (9.0)**). The response is
`Esx.Settings.Clusters.Enablement.Software.Info`, whose only required property is the
boolean **`enabled`** — "Status of the feature enablement True if feature is enabled, false
otherwise."

**How to transition a cluster that is not enabled:**
1. `POST /api/esx/settings/clusters/{cluster}/enablement/software?action=check&vmw-task=true`
   — `Esx.Settings.Clusters.Enablement.Software_check$Task`. Run this first.
2. `PUT /api/esx/settings/clusters/{cluster}/enablement/software?vmw-task=true` —
   `Esx.Settings.Clusters.Enablement.Software_enable$Task`. Body is
   `Esx.Settings.Clusters.Enablement.Software.EnableSpec`, whose single **required**
   property is `skip_software_check` (boolean) — "Skip ... SOFTWARE check during feature
   enablement." Both **spec-confirmed (9.0)**.

Both operations require `VcIntegrity.lifecycleSettings.Write`.

> **UNVERIFIED.** Whether enabling image management on a cluster is reversible is **not
> stated** in the spec text captured, and the research did not retrieve a doc page that says
> so. Do not tell a user it is one-way or that it is reversible — neither is sourced. The
> 9.1 doc set has a topic titled "Transitioning from vSphere Lifecycle Manager Baselines to
> vSphere Lifecycle Manager Images" `[DVS S25]`, but **its body was never fetched**.

**9.1 difference:** identical paths and schemas; both present in the 9.1 spec.

### P3 — Hardware compatibility (HCL) data is present and the report is clean `[9.0]`

**Must be true:** the vSphere HCL/BCG compatibility data has been downloaded, and the
cluster's hardware-compatibility report for the *target* image does not show
`INCOMPATIBLE`.

**How to verify** (all **spec-confirmed (9.0)**):
- `GET /api/esx/settings/clusters/{cluster}/software/reports/hardware-compatibility`
  (`Esx.Settings.Clusters.Software.Reports.HardwareCompatibility_get`) — the cached report.
- `GET /api/esx/hcl/compatibility-data/status` (`Esx.Hcl.CompatibilityData_get`) — returns
  `Esx.Hcl.CompatibilityData.Status` with required `updated_at` (date-time) and
  `notifications`. Stale or absent data is why a report comes back `UNAVAILABLE`.

The report's `status` (`Esx.Settings.Clusters.Software.Reports.HardwareCompatibility.CheckSummary.status`)
takes these values, verbatim from the spec:
`COMPATIBLE`, `INCOMPATIBLE`, `HCL_DATA_UNAVAILABLE`, `UNAVAILABLE`, `NO_FIRMWARE_PROVIDER`.
The spec notes `HCL_DATA_UNAVAILABLE` and `NO_FIRMWARE_PROVIDER` are "Never returned by the
HCL compliance APIs" — treat `UNAVAILABLE` as the real "could not determine" answer.

**Refreshing:** `POST /api/esx/hcl/compatibility-data?action=download&vmw-task=true`
(`Esx.Hcl.CompatibilityData_update$Task`), then
`POST /api/esx/settings/clusters/{cluster}/software/reports/hardware-compatibility?action=check&vmw-task=true`
(`Esx.Settings.Clusters.Software.Reports.HardwareCompatibility_check$Task` — **no request
body**, cluster is the only parameter).

**The critical interaction with P4:** an `INCOMPATIBLE` report does **not** block
remediation by itself. It blocks only if `enforce_hcl_validation` is set in the cluster's
apply policy. The spec is explicit: "If missing or `null`, hardware compatibility issues
will not prevent remediation."

**9.1 difference:** the six `/esx/hcl/*` operations and the whole
`.../reports/hardware-compatibility` family are present and unchanged in the 9.1 spec.
9.1 *adds a second place* to set `enforce_hcl_validation` — see P4 and `../deltas.md`.

### P4 — The apply policy is what you think it is `[9.0]`

**Must be true:** you know what remediation will do to running VMs before you start it.

**How to verify** (all **spec-confirmed (9.0)**):
- `GET /api/esx/settings/clusters/{cluster}/policies/apply` —
  `Esx.Settings.Clusters.Policies.Apply_get` — what is configured on this cluster.
- `GET /api/esx/settings/clusters/{cluster}/policies/apply/effective` —
  `Esx.Settings.Clusters.Policies.Apply.Effective_get` — what will actually be used after
  vCenter-level defaults are folded in. **Read the effective one.** A cluster with nothing
  configured still remediates according to the defaults at
  `GET /api/esx/settings/defaults/clusters/policies/apply`
  (`Esx.Settings.Defaults.Clusters.Policies.Apply_get`).

Set with `PUT /api/esx/settings/clusters/{cluster}/policies/apply`
(`Esx.Settings.Clusters.Policies.Apply_set`). Fields are listed in
[Apply policy](#apply-policy-remediation-settings) below.

**9.1 difference:** same paths. 9.1 adds a nested `software_policy_spec` object to the same
schema and begins steering callers away from three top-level fields. See `../deltas.md`.

### P5 — The cluster's image may be owned by SDDC Manager, not by you `[9.0]` `[VCF boundary]`

**Must be true:** in a VCF deployment, before you commit a new desired image to a cluster,
you have established whether that cluster's desired state is under SDDC Manager's control.

**Why this is real, with the evidence.** The commit body
(`Esx.Settings.Clusters.Software.Drafts.CommitSpec`) carries an optional `orchestrator`
object of type `Esx.Settings.OrchestratorSpec`, added in vSphere API 9.0.0.0. Verbatim from
the `9.0.0.0` spec:

> "It is used by vLCM orchestrators like SDDC Manager to manage the desired state. For a
> non-orchestrator user i.e. a VC user, it must be unset."
>
> "Setting it prevents other users from modifying the committed desired state."

and on `OrchestratorSpec.owner`:

> "Owner of the desired state. It can be the name of the owner as set by orchestrator. For
> example, for a software specification created by SDDC manager, it could be `"SDDC-M"`."

So: an SDDC-Manager-managed cluster can have a desired state committed with an owner, and
that lock is a documented mechanism, not a guess.

**How to verify:**
- From vCenter: `GET /api/esx/settings/clusters/{cluster}/software`
  (`Esx.Settings.Clusters.Software_get`) and
  `GET /api/esx/settings/clusters/{cluster}/software/software-spec-metadata`
  (`Esx.Settings.Clusters.Software.SoftwareSpecMetadata_get`), both **spec-confirmed (9.0)**.
  Inspect the response for orchestrator/owner information before committing.
- From SDDC Manager: `GET /v1/clusters/{id}/image-compliance`
  (operationId `getClusterImageCompliance`, tag `Clusters`, **spec-confirmed (9.0)** in
  `SPECSDDC9.0`) and the `Personalities` family — `GET /v1/personalities`
  (`getPersonalities`), `GET /v1/personalities/{personalityId}` (`getPersonality`),
  `POST /v1/personalities` (`uploadPersonality`), `PUT /v1/personalities/files`
  (`uploadPersonalityFiles`), `DELETE /v1/personalities` (`deletePersonality`). A cluster
  that appears in SDDC Manager's image-compliance view is being tracked by SDDC Manager.

**If it is SDDC-Manager-owned**, drive the change through `vcf-lifecycle-upgrade`, not
through the vCenter API. A direct vCenter commit either fails against the orchestrator lock
or creates drift that SDDC Manager will later report as non-compliance.

> **UNVERIFIED — and say so when it matters.** There is **no authoritative, enumerated
> statement in any source consulted** of which vCenter objects VCF claims exclusive
> lifecycle ownership over. The `OrchestratorSpec` text above is the strongest evidence
> available, and it describes a *mechanism* (an owner field that locks a committed desired
> state), not a *policy* (a list of what SDDC Manager owns). Do not present a boundary rule
> as documented. Present the check, and route the decision to the customer's VCF operating
> model.

**9.1 difference:** `OrchestratorSpec` and `CommitSpec` are byte-identical in the 9.1 spec.
SDDC Manager adds domain-scoped image compliance in 9.1 — see `../9.1/vlcm.md` P5.

### P6 — Privileges for image and remediation operations `[9.0]`

**Must be true:** the calling principal holds the right `VcIntegrity.*` privileges, both at
operation level and on the target `ClusterComputeResource`. These are quoted from the
operation descriptions in `vcenter.yaml` at the `9.0.0.0` tag:

| Operation | Privileges required |
|---|---|
| `Esx.Settings.Clusters.Software_apply$Task` | `VcIntegrity.lifecycleSoftwareRemediation.Write` **and** `VcIntegrity.lifecycleHealth.Read` |
| `Esx.Settings.Clusters.Software_check$Task` | `VcIntegrity.lifecycleSoftwareRemediation.Read` **and** `VcIntegrity.lifecycleHealth.Read` |
| `Esx.Settings.Clusters.Software.Drafts_create`, `..._set` writers | `VcIntegrity.lifecycleSoftwareSpecification.Write` |
| `Esx.Settings.Clusters.Software.Compliance_get`, draft readers | `VcIntegrity.lifecycleSoftwareSpecification.Read` |
| `Esx.Settings.Depots_sync$Task`, enablement enable/check | `VcIntegrity.lifecycleSettings.Write` |
| `Esx.Hcl.CompatibilityData_update$Task`, HCL report check | `VcIntegrity.HardwareCompatibility.Read` |

Each is required **both** for operation execution **and** on the `ClusterComputeResource`
referenced by the `cluster` parameter — the spec states both clauses separately. A role that
has the privilege globally but not on the target cluster still fails.

**How to verify:** resolve the caller's effective privileges through vCenter authorization
APIs — that surface belongs to `vcf-foundation` / `vsphere-inventory-vm-lifecycle`, not here.

**9.1 difference:** the same privilege strings appear on the same operations in the 9.1 spec.

### P7 — Host eligibility for image management `[9.0]`

**Must be true:** the hosts can be image-managed at all. From the VCF 9.0 programming guide
`[DVS §8, S15]`: managed hosts must be **vSphere 7.0 or later, stateful, identical hardware
from the same vendor, and running only integrated solutions** (vSAN, vSphere Supervisor,
NSX, vSphere HA). Since vSphere 8.0, standalone hosts are managed "using an image only
through the vSphere Lifecycle Manager automation API".

**How to verify:** the enablement check in P2 is the machine-readable form of this —
`Esx.Settings.Clusters.Enablement.Software_check$Task` exists precisely to report why a
cluster cannot be enabled. Run it rather than eyeballing the host list.

**Known limitation, verbatim** `[DVS §8, S15]`: "The only limitation for managing the life
cycle of a standalone host through the VMware Cloud Foundation API, is that you can't update
the firmware of the host."

**9.1 difference:** not restated in the 9.1 research. Treat the constraint list as
9.0-sourced; the *endpoints* are unchanged in 9.1.

### P8 — Items the research could not verify `[9.0]`

State these as unknown rather than filling them in:

1. **Reversibility of image enablement** — see P2. Not in the spec text; the 9.1 transition
   doc page body was never retrieved `[DVS S25]`.
2. **Which objects VCF exclusively owns** — see P5. No authoritative enumeration exists in
   any source consulted.
3. **The precise semantics of an `INCOMPATIBLE` HCL result for a *specific* device class**
   (PCI vs storage). The override endpoints exist and are listed below, but the research did
   not retrieve doc prose describing when an override is appropriate.
4. **The vLCM reference pages themselves.** `[DVS S37][S38]` records that
   `developer.broadcom.com/xapis/vsphere-automation-api/latest/esx/...` returned navigation
   only — "NONE VISIBLE" — on repeated fetches. Everything in this file therefore comes from
   the OpenAPI specification, not from the rendered reference. Where the spec is silent on
   *why* something behaves as it does, this file says so instead of narrating.

---

## Depots

All **spec-confirmed (9.0)**. Base path `https://{host}/api`.

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

**Depot content (what you can put in an image):**

| Method | Path | operationId |
|---|---|---|
| GET | `/esx/settings/depot-content/base-images` | `Esx.Settings.DepotContent.BaseImages_list` |
| GET | `/esx/settings/depot-content/base-images/versions/{version}` | `Esx.Settings.DepotContent.BaseImages.Versions_get` |
| GET | `/esx/settings/depot-content/add-ons` | `Esx.Settings.DepotContent.AddOns_list` |
| GET | `/esx/settings/depot-content/add-ons/{name}/versions/{version}` | `Esx.Settings.DepotContent.AddOns.Versions_get` |
| GET | `/esx/settings/depot-content/components` | `Esx.Settings.DepotContent.Components_list` |
| GET | `/esx/settings/depot-content/components/{name}/versions/{version}` | `Esx.Settings.DepotContent.Components.Versions_get` |

**Per-cluster and per-host depot overrides** (point one cluster at a different depot):
`GET|POST /esx/settings/clusters/{cluster}/depot-overrides[?action=add|remove]`
(`Esx.Settings.Clusters.DepotOverrides_get` / `_add` / `_remove`) and the matching
`/esx/settings/hosts/{host}/depot-overrides` trio
(`Esx.Settings.Hosts.DepotOverrides_get` / `_add` / `_remove`).

**Bodies you can rely on:**

`Esx.Settings.Depots.Online.CreateSpec` — **required: `location`**.

```json
{
  "location": "https://depot.example.com/vmw-depot/index.xml",
  "description": "corporate mirror",
  "enabled": true
}
```

`location` is documented as "the location to the index.xml for the depot" (format `uri`).
`enabled` defaults to enabled if omitted. `ownerdata` (added in vSphere API 7.0.3.0) is an
opaque string.

`Esx.Settings.Depots.SyncSpec` — sole property `cleanup` (boolean, added in vSphere API
9.0.0.0): "Whether to clean up all online depots before depot sync." The spec warns that
"Depot cleanup temporarily removes the online depot content which may be needed for image
operations" — do not sync with `cleanup: true` while an image operation is in flight.

**Hardware Support Managers (firmware):** `GET /esx/settings/hardware-support/managers`
(`Esx.Settings.HardwareSupport.Managers_list`),
`GET /esx/settings/hardware-support/managers/{manager}/packages`
(`Esx.Settings.HardwareSupport.Managers.Packages_list`),
`GET /esx/settings/hardware-support/managers/{manager}/packages/{pkg}/versions/{version}`
(`Esx.Settings.HardwareSupport.Managers.Packages.Versions_get`). All **spec-confirmed (9.0)**.

---

## Cluster image: read the current state

All **spec-confirmed (9.0)**, all under `/esx/settings/clusters/{cluster}/software`.

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
| The image actually installed on hosts | `GET /esx/settings/clusters/{cluster}/installed-images` | `Esx.Settings.Clusters.InstalledImages_get` |
| Extract installed image | `POST /esx/settings/clusters/{cluster}/installed-images?action=extract&vmw-task=true` | `Esx.Settings.Clusters.InstalledImages_extract$Task` |

**Reading compliance.** `GET .../software/compliance` returns
`Esx.Settings.ClusterCompliance`. Required properties include `status`, `impact`,
`scan_time`, `hosts`, `host_info`, `compliant_hosts`, `non_compliant_hosts`,
`incompatible_hosts`, `unavailable_hosts`, `notifications`. The enums, verbatim:

- `status`: `COMPLIANT` ("Target version is same as current version"), `NON_COMPLIANT`
  ("Target version is greater than current version"), `INCOMPATIBLE` ("Target state cannot
  be applied due to conflict or missing dependencies or the target state is lesser than the
  current version"), `UNAVAILABLE` ("Drift check failed due to unknown error or check hasn't
  happened yet and results are not available").
- `impact`: `NO_IMPACT`, `PARTIAL_MAINTENANCE_MODE_REQUIRED`, `MAINTENANCE_MODE_REQUIRED`,
  `REBOOT_REQUIRED`, `UNKNOWN`.
- `stage_status` (relevant only when `status` is `NON_COMPLIANT`): `STAGED`, `NOT_STAGED`.

`impact` is the field to quote when someone asks "will this reboot my hosts."

**Alternative images** (per-host-group variants within one cluster) live under
`/software/alternative-images/{image}/...` with `Esx.Settings.Clusters.Software.AlternativeImages.*`
operationIds — read-only on the committed image, editable on a draft.

---

## Cluster image: drafts

You cannot edit a committed image. You create a draft, edit it, and commit. All
**spec-confirmed (9.0)**.

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

**Two behaviours from the spec worth knowing before you write a loop:**

- `Drafts_create` takes **no request body** and returns **201** with a bare JSON string —
  "Identifier of the working copy of the document", resource type
  `com.vmware.esx.settings.draft`. It errors `Vapi.Std.Errors.AlreadyExists` "If there is
  already a draft created by this user" — **one draft per user per cluster.** Handle that
  409-shaped case by listing and reusing, not by retrying.
- The draft "will be deleted, when the draft is committed successfully. If a desired
  document is missing, then this operation will create an empty draft."

**Bodies:**

`Esx.Settings.BaseImageSpec` — **required: `version`**. `{"version": "9.0.0-<build>"}`.

`Esx.Settings.AddOnSpec` — **required: `name` and `version`**.
`{"name": "<OEM add-on name>", "version": "<version>"}`.

`Esx.Settings.Clusters.Software.Drafts.Software.Components.UpdateSpec`:

```json
{
  "components_to_set": { "<component-name>": "<version>" },
  "components_to_delete": [ "<component-name>" ]
}
```

The spec notes that a component supplied "without version" gets a version "chosen based on
constraints in the system".

`Esx.Settings.HardwareSupportSpec` — **required: `packages`**, a map keyed by Hardware
Support Manager name, each value an `Esx.Settings.HardwareSupportPackageSpec` with `pkg` and
`version` (the spec's own examples of a version string: `"20180128.1"` or `"v42"`).

`Esx.Settings.Clusters.Software.Drafts.CommitSpec`:

```json
{ "message": "Q3 patch baseline for cluster prod-01" }
```

`message` defaults to empty string. **Do not set `orchestrator`** — the spec states that for
"a non-orchestrator user i.e. a VC user, it must be unset." See P5.

---

## Hardware compatibility

| Purpose | Method + path | operationId |
|---|---|---|
| HCL data freshness | `GET /esx/hcl/compatibility-data/status` | `Esx.Hcl.CompatibilityData_get` |
| Download HCL data | `POST /esx/hcl/compatibility-data?action=download&vmw-task=true` | `Esx.Hcl.CompatibilityData_update$Task` |
| Per-host compatibility report | `GET /esx/hcl/hosts/{host}/compatibility-report` | `Esx.Hcl.Hosts.CompatibilityReport_get` |
| Generate per-host report | `POST /esx/hcl/hosts/{host}/compatibility-report?vmw-task=true` | `Esx.Hcl.Hosts.CompatibilityReport_create$Task` |
| Releases a host is compatible with | `GET /esx/hcl/hosts/{host}/compatibility-releases` | `Esx.Hcl.Hosts.CompatibilityReleases_list` |
| Fetch a generated report | `GET /esx/hcl/reports/{report}` | `Esx.Hcl.Reports_get` |
| Cluster report vs desired image | `GET .../software/reports/hardware-compatibility` | `Esx.Settings.Clusters.Software.Reports.HardwareCompatibility_get` |
| Cluster report detail | `GET .../software/reports/hardware-compatibility/details` | `...HardwareCompatibility.Details_get` |
| Re-run cluster check | `POST .../software/reports/hardware-compatibility?action=check&vmw-task=true` | `...HardwareCompatibility_check$Task` |
| Override a PCI device VCG entry | `PATCH .../hardware-compatibility/pci-device-overrides/vcg-entries?vmw-task=true` | `...PciDeviceOverrides.VcgEntries_update$Task` |
| Override a storage device VCG entry | `PATCH .../hardware-compatibility/storage-device-overrides/vcg-entries?vmw-task=true` | `...StorageDeviceOverrides.VcgEntries_update$Task` |
| Override storage compliance status | `PATCH .../hardware-compatibility/storage-device-overrides/compliance-status?vmw-task=true` | `...StorageDeviceOverrides.ComplianceStatus_update$Task` |

All **spec-confirmed (9.0)**. `Esx.Hcl.Hosts.CompatibilityReleases_list` is the endpoint to
reach for when the question is "which ESX version can this host actually take" — it answers
that directly instead of by trial remediation.

The three `PATCH` override operations exist and are spec-confirmed, but **when it is
appropriate to use them is UNVERIFIED** — no doc prose describing override policy was
retrieved. Treat an override as a support-visible decision, not a workaround to suggest.

---

## Remediation: scan, check, stage, apply

All **spec-confirmed (9.0)**, all on `/esx/settings/clusters/{cluster}/software`, all
asynchronous (`?vmw-task=true`, HTTP 202 with a bare task-id string).

| Step | Call | operationId | Body schema |
|---|---|---|---|
| Scan (refresh compliance) | `POST ?action=scan&vmw-task=true` | `Esx.Settings.Clusters.Software_scan$Task` | — |
| Check (readiness gate) | `POST ?action=check&vmw-task=true` | `Esx.Settings.Clusters.Software_check$Task` | `Esx.Settings.Clusters.Software.CheckSpec` |
| Stage (pre-download) | `POST ?action=stage&vmw-task=true` | `Esx.Settings.Clusters.Software_stage$Task` | `Esx.Settings.Clusters.Software.StageSpec` |
| **Apply (remediate)** | `POST ?action=apply&vmw-task=true` | `Esx.Settings.Clusters.Software_apply$Task` | `Esx.Settings.Clusters.Software.ApplySpec` |
| Last check result | `GET /reports/last-check-result` | `Esx.Settings.Clusters.Software.Reports.LastCheckResult_get` | — |
| Last apply result | `GET /reports/last-apply-result` | `Esx.Settings.Clusters.Software.Reports.LastApplyResult_get` | — |
| Predicted impact | `GET /reports/apply-impact` | `Esx.Settings.Clusters.Software.Reports.ApplyImpact_get` | — |

**`ApplySpec` — the whole schema, three optional properties:**

| Field | Type | Meaning (from the spec) |
|---|---|---|
| `commit` | string | "The minimum commit identifier of the desired software document to be used" — if omitted, apply uses the **latest** commit. |
| `hosts` | array of `HostSystem` ids, unique | "The specific hosts within the cluster to be considered" — if omitted, apply "will remediate **all** hosts within the cluster." |
| `accept_eula` | boolean | "Accept the VMware End User License Agreement (EULA) before starting the apply operation." If omitted, apply "could fail due to the EULA not being accepted." |

`CheckSpec` has `commit` and `hosts` with the same semantics; `StageSpec` (added in vSphere
API 8.0.0.1) likewise.

**The `commit` field is a floor, not a pin.** Verbatim: "if subsequent commits have been
made to the desired state document the apply operation will use the most recent desired
state document." If you need certainty about *which* image lands, quiesce commits — do not
assume `commit` freezes the target.

**Errors that mean something specific** on `apply` (from the `9.0.0.0` spec):

- `400 Vapi.Std.Errors.AlreadyInDesiredState` — the cluster is already at the specified
  commit. Not a failure; treat as success.
- `400 Vapi.Std.Errors.InvalidArgument` — invalid commit, invalid host, a host not in the
  cluster, **or "the cluster is not managed with a single software specification"** (that is
  the baseline-managed case from P2).
- `400 Vapi.Std.Errors.NotAllowedInCurrentState` — "If there is another operation in
  progress." vLCM serialises per cluster.
- `500 Vapi.Std.Errors.Error` — "if there is an unknown internal error **or if the EULA has
  not been accepted**." A 500 here is frequently the missing `accept_eula`.

---

## Apply policy (remediation settings)

`Esx.Settings.Clusters.Policies.Apply.ConfiguredPolicySpec` — the body of
`PUT /esx/settings/clusters/{cluster}/policies/apply`. All fields optional; omitted means
"configured value would be unset", so read `/effective` to see what will really happen.

| Field | Type | Effect (from the spec) |
|---|---|---|
| `failure_action` | object | "What action is to be taken if entering maintenance mode fails on a given host." |
| `pre_remediation_power_action` | enum | `POWER_OFF_VMS`, `SUSPEND_VMS`, `DO_NOT_CHANGE_VMS_POWER_STATE`, `SUSPEND_VMS_TO_MEMORY`. |
| `enable_quick_boot` | boolean | Quick Boot during remediation. |
| `disable_dpm` | boolean | Disable DPM on the cluster. |
| `disable_hac` | boolean | Disable HA Admission Control. |
| `evacuate_offline_vms` | boolean | "Evacuate powered off/suspended VMs when attempting maintenance mode." |
| `enforce_hcl_validation` | boolean | "Enforce Hcl validation, when applicable, to prevent remediation if hardware compatibility issues are found." **If missing or null, hardware compatibility issues will not prevent remediation.** |
| `parallel_remediation_action` | object | "Enable parallel remediation of hosts in maintenance mode. Set max hosts when applicable." If missing, "parallel remediation will not happen." |
| `enforce_quick_patch` | boolean | "Enforce quick patch on the cluster for images that support it." |
| `config_manager_policy_spec` | object | Settings for the *configuration* apply API, not the software one. |

Defaults live at `/esx/settings/defaults/clusters/policies/apply` (get/set/effective:
`Esx.Settings.Defaults.Clusters.Policies.Apply_get` / `_set` /
`Esx.Settings.Defaults.Clusters.Policies.Apply.Effective_get`) and, for standalone hosts,
`/esx/settings/defaults/hosts/policies/apply` (`Esx.Settings.Defaults.Hosts.Policies.Apply_get`
/ `_set` / `...Effective_get`). All **spec-confirmed (9.0)**.

**9.1 difference:** 9.1 adds `software_policy_spec` alongside these and marks
`enforce_hcl_validation`, `parallel_remediation_action` and `enforce_quick_patch` as fields
that "will be deprecated in the future". See `../deltas.md`.

---

## Worked example — set a base image on a cluster and remediate

The spec supports this end to end; every field below is quoted from a `9.0.0.0` schema. Auth
headers are omitted — see `vcf-foundation`. `$VC` is the vCenter FQDN, `$CL` a
`ClusterComputeResource` id such as `domain-c8`.

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

Take a `version` string from the response. Do not invent one — base-image versions are depot
content, and the spec does not enumerate them.

**2. Create a draft.** No body; returns the draft id as a bare JSON string.

```
POST https://$VC/api/esx/settings/clusters/$CL/software/drafts
→ 201 "draft-3"
```

If this returns `AlreadyExists`, you already have a draft: `GET .../software/drafts`, then
either reuse or `DELETE .../software/drafts/{draft}`.

**3. Set the base image on the draft.**

```
PUT https://$VC/api/esx/settings/clusters/$CL/software/drafts/draft-3/software/base-image
Content-Type: application/json

{"version": "<version from step 1>"}
```

Optionally also `PUT .../software/add-on` with `{"name": "...", "version": "..."}`, and
`PATCH .../software/components` with
`{"components_to_set": {"<component>": "<version>"}}`.

**4. Validate the draft against the depot.** Returns a task id.

```
POST https://$VC/api/esx/settings/clusters/$CL/software/drafts/draft-3?action=validate&vmw-task=true
→ 202 "52a1b0c4-..."
GET  https://$VC/api/cis/tasks/52a1b0c4-...
```

**5. Commit.** The draft is consumed on success.

```
POST https://$VC/api/esx/settings/clusters/$CL/software/drafts/draft-3?action=commit&vmw-task=true
Content-Type: application/json

{"message": "Q3 patch baseline"}
```

Poll the returned task. **Leave `orchestrator` unset** (P5).

**6. Hardware compatibility, before you remediate.**

```
POST https://$VC/api/esx/settings/clusters/$CL/software/reports/hardware-compatibility?action=check&vmw-task=true
GET  https://$VC/api/esx/settings/clusters/$CL/software/reports/hardware-compatibility
```

Stop on `INCOMPATIBLE` unless the customer has explicitly accepted it. Remember
`enforce_hcl_validation` decides whether vLCM stops for you — by default it does not.

**7. Scan, then check.** `check` is the readiness gate; read its result before applying.

```
POST https://$VC/api/esx/settings/clusters/$CL/software?action=scan&vmw-task=true
GET  https://$VC/api/esx/settings/clusters/$CL/software/compliance
POST https://$VC/api/esx/settings/clusters/$CL/software?action=check&vmw-task=true
Content-Type: application/json

{}

GET  https://$VC/api/esx/settings/clusters/$CL/software/reports/last-check-result
```

`{}` runs checks on all hosts at the latest commit. Scope it with
`{"hosts": ["host-42"]}` to check one host first.

**8. Optional — stage payloads.** No reboot, shortens the disruptive window.

```
POST https://$VC/api/esx/settings/clusters/$CL/software?action=stage&vmw-task=true
Content-Type: application/json

{}
```

**9. Apply. This reboots hosts.**

```
POST https://$VC/api/esx/settings/clusters/$CL/software?action=apply&vmw-task=true
Content-Type: application/json

{
  "accept_eula": true,
  "hosts": ["host-42"]
}
```

`accept_eula: true` is what avoids the documented "500 ... if the EULA has not been
accepted". `hosts` restricts remediation to a canary — **omit it and every host in the
cluster is remediated.** Poll `GET /api/cis/tasks/{task}` to a terminal state, then:

```
GET https://$VC/api/esx/settings/clusters/$CL/software/reports/last-apply-result
GET https://$VC/api/esx/settings/clusters/$CL/software/compliance
```

Expect `status: "COMPLIANT"` for the remediated hosts. Repeat step 9 without `hosts` once
the canary is good.

---

## Standalone hosts

Since vSphere 8.0 a standalone host is image-managed through the same API shape, under
`/esx/settings/hosts/{host}/...`. All **spec-confirmed (9.0)**:

- Enablement: `Esx.Settings.Hosts.Enablement.Software_get` / `_check$Task` / `_enable$Task`.
- Image read: `Esx.Settings.Hosts.Software_get`, `...Software.BaseImage_get`,
  `...Software.AddOn_get`, `...Software.Components_list`,
  `...Software.EffectiveComponents_list`, `...Software.Compliance_get`,
  `...Software.SoftwareSpecMetadata_get`, `...Software.Solutions_list`.
- Drafts: `Esx.Settings.Hosts.Software.Drafts_list` / `_create` / `_importSoftwareSpec` and
  the same per-element setters under `/software/drafts/{draft}/software/...`.
- Remediation: `Esx.Settings.Hosts.Software_scan$Task` / `_check$Task` / `_stage$Task` /
  `_apply$Task`, plus `...Software.Reports.LastCheckResult_get`,
  `...Software.Reports.LastApplyResult_get`, `...Software.Reports.ApplyImpact_get`.
- Policy: `Esx.Settings.Hosts.Policies.Apply_get` / `_set` / `...Effective_get`.
- Installed software on a host: `GET /esx/hosts/{host}/software/installed-components`
  (`Esx.Hosts.Software.InstalledComponents_list`) and `GET /esx/software`
  (`Esx.Hosts.Software_get`).

**Documented limitation** `[DVS §8, S15]`: "you can't update the firmware of the host" when
managing a standalone host's lifecycle through the VCF API.

---

## Where VCF meets vLCM

SDDC Manager, **spec-confirmed (9.0)** in `SPECSDDC9.0`:

| Method | Path | operationId | Tag |
|---|---|---|---|
| GET | `/v1/clusters/{id}/image-compliance` | `getClusterImageCompliance` | `Clusters` |
| GET | `/v1/personalities` | `getPersonalities` | `Personalities` |
| GET | `/v1/personalities/{personalityId}` | `getPersonality` | `Personalities` |
| POST | `/v1/personalities` | `uploadPersonality` | `Personalities` |
| PUT | `/v1/personalities/files` | `uploadPersonalityFiles` | `Personalities` |
| DELETE | `/v1/personalities` | `deletePersonality` | `Personalities` |
| POST | `/v1/vcenters/repository-images/queries` | `initiateRepositoryImagesQuery` | `RepositoryImages` |
| GET | `/v1/vcenters/repository-images/queries/{queryId}` | `getRepositoryImagesQueryResponse` | `RepositoryImages` |

"Personality" is SDDC Manager's term for a cluster image. Authentication to SDDC Manager
(`POST /v1/tokens`) and everything about bundles, depots and domain upgrades belongs to
`vcf-lifecycle-upgrade`.

Corroborating prose: VCF convergence prerequisites require "vSphere Lifecycle Manager images
(not baselines)" for the compute cluster `[D9.0 §4.3, S15]`.

> **UNVERIFIED.** See P5. No source consulted enumerates which vCenter objects VCF claims
> exclusive lifecycle ownership over. `OrchestratorSpec` is the mechanism; the policy is not
> documented in anything retrieved.

---

## Baselines: the recorded conflict

Two Broadcom sources, both 9.0-era, disagree. This file records both and resolves neither.

| Source | Statement |
|---|---|
| VCF 9.0 release notes, product support notes for vSphere `[DVS §5, S5]` | "**Removal of vSphere Lifecycle Manager baselines:** Managing clusters with vSphere Lifecycle Manager baselines and baseline groups (legacy vSphere Update Manager (VUM) workflows) is **no longer supported in vCenter 9.0**." Listed under *removals*. |
| vSphere 9.0 standalone doc set, "vLCM baselines and images" `[DVS §8, S14]` | "With vSphere 9.0, using baselines to upgrade the clusters and standalone hosts in your vCenter instances of version 9.0 and later is **deprecated**"; baselines remain to "Update and patch ESX hosts only of version 8.x" and "Update third-party software on ESX hosts". |

The dossier records this explicitly as a conflict `[DVS "Gaps and Ambiguities" §2]`:
removed-for-cluster-management versus deprecated-with-8.x-residual-use. Neither statement
was withdrawn or superseded by anything retrieved. **Do not pick one.**

**What is not in conflict, and settles the automation question:**

- The string `baseline` matches **zero** operations in `SPEC9.0` and zero in the 9.1
  equivalent. There is no baseline REST API to call in either version.
- **Patch Manager APIs were removed in vCenter 9.0** `[DVS §5, S5]`.
- VCF convergence explicitly requires images, not baselines `[D9.0 §4.3]`.

So: build on images. If a user needs the *support* position for patching 8.x hosts with
baselines, that is a Broadcom question against their exact build — the two doc statements
above are the whole of what this skill knows.

---

## Task polling

Every `?vmw-task=true` operation returns HTTP **202** with the task identifier as a bare
JSON string. Poll:

| Method | Path | operationId |
|---|---|---|
| GET | `/api/cis/tasks/{task}` | `Cis.Tasks_get` |
| POST | `/api/cis/tasks?action=list` | `Cis.Tasks_list` |
| POST | `/api/cis/tasks/{task}?action=cancel` | `Cis.Tasks_cancel` |

All three **spec-confirmed (9.0)** and identical in 9.1. The apply description states it
directly: "The result of this operation can be queried by calling the `cis/tasks/{task-id}`
where the task-id is the response of this operation."

Cancelling an in-flight `apply` is exposed by the API. Whether it is safe mid-remediation is
**UNVERIFIED** — no source consulted describes the state a cancelled remediation leaves a
host in. Do not recommend it casually.
