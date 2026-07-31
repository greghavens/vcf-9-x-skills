# Finding a VCF PowerCLI cmdlet you do not already know

The cmdlet surface is too large to enumerate and too version-dependent to memorise: ~36 component
modules under `VCF.PowerCLI` `[DOC]` `[TL-S05]` `[TL-S07]`, a 9.1 changelog that reports **counts**
rather than names `[DOC]` `[TL-S09]`, and a per-product cmdlet index that was unavailable at research
time `[TL-gap14]`. So the working assumption for any cmdlet not on the short verified list in
`module-map.md` §6 is: **you do not know its name or its parameters, and you can find both in one
command.**

**Evidence tags.** `[DOC]` = traced to a fetched reference page. `[UNVERIFIED]` = not confirmed —
never present as established. `[PS-CORE]` = a stock PowerShell cmdlet (`Get-Command`, `Get-Help`,
`Get-Module`, `Get-Member`), unquestionably real but **not documented by Broadcom as the VCF
discovery route** — the VCF 9.1 PowerShell Basics page offers only `Get-Help about_CommonParameters`
`[DOC]` `[TL-S43b]`. Say "standard PowerShell" if you surface these as the documented way.

Prerequisites before any of this returns anything useful: PowerShell 7.x, `VCF.PowerCLI` installed and
imported, and for cmdlets that touch a product, a live session. See the SKILL's `## Prerequisites`
and `vcf-foundation` → `references/powercli-session.md`.

---

## Contents

- [1. Why noun-first](#1-why-noun-first)
- [2. The five commands](#2-the-five-commands)
- [3. Walkthrough — a plain-English goal to a confirmed cmdlet](#3-walkthrough--a-plain-english-goal-to-a-confirmed-cmdlet)
- [4. Walkthrough — the cold SDDC Manager surface](#4-walkthrough--the-cold-sddc-manager-surface)
- [5. Reading parameter sets](#5-reading-parameter-sets)
- [6. The confidence ladder](#6-the-confidence-ladder)
- [7. When discovery comes up empty](#7-when-discovery-comes-up-empty)
- [8. Discovering the version-dependent things](#8-discovering-the-version-dependent-things)
- [Source Index](#source-index)

---

## 1. Why noun-first

PowerShell names are `Verb-Noun`. In VCF PowerCLI the **module split is by product and the noun
prefix tracks the product** `[TL-discovery]` — so the noun is the highest-signal thing you know about
a cmdlet you have never seen:

| You want | Noun prefix | Module family |
|---|---|---|
| SDDC Manager | `Sddc*` | `VMware.Vcf.SddcManager` `[DOC]` `[TL-S05]` `[TL-S07]` |
| VCF SDK surfaces | `Vcf*` | `VMware.Sdk.Vcf.*` `[DOC]` `[TL-S05]` `[TL-S07]` |
| vSAN / storage | `Vsan*` | `VMware.VimAutomation.Storage` `[DOC]` `[TL-S18]` |
| NSX | `Nsx*` | `VMware.VimAutomation.Nsxt`, `VMware.Sdk.Nsx.Policy*` `[DOC]` `[TL-S18]` |
| vCenter / ESX core | `VI*`, plus bare nouns (`VM`, `VMHost`, `Datastore`) | `VMware.VimAutomation.Core` `[DOC]` `[TL-S19]` `[TL-S18]` |

Verb-first is the weaker search — dozens of modules export `Get-*` — but it is the right one for a
narrow class of questions, chiefly "what are all the ways to connect": `Get-Command -Verb Connect`.

`Get-Command -Noun Sddc*` is precisely how you would have found `Get-SddcTask` and the
`Remove-Sddc*` family cold `[DOC]` `[TL-S08]`.

---

## 2. The five commands

Everything in this file is built from these. All `[PS-CORE]`.

```powershell
# 1. What is installed, and at what version — decides which cmdlets can exist at all
Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version
Get-Module -ListAvailable VMware.*, VCF.*
Get-Module                                        # currently imported

# 2. What does a module export?
Get-Command -Module VMware.Vcf.SddcManager
Get-Command -Module VMware.VimAutomation.Nsxt

# 3. Noun-first / verb-first / wildcard search
Get-Command -Noun Sddc*
Get-Command -Verb Connect
Get-Command *Vsan*Capacity*

# 4. Confirm it is real, and read its parameters
Get-Help <cmdlet> -Full
Get-Help <cmdlet> -Examples
Get-Help <cmdlet> -Parameter <ParameterName>

# 5. Inspect what came back — PowerCLI returns rich typed objects, not text
<cmdlet> | Get-Member
<cmdlet> | Select-Object -First 1 | Format-List *
```

Two notes worth carrying:

- **`Get-Command` only sees installed modules.** A nil result means "not in this install", which is
  a version statement, not an existence statement. `Get-Module -ListAvailable` first.
- **`Get-Help -Full` is the verification step, not a nicety.** It is what turns "a cmdlet by this
  name resolved" into "I know its parameter set". Skipping it is how a script ships with
  `-SkipCertificateCheck` against a cmdlet that wanted `-IgnoreInvalidCertificate` `[DOC]` `[TL-S20]`.

---

## 3. Walkthrough — a plain-English goal to a confirmed cmdlet

**Goal:** *"I need to report on vSAN usable capacity across the fleet."*

**Step 0 — establish the module version.** It gates everything else.

```powershell
Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version
# -> 9.1.0.25380678   (or 9.0.0.24798382 — the answer differs)
```

**Step 1 — concept to noun.** "vSAN capacity" → noun contains `Vsan`. Cast wide first:

```powershell
Get-Command *Vsan*
```

**Step 2 — narrow.** Add the second concept word, keeping the noun leading:

```powershell
Get-Command -Noun Vsan*Capacity*
# -> Get-VsanEffectiveCapacity
```

**Step 3 — confirm it is real and read the parameter set.** *Do not skip this.*

```powershell
Get-Help Get-VsanEffectiveCapacity -Full
Get-Help Get-VsanEffectiveCapacity -Examples
```

`Get-VsanEffectiveCapacity` is named on the 9.1 What's New page `[DOC]` `[TL-S08]`. **Its parameters
are `[UNVERIFIED]`** — no fetched page carries them. `Get-Help` is the only route.

**Step 4 — pin the provenance.** Which module, which version, so the answer can carry a version claim:

```powershell
Get-Command Get-VsanEffectiveCapacity | Select-Object Name, Source, Version, Module
```

**Step 5 — inspect the objects before filtering on a property you assumed:**

```powershell
Get-VsanEffectiveCapacity <args> | Get-Member
```

**The 9.0 branch.** `Get-VsanEffectiveCapacity` is **9.1-only** `[DOC]` `[TL-S08]`. On
`{PCLI 9.0.0}` step 2 returns nothing and the honest answer is *"that cmdlet is 9.1-only; on your
module version, here is what `Get-Command *Vsan*` does return"* — followed by §7 if nothing fits.
Inventing a 9.0 equivalent is the failure this whole file exists to prevent.

---

## 4. Walkthrough — the cold SDDC Manager surface

**Goal:** *"What can I do against SDDC Manager from PowerShell?"* — with no cmdlet name in hand.

```powershell
# 1. Is the SDDC Manager module even present, and is it the high- or low-level one?
Get-Module -ListAvailable VMware.Vcf.SddcManager, VMware.Sdk.Vcf.SddcManager

# 2. The whole product surface, by noun prefix — the single highest-yield command here
Get-Command -Noun Sddc*

# 3. And by module, which also tells you which layer each cmdlet belongs to
Get-Command -Module VMware.Vcf.SddcManager     | Sort-Object Verb, Noun
Get-Command -Module VMware.Sdk.Vcf.SddcManager | Sort-Object Verb, Noun

# 4. Entry points
Get-Command -Verb Connect | Where-Object { $_.Source -like 'VMware.*' -or $_.Source -like 'VCF.*' }

# 5. Read before running
Get-Help Connect-VcfSddcManagerServer -Full
```

What research can tell you before you run any of it:

- `Connect-VcfSddcManagerServer` exists in `VMware.Sdk.Vcf.SddcManager`, **with `[DOC]` full syntax**
  `[TL-S20]` — see `vcf-foundation` → `references/powercli-session.md`.
- On `{PCLI 9.1.0}`, step 2 should surface at least `Get-SddcTask`, `Remove-SddcCluster`,
  `Remove-SddcDomain`, `Remove-SddcHost` `[DOC]` `[TL-S08]`.
- On `{PCLI 9.0.0}`, **no SDDC Manager cmdlet name was verified in research.** Step 2 is the only
  route. Anything you might "remember" here is a guess.
- The complete list is not published anywhere fetched `[TL-gap14]` — step 2 *is* the source of truth.

**Two things step 3 is really testing.** First, layering: the verified connect cmdlet is in the
low-level SDK module while the `*Sddc*` cmdlets are `[INFERRED]` to sit in the high-level module
(the changelog's "+4 new commands" for `VMware.Vcf.SddcManager` `[TL-S09]` matches the four named
cmdlets exactly `[TL-S08]`). **Whether the high-level cmdlets consume the SDK module's connection is
`[UNVERIFIED]`** — if a cmdlet reports no server connection, check whether it takes its own
`-Server`. Second, destructiveness: the `Remove-Sddc*` cmdlets remove a cluster, a workload domain, a
host. Enumerating them is safe; running one is not.

---

## 5. Reading parameter sets

`Get-Help -Full` prints one **SYNTAX** block per parameter set. That structure is the information —
it tells you which parameters are mutually exclusive and which combinations are legal, which no prose
summary reliably conveys.

```powershell
Get-Help Connect-VcfSddcManagerServer -Full

# Just one parameter's semantics, type and default
Get-Help Set-PowerCLIConfiguration -Parameter InvalidCertificateAction

# Machine-readable: types, mandatory-ness, position, pipeline binding
(Get-Command Connect-VcfSddcManagerServer).Parameters.Values |
  Select-Object Name, ParameterType, IsDynamic

# Does this cmdlet carry the 9.1 token parameters at all?
Get-Help <cmdlet> -Parameter VcfApiToken
```

What to look for, and why each matters here:

| Look for | Why |
|---|---|
| **Certificate flag name** | `Connect-VIServer` uses **`-Force`** `[DOC]` `[TL-S19]`; `Connect-VcfSddcManagerServer` uses **`-IgnoreInvalidCertificate`** `[DOC]` `[TL-S20]`. Same meta-module, different names. There is no rule — read it. |
| **Credential parameter type** | `Connect-VcfSddcManagerServer -Password` is a **`SecureString`** `[DOC]` `[TL-S20]`; `Connect-VIServer -Password` is a plain `String` `[DOC]` `[TL-S19]`. Passing the wrong type fails at bind time. |
| **`-Server` on non-connect cmdlets** | Determines whether a cmdlet uses the default-connection variables (`$DefaultVIServers` / `$DefaultCIServers` `[DOC]` `[TL-S04]`) or needs an explicit target. |
| **`SupportsShouldProcess`** | If present, `-WhatIf` and `-Confirm` work — the safest way to rehearse anything that writes. Presence per cmdlet is `[UNVERIFIED]`; check, do not assume. |
| **Token parameters** | `VcfOAuthSecurityContext` / `VcfApiToken` are `{PCLI 9.1.0}`-only `[DOC]` `[TL-S08]`, and **which cmdlets expose them is disputed between sources** — see `deltas.md`. `Get-Help -Parameter` settles it for the install in front of you. |

---

## 6. The confidence ladder

Rank evidence before you state a cmdlet. Say which rung you are on when it matters.

| Rung | Evidence | What you may claim |
|---|---|---|
| 1 | `Get-Help -Full` on the user's install | Name **and** parameters, for that install. Strongest available. |
| 2 | `Get-Command` on the user's install | The name exists there. Parameters still unknown. |
| 3 | Fetched Broadcom reference page `[DOC]` | Name and parameters as documented — but the reference site is unversioned "latest" `[TL-S18]`, so version-qualify it. |
| 4 | Named in release notes `[DOC]` `[TL-S08]` | The cmdlet **exists** in that version. Parameters `[UNVERIFIED]`. |
| 5 | Counted-not-named in the changelog `[TL-S09]` | That a module gained *n* commands. **No names.** Never synthesise one. |
| 6 | Pattern-plausible from naming conventions | Nothing. This is guessing. |

Rung 5 is the sharp edge in `{PCLI 9.1.0}`: `VMware.VimAutomation.Vpc` gained **33 commands**, none
named `[DOC]` `[TL-S09]`. Thirty-three real cmdlets exist that no fetched source names. The
temptation to write `New-VpcConnectivityPolicy` because it reads right is exactly the failure mode.

---

## 7. When discovery comes up empty

In order:

1. **Confirm you searched the installed set, not a guess.** `Get-Module -ListAvailable VMware.*, VCF.*`
   — a component module can be absent from a partial install `[DOC]` `[TL-S15]`.
2. **Loosen the pattern.** `Get-Command *<concept>*` with no `-Noun`. Then try the product's other
   vocabulary — `Domain` vs `WorkloadDomain`, `Host` vs `VMHost`.
3. **Try the low-level SDK module.** The high-level cmdlet may not exist while the generated SDK
   binding does: `Get-Command -Module VMware.Sdk.Vcf.SddcManager`, `-Module VMware.Sdk.Nsx.Policy`.
4. **Check the module version.** The cmdlet may be `{PCLI 9.1.0}`-only — `deltas.md`.
5. **Check the reference site**, version-qualifying the result:
   `https://developer.broadcom.com/powercli/<module>/` `[DOC]` `[TL-S18]`. It serves "latest".
6. **Switch modality.** Use `vcf-api-discovery` to find the REST operation instead. A confirmed
   endpoint plus `Invoke-RestMethod` beats an unconfirmed cmdlet, and is honest about what it is.
7. **Say you could not find it.** Name the searches you ran and hand over the command. That is a
   useful answer; a plausible cmdlet name is not.

---

## 8. Discovering the version-dependent things

```powershell
# Module version — gates everything
Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version

# Is this a 9.1 install? Two independent tells:
Get-Module -ListAvailable VMware.Vcf.Sso            # 9.1-only module      [DOC] [TL-S07]
Get-Module -ListAvailable VMware.PowerCLI.VCenter   # 9.0-only in the meta-module [DOC] [TL-S05]

# Current PowerCLI configuration (cert action, CEIP, timeouts)
Get-PowerCLIConfiguration
```

`Get-PowerCLIConfiguration` is **`[UNVERIFIED]`** — inferred as the read counterpart to
`Set-PowerCLIConfiguration` `[TL-S21]` `[TL-S13]`; its reference page was not retrieved `[TL-gap10]`.
Present it as "expected but unverified", not as fact.

The `VMware.PowerCLI.VCenter` probe is a genuinely useful diagnostic, but read the result carefully:
its absence from the `{PCLI 9.1.0}` dependency set is `[DOC]` `[TL-S07]` `[TL-S05]`, while whether it
still installs standalone is **unresolved** — see the contradiction recorded in `deltas.md`. Absence
from the meta-module is not the same as absence from the machine.

---

## Source Index

All sources accessed **2026-07-31**.
`TECHDOCS` = `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.

### `TL-*` — `research/tooling-powercli-vks-sdk.md`

| Ref | URL / location |
|---|---|
| TL-S04 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-vsphere-powercli-specific-concepts.html` |
| TL-S05 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382` |
| TL-S07 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.1.0.25380678` |
| TL-S08 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S09 | `TECHDOCS/9-1/release-notes/.../whats-new-vcf-cli-api-sdk/vcf-powercli-changelog.html` |
| TL-S13 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/configuring-vmware-vsphere-powercli.html` |
| TL-S15 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli/install-powercli.html` |
| TL-S18 | `https://developer.broadcom.com/powercli/all-powercli-modules` |
| TL-S19 | `https://developer.broadcom.com/powercli/latest/vmware.vimautomation.core/commands/connect-viserver` |
| TL-S20 | `https://developer.broadcom.com/powercli/latest/vmware.sdk.vcf.sddcmanager/commands/connect-vcfsddcmanagerserver` |
| TL-S21 | `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/power-cli/latest/powercli/configuring-vmware-vsphere-powercli/configuring-powercli-invalid-server-certificate-actions/configure-invalid-server-certificate-action.html` |
| TL-S43b | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/microsoft-powershell-basics.html` |
| TL-discovery | dossier `## Discovery/lookup patterns` → PowerShell/PowerCLI; noun-prefix rationale |
| TL-gap10, TL-gap14 | dossier `## Gaps and Ambiguities`, items 10 and 14 |

---

*Built from documentation captured 2026-07-31. Not validated against a live VCF environment or a live
PowerCLI installation. Discovery commands here are read-only; cmdlets they surface may not be —
`Remove-SddcCluster`, `Remove-SddcDomain` and `Remove-SddcHost` are production-affecting. Verify
before executing.*
