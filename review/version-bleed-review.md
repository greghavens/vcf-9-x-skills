# Version-bleed review — 9.0 / 9.1 cross-contamination and wrong API versions

Adversarial review of `/home/claude/vcf-skills/skills/` (4 skills, 21 files), cross-checked against
`research/*.md` (version-tagged dossiers) and `research/spec-inventory/` (machine-extracted
operation inventories + `DELTA-9.0-to-9.1.md`). Date: 2026-07-31.

**Verification performed:** every `[SPEC]`-graded path/operationId in `nsx-security-policy/references/9.1/dfw.md`
was checked against `9.1__nsx-policy.ops.json` / `9.1__nsx-manager.ops.json` (24 operationIds + the
12 `communication-maps` deprecations — **all correct, zero false claims**). Every
`spec-confirmed (9.0)` / `spec-confirmed (9.1)` endpoint in the three lifecycle files was checked
against `9.0__sddc-manager.ops.json` / `9.1__sddc-manager.ops.json` / `9.1__fleet-lcm.ops.json` /
`9.1__sddc-lcm.ops.json` (~40 paths — **all correct**, including the 21-deprecation list, the
`/v1/system/precheck` absence in both tags, and the `upgrades/{id}/prechecks` deprecation flip).
`nsx-security-policy/references/9.0/dfw.md` was audited specifically for `[SPEC]`-graded 9.0 claims:
**none found** — the file uses `[DOC-9.0]` / `[DOC-9.0-partial]` / `[9.1-ONLY — NOT VERIFIED FOR 9.0]` /
`[INFERRED]` throughout and hunt item #4 produced no blocker.

---

## Findings

| # | File | Claim | Stated version | Correct version | Evidence | Severity |
|---|---|---|---|---|---|---|
| 1 | `vcf-foundation/references/9.0/auth-and-identity.md:196` (+ `:373`) | "Session operations: `POST /api/cis/session` (create), `GET /api/cis/session` (inspect), `DELETE /api/cis/session` (invalidate)" — stated flatly as a 9.0 fact | implied 9.0 (file is scoped "VCF 9.0 only") | **9.1-sourced; unverified for 9.0** | Cited `[VS-S10]` `[VS-S11]` = `developer.broadcom.com/xapis/vsphere-automation-api/**latest**/` (= 9.1). The 9.0-pinned source `[FA-S37]` (`/9.0/api-security-schema/`) gives only the *header*, not the path. `foundation-auth-identity.md` gap 1 says the path is contested **between two 9.1 sources** and must be "resolved before writing client code"; the 9.1 file (`9.1/auth-and-identity.md:274-278`) carries that caveat prominently — the 9.0 file suppresses it entirely | **major** |
| 2 | `vcf-foundation/references/deltas.md:87` | vCenter session path row: 9.0 column = "`POST\|GET\|DELETE /api/cis/session`", 9.1 column = "**Ambiguous**" | presents a real 9.0→9.1 delta | **no delta exists** — the ambiguity is entirely between two *9.1* sources | Same as #1. This manufactures a false delta: it implies 9.0 was unambiguous and 9.1 became ambiguous. Both conflicting sources (`[FA-S35]`, `[FA-S38]`) are 9.1 pages; the 9.0 path was never independently sourced | **major** |
| 3 | `vcf-foundation/SKILL.md:106` | "The reference files carry the documented trust-import mechanisms per product, including **the constraint that VCF Operations trust import is PEM-only**, and the 9.1 change that puts the identity broker under certificate management" | **unversioned** (second clause is version-tagged, first is not) | **9.1 only** | `9.0/auth-and-identity.md:517-518` states verbatim: *"PEM-only CA import … is documented on the **9.1** page `[FA-S57]`; the equivalent 9.0 statement was not retrieved. **Do not assert PEM-only for 9.0.**"* The SKILL.md body asserts exactly what its own 9.0 reference forbids | **major** |
| 4 | `vcf-api-discovery/SKILL.md:46-49` and `references/spec-corpus.md:135` | "**six** products have no spec at the 9.0 tag — all three NSX specs, fleet-lcm, sddc-lcm, realtime-metrics and log-management" / "**Six** product keys are absent from the 9.0.0.0 tag" (table then lists 7 rows) | six | **seven** | `research/spec-inventory/SUMMARY.md`: `9.0 present: no` for `log-management`, `realtime-metrics`, `fleet-lcm`, `sddc-lcm`, `nsx-policy`, `nsx-manager`, `nsx-global-policy` = 7. Both the enumerations in the skill list seven items while stating six. This is the load-bearing evidence-asymmetry fact of the whole skill | **major** |
| 5 | `vcf-foundation/references/9.1/auth-and-identity.md:296-317`, `references/deltas.md:27` (T9), `:94`, `9.1/auth-and-identity.md:465` | "NSX 9.1 auth prose could not be retrieved … The session-cookie flow … is **verified for 9.0 only**. **Do not assert it is unchanged in 9.1.**" and "NSX session timeout: `UNVERIFIED` for 9.1 (1800 s is a **9.0** figure)" | 9.1 = unverified | **9.1 IS verified** (spec + 9.1-pinned prose) | (a) `9.1__nsx-manager.ops.json`, `9.1__nsx-policy.ops.json` and `9.1__nsx-global-policy.ops.json` all contain `POST /api/session/create` (`CreateAuthenticatedSession`) and `POST /api/session/destroy` — verified by direct query. (b) `research/nsx.md` §NSX-9.1-2 sources the full 9.1 flow to **S12** = the 9.1-pinned child page `.../9-1/advanced-network-management/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html` and **S18** = the NSX 9.1.0 API Guide, incl. the 1800 s timeout and the 403-on-expiry sentence. (c) The sibling skill `nsx-security-policy/references/9.1/dfw.md` marks the same flow `[SPEC]`. Two skills give opposite answers to the same question | **major** |
| 6 | `nsx-security-policy/SKILL.md:70-71` | "**Session expiry surfaces as HTTP 403, not 401.**" — stated with no version tag, as a general NSX fact | unversioned | **9.1-doc-verified; NOT 9.0-doc-verified** | `9.0/dfw.md:248-251` states explicitly: *"the verbatim sentence … was read on the **9.1**-pinned admin-guide page. The 9.0-pinned page … **does not** contain that sentence. So for 9.0 this is `[9.1-ONLY — NOT VERIFIED FOR 9.0]`"*. `deltas.md:126` agrees ("not stated on the 9.0-pinned page"). The body asserts unversioned what the version file marks 9.1-only | **major** |
| 7 | `nsx-security-policy/SKILL.md:72-73` | "**The session cookie is bound to a single manager node.**" — no version tag | unversioned | **9.0-doc-only** | `deltas.md:127`: "*not restated on a 9.1-pinned page; assumed unchanged*, `[DOC — 9.0 page only]`". `9.1/dfw.md:219-220` correctly says the verbatim statement was read on the 9.0 page and flags that `nsx.md` over-tags it `[9.0+9.1]`. Same defect class as #6, opposite direction | **minor** |
| 8 | `vcf-api-discovery/references/live-discovery.md:44-47` | "expired session surfaces as **403**, not 401; session cookies are pinned to one manager node" — presented under a section headed "Verified in both the 9.0 and 9.1 NSX API guides" | implies both | 403 = 9.1-only; node-pinning = 9.0-only | Same evidence as #6/#7. The section heading legitimately covers only the *spec-endpoint list*; the runtime notes inherit "verified in both" by adjacency | **minor** |
| 9 | `nsx-security-policy/references/lookup.md:243-254` | §E is headed "`[9.0+9.1]` unless noted"; the `_revision` bullet ("Omit `_revision` on a `PUT` that creates a `/policy` resource") carries no note; the session-affinity bullet likewise | 9.0+9.1 | `_revision` rule = **9.1-verbatim only**; session affinity = **9.0-only** | `9.0/dfw.md:150-152` marks the `_revision` create/update rule `[INFERRED]` for 9.0 ("the 9.0 guide only says `/policy` URIs 'have slightly different behavior'"); `deltas.md:138` calls it "a documentation-precision delta". The 403 bullet in the same list *is* correctly caveated — the inconsistency is within one list | **minor** |
| 10 | `vcf-api-discovery/references/spec-corpus.md:95-106` + `scripts/find_operation.py:71-74` + `nsx-security-policy/references/lookup.md:142-144,162,177` | "A machine-extracted operation inventory **ships with this skill**" at `references/spec-inventory/`; lookup.md hardcodes `/home/claude/vcf-skills/research/spec-inventory/…` and `/tmp/vcf-api-specs/…` | n/a (packaging) | n/a | `skills/vcf-api-discovery/references/` contains only empty `9.0/` and `9.1/` dirs — **no `spec-inventory/`**. The script's 3rd fallback is `../../../research/spec-inventory`, i.e. outside the skill tree. The `--version`-mandatory search is the skill's stated anti-contamination mechanism; as packaged it cannot run, and `DELTA-9.0-to-9.1.md` (which §6 tells the agent to cross-check) is unreachable | **major** |
| 11 | `vcf-api-discovery/SKILL.md:3` (description) | "across roughly **13,000 operations** in vSphere, NSX, SDDC Manager, VCF Operations, **VCF Automation**, vSAN, fleet lifecycle and **VKS**" | n/a | 11,590 (9.1) / 5,083 (9.0); **no VCF Automation or VKS spec exists at either tag** | `SUMMARY.md` lists 15 product keys across both tags; neither VCF Automation nor VKS is among them. `spec-corpus.md` §4 enumerates only products absent *at 9.0* — it never names the class "absent in **both** versions", so a corpus miss on VCF Automation/VKS has no documented interpretation rule | **minor** |
| 12 | `vcf-lifecycle-upgrade/references/deltas.md:37` | "NSX Edge cluster upgrade position — **9.0: Edge clusters upgraded earlier within the domain upgrade**" | asserted as a 9.0 fact | **inferred from the 9.1 statement**; no 9.0 source | The Source column cites only 9.1 refs (D9.1 §3.5, §3.3, delta #10). No 9.0 page stating the earlier position was retrieved; `9.0/lifecycle.md` never states it. `SKILL.md:90` hedges correctly ("a reordering from prior behavior"); the delta table does not | **minor** |
| 13 | `vcf-lifecycle-upgrade/SKILL.md:69-71` | "**OAuth clients are not migrated** by the vIDM to identity-broker migration. They must be manually regenerated." — listed among generic Step-2 prerequisites, no version tag | unversioned | **9.1-only workflow** | `foundation-auth-identity.md` §1.4 / `[FA-S25]`: the vIDM → identity-broker migration page exists only in the 9.1 doc set; `9.1/lifecycle.md` P6 correctly labels it `[9.1 only]`. The body sentence "Any 9.0-era OAuth client breaks on upgrade" implies the context but does not state it | **minor** |
| 14 | `vcf-foundation/references/powercli-session.md` §4.1, §4.2, §7 | `Connect-VIServer -Force`, `Connect-VcfSddcManagerServer -IgnoreInvalidCertificate`, and the `InvalidCertificateAction` value table are stated with no `{PCLI 9.0.0}` / `{PCLI 9.1.0}` / `{both}` tag | untagged | sources are **unpinned `/powercli/latest/`** pages (= 9.1 module) | The file's own preamble (line 3-5) mandates a module-version tag on every fact; `[TL-S19]`, `[TL-S20]`, `[TL-S21]` are all `latest` URLs. §4.3 is correctly tagged `{both}` — §4.1/4.2/7 are not. Whether these parameter sets hold in `{PCLI 9.0.0}` is unevidenced | **minor** |
| 15 | `vcf-foundation/references/9.0/auth-and-identity.md:70-73` (P4b) | The vSphere three-step federated flow (JWT → SAML → session id) and "VMware discourages Basic" are stated inside a 9.0-scoped prerequisite | implied 9.0 | cited `[VS-S9]` = a **9.1**-pinned techdocs URL | The Source Index (line 721) notes "*the auth-mechanisms page is common to both doc sets; the 9.1 copy was the one fetched*" — but that caveat is 500 lines away from the claim and absent inline, unlike every other cross-version carry in the file | **minor** |
| 16 | `nsx-security-policy/references/9.1/dfw.md:148` | `[SPEC — CreateAuthenticatedSession, 9.1__nsx-manager.ops.json **and** 9.1__nsx-global-policy.ops.json]` | citation | also present in `9.1__nsx-policy.ops.json` | Direct query of all three inventories: `POST /api/session/create` appears in nsx-policy, nsx-manager and nsx-global-policy. Under-cited, not wrong | **minor** |
| 17 | `vcf-foundation/references/deltas.md:89`; no other file | "vCenter operation count (Automation) 1275 → **1367 (+101, −9)**" — the −9 is never explained anywhere in the four skills | n/a | the 9 removals are the entire **`/hvc/*` Hybrid Linked Mode** family | `DELTA-9.0-to-9.1.md` § `vsphere-automation` → "Removed in 9.1": `GET\|POST\|DELETE /hvc/links[/{link}]`, `/hvc/links/{link}?action=delete`, `GET\|PUT /hvc/management/administrators`, `?action=add`, `?action=remove` (9 ops). `grep -ri "hvc\|hybrid linked"` across `skills/` returns **zero hits**. These are the only operation-level *removals* in the whole 9.0→9.1 diff outside NSX, and they silently break any HLM automation on upgrade. Compounded by finding #10: the file that documents them is not reachable from the shipped skill | **minor** (would be major if the skills claimed vCenter-feature coverage) |

---

## Deltas explicitly confirmed as correctly handled

| Delta | Where handled | Verdict |
|---|---|---|
| `vcf-operations-for-logs` (9.0, 136 ops, `/api/v2`, `Bearer`, `POST /sessions`) replaced by `log-management` (9.1, 23 ops, `http://localhost:8787`, `X-JWT-Token` via `token/exchange` + `{"serviceKeys":["ops-li"]}`) | `vcf-foundation/references/deltas.md` T8; `9.0/auth-and-identity.md` §1.7; `9.1/auth-and-identity.md` §1.7 + conflict #6; `spec-corpus.md` §4; `vcf-lifecycle-upgrade/references/deltas.md:41` and `9.1/lifecycle.md` discrepancy #5 | **Correct and thorough** — base path, auth header, op-count reduction and the 9.1-only dependency all stated |
| 22 newly-deprecated operations in `vcf-operations-for-networks` | `vcf-foundation/references/deltas.md:97` and `9.1/auth-and-identity.md:362` ("636 (632 at 9.0; 5 added, 1 removed, 22 newly deprecated)") | **Correct** — matches `DELTA-9.0-to-9.1.md` exactly (the 22 are the AWS / Azure / NSX-ALB data-source families + `GET /settings/licensing/`) |
| 9 `/hvc/*` Hybrid Linked Mode removals | nowhere | **Not handled** — see finding #17 |
| SDDC Manager 375 → 423, 0 removed, 21 newly deprecated | `vcf-lifecycle-upgrade/SKILL.md:35`, `9.1/lifecycle.md:67,485-490`, `references/deltas.md:32`, `vcf-foundation/references/deltas.md:78`, `9.1/auth-and-identity.md:252` | **Correct** — verified against both `.ops.json` files; the named deprecated families match the machine diff exactly, including the upgrade-precheck pair that Broadcom's prose omits |
| NSX has no spec at `9.0.0.0`; a 9.1 `[SPEC]` hit is not 9.0 evidence | `nsx-security-policy/SKILL.md` §"evidence asymmetry", `9.0/dfw.md` READ-THIS-FIRST + 12-item unverified summary, `9.1/dfw.md` version-asymmetry warning, `references/deltas.md` `[ASYMMETRIC]` tag, `lookup.md` §C | **Exemplary.** The single best-executed part of the skill set |

---

## Adjudication: the NSX 9.1 auth conflict

**`research/nsx.md` is right; `research/foundation-auth-identity.md` is wrong (or rather, narrowly and
staleley scoped), and the skills built on the latter carry the error.**

The two dossiers did not fetch the same URL. `foundation-auth-identity.md` recorded a repeated HTTP 429
on exactly one page — the **parent index** `.../9-1/advanced-network-management/authentication-and-authorization.html`
— and generalised that single transport failure into "NSX 9.1 auth not verified … Do not assume
`j_username`/`j_password` + `x-xsrf-token` is unchanged in 9.1" (its Gaps item 3).

`nsx.md` fetched the **child** page, `.../9-1/advanced-network-management/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html`
(its **S12**), successfully, and quotes 9.1-specific content that does *not* appear in its 9.0
extraction — the verbatim 403-on-expiry sentence and the "session cookie is immediately eliminated
from the reverse-proxy" logout sentence. It independently corroborates from **S18**, the NSX 9.1.0 API
Guide mirror (`dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html`), which
self-identifies its version. Two independent 9.1-pinned sources.

Machine evidence settles it beyond the prose: `POST /api/session/create` (`CreateAuthenticatedSession`)
and `POST /api/session/destroy` (`DestroyAuthenticatedSession`) are present in **all three** 9.1 NSX
inventories — verified by direct query of `9.1__nsx-policy.ops.json`, `9.1__nsx-manager.ops.json` and
`9.1__nsx-global-policy.ops.json`. The 9.1 spec also declares `ApiServiceConfig.session_timeout`
`default: 1800` and `cookie_based_authentication_enabled` `default: true` (used, correctly, by
`nsx-security-policy/references/9.1/dfw.md`). So the claim that the 1800 s timeout is "a 9.0 figure,
UNVERIFIED for 9.1" (`9.1/auth-and-identity.md:465`) is refuted by the repo's own inventory.

The skill set's own evidence rules point the same way: `vcf-api-discovery/references/doc-portal.md` §5
says of 429 — *"**Back off. Do not conclude the page is missing.**"* — and `spec-corpus.md` says a miss
in a *present* product is evidence of absence while a transport failure is not evidence at all. A 429
is no evidence; `vcf-foundation` converted it into a positive prohibition.

**Resolution and recommended wording.** `nsx-security-policy/SKILL.md`'s unversioned auth block is
**substantively correct for both versions** and should stay — but it should say so explicitly rather
than by omission, and should split out the one sub-fact that genuinely differs:

> Session auth is `POST /api/session/create` with form fields `j_username` / `j_password`; both the
> `JSESSIONID` cookie **and** the `X-XSRF-TOKEN` header must be sent on every subsequent call.
> **[9.0+9.1 — verified independently in both doc sets and, for 9.1, in the published NSX specs.]**
> Two behaviors worth knowing:
> - **Session expiry surfaces as HTTP 403, not 401.** **[9.1 doc-verbatim; not stated on the 9.0 page —
>   treat 403 as a re-auth trigger in both, and say which you are relying on.]**
> - **The session cookie is bound to a single manager node.** **[9.0 doc-verbatim; not restated in the
>   9.1 doc set.]**

And the three `vcf-foundation` locations (`9.1/auth-and-identity.md` §1.5 and §2 NSX row,
`references/deltas.md` T9 and row "NSX session-cookie flow") must be corrected from "UNVERIFIED for
9.1 / do not assert" to "spec-confirmed for 9.1 (`CreateAuthenticatedSession` /
`DestroyAuthenticatedSession` in all three 9.1 NSX specs) and prose-confirmed on the 9.1-pinned
session-cookie page; only the **13 non-Enterprise-Admin/Auditor role names** remain unverified for
9.1, which is what the 429 actually cost." As written, `vcf-foundation` will tell a user the opposite
of what `nsx-security-policy` tells them about the same call.

---

## Overall verdict

**Version separation holds structurally and fails at the margins.**

The architecture works: version-scoped facts live in `references/9.0/` and `references/9.1/`, every
one of ~65 spec-graded endpoint claims I machine-verified is correct, `nsx-security-policy`'s
evidence-grade tagging for 9.0 is the strongest single artifact in the set, and the highest-risk
delta (`vcf-operations-for-logs` → `log-management`) is handled in four places consistently. There is
**no** case of a 9.1-spec-confirmed item being presented as verified for 9.0 — hunt item #4 came back
clean.

The failures are concentrated in three places: (a) `vcf-foundation`'s 9.0 file inheriting
vCenter-session facts from unpinned "latest" (= 9.1) portal pages while dropping the ambiguity caveat
its 9.1 sibling carries (#1, #2); (b) three SKILL.md bodies carrying unversioned fact-bearing claims
that their own version files mark version-specific — PEM-only, 403-not-401, node-bound cookie (#3, #6,
#7); and (c) a stale "unverified" verdict on NSX 9.1 auth that is contradicted by the repo's own spec
inventory and puts two skills in direct conflict (#5). Add one arithmetic error in the corpus'
load-bearing asymmetry fact (six vs seven, #4) and one packaging break that disables the
version-scoped search script the design depends on (#10).

None of these is a fabricated endpoint. All are fixable by editing text in place.
