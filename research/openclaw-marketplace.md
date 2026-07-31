# OpenClaw & ClawHub — Skills Marketplace Dossier

Research date: 2026-07-31. All claims carry a bracketed source ref keyed to `## Source Inventory`.

---

## 1. What OpenClaw is

OpenClaw is real and is one of the largest open-source projects on GitHub (~385k stars as displayed on the repo page) [S1].

- **Identity:** README describes it as "a *personal AI assistant* that learns and grows with you, running on your own devices," developed by the OpenClaw Foundation, a non-profit [S1].
- **What it does:** local-first gateway and control plane for an AI assistant; integrates 25+ messaging channels (WhatsApp, Telegram, Slack, Discord, Signal, iMessage), multi-agent routing, voice wake detection, Canvas UI, browser automation, scheduling [S1].
- **Maintainer:** Peter Steinberger and community. **License:** MIT [S1].
- **Repo:** https://github.com/openclaw/openclaw [S1]
- **Docs:** https://docs.openclaw.ai (canonical; a `documentation.openclaw.ai` mirror also serves the same ClawHub pages) [S2][S9]
- **Not a fork, but renamed twice:** the project was previously named **Clawdbot**, then **Moltbot**, then **OpenClaw** [S12]. This is corroborated inside the codebase: ClawHub accepts `metadata.clawdbot` and `metadata.clawdis` as **aliases** for `metadata.openclaw` in skill frontmatter, and legacy `.clawdhubignore` / `.clawdhub/` paths are still honored [S5][S6]. Practical consequence: older community skills in the wild may use the `clawdbot` metadata key.

**Verdict on Q1:** Real. Open-source agent/assistant framework (MIT), not a fork of Claude Code or similar — an independent project with its own rename history.

---

## 2. Does it have a skills marketplace?

**Yes — it is called ClawHub, and it is live today.** [S3][S4][S6]

- **Name:** ClawHub — "the public skill registry for OpenClaw: publish, version, and search text-based agent skills (a `SKILL.md` plus supporting files)" [S6].
- **Web:** https://clawhub.ai — live, serving listings, showing publish CLI instructions inline, advertising "signed manifests," "moderated releases," "version history," vector search, and GitHub import [S4].
- **Source:** https://github.com/openclaw/clawhub — full open-source registry (TanStack Start web app + Convex backend + OpenAI `text-embedding-3-small` vector search) [S6].
- **Docs tab:** https://docs.openclaw.ai/clawhub (mirrored from `clawhub/docs/`) [S3][S11].
- **Scale:** a third-party curated collection claims "5,400+ skills filtered and categorized from the official OpenClaw Skills Registry" [S13]; the clawhub.ai homepage metadata read at fetch time showed a much smaller featured count (30 skills / 12 plugins), so treat any single skill-count figure as UNVERIFIED [S4][S13].
- ClawHub hosts three artifact families: **skills** (text bundles), **code plugins**, and **bundle plugins** [S3][S6].

---

## 3. Format consumed — same `SKILL.md` folder spec

**OpenClaw explicitly conforms to the open AgentSkills spec.** The docs state verbatim: "OpenClaw follows the [AgentSkills](https://agentskills.io) spec." [S2]

- A skill is **a folder containing a required `SKILL.md`** plus optional supporting files [S5][S9].
- Filename tolerance: `SKILL.md`, lowercase `skill.md`, and legacy `skills.md` are all accepted by ClawHub [S5].
- Frontmatter parsing: "Frontmatter is parsed as YAML first; if that fails, it falls back to a single-line-only parser. Nested `metadata` blocks (including multi-line YAML mappings) are flattened to a JSON string and re-parsed as JSON5" [S2].
- Naming rule for portability: "For portable Agent Skills, `name` should match the parent directory and use 1–64 lowercase letters, numbers, or hyphens." ClawHub keeps the routable slug and catalog display name separate, so "existing names from other clients remain publishable and are not silently rewritten" [S5]. **This is the key portability guarantee — skills authored for Claude/Codex/Windsurf publish unchanged.**
- Body helper: use `{baseDir}` to reference files inside the skill folder without absolute paths [S2][S10].

### Install paths (loading order, highest precedence first) [S2]

| Priority | Source | Path |
|---|---|---|
| 1 (highest) | Workspace skills | `<workspace>/skills` |
| 2 | Project agent skills | `<workspace>/.agents/skills` |
| 3 | Personal agent skills | `~/.agents/skills` (default state only) |
| 4 | Managed / local skills | `<state-dir>/skills` (i.e. `~/.openclaw/skills`) |
| 5 | Bundled skills | shipped with the install |
| 6 (lowest) | Extra directories | `skills.load.extraDirs` + plugin-provided skill dirs |

"When the same skill name appears in multiple places, the highest source wins." [S2]

Discovery is **recursive**: "OpenClaw discovers a skill whenever `SKILL.md` appears anywhere under a configured root (up to 6 levels deep)," so grouped layouts like `<workspace>/skills/research/SKILL.md` work [S2].

### Cross-check vs sibling agent's findings

OpenClaw reads **`<workspace>/.agents/skills` and `~/.agents/skills`** — the *same* `.agents/skills` convention the sibling agent found for OpenAI Codex, and which Windsurf also reads [given]. So OpenClaw is **format-compatible and partially path-compatible** with the Claude / Codex / Windsurf / Triggerfish family. OpenClaw adds its own primary roots `<workspace>/skills` and `~/.openclaw/skills` [S2].

Additionally, at the *plugin* (not skill) layer, OpenClaw auto-detects foreign bundle layouts including `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and `.cursor-plugin/plugin.json`, reading their declared skill roots — further evidence of deliberate cross-ecosystem compatibility [S8].

---

## 4. Frontmatter fields

### Required (per AgentSkills spec)
| Field | Notes |
|---|---|
| `name` | Skill identifier; lowercase letters/digits/hyphens, 1–64 chars, should match parent dir [S2][S5][S10] |
| `description` | One-line summary; used by the agent for routing AND as the ClawHub UI summary / search text [S2][S5] |

### Top-level optional — OpenClaw-specific runtime behavior [S2][S10]
| Field | Type | Purpose |
|---|---|---|
| `homepage` | string | URL shown as "Website" in the macOS Skills UI (also settable via `metadata.openclaw.homepage`) |
| `user-invocable` | boolean (default `true`) | Expose as a user slash command |
| `disable-model-invocation` | boolean (default `false`) | Keep instructions out of the agent's normal prompt; still slash-invocable |
| `command-dispatch` | `"tool"` | Slash command bypasses the model, dispatches straight to a tool |
| `command-tool` | string | Tool name for dispatch |
| `command-arg-mode` | `"raw"` (default) | Forwards raw arg string to the tool |
| `version` | string (semver) | Recognized by ClawHub as basic publish metadata [S5] |

Note: the `docs/tools/skills.md` GitHub rendering also surfaced a `hidden` key and `tool-name` as a dispatch alias; these were not present in the raw canonical file section read. Treat `hidden` / `tool-name` as **UNVERIFIED** aliases [S7 vs S2].

### `metadata.openclaw` block (aliases: `metadata.clawdbot`, `metadata.clawdis`) [S5][S2]
| Field | Type | Purpose |
|---|---|---|
| `requires.env` | string[] | Env vars that MUST be present |
| `requires.bins` | string[] | CLI binaries that must ALL exist on PATH |
| `requires.anyBins` | string[] | At least one binary must exist |
| `requires.config` | string[] | OpenClaw config paths the skill reads (must be truthy) |
| `primaryEnv` | string | Main credential env var |
| `envVars` | array of `{name, required?, description?}` | Per-variable metadata; use `required: false` for optional vars |
| `always` | boolean | Skill always active, bypasses all gates |
| `skillKey` | string | Override the config lookup / invocation key |
| `emoji` | string | Display emoji (macOS UI) |
| `homepage` | string | Docs/homepage URL |
| `os` | string[] | OS restriction; docs give both `darwin\|linux\|win32` [S2] and `["macos"],["linux"]` [S5] — the two docs disagree, see Gaps |
| `install` | array | Dependency install specs |
| `nix` | object | Nix plugin pointer (`plugin`, `systems`) [S6] |
| `config` | object | Legacy Clawdbot config spec (`requiredEnv`, `stateDirs`, `example`) [S6] |
| `cliHelp` | string | Embedded `cli --help` output, recommended for nix plugins [S6] |

**Install spec shape** [S2][S5]:
```yaml
metadata:
  openclaw:
    install:
      - id: brew
        kind: brew          # brew | node | go | uv | download
        formula: jq         # or `package:` for node/go/uv
        bins: [jq]
        label: Install via Homebrew
```
`download` kind takes `url` (required), `archive` (`tar.gz` | `tar.bz2` | `zip`), `extract`, `stripComponents`, `targetDir` (default `~/.openclaw/tools/`) [S2]. Gateway-backed selection preference order: Homebrew → uv → configured node manager → go → download [S7].

### Marketplace-publishing-specific fields — the honest answer

There is **no `author`, `license`, `tags`, `category`, `icon`, or `repository` field in skill frontmatter.** [S5]

- **`license`:** forbidden to set. "All skills published on ClawHub are licensed under `MIT-0` … Do not add conflicting license terms in `SKILL.md`; ClawHub does not support per-skill license overrides." [S5][S9]
- **Pricing:** forbidden. "ClawHub does not support paid skills, per-skill pricing, paywalls, or revenue sharing. Do not add pricing metadata to `SKILL.md`; it is not part of the skill format." [S5]
- **`author`/ownership:** derived from the authenticated ClawHub publisher handle (`--owner`), not from frontmatter [S9].
- **`icon`:** exists only for **plugins**, in `openclaw.plugin.json` — "add `icon` to `openclaw.plugin.json` with any HTTPS image URL" for the catalog homepage. Not available for skills [S9].
- **`tags`:** ClawHub has version tags (string pointers to a version, e.g. `latest`) [S5]. A `--tags` publish flag was described on one docs page [S3] but does **not** appear in the canonical CLI reference [S14] — treat as UNVERIFIED.
- **`version`:** supported in frontmatter [S5], but the CLI computes it automatically (see §6).

---

## 5. Manifest file for marketplace submission

**For skills: NO manifest file is required.** The `SKILL.md` frontmatter *is* the manifest — "The server extracts metadata from frontmatter during publish." [S5] There is no `marketplace.json`, no `plugin.json`, no repo-level index for skills.

Files that may appear in a skill folder [S5]:

| File | Required? | Written by | Purpose |
|---|---|---|---|
| `SKILL.md` (or `skill.md`, legacy `skills.md`) | **Required** | you | The skill + its manifest frontmatter |
| `.clawhubignore` (legacy `.clawdhubignore`) | Optional | you | Ignore patterns for publish/sync |
| `.gitignore` | Optional | you | Also honored as publish ignore |
| `.clawhub/origin.json` (legacy `.clawdhub`) | Auto | CLI | Local install provenance |
| `<workdir>/.clawhub/lock.json` | Auto | CLI | Workdir install state / pinning |

**For plugins (different, heavier path):** a native OpenClaw plugin **must** ship `openclaw.plugin.json` in the plugin root; "A missing or invalid manifest blocks config validation and is treated as a plugin error." Minimal form [S8]:
```json
{
  "id": "voice-call",
  "configSchema": { "type": "object", "additionalProperties": false, "properties": {} }
}
```
Code plugins additionally need `package.json` carrying `openclaw.compat.pluginApi` and `openclaw.build.openclawVersion`; "Top-level `package.json.version` is not used as a fallback for publish validation." [S6][S9][S14]

---

## 6. Submission / publishing process

**CLI-driven, not PR-based.** There is no registry repo to open a pull request against [S6][S9].

```bash
npm i -g clawhub          # or: pnpm add -g clawhub
clawhub login             # GitHub OAuth; `clawhub login --device` for headless
clawhub whoami
clawhub skill publish ./my-skill --dry-run
clawhub skill publish ./my-skill --slug my-skill --name "My Skill" --owner <handle>
```
[S9][S14][S15]

Server-side flow: "ClawHub checks that your token can publish for that owner, validates the metadata, name, version, files, and source information, then stores the release and starts automated security checks. If validation fails, nothing is published. New releases may also stay out of normal install and download surfaces until review finishes." [S9]

**Publish routes (three):** [S4][S5][S9]
1. CLI (`clawhub skill publish` / `clawhub sync`)
2. Web UI, including **GitHub import** — but the importer "only discovers `SKILL.md` or legacy `skills.md` files in **public, non-fork** repositories owned by the signed-in GitHub account. It does not import private repos, forks, archived/disabled repos, or third-party public repos." [S5]
3. Reusable GitHub Action: `uses: openclaw/clawhub/.github/workflows/skill-publish.yml@main`, with inputs `owner`, `dry_run`, `root` (default `skills`), `skill_path`, and secret `clawhub_token` [S9]

**Versioning is automatic:** "New skills default to `1.0.0`; changed skills default to the next patch version." Publishing is content-fingerprint based — "Compares the local bundle fingerprint with ClawHub and exits successfully when the content is already published." Use `--version` for an explicit semver, or `--bump minor|major` with `sync` [S14].

**Verified skill-publish flags:** `--slug`, `--name`, `--owner`, `--version`, `--changelog`, `--dry-run`, `--json`, `--migrate-owner` [S9][S14][S15]. Multi-skill repo publishing: `clawhub sync --all [--root ./skills] [--owner <handle>] [--bump minor]` — "one-way publish only" [S14].

**Ownership rules:** owners are handles like `@alice` / `@openclaw`; public skill URL is `https://clawhub.ai/<owner>/<slug>` [S9]. Publisher handles may use lowercase letters, numbers, hyphens, dots, underscores; must start and end with a lowercase letter or number [S5]. For plugins the package **scope must match the publish owner** exactly, else rejection: `Package scope "@openclaw" must match selected owner "@vintageayu".` [S9] Namespace disputes go through an "Org / Namespace Claim" GitHub issue template [S9].

Lifecycle: `clawhub skill rename`, `clawhub skill merge` (old slugs become redirect aliases), soft `delete`/`undelete`; hard delete is admin-only [S6].

---

## 7. Validation, limits, security review

### Slug / naming validation
- Slug derived from folder name by default; must be lowercase and URL-safe: `^[a-z0-9][a-z0-9-]*$` [S3][S5].
- Package slugs must be lowercase and npm-safe [S5].

### File and size limits [S5]
- **Total bundle size: 50 MB** (server-side).
- Embedding text (for vector search) covers `SKILL.md` + up to **~40 bounded UTF-8 files** (best-effort cap).
- "Publish accepts **all regular files** in the skill folder, regardless of extension." Non-UTF-8 files keep exact bytes and are downloadable; UTF-8 files are previewable and analyzed. Note: an earlier docs rendering described a *text-extension allowlist* (`packages/schema/src/textFiles.ts`) [S3]; the canonical current spec supersedes that — text detection is "a rendering and analysis concern, **not an upload allowlist**" [S5].
- **Excluded from publish:** ignore-file matches (`.clawhubignore`, `.gitignore`), **hidden paths**, **symlinks**, macOS metadata [S5].

### Declaration-coherence validation (the one that will actually fail you)
"ClawHub's security analysis checks that what your skill declares matches what it actually does. If your code references `TODOIST_API_KEY` but your frontmatter doesn't declare it under `requires.env`, `primaryEnv`, or `envVars`, the analysis will flag a **metadata mismatch**." [S5][S6]

There is **no permissions / allowed-tools / network-domain allowlist field** in the skill format — OpenClaw does not have a Claude-style `allowed-tools` frontmatter key for skills. Authority is expressed implicitly through `requires.*` / `envVars` / `install` and judged by the audit [S5][S16].

### Security review pipeline [S16]
Every release is audited automatically. The audit page at `/<owner>/skills/<slug>/security-audit` combines three components:
1. **SkillSpector**
2. **VirusTotal** (malware/reputation telemetry, e.g. "62/62 vendors flagged this skill as clean")
3. **Risk analysis**, powered internally by **ClawScan**, using the [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/) as its lens — prompt injection, tool misuse, credential exposure, unsafe execution, memory/context poisoning, excessive agency.

**Audit status:** `Pass` | `Review` | `Warn` | `Malicious` | `Do not install` | `Pending` | `Error`. **Risk level:** `Low` | `Medium` | `High`. **Finding severities:** `Info`/`Low`/`Medium`/`High`/`Critical`. "Medium review findings stay visible; the suspicious filter is reserved for high-impact or malicious concerns." [S6][S16]

Key stance: "ClawScan does not treat a scary-looking capability as automatically malicious. It asks whether the capability is **disclosed, purpose-aligned, and supported by the release's stated use case**." [S16]

Authors can run scans themselves: `clawhub scan --slug <slug> [--version X] [--update] [--output report.zip]`. The report archive contains `manifest.json`, `clawscan.json`, `skillspector.json`, `static-analysis.json`, `virustotal.json`, `README.md`. Blocked versions can be retrieved via `clawhub scan download <name> --version <v>`. Local-path scans are no longer supported — you must upload a version first [S14]. False positives are recoverable via the ClawHub dashboard or `clawhub skill rescan @owner/<slug>` [S2].

### Gates and moderation
- **Account gate:** "ClawHub is open by default: anyone can upload, but publishing requires a **GitHub account old enough to pass the upload gate**." [S3][S11]
- New releases may stay hidden from install/download surfaces until review completes [S9][S11].
- Moderation: reports, moderation holds, hidden/quarantined/revoked listings, escalating publisher penalties up to bans (API tokens revoked), appeal via recovery form [S17].
- Acceptable-usage prohibits, among others, "bulk publishing large numbers of low-effort, duplicative, placeholder" skills and metric gaming via self-install loops [S18].
- Independent security researchers have publicly criticized this model — Unit 42 published on the marketplace as an AI supply-chain threat, and CertiK argues "Skill Scanning Is Not a Security Boundary" [S19][S20].

---

## 8. Symlinks and zipped skills

**Symlinks — publish side:** symlinks are **excluded** from the published bundle. "Ignore files, hidden paths, **symlinks**, macOS metadata, and server-side size limits still apply." [S5] So a skill relying on symlinked shared assets will publish with those files missing. Dereference/copy before publishing.

**Symlinks — local load side:** partially supported, gated. "Workspace, project-agent, and extra-dir skill discovery only accepts skill roots whose resolved realpath stays inside the configured root, unless `skills.load.allowSymlinkTargets` explicitly trusts a target root. … Managed `~/.openclaw/skills` and personal `~/.agents/skills` may contain symlinked skill folders, but **every `SKILL.md` realpath must still stay inside its resolved skill directory**." Skill Workshop writes through trusted targets only with `skills.workshop.allowSymlinkTargetWrites` [S2]. Config example [S2]:
```json
{ "skills": { "load": { "allowSymlinkTargets": ["~/Projects/manager/skills"], "watch": true, "watchDebounceMs": 250 } } }
```
Note `openclaw/agent-skills` ships an `install-skills` script with symlink-or-copy options for local installs [S21].

**Zipped skills:**
- **Publishing a zip is NOT supported for skills.** `clawhub skill publish <path>` takes a **folder**; the CLI fingerprints and uploads its files [S14][S5]. (Only *plugins* accept an archive source — a ClawPack npm-pack `.tgz` [S14].)
- **Distribution** is zip-based: installs "download zip via `/api/v1/download`" and extract into `<workdir>/<dir>/<slug>` [S14].
- **Private/side-channel zip installs exist but are off by default:** gateway clients can stage a zip skill archive with `skills.upload.begin` / `skills.upload.chunk` / `skills.upload.commit`, then `skills.install({ source: "upload", ... })`. "This path is off by default and requires `skills.install.allowUploadedArchives: true` in `openclaw.json`." [S2]

---

## 9. Additive requirements vs the generic AgentSkills package

If a skill already conforms to agentskills.io (Claude / Codex / Windsurf / Triggerfish shape), what OpenClaw+ClawHub adds:

1. **Nothing mandatory in the file format** — `name` + `description` in `SKILL.md` is sufficient to publish [S5][S2].
2. **Declare every env var / binary** under `metadata.openclaw.requires.*` / `envVars` / `primaryEnv`, or the audit flags a metadata mismatch [S5].
3. **Accept MIT-0.** Strip any license block from `SKILL.md` [S5].
4. **Strip pricing/paywall metadata** [S5].
5. **Dereference symlinks** — they're dropped at publish [S5].
6. **Keep the bundle under 50 MB**, and expect only ~40 files beyond `SKILL.md` to be indexed for search [S5].
7. **Slug** must match `^[a-z0-9][a-z0-9-]*$`; `name` should equal the folder name, 1–64 chars [S5].
8. **A GitHub account past the age gate**, and a ClawHub owner handle whose scope matches [S9][S11].
9. Optionally add `metadata.openclaw.emoji` / `homepage` / `os` / `install` for a better catalog and macOS UI presence [S2][S5].
10. Optionally set `user-invocable` / `disable-model-invocation` for slash-command behavior — OpenClaw-only, ignored elsewhere [S2].

---

## Gaps and Ambiguities

- **Skill count on ClawHub is unresolved.** clawhub.ai homepage metadata read as "30 skills 12 plugins" (likely a featured/curated subset) while a third-party awesome-list claims 5,400+ from the official registry, and another aggregator claims 3,286 [S4][S13][S22]. Actual registry size: **UNVERIFIED**.
- **`--tags` and `--category` publish flags:** `--tags` appears in one docs page summary [S3] but not in the canonical CLI reference [S14]. No `--category` flag found anywhere. **UNVERIFIED.**
- **`os` value vocabulary conflicts between docs:** OpenClaw core docs say `darwin | linux | win32` [S2]; ClawHub skill-format says `["macos"], ["linux"]` [S5]. Which the validator accepts: **UNVERIFIED.**
- **`hidden` and `tool-name` frontmatter keys** appeared in a GitHub-rendered summary of `docs/tools/skills.md` [S7] but not in the raw canonical section [S2]. **UNVERIFIED.**
- **`alwaysInclude` vs `always`, `platforms` vs `os`:** one rendering used `alwaysInclude`/`platforms` [S7], canonical spec uses `always`/`os` [S5][S2]. Assume `always`/`os`; aliases **UNVERIFIED**.
- **Exact rate limits, per-account publish quotas, and the numeric GitHub account-age threshold** are not published [S11][S18]. **UNVERIFIED.**
- **No documented network-domain allowlist or explicit permissions declaration** for skills. Authority is inferred by the audit rather than declared. Whether a future permissions field exists: **UNVERIFIED.**
- **Whether ClawHub validates `name` against the parent directory at publish time** (vs merely recommending it) is **UNVERIFIED** — the spec says "should" and notes existing foreign names are "not silently rewritten" [S5].
- **`.clawhubignore` pattern syntax** (gitignore-compatible or not) is not specified [S5]. **UNVERIFIED.**
- Two docs hostnames (`docs.openclaw.ai`, `documentation.openclaw.ai`) serve overlapping ClawHub content; `docs.openclaw.ai` is the one named as the mirror target by the repo [S11], so it is treated as canonical here.

---

## Source Inventory

| ID | URL | Date accessed | Covers |
|---|---|---|---|
| S1 | https://github.com/openclaw/openclaw | 2026-07-31 | What OpenClaw is, README description, maintainer, MIT license, star count |
| S2 | https://raw.githubusercontent.com/openclaw/openclaw/main/docs/tools/skills.md | 2026-07-31 | Canonical skills doc: AgentSkills conformance, load order/paths, frontmatter keys, gating, install specs, symlink containment, private zip archive installs, watcher config |
| S3 | https://docs.openclaw.ai/clawhub | 2026-07-31 | ClawHub overview, hosted families, CLI commands, upload gate, telemetry, slug regex, earlier text-allowlist description |
| S4 | https://clawhub.ai/ | 2026-07-31 | Registry is live; homepage counts, categories, inline publish commands, signed manifests / moderated releases / GitHub import claims |
| S5 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/skill-format.md | 2026-07-31 | **Authoritative skill format**: required/optional files, frontmatter reference, metadata.openclaw table, install specs, file rules, 50MB limit, symlink exclusion, slug rules, MIT-0, no paid skills, GitHub importer restrictions |
| S6 | https://raw.githubusercontent.com/openclaw/clawhub/main/README.md | 2026-07-31 | ClawHub definition, capabilities, CLI flows, metadata aliases (clawdbot/clawdis), nix/config/cliHelp metadata, delete permissions, architecture, telemetry |
| S7 | https://github.com/openclaw/clawhub — earlier rendered fetch of openclaw/openclaw docs/tools/skills.md | 2026-07-31 | Secondary rendering; source of the unverified `hidden`, `tool-name`, `alwaysInclude`, `platforms` keys and installer preference order |
| S8 | https://raw.githubusercontent.com/openclaw/openclaw/main/docs/plugins/manifest.md | 2026-07-31 | `openclaw.plugin.json` requirement and schema; foreign bundle manifests (.claude-plugin/.codex-plugin/.cursor-plugin) |
| S9 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/publishing.md | 2026-07-31 | Publish flow, owner model, validation-then-scan sequence, GitHub Action workflow, plugin scope rules, icon field, trusted publishing, namespace claims |
| S10 | https://docs.openclaw.ai/tools/creating-skills | 2026-07-31 | Skill authoring guide, required fields, gating, `{baseDir}`, publish via `clawhub skill publish` |
| S11 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/README.md and .../docs/clawhub.md | 2026-07-31 | Docs index and mirroring to docs.openclaw.ai; upload gate wording |
| S12 | https://en.wikipedia.org/wiki/OpenClaw (+ CNBC, Forbes coverage surfaced in same search) | 2026-07-31 | Rename history Clawdbot → Moltbot → OpenClaw |
| S13 | https://github.com/VoltAgent/awesome-openclaw-skills | 2026-07-31 | Third-party claim of 5,400+ skills in the official registry |
| S14 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/cli.md | 2026-07-31 | **Canonical CLI reference**: skill publish flags, sync, scan/scan download, pin/unpin, install (zip download + extract), package publish, plugin compat fields |
| S15 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/quickstart.md | 2026-07-31 | Install/login/publish quickstart, `--slug`/`--name`/`--changelog`, auto-versioning, GitHub workflow |
| S16 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/security-audits.md | 2026-07-31 | Audit statuses, risk levels, findings severities, SkillSpector + VirusTotal + ClawScan, OWASP Agentic Skills Top 10 |
| S17 | https://docs.openclaw.ai/clawhub/moderation | 2026-07-31 | Reports, moderation holds, hidden/quarantined listings, bans, appeals |
| S18 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/acceptable-usage.md | 2026-07-31 | Prohibited categories, bulk low-effort publishing, metric gaming, enforcement actions |
| S19 | https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/ | 2026-07-31 | External security critique of the skills marketplace as supply-chain risk (title/abstract from search) |
| S20 | https://www.certik.com/blog/skill-scanning-is-not-a-security-boundary | 2026-07-31 | External critique that scanning is not a security boundary (title from search) |
| S21 | https://github.com/openclaw/agent-skills | 2026-07-31 | Canonical shared-skills repo: `skills/<name>/SKILL.md` layout, `install-skills` (symlink or copy), `validate-skills` (checks YAML frontmatter + name/description) |
| S22 | https://claw-hub.net/ | 2026-07-31 | Third-party aggregator claiming 3,286 skills (conflicting count) |
