# VCF 9.0 → 9.1 — Domains, Clusters, Hosts and Network Pools Delta

Scoped to **topology**: workload domains, clusters, hosts, network pools, and the vCenter/NSX/HCX
association that goes with them. For upgrades and patching see the `vcf-lifecycle-upgrade` skill;
for auth see `vcf-foundation`.

**Source keys.** `D9.0` = `research/vcf-core-9.0.md`; `D9.1` = `research/vcf-core-9.1-and-deltas.md`;
`DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of git tags
`9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`);
`SPEC9.0` / `SPEC9.1` = the per-version `sddc-manager.ops.json` inventories;
`RAW9.0` / `RAW9.1` = the full OpenAPI documents at those tags, for schemas.

---

## The headline

**SDDC Manager did not lose the topology API in 9.1 — it gained 19 operations in it.**

| | 9.0 | 9.1 |
|---|---|---|
| SDDC Manager API, total | 375 operations | **423** — 48 added, **0 removed**, 21 newly deprecated |
| Topology operations (9 tags) | **128** | **147** — 19 added, 0 removed |
| Newly deprecated in topology | — | 9 (`/v1/edge-clusters` ×8, `PATCH /v1/domains/{id}/overlay`) |
| Brand-new topology tags | — | `HcxManagers` (6), `UpdateVcenterFqdn` (1) |

Per tag, counted from `SPEC9.0` / `SPEC9.1`:

| Tag | 9.0 | 9.1 | Δ |
|---|---|---|---|
| `Clusters` | 34 | 38 | +4 |
| `Domains` | 32 | 35 | +3 |
| `Hosts` | 19 | 21 | +2 |
| `NSX-T Clusters` | 16 | 18 | +2 |
| `Network Pools` | 9 | 13 | **+4** |
| `NsxTEdgeClusters` | 8 | 8 | 0 — but **all 8 deprecated** |
| `BrownfieldImport` | 6 | 10 | +4 |
| `vCenters` | 2 | 2 | 0 (+1 in the new `UpdateVcenterFqdn` tag) |
| `PSCs` | 2 | 2 | 0 |
| `HcxManagers` | — | 6 | **new tag** |

---

## Delta table

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| **Domain requires a cluster** | `DomainCreationSpec.required = ["computeSpec", "vcenterSpec"]`. A domain cannot exist without at least one cluster. | **`required = ["vcenterSpec"]`.** vCenter and NSX Manager can be deployed with **no initial cluster** — but **"patching/upgrades blocked until a cluster is added."** A real capability with a real trap. | `RAW9.0`/`RAW9.1`; D9.1 §3.4, delta #25 |
| **DNS and NTP** | System-scoped only: `/v1/system/dns-configuration` and `/v1/system/ntp-configuration` (9 operations) are **active**. No DNS/NTP fields on any topology schema. | **Inverted.** All 9 system operations **deprecated** (part of the documented "21 APIs deprecated … system DNS/NTP configurations"). DNS/NTP move onto topology: `dnsServers[]`/`ntpServers[]` on `DomainCreationSpec` and `ClusterCreationSpec`; `dnsNtpUpdateSpec` on `DomainUpdateSpec` and `ClusterUpdateSpec`; `dnsServers`/`ntpServers` returned on `Domain` and `Cluster`. | `SPEC9.0`/`SPEC9.1`; `RAW9.0`/`RAW9.1`; D9.1 §4, §3.5 |
| **Network pools are editable** | Effectively immutable. `PATCH /v1/network-pools/{id}` accepts **`name` only**. IP pools can only be added or deleted wholesale. No way to change a network's VLAN/MTU/subnet/gateway, resize a range in place, or mark individual IPs. | **Four new operations close all of it.** `PATCH .../networks/{networkId}` (`NetworkUpdateSpec`: vlan, mtu, subnet, gateway); `PATCH .../networks/{networkId}/ip-pools` (`IpPoolUpdateSpec`: `oldIpPool` → `newIpPool`); `GET` and `PATCH .../networks/{networkId}/ips` (`NetworkIpAddressesUpdateSpec`: `freeIps[]`, `usedIps[]`). | `DELTA`; `SPEC9.1`; `RAW9.1` |
| **Network schema / dual-stack** | `Network` **requires** `subnet`, `mask`, `gateway`. `IpPool.start`/`.end` carry an IPv4 regex `pattern`. No IP-version concept. | `subnet`, `mask`, `gateway` **no longer required**. IPv4 `pattern` on `IpPool` **removed**. Adds `ipAddressVersion` (`IPv4`/`IPv6`, default `IPv4`), `ipAddressAssignmentMode` (`STATIC`/`DHCP`/`SLAAC`, default `STATIC`), `freeIpCount`, `usedIpCount`. Backs "dual-stack networking for management and workload domains". | `RAW9.0`/`RAW9.1`; D9.1 §3.4 |
| **NSX Edge cluster API** | 8 operations under `/v1/edge-clusters`, **active**, the SDDC Manager path for creating and updating Edge clusters. | **All 8 deprecated.** Named in the release notes among the 21 deprecations affecting "edge cluster operations". They still respond; **no successor API is named in any retrieved source.** | `SPEC9.0`/`SPEC9.1`; D9.1 §4 |
| **`PATCH /v1/domains/{id}/overlay`** | Active — `enableOverlayOverManagementNetwork`, for NSX VLAN-backed domains. | **Deprecated**, named in the release notes under "domain overlays". No documented replacement. | `SPEC9.0`/`SPEC9.1`; D9.1 §4 |
| **HCX Manager** | HCX is in the BOM; **no SDDC Manager API family**, no lifecycle through VCF Operations. | **6 new operations, new tag `HcxManagers`:** `GET|POST /v1/domains/{domainId}/hcx-managers`, `POST .../validations`, `GET .../validations/{validationId}`, `GET .../versions`, `DELETE .../{hcxManagerId}`. Standard validate → execute → poll. HCX Manager deployment and upgrade via VCF Operations. | `DELTA`; `SPEC9.1`; D9.1 §3.5 |
| **vCenter FQDN** | Read-only (`getVcenters`, `getVcenter`). No way to change a managed vCenter's FQDN through the API. | **`PATCH /v1/vcenters/{vcenterId}/fqdn`** (`updateVcenterFqdn`), new tag `UpdateVcenterFqdn`. | `DELTA`; `SPEC9.1` |
| **Out-of-band change handling** | Out-of-band vCenter/NSX changes are disruptive to SDDC Manager; only the config-drift reconciler exists (`/v1/config-drifts`, `/v1/config-drift-reconciliations`, unchanged in both). | Adds **`POST /v1/clusters/{clusterId}/remediations`** (`triggerRemediation`) and **`GET /v1/clusters/{clusterId}/remediations/{remediationId}`** (`getRemediationById`) — there is no GET on the collection. `ClusterRemediationCriterion.name` — "currently, the only supported value is `SDDC_NETWORKING_DATA_REMEDIATION`". Docs: tasks performable in vCenter "without impacting SDDC Manager" (VDS changes, datastore modifications); "Out-of-band networking changes to not impact SDDC Manager". | `DELTA`; `RAW9.1`; D9.1 §3.3, §3.4 |
| **Bulk inventory refresh** | None. | Three new bulk `PATCH`es, all *refresh* semantics, not reconfiguration: `PATCH /v1/domains` (`DomainsUpdateSpec`: `domainIds[]` + `forceRefresh`), `PATCH /v1/clusters` (`ClustersUpdateSpec`: `clusterIds[]` + `forceRefresh`), `PATCH /v1/hosts` (`HostsUpdateSpec`: `hostIds[]` + `forceRefresh`). | `DELTA`; `RAW9.1` |
| **Cluster image sourcing** | `ClusterSpec.clusterImageId` only — name a personality. Required on vCenter 9.0+. | Same, plus **`ClusterSpec.hostIdForHostSeeding`** — extract the desired image from a nominated **UNASSIGNED** host ("it MUST NOT denote an ASSIGNED host"). Plus a domain-wide compliance query pair: `POST|GET /v1/domains/{domainId}/image-compliance/queries[/{queryId}]`. | `RAW9.0`/`RAW9.1`; `SPEC9.1` |
| **`ClusterUpdateSpec` reach** | expansion, compaction, stretch, unstretch, `markForDeletion`, `prepareForStretch`, `name`, `clusterTransitionSpec`, `clusterImageComplianceCheckSpec`. | All of the above **plus** `clusterPrimaryDatastoreUpdateSpec` (required `datastoreId`), `dnsNtpUpdateSpec`, `markAsDefault`. | `RAW9.0`/`RAW9.1` |
| **`DomainUpdateSpec` reach** | `clusterSpec`, `nsxTSpec`, `name`, `markForDeletion`, `isolationSpec`. | All of the above **plus** `dnsNtpUpdateSpec`, `acknowledgmentSpec` (`ackThatOfflineBackupsTaken`), `transitionSpec`, `imageComplianceCheckSpec`. | `RAW9.0`/`RAW9.1` |
| **Host inventory model** | `Host` has no standalone/witness/lifecycle concepts. `getHosts` filters: fqdn, status, domainId, clusterId, networkpoolId, storageType, datastoreName, size, page. | `Host` gains `isStandalone`, `isLifecycleManaged`, `isVsanWitnessHost`, `managedObjectReferenceId`; `getHosts` gains matching filters plus `ipAddressVersionForVmotion` (`IPv4`/`IPv6`) and `pageSize`/`pageNumber` (`size`/`page` now **deprecated**). Adds `GET /v1/hosts/{id}/software`. Backs "support for imported standalone hosts and single-host clusters". | `RAW9.0`/`RAW9.1`; `SPEC9.1`; D9.1 §3.5 |
| **List-read ergonomics** | `getClusters`: domainId, isStretched, isImageBased. `getDomains`: type. Neither paginates. | `getClusters` adds name, managedObjectReferenceId, isDefault, isHciMeshEnabled, pageNumber, pageSize, **useCache**. `getDomains` adds name, vcFqdn, vcInstanceId, isManagementSsoDomain, pageNumber, pageSize, **useCache**. `Cluster` gains `primaryDatastoreNativeId`; `Domain` gains `albCluster`, `hcxManagers`, `vspClusters`. | `RAW9.0`/`RAW9.1` |
| **Task states** | `Task.status` example: PENDING, IN_PROGRESS, SUCCESSFUL, FAILED, CANCELLED, COMPLETED_WITH_WARNING, SKIPPED (+ mixed case). | Adds **`QUEUED`** and **`TIMED_OUT`** (+ mixed case). A 9.0-era poller with a closed state list mis-reads both. | `RAW9.0`/`RAW9.1` |
| **Datastore mount validation** | `POST /v1/clusters/{clusterId}/datastores/validations` exists, but **no GET to poll the result by id**. | Adds `GET /v1/clusters/{id}/datastores/validations/{validationId}` (`getDatastoreMountValidation`) — first version where that validate-then-poll loop closes through a dedicated endpoint. | `SPEC9.0`/`SPEC9.1` |
| **Brownfield import** | 6 operations. Validation results are a single blob. | 10 operations. Adds CSV export (`GET /v1/sddcs/imports/validations/{taskId}/report`), a validation-group tree (`.../validation-groups[/{validationGroupId}]`), and `POST /v1/domains/{domainId}/synchronizations/ssh-known-hosts`. Import sources widen to vCenter 8.0 U2a+ with/without NSX, NSX Federation, and dual-stack. "Revamped UI and API for brownfield imports and prechecks." | `DELTA`; D9.1 §3.4, §3.5 |
| **NSX read granularity** | `getProjects`, `getVpcConnectivityProfiles` — list reads only. | Adds the single-item reads `getProject` and `getVpcConnectivityProfile`. `NsxTSpec` gains optional `vnaSpec` (Virtual Network Appliance). | `SPEC9.1`; `RAW9.1`; D9.1 §3.3 |
| **`storageType` values** | Example: `VSAN, VSAN_ESA, VSAN_REMOTE, VSAN_MAX, NFS, VMFS_FC, VVOL, VMFS`. | Example: same plus **`NFS41`** and a bare **`FC`** (source text repeats `VVOL`). Still an `example`, **not an `enum`**, in both. | `RAW9.0`/`RAW9.1` |
| **Scale** | Baseline. The 9.0 host-per-instance maximum was never stated in any retrieved source. | **5000 hosts per VCF Instance, explicitly "2x increase from VCF 9.0"**, reported under the heading "SDDC Manager Scale". Do **not** back-derive 2500 as a sourced 9.0 figure. | D9.1 §3.5, §1 |
| **vCLS** | Manageable from the SDDC Manager and VCF Installer UIs. | "All vCLS functionalities available in SDDC Manager UI and VCF Installer UI are **removed**"; vCLS "deactivated by default and you cannot re-activate the capability." | D9.1 §4 |
| **SDDC Manager UI** | Already deprecated in 9.0 — workflows moved to VCF Operations and the vSphere Client. **API not deprecated.** | Deprecation restated and sharpened. **API not deprecated, and larger.** 9.1 components page still assigns SDDC Manager "deployment of workload domains; import of vCenter instances; configuration of vSAN stretched clusters". | D9.0 §3.1; D9.1 §0.3, §2 |

---

## What did *not* change

- **The validate → execute → poll pattern.** Create/update paired with a `validations`
  sub-resource; long-running work returns a `Task`. Identical in both versions.
- **`Validation` semantics.** `executionStatus` then `resultStatus`, same value sets. `COMPLETED`
  with `resultStatus: FAILED` is a failure in both.
- **The four `Tasks` operations** — `getTasks`, `getTask`, `retryTask`, `cancelTask` — same paths,
  same filters. Only the status vocabulary grew.
- **`HostCommissionSpec` and `HostDecommissionSpec`.** Same properties, same required fields
  (`fqdn`, `username`, `password`, `storageType`, `networkPoolId`; and `fqdn`). Array bodies in
  both.
- **`ClusterExpansionSpec` and `ClusterCompactionSpec`.** Byte-identical property and required
  sets. A cluster expand/contract payload is portable between versions.
- **`HostSpec`.** Same properties, same `id`-required rule, same deprecated `ipAddress`, same
  "sshThumbprint will be mandatory in future releases" warning.
- **The two-phase deletion gate.** `markForDeletion` then `DELETE`, for both clusters and domains.
- **Config drift and vSAN health.** `getConfigs`, `reconcileConfigs`, `getReconciliationTask`;
  `getVsanHealthCheckByDomain` and its three companions. Identical.
- **The already-deprecated set carried forward.** `POST /v1/hosts/queries`,
  `GET /v1/hosts/queries/{id}`, `POST /v1/hosts/validations/commissions`, the four
  `clusters/{id}/hosts` criteria+query operations, the singular
  `clusters/{clusterId}/datastores/validation`, and the seven `/v1/nsx-alb-clusters` operations
  were **already deprecated in 9.0** and remain so. Prose sources mention none of them.
- **SDDC Manager's exclusion from VCF SSO,** and therefore its own `/v1/tokens` bearer flow.
  (`vcf-foundation` owns this.)

---

## Migration checklist for topology automation crossing 9.0 → 9.1

1. **Widen the task poller** to accept `QUEUED` (not terminal) and `TIMED_OUT` (terminal), and
   compare case-insensitively.
2. **Move DNS/NTP off `/v1/system/*`** onto `dnsServers`/`ntpServers` in the domain and cluster
   specs, and `dnsNtpUpdateSpec` for updates.
3. **Stop building on `/v1/edge-clusters`** and `PATCH /v1/domains/{id}/overlay` — deprecated,
   with no documented successor. Raise it as an open question rather than substituting a path.
4. **Rename `size`/`page` → `pageSize`/`pageNumber`** on `getHosts`.
5. **Audit any `useCache` usage** you add: a cached read is wrong for a pre-flight state gate.
6. **Do not assume the 9.1 built-in role names apply to SDDC Manager.** They are documented for
   vCenter, NSX, VCF Operations, VCF Automation, HCX and Orchestrator — not SDDC Manager. See P10
   in `9.1/domains-clusters.md`.
7. **If you adopt clusterless domains,** add a gate that blocks patch/upgrade attempts until a
   cluster exists.

---

## Deltas the research could NOT establish

- **What replaces `/v1/edge-clusters`.** The deprecation is machine-confirmed from both tags and
  corroborated by the release notes; the successor is not named anywhere retrieved. UNVERIFIED.
- **What replaces `PATCH /v1/domains/{id}/overlay`.** Same situation. UNVERIFIED.
- **Which operations require `acknowledgmentSpec.ackThatOfflineBackupsTaken`.** The field is
  spec-confirmed in `RAW9.1`; its trigger condition is undocumented. UNVERIFIED.
- **The API mechanism for sharing an NSX Manager between domains.** Advertised in the 9.1 NSX
  notes; no corresponding field in `NsxTSpec` in either version, and no retrieved page describes
  the workflow. UNVERIFIED in both.
- **Enumerated `storageType` / `vvolStorageProtocolType` / `Network.type` values.** `example`
  strings in both versions, never `enum`. The *delta* between the two example strings is
  observable; whether either is exhaustive is not.
- **The 9.0 host-per-instance maximum.** 9.1 says "2x increase from VCF 9.0", implying 2500, but
  no 9.0 page stating the number was retrieved. Do not assert 2500 as sourced.
- **Whether domain deletion returns hosts to the free pool** — undocumented in both versions, so
  the delta is unknown too.
- **Topology-task concurrency in either version.** The "256 simultaneous cluster upgrades" figure
  is an upgrade figure and does not transfer.
- **Ports and protocols matrix** for host commissioning and domain deployment — never retrieved in
  either version.
