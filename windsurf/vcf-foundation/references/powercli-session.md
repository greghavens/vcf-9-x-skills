# VCF PowerCLI — Install, Session Setup, Certificate Handling

Applies to VCF 9.0 and 9.1. **PowerCLI facts are tagged by the `VCF.PowerCLI` module version
(`{PCLI 9.0.0}` / `{PCLI 9.1.0}`), not by the VCF release** — the module is the real dimension of variation
`[TL-preamble]`. Where a fact holds for both module versions it is tagged `{both}`.

Every cmdlet, parameter and value below traces to a fetched reference page. **Anything the research could not
verify is marked `UNVERIFIED` and must be presented as unverified, never as an established cmdlet.**

---

## Contents

- [0. The four things that are most often got wrong](#0-the-four-things-that-are-most-often-got-wrong)
- [1. Module identity and versions](#1-module-identity-and-versions) — meta-module composition · module →
  product map
- [2. Install](#2-install) — verify what is actually installed
- [3. Platform support and prerequisites](#3-platform-support-and-prerequisites)
- [4. Session setup — verified `Connect-*` cmdlets](#4-session-setup--verified-connect-cmdlets) —
  4.1 `Connect-VIServer` · 4.2 `Connect-VcfSddcManagerServer` · 4.3 default-server variables
- [5. Cmdlets the research could NOT verify](#5-cmdlets-the-research-could-not-verify)
- [6. Token authentication — `{PCLI 9.1.0}` only](#6-token-authentication--pcli-910-only)
- [7. Certificate handling](#7-certificate-handling)
- [8. Other configuration topics](#8-other-configuration-topics)
- [9. `{PCLI 9.1.0}` new and changed cmdlets](#9-pcli-910-new-and-changed-cmdlets)
- [10. Runtime discovery — the escape hatch when a cmdlet name is unknown](#10-runtime-discovery--the-escape-hatch-when-a-cmdlet-name-is-unknown)
- [Source Index](#source-index)

---

## 0. The four things that are most often got wrong

| # | Correct | Wrong |
|---|---|---|
| 1 | The module is **`VCF.PowerCLI`** `[TL-S12]` `[TL-S05]` | `VMware.PowerCLI` — that is the pre-9.x name |
| 2 | `Connect-VcfSddcManagerServer` takes **`-IgnoreInvalidCertificate`** `[TL-S20]` | `-SkipCertificateCheck`; also not `-Force` — `-Force` is `Connect-VIServer`'s parameter `[TL-S19]` |
| 3 | **Windows PowerShell 5.1 is deprecated as of VCF PowerCLI 9.0**; use PowerShell 7.x `[TL-S17]` | Treating 5.1 as a supported target |
| 4 | On **Linux and macOS, `Set-PowerCLIConfiguration -InvalidCertificateAction` supports only `Fail` and `Ignore`** `[TL-S21]` | Offering `Warn` or `Prompt` on those platforms |

---

## 1. Module identity and versions

The PowerShell module is **`VCF.PowerCLI`**, not `VMware.PowerCLI` `[TL-S12]` `[TL-S05]`.

> *"VCF PowerCLI 9.0 (Build 24798382) represents a major rebranding from VMware.PowerCLI. The module is now
> called **VCF.PowerCLI**, though backward compatibility is maintained."* `[TL-S12]`

Gallery description: *"This PowerShell module contains commands for managing services part of VMware Cloud
Foundation."* — a renamed continuation of `VMware.PowerCLI`, *"a more tailored and streamlined automation
experience specifically for VCF environments."* `[TL-S05]`

| Module version | Published | VCF alignment |
|---|---|---|
| `VCF.PowerCLI` **9.0.0.24798382** | 2025-06-17 `[TL-S05]` `[TL-S06]` | ships alongside VCF 9.0 (same build-date family as the VCF 9.0 SDKs, build 24798170 `[TL-S12]`) |
| `VCF.PowerCLI` **9.1.0.25380678** | 2026-05-12 `[TL-S06]` `[TL-S07]` | ships alongside VCF 9.1 (Supervisor 9.1.0.0 also released 2026-05-12 `[TL-S22]`) |

Only these two versions appear in the Gallery version history `[TL-S06]`.

Load-time performance in 9.0 improved *"over 50% faster"* on PowerShell 5.1 and *"up to 70%"* on PowerShell 7.x
`[TL-S12]`.

`UNVERIFIED` — the current status and version of the legacy `VMware.PowerCLI` package on the Gallery, and
whether it simply aliases `VCF.PowerCLI`. Backward compatibility *"is maintained"* `[TL-S12]`, but the legacy
package page was not fetched `[TL-gap12]`.

### Meta-module composition

`VCF.PowerCLI` is a meta-module; its dependencies carry the cmdlets.

- `{PCLI 9.0.0}` — **36 dependencies**, all at `13.4.0.24798382` except `VMware.Vim` (`9.0.0.24798382`) and
  `VMware.VimAutomation.StorageUtility` (`1.6.1`) `[TL-S05]`.
- `{PCLI 9.1.0}` — same set at `13.5.0.25380678`, `VMware.Vim` at `9.1.0.25380678`,
  `VMware.VimAutomation.StorageUtility` still `1.6.1`, **with two deltas** `[TL-S07]`:
  - **Added: `VMware.Vcf.Sso`** — confirmed present in 9.1, confirmed absent in 9.0 `[TL-S07]` `[TL-S05]`.
  - **Removed: `VMware.PowerCLI.VCenter`** — confirmed absent in 9.1, present in 9.0 `[TL-S07]` `[TL-S05]`.

> Caveat: the 9.1 changelog reports **0 deprecated and 0 deleted** commands `[TL-S09]`, which sits oddly against
> the `VMware.PowerCLI.VCenter` removal. Most likely the module's cmdlets moved or the module still installs
> standalone and merely left the meta-module — **this is unresolved** `[TL-gap1]`. Do not tell users cmdlets were
> removed; do warn that a script explicitly importing `VMware.PowerCLI.VCenter` may break under
> `{PCLI 9.1.0}`.

### Module → product map `{both}`

| Product / surface | Module | Source |
|---|---|---|
| vCenter / ESX core inventory | `VMware.VimAutomation.Core` | `[TL-S19]` `[TL-S18]` |
| vSphere Automation (vAPI), low-level | `VMware.Sdk.vSphere` | `[TL-S05]` `[TL-S07]` |
| SDDC Manager (high-level) | `VMware.Vcf.SddcManager` | `[TL-S05]` `[TL-S07]` |
| SDDC Manager (low-level SDK) | `VMware.Sdk.Vcf.SddcManager` | `[TL-S20]` |
| VCF Installer | `VMware.Sdk.Vcf.Installer` | `[TL-S05]` `[TL-S07]` |
| VCF Cloud Builder | `VMware.Sdk.Vcf.CloudBuilder` | `[TL-S05]` `[TL-S07]` |
| VCF Operations | `VMware.Sdk.Vcf.Ops`, `VMware.VimAutomation.vROps` | `[TL-S05]` `[TL-S07]` |
| NSX (high-level) | `VMware.VimAutomation.Nsxt` | `[TL-S18]` |
| NSX Policy API (generated) | `VMware.Sdk.Nsx.Policy` (+ `.Infra`, `.GlobalInfra`, `.Initialize`) | `[TL-S05]` `[TL-S07]` |
| vSAN / storage | `VMware.VimAutomation.Storage` | `[TL-S18]` |
| Supervisor / Workload Management | `VMware.VimAutomation.WorkloadManagement` | `[TL-S18]` |
| VPC networking | `VMware.VimAutomation.Vpc` | `[TL-S05]` `[TL-S07]` |
| SSO — **`{PCLI 9.1.0}` only** | `VMware.Vcf.Sso` | `[TL-S07]` `[TL-S09]` |

Cmdlet reference root: `https://developer.broadcom.com/powercli/all-powercli-modules` `[TL-S18]`.

---

## 2. Install

```powershell
# Documented install (9.1 doc set)
Install-Module VCF.PowerCLI -Scope CurrentUser
Import-Module  VCF.PowerCLI
```
`[TL-S15]`

Prerequisites per the install page: verified system compatibility, an internet connection, and PowerShell
installed (Linux/macOS users must install PowerShell separately). If prompted about an untrusted repository,
press `y` `[TL-S15]`. Individual modules can also be installed: *"install individual VCF PowerCLI modules by
running the Install-Module cmdlet with the module name"* `[TL-S15]`.

Version-pinned form from the Gallery `[TL-S05]`:
```powershell
Install-Module -Name VCF.PowerCLI -RequiredVersion 9.0.0.24798382
```

Offline install: *"You can install all VCF PowerCLI modules in offline mode by using a ZIP file"* `[TL-S14]`
`[TL-S16]`. **`UNVERIFIED` — the exact offline command sequence.** The offline-install page was not fetched
`[TL-gap10]`. Do not invent one.

### Verify what is actually installed

```powershell
Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version
Get-Module -ListAvailable VMware.*, VCF.*
Get-Module                                    # currently imported
```
*(Standard PowerShell idioms. The VCF 9.1 PowerShell Basics page documents only
`Get-Help about_CommonParameters` `[TL-S43b]`; these discovery forms are not quoted from Broadcom docs — label
them as such if surfaced to a user.)*

---

## 3. Platform support and prerequisites

| Requirement | Value | Source |
|---|---|---|
| PowerShell | **7.x supported. Windows PowerShell 5.1 is deprecated as of VCF PowerCLI 9.0.** | `[TL-S17]` |
| OS | Windows Server plus Windows / Linux / macOS workstations | `[TL-S17]` |
| .NET (Windows) | ".NET Framework 4.7.2 or later" or ".NET Core 3.1" | `[TL-S17]` |
| .NET (Linux/macOS) | ".NET Core 3.1" | `[TL-S17]` |
| Python (for `VMware.ImageBuilder`) | **3.9+** per the 9.1 configuring page | `[TL-S13]` |
| Python — `{PCLI 9.1.0}` | adds **3.13** support; **"Python 3.7 and 3.8 is now deprecated"** (EOL) | `[TL-S08]` |
| Execution policy | allow local scripts — `RemoteSigned` | `[TL-S13]` |

**5.1 deprecation is a 9.0-era change, not a 9.1 one.** It applies to both `{PCLI 9.0.0}` and `{PCLI 9.1.0}`.
If a user reports being on PowerShell 5.1, say so and recommend PowerShell 7.x.

The compatibility-matrix page contains **no product-version table**; it defers to the Broadcom Product
Interoperability Matrix at `https://interopmatrix.broadcom.com/Interoperability` for VCF PowerCLI ↔
vCenter/ESX/vSAN/Live Site Recovery pairings `[TL-S17]`.

---

## 4. Session setup — verified `Connect-*` cmdlets

Only two `Connect-*` cmdlet reference pages were fetched. Treat everything else as unverified (§5).

### 4.1 `Connect-VIServer` — vCenter / ESX

Module `vmware.vimautomation.core` `[TL-S19]`.

```powershell
Connect-VIServer -Server <String> -User <String> -Password <String>

# documented example
Connect-VIServer -Server vcenter.example.com -User admin@vsphere.local -Password MyPassword
```

Key parameters `[TL-S19]`:

| Parameter | Meaning |
|---|---|
| `-Server` | target vCenter / ESX |
| `-User`, `-Password` | plain credentials |
| `-Credential` | `PSCredential` object |
| **`-Force`** | **suppresses certificate validation prompts** |
| `-SaveCredentials` | persist credentials |
| `-Session` | reconnect using a previous session object |
| `-NotDefault` | do not store the connection in `$DefaultVIServers` |

> **`-Force` is `Connect-VIServer`'s certificate flag. It is NOT the flag for `Connect-VcfSddcManagerServer`.**

> Before scripting username/password against vCenter 9.0, see the foundation reference: *"vCenter 9.0 blocks
> logins with just a user name and password, which might sometimes allow bypassing the federated provider
> domain"* `[VS-S5]`. That is a 9.0 release-note item; its 9.1 status is `UNVERIFIED`.

### 4.2 `Connect-VcfSddcManagerServer` — SDDC Manager

Module `VMware.Sdk.Vcf.SddcManager`. **Verified to exist, with full syntax** `[TL-S20]`:

```powershell
Connect-VcfSddcManagerServer -Server <String[]> [-Credential <PSCredential>]
  [-IgnoreInvalidCertificate] [-NotDefault] [-Password <SecureString>]
  [-Port <Int32[]>] [-Protocol <String>] [-User <String>]

# documented example
Connect-VcfSddcManagerServer -Server MySDDCManager.com -User "User" -Password "Password"
```

| Fact | Detail | Source |
|---|---|---|
| Certificate parameter | **`-IgnoreInvalidCertificate`** — *not* `-SkipCertificateCheck`, *not* `-Force` | `[TL-S20]` |
| `-Password` type | `SecureString` | `[TL-S20]` |
| `-Protocol` | defaults to HTTPS | `[TL-S20]` |
| Token parameters | The reference page does **not** list `-VcfApiToken` or `-VcfOAuthSecurityContext` on this cmdlet | `[TL-S20]` |

### 4.3 Default-server variables `{both}`

The PowerCLI Concepts page documents *"Managing Default Server Connections in VCF PowerCLI"*: by default cmdlets
run against connected systems *"if no target servers can be determined from the provided parameters,"* managed
through **`$DefaultVIServers`** and **`$DefaultCIServers`** `[TL-S04]`.

---

## 5. Cmdlets the research could NOT verify

**Do not present any of these as established.** Module existence is confirmed; parameter sets are not.

| Item | Status | What to do |
|---|---|---|
| `Connect-NsxtServer` | **`UNVERIFIED`.** The `VMware.VimAutomation.Nsxt` module exists and is the NSX cmdlet family `[TL-S18]`, but the cmdlet reference page was not retrieved | Check `https://developer.broadcom.com/powercli/latest/vmware.vimautomation.nsxt/` before asserting parameters. **Assume nothing about its certificate flag** — the two verified cmdlets already disagree (`-Force` vs `-IgnoreInvalidCertificate`) `[TL-gap11]` |
| `Connect-CisServer` | **`UNVERIFIED`.** Associated with `VMware.VimAutomation.Cis.Core`; the docs reference `$DefaultCIServers` `[TL-S04]`, which implies the cmdlet, but its reference page was not retrieved | Verify before use `[TL-gap11]` |
| `Connect-VcfOpsServer` | **`UNVERIFIED` as to parameters.** Named in the foundation dossier's reading of the 9.1 What's New page `[FA-S48]`; see the conflict note in §6 | Verify before use |
| `Get-PowerCLIConfiguration` | **`UNVERIFIED`.** Inferred as the read counterpart to `Set-PowerCLIConfiguration` `[TL-S21]` `[TL-S13]`; its reference page was not retrieved | Present as "expected but unverified" |
| CEIP cmdlet/parameter (commonly `Set-PowerCLIConfiguration -ParticipateInCEIP`) | **`UNVERIFIED`.** The 9.1 configuring page lists CEIP as a topic `[TL-S13]`; the child page was not fetched | Do not emit the exact parameter as fact `[TL-gap10]` |
| Offline install command sequence | **`UNVERIFIED`** — offline page not fetched `[TL-S16]` | Point at the *Install VCF PowerCLI Offline* page |
| Per-product SDDC Manager cmdlet index | **`UNVERIFIED`** — `developer.broadcom.com/powercli/latest/products/vcfsddcmanager/` returned *"PowerCLI Details Page is temporarily unavailable"* at fetch time `[TL-gap14]` | Enumerate at runtime with `Get-Command -Module VMware.Vcf.SddcManager` |

---

## 6. Token authentication — `{PCLI 9.1.0}` only

`{PCLI 9.1.0}` introduces a **`VcfOAuthSecurityContext`** parameter for OAuth authentication and a new
**`VcfApiToken`** parameter *"for VCF components"* `[TL-S08]`. Neither exists in `{PCLI 9.0.0}` `[TL-S05]`.

**Two dossiers disagree on which cmdlets expose them, from the same source page. Resolve conservatively.**

- The tooling dossier states plainly: *"Which specific cmdlets expose these was **UNVERIFIED — could not
  retrieve** (the changelog gives counts, not names)"* `[TL-S08]` `[TL-S09]`.
- The foundation dossier reads the same 9.1 What's New page as naming `Connect-VIServer`, `Connect-NsxServer`
  and `Connect-VcfOpsServer`, plus a `VcfApiToken` parameter enabling *"authentication either by instantiating a
  VcfOAuthSecurityContext … or just by an API token"* `[FA-S48]`.

Note also that the name in that list — **`Connect-NsxServer`** — does not match the module family name
`VMware.VimAutomation.Nsxt` / the expected `Connect-NsxtServer` `[TL-S18]`, which is itself unverified (§5).

**Guidance:** describe `VcfOAuthSecurityContext` and `VcfApiToken` as **9.1-only parameters whose cmdlet
attachment is not verified**. Discover them at runtime rather than asserting them:

```powershell
Get-Command -Verb Connect | Where-Object { $_.Source -like 'VMware.*' -or $_.Source -like 'VCF.*' }
Get-Help Connect-VIServer -Full          # inspect for VcfOAuthSecurityContext / VcfApiToken
Get-Help <cmdlet> -Parameter VcfApiToken
```

Also confirmed absent: the `Connect-VcfSddcManagerServer` reference page does **not** list either parameter
`[TL-S20]` — consistent with SDDC Manager being excluded from VCF SSO in both 9.0 and 9.1 `[FA-S18]` `[FA-S24]`.

---

## 7. Certificate handling

```powershell
Set-PowerCLIConfiguration -InvalidCertificateAction <value>
```

| Value | Meaning | Availability |
|---|---|---|
| `Unset` | **the default**; *"corresponds to Fail"* | all platforms `[TL-S21]` |
| `Fail` | reject invalid certificates | all platforms `[TL-S21]` |
| `Ignore` | accept invalid certificates | all platforms `[TL-S21]` |
| `Warn` | warn and continue | **Windows only** `[TL-S21]` |
| `Prompt` | prompt interactively | **Windows only** `[TL-S21]` |

> **On Linux and macOS only `Fail` and `Ignore` are supported** `[TL-S21]`. A lab or self-signed workflow on
> those platforms must use `-InvalidCertificateAction Ignore`, or the per-cmdlet flags `-Force`
> (`Connect-VIServer` `[TL-S19]`) / `-IgnoreInvalidCertificate` (`Connect-VcfSddcManagerServer` `[TL-S20]`).
> Offering `Warn` or `Prompt` on Linux/macOS is wrong.

**Preferred posture.** Broadcom's documented remedy for the default VMCA-signed certificates is to **replace
them with trusted enterprise CA-signed certificates**, not to disable verification — stated in both the 9.0
`[FA-S21]` and 9.1 `[FA-S22]` certificate-management pages. No fetched Broadcom page documents disabling TLS
verification as a supported practice. Treat `Ignore` / `-Force` / `-IgnoreInvalidCertificate` as a lab
expedient and say so explicitly when emitting them.

Note on page location: the correct certificate-configuration path is under
`configuring-powercli-invalid-server-certificate-actions/`; the sibling
`configuring-vmware-powercli-response-to-untrusted-certificates.html` path returned 404 (9.1) / 403 (9.0)
`[TL-retrieval-failures]`.

---

## 8. Other configuration topics

The 9.1 *Configuring VCF PowerCLI* page covers `[TL-S13]`:

- allow execution of local scripts (execution policy `RemoteSigned`);
- response to untrusted certificates (§7);
- modifying the web-task timeout via `Set-PowerCLIConfiguration`;
- **scoped settings** — per-user / per-group configuration scopes;
- installing and configuring Python (3.9+, for `VMware.ImageBuilder`);
- **CEIP** — *"optional anonymous feedback participation"* (exact cmdlet/parameter `UNVERIFIED`, §5).

---

## 9. `{PCLI 9.1.0}` new and changed cmdlets

**Named and confirmed on the 9.1 What's New page** `[TL-S08]`:

- `Get-VsanEffectiveCapacity` — vSAN capacity metrics
- `Remove-SddcCluster`, `Remove-SddcDomain`, `Remove-SddcHost`
- `Get-SddcTask` — task reporting

**Counted but not named** in the changelog `[TL-S09]` — do not invent names for these:

| Module | New commands | Updated |
|---|---|---|
| `VMware.VimAutomation.Vpc` | +33 | 2 |
| `VMware.Vcf.SddcManager` | +4 | — |
| `VMware.VimAutomation.Storage` | +3 | 1 |
| `VMware.Vcf.Sso` | +1 (new module) | — |
| `VMware.VimAutomation.Core` | — | 8 |
| `VMware.ImageBuilder` | — | 3 |

Changelog also reports **0 deprecated and 0 deleted** commands across the listed modules `[TL-S09]` — see the
`VMware.PowerCLI.VCenter` caveat in §1.

Other `{PCLI 9.1.0}` capability areas `[TL-S08]`: NVMe-over-TCP for VMkernel adapters; remote datastore
management; Transit Gateway management; VPC connectivity policies (community, private, promiscuous); DHCP
configuration and IP Block management; external IP assignment; CPU topology management ("Assigned at PowerOn");
Active Directory proxy integration.

---

## 10. Runtime discovery — the escape hatch when a cmdlet name is unknown

The docs are thin here. The only discovery idiom the VCF 9.1 PowerShell Basics page gives is `[TL-S43b]`:

> *"For a full list of the common parameters and more details on their usage, run
> `Get-Help about_CommonParameters`."*

Everything below is **standard PowerShell, not quoted from Broadcom docs** — label it as such when surfacing it.

```powershell
# Which module owns a cmdlet, and what does a module export?
Get-Command -Module VMware.Sdk.Vcf.SddcManager
Get-Command -Module VMware.VimAutomation.Nsxt
Get-Command -Noun *Sddc*          # noun-first is the highest-signal search
Get-Command -Verb Connect         # find every Connect-*Server entry point
Get-Command *Vsan*Capacity*       # wildcard when only a concept is known

# Full syntax, examples, parameter semantics
Get-Help Connect-VcfSddcManagerServer -Full
Get-Help Connect-VcfSddcManagerServer -Examples
Get-Help Set-PowerCLIConfiguration -Parameter InvalidCertificateAction

# Inspect returned objects (PowerCLI returns rich typed objects, not text)
Get-VM | Get-Member
Get-VM | Select-Object -First 1 | Format-List *
```

**Why noun-first matters:** the module split is by *product* and the noun prefix tracks the product — `*-Vcf*`
(VCF SDK modules), `*-Sddc*` (SDDC Manager), `*-Vsan*`, `*-Nsx*`, `*-VI*` (core vSphere).
`Get-Command -Noun Sddc*` is the fastest route to the SDDC Manager surface and is how `Get-SddcTask` /
`Remove-SddcCluster` `[TL-S08]` would be found without prior knowledge.

Runtime discovery is the correct answer to every `UNVERIFIED` item in §5 and §6.

---

## Source Index

All sources accessed **2026-07-31**. `TECHDOCS` = `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.

### `TL-*` — research/tooling-powercli-vks-sdk.md

| Ref | URL |
|---|---|
| TL-S04 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-vsphere-powercli-specific-concepts.html` |
| TL-S05 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382` |
| TL-S06 | `https://www.powershellgallery.com/packages/VCF.PowerCLI` |
| TL-S07 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.1.0.25380678` |
| TL-S08 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S09 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-powercli-changelog.html` |
| TL-S12 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S13 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/configuring-vmware-vsphere-powercli.html` |
| TL-S14 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli.html` |
| TL-S15 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli/install-powercli.html` |
| TL-S16 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli.html` |
| TL-S17 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-powercli-compatibility-matrix.html` |
| TL-S18 | `https://developer.broadcom.com/powercli/all-powercli-modules` |
| TL-S19 | `https://developer.broadcom.com/powercli/latest/vmware.vimautomation.core/commands/connect-viserver` |
| TL-S20 | `https://developer.broadcom.com/powercli/latest/vmware.sdk.vcf.sddcmanager/commands/connect-vcfsddcmanagerserver` |
| TL-S21 | `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/power-cli/latest/powercli/configuring-vmware-vsphere-powercli/configuring-powercli-invalid-server-certificate-actions/configure-invalid-server-certificate-action.html` |
| TL-S22 | `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vmware-vsphere-supervisor-release-notes.html` |
| TL-S43b | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/microsoft-powershell-basics.html` |
| TL-preamble | `research/tooling-powercli-vks-sdk.md`, version-tagging convention |
| TL-gap1, TL-gap10, TL-gap11, TL-gap12, TL-gap14 | `research/tooling-powercli-vks-sdk.md`, `## Gaps and Ambiguities`, items 1, 10, 11, 12, 14 |
| TL-retrieval-failures | `TECHDOCS/9-1/.../configuring-vmware-powercli-response-to-untrusted-certificates.html` — HTTP 404 (9.1 variant) / HTTP 403 (9.0 variant); `https://developer.broadcom.com/powercli/latest/products/vcfsddcmanager/` — "PowerCLI Details Page is temporarily unavailable" |

### `FA-*` — research/foundation-auth-identity.md

| Ref | URL |
|---|---|
| FA-S18 | `TECHDOCS/9-0/fleet-management/what-is.html` (SDDC Manager and ESX excluded from VCF SSO) |
| FA-S21 | `TECHDOCS/9-0/fleet-management/certificate-management-9-0.html` |
| FA-S22 | `TECHDOCS/9-1/fleet-management/certificate-management-9-0.html` |
| FA-S24 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is.html` |
| FA-S48 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` (same page as TL-S08; read as naming the cmdlets — see §6) |

### `VS-*` — research/vsphere-vcenter-vsan.md

| Ref | URL |
|---|---|
| VS-S5 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-vsphere.html` (blocked non-federated vCenter logins — a **9.0** page) |

---

*This reference was built from documentation. It has not been validated against a live VCF environment or a
live PowerCLI installation.*
