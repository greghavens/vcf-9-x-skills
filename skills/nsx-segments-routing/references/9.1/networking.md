# NSX Logical Networking — Segments, Gateways, Fabric and Routing — VCF 9.1

**Applies to:** NSX **9.1.0.0** (build 25318225), the NSX version in the VCF 9.1 Bill of Materials.
**Do not apply this file to VCF 9.0.** Use `../9.0/networking.md` for 9.0 and `../deltas.md` for the change list.

## Provenance of everything below

Two independent source classes are used, and every endpoint row is tagged with which one backs it:

| Tag | Meaning |
|---|---|
| **[SPEC]** | The exact `method + path` was found in `research/spec-inventory/9.1__nsx-policy.ops.json`, `9.1__nsx-manager.ops.json` or `9.1__nsx-global-policy.ops.json` — machine-extracted from the `9.1.0.0` tag of `github.com/vmware/vcf-api-specs` (`specifications/nsx/openapi-2.0/nsx_policy_api.yaml`, `spec_version: 9.1.0.0`, `basePath: /policy/api/v1`, 3,729 operations; `nsx_api.yaml` 1,453; `nsx_global_policy_api.yaml` 1,009, `basePath: /global-manager/api/v1`). This is the strongest evidence available. |
| **[DOC]** | Verified only from version-pinned Broadcom prose (NSX 9.1.0 developer portal, NSX 9.1.0 API Guide, VCF 9.1 NSX admin guide, VCF 9.1 What's New / product support notes). |
| **[INFERRED]** | Neither — stated as a shape or a convention, not as a verified fact. Confirm before relying on it. |

**Version-asymmetry warning.** NSX 9.1 has a published machine-readable spec; NSX 9.0 does **not**
(there is no NSX spec at the `9.0.0.0` tag of the corpus). Therefore a `[SPEC]` tag in this file is
evidence about **9.1 only** and must never be copied into the 9.0 file as verification.

---

## Contents

- [Provenance](#provenance-of-everything-below) — what `[SPEC]` / `[DOC]` / `[INFERRED]` mean
- [**Prerequisites**](#prerequisites) — **read before any write**
  - [P1 — reachability and trusted chain](#p1--you-can-reach-a-specific-nsx-manager-node-over-https-with-a-trusted-chain)
  - [P2 — session works and your role is high enough](#p2--your-session-works-and-your-role-is-high-enough)
  - [P3 — site id and enforcement point id](#p3--you-know-the-site-id-and-the-enforcement-point-id)
  - [P4 — the transport zone exists](#p4--the-transport-zone-exists-and-is-the-right-type)
  - [P5 — the gateway you are attaching to exists](#p5--the-gateway-the-segment-attaches-to-exists-and-you-have-its-path)
  - [P6 — for a Tier-1: the Tier-0 exists](#p6--for-a-tier-1-the-tier-0-exists-first)
  - [P7 — for an edge cluster: transport nodes are prepared](#p7--for-an-edge-cluster-the-edge-transport-nodes-are-already-prepared)
  - [P8 — `_revision`, partial patch, and `?force=true`](#p8--you-accept-the-concurrency-partial-patch-and-force-delete-contract)
  - [P9 — VCF ownership of fabric objects](#p9--vcf-ownership-of-the-objects-you-are-about-to-touch)
  - [P10 — blast radius: you can cut your own connectivity](#p10--blast-radius--routing-and-transport-node-changes-can-sever-management-connectivity)
- [Authentication — deferred, in one paragraph](#authentication--deferred-in-one-paragraph)
- [Base path and API surface](#base-path-and-api-surface) — Policy-only; deprecated Manager fabric tree
- [Path families](#path-families-federation-multi-tenancy-vpc)
- [Segments](#segments) — endpoints, **fixed vs flexible**, body, subnets
- [Tier-1 gateways](#tier-1-gateways)
- [Tier-0 gateways](#tier-0-gateways)
- [Locale services, interfaces and static routes](#locale-services-interfaces-and-static-routes)
- [BGP](#bgp)
- [Transport zones](#transport-zones)
- [Transport nodes](#transport-nodes-host-and-edge)
- [Edge clusters, edge nodes and VNA clusters](#edge-clusters-edge-nodes-and-vna-clusters)
- [Realization, state and troubleshooting reads](#realization-state-and-troubleshooting-reads)
- [**Worked example** — segment attached to a Tier-1](#worked-example--create-an-overlay-segment-attached-to-a-tier-1) (Steps 0–8 + [failure decode](#failure-decode-for-this-sequence))
- [What is unverified for 9.1](#what-is-unverified-for-91)

---

## Prerequisites

Everything in this section must be true **before** you issue any networking write. Each item carries
**four** elements — if one is missing, the item is incomplete:

1. **What must be true** — the condition itself.
2. **How to verify it** — a concrete, *non-destructive* call. Never verify a permission or a contract
   by performing the production change it guards.
3. **Which version it applies to** — every item below applies to **NSX 9.1.0.0** unless it says otherwise.
4. **Whether it exists in the other version** — stated as a "9.0 difference" line on every item.

### P1 — You can reach a specific NSX Manager node over HTTPS with a trusted chain

- **Must be true:** an `https://<nsx-manager>` endpoint on 443 with its certificate chain in your trust
  store. VCF-deployed appliances default to VMCA-signed certificates, which are not publicly trusted;
  a stock HTTP client fails chain validation until you add the VMCA root or the enterprise CA.
- **Verify:** `curl -sS -o /dev/null -w '%{http_code}\n' https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json`
  without `-k`. A TLS error means the trust store, not the endpoint, is the problem. **[DOC]**
- **9.0 difference:** none known.

### P2 — Your session works and your role is high enough

- **Must be true:** **Enterprise Admin** (`enterprise_admin`) for any networking write; **Auditor**
  (`auditor`) is enough for reads. Network Admin is a documented built-in role and is the narrower fit
  for this skill's object set, but the exact per-endpoint permission matrix is **[INFERRED]** — the
  9.1 doc set does not publish one. **[DOC]** for the role list.
- **Verify — read your role, do not test it by writing.**
  `GET /api/v1/aaa/role-bindings` **[SPEC — `GetAllRoleBindings`, `9.1__nsx-manager.ops.json`]**, or
  `GET /api/v1/aaa/role-bindings/{binding-id}` **[SPEC — `GetRoleBinding`]** for one known binding.
  Pair it with a harmless read such as `GET /policy/api/v1/infra/sites` **[SPEC — `ListSites`]** to
  confirm the session itself works.
  **Do not verify write permission by attempting the production write.** Creating a segment to see
  whether you are allowed to create a segment has already created the segment; creating a *gateway
  interface* to see whether you are allowed to has already changed routing. If you want a live write
  probe, use a throwaway segment id in a lab transport zone and delete it — never the target object.
- **9.0 difference:** `GET /api/v1/aaa/role-bindings` is spec-confirmed for **9.1 only**. See
  `../9.0/networking.md` P2 for the 9.0 route.

### P3 — You know the site id and the enforcement point id

- **Must be true:** every fabric object — transport zone, transport node, edge cluster, VNA cluster —
  lives under `/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/…`. The conventional
  ids are `default` for both on a single-site local manager, but that is a **convention, not a
  guarantee**, and it is wrong on Federation deployments where sites are named per location.
- **Verify:** `GET /policy/api/v1/infra/sites` **[SPEC — `ListSites`]**, then
  `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points`
  **[SPEC — `ListEnforcementPointForSite`]**. Read the `path` field out of the responses and build
  your URLs from it rather than hard-coding `default/default`.
- **Do not use** `/infra/deployment-zones/{deployment-zone-id}/enforcement-points` — every operation on
  that tree is `deprecated: true` in the 9.1 spec (`ListEnforcementPointForInfra`,
  `ReadEnforcementPointForInfra`, `PatchEnforcementPointForInfra`,
  `CreateOrUpdateEnforcementPointForInfra`, `DeleteEnforcementPoint`). **[SPEC]**
- **9.0 difference:** the site/enforcement-point path shape is 9.0-doc-verified, but `ListSites` and
  `ListEnforcementPointForSite` are spec-confirmed for **9.1 only**.

### P4 — The transport zone exists and is the right type

- **Must be true:** a **VLAN-backed** segment **requires** `transport_zone_path`. Spec text, verbatim:
  *"This field is required for VLAN backed Segments. For overlay Segments, it is auto assigned if only
  one transport zone exists in the enforcement point. Default transport zone is auto assigned for
  overlay segments if none specified."* **[SPEC — `Segment.transport_zone_path`]**
  So: on a deployment with more than one overlay TZ, "auto assigned" is not a plan — pass the path.
- **Verify:** `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones`
  **[SPEC — `ListTransportZonesForEnforcementPoint`]**, or read one directly with
  `GET …/transport-zones/{transport-zone-id}` **[SPEC — `ReadTransportZoneForEnforcementPoint`]**.
  Check `transport_zone_type` is `OVERLAY` or `VLAN` as required, and capture the `path` field.
- **9.0 difference:** the TZ **read** is 9.0-doc-verified; the **list** and the write verbs are
  spec-confirmed for 9.1 only.

### P5 — The gateway the segment attaches to exists, and you have its path

- **Must be true:** an overlay segment attaches to a gateway via `connectivity_path`, whose value is
  a **policy path string** to a Tier-0 or Tier-1 (`/infra/tier-1s/<id>`), not a name and not a UUID.
  Spec text, verbatim: *"Policy path to the connecting Tier-0 or Tier-1. Valid only for segments
  created under Infra. This field can only be used for overlay segments. VLAN backed segments cannot
  have connectivity path set."* **[SPEC — `Segment.connectivity_path`]**
  Two consequences people trip over: a VLAN segment with `connectivity_path` set is rejected, and a
  segment created under `/infra/tier-1s/{tier-1-id}/segments/…` (a *fixed* segment) does not use
  `connectivity_path` at all — the parent in the URL is the attachment.
- **Verify:** `GET /policy/api/v1/infra/tier-1s/{tier-1-id}` **[SPEC — `ReadTier1`]** (or
  `GET /policy/api/v1/infra/tier-0s/{tier-0-id}` **[SPEC — `ReadTier0`]**) returns 200, and record the
  `path` field from the response body. Use that literal string.
- **9.0 difference:** the T0 and T1 **reads** are 9.0-doc-verified. The list endpoints are 9.1-spec only.

### P6 — For a Tier-1: the Tier-0 exists first

- **Must be true:** a Tier-1 that needs north-south connectivity carries `tier0_path`, described
  verbatim as *"The reference to the Tier-0 instance using the policy path of the Tier-0 of type
  Provider."* **[SPEC — `Tier1.tier0_path`]** Create or confirm the Tier-0 first. A Tier-1 with no
  `tier0_path` is legal — it is the `ISOLATED` topology — but it will not route north.
- **Verify:** `GET /policy/api/v1/infra/tier-0s` **[SPEC — `ListTier0s`]** and
  `GET /policy/api/v1/infra/tier-0s/{tier-0-id}` **[SPEC — `ReadTier0`]** for a 200; capture `path`.
- **Also decide `route_advertisement_types` up front.** Spec, verbatim: *"When not specified, routes to
  IPSec VPN local-endpoint subnets (TIER1_IPSEC_LOCAL_ENDPOINT) are automatically advertised."*
  **[SPEC]** — i.e. the default does **not** include `TIER1_CONNECTED`, so a Tier-1 created without
  this field will not advertise its own segment subnets to the Tier-0. This is the single most common
  reason a correctly-created segment is unreachable from outside.
- **9.0 difference:** `tier0_path` and the advertisement enum come from the 9.1 spec schema; for 9.0
  they are inferred.

### P7 — For an edge cluster: the edge transport nodes are already prepared

- **Must be true:** a `PolicyEdgeCluster` is assembled from **already-deployed, already-registered edge
  transport nodes**. Its `policy_edge_nodes` member list references them; the cluster object does not
  deploy them. Similarly a Tier-1 only gets a service router — and therefore stateful services,
  standby relocation, and a place to run NAT/LB/VPN — once a `LocaleServices` child carries
  `edge_cluster_path`. Spec text, verbatim: *"Standby relocation is not enabled until edge cluster is
  configured for Tier1."* **[SPEC — `Tier1.enable_standby_relocation`]**
- **Verify, in this order:**
  1. Nodes exist and are healthy:
     `GET /policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-transport-nodes`
     **[SPEC — `ListPolicyEdgeTransportNode`]**, then
     `GET …/edge-transport-nodes/state` **[SPEC — `ListPolicyEdgeTransportNodesState`]** and
     `GET …/edge-transport-nodes/status` **[SPEC — `ListPolicyEdgeTransportNodesStatus`]**.
  2. The cluster, if it exists: `GET …/edge-clusters/{edge-cluster-id}`
     **[SPEC — `ReadEdgeClusterForEnforcementPoint`]** and its members
     `GET …/edge-clusters/{edge-cluster-id}/edge-nodes`
     **[SPEC — `ListEdgeNodesUnderEdgeClusterForEnforcementPoint`]**.
  3. Capacity before you add another gateway to it:
     `GET …/edge-clusters/{edge-cluster-id}/allocation/status`
     **[SPEC — `GetPolicyEdgeClusterAllocationStatus`]** — verbatim purpose: *"Get allocation details
     of cluster and its members."*
- **Host** transport nodes are the equivalent prerequisite for a segment to be realised on ESX. Verify
  with `GET …/host-transport-nodes-status` **[SPEC — `ListHostTNStatus`]** and
  `GET …/host-transport-nodes-aggstatus` **[SPEC — `GetAllTNsStatus`]**, and per-TZ with
  `GET /infra/sites/{site-id}/enforcement-points/{enforcement-point-id}/transport-zones/{zone-id}/transport-node-status`
  **[SPEC — `ListTNStatusForTZ`]**.
- **9.0 difference:** the edge-cluster read and the `edge-nodes` list are 9.0-doc-verified; the
  edge-transport-node CRUD tree, the state/status reads and the allocation status are 9.1-spec only.

### P8 — You accept the concurrency, partial-patch and force-delete contract

- **`_revision`:** every REST payload carries an integer `_revision`. Verbatim from the 9.1 API Guide:
  *"Clients must provide this property in PUT requests and it must match the current _revision or the
  update will be rejected."* And: *"the _revision property must **not** be set when PUT is used to
  create a new resource. Once the resource is created, however, the _revision property must be provided
  with PUT operations."* **[DOC]** `PATCH` does not require it — which is why the worked example uses
  `PATCH` for creates.
- **Partial patch is off by default:**
  `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` with `{"enable_partial_patch": "true"}`
  **[DOC — VCF 9.1 NSX admin guide]**. Read the current setting first with
  `GET /policy/api/v1/system-config/nsx-partial-patch-config`
  **[SPEC — `GetPartialPatchConfiguration`]**. This matters more for networking than for firewall
  objects: a whole-object `PUT` on a Tier-0 that omits `transit_subnets` or `ha_mode` re-applies the
  defaults, and `ha_mode` is not a field you want silently reset.
- **`?force=true` exists and is not a retry button.** `DELETE /infra/segments/{segment-id}?force=true`
  **[SPEC — `ForceDeleteInfraSegment`]**, `PATCH`/`PUT` `?force=true`
  **[SPEC — `PatchInfraSegmentWithForce`, `CreateOrReplaceInfraSegmentWithForce`]**, and
  `DELETE /infra/tier-1s/{tier-1-id}/segments/{segment-id}?force=true`
  **[SPEC — `ForceDeleteSegment`]**. Force-deleting a segment that still has attached ports removes
  the intent while leaving the realized state to be reconciled; use it only when a normal delete has
  already failed and you understand why.
- **Verify:** read any existing gateway (`GET /infra/tier-1s/{tier-1-id}` **[SPEC — `ReadTier1`]**) and
  confirm an integer `_revision` is in the body — that is the value a subsequent `PUT` must echo. Do
  not probe the contract with a deliberately stale `PUT`.
- **9.0 difference:** the same statements exist in the 9.0 doc set, but only `PATCH` on
  `nsx-partial-patch-config` is 9.0-doc-verified; the `GET` and every `?force=true` operationId here
  are 9.1-spec only.

### P9 — VCF ownership of the objects you are about to touch

- **There is no authoritative published list of which NSX objects VCF owns and which an operator may
  change directly.** This is a real gap, not an omission here. It bites harder in this skill than in
  the firewall skill, because **the fabric layer is exactly where VCF's lifecycle ownership lives.**
  What *is* documented:
  - Standalone NSX install/upgrade is not supported; NSX must follow the VCF BOM
    **[DOC — 9.0 support notes; not restated in 9.1]**.
  - In 9.1, **SDDC Manager network sync** reconciles *"network configuration changes done directly in
    vCenter or NSX Manager"* — out-of-band NSX edits are explicitly reconciled in 9.1 rather than
    purely forbidden **[DOC — VCF 9.1 What's New: NSX]**.
  - 9.1 adds *"VCF Management Domain can now share NSX Managers with other VCF workload domains"*
    **[DOC — VCF 9.1 What's New: NSX]** — so an object you change may be serving more than one domain.
- **Practical rule:** segments, Tier-1s, and routing configuration on a Tier-0 you own are the normal
  target of direct Policy API automation. **Transport zones, host transport nodes, transport node
  collections, edge transport nodes, edge clusters and NSX Manager deployment are VCF-lifecycle-owned
  — prefer creating and deleting them through SDDC Manager / VCF Operations, not through NSX
  directly.** This split is **[INFERRED]**, not doc-stated.
- **Verify — per object, before you touch it.** Read the object and inspect its origin markers:
  `_system_owned`, `_protection`, `origin_site_id`, `_create_user` on `PolicyConfigResource`
  **[SPEC]**, plus `origin_id` and `nsx_id` on `PolicyTransportZone` and `PolicyEdgeCluster`
  **[SPEC]** — a populated `origin_id` means the object was discovered from an existing NSX construct
  rather than authored through Policy. A `_system_owned: true`, or a `_protection` other than
  `NOT_PROTECTED`, or a `_create_user` that is a VCF service account, means **something else owns it —
  do not modify it**. Note this answers *"is this object system-owned"*, **not** *"is VCF entitled to
  overwrite my change"*; the latter is unanswerable from documentation. **[INFERRED]**
- **9.0 difference:** 9.0 has no network-sync reconciliation statement and no shared-NSX-Manager
  statement, so out-of-band fabric edits are less clearly supported there.

### P10 — Blast radius — routing and transport node changes can sever management connectivity

Not a permission prerequisite; a *stop and think* prerequisite, and the reason this file is longer than
it needs to be for the happy path.

- Changing `Tier0.ha_mode` from `ACTIVE_ACTIVE` to `ACTIVE_STANDBY` **disables inter-SR iBGP**;
  changing it back **enables inter-SR iBGP and removes previously configured preferred edge nodes in
  the Tier-0 locale-service.** Verbatim from the spec. **[SPEC — `Tier0.ha_mode`]** That is a
  silent destruction of `preferred_edge_paths` as a side effect of a field you thought was just a
  mode flag.
- `Tier0.transit_subnets` defaults to `100.64.0.0/16` and `internal_transit_subnets` to
  `169.254.0.0/24` (ACTIVE_ACTIVE) or `169.254.0.0/28` (ACTIVE_STANDBY) when unspecified
  **[SPEC]** — a whole-object `PUT` that omits them re-applies those defaults and renumbers the
  T0↔T1 transit links.
- Deleting or reconfiguring a **transport zone**, a **transport node**, or an **edge cluster** can
  black-hole traffic for every segment realized on it, including whatever segment carries your own
  management path to the appliance.
- **Before any of the above:** capture the current object (`GET`, save the body), know how you would
  put it back, and prefer an out-of-band access path to NSX Manager that does not traverse the
  overlay you are editing. There is no draft/publish preview for networking objects the way there is
  for DFW — `/infra/drafts` is a firewall construct. Your rollback is the `GET` you took first.
- **9.0 difference:** the same operational risk; the `ha_mode` side-effect text is 9.1-spec.

---

## Authentication — deferred, in one paragraph

Session auth is `POST /api/session/create` with form fields `j_username` and `j_password`
**[SPEC — `CreateAuthenticatedSession`]**; the response carries a `JSESSIONID` cookie and an
`X-XSRF-TOKEN` header and **both** must be sent on every subsequent call; close with
`POST /api/session/destroy` **[SPEC — `DestroyAuthenticatedSession`]**. Two traps that read like
permission problems — both are documentation facts, not spec facts, and their sources differ:
**session expiry surfaces as 403, not 401** (*"NSX Manager responds with a 403 Forbidden HTTP
response."* **[DOC — VCF 9.1 admin guide]**), and **the cookie is bound to a single manager node**
so it fails behind a VIP (**[DOC — VCF 9.0 admin guide; not restated on a 9.1-pinned page, assumed
unchanged]**).

That is the whole flow at the depth this file needs. **Do not re-derive it here.** For the timeouts,
the `cookie_based_authentication_enabled` kill switch, HTTP Basic and X.509, the token-based principal
identity route, rate limits and the unresolved spec-vs-prose limit conflict, read the
`nsx-security-policy` skill's `references/9.1/dfw.md` §§ A1–A7. For VCF-wide identity and SSO, use the
`vcf-foundation` skill.

One path note worth repeating because it is easy to get wrong: `/api/session/create` is declared as an
absolute path and does **not** sit under the `/api/v1` basePath.

---

## Base path and API surface

**Policy API base path: `/policy/api/v1`** — confirmed as the spec `basePath` in `nsx_policy_api.yaml`
at the `9.1.0.0` tag. **[SPEC]**

> *"Beginning with VCF 9.0, the NSX Manager interface provides a single mode, Policy mode, for
> configuring resources. The Manager mode and Manager API provided by NSX 4.x and earlier are no
> longer supported."* — VCF 9.1 NSX admin guide, verbatim. **[DOC]**
>
> *"The Policy API is part of the NSX REST APIs and contains URIs that begin with /policy/api."* **[DOC]**

**Consequence for an agent: never configure a segment, gateway, transport zone or edge cluster through
`/api/v1`.** The spec backs the product statement here in a way it does not for the firewall tree —
the classic Manager-API fabric endpoints are still *present* in `nsx_api.yaml` but are flagged
`deprecated: true`:

| Deprecated Manager-API path | operationIds | Evidence |
|---|---|---|
| `GET·POST /transport-nodes` | `ListTransportNodesWithDeploymentInfo`, `CreateTransportNodeWithDeploymentInfo` | **[SPEC — `deprecated: true`]** |
| `GET·PUT·DELETE /transport-nodes/{transport-node-id}` | `GetTransportNodeWithDeploymentInfo`, `UpdateTransportNodeWithDeploymentInfo`, `DeleteTransportNodeWithDeploymentInfo` | **[SPEC — `deprecated: true`]** |
| `GET·POST·PUT·DELETE /transport-node-profiles[/{id}]` | `ListTransportNodeProfiles`, `CreateTransportNodeProfile`, `GetTransportNodeProfile`, `UpdateTransportNodeProfile`, `DeleteTransportNodeProfile` | **[SPEC — `deprecated: true`]** |
| `GET·POST·PUT·DELETE /host-switch-profiles[/{id}]` | `ListHostSwitchProfiles`, `CreateHostSwitchProfile`, `GetHostSwitchProfile`, `UpdateHostSwitchProfile`, `DeleteHostSwitchProfile` | **[SPEC — `deprecated: true`]** |
| `POST /transport-nodes/{node-id}?action=redeploy` | `RedeployEdgeTransportNode` | **[SPEC — `deprecated: true`]** |

If a user has an inherited script that builds transport nodes through `/api/v1/transport-nodes`, that
is the concrete thing to flag. The Policy replacements are `/infra/host-switch-profiles`,
`/infra/host-transport-node-profiles` and the `edge-transport-nodes` tree, all listed below.

`/api/v1` survives for a narrow, non-policy set: session lifecycle, node/cluster admin
(`GET·PUT /api/v1/cluster/api-service` **[SPEC — `GetApiServiceConfig`, `UpdateApiServiceConfig`]**),
RBAC introspection (`/api/v1/aaa/role-bindings` **[SPEC]**), compute-manager and fabric registration
(`/api/v1/fabric/compute-managers` **[SPEC — `ListComputeManagers`, `AddComputeManager`]**), and
OpenAPI spec retrieval (`GET /api/v1/spec/openapi/nsx_policy_api.{json,yaml}` **[DOC]**).

---

## Path families (Federation, multi-tenancy, VPC)

Every object below exists in up to four families. They are **not** interchangeable — reading a
project-scoped segment through `/infra/` returns 404.

| Family | Template | Meaning |
|---|---|---|
| Local | `/policy/api/v1/infra/…` | The default single-tenant scope on a local NSX Manager. |
| Global (Federation) | `/policy/api/v1/global-infra/…` | Objects owned by the Global Manager. |
| Project (multi-tenancy) | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/…` | Tenant-scoped objects. |
| VPC | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/…` | VPC-scoped networking. |

Discover them rather than assuming: `GET /policy/api/v1/orgs` **[SPEC — `ListOrg`]**,
`GET /orgs/{org-id}/projects` **[SPEC — `ListProject`]**,
`GET /orgs/{org-id}/projects/{project-id}/vpcs` **[SPEC — `ListVpc`]**.

**What each family can actually do — this is where the shapes stop being symmetric:**

- **Federation, read/write split.** On the **local** manager's Policy API, the `global-infra` **segment
  and gateway objects themselves are GET-only** — `GlobalInfraReadInfraSegment`,
  `GlobalInfraListAllInfraSegments`, `GlobalInfraReadTier0`, `GlobalInfraListTier0s`,
  `GlobalInfraReadTier1`, `GlobalInfraListTier1`, `GlobalInfraListSegments` (T1 segments) all exist;
  no `PATCH`/`PUT`/`DELETE` on those paths does. **[SPEC]** Writing to a federated segment or gateway
  means talking to the **Global Manager appliance**, whose own spec
  (`9.1__nsx-global-policy.ops.json`, `basePath: /global-manager/api/v1`, 1,009 ops) carries
  `GlobalInfraCreateOrReplaceInfraSegment`, `GlobalInfraPatchInfraSegment`,
  `GlobalInfraCreateOrReplaceTier0`, `GlobalInfraCreateOrReplaceTier1` and their `DELETE`s. **[SPEC]**
- **…but the split is not clean.** Some `global-infra` *sub-objects* **do** carry write verbs on the
  local Policy API: segment **ports** (`GlobalInfraPatchInfraSegmentPort`), Tier-0 **BGP**
  (`GlobalInfraPatchBgpRoutingConfig`-family on
  `/global-infra/tier-0s/{tier-0-id}/locale-services/{locale-service-id}/bgp[/neighbors/{neighbor-id}]`),
  Tier-0 **interfaces**, and Tier-0 **static routes**. 114 non-GET `global-infra` operations exist in
  the local policy spec. **[SPEC]** Do not generalise "global-infra is read-only" — check the specific
  path.
- **Projects can own Tier-1s and segments, not Tier-0s.** Full CRUD exists at
  `/orgs/{org}/projects/{proj}/infra/tier-1s/{tier-1-id}`
  **[SPEC — `OrgsOrgIdProjectsProjectIdInfraReadTier1`, `…PatchTier1`, `…CreateOrReplaceTier1`,
  `…DeleteTier1`]** and at `…/infra/segments/{segment-id}` and
  `…/infra/tier-1s/{tier-1-id}/segments/{segment-id}`. For **Tier-0s**, the only project-scoped
  operation is `POST …/infra/tier-0s/{tier-0-id}/actions/failover`
  **[SPEC — `OrgsOrgIdProjectsProjectIdInfraTier0GatewayFailover`]** — a tenant can trigger a failover
  but cannot create or delete the provider Tier-0.
- **The fabric is not tenant-scoped at all.** There are **no** project-scoped `transport-zones` or
  `edge-clusters` paths in the 9.1 policy spec. **[SPEC — negative result]** Fabric lives only under
  `/infra/sites/…` and `/global-infra/sites/…`.
- **VPC networking is its own object model.** `GET·PATCH·PUT·DELETE
  /orgs/{org}/projects/{proj}/vpcs/{vpc-id}/subnets[/{subnet-id}]`
  **[SPEC — `ListVpcSubnet`, `GetVpcSubnet`, `PatchVpcSubnet`, `UpdateVpcSubnet`, `DeleteVpcSubnet`]**
  and `…/transit-gateways[/{transit-gateway-id}]`
  **[SPEC — `ListTransitGateway`, `ReadTransitGateway`, `PatchTransitGateway`,
  `CreateOrReplaceTransitGateway`, `DeleteTransitGateway`]**. A VPC subnet is **not** a `Segment` —
  do not reach for `/infra/segments` when the user is working inside a VPC.

---

## Segments

### The fixed-vs-flexible distinction, first, because it governs everything else

There are **two** ways a segment can exist, and they have **different URLs and different bodies**:

| | **Flexible** (infra segment) | **Fixed** (Tier-1 child segment) |
|---|---|---|
| URL | `/infra/segments/{segment-id}` | `/infra/tier-1s/{tier-1-id}/segments/{segment-id}` |
| Attachment | `connectivity_path` field in the body | the Tier-1 in the URL |
| Can be VLAN-backed | yes (and then `connectivity_path` must be **absent**) | not via `connectivity_path` |
| Can be re-parented | yes — change `connectivity_path` | no — the id is under a specific T1 |

**Prefer flexible.** It is the shape almost all current tooling and the VCF workflows produce, and it
is the only one you can move between gateways.

**The listing trap.** `GET /infra/tier-1s/{tier-1-id}/segments` does **not** return the flexible
segments attached to that Tier-1. Verbatim from the spec **[SPEC — `ListSegments`]**:

> *"Paginated list of all fixed segments (identified as
> /policy/api/v1/infra/tier-1s/&lt;tier-1-id&gt;/segments/&lt;segment-id&gt;) under Tier-1 instance. This API
> call does not return flexible segments (identified as /policy/api/v1/infra/segments/&lt;segment-id&gt;)
> connected to the Tier-1. To return all segments connected as a downlink to a Tier-1 one possibility
> is to use the search API with:
> https://{{nsx-mgr}}/policy/api/v1/search?query=resource_type:Segment%20AND%20connectivity_path:/infra/tier-1s/&lt;tier-1&gt;"*

So "list the segments on this T1" is a **two-call** question, or a search query. Note the spec's own
example writes `/policy/api/v1/search?query=…` while the operation in the inventory is
`GET /policy/api/v1/search/query` **[SPEC — `QuerySearch`]** (and `GET /search/dsl`
**[SPEC — `DslSearch`]**). Use `/search/query`; if a bare `/search` also works on your build, that is
a redirect, not a second endpoint this file can evidence.

### Endpoints

All rows **[SPEC — `9.1__nsx-policy.ops.json`]**.

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/segments` | `ListAllInfraSegments` |
| GET | `/infra/segments/{segment-id}` | `ReadInfraSegment` |
| PATCH | `/infra/segments/{segment-id}` | `PatchInfraSegment` |
| PUT | `/infra/segments/{segment-id}` | `CreateOrReplaceInfraSegment` |
| DELETE | `/infra/segments/{segment-id}` | `DeleteInfraSegment` |
| PATCH·PUT·DELETE | `/infra/segments/{segment-id}?force=true` | `PatchInfraSegmentWithForce`, `CreateOrReplaceInfraSegmentWithForce`, `ForceDeleteInfraSegment` |
| GET | `/infra/segments/{segment-id}/state` · `/statistics` | `GetInfraSegmentState`, `GetInfraSegmentStatistics` |
| GET | `/infra/segments/{segment-id}/ports` | `ListInfraSegmentPorts` |
| GET·PATCH·PUT·DELETE | `/infra/segments/{segment-id}/ports/{port-id}` | `GetInfraSegmentPort`, `PatchInfraSegmentPort`, `CreateOrReplaceInfraSegmentPort`, `DeleteInfraSegmentPort` |
| GET | `/infra/segments/{segment-id}/effective-profiles` | `ListInfraSegmentEffectiveProfiles` |
| GET | `/infra/segments/{segment-id}/arp-table` · `/mac-table` · `/tep-table` · `/arp-proxy` | `GetInfraSegmentInterfaceArpTable`, `GetInfraSegmentMacTable`, `GetInfraSegmentTepTable`, `GetDownlinkPortArpProxiesForInfraSegment` |
| GET·PATCH·PUT·DELETE | `/infra/segments/{segment-id}/dhcp-static-binding-configs/{binding-id}` | `ReadInfraSegmentDhcpStaticBinding`, `PatchInfraSegmentDhcpStaticBinding`, `CreateOrReplaceInfraSegmentDhcpStaticBinding`, `DeleteInfraSegmentDhcpStaticBinding` |
| POST | `/infra/segments/{segment-id}?action=delete_dhcp_leases` | `DeleteDhcpLease` |
| GET·PATCH·PUT·DELETE | `/infra/segments/{segment-id}/segment-connection-binding-maps/{map-id}` | `ReadInfraSegmentConnectionBindingMap`, `PatchInfraSegmentConnectionBindingMap`, `CreateOrUpdateInfraSegmentConnectionBindingMap`, `DeleteInfraSegmentConnectionBindingMap` |
| GET·PATCH·PUT·DELETE | `/infra/segments/service-segments/{service-segment-id}` | `ReadServiceSegment`, `PatchServiceSegment`, `CreateServiceSegment`, `DeleteServiceSegment` |
| GET | `/infra/tier-1s/{tier-1-id}/segments` | `ListSegments` (**fixed only** — see the trap above) |
| GET·PATCH·PUT·DELETE | `/infra/tier-1s/{tier-1-id}/segments/{segment-id}` | `ReadSegment`, `PatchSegment`, `CreateOrReplaceSegment`, `DeleteSegment` |
| GET | `/global-infra/segments[/{segment-id}]` | `GlobalInfraListAllInfraSegments`, `GlobalInfraReadInfraSegment` (**read-only on the local manager**) |
| GET·PATCH·PUT·DELETE | `/orgs/{org}/projects/{proj}/infra/segments/{segment-id}` | `OrgsOrgIdProjectsProjectIdInfraReadInfraSegment`, `…PatchInfraSegment`, `…CreateOrReplaceInfraSegment`, `…DeleteInfraSegment` |
| GET·PATCH·PUT·DELETE | `/orgs/{org}/projects/{proj}/infra/tier-1s/{tier-1-id}/segments/{segment-id}` | `OrgsOrgIdProjectsProjectIdInfraReadSegment`, `…PatchSegment`, `…CreateOrReplaceSegment`, `…DeleteSegment` |

A spec quirk worth knowing so you do not think you have the wrong path: the state and statistics
operations are declared with the path parameter spelled `{segments-id}`
(`/infra/segments/{segments-id}/state`), not `{segment-id}`. It is the same resource; the URL you send
is identical. **[SPEC]**

### Segment body essentials

`Segment` extends `PolicyConfigResource`. Fields that matter for creating one **[SPEC]**:

| Field | Type | Notes |
|---|---|---|
| `connectivity_path` | string | Policy path to the connecting Tier-0 or Tier-1. **Overlay only; VLAN-backed segments cannot set it.** Valid only for segments created under Infra. |
| `transport_zone_path` | string | **Required for VLAN-backed segments.** Auto-assigned for overlay only when exactly one TZ exists on the enforcement point. |
| `subnets` | array of `SegmentSubnet` | *"Subnet configuration. Max 1 subnet"* — verbatim. One subnet per segment. |
| `vlan_ids` | array of string | VLAN-backed segments. *"Can be a VLAN id or a range of VLAN ids specified with '-' in between."* |
| `admin_state` | enum, default `UP` | `UP` / `DOWN`. *"It does not reflect the state of other logical entities connected/attached to the segment."* |
| `replication_mode` | enum, default `MTEP` | `MTEP` / `SOURCE`. Overlay only. |
| `overlay_id` | int32 | Auto-allocated from the enforcement point's default pool if omitted. |
| `dhcp_config_path` | string | Path to a DHCP server or relay config, applied to all subnets. |
| `advanced_config` | `SegmentAdvancedConfig` | Connectivity, hybrid, urpf, local-egress, etc. |
| `type` | enum, **readOnly** | `ROUTED` / `EXTENDED` / `ROUTED_AND_EXTENDED` / `DISCONNECTED` — the realized answer, not an input. |
| `domain_name` | string | DNS domain name. |
| `metadata_proxy_paths`, `bridge_profiles`, `l2_extension`, `extra_configs`, `federation_config` | — | See the spec. |
| `address_bindings` | array | **`x-deprecated: true`** — *"Please use address_bindings in SegmentPort to configure static bindings."* |
| `ls_id` | string | **`x-deprecated: true`** — *"The segments that are newly created with ls_id will be ignored."* |

`SegmentSubnet` **[SPEC]**:

| Field | Notes |
|---|---|
| `gateway_address` | *"Gateway IP address in CIDR format for both IPv4 and IPv6."* This is the gateway IP **with prefix**, e.g. `10.10.20.1/24` — not a bare address, and not the network address. |
| `dhcp_ranges` | Array of IP element strings: single address, range (`a-b`) or CIDR. *"First valid host address from the first value is assigned to DHCP server IP address. Existing values cannot be deleted or modified, but additional DHCP ranges can be added."* |
| `dhcp_config` | `SegmentDhcpConfig`. |
| `network` | **readOnly** — computed CIDR. |

The `gateway_address`-is-CIDR detail is the most common 400 on a first segment create.

---

## Tier-1 gateways

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/tier-1s` | `ListTier1` |
| GET | `/infra/tier-1s/{tier-1-id}` | `ReadTier1` |
| PATCH | `/infra/tier-1s/{tier-1-id}` | `PatchTier1` |
| PUT | `/infra/tier-1s/{tier-1-id}` | `CreateOrReplaceTier1` |
| DELETE | `/infra/tier-1s/{tier-1-id}` | `DeleteTier1` |
| GET | `/infra/tier-1s/{tier-1-id}/state` | `GetTier1State` |
| GET | `/infra/tier-1s/{tier-1-id}/advertised-networks` (`/csv`) | `GetTier1AdvertisedNetworks`, `GetTier1AdvertisedNetworksInCsvFormat` |
| POST | `/infra/tier-1s/{tier-1-id}?action=reprocess` | `Tier1GatewayReprocess` |
| POST | `/infra/tier-1s/{tier-1-id}/actions/failover` | `Tier1GatewayFailover` |
| GET | `/infra/tier-1s/{tier-1-id}/locale-services` | `ListTier1LocaleServices` |
| GET·PATCH·PUT·DELETE | `/infra/tier-1s/{tier-1-id}/locale-services/{locale-services-id}` | see the locale-services section |
| POST | `/infra/gateways/action/reallocate` | `GatewayReallocation` — *"Reallocate or re-balance service instances of gateways within edge or VNA clusters"* |
| GET | `/global-infra/tier-1s[/{tier-1-id}]` | `GlobalInfraListTier1`, `GlobalInfraReadTier1` (read-only locally) |
| GET·PATCH·PUT·DELETE | `/orgs/{org}/projects/{proj}/infra/tier-1s[/{tier-1-id}]` | `OrgsOrgIdProjectsProjectIdInfraListTier1`, `…ReadTier1`, `…PatchTier1`, `…CreateOrReplaceTier1`, `…DeleteTier1` |
| POST | `/orgs/{org}/projects/{proj}/infra/gateways/action/reallocate` | `OrgsOrgIdProjectsProjectIdInfraGatewayReallocation` |

All **[SPEC]**.

### Tier1 body essentials **[SPEC]**

| Field | Type / default | Notes |
|---|---|---|
| `tier0_path` | string | *"The reference to the Tier-0 instance using the policy path of the Tier-0 of type Provider."* Omit for an isolated T1. |
| `route_advertisement_types` | array enum | `TIER1_STATIC_ROUTES`, `TIER1_CONNECTED`, `TIER1_NAT`, `TIER1_LB_VIP`, `TIER1_LB_SNAT`, `TIER1_DNS_FORWARDER_IP`, `TIER1_IPSEC_LOCAL_ENDPOINT`. **Default when unspecified advertises only `TIER1_IPSEC_LOCAL_ENDPOINT`** — you almost always want `TIER1_CONNECTED` here. |
| `route_advertisement_rules` | array | Per-prefix allow/deny on top of the types. |
| `ha_mode` | enum | `ACTIVE_STANDBY` / `ACTIVE_ACTIVE`. |
| `failover_mode` | enum, default `NON_PREEMPTIVE` | `PREEMPTIVE` / `NON_PREEMPTIVE`. |
| `enable_standby_relocation` | boolean, default `false` | *"Standby relocation is not enabled until edge cluster is configured for Tier1."* |
| `pool_allocation` | enum, default `ROUTING` | `ROUTING`, `LB_SMALL`, `LB_MEDIUM`, `LB_LARGE`, `LB_XLARGE`. Sizes the edge resource reservation — set it before you put a load balancer on the gateway, not after. |
| `type` | enum | `ROUTED` / `ISOLATED` / `NATTED`. *"Property value is not validated with Tier1 configuration"* — it is a label for humans, not an enforcement. |
| `dhcp_config_paths` | array of string | |
| `disable_firewall`, `default_rule_logging`, `force_whitelisting`, `arp_limit`, `qos_profile`, `intersite_config`, `federation_config` | — | |

The edge cluster is **not** a field on `Tier1`. It is `edge_cluster_path` on the Tier-1's
`LocaleServices` child — see below. This is the structural thing people get wrong.

---

## Tier-0 gateways

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/tier-0s` | `ListTier0s` |
| GET | `/infra/tier-0s/{tier-0-id}` | `ReadTier0` |
| PATCH | `/infra/tier-0s/{tier-0-id}` | `PatchTier0` |
| PUT | `/infra/tier-0s/{tier-0-id}` | `CreateOrReplaceTier0` |
| DELETE | `/infra/tier-0s/{tier-0-id}` | `DeleteTier0` |
| GET | `/infra/tier-0s/{tier-0-id}/state` | `GetTier0State` |
| POST | `/infra/tier-0s/{tier-0-id}?action=reprocess` | `Tier0GatewayReprocess` — *"Reprocess Tier0 gateway configuration and publish updates to NSX controller"* |
| POST | `/infra/tier-0s/{tier-0-id}/actions/failover` | `Tier0GatewayFailover` |
| POST | `/infra/tier-0s?action=site_failover` | `GatewaySiteFailoverAction` (Federation) |
| GET | `/global-infra/tier-0s[/{tier-0-id}]` | `GlobalInfraListTier0s`, `GlobalInfraReadTier0` (read-only locally) |
| GET | `/global-infra/tier-0s/{tier-0-id}/routing-table` (`?format=csv`) | `GlobalInfraGetTier0Routes`, `GlobalInfraGetTier0RoutesCsv` |

All **[SPEC]**.

### Tier0 body essentials **[SPEC]**

| Field | Default | Notes |
|---|---|---|
| `ha_mode` | `ACTIVE_ACTIVE` | `ACTIVE_ACTIVE` / `ACTIVE_STANDBY`. **See P10** — switching modes disables/enables inter-SR iBGP and can clear `preferred_edge_paths`. |
| `failover_mode` | — | `PREEMPTIVE` / `NON_PREEMPTIVE`. |
| `transit_subnets` | `100.64.0.0/16` | T0↔T1 transit links. Sizing note in the spec: for stateful active-active T0, *"number of IPs should be at least attached Tier-1s count * 16."* |
| `internal_transit_subnets` | `169.254.0.0/24` (A/A) or `169.254.0.0/28` (A/S) | SR↔DR links, IPv4 only, `maxItems: 1`. |
| `tgw_transit_subnets` | `169.254.4.0/22` | Links to a transit gateway, `maxItems: 1`. |
| `vrf_config`, `vrf_transit_subnets`, `enable_rd_per_edge`, `rd_admin_field`, `multi_vrf_inter_sr_routing` | — | VRF-lite / EVPN. |
| `stateful_services`, `disable_firewall`, `default_rule_logging`, `force_whitelisting`, `arp_limit`, `dhcp_config_paths`, `advanced_config`, `intersite_config`, `federation_config` | — | |

---

## Locale services, interfaces and static routes

**A gateway with no locale service has no service router**, and therefore no uplinks, no BGP, and no
edge placement. This is the layer that binds a gateway to an edge cluster.

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/tier-0s/{tier-0-id}/locale-services` | `ListTier0LocaleServices` |
| GET·PATCH·PUT·DELETE | `/infra/tier-0s/{tier-0-id}/locale-services/{locale-services-id}` | `ReadTier0LocaleServices`, `PatchTier0LocaleServices`, `CreateOrReplaceTier0LocaleServices`, `DeleteTier0LocaleServices` |
| GET | `/infra/tier-0s/{tier-0-id}/locale-services/{locale-service-id}/interfaces` | `ListTier0Interfaces` |
| GET·PATCH·PUT·DELETE | `…/interfaces/{interface-id}` | `ReadTier0Interface`, `PatchTier0Interface`, `CreateOrReplaceTier0Interface`, `DeleteTier0Interface` |
| GET | `…/interfaces/{interface-id}/statistics` · `/statistics/summary` · `/arp-table` · `/arp-proxy` · `/dad-state` | `GetTier0InterfaceStatistics`, `GetTier0InterfaceStatisticsSummary`, `GetTier0InterfaceArpTable`, `GetTier0InterfaceArpProxies`, `GetTier0InterfaceDADState` |
| GET | `/infra/tier-0s/{tier-0-id}/static-routes` | `ListTier0StaticRoutes` |
| GET·PATCH·PUT·DELETE | `/infra/tier-0s/{tier-0-id}/static-routes/{route-id}` | `ReadTier0StaticRoutes`, `PatchTier0StaticRoutes`, `CreateOrReplaceTier0StaticRoutes`, `DeleteTier0StaticRoutes` |
| GET·PATCH·PUT·DELETE | `/infra/tier-0s/{tier-0-id}/static-routes/bfd-peers/{bfd-peer-id}` | `ReadStaticRouteBfdPeer`, `PatchStaticRouteBfdPeer`, `UpdateStaticRouteBfdPeer`, `DeleteStaticRouteBfdPeer` |
| GET | `/infra/tier-1s/{tier-1-id}/locale-services` | `ListTier1LocaleServices` |
| GET·PATCH·PUT·DELETE | `/infra/tier-1s/{tier-1-id}/locale-services/{locale-services-id}` | `ReadTier1LocaleServices`, `PatchTier1LocaleServices`, `CreateOrReplaceTier1LocaleServices`, `DeleteTier1LocaleServices` |
| GET·PATCH·PUT·DELETE | `/orgs/{org}/projects/{proj}/infra/tier-1s/{tier-1-id}/locale-services/{locale-services-id}` | `OrgsOrgIdProjectsProjectIdInfraReadTier1LocaleServices`, `…DeleteTier1LocaleServices`, … |

All **[SPEC]**.

### LocaleServices body essentials **[SPEC]**

| Field | Notes |
|---|---|
| `edge_cluster_path` | *"The reference to the edge cluster using the policy path of the edge cluster of type PolicyEdgeCluster. Auto assigned on Tier0 if the associated enforcement point has only one edge cluster."* Note "auto assigned on **Tier0**" — do not assume the same for a Tier-1. |
| `preferred_edge_paths` | *"Policy paths to edge nodes. For Tier1 gateway, the field is used to statically assign the ordered list of up to two edge nodes…"* |
| `ha_vip_configs` | Active-Standby Tier-0 only, pairs exactly two external interfaces. **Verbatim: *"When this property is configured, configuration of dynamic-routing is not allowed."*** — i.e. HA VIP and BGP on the same interface pair are mutually exclusive. |
| `route_redistribution_config`, `route_redistribution_types` | Tier-0 only. |
| `bfd_profile_path` | Applies to all static route peers in the locale; a per-peer BFD profile takes precedence. |

`Tier0Interface` fields **[SPEC]**: `segment_path`, `edge_path`, `edge_cluster_member_index`, `mtu`,
`type`, `admin_state`, `access_vlan_id`, `urpf_mode`, `multicast`, `ospf`, `igmp_local_join_groups`,
`proxy_arp_filters`, `ls_id`. An external uplink interface needs `segment_path` pointing at a
**VLAN-backed** segment and `edge_path` (or `edge_cluster_member_index`) pinning it to a node.

---

## BGP

BGP lives **under the Tier-0's locale service**, not on the Tier-0 itself.

| Verb | Path (append to `/policy/api/v1/infra/tier-0s/{tier-0-id}/locale-services/{locale-service-id}`) | operationId |
|---|---|---|
| GET·PATCH·PUT·DELETE | `/bgp` | `ReadBgpRoutingConfig`, `PatchBgpRoutingConfig`, `CreateOrReplaceBgpRoutingConfig`, `DeleteOverriddenBgpRoutingConfig` |
| GET | `/bgp/neighbors` | `ListBgpNeighborConfigs` |
| GET·PATCH·PUT·DELETE | `/bgp/neighbors/{neighbor-id}` | `ReadBgpNeighborConfig`, `PatchBgpNeighborConfig`, `CreateOrReplaceBgpNeighborConfig`, `DeleteBgpNeighborConfig` |
| GET | `/bgp/neighbors/status` | `GetTier0BgpNeighborsStatus` |
| GET | `/bgp/neighbors/{neighbor-id}/routes` (`?format=csv`) | `GetTier0BgpNeighborRoutes`, `GetTier0BgpNeighborRoutesInCsvFormat` |
| GET | `/bgp/neighbors/{neighbor-id}/advertised-routes` (`?format=csv`) | `GetTier0BgpNeighborAdvertisedRoutes`, `GetTier0BgpNeighborAdvertisedRoutesInCsvFormat` |
| GET·PATCH·PUT | `/bgp/troubleshoot` | `ReadBgpTroubleshootConfig`, `PatchBgpTroubleshootConfig`, `CreateOrReplaceBgpTroubleshootConfig` |

All **[SPEC]**. A parallel **route-controller** tree exists at
`/infra/route-controllers/{router-controller-id}/bgp[/neighbors/{neighbor-id}]`
**[SPEC — `ReadControllerBgpRoutingConfig`, `PatchControllerBgpRoutingConfig`,
`CreateOrReplaceControllerBgpRoutingConfig`, `DeleteControllerBgpRoutingConfig`,
`ListControllerBgpNeighborConfig`, `ReadControllerBgpNeighborConfig`, `PatchControllerBgpNeighborConfig`,
`CreateOrReplaceControllerBgpNeighborConfig`, `DeleteControllerBgpNeighborConfig`]**, with the same
status and route reads. Do not mix the two trees for the same peering.

Bodies **[SPEC]**:

- `BgpRoutingConfig`: `enabled`, `local_as_num`, `ecmp`, `multipath_relax`, `inter_sr_ibgp`,
  `ebgp_admin_distance`, `ibgp_admin_distance`, `graceful_restart_config`, `route_aggregations`.
- `BgpNeighborConfig`: **required — `neighbor_address` and `remote_as_num`**. Optional: `source_addresses`,
  `password`, `hold_down_time`, `keep_alive_time`, `maximum_hop_limit`, `allow_as_in`,
  `graceful_restart_mode`, `bfd`, `route_filtering`, `in_route_filters`, `out_route_filters`,
  `neighbor_local_as_config`, `enabled`.

**Dynamic BGP peering — the 9.1 feature, and an honest gap.** The VCF 9.1 What's New says you can
*"define a range of IP addresses that will be used to determine when a Tier-0 gateway should establish
BGP peering."* **[DOC]** The **configuration surface for it could not be located in the 9.1 policy
spec.** `BgpNeighborConfig` still requires a single `neighbor_address` and exposes no range/prefix
field, and there is no `dynamic-neighbors`, `neighbor-groups` or `peer-group` path. The only trace is
a **read-only** field `neighbor_path`, described as *"Policy intent path of dynamic bgp neighbor"*, on
the status schemas `PolicyBgpNeighborStatus` and `RouteControllerBgpNeighborStatus`. **[SPEC]**
So: the feature is documented, dynamically-learned neighbors are observable in status output, and the
**write API for it is UNVERIFIED**. Confirm against the appliance's own spec before scripting it.

---

## Transport zones

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones` | `ListTransportZonesForEnforcementPoint` |
| GET | `…/transport-zones/{transport-zone-id}` | `ReadTransportZoneForEnforcementPoint` |
| PATCH | `…/transport-zones/{transport-zone-id}` | `PatchTransportZoneForEnforcementPoint` |
| PUT | `…/transport-zones/{transport-zone-id}` | `CreateOrUpdateTransportZoneForEnforcementPoint` |
| DELETE | `…/transport-zones/{transport-zone-id}` | `DeleteTransportZoneForEnforcementPoint` |
| GET | `…/transport-zones/{transport-zone-id}/spans` | `GetAllNetworkSpansByTz` |
| GET | `/infra/sites/{site-id}/enforcement-points/{enforcement-point-id}/transport-zones-aggstatus` | `GetAllTZStatus` |
| GET | `…/transport-zones/{zone-id}/status` | `GetHeatmapTZStatus` |
| GET | `…/transport-zones/{zone-id}/transport-node-status` | `ListTNStatusForTZ` |
| GET | `…/transport-zones/{zone-id}/transport-node-status-report` · `-json` | `GetTNReportForATZ`, `GetTNJsonReportForATZ` |
| GET | `/global-infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones[/{transport-zone-id}]` | `GlobalInfraListTransportZonesForEnforcementPoint`, `GlobalInfraReadTransportZoneForEnforcementPoint` |

All **[SPEC]**. Note the spec is inconsistent about the enforcement-point path parameter name —
`{enforcementpoint-id}` on the CRUD operations, `{enforcement-point-id}` on the status ones. Same
value; only the declaration differs.

`PolicyTransportZone` body **[SPEC]**: `transport_zone_type` (enum `OVERLAY` / `VLAN` — **use this
one**), `tz_type` (enum `OVERLAY_STANDARD`, `OVERLAY_ENS`, `VLAN_BACKED`, `OVERLAY_BACKED`, `UNKNOWN`
— the spec says `OVERLAY_STANDARD`, `OVERLAY_ENS` and `UNKNOWN` are **deprecated**, and that
`transport_zone_type` populates `tz_type` when the latter is null: `OVERLAY → OVERLAY_BACKED`,
`VLAN → VLAN_BACKED`), `is_default`, `nested_nsx`, `authorized_vlans`,
`uplink_teaming_policy_names`, `transport_zone_profile_paths`, `origin_id`, `nsx_id`.

---

## Transport nodes (host and edge)

Policy-API surface. Remember P9: these are the objects most likely to be VCF-owned.

**Edge transport nodes** — full CRUD, **[SPEC]**:

| Verb | Path (append to `/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}`) | operationId |
|---|---|---|
| GET | `/edge-transport-nodes` | `ListPolicyEdgeTransportNode` |
| GET | `/edge-transport-nodes/{edge-transport-node-id}` | `GetPolicyEdgeTransportNode` |
| PATCH | `/edge-transport-nodes/{edge-transport-node-id}` | `PatchPolicyEdgeTransportNode` |
| PUT | `/edge-transport-nodes/{edge-transport-node-id}` | `CreateOrUpdatePolicyEdgeTransportNode` |
| DELETE | `/edge-transport-nodes/{edge-transport-node-id}` | `DeletePolicyEdgeTransportNode` |
| GET | `/edge-transport-nodes/state` · `/status` | `ListPolicyEdgeTransportNodesState`, `ListPolicyEdgeTransportNodesStatus` |
| POST | `/edge-transport-nodes/{edge-transport-node-id}/action/sync-edge-configuration` | `SyncPolicyEdgeTransportNode` |
| GET | `/edge-transport-nodes/{node-id}/tunnels[/{tunnel-name}]` | `GetEdgeTunnels`, `GetEdgeTunnelByName` |
| GET | `/edge-transport-nodes/{node-id}/lldp/interfaces[/{interface-name}]` | `ListAllEdgeLldpNeighborInterfaces`, `ShowEdgeLldpNeighborInterfaces` |
| GET·PATCH | `/edge-transport-nodes/troubleshoot/datapath` | `GetPolicyEdgeTransportNodesTroubleshootConfig`, `PatchPolicyEdgeTransportNodesTroubleshootConfig` |

**Host transport nodes** — the Policy surface is **status and binding, not CRUD**, **[SPEC]**:

| Verb | Path | operationId |
|---|---|---|
| GET | `…/host-transport-nodes-status` · `-aggstatus` | `ListHostTNStatus`, `GetAllTNsStatus` |
| GET | `…/host-transport-nodes/{node-id}/status` | `GetHostTNStatus` |
| GET | `…/host-transport-nodes/{node-id}/tunnels[/{tunnel-name}]` | `GetTunnels`, `GetTunnelByName` |
| GET | `…/host-transport-nodes/{node-id}/pnic-bond-status` | `GetPnicStatusesForTN` |
| GET | `…/host-transport-nodes/{node-id}/lldp/interfaces[/{interface-name}]` | `ListAllLldpNeighborInterfaces`, `ShowLldpNeighborInterfaces` |
| GET | `…/host-transport-nodes/{node-id}/remote-transport-node-status` · `/hyperbus-status` · `/node-agent-status` | `ListRemoteTNStatus`, `GetTnHyperbusStatus`, `GetTnContainerAgentStatus` |
| GET·PATCH·PUT·DELETE | `…/host-transport-nodes/{host-transport-node-id}/transport-node-monitoring-profile-binding-maps/{binding-map-id}` | `GetTransportNodeMonitoringProfileBindingMap`, `PatchTransportNodeMonitoringProfileBindingMap`, `CreateOrUpdateTransportNodeMonitoringProfileBindingMap`, `DeleteTransportNodeMonitoringProfileBindingMap` |
| GET·DELETE | `…/transport-node-collections[/{transport-node-collection-id}]` | `ListHostTransportNodeCollections`, `DeleteHostTransportNodeCollection` |

**Profiles**, under `/infra` rather than under a site **[SPEC]**:

| Verb | Path | operationId |
|---|---|---|
| GET | `/infra/host-transport-node-profiles` | `ListPolicyHostTransportNodeProfiles` |
| GET | `/infra/host-transport-node-profiles/{host-transport-node-profile-id}` | `GetPolicyHostTransportNodeProfile` |
| PUT·DELETE | `/infra/host-transport-node-profiles/{transport-node-profile-id}` | `CreateOrUpdatePolicyHostTransportNodeProfile`, `DeletePolicyHostTransportNodeProfile` |
| GET·PATCH·PUT·DELETE | `/infra/host-switch-profiles[/{host-switch-profile-id}]` | `ListPolicyHostSwitchProfiles`, `GetPolicyHostSwitchProfile`, `PatchPolicyHostSwitchProfile`, `CreateOrUpdatePolicyHostSwitchProfile`, `DeletePolicyHostSwitchProfile` |

Note the asymmetry: `host-transport-node-profiles` has **no `PATCH`** in the spec, and the two path
parameter spellings differ between the read (`{host-transport-node-profile-id}`) and the write
(`{transport-node-profile-id}`) declarations. Same resource. **[SPEC]**

---

## Edge clusters, edge nodes and VNA clusters

All under `/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}`. All **[SPEC]**.

| Verb | Path | operationId |
|---|---|---|
| GET | `/edge-clusters` | `ListEdgeClustersForEnforcementPoint` |
| GET | `/edge-clusters/{edge-cluster-id}` | `ReadEdgeClusterForEnforcementPoint` |
| PATCH | `/edge-clusters/{edge-cluster-id}` | `PatchPolicyEdgeCluster` |
| PUT | `/edge-clusters/{edge-cluster-id}` | `CreateOrUpdatePolicyEdgeCluster` — *"Create Or Update a Policy Edge Cluster."* |
| DELETE | `/edge-clusters/{edge-cluster-id}` | `DeletePolicyEdgeCluster` |
| GET | `/edge-clusters/{edge-cluster-id}/edge-nodes[/{edge-node-id}]` | `ListEdgeNodesUnderEdgeClusterForEnforcementPoint`, `ReadEdgeNodeUnderEdgeClusterForEnforcementPoint` |
| GET | `/edge-clusters/{edge-cluster-id}/allocation/status` | `GetPolicyEdgeClusterAllocationStatus` |
| GET | `/edge-clusters/{edge-cluster-id}/status` | `GetPolicyEdgeClusterStatus` |
| POST | `/edge-clusters/{edge-cluster-id}/action/relocate-and-remove-edge-transport-node` | `RelocateAndRemovePolicyEdgeNode` — *"Relocate service contexts from policy edge node and remove it."* |
| POST | `/edge-clusters/{edge-cluster-id}/action/replace-edge-transport-node` | `ReplacePolicyEdgeNode` — *"Replace the policy edge node at specified member-index."* |
| GET | `/edge-clusters/{edge-cluster-id}/remote-tep-connectivity/status` · `/remote-tep-connectivity/bgp/summary` | `ReadPolicyEdgeClusterRemoteTunnelConnectivityStatus`, `ReadPolicyEdgeClusterRemoteTunnelConnectivityBgpSummaryStatus` |
| GET | `/edge-clusters/{edge-cluster-id}/edge-nodes/{policy-edge-node-id}/remote-tep-connectivity/bgp/neighbors[/{neighbor-id}/routes\|/advertised-routes]` | `ListPolicyEdgeNodeBgpNeighbors`, `GetPolicyEdgeNodeBgpNeighborRoutes`, `GetPolicyEdgeNodeBgpNeighborAdvertisedRoutes` |
| GET·PATCH·PUT·DELETE | `/edge-cluster-high-availability-profiles[/{edge-cluster-high-availability-profile-id}]` | `ListPolicyEdgeClusterHighAvailabilityProfile`, `ReadPolicyEdgeClusterHighAvailabilityProfile`, `PatchPolicyEdgeClusterHighAvailabilityProfile`, `CreateOrUpdatePolicyEdgeClusterHighAvailabilityProfile`, `DeletePolicyEdgeClusterHighAvailabilityProfile` |
| GET·PATCH·PUT·DELETE | `/virtual-network-appliance-clusters[/{virtual-network-appliance-cluster-id}]` | `ListVirtualNetworkApplianceClusters`, `ReadVirtualNetworkApplianceCluster`, `PatchVirtualNetworkApplianceCluster`, `CreateOrUpdateVirtualNetworkApplianceCluster`, `DeleteVirtualNetworkApplianceCluster` |
| GET·PATCH·PUT·DELETE | `…/virtual-network-appliance-clusters/{id}/virtual-network-appliances[/{virtual-network-appliance-id}]` | `ListVirtualNetworkAppliances`, `GetVirtualNetworkAppliance`, `PatchVirtualNetworkAppliance`, `CreateOrUpdateVirtualNetworkAppliance`, `DeleteVirtualNetworkAppliance` |
| POST | `…/virtual-network-appliances/{id}/action/{enter-maintenance-mode\|exit-maintenance-mode\|evacuate\|redeploy}` | `VirtualNetworkApplianceEnterMaintenanceMode`, `VirtualNetworkApplianceExitMaintenanceMode`, `EvacuateVirtualNetworkAppliance`, `RedeployVirtualNetworkAppliance` |
| GET | `/global-infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters[/{edge-cluster-id}]` | `GlobalInfraListEdgeClustersForEnforcementPoint`, `GlobalInfraReadEdgeClusterForEnforcementPoint` |

`PolicyEdgeCluster` body **[SPEC]**: `policy_edge_nodes` (the member list),
`member_node_type`, `deployment_type`, `edge_cluster_profile`, `allocation_rules`,
`inter_site_forwarding_enabled`, `rtep_ips`, `nsx_id`, `password_managed_by_vcf`. That last field is a
useful ownership signal in a VCF deployment — see P9.

The **Virtual Network Appliance** is new in 9.1 **[DOC — VCF 9.1 What's New: NSX]** and the cluster and
appliance CRUD above is spec-confirmed. `GatewayReallocation`'s own description names it:
*"Reallocate or re-balance service instances of gateways within edge or VNA clusters."* **[SPEC]**

---

## Realization, state and troubleshooting reads

A 200 on a `PATCH` means the **intent** was accepted. It does not mean the object is programmed in the
data path. Check realization separately. All **[SPEC]**:

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/realized-state/status` | `ReadIntentStatus` |
| GET | `/infra/realized-state/realized-entities` | `ListRealizedEntities` |
| GET | `/infra/realized-state/realized-entity` | `ReadRealizedEntity` |
| POST | `/infra/realized-state/realized-entity?action=refresh` | `RefreshRealizedState` |
| GET | `/infra/segments/{segment-id}/state` · `/statistics` | `GetInfraSegmentState`, `GetInfraSegmentStatistics` |
| GET | `/infra/tier-0s/{tier-0-id}/state` · `/infra/tier-1s/{tier-1-id}/state` | `GetTier0State`, `GetTier1State` |
| GET | `/search/query` · `/search/dsl` | `QuerySearch`, `DslSearch` |

**Bulk / hierarchical API:** `GET·PATCH·PUT /policy/api/v1/infra` (`ReadInfra`, `PatchInfra`,
`UpdateInfra`) **[SPEC]** accepts a nested tree, so a whole topology can be applied in one
transaction. Powerful and correspondingly dangerous — a malformed hierarchical `PUT /infra` can delete
objects you did not mention. Prefer the scoped endpoints.

---

## Worked example — create an overlay segment attached to a Tier-1

**Goal:** a new overlay segment `app-net-01`, subnet `10.10.20.0/24`, attached to an existing Tier-1
`t1-app`, in the local (`/infra`) scope. Nothing is hard-coded — every path is captured from a read.

```bash
NSX=https://nsx-mgr.example.com
SITE=default            # verify with P3 — do NOT assume
EP=default              # verify with P3 — do NOT assume
TZ=tz-overlay-01        # verify with P4
T1=t1-app               # verify with P5/P6
SEG=app-net-01
```

### Step 0 — Authenticate (see the auth section; details in `nsx-security-policy`)

```bash
curl -sS -c /tmp/nsx-session.txt -D /tmp/nsx-headers.txt -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'j_username=svc-nsx-automation@example.com' \
  --data-urlencode 'j_password=<password>' \
  "$NSX/api/session/create"

XSRF=$(grep -i '^x-xsrf-token:' /tmp/nsx-headers.txt | tr -d '\r' | awk '{print $2}')
AUTH=(-b /tmp/nsx-session.txt -H "x-xsrf-token: $XSRF" -H 'Content-Type: application/json')
```

Pin every subsequent call to the **same manager node address**.

### Step 1 — Confirm your role, read-only (P2)

```bash
curl -sS "${AUTH[@]}" "$NSX/api/v1/aaa/role-bindings" | jq -r '.results[] | "\(.name)\t\(.roles[].role)"'
```

`GET /api/v1/aaa/role-bindings` — **[SPEC — `GetAllRoleBindings`]**. You need `enterprise_admin` (or a
custom role with networking write) for the `PATCH`es below. **Do not** skip this and let the write be
your test.

### Step 2 — Resolve site and enforcement point (P3)

```bash
SITE_PATH=$(curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/sites" \
  | jq -r --arg s "$SITE" '.results[] | select(.id==$s) | .path')
EP_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/sites/$SITE/enforcement-points" \
  | jq -r --arg e "$EP" '.results[] | select(.id==$e) | .path')

[ -n "$SITE_PATH" ] && [ -n "$EP_PATH" ] || { echo "FATAL: site/EP unresolved — fix P3" >&2; exit 1; }
```

`GET /policy/api/v1/infra/sites` — **[SPEC — `ListSites`]**;
`GET /policy/api/v1/infra/sites/{site-id}/enforcement-points` — **[SPEC — `ListEnforcementPointForSite`]**.

### Step 3 — Confirm the transport zone and capture its path (P4)

```bash
TZ_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/sites/$SITE/enforcement-points/$EP/transport-zones/$TZ" \
  | jq -r 'select(.transport_zone_type=="OVERLAY") | .path')

case "$TZ_PATH" in ''|null)
  echo "FATAL: '$TZ' is not a reachable OVERLAY transport zone — fix P4" >&2; exit 1 ;;
esac
```

`GET …/transport-zones/{transport-zone-id}` — **[SPEC — `ReadTransportZoneForEnforcementPoint`]**.
The `jq` guard also enforces the *type*: attaching an overlay segment to a VLAN TZ is a realization
failure, not a 400.

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

`GET /policy/api/v1/infra/tier-1s/{tier-1-id}` — **[SPEC — `ReadTier1`]**. Those two warnings are the
two failures that produce "the segment exists and nothing can reach it".

If the Tier-1 does not exist yet, create it **first** — and give it the advertisement type in the same
call:

```bash
curl -sS -X PATCH "${AUTH[@]}" "$NSX/policy/api/v1/infra/tier-1s/$T1" \
  -d "$(jq -n --arg t0 "/infra/tier-0s/t0-provider" '{
    display_name:              "App Tier-1",
    tier0_path:                $t0,
    route_advertisement_types: ["TIER1_CONNECTED", "TIER1_NAT"],
    failover_mode:             "NON_PREEMPTIVE",
    pool_allocation:           "ROUTING"
  }')"
```

`PATCH /policy/api/v1/infra/tier-1s/{tier-1-id}` — **[SPEC — `PatchTier1`]**. To give it a service
router — required for stateful services and standby relocation (P7) — add a locale service in a
separate call, because `edge_cluster_path` is **not** a `Tier1` field:

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/tier-1s/$T1/locale-services/default" \
  -d "$(jq -n --arg ec "$EP_PATH/edge-clusters/edge-cluster-01" '{edge_cluster_path: $ec}')"
```

`PATCH /policy/api/v1/infra/tier-1s/{tier-1-id}/locale-services/{locale-services-id}`
— **[SPEC — `PatchTier1LocaleServices`]**.

### Step 5 — Create the segment

```bash
curl -sS -X PATCH "${AUTH[@]}" "$NSX/policy/api/v1/infra/segments/$SEG" \
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

`PATCH /policy/api/v1/infra/segments/{segment-id}` — **[SPEC — `PatchInfraSegment`]**.

Field notes, all **[SPEC]** from the `Segment` / `SegmentSubnet` schemas:
- `connectivity_path` takes the **captured** `$T1_PATH`, not a hand-built string. A path that does not
  resolve is accepted at write time and then never realises.
- `transport_zone_path` is passed explicitly even though overlay segments can auto-assign — auto-assign
  only applies when exactly one TZ exists on the enforcement point (P4).
- `gateway_address` is **CIDR, not a bare IP** — `10.10.20.1/24`, the gateway's own address with the
  prefix length. Sending `10.10.20.0/24` gives you a gateway on the network address.
- `subnets` accepts **at most one** entry.
- `dhcp_ranges` is optional; if you use it, note that existing values *"cannot be deleted or modified,
  but additional DHCP ranges can be added"*, and it needs a `dhcp_config_path` on the segment or a
  DHCP config inherited from the gateway to actually serve leases.
- `replication_mode` is overlay-only and defaults to `MTEP`; it is stated here so a later whole-object
  `PUT` does not silently change it.
- **Do not** add `vlan_ids` — a segment with both `connectivity_path` and `vlan_ids` is contradictory;
  VLAN-backed segments cannot carry `connectivity_path`.

Why `PATCH` and not `PUT`: `PATCH` is create-or-update and does not require `_revision`. A `PUT` works
too, but only if you **omit** `_revision` on the creating call and **supply** it on every subsequent
one (P8).

### Step 6 — Verify realization, not just the 200

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/segments/$SEG" | jq '{path, type, _revision}'
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/segments/$SEG/state"
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/realized-state/status?intent_path=/infra/segments/$SEG"
```

`GET …/segments/{segment-id}` **[SPEC — `ReadInfraSegment`]**,
`GET …/segments/{segment-id}/state` **[SPEC — `GetInfraSegmentState`]**,
`GET /infra/realized-state/status` **[SPEC — `ReadIntentStatus`]**. On the first read, `type` should
come back `ROUTED` — that read-only field is the server telling you the attachment actually took.

### Step 7 — Confirm the route is being advertised

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/tier-1s/$T1/advertised-networks"
```

`GET /policy/api/v1/infra/tier-1s/{tier-1-id}/advertised-networks`
— **[SPEC — `GetTier1AdvertisedNetworks`]**. If `10.10.20.0/24` is absent, revisit
`route_advertisement_types` (P6) — the segment is fine and the routing is not.

### Step 8 — Log out

```bash
curl -sS -X POST "${AUTH[@]}" "$NSX/api/session/destroy"
```

**[SPEC — `DestroyAuthenticatedSession`]**

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| 403 on step 1 right after a successful step 0 | `X-XSRF-TOKEN` not sent. |
| 403 mid-sequence after a pause | Session expired — **403, not 401**. Re-authenticate and retry once. |
| 403 that persists after re-auth | Role too low (P2). |
| 403 only on some calls, apparently random | Cookie used against a different cluster node behind a VIP. |
| 404 on step 2 or 3 | Wrong `{site-id}` / `{enforcementpoint-id}` (P3) — `default/default` is a convention, not a guarantee. |
| 400 on step 5 mentioning the subnet | `gateway_address` sent as a bare IP or as the network address; it must be the gateway address in CIDR form. |
| 400 on step 5 about transport zone | VLAN TZ passed to an overlay segment, or `connectivity_path` set on a VLAN-backed segment. |
| 200 on step 5, `type` comes back `DISCONNECTED` | `connectivity_path` does not resolve — you hand-built the path instead of capturing it (P5). |
| Segment realised, VMs on it cannot reach anything off-segment | Tier-1 has no `tier0_path`, or `route_advertisement_types` omits `TIER1_CONNECTED` (P6). |
| Segment realised on some hosts only | Those hosts are not in the transport zone, or their host transport nodes are unhealthy (P7). |
| Stateful service on the Tier-1 fails to configure | No locale service / no `edge_cluster_path` — the T1 has no service router (P7). |
| `GET /infra/tier-1s/{id}/segments` returns nothing though the segment exists | Expected. That endpoint returns **fixed** segments only; yours is flexible. Use `/search/query`. |
| 429 | Per-client rate limit. Back off; read the live ceiling from `GET /api/v1/cluster/api-service`. |

---

## What is unverified for 9.1

- **Dynamic BGP peering's configuration API.** The feature is in the 9.1 What's New; no write surface
  for it is identifiable in the 9.1 policy spec. Only the read-only `neighbor_path` field on the BGP
  neighbor **status** schemas references a *"dynamic bgp neighbor"*. **Do not invent a path for it.**
- **The 17 Manager-API / 9 Policy-API / 1 Autonomous-Edge operations removed in 9.1:** counts are
  published, paths are not. See `../deltas.md`.
- **Per-endpoint role requirements.** "Enterprise Admin writes, Auditor reads" is documented at the
  role level; there is no published matrix saying which networking endpoint needs which built-in role,
  so the Network Admin fit is inferred.
- **The `IpAddressBlock` "up to 10 CIDRs / 10 IP ranges" limit** is a release-note statement; the spec
  declares `cidrs`, `ranges` and `excluded_ips` as arrays with **no `maxItems`**. The array shape is
  spec-confirmed; the number 10 is prose-only.
- **Whether the 9.0 constraints still hold in 9.1** — one NSX per vCenter, narrowed NSX LB entitlement,
  FIPS-by-default — the 9.1 support notes do not restate them.
- **No authoritative VCF-owned-vs-operator-owned NSX object list exists** (P9). This is the largest
  practical gap for a skill whose object set includes the fabric.
