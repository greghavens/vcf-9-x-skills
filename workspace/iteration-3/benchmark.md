# Skill Benchmark: vcf-9x-skills — iteration 3

**Why**: regression check after converting British spellings to American English
across the skill content (commit 9df58e4). Prose-only change; no endpoint, field
name or enum value was altered.

**Evals**: 0, 1, 2, 4, 5, 6, 8 — 3 runs each per configuration (42 runs, 126 assertions)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Assertions passed | 120/126 (95%) | 85/126 (67%) | +28 pts |
| Per-run pass rate | 94% ± 14% | 65% ± 17% | +29 pts |

## Per eval (run 1 / run 2 / run 3)

| Eval | With skill | Without skill |
|---|---|---|
| 0 — nsx-dfw-rule-91 | 9/9 9/9 9/9 | 8/9 8/9 8/9 |
| 1 — nsx-dfw-rule-90-evidence-asymmetry | 5/5 5/5 5/5 | 4/5 4/5 4/5 |
| 2 — sddc-manager-gone-trap | 6/6 6/6 6/6 | 3/6 3/6 3/6 |
| 4 — router-no-version-given | 5/5 5/5 5/5 | 3/5 2/5 2/5 |
| 5 — sddc-manager-token-bash | 7/7 7/7 7/7 | 5/7 5/7 6/7 |
| 6 — discovery-uncovered-operation | 3/5 3/5 3/5 | 3/5 3/5 3/5 |
| 8 — prereq-api-client-90-does-not-exist | 5/5 5/5 5/5 | 3/5 2/5 3/5 |

## Eval 6 is the one soft spot

Six of seven evals passed every assertion on every with_skill run. Eval 6 scored
3/5 on all three runs and showed **no lift over baseline** (also 3/5). The two
missed assertions:

- *Mentions at least one on-appliance discovery route (VCF Operations swagger UI
  or the NSX openapi spec endpoint)*
- *Notes that no on-appliance API-explorer URL pattern is documented for VCF 9.x*

Both facts are present in `vcf-api-discovery/references/live-discovery.md` (§2 and
§3), and all three run traces confirm that file was read. The answers simply did
not surface them. This is answer selection, not missing content — the spelling
conversion touched two words in this skill (`labelling`→`labeling`,
`behaviour`→`behavior`), neither in the affected sections.

Iteration 1 scored 5/5 here, so this is a difference from the earlier result, not
a pass. Candidate causes: a different runner harness (subagents, no bundled
lookup script invoked), and the run instruction to answer strictly from the skills.
Worth a routing/emphasis fix in `vcf-api-discovery` SKILL.md so the on-appliance
routes get pulled into the answer rather than merely read.

## Comparability

Not directly comparable to `iteration-1/benchmark.md` (98% / 73%). That run used
the project's own harness over 12 evals; this one re-ran the 7 benchmarked evals
through a subagent runner with independent graders. Use it as a before/after
regression signal on the spelling change, not as a replacement headline number.
