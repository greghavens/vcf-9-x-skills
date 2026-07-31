# VCF Automation — Research Dossier (VCF 9.0 and 9.1)

Research date: **2026-07-31**. Every claim below carries a bracketed source ref (`[S##]`)
resolving to the Source Inventory at the bottom, plus a version tag `[9.0]`, `[9.1]`, or
`[9.0+9.1]`. `[9.0+9.1]` is used **only** where the same fact was read from both doc sets.

> Method note: all facts come from pages fetched during this task. Nothing is drawn from
> prior model knowledge. Where a page could not be retrieved, it is recorded as
> `UNVERIFIED — could not retrieve` in **Gaps and Ambiguities**.

---

## VCF Automation in VCF 9.0

### What it is

- "VMware Cloud Foundation Automation (formerly VMware Aria Automation) or VCF Automation
  enables IT teams and cloud service providers (CSPs) to deliver a self-service private cloud
  for AI, Kubernetes, and VM-based applications." `[9.0]` `[S10]`
  - The rename from Aria Automation is stated explicitly in the docs, so the lineage is
    confirmed rather than assumed. `[9.0]` `[S10]`
- Four functional areas named in the overview `[9.0]` `[S10]`:
  1. **Cloud Services** — "Provides a set of cloud services to meet the needs of application
     teams," consumed via UI, CLI, and API.
  2. **Provider Management** — for infrastructure teams managing/scaling services "across
     multiple vCenter and VCF instances."
  3. **Organization Management** — org admins "organize and govern resources allocated to them
     among application teams."
  4. **vSphere Supervisor** — "running Kubernetes workloads directly on ESX hosts and creating
     upstream Kubernetes clusters within dedicated namespaces."
- Consumption framing: VCF Automation lets you "provision VMs, Kubernetes workloads and other
  Cloud Services by using self-service UI, API, and CLI." `[9.0]` `[S03]`

### The central 9.0 concept: two organization types

This is the single most important structural fact for 9.0, and it drives everything about API
surface and auth.

- Two organization types exist: **All Apps organizations** and **VM Apps organizations**, "with
  different consumption mechanisms." `[9.0]` `[S06]`
- The **VM Apps** org is the Aria-Automation-derived surface: blueprints, catalog, deployments,
  projects, cloud accounts, cloud zones, extensibility/ABX, Orchestrator. `[9.0]` `[S22]`
- The **All Apps** org is the newer Kubernetes/VCD-derived surface, driven by CRDs and
  supervisor namespaces. `[9.0]` `[S07]` `[S32 for 9.1 detail]`

### UI surfaces

- Two web surfaces on the same FQDN `[9.0+9.1]` `[S07]` `[S29]`:
  - `https://FQDN/provider` — service provider administrators (Provider Management Portal).
  - `https://FQDN/automation` — tenant organization users (Automation Portal).
- Tools for building applications `[9.0]` `[S06]`:
  - **VCF Automation UI** — self-service interface, includes the catalog.
  - **Self-service catalog** — "The catalog in VCF Automation for All Apps is the self-service
    interface where you can provision workloads from blueprints."
  - **IaaS Services Console** — modern services enabled by vSphere Supervisor; provision "VMs,
    Kubernetes, volumes, storage, load balancers and networking objects."
  - **VCF CLI v9.0** — CLI for VCF Consumption services. `[9.0]` `[S06]`
  - **Local Consumption Interface** — alternative for environments without VCF Automation access.

### VM Apps organization: terminology and UI tabs `[9.0]` `[S22]`

VCF Automation for VM Apps is "a blueprint development and deployment service" using
cloud-templates-as-code in a dev-to-production workflow.

| Term | Definition (per 9.0 docs) |
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

UI tabs in the VM Apps org portal `[9.0]` `[S22]`: **Home**, **Consume**, **Design**,
**Infrastructure**, **Content and Policies**, **Extensibility**, **Orchestrator**, **Alerts**,
**Inbox**.

> **Terminology note — "cloud templates" vs "blueprints":** both terms are in active use in the
> 9.0 doc set. The API tutorial section is titled "Working with Blueprints/Cloud Templates" and
> the underlying API service and resource are named `blueprint` / `/blueprint/api/blueprints`.
> `[9.0]` `[S08]` `[S24]`

> **Pipelines:** no VCF Automation "pipelines" component (the old Code Stream / Automation
> Pipelines) was found in any 9.0 page fetched. See **Gaps**.

### Authentication — VM Apps API `[9.0]`

- "In the REST API, VCF Automation requires an HTTP authentication token in the Authorization
  request header." `[9.0+9.1]` `[S12]` `[S13]`
- Two token types `[9.0+9.1]` `[S12]` `[S13]`:
  - **Refresh token (a.k.a. API token)** — default lifespan "129600 minutes or 90 days".
  - **Access token** — default lifespan "one hour".
- Documented three-step flow `[9.0+9.1]` `[S12]` `[S13]`:
  1. Log in to the VCF Automation Provider Management Portal to find the name of the VM Apps
     organization.
  2. Log in to the VM Apps tenant to get the API token for the organization. "The API token for
     the organization is the refresh token."
  3. Exchange the refresh token for an access token (API client such as Postman, or a
     registered OAuth Client for customizable expiration).

**Verified token exchange endpoint (VM Apps):** `[9.0]` `[S14]`

```
POST https://{{vcfaHostname}}/tm/oauth/tenant/{{vcfaTenant}}/token
Content-Type: application/x-www-form-urlencoded
Accept: application/json

grant_type=refresh_token&refresh_token={{vcfaAPIToken}}
```

The response returns an access token; "The access token is the API bearer token that is required
to access tenant-specific APIs." It is then sent as `Authorization: Bearer <access_token>`.
`[9.0]` `[S14]` — bearer usage also visible in the blueprint curl examples `[S24]`.

**Verified provider (service-provider account) token flow — device authorization grant:** `[9.0]` `[S16]`

1. Create the refresh token in the UI: `https://<vcfa.url>/provider` → **My Account > API Tokens
   > NEW**, using the service administrator's username.
2. Request device authorization:
   ```
   curl -k 'https://<vcfa.url>/tm/oauth/tenant/<organization>/device_authorization' \
     --header 'Content-Type: application/x-www-form-urlencoded' \
     --data-urlencode 'client_id=<serviceAdminUserName>'
   ```
   Response includes `user_code` and `device_code`.
3. Approve: **Service Accounts** tab → "Review Access Requests" → paste `user_code` → **GRANT**.
4. Exchange for access token:
   ```
   curl -k 'https://<vcfa.url>/tm/oauth/tenant/<organization>/token' \
     --header 'Content-Type: application/x-www-form-urlencoded' \
     --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:device_code' \
     --data-urlencode 'refresh_token=<refresh_token>' \
     --data-urlencode 'client_id=<username>' \
     --data-urlencode 'device_code=<device_code>'
   ```
   Returns `access_token`, valid one hour.
5. Refresh when expired (note: **this step's path omits `/tm`** as printed in the doc):
   ```
   curl --location 'https://<vcfa.url>/oauth/tenant/<org>/token' \
     --header 'Content-Type: application/x-www-form-urlencoded' \
     --data-urlencode 'grant_type=refresh_token' \
     --data-urlencode 'refresh_token=<refreshToken>'
   ```
   The `/tm` vs no-`/tm` inconsistency is reproduced verbatim from the source; treat as
   ambiguous (see **Gaps**). `[9.0]` `[S16]`

### API services available in the VM Apps org `[9.0]` `[S08]`

Verbatim service list and descriptions:

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

The same 15 services are enumerated on the Broadcom Developer Portal VM Apps Org index as
`VM Apps Org - ABX`, `- Access Control`, `- Approval`, `- Blueprint`, `- Catalog`,
`- Content Gateway`, `- Custom Forms`, `- Deployment`, `- DeploymentMetric`, `- Identity`,
`- Onboarding`, `- Orchestrator Gateway`, `- Policies`, `- Project`, `- Provisioning Service`.
`[9.0+9.1 — portal is version-agnostic "latest"]` `[S25]`

### Verified API base paths and endpoint templates `[9.0]`

Only paths actually read from a fetched page are listed.

**Blueprint / cloud template service** — base path `$url/blueprint/api` `[9.0]` `[S24]`

| Method | Path | Purpose |
|---|---|---|
| POST | `/blueprint/api/blueprints` | Create a cloud template |
| GET | `/blueprint/api/blueprints` | List cloud templates |
| GET | `/blueprint/api/blueprints?name=$cloud_template_name` | Filter by name |
| PUT | `/blueprint/api/blueprints/{cloud_template_id}` | Update a cloud template |
| POST | `/blueprint/api/blueprint-validation` | Validate a cloud template |

Create body fields observed: `name`, `description`, `content` (YAML-as-string, `formatVersion: 1`,
`inputs:`, `resources:` with e.g. `type: Cloud.Machine`), `projectId`, `requestScopeOrg`.
Headers: `Content-Type: application/json`, `Authorization: Bearer $access_token`. `[9.0]` `[S24]`

**Catalog + Deployment services** `[9.0]` `[S23]`

| Method | Path | Purpose |
|---|---|---|
| POST | `/catalog/api/items/{catalogItemId}/request` | Request a deployment from a catalog item |
| GET | `/catalog/api/items/{catalogItemId}/versions` | List available versions |
| GET | `/deployment/api/deployments` | Query existing deployments |
| GET | `/deployment/api/deployments/{deploymentId}` | Check deployment status |

Request-deployment body fields: `deploymentName`, `projectId`, `catalogItemId`, `version`,
`inputs` (object of runtime variables, e.g. `count`, `image`, `flavor`). `[9.0]` `[S23]`

**Catalog collection query parameters** (from the API reference): collection endpoints support
OData-like `$orderby`, `$top`, `$skip`, plus `page` and `size`; documented example
`/catalog/api/items?$orderby=name%20desc`. `[9.1 doc-set "latest"]` `[S18]`

### Terraform / IaC integration `[9.0]` `[S26]`

VCF Automation documents **three** open-source Terraform providers required for end-to-end
operations:

1. **Terraform Provider for VCF Automation** — CRUD for Provider Management Portal and
   Organization Portal resources. On GitHub and the HashiCorp Terraform registry. Resources:
   organizations, regions, region quotas, networking, content libraries, supervisor namespaces.
   A "greenfield" folder holds provider and tenant configuration samples.
2. **Terraform Provider for Kubernetes** — CRUD against VCF Automation Organization Portal
   resources through the Kubernetes API. Resources: projects, content libraries, virtual private
   clouds, subnets.
3. **Terraform Provider for VMware Aria Automation** — operations for VM Apps organizations and
   resources not exposed through the Kubernetes API. Resources: blueprints, catalogs.

Usage examples surface: `https://<FQDN>/automation/api-docs/#/terraform-provider` `[9.0]` `[S26]`

### Orchestrator integration `[9.0]`

- **Orchestrator** is a first-class tab in the VM Apps org UI, described as "VCF Operations
  orchestrator integration for workflow automation." `[9.0]` `[S22]`
- An **Orchestrator Gateway** API service exists: "Run workflows and actions to automate complex
  IT tasks." `[9.0]` `[S08]` `[S25]`
- Workload Orchestration in the VCF 9.0 doc tree points at
  `configuration-of-vmware-cloud-foundation-operations-orchestrator.html` — i.e. Orchestrator is
  documented as **VCF Operations Orchestrator**, a separate component from VCF Automation.
  `[9.0]` `[S01]`

### Advanced Services (scope clarification) `[9.0]` `[S04]`

"Advanced Services" in the VCF 9.0 doc tree is **not** a VCF Automation sub-feature. It is a list
of add-on products: VMware Live Recovery Suite, Data Services Manager, Private AI Foundation with
NVIDIA, vDefend, Avi Load Balancer, Tanzu Platform & Tanzu Data, Network Observability. Relevant
to VCF Automation only insofar as several become consumable services in later versions. `[9.0]` `[S04]`

---

## VCF Automation in VCF 9.1

### What it is

- Same core definition, verbatim identical to 9.0: "VMware Cloud Foundation Automation (formerly
  VMware Aria Automation) or VCF Automation enables IT teams and cloud service providers (CSPs) to
  deliver a self-service private cloud for AI, Kubernetes, and VM-based applications." `[9.1]` `[S11]`
- Adds value-proposition wording not present in the 9.0 overview: it "simplifies the process of
  provisioning and scaling a multi-tenant private cloud with out-of-the-box Infrastructure as a
  Service (IaaS) offerings," with policy-based governance. `[9.1]` `[S11]`
- Four components again, but **Organization Management is re-worded**: 9.0 says org admins
  "organize and govern resources allocated to them among application teams"; 9.1 says org admins
  "create and assign projects and vSphere Namespaces tailored for different application teams."
  `[9.1]` `[S11]` vs `[9.0]` `[S10]`

### UI surfaces and tooling

- `https://FQDN/provider` and `https://FQDN/automation` unchanged. `[9.1]` `[S29]`
- **VCF CLI v9.1** (the 9.0 doc set names v9.0). `[9.1]` `[S34]`
- Workload types listed on the 9.1 Building Cloud Applications page: Kubernetes clusters, virtual
  machines, containers as vSphere Pods, secrets, persistent volumes, GPU-enabled private AI
  workloads/clusters, and **databases via Data Services Manager**. `[9.1]` `[S34]`

### VM Apps organization: terminology and UI tabs `[9.1]` `[S21]`

Definition and tab set are materially the same as 9.0 — **Home**, **Consume**, **Design**,
**Infrastructure**, **Content and Policies**, **Extensibility**, **Orchestrator**, **Alerts**,
**Inbox**. `[9.1]` `[S21]`

One wording change worth noting: in 9.1 the Blueprints entry is described as templates that may be
"VCF or AWS CloudFormation" and that "administrators can import for reuse." `[9.1]` `[S21]`

### All Apps organization: Kubernetes-native management `[9.1]` `[S32]`

The 9.1 doc set documents org management for All Apps through Kubernetes CRDs and `kubectl`.

- API group observed: `infrastructure.cci.vmware.com/v1alpha2` `[9.1]` `[S32]`
- kubectl context name: `cci` — discover resources with `kubectl --context cci api-resources`
  `[9.1]` `[S32]`
- Example `SupervisorNamespace` manifest `[9.1]` `[S32]`:
  ```yaml
  apiVersion: infrastructure.cci.vmware.com/v1alpha2
  kind: SupervisorNamespace
  metadata:
    generateName: test
    namespace: default-project
  spec:
    regionName: e2e-region
    className: e2e-small
    vpcName: e2e-region-default-vpc
  ```
- Resource/permission matrix `[9.1]` `[S32]`:

  | Resource | Admin | DevOps |
  |---|---|---|
  | Project | Full CRUD | Read-only |
  | SupervisorNamespace | Create, get, delete, list | Read-only |
  | ProjectRole | Read-only | Read-only |
  | Region | Read-only | (none listed) |

- Other listed API resources: `ProjectRoleBindings`, `RegionStorageClassQuotas`,
  `VirtualMachineRemoteConsoleRequests`, `Zone` — across `v1alpha1` and `v1alpha2`. `[9.1]` `[S32]`

### Authentication `[9.1]`

**(a) VM Apps API — unchanged from 9.0.** The 9.1 "Getting Your Authentication Token" page carries
the same refresh-token (129600 min / 90 days) and access-token (one hour) lifespans and the same
three-step flow. `[9.0+9.1]` `[S12]` `[S13]`

**(b) NEW in 9.1 — unified VCF OAuth via VCF Identity Broker (VIDB).** `[9.1]` `[S30]` `[S15]`

- "As of VCF 9.1, VMware offers unified API and CLI access across most VCF components with OAuth
  standards-based token authentication, based on VCF Identity Broker (VIDB)." `[9.1]` `[S30]`
- Token exchange endpoint `[9.1]` `[S30]`:
  ```
  POST https://{vidb.host}/acs/t/{role}/token
  Content-Type: application/x-www-form-urlencoded

  grant_type=...&api_token={vidb_token}
  ```
  Response: `{"access_token": "{bearer_token}"}`; then `Authorization: Bearer {bearer_token}`.
  > The `grant_type` value is elided as `...` in the source page as rendered; see **Gaps**.
- Token model `[9.1]` `[S30]`:
  - **API refresh token** — durable, months-long lifespan, revocable.
  - **Bearer access token** — short-lived, minutes-long, returned as JSON.
- Four-step architecture `[9.1]` `[S15]`: "Administrator creates API clients with credentials that
  are recorded in VIDB. Administrator requests a long-lived API refresh token from the VCF
  Operations UI. Automation script passes the API refresh token to VIDB and gets a bearer access
  token in return. Automation script uses the bearer access token to authenticate with VCF
  components."
- Components covered by this unified flow: vCenter, NSX, VCF Operations, Orchestrator, HCX, and
  **VCF Automation**. VIDB can federate with external IdPs such as Okta and Entra ID. `[9.1]` `[S30]`
- Admin UI path to create clients/tokens `[9.1]` `[S17]`:
  **Fleet Management > Identity & Access > VCF SSO Overview** → select identity broker →
  **API Access > API Clients > Create** (client name, roles, scope, validity), then the vertical
  ellipsis → **Generate API Token**. Configurable: API Token Name, **API Token TTL (default 30
  days)**, **Access Token TTL (default 30 mins)**. "After you click Continue, you cannot retrieve
  the API token that was generated." `[9.1]` `[S17]`

> **Important:** in 9.1 there are therefore *two* coexisting token systems — the VCF-Automation-local
> `/tm/oauth/tenant/{tenant}/token` flow, and the fleet-wide VIDB `/acs/t/{role}/token` flow.
> The docs fetched do not state that the former is deprecated. `[9.1]` `[S13]` `[S30]`

### API categories for service provider administration `[9.1]` `[S31]`

13 categories: Access Control, Aggregator, Approvals, Blueprint, Catalog, Content Gateway, Custom
Forms, Custom Resource Types & Actions, Instances, Orchestrator Gateway, Policies, Projects,
Provisioning Service. `[9.1]` `[S31]`

The 9.0 page lists the **same 13** categories with the same descriptions, and additionally states
which are excluded: "ABX, Deployment, Deployment Metrics, Identity, and Onboarding (available only
in VCF Automation for VM Apps)." `[9.0]` `[S33]`

> A summarization pass over the 9.1 page annotated "Custom Resource Types & Actions" and
> "Instances" as "new in VCF 9.1". **This is contradicted by the 9.0 page, which already lists
> both.** Treated as a summarizer artifact, not a delta. `[S31]` vs `[S33]`

### Provider Infrastructure / All Apps REST conventions `[9.1 "latest"]` `[S19]` `[S20]`

From the Broadcom Developer Portal (marked version 9.1, latest):

- REST shape: `GET /items`, `POST /items` (201), `GET /items/{urn}`, `PUT /items/{urn}`,
  `DELETE /items/{urn}` (204). `[S19]` `[S20]`
- **IDs are full Uniform Resource Names (URNs)**, not bare UUIDs. `[S20]`
- Async operations return **202** with a `Location` header carrying the tracking task URI. `[S19]`
- Content/version negotiation: `application/json;version=9.1.0`; "Each feature has a version in the
  path element present in its URL." Up to 5 major versions back are supported. `[S19]` `[S20]`
- Auth/context headers: `Authorization` (JWT), `x-vcloud-authorization` (**deprecated**),
  `X-VMWARE-VCLOUD-TENANT-CONTEXT` (org-scoped ops), `X-VMWARE-VCLOUD-AUTH-CONTEXT` (multisite).
  `[S19]`
  - The `x-vcloud-*` header family confirms VMware Cloud Director lineage for the
    provider/All-Apps side of VCF Automation. `[S19]`

### What's New — VCF Automation in 9.1 `[9.1]` `[S09]`

**Provider Management (Cloud Administration):**
1. **vDefend Firewall support** — "vDefend Distributed Firewall and Gateway Firewall support
   directly within VCF Automation," enabling delegation of firewall services to organizations with
   RBAC and predefined security profiles.
2. **Default IP block configuration** — providers configure default private VPC and private Transit
   Gateway IP blocks via the Provider Management UI, overridable per organization.
3. **Avi Load Balancer support** — "Full self-service support for Avi Load Balancer" with quota
   management, for **both All Apps and VM Apps** organizations.
4. **Multiple external connections** — organizations get multiple exit points for external traffic
   via centralized connections and distributed VLAN connections.
5. **Shared VLAN extension subnets** — configure VLAN extension NSX subnets and share across
   multiple organizations for direct device connectivity.
6. **External IP blocks** — **IP spaces renamed to external IP blocks**, with support for multiple
   CIDRs, custom IP ranges, and **Infoblox External IPAM** integration.
7. **Multi-supervisor region quota** — "Grant organizations quota across multiple supervisors in any
   given region," with capacity sharing options.

**Organization Management:**
1. **Namespace allocation changes** — day-2 operations to modify resource limits, VM classes,
   storage classes, and shared subnets.
2. **Project content libraries** — projects can hold dedicated content libraries, spanning multiple
   projects.
3. **Canonical content libraries** — subscribed libraries providing validated Ubuntu LTS images.
4. **Shared NSX subnets** — org-wide NSX subnets shareable across multiple namespaces.
5. **Transit Gateway configurations** — multiple NSX Transit Gateways with NAT, IPsec VPN, and
   vDefend Gateway Firewall support.

### Terraform / IaC integration `[9.1]` `[S27]`

Same three providers as 9.0, with re-scoped descriptions:

1. **Terraform Provider for VCF Automation** — Provider Management UI **and a subset of the
   Organization UI**; "greenfield" examples for fresh installations.
2. **Terraform Provider for Kubernetes** — Organization UI resources exposed through the **VCF
   Automation Kubernetes API layer**, such as projects.
3. **Terraform Provider for VMware Aria Automation** — VM Apps organizations **and All Apps
   resources not yet exposed through Kubernetes API layers**, including blueprints.

Resources by role `[9.1]` `[S27]`:
- **Provider administrators** — organizations, regions, quotas, networking, content libraries,
  supervisor namespaces.
- **Organization administrators (All Apps)** — VCF services projects, content libraries, Virtual
  Private Clouds, subnets, blueprints, catalogs.
- **Organization users** — provision IaaS services, deploy catalogs.

Examples surface unchanged: `https://<FQDN>/automation/api-docs/#/terraform-provider` `[9.1]` `[S27]`

### Doc-set restructure in 9.1 `[9.1]` `[S28]` vs `[9.0]` `[S05]`

The "Administration SDKs, APIs, and CLI" section was reorganized. 9.1 adds two top-level entries
absent from the 9.0 listing:
- **VMware Cloud Foundation APIs and SDKs** (`about-vmware-cloud-foundation-development.html`) —
  the new parent that hosts **OAuth Token Support for API and CLI Access**.
- **VMware Cloud Foundation Programming Guide** (`introduction-to-the-vcf-programming-guide.html`).
- Also new: **Help and Support for VCF SDKs, APIs, and VCF PowerCLI**.

Both **VMware Cloud Foundation Automation APIs for VM Apps Programming Guide** and **VCF Automation
and All Apps API** persist under identical slugs in both versions. `[9.0+9.1]` `[S05]` `[S28]`

---

## 9.0 → 9.1 Delta Table

| # | Area | 9.0 | 9.1 | Type | Source |
|---|---|---|---|---|---|
| 1 | Auth (fleet-wide) | No unified VCF OAuth documented in the fetched pages | **VCF Identity Broker (VIDB)** unified OAuth: `POST https://{vidb.host}/acs/t/{role}/token`, `grant_type=…&api_token=…` → `{"access_token": …}`; covers vCenter, NSX, VCF Operations, Orchestrator, HCX, VCF Automation | **New capability** | `[S30]` `[S15]` |
| 2 | Auth (token admin UI) | Provider portal **My Account > API Tokens > NEW**; device-authorization grant | Fleet Management > Identity & Access > VCF SSO > API Access > API Clients; API Token TTL default 30 days, Access Token TTL default 30 mins | **New/restructured** | `[S16]` `[S17]` |
| 3 | Auth (VM Apps) | `POST /tm/oauth/tenant/{tenant}/token`, refresh 90 d / access 1 h | **Unchanged** — same page, same lifespans, same flow | **No change** | `[S12]` `[S13]` `[S14]` |
| 4 | Doc structure (SDK/API) | No "VCF APIs and SDKs" or "VCF Programming Guide" parent | Adds **VMware Cloud Foundation APIs and SDKs**, **VMware Cloud Foundation Programming Guide**, **Help and Support for VCF SDKs…** | **Restructure** | `[S05]` `[S28]` |
| 5 | Networking (provider) | — | **IP spaces renamed to external IP blocks**; multiple CIDRs, custom IP ranges, **Infoblox External IPAM** | **Rename + new capability** | `[S09]` |
| 6 | Security | — | **vDefend Distributed Firewall and Gateway Firewall** delegable to orgs with RBAC + predefined security profiles | **New capability** | `[S09]` |
| 7 | Load balancing | — | **Full self-service Avi Load Balancer** with quota mgmt, for both All Apps and VM Apps orgs | **New capability** | `[S09]` |
| 8 | Networking (org) | — | Multiple **NSX Transit Gateways** with NAT, IPsec VPN, vDefend Gateway Firewall; **shared NSX subnets** across namespaces; **shared VLAN extension subnets** across orgs; multiple external connections | **New capability** | `[S09]` |
| 9 | Quota | — | **Multi-supervisor region quota** — quota across multiple supervisors in a region, with capacity sharing; default private VPC / Transit Gateway IP blocks | **New capability** | `[S09]` |
| 10 | Content | — | **Project content libraries** (multi-project spanning) and **canonical content libraries** (subscribed, validated Ubuntu LTS images) | **New capability** | `[S09]` |
| 11 | Namespaces | — | Day-2 **namespace allocation changes**: modify resource limits, VM classes, storage classes, shared subnets | **New capability** | `[S09]` |
| 12 | CLI | **VCF CLI v9.0** | **VCF CLI v9.1** | **Version bump** | `[S06]` `[S34]` |
| 13 | Workload types | VMs, K8s clusters, vSphere Pods, persistent volumes, secret store, **Harbor container registry**, GPU/private AI | K8s clusters, VMs, vSphere Pods, secrets, persistent volumes, GPU/private AI, **databases via Data Services Manager** | **List change — low confidence** (see Gaps) | `[S03]` `[S34]` |
| 14 | Overview wording | Org Mgmt = "organize and govern resources allocated to them among application teams" | Org Mgmt = "create and assign projects and vSphere Namespaces tailored for different application teams" | **Wording** | `[S10]` `[S11]` |
| 15 | Blueprints (VM Apps) | "Templates developed using canvas and YAML editor" | Adds "VCF or AWS CloudFormation" templates, importable by administrators | **Wording/scope** | `[S22]` `[S21]` |
| 16 | Provider REST API categories | 13 categories | **Same 13 categories** | **No change** (contradicts a "new in 9.1" summarizer artifact) | `[S33]` `[S31]` |
| 17 | Terraform providers | 3 providers; K8s provider covers projects, content libraries, VPCs, subnets | Same 3; K8s provider scoped to "Organization UI resources exposed through the VCF Automation Kubernetes API layer, such as projects"; Aria provider explicitly covers "All Apps resources not yet exposed through Kubernetes API layers" | **Re-scope** | `[S26]` `[S27]` |
| 18 | Building Cloud Apps doc tree | Child pages: Getting Started with Tools, Provision/Manage VMs, Provision/Manage K8s Clusters, Deploying to vSphere Pods | Child pages restructured — `getting-started-with-the-tools-for-building-applications.html` returns **404** under 9.1; page points to "VMware Cloud Foundation Consumption documentation" | **Restructure** | `[S03]` `[S34]` |

**No deprecations of VCF Automation features** were found in any fetched 9.1 page. The only
deprecation observed anywhere is the `x-vcloud-authorization` header on the provider/All-Apps REST
API, marked deprecated on the developer portal (version 9.1, latest). `[S19]`

---

## Lookup patterns

How an agent should discover API operations not covered above.

### 1. In-product API Help Center (authoritative, per-instance)

- **VM Apps org:** "To access all Swagger specifications from a single landing page, log in as
  admin to the VCF Automation for VM Apps Organization tenant. At the top-right corner of the home
  page, click the user name and open the **API Help Center**." `[9.0]` `[S08]`
- **Service provider / All Apps:** after signing into the VCF Automation interface, select
  **admin > API Help Center > Automation APIs** in the upper right corner. `[9.0+9.1]` `[S33]` `[S31]`

### 2. In-product api-docs URL (verified string)

```
https://<FQDN>/automation/api-docs/#/terraform-provider
```
Documented as the location of Terraform provider usage examples in both versions; the
`/automation/api-docs/#/<section>` shape is the discoverable pattern. `[9.0+9.1]` `[S26]` `[S27]`

### 3. Broadcom Developer Portal (public)

Base pattern — verified working:
```
https://developer.broadcom.com/xapis/<api-slug>/latest/
```

| Slug | Covers | Source |
|---|---|---|
| `org-management-vm-apps-org` | Master index of all 15 VM Apps Org APIs | `[S08]` `[S25]` |
| `vm-apps-org-catalog` | Catalog Items, Catalog Item Types, Catalog Admin Items, Deployments, Deployment Actions, Requests | `[S18]` |
| `vm-apps-org-policies` | VM Apps Org policies | `[S-search]` |
| `all-apps-org-access-control` | All Apps Org access control | `[S20]` |
| `provider-infrastructure-apis` | Provider infrastructure | `[S19]` |
| `vcf-business-services-console-apis` | Business services console | `[S-search]` |
| `vmware-cloud-foundation-api` | VCF platform API | `[S-search]` |

Slug construction rule inferred from the set above: `{all-apps-org|vm-apps-org}-{service}` in
lowercase kebab-case, e.g. `vm-apps-org-blueprint`, `vm-apps-org-deployment`. **Inferred, not
verified** — see Gaps.

The docs also state generally: "For detailed endpoint specifications, reference documentation is
available at `developer.broadcom.com/xapis/` for each category." `[9.1]` `[S31]`

The portal exposes a **REST API Index** and an **API ChangeLog** link on each API page — the
ChangeLog is the correct place to diff 9.0 vs 9.1 operations. `[S18]`

### 4. Kubernetes-native discovery (All Apps org)

```
kubectl --context cci api-resources
```
Returns available CRDs across `v1alpha1` / `v1alpha2` in the `infrastructure.cci.vmware.com`
group. `[9.1]` `[S32]`

### 5. Version negotiation when calling provider/All-Apps REST

Send `application/json;version=9.1.0` (Accept and/or Content-Type). Up to 5 major versions back
are supported, so `version=9.0.0` should remain callable against a 9.1 system. `[S19]` `[S20]`

### 6. Pagination / filtering on VM Apps collections

`$orderby`, `$top`, `$skip`, `page`, `size` — e.g. `/catalog/api/items?$orderby=name%20desc` `[S18]`

---

## Gaps and Ambiguities

1. **`grant_type` value for the 9.1 VIDB token exchange** — the source renders the body as
   `grant_type=...&api_token={vidb_token}`, eliding the literal value.
   `UNVERIFIED — could not retrieve`. `[S30]`
2. **`/tm` prefix inconsistency in the provider token flow** — steps 2–4 use
   `https://<vcfa.url>/tm/oauth/tenant/<org>/...` but the refresh step (5) uses
   `https://<vcfa.url>/oauth/tenant/<org>/token` with no `/tm`. Reproduced verbatim; not resolvable
   from the fetched page. Test both before relying on either. `[S16]`
3. **All Apps access-token endpoint** — a page titled "Generating an All Apps Access Token" at
   `.../about-the-vcf-automation-api/generating-an-access-token.html` appeared in search results but
   returned **404** on fetch. `UNVERIFIED — could not retrieve`.
4. **Projects API base path** — never verified. The `Projects` service exists `[S08]` `[S25]` and
   `projectId` is consumed by blueprint and catalog-request bodies `[S23]` `[S24]`, but the
   projects endpoint path itself was not on any retrievable page. The tutorial pages
   ("Managing Your Projects", "Create a Project with the Project Service API") are landing pages
   with no paths, and their leaf children were not retrievable within rate limits.
   `UNVERIFIED — could not retrieve`.
5. **Cloud accounts / cloud zones API paths** — same situation. "Setting up VCF Automation using
   APIs" and "Using VCF Automation APIs to Build your Resource Infrastructure" are landing pages;
   leaf pages not retrieved. The commonly-expected `/iaas/api/...` base path was **never confirmed
   in any fetched 9.0 or 9.1 page** and must not be assumed. `UNVERIFIED — could not retrieve`.
6. **Resource actions / day-2 actions API paths** — "Working with Deployments and Resources" was
   rate-limited on every attempt. The developer portal lists **Deployment Actions** as a category
   `[S18]`, but no concrete path was verified. `UNVERIFIED — could not retrieve`.
7. **ABX API base path** — service is named and described `[S08]` `[S25]` but no path verified.
   `UNVERIFIED — could not retrieve`.
8. **Pipelines / Code Stream** — no VCF Automation pipelines component appeared in any fetched 9.0
   or 9.1 page. Whether it was dropped in the Aria→VCF transition or simply lives elsewhere is
   **unresolved**; do not assert either way.
9. **"New in VCF 9.1" annotations on API categories** — a summarization pass flagged "Custom
   Resource Types & Actions" and "Instances" as new in 9.1, but the 9.0 page lists both. Discarded
   as artifact. `[S31]` vs `[S33]`
10. **Workload-type list delta (row 13)** — both lists are LLM summaries of prose, not verbatim
    enumerations. The apparent drop of "Harbor container registry" and addition of "databases via
    Data Services Manager" is **low confidence**. `[S03]` `[S34]`
11. **Developer portal version pinning** — every `xapis` page fetched reported "9.1 (latest)". No
    9.0-pinned URL pattern was discovered, so 9.0-specific API reference could not be separated from
    9.1. All `[S18]` `[S19]` `[S20]` `[S25]` facts are tagged to the 9.1/latest doc set.
12. **Developer portal slug inference** — `vm-apps-org-blueprint`, `vm-apps-org-deployment` etc. are
    extrapolated from four confirmed slugs, not fetched. Verify before use.
13. **Deep endpoint pages** — Broadcom TechDocs rate-limited (HTTP 429) repeatedly during this task,
    forcing ~90 s pauses between fetches. Several leaf tutorial pages were consequently not
    retrieved. Items 4–7 above are all attributable to this.
14. **VCF SSO relationship for the VM Apps `/tm/oauth` flow** — how the tenant-local token service
    relates to VCF SSO / VIDB in 9.1 (coexistence, precedence, migration) is **not stated** in any
    fetched page. `UNVERIFIED — could not retrieve`.

---

## Source Inventory

All accessed **2026-07-31**.

| ID | URL | Doc set version | Date accessed | Covers |
|---|---|---|---|---|
| S01 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | VCF 9.0 | 2026-07-31 | 9.0 landing; section URLs incl. Workload Orchestration |
| S02 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | 2026-07-31 | 9.1 landing; section URLs |
| S03 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-cloud-applications.html | VCF 9.0 | 2026-07-31 | VCF Automation consumption framing; workload types; child topics |
| S04 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/vcf-advanced-services.html | VCF 9.0 | 2026-07-31 | Advanced Services scope (not VCF Automation) |
| S05 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools.html | VCF 9.0 | 2026-07-31 | 9.0 SDK/API/CLI section structure |
| S06 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-cloud-applications/getting-started-with-the-tools-for-building-applications.html | VCF 9.0 | 2026-07-31 | All Apps vs VM Apps orgs; UI/catalog/CLI v9.0; IaaS Services Console |
| S07 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api.html | VCF 9.0 | 2026-07-31 | `/provider` and `/automation` UI surfaces |
| S08 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1.html | VCF 9.0 | 2026-07-31 | 15 VM Apps API services + descriptions; API Help Center; developer portal link |
| S09 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-automation.html | VCF 9.1 | 2026-07-31 | What's New — VCF Automation (primary delta source) |
| S10 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/overview-of-vmware-cloud-foundation-9/what-is-vmware-cloud-foundation-and-vmware-vsphere-foundation/vcf-automation-overview.html | VCF 9.0 | 2026-07-31 | 9.0 product definition; four components; Aria rename |
| S11 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/overview-of-vmware-cloud-foundation-9/what-is-vmware-cloud-foundation-and-vmware-vsphere-foundation/vcf-automation-overview.html | VCF 9.1 | 2026-07-31 | 9.1 product definition; four components |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token.html | VCF 9.0 | 2026-07-31 | Token types, lifespans, 3-step flow |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token.html | VCF 9.1 | 2026-07-31 | Same, confirming no change in 9.1 |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token/get-your-access-token-for-vra-8-x.html | VCF 9.0 | 2026-07-31 | **VM Apps token endpoint** `/tm/oauth/tenant/{tenant}/token` + curl |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access/token-exchange-architecture.html | VCF 9.1 | 2026-07-31 | VIDB 4-step token exchange architecture |
| S16 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/service-provider-portal/generating-provider-management-api-tokens.html | VCF 9.0 | 2026-07-31 | **Provider device-authorization grant flow** + curl |
| S17 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/managing-api-tokens.html | VCF 9.1 | 2026-07-31 | VCF SSO API client/token creation UI; TTL defaults |
| S18 | https://developer.broadcom.com/xapis/vm-apps-org-catalog/latest/ | VCF Automation API 9.1 (latest) | 2026-07-31 | Catalog/Deployment/Requests categories; OData query params |
| S19 | https://developer.broadcom.com/xapis/provider-infrastructure-apis/latest/ | VCF Automation API 9.1 (latest) | 2026-07-31 | REST conventions, URNs, 202+Location, version header, auth headers |
| S20 | https://developer.broadcom.com/xapis/all-apps-org-access-control/latest/ | VCF Automation API 9.1 (latest) | 2026-07-31 | All Apps REST shape; URN IDs; version negotiation |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/organization-management/vcfa-overview.html | VCF 9.1 | 2026-07-31 | VM Apps org terminology + 9 UI tabs (9.1) |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/organization-management/vcfa-overview.html | VCF 9.0 | 2026-07-31 | VM Apps org terminology + 9 UI tabs (9.0) |
| S23 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/requesting-a-deployment-from-a-catalog-item/request-deployment.html | VCF 9.0 | 2026-07-31 | **`/catalog/api/items/{id}/request`, `/deployment/api/deployments`** |
| S24 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/working-with-blueprints-cloud-templates/create-and-update-a-cloud-template.html | VCF 9.0 | 2026-07-31 | **`/blueprint/api/blueprints`** CRUD + validation + curl |
| S25 | https://developer.broadcom.com/xapis/org-management-vm-apps-org/latest/ | VCF Automation API (latest) | 2026-07-31 | Master index of 15 VM Apps Org APIs |
| S26 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/provider-management/terraform-configurations-in-vcf-automation-provider-management.html | VCF 9.0 | 2026-07-31 | Three Terraform providers; `/automation/api-docs/#/terraform-provider` |
| S27 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/provider-management/terraform-configurations-in-vcf-automation-provider-management.html | VCF 9.1 | 2026-07-31 | Three Terraform providers, re-scoped; resources by role |
| S28 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | 2026-07-31 | 9.1 SDK/API/CLI restructure |
| S29 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-the-vcf-automation-api.html | VCF 9.1 | 2026-07-31 | 9.1 All Apps API child topics; UI surfaces |
| S30 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access.html | VCF 9.1 | 2026-07-31 | **VIDB `/acs/t/{role}/token`**; token model; covered components |
| S31 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-the-vcf-automation-api/categories-of-vcf-automation-hard-tenancy-apis.html | VCF 9.1 | 2026-07-31 | 13 provider REST API categories (9.1) |
| S32 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-the-vcf-automation-api/kubernetes-commands-for-devops.html | VCF 9.1 | 2026-07-31 | **All Apps CRDs**, `infrastructure.cci.vmware.com/v1alpha2`, `--context cci` |
| S33 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/categories-of-vcf-automation-hard-tenancy-apis.html | VCF 9.0 | 2026-07-31 | 13 provider REST API categories (9.0); VM-Apps-only exclusions |
| S34 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/building-your-cloud-applications.html | VCF 9.1 | 2026-07-31 | VCF CLI v9.1; 9.1 workload types; doc restructure |
| S35 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/working-with-blueprints-cloud-templates.html | VCF 9.0 | 2026-07-31 | Landing page; "Blueprints/Cloud Templates" dual naming |
| S36 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/requesting-a-deployment-from-a-catalog-item.html | VCF 9.0 | 2026-07-31 | Landing page; names Catalog + Deployment APIs |
| S37 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/managing-your-projects.html | VCF 9.0 | 2026-07-31 | Landing page; Project Service API named, no paths |
| S38 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/setting-up-cloud-assembly.html | VCF 9.0 | 2026-07-31 | Landing page; names IaaS APIs, no paths |

**Retrieval failures (recorded for completeness):**

| URL | Result |
|---|---|
| `.../9-1/building-your-cloud-applications/getting-started-with-the-tools-for-building-applications.html` | HTTP 404 — page does not exist in 9.1 (evidence for delta row 18) |
| `.../9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/generating-an-access-token.html` | HTTP 404 on fetch despite appearing in search index |
| `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-1-and-later/9-1.html` | HTTP 404 — the 9.1 doc set lives under `vcf-9-0-and-later/9-1`, not `vcf-9-1-and-later` |
| `.../9-0/.../working-with-deployments-and-resources.html` | HTTP 429 on all attempts |
| `https://developer.broadcom.com/xapis/vm-apps-org-catalog/latest/catalog/api/items/` | "Object Not Found" — deep-linking into portal sub-paths does not work |
