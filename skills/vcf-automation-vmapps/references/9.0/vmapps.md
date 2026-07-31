# VCF 9.0 — VCF Automation for VM Apps Reference

**Scope:** VCF Automation (formerly VMware Aria Automation) in VMware Cloud Foundation 9.0, **VM
Apps organizations only**. For All Apps organizations see `vcf-automation-allapps-k8s`.

**Sources.** `DVCFA` = `research/vcf-automation.md`, whose own `[S##]` refs resolve to its Source
Inventory (all pages accessed 2026-07-31); `DAUTH` = `research/foundation-auth-identity.md`.
Every path below carries its dossier source ref.

**Evidence tags — read these before quoting any path.**

| Tag | Means |
|---|---|
| `[DOC-9.0]` | Printed on a fetched **9.0** documentation page. |
| `[DOC-9.1]` | Printed on a fetched **9.1** page, or on the Broadcom developer portal, which serves only "9.1 (latest)" and has no 9.0-pinned URL pattern [DVCFA Gap 11]. Applicability to 9.0 is **not** established. |
| `[DOC-BOTH]` | Read from pages in **both** doc sets. |
| `[UNVERIFIED]` | Named in the docs but **no path was ever printed on a retrievable page**, or contradicted/elided in the source. Do not emit a path. |

> **There is no OpenAPI specification for VCF Automation in the published corpus at the 9.0.0.0
> tag.** No endpoint in this file is spec-confirmed. This is weaker evidence than every sibling
> skill provides, and it is why the discovery routes at the end of this file matter more here than
> elsewhere. Confirm unverified areas against the customer's own appliance before use.

---

## Contents

- [Prerequisites](#prerequisites)
  - P0 — You are in a VM Apps organization, not an All Apps organization
  - P1 — An API token exists, is unexpired, and has been exchanged for an access token
  - P2 — The project exists and you have its id
  - P3 — The catalog item exists, is shared to the project, and you know its version
  - P4 — The caller holds rights for the operation — UNVERIFIED
  - P5 — Items the research could not verify
- [What a VM Apps organization is](#what-a-vm-apps-organization-is)
- [The 15 VM Apps API services](#the-15-vm-apps-api-services)
- [Verified endpoints — Blueprint / cloud template service](#verified-endpoints--blueprint--cloud-template-service)
- [Verified endpoints — Catalog and Deployment services](#verified-endpoints--catalog-and-deployment-services)
- [Authentication in 9.0](#authentication-in-90)
- [Unverified areas — say so and route to discovery](#unverified-areas--say-so-and-route-to-discovery)
- [Discovery routes](#discovery-routes)
- [Terraform and IaC](#terraform-and-iac)
- [Orchestrator and extensibility](#orchestrator-and-extensibility)
- [Ambiguities found while writing this file](#ambiguities-found-while-writing-this-file)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what must
hold, **how to verify it**, the version it applies to, and whether 9.1 differs.

### P0 — You are in a VM Apps organization, not an All Apps organization `[9.0]`

**Must be true:** the organization you are calling is a **VM Apps** org. VCF Automation 9.0 has
**two organization types, "with different consumption mechanisms"** — All Apps and VM Apps
[DVCFA `[S06]`]. The wrong one is not a variation on the same API; it is a completely different
API. Nothing else in this file applies if you are in an All Apps org.

**How to verify:**
- The VM Apps tenant portal presents nine tabs: **Home, Consume, Design, Infrastructure, Content
  and Policies, Extensibility, Orchestrator, Alerts, Inbox** [DVCFA `[S22]`].
- Documented capability discriminator: **"ABX, Deployment, Deployment Metrics, Identity, and
  Onboarding (available only in VCF Automation for VM Apps)"** [DVCFA `[S33]`]. If the org exposes
  a Deployment service, it is a VM Apps org.
- All Apps is driven through Kubernetes CRDs — `kubectl --context cci api-resources`, API group
  `infrastructure.cci.vmware.com` [DVCFA `[S32]`, a 9.1 page]. If that is how the caller's team
  works, they are not in a VM Apps org.
- Both org types are reached on the same FQDN: `https://FQDN/automation` for tenant users,
  `https://FQDN/provider` for service-provider administrators [DVCFA `[S07]`] `[DOC-BOTH]`.

**9.1 difference:** none. The two org types and both UI surfaces are documented identically in 9.1
[DVCFA `[S29]`, `[S21]`].

### P1 — An API token exists, is unexpired, and has been exchanged for an access token `[9.0]`

**Must be true:** you hold a current **API token (the refresh token)** for the VM Apps
organization, and you have exchanged it for an **access token**. Documented lifetimes: refresh
token default **129600 minutes / 90 days**; access token default **one hour** [DVCFA `[S12]`;
DAUTH]. "In the REST API, VCF Automation requires an HTTP authentication token in the
Authorization request header" [DVCFA `[S12]`].

**How to verify:** perform the documented three-step flow [DVCFA `[S12]`]: find the VM Apps
organization name in the Provider Management Portal; obtain the API token for that organization
from the VM Apps tenant ("The API token for the organization is the refresh token"); exchange it
for an access token. Then make one cheap read — `GET /catalog/api/items/{id}/versions` — and
confirm it does not 401.

Full endpoint and body in [Authentication in 9.0](#authentication-in-90).

**9.1 difference:** the VM Apps flow is **unchanged** — same page, same lifetimes, same three
steps [DVCFA delta row 3]. 9.1 **adds** a second, fleet-wide route via VCF Identity Broker; see
`../9.1/vmapps.md`.

### P2 — The project exists and you have its id `[9.0]`

**Must be true:** the target **project** exists before you create a deployment. `projectId` is a
body field on **both** documented write paths — blueprint creation [DVCFA `[S24]`] and the
catalog item request [DVCFA `[S23]`]. Projects are "organizational units grouping developers with
cloud zones and resources" [DVCFA `[S22]`], and the Projects service exists in the API service
list: "Provide visibility and isolation of provisioned resources" [DVCFA `[S08]`].

**How to verify — and this is where the evidence stops.** `[UNVERIFIED]` **The Projects API base
path was never printed on any retrievable page** in either version. The tutorial pages "Managing
Your Projects" and "Create a Project with the Project Service API" are landing pages with no
paths, and their leaf children were not retrievable within Broadcom's rate limits [DVCFA `[S37]`,
Gap 4]. So:

- Read the project id from the **Infrastructure** tab of the VM Apps tenant portal, or
- Look up the Projects service in the **in-product API Help Center** (see
  [Discovery routes](#discovery-routes)), which is authoritative for that instance.

**Do not construct a projects path from an Aria Automation 8.x memory.** See P5.

**9.1 difference:** none established — the gap is identical in 9.1.

### P3 — The catalog item exists, is shared to the project, and you know its version `[9.0]`

**Must be true, three things:**

1. The catalog item exists. The Catalog service "Access catalog items and catalog sources,
   **including content sharing**" [DVCFA `[S08]`]; the catalog is "a simplified interface for
   users to request pre-built templates" [DVCFA `[S22]`].
2. **The item is shared to the project you are deploying into.** Content sharing is what makes an
   item requestable by a project's members; an item that exists but is not shared behaves, for
   that project, like an item that does not exist. `[UNVERIFIED]` **No sharing endpoint path was
   printed on any retrievable page** — only the capability is documented [DVCFA `[S08]`].
3. You know which **version** to request. `version` is a required-looking field in the request
   body [DVCFA `[S23]`].

**How to verify:**
- `GET /catalog/api/items/{catalogItemId}/versions` `[DOC-9.0]` [DVCFA `[S23]`] — lists the
  available versions of the item, and incidentally proves the item is visible to your token.
- `GET /catalog/api/items` with OData-style query parameters `[DOC-9.1]` [DVCFA `[S18]`] — the
  collection endpoint is documented on the developer portal (9.1/latest only); supported
  parameters `$orderby`, `$top`, `$skip`, plus `page` and `size`, e.g.
  `/catalog/api/items?$orderby=name%20desc`. Serviceable as a 9.0 listing route, but note the tag:
  the portal page is 9.1/latest and no 9.0-pinned portal URL exists [DVCFA Gap 11].
- For sharing state itself, use the UI (**Content and Policies**) or the API Help Center.

**9.1 difference:** none established for the item/version paths; the OData parameters are
documented on the 9.1/latest portal and are stated there without a version caveat.

### P4 — The caller holds rights for the operation `[9.0]` — UNVERIFIED

**Must be true:** the account behind the token holds the rights needed for the operation —
particularly the write paths (`POST /blueprint/api/blueprints`,
`POST /catalog/api/items/{id}/request`).

> `[UNVERIFIED]` **No per-operation privilege requirement is documented for VM Apps API
> operations** in any fetched page. What *is* documented is the 9.1 role model [DAUTH `[S50]`]:
> rights are per-object-type view/manage grants, roles are sets of rights, **provider roles** are
> exclusive to the provider org, **global roles** are published by System Administrators to
> organizations, **organization-specific roles** are created locally by org admins and contain
> only a subset of organization rights, and **System Administrator** exists only in the provider
> org. That tells you the shape of the model; it does not tell you which right gates a catalog
> request. Do not name a required role in a runbook or a service-account request without checking
> it against the customer's own instance.

### P5 — Items the research could not verify — state these as gaps

- **Projects API path** — never printed on a retrievable page. See P2 [DVCFA Gap 4].
- **Cloud accounts and cloud zones API paths** — same situation. "Setting up VCF Automation using
  APIs" and "Using VCF Automation APIs to Build your Resource Infrastructure" are landing pages;
  their leaf pages were not retrieved [DVCFA `[S38]`, Gap 5].
- **The Aria-era IaaS base path** — **never confirmed in any fetched 9.0 or 9.1 page and must not
  be assumed** [DVCFA Gap 5]. This is the single most likely hallucination in this subject area.
  It is a memory of Aria Automation 8.x, not a documented VCF 9.x fact.
- **Resource / day-2 action paths** — "Working with Deployments and Resources" returned HTTP 429
  on every attempt. The developer portal lists **Deployment Actions** as a category, but no
  concrete path was verified [DVCFA Gap 6, `[S18]`].
- **ABX API base path** — the service is named and described but no path was verified
  [DVCFA Gap 7].
- **Access-token response field name** — the docs say the response "returns the access token" but
  **never name the JSON field**; the exact `Authorization` header format is likewise not stated on
  the token page [DAUTH Gap 4]. OAuth convention suggests an answer; that is not documentation.
- **Pipelines / Code Stream** — no VCF Automation pipelines component appeared in any fetched page
  in either version. Whether it was dropped in the Aria→VCF transition or lives elsewhere is
  **unresolved**; do not assert either way [DVCFA Gap 8].
- **Deployment status vocabulary and polling cadence** — no terminal-state list, no failure-state
  list, no recommended interval on any retrieved page.

---

## What a VM Apps organization is

"VCF Automation for VM Apps is a blueprint development and deployment service" using
cloud-templates-as-code in a dev-to-production workflow [DVCFA `[S22]`]. Terminology, verbatim
from the 9.0 docs [DVCFA `[S22]`]:

| Term | Definition |
|---|---|
| Cloud Accounts | Connections to public and private cloud providers |
| Cloud Zones | Specific regions or datastores designated for deployment |
| Projects | Organizational units grouping developers with cloud zones and resources |
| Blueprints | Templates developed using canvas and YAML editor |
| Catalog | Simplified interface for users to request pre-built templates |
| Deployments | Provisioned instances of blueprints across cloud resources |
| Policies | Rules defining cloud zone access and governance |
| Extensibility | Framework for extending application lifecycles through event subscriptions |
| Orchestrator | VCF Operations Orchestrator integration for workflow automation |

> **"Cloud templates" and "blueprints" are the same thing.** Both terms are in active use in the
> 9.0 doc set — the tutorial section is titled "Working with Blueprints/Cloud Templates" and the
> service and resource are named `blueprint` [DVCFA `[S08]`, `[S24]`, `[S35]`]. Mirror the user's
> term; do not correct them.

## The 15 VM Apps API services

Verbatim service list and descriptions [DVCFA `[S08]`]; the same 15 appear on the developer
portal's VM Apps Org index [DVCFA `[S25]`].

| Service | Description |
|---|---|
| ABX | "Create or manage actions and their versions. Execute actions and flows." |
| Access Control | "Supports identity operations for VCF Automation, enabling management of groups and users." |
| Approvals | "Enforce policies that control required approvals for a deployment or Day 2 action." |
| Blueprint | "Create, validate, and provision blueprints." |
| Catalog | "Access catalog items and catalog sources, including content sharing." |
| Content Gateway | "Connect to your infrastructure as code content in external content sources." |
| Custom Forms | "Define dynamic form rendering in Catalog and VCF Automation services." |
| Deployment | "Access deployment objects and platforms or blueprints deployed into the system." |
| Deployment Metric | "Aggregated metric values for the deployment objects." |
| Identity | "Authenticate and manage the authorization provider." |
| Onboarding | "Define policies and plans to bring existing VMs from any cloud." |
| Orchestrator Gateway | "Run workflows and actions to automate complex IT tasks." |
| Policies | "Interact with policies created in Catalog." |
| Projects | "Provide visibility and isolation of provisioned resources." |
| Provisioning Service | "Perform infrastructure setup tasks, including validation and provisioning." |

**A named service is not a known path.** Only Blueprint, Catalog and Deployment have printed
paths. The other twelve are names with descriptions — route them to discovery.

## Verified endpoints — Blueprint / cloud template service

Base path `$url/blueprint/api`. All from a single fetched 9.0 tutorial page [DVCFA `[S24]`].

| Method | Path | Purpose | Tag |
|---|---|---|---|
| POST | `/blueprint/api/blueprints` | Create a cloud template | `[DOC-9.0]` |
| GET | `/blueprint/api/blueprints` | List cloud templates | `[DOC-9.0]` |
| GET | `/blueprint/api/blueprints?name=$cloud_template_name` | Filter by name | `[DOC-9.0]` |
| PUT | `/blueprint/api/blueprints/{cloud_template_id}` | Update a cloud template | `[DOC-9.0]` |
| POST | `/blueprint/api/blueprint-validation` | Validate a cloud template | `[DOC-9.0]` |

**Create body fields observed** [DVCFA `[S24]`]: `name`, `description`, `content` (the YAML
template as a string — `formatVersion: 1`, `inputs:`, `resources:` with e.g.
`type: Cloud.Machine`), `projectId`, `requestScopeOrg`.

**Headers observed:** `Content-Type: application/json`, `Authorization: Bearer $access_token`
[DVCFA `[S24]`]. This is the only place in the research where the `Bearer` prefix appears in a
worked VM Apps example — the token page itself does not state the header format [DAUTH Gap 4].

**Not documented:** a delete path, a versions/release path for blueprints, and the response shape
of the validation call. Do not invent them.

## Verified endpoints — Catalog and Deployment services

All from a single fetched 9.0 tutorial page [DVCFA `[S23]`], except where tagged otherwise.

| Method | Path | Purpose | Tag |
|---|---|---|---|
| POST | `/catalog/api/items/{catalogItemId}/request` | Request a deployment from a catalog item | `[DOC-9.0]` |
| GET | `/catalog/api/items/{catalogItemId}/versions` | List available versions | `[DOC-9.0]` |
| GET | `/deployment/api/deployments` | Query existing deployments | `[DOC-9.0]` |
| GET | `/deployment/api/deployments/{deploymentId}` | Check deployment status | `[DOC-9.0]` |
| GET | `/catalog/api/items` | List catalog items; `$orderby`, `$top`, `$skip`, `page`, `size` | `[DOC-9.1]` |

**Request body fields** [DVCFA `[S23]`]: `deploymentName`, `projectId`, `catalogItemId`,
`version`, `inputs` (an object of runtime variables — the documented example uses `count`,
`image`, `flavor`, which are that blueprint's inputs, not a fixed schema).

**Worked sequence** — the full request-and-poll example lives in `../../SKILL.md` Step 4 and uses
only the paths above.

> **Requesting a catalog item provisions real infrastructure** against the project's cloud zones
> and quota. It is not a read. Confirm the project, the item and the inputs before sending, and
> note that no rollback or cancel path is documented anywhere in this research.

**Two gaps inside the happy path**, both worth stating to a user rather than papering over:
- **How the deployment id is returned by the request call is not shown** on the fetched page. Use
  `GET /deployment/api/deployments` to find the deployment if the response does not obviously
  carry it.
- **No status vocabulary and no polling interval are documented.** Read the statuses off the
  instance rather than asserting a state machine.

## Authentication in 9.0

Two documented flows in 9.0. They are different endpoints with different grant types.

### Flow 1 — VM Apps tenant access token `[DOC-BOTH]`

Printed verbatim on a 9.0 page [DVCFA `[S14]`; DAUTH]; the delta table records the flow as
unchanged in 9.1 [DVCFA delta row 3, `[S13]`].

```
POST https://{{vcfaHostname}}/tm/oauth/tenant/{{vcfaTenant}}/token
Content-Type: application/x-www-form-urlencoded
Accept: application/json

grant_type=refresh_token&refresh_token={{vcfaAPIToken}}
```

"The response returns an access token… The access token is the API bearer token that is required
to access tenant-specific APIs" [DVCFA `[S14]`], then sent as `Authorization: Bearer <token>`.

> `[UNVERIFIED]` **The response field name is not documented.** DAUTH records it explicitly:
> the docs say "The response returns the access token" but **do not name the JSON field**, and the
> exact `Authorization` header format is not stated on the token page [DAUTH Gap 4]. The `Bearer`
> prefix *is* observed in the blueprint curl examples [DVCFA `[S24]`], so the header format is on
> firmer ground than the field name. Read the field off one real response and pin it; do not
> assert it in advance.

**Lifetimes:** API token (refresh token) default **129600 minutes / 90 days**; access token
default **one hour** [DVCFA `[S12]`; DAUTH].

### Flow 2 — Provider (service-provider account) device-authorization grant `[DOC-9.0]`

For **provider** accounts, not tenant users. Four steps plus a refresh [DVCFA `[S16]`]:

1. Create the refresh token in the UI: `https://<vcfa.url>/provider` → **My Account > API Tokens
   > NEW**, using the service administrator's username.
2. Request device authorization:
   ```
   POST https://<vcfa.url>/tm/oauth/tenant/<organization>/device_authorization
   Content-Type: application/x-www-form-urlencoded
   client_id=<serviceAdminUserName>
   ```
   The response includes `user_code` and `device_code`.
3. **Approve it by hand:** **Service Accounts** tab → "Review Access Requests" → paste the
   `user_code` → **GRANT**. There is a human in this loop; it is not scriptable end to end.
4. Exchange for an access token:
   ```
   POST https://<vcfa.url>/tm/oauth/tenant/<organization>/token
   Content-Type: application/x-www-form-urlencoded
   grant_type=urn:ietf:params:oauth:grant-type:device_code
   refresh_token=<refresh_token>&client_id=<username>&device_code=<device_code>
   ```
   Returns `access_token`, valid one hour.
5. Refresh when expired — **and note the inconsistency**: the refresh step is printed with **no
   `/tm` prefix**, `https://<vcfa.url>/oauth/tenant/<org>/token`, with
   `grant_type=refresh_token&refresh_token=<refreshToken>` [DVCFA `[S16]`].

> `[UNVERIFIED]` **The `/tm` prefix inconsistency is reproduced verbatim from the source and is
> not resolvable from the fetched page** [DVCFA Gap 2]. Steps 2–4 use `/tm/oauth/...`; step 5 does
> not. Test both before depending on either, and tell the user the doc is internally inconsistent
> rather than silently picking one.

**9.1 difference:** the token-administration UI moves — 9.1 issues API clients and tokens from
**Fleet Management > Identity & Access > VCF SSO Overview > API Access** [DVCFA delta row 2,
`[S17]`] — and 9.1 adds the fleet-wide identity-broker flow. See `../9.1/vmapps.md`.

## Unverified areas — say so and route to discovery

These are real parts of the VM Apps surface with **no verified path**. The honest answer names the
service, says the path is not documented in the research, and gives the discovery route.

| Area | What is documented | What is not | Ref |
|---|---|---|---|
| **Projects** | Service name and purpose; `projectId` consumed by two write bodies | Any path | `[S08]`, Gap 4 |
| **Cloud accounts / cloud zones** | Concepts and UI location (Infrastructure tab) | Any path — and **the Aria-era IaaS base path was never confirmed** | `[S22]`, Gap 5 |
| **Resource / day-2 actions** | "Deployment Actions" exists as a portal category | Any path; source page 429'd on every attempt | `[S18]`, Gap 6 |
| **ABX** | Service name and purpose ("actions and their versions… flows") | Any path | `[S08]`, Gap 7 |
| **Approvals, Policies, Custom Forms, Onboarding, Content Gateway, Identity, Access Control, Deployment Metric, Provisioning Service** | Names and one-line purposes | Any path | `[S08]` |

## Discovery routes

In priority order. The first is authoritative for the instance you are actually calling.

1. **In-product API Help Center (VM Apps).** "To access all Swagger specifications from a single
   landing page, log in as admin to the VCF Automation for VM Apps Organization tenant. At the
   top-right corner of the home page, click the user name and open the **API Help Center**"
   [DVCFA `[S08]`]. This is the correct answer to "what is the projects endpoint".
2. **In-product api-docs.** `https://<FQDN>/automation/api-docs/#/<section>` — verified as the
   location of the Terraform provider examples in both versions, and the `#/<section>` shape is
   the discoverable pattern [DVCFA `[S26]`, `[S27]`] `[DOC-BOTH]`.
3. **Broadcom developer portal.** `https://developer.broadcom.com/xapis/<api-slug>/latest/`.
   **Confirmed slugs only:** `org-management-vm-apps-org` (master index of all 15 VM Apps Org
   APIs), `vm-apps-org-catalog` (Catalog Items, Catalog Item Types, Catalog Admin Items,
   Deployments, Deployment Actions, Requests), `all-apps-org-access-control`,
   `provider-infrastructure-apis` [DVCFA `[S25]`, `[S18]`, `[S20]`, `[S19]`]. Slugs such as
   `vm-apps-org-blueprint` are **inferred from the pattern, not fetched** [DVCFA Gap 12] — try
   them, but do not present them as documented. Each portal API page carries a **REST API
   Index** and an **API ChangeLog**; the ChangeLog is the right place to diff 9.0 against 9.1
   [DVCFA `[S18]`].
   - Deep-linking into portal sub-paths does not work — it returns "Object Not Found" [DVCFA
     retrieval failures]. Fetch the API page and navigate.
   - Every portal page fetched reported "9.1 (latest)"; **no 9.0-pinned URL pattern was
     discovered**, so portal facts cannot be attributed to 9.0 [DVCFA Gap 11].
4. **`vcf-api-discovery`** for anything outside VCF Automation.

## Terraform and IaC

Three open-source Terraform providers are documented as required for end-to-end operations
[DVCFA `[S26]`]:

1. **Terraform Provider for VCF Automation** — CRUD for Provider Management Portal and
   Organization Portal resources: organizations, regions, region quotas, networking, content
   libraries, supervisor namespaces. A "greenfield" folder holds provider and tenant samples.
2. **Terraform Provider for Kubernetes** — Organization Portal resources through the Kubernetes
   API: projects, content libraries, virtual private clouds, subnets.
3. **Terraform Provider for VMware Aria Automation** — **this is the VM Apps one**: operations for
   VM Apps organizations and resources not exposed through the Kubernetes API. Resources:
   blueprints, catalogs.

If a user wants VM Apps blueprints in Terraform, provider 3 is the one — the name still says Aria.

## Orchestrator and extensibility

- **Orchestrator** is a first-class tab in the VM Apps org UI: "VCF Operations orchestrator
  integration for workflow automation" [DVCFA `[S22]`].
- An **Orchestrator Gateway** API service exists — "Run workflows and actions to automate complex
  IT tasks" [DVCFA `[S08]`, `[S25]`] — but no path is documented. `[UNVERIFIED]`
- Orchestrator is documented as **VCF Operations Orchestrator**, a separate component from VCF
  Automation; the 9.0 doc tree points at
  `configuration-of-vmware-cloud-foundation-operations-orchestrator.html` [DVCFA `[S01]`]. Do not
  describe it as a VCF Automation subcomponent.
- **Extensibility** is defined as a "framework for extending application lifecycles through event
  subscriptions" [DVCFA `[S22]`], and **ABX** as "create or manage actions and their versions.
  Execute actions and flows" [DVCFA `[S08]`]. Concepts documented; paths not. `[UNVERIFIED]`

## Ambiguities found while writing this file

1. **Doc-set versioning of the tutorial pages.** The blueprint, catalog and deployment paths all
   come from **9.0** tutorial pages [DVCFA `[S23]`, `[S24]`]. The 9.1 doc set carries the "VMware
   Cloud Foundation Automation APIs for VM Apps Programming Guide" under **identical slugs**
   [DVCFA `[S05]`, `[S28]`], but the 9.1 leaf pages were not individually fetched. Carrying these
   paths into 9.1 is reasonable and is how `../9.1/vmapps.md` presents them — as `[DOC-9.0]`
   evidence, not as 9.1-confirmed.
2. **The developer portal cannot be pinned to 9.0.** Everything from `developer.broadcom.com` is
   tagged `[DOC-9.1]` for that reason alone, including the catalog OData parameters. They very
   likely apply to 9.0; "likely" is not "documented" [DVCFA Gap 11].
3. **"Advanced Services" is not a VCF Automation feature.** In the 9.0 doc tree it is a list of
   add-on products — Live Recovery, Data Services Manager, Private AI Foundation with NVIDIA,
   vDefend, Avi Load Balancer, Tanzu, Network Observability [DVCFA `[S04]`]. If a user says
   "advanced services", check which they mean.
4. **The 9.0 "getting started with the tools" page does not exist in 9.1** — it 404s under 9.1 and
   the content was restructured [DVCFA delta row 18]. Do not hand a 9.0 doc URL to a 9.1 user.
