# VCF Operations — VMware Cloud Foundation 9.0 and 9.1

Research date: 2026-07-31. Every claim below carries a bracketed source ID resolving to
the Source Inventory at the bottom, plus a `[9.0]` / `[9.1]` / `[9.0+9.1]` version tag.
`[9.0+9.1]` is used only where the fact was independently verified in both doc sets.

> Naming caution: the task brief referred to the "Aria Operations family". The 9.0 and 9.1
> doc sets do not use "Aria" for these components. Verified current names are recorded below.
> The only in-scope reference to Aria found was an upgrade path: "Upgrade VMware Aria
> Operations to VCF Operations 9.0" [S12].

---

## VCF Operations in VCF 9.0

### Composition (Bill of Materials)

The VCF 9.0 BOM lists these Operations-family components, all at version 9.0.0.0 [S8]:

| Component name (verbatim from BOM) | Version | Build |
|---|---|---|
| VMware Cloud Foundation Operations | 9.0.0.0 | 24695812 |
| VMware Cloud Foundation Operations orchestrator | 9.0.0.0 | 24674408 |
| VMware Cloud Foundation Operations collector | 9.0.0.0 | 24695833 |
| VMware Cloud Foundation Operations fleet management | 9.0.0.0 | 24695816 |
| VMware Cloud Foundation Operations for logs | 9.0.0.0 | 24695810 |
| VMware Cloud Foundation Operations for networks | 9.0.0.0 | 24694676 |
| VMware Cloud Foundation Operations HCX | 9.0.0.0 | 24699341 |
| VMware Cloud Foundation Identity Broker | 9.0.0.0 | 24695128 |

`[9.0]` **SDDC Manager is a separate BOM line item at 9.0.0.0 (build 24703748)** — it is not
part of the Operations family in 9.0 [S8].

The 9.0.1 patch release notes confirm the same component set shipping as independently
versioned/built artifacts, adding a "VCF Operations for logs (Agent)" line and a separate
"VCF Operations (Upgrade)" artifact [S7]:
- "VMware Cloud Foundation Operations 9.0.1.0 | 29 SEP 2025 | Build 24960351" `[9.0]` [S7]
- "VMware Cloud Foundation Fleet Management 9.0.1.0 | 29 SEP 2025 | Build 24960371" `[9.0]` [S7]
- "VMware Cloud Foundation Operations for logs 9.0.1.0 ... Build 24960345" `[9.0]` [S7]
- "VMware Cloud Foundation Operations for logs (Agent) 9.0.1.0 ... Build 24960353" `[9.0]` [S7]
- "VMware Cloud Foundation Operations for networks 9.0.1.0 ... Build 24950933" `[9.0]` [S7]
- "VMware Cloud Foundation Operations HCX 9.0.1.0 ... Build 24972592" `[9.0]` [S7]
- "VMware Cloud Foundation Identity Broker 9.0.1.0 ... Build 24941398" `[9.0]` [S7]

Note the 9.0.1 release notes render the fleet component as "VMware Cloud Foundation Fleet
Management" while the 9.0.0 BOM renders it "VMware Cloud Foundation Operations fleet
management" [S7][S8]. Treat these as the same component under two spellings.

### Deployment

`[9.0]` A **standalone VCF Operations Fleet Management Appliance** is a discrete deployable
appliance in 9.0. Its existence is established by (a) the dedicated 9.0 deployment topic
"Deploy the VCF Operations fleet management Appliance" [S13, title only — page body returned
HTTP 403 on repeated fetches, see Gaps] and (b) the 9.1 release note stating it "no longer
exists" as of 9.1 [S1] (see next section).

`[9.0]` Data collection scale-out uses **cloud proxies / collectors**; documented under Fleet
Management as "Collecting Data with Cloud Proxy in VCF Operations" [S5]. Management nodes can
be scaled up and out ("Add Nodes to VCF Operations") [S5].

`[9.0]` Fleet Management in 9.0 is performed through VCF Operations: administrators handle
"identity/access, certificates, passwords, tags, configuration profiles, and VCF fleet
availability through VCF Operations" [S5]. The doc set states: "For VCF, you use VCF Operations
and in certain cases individual components for these capabilities." `[9.0+9.1]` — this exact
sentence appears in both the 9.0 and 9.1 Fleet Management landing pages [S5][S4].

### 9.0 sub-page structure under Fleet Management [S5]

VCF Single Sign-On; Certificate Management; Accounts & Passwords; Tags & Categories;
Configuration Management; **Management Appliances** (`configuring-managemnet-appliances.html`
— note the typo in the real URL); VCF Automation Deployment; vCenter Linking; Cloud Proxy Data
Collection; **Disaster Recovery**; Shutdown/Startup; Backup & Restore; FIPS Configuration;
**Scaling Management Nodes**; **Instance Migration** (adding an existing VCF instance to a fleet).

### 9.0 API surface

`[9.0]` A 9.0-pinned VCF Operations API reference exists at `developer.broadcom.com` [S16].
Top-level categories documented for 9.0 include: Actions, Adapter Kinds, Adapters, Alert
Plugins, Alerts, Applications, Audit, Auth, Certificate, **Chargeback Billing**, **Chargeback
Reports**, Collector Groups, Collectors, Configuration Management, Content Management, Cost
Configuration, Credentials, Deployment, Events, Integrations, **Log Management**, Maintenance
Schedules, Notifications, Optimization, Policies, Product Licensing, Recommendations, Reports,
Resource, Resources, Solutions, Super Metrics, Symptoms, Tasks, Versions Info [S16].

`[9.0]` **Not present** in the 9.0 category list: `fleet-management`, `diagnostics`/`findings`,
`salt`, `whatif` [S16]. This is the API-level signature of the 9.0→9.1 fleet absorption.

---

## VCF Operations in VCF 9.1

### Composition (Bill of Materials)

The VCF 9.1 BOM lists, all at 9.1.0.0 [S9]:

| Component name (verbatim from BOM) | Version | Build |
|---|---|---|
| VCF Operations | 9.1.0.0 | 25346025 |
| Cloud proxy | 9.1.0.0 | 25346033 |
| License server | 9.1.0.0 | 25346031 |
| VCF Operations for networks | 9.1.0.0 | 25318550 |
| VCF Operations HCX | 9.1.0.0 | 25318520 |
| VCF Operations orchestrator | 9.1.0.0 | 25346069 |
| Log management | 9.1.0.0 | 25346055 |
| Real-time metrics | 9.1.0.0 | 25346020 |
| Identity broker | 9.1.0.0 | 25368698 |
| Fleet lifecycle | 9.1.0.0 | 25371109 |
| SDDC lifecycle | 9.1.0.0 | 25371107 |
| Software depot | 9.1.0.0 | 25371105 |
| Telemetry | 9.1.0.0 | 25181946 |
| VCF Services runtime | 9.1.0.0 | 25370367 |

`[9.1]` "VCF Installer/SDDC Manager: 9.1.0.0 (25371088)" remains a BOM line [S9].

Renames/replacements visible purely from BOM diffing `[9.1]` [S8][S9]:
- "VCF Operations for logs" → **"Log management"**
- "VCF Operations collector" → **"Cloud proxy"**
- "VCF Operations fleet management" → **"Fleet lifecycle"** + **"SDDC lifecycle"** (split into two)
- New BOM entries with no 9.0 counterpart: **Real-time metrics**, **License server**,
  **Software depot**, **Telemetry**, **VCF Services runtime**

`[9.1]` Log management is described as "Integrated within VCF Operations with masking,
filtering, forwarding, partitioning, archived log import", with "Upgrade support from VCF
Operations for Logs 8.18 and 9.0" — confirming the rename is a continuation, not a new product
[S1]. Agents: "Log Insight agent for appliances; Fluentbit for Kubernetes" [S1].

### UI reorganisation

`[9.1]` VCF Operations presents an "enhanced, intuitive experience structured around the
functional pillars of VCF: Build, Manage, Operate, and Protect" [S1]. The 9.1 What's New is
itself organised under those four pillars [S1].

### Deployment

`[9.1]` **The standalone Fleet Management Appliance is gone.** Verbatim: "In VCF 9.1, the
standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by fleet
lifecycle, a management component to streamline the lifecycle management of the VCF management
components." [S1]

`[9.1]` Fleet lifecycle provides a "Unified framework for: install, upgrade, patch, backup,
restore, maintain management components" [S1] and manages these component types (verbatim
list): "Identity broker, VCF Operations, VCF Operations for networks, Real-time metrics,
Real-time metrics store, Salt master, Salt RaaS, VCF Automation, Telemetry, SDDC lifecycle,
Software depot, Log management, Migration service engine, VCF services runtime." [S1]

`[9.1]` VCF Operations HCX gains "Lifecycle management support" — "HCX Manager deployed/managed/
upgraded via VCF Operations", "Existing HCX instances onboarded to VCF Operations", and "VCF SSO
and VCF Roles support for HCX" [S1].

`[9.1]` The 9.1 Fleet Management landing page states plainly: **"No dedicated Fleet Management
Appliance exists."** Management occurs through VCF Operations as the primary interface, with
SDDC Manager still handling certain specific operations (notably password management), and
individual components in specific vSphere Foundation cases [S4].

### 9.1 Fleet Management sub-pages [S4]

Managing Identity and Access With VCF Single Sign-On; Managing Certificates; Managing Passwords;
Tags and Categories; Configuration Management; **Managing External Infrastructure Services**
(DNS/NTP); **Adding VCF Components Post Deployment**; Linking vCenter instances; Cloud Proxy
data collection; Shutdown and Startup; Component Backup and Restore; FIPS Configuration;
**Performing Post-Deployment Actions on Components** (day-N); Configure a Proxy Server.

Note that the 9.0-only topics **Disaster Recovery**, **Scaling Management Nodes**, and
**Instance Migration** do not appear in the 9.1 Fleet Management sub-page list [S4][S5].
Treat as relocated rather than removed unless confirmed — see Gaps.

---

## CRITICAL: The fleet / lifecycle management relationship, 9.0 vs 9.1

**Short answer: No — VCF Operations does not take over SDDC Manager's duties in 9.1. SDDC
Manager persists in both versions. What changed is that the separate *Fleet Management
Appliance* was absorbed into VCF Operations as the "Fleet lifecycle" component.**

Precise, citable statements:

1. `[9.0]` SDDC Manager ships as its own BOM component at 9.0.0.0 build 24703748 [S8].
   `[9.1]` It still ships, as "VCF Installer/SDDC Manager: 9.1.0.0 (25371088)" [S9].
   SDDC Manager therefore exists in both releases.

2. `[9.1]` The appliance that disappeared is the *Fleet Management* appliance, not SDDC
   Manager: "In VCF 9.1, the standalone VCF Operations Fleet Management Appliance no longer
   exists and is replaced by fleet lifecycle, a management component to streamline the
   lifecycle management of the VCF management components." [S1]

3. `[9.1]` SDDC Manager's own capabilities were *expanded*, not retired. Under "SDDC Manager
   Scale": "Manage a maximum of 5000 hosts per VCF Instance"; "Per Instance level number of
   hosts scale support has been increased by 2x from VCF 9.0"; "Parallelization of operations
   has been enhanced, allowing for 256 simultaneous cluster upgrades"; plus "streamlined
   management of DNS, NTP at scale" [S1].

4. `[9.1]` SDDC Manager retains specific fleet duties. The 9.1 Fleet Management page notes
   SDDC Manager "Handles certain specific operations (particularly password management)" [S4].

5. `[9.0+9.1]` The division of labour sentence is unchanged across both doc sets: "For VCF,
   you use VCF Operations and in certain cases individual components for these capabilities."
   [S5][S4]

6. `[9.1]` Lifecycle is now split into **two** BOM components — "Fleet lifecycle" (9.1.0.0,
   25371109) for VCF *management components*, and "SDDC lifecycle" (9.1.0.0, 25371107) for
   the *domain/workload* estate [S9]. 9.0 had a single "Operations fleet management"
   component [S8]. Domain-level LCM in 9.1 is described under "Domain Lifecycle Management":
   optimized NSX Manager and vCenter maintenance windows, NSX Edge clusters upgraded at end of
   domain upgrade sequence, standalone-host and single-host-cluster support, "Select Hosts
   during Cluster Upgrades" to skip problematic hosts, enhanced prechecks exportable to CSV,
   and a Component Versions tab [S1].

7. `[9.1]` API-level corroboration: an entire `/suite-api/api/fleet-management/...` tree
   appears in the VCF Operations API only in 9.1 [S10], and is absent from the 9.0 category
   list [S16]. This is the strongest machine-checkable evidence of the absorption.

**Practical implication for an agent:** in 9.0, fleet identity/cert/password automation may
require talking to a separate Fleet Management appliance endpoint; in 9.1 the same operations
are reachable on the VCF Operations appliance under `/suite-api/api/fleet-management/`.
Domain/host/cluster lifecycle remains an SDDC Manager (and, in 9.1, Fleet LCM / SDDC LCM
service API) concern in both versions.

---

## Auth

### Classic suite-api token — `[9.0+9.1]`, identical in both

Verified independently against the 9.0 [S14] and 9.1 [S15] versions of the same topic. No
differences were found between the two.

```
POST https://RESTendpoint.example.com/suite-api/api/auth/token/acquire
Content-Type: application/json
Accept: application/json
```

Request payload [S14][S15]:
```json
{
  "username": "vRealize-user",
  "password": "vRealize-dummy-password"
}
```
The docs add: "The request body includes the user name, password, and authentication source."
[S15] Auth sources are LOCAL (default) or an imported source — LDAP, Active Directory, VMware
Identity Manager, Single Sign-On [S15].

Response 200 [S14][S15]:
```json
{
  "token": "8f868cca-27cc-43d6-a838-c5467e73ec45::77cea9b2-1e87-490e-b626-e878beeaa23b",
  "validity": 1470421325035,
  "expiresAt": "Friday, August 5, 2016 6:22:05 PM UTC",
  "roles": []
}
```

Authorization header on subsequent calls [S14][S15]:
```
Authorization: OpsToken <token>            # current form, 9.0 and 9.1
Authorization: vRealizeOpsToken <token>    # legacy form, still supported
Authorization: SSO2Token <SSO_SAML_TOKEN>  # external SSO SAML token
```

TTL: "a re-usable ops authorization token that expires after six hours" [S15].
`[9.0+9.1]` No release/revoke endpoint is documented on these pages [S14][S15].

The developer portal restates the same, and adds a Bearer alternative: "OpsToken:
`Authorization: OpsToken <token>` (from POST /api/auth/token/acquire)" and "Bearer Token:
`Authorization: Bearer <token>` (from VCF SSO)"; missing/invalid credentials return 401/403
`[9.0+9.1]` [S3].

### Token exchange for downstream services — `[9.1]` only

`[9.1]` `POST /suite-api/api/auth/token/exchange/` is listed among the operations **new in
9.1** [S10]. It is absent from the 9.0 category list [S16].

Concrete documented use — Log Management API `[9.1]` [S18]:
> "X-JWT-Token header with a token retrieved with the following authenticated call to VCF
> Operation API: POST /suite-api/api/auth/token/exchange"

with request body:
```json
{"serviceKeys": ["ops-li"]}
```
The resulting token is then sent as `X-JWT-Token: <jwt>` [S18].

Concrete documented use — Real-Time Metrics API `[9.1]` [S19]:
acquire an OpsToken, retrieve a service key where `type = VCF_VODAP`, exchange for a JWT via
the VCF Operations API, then send `Authorization: Bearer <jwt-token>` [S19].

`[9.1]` Also new in 9.1: `GET /suite-api/api/auth/sources/vidb/well-known-url/` [S10] — the
OIDC discovery URL for the VCF Identity Broker (VIDB) auth source.

### OAuth 2.0 API tokens — `[9.1]` only

`[9.1]` The 9.1 What's New lists "OAuth 2.0 API tokens for secure automation" and "IAM Settings
for global token lifecycle and security" under Fleet Management → Identity & Access [S1].
The supporting endpoints, new in 9.1 [S10]:
```
POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients/
POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens/
POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/emergency-clients/
POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps/
```
UNVERIFIED — the exact request/response payload shapes for these four were not retrieved.

### Other components' auth

`[9.0+9.1]` **VCF Operations for Networks** — two schemes documented [S17]:
- `ApiKeyAuth`: header `Authorization: NetworkInsight {token}` (apiKey in header)
- `OpsTokenAuth`: `Bearer {token}` (HTTP bearer, JWT format)

UNVERIFIED — the Networks token *acquisition* endpoint, payload and TTL could not be
retrieved [S17][S20]; and the portal does not version-split these two schemes, so the `[9.0+9.1]`
tag here reflects that the reference covers both 9.1 (latest) and 9.0 [S20].

`[9.1]` **Fleet LCM Service API** — two schemes [S22]: HTTP Basic ("Scheme : basic",
"Type : http") and Bearer JWT ("Bearer Format : JWT", "Scheme : Bearer"). Header names and
token endpoint are not stated; "Individual operations in the documentation will include their
specific authentication types" [S22].

---

## Verified API base paths and endpoint templates

### VCF Operations API — base path `/suite-api/api` `[9.0+9.1]`

Host form: `https://{api_host}` [S11]; on-appliance form
`https://<vcf-operations-fqdn>/suite-api/api/` [S19].

**Resources & inventory** `[9.0+9.1]` [S11]
```
GET  /suite-api/api/resources
     ?name=&resourceKind=&adapterKind=&resourceState=&resourceHealth=
     &pageSize=1000&page=0
```
`pageSize` default 1000, `page` 0-based [S11]. Sibling operations named in the reference [S11]:
Get Resource Properties List, Add Resources Properties, Get Resources Relationships,
Mark/Unmark Resources As Being Maintained.

**Custom groups** `[9.0+9.1]` [S11] — named operations: Get / Create / Modify Custom Groups,
Get Group Members; also Get/Create/Modify Custom Profiles.
UNVERIFIED — literal paths (expected `/suite-api/api/resources/groups`) were not retrieved.

**Stats / metrics** `[9.0+9.1]` [S11] — named operations: Get Stat Keys, Get Stats, Add Stats,
Query Latest Stats, Get Top N Stats.
UNVERIFIED — literal paths (expected `/suite-api/api/resources/stats`,
`/suite-api/api/resources/stats/latest/query`) were not retrieved.

**Alerts & alert definitions** `[9.0+9.1]` [S21] — fully verified paths:
```
GET    /suite-api/api/alerts?id=&resourceId=&page=0&pageSize=1000
POST   /suite-api/api/alerts                      # Modify Alerts
POST   /suite-api/api/alerts/query                # Query Alerts
DELETE /suite-api/api/alerts/bulk                 # Delete Canceled Alerts
GET    /suite-api/api/alerts/contributingsymptoms
GET    /suite-api/api/alertdefinitions
POST   /suite-api/api/alertdefinitions
PUT    /suite-api/api/alertdefinitions
POST   /suite-api/api/alertdefinitions/query
DELETE /suite-api/api/alertdefinitions/{id}
```

**Reports & report definitions** `[9.0+9.1]` [S23] — fully verified paths:
```
GET    /suite-api/api/reports          # filter by name, subject, status, resourceId; paginated
POST   /suite-api/api/reports
GET    /suite-api/api/reports/{id}
DELETE /suite-api/api/reports/{id}
GET    /suite-api/api/reports/{id}/download
GET    /suite-api/api/reportdefinitions
GET    /suite-api/api/reportdefinitions/{id}
GET    /suite-api/api/reportdefinitions/{id}/schedules
POST   /suite-api/api/reportdefinitions/{id}/schedules
PUT    /suite-api/api/reportdefinitions/{id}/schedules
GET    /suite-api/api/reportdefinitions/{id}/schedules/{scheduleId}
DELETE /suite-api/api/reportdefinitions/{id}/schedules/{scheduleId}
```

**Dashboards** — UNVERIFIED. No dashboard endpoints appear in the VCF Operations API category
list for either 9.0 [S16] or 9.1 [S3], and a targeted lookup returned none [S24]. Do not assume
a `/suite-api/api/dashboards` path exists in 9.x. See Gaps.

**Capacity / cost** `[9.0]` [S16]: categories "Chargeback Billing", "Chargeback Reports",
"Cost Configuration", "Optimization", "Recommendations".
`[9.1]` adds these concrete paths, all new in 9.1 [S10]:
```
GET  /suite-api/api/chargeback/bills/{id}/download/
GET  /suite-api/api/chargeback/notifications/rules/
POST /suite-api/api/chargeback/notifications/rules/
GET  /suite-api/api/optimization/datacenters/{dataCenterId}/exclusion/tags/
PUT  /suite-api/api/optimization/datacenters/{dataCenterId}/exclusion/tags/
POST /suite-api/api/optimization/reclaim/orphaneddisks/{id}/exclude/
POST /suite-api/api/optimization/rightsizing/vms/{id}/exclude/
POST /suite-api/api/whatif/scenarios/
GET  /suite-api/api/whatif/scenarios/
POST /suite-api/api/whatif/scenarios/run/
```

**Fleet management (9.1 only)** — all new in 9.1 [S10], absent in 9.0 [S16]:
```
# Certificates
GET  /suite-api/api/fleet-management/certificate-management/certificate-authorities/
PUT  /suite-api/api/fleet-management/certificate-management/certificate-authorities/
POST /suite-api/api/fleet-management/certificate-management/certificates/query/
GET  /suite-api/api/fleet-management/certificate-management/csrs/
POST /suite-api/api/fleet-management/certificate-management/csrs/

# IAM — components, roles, auth sources
GET    /suite-api/api/fleet-management/iam/components/
POST   /suite-api/api/fleet-management/iam/components/auth-sources/
DELETE /suite-api/api/fleet-management/iam/components/auth-sources/
GET    /suite-api/api/fleet-management/iam/components/roles/
POST   /suite-api/api/fleet-management/iam/components/roles/
PUT    /suite-api/api/fleet-management/iam/components/roles/
GET    /suite-api/api/fleet-management/iam/components/roles/summaries/

# IAM — identity providers
POST /suite-api/api/fleet-management/iam/identity-providers/
PUT  /suite-api/api/fleet-management/iam/identity-providers/
GET  /suite-api/api/fleet-management/iam/identity-providers/{idpConfigId}/ldap-directories/
POST /suite-api/api/fleet-management/iam/identity-providers/{idpConfigId}/ldap-directories/{ldapDirectoryId}/sync/

# IAM — global roles and SSO realms
GET  /suite-api/api/fleet-management/iam/roles/
POST /suite-api/api/fleet-management/iam/roles/
PUT  /suite-api/api/fleet-management/iam/roles/
GET  /suite-api/api/fleet-management/iam/ssorealms/
POST /suite-api/api/fleet-management/iam/ssorealms/

# Passwords
POST /suite-api/api/fleet-management/password-management/accounts/query/
PUT  /suite-api/api/fleet-management/password-management/accounts/{passwordAccountKey}/password/
```

**Diagnostics / findings (9.1 only)** [S10]:
```
POST /suite-api/api/diagnostics/findings/query/
POST /suite-api/api/diagnostics/findings/{ruleUuid}/affectedobjects/query/
```
`[9.1]` The What's New corroborates: "Public Findings APIs for integration with internal
reporting/monitoring" [S1].

**Salt / configuration management (9.1 only)** [S10]:
```
GET  /suite-api/api/salt/resources/statuses/
POST /suite-api/api/salt/resources/{id}/enable/
GET  /suite-api/api/salt/tasks/{taskId}/
```

**Logs management on the Operations appliance (9.1 only)** [S10]:
```
GET  /suite-api/api/logs/queryconfigs/
POST /suite-api/api/logs/queryconfigs/
```

**Agent / collector certificate renewal (9.1 only)** [S10]:
```
POST /suite-api/api/applications/agents/certificates/renew/
POST /suite-api/api/applications/agents/{id}/certificates/renew/
GET  /suite-api/api/applications/agents/{id}/certificates/renew/status/
POST /suite-api/api/collectorgroups/{id}/certificates/renew/
GET  /suite-api/api/collectorgroups/{id}/certificates/renew/status/
POST /suite-api/api/collectors/{id}/certificates/renew/
GET  /suite-api/api/collectors/{id}/certificates/renew/status/
```

**Integrations & adapter identifiers (9.1 only)** [S10]:
```
GET  /suite-api/api/integrations/services/
GET  /suite-api/api/integrations/services/{serviceKey}/certificates/
POST /suite-api/api/integrations/services/{serviceKey}/csrs/
GET  /suite-api/api/adapterkinds/{adapterKindKey}/resourcekinds/{resourceKindKey}/identifiers/
```
The `{serviceKey}` in `/integrations/services/` is the same notion as the `serviceKeys` used in
`auth/token/exchange` (`ops-li`, `VCF_VODAP`) [S10][S18][S19] — inferred, not stated verbatim.

### Log Management API (Operations for Logs) `[9.1]`

`[9.1]` Hosted as its own reference: "Log Management API" [S2][S18]. Covers "v2 API endpoints"
[S18]. Auth is `X-JWT-Token` obtained via `POST /suite-api/api/auth/token/exchange` with
`{"serviceKeys": ["ops-li"]}` [S18].

Top-level categories: Agent Groups, Agent Secret, Extracted Fields, Ingest, Log Forwarder,
**Query** [S18].

UNVERIFIED — concrete Log Management endpoint paths. Repeated attempts to load the operation
index and the Query category returned "Object Not Found" from the portal [S25][S26]. The
category landing page for Query is `https://developer.broadcom.com/xapis/log-management-api/latest/query/`
[S25]. Do not assume the legacy Log Insight `/api/v2/events/{constraints}` shape carries over
without checking the live appliance.

`[9.0]` For 9.0 the equivalent surface appears as the "Log Management" category **inside** the
VCF Operations API [S16], not as a standalone reference — a separate "Log Management API"
reference is not listed for 9.0.

### Real-Time Metrics API `[9.1]` — new in 9.1

`[9.1]` "The Real-Time Metrics component provides Prometheus-compatible APIs for querying real
time metrics collected from VMware vCenter environments." [S19] Categories: Metadata,
Prometheus Expression (PromQL), Vc Metrics Config [S19]. Auth: OpsToken → service key
(`type = VCF_VODAP`) → exchange → `Authorization: Bearer <jwt-token>` [S19].
Corroborated by the What's New: "PromQL-based custom queries with saved dashboards", default
sampling 20 seconds configurable to 2 seconds for ESX, TopN charts [S1].
No 9.0 counterpart — "Real-time metrics" is absent from the 9.0 BOM [S8].

### VCF Operations for Networks API `[9.0+9.1]`

`[9.0+9.1]` Reference exists with an explicit version selector offering "9.1(Latest)" and "9.0"
[S20]. Categories visible: Applications, Authentication, Config, Entities, and others [S20].
Auth headers as given above [S17].
UNVERIFIED — base path and concrete operation paths. The operation index rendered
"Object Not Found" on fetch [S20].

### Fleet LCM / SDDC LCM Service APIs `[9.1]`

`[9.1]` "VCF Fleet LCM Service APIs" [S2][S22] with categories: Components, Config, Depot
Metadata, Fleet Lcm System, Health, Network, Release Version, Resources, Sddc Lcm, Support
Bundles, Supported Components, Task, Upgrade Plan [S22].
`[9.1]` "VCF SDDC LCM Service APIs" also listed [S2].
UNVERIFIED — base paths and concrete operation paths for both.

### Orchestrator and HCX APIs

`[9.0+9.1]` "VCF Operations Orchestrator API" is listed on the portal [S2].
`[9.0+9.1]` HCX exposes "HCX Manager Appliance Management APIs" and "HCX Workload Migration
APIs" as separate references [S2].
UNVERIFIED — base paths, auth and operations for all three; not fetched.
`[9.1]` What's New notes "Non-Disruptive Certificate (NDC) management via HCX REST APIs" [S1].

---

## 9.0 → 9.1 Delta Table

| Area | 9.0 | 9.1 | Source |
|---|---|---|---|
| Fleet Management appliance | Standalone "VCF Operations fleet management" appliance in BOM (9.0.0.0 / 24695816) | "the standalone VCF Operations Fleet Management Appliance no longer exists and is replaced by fleet lifecycle" | [S8][S1] |
| Lifecycle components | One component: Operations fleet management | Two: "Fleet lifecycle" (25371109) + "SDDC lifecycle" (25371107) | [S8][S9] |
| Log product name | "VCF Operations for logs" (+ Agent) | "Log management"; upgrade supported from Operations for Logs 8.18 and 9.0 | [S8][S9][S1] |
| Collector name | "VCF Operations collector" | "Cloud proxy" | [S8][S9] |
| Real-time metrics | Not in BOM | "Real-time metrics" 9.1.0.0 (25346020); Prometheus/PromQL API | [S8][S9][S19] |
| License server | Not in BOM | "License server" 9.1.0.0 (25346031); "License server automatically installed during setup" | [S9][S1] |
| Software depot / Telemetry / Services runtime | Not in BOM | Present as BOM components | [S8][S9] |
| SDDC Manager | Present, 9.0.0.0 (24703748) | Present, "VCF Installer/SDDC Manager 9.1.0.0 (25371088)"; scale doubled to "5000 hosts per VCF Instance", "256 simultaneous cluster upgrades" | [S8][S9][S1] |
| VCF Operations API — new ops | baseline | **134 new operations, 0 deprecated, 0 deleted** | [S6] |
| API: fleet-management tree | Absent from category list | `/suite-api/api/fleet-management/{certificate-management,iam,password-management}/...` | [S16][S10] |
| API: diagnostics/findings | Absent | `POST /suite-api/api/diagnostics/findings/query/` etc.; "Public Findings APIs" | [S16][S10][S1] |
| API: salt | Absent | `/suite-api/api/salt/...` | [S16][S10] |
| API: whatif | Absent | `/suite-api/api/whatif/scenarios/...` | [S16][S10] |
| API: token exchange | Absent | `POST /suite-api/api/auth/token/exchange/` | [S16][S10] |
| API: VIDB discovery | Absent | `GET /suite-api/api/auth/sources/vidb/well-known-url/` | [S16][S10] |
| OAuth 2.0 API tokens | Not mentioned | "OAuth 2.0 API tokens for secure automation"; `/fleet-management/iam/ssorealms/{id}/{api-tokens,api-clients,oauth-apps,emergency-clients}/` | [S1][S10] |
| Classic token acquire flow | `POST /suite-api/api/auth/token/acquire`, `Authorization: OpsToken`, 6h TTL | **Unchanged** | [S14][S15] |
| Java/Python SDK coverage | SDDC Manager, VCF Installer, vCenter, vSAN Data Protection | Adds NSX, **VCF Operations, Log Management, Operations for Networks, Fleet Lifecycle, SDDC Lifecycle** | [S27][S28] |
| PowerCLI | (baseline) | Adds VMware.Vcf.Sso, VMware.Vcf.SddcManager, VMware.VimAutomation.Vpc, .Storage, .Core, VMware.ImageBuilder | [S28] |
| HCX lifecycle | HCX in BOM, no LCM via Operations | "HCX Manager deployed/managed/upgraded via VCF Operations"; existing instances onboarded; VCF SSO + VCF Roles for HCX; FIPS 140-3 | [S8][S1] |
| UI structure | "a new Operate Experience" | Four pillars: Build, Manage, Operate, Protect | [S29][S1] |
| Operations for Networks | present | Health & Diagnostics dashboards, VPC Planning, IPFIX for VKS/Antrea, **legacy NSX dashboards deprecated** | [S8][S1] |
| Orchestrator | present 9.0.0.0 | Up to two script repositories (Python/PowerShell), default error handler, configurable session timeout | [S8][S1] |
| Deprecations | — | HCX PhotonOS appliance (removal target VCF 10.0.0); VCD support (removal target VCF 9.2.0); legacy NSX dashboards | [S1] |

---

## Lookup patterns

### On-appliance API discovery

`[9.0+9.1]` Swagger UI, verbatim from the docs [S12b]:
```
https://operations.example.com/suite-api/doc/swagger-ui.html
```
"Swagger based API documentation is available with the product, with the capability of making
REST API calls right from the landing page." "To access the API documentation, you must first
log into VCF Operations at the URL of your VCF Operations instance." [S12b]

Language-specific client bindings are served from [S12b]:
```
https://operations.example.com/suite-api/
```

Note the singular `doc` (not `docs`) in the swagger path — this is as printed in the source.

### Portal reference patterns

Version-pinnable reference URLs on the developer portal:
```
https://developer.broadcom.com/xapis/vcf-operations-api/{9.0|9.1|latest}/
https://developer.broadcom.com/xapis/vcf-operations-api/{version}/operation-index/
https://developer.broadcom.com/xapis/vcf-operations-api/{version}/changelog/
https://developer.broadcom.com/xapis/vcf-operations-api/latest/api-security-schema/
https://developer.broadcom.com/xapis/vcf-operations-api/latest/suite-api/api/{path}/{method}/
```
The last form is the per-operation deep link; e.g. `.../suite-api/api/alerts/get/` and
`.../suite-api/api/reports/get/` both resolve [S21][S23]. Verified that `9.0` and `9.1` are
both valid version segments for `vcf-operations-api` [S16][S10] and for
`vcf-operations-for-networks-api` [S20].

Sibling references [S2]:
```
https://developer.broadcom.com/xapis/log-management-api/latest/
https://developer.broadcom.com/xapis/realtime-metrics-api/latest/
https://developer.broadcom.com/xapis/vcf-operations-for-networks-api/latest/
https://developer.broadcom.com/xapis/vcf-operations-orchestrator-api/latest/
https://developer.broadcom.com/xapis/vcf-fleet-lcm-service-apis/latest/
https://developer.broadcom.com/xapis/vcf-sddc-lcm-service-apis/latest/
https://developer.broadcom.com/xapis/sddc-manager-api/latest/
https://developer.broadcom.com/xapis/vcf-installer-api/latest/
https://developer.broadcom.com/xapis/hcx-manager-appliance-management-apis/latest/
https://developer.broadcom.com/xapis/hcx-workload-migration-apis/latest/
https://developer.broadcom.com/xapis/vcf-business-services-console-apis/latest/
```

### OpenAPI specs in source control

`[9.0+9.1]` `https://github.com/vmware/vcf-api-specs` — "This all-in-one repo will allow
developers to rapidly develop applications in a preferred programming language and scripts that
automate administration, management and operation for VCF product offerings." Specs live under
`/specifications`. Products with OpenAPI specs include: vSphere, NSX, SDDC Manager, VCF
Installer, vSAN Data protection, **VCF Fleet lifecycle**, **VCF SDDC lifecycle**, **VCF
Operations**, **VCF Operations for networks**, **VCF Log Management**, **VCF Real-time metrics**
[S30]. This product list is itself strong corroboration of the 9.1 component decomposition.
UNVERIFIED — per-version subdirectory layout inside `/specifications`; GitHub tree listing is
robots-disallowed to the fetch tool and the GitHub contents API returned 403 [S30].

### Doc-set URL patterns

```
https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/{9-0|9-1}/{section}.html
```
Sections verified present in both doc sets: `infrastructure-operations`,
`workload-monitoring-and-observability`, `cost-and-capacity-management`, `fleet-management`,
`security-and-compliance`, `lifecycle-management`, `release-notes`,
`administration-sdks-cli-and-tools` [S31][S32].

The Operations API topics live under:
```
.../{9-0|9-1}/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/
    getting-started-with-the-api/acquire-an-authentication-token.html
    client-workflow-overview/vrealize-operations-manager-api-rest-requests.html
    using-the-api-with-vrealize-operations-manager.html
```
Note the legacy `vr-ops` / `vrealize-operations-manager` slugs persist in 9.1 URLs even though
the product name is VCF Operations [S15][S12b].

---

## Gaps and Ambiguities

1. **9.0 Fleet Management Appliance deployment page unreadable.** The topic
   "Deploy the VCF Operations fleet management Appliance" [S13] returned HTTP 403 from the
   fetch proxy on two attempts. Its existence and title are verified via search result
   metadata [S13] and via the 9.1 statement that it "no longer exists" [S1], but the OVA name,
   sizing, and its exact division of duties with SDDC Manager in 9.0 are
   **UNVERIFIED — could not retrieve**.

2. **Dashboards API.** No dashboard endpoints found in the VCF Operations API for 9.0 [S16],
   9.1 [S3], or a targeted index lookup [S24]. Legacy vROps had `/suite-api/api/dashboards`;
   whether it persists undocumented in 9.x is **UNVERIFIED**. An agent should check the
   on-appliance swagger UI [S12b] before relying on it.

3. **Stats/metrics and custom-group literal paths.** Operation *names* verified (Get Stats,
   Query Latest Stats, Get Top N Stats, Get/Create/Modify Custom Groups) [S11], but the literal
   URL templates were not retrieved. **UNVERIFIED.**

4. **Log Management concrete endpoints.** Portal returned "Object Not Found" for both the
   operation index and the Query category [S25][S26]. Only the auth flow and category names are
   verified [S18]. **UNVERIFIED.**

5. **Operations for Networks base path and operations.** Auth headers verified [S17]; base
   path and operation paths returned "Object Not Found" [S20]. **UNVERIFIED.**
   The commonly-assumed legacy `/api/ni/...` prefix was **not** confirmed anywhere in this
   research — do not assume it.

6. **Fleet LCM / SDDC LCM base paths.** Categories verified [S22], paths not. **UNVERIFIED.**

7. **9.1 auth-source field name.** The 9.1 page says the body "includes the user name,
   password, and authentication source" [S15] but the sample payload shows only `username`
   and `password`. The literal JSON key for auth source (legacy vROps used `authSource`) is
   **UNVERIFIED**.

8. **OAuth 2.0 token payload shapes.** The four `ssorealms/{id}/...` endpoints are confirmed to
   exist in 9.1 [S10] but their request/response bodies were not retrieved. **UNVERIFIED.**

9. **9.0-only Fleet Management topics.** Disaster Recovery, Scaling Management Nodes, and
   Instance Migration appear in the 9.0 sub-page list [S5] but not the 9.1 list [S4]. Whether
   these were removed, renamed, or relocated under Lifecycle Management in 9.1 is
   **UNVERIFIED**.

10. **9.0 What's New for Operations is thin.** The 9.0 platform What's New page [S29] covers
    licensing and "a new Operate Experience" but does not enumerate Operations sub-products,
    unlike the dedicated 9.1 page [S1]. The 9.0 composition in this dossier is therefore
    reconstructed from the BOM [S8] and 9.0.1 release notes [S7] rather than a What's New
    narrative. No dedicated `whats-new-vcf-ops.html` equivalent was located for 9.0.

11. **Version tagging of developer-portal facts.** The portal's `latest` pages [S3][S11][S21]
    [S23] serve 9.1 content by default while the reference as a whole covers 9.0 and 9.1. Where
    an endpoint is also present in the 9.0 category list [S16], it is tagged `[9.0+9.1]`;
    where the 9.1 changelog explicitly flags it as new, it is tagged `[9.1]`. Endpoints tagged
    `[9.0+9.1]` on category-presence alone (alerts, reports, resources) carry a small risk that
    parameter details differ between versions.

12. **Rate limiting.** techdocs.broadcom.com returned HTTP 429 on several attempts, requiring
    pacing. Some secondary pages were therefore not fetched, notably the 9.0
    `client-workflow-overview/...rest-requests.html` topic and the per-category
    developer-portal pages for Orchestrator and HCX.

---

## Source Inventory

| ID | URL | Doc set version | Date accessed | Covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-ops.html | 9.1 | 2026-07-31 | Full 9.1 VCF Ops What's New; Fleet Lifecycle replacing Fleet Mgmt Appliance (verbatim); SDDC Manager scale; Log Management; RTM; Networks; HCX; Orchestrator; deprecations |
| S2 | https://developer.broadcom.com/xapis | portal, undated | 2026-07-31 | Master list of VCF API references and their URLs |
| S3 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/ | 9.1 (latest), notes 9.0 | 2026-07-31 | VCF Operations API overview; auth schemes; 40+ category list |
| S4 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/fleet-management.html | 9.1 | 2026-07-31 | 9.1 Fleet Mgmt scope; "No dedicated Fleet Management Appliance exists"; SDDC Manager password role; sub-page list |
| S5 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/fleet-management.html | 9.0 | 2026-07-31 | 9.0 Fleet Mgmt scope and sub-page list; shared "For VCF, you use VCF Operations..." sentence |
| S6 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-changelog.html | 9.1 | 2026-07-31 | VCF Operations API: 134 new / 0 deprecated / 0 deleted operations |
| S7 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-1-release-notes/vcf-operations-9-0-1-0000.html | 9.0.1 | 2026-07-31 | 9.0.1 component names, versions, builds incl. Fleet Management and Logs Agent |
| S8 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | 9.0 | 2026-07-31 | Full 9.0 BOM incl. SDDC Manager and all Operations components |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html | 9.1 | 2026-07-31 | Full 9.1 BOM incl. Fleet lifecycle, SDDC lifecycle, Log management, Cloud proxy, Real-time metrics |
| S10 | https://developer.broadcom.com/xapis/vcf-operations-api/9.1/changelog/ | 9.1 | 2026-07-31 | Concrete list of operations new in 9.1, grouped by category, with exact paths |
| S11 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/suite-api/api/resources/get/ | 9.1 (latest) | 2026-07-31 | GET /suite-api/api/resources params; sibling stats/groups/profiles operation names; host form |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/upgrading-cloud-foundation/preparing-your-vcf-9-management-components/upgrading-management-components/upgrade-to-vcf-operations.html | 9.0 | 2026-07-31 | Title only, via search: "Upgrade VMware Aria Operations to VCF Operations 9.0" |
| S12b | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/using-the-api-with-vrealize-operations-manager.html | 9.0 | 2026-07-31 | On-appliance swagger UI URL `/suite-api/doc/swagger-ui.html`; client bindings URL |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/upgrading-cloud-foundation/preparing-your-vcf-9-management-components/preparing-to-upgrade-to-vmware-cloud-foundation/install-the-vcf-operations-fleet-management-appliance.html | 9.0 | 2026-07-31 | Title only, via search: "Deploy the VCF Operations fleet management Appliance". Body HTTP 403 on 2 attempts |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html | 9.0 | 2026-07-31 | 9.0 token acquire endpoint, payload, response, header formats, 6h TTL |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html | 9.1 | 2026-07-31 | 9.1 token acquire — identical to 9.0; auth sources; explicit 6h TTL quote |
| S16 | https://developer.broadcom.com/xapis/vcf-operations-api/9.0/ | 9.0 | 2026-07-31 | 9.0 API category list; absence of fleet-management, findings, salt, whatif |
| S17 | https://developer.broadcom.com/xapis/vcf-operations-for-networks-api/latest/api-security-schema/ | 9.1 (latest) | 2026-07-31 | Networks auth: `Authorization: NetworkInsight {token}` and Bearer JWT |
| S18 | https://developer.broadcom.com/xapis/log-management-api/latest/ | 9.1 (latest) | 2026-07-31 | Log Management API v2; X-JWT-Token via token/exchange with serviceKeys ["ops-li"]; categories |
| S19 | https://developer.broadcom.com/xapis/realtime-metrics-api/latest/ | 9.1 (latest) | 2026-07-31 | RTM Prometheus-compatible API; VCF_VODAP service key exchange; Bearer JWT; categories; `/suite-api/api/` host form |
| S20 | https://developer.broadcom.com/xapis/vcf-operations-for-networks-api/latest/operation-index/ | 9.1 latest + 9.0 selector | 2026-07-31 | Confirms 9.0 and 9.1 versions exist; category names; operation detail returned "Object Not Found" |
| S21 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/suite-api/api/alerts/get/ | 9.1 (latest) | 2026-07-31 | Alerts and alertdefinitions exact paths and params |
| S22 | https://developer.broadcom.com/xapis/vcf-fleet-lcm-service-apis/latest/api-security-schema/ + .../latest/ | 9.1 (latest) | 2026-07-31 | Fleet LCM auth schemes (Basic, Bearer JWT); category list |
| S23 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/suite-api/api/reports/get/ | 9.1 (latest) | 2026-07-31 | Reports and reportdefinitions exact paths incl. download and schedules |
| S24 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/operation-index/ | 9.1 (latest) | 2026-07-31 | Category navigation; no dashboard endpoints found; Super Metrics / Resource / Resources category URLs |
| S25 | https://developer.broadcom.com/xapis/log-management-api/latest/operation-index/ | 9.1 (latest) | 2026-07-31 | Returned "Object Not Found"; yielded Query category URL only |
| S26 | https://developer.broadcom.com/xapis/log-management-api/latest/api/v2/events/query/post/ | 9.1 (latest) | 2026-07-31 | Returned "Object Not Found" — speculative path not confirmed |
| S27 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html | 9.0 | 2026-07-31 | 9.0 SDK component coverage (SDDC Manager, VCF Installer, vCenter, vSAN DP); SDK URLs |
| S28 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | 9.1 | 2026-07-31 | 9.1 SDK additions incl. VCF Operations, Log Management, Ops for Networks, Fleet LCM, SDDC LCM; PowerCLI modules |
| S29 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new.html | 9.0 | 2026-07-31 | 9.0 "new Operate Experience"; licensing/fleet licensing model; connected vs disconnected mode |
| S30 | https://github.com/vmware/vcf-api-specs | repo, undated | 2026-07-31 | OpenAPI spec product list incl. VCF Operations, Ops for networks, Log Management, Real-time metrics, Fleet lifecycle, SDDC lifecycle; `/specifications` layout |
| S31 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | 9.1 | 2026-07-31 | 9.1 doc-set section URLs |
| S32 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | 9.0 | 2026-07-31 | 9.0 doc-set section URLs incl. administration-sdks-cli-and-tools |
