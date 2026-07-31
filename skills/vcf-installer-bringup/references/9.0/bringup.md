# VCF 9.0 — VCF Installer and Management-Domain Bring-Up Reference

**Scope:** VMware Cloud Foundation 9.0.x (9.0.0.0 / 9.0.1.0 / 9.0.2.0), greenfield bring-up and
convergence of existing vSphere infrastructure. Everything here is `[9.0]` unless tagged
otherwise.

**Sources.** `D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DAUTH` = `research/foundation-auth-identity.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md`.
`SPECI9.0` = `research/spec-inventory/9.0__vcf-installer.ops.json` — **52 operations**, spec
version `9.0.0.0`, title *VMware Cloud Foundation Installer API Reference Guide*, taken from git
tag `9.0.0.0` of `github.com/vmware/vcf-api-specs`.
`RAW9.0` = the raw spec `specifications/vcf-installer/vcf-installer-openapi.json` at that same
tag, read for request/response schemas.

> **Note on the raw 9.0 spec.** The path `/tmp/vcf-specs-90/...` referenced in the task brief did
> not exist in this environment. The 9.0 raw spec used here was extracted from the same repository
> clone with `git show 9.0.0.0:specifications/vcf-installer/vcf-installer-openapi.json` — same tag,
> same file, same content the `SPECI9.0` inventory was built from.

**Every endpoint below was checked against `SPECI9.0`** and is marked **spec-confirmed (9.0)**
with its `operationId`, or flagged.

---

## Read this first — the appliance you are calling is the appliance you are deploying

**Cloud Builder does not exist in 9.0.** It was replaced by the **VCF Installer** appliance
[D9.0 §9.2, §4.2]. Two consequences that catch people:

1. **VCF Installer and SDDC Manager are the same appliance in two modes.** The Installer "arrives
   pre-packaged with the SDDC Manager appliance within the **`VCF-SDDC-Manager-Appliance-9.x.x.ova`**
   file" [D9.0 §3.2]. Corroboration: in the 9.0.2.0 BOM, **SDDC Manager 9.0.2.0 and VCF Installer
   9.0.2.0 share build `25151285`** [D9.0 §1.4].
2. **The mode switch is one-way.** When the Installer appliance is deployed **inside** the
   management infrastructure — on the hosts that will form the management domain — it automatically
   *"switches into SDDC Manager mode and **can no longer be used in installer mode**"* [D9.0 §3.2].
   Deployed **outside** management infrastructure it stays an installer and can build **multiple
   platforms from a single appliance** [D9.0 §4.2]. Decide this before you power it on; there is no
   documented way back.

**The SDDC Manager bring-up APIs are gone in 9.0**, "replaced" by the VCF Installer appliance
[D9.0 §9.2]. Do not look for bring-up on SDDC Manager's API — it is on the Installer's.

Also removed in 9.0: the **Deployment Parameter Worksheet**, superseded by the VCF Installer
appliance UI and its JSON specification [D9.0 §9.2]. The JSON is `SddcSpec`, documented below.

---

## Contents

- [Read this first](#read-this-first--the-appliance-you-are-calling-is-the-appliance-you-are-deploying)
- [Prerequisites](#prerequisites)
  - P0 — Authentication to the VCF Installer API — **UNVERIFIED, read in full**
  - P1 — Appliance identity and mode (one-way switch)
  - P2 — DNS, FQDNs and the subdomain
  - P3 — NTP
  - P4 — Network readiness
  - P5 — ESX host state
  - P6 — Binaries and depot
  - P7 — Licensing
  - P8 — Convergence-only gates (importing existing infrastructure)
  - P9 — Items the research could not verify
- [The 9.0 Installer API surface — 52 operations](#the-90-installer-api-surface--52-operations)
- [The bring-up workflow](#the-bring-up-workflow--validate--deploy--poll--retry)
- [The SddcSpec payload](#the-sddcspec-payload)
- [Convergence — reusing existing components](#convergence--reusing-existing-components)
- [Task and validation polling](#task-and-validation-polling)
- [What the Installer does not do](#what-the-installer-does-not-do)
- [Prose-vs-spec observations](#prose-vs-spec-observations)

---

## Prerequisites

Bring-up is the one VCF operation where the prerequisites *are* the work. A failed `deploySddc`
against half-ready infrastructure leaves partially built appliances behind, and the documented
recovery is retry (`retrySddc`), not rollback. Each item below states what must be true, **how to
verify it**, the version, and whether 9.1 differs.

### P0 — Authentication to the VCF Installer API `[9.0]` — **UNVERIFIED**

**This is the first blocking gap, and it is the one most likely to be papered over by assumption.**

**What the spec establishes (spec-confirmed (9.0)):** the Installer spec carries a `Tokens` tag
with exactly three operations:

```
POST   /v1/tokens                        createToken            body TokenCreationSpec -> 201 TokenPair
PATCH  /v1/tokens/access-token/refresh   refreshAccessToken     body: JSON string (refresh token id) -> 200 string
DELETE /v1/tokens/refresh-token          invalidateRefreshToken body: JSON string (refresh token id) -> 204
```

Schemas, from `RAW9.0`:
- `TokenCreationSpec` — `username`, `password`, plus **`apiKey`** and **`idToken`**. All optional
  in the schema; no `required` list.
- `TokenPair` — `accessToken` ("Bearer token that can be used to make public API calls") and
  `refreshToken.id` ("Refresh token id that can be used to request new access token").

**What the spec does NOT establish — checked directly, both tags:**
- `components.securitySchemes` is **absent** from the 9.0 Installer spec. `components` contains
  only `schemas`.
- There is **no top-level `security` block**, and **zero operations declare `security`**.
- So the spec never says *which header* carries the token, nor that any operation requires one.
  The word "Bearer" appears only inside the `accessToken` field *description*.

**What the documentation research established:** nothing. The auth matrix in `DAUTH` has **no VCF
Installer row at all**, in either version. And `D9.0 §11 item 2` records the gap explicitly:

> "VCF Installer API base URL and token endpoints not confirmed. A `Tokens` category exists at
> `…/vcf-installer-api/latest/tokens/`, but I did not fetch it. I therefore **cannot assert** that
> VCF Installer auth is identical to SDDC Manager auth." — `UNVERIFIED — could not retrieve`

> **Do not restate SDDC Manager's auth flow as the Installer's.** SDDC Manager's flow is
> documented (`Authorization: Bearer <accessToken>`, access token 1 h, refresh token 24 h, refresh
> body `text/plain`) [D9.0 §3.3] — *for SDDC Manager*. The path and operation names match, which is
> unsurprising for one appliance in two modes, but three things are unconfirmed for the Installer:
> **the header name and format**, **the token lifetimes**, and **the content type of the refresh
> body** — where the specs actually *differ*: the Installer spec declares the refresh and
> invalidate request bodies as **`application/json`**, while SDDC Manager's documented flow uses
> **`text/plain`** [D9.0 §3.3]. Sending the wrong one is a 400 at the very first call.
>
> **Close this before the change window**, by reading the live spec off the appliance or the
> Installer API reference at `developer.broadcom.com/xapis/vcf-installer-api/9.0/tokens/`
> (URL from [D9.0 §8.1]; not fetched in this research). Everything else in this file assumes you
> hold a working credential.

**How to verify (once you have a credential):** call a harmless read —
`GET /v1/system/appliance-info` (`getApplianceInfo`, **spec-confirmed (9.0)**). It returns
`ApplianceInfo` with `role` and `version`, which also answers P1.

**9.1 difference:** none that closes the gap. The 9.1 spec is identical on every point above —
same three `Tokens` operations, same schemas, still **no `securitySchemes`**, still no per-operation
`security`. The gap is open in both versions. See `../9.1/bringup.md` P0.

**For everything else about VCF auth** — SSO, identity broker, roles, API tokens, certificate
trust — use the `vcf-foundation` skill. Do not re-derive it here. Note one constant that matters:
**SDDC Manager and ESX are explicitly excluded from VCF SSO in both versions** [DAUTH], so an
SSO-issued token is not the answer to this gap either.

### P1 — Appliance identity and mode `[9.0]`

**Must be true:** the appliance you are calling is still in **installer** mode, and it is deployed
where you intend it to end up. The switch to SDDC Manager mode is automatic and one-way
[D9.0 §3.2].

**How to verify (both spec-confirmed (9.0)):**
```
GET  /v1/system/appliance-info      getApplianceInfo   -> ApplianceInfo { role, version }
POST /v1/sddcs/installer-mode       getInstallerType   -> InstallerSpec { applianceFqdn, type }
```
`getInstallerType` takes a `SddcInstallerRequest` (`endpoints`: a list of `SddcHostSpec` — "List of
ESXi/vCenter in which the appliance will check for itself" — plus `subdomain`, both required) and
returns `type` from the enum **`Internal` | `External` | `Internal, External`** [RAW9.0]. It is
literally the "am I inside the infrastructure I am about to build?" check. Run it before
`deploySddc`, not after.

**Also verify the version.** The 9.0.0.0 BOM lists **VCF Installer at 9.0.2.0 / build 25151285** —
a *later* version than the release it ships with, and the same for VCF Download Tool [D9.0 §1.2].
Do not assume "BOM row version == release version" for these two rows.

**9.1 difference:** both operations exist unchanged in 9.1 (**spec-confirmed (9.1)**), and
`ApplianceInfo` gains `dnsDomain`, `dnsServers`, `ntpServers`, `ipAddresses` — making it a much
better single readiness check. See `../9.1/bringup.md` P1.

### P2 — DNS, FQDNs and the subdomain `[9.0]`

**Must be true:** name resolution is in place for every appliance and host the spec names, and the
names conform to what the Installer will accept.

**What the spec requires** [RAW9.0]:
- `dnsSpec` is a **required** member of `SddcSpec`. Inside it, `subdomain` is **required** —
  "Tenant Sub domain. **Includes the full domain suffix**".
- `dnsSpec.nameservers` — "Nameservers to be configured for vCenter/ESXi's/NSX. The first is the
  primary nameserver. **Maximum allowed is two entries.**"
- `SddcHostSpec.hostname` — "ESX hostname. This value **will be prefixed to the DNS subdomain
  name** and should **not** include the domain name itself. Must also adhere to **RFC 1123** naming
  conventions." A common failure is passing an FQDN here.
- `sddcId` — "Used for **management domain name**. Can contain only letters, numbers and `-`.
  **Minimum length 3, maximum length 20.**"
- `vcfInstanceName` — minimum length 3, maximum 300.
- Component FQDNs are separate required-ish fields: `sddcManagerSpec.hostname` (required),
  `vcenterSpec.vcenterHostname` (required), `nsxtSpec.vipFqdn` (required, "Hostname for VIP so that
  common SSL certificates can be installed across all managers"), and each entry of
  `nsxtSpec.nsxtManagers`.

**How to verify:** resolve each name forward, and each address back, before you submit — then let
`validateSddcSpec` (`POST /v1/sddcs/validations`, **spec-confirmed (9.0)**) confirm it. The
validation result carries per-check detail (`Validation.validationChecks[]`, each with
`description`, `severity`, `resultStatus`, `errorResponse`).

> **UNVERIFIED.** No page retrieved in this research states the DNS **record requirements**
> explicitly — forward and reverse records per appliance, whether PTR is mandatory, or which
> component checks which. The *field* requirements above are spec-confirmed; the DNS-zone checklist
> is not. Do not present one as sourced.

**9.1 difference:** identical field semantics, with `vcfInstanceName` minimum relaxed from 3 to 1
[RAW9.1]. 9.1 additionally documents a certificate/FQDN prerequisite for VCF Management Services
deployment [D9.1 §5.2], which has no 9.0 counterpart.

### P3 — NTP `[9.0]`

**Must be true:** reachable NTP servers, since every management appliance is configured from the
same list.

**What the spec provides:** `SddcSpec.ntpServers` — "List of NTP servers to be used for
configuring **Management Appliances**" [RAW9.0]. It is an array of strings and is **not** in the
`required` list of `SddcSpec` (`dnsSpec`, `networkSpecs`, `sddcId`, `vcenterSpec` are).

**How to verify:** `POST /v1/sddcs/validations` before deploying.

> **UNVERIFIED.** How many NTP servers are required, whether time skew is checked, and what happens
> when `ntpServers` is omitted are **not documented in any retrieved source**. Do not assert a
> minimum count.

**9.1 difference:** the field is unchanged. 9.1's `ApplianceInfo` reports the Installer's own
`ntpServers`, which 9.0's does not.

### P4 — Network readiness `[9.0]`

**Must be true:** the VLANs, subnets, gateways and uplinks named in `networkSpecs` exist and work.
`networkSpecs` is a **required** member of `SddcSpec`.

**What the spec defines** (`SddcNetworkSpec`, `RAW9.0`) — `networkType` and `vlanId` are required:
- `networkType` — "One among: **VSAN, VMOTION, MANAGEMENT, VM_MANAGEMENT, NFS** or any custom
  network type"
- `gateway`, `subnet`, `subnetMask`, `mtu`, `portGroupKey` ("autogenerated if null")
- `includeIpAddress` / `includeIpAddressRanges` — the address pool for the network
- `teamingPolicy` — "for VSAN and VMOTION network types, Default is `loadbalance_loadbased`. One
  among: `loadbalance_ip`, `loadbalance_srcmac`, …"; `activeUplinks` / `standbyUplinks`
  ("specify uplink1/uplink2 for `failover_explicit` VSAN Teaming Policy")
- vSphere Distributed Switches are described by `dvsSpecs` — "if blank, a default single one will
  be created" (VCF only) — with `dvsName`, `mtu`, `vmnicsToUplinks`, `nsxtSwitchConfig`,
  `nsxTeamings`, `lagSpecs`.
- `SddcSpec.managementPoolName` — "Name for the network pool to be created and associated with the
  Management Cluster".
- **`skipGatewayPingValidation`** exists — "Skip networks gateway connectivity validation" — which
  tells you gateway reachability **is** validated by default. Setting it true suppresses a real
  check; treat it as a diagnostic, not a workaround.

**Convergence adds documented network requirements** [D9.0 §4.3]: **vDS version 8.0+**, **statically
assigned VMkernel IPs**, dedicated vMotion networks, "ports per VMware standards". Dynamically
allocated VMkernel IPs and **Cisco virtual switches** are listed as **unsupported** for convergence.

**Profile helper (spec-confirmed (9.0)):**
```
POST /v1/sddcs/network-config-profiles   getNetworkConfigProfiles
  body SddcNetworkConfigProfileSpec { storageType, hostSpecs, subdomain, nsxConfigType }
  -> SddcNetworkConfigProfileResponse { commonPhysicalNics, profiles }
```
Use it to discover which physical NICs the candidate hosts have in common before you write
`dvsSpecs` by hand.

> **UNVERIFIED — the ports and protocols matrix.** Broadcom's prerequisites point at the **VMware
> Ports and Protocols** tool (`https://ports.broadcom.com/`), which **renders client-side and
> exposes no static table**; the research could not retrieve it for 9.0 or 9.1, and product
> coverage for VCF 9.x could not even be confirmed [DAUTH §4]. **Network requirements are therefore
> NOT fully documented here.** Do not produce a port list, and do not let a bring-up plan claim the
> firewall requirements are covered. Say the requirement exists, point at the tool, and treat it as
> an open item.
>
> What *is* verified is the outbound side: online functionality needs HTTPS/443 to
> `dl.broadcom.com` (component binaries), `vvs.broadcom.com` (compatibility data — VCF Installer,
> SDDC Manager, download tools), `vsanhealth.vmware.com` (vSAN HCL), `vcsa.vmware.com` (CEIP),
> plus `eapi.broadcom.com` / `vcf.broadcom.com` for VCF Operations licensing and
> `auth.esp.vmware.com` for UMDS [DAUTH §4, sourced to the 9.1 public-URLs page — the equivalent
> 9.0 page returned **404**, so treat this list as `[9.1]`-sourced and verify for 9.0].

**9.1 difference:** `SddcNetworkSpec` gains `ipAddressVersion` (IPv4/IPv6), `ipAddressAssignmentMode`
(STATIC/DHCP/SLAAC) and a **`FLEET_MANAGEMENT`** network type. See `../9.1/bringup.md` P4 and
`../deltas.md`.

### P5 — ESX host state `[9.0]`

**Must be true:** ESX is already installed on every host, and each host is in the state the
Installer expects.

- Greenfield is defined as deploying "on **pre-installed ESX hosts**" [D9.0 §4.1]. The Installer
  does not image hosts in 9.0.
- `SddcSpec.hostSpecs` — "List of ESXi to be added to the **Management Cluster**"; each
  `SddcHostSpec` requires `hostname` and carries `credentials` (`username`/`password`, password
  required), `sslThumbprint` ("ESX host SSL thumbprint (SHA256)") and `sshThumbprint`
  ("ESX host SSH thumbprint (RSA SHA256) in new deployment scenario **or** ESX host SSH key
  (RSA, ECDSA) in reuse existing deployment scenario") [RAW9.0].
- `SddcSpec.skipEsxThumbprintValidation` — "Applies to **both** converting an existing environment
  and deploying a new one". Same warning as the gateway skip: it disables a real check.
- **Host counts, from the convergence prerequisites** [D9.0 §4.3]: shared datastores accessible and
  writable across all cluster hosts; minimum **3 ESX hosts for vSAN** or **2 for external storage**
  for simple deployments; vSAN stretched clusters and two-node ROBO supported. These are stated in
  the convergence section — see the scope caveat in P8 before quoting them as the greenfield
  minimum.
- **Compute prerequisites for convergence** [D9.0 §4.3]: vCenter VM hosted on managed clusters;
  **fully automated DRS**; **vSphere Lifecycle Manager images, not baselines** — baselines and
  baseline groups are "no longer supported" in vCenter 9.0 [D9.0 §9.2].

**How to verify:** collect thumbprints out of band, then run `POST /v1/sddcs/validations` and read
`validationChecks[]`. `POST /v1/sddcs/network-config-profiles` also takes `hostSpecs` and will tell
you the common physical NICs.

**9.1 difference:** `SddcHostSpec` is byte-identical in 9.1 [RAW9.1]. What changes around it is the
convergence matrix (P8) and, at the platform level, ESX Zero Touch Provisioning [D9.1 §3.1] — which
is a vSphere feature, not an Installer API.

### P6 — Binaries and depot `[9.0]`

**Must be true:** the Installer can obtain the binaries for the release you are deploying.

**How to verify (all spec-confirmed (9.0), on the Installer itself):**
```
GET    /v1/system/settings/depot                    getDepotSettings
PUT    /v1/system/settings/depot                    updateDepotSettings      (configure credentials)
DELETE /v1/system/settings/depot                    deleteDepotSettings      (?depotType=)
GET    /v1/system/settings/depot/depot-sync-info    getDepotSyncInfo
PATCH  /v1/system/settings/depot/depot-sync-info    syncDepotMetadata
GET    /v1/bundles                                  getBundles               (?productType, ?bundleType, ?isCompliant)
GET    /v1/bundles/download-status                  getBundleDownloadStatus  (?releaseVersion, ?bundleId, ?imageType=INSTALL|PATCH)
GET    /v1/bundles/{id}                             getBundle
PATCH  /v1/bundles/{id}                             startBundleDownloadByID  (start / schedule / cancel)
DELETE /v1/bundles/{id}                             deleteBundle             (?binaryFilesOnly)
GET    /v1/releases                                 getReleases
GET    /v1/releases/system                          getSystemRelease
GET    /v1/releases/{sku}/release-components        getReleaseComponentsBySku
GET    /v1/system/proxy-configuration               getProxyConfiguration
PATCH  /v1/system/proxy-configuration               updateProxyConfiguration
```
`POST /v1/bundles` (`uploadBundle`) exists but is marked **`deprecated: true`** in *both* versions
and its summary is literally *"[Unsupported] Upload a bundle to SDDC Manager or VCF Installer"*.
Do not build an offline workflow on it.

**Release-type limitation** [D9.0 §4.2]: the Installer supports **major, minor and maintenance**
releases. **Express patch releases are NOT supported** and must be applied **manually after the
workflows complete**. This is a planning constraint, not an API flag.

Offline/air-gapped staging is done with the **VCF Download Tool** CLI, into which the deprecated
standalone UMDS was folded [D9.0 §6.2, §9.1].

> **UNVERIFIED.** The bundle-type taxonomy and the online/offline depot payload shapes are
> **not documented on any page fetched**, in either version [D9.0 §11 item 6]. The `bundleType` and
> `productType` query parameters exist; their enumerations do not appear in any retrieved source.
> Read the live schema before constructing a depot body.

**9.1 difference:** identical set **plus** `GET /v1/system/settings/depot/machine-details`
(`getMachineDetails`) — one of the five 9.1 additions [DELTA].

### P7 — Licensing `[9.0]`

**Must be true:** you have licences, and you know they are not applied through the Installer.

- 9.0 replaced 25-character keys with **subscription licence files**, managed through a **VCF
  Operations instance** and the **VCF Business Services console** (`vcf.broadcom.com`)
  [D9.0 §5.1].
- Assignment model: assign a **primary licence to a vCenter instance**; connected assets
  **including ESX hosts are then licensed automatically**. Add-on licences only after primary
  [D9.0 §5.3].
- Evaluation mode is **90 days** [D9.0 §5.4].
- **Spec check:** the 9.0 `SddcSpec` contains **no licence field of any kind** — searched every
  schema property in `RAW9.0` for `licen*`: zero hits. Licensing is genuinely out of band for 9.0
  bring-up.

**9.1 difference — material.** `SddcSpec` gains **`licenseServerSpec`** (`hostname` required, plus
`useExistingDeployment`, `version`, `sslThumbprint`) [RAW9.1], matching the new required **License
server** component [D9.1 §5.2, §6]. In 9.1 the licence server is part of what you deploy.

### P8 — Convergence-only gates (importing existing infrastructure) `[9.0]`

Convergence ("VCF Import") means "you can use your existing virtual infrastructure as building
blocks" [D9.0 §4.3]. It has its own gates, and one scope rule people miss.

**Scope rule, verbatim** [D9.0 §4.3]:
> "For a VCF platform, the following configurations, requirements, and converge scenarios are
> applicable for your **management domain only**. You import and upgrade workload domains in VCF
> Operations, **after** you deployed the management domain."

**Three phases** [D9.0 §4.3]: (1) meet general and scenario-specific requirements, (2) **manually
upgrade components to 9.0.x**, (3) run the VCF Installer-driven deployment. Step 2 is manual and is
where most of the elapsed time goes.

**NSX version gate — differs by patch level** [D9.0 §4.3]:
- **VCF 9.0.0:** only a **new** NSX 9.0 deployment during convergence. **Existing NSX instances are
  unsupported.**
- **VCF 9.0.1 and later:** NSX instances **without Enhanced Linked Mode** support convergence.

**Explicitly unsupported for convergence** [D9.0 §4.3]: Dell **VxRail**-managed clusters; vCenter
instances with **Enhanced Linked Mode**; **Cisco virtual switches**; **dynamically allocated
VMkernel IPs**.

**Outcomes** [D9.0 §4.3]: creation of a new VCF Fleet, or a new VCF Instance within an existing
fleet; automatic provisioning of missing management components; reuse of existing vCenter and ESX
hosts for the management domain.

**How to verify:** the discovery endpoints in the next section, then `validateSddcSpec`.

**9.1 difference — the supported matrix widens substantially** (existing vCenter 8.0 U2a+ with NSX
4.1.2.1+, NSX Federation, dual-stack IPv4/IPv6, and more) [D9.1 §3.4]. See `../9.1/bringup.md` P8
and `../deltas.md`.

### P9 — Items the research could not verify — state these as gaps

- **VCF Installer authentication** — header format, token lifetimes, refresh content type. The
  spec declares **no `securitySchemes`** in either version and the doc research never fetched the
  Installer `Tokens` page [D9.0 §11 item 2; DAUTH has no Installer row]. **See P0. Blocking.**
- **Ports and protocols matrix** — never retrieved, either version [DAUTH §4]. **See P4.**
- **DNS record checklist** (forward/reverse per appliance) — not on any retrieved page. **See P2.**
- **NTP server count / skew tolerance** — not documented. **See P3.**
- **Bundle-type taxonomy and depot payload shapes** — explicitly undocumented [D9.0 §11 item 6].
- **The enumerated validation checks** that `validateSddcSpec` runs — no source enumerates them;
  the *shape* of the result (`validationChecks[]` with `severity` and `resultStatus`) is
  spec-confirmed, the *content* is not.
- **VCF Simple vs VCF High Availability topologies** — both are named as Installer deployment
  topologies [D9.0 §4.2] but "their component matrices and requirements were not retrieved"
  [D9.0 §11 item 11]. `applianceSize` on `VcfOperationsSpec` refers to "Simple" vs other
  deployments in its description, so the distinction is real and its rules are unverified.
- **Sizing / capacity requirements for the management domain** — 9.0 has **no** resources-calculation
  API (it is a 9.1 addition, `POST /v1/sddcs/resources-calculation`) and the Design and
  Planning-and-Preparation guides were not fetched [D9.0 §11 item 9].
- **Rollback semantics.** The API offers `retrySddc` and per-task retry/cancel. **No source
  retrieved describes an undo, teardown or rollback for a partially completed bring-up.** Treat the
  absence as absence of a documented path, not as evidence one does not exist.

---

## The 9.0 Installer API surface — 52 operations

Spec title *VMware Cloud Foundation Installer API Reference Guide*; description "VMware Cloud
Foundation Installer handles installation of VCF (or VVF) with new or existing components."
Declared server is the placeholder `http://localhost:80` with a `basePath` variable — substitute
your appliance FQDN; the load-bearing part is the `/v1/...` path.

Tags (12, identical in 9.1): `Bundles`, `CEIP`, `DepotSettings`, `Flexible Product Patches`,
`ProxyConfiguration`, `Releases`, `System`, `Tasks`, `Tokens`, `Trusted Certificates`,
`VCF Installer`, `VcfServices`.

**The `VCF Installer` tag — the bring-up operations themselves (14 in 9.0, all spec-confirmed):**
```
POST  /v1/sddcs/validations          validateSddcSpec             body SddcSpec -> 202 Validation
GET   /v1/sddcs/validations          getSddcSpecValidations       -> PageOfValidation
GET   /v1/sddcs/validations/latest   getLatestSddcSpecValidation  -> Validation
GET   /v1/sddcs/validations/{id}     getSddcSpecValidation        -> Validation
POST  /v1/sddcs                      deploySddc                   body SddcSpec -> 202 SddcTask   (?skipValidations)
GET   /v1/sddcs                      getSddcTasks                 -> PageOfSddcTask
GET   /v1/sddcs/latest               getLatestSddcTask            -> SddcTask
GET   /v1/sddcs/{id}                 getSddcTaskByID              -> SddcTask
PATCH /v1/sddcs/{id}                 retrySddc                    body SddcSpec -> 202 SddcTask   (?skipValidations)
GET   /v1/sddcs/{id}/spec            getSddcSpecByID              -> the spec used for that task
POST  /v1/sddcs/installer-mode       getInstallerType             -> InstallerSpec
POST  /v1/sddcs/network-config-profiles  getNetworkConfigProfiles -> SddcNetworkConfigProfileResponse
POST  /v1/sddcs/vcenter-discovery    discoverVcenter              -> VcenterDiscoveryResult
POST  /v1/sddcs/vcfops-discovery     discoverVcfOps               -> VcfOperationsDiscoveryResult
```

**Everything else on the appliance:** `Bundles` (7), `DepotSettings` (5), `Releases` (3),
`Flexible Product Patches` (3), `System` (4: `getSystemConfiguration`, `updateSystemConfiguration`,
`getApplianceInfo`, `getSystemVcfManagementComponents`), `Tasks` (4), `Tokens` (3),
`Trusted Certificates` (3: `getTrustedCertificates`, `addTrustedCertificate`,
`deleteTrustedCertificate` — note the paths are `/v1/sddc-manager/trusted-certificates`, another
tell that this is the SDDC Manager appliance), `ProxyConfiguration` (2), `CEIP` (2),
`VcfServices` (2: `getVcfServices`, `getVcfService` — "Retrieve a list of **SDDC Manager**
services").

---

## The bring-up workflow — validate → deploy → poll → retry

The 9.0 Installer follows VCF's standard **validate-then-execute-then-poll** shape [D9.0 §3.4].

```
1. GET  /v1/system/appliance-info                      confirm role/version         getApplianceInfo
2. POST /v1/sddcs/installer-mode                       confirm Internal vs External getInstallerType
3. POST /v1/sddcs/network-config-profiles              discover common NICs         getNetworkConfigProfiles
   (convergence only) POST /v1/sddcs/vcenter-discovery, POST /v1/sddcs/vcfops-discovery
4. POST /v1/sddcs/validations   { SddcSpec }        -> 202 Validation { id }        validateSddcSpec
5. GET  /v1/sddcs/validations/{id}                  -> poll to COMPLETED            getSddcSpecValidation
      executionStatus: IN_PROGRESS | FAILED | COMPLETED | UNKNOWN | SKIPPED…
      resultStatus:    SUCCEEDED | …    (read validationChecks[].severity)
6. POST /v1/sddcs               { SddcSpec }        -> 202 SddcTask { id }          deploySddc
7. GET  /v1/sddcs/{id}                              -> poll milestones + sddcSubTasks
      status: IN_PROGRESS | COMPLETED_WITH_SUCCESS | ROLLBACK_SUCCESS | COMPLETED…
8. on failure: PATCH /v1/sddcs/{id} { corrected SddcSpec }                          retrySddc
```

Notes that matter:
- **`deploySddc` returns 400 "Installation already exists"** if one is in flight [RAW9.0]. One
  bring-up per appliance at a time.
- **`?skipValidations=true`** exists on both `deploySddc` and `retrySddc`. It skips the validation
  gate on a destructive operation. There is no documented reason to use it in production.
- **`retrySddc` takes a full `SddcSpec`**, not a patch document — you resubmit the corrected
  specification against the existing task id.
- **`getSddcSpecByID`** returns the spec that was actually submitted for a task. Use it to diff what
  you *think* you sent against what the appliance recorded, before retrying.
- `SddcTask` carries `milestones[]` and `sddcSubTasks[]` — poll those for progress, not just
  `status`. `status` includes `ROLLBACK_SUCCESS`, which is the appliance's own internal unwind of a
  failed step and is **not** a documented teardown of a completed deployment.

---

## The SddcSpec payload

`SddcSpec` is the whole bring-up input. **Required: `dnsSpec`, `networkSpecs`, `sddcId`,
`vcenterSpec`** [RAW9.0]. Top-level members in 9.0:

| Field | Type | Notes |
|---|---|---|
| `sddcId` | string | **required** — management domain name; 3–20 chars, `[A-Za-z0-9-]` |
| `vcfInstanceName` | string | 3–300 chars |
| `workflowType` | string | pattern **`(VCF\|VCF_EXTEND\|VVF)`** — `VCF_EXTEND` builds an additional instance |
| `version` | string | target release |
| `dnsSpec` | DnsSpec | **required** — `subdomain` (required), `nameservers` (max 2) |
| `ntpServers` | string[] | see P3 |
| `networkSpecs` | SddcNetworkSpec[] | **required** — see P4 |
| `dvsSpecs` | DvsSpec[] | "if blank, a default single one will be created" (VCF only) |
| `managementPoolName` | string | network pool created for the management cluster |
| `hostSpecs` | SddcHostSpec[] | management-cluster ESX hosts — see P5 |
| `clusterSpec` | SddcClusterSpec | `clusterName`, `datacenterName` (both auto-generated if blank), `clusterEvcMode`, `resourcePoolSpecs` |
| `datastoreSpec` | SddcDatastoreSpec | `vsanSpec` \| `vmfsDatastoreSpec` \| `nfsDatastoreSpec` \| **`existingDatastoreName`** (convergence) |
| `vcenterSpec` | SddcVcenterSpec | **required** — `vcenterHostname` + `rootVcenterPassword` required; `ssoDomain`, `vmSize` (tiny…xlarge), `storageSize` (lstorage/xlstorage), **`useExistingDeployment`** |
| `nsxtSpec` | SddcNsxtSpec | `nsxtManagers` + `vipFqdn` required; admin/audit/root passwords ≥12 chars; `nsxtManagerSize`; `transportVlanId`; `ipAddressPoolSpec`; **`useExistingDeployment`**; `enableEdgeClusterSync`; `skipNsxOverlayOverManagementNetwork` |
| `sddcManagerSpec` | SddcManagerSpec | `hostname` required; `rootPassword`, `sshPassword` (the `vcf` user), **`localUserPassword`** — "a built-in admin account in VCF that can be used in **emergency scenarios**"; `useExistingDeployment` |
| `vcfOperationsSpec` | VcfOperationsSpec | `nodes` required; `applianceSize`; `loadBalancerFqdn`; `adminUserPassword` ("if blank the password will be auto-generated") |
| `vcfOperationsCollectorSpec` | VcfOperationsCollectorSpec | the 9.0 collector appliance |
| **`vcfOperationsFleetManagementSpec`** | VcfOperationsFleetManagementSpec | **9.0 only — the schema does not exist in the 9.1 spec at all** |
| `vcfAutomationSpec` | VcfAutomationSpec | |
| `securitySpec` | SecuritySpec | `esxiCertsMode` (`Custom` \| `VMCA`), `rootCaCerts[]` |
| `ceipEnabled` | boolean | |
| `skipEsxThumbprintValidation` | boolean | see P5 |
| `skipGatewayPingValidation` | boolean | see P4 |

`vsanSpec` carries `datastoreName`, `failuresToTolerate`, `vsanDedup` ("one flag for both
features") and `esaConfig`.

**Password rules are in the field descriptions, and they differ per component** [RAW9.0]: NSX
admin/audit/root ≥ 12 characters; vCenter root **between 15 and 20** characters; SDDC Manager root
and `vcf` "strong password with at least one alphabet and one special character"; vCenter SSO admin
password with upper/lower/etc. Read them from the live schema rather than assuming one policy.

---

## Convergence — reusing existing components

The mechanism is a **`useExistingDeployment` boolean on each component spec** — `vcenterSpec`,
`nsxtSpec`, `sddcManagerSpec`, `vcfOperationsSpec`, `vcfOperationsCollectorSpec` — described
identically: *"Import existing deployment or deploy one."* When set, the paired **`sslThumbprint`**
field becomes load-bearing: *"Need to be populated when using existing deployment in order to
establish trust"* [RAW9.0]. Storage reuse is `datastoreSpec.existingDatastoreName` — "Name of an
existing datastore that is to be used when converting an existing environment."

**Discovery endpoints (both spec-confirmed (9.0)):**
```
POST /v1/sddcs/vcenter-discovery   discoverVcenter
   body VcenterDiscoverySpec { address, username, password, sslThumbprint } -> VcenterDiscoveryResult
POST /v1/sddcs/vcfops-discovery    discoverVcfOps
   body VcfOperationsDiscoverySpec -> VcfOperationsDiscoveryResult
```
Run these first: they tell you what the Installer can actually see, before you assert it in an
`SddcSpec`. There is **no SDDC Manager discovery endpoint in 9.0** — `POST /v1/sddcs/sddcm-discovery`
is a 9.1 addition [DELTA].

`GET /v1/system/vcf-management-components` (`getSystemVcfManagementComponents`,
**spec-confirmed (9.0)**) returns `VcfManagementComponents` with exactly four members in 9.0:
`vcfOperationsFleetManagement`, `vcfOperations`, `vcfOperationsCollector`, `vcfAutomation`. That
four-member shape is itself a 9.0 fingerprint — see `../deltas.md`.

The gating requirements for convergence are in **P8**; do not run discovery and conclude a topology
is supported.

---

## Task and validation polling

```
GET    /v1/tasks        getTasks    — filters: taskStatus, taskType, resourceId, resourceType,
                                      completedAfter, taskName, pageNumber/pageSize, orderBy/orderDirection,
                                      limit, doLiveRefresh
GET    /v1/tasks/{id}   getTask
PATCH  /v1/tasks/{id}   retryTask
DELETE /v1/tasks/{id}   cancelTask
```
All **spec-confirmed (9.0)**. These are the appliance's generic task surface; the bring-up itself is
tracked as an `SddcTask` through `GET /v1/sddcs/{id}`, which carries the milestone/sub-task tree.
Poll the one that started the work.

`Validation` objects: `id`, `description`, `executionStatus`, `resultStatus`, and
`validationChecks[]` where each check has `description`, `severity`, `resultStatus`, `acknowledge`
and `errorResponse`. The `acknowledge` field implies some checks are acknowledgeable rather than
blocking; **which ones is not documented** — `UNVERIFIED`.

---

## What the Installer does not do

- **Workload domains.** Convergence "is applicable for your **management domain only**"; workload
  domains are imported and upgraded **in VCF Operations, after** the management domain exists
  [D9.0 §4.3]. Workload-domain creation is SDDC Manager `/v1/domains` [D9.0 §3.4] or the VCF
  Operations API [D9.0 §3.5].
- **Upgrades and patching of an existing fleet.** That is the `vcf-lifecycle-upgrade` skill. The
  Installer's `Bundles` / `Releases` / `Flexible Product Patches` operations exist to feed a
  *deployment*, and **express patch releases are explicitly out of scope** for its workflows
  [D9.0 §4.2].
- **Licensing.** No licence field exists in the 9.0 `SddcSpec` (P7).
- **Any operation after the mode switch.** Once the appliance flips to SDDC Manager mode it "can no
  longer be used in installer mode" [D9.0 §3.2] — at that point you are calling the SDDC Manager
  API, not this one.

---

## Prose-vs-spec observations

1. **The spec declares no security at all.** No `securitySchemes`, no root `security`, no
   per-operation `security` — verified directly against the 9.0 raw spec. Yet a `Tokens` tag exists
   and the `accessToken` description says "Bearer token that can be used to make public API calls".
   The spec is internally consistent with token auth and silent about how to present it. This is the
   basis for P0.
2. **The appliance is SDDC Manager wearing a different label, and the spec says so.** Trusted-
   certificate paths are `/v1/sddc-manager/trusted-certificates`; `VcfServices` operations are
   described as "Retrieve a list of **SDDC Manager** services"; the deprecated upload-bundle summary
   reads "Upload a bundle to **SDDC Manager or VCF Installer**". Prose [D9.0 §3.2] and spec agree.
3. **`installer-mode` is a POST that reads state.** `getInstallerType` is `POST
   /v1/sddcs/installer-mode` because it takes a body of endpoints to probe. Do not look for a GET.
4. **The 9.0 BOM row for VCF Installer is version-skewed.** The 9.0.0.0 BOM lists VCF Installer at
   **9.0.2.0** [D9.0 §1.2], and the research flags this as an anomaly to carry, not correct
   [D9.0 §1.2 note]. Check `getApplianceInfo` rather than inferring the Installer version from the
   release.
5. **`ROLLBACK_SUCCESS` in `SddcTask.status` is not a rollback feature.** It is a terminal status
   value in the enum; no retrieved source documents a user-invoked rollback of a bring-up. Do not
   present it as one.
