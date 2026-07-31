# VCF 9.1 — vSphere Supervisor and VKS Reference

**Scope:** the vSphere Supervisor and vSphere Kubernetes Service (VKS) as documented for
VCF 9.1. Everything is `[DOC-9.1]` unless tagged otherwise.

**There is no VKS OpenAPI spec in this corpus.** The bundled spec inventory
(`github.com/vmware/vcf-api-specs`, tags `9.0.0.0` / `9.1.0.0`) carries no VKS or Supervisor
product, so nothing here is *spec-confirmed*. Evidence is **doc-grade** (a Broadcom page was
fetched) or **cluster-grade** (the API server answered a query). Cluster-grade wins — see
[Discovery first](#discovery-first-and-why-it-is-not-optional).

**A gap to declare up front.** The VCF 9.1 core documentation **defers** the Supervisor and
VKS "What's New" to a separate release-notes set, and **that set was only partially fetched**
[DCORE §8.2]. The 9.1 VCF Automation What's New page says plainly: "Refer to VMware vSphere
Supervisor Release Notes for additional details." What follows comes from the Supervisor and
VKS 3.6 release notes that *were* retrieved plus 9.1 core pages — it is **not** a complete
sweep of 9.1 Supervisor/VKS changes. Say so when a user asks "what's new in 9.1 for VKS".

**Evidence tags:**

| Tag | Meaning |
|---|---|
| `[DOC-9.1]` | Stated on a fetched page in a VCF 9.1 doc set |
| `[DOC-9.0]` | Stated on a fetched page in a VCF 9.0 doc set (used where the 9.1 equivalent was not fetched) |
| `[DOC-BOTH]` | Verified on fetched pages in *both* doc sets |
| `[UPSTREAM]` | Upstream open-source project documentation, not Broadcom |
| `[UNVERIFIED]` | Not established by any fetched source. Never fill these in from memory |

**Source keys.** `DTOOL` = `research/tooling-powercli-vks-sdk.md` (its `Sxx` IDs carried
through); `DAUTH` = `research/foundation-auth-identity.md`; `DCORE` =
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
- [What 9.1 adds](#what-91-adds)
- [Destructive operations](#destructive-operations)
- [UNVERIFIED inventory for 9.1](#unverified-inventory-for-91)
- [Source map](#source-map)

---

## Prerequisites

Nothing below should be attempted until these are true. Each states what must hold, **how to
verify it**, the version it applies to, and whether 9.0 differs.

### P1 — Supervisor enabled on the cluster `[DOC-9.1]`

**Must be true:** a vSphere Supervisor must be deployed and enabled; for cluster provisioning
**the Supervisor is the Cluster API management cluster** [DOC-9.0, DTOOL S02 — stated on the
9.0 provisioning page; the 9.1 equivalent was not fetched, and nothing in the 9.1 material
contradicts it].

**Version:** `Supervisor 9.1.0.0`, build `25370922` in the 9.1 BOM [DCORE §2]. Supervisor
9.1.0.0 released **2026-05-12** and bundles three Supervisor Kubernetes versions
[DTOOL S22]:

- `v1.30.14+vmware.8-fips-vsc9.1.0.0`
- `v1.31.11+vmware.8-fips-vsc9.1.0.0`
- `v1.32.9+vmware.2-fips-vsc9.1.0.0`

That bundled set matters for P8: **VKS 3.6 requires Supervisor Kubernetes v1.30+**
[DTOOL S23].

**How to verify:** vSphere Client → **Supervisor Management > Namespaces** (namespace list,
**Summary > Status** pane) [DOC-BOTH, DTOOL S30/S31]; from a client, that a context can be
created and `kubectl api-resources` answers. **`[UNVERIFIED]`** — no REST endpoint for
"is a Supervisor enabled" was captured.

**Deployment regression, 9.1 only:** "Starting with VCF 9.1, the vSphere Client UI no longer
supports deploying a Supervisor with classic NSX Segment Networking" — **API deployment
remains supported** [DTOOL S22]. Documented 9.1 deployment topologies: VCF Networking with
VPC; Foundation Load Balancer; a "Simplified Deployment Flow" (easy Supervisor); NSX + Avi
Load Balancer; vDS + Avi Load Balancer; and deployment from an exported configuration
[DTOOL S01].

**9.0 difference:** Supervisor `9.0.0.0` build `24686447`; no UI restriction on classic NSX
segment networking documented.

### P2 — vSphere Namespace created and permissions assigned `[DOC-9.1]`

**Must be true:** a vSphere Namespace must exist to host VKS clusters, and the caller needs
permissions on it. The namespace is "the tenancy boundary that enables self-service
consumption of 3 runtimes … Virtual Machines, VKS clusters, vSphere Pods" [DTOOL S28].

Authorization model, identical in both doc sets: roles are sets of privileges; permissions
are granted by associating a role with a user or group on an object in the vCenter
hierarchy; vCenter SSO issues the token [DOC-BOTH, DAUTH S33/S34]. **9.1 adds** external IDP
integration (Okta, Entra/Azure AD) through **Pinniped Supervisor and Concierge** components
[DAUTH S34].

**How to verify:** `kubectl get namespace <ns>`, `kubectl describe namespace <ns>`; the
vSphere Client namespace list otherwise.

**`[UNVERIFIED]`** — named namespace roles (owner / edit / view) were not confirmed on any
fetched 9.0 or 9.1 page [DAUTH §11].

**9.0 difference:** no Pinniped-based external IDP path documented, and no API-token login
path (see P6/Login).

### P3 — A VM class is assigned to the namespace `[DOC-BOTH]`

**How to verify:**

```bash
kubectl get virtualmachineclass
```

Doc-verified in the 9.0 workflow [DTOOL S03]; the discovery idiom is unchanged in 9.1.
*Inference, flagged:* an empty result means no class is assigned and a cluster referencing
one will not schedule.

**9.0 difference:** the discovery command and the prerequisite are the same. What 9.1 adds is
**infrastructure policies for VM affinity and anti-affinity placement**, which affect where
those VMs land [DTOOL S22].

### P4 — A storage policy is assigned to the namespace `[DOC-BOTH]`

**How to verify — the counter-intuitive one:**

```bash
kubectl describe namespace <VSPHERE-NAMESPACE>
```

Storage classes are surfaced in the **namespace description**, not by
`kubectl get storageclass` [DOC-9.0, DTOOL S03]. Nothing in the 9.1 material changes this.

**9.0 difference:** none for this check. What 9.1 adds is **EncryptionClass** for
multi-tenancy, arriving with VKS 3.6.1's VCF 9.1 integration [DTOOL S23]. Its CRD group,
schema and relationship to storage classes are **`[UNVERIFIED]`** — resolve with
`kubectl api-resources | grep -i encryption` and `kubectl explain`.

### P5 — Content library with Kubernetes release images `[DOC-BOTH]`

**Must be true:** a content library carrying compatible Kubernetes releases [DOC-9.0,
DTOOL S03].

**How to verify:**

```bash
kubectl get kr                    # short name
kubectl get kubernetesreleases    # full name
```

**9.1-era version floor:** VKS 3.6 **drops VKr 1.31 support; the minimum is VKr 1.32**
[DTOOL S23]. VKS 3.6 ships Kubernetes **1.35** with a stated 24-month support window
[DTOOL S23]. If a user is carrying a 1.31-era release forward from a 9.0 estate, it will not
be usable after the VKS upgrade — that is the trap in this prerequisite.

**Node images:** VKS 3.6 introduces RHEL-based node images via the **ImageBaker** tool,
**replacing Image Builder** [DTOOL S23]. ImageBaker usage is **`[UNVERIFIED]`** — not
captured.

**9.0 difference:** the prerequisite and the `kubectl get kr` check are identical; the VKS
3.4 era instead dropped VKr **1.28** and interoperated with 1.33/1.32/1.31/1.30/1.29
[DTOOL S29].

**`[UNVERIFIED]`** — the content-library creation/subscription procedure.

### P6 — The `vcf` CLI is installed `[DOC-BOTH]`

Identical to 9.0. The download page — still at the legacy slug
`download-and-install-the-kubernetes-cli-tools-for-vsphere.html` — describes **only** the
`vcf` binary. No `kubectl`, no `kubectl-vsphere`, in either doc set. The phrase "Kubernetes
CLI Tools for vSphere" "appears only in the page URL and metadata …, not in the actual page
content" [DOC-BOTH, DTOOL S30/S31].

**Where to get it:** vSphere Client → **Supervisor Management > Namespaces** → namespace →
**Summary** → **Status** pane → **Link to CLI Tools** → **Open** / **Copy Link**
[DOC-BOTH].

**Install:** download `vcf-cli.tar.gz` / `.zip` → extract → **rename the executable to
`vcf`** → add to `PATH`. Package contains `vcf-cli-{os}_{arch}` [DOC-BOTH].

**How to verify:** run `vcf` for the banner; `vcf version` reports **v9.1.0.0** on the
current Consumption CLI [DTOOL S32].

**9.0 difference:** none in the documented install text; the VCF CLI first shipped in VCF 9.0
[DTOOL S12].

### P7 — CA certificate available for `--ca-certificate` `[DOC-BOTH]`

**Must be true:** `--ca-certificate <PATH>` on `vcf context create`; documented examples use
`~/ca_root.cert` [DOC-BOTH, DTOOL S24/S25] and `vcfa.cert` for the VCF Automation flow
[DAUTH S34]. VCF components are VMCA-signed by default, so a stock client fails validation
until the CA is trusted [DAUTH §3].

**Note on practice:** `--ca-certificate` is the documented way to pin a private CA in a VCF
client. **No fetched Broadcom page documents disabling TLS verification as supported.**

**9.0 difference:** the flag and its use are identical; only the 9.1 API-token flow adds a
second place it appears.

### P8 — Know which VKS version the Supervisor runs `[DOC-9.1]` + `[UNVERIFIED]`

This determines the ClusterClass name, the available Kubernetes releases, and whether the
9.1 feature set is even present.

**What is documented:** the 9.1 BOM contains rows for `VMware vSphere Kubernetes Service`,
`vSphere Kubernetes releases` and `VKS Standard Packages` — but **the version numbers on
those rows were not captured** [`[UNVERIFIED]`, DCORE §2]. Separately, the VKS 3.6 release
notes state 3.6 is "generally available for vSphere 9.x and 8.x", and **VKS 3.6.1 is the
release carrying "VCF 9.1 enhancements"** [DTOOL S23]. Released: 3.6.0+v1.35 (2026-02-11),
3.6.1 and 3.6.2 (2026-04-13), 3.6.3 (2026-06-16) [DTOOL S23].

**What is not documented:** any "VKS X ships with VCF Y" binding. VKS installs and upgrades
as a Supervisor service on its own cadence — treat 9.1 ↔ 3.6.x as **typical alignment,
inferred from release dates and the "VCF 9.1 enhancements" phrasing, not a guarantee**
[DTOOL §Gaps 5].

**Upgrade prerequisites to VKS 3.6** [DTOOL S23]: Supervisor Kubernetes **v1.30+**; minimum
**VKr 1.32**; and you must be on **VKS 3.3+ to upgrade directly**.

**How to verify — the only reliable route:**

```bash
kubectl get clusterclass -A       # expect builtin-generic-v3.6.0 in the 3.6 era
```

VKS 3.6's ClusterClass is `builtin-generic-v3.6.0`, documented as carrying "additional
configuration variables" over `builtin-generic-v3.4.0` [DTOOL S23/S29]. Older classes remain
present in all namespaces for backward compatibility, though deprecated [DTOOL S29] — so
more than one row is expected and you must choose deliberately.

**9.0 difference:** the same question, different answer — the VCF 9.0 BOM does name a
version, `VMware vSphere Kubernetes Service 3.3.1`, and the 3.4 era's class is
`builtin-generic-v3.4.0` [DOC-9.0/DOC-9.1, DCORE §2.1, DTOOL S29].

**`[UNVERIFIED]`** — **VKS 3.5 and 3.7 release notes were not fetched.** Both pages exist in
the release-notes index [DTOOL S26]. VKS **3.7** may already be current as of 2026-07-31,
which conflicts with the VKS API reference site listing **3.6.0 as the latest documented
version** [DTOOL S41]. That conflict is unresolved: do not state a "latest VKS version".

### P9 — Items the research could not verify

See [UNVERIFIED inventory](#unverified-inventory-for-91). The ones that bite during setup:
namespace role names, the VKS version actually installed, the content-library procedure, the
EncryptionClass API shape, and whether `kubectl-vsphere` still ships.

---

## Login and context

**The documented text is identical to 9.0** `[DOC-BOTH]` [DTOOL S24/S25]:

```bash
vcf context create --help

vcf context create --endpoint <SUPERVISOR-ADDRESS> \
                   --username <VCENTER-SSO-USER> \
                   --ca-certificate <PATH-TO-CERTIFICATE-FILE>

vcf context list
vcf context use <context-name>
```

Password interactively, or via **`VCF_CLI_VSPHERE_PASSWORD`** [DOC-BOTH]. A named-context
form appears in the authorization pages: `vcf context create <context_name>
--endpoint=<SUPERVISOR_ENDPOINT> --type=k8s --username=<user_name>` [DOC-BOTH, DAUTH
S33/S34]. The CLI writes `.kube/config`; the credential is a kubeconfig-managed bearer token.

### New in 9.1 — API-token login for VCF-Automation-registered Supervisors `[DOC-9.1]`

Where the Supervisor is registered with VCF Automation, 9.1 documents a non-interactive path
using `--api-token` plus `--ca-certificate` [DAUTH S34]:

```bash
export VCF_CLI_VCFA_API_TOKEN=<api_token>

vcf context create vcfa_ctx \
  -e $VCFA_ENDPOINT \
  --api-token $VCF_CLI_VCFA_API_TOKEN \
  --tenant-name $TENANT_NAME \
  --ca-certificate vcfa.cert
```

The API token comes from VCF Automation → **My Account → API Tokens** [DAUTH S34]. This is
the flow to reach for in automation; the interactive SSO flow above is the human path. Note
the endpoint here is the **VCF Automation** endpoint with a tenant name — if the question is
really about All Apps organizations and CCI CRDs, that is `vcf-automation-allapps-k8s`
territory, not this skill's.

**9.0 difference:** no `--api-token` flow is documented in the 9.0 authorization page
[DAUTH S33].

**On `kubectl vsphere login`.** No page in the 9.x doc set surfaced containing that string;
neither version's CLI-download nor SSO-login page mentions the plugin [DOC-BOTH]. The
download page slug still says `kubernetes-cli-tools-for-vsphere`, suggesting an in-place
rewrite. **`[UNVERIFIED]` — removed versus merely undocumented is unresolved.** Teach
`vcf context create`; do not assert removal.

**VCF CLI command groups** [DTOOL S33] — system: `completion`, `config`, `context`, `plugin`,
`version`; plugins: `cluster`, `imgpkg`, `kubernetes-release`, `namespaces`, `package`,
`pais`, `registry-secret`, `secret`, `telemetry`, `vm`, plus `addon` for VKS clusters.
Plugin availability is context-dependent. `vcf plugin` subcommand syntax: **`[UNVERIFIED]`**.

---

## Discovery first, and why it is not optional

**The documented contradiction.** VCF 9.0 docs: use VM Operator **v1alpha2 or v1alpha3**
[DOC-9.0, DTOOL S10]. Upstream VM Operator project: `vmoperator.vmware.com/v1alpha5`
[UPSTREAM, DTOOL S27]. **What a 9.1 Supervisor serves was not stated on any retrievable
page — `[UNVERIFIED]`.** For 9.1 specifically there is no documented answer at all, so the
cluster is the only source.

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

`kubectl api-resources` reports the *preferred* version per resource; a CRD may serve
several. To see every served version — standard kubectl, **`[UNVERIFIED]` against Broadcom
docs**:

```bash
kubectl get crd virtualmachines.vmoperator.vmware.com -o yaml   # .spec.versions[].name / .served
```

These are standard kubectl idioms, not quoted from Broadcom pages. Mark them as such when you
surface them; their *necessity* is what the documentation establishes.

---

## Which provisioning API

The API table comes from *About VKS Cluster Provisioning* in the **9.0** doc set
[DOC-9.0, DTOOL S02] — the 9.1 equivalent page was not fetched, and nothing 9.1-specific
contradicts it:

| API | `apiVersion` | Status |
|---|---|---|
| **Cluster v1beta2** | `cluster.x-k8s.io/v1beta2` | "Latest API for managing the lifecycle of a Cluster based on a Cluster Class" — requires vCenter 8 U3+, vCenter 9+ |
| **Cluster v1beta1** | `cluster.x-k8s.io/v1beta1` | "Recommended API for managing the lifecycle of a Cluster based on a Cluster Class" — requires vCenter 8+ |
| TanzuKubernetesCluster v1alpha3 | group string **`[UNVERIFIED]`** | **Deprecated** |
| TanzuKubernetesCluster v1alpha2 | — | **Deprecated** |

> "Starting with VKS 3.2, the TanzuKubernetesCluster API is deprecated. To provision new VKS
> clusters, use Cluster v1beta1 or v1beta2." [DOC-9.0, DTOOL S02]

And from VKS 3.4 onward: "you won't be able to use the deprecated TKC API to create Kubernetes
1.33 cluster"; Cluster API "is now the default method for bootstrapping, configuring, and
managing Kubernetes clusters" [DOC-9.1, DTOOL S29]. On a 9.1 estate running VKS 3.6 with
Kubernetes 1.35, TKC is not a live option for new clusters.

Since a vCenter 9 estate satisfies the v1beta2 requirement, **both versions may be served** —
which is precisely why `kubectl api-resources --api-group=cluster.x-k8s.io` comes before the
manifest.

---

## Provisioning a cluster with kubectl

The documented workflow [DOC-9.0, DTOOL S03] — the 9.1 doc set's equivalent page was not
fetched, so the sequence below is 9.0-sourced and applied to 9.1; the discovery steps are
what protect you if it has drifted.

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

# --- discovery the documented workflow omits, and this skill requires ---
kubectl api-resources --api-group=cluster.x-k8s.io    # is v1beta1 or v1beta2 served here?
kubectl get clusterclass -A                           # e.g. builtin-generic-v3.6.0
kubectl explain cluster.spec.topology                 # the schema this API server validates

# 5. Author the cluster YAML: Cluster v1beta1/v1beta2 referencing a ClusterClass
# 6. Apply
kubectl apply -f cluster-1.yaml       # -> cluster.cluster.x-k8s.io/cluster-1 created

# 7. Monitor
kubectl get cluster

# 8/9. Once the control plane is ready, attach to the new cluster
vcf context use cluster-1

# 10. Verify
kubectl get nodes
kubectl get namespaces
kubectl get pods -A
```

**About the manifest.** Documented inputs: cluster name, namespace, VM classes, storage class,
node replicas, Kubernetes version [DOC-9.0, DTOOL S03]. **The exact `spec.topology` field
paths were not captured verbatim — `[UNVERIFIED]`.** Derive them:

```bash
kubectl explain cluster.spec.topology
kubectl explain cluster.spec.topology.workers --recursive
kubectl get clusterclass builtin-generic-v3.6.0 -o yaml   # the variables this class accepts
```

The last command is standard kubectl (**`[UNVERIFIED]` against Broadcom docs**) and matters
more in 9.1 than in 9.0, because `builtin-generic-v3.6.0` is documented as exposing
*additional* configuration variables relative to `v3.4.0` [DTOOL S23] — variables a 9.0-era
manifest will not set, and which you cannot enumerate from any fetched page.

**Scaling, upgrading and deleting an existing cluster: `[UNVERIFIED]`.** Day-2 workflow pages
were not fetched.

---

## VM Service and VM Operator

API group **`vmoperator.vmware.com`** [UPSTREAM, DTOOL S27]. Kinds: `VirtualMachine`,
`VirtualMachineService`, `VirtualMachineClass`, `VirtualMachineImage` [UPSTREAM + DOC-9.0,
DTOOL S27/S10].

| Source | Says | Tag |
|---|---|---|
| VCF 9.0 product docs | v1alpha1 deprecated; use **v1alpha2 or v1alpha3** | `[DOC-9.0]` |
| Upstream project (`docs-stable`) | `v1alpha5`; references v1alpha1–v1alpha5 | `[UPSTREAM]` |
| **What VCF 9.1 serves** | **no page retrieved stating it** | **`[UNVERIFIED]`** |

For 9.1 there is no documented answer. Run
`kubectl api-resources --api-group=vmoperator.vmware.com` and report what the cluster says.

**9.1 VM Service changes** [DTOOL S22]:

- **VM snapshot management.**
- **Multiple network interfaces** at create time *and* as day-2 operations.
- **Infrastructure policies** for VM affinity / anti-affinity placement.

CRD-level shapes for these were not captured — **`[UNVERIFIED]`**; `kubectl explain
virtualmachine` is the route.

---

## What VKS is made of

From the *VKS Components* page in the 9.1 doc set [DOC-9.1, DTOOL S28]:

- **Three controller layers:** Virtual Machine Service (VM Operator), Cluster API, and the
  Cloud Provider Plugin (integrating vSphere resources and CNS).
- **Auth:** Authentication Webhook validating tokens via vCenter SSO, **or** OIDC with
  Pinniped.
- **Storage:** CSI plugin — transient, persistent and container-image storage.
- **Networking:** CNI is **Antrea (default)** or **Calico**.
- **Load balancing:** NSX embedded/advanced load balancer, or HAProxy.
- **Tenancy:** the vSphere Namespace, boundary for VMs, VKS clusters and vSphere Pods.
- **vSphere Zones:** Supervisor stretched across three vSphere clusters for HA — and in 9.1 a
  zone can span **multiple ESX clusters**, growing capacity without modifying existing zone
  objects used by vSphere Namespaces [DTOOL S22].

VKS is the renamed **Tanzu Kubernetes Grid Service**; current VKS doc URLs still carry the
slug `vmware-tanzu-kubernetes-grid-service-*` [DTOOL S23/S26].

---

## What 9.1 adds

Incomplete by construction — see the gap declared at the top of this file. What *was*
retrieved:

**From the VKS 3.6 release notes** [DTOOL S23]:

- `builtin-generic-v3.6.0` ClusterClass, with additional configuration variables.
- Kubernetes **1.35**, 24-month support window.
- **VCF 9.1 integration (3.6.1+):** multi-network support with **secondary interfaces**;
  **Antrea CNI hybrid encapsulation mode** (stated up to 40% performance improvement);
  **2.5x cluster scalability — up to 500 clusters per Supervisor**; **VM Fast Deploy**;
  **EncryptionClass** for multi-tenancy.
- RHEL-based node images via **ImageBaker**, replacing Image Builder.
- Upgrade floor: Supervisor Kubernetes v1.30+, minimum VKr 1.32, VKS 3.3+ to upgrade directly.

**From the Supervisor 9.1 release notes** [DTOOL S22]:

- **Container Service** — "seamless deployment of individual containers without the complexity
  of managing or deploying a full Kubernetes cluster", using isolated runtime environments.
  This is a genuinely new consumption mode: if a user wants a container, not a cluster, this
  is the 9.1 answer. Its API surface is **`[UNVERIFIED]`**.
- **VM Import** — non-disruptively import existing vSphere VMs onto Supervisors via the VCF-A
  VCD Migration Tool or API, with batch import and rollback.
- **vSphere Zones** spanning multiple ESX clusters.
- VM Service: snapshots, multiple NICs, affinity/anti-affinity infrastructure policies.
- **Regression:** the vSphere Client UI no longer deploys a Supervisor with classic NSX
  Segment Networking; the API still does.

**From 9.1 core pages** [DCORE §3.0, §8.2] — lower resolution, mentioned rather than detailed:

- **Istio Service Mesh for VKS workloads**; **dual-network support for VKS clusters**.
- VKS and **VM Fast-Deploy using linked clone technology**; simplified Container-as-a-Service
  with self-service namespace provisioning.
- **Expanded IPFIX for VKS clusters with Antrea** (Operations for Networks).
- **VKS cost management and chargeback models** (Cost and Capacity).
- Press-release claims, unverified against product docs: 2.6x Kubernetes cluster scale, up to
  46% lower Kubernetes operational cost.

---

## Destructive operations

- **Deleting a `Cluster`** removes the guest cluster — nodes, workloads, persistent volumes.
  No documented undo in this corpus. Confirm name and namespace against
  `kubectl get cluster -A` first.
- **Changing the ClusterClass reference**, including moving from `builtin-generic-v3.4.0` to
  `v3.6.0` after a VKS upgrade, is a topology change across every node. Blast radius:
  **`[UNVERIFIED]`** — no fetched page documents it, which is itself reason for caution.
- **Cluster upgrades** roll nodes. Procedure **`[UNVERIFIED]`**.
- **VKS upgrade itself** has hard floors (Supervisor K8s v1.30+, VKr 1.32+, from VKS 3.3+)
  [DTOOL S23]; a VKr 1.31 workload carried forward from a 9.0 estate stops being supported.

---

## UNVERIFIED inventory for 9.1

1. **The detailed Supervisor/VKS "What's New" for 9.1** — core docs defer to a release-notes
   set that was only partially fetched. Any "complete list of 9.1 VKS changes" is not
   available from this corpus.
2. **VM Operator served API version in 9.1** — no page states it.
3. **`spec.topology` field paths** for the `Cluster` manifest.
4. **The configuration variables exposed by `builtin-generic-v3.6.0`** — documented only as
   "additional" relative to 3.4.
5. **VKS 3.5 and 3.7 release notes** — not fetched. 3.7's existence conflicts with the VKS
   API reference listing 3.6.0 as latest. No "current VKS version" should be stated.
6. **VKS version numbers in the 9.1 BOM rows** — row existence confirmed, versions not.
7. **VKS ↔ VCF binding** — inferred from dates and the "VCF 9.1 enhancements" phrasing only.
8. **EncryptionClass** — named in the release notes; API group and schema unknown.
9. **Container Service API surface** — feature named, interface not documented here.
10. **ImageBaker** usage — named as replacing Image Builder, procedure not captured.
11. **Named vSphere Namespace roles** (owner / edit / view).
12. **`kubectl vsphere login` / `kubectl-vsphere`** — removed or merely undocumented.
13. **Day-2 cluster operations** — scale, upgrade, delete procedures not fetched.
14. **`TanzuKubernetesCluster` API group string**.
15. **No VKS/Supervisor OpenAPI spec** exists in the corpus; the VKS API reference site
    documents 3.6.0 and 3.4.1, but whether it offers a downloadable spec was not verified.

---

## Source map

| Key | Where | Covers |
|---|---|---|
| DTOOL S01 | VCF **9.1** — vSphere Supervisor Installation and Configuration | 9.1 Supervisor deployment topologies |
| DTOOL S22 | VCF Service Admin & Dev **9.1** — Supervisor release notes | Supervisor 9.1.0.0 + bundled K8s versions, Container Service, VM Service, VM Import, zones, NSX UI regression |
| DTOOL S23 | VCF Service Admin & Dev **9.1** — VKS 3.6 release notes | 3.6.x dates, K8s 1.35, `builtin-generic-v3.6.0`, 9.1 integration features, VKr floor, ImageBaker |
| DTOOL S26 | VCF Service Admin & Dev **9.1** — VKS release-notes index | Existence of 3.3/3.4/3.5/3.6/3.7 pages |
| DTOOL S29 | VCF Service Admin & Dev **9.1** — VKS 3.4 release notes | `builtin-generic-v3.4.0`, TKC cutoff at K8s 1.33, backward-compatible ClusterClasses |
| DTOOL S02 / S03 | VCF Service Admin & Dev **9.0** — provisioning pages | API table, CAPI/CAPV, kubectl workflow, `describe namespace` idiom |
| DTOOL S10 | VCF **9.0** — VM Service | VM Operator v1alpha2/v1alpha3 guidance |
| DTOOL S27 | Upstream VM Operator (`docs-stable`) | `vmoperator.vmware.com`, v1alpha1–v1alpha5 |
| DTOOL S28 | VCF Service Admin & Dev **9.1** — VKS Components | Controller layers, CNI/CSI/auth/LB, tenancy, zones |
| DTOOL S24 / S25 / S30 / S31 | VCF **9.0** / **9.1** — connect + CLI download | `vcf context create`, `vcf` binary only, Link to CLI Tools |
| DTOOL S32 / S33 | VCF Consumption (latest) — VCF CLI | `vcf version` v9.1.0.0, command groups |
| DTOOL S41 | `developer.broadcom.com/xapis/vmware-vsphere-kubernetes-service/latest/` | VKS API reference: 3.6.0 latest documented, 3.4.1 also available |
| DAUTH S33 / S34 | VCF **9.0** / **9.1** — understanding authorization in Supervisor | SSO model, `--type=k8s`, Pinniped, `--api-token` + `VCF_CLI_VCFA_API_TOKEN` |
| DCORE §2, §3.0, §8.2 | `research/vcf-core-9.1-and-deltas.md` | 9.1 BOM rows, 9.1 headline capabilities, the declared Supervisor/VKS What's New gap |
