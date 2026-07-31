# NSX Distributed Firewall / Security Policy — VCF 9.0

**Applies to:** NSX **9.0.0.0** (build 24733065), the NSX version in the VCF 9.0 Bill of Materials.
**Do not apply this file to VCF 9.1.** Use `../9.1/dfw.md` for 9.1 and `../deltas.md` for the change list.

> **Patch-line caveat.** The VCF 9.0 BOM page is maintained across the 9.0.x patch line and at time of
> research also listed VCF Installer 9.0.2.0. Separate NSX API doc sets exist for **9.0.0, 9.0.1 and
> 9.0.2**. If the target is on a 9.0.x patch, re-check the BOM — the NSX build will differ. The 9.0.1 /
> 9.0.2 build numbers are **unverified**.

---

## READ THIS FIRST — the evidence available for 9.0 is weaker than for 9.1

**There is no NSX OpenAPI specification published at the `9.0.0.0` tag of
`github.com/vmware/vcf-api-specs`.** The machine-extracted spec inventory confirms this: `nsx-policy`,
`nsx-manager` and `nsx-global-policy` are all recorded as **`9.0 present: no`**. Specs for those three
products appear only at the `9.1.0.0` tag (3,729 / 1,453 / 1,009 operations).

The consequences are concrete:

1. **Every endpoint in this file is sourced from prose documentation only** — version-pinned Broadcom
   pages under `developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/`,
   `dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.0.0/html/index.html`, and the VCF 9.0
   product docs. No 9.0 path in this file has been machine-confirmed against a specification.
2. **A path being spec-confirmed for 9.1 is not evidence about 9.0.** The 9.1 reference file marks many
   operations `[SPEC]`. Those tags mean nothing here. This file never presents a 9.1-spec-derived path
   as verified for 9.0 — where a path is known only from 9.1, it is marked
   **`[9.1-ONLY — NOT VERIFIED FOR 9.0]`** and you must confirm it on the appliance before use.
3. **The single reliable 9.0 verification route is the appliance itself:**
   `GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json`. The running NSX Manager serves
   the OpenAPI document that matches its own deployed build. See `../lookup.md`.

Evidence tags used below:

| Tag | Meaning |
|---|---|
| **[DOC-9.0]** | Read from a **9.0.0**-pinned Broadcom page. The strongest evidence available for 9.0. |
| **[DOC-9.0-partial]** | The path was seen on a 9.0.0 page but not every verb listed here was. |
| **[9.1-ONLY — NOT VERIFIED FOR 9.0]** | Known from the 9.1 doc set or 9.1 spec only. Confirm on the appliance first. |
| **[INFERRED]** | A shape or convention, not a verified fact. |

---

## Contents

- [**READ THIS FIRST** — 9.0 evidence is weaker than 9.1](#read-this-first--the-evidence-available-for-90-is-weaker-than-for-91) — what `[DOC-9.0]` / `[9.1-ONLY]` / `[INFERRED]` mean
- [**Prerequisites**](#prerequisites) — **read before any write**
  - [P1 — HTTPS reachability and trusted chain](#p1--you-can-reach-a-specific-nsx-manager-node-over-https-with-a-trusted-chain)
  - [P2 — Session authentication usable](#p2--session-authentication-is-usable-on-this-appliance)
  - [P3 — Role / permission level, and service accounts](#p3--you-hold-an-nsx-role-with-the-right-permission-level)
  - [P4 — Domain exists; correct domain id](#p4--the-domain-exists-and-you-are-using-the-right-domain-id)
  - [P5 — Groups exist; you have their policy paths](#p5--both-groups-already-exist-and-you-know-their-policy-paths)
  - [P6 — How you will express the service](#p6--you-know-how-you-will-express-the-service-portsprotocol)
  - [P7 — `_revision` and partial-patch contract](#p7--you-accept-the-concurrency-and-partial-patch-contract)
  - [P8 — VCF ownership of the objects you touch](#p8--vcf-ownership-of-the-nsx-objects-you-are-about-to-touch)
- [Authentication](#authentication)
  - [A1 create · A2 both credentials · A3 destroy](#a1--create-a-session)
  - [A4 — **expiry is 403, not 401**](#a4--trap-expiry-surfaces-as-403-forbidden-not-401)
  - [A5 — cookies are bound to one manager node](#a5--trap-cookies-are-bound-to-a-single-manager-node)
  - [A6 — other mechanisms](#a6--other-mechanisms) — incl. why the 9.1 token route is **not** available here
  - [Rate limits and pagination](#rate-limits-and-pagination-doc-90)
- [Base path and API surface](#base-path-and-api-surface) — Policy-only; `communication-maps`
- [Path families (multi-tenancy and federation)](#path-families-multi-tenancy-and-federation)
- [Groups](#groups) — endpoints, incremental expression edits, body
- [Security policies](#security-policies) — endpoints, body
- [Rules](#rules) — endpoints, body
- [Rule ordering and sequence](#rule-ordering-and-sequence)
- [Drafts (staged configuration)](#drafts-staged-configuration)
- [Related DFW settings](#related-dfw-settings)
- [**Worked example** — block tcp/3389 between two groups](#worked-example--block-tcp3389-rdp-from-one-existing-group-to-another) (Steps 0–7 + [failure decode](#failure-decode-for-this-sequence))
- [Summary: what remains unverified for 9.0](#summary-what-remains-unverified-for-90)

---

## Prerequisites

Everything in this section must be true **before** you issue any DFW call. Each item carries **four**
elements — if one is missing, the item is incomplete:

1. **What must be true** — the condition itself.
2. **How to verify it** — a concrete, *non-destructive* call or check. Never verify a permission or a
   contract by performing the production change it guards.
3. **Which version it applies to** — every item below applies to **NSX 9.0.0.0** unless it says otherwise.
4. **Whether it exists in the other version** — stated as a "9.1 difference" line on every item.

### P1 — You can reach a specific NSX Manager node over HTTPS with a trusted chain

- **Must be true:** an `https://<nsx-manager>` endpoint on 443, with its certificate chain in your trust
  store. VCF-deployed appliances default to VMCA-signed certificates, which are *not* publicly trusted;
  a stock HTTP client fails chain validation until you add the VMCA root or the enterprise CA. **[DOC-9.0]**
- **Verify:** `curl -sS -o /dev/null -w '%{http_code}\n' https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json`
  without `-k`. A TLS error means the trust store, not the endpoint, is the problem.
- **9.1 difference:** none known. Certificate auto-renewal covers NSX Manager in both versions.

### P2 — Session authentication is usable on this appliance

- **Must be true:** cookie-based authentication is enabled on the API service.
- **Verify:** `GET https://<nsx-manager>/api/v1/cluster/api-service` **[DOC-9.0 — this endpoint is
  documented for 9.0 as the place `session_timeout` is configured]**. Read the response for the session
  timeout and for a cookie-auth toggle.
- **9.1 difference:** in 9.1 the field name is spec-confirmed as `cookie_based_authentication_enabled`
  (spec default `true`), with the verbatim note that disabling it prevents new sessions via
  `/api/session/create`. **That field name is not confirmed for 9.0** — read the actual response body
  rather than assuming the key exists. If cookie auth is off, fall back to HTTP Basic or X.509.

### P3 — You hold an NSX role with the right permission level

- **Must be true:** **Enterprise Admin** (`enterprise_admin`) for any write (create/update/delete of
  security policies, rules, groups, drafts); **Auditor** (`auditor`) suffices for read-only. NSX 9.0
  ships **15 built-in roles**; Enterprise Admin = *"Full access (FA) — All permissions including
  Create, Read, Update, and Delete (CRUD)"*, Auditor = read-only. The other 13: Network Admin, Network
  Operator, Security Admin, Security Operator, Cloud Admin, Cloud Operator, Cloud Partner Admin, Load
  Balancer Admin, Load Balancer Operator, VPN Admin, Guest Introspection Partner Admin, Network
  Introspection Partner Admin, Support Bundle Collector. Custom roles are supported. **[DOC-9.0 — VCF 9.0
  NSX admin guide, role-based access control page]**
- **Verify — and note that a clean read-only verification is *not* spec-confirmable for 9.0.**
  There is no NSX specification at the `9.0.0.0` tag, so no 9.0 role-introspection endpoint can be
  machine-confirmed here. `GET /api/v1/aaa/role-bindings` (`GetAllRoleBindings`) is spec-confirmed for
  **9.1 only** — **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. It is very likely present in 9.0 (the RBAC
  role model is documented for 9.0), but it is not evidenced.
  **Safest documented alternative for 9.0, in this order:**
  1. Fetch the appliance's own OpenAPI document —
     `GET https://<nsx-manager>/api/v1/spec/openapi/nsx_api.json` — and search it for
     `aaa/role-bindings`. The running manager serves the spec matching its own build, so this
     converts the unverified endpoint into a verified one **for that appliance**. This is the only
     reliable 9.0 verification route (see the READ THIS FIRST section). If present, call it and read
     your binding's role.
  2. Failing that, confirm the *session* works with a harmless read against a known object —
     `GET /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` **[DOC-9.0]**. Note that
     `GET /policy/api/v1/infra/domains` (list) is **[9.1-ONLY — NOT VERIFIED FOR 9.0]**, so do not use
     it as the 9.0 smoke test.
  3. Only if neither is available, probe the write permission against a **throwaway object** — create
     and then delete a scratch security policy under a scratch id. A 403 with an authorization body
     (as opposed to a session-expiry 403, see A4) indicates the role is too low.
  **Do not verify write permission by attempting the intended production write.** An earlier revision
  of this file said to do exactly that; it verifies a firewall permission by making a firewall change,
  and if the role *is* sufficient the production change has already happened.
- **Service accounts:** **principal identities** are the documented mechanism for service-account-style
  API access in 9.0, and they are what an X.509 client certificate binds to — verbatim: *"NSX supports
  using an X.509 client certificate for authentication. The certificate is associated with a principal
  identity (a short name, similar to a username)."* **[DOC-9.0]**
  **Tension to be aware of:** the VCF 9.0 product support notes list Principal Identity accounts as
  **deprecated** — *"planned for deprecation in an upcoming release"* — directing operators to Federated
  Users via VCF SSO. So in 9.0 the only documented NSX-native service-account mechanism is
  simultaneously on the deprecation path. Use it, but plan the migration. **[DOC-9.0]**
- **VCF role mapping:** VCF **Administrator** and **SDDC Administrator** map to NSX `enterprise_admin`;
  VCF **Viewer** and **SDDC Viewer** map to NSX `auditor`. Role assignment is performed *in NSX*, not
  centrally, even when identity is federated. (This mapping table was sourced from a **9.1** page; treat
  its applicability to 9.0 as **[INFERRED]**.)
- **Identity sources in 9.0:** local accounts (SHA512-hashed passwords), Workspace ONE Access (vIDM),
  LDAP/AD/OpenLDAP, and VCF Identity Broker for SSO. Note that 9.0 narrowed OIDC support — *"NSX brings
  down the support of OpenID Connection endpoints from 10 to only one,"* which must be VMware Identity
  Broker. vIDM support is itself flagged deprecated in 9.0. **[DOC-9.0]**
- **9.1 difference:** the role list was not re-verified on a 9.1 page; 9.1 adds vCenter as an external
  identity provider (*"Starting in NSX 4.1.2, you can use vCenter server as an external identity
  provider"*). The principal-identity deprecation notice was **not restated** in the 9.1 support notes.

### P4 — The domain exists and you are using the right domain id

- **Must be true:** a DFW security policy lives under a **domain**. The conventional id is `default`.
  This is a convention, not a guarantee — user-created domains exist and restrict which rule categories
  are usable.
- **Verify (9.0):** there is **no 9.0-verified domain-list endpoint** in the research corpus. Confirm the
  domain indirectly: `GET /policy/api/v1/infra/domains/{domain-id}/security-policies` **[DOC-9.0]** or
  `GET /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` **[DOC-9.0]** returning 200 rather
  than 404 proves the domain resolves. Alternatively fetch the appliance's own OpenAPI document and
  search it for `/infra/domains`.
- **9.1 difference:** in 9.1, `GET /policy/api/v1/infra/domains` (`ListDomainForInfra`) and
  `GET·PATCH·PUT·DELETE /policy/api/v1/infra/domains/{domain-id}` are spec-confirmed. For 9.0 these are
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — very likely present, but not evidenced.
- **Never** assume `default` without a check on a multi-tenant or federated deployment.

### P5 — Both groups already exist and you know their **policy paths**

- **Must be true:** a rule references sources and destinations by **policy path string**
  (`/infra/domains/default/groups/<group-id>`), not by name and not by UUID. Create or confirm groups
  **first**; a rule whose group path does not resolve will be accepted and then fail to realize.
- **Verify:** `GET /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` **[DOC-9.0]** returns
  200. Record the `path` field from the response body and use that literal string in the rule.
- **9.0 gap:** the group **list** endpoint (`GET /infra/domains/{domain-id}/groups`) was **not**
  confirmed on a 9.0-pinned page — only the single-group read was. If you need to enumerate groups in
  9.0, confirm the list endpoint against the appliance spec first.
- **9.1 difference:** in 9.1 both list and read are spec-confirmed, plus per-expression incremental
  member operations (see P6 note and the Groups section).

### P6 — You know how you will express the service (ports/protocol)

- **Must be true:** the rule must carry either `services` (paths to `Service` objects) or
  `service_entries` (inline service definitions).
- **9.0 gap:** the `/policy/api/v1/infra/services` collection was **not covered** by the 9.0 prose
  research at all. It is spec-confirmed for 9.1 only — **[9.1-ONLY — NOT VERIFIED FOR 9.0]**.
- **Therefore, in 9.0 prefer inline `service_entries`.** An inline `L4PortSetServiceEntry` is part of the
  rule body, so it does not depend on a separate endpoint or on a predefined service object's id.
- **Verify:** if you want to use `services` instead, first confirm the collection exists on the
  appliance: `GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json` and search for
  `/infra/services`.

### P7 — You accept the concurrency and partial-patch contract

- **`_revision`:** every REST payload carries an integer `_revision`; it must be supplied on `PUT` and
  must match, or the update is rejected. The 9.0 API Guide notes that *"APIs whose URI begins with
  /policy have slightly different behavior"* for `_revision` and `PATCH`. The precise rule — *`_revision`
  must **not** be set when `PUT` creates a new `/policy` resource, but must be supplied on subsequent
  `PUT`s* — was read verbatim in the **9.1** guide. For 9.0 it is **[INFERRED]** from the 9.0 guide's
  weaker wording. Using `PATCH` for creates sidesteps the whole question.
- **Partial patch is off by default** and must be enabled explicitly before you rely on partial-object
  `PATCH` semantics: `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` with
  `{"enable_partial_patch": "true"}` **[DOC-9.0 — VCF 9.0 NSX admin guide]**.
- **Verify:** for `_revision`, read any existing policy object —
  `GET /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}` **[DOC-9.0]** —
  and confirm an integer `_revision` is present in the body; that is the value a subsequent `PUT` must
  echo. Do not probe the contract by issuing a deliberately stale `PUT` against a live object. For the
  partial-patch setting, a **`GET`** on `/policy/api/v1/system-config/nsx-partial-patch-config`
  (`GetPartialPatchConfiguration`) is spec-confirmed for **9.1 only** —
  **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. In 9.0, confirm the read verb exists by fetching the
  appliance's own OpenAPI document (`GET /api/v1/spec/openapi/nsx_policy_api.json`) and searching it
  for `nsx-partial-patch-config` before depending on it.
- **9.1 difference:** identical statements; 9.1's `_revision` rule is stated verbatim rather than by
  implication, and the `GET` on the partial-patch config is spec-confirmed there.

### P8 — VCF ownership of the NSX objects you are about to touch

- **There is no authoritative published list of which NSX objects VCF owns and which an operator may
  change directly.** This is a genuine gap in the documentation, not an omission here. What *is*
  documented for 9.0:
  - *"Starting with NSX 9.0, a standalone NSX installation or upgrade is not supported."* NSX must
    follow the VCF Bill of Materials; *"standalone upgrade of NSX is not supported."* **[DOC-9.0]**
  - *"VMware supports only one NSX instance for the same vCenter instance."* **[DOC-9.0]**
  - **NSX Embedded (NSXe) removed entirely** — *"NSX can no longer be installed or managed from
    vCenter."* **[DOC-9.0]**
  - **NSX Migration Coordinator removed.** **[DOC-9.0]**
  - **NSX Load Balancer entitlement narrowed** — general-purpose LB removed from VCF entitlement; Avi
    recommended; NSX LB retained only for VCF infrastructure and vSphere Supervisor use cases. Do not
    assume `/policy/api/v1/infra/lb-services` is a licensed general-purpose path. **[DOC-9.0]**
  - **NSX operates in FIPS-enabled mode by default and this cannot be deactivated.** **[DOC-9.0]**
  - 9.0 has **no** SDDC Manager network-sync reconciliation statement, so out-of-band NSX edits are less
    clearly supported in 9.0 than in 9.1.
- **Practical rule:** DFW security policies, rules and groups are user-authored security constructs and
  are the normal target of direct Policy API automation. Fabric objects (transport zones, edge clusters,
  host transport nodes, NSX Manager deployment) are VCF-lifecycle-owned — do not create or delete them
  via NSX directly. **This split is [INFERRED], not doc-stated.**
- **Verify — per object, before you touch it.** Since no authoritative ownership list exists, verify
  ownership *empirically and non-destructively*:
  1. **Read the object and inspect its origin markers.** `GET` the object and check `_system_owned` /
     `_protection` and `_create_user`. A `_system_owned: true`, a `_protection` value other than
     `NOT_PROTECTED`, or a `_create_user` that is an NSX/VCF service account rather than a human or
     your automation principal means **something else owns it — do not modify it**. These are fields
     of `PolicyConfigResource`, spec-confirmed for **9.1 only** —
     **[9.1-ONLY — NOT VERIFIED FOR 9.0]**; read the actual 9.0 response body rather than assuming the
     key names, or confirm them in the appliance's own OpenAPI document.
  2. **Prefer a draft as the verification harness** where drafts are available: stage the change and
     read the draft's post-publish preview, a dry run that touches nothing. See the Drafts section —
     note the draft endpoints are **[9.1-ONLY — NOT VERIFIED FOR 9.0]** unless confirmed on the
     appliance.
  3. **Fall back to the appliance spec.** `GET /api/v1/spec/openapi/nsx_policy_api.json` is the only
     reliable 9.0 verification route for whether any of the above endpoints exist on your build.
  Note these steps verify *"is this object system-owned"*, **not** *"is VCF entitled to overwrite my
  change"* — the latter is unanswerable from documentation. **[INFERRED]**
- **9.1 difference:** 9.1 adds SDDC Manager network sync, which reconciles *"network configuration
  changes done directly in vCenter or NSX Manager"* — the closest thing to permission for out-of-band
  edits, and it does not exist in 9.0. 9.1 also adds shared NSX Managers across workload domains.

---

## Authentication

The NSX 9.0.0 API Guide documents **four** mechanisms: HTTP Basic, session-based, X.509 client
certificate, and VMC token exchange (not applicable on-prem). **[DOC-9.0]**

### A1 — Create a session

```
POST https://<nsx-manager>/api/session/create
Content-Type: application/x-www-form-urlencoded

j_username=<user>&j_password=<password>
```

**[DOC-9.0 — NSX 9.0.0 API Guide, the 9.0.0 `api_usage_user_authentication` page, and the VCF 9.0 NSX
admin guide]**

Verbatim from the 9.0.0 reference: *"Authenticates using the given username and password. If successful,
the HTTP response headers will contain a Set-Cookie header and an X-XSRF-TOKEN header."* … *"Both of
these headers should be sent with subsequent API requests."*

The cookie name observed in the VCF 9.0 admin guide is **`JSESSIONID`**. **[DOC-9.0]**

### A2 — Send **both** credentials on every subsequent request

`JSESSIONID` alone is **not** sufficient. Every subsequent call needs:

```
Cookie: JSESSIONID=<value>
X-XSRF-TOKEN: <value>
```

Omitting `X-XSRF-TOKEN` on a write is a common cause of an unexplained rejection.

Verbatim 9.0 examples **[DOC-9.0 — VCF 9.0 NSX admin guide]**:

```bash
curl -i -k -c session.txt -X POST \
  -d 'j_username=admin@example.com&j_password=SecretPwsd3c4d' \
  https://<nsx-manager>/api/session/create 2>&1 > response.txt

curl -k -b session.txt -H "x-xsrf-token: 5a764b19-5ad2-4727-974d-510acbc171c8" \
  https://<nsx-manager>/policy/api/v1/infra/segments
```

URL-encode the password: *"`+` and other special characters in passwords must be URL-encoded."* **[DOC-9.0]**

### A3 — Destroy the session when done

```
POST https://<nsx-manager>/api/session/destroy
```

Verbatim: *"Unauthenticates and makes the provided session cookie invalid. The set-cookie and
x-xsrf-token headers obtained from an earlier call to /api/session/create should be provided in the HTTP
headers of this request."* **[DOC-9.0]** — send the cookie **and** the token header.

### A4 — Trap: expiry surfaces as **403 Forbidden, not 401**

Default session inactivity timeout is **1800 seconds (30 minutes)**, configurable via
`PUT https://<nsx-manager>/api/v1/cluster/api-service` (`session_timeout`). **[DOC-9.0]**

**Evidence caveat, stated honestly:** the verbatim sentence *"NSX Manager responds with a 403 Forbidden
HTTP response"* on session expiry was read on the **9.1**-pinned admin-guide page. The 9.0-pinned page
documents the timeout and the cookie mechanics but **does not** contain that sentence. So for 9.0 this is
**[9.1-ONLY — NOT VERIFIED FOR 9.0]** as a documented statement.

**Handle it anyway.** The behavior is a property of the shared NSX reverse-proxy session layer and the
underlying flow is identical in both versions. A client that only re-authenticates on 401 will spin
forever if 9.0 behaves the same way, and treating 403 as a re-auth trigger is harmless if it does not.
**Re-authenticate on 403, retry once; a second 403 means authorization (P3), not expiry.**

### A5 — Trap: cookies are bound to a **single manager node**

Session cookies are **manager-node-specific and cannot be reused across cluster nodes.** **[DOC-9.0 — the
verbatim operational note is on the 9.0-pinned admin-guide page]**

If you talk to a cluster VIP or a load balancer that distributes across members, a cookie minted on node
A will fail on node B — presenting as an intermittent, apparently random authentication failure. **Pin
the client to one node's address, or re-authenticate per node.**

### A6 — Other mechanisms

- **HTTP Basic:** verbatim — *"To authenticate a request using HTTP Basic authentication, the caller's
  credentials are passed using the 'Authorization' header."* Header form
  `Authorization: Basic YWRtaW46YWRtaW4=`; example
  `curl -k -u USERNAME:PASSWORD https://MANAGER/api/v1/logical-ports`. **[DOC-9.0]**
- **X.509 client certificate:** bound to a **principal identity**; `curl --key <keyfile> --cert <certfile>`. **[DOC-9.0]**
- **VMC token exchange:** documented, not applicable to on-prem VCF. **[DOC-9.0]**
- **No JWT/bearer flow against NSX Manager is documented for 9.0** — and, unlike 9.1, none can be
  confirmed either way, because there is no NSX specification at the `9.0.0.0` tag. Per-product
  credentials (the NSX session cookie here) are the documented 9.0 route.
- **Token-based principal identity (VCF SSO → NSX): [9.1-ONLY — NOT VERIFIED FOR 9.0].** The 9.1 spec
  confirms `POST·GET·DELETE /api/v1/trust-management/token-principal-identities` and the VIDB OIDC
  endpoint configuration operations (see `../9.1/dfw.md` § A7). **None of that is evidence about 9.0**
  and it is deliberately not reproduced here. If you need a non-interactive service account on 9.0,
  the documented mechanism is the classic **principal identity** with an X.509 client certificate
  (P3) — which is itself deprecation-flagged in the 9.0 support notes. If you want to know whether
  your 9.0 build carries the token route anyway, fetch
  `GET https://<nsx-manager>/api/v1/spec/openapi/nsx_api.json` and search for
  `token-principal-identities`; the appliance's own spec is the only authority for 9.0.

### Rate limits and pagination `[DOC-9.0]`

- Per-client **100 requests/second** — HTTP **429** on exceed.
- Per-client **40 concurrent requests**.
- Overall server maximum **199 concurrent requests**. *(Note: the 9.1 spec declares
  `global_api_concurrency_limit` with `default: 500`. The 199 figure is what the 9.0 guide states; the
  discrepancy is unresolved and may be a genuine 9.0→9.1 change.)*
- Pagination: `ListResult` responses default to **1000 results**; clients must follow the `cursor`
  property until it is absent.

---

## Base path and API surface

**Policy API base path: `/policy/api/v1`.** **[DOC-9.0]**

Verbatim from the VCF 9.0 NSX admin guide:

> *"Beginning with VCF 9.0, the NSX Manager interface provides a single mode, Policy mode, for
> configuring resources. The Manager mode and Manager API provided by NSX 4.x and earlier are no longer
> supported."*
>
> *"The Policy API is part of the NSX REST APIs and contains URIs that begin with /policy/api."*

Corroborated by the VCF 9.0 release-notes NSX support notes: *"VMware no longer supports the NSX Manager
APIs and NSX Advanced UIs."* — new deployments should use Policy APIs and Policy UIs. **[DOC-9.0]**

**Consequence for an agent: never configure a DFW object through `/api/v1`.** There is no supported
Manager-API path to a distributed firewall rule in 9.0.

`/api/v1` survives for a narrow, non-policy set **[DOC-9.0]**:

| Surviving `/api/v1` use | Example |
|---|---|
| Session lifecycle | `POST /api/session/create`, `POST /api/session/destroy` |
| Node / cluster admin | `PUT /api/v1/cluster/api-service` (session timeout) |
| Fabric admin | node and fabric management endpoints |
| OpenAPI spec retrieval | `GET /api/v1/spec/openapi/nsx_policy_api.{yaml,json}`, `nsx_api.{yaml,json}` |

The Manager networking API still *exists* in 9.0 (the Basic-auth example in the guide targets
`/api/v1/logical-ports`) but is unsupported for logical networking. A concrete example of a Manager-API
networking endpoint carrying an explicit deprecation notice in the 9.0.0 doc set:
`GET /api/v1/logical-routers/{logical-router-id}/nat/rules/{rule-id}` — *"This endpoint is deprecated as
of version 9.0."* **[DOC-9.0]**

Note the layering: the API Guide itself describes both surfaces neutrally — *"NSX Manager API: APIs for
NSX administration; node and cluster management APIs and fabric management APIs"* vs *"NSX Policy Manager
API: APIs for managing logical networking"* — and *"makes no recommendation about which to use."* The
**product documentation** is the authoritative Policy-only statement. Follow the product docs.

### Legacy: `communication-maps`

The 9.0.0 DFW reference page listed the older **`communication-maps` / `communication-entries`** tree as
**deprecated**. **[DOC-9.0]** (In 9.1 every operation on that tree is explicitly flagged `deprecated:
true` in the spec.) `security-policies` / `rules` is the current naming in both versions. Do not emit
`communication-maps` paths.

---

## Path families (multi-tenancy and federation)

| Family | Template | Evidence for 9.0 |
|---|---|---|
| Local | `/policy/api/v1/infra/...` | **[DOC-9.0]** |
| Global (Federation) | `/policy/api/v1/global-infra/...` | **[DOC-9.0]** — confirmed for groups, segments, Tier-0/Tier-1, transport zones, edge clusters on 9.0.0 pages |
| Project (multi-tenancy) | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/...` | **[DOC-9.0]** — confirmed for groups and segments on 9.0.0 pages |
| VPC | `/policy/api/v1/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/security-policies/...` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — VPCs exist in 9.0, but VPC-scoped *security-policy* paths were confirmed only in the 9.1 spec |

These families are **not** interchangeable: reading a project-scoped policy through `/infra/` returns 404.

**Specifically confirmed on 9.0.0-pinned pages for DFW objects:**
`GET /policy/api/v1/global-infra/domains/{domain-id}/groups/{group-id}` and
`GET /policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/domains/{domain-id}/groups/{group-id}`.
**[DOC-9.0]**
Project-scoped **security-policy** paths were **not** confirmed on a 9.0.0 page — they are
**[9.1-ONLY — NOT VERIFIED FOR 9.0]**.

---

## Groups

| Verb | Path (append to `/policy/api/v1`) | Evidence |
|---|---|---|
| GET | `/infra/domains/{domain-id}/groups/{group-id}` | **[DOC-9.0]** |
| GET | `/global-infra/domains/{domain-id}/groups/{group-id}` | **[DOC-9.0]** |
| GET | `/orgs/{org-id}/projects/{project-id}/infra/domains/{domain-id}/groups/{group-id}` | **[DOC-9.0]** |
| GET | `/infra/domains/{domain-id}/groups` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| PATCH·PUT·DELETE | `/infra/domains/{domain-id}/groups/{group-id}` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — the 9.0 page confirmed only the read verb. The write verbs almost certainly exist (a group has to be creatable), but they were not evidenced on a 9.0.0 page. Confirm against the appliance spec. |
| GET | `/infra/domains/{domain-id}/groups/{group-id}/member-types` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |

### Incremental expression edits (add/remove members without rewriting the group)

```
PATCH·POST·DELETE /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}/ip-address-expressions/{expression-id}
PATCH·POST·DELETE /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}/mac-address-expressions/{expression-id}
PATCH·POST·DELETE /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}/path-expressions/{expression-id}
PATCH·POST·DELETE /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}/external-id-expressions/{expression-id}
```

The **`POST`** verb performs the incremental *"add or remove members"* operation without rewriting the
whole group — which matters because a whole-group `PUT` is a read-modify-write race against any other
automation editing the same group.

**Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0].** This entire sub-resource family was confirmed on a
**9.1.0** page and in the 9.1 spec (`AddorRemoveGroupIPAddresses`, `AddorRemoveGroupMACAddresses`,
`AddorRemoveGroupPathMembers`, `AddorRemoveGroupExternalIDMembers`). It was **not** listed on any 9.0.0
page in the research corpus. **Confirm against the appliance's own spec before relying on it in 9.0.** If
it is absent, fall back to a read-modify-`PUT` of the whole group with `_revision` supplied (P7).

### Group body essentials

`Group` carries an `expression` array (and `extended_expression`). Each expression has a required
`resource_type` from: `Condition`, `ConjunctionOperator`, `NestedExpression`, `IPAddressExpression`,
`MACAddressExpression`, `ExternalIDExpression`, `PathExpression`, `IdentityGroupExpression`,
`GeoLocationExpression`. `Condition` requires `key`, `member_type` and `value`; `PathExpression` requires
`paths`.

**Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for the exact enum contents — these were read from the
9.1 spec's schema definitions. The 9.0 research did not capture group schema bodies. The *structure*
(`expression` array of typed expressions) is stable Policy-API design and is **[INFERRED]** for 9.0.
Read an existing group with `GET …/groups/{group-id}` and mirror its shape — that is the safest way to
get 9.0 group bodies right.

---

## Security policies

A **security policy** is the container. A **rule** lives inside it. There is no bare "create a DFW rule"
endpoint.

All rows in this table are **[DOC-9.0]** — read from the 9.0.0-pinned distributed-firewall reference
page, which is the single richest 9.0 DFW source in the corpus.

| Verb | Path (append to `/policy/api/v1`) |
|---|---|
| GET | `/infra/domains/{domain-id}/security-policies` |
| GET | `/infra/domains/{domain-id}/security-policies/{security-policy-id}` |
| PATCH | `/infra/domains/{domain-id}/security-policies/{security-policy-id}` |
| PUT | `/infra/domains/{domain-id}/security-policies/{security-policy-id}` |
| DELETE | `/infra/domains/{domain-id}/security-policies/{security-policy-id}` |
| POST | `/infra/domains/{domain-id}/security-policies/{security-policy-id}?action=revise` |

Not confirmed for 9.0:

| Verb | Path | Evidence |
|---|---|---|
| GET | `/infra/domains/{domain-id}/security-policies/{security-policy-id}/statistics` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — the 9.0 page listed **rule** statistics but not **policy** statistics |
| GET | `/global-infra/domains/{domain-id}/security-policies[/{id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| any | `/orgs/{org-id}/projects/{project-id}/infra/domains/{domain-id}/security-policies[/{id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |

### SecurityPolicy body essentials

Key fields: `display_name`, `description`, `category`, `sequence_number`, `scope` (the "Applied To"
group paths), `stateful`, `tcp_strict`, `locked`, `scheduler_path`, `logging_enabled`,
`connectivity_preference` / `connectivity_strategy`, and `rules` (an array of `Rule`, letting a policy
and its rules be created in one call).

**Categories** — five pre-defined categories classify a security policy: **Ethernet**, **Emergency**,
**Infrastructure**, **Environment**, **Application**. `Ethernet` is for L2 rules; the other four apply to
L3. Priority order: Emergency > Infrastructure > Environment > Application. A policy with an empty
category has the least precedence.

**Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for the field list and category semantics — these were
read from the 9.1 spec's `Policy` / `SecurityPolicy` schema definitions. The 9.0 research captured DFW
*paths* but not DFW *schemas*. The category model is long-standing NSX Policy design and is
**[INFERRED]** to be identical in 9.0; confirm by reading an existing policy or by fetching the
appliance's own spec.

---

## Rules

All rows **[DOC-9.0]** — from the 9.0.0-pinned distributed-firewall reference page.

| Verb | Path (append to `/policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}`) |
|---|---|
| GET | `/rules` |
| GET | `/rules/{rule-id}` |
| PATCH | `/rules/{rule-id}` |
| PUT | `/rules/{rule-id}` |
| DELETE | `/rules/{rule-id}` |
| GET | `/rules/{rule-id}/statistics` |
| POST | `/rules/{rule-id}?action=revise` |

This is the strongest part of the 9.0 evidence: the full policy + rule CRUD sub-tree, `?action=revise`
and `/statistics` were all listed on a single 9.0.0-pinned page.

### Rule body essentials

Key fields: `action` (`ALLOW`, `DROP`, `REJECT`, `JUMP_TO_APPLICATION`), `source_groups`,
`destination_groups` (arrays of group **policy paths**, or the literal `ANY`), `sources_excluded` /
`destinations_excluded`, `services` (paths) **or** `service_entries` (inline), `profiles` (context
profiles), `scope` ("Applied To"), `direction` (`IN` / `OUT` / `IN_OUT`, default `IN_OUT`), `ip_protocol`
(`IPV4` / `IPV6` / `IPV4_IPV6`), `sequence_number`, `disabled` (default `false`), `logged` (default
`false`), `notes`, `tag`.

Inline service entries use `resource_type` from `IPProtocolServiceEntry`, `IGMPTypeServiceEntry`,
`ICMPTypeServiceEntry`, `ALGTypeServiceEntry`, `L4PortSetServiceEntry`, `EtherTypeServiceEntry`,
`NestedServiceServiceEntry`. `L4PortSetServiceEntry` requires `l4_protocol` (`TCP` | `UDP`) and accepts
`destination_ports` / `source_ports`.

**Evidence: [9.1-ONLY — NOT VERIFIED FOR 9.0]** for the field names, enum values and defaults — read
from the 9.1 spec's `BaseRule` / `Rule` / `ServiceEntry` / `L4PortSetServiceEntry` definitions. The 9.0
research captured rule *paths* but not rule *schemas*. **[INFERRED]** to be identical in 9.0.
**Before writing a rule in 9.0, `GET` an existing rule and mirror its field names.** That is a one-call
check that removes all of this uncertainty.

---

## Rule ordering and sequence

Three mechanisms stack, in this precedence order:

1. **Category** on the security policy (Emergency → Infrastructure → Environment → Application; Ethernet
   handles L2 separately). Uncategorized policies have the least precedence.
2. **`sequence_number`** on the security policy — orders policies within a category.
3. **`sequence_number`** on the rule — orders rules within a policy.

To reposition without recomputing sequence numbers, use the imperative form **[DOC-9.0 — the
`?action=revise` endpoint itself is 9.0-confirmed]**:

```
POST /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}/rules/{rule-id}?action=revise
POST /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}?action=revise
```

Query parameters `operation` (`insert_top` — the default — `insert_bottom`, `insert_after`,
`insert_before`) and `anchor_path` (the policy/rule path when using `insert_after` / `insert_before`),
plus a **mandatory body** containing the full object, are
**[9.1-ONLY — NOT VERIFIED FOR 9.0]** — those parameter names and the "body required" fact were read
from the 9.1 spec. The 9.0 page confirmed the endpoint exists but not its parameters. Confirm against
the appliance spec before scripting a reorder in 9.0.

---

## Drafts (staged configuration)

Drafts let you assemble a change set and publish it atomically instead of writing live objects one at a
time.

| Verb | Path (append to `/policy/api/v1`) | Evidence |
|---|---|---|
| GET·PUT·PATCH·DELETE | `/infra/drafts/{draft-id}` | **[DOC-9.0]** |
| POST | `/infra/drafts/{draft-id}?action=publish` | **[DOC-9.0]** |
| GET | `/infra/drafts` (list) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| GET | `/infra/drafts/{draft-id}/complete` (post-publish preview) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| GET | `/infra/drafts/{draft-id}/aggregated`, `/aggregated_with_pagination` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |

---

## Related DFW settings

| Verb | Path (append to `/policy/api/v1`) | Evidence |
|---|---|---|
| GET·PATCH·PUT | `/infra/settings/firewall/security` (global DFW config) | **[DOC-9.0]** |
| GET·PATCH·PUT | `/infra/settings/firewall/security/exclude-list` (VMs exempt from DFW) | **[DOC-9.0]** |
| — | Identity Firewall (IDFW) endpoints | present on the 9.0.0 DFW page **[DOC-9.0-partial]** — the page listed an IDFW group but individual paths were not captured |
| GET | `/infra/firewall/policies`, `/infra/firewall/rules` (flat filtered queries) | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| POST | `/infra/settings/security/host-configuration-report` (CSV) | **[9.1-ONLY]** — explicitly *not observed* on the 9.0 DFW page; treated as a 9.1 addition, see `../deltas.md` |
| GET | `/search/query`, `/search/dsl` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** — the search API is referenced in prose in both doc sets but its concrete path was only resolvable from the 9.1 spec |
| GET·PATCH·PUT·DELETE | `/infra/services[/{service-id}]` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** (see P6) |
| GET·PATCH·PUT | `/infra/context-profiles` | **[9.1-ONLY — NOT VERIFIED FOR 9.0]** |
| PATCH | `/system-config/nsx-partial-patch-config` | **[DOC-9.0]** |

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

`POST /api/session/create` — **[DOC-9.0]**. Pin every subsequent call to the **same manager node
address** (A5) and send both the cookie jar and the token:

```bash
AUTH=(-b /tmp/nsx-session.txt -H "x-xsrf-token: $XSRF" -H 'Content-Type: application/json')
```

### Step 1 — Confirm the domain resolves (P4)

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies"
```

`GET /policy/api/v1/infra/domains/{domain-id}/security-policies` — **[DOC-9.0]**. A 200 (even with an
empty result list) proves the domain resolves; a 404 means the domain id is wrong.

**Why not `GET /infra/domains`:** that list endpoint is not verified for 9.0 (P4). This call is.

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

`GET /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` — **[DOC-9.0]**.

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

`PATCH /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}` — **[DOC-9.0]**.

Why `PATCH` and not `PUT`: `PATCH` is create-or-update and does not require `_revision`. `PUT` also works
but you must **omit** `_revision` on the creating call and **supply** it on every subsequent one, and
that exact rule is only doc-verbatim for 9.1 (P7). `PATCH` sidesteps it.

The body field names here are **[INFERRED]** for 9.0 (see the SecurityPolicy body note above). If step 3
returns a 400, `GET` an existing security policy in the same domain and mirror its field names.

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
— **[DOC-9.0]** for the path and verb; **[INFERRED]** for the body field names.

Field notes:
- `action: "DROP"` silently discards. `"REJECT"` sends an RST/ICMP unreachable instead.
- **Inline `service_entries` is deliberately chosen over `"services": ["/infra/services/RDP"]`** because
  the `/infra/services` collection is not verified for 9.0 (P6). Inlining keeps the whole service
  definition inside the rule body.
- `scope` is "Applied To" — scoping to `db-tier` limits which vNICs get the rule programmed, which
  matters for DFW rule-count scale. Omit it to inherit the policy's scope.

### Step 3+4 alternative — one call

`SecurityPolicy` carries a `rules` array, so steps 3 and 4 collapse into a single `PATCH` on the security
policy with the rule nested under `rules`. Atomic at the policy level and preferable when creating a
policy and its rules together. It is **not** a way to add one rule to an existing policy — a `PUT` with a
partial `rules` array removes the rules you left out. (The `rules` array is **[INFERRED]** for 9.0.)

### Step 5 — Verify realization

```bash
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE"

curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE/statistics"
```

Both **[DOC-9.0]**. A 200 on the read confirms the object exists; the statistics endpoint confirms the
rule is programmed in the data path and shows hit counts.

### Step 6 — Position the rule if order matters

```bash
curl -sS -X POST "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE?action=revise&operation=insert_top" \
  -d '<the full Rule body from step 5>'
```

The endpoint is **[DOC-9.0]**; the `operation` / `anchor_path` parameter names and the
body-is-mandatory fact are **[9.1-ONLY — NOT VERIFIED FOR 9.0]**. If the parameters are rejected, fall
back to setting `sequence_number` explicitly on each rule via `PATCH`.

### Step 7 — Log out

```bash
curl -sS -X POST "${AUTH[@]}" "$NSX/api/session/destroy"
```

**[DOC-9.0]**

### Failure decode for this sequence

| Symptom | Most likely cause |
|---|---|
| 403 on step 1, immediately after a successful step 0 | `X-XSRF-TOKEN` not sent (A2). |
| 403 mid-sequence after a pause | Session expired. Treat 403 as re-auth (A4) — note the 403-on-expiry statement is 9.1-doc-verified, not 9.0-doc-verified. |
| 403 that persists after re-auth | Role too low — Enterprise Admin is required to write (P3). |
| 403 only on some calls, apparently random | Cookie used against a different cluster node behind a VIP (A5) — this **is** 9.0-doc-verified. |
| 404 on step 1 | Wrong `{domain-id}` (P4). |
| 400 on step 3 or 4 | Body field name mismatch — the 9.0 schemas are inferred. `GET` an existing object and mirror it. |
| 200 on step 4 but no traffic effect | Groups empty, `scope` excludes the workloads, or a higher-precedence policy (Emergency/Infrastructure) already allows the flow. |
| Rule accepted but never realized | `source_groups`/`destination_groups` contain a path that does not resolve. Re-read the group `path` (P5). |
| 429 | Rate limit — 100 req/s per client per 9.0 prose. Back off. |
| Rule written, `$SRC_PATH`/`$DST_PATH` empty | You skipped the Step 2 capture, or the group does not exist in `$DOMAIN`. The Step 2 guard exits before this can happen. |

---

## Summary: what remains unverified for 9.0

The honest bottom line — a list of things you should confirm on the appliance rather than trust here.

1. **No machine-readable NSX spec exists at the 9.0.0.0 tag** of the public corpus. Nothing in this file
   is spec-confirmed for 9.0.
2. **DFW schemas** (rule/policy/group field names, enum values, defaults) were never captured from a
   9.0-pinned source. Everything schema-related is inferred from the 9.1 spec. Mitigation: `GET` an
   existing object and mirror its shape — one call.
3. **Group write verbs** (PATCH/PUT/DELETE) and the **group list** endpoint were not confirmed on a 9.0
   page.
4. **Group incremental-expression sub-resources** (`*-expressions/{expression-id}`) were confirmed for
   9.1 only.
5. **Project-scoped security-policy paths** were confirmed for 9.1 only. Project-scoped **group** paths
   *were* confirmed for 9.0.
6. **`/infra/services`, `/infra/context-profiles`, `/infra/firewall/policies`, `/infra/firewall/rules`,
   `/search/query`, `/search/dsl`** — none confirmed for 9.0.
7. **`?action=revise` query parameters** and the mandatory-body requirement were confirmed for 9.1 only.
8. **403-on-session-expiry** is documented on the 9.1 page, not the 9.0 page.
9. **`_revision`-on-create-vs-update** is stated verbatim only in the 9.1 guide; the 9.0 guide only says
   `/policy` URIs "have slightly different behavior."
10. **The 9.0.1 / 9.0.2 NSX build numbers** are unverified — re-check the BOM for the exact patch.
11. **No authoritative VCF-owned-vs-operator-owned NSX object list** exists for either version (P8).
12. **No bearer/JWT auth flow** against NSX Manager is documented for 9.0.

**The one call that resolves most of this:**
`GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json` — the running appliance serves the
OpenAPI document for its own build. See `../lookup.md`.
