# VCF 9.1 — Lifecycle Management Reference

**Scope:** VMware Cloud Foundation 9.1.0.0 (released 12 MAY 2026). Everything here is `[9.1]`
unless explicitly tagged otherwise.

**Sources.** `D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DOPS` = `research/vcf-operations.md`; `DVS` = `research/vsphere-vcenter-vsan.md`;
`DAUTH` = `research/foundation-auth-identity.md`.
Machine-extracted specs from git tags of `github.com/vmware/vcf-api-specs`:
`SPEC9.1` = `9.1__sddc-manager.ops.json` (**423** ops, spec version `9.1.0.0`);
`SPECFLT` = `9.1__fleet-lcm.ops.json` (**51** ops, base `/fleet-lcm`);
`SPECSDDCLCM` = `9.1__sddc-lcm.ops.json` (**26** ops, base `/sddc-lcm`);
`DELTA` = `spec-inventory/DELTA-9.0-to-9.1.md`.
Every endpoint below was checked against these inventories and is marked
**spec-confirmed (9.1)** or flagged.

---

## Read this before anything else — two facts people get wrong

### 1. There is no product named "VCF Fleet Manager"

Across every 9.1 source, **no component with that name exists** [D9.1 §8.3]. The 9.0 name was
**VCF Operations fleet management**, a standalone appliance with its own BOM row
(`9.0.0.0` / build `24695816`) [D9.0 §1.2]. In 9.1 that appliance was **eliminated**:

> "The standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by
> fleet lifecycle" — 9.1 What's New, VCF Operations [D9.1 §0.2]

> "completely replaces the standalone Fleet Management Appliance introduced in version 9.0. It is
> replaced with two new services—Fleet Lifecycle and SDDC Lifecycle—which run natively within VCF
> Management Services." — Broadcom KB 440630 [D9.1 §0.2]

The 9.1 nouns are **fleet lifecycle** and **SDDC lifecycle** (services inside VCF Management
Services), fronted by the **VCF Operations** UI/API. "Fleet Management" survives only as a doc
section name and a VCF Operations UI feature grouping [D9.1 §0.1].

**Spec corroboration:** `fleet-lcm` and `sddc-lcm` **do not exist at the 9.0.0.0 tag** and appear
for the first time at 9.1.0.0 — 51 and 26 operations respectively [DELTA]. That version split is
the core architectural change.

### 2. SDDC Manager is NOT gone in 9.1 — only its UI is deprecated

- It is **in the 9.1 BOM**, merged with VCF Installer into one row:
  `VCF Installer/SDDC Manager 9.1.0.0 (25371088)` [D9.1 §2]. In 9.0 these were two rows.
- Its documented 9.1 role: *"Provides support for lifecycle management for ESX, vCenter, HCX, and
  NSX; deployment of workload domains; import of vCenter instances; configuration of vSAN
  stretched clusters"* [D9.1 §0.3].
- It **drives the first half of the 9.0.x → 9.1 upgrade**, up to and including its own
  self-upgrade [D9.1 §5.3].
- Its scale **increased**: max 5000 hosts per VCF Instance (2x over 9.0) and 256 simultaneous
  cluster upgrades [D9.1 §3.5].

What is deprecated, precisely:

> "The SDDC Manager UI is being deprecated and will be removed in a future release. After your
> upgrade to VCF 9.1 completes, use VCF Operations to perform lifecycle management activities."
> — Upgrading to VCF 9.1 [D9.1 §0.3]

That sentence scopes the deprecation to the **UI**. No retrieved 9.1 page states the SDDC Manager
**API** is deprecated [D9.1 §8.4].

**The API grew.** From the machine-computed diff [DELTA]:

| Product | 9.0 ops | 9.1 ops | added | **removed** | newly deprecated |
|---|---|---|---|---|---|
| `sddc-manager` | **375** | **423** | 48 | **0** | 21 |

Zero operations removed. 48 added. 21 individually marked deprecated (edge-cluster operations,
domain overlays, system DNS/NTP configuration, and the upgrade-precheck pair). Anyone claiming
"SDDC Manager is gone in 9.1" is contradicted by the spec itself.

---

## Contents

- [Read this before anything else — two facts people get wrong](#read-this-before-anything-else--two-facts-people-get-wrong)
- [Prerequisites](#prerequisites)
  - P0 — Authentication to all three surfaces you will call
  - P1 — Minimum workload-domain version gate
  - P2 — Depot configured, and the right bundles are present
  - P3 — VCF Management Services deployment prerequisites
  - P4 — Prechecks run and clean, and know where the precheck API now lives
  - P5 — Credential and password state
  - P6 — Identity: the vIDM → identity broker migration breaks OAuth clients
  - P7 — Licensing: the License server is new and required
  - P8 — Caller role and privilege for lifecycle write operations — UNVERIFIED
  - P9 — Items the research could not verify
- [The LCM surface in 9.1 — who does what](#the-lcm-surface-in-91--who-does-what)
- [Fleet lifecycle API (`/fleet-lcm`) — 51 operations](#fleet-lifecycle-api-fleet-lcm--51-operations-all-spec-confirmed-91)
- [SDDC lifecycle API (`/sddc-lcm`) — 26 operations](#sddc-lifecycle-api-sddc-lcm--26-operations-all-spec-confirmed-91)
- [SDDC Manager API in 9.1 — what changed](#sddc-manager-api-in-91--what-changed)
- [Task polling in 9.1](#task-polling-in-91)
- [Upgrade orderings — three of them, and they are not interchangeable](#upgrade-orderings--three-of-them-and-they-are-not-interchangeable)
- [Prose-vs-spec discrepancies found while writing this file](#prose-vs-spec-discrepancies-found-while-writing-this-file)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what must
hold, **how to verify it**, the version it applies to, and whether 9.0 differs.

### P0 — Authentication to all three surfaces you will call `[9.1]`

**Must be true:** you hold a valid credential for **each** of the three distinct authentication
surfaces used by this file and by `../upgrade-runbook.md`. They do not share tokens; a token
issued by one is not accepted by another.

| Surface | Base | Scheme | How you obtain it | Which operations need it |
|---|---|---|---|---|
| **SDDC Manager** | `https://<sddc-manager-fqdn>` + `/v1` | `Authorization: Bearer <accessToken>` | `POST /v1/tokens` with `{"username":"…","password":"…"}` → `{"accessToken":"<JWT>","refreshToken":{"id":"<UUID>"}}`; refresh with `PATCH /v1/tokens/access-token/refresh` (refresh-token UUID as `text/plain`); revoke with `DELETE /v1/tokens/refresh-token`. Access token **1 h**, refresh token **24 h**. All three **spec-confirmed (9.1)** (tag `Tokens`). SDDC Manager is **excluded from VCF SSO** — do not present a VIDB token here [DAUTH]. | Every `/v1/...` call below: P1 version checks, P2 depot/bundles, P4 `check-sets` and the (deprecated) upgrade prechecks, P5 credentials, P7 `license-checks`, and the upgradables/upgrades/tasks operations — including the write operation **`POST /v1/upgrades`**. |
| **VCF Operations** | `https://<vcfops-fqdn>` + `/suite-api` | `Authorization: OpsToken <token>` (legacy `Authorization: vRealizeOpsToken <token>` "continues to be supported") | `POST /suite-api/api/auth/token/acquire` with `{"username":"…","password":"…"}` → `token` (format `<uuid>::<uuid>`) plus `expiresAt`/`validity`; release with `POST /suite-api/api/auth/token/release`. Both **spec-confirmed (9.1)**. 9.1 additionally accepts a **Bearer** token issued by the identity broker, and adds `POST /suite-api/api/auth/token/exchange` (**9.1-only**) for service-scoped JWTs [DAUTH; DOPS]. | The VCF Operations task pollers in *Task polling in 9.1* (`/suite-api/api/tasks`, the 9.1-only `fleet-management/iam` and `salt` task endpoints), the P7 licensing view, and everything driven through the VCF Operations UI/API from order 6 onward. |
| **fleet lifecycle / SDDC lifecycle** | `https://<host>` + `/fleet-lcm` or `/sddc-lcm` | `SPECFLT` declares **`basicAuth`** (HTTP `basic`) **and `bearerToken`** (HTTP `Bearer`, *"Bearer token using a JWT"*); `SPECSDDCLCM` declares **`bearerToken` only — no basic auth**. | **UNVERIFIED — see the box below.** | Every `/fleet-lcm/v1/...` and `/sddc-lcm/v1/...` call: P2 depot metadata and release versions, P3 `health` and resource sizing, **P4 `POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck`**, the whole upgrade-plan workflow (`?action=configure` / `?action=precheck` / **`?action=apply`**), the component and sddc-lcms trees, and the LCM task pollers. |

> **UNVERIFIED — fleet-lcm / sddc-lcm token acquisition. Close this BEFORE the change window.**
> The specs declare *which schemes are accepted* but **neither spec contains a token-issuing
> operation**: there is no `/fleet-lcm/v1/tokens`, no `/sddc-lcm/v1/tokens`, and **zero operations
> whose path contains `token`, `auth` or `login` in either `SPECFLT` or `SPECSDDCLCM`**
> (spec-confirmed absence, both inventories). **Where the JWT comes from — the identity broker,
> VCF Operations, or a local appliance account — is not established by any source in this
> research.** The 9.0 fleet-management Basic-auth pattern (`echo -n 'admin@local:<password>' |
> base64`, Broadcom KB 409715 [DAUTH]) authenticated an appliance that **does not exist in 9.1**,
> so it cannot be assumed to carry forward. Establish and test this credential path against a real
> 9.1 system **before** you depend on it — finding out at the `?action=apply` step, mid-upgrade,
> is exactly the failure this file exists to prevent. See `../upgrade-runbook.md` gate 0.11.

**9.0 difference:** 9.0 has only two of these surfaces. SDDC Manager `/v1/tokens` and VCF
Operations `token/acquire` are identical in both versions [DAUTH]; `fleet-lcm` and `sddc-lcm` do
not exist at 9.0, where the corresponding appliance used HTTP Basic auth with no token endpoint.
See `../9.0/lifecycle.md` P6.

### P1 — Minimum workload-domain version gate `[9.1]`

**Must be true, verbatim from the 9.1 Lifecycle Management guide:**

> "all workload domains must be at VMware Cloud Foundation 5.2 or later. If any workload domain
> is at a version lower than 5.2, you must upgrade it to 5.2 and then upgrade to 9.1." [DVS,
> sourced to `.../9-1/lifecycle-management.html`]

**Supported source versions for the instance as a whole** [D9.1 §5.1]: "VMware Cloud Foundation
5.2.x or 9.0.x to 9.1"; vSphere Foundation 5.2.x or 9.0.x to 9.1; plus a separate path for
vSphere 8 + Aria Operations 8 environments that have **no SDDC Manager, NSX, or other Aria
components**. "Upgrading your environment to version 9.1 requires a strict component upgrade
sequence."

**Additional gate for the mid-upgrade pivot** [D9.1 §5.2], verbatim from the Deploy VCF
Management Services prerequisites: **"Verify that VCF Operations and SDDC Manager are at version
9.1."** VCF Management Services cannot be deployed before both are on 9.1.

**How to verify:**
- `GET /v1/domains` then, per domain, `GET /v1/releases/domains/{domainId}` — reports the release
  the domain is currently on. **Spec-confirmed (9.1)** (tag `TargetUpgradeVersion`).
- `GET /v1/releases/domains/{domainId}/future-releases` — what the domain is allowed to move to.
  **Spec-confirmed (9.1)**.
- `GET /v1/version-drift` — **new in 9.1**, reports version drift for a component.
  **Spec-confirmed (9.1)** (tag `ComponentVersions`). No 9.0 equivalent.
- `GET /v1/sddc-managers` / `GET /v1/sddc-managers/{id}` for SDDC Manager's own version.
  **Spec-confirmed (9.1)**.
- Cross-check the **VMware Interoperability Matrix**,
  `https://interopmatrix.broadcom.com/Upgrade?productId=851` [D9.1 §5.2].

**9.0 difference:** the 9.0 gate is different and looser — upgrade to 9.0 is supported from **VCF
5.0 or later**, sequential or skip-level [D9.0 §4.4], and workload-domain updates are *optional*
while the management-domain upgrade is mandatory [D9.0 §4.1]. The "≥ 5.2 for every workload
domain" rule is a **9.1 gate**, not a 9.0 one.

### P2 — Depot configured, and the right bundles are present `[9.1]`

**Must be true:** binaries for both the fleet layer and the instance layer must be downloadable.
9.1 introduces **software depot** as a distinct BOM component (`9.1.0.0`, build `25371105`)
[DOPS §BOM] that "handles binaries for all VCF components", driven from the VCF Operations UI
[DVS]. "VCF Operations now uses the fleet lifecycle, SDDC lifecycle, and **software depot**
components to orchestrate lifecycle operations on both fleet and instance-level components"
[D9.1 §0.4].

Before deploying VCF Management Services you must **download install binaries for**: VCF services
runtime, fleet lifecycle, SDDC lifecycle, software depot, identity broker, Salt RaaS, Salt master,
**license server**, telemetry [D9.1 §5.2].

**How to verify:**
- SDDC Manager side (**all spec-confirmed (9.1)**): `GET /v1/system/settings/depot`,
  `GET /v1/system/settings/depot/depot-sync-info`,
  `GET /v1/system/settings/depot/machine-details` (**new in 9.1**),
  `GET /v1/bundles`, `GET /v1/bundles/download-status`, `GET /v1/bundles/domains/{id}`.
- Fleet lifecycle side (**spec-confirmed (9.1)**, `SPECFLT`):
  `POST /fleet-lcm/v1/depot-metadata?action=sync` (tag `Depot Metadata`) to sync depot metadata;
  `GET /fleet-lcm/v1/release-versions` and `GET /fleet-lcm/v1/release-versions/target-versions`
  to see what the fleet can move to;
  `GET /fleet-lcm/v1/upgrade-plans/{planId}/bundles` to see the bundles a plan requires.
- SDDC lifecycle side (**spec-confirmed (9.1)**, `SPECSDDCLCM`):
  `POST /sddc-lcm/v1/depot` (set the depot) and `POST /sddc-lcm/v1/depot/components`
  (resolve components against it).

**Online vs offline.** Online = the depot pulls from Broadcom; offline/air-gapped = binaries are
staged locally, historically via the **VCF Download Tool** CLI, into which the deprecated
standalone UMDS was folded [D9.0 §6.2, §9.1]. VCF Download Tool remains a 9.1 BOM row [D9.1 §2].

> **UNVERIFIED.** The exact 9.1 offline-depot procedure, the depot-mode field names, and the
> bundle-type taxonomy were **not retrieved in research** — the equivalent 9.0 gap is recorded
> explicitly [D9.0 §11 item 6], and no 9.1 page closing it was fetched. The existence of a
> settable depot is spec-confirmed (`POST /sddc-lcm/v1/depot`, `PUT /v1/system/settings/depot`);
> its payload shape is not. Read the live schema before constructing a body.

**9.0 difference:** 9.0 had **no software depot component**. Binaries were split between the
fleet management appliance (management components) and SDDC Manager (core components)
[D9.0 §6.2]. The SDDC Manager depot endpoints exist in both versions;
`/v1/system/settings/depot/machine-details` is 9.1-only [DELTA].

### P3 — VCF Management Services deployment prerequisites `[9.1 only]`

VCF Management Services is **new in 9.1** and is "a mandatory, required part of the deployment"
[D9.1 §0.4]. Before deploying it [D9.1 §5.2]:

- "Verify that all required ports are open. See VMware Ports and Protocols."
- "Verify that your certificates are configured and use the proper Fully Qualified Domain Name
  (FQDN)."
- **"Verify that VCF Operations and SDDC Manager are at version 9.1."** (see P1)
- Download the install binaries listed in P2.
- Obtain administrative credentials for the VCF Operations instance.
- Deploy and configure a **cloud proxy** if the environment lacks one.
- A centralised **VCF License Server is now a required component**.

**How to verify:** certificate FQDN correctness via SDDC Manager
`GET /v1/sddc-manager/trusted-certificates` (**spec-confirmed (9.1)**) and the VCF Operations
certificate-management APIs; component readiness via
`GET /fleet-lcm/v1/health` and `GET /sddc-lcm/v1/health` (**spec-confirmed (9.1)**);
resource sizing before deployment via `POST /fleet-lcm/v1/components/resource-requirements` and
`GET /fleet-lcm/v1/components/resource-sizes` (**spec-confirmed (9.1)**), and on the SDDC Manager
side `POST /v1/vcf-management-components/resources-calculation` (**spec-confirmed (9.1)**, new in
9.1).

> **UNVERIFIED — the ports matrix.** The prerequisite says "verify that all required ports are
> open" and points at "VMware Ports and Protocols", but **that matrix was never retrieved in any
> version of the research**. Do not produce a port list. Say the requirement exists and point at
> the Broadcom ports document.

**9.0 difference:** none of this applies to 9.0 — VCF Management Services did not exist
[D9.1 delta #2].

### P4 — Prechecks run and clean, and know where the precheck API now lives `[9.1]`

**Where prechecks live in 9.1:**

- **Fleet lifecycle — the new first-class precheck** (**spec-confirmed (9.1)**, `SPECFLT`):
  ```
  POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck
  ```
  This runs against a created upgrade plan; poll the returned task via
  `GET /fleet-lcm/v1/tasks/{taskId}`.
- **SDDC Manager check-sets** — carried forward and **extended** in 9.1
  (**all spec-confirmed (9.1)**):
  ```
  POST /v1/system/check-sets            POST /v1/system/check-sets/queries
  GET  /v1/system/check-sets            GET|PATCH /v1/system/check-sets/{runId}
  POST /v1/system/check-sets/{runId}/exports        <- new in 9.1
  GET  /v1/system/check-sets/{runId}/exports        <- new in 9.1
  GET  /v1/system/check-sets/{runId}/exports/data   <- new in 9.1
  ```
  The three `exports` operations are 9.1 additions [DELTA]; they back the documented "enhanced
  prechecks exportable to CSV" [DOPS].
- **SDDC Manager upgrade prechecks — NOW DEPRECATED.** In `SPEC9.1`, both
  `POST /v1/upgrades/{upgradeId}/prechecks` and `GET /v1/upgrades/{upgradeId}/prechecks/{precheckId}`
  carry `deprecated: true`. They were **not** deprecated in `SPEC9.0`. They still exist and still
  resolve — nothing was removed — but new automation should target the fleet-lifecycle precheck
  action. This is spec-confirmed in both directions.
- **Still present and not deprecated** (**spec-confirmed (9.1)**):
  `POST|GET /v1/hosts/prechecks[/{id}]`,
  `POST|GET /v1/domains/{domainId}/isolation-prechecks[/{precheckId}]`.
- **`/v1/system/precheck`** — this path was removed from the SDDC Manager LCM API back **in 9.0**
  with the note "functionality moved to VCF Operations" [D9.0 §9.2]. **Spec check: the exact path
  is absent from both `SPEC9.0` and `SPEC9.1`.** The removal is confirmed. See Discrepancies for
  what could not be confirmed about the destination.

9.1 also advertises "improved prechecks using native VCF component capabilities" and a
"Component Versions tab shows current and target versions for all supported components"
[D9.1 §3.5].

**How to verify:** create the plan, precheck it, and only then apply — see the ordering section.

> **UNVERIFIED.** The individual prechecks are still **not enumerated** in any retrieved source
> (the 9.0 gap [D9.0 §11 item 7] was never closed for 9.1). Do not present a named checklist of
> prechecks as fact.

**9.0 difference:** in 9.0 the upgrade-precheck pair is the *primary* precheck API and is **not**
deprecated; there is no `upgrade-plans` resource and no fleet-lifecycle service at all.

### P5 — Credential and password state `[9.1]`

**Must be true:** no expired credentials, no in-flight rotation.

**How to verify (all spec-confirmed (9.1)):** `GET /v1/credentials`,
`POST /v1/credentials/expirations` → `GET /v1/credentials/expirations/{id}`,
`GET /v1/credentials/tasks` / `GET /v1/credentials/tasks/{id}`.
9.1 additionally offers `POST /v1/vcf-management-components/passwords` — "generates a password
that will be valid for all components" (**spec-confirmed (9.1)**, new in 9.1) — and, on the fleet
side, `POST /fleet-lcm/v1/components/generated-passwords` (**spec-confirmed (9.1)**).

Note the 9.1 Fleet Management page states SDDC Manager still "handles certain specific operations
(particularly password management)" [DOPS]. Password *policy* moves to VCF Operations Fleet
Settings [D9.1 §3.5].

**9.0 difference:** the credentials API is the same; the two password-generation endpoints above
are 9.1-only.

### P6 — Identity: the vIDM → identity broker migration breaks OAuth clients `[9.1 only]`

**This is the prerequisite most likely to be missed, and it silently breaks automation.**

The vIDM → VCF Identity Broker migration is a **9.1 workflow**. Verbatim consequences [DAUTH,
sourced to `.../9-1/fleet-management/.../migrating-vmware-identity-manager-to-vcf-identity-broker.html`]:

- "Users and groups are migrated from VMware Identity Manager to identity broker."
- **"OAuth clients are not migrated automatically. You must manually regenerate the client and
  secret using identity broker and configure accordingly."**
- "Local accounts and local accounts with multifactor authentication are not supported."
- "Multifactor authentication with Active Directory is not supported."
- Sync settings are compared but **not migrated**; adjust manually. If VCF Operations, VCF
  Automation, or NSX use the legacy system, the migration script repoints them.

**Practical consequence:** every OAuth client used by your automation against SSO-federated
components stops working across this migration. Plan a regeneration step and a re-configuration
of every consumer of those credentials, inside the change window.

**How to verify:** before migrating, inventory every OAuth client in vIDM and every script/system
holding a client secret. After migrating, re-create each client in identity broker (VCF
Operations → Fleet Management → Managing API Clients and Tokens, a 9.1-only subtree [DAUTH]) and
re-issue secrets. Confirm by exercising the token exchange:
admin creates API clients in VIDB → admin requests a long-lived API refresh token from the VCF
Operations UI → script exchanges it at VIDB for a short-lived bearer access token → script calls
the component [D9.1 §0.5].

**9.0 difference:** the 9.0 SSO tree contains **no API client, API token, OAuth client, or role
management pages at all** [DAUTH]. SSO-issued, role-scoped API tokens are **9.1-only**. In 9.0
you use per-product credentials (SDDC Manager `/v1/tokens`, VCF Ops `token/acquire`, NSX session,
vCenter session).

**Constant across both versions:** **SDDC Manager and ESX are explicitly excluded from VCF SSO**
[DAUTH]. SDDC Manager auth remains its own `POST /v1/tokens` bearer flow in 9.1
(**spec-confirmed (9.1)**, tag `Tokens`) — do not try to drive SDDC Manager with a VIDB token.

### P7 — Licensing: the License server is new and required `[9.1]`

**Must be true:** a License server exists. "Licenses are now stored in a license server, instead
of in VCF Operations" [D9.1 §3.5]. "You must add at least one license server to each VCF
Operations instance that you use for license management" [D9.1 §6]. It is a **required component**
for VCF and vSphere Foundation [D9.1 §5.2] and has its own BOM row
(`License server 9.1.0.0`, build `25346031`) [D9.1 §2] with **no 9.0 counterpart**.

The 9.0.x → 9.1 upgrade sequence includes an explicit **licence transfer** step, performed from
VCF Operations, at the same stage as the VCF Management Services deployment [D9.1 §5.3].

**How to verify:** VCF Operations licensing view; on SDDC Manager,
`POST /v1/resources/license-checks` → `GET /v1/resources/license-checks/{id}`
(**spec-confirmed (9.1)**). Known 9.1 upgrade failure modes include vCenter licensing failures
post-upgrade and licence assignment failures when the sequence is done wrong [D9.1 §5.5].

**9.0 difference:** 9.0 stores licences in VCF Operations with no License server component
[D9.0 §5].

### P8 — Caller role and privilege for lifecycle write operations `[9.1]` — UNVERIFIED

**Must be true:** the account behind the credentials in P0 holds whatever role is required to
perform lifecycle **write** operations — `POST /v1/upgrades` and `PATCH /v1/upgrades/{upgradeId}`
on SDDC Manager, and `POST /fleet-lcm/v1/upgrade-plans/{planId}?action=configure|precheck|apply`
on fleet lifecycle.

> **UNVERIFIED. The required role for lifecycle write operations is not documented in the sources
> consulted; verify before delegating credentials.** No retrieved page names SDDC Manager role
> names at all, and SDDC Manager is excluded from VCF SSO [DAUTH], so the 9.1 VCF built-in roles
> do not govern it. The 9.1 built-in-role mapping that *does* exist (VCF Administrator, VCF
> Viewer, SDDC Administrator, SDDC Viewer) maps only to vCenter, NSX, VCF Operations, VCF
> Automation, HCX and Orchestrator roles — **neither SDDC Manager nor fleet/SDDC lifecycle appears
> in that mapping** [see `../../../vcf-foundation/references/9.1/auth-and-identity.md` §4]. The
> OpenAPI specs declare security *schemes* but no per-operation privilege requirement.
>
> Practical consequences: do not assume a token that can read `GET /v1/upgradables` can also
> submit `POST /v1/upgrades`; do not invent a role name to put in a runbook or a service-account
> request; and do not hand an upgrade operator a credential on the assumption its role is
> sufficient. Confirm against Broadcom's role documentation, or empirically against a
> non-production instance, **before** the account is provisioned.

### P9 — Items the research could not verify — state these as gaps

- **Ports and protocols matrix** — required by the prerequisites, never retrieved, in either
  version.
- **How a fleet-lcm / sddc-lcm token is obtained** — the schemes are spec-declared, the issuer is
  not documented anywhere in this research. See **P0**; it is a blocking gap, not a footnote.
- **The role required for lifecycle write operations** — not documented for SDDC Manager or for
  the LCM services. See **P8**.
- **Bundle-type taxonomy and depot online/offline payload shape** — not documented on any fetched
  page [D9.0 §11 item 6]; not closed for 9.1.
- **Enumerated precheck list** — not documented [D9.0 §11 item 7].
- **Upgrade steps 2–5 and 9–23 of the 9.0.x → 9.1 sequence, individually** — the retrieved page
  collapsed them into ranges [D9.1 §8.7]. The *shape* of the sequence is verified; the exact
  intra-range ordering is not.
- **Fate of the 9.0 appliances after the upgrade** — whether the 9.0 fleet management, collector,
  and for-logs appliances are auto-removed, left powered off, or need manual cleanup is
  **unknown**; the Deploy VCF Management Services page "contains no information about
  decommissioning, replacing, or migrating existing 9.0 fleet management appliances"
  [D9.1 §8.8].
- **Literal 9.1 base URLs from Broadcom docs** — no 9.1 techdocs page prints a literal REST base
  path [D9.1 §8.1]. The base paths quoted in this file come from the **OpenAPI specs**, which is
  the stronger source, but note that `SPECFLT`/`SPECSDDCLCM` declare an example host
  (`https://vcf.broadcom.com/fleet-lcm`, `.../sddc-lcm`) — the **path prefix** `/fleet-lcm` and
  `/sddc-lcm` is the load-bearing part; substitute your own host.
- **Build numbers for some VCF Management Services BOM rows** — partially captured [D9.1 §8.6];
  `DOPS` supplies fleet lifecycle `25371109`, SDDC lifecycle `25371107`, software depot
  `25371105`.

---

## The LCM surface in 9.1 — who does what

```
VCF Operations ............ the single pane of glass; owns Fleet Management + Lifecycle UX
  └── VCF Management Services (NEW in 9.1) — containerized services on a common runtime
        ├── VCF services runtime .. hosting/orchestration runtime (every instance)
        ├── fleet lifecycle ....... orchestrates lifecycle ACROSS the fleet (first instance)
        ├── SDDC lifecycle ........ install/update/patch WITHIN an instance (every instance)
        ├── software depot ........ binary / OCI image store
        ├── identity broker (VIDB)  SSO / OAuth token issuance
        ├── log management, real-time metrics (+ store), telemetry
        └── Salt master / Salt RaaS  desired-state config
SDDC Manager .............. still runs; workload-domain deploy, vCenter import, vSAN stretched
                            cluster config, ESX/vCenter/HCX/NSX LCM. UI deprecated, API grew.
License server (NEW) ...... stores licences (moved out of VCF Operations)
```
[D9.1 §0.4]

| Concern | 9.1 owner |
|---|---|
| Lifecycle of the **management components** (identity broker, VCF Operations, Ops for networks, real-time metrics + store, Salt master, Salt RaaS, VCF Automation, telemetry, SDDC lifecycle, software depot, log management, migration service engine, VCF services runtime) | **fleet lifecycle** — "unified framework for: install, upgrade, patch, backup, restore, maintain management components" [DOPS] |
| Install / update / patch **within a VCF instance** (the domain and workload estate) | **SDDC lifecycle** [D9.1 §0.4] |
| Binary / image store for all of the above | **software depot** [D9.1 §0.4] |
| Workload-domain deployment, vCenter import, vSAN stretched-cluster config, and LCM of **ESX, vCenter, HCX, NSX** | **SDDC Manager** [D9.1 §0.3] |
| ESX image application inside a cluster | **vLCM images** (baselines removed for cluster management in vCenter 9.0) [DVS] |
| UI for all of it | **VCF Operations** [D9.1 §0.3] |

**Statement to anchor on:** "VCF Operations now uses the fleet lifecycle, SDDC lifecycle, and
software depot components to orchestrate lifecycle operations on both fleet and instance-level
components." [D9.1 §0.4] And: 9.1 "transitions the lifecycle management of VCF Operations, VCF
Operations for logs, VCF Operations for networks, VCF Automation, and VCF Identity Broker to the
new fleet lifecycle and SDDC lifecycle components." [D9.1 §5.3]

**vLCM interaction, unchanged in shape:** VCF-level lifecycle drives the domain/cluster upgrade;
vLCM applies the desired ESX image. VCF Operations "can manage ESX components and vSphere
Lifecycle Manager images" [DVS]. 9.1 adds global remediation settings for Configuration Profile
clusters, image integrity validation for customised ESX images, and optimised VIB transfer
[D9.1 §3.1]. A dedicated 9.1 topic exists for transitioning baselines → images [DVS].

---

## Fleet lifecycle API (`/fleet-lcm`) — 51 operations, all spec-confirmed (9.1)

Base path prefix `/fleet-lcm`; spec title *VCF Fleet LCM Service APIs*; security schemes
`basicAuth` and `bearerToken` (JWT). Tags: Components, Config, Depot Metadata, Fleet LCM System,
Health, Network, Release Version, Resources, SDDC LCM, SupportBundles, SupportedComponents, Task,
Upgrade Plan. **This service does not exist at the 9.0.0.0 tag.**

**Upgrade Plan — the core lifecycle workflow**
```
GET  /fleet-lcm/v1/upgrade-plans
POST /fleet-lcm/v1/upgrade-plans                        create a plan
POST /fleet-lcm/v1/upgrade-plans/validations            validate before creating
GET  /fleet-lcm/v1/upgrade-plans/{planId}
PATCH/fleet-lcm/v1/upgrade-plans/{planId}
GET  /fleet-lcm/v1/upgrade-plans/{planId}/bundles       bundles the plan needs
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=configure
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck
POST /fleet-lcm/v1/upgrade-plans/{planId}?action=apply
```
Canonical order: **validate → create → configure → precheck → apply → poll**.

**Release versions / depot metadata**
```
GET  /fleet-lcm/v1/release-versions
GET  /fleet-lcm/v1/release-versions/target-versions
POST /fleet-lcm/v1/depot-metadata?action=sync
```

**Components (the management-component estate)**
```
GET|POST /fleet-lcm/v1/components            POST /fleet-lcm/v1/components/validations
GET  /fleet-lcm/v1/components/supported-types
POST /fleet-lcm/v1/components/status         POST /fleet-lcm/v1/components/generated-passwords
POST /fleet-lcm/v1/components/resource-requirements   GET /fleet-lcm/v1/components/resource-sizes
GET|PATCH|POST /fleet-lcm/v1/components/{componentId}      (POST = perform component action)
GET|PATCH /fleet-lcm/v1/components/{componentId}/config
POST /fleet-lcm/v1/components/{componentId}/config/validations
POST /fleet-lcm/v1/components/{componentId}/validations
GET  /fleet-lcm/v1/components/{componentId}/nodes
GET  /fleet-lcm/v1/components/{componentId}/status
GET|POST /fleet-lcm/v1/components/{componentId}/support-bundles
DELETE   /fleet-lcm/v1/components/{componentId}/support-bundles/{supportBundleId}
```

**SDDC LCM registration — how fleet lifecycle knows about instance-level LCM**
```
GET|PATCH|POST /fleet-lcm/v1/sddc-lcms                  (POST = register an SDDC LCM)
GET|PATCH /fleet-lcm/v1/sddc-lcms/{sddcLcmId}
GET|POST  /fleet-lcm/v1/sddc-lcms/{sddcLcmId}/backups
GET  /fleet-lcm/v1/sddc-lcms/{sddcLcmId}/inventory/datastores
POST /fleet-lcm/v1/sddc-lcms/{sddcLcmId}/refresh
```

**System, config, health, network**
```
GET|POST /fleet-lcm/v1/system      (POST = performSystemUpgrade — fleet lifecycle self-upgrade)
GET|POST /fleet-lcm/v1/config
GET  /fleet-lcm/v1/health
POST /fleet-lcm/v1/address-attributes
```

## SDDC lifecycle API (`/sddc-lcm`) — 26 operations, all spec-confirmed (9.1)

Base path prefix `/sddc-lcm`; spec title *VCF SDDC LCM Service APIs*. Tags: Components, Config,
Depot, Health, Nodes, SupportBundles, Task. **Does not exist at the 9.0.0.0 tag.**

```
GET|POST /sddc-lcm/v1/components                POST /sddc-lcm/v1/components/status
GET|POST /sddc-lcm/v1/components/backups        (POST = backupRestoreComponentsAction)
GET|PATCH|POST /sddc-lcm/v1/components/{componentId}      (POST = perform component action)
GET|PATCH /sddc-lcm/v1/components/{componentId}/config
GET  /sddc-lcm/v1/components/{componentId}/nodes
GET  /sddc-lcm/v1/components/{componentId}/status
GET|POST /sddc-lcm/v1/components/{componentId}/support-bundles
DELETE   /sddc-lcm/v1/components/{componentId}/support-bundles/{supportBundleId}
GET|POST /sddc-lcm/v1/config
POST /sddc-lcm/v1/depot                         set the depot for this instance
POST /sddc-lcm/v1/depot/components              resolve components against the depot
GET  /sddc-lcm/v1/health
POST /sddc-lcm/v1/nodes                         PATCH /sddc-lcm/v1/nodes/{nodeId}/config
```

Note SDDC lifecycle has **no upgrade-plan resource** — planning lives on fleet lifecycle, which
registers and refreshes SDDC LCM instances via `/fleet-lcm/v1/sddc-lcms`.

## SDDC Manager API in 9.1 — what changed

423 operations, **0 removed**, 48 added, 21 newly deprecated [DELTA]. Everything documented in
`../9.0/lifecycle.md` for bundles, depot settings, manifests, releases, compatibility matrices,
personalities, repository images, upgradables, upgrades and tasks **still resolves in 9.1**.

**Lifecycle-relevant additions, all spec-confirmed (9.1) and absent from `SPEC9.0`:**
```
GET  /v1/upgradables/domains/{domainId}/upgrade-sequences        supported upgrade sequences
GET  /v1/upgradables/domains/{domainId}/vcenter-sizing-infos     recommended vCenter size
GET  /v1/upgradables/domains/{domainId}/vcenter-upgrade-mechanisms   RDU vs alternatives
GET  /v1/version-drift                                            component version drift
GET  /v1/system/settings/depot/machine-details
POST /v1/system/check-sets/{runId}/exports  + GET .../exports, .../exports/data
PATCH /v1/sddc-manager   POST /v1/sddc-manager/validations   GET /v1/sddc-manager/validations/{id}
POST /v1/vcf-management-components/passwords
POST /v1/vcf-management-components/resources-calculation
POST /v1/vcf-management-components/vcfops-discovery              discover VCF Operations topology
GET  /v1/domains/{domainId}/image-compliance/queries/{queryId}  + POST .../image-compliance/queries
POST /v1/clusters/{clusterId}/remediations  + GET .../remediations/{remediationId}
GET  /v1/hosts/{id}/software
GET|POST|PUT|DELETE /v1/services-config[...]                     external service connections
GET|POST|DELETE /v1/domains/{domainId}/hcx-managers[...]         HCX LCM via SDDC Manager
```

**Newly deprecated in 9.1** (21 total, spec-confirmed): the whole `/v1/edge-clusters` family
(GET/POST/PATCH and its validations), `PATCH /v1/domains/{id}/overlay`, the
`/v1/system/dns-configuration` and `/v1/system/ntp-configuration` families, and
`POST|GET /v1/upgrades/{upgradeId}/prechecks[/{precheckId}]`. This matches the documented
"21 APIs deprecated, affecting edge cluster operations, domain overlays, and system DNS/NTP
configurations" [D9.1 §4] exactly — prose and spec agree.

**Auth to SDDC Manager in 9.1** is unchanged: `POST /v1/tokens`,
`PATCH /v1/tokens/access-token/refresh`, `DELETE /v1/tokens/refresh-token`
(**spec-confirmed (9.1)**). SDDC Manager is not SSO-federated [DAUTH].

## Task polling in 9.1

Three task surfaces now, and they are separate namespaces:

```
SDDC Manager:      GET /v1/tasks   GET /v1/tasks/{id}   PATCH /v1/tasks/{id}   DELETE /v1/tasks/{id}
fleet lifecycle:   GET /fleet-lcm/v1/tasks   GET /fleet-lcm/v1/tasks/{taskId}
                   POST /fleet-lcm/v1/tasks/{taskId}?action=cancel
                   POST /fleet-lcm/v1/tasks/{taskId}?action=retry
SDDC lifecycle:    GET /sddc-lcm/v1/tasks    GET /sddc-lcm/v1/tasks/{taskId}
                   POST /sddc-lcm/v1/tasks/{taskId}?action=cancel
                   POST /sddc-lcm/v1/tasks/{taskId}?action=retry
```
All **spec-confirmed (9.1)**. A task ID from one service is not resolvable on another. Poll the
service that started the work. Note the LCM services use an `?action=` query verb for
cancel/retry, whereas SDDC Manager uses `DELETE`/`PATCH` on the task resource.

VCF Operations has its own: `GET /suite-api/api/tasks`, `GET /suite-api/api/tasks/{id}`, plus
9.1-only `GET /suite-api/api/fleet-management/iam/tasks/{taskId}` and
`GET /suite-api/api/salt/tasks/{taskId}` (spec-confirmed against `9.1__vcf-operations.ops.json`).

---

## Upgrade orderings — three of them, and they are not interchangeable

Conflating orderings is a named failure mode. The 9.0 file carries the first two in full; they
are summarised here only so the third is not mistaken for them.

### Ordering A — major upgrade **5.x → 9.0** `[9.0]`
Core, via SDDC Manager: `SDDC Manager → NSX Manager → vCenter → ESX`. Management components
manual or pre-deployed. No explicit vSAN step. [D9.0 §4.4] — see `../9.0/lifecycle.md`.

### Ordering B — maintenance update **within 9.0.x** (9.0.0.0 → 9.0.1.0 → 9.0.2.0) `[9.0]`
Management first (fleet management appliance → VCF Operations instance → remaining), **then**
core: `SDDC Manager → NSX → vCenter → ESX hosts → vSAN`. [D9.0 §6.3] — see `../9.0/lifecycle.md`.
This is the ordering with the explicit **vSAN** tail step.

### Ordering C — major upgrade **9.0.x → 9.1** `[9.1]`

"Upgrading your environment to version 9.1 requires a strict component upgrade sequence."
[D9.1 §5.1] From the 9.1 upgrade guide [D9.1 §5.3]:

| Order | Component | UI that performs it |
|---|---|---|
| 0 | VCF Identity Broker 9.0.x — transition to VCF Management Network (if on NSX overlay) | **SDDC Manager** |
| 1 | VCF Operations & cloud proxy | **SDDC Manager** |
| 2–5 | *(collapsed into a range in the retrieved source — see UNVERIFIED below)* | **SDDC Manager** |
| 6 | **SDDC Manager** self-upgrade to 9.1 | **SDDC Manager** |
| 6 | **VCF Management Services & License Server** (deploy) | **VCF Operations** |
| 6 | Licence transfer | **VCF Operations** |
| 7 | VCF Identity Broker → 9.1 | **VCF Operations** |
| 8 | VCF Automation → 9.1 | **VCF Operations** |
| 9–23 | NSX, vCenter, ESX, vSAN, VMware Tools (management-domain components) | **VCF Operations** |

**The pivot is order 6.** SDDC Manager drives the upgrade **up to and including its own
upgrade**; VCF Operations drives everything after [D9.1 §5.3]. This is the single most important
structural fact about the 9.0→9.1 upgrade and the strongest evidence that SDDC Manager is not
"gone" in 9.1.

> **UNVERIFIED.** Orders 2–5 and 9–23 were collapsed into ranges on the retrieved page; their
> individual ordering is **not verified** [D9.1 §8.7]. Do not fabricate the intra-range steps.

**NSX Edge clusters move to the END of the domain upgrade in 9.1.** Two independent 9.1 sources:
- "NSX Edge clusters are now upgraded at the end of the domain upgrade process" [D9.1 §3.5]
- "Move NSX Edge/SVM Upgrades to the End of Upgrade Sequence" [D9.1 §3.3]

This is a change in **within-domain** ordering, distinct from the cross-component sequence above.
If you carry a 9.0-era mental model where Edge clusters are upgraded earlier in the domain
upgrade, correct it for 9.1 [D9.1 delta #10].

**Other 9.1 domain-upgrade behaviour changes** [D9.1 §3.5]: optimised NSX Manager and vCenter
maintenance windows and reduced-downtime update preparation; support for imported standalone
hosts and single-host clusters; the ability to **select specific hosts** during cluster upgrades
(skip problematic hosts); improved prechecks using native VCF component capabilities;
a Component Versions tab showing current and target versions. Scale: **5000 hosts per VCF
Instance** and **256 simultaneous cluster upgrades** [D9.1 §3.5].

**Known 9.1 upgrade failure modes when the sequence is done wrong** [D9.1 §5.5]: upgrade binaries
not appearing in VCF Operations 9.0; vCenter licensing failures post-upgrade; licence assignment
failures; ESXi host upgrade sync errors during the VCF Operations upgrade.

**UI path to deploy VCF Management Services** [D9.1 §5.4]: VCF Operations →
**Build > Lifecycle > VCF Instances** → **SDDC Manager Updates** tab → **Available Upgrades** →
**Install Components**.

For the executable step-by-step, see `../upgrade-runbook.md`.

---

## Prose-vs-spec discrepancies found while writing this file

1. **API size prose is stale.** A 9.1 techdocs page describes the SDDC Manager API as
   "~280 REST interfaces" and labels it "SDDC Manager (fleet management)" [D9.1 §0.5].
   `SPEC9.1` contains **423 operations**. Both the count and the "(fleet management)" label are
   misleading. Use 423, and do not let that parenthetical reintroduce "Fleet Manager."
2. **`/v1/system/precheck` destination is not spec-confirmable.** Its absence from SDDC Manager is
   confirmed in both `SPEC9.0` and `SPEC9.1`. But the claimed destination — "moved to VCF
   Operations" [D9.0 §9.2] — **has no matching operation in either the 9.0 or the 9.1 VCF
   Operations spec** (`/suite-api`, 370 → 504 ops; no path matching `precheck`). In 9.1 the
   spec-visible precheck surfaces are `POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck`
   and SDDC Manager's `check-sets`. Report the removal as fact; report the destination as
   documentation prose.
3. **Upgrade-precheck deprecation is spec-only.** `POST|GET /v1/upgrades/{upgradeId}/prechecks[...]`
   became `deprecated: true` in 9.1 and was not deprecated in 9.0. The prose summary of the
   "21 deprecated APIs" [D9.1 §4] mentions "edge cluster operations, domain overlays, and system
   DNS/NTP configurations" and **does not mention the upgrade prechecks**, though they are two of
   the 21. The spec is the better source here.
4. **Fleet/SDDC LCM base hosts are examples.** `SPECFLT` and `SPECSDDCLCM` declare
   `https://vcf.broadcom.com/fleet-lcm` and `.../sddc-lcm`. Treat `/fleet-lcm` and `/sddc-lcm` as
   the real path prefixes and substitute your own host. No Broadcom doc page printed a literal
   9.1 base path [D9.1 §8.1].
5. **`vcf-operations-for-logs` is gone as a spec.** 136 ops in 9.0; the product does not exist at
   the 9.1 tag, replaced by `log-management` (23 ops) [DELTA]. This is a rename-plus-reduction,
   not a straight rename — worth knowing if you automate against logging.
6. **Fleet-management appliance auth is 9.0-only.** The documented Basic-auth pattern for the
   fleet management API (`admin@local:<password>` base64) [DAUTH] has **no 9.1 successor** —
   the appliance it authenticated to no longer exists. fleet-lcm declares `basicAuth` and
   `bearerToken` schemes but the research contains no worked 9.1 fleet-lcm auth example.
   `UNVERIFIED`. **This is a prerequisite, not a footnote — it is stated in full at P0, and as
   gate 0.11 of `../upgrade-runbook.md`.** It is repeated here only because it is also a
   prose-vs-spec gap: the spec says which schemes are accepted and no source says who issues the
   token.
