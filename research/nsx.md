# NSX in VMware Cloud Foundation 9.0 and 9.1 — Research Dossier

Research date: **2026-07-31**. Every claim below is tagged `[9.0]`, `[9.1]`, or
`[9.0+9.1 — same, verified in both]` and carries a bracketed source ref (`S##`) resolving to the
**Source Inventory** at the bottom. Nothing here comes from model memory; anything not retrievable
in this task is marked `UNVERIFIED — could not retrieve`.

> **Contamination guard.** The two doc sets live under sibling URL trees
> (`.../vcf-9-0-and-later/9-0/...` vs `.../vcf-9-0-and-later/9-1/...`) and the developer portal
> pins versions in the path (`/9.0.0/` vs `/9.1.0/`). Every fact below was pulled from a
> version-pinned URL. Where a fact was only confirmed in one doc set, it is tagged with that
> version only — do **not** assume it carries over.

---

## NSX in VCF 9.0

### 1. Version / build

| Item | Value | Source |
|---|---|---|
| NSX version in VCF 9.0 BOM | **9.0.0.0** | S3 |
| NSX build number | **24733065** | S3 |
| Matching API doc set (developer portal) | NSX **9.0.0** | S15 |
| Matching API guide title/version string | "NSX API Guide", "NSX 9.0.0.0" | S17 |

`[9.0]` Caveat: the page at S3 is the *live* VCF 9.0 Bill of Materials and at time of access it
also listed VCF Installer 9.0.2.0 (build 25151285) alongside NSX 9.0.0.0 — i.e. the BOM page is
maintained across the 9.0.x patch line. The developer portal exposes **separate** API doc sets for
NSX `9.0.0`, `9.0.1` and `9.0.2` [S15], and the release-notes tree contains per-patch NSX pages
(e.g. `.../vmware-cloud-foundation-9-0-1-release-notes/nsx-9-0-1-0000.html`) [S22]. If the target
environment is on a 9.0.x patch, re-check the BOM for that patch — the NSX build will differ.
The per-patch NSX build numbers for 9.0.1 / 9.0.2 are **UNVERIFIED — could not retrieve** (not
fetched in this task).

### 2. Authentication to NSX Manager API

`[9.0]` The NSX 9.0.0 API Guide documents **four** auth mechanisms [S17]:

**(a) HTTP Basic authentication** `[9.0]` [S17]
- Verbatim: *"To authenticate a request using HTTP Basic authentication, the caller's credentials
  are passed using the 'Authorization' header."*
- Header form: `Authorization: Basic YWRtaW46YWRtaW4=`
- Example given: `curl -k -u USERNAME:PASSWORD https://MANAGER/api/v1/logical-ports`

**(b) Session-based authentication** `[9.0]` [S17][S19][S11]
- Create: `POST /api/session/create`, content type `application/x-www-form-urlencoded`,
  form fields **`j_username`** and **`j_password`** [S17][S11].
- Verbatim (S19): *"Authenticates using the given username and password. If successful, the HTTP
  response headers will contain a Set-Cookie header and an X-XSRF-TOKEN header."* … *"Both of these
  headers should be sent with subsequent API requests."*
- Cookie name observed in the VCF 9.0 admin guide: **`JSESSIONID`** [S11].
- Destroy: `POST /api/session/destroy` — verbatim (S19): *"Unauthenticates and makes the provided
  session cookie invalid. The set-cookie and x-xsrf-token headers obtained from an earlier call to
  /api/session/create should be provided in the HTTP headers of this request."*
- Login example [S11]:
  `curl -i -k -c session.txt -X POST -d 'j_username=admin@example.com&j_password=SecretPwsd3c4d' https://<nsx-manager>/api/session/create 2>&1 > response.txt`
- Subsequent call example [S11]:
  `curl -k -b session.txt -H "x-xsrf-token: 5a764b19-5ad2-4727-974d-510acbc171c8" https://<nsx-manager>/policy/api/v1/infra/segments`
- Session timeout default **1800 seconds (30 min)**, configurable via
  `PUT https://<nsx-mgr>/api/v1/cluster/api-service` (`session_timeout`) [S11].
- Operational notes [S11]: session cookies are **manager-node-specific** and cannot be reused
  across cluster nodes; `+` and other special characters in passwords must be URL-encoded.

**(c) X.509 client certificate authentication** `[9.0]` [S17]
- Verbatim: *"NSX supports using an X.509 client certificate for authentication. The certificate is
  associated with a principal identity (a short name, similar to a username)."*
- With curl: `--key` (private key file) and `--cert` (public certificate file) [S17].

**(d) VMware Cloud on AWS (VMC) token exchange** `[9.0]` [S17] — API token exchanged for a
limited-duration token. Not applicable to on-prem VCF.

**Identity sources** `[9.0]` [S13]: local user accounts (SHA512-hashed passwords), VMware
Workspace ONE Access (vIDM), LDAP / Active Directory / OpenLDAP, and VCF Identity Broker
(Workspace ONE Access Broker) for SSO.

**No JWT/bearer-token API auth flow is documented** in the pages retrieved for 9.0 —
`UNVERIFIED — could not retrieve` a bearer-token API auth procedure [S13][S17].

### 3. Policy API vs Manager API

`[9.0]` **Policy API is the only supported surface.** Verbatim from the VCF 9.0 NSX admin guide
[S9]:

> *"Beginning with VCF 9.0, the NSX Manager interface provides a single mode, Policy mode, for
> configuring resources. The Manager mode and Manager API provided by NSX 4.x and earlier are no
> longer supported."*

> *"The Policy API is part of the NSX REST APIs and contains URIs that begin with /policy/api."*

`[9.0]` Corroborated by the VCF 9.0 release-notes NSX support notes [S8]:
> *"VMware no longer supports the NSX Manager APIs and NSX Advanced UIs."* — new deployments
> should use Policy APIs and Policy UIs.

`[9.0]` Base paths:
- **Policy API**: `/policy/api/v1/...` [S9]
- **Manager API**: `/api/v1/...` — still *present and documented* in the 9.0.0 API guide (the Basic
  auth example targets `/api/v1/logical-ports` [S17]; node/cluster/fabric admin endpoints such as
  `/api/v1/cluster/api-service` remain in use [S11]), but the *logical networking* Manager API is
  no longer supported [S8][S9]. Concrete example of a Manager-API networking endpoint flagged
  deprecated in the 9.0.0 doc set: `GET /api/v1/logical-routers/{logical-router-id}/nat/rules/{rule-id}`
  — *"This endpoint is deprecated as of version 9.0."* [S23]
- **Global Manager / Federation**: `/policy/api/v1/global-infra/...` [S24][S25]
- **Multi-tenancy (projects)**: `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/...` [S24][S26]

`[9.0]` Partial patch: Policy API supports partial object patching, but it must be explicitly
enabled by `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` with
`"enable_partial_patch": "true"` [S9].

`[9.0]` Optimistic concurrency: `_revision` integer on all REST payloads; must be supplied on PUT
and must match, else the update is rejected. For `/policy` URIs specifically, `_revision` must
**not** be set when PUT creates a new resource, but must be supplied on subsequent PUTs [S18 —
verified in the 9.1 guide; the 9.0 guide states *"APIs whose URI begins with /policy have slightly
different behavior"* regarding `_revision` and PATCH [S17]].

`[9.0]` Rate limiting [S17]: per-client **100 requests/second** (HTTP 429 on exceed), per-client
**40 concurrent requests**, overall server maximum **199 concurrent requests**.

`[9.0]` Pagination [S17]: `ListResult` responses default to **1000 results**; clients must handle
the `cursor` property.

### 4. Verified endpoint paths (NSX 9.0.0 doc set)

All paths below were read from version-pinned NSX **9.0.0** pages.

| Object | Method | Path template | Source |
|---|---|---|---|
| Segments (infra) — create/replace | PUT | `/policy/api/v1/infra/segments/{segment-id}` | S27 |
| Segments (project-scoped) | PUT | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/segments/{segment-id}` | S27 |
| Segments under a Tier-1 — list | GET | `/policy/api/v1/infra/tier-1s/{tier-1-id}/segments` | S24 |
| Segments under a Tier-1 (global) | GET | `/policy/api/v1/global-infra/tier-1s/{tier-1-id}/segments` | S24 |
| Segments under a Tier-1 (project) | GET | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/tier-1s/{tier-1-id}/segments` | S24 |
| Tier-0 gateway — read | GET | `/policy/api/v1/infra/tier-0s/{tier-0-id}` | S28 |
| Tier-0 gateway (global) — read | GET | `/policy/api/v1/global-infra/tier-0s/{tier-0-id}` | S28 |
| Tier-1 gateway — read | GET | `/policy/api/v1/infra/tier-1s/{tier-1-id}` | S25 |
| Tier-1 gateway (global / project) | GET | `/policy/api/v1/global-infra/tier-1s/{tier-1-id}` · `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/tier-1s/{tier-1-id}` | S25 |
| DFW security policies — list | GET | `/policy/api/v1/infra/domains/{domain-id}/security-policies` | S29 |
| DFW security policy — read / patch / put / delete | GET·PATCH·PUT·DELETE | `/policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}` | S29, S30 |
| DFW security policy — reorder | POST | `/policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}?action=revise` | S29 |
| DFW rules — list | GET | `/policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}/rules` | S29 |
| DFW rule — read / patch / put / delete | GET·PATCH·PUT·DELETE | `/policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}/rules/{rule-id}` | S29 |
| DFW rule — reorder | POST | `.../rules/{rule-id}?action=revise` | S29 |
| DFW rule statistics | GET | `.../rules/{rule-id}/statistics` | S29 |
| DFW global config | GET·PATCH·PUT | `/policy/api/v1/infra/settings/firewall/security` | S29 |
| DFW exclude list | GET·PATCH·PUT | `/policy/api/v1/infra/settings/firewall/security/exclude-list` | S29 |
| Policy drafts (staged config) | GET·PUT·PATCH·DELETE | `/policy/api/v1/infra/drafts/{draft-id}` | S29 |
| Policy draft — publish | POST | `/policy/api/v1/infra/drafts/{draft-id}?action=publish` | S29 |
| Groups — read | GET | `/policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` | S31 |
| Groups (global / project) | GET | `/policy/api/v1/global-infra/domains/{domain-id}/groups/{group-id}` · `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/domains/{domain-id}/groups/{group-id}` | S31 |
| IP pools — list / CRUD | GET·PUT·PATCH·DELETE | `/policy/api/v1/infra/ip-pools` · `/policy/api/v1/infra/ip-pools/{ip-pool-id}` | S32 |
| IP allocations | GET·PUT·PATCH·DELETE | `/policy/api/v1/infra/ip-pools/{ip-pool-id}/ip-allocations/{ip-allocation-id}` | S32 |
| IP subnets | GET·PUT·PATCH·DELETE | `/policy/api/v1/infra/ip-pools/{ip-pool-id}/ip-subnets/{ip-subnet-id}` | S32 |
| Load balancer service — read | GET | `/policy/api/v1/infra/lb-services/{lb-service-id}` | S33 |
| Transport zone — read | GET | `/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones/{transport-zone-id}` | S34 |
| Transport zone (global) | GET | `/policy/api/v1/global-infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones/{transport-zone-id}` | S34 |
| Edge cluster — read | GET | `/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters/{edge-cluster-id}` | S35 |
| Edge cluster (global) | GET | `/policy/api/v1/global-infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters/{edge-cluster-id}` | S35 |
| NAT rule (Manager API, **deprecated as of 9.0**) | GET | `/api/v1/logical-routers/{logical-router-id}/nat/rules/{rule-id}` | S23 |
| OpenAPI spec — Manager | GET | `/api/v1/spec/openapi/nsx_api.yaml` · `.json` | S17 |
| OpenAPI spec — Policy | GET | `/api/v1/spec/openapi/nsx_policy_api.yaml` · `.json` | S17 |
| Session create / destroy | POST | `/api/session/create` · `/api/session/destroy` | S17, S19, S11 |
| API service config (session timeout) | PUT | `/api/v1/cluster/api-service` | S11 |
| Partial-patch enablement | PATCH | `/policy/api/v1/system-config/nsx-partial-patch-config` | S9 |

**Not directly verified in the 9.0.0 doc set** (paths exist in 9.1.0 and are almost certainly
identical, but were not opened on a 9.0.0-pinned page — treat as unconfirmed for 9.0):
Policy NAT rules on Tier-0/Tier-1 (`/policy/api/v1/infra/tier-{0,1}s/{id}/nat/{nat-id}/nat-rules/{nat-rule-id}`),
IPSec VPN services, host transport nodes, `search` endpoints.
`UNVERIFIED — could not retrieve` for 9.0.

### 5. What's new in NSX for VCF 9.0 (selected, verbatim-sourced) `[9.0]` [S6]

- **Licensing**: NSX licensing assigned through VCF Operations; 90-day evaluation mode.
- **VPC networking**: VPCs and subnets creatable *in vCenter*; VPC in VCF Automation; VPC in
  Supervisor (StaticRoute, SecurityPolicy, K8s NetworkPolicy); Connectivity and Service Profiles;
  **Transit Gateways** ("central hub for routing traffic", centralized and distributed types);
  Distributed VLAN connectivity (ESX-to-fabric without edge nodes); VPC-Ready Workload Domains;
  Terraform provider extended for Transit Gateway and VPCs.
- **Enhanced Data Path (EDP)**: EDP Standard is *"default host switch mode of operation for new VCF
  Workload Domains"*; EDP Fast Path for SPAN and Live Traffic Analysis; Industrial vSwitch mode
  with PRP.
- **Edge platform**: Edge Host Affinity; edge install/config streamlined through vCenter;
  Gateway Firewall *"automatically disabled by default for all greenfield deployments"*.
- **LCM**: *"standalone upgrade of NSX is not supported"* — must follow the VCF BOM; NSX Manager
  installed as a VCF component; NSX VIBs shipped with ESX by default; ESX Live Patch support for
  NSX VIBs; NSX integrated with vSphere Config Profiles; TEPs may use the management VMkernel
  (VMK0) IP; single NSX Manager supported; "Hitless" NSX Manager upgrade.
- **Monitoring**: Logical Switch IPFIX ConnectionTrack module; centralized System Health
  Monitoring page.
- **Security**: FIPS 140-2/140-3 cryptographic modules; *"Components including NSX operate in
  FIPS-enabled mode by default and cannot be deactivated"* [S36].

### 6. VCF-specific constraints on NSX `[9.0]` [S8][S6]

- *"Starting with NSX 9.0, a standalone NSX installation or upgrade is not supported."* VCF Bill of
  Materials and recommended processes are required [S8]. Repeated in What's New: *"standalone
  upgrade of NSX is not supported"* [S6].
- *"VMware supports only one NSX instance for the same vCenter instance."* [S8]
- **NSX Embedded (NSXe) removed entirely from VCF 9.0** — *"NSX can no longer be installed or
  managed from vCenter."* [S8]
- **NSX Migration Coordinator removed** — *"Beginning with this release, the NSX Migration
  Coordinator is no longer available."* Migrate NSX-for-vSphere to NSX 4.x first, then upgrade [S8].
- **NSX Load Balancer entitlement narrowed**: general-purpose LB removed from VCF entitlement;
  Avi Load Balancer recommended; NSX LB retained only for VCF infrastructure and vSphere Supervisor
  use cases [S8]. → An agent should not assume `/policy/api/v1/infra/lb-services` is a licensed
  general-purpose path.
- **Overlay on physical servers removed**: *"NSX 9.0.0 no longer supports the deployment of NSX
  agents on physical servers."* [S8]
- **OIDC**: *"NSX brings down the support of OpenID Connection endpoints from 10 to only one,"*
  which must be VMware Identity Broker [S8].
- **Deprecated in 9.0** (still functional, slated for removal): vIDM support in NSX; Principal
  Identity accounts (*"planned for deprecation in an upcoming release"* — migrate to Federated
  Users via VCF SSO); "Standard" virtual switch mode [S8]. → Note the tension: X.509 cert auth is
  bound to **principal identities** [S17], which are on the deprecation path [S8].
- **vShield Endpoint**: *"VMware no longer supports vShield Endpoint."* [S8]

---

## NSX in VCF 9.1

### 1. Version / build

| Item | Value | Source |
|---|---|---|
| NSX version in VCF 9.1 BOM | **9.1.0.0** | S4 |
| NSX build number | **25318225** | S4 |
| Matching API doc set (developer portal) | NSX **9.1.0** | S16 |
| Matching API guide title/version string | "NSX API Guide", "NSX 9.1.0.0" | S18 |

`[9.1]` The 9.1 BOM lists NSX as a **VMware Cloud Foundation** component that is **not** included
in the VMware vSphere Foundation component offering [S4].

### 2. Authentication to NSX Manager API

`[9.1]` The NSX 9.1.0 API Guide documents the **same four** mechanisms as 9.0 [S18]:

**(a) HTTP Basic authentication** `[9.1]` [S18]
- Verbatim: *"To authenticate a request using HTTP Basic authentication, the caller's credentials
  are passed using the 'Authorization' header."*
- `Authorization: Basic YWRtaW46YWRtaW4=`
- `curl -k -u USERNAME:PASSWORD https://MANAGER/api/v1/logical-ports`

**(b) Session-based authentication** `[9.1]` [S18][S12]
- Verbatim (S18): *"Session-based authentication is used by calling the /api/session/create
  authentication API to manage a session cookie."*
- Create: `POST /api/session/create`, form fields `j_username` / `j_password` [S18][S12].
- Response carries `Set-Cookie` (**`JSESSIONID`**) and **`X-XSRF-TOKEN`** [S12][S18].
- Login example [S12]:
  `curl -i -k -c session.txt -X POST -d 'j_username=admin@example.com&j_password=SecretPwsd3c4d' https://<nsx-manager>/api/session/create 2>&1 > response.txt`
- Subsequent call example [S12]:
  `curl -k -b session.txt -H "x-xsrf-token: 5a764b19-5ad2-4727-974d-510acbc171c8" https://<nsx-manager>/policy/api/v1/infra/segments`
- Guide example (S18): `curl -k -b cookies.txt -H "$(grep -i X-XSRF-TOKEN headers.txt | tr -d '\r\n')"`
- Destroy: `POST /api/session/destroy` (send cookie + `x-xsrf-token`) [S18][S12].
- Session timeout default **1800 s (30 min)**, changed via
  `PUT https://<nsx-mgr>/api/v1/cluster/api-service` (`session_timeout`) [S12].
- On expiry: *"NSX Manager responds with a 403 Forbidden HTTP response."* [S12]
- On logout: *"the session cookie is immediately eliminated from the reverse-proxy of the NSX
  Manager and cannot be reused."* [S12]

**(c) X.509 client certificate authentication** `[9.1]` [S18]
- Verbatim: *"NSX supports using an X.509 client certificate for authentication. The certificate is
  associated with a principal identity."*
- curl: `--key` + `--cert` [S18].

**(d) VMware Cloud on AWS (VMC) token exchange** `[9.1]` [S18] — not applicable on-prem.

**Identity sources** `[9.1]` [S14]: local user accounts (SHA512), Workspace ONE Access (vIDM),
LDAP/AD/OpenLDAP, VCF Identity Broker; *"Starting in NSX 4.1.2, you can use vCenter server as an
external identity provider."* Access via UI, API and CLI is authenticated, authorized and audited;
audit logging is on by default and cannot be disabled [S14].

**Auth delta vs 9.0: none found.** Same endpoints, same header names, same form fields, same
timeout default — `[9.0+9.1 — same, verified in both]` for `/api/session/create`,
`/api/session/destroy`, `j_username`/`j_password`, `X-XSRF-TOKEN`, `JSESSIONID`, Basic auth header,
X.509 cert auth, and the 1800 s session timeout [S17 vs S18; S11 vs S12; S19 vs S18].

No JWT/bearer-token API auth flow documented — `UNVERIFIED — could not retrieve` [S14][S18].

### 3. Policy API vs Manager API

`[9.1]` The VCF 9.1 NSX admin guide repeats the 9.0 statement verbatim [S10]:

> *"Beginning with VCF 9.0, the NSX Manager interface provides a single mode, Policy mode, for
> configuring resources. The Manager mode and Manager API provided by NSX 4.x and earlier are no
> longer supported."*

> *"The Policy API is part of the NSX REST APIs and contains URIs that begin with /policy/api."*

`[9.1]` Base paths — identical shape to 9.0:
- **Policy API**: `/policy/api/v1/...` [S10]
- **Global (Federation)**: `/policy/api/v1/global-infra/...` [S37][S38]
- **Multi-tenancy**: `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/...` [S37][S39]
- **Manager / node & cluster admin**: `/api/v1/...` still present (Basic-auth example targets
  `/api/v1/logical-ports` [S18]; `/api/v1/cluster/api-service` [S12]; OpenAPI specs served from
  `/api/v1/spec/openapi/...` [S18]).
- `[9.1]` The API guide itself still describes both surfaces neutrally: *"NSX Manager API: APIs for
  NSX administration; node and cluster management APIs and fabric management APIs"* and *"NSX Policy
  Manager API: APIs for managing logical networking"* — it *"makes no recommendation about which to
  use"* [S17, wording checked in the 9.0 guide; 9.1 guide carries the same
  `/policy` `_revision` caveat text [S18]]. The **product docs** are the authoritative
  "Policy-only" statement [S10].

`[9.1]` Optimistic concurrency, verbatim [S18]: *"All REST payloads contain a property named
'_revision'. This is an integer that is incremented each time an existing resource is updated.
Clients must provide this property in PUT requests and it must match the current _revision or the
update will be rejected."* And: *"the _revision property must **not** be set when PUT is used to
create a new resource. Once the resource is created, however, the _revision property must be
provided with PUT operations."*

`[9.1]` Rate limiting, verbatim [S18]: *"A per-client rate limit, in requests per second. If a
client makes more requests than this limit in one second, the API server will refuse to service the
API request and will return an HTTP 429 Too Many Requests Error. By default, this limit is 100
requests per second."* … *"A per-client concurrency limit… By default, this limit is 40 concurrent
requests."*

`[9.1]` Pagination, verbatim [S18]: *"The API will respond with a ListResult object that has at most
page_size results… The default page size is 1000."* Segment/list endpoints expose `cursor`,
`page_size` (0–1000, default 1000), `included_fields`, `sort_by`, `sort_ascending`,
`include_mark_for_delete_objects` [S37].

### 4. Verified endpoint paths (NSX 9.1.0 doc set)

All paths read from version-pinned NSX **9.1.0** pages. `{org}/{proj}` shorthand =
`/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/...`.

**Segments** [S37]
| Method | Path | Purpose (verbatim) |
|---|---|---|
| GET | `/policy/api/v1/infra/segments` | "Paginated list of all segments under infra" |
| GET | `/policy/api/v1/global-infra/segments` | same, global |
| GET | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/segments` | same, project |
| GET | `/policy/api/v1/infra/segments/{segment-id}` | "Read infra segment" |
| PATCH | `/policy/api/v1/infra/segments/{segment-id}` | "Create or update a segment" |
| PUT | `/policy/api/v1/infra/segments/{segment-id}` | "Create or replace infra segment" (also S40) |
| DELETE | `/policy/api/v1/infra/segments/{segment-id}` | "Delete infra segment" |
| DELETE/PATCH/PUT | `.../segments/{segment-id}?force=true` | force variants |
| GET | `/policy/api/v1/infra/segments/{segment-id}/effective-profiles` | "List all effective profiles for infra segment on given enforcement point" |
| GET | `/policy/api/v1/infra/segments/{segment-id}/segment-connection-binding-maps` | list binding maps |
| GET/PUT/PATCH/DELETE | `/policy/api/v1/infra/segments/{segment-id}/segment-connection-binding-maps/{map-id}` | binding map CRUD |
| GET | `/policy/api/v1/infra/segments/service-segments` | "Paginated list of all Service Segments" |
| GET/PUT/PATCH/DELETE | `/policy/api/v1/infra/segments/service-segments/{service-segment-id}` | service segment CRUD ("modification is not supported") |
| GET | `/policy/api/v1/infra/tier-1s/{tier-1-id}/segments` | fixed segments under a Tier-1 (excludes flexible segments — use search API) [S41] |

**Tier-0 gateways** [S42]
| Method | Path | Purpose |
|---|---|---|
| GET | `/policy/api/v1/infra/tier-0s` | "Paginated list of all Tier-0s" |
| GET | `/policy/api/v1/global-infra/tier-0s` | global list |
| GET | `/policy/api/v1/infra/tier-0s/{tier-0-id}` | "Read Tier-0" (also S43) |
| PATCH | `/policy/api/v1/infra/tier-0s/{tier-0-id}` | create/update |
| PUT | `/policy/api/v1/infra/tier-0s/{tier-0-id}` | create/replace |
| DELETE | `/policy/api/v1/infra/tier-0s/{tier-0-id}` | "Delete Tier-0" |
| POST | `/policy/api/v1/infra/tier-0s/{tier-0-id}?action=reprocess` | "Reprocess Tier0 gateway configuration and publish updates to NSX controller" |
| POST | `/policy/api/v1/infra/tier-0s?action=site_failover` | Federation site failover |
| POST | `/policy/api/v1/infra/tier-0s/{tier-0-id}/actions/failover` | manual A/S failover |
| POST | `{org}/{proj}/tier-0s/{tier-0-id}/actions/failover` | project-scoped failover |

**Tier-1 gateways** [S39]
| Method | Path | Purpose |
|---|---|---|
| GET | `/policy/api/v1/infra/tier-1s` | list |
| GET | `/policy/api/v1/global-infra/tier-1s` · `{org}/{proj}/tier-1s` | global / project list |
| GET | `/policy/api/v1/infra/tier-1s/{tier-1-id}` | read (also S38) |
| PATCH / PUT / DELETE | `/policy/api/v1/infra/tier-1s/{tier-1-id}` | create-update / create-replace / delete |
| POST | `/policy/api/v1/infra/tier-1s/{tier-1-id}?action=reprocess` | reprocess |
| POST | `/policy/api/v1/infra/tier-1s/{tier-1-id}/actions/failover` | manual failover |
| POST | `/policy/api/v1/infra/gateways/action/reallocate` | "Reallocate or re-balance service instances of gateways within edge or VNA clusters" — **new-looking in 9.1**, see delta table |
| POST | `{org}/{proj}/gateways/action/reallocate` | project-scoped reallocate |

**DFW / security policies** `[9.1]`
| Method | Path | Source |
|---|---|---|
| GET | `/policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}` | S44 |
| GET | `/policy/api/v1/global-infra/domains/{domain-id}/security-policies/{security-policy-id}` | S44 |
| GET | `{org}/{proj}/domains/{domain-id}/security-policies/{security-policy-id}` | S44 |
| GET | `/policy/api/v1/infra/firewall/policies` · `/policy/api/v1/global-infra/firewall/policies` · `{org}/{proj}/firewall/policies` | S45 — filtered policy query |
| GET | `/policy/api/v1/infra/firewall/rules` · `/policy/api/v1/global-infra/firewall/rules` · `{org}/{proj}/firewall/rules` | S45 — filtered rule query |
| POST | `/policy/api/v1/infra/settings/security/host-configuration-report` | S45 — CSV host config report (**appears in 9.1, not seen on the 9.0 DFW page**) |

`[9.1]` The full security-policy/rule CRUD sub-tree
(`.../security-policies/{id}` PATCH/PUT/DELETE, `.../rules/{rule-id}`, `?action=revise`,
`/statistics`) was **not** re-listed on a 9.1.0-pinned category page in this task — only the GET
read method was confirmed [S44]. The path *shape* is identical to 9.0 [S29]. Treat the
non-GET verbs on 9.1 as **structurally inferred, not doc-verified**.

**Groups** [S46]
| Method | Path |
|---|---|
| GET | `/policy/api/v1/infra/domains/{domain-id}/groups` (filterable by member type) |
| GET | `/policy/api/v1/global-infra/domains/{domain-id}/groups` · `{org}/{proj}/domains/{domain-id}/groups` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` |
| GET | `.../groups/{group-id}/member-types` |
| PATCH/POST/DELETE | `.../groups/{group-id}/ip-address-expressions/{expression-id}` |
| PATCH/POST/DELETE | `.../groups/{group-id}/mac-address-expressions/{expression-id}` |
| PATCH/POST/DELETE | `.../groups/{group-id}/path-expressions/{expression-id}` |
| PATCH/POST/DELETE | `.../groups/{group-id}/external-id-expressions/{expression-id}` |

`[9.1]` The `POST .../{expression-type}-expressions/{expression-id}` verb performs incremental
"add or remove members" without rewriting the whole group [S46].

**IP pools / IPAM** [S47]
| Method | Path |
|---|---|
| GET | `/policy/api/v1/infra/ip-pools` · `{org}/{proj}/ip-pools` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/ip-pools/{ip-pool-id}` |
| GET | `/policy/api/v1/infra/ip-pools/{ip-pool-id}/ip-allocations` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/ip-pools/{ip-pool-id}/ip-allocations/{ip-allocation-id}` |
| GET | `/policy/api/v1/infra/ip-pools/{ip-pool-id}/ip-subnets` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/ip-pools/{ip-pool-id}/ip-subnets/{ip-subnet-id}` |
| GET | `/policy/api/v1/infra/manager-ip-pools` · `/policy/api/v1/infra/manager-ip-pools/{manager-ip-pool-id}` |

**NAT** [S48 (Tier-0), S49 (Tier-1)]
| Method | Path |
|---|---|
| GET | `/policy/api/v1/infra/tier-0s/{tier-0-id}/nat` (list NAT sections) |
| GET | `/policy/api/v1/infra/tier-0s/{tier-0-id}/nat/{nat-id}/nat-rules` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/tier-0s/{tier-0-id}/nat/{nat-id}/nat-rules/{nat-rule-id}` |
| GET | `/policy/api/v1/infra/tier-1s/{tier-1-id}/nat` · `/policy/api/v1/global-infra/...` · `{org}/{proj}/...` |
| GET | `/policy/api/v1/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules/{nat-rule-id}` |
| GET/PATCH/PUT/DELETE | `{org}/{proj}/tier-1s/{tier-1-id}/nat/{nat-id}/nat-rules/{nat-rule-id}` |

`[9.1]` Note the asymmetry: Tier-1 NAT exposes `global-infra` and project-scoped variants; the
Tier-0 NAT page listed `global-infra` for reads only and no project-scoped variants [S48][S49].

**Load balancing** [S50]
| Method | Path | Purpose (verbatim) |
|---|---|---|
| GET | `/policy/api/v1/infra/lb-services` | "Paginated list of all LBService" |
| GET | `/policy/api/v1/infra/lb-services/{lb-service-id}` | "Read an LBService" |
| PATCH | `/policy/api/v1/infra/lb-services/{lb-service-id}` | "Create or update a LBVirtualServer" *(sic — doc text)* |
| PUT | `/policy/api/v1/infra/lb-services/{lb-service-id}` | "Create or update a LBService" |
| DELETE | `/policy/api/v1/infra/lb-services/{lb-service-id}` | "Delete the LBService along with all the entities contained by this LBService" |
| GET | `/policy/api/v1/infra/lb-services/{lb-service-id}/debug-info` | "Read the debug information of the load balancer service" |

**VPN (IPSec)** [S51]
| Method | Path |
|---|---|
| GET | `/policy/api/v1/infra/tier-0s/{tier-0-id}/ipsec-vpn-services` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/tier-0s/{tier-0-id}/ipsec-vpn-services/{service-id}` |
| GET | `/policy/api/v1/infra/tier-1s/{tier-1-id}/ipsec-vpn-services` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/tier-1s/{tier-1-id}/ipsec-vpn-services/{service-id}` |
| GET/PATCH/PUT/DELETE | `{org}/{proj}/tier-1s/{tier-1-id}/ipsec-vpn-services/{service-id}` |

`[9.1]` The 9.1.0 page explicitly notes that **locale-service-scoped IPSec VPN paths**
(`.../locale-services/{locale-service-id}/ipsec-vpn-services/...`) are present but **deprecated**
[S51]. Prefer the gateway-scoped form above.

**Transport zones** [S52]
| Method | Path |
|---|---|
| GET | `/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones` |
| GET | `/policy/api/v1/global-infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones` |
| GET/PATCH/PUT/DELETE | `/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/transport-zones/{transport-zone-id}` |

**Edge clusters** [S53]
| Method | Path | Purpose (verbatim) |
|---|---|---|
| PUT | `/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/edge-clusters/{edge-cluster-id}` | "Create Or Update a Policy Edge Cluster." |
| PATCH / DELETE | same path | patch / "Delete the specified edge cluster." |
| POST | `.../edge-clusters/{edge-cluster-id}/action/relocate-and-remove-edge-transport-node` | "Relocate service contexts from policy edge node and remove it." |
| POST | `.../edge-clusters/{edge-cluster-id}/action/replace-edge-transport-node` | "Replace the policy edge node at specified member-index." |
| GET | `.../edge-clusters/{edge-cluster-id}/edge-nodes` | "Paginated list of all Edge Nodes under an Enforcement Point." |
| GET | `.../edge-clusters/{edge-cluster-id}/allocation/status` | "Get allocation details of cluster and its members." |
| GET | `.../edge-clusters/{edge-cluster-id}/state` · `/status` | current state / real-time aggregated status |
| GET | `.../edge-clusters/{edge-cluster-id}/remote-tep-connectivity/status` · `/remote-tep-connectivity/bgp/summary` | RTEP connectivity |
| GET | `.../edge-cluster-high-availability-profiles` | "List edge cluster high availability profiles." |
| GET/PATCH/PUT/DELETE | `.../edge-cluster-high-availability-profiles/{edge-cluster-high-availability-profile-id}` | HA profile CRUD |

`[9.1]` Edge cluster **read (GET on `/edge-clusters/{id}`)** was not listed on the 9.1.0 category
page fetched [S53]; it *is* documented for 9.0.0 [S35]. Almost certainly present in 9.1 — but
`UNVERIFIED — could not retrieve` on a 9.1.0-pinned page.

**Host transport nodes** — `UNVERIFIED — could not retrieve` for either version (category and
method page guesses returned no content) [S54].

**Search API** — `UNVERIFIED — could not retrieve`. The 9.1.0 Segments doc references *"the search
API"* as the way to obtain all segments connected to a Tier-1 including flexible ones [S41], and a
"Search" nav group exists in the 9.1.0 portal [S16], but no concrete path was retrieved.

### 5. What's new in NSX for VCF 9.1 (verbatim-sourced) `[9.1]` [S5]

**VPC networking / multi-tenancy**
- **Virtual Network Appliance (VNA)** — new appliance *"designed to run and support network services
  within distributed VPC environments."*
- **VPC Load Balancer**: *"Layer 4 (L4) load balancing service is fully supported"* via the VNA.
  Plus *"support for AVI load balancers with VPCs and Transit Gateways with distributed VLAN
  connection."*
- **VPC VPN**: *"IPSec VPN service is now supported for VPC using centralized external
  connectivity"* — Policy-Based and Route-Based.
- **1:N SNAT** *"when using the distributed Transit Gateway."*
- **Multiple distributed Transit Gateways** per project with a Distributed VLAN Connection.
- **Centralized Transit Gateway advanced connectivity**: multiple gateway connections, multiple
  TGWs per project, independent HA modes, Proxy-ARP.
- **EVPN-VXLAN**: *"Distributed EVPN-VXLAN that enables direct workload integration with
  EVPN-VXLAN fabrics."*
- **VLAN extension**: extend *"VPC subnets to an existing VLAN in the fabric"* for DVPG VM onboarding.
- **VPC Connectivity Policy**: *"communities of VPCs… isolated VPCs… promiscuous VPCs."*
- **Transit Gateway / VPC span** definable *"directly from vCenter or from NSX."*
- **Infoblox integration**: *"discover Infoblox Network Views, DNS Views, and Network Containers."*
- **vCenter integration**: *"Transit Gateway visible and fully configurable from vCenter"*, subnet
  extension to VLAN, IPAM visibility, topology views, DHCP config.
- **Terraform**: extended provider coverage for Transit Gateway and VPC features.
- **Distributed Transit Gateway for the Supervisor** via VNA, for VCF Automation.
- **Tenant networking**: Distributed VLAN, multiple TGWs, *"Self Service NAT, VPN, Grouping,
  Firewalling."*

**Edge platform**
- New simplified Edge Node / Edge Cluster UI workflow.
- Bare Metal Edge datapath NIC support: Broadcom 574X/575X, Mellanox CX6 LX.
- Control-plane packet prioritization on Edge uplinks (RX and TX).
- *"VLAN and MTU pre-check for the Edge node"* during Edge VM deployment.

**Data path / performance**
- **FPO hardware steering** — *"asynchronous queue-based hardware steering engine"* for NVIDIA
  ConnectX-6 DX / ConnectX-7 / BlueField-2/3.
- **Uniform Passthrough (UPT)** — *"near line-rate networking performance through the standard
  VMXNET3 interface"*, with vMotion support.
- **Enhanced Direct Path I/O (EDPIO)** — *"direct hardware access to NVIDIA ConnectX-6 DX,
  ConnectX-7, or BlueField-3"* with **GPUDirect RDMA** for AI/ML.
- EDP optimizations: *"posted interrupt support for lower VMXNET3 latency"*, multicast perf,
  SR-IOV, LRO for Antrea.
- GRE traffic scale: vNIC RSS hashing enhancements for the Edge Node VM appliance.
- **DPDK upgraded to 24.11.**

**Platform security**
- Non-Disruptive Certificate renewal architecture adopted across VCF components.
- *"NSX Backup and Restore now support RSA and SSH-ED hostkey algorithms."*
- Reset Password now requires *"new password to be different from the old password."*
- NSX no longer creates ESXi accounts *"mux_user, da-user, nsx-user, and lldpVim-user."*
- *"All NSX appliances have been upgraded to Ubuntu 24.04"* with chiseled containers.

**VCF integration**
- **VPC-ready domains**: *"configure vNetworking service (Tunnel EndPoint - TEP) even if it was not
  configured initially."*
- **vCenter TEP configuration**: *"overlay Tunnel EndPoint (TEP) can now be configured directly
  from vCenter like other vmkernel NICs."*
- **LACP/LAG configurable directly in the UI.**
- **Shared NSX Managers**: *"VCF Management Domain can now share NSX Managers with other VCF
  workload domains."*

**Observability / IPAM / LB / ops**
- **Port Mirroring Policy API** supporting *"Local SPAN as well RSPAN"* with centralized config.
- **VDS IPFIX** updated to the ConnectionTrack-enabled module; *uplink port group IPFIX no longer
  supported.*
- **IPAM**: IP Block now supports *"up to 10 CIDRs, 10 IP ranges (from one previously), and to
  exclude specific IPs"*; providers can share IP Blocks *"while limiting the visibility on the
  content of the IP Block"*; Distributed DHCP auto-excludes detected static IPs.
- **Distributed Load Balancer** *"is now independently managed and decoupled from the Distributed
  Firewall (DFW)."*
- SSH Banner configurable on NSX Manager and Edge appliances.

**Routing**
- **Dynamic BGP peering**: *"define a range of IP addresses that will be used to determine when a
  Tier-0 gateway should establish BGP peering."*
- **L3 scale increases**: *"configuration maximums for a number of aspects of VCF Networking
  (including L3 Networking scale) has been increased."*

**VKS / Kubernetes**
- **Istio Service Mesh** *"now available at a per-VKS cluster level"* — mTLS, sidecar and ambient
  modes, L4/L7 routing.
- Dual-network: *"secondary network interface (vNIC)"* for VKS clusters and Pods with Antrea CNI.

**Brownfield / LCM**
- SDDC Manager network sync for *"network configuration changes done directly in vCenter or NSX
  Manager."*
- **Bare Metal Edge import**: existing deployments with NSX Bare Metal edge nodes can be imported
  into VCF.
- VDS capabilities to support NSX ↔ vSphere Config Profiles integration.
- *"Move NSX Edge/SVM Upgrades to the End of Upgrade Sequence"* — aligned with vSphere.

### 6. Deprecations / removals in 9.1 `[9.1]` [S7]

**Deprecated**
- **PhotonOS-based HCX appliances**: *"A new stack based on NSX Edge is being introduced that has a
  better performance than the PhotonOS stack. Therefore, the PhotonOS-based appliances in HCX is
  being deprecated."*
- **IPFIX on uplinks**: *"VDS IPFIX will be backed with NSX Connection Track based IPFIX data path
  to export TCP connection information. However, the Connection Track based IPFIX does not support
  uplink port due to performance constraints. As IPFIX will not be supported on the uplink port
  group, the dependent 'LagIpfixConfig' and 'overwrite port policy Netflow' will not be supported."*
- **Locale-service-scoped IPSec VPN paths** flagged deprecated in the 9.1.0 API reference [S51].

**Removed**
- **Port mirroring Manager-plane API**: *"Logical MP API for port mirroring is no longer
  supported."* (Replaced by the new Port Mirroring **Policy** API [S5].)
- **NSX Manager API — 17 operations removed**, affecting System Health Agent metrics/monitoring
  endpoints, port mirroring (SPAN) session management endpoints, and node user enumeration [S7].
- **NSX Policy API — 9 operations removed**, affecting VPC Subnet Bridge Profiles lifecycle
  operations, PMaaS firewall exclude-list management, and Infrastructure Policy Labels operations [S7].
- **NSX Autonomous Edge API — 1 operation removed**: edge node user enumeration [S7].

`[9.1]` The exact operation IDs / paths for those 17 + 9 + 1 removed operations were **not**
enumerated on the page retrieved — `UNVERIFIED — could not retrieve` [S7]. The developer portal
exposes "Removed Methods" / "Removed Types" sections for 9.1.0 [S16], but the page could not be
opened under any guessed filename in this task [S55].

### 7. VCF-specific constraints on NSX `[9.1]`

- `[9.1]` Policy-only: Manager mode and Manager API for logical networking are *"no longer
  supported"* [S10].
- `[9.1]` **Shared NSX Managers**: *"VCF Management Domain can now share NSX Managers with other VCF
  workload domains"* — new in 9.1; a topology assumption that changes in 9.1 vs 9.0 [S5].
- `[9.1]` **SDDC Manager network sync** now tolerates *"network configuration changes done directly
  in vCenter or NSX Manager"* [S5] — i.e. in 9.1 out-of-band NSX edits are explicitly reconciled
  rather than being purely forbidden. This is the closest thing to a "what may an agent change
  directly in NSX" statement found; a definitive list of VCF-owned-vs-NSX-owned objects is
  **UNVERIFIED — could not retrieve**.
- `[9.1]` The 9.1 product support notes contain **no statement** distinguishing VCF-based NSX object
  management from direct NSX management [S7].
- `[9.0]` constraints listed in the 9.0 section (no standalone NSX install/upgrade, one NSX per
  vCenter, NSXe removed, LB entitlement narrowed, single OIDC endpoint) were stated in the **9.0**
  support notes [S8] and were **not** re-verified in the 9.1 doc set. Do not assert them for 9.1
  without re-checking.

---

## 9.0 → 9.1 Delta Table

| Area | VCF 9.0 | VCF 9.1 | Source(s) |
|---|---|---|---|
| NSX version | 9.0.0.0 | 9.1.0.0 | S3, S4 |
| NSX build | 24733065 | 25318225 | S3, S4 |
| API doc set on developer portal | `/9.0.0/` (also `/9.0.1/`, `/9.0.2/`) | `/9.1.0/` | S15, S16 |
| Session auth endpoints | `POST /api/session/create`, `POST /api/session/destroy` | identical | S17/S19/S11 vs S18/S12 |
| Session auth form fields | `j_username`, `j_password` | identical | S17/S11 vs S18/S12 |
| Session auth headers | `Set-Cookie` (`JSESSIONID`) + `X-XSRF-TOKEN` | identical | S19/S11 vs S18/S12 |
| Session timeout default | 1800 s | 1800 s | S11, S12 |
| HTTP Basic auth | supported, `Authorization: Basic …` | supported, identical wording | S17, S18 |
| X.509 cert auth (principal identity) | supported | supported | S17, S18 |
| Rate limit | 100 req/s, 40 concurrent/client, 199 overall | 100 req/s, 40 concurrent/client (overall figure not restated) | S17, S18 |
| Default page size | 1000 | 1000 | S17, S18 |
| Policy API base path | `/policy/api/v1` | `/policy/api/v1` | S9, S10 |
| Manager mode / Manager API for networking | *"no longer supported"* | same statement repeated | S9, S8 vs S10 |
| OpenAPI spec endpoints | `/api/v1/spec/openapi/nsx_api.{yaml,json}`, `nsx_policy_api.{yaml,json}` | identical | S17, S18 |
| Developer-portal nav taxonomy | grouped by *Federation / Management Plane API / NSX Application Platform / Policy / System Administration* | regrouped by function: *Certificates, Enforcement Points, Federation, Inventory, Monitoring, Multi-Tenancy, Networking, Policy, Search, Security, System, Troubleshooting, User Management, VPC Networking* — no "Management Plane API" top-level group | S15, S16 |
| Doc-set URL shape (product docs) | `.../9-0/advanced-network-management/administration-guide/<topic>.html` | `.../9-1/advanced-network-management/<topic>.html` (no `administration-guide/` segment) | S1/S20 vs S2/S21 |
| VPC load balancing | VPC introduced; no VPC L4 LB service called out | *"Layer 4 (L4) load balancing service is fully supported"* via new **Virtual Network Appliance (VNA)** | S6, S5 |
| VPC VPN | not called out | *"IPSec VPN service is now supported for VPC using centralized external connectivity"* | S6, S5 |
| Transit Gateway | introduced (centralized + distributed) | multiple TGWs per project, multiple distributed TGWs, independent HA modes, Proxy-ARP, 1:N SNAT, EVPN-VXLAN | S6, S5 |
| Distributed Load Balancer | coupled to DFW | *"now independently managed and decoupled from the Distributed Firewall (DFW)"* | S5 |
| Port mirroring | Manager-plane ("Logical MP") API | MP API **removed**; new **Port Mirroring Policy API** with Local SPAN + RSPAN | S7, S5 |
| IPFIX | Logical Switch IPFIX ConnectionTrack module introduced | VDS IPFIX moved to ConnectionTrack module; **uplink port group IPFIX no longer supported**; `LagIpfixConfig` and "overwrite port policy Netflow" unsupported | S6, S7, S5 |
| IPAM IP Block limits | (baseline) | *"up to 10 CIDRs, 10 IP ranges (from one previously), and to exclude specific IPs"* | S5 |
| BGP peering | static peer config | **Dynamic BGP peering** via IP range on Tier-0 | S5 |
| NSX Manager sharing | (not stated) | *"VCF Management Domain can now share NSX Managers with other VCF workload domains"* | S5 |
| Appliance OS | (not stated) | *"All NSX appliances have been upgraded to Ubuntu 24.04"* + chiseled containers | S5 |
| DPDK | (not stated) | upgraded to **24.11** | S5 |
| Upgrade sequence | (baseline) | *"Move NSX Edge/SVM Upgrades to the End of Upgrade Sequence"* | S5 |
| ESXi accounts created by NSX | `mux_user`, `da-user`, `nsx-user`, `lldpVim-user` created | NSX **no longer creates** these accounts | S5 |
| API surface churn | Manager networking APIs unsupported; `/api/v1/logical-routers/.../nat/rules/...` "deprecated as of version 9.0" | 17 Manager-API + 9 Policy-API + 1 Autonomous-Edge operations **removed** | S8, S23, S7 |
| IPSec VPN path shape | gateway-scoped and locale-service-scoped both present | locale-service-scoped paths flagged **deprecated** | S51 |
| Gateway service reallocation | not observed | `POST /policy/api/v1/infra/gateways/action/reallocate` — *"Reallocate or re-balance service instances of gateways within edge or VNA clusters"* (references VNA, new in 9.1) | S39 |
| DFW host config report | not observed on 9.0 DFW page | `POST /policy/api/v1/infra/settings/security/host-configuration-report` | S29, S45 |
| NSX Migration Coordinator | **removed in 9.0** | (not restated) | S8 |
| NSXe (NSX embedded in vCenter) | **removed in 9.0** | (not restated) | S8 |
| HCX appliance stack | (not stated) | PhotonOS-based HCX appliances **deprecated** in favour of an NSX-Edge-based stack | S7 |

> **Caution on "not observed" rows.** Several 9.1-only entries above were confirmed present in the
> 9.1.0 reference but were not explicitly checked for *absence* in the 9.0.0 reference beyond the
> pages fetched. They are labeled "not observed", not "absent".

---

## Lookup patterns for undocumented operations

This section matters more than exhaustive enumeration — it is how an agent finds an endpoint that
is not listed above.

### A. Ask the appliance for its own spec (best; version-exact, no guessing)
`[9.0+9.1 — same, verified in both]` [S17][S18]

```
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_policy_api.json   # Policy API  (use this one)
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_policy_api.yaml
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_api.json          # Manager API (node/cluster/fabric)
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_api.yaml
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_vmc_policy_api.{yaml,json}
GET https://<nsx-mgr>/api/v1/spec/openapi/nsx_vmc_aws_integration_api.{yaml,json}
```

These are served by the *running* NSX Manager, so the spec always matches the deployed build
(9.0.0.0 / 24733065 or 9.1.0.0 / 25318225). This is the single most reliable discovery mechanism and
it eliminates version-contamination risk entirely. Authenticate first (session or basic).

### B. Version-pinned developer-portal URL patterns
`[9.0]` root: `https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/` [S15]
`[9.1]` root: `https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/` [S16]

Reliable sub-patterns (both verified in this task):

| Pattern | Example | Notes |
|---|---|---|
| `<root>/method_<OperationId>.html` | `…/9.1.0/method_ReadTier0.html` | Highest-value page: gives verb, **all** path templates (incl. `global-infra` and `orgs/projects` variants), and query params. Works in both doc sets. |
| `<root>/<category>.html` | `…/9.1.0/networking_switching_segments.html` | Lists every method in a functional area with verb + path. Best bulk-extraction page. |
| `<root>/api_single_page.html` | | Consolidated guide. Often too large to fetch reliably. |
| `<root>/types_<TypeName>.html`, `<root>/schemas_<Name>.html` | | Request/response body schemas. |

**Category slug naming differs between the two doc sets** — this is a real trap:
- `[9.1]` function-first: `networking_switching_segments.html`, `networking_routing_tier-0s.html`,
  `networking_routing_tier-1s.html`, `networking_nat_nat_rules_tier-0s.html`,
  `networking_nat_nat_rules_tier-1s.html`, `networking_load_balancing_lb_services.html`,
  `networking_vpn_ipsec_services.html`, `networking_ip_management_ip_pools.html`,
  `networking_switching_transport_zones.html`, `system_fabric_edge_clusters.html`,
  `inventory_groups.html`, `security_firewall.html` [S16 and the per-page sources]
- `[9.0]` `policy_`-prefixed: `policy_networking.html`, `policy_security.html`,
  `policy_security_east_west_security_distributed_firewall.html`,
  `management_plane_api_networking.html` [S15][S29]
- Adding/removing the `policy_` prefix is **not** a reliable translation between the two
  (`policy_networking_switching_segments.html` does not exist for 9.0.0; the 9.1 DFW page is not
  `security_east_west_security_distributed_firewall.html`). Navigate the left-hand tree instead of
  guessing.

**Failure signature:** a nonexistent page on developer.broadcom.com returns the SPA shell (nav menu
only, sometimes "Object Not Found"). If a fetch yields only category links and no verb/path table,
the URL is wrong — do not treat that as "the endpoint doesn't exist."

### C. Static mirror of the API guide (best for prose: auth, pagination, rate limits, concurrency)
`[9.0]` `https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.0.0/html/index.html` [S17]
`[9.1]` `https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html` [S18]

Pattern: `…/API_NTDCRA_001/<nsx-version>/html/index.html`. Each page self-identifies its version
("NSX API Guide", "NSX 9.1.0.0"), which is a useful contamination check. Note
`…/<version>/html/api_usage_user_authentication.html` returns 404 on this host — the auth content
lives inside `index.html` [S56].

### D. Path-shape heuristics for Policy API `[9.0+9.1 — same, verified in both]`

Once you know the object type, its path almost always follows one of these, and the doc pages list
all applicable variants side by side:

```
/policy/api/v1/infra/<collection>                              # local, list
/policy/api/v1/infra/<collection>/{id}                         # local, CRUD
/policy/api/v1/global-infra/<collection>/{id}                  # Federation / Global Manager
/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/...   # multi-tenancy (projects)
/policy/api/v1/infra/tier-0s/{tier-0-id}/<service>             # T0-attached service
/policy/api/v1/infra/tier-1s/{tier-1-id}/<service>             # T1-attached service
/policy/api/v1/infra/domains/{domain-id}/<security-object>     # DFW: groups, security-policies
/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/<fabric-object>
                                                               # fabric: transport-zones, edge-clusters
/policy/api/v1/infra/settings/<subsystem>/...                  # global settings
```
Verbs: `GET` list/read, `PATCH` create-or-update (merge), `PUT` create-or-replace, `DELETE` remove,
`POST …?action=<verb>` or `…/actions/<verb>` for imperative operations (`revise`, `reprocess`,
`failover`, `publish`, `site_failover`) [S29][S37][S39][S42].

### E. Runtime conventions to build into any client `[9.0+9.1 — same, verified in both]`
- **Pagination**: default `page_size` 1000, max 1000; follow `cursor` until absent [S17][S18][S37].
- **Rate limits**: back off on HTTP **429**; 100 req/s and 40 concurrent per client [S17][S18].
- **Concurrency**: read `_revision`, echo it on `PUT`; omit `_revision` on a `PUT` that *creates*
  a `/policy` resource [S18].
- **Partial patch** must be turned on first:
  `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` with
  `{"enable_partial_patch": "true"}` [S9][S10].
- **Session expiry** surfaces as **403 Forbidden**, not 401 — re-authenticate on 403 [S12].
- **Session affinity**: session cookies are bound to a single NSX Manager node; do not reuse across
  cluster members / behind a VIP that load-balances [S11].
- **Search API** is the documented way to enumerate objects that the hierarchical endpoints omit
  (e.g. flexible segments attached to a Tier-1) — referenced in 9.1.0 docs [S41], concrete path
  `UNVERIFIED — could not retrieve`.

### F. Interactive API explorer
- **UNVERIFIED — could not retrieve** that NSX Manager 9.0 or 9.1 ships an embedded interactive API
  explorer / Swagger UI. The VCF 9.0 and 9.1 NSX Manager admin pages do **not** mention one; they
  direct readers to the external NSX API Guide: *"For more information about using the Policy API,
  see the NSX API Guide."* [S9][S10]
- The practical substitutes are (A) the appliance-served OpenAPI spec, and (B) the Broadcom
  Developer Portal version-pinned reference [S15][S16].

---

## Gaps and Ambiguities

1. **9.0.x patch NSX builds.** Only NSX 9.0.0.0 / 24733065 was confirmed from the VCF 9.0 BOM [S3].
   The developer portal exposes NSX 9.0.1 and 9.0.2 doc sets [S15] and per-patch release notes exist
   [S22], but their BOM/build numbers were not fetched. **UNVERIFIED — could not retrieve.**
2. **9.1 removed operations not enumerated.** The 9.1 support notes give counts (17 Manager-API,
   9 Policy-API, 1 Autonomous-Edge) and themes, but not paths/operation IDs [S7]. The developer
   portal "Removed Methods" page could not be opened under any guessed filename [S55].
   **UNVERIFIED — could not retrieve.**
3. **9.1 DFW write operations.** Only `GET .../security-policies/{security-policy-id}` was confirmed
   on a 9.1.0-pinned page [S44]. PATCH/PUT/DELETE, `?action=revise`, `/rules/{rule-id}` and
   `/statistics` are confirmed for **9.0** [S29] and structurally implied for 9.1, but not verified.
4. **9.0 NAT / VPN / edge-cluster-list / transport-zone-list on Policy API.** Confirmed for 9.1
   [S48][S49][S51][S52][S53]; for 9.0 only the *read* forms of transport zone and edge cluster were
   confirmed [S34][S35]. Policy NAT rule paths and IPSec VPN service paths on 9.0 are
   **UNVERIFIED — could not retrieve**.
5. **Host transport nodes** endpoints: **UNVERIFIED — could not retrieve** in either doc set [S54].
6. **Search API** concrete path and parameters: **UNVERIFIED — could not retrieve** in either doc
   set, despite being referenced as the recommended workaround for incomplete list endpoints [S41].
7. **Bearer/JWT token auth.** Neither API guide nor either admin guide documents an OAuth/JWT bearer
   flow against NSX Manager for on-prem VCF; only session, basic, X.509, and the VMC-specific token
   exchange appear [S17][S18][S13][S14]. Given that VCF Identity Broker is now the sole OIDC
   endpoint [S8], a token-based path may exist but is **UNVERIFIED — could not retrieve**.
8. **"Which NSX objects must be managed via VCF."** No authoritative list found. Evidence is
   indirect: standalone NSX install/upgrade prohibited `[9.0]` [S8]; SDDC Manager network sync
   reconciles direct vCenter/NSX changes `[9.1]` [S5]; 9.1 support notes contain no such statement
   [S7]. **UNVERIFIED — could not retrieve.**
9. **Whether the 9.0 constraints still hold in 9.1.** One-NSX-per-vCenter, NSX LB entitlement
   narrowing, single OIDC endpoint, principal-identity deprecation, "Standard" vSwitch mode
   deprecation were all sourced from the **9.0** support notes [S8] and not restated in the 9.1
   support notes retrieved [S7]. They are tagged `[9.0]` only. Note the 9.1 "shared NSX Managers"
   feature [S5] does *not* contradict one-NSX-per-vCenter — it is about one NSX Manager serving
   multiple workload domains.
10. **Rate-limit "199 overall concurrent"** was quoted from the 9.0 guide [S17]; the 9.1 extraction
    quoted only the 100 req/s and 40 concurrent figures [S18]. The overall figure for 9.1 is
    **UNVERIFIED — could not retrieve** (likely unchanged, not asserted).
11. **Developer-portal taxonomy delta** (9.0 "Management Plane API" group absent from 9.1 nav) is
    based on rendered navigation menus [S15][S16], not on an explicit doc statement. Treat as an
    observation about documentation structure, not a proven API-surface removal.
12. **`api_single_page.html`** for 9.1.0 could not be fetched (server error) [S57]; the dp-downloads
    `index.html` mirror was used instead.
13. **Direct HTTP tooling was unavailable.** The sandbox egress proxy returned 403 on CONNECT to
    `techdocs.broadcom.com` for `curl` [S58], so all retrieval went through the WebFetch tool, which
    summarizes rather than returning raw HTML. Quotes marked verbatim are as returned by that tool;
    exact whitespace/punctuation may differ trivially from source. Long enumerations (e.g. full
    "All Methods" indexes) could not be extracted wholesale.

---

## Source Inventory

All accessed **2026-07-31**.

| ID | URL | Doc set version | Date accessed | Covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | VCF 9.0 | 2026-07-31 | 9.0 doc landing; NSX under "Advanced Network Management" |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | 2026-07-31 | 9.1 doc landing; NSX under "Advanced Network Management" |
| S3 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.0 | 2026-07-31 | 9.0 BOM: NSX 9.0.0.0 / 24733065 |
| S4 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.1 | 2026-07-31 | 9.1 BOM: NSX 9.1.0.0 / 25318225 |
| S5 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-nsx.html | VCF 9.1 | 2026-07-31 | What's New — NSX (9.1), full feature list |
| S6 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-nsx.html | VCF 9.0 | 2026-07-31 | What's New — NSX (9.0), full feature list |
| S7 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vcf-91-product-support-notes.html | VCF 9.1 | 2026-07-31 | 9.1 deprecations/removals; removed-operation counts |
| S8 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-nsx.html | VCF 9.0 | 2026-07-31 | 9.0 NSX deprecations/removals/constraints |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/advanced-network-management/administration-guide/nsx-manager.html | VCF 9.0 | 2026-07-31 | Policy-mode-only statement; `/policy/api`; partial patch |
| S10 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/advanced-network-management/nsx-manager.html | VCF 9.1 | 2026-07-31 | Same Policy-mode-only statement for 9.1 |
| S11 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/advanced-network-management/administration-guide/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html | VCF 9.0 | 2026-07-31 | 9.0 session-cookie auth procedure + curl |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/advanced-network-management/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html | VCF 9.1 | 2026-07-31 | 9.1 session-cookie auth procedure + curl; 403 on expiry |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/advanced-network-management/administration-guide/authentication-and-authorization.html | VCF 9.0 | 2026-07-31 | 9.0 identity sources |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/advanced-network-management/authentication-and-authorization.html | VCF 9.1 | 2026-07-31 | 9.1 identity sources; audit logging |
| S15 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/ | NSX 9.0.0 | 2026-07-31 | 9.0.0 API reference root; nav taxonomy; version list |
| S16 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/ | NSX 9.1.0 | 2026-07-31 | 9.1.0 API reference root; nav taxonomy |
| S17 | https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.0.0/html/index.html | NSX 9.0.0.0 | 2026-07-31 | NSX API Guide 9.0: basic/session/X.509/VMC auth, OpenAPI endpoints, rate limits, pagination |
| S18 | https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html | NSX 9.1.0.0 | 2026-07-31 | NSX API Guide 9.1: same sections, plus `_revision` verbatim |
| S19 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/api_usage_user_authentication.html | NSX 9.0.0 | 2026-07-31 | `/api/session/create` and `/api/session/destroy` descriptions verbatim |
| S20 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/advanced-network-management/administration-guide.html | VCF 9.0 | 2026-07-31 | 9.0 NSX admin guide TOC + subsection URLs |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/advanced-network-management.html | VCF 9.1 | 2026-07-31 | 9.1 NSX admin guide TOC + subsection URLs |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-1-release-notes/nsx-9-0-1-0000.html | VCF 9.0.1 | 2026-07-31 | Existence of per-patch NSX release notes (surfaced via search; not opened) |
| S23 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_GetNatRule.html | NSX 9.0.0 | 2026-07-31 | Manager-API NAT rule path; "deprecated as of version 9.0" |
| S24 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ListSegments.html | NSX 9.0.0 | 2026-07-31 | T1 segment list paths + query params |
| S25 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadTier1.html | NSX 9.0.0 | 2026-07-31 | Tier-1 read paths |
| S26 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadGroupForDomain.html | NSX 9.0.0 | 2026-07-31 | Group read paths |
| S27 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_CreateOrReplaceInfraSegment.html | NSX 9.0.0 | 2026-07-31 | Infra segment PUT paths |
| S28 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadTier0.html | NSX 9.0.0 | 2026-07-31 | Tier-0 read paths |
| S29 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/policy_security_east_west_security_distributed_firewall.html | NSX 9.0.0 | 2026-07-31 | Full 9.0 DFW method table: security policies, rules, drafts, IDFW, exclude list, communication-maps (deprecated) |
| S30 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadSecurityPolicyForDomain.html | NSX 9.0.0 | 2026-07-31 | Security policy read paths |
| S31 | (same as S26) | NSX 9.0.0 | 2026-07-31 | Group paths |
| S32 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/policy_networking.html | NSX 9.0.0 | 2026-07-31 | 9.0 IP pool / allocation / subnet paths |
| S33 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadLBService.html | NSX 9.0.0 | 2026-07-31 | LB service read path |
| S34 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadTransportZoneForEnforcementPoint.html | NSX 9.0.0 | 2026-07-31 | Transport zone read paths |
| S35 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadEdgeClusterForEnforcementPoint.html | NSX 9.0.0 | 2026-07-31 | Edge cluster read paths |
| S36 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new.html | VCF 9.0 | 2026-07-31 | FIPS 140-2/140-3 statement; link to NSX What's New |
| S37 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_switching_segments.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 segment method table (46 entries) |
| S38 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_ReadTier1.html | NSX 9.1.0 | 2026-07-31 | Tier-1 read paths (9.1) |
| S39 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_routing_tier-1s.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 Tier-1 method table incl. `gateways/action/reallocate` |
| S40 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_CreateOrReplaceInfraSegment.html | NSX 9.1.0 | 2026-07-31 | Infra segment PUT paths (9.1) |
| S41 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_ListSegments.html | NSX 9.1.0 | 2026-07-31 | T1 segment list; note that flexible segments require the search API |
| S42 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_routing_tier-0s.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 Tier-0 method table |
| S43 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_ReadTier0.html | NSX 9.1.0 | 2026-07-31 | Tier-0 read paths (9.1) |
| S44 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_ReadSecurityPolicyForDomain.html | NSX 9.1.0 | 2026-07-31 | Security policy read paths (9.1) |
| S45 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/security_firewall.html | NSX 9.1.0 | 2026-07-31 | 9.1 firewall query endpoints + host-configuration-report |
| S46 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/inventory_groups.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 group method table incl. expression sub-resources |
| S47 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_ip_management_ip_pools.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 IP pool / allocation / subnet / manager-ip-pool table |
| S48 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_nat_nat_rules_tier-0s.html | NSX 9.1.0 | 2026-07-31 | Tier-0 NAT method table |
| S49 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_nat_nat_rules_tier-1s.html | NSX 9.1.0 | 2026-07-31 | Tier-1 NAT method table incl. project-scoped |
| S50 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_load_balancing_lb_services.html | NSX 9.1.0 | 2026-07-31 | LB service method table |
| S51 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_vpn_ipsec_services.html | NSX 9.1.0 | 2026-07-31 | IPSec VPN service tables; locale-service paths deprecated |
| S52 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_switching_transport_zones.html | NSX 9.1.0 | 2026-07-31 | Transport zone method table |
| S53 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/system_fabric_edge_clusters.html | NSX 9.1.0 | 2026-07-31 | Edge cluster + HA profile method tables |
| S54 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/system_fabric_host_transport_nodes.html · .../9.1.0/method_ListHostTransportNodesForEnforcementPoint.html · .../9.0.0/method_ListHostTransportNodesForEnforcementPoint.html | NSX 9.1.0 / 9.0.0 | 2026-07-31 | Negative result — no content returned (host transport nodes unresolved) |
| S55 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/deprecated_methods.html · .../removed_methods.html | NSX 9.1.0 | 2026-07-31 | Negative result — SPA shell only; removed/deprecated lists not retrievable |
| S56 | https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/api_usage_user_authentication.html | NSX 9.1.0 | 2026-07-31 | Negative result — HTTP 404 (auth content is inside index.html) |
| S57 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/api_single_page.html | NSX 9.1.0 | 2026-07-31 | Negative result — fetch/server error |
| S58 | /root/.ccr/README.md + agent-proxy status endpoint (local) | n/a | 2026-07-31 | Egress policy: direct `curl` CONNECT to techdocs.broadcom.com returned 403; WebFetch used throughout |
