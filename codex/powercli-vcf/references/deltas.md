# `VCF.PowerCLI` 9.0.0 → 9.1.0 — what changed

Organised by **module version**, because that is the dimension that decides which cmdlets exist
`[TL-preamble]`. `{PCLI 9.0.0}` = `9.0.0.24798382` (2025-06-17); `{PCLI 9.1.0}` = `9.1.0.25380678`
(2026-05-12) `[DOC]` `[TL-S05]` `[TL-S06]` `[TL-S07]`. These pair with VCF 9.0 and 9.1 respectively,
but **the pairing is inference, not a documented binding** — see `module-map.md` §1.

**Evidence tags.** `[DOC]` = traced to a fetched reference page. `[UNVERIFIED]` = not confirmed —
never present as established. `[INFERRED]` = deduction from two `[DOC]` facts, labelled as such.

---

## 0. The one contradiction in this file

**The 9.1 changelog reports "0 deprecated and 0 deleted commands" across the listed modules**
`[DOC]` `[TL-S09]`.

**Yet `VMware.PowerCLI.VCenter` is present in the `{PCLI 9.0.0}` dependency set and absent from
`{PCLI 9.1.0}`** — both confirmed by direct interrogation of the two Gallery pages `[DOC]` `[TL-S05]`
`[TL-S07]`.

Those two statements are not obviously compatible. **This is recorded, not resolved.** Research could
not determine which of the plausible explanations holds:

| Possibility | Would explain | Status |
|---|---|---|
| The module's cmdlets were folded into other modules | zero *deleted commands* while a *module* left | `[UNVERIFIED]` |
| The module still installs standalone and merely left the meta-module dependency set | zero deletions; nothing lost | `[UNVERIFIED]` |
| The changelog's scope is "listed modules" and a removed module is simply out of scope | the count is technically true and unhelpful | `[UNVERIFIED]` |

**How to speak about it.** Do not tell users cmdlets were removed — no source supports that. **Do**
warn that a script explicitly running `Import-Module VMware.PowerCLI.VCenter` may break under
`{PCLI 9.1.0}`, because the meta-module no longer pulls it in. That warning is supported by `[DOC]`
evidence; a stronger claim in either direction is not.

The diagnostic, on the user's own machine:

```powershell
Get-Module -ListAvailable VMware.PowerCLI.VCenter    # present standalone, or not present at all?
```

One further reason for care: **a first-pass narrative summary of the 9.1 Gallery page asserted "no
module additions or removals"** while the page's own rendered table showed otherwise. Both deltas
were only established by pointed yes/no interrogation `[TL-gap2]`. Treat any prose summary of a
dependency list as unreliable, including this one — the Gallery page is the artefact.

---

## 1. Delta table

| Item | `{PCLI 9.0.0}` | `{PCLI 9.1.0}` | Evidence |
|---|---|---|---|
| **Module version** | `9.0.0.24798382`, published 2025-06-17 | `9.1.0.25380678`, published 2026-05-12 | `[DOC]` `[TL-S05]` `[TL-S06]` `[TL-S07]` |
| **Component modules** | `13.4.0.24798382`; `VMware.Vim` `9.0.0.24798382` | `13.5.0.25380678`; `VMware.Vim` `9.1.0.25380678` | `[DOC]` `[TL-S05]` `[TL-S07]` |
| `VMware.VimAutomation.StorageUtility` | `1.6.1` | `1.6.1` — **unchanged** | `[DOC]` `[TL-S05]` `[TL-S07]` |
| **Module added** | — | **`VMware.Vcf.Sso`** (+1 command), confirmed absent in 9.0 | `[DOC]` `[TL-S07]` `[TL-S05]` `[TL-S09]` |
| **Module removed from the meta-module** | `VMware.PowerCLI.VCenter` (`= 13.4.0.24798382`) present | **absent** — see §0 | `[DOC]` `[TL-S05]` `[TL-S07]` |
| **New cmdlets, named** | — | `Get-VsanEffectiveCapacity`, `Remove-SddcCluster`, `Remove-SddcDomain`, `Remove-SddcHost`, `Get-SddcTask` | `[DOC]` `[TL-S08]`; parameters `[UNVERIFIED]` |
| **New cmdlets, counted only** | — | `.Vpc` **+33**, `VMware.Vcf.SddcManager` **+4**, `.Storage` **+3**, `VMware.Vcf.Sso` **+1** | `[DOC]` `[TL-S09]` — **no names published** |
| **Updated cmdlets** | — | `.Core` 8, `.ImageBuilder` 3, `.Vpc` 2, `.Storage` 1 | `[DOC]` `[TL-S09]` — no names, no description of *what* changed |
| **Deprecated / deleted** | — | **0 deprecated, 0 deleted** across listed modules — **contradicts the module removal, §0** | `[DOC]` `[TL-S09]` |
| **Token auth** | No token parameters documented | **`VcfOAuthSecurityContext`** (OAuth) and **`VcfApiToken`** parameters introduced — cmdlet attachment disputed, §2 | `[DOC]` `[TL-S08]`; `[UNVERIFIED]` as to which cmdlets |
| **PowerShell** | 7.x; **5.1 deprecated as of PowerCLI 9.0** | unchanged — 7.x; 5.1 still deprecated | `[DOC]` `[TL-S17]` |
| **Python** (for `VMware.ImageBuilder`) | 3.9+ | adds **3.13**; **"Python 3.7 and 3.8 is now deprecated"** (EOL) | `[DOC]` `[TL-S13]` `[TL-S08]` |
| **Certificate handling** | `Set-PowerCLIConfiguration -InvalidCertificateAction`: `Unset`/`Fail`/`Ignore`/`Warn`/`Prompt`; Linux/macOS `Fail`+`Ignore` only | **No change documented** | `[DOC]` `[TL-S21]` |
| **Install command** | `Install-Module VCF.PowerCLI -Scope CurrentUser` | unchanged | `[DOC]` `[TL-S15]` |

**The 5.1 deprecation is a 9.0-era change, not a 9.1 one.** It applies to both module versions
`[DOC]` `[TL-S17]`. Do not present it as "new in 9.1".

---

## 2. Token authentication in `{PCLI 9.1.0}` — a source conflict

`{PCLI 9.1.0}` introduces a **`VcfOAuthSecurityContext`** parameter for OAuth and a **`VcfApiToken`**
parameter *"for VCF components"* `[DOC]` `[TL-S08]`. Neither exists in `{PCLI 9.0.0}` `[DOC]`
`[TL-S05]`. That much is settled.

**Which cmdlets expose them is not.** Two research dossiers read the *same* 9.1 What's New page
differently:

| Source | Claim |
|---|---|
| Tooling dossier `[TL-S08]` `[TL-S09]` | *"Which specific cmdlets expose these was **UNVERIFIED — could not retrieve*** (the changelog gives counts, not names)" |
| Foundation dossier `[FA-S48]` | the page names **`Connect-VIServer`**, **`Connect-NsxServer`**, **`Connect-VcfOpsServer`**, plus a `VcfApiToken` parameter enabling *"authentication either by instantiating a VcfOAuthSecurityContext … or just by an API token"* |

Two further wrinkles that argue for caution:

- The name in that list — **`Connect-NsxServer`** — does not match the NSX module family name
  `VMware.VimAutomation.Nsxt` or the expected `Connect-NsxtServer` `[DOC]` `[TL-S18]`, which is
  itself `[UNVERIFIED]` `[TL-gap11]`.
- **`Connect-VcfOpsServer`** is named only in that reading; its parameter set is `[UNVERIFIED]`.

**Confirmed negative, and useful:** the `Connect-VcfSddcManagerServer` reference page lists **neither**
`-VcfApiToken` nor `-VcfOAuthSecurityContext` `[DOC]` `[TL-S20]` — consistent with SDDC Manager being
excluded from VCF SSO in both versions `[FA-S18]` `[FA-S24]`.

**Guidance.** Describe both as **9.1-only parameters whose cmdlet attachment is not verified**. Then
resolve at runtime rather than asserting:

```powershell
Get-Command -Verb Connect | Where-Object { $_.Source -like 'VMware.*' -or $_.Source -like 'VCF.*' }
Get-Help Connect-VIServer -Full                 # inspect for VcfOAuthSecurityContext / VcfApiToken
Get-Help <cmdlet> -Parameter VcfApiToken
```

Token acquisition itself — where the API token comes from, its lifetime, which IdP issues it — is
`vcf-foundation`'s subject, not this skill's.

---

## 3. Capability areas added in `{PCLI 9.1.0}` — with no cmdlet names

The 9.1 What's New page describes these areas; **no fetched source names the cmdlets** `[DOC]`
`[TL-S08]`. This section exists so you recognise the capability and then go look up the real name —
**not so you can construct one.**

- NVMe-over-TCP support for VMkernel adapters
- Remote datastore management cmdlets
- Transit Gateway management cmdlets
- VPC connectivity policies — community, private, promiscuous
- DHCP configuration and IP Block management
- External IP assignment
- CPU topology management ("Assigned at PowerOn")
- Active Directory proxy integration

The `.Vpc` module's **+33 new commands** `[DOC]` `[TL-S09]` almost certainly cover most of the
networking items above `[INFERRED]`. Thirty-three real cmdlets, zero published names. Find them:

```powershell
Get-Command -Module VMware.VimAutomation.Vpc | Sort-Object Verb, Noun
```

---

## 4. Migration checklist for an existing script

Ordered by how often each actually bites.

| # | Check | Why |
|---|---|---|
| 1 | Does the script `Import-Module VMware.PowerCLI.VCenter` explicitly? | Not pulled in by the `{PCLI 9.1.0}` meta-module `[DOC]` `[TL-S07]`. **Most likely breakage.** §0 |
| 2 | Does it `Install-Module VMware.PowerCLI`? | Pre-9.x name; the module is `VCF.PowerCLI` `[DOC]` `[TL-S12]` `[TL-S15]` |
| 3 | Is it running on Windows PowerShell 5.1? | Deprecated since PowerCLI **9.0** `[DOC]` `[TL-S17]` — a 9.0-era issue surfacing late |
| 4 | Does it pin a module version? | `-RequiredVersion 9.0.0.24798382` will silently keep it on 9.0 `[DOC]` `[TL-S05]` |
| 5 | Does it use Python 3.7/3.8 with `VMware.ImageBuilder`? | Deprecated in 9.1 `[DOC]` `[TL-S08]` |
| 6 | Does it assume `Warn`/`Prompt` cert actions on Linux/macOS? | Only `Fail` and `Ignore` are supported there — **unchanged in both versions**, but a standing bug `[DOC]` `[TL-S21]` |
| 7 | Does it use cmdlets that only exist in one version? | `Get-SddcTask`, `Remove-Sddc*`, `Get-VsanEffectiveCapacity` are 9.1-only `[DOC]` `[TL-S08]` |
| 8 | Does it depend on a `.Core`, `.Storage`, `.Vpc` or `.ImageBuilder` cmdlet's exact behaviour? | 14 cmdlets across those modules were "updated" in 9.1, **unnamed and undescribed** `[DOC]` `[TL-S09]` — test, do not reason |

Row 8 is the one with no documentary route at all. The changelog says 8 `.Core` cmdlets changed and
names none of them `[TL-S09]`. There is no way to know which from documentation. **Test the script.**

---

## 5. What is not known about this delta

| Question | Status |
|---|---|
| What happened to `VMware.PowerCLI.VCenter`'s cmdlets | **Unresolved** `[TL-gap1]` — §0 |
| Names of the 41 new counted-only cmdlets | Not published `[TL-S09]` — `Get-Command -Module` |
| Names/behaviour of the 14 updated cmdlets | Not published `[TL-S09]` |
| Which cmdlets expose `VcfApiToken` / `VcfOAuthSecurityContext` | Sources conflict `[TL-S08]` `[FA-S48]` — §2 |
| The single `VMware.Vcf.Sso` cmdlet's name | Not published `[TL-S09]` — `Get-Command -Module VMware.Vcf.Sso` |
| Whether a PowerCLI 9.2 / VCF 9.2 exists | Only two versions in the Gallery history as of 2026-07-31 `[DOC]` `[TL-S06]` |
| Status of the legacy `VMware.PowerCLI` package | `[UNVERIFIED]` `[TL-gap12]` |

---

## Source Index

All sources accessed **2026-07-31**.
`TECHDOCS` = `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.

### `TL-*` — `research/tooling-powercli-vks-sdk.md`

| Ref | URL / location |
|---|---|
| TL-S05 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382` |
| TL-S06 | `https://www.powershellgallery.com/packages/VCF.PowerCLI` |
| TL-S07 | `https://www.powershellgallery.com/packages/VCF.PowerCLI/9.1.0.25380678` |
| TL-S08 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S09 | `TECHDOCS/9-1/release-notes/.../whats-new-vcf-cli-api-sdk/vcf-powercli-changelog.html` |
| TL-S12 | `TECHDOCS/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html` |
| TL-S13 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/configuring-vmware-vsphere-powercli.html` |
| TL-S15 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli/install-powercli.html` |
| TL-S17 | `TECHDOCS/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-powercli-compatibility-matrix.html` |
| TL-S18 | `https://developer.broadcom.com/powercli/all-powercli-modules` |
| TL-S20 | `https://developer.broadcom.com/powercli/latest/vmware.sdk.vcf.sddcmanager/commands/connect-vcfsddcmanagerserver` |
| TL-S21 | `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/power-cli/latest/powercli/configuring-vmware-vsphere-powercli/configuring-powercli-invalid-server-certificate-actions/configure-invalid-server-certificate-action.html` |
| TL-preamble | dossier version-tagging convention |
| TL-gap1, TL-gap2, TL-gap11, TL-gap12 | dossier `## Gaps and Ambiguities`, items 1, 2, 11, 12 |

### `FA-*` — `research/foundation-auth-identity.md`

| Ref | URL / location |
|---|---|
| FA-S18 | `TECHDOCS/9-0/fleet-management/what-is.html` — SDDC Manager and ESX excluded from VCF SSO |
| FA-S24 | `TECHDOCS/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is.html` |
| FA-S48 | `TECHDOCS/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html` — same page as TL-S08, read as naming the cmdlets (§2) |

---

*Built from documentation captured 2026-07-31. Not validated against a live VCF environment or a live
PowerCLI installation. The 9.1-only `Remove-SddcCluster`, `Remove-SddcDomain` and `Remove-SddcHost`
cmdlets remove real infrastructure — verify against Broadcom's docs for the exact build before
executing.*
