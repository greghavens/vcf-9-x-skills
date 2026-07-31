# NSX network services (NAT · LB · VPN · IPAM · VPC) — VCF 9.0

**Applies to:** NSX **9.0.0.0** (build 24733065), the NSX version in the VCF 9.0 Bill of Materials.
**Do not apply this file to VCF 9.1.** Use `../9.1/services.md` for 9.1 and `../deltas.md` for the
change list.

> **Patch-line caveat.** The VCF 9.0 BOM page is maintained across the 9.0.x patch line and at time
> of research also listed VCF Installer 9.0.2.0. Separate NSX API doc sets exist for **9.0.0,
> 9.0.1 and 9.0.2**. If the target is on a 9.0.x patch, re-check the BOM — the NSX build will
> differ. The 9.0.1 / 9.0.2 build numbers are **unverified**.

---

## READ THIS FIRST — the 9.0 evidence for *network services* is thin, and thinner in places than for the firewall

**There is no NSX OpenAPI specification published at the `9.0.0.0` tag of
`github.com/vmware/vcf-api-specs`.** The machine-extracted spec inventory records `nsx-policy`,
`nsx-manager` and `nsx-global-policy` all as **`9.0 present: no`**. Specs for those three products
appear only at the `9.1.0.0` tag (3,729 / 1,453 / 1,009 operations).

For this subject area that produces three tiers of 9.0 knowledge, and you must not flatten them:

| Area | 9.0 status |
|---|---|
| **IP pools, IP allocations, IP subnets** | **Prose-verified** on a 9.0.0-pinned page, full CRUD. The strongest 9.0 material in this file. |
| **Load balancer service (single read)** | **Prose-verified** — exactly one operation. |
| **Tier-0 / Tier-1 gateway reads** | **Prose-verified** (the object NAT/VPN/LB attach to). |
| **Policy NAT rule paths** | **Could not be verified for 9.0 at all.** Recorded verbatim in the research as *"UNVERIFIED — could not retrieve."* |
| **IPSec VPN service paths** | **Could not be verified for 9.0 at all.** Same. |
| **IP blocks, LB virtual servers / pools / profiles, VPC-scoped services, Avi/ALB endpoints** | Not covered by the 9.0 research. Known from 9.1 only. |

**A path being spec-confirmed for 9.1 is not evidence about 9.0.** The 9.1 reference file marks
many operations `[SPEC]`. Those tags mean nothing here, and this file never re-uses them. Where a
path is known only from 9.1 it is marked **`[9.1-ONLY — NOT VERIFIED FOR 9.0]`** and you must
confirm it on the appliance before use.

**The single reliable 9.0 verification route is the appliance itself:**
`GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json` **[DOC-9.0]**. The running NSX
Manager serves the OpenAPI document matching its own deployed build. For NAT and VPN in 9.0, this
is not optional — it is step one.

Evidence tags used below:

| Tag | Meaning |
|---|---|
| **[DOC-9.0]** | Read from a **9.0.0**-pinned Broadcom page. The strongest evidence available for 9.0. |
| **[DOC-9.0-partial]** | The path was seen on a 9.0.0 page but not every verb listed here was. |
| **[9.1-ONLY — NOT VERIFIED FOR 9.0]** | Known from the 9.1 doc set or 9.1 spec only. Confirm on the appliance first. |
| **[INFERRED]** | A shape or convention, not a verified fact. |

> **Documentation, not live validation.** Captured 2026-07-31. **NAT and VPN operations are
> production-affecting** — and in 9.0 you are additionally acting on unverified paths. Confirm
> against the appliance spec, prefer `enabled: false` over `DELETE` when backing out, and read
> before you overwrite.

---

## Contents

- [**READ THIS FIRST**](#read-this-first--the-90-evidence-for-network-services-is-thin-and-thinner-in-places-than-for-the-firewall) — the three tiers of 9.0 knowledge
- [**Prerequisites**](#prerequisites) — **read before any write**
  - [P1 — Reachability, authentication and role](#p1--you-can-reach-nsx-manager-authenticate-and-hold-a-role-that-can-write)
  - [P2 — Confirm the endpoint exists on *this* appliance](#p2--nat-and-vpn-confirm-the-endpoint-exists-on-this-appliance-first)
  - [P3 — The gateway exists and can host services](#p3--the-gateway-exists-and-can-host-a-centralised-service)
  - [P4 — NAT: the section id, and reachability of the translated address](#p4--nat-the-section-id-and-whether-the-translated-address-is-reachable)
  - [P5 — LB: the objects, and the 9.0 entitlement narrowing](#p5--lb-the-object-chain-and-the-90-entitlement-narrowing)
  - [P6 — VPN: service, local endpoint, session — path form unresolved](#p6--vpn-service-local-endpoint-session--and-which-path-form-90-accepts-is-unresolved)
  - [P7 — IPAM: the pool exists before the allocation](#p7--ipam-the-pool-exists-before-you-allocate-from-it)
  - [P8 — `_revision`, partial patch, VCF ownership](#p8--concurrency-partial-patch-and-vcf-ownership)
- [Authentication in one paragraph](#authentication-in-one-paragraph)
- [Path families](#path-families)
- [NAT in 9.0](#nat-in-90)
- [Load balancing in 9.0](#load-balancing-in-90)
- [VPN in 9.0](#vpn-in-90)
- [IPAM in 9.0](#ipam-in-90--the-solid-ground)
- [VPCs in 9.0](#vpcs-in-90)
- [**Worked example** — Tier-1 scoped SNAT rule, with the 9.0 verification gate](#worked-example--a-tier-1-scoped-snat-rule-with-the-90-verification-gate)
- [Summary: what remains unverified for 9.0](#summary-what-remains-unverified-for-90)

---

## Prerequisites

Everything in this section must be true **before** you issue any network-service write. Each item
carries **four** elements — if one is missing, the item is incomplete:

1. **What must be true** — the condition itself.
2. **How to verify it** — a concrete, *non-destructive* call. Never verify a permission or a
   contract by performing the production change it guards.
3. **Which version it applies to** — every item below applies to **NSX 9.0.0.0** unless stated.
4. **Whether it exists in the other version** — stated as a "9.1 difference" line on every item.

### P1 — You can reach NSX Manager, authenticate, and hold a role that can write

- **Must be true:** HTTPS reachability to a specific manager node with a trusted chain (VCF-deployed
  appliances default to VMCA-signed certificates, which are not publicly trusted); a valid session;
  and a role permitting writes. **Enterprise Admin** (`enterprise_admin`) covers everything;
  **Auditor** is read-only. NSX 9.0 ships **15 built-in roles**, and three of them are directly
  relevant to this skill: **Load Balancer Admin**, **Load Balancer Operator** and **VPN Admin**.
  A caller can therefore hold rights over LB and not over VPN, or vice versa. **[DOC-9.0]**
- **Verify — and note a clean read-only verification is *not* spec-confirmable for 9.0.**
  `GET /api/v1/aaa/role-bindings` (`GetAllRoleBindings`) is spec-confirmed for **9.1 only** —
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. It is very likely present in 9.0, but it is not evidenced.
  In order of preference:
  1. Fetch `GET https://<nsx-manager>/api/v1/spec/openapi/nsx_api.json` **[DOC-9.0]** and search
     for `aaa/role-bindings`. The appliance serves the spec for its own build, which converts the
     unverified endpoint into a verified one *for that appliance*. Then call it and read your role.
  2. Failing that, confirm the *session* works with a harmless read against something 9.0-verified
     — `GET /policy/api/v1/infra/ip-pools` **[DOC-9.0]** or
     `GET /policy/api/v1/infra/tier-1s/{tier-1-id}` **[DOC-9.0]**.
  3. Only if neither works, probe write permission against a **throwaway object** you then delete.
  **Do not verify NAT write permission by writing the intended NAT rule.** On success you have
  already changed the data path.
- **Service accounts:** principal identities are the documented 9.0 mechanism, and are what an
  X.509 client certificate binds to. Note the tension: the VCF 9.0 support notes flag Principal
  Identity accounts as *"planned for deprecation in an upcoming release."* **[DOC-9.0]**
- **9.1 difference:** 9.1 adds a spec-confirmed token-based principal identity route
  (`/api/v1/trust-management/token-principal-identities`) that has no 9.0 equivalent and is
  deliberately not reproduced here.

### P2 — NAT and VPN: confirm the endpoint exists on *this* appliance first

- **Must be true:** for NAT and IPSec VPN specifically, **you do not have a verified 9.0 path.**
  The 9.0 research records the Policy NAT rule paths
  (`/policy/api/v1/infra/tier-{0,1}s/{id}/nat/{nat-id}/nat-rules/{nat-rule-id}`) and the IPSec VPN
  service paths as *"UNVERIFIED — could not retrieve"* for 9.0. They exist in 9.1 and the path
  *shape* is a stable Policy-API convention **[INFERRED]** — but that is inference, not evidence.
- **Verify — this is a required step, not an optional one:**

  ```bash
  curl -sS "${AUTH[@]}" \
    "$NSX/api/v1/spec/openapi/nsx_policy_api.json" \
    | jq -r '.paths | keys[]' | grep -E '/nat/|ipsec-vpn-services'
  ```

  **[DOC-9.0 — the spec endpoint itself is 9.0-documented]**. Whatever that returns *is* the truth
  for this build. If the paths are there, proceed and treat them as verified for this appliance
  (record that in the change ticket — it is stronger evidence than any doc page). If the fetch
  fails, fall back to navigating the 9.0.0 developer-portal tree; do **not** fall back to assuming
  the 9.1 paths.
- **9.1 difference:** in 9.1 all of these are spec-confirmed with operationIds, and no appliance
  round-trip is needed. See `../9.1/services.md`.

### P3 — The gateway exists and can host a centralised service

- **Must be true:** NAT, IPSec VPN and the edge-hosted load balancer are centralised services. They
  run on an edge node, so the gateway must have an edge cluster bound to it. A gateway with no edge
  binding has nowhere to run the service; the write is accepted and never realises.
- **Verify:** `GET /policy/api/v1/infra/tier-1s/{tier-1-id}` **[DOC-9.0]** or
  `GET /policy/api/v1/infra/tier-0s/{tier-0-id}` **[DOC-9.0]** returns 200. Capture the `path`
  field from the response body and use that literal string — do not hand-assemble it, especially
  on a project-scoped or Federation deployment where the path is longer.
  For the edge cluster itself,
  `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters/{edge-cluster-id}`
  **[DOC-9.0]** is verified for 9.0 (read only — the *list* form is not).
- **9.0 gap:** the Tier-1 **locale-services** list endpoint, which is where the `edge_cluster_path`
  binding is read in 9.1, was **not** confirmed on a 9.0 page —
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. In 9.0, read the Tier-1 object itself and inspect what it
  returns rather than assuming a sub-collection exists.
- **9.1 difference:** `ListTier1LocaleServices`, `ReadTier1`, `ReadTier0` and
  `ReadEdgeClusterForEnforcementPoint` are all spec-confirmed in 9.1, along with the `Tier1` schema
  fields (`ha_mode`, `pool_allocation`, `route_advertisement_types`) that make the checks precise.

### P4 — NAT: the section id, and whether the translated address is reachable

- **Must be true:**
  - `{nat-id}` in a NAT rule path is a **system-created NAT section**, not an identifier you mint.
    The section names are `INTERNAL`, `USER`, `DEFAULT` and `NAT64`; user rules go in `USER`.
  - A correct rule can still carry no traffic if the gateway does not advertise the translated
    address northbound, or if the gateway firewall is matching the other side of the translation.
- **Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for the section-name enum, the per-section
  `sequence_number` ranges, the `route_advertisement_types` enum (`TIER1_NAT`, `TIER1_LB_VIP`,
  `TIER1_IPSEC_LOCAL_ENDPOINT`, …) and the `firewall_match` enum — all read from the 9.1 spec's
  `PolicyNat`, `PolicyNatRule` and `Tier1` schemas. The 9.0 research captured no NAT schema at all.
  The section model is long-standing Policy-API design and is **[INFERRED]** to be identical in
  9.0.
- **Verify (9.0):** list the sections on the gateway before writing —
  `GET /policy/api/v1/infra/tier-1s/{tier-1-id}/nat`
  **[9.1-ONLY — NOT VERIFIED FOR 9.0; confirm via P2]** — and read the returned `nat_type` / `path`
  values rather than assuming them. Then `GET` an **existing** NAT rule on the same gateway and
  mirror its field names; that one call removes all the schema uncertainty above.
- **9.1 difference:** everything in this item is spec-confirmed in 9.1, including the verbatim
  statement that SNAT and DNAT are *"only supported when the logical router is running in
  active-standby mode."*

### P5 — LB: the object chain, and the 9.0 entitlement narrowing

- **Must be true — licensing before API.** VCF 9.0 **narrowed the NSX Load Balancer entitlement**:
  general-purpose load balancing was removed from the VCF entitlement, **Avi Load Balancer is the
  recommendation**, and NSX LB is retained only for **VCF infrastructure and vSphere Supervisor**
  use cases. **[DOC-9.0 — VCF 9.0 NSX product support notes]** The API does not enforce this:
  `/policy/api/v1/infra/lb-services` will accept writes regardless. **Raise this with the user
  before building a general-purpose VIP on NSX LB in 9.0.**
- **Must be true — the object chain.** A virtual server needs an LB service, an application
  profile, and a pool. In 9.1 the required fields on `LBVirtualServer` are `ports`, `ip_address`
  and `application_profile_path`, and `LBPoolMember` requires `ip_address`.
  **Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** — the 9.0 research captured no LB schemas.
- **Verify (9.0):** the only 9.0-verified LB operation is
  `GET /policy/api/v1/infra/lb-services/{lb-service-id}` **[DOC-9.0]**. Read an existing LB service
  and mirror its shape. Everything else — the list endpoint, virtual servers, pools, monitor /
  persistence / SSL profiles, usage and status endpoints — is
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**; confirm via P2 before use.
- **Avi / NSX ALB in 9.0:** Avi was already the recommendation in 9.0, but **none of the
  `/policy/api/v1/alb/…` or `/infra/alb-*` endpoints, and no `AviConnectionInfo` enforcement-point
  schema, were confirmed on a 9.0 page** — **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. To find out
  whether Avi is integrated on a 9.0 deployment, read the enforcement points on that appliance and
  inspect `connection_info.resource_type`; do not assume the endpoint list from 9.1.
- **9.1 difference:** the whole LB surface is spec-confirmed in 9.1, the ALB integration surface is
  spec-confirmed, and 9.1 adds self-service Avi LB in the VCF Automation / tenant context. The 9.0
  entitlement narrowing was **not restated** in the 9.1 support notes — status unverified, not
  revoked. See `../deltas.md`.

### P6 — VPN: service, local endpoint, session — and which path form 9.0 accepts is unresolved

- **Must be true:** the dependency chain is service → local endpoint → session. A session cannot
  reference a local endpoint that does not exist, and the local endpoint carries the local tunnel
  address.
  **Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for the field names
  (`IPSecVpnLocalEndpoint.local_address` required; `IPSecVpnSession.resource_type` required, enum
  `PolicyBasedIPSecVpnSession` / `RouteBasedIPSecVpnSession`; `PolicyBasedIPSecVpnSession.rules`
  required) — all read from the 9.1 spec.
- **The path-form question is genuinely open for 9.0.** NSX has historically carried two families:
  gateway-scoped (`/infra/tier-1s/{id}/ipsec-vpn-services/…`) and locale-service-scoped
  (`/infra/tier-1s/{id}/locale-services/{locale-service-id}/ipsec-vpn-services/…`). In **9.1** both
  exist and the locale-service family is flagged `deprecated: true` throughout. **For 9.0, neither
  family was verified**, so this file cannot tell you which one your build prefers — or whether
  both work.
- **Verify (9.0):** P2, then list what the appliance actually exposes:

  ```bash
  curl -sS "${AUTH[@]}" "$NSX/api/v1/spec/openapi/nsx_policy_api.json" \
    | jq -r '.paths | keys[]' | grep 'ipsec-vpn-services'
  ```

  Then `GET` an existing VPN service and session on that appliance and mirror the shape. **Before
  touching a live tunnel, capture its current status** so you know what "working" looked like.
- **9.1 difference:** gateway-scoped is spec-confirmed and current; locale-service-scoped is
  spec-confirmed and deprecated. The deprecation is a **9.1** observation and implies nothing about
  which form 9.0 accepts.

### P7 — IPAM: the pool exists before you allocate from it

- **Must be true:** an IP allocation is a child of a pool
  (`/infra/ip-pools/{ip-pool-id}/ip-allocations/{ip-allocation-id}`), and pool subnets are children
  of the pool (`/infra/ip-pools/{ip-pool-id}/ip-subnets/{ip-subnet-id}`). Create or confirm the
  pool first; allocating from a pool that does not exist is a 404, and allocating from an exhausted
  pool is a realisation failure.
- **Verify:** `GET /policy/api/v1/infra/ip-pools` **[DOC-9.0]** and
  `GET /policy/api/v1/infra/ip-pools/{ip-pool-id}` **[DOC-9.0]**, then
  `GET /policy/api/v1/infra/ip-pools/{ip-pool-id}/ip-subnets/{ip-subnet-id}` **[DOC-9.0]** for the
  ranges. **This is the best-evidenced area of 9.0 in this file** — full GET·PUT·PATCH·DELETE on
  pools, allocations and subnets is confirmed on a 9.0.0-pinned page.
- **9.0 gap — IP blocks.** `/policy/api/v1/infra/ip-blocks` and its `usage`, `allocation-state` and
  `available-subnets` sub-resources were **not** covered by the 9.0 research —
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. If the task involves carving subnets out of a block in
  9.0, confirm via P2 first.
- **Schema note:** the `IpAddressPool` / `IpAddressPoolStaticSubnet` / `IpAddressAllocation` field
  names given in `../9.1/services.md` are **[9.1-ONLY — NOT VERIFIED FOR 9.0]**; the paths are
  9.0-verified but the bodies were never captured. `GET` an existing pool and mirror it.
- **9.1 difference:** identical paths plus IP blocks, project-scoped and VPC-scoped variants, and
  the 9.1 IP Block expansion to multiple CIDRs / ranges / exclusions. See `../deltas.md`.

### P8 — Concurrency, partial patch, and VCF ownership

- **`_revision`:** every REST payload carries an integer `_revision`; it must be supplied on `PUT`
  and must match. The 9.0 API Guide notes only that *"APIs whose URI begins with /policy have
  slightly different behavior."* The precise rule — omit on a creating `PUT`, supply on subsequent
  ones — is verbatim only in the **9.1** guide, so for 9.0 it is **[INFERRED]**. Using `PATCH` for
  creates sidesteps the question entirely, and the worked example below does.
- **Partial patch is off by default:** enable with
  `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` `{"enable_partial_patch": "true"}`
  **[DOC-9.0]**. The **`GET`** verb on that path is spec-confirmed for 9.1 only —
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. This matters for the rollback pattern: if partial patch is
  off, a `PATCH {"enabled": false}` may not do what you expect — read the object and send the full
  body with `enabled` flipped.
- **VCF ownership:** there is **no authoritative published list** of which NSX objects VCF owns.
  What *is* documented for 9.0 **[DOC-9.0]**: standalone NSX install/upgrade is not supported; only
  one NSX instance per vCenter; NSX Embedded and the Migration Coordinator removed; NSX operates in
  FIPS-enabled mode by default and this cannot be deactivated; and the LB entitlement narrowing in
  P5. 9.0 has **no** SDDC Manager network-sync reconciliation statement, so out-of-band NSX edits
  are *less* clearly supported in 9.0 than in 9.1.
  **Practical rule [INFERRED]:** NAT rules, LB virtual servers/pools, VPN sessions and user IP
  pools are operator-authored; gateways, edge clusters and fabric objects are VCF-lifecycle-owned.
  Verify per object by reading `_system_owned` / `_protection` / `_create_user` from the actual 9.0
  response body — those field names are `PolicyConfigResource` fields spec-confirmed for **9.1
  only**, so read what the appliance returns rather than assuming the keys exist.
- **9.1 difference:** 9.1 adds SDDC Manager network sync, which reconciles *"network configuration
  changes done directly in vCenter or NSX Manager"* — the closest thing to permission for
  out-of-band edits, and it does not exist in 9.0.

---

## Authentication in one paragraph

`POST /api/session/create` (form-encoded `j_username` / `j_password`) returns a `JSESSIONID`
cookie **and** an `X-XSRF-TOKEN` header; send **both** on every subsequent call. Destroy with
`POST /api/session/destroy`. Default session timeout 1800 s, changed via
`PUT /api/v1/cluster/api-service`. **Session cookies are manager-node-specific and cannot be reused
across cluster nodes** — pin the client. All **[DOC-9.0]**. URL-encode the password: *"`+` and
other special characters in passwords must be URL-encoded."* **[DOC-9.0]**

The *"NSX Manager responds with a 403 Forbidden HTTP response"* statement on session expiry was
read on the **9.1**-pinned page, not the 9.0 one — **[9.1-ONLY — NOT VERIFIED FOR 9.0]** as a
documented statement. Handle it anyway: treat 403 as a re-auth trigger, retry once, and if the
retry is also 403 it is authorization (P1), not expiry.

**Anything beyond that belongs to `vcf-foundation`.** Do not re-derive the auth surface here.

---

## Path families

| Family | Template | Evidence for 9.0 |
|---|---|---|
| Local | `/policy/api/v1/infra/…` | **[DOC-9.0]** |
| Global (Federation) | `/policy/api/v1/global-infra/…` | **[DOC-9.0]** — confirmed for Tier-0, Tier-1, transport zones and edge clusters on 9.0.0 pages |
| Project (multi-tenancy) | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/…` | **[DOC-9.0]** — confirmed for Tier-1 and segments on 9.0.0 pages |
| Transit Gateway | `/policy/api/v1/orgs/{org}/projects/{proj}/transit-gateways/{tgw-id}/…` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — Transit Gateways *exist* in 9.0, but no TGW-scoped NAT or VPN path was confirmed |
| VPC | `/policy/api/v1/orgs/{org}/projects/{proj}/vpcs/{vpc-id}/…` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — VPCs exist in 9.0; VPC-scoped *service* paths were not confirmed |

These families are **not** interchangeable: reading a project-scoped object through `/infra/`
returns 404.

The general Policy-API path shape — `/infra/tier-0s/{id}/<service>`,
`/infra/tier-1s/{id}/<service>`, `/infra/<collection>/{id}`,
`/infra/sites/{site}/enforcement-points/{ep}/<fabric-object>` — is verified as a **convention** in
both doc sets **[DOC-9.0]**. That it is a convention is *not* evidence that a specific service
collection exists on a specific gateway in 9.0. That is what P2 is for.

---

## NAT in 9.0

**Status: the Policy NAT surface is unverified for 9.0.** Confirm via P2 before use.

| Path | Evidence |
|---|---|
| `GET /api/v1/logical-routers/{logical-router-id}/nat/rules/{rule-id}` | **[DOC-9.0]** — and carries an explicit deprecation notice in the 9.0.0 doc set: *"This endpoint is deprecated as of version 9.0."* This is the **Manager API**. Do not build on it. |
| `/policy/api/v1/infra/tier-0s/{tier-0-id}/nat` · `/nat/{nat-id}/nat-rules[/{nat-rule-id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `/policy/api/v1/infra/tier-1s/{tier-1-id}/nat` · `/nat/{nat-id}/nat-rules[/{nat-rule-id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `…/nat-rules/{nat-rule-id}/statistics`, `…/nat/statistics` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `global-infra`, project-scoped, VPC-scoped and Transit-Gateway-scoped NAT | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |

The `PolicyNatRule` body (`action` required; `SNAT`/`DNAT`/`REFLEXIVE`/`NO_SNAT`/`NO_DNAT`/`NAT64`;
`source_network`, `destination_network`, `translated_network`, `translated_ports`, `service`,
`scope`, `sequence_number`, `enabled`, `logging`, `firewall_match`, `policy_based_vpn_mode`) is
listed in full in `../9.1/services.md` and is **[9.1-ONLY — NOT VERIFIED FOR 9.0]** here. The 9.0
research captured no NAT schema.

**What to do in 9.0:** P2 to confirm the paths, then `GET` an existing NAT rule on the target
gateway and mirror its field names. That single read converts every `[INFERRED]` above into an
observed fact for that appliance.

**One thing that *is* solid for 9.0:** the Manager-API NAT path is deprecated as of 9.0. If a user
has automation calling `/api/v1/logical-routers/.../nat/rules/...`, tell them now.

---

## Load balancing in 9.0

| Path | Evidence |
|---|---|
| `GET /policy/api/v1/infra/lb-services/{lb-service-id}` | **[DOC-9.0]** — the *only* 9.0-verified LB operation |
| `GET /policy/api/v1/infra/lb-services` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `PATCH·PUT·DELETE /policy/api/v1/infra/lb-services/{lb-service-id}` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — the write verbs almost certainly exist (an LB service has to be creatable) but were not evidenced on a 9.0.0 page |
| `/infra/lb-virtual-servers[/{id}]`, `/infra/lb-pools[/{id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `/infra/lb-app-profiles`, `/infra/lb-monitor-profiles`, `/infra/lb-persistence-profiles`, `/infra/lb-client-ssl-profiles`, `/infra/lb-server-ssl-profiles`, `/infra/lb-ssl-ciphers-and-protocols` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `…/detailed-status`, `…/statistics`, `/infra/lb-node-usage*`, `/infra/lb-service-usage-summary`, `…/debug-info` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `/policy/api/v1/alb/…`, `/infra/alb-auth-token`, `/infra/alb-onboarding-workflow` (Avi / NSX ALB) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| VPC-scoped LB (`/vpc-lbs`, `/vpc-lb-*`) | **[9.1-ONLY]** — VPC L4 load balancing is a **9.1** feature delivered by the Virtual Network Appliance; treat it as absent in 9.0 unless proven otherwise on the appliance |

**The entitlement question comes before the API question in 9.0.** General-purpose NSX load
balancing was removed from the VCF entitlement in 9.0; Avi is the recommendation; NSX LB is
retained for VCF infrastructure and vSphere Supervisor. **[DOC-9.0]** Say this before writing an
LB service, not after.

---

## VPN in 9.0

**Status: unverified for 9.0.** The 9.0 research explicitly records IPSec VPN service paths as
*"UNVERIFIED — could not retrieve."*

| Path family | Evidence |
|---|---|
| Gateway-scoped `/policy/api/v1/infra/tier-{0,1}s/{id}/ipsec-vpn-services[/{service-id}]` and its `local-endpoints` / `sessions` sub-trees | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| Locale-service-scoped `…/locale-services/{locale-service-id}/ipsec-vpn-services/…` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]**, and flagged `deprecated: true` **in 9.1**. That deprecation says nothing about 9.0. |
| L2VPN (`/l2vpn-services`, `l2vpn-context`, `l3vpns`) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `/infra/ipsec-vpn-ike-profiles`, `/infra/ipsec-vpn-tunnel-profiles`, `/infra/ipsec-vpn-dpd-profiles` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| Transit-Gateway-scoped VPN | **[9.1-ONLY]** — a 9.1 capability |

`IPSecVpnService` / `IPSecVpnLocalEndpoint` / `IPSecVpnSession` field names and enums are listed in
`../9.1/services.md` and are **[9.1-ONLY — NOT VERIFIED FOR 9.0]**.

**What to do in 9.0:** P2 and P6. Confirm which path family the appliance exposes, read an existing
service and session, mirror the shape, and capture the tunnel's current status before you change
anything.

---

## IPAM in 9.0 — the solid ground

All rows **[DOC-9.0]**, read from a 9.0.0-pinned page. This is the best-evidenced network-service
area for 9.0.

| Verb | Path (append to `/policy/api/v1`) |
|---|---|
| GET | `/infra/ip-pools` |
| GET·PUT·PATCH·DELETE | `/infra/ip-pools/{ip-pool-id}` |
| GET·PUT·PATCH·DELETE | `/infra/ip-pools/{ip-pool-id}/ip-allocations/{ip-allocation-id}` |
| GET·PUT·PATCH·DELETE | `/infra/ip-pools/{ip-pool-id}/ip-subnets/{ip-subnet-id}` |

Not confirmed for 9.0:

| Path | Evidence |
|---|---|
| `/infra/ip-pools/{ip-pool-id}/ip-allocations` (list) · `/ip-subnets` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — the 9.0 page gave the item paths, not the collection listings |
| `/infra/ip-blocks[/{ip-block-id}]` and its `usage` / `allocation-state` / `available-subnets` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| `/infra/manager-ip-pools[/{id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| Project-scoped and VPC-scoped IP pool / block variants | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |

Body schemas (`IpAddressPool`, `IpAddressPoolStaticSubnet`, `IpAddressAllocation`) were **not**
captured for 9.0 — **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. `GET` an existing pool and mirror it.

---

## VPCs in 9.0

VPCs, subnets, Transit Gateways, Connectivity Profiles and Service Profiles all **exist in 9.0**
**[DOC-9.0 — VCF 9.0 What's New: NSX]**, including VPC creation from vCenter, VPC in VCF
Automation, VPC in Supervisor, and both centralized and distributed Transit Gateway types.

What is **not** established for 9.0 is the VPC-scoped **service** surface:

- **VPC load balancing** — the 9.0 What's New calls out no VPC L4 LB service. VPC L4 LB is a
  **9.1** feature delivered by the new Virtual Network Appliance. **[DOC — 9.1 What's New]**
- **VPC IPSec VPN** — likewise called out as new in **9.1**.
- **VPC NAT paths** (`/orgs/…/vpcs/{vpc-id}/nat/…`) — **[9.1-ONLY — NOT VERIFIED FOR 9.0]**.
- **1:N SNAT with the distributed Transit Gateway** — a **9.1** addition. **[DOC — 9.1]**

Treat VPC-scoped NAT, LB and VPN as **9.1 capabilities** in any 9.0 conversation, and say that the
absence is release-note-based rather than proven by a 9.0 API enumeration.

---

## Worked example — a Tier-1 scoped SNAT rule, with the 9.0 verification gate

**Goal:** on an existing Tier-1 gateway, SNAT the `10.20.30.0/24` workload subnet behind
`203.0.113.10` on egress, logged, in the `USER` NAT section.

> **Blocker before you start.** The Policy NAT path family used below is
> **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. Step 1 is not optional: it converts these paths from
> inference into observed fact *for this appliance*. If step 1 does not find the paths, stop and
> navigate the 9.0.0 developer-portal reference — do not proceed on the 9.1 shape.
>
> **And this is a production data-path change.** Steps 1–4 are reads. Nothing is written until
> step 5, and step 7 is the rollback.

```bash
NSX=https://nsx-mgr.example.com
T1=tier1-app-prod
NAT_SECTION=USER
RULE=snat-app-prod-egress
SRC_CIDR=10.20.30.0/24
XLATE_IP=203.0.113.10
```

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

`POST /api/session/create` — **[DOC-9.0]**. Pin every subsequent call to the same manager node.

### Step 1 — **The 9.0 gate:** confirm the NAT paths exist on this build (P2)

```bash
curl -sS "${AUTH[@]}" "$NSX/api/v1/spec/openapi/nsx_policy_api.json" \
  | jq -r '.paths | keys[]' | grep -E 'tier-1s/\{tier-1-id\}/nat'
```

`GET /api/v1/spec/openapi/nsx_policy_api.json` — **[DOC-9.0]**. Expect to see
`/infra/tier-1s/{tier-1-id}/nat` and
`/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules/{nat-rule-id}`. **If they are absent, stop.**

### Step 2 — Confirm the Tier-1 exists and capture its path (P3)

```bash
T1_PATH=$(curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/tier-1s/$T1" | jq -r '.path')
case "$T1_PATH" in ''|null) echo "FATAL: Tier-1 '$T1' not found" >&2; exit 1 ;; esac
echo "gateway: $T1_PATH"
```

`GET /policy/api/v1/infra/tier-1s/{tier-1-id}` — **[DOC-9.0]**. Inspect the rest of the body while
you are here: the field names you see are the 9.0 truth, and in 9.1 this object carries
`route_advertisement_types` (must include `TIER1_NAT`) and `ha_mode` (SNAT needs active-standby).
**Those field names are [9.1-ONLY — NOT VERIFIED FOR 9.0]** — read what the appliance actually
returns rather than assuming them.

### Step 3 — Read the NAT sections and confirm `USER` exists (P4)

```bash
NAT_PATH=$(curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/tier-1s/$T1/nat" \
  | jq -r --arg s "$NAT_SECTION" '.results[] | select(.nat_type == $s) | .path')
case "$NAT_PATH" in ''|null) echo "FATAL: NAT section '$NAT_SECTION' not found" >&2; exit 1 ;; esac
echo "NAT section: $NAT_PATH"
```

`GET /policy/api/v1/infra/tier-1s/{tier-1-id}/nat` — **[9.1-ONLY — NOT VERIFIED FOR 9.0]**,
confirmed for this appliance in step 1. The section names (`INTERNAL`, `USER`, `DEFAULT`,
`NAT64`) and the `nat_type` field name are **[INFERRED]** for 9.0 — which is precisely why this
step reads them instead of hard-coding `USER` into the write path.

### Step 4 — Read an existing rule and mirror its shape

```bash
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules" | jq '.results[0]'
```

**This is the step that removes the schema uncertainty.** The 9.0 research captured no NAT schema,
so the field names in step 5 are inferred from the 9.1 spec. One read of a real rule on this
gateway tells you the actual field names, and simultaneously shows you whether an existing rule
already covers `$SRC_CIDR` or collides on `sequence_number`.

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

`PATCH …/nat/{nat-id}/nat-rules/{nat-rule-id}` — **[9.1-ONLY — NOT VERIFIED FOR 9.0]** for the
path, confirmed for this appliance in step 1; **[9.1-ONLY — NOT VERIFIED FOR 9.0]** for every field
name and enum value, cross-checked against the real object in step 4.

Field notes (all read from the 9.1 `PolicyNatRule` schema, inferred for 9.0):
- `action` is the only required field; `SNAT` needs `source_network` **and**
  `translated_network`.
- `source_network` accepts a single IP, a CIDR, or a comma-separated list of single IPs — **not**
  an IP range and **not** an IP set. Omitting it means "SNAT everything," which is how a NAT change
  becomes an outage.
- `firewall_match` decides whether the gateway firewall sees the pre- or post-NAT address. The 9.1
  default is `MATCH_INTERNAL_ADDRESS`; it is set explicitly here rather than relied on, because the
  9.0 default is not evidenced.
- `service` is omitted deliberately — for SNAT the service's destination port is ignored.
- `PATCH` rather than `PUT`: create-or-update without `_revision`, whose exact 9.0 semantics are
  inferred (P8).

**If step 5 returns 400,** the field names differ. Go back to step 4 and mirror the real object.

### Step 6 — Verify realisation, not just acceptance

```bash
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules/$RULE" | jq '.'

curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules/$RULE/statistics" | jq '.'
```

Both **[9.1-ONLY — NOT VERIFIED FOR 9.0]**, confirmed for this appliance in step 1. A 200 on the
object read proves the object exists; only the statistics endpoint proves the rule is programmed in
the data path.

### Step 7 — Roll back without deleting

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/nat/$NAT_SECTION/nat-rules/$RULE" \
  -d '{"enabled": false}'
```

Prefer this to `DELETE`: reversible in one call, and the object survives for post-incident
inspection. **Caveat for 9.0:** this single-field `PATCH` depends on partial-patch behavior, whose
9.0 read-back verb is unverified (P8). If it does not take effect, read the full rule, set
`enabled: false` in the whole body, and `PATCH` that.

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| Step 1 finds no `/nat` paths | This build does not expose Policy NAT where 9.1 does. Stop and check the 9.0.0 developer-portal reference. Do not guess. |
| 403 immediately after a successful step 0 | `X-XSRF-TOKEN` not sent on the follow-up call. |
| 403 mid-sequence after a pause | Session expired. Treat 403 as re-auth — note the 403-on-expiry statement is 9.1-doc-verified, not 9.0-doc-verified. |
| 403 that persists after re-auth | Role too low (P1). NSX 9.0 has narrow roles — VPN Admin cannot write NAT. |
| 403 only on some calls, apparently random | Cookie used against a different cluster node behind a VIP — this **is** 9.0-doc-verified. Pin the node. |
| 404 on step 2 | Wrong Tier-1 id, or the gateway is project-scoped and needs the `orgs/…/projects/…/infra/` family. |
| 404 on step 5 with a valid Tier-1 | `{nat-id}` wrong — it must be a section name captured in step 3. |
| 400 on step 5 | Field-name or enum mismatch; the 9.0 schema is inferred. Mirror the real object from step 4. |
| 200 on step 5, zero statistics on step 6 | Not realised. The Tier-1 probably has no edge cluster bound (P3). |
| Realised but no traffic effect | Route advertisement or gateway-firewall matching — both **[9.1-ONLY]** as documented mechanisms, but the failure mode is real in 9.0 too. |
| 429 | Rate limit — 100 req/s per client per 9.0 prose. Back off. |

---

## Summary: what remains unverified for 9.0

The honest bottom line — confirm these on the appliance rather than trusting this file.

1. **No machine-readable NSX spec exists at the 9.0.0.0 tag.** Nothing in this file is
   spec-confirmed for 9.0.
2. **Policy NAT rule paths on Tier-0 and Tier-1** — recorded as *"UNVERIFIED — could not
   retrieve"* for 9.0. The Manager-API NAT path is 9.0-documented and **deprecated as of 9.0**.
3. **IPSec VPN service paths** — same. Neither the gateway-scoped nor the locale-service-scoped
   family was confirmed for 9.0, so which one your build prefers is unknown.
4. **Load balancing** — only `GET /infra/lb-services/{lb-service-id}` is 9.0-verified. No list, no
   virtual servers, no pools, no profiles, no status or usage endpoints, no Avi/ALB surface.
5. **IP blocks** (`/infra/ip-blocks…`) were not covered for 9.0; IP **pools**, allocations and
   subnets were.
6. **All body schemas** — `PolicyNatRule`, `LBService`, `LBVirtualServer`, `LBPool`,
   `IPSecVpnService`, `IPSecVpnSession`, `IpAddressPool`, `IpAddressBlock` — were read from the 9.1
   spec. None was captured from a 9.0 source. Mitigation: `GET` an existing object and mirror it.
7. **VPC-scoped and Transit-Gateway-scoped NAT, LB and VPN** — not confirmed for 9.0, and VPC L4
   LB / VPC IPSec VPN are called out as **9.1** features.
8. **`_revision`-on-create-vs-update** is verbatim only in the 9.1 guide; the 9.0 guide says only
   that `/policy` URIs *"have slightly different behavior."*
9. **403-on-session-expiry** is documented on the 9.1 page, not the 9.0 page.
10. **Whether the 9.0 LB entitlement narrowing persists** — the 9.1 support notes do not restate
    it. For 9.0 itself the narrowing **is** documented and applies.
11. **The 9.0.1 / 9.0.2 NSX build numbers** are unverified — re-check the BOM for the exact patch.
12. **No authoritative VCF-owned-vs-operator-owned NSX object list** exists for either version.

**The one call that resolves most of this:**
`GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json` — the running appliance serves
the OpenAPI document for its own build.
