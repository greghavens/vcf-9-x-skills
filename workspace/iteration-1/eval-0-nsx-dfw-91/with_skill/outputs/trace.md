# Trace — eval-0-nsx-dfw-91 (with_skill)

## Order of consultation

1. **Listed** `/home/claude/vcf-skills/skills/` and read the YAML frontmatter (`description`) of all
   four SKILL.md files to route.
   - Routed **in**: `nsx-security-policy` (DFW rules, "block RDP between two app tiers" is a verbatim
     trigger phrase in its description) and `vcf-foundation` (auth; the NSX skill's description says
     to consult foundation alongside it, not instead of it).
   - Routed **out**: `vcf-lifecycle-upgrade` (no upgrade/patch/precheck element in the task) and
     `vcf-api-discovery` (not needed — the NSX skill's own 9.1 reference file carries spec-confirmed
     endpoints for everything the task requires; discovery is the fallback for uncovered endpoints).

2. **Read** `/home/claude/vcf-skills/skills/nsx-security-policy/SKILL.md` (full).
   Key routing instruction taken from it: settle the version first, then read **only** that version's
   reference file; start from the worked example rather than assembling calls from the tables.

3. **Read** `/home/claude/vcf-skills/skills/vcf-foundation/SKILL.md` (full).
   Step 1 (resolve version) was satisfied directly by the user's statement — "We're on VCF 9.1" —
   so no environment query or clarifying question was needed. Version pinned to 9.1.

4. **Read** `/home/claude/vcf-skills/skills/nsx-security-policy/references/9.1/dfw.md` (full, 947 lines).
   This is the primary source for the answer: Prerequisites P1–P8, Authentication A1–A7, the
   Groups / Security policies / Rules endpoint tables, rule ordering and `?action=revise`, drafts,
   and the Worked example (Steps 0–7 plus the failure-decode table).

5. **Read** `/home/claude/vcf-skills/skills/vcf-foundation/references/9.1/auth-and-identity.md`
   (lines 1–637 of 1051; stopped at §4 Roles). Section **1.5 NSX Manager / NSX Policy / NSX Global
   Policy** and §2 (token lifetimes — NSX `JSESSIONID` row) corroborated the DFW file's auth flow;
   P9 supplied the TLS/VMCA trust posture and §4 the VCF-role → `enterprise_admin` mapping. Did not
   page further — the remaining sections (spec-vs-prose conflicts, source index) were not needed for
   an NSX-scoped answer.

## Files NOT read, deliberately

- `references/9.0/dfw.md` and `references/9.0/auth-and-identity.md` — the version was resolved to
  9.1; both skills warn explicitly that reading both version files is how cross-version
  contamination happens.
- `references/deltas.md` (both skills) — the task is not a version-comparison question.
- `references/lookup.md` and the `vcf-api-discovery` skill — no endpoint in the answer was
  unconfirmed, so the lookup/discovery escape hatch was not required.
- `references/powercli-session.md` — the user asked for API calls, not PowerCLI.

## Skill guidance that materially shaped the answer

- **Nesting**: rule inside security policy inside domain; no top-level rule endpoint. Led the answer
  rather than being a footnote.
- **Policy API only**: flagged `/api/v1` and deprecated `communication-maps` as dead ends up front.
- **Both credentials on every call** (`JSESSIONID` + `X-XSRF-TOKEN`), and the two disguised failures:
  expiry surfaces as **403 not 401**, and cookies are bound to a single manager node.
- **P5 group-path capture**: use the server-returned `.path`, never a hand-assembled string; the
  worked example's fail-closed guard was carried through verbatim.
- **P3 verification discipline**: read the role binding rather than probing write permission by
  performing the production write.
- **Ordering caveat**: `Application` is the lowest-precedence L3 category, so a correct rule can be
  shadowed — surfaced with `GetFilteredRules` as the diagnostic.
- **Drafts raised unprompted**, per the skill's instruction to offer them for changes that would be
  hard to unwind, while noting a DROP rule here is comparatively low-risk.
- **TLS honesty**: gave the working `-k` command plus the one-line proper path, per the foundation
  skill's instruction not to lecture but not to make the tradeoff invisible.
- **Provenance stated**: [SPEC]-backed for 9.1, nothing run live; the A7 token-PI wire-format gap and
  the P8 "no authoritative VCF-ownership list" gap both surfaced rather than papered over.
- **Path families** (project / VPC / global-infra read-only) flagged as a caveat, since the answer
  assumes single-tenant `/infra/`.
