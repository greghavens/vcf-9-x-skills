# Runbook — VCF 9.0.x → 9.1 Upgrade

> ## ⚠ READ THIS FIRST — HIGH-IMPACT, VERIFY BEFORE EXECUTION
>
> This runbook upgrades an entire VMware Cloud Foundation instance. It takes vCenter, NSX, ESX
> hosts and the management appliances through service-affecting operations, permanently changes
> the management architecture (VCF Management Services is **mandatory and not reversible by
> simply skipping it**), moves licence storage into a new required License server, and **breaks
> every existing OAuth client** on the vIDM → identity broker migration.
>
> **Nothing here may be executed on the strength of this document alone.** Every step must be
> verified against Broadcom's own 9.1 documentation and the VMware Interoperability Matrix
> (`https://interopmatrix.broadcom.com/Upgrade?productId=851`) before it is run, and the whole
> sequence must be rehearsed in a non-production environment first. Broadcom states the upgrade
> "requires a **strict** component upgrade sequence" — deviating from it produces documented
> failures (see step 0.9).
>
> This runbook is assembled **strictly from the research dossiers**. Where the research could not
> establish something, the step says **`UNVERIFIED`** rather than guessing. Treat every
> `UNVERIFIED` marker as a mandatory stop-and-check against Broadcom docs.

**Source keys.** `D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DOPS` = `research/vcf-operations.md`; `DVS` = `research/vsphere-vcenter-vsan.md`;
`DAUTH` = `research/foundation-auth-identity.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md`;
`SPEC9.0` / `SPEC9.1` / `SPECFLT` / `SPECSDDCLCM` = the `.ops.json` inventories.
Every endpoint cited is marked **spec-confirmed** against the version's inventory.

**Scope.** VCF **9.0.x → 9.1**, management domain. Other supported 9.1 paths — VCF 5.2.x → 9.1,
vSphere Foundation → 9.1, and vSphere 8 + Aria Ops 8 → 9.1 — are **out of scope here** and their
sequences were **not retrieved** in research [D9.1 §5.1, §8.7]. Do not adapt this runbook to them.

---

## Contents

- [Phase 0 — Readiness gates](#phase-0--readiness-gates-all-must-pass-before-any-change) (0.1 source version · 0.2 depot and binaries · 0.3 prechecks · 0.4 credentials · 0.5 ports and certificates · 0.6 OAuth client breakage · 0.7 licensing · 0.8 backups · 0.9 failure modes · 0.10 the three orderings · **0.11 authentication to each surface**)
- [Phase 1 — SDDC Manager drives (orders 0 → 6)](#phase-1--sddc-manager-drives-upgrade-orders-0--6)
- [Phase 2 — the pivot, VCF Operations takes over (order 6 → 8)](#phase-2--the-pivot-and-vcf-operations-takes-over-order-6-continued--8)
- [Phase 3 — Management-domain components (orders 9 → 23)](#phase-3--management-domain-components-orders-9--23)
- [Phase 4 — Post-upgrade](#phase-4--post-upgrade)
- [Summary of steps this runbook could NOT fully verify](#summary-of-steps-this-runbook-could-not-fully-verify)

---

## Phase 0 — Readiness gates (all must pass before any change)

### 0.1 Confirm the source version and the workload-domain floor `[GATE]`

- The instance must be at **9.0.x** [D9.1 §5.2].
- **"All workload domains must be at VMware Cloud Foundation 5.2 or later. If any workload domain
  is at a version lower than 5.2, you must upgrade it to 5.2 and then upgrade to 9.1."**
  [DVS, sourced to the 9.1 Lifecycle Management guide] — this is a hard gate and it is easy to
  miss on a fleet that has an old, quiet workload domain in it.

**Verify:** `GET /v1/domains`, then per domain `GET /v1/releases/domains/{domainId}`
(**spec-confirmed 9.0 and 9.1**). Cross-check with `GET /v1/version-drift` once on 9.1
(**9.1-only**). Also check the Interoperability Matrix.

### 0.2 Confirm depot configuration and stage every required binary `[GATE]`

Before deploying VCF Management Services you must have downloaded install binaries for:
**VCF services runtime, fleet lifecycle, SDDC lifecycle, software depot, identity broker,
Salt RaaS, Salt master, license server, telemetry** [D9.1 §5.2].

**Verify (all spec-confirmed 9.0 and 9.1):** `GET /v1/system/settings/depot`,
`GET /v1/system/settings/depot/depot-sync-info`, `GET /v1/bundles`,
`GET /v1/bundles/download-status`, `GET /v1/bundles/domains/{id}`.
Trigger a download with `PATCH /v1/bundles/{id}`.

Air-gapped sites stage binaries with the **VCF Download Tool** (the deprecated standalone UMDS is
folded into it) [D9.0 §6.2, §9.1].

> **`UNVERIFIED`** — the bundle-type taxonomy and the online/offline depot configuration payload
> are **not documented on any page fetched in research** [D9.0 §11 item 6]. Confirm the depot mode
> and bundle set against Broadcom docs; do not construct a depot payload from this runbook.

### 0.3 Run prechecks and clear every finding `[GATE]`

On 9.0, use (**spec-confirmed 9.0**):
```
POST /v1/system/check-sets            then poll GET /v1/system/check-sets/{runId}
POST /v1/upgrades/{upgradeId}/prechecks   then GET /v1/upgrades/{upgradeId}/prechecks/{precheckId}
POST /v1/hosts/prechecks              then GET /v1/hosts/prechecks/{id}
POST /v1/domains/{domainId}/isolation-prechecks   then GET .../{precheckId}
```
Note `/v1/system/precheck` **does not exist** — it was removed in 9.0 with the note that its
functionality "moved to VCF Operations" [D9.0 §9.2]; the path is absent from both `SPEC9.0` and
`SPEC9.1`.

After the pivot to 9.1, the equivalents are `POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck`
(**spec-confirmed 9.1**) and `check-sets` with CSV export
(`POST|GET /v1/system/check-sets/{runId}/exports`, **9.1-only**). The SDDC Manager upgrade-precheck
pair becomes **deprecated** in 9.1.

> **`UNVERIFIED`** — the individual prechecks are **not enumerated anywhere in the research**
> [D9.0 §11 item 7]. Read whatever the precheck run actually returns; do not work to an assumed
> checklist.

### 0.4 Verify credential and password state `[GATE]`

No expired credentials; no rotation task in flight. **Verify (spec-confirmed both versions):**
`GET /v1/credentials`; `POST /v1/credentials/expirations` → `GET /v1/credentials/expirations/{id}`;
`GET /v1/credentials/tasks` and `GET /v1/credentials/tasks/{id}`.

### 0.5 Verify ports and certificates `[GATE]` — partly UNVERIFIED

Broadcom's prerequisites say, verbatim: "Verify that all required ports are open. See VMware Ports
and Protocols" and "Verify that your certificates are configured and use the proper Fully
Qualified Domain Name (FQDN)" [D9.1 §5.2].

**Verify certificates:** `GET /v1/sddc-manager/trusted-certificates` (**spec-confirmed both**),
plus the VCF Operations certificate-management views.

> **`UNVERIFIED`** — **the ports and protocols matrix was never retrieved in any part of this
> research.** No port list appears in this runbook because none can be sourced. Obtain the matrix
> from Broadcom directly. This is a real gate, not a formality.

### 0.6 Inventory and plan for OAuth client breakage `[GATE — most-missed step]`

The vIDM → VCF Identity Broker migration is a 9.1 workflow, and, verbatim:

> **"OAuth clients are not migrated automatically. You must manually regenerate the client and
> secret using identity broker and configure accordingly."** [DAUTH]

Also not carried over: local accounts, local accounts with MFA, and MFA with Active Directory are
**not supported**; sync settings are compared but not migrated and must be adjusted manually
[DAUTH].

**Do now, before the window:** enumerate every OAuth client in vIDM and every script, pipeline,
CMDB entry and integration holding one of those client secrets. Schedule regeneration and
re-configuration **inside** the change window — every one of them stops working across this
migration.

**Note the 9.0/9.1 asymmetry:** the 9.0 SSO tree has **no API-client or API-token pages at all**;
SSO-issued, role-scoped API tokens are a **9.1-only** capability [DAUTH]. In 9.0 you use
per-product credentials.

**Constant across both:** **SDDC Manager and ESX are excluded from VCF SSO** [DAUTH]. SDDC
Manager keeps its own `POST /v1/tokens` flow (**spec-confirmed 9.0 and 9.1**) — you will need it
throughout Phase 1.

### 0.7 Confirm licensing readiness `[GATE]`

A centralised **VCF License Server is a required component** in 9.1 [D9.1 §5.2] and licences move
out of VCF Operations into it [D9.1 §3.5]. Plan for the licence-transfer step (2.3).
**Verify:** `POST /v1/resources/license-checks` → `GET /v1/resources/license-checks/{id}`
(**spec-confirmed both versions**).

### 0.8 Back up, and know what you cannot do mid-upgrade

Take backups of SDDC Manager, vCenter, NSX Manager and the VCF Operations appliances per Broadcom
guidance. SDDC Manager exposes `POST /v1/backups/tasks`, `POST /v1/restores/tasks` and
`GET /v1/restores/tasks/{id}` (**spec-confirmed both versions**).

> **`UNVERIFIED` — and operationally important.** A Broadcom page titled *"SDDC Manager
> Functionality During an Upgrade to VMware Cloud Foundation 9.0"* was located by search but
> **never fetched** [D9.0 §11 item 13]. **What SDDC Manager cannot do while an upgrade is in
> flight is therefore unknown to this runbook.** Retrieve the 9.1 equivalent before starting.

> **`UNVERIFIED`** — the fate of the 9.0 fleet management, collector and for-logs appliances after
> the upgrade is unknown. The Deploy VCF Management Services page "contains no information about
> decommissioning, replacing, or migrating existing 9.0 VCF Operations fleet management
> appliances" [D9.1 §8.8]. **Do not power any of them off on the assumption they are obsolete
> until Broadcom docs say so.**

### 0.9 Know the documented failure modes before you start

Four problems are documented when incorrect upgrade paths are followed [D9.1 §5.5]:
1. upgrade binaries not appearing in VCF Operations 9.0;
2. vCenter licensing failures post-upgrade;
3. licence assignment failures;
4. ESXi host upgrade sync errors during the VCF Operations upgrade.

Every one of these is a symptom of sequence deviation. That is why the ordering below is not
negotiable.

### 0.10 Do not confuse this with the other two orderings `[GATE — named failure mode]`

Three distinct orderings exist. Using the wrong one is a known failure mode.

| | When it applies | Order |
|---|---|---|
| **A — major, 5.x → 9.0** | source is VCF 5.0+ | core via SDDC Manager: SDDC Manager → NSX Manager → vCenter → ESX. Management components manual or pre-deployed. **No explicit vSAN step.** [D9.0 §4.4] |
| **B — maintenance within 9.0.x** | 9.0.0.0 → 9.0.1.0 → 9.0.2.0 | management **first** (fleet management appliance → VCF Operations instance → remaining), **then** core: SDDC Manager → NSX → vCenter → ESX hosts → **vSAN**. [D9.0 §6.3] |
| **C — major, 9.0.x → 9.1** | **this runbook** | the order-0-to-23 sequence below, pivoting from SDDC Manager to VCF Operations at order 6. [D9.1 §5.3] |

All three start core work with SDDC Manager. That is the only thing they share.

### 0.11 Hold a working credential for **each** of the three API surfaces `[GATE]` — partly UNVERIFIED

This runbook issues authenticated calls against three surfaces that **do not share tokens**. Prove
each one works *before* the change window, not at the step that needs it.

| Surface | Scheme | How you obtain it | Where this runbook uses it |
|---|---|---|---|
| **SDDC Manager** `/v1` | `Authorization: Bearer <accessToken>` | `POST /v1/tokens` → `{"accessToken","refreshToken":{"id"}}`; refresh via `PATCH /v1/tokens/access-token/refresh`; access **1 h** / refresh **24 h** (**spec-confirmed 9.0 and 9.1**). SDDC Manager is **excluded from VCF SSO** [DAUTH] — a VIDB token will not work here. | every gate in Phase 0, all of Phase 1, and the SDDC Manager calls in Phases 2–4 |
| **VCF Operations** `/suite-api` | `Authorization: OpsToken <token>` (legacy `vRealizeOpsToken` still accepted) | `POST /suite-api/api/auth/token/acquire` → `token` (`<uuid>::<uuid>`) with `expiresAt`/`validity`; release with `POST /suite-api/api/auth/token/release` (**spec-confirmed 9.0 and 9.1**). 9.1 also accepts an identity-broker **Bearer** token and adds `POST /suite-api/api/auth/token/exchange` (**9.1-only**) [DAUTH; DOPS]. | Phase 2 onward, where VCF Operations drives; the licensing and Fleet Management views; VCF Operations task polling |
| **fleet lifecycle** `/fleet-lcm` and **SDDC lifecycle** `/sddc-lcm` | `SPECFLT` declares **`basicAuth`** and **`bearerToken`** (JWT); `SPECSDDCLCM` declares **`bearerToken` only — no basic auth** | **UNVERIFIED — see below** | 2.1 health/components/sizing checks; **all of 3.1**, including `?action=precheck` and `?action=apply`; 4.1 component status |

> **`UNVERIFIED` — and it sits directly on the critical path.** The fleet-lcm and sddc-lcm specs
> declare *which* schemes are accepted but **contain no token-issuing operation at all**: there is
> no `/fleet-lcm/v1/tokens`, no `/sddc-lcm/v1/tokens`, and **zero operations whose path contains
> `token`, `auth` or `login`** in either inventory (spec-confirmed absence). **No source in this
> research establishes who issues that JWT** — identity broker, VCF Operations, or a local
> appliance account. The 9.0 fleet-management Basic-auth pattern
> (`echo -n 'admin@local:<password>' | base64`, Broadcom KB 409715 [DAUTH]) authenticated an
> appliance that **does not exist in 9.1** and cannot be assumed to carry forward.
>
> **Do this before the window:** obtain and exercise a working fleet-lcm credential against
> `GET /fleet-lcm/v1/health` and a sddc-lcm credential against `GET /sddc-lcm/v1/health`, on a
> non-production 9.1 instance. If you cannot, **you cannot execute step 3.1**, because
> `?action=apply` is on the far side of it. Discovering this at the apply step, mid-upgrade, with
> the management domain half-migrated, is the specific failure this gate exists to prevent.
> See `9.1/lifecycle.md` P0.

Also note **role/privilege is a separate, unclosed question**: the role required to *submit*
`POST /v1/upgrades` or `POST /fleet-lcm/v1/upgrade-plans/{planId}?action=apply` **is not
documented in any source consulted** — verify before delegating credentials, and do not assume a
read-capable token is write-capable. See `9.1/lifecycle.md` P8 and `9.0/lifecycle.md` P8.

---

## Phase 1 — SDDC Manager drives (upgrade orders 0 → 6)

Source for the whole phase: [D9.1 §5.3]. The performing UI for every step in this phase is
**SDDC Manager** — which is precisely why "SDDC Manager is gone in 9.1" is wrong.

### 1.1 (order 0) Transition VCF Identity Broker 9.0.x to the VCF Management Network
Applies **if** the identity broker currently sits on an NSX overlay. Performed from SDDC Manager.
Pair this with the OAuth-client inventory from 0.6.

### 1.2 (order 1) Upgrade VCF Operations and the cloud proxy
Performed from SDDC Manager. Note the 9.0 *collector* becomes the 9.1 **cloud proxy** [D9.1 §2];
a cloud proxy must exist before VCF Management Services can be deployed [D9.1 §5.2].

### 1.3 (orders 2–5) Remaining pre-pivot components — `UNVERIFIED`

> **`UNVERIFIED`** — the retrieved Broadcom page **collapsed orders 2 through 5 into a range** and
> did not enumerate them [D9.1 §5.3, §8.7]. **This runbook cannot tell you what orders 2–5 are.**
> Retrieve `.../9-1/deployment/upgrading-cloud-foundation.html` and
> `.../release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/upgrade-sequence-to-91.html`
> and fill these in before executing. Do not skip from order 1 to order 6.

### 1.4 (order 6) Upgrade SDDC Manager itself to 9.1
Performed from SDDC Manager. This is its **self-upgrade** and the last step it drives.

**Verify readiness:** `GET /v1/sddc-manager/upgradables` and `GET /v1/system/upgradables`
(**spec-confirmed 9.0**). **Poll:** `GET /v1/tasks/{id}` (**spec-confirmed 9.0**).

**Post-condition — this is the gate for Phase 2:** Broadcom's stated prerequisite for deploying
VCF Management Services is, verbatim, **"Verify that VCF Operations and SDDC Manager are at
version 9.1."** [D9.1 §5.2] Confirm with `GET /v1/sddc-managers/{id}` (**spec-confirmed 9.1**)
before proceeding.

---

## Phase 2 — the pivot, and VCF Operations takes over (order 6 continued → 8)

> **The pivot point is order 6.** SDDC Manager drives the upgrade up to and including its own
> upgrade; **VCF Operations drives everything after** [D9.1 §5.3].

### 2.1 (order 6) Deploy VCF Management Services and the License Server
Performed from **VCF Operations**. VCF Management Services is "a mandatory, required part of the
deployment" [D9.1 §0.4] and the License Server is "a required component" [D9.1 §5.2].

**UI path** [D9.1 §5.4]: VCF Operations → **Build > Lifecycle > VCF Instances** →
**SDDC Manager Updates** tab → **Available Upgrades** → **Install Components**.

**Prerequisites re-check before clicking:** ports open; certificates on correct FQDNs; VCF
Operations and SDDC Manager both at 9.1; the nine install binaries staged; VCF Operations admin
credentials in hand; a cloud proxy deployed [D9.1 §5.2] — i.e. gates 0.2, 0.5, 1.4.

**What gets stood up:** fleet lifecycle, SDDC lifecycle, software depot, identity broker,
log management, real-time metrics (+ store), Salt master, Salt RaaS, telemetry, VCF services
runtime — all on the common VCF Management Services runtime [D9.1 §0.4].

**Verify after** — these are the **first** `/fleet-lcm` and `/sddc-lcm` calls in the runbook, so
they are also the first test of the credential whose issuer is `UNVERIFIED` (gate 0.11); a 401
here means the auth gap, not a failed deployment: `GET /fleet-lcm/v1/health` and
`GET /sddc-lcm/v1/health` (**spec-confirmed 9.1**); `GET /fleet-lcm/v1/components` and
`POST /fleet-lcm/v1/components/status` (**spec-confirmed 9.1**);
`GET /fleet-lcm/v1/sddc-lcms` to confirm the instance-level SDDC LCM registered
(**spec-confirmed 9.1**). Sizing can be pre-checked with
`POST /fleet-lcm/v1/components/resource-requirements` and
`GET /fleet-lcm/v1/components/resource-sizes` (**spec-confirmed 9.1**), or from SDDC Manager with
`POST /v1/vcf-management-components/resources-calculation` (**spec-confirmed 9.1**, new).

### 2.2 (order 6) Transfer licences
Performed from **VCF Operations**. Licences move out of VCF Operations into the License server
[D9.1 §3.5, §6]. Doing this out of order is implicated in two of the four documented failure modes
(vCenter licensing failures, licence assignment failures) [D9.1 §5.5].
**Verify:** `POST /v1/resources/license-checks` → `GET /v1/resources/license-checks/{id}`
(**spec-confirmed 9.1**).

### 2.3 (order 7) Upgrade VCF Identity Broker to 9.1 — **OAuth clients break here**
Performed from **VCF Operations**.

**Immediately after this step, execute the regeneration plan from gate 0.6.** Verbatim: "OAuth
clients are not migrated automatically. You must manually regenerate the client and secret using
identity broker and configure accordingly." [DAUTH] Users and groups **do** migrate; OAuth clients
do not. Local accounts, local-account MFA and AD MFA are not supported. Sync settings must be
re-applied manually. If VCF Operations, VCF Automation or NSX use the legacy system, the migration
script repoints them [DAUTH].

**Verify:** exercise the 9.1 token exchange end to end [D9.1 §0.5] — create the API client in
VIDB, request a long-lived API refresh token from the VCF Operations UI, exchange it at VIDB for a
bearer access token, and call a federated component with it. Confirm every regenerated client
works before moving on.

> Reminder: **SDDC Manager and ESX are not SSO-federated** in either version [DAUTH]. Keep using
> `POST /v1/tokens` for SDDC Manager.

### 2.4 (order 8) Upgrade VCF Automation to 9.1
Performed from **VCF Operations**.

---

## Phase 3 — Management-domain components (orders 9 → 23)

Performed from **VCF Operations**, which now orchestrates through fleet lifecycle, SDDC lifecycle
and software depot [D9.1 §0.4]. The components in this range are **NSX, vCenter, ESX, vSAN and
VMware Tools** [D9.1 §5.3].

> **`UNVERIFIED`** — orders 9 through 23 were **collapsed into a single range** on the retrieved
> page; their individual ordering is **not verified** [D9.1 §5.3, §8.7]. The *membership* of the
> range is sourced; the *sequence within it* is not. Retrieve the full sequence from Broadcom
> before executing. Do **not** assume it matches the 9.0 orderings — the 9.0 maintenance ordering
> (SDDC Manager → NSX → vCenter → ESX → vSAN) is a **different** sequence for a **different**
> upgrade, and substituting it here is exactly the conflation this document is meant to prevent.

### 3.1 Build and run an upgrade plan (fleet lifecycle)

> **Authentication for every call in this step — `UNVERIFIED` issuer, see gate 0.11.** These are
> `/fleet-lcm` and `/sddc-lcm` calls, **not** SDDC Manager calls: your `POST /v1/tokens` bearer
> token is not accepted here. `SPECFLT` declares `basicAuth` and `bearerToken`; `SPECSDDCLCM`
> declares `bearerToken` only. **Neither spec contains a token-issuing operation, and no source in
> this research says who issues the JWT.** Do not enter this step without a credential you have
> already exercised against `GET /fleet-lcm/v1/health` — `?action=apply` below is the point of no
> easy return.

The 9.1 native workflow, all **spec-confirmed (9.1)** against `SPECFLT`:
```
POST /fleet-lcm/v1/depot-metadata?action=sync          sync depot metadata
GET  /fleet-lcm/v1/release-versions/target-versions    what can we move to
POST /fleet-lcm/v1/upgrade-plans/validations           validate the plan spec
POST /fleet-lcm/v1/upgrade-plans                       create the plan
GET  /fleet-lcm/v1/upgrade-plans/{planId}/bundles      confirm required bundles are present
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=configure
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck     <- do not skip
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=apply
GET  /fleet-lcm/v1/tasks/{taskId}                      poll to terminal state
POST /fleet-lcm/v1/tasks/{taskId}?action=retry         on recoverable failure
POST /fleet-lcm/v1/tasks/{taskId}?action=cancel
```
Canonical order: **validate → create → configure → precheck → apply → poll.**

Instance-level component work runs through SDDC lifecycle (**spec-confirmed 9.1**):
`POST /sddc-lcm/v1/depot`, `POST /sddc-lcm/v1/depot/components`, `GET /sddc-lcm/v1/components`,
`POST /sddc-lcm/v1/components/{componentId}` (perform action),
`GET /sddc-lcm/v1/tasks/{taskId}`.

Task IDs are **not** interchangeable between SDDC Manager, fleet lifecycle and SDDC lifecycle.
Poll the service that started the work.

### 3.2 NSX Edge clusters are upgraded at the END of the domain upgrade `[9.1 CHANGE]`

Two independent 9.1 sources:
- "NSX Edge clusters are now upgraded at the end of the domain upgrade process" [D9.1 §3.5]
- "Move NSX Edge/SVM Upgrades to the End of Upgrade Sequence" [D9.1 §3.3]

If you are carrying a 9.0-era plan in which Edge clusters go earlier in the domain upgrade,
**re-sequence it**. This is a within-domain ordering change and it is separate from the
cross-component order table above.

Note also that the entire SDDC Manager `/v1/edge-clusters` API family is **deprecated in 9.1**
(spec-confirmed, part of the 21) — do not build new Edge automation on it.

### 3.3 Cluster and host upgrade behaviour available in 9.1

New capabilities you can use during this phase [D9.1 §3.5]: select **specific hosts** during
cluster upgrades (skip problematic hosts); imported standalone hosts and single-host clusters are
supported; optimised NSX Manager and vCenter maintenance windows; reduced-downtime update
preparation; **256 simultaneous cluster upgrades** at up to **5000 hosts per VCF Instance**;
a Component Versions tab showing current and target versions for all supported components.

Planning helpers new in 9.1 on SDDC Manager (**spec-confirmed 9.1**):
```
GET /v1/upgradables/domains/{domainId}/upgrade-sequences
GET /v1/upgradables/domains/{domainId}/vcenter-sizing-infos
GET /v1/upgradables/domains/{domainId}/vcenter-upgrade-mechanisms
GET /v1/version-drift
```

ESX images continue to be applied by **vLCM images** (baselines are not supported for cluster
management from vCenter 9.0 onward) [D9.0 §9.2; DVS].

---

## Phase 4 — Post-upgrade

### 4.1 Verify component versions and drift
`GET /v1/version-drift` (**spec-confirmed 9.1**, new in 9.1); the Component Versions tab in VCF
Operations [D9.1 §3.5]; `GET /fleet-lcm/v1/components` and `POST /fleet-lcm/v1/components/status`
(**spec-confirmed 9.1**).

### 4.2 Re-run check-sets and export the evidence
`POST /v1/system/check-sets` → `GET /v1/system/check-sets/{runId}`, then
`POST /v1/system/check-sets/{runId}/exports` → `GET /v1/system/check-sets/{runId}/exports[/data]`
(the three export operations are **9.1-only, spec-confirmed**). Useful as change-control evidence.

### 4.3 Confirm every regenerated OAuth client works
See 2.3. Do not close the change until each one has been exercised.

### 4.4 Move your operational habits to VCF Operations
"After your upgrade to VCF 9.1 completes, use VCF Operations to perform lifecycle management
activities" — the SDDC Manager **UI** is deprecated and will be removed in a future release
[D9.1 §0.3].

**But do not retire your SDDC Manager automation.** SDDC Manager remains in the 9.1 BOM
(`VCF Installer/SDDC Manager 9.1.0.0`, build `25371088`), still owns workload-domain deployment,
vCenter import, vSAN stretched-cluster configuration and LCM for ESX/vCenter/HCX/NSX
[D9.1 §0.3, §2], and its API went **375 → 423 operations with zero removed** [DELTA]. The only
API-level attrition is **21 individually deprecated operations** — the `/v1/edge-clusters` family,
`PATCH /v1/domains/{id}/overlay`, the `system/dns-configuration` and `system/ntp-configuration`
families, and the upgrade-precheck pair. Audit your scripts against that list of 21; leave the
rest alone.

### 4.5 Do not decommission the old 9.0 appliances yet — `UNVERIFIED`

> **`UNVERIFIED`** — whether the 9.0 fleet management, collector and for-logs appliances are
> auto-removed, left powered off, or require manual cleanup is **not documented in any page
> retrieved** [D9.1 §8.8]. Get Broadcom's answer before touching them.

---

## Summary of steps this runbook could NOT fully verify

| Step | What is unverified | Ref |
|---|---|---|
| 1.3 | Upgrade **orders 2–5** — collapsed into a range, contents unknown | D9.1 §5.3, §8.7 |
| Phase 3 | Ordering **within orders 9–23** (NSX, vCenter, ESX, vSAN, Tools) — membership sourced, sequence not | D9.1 §5.3, §8.7 |
| 0.2 | Depot online/offline configuration payload; bundle-type taxonomy | D9.0 §11 item 6 |
| 0.3 | The enumerated list of individual prechecks | D9.0 §11 item 7 |
| 0.5 | **The ports and protocols matrix** — never retrieved, in any version | D9.1 §5.2 |
| 0.8 | What SDDC Manager cannot do **during** an upgrade — page found, never fetched | D9.0 §11 item 13 |
| 0.11, 3.1 | **How a fleet-lcm / sddc-lcm token is obtained** — schemes are spec-declared, the issuer is documented nowhere; no token operation exists in either spec | `SPECFLT`, `SPECSDDCLCM`; DAUTH |
| 0.11 | **The role required for lifecycle write operations** (`POST /v1/upgrades`, `?action=apply`) — no role names captured for SDDC Manager or the LCM services | DAUTH |
| 4.5 | Fate of the 9.0 fleet management / collector / for-logs appliances post-upgrade | D9.1 §8.8 |
| — | The **5.2.x → 9.1**, **VVF → 9.1**, and **vSphere 8 + Aria 8 → 9.1** sequences — out of scope, not retrieved | D9.1 §5.1, §8.7 |

Nine of the ten gaps above sit on the critical path. **Close them against Broadcom
documentation before execution.**
