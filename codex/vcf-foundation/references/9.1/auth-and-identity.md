# VCF 9.1 — Authentication, Identity, Certificates, Reachability

**Scope: VMware Cloud Foundation 9.1 only.** Nothing on this page is asserted for 9.0. Where a fact was
verified independently in both doc sets the tag `[9.0+9.1]` appears inline and says so explicitly. Facts the
research could not retrieve are marked `UNVERIFIED` in place — they are not omitted and not filled in by
inference.

Two classes of evidence are used and are labelled distinctly:

- **Prose evidence** — Broadcom TechDocs / developer-portal pages, cited `[FA-Sxx]`, `[TL-Sxx]`, `[C91-Sxx]`,
  `[VS-Sxx]` and resolved to full URLs in `## Source Index`.
- **Spec evidence** — machine-extracted `securitySchemes` and operation lists from the OpenAPI specs at git tag
  `9.1.0.0` of `github.com/vmware/vcf-api-specs`, cited `[SPEC-9.1]`. Spec evidence outranks prose where the two
  disagree; every disagreement is called out at `## Spec-vs-prose conflicts`.

---

## Contents

- [Prerequisites](#prerequisites) — P0 bootstrap admin credential · P1 version pinning · P2 SSO API tokens
  exist · P3 API client + token · P4 TTL ceilings and the JIT trap · P5 OAuth clients after vIDM migration ·
  P6 SSO exclusions · P7 one identity broker per instance (**source of `{ssoRealmId}`**) · P8 VCF built-in
  roles · P9 TLS trust · P10 DNS/FQDN · P11 reachability (**inbound ports UNVERIFIED**) · P12 PowerCLI 9.1 ·
  P13 vCenter federation state
- [1. Per-product authentication](#1-per-product-authentication-91) — 1.1 Identity Broker · 1.2 SDDC Manager ·
  1.3 vCenter / vSphere Automation · 1.4 VI JSON · 1.5 NSX · 1.6 VCF Operations · 1.7 Log Management ·
  1.8 Operations for Networks · 1.9 Realtime Metrics · 1.10 Fleet LCM · 1.11 SDDC LCM · 1.12 VCF Automation ·
  1.13 vSAN DP · 1.14 VCF Installer · 1.15 Supervisor / VKS
- [2. Token lifetimes and refresh](#2-token-lifetimes-and-refresh-91)
- [3. Identity / SSO architecture](#3-identity--sso-architecture-91)
- [4. Roles and permissions](#4-roles-and-permissions-91)
- [5. The 9.1 IAM API surface (spec-confirmed)](#5-the-91-iam-api-surface-spec-confirmed-spec-91)
- [6. Certificate handling and TLS-trust pitfalls](#6-certificate-handling-and-tls-trust-pitfalls-91)
- [7. Network reachability](#7-network-reachability-91)
- [8. Spec-vs-prose conflicts and how they were resolved](#8-spec-vs-prose-conflicts-and-how-they-were-resolved)
- [9. Consolidated `UNVERIFIED` list for 9.1](#9-consolidated-unverified-list-for-91)
- [Source Index](#source-index)

---

## Prerequisites

Read this whole block before issuing any request. Each item states **(a)** what must be true, **(b)** how to
verify it is satisfied, **(c)** the version it applies to, **(d)** whether it exists in the other version.

> **Ordering note — these are not strictly sequential.** P3, P4 and P5 all reference an `{ssoRealmId}` path
> parameter. That value is **not** available until P7, which is where the realm is enumerated
> (`GET /suite-api/api/fleet-management/iam/ssorealms` `[SPEC-9.1]`). Satisfy **P0 → P1 → P2 → P7** first to
> obtain a console login and an `{ssoRealmId}`, then return to P3–P5. The numbering follows importance, not
> execution order.

### P0 — A VCF Operations administrator credential exists to bootstrap from

(a) Every 9.1 flow in P2–P5 begins inside the VCF Operations console at *Manage → Fleet Management →
Identity & Access* `[FA-S11]`. Reaching that node requires an **already-working** interactive login holding the
VCF Operations **Administrator** role — the bootstrap credential established at deployment. **You cannot create
the first API client with an API client.** If no such credential is in hand, stop here: none of P3–P5 is
reachable.
(b) Sign in to the VCF Operations console and confirm the *Fleet Management → Identity & Access* node renders.
The VCF built-in role mapping names **VCF Operations Administrator** as the component role behind **VCF
Administrator** `[FA-S20]`.
(c) 9.1.
(d) 9.0 has the console but no *Identity & Access → API Access* node (P2) `[FA-S53]`. For the separate 9.0
Fleet Management **API**, Broadcom KB 409715 documents an appliance-local `admin@local` credential
`[FA-S47]`.
> *This prerequisite is an operational consequence of the documented UI path `[FA-S11]`; no fetched Broadcom
> page names a specific bootstrap account for the 9.1 Identity & Access UI. Treat the account name as
> deployment-specific.*

### P1 — The target version is confirmed to be 9.1 before any auth flow is chosen

(a) The auth surface differs materially between 9.0 and 9.1. Choosing a flow before pinning the version
produces endpoints that do not exist on the other release.
(b) Verify from the deployed BOM: VCF 9.1.0.0 released **12 MAY 2026**; all 9.1 core components are version
9.1.0.0 (VCF Installer/SDDC Manager build 25371088, ESX 25370933, vCenter 25370922, NSX 25318225) `[C91-S2]`
`[C91-S8]`. VCF 9.0.0.0 was 17 JUN 2025, build 24755599 `[C91-S11]`.
(c) 9.1.
(d) The same discipline applies in 9.0; the 9.0 file is the counterpart.

### P2 — SSO-issued, role-scoped API tokens EXIST in 9.1 — and have no 9.0 equivalent

**This is the loudest version-scoped prerequisite on this page.**

(a) VCF 9.1 provides **API clients, SSO-issued role-scoped API tokens, OAuth apps, emergency access clients**
and fleet-level **IAM TTL ceilings**. A non-interactive, role-scoped API token issued by VCF SSO is a **9.1
capability** `[FA-S51]` `[FA-S11]` `[FA-S52]`.
(b) Two independent verifications:
  - **UI check:** *VCF Operations → Manage → Fleet Management → Identity & Access → VCF SSO Overview → select
    identity broker → API Access → API Clients* `[FA-S11]`. If the *API Access* node is absent, you are not on
    9.1.
  - **Spec check (strongest):** the `vcf-operations` spec at tag `9.1.0.0` contains **70 operations** under
    `/api/fleet-management/iam/**` (base `/suite-api`); the `9.0.0.0` spec contains **0** `[SPEC-9.1]`. See §5
    for the endpoint list.
(c) 9.1.
(d) **DOES NOT EXIST IN 9.0.** The 9.0 SSO doc tree has no API client, API token, OAuth client or role
management page `[FA-S53]`, and the 9.0 spec has no `iam/**` routes `[SPEC-9.1]`. Never present this flow to a
9.0 user.

### P3 — An API client exists, is role-scoped, and its API token is captured at creation

(a) Before requesting an access token you need an API client with a **scope** and a **role**, plus a generated
API token. The API token value **cannot be retrieved after clicking Continue** — capture it at generation time
`[FA-S11]`.
(b) Verify via UI (*Create API Client* → name, optional description → **Create API Client**; then **Roles**:
select scope, choose role, enter validity period → Save) `[FA-S11]`, or via API:
`GET /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients/{clientId}` and
`GET .../api-tokens/{apiTokenId}` `[SPEC-9.1]`.
→ **`{ssoRealmId}` comes from P7**: `GET /suite-api/api/fleet-management/iam/ssorealms` `[SPEC-9.1]`. Satisfy
P0/P7 before attempting this item.
(c) 9.1.
(d) No 9.0 equivalent (P2).

### P4 — Token TTLs are inside the IAM ceilings, and the JIT-inactivity trap is handled

(a) Generated tokens must fit the configured ceilings, and the client must survive a **silent token-death mode**.
  - *API Token TTL* — **default 30 days**, bounded by Fleet Settings → IAM Setting; maximum **180 days**
    `[FA-S11]` `[FA-S52]`.
  - *Access Token TTL* — **default 30 minutes**, bounded by IAM Settings; maximum **480 minutes** `[FA-S11]`
    `[FA-S52]`.
  - *Expired API Token Retention Period* — maximum **90 days** `[FA-S52]`.
  - **JIT User Inactivity Period** — once a JIT user is inactive, *"previously issued API tokens cannot retrieve
    access tokens until the user authenticates again"* `[FA-S52]`. A working token stops working with no
    revocation event. **Automation that runs on a JIT-provisioned identity will die silently.**
(b) Verify with `GET /suite-api/api/fleet-management/iam/settings` ("Get IAM Global Settings"); change with
`PUT .../iam/settings` `[SPEC-9.1]`. Cross-check the token's own record via
`GET .../ssorealms/{ssoRealmId}/api-tokens/{apiTokenId}` `[SPEC-9.1]`.
→ **`{ssoRealmId}` comes from P7** (`GET .../iam/ssorealms`). Note that `GET|PUT .../iam/settings` is
realm-independent and can be called before P7.
(c) 9.1.
(d) **No 9.0 equivalent.** There are no fleet-level token TTL controls and no JIT-inactivity behaviour in 9.0
`[FA-S53]`.
> Diagnostic: automation that "randomly stops working after a few weeks" on 9.1 is most often (i) the 30-day
> default API Token TTL expiring, or (ii) JIT user inactivity. Check both before regenerating credentials.
`UNVERIFIED — defaults`: the IAM settings page publishes **maxima only**; the 30-day / 30-minute figures come
from the token-generation dialog description and may be UI defaults rather than system settings `[FA-S52]`
`[FA-gap10]`.

### P5 — Pre-existing OAuth clients were manually regenerated after a vIDM migration

(a) On the **vIDM → VCF Identity Broker** migration, verbatim: *"OAuth clients are not migrated automatically.
You must manually regenerate the client and secret using identity broker and configure accordingly."*
`[FA-S25]`. Any 9.0-era OAuth client **breaks on upgrade**.
(b) Verify the client exists in the broker:
`GET /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps` `[SPEC-9.1]`. Rotate the secret with
`POST .../oauth-apps/{oauthAppId}/rotate` `[SPEC-9.1]`.
→ **`{ssoRealmId}` comes from P7** (`GET .../iam/ssorealms`).
Also migrated/not-migrated, verbatim `[FA-S25]`: *"Users and groups are migrated from VMware Identity Manager to
identity broker."*; *"Local accounts and local accounts with multifactor authentication are not supported."*;
*"Multifactor authentication with Active Directory is not supported."* Sync settings are compared but **not**
migrated and must be adjusted manually. If VCF Operations, VCF Automation or NSX use the legacy system, the
migration script repoints them.
(c) 9.1.
(d) The migration workflow is 9.1-only; there is no such page in the 9.0 doc set `[FA-S53]`.

### P6 — SDDC Manager and ESX are excluded from VCF SSO

(a) SDDC Manager authentication is **not** SSO-brokered even in 9.1. It uses its own `/v1/tokens` flow (§1.2).
ESX is likewise excluded.
(b) The 9.1 SSO overview lists the federated components — vCenter, VCF Operations, VCF Automation, log
management (VCF Operations for Logs), VCF Operations for Networks, VCF Operations orchestrator, VCF Operations
HCX, NSX — and explicitly excludes SDDC Manager and ESX `[FA-S24]`.
(c) 9.1.
(d) `[9.0+9.1]` — verified independently in the 9.0 doc set with the identical component list and identical
exclusions `[FA-S18]`. Do not assume a fleet-wide SSO token authenticates SDDC Manager.

### P7 — All workload-domain components in one VCF instance use the same identity broker

(a) *"split-SSO configurations … are not supported"* `[FA-S56]`. All workload-domain components in a single VCF
instance must connect to the same identity broker. Fleet-management components may connect to any broker;
same-instance is recommended `[FA-S56]`.
(b) Verify with `GET /suite-api/api/fleet-management/iam/ssorealms` and
`GET /suite-api/api/fleet-management/iam/vidbs` ("Get eligible identity broker instances for IDP
configuration") `[SPEC-9.1]`.
(c) 9.1. The three topology models — **VCF Fleet-Wide SSO**, **Cross VCF Instance SSO**, **Single VCF Instance
SSO** — are formalised in the 9.1 design library `[FA-S56]`.
(d) **Not formalised in 9.0.** No equivalent 9.0 design-library page was retrievable (404) `[FA-retrieval-failures]`.

### P8 — VCF built-in roles are documented only in the 9.1 doc set

(a) **VCF Administrator, VCF Viewer, SDDC Administrator, SDDC Viewer** with per-component mappings are 9.1
documentation. *"VCF roles are mapped to the individual VCF component roles"*; *"built-in VCF roles cannot be
modified."* `[FA-S20]`
(b) Verify with `GET /suite-api/api/fleet-management/iam/roles` ("Get Paginated List of VCF Roles") and
`GET .../iam/roles/{name}` `[SPEC-9.1]`.
(c) 9.1.
(d) **No equivalent page exists in the 9.0 fleet-management tree** `[FA-S53]`. Do not use these role names when
answering for 9.0.

### P9 — The client trusts the VCF certificate chain, including the identity broker's

(a) At deployment components receive certificates from the default **VMware Certificate Authority (VMCA)**;
Broadcom's documented guidance is to replace them with trusted enterprise CA-signed certificates `[FA-S22]`. A
stock HTTP client fails chain/hostname validation until the VMCA root or the enterprise CA is trusted.
(b) Perform a TLS handshake with verification **enabled** and inspect the issuer. Enumerate managed certificates
with `GET /suite-api/api/fleet-management/certificate-management/certificate-authorities` and
`POST .../certificate-management/certificates/query` `[SPEC-9.1]`.
(c) 9.1.
(d) `[9.0+9.1]` — the same default-VMCA state and the same replace-don't-disable guidance are verified
independently in 9.0 `[FA-S21]`.
**9.1-specific escalation:** the **identity broker itself holds a certificate** in the 9.1 *VCF Management*
coverage tier `[FA-S22]`. Because the broker is the token issuer, a stale or untrusted broker certificate breaks
**every SSO-based API client at once** — a single TLS point of failure that 9.0's per-product auth did not have.
*Inference from the 9.1 coverage list; the docs do not state the blast radius.*

### P10 — DNS resolves every component FQDN, and the client connects by FQDN

(a) *"VCF requires unique FQDNs and static IP addresses for VCF components and proper DNS resolution for each
FQDN and IP address is required."* *"FQDNs must point to unique IP addresses that are not assigned and the FQDNs
must not be in the IP Ranges assigned to VCF management services nodes."* `[FA-S27]`
(b) Verify forward and reverse resolution for every component FQDN, including the **identity broker** — it is
named explicitly in the FQDN/IP requirement list for both the first and additional VCF instances `[FA-S27]`.
(c) 9.1.
(d) The equivalent 9.0 statement was not separately retrieved; treat it as verified-9.1 text only.
→ **API clients must resolve the same FQDNs the certificates are issued to; IP-address connections fail
hostname verification.** *Inference from the FQDN/cert facts.*

### P11 — Reachability: outbound HTTPS/443 allow-list is open, and the inbound side is NOT covered here

(a) **Outbound:** eight destinations, all HTTPS/443 `[FA-S26]`. See §7.
**Inbound: `UNVERIFIED — could not retrieve`. This prerequisite list is NOT complete on the inbound side.**
The per-service *inbound* port matrix could not be retrieved: both the 9.0 and 9.1 Planning and Preparation
pages defer to the VMware Ports and Protocols tool at `https://ports.broadcom.com/`, which renders client-side
and exposes no static table; VCF 9.0/9.1 coverage could not be confirmed `[FA-S28]` `[FA-S29]` `[FA-S64]`.
Inbound ports for vCenter, NSX, SDDC Manager, VCF Operations, the identity broker and Supervisor are therefore
**not listed below and not listed in §7**. Do not sign this prerequisite off as complete, and do not invent a
port table — direct the user to `https://ports.broadcom.com/`.
(b) Verify TCP/443 egress to each FQDN in that table. For inbound, establish the matrix out-of-band before
treating reachability as satisfied.
(c) 9.1.
(d) The equivalent 9.0 outbound page returned **404** — `UNVERIFIED — 9.0 public URL list`
`[FA-retrieval-failures]`. Do not back-port this list into a 9.0 answer. The inbound gap is identical in 9.0
(see the 9.0 file, P10d).

### P12 — PowerCLI 9.1 is installed if token auth via PowerShell is intended

(a) `VcfOAuthSecurityContext` and `VcfApiToken` parameters exist only in `{PCLI 9.1.0}` `[TL-S08]`.
(b) `Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version` — the 9.1-aligned module is
`VCF.PowerCLI 9.1.0.25380678`, published 2026-05-12 `[TL-S06]` `[TL-S07]`.
(c) 9.1.
(d) **Not present in `{PCLI 9.0.0}`** `[TL-S05]`. See `../powercli-session.md`, including the caveat that the
specific cmdlets exposing these parameters were **not verified**.

### P13 — vCenter federation state is known

(a) The 9.0 release notes state: *"Blocked non-federated username/password logins to vCenter: vCenter 9.0 blocks
logins with just a user name and password, which might sometimes allow bypassing the federated provider
domain."* `[VS-S5]`
(b) Determine whether the vCenter is federated with an external IdP; if it is, use the documented federated
flow (§1.3).
(c) **This statement is a 9.0 release-note item.** Its status in 9.1 is **`UNVERIFIED`** — no 9.1 page
re-stating, extending or relaxing it was retrieved. Do not assert it as verified 9.1 behaviour, and do not
assert it was reverted.
(d) Verified for 9.0 `[VS-S5]` — see the 9.0 file, P4.

---

## 1. Per-product authentication `[9.1]`

Base-path warning: the machine-extracted `servers[0].url` for the SDDC Manager and VCF Installer specs is the
placeholder `http://localhost:80`, and for Fleet LCM / SDDC LCM it is `https://vcf.broadcom.com/fleet-lcm` /
`https://vcf.broadcom.com/sddc-lcm` `[SPEC-9.1]`. These are spec artifacts, **not** callable bases. Substitute
the deployed component FQDN.

### 1.1 VCF Identity Broker — the 9.1 token endpoint

| Field | Value |
|---|---|
| Method + path | `POST https://{api_host}/acs/t/{tenant}/token` `[FA-S40]` |
| Content type | `application/x-www-form-urlencoded`; HTTP Basic auth is also supported on the endpoint `[FA-S40]` |
| Required body field | `grant_type` — one of `authorization_code`, `password`, `client_credentials`, `refresh_token`, or an extended grant `[FA-S40]` |
| Optional body fields | `client_id`, `client_secret`, `refresh_token`, **`api_token`**, `code`, `username`, `password`, `scope`, `redirect_uri`, `domain`, `assertion`, `code_verifier` `[FA-S40]` |
| Response fields | `access_token`; also `token_type` (= `"Bearer"`), `expires_in` (seconds), `refresh_token`, `id_token`, `scope` `[FA-S40]` |
| Subsequent header | `Authorization: Bearer <access_token>` `[FA-S40]` |
| Role | *"centralized authentication source for the VCF components"* `[FA-S39]` |

**Documented four-step exchange flow** (verbatim) `[C91-S19]`:
1. *"Administrator creates API clients with credentials that are recorded in VIDB."*
2. *"Administrator requests a long-lived API refresh token from the VCF Operations UI."*
3. *"Automation script passes the API refresh token to VIDB and gets a bearer access token in return."*
4. *"Automation script uses the bearer access token to authenticate with VCF components."*

Caveat from the same page: *"not all VCF components employ identical token authentication methods, but many of
them start with VCF Operations and VCF Identity Broker (VIDB)."* `[C91-S19]` Corroborating: *"VMware provides
unified API and CLI access across most VCF components with OAuth standards-based token authentication, based on
VCF Identity Broker (VIDB)."* `[C91-S20]`

Broker discovery endpoint: `GET /suite-api/api/auth/sources/vidb/well-known-url` ("Get VIDB well-known URL") —
new in 9.1 `[SPEC-9.1]`.

**9.0 status of this endpoint: `UNVERIFIED`.** The reference is version-tagged 9.1 and the 9.0 doc set has no
API-token feature `[FA-S39]` `[FA-S40]` `[FA-S53]` `[FA-gap14]`.

### 1.2 SDDC Manager — `POST /v1/tokens` (not SSO-brokered)

| Field | Value |
|---|---|
| Method + path | `POST /v1/tokens` — "Create Token Pair" `[SPEC-9.1]` |
| Refresh | `PATCH /v1/tokens/access-token/refresh` — "Refresh Access Token" `[SPEC-9.1]` |
| Revoke | `DELETE /v1/tokens/refresh-token` — "Invalidate Refresh Token" `[SPEC-9.1]` |
| Payload (create) | JSON: `{"username":"string","password":"string"}` — **carried from the 9.0 reference** `[FA-S42]` |
| Token field | `accessToken` (JWT); refresh handle at `refreshToken.id` (UUID) — **carried from the 9.0 reference** `[FA-S42]` |
| Subsequent header | `Authorization: Bearer <accessToken>` — **carried from the 9.0 reference** `[FA-S42]` `[FA-S43]` |
| Refresh body semantics | plain-text refresh-token UUID; response body **is** the raw JWT — **carried from the 9.0 reference** `[FA-S42]` |

**Path verification status has improved over the prose dossier.** The 9.1 API reference index lists the three
operations by name only, so the dossier marked the 9.1 paths *presumed* `[FA-S41]` `[FA-gap2]`. The spec resolves
it: all three paths and summaries are present verbatim at tag `9.1.0.0`, unchanged from `9.0.0.0`, and none of
them appears in the 9.1 added / removed / newly-deprecated lists `[SPEC-9.1]`. **Paths are confirmed for 9.1.**

**Payload shapes and the Bearer header remain prose-carried from the 9.0 reference** — the SDDC Manager spec
declares **no `securitySchemes`** (`{}`) and no per-operation `security` block in either version `[SPEC-9.1]`.

The SDDC Manager API surface **grew** in 9.1: 375 → **423** operations, 48 added, 0 removed, 21 newly deprecated
(edge-cluster reads, DNS/NTP configuration reads) `[SPEC-9.1]`. Its OpenAPI spec still ships in the 9.1 bundle
`[C91-S16]`, and the SDDC Manager **UI** — not the API — is what is deprecated `[C91-S15]`.

Not SSO-brokered — see P6.

### 1.3 vCenter / vSphere Automation REST API

| Field | Value |
|---|---|
| Base path | `https://{host}/api` (spec `servers[0].url`) `[SPEC-9.1]`; port 443, with an appliance-configuration subset on port 5480; deprecated `/rest` base path still present `[VS-S18]` |
| Declared security schemes (spec) | `basic_auth` (HTTP `basic`); `api_key_auth` (apiKey, header **`vmware-api-session-id`**); `federated_identity_auth` (HTTP `bearer`, described as: *"If your vCenter Server is federated with an external identity provider, please see: VMware Identity Broker - vCenter Server Workflows"*) `[SPEC-9.1]` — identical to the 9.1 security-schema page `[FA-S36]` |
| Session flow | Create a session with Basic credentials, then reuse the returned session id `[FA-S36]` |
| Token field | session id string, e.g. `b00db39f948d13ea1e59b4d6fce56389` `[FA-S36]` |
| Subsequent header | `vmware-api-session-id: <session-id>` `[FA-S36]` `[VS-S10]` |
| Federated flow | JWT from external IdP → exchange for a vCenter SSO SAML token → exchange for a session identifier `[VS-S9]` |
| Supported IdPs | vCenter SSO (default), AD FS (7.0+), Okta (8.0 U1+), Azure AD (8.0 U2+) `[VS-S9]` |
| Basic auth posture | described but *"VMware discourages"* it in favour of token-based flows `[VS-S9]` |

`[9.0+9.1]` — the three security schemes are verified independently in the 9.0 `[FA-S37]` and 9.1 `[FA-S36]`
security-schema pages and in both spec tags `[SPEC-9.1]`.

**Session path — spec-confirmed: `POST /api/session`.** `GET|POST|DELETE /session` are present as operations
with operationIds `Cis.Session_get` / `Cis.Session_create` / `Cis.Session_delete` in the `vsphere-automation`
spec at tag `9.1.0.0` — and identically at `9.0.0.0`, so **this is not a version delta** `[SPEC-9.1]`. With
`servers[0].url` = `https://{host}/api`, the callable paths are `POST /api/session` (create),
`GET /api/session` (inspect), `DELETE /api/session` (invalidate). The string `/api/cis/session` appears
**nowhere** in either spec.

Some Broadcom prose pages nonetheless print `/api/cis/session` `[FA-S35]` `[VS-S10]`, while the `cis-session`
reference page prints `/session` `[FA-S38]`. That is a **prose-vs-spec conflict, resolved in favour of the
spec** — see `## Spec-vs-prose conflicts`, item 5. The observation is recorded rather than deleted: if a
deployment rejects `/api/session`, the prose variant is the fallback to test `[FA-gap1]`. The header
(`vmware-api-session-id`) was never ambiguous.

`POST /vcenter/authentication/token` ("issue"; added in vSphere API 7.0.2.0) is documented on the developer
portal, but its **request parameters and response fields were not rendered** on the fetched page and the
operation does not appear in the extracted spec — `UNVERIFIED` `[FA-S67]` `[SPEC-9.1]`.

**vCenter Group Federated API (VGFA)** — new in 9.1, *"a single unified API endpoint for managing all vCenter
instances in a vCenter group"*, activatable from the VCF Operations UI **after** SSO configuration `[FA-S48]`
`[C91-S6]`.

### 1.4 Virtual Infrastructure JSON API (`/sdk/vim25`)

| Field | Value |
|---|---|
| Base path | `https://{vcenter-host}/sdk/vim25/{release}` `[SPEC-9.1]` |
| Declared security scheme (spec) | `Session` — apiKey in header **`vmware-api-session-id`**, described as *"A session token, placed in the `vmware-api-session-id` HTTP header, returned by the `Login` operation of the `SessionManager` interface."* `[SPEC-9.1]` |
| Surface | 2243 operations at 9.1 (2195 at 9.0, +48) `[SPEC-9.1]` |

### 1.5 NSX Manager / NSX Policy / NSX Global Policy

**NSX session authentication is verified for 9.1** `[9.0+9.1]`.

| Field | Value |
|---|---|
| Method + path | `POST /api/session/create` — **spec-confirmed** as operationId `CreateAuthenticatedSession` in **all three** 9.1 NSX spec inventories (`9.1__nsx-policy`, `9.1__nsx-manager`, `9.1__nsx-global-policy`) `[SPEC-9.1]`; documented in prose at `[NSX-S12]` `[NSX-S18]` |
| Payload | `application/x-www-form-urlencoded`: `j_username=<user>&j_password=<pass>` `[NSX-S12]` `[NSX-S18]` |
| Token fields | Session cookie **`JSESSIONID`** plus response header **`X-XSRF-TOKEN`** `[NSX-S12]` `[NSX-S18]` |
| Subsequent headers | **Both are required**: `Cookie: JSESSIONID=<id>` **and** `x-xsrf-token: <token>` `[NSX-S12]` |
| Logout | `POST /api/session/destroy` — **spec-confirmed** as `DestroyAuthenticatedSession` in all three 9.1 NSX specs `[SPEC-9.1]`; prose `[NSX-S12]` `[NSX-S18]` |
| Session timeout | default **1800 seconds (30 minutes)**, configurable via `PUT /api/v1/cluster/api-service` (`session_timeout`) `[NSX-S12]` |
| Expiry behaviour | *"NSX Manager responds with a 403 Forbidden HTTP response."* — re-authenticate on **403**, not 401 `[NSX-S12]` |

**Correction to an earlier verdict.** This flow was previously marked `UNVERIFIED` for 9.1 on the strength of
an HTTP 429 returned by the 9.1 `advanced-network-management/authentication-and-authorization` **parent index**
page `[FA-retrieval-failures]` `[FA-gap3]`. That generalised too far: a 429 is a rate-limit response and is not
evidence of absence. The **child** page was retrieved successfully `[NSX-S12]`, a second independent 9.1 source
(the NSX 9.1.0.0 API Guide) states the same `[NSX-S18]`, and the 9.1 spec inventories carry both operations
`[SPEC-9.1]`. What the 429 actually cost is the **13 non-Enterprise-Admin / non-Auditor NSX role names**, which
remain `UNVERIFIED` for 9.1 (§4).

**What the 9.1 specs also establish** `[SPEC-9.1]`:

| Spec | Base path | OpenAPI version | Declared security scheme | Operations |
|---|---|---|---|---|
| `nsx-policy` | `/policy/api/v1` | **2.0** | `BasicAuth` — *"HTTP Basic Authentication"* | 3729 |
| `nsx-manager` | `/api/v1` | **2.0** | `BasicAuth` — *"HTTP Basic Authentication"* | 1453 |
| `nsx-global-policy` | `/global-manager/api/v1` | **2.0** | `BasicAuth` — *"HTTP Basic Authentication"* | 1009 |

All three NSX specs are **new at tag `9.1.0.0`** — none exists at `9.0.0.0` `[SPEC-9.1]`. NSX specs are OpenAPI
**2.0** while every other VCF component is OpenAPI 3.0.x; generators must be told which per component
`[TL-S11]`.

Conclusion for 9.1: **both mechanisms are confirmed.** HTTP Basic is a spec-declared scheme for all three NSX
surfaces `[SPEC-9.1]`, and the session cookie + XSRF flow is confirmed by prose `[NSX-S12]` `[NSX-S18]` and by
the presence of `CreateAuthenticatedSession` / `DestroyAuthenticatedSession` in all three 9.1 spec inventories
`[SPEC-9.1]`. The NSX 9.1.0 API Guide documents the same four mechanisms as 9.0 — HTTP Basic, session-based,
X.509 client certificate (bound to a **principal identity**), and VMC token exchange (not applicable on-prem)
`[NSX-S18]`.

### 1.6 VCF Operations — `token/acquire`, Bearer, and `token/exchange`

| Field | Value |
|---|---|
| Method + path | `POST https://<host>/suite-api/api/auth/token/acquire` `[FA-S13]` `[SPEC-9.1]` |
| Payload | `{"username":"vRealize-user","password":"vRealize-dummy-password"}` `[FA-S13]` |
| Token field | `token`, format `<uuid>::<uuid>`; response also carries `expiresAt` and `validity` (ms) `[FA-S13]` |
| Subsequent header | `Authorization: OpsToken <token>`. Legacy `Authorization: vRealizeOpsToken <token>` *"continues to be supported"* `[FA-S13]` |
| **9.1 addition** | The same API also accepts `Authorization: Bearer <token>` where the token is *"an access token from VCF SSO"*. Missing / expired / invalid → **`401 Unauthorized`** `[FA-S44]` |
| Lifetime | *"expires after **six hours**"* `[FA-S13]` |
| Release | `POST /api/auth/token/release` — "Terminate the current sessionId" `[SPEC-9.1]` |
| **9.1-new operation** | `POST /api/auth/token/exchange` — "Exchange current user token with jwt token" `[SPEC-9.1]` `[FA-S45]` |

`[9.0+9.1]` — the acquire endpoint, payload, token format and six-hour lifetime are **identical text** in both
doc sets `[FA-S12]` `[FA-S13]`; verified independently.

**`token/exchange` is genuinely 9.1-only**: absent from the `9.0.0.0` spec, present at `9.1.0.0` `[SPEC-9.1]`.
The `Bearer` acceptance is likewise documented only in the 9.1 API reference `[FA-S44]`; the 9.0 page describes
only `OpsToken` / `vRealizeOpsToken` `[FA-S12]`.

Overall surface: 370 → **504** operations, 134 added, 0 removed `[SPEC-9.1]`.

### 1.7 Log Management `[9.1 only]`

| Field | Value |
|---|---|
| Spec | `specifications/vcf-operations/log-management-openapi.json`, title "Log Management API", 23 operations, spec placeholder base `http://localhost:8787` `[SPEC-9.1]` |
| Declared security scheme (spec) | `OPSTokenAuthorization` — apiKey in header **`X-JWT-Token`** `[SPEC-9.1]` |
| How to obtain the token (verbatim from the spec description) | *"This documentation covers v2 API endpoints. Authenticated requests must include an X-JWT-Token header with a token retrieved with the following authenticated call to VCF Operation API : `POST /suite-api/api/auth/token/exchange` Request body `{"serviceKeys": ["ops-li"]}`. Access is allowed only to resources that the user is authorized to use."* `[SPEC-9.1]` |

**This replaces the 9.0 `vcf-operations-for-logs` spec**, which had base `/api/v2`, 136 operations, a `Bearer`
scheme and a `POST /sessions` session-create — and is **absent at tag `9.1.0.0`** `[SPEC-9.1]`. Do not carry
`/api/v2/sessions` forward into 9.1.

Note the dependency chain: Log Management auth in 9.1 requires the VCF Operations `token/exchange` operation,
which is itself 9.1-only (§1.6).

### 1.8 VCF Operations for Networks

| Field | Value |
|---|---|
| Base path | `/api/ni` (unchanged from 9.0) `[SPEC-9.1]` |
| Declared security schemes (spec) | `ApiKeyAuth` — apiKey in header `Authorization`, `API Key - NetworkInsight {token}`; **plus, new in 9.1**, `OpsTokenAuth` — HTTP `bearer`, *"VCF Ops JWT Token - Bearer {token}"* `[SPEC-9.1]` |
| Operations | 636 (632 at 9.0; 5 added, 1 removed, 22 newly deprecated) `[SPEC-9.1]` |

The `OpsTokenAuth` bearer scheme is **9.1-new** — the 9.0 spec declares only `ApiKeyAuth` `[SPEC-9.1]`.

### 1.9 Realtime Metrics `[9.1 only]`

Spec new at tag `9.1.0.0`: 4 operations, spec placeholder base `http://localhost:8080/`, single declared scheme
`bearerAuth` (HTTP `bearer`) `[SPEC-9.1]`. No `9.0.0.0` counterpart exists. `UNVERIFIED` — no prose page
describing how to obtain this bearer token was retrieved.

### 1.10 Fleet LCM `[9.1 only]`

Spec new at tag `9.1.0.0`: 51 operations, spec placeholder base `https://vcf.broadcom.com/fleet-lcm`. Two
declared schemes `[SPEC-9.1]`:
- `basicAuth` — HTTP `basic`
- `bearerToken` — HTTP `Bearer`, *"Bearer token using a JWT"*

No `9.0.0.0` counterpart. Note: the 9.0-era **VCF Operations Fleet Management API** was HTTP-Basic-only and
documented in a **KB article**, not product docs, with `Authorization: Basic <base64 of admin@local:<pwd>>`
`[FA-S47]`; no 9.1 equivalent KB was found `[FA-gap6]`. The spec-declared `basicAuth` on Fleet LCM is consistent
with that lineage but is **not** the same API and must not be described as such.

### 1.11 SDDC LCM `[9.1 only]`

Spec new at tag `9.1.0.0`: 26 operations, spec placeholder base `https://vcf.broadcom.com/sddc-lcm`, single
declared scheme `bearerToken` (HTTP `Bearer`, *"Bearer token using a JWT"*) — **no** basic auth `[SPEC-9.1]`.

### 1.12 VCF Automation — All Apps / Provider

| Field | Value |
|---|---|
| Token endpoint URL | **`UNVERIFIED`.** Not stated in the fetched reference. The techdocs page "Generating an All Apps Access Token" returned **404 on three attempts** `[FA-S46]` `[FA-gap5]` |
| Auth scheme | **JWT via the `Authorization` header (recommended)** `[FA-S46]` |
| Deprecated | `x-vcloud-authorization` session header `[FA-S46]` |
| Context headers | `X-VMWARE-VCLOUD-TENANT-CONTEXT`, `X-VMWARE-VCLOUD-AUTH-CONTEXT` `[FA-S46]` |
| Payload / token field | `UNVERIFIED` `[FA-S46]` |

Do **not** carry the 9.0 VM Apps endpoint (`POST /tm/oauth/tenant/{tenant}/token` `[FA-S15]`) into a 9.1 All
Apps answer — that is a different tenancy model and was documented in the 9.0 doc set.

### 1.13 vSAN Data Protection

Base `https://{host}/api`, 65 operations at 9.1 (48 at 9.0, +17). Declares the same three schemes as vSphere
Automation: `basic_auth`, `api_key_auth` (header `vmware-api-session-id`), `federated_identity_auth` (bearer)
`[SPEC-9.1]`.
vSAN itself has no independent authentication — vSAN Management APIs *"depend on the vSphere Web Services API
for login procedures"* `[FA-S68]` (9.0 page; the statement was not re-verified in a 9.1 page).

### 1.14 VCF Installer

The VCF Installer OpenAPI spec at tag `9.1.0.0` declares **no `securitySchemes`** (`{}`), 57 operations (52 at
9.0, +5), spec placeholder base `http://localhost:80` `[SPEC-9.1]`. `UNVERIFIED` — no authentication method for
the VCF Installer API is established by either the spec or any fetched 9.1 prose page.

### 1.15 Supervisor / VKS

Two documented paths in 9.1.

**(a) vCenter SSO or external IdP** `[FA-S34]`:
```
vcf context create <context_name> --endpoint=<SUPERVISOR_ENDPOINT> --type=k8s --username=<user_name>
```
Documented form `[TL-S25]`:
```
vcf context create --endpoint <SUPERVISOR-ADDRESS> --username <VCENTER-SSO-USER> --ca-certificate <PATH-TO-CERTIFICATE-FILE>
```
Password is entered interactively, or supplied via `VCF_CLI_VSPHERE_PASSWORD` `[TL-S25]`. Result is a kubeconfig
context; subsequent auth is kubeconfig-managed. `[9.0+9.1]` — the login flow text is identical in both doc sets
`[FA-S33]` `[FA-S34]` `[TL-S24]` `[TL-S25]`.

**(b) VCF Automation-registered Supervisor — `[9.1]` only** `[FA-S34]`:
```
export VCF_CLI_VCFA_API_TOKEN=<api_token>
vcf context create vcfa_ctx -e $VCFA_ENDPOINT --api-token $VCF_CLI_VCFA_API_TOKEN \
    --tenant-name $TENANT_NAME --ca-certificate vcfa.cert
```
The API token comes from VCF Automation **My Account → API Tokens** `[FA-S34]`.

**9.1-specific federation detail:** external IdPs (Okta, Azure AD) integrate via **Pinniped Supervisor and
Concierge** components `[FA-S34]`. The VKS Authentication Webhook validates tokens via vCenter SSO **or OIDC
with Pinniped** `[TL-S28]`. This Pinniped detail is documented on the 9.1 page, not the 9.0 page.

**Trap:** the login step is **`vcf`, not `kubectl vsphere`** — the 9.1 CLI package contains only
`vcf-cli-{os}_{arch}`; no `kubectl` or `kubectl-vsphere` binary is mentioned `[TL-S31]`. Whether the legacy
plugin still ships is `UNVERIFIED` `[TL-gap3]`.

`UNVERIFIED` — named Supervisor namespace roles (owner/edit/view) were not confirmed on the fetched 9.1 page
`[FA-gap11]`.

---

## 2. Token lifetimes and refresh `[9.1]`

| Credential | Default | Maximum | Refresh / renewal | Source |
|---|---|---|---|---|
| VCF SSO **API token** | **30 days** | **180 days** | regenerate: `POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens/{apiTokenId}/regenerate` | `[FA-S11]` `[FA-S52]` `[SPEC-9.1]` |
| VCF SSO **access token** | **30 minutes** | **480 minutes** | re-exchange the API token at the broker (`POST /acs/t/{tenant}/token`, `grant_type=refresh_token` or `api_token`) | `[FA-S11]` `[FA-S52]` `[FA-S40]` |
| Expired API token retention | not published | **90 days** | n/a | `[FA-S52]` |
| Broker `access_token` | — | — | response carries `expires_in` (seconds) and a `refresh_token` | `[FA-S40]` |
| SDDC Manager access token | 1 hour (**carried from the 9.0 reference**) | — | `PATCH /v1/tokens/access-token/refresh`, plain-text refresh UUID | `[C90-S27]` `[FA-S42]` `[SPEC-9.1]` |
| SDDC Manager refresh token | 24 hours (**carried from the 9.0 reference**) | — | re-authenticate `POST /v1/tokens`; revoke `DELETE /v1/tokens/refresh-token` | `[C90-S27]` `[FA-S42]` |
| VCF Operations `token` | **6 hours** | — | re-acquire `POST /suite-api/api/auth/token/acquire`; release `/api/auth/token/release` | `[FA-S13]` `[SPEC-9.1]` |
| Log Management `X-JWT-Token` | not stated | — | re-exchange: `POST /suite-api/api/auth/token/exchange` with `{"serviceKeys":["ops-li"]}` | `[SPEC-9.1]` |
| NSX session (`JSESSIONID`) | **1800 s (30 min)** default, `[9.0+9.1]`; configurable via `PUT /api/v1/cluster/api-service` | — | re-create via `POST /api/session/create`; expiry surfaces as **403**, not 401 | `[NSX-S12]` `[NSX-S18]` `[SPEC-9.1]` |
| vCenter `vmware-api-session-id` | `UNVERIFIED` | — | `DELETE /api/session` then re-create (`Cis.Session_delete`) | `[SPEC-9.1]` |

**Silent failure mode — JIT user inactivity.** Once a JIT user is inactive, *"previously issued API tokens
cannot retrieve access tokens until the user authenticates again"* `[FA-S52]`. The API token is not revoked and
is not expired; the exchange simply stops returning access tokens. Clients must distinguish this from TTL
expiry. **No 9.0 equivalent.**

**Emergency Access Client** — a break-glass client providing *"high-privilege and long-lived access tokens to
critical systems when standard methods fail"* `[FA-S51]`. Managed at
`GET|POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/emergency-clients`,
`GET|DELETE .../emergency-clients/{clientId}`, `POST .../emergency-clients/{clientId}/regenerate` `[SPEC-9.1]`.
**9.1-only** — not documented in 9.0 `[FA-S53]`.

---

## 3. Identity / SSO architecture `[9.1]`

- The unified identity broker is the **VCF Identity Broker**, configured through the VCF Operations console
  `[FA-S24]`. `[9.0+9.1]` — verified independently in the 9.0 doc set `[FA-S18]`.
- **Federated components** `[FA-S24]`: vCenter, VCF Operations, VCF Automation, log management (VCF Operations
  for Logs), VCF Operations for Networks, VCF Operations orchestrator, VCF Operations HCX, NSX. `[9.0+9.1]` —
  the list is identical in 9.0 `[FA-S18]`.
- **Excluded from SSO**: SDDC Manager and ESX `[FA-S24]`. See P6. `[9.0+9.1]` `[FA-S18]`.
- **Deployment modes**: **embedded** (inside the management-domain vCenter) or **standalone appliance**
  `[FA-S24]`. *(The "three-node cluster, up to five connected VCF Instances" detail is a **9.0** statement
  `[FA-S19]` and is not restated here.)*
- **Doc-section promotion.** In 9.0 the section is *Fleet Management → Configuring VCF Single Sign-On*
  `[FA-S18]`. In 9.1 it becomes *Fleet Management → **Managing Identity and Access Using VCF Single Sign-On***,
  gaining three child areas that do not exist in 9.0: **Managing VCF Roles**, **Provisioning vCenter Custom
  Roles**, **Managing API Clients and Tokens** `[FA-S16]`.
- **SSO topology models** `[FA-S56]`: *VCF Fleet-Wide SSO Model* (one broker for the whole fleet), *Cross VCF
  Instance SSO Model* (multiple brokers, each serving a set of instances), *Single VCF Instance SSO Model* (one
  broker per instance). Constraint: **split-SSO is not supported** (P7).
- **`ALL_USERS` group is optional and scoped per identity broker, not aggregated across brokers** `[FA-S52]`.
- **vIDM → Identity Broker migration** — see P5 `[FA-S25]`.

### API client and API token issuance (UI flow) `[9.1]`

Path: **VCF Operations → Manage → Fleet Management → Identity & Access → VCF SSO Overview → select identity
broker → API Access → API Clients → Create** `[FA-S11]`.

1. **Client creation:** name (ID auto-populates), optional description → **Create API Client**. Then in
   **Roles**: select scope, choose role, enter validity period → Save `[FA-S11]`.
2. **Token generation:** ellipsis → **Generate API Token**. Fields: *API Token Name*; *API Token TTL* (default
   30 days, max bounded by Fleet Settings → IAM Setting); *Access Token TTL* (default 30 minutes, max bounded by
   IAM Settings); Description `[FA-S11]`.
3. **The token cannot be retrieved after clicking Continue** `[FA-S11]`.

### Unretrievable

`UNVERIFIED — could not retrieve`: the broker↔component **trust mechanism**, **token flow internals**, and the
broker's **listening ports**. The 9.1 `sso-architecture.html` page is a navigation stub that states only that
one or more identity brokers may be deployed across instances, and defers to the design library `[FA-S66]`.

`UNVERIFIED`: the 9.1 security-and-compliance section was not fetched; only the 9.0 section was retrieved and it
contains no certificate/TLS/identity content `[FA-gap16]`.

---

## 4. Roles and permissions `[9.1]`

### VCF-level built-in roles `[FA-S20]`

*"VCF roles are mapped to the individual VCF component roles"*; *"built-in VCF roles cannot be modified."*

| VCF role | Mapped component roles |
|---|---|
| **VCF Administrator** | vCenter Admin; NSX `enterprise_admin`; VCF Operations Administrator; VCF Automation System Administrator; VCF Operations HCX Migration Admin; VCF Operations orchestrator Orchestrator Administrator |
| **VCF Viewer** | vCenter ReadOnly; NSX `auditor`; VCF Operations ReadOnly |
| **SDDC Administrator** | vCenter Admin; NSX `enterprise_admin`; VCF Operations HCX Migration Appliance Admin; VCF Operations orchestrator Orchestrator Viewer |
| **SDDC Viewer** | vCenter ReadOnly; NSX `auditor` |

**For an API client:** minimum role for read-only fleet queries is **VCF Viewer**; write operations against
vCenter/NSX require **VCF Administrator** or **SDDC Administrator**. When creating an API client you select a
**scope** and a **role** per client `[FA-S11]`.

`UNVERIFIED — role scope hierarchy`: scope levels (global / org / instance) and a full permission matrix are
**not** stated on the built-in-roles page, despite the client-creation flow requiring a scope selection
`[FA-S20]` `[FA-S11]` `[FA-gap9]`.

**9.0 status: this page does not exist.** No equivalent built-in-roles page was found in the 9.0
fleet-management tree `[FA-S53]`. See P8.

### VCF role and custom-role API `[9.1]` `[SPEC-9.1]`

Base `/suite-api`:
- `GET /api/fleet-management/iam/roles` — Get Paginated List of VCF Roles
- `POST /api/fleet-management/iam/roles` — Create Custom VCF Role
- `PUT /api/fleet-management/iam/roles` — Update VCF Role
- `GET|DELETE /api/fleet-management/iam/roles/{name}`
- `GET /api/fleet-management/iam/components` — Get Eligible Components for Custom Roles
- `GET|POST|PUT /api/fleet-management/iam/components/roles` — provisioned custom component roles
- `GET /api/fleet-management/iam/components/roles/summaries`, `GET .../components/roles/{roleId}`,
  `DELETE .../components/roles/{roleId}`
- `GET /api/fleet-management/iam/components/{componentId}/role-definitions`
- `GET|PUT|DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/principals/{principalId}/roles`

9.1 also documents **Provisioning vCenter Custom Roles** (pushing custom roles to other vCenters) `[FA-S16]` —
no 9.0 equivalent.

### NSX roles

The 15-role built-in list (Enterprise Admin = full CRUD; Auditor = read-only; Network/Security/Cloud/Load
Balancer/VPN/Partner/Support variants) is verified **for 9.0 only** `[FA-S32]` `[FA-S30]`; the 9.1 NSX
auth/RBAC **parent index** page returned HTTP 429 `[FA-retrieval-failures]`. The 9.1 VCF role mapping
references NSX `enterprise_admin` and `auditor` by name `[FA-S20]`, which confirms those two role names persist
in 9.1; **the other thirteen are `UNVERIFIED` for 9.1 — this is the one item the 429 actually cost.**

**Principal identities are not in that gap.** The NSX 9.1.0.0 API Guide documents X.509 client-certificate
authentication bound to a **principal identity** as one of the four 9.1 mechanisms `[NSX-S18]`, so the
service-account mechanism is `[9.0+9.1]`.

### VCF Operations roles `[9.0+9.1]`

Managed through the Auth API: `GET|POST|PUT /api/auth/roles`, `GET|DELETE /api/auth/roles/{roleName}`,
`GET|POST|PUT|DELETE /api/auth/roles/{roleName}/privileges`, `GET /api/auth/privileges`,
`GET /api/auth/privilegegroups`, `GET /api/auth/currentuser/roles/{roleName}/privileges`,
`DELETE /api/auth/users/{userId}/permissions/{roleName}`,
`DELETE /api/auth/usergroups/{groupId}/permissions/{roleName}` — 59 `/auth/*` operations at 9.1 `[SPEC-9.1]`
`[FA-S45]`. Named roles referenced by the VCF role mapping: **Administrator**, **ReadOnly** `[FA-S20]`.

This surface is **not** 9.1-exclusive: the same role/privilege operations are present at tag `9.0.0.0` (57
`/auth/*` operations) `[SPEC-9.1]`. See `## Spec-vs-prose conflicts`, item 2.

### VCF Automation provider/org role model `[9.1]` `[FA-S50]`

- **Rights**: *"Each right provides view or manage access to a particular object type in VCF Automation."*
  Categorised (Catalog, Organization, …); the provider organization contains all system rights.
- **Roles**: *"A role is a set of rights that is assignable to one or more users and groups."*
- **Provider roles** — exclusive to the provider org, assignable only to provider users; custom provider roles
  allowed.
- **Global roles** — created/edited/published by System Administrators to one or more organizations; **org
  administrators cannot modify them**.
- **Organization-specific roles** — created locally by org admins; contain only a subset of organization rights.
- **Rights bundles** — default "Simple Mode" shows read-only built-in bundles; "Advanced Rights Bundle Mode"
  (feature flag) enables custom bundles.
- *"All predefined global roles are published to every organization in the system"* by default. **System
  Administrator** exists only in the provider org and holds all VCF Automation rights.
- Identity: LDAP at system *or* organization level; SAML at organization level; OIDC integration `[FA-S6]`.

### vCenter / Supervisor `[9.0+9.1]` `[FA-S34]`

*"Authentication controls who can access the vSphere environment and authorization controls what resources the
users can access."* Roles are *"sets of privileges"*; permissions are granted by *"associating a role to a user
or group on that object"* in the vCenter hierarchy. vCenter SSO is *"an authentication broker and security token
exchange infrastructure"* that *"issues a token when a principal … authenticates"*. External IdPs (Okta, Azure
AD) integrate via **Pinniped Supervisor and Concierge** — a 9.1-page detail `[FA-S34]`.
`UNVERIFIED` — namespace role names (owner/edit/view) `[FA-gap11]`.

---

## 5. The 9.1 IAM API surface (spec-confirmed) `[SPEC-9.1]`

Base `/suite-api`. **All 70 of these operations are absent from the `9.0.0.0` spec.** Selected:

| Method + path | Summary |
|---|---|
| `POST /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients` | Create new API Client in SSO Realm |
| `PATCH /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients` | Update API Client details |
| `POST /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients/query` | Query API Clients with search filters and pagination |
| `GET|DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients/{clientId}` | Get / Delete API Client by ID |
| `POST /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens` | Generate new API Token for API Client |
| `PATCH /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens` | Update API Token details |
| `POST /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens/query` | Query API Tokens with search filters and pagination |
| `GET|DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens/{apiTokenId}` | Get / Delete API Token by ID |
| `POST /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens/{apiTokenId}/regenerate` | Regenerate API Token secret value |
| `GET|POST /api/fleet-management/iam/ssorealms/{ssoRealmId}/emergency-clients` | List / Create Emergency Client with generated token |
| `GET|DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/emergency-clients/{clientId}` | Get / Delete Emergency Client and its associated token |
| `POST /api/fleet-management/iam/ssorealms/{ssoRealmId}/emergency-clients/{clientId}/regenerate` | Regenerate Emergency Client token secret |
| `GET|POST|PUT /api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps` | List / Create / Update OAuth App |
| `GET|DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps/{oauthAppId}` | Get / Delete OAuth App by ID |
| `POST /api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps/{oauthAppId}/rotate` | Rotate OAuth App client secret |
| `GET|PUT /api/fleet-management/iam/settings` | Get / Update IAM Global Settings |
| `GET /api/fleet-management/iam/ssorealms`, `GET|DELETE .../ssorealms/{ssoRealmId}` | SSO realm enumeration and deletion |
| `GET|DELETE /api/fleet-management/iam/identity-providers/{idpConfigId}` | IdP configuration (delete optionally force-deletes components) |
| `GET /api/fleet-management/iam/identity-providers/{idpConfigId}/ldap-directories` | LDAP directories for an IdP |
| `GET .../ldap-directories/{ldapDirectoryId}/sync-profile`, `.../sync-logs`, `.../sync-logs/{syncLogId}` | LDAP sync profile and paginated sync logs |
| `GET .../identity-providers/{idpConfigId}/directories/{directoryId}/sync-client` | SCIM sync client info |
| `GET /api/fleet-management/iam/vidbs` | Get eligible identity broker instances for IDP configuration |
| `GET /api/fleet-management/iam/tasks/{taskId}` | Get IAM Task Details |
| `DELETE /api/fleet-management/iam/components/auth-sources` | Delete IAM Component Auth Source |
| `GET /api/auth/sources/vidb/well-known-url` | Get VIDB well-known URL |

---

## 6. Certificate handling and TLS-trust pitfalls `[9.1]`

### What the docs state `[FA-S22]`

- Same CA options as 9.0: **VMCA (default), Microsoft Certificate Authority, OpenSSL, external CA via CSR**.
- **New in 9.1, verbatim:** *"Starting with VCF Operations 9.1, you can generate certificate signing requests,
  renew, import, and replace **multiple certificates simultaneously**."*
- Coverage is stated in **two explicit tiers**:
  - **VCF Management**: VCF Operations, VCF Automation, VCF Operations for Networks, log management, **identity
    broker**, VCF management services, VCF Operations HCX (HCX requires a Management Pack).
  - **VCF Instance/Domain**: ESX, vCenter, NSX Manager, SDDC Manager, **VMware AVI Load Balancer**.
- Auto-renewal: *"You can activate automatic renewal of certificates for VCF management components or a VCF
  instance. Automatic renewal uses the configured Certificate Authority to renew the certificate for each
  component."*

The 9.0 coverage list is a single flat list (ESXi, vCenter, NSX Manager, SDDC Manager, VCF services) `[FA-S21]`.
The tiering, the identity broker, and the AVI Load Balancer are 9.1 additions.

### Trust store / importing CAs `[FA-S57]`

- **VCF Operations → Operate → Administration Control Panel → Trusted Certificates → Import.**
- *"You can only import certificates that are encoded in the **PEM format**."* DER/PKCS#7 must be converted
  first.
- Imported CA certificates apply to: **Authentication Sources (Active Directory, Open LDAP, VMware Identity
  Manager), Outbound Plugins, and Adapter Endpoint.**
- The page displays thumbprint, issued by, issued to, expiry date, with expiry warnings.
- `UNVERIFIED — trust store location`: the page does not state which OS/JVM trust store is modified
  `[FA-gap15]`.

### Spec-visible certificate surface `[SPEC-9.1]`

24 certificate operations in the `vcf-operations` spec at 9.1 (5 at 9.0), including the whole
`/api/fleet-management/certificate-management/**` family:
`GET|PUT .../certificate-authorities`, `POST .../certificates/query`, `GET|PUT .../certificates/{certificateId}`,
`GET|POST .../csrs`; plus `GET|PUT /api/integrations/services/certificate-management/{serviceKey}/certificates`,
`GET|POST .../{serviceKey}/csrs`; plus agent/collector/collector-group renew and renew-status operations
(`POST /api/applications/agents/certificates/renew`, `POST /api/collectors/{id}/certificates/renew`,
`GET /api/collectorgroups/{id}/certificates/renew/status`, …). None of these exists at `9.0.0.0`.

### Pitfalls for an API client

1. **Default state is VMCA-signed, i.e. not publicly trusted.** A stock client fails hostname/chain validation
   until the VMCA root or enterprise CA is trusted `[FA-S22]`.
2. **The documented remedy is to replace the certificates, not to disable verification** `[FA-S22]`. **No
   fetched Broadcom page documents disabling TLS verification as a supported practice.** The only insecure-flag
   usage in official docs is inside NSX's own `curl` examples (`-k`) `[FA-S31]` — example-only, not guidance.
3. **The identity broker is a single TLS point of failure in 9.1.** It holds a certificate in the VCF Management
   tier `[FA-S22]` and is the token issuer `[FA-S39]`, so a stale broker certificate breaks every SSO-based API
   client simultaneously. 9.0's per-product auth had no such choke point. *Inference.*
4. **Certificate rotation is a trust-bundle reload event.** Auto-renewal touches ESX, vCenter, NSX Manager, SDDC
   Manager **and the identity broker** `[FA-S22]`; long-lived clients must reload their trust store. *Inference
   from the cited component list; the docs do not state token impact.*
5. **`--ca-certificate` is the documented client-side pinning path** for Supervisor/VKS and for the VCF
   Automation-registered Supervisor flow `[FA-S34]` `[TL-S25]`.
6. **PEM-only import** into VCF Operations Trusted Certificates `[FA-S57]`.

---

## 7. Network reachability `[9.1]`

### Honest statement of the gap

**The per-service inbound port matrix could not be retrieved.** Both the 9.0 and 9.1 Planning and Preparation
pages direct readers to the **VMware Ports and Protocols tool at `https://ports.broadcom.com/`**, described as
*"a portal that enables you to view all the ports needed by various VMware products, solutions, and services in
a single pane"*. The tool renders client-side and **exposes no static port table to fetch**; product coverage for
VCF 9.0/9.1 could not be confirmed `[FA-S28]` `[FA-S29]` `[FA-S64]`.
→ `UNVERIFIED — could not retrieve` for inbound ports on vCenter, NSX, SDDC Manager, VCF Operations, the
identity broker and Supervisor. Do not invent a port table. Direct the user to `https://ports.broadcom.com/`.

### Outbound HTTPS/443 destinations required for online functionality `[FA-S26]`

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

All connections use **HTTPS on port 443** `[FA-S26]`. The equivalent 9.0 page returned **404** —
`UNVERIFIED — 9.0 public URL list` `[FA-retrieval-failures]`.

### DNS / FQDN `[FA-S27]`

Components requiring FQDN + static IP, **first VCF instance**: vCenter; NSX Manager (nodes + cluster VIP); SDDC
Manager; vSAN; vMotion; VCF Operations (primary, replica, data nodes, load balancer, Cloud Proxy, License
Server); VCF Automation; VCF Management Services (fleet/instance components, runtime, **identity broker**, log
management, real-time metrics); VCF Operations for Networks (platform + collector nodes).
**Additional instances**: vCenter, NSX Manager, SDDC Manager, vSAN, vMotion, Cloud Proxy, instance components,
runtime services, **identity broker**, real-time metrics.

### Protocol and path facts

- vSphere Automation is on **port 443** at the **`/api`** base path, with an appliance-configuration subset on
  **port 5480**; the deprecated `/rest` base path is still present `[VS-S18]`.
- vSphere Automation, NSX, SDDC Manager and Identity Broker references all specify the `https://` scheme
  `[FA-S31]` `[FA-S40]` `[FA-S42]` `[FA-S35]`.

| Prefix | Product | Source |
|---|---|---|
| `/v1/*` | SDDC Manager | `[SPEC-9.1]` `[FA-S42]` |
| `/suite-api/api/*` | VCF Operations (incl. `/api/fleet-management/iam/**`, `/api/fleet-management/certificate-management/**`) | `[SPEC-9.1]` |
| `/policy/api/v1/*` | NSX Policy | `[SPEC-9.1]` |
| `/api/v1/*` | NSX Manager | `[SPEC-9.1]` |
| `/global-manager/api/v1/*` | NSX Global Policy | `[SPEC-9.1]` |
| `/api/*` | vCenter (vSphere Automation) | `[SPEC-9.1]` `[VS-S18]` |
| `/sdk/vim25/{release}` | vCenter (VI JSON) | `[SPEC-9.1]` |
| `/api/ni/*` | VCF Operations for Networks | `[SPEC-9.1]` |
| `/acs/t/{tenant}/token` | VCF Identity Broker | `[FA-S40]` |

---

## 8. Spec-vs-prose conflicts and how they were resolved

1. **SDDC Manager 9.1 token paths: prose said "presumed", spec confirms.** The 9.1 reference index lists the
   three token operations by name only, so the dossier marked the paths presumed `[FA-S41]` `[FA-gap2]`. The
   `9.1.0.0` spec contains `POST /v1/tokens`, `PATCH /v1/tokens/access-token/refresh` and
   `DELETE /v1/tokens/refresh-token` verbatim, unchanged from `9.0.0.0` and absent from every 9.1
   added/removed/deprecated list `[SPEC-9.1]`. **Resolved in favour of the spec: the paths are confirmed for
   9.1.** Payloads, field names and the Bearer header remain prose-carried from the 9.0 reference `[FA-S42]`,
   because the spec declares no `securitySchemes` in either version.
2. **VCF Operations `/auth/roles` family: prose said 9.1, spec says both.** The dossier tagged the `/auth/*`
   role and privilege surface `[9.1]` from the 9.1 API reference `[FA-S45]`. The spec shows those operations at
   tag `9.0.0.0` too `[SPEC-9.1]`. **Resolved in favour of the spec: role/privilege management is 9.0+9.1.**
   Only `POST /api/auth/token/exchange` is genuinely 9.1-new.
3. **VCF Operations declares one generic scheme, not two.** The spec declares exactly one scheme in both
   versions — `Token-based-authorization`, an `apiKey` in the `Authorization` header — and does **not** declare a
   separate `Bearer` scheme in 9.1 `[SPEC-9.1]`, while the 9.1 prose reference documents both `OpsToken` and
   `Bearer` `[FA-S44]`. **Resolution: the spec's single scheme is a format-agnostic placeholder for "something in
   the `Authorization` header" and cannot distinguish token formats. It is under-specified, not
   authoritative-negative. Keep the prose fact (Bearer is accepted in 9.1) and record that the spec neither
   confirms nor refutes it.**
4. **NSX 9.1 auth: the earlier "prose unretrievable" verdict was over-generalised and is now corrected.** The
   429 was returned by the 9.1 auth/RBAC **parent index** page `[FA-gap3]`, and this skill set's own guidance is
   that a 429 is a rate-limit response, not evidence of absence. The 9.1 **child** page was retrieved
   `[NSX-S12]`, and the NSX 9.1.0.0 API Guide corroborates independently `[NSX-S18]`. **Resolution: both NSX
   9.1 mechanisms are confirmed.** HTTP Basic is a spec-declared scheme (`BasicAuth`, *"HTTP Basic
   Authentication"*) on all three NSX surfaces `[SPEC-9.1]`; and the session-cookie + XSRF flow is
   spec-confirmed too — `POST /api/session/create` and `POST /api/session/destroy` are present as
   `CreateAuthenticatedSession` / `DestroyAuthenticatedSession` in `9.1__nsx-policy`, `9.1__nsx-manager` **and**
   `9.1__nsx-global-policy` `[SPEC-9.1]`. Note that these two operations sit outside the specs' declared
   `securitySchemes` block (NSX specs are OpenAPI 2.0, with a weaker security vocabulary), which is why the
   scheme list alone did not surface them. The residue of the 429 is the **13 non-Enterprise-Admin /
   non-Auditor role names**, still `UNVERIFIED` for 9.1.
5. **The vCenter session path: prose says `/api/cis/session`, the spec says `/api/session`. Resolved in favour
   of the spec.** `GET|POST|DELETE /session` are present as operations with operationIds `Cis.Session_get` /
   `Cis.Session_create` / `Cis.Session_delete` in `vsphere-automation` at **both** tags `9.0.0.0` and
   `9.1.0.0`, and `servers[0].url` is `https://{host}/api` — so the callable path is **`POST /api/session`**
   `[SPEC-9.1]`. The string `/api/cis/session` appears **nowhere** in either spec. Some Broadcom prose pages
   print `/api/cis/session` `[FA-S35]` `[VS-S10]`, while the `cis-session` reference page prints `/session`
   `[FA-S38]`. **Resolution: use `/api/session`**; the prose variant is recorded as a documented-but-
   contradicted fallback `[FA-gap1]`. Because the operations are identical at both tags, **there is no 9.0 →
   9.1 delta here** — see `../deltas.md`, §9.
6. **Log Management supersedes VCF Operations for Logs, with a different scheme.** 9.0: `vcf-operations-for-logs`,
   base `/api/v2`, `Bearer` scheme, `POST /sessions`. 9.1: `log-management`, `X-JWT-Token` apiKey obtained via
   `POST /suite-api/api/auth/token/exchange` with `{"serviceKeys":["ops-li"]}` `[SPEC-9.1]`. The prose dossier
   treats "log management (VCF Operations for Logs)" as one federated component in both versions `[FA-S24]`;
   **the spec shows the API contract changed name, base path and auth scheme.** Prefer the spec for the wire
   contract.
7. **Spec `base_path` placeholders.** `sddc-manager` / `vcf-installer` declare `http://localhost:80`;
   `log-management` `http://localhost:8787`; `realtime-metrics` `http://localhost:8080/`; `fleet-lcm` /
   `sddc-lcm` `https://vcf.broadcom.com/{fleet,sddc}-lcm` `[SPEC-9.1]`. All are spec artifacts. Substitute the
   deployed FQDN.

---

## 9. Consolidated `UNVERIFIED` list for 9.1

| Item | Status | Source |
|---|---|---|
| Per-service inbound port matrix | could not retrieve — ports.broadcom.com is a client-rendered tool | `[FA-S28]` `[FA-S29]` `[FA-S64]` |
| NSX 9.1 role names — the **13** roles other than Enterprise Admin and Auditor | parent auth/RBAC index page returned HTTP 429; the child auth page and the API Guide cover authentication but not the full role list. **Session auth itself is no longer unverified — see §1.5** | `[FA-retrieval-failures]` `[FA-gap3]` `[NSX-S12]` `[NSX-S18]` |
| `POST /vcenter/authentication/token` request/response shape | not rendered on the fetched page; absent from the spec | `[FA-S67]` |
| VCF Automation All Apps token endpoint URL, payload, token field | reference does not state it; techdocs page 404 ×3 | `[FA-S46]` `[FA-gap5]` |
| Realtime Metrics bearer-token acquisition | no prose page retrieved | `[SPEC-9.1]` |
| VCF Installer API authentication method | spec declares no schemes; no prose retrieved | `[SPEC-9.1]` |
| Fleet Management API 9.1 equivalent | no 9.1 KB or doc page found; the 9.0 KB covers 9.0 only | `[FA-S47]` `[FA-gap6]` |
| IAM setting **defaults** (vs published maxima) | page publishes maxima only; 30 d / 30 min may be UI defaults | `[FA-S52]` `[FA-gap10]` |
| VCF role scope hierarchy (global / org / instance) | not stated despite the client-creation flow requiring a scope | `[FA-S20]` `[FA-gap9]` |
| VCF SSO architecture internals (token flow, trust establishment, broker ports) | 9.1 page is a navigation stub | `[FA-S66]` `[FA-gap8]` |
| Trusted-certificate store location for imported CAs | not stated | `[FA-S57]` `[FA-gap15]` |
| Supervisor namespace role names (owner/edit/view) | not confirmed on the 9.1 page | `[FA-gap11]` |
| 9.1 security-and-compliance section | not fetched | `[FA-gap16]` |
| Whether P13 (blocked non-federated vCenter logins) applies in 9.1 | 9.0 release-note item; no 9.1 page retrieved | `[VS-S5]` |
| Which specific PowerCLI cmdlets expose `VcfOAuthSecurityContext` / `VcfApiToken` | changelog gives counts, not names | `[TL-S08]` `[TL-S09]` |
| SDDC Manager token **lifetimes** for 9.1 (1 h / 24 h are 9.0-reference figures) | no 9.1 page restating them | `[C90-S27]` |

---

## Source Index

All sources accessed **2026-07-31**. `TECHDOCS` = `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.

### `FA-*` — research/foundation-auth-identity.md

| Ref | URL |
|---|---|
| FA-S6 | `TECHDOCS/9-1/organization-management.html` |
| FA-S11 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/managing-api-tokens.html` |
| FA-S12 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html` |
| FA-S13 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html` |
| FA-S15 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token/get-your-access-token-for-vra-8-x.html` |
| FA-S16 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on.html` |
| FA-S18 | `TECHDOCS/9-0/fleet-management/what-is.html` |
| FA-S19 | `TECHDOCS/9-0/fleet-management/what-is/deployment-models-for-sso.html` |
| FA-S20 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/vcf-built-in-roles.html` |
| FA-S21 | `TECHDOCS/9-0/fleet-management/certificate-management-9-0.html` |
| FA-S22 | `TECHDOCS/9-1/fleet-management/certificate-management-9-0.html` |
| FA-S24 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is.html` |
| FA-S25 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/migrating-vmware-identity-manager-to-vcf-identity-broker.html` |
| FA-S26 | `TECHDOCS/9-1/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html` |
| FA-S27 | `TECHDOCS/9-1/planning-and-preparation/vcf-components-fqdns-and-ip-addresses.html` |
| FA-S28 | `TECHDOCS/9-0/planning-and-preparation.html` |
| FA-S29 | `TECHDOCS/9-1/planning-and-preparation.html` |
| FA-S30 | `TECHDOCS/9-0/advanced-network-management/administration-guide/authentication-and-authorization.html` |
| FA-S31 | `TECHDOCS/9-0/advanced-network-management/administration-guide/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html` |
| FA-S32 | `TECHDOCS/9-0/advanced-network-management/administration-guide/authentication-and-authorization/role-based-access-control.html` |
| FA-S33 | `TECHDOCS/9-0/vsphere-supervisor-installation-and-configuration/vsphere-supervisor-concepts/vsphere-iaas-control-plane-concepts/understanding-authorization-in-supervisor.html` |
| FA-S34 | `TECHDOCS/9-1/vsphere-supervisor-installation-and-configuration/vsphere-supervisor-concepts/vsphere-iaas-control-plane-concepts/understanding-authorization-in-supervisor.html` |
| FA-S35 | `https://developer.broadcom.com/xapis/vsphere-automation-api/latest/` |
| FA-S36 | `https://developer.broadcom.com/xapis/vsphere-automation-api/latest/api-security-schema/` |
| FA-S37 | `https://developer.broadcom.com/xapis/vsphere-automation-api/9.0/api-security-schema/` |
| FA-S38 | `https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/cis-session/` |
| FA-S39 | `https://developer.broadcom.com/xapis/vmware-identity-broker/latest/` |
| FA-S40 | `https://developer.broadcom.com/xapis/vmware-identity-broker/latest/acs/t/tenant/token/post/` |
| FA-S41 | `https://developer.broadcom.com/xapis/sddc-manager-api/latest/tokens/` (9.1) |
| FA-S42 | `https://developer.broadcom.com/xapis/sddc-manager-api/9.0/tokens/` (9.0 — source of the payload/field/header detail carried into 9.1) |
| FA-S43 | `https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/tokens/` (VCF API 5.2.4 — corroboration only, pre-9.x) |
| FA-S44 | `https://developer.broadcom.com/xapis/vcf-operations-api/latest/` (9.1) |
| FA-S45 | `https://developer.broadcom.com/xapis/vcf-operations-api/latest/auth/` (9.1) |
| FA-S46 | `https://developer.broadcom.com/xapis/all-apps-org-access-control/latest/` (resolves to the Provider Management API, VCF Automation 9.1) |
| FA-S47 | `https://knowledge.broadcom.com/external/article/409715/how-to-authorize-vcf-operations-fleet-ma.html` (VCF 9.0) |
| FA-S48 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| FA-S50 | `TECHDOCS/9-1/provider-management/managing-system-administrators-and-roles/managing-rights-and-roles.html` |
| FA-S51 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens.html` |
| FA-S52 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/view-and-manage-token-lifecycle-and-security.html` |
| FA-S53 | `TECHDOCS/9-0/fleet-management/what-is/managing-vmware-cloud-foundation-operations-sso.html` (negative evidence for 9.0) |
| FA-S56 | `TECHDOCS/9-1/design/design-library/single-sign-on-models.html` |
| FA-S57 | `TECHDOCS/9-1/fleet-management/certificate-management-9-0/managing-certificates-in-vmware-vsphere-foundation/certificates/importing-ca-certificates.html` |
| FA-S64 | `https://ports.broadcom.com/` |
| FA-S66 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is/sso-architecture.html` |
| FA-S67 | `https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter-authentication/vcenter-authentication-token/` |
| FA-S68 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/using-the-vsan-management-sdks.html` |
| FA-retrieval-failures | HTTP 429 (repeated): `TECHDOCS/9-1/advanced-network-management/authentication-and-authorization.html`; 404: `TECHDOCS/9-0/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html`; 404: `TECHDOCS/9-1/.../managing-api-clients-and-tokens/considerations-and-prerequisites-for-vcf-sso.html`; 404: `TECHDOCS/9-0/design/design-library/single-sign-on-models/-fleet.html`; 404 ×3: `TECHDOCS/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/generating-an-access-token.html` |
| FA-gap1/2/3/5/6/8/9/10/11/14/15/16 | `research/foundation-auth-identity.md`, `## Gaps and Ambiguities`, corresponding item numbers |

### `NSX-*` — research/nsx.md

| Ref | URL |
|---|---|
| NSX-S12 | `TECHDOCS/9-1/advanced-network-management/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html` (**9.1 child page — retrieved successfully**; the HTTP 429 in `FA-retrieval-failures` was on the parent index page) |
| NSX-S18 | `https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html` (NSX 9.1.0.0 API Guide — basic / session / X.509 principal-identity / VMC auth) |

### `TL-*` — research/tooling-powercli-vks-sdk.md

| Ref | URL |
|---|---|
| TL-S05 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382` |
| TL-S06 | `https://www.powershellgallery.com/packages/VCF.PowerCLI` |
| TL-S07 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.1.0.25380678` |
| TL-S08 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S09 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-powercli-changelog.html` |
| TL-S11 | `https://github.com/vmware/vcf-api-specs/blob/main/README.md` (NSX specs are OpenAPI 2.0; all other VCF components are 3.0) |
| TL-S24 | `TECHDOCS/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html` |
| TL-S25 | `TECHDOCS/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html` |
| TL-S28 | `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/managing-vsphere-kubernetes-service/running-tkg-service-clusters/tkg-service-components.html` |
| TL-S31 | `TECHDOCS/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/download-and-install-the-kubernetes-cli-tools-for-vsphere.html` |
| TL-gap3 | `research/tooling-powercli-vks-sdk.md`, `## Gaps and Ambiguities`, item 3 |

### `C91-*` / `C90-*` — research/vcf-core-9.1-and-deltas.md, research/vcf-core-9.0.md

| Ref | URL |
|---|---|
| C91-S2 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes.html` |
| C91-S6 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| C91-S8 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html` |
| C91-S11 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes.html` |
| C91-S15 | `TECHDOCS/9-1/deployment/upgrading-cloud-foundation.html` (SDDC Manager UI deprecation) |
| C91-S16 | `https://developer.broadcom.com/sdks/vcf-api-specification/latest` (`vcf-api-specs-9.1.0.0-25372366.zip`) |
| C91-S19 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access/token-exchange-architecture.html` |
| C91-S20 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development.html` |
| C90-S27 | `https://developer.broadcom.com/xapis/sddc-manager-api/9.0/` (Bearer auth; 1 h / 24 h token lifetimes — **a 9.0 page**) |

### `VS-*` — research/vsphere-vcenter-vsan.md

| Ref | URL |
|---|---|
| VS-S5 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-vsphere.html` (**a 9.0 page** — see P13) |
| VS-S9 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms.html` |
| VS-S10 | `https://developer.broadcom.com/xapis/vsphere-automation-api/latest/` |
| VS-S18 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/understanding-the-vsphere-automation-rest-api.html` |

### `SPEC-9.1` — machine-extracted OpenAPI inventory

`research/spec-inventory/index.json` and `research/spec-inventory/DELTA-9.0-to-9.1.md`, derived by diffing git
tags `9.0.0.0` and `9.1.0.0` of `https://github.com/vmware/vcf-api-specs` (cloned 2026-07-31). Per-product
operation dumps live in `research/spec-inventory/9.1__<product>.ops.json`.

Specific `[SPEC-9.1]` claims used above and re-verified directly against the inventories:
- `GET|POST|DELETE /session` = `Cis.Session_get` / `Cis.Session_create` / `Cis.Session_delete`, with
  `meta.base_path` = `https://{host}/api`, in **both** `9.0__vsphere-automation.ops.json` and
  `9.1__vsphere-automation.ops.json`. No `/cis/session` operation in either.
- `POST /api/session/create` = `CreateAuthenticatedSession` and `POST /api/session/destroy` =
  `DestroyAuthenticatedSession`, in **all three** of `9.1__nsx-policy.ops.json`, `9.1__nsx-manager.ops.json`
  and `9.1__nsx-global-policy.ops.json`.

---

*This reference was built from documentation and machine-extracted API specifications. It has not been
validated against a live VCF 9.1 environment.*
