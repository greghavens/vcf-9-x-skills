# Getting an API token for VCF automation

Short version: **the answer depends heavily on which VCF version you're on, and on which component you're actually automating.** "VCF" isn't one API — SDDC Manager, VCF Operations, VCF Automation, vCenter, and NSX each have their own auth. And VCF 9.1 changed the story significantly by introducing real long-lived API tokens, which did not exist before.

So before anything else:

**1. What VCF version are you on?** — SDDC Manager UI → bottom-left / Administration, or `GET /v1/system/version` (older) or the VCF Operations UI banner in 9.x.
**2. What are you automating against?** — SDDC Manager (fleet/domain/lifecycle ops), VCF Operations, VCF Automation, or straight vCenter/NSX?

Here are the paths.

---

## Path A — VCF 9.1 and later (the "real API token" path)

This is what you want if you're on 9.1. It's the first VCF release with a proper long-lived, revocable API token, issued through VCF SSO and redeemed via the VMware Identity Broker (VIDB).

**Generate the token (UI):**
1. Make sure VCF SSO is configured.
2. From any VCF component UI, right-click your username in the top bar → **Generate API Token**.
3. You're redirected to the **Identity Broker** interface in VCF Management Services, where you create, view, and revoke tokens.
4. Copy the token at creation time — you won't be able to read it again.

**How it's used:** the long-lived API token is not itself a bearer token. Your script passes it to VIDB, which validates it and returns a **short-lived bearer access token** that you then send as `Authorization: Bearer <token>`.

Rough lifetimes:
- API token: **up to 30 days**
- Bearer access token from VIDB: **short-lived, ~30 minutes**

So your automation should cache the bearer token and re-exchange on expiry (or on a 401), not re-exchange on every call.

**PowerCLI 9.1 makes this nearly free:**

```powershell
# Explicit exchange
$ctx = New-VcfOAuthSecurityContext -IdentityBrokerHostname <vidb-fqdn> -ApiToken '<api-token>'
Connect-VIServer -VcfOAuthSecurityContext $ctx

# Or let PowerCLI do the whole chain for you
Connect-VIServer <vcenter-fqdn> -VcfApiToken '<api-token>'
```

Under the hood for vCenter the chain is: VCF SSO API token → Identity Broker access token → vCenter SAML token → vCenter session. If you're scripting in something other than PowerShell you'll have to walk that chain yourself; William Lam's `vcenter91_idb_api_token_client.ps1` is a good reference implementation to port.

---

## Path B — VCF 5.x through 9.0 (SDDC Manager token pair)

On these versions there is **no long-lived API token**. You authenticate with a username and password and get back a short-lived access token plus a refresh token. Plan your credential storage accordingly — you are storing a password, not a token.

**Create the token pair:**

```bash
curl -k -X POST https://<sddc-manager-fqdn>/v1/tokens \
  -H 'Content-Type: application/json' \
  -d '{"username":"svc-automation@vsphere.local","password":"<password>"}'
```

Response contains `accessToken` (a JWT) and `refreshToken.id`.

**Use it:**

```bash
curl -k https://<sddc-manager-fqdn>/v1/domains \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Refresh it** (access tokens are short-lived, on the order of an hour; the refresh token lasts considerably longer and can be reused any number of times until it expires or is revoked):

```bash
curl -k -X PATCH https://<sddc-manager-fqdn>/v1/tokens/access-token/refresh \
  -H 'Content-Type: application/json' \
  -d '"<refresh-token-id>"'
```

**Revoke** when a job or service is decommissioned:

```bash
curl -k -X DELETE https://<sddc-manager-fqdn>/v1/tokens/refresh-token \
  -H 'Content-Type: application/json' \
  -d '"<refresh-token-id>"'
```

**Required access:** the account must exist in SSO or your AD domain and be assigned **ADMIN, OPERATOR, or VIEWER** in VCF. Pick the least privileged one that works — VIEWER for read-only reporting/inventory automation, OPERATOR for day-2 tasks, ADMIN only if you genuinely need it.

---

## Other VCF 9.x components (they each differ)

If you're on 9.x, note these are separate endpoints with separate token formats:

| Component | Endpoint | Body | Token field |
|---|---|---|---|
| SDDC Manager | `POST /v1/tokens` | JSON `{"username","password"}` | `.accessToken` |
| VCF Installer | `POST /v1/tokens` | JSON `{"username","password"}` | `.accessToken` |
| VCF Operations | `POST /suite-api/api/auth/token/acquire` | JSON `{"username","password","authSource":"LOCAL"}` | `.token` |
| VCF Services Runtime | `POST /v1/identity/token` | form-encoded, `grant_type=password` | `.access_token` |

Note VCF Operations uses a non-standard auth header (`Authorization: vRealizeOpsToken <token>`), not `Bearer` — a common first-day gotcha. Set `authSource` to your AD/LDAP source name rather than `LOCAL` if you're using a domain account.

**vCenter** directly: `POST /api/session` with basic auth returns a session ID used as the `vmware-api-session-id` header.
**NSX** directly: supports basic auth, session-based auth (`POST /api/session/create` → `JSESSIONID` + `X-XSRF-Token`), and — best for automation — **Principal Identity** certificate-based auth, which avoids passwords entirely.

---

## Recommendations before you start

- **Create a dedicated service account.** Do not automate as `administrator@vsphere.local`. A named service account gives you an audit trail and lets you revoke without breaking human admins.
- **Least privilege.** Start at VIEWER/read-only, escalate only where a specific call requires it.
- **Drop the `-k`.** I used it above for brevity, but in production import the SDDC Manager / VCF CA into your trust store and verify TLS properly. Certificate validation is the main thing protecting these very privileged credentials.
- **Store secrets in a vault**, not in the script or a CI variable in plaintext. On pre-9.1 you're storing a reusable password, which makes this more important, not less.
- **Handle 401 by re-authenticating**, and back off on 429 — SDDC Manager will rate-limit.
- **Version-pin your API calls.** VCF 9.0 → 9.1 moved a lot of surface area around; code written against 9.0 endpoints should not be assumed to work post-upgrade.

---

## What I need from you to be more specific

Tell me your **VCF version** and **which component** you're targeting, and I can give you an exact, working script — including the token-refresh loop and a least-privilege role recommendation for the specific operations you want to automate. If you're on 9.0 today and upgrading to 9.1 soon, I'd also suggest structuring the auth as a swappable module now, because the token model genuinely changes.

---

Sources:
- [Tokens APIs | VMware Cloud Foundation API](https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/tokens/)
- [VMware Cloud Foundation 9.1 APIs: Obtaining Authentication Tokens](https://my-cloudy-world.com/2026/05/14/vmware-cloud-foundation-9-1-apis-obtaining-authentication-tokens/)
- [VCF 9.1 - Quick Tip: Easily Generate VCF SSO API Tokens using VCF Component UI](https://williamlam.com/2026/07/vcf-9-1-quick-tip-easily-generate-vcf-sso-api-tokens-using-vcf-component-ui.html)
- [OAuth 2.0 Authentication Using VMware Cloud Foundation PowerCLI 9.1](https://blogs.vmware.com/cloud-foundation/2026/06/01/oauth-2-0-authentication-using-vmware-cloud-foundation-powercli-9-1/)
- [Getting Started with Token-Based Authentication for VMware Cloud Foundation APIs](https://blogs.vmware.com/cloud-foundation/2020/05/20/getting-started-with-token-based-authentication-for-vmware-cloud-foundation-apis/)
- [VMware Cloud Foundation Automation APIs for VM Apps Programming Guide](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1.html)
