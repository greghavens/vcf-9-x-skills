# The brief, as I'm holding it

Restated so you can confirm nothing was lost. Nothing here is new — this is your
prompt plus the two mid-flight additions, compressed.

## Goal

Build installable agent skills covering **VMware Cloud Foundation 9.0 and 9.1**,
including NSX, VCF Automation, VCF Operations, vSAN, SDDC Manager, Fleet Manager,
vCenter, vSphere. Author once in the open `SKILL.md` (Agent Skills) format, then
package per platform at the end.

**Targets:** Claude, Codex, Windsurf, **Triggerfish (trigger.fish)**, **OpenClaw /
ClawHub marketplace**.
- Triggerfish: you told me it's trigger.fish. Verified real; consumes `SKILL.md`.
- OpenClaw: you added marketplace deployability mid-flight. Verified real and live.

## Research mandate

- Assume training knowledge of 9.0 and especially 9.1 is incomplete or wrong.
  **No skill content from memory.** Every claim from live research during this task.
- Deep-research current official docs first: techdocs.broadcom.com,
  developer.broadcom.com (API refs + OpenAPI specs), 9.0 and 9.1 release notes,
  per-product docs, PowerCLI reference, VKS docs.
- **Research each product per version** — pull the 9.0 and 9.1 doc sets separately;
  note restructures, renames, deprecations between them.
- Research current best practices for authoring/installing skills in each target
  ecosystem, since those formats are recent and evolving.
- Parallel research agents per product/version. Build a source inventory
  (URL + version + date accessed) as you go.
- If something can't be found or is ambiguous, **say so in the skill** rather than
  filling the gap from memory.

## Design philosophy

- Skills are **not** API mirrors. Don't enumerate every endpoint/cmdlet inline —
  that produces stale, context-blowing skills.
- Each skill contains: workflow guidance, auth/session setup, prerequisites, version
  gotchas, worked examples of common operations — **plus** `references/` files that
  condense or index the full API surface, **plus** explicit instructions teaching the
  agent how to look up anything not covered (API explorer, developer.broadcom.com,
  `Get-Command`/`Get-Help`, OpenAPI specs, kubectl/vks discovery).
- **Coverage target:** an agent using these skills can reach *every* exercisable
  operation — some directly, the rest via taught lookup patterns. That's the standard,
  not "every option written out."

## Version separation — hard rule

- 9.0 and 9.1 are materially different. **Every fact version-tagged.**
- Propose the architecture up front: separate trees per version, or shared skills with
  per-version reference files plus a router step that determines target version first.
- Explicitly call out everything that changed between 9.0 and 9.1.
- **Cross-contamination is the #1 failure mode** — any 9.0 fact in a 9.1 context is a bug.

## Skill taxonomy

- Split by **product × task-domain**, not one skill per API. Roughly 10–25 skills;
  propose the exact list before building.
- Dedicated **foundation skill**: prerequisites and environment setup — certificates,
  SSO/identity, roles and permissions, network reachability, token acquisition per
  product, PowerCLI session setup. Other skills reference it rather than repeat it.
- Write each description so an agent routes reliably; run description optimization on
  the final set.
- Bundle scripts where test runs show repeated work.

## Verification — mandatory, replaces a live environment

1. **Source traceability.** No API call, cmdlet, endpoint or parameter without a
   citation to a specific Broadcom doc URL / OpenAPI spec and its version, drawn from
   the source inventory. Prefer published specs over prose for payloads and parameters.
2. **Acceptance criteria first.** Before drafting each skill, write test prompts with
   concrete assertions. Run the eval loop with graders — don't skip it.
3. **Adversarial review.** After drafting, separate review passes by *independent
   agents* hunting: hallucinated endpoints/cmdlets, wrong API versions, 9.0/9.1 bleed,
   missing prerequisites. Anything unverifiable gets removed or flagged.
4. **Honest caveat** in every skill: built from documentation, not validated against a
   live environment; verify destructive operations before execution.

## Process — phased, with checkpoints

1. **Phase 1 — Research & taxonomy.** Deliver proposed skill list with per-skill scope,
   the version-architecture decision, and the source inventory. **Stop for sign-off.**
   → *Delivered. Awaiting your sign-off.*
2. **Phase 2 — Pilot.** Build 2–3 representative skills fully (including the prereqs
   skill), run evals, show results. **Stop for review.**
3. **Phase 3 — Scale.** Apply the validated pattern to the rest, same eval +
   adversarial verification each. Then optimize descriptions and package per platform.

"Iterate several times" means against these criteria — not rereading my own output.

## Where Phase 1 landed

- 301 unique source URLs, 10 research dossiers, all fetched 2026-07-31.
- Machine-readable OpenAPI corpus from git tags `9.0.0.0` and `9.1.0.0` of
  `github.com/vmware/vcf-api-specs` — ~13,000 operations extracted and diffed.
- 19 proposed skills, shared-tree + version-scoped-references + router architecture.
- Three corrections to the brief's premises (Fleet Manager doesn't exist; SDDC Manager
  isn't gone in 9.1; NSX has no 9.0 spec).

## Open decisions blocking Phase 2

1. Version architecture — shared tree + version-scoped references + router (my
   recommendation), or fully separate 9.0/9.1 trees?
2. Skill count — keep 19, or merge down to 18 or 17?
3. Third pilot skill — `nsx-security-policy` or `vcf-lifecycle-upgrade`?
4. Confirm all five packaging targets.
