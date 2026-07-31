---
name: powercli-vcf
description: PowerCLI as the automation modality for VMware Cloud Foundation 9.0 and 9.1 — which of the ~36 modules under the VCF.PowerCLI meta-module covers which product, how to find a cmdlet you do not already know, scripting patterns, and the traps. Use this when a task should be done in PowerShell rather than REST, when someone asks "which cmdlet does X", when a script breaks after a PowerCLI upgrade, when a cmdlet name is not already confirmed, and before you state any cmdlet or parameter name in an answer. The module is VCF.PowerCLI, not VMware.PowerCLI, and the certificate flags differ between cmdlets in the same meta-module. Routing against its sibling — vcf-api-discovery finds REST operations in the published OpenAPI specs; this skill finds and uses cmdlets. Module install and Connect-* session setup live in vcf-foundation's powercli-session reference; this skill links there rather than restating it.
compatibility: Requires PowerShell 7.x and the VCF.PowerCLI module for any live discovery or execution. The module map, discovery patterns and delta tables are usable offline; confirming a cmdlet name requires an installed module or the developer.broadcom.com cmdlet reference.
metadata:
  {
    "openclaw": {
      "requires": {}
    }
  }
---

# PowerCLI for VCF: finding cmdlets instead of guessing them

The VCF PowerCLI cmdlet surface is too large to enumerate and too version-dependent to
memorise. `VCF.PowerCLI` is a meta-module over roughly **36 component modules**, the 9.1
changelog adds cmdlets in counts rather than names, and Broadcom's own per-product cmdlet
index was unavailable during research.

A guessed REST path 404s immediately. A guessed cmdlet name fails at runtime, inside
someone's automation, usually after the script has already changed something. So the rule
is the one `vcf-api-discovery` enforces for endpoints: **if you are about to state a
cmdlet or parameter you have not confirmed for the module version in question, confirm it
first.** The discovery patterns below make that cheap.

> **Built from documentation captured 2026-07-31, not validated live.** Every cmdlet and
> parameter here traces to a fetched reference page, tagged `[DOC]`, or is marked
> `[UNVERIFIED]`. Nothing has been run against a VCF deployment or a live PowerCLI
> install. **PowerCLI cmdlets that modify infrastructure are production-affecting** —
> `Remove-SddcCluster`, `Remove-SddcDomain` and `Remove-SddcHost` remove real
> infrastructure. Verify against Broadcom's docs for the exact build before executing
> anything that writes.

## Prerequisites

All five, before you write a single cmdlet.

| # | Requirement | Detail |
|---|---|---|
| 1 | **PowerShell 7.x** | Windows PowerShell **5.1 is deprecated as of VCF PowerCLI 9.0** `[DOC]` `[TL-S17]`. If the user reports 5.1, say so before answering the rest. |
| 2 | **`VCF.PowerCLI` installed** | `Install-Module VCF.PowerCLI -Scope CurrentUser` `[DOC]` `[TL-S15]`. **Not `VMware.PowerCLI`** — that is the pre-9.x name `[DOC]` `[TL-S12]`. |
| 3 | **A session established** | `Connect-VIServer` for vCenter/ESX `[DOC]` `[TL-S19]`; `Connect-VcfSddcManagerServer` for SDDC Manager `[DOC]` `[TL-S20]`. Full syntax, parameters and the auth flows behind them: **`vcf-foundation` → `references/powercli-session.md`**. This skill does not restate them. |
| 4 | **Certificate handling decided** | `Set-PowerCLIConfiguration -InvalidCertificateAction` takes `Unset`/`Fail`/`Ignore`/`Warn`/`Prompt`, but **only `Fail` and `Ignore` work on Linux and macOS** `[DOC]` `[TL-S21]`. Broadcom's documented remedy is replacing certificates, not disabling verification. |
| 5 | **The right role on the target product** | Cmdlets carry no privileges of their own — they inherit whatever the connected account has. A read cmdlet needs a viewer role; anything that writes needs the product's administrator role. Role models differ per product and between 9.0 and 9.1 — see `vcf-foundation`. |

## The traps

| Correct | Wrong, and common |
|---|---|
| The module is **`VCF.PowerCLI`** `[DOC]` `[TL-S12]` `[TL-S05]` | `VMware.PowerCLI` — pre-9.x name |
| `Connect-VcfSddcManagerServer` takes **`-IgnoreInvalidCertificate`** `[DOC]` `[TL-S20]` | `-Force`, or `-SkipCertificateCheck` |
| `Connect-VIServer` takes **`-Force`** `[DOC]` `[TL-S19]` | `-IgnoreInvalidCertificate` |
| Token parameters (`VcfOAuthSecurityContext`, `VcfApiToken`) are **9.1-only** `[DOC]` `[TL-S08]` | Offering them on `{PCLI 9.0.0}` |
| SDKs are **Java and Python only** `[DOC]` `[TL-S12]` `[TL-S34]` | Suggesting a first-party Go or .NET VCF SDK — neither exists |

Rows two and three are one trap from both sides: **two cmdlets in the same meta-module use
different names for the same idea.** There is no rule to infer from — read the parameter set.

## Discovery is the point of this skill

The module split is **by product**, and the noun prefix tracks the product — `*-Sddc*`
(SDDC Manager), `*-Vsan*`, `*-Nsx*`, `*-VI*` (core vSphere), `*-Vcf*` (the VCF SDK
modules). That makes **noun-first search** the highest-signal move available:

```powershell
Get-Command -Noun Sddc*          # the whole SDDC Manager surface, cold
Get-Command -Module VMware.Vcf.SddcManager
Get-Command -Verb Connect        # every Connect-*Server entry point
Get-Help <cmdlet> -Full          # syntax, parameter sets, examples
```

`Get-Command -Noun Sddc*` is exactly how you would have found `Get-SddcTask` without
knowing it existed `[DOC]` `[TL-S08]`. Full patterns and the confidence ladder:
**`references/discovery.md`**. These are standard PowerShell, not quoted from Broadcom's
docs — the VCF 9.1 PowerShell Basics page documents only `Get-Help about_CommonParameters`
`[DOC]` `[TL-S43b]`. Say so if you surface them as "the documented way".

## Worked example 1 — connect to SDDC Manager and enumerate

`{PCLI 9.1.0}`. Read-only; run it before anything that writes.

```powershell
# 1. Confirm the module version you are actually on — it decides which cmdlets exist
Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version

# 2. Connect.  -IgnoreInvalidCertificate is a lab expedient, not a production posture.
Connect-VcfSddcManagerServer -Server sddc-manager.example.com `
  -User 'administrator@vsphere.local' -Password $secure -IgnoreInvalidCertificate

# 3. Enumerate.  Get-SddcTask is named in the 9.1 What's New page  [DOC] [TL-S08]
Get-SddcTask | Select-Object -First 10 | Format-Table -AutoSize

# 4. Inspect the object before you filter on a property you assumed
Get-SddcTask | Select-Object -First 1 | Get-Member
```

Step 2's syntax and `-Password` being a `SecureString` are documented `[DOC]` `[TL-S20]`.
`Get-SddcTask` is documented as existing `[DOC]` `[TL-S08]`; **its parameters are
`[UNVERIFIED]`** — the changelog gives counts, not signatures `[TL-gap14]`. Run
`Get-Help Get-SddcTask -Full` before promising a filter. **On `{PCLI 9.0.0}` this does not
port**: `Get-SddcTask` is 9.1-only and **no 9.0 SDDC Manager read cmdlet name was verified
in research** — discover it with `Get-Command -Noun Sddc*`, do not substitute a plausible one.

One open question: `Connect-VcfSddcManagerServer` lives in the low-level SDK module
`VMware.Sdk.Vcf.SddcManager` `[DOC]` `[TL-S20]`, while `Get-SddcTask` most likely sits in
the high-level `VMware.Vcf.SddcManager` (inferred — that module's "+4 new commands"
matches the four named `*Sddc*` cmdlets exactly `[TL-S09]` `[TL-S08]`). **Whether the
high-level cmdlets consume the SDK module's connection context is `[UNVERIFIED]`.** If
step 3 reports no server connection, that is why — check
`Get-Command Get-SddcTask | Select-Object Source`.

## Worked example 2 — from a plain-English goal to a cmdlet

*"I need to report on vSAN usable capacity across the fleet."*

```powershell
Get-Command *Vsan*                          # 1. concept → wildcard
Get-Command -Noun Vsan*Capacity*            # 2. narrow on the noun
Get-Help Get-VsanEffectiveCapacity -Full    # 3. confirm it is real, read the parameter sets
Get-Command Get-VsanEffectiveCapacity | Select-Object Source, Version   # 4. which module, which version
```

Step 3 is the one people skip, and the one that catches a 9.1-only cmdlet on a 9.0
install. `Get-VsanEffectiveCapacity` is **9.1-only** `[DOC]` `[TL-S08]`; on `{PCLI 9.0.0}`
step 1 returns nothing and the honest answer is "not in your module version". Long form,
including what to do when the goal maps to no cmdlet at all: `references/discovery.md`.

## Which PowerCLI version pairs with which VCF version

| VCF | `VCF.PowerCLI` | Published | Evidence grade |
|---|---|---|---|
| 9.0 | **9.0.0.24798382** | 2025-06-17 | version and date `[DOC]` `[TL-S05]` `[TL-S06]`; **pairing is inference** from the shared build-date family (VCF 9.0 SDKs, build 24798170) |
| 9.1 | **9.1.0.25380678** | 2026-05-12 | version and date `[DOC]` `[TL-S06]` `[TL-S07]`; **pairing is inference** from the shared 2026-05-12 date with Supervisor 9.1.0.0 |

Only these two versions exist in the Gallery version history `[DOC]` `[TL-S06]`, and
**the pairing is inference, not a documented binding** — the compatibility-matrix page
carries no product-version table, deferring to the Broadcom Product Interoperability
Matrix at `https://interopmatrix.broadcom.com/Interoperability` `[DOC]` `[TL-S17]`. A 9.1
module can be pointed at a 9.0 estate and nothing stops you. **Ask which module version is
installed rather than deriving it from the VCF version** — hence references organised by
module version.

## Reference files

| You need | Read |
|---|---|
| Which module covers which product, per module version | `references/module-map.md` |
| How to find a cmdlet you do not know | `references/discovery.md` |
| What changed between `{PCLI 9.0.0}` and `{PCLI 9.1.0}` | `references/deltas.md` |
| Install, `Connect-*` syntax, certificate config, auth | `vcf-foundation` → `references/powercli-session.md` |

## When PowerCLI is the wrong modality, and what research could not verify

Reach elsewhere when: **no cmdlet exists or you cannot find one** — `vcf-api-discovery`
finds the REST operation in the published specs, and a confirmed endpoint beats an
unconfirmed cmdlet; **the client is not PowerShell** — VCF SDKs are **Java**
(`com.vmware.sdk:vcf-sdk-bom`, Maven) and **Python** (`pip install vcf-sdk`) `[DOC]`
`[TL-S37]` `[TL-S38]`, and **there is no first-party Go or .NET VCF SDK** `[DOC]`
`[TL-S12]` `[TL-S34]`, so generate bindings from the specs; or **the target is Supervisor
/ VKS**, which is `kubectl` and the `vcf` CLI, notwithstanding
`VMware.VimAutomation.WorkloadManagement` `[DOC]` `[TL-S18]`.

Not verified in research: `Connect-NsxtServer` and `Connect-CisServer` parameter sets,
which cmdlets carry `VcfApiToken`, the full SDDC Manager cmdlet index, and what happened
to `VMware.PowerCLI.VCenter` (`references/deltas.md`). When you hit one, say the docs do
not publish it and hand over the discovery command. "Run
`Get-Command -Module VMware.VimAutomation.Nsxt` and tell me what you see" beats a
confident cmdlet name that does not exist.

**Source refs.** `[TL-*]` and `[FA-*]` resolve in each reference file's Source Index, and
ultimately to `research/tooling-powercli-vks-sdk.md` and `research/foundation-auth-identity.md`.
Three used only here: `TL-S34` = the 9.1 programming-language-support page (Java, Python,
OpenAPI 3.0.1, SOAP); `TL-S37` = `developer.broadcom.com/vcf-python-sdk`; `TL-S38` =
`developer.broadcom.com/vcf-java-sdk`. All accessed 2026-07-31.

## Shaping your answer

### Answer the question that was asked, at the length it deserves

"Give me the exact API calls" means: give the calls. A numbered sequence of requests with
the payloads, and the two or three things that will actually bite. Not a runbook, not a
failure-mode table, not every caveat the reference file carries.

The reference material exists so your answer is *correct*, not so your answer is *long*.
Most of what you read should never appear in the reply. A useful test before sending:
would a VMware engineer who knows their environment skim this and find the command, or
would they have to hunt for it?

### Lead with the thing they asked for

Put the calls, the script, or the direct answer first. Context, prerequisites and
caveats come after, and only the ones that bear on this specific task.

If a prerequisite would actually cause the call to fail — the group doesn't exist yet,
the token type is wrong, the version gate isn't met — that belongs up top, because it
changes what they do next. A prerequisite that is merely true does not.

### Caveats: fewer, and where they matter

Every skill carries a documentation-not-live-validated caveat and a
destructive-operations warning. State them once, briefly, and place them where they bear
on the task rather than repeating them per section.

For a read-only query, one line is enough. For something that changes a production
firewall or starts an upgrade, say more — that is where the warning earns its space.
Uniform hedging on everything trains the reader to skip all of it, including the one that
mattered.

### Version labelling stays, and stays short

Say which version the answer applies to. Once, clearly, near the top. You do not need to
re-tag every line — the tags in the reference files are for you, not for the reply.

When evidence quality genuinely differs — a 9.1 endpoint confirmed in the spec versus a
9.0 endpoint sourced only from prose — say so in one sentence at the point it matters. A
user writing a change record needs that. A user prototyping does not need it five times.

### Length calibration

| They asked for | Give them |
|---|---|
| "the exact API calls" | The call sequence with payloads. Prereqs that would break it. Nothing else. |
| "write me a script" | The script, runnable. A short note on what to set. |
| "how do I find X" | The lookup route, and the answer if you found it. |
| "walk me through the upgrade" | The ordered steps with gates — this one legitimately runs long. |
| "is X true?" | Yes or no, then why. Two paragraphs, not ten. |
| A question with a false premise | Correct the premise first, briefly, then answer what they meant. |

When in doubt, answer short and offer the depth: "there's more on rollback and drafts if
you want it" costs one line and lets them pull rather than being pushed.
