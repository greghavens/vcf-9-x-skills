# NSX network services — VCF 9.0 → 9.1 change table

Scope: **NAT, load balancing (including Avi / NSX ALB), IPSec and L2 VPN, IPAM (IP pools and IP
blocks), and VPC-scoped services.** Distributed firewall and security policy deltas belong to
`nsx-security-policy/references/deltas.md`; segments, Tier-0/Tier-1 creation, routing, transport
zones and edge platform deltas belong to `nsx-segments-routing`.

Source classes, same convention as the version files:

| Tag | Meaning |
|---|---|
| **[DOC]** | Version-pinned Broadcom prose (release notes, product support notes, admin guide, developer portal). |
| **[SPEC-9.1]** | Confirmed in the machine-extracted 9.1 spec inventory (`9.1.0.0` tag of `github.com/vmware/vcf-api-specs`). |
| **[ASYMMETRIC]** | The 9.1 side is spec-confirmed; the 9.0 side is prose-only, because **no NSX spec is published at the `9.0.0.0` tag**. |
| **[9.0-UNVERIFIABLE]** | The 9.0 side could not be established *at all* — the research records it as unretrievable. Stronger than "not observed". |

> **The structural asymmetry that governs this whole table.** The public spec corpus has **no NSX
> specification at `9.0.0.0`** — `nsx-policy`, `nsx-manager` and `nsx-global-policy` are absent at
> that tag and present only at `9.1.0.0` (3,729 / 1,453 / 1,009 operations). A row saying "not
> observed in 9.0" almost never means "proven absent in 9.0"; it means the 9.0 prose docs did not
> show it. For NAT and VPN it is worse still — see the `[9.0-UNVERIFIABLE]` rows. Only the
> appliance's own OpenAPI document settles a 9.0 question.

---

## 1. Headline changes affecting network services

| Area | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| **Distributed Load Balancer / DFW coupling** | Distributed LB coupled to the DFW | *"Distributed Load Balancer is now independently managed and decoupled from the Distributed Firewall (DFW)."* | **[DOC — VCF 9.1 What's New: NSX]** — but see §3, the spec still couples the kill switch |
| **Virtual Network Appliance (VNA)** | does not exist | New appliance *"designed to run and support network services within distributed VPC environments"*; full lifecycle API present | **[DOC — 9.1 What's New]** + **[SPEC-9.1]** |
| **VPC Layer-4 load balancing** | not called out | *"Layer 4 (L4) load balancing service is fully supported"* via the VNA; full `vpc-lbs` / `vpc-lb-*` API family | **[DOC — 9.1]** + **[SPEC-9.1]** |
| **VPC IPSec VPN** | not called out | *"IPSec VPN service is now supported for VPC using centralized external connectivity"*, Policy-Based and Route-Based | **[DOC — 9.1]**; the concrete API family is Transit-Gateway-scoped — see §5 |
| **Avi / NSX ALB with VPCs** | Avi recommended (9.0 entitlement change) | *"support for AVI load balancers with VPCs and Transit Gateways with distributed VLAN connection"*; self-service tenant *"NAT, VPN, Grouping, Firewalling"* in the VCF Automation context | **[DOC — 9.1 What's New]** |
| **IPAM IP Block capacity** | one CIDR, one IP range | *"up to 10 CIDRs, 10 IP ranges (from one previously), and to exclude specific IPs"*; providers can share IP Blocks *"while limiting the visibility on the content of the IP Block"* | **[DOC — 9.1 What's New]** — see §4 for what the spec actually shows |
| **Locale-service-scoped VPN paths** | both path forms historically present; **neither verified for 9.0** | locale-service-scoped IPSec/L2/L3 VPN operations all flagged `deprecated: true`; gateway-scoped is current | **[DOC — 9.1 deprecations]** + **[SPEC-9.1]**; 9.0 side **[9.0-UNVERIFIABLE]** |
| **1:N SNAT** | not called out | *"1:N SNAT when using the distributed Transit Gateway"* | **[DOC — 9.1]** |
| **Machine-readable spec availability** | **none published** at the `9.0.0.0` corpus tag | `nsx-policy` (3,729 ops), `nsx-manager` (1,453 ops), `nsx-global-policy` (1,009 ops) | **[ASYMMETRIC]** |
| **NSX version / build** | 9.0.0.0 / 24733065 | 9.1.0.0 / 25318225 | **[DOC — BOM pages]** |

---

## 2. NAT

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Policy NAT rule paths (`/infra/tier-{0,1}s/{id}/nat/{nat-id}/nat-rules/{nat-rule-id}`) | **could not be verified** | spec-confirmed: `ListPolicyNatOnTier1`, `ListPolicyNatRules`, `GetPolicyNatRule`, `PatchPolicyNatRule`, `CreateOrReplacePolicyNatRule`, `DeletePolicyNatRule`; Tier-0 equivalents `ListPolicyNatOnTier0`, `PatchPolicyNatRuleOnTier0`, … | **[9.0-UNVERIFIABLE]** + **[SPEC-9.1]** |
| Manager-API NAT rule | `GET /api/v1/logical-routers/{id}/nat/rules/{rule-id}` — *"This endpoint is deprecated as of version 9.0."* | (unsupported surface) | **[DOC — 9.0.0 developer portal]** |
| NAT statistics | not observed | `GetPolicyNatRuleStatisticsFromTier1`, `GetPolicyNatRuleStatisticsFromTier0`, `ListPolicyNatRulesStatisticsFromTier{0,1}`, plus per-edge-node `GetNatStatisticsPerPolicyEdgeNode` | **[SPEC-9.1]** |
| Project-scoped NAT | not observed | Tier-1 only: `OrgsOrgIdProjectsProjectIdInfra{Get,Patch,CreateOrReplace,Delete}PolicyNatRule`. **No project-scoped Tier-0 NAT.** | **[SPEC-9.1]** |
| VPC-scoped NAT | not observed | `ListPolicyNatOnVpc`, `GetPolicyNatOnVpc`, `ListPolicyNatRulesOnVpc`, `PatchPolicyVpcNatRuleOnVpc`, `CreateOrReplacePolicyNatRuleOnVpc`, `DeletePolicyNatRuleOnVpc`, `GetPolicyVpcNatRuleStatistics` | **[SPEC-9.1]** |
| Transit-Gateway NAT | Transit Gateways exist in 9.0; TGW NAT not observed | `ListTransitGatewayNat`, `GetTransitGatewayNat`, `ListTransitGatewayNatRules`, `PatchTransitGatewayNatRule`, `CreateOrReplaceTransitGatewayNatRule`, `DeleteTransitGatewayNatRule`, `GetTransitGatewayNatRuleStatistics` | **[SPEC-9.1]** |
| NAT sections | not characterised | `PolicyNat.nat_type` ∈ `INTERNAL`, `USER`, `DEFAULT`, `NAT64`; sections are `_system_owned` and created with the gateway; single-section read exists **only** for VPC and TGW | **[SPEC-9.1]** |
| 1:N SNAT | not called out | supported *"when using the distributed Transit Gateway"* | **[DOC — 9.1]** |
| Federation NAT | `global-infra` documented generally | on the **local** manager `global-infra` NAT is **GET-only**; write verbs live on the Global Manager spec (`GlobalInfraDeletePolicyNatRuleFromTier0`, …) | **[SPEC-9.1]** — a read/write split not visible in the 9.0 prose |
| `PolicyNatRule` schema | never captured | full schema: `action` required; enums, `firewall_match`, `policy_based_vpn_mode`, per-section `sequence_number` ranges | **[SPEC-9.1]** — inferred, not verified, for 9.0 |

---

## 3. Load balancing — including the DLB decoupling and its unresolved conflict

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| LB service read | `GET /infra/lb-services/{lb-service-id}` | same, spec-confirmed (`ReadLBService`) | **[ASYMMETRIC]** |
| LB service list + write verbs | not observed | `ListLBServices`, `PatchLBService`, `UpdateLBService`, `DeleteLBService` | **[SPEC-9.1]** — 9.0 side unverified, not absent |
| Virtual servers | not observed | `ListLBVirtualServers`, `ReadLBVirtualServer`, `PatchLBVirtualServer`, `UpdateLBVirtualServer`, `DeleteLBVirtualServer`; required fields `ports`, `ip_address`, `application_profile_path` | **[SPEC-9.1]** |
| Pools | not observed | `ListLBPools`, `ReadLBPool`, `PatchLBPool`, `UpdateLBPool`, `DeleteLBPool`; `algorithm` enum; `LBPoolMember.ip_address` required | **[SPEC-9.1]** |
| Profiles (app / monitor / persistence / client-SSL / server-SSL) | not observed | `ListLBAppProfiles`, `ListLBMonitorProfiles`, `ListLBPersistenceProfiles`, `ListLBClientSslProfiles`, `ListLBServerSslProfiles`, `ListSslCiphersAndProtocols` + full CRUD | **[SPEC-9.1]** |
| Status / statistics / capacity | not observed | `GetLBServiceStatus`, `GetLBServiceStatistics`, `GetLBVirtualServerStatus`, `GetLBPoolStatistics`, `GetLBNodeUsage`, `GetLBNodeUsageSummary`, `GetLBServiceUsageSummary`, `ReadLBServiceDebugInfo` | **[SPEC-9.1]** |
| **Distributed LB** | coupled to the DFW | *"now independently managed and decoupled from the Distributed Firewall (DFW)"*; in the API a DLB is `LBService` with `size: DLB` and a **Group** `connectivity_path` | **[DOC — 9.1]** + **[SPEC-9.1]** — **conflict, see below** |
| **Avi / NSX ALB integration surface** | not observed on any 9.0 page | `InitiateAlbOnBoardingWorkflow`, `DeleteAlbOnBoardingWorkflow`, `GetALBAuthToken`, `ListAlbControllerInfo` / `CreateOrUpdateAlbControllerInfo`, `AddALBControllerNodeVM`, `ListALBControllerClusterInfo`, `CreateALBControllerCloud`, `CreateALBControllerVcenterServer`, `SetupALBControllerPKIProfile`, `CreateAlbPortalCertificateCSR`, `InstallAlbPortalCertificate`, controller users/credentials | **[SPEC-9.1]** |
| Avi binding object | not characterised | `EnforcementPointConnectionInfo.resource_type` includes **`AviConnectionInfo`**; fields `password`, `certificate`, `managed_by`, `is_default_cert`, `expires_at`, `status` ∈ `ACTIVATE`/`DEACTIVATE_PROVIDER`/`DEACTIVATE_API` | **[SPEC-9.1]** |
| Self-service Avi LB for tenants | not called out | *"support for AVI load balancers with VPCs and Transit Gateways"* and tenant *"Self Service NAT, VPN, Grouping, Firewalling"* in the VCF Automation context | **[DOC — 9.1 What's New]** |
| **NSX LB entitlement** | **narrowed**: general-purpose LB removed from the VCF entitlement; Avi recommended; NSX LB retained only for VCF infrastructure and vSphere Supervisor | **not restated** in the 9.1 support notes | **[DOC — 9.0 only]** — see below |
| VPC LB | not called out | `ListVpcLBServices`, `PatchVpcLBService`, `ListVpcLBVirtualServers`, `ListVpcLBPools`, the five `vpc-lb-*-profiles` families, `GetVpcLBNodeCapacityStatus`, `GetProjectLBNodeCapacityStatus`; body schema is `LBService` | **[SPEC-9.1]** |

### The LB entitlement narrowing — where it stands

VCF **9.0** support notes are explicit: general-purpose NSX load balancing was removed from the VCF
entitlement, Avi Load Balancer is the recommendation, and NSX LB was retained only for VCF
infrastructure and vSphere Supervisor use cases. **[DOC — 9.0]**

**The VCF 9.1 support notes do not restate it.** That is a documentation absence, not a
revocation. Its 9.1 status is therefore **unverified in both directions**: this file will not tell
you it lapsed, and will not tell you it holds.

Practical guidance, which is the same in both versions: `/policy/api/v1/infra/lb-services` accepts
writes regardless — entitlement is not enforced at the endpoint. Raise the licensing question with
the customer before building a general-purpose VIP on NSX LB, and point at Avi. In 9.0 you can
state the constraint as documented; in 9.1 you must state it as unverified.

### The DLB decoupling — unresolved spec-vs-prose conflict

| Source | What it says |
|---|---|
| **[DOC — VCF 9.1 What's New: NSX]** | *"Distributed Load Balancer is now independently managed and decoupled from the Distributed Firewall (DFW)."* |
| **[SPEC-9.1]** `PATCH /policy/api/v1/infra/settings/firewall/security` | *"Turning off distributed services ("enable_firewall": false) will turn off Distributed Firewall, Identity Firewall, Distributed Intrusion Detection and Prevention Service, **Distributed Load Balancer**."* |
| **[SPEC-9.1]** `GET /infra/settings/firewall/security/dependent-services` (`GetDistributedFirewallDependentServices`) example response | lists `"Distributed Load Balancer"` among the dependent services |

**Resolution: none. Recorded, not resolved.** The most defensible reading is that *management* of
the DLB was decoupled (it is its own `LBService` with `size: DLB` and a Group `connectivity_path`)
while the DFW master on/off switch still gates the distributed data path — but that reconciliation
is **[INFERRED]**, not documented.

**What to do:** if a 9.1 user is about to set `enable_firewall: false` on a system running a
distributed load balancer, call `GET /infra/settings/firewall/security/dependent-services` on
*their* appliance and act on what it returns. Do not assert either the release note or the spec as
settled.

---

## 4. VPN

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Gateway-scoped IPSec VPN (`/infra/tier-{0,1}s/{id}/ipsec-vpn-services/…`) | **could not be verified** | spec-confirmed: `ListTier1VpnIPSecVpnServices`, `CreateOrPatchTier1VpnIPSecVpnService`, `ListTier1VpnIPSecVpnLocalEndpoints`, `CreateOrPatchTier1VpnIPSecVpnSession`, `GetTier1VpnIPSecVpnSessionStatus`, plus the Tier-0 equivalents | **[9.0-UNVERIFIABLE]** + **[SPEC-9.1]** |
| **Locale-service-scoped VPN** (`…/locale-services/{locale-service-id}/ipsec-vpn-services/…`) | both forms historically present; **neither verified for 9.0** | present and **every operation flagged `deprecated: true`** — `ListTier0IPSecVpnServices`, `CreateOrUpdateTier0IPSecVpnService`, `GetTier0IPSecVpnSession`, … Same for `l2vpn-services`, `l2vpn-context`/`l2vpns` and `l3vpns` under `locale-services` | **[DOC — 9.1 deprecations]** + **[SPEC-9.1]** |
| Knock-on effect of the deprecation | — | NAT rule `scope` may reference an `IPSecVpnSession`; the spec notes the old session path is deprecated and a `GET` returns the **new** path for the same resource, *"there is no functional impact"* | **[SPEC-9.1]** |
| L2VPN current form | not observed | `/infra/tier-0s/{id}/l2vpn-services[/{service-id}]` with `sessions`, `peer-config`, `remote-mac`, `statistics`, and `?action=create_with_peer_code` | **[SPEC-9.1]** |
| VPN profiles | not observed | `/infra/ipsec-vpn-ike-profiles`, `/infra/ipsec-vpn-tunnel-profiles`, `/infra/ipsec-vpn-dpd-profiles`, full CRUD | **[SPEC-9.1]** |
| Project-scoped VPN | not observed | Tier-1 IPSec and L2VPN under `orgs/{org}/projects/{proj}/infra/tier-1s/{id}/…`; the locale-service variants there are also deprecated | **[SPEC-9.1]** |
| **Transit-Gateway VPN** | not observed | `ListTransitGatewayIPSecVpnServices`, `CreateOrPatchTransitGatewayIPSecVpnService`, `ListTransitGatewayIPSecVpnLocalEndpoints`, `CreateOrPatchTransitGatewayIPSecVpnSession`, `GetTransitGatewayIPSecVpnSessionStatus`, `GetTransitGatewayIpsecVpnSessionSummary` | **[SPEC-9.1]** — this is the concrete surface behind the "VPC IPSec VPN" release note |
| Session schema | never captured | `IPSecVpnSession.resource_type` required, ∈ `PolicyBasedIPSecVpnSession` / `RouteBasedIPSecVpnSession`; `PolicyBased…` requires `rules`; `RouteBased…` carries `tunnel_interfaces`; `IPSecVpnLocalEndpoint.local_address` required | **[SPEC-9.1]** |

---

## 5. IPAM

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| IP pools, allocations, subnets | `GET /infra/ip-pools`; GET·PUT·PATCH·DELETE on `/infra/ip-pools/{id}`, `…/ip-allocations/{id}`, `…/ip-subnets/{id}` | same, spec-confirmed (`ListIpAddressPools`, `ReadIpAddressPool`, `CreateOrPatchIpAddressPool`, `CreateOrReplaceIpAddressPool`, `DeleteIpAddressPool`, and the allocation / subnet equivalents) | **[ASYMMETRIC]** — the best-evidenced 9.0 area in this skill |
| Allocation / subnet **list** endpoints | not observed | `ListIpAddressPoolAllocations`, `ListIpAddressPoolSubnets` | **[SPEC-9.1]** |
| **IP blocks** | **not observed** | `ListIpAddressBlocks`, `ReadIpAddressBlock`, `CreateOrPatchIpAddressBlock`, `CreateOrReplaceIpAddressBlock`, `DeleteIpAddressBlock`, plus `GetIpAddressBlockUsage`, `GetIpAddressBlockAllocationState`, `GetFreeSubnetCountForIpAddressBlock`, `GetAllIpAddressBlocksUsage`, `GetIpAddressBlockState` | **[SPEC-9.1]** |
| **IP Block capacity** | one CIDR, one IP range | *"up to 10 CIDRs, 10 IP ranges (from one previously), and to exclude specific IPs"* | **[DOC — 9.1 What's New]** — see the caveat below |
| IP Block sharing | not called out | providers can share IP Blocks *"while limiting the visibility on the content of the IP Block"*; `IpAddressBlock.visibility` ∈ `PRIVATE`/`EXTERNAL`, immutable once associated | **[DOC — 9.1]** + **[SPEC-9.1]** |
| Distributed DHCP | not called out | auto-excludes detected static IPs | **[DOC — 9.1]** |
| Infoblox integration | not called out | *"discover Infoblox Network Views, DNS Views, and Network Containers"*; `IpAddressBlock.third_party_ipam` present in the spec | **[DOC — 9.1]** + **[SPEC-9.1]** |
| `manager-ip-pools` | not observed | `ListManagerIpPools`, `ReadManagerIpPool` (read-only) | **[SPEC-9.1]** |
| Project / VPC IPAM | not observed | `OrgsOrgIdProjectsProjectIdInfra…` variants for pools and blocks; `ListVpcIpAddressAllocations`, `ListVpcSubnetIpAddressPools`, `GetIpAddressBlockUsageForVPC` | **[SPEC-9.1]** |

### Caveat on the "10 CIDRs" figure

The **1 → 10** expansion is a **release-note statement**, not a spec constraint. In the 9.1
`IpAddressBlock` schema **[SPEC-9.1]**:

- the singular `cidr` field is marked **`x-deprecated: true`**;
- `cidrs`, `ranges` and `excluded_ips` exist as arrays;
- **no `maxItems` is declared on any of them.**

So the spec confirms the *shape* change (singular deprecated, arrays current, exclusions added) and
says nothing about the number 10. Quote the figure as a release note, not as an API limit, and read
the live object if a customer is close to the boundary.

---

## 6. VPC-scoped services and the Virtual Network Appliance

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| VPCs and Transit Gateways exist | yes — VPCs, subnets, centralized and distributed Transit Gateways, Connectivity and Service Profiles | yes, extended | **[DOC — 9.0 and 9.1 What's New]** |
| **Virtual Network Appliance** | does not exist | `ListVirtualNetworkApplianceClusters`, `CreateOrUpdateVirtualNetworkApplianceCluster`, `ListVirtualNetworkAppliances`, `CreateOrUpdateVirtualNetworkAppliance`, plus `action/enter-maintenance-mode`, `action/exit-maintenance-mode`, `action/evacuate`, `action/redeploy`, and cluster `state`/`status`/`allocation/status` | **[DOC — 9.1]** + **[SPEC-9.1]** |
| VNA as an LB host | — | `LBNodeCapacity` is described as *"the available capacity of the edge or virtual network appliance"* | **[SPEC-9.1]** |
| Gateway service reallocation | not observed | `POST /infra/gateways/action/reallocate` (`GatewayReallocation`) — *"Reallocate or re-balance service instances of gateways within edge or VNA clusters"*, plus the project-scoped variant | **[SPEC-9.1]** + **[DOC]** |
| VPC L4 load balancing | not called out | fully supported via the VNA; `vpc-lbs` / `vpc-lb-*` family | **[DOC — 9.1]** + **[SPEC-9.1]** |
| **VPC IPSec VPN** | not called out | *"IPSec VPN service is now supported for VPC using centralized external connectivity"* — **but there is no `…/vpcs/{vpc-id}/ipsec-vpn-services` path in the spec.** The spec-confirmed tenant VPN surface is Transit-Gateway-scoped. | **[DOC — 9.1]**; the mapping to the TGW path family is **[INFERRED]** |
| VPC NAT | not observed | full `…/vpcs/{vpc-id}/nat/…` family; VPC SNAT/DNAT addresses must come from the **external** block associated with the VPC | **[SPEC-9.1]** |
| VPC IP allocation | not observed | `VpcIpAddressAllocation` with `ip_address_block_visibility` ∈ `EXTERNAL`, `PRIVATE`, **`PRIVATE_TGW`** — a three-value enum unique to the VPC object | **[SPEC-9.1]** |
| Multiple / distributed Transit Gateways | centralized and distributed TGW types introduced; no multiplicity statement | multiple distributed TGWs per project with a Distributed VLAN Connection; multiple gateway connections; independent HA modes; Proxy-ARP; EVPN-VXLAN | **[DOC — 9.1]** |
| Tenant self-service | VPC in VCF Automation | *"Self Service NAT, VPN, Grouping, Firewalling"* plus Avi LB in the VCF Automation context | **[DOC — 9.1]** |
| Removed in 9.1 | — | **VPC Subnet Bridge Profiles lifecycle operations** are among the 9 removed NSX Policy API operations. Paths not published. | **[DOC — 9.1 support notes]** |

---

## 7. Cross-cutting constraints worth carrying into an answer

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Policy API base path | `/policy/api/v1` | unchanged, confirmed as the spec `basePath` | **[ASYMMETRIC]** |
| Manager API for networking | *"no longer supported"*; `/api/v1/logical-routers/.../nat/rules/...` *"deprecated as of version 9.0"* | same statement repeated | **[DOC]** |
| Removed operations | — | 17 NSX Manager API + 9 NSX Policy API + 1 Autonomous Edge API operations removed; **paths not published by Broadcom**, only counts and themes | **[DOC — 9.1 support notes]** |
| Standalone NSX install/upgrade | not supported | not restated | **[DOC — 9.0 only]** |
| One NSX per vCenter | *"VMware supports only one NSX instance for the same vCenter instance."* | not restated; 9.1 adds shared NSX Managers across workload domains, which does **not** contradict it | **[DOC — 9.0]** / **[DOC — 9.1]** |
| Out-of-band NSX edits | no reconciliation statement | **SDDC Manager network sync** reconciles *"network configuration changes done directly in vCenter or NSX Manager"* | **[DOC — 9.1]** |
| Authoritative VCF-owned-object list | **does not exist** | **does not exist** | **[DOC — negative result in both]** |
| FIPS | *"Components including NSX operate in FIPS-enabled mode by default and cannot be deactivated"* — relevant to VPN cipher choice | not restated | **[DOC — 9.0]** |
| `_revision` on `/policy` PUT | 9.0 guide: `/policy` URIs *"have slightly different behavior"* | 9.1 guide, verbatim: omit on a creating PUT, supply on subsequent ones | **[DOC]** — a documentation-precision delta, not a behavior delta |
| Partial patch enablement | `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` `{"enable_partial_patch":"true"}` | identical; the **`GET`** verb is spec-confirmed (`GetPartialPatchConfiguration`) | **[ASYMMETRIC]** |
| Session auth | `POST /api/session/create` / `destroy`, `j_username`/`j_password`, `JSESSIONID` + `X-XSRF-TOKEN`, 1800 s | identical; spec-confirmed as absolute paths outside the `/api/v1` basePath | **[ASYMMETRIC]** — details belong to `vcf-foundation` |

> **Caution on the "not restated" rows.** The 9.0 constraints above were sourced from the **9.0**
> product support notes and were not re-verified in the 9.1 doc set. "Not restated" is not
> "revoked." Do not assert them for 9.1 without re-checking, and do not assume they lapsed. The LB
> entitlement narrowing (§3) is the one that most often changes a recommendation.
