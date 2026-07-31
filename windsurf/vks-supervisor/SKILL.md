---
name: vks-supervisor
description: Provision and operate vSphere Kubernetes Service (VKS) clusters and the vSphere Supervisor in VCF 9.0 and 9.1 — Supervisor login and contexts, vSphere Namespaces, guest cluster lifecycle through Cluster API and ClusterClass, VM Service and VM Operator, VM classes, storage policies and Kubernetes releases. Use this whenever someone asks how to log in to a Supervisor, how to create, scale, upgrade or delete a guest/workload Kubernetes cluster, which ClusterClass or Kubernetes release to reference, or how to drive kubectl against a vSphere Namespace — and especially whenever someone reaches for `kubectl vsphere login`, which appears nowhere in the VCF 9.x documentation, or for `TanzuKubernetesCluster`, which is deprecated. This skill is the Supervisor platform and the cluster lifecycle itself. For the VCF Automation consumption surface — All Apps organizations, CCI CRDs under `infrastructure.cci.vmware.com`, provider and org tenancy — use `vcf-automation-allapps-k8s` instead.
license: MIT-0
compatibility: Live work needs the `vcf` CLI and `kubectl` on the client plus reachability to the Supervisor endpoint. Reference material works offline. No VKS OpenAPI spec exists in this corpus — evidence here is documentation-grade and cluster-grade only.
---

# VKS and the vSphere Supervisor

This is the one layer in VCF where the documentation is *known* to be wrong in a specific,
reproducible way, and where the shape of a manifest tracks the VKS version on the Supervisor
rather than the VCF version on the box. So the method here differs from the rest of these
skills: **ask the cluster first, cite the document second.**

> **Built from documentation captured 2026-07-31, not validated live.** Nothing here has been
> executed against a running Supervisor. Cluster deletion and ClusterClass changes are
> destructive — deleting a `Cluster` takes the nodes, workloads and persistent volumes with
> it — so verify against the customer's build before executing.

## Two premises to correct on contact

**`kubectl vsphere login` appears nowhere in the VCF 9.x documentation.** The login flow in
both doc sets is the VCF CLI (`vcf`, the VCF Consumption CLI):

```bash
vcf context create --endpoint <SUPERVISOR-ADDRESS> --username <VCENTER-SSO-USER> \
                   --ca-certificate <PATH-TO-CA-CERT>
vcf context use <context-name>
```

The documented text is **identical in 9.0 and 9.1**. The download page still carries the
legacy slug `download-and-install-the-kubernetes-cli-tools-for-vsphere.html` but now ships
only the `vcf` binary — no `kubectl`, no `kubectl-vsphere`.

Be precise about the strength of that claim: a targeted search of the 9.x doc set found no
page containing the string `kubectl vsphere login`, which is **absence of documentation, not
proof of removal**. Whether the legacy plugin still ships for backward compatibility is
unresolved. Teach `vcf context create`; do not assert the plugin is gone. `kubectl` remains
the tool for everything after login — the VCF CLI writes the kubeconfig, `kubectl` uses it.

**`TanzuKubernetesCluster` will not do what they want.** Deprecated since VKS 3.2, and from
VKS 3.4 the TKC API cannot create a Kubernetes 1.33 cluster at all. Creation is Cluster API
(CAPI) and the Cluster API Provider for vSphere (CAPV) with the **Supervisor as the CAPI
management cluster** — a `Cluster` in `cluster.x-k8s.io/v1beta1` (or `v1beta2` on vCenter 9)
referencing a versioned **ClusterClass**. If someone arrives with a TKC manifest, correct
that before answering the question they asked.

## Discovery-first, and why this skill insists on it

There is a live contradiction in the corpus: the VCF 9.0 docs say the VM Operator API is
`v1alpha2`/`v1alpha3`, upstream shows `v1alpha5`, and what 9.1 actually serves was not
verifiable at all. A manifest written against the wrong served version fails to apply, and
no amount of reading resolves it. ClusterClass is the same problem — the name is
VKS-version-coupled (`builtin-generic-v3.4.0`, `builtin-generic-v3.6.0`), VKS is not bound
to the VCF version, and older classes stay present for compatibility.

So run these before writing any manifest, and say in your answer that you did:

```bash
kubectl api-resources --api-group=cluster.x-k8s.io       # which Cluster version is served
kubectl api-resources --api-group=vmoperator.vmware.com  # settles the v1alphaN question
kubectl api-versions | grep -E 'cluster.x-k8s|vmoperator|run.tanzu'
kubectl get clusterclass -A                              # which builtin-generic-vX.Y.0 exists here
kubectl explain cluster.spec.topology                    # the schema this API server serves
kubectl get crd                                          # raw CRD list, and served versions
```

These are standard kubectl idioms, not quoted from Broadcom documentation — mark them as
such if you surface them. Their *necessity* is what the corpus documents.

## Step 1 — resolve the version, read one file

| Target | Read |
|---|---|
| VCF 9.0 Supervisor / VKS | `references/9.0/vks.md` |
| VCF 9.1 Supervisor / VKS | `references/9.1/vks.md` |
| What changed between them | `references/deltas.md` |

Use `vcf-foundation` if the VCF version is unknown. The **VKS** version matters at least as
much and is a separate question — VKS installs and upgrades as a Supervisor service on its
own cadence.

## Step 2 — prerequisites, before any command

Each version file opens with a prerequisite block — Supervisor enabled, namespace created
with permissions assigned, a VM class and storage policy assigned to it, a content library
carrying the Kubernetes release images, the `vcf` CLI installed, the CA certificate on disk
for `--ca-certificate` — each stating what must be true, **how to verify it**, and whether
the other version differs. Not ceremony: a namespace with no VM class assigned yields a
cluster that never schedules, surfacing late as a `kubectl get cluster` that never moves.

## Worked example — a guest cluster, discovered rather than assumed

Discovery is steps 2–4. Skipping them is how you get a manifest that fails to apply.

```bash
# 1. Attach to the Supervisor, select the namespace context
vcf context create --endpoint 10.92.42.13 --username <sso-user> --ca-certificate ~/ca_root.cert
vcf context use <context-name>

# 2. Which Cluster API version does this Supervisor serve — v1beta1 or v1beta2?
kubectl api-resources --api-group=cluster.x-k8s.io
# 3. Which ClusterClass is present here? Do not assume the version suffix.
kubectl get clusterclass -A
# 4. What can the namespace place, and which Kubernetes releases exist?
kubectl get virtualmachineclass
kubectl describe namespace <ns>      # storage classes appear HERE, not in `kubectl get storageclass`
kubectl get kr                       # short name for kubernetesreleases
kubectl explain cluster.spec.topology

# 5. Author the manifest from what 2–4 returned, apply, monitor, then attach
kubectl apply -f cluster-1.yaml      # -> cluster.cluster.x-k8s.io/cluster-1 created
kubectl get cluster
vcf context use cluster-1 && kubectl get nodes
```

Documented manifest inputs: cluster name, namespace, VM classes, storage class, node replica
counts, Kubernetes version. **The exact `spec.topology` field paths were not captured
verbatim from a fetched page** — derive them from `kubectl explain`, not from memory.

## What is not settled, and should be said out loud

The VKS-to-VCF version binding is **inferred from release dates, not documented** — VKS 3.4.0
and VCF 9.0 share a release date and VKS 3.6.1 carries "VCF 9.1 enhancements", but the docs
state compatibility as "vSphere 9.x and 8.x", never as a VCF binding. Typical alignment,
never a guarantee. The VKS 3.5 and 3.7 release notes were not fetched, and 3.7's existence
conflicts with the VKS API reference listing 3.6.0 as latest. The detailed Supervisor/VKS
"What's New" for 9.1 is a gap too — the 9.1 core docs defer to a Supervisor release-notes
set that was never fetched, so 9.1 feature claims here come from the notes that *were*
retrieved.

## When it isn't covered here

**No VKS OpenAPI spec exists in the bundled corpus**, so nothing here is spec-confirmed the
way an SDDC Manager endpoint is; `vcf-api-discovery` covers operations outside these
references. `vcf-foundation` owns VCF-wide auth and the identity broker.
`vcf-automation-allapps-k8s` owns VCF Automation's consumption CRDs.

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

### Version labeling stays, and stays short

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
