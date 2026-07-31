# VCF 9.0 — Lifecycle Management Reference

**Scope:** VMware Cloud Foundation 9.0.x (9.0.0.0 / 9.0.1.0 / 9.0.2.0). Everything here is
`[9.0]` unless explicitly tagged otherwise.

**Sources.** `D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DOPS` = `research/vcf-operations.md`; `DVS` = `research/vsphere-vcenter-vsan.md`;
`DAUTH` = `research/foundation-auth-identity.md`.
`SPEC9.0` = `research/spec-inventory/9.0__sddc-manager.ops.json` (375 operations, spec version
`9.0.0.0`, from git tag `9.0.0.0` of `github.com/vmware/vcf-api-specs`).
Every endpoint below was checked against `SPEC9.0` — each one is marked
**spec-confirmed (9.0)** or flagged as a discrepancy.

**Two names to get right before anything else.**
1. There is **no product called "VCF Fleet Manager."** In 9.0 the component is
   **VCF Operations fleet management**, a standalone appliance with its own BOM row
   (`9.0.0.0`, build `24695816`) [D9.0 §1.2]. In 9.1 that appliance is eliminated and replaced
   by two services, **fleet lifecycle** and **SDDC lifecycle** [D9.1 §0.2]. Never write
   "Fleet Manager."
2. **SDDC Manager is not going away.** In 9.0 its **UI** is deprecated; its **API** is the
   supported automation surface [D9.0 §3.1]. See `../9.1/lifecycle.md` for how this carries
   into 9.1.

---

## Contents

- [Prerequisites](#prerequisites)
  - P1 — Binaries are present in the right place before any core LCM operation
  - P2 — Depot is configured and reachable (online or offline)
  - P3 — VCF Operations and the fleet management appliance are healthy and at a known version
  - P4 — Prechecks have been run and are clean
  - P5 — Credential and password state is valid
  - P6 — Authentication to SDDC Manager
  - P7 — Licensing state
  - P8 — Caller role and privilege for lifecycle write operations — UNVERIFIED
  - P9 — Items the research could not verify
- [The LCM surface in 9.0](#the-lcm-surface-in-90)
- [Bundles, depots, manifests, releases](#bundles-depots-manifests-releases)
- [Upgradables and upgrades](#upgradables-and-upgrades)
- [Task polling](#task-polling)
- [The two upgrade orderings — keep them apart](#the-two-upgrade-orderings--keep-them-apart)
- [Prose-vs-spec discrepancies found while writing this file](#prose-vs-spec-discrepancies-found-while-writing-this-file)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what must
hold, **how to verify it**, the version it applies to, and whether 9.1 differs.

### P1 — Binaries are present in the right place before any core LCM operation `[9.0]`

**Must be true:** binaries must be downloaded to **SDDC Manager** before core-component
lifecycle operations can proceed [D9.0 §6.4]. Binary ownership in 9.0 is **split**:
VCF Operations fleet management owns binaries for VCF **management** components; SDDC Manager
owns binaries for VCF **core** components, per VCF Instance [D9.0 §6.2].

**How to verify:** `GET /v1/bundles` and `GET /v1/bundles/download-status` on SDDC Manager
(both **spec-confirmed (9.0)**), plus `GET /v1/bundles/domains/{id}` to confirm the bundles
applicable to the target domain are present. For the management side, the fleet management
appliance is the authority; see P3.

**9.1 difference:** in 9.1 the fleet-management appliance is gone. Binary handling moves to the
**software depot** component inside VCF Management Services, orchestrated by fleet lifecycle and
SDDC lifecycle [D9.1 §0.2, §0.4; DOPS "software depot handles binaries for all VCF components"].

### P2 — Depot is configured and reachable (online or offline) `[9.0]`

**Must be true:** a depot must be configured before bundles can be synced or downloaded.

**How to verify:** `GET /v1/system/settings/depot` and
`GET /v1/system/settings/depot/depot-sync-info` on SDDC Manager (both **spec-confirmed (9.0)**).
Configure with `PUT /v1/system/settings/depot`; force a metadata refresh with
`PATCH /v1/system/settings/depot/depot-sync-info` (both **spec-confirmed (9.0)**).
Proxy for a restricted-egress site: the `ProxyConfiguration` tag exists in `SPEC9.0`.

**Offline / disconnected path:** the **VCF Download Tool** is "a command-line interface (CLI)
utility designed to simplify the management of binaries and metadata" [D9.0 §6.2]. The
standalone **UMDS** is deprecated and its function is folded into the VCF Download Tool
[D9.0 §9.1]. `PATCH /v1/system/host-bundle-depot` (tag `UMDS`) is **spec-confirmed (9.0)** and
is the API-level hook for pointing host bundles at an alternate depot.

> **UNVERIFIED.** The research explicitly records that the 9.0 core-components LCM page and the
> binary-management page **did not define bundle types or the depot online/offline distinction**
> [D9.0 §11 item 6]. So: the *existence* of online and offline depot modes is confirmed at the
> API and tooling level (depot settings, Download Tool, UMDS hook), but **the exact
> configuration payloads, mode names, and the enumerated bundle types are not verified.** Do not
> invent a `"depotType": "OFFLINE"` field or a bundle-type enum. Read the live
> `Depot Settings` / `Bundles` schemas before writing a body.

**9.1 difference:** same API paths still exist on SDDC Manager in 9.1, plus a new
`GET /v1/system/settings/depot/machine-details`. The *authoritative* depot in 9.1 is the
separate software depot component. See `../9.1/lifecycle.md` P2.

### P3 — VCF Operations and the fleet management appliance are healthy and at a known version `[9.0]`

**Must be true:** VCF Operations is the central LCM platform in 9.0 — "Use VCF Operations as a
VI administrator to manage the lifecycle of the management and SDDC components in VCF,
including downloading binaries and updating VCF fleet and VCF Instances" [D9.0 §6.1]. The
fleet management appliance owns management-component binaries [D9.0 §6.2].

**How to verify:** VCF Operations `suite-api` version endpoints (`Versions Info` tag is present
in the 9.0 VCF Operations spec). For the fleet management appliance, note that its API in 9.0
uses **HTTP Basic auth** — credential built as
`echo -n 'admin@local:<fleet-admin-password>' | base64`, sent as `Authorization: Basic <b64>`
[DAUTH, Broadcom KB 409715]. There is **no documented token endpoint** for it.

**9.1 difference:** **this appliance does not exist in 9.1.** Its API and its Basic-auth pattern
are 9.0-only. Anything you automate against it will not survive the 9.1 upgrade.

### P4 — Prechecks have been run and are clean `[9.0]`

**Must be true:** prechecks pass before an upgrade is submitted.

**Where the precheck API lives in 9.0 — read carefully.**
- `/v1/system/precheck` was **removed from the SDDC Manager LCM API in 9.0**; the release notes
  state its "functionality moved to VCF Operations" [D9.0 §9.2].
  **Spec check:** the exact path `/v1/system/precheck` is **absent from `SPEC9.0`** — the
  removal is confirmed. See the Discrepancies section for what could *not* be confirmed.
- What SDDC Manager **does** still expose in 9.0, all **spec-confirmed (9.0)**:
  - `POST /v1/upgrades/{upgradeId}/prechecks` + `GET /v1/upgrades/{upgradeId}/prechecks/{precheckId}` (tag `Upgrades`) — upgrade-scoped precheck.
  - `POST /v1/system/check-sets`, `POST /v1/system/check-sets/queries`, `GET /v1/system/check-sets`, `GET|PATCH /v1/system/check-sets/{runId}` (tag `CheckSets`) — the general health/readiness check-set runner.
  - `POST /v1/hosts/prechecks` + `GET /v1/hosts/prechecks/{id}` (tag `Hosts`).
  - `POST /v1/domains/{domainId}/isolation-prechecks` + `GET /v1/domains/{domainId}/isolation-prechecks/{precheckId}` (tag `Domains`).
  - `GET /v1/identity-broker/prechecks` (tag `Identity Provider Precheck`) — **already marked deprecated in the 9.0 spec.**

**How to verify:** run a check-set (`POST /v1/system/check-sets`), poll
`GET /v1/system/check-sets/{runId}` to a terminal state, and read the per-check results before
proceeding.

> **UNVERIFIED.** The individual prechecks are **not enumerated** anywhere in the research — the
> 9.0 LCM page states prechecks exist but does not detail them [D9.0 §11 item 7]. Do not present
> a named list of prechecks as fact.

**9.1 difference:** in 9.1 the SDDC Manager upgrade-precheck pair
(`POST /v1/upgrades/{upgradeId}/prechecks`, `GET .../{precheckId}`) becomes **deprecated**, and a
first-class precheck action appears on fleet lifecycle
(`POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck`). `check-sets` survives and gains
CSV export. See `../9.1/lifecycle.md` P4.

### P5 — Credential and password state is valid `[9.0]`

**Must be true:** no credential used by SDDC Manager for a managed component is expired or
mid-rotation when an upgrade starts, and no credential rotation task is in flight.

**How to verify (all spec-confirmed (9.0)):**
- `GET /v1/credentials` — inventory of managed credentials.
- `POST /v1/credentials/expirations` then `GET /v1/credentials/expirations/{id}` — expiry check.
- `GET /v1/credentials/tasks` and `GET /v1/credentials/tasks/{id}` — confirm no rotate/update
  task is running; `GET /v1/credentials/tasks/{id}/subtasks/{subtaskId}` for detail.
- `GET /v1/sddc-manager/local-os-user-accounts` (tag `SddcManagers`) for appliance-local accounts.

**9.1 difference:** the same credential API exists in 9.1. 9.1 adds
`POST /v1/vcf-management-components/passwords` ("generates a password that will be valid for all
components"). Password *policy* management moves into VCF Operations Fleet Settings in 9.1
[D9.1 §3.5].

### P6 — Authentication to SDDC Manager `[9.0]`

**Must be true:** you hold a valid SDDC Manager bearer token. **SDDC Manager is explicitly
excluded from VCF SSO in both 9.0 and 9.1** — it uses its own token flow, not the identity
broker [DAUTH].

**How to verify / obtain** [D9.0 §3.3]:
- `POST /v1/tokens` with `{"username":"…","password":"…"}` → `{"accessToken":"<JWT>","refreshToken":{"id":"<UUID>"}}`
- `PATCH /v1/tokens/access-token/refresh`, body = refresh-token UUID as `text/plain`
- `DELETE /v1/tokens/refresh-token`
- Access token valid **1 hour**; refresh token **24 hours**. Send `Authorization: Bearer <accessToken>`.

All three are **spec-confirmed (9.0)** (tag `Tokens`).

**9.1 difference:** 9.1 adds OAuth 2.0 via the **VCF Identity Broker (VIDB)** as the unified path
for most components [D9.1 §0.5], and SSO-issued, role-scoped API tokens are a **9.1-only**
capability — 9.0 has no API-client/API-token pages at all [DAUTH]. SDDC Manager's own
`/v1/tokens` flow persists in 9.1.

### P7 — Licensing state `[9.0]`

**Must be true:** licensing is in a state that will not block management operations.
9.0 replaced 25-character keys with subscription license files managed through VCF Operations
and the VCF Business Services console [D9.0 §5.1]. Expiration triggers a **90-day grace period**,
after which management operations become restricted and **hosts disconnect from vCenter**
[D9.0 §5.4]. Usage must be reported at minimum every **180 days** [D9.0 §5.4].

**How to verify:** `GET /v1/license-keys` and `POST /v1/resources/license-checks` →
`GET /v1/resources/license-checks/{id}` (**spec-confirmed (9.0)**), plus the VCF Operations
licensing view.

**9.1 difference:** licences move **out of VCF Operations into a new, required License server**
component [D9.1 §6]. A licence-transfer step exists in the 9.0→9.1 upgrade sequence.

### P8 — Caller role and privilege for lifecycle write operations `[9.0]` — UNVERIFIED

**Must be true:** the account behind the bearer token from P6 holds whatever role is required to
perform lifecycle **write** operations — principally `POST /v1/upgrades` and
`PATCH /v1/upgrades/{upgradeId}`, and also `PATCH /v1/bundles/{id}`,
`PUT /v1/system/settings/depot` and `POST /v1/system/check-sets`.

> **UNVERIFIED. The required role for lifecycle write operations is not documented in the sources
> consulted; verify before delegating credentials.** No retrieved 9.0 page names SDDC Manager role
> names, and no built-in-roles page exists anywhere in the 9.0 fleet-management tree — the page
> that defines VCF built-in roles is **9.1-only**, and its names must not be used for 9.0
> [see `../../../vcf-foundation/references/9.0/auth-and-identity.md` P5]. What the 9.0 SSO
> configuration sequence does say is that roles and permissions are assigned **in the individual
> components**, not centrally — which tells you where to look, not what to ask for. `SPEC9.0`
> declares security *schemes* but no per-operation privilege requirement.
>
> Practical consequences: do not assume a token that can read `GET /v1/upgradables` can also
> submit `POST /v1/upgrades`; do not invent a role name to put in a runbook or a service-account
> request. Confirm against Broadcom's role documentation, or empirically against a non-production
> instance, **before** the account is provisioned.

**9.1 difference:** 9.1 documents VCF-level built-in roles (VCF Administrator, VCF Viewer, SDDC
Administrator, SDDC Viewer), but their published mapping covers vCenter, NSX, VCF Operations, VCF
Automation, HCX and Orchestrator — **not SDDC Manager**, which remains outside VCF SSO. The gap is
therefore open in both versions. See `../9.1/lifecycle.md` P8.

### P9 — Items the research could not verify — state these as gaps, do not fill them in

- **Ports and protocols matrix for 9.0 LCM operations** — not retrieved. The 9.1 upgrade
  prerequisites do say "verify that all required ports are open. See VMware Ports and Protocols"
  [D9.1 §5.2], but the actual matrix was never fetched, in either version.
- **Bundle type taxonomy and depot online/offline payload shape** — explicitly not documented on
  the pages fetched [D9.0 §11 item 6].
- **The enumerated list of prechecks** — not documented [D9.0 §11 item 7].
- **"SDDC Manager Functionality During an Upgrade to VCF 9.0"** — a page with this title was
  found by search but **never fetched** [D9.0 §11 item 13]. What SDDC Manager cannot do
  mid-upgrade is therefore unknown. Treat as a real operational risk, not as "no limitations."
- **9.0 OpenAPI download URL** — no 9.0 spec bundle download link was visible on the Broadcom
  portal [D9.0 §11 item 3]. The 9.0 operation inventory used here comes from the GitHub git tag,
  not the portal.
- **The role required for lifecycle write operations** — not documented for SDDC Manager in 9.0.
  See **P8**.

---

## The LCM surface in 9.0

One control plane, two binary owners.

| Concern | Owner in 9.0 | Reference |
|---|---|---|
| LCM **UI** and orchestration | **VCF Operations** — "Starting with VCF 9, lifecycle management of components occurs through the VCF Operations UI" | D9.0 §6.1 |
| Binaries for VCF **management** components | **VCF Operations fleet management** (standalone appliance) | D9.0 §6.2 |
| Binaries for VCF **core** components, per instance | **SDDC Manager** | D9.0 §6.2 |
| **Programmatic** LCM surface | **SDDC Manager API** (`https://<sddc-manager-fqdn>/v1`) | D9.0 §3.3 |
| ESX image-level lifecycle inside a cluster | **vSphere Lifecycle Manager (vLCM) images** — baselines and baseline groups are **no longer supported** in vCenter 9.0 | D9.0 §9.2; DVS |

**vLCM interaction.** VCF-level lifecycle sits *above* vLCM: VCF Operations / SDDC Manager drive
the domain and cluster upgrade, and vLCM applies the desired ESX image to the cluster. The vLCM
model is: read current cluster state → build a **desired state** (ESX version, partner software,
firmware, add-ons) → validate against hardware → check compliance → apply [DVS]. Managed hosts
must be vSphere 7.0+, stateful, identical hardware from one vendor. Since vSphere 8.0 standalone
hosts are image-managed **only through the vLCM automation API**. Known limitation: you cannot
update host firmware for a standalone host through the VCF API [DVS]. Convergence into 9.0
requires clusters already be on **vLCM images, not baselines** [D9.0 §4.3].

SDDC Manager exposes the VCF-side handles for images: `GET|POST|DELETE /v1/personalities`,
`PUT /v1/personalities/files`, `GET /v1/personalities/{personalityId}`, and
`POST /v1/vcenters/repository-images/queries` → `GET /v1/vcenters/repository-images/queries/{queryId}`
— all **spec-confirmed (9.0)**.

**API size, for reference.** The 9.0 techdocs page claims "about 280 interfaces in the SDDC
Manager API" [D9.0 §3.3]. The machine-extracted 9.0 spec contains **375 operations**. Prefer the
spec count; see Discrepancies.

---

## Bundles, depots, manifests, releases

All **spec-confirmed (9.0)** unless noted.

**Bundles** (tag `Bundles`)
```
GET    /v1/bundles                      list bundles
GET    /v1/bundles/{id}                 bundle detail
PATCH  /v1/bundles/{id}                 trigger/modify download of a bundle
DELETE /v1/bundles/{id}                 remove a downloaded bundle
GET    /v1/bundles/domains/{id}         bundles applicable to a domain
GET    /v1/bundles/download-status      aggregate download state
POST   /v1/bundles                      DEPRECATED already in the 9.0 spec — do not use
```

**Depot settings** (tag `DepotSettings`)
```
GET    /v1/system/settings/depot
PUT    /v1/system/settings/depot
DELETE /v1/system/settings/depot
GET    /v1/system/settings/depot/depot-sync-info
PATCH  /v1/system/settings/depot/depot-sync-info
PATCH  /v1/system/host-bundle-depot            (tag UMDS)
```

**Manifests, releases, catalogs, compatibility**
```
GET  /v1/manifests                                     POST /v1/manifests
GET  /v1/releases                                      GET  /v1/releases/system
GET  /v1/releases/domains                              GET  /v1/releases/domains/{domainId}
PATCH/DELETE /v1/releases/domains/{domainId}           POST /v1/releases/domains/{domainId}/validations
GET  /v1/releases/domains/validations/{validationId}
GET  /v1/releases/domains/{domainId}/future-releases   <- what this domain can move to
GET  /v1/releases/custom-patches                       (tag Flexible Product Patches)
GET  /v1/releases/domains/{domainId}/custom-patches
GET  /v1/releases/{sku}/release-components
GET  /v1/compatibility-matrices   PUT /v1/compatibility-matrices
GET  /v1/compatibility-matrices/{compatibilityMatrixSource}[/content|/metadata]
GET|PATCH|POST /v1/product-version-catalogs
GET  /v1/product-version-catalogs/upload-tasks/{taskId}
POST /v1/product-binaries                              (tag ProductBinaries)
```
`GET|POST /v1/product-version-catalog` (singular) is **deprecated in the 9.0 spec** — use the
plural `product-version-catalogs`.

**Flexible BOM.** 9.0 supports per-component version flexibility rather than strict whole-BOM
lockstep — documented as "flexible BOM upgrade" and backed by the `Flexible Product Patches`
resources above [D9.0 §6.5].

**Version aliases.** `GET|PUT /v1/system/settings/version-aliases` and the
`/{bundleComponentType}[/{version}]` variants are **already deprecated in the 9.0 spec**.

---

## Upgradables and upgrades

```
GET  /v1/system/upgradables                          what the system as a whole can move to
GET  /v1/sddc-manager/upgradables                    SDDC Manager self-upgrade candidates
GET  /v1/upgradables/domains/{domainId}
GET  /v1/upgradables/domains/{domainId}/clusters
GET  /v1/upgradables/domains/{domainId}/nsxt
GET  /v1/upgrades                POST /v1/upgrades                GET /v1/upgrades/preview
GET  /v1/upgrades/{upgradeId}    PATCH /v1/upgrades/{upgradeId}
POST /v1/upgrades/{upgradeId}/prechecks
GET  /v1/upgrades/{upgradeId}/prechecks/{precheckId}
```
All **spec-confirmed (9.0)**.

**The 9.0 execution pattern** [D9.0 §3.4]: validate the spec first, poll the validation, then
submit, then poll the task. Create/update resources are paired with a `validations` sub-resource;
long-running work returns a `Task`.

## Task polling

```
GET    /v1/tasks           GET /v1/tasks/{id}
PATCH  /v1/tasks/{id}      (retry)      DELETE /v1/tasks/{id}   (cancel)
GET    /v1/vcf-management-components/tasks
GET    /v1/vcf-management-components/tasks/latest
GET    /v1/vcf-management-components/tasks/{taskId}
GET    /v1/vcf-management-components/tasks/{taskId}/spec
```
All **spec-confirmed (9.0)**. Domain-scoped async work has its own pollers:
`GET /v1/credentials/tasks/{id}`, `GET /v1/domains/{domainId}/health-checks/tasks/{taskId}`,
`GET /v1/domains/{id}/compliance-audits/tasks/{taskId}`, `GET /v1/config-drift-reconciliations/{taskId}`,
`GET /v1/sddcs/imports/{taskId}`, `GET /v1/restores/tasks/{id}` — all **spec-confirmed (9.0)**.

> The spec's declared `base_path` is the placeholder `http://localhost:80`. The real base is
> `https://<sddc-manager-fqdn>` with the `/v1` (or `/v2`) prefix carried in the path, as shown by
> the API reference's example server `https://sfo-vcf01.rainpole.io/v1` [D9.0 §3.3].

---

## The two upgrade orderings — keep them apart

Conflating these is a known failure mode. They are different sequences for different situations.

### Ordering A — MAJOR upgrade, VCF 5.x → 9.0

Applies when moving a 5.x platform onto 9.0. Supported sources: **VCF 5.0 or later**, sequential
or skip-level; anything older must reach 5.0+ first [D9.0 §4.4]. Management domain upgrade is
**mandatory**; workload domain updates are optional [D9.0 §4.1].

**Core components, via SDDC Manager, in this order** [D9.0 §4.4]:

```
1. SDDC Manager
2. NSX Manager
3. vCenter
4. ESX
```

**Management components** are upgraded manually, or deployed prior to the core upgrade
[D9.0 §4.4]: VCF Operations; VCF Operations fleet management; VCF Operations collector (deploy
*after* the SDDC Manager upgrade for new installations); VCF Automation (deployable as a
post-upgrade task).

Note this ordering has **no explicit vSAN step**.

After the upgrade completes, use **VCF Operations** for lifecycle management — the SDDC Manager
UI is deprecated [D9.0 §4.4].

### Ordering B — MAINTENANCE update within the 9.0.x train (e.g. 9.0.0.0 → 9.0.1.0 → 9.0.2.0)

"When you update your VCF environment to a maintenance release version, for example, from 9.0.0.0
to 9.0.1.0 or 9.0.2.0, you first update your management components." [D9.0 §6.3]

**Step 1 — management components first (fleet level)** [D9.0 §6.3]:
```
1. VCF Operations fleet management appliance
2. VCF Operations instance
3. Remaining components (preferred order)
```

**Step 2 — then core components, in this specified order** [D9.0 §6.3]:
```
1. SDDC Manager
2. NSX
3. vCenter
4. ESX hosts
5. vSAN
```

### The difference, stated plainly

| | Ordering A (major, 5.x → 9.0) | Ordering B (maintenance, 9.0.x → 9.0.y) |
|---|---|---|
| Source | VCF 5.0+ | VCF 9.0.x |
| Management components | manual, or pre-deployed before core | **explicitly first**, fleet management appliance leading |
| Core order | SDDC Manager → NSX Manager → vCenter → ESX | SDDC Manager → NSX → vCenter → ESX → **vSAN** |
| vSAN step | not called out | **explicit final step** |
| Reference | D9.0 §4.4 | D9.0 §6.3 |

Both orderings put **SDDC Manager first among the core components**. That is the one thing they
share; do not let it collapse them into a single remembered sequence.

**9.1 difference:** a third, distinct ordering exists for 9.0.x → 9.1, and it is not either of
these. It also moves **NSX Edge cluster upgrades to the end of the domain upgrade**. See
`../9.1/lifecycle.md` and `../upgrade-runbook.md`.

---

## Prose-vs-spec discrepancies found while writing this file

1. **API size.** Techdocs says "about 280 interfaces in the SDDC Manager API" [D9.0 §3.3];
   `SPEC9.0` contains **375 operations**. The doc prose is stale. Use 375.
2. **`/v1/system/precheck` destination.** The removal from SDDC Manager is spec-confirmed (the
   path is absent from `SPEC9.0`). The claimed destination — "functionality moved to VCF
   Operations" [D9.0 §9.2] — **could not be confirmed against a spec**: no precheck operation
   appears anywhere in the 9.0 VCF Operations spec (`9.0__vcf-operations.ops.json`, base
   `/suite-api`) either. State the removal as fact; state the destination as documentation
   prose, not as a callable endpoint.
3. **Spec base path.** `SPEC9.0` declares `http://localhost:80` as its server. That is a build
   placeholder, not a real base. Use `https://<sddc-manager-fqdn>` + `/v1`.
4. **BOM row drift.** The 9.0.0.0 BOM lists VCF Installer at **9.0.2.0** and the Download Tool at
   **9.0.1.0** — later than the release itself [D9.0 §1.2]. Do not assume "row version == release
   version" for those two rows. The same page also gives the Download Tool 9.0.1.0 two different
   build numbers across the 9.0.0.0 and 9.0.1.0 BOM pages [D9.0 §11 item 5]; unresolved.
5. **Already-deprecated in 9.0.** `POST /v1/bundles`, `GET|POST /v1/product-version-catalog`,
   all `version-aliases` operations, `GET /v1/identity-broker/prechecks`,
   `GET /v1/identity-broker/sddc-manager-oidc`, and
   `POST /v1/nsx-alb-clusters/validations/version` carry `deprecated: true` in `SPEC9.0`. Prose
   sources do not mention this.
