# VCF 9.0 / 9.1 agent skills

19 agent skills covering VMware Cloud Foundation 9.0 and 9.1 — NSX, VCF Automation,
VCF Operations, vSAN, SDDC Manager, vCenter, vSphere, VKS and PowerCLI.

Ready to use for **Windsurf, Claude, Codex, Triggerfish and OpenClaw**.

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

Each zip contains the 19 skill folders, ready to drop into place.

---

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

Confirm all 19 landed:

```bash
ls <where-you-installed> | wc -l          # 19
```

---

## Use

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

## Licence

MIT-0.
