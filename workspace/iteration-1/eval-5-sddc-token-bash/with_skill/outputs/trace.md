# Trace — skills and reference files consulted

Task: bash function to obtain and auto-refresh an SDDC Manager API token on VCF 9.0,
self-signed certificate.

## Skill selection

Read the `description` frontmatter of all four available skills, then selected:

| Skill | Used? | Why |
|---|---|---|
| `vcf-foundation` | **Yes — primary** | Its description names API tokens, token refresh, certificates and TLS trust explicitly. Both halves of the task sit inside it. |
| `vcf-api-discovery` | **Yes — supporting** | `vcf-foundation` §"When something here does not cover the case" routes here, and the discovery skill's core rule is to confirm any endpoint before stating it. Used to verify the three token endpoints and their payload schemas at the 9.0 tag. |
| `nsx-security-policy` | No | No NSX, DFW or microsegmentation content in the task. |
| `vcf-lifecycle-upgrade` | No | No upgrade, patching, bundle or precheck content in the task. |

## Files read, in order

1. `/home/claude/vcf-skills/skills/*/SKILL.md` — frontmatter descriptions of all four, for routing.
2. `/home/claude/vcf-skills/skills/vcf-foundation/SKILL.md` — full read.
   - Step 1 (version routing): resolved to **9.0** from the user's own statement; per the skill's
     instruction to load one version file only, did **not** read the 9.1 reference.
   - "Certificates and TLS trust" section drove the self-signed handling: give the working command
     *and* the proper path, name the risk without lecturing, leave the choice visible.
3. `/home/claude/vcf-skills/skills/vcf-foundation/references/9.0/auth-and-identity.md` — full read
   (790 lines, two passes). Load-bearing sections:
   - §1.1 SDDC Manager — the three `/v1/tokens` operations, payload, `accessToken` /
     `refreshToken.id` fields, `Authorization: Bearer` header, and the caveat that the 9.0 spec
     declares no `securitySchemes` so the header is prose-sourced.
   - §2 Token lifetimes — access 1 h, refresh 24 h; the 24 h ceiling on unattended operation.
   - P2 — SSO-issued role-scoped API tokens do not exist in 9.0 (9.1 only).
   - P3 — SDDC Manager excluded from VCF SSO in both versions.
   - P7 — a refresh-capable credential store must exist before the first call.
   - P8 / §5 — VMCA-signed by default; documented remedy is to replace or trust the certificate,
     not disable verification; `-k` in NSX docs is example-only.
   - P9 — connect by FQDN, not IP, because certs are issued to FQDNs.
   - §1.2/1.4/1.5 — per-product headers, used for the "this token is SDDC-Manager-only" note.
4. `/home/claude/vcf-skills/skills/vcf-foundation/references/deltas.md` — targeted read on token
   rows. Confirmed the three SDDC Manager token paths are spec-confirmed unchanged at 9.1.0.0
   (T7, and the SDDC Manager token API row), and that API clients / SSO tokens are 9.1-only (T1).
5. `/home/claude/vcf-skills/skills/vcf-api-discovery/SKILL.md` — Route 1 and the bundled-inventory
   vs raw-spec distinction ("do not infer a body field from an operation summary").
6. `/home/claude/vcf-skills/skills/vcf-api-discovery/references/spec-corpus.md` — §1, the tagged
   clone/worktree recipe.
7. `/home/claude/vcf-skills/skills/vcf-api-discovery/references/spec-inventory/9.0__sddc-manager.ops.json`
   — confirmed `createToken`, `refreshAccessToken`, `invalidateRefreshToken` exist at 9.0 with
   those exact paths and methods; confirmed `securitySchemes: {}`.
8. `.../spec-inventory/9.1__sddc-manager.ops.json` — same three paths present, none deprecated.

## Beyond the bundled inventory

The inventory carries operations, not schemas, and the skill is explicit that payload detail
requires the raw spec. Checked out tag `9.0.0.0` of `github.com/vmware/vcf-api-specs` and read
`specifications/sddc-manager/sddc-manager-openapi.json` directly, which confirmed:

- `TokenCreationSpec` = `{username, password, apiKey, idToken}` (all optional strings).
- `TokenPair` = `{accessToken, refreshToken:{id}}`; 201 on create.
- `PATCH /v1/tokens/access-token/refresh` — request body is a **JSON string** ("ID of the refresh
  token") under `application/json`; 200 response is likewise a bare string.
- `DELETE /v1/tokens/refresh-token` — JSON-string body, 204.

That last item is the one place the spec and Broadcom's prose sit slightly apart: prose says the
body is the plain-text UUID, while the spec types it as a JSON string under an `application/json`
content type, and a bare UUID is not strictly valid JSON. Rather than pick one, the script sends
it bare and retries quoted on a 400, and the answer flags it as the thing to watch on first run.

## Verification performed

Built a mock SDDC Manager (Python HTTPS server with a self-signed cert, 3-second access tokens,
strict-JSON refresh body) and exercised: first login with a password containing `"` and `\`;
cache hit across a `$(...)` subshell; expiry-driven refresh including the bare→quoted 400 retry;
mid-flight 401 with transparent retry; refresh-token rejection falling back to full login;
cross-process cache reuse; logout returning 204; wrong-password handling; TLS failing closed with
no CA bundle and `SDDC_INSECURE=0`; and the `--cacert` pin succeeding. `shellcheck` clean.

This caught a real bug in the first draft: state held in shell variables was silently discarded
because `$(sddc_token)` runs in a subshell, so the cache never hit and every call re-authenticated.
Fixed by moving the cache to a mode-0600 file.
