# VCF PowerCLI — module map, by module version

Which module carries which product's cmdlets, per `VCF.PowerCLI` version.

**Organized by `VCF.PowerCLI` module version (`{PCLI 9.0.0}` / `{PCLI 9.1.0}`), not by VCF release**
`[TL-preamble]`. `{both}` = holds for both module versions. The module version, not the VCF version,
decides which cmdlets exist — see [§1](#1-versions-and-the-vcf-pairing) for the pairing and its
evidence grade.

**Evidence tags.** `[DOC]` = traced to a fetched reference page (source ref follows).
`[UNVERIFIED]` = research could not retrieve confirmation — **never present these as established**.
`[INFERRED]` = a defensible deduction from two `[DOC]` facts, labeled as deduction, not fact.

For install, `Connect-*` syntax, certificate configuration and auth flows, see
**`vcf-foundation` → `references/powercli-session.md`**. This file does not restate them.

---

## Contents

- [1. Versions and the VCF pairing](#1-versions-and-the-vcf-pairing)
- [2. Product → module map](#2-product--module-map)
- [3. Noun prefix → product](#3-noun-prefix--product)
- [4. The full dependency set](#4-the-full-dependency-set)
- [5. High-level vs low-level SDK modules](#5-high-level-vs-low-level-sdk-modules)
- [6. Named cmdlets, by module version](#6-named-cmdlets-by-module-version)
- [7. What this map cannot tell you](#7-what-this-map-cannot-tell-you)
- [Source Index](#source-index)

---

## 1. Versions and the VCF pairing

| `VCF.PowerCLI` | Published | Component modules at | Typical VCF pairing |
|---|---|---|---|
| **9.0.0.24798382** | 2025-06-17 `[DOC]` `[TL-S05]` `[TL-S06]` | `13.4.0.24798382`; `VMware.Vim` `9.0.0.24798382`; `VMware.VimAutomation.StorageUtility` `1.6.1` `[DOC]` `[TL-S05]` | VCF 9.0 — `[INFERRED]` |
| **9.1.0.25380678** | 2026-05-12 `[DOC]` `[TL-S06]` `[TL-S07]` | `13.5.0.25380678`; `VMware.Vim` `9.1.0.25380678`; `StorageUtility` still `1.6.1` `[DOC]` `[TL-S07]` | VCF 9.1 — `[INFERRED]` |

Only these two versions appear in the Gallery version history `[DOC]` `[TL-S06]`.

**The pairing is `[INFERRED]`, and this matters.** The 9.0 module shares a build-date family with the
VCF 9.0 SDKs (build 24798170, same 2025-06-17 date) `[TL-S05]` `[TL-S12]`, and the 9.1 module shares
its 2026-05-12 release date with vSphere Supervisor 9.1.0.0 `[TL-S06]` `[TL-S07]` `[TL-S22]`. That is
a date correlation, not a documented binding. **The compatibility-matrix page contains no
product-version table at all** — it defers to the Broadcom Product Interoperability Matrix at
`https://interopmatrix.broadcom.com/Interoperability` for VCF PowerCLI ↔ vCenter/ESX/vSAN/Live Site
Recovery pairings `[DOC]` `[TL-S17]`.

Practical consequence: nothing prevents a `{PCLI 9.1.0}` workstation from managing a VCF 9.0 estate,
or the reverse. **Establish the installed module version directly** rather than deriving it:

```powershell
Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version
```
*(Standard PowerShell — the VCF 9.1 PowerShell Basics page documents only
`Get-Help about_CommonParameters` `[DOC]` `[TL-S43b]`.)*

### Module identity

The module is **`VCF.PowerCLI`**, not `VMware.PowerCLI` `[DOC]` `[TL-S12]` `[TL-S05]`:

> *"VCF PowerCLI 9.0 (Build 24798382) represents a major rebranding from VMware.PowerCLI. The module
> is now called **VCF.PowerCLI**, though backward compatibility is maintained."* `[TL-S12]`

`[UNVERIFIED]` — the current version and status of the legacy `VMware.PowerCLI` package on the
Gallery, and whether it simply aliases `VCF.PowerCLI`. Backward compatibility *"is maintained"*
`[TL-S12]`, but the legacy package page was not fetched `[TL-gap12]`.

---

## 2. Product → module map

`{both}` unless marked. This is the table to consult first when the question is "which module do I
even look in".

| Product / surface | Module | Evidence |
|---|---|---|
| vCenter / ESX core inventory | `VMware.VimAutomation.Core` | `[DOC]` `[TL-S19]` `[TL-S18]` |
| vSphere Automation (vAPI), low-level | `VMware.Sdk.vSphere` | `[DOC]` `[TL-S05]` `[TL-S07]` |
| **SDDC Manager (high-level)** | `VMware.Vcf.SddcManager` | `[DOC]` `[TL-S05]` `[TL-S07]` |
| **SDDC Manager (low-level SDK)** | `VMware.Sdk.Vcf.SddcManager` | `[DOC]` `[TL-S20]` |
| VCF Installer | `VMware.Sdk.Vcf.Installer` | `[DOC]` `[TL-S05]` `[TL-S07]` |
| VCF Cloud Builder | `VMware.Sdk.Vcf.CloudBuilder` | `[DOC]` `[TL-S05]` `[TL-S07]` |
| VCF Operations | `VMware.Sdk.Vcf.Ops`, `VMware.VimAutomation.vROps` | `[DOC]` `[TL-S05]` `[TL-S07]` |
| NSX (high-level) | `VMware.VimAutomation.Nsxt` | `[DOC]` `[TL-S18]` |
| NSX Policy API (generated) | `VMware.Sdk.Nsx.Policy` (+ `.Infra`, `.GlobalInfra`, `.Initialize`) | `[DOC]` `[TL-S05]` `[TL-S07]` |
| vSAN / storage | `VMware.VimAutomation.Storage` | `[DOC]` `[TL-S18]` |
| Supervisor / Workload Management | `VMware.VimAutomation.WorkloadManagement` | `[DOC]` `[TL-S18]` |
| VPC networking | `VMware.VimAutomation.Vpc` | `[DOC]` `[TL-S05]` `[TL-S07]` |
| SSO — **`{PCLI 9.1.0}` only** | `VMware.Vcf.Sso` | `[DOC]` `[TL-S07]` `[TL-S09]` |
| vCenter (grouping module) — **`{PCLI 9.0.0}` only** | `VMware.PowerCLI.VCenter` | `[DOC]` `[TL-S05]`; absent from 9.1 `[TL-S07]` — see `deltas.md` |

Cmdlet reference root: `https://developer.broadcom.com/powercli/all-powercli-modules` `[DOC]`
`[TL-S18]`. Per-module pages follow
`https://developer.broadcom.com/powercli/latest/<module-name-lowercased>/`, e.g.
`.../vmware.vimautomation.core/`, `.../vmware.vimautomation.nsxt/` `[DOC]` `[TL-S18]`.

> Note the reference site serves **latest**, not a version-pinned view. A cmdlet listed there is not
> automatically present in `{PCLI 9.0.0}`. Confirm against the installed module.

---

## 3. Noun prefix → product

The module split is by product, and the **noun prefix tracks the product**. This is what makes
noun-first discovery work (see `discovery.md`).

| Noun prefix | Product surface | Example |
|---|---|---|
| `*-Sddc*` | SDDC Manager | `Get-SddcTask` `[DOC]` `[TL-S08]` |
| `*-Vcf*` | VCF SDK modules (SDDC Manager SDK, Installer, Cloud Builder, Ops) | `Connect-VcfSddcManagerServer` `[DOC]` `[TL-S20]` |
| `*-Vsan*` | vSAN / storage | `Get-VsanEffectiveCapacity` `[DOC]` `[TL-S08]`, 9.1-only |
| `*-Nsx*` | NSX | `Connect-NsxtServer` `[UNVERIFIED]` `[TL-gap11]` |
| `*-VI*` | core vSphere (vCenter/ESX) | `Connect-VIServer` `[DOC]` `[TL-S19]` |
| `*-Cis*` | vSphere Automation / CIS session layer | `Connect-CisServer` `[UNVERIFIED]` `[TL-gap11]` |

The prefix mapping itself is a research observation `[TL-discovery]`, corroborated by the module
inventory `[TL-S05]` `[TL-S07]` — treat it as a search heuristic, not a naming guarantee.

---

## 4. The full dependency set

`VCF.PowerCLI` is a **meta-module**. It exports nothing itself; its dependencies carry the cmdlets.

**`{PCLI 9.0.0}` — 36 dependencies** `[DOC]` `[TL-S05]`, all at `13.4.0.24798382` except where noted:

`VMware.CloudServices` · `VMware.DeployAutomation` · `VMware.ImageBuilder` · `VMware.OpenAPI` (≥) ·
**`VMware.PowerCLI.VCenter`** · `VMware.Sdk.Nsx.Policy` · `VMware.Sdk.Nsx.Policy.GlobalInfra` ·
`VMware.Sdk.Nsx.Policy.Infra` · `VMware.Sdk.Nsx.Policy.Initialize` · `VMware.Sdk.Srm` ·
`VMware.Sdk.Vcf.CloudBuilder` · `VMware.Sdk.Vcf.Installer` · `VMware.Sdk.Vcf.Ops` ·
`VMware.Sdk.Vcf.SddcManager` · `VMware.Sdk.Vr` · `VMware.Sdk.vSphere` · `VMware.Vcf.SddcManager` ·
`VMware.Vim` (`9.0.0.24798382`) · `VMware.VimAutomation.Cis.Core` · `.Cloud` · `.Common` · `.Core` ·
`.Hcx` · `.License` · `.Nsxt` · `.Sdk` · `.Security` · `.Srm` · `.Storage` ·
`VMware.VimAutomation.StorageUtility` (`1.6.1`) · `.Vds` · `.Vmc` · `.Vpc` · `.vROps` ·
`.WorkloadManagement` · `VMware.VumAutomation`

**`{PCLI 9.1.0}`** — the same set at `13.5.0.25380678`, **with exactly two deltas** `[DOC]`
`[TL-S07]`:

- **Added: `VMware.Vcf.Sso`** — confirmed present in 9.1, confirmed absent in 9.0 `[TL-S07]` `[TL-S05]`
- **Removed: `VMware.PowerCLI.VCenter`** — confirmed absent in 9.1, confirmed present in 9.0
  `[TL-S07]` `[TL-S05]`

Both were verified by pointed yes/no interrogation of each Gallery page, because a first-pass
narrative summary of the 9.1 page wrongly asserted "no module additions or removals" `[TL-gap2]`.
The removal sits oddly against the changelog's "0 deleted commands" — **see `deltas.md` §
the changelog contradiction. It is recorded, not resolved.**

---

## 5. High-level vs low-level SDK modules

Several products appear twice in §2, and choosing wrong is a common source of "the cmdlet exists but
does nothing".

| Layer | Naming | What it is |
|---|---|---|
| High-level | `VMware.Vcf.<Product>`, `VMware.VimAutomation.<Area>` | Idiomatic PowerShell cmdlets returning rich typed objects |
| Low-level SDK | `VMware.Sdk.Vcf.<Product>`, `VMware.Sdk.Nsx.Policy*`, `VMware.Sdk.vSphere` | Generated bindings mapping close to the REST surface |

SDDC Manager is the clearest case: **the only verified connection cmdlet,
`Connect-VcfSddcManagerServer`, is in the low-level `VMware.Sdk.Vcf.SddcManager`** `[DOC]` `[TL-S20]`,
while the high-level cmdlets (`Get-SddcTask`, `Remove-SddcCluster`, `Remove-SddcDomain`,
`Remove-SddcHost`) sit in `VMware.Vcf.SddcManager` — `[INFERRED]`, because the changelog's **+4 new
commands for `VMware.Vcf.SddcManager`** `[TL-S09]` matches those four named cmdlets exactly
`[TL-S08]`.

**`[UNVERIFIED]` — whether the high-level cmdlets consume the SDK module's connection context.** No
fetched page states it. Resolve at runtime:

```powershell
Get-Command Get-SddcTask | Select-Object Name, Source, Version
Get-Help Get-SddcTask -Full        # look for a -Server parameter of its own
```

Generated SDK modules also tend toward a different call shape (create-request-object, invoke) than
idiomatic cmdlets. Nothing fetched documents that for these modules, so **read `Get-Help -Full`
rather than assuming either style**.

---

## 6. Named cmdlets, by module version

Everything below is confirmed to **exist**. **Parameter sets for all of them except
`Connect-VIServer` and `Connect-VcfSddcManagerServer` are `[UNVERIFIED]`** — the What's New page
names cmdlets, the changelog gives counts, and neither gives signatures `[TL-S08]` `[TL-S09]`.

### `{both}`

| Cmdlet | Module | Evidence |
|---|---|---|
| `Connect-VIServer` | `VMware.VimAutomation.Core` | `[DOC]` `[TL-S19]` — full syntax in `vcf-foundation` |
| `Connect-VcfSddcManagerServer` | `VMware.Sdk.Vcf.SddcManager` | `[DOC]` `[TL-S20]` — full syntax in `vcf-foundation` |
| `Set-PowerCLIConfiguration` | PowerCLI configuration | `[DOC]` `[TL-S21]` `[TL-S13]` |
| `Install-Module` / `Import-Module` (PowerShellGet) | — | `[DOC]` `[TL-S15]` |
| `Get-PowerCLIConfiguration` | PowerCLI configuration | **`[UNVERIFIED]`** — inferred read counterpart to `Set-PowerCLIConfiguration`; reference page not retrieved `[TL-gap10]` |
| `Connect-NsxtServer` | `VMware.VimAutomation.Nsxt` | **`[UNVERIFIED]`** — module confirmed `[TL-S18]`, cmdlet page not retrieved `[TL-gap11]` |
| `Connect-CisServer` | `VMware.VimAutomation.Cis.Core` | **`[UNVERIFIED]`** — implied by `$DefaultCIServers` `[TL-S04]`, cmdlet page not retrieved `[TL-gap11]` |

`$DefaultVIServers` and `$DefaultCIServers` hold default server connections; cmdlets run against
connected systems *"if no target servers can be determined from the provided parameters"* `[DOC]`
`[TL-S04]`.

### `{PCLI 9.1.0}` only

| Cmdlet | Likely module | Evidence |
|---|---|---|
| `Get-SddcTask` — task reporting | `VMware.Vcf.SddcManager` `[INFERRED]` | exists `[DOC]` `[TL-S08]`; parameters `[UNVERIFIED]` |
| `Remove-SddcCluster` — **destructive** | `VMware.Vcf.SddcManager` `[INFERRED]` | exists `[DOC]` `[TL-S08]`; parameters `[UNVERIFIED]` |
| `Remove-SddcDomain` — **destructive** | `VMware.Vcf.SddcManager` `[INFERRED]` | exists `[DOC]` `[TL-S08]`; parameters `[UNVERIFIED]` |
| `Remove-SddcHost` — **destructive** | `VMware.Vcf.SddcManager` `[INFERRED]` | exists `[DOC]` `[TL-S08]`; parameters `[UNVERIFIED]` |
| `Get-VsanEffectiveCapacity` — vSAN capacity metrics | `VMware.VimAutomation.Storage` `[INFERRED]` | exists `[DOC]` `[TL-S08]`; parameters `[UNVERIFIED]` |

> The three `Remove-Sddc*` cmdlets remove real infrastructure — a cluster, a workload domain, a host.
> Never emit one without confirming the parameter set against the target install first, and never as
> part of a "here's how you'd do it" illustration.

`{PCLI 9.1.0}` also adds cmdlets in these areas, **named nowhere in the fetched sources** `[TL-S08]`
— NVMe-over-TCP for VMkernel adapters, remote datastore management, Transit Gateway management, VPC
connectivity policies (community/private/promiscuous), DHCP and IP Block management, external IP
assignment, CPU topology ("Assigned at PowerOn"), Active Directory proxy integration. **Do not invent
names for these.** The changelog counts are in `deltas.md`; the route to real names is
`Get-Command -Module <module>` against a 9.1 install.

---

## 7. What this map cannot tell you

| Question | Why not | Route |
|---|---|---|
| The full cmdlet list for a module | Never published in a fetched source; `developer.broadcom.com/powercli/latest/products/vcfsddcmanager/` returned *"PowerCLI Details Page is temporarily unavailable"* `[TL-gap14]` | `Get-Command -Module <module>` |
| Whether a cmdlet exists in `{PCLI 9.0.0}` specifically | The reference site is unversioned "latest" `[TL-S18]` | Run `Get-Command` on a 9.0 install |
| Parameter sets for anything beyond the two verified `Connect-*` cmdlets | Not published `[TL-S08]` `[TL-S09]` | `Get-Help <cmdlet> -Full` |
| Which cmdlets expose `VcfApiToken` | Sources conflict — see `deltas.md` | `Get-Help <cmdlet> -Parameter VcfApiToken` |

`discovery.md` turns each of these into a concrete command sequence.

---

## Source Index

All sources accessed **2026-07-31**.
`TECHDOCS` = `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.

### `TL-*` — `research/tooling-powercli-vks-sdk.md`

| Ref | URL / location |
|---|---|
| TL-S04 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-vsphere-powercli-specific-concepts.html` |
| TL-S05 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382` |
| TL-S06 | `https://www.powershellgallery.com/packages/VCF.PowerCLI` |
| TL-S07 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.1.0.25380678` |
| TL-S08 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S09 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-powercli-changelog.html` |
| TL-S12 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S13 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/configuring-vmware-vsphere-powercli.html` |
| TL-S15 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli/install-powercli.html` |
| TL-S17 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-powercli-compatibility-matrix.html` |
| TL-S18 | `https://developer.broadcom.com/powercli/all-powercli-modules` |
| TL-S19 | `https://developer.broadcom.com/powercli/latest/vmware.vimautomation.core/commands/connect-viserver` |
| TL-S20 | `https://developer.broadcom.com/powercli/latest/vmware.sdk.vcf.sddcmanager/commands/connect-vcfsddcmanagerserver` |
| TL-S21 | `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/power-cli/latest/powercli/configuring-vmware-vsphere-powercli/configuring-powercli-invalid-server-certificate-actions/configure-invalid-server-certificate-action.html` |
| TL-S22 | `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vmware-vsphere-supervisor-release-notes.html` |
| TL-S43b | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/microsoft-powershell-basics.html` |
| TL-preamble | dossier version-tagging convention (PowerCLI facts tagged by module version) |
| TL-discovery | dossier `## Discovery/lookup patterns` → PowerShell/PowerCLI, noun-prefix rationale |
| TL-gap2, TL-gap10, TL-gap11, TL-gap12, TL-gap14 | dossier `## Gaps and Ambiguities`, items 2, 10, 11, 12, 14 |

---

*Built from documentation captured 2026-07-31. Not validated against a live VCF environment or a live
PowerCLI installation. Cmdlets that modify infrastructure are production-affecting — verify against
Broadcom's docs for the exact build before executing.*
