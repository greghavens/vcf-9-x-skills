# NSX Logical Networking — VCF 9.0 → 9.1 change table

Scope: **segments, Tier-0 and Tier-1 gateways, transport zones, transport nodes, edge clusters and
edge nodes, BGP and routing, and the multi-tenancy / Federation path families.** Distributed firewall
and security deltas are out of scope — see the `nsx-security-policy` skill's `references/deltas.md`.
NAT, load balancing, VPN and IPAM belong to a forthcoming `nsx-network-services` skill and appear here
only where they change the *networking* surface.

Source classes, same convention as the version files:

| Tag | Meaning |
|---|---|
| **[DOC]** | Version-pinned Broadcom prose (release notes, product support notes, admin guide, developer portal). |
| **[SPEC-9.1]** | Confirmed in the machine-extracted 9.1 spec inventory (`9.1.0.0` tag of `github.com/vmware/vcf-api-specs`). |
| **[ASYMMETRIC]** | The 9.1 side is spec-confirmed; the 9.0 side is prose-only, because **no NSX spec is published at the `9.0.0.0` tag**. |

> **The structural asymmetry that governs this whole table.** The public spec corpus has **no NSX
> specification at `9.0.0.0`** — `nsx-policy`, `nsx-manager` and `nsx-global-policy` are all absent at
> that tag and present only at `9.1.0.0` (3,729 / 1,453 / 1,009 operations). Therefore a row saying
> "not observed in 9.0" almost never means "proven absent in 9.0." It means the 9.0 prose docs did not
> show it. Only the appliance's own OpenAPI document can settle a 9.0 question:
> `GET /api/v1/spec/openapi/nsx_policy_api.json`.

---

## Contents

1. [Headline changes affecting logical networking](#1-headline-changes-affecting-logical-networking)
2. [Object-by-object API surface](#2-object-by-object-api-surface) — segments, gateways, routing, fabric
3. [Dynamic BGP peering — documented feature, unverified API](#3-dynamic-bgp-peering--a-documented-feature-with-an-unverified-api)
4. [IPAM IP Block: 1 → 10 CIDRs and ranges](#4-ipam-ip-block-1--10-cidrs-and-ranges)
5. [Uplink IPFIX dropped](#5-uplink-ipfix-dropped)
6. [Locale-service-scoped VPN paths deprecated](#6-locale-service-scoped-vpn-paths-deprecated)
7. [Manager-API fabric tree: now formally deprecated](#7-manager-api-fabric-tree-now-formally-deprecated-in-the-spec)
8. [Removed operations — counts published, paths not](#8-removed-operations--counts-published-paths-not-published)
9. [Path families and tenancy](#9-path-families-and-tenancy)
10. [Platform and VCF-integration changes](#10-platform-and-vcf-integration-changes-that-affect-a-networking-agent)
11. [Documentation-structure deltas (traps, not API changes)](#11-documentation-structure-deltas-traps-not-api-changes)
12. [What this table does not settle](#12-what-this-table-does-not-settle)

---

## 1. Headline changes affecting logical networking

| Area | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| **NSX version / build** | 9.0.0.0 / 24733065 | 9.1.0.0 / 25318225 | **[DOC — BOM pages]** |
| **Machine-readable spec availability** | **none published** at the `9.0.0.0` corpus tag | `nsx-policy` (3,729 ops, `basePath: /policy/api/v1`), `nsx-manager` (1,453), `nsx-global-policy` (1,009, `basePath: /global-manager/api/v1`) | **[ASYMMETRIC]** |
| **Dynamic BGP peering** | static per-neighbor config only | *"define a range of IP addresses that will be used to determine when a Tier-0 gateway should establish BGP peering."* | **[DOC — VCF 9.1 What's New: NSX]**. **The write API for this is UNVERIFIED — see §3.** |
| **Virtual Network Appliance (VNA)** | does not exist | new appliance *"designed to run and support network services within distributed VPC environments"*; full cluster + appliance CRUD in the spec | **[DOC + SPEC-9.1]** |
| **IPAM IP Block limits** | 1 CIDR, 1 IP range | *"up to 10 CIDRs, 10 IP ranges (from one previously), and to exclude specific IPs"* | **[DOC — 9.1 What's New]**; the array shape is **[SPEC-9.1]**, the number 10 is prose-only — see §4 |
| **Uplink IPFIX** | Logical Switch IPFIX ConnectionTrack module introduced | *"the Connection Track based IPFIX does not support uplink port… As IPFIX will not be supported on the uplink port group, the dependent 'LagIpfixConfig' and 'overwrite port policy Netflow' will not be supported."* | **[DOC — 9.1 product support notes]** + **[SPEC-9.1 negative result]** — see §5 |
| **NSX Manager sharing** | not stated | *"VCF Management Domain can now share NSX Managers with other VCF workload domains."* | **[DOC — 9.1 What's New]** |
| **Locale-service-scoped VPN paths** | present, not flagged | **`deprecated: true` on every operation** | **[DOC — 9.1 API reference]** + **[SPEC-9.1]** — see §6 |
| **Manager-API fabric tree** | unsupported by product statement, no spec flag available | `/transport-nodes`, `/transport-node-profiles`, `/host-switch-profiles` all **`deprecated: true` in the spec** | **[ASYMMETRIC]** — see §7 |
| **L3 scale** | baseline | *"configuration maximums for a number of aspects of VCF Networking (including L3 Networking scale) has been increased."* Actual figures not published in the retrieved pages. | **[DOC — 9.1 What's New]** |
| **Removed operations (all three NSX APIs)** | — | **17 NSX Manager API + 9 NSX Policy API + 1 NSX Autonomous Edge API operations removed** | **[DOC — VCF 9.1 product support notes]** — see §8 |

---

## 2. Object-by-object API surface

Every 9.1 operationId below was confirmed in the 9.1 spec inventory.

| Object | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Policy API base path | `/policy/api/v1` | unchanged, confirmed as the spec `basePath` | **[ASYMMETRIC]** |
| Policy-only statement | *"The Manager mode and Manager API provided by NSX 4.x and earlier are no longer supported."* | same sentence, verbatim, in the 9.1 admin guide | **[DOC]** |
| Segment create/replace | `PUT /infra/segments/{segment-id}` | same, **spec-confirmed** (`CreateOrReplaceInfraSegment`) | **[ASYMMETRIC]** |
| Segment read / patch / delete / list | **not observed** on a 9.0 page (only `PUT` was) | `ReadInfraSegment`, `PatchInfraSegment`, `DeleteInfraSegment`, `ListAllInfraSegments` | **[SPEC-9.1]** — 9.0 side unverified, not absent |
| Segment `?force=true` variants | not observed | `ForceDeleteInfraSegment`, `PatchInfraSegmentWithForce`, `CreateOrReplaceInfraSegmentWithForce`, `ForceDeleteSegment` | **[SPEC-9.1]** |
| Segment sub-resources — ports, state, statistics, effective-profiles, ARP/MAC/TEP tables, DHCP static bindings, connection binding maps, service segments | not observed | full trees present (`ListInfraSegmentPorts`, `GetInfraSegmentState`, `GetInfraSegmentStatistics`, `ListInfraSegmentEffectiveProfiles`, `GetInfraSegmentInterfaceArpTable`, `GetInfraSegmentMacTable`, `GetInfraSegmentTepTable`, `ReadInfraSegmentDhcpStaticBinding`, `ReadInfraSegmentConnectionBindingMap`, `ReadServiceSegment`, …) | **[SPEC-9.1]** |
| Segments under a Tier-1 (fixed) | `GET /infra/tier-1s/{tier-1-id}/segments` + global and project variants | same, **spec-confirmed** (`ListSegments`, `GlobalInfraListSegments`, `OrgsOrgIdProjectsProjectIdInfraListSegments`) plus per-segment CRUD (`ReadSegment`, `PatchSegment`, `CreateOrReplaceSegment`, `DeleteSegment`) | **[ASYMMETRIC]** |
| **Fixed-vs-flexible listing caveat** | not stated on a 9.0 page | stated verbatim in the spec: this endpoint *"does not return flexible segments"* and the search API is the workaround | **[SPEC-9.1]** — behavior assumed identical in 9.0 |
| Tier-0 read | `GET /infra/tier-0s/{tier-0-id}` + `global-infra` variant | same, **spec-confirmed** (`ReadTier0`, `GlobalInfraReadTier0`) | **[ASYMMETRIC]** |
| Tier-0 list / write / state / reprocess / failover | not observed | `ListTier0s`, `PatchTier0`, `CreateOrReplaceTier0`, `DeleteTier0`, `GetTier0State`, `Tier0GatewayReprocess`, `Tier0GatewayFailover`, `GatewaySiteFailoverAction` | **[SPEC-9.1]** |
| Tier-1 read | `GET /infra/tier-1s/{tier-1-id}` + global and project variants | same, **spec-confirmed** (`ReadTier1`, `GlobalInfraReadTier1`, `OrgsOrgIdProjectsProjectIdInfraReadTier1`) | **[ASYMMETRIC]** |
| Tier-1 list / write / state / advertised-networks / reprocess / failover | not observed | `ListTier1`, `PatchTier1`, `CreateOrReplaceTier1`, `DeleteTier1`, `GetTier1State`, `GetTier1AdvertisedNetworks`, `Tier1GatewayReprocess`, `Tier1GatewayFailover` | **[SPEC-9.1]** |
| **Gateway service reallocation** | not observed | `POST /infra/gateways/action/reallocate` (`GatewayReallocation`) — *"Reallocate or re-balance service instances of gateways within edge or VNA clusters"*; project variant `OrgsOrgIdProjectsProjectIdInfraGatewayReallocation` | **[SPEC-9.1]** — the description names **VNA clusters**, which do not exist in 9.0, so this is a genuine 9.1 addition |
| Locale services (T0 and T1) | **no 9.0-pinned page at all** | `ListTier0LocaleServices`, `ReadTier0LocaleServices`, `PatchTier0LocaleServices`, `CreateOrReplaceTier0LocaleServices`, `DeleteTier0LocaleServices`; same family for Tier-1 and for the project scope | **[SPEC-9.1]** |
| Gateway interfaces | **no 9.0-pinned page** | `ListTier0Interfaces`, `ReadTier0Interface`, `PatchTier0Interface`, `CreateOrReplaceTier0Interface`, `DeleteTier0Interface` + statistics/ARP/DAD reads | **[SPEC-9.1]** |
| Static routes and BFD peers | **no 9.0-pinned page** | `ListTier0StaticRoutes`, `ReadTier0StaticRoutes`, `PatchTier0StaticRoutes`, `CreateOrReplaceTier0StaticRoutes`, `DeleteTier0StaticRoutes`, `ReadStaticRouteBfdPeer`, `UpdateStaticRouteBfdPeer`, … | **[SPEC-9.1]** |
| BGP config and neighbors | **no 9.0-pinned page** | `ReadBgpRoutingConfig`, `PatchBgpRoutingConfig`, `CreateOrReplaceBgpRoutingConfig`, `DeleteOverriddenBgpRoutingConfig`, `ListBgpNeighborConfigs`, `ReadBgpNeighborConfig`, `PatchBgpNeighborConfig`, `CreateOrReplaceBgpNeighborConfig`, `DeleteBgpNeighborConfig`, `GetTier0BgpNeighborsStatus`, `GetTier0BgpNeighborRoutes`, `GetTier0BgpNeighborAdvertisedRoutes`, `ReadBgpTroubleshootConfig` | **[SPEC-9.1]** |
| Route-controller BGP tree | not observed | `/infra/route-controllers/{router-controller-id}/bgp[/neighbors/{neighbor-id}]` — `ReadControllerBgpRoutingConfig`, `CreateOrReplaceControllerBgpNeighborConfig`, … | **[SPEC-9.1]** |
| Transport zone read | `GET …/transport-zones/{transport-zone-id}` + `global-infra` variant | same, **spec-confirmed** (`ReadTransportZoneForEnforcementPoint`, `GlobalInfraReadTransportZoneForEnforcementPoint`) | **[ASYMMETRIC]** |
| Transport zone list / write / spans / status reports | not observed | `ListTransportZonesForEnforcementPoint`, `PatchTransportZoneForEnforcementPoint`, `CreateOrUpdateTransportZoneForEnforcementPoint`, `DeleteTransportZoneForEnforcementPoint`, `GetAllNetworkSpansByTz`, `GetAllTZStatus`, `GetHeatmapTZStatus`, `ListTNStatusForTZ`, `GetTNReportForATZ`, `GetTNJsonReportForATZ` | **[SPEC-9.1]** |
| Edge cluster read | `GET …/edge-clusters/{edge-cluster-id}` + `global-infra` variant | same, **spec-confirmed** (`ReadEdgeClusterForEnforcementPoint`) — this **closes a gap** the prose research left open, which had the 9.1 read as "not listed on the 9.1.0 category page" | **[ASYMMETRIC]** |
| Edge cluster list / write / members / allocation / relocate / replace | not observed for 9.0 | `ListEdgeClustersForEnforcementPoint`, `PatchPolicyEdgeCluster`, `CreateOrUpdatePolicyEdgeCluster`, `DeletePolicyEdgeCluster`, `ListEdgeNodesUnderEdgeClusterForEnforcementPoint`, `ReadEdgeNodeUnderEdgeClusterForEnforcementPoint`, `GetPolicyEdgeClusterAllocationStatus`, `GetPolicyEdgeClusterStatus`, `RelocateAndRemovePolicyEdgeNode`, `ReplacePolicyEdgeNode` | **[SPEC-9.1]** |
| Edge cluster HA profiles | not observed | `ListPolicyEdgeClusterHighAvailabilityProfile`, `ReadPolicyEdgeClusterHighAvailabilityProfile`, `PatchPolicyEdgeClusterHighAvailabilityProfile`, `CreateOrUpdatePolicyEdgeClusterHighAvailabilityProfile`, `DeletePolicyEdgeClusterHighAvailabilityProfile` | **[SPEC-9.1]** |
| Policy edge transport nodes | not observed | `ListPolicyEdgeTransportNode`, `GetPolicyEdgeTransportNode`, `PatchPolicyEdgeTransportNode`, `CreateOrUpdatePolicyEdgeTransportNode`, `DeletePolicyEdgeTransportNode`, `ListPolicyEdgeTransportNodesState`, `ListPolicyEdgeTransportNodesStatus`, `SyncPolicyEdgeTransportNode` | **[SPEC-9.1]** |
| Policy host transport node status family | **negative result** in 9.0 research (no content retrieved) | `ListHostTNStatus`, `GetAllTNsStatus`, `GetHostTNStatus`, `GetTunnels`, `GetPnicStatusesForTN`, `ListAllLldpNeighborInterfaces`, `GetTnHyperbusStatus`, `GetTnContainerAgentStatus`, `ListRemoteTNStatus` | **[SPEC-9.1]** |
| Policy host switch / transport node profiles | not observed | `ListPolicyHostSwitchProfiles`, `GetPolicyHostSwitchProfile`, `PatchPolicyHostSwitchProfile`, `CreateOrUpdatePolicyHostSwitchProfile`, `DeletePolicyHostSwitchProfile`, `ListPolicyHostTransportNodeProfiles`, `GetPolicyHostTransportNodeProfile`, `CreateOrUpdatePolicyHostTransportNodeProfile`, `DeletePolicyHostTransportNodeProfile` | **[SPEC-9.1]** |
| Host transport node collections | not observed | `ListHostTransportNodeCollections`, `DeleteHostTransportNodeCollection` | **[SPEC-9.1]** |
| Sites and enforcement points | path shape 9.0-verified; list endpoints not observed | `ListSites`, `ReadSite`, `CreateOrUpdateInfraSite`, `DeleteInfraSite`, `ListEnforcementPointForSite`, `ReadEnforcementPointForSite`, `CreateOrUpdateEnforcementPointForSite`, `DeleteEnforcementPointForSite` | **[SPEC-9.1]** |
| `deployment-zones` enforcement-point tree | present, not flagged | **every operation `deprecated: true`** (`ListEnforcementPointForInfra`, `ReadEnforcementPointForInfra`, `PatchEnforcementPointForInfra`, `CreateOrUpdateEnforcementPointForInfra`, `DeleteEnforcementPoint`) | **[SPEC-9.1]** |
| Realization status | not observed | `ReadIntentStatus`, `ListRealizedEntities`, `ReadRealizedEntity`, `RefreshRealizedState` | **[SPEC-9.1]** |
| Search API | referenced in prose, **concrete path unresolvable** in either doc set | `GET /search/query` (`QuerySearch`), `GET /search/dsl` (`DslSearch`), `POST /search/reconcile`, `GET /search/reconcile/status` | **[SPEC-9.1]** — resolves a gap the prose research could not close in either version |
| Hierarchical `/infra` | not observed | `ReadInfra`, `PatchInfra`, `UpdateInfra` | **[SPEC-9.1]** |

---

## 3. Dynamic BGP peering — a documented feature with an unverified API

The VCF 9.1 What's New states: *"Dynamic BGP peering: define a range of IP addresses that will be used
to determine when a Tier-0 gateway should establish BGP peering."* **[DOC]**

**The configuration surface for it could not be located in the 9.1 policy spec.** Concretely:

- `BgpNeighborConfig` still declares `neighbor_address` and `remote_as_num` as its two **required**
  fields, and exposes no range, prefix or peer-group field. **[SPEC-9.1]**
- There is no `dynamic-neighbors`, `neighbor-groups`, `peer-group` or similarly named path anywhere in
  the 3,729-operation policy spec. **[SPEC-9.1 — negative result]**
- The only trace is a **read-only** field `neighbor_path`, described as *"Policy intent path of dynamic
  bgp neighbor"*, on two **status** schemas: `PolicyBgpNeighborStatus` and
  `RouteControllerBgpNeighborStatus`. **[SPEC-9.1]**

So: the feature exists, dynamically-learned neighbours are **observable** in BGP status output, and the
**write path is UNVERIFIED**. Do not construct one. Confirm against the appliance's own OpenAPI
document (`GET /api/v1/spec/openapi/nsx_policy_api.json`) or the 9.1 UI before scripting it.

For **9.0** the feature does not exist at all — it is a 9.1 What's New item. Do not offer it.

---

## 4. IPAM IP Block: 1 → 10 CIDRs and ranges

The 9.1 What's New states the IP Block now supports *"up to 10 CIDRs, 10 IP ranges (from one
previously), and to exclude specific IPs"*, that providers can share IP Blocks *"while limiting the
visibility on the content of the IP Block"*, and that Distributed DHCP auto-excludes detected static
IPs. **[DOC]**

What the spec confirms **[SPEC-9.1 — `IpAddressBlock`]**:

| Field | Status |
|---|---|
| `cidrs` | array of CIDR strings — *"Represents list of CIDRs."* |
| `cidr` | singular, **`x-deprecated: true`** — the 1→many change is visible here |
| `ranges` | array of `IpPoolRange` |
| `excluded_ips` | array of `IpPoolRange` — *"Represents list of excluded IP address in the form of start and end IPs"* |
| `subnet_exclusive` | *"this block is reserved for direct vlan extension use case. This flag cannot be modified from true to false."* |
| `sync_realization`, `third_party_ipam`, `total_size`, `usage_percentage`, `ip_address_type` | present |

Operations **[SPEC-9.1]**: `ListIpAddressBlocks`, `ReadIpAddressBlock`, `CreateOrPatchIpAddressBlock`,
`CreateOrReplaceIpAddressBlock`, `DeleteIpAddressBlock`, plus `GetIpAddressBlockAllocationState`,
`GetAllIpAddressBlocksUsage`, `GetFreeSubnetCountForIpAddressBlock`, `GetIpAddressBlockState`.

**Caveat, stated plainly:** the *array shape* is spec-confirmed; **the number 10 is not.** The spec
declares no `maxItems` on `cidrs`, `ranges` or `excluded_ips`. Treat "10" as the release-note figure,
not as a spec-enforced limit. Deeper IPAM coverage belongs to the forthcoming `nsx-network-services`
skill.

---

## 5. Uplink IPFIX dropped

Verbatim from the 9.1 product support notes **[DOC]**:

> *"VDS IPFIX will be backed with NSX Connection Track based IPFIX data path to export TCP connection
> information. However, the Connection Track based IPFIX does not support uplink port due to
> performance constraints. As IPFIX will not be supported on the uplink port group, the dependent
> 'LagIpfixConfig' and 'overwrite port policy Netflow' will not be supported."*

Corroborating spec evidence: **`LagIpfixConfig` does not appear anywhere in the 9.1 policy spec or the
9.1 manager spec** (0 occurrences in both). **[SPEC-9.1 — negative result]**

Read that carefully. Because there is no 9.0 spec to diff against, absence at 9.1 is **consistent with**
removal but is not by itself proof of it — the prose statement is what establishes the change. The
Policy IPFIX profile trees that **do** survive in 9.1 are `/infra/ipfix-dfw-profiles`,
`/infra/ipfix-dfw-collector-profiles`, `/infra/ipfix-l2-profiles` and
`/infra/ipfix-l2-collector-profiles`, all with full CRUD. **[SPEC-9.1]**

Practical effect for this skill: a 9.0 design that collects flow data on uplink port groups does not
carry forward to 9.1. Flow export moves to the segment/L2 profiles.

---

## 6. Locale-service-scoped VPN paths deprecated

In 9.0 both shapes were documented without a deprecation flag. In 9.1 the locale-service-scoped IPSec
VPN tree is **`deprecated: true` on every operation** **[SPEC-9.1]**, matching the 9.1 API reference
note **[DOC]**:

```
/infra/tier-0s/{tier-0-id}/locale-services/{locale-service-id}/ipsec-vpn-services            DEPRECATED
/infra/tier-0s/{tier-0-id}/locale-services/{locale-service-id}/ipsec-vpn-services/{service-id} DEPRECATED
  … /local-endpoints[/{local-endpoint-id}]                                                    DEPRECATED
```

(`ListTier0IPSecVpnServices`, `GetTier0IPSecVpnService`, `CreateOrPatchTier0IPSecVpnService`,
`CreateOrUpdateTier0IPSecVpnService`, `DeleteTier0IPSecVpnService`, `ListTier0IPSecVpnLocalEndpoints`,
`GetTier0IPSecVpnLocalEndpoint`, `DeleteTier0IPSecVpnLocalEndpoint`, …)

Prefer the **gateway-scoped** form: `/infra/tier-0s/{tier-0-id}/ipsec-vpn-services/{service-id}` and
`/infra/tier-1s/{tier-1-id}/ipsec-vpn-services/{service-id}`.

This is in a *networking* delta table only because it changes the shape of a gateway sub-tree an agent
will encounter while reading a Tier-0. **VPN configuration itself belongs to the forthcoming
`nsx-network-services` skill** — do not treat this section as VPN coverage.

A related shape note the spec surfaces on `ListSegments` **[SPEC-9.1]**: *"Please note that old vpn
path deprecated. If user specify old l2vpn path in the 'l2_extension' object in the PUT/PATCH API
payload, the path returned in the GET response payload may include the new path instead of the
deprecated l2vpn path. Both old and new l2vpn path refer to same resource. there is no functional
impact."* So a round-tripped segment body may come back with a different `l2_extension` path than you
sent. That is expected, not drift.

---

## 7. Manager-API fabric tree: now formally deprecated in the spec

In both versions the product documentation says the Manager API is no longer supported for logical
networking. What is **new in 9.1 is the machine-readable confirmation** — the fabric operations carry
`deprecated: true` in `nsx_api.yaml`:

| Path | operationIds | Evidence |
|---|---|---|
| `GET·POST /transport-nodes` | `ListTransportNodesWithDeploymentInfo`, `CreateTransportNodeWithDeploymentInfo` | **[SPEC-9.1 — `deprecated: true`]** |
| `GET·PUT·DELETE /transport-nodes/{transport-node-id}` | `GetTransportNodeWithDeploymentInfo`, `UpdateTransportNodeWithDeploymentInfo`, `DeleteTransportNodeWithDeploymentInfo` | **[SPEC-9.1 — `deprecated: true`]** |
| `/transport-node-profiles[/{id}]` | `ListTransportNodeProfiles`, `CreateTransportNodeProfile`, `GetTransportNodeProfile`, `UpdateTransportNodeProfile`, `DeleteTransportNodeProfile` | **[SPEC-9.1 — `deprecated: true`]** |
| `/host-switch-profiles[/{id}]` | `ListHostSwitchProfiles`, `CreateHostSwitchProfile`, `GetHostSwitchProfile`, `UpdateHostSwitchProfile`, `DeleteHostSwitchProfile` | **[SPEC-9.1 — `deprecated: true`]** |
| `POST /transport-nodes/{node-id}?action=redeploy` | `RedeployEdgeTransportNode` | **[SPEC-9.1 — `deprecated: true`]** |

Not everything under `/transport-nodes` is deprecated — the **status and central-CLI** reads survive
unflagged (`GetTransportNodeStatus`, `QueryTunnels`, `GetTunnel`, `ListTransportNodeCapabilities`,
`ListTransportNodeInterfaces`, `GetPnicStatusesForTransportNode`, `ListRemoteTransportNodeStatus`,
`InvokeGetTransportNodeCentralAPI`). **[SPEC-9.1]** So "the Manager transport-node tree is gone" is
too strong; "its *lifecycle* verbs are deprecated" is right.

Policy replacements: `/infra/host-switch-profiles`, `/infra/host-transport-node-profiles`, and the
`/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-transport-nodes` tree. **[SPEC-9.1]**

**For 9.0 this is [ASYMMETRIC]:** the same paths exist and the same product statement applies, but
there is no 9.0 spec in which to read a deprecation flag.

---

## 8. Removed operations — counts published, paths **not** published

The VCF 9.1 product support notes state the counts and the affected **themes**, but **Broadcom does not
publish the individual paths or operation IDs.** Stated plainly so no downstream consumer guesses:

**The paths of the removed operations are not published.** They are absent from the vendor's own
release documentation, not merely unknown to this file.

| API surface | Count removed in 9.1 | Themes named by Broadcom |
|---|---|---|
| **NSX Manager API** (`/api/v1`) | **17** | System Health Agent metrics/monitoring endpoints; **port mirroring (SPAN) session management endpoints**; node user enumeration |
| **NSX Policy API** (`/policy/api/v1`) | **9** | **VPC Subnet Bridge Profiles lifecycle operations**; PMaaS firewall exclude-list management; **Infrastructure Policy Labels operations** |
| **NSX Autonomous Edge API** | **1** | Edge node user enumeration |

**[DOC — VCF 9.1 product support notes]**

Notes for a networking-focused agent:

- Two of the three Policy-API removal themes touch **networking**: VPC Subnet Bridge Profiles and
  Infrastructure Policy Labels. If a 9.0 script manages either, it is the most likely thing to break
  on upgrade — and you cannot get the path list from documentation.
- The port-mirroring Manager-plane API is **removed** and replaced by a Policy API supporting
  *"Local SPAN as well RSPAN"*. **[DOC]** The replacement paths are in the `nsx-security-policy`
  skill's deltas file; they are group/domain-scoped rather than segment-scoped.
- The removals do **not** touch segments, Tier-0s, Tier-1s, transport zones, edge clusters or BGP —
  the full CRUD trees for all of those are present in the 9.1 spec (see §2).
- **Do not attempt to reconstruct the removed paths by diffing a 9.0 spec against the 9.1 spec** —
  there is no 9.0 spec to diff against.
- **How to detect a removal against a live 9.0 appliance:** fetch that appliance's own
  `/api/v1/spec/openapi/nsx_policy_api.json` and `nsx_api.json` and diff them against the published
  9.1 specs. That is the only route to the actual list, and it requires access to a 9.0 appliance.

---

## 9. Path families and tenancy

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Local `/infra/…` | present | present | **[ASYMMETRIC]** |
| Federation `/global-infra/…` | documented for segments, T0, T1, transport zones, edge clusters — **reads only** | reads confirmed; **on the local manager the segment and gateway objects themselves are GET-only**, while writes live on the Global Manager appliance (`basePath: /global-manager/api/v1`, `GlobalInfraCreateOrReplaceInfraSegment`, `GlobalInfraCreateOrReplaceTier0`, `GlobalInfraCreateOrReplaceTier1`, …) | **[SPEC-9.1]** — this read/write split was not visible in the 9.0 prose |
| …but the split is not clean | — | 114 non-GET `global-infra` operations **do** exist in the local policy spec: segment **ports**, Tier-0 **BGP** config and neighbors, Tier-0 **interfaces**, Tier-0 **static routes** | **[SPEC-9.1]** — do not generalise "global-infra is read-only" |
| Projects `/orgs/{org}/projects/{proj}/infra/…` | documented for infra segments, Tier-1 segments, Tier-1 reads | full Tier-1 CRUD (`OrgsOrgIdProjectsProjectIdInfraCreateOrReplaceTier1`, …), full segment CRUD, locale services, `gateways/action/reallocate` | **[ASYMMETRIC]** |
| **Projects cannot own a Tier-0** | not characterised | the only project-scoped Tier-0 operation is `POST …/infra/tier-0s/{tier-0-id}/actions/failover` (`OrgsOrgIdProjectsProjectIdInfraTier0GatewayFailover`) — no create, read, update or delete | **[SPEC-9.1]** |
| **Fabric is not tenant-scoped** | not characterised | **no** project-scoped `transport-zones` or `edge-clusters` paths exist in the 9.1 policy spec | **[SPEC-9.1 — negative result]** |
| Org / project / VPC discovery | not observed | `ListOrg`, `ListProject`, `GetProject`, `PatchProject`, `UpdateProject`, `DeleteProject`, `ListVpc`, `GetVpc`, `PatchVPC`, `UpdateVpc`, `DeleteVpc` | **[SPEC-9.1]** |
| VPC subnets and transit gateways | VPCs and Transit Gateways are 9.0 features per the What's New; **no API paths opened on a 9.0 page** | `ListVpcSubnet`, `GetVpcSubnet`, `PatchVpcSubnet`, `UpdateVpcSubnet`, `DeleteVpcSubnet`; `ListTransitGateway`, `ReadTransitGateway`, `PatchTransitGateway`, `CreateOrReplaceTransitGateway`, `DeleteTransitGateway`, `TransitGatewayFailover`, `VpcGatewayFailover` | **[SPEC-9.1]** |
| VPC feature depth | VPCs, subnets, Transit Gateways (centralized + distributed), Distributed VLAN connectivity, VPC-Ready Workload Domains | multiple distributed TGWs per project, multiple TGWs per project with independent HA modes and Proxy-ARP, 1:N SNAT on the distributed TGW, EVPN-VXLAN, VLAN extension of VPC subnets, VPC Connectivity Policy (isolated / promiscuous VPCs), TGW span definable from vCenter | **[DOC — 9.0 and 9.1 What's New]** |

**A VPC subnet is not a `Segment`.** They are separate object models with separate paths. When a user
is working inside a VPC, `/infra/segments` is the wrong tree.

---

## 10. Platform and VCF-integration changes that affect a networking agent

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Standalone NSX install/upgrade | *"Starting with NSX 9.0, a standalone NSX installation or upgrade is not supported."* | not restated | **[DOC — 9.0 only]** |
| NSX per vCenter | *"VMware supports only one NSX instance for the same vCenter instance."* | not restated | **[DOC — 9.0 only]** |
| NSX Manager sharing | not stated | *"VCF Management Domain can now share NSX Managers with other VCF workload domains."* Does **not** contradict one-NSX-per-vCenter — it is one NSX Manager serving multiple workload domains, so an object you edit may serve more than one domain | **[DOC — 9.1]** |
| Out-of-band NSX edits | no reconciliation statement | **SDDC Manager network sync** reconciles *"network configuration changes done directly in vCenter or NSX Manager"* | **[DOC — 9.1]** |
| Authoritative VCF-owned-object list | **does not exist** | **does not exist** | **[DOC — negative result in both]** |
| Overlay on physical servers | **removed in 9.0** — *"NSX 9.0.0 no longer supports the deployment of NSX agents on physical servers."* | (removed) | **[DOC — 9.0]** |
| TEP on management VMkernel | 9.0 allows TEPs to use the management VMkernel (VMK0) IP | 9.1 adds *"overlay Tunnel EndPoint (TEP) can now be configured directly from vCenter like other vmkernel NICs"* and VPC-ready domains can add TEP config after the fact | **[DOC]** |
| Enhanced Data Path | EDP Standard is *"default host switch mode of operation for new VCF Workload Domains"*; EDP Fast Path; Industrial vSwitch with PRP | FPO hardware steering, Uniform Passthrough (UPT), Enhanced Direct Path I/O with GPUDirect RDMA, posted-interrupt VMXNET3 latency work, SR-IOV, LRO for Antrea | **[DOC]** |
| DPDK | not stated | upgraded to **24.11** | **[DOC — 9.1]** |
| Edge platform | Edge Host Affinity; edge install/config via vCenter; Gateway Firewall disabled by default for greenfield | new simplified Edge Node / Edge Cluster UI workflow; Bare Metal Edge NIC support (Broadcom 574X/575X, Mellanox CX6 LX); control-plane packet prioritization on edge uplinks; *"VLAN and MTU pre-check for the Edge node"* during Edge VM deployment; Bare Metal Edge **import** into VCF | **[DOC]** |
| LACP / LAG | — | configurable directly in the UI on VCF workflows | **[DOC — 9.1]** |
| Upgrade sequence | baseline | *"Move NSX Edge/SVM Upgrades to the End of Upgrade Sequence"* — edge clusters upgraded at the end of the domain upgrade | **[DOC — 9.1]** |
| Appliance OS | not stated | *"All NSX appliances have been upgraded to Ubuntu 24.04"* with chiseled containers | **[DOC — 9.1]** |
| ESXi accounts created by NSX | creates `mux_user`, `da-user`, `nsx-user`, `lldpVim-user` | **no longer creates** those accounts | **[DOC — 9.1]** |
| NSX Load Balancer entitlement | general-purpose LB removed from VCF entitlement; Avi recommended; NSX LB retained only for VCF infrastructure and vSphere Supervisor | not restated; 9.1 adds a **VPC L4 load balancer via the VNA** and *"support for AVI load balancers with VPCs and Transit Gateways"* | **[DOC — 9.0 for the entitlement; 9.1 for the VNA LB]** — relevant here only because it should inform `Tier1.pool_allocation` sizing |
| FIPS | *"Components including NSX operate in FIPS-enabled mode by default and cannot be deactivated"* | not restated | **[DOC — 9.0]** |

> **Caution on the "not restated" rows.** The 9.0 constraints above were sourced from the **9.0**
> product support notes and were not re-verified in the 9.1 doc set. "Not restated" is not "revoked."
> Do not assert them for 9.1 without re-checking, and do not assume they lapsed.

---

## 11. Documentation-structure deltas (traps, not API changes)

| Item | VCF 9.0 | VCF 9.1 |
|---|---|---|
| Developer portal root | `https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/` (also `9.0.1`, `9.0.2`) | `.../9.1.0/` |
| Portal nav taxonomy | grouped by *Federation / Management Plane API / NSX Application Platform / Policy / System Administration* | regrouped by function: *Certificates, Enforcement Points, Federation, Inventory, Monitoring, Multi-Tenancy, Networking, Policy, Search, Security, System, Troubleshooting, User Management, VPC Networking* — **no "Management Plane API" top-level group** |
| Networking category slugs | `policy_networking.html`, `management_plane_api_networking.html` | `networking_switching_segments.html`, `networking_routing_tier-0s.html`, `networking_routing_tier-1s.html`, `networking_switching_transport_zones.html`, `system_fabric_edge_clusters.html`, `networking_ip_management_ip_pools.html` |
| Product doc URL shape | `.../9-0/advanced-network-management/administration-guide/<topic>.html` | `.../9-1/advanced-network-management/<topic>.html` (**no `administration-guide/` segment**) |

The slug change is a real trap: **adding or removing the `policy_` prefix is not a reliable translation
between the doc sets.** `policy_networking_switching_segments.html` does not exist for 9.0.0. Navigate
the left-hand tree rather than guessing a slug. A nonexistent page returns the SPA navigation shell —
nav links and no verb/path table. **If a fetch yields only category links, the URL is wrong; do not
read that as "the endpoint does not exist."**

The nav-taxonomy change is an **observation about documentation structure**, based on rendered
navigation menus — **not** proof that the Management Plane API surface was removed.

---

## 12. What this table does not settle

1. **Dynamic BGP peering's write API** (§3). Documented feature, no locatable configuration path.
2. **The 27 removed operations' paths** (§8). Not published by the vendor.
3. **The "10 CIDRs / 10 ranges" figure** (§4). Prose-only; the spec declares no `maxItems`.
4. **The L3 scale increase figures.** *"has been increased"* is all the retrieved pages say.
5. **Whether the 9.0 constraints still hold in 9.1** (§10, "not restated" rows).
6. **Everything about 9.0 that this table records as "not observed."** With no 9.0 spec, that phrase
   means *the prose docs did not show it*, never *it is absent*. The appliance's own OpenAPI document
   is the only authority.
