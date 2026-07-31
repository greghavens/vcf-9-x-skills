# vSphere / vCenter / ESX / vSAN in VMware Cloud Foundation 9.0 and 9.1

Research date: **2026-07-31**. Every claim below carries a source ref `[Sxx]` (see
`## Source Inventory`) and a version tag `[9.0]`, `[9.1]`, or `[9.0+9.1]`.
`[9.0+9.1]` is used only where the fact was independently confirmed in both doc sets.
Anything I could not retrieve is marked `UNVERIFIED — could not retrieve`.

---

## In VCF 9.0

### 1. Component versions (Bill of Materials)

From the VCF 9.0 release-notes BOM `[S3]` `[9.0]`:

| Component (name exactly as printed) | Version | Build |
|---|---|---|
| VCF Installer | 9.0.2.0 | 25151285 |
| **VMware ESX** | **9.0.0.0** | 24755229 |
| **VMware vCenter** | **9.0.0.0** | 24755230 |
| VMware vSAN ESA Witness | 9.0.0.0 | 24755427 |
| VMware vSAN File Services | 9.0.0.0 | 24755229 |
| VMware vSAN OSA Witness | 9.0.0.0 | 24755428 |
| VMware NSX | 9.0.0.0 | 24733065 |
| SDDC Manager | 9.0.0.0 | 24703748 |
| VCF Operations | 9.0.0.0 | 24695812 |
| VCF Operations Orchestrator | 9.0.0.0 | 24674408 |
| VCF Operations Collector | 9.0.0.0 | 24695833 |
| VCF Operations Fleet Management | 9.0.0.0 | 24695816 |
| VCF Operations for Logs | 9.0.0.0 | 24695810 |
| VCF Operations for Networks | 9.0.0.0 | 24694676 |
| VCF Operations HCX | 9.0.0.0 | 24699341 |
| VCF Automation | 9.0.0.0 | 24701403 |
| VMware vSphere Supervisor | 9.0.0.0 | 24686447 |
| Kubernetes Backup & Recovery Service | 1.8.0 | 24668882 |
| vSphere Kubernetes Service | 3.3.1 | n/a |
| VMware Remote Console | 13.0.0.0 | 24645870 |
| VMware Tools Async Release | 13.0.0.0 | 24696475 |
| VCF Download Tool | 9.0.1.0 | 25151284 |
| VCF Identity Broker | 9.0.0.0 | 24695128 |

Add-ons listed as compatible: VMware Private AI 9.0.0.0; Data Services Manager
9.0.0.0 (build 24713720); Live Recovery 9.0.3 (build 24693627) `[S3]` `[9.0]`.

**Hypervisor naming.** The BOM row is literally **"VMware ESX"**, not "ESXi"
`[S3]` `[9.0]`. The 9.0 vSphere what's-new page uses "**ESX 9.0**, Build 24755229
(17 JUN 2025)" and "**vCenter 9.0**, Build 24755230 (17 JUN 2025)" `[S4]` `[9.0]`.
However, the VCF 9.0 vSphere product-support-notes page uses "ESX" and "ESXi"
interchangeably and contains **no explicit statement that ESXi was renamed to ESX**
`[S5]` `[9.0]`. Conclusion: the product/BOM name is **ESX** in 9.0, but a formal
"renamed from ESXi" statement is `UNVERIFIED — could not retrieve`.

Note the 9.0 doc set also ships 9.0.1.0 and 9.0.2.0 patch release notes with their own
BOMs (e.g. `.../release-notes/vmware-cloud-foundation-9-0-1-release-notes/esx-9-0-1-0000.html`,
`.../vcenter-9-0-1-0000.html`) — those per-patch BOMs were not fetched `[S2]` `[9.0]`.

### 2. What's new — ESX 9.0 `[S4]` `[9.0]`

- **Virtual hardware version 22**: supports "960 logical processors" and "960 cores
  per socket"; adds peer-to-peer passthrough devices, NVMe 1.4, Intel TDX, AMD SEV-SNP,
  4KN VMDK.
- Security: "support for AMD Secure Encrypted Virtualization-Secure Nested Paging
  (SEV-SNP)"; Intel TDX; "TLS 1.3 support" with NIST_2024 compliance.
- Storage: "Boot over NVMe/FC SAN" and "Boot over NVMe/TCP SAN"; "more precise tracking
  of the progress of consolidation tasks".
- Accelerators: **Memory Tiering** GA using NVMe as tiered memory; Enhanced DirectPath I/O
  gains virtual IOMMU and non-checkpointable device support.
- Networking: "NSX VIBs Included with ESX and Live Patch Support".

### 3. What's new — vCenter 9.0 `[S4]` `[9.0]`

- Accelerator capacity visualization and **GPU Reservations**.
- "4K native support" (4Kn VMDKs); "NFS 4.1 support for Kerberos krb5p security model".
- VPC support in vCenter (subnet creation, external IP exposure for VMs).
- vMotion: "vGPU cold data precopy" — 65–80% checkpoint-data reduction, 40–60% downtime
  reduction claimed for AI workloads.

### 4. API / SDK changes in 9.0 `[S6]` `[9.0]`

- "vCenter 9.0 adds **OpenAPI 3.0** to support all vCenter and vSAN APIs, along with the
  existing VI JSON and vCenter REST APIs, aligning vCenter APIs with the industry standard
  for API specifications."
- "vCenter 9.0 adds the **`com.vmware.vcenter.authorization`** package that enables you to
  use modern REST APIs to configure all aspects of authorization in a vCenter system,
  including privileges, roles, global and inventory permissions."
- New VM-customization pre-check API; Guest OS customization available through vAPIs for
  "all GOSC operations and supported scenarios".
- **Java SDK 9.0.0.0** (Maven Central, groupId `com.vmware.sdk`), **Python SDK 9.0.0.0**
  (PyPI; bundles pyVmomi, vCenter, vSAN Data Protection, SDDC Manager, VCF Installer modules).
- **PowerCLI renamed** `VMware.PowerCLI` → **`VCF.PowerCLI`**.
- New **VCF Consumption CLI**.

### 5. Deprecations / removals relevant to automation, 9.0 `[S5]` `[9.0]`

Removed in vCenter 9.0 (hard blockers for old scripts):
- **"Removal of vSphere Lifecycle Manager baselines: Managing clusters with vSphere
  Lifecycle Manager baselines and baseline groups (legacy vSphere Update Manager (VUM)
  workflows) is no longer supported in vCenter 9.0."**
- **"Blocked non-federated username/password logins to vCenter: vCenter 9.0 blocks logins
  with just a user name and password, which might sometimes allow bypassing the federated
  provider domain."** (Directly affects Basic-auth session creation — see Auth below.)
- Integrated Windows Authentication (IWA) removed; SSPI / smart card / RSA SecurID removed.
- **Patch Manager APIs** removed.
- vCenter Service Lifecycle Management API (`vmonapi`) removed.
- vSphere Trust Authority no longer accessible via API or UI.
- vSphere Automation SDK for Ruby removed.
- Storage DRS I/O Load Balancer + SIOC discontinued; NPIV removed; RoCE v1 removed;
  local vSphere Client plug-ins removed; CIM/SFCB/WSMan stack removed from ESX;
  Intel Optane PMEM support removed.

Deprecated in 9.0:
- vSphere **Auto Deploy** deprecated; **ESX Agent Manager** deprecated; **Host Profiles**
  deprecated (use vSphere Configuration Profiles); **Enhanced Linked Mode** deprecated
  (use grouping under VCF Operations); **vVols** deprecated; **vCLS** deprecated
  ("will be removed in a future vCenter release"); ESX Image Builder UI deprecated
  (CLI continues); first-generation vCenter profile endpoint
  `https://{api_host}/api/appliance/infraprofile/configs` deprecated; vSAN .NET/Perl/Ruby
  management SDKs deprecated.

SDK-side deprecations `[S7]` `[9.0]`: vSAN Ruby/Perl/C# SDKs "officially deprecated";
vSphere Management SDK and vSphere Automation SDK (Java) "deprecated from 9.0.0.0"
in favour of the VCF Java SDK; pyVmomi removals (`pyVmomi.Feature`,
`pyVmomi.pyVmomiSettings`, `ThumbprintMismatchException` imports,
`VmomiSupport.VmomiJSONEncoder`, `templateOf()`, `publicVersions`/`dottedVersions` →
`ltsVersions`, `setup.py` → `pyproject.toml`); PowerShell 5.1 deprecated in VCF PowerCLI 9.0;
`Connect-AutoDeployServer` / `Disconnect-AutoDeployServer` removed; PSObject → Dictionary/
HashTable return-type breaking changes.

### 6. vSphere Automation REST API — base path and auth `[9.0]`

Verbatim from the VCF 9.0 programming guide `[S8]` `[9.0]`:
- "All existing and non-deprecated HTTP operations of the VMware Cloud Foundation API are
  available on port **443** and the **`/api`** base path."
- "The APIs released up to vSphere version 7.0.2 are also available on the **deprecated
  `/rest`** base path."
- "The `/api` base path will remain the only active base path when the `/rest` base path is
  removed in a future vSphere release."
- A subset of the API (appliance configuration and lifecycle) is also on **port 5480**.
- Verb conventions: GET = retrieve, POST = create *and custom actions*, PATCH/PUT = modify,
  DELETE = remove.

**So: `/rest` still exists in 9.0, deprecated, and only carries operations that existed
up to vSphere 7.0.2. New 8.x/9.x operations are `/api`-only** `[S8]` `[9.0]`.

Authentication `[S9]` `[9.0+9.1]` (the auth-mechanisms page is common to both doc sets;
the 9.1 copy was fetched, the 9.0 copy exists at the mirrored URL `[S18]`):
- Token types: session identifiers, SAML tokens, JWT (OAuth 2.0 from external IdP).
- Basic authentication (username/password to vCenter) is described but "VMware discourages"
  it in favour of token-based flows — and see the 9.0 removal note above about blocked
  non-federated logins `[S5]`.
- Federated three-step flow (vSphere 7.0+): obtain JWT from external IdP → exchange JWT for
  a vCenter SSO SAML token → exchange SAML token for a session identifier.
- Supported IdPs: vCenter SSO (default), AD FS (7.0+), Okta (8.0 U1+), Azure AD (8.0 U2+).

Session endpoint (vSphere Automation API reference, version selector includes 9.0 and 9.1)
`[S10]` `[S11]` `[9.0+9.1]`:
```
POST   /api/cis/session      -> create session token
GET    /api/cis/session      -> retrieve info about the current session token
DELETE /api/cis/session      -> invalidate the session token
```
Subsequent calls carry the token in the **`vmware-api-session-id`** HTTP header `[S10]` `[S11]`.
Errors: `Vapi Std Errors Unauthenticated`, `Vapi Std Errors ServiceUnavailable` `[S11]`.
The exact `Authorization: Basic ...` header string on `POST /api/cis/session` is
`UNVERIFIED — could not retrieve` (the SSO-credential walkthrough page returned HTTP 403
through the fetch proxy on repeated attempts) `[S19]`.

### 7. vSAN in 9.0

- Both architectures present: the BOM ships **vSAN ESA Witness** *and* **vSAN OSA Witness**
  appliances at 9.0.0.0 `[S3]` `[9.0]`.
- What's new in vSAN 9.0 `[S12]` `[9.0]`:
  - "Disaster Recovery for vSAN clusters using VMware Live Recovery" (host-based VM
    replication, RPO as low as 1 minute).
  - "vSAN Licensing via VCF Operations" (allocate vSAN TiB entitlements through VCF Operations).
  - "Support of Stretched Compute-only Clusters with vSAN storage clusters".
  - "Support for client traffic separation with vSAN storage clusters" (dedicated VMkernel
    ports separating external VM traffic from internal storage traffic).
  - "Support of up to 500 file shares per cluster in vSAN File Services".
  - "Dying Disk Handling (DDH) supports Cache Drives" — proactive detection in OSA, latency
    monitoring in ESA.
  - The 9.0 what's-new page does **not** list global deduplication, storage-policy changes,
    or capacity-reporting changes `[S12]` `[9.0]`.
- vSAN Management API is a **SOAP/vmodl** web service (not REST), with a 9.0.0.0 entry in the
  reference version selector `[S13]` `[9.0+9.1]`. Endpoints: `/vsan` on ESX hosts,
  `/vsanHealth` on vCenter, `/sdk` for legacy MOs (`HostVsanSystem`, `VsanUpgradeSystem`).
  Key managed objects: `VsanVcClusterConfigSystem`, `VsanPerformanceManager`,
  `VsanVcClusterHealthSystem`, `VsanVcDiskManagementSystem`, `VsanObjectSystem`,
  `VsanIscsiTargetSystem`, `VsanCapabilitySystem` `[S13]`.
- OpenAPI 3.0 now covers "all vCenter **and vSAN** APIs" as of vCenter 9.0 `[S6]` `[9.0]`.

### 8. vSphere Lifecycle Management in 9.0

- **Baselines/baseline groups are removed** for cluster management in vCenter 9.0 — legacy
  VUM workflows "no longer supported in vCenter 9.0" `[S5]` `[9.0]`.
- The standalone vSphere 9.0 doc set states: "With vSphere 9.0, using baselines to upgrade
  the clusters and standalone hosts in your vCenter instances of version 9.0 and later is
  deprecated"; baselines remain only to "Update and patch ESX hosts only of version 8.x"
  and "Update third-party software on ESX hosts" `[S14]` `[9.0]`.
  (These two statements are in tension — VCF release notes say *removed for cluster
  management*, the vSphere guide says *deprecated, 8.x-only residual use*. See Gaps.)
- vLCM automation model, from the VCF 9.0 programming guide `[S15]` `[9.0]`:
  retrieve current cluster/standalone-host state → create a **desired state** (ESX version,
  compatible partner software, firmware, add-ons) → validate against hardware →
  check compliance → apply to cluster or standalone host. Since vSphere 8.0, standalone hosts
  are managed "using an image only through the vSphere Lifecycle Manager automation API".
  Managed hosts must be vSphere 7.0+, stateful, identical hardware from the same vendor,
  and running only integrated solutions (vSAN, vSphere Supervisor, NSX, vSphere HA).
  "The only limitation for managing the life cycle of a standalone host through the VMware
  Cloud Foundation API, is that you can't update the firmware of the host."
  Documented sub-topics: software depots, enabling cluster/standalone-host software specs,
  **draft** software specifications, desired software states, hardware compatibility data,
  remediation settings and operations, third-party solution integration.

---

## In VCF 9.1

### 1. Component versions (Bill of Materials)

From the VCF 9.1.0.0 release-notes BOM `[S16]` `[9.1]` (release notes page dated 12 MAY 2026 `[S17]`):

| Component (name exactly as printed) | Version | Build |
|---|---|---|
| VCF Installer / SDDC Manager | 9.1.0.0 | 25371088 |
| **ESX** | **9.1.0.0** | 25370933 |
| **vCenter** | **9.1.0.0** | 25370922 |
| vSAN ESA Witness | 9.1.0.0 | 25370927 |
| vSAN File Services | 9.1.0.0 | 25370922 |
| vSAN OSA Witness | 9.1.0.0 | 25370925 |
| NSX | 9.1.0.0 | 25318225 |
| VCF Operations | 9.1.0.0 | 25346025 |
| Cloud proxy | 9.1.0.0 | 25346033 |
| License server | 9.1.0.0 | 25346031 |
| VCF Operations for networks | 9.1.0.0 | 25318550 |
| VCF Operations HCX | 9.1.0.0 | 25318520 |
| VCF Operations orchestrator | 9.1.0.0 | 25346069 |
| VCF Automation | 9.1.0.0 | 25370929 |
| Fleet lifecycle | 9.1.0.0 | 25371109 |
| SDDC lifecycle | 9.1.0.0 | 25371107 |
| Software depot | 9.1.0.0 | 25371105 |
| Telemetry | 9.1.0.0 | 25181946 |

No release dates were present in the 9.1 BOM tables `[S16]` `[9.1]`.

**Hypervisor naming.** The 9.1 BOM row is **"ESX"** and the 9.1 vSphere what's-new page
"uses 'ESX' throughout (not 'ESXi')" `[S1]` `[S16]` `[9.1]`.

### 2. What's new — ESX 9.1 `[S1]` `[9.1]`

- **Zero Touch Provisioning (ZTP)** — "using a secure UEFI and HTTPS-based network boot to
  provision ESX images on hosts at scale", replacing the deprecated Auto Deploy.
- Storage: RDMA observability enhancements (packet analysis tools, validation utilities).
- **Guest Customization APIs**: "IPv6-Only Support" for powered-off VMs, "Partial Network
  Customization", expanded account management, and **"Live Network Customization"** for
  powered-on VMs.
- Security: **"User-Level Monitor (ULM) as the default monitor for all virtual machines"** —
  significantly reduces hypervisor code running in privileged mode. AMD SEV-SNP and Intel TDX
  move from limited availability to **general availability** for confidential VMs.
- I/O: NVIDIA Mellanox ConnectX-7, BlueField-3, AMD MI350 GPU with Enhanced DirectPath,
  Intel NIC E825 (Granite Rapids-D).
- **Memory Tiering**: configuration no longer requires a host reboot; RAID1 mirroring support.

### 3. What's new — vCenter 9.1 `[S1]` `[9.1]`

- **vCenter VM hardware version upgrades "from vmx-10 to vmx-17"** (i.e. the vCenter appliance's
  own VM hardware version).
- **vCenter Quick Patch** — upgrades with "zero to 5 minutes of downtime".
- APIs: **OAuth 2.0 token support**, **Query API** for efficient inventory retrieval,
  **vCenter group federated API** for unified multi-instance management, **Utilization API**
  for capacity monitoring.
- Snapshots: **"Resumable Consolidation"** — powered-on VM snapshot consolidation can restart
  without full reprocessing.

### 4. API / SDK changes in 9.1 `[S20]` `[9.1]`

- **Utilization API** — "monitors vCenter capacity and usage metrics" (active connections,
  service request volume) with configurable thresholds.
- **vCenter Group Federated API (VGFA)** — "a single unified API endpoint for managing all
  vCenter instances in a vCenter group".
- **Query API** — "delivers a fast, flexible, and scalable way to retrieve vSphere inventory
  data" with server-side filtering, pagination, and entity counting.
- **Java SDK (VCF 9.1)** adds NSX, VCF Operations, Log Management, network operations, Fleet
  Lifecycle, SDDC Lifecycle; VODAP OpenAPI specifications now available.
- **Python SDK (VCF 9.1)** — same component coverage; separate .ZIP deliverable with code samples.
- **VCF PowerCLI 9.1** new cmdlets: vSAN (`Get-VsanEffectiveCapacity`, remote datastore
  management), VPC (Transit Gateway, DHCP, IP Block, connectivity policy), core (CPU topology,
  NVMe over TCP, **OAuth authentication support**).
- Deprecation: "Python 3.7 and 3.8 is now deprecated" in ImageBuilder; migrate to Python 3.9+.

The exact REST path/verb templates for the Query, Utilization, and VGFA APIs are
`UNVERIFIED — could not retrieve` (no reference page for them was successfully rendered).

### 5. Deprecations in 9.1 `[S21]` `[9.1]`

- ESX system storage: "USB and SD boot devices" and "ESX without a persistent system storage
  device for OSDATA partition" deprecated; devices under 32 GB deprecated.
- "Deprecation of Marvell/Aquantia (Atlantic) NIC devices and drivers".
- "AMD Solarflare 8000 and X2 series Ethernet adapters are deprecated and support will be
  removed in a future VCF release."
- "Usage and dependencies on SHA1-based cryptographic algorithms are deprecated and will be
  removed in a future minor VCF release."
- Marvell FastLinQ 57800/57810/57811 and 41000/45000 CNAs deprecated in VCF 9.1.
- Cisco VIC 1200 and 1300 series deprecated in VCF 9.1.
- vCenter: "Using IPFIX on a VMware vSphere Distributed Switch (VDS) Uplink Port Group" deprecated.
- **vSAN section on the 9.1 product-support-notes page reads "None"** — no vSAN deprecations
  or removals in 9.1 `[S21]` `[9.1]`.

### 6. vSphere Automation REST API — base path and auth `[9.1]`

Verbatim from the VCF **9.1** programming guide `[S18]` `[9.1]` (identical wording to 9.0):
- "All existing and non-deprecated HTTP operations of the VMware Cloud Foundation API are
  available on port 443 and the `/api` base path."
- "The APIs released up to vSphere version 7.0.2 are also available on the deprecated `/rest`
  base path."
- "The `/api` base path will remain the only active base path when the `/rest` base path is
  removed in a future vSphere release."
- Port 5480 subset for appliance configuration and lifecycle.
- GET / POST (create + custom actions) / PATCH / PUT / DELETE conventions.

**`/rest` therefore still exists in 9.1, still deprecated, still limited to pre-7.0.2
operations** `[S18]` `[9.1]`.

Session endpoint is unchanged: `POST|GET|DELETE /api/cis/session`, header
**`vmware-api-session-id`** `[S10]` `[S11]` `[9.0+9.1]` (the reference version selector lists
9.1 as "Latest" and 9.0 as a selectable version `[S10]`).
New in 9.1: **OAuth 2.0 token support** in vCenter and OAuth authentication support in
VCF PowerCLI `[S1]` `[S20]` `[9.1]` — the concrete token endpoint/grant paths are
`UNVERIFIED — could not retrieve`.

### 7. vSAN in 9.1 `[S22]` `[9.1]`

Both architectures still present (ESA Witness and OSA Witness both in the 9.1 BOM `[S16]`).
What's new:

- **vSAN ESA Auto RAID 6** — "vSAN clusters use RAID-6 as the default RAID level" with
  automatic configuration.
- **vSAN ESA Global Deduplication** — "a cluster-wide and post-processing setting with
  encryption support".
- **vSAN ESA Compression Enhancements** — "better storage efficiency", "increased space savings".
- **vSAN Stretched Storage Across vCenter Instances** — storage sharing "across vCenter
  boundaries" and "across multiple VCF deployments".
- **Site maintenance mode** — "support for placing a site in maintenance mode in a vSAN
  stretched cluster" with automated failover.
- **Cyber recovery vSAN storage cluster** — deployable through vCenter, with integrated EDR
  and network isolation. (Mirrored in the 9.1 vSAN planning TOC as "Creating a vSAN ESA
  Storage Cluster for Cyber Recovery" `[S23]` `[9.1]`.)
- **Multiple Retention Schedules for vSAN Snapshots** — daily, weekly, monthly.
- **Seeding for vSAN Replication**; replication support extended to "workloads running on
  any storage".
- **Shared vSAN Storage Cluster Support** — mount both ESA and OSA clusters simultaneously.
- **RWX File Volume Support** and **Fast Clone Volume Support** with snapshots for VM Service.
- CNS/CSI scalability increased to "50,000 volumes per vCenter".

vSAN Management API surface: unchanged shape — SOAP/vmodl, `/vsanHealth` on vCenter,
`/vsan` on hosts, `/sdk` for legacy MOs; the reference's version selector lists **9.1 (Latest)**
`[S13]` `[9.0+9.1]`.

### 8. vSphere Lifecycle Management in 9.1

- vLCM images remain the model; VCF Operations "can manage ESX components and vSphere
  Lifecycle Manager images" `[S24]` `[9.1]`.
- VCF-level lifecycle in 9.1: administrators use "VCF Operations as a VI administrator to
  manage the lifecycle of the management and SDDC components in VCF", covering "downloading
  binaries and updating VCF fleet and VCF Instances". A **software depot** component "handles
  binaries for all VCF components", driven from the VCF Operations UI `[S24]` `[9.1]`.
  Note the 9.1 BOM separates **Fleet lifecycle**, **SDDC lifecycle**, and **Software depot**
  as distinct 9.1.0.0 components `[S16]` `[9.1]` — 9.0's BOM listed a single SDDC Manager
  plus VCF Operations Fleet Management `[S3]` `[9.0]`.
- Upgrade prerequisite: "all workload domains must be at VMware Cloud Foundation 5.2 or later.
  If any workload domain is at a version lower than 5.2, you must upgrade it to 5.2 and then
  upgrade to 9.1." `[S24]` `[9.1]`
- A dedicated 9.1 transition topic exists: "Transitioning from vSphere Lifecycle Manager
  Baselines to vSphere Lifecycle Manager Images" `[S25]` `[9.1]` (URL captured; page body not
  fetched).
- **ZTP replaces Auto Deploy** for at-scale ESX provisioning in 9.1 `[S1]` `[9.1]`.

---

## 9.0 → 9.1 Delta Table

| Area | VCF 9.0 | VCF 9.1 | Refs |
|---|---|---|---|
| ESX version / build | 9.0.0.0 / 24755229 | 9.1.0.0 / 25370933 | `[S3]` `[S16]` |
| vCenter version / build | 9.0.0.0 / 24755230 | 9.1.0.0 / 25370922 | `[S3]` `[S16]` |
| vSAN ESA Witness | 9.0.0.0 / 24755427 | 9.1.0.0 / 25370927 | `[S3]` `[S16]` |
| vSAN OSA Witness | 9.0.0.0 / 24755428 | 9.1.0.0 / 25370925 | `[S3]` `[S16]` |
| vSAN File Services | 9.0.0.0 / 24755229 | 9.1.0.0 / 25370922 | `[S3]` `[S16]` |
| NSX | 9.0.0.0 / 24733065 | 9.1.0.0 / 25318225 | `[S3]` `[S16]` |
| Hypervisor product name | "VMware ESX" in BOM; docs mix ESX/ESXi prose | "ESX" in BOM and used throughout what's-new prose | `[S3]` `[S5]` `[S16]` `[S1]` |
| REST base path | `/api` (port 443); `/rest` deprecated, pre-7.0.2 ops only | identical wording, unchanged | `[S8]` `[S18]` |
| Session auth | `POST /api/cis/session` → `vmware-api-session-id`; SAML/JWT federation; **non-federated user/pass logins blocked** | same session model, **plus OAuth 2.0 token support** in vCenter and PowerCLI | `[S10]` `[S11]` `[S5]` `[S1]` `[S20]` |
| New vCenter APIs | `com.vmware.vcenter.authorization` package; VM-customization pre-check; full GOSC vAPIs; OpenAPI 3.0 across vCenter+vSAN | **Query API**, **Utilization API**, **vCenter Group Federated API (VGFA)**; Guest Customization: IPv6-only, partial network customization, **Live Network Customization** (powered-on) | `[S6]` `[S20]` `[S1]` |
| ESX provisioning at scale | Auto Deploy **deprecated** | **Zero Touch Provisioning (ZTP)** (secure UEFI + HTTPS network boot) replaces Auto Deploy | `[S5]` `[S1]` |
| VM monitor | (not stated) | **User-Level Monitor (ULM) is the default monitor for all VMs** | `[S1]` |
| Confidential computing | AMD SEV-SNP / Intel TDX introduced | SEV-SNP and TDX move **limited availability → general availability** | `[S4]` `[S1]` |
| Memory Tiering | GA (NVMe as tiered memory) | **No host reboot** to reconfigure; **RAID1 mirroring** | `[S4]` `[S1]` |
| Snapshot consolidation | "more precise tracking of the progress of consolidation tasks" | **Resumable Consolidation** for powered-on VMs | `[S4]` `[S1]` |
| vCenter patching | (not stated) | **vCenter Quick Patch**, "zero to 5 minutes of downtime" | `[S1]` |
| vCenter appliance HW version | (not stated) | upgraded **vmx-10 → vmx-17** | `[S1]` |
| vLCM baselines | **Removed** for cluster management in vCenter 9.0; deprecated overall, residual 8.x patching only | Images-only model continues; explicit baseline→image transition topic in 9.1 docs | `[S5]` `[S14]` `[S25]` |
| VCF lifecycle components | SDDC Manager + VCF Operations Fleet Management | Split into **Fleet lifecycle**, **SDDC lifecycle**, **Software depot** (each 9.1.0.0) | `[S3]` `[S16]` |
| vSAN default RAID | (not stated) | **ESA Auto RAID 6** — RAID-6 is the default RAID level | `[S22]` |
| vSAN dedupe | not listed as new | **ESA Global Deduplication** — cluster-wide, post-processing, encryption-compatible | `[S12]` `[S22]` |
| vSAN compression | not listed as new | **ESA Compression Enhancements** | `[S12]` `[S22]` |
| vSAN stretched | Stretched compute-only clusters with vSAN storage clusters | **Stretched storage across vCenter instances / across VCF deployments**; **site maintenance mode** | `[S12]` `[S22]` |
| vSAN mixed ESA/OSA mounts | not listed | **Shared vSAN Storage Cluster Support** — mount ESA and OSA clusters simultaneously | `[S22]` |
| vSAN DR / cyber recovery | Live Recovery-based DR for vSAN clusters | **Cyber recovery vSAN storage cluster** deployable from vCenter; multi-schedule snapshot retention; replication seeding | `[S12]` `[S22]` |
| vSAN CNS/CSI scale | up to 500 file shares per cluster (File Services) | **50,000 volumes per vCenter**; RWX file volumes; fast clone volumes | `[S12]` `[S22]` |
| vSAN deprecations | vSAN .NET/Perl/Ruby SDKs deprecated | product-support-notes vSAN section = **"None"** | `[S5]` `[S7]` `[S21]` |
| PowerCLI | `VMware.PowerCLI` → **`VCF.PowerCLI`** 9.0; PowerShell 5.1 deprecated | **VCF PowerCLI 9.1**: `Get-VsanEffectiveCapacity`, VPC/Transit Gateway/DHCP/IP Block cmdlets, CPU topology, NVMe/TCP, OAuth auth | `[S6]` `[S20]` |
| SDK coverage | Java + Python SDK 9.0.0.0 (vCenter, vSAN DP, SDDC Manager, VCF Installer) | Java + Python SDK add **NSX, VCF Operations, Log Management, network ops, Fleet Lifecycle, SDDC Lifecycle**; VODAP OpenAPI specs | `[S6]` `[S20]` |

---

## Lookup patterns

### A. Verified endpoint templates (vSphere Automation REST, base path `/api`)

All of the following were read off the vSphere Automation API reference. The reference's
version selector offers **9.1 (Latest)** and **9.0**, and the same resource pages render for
both — so these are tagged `[9.0+9.1]` where the 9.0-pinned URL was also confirmed to render
`[S10]` `[S26]`.

**Session / auth** `[S11]` `[9.0+9.1]`
```
POST   /api/cis/session                 # create; returns session id
GET    /api/cis/session                 # info about current token
DELETE /api/cis/session                 # invalidate
Header on all subsequent calls:  vmware-api-session-id: <token>
```

**Tasks** `[S11]` `[9.0+9.1]`
```
/api/cis/tasks                          # long-running operation tasks
```

**VM lifecycle** `[S27]` `[9.0+9.1]`
```
GET    /api/vcenter/vm
POST   /api/vcenter/vm
GET    /api/vcenter/vm/{vm}
DELETE /api/vcenter/vm/{vm}
POST   /api/vcenter/vm?action=clone
POST   /api/vcenter/vm?action=clone&vmw-task=true
POST   /api/vcenter/vm/{vm}?action=relocate
POST   /api/vcenter/vm/{vm}?action=relocate&vmw-task=true
POST   /api/vcenter/vm?action=instant-clone
POST   /api/vcenter/vm?action=register
POST   /api/vcenter/vm/{vm}?action=unregister
```
Note the **`vmw-task=true`** query parameter to run an action as a task `[S27]` `[9.0+9.1]`.

**VM power** `[S28]` `[9.0+9.1]` — the reference renders the path parameter literally as
`vm`; the template is `/api/vcenter/vm/{vm}/power`:
```
GET    /api/vcenter/vm/{vm}/power
POST   /api/vcenter/vm/{vm}/power?action=start
POST   /api/vcenter/vm/{vm}/power?action=stop
POST   /api/vcenter/vm/{vm}/power?action=suspend
POST   /api/vcenter/vm/{vm}/power?action=reset
```

**Inventory** `[S29]` `[S30]` `[S31]` `[S32]` `[S33]` `[9.0+9.1]`
```
GET    /api/vcenter/datacenter                 POST /api/vcenter/datacenter
GET    /api/vcenter/datacenter/{datacenter}    DELETE /api/vcenter/datacenter/{datacenter}
GET    /api/vcenter/cluster
GET    /api/vcenter/cluster/{cluster}
GET    /api/vcenter/host
POST   /api/vcenter/host
DELETE /api/vcenter/host/{host}
POST   /api/vcenter/host/{host}?action=connect
POST   /api/vcenter/host/{host}?action=disconnect
GET    /api/vcenter/datastore
GET    /api/vcenter/datastore/{datastore}
GET    /api/vcenter/network
```
Also present in the same group (URLs captured, endpoint tables not individually read):
`/api/vcenter/folder`, `/api/vcenter/resource-pool`,
`/api/vcenter/vm-guest-customization`, `/api/vcenter/authorization/{permissions,roles,privileges}`
`[S31]` `[9.0+9.1]`.
The concrete `filter.*` query-parameter names for the list operations are
`UNVERIFIED — could not retrieve` on the pages fetched.

**Storage policies** `[S34]` `[9.0+9.1]`
```
GET    /api/vcenter/storage/policies
POST   /api/vcenter/storage/policies?action=check-compatibility
GET    /api/vcenter/storage/policies/compliance
GET    /api/vcenter/storage/policies/compliance/vm
GET    /api/vcenter/storage/policies/vm
GET    /api/vcenter/datastore-default-policy        # group page URL confirmed [S31]
```

**Content library** `[S35]` `[S36]` `[9.0+9.1]`
Service groups (paths as printed on the group index):
```
/api/content/configuration/
/api/content/library/
/api/content/local-library/
/api/content/subscribed-library/
/api/content/library/item/
/api/content/library/item/file/
/api/content/library/item/update-session/
/api/content/library/item/download-session/
/api/content/library/subscriptions/
/api/content/library/item/changes/
```
Fully verified operation table for local libraries `[S36]`:
```
GET    /api/content/local-library/
POST   /api/content/local-library/
GET    /api/content/local-library/{libraryId}
PATCH  /api/content/local-library/{libraryId}
DELETE /api/content/local-library/{libraryId}
POST   /api/content/local-library/{libraryId}?action=force-delete
POST   /api/content/local-library/{libraryId}?action=publish
```
VM templates: group page at
`https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter-vm-template/vcenter-vm-template-library-items/`
`[S31]` `[9.0+9.1]` — endpoint table not read.

**Tags and categories** `[S11]` `[9.0+9.1]` — group index lists:
```
/api/cis-tagging/category
/api/cis-tagging/tag
/api/cis-tagging/tag-association
```
Per-operation verbs/paths for these three are `UNVERIFIED — could not retrieve`
(the `cis-tagging-*` reference pages did not render operation tables through the fetch proxy).

**vSphere Lifecycle Manager (vLCM)** — `UNVERIFIED — could not retrieve`.
The ESX Settings reference group exists at
`https://developer.broadcom.com/xapis/vsphere-automation-api/latest/esx/` with sub-groups named
"Esx Settings Clusters Software", "Esx Settings Clusters Software Drafts",
"Esx Settings Clusters Configuration", "Esx Settings Hosts Software", "Esx Settings Depots"
`[S37]` `[S38]` `[9.0+9.1]`, but none of those pages rendered a path/verb table on repeated
fetches. **Do not hard-code vLCM REST paths from this dossier** — resolve them at runtime from
the OpenAPI spec or the reference pages (see section C below). The *workflow* (draft → validate
→ compliance check → apply, plus depots and remediation settings) is documented narratively
`[S15]` `[9.0]`.

### B. Other API surfaces

**Virtual Infrastructure JSON API (VI/JSON)** `[S39]` `[9.0+9.1]` — HTTP/JSON alternative to
the SOAP/vim25 Web Services API, introduced in vCenter 8.0 U1, described with OpenAPI 3.0.
Version selector includes **9.1 (Latest)** and **9.0**. Path shape:
```
/sdk/vim25/{version}/{managedObjectType}/{moId}/{operation}
```
Verified examples:
```
GET  /sdk/vim25/9.1.0.0/ServiceInstance/ServiceInstance/content
POST /sdk/vim25/9.1.0.0/SessionManager/{moId}/Login
GET  /sdk/vim25/9.1.0.0/VirtualMachine/vm-495/config
```
This is the JSON front-end for everything that used to be SOAP/pyVmomi.

**vSAN Management API** `[S13]` `[9.0+9.1]` — SOAP/vmodl, not REST.
```
vCenter:   /vsanHealth
ESX host:  /vsan
legacy MOs (HostVsanSystem, VsanUpgradeSystem):  /sdk
```
Version selector: 9.1 (Latest), 9.0.0.0, 8.0U3 … 6.7U1.
Managed objects seen: `VsanVcClusterConfigSystem`, `VsanPerformanceManager`,
`VsanVcClusterHealthSystem`, `VsanVcDiskManagementSystem`, `VsanObjectSystem`,
`VsanIscsiTargetSystem`, `VsanCapabilitySystem`.

### C. How an agent discovers operations it doesn't know

1. **Broadcom developer portal, version-pinned URLs.** Confirmed working pattern `[S26]` `[9.0]`:
   ```
   https://developer.broadcom.com/xapis/vsphere-automation-api/{version}/{group}/{resource}/
   ```
   where `{version}` ∈ `latest` (= 9.1), `9.0`, `8.0.3`, `v8.0U2`, `v8.0U1`, `v8.0.0`,
   `v7.0U3`, `v7.0U2` … `v6.5` `[S10]`; `{group}` ∈ `cis`, `content`, `esx`, `vcenter`,
   `appliance`, `vcenter-vm-template`, … ; `{resource}` is the kebab-cased service name,
   e.g. `vcenter-cluster`, `cis-session`, `content-local-library`,
   `esx-settings-clusters-software`.
   Sibling references on the same portal:
   ```
   https://developer.broadcom.com/xapis/virtual-infrastructure-json-api/{latest|9.1|9.0|8.0.3|...}/
   https://developer.broadcom.com/xapis/vsan-management-api/{latest|9.0.0.0|8.0U3|...}/
   ```
   `[S39]` `[S13]`
   Caveat observed on 2026-07-31: many resource pages are JS-rendered and return only a
   navigation menu to a plain HTTP fetch. `vcenter-*`, `cis-session`, `content-local-library`
   rendered; `esx-settings-*` and `cis-tagging-*` did not `[S37]` `[S38]` `[S40]` `[S41]`.

2. **OpenAPI specifications shipped in the VCF SDK package** `[S42]` `[9.0]`. The docs state:
   "Under the **`specifications/vsphere`** folder reside two YAML files containing OpenAPI
   definitions", and "the **`wsdl`** folder contains per-service definition files, XSD and WSDL"
   for legacy use. The three specs identified:
   - **VI/JSON spec** — describes VIM interfaces, covering "all the former Web Services API
     categories, including EAM, PBM, SMS, SSO, VIM, and VSLM".
   - **vCenter YAML spec** — describes vSphere Automation (vAPI), "focused on the vCenter
     appliance, content library, tagging, and ESX host management".
   - **vSAN data protection YAML spec** — Snap Service for "vSAN native snapshots".
   These are obtained from the VCF SDK download rather than a public URL; the page gives no
   direct download URL `[S42]`. 9.1 adds **VODAP OpenAPI specifications** to the Java SDK `[S20]` `[9.1]`.
   Also relevant: vCenter 9.0 "adds OpenAPI 3.0 to support all vCenter and vSAN APIs" `[S6]` `[9.0]`.

3. **In-product vCenter API Explorer.** `UNVERIFIED — could not retrieve` for 9.0/9.1.
   Only vSphere **7.0 and 8.0** doc-set pages for "Working with the Developer Center" /
   "Using the API Explorer" surfaced in search `[S43]`; no 9.x page was found, and the exact
   in-vCenter URL pattern was not confirmed on any fetched 9.x page. Treat the API Explorer
   as present-but-unconfirmed and prefer the developer-portal + OpenAPI routes above.

4. **Doc-set TOC endpoint.** TechDocs pages reference a machine-readable TOC at
   `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/{9-0|9-1}/_jcr_content.toc.html`
   `[S44]` `[9.1]`. Direct `curl` to techdocs.broadcom.com was blocked by egress policy in this
   environment, so the TOC endpoint itself is `UNVERIFIED — could not retrieve`.

5. **Doc-set URL shape** (useful for guessing sibling pages), both versions `[S2]` `[S17]`:
   ```
   https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/{platform-whats-new|platform-product-support-notes|vmware-cloud-foundation-bill-of-materials}...
   https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/{what-s-new|vcf-91-product-support-notes|vmware-cloud-foundation-bill-of-materials}...
   ```
   Note the **slug differs between versions** (`platform-whats-new` in 9.0 vs `what-s-new` in 9.1;
   `vmware-cloud-foundation-90-release-notes` vs `vmware-cloud-foundation-9-1-0-0-release-notes`).
   A standalone vSphere 9.0 doc set also exists at
   `https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/9-0/...` `[S14]`.

---

## Gaps and Ambiguities

1. **Exact Basic-auth header on `POST /api/cis/session`.** The SSO-credentials walkthrough page
   (`.../authentication-mechanisms/authenticate-to-vcenter-server-with-vcenter-single-sign-on-credentials.html`)
   returned HTTP 403 from the fetch proxy on two attempts `[S19]`. The header *name* for the
   returned token (`vmware-api-session-id`) is verified `[S11]`; the request-side auth header
   string is not.

2. **Conflict on vLCM baselines.** VCF 9.0 release notes: baselines/baseline groups for cluster
   management are "no longer supported in vCenter 9.0" `[S5]`. The vSphere 9.0 product doc says
   baselines are "deprecated" and still usable to "Update and patch ESX hosts only of version
   8.x" `[S14]`. Safe reading: **do not build 9.x automation on baselines**; images only.

3. **vLCM REST endpoint paths are not verified.** The `/esx/esx-settings-*` reference pages did
   not render operation tables `[S37]` `[S38]`. An earlier fetch of the `/esx/` group index
   returned a plausible-looking path list (`/api/esx-settings/clusters/software`, `…/drafts`,
   `…/compliance`, `/api/esx-settings/depots`, …) but a follow-up fetch of the same and child
   pages explicitly reported "NONE VISIBLE", so those paths could not be corroborated and are
   **excluded from the verified section**. Note also that older vSphere used
   `/api/esx/settings/...` (slash) rather than `/api/esx-settings/...` (hyphen) — the correct
   separator for 9.x is unresolved. Resolve from the OpenAPI spec before use.

4. **Tags/categories operation tables** are unverified — only the three group paths
   (`/api/cis-tagging/category`, `/tag`, `/tag-association`) are confirmed `[S11]`.

5. **9.1's new Query API / Utilization API / vCenter Group Federated API** are named and
   described in release notes `[S1]` `[S20]` but no reference page with paths/verbs was
   retrieved. Same for the 9.1 OAuth 2.0 token endpoint.

6. **`filter.*` query parameters** for list operations (datacenters, clusters, hosts,
   datastores, networks) were not shown on the fetched pages.

7. **In-product API Explorer URL for 9.x** — not found; only 7.0/8.0 doc-set pages exist `[S43]`.

8. **ESA vs OSA defaults / OSA deprecation status in 9.x** — both witness appliances ship in
   both BOMs `[S3]` `[S16]`, and 9.1 explicitly supports mounting both `[S22]`, but the
   vSAN planning pages fetched were TOC-only and no statement of "default architecture" or
   "OSA deprecated" was retrieved for either version `[S23]` `[S45]`.
   9.1's "ESA Auto RAID 6" makes RAID-6 the default *RAID level* for ESA — that is not a
   statement about ESA being the default *architecture* `[S22]`.

9. **9.0.1 / 9.0.2 patch BOMs** were not fetched; the 9.0 figures above are the 9.0.0.0 GA BOM
   (with VCF Installer already at 9.0.2.0 in that table) `[S3]`. Per-patch ESX/vCenter release
   notes exist at `.../vmware-cloud-foundation-9-0-1-release-notes/{esx,vcenter}-9-0-1-0000.html` `[S2]`.

10. **Explicit "ESXi renamed to ESX" statement** not found in any fetched page; inferred from
    BOM component naming and consistent 9.1 prose usage `[S3]` `[S16]` `[S1]` `[S5]`.

11. **Fetch-tooling caveat.** techdocs.broadcom.com is blocked for direct `curl` by the egress
    policy in this environment; all TechDocs content was obtained via the summarizing fetch
    tool, which occasionally paraphrases. Where wording matters I have quoted; where a page
    returned only navigation I have marked the item unverified rather than inferring.

---

## Source Inventory

| ID | URL | Doc set version | Date accessed | Covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsphere.html | VCF 9.1 | 2026-07-31 | What's new in vSphere 9.1: ESX ZTP, ULM, memory tiering, guest customization APIs; vCenter Quick Patch, vmx-17, Query/Utilization/VGFA APIs, Resumable Consolidation; ESX naming |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes.html | VCF 9.0 | 2026-07-31 | 9.0 release-notes index; 9.0.1 / 9.0.2 / patch / async release-note URLs |
| S3 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.0 | 2026-07-31 | VCF 9.0 Bill of Materials (versions + builds) |
| S4 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vsphere.html | VCF 9.0 | 2026-07-31 | What's new in vSphere 9.0: HW v22, SEV-SNP/TDX, NVMe boot, Memory Tiering, GPU reservations, vGPU precopy |
| S5 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-vsphere.html | VCF 9.0 | 2026-07-31 | vSphere 9.0 deprecations and removals incl. vLCM baselines removal, blocked non-federated logins, Auto Deploy, Host Profiles, ELM, vCLS, Patch Manager APIs |
| S6 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html | VCF 9.0 | 2026-07-31 | 9.0 API/SDK/CLI what's new: OpenAPI 3.0, authorization package, Java/Python SDK 9.0.0.0, VCF.PowerCLI rename |
| S7 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/vcf-sdks-apis-and-clis-product-support-notes.html | VCF 9.0 | 2026-07-31 | 9.0 SDK deprecations/removals: vSAN Ruby/Perl/C#, Java SDK deprecation, pyVmomi removals, PowerCLI changes |
| S8 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/understanding-the-vsphere-automation-rest-api.html | VCF 9.0 | 2026-07-31 | `/api` base path, deprecated `/rest`, port 443 / 5480, HTTP verb conventions |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms.html | VCF 9.1 | 2026-07-31 | Auth mechanisms: session id, SAML, JWT, OAuth 2.0, basic auth discouraged, IdP support matrix, child page URLs |
| S10 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/ | vSphere Automation API 9.1 (latest); selector lists 9.0 | 2026-07-31 | Reference landing page: version list, `/api` base path, service categories, `POST /api/cis/session` + `vmware-api-session-id` |
| S11 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/ and .../cis/cis-session/ | 9.1 (latest) | 2026-07-31 | CIS group: session POST/GET/DELETE, `/api/cis/tasks`, `/api/cis-tagging/{category,tag,tag-association}`, error types |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vsan.html | VCF 9.0 | 2026-07-31 | What's new in vSAN 9.0 |
| S13 | https://developer.broadcom.com/xapis/vsan-management-api/latest/ | vSAN Management API 9.1 (latest); selector lists 9.0.0.0 | 2026-07-31 | vSAN API protocol (SOAP/vmodl), endpoints `/vsan`, `/vsanHealth`, `/sdk`, managed objects, version list |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/9-0/managing-host-and-cluster-lifecycle/about-vsphere-lifecycle-manager-new/vlcm-baselines-and-images.html | vSphere 9.0 (standalone doc set) | 2026-07-31 | Baselines deprecated in vSphere 9.0; residual 8.x-only patching use; images are primary |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/managing-the-lifecycle-of-hosts-and-clusters.html | VCF 9.0 | 2026-07-31 | vLCM automation workflow, host requirements, standalone-host firmware limitation, sub-topic list |
| S16 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.1 | 2026-07-31 | VCF 9.1 Bill of Materials (versions + builds) |
| S17 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes.html | VCF 9.1 | 2026-07-31 | 9.1 release-notes landing page, child URLs, "12 MAY 2026" currency note |
| S18 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/understanding-the-vsphere-automation-rest-api.html | VCF 9.1 | 2026-07-31 | 9.1 confirmation of `/api` base path, deprecated `/rest`, ports 443/5480, verb conventions |
| S19 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms/authenticate-to-vcenter-server-with-vcenter-single-sign-on-credentials.html | VCF 9.1 | 2026-07-31 | ATTEMPTED — HTTP 403 from fetch proxy on 2 attempts; content not retrieved |
| S20 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | VCF 9.1 | 2026-07-31 | 9.1 API/SDK/CLI what's new: Utilization API, VGFA, Query API, Java/Python SDK scope, VCF PowerCLI 9.1 cmdlets, Python 3.7/3.8 deprecation |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vcf-91-product-support-notes.html | VCF 9.1 | 2026-07-31 | 9.1 deprecations for ESX/vCenter; vSAN section = "None" |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsan.html | VCF 9.1 | 2026-07-31 | What's new in vSAN 9.1: Auto RAID 6, Global Dedup, compression, cross-vCenter stretched storage, site maintenance mode, cyber recovery, shared ESA+OSA, CNS scale |
| S23 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsan-deployment-administration-and-monitoring/vsan-planning-and-deployment.html | VCF 9.1 | 2026-07-31 | vSAN planning TOC (incl. "Creating a vSAN ESA Storage Cluster for Cyber Recovery"); no ESA/OSA default statement retrieved |
| S24 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/lifecycle-management.html | VCF 9.1 | 2026-07-31 | VCF 9.1 lifecycle model, software depot, VCF Operations manages ESX components and vLCM images, 5.2 upgrade prerequisite |
| S25 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment/upgrading-cloud-foundation/upgrade-the-management-domain-to-vmware-cloud-foundation-5-2/vlcm-baseline-to-vlcm-image-cluster-transition-.html | VCF 9.1 | 2026-07-31 | URL only (surfaced via search): "Transitioning from vSphere Lifecycle Manager Baselines to vSphere Lifecycle Manager Images" — page body not fetched |
| S26 | https://developer.broadcom.com/xapis/vsphere-automation-api/9.0/vcenter/vcenter-cluster/ | vSphere Automation API 9.0 | 2026-07-31 | Confirms version-pinned URL pattern renders; `GET /api/vcenter/cluster/`, `GET /api/vcenter/cluster/{cluster}` under 9.0 |
| S27 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-vm/ | 9.1 (latest) | 2026-07-31 | VM CRUD + clone/instant-clone/relocate/register/unregister paths, `vmw-task=true` |
| S28 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-vm-power/ | 9.1 (latest) | 2026-07-31 | VM power get/start/stop/suspend/reset |
| S29 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-datacenter/ | 9.1 (latest) | 2026-07-31 | Datacenter list/create/get/delete |
| S30 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-cluster/ | 9.1 (latest) | 2026-07-31 | Cluster list/get |
| S31 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/ | 9.1 (latest) | 2026-07-31 | vCenter service group index: datacenter, cluster, host, datastore, network, folder, resource-pool, vm, vm-template library items, guest customization, storage policies, datastore default policy, authorization {permissions,roles,privileges} |
| S32 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-host/ | 9.1 (latest) | 2026-07-31 | Host list/create/delete/connect/disconnect |
| S33 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-datastore/ and .../vcenter-network/ | 9.1 (latest) | 2026-07-31 | Datastore list/get; network list |
| S34 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-storage-policies/ | 9.1 (latest) | 2026-07-31 | Storage policies list, check-compatibility, compliance, compliance/vm, policies/vm |
| S35 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/content/ | 9.1 (latest) | 2026-07-31 | Content library service groups and `/api/content/...` paths |
| S36 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/content/content-local-library/ | 9.1 (latest) | 2026-07-31 | Local library full operation table incl. force-delete and publish actions |
| S37 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/esx/ | 9.1 (latest) | 2026-07-31 | ESX Settings group index (names of vLCM sub-groups); path list returned was not reproducible on re-fetch |
| S38 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/esx/esx-settings-clusters-software/ and .../esx-settings-clusters-software-drafts/ | 9.1 (latest) | 2026-07-31 | ATTEMPTED — pages returned navigation only ("NONE VISIBLE"); vLCM endpoint tables not retrieved |
| S39 | https://developer.broadcom.com/xapis/virtual-infrastructure-json-api/latest/ | VI/JSON API 9.1 (latest); selector lists 9.0 | 2026-07-31 | VI/JSON base path `/sdk/vim25/{version}/{moType}/{moId}/{operation}`, examples, version list, relationship to SOAP |
| S40 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/cis-tagging-tag/ | 9.1 (latest) | 2026-07-31 | ATTEMPTED — navigation only; tag operation table not retrieved |
| S41 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/cis-tagging-category/ | 9.1 (latest) | 2026-07-31 | ATTEMPTED — navigation only; category operation table not retrieved |
| S42 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi/openapi-specifications-for-vsphere.html | VCF 9.0 | 2026-07-31 | OpenAPI spec locations (`specifications/vsphere` folder, `wsdl` folder) and the three specs (VI/JSON, vCenter vAPI, vSAN data protection) |
| S43 | Search results on techdocs.broadcom.com for "vSphere Developer Center / API Explorer" (only 7.0 and 8.0 doc-set pages returned, e.g. https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/8-0/retrieve-apis-using-api-explorer.html) | vSphere 7.0 / 8.0 | 2026-07-31 | Evidence that no 9.x API Explorer doc page was findable |
| S44 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-in-vcf.html | VCF 9.1 | 2026-07-31 | vSphere-in-VCF landing page; reference to the `_jcr_content.toc.html` TOC endpoint |
| S45 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/vsan-deployment-administration-and-monitoring/vsan-planning-and-deployment.html | VCF 9.0 | 2026-07-31 | vSAN 9.0 planning landing page; no ESA/OSA default or deprecation statement present |
| S46 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html and .../9-1.html | VCF 9.0 / 9.1 | 2026-07-31 | Top-level doc-set section maps and section URLs (vSphere in VCF, vSAN, SDKs/APIs/CLI) |
| S47 | https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere-sdks-tools/8-0/vmware-vsphere-automation-rest-programming-guide-8-0/introduction-to-the-vsphere-automation-rest-apis/vsphere-automation-api-base-path.html | vSphere SDKs & Tools **8.0** (NOT 9.x) | 2026-07-31 | Background only: "/rest base path has been deprecated and will be removed in a future release" since vSphere 7.0 U2. Used only as corroboration; 9.x claims rest on S8/S18 |
| S48 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | 2026-07-31 | 9.1 SDK/API/CLI section index and child URLs (programming guide, PowerCLI, Web Services SDK setup) |
