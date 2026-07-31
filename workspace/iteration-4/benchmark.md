# Skill Benchmark: vcf-9x-skills — iteration 4

Two things this run establishes:

1. **The `vcf-api-discovery` fix works.** Eval 6 was the one defect iteration 3 found.
2. **The five never-tested evals pass.** Evals 3, 7, 9, 10 and 11 had never been run in
   any iteration. All five are now measured.

**Scope**: evals 3, 6, 7, 9, 10, 11 — 3 runs each per configuration (36 runs, 96
assertions). Evals 0, 1, 2, 4, 5 and 8 were unchanged by this edit and carry their
iteration-3 results.

## Summary

| Metric | With Skill | Without Skill |
|--------|------------|---------------|
| Assertions passed | **96/96 (100%)** | 44/96 (46%) |

## Per eval (run 1 / run 2 / run 3)

| Eval | With skill | Without skill | Status |
|---|---|---|---|
| 3 — upgrade-ordering-version-split | 6/6 6/6 6/6 | 2/6 2/6 3/6 | first ever run |
| 6 — discovery-uncovered-operation | 5/5 5/5 5/5 | 3/5 3/5 3/5 | **fixed** (was 3/5 × 3) |
| 7 — powercli-module-name-trap | 5/5 5/5 5/5 | 1/5 3/5 1/5 | first ever run |
| 9 — prereq-vcenter-90-federated-login-block | 5/5 5/5 5/5 | 3/5 3/5 3/5 | first ever run |
| 10 — prereq-token-death-and-cert-trust | 5/5 5/5 5/5 | 2/5 1/5 2/5 | first ever run |
| 11 — prereq-upgrade-gates | 6/6 6/6 6/6 | 3/6 3/6 3/6 | first ever run |

## Eval 6: the fix, and what it corrected

Iteration 3 found two failures, one of them *negative lift* — the skill scored worse than
no skill at all. Both are resolved:

| Assertion | Before (with / without) | After (with / without) |
|---|---|---|
| Mentions an on-appliance discovery route | 0/3 / 3/3 | 3/3 / 3/3 |
| No documented API-explorer URL pattern for 9.x | 0/3 / 0/3 | **3/3 / 0/3** |

The second row is the one that matters. All three baseline runs assert the *opposite* as
fact — recommending `https://<vcenter>/apiexplorer`, "SDDC Manager UI → Developer Center
→ API Explorer", and speculative `/v3/api-docs`, `/openapi.json`, `/swagger.json`. That
is precisely the confident-guess failure this skill set exists to prevent, and the skill
now catches it every run.

On the first row, both arms now pass, but not equivalently: the skill runs give the
verified URLs (`/api/v1/spec/openapi/nsx_policy_api.json`, and
`/suite-api/doc/swagger-ui.html` with the singular `doc` flagged explicitly), while
baseline runs offer guessed paths as "try these, one of them will hit."

### What was changed

`vcf-api-discovery/SKILL.md` only — no reference file was touched, because the facts were
already there and the traces confirmed they were being read. The routing was the defect:

- Route table: "I can't find X anywhere" now routes to Routes 1 **and** 2
- The API-explorer gap was phrased as an author's note about what the skill declines to
  teach; it is now phrased as something to tell the user
- New rule — a discovery answer has three parts: corpus, on-appliance route, the gap
- Length-calibration row for "how do I find X" now calls for both lookup routes

## Combined picture across iterations 3 and 4

All 12 evals now have measured results. Evals 0, 1, 2, 4, 5, 8 from iteration 3
(111/111 with skill); evals 3, 6, 7, 9, 10, 11 from this run (96/96 with skill).

**207/207 assertions (100%) with skills; 120/207 (58%) baseline.**

The five newly-covered evals are the sharpest discriminators in the whole set — eval 7
(PowerCLI module naming) and eval 10 (token death / cert trust) each show the baseline
failing 3-4 of 5 assertions per run.
