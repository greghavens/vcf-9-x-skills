# Agent Skill Authoring & Installation Formats — Cross-Ecosystem Research

**Research date: 2026-07-31.** All claims below were verified against a page fetched
during this task. Anything not verified is explicitly marked `UNVERIFIED`.

**Headline finding:** there *is* a cross-vendor open standard — **Agent Skills**
(<https://agentskills.io>) — and **all four targets consume `SKILL.md` folders**, including
Triggerfish. A single canonical skill folder can be packaged for all four with only
additive, per-target frontmatter changes. No target requires a body rewrite.

---

## 0. The Open Standard — Agent Skills (agentskills.io)

Yes, a cross-vendor open spec exists and is the correct authoring baseline.

> "The Agent Skills format was originally developed by [Anthropic], released as an open
> standard, and has been adopted by a growing number of agent products. The standard is
> open to contributions from the broader ecosystem."
> — [S1] agentskills.io/home.md

Governance/discussion: <https://github.com/agentskills/agentskills> and a public Discord.
Reference validator: `skills-ref validate ./my-skill`
(<https://github.com/agentskills/agentskills/tree/main/skills-ref>) [S2].

`UNVERIFIED`: the spec's version number, its content license, and its formal governance
model (BDFL vs. committee) were not stated on any page fetched.

### Canonical directory layout [S2]

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

### Canonical frontmatter field list [S2]

| Field | Required | Constraints |
|---|---|---|
| `name` | **Yes** | 1–64 chars; lowercase `a-z`, `0-9`, `-` only; no leading/trailing hyphen; no consecutive hyphens (`--`); **must match the parent directory name** |
| `description` | **Yes** | 1–1024 chars, non-empty; must say *what* it does AND *when* to use it |
| `license` | No | License name or reference to a bundled license file |
| `compatibility` | No | Max 500 chars; environment requirements (intended product, system packages, network access) |
| `metadata` | No | Map of string keys → string values; for client-specific properties not defined by the spec |
| `allowed-tools` | No | Space-separated string of pre-approved tools. **Experimental** — "Support for this field may vary between agent implementations" |

### Canonical example [S2]

```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---

## Instructions
...
```

### Conformance notes [S2]

- **Progressive disclosure, three stages:** metadata (~100 tokens, `name` + `description`
  loaded at startup for all skills) → instructions (full body on activation, **<5000 tokens
  recommended**) → resources (`scripts/`, `references/`, `assets/` loaded only when needed).
- **Keep `SKILL.md` under 500 lines.** Move detail into referenced files.
- **File references** use relative paths from the skill root, e.g.
  `See [the reference guide](references/REFERENCE.md)`. Keep references **one level deep**;
  avoid deeply nested reference chains.
- Body content has **no format restrictions**.

### Ecosystem breadth [S1]

The published client showcase lists 40+ conforming products, including all four of our
targets plus Cursor, GitHub Copilot, VS Code, Gemini CLI, Goose, OpenCode, OpenHands,
Roo Code, Kiro, Factory, Letta, Amp, Tabnine, Snowflake Cortex Code, Databricks Genie Code,
Mistral Vibe, Junie, and Pulumi Neo. This matters for the packaging decision: writing to
the open spec, not to Claude's dialect, buys ~40 targets for free.

---

## 1. Claude (Claude Code / Claude.ai / Cowork)

Claude Code explicitly declares conformance:

> "Claude Code skills follow the [Agent Skills](https://agentskills.io) open standard, which
> works across multiple AI tools. Claude Code extends the standard with additional features
> like invocation control, subagent execution, and dynamic context injection."
> — [S3] code.claude.com/docs/en/skills

### Install locations

| Level | Path | Scope |
|---|---|---|
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<skill-name>/SKILL.md` | This project only |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Where plugin is enabled |

Source: [S3]. Precedence: **enterprise > personal > project**; any of these overrides a
bundled skill of the same name. Plugin skills are namespaced `plugin-name:skill-name` and
therefore cannot conflict.

Additional Claude Code loading behaviour [S3]:
- Project skills load from `.claude/skills/` in the start directory **and every parent
  directory up to the repo root**.
- **Nested** `.claude/skills/` below the working directory load lazily — the first time
  Claude reads or edits a file in that subdirectory. Until then they are not in autocomplete.
  A nested clash produces a path-qualified command, e.g. `apps/web/.claude/skills/deploy/` →
  `/apps/web:deploy`.
- `--add-dir` / `/add-dir` **do** load `.claude/skills/` from the added directory (an
  explicit exception to the "file access, not configuration" rule). The
  `permissions.additionalDirectories` setting does **not**.
- Skill entries may be **symlinks** to directories elsewhere on disk; the same target
  reachable twice is loaded once.
- **Live change detection**: edits under `~/.claude/skills/`, project `.claude/skills/`, or an
  `--add-dir` directory are picked up mid-session without restart. This covers `SKILL.md`
  **text only** — changes to `hooks/`, `.mcp.json`, `agents/`, `output-styles/` in a
  skills-dir plugin need `/reload-plugins`.
- Custom commands merged into skills: `.claude/commands/deploy.md` and
  `.claude/skills/deploy/SKILL.md` both create `/deploy`. Existing `commands/` files keep
  working; on a name clash the **skill wins**.
- Adding `.claude-plugin/plugin.json` to a skill folder makes it load as a plugin named
  `<name>@skills-dir`, letting it bundle agents, hooks, and MCP servers.

### Cowork and cloud sessions — important packaging constraint [S3]

> "Cowork sessions and cloud sessions, including routines, don't read `~/.claude/skills/` on
> your machine. Both interactive and scheduled Cowork sessions load the skills enabled for
> your claude.ai account, synced at session start; manage them from **Customize** in the
> Desktop app sidebar or from the skills settings on claude.ai. Cloud sessions additionally
> load project skills committed to the cloned repository's `.claude/skills/`."

So a skill that exists only in `~/.claude/skills/` is **reported as not found** when a
routine invokes it. To reach Cowork/cloud you must either enable it on the claude.ai
account, commit it to the repo's `.claude/skills/`, or ship it in a plugin declared in the
repository's `.claude/settings.json` (repo-declared plugins install at session start;
plugins enabled only in user settings do not transfer).

### Claude.ai upload format

Custom skills are uploaded to claude.ai as **zip files** via **Settings > Features**; the API
uses the `/v1/skills` endpoints [S4].

### The `.skill` package format — NOT CONFIRMED

`UNVERIFIED`. No page fetched in this task documents a `.skill` file extension or package
format. [S4] states affirmatively that skills are filesystem directories and that
*"the documentation does not explicitly mention a `.skill` package format"*; claude.ai
distribution is plain **zip**. Distribution mechanisms that *are* documented [S3]:

- **Project skills** — commit `.claude/skills/` to version control
- **Plugins** — create a `skills/` directory inside a plugin, distributed via marketplaces
  (`/plugin marketplace add anthropics/claude-plugins-official`)
- **Managed** — deploy organization-wide through managed settings

Treat `.skill` as non-existent unless a later source proves otherwise.

### Claude Code frontmatter reference [S3]

Claude Code accepts the open-spec fields and adds a large proprietary set. Note the
divergence: in Claude Code **`name` is optional**, and `description` is only "recommended".

| Field | Required | Notes |
|---|---|---|
| `name` | No | Display name in listings; **defaults to the directory name**. In personal/project skills it sets only the display label — the command still comes from the directory name. In a **plugin** skill it sets the last command segment. |
| `description` | Recommended | If omitted, the first paragraph of markdown is used. Combined `description` + `when_to_use` is **truncated at 1,536 characters** in the skill listing. |
| `when_to_use` | No | Extra trigger phrases/example requests; appended to `description`, counts toward the 1,536-char cap. |
| `argument-hint` | No | Autocomplete hint, e.g. `[issue-number]`. |
| `arguments` | No | Named positional args for `$name` substitution. Space-separated string or YAML list. |
| `disable-model-invocation` | No | `true` prevents automatic loading (manual `/name` only). Also blocks preloading into subagents and (v2.1.196+) blocks scheduled-task firing. Default `false`. |
| `user-invocable` | No | `false` hides it from the `/` menu. Default `true`. |
| `allowed-tools` | No | Tools usable without permission prompts during the invoking turn; grant clears on next message. Space/comma string or YAML list. |
| `disallowed-tools` | No | Tools removed from the pool while active. Cannot remove `EndConversation` while any other tool remains. |
| `model` | No | Model override for the rest of the turn; not saved to settings. Accepts `/model` values or `inherit`. |
| `effort` | No | `low`, `medium`, `high`, `xhigh`, `max`. Overrides session effort. |
| `context` | No | `fork` runs the skill in a forked subagent context. |
| `agent` | No | Which subagent type to use when `context: fork`. |
| `background` | No | Only with `context: fork`. `false` waits for the result in-turn. Default `true`. Requires v2.1.218+. |
| `hooks` | No | Hooks scoped to this skill's lifecycle. |
| `paths` | No | Glob patterns limiting activation to matching files. Comma string or YAML list. |
| `shell` | No | `bash` (default) or `powershell` for inline `` !`command` `` blocks. |

Claude Code also offers a `skillOverrides` **setting** (written by the `/skills` menu into
`.claude/settings.local.json`) to control visibility without editing a skill's frontmatter —
useful for skills checked into a shared repo [S3].

### Claude-only string substitutions [S3]

`$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `$name`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`,
`${CLAUDE_SKILL_DIR}`. **`${CLAUDE_SKILL_DIR}` is the portability trap** — it resolves the
skill's own directory and is the documented way to reference bundled scripts regardless of
cwd, but it is Claude-specific and will not expand in Codex, Windsurf, or Triggerfish.

Context note: auto-compaction re-attaches the most recent invocation of each skill after
summarisation, keeping the **first 5,000 tokens** of each, within a **combined 25,000-token
budget** [S3]. Another reason to keep `SKILL.md` short and push detail to `references/`.

### Platform-level (claude.ai / API) constraints [S4]

`name`: max 64 chars, lowercase/numbers/hyphens, no XML tags, and **must not contain the
reserved words "anthropic" or "claude"**. `description`: non-empty, max 1024 chars, no XML
tags. This reserved-word rule is stricter than the open spec and is a real packaging gate.

---

## 2. OpenAI Codex

**Yes — Codex consumes Agent Skills natively.** It is listed as a conforming client on
agentskills.io [S1] and has first-party documentation [S5]. It is *not* limited to
AGENTS.md, and it does not require MCP for this.

### Directory layout [S5]

```
my-skill/
├── SKILL.md              (required)
├── scripts/              (optional)
├── references/           (optional)
├── assets/               (optional)
└── agents/
    └── openai.yaml       (optional: Codex-specific UI/policy metadata)
```

### Search paths and precedence [S5]

Codex searches most-specific → most-general:

| Scope | Path | Use case |
|---|---|---|
| REPO | `$CWD/.agents/skills` | Folder-specific workflows |
| REPO | `$CWD/../.agents/skills` | Nested repository shared skills |
| REPO | `$REPO_ROOT/.agents/skills` | Organization-wide repository skills |
| USER | `$HOME/.agents/skills` | User's personal curated skills |
| ADMIN | `/etc/codex/skills` | System-level defaults |
| SYSTEM | Bundled with Codex | OpenAI-provided built-ins |

**Note the directory is `.agents/skills`, NOT `.claude/skills`.** Duplicate skill names do
**not** merge — both appear in selectors. Codex **follows symlinked skill folders** to their
targets, which makes a single canonical source directory + per-target symlinks a viable
install strategy.

### Frontmatter [S5]

Required: `name`, `description`. Codex guidance is that the description should
*"front-load the key use case and trigger words"* so it still works when abbreviated under
context limits, and should *"explain exactly when this skill should and should not
trigger"*.

`UNVERIFIED`: whether Codex reads `license`, `compatibility`, `metadata`, or `allowed-tools`.
The Codex page documents only `name` and `description` in `SKILL.md`; extra keys are
presumed inert but this was not confirmed.

### Optional `agents/openai.yaml` [S5]

```yaml
interface:
  display_name: "User-facing name"
  short_description: "Alternative description"
  icon_small: "./assets/small-logo.svg"
  icon_large: "./assets/large-logo.png"
  brand_color: "#3B82F6"
  default_prompt: "Surrounding prompt context"

policy:
  allow_implicit_invocation: false

dependencies:
  tools:
    - type: "mcp"
      value: "serverName"
      description: "Tool description"
      transport: "streamable_http"
      url: "https://example.com"
```

`allow_implicit_invocation` defaults to `true` and controls whether Codex auto-selects the
skill; explicit invocation via `$skill` always works.

### Invocation [S5]

- **Explicit**: `/skills`, `$skill-name`, or the skill selector.
- **Implicit**: Codex matches the skill's `description` against user intent.

### Relationship to AGENTS.md

AGENTS.md remains Codex's always-on repo instruction file and is a **separate mechanism**
from skills; skills are the on-demand, progressively-disclosed unit. `UNVERIFIED`: the exact
current AGENTS.md precedence/merge rules were not re-verified in this task — the Codex
skills page does not restate them. Do **not** package our skills as AGENTS.md content;
use `.agents/skills/`.

---

## 3. Windsurf (Codeium)

Windsurf has **three distinct customization mechanisms**. Only the third is Agent Skills.
Conflating rules and skills is the most common mistake here.

### 3a. Skills — the one that matters [S6]

Windsurf Skills **conform to the agentskills.io open standard** [S6, S1].

| Scope | Path |
|---|---|
| Workspace (committed) | `.windsurf/skills/<skill-name>/` |
| Global (not committed) | `~/.codeium/windsurf/skills/<skill-name>/` |
| System, macOS (Enterprise) | `/Library/Application Support/Windsurf/skills/` |
| System, Linux/WSL (Enterprise) | `/etc/windsurf/skills/` |
| System, Windows (Enterprise) | `C:\ProgramData\Windsurf\skills\` |

**Cross-agent compatibility paths — the key packaging win** [S6]: Windsurf also reads
`.agents/skills/`, `~/.agents/skills/`, `.claude/skills/`, and `~/.claude/skills/`.
This means a repo laid out for Claude or Codex is picked up by Windsurf with **zero extra
files**.

Frontmatter — required only:

```yaml
---
name: deploy-to-production
description: Guides the deployment process to production with safety checks
---
```

`name` must be lowercase letters, numbers, hyphens. Layout bundles supporting resources
alongside `SKILL.md`:

```
.windsurf/skills/skill-name/
├── SKILL.md
├── supporting-file.md
├── scripts.sh
└── config-template.yaml
```

Activation: **automatic** (model matches the description, via progressive disclosure — "only
the skill's `name` and `description` are shown to the model by default") or **manual** via
`@skill-name` in Cascade input. **No character or file size limits are documented for
skills** [S6] — unlike rules and workflows below.

`UNVERIFIED`: whether Windsurf honours `license`, `compatibility`, `metadata`, or
`allowed-tools`. The docs page states required fields only and does not enumerate optional
ones.

### 3b. Rules — always-on / conditional context [S7]

| Scope | Path |
|---|---|
| Workspace | `.windsurf/rules/*.md` (one file per rule) |
| Global | `~/.codeium/windsurf/memories/global_rules.md` (single file) |
| System (Enterprise) | e.g. `/etc/windsurf/rules/` on Linux |

Rules are auto-discovered from the current workspace, subdirectories, and **parent
directories up to the git root**.

```markdown
---
trigger: always_on | model_decision | glob | manual
globs: [pattern]   # required for glob mode
---

Rule content here
```

| Mode | `trigger:` | Behavior |
|---|---|---|
| Always On | `always_on` | Full rule content in the system prompt on every message |
| Model Decision | `model_decision` | Description only; model retrieves full content when relevant |
| Glob | `glob` | Applied when Cascade reads/edits a file matching `globs` |
| Manual | `manual` | Only via `@rule-name` |

**Size limits: 12,000 characters per workspace rule file; 6,000 characters for global
rules.** The global rules file and root-level `AGENTS.md` files **don't use frontmatter —
they are always on** [S7].

### 3c. Workflows — manual slash-command procedures [S8]

| Scope | Path |
|---|---|
| Workspace | `.windsurf/workflows/*.md` |
| Global | `~/.codeium/windsurf/global_workflows/*.md` |
| System, macOS | `/Library/Application Support/Windsurf/workflows/` |
| System, Linux/WSL | `/etc/windsurf/workflows/` |
| System, Windows | `C:\ProgramData\Windsurf\workflows\` |

Contain a title, description, and a series of steps. Invoked as `/[workflow-name]`.
**Workflows are manual-only — Cascade will never invoke a workflow automatically.**
**Limited to 12,000 characters each.** The docs explicitly redirect: *"If you want Cascade
to pick up a procedure on its own, use a Skill instead."* [S8]

`UNVERIFIED`: exact workflow frontmatter keys (e.g. `auto_execution_mode`) — [S8] describes
title/description/steps but does not enumerate a frontmatter schema.

**Recommendation: target 3a (Skills). Do not port to rules or workflows** — you'd inherit
the 12,000-char cap and lose automatic activation.

---

## 4. Triggerfish (trigger.fish)

### Product identity and disambiguation

**Triggerfish** (<https://trigger.fish/>, source: `github.com/greghavens/triggerfish`) is an
open-source, multi-channel AI agent platform — Telegram, Signal, Slack, Discord, WhatsApp,
WebChat, Email, Google Chat, CLI — built on Deno/TypeScript, emphasising deterministic
policy enforcement below the LLM layer, with classification levels (PUBLIC → RESTRICTED)
and audit logging [S9, S12].

**This is a different product from Trigger.dev** (<https://trigger.dev>), a background-jobs
platform. Trigger.dev also has an "Agent Skills" documentation page, which pollutes search
results for these terms. Every Triggerfish claim below comes from `trigger.fish` or the
`greghavens/triggerfish` repository — **no Trigger.dev source contributed to this section.**

### VERDICT: YES — Triggerfish accepts user-authored skills, in `SKILL.md` format

This is confirmed from three independent, mutually corroborating sources: the marketing
site [S9], the repository README [S12], and the shipped documentation + runtime loader
source code [S10, S13, S14].

> "Skills are folders with a `SKILL.md` file. Install community skills from The Reef or
> create your own." — [S12] README.md
>
> "🎯 **Skill** | A folder with `SKILL.md` that gives the agent new capabilities" — [S12]
>
> "A skill is a folder with a `SKILL.md` file at its root. The file contains YAML
> frontmatter (metadata) and markdown body (instructions for the agent). Optional
> supporting files -- scripts, templates, configuration -- can live alongside it."
> — [S10] docs/integrations/skills.md, live at <https://trigger.fish/integrations/skills>

### Install locations and precedence [S10]

| Type | Path | Meaning |
|---|---|---|
| **Bundled** | `skills/bundled/` (in-repo: `src/skills/bundled/`) | Ships with Triggerfish, project-maintained |
| **Managed** | `~/.triggerfish/skills/` | Installed from The Reef marketplace |
| **Workspace** | `~/.triggerfish/workspace/<agent-id>/skills/` | **User-authored or agent-authored** |

**Priority: Workspace > Managed > Bundled.** Per [S10]: *"you can always override a bundled
or marketplace skill with your own version. Your customizations are never overwritten by
updates."* **`~/.triggerfish/workspace/<agent-id>/skills/<skill-name>/SKILL.md` is our
install target.**

Note: skills are **not** configured in `triggerfish.yaml` — the config reference has no
skills section [S11]. Discovery is purely filesystem-based via the loader.

### Layout [S10]

```
morning-briefing/
  SKILL.md
  briefing.ts        # Optional supporting code
  template.md        # Optional template
```

Supporting files sit **flat alongside `SKILL.md`**. `UNVERIFIED`: whether Triggerfish
treats `scripts/`, `references/`, `assets/` subdirectories specially. Nothing in the docs or
loader indicates it does — the loader only reads `SKILL.md` and never enumerates
subdirectories, so subdirectories are almost certainly inert-but-harmless (safe to ship).

### Documented frontmatter [S10]

| Field | Required | Description |
|---|---|---|
| `name` | **Yes** | Unique skill identifier |
| `description` | **Yes** | Human-readable description of what the skill does |
| `version` | **Yes** | Semantic version |
| `category` | No | Grouping category (productivity, development, communication…) |
| `tags` | No | Searchable tags for discovery |
| `triggers` | No | Automatic invocation rules (cron schedules, event patterns) |
| `metadata.triggerfish.classification_ceiling` | No | Max taint level this skill can reach (default `PUBLIC`) |
| `metadata.triggerfish.requires_tools` | No | Tools the skill depends on (browser, exec…) |
| `metadata.triggerfish.network_domains` | No | Allowed network endpoints |

Documented example [S10]:

```yaml
---
name: morning-briefing
description: Prepare a daily morning briefing with calendar, email, and weather
version: 1.0.0
category: productivity
tags:
  - calendar
  - email
  - daily
triggers:
  - cron: "0 7 * * *"
metadata:
  triggerfish:
    classification_ceiling: INTERNAL
    requires_tools:
      - browser
      - exec
    network_domains:
      - api.openweathermap.org
      - www.googleapis.com
---
```

### ⚠️ Docs-vs-implementation discrepancy (verified in source) — ACT ON THIS

The prose docs show security fields **nested** under `metadata.triggerfish.*`. **The actual
runtime loader and every shipped bundled skill use them TOP-LEVEL.**

Runtime loader, `src/tools/skills/loader.ts` → `buildSkillFromFrontmatter()` [S13]:

```ts
if (!frontmatter || !frontmatter.name) return null;

const classResult = parseClassification(
  frontmatter.classification_ceiling ?? "PUBLIC",
);
...
return {
  name: frontmatter.name,
  version: frontmatter.version ?? "0.0.0",
  description: frontmatter.description ?? "",
  classificationCeiling: ceiling,
  requiresTools: frontmatter.requires_tools ?? null,
  networkDomains: frontmatter.network_domains ?? null,
  ...
};
```

Shipped bundled skill `src/skills/bundled/pdf/SKILL.md` [S14] — top-level, no `metadata:`:

```yaml
---
name: pdf
version: 1.0.0
description: >
  Extract text and metadata from PDF files using the exec environment.
classification_ceiling: CONFIDENTIAL
requires_tools:
  - run_command
  - write_file
  - read_file
network_domains:
  - registry.npmjs.org
---
```

Three consequences, all load-bearing:

1. **At runtime, only `name` is truly required.** `version` defaults to `"0.0.0"` and
   `description` defaults to `""`. The docs' "required" column describes Reef-publish
   validation, not loading. **An unmodified open-spec `SKILL.md` (name + description only)
   will load in Triggerfish** and default to `classification_ceiling: PUBLIC`.
2. **Emit security fields TOP-LEVEL, not nested**, or they are silently ignored and the
   skill quietly falls back to `PUBLIC` — a security-relevant failure mode.
3. **`metadata:` is ignored by the loader**, so an open-spec `metadata:` block is harmless
   but carries no meaning. Do not encode anything Triggerfish needs there.

Other loader behaviour [S13]: directory entries that are **symlinks are skipped**
(`if (!entry.isDirectory || entry.isSymlink) continue;`) — so unlike Codex, **the
symlink-farm install strategy will NOT work for Triggerfish; copy real directories.**
Directory names are sanitised and path-jailed; a `SKILL.md` that fails to read causes the
directory to be skipped silently. A content hash is computed per skill for integrity.

### The Reef publish validation — stricter than loading [S15]

`docs/reef-registry/scripts/validate-skill.ts`:

```ts
/** Required frontmatter fields for a valid skill submission. */
const SKILL_REQUIRED_FIELDS = [
  "name",
  "version",
  "description",
  "author",
  "tags",
  "category",
  "classification_ceiling",
] as const;
```

Note `author`, `tags`, `category`, `classification_ceiling` are required **for marketplace
publication** (and `classification_ceiling` is expected **top-level** here too, confirming
the loader's reading over the prose docs). `tags` must be an array. Local install does not
require them.

### Discovery, loading, and CLI [S10]

Pipeline: **Scanner** (finds skills across bundled/managed/workspace) → **Loader** (reads
frontmatter, validates metadata) → **Resolver** (priority conflict resolution) →
**Registration**. Skills with `triggers` are automatically wired into the scheduler. Skills
with `requires_tools` are checked against available tools — a missing tool **flags but does
not block** the skill.

```bash
triggerfish skill search "calendar"
triggerfish skill install google-cal
triggerfish skill list
triggerfish skill update --all
triggerfish skill publish
triggerfish skill remove google-cal
```

**The Reef** (marketplace) is marked **_coming soon_** in both the README and the docs
[S12, S10]. Search/browse, one-command install, publish, security scanning, versioning, and
reviews are described as planned features. **Local/manual install by dropping a folder into
the workspace skills directory is the available path today.**

### Security lifecycle — affects installs [S10]

Skills installed from The Reef are downloaded, scanned for malicious patterns, then
**enter `UNTRUSTED` state until the owner classifies them**, and must be classified and
activated by an owner or admin. Agent-authored skills are marked `PENDING_APPROVAL` and
*"always require owner approval before they become active. The agent cannot self-approve its
own skills."* Enterprise deployments add: skills cannot declare a classification ceiling
above the user's clearance, network endpoint declarations are audited, and all self-authored
skills are logged for compliance.

`UNVERIFIED`: whether a **manually placed** workspace skill (copied in by the user, not
agent-authored and not Reef-installed) also requires an explicit classification/approval
step before activation. The docs describe the approval gate for agent-authored and
Reef-installed skills specifically. **Budget for a possible one-time approval step when
installing.**

### Adjacent Triggerfish concepts (not skills — don't confuse)

- **SPINE.md** — agent identity and mission file; the system-prompt foundation [S12].
- **TRIGGER.md** — proactive/autonomous monitoring behaviour on configurable schedules
  [S9]. A bundled `triggers` skill teaches authoring these.
- **Plugins** — a separate mechanism, in `~/.triggerfish/plugins/`, configured under the
  `plugins` key of `triggerfish.yaml` [S11]. Not our target.
- Bundled skills (10): `tdd`, `mastering-typescript`, `mastering-python`, `skill-builder`,
  `integration-builder`, `git-branch-management`, `deep-research`, `pdf`, `triggerfish`,
  `triggers` [S10, S12]. `skill-builder` documents the SKILL.md format to the agent itself.

---

## Portability Matrix

Baseline = the agentskills.io canonical field set. ✅ consumed · ⚠️ accepted but altered or
unconfirmed · ➕ target-specific addition · ❌ not supported / ignored.

| Field | Open spec | Claude | Codex | Windsurf | Triggerfish |
|---|---|---|---|---|---|
| `name` | Required; must match dir name | ⚠️ **Optional**; defaults to dir name; display-label only for personal/project. Reserved words "anthropic"/"claude" banned on claude.ai | ✅ Required | ✅ Required | ✅ **The only truly required field at runtime** |
| `description` | Required, ≤1024 | ⚠️ "Recommended"; falls back to first paragraph; `description`+`when_to_use` truncated at **1,536** | ✅ Required; front-load trigger words | ✅ Required | ⚠️ Docs say required; loader defaults to `""` |
| `license` | Optional | ⚠️ UNVERIFIED (not in Claude Code table; harmless) | ⚠️ UNVERIFIED | ⚠️ UNVERIFIED | ❌ Ignored by loader |
| `compatibility` | Optional, ≤500 | ⚠️ UNVERIFIED | ⚠️ UNVERIFIED | ⚠️ UNVERIFIED | ❌ Ignored by loader |
| `metadata` | Optional map | ⚠️ UNVERIFIED | ⚠️ UNVERIFIED | ⚠️ UNVERIFIED | ❌ **Ignored** — nested `metadata.triggerfish.*` does NOT work |
| `allowed-tools` | Optional, experimental | ✅ Space/comma string or YAML list; permission pre-grant for the turn | ⚠️ UNVERIFIED | ⚠️ UNVERIFIED | ❌ Use top-level `requires_tools` instead |
| `version` | ❌ not in spec (use `metadata.version`) | ❌ | ❌ | ❌ | ➕ **Top-level, required for publish**; defaults `0.0.0` |
| `classification_ceiling` | ❌ | ❌ | ❌ | ❌ | ➕ **Top-level**; default `PUBLIC` |
| `requires_tools` / `network_domains` | ❌ | ❌ | ❌ | ❌ | ➕ **Top-level** |
| `author` / `tags` / `category` | ❌ (put in `metadata`) | ❌ | ❌ | ❌ | ➕ Required for **Reef publish** only |
| `triggers` (cron) | ❌ | ➕ separate scheduled-tasks feature | ❌ | ❌ | ➕ Auto-wires into the scheduler |
| `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell` | ❌ | ➕ Claude-only | ❌ | ❌ | ❌ |
| UI/policy metadata | ❌ | ❌ | ➕ `agents/openai.yaml` | ❌ | ❌ |
| `scripts/` `references/` `assets/` | ✅ Canonical | ✅ | ✅ | ✅ (flat files also fine) | ⚠️ Flat layout documented; subdirs presumed inert-but-harmless |
| `${CLAUDE_SKILL_DIR}` etc. | ❌ | ➕ Claude-only | ❌ | ❌ | ❌ |
| Symlinked skill dirs | — | ✅ Followed, deduped | ✅ Followed | ⚠️ UNVERIFIED | ❌ **Explicitly skipped** |
| Size guidance | <5000 tokens / <500 lines | 5,000-token compaction retention | — | No documented limit | — |

### Required transformation, per target

Author **one canonical open-spec skill folder** (`name`, `description`, plus `license` /
`metadata` as desired; body <500 lines; detail in `references/`). Then:

- **Claude** — *zero transformation.* Copy to `~/.claude/skills/<name>/` or
  `.claude/skills/<name>/`. Verify `name` contains neither "anthropic" nor "claude" if
  claude.ai/Cowork is a target. Optionally add `allowed-tools`, `disable-model-invocation`,
  `paths`, `context: fork`. For Cowork/routines you **must** enable on the claude.ai account,
  commit to the repo, or ship in a repo-declared plugin — `~/.claude/skills/` is not read.
  For claude.ai, upload as a **zip** (Settings > Features). There is no `.skill` format.
- **Codex** — *zero content transformation; path change only.* Copy to
  `.agents/skills/<name>/` or `~/.agents/skills/`. Symlinks are followed, so one canonical
  directory can serve both Claude and Codex. Optionally add `agents/openai.yaml` for
  display name, icon, and `policy.allow_implicit_invocation`.
- **Windsurf** — *zero transformation, and usually zero copying.* Windsurf already reads
  `.agents/skills/`, `~/.agents/skills/`, `.claude/skills/`, `~/.claude/skills/`. Only place
  a copy in `.windsurf/skills/<name>/` or `~/.codeium/windsurf/skills/<name>/` if you want
  Windsurf-exclusive behaviour. Do **not** downconvert to `.windsurf/rules/` or
  `.windsurf/workflows/` — those cap at 12,000 chars and workflows never auto-activate.
- **Triggerfish** — *additive frontmatter transformation + real-copy install.* Copy the
  **real directory** (not a symlink — symlinks are skipped) to
  `~/.triggerfish/workspace/<agent-id>/skills/<name>/`. Add **top-level**:
  `version: <semver>` (required for publish, defaults `0.0.0`),
  `classification_ceiling: PUBLIC|INTERNAL|CONFIDENTIAL|RESTRICTED` (defaults `PUBLIC` — set
  it explicitly), and `requires_tools:` / `network_domains:` if the skill executes or
  reaches the network. **Never nest these under `metadata:`.** For Reef publication also add
  `author`, `tags` (array), `category`. Expect a possible owner classification/approval step.

**Net result:** the canonical folder is byte-identical for Claude, Codex, and Windsurf.
Triggerfish needs 1–4 extra top-level YAML keys — all additive, all ignored by the other
three. **A single source of truth plus a thin Triggerfish frontmatter-injection step covers
all four.** No body rewriting is required for any target; the only body-level portability
hazard is `${CLAUDE_SKILL_DIR}` and Claude's `$ARGUMENTS`-family substitutions, which should
be avoided in a portable skill (use relative paths from the skill root instead).

---

## Triggerfish Verdict

**CONFIRMED YES — Triggerfish accepts user-authored skills, and the format is `SKILL.md`.**

The user asked to be told definitively rather than have this guessed at. This is not a
guess. It is verified from three independent sources fetched today:

1. **Marketing site** — "Skills extend capabilities through simple folder conventions" [S9].
2. **Repository README** — "Skills are folders with a `SKILL.md` file. Install community
   skills from The Reef or create your own." [S12].
3. **Shipped docs + runtime source** — a full frontmatter table, three-tier install paths
   with documented precedence, a scanner/loader/resolver pipeline, 10 real bundled
   `SKILL.md` files on disk, and the loader function that parses the frontmatter
   [S10, S13, S14].

**Concretely:**
- **Format:** a folder containing `SKILL.md` — YAML frontmatter + markdown body. Same shape
  as the agentskills.io open standard.
- **User install path:** `~/.triggerfish/workspace/<agent-id>/skills/<skill-name>/SKILL.md`.
  Workspace skills have the **highest** priority and override bundled/managed skills of the
  same name; they are never overwritten by updates.
- **Compatibility with our canonical skills:** **high.** At runtime only `name` is strictly
  required, so an unmodified open-spec `SKILL.md` loads successfully.
- **Required change for a good port:** add **top-level** `version` and
  `classification_ceiling` (plus `requires_tools` / `network_domains` where relevant).
  **Do not** nest them under `metadata:` despite what the prose docs show — the loader reads
  them top-level and silently defaults to `PUBLIC` otherwise. Verified in
  `src/tools/skills/loader.ts` and in every shipped bundled skill.
- **Install must copy real directories, not symlinks** — the loader explicitly skips symlinked
  entries.

**Caveats, stated plainly:**
- **The Reef marketplace is _coming soon_,** not shipping. `triggerfish skill install`
  exists as a CLI command but the registry behind it is not live. **Install today is
  manual**: place the folder in the workspace skills directory.
- Triggerfish is **not** listed on the agentskills.io client showcase [S1], and no
  Triggerfish page fetched claims conformance with the agentskills.io spec. The format is
  *convergent and compatible*, not *certified*. Its `version` / `classification_ceiling` /
  `requires_tools` / `network_domains` fields are Triggerfish extensions outside the open
  spec.
- `UNVERIFIED`: whether a manually-placed workspace skill needs an explicit owner
  classification/approval step before activation. The documented approval gates cover
  agent-authored (`PENDING_APPROVAL`) and Reef-installed (`UNTRUSTED`) skills. Budget for
  a possible one-time approval.

**Trigger.dev disambiguation:** trigger.dev is a *different product* (background jobs) that
also publishes an "Agent Skills" page. It is a genuine search-result hazard for these query
terms. No Trigger.dev source was used for any Triggerfish claim above.

---

## Gaps and Ambiguities

1. **No `.skill` package format found.** `UNVERIFIED` / probably non-existent. Claude
   distributes skills as directories, zips (claude.ai), or plugins. If the packaging plan
   assumed a `.skill` archive, that assumption should be dropped.
2. **Optional-field support is unconfirmed for three of four targets.** Only agentskills.io
   [S2] and Claude Code [S3] enumerate optional frontmatter. Codex and Windsurf document
   required fields only. `license`, `compatibility`, `metadata`, and `allowed-tools` are
   presumed accepted-and-ignored there, but this is not verified. Low risk — YAML frontmatter
   parsers generally tolerate unknown keys, and Triggerfish's loader demonstrably does.
3. **Triggerfish docs contradict Triggerfish code** on nesting of `classification_ceiling` /
   `requires_tools` / `network_domains`. Resolved in favour of the code [S13] and the shipped
   bundled skills [S14], which agree with each other and with the Reef validator [S15].
   Worth reporting upstream.
4. **`allowed-tools` is flagged Experimental** in the open spec: "Support for this field may
   vary between agent implementations." Do not rely on it for security in a portable skill.
5. **Codex + AGENTS.md precedence not re-verified** in this task. Skills and AGENTS.md are
   separate mechanisms; the exact merge/precedence rules for AGENTS.md were not restated on
   the Codex skills page.
6. **Windsurf skill size limits undocumented.** Rules cap at 12,000 chars and workflows at
   12,000 chars, but [S6] documents no limit for skills. Assume the open spec's <5,000-token
   guidance rather than relying on an unstated ceiling.
7. **Windsurf symlink support unverified** for skill directories. Claude follows symlinks,
   Codex follows symlinks, Triggerfish skips them. Windsurf is unknown — prefer real copies
   if you need one install strategy that works everywhere.
8. **Triggerfish `scripts/`/`references/`/`assets/` handling unverified.** Docs show a flat
   layout. Subdirectories are almost certainly inert-but-harmless (the loader reads only
   `SKILL.md`), but progressive loading of `references/` may not occur — the agent would need
   an explicit instruction in the body to read them.
9. **agentskills.io spec version, license, and governance model not stated** on the pages
   fetched. Known: originated at Anthropic, released as an open standard, developed openly
   on GitHub with a public Discord.
10. **Cowork skill sync mechanics** are documented at the level of "synced at session start"
    from claude.ai account settings; the underlying upload/packaging format for that sync
    (beyond the zip upload path) was not verified.

---

## Source Inventory

All accessed **2026-07-31**.

| ID | URL | Date accessed | Covers |
|---|---|---|---|
| S1 | https://agentskills.io/home.md | 2026-07-31 | Open standard overview; origin at Anthropic; progressive disclosure; 40+ conforming clients incl. all four targets; GitHub/Discord governance |
| S2 | https://agentskills.io/specification | 2026-07-31 | **Canonical spec**: full frontmatter table, name/description constraints, `license`/`compatibility`/`metadata`/`allowed-tools`, directory layout, progressive disclosure, file references, `skills-ref` validator |
| S3 | https://code.claude.com/docs/en/skills | 2026-07-31 | Claude Code: install paths & precedence, nested/`--add-dir`/symlink/live-reload behaviour, **full 18-field frontmatter reference**, string substitutions, command naming, Cowork/cloud limits, share/distribution, `skillOverrides`, compaction budgets |
| S4 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | 2026-07-31 | Claude platform: required fields, name reserved words ("anthropic"/"claude"), 1024-char description, claude.ai **zip** upload via Settings > Features, `/v1/skills` API, absence of a `.skill` format |
| S5 | https://developers.openai.com/codex/skills/ | 2026-07-31 | **Codex**: `.agents/skills` search paths & precedence, symlink following, duplicate handling, required frontmatter, `agents/openai.yaml` schema, implicit/explicit invocation |
| S6 | https://docs.windsurf.com/windsurf/cascade/skills | 2026-07-31 | **Windsurf Skills**: `.windsurf/skills/`, `~/.codeium/windsurf/skills/`, enterprise system paths, **cross-agent paths `.agents/skills/` + `.claude/skills/`**, frontmatter, activation, open-standard conformance |
| S7 | https://docs.windsurf.com/windsurf/cascade/memories | 2026-07-31 | Windsurf **rules**: `.windsurf/rules/*.md`, `global_rules.md`, `trigger:` activation modes, `globs`, 12,000 / 6,000 char limits, AGENTS.md always-on |
| S8 | https://docs.windsurf.com/windsurf/cascade/workflows | 2026-07-31 | Windsurf **workflows**: `.windsurf/workflows/*.md`, global + enterprise paths, slash invocation, manual-only, 12,000-char limit, "use a Skill instead" guidance |
| S9 | https://trigger.fish/ and https://trigger.fish/features/ | 2026-07-31 | **Triggerfish** product identity: multi-channel, open-source, policy enforcement, classification levels, "Skills extend capabilities through simple folder conventions", The Reef, SPINE.md, TRIGGER.md |
| S10 | https://trigger.fish/integrations/skills (repo: `docs/integrations/skills.md`) | 2026-07-31 | **Triggerfish skills — primary source**: SKILL.md definition, frontmatter table, example, bundled/managed/workspace paths & precedence, discovery pipeline, self-authoring flow, The Reef (coming soon), CLI commands, security lifecycle |
| S11 | https://trigger.fish/reference/config-yaml.html | 2026-07-31 | `triggerfish.yaml` reference — confirms **no skills section**; plugins live in `~/.triggerfish/plugins/` (separate mechanism) |
| S12 | https://raw.githubusercontent.com/greghavens/triggerfish/master/README.md | 2026-07-31 | "Skills are folders with a `SKILL.md` file"; key-concepts table (SPINE.md, Skill, Trigger, The Reef _coming soon_); 10 bundled skills |
| S13 | `greghavens/triggerfish` @ `master`, `src/tools/skills/loader.ts` | 2026-07-31 | **Runtime loader source**: `buildSkillFromFrontmatter()` reads **top-level** `classification_ceiling`/`requires_tools`/`network_domains`; only `name` strictly required; `version` defaults `0.0.0`; **symlinked dirs skipped**; path jailing; content hashing; priority resolution |
| S14 | `greghavens/triggerfish` @ `master`, `src/skills/bundled/{pdf,deep-research}/SKILL.md` | 2026-07-31 | Real shipped skills confirming **top-level** security fields and no `metadata:` block |
| S15 | `greghavens/triggerfish` @ `master`, `docs/reef-registry/scripts/validate-skill.ts` | 2026-07-31 | Reef publish validation: `SKILL_REQUIRED_FIELDS` = name, version, description, author, tags, category, classification_ceiling; `tags` must be an array |
| S16 | https://agentskills.io/clients.md | 2026-07-31 | Client showcase with per-vendor setup-instruction URLs; confirms Claude Code, Claude, OpenAI Codex, Cursor, Copilot, VS Code et al.; **Triggerfish absent** |

**Access notes:** `docs.claude.com` 302-redirects to `platform.claude.com`. The GitHub API
and `github.com/tree/...` HTML were unavailable in this environment (session access
restriction and robots.txt respectively); Triggerfish source claims [S13][S14][S15] were
verified by shallow-cloning the repository over HTTPS and reading the files directly. The
repo's default branch is `master`, not `main`. `trigger.fish` serves docs under
`/integrations/` (extensionless URLs); `/guide/skills.html` and `/llms.txt` 404.
