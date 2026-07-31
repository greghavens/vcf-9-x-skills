# Trace — skills and reference files consulted

## Task
"In VCF 9.1 SDDC Manager is gone and replaced by VCF Fleet Manager, right? What should I be
calling for lifecycle management now?"

Both premises in the question are false. The routing below was driven by that.

## 1. Skill triage

Read the frontmatter `description` of all four skills:

- `/home/claude/vcf-skills/skills/vcf-foundation/SKILL.md`
- `/home/claude/vcf-skills/skills/vcf-api-discovery/SKILL.md`
- `/home/claude/vcf-skills/skills/nsx-security-policy/SKILL.md`
- `/home/claude/vcf-skills/skills/vcf-lifecycle-upgrade/SKILL.md`

**Selected:** `vcf-lifecycle-upgrade` (primary), `vcf-api-discovery` (verification),
`vcf-foundation` (version routing, consulted lightly).
**Rejected:** `nsx-security-policy` — no DFW/microsegmentation content in the task.

The lifecycle skill's description matched the task explicitly on two clauses: "about what replaced
the 9.0 fleet management appliance" and "whenever someone asserts that SDDC Manager was removed or
replaced in 9.1 — that premise is wrong and needs correcting before the rest of the answer."

## 2. Files read in full

| File | Why |
|---|---|
| `/home/claude/vcf-skills/skills/vcf-lifecycle-upgrade/SKILL.md` | Primary routing. Its "Two premises to correct on contact" section is the direct answer to the question's framing. |
| `/home/claude/vcf-skills/skills/vcf-lifecycle-upgrade/references/9.1/lifecycle.md` | The substantive answer: the three LCM surfaces, `/fleet-lcm` and `/sddc-lcm` operation lists, SDDC Manager 9.1 additions, precheck relocation, task-polling namespaces, P0–P9 prerequisites. |
| `/home/claude/vcf-skills/skills/vcf-lifecycle-upgrade/references/deltas.md` | 9.0→9.1 delta table; confirmed the fleet-management appliance elimination, the SDDC-Manager-UI-only deprecation, the `/hvc/*` removal, and the licence-server addition. |
| `/home/claude/vcf-skills/skills/vcf-api-discovery/references/spec-inventory/SUMMARY.md` | Cross-product spec inventory — confirmed `fleet-lcm`/`sddc-lcm` absent at 9.0 and present at 9.1. |

Read partially: `/home/claude/vcf-skills/skills/vcf-foundation/SKILL.md` (Step 1 version-routing
section only — the user stated 9.1, so routing was already settled; noted `GET /v1/system` is the
wrong call for version detection but it did not need to appear in the answer).

Routed to but **not** read: `references/9.0/lifecycle.md` and `references/upgrade-runbook.md` — the
question is a 9.1 architecture question, not a 9.0 question and not an executable upgrade run. The
skill's Step 1 table says to read only the matching file.

## 3. Independent verification performed

The lifecycle skill instructs (final section) that any endpoint stated must be spec-confirmed rather
than inferred. Rather than take the reference file's counts on trust, I re-derived them from the
machine-extracted spec inventory:

```
python3 over /home/claude/vcf-skills/skills/vcf-api-discovery/references/spec-inventory/
  9.1__fleet-lcm.ops.json      ->  51 operations   (matches reference)
  9.1__sddc-lcm.ops.json       ->  26 operations   (matches reference)
  9.1__sddc-manager.ops.json   -> 423 operations   (matches reference)
  9.0__sddc-manager.ops.json   -> 375 operations   (matches reference)
```

Endpoint-level spot checks against the raw spec JSON:

- `9.1__fleet-lcm.ops.json` — confirmed all nine `upgrade-plans` operations exist, including
  `?action=configure`, `?action=precheck`, `?action=apply`, plus the four `tasks` operations with
  `?action=cancel|retry`.
- `9.1__sddc-manager.ops.json` — confirmed `POST /v1/upgrades/{upgradeId}/prechecks` and
  `GET /v1/upgrades/{upgradeId}/prechecks/{precheckId}` carry `deprecated: true`, while
  `/v1/hosts/prechecks` and `/v1/domains/{domainId}/isolation-prechecks` do not. Confirmed
  `POST /v1/tokens`, `PATCH /v1/tokens/access-token/refresh`, `DELETE /v1/tokens/refresh-token`
  present and not deprecated, and `POST /v1/upgrades` present and not deprecated.
- Grepped the whole spec inventory for "fleet manager" — **zero matches**, corroborating that no
  such product exists.

Everything asserted in the answer is either spec-confirmed by the above or explicitly flagged
UNVERIFIED.

## 4. Skill guidance carried into the answer

- Corrected both false premises up front, before answering the "what do I call" question — per the
  skill's "correct them early, because everything downstream inherits the error."
- Kept the two lifecycle orderings apart and did not fabricate the collapsed ranges (orders 2–5,
  9–23) — a named failure mode in the skill.
- Passed through the UNVERIFIED items rather than papering over them: fleet-lcm/sddc-lcm token
  issuance (P0, flagged blocking), lifecycle write-operation roles (P8), and the intra-range upgrade
  ordering. The skill states a checklist that looks complete but silently omits unverified items is
  worse than one with honest holes.
- Surfaced the OAuth-client migration hazard (P6) and the `/hvc/*` removal unprompted, since both
  break automation after the change window.
- Retained the "documentation, not live environment" sourcing caveat.
