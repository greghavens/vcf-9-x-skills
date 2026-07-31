# Read-only service account + long-lived API token on VCF 9.0

## Short version

Good instinct — getting automation off your personal admin credentials is the right move. But there's a version problem you need to know about before you start clicking around:

**The feature you're describing — a first-class "API client" with a generated, long-lived, role-scoped API token managed centrally in VCF Operations — is new in VCF 9.1. It does not exist in VCF 9.0.**

The Broadcom docs for "Create an API Client and Generate an API Token" state it plainly: *"Starting with VCF 9.1, you can log in to VCF Operations and create an API client and generate an API token."* That page only exists in the 9.1 branch of the docs; there is no 9.0 equivalent.

So on 9.0 you have two paths:

1. **Upgrade to 9.1** and use the built-in VCF SSO API client/token flow (this is the clean answer, and it's what your automation should eventually target).
2. **Stay on 9.0** and build the equivalent per component, because in 9.0 there is no single credential that spans the stack. Details below.

There is no supported way to backport the 9.1 API client feature into 9.0.

---

## What you get if/when you go to 9.1

Worth knowing so you can decide whether to just upgrade:

- Path: **Manage > Fleet Management > Identity & Access > VCF SSO Overview > (your identity broker) > API Access > API Clients**.
- You create a *client* (name, description) and assign it **scope + role + validity** — this is where your read-only scoping lives.
- Then **Generate API Token** on that client, with two separate TTLs:
  - **API Token TTL** — the long-lived refresh credential. Default **30 days**.
  - **Access Token TTL** — the short-lived bearer token. Default **30 minutes**.
  - Maximum values for both are capped by **Fleet Settings > IAM Setting**, so if you want longer than the default you raise the cap there first.
- The token is shown **once**. After you click Continue it cannot be retrieved again. Pipe it straight into your secrets manager.
- 9.1 also adds a shortcut: right-click your username in any VCF component UI and pick **Generate API Token**, which redirects you to the Identity Broker UI.
- PowerCLI 9.1 consumes these directly (`Connect-VIServer -VcfApiToken ...`).

Prerequisite either way: **VCF SSO / VCF Identity Broker must be configured** before any of this is available.

---

## Doing it on 9.0, component by component

On 9.0 you're assembling this yourself. Which of these you need depends entirely on **which APIs your automation actually calls** — that's the first thing to pin down, because the answer is different for each.

### VCF Operations (`/suite-api`)

This is probably where most read-only automation points (inventory, metrics, alerts).

- Create a **local VCF Operations user**, assign the built-in **Read Only** role, scoped to the object groups you want. Don't reuse an existing account.
- Authenticate with `POST https://<vcf-ops>/suite-api/api/auth/token/acquire` with a JSON body of `{"username": "...", "password": "..."}`.
- Use the result as header `Authorization: OpsToken <token>`.
- **The token expires after six hours.** There is no long-lived variant in 9.0. Your automation has to re-acquire.

**Important 9.0 gotcha:** you cannot use a VCF SSO / VCF Identity Broker (VIDB) user for this. Broadcom KB 422959 states *"Generation of Auth token using VIDB user is not supported in VCF Operations 9.0.x."* Token acquisition against `/suite-api` works with **local users only** on 9.0. If you build your service account as a federated/SSO identity, token acquisition will fail and you'll burn a day on it. Make it a local Ops user.

### SDDC Manager

- Still present in 9.0, but **deprecated** — Broadcom has said it will be removed in a future release, and many workflows have moved to VCF Operations. Don't build new long-term automation against it if you can avoid it.
- Also note: **VCF Single Sign-On in 9.0 explicitly excludes SDDC Manager and ESXi.** So an SSO-based service identity won't cover SDDC Manager; it needs its own account (local account or the management domain vCenter SSO).
- Assign the **VIEWER** role for read-only. (Roles are ADMIN / OPERATOR / VIEWER.)
- Auth: `POST /v1/tokens` with `{"username","password"}` returns an `accessToken` (JWT, **1 hour**) and a `refreshToken.id`.
- Refresh with `PATCH /v1/tokens/access-token/refresh`, passing the refresh token ID, to get a new access token without re-sending the password.
- Revoke with `DELETE /v1/tokens/refresh-token`. This is your kill switch — worth wiring into your offboarding runbook.
- The refresh token is the closest thing to "long-lived" here, but it's still a bearer secret with a bounded life, not a permanent API key.

### VCF Automation (if you have it deployed)

This is the one place in 9.0 with a genuine **service account** primitive, so if your automation targets VCF Automation, use it rather than a human account.

- Service accounts are API-only identities, created via the Provider Management Portal.
- They authenticate with an **OAuth refresh token (API token)**, exchanged for short-lived JWT access tokens (**access token expires after 1 hour**).
- A service account holds **exactly one role**, passed as a URL-encoded OAuth scope in the form `urn:vcloud:role:<roleName>`. Pick a read-only role here.
- **Token rotation:** service account tokens rotate on each use per RFC 6749. Your client must persist the new refresh token after every exchange or you'll lock yourself out. Unused tokens persist indefinitely until an admin revokes them.
- The account goes through a grant workflow: Created → Requested → Granted → Active. An admin approves the device-code request under **Service Accounts > Review Access Requests** before it can be used.
- Rough shape of the flow: `POST /tm/oauth/tenant/<org>/device_authorization` (with `client_id=<serviceAccountName>`) → admin approves the `user_code` in the UI → `POST /tm/oauth/tenant/<org>/token` with `grant_type=urn:ietf:params:oauth:grant-type:device_code`, the `refresh_token`, `client_id`, and `device_code`. Afterwards use `grant_type=refresh_token` to renew.
- Service accounts deliberately cannot create further API tokens or manage other service accounts — which is exactly the blast-radius property you want.

### vCenter

- No long-lived API token in 9.0. Create a dedicated **vCenter SSO user**, grant the built-in **Read-only** role at the vCenter root object with propagation, and use session-based auth (`POST /api/session`) — the session token is short-lived and idle-timed out.
- Set the account to non-expiring password in SSO policy, or you'll get a 3am surprise.

### NSX

- If your automation reads NSX, use a **Principal Identity** with **certificate-based auth** and the **Auditor** (read-only) role. This is the best answer in the whole stack for "long-lived, no password, non-human": the credential is an X.509 client cert whose lifetime you control, and a PI cannot be modified by other users.
- Trade-off: you now own certificate rotation. Put the expiry date in your calendar.

---

## Practical recommendation

Given you're on 9.0:

1. **Scope the work first.** List the exact endpoints your automation hits. If it's all VCF Operations `/suite-api`, this is a one-hour job (local Read Only user + a token-caching wrapper). If it spans Ops + SDDC Manager + vCenter + NSX, you're creating four identities and there's no way around that in 9.0.
2. **Accept that "long-lived token" means "long-lived credential + short-lived token"** on 9.0. Store the password/refresh-token/cert in a real secrets manager (Vault, CyberArk, etc.), and have your automation acquire a fresh access token per run or cache it with a safety margin (e.g. renew at 80% of TTL). Do not hardcode.
3. **Scope read-only on the identity, not the token.** In both 9.0 and 9.1, the token inherits the role assigned to the account/client. There is no per-token "downscope to read-only" — if the account has admin, the token has admin. So the role assignment is the actual security control. Verify it by having the service account attempt a write and confirming it gets a 403.
4. **Document the revocation path** for each identity now, while you're building it: SDDC Manager `DELETE /v1/tokens/refresh-token`, disable the Ops local user, revoke the VCF Automation service account, remove the NSX PI.
5. **Plan the 9.1 migration.** When you upgrade, collapse whatever you built into a single VCF SSO API client with a read-only role and let the platform manage TTL and revocation. Design your automation's credential handling behind an interface now so that swap is a config change, not a rewrite.

## Things I'd want to confirm in your environment

- Which components the automation actually reads from (drives everything above).
- Whether VCF SSO / Identity Broker is already configured in your instance.
- Whether VCF Automation is deployed at all — many VCF 9.0 installs don't have it.
- Your exact 9.0 patch level (9.0.0 vs 9.0.x); some of the 9.0.x updates shifted identity behaviour, so check the release notes for your build before finalising the design.

---

## Sources

- [Create an API Client and Generate an API Token (VCF 9.1 — "Starting with VCF 9.1")](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/managing-api-tokens.html)
- [How to authenticate VCF Operations API using VIDB user (Broadcom KB 422959 — not supported on 9.0.x)](https://knowledge.broadcom.com/external/article/422959/how-to-authenticate-vcf-operations-api-u.html)
- [Acquire an Authentication Token — VCF Operations 9.0 suite-api (6-hour token)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html)
- [Tokens APIs — VMware Cloud Foundation API (POST /v1/tokens, refresh, revoke)](https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/tokens/)
- [Managing Service Accounts in VCF Automation 9.0](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/provider-management/managing-system-administrators-and-roles/managing-provider-users-and-groups/managing-service-accounts.html)
- [Generating API Tokens for Service Provider Account — VCF Automation 9.0](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/service-provider-portal/generating-provider-management-api-tokens.html)
- [VCF 9.1 Quick Tip: Generate VCF SSO API Tokens using VCF Component UI (William Lam)](https://williamlam.com/2026/07/vcf-9-1-quick-tip-easily-generate-vcf-sso-api-tokens-using-vcf-component-ui.html)
- [VMware Cloud Foundation 9.0: Transitioning from SDDC Manager to VCF Operations (SDDC Manager deprecated)](https://my-cloudy-world.com/2025/07/03/vmware-cloud-foundation-9-0-transitioning-from-sddc-manager-to-vcf-operations/)
- [VCF 9.0 GA Mental Model: Fleet Services vs Instance Management Planes (VCF SSO excludes SDDC Manager and ESXi)](https://digitalthoughtdisruption.com/2026/02/17/vcf-9-0-ga-fleet-services-vs-instance-management-planes/)
- [Add a Role Assignment or Principal Identity — NSX](https://techdocs.broadcom.com/us/en/vmware-cis/nsx/vmware-nsx/4-2/administration-guide/authentication-and-authorization/add-role-assignment-or-principal-identity.html)
- [OAuth 2.0 Authentication Using VMware Cloud Foundation PowerCLI 9.1](https://blogs.vmware.com/cloud-foundation/2026/06/01/oauth-2-0-authentication-using-vmware-cloud-foundation-powercli-9-1/)
- [Streamline Administrative Access with VMware Cloud Foundation Single Sign-On](https://blogs.vmware.com/cloud-foundation/2025/06/19/streamline-administrative-access-with-vcf-single-sign-on/)
