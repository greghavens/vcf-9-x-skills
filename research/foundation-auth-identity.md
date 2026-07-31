# VCF 9.0 / 9.1 Foundation Layer — Identity, Auth, Certificates, Network

**Research date:** 2026-07-31
**Scope:** identity/SSO, roles & permissions, certificate management, API token acquisition per product, network reachability.
**Rule applied:** every fact below traces to a page fetched on 2026-07-31 (see `## Source Inventory`). Anything not retrievable is marked `UNVERIFIED — could not retrieve`.

Version tags: `[9.0]`, `[9.1]`, `[9.0+9.1]` (verified independently in both doc sets).

---

## Auth Matrix

| Product | Version | Method + Path | Payload | Token field | Subsequent header | Source ref |
|---|---|---|---|---|---|---|
| **SDDC Manager** | `[9.0]` | `POST /v1/tokens` | `{"username":"string","password":"string"}` (JSON) | `accessToken` (JWT); `refreshToken.id` (UUID) | `Authorization: Bearer <accessToken>` | S42, S43 |
| **SDDC Manager** — refresh | `[9.0]` | `PATCH /v1/tokens/access-token/refresh` | plain-text refresh-token UUID | response body **is** the raw JWT (not JSON-wrapped) | as above | S42, S43 |
| **SDDC Manager** — revoke | `[9.0]` | `DELETE /v1/tokens/refresh-token` | plain-text refresh-token UUID | n/a (204 No Content) | n/a | S42 |
| **SDDC Manager** | `[9.1]` | Tokens API present with the same three operations ("Create Token", "Refresh Access Token", "Invalidate Refresh Token") in the 9.1 reference. Exact 9.1 paths/schemas not rendered on the fetched index page — **paths carried over from 9.0 are PRESUMED, not verified for 9.1.** | — | — | — | S41 |
| **VCF Identity Broker** (VCF SSO token endpoint) | `[9.1]` | `POST https://{api_host}/acs/t/{tenant}/token` | `application/x-www-form-urlencoded`; `grant_type` (required — `authorization_code`, `password`, `client_credentials`, `refresh_token`, or extended); optional `client_id`, `client_secret`, `refresh_token`, **`api_token`**, `code`, `username`, `password`, `scope`, `redirect_uri`, `domain`, `assertion`, `code_verifier`. HTTP Basic auth supported on the endpoint. | `access_token`; also `token_type` (= `"Bearer"`), `expires_in` (seconds), `refresh_token`, `id_token`, `scope` | `Authorization: Bearer <access_token>` | S39, S40 |
| **vCenter** (vSphere Automation REST) | `[9.0+9.1]` | Create session, then reuse session id. Security schemes documented identically in both doc sets: HTTP `basic`; apiKey in header `vmware-api-session-id`; HTTP `bearer` (federated vCenter). | Basic credentials on the session-create call | session id string (e.g. `b00db39f948d13ea1e59b4d6fce56389`) | `vmware-api-session-id: <session-id>` | S36 (9.1), S37 (9.0), S35, S38 |
| **vCenter** — session path | `[9.1]` | Two forms observed in 9.1 sources: `POST /api/cis/session` (S35) and `POST /session` / `DELETE /session` (S38). See `## Gaps and Ambiguities`. | — | — | `vmware-api-session-id` | S35, S38 |
| **vCenter** — token issue | `[9.1]` | `POST /vcenter/authentication/token` — "issue"; added in vSphere API 7.0.2.0. Request params & response fields **not rendered** on the fetched page. | UNVERIFIED | UNVERIFIED | UNVERIFIED | S67 |
| **NSX Manager** | `[9.0]` | `POST /api/session/create` | `application/x-www-form-urlencoded`: `j_username=<user>&j_password=<pass>` | Session cookie `JSESSIONID` + response header `x-xsrf-token` | **Both** required: `Cookie: JSESSIONID=<id>` and `x-xsrf-token: <token>` | S31 |
| **NSX Manager** — logout | `[9.0]` | `/api/session/destroy` | cookie + xsrf header | n/a | n/a | S31 |
| **NSX Manager** | `[9.1]` | UNVERIFIED — could not retrieve (9.1 `advanced-network-management/authentication-and-authorization` page returned HTTP 429 on every attempt). 9.1 NSX section exists at S30-equivalent path. | — | — | — | — |
| **VCF Operations** | `[9.0+9.1]` | `POST https://<host>/suite-api/api/auth/token/acquire` — identical text in both doc sets | `{"username":"vRealize-user","password":"vRealize-dummy-password"}` | `token` (format `<uuid>::<uuid>`); response also carries `expiresAt` and `validity` (ms) | `Authorization: OpsToken <token>`. Legacy `Authorization: vRealizeOpsToken <token>` "continues to be supported". | S12 (9.0), S13 (9.1) |
| **VCF Operations** — token lifetime | `[9.0+9.1]` | — | — | — | "expires after **six hours**" | S12, S13 |
| **VCF Operations** — SSO bearer | `[9.1]` | Same API also accepts `Authorization: Bearer <token>` where the token is "an access token from VCF SSO". Missing/expired/invalid → `401 Unauthorized`. | — | — | `Authorization: Bearer <token>` | S44 |
| **VCF Operations** — other auth ops | `[9.1]` | `POST /auth/token/acquire`, `POST /auth/token/release`, `POST /auth/token/exchange` (exchange for JWT) | — | — | — | S45 |
| **VCF Operations Fleet Management API** | `[9.0]` | No token endpoint documented. **HTTP Basic.** Credential built by `echo -n 'admin@local:<fleet-admin-password>' \| base64` on the Fleet Management appliance. | n/a | n/a | `Authorization: Basic <base64>` — "The word Basic must be present before the Base64 value" | S47 (Broadcom KB 409715) |
| **VCF Automation — VM Apps** (access token) | `[9.0]` | `POST https://{{vcfaHostname}}/tm/oauth/tenant/{{vcfaTenant}}/token` | `Content-Type: application/x-www-form-urlencoded`, `Accept: application/json`; body `grant_type=refresh_token`, `refresh_token={{vcfaAPIToken}}` | Docs say "The response returns the access token" but **do not name the JSON field** | Docs say "an HTTP authentication token in the `Authorization` request header"; **exact format not stated on the page** | S15, S14 |
| **VCF Automation — VM Apps** lifetimes | `[9.0]` | — | — | — | API token (refresh token) default **129600 minutes / 90 days**; access token default **one hour** | S14, S15 |
| **VCF Automation — All Apps / Provider** | `[9.1]` | Token endpoint URL not stated in the fetched reference. Auth schemes: **JWT via `Authorization` header (recommended)**; `x-vcloud-authorization` session header **deprecated**. Context headers: `X-VMWARE-VCLOUD-TENANT-CONTEXT`, `X-VMWARE-VCLOUD-AUTH-CONTEXT`. | UNVERIFIED | UNVERIFIED | `Authorization: <JWT>` | S46 |
| **vSAN** | `[9.0]` | No independent auth. vSAN Management APIs "depend on the vSphere Web Services API for login procedures" — authenticate to vCenter and reuse that session. | see vCenter | see vCenter | see vCenter | S68 |
| **vSAN / unified session** | `[9.0]` | Session established on vSphere Web Services API (`/vim25`) can be reused on vSphere Automation API (`/api`); both recognise `vmware-api-session-id`. VCF SDK 9.0 consolidates vSphere, vSAN, vSAN Data Protection and SDDC Manager. | — | — | `vmware-api-session-id` | S58 (Broadcom/VMware blog, 2025-11-19) |
| **Supervisor / VKS** — SSO or external IDP | `[9.0+9.1]` | `vcf context create <context_name> --endpoint=<SUPERVISOR_ENDPOINT> --type=k8s --username=<user_name>` | interactive credentials | writes kubeconfig (`.kube/config`) | kubeconfig-managed bearer token | S33 (9.0), S34 (9.1), S63 |
| **Supervisor / VKS** — VCF Automation-registered | `[9.1]` | `export VCF_CLI_VCFA_API_TOKEN=<api_token>` then `vcf context create vcfa_ctx -e $VCFA_ENDPOINT --api-token $VCF_CLI_VCFA_API_TOKEN --tenant-name $TENANT_NAME --ca-certificate vcfa.cert` | API token from VCF Automation **My Account → API Tokens** | kubeconfig context | kubeconfig-managed | S34 |
| **VCF Fleet Manager (9.1 equivalent)** | `[9.1]` | The 9.1 doc set has no product named "VCF Fleet Manager". Fleet-level identity/API-client management lives under **Fleet Management → Identity & Access → VCF SSO Overview → API Access**. Token issuance is via the Identity Broker endpoint (row 2). | — | — | — | S11, S16 |

### API client / API token issuance (UI flow) `[9.1]`

Path: **VCF Operations → Manage → Fleet Management → Identity & Access → VCF SSO Overview → select identity broker → API Access → API Clients → Create**.
- Client creation: name (ID auto-populates), optional description → **Create API Client**. Then in **Roles**: select scope, choose role, enter validity period → Save. (S11)
- Token generation: ellipsis → **Generate API Token**. Fields: *API Token Name*; *API Token TTL* — **default 30 days**, max bounded by Fleet Settings → IAM Setting; *Access Token TTL* — **default 30 minutes**, max bounded by IAM Settings; Description. (S11)
- **The token cannot be retrieved after clicking Continue.** (S11)
- **Emergency Access Client**: break-glass client providing "high-privilege and long-lived access tokens to critical systems when standard methods fail". (S51)

### IAM ceilings `[9.1]` (S52)
- API Token Expiry — **max 180 days**
- Access Token Expiry — **max 480 minutes**
- Expired API Token Retention Period — **max 90 days**
- *JIT User Inactivity Period*: once a JIT user is inactive, "previously issued API tokens cannot retrieve access tokens until the user authenticates again" — **a silent token-death mode API clients must handle.**
- `ALL_USERS` group is optional and scoped per identity broker, **not aggregated across brokers**.
- Defaults for these settings are not published on the page (only maxima). `UNVERIFIED — defaults`

---

## 1. Identity / SSO Architecture — 9.0 vs 9.1

### Common to both `[9.0+9.1]`
- **A unified identity broker exists in both versions.** It is called the **VCF Identity Broker**, configured through the VCF Operations console. (S18, S24)
- Federated components in both doc sets, listed identically: **vCenter, VCF Operations, VCF Automation, log management (VCF Operations for Logs), VCF Operations for Networks, VCF Operations orchestrator, VCF Operations HCX, NSX**. (S18, S24)
- **Explicitly excluded from SSO in both: SDDC Manager and ESX.** This is the single most important constraint for an API client — SDDC Manager auth is *not* SSO-brokered and uses its own `/v1/tokens` flow. (S18, S24)
- Deployment modes, both versions: **embedded** (inside management-domain vCenter) or **standalone appliance**. In 9.0 the appliance is described as a **three-node cluster supporting up to five connected VCF Instances**. (S19, S24)
- Supported IdPs `[9.0]`: Okta, Ping Identity, Microsoft Entra ID, Microsoft AD FS, "Any SAML 2.0 Identity Providers", AD/LDAP, OpenLDAP. Protocols: **SAML 2.0** and **OIDC** for authentication; **SCIM 2.0, JIT, AD/LDAP** for user/group provisioning. (S23)

### What changed in 9.1
1. **Documentation and feature promotion.** In 9.0 the section is `Fleet Management → Configuring VCF Single Sign-On`. In 9.1 it becomes `Fleet Management → **Managing Identity and Access Using VCF Single Sign-On**`, gaining three new child areas that do not exist in 9.0: **Managing VCF Roles**, **Provisioning vCenter Custom Roles**, and **Managing API Clients and Tokens**. (S16 vs S18)
2. **API clients and API tokens are a 9.1 feature.** The 9.0 "Managing VCF Single Sign-On" tree contains **no API client, API token, OAuth client, or role management pages** — its children are limited to SSO overview, reset, change IdP, change deployment mode, edit IdP config, additional component configurations, deregister configurations, and change identity management. (S53) In 9.1 there is a dedicated **Managing API Clients and Tokens** subtree with client creation, token generation, edit/delete/regenerate, emergency access client, and IAM settings. (S51)
   - Practical consequence: **a non-interactive, role-scoped API token issued by VCF SSO is a 9.1 capability.** For 9.0, per-product credentials (SDDC Manager `/v1/tokens`, VCF Ops `token/acquire`, NSX session cookie, vCenter session) are the documented route.
3. **VCF built-in roles are documented in 9.1** with explicit component mappings (see §2). No equivalent page was found in the 9.0 fleet-management tree. (S20, S53)
4. **vIDM → Identity Broker migration is a 9.1 workflow.** (S25) Verbatim consequences for API clients:
   - "Users and groups are migrated from VMware Identity Manager to identity broker."
   - **"OAuth clients are not migrated automatically. You must manually regenerate the client and secret using identity broker and configure accordingly."** — *any 9.0-era OAuth client breaks on upgrade.*
   - "Local accounts and local accounts with multifactor authentication are not supported."
   - "Multifactor authentication with Active Directory is not supported."
   - Sync settings are compared but not migrated; must be adjusted manually. If VCF Operations, VCF Automation, or NSX use the legacy system, the migration script repoints them.
5. **VCF Operations API accepts VCF SSO bearer tokens in 9.1** (`Authorization: Bearer <token>`) alongside `OpsToken`. (S44) The 9.0 doc set page describes only `OpsToken`/`vRealizeOpsToken`. (S12)
6. **SSO topology models are formalised in the 9.1 design library**: *VCF Fleet-Wide SSO Model* (one identity broker for the whole fleet), *Cross VCF Instance SSO Model* (multiple brokers, each serving a set of instances), *Single VCF Instance SSO Model* (one broker per instance). Constraint: all workload-domain components in a single VCF instance must connect to the same identity broker — **"split-SSO configurations … are not supported."** Fleet management components may connect to any broker, same-instance recommended. (S56)
7. **PowerCLI 9.1 gains first-class token auth**: new `VcfOAuthSecurityContext` parameter on `Connect-VIServer`, `Connect-NsxServer`, `Connect-VcfOpsServer`, and a new `VcfApiToken` parameter enabling "authentication either by instantiating a VcfOAuthSecurityContext … or just by an API token". (S48)
8. **vCenter Group Federated API (VGFA)** — new in 9.1, "a single unified API endpoint for managing all vCenter instances in a vCenter group". (S48)

### 9.0 SSO configuration order `[9.0]` (S54)
1. Select a VCF Instance → 2. Choose deployment mode → 3. Select and configure the identity provider → 4. Configure VCF SSO for **NSX and vCenter** → 5. Configure VCF SSO for **VCF Operations and VCF Automation** → 6. (Optional) other components (HCX, networks, orchestrator, logs) → 7. **Assign required roles and permissions for users or groups** — note step 7 is performed *in the individual components*, not centrally.

### VCF SSO Architecture detail pages
`UNVERIFIED — could not retrieve` for token-flow/trust/port internals. Both `sso-architecture.html` pages (9.0 S65, 9.1 S66) are navigation stubs stating only that one or more identity brokers may be deployed across instances; they defer to the design library. No page fetched documents the broker↔component trust mechanism or the broker's listening ports.

---

## 2. Roles and Permissions

### VCF-level built-in roles `[9.1]` (S20)
"VCF roles are mapped to the individual VCF component roles"; "built-in VCF roles cannot be modified."

| VCF role | Mapped component roles |
|---|---|
| **VCF Administrator** | vCenter Admin; NSX `enterprise_admin`; VCF Operations Administrator; VCF Automation System Administrator; VCF Operations HCX Migration Admin; VCF Operations orchestrator Orchestrator Administrator |
| **VCF Viewer** | vCenter ReadOnly; NSX `auditor`; VCF Operations ReadOnly |
| **SDDC Administrator** | vCenter Admin; NSX `enterprise_admin`; VCF Operations HCX Migration Appliance Admin; VCF Operations orchestrator Orchestrator Viewer |
| **SDDC Viewer** | vCenter ReadOnly; NSX `auditor` |

Scope levels (global/org/instance) and a full permission matrix are **not** stated on this page. `UNVERIFIED — role scope hierarchy`. 9.1 also documents **Provisioning vCenter Custom Roles** to other vCenters. (S16)

**For an API client:** the minimum role for read-only fleet queries is **VCF Viewer**; write operations against vCenter/NSX require **VCF Administrator** or **SDDC Administrator**. When creating an API client in 9.1 you select a **scope** and a **role** per client. (S11)

### NSX roles `[9.0]` (S32)
15 built-in roles. Enterprise Admin (EA) = "Full access (FA) — All permissions including Create, Read, Update, and Delete (CRUD)". Auditor (A) = read-only. Others: Network Admin, Network Operator, Security Admin, Security Operator, Cloud Admin, Cloud Operator, Cloud Partner Admin, Load Balancer Admin, Load Balancer Operator, VPN Admin, Guest Introspection Partner Admin, Network Introspection Partner Admin, Support Bundle Collector. Custom roles supported. **Principal identities** are the documented mechanism for service-account style API access. (S30, S32)

### VCF Operations roles `[9.1]` (S45)
Managed through the Auth API: `/auth/roles` (CRUD), `/auth/roles/{roleName}/privileges`, `/auth/users/{userId}/permissions`, `/auth/usergroups/{groupId}/permissions`, `/auth/currentuser/permissions`, `/auth/privileges`, `/auth/privilegegroups`. Named roles referenced by the VCF role mapping: **Administrator**, **ReadOnly**. (S20, S45)

### vCenter / Supervisor `[9.0+9.1]` (S33, S34)
"Authentication controls who can access the vSphere environment and authorization controls what resources the users can access." Roles are "sets of privileges"; permissions are granted by "associating a role to a user or group on that object" in the vCenter hierarchy. vCenter SSO is "an authentication broker and security token exchange infrastructure" that "issues a token when a principal … authenticates". External IDPs (Okta, Azure AD) integrate via **Pinniped Supervisor and Concierge** components `[9.1]`. Named namespace roles (owner/edit/view) `UNVERIFIED — could not retrieve`.

### VCF Automation provider/org role model `[9.1]` (S50)
- **Rights**: "Each right provides view or manage access to a particular object type in VCF Automation." Categorised (Catalog, Organization, …); the provider organization contains all system rights.
- **Roles**: "A role is a set of rights that is assignable to one or more users and groups."
- **Provider roles** — exclusive to the provider org; assignable only to provider users; custom provider roles allowed.
- **Global roles** — created/edited/published by System Administrators to one or more organizations; **org administrators cannot modify them**.
- **Organization-specific roles** — created locally by org admins; contain only a subset of organization rights.
- **Rights bundles** — default "Simple Mode" shows read-only built-in bundles; "Advanced Rights Bundle Mode" (feature flag) enables custom bundles.
- "All predefined global roles are published to every organization in the system" by default. **System Administrator** exists only in the provider org and holds all VCF Automation rights.
- Identity: LDAP at system *or* organization level; SAML at organization level; OIDC integration. (S49, S5, S6)

---

## 3. Certificate Management

### `[9.0]` (S21)
- At deployment "each component is assigned a certificate from a default signing Certificate Authority (VMware Certificate Authority CA)".
- "You should replace the default certificates for the management domain components with trusted enterprise CA-signed certificates to provide secure access."
- Supported CA types: **VMCA, Microsoft Certificate Authority, OpenSSL, self-signed**.
- Managed from the **VCF Operations console**: view certificates & alerts, configure a CA, set up automatic renewal, manually renew, generate CSRs, replace with CA-signed, replace with external CA cert.
- Non-disruptive updates / auto-renewal cover **ESXi, vCenter, NSX Manager, SDDC Manager** and VCF services.
- Replace when: expiry imminent/passed, issuing CA revoked them, or (optionally) on new workload domain creation.

### `[9.1]` (S22)
- Same CA options (VMCA default; Microsoft CA; OpenSSL; external CA via CSR).
- **New in 9.1, verbatim:** "Starting with VCF Operations 9.1, you can generate certificate signing requests, renew, import, and replace **multiple certificates simultaneously**."
- Coverage is stated in two explicit tiers:
  - **VCF Management**: VCF Operations, VCF Automation, VCF Operations for Networks, log management, **identity broker**, VCF management services, VCF Operations HCX (HCX requires Management Pack).
  - **VCF Instance/Domain**: ESX, vCenter, NSX Manager, SDDC Manager, **VMware AVI Load Balancer**.
- Auto-renewal: "You can activate automatic renewal of certificates for VCF management components or a VCF instance. Automatic renewal uses the configured Certificate Authority to renew the certificate for each component."

### Trust store / importing CAs `[9.1]` (S57)
- **VCF Operations → Operate → Administration Control Panel → Trusted Certificates → Import.**
- "You can only import certificates that are encoded in the **PEM format**."
- Imported CA certificates apply to: **Authentication Sources (Active Directory, Open LDAP, VMware Identity Manager), Outbound Plugins, and Adapter Endpoint.**
- The page displays thumbprint, issued by, issued to, expiry date, with expiry warnings.
- **It does not state which OS/JVM trust store is modified.** `UNVERIFIED — trust store location`

### TLS-trust pitfalls for API clients (derived from cited facts — flagged as inference where so)
1. **Default state is VMCA-signed, i.e. not publicly trusted.** A stock API client will fail hostname/chain validation against vCenter, NSX, SDDC Manager, VCF Operations until the VMCA root (or the enterprise CA) is added to the client trust store. (S21, S22)
2. **The documented remedy is to replace the certs, not to disable verification.** Both versions say to replace defaults with trusted enterprise CA-signed certificates. (S21, S22) **No fetched Broadcom page documents disabling TLS verification as a supported practice.** The only insecure-flag usage observed in official docs is inside NSX's own `curl` examples, which use `-k`: `curl -i -k -c session.txt -X POST -d 'j_username=… ' https://<nsx-manager>/api/session/create` (S31). Treat `-k` as example-only, not guidance.
3. **`--ca-certificate` is the documented API-client path for Supervisor/VKS**: `vcf context create … --ca-certificate vcfa.cert` (S34). This is the cleanest documented pattern for pinning a self-signed/private CA in a VCF client.
4. **Certificate rotation is a token-invalidation event in practice** — auto-renewal touches ESX, vCenter, NSX Manager, SDDC Manager and the identity broker (S21, S22), so long-lived clients must be prepared to reload their trust bundle. *Inference from the cited component list; the docs do not state token impact.*
5. **The identity broker itself holds a certificate** in the 9.1 VCF Management tier (S22). Because the broker is the token issuer, a stale broker cert breaks every SSO-based API client at once — a single point of TLS failure absent in 9.0's per-product auth. *Inference.*
6. **PEM-only import** for trusted certificates in VCF Operations — DER/PKCS#7 must be converted first. (S57)

---

## 4. Ports / Protocols an API Client Needs

**Primary source is a dynamic tool, not a document.** Both 9.0 and 9.1 Planning and Preparation pages direct readers to the **VMware Ports and Protocols tool at https://ports.broadcom.com/**, described as "a portal that enables you to view all the ports needed by various VMware products, solutions, and services in a single pane". The tool renders client-side and **exposes no static port table to fetch**; product coverage for VCF 9.0/9.1 could not be confirmed. (S28, S29, S64)
→ **`UNVERIFIED — could not retrieve` for the per-service inbound port matrix (vCenter, NSX, SDDC Manager, VCF Operations, identity broker, Supervisor).**

### What *is* verified

**Outbound HTTPS/443 destinations required for online functionality `[9.1]`** (S26):

| URL | Port | Protocol | Purpose |
|---|---|---|---|
| `dl.broadcom.com` | 443 | HTTPS | Binaries download for components (VCF Installer, vCenter, related services) |
| `projects.packages.broadcom.com` | 443 | HTTPS | Binaries download for Supervisor services and VCF services (software depot) |
| `vcsa.vmware.com` | 443 | HTTPS | CEIP telemetry from SDDC Manager and VCF runtime instances |
| `vvs.broadcom.com` | 443 | HTTPS | Compatibility data — VCF Installer, SDDC Manager, download tools |
| `vsanhealth.vmware.com` | 443 | HTTPS | vSAN HCL data — VCF Installer, SDDC Manager, vCenter, download tools |
| `eapi.broadcom.com` | 443 | HTTPS | vSAN HCL data and licensing info for VCF Operations |
| `vcf.broadcom.com` | 443 | HTTPS | Licensing functionality for VCF Operations |
| `auth.esp.vmware.com` | 443 | HTTPS | UMDS for SDDC Manager and download tools |

All connections use **HTTPS on port 443**. The equivalent 9.0 page (`/9-0/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html`) returned **404** — `UNVERIFIED — 9.0 public URL list`.

**Protocol facts confirmed from the API references (all HTTPS):**
- VCF Operations: "clients communicate with the server over HTTP, exchanging representations of VCF Operations objects", over HTTPS. `[9.0]` (S9)
- VCF Operations API clients and servers "communicate over HTTPS". `[9.0]` (S12 parent page)
- vSphere Automation, NSX, SDDC Manager, Identity Broker references all specify `https://` scheme in their endpoint examples. `[9.0+9.1]` (S31, S40, S42, S35)

**DNS is a hard prerequisite `[9.1]`** (S27): "VCF requires unique FQDNs and static IP addresses for VCF components and proper DNS resolution for each FQDN and IP address is required." "FQDNs must point to unique IP addresses that are not assigned and the FQDNs must not be in the IP Ranges assigned to VCF management services nodes."
Components requiring FQDN/IP (first VCF instance): vCenter; NSX Manager (nodes + cluster VIP); SDDC Manager; vSAN; vMotion; VCF Operations (primary, replica, data nodes, load balancer, Cloud Proxy, License Server); VCF Automation; VCF Management Services (fleet/instance components, runtime, **identity broker**, log management, real-time metrics); VCF Operations for Networks (platform + collector nodes). Additional instances: vCenter, NSX Manager, SDDC Manager, vSAN, vMotion, Cloud Proxy, instance components, runtime services, identity broker, real-time metrics.
→ **API clients must resolve the same FQDNs the certificates are issued to; IP-address connections will fail hostname verification.** *Inference from the FQDN/cert facts above.*

**Known path prefixes an API client hits** (reachability targets on 443): `/v1/*` (SDDC Manager, S42), `/suite-api/api/*` (VCF Operations, S12), `/api/session/*` and `/policy/api/v1/*` and `/api/v1/*` (NSX, S31), `/api/*` and `/vim25` (vCenter/vSphere, S35, S58), `/acs/t/{tenant}/token` (Identity Broker, S40), `/tm/oauth/tenant/{tenant}/token` (VCF Automation VM Apps, S15).

**NSX session timeout:** default **1800 seconds (30 minutes)**. `[9.0]` (S31)

---

## 5. 9.0 → 9.1 Delta Table

| Area | 9.0 | 9.1 | Source |
|---|---|---|---|
| Identity broker | **Present.** "VCF Identity Broker", configured via VCF Operations console | **Present**, same name and same federated component list | S18 / S24 |
| Doc section name | `Fleet Management → Configuring VCF Single Sign-On` | `Fleet Management → Managing Identity and Access Using VCF Single Sign-On` | S18 / S16 |
| API clients & API tokens via SSO | **Absent** — no API client/token/OAuth pages in the SSO tree | **Added** — Managing API Clients and Tokens (create client, generate token, edit/delete/regenerate, emergency access client, IAM settings) | S53 / S51, S11 |
| Token TTL controls | Not documented at fleet level | API Token TTL default **30 days** (max 180 d); Access Token TTL default **30 min** (max 480 min); expired-token retention max 90 d | — / S11, S52 |
| Emergency access client | Not documented | **Added** — "high-privilege and long-lived access tokens … when standard methods fail" | — / S51 |
| VCF built-in roles page | Not found in fleet-management tree | **Added** — VCF Administrator, VCF Viewer, SDDC Administrator, SDDC Viewer with per-component mappings | S53 / S20 |
| vCenter custom role provisioning | Not documented | **Added** — "Provisioning vCenter Custom Roles" (push custom roles to other vCenters) | S18 / S16 |
| vIDM → Identity Broker migration | n/a | **Added.** Users/groups migrate; **OAuth clients do NOT** — regenerate client+secret manually. Local accounts, local-account MFA, and AD MFA **not supported** | — / S25 |
| VCF Operations API auth header | `Authorization: OpsToken <t>` (legacy `vRealizeOpsToken` supported) | Same, **plus** `Authorization: Bearer <t>` from VCF SSO | S12 / S13, S44 |
| VCF Operations token endpoint & 6-hour lifetime | `POST /suite-api/api/auth/token/acquire`, 6 h | **Identical text** | S12 / S13 |
| Certificate bulk operations | Single-cert operations | "Starting with VCF Operations 9.1, you can generate CSRs, renew, import, and replace **multiple certificates simultaneously**" | S21 / S22 |
| Certificate coverage list | ESXi, vCenter, NSX Manager, SDDC Manager, VCF services | Split into VCF Management tier (incl. **identity broker**, VCF management services) and VCF Instance tier (incl. **AVI Load Balancer**) | S21 / S22 |
| SSO topology models | Not formalised in fetched pages | Three documented models: Fleet-Wide, Cross VCF Instance, Single VCF Instance; **split-SSO not supported** | — / S56 |
| PowerCLI auth | No token parameters documented | `VcfOAuthSecurityContext` + `VcfApiToken` on `Connect-VIServer`, `Connect-NsxServer`, `Connect-VcfOpsServer` | — / S48 |
| Multi-vCenter API | — | **vCenter Group Federated API (VGFA)** — single unified endpoint for all vCenters in a group | — / S48 |
| New APIs | — | Utilization API; Query API (server-side filtering, pagination, projections) | — / S48 |
| SDKs | Java/Python | Java + Python extended to NSX, VCF Operations, Log Management, Fleet/SDDC Lifecycle; VODAP OpenAPI specs; Java build Gradle → **Maven**; Python 3.13 supported, **3.7/3.8 deprecated** | — / S48 |
| vSphere Automation security schemes | basic / `vmware-api-session-id` / bearer | **Identical** | S37 / S36 |
| SDDC Manager token API | `POST /v1/tokens`, `PATCH /v1/tokens/access-token/refresh`, `DELETE /v1/tokens/refresh-token` | Same three operations listed; paths not re-verified | S42 / S41 |
| Public URL list | 404 — not retrievable | 8 URLs, all 443/HTTPS | — / S26 |
| Supervisor auth | vCenter SSO / external IDP; VCF Automation API token mentioned | Same, **plus** explicit Pinniped Supervisor + Concierge for federated auth, and a full `--api-token` CLI example | S33 / S34 |

---

## Gaps and Ambiguities

1. **vCenter session-create path is inconsistent across two 9.1 sources.** S35 (vSphere Automation API landing) shows `POST /api/cis/session`; S38 (Cis Session operation page) shows `POST /session` and `DELETE /session`. Both are 9.1. The header is unambiguous (`vmware-api-session-id`); the path is not. **Resolve before writing client code.**
2. **SDDC Manager 9.1 token paths not directly verified.** S41 (9.1 reference) lists the three operations by name only; the concrete paths/schemas come from S42 (9.0) and S43 (VCF API 5.2.4). Carry-over is presumed.
3. **NSX 9.1 auth not verified.** The 9.1 `advanced-network-management/authentication-and-authorization` page returned HTTP 429 on every attempt. The session-cookie flow is verified for 9.0 only (S31). Do not assume `j_username`/`j_password` + `x-xsrf-token` is unchanged in 9.1.
4. **VCF Automation VM Apps: response token field name and exact Authorization header format are not stated in the docs.** S15 says only "The response returns the access token"; S14 says "an HTTP authentication token in the `Authorization` request header". OAuth2 convention suggests `access_token` / `Bearer`, but **that is not documented** — verify empirically.
5. **VCF Automation All Apps / Provider token endpoint URL is undocumented** in the fetched reference (S46). Only the header schemes are stated. The techdocs page "Generating an All Apps Access Token" (surfaced in search results at `.../about-the-vcf-automation-api/generating-an-access-token.html`) returned **404 on three attempts** with and without query-string variation.
6. **VCF Operations Fleet Management API auth rests on a KB article, not product docs** (S47), is Basic-auth only, and covers 9.0. No 9.1 equivalent found. Also note the KB itself says paths, payloads and token lifetime are not documented.
7. **Ports matrix is unobtainable from documentation.** ports.broadcom.com is a client-rendered tool (S64) and both Planning and Preparation pages defer to it (S28, S29). Only outbound 443 destinations (S26) and DNS/FQDN requirements (S27) are documented text.
8. **VCF SSO architecture internals undocumented in fetched pages** — no token flow, no trust-establishment mechanism, no broker ports (S65, S66 are stubs).
9. **VCF role scope hierarchy (global vs org vs instance) not stated** on the 9.1 built-in roles page (S20), despite the API-client creation flow requiring a "scope" selection (S11).
10. **IAM setting defaults not published** — S52 gives maxima only. The 30-day / 30-minute defaults come from the token-generation dialog description (S11), which may be UI defaults rather than system settings.
11. **Supervisor namespace role names (owner/edit/view) not confirmed** in the fetched 9.0/9.1 concept pages (S33, S34).
12. **9.0 public URLs page 404s** — cannot confirm the 9.0 outbound allow-list matches 9.1's.
13. **vSAN has no independent auth documentation.** S68 states dependency on the vSphere Web Services API for login; the session-reuse mechanism is corroborated only by a Broadcom blog (S58), not product docs.
14. **`vmware-identity-broker` API reference is titled "VMware Identity Broker - vCenter Server"** (S39, S40) and is version-tagged 9.1. Whether the identical `/acs/t/{tenant}/token` endpoint exists and behaves the same in 9.0 is **unverified** — the 9.0 doc set has no API-token feature (S53), which suggests it may not be exposed for customer use in 9.0.
15. **Certificate trust-store location for imported CAs is unstated** (S57).
16. **9.1 security-and-compliance section not fetched.** Only the 9.0 section was retrieved (S55: Monitoring Security Operations, Viewing and Configuring Compliance, Viewing and Configuring Audit Events); it contains no certificate/TLS/identity content.

---

## Source Inventory

All accessed **2026-07-31**.

| ID | URL | Doc set / version | Covers |
|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | VCF 9.0 | Section index |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | Section index |
| S3 | .../9-0/administration-sdks-cli-and-tools.html | VCF 9.0 | SDK/API index |
| S4 | .../9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | SDK/API index |
| S5 | .../9-0/organization-management.html | VCF 9.0 | Org mgmt, IdP overview |
| S6 | .../9-1/organization-management.html | VCF 9.1 | Org mgmt, IdP overview |
| S7 | .../9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide.html | VCF 9.0 | Programming guide index |
| S8 | .../9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide.html | VCF 9.1 | Programming guide index |
| S9 | .../9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api.html | VCF 9.0 | VCF Ops API overview, HTTPS |
| S10 | .../9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api.html | VCF 9.0 | VCF Automation API index |
| S11 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/managing-api-tokens.html | VCF 9.1 | **API client + API token creation, TTL defaults** |
| S12 | .../9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html | VCF 9.0 | **VCF Ops token acquire, OpsToken header, 6 h** |
| S13 | .../9-1/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html | VCF 9.1 | **VCF Ops token acquire (identical to 9.0)** |
| S14 | .../9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token.html | VCF 9.0 | VCF Automation VM Apps token lifetimes |
| S15 | .../9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token/get-your-access-token-for-vra-8-x.html | VCF 9.0 | **VM Apps `/tm/oauth/tenant/{t}/token`** |
| S16 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on.html | VCF 9.1 | **9.1 SSO section structure, federated components** |
| S17 | .../9-0/fleet-management.html | VCF 9.0 | Fleet Management child list |
| S18 | .../9-0/fleet-management/what-is.html | VCF 9.0 | **9.0 SSO overview, identity broker, exclusions** |
| S19 | .../9-0/fleet-management/what-is/deployment-models-for-sso.html | VCF 9.0 | Embedded vs appliance broker modes |
| S20 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/vcf-built-in-roles.html | VCF 9.1 | **VCF built-in roles + component mappings** |
| S21 | .../9-0/fleet-management/certificate-management-9-0.html | VCF 9.0 | **Cert mgmt: CA types, rotation, coverage** |
| S22 | .../9-1/fleet-management/certificate-management-9-0.html | VCF 9.1 | **Cert mgmt 9.1 incl. bulk ops, tiers** |
| S23 | .../9-0/fleet-management/what-is/protocols-suported-for--sso.html | VCF 9.0 | **IdPs + SAML/OIDC/SCIM/JIT** |
| S24 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is.html | VCF 9.1 | 9.1 SSO overview, deployment modes |
| S25 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/migrating-vmware-identity-manager-to-vcf-identity-broker.html | VCF 9.1 | **vIDM→broker migration, OAuth client caveat** |
| S26 | .../9-1/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html | VCF 9.1 | **Outbound 443 URL allow-list** |
| S27 | .../9-1/planning-and-preparation/vcf-components-fqdns-and-ip-addresses.html | VCF 9.1 | **FQDN/DNS requirements, component list** |
| S28 | .../9-0/planning-and-preparation.html | VCF 9.0 | Points to ports.broadcom.com |
| S29 | .../9-1/planning-and-preparation.html | VCF 9.1 | Points to ports.broadcom.com |
| S30 | .../9-0/advanced-network-management/administration-guide/authentication-and-authorization.html | VCF 9.0 (NSX) | NSX auth page index, broker integration |
| S31 | .../9-0/advanced-network-management/administration-guide/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html | VCF 9.0 (NSX) | **NSX session create/destroy, JSESSIONID + x-xsrf-token, 1800 s** |
| S32 | .../9-0/advanced-network-management/administration-guide/authentication-and-authorization/role-based-access-control.html | VCF 9.0 (NSX) | **15 NSX built-in roles** |
| S33 | .../9-0/vsphere-supervisor-installation-and-configuration/vsphere-supervisor-concepts/vsphere-iaas-control-plane-concepts/understanding-authorization-in-supervisor.html | VCF 9.0 | Supervisor auth/authz, `vcf context create` |
| S34 | .../9-1/vsphere-supervisor-installation-and-configuration/vsphere-supervisor-concepts/vsphere-iaas-control-plane-concepts/understanding-authorization-in-supervisor.html | VCF 9.1 | **Supervisor auth incl. Pinniped, `--api-token`, `--ca-certificate`** |
| S35 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/ | vSphere Automation API 9.1 | Session id header, `POST /api/cis/session` |
| S36 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/api-security-schema/ | vSphere Automation API 9.1 | **basic / `vmware-api-session-id` / bearer** |
| S37 | https://developer.broadcom.com/xapis/vsphere-automation-api/9.0/api-security-schema/ | vSphere Automation API 9.0 | **Same three schemes, 9.0** |
| S38 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/cis-session/ | vSphere Automation API 9.1 | `POST /session`, `DELETE /session`, SAML exchange |
| S39 | https://developer.broadcom.com/xapis/vmware-identity-broker/latest/ | VMware Identity Broker 9.1 | Broker as "centralized authentication source for the VCF components" |
| S40 | https://developer.broadcom.com/xapis/vmware-identity-broker/latest/acs/t/tenant/token/post/ | VMware Identity Broker 9.1 | **`POST /acs/t/{tenant}/token`, grant types, `api_token`, `access_token`** |
| S41 | https://developer.broadcom.com/xapis/sddc-manager-api/latest/tokens/ | SDDC Manager API 9.1 | Three token operations by name |
| S42 | https://developer.broadcom.com/xapis/sddc-manager-api/9.0/tokens/ | SDDC Manager API 9.0 | **`/v1/tokens` create/refresh/revoke, payloads, `accessToken`** |
| S43 | https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/tokens/ | VMware Cloud Foundation API 5.2.4 | Corroborates paths + `Authorization: Bearer`. **Pre-9.x — corroboration only** |
| S44 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/ | VCF Operations API 9.1 | **`OpsToken` and `Bearer` (VCF SSO) schemes, 401 behaviour** |
| S45 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/auth/ | VCF Operations API 9.1 | **Full `/auth/*` surface incl. token acquire/release/exchange, roles, privileges** |
| S46 | https://developer.broadcom.com/xapis/all-apps-org-access-control/latest/ (resolves to Provider Management API) | VCF Automation 9.1 | **JWT via `Authorization`; `x-vcloud-authorization` deprecated; tenant-context headers** |
| S47 | https://knowledge.broadcom.com/external/article/409715/how-to-authorize-vcf-operations-fleet-ma.html | Broadcom KB, VCF 9.0 | **Fleet Management API = HTTP Basic, base64 `admin@local:<pwd>`** |
| S48 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | VCF 9.1 | **9.1 API/SDK/PowerCLI deltas, VGFA, token params** |
| S49 | .../9-0/provider-management.html | VCF 9.0 | Provider portal, IdP integration levels |
| S50 | .../9-1/provider-management/managing-system-administrators-and-roles/managing-rights-and-roles.html | VCF 9.1 | **Rights/roles/bundles, provider vs global vs org roles** |
| S51 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens.html | VCF 9.1 | API client purpose, emergency access client |
| S52 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/view-and-manage-token-lifecycle-and-security.html | VCF 9.1 | **IAM maxima: 180 d / 480 min / 90 d, JIT inactivity** |
| S53 | .../9-0/fleet-management/what-is/managing-vmware-cloud-foundation-operations-sso.html | VCF 9.0 | **Negative evidence: no API client/token/role pages in 9.0** |
| S54 | .../9-0/fleet-management/what-is/setting-up-sso.html | VCF 9.0 | 7-step SSO configuration order |
| S55 | .../9-0/security-and-compliance.html | VCF 9.0 | Section contents (no cert/TLS/identity content) |
| S56 | .../9-1/design/design-library/single-sign-on-models.html | VCF 9.1 | **Three SSO topology models; split-SSO unsupported** |
| S57 | .../9-1/fleet-management/certificate-management-9-0/managing-certificates-in-vmware-vsphere-foundation/certificates/importing-ca-certificates.html | VCF 9.1 | **Trusted Certificates import, PEM-only, affected domains** |
| S58 | https://blogs.vmware.com/cloud-foundation/2025/11/19/unified-authentication-in-vmware-cloud-foundation-sdk-9-0-seamless-authentication-across-vsphere-and-vsan-apis/ | Broadcom/VMware blog, 2025-11-19, VCF SDK 9.0 | **Session reuse `/vim25` ↔ `/api` via `vmware-api-session-id`** |
| S59 | .../9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms.html | VCF 9.1 | **Basic vs token auth, JWT→SAML→session workflow, federation IdPs** |
| S60 | .../9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis.html | VCF 9.0 | Auth mechanisms pointer, SSO/external IdP statement |
| S61 | .../9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis.html | VCF 9.1 | Same, 9.1 |
| S62 | .../9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/categories-of-vcf-automation-hard-tenancy-apis.html | VCF 9.0 | **10 All Apps API categories (Access Control, Aggregator, …)** |
| S63 | .../9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-a-tkg-service-cluster-as-a-vcenter-single-sign-on-user-with-kubectl.html | VCF 9.0 | VKS connect prerequisites, kubeconfig |
| S64 | https://ports.broadcom.com/ | Broadcom tool (undated) | Ports portal description; **no static data extractable** |
| S65 | .../9-0/fleet-management/what-is/sso-architecture.html | VCF 9.0 | Stub — defers to design library |
| S66 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is/sso-architecture.html | VCF 9.1 | Stub — defers to design library |
| S67 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter-authentication/vcenter-authentication-token/ | vSphere Automation API 9.1 | `POST /vcenter/authentication/token`, added 7.0.2.0 |
| S68 | .../9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/using-the-vsan-management-sdks.html | VCF 9.0 | **vSAN depends on vSphere Web Services API for login** |

### Retrieval failures (recorded for completeness)
| URL | Result |
|---|---|
| .../9-0/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html | 404 |
| .../9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/generating-an-access-token.html | 404 (3 attempts) |
| .../9-1/advanced-network-management/authentication-and-authorization.html | HTTP 429 (repeated) |
| .../9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms.html | HTTP 429 (repeated) |
| .../9-1/.../managing-api-clients-and-tokens/... considerations-and-prerequisites-for-vcf-sso.html | 404 |
| .../9-0/fleet-management/what-is/points-to-consider-and-prerequisites-while-configuring-vcf-sso.html | 404 |
| .../9-0/design/design-library/single-sign-on-models/-fleet.html | 404 |
| .../9-0/deployment/.../installing-vcf-identity-broker.html | HTTP 403 |
| developer.broadcom.com/xapis/vmware-cloud-foundation-fleet-management-api/latest/ | 404 (API does not exist under that slug) |
| developer.broadcom.com/xapis/sddc-manager-api/latest/tokens/post-v1-tokens/ | Page rendered without operation detail |
| developer.broadcom.com/xapis/vcf-operations-api/latest/auth/token/acquire/post/ | Page rendered without operation detail |
| .../9-0/.../getting-your-authentication-token/get-your-refresh-token-for-the-vm-apps-tenant.html | 404 |
