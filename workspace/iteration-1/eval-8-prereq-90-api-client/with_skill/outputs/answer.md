# Service account with a long-lived read-only API token — on VCF 9.0

## The short version, and it's the important part

**The thing you're describing does not exist in VCF 9.0.**

SSO-issued, role-scoped API tokens — the "create an API client, generate a long-lived
API token, scope it to a role" flow you've almost certainly read about — is a **9.1
capability**. In 9.0 there is no VCF SSO API client, no SSO-issued API token, no OAuth-app
management, and no emergency access client. There is no *Fleet Management → Identity &
Access → API Clients* node to click; the navigation item isn't there.

Two independent checks back this up:

- **Doc tree:** the 9.0 "Managing VMware Cloud Foundation Operations SSO" tree contains only
  SSO overview, reset, change IdP, change deployment mode, edit IdP config, additional
  component configurations, deregister, and change identity management. No API client, API
  token, OAuth client or role management page.
- **Spec (the stronger check):** the `vcf-operations` OpenAPI spec at git tag `9.0.0.0` has
  **0 operations** under `/api/fleet-management/iam/**`. The `9.1.0.0` tag has **70**. There is
  no `.../ssorealms/{id}/api-tokens`, no `.../api-clients`, no `.../oauth-apps`, no
  `.../iam/settings` route to call on a 9.0 appliance.

So the goal — stop using your personal admin creds for automation — is completely
achievable on 9.0, but the shape of the answer is different: **per-product service
accounts with per-product credentials and per-product read-only roles**, not one fleet-wide
token.

Also worth saying plainly up front: **nothing in 9.0 is "long-lived" in the token sense.**
The longest-lived credential in the platform is 90 days (VCF Automation) and everything
else is measured in hours. Your automation will need a credential store and a refresh
loop regardless. Plan for that now rather than discovering it at 03:00.

---

## What "service account" means per product in 9.0

There is no single VCF token. Each product has its own auth flow, its own role model, and
its own lifetime. Build one account per product your automation actually touches — don't
create four if you only read from two.

| Product | Service-account mechanism | Credential lifetime | Read-only role |
|---|---|---|---|
| SDDC Manager | Local/AD user assigned an SDDC Manager role; auth via `POST /v1/tokens` | access token **1 h**, refresh token **24 h** | query `GET /v1/roles` on your appliance — see below |
| vCenter | SSO user + vCenter role/permission; session via `POST /api/session` | session id, lifetime **not documented** | vCenter role model = sets of privileges assigned on objects |
| NSX | **Principal identity** with an X.509 client certificate | cert-lifetime; session cookie **1800 s** | `auditor` (read-only) |
| VCF Operations | Local or imported user + role; auth via `POST /suite-api/api/auth/token/acquire` | token **6 h** | `ReadOnly` |
| VCF Automation (VM Apps) | API token from the tenant | API token **90 days**, access token **1 h** | role model not documented for 9.0 |

Note that **SDDC Manager and ESX are excluded from VCF SSO** — in 9.0 *and* in 9.1. Even
after you upgrade, a fleet-wide SSO token will not open SDDC Manager. It keeps its own
`/v1/tokens` flow. If your automation talks to SDDC Manager, that account is separate
forever.

---

## Concrete setup, product by product

### 1. VCF Operations — the cleanest read-only story in 9.0

This is the one place where 9.0 gives you a proper named read-only role and a full
role/user management API. The `/auth/*` surface is **spec-confirmed present at tag
`9.0.0.0`** (57 operations) — this is not a 9.1-only feature, despite what some of
Broadcom's own prose implies.

Create the account and grant it read-only:

```
POST   /suite-api/api/auth/users                 # Create a new user
PUT    /suite-api/api/auth/users/{userId}/permissions   # Assign a role permission to a user
GET    /suite-api/api/auth/roles                 # Confirm the role name on your build
GET    /suite-api/api/auth/users/{userId}/permissions   # Verify what it actually got
```

The named roles referenced in the corpus are **Administrator** and **ReadOnly**. Confirm
`ReadOnly` exists verbatim on your appliance with `GET /api/auth/roles` before hard-coding
it. If `ReadOnly` is broader than you want, 9.0 supports custom roles:
`POST /api/auth/roles` then `PUT /api/auth/roles/{roleName}/privileges`, with the
available privileges enumerable via `GET /api/auth/privileges` and
`GET /api/auth/privilegegroups`.

Then authenticate as that account:

```bash
curl -X POST https://<ops-fqdn>/suite-api/api/auth/token/acquire \
  -H 'Content-Type: application/json' \
  -d '{"username":"svc-automation","password":"<password>"}'
```

Response carries `token` (format `<uuid>::<uuid>`), plus `expiresAt` and `validity` (ms).
Subsequent calls use:

```
Authorization: OpsToken <token>
```

**Lifetime is six hours.** Re-acquire; there is no refresh. Release early with
`POST /suite-api/api/auth/token/release`.

Two things *not* to do on 9.0:
- Do **not** send `Authorization: Bearer <token>` to VCF Operations. The Bearer form is a
  9.1 addition; 9.0 documents `OpsToken` only (legacy `vRealizeOpsToken` also still works).
- Do **not** try `POST /api/auth/token/exchange`. Absent at 9.0, present at 9.1.

### 2. SDDC Manager — separate account, always

Not SSO-brokered. Create a user and assign a role:

```
GET    /v1/roles          # Retrieve a list of roles from SDDC Manager
POST   /v1/users          # Assign access to users in SDDC Manager
GET    /v1/users          # Verify
DELETE /v1/users/{id}     # Revoke
```

All spec-confirmed at tag `9.0.0.0`. **I'm deliberately not naming the role strings** —
the role names aren't published in the spec inventory, and guessing one is exactly the kind
of plausible-looking wrong answer that survives review and fails in your estate. Call
`GET /v1/roles` against your own SDDC Manager and use what it returns. Pick the least
privileged one that still satisfies your automation's reads.

Then get tokens:

```bash
curl -X POST https://<sddc-manager-fqdn>/v1/tokens \
  -H 'Content-Type: application/json' \
  -d '{"username":"svc-automation@vsphere.local","password":"<password>"}'
```

Returns `accessToken` (a JWT) and `refreshToken.id` (a UUID). Use
`Authorization: Bearer <accessToken>`.

Refresh — and this one has a trap in the payload shape:

```
PATCH /v1/tokens/access-token/refresh
```

The body is the **plain-text refresh-token UUID, not JSON**, and the response body **is the
raw JWT**, not a JSON wrapper. Revoke with `DELETE /v1/tokens/refresh-token`, same
plain-text body, returns `204`.

Access token 1 hour, refresh token 24 hours. So your service account re-authenticates with
username/password at least daily no matter what. Store the password in a secrets manager,
not in the script.

*(Caveat worth knowing: the SDDC Manager OpenAPI document declares no `securitySchemes` at
all in 9.0, and no operation carries a `security` block. The `Authorization: Bearer` header
is documented in prose and is correct, but the spec offers no machine confirmation of it.)*

### 3. NSX — principal identities, with an honest asterisk

For non-interactive NSX access in 9.0, the documented mechanism is an NSX **principal
identity**, which is what an X.509 client certificate binds to. Verbatim from the docs:
*"NSX supports using an X.509 client certificate for authentication. The certificate is
associated with a principal identity (a short name, similar to a username)."*

Assign it the **`auditor`** role — that's the built-in read-only role (Enterprise Admin is
full CRUD; Auditor is read-only; there are 13 other built-ins and custom roles are
supported). Then call with `curl --key <keyfile> --cert <certfile>`.

**The asterisk you need to know about:** the VCF 9.0 product support notes list Principal
Identity accounts as **deprecated** — *"planned for deprecation in an upcoming release"* —
directing operators toward Federated Users via VCF SSO. So the only documented NSX-native
service-account mechanism in 9.0 is simultaneously on the deprecation path. Use it, but
plan the migration; this is one of the things 9.1 actually fixes.

Do not reach for the token-based principal identity route
(`/api/v1/trust-management/token-principal-identities`). That is confirmed for 9.1 and is
**not verified for 9.0** — there is no NSX OpenAPI spec published at the `9.0.0.0` tag at
all, so I can't tell you either way. If you want to know whether your specific 9.0 build
carries it anyway, fetch your appliance's own spec and search it:

```bash
curl https://<nsx-manager>/api/v1/spec/openapi/nsx_api.json | grep token-principal-identities
```

Your appliance's spec is the only authority for NSX on 9.0.

If you're using the session-cookie flow instead of a client certificate:
`POST /api/session/create` with form body `j_username`/`j_password`, and you need **both**
`Cookie: JSESSIONID=<id>` and `x-xsrf-token: <token>` on every subsequent call. Default
timeout 1800 seconds.

*Confidence note: all NSX 9.0 auth facts here are prose-documentation evidence only, not
spec-grade, because Broadcom published no NSX specs at the 9.0 tag.*

### 4. vCenter — read this before you write the script

**vCenter 9.0 blocks non-federated username/password logins.** Verbatim from the 9.0
vSphere product support notes: *"vCenter 9.0 blocks logins with just a user name and
password, which might sometimes allow bypassing the federated provider domain."*

If your vCenter is federated with an external IdP, a plain Basic-auth session create for
your new service account may simply be rejected — and the documented path is the three-step
federated flow: get a JWT from the external IdP → exchange it for a vCenter SSO SAML token →
exchange that for a session identifier. That is a materially bigger lift than "make a
service account", and it's worth finding out which situation you're in before you build
anything.

The session endpoint is `POST /api/session` (create), `GET /api/session`,
`DELETE /api/session`. Subsequent header is `vmware-api-session-id: <session-id>`.

One documentation trap: some Broadcom prose pages print `/api/cis/session`. That string
appears nowhere in either the 9.0 or 9.1 spec — the operations are `Cis.Session_create` etc.
on `/session` with base `https://{host}/api`, so **use `/api/session`**. If your deployment
rejects it, `/api/cis/session` is the fallback to test.

Roles on vCenter are sets of privileges associated to a user or group on an object in the
hierarchy. Grant your service account read privileges at the appropriate scope rather than
at the root if you can.

---

## Certificates — you will hit this on the first call

At deployment every VCF component gets a certificate from the **VMware Certificate
Authority (VMCA)**, which nothing trusts by default. Your brand-new service account's first
API call will very likely fail on TLS, and it will look like a problem with the account.
It isn't.

The documented remedy is to **import the VMCA root (or your enterprise CA) into your
automation host's trust store, or replace the component certificates** with enterprise
CA-signed ones. Supported CA types are VMCA, Microsoft CA, OpenSSL, self-signed, managed
from the VCF Operations console.

No Broadcom page documents disabling TLS verification as a supported practice. The only
`-k` in the official docs is inside NSX's own `curl` examples — treat that as
example-only. If you're prototyping and want to use `-k` or `verify=False` for an
afternoon, that's a reasonable call to make with your eyes open; just don't let it ship.
This is a management plane holding infrastructure credentials, which is a different risk
class from an insecure flag against a test API.

Two related points:
- **Connect by FQDN, not IP.** Certificates are issued to FQDNs; connecting by address
  fails hostname verification. Make sure forward and reverse DNS resolve for every
  component your automation touches.
- **Certificate rotation is a trust-bundle reload event.** Auto-renewal touches ESX,
  vCenter, NSX Manager and SDDC Manager. A long-running automation process that caches its
  trust store at startup will break at renewal time. (That consequence is inferred from the
  documented component coverage — the docs don't state the impact on running clients.)

---

## Practical shape for your automation

Given the lifetimes above, here's what I'd actually build:

1. **A secrets store holding per-product passwords/certs**, not tokens. Tokens are too
   short-lived to be the stored artifact anywhere except VCF Automation.
2. **A refresh-capable client per product.** Specifically: capture `refreshToken.id` from
   SDDC Manager (not just the access token), handle the VCF Operations 6-hour expiry, and
   handle the NSX 1800-second session timeout. Getting this wrong is the single most common
   cause of "it worked for an hour then started 401ing".
3. **Least-privilege verified, not assumed.** After creating each account, log in *as it*
   and confirm both that a representative read succeeds and that a write is refused. For
   NSX specifically, do **not** verify write-refusal by attempting your intended production
   write — use a throwaway scratch object, because if the role turns out to be sufficient
   you've just made the production change.
4. **Document the accounts.** Four separate accounts across four products with four
   different lifetimes is more operational surface than one token. That's the real cost of
   doing this on 9.0, and it's still much better than shipping your admin creds.

---

## What changes if/when you go to 9.1

Worth knowing, because it's the reason the flow you were looking for exists at all:

- **API clients and API tokens arrive**, managed under *Fleet Management → Managing
  Identity and Access Using VCF Single Sign-On → Managing API Clients and Tokens*, with a
  70-operation IAM API behind it.
- **Fleet-level TTL controls arrive:** API Token TTL default 30 days / **max 180 days**;
  Access Token TTL default 30 minutes / **max 480 minutes**. That 180-day ceiling is the
  real answer to "long-lived" — it's long-*er*-lived, not permanent. (The default figures
  come from the token-generation dialog and may be UI defaults rather than published
  defaults; the maxima are documented.)
- **VCF built-in roles arrive:** VCF Administrator, VCF Viewer, SDDC Administrator, SDDC
  Viewer, mapped to component roles. **VCF Viewer / SDDC Viewer map to NSX `auditor`** —
  that's the read-only scoping you're asking for, centrally. These names do not exist in
  9.0; don't let anyone hand you a runbook that uses them.
- Three gotchas to carry into the upgrade: the API token **cannot be retrieved after you
  click Continue** (capture it immediately); **OAuth clients are not migrated** on the
  vIDM → identity-broker migration and must be manually regenerated; and if the service
  account is a **JIT user, going inactive silently kills previously issued API tokens** —
  they aren't revoked or expired, the exchange just stops returning access tokens.
- And the identity broker comes under VCF certificate management in 9.1, which makes it a
  single TLS point of failure for every SSO-federated client at once. 9.0's per-product auth
  has no such choke point — a small consolation for the extra account sprawl.

---

## Things I could not verify, stated as such

Rather than fill these in by inference:

- **VCF Operations role name `ReadOnly`** is referenced in the corpus but the page naming it
  is a 9.1 page; the *endpoints* are confirmed 9.0. Confirm the exact string via
  `GET /api/auth/roles` on your appliance.
- **SDDC Manager role names** are not published in the spec inventory. Use `GET /v1/roles`.
- **vCenter session id lifetime** is not documented anywhere I can confirm.
- **Whether the vCenter non-federated login block persists in 9.1** — no 9.1 page restating
  or relaxing it was retrievable.
- **The per-service inbound port matrix.** Both the 9.0 and 9.1 planning pages defer to
  <https://ports.broadcom.com/>, which renders client-side and exposes no static table. All
  documented VCF API traffic is HTTPS; vSphere Automation is port 443 at `/api`, with an
  appliance-config subset on 5480. Verify TCP/443 to each target FQDN from wherever your
  automation runs.
- **Whether the Identity Broker token endpoint `POST /acs/t/{tenant}/token` exists in 9.0.**
  The reference for it is version-tagged 9.1, and the total absence of any API-token feature
  from the 9.0 doc set suggests it may not be customer-exposed in 9.0. Do not build against
  it on 9.0.

---

*Sources: Broadcom TechDocs for VCF 9.0 and 9.1, the Broadcom developer portal, and
machine-extracted OpenAPI operation inventories diffed between git tags `9.0.0.0` and
`9.1.0.0` of `github.com/vmware/vcf-api-specs` — all captured 2026-07-31. None of this has
been executed against a live VCF environment. Account creation and role assignment are
state-changing operations; confirm the exact role names and payloads against Broadcom's
documentation for your specific build (VCF 9.0.0.0 released 17 JUN 2025, build 24755599)
before running them.*
