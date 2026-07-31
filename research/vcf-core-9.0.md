# VMware Cloud Foundation (VCF) 9.0 — Core Platform Research Dossier

**Research date:** 2026-07-31
**Scope:** VCF 9.0 core platform — release notes, architecture/overview, SDDC Manager, deployment/convergence/upgrade, licensing, lifecycle management, API references.
**Method:** Every claim below was retrieved from a live page fetch on 2026-07-31. Nothing is written from prior model knowledge. Version tags: `[9.0]` = verified against the 9.0-scoped doc tree; `[9.0.1]` / `[9.0.2]` = maintenance-release-specific; `[9.0+]` = page explicitly indicates applicability beyond 9.0.

> **Important scoping note on the doc tree.** The product doc set is branded "VCF 9.0 and Later" and the landing page states coverage includes 9.1 `[S1]`. However, 9.0 and 9.1 have **separate URL subtrees** (`/9-0/` and `/9-1/`) — see §7. Everything in this dossier was fetched from the `/9-0/` subtree unless stated otherwise, so it is tagged `[9.0]`.

---

## 1. Release Train and Bill of Materials

### 1.1 Release identity

- VCF 9.0 released **17 JUN 2025**, **Build 24755599** `[9.0]` `[S2]`
- VCF **9.0.1.0** released **29 SEP 2025** `[9.0.1]` `[S6]`
- VCF **9.0.2.0** released **20 JAN 2026** `[9.0.2]` `[S8]`
- 9.0.1.0 is characterized as a maintenance release whose features are "mostly focused on improving the supportability of the product," including bug and security fixes, hardware enablement changes, driver updates, and guest OS support enhancements `[9.0.1]` `[S6]`
- 9.0.2.0 is likewise a maintenance release focused on "improving the supportability of the product," with bug fixes, security updates, hardware enablement, and driver updates; components can be updated independently based on environmental impact `[9.0.2]` `[S8]`
- Additional release-note streams exist: **Patch Releases 9.0.x** and **Async Releases** (see §7 for URLs) `[9.0]` `[S3]`

### 1.2 Bill of Materials — VCF 9.0.0.0

Reproduced from the 9.0 BOM page as fetched on 2026-07-31. The "vSphere Foundation" column indicates whether the component is also part of VMware vSphere Foundation (VVF). `[9.0]` `[S4]`

| Component | In vSphere Foundation | Version | Build |
|---|---|---|---|
| VCF Installer * | Yes | 9.0.2.0 | 25151285 |
| VMware ESX | Yes | 9.0.0.0 | 24755229 |
| VMware vCenter | Yes | 9.0.0.0 | 24755230 |
| VMware vSAN ESA Witness | Yes | 9.0.0.0 | 24755427 |
| VMware vSAN File Services | Yes | 9.0.0.0 | 24755229 |
| VMware vSAN OSA Witness | Yes | 9.0.0.0 | 24755428 |
| VMware NSX | — | 9.0.0.0 | 24733065 |
| **SDDC Manager** | — | **9.0.0.0** | **24703748** |
| VCF Operations | Yes | 9.0.0.0 | 24695812 |
| VCF Operations orchestrator | Yes | 9.0.0.0 | 24674408 |
| VCF Operations collector | Yes | 9.0.0.0 | 24695833 |
| VCF Operations fleet management | — | 9.0.0.0 | 24695816 |
| VCF Operations for logs | Yes | 9.0.0.0 | 24695810 |
| VCF Operations for networks | — | 9.0.0.0 | 24694676 |
| VCF Operations HCX | — | 9.0.0.0 | 24699341 |
| VCF Automation | — | 9.0.0.0 | 24701403 |
| VMware vSphere Supervisor | Yes | 9.0.0.0 | 24686447 |
| VMware Kubernetes Backup & Recovery Service | Yes | 1.8.0 | 24668882 |
| VMware vSphere Kubernetes Service | Yes | 3.3.1 | N/A |
| VMware Remote Console | Yes | 13.0.0.0 | 24645870 |
| VMware Tools Async Release | Yes | 13.0.0.0 | 24696475 |
| VMware Cloud Foundation Download Tool | Yes | 9.0.1.0 | 25151284 |
| VMware Cloud Foundation Identity Broker | — | 9.0.0.0 | 24695128 |

**Add-ons** `[9.0]` `[S4]`

| Add-on | vSphere Foundation Add-on | Version | Build |
|---|---|---|---|
| VMware Private AI | — | 9.0.0.0 | N/A |
| VMware Data Services Manager | — | 9.0.0.0 | 24713720 |
| VMware Live Recovery | Yes | 9.0.3 | 24693627 |

> **Anomaly worth flagging to any consuming skill:** on the page as fetched 2026-07-31, the 9.0.0.0 BOM lists **VCF Installer at 9.0.2.0 / 25151285** and **VCF Download Tool at 9.0.1.0 / 25151284** — i.e. these two rows carry *later* versions than the 9.0.0.0 release itself. This is consistent with Broadcom updating the installer/downloader rows in place across the 9.0.x train, but it means a skill must **not** assume "row version == release version" for the Installer and Download Tool. `[9.0]` `[S4]`

### 1.3 Bill of Materials — VCF 9.0.1.0

`[9.0.1]` `[S7]`

| Component | In vSphere Foundation | Version | Build |
|---|---|---|---|
| VCF Installer * | Yes | 9.0.2.0 | 25151285 |
| VMware ESX | Yes | 9.0.1.0 | 24957456 |
| VMware vCenter | Yes | 9.0.1.0 | 24957454 |
| VMware vSAN ESA Witness | Yes | 9.0.1.0 | 24957987 |
| VMware vSAN File Services | Yes | 9.0.1.0 | 24957456 |
| VMware vSAN OSA Witness | Yes | 9.0.1.0 | 24957988 |
| VMware NSX | — | 9.0.1.0 | 24952111 |
| **SDDC Manager** | — | **9.0.1.0** | **24962180** |
| VCF Operations | Yes | 9.0.1.0 | 24960351 |
| VCF Operations orchestrator | Yes | 9.0.1.0 | 24923009 |
| VCF Operations collector | Yes | 9.0.1.0 | 24960349 |
| VCF Operations fleet management | — | 9.0.1.0 | 24960371 |
| VCF Operations for logs | Yes | 9.0.1.0 | 24960345 |
| VCF Operations for networks | — | 9.0.1.0 | 24950933 |
| VCF Operations HCX | — | 9.0.1.0 | 24972592 |
| VCF Automation | — | 9.0.1.0 | 24965341 |
| VMware vSphere Supervisor | Yes | 9.0.1.0 | 24953340 |
| VMware Kubernetes Backup & Recovery Service | Yes | 1.82 | 24925800 |
| VMware vSphere Kubernetes Service | Yes | 3.4.1 + v1.33 | N/A |
| VMware Remote Console | Yes | 13.0.1 | 24954779 |
| VMware Tools Async Release | Yes | 13.0.5 | 24916190 |
| VCF Download Tool | Yes | 9.0.1.0 | 24962179 |
| VCF Identity Broker | — | 9.0.1.0 | 24941398 |

### 1.4 Bill of Materials — VCF 9.0.2.0

`[9.0.2]` `[S9]`

| Component | Version | Build |
|---|---|---|
| VCF Installer * | 9.0.2.0 | 25151285 |
| VMware ESX | 9.0.2.0 | 25148076 |
| VMware vCenter | 9.0.2.0 | 25148086 |
| VMware vSAN ESA Witness | 9.0.2.0 | 25160897 |
| VMware vSAN File Services | 9.0.2.0 | 25148076 |
| VMware vSAN OSA Witness | 9.0.2.0 | 25160898 |
| VMware NSX | 9.0.2.0 | 25150386 |
| **SDDC Manager** | **9.0.2.0** | **25151285** |
| VCF Operations | 9.0.2.0 | 25137838 |
| VCF Operations orchestrator | 9.0.2.0 | 25099234 |
| VCF Operations collector | 9.0.2.0 | 25137840 |
| VCF Operations fleet management | 9.0.2.0 | 25137839 |
| VCF Operations for logs | 9.0.2.0 | 25137850 |
| VCF Operations for networks | 9.0.2.0 | 25119537 |
| VCF Operations HCX | 9.0.2.0 | 25149576 |
| VCF Automation | 9.0.2.0 | 25145732 |
| VMware vSphere Supervisor | 9.0.2.0 | 24953340 |
| VMware Kubernetes Backup & Recovery Service | 1.82 | 24925800 |
| VMware vSphere Kubernetes Service | 3.4.1 + v1.33 | N/A |
| VMware Remote Console | 13.0.2 | 25127503 |
| VMware Tools Async Release | 13.0.10 | 25056151 |
| VCF Download Tool | 9.0.2.0 | 24962179 |
| VCF Identity Broker | 9.0.2.0 | 25084325 |

> Note: SDDC Manager 9.0.2.0 and VCF Installer 9.0.2.0 share build **25151285**, corroborating §3.2 (they are the same OVA/appliance in two modes). `[9.0.2]` `[S9]`

### 1.5 What's New in 9.0 (headline themes)

`[9.0]` `[S5]`

- **One interface to private cloud operations** — "VCF Operations provides a new Operate Experience" alongside VCF Installer's build capabilities, enabling "quick deployment with integrated governance."
- **One interface for a cloud consumption experience** — "VCF Automation enables IT teams and Cloud Service Providers to deliver a self-service private cloud" with integrated services spanning VMs, Kubernetes, networking, volumes, secret stores, databases, container registries, DNS, certificates, and AI workloads.
- **Run containers, VMs and traditional apps natively** — Kubernetes and virtualization integrated "out of the box, eliminating the need to assemble separate stacks."
- **Sovereign, secure and compliant as a platform** — data sovereignty support with control over data storage, processing, and access.
- **Private cloud cost transparency** — "deep cost visibility" with "out-of-the-box insights" across infrastructure, software licensing, operational expense, and physical data center costs.
- **Accessibility & security** — all components support FIPS 140-2 and 140-3; **"vCenter, ESX, and NSX run in FIPS-enabled mode by default."**
- **Licensing improvements** — see §5.

---

## 2. Architecture and Taxonomy

### 2.1 VCF object model

`[9.0]` `[S12]`

- **VCF Instance** — "Compute, storage, networking virtual infrastructure that runs business workloads." Comprises a management domain plus optional workload domains.
- **VCF Fleet** — "An environment that is managed by a single set of fleet-level management components — VCF Operations and VCF Automation." This is the highest *operational* management level.
- **VCF Private Cloud** — "The highest level of management and consumption for the underlying software-defined data center resources"; contains one or more fleets.
- **Management domain** — created during initial deployment; hosts the SDDC Manager appliance and foundational components. For the **first** instance it also hosts the fleet-level management tools.
- **Workload domain (VI workload domain)** — user-created; runs consumer applications; has its own vCenter and optionally a dedicated NSX Manager instance.
- **Composition of any VCF domain** (management or workload): one vCenter, one or more vSphere clusters with HA/DRS enabled, distributed switches, NSX Manager for networking, and shared storage.
- SDDC Manager, VCF Operations, and VCF Automation function as **management appliances** orchestrating infrastructure deployment, lifecycle management, and fleet-level automation across instances.

Hierarchy, therefore: **Private Cloud → Fleet → Instance → Domain (management | workload) → Cluster → Host** `[9.0]` `[S12]`

### 2.2 Product positioning

- VCF is positioned as enabling "public cloud scale and agility with on-premises security, resilience and performance, while lowering total cost of ownership"; the doc set is organized "across the stages in the private cloud lifecycle" `[9.0]` `[S11]`
- **VMware vSphere Foundation (VVF)** is a distinct, smaller SKU. The BOM marks which components are included in VVF (see §1.2) `[9.0]` `[S4]`. A separate overview page covers "What Is vSphere Foundation?" `[9.0]` `[S11]`

---

## 3. SDDC Manager in 9.0

### 3.1 Role, and the critical change: the UI is deprecated

This is the single most important 9.0 fact for anyone carrying 5.x-era assumptions.

- **"With VMware Cloud Foundation 9.0 the SDDC Manager UI is being deprecated. SDDC Manager workflows can now be found in VCF Operations and vSphere Client."** `[9.0]` `[S32]`
- Product support notes restate it: **"SDDC Manager UI is now deprecated, to be removed in a future major release."** `[9.0]` `[S10]`
- The upgrade guide restates it again: "SDDC Manager UI is being deprecated and will be removed in a future release. After your upgrade to VCF 9.0 is complete, use VCF Operations" for lifecycle management `[9.0]` `[S16]`
- SDDC Manager is still described as a virtual appliance that helps administrators "deploy, manage, and operate their private cloud," handling provisioning, password management, certificate installation, and patching `[9.0]` `[S34]`
- The **SDDC Manager API remains the programmatic surface** and is not deprecated wholesale — only specific API families are (see §3.3). "Currently there are about 280 interfaces in the SDDC Manager API, also available as REST commands." `[9.0]` `[S34]`

**Where SDDC Manager workflows moved** `[9.0]` `[S32]`

| Former SDDC Manager workflow | New location (9.0) |
|---|---|
| Managing licenses | VCF Operations + VCF Business Services console — `/9-0/licensing/licensing-overview.html` |
| Managing certificates | VCF Operations (Fleet Management) — `/9-0/fleet-management/certificate-management-9-0.html` |
| Managing ESX hosts | `/9-0/building-your-private-cloud-infrastructure/host-management.html` |
| Managing VCF domains | `/9-0/building-your-private-cloud-infrastructure/working-with-workload-domains.html` |
| Accounts and passwords | `/9-0/fleet-management/manage-passwords.html` |
| Backup and restore | `/9-0/fleet-management/backup-and-restore-of-cloud-foundation.html` |
| Network connectivity / VPC | vSphere Client `[S31]` |
| Stretched cluster automation | SDDC Manager **API** `[S31]` |

### 3.2 SDDC Manager and VCF Installer are the same appliance in two modes

- The VCF Installer "arrives pre-packaged with the SDDC Manager appliance within the **`VCF-SDDC-Manager-Appliance-9.x.x.ova`** file." `[9.0]` `[S14]`
- Critical operational behavior: when the VCF Installer appliance is deployed **inside** management infrastructure (on hosts forming the management domain), it automatically **"switches into SDDC Manager mode and can no longer be used in installer mode."** `[9.0]` `[S14]`
- Corroborated by the 9.0.2 BOM, where SDDC Manager and VCF Installer share build 25151285 `[9.0.2]` `[S9]`

### 3.3 SDDC Manager API — base path, auth, and workflow domains

**Security model** `[9.0]` `[S27]`
- "All APIs are secured and need an access token for invocation."
- **Bearer Authentication** scheme.
- **Access tokens valid for 1 hour; refresh tokens valid for 24 hours.**
- Tokens obtained via the Token API.

**Versioning / base path** `[9.0]` `[S27]` `[S29]`
- Endpoints follow the pattern `/<version>/resource`, e.g. `/v1/hosts`, `/v2/domains`. Both `v1` and `v2` exist for some resources.
- The API reference's example server base URL is `https://sfo-vcf01.rainpole.io/v1` — i.e. **`https://<sddc-manager-fqdn>/v1`** `[9.0]` `[S29]`

**Token endpoints (exact)** `[9.0]` `[S28]`

| Purpose | Method | Path | Content-Type | Body | Response |
|---|---|---|---|---|---|
| Create token pair | `POST` | `/v1/tokens` | `application/json` | `{"username":"…","password":"…"}` | `{"accessToken":"<JWT>","refreshToken":{"id":"<UUID>"}}` |
| Refresh access token | `PATCH` | `/v1/tokens/access-token/refresh` | `text/plain` | refresh token UUID as plain text | JWT access token (string) |
| Revoke refresh token | `DELETE` | `/v1/tokens/refresh-token` | `application/json` | refresh token UUID | `204 No Content` |

**Headers** `[9.0]` `[S28]`
- `Authorization: Bearer <accessToken>` on all subsequent calls
- `Content-Type: application/json` (or `text/plain` for the refresh PATCH)
- `Accept: application/json`

**Resource categories (workflow domains).** The 9.0 SDDC Manager API reference exposes 50+ categories `[9.0]` `[S27]`; the "latest" (9.1) reference lists 58 `[9.0+]` `[S26]`. Categories confirmed present in the **9.0** reference `[S27]`:

`Albclusters, Backup Restore, Brownfield Import, Bundles, Ceip, Certificates, Check Sets, Clusters, Compatibility Matrix, Compliance, Config Reconciler, Credentials, Depot Settings, Domains, Fips Mode Details, Flexible Product Patches, Hosts, Identity Provider Precheck, Identity Providers, License Keys, Manifests, Network Pools, Notifications, NSX T Clusters, NSX Tedge Clusters, Personalities, Product Binaries, Product Version Catalog(s), Proxy Configuration, Pscs, Releases, Repository Images, Resource Functionalities, Resource Warnings, Sddc Manager Upgradable, Sddc Managers, Sos, System, System Configuration, Target Upgrade Version, Tasks, Tokens, Trusted Certificates, Umds, Upgradables, Upgrades, Users, V Centers, V San Hcl, V Sanhealth Check, Vasa Providers, Vcf Management Components, Vcf Services, Version Aliases For Bundle Component Type`

Categories additionally present in the 9.1/"latest" reference but **not** confirmed in the 9.0 list: `Cache`, `Hcx Managers`, `SDDC Manager Configuration`, `Update vCenter FQDN` `[9.0+]` `[S26]` — a skill should treat these as 9.1-only unless verified.

This maps directly onto the task's requested workflow domains:
- **domains** → `Domains` (see §3.4)
- **clusters** → `Clusters`, `NSX T Clusters`, `NSX Tedge Clusters`, `Albclusters`
- **hosts** → `Hosts`, `Network Pools`
- **bundles** → `Bundles`, `Product Binaries`, `Repository Images`, `Depot Settings`, `Manifests`, `Releases`, `Personalities`, `Version Aliases For Bundle Component Type`
- **upgrades** → `Upgrades`, `Upgradables`, `Sddc Manager Upgradable`, `Target Upgrade Version`, `Flexible Product Patches`, `Compatibility Matrix`
- **credentials** → `Credentials`, `Users`, `Identity Providers`, `License Keys`
- **certificates** → `Certificates`, `Trusted Certificates`
- **async work** → `Tasks`, `Notifications`
- **support/diagnostics** → `Sos`, `Check Sets`, `Compliance`, `Resource Warnings`, `V San Hcl`, `V Sanhealth Check`

### 3.4 Domains API — verified endpoint inventory

From the 9.0 reference, `Domains` category `[9.0]` `[S29]`:

| Method | Path |
|---|---|
| GET | `/domains` — retrieve a list of domains |
| POST | `/domains` — create a domain |
| POST | `/domains/validations` — validate a `DomainCreationSpec` |
| GET | `/domains/{id}` |
| PATCH | `/domains/{id}` — update a domain |
| DELETE | `/domains/{id}` — remove a domain previously initialized for deletion |
| POST | `/domains/{id}/validations` — validate a `DomainUpdateSpec` |
| GET | `/domains/{id}/validations/{validationId}` |
| GET | `/domains/{id}/endpoints` |
| GET | `/domains/{id}/capabilities` |
| GET | `/domains/{id}/datacenters` |
| GET / PUT / DELETE | `/domains/{id}/tags` |
| GET | `/domains/{id}/tags/tag-manager` |
| GET | `/domains/{id}/tags/assignable-tags` |
| PATCH | `/domains/{id}/overlay` — enable overlay over management network for NSX VLAN-backed domain |
| GET | `/domains/capabilities` |
| GET | `/domains/tags` |
| POST | `/domains/{domainId}/isolation-prechecks` |
| GET | `/domains/{domainId}/isolation-prechecks/{precheckId}` |
| POST / GET | `/domains/{domainId}/datastores/queries` , `/queries/{queryId}` |
| GET | `/domains/{domainId}/datastores/criteria` , `/criteria/{name}` |
| POST / GET | `/domains/{domainId}/clusters/queries` , `/queries/{queryId}` |
| POST / GET | `/domains/{domainId}/clusters/{clusterName}/queries` , `/queries/{queryId}` |
| GET | `/domains/{domainId}/clusters/criteria` , `/criteria/{name}` |

**Notable 9.0 API pattern:** create/update operations are paired with a `validations` sub-resource — validate the spec first, poll the validation, then submit. Long-running work returns `Tasks`. `[9.0]` `[S29]`

### 3.5 Domain management operations (UI-level)

`[9.0]` `[S33]`

| Operation | Interface | Page |
|---|---|---|
| Create workload domain ("adds a logical pool of compute, network, and storage infrastructure to a VCF instance") | SDDC Manager UI (legacy path, still documented) | `…/working-with-workload-domains/deploy-a-vi-workload-domain-using-the-sddc-manager-ui.html` |
| Create workload domain via API (JSON) | VCF Operations API | `…/working-with-workload-domains/create-a-workload-domain-by-using-the-vcf-operations-api.html` |
| Import existing vCenter as a workload domain | VCF Operations | `…/working-with-workload-domains/import-an-existing-vcenter-to-create-a-workload-domain.html` |
| Delete domain | VCF Operations | `…/working-with-workload-domains/delete-a-workload-domain.html` |
| Expand domain | VCF Operations | `…/working-with-workload-domains/expand-a-workload-domain.html` |
| Shrink domain | VCF Operations | `…/working-with-workload-domains/reduce-a-workload-domain-1.html` |
| Configuration drift management (sync out-of-band vCenter/NSX changes back to SDDC Manager) | VCF Operations | `…/working-with-workload-domains/manage-workload-domain-configuration-drift-between-vcenter-server-and-sddc-manager.html` |

Other Build-phase workflows: network pool creation and expansion for host commissioning; vSAN stretched cluster deployment across availability zones; NSX Edge cluster and transit gateway configuration; VPC provisioning `[9.0]` `[S31]`

---

## 4. Deployment, Convergence, and Upgrade

### 4.1 Three paths into 9.0

VCF 9 offers three primary scenarios, driven by **VCF Installer** and **VCF Operations** `[9.0]` `[S13]`:

1. **Greenfield deployment** — "deploy a new VCF or vSphere Foundation platform on pre-installed ESX hosts."
2. **Convergence** — existing virtual infrastructure serves as "building blocks" for new platforms; requires updating components to version 9 before deploying additional infrastructure via VCF Installer.
3. **Upgrade** — existing VCF 5.x environments (with or without management components) upgrade to version 9; **management domain upgrade is mandatory**, workload domain updates optional.

### 4.2 VCF Installer

`[9.0]` `[S14]`

- "A dedicated virtual machine, that helps you plan, configure, and deploy all the required VMware Cloud Foundation and VMware vSphere Foundation components."
- Ships in `VCF-SDDC-Manager-Appliance-9.x.x.ova`.
- Functions: download and manage binaries; deploy and configure new platforms with automated workflows; leverage existing infrastructure; support **multiple platforms from a single appliance** when deployed *outside* management infrastructure.
- Supported release types: **major, minor, and maintenance releases**. **Express patch releases are NOT supported** and must be applied manually after workflows complete.
- Deployment topologies referenced: **VCF Simple** (single-node), **VCF High Availability** (multi-node), and **vSphere Foundation**. Components deployed vary by topology and include vCenter, NSX, VCF Operations, VCF Automation, and SDDC Manager.
- Mode-switch behavior: deploying inside the management domain converts it permanently into SDDC Manager mode (§3.2).
- **Replaces the Cloud Builder appliance**, which is removed in 9.0 `[9.0]` `[S10]`
- **Replaces the Deployment Parameter Worksheet**, superseded by the VCF Installer appliance UI and JSON functionality `[9.0]` `[S10]`

### 4.3 Convergence (VCF Import)

`[9.0]` `[S15]`

- Meaning: "You can use your existing virtual infrastructure as building blocks for your VCF or vSphere Foundation platforms." Transforms standalone vSphere into managed VCF via systematic upgrades plus VCF Installer automation.
- Three phases: (1) meet general and scenario-specific requirements, (2) manually upgrade components to 9.0.x, (3) run VCF Installer-driven deployment.
- **Scope caveat:** "For a VCF platform, the following configurations, requirements, and converge scenarios are applicable for your **management domain only**. You import and upgrade workload domains in VCF Operations, after you deployed the management domain."
- **Outcomes:** creation of a new VCF Fleet or a new VCF Instance within an existing fleet; automatic provisioning of missing management components; reuse of existing vCenter and ESX hosts for the management domain.

**NSX version gate** `[9.0]` `[S15]`
- **VCF 9.0.0:** only a *new* NSX 9.0 deployment during convergence; **existing NSX instances are unsupported**.
- **VCF 9.0.1 and later:** NSX instances **without Enhanced Linked Mode** support convergence.

**Prerequisites** `[9.0]` `[S15]`
- *Storage:* shared datastores accessible and writable across all cluster hosts; minimum **3 ESX hosts (vSAN)** or **2 (external storage)** for simple deployments; vSAN Stretched Clusters and two-node ROBO supported.
- *Network:* **vDS version 8.0+**; statically assigned VMkernel IPs; dedicated vMotion networks; ports per VMware standards.
- *Compute:* vCenter VM hosted on managed clusters; **fully automated DRS**; **vSphere Lifecycle Manager images (not baselines)**.

**Unsupported for convergence** `[9.0]` `[S15]`: Dell VxRail-managed clusters; vCenter instances with Enhanced Linked Mode; Cisco virtual switches; dynamically allocated VMkernel IPs.

### 4.4 Upgrade to 9.0

`[9.0]` `[S16]`

- **Supported sources:** sequential or skip-level upgrade to VCF 9.0 from **VCF 5.0 or later**. Platforms earlier than 5.0 must first reach 5.0+.
- Upgrade process depends on which VMware Aria management components are currently deployed.
- **Core components upgraded via SDDC Manager:** SDDC Manager → NSX Manager → vCenter → ESX.
- **Management components upgraded manually or deployed prior to core upgrade:** VCF Operations; VCF Operations fleet management; VCF Operations collector (deploy *after* SDDC Manager upgrade for new installations); VCF Automation (deployable as a post-upgrade task).
- Post-upgrade guidance: use **VCF Operations** for lifecycle management, since the SDDC Manager UI is deprecated.
- A documented section covers **SDDC Manager functionality limitations during an upgrade to 9.0** `[9.0]` `[S-search]` — see Gaps.

---

## 5. Licensing in 9.0

### 5.1 The model changed fundamentally

- **"Starting with version 9.0 of VMware Cloud Foundation (VCF) and VMware vSphere Foundation (vSphere Foundation), you license your environment by using a VCF Operations instance and the VMware Cloud Foundation Business Services console (vcf.broadcom.com). Subscription-based license files replace the use of the 25-character license keys."** `[9.0]` `[S17]`
- Existing 8.x environments receive license keys alongside 9.0 default licenses `[9.0]` `[S18]`

### 5.2 License types and metering units

`[9.0]` `[S18]`

| License | Type | Metering unit |
|---|---|---|
| VMware Cloud Foundation | Primary | **cores** |
| VMware vSphere Foundation | Primary | **cores** |
| VMware vSAN | Add-on | **TiB** |
| VMware Private AI Foundation with NVIDIA | Add-on | **cores** |

- "A license is an object that entitles you to use the products that you purchased subscriptions for." `[9.0]` `[S18]`
- The 9.0 What's New frames this as simplification to two primary licenses: "VMware Cloud Foundation (cores)" and "VMware vSAN (TiBs)" `[9.0]` `[S5]`
- **Default license generation:** purchasing a subscription auto-generates a default license. Example given: a VCF subscription for 500 cores grants a **500-core VCF license plus a 500 TiB vSAN license** automatically `[9.0]` `[S18]`
- One default license per product, with capacity-splitting capability `[9.0]` `[S17]`

### 5.3 Assignment model

- "Assign a **primary license to a vCenter instance**. Your other assets that are connected to that vCenter instance, **including ESX hosts, are then licensed automatically**." `[9.0]` `[S17]`
- Add-on licenses can only be assigned **after** primary licenses are assigned `[9.0]` `[S17]`
- An **override license** concept exists (dedicated doc page) `[9.0]` `[S17]`

### 5.4 Connected vs disconnected, evaluation, and compliance

- **Connected mode:** "Internet connection is not required to register but connected registration is recommended because it simplifies license management." License usage data transmits automatically to the VCF Business Services console `[9.0]` `[S18]`
- **Disconnected mode:** manually generate a usage file and upload it to the console `[9.0]` `[S18]`
- Automatic license usage submission in connected mode `[9.0]` `[S5]`
- **Evaluation mode extended to 90 days** `[9.0]` `[S5]`
- **Usage reporting cadence:** compliance requires submitting usage reports **at minimum every 180 days** `[9.0]` `[S18]`
- **Expiration behavior:** license expiration triggers a **90-day grace period**, after which management operations become restricted and **hosts disconnect from vCenter** `[9.0]` `[S18]`
- Unified fleet management via VCF Operations and the VCF Business Services console `[9.0]` `[S5]`
- Dedicated pages exist for **license sharing** and **license management for cloud service providers and hyperscalers** `[9.0]` `[S17]`

---

## 6. Lifecycle Management

### 6.1 Who owns LCM in 9.0

- **VCF Operations is the central LCM platform:** "Use VCF Operations as a VI administrator to manage the lifecycle of the management and SDDC components in VCF, including downloading binaries and updating VCF fleet and VCF Instances." `[9.0]` `[S19]`
- "Starting with VCF 9, lifecycle management of components occurs through the **VCF Operations UI**." `[9.0]` `[S21]`
- VCF Operations manages upgrades, patches, and installations for SDDC Manager, vCenter, NSX Manager, and ESX `[9.0]` `[S19]` `[S20]`

### 6.2 Split of binary ownership

`[9.0]` `[S21]`

| System | Owns binaries for |
|---|---|
| **VCF Operations fleet management** | VCF **management** components |
| **SDDC Manager** | VCF **core** components, per VCF Instance |

- The **VCF Download Tool** is "a command-line interface (CLI) utility that is designed to simplify the management of binaries and metadata" for VCF platforms `[9.0]` `[S21]`
- The standalone **UMDS** (VMware Update Manager Download Service) is deprecated and its function is **now integrated into the VCF Download Tool** `[9.0]` `[S10]`
- A `VMware Cloud Foundation Download Tool 9.0.0.0100` release note exists under Patch Releases `[9.0]` `[S3]`

### 6.3 Upgrade sequencing for maintenance releases

"When you update your VCF environment to a maintenance release version, for example, **from 9.0.0.0 to 9.0.1.0 or 9.0.2.0**, you first update your management components." `[9.0]` `[S20]`

**Order — management components first (fleet level):** `[9.0]` `[S20]`
1. VCF Operations fleet management appliance
2. VCF Operations instance
3. Remaining components (preferred order)

**Then core components, in this specified order:** `[9.0]` `[S20]`
1. **SDDC Manager**
2. **NSX**
3. **vCenter**
4. **ESX hosts**
5. **vSAN**

> Note this differs from the *upgrade-to-9.0* core ordering in §4.4 (SDDC Manager → NSX → vCenter → ESX), which omits an explicit vSAN step. A skill should treat §4.4 as the "major upgrade to 9.0" path and §6.3 as the "9.0.x maintenance update" path. `[9.0]` `[S16]` `[S20]`

### 6.4 Prerequisites

- Binaries must be downloaded to SDDC Manager before core-component LCM operations can proceed `[9.0]` `[S20]`
- `/v1/system/precheck` functionality **moved from SDDC Manager to VCF Operations** `[9.0]` `[S10]`
- The API retains `Check Sets`, `Compliance`, and domain `isolation-prechecks` resources `[9.0]` `[S27]` `[S29]`

### 6.5 LCM sub-topics

`[9.0]` `[S20]`
- Update or Patch SDDC Manager — `…/lifecycle-management/lifecycle-management-of-vcf-core-components/upgrade-sddc-manager-without-upgrading-vcf.html`
- Upgrade Core Components in VCF Domain (**flexible BOM upgrade**) — `…/flexible-bom-upgrade-in-vmware-cloud-foundation.html`
- Updating Individual Components — `…/patching-the-management-and-workload-domains.html`
- Managing vSphere Lifecycle Manager Images — `…/managing-vsphere-lifecycle-manager-images-for-vmware-cloud-foundation.html`

"Flexible BOM upgrade" and the `Flexible Product Patches` API category together indicate 9.0 supports **per-component version flexibility** rather than strict whole-BOM lockstep. `[9.0]` `[S20]` `[S27]`

---

## 7. Doc Tree Structure and URL Patterns (for skill authoring)

### 7.1 Canonical URL grammar

```
https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/{VERSION}/{GUIDE}[/{PAGE}[/{SUBPAGE}…]].html
```

- `{VERSION}` ∈ `9-0`, `9-1` (note hyphen, not dot). The product family segment is literally `vcf-9-0-and-later`. `[9.0+]` `[S1]` `[S-search]`
- Landing page for a version: `…/vcf-9-0-and-later/9-0.html`
- Guide landing page: `…/9-0/{guide}.html`, and its children live under `…/9-0/{guide}/{page}.html`
- **Slugs are semantic but frequently stale** — they often retain names from earlier releases. Examples that a skill MUST know, because guessing will fail:
  - Upgrade to 9.0 management domain → `…/deployment/upgrading-cloud-foundation/upgrade-the-management-domain-to-vmware-cloud-foundation-**5-2**.html` `[S16]`
  - Upgrade 5.x workload domains to 9.0 → `…/lifecycle-management/upgrade-workload-domains-to-vcf-**5-2**.html` `[S19]`
  - LCM of VCF *management* components → `…/lifecycle-management/**using-the-depot-configuration-tab**.html` `[S19]`
  - Overview → VCF taxonomy → `…/overview-of-vmware-cloud-foundation-9/**workload-domains-in-vmware-cloud-foundation**.html` `[S11]`
  - SDKs Developer's Setup Guide → `…/administration-sdks-cli-and-tools/**what-is-the-vsphere-web-services-sdk**.html` `[S22]`
  - Shrink a workload domain → `…/**reduce-a-workload-domain-1**.html` `[S33]`
  - OpenAPI for SDDC Manager → `…/setup-for-development-with-openapi/**opnapi**-for-sddc-manager.html` (note the typo "opnapi") `[S34]`

**Practical rule for a skill:** never construct a deep page URL by guessing the slug. Fetch the *guide landing page* (`…/9-0/{guide}.html`) and read the child links from it. Landing pages reliably enumerate their children.

### 7.2 Top-level guide index for 9.0

All under `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/` `[9.0]` `[S1]`

| # | Guide | Slug |
|---|---|---|
| 1 | Release Notes | `release-notes.html` |
| 2 | Overview | `overview-of-vmware-cloud-foundation-9.html` |
| 3 | Design | `design.html` |
| 4 | Planning and Preparation | `planning-and-preparation.html` |
| 5 | Deployment, Convergence, and Upgrade | `deployment.html` |
| 6 | Licensing | `licensing.html` |
| 7 | Building Cloud Infrastructure | `building-your-private-cloud-infrastructure.html` |
| 8 | vSphere | `vsphere-in-vcf.html` |
| 9 | vSAN | `vsan-deployment-administration-and-monitoring.html` |
| 10 | NSX | `advanced-network-management.html` |
| 11 | Lifecycle Management | `lifecycle-management.html` |
| 12 | Fleet Management | `fleet-management.html` |
| 13 | Infrastructure Operations | `infrastructure-operations.html` |
| 14 | Workload Monitoring and Observability | `workload-monitoring-and-observability.html` |
| 15 | Cost and Capacity Management | `cost-and-capacity-management.html` |
| 16 | Workload Mobility | `workload-mobility.html` |
| 17 | Security and Compliance | `security-and-compliance.html` |
| 18 | vSphere Supervisor Platform | `vsphere-supervisor-installation-and-configuration.html` |
| 19 | Provider Management | `provider-management.html` |
| 20 | Organization Management | `organization-management.html` |
| 21 | Workload Orchestration | `configuration-of-vmware-cloud-foundation-operations-orchestrator.html` |
| 22 | Building Cloud Applications | `building-your-cloud-applications.html` |
| 23 | Administration SDKs, APIs, and CLI | `administration-sdks-cli-and-tools.html` |
| 24 | Advanced Services | `vcf-advanced-services.html` |
| 25 | Documentation Legal Notice | `documentation-legal-notice-english-public.html` |

### 7.3 Release notes subtree

`[9.0]` `[S3]` `[S2]`

```
/9-0/release-notes.html
├── /release-notes/vmware-cloud-foundation-90-release-notes.html
│   ├── /overview.html
│   ├── /platform-whats-new.html
│   │   └── /platform-whats-new/whats-new-vcf-cli-api-sdk.html
│   ├── /vmware-cloud-foundation-bill-of-materials.html
│   ├── /platform-product-support-notes.html
│   └── /component-specific.html          ← Known Issues
│       └── /component-specific/vcf-sdks-apis-and-clis-known-issues.html
├── /release-notes/vmware-cloud-foundation-9-0-1-release-notes.html
│   ├── /vmware-cloud-foundation-901-bill-of-materials.html
│   ├── /vcenter-9-0-1-0000.html
│   ├── /esx-9-0-1-0000.html
│   ├── /vsan-9-0-1-0000.html
│   ├── /nsx-9-0-1-0000.html
│   ├── /vcf-installer-9-0-1-0000.html
│   ├── /vcf-operations-9-0-1-0000.html
│   └── /vcf-automation-9-0-1-0000.html
├── /release-notes/vmware-cloud-foundation-9-0-2-release-notes.html
│   └── /vmware-cloud-foundation-902-bill-of-materials.html
├── /release-notes/patch-releases-9-0-0-x.html
│   └── /patch-releases-9-0-0-x/vmware-download-tool/vcf-dt-9-0-0-0100.html
└── /release-notes/vmware-cloud-foundation-async-releases.html
```

Note the **inconsistent BOM slug pattern**: `vmware-cloud-foundation-bill-of-materials.html` (9.0), `vmware-cloud-foundation-901-bill-of-materials.html` (9.0.1), `vmware-cloud-foundation-902-bill-of-materials.html` (9.0.2). `[9.0]` `[S2]` `[S6]` `[S8]`

### 7.4 PDF of the whole doc set

`https://techdocs.broadcom.com/content/dam/broadcom/techdocs/us/en/pdf/vmware/vcf/vcf-90/vmware-cloud-foundation-9-0.pdf` `[9.0]` `[S2]`

### 7.5 Fetchability notes

- `techdocs.broadcom.com` renders fine through WebFetch. Direct `curl` from the sandbox failed (no output written) — use WebFetch.
- Landing pages return their child link lists reliably; leaf pages return body content reliably.
- `developer.broadcom.com/xapis/...` renders and returns endpoint tables.
- Rate limiting was observed (HTTP 429) on rapid successive fetches; back off ~60s.

---

## 8. API References and SDKs

### 8.1 Confirmed API reference portals

| Reference | URL | Notes |
|---|---|---|
| **SDDC Manager API** | `https://developer.broadcom.com/xapis/sddc-manager-api/latest/` (9.1) and `https://developer.broadcom.com/xapis/sddc-manager-api/9.0/` (9.0) | Both fetched and confirmed live. Category pages: `…/sddc-manager-api/9.0/{category}/` e.g. `/domains/`, `/tokens/` `[S26]` `[S27]` `[S28]` `[S29]` |
| **VCF Installer API** | `https://developer.broadcom.com/xapis/vcf-installer-api/latest/` | Confirmed live; "latest" = 9.1, with 9.0 also available. Described as handling "installation of VCF (or VVF) with new or existing components" `[S30]` |
| **VMware Cloud Foundation API** | `https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/` | Referenced from techdocs as the "main VMware Cloud Foundation API reference" `[S24]`; also surfaced by search `[S-search]`. **Not directly fetched in this task.** |
| **VCF API Specification (downloads)** | `https://developer.broadcom.com/sdks/vcf-api-specification/latest` | Confirmed live `[S35]` |
| **VCF PowerCLI** | `https://developer.broadcom.com/powercli` | `[S25]` |

**VCF Installer API resource categories** `[9.0+]` `[S30]`: Bundles, CEIP, Depot Settings, Flexible Product Patches, Proxy Configuration, Releases, System, Tasks, Tokens, Trusted Certificates, VCF Installer, VCF Services. (Fetched from `/latest/` = 9.1; a 9.0 variant exists but was not separately fetched.)

### 8.2 OpenAPI specifications

- The **VCF API Specification** download bundle exists on the Broadcom Developer Portal, covering eight components: vSphere (WSDL and OpenAPI), NSX, **SDDC Manager**, **VCF Installer**, VCF Operations, vSAN Data Protection, SDDC Lifecycle, and Fleet Lifecycle. Most are OpenAPI format. `[9.0+]` `[S35]`
- Only **9.1** was listed as downloadable at time of access: filename `vcf-api-specs-9.1.0.0-25372366.zip`, 39.36 MB, MD5 `38ec69f82cb898864cfae4474ad8cdec`. Version 9.0 is mentioned but **no 9.0 download link was visible**. `[9.0+]` `[S35]`
- GitHub mirror: `https://github.com/vmware/vcf-api-specs` `[9.0+]` `[S35]`
- Guidance: "Developers working with languages other than Java or Python… can leverage the API definitions located in the `/specifications` directory." `[9.0+]` `[S35]`
- The techdocs "OpenAPI for SDDC Manager" page confirms SDDC Manager OpenAPI support and states there are **~280 interfaces in the SDDC Manager API**, but provides **no direct spec download URL, no spec version, and no codegen examples** `[9.0]` `[S34]`

### 8.3 SDKs and CLIs new in 9.0

`[9.0]` `[S25]`

**Java SDK 9.0.0.0** (Build 24798170, released 17 June 2025)
- Channels: Broadcom Developer Portal; Maven Central (`groupId: com.vmware.sdk`); GitHub `https://github.com/vmware/vcf-sdk-java/`
- **New: SDDC Manager SDK and VCF Installer SDK**
- vSphere Management (Web Services) and Automation SDKs unified into a single deliverable; vSAN Management SDK integrated

**Python SDK 9.0.0.0** (Build 24798170, released 17 June 2025)
- Channels: Broadcom Developer Portal; PyPI `https://pypi.org/project/vcf-sdk/9.0.0.0/`; GitHub `https://github.com/vmware/vcf-sdk-python/`
- **New: SDDC Manager bindings and VCF Installer bindings**
- PyPI modules published at v9.0.0.0: `vcf-sdk`, `vcf-installer`, `pyvmomi`, `vmware-vcenter`, `vmware-sddc-manager`

**PowerCLI 9.0** (Build 24798382, released 17 June 2025)
- **Renamed: "VMware PowerCLI has been renamed to VCF PowerCLI"**
- Cmdlet load time "over 50% faster for PowerShell 5.1" and "70% for PowerShell 7.x"
- **New SDDC Manager cmdlets: `Get-SddcCluster`, `Get-SddcDomain`, `Get-SddcHost`, `Get-SddcVcenter`**
- Also: vSAN dedup properties, vSAN iSCSI VIP config, VPC support, vCenter authorization cmdlets

**VCF Consumption CLI (first release)** — context management for auth/server config; kubeconfig mapping for kubectl consistency; supports VCFA and vSphere Supervisor endpoints; auto-discovery and installation of context-scoped plugins; airgapped support. Installable via Homebrew, apt, yum, choco, and binary downloads. `[9.0]` `[S25]`

**vCenter API changes in 9.0** `[9.0]` `[S25]`
- "vCenter 9.0 adds **OpenAPI 3.0** to support all vCenter and vSAN APIs, along with the existing VI JSON and vCenter REST APIs"
- New `com.vmware.vcenter.authorization` package for REST-based privilege/role/permission configuration
- New API to verify VM customization capability before applying; guest OS customization vAPIs support all GOSC operations while systems are running

**SDK sample code** — the VCF SDK for Python (`vcf-sdk-python`) and Java (`vcf-sdk-java`) GitHub repos contain "many code examples demonstrating use cases for **SDDC Manager and VCF Import**" `[9.0]` `[S24]`

---

## 9. Deprecations, Removals, and Breaking Changes in 9.0

This section is the highest-value content for anyone migrating from 5.x. All from the 9.0 Product Support Notes unless noted. `[9.0]` `[S10]`

### 9.1 Deprecated (still present, removal planned)

| Item | Statement | Replacement |
|---|---|---|
| **SDDC Manager UI** | "SDDC Manager UI is now deprecated, to be removed in a future major release." | VCF Operations + vSphere Client |
| **SDDC Manager Identity APIs** | "SDDC Manager APIs for identity configuration are deprecated and will be removed in a future major release" | VCF Operations |
| **vCenter Enhanced Linked Mode (ELM)** | "ELM, which allows unified view and administration of multiple vCenter instances, is deprecated" | VCF Operations grouping capability |
| **vSphere Host Profiles** | "The vSphere Host Profiles capability is deprecated in vCenter 9.0 and will be removed in a future release." | vSphere Configuration Profiles |
| **VMware Aria Operations for Logs** | "now deprecated, with version 8.18 being the final release." VCF Operations 9.0 does **not** support integration with 8.18, though existing instances can forward logs | VCF Operations for Logs |
| **UMDS (standalone)** | "The standalone UMDS tool is deprecated and will be removed in a future vCenter release" | Integrated into VCF Download Tool |

### 9.2 Removed / no longer supported in 9.0

| Item | Statement | Replacement |
|---|---|---|
| **Cloud Builder appliance** | Replaced | **VCF Installer appliance** |
| **Integrated Windows Authentication (IWA)** | "vCenter 9.0 **discontinues support** for Integrated Windows Authentication" | AD over LDAPS, or Identity Federation with MFA |
| **vSphere Lifecycle Manager baselines / baseline groups** | "Managing clusters with vSphere Lifecycle Manager baselines and baseline groups (legacy vSphere Update Manager workflows) is **no longer supported** in vCenter 9.0" | vSphere Lifecycle Manager **images** |
| **Deployment Parameter Worksheet** | Replaced | VCF Installer appliance UI + JSON |
| **SDDC Manager UI for Application Virtual Networks** | "Removed and replaced by API functionality" | API, for deploying VCF Operations/Automation on NSX Segments |
| **SDDC Manager UI/API for VMware Aria Suite** | Replaced | VCF Installer and VCF Operations |
| **SDDC Manager LCM API `/v1/system/precheck`** | "functionality moved to VCF Operations" | VCF Operations |
| **SDDC Manager Bring-Up APIs** | Replaced | VCF Installer appliance |

### 9.3 Default behavior changes

- **FIPS by default:** all components support FIPS 140-2 and 140-3; "vCenter, ESX, and NSX run in FIPS-enabled mode by default" `[9.0]` `[S5]`
- **Evaluation mode extended to 90 days** `[9.0]` `[S5]`
- **License keys replaced by subscription license files** `[9.0]` `[S17]`

---

## 10. What a VCF 9.0 Core Skill Must Contain

Synthesis for skill authoring — derived from the verified content above.

1. **Lead with the 9.0 paradigm shift.** The three facts an agent must internalize before answering anything: (a) SDDC Manager **UI** is deprecated; workflows moved to VCF Operations and vSphere Client `[S32]` `[S10]`; (b) the SDDC Manager **API** remains the automation surface and is largely intact `[S27]` `[S34]`; (c) Cloud Builder is gone, replaced by **VCF Installer**, which is the *same OVA* as SDDC Manager and mode-switches `[S10]` `[S14]`.
2. **Encode the auth flow verbatim.** `POST /v1/tokens` → `{accessToken, refreshToken.id}`; `Authorization: Bearer`; 1h access / 24h refresh; `PATCH /v1/tokens/access-token/refresh` with `text/plain` body `[S28]`.
3. **Encode the validate-then-execute pattern.** `POST /domains/validations` → poll `GET /domains/{id}/validations/{validationId}` → execute → poll `Tasks` `[S29]`.
4. **Encode both upgrade orderings** and when each applies (§4.4 vs §6.3) — they differ, and conflating them is a realistic failure mode.
5. **Encode the licensing model completely** — cores/TiB units, vCenter-level assignment with automatic ESX inheritance, 90-day eval, 180-day usage reporting, 90-day expiration grace period ending in host disconnection `[S18]`.
6. **Teach URL-tree navigation, not URL guessing.** Ship the §7.2 guide table and the rule "fetch the guide landing page and read its children," plus the stale-slug examples in §7.1.
7. **Ship the BOM tables per patch level** and the caveat that VCF Installer / Download Tool rows drift ahead of the release version `[S4]`.
8. **Ship the deprecation/removal table (§9)** — this is what agents get wrong when reasoning from 5.x-era training data.
9. **Ship the API category → capability map (§3.3)** so an agent can route a natural-language request to the right resource family.
10. **Note the fetch mechanics:** WebFetch works, curl did not; back off on 429; landing pages enumerate children.

---

## 11. Gaps and Ambiguities

Items I could not verify from a fetched page, or where fetched sources conflict:

1. **`developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/` was never directly fetched.** It is referenced from techdocs `[S24]` and appeared in search results, but I did not retrieve it, so I cannot confirm its scope, version coverage, or how it differs from the SDDC Manager API reference. — `UNVERIFIED — could not retrieve`
2. **VCF Installer API base URL and token endpoints not confirmed.** A `Tokens` category exists at `…/vcf-installer-api/latest/tokens/` `[S30]`, but I did not fetch it. I therefore **cannot assert** that VCF Installer auth is identical to SDDC Manager auth. — `UNVERIFIED — could not retrieve`
3. **No 9.0 OpenAPI spec download URL confirmed.** The spec bundle page listed only 9.1 (`vcf-api-specs-9.1.0.0-25372366.zip`); 9.0 was "mentioned but no download link appears" `[S35]`. The techdocs OpenAPI-for-SDDC-Manager page gave no URL, no spec version, and no codegen commands `[S34]`. Whether SDDC Manager serves its own spec at a runtime endpoint (e.g. `/v1/api-docs`) — `UNVERIFIED — could not retrieve`
4. **`https://broadcom.net/apis/vcf-installer/latest/`** is cited on the techdocs sample-programs page as the VCF Installer API location `[S24]`, but that host differs from `developer.broadcom.com`. I did not fetch `broadcom.net` and cannot confirm it resolves. — `UNVERIFIED — could not retrieve`
5. **9.0 BOM internal inconsistency.** The 9.0.0.0 BOM lists VCF Installer at 9.0.2.0 and Download Tool at 9.0.1.0 `[S4]`; the 9.0.1.0 BOM lists Download Tool at 9.0.1.0 build 24962179 while the 9.0.0.0 BOM lists 9.0.1.0 build **25151284** `[S7]` — the same version with two different build numbers. I could not resolve which is authoritative; the pages appear to be edited in place over time.
6. **Bundle types and naming conventions not documented on pages fetched.** Both the core-components LCM page and the binary-management page explicitly lacked bundle-type definitions and depot online/offline distinctions `[S20]` `[S21]`. The API exposes `Bundles`, `Depot Settings`, `Manifests`, `Personalities`, `Repository Images` `[S27]`, but I did not fetch those category pages. — `UNVERIFIED — could not retrieve`
7. **Prechecks not enumerated.** The LCM page states prechecks exist but does not detail them `[S20]`. The `Check Sets` API category and `isolation-prechecks` endpoints exist `[S27]` `[S29]` but were not explored in depth. — partially `UNVERIFIED`
8. **Known Issues content not retrieved.** The Known Issues page URL is confirmed (`…/component-specific.html`) `[S2]` but its contents were not fetched.
9. **Design and Planning-and-Preparation guides not fetched.** Confirmed to exist `[S1]`; contents unknown — these likely hold sizing, network, and prerequisite detail relevant to deployment.
10. **Fleet Management guide not fetched.** Certificate management, password management, and backup/restore pages are referenced by URL `[S32]` but their contents were not retrieved. Certificate and credential workflow detail is therefore thin in this dossier.
11. **VCF Simple vs VCF High Availability topologies** are named `[S14]` but their component matrices and requirements were not retrieved. — `UNVERIFIED — could not retrieve`
12. **9.1 delta not researched.** The doc set is titled "9.0 and Later" and the landing page indicates 9.1 coverage `[S1]`, but the `/9-1/` subtree was out of scope. Facts tagged `[9.0+]` in this dossier are those where a *9.1-scoped* page (the `latest` API references) was the source; they are **not** confirmed to hold for 9.0 unless separately noted.
13. **"SDDC Manager Functionality During an Upgrade to VMware Cloud Foundation 9.0"** page appeared in search results (under `…/deployment/upgrading-cloud-foundation/upgrade-the-management-domain-to-vmware-cloud-foundation-5-2/apply-cloud-foundation-5-2-update-bundle/sddc-functionality-limitations.html`) but was **not fetched**. Its content — what SDDC Manager cannot do mid-upgrade — is likely operationally important. — `UNVERIFIED — could not retrieve`
14. **Exact evaluation-mode mechanics** (what triggers the 90-day clock, what happens at expiry of *evaluation* specifically vs *subscription*) not separated in sources. `[S5]` gives "extended evaluation mode to 90 days"; `[S18]` gives the 90-day post-expiration grace period. These may or may not be the same 90 days. — ambiguous.
15. **Async Releases and Patch Releases 9.0.x contents** not fetched; only their index URLs confirmed `[S3]`.

---

## Source Inventory

All accessed **2026-07-31**. "Doc set version" indicates the version scope of the URL subtree, not necessarily the version of every fact on the page.

| ID | URL | Doc set version | Date accessed | What it covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | 9.0 (family "9.0 and later") | 2026-07-31 | VCF 9.0 doc landing page; full 25-guide table of contents and URLs |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes.html | 9.0 | 2026-07-31 | 9.0 release date (17 JUN 2025) and build (24755599); RN subtree URLs; PDF link |
| S3 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes.html | 9.0 | 2026-07-31 | Release-notes index: 9.0, 9.0.1, 9.0.2, patch releases, async releases, Download Tool RN |
| S4 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | 9.0 | 2026-07-31 | Full 9.0.0.0 BOM incl. add-ons; vSphere Foundation inclusion column |
| S5 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new.html | 9.0 | 2026-07-31 | What's New themes; FIPS default; licensing simplification; 90-day eval |
| S6 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-1-release-notes.html | 9.0 (9.0.1 content) | 2026-07-31 | 9.0.1.0 release date 29 SEP 2025; maintenance-release characterization; child URLs |
| S7 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-1-release-notes/vmware-cloud-foundation-901-bill-of-materials.html | 9.0 (9.0.1 content) | 2026-07-31 | Full 9.0.1.0 BOM with versions and builds |
| S8 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-2-release-notes.html | 9.0 (9.0.2 content) | 2026-07-31 | 9.0.2.0 release date 20 JAN 2026; maintenance scope; BOM sub-page URL |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-2-release-notes/vmware-cloud-foundation-902-bill-of-materials.html | 9.0 (9.0.2 content) | 2026-07-31 | Full 9.0.2.0 BOM; SDDC Manager and VCF Installer share build 25151285 |
| S10 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes.html | 9.0 | 2026-07-31 | Deprecations and removals: SDDC Manager UI, ELM, Host Profiles, IWA, vLCM baselines, Cloud Builder, UMDS, precheck API move |
| S11 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/overview-of-vmware-cloud-foundation-9.html | 9.0 | 2026-07-31 | Overview landing; positioning statement; child page URLs (taxonomy, VVF, getting started) |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/overview-of-vmware-cloud-foundation-9/workload-domains-in-vmware-cloud-foundation.html | 9.0 | 2026-07-31 | VCF taxonomy: Private Cloud, Fleet, Instance, management domain, workload domain, domain composition |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment.html | 9.0 | 2026-07-31 | Deployment landing; three paths (new / converge / upgrade); child page URLs |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/what-is-the-vcf-installer-.html | 9.0 | 2026-07-31 | VCF Installer definition; `VCF-SDDC-Manager-Appliance-9.x.x.ova`; SDDC Manager mode switch; express-patch limitation; topologies |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/converging-your-existing-vsphere-infrastructure-to-a-vcf-or-vvf-platform-.html | 9.0 | 2026-07-31 | Convergence definition, phases, NSX gate (9.0.0 vs 9.0.1), storage/network/compute prereqs, unsupported configs |
| S16 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/upgrading-cloud-foundation.html | 9.0 | 2026-07-31 | Upgrade sources (VCF 5.0+), skip-level support, core vs management component ordering, SDDC Manager UI deprecation notice |
| S17 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/licensing.html | 9.0 | 2026-07-31 | Licensing landing; subscription license files replace 25-char keys; vCenter-level assignment; 20 child page URLs |
| S18 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/licensing/licensing-overview.html | 9.0 | 2026-07-31 | License types and units (cores/TiB), default license generation, connected vs disconnected, 180-day reporting, 90-day grace |
| S19 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/lifecycle-management.html | 9.0 | 2026-07-31 | LCM landing; VCF Operations as central LCM tool; five child page URLs |
| S20 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/lifecycle-management/lifecycle-management-of-vcf-core-components.html | 9.0 | 2026-07-31 | Maintenance-release upgrade sequencing (mgmt then core: SDDC Mgr → NSX → vCenter → ESX → vSAN); flexible BOM upgrade; child URLs |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/lifecycle-management/binary-management-for-vmware-cloud-foundation.html | 9.0 | 2026-07-31 | Binary ownership split (fleet mgmt vs SDDC Manager); VCF Download Tool as CLI; three child URLs |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools.html | 9.0 | 2026-07-31 | SDK/API/CLI guide index and child URLs |
| S23 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide.html | 9.0 | 2026-07-31 | VCF Programming Guide index; confirms no API detail at this level |
| S24 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/vcf-apis-and-scripts.html | 9.0 | 2026-07-31 | SDK GitHub repos (vcf-sdk-python, vcf-sdk-java) with SDDC Manager / VCF Import examples; pointers to API reference portals |
| S25 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html | 9.0 | 2026-07-31 | Java/Python SDK 9.0.0.0 details, PowerCLI→VCF PowerCLI rename and new Sddc cmdlets, VCF Consumption CLI, vCenter OpenAPI 3.0 |
| S26 | https://developer.broadcom.com/xapis/sddc-manager-api/latest/ | 9.1 ("latest"), 9.0 also selectable | 2026-07-31 | SDDC Manager API reference index; 58 resource categories |
| S27 | https://developer.broadcom.com/xapis/sddc-manager-api/9.0/ | 9.0 | 2026-07-31 | 9.0 SDDC Manager API: Bearer auth, 1h/24h token lifetimes, `/<version>/resource` pattern, 50+ resource categories, category URL pattern |
| S28 | https://developer.broadcom.com/xapis/sddc-manager-api/9.0/tokens/ | 9.0 | 2026-07-31 | Exact token endpoints: `POST /v1/tokens`, `PATCH /v1/tokens/access-token/refresh`, `DELETE /v1/tokens/refresh-token`; schemas and headers |
| S29 | https://developer.broadcom.com/xapis/sddc-manager-api/9.0/domains/ | 9.0 | 2026-07-31 | Full Domains endpoint inventory; example base URL `https://sfo-vcf01.rainpole.io/v1`; validations/tags/isolation-prechecks/query patterns |
| S30 | https://developer.broadcom.com/xapis/vcf-installer-api/latest/ | 9.1 ("latest"), 9.0 also available | 2026-07-31 | VCF Installer API reference; 11-12 resource categories; scope statement |
| S31 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-private-cloud-infrastructure.html | 9.0 | 2026-07-31 | Build-phase guide index; which UI performs which workflow; network pools, stretched clusters, VPCs |
| S32 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-private-cloud-infrastructure/sddc-manager-workflows.html | 9.0 | 2026-07-31 | **SDDC Manager UI deprecation statement**; mapping of former SDDC Manager workflows to their new locations |
| S33 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-private-cloud-infrastructure/working-with-workload-domains.html | 9.0 | 2026-07-31 | Domain operations: create, import, delete, expand, shrink, configuration drift; per-operation URLs and interfaces |
| S34 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi/opnapi-for-sddc-manager.html | 9.0 | 2026-07-31 | "~280 interfaces in the SDDC Manager API"; SDDC Manager appliance role; confirms absence of spec download URL on this page |
| S35 | https://developer.broadcom.com/sdks/vcf-api-specification/latest | 9.1 ("latest") | 2026-07-31 | VCF API Specification bundle: 8 component specs incl. SDDC Manager and VCF Installer; `vcf-api-specs-9.1.0.0-25372366.zip`; GitHub `vmware/vcf-api-specs` |
| S-search | WebSearch result sets (queries on developer.broadcom.com SDDC Manager API and OpenAPI spec) | mixed | 2026-07-31 | Used only for URL **discovery** (locating S26–S30, S34, S35 and the `/9-1/` subtree). No substantive facts sourced from search snippets alone. |
