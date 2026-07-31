# VCF 9.1 — VCF Installer and Management-Domain Bring-Up Reference

**Scope:** VMware Cloud Foundation 9.1.0.0 (released 12 MAY 2026), greenfield bring-up and
convergence of existing vSphere infrastructure. Everything here is `[9.1]` unless tagged otherwise.

**Sources.** `D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DAUTH` = `research/foundation-auth-identity.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md`.
`SPECI9.1` = `research/spec-inventory/9.1__vcf-installer.ops.json` — **57 operations**, spec version
`9.1.0.0`, title *VMware Cloud Foundation Installer API Reference Guide*, from git tag `9.1.0.0` of
`github.com/vmware/vcf-api-specs`.
`RAW9.1` = `/tmp/vcf-api-specs/specifications/vcf-installer/vcf-installer-openapi.json` at that tag,
read for request/response schemas. `RAW9.0` = the same file at tag `9.0.0.0`, for comparison.

**Every endpoint below was checked against `SPECI9.1`** and is marked **spec-confirmed (9.1)** with
its `operationId`, or flagged.

---

## Read this first — one appliance, one BOM row

**Cloud Builder does not exist.** It was removed in 9.0 and replaced by the **VCF Installer**
appliance [D9.0 §9.2]. The Installer ships inside **`VCF-SDDC-Manager-Appliance-9.x.x.ova`** — it
*is* the SDDC Manager appliance, in a different mode [D9.0 §3.2].

**9.1 stops pretending they are two products.** The 9.1 BOM merges them into a single row:

> **`VCF Installer/SDDC Manager  9.1.0.0  build 25371088`** [D9.1 §2]

In 9.0 these were two rows — `VCF Installer 9.0.2.0 (25151285)` and `SDDC Manager 9.0.0.0
(24703748)` — though even then the 9.0.2.0 BOM showed both at build `25151285` [D9.1 §0.3;
D9.0 §1.4].

**The mode switch is still one-way.** Deploy the appliance **inside** the management infrastructure
and it "switches into SDDC Manager mode and **can no longer be used in installer mode**"
[D9.0 §3.2]. Deployed outside, it can build multiple platforms. Nothing in the 9.1 research
contradicts or softens this. Decide before you power it on.

**What 9.1 adds to the bring-up itself:** *"VCF 9.1 deploys standardized management services
components **by default**, including runtime, fleet lifecycle, identity broker, and software
depot"* [D9.1 §3.4]. That is visible in the spec — `SddcSpec` gains `fleetLcmSpec`, `sddcLcmSpec`,
`fleetDepotSpec`, `vidbSpec`, `saltSpec`, `saltRaasSpec`, `telemetryAcceptorSpec`,
`licenseServerSpec`, `vspClusterSpec` and `vcfManagementComponentsInfrastructureSpec`, and **loses**
`vcfOperationsFleetManagementSpec` entirely [RAW9.0 vs RAW9.1].

---

## Contents

- [Read this first](#read-this-first--one-appliance-one-bom-row)
- [Prerequisites](#prerequisites)
  - P0 — Authentication to the VCF Installer API — **UNVERIFIED, read in full**
  - P1 — Appliance identity and mode (one-way switch)
  - P2 — DNS, FQDNs and the subdomain
  - P3 — NTP
  - P4 — Network readiness (incl. dual-stack and the fleet-management network)
  - P5 — ESX host state
  - P6 — Binaries and depot
  - P7 — Licensing — the License server is now something you deploy
  - P8 — Convergence gates (importing existing infrastructure) — widened in 9.1
  - P9 — Capacity: size the deployment before you submit it (9.1-only)
  - P10 — Items the research could not verify
- [The 9.1 Installer API surface — 57 operations](#the-91-installer-api-surface--57-operations)
- [The bring-up workflow](#the-bring-up-workflow--calculate--validate--deploy--poll--retry)
- [The SddcSpec payload in 9.1](#the-sddcspec-payload-in-91)
- [Convergence — reusing existing components](#convergence--reusing-existing-components)
- [Task and validation polling](#task-and-validation-polling)
- [What the Installer does not do](#what-the-installer-does-not-do)
- [Prose-vs-spec observations](#prose-vs-spec-observations)

---

## Prerequisites

Bring-up is the one VCF operation where the prerequisites *are* the work. A failed `deploySddc`
against half-ready infrastructure leaves partially built appliances behind, and the documented
recovery is retry (`retrySddc`), not rollback. Each item states what must be true, **how to verify
it**, the version, and whether 9.0 differs.

### P0 — Authentication to the VCF Installer API `[9.1]` — **UNVERIFIED**

**Same gap as 9.0, unchanged. It is the first blocking prerequisite, not a footnote.**

**What the spec establishes (spec-confirmed (9.1)):** a `Tokens` tag with three operations,
identical in path, method and `operationId` to 9.0:

```
POST   /v1/tokens                        createToken            body TokenCreationSpec -> 201 TokenPair
PATCH  /v1/tokens/access-token/refresh   refreshAccessToken     body: JSON string (refresh token id) -> 200
DELETE /v1/tokens/refresh-token          invalidateRefreshToken body: JSON string (refresh token id) -> 204
```
`TokenCreationSpec` = `username`, `password`, `apiKey`, `idToken` (none marked required).
`TokenPair` = `accessToken` ("Bearer token that can be used to make public API calls") +
`refreshToken.id`.

**What the spec does NOT establish — checked directly against `RAW9.1`:**
- `components.securitySchemes` is **absent**; `components` contains only `schemas`.
- No top-level `security` block; **zero operations declare `security`**.
- Nothing states the header name, the token lifetimes, or that any operation requires a token.

**What the documentation research established:** nothing for either version. The auth matrix in
`DAUTH` contains rows for SDDC Manager, VCF Identity Broker, vCenter, NSX, VCF Operations, the 9.0
fleet-management API, VCF Automation, vSAN and Supervisor — and **no VCF Installer row at all**.
`D9.0 §11 item 2` records it verbatim: *"VCF Installer API base URL and token endpoints not
confirmed … I therefore **cannot assert** that VCF Installer auth is identical to SDDC Manager
auth."* — `UNVERIFIED — could not retrieve`.

> **Two wrong shortcuts, both tempting in 9.1:**
>
> 1. **"It's the same appliance as SDDC Manager, so use SDDC Manager's flow."** The paths match,
>    which is expected. But SDDC Manager's documented flow — `Authorization: Bearer <accessToken>`,
>    1 h access / 24 h refresh, refresh body **`text/plain`** [D9.0 §3.3] — is documented *for SDDC
>    Manager*, and the Installer spec declares its refresh and invalidate bodies as
>    **`application/json`**. That is a concrete divergence, and it fails at the first call.
> 2. **"9.1 unified everything on OAuth via the identity broker, so use a VIDB token."** 9.1 does
>    introduce OAuth 2.0 via VCF Identity Broker for "most VCF components" [D9.1 §0.5] — but the
>    same page warns *"not all VCF components employ identical token authentication methods"*, and
>    **SDDC Manager and ESX are explicitly excluded from VCF SSO in both versions** [DAUTH]. Since
>    the Installer is the SDDC Manager appliance, assuming a VIDB token works here is unsupported.
>
> **Close this before the change window** by reading the live spec off the appliance, or the
> Installer API reference at `developer.broadcom.com/xapis/vcf-installer-api/latest/tokens/`
> (URL from [D9.0 §8.1]; not fetched in this research).

**How to verify (once you have a credential):** `GET /v1/system/appliance-info`
(`getApplianceInfo`, **spec-confirmed (9.1)**) — in 9.1 it also answers most of P1, P2 and P3 at
once.

**9.0 difference:** none. The gap is open identically in both versions [see `../9.0/bringup.md` P0].

**For all other VCF auth** — SSO, identity broker, API clients and tokens, roles, TLS trust — use
the `vcf-foundation` skill. Do not restate it here.

### P1 — Appliance identity and mode `[9.1]`

**Must be true:** the appliance is still in **installer** mode and sits where you intend.

**How to verify (both spec-confirmed (9.1)):**
```
GET  /v1/system/appliance-info    getApplianceInfo
     -> ApplianceInfo { role, version, dnsDomain, dnsServers, ntpServers, ipAddresses }
POST /v1/sddcs/installer-mode     getInstallerType
     body SddcInstallerRequest { endpoints[] (SddcHostSpec), subdomain }  — both required
     -> InstallerSpec { applianceFqdn, type }   type ∈ Internal | External | "Internal, External"
```
`getInstallerType` probes the ESXi/vCenter endpoints you give it "in which the appliance will check
for itself" [RAW9.1] — the literal "am I inside the infrastructure I am about to build?" question.
Run it before `deploySddc`.

**9.0 difference:** both operations exist in 9.0, but `ApplianceInfo` there has **only** `role` and
`version` [RAW9.0]. The DNS/NTP/IP self-report is a 9.1 gain and makes P2/P3 verifiable from the
appliance itself.

### P2 — DNS, FQDNs and the subdomain `[9.1]`

**Must be true:** name resolution exists for every appliance and host named in the spec, and the
names conform.

**What the spec requires** [RAW9.1], unchanged from 9.0 except where noted:
- `dnsSpec` **required** in `SddcSpec`; `dnsSpec.subdomain` **required** — "Includes the full domain
  suffix". `nameservers`: "The first is the primary nameserver. **Maximum allowed is two entries.**"
- `SddcHostSpec.hostname` — "will be **prefixed to the DNS subdomain name** and should **not**
  include the domain name itself. Must also adhere to **RFC 1123**."
- `sddcId` — management domain name, 3–20 chars, `[A-Za-z0-9-]`.
- `vcfInstanceName` — **"Minimum length 1"** in 9.1, versus "Minumum length 3" in 9.0 [RAW9.0 vs
  RAW9.1]. A minor relaxation, and the 9.0 text carries a typo.
- Component FQDNs: `sddcManagerSpec.hostname`, `vcenterSpec.vcenterHostname`, `nsxtSpec.vipFqdn`,
  `vidbSpec.hostname`, `licenseServerSpec.hostname`, and **`vspClusterSpec`** which requires
  **three** FQDNs — `instanceFqdn`, `platformFqdn` (both required) and `fleetFqdn` ("should be
  provided in VVF and primary VCF instance. If building a secondary VCF instance, do not provide").

**Certificates.** 9.1 documents a prerequisite with no 9.0 counterpart, for VCF Management Services:
*"Verify that your certificates are configured and use the proper Fully Qualified Domain Name
(FQDN)"* [D9.1 §5.2]. On the Installer, the trust-store hooks are
`GET|POST /v1/sddc-manager/trusted-certificates` and
`DELETE /v1/sddc-manager/trusted-certificates/{alias}` (**spec-confirmed (9.1)**).

**How to verify:** resolve every name forward and reverse, then `POST /v1/sddcs/validations`
(`validateSddcSpec`) and read `validationChecks[]`.

> **UNVERIFIED.** No retrieved page states the DNS **record checklist** — forward/reverse per
> appliance, whether PTR is mandatory, which component checks which. The field requirements above
> are spec-confirmed; the zone checklist is not.

**9.0 difference:** field semantics identical apart from `vcfInstanceName` and the additional 9.1
component FQDNs listed above.

### P3 — NTP `[9.1]`

**Must be true:** reachable NTP servers — every management appliance is configured from one list.

**What the spec provides:** `SddcSpec.ntpServers` — "List of NTP servers to be used for configuring
**Management Appliances**". Not in the `required` set (`dnsSpec`, `networkSpecs`, `sddcId`,
`vcenterSpec` are).

**How to verify:** `GET /v1/system/appliance-info` reports the Installer's own `ntpServers` in 9.1;
`POST /v1/sddcs/validations` covers the target estate.

> **UNVERIFIED.** Required server count, skew tolerance, and behaviour when `ntpServers` is omitted
> are **not documented in any retrieved source**.

**9.0 difference:** same field; 9.0's `ApplianceInfo` cannot report NTP.

### P4 — Network readiness `[9.1]`

**Must be true:** every VLAN, subnet, gateway and uplink named in `networkSpecs` exists and works.
`networkSpecs` is **required**.

**`SddcNetworkSpec` in 9.1** — `networkType` and `vlanId` required:
- `networkType` — "One among: VSAN, VMOTION, MANAGEMENT, VM_MANAGEMENT, NFS, **`FLEET_MANAGEMENT`**
  or any custom network type". `FLEET_MANAGEMENT` is **new in 9.1** [RAW9.0 vs RAW9.1] and is the
  network the fleet-level management services sit on.
- **`ipAddressVersion`** — "One among: **IPv4, IPv6**" — **new in 9.1**.
- **`ipAddressAssignmentMode`** — "One among: **STATIC, DHCP, SLAAC**" — **new in 9.1**. These two
  are the spec-side of the documented *"dual-stack IPv4/IPv6"* support [D9.1 §3.4].
- Carried over: `gateway`, `subnet`, `subnetMask`, `mtu`, `portGroupKey`, `includeIpAddress`,
  `includeIpAddressRanges`, `teamingPolicy`, `activeUplinks`, `standbyUplinks`.
- `dvsSpecs` is unchanged from 9.0 (`dvsName`, `networks`, `mtu`, `nsxtSwitchConfig`,
  `vmnicsToUplinks`, `nsxTeamings`, `lagSpecs`); 9.1 documents **native UI LACP configuration on
  VDS** [D9.1 §3.4] which maps to the existing `lagSpecs`.
- **`vcfManagementComponentsInfrastructureSpec`** — **new in 9.1** — carries `localRegionNetwork`
  and `xRegionNetwork`, each a `VcfManagementComponentsNetworkSpec` requiring `networkName`,
  `gateway` and `subnetMask`, with optional `ipv6Gateway` / `ipv6Prefix`. This is where the
  management-services placement network is declared, and it has no 9.0 equivalent.
- **`skipGatewayPingValidation`** still exists — gateway reachability **is** validated by default.
  Skipping it suppresses a real check.

**Discovery helpers (spec-confirmed (9.1)):**
```
POST /v1/sddcs/network-config-profiles   getNetworkConfigProfiles
     body { storageType, hostSpecs, subdomain, nsxConfigType, additionalPortGroups }  <- additionalPortGroups new in 9.1
     -> { commonPhysicalNics, profiles }
POST /v1/sddcs/vcenter-discovery/networks  discoverVcenterNetworks     <- NEW IN 9.1
     body VcenterNetworkDiscoverySpec { endpoint (VcenterDiscoverySpec, required), name, page, size }
     -> PageOfVcenterNetworkInfo
```
`discoverVcenterNetworks` is one of the five 9.1 additions [DELTA] and exists precisely so a
convergence run can enumerate the existing vCenter's port groups instead of you transcribing them.

> **UNVERIFIED — the ports and protocols matrix.** The 9.1 prerequisites say *"Verify that all
> required ports are open. See VMware Ports and Protocols"* [D9.1 §5.2], and that matrix
> (`https://ports.broadcom.com/`) **renders client-side and exposes no static table**; it was never
> retrieved in any version of this research, and VCF 9.x coverage could not be confirmed
> [DAUTH §4]. **Network requirements are therefore NOT fully documented here.** Do not produce a
> port list and do not sign off a bring-up plan as network-complete on the basis of this file.
>
> The outbound side *is* verified `[9.1]` (all HTTPS/443) [DAUTH §4]: `dl.broadcom.com` (component
> binaries), `projects.packages.broadcom.com` (Supervisor and VCF services binaries — software
> depot), `vvs.broadcom.com` (compatibility data for VCF Installer, SDDC Manager, download tools),
> `vsanhealth.vmware.com` (vSAN HCL), `vcsa.vmware.com` (CEIP), `eapi.broadcom.com` and
> `vcf.broadcom.com` (VCF Operations licensing), `auth.esp.vmware.com` (UMDS).

**9.0 difference:** no `FLEET_MANAGEMENT` network type, no IP-version or assignment-mode fields, no
`vcfManagementComponentsInfrastructureSpec`, no `additionalPortGroups`, no network-discovery
endpoint. See `../deltas.md`.

### P5 — ESX host state `[9.1]`

**Must be true:** ESX is installed and each host is in the expected state.

- `SddcSpec.hostSpecs` — "List of ESXi to be added to the **Management Cluster**". `SddcHostSpec` is
  **byte-identical to 9.0**: `hostname` required (RFC 1123, no domain suffix), `credentials`
  (`password` required), `sslThumbprint` (SHA256), `sshThumbprint` ("RSA SHA256 in new deployment
  scenario **or** ESX host SSH key (RSA, ECDSA) in reuse existing deployment scenario") [RAW9.1].
- `skipEsxThumbprintValidation` — "Applies to **both** converting an existing environment and
  deploying a new one". Disables a real check.
- **Host counts and compute rules** come from the convergence prerequisites, which the research
  captured for 9.0 [D9.0 §4.3]: minimum **3 ESX hosts (vSAN)** or **2 (external storage)** for
  simple deployments; shared datastores writable across all cluster hosts; **fully automated DRS**;
  **vLCM images, not baselines**. **No 9.1-scoped restatement of these numbers was retrieved** —
  treat them as `[9.0]`-sourced and confirm against the 9.1 convergence page before quoting them for
  9.1. `UNVERIFIED for 9.1`.
- 9.1 platform-level host changes worth knowing but **not** Installer API surface: ESX **Zero Touch
  Provisioning** via UEFI/HTTPS network boot [D9.1 §3.1], and **vCLS "deactivated by default and you
  cannot re-activate the capability"** with *"all vCLS functionalities available in SDDC Manager UI
  and VCF Installer UI removed"* [D9.1 §4].

**How to verify:** thumbprints out of band, then `POST /v1/sddcs/validations`;
`POST /v1/sddcs/network-config-profiles` reports the hosts' common physical NICs.

**9.0 difference:** none in the host spec itself.

### P6 — Binaries and depot `[9.1]`

**Must be true:** the Installer can obtain binaries for the target release.

**How to verify (all spec-confirmed (9.1), on the Installer):**
```
GET    /v1/system/settings/depot                    getDepotSettings
PUT    /v1/system/settings/depot                    updateDepotSettings
DELETE /v1/system/settings/depot                    deleteDepotSettings        (?depotType)
GET    /v1/system/settings/depot/depot-sync-info    getDepotSyncInfo
PATCH  /v1/system/settings/depot/depot-sync-info    syncDepotMetadata
GET    /v1/system/settings/depot/machine-details    getMachineDetails          <- NEW IN 9.1 (-> { machineId })
GET    /v1/bundles                                  getBundles                 (?productType, ?bundleType, ?isCompliant)
GET    /v1/bundles/download-status                  getBundleDownloadStatus    (?releaseVersion, ?bundleId, ?imageType=INSTALL|PATCH)
GET    /v1/bundles/{id} | PATCH /v1/bundles/{id} | DELETE /v1/bundles/{id}
GET    /v1/releases | GET /v1/releases/system | GET /v1/releases/{sku}/release-components
GET    /v1/releases/custom-patches | GET /v1/releases/domains/{domainId}/custom-patches
GET    /v1/system/proxy-configuration | PATCH /v1/system/proxy-configuration
```
`POST /v1/bundles` (`uploadBundle`) is **`deprecated: true`** in both versions —
*"[Unsupported] Upload a bundle to SDDC Manager or VCF Installer"*. Do not build an offline path on
it.

**Release-type limitation** [D9.0 §4.2, stated for the Installer and not contradicted by any 9.1
source]: major, minor and maintenance releases are supported; **express patch releases are NOT**,
and must be applied manually after the workflows complete.

Air-gapped staging uses the **VCF Download Tool** CLI (UMDS folded into it) [D9.0 §6.2, §9.1]; VCF
Download Tool remains a 9.1 BOM row [D9.1 §2].

> **UNVERIFIED.** Bundle-type taxonomy and the online/offline depot payload shapes are undocumented
> on every page fetched, in both versions [D9.0 §11 item 6]. `bundleType` / `productType` exist as
> query parameters; their enumerations do not appear in any retrieved source.

**9.0 difference:** identical minus `machine-details`.

### P7 — Licensing — the License server is now something you deploy `[9.1]`

**Must be true:** a **License server** exists, because 9.1 made it a component of the platform.

- *"Licenses are now stored in a **license server**, instead of in VCF Operations"* [D9.1 §3.5].
- *"You must add at least one license server to each VCF Operations instance that you use for
  license management"* [D9.1 §6]; it is a **required component** [D9.1 §5.2] with its own BOM row
  (`License server 9.1.0.0`, build `25346031`) and **no 9.0 counterpart** [D9.1 §2].
- **Spec confirmation:** `SddcSpec.licenseServerSpec` exists in 9.1 and **does not exist in 9.0** —
  a search of every schema property in `RAW9.0` for `licen*` returns **zero hits**; in `RAW9.1` it
  returns exactly one, `SddcSpec.licenseServerSpec`. Schema: `hostname` **required**, plus
  `useExistingDeployment`, `version`, `sslThumbprint`.
- Licence *assignment* is still out of band: primary licence to a **vCenter instance**, connected
  assets including ESX hosts licensed automatically [D9.0 §5.3], managed through VCF Operations and
  the VCF Business Services console.

**How to verify:** populate `licenseServerSpec` (or set `useExistingDeployment` with an
`sslThumbprint` if one already exists) and let `validateSddcSpec` check it.

**9.0 difference:** no licence field at all in the 9.0 `SddcSpec`; licensing is entirely post-
deployment. See `../9.0/bringup.md` P7.

### P8 — Convergence gates (importing existing infrastructure) `[9.1]`

Convergence means using existing virtual infrastructure "as building blocks" [D9.0 §4.3]. **9.1
widens the supported matrix substantially.**

**Supported convergence sources in 9.1, verbatim scope** [D9.1 §3.4]:
- existing **vCenter 8.0 U2a+ with NSX Manager 4.1.2.1+**
- **vCenter 8.0 U2a without NSX** (requires **manual vCenter upgrade to 9.1**)
- vCenter with existing **NSX Federation**
- **dual-stack IPv4/IPv6** environments

Compare 9.0, where the gate was far tighter: **VCF 9.0.0 supported only a *new* NSX 9.0 deployment
during convergence — existing NSX instances were unsupported** — and only **9.0.1 and later**
allowed existing NSX instances, and then only **without Enhanced Linked Mode** [D9.0 §4.3].

**Still applicable from the 9.0 documentation (no 9.1 restatement retrieved):**
- **Scope rule:** convergence applies to your **management domain only**; workload domains are
  imported and upgraded **in VCF Operations, after** the management domain is deployed [D9.0 §4.3].
- **Three phases:** meet requirements → **manually upgrade components** → run the Installer-driven
  deployment [D9.0 §4.3]. Phase 2 is manual and dominates the timeline.
- **Unsupported:** Dell VxRail-managed clusters; vCenter with **Enhanced Linked Mode**; Cisco
  virtual switches; dynamically allocated VMkernel IPs [D9.0 §4.3]. `UNVERIFIED for 9.1` — no 9.1
  page restating this list was retrieved, and the ELM entry is in tension with 9.1's documented
  support for NSX Federation, so confirm before relying on it.
- **Bare Metal Edge support in VCF import** and *"out-of-band networking changes to not impact SDDC
  Manager"* are 9.1 additions [D9.1 §3.3, §3.4].

**How to verify:** the discovery endpoints below, then `validateSddcSpec`. Discovery tells you what
the Installer can see; it does **not** tell you the topology is supported.

**9.0 difference:** see `../9.0/bringup.md` P8 and `../deltas.md` — this is the largest functional
delta in the Installer between the two versions.

### P9 — Capacity: size the deployment before you submit it `[9.1 only]`

**New in 9.1**, and the single most useful prerequisite addition [DELTA]:
```
POST /v1/sddcs/resources-calculation        resourcesCalculation
     body SddcSpec  -> 202 CapacityValidation
GET  /v1/sddcs/resources-calculation/{id}   getResourcesCalculation -> CapacityValidation
```
Both **spec-confirmed (9.1)**. `CapacityValidation` extends the ordinary `Validation` shape
(`id`, `description`, `executionStatus`, `resultStatus`, `validationChecks[]`) with
**`requiredCapacity`** and **`availableCapacity`**, each a `CapacityInfo`:

```
CapacityInfo { numberOfEsxiHosts, numberOfCores, memory, storage, context,
               componentsVmRequirements[] }
ComponentVmRequirement { component, componentType, cpuCores, memoryGb, storageGb,
                         workersCount, ipCount, ipCountRecommended, ipCountLimit }
```

That gives you a per-component CPU/memory/storage **and IP-address-count** requirement before you
commit hosts — including `ipCountRecommended` and `ipCountLimit`, which is exactly the number people
under-provision when sizing management networks. Run it as a gate. Once the appliance has flipped
into SDDC Manager mode, the equivalent is `POST /v1/vcf-management-components/resources-calculation`
on the **SDDC Manager** API (`resourcesCalculation`, spec-confirmed in `9.1__sddc-manager.ops.json`,
also new in 9.1) [DELTA] — a different spec, not this one.

This matches the documented 9.1 Installer feature *"integrated planning workflow with resource
validation"* [D9.1 §3.4].

**9.0 difference:** **does not exist.** In 9.0 there is no resources-calculation API and the Design
and Planning-and-Preparation guides were not fetched by the research [D9.0 §11 item 9], so 9.0
sizing has no documented programmatic gate here.

### P10 — Items the research could not verify — state these as gaps

- **VCF Installer authentication** — header format, token lifetimes, refresh content type. **No
  `securitySchemes` in either spec; no Installer row in the auth research** [D9.0 §11 item 2;
  DAUTH]. **See P0. Blocking.**
- **Ports and protocols matrix** — never retrieved, either version [DAUTH §4; D9.1 §5.2 names the
  requirement]. **See P4.**
- **DNS record checklist** — not on any retrieved page. **See P2.**
- **NTP server count / skew tolerance** — not documented. **See P3.**
- **Bundle-type taxonomy and depot payload shapes** — explicitly undocumented [D9.0 §11 item 6].
- **The enumerated validation checks** run by `validateSddcSpec` — no source enumerates them. The
  result *shape* is spec-confirmed; the *content* is not. Same for `validationChecks[].acknowledge`
  — which checks are acknowledgeable rather than blocking is undocumented.
- **9.1-scoped restatement of host-count minima, DRS/vLCM rules, and the convergence-unsupported
  list** — captured only from the 9.0 convergence page. **See P5, P8.**
- **Whether the convergence "unsupported: Enhanced Linked Mode" rule still holds in 9.1** — 9.1
  documents NSX **Federation** support without restating the ELM exclusion, and separately, vCenter
  ELM was already deprecated in 9.0 [D9.0 §9.1]. Unresolved.
- **VCF Simple vs VCF High Availability topologies** — named as Installer deployment topologies
  [D9.0 §4.2] with "component matrices and requirements … not retrieved" [D9.0 §11 item 11]. The
  `applianceSize` description on `VcfOperationsSpec` still distinguishes "Simple" deployments, so
  the distinction is live and its rules are unverified.
- **Rollback semantics.** `retrySddc` and per-task retry/cancel exist. **No retrieved source
  describes an undo or teardown for a partially completed bring-up.**
- **Literal base URL.** The spec's declared server is the placeholder `http://localhost:80` with a
  `basePath` variable, and *no 9.1 techdocs page prints a literal REST base path* [D9.1 §8.1]. The
  load-bearing part is the `/v1/...` path; substitute your appliance FQDN.

---

## The 9.1 Installer API surface — 57 operations

Spec title *VMware Cloud Foundation Installer API Reference Guide*; description "VMware Cloud
Foundation Installer handles installation of VCF (or VVF) with new or existing components."
Server: placeholder `http://localhost:80` + `basePath` variable. **Base path did not change between
versions** [DELTA].

Tags (12, identical to 9.0): `Bundles`, `CEIP`, `DepotSettings`, `Flexible Product Patches`,
`ProxyConfiguration`, `Releases`, `System`, `Tasks`, `Tokens`, `Trusted Certificates`,
`VCF Installer`, `VcfServices`.

**Delta from 9.0: 5 operations added, 0 removed, 0 newly deprecated** [DELTA]:
```
POST /v1/sddcs/resources-calculation        resourcesCalculation      (P9)
GET  /v1/sddcs/resources-calculation/{id}   getResourcesCalculation   (P9)
POST /v1/sddcs/sddcm-discovery              discoverSddcManager       (convergence)
POST /v1/sddcs/vcenter-discovery/networks   discoverVcenterNetworks   (P4)
GET  /v1/system/settings/depot/machine-details  getMachineDetails     (P6)
```

**The `VCF Installer` tag — the bring-up operations (18 in 9.1, all spec-confirmed):**
```
POST  /v1/sddcs/validations               validateSddcSpec            body SddcSpec -> Validation
GET   /v1/sddcs/validations               getSddcSpecValidations
GET   /v1/sddcs/validations/latest        getLatestSddcSpecValidation
GET   /v1/sddcs/validations/{id}          getSddcSpecValidation
POST  /v1/sddcs/resources-calculation     resourcesCalculation        <- NEW
GET   /v1/sddcs/resources-calculation/{id} getResourcesCalculation    <- NEW
POST  /v1/sddcs                           deploySddc                  -> SddcTask   (?skipValidations)
GET   /v1/sddcs                           getSddcTasks
GET   /v1/sddcs/latest                    getLatestSddcTask
GET   /v1/sddcs/{id}                      getSddcTaskByID
PATCH /v1/sddcs/{id}                      retrySddc                   (?skipValidations)
GET   /v1/sddcs/{id}/spec                 getSddcSpecByID
POST  /v1/sddcs/installer-mode            getInstallerType
POST  /v1/sddcs/network-config-profiles   getNetworkConfigProfiles
POST  /v1/sddcs/vcenter-discovery         discoverVcenter
POST  /v1/sddcs/vcenter-discovery/networks discoverVcenterNetworks    <- NEW
POST  /v1/sddcs/vcfops-discovery          discoverVcfOps
POST  /v1/sddcs/sddcm-discovery           discoverSddcManager         <- NEW
```

Everything else matches 9.0: `Bundles` (7), `DepotSettings` (**6** with `machine-details`),
`Releases` (3), `Flexible Product Patches` (3), `System` (4), `Tasks` (4), `Tokens` (3),
`Trusted Certificates` (3, on `/v1/sddc-manager/trusted-certificates`), `ProxyConfiguration` (2),
`CEIP` (2), `VcfServices` (2).

---

## The bring-up workflow — calculate → validate → deploy → poll → retry

```
1. GET  /v1/system/appliance-info                     role, version, dnsDomain, dnsServers, ntpServers, ipAddresses
2. POST /v1/sddcs/installer-mode                      Internal vs External — before anything destructive
3. POST /v1/sddcs/network-config-profiles             common physical NICs across the candidate hosts
   (convergence) POST /v1/sddcs/vcenter-discovery
                 POST /v1/sddcs/vcenter-discovery/networks
                 POST /v1/sddcs/vcfops-discovery
                 POST /v1/sddcs/sddcm-discovery
4. POST /v1/sddcs/resources-calculation { SddcSpec } -> 202 CapacityValidation { id }        <- 9.1 gate
   GET  /v1/sddcs/resources-calculation/{id}         -> requiredCapacity vs availableCapacity
5. POST /v1/sddcs/validations           { SddcSpec } -> 202 Validation { id }
   GET  /v1/sddcs/validations/{id}                   -> poll to COMPLETED / SUCCEEDED
6. POST /v1/sddcs                       { SddcSpec } -> 202 SddcTask { id }
7. GET  /v1/sddcs/{id}                               -> poll milestones[] + sddcSubTasks[]
8. on failure: PATCH /v1/sddcs/{id}     { corrected SddcSpec }
```

Notes:
- **`deploySddc` returns 400 "Installation already exists"** if one is in flight. One bring-up per
  appliance at a time.
- **`?skipValidations=true`** on `deploySddc`/`retrySddc` skips the validation gate on a destructive
  operation. There is no documented production reason to use it.
- **`retrySddc` takes a full `SddcSpec`**, not a patch.
- **`getSddcSpecByID`** returns the spec actually recorded for a task — diff it against what you
  believe you sent before retrying.
- `SddcTask` in 9.1 gains **`deploymentType`** and **`vcfInstanceName`**, and `name` is redescribed
  from "Task name" to "**Deployment name**" [RAW9.0 vs RAW9.1]. Status enum still includes
  `IN_PROGRESS`, `COMPLETED_WITH_SUCCESS`, `ROLLBACK_SUCCESS`, `COMPLETED…`.
- `ValidationCheck` gains **`nestedValidationChecks`** in 9.1 — validation results are now a tree,
  so a naive flat reader will miss failures. Recurse.

---

## The SddcSpec payload in 9.1

**Required: `dnsSpec`, `networkSpecs`, `sddcId`, `vcenterSpec`** — unchanged from 9.0.

**`workflowType` widened.** 9.0 pattern `(VCF|VCF_EXTEND|VVF)`; **9.1 pattern
`(VCF|VCF_COMPLETE|VCF_EXTEND|VVF|VCF_BOOTSTRAP)`** [RAW9.0 vs RAW9.1] — two new values,
**`VCF_COMPLETE`** and **`VCF_BOOTSTRAP`**. The 9.1 description adds: *"If building a **secondary
VCF instance** to connect it to the fleet, specify workflowType as `VCF_EXTEND`."*

> **UNVERIFIED — what `VCF_COMPLETE` and `VCF_BOOTSTRAP` do.** The values are spec-confirmed in the
> 9.1 pattern; **no retrieved page describes their semantics**, and the schema `example` still reads
> "One among: VCF, VCF_EXTEND, VVF" — the example was not updated with the pattern. Do not guess.
> (Plausible-looking mappings to 9.1 features such as the workload-domain-without-cluster workflow
> [D9.1 §3.4] are **inference, not evidence** — do not present them as fact.)

**Members new in 9.1** (all absent from `RAW9.0`):

| Field | Schema | Why it exists |
|---|---|---|
| `fleetLcmSpec` | `{ size, version }` | fleet lifecycle service |
| `sddcLcmSpec` | `{ size, version }` | SDDC lifecycle service |
| `fleetDepotSpec` | `{ size, version }` | software depot |
| `vidbSpec` | `{ hostname (req), size, version }` | identity broker |
| `saltSpec`, `saltRaasSpec` | `{ size, version }` | Salt master / Salt RaaS |
| `telemetryAcceptorSpec` | `{ size, version }` | telemetry |
| `licenseServerSpec` | `{ hostname (req), useExistingDeployment, version, sslThumbprint }` | new required License server (P7) |
| `vcfManagementComponentsInfrastructureSpec` | `{ localRegionNetwork, xRegionNetwork }` | placement networks for management services (P4) |
| `vspClusterSpec` | `{ instanceFqdn (req), platformFqdn (req), ipv4Pool (req), fleetFqdn, ipv6Pool, internalClusterCidrIpv4/Ipv6, size (small/medium/large), systemUserPassword, useExistingDeployment, version, sslThumbprint }` | the VSP cluster |

Together these are the spec-side of *"VCF 9.1 deploys standardized management services components
by default, including runtime, fleet lifecycle, identity broker, and software depot"* [D9.1 §3.4].

**Member removed in 9.1:** **`vcfOperationsFleetManagementSpec`** — and the
`VcfOperationsFleetManagementSpec` **schema itself is gone from the 9.1 components block**
(along with `PartnerExtensionSpec`; those are the only two schemas removed). That is independent,
machine-checkable corroboration from the Installer's own spec that the standalone fleet-management
appliance was eliminated [D9.1 §0.2].

**Other 9.1 field-level changes:** `vsanSpec` gains `encryptionConfig` (→ `dataInTransitConfig`);
`nsxtSpec` gains `vpcSpec` (→ `dtgwSpec`, distributed transit gateway); `SddcClusterSpec`,
`SddcDatastoreSpec`, `SddcHostSpec`, `SddcManagerSpec`, `SecuritySpec` and `DvsSpec` are unchanged
in shape. `SddcVcenterSpec.rootVcenterPassword` is redescribed: 9.0 said "between 15 characters and
20 characters"; 9.1 says *"For new deployments, the password must be between 15 and 20 characters
long. For existing vCenter (brownfield)…"* — read the live schema rather than assuming one rule.
`SddcManagerSpec` root/`vcf` passwords are now stated as **"at least 15 characters"** where 9.0 said
only "strong password with at least one alphabet and one special character".

`sddcManagerSpec.localUserPassword` remains: *"a built-in admin account in VCF that can be used in
**emergency scenarios**"* — the break-glass account. Set it deliberately.

---

## Convergence — reusing existing components

Mechanism unchanged from 9.0: a **`useExistingDeployment` boolean per component spec**, with the
paired **`sslThumbprint`** required "when using existing deployment in order to establish trust"
[RAW9.1]. In 9.1 the flag is present on `vcenterSpec`, `nsxtSpec`, `sddcManagerSpec`,
`vcfOperationsSpec`, `vcfOperationsCollectorSpec`, **`licenseServerSpec`** and **`vspClusterSpec`**.
Storage reuse remains `datastoreSpec.existingDatastoreName`.

`vcfOperationsSpec` descriptions gained secondary-instance semantics in 9.1: `nodes` — *"If building
a secondary VCF instance, specify the details of the existing…"*; `useExistingDeployment` and
`adminUserPassword` carry matching notes. Pair with `workflowType: VCF_EXTEND`.

**Discovery endpoints (all spec-confirmed (9.1)):**
```
POST /v1/sddcs/vcenter-discovery           discoverVcenter
     body { address, username, password, sslThumbprint } -> VcenterDiscoveryResult
                                                            { vcenterVersion, vcenterBuildNumber, nsxInfo }
POST /v1/sddcs/vcenter-discovery/networks  discoverVcenterNetworks   <- NEW IN 9.1
     body { endpoint (VcenterDiscoverySpec), name, page, size } -> PageOfVcenterNetworkInfo
POST /v1/sddcs/vcfops-discovery            discoverVcfOps  -> VcfOperationsDiscoveryResult
POST /v1/sddcs/sddcm-discovery             discoverSddcManager       <- NEW IN 9.1
     body { address, adminUsername, adminPassword, sslThumbprint }
     -> SddcManagerDiscoveryResult { sddcManager, managementVcenter, vcfManagementComponents }
```

`discoverSddcManager` is the one that changes what convergence can do: it discovers an **existing
SDDC Manager topology**, returning the SDDC Manager, its management vCenter, and the full
`VcfManagementComponents` inventory. There is no 9.0 equivalent [DELTA].

`GET /v1/system/vcf-management-components` (`getSystemVcfManagementComponents`,
**spec-confirmed (9.1)**) returns `VcfManagementComponents`, which grew from **4 members in 9.0** —
`vcfOperationsFleetManagement`, `vcfOperations`, `vcfOperationsCollector`, `vcfAutomation` — to
**12 in 9.1**: `vcfOperations`, `vcfOperationsCollector`, `vcfAutomation`,
`vcfOperationsFleetManagement`, `vcfOperationsLogs`, `vspCluster`, `sddcLcm`, `fleetLcm`,
`telemetryAcceptor`, `vidb`, `salt`, `saltRaas` [RAW9.0 vs RAW9.1]. Note the oddity:
**`vcfOperationsFleetManagement` is still a member of this response schema in 9.1** even though the
*input* spec `vcfOperationsFleetManagementSpec` was deleted — see Observations.

Gating requirements are in **P8**. Discovery succeeding does not mean the topology is supported.

---

## Task and validation polling

```
GET    /v1/tasks        getTasks    — taskStatus, taskType, resourceId, resourceType, completedAfter,
                                      taskName, pageNumber/pageSize, orderBy/orderDirection, limit, doLiveRefresh
GET    /v1/tasks/{id}   getTask
PATCH  /v1/tasks/{id}   retryTask
DELETE /v1/tasks/{id}   cancelTask
```
All **spec-confirmed (9.1)**, identical to 9.0. The bring-up itself is tracked as an `SddcTask`
through `GET /v1/sddcs/{id}` with its `milestones[]` / `sddcSubTasks[]` tree — poll the surface that
started the work.

`Validation` = `id`, `description`, `executionStatus`, `resultStatus`, `validationChecks[]`. Each
check: `description`, `severity`, `resultStatus`, `acknowledge`, `errorResponse`, **and in 9.1
`nestedValidationChecks`**. Recurse into the nested checks; a flat reader silently misses failures.

---

## What the Installer does not do

- **Workload domains.** Convergence is management-domain-only; workload domains are imported and
  upgraded in **VCF Operations, after** the management domain exists [D9.0 §4.3]. In 9.1, SDDC
  Manager's documented role is *"lifecycle management for ESX, vCenter, HCX, and NSX; deployment of
  workload domains; import of vCenter instances; configuration of vSAN stretched clusters"*
  [D9.1 §0.3]. A 9.1 workflow can create a workload domain **without an initial vSphere cluster**,
  but *"patching/upgrades [are] blocked until a cluster is added"* [D9.1 §3.4].
- **Upgrades and patching of an existing fleet.** That is the `vcf-lifecycle-upgrade` skill —
  including the whole 9.0.x → 9.1 sequence, fleet lifecycle and SDDC lifecycle. Express patch
  releases are explicitly outside the Installer's workflows [D9.0 §4.2].
- **vCLS management.** *"All vCLS functionalities available in SDDC Manager UI and VCF Installer UI
  are removed"* in 9.1 [D9.1 §4].
- **Licence assignment.** You now deploy a License server (P7); assignment still happens in VCF
  Operations / VCF Business Services.
- **Anything after the mode switch.** Once the appliance flips to SDDC Manager mode it "can no
  longer be used in installer mode" [D9.0 §3.2] — you are then on the SDDC Manager API.

---

## Prose-vs-spec observations

1. **The spec declares no security at all, in either version.** No `securitySchemes`, no root
   `security`, no per-operation `security` — verified directly against both raw specs — while a
   `Tokens` tag exists and `accessToken` is described as a "Bearer token". Basis for P0.
2. **The BOM merge is visible in the spec, from both directions.** The appliance exposes
   `/v1/sddc-manager/trusted-certificates`, `VcfServices` operations described as "Retrieve a list
   of **SDDC Manager** services", and a deprecated "[Unsupported] Upload a bundle to **SDDC Manager
   or VCF Installer**". Prose [D9.1 §2] and spec agree: one appliance, one row.
3. **`vcfOperationsFleetManagementSpec` was deleted; `vcfOperationsFleetManagement` was not.** The
   *input* schema is gone from the 9.1 spec (one of only two schemas removed), but the *output*
   `VcfManagementComponents` object still carries a `vcfOperationsFleetManagement` member. Most
   likely a discovery/back-compat field for reading 9.0-era estates — but **no source states this**.
   `UNVERIFIED`. Do not tell anyone they can still deploy a fleet-management appliance in 9.1: the
   appliance "no longer exists" [D9.1 §0.2] and the input field to request one is gone.
4. **`workflowType` gained two values with no documentation.** `VCF_COMPLETE` and `VCF_BOOTSTRAP`
   are in the 9.1 pattern; the schema's own `example` was not updated and still lists only the three
   9.0 values. See the UNVERIFIED box above.
5. **`installer-mode` is a POST that reads state** — it takes endpoints to probe. There is no GET.
6. **Five operations added, zero removed, zero deprecated** [DELTA] — the Installer API is the most
   stable surface in the 9.0 → 9.1 delta. The change of substance is in the **schemas**, not the
   paths: **44 schemas added, 2 removed** (120 → 162). If you diff only endpoint lists between
   versions you will conclude, wrongly, that almost nothing changed.
7. **Prose says "deployed by default", the spec says "configurable".** The management-services
   components appear as optional `SddcSpec` members with `size` and `version`, while the release
   notes say they are deployed by default [D9.1 §3.4]. What happens when you omit them — defaults
   applied, or components skipped — is **not documented**. `UNVERIFIED`.
