# VCF 9.0 → 9.1 — Supervisor and VKS Delta

Scoped to the vSphere Supervisor, VKS cluster lifecycle, VM Service and the login path. For
the full cross-product delta see the research dossiers; this is the Supervisor/VKS slice.

**Source keys.** `DTOOL` = `research/tooling-powercli-vks-sdk.md` (its `Sxx` IDs carried
through); `DAUTH` = `research/foundation-auth-identity.md`; `DCORE` =
`research/vcf-core-9.1-and-deltas.md`.

**Evidence tags:** `[DOC-9.0]`, `[DOC-9.1]`, `[DOC-BOTH]`, `[UPSTREAM]`, `[UNVERIFIED]` —
same meanings as in the version files. **No VKS or Supervisor OpenAPI spec exists in this
corpus**, so nothing in this table is spec-confirmed; there is no machine-computed diff to
lean on the way there is for SDDC Manager or NSX.

> **Built from documentation captured 2026-07-31, not validated live.** ClusterClass changes
> and cluster deletion are destructive — verify before executing.

---

## Two things this table exists to enforce

1. **The login flow did not change.** `vcf context create` in both versions, with **identical
   documented text** [DOC-BOTH, DTOOL S24/S25]. Anyone who thinks 9.1 introduced a new login
   is thinking of the *additional* API-token path for VCF-Automation-registered Supervisors,
   which is an addition, not a replacement. And `kubectl vsphere login` was never in the 9.x
   documentation to begin with — not in 9.0, not in 9.1.

2. **The important version axis is VKS, not VCF.** VKS installs and upgrades as a Supervisor
   service on its own cadence. A "9.0 vs 9.1" question about ClusterClass, Kubernetes
   releases or cluster scale is usually a VKS 3.4-era vs 3.6-era question, and the two do not
   move in lockstep. See [The version binding](#the-version-binding-is-inferred-not-documented).

---

## Delta table

| Item | 9.0 | 9.1 | Evidence |
|---|---|---|---|
| **Supervisor version** | `VMware vSphere Supervisor 9.0.0.0`, build `24686447` | `Supervisor 9.1.0.0`, build `25370922`, released 2026-05-12 | `[DOC-9.0]`/`[DOC-9.1]` DCORE §2.1, §2; DTOOL S22 |
| **Bundled Supervisor Kubernetes versions** | Not captured | `v1.30.14+vmware.8-fips-vsc9.1.0.0`, `v1.31.11+vmware.8-fips-vsc9.1.0.0`, `v1.32.9+vmware.2-fips-vsc9.1.0.0` | `[DOC-9.1]` DTOOL S22; 9.0 side `[UNVERIFIED]` |
| **VKS version in the BOM** | `VMware vSphere Kubernetes Service 3.3.1` (no build number) | Rows exist for `VMware vSphere Kubernetes Service`, `vSphere Kubernetes releases`, `VKS Standard Packages` — **version numbers not captured** | `[DOC-9.0]` DCORE §2.1; `[UNVERIFIED]` DCORE §2 |
| **VKS era in practice** | 3.4.x (K8s **1.33**, ClusterClass `builtin-generic-v3.4.0`) | 3.6.x (K8s **1.35**, ClusterClass `builtin-generic-v3.6.0`); 3.6.1 explicitly carries "VCF 9.1 enhancements" | `[DOC-9.1]` DTOOL S29/S23 — **alignment inferred**, see below |
| **Login command** | `vcf context create --endpoint … --username … --ca-certificate …` | **Identical text** | `[DOC-BOTH]` DTOOL S24/S25 |
| **Non-interactive login** | Not documented | **`--api-token` + `--ca-certificate`** for VCF-Automation-registered Supervisors, via `export VCF_CLI_VCFA_API_TOKEN=<token>`, with `--tenant-name` | `[DOC-9.1]` DAUTH S34 |
| **External identity providers** | vCenter SSO / external IDP mentioned | Same **plus** explicit **Pinniped Supervisor + Concierge** for federated auth | `[DOC-9.1]` DAUTH S34 |
| **`kubectl vsphere login`** | Absent from the doc set | Absent from the doc set | `[DOC-BOTH]` (absence); removal vs non-documentation `[UNVERIFIED]` |
| **CLI package contents** | `vcf` binary only (`vcf-cli-{os}_{arch}`) | `vcf` binary only — identical page text | `[DOC-BOTH]` DTOOL S30/S31 |
| **VCF CLI version** | First release, shipped with VCF 9.0 | `vcf version` reports **v9.1.0.0** | `[DOC-9.1]` DTOOL S12/S32 |
| **Provisioning API** | Cluster `v1beta1` (recommended) / `v1beta2` (latest, vCenter 8U3+/9+); TKC deprecated | No change documented; on vCenter 9 both are eligible, so query which is served | `[DOC-9.0]` DTOOL S02 |
| **`TanzuKubernetesCluster`** | Deprecated since VKS 3.2; from VKS 3.4 cannot create K8s 1.33 clusters | Same deprecation, and moot in practice — the 3.6 line ships K8s 1.35 | `[DOC-9.0]` DTOOL S02, `[DOC-9.1]` DTOOL S29/S23 |
| **ClusterClass** | `builtin-generic-v3.4.0` in the 3.4 era; the class for 3.3.x is **`[UNVERIFIED]`** | `builtin-generic-v3.6.0`, with "additional configuration variables"; older classes remain in all namespaces for backward compatibility, though deprecated | `[DOC-9.1]` DTOOL S29/S23 |
| **Kubernetes release floor** | VKS 3.4 drops VKr **1.28**; interop 1.33/1.32/1.31/1.30/1.29 | VKS 3.6 drops VKr **1.31** — **minimum VKr 1.32**; K8s 1.35 with a 24-month support window | `[DOC-9.1]` DTOOL S29/S23 |
| **VKS upgrade floor** | — | Supervisor Kubernetes **v1.30+**; must be on **VKS 3.3+** to upgrade directly to 3.6 | `[DOC-9.1]` DTOOL S23 |
| **Cluster scale per Supervisor** | Baseline (half of 9.1 by the 9.1 statement) | **Up to 500 VKS clusters per Supervisor — stated as 2.5x** | `[DOC-9.1]` DTOOL S23 |
| **CNI** | Antrea (default) or Calico | Same, plus **Antrea hybrid encapsulation mode**, stated up to 40% performance improvement | `[DOC-9.1]` DTOOL S28/S23 |
| **Cluster networking** | Single network | **Multi-network support with secondary interfaces**; core pages also cite "dual-network support for VKS cluster" | `[DOC-9.1]` DTOOL S23; DCORE §3.0 |
| **Node images** | Image Builder | **ImageBaker**, producing RHEL-based node images, replacing Image Builder | `[DOC-9.1]` DTOOL S23 |
| **Encryption** | Not documented | **EncryptionClass** for multi-tenancy (3.6.1+); API shape `[UNVERIFIED]` | `[DOC-9.1]` DTOOL S23 |
| **VM provisioning speed** | Baseline | **VM Fast Deploy** (core pages: "VKS and VM Fast-Deploy using linked clone technology") | `[DOC-9.1]` DTOOL S23; DCORE §3.0 |
| **VM Service** | VM Operator group `vmoperator.vmware.com`; kinds `VirtualMachine`, `VirtualMachineService`, `VirtualMachineClass`, `VirtualMachineImage` | Adds **VM snapshot management**, **multiple network interfaces** at create and as day-2, **infrastructure policies** for affinity/anti-affinity placement | `[DOC-9.0]`/`[UPSTREAM]` DTOOL S10/S27; `[DOC-9.1]` DTOOL S22 |
| **VM Operator API version** | Docs say **v1alpha2/v1alpha3** (v1alpha1 deprecated as of VCF 9.0) | **No page states what 9.1 serves.** Upstream shows v1alpha5 | `[DOC-9.0]` DTOOL S10; `[UPSTREAM]` DTOOL S27; `[UNVERIFIED]` for 9.1 |
| **Container Service** | Does not exist | **New** — "deployment of individual containers without the complexity of managing or deploying a full Kubernetes cluster", isolated runtime environments. API surface `[UNVERIFIED]` | `[DOC-9.1]` DTOOL S22 |
| **VM Import** | Not documented | **New** — non-disruptive import of existing vSphere VMs onto Supervisors via the VCF-A VCD Migration Tool or API; batch import and rollback | `[DOC-9.1]` DTOOL S22 |
| **vSphere Zones** | Supervisor stretched across three vSphere clusters for HA | Same, and a zone may now span **multiple ESX clusters**, growing capacity without modifying existing zone objects | `[DOC-9.1]` DTOOL S28/S22 |
| **Supervisor deployment UI** | Classic NSX Segment Networking deployable from the vSphere Client | **Regression:** the vSphere Client UI no longer supports it. **API deployment remains supported.** | `[DOC-9.1]` DTOOL S22 |
| **Deployment topologies documented** | Not enumerated in the fetched 9.0 material | VCF Networking with VPC; Foundation Load Balancer; "Simplified Deployment Flow" (easy Supervisor); NSX + Avi; vDS + Avi; deploy from exported configuration | `[DOC-9.1]` DTOOL S01 |
| **Service mesh** | Not documented | **Istio Service Mesh for VKS workloads** (named on a core 9.1 page, not detailed) | `[DOC-9.1]` DCORE §3.0 |
| **Observability / cost** | Baseline | **Expanded IPFIX for VKS clusters with Antrea**; **VKS cost management and chargeback models** | `[DOC-9.1]` DCORE |
| **API specs** | No VKS spec published | No VKS spec published | `[DOC-BOTH]` — absence confirmed in the spec inventory |

---

## The version binding is inferred, not documented

This is the single most important caveat in this file, and it is easy to state wrongly.

**What the documents actually say:**

- The **VCF 9.0 BOM** lists `VMware vSphere Kubernetes Service 3.3.1` [DOC-9.0, DCORE §2.1].
- **VKS 3.4.0 released 2025-06-17 — the same day as VCF 9.0** [DOC-9.1, DTOOL S29/S12].
- **VKS 3.6.1 is described as the release carrying "VCF 9.1 enhancements"** [DOC-9.1,
  DTOOL S23].
- VKS release notes state compatibility as **"vSphere 9.x and 8.x"** — never as a VCF release
  binding [DOC-9.1, DTOOL S23/S29].
- The 9.1 BOM has VKS rows but **the versions on them were not captured** [`[UNVERIFIED]`,
  DCORE §2].

**What follows:** the 9.0 ↔ 3.4 / 9.1 ↔ 3.6 pairing used throughout these files is
**inference from release dates and one phrase in a release note**, not a documented mapping.
A VCF 9.0 estate can be on 3.3.1 (its BOM row), on 3.4.x, or on something later; a 9.1 estate
may be on 3.6.x or on 3.7. State it as typical alignment and resolve the actual version at
the cluster:

```bash
kubectl get clusterclass -A     # the ClusterClass name is the practical VKS-version signal
```

**And the version list itself is incomplete.** The **VKS 3.5 and 3.7 release notes were not
fetched** — both pages exist in the release-notes index [DTOOL S26]. **VKS 3.7 may already be
current as of 2026-07-31**, which conflicts with the VKS API reference site listing **3.6.0
as the latest documented version** [DTOOL S41]. That conflict is unresolved. **Do not state a
"latest VKS version"** on the basis of this corpus.

---

## Coverage gap: the 9.1 Supervisor/VKS "What's New"

The 9.1 VCF Automation What's New page explicitly defers: "Refer to VMware vSphere Supervisor
Release Notes for additional details", and **that release-notes set was never fully fetched**
[DCORE §8.2]. The 9.1 column above is assembled from the Supervisor 9.1 and VKS 3.6 release
notes that *were* retrieved, plus scattered mentions on 9.1 core pages.

Practically: this table is reliable for what it contains and **cannot be treated as
exhaustive**. If a user asks "what changed for VKS in 9.1", give them this and say explicitly
that the Supervisor release-notes set was not swept end to end.

---

## What did *not* change

Worth saying out loud, because "9.1 changed everything" is the default assumption:

- The **login command and its documented text** [DOC-BOTH].
- The **CLI package contents** — `vcf` binary only, same page text in both doc sets
  [DOC-BOTH].
- The **provisioning API table** — v1beta1/v1beta2 with a ClusterClass; TKC deprecated
  [DOC-9.0, no 9.1 contradiction found].
- The **storage-class discovery idiom** — `kubectl describe namespace <ns>`, not
  `kubectl get storageclass` [DOC-9.0].
- The **VM Operator API group** `vmoperator.vmware.com` and its kinds — only the *served
  version* is in question [UPSTREAM + DOC-9.0].
- The absence of a **VKS OpenAPI spec** in either version's spec bundle [DOC-BOTH].
