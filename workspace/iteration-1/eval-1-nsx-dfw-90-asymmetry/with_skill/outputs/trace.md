# Trace — skills and reference files consulted

## Routing decision

Read the `description` frontmatter of all four skills, then selected:

- **`nsx-security-policy`** — primary. Task is a DFW rule blocking tcp/3389 between two NSX groups;
  the description names that exact phrasing ("block RDP between these two app tiers").
- **`vcf-foundation`** — consulted for version routing and NSX auth prerequisites. The
  `nsx-security-policy` SKILL.md explicitly defers version resolution here.
- **`vcf-api-discovery`** — used only to independently verify the "no NSX spec at the `9.0.0.0` tag"
  claim against the machine-extracted inventory. Did not need its full lookup workflow, since the
  NSX skill's own `lookup.md` covers the NSX case.
- **`vcf-lifecycle-upgrade`** — read description only; not applicable (no upgrade/patching/precheck
  content in the task).

Version was resolved at step 1 with no ambiguity: the user stated **VCF 9.0** explicitly. Per the
skill's instruction, I read **only** the 9.0 version file for endpoint material, and used the 9.1
side of `deltas.md` solely to characterise the evidence asymmetry — not to source 9.0 endpoints.

## Files read

| File | Why |
|---|---|
| `skills/nsx-security-policy/SKILL.md` | Routing, the evidence-asymmetry rule, object nesting, auth failure modes, drafts guidance |
| `skills/nsx-security-policy/references/9.0/dfw.md` (full, 870 lines) | The whole answer: prerequisites P1–P8, auth A1–A6, path tables with per-line evidence grades, the worked tcp/3389 example (Steps 0–7), failure-decode table, and the closing "what remains unverified for 9.0" list |
| `skills/nsx-security-policy/references/deltas.md` (full) | Confirmed the 9.0-vs-9.1 auth surface has no functional delta; sourced the `[ASYMMETRIC]` framing and the "removed operation paths are not published" fact |
| `skills/nsx-security-policy/references/lookup.md` (full) | Method A (`GET /api/v1/spec/openapi/nsx_policy_api.json`) as the only route to spec-grade 9.0 answers; the decision procedure at §G confirming method C does not apply to 9.0 |
| `skills/vcf-foundation/SKILL.md` | Version-resolution procedure; the "SSO-issued role-scoped API tokens are 9.1-only" prerequisite that shapes the service-account note |
| `skills/vcf-foundation/references/9.0/auth-and-identity.md` (grepped for NSX) | Cross-checked P6 (principal identities), §1.4 (NSX session cookie + XSRF), the 1800 s timeout, and the file's own statement that NSX 9.0 auth is prose-only |
| `skills/vcf-api-discovery/references/spec-inventory/SUMMARY.md` | Independent verification: `nsx-policy` / `nsx-manager` / `nsx-global-policy` all recorded `9.0 present: no`, present at 9.1 with 3729 / 1453 / 1009 ops |
| `skills/vcf-api-discovery/references/spec-inventory/index.json` | Confirmed which products *do* have 9.0 specs, to be sure the NSX absence was specific rather than a corpus-wide gap |

## Deliberately not read

- `skills/nsx-security-policy/references/9.1/dfw.md` — the SKILL.md warns that reading both version
  files is how contamination happens. Version was settled as 9.0, so the 9.1 file was skipped
  entirely; all 9.1-side facts in the answer came via `deltas.md`, which labels them as such.

## How the sources shaped the answer

The user asked two things: give the runbook, and state confidence. The 9.0 reference file supports
both directly because it tags every path with `[DOC-9.0]` / `[9.1-ONLY]` / `[INFERRED]`. The answer
therefore separates **paths and verbs (documented for 9.0, high confidence)** from **JSON schemas
(inferred from the 9.1 spec, low confidence)**, which is the actual shape of the uncertainty rather
than a blanket hedge.

Three 9.0-specific substantive divergences from what a 9.1 answer would say, all sourced from the
9.0 file's prerequisites:

1. Inline `service_entries` instead of a `/infra/services` reference (P6 — the services collection
   is unverified for 9.0).
2. Domain smoke test via `GET .../security-policies` instead of `GET /infra/domains` (P4 — the
   domain list endpoint is 9.1-only).
3. Principal identity + X.509 instead of an SSO-issued API token (P3 and vcf-foundation — token
   route is a 9.1 capability), including the 9.0 deprecation flag on principal identities.
