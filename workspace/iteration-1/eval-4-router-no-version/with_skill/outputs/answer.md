# Getting an API token for VCF automation

Short answer up front: **there is no single "VCF API token."** Each product has its own auth flow, and — more
importantly — the thing most people mean by "an API token" (a long-lived, role-scoped token issued by VCF SSO)
**only exists in VCF 9.1. It does not exist in 9.0 at all.** So before anything else:

## First: which version are you on?

**Is this a 9.0 or a 9.1 fleet? If you're not sure, what does SDDC Manager report under About?**

I'm asking rather than assuming because this is the one question that changes the answer completely. Pointing a
9.0 user at the 9.1 *Fleet Management → Identity & Access → API Clients* flow doesn't produce an error message —
the navigation node simply isn't there, and the corresponding API routes return 404. Below I've given **both**
answers, clearly labelled. Take the one that matches your estate; don't blend them.

If you'd rather have the environment answer for you, ask SDDC Manager:

```bash
# 1. Get an SDDC Manager token (this flow is identical in 9.0 and 9.1, so it's safe to use before
#    you know the version)
curl -X POST "https://<sddc-manager-fqdn>/v1/tokens" \
  -H 'Content-Type: application/json' \
  -d '{"username":"<user>","password":"<password>"}'
# → {"accessToken":"<JWT>", "refreshToken":{"id":"<uuid>"}}

# 2. Ask it what it is
curl "https://<sddc-manager-fqdn>/v1/system/appliance-info" \
  -H "Authorization: Bearer <accessToken>"
# → ApplianceInfo, with a "version" field
```

`GET /v1/releases/system` and `GET /v1/sddc-managers` also carry `version` and make good cross-checks.

> **Do not use `GET /v1/system` for this.** It exists in both versions and the name is inviting, but its schema
> contains only `id`, `maxAllowedDomainsInSubscription` and (in 9.1) `vcfInstanceName` — no version field. It
> will appear to work and tell you nothing.

Quick sanity check on build numbers: VCF 9.0.0.0 released 17 JUN 2025, build 24755599. VCF 9.1.0.0 released
12 MAY 2026 (SDDC Manager build 25371088, ESX 25370933, vCenter 25370922, NSX 25318225).

---

# If you are on VCF 9.1 — yes, there is a real API token

9.1 added SSO-issued, role-scoped API tokens, API clients, OAuth apps and emergency access clients. This is the
flow you want.

### Prerequisite you cannot skip

You need an **existing interactive login with the VCF Operations Administrator role**. You cannot create the
first API client with an API client — it bootstraps from a human credential established at deployment.

### Step 1 — create an API client (UI)

**VCF Operations → Manage → Fleet Management → Identity & Access → VCF SSO Overview → select identity broker →
API Access → API Clients → Create**

Give it a name (the ID auto-populates) and an optional description, then **Create API Client**. Then under
**Roles**, select a **scope**, choose a **role**, and enter a validity period, and Save.

*(If the "API Access" node isn't there, you're on 9.0 — jump to the 9.0 section.)*

### Step 2 — generate the API token

Ellipsis on the client → **Generate API Token**. You'll be asked for:

| Field | Default | Maximum |
|---|---|---|
| API Token TTL | 30 days | 180 days |
| Access Token TTL | 30 minutes | 480 minutes |

**The token value cannot be retrieved after you click Continue.** Capture it into your secret store at
generation time or you will be regenerating it.

*(Caveat: Broadcom's IAM settings page publishes the maxima only. The 30-day / 30-minute figures come from the
token-generation dialog and may be UI defaults rather than system settings.)*

### Step 3 — exchange the API token for a bearer access token

The API token is a long-lived refresh credential, not the thing you put in the `Authorization` header. Exchange
it at the identity broker:

```bash
curl -X POST "https://<identity-broker-fqdn>/acs/t/<tenant>/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=refresh_token' \
  -d 'api_token=<your-api-token>'
```

Response carries `access_token`, `token_type` (= `"Bearer"`), `expires_in` (seconds), `refresh_token`,
`id_token`, `scope`. Then:

```
Authorization: Bearer <access_token>
```

Broadcom's own four-step description of this flow, verbatim: *"Administrator creates API clients with
credentials that are recorded in VIDB"* → *"Administrator requests a long-lived API refresh token from the VCF
Operations UI"* → *"Automation script passes the API refresh token to VIDB and gets a bearer access token in
return"* → *"Automation script uses the bearer access token to authenticate with VCF components."*

You can discover the broker's endpoint with `GET /suite-api/api/auth/sources/vidb/well-known-url` (9.1-new).

### The same thing via API instead of the UI

All of it is scriptable. The `{ssoRealmId}` comes first:

```
GET  /suite-api/api/fleet-management/iam/ssorealms                                  # get {ssoRealmId}
POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients         # create client
POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens          # generate token
POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens/{apiTokenId}/regenerate
GET|PUT /suite-api/api/fleet-management/iam/settings                                # TTL ceilings
```

There are 70 operations under `/api/fleet-management/iam/**` in 9.1 (and zero in 9.0).

### Which role to pick

Ask what the automation will *do* before you pick, or you'll get a token that fails on the first write.

| VCF role | Maps to |
|---|---|
| **VCF Administrator** | vCenter Admin; NSX `enterprise_admin`; VCF Operations Administrator; VCF Automation System Administrator; VCF Operations HCX Migration Admin; VCF Operations orchestrator Orchestrator Administrator |
| **VCF Viewer** | vCenter ReadOnly; NSX `auditor`; VCF Operations ReadOnly |
| **SDDC Administrator** | vCenter Admin; NSX `enterprise_admin`; VCF Operations HCX Migration Appliance Admin; VCF Operations orchestrator Orchestrator Viewer |
| **SDDC Viewer** | vCenter ReadOnly; NSX `auditor` |

Read-only fleet queries: **VCF Viewer**. Writes against vCenter/NSX: **VCF Administrator** or **SDDC
Administrator**. Built-in VCF roles cannot be modified.

*(Honest gap: the scope hierarchy — global vs org vs instance — is not documented on Broadcom's built-in-roles
page, even though the client-creation flow makes you pick a scope. You'll have to see what the dropdown offers.)*

### Three 9.1 traps worth knowing before you build on this

1. **JIT user inactivity silently kills working tokens.** Verbatim: once a JIT-provisioned user goes inactive,
   *"previously issued API tokens cannot retrieve access tokens until the user authenticates again."* The token
   is neither revoked nor expired — the exchange just stops returning access tokens. If your automation runs on
   a JIT identity, it will die quietly. Prefer a non-JIT service identity.
2. **"It randomly stopped working after a few weeks"** is nearly always either the 30-day default API Token TTL
   expiring or the JIT trap above. Check both before regenerating credentials.
3. **If you migrated from vIDM to the VCF Identity Broker, your old OAuth clients are broken.** Verbatim:
   *"OAuth clients are not migrated automatically. You must manually regenerate the client and secret using
   identity broker and configure accordingly."* Rotate via
   `POST /suite-api/api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps/{oauthAppId}/rotate`.

There is also an **Emergency Access Client** for break-glass — *"high-privilege and long-lived access tokens to
critical systems when standard methods fail"* — under `.../iam/ssorealms/{ssoRealmId}/emergency-clients`.

---

# If you are on VCF 9.0 — the token you've read about doesn't exist

This is the honest answer rather than the convenient one. **VCF 9.0 has no SSO API client, no SSO-issued API
token, no OAuth-app management and no emergency access client.** Two independent confirmations: the 9.0 SSO doc
tree contains no API client / API token / OAuth client / role management page at all, and the 9.0 `vcf-operations`
OpenAPI spec contains **zero** operations under `/api/fleet-management/iam/**` (9.1 has 70). There is nothing to
call.

So on 9.0 you automate with **per-product credentials**. Here's each one:

### SDDC Manager — `POST /v1/tokens`

```bash
curl -X POST "https://<sddc-manager-fqdn>/v1/tokens" \
  -H 'Content-Type: application/json' \
  -d '{"username":"<user>","password":"<password>"}'
```

| | |
|---|---|
| Token field | `accessToken` (JWT); refresh handle at `refreshToken.id` (UUID) |
| Header | `Authorization: Bearer <accessToken>` |
| Refresh | `PATCH /v1/tokens/access-token/refresh` — body is the **plain-text refresh UUID, not JSON**; the response body **is** the raw JWT, not a JSON wrapper |
| Revoke | `DELETE /v1/tokens/refresh-token` — plain-text UUID, returns `204` |
| Lifetimes | access token **1 hour**, refresh token **24 hours** |

Capture `refreshToken.id` on the first call — with a 1-hour access token you need it.

### VCF Operations — `token/acquire`

```bash
curl -X POST "https://<ops-fqdn>/suite-api/api/auth/token/acquire" \
  -H 'Content-Type: application/json' \
  -d '{"username":"<user>","password":"<password>"}'
```

Token field is `token`, format `<uuid>::<uuid>`; the response also carries `expiresAt` and `validity` (ms).
Lifetime is **six hours**. Header is `Authorization: OpsToken <token>` (legacy `vRealizeOpsToken` still
supported). Release with `POST /api/auth/token/release`.

**Not available on 9.0:** `Authorization: Bearer <token>` against VCF Operations, and
`POST /api/auth/token/exchange`. Both are 9.1.

### NSX Manager — session cookie + XSRF

```bash
curl -i -c session.txt -X POST \
  -d 'j_username=<user>&j_password=<password>' \
  https://<nsx-manager>/api/session/create
```

You need **both** the `JSESSIONID` cookie and the `x-xsrf-token` response header on every subsequent call —
sending only the cookie is the classic failure and reads like a permissions problem. Default session timeout is
**1800 seconds**. Destroy with `/api/session/destroy`. For a genuine service account, the documented mechanism
is an **NSX principal identity** (X.509 client certificate bound to the identity), not a token.

*Confidence note: no NSX OpenAPI spec is published for 9.0 — the NSX 9.0 facts above are Broadcom prose only,
not spec-confirmed. (They are spec-confirmed for 9.1.)*

### vCenter / vSphere Automation

Base is `https://{host}/api` on port 443. Create a session with `POST /api/session`, then send the returned
session id as `vmware-api-session-id: <session-id>`.

**Read this before you script it:** vCenter 9.0 release notes state *"vCenter 9.0 blocks logins with just a user
name and password, which might sometimes allow bypassing the federated provider domain."* If your vCenter is
federated with an external IdP, plain Basic auth on session-create may be rejected and you need the three-step
federated flow: JWT from the external IdP → exchange for a vCenter SSO SAML token → exchange for a session
identifier. **A script that worked on 8.x and now fails at session-create on 9.0 is usually hitting this, not a
certificate problem** — an auth rejection, not a transport error.

*(A note on the path: some Broadcom prose pages print `/api/cis/session`, but `/api/cis/session` appears nowhere
in either OpenAPI spec, while `POST /api/session` is spec-confirmed at both 9.0 and 9.1. Use `/api/session`; if
your deployment rejects it, the prose variant is the fallback to test.)*

### VCF Automation (VM Apps tenant)

```
POST https://{vcfaHostname}/tm/oauth/tenant/{vcfaTenant}/token
Content-Type: application/x-www-form-urlencoded
grant_type=refresh_token&refresh_token=<api token>
```

API token (refresh token) defaults to **90 days**; access token to **1 hour**. **Honest gap:** the docs say
*"the response returns the access token"* but never name the JSON field, and never state the `Authorization`
header format. OAuth convention suggests `access_token` and `Bearer` — that is not documented. Verify
empirically before hard-coding it.

### Others on 9.0

- **vSAN** has no independent auth — it *"depend[s] on the vSphere Web Services API for login procedures."*
  Authenticate to vCenter and reuse the session.
- **VCF Operations for Logs**: `POST /api/v2/sessions`, Bearer scheme. (This is replaced entirely in 9.1 —
  different name, different base path, different header. Don't carry it forward.)
- **VCF Operations for Networks**: `/api/ni`, header `Authorization: API Key - NetworkInsight {token}`.
- **Fleet Management API**: HTTP Basic only, from KB 409715 —
  `echo -n 'admin@local:<fleet-admin-password>' | base64`, sent as `Authorization: Basic <base64>` (the word
  `Basic` must be present). The KB itself says the paths, payloads and credential lifetime are undocumented.
- **VCF Installer**: authentication method is **UNVERIFIED** — the spec declares no security schemes in either
  version and no Broadcom page documents it.

**There are no fleet-level token TTL controls in 9.0.** Every product's token expires on its own schedule; your
client needs to hold refresh material per product, not just access tokens.

---

# True on both versions

### SDDC Manager is not behind SSO. Ever.

**SDDC Manager and ESX are excluded from VCF SSO in both 9.0 and 9.1** — verified independently in each doc set.
Even on 9.1 with a working fleet-wide SSO token, SDDC Manager still needs its own `POST /v1/tokens`. If you're
building a client that assumes one token opens every door, this is where it breaks.

The federated components are: vCenter, VCF Operations, VCF Automation, log management, VCF Operations for
Networks, VCF Operations orchestrator, VCF Operations HCX, and NSX. Everything else is on its own.

### Your first call will probably fail on TLS, and `-k` is the wrong reflex

VCF appliances ship certificates from the default **VMware Certificate Authority**, which nothing trusts out of
the box. So your first request against vCenter, NSX, SDDC Manager or VCF Operations fails hostname/chain
validation.

Broadcom's documented remedy is to **import the CA or replace the certificates** — supported CA types are VMCA,
Microsoft CA, OpenSSL and self-signed, managed from the VCF Operations console. **No Broadcom page documents
disabling TLS verification as a supported practice.** The only `-k` in the official docs is inside NSX's own
`curl` examples; treat that as example-only, not guidance.

I'm not going to pretend `curl -k` won't work while you're prototyping — it will, and choosing it knowingly is a
reasonable call to make. But note the tradeoff is different here than against a test API: this is a management
plane holding your infrastructure credentials, so an intercepted session is an estate-wide problem. The one-line
proper fix is to add the VMCA root (or your enterprise CA) to your client's trust store. On 9.1 you'd import via
**VCF Operations → Operate → Administration Control Panel → Trusted Certificates → Import**, and note that
**only PEM is accepted** — convert DER/PKCS#7 first. *(That PEM-only statement is from the 9.1 doc set; I'm
deliberately not asserting it for 9.0, where the equivalent page wasn't retrievable.)*

Two related points:

- **Connect by FQDN, not IP.** Certificates are issued to FQDNs, so an IP connection fails hostname
  verification. Confirm forward and reverse DNS for every component.
- **On 9.1 specifically, the identity broker itself is under VCF certificate management** — and because it's the
  token issuer, a stale or untrusted broker certificate breaks *every* SSO-based API client at once. 9.0's
  per-product auth had no such single point of failure. (That blast-radius conclusion is my inference from the
  9.1 coverage list; the docs state the coverage, not the consequence.)

### PowerCLI

Install with `Install-Module VCF.PowerCLI -Scope CurrentUser`. Version-align it:

- 9.0 estate → `VCF.PowerCLI 9.0.0.24798382`
- 9.1 estate → `VCF.PowerCLI 9.1.0.25380678`

Check with `Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version`.

**`-VcfApiToken` and `-VcfOAuthSecurityContext` are 9.1-only parameters — they do not exist in PowerCLI 9.0.**
And a caveat I'd rather flag than paper over: Broadcom's changelog gives counts, not cmdlet names, so **which
cmdlets actually expose those parameters is unverified.** The 9.1 What's New page mentions `Connect-VIServer`,
`Connect-NsxServer` and `Connect-VcfOpsServer`; the `Connect-VcfSddcManagerServer` reference page does *not*
list either parameter. Confirm on your own install:

```powershell
Get-Help Connect-VIServer -Full
Get-Help <cmdlet> -Parameter VcfApiToken
```

Certificate-flag trap while you're there: `Connect-VIServer` uses `-Force`, but
`Connect-VcfSddcManagerServer` uses **`-IgnoreInvalidCertificate`** — not `-SkipCertificateCheck`, not `-Force`.

---

# What I'd do next

1. **Tell me 9.0 or 9.1** (or run the `appliance-info` call above) and I'll collapse this to just your path.
2. **Tell me what the automation needs to do** — read-only reporting versus writes against vCenter/NSX changes
   which role you should scope the token to, and getting that wrong means a token that authenticates fine and
   then fails on the first write.
3. **Tell me which products you're actually hitting.** If it's only SDDC Manager, the answer is the same on both
   versions and you can start today. If it's NSX or VCF Automation, there are product-specific wrinkles worth
   covering before you write code.

---

### Where I was working from documentation with known gaps

Being explicit, since these are places where a confident-sounding answer would be a guess:

- **VCF Installer API authentication** — unverified in both 9.0 and 9.1.
- **VCF Automation 9.1 All Apps token endpoint URL** — unverified; the Broadcom techdocs page 404s. The scheme
  is JWT via the `Authorization` header, with `x-vcloud-authorization` deprecated, but the endpoint isn't
  published. Don't carry the 9.0 VM Apps endpoint forward — different tenancy model.
- **VCF Automation 9.0 response token field name and header format** — the docs describe them without naming
  them.
- **Whether the identity broker `/acs/t/{tenant}/token` endpoint exists in 9.0** — the reference is
  version-tagged 9.1, and the absence of any API-token feature from the 9.0 doc set suggests it isn't
  customer-exposed there. I have deliberately not offered it as a 9.0 route.
- **Inbound port matrix** — unretrievable for both versions; both Planning and Preparation pages defer to
  `https://ports.broadcom.com/`, which renders client-side and publishes no static table. I won't invent one —
  go there directly.
- **9.1 status of the vCenter non-federated-login block** — no 9.1 page restating or relaxing it was found. It's
  a verified 9.0 behaviour; I'm neither asserting it for 9.1 nor claiming it was reverted.

All of the above is drawn from Broadcom documentation and published OpenAPI specifications (captured
2026-07-31), not from a live environment. Before running anything state-changing against a production estate,
validate it against Broadcom's docs for your exact build.
