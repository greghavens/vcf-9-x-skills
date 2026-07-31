# VCF 9.0 / 9.1 agent skills

19 installable agent skills covering VMware Cloud Foundation 9.0 and 9.1 — NSX, VCF
Automation, VCF Operations, vSAN, SDDC Manager, vCenter, vSphere, VKS and PowerCLI.

Authored once in the open [agentskills.io](https://agentskills.io) `SKILL.md` format and
packaged for Claude, OpenAI Codex, Windsurf, Triggerfish and OpenClaw/ClawHub.

> **Built from documentation, not from a live environment.** Every endpoint traces to
> Broadcom documentation or to a published OpenAPI specification, captured 2026-07-31.
> Nothing here has been executed against a running VCF deployment. Verify destructive
> operations before running them.

## Install

```bash
python3 package.py          # writes dist/ for all five targets
```

Then copy the tree for your target — see [`docs/INSTALL.md`](docs/INSTALL.md).

| Target | Path |
|---|---|
| Windsurf | `.windsurf/skills/` (also reads `.agents/skills/` and `.claude/skills/`) |
| Claude | `~/.claude/skills/`, or the generated `.skill` packages |
| Codex | `.agents/skills/` |
| Triggerfish | `~/.triggerfish/workspace/<agent-id>/skills/` |
| OpenClaw / ClawHub | `~/.agents/skills/`, or `clawhub sync --all` |

Claude, Codex and Windsurf take the source unchanged. Triggerfish and OpenClaw need
small additive/subtractive frontmatter transforms, which `package.py` applies —
see the header of that file for why each is needed.

## Repository layout

```
skills/          19 skills — the canonical source. Edit here, never in dist/.
research/        Research dossiers, consolidated source inventory (301 URLs),
                 and the extracted OpenAPI operation corpus + extraction tools.
review/          Adversarial review reports and the verification scripts.
workspace/       Eval definitions, grading, and benchmark results.
docs/            Design proposal, install guide, 9.0→9.1 API delta.
package.py       Multi-target packaging.
```

## How version separation works

VCF 9.0 and 9.1 are materially different platforms that share most of their vocabulary,
which is the trap: an auth flow or prerequisite correct for one is often absent or
renamed in the other, and the failure is silent.

Every skill resolves the target version first, then reads only `references/9.0/` or
`references/9.1/`. `SKILL.md` bodies carry workflow and routing; version-specific facts
live in the version-scoped reference files, so they cannot mix in transit.

The mechanism that makes this mechanical rather than a matter of discipline:
[`github.com/vmware/vcf-api-specs`](https://github.com/vmware/vcf-api-specs) carries git
tags `9.0.0.0` and `9.1.0.0`. Both were extracted and diffed
(`research/tools/extract_specs.py`, `diff_specs.py`), giving a per-version inventory of
~13,000 operations that every endpoint claim was checked against.

`skills/vcf-api-discovery` bundles that inventory and a search script, so an agent can
confirm an operation exists for a specific version instead of guessing one.

## Three documented things these skills correct

- **"VCF Fleet Manager" does not exist.** The 9.0 standalone fleet-management appliance
  was replaced in 9.1 by two services: *fleet lifecycle* and *SDDC lifecycle*.
- **SDDC Manager was not removed in 9.1.** Only its UI is deprecated; its API grew from
  375 to 423 operations with none removed.
- **NSX has no published spec at the 9.0 tag**, so NSX 9.0 endpoints rest on prose
  documentation while 9.1 is spec-confirmable. The skills state which grade of evidence
  an answer rests on.

## Verification

- **Source traceability** — 301 unique documentation URLs
  (`research/SOURCE-INVENTORY.md`), plus the machine-readable spec corpus. No endpoint,
  cmdlet or parameter was written without a citation.
- **Evals** — 12 test cases, 69 assertions, written *before* the skills were drafted.
  Pilot run: **98% with skill vs 73% baseline**. Results in `workspace/`.
- **Adversarial review** — independent agents hunting hallucinated endpoints, wrong API
  versions, 9.0/9.1 bleed and missing prerequisites. ~7,000 machine checks across the
  final 15 skills; reports in `review/`.
- **Honest gaps** — unverifiable items are marked UNVERIFIED in place rather than
  omitted or filled in. The ports/protocols matrix, VCF Automation leaf endpoints and
  VCF Installer auth are the notable ones.

## Regenerating the spec corpus

```bash
git clone https://github.com/vmware/vcf-api-specs /tmp/vcf-api-specs
cd /tmp/vcf-api-specs && git fetch --depth 1 origin tag 9.0.0.0
git worktree add /tmp/vcf-specs-90 9.0.0.0
cd - && python3 research/tools/extract_specs.py && python3 research/tools/diff_specs.py
```

## Licence

MIT-0. The OpenClaw/ClawHub package drops the per-skill `license` field, which that
registry rejects.
