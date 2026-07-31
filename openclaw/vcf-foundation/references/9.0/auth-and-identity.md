# VCF 9.0 — Authentication, Identity, Certificates, Reachability

**Scope: VMware Cloud Foundation 9.0 only.** Nothing on this page is asserted for 9.1. Where a fact was
verified independently in both doc sets the tag `[9.0+9.1]` appears inline, and the 9.1 file states the
same fact separately. Facts the research could not retrieve are marked `UNVERIFIED` in place — they are
not omitted and not filled in by inference.

Two classes of evidence are used and are labeled distinctly:

- **Prose evidence** — Broadcom TechDocs / developer-portal pages, cited `[FA-Sxx]`, `[TL-Sxx]`, `[C90-Sxx]`,
  `[VS-Sxx]` and resolved to full URLs in `## Source Index`.
- **Spec evidence** — machine-extracted `securitySchemes` and operation lists from the OpenAPI specs at git
  tag `9.0.0.0` of `github.com/vmware/vcf-api-specs`, cited `[SPEC-9.0]`. Spec evidence outranks prose where
  the two disagree; every disagreement is called out at `## Spec-vs-prose conflicts`.

---

## Contents

- [Prerequisites](#prerequisites) — P1 version pinning · P2 no SSO API tokens · P3 SSO exclusions ·
  P4 blocked non-federated vCenter logins · P5 no VCF built-in roles · P6 NSX principal identities ·
  P7 refresh-capable credential store · P8 TLS trust · P9 DNS/FQDN · P10 reachability · P11 PowerCLI
- [1. Per-product authentication](#1-per-product-authentication-90) — 1.1 SDDC Manager · 1.2 vCenter /
  vSphere Automation · 1.3 VI JSON · 1.4 NSX Manager · 1.5 VCF Operations · 1.6 VCF Operations roles API ·
  1.7 Operations for Logs · 1.8 Operations for Networks · 1.9 Fleet Management API · 1.10 VCF Automation ·
  1.11 vSAN · 1.12 VCF Installer · 1.13 Supervisor / VKS
- [2. Token lifetimes and refresh](#2-token-lifetimes-and-refresh-90)
- [3. Identity / SSO architecture](#3-identity--sso-architecture-90)
- [4. Roles and permissions](#4-roles-and-permissions-90)
- [5. Certificate handling and TLS-trust pitfalls](#5-certificate-handling-and-tls-trust-pitfalls-90)
- [6. Network reachability](#6-network-reachability-90)
- [7. Spec-vs-prose conflicts and how they were resolved](#7-spec-vs-prose-conflicts-and-how-they-were-resolved)
- [8. Consolidated `UNVERIFIED` list for 9.0](#8-consolidated-unverified-list-for-90)
- [Source Index](#source-index)

---

## Prerequisites

Read this whole block before issuing any request. Each item states **(a)** what must be true, **(b)** how to
verify it is satisfied, **(c)** the version it applies to, **(d)** whether it exists in the other version.

### P1 — The target version is confirmed to be 9.0 before any auth flow is chosen

(a) The auth surface differs materially between 9.0 and 9.1. Choosing a flow before pinning the version
produces endpoints that do not exist.
(b) Verify from the deployed BOM, not from assumption: VCF 9.0.0.0 released **17 JUN 2025, build 24755599**
`[C90-S2]`. Any 9.1 answer would be build family 9.1.0.0, released 12 MAY 2026 `[C91-S2]`.
(c) 9.0.
(d) The same discipline applies in 9.1; the 9.1 file is the counterpart.

### P2 — SSO-issued, role-scoped API tokens DO NOT EXIST in 9.0

**This is the single loudest prerequisite on this page.**

(a) There is **no VCF SSO API client, no SSO-issued API token, no OAuth-app management, and no emergency
access client** in VCF 9.0. Automation must use **per-product credentials** (P4–P11 below).
(b) Two independent verifications:
  - **Doc-tree check:** the 9.0 "Managing VMware Cloud Foundation Operations SSO" tree contains only SSO
    overview, reset, change IdP, change deployment mode, edit IdP config, additional component
    configurations, deregister configurations, and change identity management. There is **no API client, API
    token, OAuth client, or role management page** `[FA-S53]`.
  - **Spec check (strongest):** the `vcf-operations` OpenAPI spec at tag `9.0.0.0` contains **0 operations**
    under `/api/fleet-management/iam/**`. The 9.1 spec contains **70** `[SPEC-9.0]`. There is no
    `.../iam/ssorealms/{ssoRealmId}/api-tokens`, `.../api-clients`, `.../oauth-apps`, `.../emergency-clients`,
    or `.../iam/settings` route to call on a 9.0 appliance.
(c) 9.0.
(d) **Exists in 9.1.** SSO-issued role-scoped API tokens, API clients, OAuth apps, emergency access clients
and IAM TTL ceilings are all 9.1 capabilities `[FA-S51]` `[FA-S11]` `[FA-S52]` `[SPEC-9.1]`. Do not walk a 9.0
user through the 9.1 *Fleet Management → Identity & Access → API Clients* flow — the navigation node is not
present.

### P3 — SDDC Manager and ESX are excluded from VCF SSO

(a) SDDC Manager authentication is **not** SSO-brokered. It has its own `/v1/tokens` flow (§1.1). ESX is
likewise excluded.
(b) The 9.0 SSO overview lists the federated components explicitly — vCenter, VCF Operations, VCF Automation,
log management (VCF Operations for Logs), VCF Operations for Networks, VCF Operations orchestrator, VCF
Operations HCX, NSX — and explicitly excludes SDDC Manager and ESX `[FA-S18]`.
(c) 9.0.
(d) `[9.0+9.1]` — verified independently in the 9.1 doc set as well, with the identical component list and
identical exclusions `[FA-S24]`. This exclusion does **not** go away in 9.1.

### P4 — vCenter 9.0 blocks non-federated username/password logins

(a) A plain Basic-auth session create against vCenter using only a username and password may be rejected.
Verbatim from the 9.0 vSphere product support notes: *"Blocked non-federated username/password logins to
vCenter: vCenter 9.0 blocks logins with just a user name and password, which might sometimes allow bypassing
the federated provider domain."* `[VS-S5]`
(b) Verify by checking whether the vCenter is federated with an external identity provider, and by testing a
session create. If federated, the documented prerequisite is the **three-step federated flow** (vSphere 7.0+):
obtain a JWT from the external IdP → exchange the JWT for a vCenter SSO SAML token → exchange the SAML token
for a session identifier `[VS-S9]`. Basic authentication is documented but *"VMware discourages"* it in favour
of token-based flows `[VS-S9]`.
(c) 9.0 — this is a 9.0 release-note removal item.
(d) **9.1 status: `UNVERIFIED`.** No 9.1 page re-stating or relaxing this behavior was retrieved. Do not
assert it as a 9.1 behavior and do not assert it was reverted.
> Diagnostic note: a script that worked on vSphere 8.x and fails after a 9.0 upgrade at the session-create
> step should be assessed against this removal **before** a certificate hypothesis is raised. A TLS trust
> failure (P8) presents as a transport/verification error, not an authentication rejection.

### P5 — VCF built-in roles are NOT documented for 9.0

(a) Do not reference **VCF Administrator, VCF Viewer, SDDC Administrator, SDDC Viewer** when answering for
9.0. These names and their component mappings appear only in the 9.1 doc set.
(b) No equivalent built-in-roles page was found anywhere in the 9.0 fleet-management tree `[FA-S53]`; the page
that defines them is 9.1-only `[FA-S20]`.
(c) 9.0.
(d) **Exists in 9.1** (see the 9.1 file, §Roles). In 9.0, authorization is granted **per component**: the
documented 9.0 SSO configuration order ends at step 7, *"Assign required roles and permissions for users or
groups"*, performed **in the individual components**, not centrally `[FA-S54]`.

### P6 — NSX service-account access uses principal identities

(a) For non-interactive NSX access in 9.0, the documented mechanism is an NSX **principal identity**, not an
SSO token.
(b) Principal identities are documented as the mechanism for service-account style API access in the 9.0 NSX
authentication and RBAC pages `[FA-S30]` `[FA-S32]`.
(c) 9.0.
(d) `[9.0+9.1]` — the NSX 9.1.0 API Guide documents the same four authentication mechanisms as 9.0, including
**X.509 client-certificate authentication bound to a principal identity** `[NSX-S18]`. The earlier
`UNVERIFIED` verdict here came from an HTTP 429 on the 9.1 *parent index* page `[FA-gap3]`; the child page and
the 9.1 API Guide were both retrieved `[NSX-S12]` `[NSX-S18]`. What remains genuinely unverified for 9.1 is the
list of **13 non-Enterprise-Admin / non-Auditor NSX role names** (§4).

### P7 — A refresh-capable credential store exists before the first call

(a) Every 9.0 product token is short-lived (§2). A client must hold the refresh material, not just the access
token.
(b) Verify you captured `refreshToken.id` from the SDDC Manager token-pair response `[FA-S42]`, and that the
VCF Operations six-hour expiry `[FA-S12]` and NSX 1800-second session timeout `[FA-S31]` are handled.
(c) 9.0.
(d) In 9.1 the same per-product refresh applies, plus an SSO API-token → access-token exchange with its own
TTL ceilings that do not exist in 9.0.

### P8 — The client trusts the VCF certificate chain

(a) At deployment *"each component is assigned a certificate from a default signing Certificate Authority
(VMware Certificate Authority CA)"* `[FA-S21]`. That chain is **not** publicly trusted, so a stock HTTP client
fails chain/hostname validation against vCenter, NSX, SDDC Manager and VCF Operations until the VMCA root or
the enterprise CA is in the client trust store.
(b) Verify by performing a TLS handshake with verification **enabled** and inspecting the issuer. Remediate by
importing the CA, or by replacing the component certificates — the documented supported CA types are **VMCA,
Microsoft Certificate Authority, OpenSSL, self-signed**, managed from the VCF Operations console `[FA-S21]`.
(c) 9.0.
(d) `[9.0+9.1]` — the same default-VMCA state and the same replace-don't-disable guidance are verified
independently in the 9.1 cert-management page `[FA-S22]`. **No fetched Broadcom page documents disabling TLS
verification as a supported practice.** The only `-k` usage observed in official docs is inside NSX's own
`curl` examples `[FA-S31]`; treat it as example-only.

### P9 — DNS resolves every component FQDN, and the client connects by FQDN

(a) Certificates are issued to FQDNs. Connecting by IP address fails hostname verification.
(b) Verify forward and reverse resolution for each component FQDN before authenticating.
(c) The explicit DNS/FQDN requirement statement was retrieved from the **9.1** planning page `[FA-S27]`; the
equivalent 9.0 statement was not separately captured. Treat the FQDN-vs-certificate consequence as an
operational inference for 9.0, not as a quoted 9.0 requirement.
(d) Verified as documented text in 9.1 `[FA-S27]`.

### P10 — Outbound and inbound reachability

(a) All documented VCF API traffic is HTTPS. The vSphere Automation API is *"available on port **443** and the
**`/api`** base path"*, with an appliance-configuration subset also on **port 5480** `[VS-S8]`.
(b) Verify TCP/443 to each target FQDN.
(c) 9.0.
(d) **`UNVERIFIED — could not retrieve` in both versions:** the per-service *inbound* port matrix. Both the 9.0
and 9.1 Planning and Preparation pages defer to the VMware Ports and Protocols tool at
`https://ports.broadcom.com/`, which renders client-side and exposes no static table; VCF 9.0/9.1 coverage
could not be confirmed `[FA-S28]` `[FA-S29]` `[FA-S64]`. See §6.

### P11 — PowerCLI 9.0 has no token-auth parameters

(a) Do not attempt `-VcfApiToken` or `-VcfOAuthSecurityContext` against `{PCLI 9.0.0}`.
(b) Verify with `Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version` — the 9.0-aligned
module is `VCF.PowerCLI 9.0.0.24798382` `[TL-S05]` `[TL-S06]`.
(c) 9.0.
(d) **Introduced in 9.1**: `VcfOAuthSecurityContext` and `VcfApiToken` parameters appear in `{PCLI 9.1.0}`
`[TL-S08]`. See `../powercli-session.md`.

---

## 1. Per-product authentication `[9.0]`

Base-path warning: the machine-extracted `servers[0].url` for the SDDC Manager and VCF Installer specs is the
placeholder `http://localhost:80` `[SPEC-9.0]`. That is a spec artifact, **not** a callable base. The real base
is `https://<component-fqdn>` + the versioned path prefix; the 9.0 SDDC Manager reference uses the example base
`https://sfo-vcf01.rainpole.io/v1` `[C90-S29]`.

### 1.1 SDDC Manager — `POST /v1/tokens`

| Field | Value |
|---|---|
| Method + path | `POST /v1/tokens` — "Create Token Pair" `[FA-S42]` `[SPEC-9.0]` |
| Payload | JSON: `{"username":"string","password":"string"}` `[FA-S42]` |
| Token field | `accessToken` (JWT); refresh handle at `refreshToken.id` (UUID) `[FA-S42]` |
| Subsequent header | `Authorization: Bearer <accessToken>` `[FA-S42]` `[FA-S43]` |
| Refresh | `PATCH /v1/tokens/access-token/refresh` — "Refresh Access Token". Body is the **plain-text refresh-token UUID, not JSON**. The response body **is** the raw JWT, not a JSON wrapper `[FA-S42]` `[SPEC-9.0]` |
| Revoke | `DELETE /v1/tokens/refresh-token` — "Invalidate Refresh Token". Body is the plain-text refresh-token UUID; returns `204 No Content` `[FA-S42]` `[SPEC-9.0]` |
| Lifetimes | access token **1 hour**, refresh token **24 hours** `[C90-S27]` |

All three operations are confirmed present at spec tag `9.0.0.0` with exactly these paths and these summaries
`[SPEC-9.0]`.

**Caveat carried from the spec:** the SDDC Manager OpenAPI document declares **no `securitySchemes` at all**
(`components.securitySchemes == {}`) in 9.0, and no operation carries a `security` block `[SPEC-9.0]`. The
`Authorization: Bearer` header is therefore prose-sourced `[FA-S42]` `[FA-S43]`, not spec-sourced. Treat the
header as correct but note the spec offers no machine confirmation.

Not SSO-brokered — see P3.

### 1.2 vCenter / vSphere Automation REST API

| Field | Value |
|---|---|
| Base path | `https://{host}/api`, port 443; deprecated `/rest` base path still present in 9.0 and carries only operations that existed up to vSphere 7.0.2 `[VS-S8]`. Spec `servers[0].url` = `https://{host}/api` `[SPEC-9.0]` |
| Declared security schemes (spec) | `basic_auth` (HTTP `basic`); `api_key_auth` (apiKey, header **`vmware-api-session-id`**); `federated_identity_auth` (HTTP `bearer`, for vCenter federated with an external IdP) `[SPEC-9.0]` — identical to the prose security-schema page `[FA-S37]` |
| Session flow | Create a session with Basic credentials, then reuse the returned session id `[FA-S37]` |
| Token field | session id string, e.g. `b00db39f948d13ea1e59b4d6fce56389` `[FA-S37]` |
| Subsequent header | `vmware-api-session-id: <session-id>` `[FA-S37]` `[VS-S10]` |
| Session operations | `POST /api/session` (create), `GET /api/session` (inspect), `DELETE /api/session` (invalidate) — **spec-confirmed**: operations `/session` with operationIds `Cis.Session_create` / `Cis.Session_get` / `Cis.Session_delete`, under `servers[0].url` = `https://{host}/api` `[SPEC-9.0]`. Corroborated in prose by `[FA-S38]` |
| Error types | `Vapi Std Errors Unauthenticated`, `Vapi Std Errors ServiceUnavailable` `[VS-S11]` |

`[9.0+9.1]` — the three security schemes are verified independently in the 9.0 `[FA-S37]` and 9.1 `[FA-S36]`
security-schema pages and in both spec tags `[SPEC-9.0]`.

`[9.0+9.1]` — **the session path is spec-confirmed at both tags.** `GET|POST|DELETE /session` (operationIds
`Cis.Session_get` / `Cis.Session_create` / `Cis.Session_delete`) are present in both
`9.0__vsphere-automation.ops.json` and `9.1__vsphere-automation.ops.json`; with the spec's
`servers[0].url` = `https://{host}/api`, the callable path is **`POST /api/session`** `[SPEC-9.0]`. There is
**no** `/api/cis/session` operation in either spec. Some Broadcom prose pages print `/api/cis/session`
`[FA-S35]` `[VS-S10]` — that is a prose-vs-spec conflict, resolved in favour of the spec. See
`## Spec-vs-prose conflicts`, item 5.

`UNVERIFIED` — the exact `Authorization: Basic ...` header string on `POST /api/session` was not retrieved;
the SSO-credential walkthrough page returned HTTP 403 on repeated attempts `[VS-S19]`.

**Read P4 before using Basic credentials here.**

### 1.3 Virtual Infrastructure JSON API (`/sdk/vim25`)

| Field | Value |
|---|---|
| Base path | `https://{vcenter-host}/sdk/vim25/{release}` `[SPEC-9.0]` |
| Declared security scheme (spec) | `Session` — apiKey in header **`vmware-api-session-id`**, described as *"A session token, placed in the `vmware-api-session-id` HTTP header, returned by the `Login` operation of the `SessionManager` interface."* `[SPEC-9.0]` |
| Session reuse | A session established on the vSphere Web Services API (`/vim25`) can be reused on the vSphere Automation API (`/api`); both recognize `vmware-api-session-id`. Source is a Broadcom/VMware blog, **not product documentation** `[FA-S58]` |

### 1.4 NSX Manager — session cookie + XSRF

| Field | Value |
|---|---|
| Method + path | `POST /api/session/create` `[FA-S31]` |
| Payload | `application/x-www-form-urlencoded`: `j_username=<user>&j_password=<pass>` `[FA-S31]` |
| Token fields | Session cookie **`JSESSIONID`** plus response header **`x-xsrf-token`** `[FA-S31]` |
| Subsequent headers | **Both are required**: `Cookie: JSESSIONID=<id>` **and** `x-xsrf-token: <token>` `[FA-S31]` |
| Logout | `/api/session/destroy` (cookie + xsrf header) `[FA-S31]` |
| Session timeout | default **1800 seconds (30 minutes)** `[FA-S31]` |
| Path prefixes | `/policy/api/v1/*` and `/api/v1/*` `[FA-S31]` |
| Service accounts | **principal identities** (P6) `[FA-S30]` `[FA-S32]` |

`[9.0+9.1]` — **the session flow above is verified for 9.1 as well**, independently: the 9.1 session-cookie
page documents `POST /api/session/create` with `j_username`/`j_password`, `JSESSIONID` + `X-XSRF-TOKEN`,
`/api/session/destroy` and the **1800 s** default timeout `[NSX-S12]`, and the NSX 9.1.0 API Guide states the
same `[NSX-S18]`. Decisively, `POST /api/session/create` and `POST /api/session/destroy` are present as
`CreateAuthenticatedSession` / `DestroyAuthenticatedSession` in **all three** 9.1 NSX spec inventories —
`9.1__nsx-policy`, `9.1__nsx-manager` and `9.1__nsx-global-policy` `[SPEC-9.1-NSX]`.

**Spec evidence is absent for 9.0.** No NSX OpenAPI spec (`nsx-policy`, `nsx-manager`, `nsx-global-policy`)
exists at git tag `9.0.0.0` of `vmware/vcf-api-specs`; all three first appear at `9.1.0.0` `[SPEC-9.0]`. NSX 9.0
endpoint and auth facts are therefore **prose-doc evidence only**, not spec-grade. State that confidence level
when answering.

### 1.5 VCF Operations — `token/acquire`

| Field | Value |
|---|---|
| Method + path | `POST https://<host>/suite-api/api/auth/token/acquire` `[FA-S12]` `[SPEC-9.0]` |
| Payload | `{"username":"vRealize-user","password":"vRealize-dummy-password"}` `[FA-S12]` |
| Token field | `token`, format `<uuid>::<uuid>`; response also carries `expiresAt` and `validity` (ms) `[FA-S12]` |
| Subsequent header | `Authorization: OpsToken <token>`. Legacy `Authorization: vRealizeOpsToken <token>` *"continues to be supported"* `[FA-S12]` |
| Lifetime | *"expires after **six hours**"* `[FA-S12]` |
| Release | `POST /api/auth/token/release` — "Terminate the current sessionId" `[SPEC-9.0]` |
| Transport | clients and servers *"communicate over HTTPS"*; *"clients communicate with the server over HTTP, exchanging representations of VCF Operations objects"* `[FA-S9]` `[FA-S12]` |

`[9.0+9.1]` — the acquire endpoint, payload, token format and six-hour lifetime are identical text in both doc
sets `[FA-S12]` `[FA-S13]`; verified independently.

Spec base path is `/suite-api`, so declared operation paths are relative: `/api/auth/token/acquire` under
`/suite-api` `[SPEC-9.0]`.

**Not available in 9.0:** `POST /api/auth/token/exchange`. That operation is absent from the `9.0.0.0` spec and
present in `9.1.0.0` `[SPEC-9.0]`. Do not offer JWT exchange as a 9.0 route.

**Also not available in 9.0:** `Authorization: Bearer <VCF SSO access token>` against the VCF Operations API.
The 9.0 doc page describes only `OpsToken` / `vRealizeOpsToken` `[FA-S12]`; the Bearer scheme is documented in
the 9.1 API reference `[FA-S44]`.

### 1.6 VCF Operations — roles and privileges API `[9.0+9.1]`

The full `/auth/*` role and privilege surface is present at spec tag `9.0.0.0`, not just 9.1 `[SPEC-9.0]`:

`GET|POST|PUT /api/auth/roles`, `GET|DELETE /api/auth/roles/{roleName}`,
`GET|POST|PUT|DELETE /api/auth/roles/{roleName}/privileges`, `GET /api/auth/privileges`,
`GET /api/auth/privilegegroups`, `GET /api/auth/currentuser/roles/{roleName}/privileges`,
`DELETE /api/auth/users/{userId}/permissions/{roleName}`,
`DELETE /api/auth/usergroups/{groupId}/permissions/{roleName}` — 57 `/auth/*` operations total at 9.0 `[SPEC-9.0]`.

This **corrects the prose dossier**, which tagged the `/auth/*` role surface `[9.1]` on the strength of the 9.1
API reference `[FA-S45]`. See `## Spec-vs-prose conflicts`, item 2.

### 1.7 VCF Operations for Logs `[9.0 only]`

| Field | Value |
|---|---|
| Base path | `/api/v2` `[SPEC-9.0]` |
| Session create | `POST /sessions`; also `GET /sessions/current` `[SPEC-9.0]` |
| Declared security scheme (spec) | `Bearer` — HTTP, scheme `Bearer`, header `Authorization`. Verbatim description: *"Authenticated requests must include an Authorization header with a session ID that was retrieved from `/api/v2/sessions`. The session ID has a limited lifespan. Access is allowed only to resources that the user is authorized to use."* `[SPEC-9.0]` |
| Operation count | 136 `[SPEC-9.0]` |

**This spec is removed in 9.1** and superseded by a differently-named, differently-authenticated
`log-management` spec `[SPEC-9.1]`. Do not carry `/api/v2/sessions` forward.

### 1.8 VCF Operations for Networks

| Field | Value |
|---|---|
| Base path | `/api/ni` `[SPEC-9.0]` |
| Declared security scheme (spec) | `ApiKeyAuth` — apiKey in header `Authorization`, described as `API Key - NetworkInsight {token}` `[SPEC-9.0]` |
| Operation count | 632 `[SPEC-9.0]` |

Only the one scheme is declared in 9.0. The bearer/OpsToken scheme is a 9.1 addition `[SPEC-9.1]`.

### 1.9 VCF Operations Fleet Management API

| Field | Value |
|---|---|
| Auth | **HTTP Basic.** No token endpoint is documented `[FA-S47]` |
| Credential construction | `echo -n 'admin@local:<fleet-admin-password>' \| base64`, run on the Fleet Management appliance `[FA-S47]` |
| Header | `Authorization: Basic <base64>` — *"The word Basic must be present before the Base64 value"* `[FA-S47]` |
| Evidence quality | Broadcom **KB article 409715**, not product documentation. The KB itself states that paths, payloads and token lifetime are not documented `[FA-S47]` |

`UNVERIFIED` — endpoint paths, payload shapes and credential lifetime for this API `[FA-S47]`.

### 1.10 VCF Automation — VM Apps tenant

| Field | Value |
|---|---|
| Method + path | `POST https://{{vcfaHostname}}/tm/oauth/tenant/{{vcfaTenant}}/token` `[FA-S15]` |
| Headers | `Content-Type: application/x-www-form-urlencoded`, `Accept: application/json` `[FA-S15]` |
| Body | `grant_type=refresh_token`, `refresh_token={{vcfaAPIToken}}` `[FA-S15]` |
| Token field | **`UNVERIFIED`.** The docs say *"The response returns the access token"* but **do not name the JSON field** `[FA-S15]` |
| Subsequent header | **`UNVERIFIED`.** The docs say *"an HTTP authentication token in the `Authorization` request header"*; the exact format is not stated `[FA-S14]` |
| Lifetimes | API token (refresh token) default **129600 minutes / 90 days**; access token default **one hour** `[FA-S14]` `[FA-S15]` |

OAuth2 convention would suggest `access_token` and `Bearer`, but **that is not documented** — verify
empirically before hard-coding `[FA-gap4]`.

### 1.11 vSAN and vSAN Data Protection

- **vSAN has no independent authentication.** vSAN Management APIs *"depend on the vSphere Web Services API for
  login procedures"* — authenticate to vCenter and reuse that session `[FA-S68]`.
- **vSAN Data Protection (Snapshot Appliance API)**, base `https://{host}/api`, declares the same three schemes
  as vSphere Automation: `basic_auth`, `api_key_auth` (header `vmware-api-session-id`),
  `federated_identity_auth` (bearer) `[SPEC-9.0]`. 48 operations at 9.0 `[SPEC-9.0]`.
- Session reuse across `/vim25` and `/api` is corroborated only by a Broadcom/VMware blog, not product docs
  `[FA-S58]` `[FA-gap13]`.

### 1.12 VCF Installer

The VCF Installer OpenAPI spec at tag `9.0.0.0` declares **no `securitySchemes`** (`{}`), 52 operations, spec
placeholder base `http://localhost:80` `[SPEC-9.0]`. `UNVERIFIED` — no authentication method for the VCF
Installer API is established by either the spec or any fetched 9.0 prose page.

### 1.13 Supervisor / VKS

| Field | Value |
|---|---|
| Login command | `vcf context create <context_name> --endpoint=<SUPERVISOR_ENDPOINT> --type=k8s --username=<user_name>` `[FA-S33]` |
| Documented form | `vcf context create --endpoint <SUPERVISOR-ADDRESS> --username <VCENTER-SSO-USER> --ca-certificate <PATH-TO-CERTIFICATE-FILE>` `[TL-S24]` |
| Credentials | entered interactively, **or** via environment variable `VCF_CLI_VSPHERE_PASSWORD` `[TL-S24]` |
| Result | writes a kubeconfig context (`.kube/config`); subsequent auth is kubeconfig-managed bearer token `[FA-S33]` `[FA-S63]` |
| Context management | `vcf context list`, `vcf context use <context-name>` `[TL-S24]` |
| CA pinning | `--ca-certificate` is the documented API-client path for pinning a private/self-signed CA `[FA-S34]` |

`[9.0+9.1]` — the login flow text is identical in both doc sets `[FA-S33]` `[FA-S34]` `[TL-S24]` `[TL-S25]`.

**Trap:** the login step is **`vcf`, not `kubectl vsphere`**. In VCF 9.x documentation the CLI package contains
only `vcf-cli-{os}_{arch}`; no `kubectl` or `kubectl-vsphere` binary is mentioned `[TL-S30]` `[TL-S31]`. Whether
the legacy `kubectl-vsphere` plugin still ships for backward compatibility is `UNVERIFIED` — teach
`vcf context create`, do not assert the plugin is gone `[TL-gap3]`.

Authorization concepts: *"Authentication controls who can access the vSphere environment and authorization
controls what resources the users can access."* Roles are *"sets of privileges"*; permissions are granted by
*"associating a role to a user or group on that object"* in the vCenter hierarchy. vCenter SSO is *"an
authentication broker and security token exchange infrastructure"* that *"issues a token when a principal …
authenticates"* `[FA-S33]`.
`UNVERIFIED` — named Supervisor namespace roles (owner/edit/view) were not confirmed on the fetched 9.0 page
`[FA-gap11]`.

---

## 2. Token lifetimes and refresh `[9.0]`

| Product | Credential | Lifetime | Refresh mechanism | Source |
|---|---|---|---|---|
| SDDC Manager | access token (JWT) | **1 hour** | `PATCH /v1/tokens/access-token/refresh` with plain-text refresh UUID; response body is the raw JWT | `[C90-S27]` `[FA-S42]` |
| SDDC Manager | refresh token (UUID) | **24 hours** | re-authenticate via `POST /v1/tokens`; revoke early with `DELETE /v1/tokens/refresh-token` | `[C90-S27]` `[FA-S42]` |
| VCF Operations | `token` (`<uuid>::<uuid>`) | **6 hours**; response carries `expiresAt` and `validity` (ms) | re-acquire via `POST /suite-api/api/auth/token/acquire`; release via `/api/auth/token/release` | `[FA-S12]` `[SPEC-9.0]` |
| NSX Manager | `JSESSIONID` session | **1800 s (30 min)** default | re-create via `POST /api/session/create` | `[FA-S31]` |
| VCF Automation VM Apps | API token (refresh token) | **129600 min / 90 days** default | reissue in VCF Automation | `[FA-S14]` |
| VCF Automation VM Apps | access token | **1 hour** default | `grant_type=refresh_token` against `/tm/oauth/tenant/{t}/token` | `[FA-S14]` `[FA-S15]` |
| VCF Operations for Logs | session id | *"limited lifespan"* — value not stated | re-create via `POST /api/v2/sessions` | `[SPEC-9.0]` |
| vCenter | `vmware-api-session-id` | **`UNVERIFIED`** — no lifetime retrieved | `DELETE /api/session` then re-create (`Cis.Session_delete`, spec-confirmed) | `[SPEC-9.0]` `[VS-S11]` |
| Fleet Management API | HTTP Basic (no token) | n/a | n/a — KB states lifetime is undocumented | `[FA-S47]` |

**There are no fleet-level token TTL controls in 9.0.** API Token TTL, Access Token TTL, expired-token
retention and the JIT-user inactivity behavior are 9.1 IAM settings `[FA-S11]` `[FA-S52]`; none of them has a
9.0 equivalent `[FA-S53]` `[SPEC-9.0]`.

---

## 3. Identity / SSO architecture `[9.0]`

- A unified identity broker exists in 9.0. It is the **VCF Identity Broker**, configured through the VCF
  Operations console `[FA-S18]`. `[9.0+9.1]` — verified independently in the 9.1 doc set `[FA-S24]`.
- **Federated components** `[FA-S18]`: vCenter, VCF Operations, VCF Automation, log management (VCF Operations
  for Logs), VCF Operations for Networks, VCF Operations orchestrator, VCF Operations HCX, NSX.
- **Excluded from SSO**: SDDC Manager and ESX `[FA-S18]`. See P3.
- **Deployment modes**: **embedded** (inside the management-domain vCenter) or **standalone appliance**. In 9.0
  the appliance is described as a **three-node cluster supporting up to five connected VCF Instances**
  `[FA-S19]`.
- **Supported IdPs** `[FA-S23]`: Okta, Ping Identity, Microsoft Entra ID, Microsoft AD FS, *"Any SAML 2.0
  Identity Providers"*, AD/LDAP, OpenLDAP.
- **Protocols** `[FA-S23]`: **SAML 2.0** and **OIDC** for authentication; **SCIM 2.0, JIT, AD/LDAP** for
  user/group provisioning.
- **vCenter-level IdP support** `[VS-S9]`: vCenter SSO (default), AD FS (7.0+), Okta (8.0 U1+), Azure AD
  (8.0 U2+).
- **Removed in vCenter 9.0**: Integrated Windows Authentication (IWA); SSPI, smart card and RSA SecurID
  `[VS-S5]` `[C90-S10]`. Replacement guidance is AD over LDAPS, or Identity Federation with MFA `[C90-S10]`.

### 9.0 SSO configuration order `[FA-S54]`

1. Select a VCF Instance → 2. Choose deployment mode → 3. Select and configure the identity provider →
4. Configure VCF SSO for **NSX and vCenter** → 5. Configure VCF SSO for **VCF Operations and VCF Automation** →
6. (Optional) other components (HCX, networks, orchestrator, logs) → 7. **Assign required roles and permissions
for users or groups** — step 7 is performed *in the individual components*, not centrally.

### Not present in 9.0

- No API client / API token / OAuth-app / emergency-client management (P2) `[FA-S53]` `[SPEC-9.0]`.
- No formalised SSO topology models. The Fleet-Wide / Cross VCF Instance / Single VCF Instance models and the
  *"split-SSO configurations … are not supported"* constraint are documented in the **9.1** design library
  `[FA-S56]`; the 9.0 equivalent design-library page returned 404 `[FA-gap]`.
- No vIDM → identity-broker migration workflow; that is a 9.1 page `[FA-S25]`.

### Unretrievable

`UNVERIFIED — could not retrieve`: the broker↔component **trust mechanism**, the **token flow internals**, and
the broker's **listening ports**. The 9.0 `sso-architecture.html` page is a navigation stub that states only
that one or more identity brokers may be deployed across instances, and defers to the design library
`[FA-S65]`.

### VMware Identity Broker token endpoint — 9.0 status

The `POST /acs/t/{tenant}/token` endpoint is documented in an API reference titled *"VMware Identity Broker -
vCenter Server"* that is **version-tagged 9.1** `[FA-S39]` `[FA-S40]`. Whether the identical endpoint exists and
behaves the same in 9.0 is **`UNVERIFIED`**; the absence of any API-token feature from the 9.0 doc set
`[FA-S53]` suggests it may not be exposed for customer use in 9.0 `[FA-gap14]`. **Do not present it as a 9.0
route.**

---

## 4. Roles and permissions `[9.0]`

### VCF-level built-in roles

**Not documented for 9.0.** See P5. No built-in-roles page exists in the 9.0 fleet-management tree `[FA-S53]`.
Authorization is assigned per component (step 7 of the SSO configuration order, `[FA-S54]`).

### NSX roles `[FA-S32]`

15 built-in roles. **Enterprise Admin (EA)** = *"Full access (FA) — All permissions including Create, Read,
Update, and Delete (CRUD)"*. **Auditor (A)** = read-only. The remaining thirteen: Network Admin, Network
Operator, Security Admin, Security Operator, Cloud Admin, Cloud Operator, Cloud Partner Admin, Load Balancer
Admin, Load Balancer Operator, VPN Admin, Guest Introspection Partner Admin, Network Introspection Partner
Admin, Support Bundle Collector. Custom roles are supported. **Principal identities** are the documented
service-account mechanism `[FA-S30]` `[FA-S32]`.

### VCF Operations roles `[9.0+9.1]`

Managed through the Auth API — see §1.6 for the full endpoint list confirmed present at spec tag `9.0.0.0`
`[SPEC-9.0]`. Named roles referenced elsewhere in the corpus: **Administrator**, **ReadOnly** `[FA-S20]`
`[FA-S45]` (the mapping page that names them is 9.1; the endpoints themselves are 9.0+9.1).

### vCenter / Supervisor `[FA-S33]`

Roles are *"sets of privileges"*; permissions are granted by *"associating a role to a user or group on that
object"* in the vCenter hierarchy. vCenter 9.0 additionally ships **vCenter Authorization Management** — *"modern
REST APIs to configure all aspects of authorization … including privileges, roles"* `[C90-S25]` `[VS-S6]`.
`UNVERIFIED` — namespace role names (owner/edit/view) `[FA-gap11]`.
Pinniped Supervisor/Concierge integration for external IdPs is documented on the **9.1** page `[FA-S34]`, not
the 9.0 page.

### VCF Automation provider/org roles

The rights/roles/rights-bundles model (provider roles, global roles, organization-specific roles, Simple vs
Advanced Rights Bundle Mode, System Administrator scope) is documented on a **9.1** page `[FA-S50]`. For 9.0 the
retrieved evidence is limited to identity-integration levels — LDAP at system *or* organization level, SAML at
organization level, OIDC integration `[FA-S49]` `[FA-S5]`. Do not restate the 9.1 role taxonomy as 9.0.

---

## 5. Certificate handling and TLS-trust pitfalls `[9.0]`

### What the docs state `[FA-S21]`

- At deployment *"each component is assigned a certificate from a default signing Certificate Authority (VMware
  Certificate Authority CA)"*.
- *"You should replace the default certificates for the management domain components with trusted enterprise
  CA-signed certificates to provide secure access."*
- Supported CA types: **VMCA, Microsoft Certificate Authority, OpenSSL, self-signed**.
- Managed from the **VCF Operations console**: view certificates and alerts, configure a CA, set up automatic
  renewal, manually renew, generate CSRs, replace with CA-signed, replace with an external CA cert.
- Non-disruptive updates / auto-renewal cover **ESXi, vCenter, NSX Manager, SDDC Manager** and VCF services.
- Replace when: expiry is imminent or passed, the issuing CA revoked them, or (optionally) on new workload
  domain creation.

**9.0 certificate operations are single-certificate operations.** Bulk CSR/renew/import/replace is a 9.1
addition `[FA-S22]`. The 9.0 certificate coverage list is flat (ESXi, vCenter, NSX Manager, SDDC Manager, VCF
services); the split into *VCF Management* and *VCF Instance/Domain* tiers is 9.1 `[FA-S21]` vs `[FA-S22]`.

### Spec-visible certificate surface `[SPEC-9.0]`

The `vcf-operations` spec at tag `9.0.0.0` exposes **5** certificate operations:
`GET|POST|DELETE /api/certificate`, `POST /api/applications/clientCertificate/{collectorId}`,
`GET /api/applications/clientCertificate/{collectorIpOrGroupName}`. The 9.1 spec exposes **24**, including the
entire `/api/fleet-management/certificate-management/**` family `[SPEC-9.1]` — none of which is callable on 9.0.

### Pitfalls for an API client

1. **Default state is VMCA-signed, i.e. not publicly trusted.** A stock client fails hostname/chain validation
   against vCenter, NSX, SDDC Manager and VCF Operations until the VMCA root (or enterprise CA) is added to the
   client trust store `[FA-S21]`.
2. **The documented remedy is to replace the certificates, not to disable verification** `[FA-S21]`. No fetched
   Broadcom page documents disabling TLS verification as a supported practice. The only insecure-flag usage in
   official docs is inside NSX's own `curl` examples, which use `-k`:
   `curl -i -k -c session.txt -X POST -d 'j_username=… ' https://<nsx-manager>/api/session/create` `[FA-S31]`.
   Treat `-k` as example-only, not guidance.
3. **`--ca-certificate` is the documented client-side pinning path** for Supervisor/VKS
   (`vcf context create … --ca-certificate <file>`) `[FA-S34]` `[TL-S24]`.
4. **Certificate rotation is a trust-bundle reload event.** Auto-renewal touches ESX, vCenter, NSX Manager and
   SDDC Manager `[FA-S21]`, so long-lived clients must reload their trust store. *Inference from the cited
   component list; the docs do not state token impact.*
5. **In 9.0 there is no single broker certificate that can break every client at once.** The identity broker is
   brought under VCF certificate management in **9.1** `[FA-S22]`; in 9.0 auth is per-product, so a certificate
   failure is scoped to one component. *Inference from the 9.0-vs-9.1 coverage lists.*
6. **PEM-only CA import** into VCF Operations Trusted Certificates is documented on the **9.1** page
   `[FA-S57]`; the equivalent 9.0 statement was not retrieved. Do not assert PEM-only for 9.0.
7. `UNVERIFIED — trust store location`: no page states which OS/JVM trust store is modified by an imported CA
   `[FA-S57]` `[FA-gap15]`.

---

## 6. Network reachability `[9.0]`

### Honest statement of the gap

**The per-service inbound port matrix could not be retrieved.** Both the 9.0 and 9.1 Planning and Preparation
pages direct readers to the **VMware Ports and Protocols tool at `https://ports.broadcom.com/`**, described as
*"a portal that enables you to view all the ports needed by various VMware products, solutions, and services in
a single pane"*. The tool renders client-side and **exposes no static port table to fetch**; product coverage
for VCF 9.0/9.1 could not be confirmed `[FA-S28]` `[FA-S29]` `[FA-S64]`.
→ `UNVERIFIED — could not retrieve` for inbound ports on vCenter, NSX, SDDC Manager, VCF Operations, the
identity broker and Supervisor. Do not invent a port table. Direct the user to `https://ports.broadcom.com/`.

### What is verified

- **All documented VCF API traffic is HTTPS.** The vSphere Automation API is on **port 443** at the **`/api`**
  base path; a subset (appliance configuration and lifecycle) is also on **port 5480** `[VS-S8]`.
- The deprecated `/rest` base path still exists in 9.0 and carries only operations that existed up to vSphere
  7.0.2. *"The `/api` base path will remain the only active base path when the `/rest` base path is removed in a
  future vSphere release."* `[VS-S8]`
- vSphere Automation, NSX, SDDC Manager and Identity Broker references all specify the `https://` scheme in
  their endpoint examples `[FA-S31]` `[FA-S40]` `[FA-S42]` `[FA-S35]`.
- VCF Operations clients and servers *"communicate over HTTPS"* `[FA-S9]` `[FA-S12]`.

### Path prefixes an API client hits (reachability targets on 443)

| Prefix | Product | Source |
|---|---|---|
| `/v1/*` | SDDC Manager | `[FA-S42]` `[SPEC-9.0]` |
| `/suite-api/api/*` | VCF Operations | `[FA-S12]` `[SPEC-9.0]` |
| `/api/session/*`, `/policy/api/v1/*`, `/api/v1/*` | NSX Manager | `[FA-S31]` |
| `/api/*` | vCenter (vSphere Automation) | `[VS-S8]` `[SPEC-9.0]` |
| `/sdk/vim25/{release}` | vCenter (VI JSON) | `[SPEC-9.0]` |
| `/api/v2/*` | VCF Operations for Logs | `[SPEC-9.0]` |
| `/api/ni/*` | VCF Operations for Networks | `[SPEC-9.0]` |
| `/tm/oauth/tenant/{tenant}/token` | VCF Automation VM Apps | `[FA-S15]` |

### Outbound

`UNVERIFIED — 9.0 public URL list.` The 9.0 page
`/9-0/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html` returned **404**
`[FA-retrieval-failures]`. An 8-URL outbound allow-list (all HTTPS/443) is documented for **9.1** `[FA-S26]`;
it is **not** reproduced here because it could not be confirmed for 9.0. Do not copy the 9.1 list into a 9.0
answer.

### DNS

The explicit FQDN/DNS requirement text was retrieved from the **9.1** planning page `[FA-S27]`. For 9.0, treat
"resolve by FQDN, not IP, because certificates are issued to FQDNs" as an operational consequence of `[FA-S21]`,
flagged as inference.

---

## 7. Spec-vs-prose conflicts and how they were resolved

1. **SDDC Manager declares no `securitySchemes`.** The 9.0 spec has `components.securitySchemes == {}` and no
   per-operation `security` block `[SPEC-9.0]`, while the prose reference documents `Authorization: Bearer
   <accessToken>` `[FA-S42]` `[FA-S43]`. **Not a contradiction — the spec is silent, not negative.** Resolution:
   use the prose header; record that the spec offers no machine confirmation. The same silence exists in 9.1.
2. **VCF Operations `/auth/roles` family: prose said 9.1, spec says both.** The prose dossier tagged the
   `/auth/*` role and privilege surface `[9.1]` because it was read off the 9.1 API reference `[FA-S45]`. The
   spec shows those operations present at tag `9.0.0.0` (57 `/auth/*` operations) `[SPEC-9.0]`. **Resolved in
   favour of the spec: role/privilege management is 9.0+9.1.** Only `POST /api/auth/token/exchange` is genuinely
   9.1-new.
3. **VCF Operations declares one generic scheme, not two.** The spec declares exactly one scheme in both
   versions — `Token-based-authorization`, an `apiKey` in the `Authorization` header `[SPEC-9.0]` `[SPEC-9.1]`.
   The prose reference for 9.1 documents two header forms, `OpsToken` and `Bearer` `[FA-S44]`. **Resolution: the
   spec's single scheme is a format-agnostic placeholder for "something in the `Authorization` header" and
   cannot distinguish token formats; it neither confirms nor refutes the prose.** For 9.0 the prose is
   unambiguous — `OpsToken` (legacy `vRealizeOpsToken`) only `[FA-S12]`.
4. **NSX has no 9.0 spec at all.** All three NSX specs first appear at tag `9.1.0.0` `[SPEC-9.0]` `[SPEC-9.1]`.
   NSX 9.0 auth is prose-only `[FA-S31]`. State that confidence level explicitly when answering for 9.0.
5. **The vCenter session path: prose says `/api/cis/session`, the spec says `/api/session`. Resolved in favour
   of the spec.** `GET|POST|DELETE /session` are present as operations with operationIds `Cis.Session_get` /
   `Cis.Session_create` / `Cis.Session_delete` in the `vsphere-automation` spec at **both** tags `9.0.0.0` and
   `9.1.0.0`, and `servers[0].url` is `https://{host}/api` — so the callable path is **`POST /api/session`**
   `[SPEC-9.0]`. The string `/api/cis/session` appears **nowhere** in either spec. Some Broadcom prose pages
   nonetheless print `/api/cis/session` `[FA-S35]` `[VS-S10]`, while the `cis-session` reference page prints
   `/session` `[FA-S38]`. **Resolution: use `/api/session`.** The observation that prose disagrees is recorded,
   not deleted — if a deployment rejects `/api/session`, the prose variant is the fallback to test
   `[FA-gap1]`. The header (`vmware-api-session-id`) was never ambiguous.
6. **Spec `base_path` placeholders.** `sddc-manager` and `vcf-installer` declare `http://localhost:80`
   `[SPEC-9.0]`. This is a spec artifact. The callable base is `https://<fqdn>/v1/...` `[C90-S29]`.

---

## 8. Consolidated `UNVERIFIED` list for 9.0

| Item | Status | Source |
|---|---|---|
| Per-service inbound port matrix | could not retrieve — ports.broadcom.com is a client-rendered tool | `[FA-S28]` `[FA-S29]` `[FA-S64]` |
| 9.0 outbound public-URL allow-list | page returned 404 | `[FA-retrieval-failures]` |
| VCF SSO architecture internals (token flow, trust establishment, broker ports) | 9.0 page is a navigation stub | `[FA-S65]` |
| Identity Broker `/acs/t/{tenant}/token` existence in 9.0 | reference is version-tagged 9.1 only | `[FA-S39]` `[FA-S40]` `[FA-gap14]` |
| VCF Automation VM Apps response token field name | docs say only "the access token" | `[FA-S15]` `[FA-gap4]` |
| VCF Automation VM Apps `Authorization` header format | docs do not state it | `[FA-S14]` `[FA-gap4]` |
| Fleet Management API paths, payloads, credential lifetime | KB states they are undocumented | `[FA-S47]` |
| VCF Installer API authentication method | spec declares no schemes; no prose retrieved | `[SPEC-9.0]` |
| `Authorization: Basic ...` header string on vCenter session create | page returned HTTP 403 | `[VS-S19]` |
| vCenter session id lifetime | not retrieved | `[VS-S10]` `[VS-S11]` |
| Supervisor namespace role names (owner/edit/view) | not confirmed on the 9.0 page | `[FA-gap11]` |
| Trusted-certificate store location for imported CAs | not stated | `[FA-S57]` `[FA-gap15]` |
| vSAN session-reuse mechanism | corroborated only by a blog, not product docs | `[FA-S58]` `[FA-gap13]` |
| Whether P4 (blocked non-federated logins) persists in 9.1 | no 9.1 page retrieved | `[VS-S5]` |

---

## Source Index

All sources accessed **2026-07-31**. `TECHDOCS` = `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.

### `FA-*` — research/foundation-auth-identity.md

| Ref | URL |
|---|---|
| FA-S5 | `TECHDOCS/9-0/organization-management.html` |
| FA-S9 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api.html` |
| FA-S11 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/managing-api-tokens.html` |
| FA-S12 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html` |
| FA-S13 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html` |
| FA-S14 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token.html` |
| FA-S15 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token/get-your-access-token-for-vra-8-x.html` |
| FA-S18 | `TECHDOCS/9-0/fleet-management/what-is.html` |
| FA-S19 | `TECHDOCS/9-0/fleet-management/what-is/deployment-models-for-sso.html` |
| FA-S20 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/vcf-built-in-roles.html` |
| FA-S21 | `TECHDOCS/9-0/fleet-management/certificate-management-9-0.html` |
| FA-S22 | `TECHDOCS/9-1/fleet-management/certificate-management-9-0.html` |
| FA-S23 | `TECHDOCS/9-0/fleet-management/what-is/protocols-suported-for--sso.html` |
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
| FA-S42 | `https://developer.broadcom.com/xapis/sddc-manager-api/9.0/tokens/` |
| FA-S43 | `https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/tokens/` (VCF API 5.2.4 — corroboration only, pre-9.x) |
| FA-S44 | `https://developer.broadcom.com/xapis/vcf-operations-api/latest/` (9.1) |
| FA-S45 | `https://developer.broadcom.com/xapis/vcf-operations-api/latest/auth/` (9.1) |
| FA-S47 | `https://knowledge.broadcom.com/external/article/409715/how-to-authorize-vcf-operations-fleet-ma.html` |
| FA-S49 | `TECHDOCS/9-0/provider-management.html` |
| FA-S50 | `TECHDOCS/9-1/provider-management/managing-system-administrators-and-roles/managing-rights-and-roles.html` |
| FA-S51 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens.html` |
| FA-S52 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/view-and-manage-token-lifecycle-and-security.html` |
| FA-S53 | `TECHDOCS/9-0/fleet-management/what-is/managing-vmware-cloud-foundation-operations-sso.html` |
| FA-S54 | `TECHDOCS/9-0/fleet-management/what-is/setting-up-sso.html` |
| FA-S56 | `TECHDOCS/9-1/design/design-library/single-sign-on-models.html` |
| FA-S57 | `TECHDOCS/9-1/fleet-management/certificate-management-9-0/managing-certificates-in-vmware-vsphere-foundation/certificates/importing-ca-certificates.html` |
| FA-S58 | `https://blogs.vmware.com/cloud-foundation/2025/11/19/unified-authentication-in-vmware-cloud-foundation-sdk-9-0-seamless-authentication-across-vsphere-and-vsan-apis/` |
| FA-S63 | `TECHDOCS/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-a-tkg-service-cluster-as-a-vcenter-single-sign-on-user-with-kubectl.html` |
| FA-S64 | `https://ports.broadcom.com/` |
| FA-S65 | `TECHDOCS/9-0/fleet-management/what-is/sso-architecture.html` |
| FA-S68 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/using-the-vsan-management-sdks.html` |
| FA-retrieval-failures | 404: `TECHDOCS/9-0/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html`; 404: `TECHDOCS/9-0/fleet-management/what-is/points-to-consider-and-prerequisites-while-configuring-vcf-sso.html`; 404: `TECHDOCS/9-0/design/design-library/single-sign-on-models/-fleet.html`; 403: `TECHDOCS/9-0/deployment/.../installing-vcf-identity-broker.html` |
| FA-gap1/4/11/13/14/15, FA-gap3 | `research/foundation-auth-identity.md`, `## Gaps and Ambiguities`, items 1, 4, 11, 13, 14, 15 and 3 |

### `NSX-*` — research/nsx.md

| Ref | URL |
|---|---|
| NSX-S12 | `TECHDOCS/9-1/advanced-network-management/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html` (**9.1 child page — retrieved successfully**; the HTTP 429 was on the parent index page) |
| NSX-S18 | `https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html` (NSX 9.1.0.0 API Guide — basic / session / X.509 principal-identity / VMC auth) |

### `TL-*` — research/tooling-powercli-vks-sdk.md

| Ref | URL |
|---|---|
| TL-S05 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382` |
| TL-S06 | `https://www.powershellgallery.com/packages/VCF.PowerCLI` |
| TL-S08 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S24 | `TECHDOCS/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html` |
| TL-S25 | `TECHDOCS/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html` |
| TL-S30 | `TECHDOCS/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/download-and-install-the-kubernetes-cli-tools-for-vsphere.html` |
| TL-S31 | `TECHDOCS/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/download-and-install-the-kubernetes-cli-tools-for-vsphere.html` |
| TL-gap3 | `research/tooling-powercli-vks-sdk.md`, `## Gaps and Ambiguities`, item 3 |

### `C90-*` — research/vcf-core-9.0.md

| Ref | URL |
|---|---|
| C90-S2 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes.html` |
| C90-S10 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes.html` |
| C90-S25 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html` |
| C90-S27 | `https://developer.broadcom.com/xapis/sddc-manager-api/9.0/` (Bearer auth; 1 h / 24 h token lifetimes) |
| C90-S29 | `https://developer.broadcom.com/xapis/sddc-manager-api/9.0/domains/` (example base `https://sfo-vcf01.rainpole.io/v1`) |

### `C91-*` — research/vcf-core-9.1-and-deltas.md

| Ref | URL |
|---|---|
| C91-S2 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes.html` |

### `VS-*` — research/vsphere-vcenter-vsan.md

| Ref | URL |
|---|---|
| VS-S5 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-vsphere.html` (blocked non-federated username/password logins) |
| VS-S6 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html` |
| VS-S8 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/understanding-the-vsphere-automation-rest-api.html` |
| VS-S9 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms.html` (auth-mechanisms page is common to both doc sets; the 9.1 copy was the one fetched) |
| VS-S10 | `https://developer.broadcom.com/xapis/vsphere-automation-api/latest/` |
| VS-S11 | `https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/` and `.../cis/cis-session/` |
| VS-S19 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms/authenticate-to-vcenter-server-with-vcenter-single-sign-on-credentials.html` — **HTTP 403, content not retrieved** |

### `SPEC-9.0` — machine-extracted OpenAPI inventory

`research/spec-inventory/index.json` and `research/spec-inventory/DELTA-9.0-to-9.1.md`, derived by diffing git
tags `9.0.0.0` and `9.1.0.0` of `https://github.com/vmware/vcf-api-specs` (cloned 2026-07-31). Per-product
operation dumps live in `research/spec-inventory/9.0__<product>.ops.json`.

`[SPEC-9.1-NSX]` — `research/spec-inventory/9.1__nsx-policy.ops.json`,
`research/spec-inventory/9.1__nsx-manager.ops.json`, `research/spec-inventory/9.1__nsx-global-policy.ops.json`
(`CreateAuthenticatedSession` / `DestroyAuthenticatedSession` present in all three).

---

*This reference was built from documentation and machine-extracted API specifications. It has not been
validated against a live VCF 9.0 environment.*
