# Phase 3 — Hallucinated endpoints & wrong-version claims (adversarial review)

**Target:** the 15 newly built skills under `/home/claude/vcf-skills/skills/`
(the 4 previously reviewed — `vcf-foundation`, `vcf-api-discovery`, `nsx-security-policy`,
`vcf-lifecycle-upgrade` — are out of scope).
**Ground truth:** `/home/claude/vcf-skills/research/spec-inventory/*.ops.json` (22 product×version
inventories, extracted from git tags `9.0.0.0` / `9.1.0.0` of `github.com/vmware/vcf-api-specs`),
plus `/home/claude/vcf-skills/research/*.md` dossiers for the four unspecced products.

---

## 1. Methodology

Everything below is machine-driven. Three scripts live in
`/home/claude/vcf-skills/review/scripts/`:

| Script | What it checks |
|---|---|
| `check2.py` | every `METHOD /path` / backticked path / full URL in every `.md` → does it exist in the ops inventory for **that file's version**, in **any** product? |
| `check_pairs.py` | every `(METHOD-list, path, operationId-list)` triple cited on one line → do the verbs and the operationIds line up with the spec, at the claimed version? |
| `check_dep.py` | every line asserting (or denying) `deprecated` next to a known operationId → does the spec agree, at the claimed version? |

### Normalization rules (these are what stop the check from drowning in false positives)

1. **Base-path stripping.** A claim is compared against the spec both verbatim and with any of
   `/policy/api/v1`, `/global-manager/api/v1`, `/suite-api/api`, `/suite-api`, `/api/ni`,
   `/api/v2`, `/api/v1`, `/rest/api`, `/fleet-lcm`, `/sddc-lcm`, `/api`, `/v1` removed, plus the
   `sdk/vim25/{release}` regex form. Spec paths are indexed under the same set of variants, so
   `/api/vcenter/vm` ≡ `/vcenter/vm` and `/policy/api/v1/infra/segments` ≡ `/infra/segments`.
2. **Query stripping.** `?action=`, `?vmw-task=true`, `&format=csv` etc. are removed from **both**
   sides. Without this, ~180 legitimate vSphere Automation and NSX action-verb paths read as misses.
3. **Structural parameter collapse.** `{anything}`, `<anything>`, `:name`, `$VAR`, `...`, `…` all
   collapse to `*`, so `/v1/domains/{domain-id}` ≡ `/v1/domains/{id}` and a curl example with
   `$CL` substituted matches the templated spec path.
4. **Notation expansion.** `[/{id}]` optional segments and `{json,yaml}` / `tier-{0,1}s`
   alternations are expanded to all concrete candidates.
5. **Multi-verb / multi-id zipping.** The reference files use `GET|POST /path` (`idA` / `idB`) and
   `| GET·PUT·DELETE | /path | idA, idB, idC |`. Verbs and operationIds are split and **zipped
   positionally**; rows that do not zip cleanly are counted as ambiguous and reported separately
   (59 of them) rather than as failures.
6. **Relative-path handling.** Reference tables list paths relative to a section base
   (`/bgp/neighbors` under a Tier-0 locale-service heading, `…/transport-zones/{id}`). For the
   triple check, an operationId matches if its spec path **ends with** the cited path.
7. **Cross-product search.** A claim is a miss only if it resolves in **no** product at that
   version — so vSAN citing SDDC Manager, or a tags skill citing the VI-JSON `/pbm` surface, is
   correctly accepted.
8. **Prefix/suffix suppression.** A bare namespace mention (`/api/esx/settings`, `/suite-api/api`)
   that is a strict prefix of ≥1 real operation is not an endpoint claim and is not counted as a
   miss; it is counted separately.

### Version-context rule

`references/9.0/*.md` → claims are checked against the **9.0** inventories only.
`references/9.1/*.md` → **9.1** only. `SKILL.md` and `references/deltas.md` → either version is
acceptable (they legitimately discuss both).

### Products with no spec — a different property is checked

`vcf-automation-vmapps`, `vcf-automation-allapps-k8s`, `vks-supervisor`, `powercli-vcf` have **no
OpenAPI spec at either tag**. For these the script asserts (a) no claim is graded `[SPEC]` /
"spec-confirmed", and (b) every path traces to a dossier in `/home/claude/vcf-skills/research/`.
NSX likewise has **no spec at the 9.0 tag** — every `[SPEC]`-graded claim in
`nsx-*/references/9.0/` is flagged as a candidate blocker and then read in context.

---

## 2. Volume checked

| Class | Count |
|---|---|
| API path claims (`METHOD /path`, backticked paths, full URLs) | **2,597** |
| Backticked operationId tokens resolved against the inventories | **3,066** |
| `(method, path, operationId)` triples cross-checked | **1,188** (+59 ambiguous, reported not failed) |
| `deprecated` assertions cross-checked | **99** |
| No-spec skills: distinct paths traced to a dossier source ref | **19** (15 + 4; VKS and PowerCLI cite none) |
| Named traps from the brief | **8** |
| Tag-level operation counts recomputed | 13 tags (SDDC Manager topology), plus vSAN `/vsan/` prefix counts at both tags |
| **Total machine checks** | **≈ 6,970** |

## 3. Per-skill summary

`ok` = resolved at the claimed version. `neg` = resolved only at the *other* version **and** the
line explicitly states it as a cross-version / "9.1-only" / "not in 9.0" negative claim (all 84 were
read in context and all 84 are correct). `ns` = namespace/prefix mention, not an endpoint claim.
`FP` = flagged by the script, cleared on reading. `MISS` = surviving defect.

| Skill | Path claims | ok | neg | ns | FP | **MISS** | opIds | Triples | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `vcf-domains-clusters` | 404 | 393 | 6 | 0 | 3 | **2** | 205 | 190 | pass w/ 2 defects |
| `vcf-installer-bringup` | 171 | 168 | 3 | 0 | 0 | 0 | 57 | 52 | **clean** |
| `vcf-certificates-credentials` | 168 | 165 | 2 | 1 | 0 | 0 | 186 | 141 | **clean** |
| `nsx-segments-routing` | 116 | 67 | 0 | 0 | 49 (47 = 9.0 no-spec, correctly graded) | 0 | 569 | 268 | **clean** |
| `nsx-network-services` | 80 | 46 | 0 | 0 | 34 (30 = 9.0 no-spec) | 0 | 395 | 173 | **clean** |
| `vsphere-inventory-vm-lifecycle` | 220 | 169 | 9 | 18 | 24 | 0 | 268 | 96 | **clean** |
| `vsphere-content-tags-policies` | 194 | 138 | 4 | 13 | 39 | 0 | 212 | 108 | **clean** |
| `vsphere-lifecycle-vlcm` | 162 | 136 | 0 | 11 | 15 | 0 | 212 | 84 | **clean** |
| `vsan-storage` | 202 | 175 | 7 | 12 | 8 | **1** (count, in SKILL.md) | 89 | 42 | pass w/ 1 defect |
| `vcf-operations-monitoring` | 475 | 424 | 5 | 35 | 11 | 0 | 603 | 21 | **clean** |
| `vcf-operations-logs-and-networks` | 329 | 295 | 7 | 6 | 21 | 0 | 270 | 13 | **clean** |
| `vcf-automation-vmapps` | 35 | n/a | — | — | — | 0 | — | — | **clean** (0 `[SPEC]`, 15/15 traced) |
| `vcf-automation-allapps-k8s` | 15 | n/a | — | — | — | 0 | — | — | **clean** (0 `[SPEC]`, 4/4 traced) |
| `vks-supervisor` | 0 | n/a | — | — | — | 0 | — | — | **clean** (0 `[SPEC]`) |
| `powercli-vcf` | 26 | n/a | — | — | — | 0 | — | — | **clean** (0 `[SPEC]`, cmdlets only) |

**Zero BLOCKERs.** No hallucinated endpoint survived verification in any skill. The three defects
below are a wrong verb, a wrong compressed-notation verb pair, and a mis-scoped count.

---

## 4. Findings

| # | Skill | File | Line | Claim | Version claimed | Verdict | Evidence | Severity |
|---|---|---|---|---|---|---|---|---|
| 1 | `vcf-domains-clusters` | `references/9.1/domains-clusters.md` | 223 | *"**How to verify:** `GET /v1/domains/{domainId}/clusters/queries` (post a `ClusterCriterion`, then `GET …/queries/{queryId}`)"* | 9.1 | **WRONG METHOD** | `9.1__sddc-manager.ops.json`: the collection is `POST /v1/domains/{domainId}/clusters/queries` (`postClustersQuery`). The only `GET` in this family is `/v1/domains/{domainId}/clusters/queries/{queryId}` (`getClustersQueryResponse`). No `GET` is declared on the collection at **either** tag. The parenthetical in the same sentence says *"post a `ClusterCriterion`"*, so the verb contradicts its own instruction. A caller following it literally gets 405/404 on the P-prerequisite check for "domain without a cluster". | **major** |
| 2 | `vcf-domains-clusters` | `references/9.0/domains-clusters.md` · `references/deltas.md` | 537 · 55 | "`POST\|GET /v1/clusters/{clusterId}/remediations` (`triggerRemediation` / `getRemediationById`)" | 9.1 (as a 9.1-only addition) | **WRONG METHOD on the compressed pair** | `9.1__sddc-manager.ops.json` declares exactly two remediation ops: `POST /v1/clusters/{clusterId}/remediations` (`triggerRemediation`) and `GET /v1/clusters/{clusterId}/remediations/{remediationId}` (`getRemediationById`). There is **no** `GET` on the collection. The `POST\|GET <one-path>` notation used everywhere else in these files means "both verbs, same path", so this reads as a `GET` on the collection that does not exist. Both `vcf-domains-clusters/references/9.1/domains-clusters.md:552-553` and `vsan-storage/references/deltas.md:63` state the same pair **correctly** — this is an inconsistency between siblings, not a shared misunderstanding. | **minor** |
| 3 | `vsan-storage` | `SKILL.md` | 32–33 | "under `/sdk/vim25/{release}/vsan/{ManagedObject}/{moId}/{Operation}` — **301 vSAN operations in 9.0, 317 in 9.1**" | 9.0 + 9.1 | **MISGRADED (count mis-scoped)** | Operations actually **under the `/vsan/` prefix**: **285** at 9.0, **301** at 9.1 (recomputed from `9.{0,1}__vsphere-vi-json.ops.json`). The 301/317 figures are the wider *"vSAN-matching"* totals defined in the reference files — `/vsan/` prefix **plus** ~15 vSAN-named ops outside it **plus** one vSAN-named `/pbm` op (`references/9.0/vsan.md:422-424`, `references/9.1/vsan.md:521-523`, both internally correct). Attaching them to the `/vsan/…` path pattern in SKILL.md silently shifts the 9.0 number one version-step forward: a reader is told 9.0 has 301 ops under `/vsan/` when it has 285, i.e. exactly the 9.1 figure. | **minor** |

### Items that fired in the scanner and were cleared on reading

84 path claims and 31 operationId tokens resolved only at the *other* version. **All 84 + 31 were
read in context and every one is a deliberate, correctly-worded cross-version statement** —
"9.1-only", "not available in 9.0", "there is no SDDC Manager discovery endpoint in 9.0", "removed
at 9.1". The largest of these is `vsphere-inventory-vm-lifecycle/references/9.1/inventory-and-vms.md:963-979`,
which reproduces the nine removed `/hvc/*` operations verbatim under a "**Removed at 9.1 — Hybrid
Linked Mode**" heading; recomputing the 9.0→9.1 set diff for `vsphere-automation` yields **exactly
those nine and nothing else**, so the claim "exactly nine operations were removed and all nine are
`/hvc/*`" is machine-confirmed.

---

## 5. Named traps — all eight verified

| Trap | Verdict | Evidence |
|---|---|---|
| `/iaas/api/` must appear nowhere in the two VCF Automation skills | **CLEAN** | `grep -rn '/iaas/api' skills/` → **zero occurrences repo-wide**. The dossier's "never confirmed" note was respected. |
| `/api/esx-settings/` (hyphen) vs `/api/esx/settings/` (slash) in `vsphere-lifecycle-vlcm` | **CLEAN — and the agent's claim is correct** | Spec: `servers[0].url = https://{host}/api`, paths `/esx/settings/clusters/...` → the resolved form is the **slash** version, `/api/esx/settings/`. `vsphere-lifecycle-vlcm/references/9.0/vlcm.md:18` and `9.1/vlcm.md:19` state *"`/api/esx-settings/...` does **not** exist — zero operations contain the string"*, which is exactly right (0 hits at both tags). All 26 worked-example URLs use the slash form. `vsphere-inventory-vm-lifecycle` carries the same resolution at `9.0:913` / `9.1:1019`. |
| `kubectl vsphere login` in `vks-supervisor` | **CLEAN** | Taught as `vcf context create` (3 mentions in `SKILL.md`, 10 in `9.0/vks.md`, 8 in `9.1/vks.md`). `kubectl vsphere login` appears **only** as an explicit trap warning, and `references/deltas.md:46` leaves removal-vs-undocumented open: *"`[DOC-BOTH]` (absence); removal vs non-documentation `[UNVERIFIED]`"*. Exactly the required treatment. |
| `VMware.PowerCLI` vs `VCF.PowerCLI` | **CLEAN** | `VCF.PowerCLI` used throughout. `VMware.PowerCLI` appears only as the named pre-9.x brand (`module-map.md:60-66`, with the Gallery status of the legacy package correctly marked `[UNVERIFIED]`). `VMware.PowerCLI.VCenter` is a genuinely different, correctly-scoped 9.0-only component module. |
| `-SkipCertificateCheck` vs `-IgnoreInvalidCertificate` | **CLEAN** | `SKILL.md:46-47` gives the right-vs-wrong table: `Connect-VcfSddcManagerServer` → `-IgnoreInvalidCertificate`, `Connect-VIServer` → `-Force`; `-SkipCertificateCheck` appears **only** in the "wrong" column and in `discovery.md:93` as a named failure mode. |
| `/api/cis/session` anywhere | **CLEAN — correctly resolved against it** | Spec: `POST\|GET\|DELETE /session` = `Cis.Session_create/_get/_delete` at **both** tags, base `/api` → **`POST /api/session`**. `vsphere-inventory-vm-lifecycle/SKILL.md:66` leads with *"`POST /api/session`, not `POST /api/cis/session`"*, and both version files carry a "Path conflict … resolved in favour of the spec" block that keeps *whether* the `cis` form also resolves as `UNVERIFIED`. This is the correct fix for the blocker found in the earlier `vcf-foundation` review, applied here. |
| Cross-product citation (vSAN stretched clusters in SDDC Manager, PBM in VI-JSON) | **CLEAN** | All 7 SDDC-Manager paths cited from `vsan-storage` and all 33 `/pbm/*` paths cited from `vsphere-content-tags-policies` resolve in the correct foreign inventory. |
| NSX `[SPEC]` grading at 9.0 (no spec at that tag) | **CLEAN — no blocker** | 26 lines in `nsx-segments-routing/references/9.0/networking.md` and `nsx-network-services/references/9.0/services.md` contain the strings `[SPEC]` / "spec-confirmed"; **every one** is a negative or 9.1-scoped statement (e.g. `networking.md:26-27` *"A path being spec-confirmed for 9.1 is not evidence about 9.0 … Those tags mean nothing here"*; `networking.md:107` `GET /api/v1/aaa/role-bindings` marked *"spec-confirmed for **9.1 only** — [9.1-ONLY — NOT VERIFIED FOR 9.0]"*). **Zero** 9.0 claims are graded `[SPEC]`. |

### Bonus: an incidental `/api/cis-tagging` trap, also clean

`vsphere-content-tags-policies` carries the same class of conflict for tagging. Spec:
`/cis/tagging/category|tag|tag-association` (33 ops at 9.0, 34 at 9.1) — the **slash** form. The
skill resolves in favour of the spec at `9.0:490-506` / `9.1:517-532`, keeps the hyphen form as an
`UNVERIFIED` live-appliance question, and adds a troubleshooting row mapping a 404 back to the
hyphen form. It also correctly asserts three *negatives* that the scanner reconfirmed:
`/vcenter/storage/policies/compliance`, `/vcenter/storage/policies/vm` and
`/vcenter/datastore-default-policy` do **not** exist (real forms are
`/vcenter/storage/policies/entities/compliance`, `/vcenter/storage/policies/{policy}/vm`,
`/vcenter/datastore/{datastore}/default-policy`).

## 6. Counts independently recomputed and matching

- `vcf-domains-clusters/references/9.0/domains-clusters.md:30-33` — "128 operations across the nine
  topology tags (`Domains` 32, `Clusters` 34, `Hosts` 19, `NSX-T Clusters` 16, `Network Pools` 9,
  `NsxTEdgeClusters` 8, `BrownfieldImport` 6, `PSCs` 2, `vCenters` 2), plus 26 supporting
  (`ALBClusters` 15, `vSANHealthCheck` 4, `Tasks` 4, `ConfigReconciler` 3)" — **all 13 tag counts
  and both totals exact.**
- VI-JSON corpus sizes 2,195 / 2,243 and vSAN `/vsan/` prefix 285 / 301 — exact (see finding 3 for
  where the SKILL.md summary mis-scopes them).
- `vcf-operations-for-networks` licensing: `getLicensesV2` genuinely 9.1-only; `getLicenses`
  `deprecated: false` at 9.0 and `true` at 9.1 — both stated correctly.
- `vcf-operations` Salt: `/api/salt` = 0 ops at 9.0, 5 at 9.1 — claim exact.
- `vsphere-automation` 9.0→9.1 removals: exactly 9, all `/hvc/*` — claim exact.

## 7. Scripts

Reproduce with:

```
python3 /home/claude/vcf-skills/review/scripts/check2.py       # path existence + version
python3 /home/claude/vcf-skills/review/scripts/check_pairs.py  # (method, path, operationId) triples
python3 /home/claude/vcf-skills/review/scripts/check_dep.py    # deprecation assertions
```

Raw output: `scripts/out2.json`, `scripts/pairs.json`.
