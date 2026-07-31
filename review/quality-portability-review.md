# Adversarial quality & portability review — VCF 9.x skill set

Reviewer: independent (did not author these skills). Date: 2026-07-31.
Target: `/home/claude/vcf-skills/skills/` — `vcf-foundation`, `vcf-api-discovery`,
`nsx-security-policy`, `vcf-lifecycle-upgrade`.

Severity scale: **BLOCKER** (ships broken) · **HIGH** (wrong behavior likely) ·
**MEDIUM** (degrades quality/usability) · **LOW** (polish).

---

## Part 1 — Routing

### 1.1 Measured facts

| Skill | `name` len | dir match | `description` chars | `compatibility` chars |
|---|---|---|---|---|
| `vcf-foundation` | 14 | ✅ | **661** | 140 |
| `vcf-api-discovery` | 17 | ✅ | **680** | 160 |
| `nsx-security-policy` | 19 | ✅ | **625** | 99 |
| `vcf-lifecycle-upgrade` | 21 | ✅ | **672** | 122 |

**No description exceeds the 1024-character open-spec limit.** All are between 625 and
680 characters — comfortably inside the limit, and also inside Claude Code's 1,536-char
`description` + `when_to_use` truncation cap. `compatibility` is under the 500-char cap in
all four. This particular gate is clean.

### 1.2 R1 — `vcf-foundation` claims universal territory and swallows the other three — **HIGH**

`vcf-foundation`'s description contains:

> "Use this **FIRST** for **any** VCF, vCenter, NSX, vSAN, SDDC Manager, VCF Operations,
> VCF Automation or VKS task … Trigger this even when the user does not say
> 'authentication' — if they want to **automate anything** against VCF …"

That is not a routing description, it is a claim on the entire product surface. Every task
the other three skills exist for is, literally, "a VCF task" or "an NSX task". At routing
time the model sees only name + description, so it has no basis to prefer
`nsx-security-policy` over a skill whose description says *use this first for any NSX
task*.

The body then does the opposite of what the description promises — it says "This skill
covers prerequisites and getting authenticated. It deliberately does not enumerate product
APIs." So the description over-claims relative to the body (see R5).

**Fix:** scope the trigger to the *auth/version-resolution* job and make the "first" claim
conditional and cheap, e.g. "…for the authentication, identity, certificate, role and
version-resolution part of any VCF task. Other VCF skills call into this one; if the task
is NSX firewall, lifecycle/upgrade, or finding an API operation, go to that skill and let
it pull this one in."

### 1.3 R2 — `vcf-api-discovery` has an unresolvable guard clause — **MEDIUM**

> "Use this whenever a VCF, vCenter, NSX, vSAN or PowerCLI task needs a call **that isn't
> already documented in another skill** …"

The router cannot evaluate that condition. Deciding whether a call is "already documented
in another skill" requires having loaded the other skills' bodies — which is precisely what
the routing decision is gating. In practice one of two things happens: the model ignores
the clause (over-triggering), or it treats it as a reason to defer (under-triggering).
Combined with the second trigger — "whenever you are about to state an endpoint, cmdlet or
CRD you have not confirmed" — this skill also has a near-universal claim.

**Fix:** replace with an observable condition: "Use this when the specific endpoint,
cmdlet or CRD is not present in the NSX firewall or lifecycle skill's reference tables, or
when the question is explicitly *does this exist in 9.0 vs 9.1*."

### 1.4 R3 — 12 realistic queries, predicted routing

Queries written as a VMware engineer would actually type them.

| # | Query | Should route to | Likely routes to | Verdict |
|---|---|---|---|---|
| 1 | "I'm getting a 403 when I try to create a DFW rule on NSX 9.1 — the token's fine, I just made it" | `nsx-security-policy` | **`vcf-foundation`** | ❌ **worst collision** — see below |
| 2 | "we're on 9.1, block RDP from app-tier group to db-tier group, both groups exist, give me the API calls" | `nsx-security-policy` | `nsx-security-policy` | ✅ clean |
| 3 | "SDDC Manager is gone in 9.1 right? how do we deploy a workload domain now" | `vcf-lifecycle-upgrade` | `vcf-lifecycle-upgrade` | ✅ clean — the description names this exact false premise |
| 4 | "what replaced the fleet management appliance in 9.1" | `vcf-lifecycle-upgrade` | `vcf-lifecycle-upgrade` | ✅ clean |
| 5 | "our precheck keeps failing on the mgmt domain before the 9.1 upgrade" | `vcf-lifecycle-upgrade` | `vcf-lifecycle-upgrade` | ✅ clean |
| 6 | "set up a service account so our automation platform can talk to NSX" | `vcf-foundation` (principal identities), with NSX detail | tie: `vcf-foundation` / `nsx-security-policy` | ⚠️ ambiguous — both descriptions claim service accounts |
| 7 | "does `Get-VcfHost` exist in VCF PowerCLI 9.1?" | `vcf-api-discovery` | tie: `vcf-api-discovery` / `vcf-foundation` | ⚠️ ambiguous — foundation's description claims "connecting PowerCLI", discovery's claims "PowerCLI task…cmdlet" |
| 8 | "what's the API to check upgrade status of an NSX edge cluster on 9.1?" | `vcf-lifecycle-upgrade` | tie: `vcf-lifecycle-upgrade` / `vcf-api-discovery` | ⚠️ ambiguous |
| 9 | "vCenter cert expired, PowerCLI won't connect any more" | `vcf-foundation` | `vcf-foundation` | ✅ clean |
| 10 | "can I still use `/api/v1` to create a firewall section?" | `nsx-security-policy` | `nsx-security-policy` | ✅ clean — explicitly named |
| 11 | "write me a script that tags every VM in the prod cluster and emails a report" | `vcf-foundation` then `vcf-api-discovery` | **probably none** | ❌ under-trigger — the query never says "VCF", so no description matches |
| 12 | "why is traffic between web and app tier getting dropped?" | `nsx-security-policy` | `nsx-security-policy` | ✅ clean — the exact phrasing is in the description |

Score: 6 clean, 3 ambiguous, 2 wrong/missed, 1 correct-but-lucky.

### 1.5 R4 — The worst query — **HIGH**

**Query 1: "I'm getting a 403 when I try to create a DFW rule on NSX 9.1 — the token's fine, I just made it."**

This is the single most damaging ambiguity in the set, because *both descriptions
explicitly name the trigger and the wrong one wins*:

- `vcf-foundation` says: "Use this **FIRST** … including … **debugging a 401/403**".
- `nsx-security-policy` says: "…NSX distributed firewall rules … DFW rules …".

The correct destination is `nsx-security-policy`, because it is the only skill that holds
the actual answer: *"Session expiry surfaces as HTTP 403, not 401"* and *"the session
cookie is bound to a single manager node."* A router that follows `vcf-foundation`'s
"use this FIRST … debugging a 401/403" instruction gets generic per-product auth material,
sends the user to check roles — and the skill body's own words describe exactly that
failure: *"people go chase roles that were fine all along."* The skill set therefore
routes the user into the failure mode one of its own skills warns about.

**Fix:** remove "debugging a 401/403" from `vcf-foundation`'s description, or qualify it
("…a 401/403 that is not product-specific"), and add "403 on an NSX call", "NSX session
expired", "XSRF" to `nsx-security-policy`'s description.

### 1.6 R5 — Over-claims in descriptions

| ID | Skill | Over-claim | Severity |
|---|---|---|---|
| R5a | `vcf-foundation` | Claims coverage for "VCF Automation or VKS task"; body delivers only auth/context-creation fragments (9 hits in `deltas.md`, 17/25 in the version files, mostly `vcf context create`). No VCF Automation or VKS *task* guidance exists. | MEDIUM |
| R5b | `vcf-api-discovery` | "roughly **13,000** operations" matches nothing in the corpus: 9.0 = 5,083; 9.1 = 11,590; union = 16,673. A routing-critical field states a number the skill's own `references/spec-corpus.md` contradicts. | LOW |
| R5c | `vcf-api-discovery` | Implies the bundled search script is usable. It is not, once packaged — see U1/P1 (BLOCKER). | HIGH |
| R5d | `vcf-foundation` | "Use this FIRST for any … NSX … task" while the body says it "deliberately does not enumerate product APIs" — description and body disagree. | HIGH |

### 1.7 R6 — What routes well

Credit where due: `vcf-lifecycle-upgrade` has the best description in the set. It names the
false premises users arrive with ("someone asserts that SDDC Manager was removed or
replaced in 9.1 — that premise is wrong"), which is a genuinely load-bearing trigger and
routes 4/4 lifecycle queries correctly. `nsx-security-policy` is second best: embedding
casual phrasings ("block RDP between these two app tiers", "why is this traffic being
dropped") is the right technique and works.

---

## Part 2 — Usability and bloat

### 2.1 Body sizes — clean

| Skill | `SKILL.md` lines | Under 500? |
|---|---|---|
| `vcf-lifecycle-upgrade` | 117 | ✅ |
| `nsx-security-policy` | 122 | ✅ |
| `vcf-api-discovery` | 124 | ✅ |
| `vcf-foundation` | 138 | ✅ |

All four are well inside the ~500-line guidance and inside the <5,000-token progressive-
disclosure recommendation. No body contains material that obviously belongs in
`references/` — the endpoint tables, payloads and worked examples are correctly pushed
down. **This part is done properly.**

### 2.2 U1 — `scripts/find_operation.py` is broken in every packaged deployment — **BLOCKER**

The single most serious defect in the set.

`vcf-api-discovery/SKILL.md` teaches the script as the primary route ("Route 1 — start
here"), but the inventory data it reads is **not in the skill bundle**. The script looks in
three places (`scripts/find_operation.py:70-74`):

```
1. <skill>/references/spec-inventory     -> DOES NOT EXIST
2. <skill>/spec-inventory                -> DOES NOT EXIST
3. <skill>/../../../research/spec-inventory  -> outside the skill root
```

Only candidate 3 resolves, and only because the skill currently sits inside the authoring
repo. Verified empirically:

```
$ cd /home/claude/vcf-skills/skills/vcf-api-discovery
$ python3 scripts/find_operation.py --version 9.1 "depot"
=== VCF 9.1 (git tag 9.1.0.0) — 56 matches across 14 products      # works

$ cp -r vcf-api-discovery /tmp/pk/ && cd /tmp/pk/vcf-api-discovery
$ python3 scripts/find_operation.py --version 9.1 "depot"
ERROR: no usable spec inventory found.                              # exit 2
```

`/tmp/pk/` is a faithful simulation of every real install target:
`~/.claude/skills/<name>/`, `.agents/skills/<name>/`, `~/.codeium/windsurf/skills/<name>/`,
`~/.triggerfish/workspace/<agent-id>/skills/<name>/`, and a ClawHub-published bundle. In
all of them the skill's headline capability fails.

Candidate 3 is also a **path traversal three levels above the skill root**. ClawHub's
security audit (SkillSpector / ClawScan, OWASP Agentic Skills Top 10, "unsafe execution")
is a plausible flagger of a bundled script that reads from `../../../` outside its own
directory. Triggerfish path-jails skill directories outright.

**Fix (required before any packaging):** copy `research/spec-inventory/` into
`vcf-api-discovery/references/spec-inventory/` (5.0 MB measured — trivially inside
ClawHub's 50 MB bundle limit and it keeps the file count near the ~40-file search-indexing
best-effort cap, which is acceptable since the JSON is data not prose), then **delete
candidate 3** so failures are honest rather than environment-dependent.

Partial credit: the failure message is excellent — it prints the regeneration recipe and
exits 2, not 0. That is the right behavior for a broken dependency.

### 2.3 U2 — Cross-skill evidence contradiction on NSX 9.1 authentication — **HIGH**

Two skills state incompatible evidence grades for the same fact.

`vcf-foundation/references/9.1/auth-and-identity.md:298-302`:

> "**NSX 9.1 auth prose could not be retrieved.** … The session-cookie flow
> (`POST /api/session/create` with `j_username`/`j_password`, `JSESSIONID` + `x-xsrf-token`)
> is **verified for 9.0 only**. **Do not assert it is unchanged in 9.1.**"

`nsx-security-policy/references/9.1/dfw.md:137-185` asserts exactly that flow for 9.1,
tagged `[SPEC — CreateAuthenticatedSession, 9.1__nsx-manager.ops.json …]` **and**
`[DOC — VCF 9.1 NSX admin guide]`, and `nsx-security-policy/SKILL.md` states it flatly in
the body with no version qualification at all.

The NSX skill's evidence is the stronger of the two (spec-confirmed), so `vcf-foundation`
is the stale one. But the skills are wired so `nsx-security-policy` tells the agent to
*"Use the `vcf-foundation` skill"* first — meaning the agent reads the prohibition
("do not assert it is unchanged in 9.1") *before* it reads the spec-confirmed
contradiction. The likely outcome is an agent that refuses to give the 9.1 auth flow, or
hedges it into uselessness, on a task the skill set demonstrably can answer.

**Fix:** one owner for NSX auth. Update `vcf-foundation/references/9.1/auth-and-identity.md`
§1.5 to cite the `CreateAuthenticatedSession` spec evidence and point at
`nsx-security-policy/references/9.1/dfw.md` §A1 as the authority, rather than leaving a
standing prohibition.

### 2.4 U3 — Reference-file routing is good; SKILL.md-body auth restatement is not — **MEDIUM**

**The routing itself is done well.** Every body has an explicit *what you need → which file
to read* table, not a vague "read the references":

- `vcf-foundation` — 4-row table, plus "Load the version file for the resolved version
  **only**."
- `nsx-security-policy` — 4-row table keyed on resolved version.
- `vcf-lifecycle-upgrade` — 4-row table, with the correct nuance that a 9.0→9.1 upgrade is
  legitimately in both versions and should use the runbook.
- `vcf-api-discovery` — per-route pointers plus a 7-row "Choosing a route" decision table.

That is above average for skill authoring and should be preserved.

**But the delegation the brief asked for is only half-done.** `nsx-security-policy` and
`vcf-lifecycle-upgrade` each mention `vcf-foundation` exactly **once**, and only for version
resolution — never for auth:

```
nsx-security-policy/SKILL.md:23    Use the `vcf-foundation` skill to resolve whether ...
vcf-lifecycle-upgrade/SKILL.md:42  Use the `vcf-foundation` skill. Then read only ...
```

`nsx-security-policy/SKILL.md` then spends a full section restating NSX session auth —
endpoint, form field names, both required headers, the 403 behavior, the node-binding
behavior — all of which `vcf-foundation` also carries
(`9.0/auth-and-identity.md:219-220,369,507`; `deltas.md:94`). Duplicated auth material
appears across the two dependent skills: 14 auth-token hits in each NSX version file, 4 in
`nsx/deltas.md`, 5 in `nsx/lookup.md`, 2 each in all four lifecycle references.

Some of that duplication is *justified* — the 403-is-session-expiry and single-node-binding
insights are firewall-debugging facts, and having the worked example self-contained is
correct. But the endpoint/payload restatement is what created U2. **Fix:** keep the
diagnostic insights in the NSX skill; replace the endpoint/payload restatement with a
pointer, and have the version files carry the canonical copy in exactly one place.

### 2.5 U4 — No reference file over 300 lines has a table of contents — **MEDIUM**

Zero of the 16 reference files contain a TOC (verified: no `## Contents` / `## Table of
Contents` / `**Contents**` heading anywhere in the tree). **Ten files exceed 300 lines:**

| File | Lines |
|---|---|
| `vcf-foundation/references/9.1/auth-and-identity.md` | **935** |
| `nsx-security-policy/references/9.1/dfw.md` | **757** |
| `nsx-security-policy/references/9.0/dfw.md` | **752** |
| `vcf-foundation/references/9.0/auth-and-identity.md` | **735** |
| `vcf-lifecycle-upgrade/references/9.1/lifecycle.md` | **614** |
| `vcf-foundation/references/powercli-session.md` | 410 |
| `vcf-lifecycle-upgrade/references/9.0/lifecycle.md` | 404 |
| `vcf-lifecycle-upgrade/references/upgrade-runbook.md` | 398 |
| `nsx-security-policy/references/lookup.md` | 306 |
| `vcf-api-discovery/references/doc-portal.md` | 301 |

A 935-line file with no navigational header forces a full read into context on every use —
which directly undermines the progressive-disclosure design the SKILL.md bodies otherwise
implement well, and burns against Claude's 5,000-token-per-skill compaction retention.

**Fix:** add a `## Contents` section-list to each of the ten. `9.1/dfw.md` is the easiest —
it already has 12 clean `##` headings; they just need surfacing at the top.

### 2.6 U5 — ALWAYS/NEVER vs soft-pedalled criticals — **LOW/MEDIUM**

**Rigid constructions are not a problem here.** The count is low (max 3 in any file) and
almost all are earned and explained rather than barked. Examples that work:

- `vcf-foundation/SKILL.md`: "Never answer a VCF question without knowing whether the
  target is 9.0 or 9.1 … Defaulting is how 9.1 facts end up in a 9.0 estate's runbook."
  The reason is attached; this is fine.
- The certificates section explicitly refuses to lecture, gives the working command *and*
  the correct path, and names the risk delta. This is a model of how to do it.

**One thing is stated too softly — MEDIUM.** In `vcf-foundation/SKILL.md`, the strongest
constraint in the entire skill set is delivered as a passing subordinate clause:

> "Read the `## Prerequisites` block at the top of the version-scoped reference file
> before you write any call."

Compare with the prominence given to version resolution (its own numbered Step 1, with a
"never" and a rationale). Yet all three dependent skills independently say prerequisites
are the highest-value content ("Prerequisites are most of the work"; "the prerequisite
block … is the highest-value part of this skill"; "Upgrade failures are overwhelmingly
readiness failures"). An agent under context pressure skips the sentence and keeps the
Step-1 instruction. **Fix:** promote it to the same structural weight as version
resolution.

### 2.7 U6 — Empty scaffold directories shipped — **LOW**

`vcf-api-discovery/references/9.0/` and `vcf-api-discovery/references/9.1/` are **empty
directories**. Nothing in `SKILL.md` references them, and the skill's actual reference files
are version-agnostic by design. They are leftover scaffolding that will confuse anyone
extending the skill (and are silently dropped by git and by ClawHub's file walker, so they
also create a dev-vs-published structural difference). Delete them.

### 2.8 U7 — `python` vs `python3` inconsistency — **LOW**

`vcf-api-discovery/SKILL.md:59-61` invokes `python scripts/find_operation.py`, while
`references/spec-corpus.md:115-118` and the script's own docstring use `python3`. On many
Linux distributions and on macOS `python` is absent or is Python 2. Since the SKILL.md body
is what the agent reads first, standardise on `python3` there.

---

## Part 3 — Portability across the five targets

Research consulted: `/home/claude/vcf-skills/research/skill-ecosystems.md` (agentskills.io
spec, Claude, Codex, Windsurf, Triggerfish) and
`/home/claude/vcf-skills/research/openclaw-marketplace.md` (OpenClaw/ClawHub).

### 3.1 Open-spec conformance — passes

| Check | Result |
|---|---|
| `name` ≤64 chars, `^[a-z0-9][a-z0-9-]*$`, no `--`, no leading/trailing hyphen | ✅ all four (14–21 chars) |
| `name` matches parent directory | ✅ all four |
| `description` 1–1024 chars | ✅ **661 / 680 / 625 / 672** — none over |
| `compatibility` ≤500 chars | ✅ 140 / 160 / 99 / 122 |
| `SKILL.md` <500 lines | ✅ 117–138 |
| Frontmatter keys are spec-legal | ✅ only `name`, `description`, `license`, `compatibility` |
| Canonical dirs (`scripts/`, `references/`) | ✅ |
| Relative file references from skill root | ✅ |
| No `${CLAUDE_SKILL_DIR}`, `$ARGUMENTS`, `{baseDir}` | ✅ verified absent — no Claude- or OpenClaw-only substitutions to strip |
| No symlinks anywhere in the tree | ✅ verified |
| All files UTF-8 / US-ASCII | ✅ verified |
| No hidden files | ✅ verified |
| Bundle sizes | 92 KB – 216 KB (5.1–5.3 MB once the spec inventory is bundled per U1) |

`name` contains neither "anthropic" nor "claude" in any skill — the claude.ai/Cowork
reserved-word gate passes.

### 3.2 P1 — ClawHub `metadata.openclaw.requires` declarations are entirely absent — **BLOCKER for ClawHub**

Per the ClawHub skill-format spec: *"If your code references `TODOIST_API_KEY` but your
frontmatter doesn't declare it under `requires.env`, `primaryEnv`, or `envVars`, the
analysis will flag a **metadata mismatch**."* None of the four skills declares anything.

**Environment variables found across the tree** (all in `vcf-foundation`):

| Variable | Location |
|---|---|
| `VCF_CLI_VCFA_API_TOKEN` | `references/9.1/auth-and-identity.md:434-435`, `references/deltas.md:105` |
| `VCFA_ENDPOINT` | `references/9.1/auth-and-identity.md:435` |
| `TENANT_NAME` | `references/9.1/auth-and-identity.md:436` |
| `VCF_CLI_VSPHERE_PASSWORD` | `references/9.0/auth-and-identity.md:340`, `references/deltas.md:105` |

All four are **optional** user-supplied credentials that appear in illustrative command
examples — none is required for the skill to load. So they belong under `envVars` with
`required: false`, **not** under `requires.env` (which is a hard gate that would make the
skill inert for anyone without them). `requires.env` should be empty/omitted for all four.

**Binaries actually invoked** (counted from real command lines, excluding prose uses of the
word "node" meaning an NSX manager node):

| Skill | Binaries | Notes |
|---|---|---|
| `vcf-foundation` | `vcf` (13), `git` (4), `kubectl` (2), `curl` (1), `pwsh` | `pwsh` implied by 29 PowerShell cmdlet invocations (`Connect-VcfSddcManagerServer`, `Get-Module`, `Import-Module`, `Get-Command`, `Get-Help`) and the explicit "PowerShell 7.x, not 5.1" requirement |
| `vcf-api-discovery` | `python3` (11), `kubectl` (21), `git` (13), `vcf` (6), `pwsh` | `python3` and `git` are load-bearing (bundled script + spec-corpus clone) |
| `nsx-security-policy` | `curl` (32), `python3` (1), `jq` (1) | |
| `vcf-lifecycle-upgrade` | `git` (4) | only in spec-corpus cross-references; no executable workflow |

Because none of these is required for the skill to *function as documentation* — all are
alternatives the user may or may not have — every binary belongs under `anyBins`, not
`bins`. `requires.bins` is an **AND** gate: declaring `[curl, git, python3, kubectl, pwsh]`
would render `vcf-foundation` inert on any machine lacking `pwsh`. The one genuine
exception is `vcf-api-discovery`, whose headline Route 1 genuinely requires `python3`.

**Exact declaration blocks to add.**

`vcf-foundation/SKILL.md`:

```yaml
metadata:
  openclaw:
    homepage: https://techdocs.broadcom.com/us/en/vmware-cis/vcf.html
    envVars:
      - name: VCF_CLI_VSPHERE_PASSWORD
        required: false
        description: Password for `vcf context create` against a Supervisor endpoint (9.0 and 9.1); alternative to interactive entry.
      - name: VCF_CLI_VCFA_API_TOKEN
        required: false
        description: VCF Automation API token for the 9.1 VCF-Automation-registered Supervisor context flow.
      - name: VCFA_ENDPOINT
        required: false
        description: VCF Automation endpoint used with `vcf context create` in the 9.1 flow.
      - name: TENANT_NAME
        required: false
        description: VCF Automation tenant name used with `vcf context create --tenant-name` in the 9.1 flow.
    requires:
      anyBins: [curl, pwsh, vcf, kubectl, openssl, git]
```

`vcf-api-discovery/SKILL.md`:

```yaml
metadata:
  openclaw:
    homepage: https://github.com/vmware/vcf-api-specs
    requires:
      bins: [python3]
      anyBins: [git, kubectl, pwsh, vcf, curl]
```

`nsx-security-policy/SKILL.md`:

```yaml
metadata:
  openclaw:
    homepage: https://techdocs.broadcom.com/us/en/vmware-cis/vcf.html
    requires:
      anyBins: [curl, python3, jq]
```

`vcf-lifecycle-upgrade/SKILL.md`:

```yaml
metadata:
  openclaw:
    homepage: https://techdocs.broadcom.com/us/en/vmware-cis/vcf.html
    requires:
      anyBins: [curl, git]
```

Caveat, stated honestly: the ClawHub research does not publish the audit's exact matching
heuristic, so whether an env var appearing only inside a fenced example in a `references/`
file triggers the mismatch check is not documented. Declaring them costs nothing and
removes the risk.

### 3.3 P2 — `license: MIT-0` must be REMOVED for ClawHub — **definitive, BLOCKER for ClawHub**

**Yes — the field must be deleted from all four `SKILL.md` files before publishing to
ClawHub. This is not a judgment call.** From the authoritative ClawHub skill-format spec
(`openclaw/clawhub`, `docs/skill-format.md`):

> "There is **no `author`, `license`, `tags`, `category`, `icon`, or `repository` field in
> skill frontmatter.**"
>
> "**`license`: forbidden to set.** All skills published on ClawHub are licensed under
> `MIT-0` … **Do not add conflicting license terms in `SKILL.md`; ClawHub does not support
> per-skill license overrides.**"

The intent behind `license: MIT-0` is correct — MIT-0 is exactly what ClawHub mandates. But
the *mechanism* is prohibited: ClawHub applies MIT-0 registry-wide and rejects the field
rather than reading it, so setting it is a per-skill override regardless of the value
matching. Note the field is legal and harmless in the open spec and for Claude, Codex and
Windsurf, and is ignored outright by Triggerfish's loader.

**Recommendation:** keep `license: MIT-0` in the canonical source (it is correct and useful
for the other four targets); strip it in the ClawHub packaging step only. This is one
`sed`/`yq` line in a build script, not a source change. If a single canonical artifact is
required for all five targets, drop it from source and put the MIT-0 statement in a
`LICENSE` file at the skill root instead.

### 3.4 P3 — Triggerfish needs top-level (NOT nested) security fields — **HIGH**

The research is unambiguous and was verified against Triggerfish's runtime loader source
(`src/tools/skills/loader.ts`, `buildSkillFromFrontmatter()`) and its shipped bundled
skills: the prose docs show these fields nested under `metadata.triggerfish.*`, **but the
loader reads them top-level**. Nesting them means they are silently ignored and the skill
falls back to `classification_ceiling: PUBLIC` — a security-relevant silent failure.

Recommended values and the reasoning:

| Skill | `classification_ceiling` | Why |
|---|---|---|
| `vcf-foundation` | **`CONFIDENTIAL`** | Handles API tokens, service-account credentials, certificate private material and role assignments for a customer's management plane. This is the highest-sensitivity skill in the set; anything below `CONFIDENTIAL` under-declares. |
| `nsx-security-policy` | **`CONFIDENTIAL`** | Handles NSX admin credentials (`j_username`/`j_password` in examples), session tokens, and produces production-affecting firewall changes. Getting this wrong severs management connectivity. |
| `vcf-lifecycle-upgrade` | **`CONFIDENTIAL`** | Touches SDDC Manager credentials, depot credentials, and drives largely irreversible fleet-wide upgrades. |
| `vcf-api-discovery` | **`INTERNAL`** | Reads public Broadcom specs and a bundled inventory. Its live-discovery route touches appliances but the skill itself carries no credential material. `INTERNAL` is the honest level — declaring `CONFIDENTIAL` here would be over-declaration, and enterprise Triggerfish rejects a ceiling above the user's clearance, so needlessly inflating it reduces who can run the skill. |

`requires_tools` should name Triggerfish's own tool vocabulary (per the shipped `pdf`
bundled skill: `run_command`, `write_file`, `read_file`), **not** binary names. A missing
tool flags but does not block, so this is advisory. `network_domains` should list only what
the skill actually reaches.

```yaml
# vcf-foundation — top-level, appended to existing frontmatter
version: 1.0.0
classification_ceiling: CONFIDENTIAL
requires_tools: [run_command, read_file]
network_domains: [techdocs.broadcom.com, developer.broadcom.com]

# vcf-api-discovery
version: 1.0.0
classification_ceiling: INTERNAL
requires_tools: [run_command, read_file, write_file]
network_domains: [github.com, raw.githubusercontent.com, developer.broadcom.com, techdocs.broadcom.com]

# nsx-security-policy
version: 1.0.0
classification_ceiling: CONFIDENTIAL
requires_tools: [run_command, read_file]
network_domains: [techdocs.broadcom.com, developer.broadcom.com]

# vcf-lifecycle-upgrade
version: 1.0.0
classification_ceiling: CONFIDENTIAL
requires_tools: [run_command, read_file]
network_domains: [techdocs.broadcom.com, developer.broadcom.com]
```

`network_domains` deliberately omits customer appliance hostnames — they are
per-deployment and cannot be enumerated. Flag this to the installing operator as a
site-specific addition rather than pretending the list is complete.

For **Reef marketplace publication** (not local install) also add top-level `author`, `tags`
(must be an array), and `category` — e.g. `category: development`, `tags: [vmware, vcf,
nsx, vsphere, infrastructure]`.

**Second Triggerfish issue — `references/` may not be read.** The research flags as
UNVERIFIED whether Triggerfish's loader surfaces `references/` at all: it "only reads
`SKILL.md` and never enumerates subdirectories," so progressive loading of `references/`
may not occur and "the agent would need an explicit instruction in the body to read them."
The bodies *do* contain explicit relative-path instructions ("Read
`references/9.1/dfw.md`"), which is the right mitigation — but this needs a smoke test on
Triggerfish before shipping. If the agent cannot read files under the skill directory, all
four skills lose ~95% of their content and become routing stubs.

### 3.5 P4 — Per-target packaging summary

| Target | Path | Changes required |
|---|---|---|
| **Claude** | `~/.claude/skills/<name>/` or `.claude/skills/<name>/` (Cowork/cloud: enable on the claude.ai account, commit to repo `.claude/skills/`, or ship in a repo-declared plugin — `~/.claude/skills/` is **not** read by Cowork/routines); claude.ai upload is a **zip** | **None to frontmatter.** Fix U1 first. |
| **OpenAI Codex** | `.agents/skills/<name>/` or `~/.agents/skills/` | **None.** Symlinks are followed, so one canonical dir can serve Claude and Codex. Optionally add `agents/openai.yaml`. |
| **Windsurf** | already reads `.agents/skills/`, `~/.agents/skills/`, `.claude/skills/`, `~/.claude/skills/` | **None, usually zero copying.** Do **not** downconvert to `.windsurf/rules/` or `.windsurf/workflows/` — 12,000-char cap and no auto-activation. |
| **Triggerfish** | `~/.triggerfish/workspace/<agent-id>/skills/<name>/` — **real directory copy, symlinks are skipped by the loader** | Add top-level `version`, `classification_ceiling`, `requires_tools`, `network_domains` (**never** under `metadata:`). Budget for a one-time owner classification/approval step. Smoke-test `references/` loading. |
| **OpenClaw / ClawHub** | `<workspace>/skills`, `<workspace>/.agents/skills`, `~/.agents/skills`, `~/.openclaw/skills`; publish via `clawhub skill publish ./<skill> --dry-run` then for real | **Remove `license:` (P2).** Add `metadata.openclaw.requires`/`envVars` (P1). Fix U1 — the `../../../` traversal is audit-visible. Slug matches `^[a-z0-9][a-z0-9-]*$` ✅. Bundle stays far under 50 MB ✅. |

### 3.6 P5 — Breakage scan: what is clean

Explicitly checked and **clear** across all four skills:

- **Symlinks** — none anywhere in the tree. Safe for Triggerfish (skips them) and ClawHub
  (excludes them from published bundles).
- **Non-UTF8 files** — none; every file is UTF-8 or US-ASCII.
- **Oversized bundles** — 92 KB–216 KB now; 5.1–5.3 MB after the U1 fix. ClawHub's limit is
  50 MB.
- **`name` vs directory mismatch** — none.
- **Hidden files / macOS metadata** — none (these are silently dropped by ClawHub publish).
- **Claude-only substitutions** (`${CLAUDE_SKILL_DIR}`, `$ARGUMENTS`) — none.
- **OpenClaw-only `{baseDir}`** — none.
- **Reserved words "anthropic"/"claude" in `name`** — none.

**One caveat on file count:** ClawHub's vector-search embedding covers `SKILL.md` plus
"up to ~40 bounded UTF-8 files (best-effort cap)." Bundling `spec-inventory/` adds ~23 JSON
files to `vcf-api-discovery`, taking it to ~28 files total. Still under the cap, but note
that the JSON payloads consuming embedding budget will *dilute* search relevance for a
prose-driven discovery skill. Consider a `.clawhubignore` entry for
`references/spec-inventory/*.ops.json` — ClawHub still **uploads** ignored-by-embedding
content? No: `.clawhubignore` excludes files from the published bundle entirely, which
would re-break the script. **Do not ignore them** — accept the embedding dilution.

**One structural note:** `skills/evals/` sits alongside the four skill directories and
contains `evals.json` with no `SKILL.md`. Harmless for Claude/Codex/Windsurf. OpenClaw
discovers skills recursively (any `SKILL.md` up to 6 levels under a configured root), so
`evals/` is correctly ignored — but if `skills/` is ever used as a ClawHub `sync --all
--root ./skills` target, keep `evals/` out of the publish set.

---

## Consolidated defect register

| ID | Severity | Finding |
|---|---|---|
| U1 / R5c | **BLOCKER** | `find_operation.py` cannot find its inventory once packaged; only works inside the authoring repo via a `../../../` traversal |
| P1 | **BLOCKER (ClawHub)** | No `metadata.openclaw.requires`/`envVars` declarations → automated metadata-mismatch flag |
| P2 | **BLOCKER (ClawHub)** | `license: MIT-0` is a prohibited per-skill override; must be stripped for ClawHub |
| R1 / R5d | **HIGH** | `vcf-foundation` description claims "any VCF/NSX/vSAN… task", swallowing the other three and contradicting its own body |
| R4 | **HIGH** | "403 on a DFW rule" routes to `vcf-foundation`, not `nsx-security-policy` — into the exact failure the NSX skill warns about |
| U2 | **HIGH** | `vcf-foundation` forbids asserting NSX 9.1 session auth; `nsx-security-policy` asserts it with spec evidence |
| P3 | **HIGH** | Triggerfish security fields absent; must be **top-level**, and `references/` loading is unverified |
| R5c | **HIGH** | Description implies a working bundled search script (see U1) |
| R2 | **MEDIUM** | `vcf-api-discovery` guard clause ("isn't already documented in another skill") is unresolvable at routing time |
| R5a | **MEDIUM** | `vcf-foundation` over-claims VCF Automation / VKS task coverage |
| U3 | **MEDIUM** | Dependent skills delegate to `vcf-foundation` for version only, not auth; auth endpoint/payload restated |
| U4 | **MEDIUM** | 10 reference files >300 lines, zero with a table of contents (largest: 935) |
| U5 | **MEDIUM** | "Read the Prerequisites block" — the set's most-emphasised constraint — is a passing clause in `vcf-foundation` |
| R5b | **LOW** | "roughly 13,000 operations" matches no figure in the corpus (5,083 / 11,590 / 16,673) |
| U6 | **LOW** | Empty `vcf-api-discovery/references/9.0/` and `9.1/` scaffold directories |
| U7 | **LOW** | `python` vs `python3` inconsistency between SKILL.md and references |

## What is genuinely good

Stated for calibration, not politeness: all four `SKILL.md` bodies are 117–138 lines with
real reference-routing tables rather than "read the references"; the evidence-grading
system (`[SPEC]`/`[DOC]`/`[INFERRED]`) and the "a miss in an absent spec is not evidence"
rule are better epistemic hygiene than most skill sets have; the ALWAYS/NEVER problem the
brief anticipated does not exist here; the certificates section models how to give a user
the command they asked for *and* the correct path without lecturing; `vcf-lifecycle-upgrade`'s
false-premise triggers are the best description-writing in the set; and the frontmatter is
already open-spec clean with no descriptions anywhere near the 1024-character limit.
