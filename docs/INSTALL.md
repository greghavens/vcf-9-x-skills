# VCF 9.0 / 9.1 agent skills — 19 skills, five install targets

Built 2026-07-31 from live research. Every endpoint traces to Broadcom documentation
or to a published OpenAPI specification. **Nothing has been validated against a live
VCF environment** — verify destructive operations before executing them.

## Install

| Target | Copy from | To |
|---|---|---|
| **Windsurf** | `windsurf/.windsurf/skills/` | your repo's `.windsurf/skills/` |
| Claude | `claude/skills/` | `~/.claude/skills/` or a project `.claude/skills/` |
| Claude (packaged) | `claude/skill-packages/*.skill` | open/import each |
| Codex | `codex/.agents/skills/` | repo root `.agents/skills/` or `~/.agents/skills/` |
| Triggerfish | `triggerfish/skills/` | `~/.triggerfish/workspace/<agent-id>/skills/` |
| OpenClaw / ClawHub | `openclaw/.agents/skills/` | `~/.agents/skills/`, or `clawhub sync --all --root .` |

Windsurf also reads `.agents/skills/` and `.claude/skills/`, so a repo already
carrying either layout needs no second copy. Copy real directories — Triggerfish's
loader skips symlinked ones and ClawHub dereferences at publish.

## What differs per target

Claude, Codex and Windsurf take the source unchanged. Triggerfish adds four
**top-level** keys (`version`, `classification_ceiling`, `requires_tools`,
`network_domains`) — top-level deliberately, because its docs show them nested under
`metadata.triggerfish.*` but its loader reads them top-level and silently falls back
to `PUBLIC` otherwise. OpenClaw strips `license` (ClawHub rejects per-skill
overrides; publishing is MIT-0) and adds `metadata.openclaw.requires`, declaring
binaries as `anyBins` rather than `bins` so a host missing one doesn't render the
skill inert.

## The 19 skills

**Foundation** — `vcf-foundation` (auth, identity, certs, roles, and the version
router everything else defers to), `vcf-api-discovery` (find any of ~13,000
operations without guessing; bundles a search script over the extracted spec corpus).

**VCF platform** — `vcf-domains-clusters`, `vcf-lifecycle-upgrade`,
`vcf-installer-bringup`, `vcf-certificates-credentials`.

**NSX** — `nsx-security-policy`, `nsx-segments-routing`, `nsx-network-services`.

**vSphere / vSAN** — `vsphere-inventory-vm-lifecycle`, `vsphere-content-tags-policies`,
`vsphere-lifecycle-vlcm`, `vsan-storage`.

**VCF Operations** — `vcf-operations-monitoring`, `vcf-operations-logs-and-networks`.

**VCF Automation** — `vcf-automation-vmapps`, `vcf-automation-allapps-k8s`.

**Tooling** — `vks-supervisor`, `powercli-vcf`.

## How version separation works

9.0 and 9.1 are materially different and share most of their vocabulary, which is the
trap. Every skill routes through a version determination first, then reads only
`references/9.0/` or `references/9.1/`. SKILL.md bodies carry workflow and routing;
version-specific facts live in the version-scoped reference files, so they cannot mix.

The mechanism that makes this reliable: `github.com/vmware/vcf-api-specs` carries git
tags `9.0.0.0` and `9.1.0.0`. Both were extracted and diffed, so version claims are
checked mechanically rather than by discipline.

## Three things the docs get wrong that these skills correct

- **"VCF Fleet Manager" does not exist.** The 9.0 fleet-management appliance was
  replaced in 9.1 by two services: fleet lifecycle and SDDC lifecycle.
- **SDDC Manager was not removed in 9.1.** Only its UI is deprecated; its API grew
  from 375 to 423 operations with none removed.
- **NSX has no published spec at the 9.0 tag**, so NSX 9.0 endpoints are prose-grade
  evidence while 9.1 is spec-grade. The skills state which you're acting on.

## Evidence and caveats

Reference files grade every claim and mark unverifiable items UNVERIFIED in place
rather than filling the gap — the ports/protocols matrix, VCF Automation leaf
endpoints, VCF Installer auth, and others. That is deliberate: a checklist that reads
complete but silently omits unverified items is the one that gets signed off.
