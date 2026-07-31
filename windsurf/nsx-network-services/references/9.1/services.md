# NSX network services (NAT · LB · VPN · IPAM · VPC) — VCF 9.1

**Applies to:** NSX **9.1.0.0** (build 25318225), the NSX version in the VCF 9.1 Bill of Materials.
**Do not apply this file to VCF 9.0.** Use `../9.0/services.md` for 9.0 and `../deltas.md` for the
change list.

## Provenance of everything below

Two independent source classes are used, and every endpoint row is tagged with which one backs it:

| Tag | Meaning |
|---|---|
| **[SPEC]** | The exact `method + path` was found in `research/spec-inventory/9.1__nsx-policy.ops.json`, `9.1__nsx-manager.ops.json` or `9.1__nsx-global-policy.ops.json` — machine-extracted from the `9.1.0.0` tag of `github.com/vmware/vcf-api-specs` (`specifications/nsx/openapi-2.0/nsx_policy_api.yaml`, `spec_version: 9.1.0.0`, `basePath: /policy/api/v1`, 3,729 operations). Schema and field-level claims marked `[SPEC]` were read from that YAML directly. This is the strongest evidence available. |
| **[DOC]** | Verified only from version-pinned Broadcom prose (NSX 9.1.0 developer portal, NSX 9.1.0 API Guide, VCF 9.1 release notes / NSX admin guide). |
| **[INFERRED]** | Neither — stated as a shape or convention, not as a verified fact. Confirm before relying on it. |

**Version-asymmetry warning.** NSX 9.1 has a published machine-readable spec; NSX 9.0 does **not**
(there is no NSX spec at the `9.0.0.0` tag of the corpus). A `[SPEC]` tag in this file is evidence
about **9.1 only** and must never be copied into the 9.0 file as verification. This matters more
here than for the firewall: the 9.0 research could not verify Policy NAT or IPSec VPN paths at all.

> **Documentation, not live validation.** Captured 2026-07-31. **NAT and VPN operations are
> production-affecting.** A wrong `source_network` on a SNAT rule silently re-routes a subnet; a
> VPN session edit tears down an established tunnel. Prefer `enabled: false` over `DELETE` when
> backing out, and read the rule before you overwrite it.

---

## Contents

- [Provenance](#provenance-of-everything-below) — what `[SPEC]` / `[DOC]` / `[INFERRED]` mean
- [**Prerequisites**](#prerequisites) — **read before any write**
  - [P1 — Reachability, authentication and role](#p1--you-can-reach-nsx-manager-authenticate-and-hold-a-role-that-can-write)
  - [P2 — The gateway exists and can host services](#p2--nat-vpn-lb-the-gateway-exists-and-can-host-a-centralised-service)
  - [P3 — NAT: the NAT section id is not yours to invent](#p3--nat-the-nat-id-path-segment-is-a-system-created-section)
  - [P4 — NAT: route advertisement and firewall interaction](#p4--nat-the-translated-address-has-to-be-reachable)
  - [P5 — LB: service, pool, profile, and capacity](#p5--lb-a-virtual-server-needs-a-service-a-pool-an-application-profile-and-capacity)
  - [P6 — LB: **which** load balancer — NSX built-in vs Avi / NSX ALB](#p6--lb-which-load-balancer--nsx-built-in-or-avi--nsx-alb)
  - [P7 — VPN: service, local endpoint, profiles — and the deprecated path family](#p7--vpn-service-then-local-endpoint-then-session)
  - [P8 — IPAM: the block or pool must exist before the allocation](#p8--ipam-the-block-or-pool-exists-before-you-allocate-from-it)
  - [P9 — `_revision`, partial patch, and VCF ownership](#p9--concurrency-partial-patch-and-vcf-ownership)
- [Authentication in one paragraph](#authentication-in-one-paragraph) — deferred to `vcf-foundation`
- [Path families](#path-families-where-a-service-object-can-live)
- [NAT](#nat) — sections, rule CRUD, `PolicyNatRule` body, statistics
- [Load balancing](#load-balancing) — LB services, virtual servers, pools, profiles, status
  - [Avi / NSX Advanced Load Balancer](#avi--nsx-advanced-load-balancer-integration)
  - [Distributed load balancing (DLB)](#distributed-load-balancing-dlb--91-decoupling-and-a-spec-conflict)
- [IPSec and L2 VPN](#ipsec-and-l2-vpn) — services, local endpoints, sessions, profiles, deprecations
- [IPAM — IP pools, blocks, allocations](#ipam--ip-pools-ip-blocks-and-allocations)
- [VPC-scoped services](#vpc-scoped-services--91)
- [**Worked example** — Tier-1 scoped SNAT rule](#worked-example--a-tier-1-scoped-snat-rule) (Steps 0–7 + [failure decode](#failure-decode-for-this-sequence))
- [What is unverified for 9.1](#what-is-unverified-for-91)

---

## Prerequisites

Everything in this section must be true **before** you issue any network-service write. Each item
carries **four** elements — if one is missing, the item is incomplete:

1. **What must be true** — the condition itself.
2. **How to verify it** — a concrete, *non-destructive* call. Never verify a permission or a
   contract by performing the production change it guards.
3. **Which version it applies to** — every item below applies to **NSX 9.1.0.0** unless stated.
4. **Whether it exists in the other version** — stated as a "9.0 difference" line on every item.

### P1 — You can reach NSX Manager, authenticate, and hold a role that can write

- **Must be true:** HTTPS reachability to a specific manager node with a trusted chain; a valid
  session; and a role permitting writes. **Enterprise Admin** (`enterprise_admin`) covers all of
  it. NSX also ships narrower built-in roles that are directly relevant here — **Load Balancer
  Admin / Load Balancer Operator** and **VPN Admin** exist as distinct roles, so a caller may be
  able to write LB objects and not VPN objects, or vice versa. **[DOC]**
- **Verify — by reading, never by writing.** `GET /api/v1/aaa/role-bindings`
  **[SPEC — `GetAllRoleBindings`, `9.1__nsx-manager.ops.json`]** and read the role on your
  principal's binding. Confirm the session itself with a harmless read such as
  `GET /policy/api/v1/infra/tier-1s` **[SPEC — `ListTier1`]**.
  **Do not test NAT write permission by writing a NAT rule.** On success you have already changed
  the data path. If you want a live write probe, use a throwaway object id you then delete — never
  the target rule.
- **9.0 difference:** the role model is documented for 9.0 and includes the same LB/VPN roles, but
  no 9.0 role-introspection endpoint is spec-confirmable (no 9.0 spec exists). See
  `../9.0/services.md` P1.

### P2 — NAT, VPN, LB: the gateway exists and can host a centralised service

- **Must be true:** NAT, IPSec VPN and the edge-hosted load balancer are **centralised services**.
  They run on an edge node, which means the gateway they attach to must have an edge cluster bound
  to it. On a Tier-1 that binding lives in a **locale service** (`LocaleServices.edge_cluster_path`
  **[SPEC]**). A Tier-1 with no locale service has nowhere to run the service, and the write will
  be accepted and never realise.
- **Verify, in this order:**
  1. `GET /policy/api/v1/infra/tier-1s/{tier-1-id}` **[SPEC — `ReadTier1`]** (or
     `GET /policy/api/v1/infra/tier-0s/{tier-0-id}` **[SPEC — `ReadTier0`]**) returns 200.
     Capture the `path` from the body — use that literal string, do not hand-assemble it.
  2. `GET /policy/api/v1/infra/tier-1s/{tier-1-id}/locale-services`
     **[SPEC — `ListTier1LocaleServices`]** and confirm at least one result with a non-empty
     `edge_cluster_path`.
  3. If you want to confirm the referenced edge cluster itself:
     `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters/{edge-cluster-id}`
     **[SPEC — `ReadEdgeClusterForEnforcementPoint`]**.
- **Also on `Tier1` and relevant here [SPEC]:** `type` ∈ `ROUTED` / `ISOLATED` / `NATTED`;
  `ha_mode` ∈ `ACTIVE_STANDBY` / `ACTIVE_ACTIVE`; `pool_allocation` ∈ `ROUTING`, `LB_SMALL`,
  `LB_MEDIUM`, `LB_LARGE`, `LB_XLARGE` (default `ROUTING`). Note the NAT action descriptions in
  the spec: *"SNAT is only supported when the logical router is running in active-standby mode"*
  and the same for DNAT; `REFLEXIVE` *"is supported on both Active/Standby and Active/Active LR."*
  **[SPEC]** An active-active Tier-0 therefore cannot host plain SNAT.
- **9.0 difference:** `GET /infra/tier-0s/{tier-0-id}` and `GET /infra/tier-1s/{tier-1-id}` are
  prose-verified for 9.0; the locale-service list and the edge-cluster read verbs are not equally
  evidenced. See `../9.0/services.md`.

### P3 — NAT: the `{nat-id}` path segment is a system-created section

- **Must be true:** a NAT rule path is
  `/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules/{nat-rule-id}`, and `{nat-id}` is **not** an
  identifier you choose. Verbatim from the 9.1 spec: *"Under tier-0/tier-1 there will be 4
  different NATs(sections). (INTERNAL, USER, DEFAULT and NAT64)."* The `PolicyNat.nat_type` enum is
  `INTERNAL`, `USER`, `DEFAULT`, `NAT64` **[SPEC]**, and the spec's own example response shows each
  section with `"_system_owned": true` and `id` equal to the section name.
- **User-authored rules go in `USER`.** `INTERNAL` and `DEFAULT` are reserved; the spec documents
  distinct `sequence_number` ranges per section (`INTERNAL` 0–1023, `USER` 0–2147481599,
  `DEFAULT` 0–1023) **[SPEC]**.
- **Verify:** `GET /policy/api/v1/infra/tier-1s/{tier-1-id}/nat`
  **[SPEC — `ListPolicyNatOnTier1`]** (Tier-0: `ListPolicyNatOnTier0`) and read `nat_type` and
  `path` from the results. There is **no single-section read** (`GET .../nat/{nat-id}`) on
  `/infra` Tier-0 or Tier-1 in the 9.1 spec — only the list. The single-section read exists for
  **VPC** (`GetPolicyNatOnVpc`) and **Transit Gateway** (`GetTransitGatewayNat`) **[SPEC]**.
- **9.0 difference:** **the entire 9.0 Policy NAT path family is unverified.** Do not carry these
  paths across. See `../9.0/services.md`.

### P4 — NAT: the translated address has to be reachable

- **Must be true:** a correct NAT rule can still produce no working traffic for two reasons that
  are not visible in the rule itself.
  - **Route advertisement.** `Tier1.route_advertisement_types` **[SPEC]** is an enum array
    including `TIER1_NAT`, `TIER1_LB_VIP`, `TIER1_LB_SNAT`, `TIER1_IPSEC_LOCAL_ENDPOINT`,
    `TIER1_STATIC_ROUTES`, `TIER1_CONNECTED`, `TIER1_DNS_FORWARDER_IP`. If `TIER1_NAT` is absent,
    the translated address is not advertised to the Tier-0 and nothing north of the Tier-1 can
    reach it. The LB and VPN equivalents (`TIER1_LB_VIP`, `TIER1_IPSEC_LOCAL_ENDPOINT`) have the
    same failure mode.
  - **Firewall interaction.** `PolicyNatRule.firewall_match` **[SPEC]**, default
    `MATCH_INTERNAL_ADDRESS`, enum `MATCH_EXTERNAL_ADDRESS` / `MATCH_INTERNAL_ADDRESS` / `BYPASS`,
    decides whether the gateway firewall sees the pre-NAT or post-NAT address. Getting it wrong
    produces a rule that translates and then gets dropped by a firewall rule written against the
    other address. For `NO_SNAT` / `NO_DNAT` the spec says it *"must be BYPASS or leave it
    unassigned."*
- **Verify:** read the gateway (`ReadTier1` **[SPEC]**) and inspect `route_advertisement_types`
  before writing the rule. After writing, confirm realisation with
  `GET .../nat/{nat-id}/nat-rules/{nat-rule-id}/statistics`
  **[SPEC — `GetPolicyNatRuleStatisticsFromTier1`]** — non-zero counters prove the data path, a
  200 on the object read alone does not.
- **9.0 difference:** the `Tier1` and `PolicyNatRule` schemas were never captured from a 9.0-pinned
  source. Treat the field names as **inferred** for 9.0 and mirror an existing object instead.

### P5 — LB: a virtual server needs a service, a pool, an application profile and capacity

- **Must be true:** four objects, in dependency order.
  1. An **LB service** (`LBService`) with `connectivity_path` pointing at where it runs. Verbatim
     from the spec: *"LBS could be instantiated (or created) on the one of Tier-1, Group, VPC. For
     SLB, the Tier-1 object or the VPC object is supported. If the LB service is created under VPC,
     the connectivity path is set as VPC path internally. For DLB, only the Group object is
     supported."* **[SPEC]** `size` ∈ `SMALL`, `MEDIUM`, `LARGE`, `XLARGE`, `DLB` (default
     `SMALL`).
  2. An **application profile** — `LBAppProfile.resource_type` ∈ `LBHttpProfile`,
     `LBFastTcpProfile`, `LBFastUdpProfile` **[SPEC]**, `resource_type` required.
  3. An **LB pool** (`LBPool`) with `members` (each `LBPoolMember` requires `ip_address`
     **[SPEC]**) or a `member_group`.
  4. The **virtual server** itself. `LBVirtualServer` requires **`ports`, `ip_address` and
     `application_profile_path`** **[SPEC]** — all three, or the write is rejected.
- **Capacity is a separate gate.** A Tier-1 hosting an edge LB needs `pool_allocation` set to an
  `LB_*` value; the default is `ROUTING` **[SPEC]**. `LBService.relax_scale_validation` exists
  precisely because scale validation fails otherwise, and the spec notes the default differs:
  *"For LB under Infra, the default relax_scale_validation value is false. For LB under VPC, the
  default relax_scale_validation value is true."* **[SPEC]**
- **Verify, non-destructively:** `GET /policy/api/v1/infra/lb-services`
  **[SPEC — `ListLBServices`]**, `GET /policy/api/v1/infra/lb-app-profiles`
  **[SPEC — `ListLBAppProfiles`]**, `GET /policy/api/v1/infra/lb-pools`
  **[SPEC — `ListLBPools`]**, and for headroom
  `GET /policy/api/v1/infra/lb-node-usage-summary` **[SPEC — `GetLBNodeUsageSummary`]** or
  `GET /policy/api/v1/infra/lb-service-usage-summary` **[SPEC — `GetLBServiceUsageSummary`]**.
- **9.0 difference:** for 9.0 only `GET /policy/api/v1/infra/lb-services/{lb-service-id}` is
  prose-verified — no list, no virtual servers, no pools, no profiles. See `../9.0/services.md`.

### P6 — LB: **which** load balancer — NSX built-in, or Avi / NSX ALB?

- **Must be true:** decide this *before* writing anything, because the two are entirely separate
  API surfaces and configuring the wrong one is a silent no-op against the customer's actual data
  path.
  - **NSX built-in LB** → `/policy/api/v1/infra/lb-services…` and friends (P5).
  - **Avi / NSX Advanced Load Balancer** → NSX does not carry Avi virtual servers. NSX holds the
    *integration*: an **enforcement point** whose `connection_info.resource_type` is
    `AviConnectionInfo` **[SPEC — `EnforcementPointConnectionInfo.resource_type` enum is
    `NSXTConnectionInfo`, `NSXVConnectionInfo`, `CvxConnectionInfo`, `AviConnectionInfo`]**, plus
    an onboarding and controller-management surface. The virtual services themselves are
    configured on the Avi Controller, not through NSX.
- **Verify which one is in play:**
  `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points`
  **[SPEC — `ListEnforcementPointForSite`]** and
  `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}`
  **[SPEC — `ReadEnforcementPointForSite`]**; look at `connection_info.resource_type`. An
  `AviConnectionInfo` enforcement point means Avi is integrated. Corroborate with
  `GET /policy/api/v1/alb/controller-info/info` **[SPEC — `ListAlbControllerInfo`]** and
  `GET /policy/api/v1/alb/controller-nodes/cluster` **[SPEC — `ListALBControllerClusterInfo`]**.
- **Licensing gate — raise it, do not assume it.** VCF **9.0** narrowed the NSX LB entitlement:
  general-purpose LB removed from the VCF entitlement, Avi recommended, NSX LB retained only for
  VCF infrastructure and vSphere Supervisor use cases **[DOC — VCF 9.0 support notes]**. **The 9.1
  support notes do not restate this.** Its 9.1 status is therefore **unverified** — not revoked and
  not confirmed. The API will happily accept `/infra/lb-services` writes either way; entitlement is
  not enforced at the endpoint. Flag it to the user before they build on NSX LB.
- **9.0 difference:** VCF 9.0 already recommended Avi. The **self-service** Avi LB experience in
  the VCF Automation / tenant context is a **9.1** addition **[DOC — VCF 9.1 What's New: NSX,
  "Self Service NAT, VPN, Grouping, Firewalling"; "support for AVI load balancers with VPCs and
  Transit Gateways with distributed VLAN connection"]**.

### P7 — VPN: service, then local endpoint, then session

- **Must be true:** the dependency chain is strict.
  1. An **IPSec VPN service** on the gateway (`IPSecVpnService`; fields `enabled` default `true`,
     `ha_sync` default `true`, `ike_log_level` default `INFO`, `bypass_rules` **[SPEC]**).
  2. An **IPSec VPN local endpoint** under that service — `IPSecVpnLocalEndpoint` **requires
     `local_address`** **[SPEC]**; optional `local_id`, `certificate_path`, `trust_ca_paths`,
     `trust_crl_paths`.
  3. The **session**. `IPSecVpnSession` **requires `resource_type`**, enum
     `PolicyBasedIPSecVpnSession` / `RouteBasedIPSecVpnSession` **[SPEC]**.
     `PolicyBasedIPSecVpnSession` additionally **requires `rules`**; `RouteBasedIPSecVpnSession`
     carries `tunnel_interfaces` **[SPEC]**. Other session fields: `authentication_mode`
     (`PSK` default / `CERTIFICATE`), `connection_initiation_mode` (`INITIATOR` default /
     `RESPOND_ONLY` / `ON_DEMAND`), `compliance_suite` (`CNSA`, `SUITE_B_GCM_128`,
     `SUITE_B_GCM_256`, `PRIME`, `FOUNDATION`, `FIPS`, `NONE`), `peer_address`, `peer_id`, `psk`,
     `ike_profile_path`, `tunnel_profile_path`, `dpd_profile_path`, `local_endpoint_path`.
  4. Profiles, if you are not using the defaults: `/infra/ipsec-vpn-ike-profiles`,
     `/infra/ipsec-vpn-tunnel-profiles`, `/infra/ipsec-vpn-dpd-profiles` **[SPEC]**.
- **The 9.1 path replacement.** VPN services attach to the **gateway** in 9.1:
  `/infra/tier-0s/{tier-0-id}/ipsec-vpn-services/{service-id}` and
  `/infra/tier-1s/{tier-1-id}/ipsec-vpn-services/{service-id}` **[SPEC —
  `CreateOrPatchTier0VpnIPSecVpnService`, `CreateOrPatchTier1VpnIPSecVpnService`]**. The older
  **locale-service-scoped** family
  (`/infra/tier-0s/{id}/locale-services/{locale-service-id}/ipsec-vpn-services/…`) is still present
  and **every operation on it is flagged `deprecated: true` in the 9.1 spec** **[SPEC]** — that
  includes the L2VPN, `l2vpn-context` and `l3vpns` sub-trees. **Emit the gateway-scoped form.**
- **Verify:** `GET /policy/api/v1/infra/tier-1s/{tier-1-id}/ipsec-vpn-services`
  **[SPEC — `ListTier1VpnIPSecVpnServices`]**, then
  `GET …/ipsec-vpn-services/{service-id}/local-endpoints`
  **[SPEC — `ListTier1VpnIPSecVpnLocalEndpoints`]**. Before changing a live tunnel, read its state
  with `GET …/sessions/{session-id}/detailed-status`
  **[SPEC — `GetTier1VpnIPSecVpnSessionStatus`]** so you know what "working" looked like.
  Do **not** use `?action=show_sensitive_data` (`GetTier1VpnIPSecVpnSessionWithSensitiveData`
  **[SPEC]**) unless you actually need the PSK — it returns the shared secret.
- **9.0 difference:** **9.0 IPSec VPN service paths are unverified** — the research could not
  retrieve them. The locale-service deprecation is a 9.1 spec observation and says nothing about
  which form 9.0 accepts. See `../9.0/services.md`.

### P8 — IPAM: the block or pool exists before you allocate from it

- **Must be true:** allocations are children. An `IpAddressAllocation` lives under an IP pool
  (`/infra/ip-pools/{ip-pool-id}/ip-allocations/{ip-allocation-id}`), and pool subnets can be
  carved from an IP block. `IpAddressPoolStaticSubnet` **requires `allocation_ranges` and `cidr`**
  **[SPEC]**. On `IpAddressBlock`, the singular `cidr` field is **`x-deprecated: true`** in the 9.1
  spec — the current fields are the arrays `cidrs` and `ranges`, plus `excluded_ips` **[SPEC]**.
- **Verify:** `GET /policy/api/v1/infra/ip-blocks` **[SPEC — `ListIpAddressBlocks`]** and
  `GET /policy/api/v1/infra/ip-blocks/{ip-block-id}/usage`
  **[SPEC — `GetIpAddressBlockUsage`]** or `…/available-subnets`
  **[SPEC — `GetFreeSubnetCountForIpAddressBlock`]** before carving; for pools,
  `GET /policy/api/v1/infra/ip-pools/{ip-pool-id}` **[SPEC — `ReadIpAddressPool`]** and read
  `pool_usage`. Exhaustion is the normal failure here, and it is visible without writing anything.
- **`visibility` is one-way.** `IpAddressBlock.visibility` ∈ `PRIVATE` / `EXTERNAL`, and the spec
  says verbatim: *"Visibility cannot be updated once block is associated with other intents."*
  **[SPEC]** `IpAddressPool.visibility` uses a different enum — `PRIVATE` / `PUBLIC` **[SPEC]**.
  Do not assume they are the same field.
- **9.0 difference:** IP **pools**, `ip-allocations` and `ip-subnets` are prose-verified for 9.0
  (GET·PUT·PATCH·DELETE). IP **blocks** are **not** verified for 9.0. The 10-CIDR limit is a 9.1
  release-notes item — see `../deltas.md`.

### P9 — Concurrency, partial patch, and VCF ownership

- **`_revision`:** every REST payload carries an integer `_revision`; it must be echoed on `PUT`
  for an existing object and **omitted** on a `PUT` that creates one. `PATCH` does not require it.
  **[DOC — NSX 9.1 API Guide, verbatim]** Using `PATCH` for create-or-update sidesteps the whole
  question, and every worked example below uses `PATCH` for that reason.
- **Partial patch is off by default:** enable with
  `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` `{"enable_partial_patch": "true"}`
  **[DOC]**; read it first with
  `GET /policy/api/v1/system-config/nsx-partial-patch-config`
  **[SPEC — `GetPartialPatchConfiguration`]**.
- **VCF ownership:** there is **no authoritative published list** of which NSX objects VCF owns.
  For this skill's objects the practical split is that NAT rules, LB virtual servers/pools, VPN
  sessions and user IP pools are operator-authored, while the gateways, edge clusters and the VNA
  clusters underneath them are VCF-lifecycle-owned — **this split is [INFERRED], not doc-stated.**
  Verify per object by reading `_system_owned`, `_protection` and `_create_user` on the object
  (`PolicyConfigResource` fields **[SPEC]**). Note that **every NAT section is `_system_owned:
  true`** in the spec's own example — that is expected and does not mean the rules inside it are
  off-limits.
- **9.0 difference:** the `_revision`-on-create rule is verbatim only in the 9.1 guide; 9.0's guide
  says only that `/policy` URIs *"have slightly different behavior."* The `GET` verb on the
  partial-patch config is spec-confirmed for 9.1 only.

---

## Authentication in one paragraph

`POST /api/session/create` (form-encoded `j_username` / `j_password`) returns a `JSESSIONID`
cookie **and** an `X-XSRF-TOKEN` header; send **both** on every subsequent call. Destroy with
`POST /api/session/destroy`. **Both operations** are spec-confirmed in `9.1__nsx-manager.ops.json`
(`CreateAuthenticatedSession`, `DestroyAuthenticatedSession`) and declared as absolute paths
**outside** the `/api/v1` basePath. **[SPEC]**

Two traps that read like permission problems, with their evidence stated separately — neither is a
spec fact:

- **Session expiry surfaces as 403, not 401.** *"NSX Manager responds with a 403 Forbidden HTTP
  response."* **[DOC — VCF 9.1 admin guide]**
- **Cookies are bound to a single manager node** and cannot be reused across cluster members — pin
  the client, or it fails intermittently behind a VIP. **[DOC — VCF 9.0 admin guide; not restated
  on a 9.1-pinned page, assumed unchanged]**

**Anything more than that belongs to `vcf-foundation`** — token-based principal identities, OIDC,
role mapping, rate limits and the full 401/403 decode. Do not re-derive it here.

---

## Path families: where a service object can live

The same object type exists in several families and they are **not** interchangeable — reading a
project-scoped NAT rule through `/infra/` returns 404.

| Family | Template | Notes |
|---|---|---|
| Local | `/policy/api/v1/infra/…` | Default single-tenant scope. Full CRUD. |
| Global (Federation) | `/policy/api/v1/global-infra/…` | On the **local** manager these are **GET-only** for NAT and VPN — the spec exposes `GlobalInfraListPolicyNatOnTier1`, `GlobalInfraGetPolicyNatRule` and friends as reads. Writes live on the Global Manager appliance (`basePath: /global-manager/api/v1`, `9.1__nsx-global-policy.ops.json`, which *does* carry `GlobalInfraDeletePolicyNatRuleFromTier0` etc.). **[SPEC]** |
| Project (multi-tenancy) | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/…` | Full CRUD for Tier-1 NAT and Tier-1 VPN. **[SPEC]** |
| Transit Gateway | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/transit-gateways/{tgw-id}/…` | NAT and IPSec VPN attach here. **[SPEC]** |
| VPC | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/…` | NAT, LB (`vpc-lbs`, `vpc-lb-*`), subnet IP pools. **[SPEC]** |

A notable asymmetry: **Tier-1 NAT has project-scoped variants; Tier-0 NAT does not.** The 9.1 spec
carries `OrgsOrgIdProjectsProjectIdInfra*PolicyNatRule*` for Tier-1 only, and exposes Tier-0 NAT on
`global-infra` as reads. **[SPEC]**

---

## NAT

### Sections

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/tier-0s/{tier-0-id}/nat` | `ListPolicyNatOnTier0` |
| GET | `/infra/tier-1s/{tier-1-id}/nat` | `ListPolicyNatOnTier1` |
| GET | `/orgs/{org-id}/projects/{project-id}/infra/tier-1s/{tier-1-id}/nat` | `OrgsOrgIdProjectsProjectIdInfraListPolicyNatOnTier1` |
| GET | `/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/nat` · `/nat/{nat-id}` | `ListPolicyNatOnVpc` · `GetPolicyNatOnVpc` |
| GET | `/orgs/{org-id}/projects/{project-id}/transit-gateways/{tgw-id}/nat` · `/nat/{nat-id}` | `ListTransitGatewayNat` · `GetTransitGatewayNat` |

All **[SPEC]**. Sections are `INTERNAL`, `USER`, `DEFAULT`, `NAT64` and are `_system_owned`.

### Rules

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules` | `ListPolicyNatRules` |
| GET | `/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules/{nat-rule-id}` | `GetPolicyNatRule` |
| PATCH | same | `PatchPolicyNatRule` |
| PUT | same | `CreateOrReplacePolicyNatRule` |
| DELETE | same | `DeletePolicyNatRule` |
| GET | `/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules/{nat-rule-id}/statistics` | `GetPolicyNatRuleStatisticsFromTier1` |
| GET | `/infra/tier-1s/{tier-1-id}/nat/statistics` | `ListPolicyNatRulesStatisticsFromTier1` |
| GET | `/infra/tier-0s/{tier-0-id}/nat/{nat-id}/nat-rules` | `ListPolicyNatRulesFromTier0` |
| GET·PATCH·PUT·DELETE | `/infra/tier-0s/{tier-0-id}/nat/{nat-id}/nat-rules/{nat-rule-id}` | `GetPolicyNatRuleFromTier0`, `PatchPolicyNatRuleOnTier0`, `CreateOrReplacePolicyNatRuleOnTier0`, `DeletePolicyNatRuleFromTier0` |
| GET | `/infra/tier-0s/{tier-0-id}/nat/{nat-id}/nat-rules/{nat-rule-id}/statistics` | `GetPolicyNatRuleStatisticsFromTier0` |
| GET·PATCH·PUT·DELETE | `/orgs/{org}/projects/{proj}/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules/{nat-rule-id}` | `OrgsOrgIdProjectsProjectIdInfra{Get,Patch,CreateOrReplace,Delete}PolicyNatRule` |
| GET·PATCH·PUT·DELETE | `/orgs/{org}/projects/{proj}/vpcs/{vpc-id}/nat/{nat-id}/nat-rules/{nat-rule-id}` | `GetPolicyVpcNatRuleOnVpc`, `PatchPolicyVpcNatRuleOnVpc`, `CreateOrReplacePolicyNatRuleOnVpc`, `DeletePolicyNatRuleOnVpc` |
| GET·PATCH·PUT·DELETE | `/orgs/{org}/projects/{proj}/transit-gateways/{tgw-id}/nat/{nat-id}/nat-rules/{nat-rule-id}` | `GetTransitGatewayNatRule`, `PatchTransitGatewayNatRule`, `CreateOrReplaceTransitGatewayNatRule`, `DeleteTransitGatewayNatRule` |
| GET | `/infra/sites/{site-id}/enforcement-points/{ep-id}/edge-clusters/{ec-id}/edge-nodes/{node-id}/nat/statistics` | `GetNatStatisticsPerPolicyEdgeNode` |

All **[SPEC]**. `global-infra` equivalents exist as **GET only** on the local manager
(`GlobalInfraGetPolicyNatRule`, `GlobalInfraListPolicyNatRulesFromTier0`, …) **[SPEC]**.

### `PolicyNatRule` body **[SPEC]**

`PolicyNatRule` extends `PolicyConfigResource`. **`action` is the only required field.**

| Field | Type / enum | Default | Notes |
|---|---|---|---|
| `action` | `SNAT`, `DNAT`, `REFLEXIVE`, `NO_SNAT`, `NO_DNAT`, `NAT64` | — | **required**. SNAT/DNAT *"only supported when the logical router is running in active-standby mode"*; REFLEXIVE works on both. `NO_SNAT`/`NO_DNAT` accept only `source_network` / `destination_network`. |
| `source_network` | address / CIDR / comma-separated list | — | Mandatory for SNAT, NO_SNAT, NAT64, REFLEXIVE. Optional for DNAT/NO_DNAT. NULL = ANY. **No IP ranges, no IP sets.** |
| `destination_network` | same format | — | Mandatory for DNAT/NO_DNAT. Optional otherwise. |
| `translated_network` | same format | — | Mandatory for SNAT, DNAT, NAT64, REFLEXIVE; **must be empty** for NO_SNAT/NO_DNAT. A CIDR here *"is actually used as an IP pool that includes both the subnet and broadcast addresses as valid for NAT translations."* Comma-separated lists are **not** supported for DNAT or REFLEXIVE. |
| `translated_ports` | port-or-range | — | Only meaningful with `service` set. |
| `service` | policy path to a `Service` | — | Blank = ANY. For DNAT the service's `destination_port` is realised as the translated port; **for SNAT the destination port is ignored.** |
| `scope` | array of policy paths | — | Paths of `ProviderInterface` / `NetworkInterface` / labels / `IPSecVpnSession`. *"The interfaces must belong to the same router for which the NAT Rule is created."* |
| `sequence_number` | int32 | `0` | Maps 1:1 to rule priority. Per-section ranges — see P3. |
| `enabled` | boolean | `true` | **The rollback lever.** Prefer over `DELETE`. |
| `logging` | boolean | `false` | |
| `firewall_match` | `MATCH_EXTERNAL_ADDRESS`, `MATCH_INTERNAL_ADDRESS`, `BYPASS` | `MATCH_INTERNAL_ADDRESS` | See P4. |
| `policy_based_vpn_mode` | `BYPASS`, `MATCH` | — | DNAT/NO_DNAT only; leave unset otherwise. `MATCH` restricts the rule to policy-based VPN traffic. |

**VPC note [SPEC]:** *"For VPC SNAT and Refelexive NATRule, translated network address should be
IPv4 address allocated from External Block associated with VPC"* (sic), and for VPC DNAT the
destination address must likewise come from the VPC's external block.

---

## Load balancing

### Core objects

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/lb-services` | `ListLBServices` |
| GET·PATCH·PUT·DELETE | `/infra/lb-services/{lb-service-id}` | `ReadLBService`, `PatchLBService`, `UpdateLBService`, `DeleteLBService` |
| GET | `/infra/lb-services/{lb-service-id}/detailed-status` · `/statistics` · `/service-usage` · `/debug-info` | `GetLBServiceStatus`, `GetLBServiceStatistics`, `GetLBServiceUsage`, `ReadLBServiceDebugInfo` |
| GET | `/infra/lb-virtual-servers` | `ListLBVirtualServers` |
| GET·PATCH·PUT·DELETE | `/infra/lb-virtual-servers/{lb-virtual-server-id}` | `ReadLBVirtualServer`, `PatchLBVirtualServer`, `UpdateLBVirtualServer`, `DeleteLBVirtualServer` |
| GET | `/infra/lb-pools` · `/infra/lb-pools/{lb-pool-id}` | `ListLBPools`, `ReadLBPool` |
| PATCH·PUT·DELETE | `/infra/lb-pools/{lb-pool-id}` | `PatchLBPool`, `UpdateLBPool`, `DeleteLBPool` |
| GET·PATCH·PUT·DELETE | `/infra/lb-app-profiles[/{lb-app-profile-id}]` | `ListLBAppProfiles`, `ReadLBAppProfile`, `PatchLBAppProfile`, `UpdateLBAppProfile`, `DeleteLBAppProfile` |
| GET·PATCH·PUT·DELETE | `/infra/lb-monitor-profiles[/{lb-monitor-profile-id}]` | `ListLBMonitorProfiles`, `ReadLBMonitorProfile`, … |
| GET·PATCH·PUT·DELETE | `/infra/lb-persistence-profiles[/{id}]` | `ListLBPersistenceProfiles`, … |
| GET·PATCH·PUT·DELETE | `/infra/lb-client-ssl-profiles[/{id}]` · `/infra/lb-server-ssl-profiles[/{id}]` | `ListLBClientSslProfiles`, `ListLBServerSslProfiles`, … |
| GET | `/infra/lb-ssl-ciphers-and-protocols` | `ListSslCiphersAndProtocols` |
| GET | `/infra/lb-services/{id}/lb-virtual-servers/{vs-id}/detailed-status` · `/statistics` | `GetLBVirtualServerStatus`, `GetLBVirtualServerStatistics` |
| GET | `/infra/lb-services/{id}/lb-pools/{pool-id}/detailed-status` · `/statistics` | `GetLBPoolStatus`, `GetLBPoolStatistics` |
| GET | `/infra/lb-node-usage` · `/infra/lb-node-usage-summary` · `/infra/lb-service-usage-summary` | `GetLBNodeUsage`, `GetLBNodeUsageSummary`, `GetLBServiceUsageSummary` |

All **[SPEC]**.

### Bodies **[SPEC]**

- **`LBService`** — `connectivity_path` (Tier-1, Group, or VPC — see P5), `size`
  (`SMALL`/`MEDIUM`/`LARGE`/`XLARGE`/`DLB`, default `SMALL`), `enabled` (default `true`),
  `error_log_level` (`DEBUG`…`EMERGENCY`, default `INFO`), `relax_scale_validation`.
  `access_log_enabled` on `LBService` is **`x-deprecated: true`** — the live one is on
  `LBVirtualServer`.
- **`LBVirtualServer`** — **required: `ports`, `ip_address`, `application_profile_path`.** Also
  `pool_path`, `sorry_pool_path`, `lb_service_path`, `lb_persistence_profile_path`,
  `client_ssl_profile_binding`, `server_ssl_profile_binding`, `access_list_control`, `rules`
  (`LBRule`), `default_pool_member_ports`, `max_concurrent_connections`, `max_new_connection_rate`,
  `enabled` (default `true`), `access_log_enabled` (default `false`),
  `log_significant_event_only` (default `false`).
- **`LBPool`** — `algorithm` ∈ `ROUND_ROBIN` (default), `WEIGHTED_ROUND_ROBIN`, `LEAST_CONNECTION`,
  `WEIGHTED_LEAST_CONNECTION`, `IP_HASH`; `members` (array of `LBPoolMember`) or `member_group`;
  `active_monitor_paths`, `passive_monitor_path`, `snat_translation`, `min_active_members`
  (default `1`), `tcp_multiplexing_enabled` (default `false`), `tcp_multiplexing_number`
  (default `6`).
- **`LBPoolMember`** — **required: `ip_address`.** Plus `port`, `weight` (1–256, default 1, only
  honoured by `WEIGHTED_ROUND_ROBIN`), `admin_state` (`ENABLED` default / `DISABLED` /
  `GRACEFUL_DISABLED`), `backup_member`, `max_concurrent_connections`.
- **`LBAppProfile.resource_type`** ∈ `LBHttpProfile`, `LBFastTcpProfile`, `LBFastUdpProfile`
  (required). **`LBMonitorProfile.resource_type`** ∈ `LBTcpMonitorProfile`, `LBUdpMonitorProfile`,
  `LBIcmpMonitorProfile`, `LBHttpMonitorProfile`, `LBHttpsMonitorProfile`,
  `LBPassiveMonitorProfile` (required).

### Avi / NSX Advanced Load Balancer integration

NSX integrates with the Avi Controller; it does not proxy Avi virtual services. What the 9.1 NSX
Policy API exposes **[SPEC]**:

| Verb | Path (append to `/policy/api/v1`) | operationId | Purpose |
|---|---|---|---|
| PUT | `/infra/alb-onboarding-workflow` | `InitiateAlbOnBoardingWorkflow` | Start the ALB onboarding. |
| DELETE | `/infra/alb-onboarding-workflow/{managed-by}` | `DeleteAlbOnBoardingWorkflow` | Tear it down. |
| PUT | `/infra/alb-auth-token` | `GetALBAuthToken` | Mint an Avi Controller auth token (`ALBAuthToken` requires `username` and `hours`). |
| GET·PUT·DELETE | `/alb/controller-info/info[/{controller-id}]` | `ListAlbControllerInfo`, `ReadAlbControllerInfo`, `CreateOrUpdateAlbControllerInfo`, `DeleteAlbControllerInfo` | Controller registration for **license usage collection**. `AlbControllerInfo` requires `node_ip`, `username`, `controller_id`. |
| GET·POST | `/alb/controller-nodes/deployments[/{node-id}]` · `/status` | `ListALBControllerNodeVMDeploymentRequests`, `AddALBControllerNodeVM`, `ReadALBControllerNodeVMDeploymentRequest`, `ReadALBControllerNodeVMDeploymentStatus` | Deploy / track Controller VMs. |
| GET·POST·DELETE | `/alb/controller-nodes/clusterconfig` · `/cluster` | `ReadALBControllerNodeClusterConfig`, `AddALBControllerNodeClusterConfig`, `DeleteALBControllerNodeClusterConfig`, `ListALBControllerClusterInfo`, `RetriggerClustering` | Controller clustering. |
| POST | `/alb/controller-nodes/cloud` · `/vcenterserver` · `/pki-profile` | `CreateALBControllerCloud`, `CreateALBControllerVcenterServer`, `SetupALBControllerPKIProfile` | Cloud, vCenter and PKI wiring. |
| POST·PUT·DELETE | `/alb/controller-nodes/user[/{username}]` · `/user-credential[/{username}]` | `CreateALBControllerUser`, `UpdateALBControllerUser`, `DeleteALBControllerUser`, `CreateAlbUserCredentialObject`, `UpdateAlbUserCredentialObject`, `DeleteAlbUserCredentialObject` | Controller users and stored credentials. |
| POST | `/alb/controller-nodes/certificate/csr` · `/certificate/install` | `CreateAlbPortalCertificateCSR`, `InstallAlbPortalCertificate` | Portal certificate. |
| GET | `/alb/controller-nodes/form-factors` | `ListALBControllerFormFactors` | Sizing options. |

The **binding** to NSX is the enforcement point: `EnforcementPoint.connection_info` of
`resource_type: AviConnectionInfo`, whose fields include `enforcement_point_address` (required on
the base type), `password` (*"Password or Token for Avi Controller"*), `certificate`,
`is_default_cert`, `managed_by`, `expires_at`, and `status` ∈ `ACTIVATE`, `DEACTIVATE_PROVIDER`,
`DEACTIVATE_API` (default `DEACTIVATE_API`) **[SPEC]**. `AviConnectionInfo.cloud` is
`x-deprecated: true` — *"Cloud has been renamed to cloud_name and it will added from specific ALB
entity."*

Note the `managed_by` / `certificate` field descriptions: *"used when on-boarding workflow created
by LCM/VCF"* **[SPEC]** — in a VCF deployment this integration is normally established by VCF
lifecycle, not by hand. Read it before you write it.

**9.1 addition [DOC]:** *"support for AVI load balancers with VPCs and Transit Gateways with
distributed VLAN connection"*, and self-service tenant networking including LB in the VCF
Automation context. See `../deltas.md`.

### Distributed load balancing (DLB) — 9.1 decoupling, and a spec conflict

- **[DOC — VCF 9.1 What's New: NSX, verbatim]:** *"Distributed Load Balancer is now independently
  managed and decoupled from the Distributed Firewall (DFW)."*
- **In the API**, a distributed LB is an `LBService` with `size: DLB`, and *"For DLB, only the
  Group object is supported"* as `connectivity_path` **[SPEC]** — i.e. it attaches to a security
  group rather than to a gateway.
- **Unresolved conflict — do not paper over it.** The 9.1 spec still says of
  `PATCH /policy/api/v1/infra/settings/firewall/security`: *"Turning off distributed services
  ("enable_firewall": false) will turn off Distributed Firewall, Identity Firewall, Distributed
  Intrusion Detection and Prevention Service, Distributed Load Balancer."* **[SPEC]** And the
  example response for `GET /infra/settings/firewall/security/dependent-services`
  **[SPEC — `GetDistributedFirewallDependentServices`]** lists `"Distributed Load Balancer"` among
  the dependent services. So the release note says decoupled; the spec still couples the master
  on/off switch. **Recorded, not resolved.** If a user is about to set `enable_firewall: false` on
  a 9.1 system running DLB, call `dependent-services` on *their* appliance first and act on what
  it returns.

---

## IPSec and L2 VPN

### Gateway-scoped (current) — **[SPEC]**

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/tier-1s/{tier-1-id}/ipsec-vpn-services` | `ListTier1VpnIPSecVpnServices` |
| GET·PATCH·PUT·DELETE | `/infra/tier-1s/{tier-1-id}/ipsec-vpn-services/{service-id}` | `GetTier1VpnIPSecVpnService`, `CreateOrPatchTier1VpnIPSecVpnService`, `CreateOrUpdateTier1VpnIPSecVpnService`, `DeleteTier1VpnIPSecVpnService` |
| GET·PATCH·PUT·DELETE | `…/{service-id}/local-endpoints[/{local-endpoint-id}]` | `ListTier1VpnIPSecVpnLocalEndpoints`, `GetTier1VpnIPSecVpnLocalEndpoint`, `CreateOrPatchTier1VpnIPSecVpnLocalEndpoint`, … |
| GET·PATCH·PUT·DELETE | `…/{service-id}/sessions[/{session-id}]` | `ListTier1VpnIPSecVpnSessions`, `GetTier1VpnIPSecVpnSession`, `CreateOrPatchTier1VpnIPSecVpnSession`, … |
| GET | `…/sessions/{session-id}/detailed-status` · `/statistics` · `/peer-config` | `GetTier1VpnIPSecVpnSessionStatus`, `GetTier1VpnIPSecVpnSessionStatistics`, `GetTier1VpnIPSecVpnPeerConfig` |
| POST | `…/sessions/{session-id}/statistics` | `ResetTier1VpnIPSecVpnSessionStatistics` |
| GET | `…/{service-id}/summary` | `GetTier1VpnIpsecVpnSessionSummary` |
| GET | `…/sessions/{session-id}?action=show_sensitive_data` | `GetTier1VpnIPSecVpnSessionWithSensitiveData` — **returns the PSK** |

The Tier-0 family mirrors this exactly (`ListTier0VpnIPSecVpnServices`,
`CreateOrPatchTier0VpnIPSecVpnService`, `GetTier0VpnIPSecVpnSessionStatus`, …), and Tier-0 also
carries the current **L2VPN** family: `/infra/tier-0s/{tier-0-id}/l2vpn-services[/{service-id}]`
with `sessions`, `peer-config`, `remote-mac`, `statistics`, and
`POST …/sessions/{session-id}?action=create_with_peer_code`
(`CreateOrPatchTier0VpnL2VPNSessionFromPeerCodes`). **[SPEC]**

Project-scoped Tier-1 equivalents exist with the `OrgsOrgIdProjectsProjectIdInfra…` prefix, and
Transit-Gateway-scoped equivalents exist as
`/orgs/{org}/projects/{proj}/transit-gateways/{transit-gateway-id}/ipsec-vpn-services/…`
(`ListTransitGatewayIPSecVpnServices`, `CreateOrPatchTransitGatewayIPSecVpnService`,
`CreateOrPatchTransitGatewayIPSecVpnSession`, `GetTransitGatewayIPSecVpnSessionStatus`, …).
**[SPEC]**

### Profiles — **[SPEC]**

| Verb | Path | operationId |
|---|---|---|
| GET·PATCH·PUT·DELETE | `/infra/ipsec-vpn-ike-profiles[/{ike-profile-id}]` | `ListIPSecVpnIkeProfiles`, `GetIPSecVpnIkeProfile`, `CreateOrPatchIPSecVpnIkeProfile`, `CreateOrUpdateIPSecVpnIkeProfile`, `DeleteIPSecVpnIkeProfile` |
| GET·PATCH·PUT·DELETE | `/infra/ipsec-vpn-tunnel-profiles[/{tunnel-profile-id}]` | `ListIPSecVpnTunnelProfiles`, … |
| GET·PATCH·PUT·DELETE | `/infra/ipsec-vpn-dpd-profiles[/{dpd-profile-id}]` | `ListIPSecVpnDpdProfiles`, … |

### Deprecated: the locale-service-scoped family

`/infra/tier-{0,1}s/{id}/locale-services/{locale-service-id}/ipsec-vpn-services/…` and the
`l2vpn-services`, `l2vpn-context`/`l2vpns` and `l3vpns` sub-trees under `locale-services` are
present in the 9.1 spec and **every operation on them carries `deprecated: true`** **[SPEC]** —
`ListTier0IPSecVpnServices`, `CreateOrUpdateTier0IPSecVpnService`, `GetTier0IPSecVpnSession`,
`ReadL2VpnContext`, `ListL3Vpns` and the rest. The 9.1 release notes list this deprecation
explicitly **[DOC]**. **Emit the gateway-scoped form.** Note that the deprecation reaches into
other objects too: the NAT documentation warns that *"old IPSecVpnSession policy path deprecated.
If user specifiy old IPSecVpnSession path in the scope property in the PATCH/PUT API, the path
returned in the GET response payload will be a new path"* — same resource, new path, no functional
impact **[SPEC]**.

---

## IPAM — IP pools, IP blocks and allocations

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/ip-pools` | `ListIpAddressPools` |
| GET·PATCH·PUT·DELETE | `/infra/ip-pools/{ip-pool-id}` | `ReadIpAddressPool`, `CreateOrPatchIpAddressPool`, `CreateOrReplaceIpAddressPool`, `DeleteIpAddressPool` |
| GET | `/infra/ip-pools/{ip-pool-id}/ip-allocations` | `ListIpAddressPoolAllocations` |
| GET·PATCH·PUT·DELETE | `/infra/ip-pools/{ip-pool-id}/ip-allocations/{ip-allocation-id}` | `ReadIpAddressPoolAllocation`, `CreateOrPatchIpAddressPoolAllocation`, `CreateOrReplaceIpAddressPoolAllocation`, `DeleteIpAddressPoolAllocation` |
| GET | `/infra/ip-pools/{ip-pool-id}/ip-subnets` | `ListIpAddressPoolSubnets` |
| GET·PATCH·PUT·DELETE | `/infra/ip-pools/{ip-pool-id}/ip-subnets/{ip-subnet-id}` | `ReadIpAddressPoolSubnet`, `CreateOrPatchIpAddressPoolSubnet`, `CreateOrReplaceIpAddressPoolSubnet`, `DeleteIpAddressPoolSubnet` |
| GET | `/infra/ip-blocks` | `ListIpAddressBlocks` |
| GET·PATCH·PUT·DELETE | `/infra/ip-blocks/{ip-block-id}` | `ReadIpAddressBlock`, `CreateOrPatchIpAddressBlock`, `CreateOrReplaceIpAddressBlock`, `DeleteIpAddressBlock` |
| GET | `/infra/ip-blocks/{ip-block-id}/usage` · `/allocation-state` · `/available-subnets` | `GetIpAddressBlockUsage`, `GetIpAddressBlockAllocationState`, `GetFreeSubnetCountForIpAddressBlock` |
| GET | `/infra/ip-blocks/usage` · `/allocation-state` · `/state` | `GetAllIpAddressBlocksUsage`, `GetAllIpAddressBlocksAllocationState`, `GetIpAddressBlockState` |
| GET | `/infra/manager-ip-pools[/{manager-ip-pool-id}]` | `ListManagerIpPools`, `ReadManagerIpPool` |
| all of the above | `/orgs/{org-id}/projects/{project-id}/infra/ip-pools…` and `…/infra/ip-blocks…` | `OrgsOrgIdProjectsProjectIdInfra…` prefix |
| GET | `/orgs/{org}/projects/{proj}/vpcs/{vpc-id}/ip-blocks/usage` · `/allocation-state` | `GetIpAddressBlockUsageForVPC`, `GetIpAddressBlockAllocationStateForVPC` |

All **[SPEC]**.

### Bodies **[SPEC]**

- **`IpAddressBlock`** — `cidrs` (array), `ranges` (array of `IpPoolRange`), `excluded_ips` (array
  of `IpPoolRange`), `visibility` ∈ `PRIVATE`/`EXTERNAL` (immutable once associated),
  `subnet_exclusive` (*"reserved for direct vlan extension use case… cannot be modified from true
  to false"*), `ip_address_type` (read-only), `total_size` / `used_size` / `usage_percentage`,
  `third_party_ipam`, `sync_realization`. The singular **`cidr` is `x-deprecated: true`**, as is
  `available_allocation_size` (*"Please use below GET API instead … /ip-blocks/Finance-block/
  usage"*).
  **The spec declares no `maxItems` on `cidrs` or `ranges`** — the "up to 10" figure is a release
  note, not a spec constraint. See `../deltas.md`.
- **`IpAddressPool`** — `ip_address_type` ∈ `IPV4`/`IPV6`/`DUAL`, `visibility` ∈
  `PRIVATE`/`PUBLIC` (**different enum from the block**), `ip_release_delay`, `pool_usage`
  (read), `check_overlap_with_existing_pools` (default `false`), `sync_realization`.
- **`IpAddressPoolStaticSubnet`** — **requires `allocation_ranges` and `cidr`**; also
  `gateway_ip`, `dns_nameservers`, `dns_suffix`.
- **`IpAddressAllocation`** — `allocation_ip` (what you ask for), `allocated_ip` (what you got),
  `sync_realization`.

---

## VPC-scoped services — 9.1

The 9.1 spec carries a full VPC service surface. **[SPEC]**

| Service | Paths (append to `/policy/api/v1/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}`) | operationIds |
|---|---|---|
| **NAT** | `/nat` · `/nat/{nat-id}` · `/nat/{nat-id}/nat-rules[/{nat-rule-id}]` · `…/statistics` | `ListPolicyNatOnVpc`, `GetPolicyNatOnVpc`, `ListPolicyNatRulesOnVpc`, `GetPolicyVpcNatRuleOnVpc`, `PatchPolicyVpcNatRuleOnVpc`, `CreateOrReplacePolicyNatRuleOnVpc`, `DeletePolicyNatRuleOnVpc`, `GetPolicyVpcNatRuleStatistics`, `ListPolicyVpcNatRulesStatistics` |
| **LB service** | `/vpc-lbs[/{vpc-lb-id}]` · `/detailed-status` · `/statistics` · `/usage` | `ListVpcLBServices`, `ReadVpcLBService`, `PatchVpcLBService`, `UpdateVpcLBService`, `DeleteVpcLBService`, `GetVpcLBServiceStatus`, `GetVpcLBServiceStatistics`, `GetVpcLBServiceUsage` — body schema is `LBService` |
| **LB virtual servers / pools** | `/vpc-lb-virtual-servers[/{id}]` · `/vpc-lb-pools[/{id}]` · `/vpc-lbs/{vpc-lb-id}/vpc-lb-pools/{id}/detailed-status`·`/statistics` | `ListVpcLBVirtualServers`, `PatchVpcLBVirtualServer`, `ListVpcLBPools`, `PatchVpcLBPool`, `GetVpcLBPoolStatus`, `GetVpcLBPoolStatistics` |
| **LB profiles** | `/vpc-lb-app-profiles[/{id}]` · `/vpc-lb-monitor-profiles[/{id}]` · `/vpc-lb-persistence-profiles[/{id}]` · `/vpc-lb-client-ssl-profiles[/{id}]` · `/vpc-lb-server-ssl-profiles[/{id}]` | `ListVpcLBAppProfiles`, `ListVpcLBMonitorProfiles`, … |
| **LB capacity** | `/vpc-lb-node-capacity-status`; project-level `/orgs/{org}/projects/{proj}/lb-node-capacity-status` | `GetVpcLBNodeCapacityStatus`, `GetProjectLBNodeCapacityStatus` |
| **IP allocation** | `/ip-address-allocations[/{ip-address-allocation-id}]` · `/ip-address-usage` · `/ip-blocks/usage` | `ListVpcIpAddressAllocations`, `GetVpcIpAddressAllocation`, `PatchVpcIpAddressAllocation`, `updateVpcIpAddressAllocation`, `DeleteVpcIpAddressAllocation` |
| **Subnet IP pools** | `/subnets/{subnet-id}/ip-pools[/{ip-pool-id}]` · `…/ip-allocations[/{id}]` | `ListVpcSubnetIpAddressPools`, `ReadVpcSubnetIpAddressPool`, `ListVpcSubnetIpAllocations`, `PatchVpcSubnetIpAllocation`, `updateVpcSubnetIpAllocation`, `DeleteVpcSubnetIpAllocation` |
| **Service profile** | `/orgs/{org}/projects/{proj}/vpc-service-profiles[/{vpc-service-profile-id}]` | `ListVpcServiceProfiles`, `GetVpcServiceProfile`, `PatchVpcServiceProfile`, `CreateOrReplaceVpcServiceProfile` |
| **Connectivity profile** | `/orgs/{org}/projects/{proj}/vpc-connectivity-profiles[/{id}]` | `ListVpcConnectivityProfiles`, `GetVpcConnectivityProfile`, `PatchVpcConnectivityProfile`, `CreateOrReplaceVpcConnectivityProfile` |

`VpcIpAddressAllocation` **[SPEC]** carries `allocation_ip` / `allocation_ips` /
`allocation_size`, `ip_block`, `ip_address_type` (`IPV4`/`IPV6`) and
`ip_address_block_visibility` ∈ **`EXTERNAL`, `PRIVATE`, `PRIVATE_TGW`** — a three-value enum, not
the two-value one on `IpAddressBlock`. VPC SNAT and DNAT addresses must come from the **external**
block associated with the VPC (P4 note above).

### VPC VPN — where it actually lives

**[DOC — VCF 9.1 What's New: NSX, verbatim]:** *"IPSec VPN service is now supported for VPC using
centralized external connectivity"*, Policy-Based and Route-Based, delivered by the new **Virtual
Network Appliance**.

**There is no `…/vpcs/{vpc-id}/ipsec-vpn-services` path in the 9.1 spec.** The spec-confirmed
tenant VPN surface is **Transit-Gateway-scoped** —
`/orgs/{org}/projects/{proj}/transit-gateways/{transit-gateway-id}/ipsec-vpn-services/…`
**[SPEC]** — which is consistent with "using centralized external connectivity", i.e. the VPN
terminates on the transit gateway that provides the VPC's external connectivity, not on the VPC
object itself. **The mapping from the release-note phrase to that path family is [INFERRED].** If
a user asks for "VPC VPN" in 9.1, point them at the transit-gateway paths and say why.

### The Virtual Network Appliance (VNA) — 9.1

**[DOC]:** a new appliance *"designed to run and support network services within distributed VPC
environments"*, and the enabler for VPC L4 load balancing (*"Layer 4 (L4) load balancing service
is fully supported"*) and VPC IPSec VPN.

Spec surface **[SPEC]**, under
`/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}`:

| Verb | Path tail | operationId |
|---|---|---|
| GET | `/virtual-network-appliance-clusters` | `ListVirtualNetworkApplianceClusters` |
| GET·PATCH·PUT·DELETE | `/virtual-network-appliance-clusters/{id}` | `ReadVirtualNetworkApplianceCluster`, `PatchVirtualNetworkApplianceCluster`, `CreateOrUpdateVirtualNetworkApplianceCluster`, `DeleteVirtualNetworkApplianceCluster` |
| GET | `…/{id}/state` · `/status` · `/allocation/status` | `GetVirtualNetworkApplianceClusterState`, `GetVirtualNetworkApplianceClusterStatus`, `GetVirtualNetworkApplianceClusterAllocationStatus` |
| GET·PATCH·PUT·DELETE | `…/{id}/virtual-network-appliances[/{virtual-network-appliance-id}]` | `ListVirtualNetworkAppliances`, `GetVirtualNetworkAppliance`, `PatchVirtualNetworkAppliance`, `CreateOrUpdateVirtualNetworkAppliance`, `DeleteVirtualNetworkAppliance` |
| POST | `…/action/enter-maintenance-mode` · `/exit-maintenance-mode` · `/evacuate` · `/redeploy` | `VirtualNetworkApplianceEnterMaintenanceMode`, `VirtualNetworkApplianceExitMaintenanceMode`, `EvacuateVirtualNetworkAppliance`, `RedeployVirtualNetworkAppliance` |

Related and new-looking in 9.1: `POST /policy/api/v1/infra/gateways/action/reallocate`
**[SPEC — `GatewayReallocation`]**, described as reallocating or re-balancing gateway service
instances *"within edge or VNA clusters"* **[DOC]**, with a project-scoped variant
(`OrgsOrgIdProjectsProjectIdInfraGatewayReallocation`). `LBNodeCapacity` in the spec is described
as *"the available capacity of the edge or virtual network appliance"* **[SPEC]** — the VNA is a
first-class LB host alongside the edge.

VNA clusters are infrastructure. Treat them as VCF-lifecycle-owned (P9) and read rather than write
unless the task is explicitly VNA lifecycle.

---

## Worked example — a Tier-1 scoped SNAT rule

**Goal:** on an existing Tier-1 gateway, SNAT the `10.20.30.0/24` workload subnet behind a single
public address `203.0.113.10` on egress, logged, in the `USER` NAT section.

The nesting is the point: **a NAT rule lives inside a NAT section, which lives on a gateway, which
needs an edge.** There is no `POST /policy/api/v1/infra/nat-rules`. `{nat-id}` is a system-created
section name, not an id you mint.

```bash
NSX=https://nsx-mgr.example.com
T1=tier1-app-prod          # verify with P2 — do NOT assume it exists or has an edge
NAT_SECTION=USER           # verify with P3 — read the sections, don't assume
RULE=snat-app-prod-egress
SRC_CIDR=10.20.30.0/24
XLATE_IP=203.0.113.10
```

> **This is a production data-path change.** Steps 1–4 are all reads. Nothing is written until
> step 5, and step 7 is the rollback. Do not skip step 3 — writing into `DEFAULT` or `INTERNAL`
> instead of `USER` puts your rule in a reserved section.

### Step 0 — Authenticate

```bash
curl -sS -c /tmp/nsx-session.txt -D /tmp/nsx-headers.txt -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'j_username=svc-nsx-automation@example.com' \
  --data-urlencode 'j_password=<password>' \
  "$NSX/api/session/create"

XSRF=$(grep -i '^x-xsrf-token:' /tmp/nsx-headers.txt | tr -d '\r' | awk '{print $2}')
AUTH=(-b /tmp/nsx-session.txt -H "x-xsrf-token: $XSRF" -H 'Content-Type: application/json')
```

Pin every subsequent call to the **same manager node address**. Full auth detail lives in
`vcf-foundation`.

### Step 1 — Confirm the Tier-1 exists, and read what it advertises (P2, P4)

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/tier-1s/$T1" \
  | jq '{path, type, ha_mode, pool_allocation, route_advertisement_types, tier0_path}'
```

`GET /policy/api/v1/infra/tier-1s/{tier-1-id}` — **[SPEC — `ReadTier1`]**. Expect 200.

Two things to check in that output before continuing:
- `route_advertisement_types` **must contain `TIER1_NAT`**, or the translated address will not be
  advertised to the Tier-0 and return traffic will not find its way back (P4).
- `ha_mode` — the spec states SNAT is *"only supported when the logical router is running in
  active-standby mode"* (P2).

### Step 2 — Confirm the Tier-1 has an edge to run NAT on (P2)

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/tier-1s/$T1/locale-services" \
  | jq '.results[] | {path, edge_cluster_path}'
```

`GET /policy/api/v1/infra/tier-1s/{tier-1-id}/locale-services`
— **[SPEC — `ListTier1LocaleServices`]**. An empty result, or a result with no
`edge_cluster_path`, means NAT has nowhere to run: the write will succeed and never realise.

### Step 3 — Read the NAT sections and capture the `USER` section path (P3)

```bash
NAT_PATH=$(curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/tier-1s/$T1/nat" \
  | jq -r --arg s "$NAT_SECTION" '.results[] | select(.nat_type == $s) | .path')

case "$NAT_PATH" in
  ''|null) echo "FATAL: NAT section '$NAT_SECTION' not found on $T1" >&2; exit 1 ;;
esac
echo "NAT section: $NAT_PATH"
```

`GET /policy/api/v1/infra/tier-1s/{tier-1-id}/nat` — **[SPEC — `ListPolicyNatOnTier1`]**. Returns
the four system-created sections (`INTERNAL`, `USER`, `DEFAULT`, `NAT64`), each with
`"_system_owned": true`. There is **no** `GET …/nat/{nat-id}` single-section read on `/infra`
Tier-1 — the list is the check.

### Step 4 — See what is already in the section before you add to it

```bash
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules" \
  | jq '.results[] | {id, action, sequence_number, source_network, translated_network, enabled}'
```

`GET …/nat/{nat-id}/nat-rules` — **[SPEC — `ListPolicyNatRules`]**. Two things you are looking
for: an existing rule with the same `sequence_number` (ordering collision) and an existing broader
SNAT that already covers `$SRC_CIDR` (your rule will never match). This read is what turns "the
rule didn't work" into a five-second diagnosis.

### Step 5 — Write the rule

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules/$RULE" \
  -d "$(jq -n --arg src "$SRC_CIDR" --arg xlate "$XLATE_IP" '{
    display_name:        "SNAT app-prod egress",
    description:         "Managed by automation",
    action:              "SNAT",
    source_network:      $src,
    translated_network:  $xlate,
    sequence_number:     100,
    firewall_match:      "MATCH_INTERNAL_ADDRESS",
    logging:             true,
    enabled:             true
  }')"
```

`PATCH /policy/api/v1/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules/{nat-rule-id}`
— **[SPEC — `PatchPolicyNatRule`]**. Field notes, all **[SPEC]**:

- `action: "SNAT"` — the only **required** field on `PolicyNatRule`.
- `source_network` is **mandatory for SNAT** and accepts a single IP, a CIDR, or a comma-separated
  list of single IPs. It does **not** accept an IP range or an IP set. Leave it null and you have
  written "SNAT everything", which is how a NAT change becomes an outage.
- `translated_network` is **mandatory for SNAT**. A CIDR here is treated as a translation pool
  *"that includes both the subnet and broadcast addresses as valid for NAT translations"* — use a
  single address unless you mean a pool.
- `firewall_match` defaults to `MATCH_INTERNAL_ADDRESS`; it is set explicitly here so that gateway
  firewall rules written against `10.20.30.0/24` still match after translation. Flip to
  `MATCH_EXTERNAL_ADDRESS` if your firewall rules are written against `203.0.113.10`.
- `sequence_number` maps 1:1 to rule priority; the valid range in the `USER` section is
  0–2147481599. Leave gaps (100, 200, 300) so later insertions do not require a renumber.
- **`service` is deliberately omitted.** For SNAT the spec says the service's destination port
  *"will be ignored"* — a service reference here buys nothing and misleads the next reader.
- **`scope` is deliberately omitted**, which applies the rule to the whole gateway. Set it to an
  array of interface policy paths (`ProviderInterface` / `NetworkInterface`, *"must belong to the
  same router"*) if you need to restrict egress to one uplink.
- `PATCH` rather than `PUT`: create-or-update without `_revision` (P9). A `PUT` works too, but you
  must omit `_revision` on the creating call and supply it on every subsequent one.

### Step 6 — Verify realisation, not just acceptance

```bash
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules/$RULE" | jq '.'

curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules/$RULE/statistics" | jq '.'
```

`GET …/nat-rules/{nat-rule-id}` **[SPEC — `GetPolicyNatRule`]** proves the object exists.
`GET …/nat-rules/{nat-rule-id}/statistics`
**[SPEC — `GetPolicyNatRuleStatisticsFromTier1`]** proves it is programmed in the data path and
counting packets. **A 200 on the object read is not evidence that NAT is happening.**

### Step 7 — Roll back without deleting

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules/$RULE" \
  -d '{"enabled": false}'
```

`enabled` has a default of `true` and is the intended disable switch **[SPEC]**. Prefer this to
`DELETE /…/nat-rules/{nat-rule-id}` **[SPEC — `DeletePolicyNatRule`]** during a change window:
it is reversible in one call and leaves the object for post-incident inspection. Note that this
relies on partial-patch behaviour (P9) — if partial patch is not enabled on the appliance, read
the rule, set `enabled: false` in the full body, and `PATCH` that.

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| 403 immediately after a successful step 0 | `X-XSRF-TOKEN` not sent on the follow-up call. |
| 403 mid-sequence after a pause | Session expired — NSX returns **403, not 401**. Re-authenticate and retry once. |
| 403 that persists after re-auth | Role too low (P1). Note NSX has narrow roles — a VPN Admin cannot write NAT. |
| 403 only on some calls, apparently at random | Cookie used against a different cluster node behind a VIP. Pin the node. |
| 404 on step 1 | Wrong Tier-1 id, or the gateway is project-scoped and you need the `orgs/…/projects/…/infra/` family. |
| 404 on step 5 with a valid Tier-1 | `{nat-id}` is wrong. It must be a section name from step 3, not a UUID. |
| 400 on step 5, `translated_network` | You supplied an IP range or an IP set. Only single IPs, comma-separated single IPs, or CIDRs are accepted. |
| 400 on step 5, `action` | Missing `action`, or `NO_SNAT`/`NO_DNAT` sent with a `translated_network`. |
| 200 on step 5, zero statistics on step 6 | Not realised. Check the locale service / edge cluster (step 2) first, then that traffic is actually traversing this Tier-1. |
| Rule realised, traffic still fails outbound | `TIER1_NAT` missing from `route_advertisement_types` (step 1), so the translated address is not advertised north. |
| Rule realised, traffic dropped by firewall | `firewall_match` set to the wrong address family for your gateway firewall rules (P4). |
| Rule realised but never matches | A lower `sequence_number` rule in the same section already covers the source (step 4), or a `NO_SNAT` rule is exempting it. |
| SNAT rejected on a Tier-0 | The Tier-0 is `ACTIVE_ACTIVE`; SNAT requires active-standby. Use `REFLEXIVE`. |

---

## What is unverified for 9.1

- **The DLB / DFW decoupling conflict.** The release notes say decoupled; the spec still lists
  Distributed Load Balancer under DFW dependent services and under what `enable_firewall: false`
  turns off. Recorded, not resolved.
- **Whether the 9.0 NSX load-balancer entitlement narrowing still applies in 9.1.** The 9.1 support
  notes do not restate it. Not revoked, not confirmed.
- **The mapping from "VPC IPSec VPN" (release note) to the transit-gateway VPN path family** is
  inferred; no `vpcs/{vpc-id}/ipsec-vpn-services` path exists in the spec.
- **The 10-CIDR / 10-range IP Block limit** is a release-note figure. The `IpAddressBlock` schema
  declares no `maxItems` on `cidrs` or `ranges`, so the limit is not spec-visible.
- **The paths of the 17 Manager-API / 9 Policy-API / 1 Autonomous-Edge operations removed in 9.1**
  are not published by Broadcom — only the counts and themes. One Policy-API removal theme (VPC
  Subnet Bridge Profiles lifecycle) touches VPC networking.
- **`GET /infra/tier-{0,1}s/{id}/nat/{nat-id}`** (single-section read) does not exist on `/infra`
  in the spec, only on VPC and Transit Gateway. Whether that is an omission or intentional is
  unknown.
- **No authoritative VCF-owned-vs-operator-owned NSX object list exists** for either version.
