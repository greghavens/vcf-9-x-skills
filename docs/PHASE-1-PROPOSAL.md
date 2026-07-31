# Phase 1 deliverable — VCF 9.0 / 9.1 agent skills

**Research date: 2026-07-31. Nothing below is written from model memory.**
301 unique source URLs across 10 research dossiers, plus a machine-readable OpenAPI
corpus extracted from git tags `9.0.0.0` and `9.1.0.0` of
`https://github.com/vmware/vcf-api-specs`.

Awaiting your sign-off before Phase 2.

---

## 0. Answers to the two questions you asked up front

### Triggerfish — CONFIRMED REAL, and it consumes `SKILL.md`

trigger.fish is a real multi-channel AI agent product. Verified three independent
ways (marketing site, repo README, and the shipped runtime loader source):
skills are folders containing a `SKILL.md`, installed to
`~/.triggerfish/workspace/<agent-id>/skills/<name>/`.

Three things to plan around:

- **Its docs contradict its code.** The docs nest `classification_ceiling`,
  `requires_tools` and `network_domains` under `metadata.triggerfish.*`; the loader
  and all ten bundled skills read them **top-level**. Nested keys are silently
  ignored and default to `PUBLIC` — a security-relevant failure. We emit top-level.
- **Its loader skips symlinked directories.** A symlink-farm install works for
  Claude/Codex/Windsurf but not here — we copy real directories.
- Its "Reef" marketplace is still *coming soon*, so install is manual today.
  Triggerfish is not on the agentskills.io showcase and never claims conformance —
  the format is convergent and compatible, not certified.

### OpenClaw / ClawHub — also real, also live, also `SKILL.md`

You added this mid-flight and it's a clean fit. OpenClaw (MIT, OpenClaw Foundation,
`github.com/openclaw/openclaw`, renamed twice from Clawdbot → Moltbot → OpenClaw)
states verbatim that it "follows the AgentSkills spec". Its marketplace **ClawHub**
(`clawhub.ai`) is fully live: CLI publish, vector search, versioning, automated
security audits. It reads `~/.agents/skills` and `<workspace>/.agents/skills`, which
means **the same layout we build for Codex already loads in OpenClaw**.

Additive requirements specific to ClawHub publishing, all of which I've folded into
the Phase 3 packaging plan:

- No manifest file — frontmatter *is* the manifest.
- Every env var and binary a skill touches must be declared under
  `metadata.openclaw.requires.env|bins`. The audit flags "metadata mismatch" when
  code references an undeclared var — this is the most likely publish blocker for
  us, since our skills reference things like `VCF_SDDC_MANAGER_FQDN`.
- MIT-0 required; any per-skill `license` block must be **deleted**, not overridden.
- Symlinks dereferenced, ≤50 MB bundle, slug `^[a-z0-9][a-z0-9-]*$`.
- Publish via `clawhub skill publish` / `clawhub sync --all`, not a PR.

### The happy consequence: one folder, five targets

| Target | Install path | Transformation needed |
|---|---|---|
| Claude | `~/.claude/skills/<n>/`, `.claude/skills/<n>/`, plugin | none |
| Codex | `.agents/skills/`, `~/.agents/skills/`, `/etc/codex/skills` | path only |
| Windsurf | `.windsurf/skills/` — **also reads `.agents/` and `.claude/`** | usually none |
| Triggerfish | `~/.triggerfish/workspace/<id>/skills/` | +1–4 top-level keys |
| OpenClaw / ClawHub | `~/.agents/skills`, `~/.openclaw/skills` | +`metadata.openclaw.requires`, license strip |

There is a genuine cross-vendor open spec (**agentskills.io**, originated at
Anthropic, developed openly). We author to it. Required fields `name` (≤64,
lowercase-hyphen, must match dir) and `description` (≤1024); optional `license`,
`compatibility`, `metadata`, `allowed-tools`.

One caveat worth flagging: the ecosystem researcher found no *public* documentation
of a `.skill` package format. It does exist in this toolchain (`package_skill.py`
produces one, and Cowork renders a **Save skill** button for it) — so we'll ship
`.skill` for Claude *and* plain directories for everyone else.

---

## 1. Three corrections to the brief's premises

These came out of research and change what we build. Worth agreeing on before Phase 2.

### 1.1 "VCF Fleet Manager" does not exist as a product name in 9.1

No 9.1 page names such a component. What actually happened:

- **9.0** shipped a standalone appliance, *VMware Cloud Foundation Operations fleet
  management 9.0.0.0 (build 24695816)*, as its own BOM row.
- **9.1** eliminates it. Verbatim: *"the standalone VCF Operations Fleet Management
  Appliance no longer exists and is replaced by fleet lifecycle."* KB 440630:
  *"replaced with two new services — Fleet Lifecycle and SDDC Lifecycle — which run
  natively within VCF Management Services."*

Machine-confirmed: the 9.1 spec tag adds `fleet-lcm-openapi.yaml` (51 ops, base
`/fleet-lcm`) and `sddc-lcm-openapi.yaml` (26 ops, base `/sddc-lcm`) — **neither
exists at tag 9.0.0.0.**

So the skills will say *fleet lifecycle* and *SDDC lifecycle*, never "Fleet Manager".

### 1.2 SDDC Manager is NOT gone in 9.1 — only its UI is deprecated

This is the highest-risk fact in the project and the easiest one to over-claim.

- SDDC Manager is in the 9.1 BOM (merged row: *VCF Installer/SDDC Manager 9.1.0.0 /
  25371088*), still owns workload-domain deployment, vCenter import, vSAN stretched
  clusters, and ESX/vCenter/HCX/NSX LCM, and **drives the first half of the 9.0→9.1
  upgrade itself.**
- The deprecation is scoped to the UI: *"The SDDC Manager UI is being deprecated and
  will be removed in a future release."* (In 9.0 the UI was *already* deprecated in
  favour of VCF Operations and the vSphere Client.)
- The **API grew**: machine-counted **375 operations at 9.0 → 423 at 9.1, with zero
  removed.**

An agent that concludes "SDDC Manager is gone, use Fleet Manager" in 9.1 is wrong on
both halves. This becomes an explicit negative assertion in the skills and an
adversarial-review check.

### 1.3 NSX has no machine-readable 9.0 spec in the public corpus

The `9.0.0.0` tag contains **no NSX specs at all**; the `9.1.0.0` tag adds three
(policy 3,729 ops, manager 1,453, global-policy 1,009). So NSX 9.1 gets
spec-grade traceability and **NSX 9.0 gets prose-doc traceability only**, from the
version-pinned `/9.0.0/` doc sets on developer.broadcom.com. The NSX skills will
state this asymmetry rather than paper over it.

---

## 2. The single most valuable research artifact

`github.com/vmware/vcf-api-specs` carries **git tags `9.0.0.0` and `9.1.0.0`**. That
gives us authoritative, version-separated, machine-diffable ground truth for most of
the platform — which converts your traceability rule from a discipline problem into a
mechanical one. I cloned both tags and extracted every operation.

| Product | 9.0 ops | 9.0 base path | 9.1 ops | 9.1 base path |
|---|---|---|---|---|
| sddc-manager | 375 | `/v1` (server stub `localhost:80`) | 423 | same |
| vcf-installer | 52 | stub | 57 | stub |
| vcf-operations | 370 | `/suite-api` | 504 | `/suite-api` |
| vcf-operations-for-logs | 136 | `/api/v2` | — | **spec removed** |
| log-management | — | **absent** | 23 | `:8787` |
| vcf-operations-for-networks | 632 | `/api/ni` | 636 | `/api/ni` |
| realtime-metrics | — | **absent** | 4 | `:8080` |
| fleet-lcm | — | **absent** | 51 | `/fleet-lcm` |
| sddc-lcm | — | **absent** | 26 | `/sddc-lcm` |
| vsphere-automation | 1275 | `https://{host}/api` | 1367 | same |
| vsphere-vi-json | 2195 | `/sdk/vim25/{release}` | 2243 | same |
| vsan-data-protection | 48 | `https://{host}/api` | 65 | same |
| nsx-policy | — | **absent** | 3729 | `/policy/api/v1` |
| nsx-manager | — | **absent** | 1453 | `/api/v1` |
| nsx-global-policy | — | **absent** | 1009 | `/global-manager/api/v1` |

Machine-computed deltas (full list in `research/spec-inventory/DELTA-9.0-to-9.1.md`):

- **`vcf-operations`: +134 operations, 0 removed** — matches the changelog's "134 new,
  0 deprecated, 0 deleted" exactly. Independent corroboration that the extraction is
  sound.
- **`vsphere-automation`: +101, −9.** All nine removals are the `/hvc/*` Hybrid Linked
  Mode tree — an entire capability withdrawn in 9.1. This did not surface in any
  prose research; only the spec diff caught it.
- **`vcf-operations-for-networks`: 22 operations newly deprecated in 9.1** — the AWS,
  Azure and NSX-ALB data-source families, plus `GET /settings/licensing/` superseded
  by `/settings/licensing/v2`.
- `/api/ni` is **confirmed** as the Ops-for-Networks base path (an earlier prose pass
  could not verify it and correctly refused to assume it).

Auth ground truth straight from the specs' `securitySchemes`, per version:

| Product | 9.0 | 9.1 |
|---|---|---|
| vSphere Automation & vSAN DP | basic / `vmware-api-session-id` / federated | identical |
| vSphere VI-JSON | `vmware-api-session-id` | identical |
| VCF Operations | apiKey header `Authorization` | identical |
| Ops for Logs → Log Management | HTTP bearer via `/api/v2/sessions` | **`X-JWT-Token` via `POST /suite-api/api/auth/token/exchange` with `{"serviceKeys":["ops-li"]}`** |
| Ops for Networks | `Authorization: NetworkInsight {token}` | **adds** HTTP bearer (VCF Ops JWT) |
| fleet-lcm | n/a | basic **and** bearer JWT |
| sddc-lcm | n/a | bearer JWT only |
| realtime-metrics | n/a | bearer |
| NSX (all three) | *no 9.0 spec* | HTTP Basic declared in spec |

That last NSX row is a trap I want to call out now: the spec declares only Basic, but
the prose docs document a session flow (`POST /api/session/create` with
`j_username`/`j_password` → `JSESSIONID` cookie **plus** `X-XSRF-TOKEN` header, both
required, expiry surfaces as **403 not 401**, cookie bound to a single manager node).
Spec and prose disagree in emphasis; the skill teaches the session flow and notes
Basic as the spec-declared fallback.

---

## 3. Version architecture — recommendation

**Recommended: shared skill tree, version-scoped reference files, mandatory router
step — with a small number of version-exclusive skills where the product itself only
exists in one version.**

The rule that makes this safe, and that I'd like your explicit buy-in on:

> **No SKILL.md body contains a version-specific fact.** Bodies carry workflow,
> reasoning, and pointers only. Every endpoint, path, cmdlet, payload field and
> prerequisite lives in `references/9.0/*.md` or `references/9.1/*.md`. A fact-bearing
> line in a SKILL.md body is a bug, checkable by grep.

Why not separate trees per version: it would put us at ~36 skills (past your 25
ceiling), double the maintenance surface, and — counterintuitively — *increase* bleed
risk, because the duplicated bodies drift and nobody notices which copy is stale.

Why not naive shared skills: because "mention the version in the text" is exactly how
9.0 facts end up in 9.1 answers.

The hybrid gets the best of both: workflow written once, facts physically
unmixable, and the router makes version determination the agent's first action rather
than an afterthought.

**Router mechanics.** `vcf-foundation` is invoked first by every other skill and must
resolve the target version before any operation is proposed. Order of resolution:
1. The user stated it explicitly.
2. Query the environment (`GET /v1/system` on SDDC Manager; vCenter appliance version;
   BOM query) — the skill bundles a script for this.
3. Ask. Never guess, and never default to "latest" — a wrong default silently
   produces 9.1 answers for a 9.0 estate.

Version-exclusive skills (no 9.0 counterpart exists): `vcf-fleet-sddc-lifecycle-91`.
Version-asymmetric skills carry an explicit "this operation does not exist in 9.x"
section rather than silence.

Layout:

```
vcf-nsx-security-policy/
├── SKILL.md                      # workflow, decision-making, lookup teaching. No facts.
├── references/
│   ├── 9.0/dfw.md                # endpoints, payloads, prereqs — 9.0 only
│   ├── 9.1/dfw.md                # endpoints, payloads, prereqs — 9.1 only
│   └── deltas.md                 # the explicit 9.0→9.1 change list for this domain
└── scripts/
    └── (bundled only where evals show repeated work)
```

---

## 4. Proposed skill list — 18 skills

Ordered as I'd build them. Every skill inherits: version-router-first, the
documentation-not-live-validated caveat, and the destructive-operation warning.

### Foundation (2)

| # | Skill | Scope |
|---|---|---|
| 1 | `vcf-foundation` | **The router + prereqs skill every other skill defers to.** Determine target version (9.0 vs 9.1) before anything else. Per-product auth matrix with exact endpoints, payloads, token fields and headers. Identity: VCF Identity Broker (present in *both*, contrary to a common assumption — what's new in 9.1 is API clients/tokens, built-in VCF roles, and vIDM migration). Certificates and the TLS-trust pitfalls. Roles/permissions. Network reachability. Bundles auth-token helper scripts. |
| 2 | `vcf-api-discovery` | **How to find anything the skills don't cover.** The `vcf-api-specs` repo and its version tags; on-appliance OpenAPI endpoints (`GET /api/v1/spec/openapi/nsx_policy_api.json`, `/suite-api/doc/swagger-ui.html`); version-pinned developer.broadcom.com URL patterns; `Get-Command -Noun`/`Get-Help`; `kubectl api-resources`/`explain`. Bundles a spec-query script so the agent greps 13,000 operations instead of guessing. **This skill is what makes the coverage target reachable.** |

### VCF platform (4)

| # | Skill | Scope |
|---|---|---|
| 3 | `vcf-domains-clusters` | Workload domains, clusters, hosts, network pools via the SDDC Manager API. The validate → execute → poll-Tasks pattern. |
| 4 | `vcf-lifecycle-upgrade` | Bundles, depots, prechecks, upgrade sequencing. **Sharply version-split**: 9.0 runs through SDDC Manager; 9.1 through fleet-lifecycle + SDDC-lifecycle. Carries both upgrade orderings (major-to-9.0 vs 9.0.x maintenance) — conflating them is a realistic failure. |
| 5 | `vcf-installer-bringup` | VCF Installer, management-domain bring-up, convergence. Includes the 9.0 gotcha that Installer and SDDC Manager are the *same OVA*, and that deploying it into the management domain permanently switches it to SDDC Manager mode. |
| 6 | `vcf-certificates-credentials` | Certificate lifecycle and credential/password rotation. 9.1 adds bulk CSR/renew/import and puts the identity broker itself under cert management — a single TLS point of failure for every SSO client. |

### NSX (3)

| # | Skill | Scope |
|---|---|---|
| 7 | `nsx-segments-routing` | Segments, Tier-0/Tier-1 gateways, transport zones, edge clusters. Policy API only — Manager mode/API from NSX 4.x and earlier is explicitly no longer supported. |
| 8 | `nsx-security-policy` | DFW, security policies, rules, drafts, groups (including incremental expression POSTs). |
| 9 | `nsx-network-services` | NAT, load balancing (incl. Avi/ALB), IPSec VPN, IP pools/blocks, VPC. Carries the 9.1 deltas: distributed LB decoupled from DFW, Virtual Network Appliance, dynamic BGP peering, IP Block 1→10 CIDRs, locale-service-scoped VPN paths deprecated. |

### vSphere / vSAN (4)

| # | Skill | Scope |
|---|---|---|
| 10 | `vsphere-inventory-vm-lifecycle` | VM CRUD/clone/power, datacenters/clusters/hosts/datastores/networks. `/api` vs the deprecated `/rest` (which froze at vSphere 7.0.2 — new operations are `/api`-only). |
| 11 | `vsphere-content-tags-policies` | Content library, tags/categories, storage policies and compliance. |
| 12 | `vsphere-lifecycle-vlcm` | vLCM images and remediation; how it meets VCF-level lifecycle. Flags honestly that vLCM REST paths are **unverified** — even the `/api/esx/settings/` vs `/api/esx-settings/` separator is unresolved in the docs, so the skill routes the agent to the spec rather than hard-coding. |
| 13 | `vsan-storage` | vSAN ESA/OSA, policies, health, plus the vSAN Data Protection / snapservice API. 9.1: ESA Auto RAID-6, ESA global dedupe, stretched storage across vCenter instances. |

### VCF Operations (2)

| # | Skill | Scope |
|---|---|---|
| 14 | `vcf-operations-monitoring` | Resources, stats, alerts, alert definitions, reports via `/suite-api`. The 9.1-only trees (`diagnostics`, `salt`, `whatif`, `chargeback`, `optimization`) are marked as such. |
| 15 | `vcf-operations-logs-and-networks` | The big rename: Ops **for Logs** (`/api/v2`, 136 ops, 9.0) → **Log Management** (`:8787`, 23 ops, 9.1, `X-JWT-Token` via token-exchange), plus Ops for Networks (`/api/ni`) and its 22 newly-deprecated operations, plus 9.1 real-time metrics (PromQL). |

### VCF Automation (2)

| # | Skill | Scope |
|---|---|---|
| 16 | `vcf-automation-vmapps` | Blueprints, catalog, deployments, projects — the Aria-derived "VM Apps" org type. Three distinct token flows, all verified. |
| 17 | `vcf-automation-allapps-k8s` | The "All Apps" org type: CRDs under `infrastructure.cci.vmware.com/v1alpha2`, `cci` kubectl context, supervisor namespaces, provider/org admin. |

### Tooling (1 + 1)

| # | Skill | Scope |
|---|---|---|
| 18 | `vks-supervisor` | vSphere Kubernetes Service. **`kubectl vsphere login` appears nowhere in the VCF 9.x docs** — login is `vcf context create --endpoint … --ca-certificate …`. CAPI/CAPV with versioned ClusterClass; `TanzuKubernetesCluster` deprecated since VKS 3.2 and cannot create K8s ≥1.33. |
| 19 | `powercli-vcf` | Module is **`VCF.PowerCLI`, not `VMware.PowerCLI`**. Session cmdlets, the `-IgnoreInvalidCertificate` vs `-Force` inconsistency between `Connect-VcfSddcManagerServer` and `Connect-VIServer`, and noun-first discovery. |

That's **19** — one over the 18 I claimed, because I'd rather show you the split than
silently merge. Two trim candidates if you want a tighter set:

- Merge **#19 `powercli-vcf` into #2 `vcf-api-discovery`** (both are "how to find the
  call you need"). Gets to 18.
- Merge **#6 `vcf-certificates-credentials` into #1 `vcf-foundation`** (certs are
  already a foundation concern). Gets to 17.

I lean toward keeping both separate: PowerCLI is a genuinely different modality, and
cert *rotation* is an operational task rather than a setup prerequisite. Your call.

---

## 5. What I could not verify (and will say so in the skills)

Honest list, so nothing surprises you in Phase 2:

- **NSX 9.0 has no machine-readable spec.** Prose-doc traceability only.
- **VCF Automation leaf pages** — projects, cloud accounts/zones, resource actions, ABX
  paths. Broadcom TechDocs rate-limited hard (HTTP 429, ~90 s back-offs). `/iaas/api/...`
  was never confirmed anywhere and will **not** appear in any skill.
- **vLCM REST paths** — reference pages render JS-only.
- **Ports matrix** — both doc sets defer to the client-rendered ports.broadcom.com.
  Only the outbound-443 allow-list and DNS/FQDN requirements are verified.
- **vCenter session path conflict** — two 9.1 sources say `/api/cis/session` and
  `/session` respectively. The spec supports `/api/cis/session`; the skill will say so
  and note the conflict.
- **VM Apps token field name** is undocumented; the VIDB `grant_type` literal is elided
  as `...` in the source page.
- **PowerCLI 9.1 changelog says "0 deleted commands"** yet `VMware.PowerCLI.VCenter`
  disappeared from the dependency set. Contradiction recorded, not resolved.
- **No on-appliance API-explorer URL pattern is documented for VCF 9.x** (only 7.0/8.0).
  We will not teach one.
- `foundation-auth-identity.md` cites 68 sources in prose but its inventory table
  resolves only 18 URLs — a formatting gap to clean up in Phase 2, not a factual one.

---

## 6. Phase 2 plan, pending your sign-off

Build three skills fully: **`vcf-foundation`**, **`vcf-api-discovery`**, and
**`nsx-security-policy`** (chosen because it exercises version asymmetry — 9.1 spec
vs 9.0 prose — which is the hardest case).

Acceptance criteria written **before** drafting, e.g.:

> *"Create a DFW rule blocking TCP 3389 between two groups in VCF 9.1"* must produce:
> the `/policy/api/v1` base path (not `/api/v1`), the session-create auth flow with
> both `JSESSIONID` and `X-XSRF-TOKEN`, the security-policy-before-rule ordering, a
> stated prerequisite that both groups exist, and an explicit note that this is a
> 9.1 answer.
>
> The same prompt for **9.0** must not cite any spec-derived 9.1 path, and must say
> that 9.0 endpoint verification comes from prose docs.

Then: eval runs with/without skill, graders, the eval viewer for your review, and
**independent** adversarial review agents hunting hallucinated endpoints, wrong API
versions, 9.0/9.1 bleed, and missing prerequisites.

### Decisions I need from you

1. **Version architecture** — approve the shared-tree + version-scoped-references +
   router design, or do you want fully separate 9.0 / 9.1 trees despite the cost?
2. **Skill count** — keep 19, or take one/both of the merges down to 18 or 17?
3. **Pilot trio** — is `nsx-security-policy` the right third pilot, or would you
   rather stress `vcf-lifecycle-upgrade` (the sharpest 9.0/9.1 split in the set)?
4. **Packaging targets** — confirm all five: Claude, Codex, Windsurf, Triggerfish,
   OpenClaw/ClawHub.
