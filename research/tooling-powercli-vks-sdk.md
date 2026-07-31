# VCF 9.0 / 9.1 Tooling Layer — PowerCLI, VKS/Supervisor, SDKs & OpenAPI

Research date: **2026-07-31**. Every claim below carries a bracketed source ID resolving to the
`## Source Inventory` table at the end. Facts not verified against a page fetched in this task are
explicitly marked `UNVERIFIED — could not retrieve`.

Version tagging convention:
- `[9.0]` / `[9.1]` = VCF doc-set-specific.
- PowerCLI facts are tagged with the **VCF.PowerCLI module version** (`{PCLI 9.0.0}` / `{PCLI 9.1.0}`)
  because that — not the VCF release — is the real dimension of variation.
- VKS facts are tagged with the **VKS version** (`{VKS 3.4}` … `{VKS 3.7}`).

---

## PowerCLI

### The headline: the module was renamed

The PowerShell module is **`VCF.PowerCLI`**, not `VMware.PowerCLI`. [S12][S05]

> "VCF PowerCLI 9.0 (Build 24798382) represents a major rebranding from VMware.PowerCLI. The module
> is now called **VCF.PowerCLI**, though backward compatibility is maintained." [S12]

The gallery description reads: "This PowerShell module contains commands for managing services part
of VMware Cloud Foundation." — described as a renamed continuation of VMware.PowerCLI, "a more
tailored and streamlined automation experience specifically for VCF environments." [S05]

Load-time performance in 9.0 improved "over 50% faster" on PowerShell 5.1 and "up to 70%" on
PowerShell 7.x. [S12]

**Agent-facing implication:** `Install-Module VMware.PowerCLI` is the *old* name. Teach `VCF.PowerCLI`
as the umbrella meta-module for 9.x. Note that `VMware.PowerCLI` still exists on the Gallery as a
separate legacy package — but its current status/version was **UNVERIFIED — could not retrieve** in
this task (the gallery page for `VMware.PowerCLI` was not fetched).

### Published versions

| Module version | Published | VCF alignment |
|---|---|---|
| `VCF.PowerCLI` **9.0.0.24798382** | 2025-06-17 [S05][S06] | ships alongside VCF 9.0 (same build-date family as VCF 9.0 SDKs, build 24798170 [S12]) |
| `VCF.PowerCLI` **9.1.0.25380678** | 2026-05-12 [S06][S07] | ships alongside VCF 9.1 (Supervisor 9.1.0.0 also released 2026-05-12 [S22]) |

Only these two versions are listed in the gallery version history. [S06]

### Install

```powershell
# Documented install (9.1 doc set)
Install-Module VCF.PowerCLI -Scope CurrentUser
Import-Module  VCF.PowerCLI
```
[S15]

Prerequisites per the install page: system compatibility verified, an internet connection, and
PowerShell installed (Linux/macOS users must install PowerShell separately). If prompted about an
untrusted repository, press `y`. [S15] The docs also note you may "install individual VCF PowerCLI
modules by running the Install-Module cmdlet with the module name." [S15]

Version-pinned form from the Gallery: [S05]
```powershell
Install-Module -Name VCF.PowerCLI -RequiredVersion 9.0.0.24798382
```

Offline install: "You can install all VCF PowerCLI modules in offline mode by using a ZIP file" —
see the *Install VCF PowerCLI Offline* page [S14][S16]. Exact offline commands were
**UNVERIFIED — could not retrieve** (the offline page itself was not fetched).

### Platform support

- `{PCLI 9.1.0}` supports **PowerShell 7.x**. **Windows PowerShell 5.1 is deprecated as of VCF
  PowerCLI 9.0.** [S17]
- Runs on Windows Server plus Windows/Linux/macOS workstations. [S17]
- Windows prerequisite: ".NET Framework 4.7.2 or later" or ".NET Core 3.1"; Linux/macOS: ".NET Core
  3.1". [S17]
- Python is a prerequisite for the `VMware.ImageBuilder` module — "Python 3.9+" per the 9.1
  configuring page [S13]. `{PCLI 9.1.0}` adds **Python 3.13 support**; **"Python 3.7 and 3.8 is now
  deprecated"** due to EOL. [S08]
- The compatibility matrix page does **not** contain a product-version table; it defers to the
  Broadcom Product Interoperability Matrix at `https://interopmatrix.broadcom.com/Interoperability`
  for VCF PowerCLI ↔ vCenter/ESX/vSAN/Live Site Recovery pairings. [S17]

### Module inventory (verified from the Gallery dependency lists)

`VCF.PowerCLI` is a meta-module. Its dependencies are the modules that actually carry cmdlets.

**`{PCLI 9.0.0}` — 36 dependencies** [S05], all at `13.4.0.24798382` except where noted:

`VMware.CloudServices`, `VMware.DeployAutomation`, `VMware.ImageBuilder`, `VMware.OpenAPI` (≥),
`VMware.PowerCLI.VCenter`, `VMware.Sdk.Nsx.Policy`, `VMware.Sdk.Nsx.Policy.GlobalInfra`,
`VMware.Sdk.Nsx.Policy.Infra`, `VMware.Sdk.Nsx.Policy.Initialize`, `VMware.Sdk.Srm`,
`VMware.Sdk.Vcf.CloudBuilder`, `VMware.Sdk.Vcf.Installer`, `VMware.Sdk.Vcf.Ops`,
`VMware.Sdk.Vcf.SddcManager`, `VMware.Sdk.Vr`, `VMware.Sdk.vSphere`, `VMware.Vcf.SddcManager`,
`VMware.Vim` (9.0.0.24798382), `VMware.VimAutomation.Cis.Core`, `.Cloud`, `.Common`, `.Core`,
`.Hcx`, `.License`, `.Nsxt`, `.Sdk`, `.Security`, `.Srm`, `.Storage`,
`VMware.VimAutomation.StorageUtility` (1.6.1), `.Vds`, `.Vmc`, `.Vpc`, `.vROps`,
`.WorkloadManagement`, `VMware.VumAutomation`.

**`{PCLI 9.1.0}`** — same set at `13.5.0.25380678` (with `VMware.Vim` at `9.1.0.25380678` and
`VMware.VimAutomation.StorageUtility` still pinned to `1.6.1`), **with two deltas**: [S07]

- **Added: `VMware.Vcf.Sso`** — confirmed present in 9.1, confirmed *absent* in 9.0. [S07][S05]
- **Removed: `VMware.PowerCLI.VCenter`** — confirmed absent in 9.1, confirmed present in 9.0
  (`VMware.PowerCLI.VCenter (= 13.4.0.24798382)`). [S07][S05]

Both deltas were verified by direct yes/no interrogation of each Gallery page rather than by
narrative summary, because a first-pass summary of the 9.1 page incorrectly asserted "no module
additions or removals." See `## Gaps and Ambiguities`.

### Cmdlet families by product

| Product / surface | Module | Evidence |
|---|---|---|
| vCenter / ESX core inventory | `VMware.VimAutomation.Core` | [S19][S18] |
| vSphere Automation (vAPI) low-level | `VMware.Sdk.vSphere` | [S05][S07] |
| SDDC Manager (high-level) | `VMware.Vcf.SddcManager` | [S05][S07] |
| SDDC Manager (low-level SDK) | `VMware.Sdk.Vcf.SddcManager` | [S20] |
| VCF Installer | `VMware.Sdk.Vcf.Installer` | [S05][S07] |
| VCF Cloud Builder | `VMware.Sdk.Vcf.CloudBuilder` | [S05][S07] |
| VCF Operations | `VMware.Sdk.Vcf.Ops`, `VMware.VimAutomation.vROps` | [S05][S07] |
| NSX (high-level) | `VMware.VimAutomation.Nsxt` | [S18] |
| NSX Policy API (generated) | `VMware.Sdk.Nsx.Policy` (+ `.Infra`, `.GlobalInfra`, `.Initialize`) | [S05][S07] |
| vSAN / storage | `VMware.VimAutomation.Storage` | [S18] |
| Supervisor / Workload Mgmt | `VMware.VimAutomation.WorkloadManagement` | [S18] |
| VPC networking | `VMware.VimAutomation.Vpc` | [S05][S07] |
| SSO `{PCLI 9.1.0}` only | `VMware.Vcf.Sso` | [S07][S09] |

Cmdlet reference root: `https://developer.broadcom.com/powercli/all-powercli-modules`, with
per-module pages such as `https://developer.broadcom.com/powercli/latest/vmware.vimautomation.core/`
and `.../vmware.vimautomation.nsxt/`. [S18]

### Session setup — verified `Connect-*` cmdlets

**`Connect-VIServer`** — module `vmware.vimautomation.core`. [S19]
```powershell
Connect-VIServer -Server <String> -User <String> -Password <String>
# example
Connect-VIServer -Server vcenter.example.com -User admin@vsphere.local -Password MyPassword
```
Key parameters: `-Server`, `-User`, `-Password`, `-Credential` (PSCredential), `-Force` (suppresses
certificate validation prompts), `-SaveCredentials`, `-Session` (reconnect using a previous session
object), `-NotDefault` (prevents storing the connection in `$DefaultVIServers`). [S19]

**`Connect-VcfSddcManagerServer`** — module `VMware.Sdk.Vcf.SddcManager`. **Verified to exist**, with
full syntax: [S20]
```powershell
Connect-VcfSddcManagerServer -Server <String[]> [-Credential <PSCredential>]
  [-IgnoreInvalidCertificate] [-NotDefault] [-Password <SecureString>]
  [-Port <Int32[]>] [-Protocol <String>] [-User <String>]
# example
Connect-VcfSddcManagerServer -Server MySDDCManager.com -User "User" -Password "Password"
```
Note the certificate parameter here is **`-IgnoreInvalidCertificate`**, *not* `-SkipCertificateCheck`.
`-Protocol` defaults to HTTPS. The reference page does **not** list `-VcfApiToken` or
`-VcfOAuthSecurityContext` on this cmdlet. [S20]

**`Connect-NsxtServer`** — the `VMware.VimAutomation.Nsxt` module exists and is the NSX cmdlet family
[S18], but the cmdlet reference page for `Connect-NsxtServer` itself was
**UNVERIFIED — could not retrieve** in this task. Do not assert its parameter set without checking
`https://developer.broadcom.com/powercli/latest/vmware.vimautomation.nsxt/`.

**`Connect-CisServer`** — associated with `VMware.VimAutomation.Cis.Core`; the docs reference a
`$DefaultCIServers` variable [S04], which implies the cmdlet, but the cmdlet reference page was
**UNVERIFIED — could not retrieve**.

**Default-server variables.** The PowerCLI Concepts page documents "Managing Default Server
Connections in VCF PowerCLI": by default cmdlets run against connected systems "if no target servers
can be determined from the provided parameters," managed through the **`$DefaultVIServers`** and
**`$DefaultCIServers`** variables. [S04]

**New auth in `{PCLI 9.1.0}`:** a **`VcfOAuthSecurityContext`** parameter for OAuth authentication and
a new **`VcfApiToken`** parameter "for VCF components." [S08] Which specific cmdlets expose these was
**UNVERIFIED — could not retrieve** (the changelog gives counts, not names [S09]).

### Certificate handling

```powershell
Set-PowerCLIConfiguration -InvalidCertificateAction <value>
```
Allowed values: **`Unset`** (the default, "corresponds to Fail"), **`Fail`**, **`Ignore`**, **`Warn`**,
**`Prompt`**. On **Linux and macOS only `Fail` and `Ignore` are supported.** [S21]

This matters for agents: on Linux/macOS, `Prompt` and `Warn` are not available, so a lab/self-signed
workflow must use `-InvalidCertificateAction Ignore` (or per-cmdlet `-Force` /
`-IgnoreInvalidCertificate`).

### Other configuration topics

The 9.1 *Configuring VCF PowerCLI* page covers: allow execution of local scripts (execution policy
`RemoteSigned`); response to untrusted certificates; modifying the web-task timeout via
`Set-PowerCLIConfiguration`; **scoped settings** (per-user/per-group configuration scopes); installing
and configuring Python (3.9+, for `VMware.ImageBuilder`); and **CEIP** — "optional anonymous feedback
participation." [S13] The exact CEIP cmdlet/parameter (commonly `-ParticipateInCEIP`) was
**UNVERIFIED — could not retrieve**; the child page was not fetched.

### `{PCLI 9.1.0}` new/changed cmdlets

Named cmdlets confirmed by the 9.1 What's New page: [S08]
- `Get-VsanEffectiveCapacity` (vSAN capacity metrics)
- `Remove-SddcCluster`, `Remove-SddcDomain`, `Remove-SddcHost`
- `Get-SddcTask` (task reporting)

Also in `{PCLI 9.1.0}`: NVMe-over-TCP support for VMkernel adapters; remote datastore management
cmdlets; Transit Gateway management cmdlets; VPC connectivity policies (community, private,
promiscuous); DHCP configuration and IP Block management; external IP assignment; CPU topology
management ("Assigned at PowerOn"); Active Directory proxy integration. [S08]

Changelog counts (no names given on that page): `VMware.VimAutomation.Vpc` +33 new commands,
`VMware.Vcf.SddcManager` +4, `VMware.VimAutomation.Storage` +3, `VMware.Vcf.Sso` +1 (new module);
updated: `.Core` 8, `.ImageBuilder` 3, `.Vpc` 2, `.Storage` 1. **"0" deprecated and "0" deleted
commands** across listed modules. [S09]

---

## VKS / Supervisor

### What VKS is

**vSphere Kubernetes Service (VKS)** is the Kubernetes-cluster service running on **vSphere
Supervisor**. It is the renamed **Tanzu Kubernetes Grid Service** — visible in the fact that every
current VKS doc URL still uses the legacy slug `vmware-tanzu-kubernetes-grid-service-*`. [S23][S26]

VKS provisions clusters via **Cluster API (CAPI)** and the **Cluster API Provider for vSphere
(CAPV)**, with **the vSphere Supervisor acting as the CAPI management cluster.** [S02]

Component layers per the VKS Components page: [S28]
- Three controller layers: **Virtual Machine Service (VM Operator)**, **Cluster API**, and the
  **Cloud Provider Plugin** (integrates vSphere resources and CNS).
- Auth: Authentication Webhook validating tokens via vCenter SSO **or OIDC with Pinniped**.
- Storage: CSI plugin; transient, persistent and container-image storage.
- Networking: CNI is **Antrea (default)** or **Calico**.
- Load balancing: NSX embedded/advanced load balancer, or HAProxy.
- Tenancy: **vSphere Namespace** is the "tenancy boundary that enables self-service consumption of
  3 runtimes … Virtual Machines, VKS clusters, vSphere Pods."
- **vSphere Zones**: Supervisor stretched across three vSphere clusters for HA.

### Version map

| VKS | Releases | Notes |
|---|---|---|
| **3.4** | 3.4.0+v1.33 (2025-06-17), 3.4.1+v1.33 (2025-09-29), 3.4.2+v1.33 (2026-01-27) | "generally available for use with vSphere 9.0 and vSphere 8.x". K8s 1.33 added; interop 1.32/1.31/1.30/1.29; **drops VKr 1.28**. ClusterClass **`builtin-generic-v3.4.0`**. [S29] |
| **3.5** | (page exists, not fetched) | **UNVERIFIED — could not retrieve** [S26] |
| **3.6** | 3.6.0+v1.35 (2026-02-11), 3.6.1+v1.35 (2026-04-13), 3.6.2+v1.35 (2026-04-13), 3.6.3+v1.35 (2026-06-16) | "generally available for vSphere 9.x and 8.x". K8s **1.35** (24-month support). ClusterClass **`builtin-generic-v3.6.0`**. [S23] |
| **3.7** | (page exists, not fetched) | **UNVERIFIED — could not retrieve** [S26] |

VKS 3.4.0 and VCF 9.0 share a release date (2025-06-17) [S29][S12], and VKS 3.6.1 is explicitly the
release carrying "VCF 9.1 enhancements" [S23]. Note the docs do **not** state a hard "VKS X ships
with VCF Y" binding — VKS releases asynchronously and is installed/upgraded as a Supervisor service.
Treat the alignment above as inference from dates, not as a documented mapping. See
`## Gaps and Ambiguities`.

**VKS 3.6 (i.e. the 9.1 era) new capabilities:** [S23]
- `builtin-generic-v3.6.0` ClusterClass with additional configuration variables.
- **VCF 9.1 integration (3.6.1+):** multi-network support with secondary interfaces; **Antrea CNI
  hybrid encapsulation mode (up to 40% performance improvement)**; **2.5x cluster scalability —
  up to 500 clusters per Supervisor**; **VM Fast Deploy**; **EncryptionClass** for multi-tenancy.
- RHEL-based node images via the **ImageBaker** tool, replacing Image Builder.
- Upgrade prerequisites: Supervisor Kubernetes **v1.30+**; **VKr 1.31 support dropped, minimum VKr
  1.32**; must be on VKS 3.3+ to upgrade directly.

**vSphere Supervisor 9.1.0.0** (released **2026-05-12**) bundles three Supervisor Kubernetes
versions: `v1.30.14+vmware.8-fips-vsc9.1.0.0`, `v1.31.11+vmware.8-fips-vsc9.1.0.0`,
`v1.32.9+vmware.2-fips-vsc9.1.0.0`. [S22]

### Cluster creation — which API

Per *About VKS Cluster Provisioning*: [S02]

| API | apiVersion | Status |
|---|---|---|
| **Cluster v1beta2** | `cluster.x-k8s.io/v1beta2` | "Latest API for managing the lifecycle of a Cluster based on a Cluster Class" — requires vCenter 8 U3+, vCenter 9+ |
| **Cluster v1beta1** | `cluster.x-k8s.io/v1beta1` | "Recommended API for managing the lifecycle of a Cluster based on a Cluster Class" — requires vCenter 8+ |
| TanzuKubernetesCluster v1alpha3 | (`run.tanzu.vmware.com/v1alpha3` — group string **UNVERIFIED**) | **Deprecated** |
| TanzuKubernetesCluster v1alpha2 | — | Deprecated (vCenter 7 U3 Supervisor) |

> "Starting with VKS 3.2, the TanzuKubernetesCluster API is deprecated. To provision new VKS
> clusters, use Cluster v1beta1 or v1beta2." [S02]

And harder, from VKS 3.4: "starting version 3.4, you won't be able to use the deprecated TKC API to
create Kubernetes 1.33 cluster." [S29] Cluster API "is now the default method for bootstrapping,
configuring, and managing Kubernetes clusters." [S29]

**So: for 9.0/9.1, teach `cluster.x-k8s.io/v1beta1` (or `v1beta2` on vCenter 9) + a ClusterClass. Do
not teach `TanzuKubernetesCluster`.**

ClusterClass is versioned and named `builtin-generic-v<VKS-version>` — e.g. `builtin-generic-v3.4.0`
[S29], `builtin-generic-v3.6.0` [S23]. Older ClusterClasses "remain available in all namespaces to
retain backwards compatibility," though deprecated. [S29]

Two supported client workflows: **kubectl** (declarative) and **VCF CLI** (interactive). [S02]

### The login flow — **`kubectl vsphere login` is gone from the 9.x docs**

This is the single biggest trap in this layer. In VCF 9.x documentation the Supervisor login flow is
**not** `kubectl vsphere login`. It is the **VCF CLI** (a.k.a. "VCF Consumption CLI"), binary `vcf`.

The download page — whose URL still carries the legacy slug
`download-and-install-the-kubernetes-cli-tools-for-vsphere.html` — now describes only the `vcf`
binary. Verified for both doc sets: [S30][S31]

- Package contains "an executable file: `vcf-cli-{os}_{arch}`, for example, `vcf-cli-darwin_amd64`."
- **No `kubectl` or `kubectl-vsphere` binaries are mentioned.** [S31]
- The phrase "Kubernetes CLI Tools for vSphere" "appears only in the page URL and metadata …, not in
  the actual page content." [S31]

**Getting the download link:** in the vSphere Client, navigate **Supervisor Management > Namespaces**,
select a vSphere Namespace, open the **Summary** tab, find the **Status** pane, and under **Link to
CLI Tools** click **Open** or **Copy Link**. [S30][S31]

**Install:** select OS → download `vcf-cli.tar.gz` (or `vcf-cli.zip`) → extract → **rename the
executable to `vcf`** and add its location to `PATH` → run `vcf` to verify (you get the VCF CLI
banner and command list). [S30][S31]

**Login (identical text in 9.0 and 9.1 doc sets):** [S24][S25]
```bash
vcf context create --help

vcf context create --endpoint <SUPERVISOR-ADDRESS> \
                   --username <VCENTER-SSO-USER> \
                   --ca-certificate <PATH-TO-CERTIFICATE-FILE>

# documented examples
vcf context create --endpoint 10.92.42.13        --username <sso-user> --ca-certificate ~/ca_root.cert
vcf context create --endpoint wonderland.example.com --username <sso-user> --ca-certificate ~/ca_root.cert
```
Password is entered interactively, **or** set the environment variable **`VCF_CLI_VSPHERE_PASSWORD`**.
[S24][S25]

**Context management:** [S24][S25][S03]
```bash
vcf context list                    # list available contexts
vcf context use <context-name>      # switch context
vcf context use cluster-1           # switch to a provisioned VKS cluster
```

`kubectl` itself is still used for everything after login [S03] — the VCF CLI writes the kubeconfig
context; `kubectl` consumes it. But the **login/credential step is `vcf`, not `kubectl vsphere`.**

Whether the legacy `kubectl-vsphere` plugin still ships and functions in 9.x for backward
compatibility is **UNVERIFIED — could not retrieve**: a targeted site-restricted search for
`"kubectl vsphere login"` across `vcf-9-0-and-later` returned no page containing that string, and
neither 9.0 nor 9.1 CLI-download or SSO-login pages mention it. Absence of evidence here is
suggestive but not proof of removal.

### VCF CLI

Current version **v9.1.0.0**, reported by `vcf version`. [S32]

> "The VMware Cloud Foundation command-line interface (VCF CLI) is a command-line tool that enables
> you to interact with VCF Consumption services." [S32]

Capabilities: create/manage contexts for vSphere Namespaces; create/manage workload clusters; manage
Kubernetes releases; install/manage packages on workload clusters; configure the CLI itself. [S32]
Installation paths documented for both internet-connected and internet-restricted (airgapped)
environments. [S32] First shipped in VCF 9.0 as "a new first-release CLI focused on 'context'
management for unified VCF environment interaction, supporting VCFA and vSphere Supervisor endpoints
with auto-discovery plugins and airgapped environment support." [S12]

**Command groups** — system commands: `completion`, `config`, `context`, `plugin`, `version`.
Plugin-based commands: `cluster`, `imgpkg`, `kubernetes-release`, `namespaces`, `package`, `pais`,
`registry-secret`, `secret`, `telemetry`, `vm`; plus an `addon` plugin for managing add-ons in VKS
clusters. [S33]

Other referenced commands: `vcf config set`, `vcf telemetry cli-usage-analytics update` (CEIP). [S32]

### kubectl provisioning workflow (verbatim command sequence)

From *Workflow for Provisioning VKS Clusters Using kubectl*: [S03]

```bash
# Prereqs: content library with compatible Kubernetes releases;
#          a configured vSphere Namespace to host VKS clusters.

# 1. Log in to the Supervisor and switch to the target namespace (vcf context create / vcf context use)

# 2. List available VM classes
kubectl get virtualmachineclass

# 3. Get storage classes for the namespace
kubectl describe namespace <VSPHERE-NAMESPACE>

# 4. List available Kubernetes releases
kubectl get kr
kubectl get kubernetesreleases

# 5. Author cluster YAML (Cluster v1beta1/v1beta2, referencing a ClusterClass):
#    cluster name, namespace, VM classes, storage class, node replicas, Kubernetes version

# 6. Apply
kubectl apply -f cluster-1.yaml
#    -> cluster.cluster.x-k8s.io/cluster-1 created

# 7. Monitor
kubectl get cluster

# 8/9. Log in to the VKS cluster with the VCF CLI once the control plane is ready
vcf context use cluster-1

# 10. Verify
kubectl get nodes
kubectl get namespaces
kubectl get pods -A
```

Note the storage-class discovery idiom is **`kubectl describe namespace <ns>`** (storage classes are
surfaced in the namespace description), not `kubectl get storageclass`. [S03] And Kubernetes releases
use the short name **`kr`** / full name **`kubernetesreleases`**. [S03]

### VM Service / VM Operator

The VM Operator API group is **`vmoperator.vmware.com`**. [S27]

**Version guidance differs between sources and this matters:**
- The **VCF 9.0 product docs** state: "Starting with VCF 9.0, the v1alpha1 version of the VM Operator
  API is deprecated. Use **v1alpha2 or v1alpha3** instead, as both are supported on Supervisor and
  are fully backward compatible." [S10]
- The **upstream open-source VM Operator project docs** (readthedocs, `docs-stable`) show
  `apiVersion: vmoperator.vmware.com/v1alpha5` and reference v1alpha1–v1alpha5. [S27]

The upstream project is ahead of what VCF 9.0 documents as supported. **For VCF 9.0, trust
v1alpha2/v1alpha3 [S10].** What the shipped Supervisor serves in **9.1** is
**UNVERIFIED — could not retrieve** — resolve it at runtime with `kubectl api-resources` /
`kubectl explain` rather than assuming.

Kinds under this group: `VirtualMachine`, `VirtualMachineService`, `VirtualMachineClass`,
`VirtualMachineImage`. [S27][S10]

**Supervisor 9.1 VM Service changes:** VM snapshot management; multiple network interfaces at create
time and as day-2 operations; infrastructure policies for VM affinity/anti-affinity placement. [S22]

### Other Supervisor 9.1 changes

- **Container Service** — new: "seamless deployment of individual containers without the complexity
  of managing or deploying a full Kubernetes cluster," using isolated runtime environments. [S22]
- **vSphere Zones** now support **multiple ESX clusters** per zone, growing capacity without
  modifying existing zone objects used by vSphere Namespaces. [S22]
- **VM Import** — non-disruptively import existing vSphere VMs onto Supervisors via the VCF-A VCD
  Migration Tool or API, with batch import and rollback. [S22]
- **Deployment regression to know about:** "Starting with VCF 9.1, the vSphere Client UI no longer
  supports deploying a Supervisor with classic NSX Segment Networking," though **API deployment
  remains supported.** [S22]

Supervisor deployment topologies documented in 9.1: VCF Networking with VPC; Foundation Load
Balancer; a "Simplified Deployment Flow" (easy Supervisor); NSX + Avi Load Balancer; vDS + Avi Load
Balancer; and deployment from an exported configuration. [S01]

---

## SDKs and OpenAPI specs

### Officially supported languages

The VCF SDKs support **Java** ("OpenJDK or JDK 11, JDK 17, and JDK 21"), **Python** ("Python 3.9 or
later"), **OpenAPI** ("REST" with "OpenAPI 3.0.1"), and **SOAP** "for legacy uses." [S34]

> The VCF 9.0 What's New page confirms only Java and Python: "**Go and .NET are not mentioned in this
> release.**" [S12]

So: **there is no first-party VCF Go SDK and no first-party VCF .NET SDK.** Non-Java/Python consumers
are expected to generate bindings from the OpenAPI specs — "Developers who use other programming
languages can use API definitions under the specifications folder to manually generate client code
and server stubs in many languages," using tools such as **openapi-generator**, producing clients "in
languages like Go, Java, or Python." [S35]

Legacy vSphere-specific SDKs for **.NET, Perl and Ruby** still appear on the developer portal but are
marked **deprecated** (for both the vSphere Automation and vSAN Management SDK families). [S36]

### VCF Python SDK

- PyPI package: **`vcf-sdk`** → `pip install vcf-sdk` [S37]
- Current version **9.1** [S37]
- Supports "Python versions 3.10, 3.11, 3.12, 3.13 and 3.14" [S37]
  (note: this is *stricter* than the generic "Python 3.9 or later" on the language-support page
  [S34] — see Gaps)
- GitHub: `https://github.com/vmware/vcf-sdk-python` [S37]
- Covers: VMware vSphere Foundation (pyVmomi, vSphere Automation, vSAN), SDDC Manager, VCF Installer,
  NSX, VCF Operations (Networks, Logs Management), Fleet Lifecycle, SDDC Lifecycle [S37]

### VCF Java SDK

- Maven: groupId **`com.vmware.sdk`**, artifactId **`vcf-sdk-bom`** (a BOM import) [S38]
- Current version **9.1** [S38]
- "compatible with the latest supported Java LTS versions: **11, 17, 21, 25**" [S38]
  (note: this exceeds the "11, 17, 21" on the language-support page [S34] — see Gaps)
- GitHub: `https://github.com/vmware/vcf-sdk-java` [S38]
- Same component coverage as the Python SDK [S38]
- Samples are "delivered separately"; in 9.1 the Java SDK samples build system **changed from Gradle
  to Maven** [S08][S38]

### VCF 9.0 SDK builds

Java SDK **9.0.0.0** and Python SDK **9.0.0.0**, both build **24798170**, both dated **2025-06-17** —
distributed via the developer portal, package managers (Maven Central, PyPI) and GitHub. [S12]

`{9.1}` SDK additions: Java and Python SDKs now additionally support **VMware NSX, VCF Operations,
Log Management, Fleet Lifecycle, SDDC Lifecycle, and VODAP** OpenAPI specifications, with enhanced
samples/docs delivered as separate ZIPs. [S08]

### Legacy / component SDKs on the developer portal [S36]

vSphere: Automation SDK for **Java** / **Python** / **REST**; vSphere Management SDK (Java); vSphere
Guest SDK (C); **pyVmomi**; vSphere Client SDK (Java). vSAN: Management SDK for **Java** / **Python**.
NSX: **VMware NSX for Java** / **VMware NSX for Python**. Deprecated variants exist in .NET, Perl and
Ruby for the vSphere Automation and vSAN families. Root: `https://developer.broadcom.com/sdks`.

For raw pyVmomi work the docs give: [S39]
```bash
pip install --upgrade pip
pip install --upgrade setuptools
pip install --upgrade pyvmomi
pip install --upgrade git+https://github.com/vmware/vsphere-automation-sdk-python.git
```
Entry points: `SmartConnect` (VIM/Web Services endpoint) and `create_vsphere_client` (Automation API
session); `ServiceInstance` is the root managed object. Community samples:
`https://github.com/vmware/pyvmomi-community-samples`. [S39]

### Where the OpenAPI specs actually live

**Two channels, both verified:**

**1. GitHub — `https://github.com/vmware/vcf-api-specs`** [S11][S35]
- "API specifications for the VMware VCF products."
- Layout: **`/specifications`** (all API definitions, organized by component), **`/scripts`** (example
  build scripts for generating language-specific bindings). Under
  `/specifications/vsphere/openapi` there are **`/automation`** and **`/vi-json`** variants (the two
  vSphere REST API flavors).
- Coverage: vSphere (WSDL **and** OpenAPI), NSX, SDDC Manager, VCF Installer, vSAN Data Protection,
  Fleet Lifecycle, SDDC Lifecycle, Operations, Operations for Networks, Log Management, Real-time
  Metrics.
- **Format gotcha:** "**NSX are OpenAPI 2.0 based unlike other VCF components which are based on
  OpenAPI 3.0.**" [S11] Generators must be told which spec version per component.
- Legacy WSDL references are included for EAM, PBM, SMS, VIM, vSAN and VSLM. [S35]

**2. Broadcom developer portal ZIP —
`https://developer.broadcom.com/sdks/vcf-api-specification/latest`** [S40]
- `{9.1}` artifact: **`vcf-api-specs-9.1.0.0-25372366.zip`** (39.36 MB).
- Covers eight products: "vSphere, NSX, SDDC Manager, VMware Cloud Foundation (VCF) Installer,
  VMware Cloud Foundation (VCF) Operations, VMware vSAN Data Protection (vSAN DP), SDDC Lifecycle,
  Fleet Lifecycle."
- vSphere ships as "WSDL, OpenAPI"; remaining components as OpenAPI.

The docs put it plainly: "You can find specifications to browse at **github.com/vmware/vcf-api-specs**,
or to download as a **Zip archive on the Broadcom developer website**." [S35]

A 9.0-equivalent spec ZIP filename was **UNVERIFIED — could not retrieve** (only `latest` = 9.1 was
fetched).

### API reference sites

- **VKS API reference:** `https://developer.broadcom.com/xapis/vmware-vsphere-kubernetes-service/latest/`
  — latest documented **3.6.0**, with **3.4.1** also available; the API-docs page is
  `.../latest/api-docs.html`. Whether a downloadable OpenAPI/Swagger file is offered there was
  **UNVERIFIED — could not retrieve**. [S41]
- **VCF CLI API:** `https://developer.broadcom.com/xapis/vcf-cli-api/latest/` (surfaced in search
  [S26-search]; contents **UNVERIFIED — could not retrieve**).
- **PowerCLI cmdlet reference:** `https://developer.broadcom.com/powercli/all-powercli-modules` [S18]

### On-appliance API explorers — mostly unresolved for 9.x

This is a real gap. What was verified:

- **VCF Operations for Networks** has an in-product **API Explorer**, documented at
  `.../9-0/administration-sdks-cli-and-tools/vmware-cloud-foundation-operations-for-networks-api-guide/understanding-the-rest-apis/using-api-explorer.html`
  [S42-search]. Page contents **UNVERIFIED — could not retrieve**.
- The **vCenter Developer Center / API Explorer** is documented for **vSphere 7.0 and 8.0** doc sets
  (`.../vsphere/vsphere/8-0/vcenter-and-host-management/working-with-the-developer-center-host-management.html`)
  [S43-search]. **No equivalent page was found in the `vcf-9-0-and-later` doc sets** by targeted
  site-restricted search.
- The 9.1 *VCF APIs and SDKs* overview page explicitly does **not** provide "API explorer appliance
  access points." [S43]
- The OpenAPI setup page explicitly states it does **not** specify on-appliance URLs "(like
  `/apiexplorer` or `/api` metadata endpoints) for retrieving OpenAPI specifications from running VCF
  components." [S35]

**Conclusion:** do **not** teach an on-appliance API-explorer URL pattern for VCF 9.x — none was
verifiable. Point at the GitHub repo and the spec ZIP instead. Whether the vCenter 9 Developer Center
still exists at its vSphere-8 UI location is **UNVERIFIED — could not retrieve**.

### `{9.1}` new VCF APIs

- **Utilization API** — monitors vCenter capacity metrics (active connections, service request
  volumes) with configurable threshold alarms. [S08]
- **vCenter Group Federated API (VGFA)** — "single unified API endpoint for managing all vCenter
  instances in a vCenter," consolidating inventory access across instances. [S08]
- **Query API** — extends Search Index; "fast, flexible, and scalable way to retrieve vSphere
  inventory data" with server-side filtering and pagination. [S08]

`{9.0}` new APIs: vCenter Authorization Management ("modern REST APIs to configure all aspects of
authorization … including privileges, roles"); **OpenAPI 3.0 support added to vCenter 9.0** alongside
the existing VI JSON and REST APIs; Guest OS Customization via vSphere Automation APIs "while
running." [S12]

---

## Discovery/lookup patterns

Teach these. The docs are thin on them, so most are standard-tooling idioms that happen to be the
right escape hatch when a cmdlet/CRD name isn't known.

### PowerShell / PowerCLI

**Doc-verified:** the only discovery idiom the VCF 9.1 PowerShell Basics page actually gives is: [S43b]

> "For a full list of the common parameters and more details on their usage, run
> `Get-Help about_CommonParameters`."

That page does **not** document `Get-Command` / `Get-Module` / `Get-Member` usage — flagged as a doc
gap, not a tooling gap.

**Recommended patterns** (standard PowerShell; not quoted from Broadcom docs — mark as such if
surfaced to users):

```powershell
# What VCF modules are installed / loaded?
Get-Module -ListAvailable VMware.*, VCF.*
Get-Module                                    # currently imported

# Which module owns a cmdlet, and what cmdlets does a module export?
Get-Command -Module VMware.Sdk.Vcf.SddcManager
Get-Command -Module VMware.VimAutomation.Nsxt
Get-Command -Noun *Sddc*                      # noun-first is the highest-signal search
Get-Command -Verb Connect                     # find every Connect-*Server entry point
Get-Command *Vsan*Capacity*                   # wildcard when only a concept is known

# Full syntax + examples + parameter semantics
Get-Help Connect-VcfSddcManagerServer -Full
Get-Help Connect-VcfSddcManagerServer -Examples
Get-Help Set-PowerCLIConfiguration -Parameter InvalidCertificateAction

# Inspect returned objects (PowerCLI returns rich typed objects, not text)
Get-VM | Get-Member
Get-VM | Select-Object -First 1 | Format-List *
```

**Why noun-first matters here:** the module split is by *product*, and the noun prefix tracks the
product — `*-Vcf*` (VCF SDK modules), `*-Sddc*` (SDDC Manager), `*-Vsan*`, `*-Nsx*`, `*-VI*` (core
vSphere). `Get-Command -Noun Sddc*` is the fastest route to the SDDC Manager surface, and it is how
you'd have found `Get-SddcTask` / `Remove-SddcCluster` [S08] without prior knowledge.

**Version self-check:**
```powershell
Get-Module VCF.PowerCLI -ListAvailable | Select-Object Name, Version
Get-PowerCLIConfiguration              # current scope settings incl. InvalidCertificateAction, CEIP
```
(`Get-PowerCLIConfiguration` is inferred as the read counterpart to `Set-PowerCLIConfiguration`
[S21][S13]; its reference page was **UNVERIFIED — could not retrieve**.)

### kubectl / Supervisor / VKS

**Doc-verified idioms** [S03]:
```bash
kubectl get virtualmachineclass          # available VM classes
kubectl describe namespace <ns>          # storage classes for the namespace
kubectl get kr                           # Kubernetes releases (short name)
kubectl get kubernetesreleases           # ...full name
kubectl get cluster                      # provisioning status
kubectl get nodes / namespaces / pods -A
```

**Recommended generic discovery** (standard kubectl; the docs do not present these, per [S28]):
```bash
kubectl api-resources                                  # every kind, its short name, group & namespaced-ness
kubectl api-resources --api-group=vmoperator.vmware.com
kubectl api-resources --api-group=cluster.x-k8s.io
kubectl api-versions | grep -E 'vmoperator|cluster.x-k8s|run.tanzu'

kubectl explain cluster.spec.topology                  # schema walk, served by the live API server
kubectl explain virtualmachine --recursive
kubectl get crd                                        # raw CRD list
kubectl get clusterclass -A                            # which builtin-generic-v3.x.0 exist here
```

`kubectl explain` and `kubectl api-resources` are the correct answer to the VM Operator version
ambiguity noted above (v1alpha2/v1alpha3 per VCF 9.0 docs [S10] vs v1alpha5 upstream [S27]): **query
the cluster, don't guess the served version.**

`kubectl get clusterclass -A` is the practical way to learn which ClusterClass to reference, since
the name is VKS-version-coupled (`builtin-generic-v3.4.0` [S29] / `builtin-generic-v3.6.0` [S23]).

### VCF CLI

```bash
vcf version                    # verified: reports v9.1.0.0            [S32]
vcf context create --help      # verified: doc-recommended syntax check [S24][S25]
vcf context list               # verified                               [S24][S25]
vcf plugin                     # verified command group                 [S33]
```
Command groups worth enumerating: `context`, `plugin`, `config`, `version`, `completion` (system);
`cluster`, `namespaces`, `kubernetes-release`, `package`, `vm`, `secret`, `registry-secret`,
`imgpkg`, `pais`, `telemetry`, `addon` (plugins). [S33]

Because the CLI is plugin-based, `vcf plugin list` (inferred form) is the way to see what is actually
installed in a given environment — plugin availability is context-dependent and auto-discovered from
the endpoint [S12]. Exact `vcf plugin` subcommand syntax was **UNVERIFIED — could not retrieve**.

---

## 9.0 → 9.1 Deltas

**PowerCLI**
| Delta | Detail |
|---|---|
| Module version | `9.0.0.24798382` (2025-06-17) → `9.1.0.25380678` (2026-05-12) [S05][S06][S07] |
| Component modules | `13.4.0.24798382` → `13.5.0.25380678`; `VMware.Vim` `9.0.0.*` → `9.1.0.*` [S05][S07] |
| **Module added** | **`VMware.Vcf.Sso`** (1 new command) [S07][S09] |
| **Module removed** | **`VMware.PowerCLI.VCenter`** dropped from the meta-module dependency set [S07][S05] |
| New cmdlets (named) | `Get-VsanEffectiveCapacity`, `Remove-SddcCluster`, `Remove-SddcDomain`, `Remove-SddcHost`, `Get-SddcTask` [S08] |
| New cmdlets (counted) | `.Vpc` +33, `.Vcf.SddcManager` +4, `.Storage` +3, `.Vcf.Sso` +1 [S09] |
| Auth | `VcfOAuthSecurityContext` (OAuth) and `VcfApiToken` parameters introduced [S08] |
| Python | 3.13 supported; **3.7 and 3.8 deprecated** [S08] |
| Deprecations | changelog reports **0 deprecated, 0 deleted** commands [S09] — which sits oddly against the `VMware.PowerCLI.VCenter` removal (see Gaps) |

**SDKs / APIs**
| Delta | Detail |
|---|---|
| SDK version | Java & Python 9.0.0.0 (build 24798170) → 9.1 [S12][S37][S38] |
| Java LTS | 11/17/21 → **11/17/21/25** [S34][S38] |
| Python | 3.9+ → **3.10–3.14** for `vcf-sdk` [S34][S37] |
| Coverage added | NSX, VCF Operations, Log Management, Fleet Lifecycle, SDDC Lifecycle, VODAP OpenAPI specs [S08] |
| Samples | delivered as separate ZIPs; **Java samples build moved Gradle → Maven** [S08] |
| New APIs | Utilization API; **vCenter Group Federated API (VGFA)**; Query API [S08] |
| Spec bundle | `vcf-api-specs-9.1.0.0-25372366.zip`, 39.36 MB, 8 products [S40] |

**Supervisor / VKS**
| Delta | Detail |
|---|---|
| VKS era | 3.4.x (K8s 1.33, `builtin-generic-v3.4.0`) → 3.6.x (K8s 1.35, `builtin-generic-v3.6.0`); 3.7 page exists [S29][S23][S26] |
| Supervisor | 9.1.0.0 (2026-05-12) bundles Supervisor K8s v1.30.14 / v1.31.11 / v1.32.9 (all `-fips-vsc9.1.0.0`) [S22] |
| Scale | **up to 500 VKS clusters per Supervisor (2.5x)** [S23] |
| Networking | Antrea **hybrid encapsulation mode**, up to 40% perf gain; multi-network secondary interfaces [S23] |
| New service | **Container Service** — run individual containers without a full K8s cluster [S22] |
| VM Service | snapshots; multiple NICs at create + day-2; affinity/anti-affinity infrastructure policies [S22] |
| Zones | multiple ESX clusters per vSphere Zone [S22] |
| **Regression** | "Starting with VCF 9.1, the vSphere Client UI no longer supports deploying a Supervisor with classic NSX Segment Networking" (API still supported) [S22] |
| Node images | ImageBaker replaces Image Builder for RHEL-based node images [S23] |
| VKr floor | VKr 1.31 dropped; **minimum VKr 1.32** [S23] |
| Login flow | **unchanged** — `vcf context create` in both 9.0 and 9.1, identical documented syntax [S24][S25] |
| CLI | VCF CLI first release in 9.0 [S12]; v9.1.0.0 current [S32] |

---

## Gaps and Ambiguities

1. **`VMware.PowerCLI.VCenter` removal vs "0 deleted commands."** The 9.1 changelog reports zero
   deprecated and zero deleted commands [S09], yet `VMware.PowerCLI.VCenter` is present in the 9.0
   dependency set and absent from 9.1 [S05][S07]. Most likely the module's cmdlets were folded
   elsewhere (or the module still installs standalone and merely left the meta-module), but this is
   **not resolved**. Do not tell users cmdlets were removed; do warn that a script importing
   `VMware.PowerCLI.VCenter` explicitly may break under `{PCLI 9.1.0}`.

2. **A first-pass page summary was wrong.** An initial read of the 9.1 Gallery page asserted "no
   module additions or removals" while its own rendered table showed otherwise. Both deltas were
   re-verified by direct yes/no interrogation. Lesson worth carrying: for dependency/version lists,
   verify by pointed question, not by narrative summary. (The PowerShell Gallery OData API at
   `/api/v2/Packages(...)` returns binary/unparseable content through the fetch path and `curl` is
   blocked by the agent proxy with `CONNECT tunnel failed, 403`, so the HTML page is the only
   available channel.)

3. **`kubectl vsphere login` — removed, or merely undocumented?** No page in `vcf-9-0-and-later`
   surfaced containing that string, and the CLI-download page for both 9.0 and 9.1 describes only the
   `vcf` binary [S30][S31]. But the page *URL slug* is still
   `download-and-install-the-kubernetes-cli-tools-for-vsphere.html`, which hints at an in-place
   rewrite of a page that used to ship `kubectl-vsphere`. Whether the plugin still ships for backward
   compatibility is **unresolved**. Teach `vcf context create` as the answer; don't assert the plugin
   is gone.

4. **VM Operator API version served in 9.1.** VCF 9.0 docs say v1alpha2/v1alpha3 [S10]; upstream
   open-source docs show v1alpha5 [S27]. No VCF 9.1 page stating the served versions was retrieved.
   Resolve per-cluster with `kubectl api-resources --api-group=vmoperator.vmware.com`.

5. **VKS ↔ VCF version binding is inferred, not documented.** VKS 3.4.0 and VCF 9.0 share a release
   date; VKS 3.6.1 is described as carrying "VCF 9.1 enhancements" [S29][S23][S12]. But VKS release
   notes describe compatibility as "vSphere 9.x and 8.x," not as a VCF-release binding [S23][S29] —
   VKS is installed/upgraded as a Supervisor service on its own cadence. Present the mapping as
   typical alignment, not as a guarantee.

6. **VKS 3.5 and 3.7 release notes not fetched.** Pages exist [S26]; contents unknown. 3.7 in
   particular may already be the current release as of 2026-07-31 — the VKS API reference site lists
   "latest documented version 3.6.0" [S41], which conflicts with a 3.7 release-notes page existing.
   Unresolved.

7. **On-appliance API explorer URLs for VCF 9.x: not found.** Documented for vSphere 7/8 only
   [S43-search]; the 9.1 overview page and the OpenAPI setup page both explicitly lack them
   [S43][S35]. Only VCF Operations for Networks has a confirmed in-product API Explorer doc page
   [S42-search], itself unfetched. **Do not invent a URL pattern.**

8. **`TanzuKubernetesCluster` API group string.** The kind and versions (v1alpha2/v1alpha3, both
   deprecated) are documented [S02], but the literal group (`run.tanzu.vmware.com`) was not confirmed
   on a fetched page. Deprecated anyway — low value to chase.

9. **Python/Java version ranges disagree between pages.** Language-support page: Python 3.9+, JDK
   11/17/21 [S34]. Product SDK pages: Python 3.10–3.14 [S37], Java 11/17/21/25 [S38]. The product
   pages are 9.1-current and more specific; prefer them, but the discrepancy is real.

10. **CEIP cmdlet syntax not captured.** The configuring page lists CEIP as a topic [S13] but the
    child page was not fetched; the exact `Set-PowerCLIConfiguration -ParticipateInCEIP` form is
    **unverified**. Same for the offline-install command sequence [S16] and
    `Get-PowerCLIConfiguration`.

11. **`Connect-NsxtServer` and `Connect-CisServer` reference pages not fetched.** Module existence is
    confirmed [S18][S04]; cmdlet parameter sets are not. Note the naming inconsistency already
    visible in what *was* verified: `Connect-VIServer` uses `-Force` for certificate bypass [S19]
    while `Connect-VcfSddcManagerServer` uses `-IgnoreInvalidCertificate` [S20]. Assume nothing about
    the NSX cmdlet's parameter names.

12. **`VMware.PowerCLI` (legacy meta-module) status.** Backward compatibility "is maintained" [S12],
    but the legacy package's current version and whether it simply aliases `VCF.PowerCLI` was not
    verified.

13. **`vcf plugin` subcommand syntax** (e.g. `vcf plugin list` / `install`) not verified; only the
    command group name is confirmed [S33].

14. **`developer.broadcom.com/powercli/latest/products/vcfsddcmanager/`** returned "PowerCLI Details
    Page is temporarily unavailable" at fetch time — the per-product cmdlet index for SDDC Manager
    could not be enumerated. Retry later for a full cmdlet list.

---

## Source Inventory

All accessed **2026-07-31**.

| ID | URL | Doc set / version | Covers |
|---|---|---|---|
| S01 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-supervisor-installation-and-configuration.html | VCF 9.1 | Supervisor Platform section index; deployment topologies |
| S02 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-0/managing-vsphere-kuberenetes-service-clusters-and-workloads/provisioning-tkg-service-clusters/about-tkg-cluster-provisioning.html | VCF Service Admin & Dev 9.0 | VKS provisioning APIs, CAPI/CAPV, v1beta1/v1beta2, TKC deprecation |
| S03 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-0/managing-vsphere-kuberenetes-service-clusters-and-workloads/provisioning-tkg-service-clusters/workflow-for-provisioning-tkg-clusters-using-kubectl.html | VCF Service Admin & Dev 9.0 | kubectl provisioning workflow, verbatim commands |
| S04 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-vsphere-powercli-specific-concepts.html | VCF 9.1 | PowerCLI concepts; `$DefaultVIServers` / `$DefaultCIServers` |
| S05 | https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382 | PS Gallery | VCF.PowerCLI 9.0 dependency list, publish date, install cmd |
| S06 | https://www.powershellgallery.com/packages/VCF.PowerCLI | PS Gallery | Version history (9.0.0.24798382, 9.1.0.25380678) |
| S07 | https://www.powershellgallery.com/packages/VCF.PowerCLI/9.1.0.25380678 | PS Gallery | VCF.PowerCLI 9.1 dependency list; Sso added / VCenter removed |
| S08 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | VCF 9.1 | 9.1 What's New: CLI/API/SDK, new cmdlets, new APIs |
| S09 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-powercli-changelog.html | VCF 9.1 | PowerCLI 9.1 changelog counts per module |
| S10 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-cloud-applications/provision-and-manage-virtual-machines/deploying-and-managing-virtual-machines-in-vsphere-iaas-control-plane.html | VCF 9.0 | VM Service; VM Operator v1alpha1 deprecation, v1alpha2/v1alpha3 |
| S11 | https://github.com/vmware/vcf-api-specs/blob/main/README.md | GitHub main | OpenAPI spec repo layout, components, OpenAPI 2.0 vs 3.0 |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html | VCF 9.0 | 9.0 What's New: VCF.PowerCLI rename, SDK builds, VCF CLI intro |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/configuring-vmware-vsphere-powercli.html | VCF 9.1 | Configuration topics: certs, timeout, scopes, Python, CEIP |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli.html | VCF 9.1 | PowerCLI section index; full child-page list |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli/install-powercli.html | VCF 9.1 | `Install-Module VCF.PowerCLI -Scope CurrentUser`, `Import-Module` |
| S16 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli.html | VCF 9.1 | Install section index; offline-install existence |
| S17 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-powercli-compatibility-matrix.html | VCF 9.1 | PowerShell 7.x; 5.1 deprecated; OS & .NET prereqs; interop matrix pointer |
| S18 | https://developer.broadcom.com/powercli/all-powercli-modules | developer portal (latest) | Module → cmdlet-reference URL map |
| S19 | https://developer.broadcom.com/powercli/latest/vmware.vimautomation.core/commands/connect-viserver | developer portal (latest) | `Connect-VIServer` syntax and parameters |
| S20 | https://developer.broadcom.com/powercli/latest/vmware.sdk.vcf.sddcmanager/commands/connect-vcfsddcmanagerserver | developer portal (latest) | `Connect-VcfSddcManagerServer` full syntax |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/power-cli/latest/powercli/configuring-vmware-vsphere-powercli/configuring-powercli-invalid-server-certificate-actions/configure-invalid-server-certificate-action.html | PowerCLI doc set (latest) | `-InvalidCertificateAction` values, default, Linux/macOS limits |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vmware-vsphere-supervisor-release-notes.html | VCF Service Admin & Dev 9.1 | Supervisor 9.1.0.0 versions, Container Service, VM Service, NSX UI regression |
| S23 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes/vmware-tanzu-kubernetes-grid-service-36-release-notes.html | VCF Service Admin & Dev 9.1 | VKS 3.6.x versions/dates, K8s 1.35, ClusterClass, 9.1 features |
| S24 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html | VCF 9.0 | `vcf context create` login, env var, context commands |
| S25 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html | VCF 9.1 | Same login flow, 9.1; no kubectl vsphere mention |
| S26 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes.html | VCF Service Admin & Dev 9.1 | VKS release-notes index: 3.3/3.4/3.5/3.6/3.7 |
| S27 | https://vm-operator.readthedocs.io/en/docs-stable/concepts/services-networking/vm-service/ | upstream OSS (docs-stable) | `vmoperator.vmware.com` group; v1alpha1–v1alpha5; kinds |
| S28 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/managing-vsphere-kubernetes-service/running-tkg-service-clusters/tkg-service-components.html | VCF Service Admin & Dev 9.1 | VKS components, controller layers, CNI/CSI/auth/LB |
| S29 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes/vmware-tanzu-kubernetes-grid-service-34-release-notes.html | VCF Service Admin & Dev 9.1 | VKS 3.4.x versions/dates, K8s 1.33, `builtin-generic-v3.4.0`, TKC cutoff |
| S30 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/download-and-install-the-kubernetes-cli-tools-for-vsphere.html | VCF 9.0 | VCF Consumption CLI download/install; `vcf-cli-{os}_{arch}` |
| S31 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/download-and-install-the-kubernetes-cli-tools-for-vsphere.html | VCF 9.1 | Same, 9.1; confirms no kubectl/kubectl-vsphere in package |
| S32 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-consumption/latest/consumer-interfaces-in-vcf/installing-and-using-vcf-cli-v9.html | VCF Consumption (latest) | VCF CLI v9.1.0.0, capabilities, install modes |
| S33 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-consumption/latest/consumer-interfaces-in-vcf/installing-and-using-vcf-cli-v9/command-reference2.html | VCF Consumption (latest) | VCF CLI command groups and plugin list |
| S34 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/programming-language-support-in-the-vsphere-web-services-sdk.html | VCF 9.1 | Supported languages: Java, Python, OpenAPI 3.0.1, SOAP |
| S35 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi.html | VCF 9.0 | Spec download channels; openapi-generator; no on-appliance URLs |
| S36 | https://developer.broadcom.com/sdks | developer portal | Full SDK catalogue incl. deprecated .NET/Perl/Ruby |
| S37 | https://developer.broadcom.com/vcf-python-sdk | developer portal | `vcf-sdk` PyPI, v9.1, Python 3.10–3.14, GitHub, coverage |
| S38 | https://developer.broadcom.com/vcf-java-sdk | developer portal | `com.vmware.sdk:vcf-sdk-bom`, v9.1, Java 11/17/21/25, GitHub |
| S39 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/getting-started-with-vsphere-apis-and-sdks/python-access-to-vsphere-apis.html | VCF 9.0 | pyVmomi install, SmartConnect, community samples |
| S40 | https://developer.broadcom.com/sdks/vcf-api-specification/latest | developer portal | `vcf-api-specs-9.1.0.0-25372366.zip`, 39.36 MB, 8 products |
| S41 | https://developer.broadcom.com/xapis/vmware-vsphere-kubernetes-service/latest/ | developer portal | VKS API reference; versions 3.6.0 / 3.4.1; api-docs.html |
| S43 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development.html | VCF 9.1 | VCF APIs & SDKs overview; API categories; explicit absence of explorer URLs |
| S43b | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/microsoft-powershell-basics.html | VCF 9.1 | PowerShell basics; `Get-Help about_CommonParameters` |
| S44 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | "Administration SDKs, APIs, and CLI" section index (9 subsections) |
| S45 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | Top-level doc-set index |
| S46 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk.html | VCF 9.1 | SDK Developer's Setup Guide child-page list |
| S47 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters.html | VCF 9.1 | "Connecting to Supervisor and VKS Clusters" index; VCF Consumption CLI framing |
| S48 | https://developer.broadcom.com/powercli | developer portal | PowerCLI landing: 9.1/9.0, install guide, changelog, reference URLs |
| S49 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes.html | VCF Service Admin & Dev 9.1 | Release-notes index (Supervisor, VKS, VKr, Standard Packages) |
| S50 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-0/release-notes.html | VCF Service Admin & Dev 9.0 | 9.0 release-notes index |

**Search-only sources** (result listings used to locate URLs; not themselves fact sources):
`S26-search` (VCF CLI / consumption CLI query, surfaced `developer.broadcom.com/xapis/vcf-cli-api/latest/`),
`S42-search` (VCF Operations for Networks "Using API Explorer" page URL),
`S43-search` (vCenter Developer Center / API Explorer — vSphere 7.0 & 8.0 doc sets only).

**Retrieval failures encountered:**
- `https://developer.broadcom.com/powercli/latest/products/vcfsddcmanager/` — "PowerCLI Details Page is temporarily unavailable."
- `https://techdocs.broadcom.com/.../9-1/.../configuring-vmware-powercli-response-to-untrusted-certificates.html` — HTTP 404 (correct path is under `configuring-powercli-invalid-server-certificate-actions/`; the 9.0 variant returned HTTP 403, the `power-cli/latest` variant [S21] succeeded).
- `https://www.powershellgallery.com/api/v2/Packages(...)` — returns binary/unparseable content via fetch; `curl` blocked by agent proxy (`CONNECT tunnel failed, 403`).
- `https://techdocs.broadcom.com/.../vcf-service-administration-and-development/9-1.html` — JS-only shell, no navigable content.
- `https://techdocs.broadcom.com/.../vcf-service-administration-and-development/9-0/release-notes/vmware-tanzu-kubernetes-grid-service-release-notes.html` — redirect stub pointing to the 9.1 site.
