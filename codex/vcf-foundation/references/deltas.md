# VCF 9.0 → 9.1 — Foundation Layer Change List

Explicit, itemised deltas for the **foundation layer only**: authentication, identity/SSO, roles, certificates,
reachability, and the tooling that consumes them. Anything not listed here was either verified unchanged (marked
so) or was not retrievable (marked `UNVERIFIED`).

Evidence classes:
- **Prose** — Broadcom TechDocs / developer portal, refs resolved in `## Source Index`.
- **Spec** — `securitySchemes` and operation lists diffed between git tags `9.0.0.0` and `9.1.0.0` of
  `github.com/vmware/vcf-api-specs`, cited `[SPEC]`. Spec evidence outranks prose; conflicts are called out in
  the Notes column.

---

## Contents

- [1. The traps — read these first](#1-the-traps--read-these-first) (T1–T10)
- [2. Identity and SSO](#2-identity-and-sso)
- [3. API clients, tokens and IAM settings](#3-api-clients-tokens-and-iam-settings)
- [4. Per-product authentication](#4-per-product-authentication) — plus Note A (Ops `Bearer` scheme),
  Note B (Ops role API version tag), Note C (SDDC Manager 9.1 paths), **Note D (vCenter session path — no
  delta; a previously listed delta was withdrawn)**
- [5. Roles and permissions](#5-roles-and-permissions)
- [6. Certificates](#6-certificates)
- [7. Network reachability](#7-network-reachability)
- [8. Tooling (PowerCLI, SDKs, CLI)](#8-tooling-powercli-sdks-cli)
- [9. Items verified as UNCHANGED between 9.0 and 9.1](#9-items-verified-as-unchanged-between-90-and-91)
- [Source Index](#source-index)

---

## 1. The traps — read these first

| # | Trap | Why it bites |
|---|---|---|
| T1 | **API clients and SSO-issued API tokens are 9.1-only.** | A 9.0 user pointed at *Fleet Management → Identity & Access → API Clients* will not find the node. The 9.0 `vcf-operations` spec has **0** `/api/fleet-management/iam/**` operations; 9.1 has **70** `[SPEC]` `[FA-S53]` `[FA-S51]`. |
| T2 | **OAuth clients are NOT migrated on the vIDM → identity-broker migration.** | Verbatim: *"OAuth clients are not migrated automatically. You must manually regenerate the client and secret using identity broker and configure accordingly."* Any 9.0-era OAuth client **breaks on upgrade** `[FA-S25]`. Rotate/recreate via `POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps` and `.../oauth-apps/{oauthAppId}/rotate` `[SPEC]`. |
| T3 | **VCF Operations gains `Bearer` alongside `OpsToken` in 9.1.** | 9.0 accepts `Authorization: OpsToken <t>` (legacy `vRealizeOpsToken`) only `[FA-S12]`. 9.1 also accepts `Authorization: Bearer <t>` where the token is *"an access token from VCF SSO"*; missing/expired/invalid → `401` `[FA-S44]`. Sending Bearer to a 9.0 appliance is undocumented. |
| T4 | **PowerCLI gains `VcfOAuthSecurityContext` and `VcfApiToken` in 9.1.** | Neither parameter exists in `{PCLI 9.0.0}` `[TL-S05]` `[TL-S08]`. **Which cmdlets expose them is `UNVERIFIED`** — the changelog gives counts, not names `[TL-S09]`. See `powercli-session.md`. |
| T5 | **The identity broker comes under VCF certificate management in 9.1 — a single TLS point of failure.** | 9.1 lists the **identity broker** in the *VCF Management* certificate tier `[FA-S22]`; 9.0's flat coverage list does not `[FA-S21]`. Because the broker is the token issuer `[FA-S39]`, a stale broker certificate breaks **every SSO-based API client at once**. 9.0's per-product auth had no such choke point. *Inference from the coverage lists; the docs do not state the blast radius.* |
| T6 | **JIT user inactivity silently kills previously issued API tokens.** | Verbatim: once a JIT user is inactive, *"previously issued API tokens cannot retrieve access tokens until the user authenticates again"* `[FA-S52]`. The token is neither revoked nor expired — the exchange just stops returning access tokens. **9.1-only**; no 9.0 equivalent. |
| T7 | **SDDC Manager and ESX are excluded from VCF SSO in *both* versions.** | Verified independently in 9.0 `[FA-S18]` and 9.1 `[FA-S24]`. A fleet-wide SSO token does **not** authenticate SDDC Manager — it still uses `POST /v1/tokens`. |
| T8 | **`vcf-operations-for-logs` is gone in 9.1**, replaced by `log-management` with a different base path, a different header and a dependency on a 9.1-only operation. | 9.0: base `/api/v2`, `Bearer` scheme, `POST /sessions`, 136 ops. 9.1: base placeholder `http://localhost:8787`, `X-JWT-Token` apiKey, token obtained via `POST /suite-api/api/auth/token/exchange` with `{"serviceKeys":["ops-li"]}`, 23 ops `[SPEC]`. `token/exchange` itself is 9.1-only. |
| T9 | **NSX session authentication is UNCHANGED between 9.0 and 9.1 — the trap is now the opposite one.** | An earlier revision marked NSX 9.1 auth `UNVERIFIED` because the 9.1 auth/RBAC **parent index** page returned HTTP 429 `[FA-gap3]`. A 429 is a rate-limit response, not evidence of absence, and the verdict was over-generalised. The 9.1 **child** page was retrieved `[NSX-S12]`, the NSX 9.1.0.0 API Guide corroborates independently `[NSX-S18]`, and `POST /api/session/create` / `POST /api/session/destroy` are present as `CreateAuthenticatedSession` / `DestroyAuthenticatedSession` in **all three** 9.1 NSX spec inventories `[SPEC]`. `POST /api/session/create` (`j_username`/`j_password`) → `JSESSIONID` + `X-XSRF-TOKEN`, 1800 s default timeout, is `[9.0+9.1]`. The 9.1 specs *additionally* declare `BasicAuth` `[SPEC]`. **The one thing the 429 did cost: the 13 non-Enterprise-Admin/Auditor role names (§5).** |
| T10 | **`vcf-installer` and `sddc-manager` declare no `securitySchemes` in either version.** | `components.securitySchemes == {}` at both tags `[SPEC]`. SDDC Manager's Bearer header is prose-sourced `[FA-S42]`; VCF Installer auth is `UNVERIFIED` in both versions. |

---

## 2. Identity and SSO

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| Identity broker | **Present.** "VCF Identity Broker", configured via the VCF Operations console | **Present**, same name, same federated component list — verified independently in both doc sets | `[FA-S18]` / `[FA-S24]` |
| Federated components | vCenter, VCF Operations, VCF Automation, log management, VCF Operations for Networks, VCF Operations orchestrator, VCF Operations HCX, NSX | **Identical list** | `[FA-S18]` / `[FA-S24]` |
| SSO exclusions | SDDC Manager, ESX | **Identical** — unchanged | `[FA-S18]` / `[FA-S24]` |
| Doc section name | `Fleet Management → Configuring VCF Single Sign-On` | `Fleet Management → Managing Identity and Access Using VCF Single Sign-On` | `[FA-S18]` / `[FA-S16]` |
| New SSO child areas | — | **Managing VCF Roles**, **Provisioning vCenter Custom Roles**, **Managing API Clients and Tokens** | — / `[FA-S16]` |
| Deployment modes | embedded or standalone appliance; appliance described as a **three-node cluster supporting up to five connected VCF Instances** | embedded or standalone appliance; the node-count/instance-count figures are **not restated** on the 9.1 page | `[FA-S19]` / `[FA-S24]` |
| Supported IdPs & protocols | Okta, Ping Identity, Microsoft Entra ID, Microsoft AD FS, "Any SAML 2.0 Identity Providers", AD/LDAP, OpenLDAP. SAML 2.0 + OIDC for authn; SCIM 2.0, JIT, AD/LDAP for provisioning | **`UNVERIFIED`** — no equivalent 9.1 protocols page was retrieved. Do not assume the list is identical | `[FA-S23]` / — |
| SSO configuration order | 7 documented steps, ending at *"Assign required roles and permissions for users or groups"* performed **in the individual components** | **`UNVERIFIED`** — no equivalent 9.1 ordering page retrieved | `[FA-S54]` / — |
| SSO topology models | Not formalised in any retrievable page (9.0 design-library page 404s) | **Three models formalised**: VCF Fleet-Wide SSO, Cross VCF Instance SSO, Single VCF Instance SSO. Constraint: *"split-SSO configurations … are not supported"* | — / `[FA-S56]` |
| vIDM → Identity Broker migration | n/a | **Added.** Users/groups migrate; **OAuth clients do NOT** (T2); local accounts, local-account MFA and AD MFA **not supported**; sync settings compared but not migrated | — / `[FA-S25]` |
| `ALL_USERS` group | Not documented | Optional and scoped **per identity broker, not aggregated across brokers** | — / `[FA-S52]` |
| SSO architecture internals (token flow, trust mechanism, broker ports) | **`UNVERIFIED`** — page is a navigation stub | **`UNVERIFIED`** — page is a navigation stub | `[FA-S65]` / `[FA-S66]` |
| Identity Broker token endpoint `POST /acs/t/{tenant}/token` | **`UNVERIFIED`** — the reference is version-tagged 9.1; the 9.0 doc set has no API-token feature, suggesting it may not be customer-exposed in 9.0 | **Documented.** `application/x-www-form-urlencoded`; required `grant_type`; optional `client_id`, `client_secret`, `refresh_token`, **`api_token`**, `code`, `username`, `password`, `scope`, `redirect_uri`, `domain`, `assertion`, `code_verifier`; HTTP Basic supported on the endpoint. Response: `access_token`, `token_type` (=`"Bearer"`), `expires_in`, `refresh_token`, `id_token`, `scope` | `[FA-gap14]` / `[FA-S39]` `[FA-S40]` |
| Documented OAuth exchange flow | n/a | 4 steps: admin creates API clients in VIDB → admin requests a long-lived API refresh token from the VCF Operations UI → script exchanges it at VIDB for a bearer access token → script authenticates to VCF components. Caveat: *"not all VCF components employ identical token authentication methods"* | — / `[C91-S19]` `[C91-S20]` |
| Broker discovery endpoint | Absent | `GET /suite-api/api/auth/sources/vidb/well-known-url` — "Get VIDB well-known URL" | `[SPEC]` |

---

## 3. API clients, tokens and IAM settings

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| API clients / API tokens via SSO | **Absent.** No API client, API token, OAuth client or role management pages in the SSO tree | **Added.** Create client, generate token, edit/delete/regenerate, emergency access client, IAM settings | `[FA-S53]` / `[FA-S51]` `[FA-S11]` |
| IAM API surface (`/suite-api/api/fleet-management/iam/**`) | **0 operations** at spec tag `9.0.0.0` | **70 operations** at spec tag `9.1.0.0` | `[SPEC]` |
| API client CRUD | Absent | `POST\|PATCH .../ssorealms/{ssoRealmId}/api-clients`; `POST .../api-clients/query`; `GET\|DELETE .../api-clients/{clientId}` | `[SPEC]` |
| API token CRUD | Absent | `POST\|PATCH .../ssorealms/{ssoRealmId}/api-tokens`; `POST .../api-tokens/query`; `GET\|DELETE .../api-tokens/{apiTokenId}`; `POST .../api-tokens/{apiTokenId}/regenerate` | `[SPEC]` |
| OAuth app CRUD | Absent | `GET\|POST\|PUT .../ssorealms/{ssoRealmId}/oauth-apps`; `GET\|DELETE .../oauth-apps/{oauthAppId}`; `POST .../oauth-apps/{oauthAppId}/rotate` | `[SPEC]` |
| Emergency access client | Not documented | **Added** — *"high-privilege and long-lived access tokens to critical systems when standard methods fail"*. `GET\|POST .../emergency-clients`; `GET\|DELETE .../emergency-clients/{clientId}`; `POST .../emergency-clients/{clientId}/regenerate` | — / `[FA-S51]` `[SPEC]` |
| Token TTL controls | Not documented at fleet level | API Token TTL **default 30 days / max 180 days**; Access Token TTL **default 30 minutes / max 480 minutes**; expired-token retention **max 90 days**. Read/write via `GET\|PUT .../iam/settings` | — / `[FA-S11]` `[FA-S52]` `[SPEC]` |
| Token retrievability | n/a | **The API token cannot be retrieved after clicking Continue** | — / `[FA-S11]` |
| JIT user inactivity | Not documented | **Silent token death** (T6) | — / `[FA-S52]` |
| IAM setting **defaults** | n/a | **`UNVERIFIED`** — the page publishes maxima only; the 30-day/30-minute figures come from the token-generation dialog and may be UI defaults | — / `[FA-S52]` `[FA-gap10]` |
| IdP / LDAP / SCIM management API | Absent | `GET\|DELETE .../iam/identity-providers/{idpConfigId}`; `.../ldap-directories`; `.../ldap-directories/{id}/sync-profile`, `/sync-logs`, `/sync-logs/{syncLogId}`; `.../directories/{directoryId}/sync-client`; `GET .../iam/vidbs`; `GET .../iam/tasks/{taskId}`; `DELETE .../iam/components/auth-sources` | `[SPEC]` |

---

## 4. Per-product authentication

| Product | 9.0 | 9.1 | Source |
|---|---|---|---|
| **SDDC Manager** token API | `POST /v1/tokens` (JSON `{"username","password"}` → `accessToken`, `refreshToken.id`); `PATCH /v1/tokens/access-token/refresh` (plain-text refresh UUID → raw JWT body); `DELETE /v1/tokens/refresh-token` (204). Header `Authorization: Bearer <accessToken>` | **Same three paths, spec-confirmed unchanged** at tag `9.1.0.0` — not added, not removed, not deprecated. Payloads/field names/header are prose-carried from the 9.0 reference | `[FA-S42]` `[SPEC]` / `[SPEC]` `[FA-S41]` |
| **SDDC Manager** declared `securitySchemes` | `{}` (none) | `{}` (none) — unchanged | `[SPEC]` |
| **SDDC Manager** operation count | 375 | **423** (+48, 0 removed, 21 newly deprecated: edge-cluster reads, DNS/NTP configuration reads) | `[SPEC]` |
| **VCF Operations** token acquire | `POST /suite-api/api/auth/token/acquire`, `{"username","password"}` → `token` (`<uuid>::<uuid>`), `expiresAt`, `validity`; **6-hour** lifetime | **Identical text**, verified independently in both doc sets | `[FA-S12]` / `[FA-S13]` |
| **VCF Operations** auth header | `Authorization: OpsToken <t>`; legacy `vRealizeOpsToken` supported | Same, **plus `Authorization: Bearer <t>`** from VCF SSO; `401` on missing/expired/invalid (T3) | `[FA-S12]` / `[FA-S13]` `[FA-S44]` |
| **VCF Operations** token operations | `POST /api/auth/token/acquire`, `POST /api/auth/token/release` | Same, **plus `POST /api/auth/token/exchange`** — "Exchange current user token with jwt token" | `[SPEC]` |
| **VCF Operations** declared `securitySchemes` | one: `Token-based-authorization` (apiKey, header `Authorization`) | **identical single scheme** — the spec does *not* declare a separate `Bearer` scheme despite the prose | `[SPEC]` — see Note A |
| **VCF Operations** `/auth/*` role & privilege API | **Present** — 57 `/auth/*` operations incl. `GET\|POST\|PUT /api/auth/roles`, `.../roles/{roleName}/privileges`, `/api/auth/privileges`, `/api/auth/privilegegroups`, user/group permission unassign | **Present** — 59 `/auth/*` operations | `[SPEC]` — see Note B |
| **VCF Operations** operation count | 370 | **504** (+134, 0 removed) | `[SPEC]` |
| **vCenter / vSphere Automation** security schemes | `basic_auth`; `api_key_auth` (header `vmware-api-session-id`); `federated_identity_auth` (bearer) | **Identical** — verified in both prose security-schema pages and both spec tags | `[FA-S37]` `[SPEC]` / `[FA-S36]` `[SPEC]` |
| **vCenter** base path | `https://{host}/api`, port 443; deprecated `/rest` carries only pre-7.0.2 operations; appliance subset on 5480 | **Unchanged** | `[VS-S8]` / `[VS-S18]` `[SPEC]` |
| **vCenter** session path | `POST\|GET\|DELETE /api/session` | **Identical — no delta.** `GET\|POST\|DELETE /session` (operationIds `Cis.Session_get` / `Cis.Session_create` / `Cis.Session_delete`) are present in **both** spec tags, with `servers[0].url` = `https://{host}/api`, giving `POST /api/session`. `/api/cis/session` appears in neither spec. Any residual ambiguity is internal to Broadcom's 9.1 prose, **not** a version difference — see Note D | `[SPEC]` — see Note D |
| **vCenter** non-federated logins | **Blocked** — *"vCenter 9.0 blocks logins with just a user name and password, which might sometimes allow bypassing the federated provider domain"* | **`UNVERIFIED`** — no 9.1 page restating or relaxing this was retrieved | `[VS-S5]` / — |
| **vCenter** operation count (Automation) | 1275 | **1367** (+101, −9) | `[SPEC]` |
| **vCenter** operation count (VI JSON) | 2195 | **2243** (+48) | `[SPEC]` |
| **vCenter** multi-instance API | — | **vCenter Group Federated API (VGFA)** — *"single unified API endpoint for managing all vCenter instances in a vCenter group"*, activatable from the VCF Operations UI after SSO configuration | — / `[FA-S48]` `[C91-S6]` |
| **NSX** OpenAPI specs | **None published** at tag `9.0.0.0` — 9.0 NSX facts are prose-only | **Three added**: `nsx-policy` (`/policy/api/v1`, 3729 ops), `nsx-manager` (`/api/v1`, 1453 ops), `nsx-global-policy` (`/global-manager/api/v1`, 1009 ops). All **OpenAPI 2.0** while every other component is 3.0.x | `[SPEC]` `[TL-S11]` |
| **NSX** declared security scheme | n/a (no spec) | `BasicAuth` — *"HTTP Basic Authentication"* on all three specs | `[SPEC]` |
| **NSX** session-cookie flow | `POST /api/session/create` (form `j_username`/`j_password`) → `JSESSIONID` cookie + `x-xsrf-token` header; **both** required on subsequent calls; `/api/session/destroy`; **1800 s** default timeout | **Identical — no delta.** Verified in 9.1 prose `[NSX-S12]` `[NSX-S18]` and spec-confirmed as `CreateAuthenticatedSession` / `DestroyAuthenticatedSession` in all three 9.1 NSX inventories `[SPEC]`. Expiry surfaces as **403**, not 401 `[NSX-S12]` (T9) | `[FA-S31]` / `[NSX-S12]` `[NSX-S18]` `[SPEC]` |
| **NSX** principal identities / X.509 client-cert auth | Documented service-account mechanism | **Identical** — the NSX 9.1.0.0 API Guide documents the same four mechanisms as 9.0, including X.509 client certificates bound to a principal identity | `[FA-S30]` `[FA-S32]` / `[NSX-S18]` |
| **VCF Operations for Logs** | Spec present: base `/api/v2`, 136 ops, `Bearer` scheme, `POST /sessions`, `GET /sessions/current` | **Spec removed** | `[SPEC]` |
| **Log Management** | Spec absent | **Spec added**: 23 ops, `OPSTokenAuthorization` apiKey in header **`X-JWT-Token`**, token via `POST /suite-api/api/auth/token/exchange` body `{"serviceKeys": ["ops-li"]}` (T8) | `[SPEC]` |
| **VCF Operations for Networks** | base `/api/ni`; one scheme: `ApiKeyAuth` (apiKey header `Authorization`, `API Key - NetworkInsight {token}`); 632 ops | Same base and scheme, **plus `OpsTokenAuth`** (HTTP bearer, *"VCF Ops JWT Token - Bearer {token}"*); 636 ops (+5, −1, 22 newly deprecated) | `[SPEC]` |
| **Realtime Metrics** | Spec absent | **Spec added**: 4 ops, single scheme `bearerAuth` (HTTP bearer). Token acquisition `UNVERIFIED` | `[SPEC]` |
| **Fleet LCM** | Spec absent | **Spec added**: 51 ops, two schemes — `basicAuth` (HTTP basic) and `bearerToken` (HTTP Bearer, *"Bearer token using a JWT"*) | `[SPEC]` |
| **SDDC LCM** | Spec absent | **Spec added**: 26 ops, single scheme `bearerToken` (HTTP Bearer, JWT) — **no** basic auth | `[SPEC]` |
| **VCF Operations Fleet Management API** | **HTTP Basic only**, per Broadcom KB 409715: `Authorization: Basic <base64 of admin@local:<fleet-admin-password>>`; *"The word Basic must be present before the Base64 value"*. Paths, payloads and lifetime undocumented | **No 9.1 equivalent KB or doc page found.** Not the same thing as the new Fleet LCM spec | `[FA-S47]` / `[FA-gap6]` |
| **VCF Automation** | **VM Apps tenant**: `POST /tm/oauth/tenant/{tenant}/token`, form body `grant_type=refresh_token`, `refresh_token=<api token>`. Response token field name **`UNVERIFIED`**; `Authorization` header format **`UNVERIFIED`**. API token 90 d, access token 1 h | **All Apps / Provider**: JWT via `Authorization` header (recommended); `x-vcloud-authorization` **deprecated**; context headers `X-VMWARE-VCLOUD-TENANT-CONTEXT`, `X-VMWARE-VCLOUD-AUTH-CONTEXT`. **Token endpoint URL `UNVERIFIED`** (techdocs page 404 ×3) | `[FA-S14]` `[FA-S15]` / `[FA-S46]` `[FA-gap5]` |
| **vSAN / vSAN Data Protection** | No independent auth — depends on the vSphere Web Services API for login. vSAN DP spec: 48 ops, three schemes (`basic_auth`, `api_key_auth`, `federated_identity_auth`) | vSAN DP spec: **65 ops** (+17), **identical three schemes** | `[FA-S68]` `[SPEC]` / `[SPEC]` |
| **VCF Installer** | 52 ops; `securitySchemes` = `{}`; auth `UNVERIFIED` | **57 ops** (+5); `securitySchemes` = `{}`; auth still `UNVERIFIED` | `[SPEC]` |
| **Supervisor / VKS** | `vcf context create --endpoint … --username … --ca-certificate …`; interactive password or `VCF_CLI_VSPHERE_PASSWORD`; kubeconfig result | **Same flow, identical documented text**, plus (i) explicit **Pinniped Supervisor + Concierge** for federated auth and (ii) a **VCF Automation-registered** path: `export VCF_CLI_VCFA_API_TOKEN=<t>` then `vcf context create … --api-token … --tenant-name … --ca-certificate vcfa.cert`, token from VCF Automation **My Account → API Tokens** | `[FA-S33]` `[TL-S24]` / `[FA-S34]` `[TL-S25]` |

**Note A — VCF Operations `Bearer` scheme.** The spec declares exactly one, format-agnostic scheme
(`Token-based-authorization`, apiKey in the `Authorization` header) in **both** versions `[SPEC]`, while the 9.1
prose reference documents two header forms `[FA-S44]`. Resolution: the spec is *under-specified*, not
authoritative-negative — it cannot distinguish `OpsToken <t>` from `Bearer <t>`. Keep the prose fact for 9.1;
keep `OpsToken`-only for 9.0, which is what the 9.0 prose says `[FA-S12]`.

**Note B — VCF Operations role API version tag corrected.** The prose dossier tagged the `/auth/*` role and
privilege surface `[9.1]` because it was read off the 9.1 API reference `[FA-S45]`. The spec shows the same
operations at tag `9.0.0.0` `[SPEC]`. **Corrected: role/privilege management is 9.0+9.1.** Only
`POST /api/auth/token/exchange` is genuinely 9.1-new.

**Note C — SDDC Manager 9.1 token paths upgraded from "presumed" to "confirmed".** The prose dossier could only
list the three 9.1 operations by name `[FA-S41]` `[FA-gap2]`. The spec confirms the literal paths at
`9.1.0.0` `[SPEC]`.

**Note D — the vCenter session path is NOT a delta; a previously listed one was withdrawn.** An earlier revision
of this table listed 9.0 = `POST|GET|DELETE /api/cis/session` against 9.1 = "Ambiguous", on the basis that
neither `/cis/session` nor `/session` appeared in the specs. **That negative was wrong.**
`GET|POST|DELETE /session` exist with operationIds `Cis.Session_get` / `Cis.Session_create` /
`Cis.Session_delete` in **both** `9.0__vsphere-automation.ops.json` and `9.1__vsphere-automation.ops.json`, and
`servers[0].url` is `https://{host}/api` in both — so the callable path is **`POST /api/session`** at both
tags, unchanged `[SPEC]`. `/api/cis/session` appears **nowhere** in either spec. Some Broadcom prose pages do
print `/api/cis/session` `[FA-S35]` `[VS-S10]` while the `cis-session` reference page prints `/session`
`[FA-S38]`; that is a **prose-vs-spec conflict resolved in favour of the spec**, and it is internal to
Broadcom's documentation — it is not a 9.0-vs-9.1 difference `[FA-gap1]`. **Do not manufacture a delta here.**

---

## 5. Roles and permissions

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| VCF built-in roles page | **Not found** anywhere in the 9.0 fleet-management tree | **Added**: VCF Administrator, VCF Viewer, SDDC Administrator, SDDC Viewer, with per-component mappings. *"VCF roles are mapped to the individual VCF component roles"*; *"built-in VCF roles cannot be modified"* | `[FA-S53]` / `[FA-S20]` |
| VCF role management API | Absent | `GET\|POST\|PUT /api/fleet-management/iam/roles`, `GET\|DELETE .../iam/roles/{name}`, custom component roles under `.../iam/components/roles`, principal role assignment under `.../ssorealms/{id}/principals/{principalId}/roles` | `[SPEC]` |
| vCenter custom role provisioning | Not documented | **Added** — "Provisioning vCenter Custom Roles" (push custom roles to other vCenters) | `[FA-S18]` / `[FA-S16]` |
| VCF role scope hierarchy (global/org/instance) | n/a | **`UNVERIFIED`** — not stated on the built-in-roles page despite the client-creation flow requiring a scope | — / `[FA-S20]` `[FA-gap9]` |
| Where authorization is assigned | **In the individual components** — step 7 of the documented 9.0 SSO configuration order | Centrally, via VCF roles + per-client scope/role at API-client creation | `[FA-S54]` / `[FA-S11]` `[FA-S20]` |
| NSX roles | 15 built-in roles documented (Enterprise Admin = full CRUD; Auditor = read-only; plus Network/Security/Cloud/LB/VPN/Partner/Support variants); custom roles supported | **The 13 non-EA/non-Auditor role names are `UNVERIFIED` for 9.1** — the auth/RBAC **parent index** page returned HTTP 429. `enterprise_admin` and `auditor` are corroborated for 9.1 via the VCF role mapping. **This is the only item the 429 actually cost** — NSX session auth and principal identities are verified for 9.1 (T9) | `[FA-S32]` `[FA-S30]` / `[FA-S20]` `[FA-gap3]` |
| VCF Operations roles | `/auth/*` role & privilege API present (Note B); named roles **Administrator**, **ReadOnly** | Same API; same named roles referenced by the VCF role mapping | `[SPEC]` / `[SPEC]` `[FA-S20]` `[FA-S45]` |
| VCF Automation role model | Identity-integration levels only: LDAP at system *or* organization level; SAML at organization level; OIDC | **Full model documented**: rights, roles, **provider roles**, **global roles** (org admins cannot modify), organization-specific roles, rights bundles (Simple / Advanced modes), System Administrator scoped to the provider org | `[FA-S49]` / `[FA-S50]` |
| Supervisor namespace role names | **`UNVERIFIED`** | **`UNVERIFIED`** | `[FA-gap11]` |

---

## 6. Certificates

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| Default issuing CA | VMware Certificate Authority (VMCA); *"You should replace the default certificates … with trusted enterprise CA-signed certificates"* | **Same** — verified independently | `[FA-S21]` / `[FA-S22]` |
| Supported CA types | VMCA, Microsoft Certificate Authority, OpenSSL, self-signed | VMCA (default), Microsoft CA, OpenSSL, external CA via CSR | `[FA-S21]` / `[FA-S22]` |
| Bulk operations | Single-certificate operations | **Added, verbatim:** *"Starting with VCF Operations 9.1, you can generate certificate signing requests, renew, import, and replace **multiple certificates simultaneously**."* | `[FA-S21]` / `[FA-S22]` |
| Coverage list | Flat: ESXi, vCenter, NSX Manager, SDDC Manager, VCF services | **Split into two tiers.** *VCF Management*: VCF Operations, VCF Automation, VCF Operations for Networks, log management, **identity broker**, VCF management services, VCF Operations HCX (needs Management Pack). *VCF Instance/Domain*: ESX, vCenter, NSX Manager, SDDC Manager, **VMware AVI Load Balancer** | `[FA-S21]` / `[FA-S22]` |
| Identity broker under cert management | **No** | **Yes** — single TLS point of failure for all SSO-based clients (T5) | `[FA-S21]` / `[FA-S22]` |
| Certificate API surface | 5 operations in `vcf-operations`: `GET\|POST\|DELETE /api/certificate`, `POST\|GET /api/applications/clientCertificate/…` | **24 operations**, adding the whole `/api/fleet-management/certificate-management/**` family (`certificate-authorities`, `certificates/query`, `certificates/{id}`, `csrs`), `/api/integrations/services/certificate-management/{serviceKey}/…`, and agent/collector/collector-group renew + renew-status operations | `[SPEC]` |
| Trusted-certificate import | **`UNVERIFIED`** for 9.0 — the import page retrieved is 9.1 | *VCF Operations → Operate → Administration Control Panel → Trusted Certificates → Import*; **PEM format only**; applies to Authentication Sources (AD, OpenLDAP, VMware Identity Manager), Outbound Plugins, Adapter Endpoint | — / `[FA-S57]` |
| Trust store location for imported CAs | **`UNVERIFIED`** | **`UNVERIFIED`** — page does not state which OS/JVM store is modified | `[FA-S57]` `[FA-gap15]` |
| Documented remedy for TLS trust failures | Replace certificates with enterprise CA-signed ones. **No fetched Broadcom page documents disabling TLS verification as a supported practice**; the only `-k` in official docs is inside NSX's own `curl` examples | **Same** | `[FA-S21]` `[FA-S31]` / `[FA-S22]` |

---

## 7. Network reachability

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| Per-service inbound port matrix | **`UNVERIFIED — could not retrieve`.** Planning and Preparation defers to `https://ports.broadcom.com/`, a client-rendered tool exposing no static table; VCF 9.0/9.1 coverage could not be confirmed | **`UNVERIFIED — could not retrieve`**, same reason | `[FA-S28]` `[FA-S64]` / `[FA-S29]` `[FA-S64]` |
| Outbound public-URL allow-list | **404 — page does not exist.** `UNVERIFIED` | **8 URLs, all HTTPS/443**: `dl.broadcom.com`, `projects.packages.broadcom.com`, `vcsa.vmware.com`, `vvs.broadcom.com`, `vsanhealth.vmware.com`, `eapi.broadcom.com`, `vcf.broadcom.com`, `auth.esp.vmware.com` | `[FA-retrieval-failures]` / `[FA-S26]` |
| DNS / FQDN requirement | Not separately retrieved for 9.0 | Documented: unique FQDNs + static IPs, forward and reverse resolution required; component list explicitly includes the **identity broker** for both first and additional instances | — / `[FA-S27]` |
| vSphere API ports and base paths | 443 + `/api`; deprecated `/rest` (pre-7.0.2 operations only); appliance subset on 5480 | **Unchanged** | `[VS-S8]` / `[VS-S18]` |
| New base paths a client must reach | `/v1/*`, `/suite-api/api/*`, `/api/session/*`, `/policy/api/v1/*`, `/api/v1/*`, `/api/*`, `/sdk/vim25/*`, `/api/v2/*`, `/api/ni/*`, `/tm/oauth/tenant/{t}/token` | Adds `/acs/t/{tenant}/token` (identity broker), `/global-manager/api/v1/*` (NSX Global Policy), `/suite-api/api/fleet-management/iam/**`, `/suite-api/api/fleet-management/certificate-management/**`. Drops `/api/v2/*` (Logs) | `[SPEC]` `[FA-S40]` |

---

## 8. Tooling (PowerCLI, SDKs, CLI)

Full detail in `powercli-session.md`.

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| PowerCLI meta-module | `VCF.PowerCLI` **9.0.0.24798382** (2025-06-17) — renamed from `VMware.PowerCLI` in 9.0 | `VCF.PowerCLI` **9.1.0.25380678** (2026-05-12) | `[TL-S05]` `[TL-S12]` / `[TL-S06]` `[TL-S07]` |
| Component module versions | `13.4.0.24798382`; `VMware.Vim 9.0.0.24798382` | `13.5.0.25380678`; `VMware.Vim 9.1.0.25380678` | `[TL-S05]` / `[TL-S07]` |
| Module added | — | **`VMware.Vcf.Sso`** (+1 command) — confirmed absent in 9.0 | `[TL-S05]` / `[TL-S07]` `[TL-S09]` |
| Module removed | `VMware.PowerCLI.VCenter` present | **Dropped** from the meta-module dependency set — sits oddly against the changelog's "0 deprecated, 0 deleted commands" | `[TL-S05]` / `[TL-S07]` `[TL-S09]` `[TL-gap1]` |
| PowerCLI auth parameters | None documented | **`VcfOAuthSecurityContext`** (OAuth) and **`VcfApiToken`** introduced (T4). **Which cmdlets expose them is `UNVERIFIED`** | — / `[TL-S08]` `[TL-S09]` |
| PowerShell support | PowerShell 7.x; **Windows PowerShell 5.1 deprecated as of VCF PowerCLI 9.0** | Same — 5.1 remains deprecated | `[TL-S17]` |
| SDK languages | Java + Python only (no first-party Go or .NET) | Same | `[TL-S12]` `[TL-S34]` |
| SDK coverage | vSphere, vSAN, vSAN DP, SDDC Manager, VCF Installer | Extended to **NSX, VCF Operations, Log Management, Fleet Lifecycle, SDDC Lifecycle**, plus VODAP OpenAPI specs | — / `[TL-S08]` |
| Java SDK build | Gradle | **Maven** | — / `[TL-S08]` |
| Python support | 3.9+ (generic); `vcf-sdk` 3.10–3.14 | **3.13 supported; 3.7 and 3.8 deprecated** | `[TL-S34]` / `[TL-S08]` `[TL-S37]` |
| New APIs | vCenter Authorization Management ("modern REST APIs to configure all aspects of authorization … including privileges, roles"); OpenAPI 3.0 added to vCenter 9.0 | **Utilization API; Query API; vCenter Group Federated API (VGFA)**; OAuth 2.0 API token support; FIPS API (tech preview) | `[TL-S12]` / `[TL-S08]` `[C91-S5]` |
| VCF CLI | First release, "context" management, VCFA + Supervisor endpoints, auto-discovery plugins, airgapped support | **v9.1.0.0**; login flow unchanged (`vcf context create`) | `[TL-S12]` / `[TL-S32]` |
| Spec bundle | 9.0-equivalent ZIP filename **`UNVERIFIED`** (only `latest` = 9.1 was fetched) | `vcf-api-specs-9.1.0.0-25372366.zip`, 39.36 MB, 8 products | — / `[TL-S40]` |

---

## 9. Items verified as UNCHANGED between 9.0 and 9.1

Listing these explicitly so an agent does not manufacture a delta where none exists.

| Item | Evidence |
|---|---|
| Identity broker exists and is named "VCF Identity Broker" | `[FA-S18]` / `[FA-S24]` |
| Federated component list | `[FA-S18]` / `[FA-S24]` |
| SDDC Manager and ESX excluded from SSO | `[FA-S18]` / `[FA-S24]` |
| VCF Operations `token/acquire` endpoint, payload, `token` format, 6-hour lifetime — **identical text** | `[FA-S12]` / `[FA-S13]` |
| vSphere Automation security schemes (basic / `vmware-api-session-id` / bearer) | `[FA-S37]` `[SPEC]` / `[FA-S36]` `[SPEC]` |
| vSphere Automation base path `https://{host}/api`, port 443, deprecated `/rest`, 5480 subset | `[VS-S8]` / `[VS-S18]` `[SPEC]` |
| vCenter session operations `GET\|POST\|DELETE /session` (`Cis.Session_*`) — i.e. `POST /api/session` — identical at both tags (Note D) | `[SPEC]` |
| NSX session auth: `POST /api/session/create` / `/api/session/destroy`, `j_username`/`j_password`, `JSESSIONID` + `X-XSRF-TOKEN`, 1800 s default timeout (T9) | `[FA-S31]` / `[NSX-S12]` `[NSX-S18]` `[SPEC]` |
| NSX principal identities / X.509 client-certificate auth as the service-account mechanism | `[FA-S30]` `[FA-S32]` / `[NSX-S18]` |
| VI JSON base path and `Session` apiKey scheme (`vmware-api-session-id`) | `[SPEC]` |
| vSAN Data Protection security schemes | `[SPEC]` |
| SDDC Manager token API paths (all three) | `[SPEC]` |
| SDDC Manager and VCF Installer declare no `securitySchemes` | `[SPEC]` |
| VCF Operations for Networks base path `/api/ni` | `[SPEC]` |
| Supervisor/VKS `vcf context create` login flow — **identical documented text** | `[TL-S24]` / `[TL-S25]` |
| Default VMCA-signed certificates and the replace-don't-disable guidance | `[FA-S21]` / `[FA-S22]` |
| Ports matrix unobtainable (both versions defer to ports.broadcom.com) | `[FA-S28]` / `[FA-S29]` |
| SSO architecture pages are navigation stubs in both versions | `[FA-S65]` / `[FA-S66]` |

---

## Source Index

All sources accessed **2026-07-31**. `TECHDOCS` = `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.

| Ref | URL / location |
|---|---|
| FA-S11 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/managing-api-tokens.html` |
| FA-S12 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html` |
| FA-S13 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html` |
| FA-S14 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token.html` |
| FA-S15 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token/get-your-access-token-for-vra-8-x.html` |
| FA-S16 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on.html` |
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
| FA-S41 | `https://developer.broadcom.com/xapis/sddc-manager-api/latest/tokens/` (9.1) |
| FA-S42 | `https://developer.broadcom.com/xapis/sddc-manager-api/9.0/tokens/` |
| FA-S44 | `https://developer.broadcom.com/xapis/vcf-operations-api/latest/` (9.1) |
| FA-S45 | `https://developer.broadcom.com/xapis/vcf-operations-api/latest/auth/` (9.1) |
| FA-S46 | `https://developer.broadcom.com/xapis/all-apps-org-access-control/latest/` (VCF Automation 9.1 Provider Management API) |
| FA-S47 | `https://knowledge.broadcom.com/external/article/409715/how-to-authorize-vcf-operations-fleet-ma.html` |
| FA-S48 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| FA-S49 | `TECHDOCS/9-0/provider-management.html` |
| FA-S50 | `TECHDOCS/9-1/provider-management/managing-system-administrators-and-roles/managing-rights-and-roles.html` |
| FA-S51 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens.html` |
| FA-S52 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/view-and-manage-token-lifecycle-and-security.html` |
| FA-S53 | `TECHDOCS/9-0/fleet-management/what-is/managing-vmware-cloud-foundation-operations-sso.html` |
| FA-S54 | `TECHDOCS/9-0/fleet-management/what-is/setting-up-sso.html` |
| FA-S56 | `TECHDOCS/9-1/design/design-library/single-sign-on-models.html` |
| FA-S57 | `TECHDOCS/9-1/fleet-management/certificate-management-9-0/managing-certificates-in-vmware-vsphere-foundation/certificates/importing-ca-certificates.html` |
| FA-S64 | `https://ports.broadcom.com/` |
| FA-S65 | `TECHDOCS/9-0/fleet-management/what-is/sso-architecture.html` |
| FA-S66 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is/sso-architecture.html` |
| FA-S68 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/using-the-vsan-management-sdks.html` |
| NSX-S12 | `TECHDOCS/9-1/advanced-network-management/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html` (**9.1 child page — retrieved successfully**; the 429 below was on the parent index page). Source: `research/nsx.md` |
| NSX-S18 | `https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html` (NSX 9.1.0.0 API Guide). Source: `research/nsx.md` |
| FA-retrieval-failures | 404: `TECHDOCS/9-0/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html`; 429 (repeated, **parent index page only**): `TECHDOCS/9-1/advanced-network-management/authentication-and-authorization.html`; 404 ×3: `TECHDOCS/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/generating-an-access-token.html`; 404: `TECHDOCS/9-0/design/design-library/single-sign-on-models/-fleet.html` |
| FA-gap1/2/3/5/6/9/10/11/14/15 | `research/foundation-auth-identity.md`, `## Gaps and Ambiguities`, corresponding items |
| TL-S05 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382` |
| TL-S06 | `https://www.powershellgallery.com/packages/VCF.PowerCLI` |
| TL-S07 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.1.0.25380678` |
| TL-S08 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S09 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-powercli-changelog.html` |
| TL-S11 | `https://github.com/vmware/vcf-api-specs/blob/main/README.md` |
| TL-S12 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S17 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-powercli-compatibility-matrix.html` |
| TL-S24 | `TECHDOCS/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html` |
| TL-S25 | `TECHDOCS/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html` |
| TL-S32 | `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-consumption/latest/consumer-interfaces-in-vcf/installing-and-using-vcf-cli-v9.html` |
| TL-S34 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/programming-language-support-in-the-vsphere-web-services-sdk.html` |
| TL-S37 | `https://developer.broadcom.com/vcf-python-sdk` |
| TL-S40 | `https://developer.broadcom.com/sdks/vcf-api-specification/latest` |
| TL-gap1 | `research/tooling-powercli-vks-sdk.md`, `## Gaps and Ambiguities`, item 1 |
| C91-S5 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsphere.html` |
| C91-S6 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| C91-S19 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access/token-exchange-architecture.html` |
| C91-S20 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development.html` |
| VS-S5 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-vsphere.html` |
| VS-S8 | `TECHDOCS/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/understanding-the-vsphere-automation-rest-api.html` |
| VS-S10 | `https://developer.broadcom.com/xapis/vsphere-automation-api/latest/` |
| VS-S18 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/understanding-the-vsphere-automation-rest-api.html` |
| SPEC | `research/spec-inventory/index.json`, `research/spec-inventory/DELTA-9.0-to-9.1.md`, `research/spec-inventory/9.{0,1}__<product>.ops.json` — derived by diffing git tags `9.0.0.0` and `9.1.0.0` of `https://github.com/vmware/vcf-api-specs` (cloned 2026-07-31). Re-verified directly for this revision: `Cis.Session_get`/`_create`/`_delete` on `/session` with `base_path` `https://{host}/api` in `9.{0,1}__vsphere-automation.ops.json`; `CreateAuthenticatedSession` / `DestroyAuthenticatedSession` on `/api/session/{create,destroy}` in `9.1__nsx-{policy,manager,global-policy}.ops.json` |

---

*This change list was built from documentation and machine-extracted API specifications. It has not been
validated against a live VCF environment.*
