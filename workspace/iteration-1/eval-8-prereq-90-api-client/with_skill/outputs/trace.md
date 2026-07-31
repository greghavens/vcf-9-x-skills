# Trace — skills and reference files read

## Skill selection

Read the `description` frontmatter of all four SKILL.md files first.

- **`vcf-foundation` — selected (primary).** Description explicitly covers "getting or
  refreshing an API token, setting up a service account or API client, choosing the right
  role or privilege" and version routing. Exact match for the task.
- **`nsx-security-policy` — selected (secondary).** Consulted only for the NSX
  principal-identity service-account detail, since `vcf-foundation` P6 routes NSX
  service-account questions toward NSX-specific material.
- **`vcf-api-discovery` — selected (secondary).** Used its bundled 9.0 spec inventory to
  confirm the SDDC Manager and VCF Operations user/role endpoints rather than asserting
  endpoints from memory (the skill's stated rule: confirm before stating).
- **`vcf-lifecycle-upgrade` — not used.** No upgrade, patch, precheck, bundle or depot
  content in the task.

## Version routing (SKILL.md Step 1)

User stated "VCF 9.0" explicitly. Per the router, that resolves step 1, so only the
`9.0` reference tree was loaded — deliberately not `references/9.1/auth-and-identity.md`,
to avoid 9.1 facts bleeding into a 9.0 answer. `deltas.md` was read separately as the
sanctioned cross-version comparison source.

## Files read

| File | Why |
|---|---|
| `skills/vcf-foundation/SKILL.md` | Full read. Version router, Step 2 prerequisites, Step 3 per-product auth, certs, roles, honest-reporting guidance. Flagged the exact scenario in Step 2: "SSO-issued, role-scoped API tokens are a 9.1 capability... If someone on 9.0 asks for a service account with a long-lived scoped token, the honest answer is that the 9.1 flow they have read about does not apply." |
| `skills/vcf-foundation/references/9.0/auth-and-identity.md` | Full read (both pages, 790 lines). P2 (no SSO API tokens in 9.0), P3 (SDDC Manager/ESX SSO exclusion), P4 (blocked non-federated vCenter logins), P5 (no VCF built-in roles), P6 (NSX principal identities), P7 (refresh-capable store), P8/P9 (TLS trust, FQDN). §1.1–1.5 per-product auth, §2 token lifetimes, §4 roles, §5 certs, §6 reachability, §7 spec-vs-prose conflicts, §8 UNVERIFIED list. |
| `skills/vcf-foundation/references/deltas.md` | Full read. T1 (API clients 9.1-only), T2 (OAuth clients not migrated), T3 (Bearer is 9.1), T5 (broker cert choke point), T6 (JIT silent token death), T7 (SSO exclusions unchanged). §3 API clients/tokens/IAM TTLs. §5 role mapping (VCF Viewer → NSX `auditor`). Used for the "what changes at 9.1" section. |
| `skills/vcf-foundation/references/powercli-session.md` | Partial (§0–1). Checked whether a PowerCLI token route existed for 9.0; confirmed `VcfApiToken` / `VcfOAuthSecurityContext` are 9.1-only, so PowerCLI was left out of the answer. |
| `skills/nsx-security-policy/references/9.0/dfw.md` | Targeted read (P3 service-accounts block, A6 other auth mechanisms). Principal-identity + X.509 verbatim quote, the 9.0 deprecation-flag tension, `auditor` read-only role, and the explicit 9.1-only status of `token-principal-identities` plus the appliance-spec self-check command. |
| `skills/vcf-api-discovery/SKILL.md` | Partial (Route 1). Confirmed the spec-inventory usage rule, including "a miss in a product whose spec is absent for that version is no evidence at all" — which is why the NSX 9.0 statements are labelled prose-only. |
| `skills/vcf-api-discovery/references/spec-inventory/9.0__sddc-manager.ops.json` | Queried for role/user/token paths. Confirmed `GET /v1/roles`, `GET|POST /v1/users`, `DELETE /v1/users/{id}`, and the three `/v1/tokens` operations at tag `9.0.0.0`. |
| `skills/vcf-api-discovery/references/spec-inventory/9.0__vcf-operations.ops.json` | Queried `/api/auth/*`. Confirmed `POST /api/auth/users`, `PUT /api/auth/users/{userId}/permissions`, `GET /api/auth/roles`, `POST /api/auth/roles`, `PUT /api/auth/roles/{roleName}/privileges`, `GET /api/auth/privileges`, `token/acquire`, `token/release` — all present at 9.0. |

## Skill directives that shaped the answer

- Lead with the 9.0/9.1 prerequisite mismatch rather than answering the question as asked
  (SKILL.md Step 2, reference P2).
- Do not name VCF Administrator / VCF Viewer / SDDC Administrator / SDDC Viewer for 9.0
  (P5) — deferred them to the 9.1 section.
- Do not offer `Authorization: Bearer` or `token/exchange` against 9.0 VCF Operations
  (§1.5).
- Do not present `POST /acs/t/{tenant}/token` as a 9.0 route (§3, UNVERIFIED).
- Use `POST /api/session`, not `/api/cis/session` (spec-vs-prose conflict item 5).
- Don't guess role name strings — point at `GET /v1/roles` / `GET /api/auth/roles`
  (api-discovery: "if you are about to state an endpoint... you have not confirmed, stop").
- On `-k` / `verify=False`: give the tradeoff, not a lecture (SKILL.md, Certificates).
- Report the UNVERIFIED items plainly rather than filling them in (SKILL.md, Honest
  reporting).
