# VCF 9.0 / 9.1 agent skills

19 agent skills covering VMware Cloud Foundation 9.0 and 9.1 — NSX, VCF Automation,
VCF Operations, vSAN, SDDC Manager, vCenter, vSphere, VKS and PowerCLI.

They give a coding agent accurate, version-correct VCF knowledge: exact API endpoints,
auth flows, prerequisites, and the 9.0-vs-9.1 differences that are easy to get wrong.

Ready to use for **Windsurf, Claude, Codex, Triggerfish and OpenClaw**. Nothing to
build — download the zip for your tool, unzip, copy into place.

> **Built from documentation, not from a live environment.** Every endpoint traces to
> Broadcom documentation or a published OpenAPI spec, captured 2026-07-31. Nothing has
> been run against a live VCF deployment. Verify destructive operations first.

---

## Download

Grab the one zip for your tool — nothing to build:

| Tool | Download |
|---|---|
| Windsurf | [`vcf-skills-windsurf.zip`](https://github.com/greghavens/vcf-9-x-skills/raw/main/download/vcf-skills-windsurf.zip) |
| Claude | [`vcf-skills-claude.zip`](https://github.com/greghavens/vcf-9-x-skills/raw/main/download/vcf-skills-claude.zip) |
| Codex | [`vcf-skills-codex.zip`](https://github.com/greghavens/vcf-9-x-skills/raw/main/download/vcf-skills-codex.zip) |
| Triggerfish | [`vcf-skills-triggerfish.zip`](https://github.com/greghavens/vcf-9-x-skills/raw/main/download/vcf-skills-triggerfish.zip) |
| OpenClaw | [`vcf-skills-openclaw.zip`](https://github.com/greghavens/vcf-9-x-skills/raw/main/download/vcf-skills-openclaw.zip) |

Each zip contains the 19 skill folders, ready to drop into place. Or clone the repo and
copy the matching top-level folder:

```bash
git clone https://github.com/greghavens/vcf-9-x-skills.git
```

## Install

Unzip, then move the skills where your tool looks for them.

### Windsurf

```bash
unzip vcf-skills-windsurf.zip -d vcf-skills-windsurf

# Project scope — travels with your repo
mkdir -p /path/to/your/repo/.windsurf
cp -R vcf-skills-windsurf /path/to/your/repo/.windsurf/skills

# Or global scope
mkdir -p ~/.codeium/windsurf
cp -R vcf-skills-windsurf ~/.codeium/windsurf/skills
```

Restart Windsurf. Install as **skills**, not rules or workflows — those cap at ~12,000
characters and can't load the reference files these depend on.

### Claude

```bash
unzip vcf-skills-claude.zip -d vcf-skills-claude

# Personal, all projects
mkdir -p ~/.claude
cp -R vcf-skills-claude ~/.claude/skills

# Or one project, shared through your repo
mkdir -p /path/to/your/repo/.claude
cp -R vcf-skills-claude /path/to/your/repo/.claude/skills
```

`claude-skill-packages/` also holds one `.skill` file per skill if you prefer importing
them individually.

Cloud sessions don't read `~/.claude/skills/` — for those, commit the skills into the
repo the session runs against.

### Codex

```bash
unzip vcf-skills-codex.zip -d vcf-skills-codex

# Repository scope
mkdir -p /path/to/your/repo/.agents
cp -R vcf-skills-codex /path/to/your/repo/.agents/skills

# Or user scope
mkdir -p ~/.agents
cp -R vcf-skills-codex ~/.agents/skills
```

### Triggerfish

```bash
unzip vcf-skills-triggerfish.zip -d vcf-skills-triggerfish

ls ~/.triggerfish/workspace/          # find your agent id
cp -R vcf-skills-triggerfish ~/.triggerfish/workspace/<agent-id>/skills
```

**Copy, don't symlink** — the Triggerfish loader skips symlinked directories silently.

### OpenClaw

```bash
unzip vcf-skills-openclaw.zip -d vcf-skills-openclaw

mkdir -p ~/.agents
cp -R vcf-skills-openclaw ~/.agents/skills
```

Publishing to ClawHub:

```bash
npm install -g clawhub
clawhub login
clawhub sync --all --root vcf-skills-openclaw
```

---

## Check it worked

```bash
ls <where-you-installed> | wc -l          # 19
```

Then run the bundled lookup script — it's what `vcf-api-discovery` uses:

```bash
python3 <where-you-installed>/vcf-api-discovery/scripts/find_operation.py \
  --version 9.1 --product fleet-lcm "upgrade"
```

Expect ten operations under `/v1/upgrade-plans`.

---

## Using them

Just ask normally — the skills route themselves.

```
Block RDP between our app-tier and db-tier groups in NSX. We're on 9.1.
What has to be true before we can start the 9.0 to 9.1 upgrade?
Write a bash function that gets an SDDC Manager token on 9.0 and refreshes it.
I can't find the vSAN stretched cluster API anywhere.
```

**Say which version you're on.** 9.0 and 9.1 differ materially. If you don't, the skills
ask or answer for both rather than guessing.

Answers cite their evidence. "Confirmed in the 9.1 spec" and "documented in the 9.0
admin guide, no spec published" are different claims, and you'll be told which you're
acting on.

---

## The 19 skills

| Skill | Covers |
|---|---|
| `vcf-foundation` | Auth, API tokens, SSO, roles, certificates. Determines your version. Others defer here. |
| `vcf-api-discovery` | Finds any of ~13,000 operations without guessing. Bundles a search script. |
| `vcf-domains-clusters` | Workload domains, clusters, hosts, network pools |
| `vcf-lifecycle-upgrade` | Fleet upgrades, patching, prechecks, bundles, depots |
| `vcf-installer-bringup` | Initial deployment, management-domain bring-up, convergence |
| `vcf-certificates-credentials` | Certificate and password rotation |
| `nsx-security-policy` | Distributed firewall, security policies, groups, drafts |
| `nsx-segments-routing` | Segments, Tier-0/Tier-1, transport zones, edge clusters, BGP |
| `nsx-network-services` | NAT, load balancing, VPN, IP pools and IPAM |
| `vsphere-inventory-vm-lifecycle` | VM create/clone/power/delete, inventory traversal |
| `vsphere-content-tags-policies` | Content libraries, tags, storage policies |
| `vsphere-lifecycle-vlcm` | ESX cluster images, depots, remediation |
| `vsan-storage` | ESA/OSA, storage policies, stretched clusters, health, snapshots |
| `vcf-operations-monitoring` | Resources, metrics, alerts, reports |
| `vcf-operations-logs-and-networks` | Log management, Ops for Networks, real-time metrics |
| `vcf-automation-vmapps` | Blueprints, catalog, deployments, projects |
| `vcf-automation-allapps-k8s` | CCI CRDs, supervisor namespaces, provider admin |
| `vks-supervisor` | vSphere Kubernetes Service cluster lifecycle |
| `powercli-vcf` | PowerCLI modules, session setup, cmdlet discovery |

---

## Why version separation is the point

9.0 and 9.1 share most of their vocabulary while differing materially underneath. An
auth flow or prerequisite that is correct for one is often absent or renamed in the
other, and the failure is silent — you get a plausible answer that fails against the
real estate.

Every skill settles the version first, then reads only its `references/9.0/` or
`references/9.1/` files. Skill bodies carry workflow and routing; version-specific facts
live in version-scoped files, so they can't mix.

This is mechanical rather than editorial.
[`vmware/vcf-api-specs`](https://github.com/vmware/vcf-api-specs) carries git tags
`9.0.0.0` and `9.1.0.0`; both were extracted and diffed into a per-version inventory of
~13,000 operations that every endpoint claim was checked against.

### Three things these skills correct

- **"VCF Fleet Manager" doesn't exist.** 9.1 replaced the 9.0 fleet-management appliance
  with two services: *fleet lifecycle* and *SDDC lifecycle*.
- **SDDC Manager wasn't removed in 9.1.** Only its UI is deprecated. Its API grew from
  375 to 423 operations with none removed.
- **NSX has no published spec at the 9.0 tag**, so NSX 9.0 evidence is prose-grade while
  9.1 is spec-grade. The skills say which you're getting.

---

## How it was verified

No live VCF environment was available, so verification is documentary and adversarial:

- **301 documentation URLs** in `research/SOURCE-INVENTORY.md`, plus the machine-readable
  spec corpus. No endpoint, cmdlet or parameter written without a citation.
- **12 evals, 69 assertions**, written before the skills were drafted.
  **98% with skills vs 73% baseline.** Results in `workspace/`.
- **Independent adversarial review** hunting hallucinated endpoints, wrong API versions,
  9.0/9.1 bleed and missing prerequisites — ~7,000 machine checks. Reports in `review/`.
- **Honest gaps.** Unverifiable items are marked UNVERIFIED in place rather than filled
  in. The ports/protocols matrix, VCF Automation leaf endpoints and VCF Installer auth
  are the notable ones.

---

## Troubleshooting

**A skill never triggers.** Agents choose skills from name and description alone. Simple
one-step questions often don't trigger any skill — the agent just answers directly. Test
with substantive questions.

**Not showing up in a Claude cloud session.** `~/.claude/skills/` isn't read there.
Commit the skills into the repo the session runs against.

**Triggerfish skill behaves as `PUBLIC`.** Its `classification_ceiling` got nested under
`metadata:`. It belongs at the top level — Triggerfish's docs show it nested but its
loader reads it top-level and silently falls back to `PUBLIC`.

**ClawHub publish rejected, metadata mismatch.** A file references a binary not declared
in `metadata.openclaw.requires`.

**`find_operation.py` exits 2.** `references/spec-inventory/` didn't come across in the
copy. Re-copy with `cp -R`.

**Answers longer than you want.** Each skill ends with a `## Shaping your answer`
section holding a length-calibration table. Edit it.

---

## Repository layout

The five folders above are what you install. The rest is provenance:

```
download/                                              per-tool zips — start here
windsurf/  claude/  codex/  triggerfish/  openclaw/    the same skills, unzipped
claude-skill-packages/                                 .skill packages for Claude
research/     dossiers, source inventory, extracted spec corpus
review/       adversarial review reports
workspace/    eval definitions, gradings, benchmark results
docs/         design notes, 9.0→9.1 API delta
build/        regenerates the five target folders from skills/
skills/       shared source the five folders are built from
```

Windsurf, Claude and Codex get byte-identical skills. Triggerfish adds four top-level
frontmatter keys; OpenClaw strips `license` (ClawHub rejects per-skill overrides) and
declares required binaries.

---

## Licence

MIT-0.
