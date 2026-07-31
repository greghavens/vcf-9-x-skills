# VMware Cloud Foundation 9.1 — Core Platform Dossier and 9.0 → 9.1 Delta

**Research date (all sources accessed):** 2026-07-31
**Doc set:** `vmware-cis/vcf/vcf-9-0-and-later/9-1` (TechDocs), plus `.../9-0` for baseline comparison.
**Rule applied:** every fact below is sourced to a page actually fetched during this task. Anything not retrievable is explicitly marked `UNVERIFIED — could not retrieve`.

---

## 0. Executive answer: SDDC Manager vs "VCF Fleet Manager" vs VCF Operations

### 0.1 There is no product called "VCF Fleet Manager" in 9.1

Across every 9.1 page retrieved, **no component named "VCF Fleet Manager" exists**. The name that existed in 9.0 was **"VMware Cloud Foundation Operations fleet management"** — a standalone appliance shipped as its own BOM line item [S12]. In 9.1 that appliance is gone [S4][S6][S14].

"Fleet Management" in 9.1 survives only as (a) a **documentation section name** [S9] and (b) a **feature grouping inside the VCF Operations UI** [S4]. It is not an appliance and not an API surface of its own.

> Anyone writing a 9.1 skill that says "call the VCF Fleet Manager API" is wrong. The 9.1 nouns are **fleet lifecycle** and **SDDC lifecycle** (services), fronted by the **VCF Operations** UI/API. `[9.1]`

### 0.2 What actually happened to the 9.0 fleet management appliance

> "The standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by fleet lifecycle" — 9.1 What's New, VCF Operations [S4] `[9.1]`

> "the fleet lifecycle and SDDC lifecycle components now replace the VCF Operations fleet management appliance" — Lifecycle Management in VMware Cloud Foundation, 9.1 [S14] `[9.1]`

> "completely replaces the standalone Fleet Management Appliance introduced in version 9.0. It is replaced with two new services—Fleet Lifecycle and SDDC Lifecycle—which run natively within VCF Management Services." — Broadcom KB 440630 [S18] `[9.1]`

Baseline confirming prior behavior: the **9.0 BOM lists `VMware Cloud Foundation Operations fleet management  9.0.0.0  build 24695816` as its own appliance row** [S12] `[9.0]`. The 9.1 BOM has **no such row** [S8] `[9.1]`.

### 0.3 Is SDDC Manager still present? Yes — but its UI is deprecated

**SDDC Manager still exists as a running component in 9.1.** Evidence:

- It is in the 9.1 BOM, but **merged with VCF Installer into a single row**: `VCF Installer/SDDC Manager  9.1.0.0  build 25371088` [S8] `[9.1]`. In 9.0 these were **two separate rows** — `VCF Installer 9.0.2.0 (25151285)` and `SDDC Manager 9.0.0.0 (24703748)` [S12] `[9.0]`.
- The 9.1 components page lists SDDC Manager with the role: *"Provides support for lifecycle management for ESX, vCenter, HCX, and NSX; deployment of workload domains; import of vCenter instances; configuration of vSAN stretched clusters"* [S13] `[9.1]`.
- 9.1 release notes still contain a section headed **"SDDC Manager Scale"** [S4] and NSX/Installer What's New items referencing SDDC Manager ("Out-of-band networking changes to not impact SDDC Manager") [S5][S7] `[9.1]`.
- SDDC Manager is still the **driving UI for the first steps of the 9.0.x → 9.1 upgrade** (identity broker transition, VCF Operations upgrade, SDDC Manager self-upgrade) [S15] `[9.1]`.

**But it is on a deprecation path:**

> "The SDDC Manager UI is being deprecated and will be removed in a future release. After your upgrade to VCF 9.1 completes, use VCF Operations to perform lifecycle management activities." — Upgrading to VMware Cloud Foundation 9.1 [S15] `[9.1]`

Note the precise scope: the quote deprecates the **SDDC Manager UI**, not the SDDC Manager appliance/service or its API. No retrieved 9.1 page states that the SDDC Manager *API* is deprecated. See Gaps §8.

Additional 9.1 removal inside SDDC Manager: *"All vCLS functionalities available in SDDC Manager UI and VCF Installer UI are removed"* and **"21 APIs Deprecated"** affecting "edge cluster operations, domain overlays, and system DNS/NTP configurations" [S10] `[9.1]`.

### 0.4 The correct 9.1 mental model

```
VCF Operations  ......... the single pane of glass; owns Fleet Management + Lifecycle UX
   └── VCF Management Services (NEW in 9.1) — containerized services on a common runtime
         ├── VCF services runtime .... hosting/orchestration runtime (every instance)
         ├── fleet lifecycle ........ orchestrates lifecycle ACROSS the fleet (first instance)
         ├── SDDC lifecycle ......... install/update/patch WITHIN an instance (every instance)
         ├── software depot ......... binary/OCI image store
         ├── identity broker (VIDB) . SSO / OAuth token issuance
         ├── log management, real-time metrics (+ store), telemetry
         └── Salt master / Salt RaaS . desired-state config
SDDC Manager .............. still runs; workload-domain deploy, vCenter import, vSAN stretched
                            cluster config, ESX/vCenter/HCX/NSX LCM. UI deprecated.
License server (NEW) ...... stores licenses (moved out of VCF Operations)
```

Source for the VCF Management Services table and every service description: [S13] `[9.1]`.
> "VCF 9.1 introduces VCF management services to provide unified architecture for centralized lifecycle and operational functions." [S13]
> "VCF Operations now uses the fleet lifecycle, SDDC lifecycle, and software depot components to orchestrate lifecycle operations on both fleet and instance-level components." [S14]
> "VCF 9.1 introduces a common runtime and a unified set of components for lifecycle and operational capabilities. This architecture layer is a mandatory, required part of the deployment." [S18]

### 0.5 Where did the API move? (partial answer — read the caveats)

| Question | Answer | Source |
|---|---|---|
| Does an SDDC Manager OpenAPI spec still ship in 9.1? | **Yes.** The 9.1 API spec bundle `vcf-api-specs-9.1.0.0-25372366.zip` includes **SDDC Manager (OpenAPI)** alongside VCF Operations, VCF Installer, vSphere, NSX, vSAN Data Protection | [S16] `[9.1]` |
| Are there new lifecycle APIs? | **Yes.** The same bundle adds **"SDDC Lifecycle" and "Fleet Lifecycle" (both OpenAPI)** as first-class specs | [S16] `[9.1]` |
| SDDC Manager API surface size | ~280 REST interfaces, described as "SDDC Manager (fleet management)" | [S17] `[9.1]` |
| SDK coverage change | Java + Python SDKs extended to **NSX, VCF Operations, Log Management, Fleet Lifecycle, SDDC Lifecycle**; VODAP OpenAPI specs published; Java build moved Gradle → Maven | [S6] `[9.1]` |
| 9.1 auth flow | OAuth 2.0 via **VCF Identity Broker (VIDB)** | [S19][S20] `[9.1]` |

**9.1 OAuth token exchange (verbatim steps)** [S19] `[9.1]`:
1. "Administrator creates API clients with credentials that are recorded in VIDB."
2. "Administrator requests a long-lived API refresh token from the VCF Operations UI."
3. "Automation script passes the API refresh token to VIDB and gets a bearer access token in return."
4. "Automation script uses the bearer access token to authenticate with VCF components."

Caveat from the same page: *"not all VCF components employ identical token authentication methods, but many of them start with VCF Operations and VCF Identity Broker (VIDB)."* [S19]

Corroborating 9.1 statement: *"VMware provides unified API and CLI access across most VCF components with OAuth standards-based token authentication, based on VCF Identity Broker (VIDB)."* [S20] `[9.1]`

**Prior (legacy/9.0-era) SDDC Manager auth**, from the still-published VCF API Reference Guide (which serves **VCF 5.2.4 as "Latest"**): Bearer token via the **Tokens API** — "Create a token pair"; access token valid 1 hour, refresh token valid 24 hours; Cloud Builder APIs used Basic Auth [S21]. Endpoints follow `/v1/` and `/v2/` URI prefixes, "versions incremented only for backward-incompatible changes" [S21].

**Concrete API base paths for 9.1 — `UNVERIFIED — could not retrieve`.** No retrieved 9.1 TechDocs page prints a literal base path (e.g. `https://<sddc-manager>/v1/...`) or a literal token endpoint. See Gaps §8.1. The one literal 9.1 endpoint captured anywhere was for the new vCenter Utilization API, from a VMware blog: `https://developer.broadcom.com/xapis/vsphere-automation-api/9.1/api/vcenter/utilization/connections/get/` [S22] `[9.1]`.

---

## 1. Release identity

| Fact | Value | Source |
|---|---|---|
| Product | VMware Cloud Foundation 9.1 | [S2] `[9.1]` |
| Release date | **12 MAY 2026** | [S2] `[9.1]` |
| Doc "Last Updated" on What's New | May 12, 2026 | [S3] `[9.1]` |
| Announcement (press release) | **May 5, 2026** | [S23] `[9.1]` |
| 9.0 baseline release date | **17 JUN 2025** (Build 24755599) | [S11] `[9.0]` |

Press-release headline claims [S23] `[9.1]`: up to 40% server cost reduction via memory tiering; up to 39% lower storage TCO; up to 46% lower Kubernetes operational cost; **4x faster cluster upgrades**; **2x fleet capacity (5,000 hosts)**; 2.6x Kubernetes cluster scale; zero-downtime live patching "up to 80% of use cases"; 9 Tbps threat inspection.

---

## 2. VCF 9.1 Bill of Materials `[9.1]`

Source: [S8]. All 9.1 core components are version **9.1.0.0**.

| Component | VCF | VSF | Version | Build |
|---|---|---|---|---|
| **VCF Installer/SDDC Manager** | Yes | Yes | 9.1.0.0 | 25371088 |
| ESX | Yes | Yes | 9.1.0.0 | 25370933 |
| vCenter | Yes | Yes | 9.1.0.0 | 25370922 |
| vSAN ESA Witness | Yes | Yes | 9.1.0.0 | 25370927 |
| vSAN File Services | Yes | Yes | 9.1.0.0 | 25370922 |
| vSAN OSA Witness | Yes | Yes | 9.1.0.0 | 25370925 |
| NSX | — | — | 9.1.0.0 | 25318225 |
| VCF Operations | Yes | Yes | 9.1.0.0 | 25346025 |
| **Cloud proxy** | Yes | Yes | 9.1.0.0 | 25346033 |
| **License server** | Yes | Yes | 9.1.0.0 | 25346031 |
| VCF Operations for networks | — | — | 9.1.0.0 | 25318550 |
| VCF Operations HCX | — | — | 9.1.0.0 | 25318520 |
| VCF Operations orchestrator | Yes | Yes | 9.1.0.0 | 25346069 |
| VCF Automation | — | — | 9.1.0.0 | 25370929 |
| Supervisor | Yes | Yes | 9.1.0.0 | 25370922 |

Additional rows present in the same main table [S8] `[9.1]`: **Fleet lifecycle, Identity broker, Log management, Real-time metrics, Real-time metrics store, Salt RaaS, Salt master, SDDC lifecycle, Software depot, Telemetry, VCF services runtime**, plus VKS Standard Packages, vSphere Kubernetes releases, VMware vSphere Kubernetes Service, VCF Download Tool, VMware Remote Console, VMware Tools, VCF Consumption CLI variants.

Explicit row presence/absence check [S8] `[9.1]`:
- `Fleet lifecycle` — **EXISTS**
- `Identity broker` — **EXISTS**
- `Log management` — **EXISTS**
- `collector` — **DOES NOT EXIST** (replaced by `Cloud proxy`)
- `fleet management` — **DOES NOT EXIST**
- `VCF Operations for logs` — **DOES NOT EXIST** as a separate row (now `Log management`)

Other 9.1 BOM tables [S8]: **Supervisor Services** (Harbor, Argo CD, CA cluster issuer, Contour, External DNS, Supervisor Management Proxy); **VCF Services** (Secret Store Service, Migration service engine, VKS Cluster Management, Configuration Service, DSM Data Services, Encryption Management, Metrics Aggregator Package, Protection and Recovery, Harbor); **Add-ons** (Deep learning VM, VMware Data Services Manager, Protection and Recovery, Avi Load Balancer).

`UNVERIFIED — could not retrieve`: per-row release dates; exact build numbers for the VCF Management Services rows (Fleet lifecycle, SDDC lifecycle, etc.) — the retrieved extract confirmed row existence but not their build numbers.

### 2.1 VCF 9.0 BOM (baseline) `[9.0]`

Source: [S12].

| Component | Version | Build |
|---|---|---|
| VCF Installer | 9.0.2.0 | 25151285 |
| VMware ESX | 9.0.0.0 | 24755229 |
| VMware vCenter | 9.0.0.0 | 24755230 |
| VMware vSAN ESA Witness | 9.0.0.0 | 24755427 |
| VMware vSAN File Services | 9.0.0.0 | 24755229 |
| VMware vSAN OSA Witness | 9.0.0.0 | 24755428 |
| VMware NSX | 9.0.0.0 | 24733065 |
| **SDDC Manager** | 9.0.0.0 | 24703748 |
| VCF Operations | 9.0.0.0 | 24695812 |
| VCF Operations orchestrator | 9.0.0.0 | 24674408 |
| **VCF Operations collector** | 9.0.0.0 | 24695833 |
| **VCF Operations fleet management** | 9.0.0.0 | 24695816 |
| **VCF Operations for logs** | 9.0.0.0 | 24695810 |
| VCF Operations for networks | 9.0.0.0 | 24694676 |
| VCF Operations HCX | 9.0.0.0 | 24699341 |
| VCF Automation | 9.0.0.0 | 24701403 |
| VMware vSphere Supervisor | 9.0.0.0 | 24686447 |
| VMware Kubernetes Backup & Recovery Service | 1.8.0 | 24668882 |
| VMware vSphere Kubernetes Service | 3.3.1 | N/A |
| VMware Remote Console | 13.0.0.0 | 24645870 |
| VMware Tools Async Release | 13.0.0.0 | 24696475 |
| VCF Download Tool | 9.0.1.0 | 25151284 |
| VCF Identity Broker | 9.0.0.0 | 24695128 |

Note: no **License server** row in 9.0 [S12] — it is new in 9.1 [S8].

---

## 3. What's New in 9.1, by component `[9.1]`

### 3.0 Headline capabilities (What's New landing page) [S3]
Enhanced NVMe Memory Tiering; Extended vSAN Deduplication/Compression across cluster types; vSphere Elastic Provisioning (Zero Touch) for bare metal bootstrap; **VCF Management Services as unified runtime architecture**; VKS and VM Fast-Deploy using linked clone technology; Simplified Container-as-a-Service with self-service namespace provisioning; Native Object Storage (Tech Preview) for S3 access; Live Patching for ESX for TPM-enabled hosts covering up to 80% of patches; Continuous Compliance Enforcement; On-prem Ransomware Recovery.

### 3.1 vSphere / ESX / vCenter [S5]
- **ESX install:** "Zero Touch Provisioning (ZTP), using a secure UEFI and HTTPS-based network boot to provision ESX images"
- **Memory tiering:** configuration **without host reboot**; support for **all VM types**; **software RAID mirroring** for resiliency; vSphere Client Tier 1 statistics at host/cluster level
- **Security:** Quick Boot for confidential VMs; **User-Level Monitor (ULM) as default VM monitor**; **AMD SEV-SNP and Intel TDX now generally available**
- **I/O:** NVIDIA ConnectX-7, BlueField-3, AMD MI350 with Enhanced DirectPath; Intel NIC E825 (Xeon Gen 6 / Granite Rapids-D); IOMMU virtualization for AMD hosts with DirectPath
- **Snapshots:** "Change Block Tracking (CBT) Enhancement" reducing VM unresponsiveness; resumable consolidation for powered-on VMs; disk-chain integrity detection; Max Data to Consolidate metric
- **VM management:** "Linked Clones of First Class Disk" for container storage volume provisioning
- **vCenter:** File Integrity Monitoring (runs every four hours); pre-installed logs agent persisting across upgrades; vCenter VM hardware upgraded **vmx-10 → vmx-17**; RDU on-demand prechecks + automated payload downloads; **Quick patches enabling zero to 5-minute downtime patching**; folder name limit **80 → 255 characters**; up to 20% faster ops/minute
- **vSphere Lifecycle Manager:** global remediation settings for Configuration Profile clusters; image integrity validation for customized ESX images; optimized VIB transfer
- **Storage:** VAAI-NAS Unmap for NFS v4.1; **256 hosts per NFS datastore**; NVMe dispersed namespaces for stretch clusters; iSNS for iSCSI discovery
- **DRS:** Intel QAT offload for encrypted vMotion; non-disruptive maintenance mode; streaming vMotion with adaptive host-pair distribution; **dynamic concurrency control beyond the 8-migration cluster limit**
- **APIs:** OAuth 2.0 API token support; FIPS API (tech preview); **Query API**; **vCenter Group Federated API (VGFA)**; **Utilization API**
- **ESX Host Client:** feature parity with vSphere Client for compute/storage/networking
- **vSphere Client:** GPU passthrough human-readable enumeration; VPC management (Transit Gateway, Traceflow, Live Traffic Analysis, port mirroring/SPAN, VNAC); CSV export of roles and permissions; 900-row page limit in task/event consoles

### 3.2 vSAN [S24]
vSAN ESA **Auto RAID 6** ("removing the need for manual selection"); **Cyber Recovery vSAN Storage Clusters** via vCenter Quickstart; **seeding for vSAN Replication** ("syncing only incremental changes"); tag-based VM membership for vSAN Protection Groups; multiple retention schedules for vSAN snapshots; **cyber recovery using on-premises clean room**; vSAN replication from any source site; **ESA compression enhancements**; **ESA Global Deduplication** ("cluster-wide and post-processing setting with encryption support"); RWX file volume support for VM Service VMs and multiple clusters in a vSphere Zone; fast clone volume support; **CNS/CSI scalability to 50,000 volumes per vCenter**; SMB metadata ops "up to 2 times faster"; clustered application support (Oracle RAC, WSFC); **vSAN stretched storage across vCenter instances**; shared vSAN storage cluster support (OSA + ESA); end-to-end encryption for disaggregated vSAN; automated site promotion for stretched-cluster site maintenance.

### 3.3 NSX [S25]
- **VPC networking:** AVI integration with VPC and Distributed Transit Gateway (DTGW); distributed VLAN connection support for Supervisor and VCF Automation; **"Introduction of Virtual Network Appliance in VCF 9.1"**; VLAN extension for VPC subnets; centralized TGW advanced connectivity types; multiple distributed TGWs per Project; DTGW with **EVPN VXLAN** connectivity; native **Infoblox** integration with VPC; Span definition for TGW and VPC; new VPC Connectivity Policy; VPC Services load balancer on Virtual Network Appliance; VPN on Centralized TGW; 1:N SNAT; Terraform coverage extended to TGW/VPCs
- **Edge:** new UI for Edge Node creation; Broadcom 574X/575X and Mellanox CX6 LX BM Edge datapath NIC support; Edge Control Plane Prioritization; Edge VM VLAN/MTU health check
- **Performance:** FPO hardware steering for NVIDIA accelerated NICs; Uniform Passthrough (UPT); Enhanced Direct Path I/O; EDP optimizations; GRE traffic scale for CSPs
- **Security:** non-disruptive certificate renewal for VCF components consuming NSX; RSA & SSH-ED for backup/restore; **NSX transition to Ubuntu 24.04 and chiseled containers**
- **VCF integration:** workflow to make domains VPC-ready; overlay service config in vCenter; LACP UI support on VCF workflows; **"Sharing NSX Managers between Management and Workload Domains"**
- **LCM:** VDS support for VCP Autobootstrap; **"Move NSX Edge/SVM Upgrades to the End of Upgrade Sequence"**; DPDK upgrade to 24.11
- **Brownfield/import:** **"Out-of-band networking changes to not impact SDDC Manager"**; Bare Metal Edge support in VCF import
- **VKS:** Istio Service Mesh for VKS workloads; **dual-network support for VKS cluster**
- **Other:** IPAM for Cloud Consumption; VPC distributed DHCP enhancements; Distributed Load Balancer decoupled from Distributed Firewall; dynamic BGP peering for auto-scaling apps; increased L3 networking scale; port mirroring policy API; VDS IPFIX ConnTrack module

### 3.4 VCF Installer [S7]
- **Out of Band Operations:** tasks performable in vCenter "without impacting SDDC Manager", including vSphere Distributed Switch changes, datastore modifications, manual component upgrades
- **Workload Domain without vSphere Cluster:** new workflow deploys vCenter and NSX Manager without an initial cluster; **patching/upgrades blocked until a cluster is added**
- **Convergence/import (brownfield):** existing vCenter 8.0 U2a+ with NSX Manager 4.1.2.1+; vCenter 8.0 U2a without NSX (requires manual vCenter upgrade to 9.1); vCenter with existing **NSX Federation**; **dual-stack IPv4/IPv6** environments
- **Default deployment:** "VCF 9.1 deploys standardized management services components by default, including runtime, fleet lifecycle, identity broker, and software depot"
- Native UI LACP config on VDS; dual-stack networking for management and workload domains; auto-generated complex passwords for system accounts; custom network config for VCF Operations and Automation; integrated planning workflow with resource validation

### 3.5 VCF Operations (incl. Fleet Management, Lifecycle, Licensing) [S4]

**Build → Fleet Lifecycle**
- "The standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by fleet lifecycle"
- Unified framework manages: identity broker, VCF Operations, VCF Operations for networks, real-time metrics, real-time metrics store, Salt master, Salt RaaS, VCF Automation, telemetry, SDDC lifecycle, software depot, log management, migration service engine, VCF services runtime

**Build → Domain Lifecycle Management**
- Optimized NSX Manager and vCenter maintenance window; reduced-downtime update preparation
- "NSX Edge clusters are now upgraded at the end of the domain upgrade process"
- Support for imported standalone hosts and single-host clusters
- Ability to select specific hosts during cluster upgrades
- Improved prechecks using native VCF component capabilities
- Component Versions tab shows current and target versions for all supported components

**Build → SDDC Manager Scale**
- **Maximum 5000 hosts per VCF Instance (2x increase from 9.0)**
- Streamlined DNS and NTP management at scale
- **256 simultaneous cluster upgrades**
- Revamped UI and API for brownfield imports and prechecks

**Build → other:** Prometheus support in Management Pack Builder (Developer Center); lifecycle management support for VCF Operations HCX; support for upgrading **VCF on VxRail 5.2.2 → VCF 9.1**

**Manage → License Management**
- "Automatic License File Download in Connected Mode" every 24 hours
- Override license support for individual assets (ESX hosts, vSAN clusters)
- Unified license usage reporting for ESX 8.x and 9.x
- **"Licenses are now stored in a license server, instead of in VCF Operations"**

**Manage → Fleet Management**
- **VCF Roles** with custom role creation mapping to component permissions
- SSO-centric management at identity broker level
- vCenter custom role provisioning with automatic drift remediation
- **OAuth 2.0 API tokens for secure automation**
- Identity broker migration: embedded → instance mode
- VMware Identity Manager → Identity Broker migration support
- IAM Settings for global token lifecycle and security policies
- **Symantec Identity Security Platform** as identity provider; **generic OIDC** support
- Certificate management for **VCF 5.2.x components, standalone vCenter, ESX hosts**
- Password policy management across VCF components
- Configuration management templates for vSphere Configuration Profile clusters
- Centralized vCenter tag management across the VCF fleet
- **Fleet Settings** for password policies, IAM, DNS, NTP

**Manage → Cost and Capacity:** server hardware expense management (spreadsheet interface); cost drivers extended to clusters/hosts/datacenters; customizable CPU/memory cost ratio; reclamation dashboard; application showback/chargeback; **VKS cost management + VKS chargeback models**; upfront pricing estimates in VCF Automation; tenant reports/alerts via email; bill PDF export; storage-based workload eviction; network port group support for VM placement; enhanced storage capacity visibility (vSAN, VMFS, NFS, vVol); multiple simultaneous recommendations per VM; orphaned disk identification/deletion; **what-if analysis scaling to 10,000 VMs and 200 TB**

**Manage → Orchestrator:** up to two repositories for Python and PowerShell environments; default error handler now catches errors within itself; configurable session timeout (minutes) for external instances

**Manage → Workload Mobility (HCX):** **PhotonOS appliance support deprecated (target removal VCF 10.0.0)**; **VMware Cloud Director support deprecated (target removal VCF 9.2.0)**; Windows Server 2022 guest OS customization/bulk migration; Windows Server 2022 & 2025 OS-assisted migration; **FIPS 140-3 certification for HCX**; non-disruptive certificate management via HCX Manager REST APIs; HCX ports added to DFW exclusion list; **HCX Manager deployment and upgrade via VCF Operations**; VCF Operations HCX Management Pack; VCF SSO and VCF Roles for HCX Web UI/API; WAN optimization reintroduced; appliance-less migrations within a single vCenter; non-default storage policies in cold migrations; multiple destination datastores per VM; VLAN network extension to native DVPGs; enhanced architecture for Interconnect/Network Extension appliances (default for new service meshes)

**Operate → Real-Time Metrics:** real-time or historical data on Overview page; **configurable granularity (default 20 s, minimum 2 s for ESX)**; TopN charts; **PromQL-based custom queries**; network flow exploration; CLI tool access (ipconfig, nslookup, iptables, netstat, tcpdump, route, arp, dig); notes; troubleshooting sessions saved as investigations; investigation sharing

**Operate → Findings:** automatic log bundle generation (VCF Operations cluster, management services, cloud proxies, log management, identity broker); node-level bundles; **public APIs for Findings**; vSphere HA metrics

**Operate → VCF Health:** ESX health/operational state (reachability, connectivity, hardware services, PSOD failures, utilization); vCenter health with endpoint monitoring **replacing ping checks**; **extended vCenter services list from 6 to 18**; VM Operations Task ID parameter for task backtrace; Error Stack panel; snapshot size monitoring; NSX health/operational state; vSAN cluster health + performance integration

**Operate → Log Management:** **unified log management integration within VCF Operations**; masking, filtering, forwarding, partitioning, archived log import; centralized agent configuration; **upgrade paths from VCF Operations for Logs 8.18 and 9.0**; centralized log collection config across VCF components; log volume management; standardized collection using Log Insight agent and Fluentbit

**Operate → Operations for Networks:** infrastructure visibility dashboards; NSX appliance/capability critical issues; NSX edge and ESX host networking capacity dashboards; Network Assessment and Value feature; **expanded IPFIX for VKS clusters with Antrea**; **VPC planning feature for vSphere → VPC transition**; NSX inventory enhancements incl. VPC support and **legacy dashboard deprecation**; automatic migration wave/group generation; migration plan summary

**Operate → Storage:** vSAN storage performance insights with proactive rule-based monitoring; actionable insights for performance deviations; vSAN diagnostics integration; **vSAN Effective Capacity reporting**

**Operate → Workload Monitoring:** load balancing for cloud proxies in HA-enabled collector groups; product-managed and open-source **Telegraf** agents; Data Services workload monitoring; out-of-the-box database workload monitoring

**Operate → Organizations:** enhanced monitoring of Organizations provisioned through VMware Kubernetes Service, Virtual Machine Service, Data Services

**Protect → Security and Compliance:** confidential computing capability profiling/discovery; "Confidential VM environment" visibility; **centralized audit records and audit trail investigation across VCF components**; time-sliced view for user action analysis; aggregated action summaries; **compliance assessment against VCF Security Configuration Guide and PCI DSS v4.0.1**; revamped remediation experience

### 3.6 VCF Automation [S26]
**Provider Management:** support for **vDefend Distributed Firewall and Gateway Firewall** delegation; setting for default Private VPC and Private TGW IP blocks; **support for Avi Load Balancer** with self-service and quota management; **"Multiple External Connections (Formerly Provider Gateways)"** supporting multiple exit points per organization; shared VLAN extension subnets; external IP blocks with multiple CIDRs + Infoblox IPAM; fully allocated and **multi-Supervisor region quota** for organizations.

**Organization Management:** change namespace allocation limits (day-2); **Project Content Libraries**; **Canonical Content Libraries** with Ubuntu LTS image subscriptions; shared NSX subnets within organizations; NSX Transit Gateway configurations in organizations with NAT and IPsec VPN.

**vSphere Supervisor:** the 9.1 VCF Automation What's New page defers to the *VMware vSphere Supervisor Release Notes* [S26]. Detailed Supervisor/VKS What's New content — `UNVERIFIED — could not retrieve` (separate release-notes doc set not fetched in this task). See Gaps §8.2.

### 3.7 VCF SDKs, APIs, CLIs [S6]
**New VCF APIs:** **Utilization API** (vCenter capacity/usage, active connections vs max, service request volume vs supported capacity, configurable thresholds via Advanced Settings); **vCenter Group Federated API (VGFA)** (single unified endpoint across multiple vCenter instances; activatable from VCF Operations UI post-SSO configuration); **Query API** (extension of Search Index API; server-side filtering, pagination, property selection, entity counts).

**Java SDK:** extended to **NSX, VCF Operations, Log Management, Fleet Lifecycle, SDDC Lifecycle**; VODAP OpenAPI specifications available; enhanced samples (VCF Installer, vCenter, NSX, VCF Operations, SDDC workflows); **build system migrated Gradle → Maven**; code samples delivered as a separate .ZIP.

**Python SDK:** mirrors Java SDK component additions; VODAP OpenAPI specs; samples shipped separately as .ZIP.

**PowerCLI 9.1:** new `VcfOAuthSecurityContext` parameter for VCF SSO-integrated components; `VcfApiToken` parameter; automatic VCF SSO discovery. New cmdlets: `Get-VsanEffectiveCapacity`, `New-VsanRemoteDatastore`, `Remove-VsanRemoteDatastore`, `New-VpcTransitGateway`, `Set-VpcTransitGateway`, `Remove-VpcTransitGateway`, `New-VpcGroup`, `Set-VpcGroup`, `Remove-VpcGroup`, `Remove-SddcCluster`, `Remove-SddcDomain`, `Remove-SddcHost`. Deprecations: Python 3.7/3.8 support deprecated (EOL); Python 3.13 officially supported.

Blog corroboration [S22] `[9.1]`: Real-Time Metrics APIs are **Prometheus-compatible** with native PromQL, queryable "up to 2-second" granularity across ESX, vCenter, vSAN, NSX, and work directly with Grafana. SDKs distributed via Broadcom Developer Portal, PyPI, Maven Central, PowerShell Gallery. OpenAPI specs at `brcm.tech/vcf-91-api-spec-dev`; API changelog at `brcm.tech/vcf-91-api-change-log`. PowerCLI adds `New-VcfOAuthSecurityContext`.

---

## 4. Product Support Notes — deprecations and removals in 9.1 `[9.1]`

Source: [S10].

**ESX:** USB/SD boot devices, ESX without persistent OSDATA storage, and sub-32GB system storage devices deprecated — **removed in the next major release**. Marvell/Aquantia (Atlantic) NIC drivers and AMD Solarflare 8000/X2 series adapters deprecated. Marvell E3/E4 drivers (FastLinQ 57800/57810/57811, 41000/45000 series) deprecated. Cisco VIC 1200/1300 deprecated (no Enhanced Data Path support).

**vCenter:** "Starting with vCenter 9.1, the unencrypted port 514 (UDP/TCP) is blocked for use" for syslog — migrate to port 1514 with TLS. **vSphere Cluster Services (vCLS) "deactivated by default and you cannot re-activate the capability."** IPFIX on VDS uplink port groups deprecated.

**VCF Operations for Logs:** "The OpenSSL library is no longer bundled within the agent package" as of 9.1.0 — hosts require OpenSSL 3+. "Beginning with VCF 9.1, you will not be able to use VMware Aria Operation for logs content packs" — migrate to management packs. Network Share plugin removed (FIPS incompatibility). **Direct vCenter authentication for VCF Operations login removed.**

**SDDC Manager & Installer:** "All vCLS functionalities available in SDDC Manager UI and VCF Installer UI are removed." **21 APIs deprecated**, affecting edge cluster operations, domain overlays, and system DNS/NTP configurations.

**Fleet Management:** "The standalone Management Pack Builder appliance is no longer supported or actively maintained."

**VCF APIs — removals:** Tech Preview **vStats APIs removed** (use Real Time Metrics API instead). NSX Manager API: **17 operations removed** (SHA metrics, port mirroring, node user enumeration). Provider Infrastructure APIs: **369 operations deleted** (154 GET, 56 Update, 43 Create, 42 Query). vSphere Automation API: **9 operations removed** related to Hybrid Linked Mode.

**SDKs:** PowerCLI — Python 3.7/3.8 deprecated, migration to 3.9+ required for next release. Java SDK — LTS 11, 17, 21, 25. Python SDK — 3.10–3.14.

**HCX (from [S4]):** PhotonOS appliances deprecated (target removal **VCF 10.0.0**); VMware Cloud Director support deprecated (target removal **VCF 9.2.0**).

---

## 5. Upgrade path 9.0 → 9.1 `[9.1]`

### 5.1 Supported source versions [S27]
> "VMware Cloud Foundation 5.2.x or 9.0.x to 9.1"; vSphere Foundation 5.2.x or 9.0.x to 9.1; also a distinct path for **vSphere 8 and Aria Operations 8** environments.
> "Upgrading your environment to version 9.1 requires a strict component upgrade sequence."

Four documented scenarios [S27][S28]: VCF 5.2.x → 9.1; **VCF 9.0.x → 9.1**; vSphere Foundation → 9.1; vSphere 8 + Aria Operations 8 → 9.1 (the last is scoped to "environments [that have] just vSphere and Aria Operations components and **no SDDC Manager, NSX, or other Aria components**" [S28]).

### 5.2 Prerequisites [S15][S18][S29]
- Current VCF version must be **9.0.x** [S15]
- Check the **VMware Interoperability Matrix** (`https://interopmatrix.broadcom.com/Upgrade?productId=851`) [S15]
- Before deploying VCF Management Services [S29]:
  - "Verify that all required ports are open. See VMware Ports and Protocols."
  - "Verify that your certificates are configured and use the proper Fully Qualified Domain Name (FQDN)."
  - **"Verify that VCF Operations and SDDC Manager are at version 9.1."**
  - Download install binaries for: VCF services runtime, fleet lifecycle, SDDC lifecycle, software depot, identity broker, Salt RaaS, Salt master, **license server**, telemetry
  - Obtain administrative credentials for the VCF Operations instance
  - Deploy and configure a **cloud proxy** if the environment lacks one
- A centralized **VCF License Server is now a required component** for VCF and vSphere Foundation environments [S18]
- VCF Management Services "is a mandatory, required part of the deployment" [S18]

### 5.3 Ordered sequence (9.0.x → 9.1) [S15]

| Order | Component | UI that performs it |
|---|---|---|
| 0 | VCF Identity Broker 9.0.x — transition to VCF Management Network (if on NSX overlay) | **SDDC Manager** |
| 1 | VCF Operations & cloud proxy | **SDDC Manager** |
| 6 | **SDDC Manager** (self-upgrade to 9.1) | **SDDC Manager** |
| 6 | **VCF Management Services & License Server** (deploy) | **VCF Operations** |
| 6 | License transfer | **VCF Operations** |
| 7 | VCF Identity Broker → 9.1 | **VCF Operations** |
| 8 | VCF Automation → 9.1 | **VCF Operations** |
| 9–23 | NSX, vCenter, ESX, vSAN, VMware Tools (management domain components) | **VCF Operations** |

The pivot point is order 6: **SDDC Manager drives the upgrade up to and including its own upgrade; VCF Operations drives everything after.** [S15]

Key architectural statement on the upgrade [S15]:
> "VCF 9.1 transitions the lifecycle management of VCF Operations, VCF Operations for logs, VCF Operations for networks, VCF Automation, and VCF Identity Broker to the new fleet lifecycle and SDDC lifecycle components."

And the deprecation notice [S15]:
> "The SDDC Manager UI is being deprecated and will be removed in a future release. After your upgrade to VCF 9.1 completes, use VCF Operations to perform lifecycle management activities."

### 5.4 Deploying VCF Management Services — UI path [S29]
VCF Operations UI → **Build > Lifecycle > VCF Instances** → **SDDC Manager Updates** tab → **Available Upgrades** section → click **Install Components**.

### 5.5 Known upgrade issues [S18]
Four documented problems when incorrect upgrade paths are followed: (1) upgrade binaries not appearing in VCF Operations 9.0; (2) vCenter licensing failures post-upgrade; (3) license assignment failures; (4) ESXi host upgrade sync errors during VCF Operations upgrade.

`UNVERIFIED — could not retrieve`: the full ordered step list for orders 2–5 and 9–23 individually (the retrieved page collapsed them into ranges); the 5.2.x → 9.1 sequence in detail.

---

## 6. Licensing in 9.1 `[9.1]`

Source: [S30], with [S4] for the change statement and [S31] for the 9.0 baseline.

- "Use a **VCF Operations** instance and the **VCF Business Services** console as a VI administrator to manage and assign licenses." [S30]
- **License server (new in 9.1):** "A license server is added to a VCF Operations instance to store the licenses you want to assign from this VCF Operations instance." [S30] "You must add at least one license server to each VCF Operations instance that you use for license management." [S30]
- The change: **"Licenses are now stored in a license server, instead of in VCF Operations"** [S4] — this is the explicit 9.0 → 9.1 delta.
- License server is a **required component** for VCF and vSphere Foundation [S18], and appears in the 9.1 BOM (`License server 9.1.0.0 build 25346031`) [S8] with **no equivalent row in the 9.0 BOM** [S12].
- Automatic License File Download in Connected Mode every 24 hours; **override licenses** for individual assets (ESX hosts, vSAN clusters); unified license usage reporting across ESX 8.x and 9.x [S4].
- Carried forward from 9.0 (not a 9.1 change): "Starting with version 9.0, you have one default license per product. You can split the default license into as many licenses as you need within your total purchased capacity." [S30] The 9.0 baseline: "Now, instead of 11 license keys, there are only two licenses for VCF—'VMware Cloud Foundation (cores)' and 'VMware vSAN (TiBs)'" [S31] `[9.0]`.

Licensing doc sub-pages [S30]: `/licensing/licensing-overview.html`, `/licensing/license-server-overview.html`, `/licensing/register-vcf-operations.html`, `/licensing/manage-licenses-in-the-vcf-business-services-console.html`, `/licensing/add-a-license-to-vcf-operations.html`, `/licensing/assign-a-licenses-to-a-vcenter-instance.html`, `/licensing/assign-an-addon-license-to-an-asset.html`, `/licensing/what-is-an-override-license.html`.

---

## 7. 9.0 → 9.1 Delta Table

| # | Item | 9.0 behavior / name | 9.1 behavior / name | Source(s) |
|---|---|---|---|---|
| 1 | **Fleet management appliance** | Standalone appliance: `VMware Cloud Foundation Operations fleet management 9.0.0.0 (24695816)`, separate BOM row | **Appliance eliminated.** Replaced by two containerized services, **fleet lifecycle** + **SDDC lifecycle**, running inside VCF Management Services. "The standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by fleet lifecycle" | 9.0: [S12] · 9.1: [S4][S8][S14][S18] |
| 2 | **VCF Management Services** | Did not exist | **New in 9.1.** Mandatory, unified containerized runtime hosting fleet lifecycle, SDDC lifecycle, software depot, identity broker, log management, real-time metrics (+ store), Salt master, Salt RaaS, telemetry, VCF services runtime | 9.1: [S13][S18] · absent from 9.0 BOM: [S12] |
| 3 | **SDDC Manager UI** | Primary UI for VCF lifecycle management | **"The SDDC Manager UI is being deprecated and will be removed in a future release. After your upgrade to VCF 9.1 completes, use VCF Operations to perform lifecycle management activities."** Appliance/service still runs | 9.1: [S15] · 9.0 role: [S12][S20] |
| 4 | **SDDC Manager in BOM** | Own row: `SDDC Manager 9.0.0.0 (24703748)`; VCF Installer separate at `9.0.2.0 (25151285)` | **Merged single row: `VCF Installer/SDDC Manager 9.1.0.0 (25371088)`** | 9.0: [S12] · 9.1: [S8] |
| 5 | **License storage** | Licenses stored in VCF Operations; no license server component | **"Licenses are now stored in a license server, instead of in VCF Operations."** New required `License server 9.1.0.0 (25346031)` component; at least one per VCF Operations instance | 9.0: [S12] (no row) · 9.1: [S4][S8][S18][S30] |
| 6 | **Data collector appliance** | `VMware Cloud Foundation Operations collector 9.0.0.0 (24695833)` | Renamed/replaced by **`Cloud proxy 9.1.0.0 (25346033)`**; no `collector` row exists in 9.1 | 9.0: [S12] · 9.1: [S8] |
| 7 | **Log platform** | Separate appliance `VMware Cloud Foundation Operations for logs 9.0.0.0 (24695810)` | Folded in as **`Log management`**, a VCF Management Services component: "unified log management integration within VCF Operations". Upgrade paths from VCF Operations for Logs 8.18 and 9.0 | 9.0: [S12] · 9.1: [S4][S8][S13] |
| 8 | **Identity Broker** | `VMware Cloud Foundation Identity Broker 9.0.0.0 (24695128)` standalone | **`Identity broker`** becomes a VCF Management Services component; adds embedded→instance mode migration, VMware Identity Manager→Identity Broker migration, generic OIDC, Symantec Identity Security Platform as IdP | 9.0: [S12] · 9.1: [S4][S8][S13] |
| 9 | **Max hosts per VCF instance** | Baseline implied at half of 9.1 | **5000 hosts per VCF Instance — explicitly "2x increase from 9.0"**; 256 simultaneous cluster upgrades; press release: "doubled management capacity to 5,000 hosts", "4x faster cluster upgrades" | 9.1: [S4][S23] |
| 10 | **NSX Edge upgrade ordering** | Edge clusters upgraded earlier in the domain upgrade | **"NSX Edge clusters are now upgraded at the end of the domain upgrade process"** / "Move NSX Edge/SVM Upgrades to the End of Upgrade Sequence" | 9.1: [S4][S25] |
| 11 | **Lifecycle orchestration owner** | Fleet management appliance + SDDC Manager | **"VCF Operations now uses the fleet lifecycle, SDDC lifecycle, and software depot components to orchestrate lifecycle operations on both fleet and instance-level components."** VCF 9.1 "transitions the lifecycle management of VCF Operations, VCF Operations for logs, VCF Operations for networks, VCF Automation, and VCF Identity Broker to the new fleet lifecycle and SDDC lifecycle components" | 9.1: [S14][S15] |
| 12 | **API/SDK component coverage** | Narrower SDK coverage | Java & Python SDKs extended to **NSX, VCF Operations, Log Management, Fleet Lifecycle, SDDC Lifecycle**; new **Fleet Lifecycle** and **SDDC Lifecycle** OpenAPI specs ship in the 9.1 spec bundle | 9.1: [S6][S16] |
| 13 | **API auth** | SDDC Manager Tokens API bearer pair (access 1 h / refresh 24 h); Cloud Builder Basic Auth (per still-published API reference at v5.2.4) | **OAuth 2.0 via VCF Identity Broker (VIDB)**: admin creates API clients in VIDB → requests long-lived API refresh token from VCF Operations UI → script exchanges it at VIDB for a short-lived bearer access token. PowerCLI adds `VcfOAuthSecurityContext` / `VcfApiToken` | legacy: [S21] · 9.1: [S4][S6][S19][S20] |
| 14 | **vCLS** | Available; manageable from SDDC Manager and VCF Installer UIs | **"deactivated by default and you cannot re-activate the capability"**; "All vCLS functionalities available in SDDC Manager UI and VCF Installer UI are removed" | 9.1: [S10] |
| 15 | **SDDC Manager APIs** | Full API set | **21 APIs deprecated** (edge cluster operations, domain overlays, system DNS/NTP config) | 9.1: [S10] |
| 16 | **vStats APIs** | Tech Preview vStats APIs present | **Removed** — "use Real Time Metrics API instead" | 9.1: [S10] |
| 17 | **Provider Infrastructure APIs** | Larger surface | **369 operations deleted** (154 GET, 56 Update, 43 Create, 42 Query) | 9.1: [S10] |
| 18 | **NSX Manager API** | — | **17 operations removed** (SHA metrics, port mirroring, node user enumeration) | 9.1: [S10] |
| 19 | **VCF Operations login auth** | vCenter authentication supported for VCF Operations login | **Direct vCenter authentication removed** | 9.1: [S10] |
| 20 | **Aria Ops for Logs content packs** | Supported | **"Beginning with VCF 9.1, you will not be able to use VMware Aria Operation for logs content packs"** — migrate to management packs | 9.1: [S10] |
| 21 | **Management Pack Builder** | Standalone appliance | **"no longer supported or actively maintained"**; Management Pack Builder gains Prometheus support inside Developer Center | 9.1: [S4][S10] |
| 22 | **vCenter syslog port 514** | Usable | **"Starting with vCenter 9.1, the unencrypted port 514 (UDP/TCP) is blocked for use"** — use 1514 with TLS | 9.1: [S10] |
| 23 | **Installer default deployment** | Did not deploy management services | **"VCF 9.1 deploys standardized management services components by default, including runtime, fleet lifecycle, identity broker, and software depot"** | 9.1: [S7] |
| 24 | **Out-of-band vCenter operations** | Out-of-band changes disruptive to SDDC Manager | Tasks performable in vCenter "without impacting SDDC Manager" (VDS changes, datastore modifications, manual component upgrades); "Out-of-band networking changes to not impact SDDC Manager" | 9.1: [S7][S25] |
| 25 | **Workload domain creation** | Required an initial vSphere cluster | New workflow deploys **vCenter and NSX Manager without an initial vSphere cluster**; patching/upgrades blocked until a cluster is added | 9.1: [S7] |
| 26 | **VCF Automation "Provider Gateways"** | Named **Provider Gateways** | Renamed: **"Multiple External Connections (Formerly Provider Gateways)"**, now supporting multiple exit points per organization | 9.1: [S26] |
| 27 | **Memory tiering** | Required host reboot to configure; limited VM support | Configurable **without host reboot**; **all VM types**; **software RAID mirroring**; vSphere Client Tier 1 statistics UI | 9.1: [S3][S5] |
| 28 | **AMD SEV-SNP / Intel TDX** | Not GA | **Generally available** | 9.1: [S5] |
| 29 | **vCenter appliance VM hardware** | vmx-10 | **vmx-17** | 9.1: [S5] |
| 30 | **vCenter folder name limit** | 80 characters | **255 characters** (for NSX compatibility) | 9.1: [S5] |
| 31 | **vCenter health monitoring** | Ping checks; 6 services tracked | Endpoint monitoring **replacing ping checks**; **service list extended from 6 to 18** | 9.1: [S4] |
| 32 | **VCF Ops for Networks NSX dashboards** | Legacy dashboards present | **Legacy dashboard deprecation**; new VPC support in NSX inventory | 9.1: [S4] |
| 33 | **HCX lifecycle** | Managed separately | **HCX Manager deployment and upgrade via VCF Operations**; VCF Operations HCX Management Pack; VCF SSO/VCF Roles for HCX UI+API; FIPS 140-3 certification | 9.1: [S4] |
| 34 | **HCX PhotonOS / Cloud Director** | Supported | **PhotonOS appliances deprecated (removal target VCF 10.0.0); VMware Cloud Director support deprecated (removal target VCF 9.2.0)** | 9.1: [S4] |
| 35 | **Java SDK build system** | Gradle | **Maven** | 9.1: [S6] |
| 36 | **vSAN ESA RAID-6** | Manual selection | **Auto RAID 6** — "vSAN automatically configures RAID-6, removing the need for manual selection" | 9.1: [S24] |
| 37 | **CNS/CSI volume scale** | Lower | **50,000 volumes per vCenter** | 9.1: [S24] |
| 38 | **NSX appliance OS** | Prior base OS | **Ubuntu 24.04 and chiseled containers** | 9.1: [S25] |
| 39 | **VCF on VxRail** | — | **Support for upgrading VCF on VxRail 5.2.2 to VCF 9.1** | 9.1: [S4] |
| 40 | **Log agent OpenSSL** | OpenSSL bundled in agent package | **"The OpenSSL library is no longer bundled within the agent package"** as of 9.1.0; hosts require OpenSSL 3+ | 9.1: [S10] |

**Top-10 most operationally significant deltas:** #1, #2, #3, #5, #11, #13, #4, #9, #10, #23.

---

## 8. Gaps and Ambiguities

### 8.1 API base paths and literal endpoints for 9.1 — NOT VERIFIED
No 9.1 TechDocs page retrieved in this task prints a literal REST base path (e.g. `https://<sddc-manager>/v1/domains`) or a literal token endpoint URL. `UNVERIFIED — could not retrieve`.
- The public **VCF API Reference Guide** at `developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/` still serves **VCF 5.2.4 as "Latest"** with backward versions to 3.x — it has **not** been refreshed to 9.x [S21]. Do not treat it as a 9.1 reference.
- The **VCF API Specification** portal at `developer.broadcom.com/sdks/vcf-api-specification/latest` **does** offer a `v9.1 (Latest)` selector and the downloadable bundle `vcf-api-specs-9.1.0.0-25372366.zip` (39.36 MB) containing SDDC Manager, VCF Operations, VCF Installer, vSphere, NSX, vSAN Data Protection, **SDDC Lifecycle**, and **Fleet Lifecycle** OpenAPI specs [S16]. **This zip is the authoritative source for 9.1 base paths — download and inspect it to close this gap.**
- Shortlinks cited by a VMware blog (not independently resolved in this task): `brcm.tech/vcf-91-api-spec-dev` and `brcm.tech/vcf-91-api-change-log` [S22]. `UNVERIFIED — could not retrieve` (redirect targets not fetched).

### 8.2 vSphere Supervisor / VKS "What's New" — NOT VERIFIED in detail
The 9.1 VCF Automation What's New page explicitly defers: "Refer to VMware vSphere Supervisor Release Notes for additional details" [S26]. That separate release-notes doc set was not fetched. What *is* verified from 9.1 core pages: VKS and VM Fast-Deploy using linked clone technology, simplified Container-as-a-Service with self-service namespace provisioning [S3]; Istio Service Mesh for VKS workloads and dual-network VKS cluster support [S25]; expanded IPFIX for VKS with Antrea, VKS cost management and chargeback models [S4]; `Supervisor 9.1.0.0 (25370922)` and `VMware vSphere Kubernetes Service` in the BOM [S8]; press-release claim of "2.6x increased Kubernetes cluster scale" and "up to 46% reduction in Kubernetes operational costs" [S23]. Detailed per-feature Supervisor/VKS notes: `UNVERIFIED — could not retrieve`.

### 8.3 "VCF Fleet Manager" — the name in the task brief does not exist
No retrieved 9.1 page names a component "VCF Fleet Manager". The 9.0 name was "VCF Operations fleet management" (an appliance) [S12]; the 9.1 names are "fleet lifecycle" and "SDDC lifecycle" (services) [S8][S13][S14]. "Fleet Management" persists only as a doc section [S9] and a VCF Operations UI feature group [S4]. Treat "VCF Fleet Manager" as a non-existent product name.

### 8.4 Scope of the SDDC Manager deprecation is UI-only, as written
The verified sentence deprecates the **SDDC Manager UI** [S15]. It does **not** say the appliance, service, or API is deprecated — and the SDDC Manager OpenAPI spec still ships in the 9.1 bundle [S16] with ~280 REST interfaces [S17], with only 21 specific APIs deprecated [S10]. **Do not over-claim that "SDDC Manager is gone in 9.1."** It is present, in the BOM, and drives the first half of the 9.0→9.1 upgrade [S8][S15].

### 8.5 Conflicting/absent deprecation signal across pages
The Lifecycle Management page [S14] and KB 440630 [S18] contain **no** SDDC Manager UI deprecation statement, while the Upgrading page [S15] does. The deprecation notice appears to be scoped to the upgrade documentation. Cite [S15] specifically.

### 8.6 9.1 BOM build numbers for VCF Management Services rows
Row existence for Fleet lifecycle, Identity broker, Log management, Real-time metrics, Real-time metrics store, Salt RaaS, Salt master, SDDC lifecycle, Software depot, Telemetry, VCF services runtime is confirmed [S8], but their individual build numbers were not captured. `UNVERIFIED — could not retrieve`.

### 8.7 Upgrade sequence granularity
The 9.0.x → 9.1 sequence was retrieved with orders 2–5 and 9–23 collapsed into ranges [S15]. Individual step ordering within those ranges: `UNVERIFIED — could not retrieve`. Also unverified: the full VCF 5.2.x → 9.1 sequence, and the vSphere 8 + Aria 8 → 9.1 sequence.

### 8.8 Fate of 9.0 appliances after upgrade
The "Deploy VCF Management Services" page states prerequisites and procedure but "contains no information about decommissioning, replacing, or migrating existing 9.0 VCF Operations fleet management appliances" [S29]. Whether the 9.0 fleet management / collector / for-logs appliances are auto-removed, left powered off, or require manual cleanup: `UNVERIFIED — could not retrieve`.

### 8.9 Architecture pages were thin
`overview-of-vmware-cloud-foundation-9.html` [S32] and `what-is-vmware-cloud-foundation-and-vmware-vsphere-foundation.html` [S33] are navigation hubs and did not yield SDDC Manager architecture detail. The authoritative component page is `deployment/vcf-management-appliances.html` [S13] — use that one.

### 8.10 Fetch failures encountered
- `.../release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/bill-of-materials.html` → 404 (correct slug is `vmware-cloud-foundation-bill-of-materials.html`)
- `.../release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/upgrade-sequence-to-9-1.html` → 404 (correct slug is `upgrade-sequence-to-91.html`)
- `.../9-0/release-notes/vmware-cloud-foundation-9-0-0-0-release-notes/what-s-new.html` → 404 (9.0 uses a different pattern, see §9)
- `.../administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi.html` → HTTP 429 rate limited, not retried

---

## 9. Doc tree URL patterns for 9.1 (for skill-based lookup)

### 9.1 Root pattern
```
https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/{version}/...
    {version} ∈ { "9-0", "9-1" }
```
Note the doc set is literally named `vcf-9-0-and-later` and holds **both** 9.0 and 9.1 as sibling subtrees.

### 9.2 Release notes — pattern CHANGED between 9.0 and 9.1

| | 9.0 | 9.1 |
|---|---|---|
| RN root | `.../9-0/release-notes/vmware-cloud-foundation-90-release-notes.html` | `.../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes.html` |
| What's New | `.../vmware-cloud-foundation-90-release-notes/platform-whats-new.html` | `.../vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new.html` |
| Per-component | `.../platform-whats-new/whats-new-{comp}.html` | `.../what-s-new/whats-new-{comp}.html` |
| BOM | `.../vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html` | `.../vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html` |
| Support notes | `.../platform-product-support-notes.html` | `.../vcf-91-product-support-notes.html` |
| Known issues | `.../component-specific.html` | `.../known-issues.html` |

**Gotcha:** the RN folder slug is `vmware-cloud-foundation-**90**-release-notes` for 9.0 but `vmware-cloud-foundation-**9-1-0-0**-release-notes` for 9.1. Do not pattern-match naively.

`{comp}` values (both versions): `vsphere`, `vsan`, `nsx`, `installer`, `vcf-ops`, `vcf-automation`, `vcf-cli-api-sdk`.

### 9.3 Top-level 9.1 guide slugs (all under `.../9-1/`)
`release-notes.html` · `overview-of-vmware-cloud-foundation-9.html` · `design.html` · `planning-and-preparation.html` · **`deployment.html`** (Deployment, Convergence, and Upgrade) · `licensing.html` · `building-your-private-cloud-infrastructure.html` · `vsphere-in-vcf.html` · `vsan-deployment-administration-and-monitoring.html` · `advanced-network-management.html` (NSX) · **`lifecycle-management.html`** · **`fleet-management.html`** · `infrastructure-operations.html` · `workload-monitoring-and-observability.html` · `cost-and-capacity-management.html` · `workload-mobility.html` · `security-and-compliance.html` · `vsphere-supervisor-installation-and-configuration.html` · `provider-management.html` · `organization-management.html` · `configuration-of-vmware-cloud-foundation-operations-orchestrator.html` · `building-your-cloud-applications.html` · `private-ai.html` · **`administration-sdks-cli-and-tools.html`** · `vcf-advanced-services.html` [S1]

### 9.4 High-value deep links
```
# THE component/architecture page (best single source on SDDC Manager vs mgmt services)
.../9-1/deployment/vcf-management-appliances.html

# Upgrade
.../9-1/deployment/overview-of-deploy--converge--and-upgrade.html
.../9-1/deployment/upgrading-cloud-foundation.html                    <- 9.0.x -> 9.1, has the SDDC Manager UI deprecation quote
.../9-1/deployment/upgrading-cloud-foundation/deploy-vcf-management-services.html
.../9-1/deployment/upgrading-cloud-foundation/transfer-your-licenses-after-you-upgrade-vcf-operations.html
.../9-1/deployment/upgrading-cloud-foundation/upgrade-vcf-identity-broker.html
.../9-1/deployment/converging-your-existing-vsphere-infrastructure-to-a-vcf-or-vvf-platform-.html
.../9-1/deployment/upgrading-your-vsphere-foundation-to-9-1.html
.../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/upgrade-sequence-to-91.html

# Lifecycle
.../9-1/lifecycle-management/lifecycle-management-in-vmware-cloud-foundation.html
.../9-1/lifecycle-management/binary-management-for-vmware-cloud-foundation.html
.../9-1/lifecycle-management/using-the-depot-configuration-tab.html
.../9-1/lifecycle-management/upgrade-workload-domains-to-vcf-5-2.html   <- NB: stale slug, is the 9.1 WLD upgrade page

# APIs / auth
.../9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development.html
.../9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access/token-exchange-architecture.html
.../9-1/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi/opnapi-for-sddc-manager.html
```
**Slug gotchas:** several 9.1 pages retain legacy 5.2-era slugs (`upgrade-workload-domains-to-vcf-5-2.html`, `apply-cloud-foundation-5-2-update-bundle.html`, `upgrade-the-management-domain-to-vmware-cloud-foundation-5-2.html`, `phase-3-import-and-upgrade-aria-automation-8-to-vcf-automation-9.html`). Titles are 9.1; slugs are not. Also `opnapi-for-sddc-manager.html` is misspelled ("opnapi") in the real URL.

### 9.5 PDF and API portals
```
PDF (9.1):  https://techdocs.broadcom.com/content/dam/broadcom/techdocs/us/en/pdf/vmware/vcf/vcf-90/vmware-cloud-foundation-9-1.pdf
PDF (9.0):  https://techdocs.broadcom.com/content/dam/broadcom/techdocs/us/en/pdf/vmware/vcf/vcf-90/vmware-cloud-foundation-9-0.pdf
            (note: both live under the .../vcf/vcf-90/ path)
API specs:  https://developer.broadcom.com/sdks/vcf-api-specification/latest   <- has v9.1 selector; download vcf-api-specs-9.1.0.0-25372366.zip
API ref:    https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/   <- STALE, serves 5.2.4
vSphere:    https://developer.broadcom.com/xapis/vsphere-automation-api/9.1/
IdB API:    https://developer.broadcom.com/xapis/vmware-identity-broker/latest/
BizSvcs:    https://developer.broadcom.com/xapis/vcf-business-services-console-apis/latest/
Java SDK:   https://developer.broadcom.com/vcf-java-sdk
Python SDK: https://developer.broadcom.com/vcf-python-sdk
Interop:    https://interopmatrix.broadcom.com/Upgrade?productId=851
```

---

## 10. Source Inventory

| ID | URL | Doc set / version | Date accessed | Covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | 2026-07-31 | 9.1 doc tree / top-level guide slugs |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes.html | VCF 9.1 RN | 2026-07-31 | Release date 12 MAY 2026; RN section map; sub-page URLs |
| S3 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new.html | VCF 9.1 RN | 2026-07-31 | Headline 9.1 capabilities; per-component link map |
| S4 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-ops.html | VCF 9.1 RN | 2026-07-31 | **Fleet Management Appliance removal**; fleet lifecycle; SDDC Manager scale 5000 hosts; license server; Fleet Mgmt features; HCX; logs; health |
| S5 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsphere.html | VCF 9.1 RN | 2026-07-31 | vSphere/ESX/vCenter What's New; new APIs |
| S6 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | VCF 9.1 RN | 2026-07-31 | New APIs; Java/Python SDK coverage incl. Fleet+SDDC Lifecycle; PowerCLI 9.1 |
| S7 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-installer.html | VCF 9.1 RN | 2026-07-31 | Installer What's New; out-of-band ops; convergence scenarios; default mgmt services deployment |
| S8 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.1 RN | 2026-07-31 | **9.1 BOM**; VCF Installer/SDDC Manager merged row; row presence/absence checks |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/fleet-management.html | VCF 9.1 | 2026-07-31 | Fleet Management doc section scope; "Use VCF Operations as a VI administrator…" |
| S10 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vcf-91-product-support-notes.html | VCF 9.1 RN | 2026-07-31 | **All 9.1 deprecations/removals**: vCLS, port 514, 21 SDDC Mgr APIs, vStats, 369 provider ops, content packs |
| S11 | .../9-0/release-notes/vmware-cloud-foundation-90-release-notes.html | VCF 9.0 RN | 2026-07-31 | 9.0 release date 17 JUN 2025 (build 24755599); 9.0 RN URL map |
| S12 | .../9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.0 RN | 2026-07-31 | **9.0 BOM baseline** — separate SDDC Manager, fleet management, collector, for-logs, Identity Broker rows |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment/vcf-management-appliances.html | VCF 9.1 | 2026-07-31 | **Authoritative 9.1 component list**; SDDC Manager role; VCF Management Services table |
| S14 | .../9-1/lifecycle-management/lifecycle-management-in-vmware-cloud-foundation.html | VCF 9.1 | 2026-07-31 | "fleet lifecycle and SDDC lifecycle components now replace the VCF Operations fleet management appliance" |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment/upgrading-cloud-foundation.html | VCF 9.1 | 2026-07-31 | **9.0.x→9.1 ordered upgrade sequence**; **SDDC Manager UI deprecation quote**; LCM transition statement |
| S16 | https://developer.broadcom.com/sdks/vcf-api-specification/latest | VCF API Spec v9.1 | 2026-07-31 | v9.1 selector; `vcf-api-specs-9.1.0.0-25372366.zip`; includes SDDC Manager, SDDC Lifecycle, Fleet Lifecycle OpenAPI |
| S17 | .../9-1/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi/opnapi-for-sddc-manager.html | VCF 9.1 | 2026-07-31 | SDDC Manager ~280 REST interfaces; appliance description |
| S18 | https://knowledge.broadcom.com/external/article/440630/upgrade-sequence-and-related-issues-for.html | Broadcom KB 440630 (9.1) | 2026-07-31 | VCF Mgmt Services mandatory; "completely replaces the standalone Fleet Management Appliance"; license server required; 4 known upgrade issues |
| S19 | .../9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access/token-exchange-architecture.html | VCF 9.1 | 2026-07-31 | **9.1 OAuth token exchange 4-step flow**; VIDB role; refresh vs access token |
| S20 | .../9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development.html | VCF 9.1 | 2026-07-31 | "unified API and CLI access … OAuth standards-based token authentication, based on VCF Identity Broker (VIDB)" |
| S21 | https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/ | VCF API Ref — **5.2.4 "Latest"** | 2026-07-31 | Legacy SDDC Manager Tokens API auth (1 h / 24 h); `/v1/` `/v2/` prefixes; **stale, not 9.x** |
| S22 | https://blogs.vmware.com/cloud-foundation/2026/05/25/unlocking-the-full-potential-of-programmable-infrastructure-with-vmware-cloud-foundation-9-1-new-features-and-capabilities/ | VMware blog (9.1), 2026-05-25 | 2026-07-31 | Real-Time Metrics Prometheus/PromQL/Grafana; Utilization API URL; SDK distribution; spec shortlinks |
| S23 | https://news.broadcom.com/releases/broadcom-announces-vmware-cloud-foundation-9-1 | Broadcom press release, 2026-05-05 | 2026-07-31 | Announcement date; 5,000 hosts; 4x faster cluster upgrades; 40%/39%/46% claims; 2.6x K8s scale |
| S24 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsan.html | VCF 9.1 RN | 2026-07-31 | vSAN 9.1 What's New (18 items) |
| S25 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-nsx.html | VCF 9.1 RN | 2026-07-31 | NSX 9.1 What's New; Edge upgrade reordering; out-of-band SDDC Manager |
| S26 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-automation.html | VCF 9.1 RN | 2026-07-31 | VCF Automation 9.1; "Multiple External Connections (Formerly Provider Gateways)"; Supervisor deferral |
| S27 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/upgrade-sequence-to-91.html | VCF 9.1 RN | 2026-07-31 | Supported source versions (5.2.x / 9.0.x); "strict component upgrade sequence" |
| S28 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment.html | VCF 9.1 | 2026-07-31 | Deployment/convergence/upgrade sub-page map; four upgrade scenarios |
| S29 | .../9-1/deployment/upgrading-cloud-foundation/deploy-vcf-management-services.html | VCF 9.1 | 2026-07-31 | Mgmt Services deploy prerequisites; VCF Operations UI navigation path |
| S30 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/licensing.html | VCF 9.1 | 2026-07-31 | License server statements; VCF Business Services console; licensing sub-pages |
| S31 | .../9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new.html | VCF 9.0 RN | 2026-07-31 | 9.0 baseline What's New; "instead of 11 license keys, there are only two licenses" |
| S32 | .../9-1/overview-of-vmware-cloud-foundation-9.html | VCF 9.1 | 2026-07-31 | Navigation hub only — thin, see Gap 8.9 |
| S33 | .../9-1/overview-of-vmware-cloud-foundation-9/what-is-vmware-cloud-foundation-and-vmware-vsphere-foundation.html | VCF 9.1 | 2026-07-31 | VCF Operations / VCF Automation role statements; no SDDC Manager detail |
| S34 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | 2026-07-31 | SDK/API/CLI guide sub-page map |
| S35 | .../9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-ops.html | VCF 9.0 RN | 2026-07-31 | 9.0 Fleet Management feature baseline (license/IAM/cert/password/config/tag mgmt) |
| S36 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/lifecycle-management.html | VCF 9.1 | 2026-07-31 | Lifecycle Management section map; "Use VCF Operations … to manage the lifecycle" |

*(Paths shown with a leading `...` share the prefix `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.)*
