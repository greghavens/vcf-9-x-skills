# VCF 9.0 — vSphere Supervisor and VKS Reference

**Scope:** the vSphere Supervisor and vSphere Kubernetes Service (VKS) as documented for
VCF 9.0. Everything is `[DOC-9.0]` unless tagged otherwise.

**There is no VKS OpenAPI spec in this corpus.** The bundled spec inventory
(`github.com/vmware/vcf-api-specs`, tags `9.0.0.0` / `9.1.0.0`) carries no VKS or Supervisor
product. So nothing in this file can be *spec-confirmed* the way an SDDC Manager endpoint
can. Evidence here is **doc-grade** (a Broadcom page was fetched) or **cluster-grade** (you
run a command and the API server answers). Cluster-grade beats doc-grade — see
[Discovery first](#discovery-first-and-why-it-is-not-optional).

**Evidence tags used throughout:**

| Tag | Meaning |
|---|---|
| `[DOC-9.0]` | Stated on a fetched page in a VCF 9.0 doc set |
| `[DOC-9.1]` | Stated on a fetched page in a VCF 9.1 doc set (used here where the 9.0 equivalent was not fetched, or for VKS release notes, which are published only in the 9.1 tree) |
| `[DOC-BOTH]` | Verified on fetched pages in *both* doc sets |
| `[UPSTREAM]` | Upstream open-source project documentation, not Broadcom |
| `[UNVERIFIED]` | Not established by any fetched source. Never fill these in from memory |

**A tagging wrinkle worth knowing.** VKS release notes for **every** VKS version (3.3 → 3.7)
live in the *VCF Service Administration and Development 9.1* doc set, so a fact about VKS 3.4
carries `[DOC-9.1]` even though the VKS 3.4 era is the one that lines up with VCF 9.0. That
is a hosting artifact, not evidence about which VCF release it applies to. VKS versions and
VCF versions are separate axes — see prerequisite **P8** below.

**Source keys.** `DTOOL` = `research/tooling-powercli-vks-sdk.md` (its own `Sxx` IDs are
carried through); `DAUTH` = `research/foundation-auth-identity.md`; `DCORE` =
`research/vcf-core-9.1-and-deltas.md`.

> **Built from documentation captured 2026-07-31, not validated live.** Cluster deletion and
> ClusterClass changes are destructive — verify before executing. See
> [Destructive operations](#destructive-operations).

---

## Contents

- [Prerequisites](#prerequisites)
  - P1 — Supervisor enabled on the cluster
  - P2 — vSphere Namespace created and permissions assigned
  - P3 — A VM class is assigned to the namespace
  - P4 — A storage policy is assigned to the namespace
  - P5 — Content library with Kubernetes release images
  - P6 — The `vcf` CLI is installed
  - P7 — CA certificate available for `--ca-certificate`
  - P8 — Know which VKS version the Supervisor runs
  - P9 — Items the research could not verify
- [Login and context](#login-and-context)
- [Discovery first, and why it is not optional](#discovery-first-and-why-it-is-not-optional)
- [Which provisioning API](#which-provisioning-api)
- [Provisioning a cluster with kubectl](#provisioning-a-cluster-with-kubectl)
- [VM Service and VM Operator](#vm-service-and-vm-operator)
- [What VKS is made of](#what-vks-is-made-of)
- [Destructive operations](#destructive-operations)
- [UNVERIFIED inventory for 9.0](#unverified-inventory-for-90)
- [Source map](#source-map)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what
must hold, **how to verify it**, the version it applies to, and whether 9.1 differs.

### P1 — Supervisor enabled on the cluster `[DOC-9.0]`

**Must be true:** a vSphere Supervisor must be deployed and enabled. VKS runs *on* the
Supervisor, and for cluster provisioning **the Supervisor is the Cluster API management
cluster** [DTOOL S02]. The 9.0 BOM row is `VMware vSphere Supervisor 9.0.0.0` build
`24686447` [DCORE §2.1].

**How to verify:** in the vSphere Client, **Supervisor Management > Namespaces** lists
namespaces and their **Summary > Status** pane [DOC-BOTH, DTOOL S30/S31]. From a client,
the practical check is that a context can be created (P6/P7) and `kubectl api-resources`
answers. **`[UNVERIFIED]`** — no REST endpoint for "is a Supervisor enabled here" was
captured in this corpus; do not invent one, and see `vcf-api-discovery` if a caller needs
one.

**9.1 difference:** Supervisor is `9.1.0.0` build `25370922` [DOC-9.1, DCORE §2] and bundles
three Supervisor Kubernetes versions [DOC-9.1]. Also a 9.1-only deployment regression: the
vSphere Client UI no longer supports deploying a Supervisor with classic NSX Segment
Networking, though API deployment remains supported [DOC-9.1, DTOOL S22].

### P2 — vSphere Namespace created and permissions assigned `[DOC-9.0]`

**Must be true:** a vSphere Namespace must exist to host VKS clusters — the documented
prerequisite for the kubectl provisioning workflow is "a configured vSphere Namespace to
host VKS clusters" [DTOOL S03]. The namespace is the tenancy boundary that "enables
self-service consumption of 3 runtimes … Virtual Machines, VKS clusters, vSphere Pods"
[DOC-9.1, DTOOL S28 — stated on the 9.1 components page; the 9.0 equivalent page was not
fetched].

Authorization model, identical in both doc sets: roles are sets of privileges, and
permissions are granted by "associating a role to a user or group on that object" in the
vCenter hierarchy; vCenter SSO is the token issuer [DOC-BOTH, DAUTH S33/S34].

**How to verify:** `kubectl get namespace <ns>` and `kubectl describe namespace <ns>` once a
context exists; the vSphere Client namespace list otherwise.

**`[UNVERIFIED]`** — the named namespace roles (owner / edit / view) were **not** confirmed
on any fetched 9.0 or 9.1 page [DAUTH §11]. Do not state them.

**9.1 difference:** external IDPs (Okta, Entra/Azure AD) integrate through **Pinniped
Supervisor and Concierge** [DOC-9.1, DAUTH], and a VCF-Automation-registered Supervisor
accepts an API token — see `../9.1/vks.md`.

### P3 — A VM class is assigned to the namespace `[DOC-9.0]`

**Must be true:** the cluster manifest names VM classes for its nodes, so classes must be
available in the namespace.

**How to verify:**

```bash
kubectl get virtualmachineclass
```

That command is doc-verified [DTOOL S03]. *Inference, flagged as such:* an empty result
means no class is assigned to this namespace, and a cluster referencing one will not
schedule — the docs do not spell that out.

**9.1 difference:** none documented for the discovery command itself. `VirtualMachineClass`
is a kind in the `vmoperator.vmware.com` group [DTOOL S27/S10].

### P4 — A storage policy is assigned to the namespace `[DOC-9.0]`

**Must be true:** the manifest names a storage class, which comes from a storage policy
assigned to the vSphere Namespace.

**How to verify — and this one is counter-intuitive:**

```bash
kubectl describe namespace <VSPHERE-NAMESPACE>
```

Storage classes are surfaced in the **namespace description**. The documented workflow step
is literally "Get storage classes for the namespace" via `kubectl describe namespace`, **not**
`kubectl get storageclass` [DTOOL S03]. If someone reports "no storage classes", check that
they ran the documented command before concluding the policy is missing.

**9.1 difference:** none captured.

### P5 — Content library with Kubernetes release images `[DOC-9.0]`

**Must be true:** the documented prerequisite is "content library with compatible Kubernetes
releases" [DTOOL S03]. Without it there is nothing to install on the nodes.

**How to verify:**

```bash
kubectl get kr                    # short name
kubectl get kubernetesreleases    # full name
```

Both forms are doc-verified [DTOOL S03]. The release you intend to reference must appear
here.

**`[UNVERIFIED]`** — the content-library *creation and subscription* procedure (URL, sync
mode, which library type) was not captured; that page was not fetched.

**9.1 difference:** the available releases move with the VKS version. VKS 3.6 raises the
floor: **VKr 1.31 support is dropped, minimum VKr 1.32** [DOC-9.1, DTOOL S23].

### P6 — The `vcf` CLI is installed `[DOC-BOTH]`

**Must be true:** login is the VCF CLI, binary `vcf`. The download page — still at the legacy
slug `download-and-install-the-kubernetes-cli-tools-for-vsphere.html` — describes **only**
the `vcf` binary in both doc sets. No `kubectl` and no `kubectl-vsphere` binary is mentioned
in the package [DOC-BOTH, DTOOL S30/S31].

**Where to get it:** vSphere Client → **Supervisor Management > Namespaces** → select the
namespace → **Summary** tab → **Status** pane → **Link to CLI Tools** → **Open** or **Copy
Link** [DOC-BOTH].

**Install:** select OS → download `vcf-cli.tar.gz` (or `.zip`) → extract → **rename the
executable to `vcf`** → add its directory to `PATH`. The package contains
`vcf-cli-{os}_{arch}`, e.g. `vcf-cli-darwin_amd64` [DOC-BOTH].

**How to verify:** run `vcf` — you get the CLI banner and command list [DOC-BOTH]. `vcf
version` reports the CLI version (**v9.1.0.0** on the current Consumption CLI page)
[DOC-9.1, DTOOL S32].

*Inference, flagged:* since the package ships no `kubectl`, `kubectl` must be obtained
separately. The docs do not say where from.

**9.1 difference:** none in the documented install text.

### P7 — CA certificate available for `--ca-certificate` `[DOC-BOTH]`

**Must be true:** `vcf context create` takes `--ca-certificate <PATH>`; the documented
examples use `~/ca_root.cert` [DOC-BOTH, DTOOL S24/S25]. VCF components are VMCA-signed by
default, i.e. not publicly trusted, so a stock client fails chain validation until the CA is
supplied or the certificates are replaced [DAUTH §3].

**How to verify:** the file exists and `vcf context create` completes without a TLS error.

**Note on practice:** `--ca-certificate` is the documented path for pinning a private CA in a
VCF client [DAUTH]. **No fetched Broadcom page documents disabling TLS verification as a
supported practice** — do not offer it as the fix.

**9.1 difference:** `--ca-certificate` also appears in the 9.1 API-token flow for
VCF-Automation-registered Supervisors [DOC-9.1, DAUTH].

### P8 — Know which VKS version the Supervisor runs `[DOC-9.0]` + `[UNVERIFIED]`

This is the prerequisite people skip, and it determines the ClusterClass name in the
manifest.

**What is documented:** the **VCF 9.0 BOM lists `VMware vSphere Kubernetes Service 3.3.1`**
(no build number) [DOC-9.0, DCORE §2.1]. Separately, **VKS 3.4.0 released on 2025-06-17, the
same date as VCF 9.0** [DOC-9.1, DTOOL S29/S12], and VKS 3.4 is described as "generally
available for use with vSphere 9.0 and vSphere 8.x" [DOC-9.1, DTOOL S29].

**What is not documented:** any hard "VKS X ships with VCF Y" binding. VKS installs and
upgrades as a Supervisor service on its own cadence, and its release notes describe
compatibility as "vSphere 9.x and 8.x" [DOC-9.1, DTOOL S23/S29]. So a 9.0 estate may be on
3.3.1 (the GA BOM row), on 3.4.x, or on something later. **`[UNVERIFIED]`** — the
ClusterClass name shipped by VKS **3.3.x** was not captured; the 3.3 release notes were not
fetched. `builtin-generic-v3.4.0` is documented for 3.4 [DOC-9.1, DTOOL S29].

**How to verify — the only reliable route:**

```bash
kubectl get clusterclass -A
```

Older ClusterClasses "remain available in all namespaces to retain backwards compatibility",
though deprecated [DOC-9.1, DTOOL S29] — so expect more than one, and pick deliberately
rather than taking the first row.

**9.1 difference:** the 9.1 BOM contains rows for `VMware vSphere Kubernetes Service`,
`vSphere Kubernetes releases` and `VKS Standard Packages`, but **the version numbers on those
rows were not captured** [`[UNVERIFIED]`, DCORE §2]. The 9.1-era VKS line is 3.6.x,
ClusterClass `builtin-generic-v3.6.0` [DOC-9.1].

### P9 — Items the research could not verify

Do not fill these from memory. They are listed in full in
[UNVERIFIED inventory](#unverified-inventory-for-90); the ones that bite during setup are:
namespace role names, the content-library procedure, whether `kubectl-vsphere` still ships,
and the VKS version actually installed.

---

## Login and context

Identical documented text in the 9.0 and 9.1 doc sets `[DOC-BOTH]` [DTOOL S24/S25].

```bash
vcf context create --help          # the docs recommend checking syntax first

vcf context create --endpoint <SUPERVISOR-ADDRESS> \
                   --username <VCENTER-SSO-USER> \
                   --ca-certificate <PATH-TO-CERTIFICATE-FILE>

# documented examples
vcf context create --endpoint 10.92.42.13 --username <sso-user> --ca-certificate ~/ca_root.cert
vcf context create --endpoint wonderland.example.com --username <sso-user> --ca-certificate ~/ca_root.cert
```

The password is entered interactively, **or** supplied through the environment variable
**`VCF_CLI_VSPHERE_PASSWORD`** [DOC-BOTH].

A named-context form with an explicit type also appears in the authorization pages
`[DOC-BOTH]` [DAUTH S33/S34]:

```bash
vcf context create <context_name> --endpoint=<SUPERVISOR_ENDPOINT> --type=k8s --username=<user_name>
```

Context management [DOC-BOTH, DTOOL S24/S25/S03]:

```bash
vcf context list                   # available contexts
vcf context use <context-name>     # switch context
vcf context use cluster-1          # switch to a provisioned VKS cluster
```

The CLI writes the kubeconfig (`.kube/config`) and the resulting credential is a
kubeconfig-managed bearer token [DOC-BOTH, DAUTH]. **`kubectl` is used for everything after
login** [DOC-9.0, DTOOL S03].

**On `kubectl vsphere login`.** No page in the `vcf-9-0-and-later` doc set surfaced containing
that string, and neither version's CLI-download or SSO-login page mentions the plugin
[DOC-BOTH]. But the download page's URL slug is still
`download-and-install-the-kubernetes-cli-tools-for-vsphere.html`, which suggests an in-place
rewrite of a page that used to ship `kubectl-vsphere`. **`[UNVERIFIED]` — removed, or merely
undocumented, is unresolved.** Teach `vcf context create`; do not assert the plugin is gone.

**VCF CLI command groups** [DOC-9.1, DTOOL S33] — system: `completion`, `config`, `context`,
`plugin`, `version`; plugin-based: `cluster`, `imgpkg`, `kubernetes-release`, `namespaces`,
`package`, `pais`, `registry-secret`, `secret`, `telemetry`, `vm`, plus an `addon` plugin for
VKS clusters. The CLI is plugin-based and **plugin availability is context-dependent**, so
"does command X exist" is only answerable against a live context. Exact `vcf plugin`
subcommand syntax is **`[UNVERIFIED]`**.

---

## Discovery first, and why it is not optional

This section is the reason the skill exists, so treat it as procedure rather than advice.

**The documented contradiction.** The VCF 9.0 product docs say: "Starting with VCF 9.0, the
v1alpha1 version of the VM Operator API is deprecated. Use **v1alpha2 or v1alpha3** instead,
as both are supported on Supervisor and are fully backward compatible" [DOC-9.0, DTOOL S10].
The upstream VM Operator project publishes `apiVersion: vmoperator.vmware.com/v1alpha5` and
references v1alpha1 through v1alpha5 [UPSTREAM, DTOOL S27]. Both cannot describe the same
served API surface, and no document resolves it. A manifest written against a version the
API server does not serve fails to apply.

**The commands.** Standard kubectl — the Broadcom pages do not present these, so mark them as
tooling idioms rather than doc-sourced if you surface them:

```bash
kubectl api-resources                                    # every kind: short name, group, namespaced
kubectl api-resources --api-group=vmoperator.vmware.com  # settles the v1alphaN question
kubectl api-resources --api-group=cluster.x-k8s.io       # v1beta1 vs v1beta2, as served here
kubectl api-versions | grep -E 'vmoperator|cluster.x-k8s|run.tanzu'

kubectl get crd                                          # raw CRD list
kubectl get clusterclass -A                              # which builtin-generic-vX.Y.0 exists here

kubectl explain cluster.spec.topology                    # schema, from the live API server
kubectl explain virtualmachine --recursive
```

**Checking served versions specifically.** `kubectl api-resources` reports the *preferred*
version per resource; a CRD may serve several. Inspecting the CRD object itself shows every
served version — standard kubectl, **`[UNVERIFIED]` against Broadcom docs**, and worth
running when a manifest is rejected on `apiVersion`:

```bash
kubectl get crd virtualmachines.vmoperator.vmware.com -o yaml   # .spec.versions[].name / .served
```

**What to tell the user.** State the conflict, give them the command, and report what their
cluster answered. Picking a side and hoping is the failure mode this skill was built to
prevent.

---

## Which provisioning API

Per *About VKS Cluster Provisioning* `[DOC-9.0]` [DTOOL S02]:

| API | `apiVersion` | Status |
|---|---|---|
| **Cluster v1beta2** | `cluster.x-k8s.io/v1beta2` | "Latest API for managing the lifecycle of a Cluster based on a Cluster Class" — requires vCenter 8 U3+, vCenter 9+ |
| **Cluster v1beta1** | `cluster.x-k8s.io/v1beta1` | "Recommended API for managing the lifecycle of a Cluster based on a Cluster Class" — requires vCenter 8+ |
| TanzuKubernetesCluster v1alpha3 | group string **`[UNVERIFIED]`** | **Deprecated** |
| TanzuKubernetesCluster v1alpha2 | — | **Deprecated** (vCenter 7 U3 Supervisor) |

> "Starting with VKS 3.2, the TanzuKubernetesCluster API is deprecated. To provision new VKS
> clusters, use Cluster v1beta1 or v1beta2." [DOC-9.0, DTOOL S02]

Harder, from the VKS 3.4 notes: "starting version 3.4, you won't be able to use the deprecated
TKC API to create Kubernetes 1.33 cluster", and Cluster API "is now the default method for
bootstrapping, configuring, and managing Kubernetes clusters" [DOC-9.1, DTOOL S29].

Provisioning is **CAPI + CAPV with the Supervisor as the management cluster** [DOC-9.0,
DTOOL S02]. Two documented client workflows: **kubectl** (declarative) and the **VCF CLI**
(interactive) [DOC-9.0, DTOOL S02].

The literal `TanzuKubernetesCluster` API group (commonly written `run.tanzu.vmware.com`) was
**not confirmed** on any fetched page — **`[UNVERIFIED]`**. It is deprecated anyway; if you
must touch one, get the group from `kubectl api-resources`.

---

## Provisioning a cluster with kubectl

The documented workflow, in order `[DOC-9.0]` [DTOOL S03]. Prerequisites: a content library
with compatible Kubernetes releases, and a configured vSphere Namespace.

```bash
# 1. Log in to the Supervisor and select the namespace context
vcf context create --endpoint <supervisor> --username <sso-user> --ca-certificate ~/ca_root.cert
vcf context use <context-name>

# 2. List available VM classes
kubectl get virtualmachineclass

# 3. Get storage classes for the namespace  (NOT `kubectl get storageclass`)
kubectl describe namespace <VSPHERE-NAMESPACE>

# 4. List available Kubernetes releases
kubectl get kr

# --- discovery that the documented workflow does not include, but this skill requires ---
kubectl api-resources --api-group=cluster.x-k8s.io    # is v1beta1 or v1beta2 served here?
kubectl get clusterclass -A                           # which builtin-generic-vX.Y.0 to reference
kubectl explain cluster.spec.topology                 # the schema this API server will validate

# 5. Author the cluster YAML: Cluster v1beta1/v1beta2 referencing a ClusterClass
# 6. Apply
kubectl apply -f cluster-1.yaml       # -> cluster.cluster.x-k8s.io/cluster-1 created

# 7. Monitor
kubectl get cluster

# 8/9. Once the control plane is ready, attach to the new cluster with the VCF CLI
vcf context use cluster-1

# 10. Verify
kubectl get nodes
kubectl get namespaces
kubectl get pods -A
```

**About the manifest.** The documented inputs are: cluster name, namespace, VM classes,
storage class, node replicas, and Kubernetes version [DOC-9.0, DTOOL S03]. **The exact
`spec.topology` field paths were not captured verbatim from any fetched page —
`[UNVERIFIED]`.** Do not reconstruct them from memory or from a neighbouring product's
example. Derive them:

```bash
kubectl explain cluster.spec.topology
kubectl explain cluster.spec.topology.workers --recursive
kubectl get clusterclass builtin-generic-v3.4.0 -o yaml   # the variables this class accepts
```

The last command is standard kubectl, **`[UNVERIFIED]` against Broadcom docs**, but it is the
mechanical way to learn which variables a versioned ClusterClass exposes — and those vary by
version, since VKS 3.6's class is documented as adding "additional configuration variables"
over 3.4's [DOC-9.1, DTOOL S23].

**Scaling, upgrading and deleting an existing cluster: `[UNVERIFIED]`.** The day-2 workflow
pages were not fetched. `kubectl get cluster` for status is doc-verified; the rest is not.

---

## VM Service and VM Operator

API group: **`vmoperator.vmware.com`** [UPSTREAM, DTOOL S27]. Kinds: `VirtualMachine`,
`VirtualMachineService`, `VirtualMachineClass`, `VirtualMachineImage` [UPSTREAM + DOC-9.0,
DTOOL S27/S10].

**Version guidance conflicts, and the conflict is the point:**

| Source | Says | Tag |
|---|---|---|
| VCF 9.0 product docs | `v1alpha1` deprecated as of VCF 9.0; "use v1alpha2 or v1alpha3 … both are supported on Supervisor and are fully backward compatible" | `[DOC-9.0]` |
| Upstream VM Operator project (`docs-stable`) | `apiVersion: vmoperator.vmware.com/v1alpha5`; references v1alpha1–v1alpha5 | `[UPSTREAM]` |
| What a 9.1 Supervisor serves | not stated on any retrievable page | `[UNVERIFIED]` |

**For VCF 9.0, trust v1alpha2/v1alpha3** as the documented supported set — but confirm against
the cluster before writing a manifest, because the upstream project is demonstrably ahead of
what the 9.0 docs describe.

```bash
kubectl api-resources --api-group=vmoperator.vmware.com
kubectl explain virtualmachine
```

**9.1 difference:** VM Service gains snapshot management, multiple network interfaces at
create time and as a day-2 operation, and infrastructure policies for affinity/anti-affinity
placement [DOC-9.1, DTOOL S22].

---

## What VKS is made of

Stated on the *VKS Components* page in the **9.1** doc set [DOC-9.1, DTOOL S28]. The 9.0
equivalent page was not fetched, so treat applicability to a 9.0 estate as likely but
**`[UNVERIFIED]`**:

- **Three controller layers:** Virtual Machine Service (VM Operator), Cluster API, and the
  Cloud Provider Plugin (integrates vSphere resources and CNS).
- **Auth:** an Authentication Webhook validating tokens via vCenter SSO, **or** OIDC with
  Pinniped.
- **Storage:** CSI plugin — transient, persistent and container-image storage.
- **Networking:** CNI is **Antrea (default)** or **Calico**.
- **Load balancing:** NSX embedded/advanced load balancer, or HAProxy.
- **Tenancy:** the vSphere Namespace, boundary for three runtimes — VMs, VKS clusters,
  vSphere Pods.
- **vSphere Zones:** a Supervisor stretched across three vSphere clusters for HA.

VKS is the renamed **Tanzu Kubernetes Grid Service** — visible in the fact that current VKS
doc URLs still use the slug `vmware-tanzu-kubernetes-grid-service-*` [DOC-9.1, DTOOL S23/S26].
Expect that name in URLs, search results and older runbooks.

---

## Destructive operations

- **Deleting a `Cluster`** removes the guest cluster: nodes, workloads and their persistent
  volumes. There is no documented undo in this corpus. Confirm the target name and namespace
  against `kubectl get cluster -A` before issuing anything destructive.
- **Changing the ClusterClass reference** on an existing cluster is a topology change across
  every node it manages. The blast radius was not documented in any fetched page —
  **`[UNVERIFIED]`** — which is itself a reason to treat it as high-impact.
- **Cluster upgrades** (changing the Kubernetes version in the topology) roll nodes. The
  documented procedure was not captured — **`[UNVERIFIED]`**.

State these plainly when a user is about to run one, and prefer a dry inspection
(`kubectl get cluster -A`, `kubectl get cluster <name> -o yaml`) first.

---

## UNVERIFIED inventory for 9.0

Everything the research could not establish. Never fill these in from memory; resolve them
against the live cluster or say they are open.

1. **`kubectl vsphere login` / the `kubectl-vsphere` plugin** — absent from the 9.x docs, but
   removal versus non-documentation is unresolved.
2. **VM Operator served API version on a real Supervisor** — 9.0 docs say v1alpha2/v1alpha3,
   upstream shows v1alpha5, 9.1 unstated.
3. **`spec.topology` field paths** for the `Cluster` manifest — no verbatim example captured.
4. **`TanzuKubernetesCluster` API group string** — never confirmed on a fetched page.
5. **ClusterClass shipped by VKS 3.3.x** — the VKS 3.3 release notes were not fetched, and
   3.3.1 is the version in the VCF 9.0 BOM.
6. **VKS ↔ VCF version binding** — inferred from release dates only; never documented.
7. **Named vSphere Namespace roles** (owner / edit / view) — not confirmed in either doc set.
8. **Content-library creation/subscription procedure** for Kubernetes release images.
9. **Day-2 cluster operations** — scale, upgrade, delete procedures were not fetched.
10. **`vcf plugin` subcommand syntax** — only the command group name is confirmed.
11. **Namespace/Supervisor REST endpoints** — no VKS or Supervisor OpenAPI spec exists in the
    corpus; the VKS API reference site exists (`developer.broadcom.com/xapis/
    vmware-vsphere-kubernetes-service/latest/`, documenting 3.6.0 and 3.4.1) but whether it
    offers a downloadable spec was not verified.
12. **Whether an empty `kubectl get virtualmachineclass` means "not assigned"** — that is
    inference, not documentation.

---

## Source map

| Key | Where | Covers |
|---|---|---|
| DTOOL S02 | VCF Service Admin & Dev **9.0** — *About VKS Cluster Provisioning* | CAPI/CAPV, Supervisor as management cluster, v1beta1/v1beta2, TKC deprecation |
| DTOOL S03 | VCF Service Admin & Dev **9.0** — *Workflow for Provisioning VKS Clusters Using kubectl* | The verbatim command sequence, `describe namespace` idiom, `kr` short name |
| DTOOL S10 | VCF **9.0** — VM Service / IaaS control plane | VM Operator v1alpha1 deprecation, v1alpha2/v1alpha3 |
| DTOOL S24 / S25 | VCF **9.0** / **9.1** — connect to Supervisor as an SSO user | `vcf context create`, `VCF_CLI_VSPHERE_PASSWORD`, context commands |
| DTOOL S30 / S31 | VCF **9.0** / **9.1** — download/install the CLI tools | `vcf` binary only; Link to CLI Tools path; no kubectl in package |
| DTOOL S22 | VCF Service Admin & Dev **9.1** — Supervisor release notes | Supervisor 9.1.0.0, VM Service changes, NSX segment UI regression |
| DTOOL S23 / S29 | VCF Service Admin & Dev **9.1** — VKS 3.6 / 3.4 release notes | ClusterClass names, K8s versions, VKr floor, TKC cutoff |
| DTOOL S27 | Upstream VM Operator project (`docs-stable`) | `vmoperator.vmware.com`, v1alpha1–v1alpha5, kinds |
| DTOOL S28 | VCF Service Admin & Dev **9.1** — VKS Components | Controller layers, CNI/CSI/auth/LB, namespace tenancy, zones |
| DTOOL S32 / S33 | VCF Consumption (latest) — VCF CLI | `vcf version` v9.1.0.0, command groups, plugin model |
| DAUTH S33 / S34 | VCF **9.0** / **9.1** — understanding authorization in Supervisor | SSO model, `--type=k8s` context form, Pinniped `[9.1]`, `--api-token` `[9.1]` |
| DCORE §2, §2.1 | `research/vcf-core-9.1-and-deltas.md` | 9.0 BOM (Supervisor 9.0.0.0, VKS 3.3.1), 9.1 BOM rows |
