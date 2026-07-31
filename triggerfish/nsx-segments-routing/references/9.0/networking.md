# NSX Logical Networking — Segments, Gateways, Fabric and Routing — VCF 9.0

**Applies to:** NSX **9.0.0.0** (build 24733065), the NSX version in the VCF 9.0 Bill of Materials.
**Do not apply this file to VCF 9.1.** Use `../9.1/networking.md` for 9.1 and `../deltas.md` for the change list.

> **Patch-line caveat.** The VCF 9.0 BOM page is maintained across the 9.0.x patch line and at time of
> research also listed VCF Installer 9.0.2.0. Separate NSX API doc sets exist for **9.0.0, 9.0.1 and
> 9.0.2**. If the target is on a 9.0.x patch, re-check the BOM — the NSX build will differ. The 9.0.1 /
> 9.0.2 build numbers are **unverified**.

---

## READ THIS FIRST — the evidence available for 9.0 is weaker than for 9.1

**There is no NSX OpenAPI specification published at the `9.0.0.0` tag of
`github.com/vmware/vcf-api-specs`.** The machine-extracted spec inventory confirms this: `nsx-policy`,
`nsx-manager` and `nsx-global-policy` are all recorded as **`9.0 present: no`**. Specs for those three
products appear only at the `9.1.0.0` tag (3,729 / 1,453 / 1,009 operations).

The consequences are concrete:

1. **Every endpoint in this file is sourced from prose documentation only** — version-pinned Broadcom
   pages under `developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/`,
   `dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.0.0/html/index.html`, and the VCF 9.0
   product docs. No 9.0 path in this file has been machine-confirmed against a specification.
2. **A path being spec-confirmed for 9.1 is not evidence about 9.0.** The 9.1 reference file marks many
   operations `[SPEC]`. Those tags mean nothing here. Where a path is known only from 9.1, it is marked
   **`[9.1-ONLY — NOT VERIFIED FOR 9.0]`** and you must confirm it on the appliance before use.
3. **The single reliable 9.0 verification route is the appliance itself:**
   `GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json`. The running NSX Manager serves
   the OpenAPI document that matches its own deployed build.

This asymmetry bites harder for logical networking than for the firewall, because the 9.0 prose
research covered networking **unevenly**: segments, Tier-0 and Tier-1 reads are solid; transport zones
and edge clusters were confirmed for the **read verb only**; BGP, locale services, gateway interfaces
and static routes were **not opened on a 9.0.0-pinned page at all**.

Evidence tags used below:

| Tag | Meaning |
|---|---|
| **[DOC-9.0]** | Read from a **9.0.0**-pinned Broadcom page. The strongest evidence available for 9.0. |
| **[DOC-9.0-partial]** | The path was seen on a 9.0.0 page but not every verb listed here was. |
| **[9.1-ONLY — NOT VERIFIED FOR 9.0]** | Known from the 9.1 doc set or 9.1 spec only. Confirm on the appliance first. |
| **[INFERRED]** | A shape or convention, not a verified fact. |

---

## Contents

- [**READ THIS FIRST** — 9.0 evidence is weaker than 9.1](#read-this-first--the-evidence-available-for-90-is-weaker-than-for-91)
- [**Prerequisites**](#prerequisites) — **read before any write**
  - [P1 — reachability and trusted chain](#p1--you-can-reach-a-specific-nsx-manager-node-over-https-with-a-trusted-chain)
  - [P2 — session works and your role is high enough](#p2--your-session-works-and-your-role-is-high-enough)
  - [P3 — site id and enforcement point id](#p3--you-know-the-site-id-and-the-enforcement-point-id)
  - [P4 — the transport zone exists](#p4--the-transport-zone-exists-and-is-the-right-type)
  - [P5 — the gateway you are attaching to exists](#p5--the-gateway-the-segment-attaches-to-exists-and-you-have-its-path)
  - [P6 — for a Tier-1: the Tier-0 exists](#p6--for-a-tier-1-the-tier-0-exists-first)
  - [P7 — for an edge cluster: transport nodes are prepared](#p7--for-an-edge-cluster-the-edge-transport-nodes-are-already-prepared)
  - [P8 — `_revision` and partial patch](#p8--you-accept-the-concurrency-and-partial-patch-contract)
  - [P9 — VCF ownership of fabric objects](#p9--vcf-ownership-of-the-objects-you-are-about-to-touch)
  - [P10 — blast radius](#p10--blast-radius--routing-and-transport-node-changes-can-sever-management-connectivity)
- [Authentication — deferred, in one paragraph](#authentication--deferred-in-one-paragraph)
- [Base path and API surface](#base-path-and-api-surface)
- [Path families](#path-families-federation-and-multi-tenancy)
- [Segments](#segments)
- [Tier-1 gateways](#tier-1-gateways)
- [Tier-0 gateways](#tier-0-gateways)
- [Locale services, interfaces, static routes and BGP](#locale-services-interfaces-static-routes-and-bgp) — **the weakest area for 9.0**
- [Transport zones](#transport-zones)
- [Transport nodes](#transport-nodes)
- [Edge clusters and edge nodes](#edge-clusters-and-edge-nodes)
- [**Worked example** — segment attached to a Tier-1](#worked-example--create-an-overlay-segment-attached-to-a-tier-1) (Steps 0–7 + [failure decode](#failure-decode-for-this-sequence))
- [Summary: what remains unverified for 9.0](#summary-what-remains-unverified-for-90)

---

## Prerequisites

Everything in this section must be true **before** you issue any networking write. Each item carries
**four** elements — if one is missing, the item is incomplete:

1. **What must be true** — the condition itself.
2. **How to verify it** — a concrete, *non-destructive* call. Never verify a permission or a contract
   by performing the production change it guards.
3. **Which version it applies to** — every item below applies to **NSX 9.0.0.0** unless it says otherwise.
4. **Whether it exists in the other version** — stated as a "9.1 difference" line on every item.

### P1 — You can reach a specific NSX Manager node over HTTPS with a trusted chain

- **Must be true:** an `https://<nsx-manager>` endpoint on 443 with its certificate chain in your trust
  store. VCF-deployed appliances default to VMCA-signed certificates, which are not publicly trusted;
  a stock HTTP client fails chain validation until you add the VMCA root or the enterprise CA. **[DOC-9.0]**
- **Verify:** `curl -sS -o /dev/null -w '%{http_code}\n' https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json`
  without `-k`. A TLS error means the trust store, not the endpoint, is the problem.
- **9.1 difference:** none known.

### P2 — Your session works and your role is high enough

- **Must be true:** **Enterprise Admin** (`enterprise_admin`) for any networking write; **Auditor**
  (`auditor`) suffices for reads. NSX 9.0 ships **15 built-in roles** including Network Admin and
  Network Operator; Enterprise Admin = *"Full access (FA) — All permissions including Create, Read,
  Update, and Delete (CRUD)"*. Custom roles are supported. **[DOC-9.0 — VCF 9.0 NSX admin guide, RBAC page]**
  Which built-in role is the minimum for a given networking endpoint is **[INFERRED]** — no matrix is published.
- **Verify — and note that a clean read-only verification is *not* spec-confirmable for 9.0.**
  There is no NSX specification at the `9.0.0.0` tag, so no 9.0 role-introspection endpoint can be
  machine-confirmed here. `GET /api/v1/aaa/role-bindings` (`GetAllRoleBindings`) is spec-confirmed for
  **9.1 only** — **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. It is very likely present in 9.0 (the RBAC role
  model is documented for 9.0), but it is not evidenced.
  **Safest documented sequence for 9.0:**
  1. Fetch the appliance's own OpenAPI document —
     `GET https://<nsx-manager>/api/v1/spec/openapi/nsx_api.json` — and search it for
     `aaa/role-bindings`. The running manager serves the spec matching its own build, so this converts
     the unverified endpoint into a verified one **for that appliance**. If present, call it and read
     your binding's role.
  2. Failing that, confirm the *session* works with a harmless read of a known object —
     `GET /policy/api/v1/infra/tier-1s/{tier-1-id}` **[DOC-9.0]** or
     `GET /policy/api/v1/infra/segments/{segment-id}`.
  3. Only if neither is available, probe write permission against a **throwaway object** — a scratch
     segment id in a lab transport zone, created and then deleted. A 403 with an authorization body
     indicates the role is too low.
  **Do not verify write permission by attempting the intended production write.** Creating the target
  segment to find out whether you may create it has already created it; creating a gateway interface
  to find out has already changed routing.
- **Service accounts:** **principal identities** are the documented 9.0 mechanism, and are what an
  X.509 client certificate binds to. They are simultaneously flagged in the VCF 9.0 support notes as
  *"planned for deprecation in an upcoming release"*, directing operators to Federated Users via VCF
  SSO. Use it, plan the migration. **[DOC-9.0]**
- **9.1 difference:** 9.1 adds a spec-confirmed token-based principal identity route
  (`/api/v1/trust-management/token-principal-identities`) that has no 9.0 equivalent and is
  deliberately not reproduced here. See the `nsx-security-policy` skill, `references/9.1/dfw.md` § A7.

### P3 — You know the site id and the enforcement point id

- **Must be true:** every fabric object — transport zone, edge cluster — lives under
  `/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/…`. This path shape
  **is** 9.0-verified: it was read on the 9.0.0-pinned transport-zone and edge-cluster method pages.
  **[DOC-9.0]** The conventional ids are `default` for both on a single-site local manager, but that is
  a **convention, not a guarantee**, and it is wrong on Federation deployments.
- **Verify (9.0):** there is **no 9.0-verified `/infra/sites` list endpoint** in the research corpus.
  `GET /policy/api/v1/infra/sites` (`ListSites`) and
  `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points` (`ListEnforcementPointForSite`) are
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. Confirm the ids indirectly instead: a 200 (rather than 404)
  from `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones/{transport-zone-id}`
  **[DOC-9.0]** proves both ids resolve. Or fetch the appliance's own OpenAPI document and search it
  for `/infra/sites`.
- **9.1 difference:** in 9.1 both list endpoints are spec-confirmed, and the deprecated
  `/infra/deployment-zones/{deployment-zone-id}/enforcement-points` tree is explicitly flagged
  `deprecated: true` in the spec. For 9.0 that deprecation flag is not evidenced — but do not use that
  tree either way.

### P4 — The transport zone exists and is the right type

- **Must be true:** a VLAN-backed segment requires a transport zone path; an overlay segment gets one
  auto-assigned only when the enforcement point has exactly one. On a deployment with more than one
  overlay TZ, pass the path.
  **Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for the exact wording and for the
  `transport_zone_type` field name — those come from the 9.1 `Segment` and `PolicyTransportZone`
  schemas. The 9.0 research captured transport-zone *paths* but not transport-zone *schemas*.
  **[INFERRED]** to be identical in 9.0.
- **Verify:** `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones/{transport-zone-id}`
  **[DOC-9.0]** returns 200. Record the `path` field from the response and use that literal string.
- **9.0 gap:** the transport-zone **list** endpoint and every write verb on transport zones were
  **not** confirmed on a 9.0.0-pinned page — only the single-zone read was.
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]** for `ListTransportZonesForEnforcementPoint`,
  `PatchTransportZoneForEnforcementPoint`, `CreateOrUpdateTransportZoneForEnforcementPoint`,
  `DeleteTransportZoneForEnforcementPoint`.
- **9.1 difference:** list, all write verbs, `/spans` and the per-TZ status/report reads are
  spec-confirmed there.

### P5 — The gateway the segment attaches to exists, and you have its path

- **Must be true:** an overlay segment attaches to a gateway by **policy path string**
  (`/infra/tier-1s/<id>`), not by name and not by UUID. A path that does not resolve is accepted at
  write time and then silently never realises.
  The field name is `connectivity_path`; **the field name and its overlay-only / VLAN-exclusion rules
  are [9.1-ONLY — NOT VERIFIED FOR 9.0]**, read from the 9.1 `Segment` schema. The 9.0 research
  captured segment *paths* but not the segment *schema*. **[INFERRED]** to be identical in 9.0 —
  and one `GET` of an existing segment settles it (see below).
- **Verify:** `GET /policy/api/v1/infra/tier-1s/{tier-1-id}` **[DOC-9.0]** (or
  `GET /policy/api/v1/infra/tier-0s/{tier-0-id}` **[DOC-9.0]**) returns 200; capture the `path` field.
- **The one call that removes most 9.0 schema uncertainty in this file:**
  `GET /policy/api/v1/infra/segments/{segment-id}` on an **existing** segment and mirror its field
  names. That is a single read and it beats every inference below.
- **9.1 difference:** the gateway **list** endpoints (`ListTier0s`, `ListTier1`) are spec-confirmed
  there; for 9.0 only the reads are evidenced.

### P6 — For a Tier-1: the Tier-0 exists first

- **Must be true:** a Tier-1 that needs north-south connectivity references a Tier-0 by path
  (`tier0_path`). Create or confirm the Tier-0 first. A Tier-1 with no Tier-0 reference is legal — the
  isolated topology — but does not route north.
- **Verify:** `GET /policy/api/v1/infra/tier-0s/{tier-0-id}` **[DOC-9.0]** for a 200; capture `path`.
- **Route advertisement is the silent failure.** In the 9.1 schema, `route_advertisement_types`
  defaults to advertising only `TIER1_IPSEC_LOCAL_ENDPOINT` when unspecified — so a Tier-1 created
  without it does not advertise its own segment subnets. **Evidence for 9.0:
  [9.1-ONLY — NOT VERIFIED FOR 9.0].** The field names and the enum
  (`TIER1_STATIC_ROUTES`, `TIER1_CONNECTED`, `TIER1_NAT`, `TIER1_LB_VIP`, `TIER1_LB_SNAT`,
  `TIER1_DNS_FORWARDER_IP`, `TIER1_IPSEC_LOCAL_ENDPOINT`) were read from the 9.1 `Tier1` schema.
  **Confirm against an existing 9.0 Tier-1 with a `GET` before relying on the default's shape.**
- **9.1 difference:** the whole `Tier1` schema is spec-confirmed there and is reproduced in
  `../9.1/networking.md`.

### P7 — For an edge cluster: the edge transport nodes are already prepared

- **Must be true:** an edge cluster is assembled from **already-deployed, already-registered edge
  transport nodes**; the cluster object does not deploy them. A Tier-1 only gets a service router —
  and therefore stateful services and a place to run NAT/LB/VPN — once a locale service under it
  carries an edge cluster reference. **[INFERRED for 9.0]**, verbatim-confirmed in the 9.1 schema.
- **Verify (9.0):**
  1. The cluster exists: `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters/{edge-cluster-id}`
     **[DOC-9.0]** — the edge-cluster **read** is the one 9.0-verified fabric read for edges.
  2. Its members: `GET …/edge-clusters/{edge-cluster-id}/edge-nodes` —
     **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. Confirm against the appliance spec first.
  3. **Not available for 9.0 in the research corpus:** any `edge-transport-nodes` list/state/status
     endpoint, `allocation/status`, or `host-transport-nodes-status`.
     **[9.1-ONLY — NOT VERIFIED FOR 9.0]** for all of them. Host transport node endpoints were
     explicitly a **negative result** in the 9.0 doc research — the category and method pages returned
     no content. If you need edge/host node state in 9.0, fetch the appliance's own OpenAPI document
     and search it for `edge-transport-nodes` and `host-transport-nodes` before scripting anything.
- **9.1 difference:** substantial. 9.1 spec-confirms edge-transport-node CRUD, state and status, the
  host-transport-node status family, `allocation/status`, the
  `relocate-and-remove-edge-transport-node` / `replace-edge-transport-node` actions, edge-cluster HA
  profiles, and the new Virtual Network Appliance clusters. **None of that is evidence about 9.0.**

### P8 — You accept the concurrency and partial-patch contract

- **`_revision`:** every REST payload carries an integer `_revision`; it must be supplied on `PUT` and
  must match, or the update is rejected. The 9.0 API Guide notes that *"APIs whose URI begins with
  /policy have slightly different behavior"* for `_revision` and `PATCH`. The precise rule — *`_revision`
  must **not** be set when `PUT` creates a new `/policy` resource, but must be supplied on subsequent
  `PUT`s* — was read verbatim in the **9.1** guide. For 9.0 it is **[INFERRED]** from the weaker 9.0
  wording. Using `PATCH` for creates sidesteps the whole question. **[DOC-9.0]** for the base statement.
- **Partial patch is off by default** and must be enabled explicitly:
  `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` with
  `{"enable_partial_patch": "true"}` **[DOC-9.0 — VCF 9.0 NSX admin guide]**. This matters more for
  networking than for firewall objects: a whole-object `PUT` on a Tier-0 that omits transit subnets or
  the HA mode re-applies defaults you did not intend.
- **Verify:** read any existing gateway — `GET /policy/api/v1/infra/tier-1s/{tier-1-id}` **[DOC-9.0]** —
  and confirm an integer `_revision` is present; that is the value a subsequent `PUT` must echo. Do not
  probe the contract with a deliberately stale `PUT`. A **`GET`** on `nsx-partial-patch-config`
  (`GetPartialPatchConfiguration`) is spec-confirmed for **9.1 only** —
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**; in 9.0, confirm the read verb exists via the appliance's own
  OpenAPI document.
- **`?force=true`:** the force variants of segment delete/patch/put are
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. Do not assume they exist in 9.0.
- **9.1 difference:** identical statements, stated verbatim rather than by implication, plus the
  spec-confirmed `GET` and the force variants.

### P9 — VCF ownership of the objects you are about to touch

- **There is no authoritative published list of which NSX objects VCF owns and which an operator may
  change directly.** This is a genuine documentation gap. It bites harder in this skill than in the
  firewall skill, because **the fabric layer is exactly where VCF's lifecycle ownership lives.** What
  *is* documented for 9.0:
  - *"Starting with NSX 9.0, a standalone NSX installation or upgrade is not supported."* NSX must
    follow the VCF Bill of Materials. **[DOC-9.0]**
  - *"VMware supports only one NSX instance for the same vCenter instance."* **[DOC-9.0]**
  - **NSX Embedded (NSXe) removed entirely** — *"NSX can no longer be installed or managed from
    vCenter."* **[DOC-9.0]**
  - **Overlay on physical servers removed** — *"NSX 9.0.0 no longer supports the deployment of NSX
    agents on physical servers."* **[DOC-9.0]** Directly relevant here: do not plan a transport-node
    design that assumes bare-metal server agents.
  - **NSX Load Balancer entitlement narrowed** — general-purpose LB removed from VCF entitlement; Avi
    recommended; NSX LB retained only for VCF infrastructure and vSphere Supervisor use cases.
    **[DOC-9.0]** Relevant to `Tier1.pool_allocation`: sizing a Tier-1 for a load balancer you are not
    entitled to run is wasted edge capacity.
  - **NSX operates in FIPS-enabled mode by default and cannot be deactivated.** **[DOC-9.0]**
  - 9.0 has **no** SDDC Manager network-sync reconciliation statement, so out-of-band NSX edits are
    **less** clearly supported in 9.0 than in 9.1.
- **Practical rule:** segments, Tier-1s and routing configuration on a Tier-0 you own are the normal
  target of direct Policy API automation. **Transport zones, host and edge transport nodes, and edge
  clusters are VCF-lifecycle-owned — prefer creating and deleting them through SDDC Manager, not
  through NSX directly.** **[INFERRED]**, not doc-stated.
- **Verify — per object, before you touch it.** `GET` the object and inspect its origin markers:
  `_system_owned`, `_protection`, `_create_user`. A `_system_owned: true`, a `_protection` other than
  `NOT_PROTECTED`, or a `_create_user` that is a VCF service account means **something else owns it —
  do not modify it**. These are fields of `PolicyConfigResource`, spec-confirmed for **9.1 only** —
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**; read the actual 9.0 response body rather than assuming the key
  names. There is **no draft/preview harness for networking objects** in either version — `/infra/drafts`
  is a firewall construct. Your rollback is the `GET` you took first.
- **9.1 difference:** 9.1 adds SDDC Manager network sync, which reconciles *"network configuration
  changes done directly in vCenter or NSX Manager"* — the closest thing to permission for out-of-band
  edits, and it does not exist in 9.0. 9.1 also allows the Management Domain to share NSX Managers
  with workload domains, so a 9.1 object may serve more than one domain; in 9.0 it does not.

### P10 — Blast radius — routing and transport node changes can sever management connectivity

Not a permission prerequisite; a *stop and think* prerequisite.

- Changing a Tier-0's HA mode, transit subnets, or uplink interfaces re-plumbs north-south forwarding.
  The 9.1 spec states verbatim that switching `ha_mode` between `ACTIVE_ACTIVE` and `ACTIVE_STANDBY`
  disables/enables inter-SR iBGP and **removes previously configured preferred edge nodes**;
  for 9.0 that side-effect text is **[9.1-ONLY — NOT VERIFIED FOR 9.0]** but the underlying behaviour
  is a property of the same datapath and should be assumed.
- Deleting or reconfiguring a **transport zone**, a **transport node**, or an **edge cluster** can
  black-hole traffic for every segment realized on it — including whatever segment carries your own
  management path to the appliance.
- **Before any of the above:** `GET` the current object and save the body, know how you would put it
  back, and prefer an out-of-band path to NSX Manager that does not traverse the overlay you are
  editing.
- **9.1 difference:** none operationally; only the documentation of the `ha_mode` side effect.

---

## Authentication — deferred, in one paragraph

Session auth is `POST /api/session/create` with form fields `j_username` and `j_password`
**[DOC-9.0]**; the response carries a `JSESSIONID` cookie and an `X-XSRF-TOKEN` header and **both**
must be sent on every subsequent call; close with `POST /api/session/destroy` **[DOC-9.0]**. Two traps
that read like permission problems: **the cookie is bound to a single manager node** so it fails behind
a VIP (*"session cookies are manager-node-specific and cannot be reused across cluster nodes"* —
**[DOC-9.0]**, verbatim from the 9.0-pinned page), and **session expiry surfaces as 403, not 401**
(that sentence is on the **9.1** page, not the 9.0 one — treat 403 as a re-auth trigger anyway;
it is harmless if 9.0 differs).

That is the whole flow at the depth this file needs. **Do not re-derive it here.** For the 1800 s
timeout, HTTP Basic, X.509 client certificates, principal identities, rate limits and pagination, read
the `nsx-security-policy` skill's `references/9.0/dfw.md` §§ A1–A6. For VCF-wide identity and SSO, use
the `vcf-foundation` skill.

The 9.0 admin guide's own worked example happens to be a networking call, which is a convenient
smoke test **[DOC-9.0]**:

```bash
curl -i -k -c session.txt -X POST \
  -d 'j_username=admin@example.com&j_password=SecretPwsd3c4d' \
  https://<nsx-manager>/api/session/create 2>&1 > response.txt

curl -k -b session.txt -H "x-xsrf-token: 5a764b19-5ad2-4727-974d-510acbc171c8" \
  https://<nsx-manager>/policy/api/v1/infra/segments
```

URL-encode the password: *"`+` and other special characters in passwords must be URL-encoded."* **[DOC-9.0]**
One path note: `/api/session/create` does **not** sit under the `/api/v1` base path.

---

## Base path and API surface

**Policy API base path: `/policy/api/v1`.** **[DOC-9.0]**

Verbatim from the VCF 9.0 NSX admin guide:

> *"Beginning with VCF 9.0, the NSX Manager interface provides a single mode, Policy mode, for
> configuring resources. The Manager mode and Manager API provided by NSX 4.x and earlier are no longer
> supported."*
>
> *"The Policy API is part of the NSX REST APIs and contains URIs that begin with /policy/api."*

Corroborated by the VCF 9.0 release-notes NSX support notes: *"VMware no longer supports the NSX Manager
APIs and NSX Advanced UIs."* **[DOC-9.0]**

**Consequence for an agent: never configure a segment, gateway, transport zone or edge cluster through
`/api/v1`.** The Manager networking API still *exists* in 9.0 — the Basic-auth example in the guide
targets `/api/v1/logical-ports` — but is unsupported for logical networking. A concrete Manager-API
networking endpoint carrying an explicit deprecation notice in the 9.0.0 doc set:
`GET /api/v1/logical-routers/{logical-router-id}/nat/rules/{rule-id}` — *"This endpoint is deprecated
as of version 9.0."* **[DOC-9.0]**

For the **fabric** specifically: the classic `/api/v1/transport-nodes`, `/api/v1/transport-node-profiles`
and `/api/v1/host-switch-profiles` trees are flagged `deprecated: true` in the **9.1** spec — that
finding is **[9.1-ONLY — NOT VERIFIED FOR 9.0]** as a formal flag. What *is* 9.0-documented is the
blanket "Manager APIs no longer supported" statement above, which covers them. **If a user has an
inherited script that builds transport nodes through `/api/v1/transport-nodes`, flag it in 9.0 too** —
just say the evidence is the product statement, not a spec deprecation flag.

`/api/v1` survives for a narrow, non-policy set **[DOC-9.0]**: session lifecycle, node/cluster admin
(`PUT /api/v1/cluster/api-service`), fabric registration, and OpenAPI spec retrieval
(`GET /api/v1/spec/openapi/nsx_policy_api.{yaml,json}`, `nsx_api.{yaml,json}`).

---

## Path families (Federation and multi-tenancy)

| Family | Template | Evidence for 9.0 |
|---|---|---|
| Local | `/policy/api/v1/infra/…` | **[DOC-9.0]** |
| Global (Federation) | `/policy/api/v1/global-infra/…` | **[DOC-9.0]** — confirmed on 9.0.0 pages for **segments under a Tier-1, Tier-0, Tier-1, transport zones and edge clusters** |
| Project (multi-tenancy) | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/…` | **[DOC-9.0]** — confirmed on 9.0.0 pages for **infra segments and Tier-1 segments and Tier-1 reads** |
| VPC | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/…` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — VPCs and Transit Gateways exist in 9.0 per the What's New, but no VPC-scoped subnet or transit-gateway API path was opened on a 9.0.0 page |

These families are **not** interchangeable: reading a project-scoped segment through `/infra/` returns 404.

**Specifically confirmed on 9.0.0-pinned pages:**
`PUT /policy/api/v1/infra/segments/{segment-id}` and
`PUT /policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/segments/{segment-id}`;
`GET /policy/api/v1/infra/tier-1s/{tier-1-id}/segments`,
`GET /policy/api/v1/global-infra/tier-1s/{tier-1-id}/segments`,
`GET /policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/tier-1s/{tier-1-id}/segments`;
`GET /policy/api/v1/infra/tier-0s/{tier-0-id}` and `GET /policy/api/v1/global-infra/tier-0s/{tier-0-id}`;
`GET /policy/api/v1/infra/tier-1s/{tier-1-id}`, `GET /policy/api/v1/global-infra/tier-1s/{tier-1-id}`,
`GET /policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/tier-1s/{tier-1-id}`;
transport zone and edge cluster reads under both `/infra/sites/…` and `/global-infra/sites/…`.
All **[DOC-9.0]**.

**The Federation read/write split is not characterised for 9.0.** In 9.1 the local manager's
`global-infra` segment and gateway objects are GET-only and writes live on the Global Manager appliance
(`basePath: /global-manager/api/v1`). That split is **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. In 9.0 the
prose shows `global-infra` **reads** only, which is consistent with the same split but is not proof of
it. If you need to write a federated segment in 9.0, target the Global Manager and confirm the base
path against that appliance's own spec.

---

## Segments

### The fixed-vs-flexible distinction, first

Two ways a segment can exist, with **different URLs**:

| | **Flexible** (infra segment) | **Fixed** (Tier-1 child segment) |
|---|---|---|
| URL | `/infra/segments/{segment-id}` **[DOC-9.0]** | `/infra/tier-1s/{tier-1-id}/segments/{segment-id}` |
| Attachment | a connectivity field in the body | the Tier-1 in the URL |
| Can be re-parented | yes | no |

**Prefer flexible.** The 9.0.0-pinned page confirms `PUT /policy/api/v1/infra/segments/{segment-id}`
**[DOC-9.0]**. Its operationId is `CreateOrReplaceInfraSegment` — and that name is **also** 9.0-verified,
because the 9.0.0 developer-portal page it was read from is literally
`…/9.0.0/method_CreateOrReplaceInfraSegment.html`. It is the one operationId in this file that is not
borrowed from the 9.1 spec.

**The listing trap applies in 9.0 too.** `GET /policy/api/v1/infra/tier-1s/{tier-1-id}/segments` was
confirmed on a 9.0.0 page **[DOC-9.0]**, and the 9.1 spec states verbatim that this endpoint returns
**fixed segments only** and that flexible segments connected to the Tier-1 must be found via the search
API. That statement was read on the 9.1 page. **[9.1-ONLY — NOT VERIFIED FOR 9.0]** as a documented
fact — but the endpoint's *shape* is identical in both, so **assume the same behaviour in 9.0** and do
not treat an empty result as "no segments attached". The 9.0 **search API path is unverified**
(`/search/query`, `/search/dsl` are 9.1-spec only), so in 9.0 the reliable route is
`GET /policy/api/v1/infra/segments` and filter client-side on the connectivity field — noting that the
*list* endpoint under `/infra/segments` is itself **[9.1-ONLY — NOT VERIFIED FOR 9.0]**; only the
per-segment `PUT` was confirmed for 9.0. Confirm both against the appliance spec.

### Endpoints

| Verb | Path (append to `/policy/api/v1`) | Evidence |
|---|---|---|
| PUT | `/infra/segments/{segment-id}` | **[DOC-9.0]** |
| PUT | `/orgs/{org-id}/projects/{project-id}/infra/segments/{segment-id}` | **[DOC-9.0]** |
| GET | `/infra/tier-1s/{tier-1-id}/segments` | **[DOC-9.0]** |
| GET | `/global-infra/tier-1s/{tier-1-id}/segments` | **[DOC-9.0]** |
| GET | `/orgs/{org-id}/projects/{project-id}/infra/tier-1s/{tier-1-id}/segments` | **[DOC-9.0]** |
| GET·PATCH·DELETE | `/infra/segments/{segment-id}` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — the 9.0 page confirmed only `PUT`. The read almost certainly exists (you cannot operate without it), but it was not evidenced on a 9.0.0 page. |
| GET | `/infra/segments` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| GET·PATCH·PUT·DELETE | `/infra/tier-1s/{tier-1-id}/segments/{segment-id}` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| any | `/infra/segments/{segment-id}/ports[/{port-id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| GET | `/infra/segments/{segment-id}/state` · `/statistics` · `/effective-profiles` · `/arp-table` · `/mac-table` · `/tep-table` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| any | `/infra/segments/{segment-id}/segment-connection-binding-maps[/{map-id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| any | `/infra/segments/service-segments[/{service-segment-id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| any | `?force=true` variants | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |

### Segment body essentials

Key fields: `display_name`, `description`, `connectivity_path` (policy path to the connecting Tier-0 or
Tier-1; overlay only — VLAN-backed segments cannot set it), `transport_zone_path` (required for
VLAN-backed segments; auto-assigned for overlay only when exactly one TZ exists), `subnets` (**max 1**,
each with `gateway_address` in **CIDR form** and optional `dhcp_ranges`), `vlan_ids`, `admin_state`
(default `UP`), `replication_mode` (default `MTEP`), `overlay_id`, `dhcp_config_path`,
`advanced_config`, `domain_name`, and a read-only `type` (`ROUTED` / `EXTENDED` /
`ROUTED_AND_EXTENDED` / `DISCONNECTED`). `address_bindings` and `ls_id` are deprecated in favour of
`SegmentPort.address_bindings` and nothing, respectively.

**Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for every field name, default and enum value above —
they were read from the 9.1 spec's `Segment` and `SegmentSubnet` definitions. The 9.0 research captured
segment *paths* but not segment *schemas*. The structure is long-standing Policy-API design and is
**[INFERRED]** to be identical in 9.0.

**Before writing a segment in 9.0, `GET` an existing segment and mirror its field names.** One call,
and it removes all of this uncertainty.

---

## Tier-1 gateways

| Verb | Path (append to `/policy/api/v1`) | Evidence |
|---|---|---|
| GET | `/infra/tier-1s/{tier-1-id}` | **[DOC-9.0]** |
| GET | `/global-infra/tier-1s/{tier-1-id}` | **[DOC-9.0]** |
| GET | `/orgs/{org-id}/projects/{project-id}/infra/tier-1s/{tier-1-id}` | **[DOC-9.0]** |
| GET | `/infra/tier-1s` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| PATCH·PUT·DELETE | `/infra/tier-1s/{tier-1-id}` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — the 9.0 page confirmed only the read verb. The write verbs almost certainly exist (a Tier-1 has to be creatable), but they were not evidenced on a 9.0.0 page. Confirm against the appliance spec. |
| GET | `/infra/tier-1s/{tier-1-id}/state` · `/advertised-networks` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| POST | `/infra/tier-1s/{tier-1-id}?action=reprocess` · `/actions/failover` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| POST | `/infra/gateways/action/reallocate` | **[9.1-ONLY]** — the 9.1 description references **VNA clusters**, which do not exist in 9.0. Treat as a 9.1 addition. |

### Tier1 body essentials

Key fields: `tier0_path`, `route_advertisement_types` (and `route_advertisement_rules`), `ha_mode`,
`failover_mode` (default `NON_PREEMPTIVE`), `enable_standby_relocation`, `pool_allocation`
(default `ROUTING`; `LB_SMALL`…`LB_XLARGE` size the edge reservation), `type`
(`ROUTED`/`ISOLATED`/`NATTED`, a label rather than an enforcement), `dhcp_config_paths`,
`disable_firewall`, `arp_limit`.

The edge cluster is **not** a `Tier1` field — it is `edge_cluster_path` on the Tier-1's locale service.

**Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for the field list, enums and defaults — read from the
9.1 `Tier1` schema. **[INFERRED]** to be identical in 9.0. `GET` an existing Tier-1 and mirror it.

---

## Tier-0 gateways

| Verb | Path (append to `/policy/api/v1`) | Evidence |
|---|---|---|
| GET | `/infra/tier-0s/{tier-0-id}` | **[DOC-9.0]** |
| GET | `/global-infra/tier-0s/{tier-0-id}` | **[DOC-9.0]** |
| GET | `/infra/tier-0s` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| PATCH·PUT·DELETE | `/infra/tier-0s/{tier-0-id}` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| GET | `/infra/tier-0s/{tier-0-id}/state` · `/routing-table` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| POST | `?action=reprocess` · `/actions/failover` · `?action=site_failover` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |

### Tier0 body essentials

Key fields: `ha_mode` (default `ACTIVE_ACTIVE`), `failover_mode`, `transit_subnets` (default
`100.64.0.0/16`), `internal_transit_subnets` (default `169.254.0.0/24` in A/A, `169.254.0.0/28` in
A/S), `vrf_config`, `stateful_services`, `disable_firewall`, `arp_limit`, `advanced_config`,
`intersite_config`. `tgw_transit_subnets` and `enable_rd_per_edge` relate to transit gateways / EVPN.

**Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for all of it, including the defaults and the
`ha_mode` side effects described in P10. **[INFERRED]** for 9.0. `GET` an existing Tier-0 and mirror it.

---

## Locale services, interfaces, static routes and BGP

**This is the weakest area of the 9.0 evidence in this file, and the area where a wrong guess does the
most damage.** The 9.0 research corpus contains **no** 9.0.0-pinned page for Tier-0 locale services,
gateway interfaces, static routes or BGP. Everything below is
**[9.1-ONLY — NOT VERIFIED FOR 9.0]** as a documented path:

```
/policy/api/v1/infra/tier-0s/{tier-0-id}/locale-services[/{locale-services-id}]
/policy/api/v1/infra/tier-0s/{tier-0-id}/locale-services/{locale-service-id}/interfaces[/{interface-id}]
/policy/api/v1/infra/tier-0s/{tier-0-id}/static-routes[/{route-id}]
/policy/api/v1/infra/tier-0s/{tier-0-id}/static-routes/bfd-peers[/{bfd-peer-id}]
/policy/api/v1/infra/tier-0s/{tier-0-id}/locale-services/{locale-service-id}/bgp
/policy/api/v1/infra/tier-0s/{tier-0-id}/locale-services/{locale-service-id}/bgp/neighbors[/{neighbor-id}]
/policy/api/v1/infra/tier-1s/{tier-1-id}/locale-services[/{locale-services-id}]
```

The structural facts — **BGP lives under the Tier-0's locale service, not on the Tier-0 itself**, and
**`edge_cluster_path` lives on the locale service, not on the gateway** — are consistent with
long-standing Policy-API design and are **[INFERRED]** for 9.0. The field-level details
(`BgpNeighborConfig` requiring `neighbor_address` and `remote_as_num`; `ha_vip_configs` being
incompatible with dynamic routing; `preferred_edge_paths` capped at two nodes for a Tier-1) are
**[9.1-ONLY — NOT VERIFIED FOR 9.0]**.

**How to work in 9.0 anyway, in order of preference:**

1. **Fetch the appliance's own OpenAPI document** — `GET /api/v1/spec/openapi/nsx_policy_api.json` —
   and search it for `locale-services`, `/bgp`, `static-routes`. This converts every path above into a
   verified one *for that appliance*. In this area it is not optional; it is the step.
2. **`GET` an existing configured Tier-0** and read its locale service and BGP config to learn the
   exact field names before writing anything.
3. Only then write, and only with P10 in mind.

**Dynamic BGP peering does not exist in 9.0.** It is a 9.1 What's New item. Do not offer it here.

---

## Transport zones

| Verb | Path (append to `/policy/api/v1`) | Evidence |
|---|---|---|
| GET | `/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones/{transport-zone-id}` | **[DOC-9.0]** |
| GET | `/global-infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones/{transport-zone-id}` | **[DOC-9.0]** |
| GET | `…/transport-zones` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| PATCH·PUT·DELETE | `…/transport-zones/{transport-zone-id}` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| GET | `…/transport-zones/{transport-zone-id}/spans`, `…/transport-zones-aggstatus`, `…/transport-zones/{zone-id}/status`, `…/transport-node-status`, `…/transport-node-status-report[-json]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |

Body fields (`transport_zone_type` `OVERLAY`/`VLAN`, the deprecating `tz_type`, `is_default`,
`nested_nsx`, `authorized_vlans`, `uplink_teaming_policy_names`, `origin_id`, `nsx_id`) are
**[9.1-ONLY — NOT VERIFIED FOR 9.0]** — read from the 9.1 `PolicyTransportZone` schema. `GET` an
existing zone and mirror it.

---

## Transport nodes

**Host transport node endpoints were a negative result in the 9.0 research** — the category page and
the method pages returned no content in either doc set at the time. Nothing about host transport nodes
in this skill is 9.0-documented.

| Area | Evidence for 9.0 |
|---|---|
| Policy `edge-transport-nodes` CRUD / state / status | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| Policy `host-transport-nodes-status` / `-aggstatus` / per-node status, tunnels, LLDP, pnic-bond | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| Policy `/infra/host-transport-node-profiles`, `/infra/host-switch-profiles` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| Policy `…/transport-node-collections` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| Manager-API `/api/v1/transport-nodes` etc. carrying a formal `deprecated: true` flag | **[9.1-ONLY]** — in 9.0 the evidence is the blanket "Manager APIs no longer supported" product statement **[DOC-9.0]**, not a spec flag |

**Practical guidance for 9.0:** transport nodes are VCF-lifecycle-owned (P9). Prepare them through
SDDC Manager. If you must read their state via API, fetch the appliance's own OpenAPI document first
and use whatever it declares — do not construct a path from the 9.1 file.

---

## Edge clusters and edge nodes

| Verb | Path (append to `/policy/api/v1`) | Evidence |
|---|---|---|
| GET | `/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters/{edge-cluster-id}` | **[DOC-9.0]** |
| GET | `/global-infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters/{edge-cluster-id}` | **[DOC-9.0]** |
| GET | `…/edge-clusters` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| PATCH·PUT·DELETE | `…/edge-clusters/{edge-cluster-id}` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| GET | `…/edge-clusters/{edge-cluster-id}/edge-nodes[/{edge-node-id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| GET | `…/edge-clusters/{edge-cluster-id}/allocation/status` · `/state` · `/status` · `/remote-tep-connectivity/…` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| POST | `…/action/relocate-and-remove-edge-transport-node` · `…/action/replace-edge-transport-node` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| any | `…/edge-cluster-high-availability-profiles[/{id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| any | `…/virtual-network-appliance-clusters[/…]` | **9.1 feature — does not exist in 9.0.** The Virtual Network Appliance is a VCF 9.1 What's New item. Do not offer it for 9.0. |

Note the direction of the gap here: 9.0 documents the edge-cluster **read**, 9.1 documents the whole
tree. The 9.0 side is not "absent", it is "unevidenced" — with the exception of the VNA, which is a
genuine 9.1 addition.

---

## Worked example — create an overlay segment attached to a Tier-1

**Goal:** a new overlay segment `app-net-01`, subnet `10.10.20.0/24`, attached to an existing Tier-1
`t1-app`, in the local (`/infra`) scope.

```bash
NSX=https://nsx-mgr.example.com
SITE=default            # verify with P3 — do NOT assume
EP=default              # verify with P3 — do NOT assume
TZ=tz-overlay-01        # verify with P4
T1=t1-app               # verify with P5/P6
SEG=app-net-01
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

`POST /api/session/create` — **[DOC-9.0]**. Pin every subsequent call to the **same manager node
address** — the 9.0-documented cookie affinity trap.

### Step 1 — Learn what this appliance actually exposes (P2, and the 9.0 tax)

```bash
curl -sS "${AUTH[@]}" "$NSX/api/v1/spec/openapi/nsx_policy_api.json" > /tmp/nsx-9.0-spec.json
jq -r '.paths | keys[]' /tmp/nsx-9.0-spec.json | grep -E 'segments|tier-1s|transport-zones|role-bindings'
```

**This step has no equivalent in the 9.1 file, and it is not optional in 9.0.** There is no published
9.0 spec, so the appliance's own document is the only authority for which of the endpoints below exist
on your build. Do it once, keep the file, grep it whenever this reference says
**[9.1-ONLY — NOT VERIFIED FOR 9.0]**.

Then read your role — if `aaa/role-bindings` appeared in the grep above:

```bash
curl -sS "${AUTH[@]}" "$NSX/api/v1/aaa/role-bindings" | jq -r '.results[] | "\(.name)\t\(.roles[].role)"'
```

**[9.1-ONLY — NOT VERIFIED FOR 9.0]** as a documented endpoint — but step 1 has just verified it for
*this appliance*, which is the point. **Do not** substitute the production write as your permission test.

### Step 2 — Confirm the site and enforcement point resolve (P3)

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/sites/$SITE/enforcement-points/$EP/transport-zones/$TZ"
```

`GET …/transport-zones/{transport-zone-id}` — **[DOC-9.0]**. A 200 proves the site id, the
enforcement point id **and** the transport zone all resolve in one call. A 404 means one of the three
is wrong, and you cannot tell which from the status code alone — narrow it by dropping path segments.

**Why not `GET /infra/sites`:** that list endpoint is not verified for 9.0 (P3). This call is.

### Step 3 — Capture the transport zone path (P4)

```bash
TZ_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/sites/$SITE/enforcement-points/$EP/transport-zones/$TZ" | jq -r '.path')

case "$TZ_PATH" in ''|null)
  echo "FATAL: transport zone '$TZ' unresolved — fix P4 before continuing" >&2; exit 1 ;;
esac
```

Capture the server-returned `path`; **do not assemble it yourself.** Global- and project-scoped
objects have longer paths, and a hand-built path is the most common cause of an object that writes
successfully and never realises.

### Step 4 — Confirm the Tier-1 exists and capture its path (P5, P6)

```bash
T1_JSON=$(curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/tier-1s/$T1")
T1_PATH=$(jq -r '.path' <<<"$T1_JSON")
T1_T0=$(jq -r '.tier0_path // empty' <<<"$T1_JSON")
T1_ADV=$(jq -r '(.route_advertisement_types // []) | join(",")' <<<"$T1_JSON")

case "$T1_PATH" in ''|null)
  echo "FATAL: Tier-1 '$T1' not found — create it before the segment (P5)" >&2; exit 1 ;;
esac
[ -n "$T1_T0" ] || echo "WARN: $T1 has no tier0_path — this segment will not route north (P6)" >&2
case "$T1_ADV" in *TIER1_CONNECTED*) ;; *)
  echo "WARN: $T1 does not advertise TIER1_CONNECTED — the new subnet will not reach the T0 (P6)" >&2 ;;
esac
```

`GET /policy/api/v1/infra/tier-1s/{tier-1-id}` — **[DOC-9.0]** for the path and verb;
**[INFERRED]** for the `tier0_path` and `route_advertisement_types` field names (P6). If those two
`jq` selectors come back empty on a Tier-1 you *know* is connected, the field names differ on your
build — read the whole body and adjust. Those two warnings cover the two failures that produce
"the segment exists and nothing can reach it".

### Step 5 — Create the segment

```bash
curl -sS -X PUT "${AUTH[@]}" "$NSX/policy/api/v1/infra/segments/$SEG" \
  -d "$(jq -n --arg t1 "$T1_PATH" --arg tz "$TZ_PATH" '{
    display_name:        "App network 01",
    description:         "Managed by automation",
    connectivity_path:   $t1,
    transport_zone_path: $tz,
    admin_state:         "UP",
    replication_mode:    "MTEP",
    subnets: [
      {
        gateway_address: "10.10.20.1/24",
        dhcp_ranges:     ["10.10.20.100-10.10.20.200"]
      }
    ]
  }')"
```

`PUT /policy/api/v1/infra/segments/{segment-id}` — **[DOC-9.0]** for the path and verb;
**[INFERRED]** for every body field name (see the Segment body note above).

Note the `jq -n --arg` construction: the body is **built from the captured `$T1_PATH` and `$TZ_PATH`**,
not from literal strings. A single-quoted `-d '{...}'` would not expand the variables at all.

Field notes:
- `PUT` is used here because it is the **verb 9.0 documentation actually confirms** for this path.
  `PATCH` almost certainly works and would avoid the `_revision` question entirely — but it is
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]** on this path, so confirm it in your step-1 spec dump before
  switching. With `PUT`, **omit `_revision` on this creating call and supply it on every subsequent
  one** (P8).
- `gateway_address` is **CIDR, not a bare IP** — the gateway's own address with a prefix length.
- `subnets` accepts at most one entry.
- **Do not** add `vlan_ids` alongside `connectivity_path` — VLAN-backed segments cannot carry a
  connectivity path.
- If step 5 returns a 400, `GET` an existing segment in the same scope and mirror its field names.
  That is the fastest resolution for every schema uncertainty in this file.

### Step 6 — Verify it took

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/segments/$SEG" | jq '{path, type, _revision}'
```

`GET /policy/api/v1/infra/segments/{segment-id}` — **[9.1-ONLY — NOT VERIFIED FOR 9.0]** as a
documented endpoint, but confirmed for your appliance by step 1. `type` coming back `ROUTED` is the
server telling you the attachment actually took; `DISCONNECTED` means `connectivity_path` did not
resolve.

There is **no 9.0-verified realization-status endpoint** — `/infra/realized-state/status`,
`…/segments/{id}/state` and `/search/query` are all **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. Check for
them in your step-1 spec dump; if absent, fall back to reading the object and testing datapath
connectivity from a workload.

### Step 7 — Log out

```bash
curl -sS -X POST "${AUTH[@]}" "$NSX/api/session/destroy"
```

**[DOC-9.0]**

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| 403 right after a successful step 0 | `X-XSRF-TOKEN` not sent. |
| 403 mid-sequence after a pause | Session expired. Treat 403 as re-auth — note the 403-on-expiry statement is 9.1-doc-verified, not 9.0-doc-verified. |
| 403 that persists after re-auth | Role too low (P2). |
| 403 only on some calls, apparently random | Cookie used against a different cluster node behind a VIP — this **is** 9.0-doc-verified. |
| 404 on step 2 | Wrong `{site-id}`, `{enforcementpoint-id}` or `{transport-zone-id}` (P3, P4). Drop path segments to narrow it. |
| 400 on step 5 | Body field name mismatch — the 9.0 schemas are inferred. `GET` an existing segment and mirror it. |
| 400 on step 5 mentioning the subnet | `gateway_address` sent as a bare IP or as the network address; it must be the gateway address in CIDR form. |
| 200 on step 5, `type` comes back `DISCONNECTED` | `connectivity_path` does not resolve — you hand-built the path instead of capturing it (P5). |
| Segment created, VMs on it cannot reach anything off-segment | Tier-1 has no Tier-0 reference, or does not advertise connected routes (P6). |
| Segment realised on some hosts only | Those hosts are not in the transport zone, or their transport nodes are unhealthy (P7) — and 9.0 gives you no documented API to check that. |
| 404 on any endpoint this file marks **[9.1-ONLY]** | Expected outcome. That is what the tag means. Check your step-1 spec dump. |
| 429 | Rate limit — 100 req/s per client per 9.0 prose. Back off. |

---

## Summary: what remains unverified for 9.0

The honest bottom line — a list of things to confirm on the appliance rather than trust here.

1. **No machine-readable NSX spec exists at the 9.0.0.0 tag** of the public corpus. Nothing in this
   file is spec-confirmed for 9.0.
2. **Every schema in this file** — `Segment`, `SegmentSubnet`, `Tier1`, `Tier0`, `LocaleServices`,
   `BgpNeighborConfig`, `PolicyTransportZone`, `PolicyEdgeCluster` — was read from the 9.1 spec. The
   9.0 research captured *paths*, not *bodies*. Mitigation: `GET` an existing object and mirror it.
3. **Segment write verbs other than `PUT`**, the `/infra/segments` **list**, every segment sub-resource
   (ports, state, statistics, binding maps, service segments) and every `?force=true` variant were not
   confirmed on a 9.0 page.
4. **Tier-0 and Tier-1 write verbs and list endpoints** were not confirmed on a 9.0 page — only the
   reads were.
5. **Locale services, gateway interfaces, static routes and BGP have no 9.0-pinned page at all** in the
   research corpus. This is the largest single gap and the one with the worst failure mode.
6. **Transport zone list and write verbs** were not confirmed for 9.0; only the read was.
7. **Edge cluster list, write verbs, member/edge-node reads, allocation status and the relocate/replace
   actions** were not confirmed for 9.0; only the read was.
8. **Host and edge transport node endpoints** were a negative result in 9.0 research — no content
   retrieved in either doc set.
9. **Realization-status endpoints** (`/infra/realized-state/…`) and the **search API**
   (`/search/query`, `/search/dsl`) were not confirmed for 9.0, despite the search API being the
   documented workaround for the fixed-vs-flexible segment listing trap.
10. **The Federation read/write split** (local `global-infra` is GET-only; writes go to the Global
    Manager appliance) was only visible in the 9.1 specs.
11. **VPC-scoped subnet and transit-gateway API paths** were not confirmed for 9.0, though VPCs and
    Transit Gateways are 9.0 features per the What's New.
12. **The 9.0.1 / 9.0.2 NSX build numbers** are unverified — re-check the BOM for the exact patch.
13. **No authoritative VCF-owned-vs-operator-owned NSX object list** exists for either version (P9).

**The one call that resolves most of this:**
`GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json` — the running appliance serves the
OpenAPI document for its own build. It is Step 1 of the worked example for exactly this reason.
