# VCF 9.1 — VCF Automation for VM Apps Reference

**Scope:** VCF Automation (formerly VMware Aria Automation) in VMware Cloud Foundation 9.1, **VM
Apps organizations only**. For All Apps organizations see `vcf-automation-allapps-k8s`.

**Sources.** `DVCFA` = `research/vcf-automation.md`, whose own `[S##]` refs resolve to its Source
Inventory (all pages accessed 2026-07-31); `DAUTH` = `research/foundation-auth-identity.md`.
Every path below carries its dossier source ref.

**Evidence tags — read these before quoting any path.**

| Tag | Means |
|---|---|
| `[DOC-9.1]` | Printed on a fetched **9.1** page, or on the Broadcom developer portal (which serves "9.1 (latest)"). |
| `[DOC-9.0]` | Printed on a fetched **9.0** page only. The 9.1 guide persists under identical slugs [DVCFA `[S05]`, `[S28]`] but the 9.1 leaf page was **not fetched**, so 9.1 applicability is presumed, not confirmed. |
| `[DOC-BOTH]` | Read from pages in **both** doc sets. |
| `[UNVERIFIED]` | Named in the docs but **no path was ever printed on a retrievable page**, or elided/contradicted in the source. Do not emit a path. |

> **There is no OpenAPI specification for VCF Automation in the published corpus at the 9.1.0.0
> tag.** No endpoint in this file is spec-confirmed. This is weaker evidence than every sibling
> skill provides. Confirm unverified areas against the customer's own appliance — via the
> in-product API Help Center — before use.

**The headline for 9.1:** the VM Apps API surface and its tenant auth flow are **unchanged**. What
9.1 adds is a *second* authentication route (fleet-wide, via VCF Identity Broker) and a large set
of provider-side capabilities. If a user is on 9.1 and asking about catalog requests and
deployments, the 9.0 answer is still the answer.

---

## Contents

- [Prerequisites](#prerequisites)
  - P0 — You are in a VM Apps organization, not an All Apps organization
  - P1 — A token exists and you chose the right one of two token systems
  - P2 — The project exists and you have its id
  - P3 — The catalog item exists, is shared to the project, and you know its version
  - P4 — The caller holds rights for the operation — UNVERIFIED
  - P5 — Items the research could not verify
- [Endpoints in 9.1 — what carries over](#endpoints-in-91--what-carries-over)
- [Authentication in 9.1 — two coexisting token systems](#authentication-in-91--two-coexisting-token-systems)
- [Provider / All-Apps REST conventions worth knowing](#provider--all-apps-rest-conventions-worth-knowing)
- [What's new in 9.1](#whats-new-in-91)
- [Unverified areas — say so and route to discovery](#unverified-areas--say-so-and-route-to-discovery)
- [Discovery routes](#discovery-routes)
- [Terraform and IaC in 9.1](#terraform-and-iac-in-91)
- [Ambiguities found while writing this file](#ambiguities-found-while-writing-this-file)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what must
hold, **how to verify it**, the version it applies to, and whether 9.0 differs.

### P0 — You are in a VM Apps organization, not an All Apps organization `[9.1]`

**Must be true:** the organization you are calling is a **VM Apps** org. The two organization
types persist in 9.1 with different consumption mechanisms; the wrong one is a completely
different API, not a variant of this one. Nothing else in this file applies to an All Apps org.

**How to verify:**
- The 9.1 VM Apps tenant portal presents the same nine tabs as 9.0 — **Home, Consume, Design,
  Infrastructure, Content and Policies, Extensibility, Orchestrator, Alerts, Inbox**
  [DVCFA `[S21]`].
- Capability discriminator, documented on the 9.0 page and not contradicted in 9.1: **ABX,
  Deployment, Deployment Metrics, Identity and Onboarding are available only in VCF Automation for
  VM Apps** [DVCFA `[S33]`].
- All Apps in 9.1 is explicitly Kubernetes-native: `kubectl --context cci api-resources`, API
  group `infrastructure.cci.vmware.com/v1alpha2`, resources including `SupervisorNamespace`,
  `Project`, `ProjectRole`, `ProjectRoleBindings`, `Region`, `RegionStorageClassQuotas`, `Zone`
  [DVCFA `[S32]`]. If the caller is writing YAML manifests against that group, they are not in a
  VM Apps org — route to `vcf-automation-allapps-k8s`.
- UI surfaces unchanged: `https://FQDN/automation` (tenant) and `https://FQDN/provider`
  (service-provider administrators) [DVCFA `[S29]`] `[DOC-BOTH]`.

**9.0 difference:** none. Both org types and both UI surfaces exist identically in 9.0
[DVCFA `[S06]`, `[S07]`].

### P1 — A token exists, and you chose the right one of two token systems `[9.1]`

**Must be true:** you hold a current token issued by the **correct** of the **two coexisting**
token systems in 9.1 [DVCFA `[S13]`, `[S30]`]:

1. The **VCF-Automation-local VM Apps tenant flow** — `/tm/oauth/tenant/{tenant}/token`. Unchanged
   from 9.0. This is the one to use for everything in this file.
2. The **fleet-wide VCF Identity Broker (VIDB) flow** — `/acs/t/{role}/token`. New in 9.1, covers
   VCF Automation among other components.

**No fetched page states that the tenant flow is deprecated** [DVCFA `[S13]` vs `[S30]`], and how
the two relate — coexistence, precedence, migration — is **not stated anywhere**
[DVCFA Gap 14] `[UNVERIFIED]`. Do not tell a user the tenant flow is going away.

**How to verify:** obtain the token by the flow you chose (both are written out in
[Authentication in 9.1](#authentication-in-91--two-coexisting-token-systems)), then make one cheap
read — `GET /catalog/api/items/{id}/versions` — and confirm it does not 401.

**Lifetimes differ between the two systems.** Tenant flow: API/refresh token default **90 days**,
access token **one hour** [DVCFA `[S13]`]. VIDB clients created through the 9.1 SSO UI: **API
Token TTL default 30 days**, **Access Token TTL default 30 minutes**, both configurable
[DVCFA `[S17]`]. A script written against 90-day assumptions and issued a 30-day VIDB token will
fail about a month in, at no particular time, which reads like an outage rather than an expiry.

**9.0 difference:** 9.0 has only the tenant flow (plus the provider device-authorization grant).
The VIDB route does not exist in 9.0 [DVCFA delta row 1].

### P2 — The project exists and you have its id `[9.1]`

**Must be true:** the target **project** exists before you create a deployment. `projectId` is a
body field on both documented write paths [DVCFA `[S23]`, `[S24]`]. In 9.1 the Organization
Management description is re-worded around exactly this: org admins "create and assign projects
and vSphere Namespaces tailored for different application teams" [DVCFA `[S11]`].

**How to verify — the evidence stops here too.** `[UNVERIFIED]` **The Projects API base path was
never printed on any retrievable page** in either version; the tutorial landing pages carry no
paths and their leaf children were not retrievable within Broadcom's rate limits [DVCFA Gap 4].
Use the **Infrastructure** tab of the tenant portal, or look the Projects service up in the
**in-product API Help Center**.

Note the adjacent trap: in **All Apps** orgs, `Project` is a Kubernetes CRD with a documented
permission matrix (Admin full CRUD, DevOps read-only) [DVCFA `[S32]`]. That is *not* the VM Apps
projects API, and it is not a substitute for it.

**9.0 difference:** none — the gap is identical.

### P3 — The catalog item exists, is shared to the project, and you know its version `[9.1]`

**Must be true, three things:** the item exists; **it is shared to the project you are deploying
into** (the Catalog service covers "content sharing" [DVCFA `[S08]`], and an unshared item behaves
for that project's members like an item that does not exist); and you know which `version` to
request [DVCFA `[S23]`].

**How to verify:**
- `GET /catalog/api/items/{catalogItemId}/versions` `[DOC-9.0]` [DVCFA `[S23]`] — lists versions,
  and incidentally proves the item is visible to your token.
- `GET /catalog/api/items` `[DOC-9.1]` [DVCFA `[S18]`] — documented on the developer portal with
  OData-style parameters `$orderby`, `$top`, `$skip`, plus `page` and `size`; example
  `/catalog/api/items?$orderby=name%20desc`.
- Sharing state itself: the **Content and Policies** tab, or the API Help Center.
  `[UNVERIFIED]` — no sharing endpoint path was printed on any retrievable page.

**9.0 difference:** none established. The versions path comes from the 9.0 doc set; the collection
path and OData parameters come from the 9.1/latest portal.

### P4 — The caller holds rights for the operation `[9.1]` — UNVERIFIED

**Must be true:** the account behind the token holds the rights for the operation, especially the
writes (`POST /blueprint/api/blueprints`, `POST /catalog/api/items/{id}/request`).

> `[UNVERIFIED]` **No per-operation privilege requirement is documented for VM Apps API
> operations.** The 9.1 role model *is* documented [DAUTH `[S50]`]: **rights** are per-object-type
> view/manage grants, categorised (Catalog, Organization, …); **roles** are sets of rights;
> **provider roles** are exclusive to the provider org; **global roles** are created and published
> by System Administrators to one or more organizations and org admins cannot modify them;
> **organization-specific roles** are created locally and hold only a subset of organization
> rights; **rights bundles** default to a read-only "Simple Mode" with an "Advanced Rights Bundle
> Mode" feature flag; and **System Administrator** exists only in the provider org and holds all
> VCF Automation rights. That is the shape of the model, not a mapping from operation to right.
> Do not name a required role in a runbook without checking it on the customer's instance.

Related and worth flagging when tokens are being provisioned: in 9.1 the VCF built-in role mapping
gives **VCF Administrator** → *VCF Automation System Administrator* [DAUTH]. That is a fleet-level
mapping, not a per-endpoint grant.

### P5 — Items the research could not verify — state these as gaps

- **Projects, cloud accounts / cloud zones, resource / day-2 actions, ABX paths** — none printed on
  any retrievable page, in either version [DVCFA Gaps 4–7].
- **The Aria-era IaaS base path** — **never confirmed in any fetched 9.0 or 9.1 page and must not
  be assumed** [DVCFA Gap 5]. The most likely hallucination in this subject area; it is a memory
  of Aria Automation 8.x, not a VCF 9.x fact.
- **The VIDB `grant_type` literal** — elided as `...` in the source page as rendered
  [DVCFA Gap 1].
- **The access-token response field name** for the tenant flow — not named in the docs
  [DAUTH Gap 4].
- **The All Apps access-token endpoint** — the page "Generating an All Apps Access Token" appeared
  in search results but returned **404 on fetch** [DVCFA Gap 3; DAUTH Gap 5]. Relevant here only
  as a boundary: if a user is asking for All Apps tokens, that is a known hole, not something to
  fill in.
- **Relationship between the tenant flow and VCF SSO / VIDB in 9.1** — coexistence, precedence and
  migration are not stated on any fetched page [DVCFA Gap 14].
- **Deployment status vocabulary and polling cadence** — no terminal-state list, no failure-state
  list, no recommended interval, in either version.
- **Pipelines / Code Stream** — absent from every fetched page in both versions; whether dropped
  or relocated is unresolved. Do not assert either way [DVCFA Gap 8].

---

## Endpoints in 9.1 — what carries over

The blueprint, catalog and deployment paths were read from **9.0** tutorial pages. The 9.1 doc set
carries the "VMware Cloud Foundation Automation APIs for VM Apps Programming Guide" under
**identical slugs** [DVCFA `[S05]`, `[S28]`], and the delta research found **no VCF Automation
feature deprecations anywhere in 9.1** [DVCFA delta table footnote]. Presenting these as 9.1 paths
is reasonable — presenting them as 9.1-*confirmed* is not, hence the tags.

**Blueprint / cloud template service** — base path `$url/blueprint/api` [DVCFA `[S24]`]

| Method | Path | Purpose | Tag |
|---|---|---|---|
| POST | `/blueprint/api/blueprints` | Create a cloud template | `[DOC-9.0]` |
| GET | `/blueprint/api/blueprints` | List cloud templates | `[DOC-9.0]` |
| GET | `/blueprint/api/blueprints?name=$cloud_template_name` | Filter by name | `[DOC-9.0]` |
| PUT | `/blueprint/api/blueprints/{cloud_template_id}` | Update a cloud template | `[DOC-9.0]` |
| POST | `/blueprint/api/blueprint-validation` | Validate a cloud template | `[DOC-9.0]` |

Create body: `name`, `description`, `content` (YAML template as a string — `formatVersion: 1`,
`inputs:`, `resources:` with e.g. `type: Cloud.Machine`), `projectId`, `requestScopeOrg`.
Headers: `Content-Type: application/json`, `Authorization: Bearer $access_token` [DVCFA `[S24]`].

**Catalog and Deployment services** [DVCFA `[S23]`, `[S18]`]

| Method | Path | Purpose | Tag |
|---|---|---|---|
| POST | `/catalog/api/items/{catalogItemId}/request` | Request a deployment from a catalog item | `[DOC-9.0]` |
| GET | `/catalog/api/items/{catalogItemId}/versions` | List available versions | `[DOC-9.0]` |
| GET | `/deployment/api/deployments` | Query existing deployments | `[DOC-9.0]` |
| GET | `/deployment/api/deployments/{deploymentId}` | Check deployment status | `[DOC-9.0]` |
| GET | `/catalog/api/items` | List catalog items; `$orderby`, `$top`, `$skip`, `page`, `size` | `[DOC-9.1]` |

Request body fields: `deploymentName`, `projectId`, `catalogItemId`, `version`, `inputs` (runtime
variables of that blueprint — the documented example uses `count`, `image`, `flavor`, which is not
a fixed schema) [DVCFA `[S23]`].

**Worked sequence:** `../../SKILL.md` Step 4, using only these paths.

> **Requesting a catalog item provisions real infrastructure** against the project's cloud zones
> and quota. No rollback or cancel path is documented anywhere in this research.

**Same two gaps as 9.0:** how the deployment id comes back from the request call is not shown on
the fetched page (query `GET /deployment/api/deployments`), and no status vocabulary or polling
interval is documented.

**9.1 blueprint wording change, harmless but worth knowing:** the 9.1 docs describe blueprints as
templates that may be "VCF or AWS CloudFormation" and that "administrators can import for reuse"
[DVCFA `[S21]`]. That is a description change, not an API change — no import path is documented.
`[UNVERIFIED]`

## Authentication in 9.1 — two coexisting token systems

### Flow 1 — VM Apps tenant access token (use this one) `[DOC-BOTH]`

Unchanged from 9.0: same page, same lifetimes, same three-step flow [DVCFA delta row 3, `[S13]`].
The endpoint itself is printed on the 9.0 page [DVCFA `[S14]`].

```
POST https://{{vcfaHostname}}/tm/oauth/tenant/{{vcfaTenant}}/token
Content-Type: application/x-www-form-urlencoded
Accept: application/json

grant_type=refresh_token&refresh_token={{vcfaAPIToken}}
```

Then `Authorization: Bearer <access_token>` — the `Bearer` prefix is observed in the blueprint
curl examples [DVCFA `[S24]`].

**Lifetimes:** refresh/API token default **129600 minutes / 90 days**; access token **one hour**
[DVCFA `[S13]`].

> `[UNVERIFIED]` **The response field name is not documented.** The docs say only that "the
> response returns the access token" and never name the JSON field; the exact `Authorization`
> header format is not stated on the token page either [DAUTH Gap 4]. Read the field off one real
> response and pin it.

### Flow 2 — fleet-wide VCF Identity Broker OAuth `[DOC-9.1]` — new in 9.1

"As of VCF 9.1, VMware offers unified API and CLI access across most VCF components with OAuth
standards-based token authentication, based on VCF Identity Broker (VIDB)" [DVCFA `[S30]`].
Covered components include vCenter, NSX, VCF Operations, Orchestrator, HCX and **VCF Automation**;
VIDB can federate with external IdPs such as Okta and Entra ID [DVCFA `[S30]`].

```
POST https://{vidb.host}/acs/t/{role}/token
Content-Type: application/x-www-form-urlencoded

grant_type=...&api_token={vidb_token}
```

Response: `{"access_token": "{bearer_token}"}`, then `Authorization: Bearer {bearer_token}`
[DVCFA `[S30]`].

> `[UNVERIFIED]` **The `grant_type` literal is elided as `...` in the source page as rendered**
> [DVCFA Gap 1]. The response field name here **is** documented (`access_token`) — unlike the
> tenant flow — but the grant type is not. Read it from the instance or from Broadcom's current
> page before scripting this.

**Token model** [DVCFA `[S30]`]: an **API refresh token** (durable, months-long, revocable) and a
**bearer access token** (short-lived, minutes-long, returned as JSON).

**Four-step architecture** [DVCFA `[S15]`]: administrator creates API clients with credentials
recorded in VIDB → administrator requests a long-lived API refresh token from the VCF Operations
UI → automation script passes the refresh token to VIDB and receives a bearer access token →
script uses the bearer token against VCF components.

**Where clients and tokens are created** [DVCFA `[S17]`]: **Fleet Management > Identity & Access >
VCF SSO Overview** → select identity broker → **API Access > API Clients > Create** (client name,
roles, scope, validity), then the vertical ellipsis → **Generate API Token**. Configurable: API
Token Name, **API Token TTL (default 30 days)**, **Access Token TTL (default 30 mins)**. **"After
you click Continue, you cannot retrieve the API token that was generated"** — capture it at
creation or start over.

**9.0 difference:** this whole flow is 9.1-only. In 9.0, tokens come from the provider portal
under **My Account > API Tokens > NEW**, with the device-authorization grant for provider accounts
[DVCFA delta row 2; `../9.0/vmapps.md`].

## Provider / All-Apps REST conventions worth knowing

From the Broadcom developer portal, marked 9.1/latest [DVCFA `[S19]`, `[S20]`]. These describe the
**provider and All-Apps** REST surface, **not** the VM Apps `/blueprint`, `/catalog` and
`/deployment` paths above — but they are what you will meet the moment a task crosses into
provider administration, and the header deprecation is worth knowing before someone copies an old
script.

- **Resource shape:** `GET /items`, `POST /items` (201), `GET /items/{urn}`, `PUT /items/{urn}`,
  `DELETE /items/{urn}` (204).
- **IDs are full Uniform Resource Names (URNs)**, not bare UUIDs. Code that assumes a UUID shape
  will mis-parse them.
- **Async operations return `202` with a `Location` header** carrying the tracking task URI. Poll
  the URI you were handed rather than constructing one.
- **Content/version negotiation:** `application/json;version=9.1.0`. "Each feature has a version
  in the path element present in its URL", and **up to 5 major versions back are supported** — so
  `version=9.0.0` should remain callable against a 9.1 system.
- **Auth and context headers:** `Authorization` (JWT, the recommended scheme);
  **`x-vcloud-authorization` is deprecated** — this is the only VCF Automation deprecation found
  anywhere in the 9.1 research [DVCFA delta table footnote];
  `X-VMWARE-VCLOUD-TENANT-CONTEXT` for org-scoped operations; `X-VMWARE-VCLOUD-AUTH-CONTEXT` for
  multisite.
- The `x-vcloud-*` header family confirms **VMware Cloud Director lineage** for the provider and
  All-Apps side — which is exactly why it does not look like the Aria-derived VM Apps side.

**Provider REST API categories, 13 of them** [DVCFA `[S31]`]: Access Control, Aggregator,
Approvals, Blueprint, Catalog, Content Gateway, Custom Forms, Custom Resource Types & Actions,
Instances, Orchestrator Gateway, Policies, Projects, Provisioning Service. **The 9.0 page lists
the same 13** [DVCFA `[S33]`] — a summarization pass once flagged two of them as "new in 9.1",
which the 9.0 page contradicts. Treat it as an artifact, not a delta [DVCFA Gap 9].

**9.0 difference:** the portal cannot be pinned to 9.0, so these conventions are tagged 9.1 even
where they are probably true of 9.0 as well [DVCFA Gap 11].

## What's new in 9.1

All from the 9.1 What's New page for VCF Automation [DVCFA `[S09]`]. Mostly **provider-side**;
none of it changes the VM Apps endpoints above, and none of it comes with a documented API path.

**Provider Management (Cloud Administration):**
1. **vDefend Firewall support** — vDefend Distributed Firewall and Gateway Firewall directly
   within VCF Automation, delegable to organizations with RBAC and predefined security profiles.
2. **Default IP block configuration** — providers set default private VPC and private Transit
   Gateway IP blocks, overridable per organization.
3. **Avi Load Balancer support** — full self-service with quota management, for **both All Apps
   and VM Apps** organizations. The one item on this list that touches VM Apps directly.
4. **Multiple external connections** — multiple exit points via centralized connections and
   distributed VLAN connections.
5. **Shared VLAN extension subnets** — shareable across multiple organizations.
6. **External IP blocks** — **IP spaces renamed to external IP blocks**, with multiple CIDRs,
   custom IP ranges and **Infoblox External IPAM** integration. It is a rename; if a user says "IP
   spaces" on 9.1, that is what they mean.
7. **Multi-supervisor region quota** — quota across multiple supervisors in a region, with
   capacity-sharing options.

**Organization Management:**
1. **Namespace allocation changes** — day-2 modification of resource limits, VM classes, storage
   classes and shared subnets.
2. **Project content libraries** — dedicated per-project libraries, spanning multiple projects.
3. **Canonical content libraries** — subscribed libraries providing validated Ubuntu LTS images.
4. **Shared NSX subnets** — org-wide subnets shareable across namespaces.
5. **Transit Gateway configurations** — multiple NSX Transit Gateways with NAT, IPsec VPN and
   vDefend Gateway Firewall.

**Also 9.1:** VCF CLI **v9.1** (9.0 documents v9.0) [DVCFA `[S34]`], and workload types listed as
Kubernetes clusters, VMs, containers as vSphere Pods, secrets, persistent volumes, GPU-enabled
private AI workloads, and **databases via Data Services Manager** — though that list is an LLM
summary of prose in both versions and the apparent drop of "Harbor container registry" is **low
confidence** [DVCFA Gap 10].

## Unverified areas — say so and route to discovery

Identical to 9.0. Real parts of the VM Apps surface with **no verified path**: **Projects**,
**cloud accounts / cloud zones**, **resource / day-2 actions**, **ABX**, and the remaining named
services (Approvals, Policies, Custom Forms, Onboarding, Content Gateway, Identity, Access
Control, Deployment Metric, Provisioning Service, Orchestrator Gateway) [DVCFA `[S08]`, Gaps 4–7].
The honest answer names the service, says the path is not documented in the research, and gives
the discovery route below.

## Discovery routes

1. **In-product API Help Center.** VM Apps: log in as admin to the VM Apps tenant, click the user
   name top-right, open **API Help Center** — a single landing page for all Swagger specs
   [DVCFA `[S08]`]. Service provider / All Apps: **admin > API Help Center > Automation APIs**
   in the upper right [DVCFA `[S31]`, `[S33]`] `[DOC-BOTH]`. Authoritative for that instance, and
   the correct answer to "what is the projects endpoint".
2. **In-product api-docs.** `https://<FQDN>/automation/api-docs/#/<section>` [DVCFA `[S27]`]
   `[DOC-BOTH]`.
3. **Broadcom developer portal.** `https://developer.broadcom.com/xapis/<api-slug>/latest/`.
   **Confirmed slugs:** `org-management-vm-apps-org`, `vm-apps-org-catalog`,
   `all-apps-org-access-control`, `provider-infrastructure-apis` [DVCFA `[S25]`, `[S18]`, `[S20]`,
   `[S19]`]. Slugs such as `vm-apps-org-blueprint` are **inferred, not fetched** [DVCFA Gap 12].
   Each API page carries a **REST API Index** and an **API ChangeLog** — the ChangeLog is the
   right place to diff 9.0 against 9.1 [DVCFA `[S18]`]. Deep-linking into sub-paths returns
   "Object Not Found"; fetch the API page and navigate. The docs state generally: "For detailed
   endpoint specifications, reference documentation is available at `developer.broadcom.com/xapis/`
   for each category" [DVCFA `[S31]`].
4. **Kubernetes-native discovery** — All Apps only: `kubectl --context cci api-resources`
   [DVCFA `[S32]`]. Listed here so you recognise it as the *other* skill's route.
5. **`vcf-api-discovery`** for anything outside VCF Automation.

## Terraform and IaC in 9.1

Same three providers as 9.0, re-scoped [DVCFA `[S27]`]:

1. **Terraform Provider for VCF Automation** — Provider Management UI **and a subset of the
   Organization UI**; "greenfield" examples for fresh installations.
2. **Terraform Provider for Kubernetes** — Organization UI resources exposed through the **VCF
   Automation Kubernetes API layer**, such as projects.
3. **Terraform Provider for VMware Aria Automation** — **the VM Apps one**: VM Apps organizations,
   plus All Apps resources not yet exposed through the Kubernetes API layers, including
   blueprints.

Resources by role [DVCFA `[S27]`]: **provider administrators** — organizations, regions, quotas,
networking, content libraries, supervisor namespaces; **organization administrators (All Apps)** —
projects, content libraries, VPCs, subnets, blueprints, catalogs; **organization users** —
provision IaaS services, deploy catalogs.

For VM Apps blueprints in Terraform, provider 3 is the one. The name still says Aria.

## Ambiguities found while writing this file

1. **Every VM Apps endpoint tag in this file is `[DOC-9.0]`.** That is not an oversight. The 9.1
   leaf tutorial pages were not individually fetched; the guide persists under identical slugs
   [DVCFA `[S05]`, `[S28]`] and no VCF Automation deprecations were found in 9.1, so carry-over is
   the reasonable reading — but it is a reading, not a retrieval. If a change record needs the
   stronger statement, get it from the instance's API Help Center.
2. **The developer portal cannot be pinned to a version.** Every `xapis` page fetched reported
   "9.1 (latest)"; no 9.0-pinned URL pattern exists [DVCFA Gap 11]. So `[DOC-9.1]` on portal facts
   means "the portal says so", not "9.1 only".
3. **The two 9.1 token systems have no documented relationship.** Coexistence is observable;
   precedence and migration are not documented [DVCFA Gap 14]. If a customer is standardising on
   VIDB, that is a question for Broadcom, not an inference to make here.
4. **"Custom Resource Types & Actions" and "Instances" are not new in 9.1**, despite a
   summarization artifact saying so — the 9.0 page lists both [DVCFA Gap 9].
5. **The 9.0 "getting started with the tools" page 404s under 9.1** and its content was
   restructured toward "VMware Cloud Foundation Consumption documentation" [DVCFA delta row 18].
   Do not hand a 9.0 doc URL to a 9.1 user.
