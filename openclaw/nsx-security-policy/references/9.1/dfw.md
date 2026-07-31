# NSX Distributed Firewall / Security Policy — VCF 9.1

**Applies to:** NSX **9.1.0.0** (build 25318225), the NSX version in the VCF 9.1 Bill of Materials.
**Do not apply this file to VCF 9.0.** Use `../9.0/dfw.md` for 9.0 and `../deltas.md` for the change list.

## Provenance of everything below

Two independent source classes are used, and every endpoint row is tagged with which one backs it:

| Tag | Meaning |
|---|---|
| **[SPEC]** | The exact `method + path` was found in `research/spec-inventory/9.1__nsx-policy.ops.json`, `9.1__nsx-manager.ops.json` or `9.1__nsx-global-policy.ops.json` — machine-extracted from the `9.1.0.0` tag of `github.com/vmware/vcf-api-specs` (`specifications/nsx/openapi-2.0/nsx_policy_api.yaml`, `spec_version: 9.1.0.0`, `basePath: /policy/api/v1`, 3,729 operations). This is the strongest evidence available. |
| **[DOC]** | Verified only from version-pinned Broadcom prose (NSX 9.1.0 developer portal, NSX 9.1.0 API Guide, VCF 9.1 NSX admin guide). |
| **[INFERRED]** | Neither — stated as a shape/convention, not as a verified fact. Confirm before relying on it. |

**Version-asymmetry warning.** NSX 9.1 has a published machine-readable spec; NSX 9.0 does **not**
(there is no NSX spec at the `9.0.0.0` tag of the corpus). Therefore a `[SPEC]` tag in this file is
evidence about **9.1 only** and must never be copied into the 9.0 file as verification.

---

## Contents

- [Provenance of everything below](#provenance-of-everything-below) — what `[SPEC]` / `[DOC]` / `[INFERRED]` mean
- [**Prerequisites**](#prerequisites) — **read before any write**
  - [P1 — HTTPS reachability and trusted chain](#p1--you-can-reach-a-specific-nsx-manager-node-over-https-with-a-trusted-chain)
  - [P2 — Cookie-based authentication enabled](#p2--cookie-based-authentication-is-enabled-on-the-api-service)
  - [P3 — Role / permission level, and service accounts](#p3--you-hold-an-nsx-role-with-the-right-permission-level)
  - [P4 — Domain exists; correct domain id](#p4--the-domain-exists-and-you-are-using-the-right-domain-id)
  - [P5 — Groups exist; you have their policy paths](#p5--both-groups-already-exist-and-you-know-their-policy-paths)
  - [P6 — Services: referenced or inlined](#p6--you-know-which-services-you-will-reference-or-will-inline-them)
  - [P7 — `_revision` and partial-patch contract](#p7--you-accept-the-concurrency-and-partial-patch-contract)
  - [P8 — VCF ownership of the objects you touch](#p8--vcf-ownership-of-the-nsx-objects-you-are-about-to-touch)
- [Authentication](#authentication)
  - [A1 create · A2 both credentials · A3 destroy](#a1--create-a-session)
  - [A4 — **expiry is 403, not 401**](#a4--trap-expiry-surfaces-as-403-forbidden-not-401)
  - [A5 — cookies are bound to one manager node](#a5--trap-cookies-are-bound-to-a-single-manager-node)
  - [A6 — other mechanisms](#a6--other-mechanisms)
  - [A7 — **token-based principal identity (service accounts)**](#a7--token-based-principal-identity-the-service-account-route--91)
  - [Rate limits and pagination](#rate-limits-and-pagination) — **spec-vs-prose conflict, unresolved**
- [Base path and API surface](#base-path-and-api-surface) — Policy-only; `communication-maps` deprecated
- [Path families (multi-tenancy and federation)](#path-families-multi-tenancy-and-federation)
- [Groups](#groups) — endpoints, body, incremental expression edits
- [Security policies](#security-policies) — endpoints, body, categories
- [Rules](#rules) — endpoints, body, `ServiceEntry`
- [Rule ordering and sequence](#rule-ordering-and-sequence) — categories, `sequence_number`, `?action=revise`
- [Drafts (staged configuration)](#drafts-staged-configuration)
- [Related DFW settings and query endpoints](#related-dfw-settings-and-query-endpoints)
- [**Worked example** — block tcp/3389 between two groups](#worked-example--block-tcp3389-rdp-from-one-existing-group-to-another) (Steps 0–7 + [failure decode](#failure-decode-for-this-sequence))
- [What is unverified for 9.1](#what-is-unverified-for-91)

---

## Prerequisites

Everything in this section must be true **before** you issue any DFW call. Each item carries **four**
elements — if one is missing, the item is incomplete:

1. **What must be true** — the condition itself.
2. **How to verify it** — a concrete, *non-destructive* call or check. Never verify a permission or a
   contract by performing the production change it guards.
3. **Which version it applies to** — every item below applies to **NSX 9.1.0.0** unless it says otherwise.
4. **Whether it exists in the other version** — stated as a "9.0 difference" line on every item.

### P1 — You can reach a specific NSX Manager node over HTTPS with a trusted chain

- **Must be true:** an `https://<nsx-manager>` endpoint on 443, with its certificate chain in your
  trust store. VCF-deployed appliances default to VMCA-signed certificates, which are *not* publicly
  trusted; a stock HTTP client fails chain validation until you add the VMCA root or the enterprise CA.
- **Verify:** `curl -sS -o /dev/null -w '%{http_code}\n' https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json`
  without `-k`. A TLS error means the trust store, not the endpoint, is the problem.
- **9.0 difference:** none known. Certificate auto-renewal covers NSX Manager in both versions, so a
  long-lived client must be able to reload its trust bundle.

### P2 — Cookie-based authentication is enabled on the API service

- **Must be true:** `cookie_based_authentication_enabled` is `true` (spec default: `true`). The 9.1
  spec states verbatim: *"When cookie-based authentication is disabled, new sessions cannot be created
  via /api/session/create."*
- **Verify:** `GET https://<nsx-manager>/api/v1/cluster/api-service` **[SPEC — `GetApiServiceConfig`,
  `9.1__nsx-manager.ops.json`]** and read `cookie_based_authentication_enabled` and `session_timeout`.
- **9.0 difference:** the same endpoint exists in 9.0 per prose docs, but the
  `cookie_based_authentication_enabled` field is spec-confirmed for **9.1 only**. If it is `false`,
  fall back to HTTP Basic or X.509 client-certificate auth.

### P3 — You hold an NSX role with the right permission level

- **Must be true:** **Enterprise Admin** (`enterprise_admin`) for any write (create/update/delete of
  security policies, rules, groups, drafts); **Auditor** (`auditor`) is sufficient for read-only.
  NSX ships 15 built-in roles; Enterprise Admin = *"Full access (FA) — All permissions including
  Create, Read, Update, and Delete (CRUD)"*, Auditor = read-only. Custom roles are supported.
- **Verify — read your role, do not test it by writing.** Call
  `GET /api/v1/aaa/role-bindings` **[SPEC — `GetAllRoleBindings`, `9.1__nsx-manager.ops.json`]** and
  find the binding for your principal; its role is the answer. For a single known binding use
  `GET /api/v1/aaa/role-bindings/{binding-id}` **[SPEC — `GetRoleBinding`]**. Pair it with a harmless
  read such as `GET /policy/api/v1/infra/domains` **[SPEC — `ListDomainForInfra`]** to confirm the
  session itself works.
  **Do not verify write permission by attempting the production write.** An earlier revision of this
  file said to "attempt the intended write" and read the 403 — that verifies a firewall permission by
  making a firewall change, and on success it has already changed production. If you want a live
  write probe anyway, do it against a **throwaway object** (a scratch security policy id you then
  delete), never against the target rule.
- **Service accounts:** two routes, and they are not equivalent.
  - **Token-based principal identity via VCF SSO / VIDB OIDC — prefer this.** Spec-confirmed for 9.1
    and not deprecation-flagged. Full prerequisites and operationIds in **A7**.
  - **Classic principal identities** — the mechanism an X.509 client certificate binds to (*"The
    certificate is associated with a principal identity (a short name, similar to a username)"*),
    `POST /api/v1/trust-management/principal-identities` **[SPEC — `RegisterPrincipalIdentity`]**.
    Note the tension: the VCF **9.0** product support notes flagged Principal Identity accounts as
    *"planned for deprecation in an upcoming release,"* directing operators to Federated Users via VCF
    SSO. That statement was **not restated in the 9.1 support notes retrieved**, so its 9.1 status is
    unverified. Use A7 for new automation.
  - The earlier claim that principal identities are *"the only documented NSX-native service-account
    mechanism"* is **withdrawn for 9.1** — the token-based route in A7 is spec-confirmed.
- **VCF role mapping:** VCF **Administrator** and **SDDC Administrator** map to NSX `enterprise_admin`;
  VCF **Viewer** and **SDDC Viewer** map to NSX `auditor`. Role assignment is performed *in NSX*, not
  centrally, even when identity is federated.
- **9.0 difference:** the 15-role list and the Enterprise Admin / Auditor definitions were sourced from
  a **9.0**-pinned page and were not re-verified on a 9.1 page. Treat the role model as unchanged but
  not independently 9.1-confirmed.

### P4 — The domain exists and you are using the right domain id

- **Must be true:** a DFW security policy lives under a **domain**. The conventional id is `default`;
  the 9.1 spec text refers to the `'default' Domain` when describing category restrictions. It is a
  convention, not a guarantee — user-created domains exist and restrict which rule categories are usable.
- **Verify:** `GET /policy/api/v1/infra/domains` **[SPEC — `ListDomainForInfra`]**, or
  `GET /policy/api/v1/infra/domains/{domain-id}` **[SPEC — `ReadDomainForInfra`]** for a 200.
- **Never** assume `default` without this check on a multi-tenant or federated deployment.
- **9.0 difference:** `GET /infra/domains` was **not** confirmed on a 9.0-pinned page. In 9.0, verify
  the domain by reading a known object under it instead.

### P5 — Both groups already exist and you know their **policy paths**

- **Must be true:** a rule references sources and destinations by **policy path string**
  (`/infra/domains/default/groups/<group-id>`), not by name and not by UUID. `Rule.source_groups` and
  `Rule.destination_groups` are arrays of strings; a nonexistent path is a realization failure, not a
  400 at write time in every case. Create or confirm groups **first**.
- **Verify:** `GET /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` **[SPEC —
  `ReadGroupForDomain`]** returns 200, and record the `path` field from the response body — use that
  literal string in the rule.
- **9.0 difference:** the group read endpoint is prose-verified for 9.0; the group *list* endpoint is
  not. See `../9.0/dfw.md`.

### P6 — You know which services you will reference (or will inline them)

- **Must be true:** `Rule.services` is an array of paths to `Service` objects
  (`/infra/services/<service-id>`); `Rule.service_entries` is an array of inline `ServiceEntry`
  objects. Use one or the other. Inlining avoids a dependency on a predefined service existing.
- **Verify:** `GET /policy/api/v1/infra/services` / `GET /policy/api/v1/infra/services/{service-id}`
  **[SPEC — `ListServicesForTenant`, `ReadServiceForTenant`]**.
- **9.0 difference:** `/infra/services` was **not** covered by the 9.0 prose research. For 9.0, prefer
  inline `service_entries`, whose shape is part of the rule body rather than a separate endpoint.

### P7 — You accept the concurrency and partial-patch contract

- **`_revision`:** every REST payload carries an integer `_revision`. Verbatim from the 9.1 API Guide:
  *"Clients must provide this property in PUT requests and it must match the current _revision or the
  update will be rejected."* And: *"the _revision property must **not** be set when PUT is used to
  create a new resource. Once the resource is created, however, the _revision property must be provided
  with PUT operations."* `PATCH` does not require it.
- **Partial patch is off by default** and must be enabled explicitly before you rely on partial-object
  `PATCH` semantics: `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` with
  `{"enable_partial_patch": "true"}` **[DOC — VCF 9.1 NSX admin guide]**.
- **Verify:** read the partial-patch setting before relying on it —
  `GET /policy/api/v1/system-config/nsx-partial-patch-config`
  **[SPEC — `GetPartialPatchConfiguration`, `9.1__nsx-policy.ops.json`]** and check
  `enable_partial_patch`. For `_revision`, verify non-destructively by reading any existing policy
  object (`GET …/security-policies/{id}` **[SPEC — `ReadSecurityPolicyForDomain`]**) and confirming an
  integer `_revision` is present in the body — that is the value a subsequent `PUT` must echo. Do not
  probe the contract by issuing a deliberately stale `PUT` against a live object.
- **9.0 difference:** identical statements appear in the 9.0 doc set, but the `GET` verb on
  `nsx-partial-patch-config` is spec-confirmed for **9.1 only**.

### P8 — VCF ownership of the NSX objects you are about to touch

- **There is no authoritative published list of which NSX objects VCF owns and which an operator may
  change directly.** This is a real gap, not an omission here. What *is* documented:
  - Standalone NSX install/upgrade is not supported; NSX must follow the VCF BOM **[DOC — 9.0 support
    notes; not restated in 9.1]**.
  - In 9.1, **SDDC Manager network sync** reconciles *"network configuration changes done directly in
    vCenter or NSX Manager"* — i.e. out-of-band NSX edits are explicitly reconciled in 9.1 rather than
    purely forbidden **[DOC — VCF 9.1 What's New: NSX]**.
  - The 9.1 product support notes contain **no** statement distinguishing VCF-managed from
    directly-managed NSX objects.
- **Practical rule:** DFW security policies, rules and groups are user-authored security constructs and
  are the normal target of direct Policy API automation. Fabric objects (transport zones, edge
  clusters, host transport nodes, NSX Manager deployment) are VCF-lifecycle-owned — do not create or
  delete them via NSX directly. **This split is [INFERRED], not doc-stated.**
- **Verify — per object, before you touch it.** Since no authoritative ownership list exists, verify
  ownership *empirically and non-destructively*:
  1. **Read the object and inspect its origin markers.** `GET` the object and check
     `_system_owned` / `_protection` / `origin_site_id` and the `_create_user` field on
     `PolicyConfigResource`. A `_system_owned: true` or a `_protection` value other than
     `NOT_PROTECTED`, or a `_create_user` that is an NSX/VCF service account rather than a human or
     your automation principal, means **something else owns it — do not modify it**.
  2. **Check the system-owned exclusion set** rather than guessing:
     `GET /policy/api/v1/infra/settings/firewall/security/exclude-list?system_owned=true`
     **[SPEC — `GetInternalFirewallExcludeList`]**.
  3. **Check for dependents before disabling DFW-wide settings:**
     `GET /policy/api/v1/infra/settings/firewall/security/dependent-services`
     **[SPEC — `GetDistributedFirewallDependentServices`]**.
  4. **Prefer a draft as the verification harness.** Stage the change and read
     `GET /policy/api/v1/infra/drafts/{draft-id}/complete`
     **[SPEC — `GetPreviewOfConfigurationAfterPublishOfDraft`]**, which returns the configuration *as
     it would look after publish* — a dry run that touches nothing. This is the closest thing to a
     safe ownership/impact check available.
  Note that steps 1–4 verify *"is this object system-owned"*, **not** *"is VCF entitled to overwrite
  my change"* — the latter is unanswerable from documentation. **[INFERRED]**
- **9.0 difference:** 9.0 has no SDDC Manager network-sync reconciliation statement, so out-of-band
  edits are less clearly supported there; and the three `[SPEC]` verification endpoints above are
  spec-confirmed for **9.1 only**.

---

## Authentication

### A1 — Create a session

```
POST https://<nsx-manager>/api/session/create
Content-Type: application/x-www-form-urlencoded

j_username=<user>&j_password=<password>
```

**[SPEC — `CreateAuthenticatedSession`, `9.1__nsx-manager.ops.json` and `9.1__nsx-global-policy.ops.json`.
Note the path is `/api/session/create` verbatim — it is declared as an absolute path and does *not*
sit under the `/api/v1` basePath.]**

Spec description, verbatim: *"Authenticates using the given username and password. If successful, the
HTTP response headers will contain a Set-Cookie header and an X-XSRF-TOKEN header. Both of these
headers should be sent with subsequent API requests."*

Spec example response, verbatim:

```
set-cookie: JSESSIONID=57021338F5FDB766121F51BB5E1B82C3; Path=/; Secure; HttpOnly; SameSite=Lax
x-xsrf-token: 8bf06253-c246-4e4b-a379-f218dd0a193c
200 OK
```

### A2 — Send **both** credentials on every subsequent request

`JSESSIONID` alone is **not** sufficient. Every subsequent call needs:

```
Cookie: JSESSIONID=<value>
X-XSRF-TOKEN: <value>
```

Omitting `X-XSRF-TOKEN` on a write is a common cause of an unexplained rejection. The header name is
case-insensitive in practice (`x-xsrf-token` appears in the Broadcom curl examples).

```bash
curl -i -k -c session.txt -X POST \
  -d 'j_username=admin@example.com&j_password=SecretPwsd3c4d' \
  https://<nsx-manager>/api/session/create 2>&1 > response.txt

curl -k -b session.txt -H "x-xsrf-token: 5a764b19-5ad2-4727-974d-510acbc171c8" \
  https://<nsx-manager>/policy/api/v1/infra/segments
```

**[DOC — VCF 9.1 NSX admin guide, "NSX API authentication using a session cookie"]**

URL-encode the password: `+` and other special characters break the form encoding otherwise.

### A3 — Destroy the session when done

```
POST https://<nsx-manager>/api/session/destroy
```

Send the cookie **and** the `x-xsrf-token` header. **[SPEC — `DestroyAuthenticatedSession`]**
Spec description, verbatim: *"Unauthenticates and makes the provided session cookie invalid. The
set-cookie and x-xsrf-token headers obtained from an earlier call to /api/session/create should be
provided in the HTTP headers of this request."* On logout *"the session cookie is immediately
eliminated from the reverse-proxy of the NSX Manager and cannot be reused."*

### A4 — Trap: expiry surfaces as **403 Forbidden, not 401**

Default session inactivity timeout is **1800 seconds (30 minutes)** — spec-confirmed:
`ApiServiceConfig.session_timeout` has `default: 1800` in the 9.1 spec. **[SPEC]**

> **Attribution correction.** The spec's `x-vmw-nsx-example-response` for
> `GET /api/v1/cluster/api-service` contains **no `session_timeout` key at all** (it shows
> `global_api_concurrency_limit`, `client_api_rate_limit`, `client_api_concurrency_limit`,
> `connection_timeout`, `redirect_host`, `cipher_suites`). The `default: 1800` on the
> `ApiServiceConfig` schema is the *only* spec evidence for this value. A `session_timeout: 1800`
> **does** appear in a spec example — but in the example for the **deprecated**
> `GET /api/v1/node/services/http` (`HttpServiceProperties`), which is a different endpoint. Do not
> cite that example as evidence about `api-service`.

When the session expires, *"NSX Manager responds with a 403 Forbidden HTTP response."* **[DOC — VCF 9.1
admin guide]** A client that only re-authenticates on 401 will spin on 403 forever. **Re-authenticate
on 403**, then retry once; if the retry is also 403, it is an authorization problem (P3), not expiry.

Change the timeout with `PUT https://<nsx-manager>/api/v1/cluster/api-service` (`session_timeout`)
**[SPEC — `UpdateApiServiceConfig`]**.

### A5 — Trap: cookies are bound to a **single manager node**

Session cookies are manager-node-specific and **cannot be reused across cluster nodes**. If you talk to
a cluster VIP or a load balancer that distributes across members, a cookie minted on node A will fail
on node B — again as a 403, indistinguishable from expiry without pinning. **Pin the client to one
node's address, or re-authenticate per node.** **[DOC — VCF 9.0 admin guide; the dossier tags this
convention `[9.0+9.1 — same]`, but the verbatim statement was read on the 9.0-pinned page.]**

### A6 — Other mechanisms

- **HTTP Basic:** `Authorization: Basic <base64>` — supported. `curl -k -u USER:PASS https://MANAGER/api/v1/logical-ports`.
  The 9.1 policy spec declares exactly one security scheme: `BasicAuth` (`type: basic`). **[SPEC — `security_schemes`]**
- **X.509 client certificate:** bound to a **principal identity**; `curl --key <key> --cert <cert>`. **[DOC]**
- **VMC token exchange:** documented but not applicable to on-prem VCF.
- **Token-based principal identity (VCF SSO → NSX):** see A7. A bearer-token route **does** exist in
  the 9.1 spec. The blanket "no bearer flow is documented" claim carried by earlier revisions of this
  file was **wrong for 9.1** — what remains true is that the 9.1 *prose* doc set does not describe an
  end-to-end token flow, and that no such route is verifiable for **9.0** (no NSX spec at that tag).

### A7 — Token-based principal identity (the service-account route) — **9.1**

This is the non-interactive, non-deprecated service-account mechanism, and it is the alternative to
the classic (deprecation-flagged) principal identity offered in P3. It binds an **external OIDC
identity** — in VCF, the VMware Identity Broker (**VIDB**) — to an NSX role, so a caller presenting a
VIDB-issued token is authorized in NSX without a local NSX password or a client certificate.

**Prerequisites, in order:**

1. **A VIDB OIDC endpoint must be configured on NSX.** Without it there is no issuer for NSX to
   validate tokens against, and step 2 has nothing to bind to.
   - `POST /api/v1/trust-management/oidc-uris/action/configure-vidb-oidc-endpoint`
     **[SPEC — `ConfigureVidbAndAddOidcEndPoint`, `9.1__nsx-manager.ops.json`]**
   - Verify / list what is already configured: `GET /api/v1/trust-management/oidc-uris`
     **[SPEC — `ListOidcEndPoints`]**; single endpoint `GET /api/v1/trust-management/oidc-uris/{id}`
     **[SPEC — `GetOidcEndPoint`]**.
   - Health-check it before relying on it: `GET /api/v1/trust-management/oidc-uris/{id}/health`
     **[SPEC — `CheckOidcEndPointHealth`]**, and connectivity-test with
     `POST /api/v1/trust-management/oidc-uris/action/test-vidb-oidc-endpoint-connection`
     **[SPEC — `TestVidbConnection`]**.
   - **Constraint carried over from 9.0:** 9.0 narrowed NSX to **one** OIDC endpoint, which must be
     VMware Identity Broker. The 9.1 support notes do **not** restate this, so whether 9.1 still caps
     it at one is **unverified** — `ListOidcEndPoints` returning a collection is not proof that more
     than one is supported. Check the live list before adding a second.

2. **A token-based principal identity must be registered**, mapping that external identity to an NSX
   role (P3 still governs *which* role you need — `enterprise_admin` for DFW writes).
   - `POST /api/v1/trust-management/token-principal-identities`
     **[SPEC — `RegisterTokenBasedPrincipalIdentity`, `9.1__nsx-manager.ops.json`]**
   - **Verify:** `GET /api/v1/trust-management/token-principal-identities`
     **[SPEC — `ListTokenBasedPrincipalIdentities`]**, or
     `GET /api/v1/trust-management/token-principal-identities/{principal-identity-id}`
     **[SPEC — `GetTokenBasedPrincipalIdentity`]** for a 200.
   - Remove with `DELETE /api/v1/trust-management/token-principal-identities/{principal-identity-id}`
     **[SPEC — `DeleteTokenBasedPrincipalIdentity`]**.

**What is spec-confirmed and what is not.** The four `token-principal-identities` operations and the
`oidc-uris` operations above are confirmed **[SPEC]** in `9.1__nsx-manager.ops.json` — that is
evidence the *configuration surface* exists. The **wire format of the resulting authenticated
request** (header name, token type, whether NSX still demands `X-XSRF-TOKEN` alongside it) was **not**
found in either the spec or the prose doc set and is **[INFERRED]** at best. Confirm it against the
appliance before building a client on it; the session-cookie flow (A1–A3) remains the route this file
can fully evidence end to end.

**9.0:** **not applicable / unverified.** There is no NSX specification at the `9.0.0.0` tag, so
neither the endpoints nor the capability can be confirmed for 9.0. Do **not** back-port this section.
`../9.0/dfw.md` deliberately omits it.

### Rate limits and pagination

- Per-client rate limit **100 req/s**, HTTP **429** on exceed; per-client concurrency **40**.
  **[DOC — 9.1 prose only. NOT spec-confirmed for `/api/v1/cluster/api-service`.]**
- **Spec-vs-prose conflict on the per-client limits — unresolved, do not silently pick one.**

  | Source | `client_api_rate_limit` | `client_api_concurrency_limit` | `global_api_concurrency_limit` |
  |---|---|---|---|
  | **Prose** (9.1 admin guide / API Guide) | 100 req/s | 40 | 199 (9.0 prose) |
  | **[SPEC]** `ApiServiceConfig` schema defaults — `GET·PUT /api/v1/cluster/api-service` | **250** | **100** | **500** |
  | **[SPEC]** `api-service` `x-vmw-nsx-example-response` | **250** | **100** | **500** |
  | **[SPEC]** `HttpServiceProperties` schema defaults — `/api/v1/node/services/http`, **`x-deprecated: true`** | 100 | 40 | 100 |
  | **[SPEC]** `/api/v1/node/services/http` example response | 100 | 40 | 199 |

  The 100 / 40 / 199 figures **are** in the 9.1 spec, but they belong to the **deprecated**
  `HttpServiceProperties` model on `/api/v1/node/services/http` — *not* to `ApiServiceConfig` on
  `/api/v1/cluster/api-service`, which is the endpoint this file tells you to read (P2, A4). The
  earlier claim that the `api-service` example shows `100`/`40` was a **misattribution**: that example
  shows `250`/`100`/`500`.

  **What to do:** treat the limits as **deployment-specific and unknowable from documentation**. Read
  them at runtime with `GET /api/v1/cluster/api-service` **[SPEC — `GetApiServiceConfig`]** and honour
  what that returns. If you must assume a value before you can read one, assume the **lower** (prose)
  figures — 100 req/s and 40 concurrent — because backing off too early is safe and backing off too
  late produces 429/503. Do **not** record either pair as a spec-confirmed fact about the API service.
- **Global concurrency, same conflict:** 9.0 API Guide prose gives an *overall server maximum of 199
  concurrent requests*; the 9.1 spec's `ApiServiceConfig.global_api_concurrency_limit` declares
  `default: 500` (503 Service Unavailable on exceed) — while the deprecated node-http model declares
  `default: 100` and shows `199` in its example. Flagged, **not resolved**; read the live value.
- Pagination: `ListResult` with `page_size` default and max **1000**; follow `cursor` until absent.

---

## Base path and API surface

**Policy API base path: `/policy/api/v1`** — confirmed as the spec `basePath` in
`nsx_policy_api.yaml` at the `9.1.0.0` tag. **[SPEC]**

> *"Beginning with VCF 9.0, the NSX Manager interface provides a single mode, Policy mode, for
> configuring resources. The Manager mode and Manager API provided by NSX 4.x and earlier are no
> longer supported."* — VCF 9.1 NSX admin guide, verbatim. **[DOC]**
>
> *"The Policy API is part of the NSX REST APIs and contains URIs that begin with /policy/api."* **[DOC]**

**Consequence for an agent: never configure a DFW object through `/api/v1`.** There is no supported
Manager-API path to a distributed firewall rule in 9.1.

`/api/v1` survives for a narrow, non-policy set:

| Surviving `/api/v1` use | Example | Evidence |
|---|---|---|
| Session lifecycle | `POST /api/session/create`, `POST /api/session/destroy` | **[SPEC]** (declared as absolute paths) |
| Node / cluster admin | `GET·PUT /api/v1/cluster/api-service` | **[SPEC — `GetApiServiceConfig`, `UpdateApiServiceConfig`]** |
| Fabric admin | node and fabric management endpoints | **[DOC — 9.1 API Guide: *"NSX Manager API: APIs for NSX administration; node and cluster management APIs and fabric management APIs"*]** |
| OpenAPI spec retrieval | `GET /api/v1/spec/openapi/nsx_policy_api.{json,yaml}`, `nsx_api.{json,yaml}` | **[DOC — 9.1 API Guide]** |

Note the layering: the API Guide still *describes* both surfaces neutrally and makes no recommendation.
The **product documentation** is the authoritative "Policy-only" statement — follow the product docs.

### Legacy: `communication-maps` is deprecated

The pre-Policy-naming DFW tree still exists in the 9.1 spec and **every operation on it is marked
`deprecated: true`**: `/infra/domains/{domain-id}/communication-maps[/{id}[/communication-entries[/{id}]]]`
plus their `?action=revise` forms — 12 deprecated operations. **[SPEC]** `security-policies` /
`rules` is the current naming. Do not emit `communication-maps` paths.

---

## Path families (multi-tenancy and federation)

Every DFW object below exists in up to four families. Pick the one that matches where the object lives —
they are **not** interchangeable, and reading a project-scoped policy through `/infra/` returns 404.

| Family | Template | Meaning |
|---|---|---|
| Local | `/policy/api/v1/infra/...` | The default single-tenant scope on a local NSX Manager. |
| Global (Federation) | `/policy/api/v1/global-infra/...` | Objects owned by the Global Manager. |
| Project (multi-tenancy) | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/...` | Tenant-scoped objects. |
| VPC | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/...` | VPC-scoped security policies (9.1 VPC networking). |

Also note the separate **Global Manager appliance** spec: `9.1__nsx-global-policy.ops.json` has
`basePath: /global-manager/api/v1` (1,009 operations) and carries write verbs on `global-infra` paths
(`GlobalInfraPatchSecurityPolicyForDomain`, `GlobalInfraUpdateGroupForDomain`, …). **[SPEC]**
On the *local* manager's Policy API, `global-infra` DFW paths are **read-only** — the local spec exposes
only `GET` on `/global-infra/domains/{domain-id}/security-policies…` and `…/groups…`. **[SPEC]**
Writing to a federated policy means talking to the Global Manager, not the local manager.

---

## Groups

All rows **[SPEC — `9.1__nsx-policy.ops.json`]** unless noted.

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/domains/{domain-id}/groups` | `ListGroupForDomain` |
| GET | `/infra/domains/{domain-id}/groups/{group-id}` | `ReadGroupForDomain` |
| PATCH | `/infra/domains/{domain-id}/groups/{group-id}` | `PatchGroupForDomain` |
| PUT | `/infra/domains/{domain-id}/groups/{group-id}` | `UpdateGroupForDomain` |
| DELETE | `/infra/domains/{domain-id}/groups/{group-id}` | `DeleteGroup` |
| GET | `/infra/domains/{domain-id}/groups/{group-id}/member-types` | `GetMemberTypesForGroup` |
| GET | `/infra/domains/{domain-id}/groups/{group-id}/members/virtual-machines` | `GetGroupVMMembers` |
| GET | `/global-infra/domains/{domain-id}/groups[/{group-id}]` | `GlobalInfraListGroupForDomain` / `GlobalInfraReadGroupForDomain` (**read-only on the local manager**) |
| GET/PATCH/PUT/DELETE | `/orgs/{org-id}/projects/{project-id}/infra/domains/{domain-id}/groups[/{group-id}]` | project-scoped equivalents |

### Group body essentials

`Group` extends `PolicyConfigResource` and adds:

| Field | Type | Notes |
|---|---|---|
| `expression` | array of `Expression` | The membership criteria. |
| `extended_expression` | array of `Expression` | Identity/context extensions. |
| `group_type` | array | e.g. IP-address-only group typing. |
| `reference` | boolean (default `false`) | |
| `state` | enum `IN_PROGRESS` / `SUCCESS` / `FAILURE` | Read-only realization state. |

`Expression.resource_type` is **required** and one of: `Condition`, `ConjunctionOperator`,
`NestedExpression`, `IPAddressExpression`, `MACAddressExpression`, `ExternalIDExpression`,
`PathExpression`, `IdentityGroupExpression`, `GeoLocationExpression`. **[SPEC]**

- `Condition` requires `key` (`Tag`, `Name`, `OSName`, `ComputerName`, `NodeType`, `GroupType`, `ALL`,
  `IPAddress`, `PodCidr`, `ManagementInterface`, `OSVersion`), `member_type` (`VirtualMachine`,
  `Segment`, `SegmentPort`, `IPSet`, `Pod`, `Group`, …), and `value`; `operator` is one of `EQUALS`,
  `CONTAINS`, `STARTSWITH`, `ENDSWITH`, `NOTEQUALS`, `NOTIN`, `MATCHES`, `IN`. **[SPEC]**
- `PathExpression` requires `paths` (array of policy paths). **[SPEC]**

### Incremental expression edits — add/remove members without rewriting the group

A whole-group `PUT` is a read-modify-write race on a group that other automation also edits. Use the
per-expression sub-resource instead. The **`POST`** verb on these paths is the incremental
"add or remove members" operation; `PATCH` merges the expression; `DELETE` removes it.

| Verb | Path (append to `/policy/api/v1/infra/domains/{domain-id}/groups/{group-id}`) | operationId |
|---|---|---|
| POST | `/ip-address-expressions/{expression-id}` | `AddorRemoveGroupIPAddresses` |
| PATCH | `/ip-address-expressions/{expression-id}` | `PatchGroupIPAddressExpressionForDomain` |
| DELETE | `/ip-address-expressions/{expression-id}` | `DeleteGroupIPAddressExpression` |
| POST | `/mac-address-expressions/{expression-id}` | `AddorRemoveGroupMACAddresses` |
| PATCH·DELETE | `/mac-address-expressions/{expression-id}` | `PatchGroupMACAddressExpressionForDomain` / `DeleteGroupMACAddressExpression` |
| POST | `/path-expressions/{expression-id}` | `AddorRemoveGroupPathMembers` |
| PATCH·DELETE | `/path-expressions/{expression-id}` | `PatchGroupPathExpressionForDomain` / `DeleteGroupPathExpression` |
| POST | `/external-id-expressions/{expression-id}` | `AddorRemoveGroupExternalIDMembers` |
| PATCH·DELETE | `/external-id-expressions/{expression-id}` | `PatchGroupExternalIDExpressionForDomain` / `DeleteGroupExternalIDExpression` |

All **[SPEC]**. The `{expression-id}` addresses an *existing* expression inside the group's
`expression` array — read the group first to learn it.

---

## Security policies

A **security policy** is the container. A **rule** lives inside it. There is no bare "create a DFW rule"
endpoint — see the worked example.

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/domains/{domain-id}/security-policies` | `ListSecurityPoliciesForDomain` |
| GET | `/infra/domains/{domain-id}/security-policies/{security-policy-id}` | `ReadSecurityPolicyForDomain` |
| PATCH | `/infra/domains/{domain-id}/security-policies/{security-policy-id}` | `PatchSecurityPolicyForDomain` |
| PUT | `/infra/domains/{domain-id}/security-policies/{security-policy-id}` | `UpdateSecurityPolicyForDomain` |
| DELETE | `/infra/domains/{domain-id}/security-policies/{security-policy-id}` | `DeleteSecurityPolicyForDomain` |
| GET | `/infra/domains/{domain-id}/security-policies/{security-policy-id}/statistics` | `GetSecurityPolicyStatistics` |
| POST | `/infra/domains/{domain-id}/security-policies/{security-policy-id}?action=revise` | `ReviseSecurityPolicies` |
| GET | `/global-infra/domains/{domain-id}/security-policies[/{id}]` | `GlobalInfraListSecurityPoliciesForDomain` / `GlobalInfraReadSecurityPolicyForDomain` (read-only locally) |
| GET·PATCH·PUT·DELETE | `/orgs/{org-id}/projects/{project-id}/infra/domains/{domain-id}/security-policies[/{id}]` | `OrgsOrgIdProjectsProjectIdInfra*` |
| POST | `/orgs/{org-id}/projects/{project-id}/infra/domains/{domain-id}/security-policies/{id}?action=revise` | `OrgsOrgIdProjectsProjectIdInfraReviseSecurityPolicies` |
| GET·PATCH·PUT·DELETE | `/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/security-policies[/{id}]` | `ListVpcSecurityPolicies`, `GetVpcSecurityPolicy`, `PatchVpcSecurityPolicy`, `UpdateVpcSecurityPolicy`, `DeleteVpcSecurityPolicy` |
| GET | `/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/security-policies/realization-failures` | `GetVpcSecurityPolicyAlarms` |

All **[SPEC]**. This closes a gap in the prose research, which had confirmed only the **GET** verb on
a 9.1-pinned portal page and marked PATCH/PUT/DELETE, `?action=revise`, `/rules` and `/statistics` as
"structurally inferred, not doc-verified" for 9.1. **They are now spec-confirmed for 9.1.**

### SecurityPolicy body essentials

`SecurityPolicy` extends `Policy` (which extends `PolicyConfigResource`).

From `Policy` **[SPEC]**:

| Field | Type | Notes |
|---|---|---|
| `category` | string | See below. Drives evaluation precedence. |
| `sequence_number` | integer | Ordering **within** a category. Lower = earlier. |
| `scope` | array of paths | Applies the whole policy to specific groups (the "Applied To" field). |
| `stateful` | boolean | |
| `tcp_strict` | boolean | |
| `locked` | boolean (default `false`) | With `lock_modified_by` / `lock_modified_time`. |
| `scheduler_path` | string | Path to a `firewall-scheduler`. |
| `comments` | string | |
| `rule_count`, `is_default`, `internal_sequence_number` | read-mostly | |

From `SecurityPolicy` **[SPEC]**:

| Field | Type | Notes |
|---|---|---|
| `rules` | array of `Rule` | Lets you create the policy and its rules in **one** call. |
| `connectivity_preference` | enum | `ALLOWLIST`, `DENYLIST`, `ALLOWLIST_ENABLE_LOGGING`, `DENYLIST_ENABLE_LOGGING`, `NONE` |
| `connectivity_strategy` | enum | `WHITELIST`, `BLACKLIST`, `WHITELIST_ENABLE_LOGGING`, `BLACKLIST_ENABLE_LOGGING`, `NONE` (older naming; prefer `connectivity_preference`) |
| `logging_enabled` | boolean (default `false`) | |
| `default_rule_id` | integer | |
| `application_connectivity_strategy` | array | |

**Categories**, verbatim from the 9.1 spec **[SPEC]**: *"Policy framework provides five pre-defined
categories for classifying a security policy. They are "Ethernet","Emergency", "Infrastructure"
"Environment" and "Application". There is a pre-determined order in which the policy framework manages
the priority of these security policies. Ethernet category is for supporting layer 2 firewall rules.
The other four categories are applicable for layer 3 rules. Among them, the Emergency category has
the highest priority followed by Infrastructure, Environment and then Application rules. … If empty it
will have the least precedence w.r.t the above four categories."*

The spec also notes that for **user-created domains** (Edge/Gateway firewall), category is *"restricted
to "SharedPreRules" or "LocalGatewayRules" only"* — another reason P4 matters.

---

## Rules

| Verb | Path (append to `/policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}`) | operationId |
|---|---|---|
| GET | `/rules` | `ListSecurityRules` |
| GET | `/rules/{rule-id}` | `ReadSecurityRule` |
| PATCH | `/rules/{rule-id}` | `PatchSecurityRule` |
| PUT | `/rules/{rule-id}` | `UpdateSecurityRule` |
| DELETE | `/rules/{rule-id}` | `DeleteSecurityRule` |
| GET | `/rules/{rule-id}/statistics` | `GetRuleStatistics` |
| POST | `/rules/{rule-id}?action=revise` | `ReviseSecurityRule` |

Project-scoped and VPC-scoped equivalents exist with the same tail
(`OrgsOrgIdProjectsProjectIdInfraListSecurityRules`, `ListVpcPolicyRules`, `ReviseVpcSecurityRule`, …).
Federation `global-infra` rules are **GET-only** on the local manager
(`GlobalInfraListSecurityRules`, `GlobalInfraReadSecurityRule`, `GlobalInfraGetRuleStatistics`).
All **[SPEC]**.

### Rule body essentials

`Rule` = `BaseRule` + `action`. **[SPEC]**

| Field | Type | Default | Notes |
|---|---|---|---|
| `action` | enum | — | `ALLOW`, `DROP`, `REJECT`, `JUMP_TO_APPLICATION`. `DROP` = silent discard; `REJECT` = send RST/ICMP unreachable. |
| `source_groups` | array of string | — | **Group policy paths**, or the literal `ANY`. |
| `destination_groups` | array of string | — | Same. |
| `sources_excluded` | boolean | `false` | Negate the source match. |
| `destinations_excluded` | boolean | `false` | Negate the destination match. |
| `services` | array of string | — | Paths to `Service` objects (`/infra/services/<id>`). |
| `service_entries` | array of `ServiceEntry` | — | Inline service definitions — use instead of `services`. |
| `profiles` | array | — | Context profile paths (L7 / FQDN). |
| `scope` | array | — | "Applied To". Defaults to the policy's scope if omitted. |
| `direction` | enum | `IN_OUT` | `IN`, `OUT`, `IN_OUT`. |
| `ip_protocol` | enum | — | `IPV4`, `IPV6`, `IPV4_IPV6`. |
| `sequence_number` | integer | — | Ordering within the policy. |
| `disabled` | boolean | `false` | |
| `logged` | boolean | `false` | Firewall logging for this rule. |
| `notes`, `tag` | string | — | `tag` is stamped into log records. |
| `rule_id`, `is_default` | integer/boolean | — | System-assigned. |

### ServiceEntry (inline services)

`ServiceEntry.resource_type` is **required**, one of: `IPProtocolServiceEntry`, `IGMPTypeServiceEntry`,
`ICMPTypeServiceEntry`, `ALGTypeServiceEntry`, `L4PortSetServiceEntry`, `EtherTypeServiceEntry`,
`NestedServiceServiceEntry`. **[SPEC]**

`L4PortSetServiceEntry` **[SPEC]**:

| Field | Required | Notes |
|---|---|---|
| `l4_protocol` | **yes** | `TCP` or `UDP` |
| `destination_ports` | no | array of port or port-range strings |
| `source_ports` | no | array of port or port-range strings |

---

## Rule ordering and sequence

Three mechanisms stack, in this precedence order:

1. **Category** on the security policy (`Emergency` → `Infrastructure` → `Environment` → `Application`;
   `Ethernet` handles L2 separately). A policy with no category has the least precedence.
2. **`sequence_number`** on the security policy — orders policies *within* a category.
3. **`sequence_number`** on the rule — orders rules *within* a policy.

To reposition without recomputing every sequence number, use the imperative `?action=revise` form:

```
POST /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}/rules/{rule-id}?action=revise
     &operation=insert_before
     &anchor_path=/infra/domains/default/security-policies/<pol>/rules/<other-rule>
Body: the full Rule object
```

**[SPEC — `ReviseSecurityRule`]** Spec description, verbatim: *"This is used to re-order a rule within a
security policy."*

Query parameters **[SPEC]**:

| Param | Required | Values |
|---|---|---|
| `operation` | no (default `insert_top`) | `insert_top`, `insert_bottom`, `insert_after`, `insert_before` |
| `anchor_path` | no | *"The security policy/rule path if operation is 'insert_after' or 'insert_before'"* |

The **body is required** and is a full `Rule` object — `?action=revise` is a move-with-replace, not a
pure move. Read the rule first, then post it back with the position parameters.

`ReviseSecurityPolicies` (`POST …/security-policies/{id}?action=revise`) works the same way at policy
level with a `SecurityPolicy` body. **[SPEC]**

---

## Drafts (staged configuration)

Drafts let you assemble a change set and publish it atomically instead of writing live objects one at a
time. All **[SPEC]**.

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/drafts` | `ListDrafts` |
| GET | `/infra/drafts/{draft-id}` | `ReadDraft` |
| PUT | `/infra/drafts/{draft-id}` | `PutDraft` |
| PATCH | `/infra/drafts/{draft-id}` | `PatchDraft` |
| DELETE | `/infra/drafts/{draft-id}` | `DeleteDraft` |
| GET | `/infra/drafts/{draft-id}/aggregated` | `GetAggregatedConfigurationToBePublishedForDraft` |
| GET | `/infra/drafts/{draft-id}/aggregated_with_pagination` | `GetPolicyDraftPaginatedAggregatedConfigurationResult` |
| GET | `/infra/drafts/{draft-id}/complete` | `GetPreviewOfConfigurationAfterPublishOfDraft` |
| POST | `/infra/drafts/{draft-id}?action=publish` | `PublishDraft` |

`/complete` is the pre-flight: it returns *the configuration as it would look after publish*. Read it
before publishing a draft that touches production rules.

---

## Related DFW settings and query endpoints

All **[SPEC]**.

| Verb | Path (append to `/policy/api/v1`) | operationId | Notes |
|---|---|---|---|
| GET·PATCH·PUT | `/infra/settings/firewall/security` | `GetDfwFirewallConfiguration`, `PatchDfwFirewallConfiguration`, `PutDfwFirewallConfiguration` | Global DFW config. |
| GET | `/infra/settings/firewall/security/dependent-services` | `GetDistributedFirewallDependentServices` | Check before disabling DFW. |
| GET·PATCH·PUT | `/infra/settings/firewall/security/exclude-list` | `GetFirewallExcludeList`, `PatchExcludeList`, `PutExcludeList` | VMs exempt from DFW. |
| GET | `/infra/settings/firewall/security/exclude-list/members-count` | `GetFirewallExcludeListMembersCount` | |
| POST | `/infra/settings/firewall/security/exclude-list?action=filter` | `FilterFirewallExcludeList` | |
| GET | `/infra/settings/firewall/security/exclude-list?system_owned=true` | `GetInternalFirewallExcludeList` | System-owned exclusions. |
| GET | `/infra/firewall/policies` | `GetFilteredPolicies` | Flat, filtered query across domains. |
| GET | `/infra/firewall/rules` | `GetFilteredRules` | Flat, filtered rule query — use this instead of walking every policy. |
| POST | `/infra/settings/security/host-configuration-report` | `GenerateHostConfigReportInCsv` | CSV host security config report. **Not observed on the 9.0 DFW page.** |
| GET·PATCH·PUT | `/infra/settings/firewall/idfw/cluster/{cluster-id}` | `*ComputeClusterIdfwConfiguration` | Identity Firewall per cluster. |
| GET | `/infra/settings/firewall/idfw/user-session-data` | `GetUserSessionData` | |
| GET·…·PUT | `/infra/firewall-schedulers[/{firewall-scheduler-id}]` | `ListPolicyFirewallSchedulers`, … | Time-based rule application (`Policy.scheduler_path`). |
| GET·…·PUT | `/infra/firewall-session-timer-profiles[/{id}]` | `ListPolicyFirewallSessionTimerProfiles`, … | |
| GET | `/infra/context-profiles` | `ListPolicyContextProfiles` | L7 / FQDN profiles for `Rule.profiles`. |
| GET·…·PUT | `/infra/services[/{service-id}]` | `ListServicesForTenant`, `ReadServiceForTenant`, `PatchServiceForTenant`, `UpdateServiceForTenant`, `DeleteServiceForTenant` | Reusable service objects. |

**Bulk / hierarchical API:** `GET·PATCH·PUT /policy/api/v1/infra` (`ReadInfra`, `PatchInfra`,
`UpdateInfra`) accepts a nested tree so a whole security posture can be applied in one transaction.
`PATCH /global-infra` and `PATCH /orgs/{org-id}/projects/{project-id}/infra` also exist. **[SPEC]**
Powerful and correspondingly dangerous — a malformed hierarchical `PUT /infra` can delete objects you
did not mention. Prefer the scoped endpoints for targeted changes.

**Object discovery:** `GET /policy/api/v1/search/query` (`QuerySearch`) and
`GET /policy/api/v1/search/dsl` (`DslSearch`). **[SPEC]** This resolves the "search API" that the 9.1
docs reference but never give a path for; the prose research had it as unverified. Use it when the
hierarchical list endpoints are known to omit objects.

---

## Worked example — block tcp/3389 (RDP) from one existing group to another

**Goal:** a new security policy in the `default` domain containing one rule that drops TCP/3389 from
group `app-tier` to group `db-tier`. Both groups already exist.

The nesting is the point: **a rule lives under a security policy, which lives under a domain.**
There is no `POST /policy/api/v1/rules`. There is no `POST /policy/api/v1/infra/domains/default/rules`.
The only way to create a rule is `PUT`/`PATCH` at
`/infra/domains/{domain-id}/security-policies/{security-policy-id}/rules/{rule-id}` — or by embedding
the rule in the policy's `rules` array.

```bash
NSX=https://nsx-mgr.example.com
DOMAIN=default          # verify with P4 — do NOT assume; see Step 1
SRC_GROUP=app-tier
DST_GROUP=db-tier
POLICY=block-rdp-app-to-db
RULE=deny-rdp
```

> **Every path below is derived from `$DOMAIN`.** Nothing in this example hard-codes the literal
> `default`. Set `DOMAIN=prod-dfw` and the whole sequence still works. This matters because a rule
> whose `source_groups` / `destination_groups` / `scope` point at a `/infra/domains/default/...` path
> that does not exist in *your* domain is **accepted at write time and then silently never realises**
> — exactly the failure P4 and P5 exist to prevent.

### Step 0 — Authenticate (P2, A1)

```bash
curl -sS -c /tmp/nsx-session.txt -D /tmp/nsx-headers.txt \
  -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'j_username=svc-nsx-automation@example.com' \
  --data-urlencode 'j_password=<password>' \
  "$NSX/api/session/create"

XSRF=$(grep -i '^x-xsrf-token:' /tmp/nsx-headers.txt | tr -d '\r' | awk '{print $2}')
```

Pin every subsequent call to the **same manager node address** (A5), and send both the cookie jar and
the token:

```bash
AUTH=(-b /tmp/nsx-session.txt -H "x-xsrf-token: $XSRF" -H 'Content-Type: application/json')
```

### Step 1 — Confirm the domain exists (P4)

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN"
```
`GET /policy/api/v1/infra/domains/{domain-id}` — **[SPEC — `ReadDomainForInfra`]**. Expect 200.

### Step 2 — Confirm both groups exist and capture their **paths** (P5)

Capture the server-returned `path` of each group into a variable. **Do not assemble these strings
yourself** — project-scoped and Federation-scoped groups have longer paths, and a hand-built path is
the single most common cause of a rule that writes successfully and never realises.

```bash
SRC_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/groups/$SRC_GROUP" | jq -r '.path')
DST_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/groups/$DST_GROUP" | jq -r '.path')

# Fail closed: an empty or null path means the group does not exist in THIS domain.
for v in SRC_PATH DST_PATH; do
  case "${!v}" in
    ''|null) echo "FATAL: $v unresolved in domain '$DOMAIN' — fix P5 before continuing" >&2; exit 1 ;;
  esac
done

printf 'source: %s\ndest:   %s\n' "$SRC_PATH" "$DST_PATH"
```

`GET /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` — **[SPEC — `ReadGroupForDomain`]**.

With `DOMAIN=default` this prints `/infra/domains/default/groups/app-tier` and
`/infra/domains/default/groups/db-tier`. With `DOMAIN=prod-dfw` it prints the `prod-dfw` equivalents —
and every step below picks that up automatically, because they reference `$SRC_PATH` / `$DST_PATH`
rather than a literal.

### Step 3 — Create the security policy (the container)

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY" \
  -d "$(jq -n --arg dst "$DST_PATH" '{
    display_name:    "Block RDP app-tier to db-tier",
    description:     "Managed by automation",
    category:        "Application",
    sequence_number: 100,
    stateful:        true,
    scope:           [$dst]
  }')"
```

Note the `jq -n --arg` construction: the body is **built from the captured `$DST_PATH`**, not from a
literal `/infra/domains/default/...` string. Single-quoted `-d '{...}'` would not expand the variable
at all — that is precisely how a domain-parameterised example ends up writing `default` paths.

`PATCH /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}`
— **[SPEC — `PatchSecurityPolicyForDomain`]**.

Why `PATCH` and not `PUT`: `PATCH` is create-or-update and does not require `_revision`. A `PUT` here
would also work, but only if you **omit** `_revision` on the creating call and **supply** it on every
subsequent one (P7).

### Step 4 — Create the rule **inside** that policy

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE" \
  -d "$(jq -n --arg src "$SRC_PATH" --arg dst "$DST_PATH" '{
    display_name:       "Deny RDP 3389",
    action:             "DROP",
    source_groups:      [$src],
    destination_groups: [$dst],
    service_entries: [
      {
        resource_type:     "L4PortSetServiceEntry",
        display_name:      "tcp-3389",
        l4_protocol:       "TCP",
        destination_ports: ["3389"]
      }
    ],
    scope:           [$dst],
    direction:       "IN_OUT",
    ip_protocol:     "IPV4_IPV6",
    sequence_number: 10,
    logged:          true
  }')"
```

`PATCH /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}/rules/{rule-id}`
— **[SPEC — `PatchSecurityRule`]**.

Field notes:
- `action: "DROP"` silently discards. Use `"REJECT"` if the client should get an immediate RST/ICMP
  unreachable instead of a timeout. Both are valid `Rule.action` enum values **[SPEC]**.
- `service_entries` with an inline `L4PortSetServiceEntry` avoids depending on a predefined RDP
  `Service` object existing. The alternative is `"services": ["/infra/services/RDP"]`, which requires
  you to first confirm that service id via `GET /policy/api/v1/infra/services` (P6).
- `l4_protocol` is the only **required** field of `L4PortSetServiceEntry` **[SPEC]**; `destination_ports`
  is what makes it 3389.
- `scope` is "Applied To" — scoping the rule to `db-tier` limits which vNICs get the rule programmed,
  which matters for DFW rule-count scale. Omit it to inherit the policy's scope.

### Step 3+4 alternative — one call

Because `SecurityPolicy.rules` is an array of `Rule` **[SPEC]**, steps 3 and 4 collapse into a single
`PATCH` on the security policy with the rule nested in `rules`. This is atomic at the policy level and
is preferable when creating a policy and its rules together. It is **not** a way to add one rule to an
existing policy — a `PUT` with a partial `rules` array will remove the rules you left out.

### Step 5 — Verify realization

```bash
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE"

curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE/statistics"
```

`GET …/rules/{rule-id}` **[SPEC — `ReadSecurityRule`]** and
`GET …/rules/{rule-id}/statistics` **[SPEC — `GetRuleStatistics`]**. A 200 on the read confirms the
object exists; the statistics endpoint confirms the rule is programmed in the data path and shows hit
counts.

### Step 6 — Position the rule if order matters

```bash
curl -sS -X POST "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE?action=revise&operation=insert_top" \
  -d '<the full Rule body from step 5>'
```

**[SPEC — `ReviseSecurityRule`]**. Remember the body is mandatory.

### Step 7 — Log out

```bash
curl -sS -X POST "${AUTH[@]}" "$NSX/api/session/destroy"
```

**[SPEC — `DestroyAuthenticatedSession`]**

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| 403 on step 1, immediately after a successful step 0 | `X-XSRF-TOKEN` not sent (A2). |
| 403 mid-sequence after a pause | Session expired — **403, not 401** (A4). Re-authenticate and retry once. |
| 403 that persists after re-auth | Role too low — you need Enterprise Admin to write (P3). |
| 403 only on some calls, random | Cookie used against a different cluster node behind a VIP (A5). |
| 404 on step 3 | Wrong `{domain-id}` (P4), or you are on a project-scoped deployment and need the `orgs/.../projects/.../infra/` family. |
| 200 on step 4 but no traffic effect | Groups empty, or `scope` excludes the workloads, or a higher-precedence policy (Emergency/Infrastructure) already allows the flow. |
| Rule accepted but never realized | `source_groups`/`destination_groups` contain a path that does not resolve. Re-read the group `path` (P5). |
| 429 | Per-client rate limit exceeded. Back off. The exact ceiling is **conflicted** between spec and prose (see "Rate limits and pagination") — read the live value from `GET /api/v1/cluster/api-service` rather than assuming 100 or 250. |
| Rule written, `$SRC_PATH`/`$DST_PATH` empty | You skipped the Step 2 capture, or the group does not exist in `$DOMAIN`. The Step 2 guard exits before this can happen. |

---

## What is unverified for 9.1

- The 17 Manager-API / 9 Policy-API / 1 Autonomous-Edge operations removed in 9.1: **counts are
  published, paths are not.** See `../deltas.md`.
- The "199 overall concurrent requests" figure from 9.0 prose is contradicted by the 9.1 spec's
  `global_api_concurrency_limit: 500`. Flagged, not resolved.
- Whether the 9.0 constraints (one NSX per vCenter, narrowed NSX LB entitlement, single OIDC endpoint,
  principal-identity deprecation) still hold in 9.1 — the 9.1 support notes do not restate them.
- No authoritative VCF-owned-vs-operator-owned NSX object list exists (P8).
