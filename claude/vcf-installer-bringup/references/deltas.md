# VCF 9.0 → 9.1 — VCF Installer and Bring-Up Delta

Scoped to the VCF Installer, management-domain bring-up, and convergence. For the full
cross-product delta see the research dossiers; this file is the bring-up slice.

**Source keys.** `D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DAUTH` = `research/foundation-auth-identity.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of git tags `9.0.0.0`
and `9.1.0.0` of `github.com/vmware/vcf-api-specs`);
`SPECI9.0` / `SPECI9.1` = the `*__vcf-installer.ops.json` inventories (**52** and **57** operations);
`RAW9.0` / `RAW9.1` = the raw `vcf-installer-openapi.json` at each tag, read for schemas.

---

## Two facts this file exists to keep straight

1. **Cloud Builder is gone, and VCF Installer is the same appliance as SDDC Manager.** Removed in
   9.0 and replaced by the VCF Installer [D9.0 §9.2], which ships inside
   **`VCF-SDDC-Manager-Appliance-9.x.x.ova`** and, when deployed inside the management
   infrastructure, "switches into SDDC Manager mode and **can no longer be used in installer
   mode**" [D9.0 §3.2]. **9.1 makes it official in the BOM: one row,
   `VCF Installer/SDDC Manager 9.1.0.0 (25371088)`** [D9.1 §2], where 9.0 had two.
2. **The endpoint list barely moved; the payload changed a lot.** 5 operations added, **0 removed,
   0 newly deprecated** [DELTA] — but **44 schemas added and 2 removed** (120 → 162) between the
   tags. Diffing only paths gives you the wrong answer.

---

## Delta table

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| **BOM identity** | Two rows: `VCF Installer 9.0.2.0 (25151285)` and `SDDC Manager 9.0.0.0 (24703748)`. The 9.0.2.0 BOM already showed both at build `25151285`. The Installer row is **version-skewed** — 9.0.2.0 listed inside the 9.0.0.0 BOM. | **One row: `VCF Installer/SDDC Manager 9.1.0.0 (25371088)`.** | 9.0: D9.0 §1.2, §1.4 · 9.1: D9.1 §2, §0.3 |
| **Predecessor** | **Cloud Builder removed in 9.0**, replaced by VCF Installer. Deployment Parameter Worksheet removed, replaced by the appliance UI + JSON (`SddcSpec`). | Unchanged — Cloud Builder does not exist in either version. | D9.0 §9.2, §4.2 |
| **Mode switch** | Deployed inside management infrastructure → SDDC Manager mode, **one-way**. Outside → can build multiple platforms. | No 9.1 source contradicts or softens this. Treat as unchanged. | D9.0 §3.2 |
| **API size** | **52 operations**, spec version `9.0.0.0`. | **57 operations**, spec version `9.1.0.0`. **+5, −0, 0 newly deprecated.** Base path unchanged. | **DELTA**; SPECI9.0/9.1 |
| **Operations added** | — | `POST /v1/sddcs/resources-calculation` (`resourcesCalculation`), `GET /v1/sddcs/resources-calculation/{id}` (`getResourcesCalculation`), `POST /v1/sddcs/sddcm-discovery` (`discoverSddcManager`), `POST /v1/sddcs/vcenter-discovery/networks` (`discoverVcenterNetworks`), `GET /v1/system/settings/depot/machine-details` (`getMachineDetails`). | **DELTA**; SPECI9.1 |
| **Deprecated operations** | `POST /v1/bundles` (`uploadBundle`) — *"[Unsupported] Upload a bundle to SDDC Manager or VCF Installer"*. | **The same one, and only that one.** No new deprecations. | SPECI9.0/9.1 |
| **Capacity / sizing gate** | **None.** No resources-calculation API; the Design and Planning guides were never fetched [D9.0 §11 item 9]. | **New:** `resources-calculation` returns `CapacityValidation` with `requiredCapacity` vs `availableCapacity`, each a `CapacityInfo` carrying `numberOfEsxiHosts`, `numberOfCores`, `memory`, `storage` and per-component `ComponentVmRequirement` (`cpuCores`, `memoryGb`, `storageGb`, `workersCount`, **`ipCount` / `ipCountRecommended` / `ipCountLimit`**). Matches the documented *"integrated planning workflow with resource validation"*. | RAW9.1; **DELTA** · prose: D9.1 §3.4 |
| **SDDC Manager discovery** | No such endpoint. | `POST /v1/sddcs/sddcm-discovery` → `SddcManagerDiscoveryResult { sddcManager, managementVcenter, vcfManagementComponents }`. Discovers an **existing SDDC Manager topology** for import. | **DELTA**; RAW9.1 |
| **Network discovery** | `vcenter-discovery` and `vcfops-discovery` only. | Adds `POST /v1/sddcs/vcenter-discovery/networks` → `PageOfVcenterNetworkInfo`, with name filter and paging. Enumerate the existing vCenter's networks instead of transcribing them. | **DELTA**; RAW9.1 |
| **`SddcSpec.workflowType`** | Pattern **`(VCF\|VCF_EXTEND\|VVF)`**. | Pattern **`(VCF\|VCF_COMPLETE\|VCF_EXTEND\|VVF\|VCF_BOOTSTRAP)`** — two new values. Description adds: *"If building a **secondary VCF instance** to connect it to the fleet, specify workflowType as `VCF_EXTEND`."* **What `VCF_COMPLETE` and `VCF_BOOTSTRAP` do is `UNVERIFIED`** — the schema's own `example` was not updated and still lists only the three 9.0 values. | RAW9.0 vs RAW9.1 |
| **Fleet-management appliance in the spec** | `SddcSpec.vcfOperationsFleetManagementSpec` exists; schema `VcfOperationsFleetManagementSpec` present. | **Both gone.** `VcfOperationsFleetManagementSpec` is one of only **two** schemas removed between the tags (the other is `PartnerExtensionSpec`). Independent spec-level corroboration of *"The standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by fleet lifecycle."* | RAW9.0 vs RAW9.1 · prose: D9.1 §0.2 |
| **Management services in the spec** | Not present. | `SddcSpec` gains **`fleetLcmSpec`**, **`sddcLcmSpec`**, **`fleetDepotSpec`**, **`vidbSpec`**, **`saltSpec`**, **`saltRaasSpec`**, **`telemetryAcceptorSpec`**, **`vspClusterSpec`**, **`vcfManagementComponentsInfrastructureSpec`** — the spec side of *"VCF 9.1 deploys standardized management services components by default, including runtime, fleet lifecycle, identity broker, and software depot."* | RAW9.1 · prose: D9.1 §3.4 |
| **Licensing in the spec** | **No license field anywhere** — a search of every schema property in `RAW9.0` for `licen*` returns **zero hits**. Licensing is entirely post-deployment, via VCF Operations + VCF Business Services. | **`SddcSpec.licenseServerSpec`** (`hostname` required, plus `useExistingDeployment`, `version`, `sslThumbprint`) — exactly one hit. Matches the new **required** `License server 9.1.0.0 (25346031)` component, which has no 9.0 BOM row. | RAW9.0 vs RAW9.1 · prose: D9.0 §5; D9.1 §2, §5.2, §6 |
| **Convergence support matrix** | **Tight.** VCF 9.0.0: only a **new** NSX 9.0 deployment — **existing NSX instances unsupported**. VCF 9.0.1+: existing NSX **without Enhanced Linked Mode**. Unsupported: VxRail-managed clusters, vCenter with ELM, Cisco virtual switches, dynamic VMkernel IPs. | **Substantially wider:** existing **vCenter 8.0 U2a+ with NSX Manager 4.1.2.1+**; **vCenter 8.0 U2a without NSX** (requires manual vCenter upgrade to 9.1); vCenter with existing **NSX Federation**; **dual-stack IPv4/IPv6**. Plus Bare Metal Edge support in VCF import. **The 9.0 unsupported list was not restated on any 9.1 page retrieved — `UNVERIFIED for 9.1`.** | 9.0: D9.0 §4.3 · 9.1: D9.1 §3.4, §3.3 |
| **Networking in `SddcNetworkSpec`** | `networkType`: VSAN, VMOTION, MANAGEMENT, VM_MANAGEMENT, NFS or custom. No IP-version or assignment-mode fields. | Adds **`FLEET_MANAGEMENT`** network type, **`ipAddressVersion`** (IPv4/IPv6) and **`ipAddressAssignmentMode`** (STATIC/DHCP/SLAAC). `SddcNetworkConfigProfileSpec` gains `additionalPortGroups`. `nsxtSpec` gains `vpcSpec` → `dtgwSpec` (distributed transit gateway). | RAW9.0 vs RAW9.1 · prose: D9.1 §3.4 |
| **`ApplianceInfo`** | `role`, `version` only. | Adds **`dnsDomain`, `dnsServers`, `ntpServers`, `ipAddresses`** — one call now answers most of the DNS/NTP self-check. | RAW9.0 vs RAW9.1 |
| **`VcfManagementComponents`** (discovery output) | **4 members**: `vcfOperationsFleetManagement`, `vcfOperations`, `vcfOperationsCollector`, `vcfAutomation`. | **12 members**: adds `vspCluster`, `sddcLcm`, `fleetLcm`, `vcfOperationsLogs`, `telemetryAcceptor`, `vidb`, `salt`, `saltRaas` — and **retains `vcfOperationsFleetManagement`** even though the input spec for it was deleted. Probably for reading 9.0-era estates; **no source states this** — `UNVERIFIED`. | RAW9.0 vs RAW9.1 |
| **`SddcTask`** | `id`, `name` ("Task name"), `status`, `creationTimestamp`, `milestones`, `sddcSubTasks`, `localizableNamePack`. | Adds **`deploymentType`** and **`vcfInstanceName`**; `name` redescribed as "**Deployment name**". | RAW9.0 vs RAW9.1 |
| **`ValidationCheck`** | `description`, `severity`, `resultStatus`, `acknowledge`, `errorResponse`. | Adds **`nestedValidationChecks`** — validation results are a tree in 9.1. A flat reader silently misses failures. | RAW9.0 vs RAW9.1 |
| **Depot** | Depot settings + sync-info on the Installer. | Same, plus **`GET /v1/system/settings/depot/machine-details`** → `{ machineId }`. At the platform level, **software depot** becomes a distinct component that "handles binaries for all VCF components". | **DELTA** · prose: D9.1 §0.4 |
| **Password rules in the schemas** | vCenter root "between 15 characters and 20 characters"; SDDC Manager root/`vcf` "strong password with at least one alphabet and one special character"; NSX admin/audit/root ≥ 12. | vCenter root: *"For new deployments … between 15 and 20 … For existing vCenter (brownfield) …"*; SDDC Manager root/`vcf` now "**at least 15 characters**". NSX unchanged. Also documented: *"auto-generated complex passwords for system accounts."* | RAW9.0 vs RAW9.1 · prose: D9.1 §3.4 |
| **`vcfInstanceName` length** | "Minumum length 3, maximum length 300" (typo in source). | "Minimum length 1, maximum length 300". | RAW9.0 vs RAW9.1 |
| **vCLS** | Manageable from SDDC Manager and VCF Installer UIs. | *"All vCLS functionalities available in SDDC Manager UI and VCF Installer UI are **removed**"*; vCLS "deactivated by default and you cannot re-activate the capability." | D9.1 §4 |
| **Out-of-band changes** | Out-of-band vCenter changes disruptive to SDDC Manager. | Tasks performable in vCenter *"without impacting SDDC Manager"* — VDS changes, datastore modifications, manual component upgrades; *"Out-of-band networking changes to not impact SDDC Manager."* | D9.1 §3.4, §3.3 |
| **Workload domain creation** | Required an initial vSphere cluster. | New workflow deploys **vCenter and NSX Manager without an initial cluster** — but **patching and upgrades are blocked until a cluster is added**. (SDDC Manager / VCF Operations surface, not the Installer's.) | D9.1 §3.4 |
| **Installer authentication** | `Tokens` tag with three operations; **no `securitySchemes`**; no per-operation `security`; **no Installer row in the auth research**. | **Identical, and identically unresolved.** | RAW9.0, RAW9.1; DAUTH; D9.0 §11 item 2 |

---

## What did *not* change

- **The base path.** `/v1/...` in both; the declared server is a placeholder (`http://localhost:80`
  with a `basePath` variable) in both. Substitute your appliance FQDN. [DELTA]
- **The tag set.** All 12 tags identical: Bundles, CEIP, DepotSettings, Flexible Product Patches,
  ProxyConfiguration, Releases, System, Tasks, Tokens, Trusted Certificates, VCF Installer,
  VcfServices. [SPECI9.0/9.1]
- **The workflow shape.** validate (`POST /v1/sddcs/validations`) → deploy (`POST /v1/sddcs`) →
  poll (`GET /v1/sddcs/{id}`) → retry (`PATCH /v1/sddcs/{id}` with a full corrected `SddcSpec`).
  `?skipValidations` exists on both write operations in both versions.
- **The convergence mechanism.** `useExistingDeployment` per component spec, with `sslThumbprint`
  "populated when using existing deployment in order to establish trust", plus
  `datastoreSpec.existingDatastoreName`.
- **`SddcHostSpec`.** Byte-identical: `hostname` (RFC 1123, no domain suffix), `credentials`,
  `sslThumbprint`, `sshThumbprint`.
- **The required set of `SddcSpec`:** `dnsSpec`, `networkSpecs`, `sddcId`, `vcenterSpec`.
- **`sddcId` constraints:** 3–20 characters, `[A-Za-z0-9-]`, used as the management domain name.
- **The one-way mode switch**, and the fact that **SDDC Manager's bring-up APIs remain replaced by
  the Installer** [D9.0 §9.2].
- **Express patch releases remain out of scope** for Installer workflows; apply them manually after
  the workflows complete [D9.0 §4.2].
- **The `uploadBundle` deprecation** — deprecated and "[Unsupported]" in both.

---

## Deltas the research could NOT establish

- **The Installer auth delta** — there is nothing to compare, because neither version's auth is
  documented. Header format, token lifetimes and the refresh content type are unverified in both.
  **This is the single most consequential open item in this skill.** [D9.0 §11 item 2; DAUTH]
- **Semantics of `VCF_COMPLETE` and `VCF_BOOTSTRAP`** — new `workflowType` values, spec-confirmed
  in the 9.1 pattern, described nowhere.
- **Whether the 9.0 convergence-unsupported list still applies in 9.1** — VxRail, Enhanced Linked
  Mode, Cisco virtual switches, dynamic VMkernel IPs. No 9.1 page restating it was retrieved, and
  9.1's documented NSX Federation support sits awkwardly beside the ELM exclusion.
- **9.1-scoped host-count minima, DRS and vLCM-image rules** — captured only from the 9.0
  convergence page [D9.0 §4.3].
- **Ports and protocols, either version** — the matrix is a client-side tool with no static table;
  never retrieved [DAUTH §4]. 9.1 explicitly names it as a prerequisite [D9.1 §5.2].
- **DNS record checklist and NTP requirements, either version** — field-level requirements are
  spec-confirmed; the operational checklists are not.
- **Bundle-type taxonomy and depot payload shapes, either version** [D9.0 §11 item 6].
- **The enumerated validation checks** run by `validateSddcSpec`, and which are acknowledgeable
  rather than blocking, in either version.
- **VCF Simple vs VCF High Availability topology requirements** — named in 9.0 [D9.0 §4.2], matrices
  never retrieved [D9.0 §11 item 11], no 9.1 restatement.
- **What happens if the new 9.1 management-services members are omitted from `SddcSpec`** — prose
  says these components are "deployed by default", the schema makes them optional objects with
  `size` and `version`. Whether omission means defaults or skipped components is undocumented.
- **Rollback or teardown of a partially completed bring-up, either version** — `retrySddc` and task
  retry/cancel exist; nothing documents an undo. `SddcTask.status` includes `ROLLBACK_SUCCESS`, but
  that is an internal terminal status, not a user-invoked feature.
