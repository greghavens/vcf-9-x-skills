# VCF 9.0 → 9.1 — Lifecycle Management Delta

Scoped to lifecycle management, bundles/depots, prechecks and upgrades. For the full
cross-product delta see the research dossiers; this file is the lifecycle slice.

**Source keys.** `D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DOPS` = `research/vcf-operations.md`; `DVS` = `research/vsphere-vcenter-vsan.md`;
`DAUTH` = `research/foundation-auth-identity.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of git tags
`9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`);
`SPEC*` = the per-product `.ops.json` inventories in `research/spec-inventory/`.

---

## Two corrections this table exists to enforce

1. **"VCF Fleet Manager" is not a product.** It has never been one. The 9.0 name is
   *VCF Operations fleet management* (an appliance); the 9.1 names are *fleet lifecycle* and
   *SDDC lifecycle* (services). [D9.1 §0.1, §8.3]
2. **SDDC Manager is not gone in 9.1.** Only its **UI** is deprecated. Its API went from
   **375 to 423 operations with zero removed**. [DELTA; D9.1 §0.3, §8.4]

---

## Delta table

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| **Fleet-management appliance** | Standalone appliance with its own BOM row: `VMware Cloud Foundation Operations fleet management 9.0.0.0` (build `24695816`). Owns binaries for VCF management components. Its API uses **HTTP Basic** auth (`admin@local:<password>` base64); no token endpoint documented. | **Eliminated.** "The standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by fleet lifecycle." Replaced by **two** containerized services — **fleet lifecycle** and **SDDC lifecycle** — running natively within VCF Management Services. **No `fleet management` row in the 9.1 BOM.** | 9.0: D9.0 §1.2, §6.2; DAUTH · 9.1: D9.1 §0.2, §2; DOPS |
| **VCF Management Services** | Did not exist. | **New in 9.1**, and "a mandatory, required part of the deployment." A common containerized runtime hosting fleet lifecycle, SDDC lifecycle, software depot, identity broker, log management, real-time metrics (+ store), Salt master, Salt RaaS, telemetry, VCF services runtime. Deployed from VCF Operations → Build > Lifecycle > VCF Instances > SDDC Manager Updates > Install Components. | 9.1: D9.1 §0.4, §5.2, §5.4 · absent from 9.0 BOM: D9.0 §1.2 |
| **SDDC Manager UI** | Already deprecated in 9.0: "With VMware Cloud Foundation 9.0 the SDDC Manager UI is being deprecated. SDDC Manager workflows can now be found in VCF Operations and vSphere Client." | Deprecation restated and sharpened for the upgrade: "The SDDC Manager UI is being deprecated and will be removed in a future release. After your upgrade to VCF 9.1 completes, use VCF Operations to perform lifecycle management activities." **VCF Operations is the LCM UI.** The appliance, service and API are *not* deprecated. | 9.0: D9.0 §3.1 · 9.1: D9.1 §0.3, §8.4 |
| **SDDC Manager API surface** | **375 operations** (spec version `9.0.0.0`). Techdocs prose claims "~280 interfaces" — stale. | **423 operations. 48 added, 0 removed, 21 newly deprecated.** The deprecated 21 are the `/v1/edge-clusters` family, `PATCH /v1/domains/{id}/overlay`, the `/v1/system/dns-configuration` and `/v1/system/ntp-configuration` families, and `POST\|GET /v1/upgrades/{upgradeId}/prechecks[/{precheckId}]`. Prose independently states "21 APIs deprecated" — prose and spec agree exactly. | **DELTA** (machine-computed) · prose: D9.0 §3.3, D9.1 §4 |
| **SDDC Manager in the BOM** | Two separate rows: `SDDC Manager 9.0.0.0 (24703748)` and `VCF Installer 9.0.2.0 (25151285)`. (They were already the same OVA in two modes; the 9.0.2 BOM shows both at build `25151285`.) | **Merged into one row: `VCF Installer/SDDC Manager 9.1.0.0 (25371088)`.** | 9.0: D9.0 §1.2, §1.4, §3.2 · 9.1: D9.1 §2 |
| **Software depot** | Not a component. Binaries split: fleet-management appliance owned management-component binaries; SDDC Manager owned core-component binaries per instance. | **Software depot is a distinct BOM component** (`9.1.0.0`, build `25371105`) that "handles binaries for all VCF components", driven from the VCF Operations UI. "VCF Operations now uses the fleet lifecycle, SDDC lifecycle, and **software depot** components to orchestrate lifecycle operations on both fleet and instance-level components." Deployed by default by the 9.1 Installer. | 9.0: D9.0 §6.2 · 9.1: D9.1 §0.4, §3.4; DOPS; DVS |
| **Licence storage** | Licences stored **in VCF Operations**; no license-server component; subscription licence files replaced 25-character keys in 9.0. | **Licences moved out of VCF Operations into a new License server.** "Licenses are now stored in a license server, instead of in VCF Operations." New **required** component `License server 9.1.0.0 (25346031)`; "at least one license server [per] VCF Operations instance." A licence-transfer step exists in the upgrade sequence. | 9.0: D9.0 §5; D9.1 §2.1 (no row) · 9.1: D9.1 §3.5, §5.2, §6 |
| **Scale per VCF instance** | Baseline (half of 9.1, per the 9.1 statement). | **5000 hosts per VCF Instance — explicitly "2x increase from VCF 9.0"**, and **256 simultaneous cluster upgrades**. Press release: "doubled management capacity to 5,000 hosts", "4x faster cluster upgrades". Reported under the heading **"SDDC Manager Scale"** — i.e. SDDC Manager's capabilities grew. | 9.1: D9.1 §3.5, §1; DOPS |
| **NSX Edge cluster upgrade position** | Edge clusters upgraded earlier within the domain upgrade. | **"NSX Edge clusters are now upgraded at the end of the domain upgrade process."** Corroborated by the NSX What's New: "Move NSX Edge/SVM Upgrades to the End of Upgrade Sequence." | 9.1: D9.1 §3.5, §3.3, delta #10 |
| **Lifecycle-service APIs** | **`fleet-lcm` and `sddc-lcm` do not exist at the 9.0.0.0 tag.** | **Both added in 9.1**: `fleet-lcm` **51 ops** (base path `/fleet-lcm`, title *VCF Fleet LCM Service APIs*, tags incl. Upgrade Plan, Depot Metadata, Release Version, SDDC LCM, Task); `sddc-lcm` **26 ops** (base path `/sddc-lcm`, title *VCF SDDC LCM Service APIs*, tags incl. Components, Depot, Nodes, Task). Both ship as first-class OpenAPI specs in the 9.1 bundle and gain Java/Python SDK coverage. | **DELTA**; `SPEC 9.1__fleet-lcm`, `SPEC 9.1__sddc-lcm` · prose: D9.1 §0.5, §3.7 |
| **Upgrade precheck API** | `POST /v1/upgrades/{upgradeId}/prechecks` + `GET .../{precheckId}` — active, the primary upgrade precheck. `/v1/system/precheck` **already removed in 9.0** ("functionality moved to VCF Operations"); path absent from `SPEC 9.0__sddc-manager`. | Same SDDC Manager pair now **deprecated**. New first-class action: `POST /fleet-lcm/v1/upgrade-plans/{planId}?action=precheck`. `check-sets` survives and gains CSV export (`POST\|GET /v1/system/check-sets/{runId}/exports`, `GET .../exports/data`). `/v1/system/precheck` still absent. | DELTA; SPEC 9.0/9.1 `sddc-manager`, `fleet-lcm` · prose: D9.0 §9.2; D9.1 §3.5 |
| **Upgrade planning primitives** | `GET /v1/upgradables/domains/{domainId}[/clusters\|/nsxt]`, `GET /v1/upgrades/preview`. | Adds `GET /v1/upgradables/domains/{domainId}/upgrade-sequences`, `.../vcenter-sizing-infos`, `.../vcenter-upgrade-mechanisms` (RDU as default), and `GET /v1/version-drift`. Plus the whole `upgrade-plans` resource on fleet lifecycle. | DELTA; SPEC 9.1 `sddc-manager`, `fleet-lcm` |
| **Ops appliance names** | `VCF Operations collector 9.0.0.0 (24695833)`; `VCF Operations for logs 9.0.0.0 (24695810)`. | Collector → **Cloud proxy** (`9.1.0.0`, `25346033`). For-logs → **Log management** (`9.1.0.0`, `25346055`), a VCF Management Services component; upgrade paths from Ops for Logs 8.18 and 9.0. **Spec-level**: `vcf-operations-for-logs` (136 ops) does not exist at the 9.1 tag; `log-management` (23 ops) is new — a rename *and* a large surface reduction. | 9.0: D9.0 §1.2 · 9.1: D9.1 §2, §3.5; DOPS; **DELTA** |
| **Identity broker & OAuth clients** | `VCF Identity Broker 9.0.0.0 (24695128)` standalone. **No API-client / API-token / OAuth-client pages exist in the 9.0 SSO tree at all.** | Identity broker becomes a VCF Management Services component. New **Managing API Clients and Tokens** subtree; OAuth 2.0 via VIDB is the unified auth story. **Migration hazard: "OAuth clients are not migrated automatically. You must manually regenerate the client and secret using identity broker and configure accordingly."** Local accounts, local-account MFA and AD MFA are not supported by the migration. | 9.0: D9.0 §1.2; DAUTH · 9.1: D9.1 §3.5, §0.5; **DAUTH (vIDM→broker migration page)** |
| **SDDC Manager auth** | `POST /v1/tokens` → bearer pair; access 1 h, refresh 24 h. SDDC Manager **excluded from VCF SSO**. | **Unchanged** — the `Tokens` operations are spec-confirmed in 9.1 and SDDC Manager remains excluded from VCF SSO. The VIDB OAuth flow covers the *other* components, not SDDC Manager. | D9.0 §3.3; DAUTH; SPEC 9.0/9.1 `sddc-manager` |
| **Upgrade source versions** | To 9.0: **VCF 5.0 or later**, sequential or skip-level. Management-domain upgrade mandatory; workload-domain updates **optional**. | To 9.1: **VCF 5.2.x or 9.0.x** (also VVF 5.2.x/9.0.x, and a separate vSphere 8 + Aria Ops 8 path). "Requires a strict component upgrade sequence." **Gate: "all workload domains must be at VMware Cloud Foundation 5.2 or later"** — below 5.2, upgrade to 5.2 first. | 9.0: D9.0 §4.4, §4.1 · 9.1: D9.1 §5.1; **DVS** |
| **Who drives the upgrade** | VCF Operations is the LCM UI; SDDC Manager performs core-component upgrades. | **Split at order 6.** SDDC Manager drives orders 0–6 (identity-broker network transition, VCF Operations + cloud proxy, its own self-upgrade); VCF Operations drives orders 6–23 (VCF Management Services + License Server deployment, licence transfer, identity broker, VCF Automation, then NSX/vCenter/ESX/vSAN/Tools). | 9.0: D9.0 §6.1 · 9.1: D9.1 §5.3 |
| **vCLS in LCM UIs** | Available; manageable from SDDC Manager and VCF Installer UIs. | "All vCLS functionalities available in SDDC Manager UI and VCF Installer UI are **removed**"; vCLS is "deactivated by default and you cannot re-activate the capability." | 9.1: D9.1 §4 |
| **Out-of-band vCenter changes** | Out-of-band changes disruptive to SDDC Manager. | Tasks performable in vCenter "without impacting SDDC Manager" (VDS changes, datastore modifications, manual component upgrades); "Out-of-band networking changes to not impact SDDC Manager". New remediation API: `POST /v1/clusters/{clusterId}/remediations` → `GET .../remediations/{remediationId}`. | 9.1: D9.1 §3.4, §3.3; DELTA |
| **Domain upgrade behaviour** | Baseline. | Optimised NSX Manager and vCenter maintenance windows; reduced-downtime update preparation; support for imported standalone hosts and single-host clusters; **ability to select specific hosts during cluster upgrades**; improved prechecks using native VCF component capabilities; Component Versions tab showing current and target versions. | 9.1: D9.1 §3.5 |
| **HCX lifecycle** | HCX in the BOM; no LCM through VCF Operations. | **HCX Manager deployment and upgrade via VCF Operations**; SDDC Manager gains an HCX manager API family (`GET\|POST\|DELETE /v1/domains/{domainId}/hcx-managers[...]`, `.../versions`, `.../validations/{validationId}`) — all new in 9.1. | 9.1: D9.1 §3.5; DELTA |
| **vLCM relationship** | vLCM **images** only for cluster management (baselines/baseline groups no longer supported in vCenter 9.0). Convergence requires images, not baselines. | Images-only model continues; VCF Operations "can manage ESX components and vSphere Lifecycle Manager images." Adds global remediation settings for Configuration Profile clusters, image integrity validation for customised ESX images, optimised VIB transfer. A dedicated baselines→images transition topic exists. | 9.0: D9.0 §9.2, §4.3; DVS · 9.1: D9.1 §3.1; DVS |
| **Workload-domain creation constraint** | A workload domain required an initial vSphere cluster. | New workflow deploys **vCenter and NSX Manager without an initial cluster** — but **patching and upgrades are blocked until a cluster is added**. A lifecycle-relevant trap. | 9.1: D9.1 §3.4, delta #25 |
| **Installer default deployment** | Installer did not deploy management services. | "VCF 9.1 deploys standardized management services components by default, including runtime, fleet lifecycle, identity broker, and software depot." | 9.1: D9.1 §3.4 |
| **VCF Operations API surface** | 370 ops (base `/suite-api`). | **504 ops. 134 added, 0 removed.** New trees include `/suite-api/api/fleet-management/{iam,certificate-management,password-management}/...`, `/suite-api/api/salt/...`, and Findings. | **DELTA**; DOPS |
| **VCF Installer API** | 52 ops. | **57 ops. 5 added, 0 removed, 0 deprecated.** Additions include `POST /v1/sddcs/resources-calculation`, `POST /v1/sddcs/sddcm-discovery`, `GET /v1/system/settings/depot/machine-details`. | **DELTA** |
| **Hybrid Linked Mode (`/hvc/*`) on vCenter** | Present in `vsphere-automation` (1275 ops): the nine-operation `/hvc/links` and `/hvc/management/administrators` tree. | **Removed.** `vsphere-automation` grows to 1367 ops (101 added, 28 newly deprecated) but the **only 9 operations removed are the entire `/hvc/*` tree** — an upgrade-impacting capability withdrawal, not an API tidy-up. See the section below. | **DELTA** (machine-computed) |

---

## Removed capability: Hybrid Linked Mode (`/hvc/*`) `[upgrade-impacting]`

**Nine operations were removed from `vsphere-automation` between the `9.0.0.0` and `9.1.0.0` tags,
and they are all of `/hvc/*`.** Verbatim from `DELTA` (§`vsphere-automation` → *Removed in 9.1*):

```
DELETE /hvc/links/{link}                          Vcenter.Hvc.Links_delete
GET    /hvc/links                                 Vcenter.Hvc.Links_list
GET    /hvc/links/{link}                          Vcenter.Hvc.Links_get
GET    /hvc/management/administrators             Vcenter.Hvc.Management.Administrators_get
POST   /hvc/links                                 Vcenter.Hvc.Links_create
POST   /hvc/links/{link}?action=delete            Vcenter.Hvc.Links_deleteWithCredentials
POST   /hvc/management/administrators?action=add  Vcenter.Hvc.Management.Administrators_add
POST   /hvc/management/administrators?action=remove Vcenter.Hvc.Management.Administrators_remove
PUT    /hvc/management/administrators             Vcenter.Hvc.Management.Administrators_set
```

Of the seven products present at **both** tags, only two remove anything at all:
`vsphere-automation` (**9**, all `/hvc/*`) and `vcf-operations-for-networks` (**1**,
`GET /migration/{groupType}`). `sddc-manager`, `vcf-operations`, `vcf-installer`,
`vsphere-vi-json` and `vsan-data-protection` all removed **zero**. That makes `/hvc/*` the largest
hard API breakage in the 9.0 → 9.1 delta. [DELTA]

**Why it belongs in a lifecycle file.** This is a whole capability withdrawn, not a deprecation
with a grace period. Anyone using **Hybrid Linked Mode** — linking an on-premises vCenter SSO
domain to a cloud vCenter, and the HLM administrator group that goes with it — must establish a
replacement **before** upgrading, because after the upgrade the API to create, list, delete or
administer those links is simply gone. Automation that calls `/hvc/links` will start returning 404
and there is no renamed successor path in the 9.1 spec.

> **What the spec does *not* tell you, and no retrieved prose page covered:**
> - whether **existing** HLM links keep functioning after the upgrade, or are torn down;
> - whether a replacement mechanism (a different API, a UI-only flow, or a different product
>   feature) exists in 9.1;
> - whether the upgrade **pre-checks for** or **blocks on** the presence of HLM links.
>
> `UNVERIFIED` on all three. The removal itself is machine-confirmed from the two tags; the
> operational consequence is inferred from the removal and must be confirmed against Broadcom's
> 9.1 vCenter documentation and release notes before you upgrade an instance that uses HLM.

---

## What did *not* change

- **SDDC Manager's core LCM API shape.** Bundles, depot settings, manifests, releases,
  compatibility matrices, personalities, repository images, upgradables, upgrades, credentials
  and tasks all exist in both versions with identical paths. Zero removals. [DELTA]
- **SDDC Manager auth.** `POST /v1/tokens` bearer pair, 1 h / 24 h, and exclusion from VCF SSO.
  [D9.0 §3.3; DAUTH]
- **The validate-then-execute-then-poll pattern.** Create/update paired with a `validations`
  sub-resource; long-running work returns a task. [D9.0 §3.4]
- **The stale-slug hazard in Broadcom's doc tree.** 9.1 pages still carry 5.2-era slugs
  (`upgrade-workload-domains-to-vcf-5-2.html`,
  `upgrade-the-management-domain-to-vmware-cloud-foundation-5-2.html`,
  `opnapi-for-sddc-manager.html` — note the typo). Fetch the guide landing page and read its
  children; never guess a deep slug. [D9.0 §7.1; D9.1 §9.4]

## Deltas the research could NOT establish

- **Bundle-type taxonomy and depot online/offline configuration payloads** — undocumented on
  every page fetched, in both versions [D9.0 §11 item 6]. So the *delta* here is also unknown.
- **Ports and protocols matrix** — required by the 9.1 prerequisites, never retrieved.
- **Enumerated precheck list** — not documented in either version [D9.0 §11 item 7].
- **Upgrade orders 2–5 and 9–23 of the 9.0.x → 9.1 sequence, individually** — collapsed into
  ranges on the retrieved page [D9.1 §8.7].
- **Fate of the 9.0 appliances after the 9.1 upgrade** — whether the fleet-management, collector
  and for-logs appliances are auto-removed, left powered off, or need manual cleanup is unknown
  [D9.1 §8.8].
- **Whether existing Hybrid Linked Mode links survive the upgrade, and what replaces `/hvc/*`** —
  the removal of the nine operations is machine-confirmed; the operational consequence is not
  documented on any page retrieved. See the `/hvc/*` section above.
- **9.0 baseline for max hosts per instance** — 9.1 says "2x increase from VCF 9.0", implying
  2500, but no 9.0 page stating the number was retrieved. Do not assert 2500 as sourced.
