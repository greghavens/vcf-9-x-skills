# Trace — skills and reference files read

## Routing decision

Read the `description` frontmatter of all four SKILL.md files first.

| Skill | Used? | Why |
|---|---|---|
| `vcf-foundation` | **Yes — primary** | Description explicitly covers "getting or refreshing an API token", service accounts/API clients, role selection, TLS trust, and "the version router that determines whether an estate is 9.0 or 9.1". Also says to "check here first whenever a VCF version has not yet been established" — exactly this task. |
| `vcf-api-discovery` | No | Reserved for confirming endpoints not documented elsewhere. Every endpoint needed here was already documented and spec-cited inside vcf-foundation's reference files, so there was nothing to discover. |
| `nsx-security-policy` | No | Task is not DFW/microsegmentation. NSX *auth* (session cookie + XSRF, principal identities) is held in vcf-foundation, which is where I took it from. |
| `vcf-lifecycle-upgrade` | No | No upgrade, patch, precheck, bundle or depot content in the task. |

## Files read

1. `/home/claude/vcf-skills/skills/*/SKILL.md` — frontmatter/description of all four, for routing.
2. `/home/claude/vcf-skills/skills/vcf-foundation/SKILL.md` — full read. Gave the 3-step procedure (resolve
   version → check prerequisites → authenticate per product), the version-resolution order, the
   `GET /v1/system/appliance-info` vs `GET /v1/system` trap, the certificates/TLS posture, the roles guidance,
   and the honest-reporting instruction.
3. `/home/claude/vcf-skills/skills/vcf-foundation/references/deltas.md` — full read. Traps T1–T10, the
   9.0-vs-9.1 API-client/token table, per-product auth deltas.
4. `/home/claude/vcf-skills/skills/vcf-foundation/references/9.0/auth-and-identity.md` — read (lines 1–661 of
   790; prerequisites P1–P11, all of §1 per-product auth, §2 lifetimes, §3 SSO architecture, §4 roles,
   §5 certificates, §6 reachability, §7 spec-vs-prose conflicts, §8 UNVERIFIED list).
5. `/home/claude/vcf-skills/skills/vcf-foundation/references/9.1/auth-and-identity.md` — read (lines 1–637 plus
   638–767; prerequisites P0–P13, §1 per-product auth incl. identity broker token endpoint, §2 lifetimes,
   §3 SSO architecture + UI issuance flow, §4 roles incl. the built-in role mapping table, §5 the 70-operation
   IAM API surface, §6 certificates).
6. `/home/claude/vcf-skills/skills/vcf-foundation/references/powercli-session.md` — targeted grep for
   `VcfApiToken` / `VcfOAuthSecurityContext` / `Install-Module` / connect cmdlets / cert flags, rather than a
   full read.

## How the missing version was handled

Followed the SKILL.md step-1 ladder. The user did not state a version (rule 1 fails); there is no API
reachability from this session to query the estate (rule 2 unavailable). That left rule 3, "ask the user", and
the documented fallback for when the user needs an answer now: **give the answer for both versions with each
clearly labelled, and say why it was split. Never blend them.**

So the answer does three things: (a) asks the one prescribed question — *"Is this a 9.0 or a 9.1 fleet? If
you're not sure, what does SDDC Manager report under About?"*; (b) supplies the self-service
`appliance-info` check, bootstrapped via the SDDC Manager `POST /v1/tokens` flow since that is identical in both
versions and resolves the auth chicken-and-egg; and (c) gives fully separated 9.0 and 9.1 sections plus a
"true on both versions" section.

I deliberately read both version files despite SKILL.md's "load the version file for the resolved version only"
guidance — that instruction is scoped to the case where step 1 *has* resolved, and the split-answer fallback
requires both. Bleed was managed by keeping the two sections structurally separate and never stating a fact
from one file under the other's heading.

## Skill-driven content that shaped the answer

- **Headline framing** from P2 in both files: SSO-issued role-scoped API tokens are 9.1-only, verified by both a
  doc-tree check and a spec check (0 vs 70 `/api/fleet-management/iam/**` operations). The 9.0 answer states
  plainly that the flow they've read about doesn't apply, then gives the real 9.0 route.
- **SDDC Manager / ESX excluded from VCF SSO in both versions** (P3 / P6) — called out because an agent
  assuming one fleet-wide token fails here specifically.
- **vCenter 9.0 non-federated login block** (P4) — included with the diagnostic note that it presents as an auth
  rejection, not a cert error.
- **TLS section** written per SKILL.md's explicit instruction: give the working command *and* the one-line
  proper path, name the management-plane-vs-test-API risk difference, and don't lecture. PEM-only import kept
  scoped to 9.1 as the 9.0 file instructs.
- **Roles** — 9.1 built-in role mapping table used for 9.1; per-component authorization used for 9.0, with the
  9.1 role names withheld from the 9.0 section per P5/P8.
- **Path disambiguations** carried through: `POST /api/session` over the prose `/api/cis/session`; `GET
  /v1/system/appliance-info` over `GET /v1/system`.
- **Honest reporting section** built from the consolidated UNVERIFIED lists (VCF Installer auth, VCF Automation
  All Apps endpoint and 9.0 token field, broker endpoint in 9.0, inbound ports, PowerCLI cmdlet coverage,
  vCenter 9.1 federation status).
