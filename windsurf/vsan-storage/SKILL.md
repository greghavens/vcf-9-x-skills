---
name: vsan-storage
description: vSAN storage in VMware Cloud Foundation 9.0 and 9.1 — ESA and OSA architectures, storage policies and compliance, cluster and disk configuration, stretched clusters and witness hosts, site maintenance mode, vSAN health and HCL, remote / HCI-mesh datastore mounts, and vSAN Data Protection (snapservice) snapshots, protection groups and replication. Use this whenever the task touches vSAN itself — enabling or reconfiguring vSAN, RAID level, failures-to-tolerate, dedup and compression, stretching or unstretching a cluster, witness placement, resyncs and capacity, health checks, or vSAN snapshots. It also routes between the three API surfaces vSAN spans — SDDC Manager, VI-JSON and vSAN Data Protection — which is what people most often get wrong. Use vsphere-inventory-vm-lifecycle for non-vSAN VM, host and datastore work; vcf-domains-clusters for domain and cluster creation; vsphere-content-tags-policies for storage policy authoring that is not vSAN-specific.
license: MIT-0
compatibility: Requires reachability to SDDC Manager, vCenter and (for snapshots) the vSAN Data Protection appliance for live operations. Reference material works offline.
---

# vSAN storage in VCF

vSAN is the topic where a correct-sounding endpoint is most likely to be wrong, because
the operations are scattered across three unrelated API surfaces with three different
conventions — and the one people reach for first, the modern vCenter REST API, contains
almost none of them.

> **Built from documentation, not from a live environment.** Everything traces to Broadcom
> documentation or to the published OpenAPI specifications, captured 2026-07-31. Nothing
> has been executed against a running VCF deployment. Storage-policy changes and
> stretched-cluster operations are production-affecting: both can trigger large object
> resyncs that saturate the storage network for hours and reduce redundancy while they
> run. Verify against Broadcom's documentation for the customer's exact build, and against
> the cluster's current slack space, before executing anything here.

## The premise to correct on contact

**vSAN is not in the vCenter REST (vSphere Automation) API.** The `/api/vcenter/...`
surface has **zero** vSAN operations in both 9.0 and 9.1 — spec-confirmed absence against
both `vsphere-automation` inventories. Its two `witness` operations are `vcenter/vcha`,
which is **vCenter High Availability**, not vSAN. Anyone who greps for "witness" there and
finds those two will build the wrong thing.

The vCenter-side vSAN management API lives in the **VI-JSON API**, under
`/sdk/vim25/{release}/vsan/{ManagedObject}/{moId}/{Operation}` — **285 operations under the
`/vsan/` prefix in 9.0, 301 in 9.1**. Counting every vSAN-matching operation, including those
outside the `/vsan/` prefix and one vSAN-named `/pbm` operation, gives the wider totals of
**301 (9.0) and 317 (9.1)** used in the reference files. The two scopes differ by 16 in each
version — do not carry a 9.0 figure into 9.1 or vice versa.

## Step 1 — resolve the version

Use the `vcf-foundation` skill. Then read only the matching file:

| Target | Read |
|---|---|
| vSAN in VCF 9.0 | `references/9.0/vsan.md` |
| vSAN in VCF 9.1 | `references/9.1/vsan.md` |
| What changed between them | `references/deltas.md` |

## Step 2 — pick the right surface before writing a single call

This is the routing decision that makes or breaks the answer. Three surfaces, three
conventions, three sets of identifiers:

| You want to… | Surface | Shape |
|---|---|---|
| Stretch / unstretch a cluster, mount a remote vSAN datastore, run domain-wide vSAN health, manage the vSAN HCL | **SDDC Manager** | REST, `/v1/...`, `operationId` names like `updateCluster`; long-running work returns a `Task` |
| Configure vSAN on a cluster, disks and storage pools, fault domains, witness hosts, site maintenance, health, performance, space reporting, file services, iSCSI, CNS | **VI-JSON** | `POST /sdk/vim25/{release}/vsan/{MO}/{moId}/{Op}`; singleton `moId` values like `vsan-cluster-config-system`; body is `{Op}RequestType` |
| Storage policies, compliance, per-VM policy | **VI-JSON `/pbm/...`** for authoring; **vSphere Automation `/api/vcenter/storage/policies...`** for read and compliance | two different surfaces for one concept — see the version file |
| vSAN snapshots, protection groups, replication, ransomware recovery | **vSAN Data Protection** | REST, `/api/snapservice/...`, dotted `operationId`s, `?vmw-task=true` |

The version files list every operation with its `operationId` and mark which surface it
belongs to. Do not migrate a path between surfaces because it looks similar.

## Step 3 — prerequisites, before any sequence

Each version file opens with a prerequisites block stating what must be true, **how to
verify it**, and whether the other version differs. The ones that actually bite:

- **Stretched clusters need a witness host and exactly two fault domains.** Both are
  spec-stated, not folklore, and the witness has placement constraints that will fail the
  call late rather than early.
- **Storage-policy and RAID changes need capacity headroom** — the operation is accepted,
  then the resync runs. Check before, not after.
- **ESA has hardware requirements** that the sources here do not enumerate. The
  *verification route* is documented; the requirement list is not. Say so rather than
  inventing one.

Where the research could not verify a prerequisite, the files say so. Pass that through.

## Step 4 — ESA vs OSA: what is known and what is not

Both architectures ship in both versions — ESA Witness and OSA Witness appliances are both
in the 9.0 and the 9.1 BOM, and 9.1 adds simultaneous mounting of ESA and OSA clusters.

**Which architecture is the default for a new cluster is `UNVERIFIED`.** No retrieved
Broadcom page states it, and the specs do not imply it: `EsaConfig.enabled` is a required
boolean with no declared default. Do not resolve this from memory. If someone needs the
answer, tell them it is unconfirmed and point them at their build's planning guide.

9.1's **ESA Auto RAID-6** makes RAID-6 the default *RAID level* for ESA. That is a
statement about RAID level, not about architecture — the two get conflated constantly.

## Talking about risk honestly

Storage-policy changes, RAID-level changes, disk-group operations and stretch/unstretch all
move data. The useful answer says which of those resync, roughly what they resync, and what
the cluster's redundancy looks like while it happens. If the user's plan changes a policy on
a cluster whose free capacity you have not seen, say that the check comes first.

Unstretching is not the inverse of stretching. It is its own destructive operation.

## When it isn't covered here

Use `vcf-api-discovery` to confirm any operation not documented in the references. Every
endpoint in these files was checked against the published spec for its version and is cited
with its `operationId`; if you add one, hold it to that standard rather than inferring it
from a neighbouring path.

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
