---
name: vsphere-inventory-vm-lifecycle
description: Create, clone, power, reconfigure and delete virtual machines, and walk vCenter inventory — datacenters, clusters, hosts, datastores, networks, folders, resource pools — in VMware Cloud Foundation 9.0 and 9.1 via the vSphere Automation REST API on /api. Use this for any VM provisioning or teardown task, for "deploy a VM from a template", "power off these VMs", "resize CPU or memory", "list every VM in this cluster", "find the datastore/resource pool/folder id", or for scripting against vCenter. Also use it whenever someone is calling the deprecated /rest base path, or is hitting 401/403 against vCenter, since vCenter 9.0 blocks non-federated username/password logins and that failure reads like a bad password. Route content library, tags and storage policies to `vsphere-content-tags-policies`; route ESX host images, depots and cluster remediation to `vsphere-lifecycle-vlcm`.
compatibility: Requires network reachability to vCenter on 443 for live operations. Reference material works offline.
metadata:
  {
    "openclaw": {
      "requires": {
        "anyBins": [
          "curl",
          "jq",
          "git"
        ]
      }
    }
  }
---

# vSphere inventory and VM lifecycle

Most of the difficulty here is not the VM calls — those are small and regular. It is the
three things around them: getting onto the API at all (vCenter 9.0 changed the login
rules), resolving the opaque identifiers that every placement field demands, and knowing
which calls come back finished and which come back as a task.

> **Built from documentation, not from a live environment.** Everything traces to the
> published vSphere Automation OpenAPI specification (`vcenter.yaml`, git tags `9.0.0.0`
> and `9.1.0.0` of `github.com/vmware/vcf-api-specs`) or to version-pinned Broadcom prose,
> captured 2026-07-31. Nothing has been run against a live vCenter. **`DELETE
> /api/vcenter/vm/{vm}` destroys the VM and its files, and the power operations interrupt
> running workloads** — confirm the target identifier against a `GET` before executing
> either.

## Step 1 — settle the version

Use the `vcf-foundation` skill to resolve whether the target is VCF 9.0 or 9.1, then read
**only** that version's file.

| Target | Read |
|---|---|
| VCF 9.0 (vCenter 9.0.0.0) | `references/9.0/inventory-and-vms.md` |
| VCF 9.1 (vCenter 9.1.0.0) | `references/9.1/inventory-and-vms.md` |
| What changed between them | `references/deltas.md` |

Evidence quality is symmetric here, unusually: both versions have a full machine-readable
spec — 1,275 operations at 9.0, 1,367 at 9.1. Every endpoint in the reference files carries
the `operationId` it was matched on. Hold any you add to the same standard.

## `/api` is the surface. `/rest` is a trap.

All non-deprecated operations are on port **443** at the **`/api`** base path — the spec
declares `servers[0].url = https://{host}/api` at both tags. The legacy **`/rest`** base
path still exists and is **deprecated**, and it carries only the operations released up to
**vSphere 7.0.2**. Every 8.x and 9.x operation is `/api`-only.

That matters more than a deprecation notice usually does. A script written for `/rest`
does not fail loudly on 9.x — the old calls in it keep working, and only the newer ones
404. If someone shows you a script mixing the two, or reports "half my calls work", start
there.

A second surface, **VI-JSON**, sits at `/sdk/vim25/{release}` — the JSON front end for what
used to be SOAP/pyVmomi (2,195 operations at 9.0, 2,243 at 9.1), taking the same
`vmware-api-session-id` header. Reach for it only when `/api` has no equivalent:
`PropertyCollector`-style bulk retrieval, vApp operations, a reconfigure field
`/api/vcenter/vm/{vm}/hardware` does not expose. Its payloads are far larger; do not
default to it.

## The auth gate people trip on

Session auth is `POST /api/session` with HTTP Basic, returning **201** and a token you send
as the **`vmware-api-session-id`** header on every subsequent call. That is the whole
mechanism — `vcf-foundation` owns the federated-identity flow that produces the credential,
so defer to it rather than re-deriving SAML/JWT exchange here.

Two things to say out loud before anyone debugs a 401:

**`POST /api/session`, not `POST /api/cis/session`.** Some Broadcom prose renders a `cis`
segment. The specification does not: at **both** tags the operations are declared at
`/session` (`Cis.Session_get` / `_create` / `_delete`) under the `/api` server URL. `Cis` is
the tag name, not a path segment. Where prose and spec disagree, follow the spec.

**vCenter 9.0 blocks non-federated username/password logins.** A documented removal, not a
hardening default — *"vCenter 9.0 blocks logins with just a user name and password, which
might sometimes allow bypassing the federated provider domain."* On a federated deployment a
plain local credential fails, and it fails looking exactly like a wrong password. Establish
the identity source **before** writing the client. 9.1 does not restate the removal, so
assume it persists.

## Identifiers are opaque, and placement is where that bites

Every placement field — `folder`, `resource_pool`, `datastore`, `host`, `cluster`,
`network` — takes a vCenter managed-object identifier (`group-v42`, `resgroup-8`,
`datastore-15`), never a display name. You cannot construct one. You resolve it from a
list call, filtered by name, and you use the value the server returned.

This is the most common cause of a VM create that fails in a way reading like a permissions
problem. The reference files give the resolution order — datacenter → cluster/host →
resource pool + VM folder + datastore + network — because out of order means re-querying.

And **the list operations truncate silently.** The spec caps them at 4,000 VMs, 2,500 hosts,
2,500 datastores, and 1,000 each for datacenters, clusters, folders, networks and resource
pools, with no pagination cursor. An unfiltered `GET /api/vcenter/vm` on a large estate
returns a valid-looking 200 with a short body and no marker saying so. Always filter.

## Tasks: the `vmw-task=true` convention

Several operations exist twice — a synchronous form, and a `?...&vmw-task=true` form that
returns **202** and hands you a task to poll at `GET /api/cis/tasks/{task}` (144 such
operations at 9.0, 151 at 9.1). Use the task form for anything that moves data — clone,
relocate, OVF deploy; use the synchronous form for create, power and reconfigure. The
version files carry the status enum and the one spec-text ambiguity in the 202 body that
matters before you write a poller.

## Prerequisites are the front half of the work

Each reference file opens with a `## Prerequisites` block before any endpoint. Each item
says what must be true, **how to verify it non-destructively**, and whether it differs in
the other version. The ones that actually stop people:

- The **federated-login gate** above.
- **Privileges are per-object, not global.** The spec names them per operation —
  `VirtualMachine.Inventory.Create`, `Resource.AssignVMToPool`, `Datastore.AllocateSpace`,
  `Network.Assign` for a create; `VirtualMachine.Provisioning.Clone` for a clone;
  `VirtualMachine.Inventory.Delete` for a delete. Holding one does not imply the others.
- **VM create needs its placement targets to already exist** — a resource pool (or host),
  a `VIRTUAL_MACHINE`-type folder, a datastore, a network. None are created as a side effect.
- **`DELETE /api/vcenter/vm/{vm}` returns 400 if the VM is powered on.** Power off first.

## Scope boundaries — where to send the question instead

| If the task is about | Use |
|---|---|
| Content library, library items, tags, categories, tag associations, storage policies | `vsphere-content-tags-policies` |
| ESX host images, software drafts, depots, cluster remediation, configuration profiles (`/api/esx/settings/...`) | `vsphere-lifecycle-vlcm` |
| Obtaining the credential itself — SSO, federation, token exchange | `vcf-foundation` |
| An operation none of these cover | `vcf-api-discovery` |

The boundary is fuzzy in one place worth naming. Deploying from a **content library** VM
template is `POST /api/vcenter/vm-template/library-items/{templateLibraryItem}?action=deploy`
— content side. Cloning from a VM or template **already in inventory** is
`POST /api/vcenter/vm?action=clone` — here. Both version files carry the worked clone
example end to end including the task poll; start from that rather than assembling calls
from the tables, because it encodes the identifier-resolution order the tables do not.

## When it isn't covered here

Confirm against the spec for the version in hand; do not extrapolate from a neighbouring
path. These paths are regular enough that an invented one looks convincing —
`/api/vcenter/folder` exists but has no `POST`, and `/api/vcenter/network` has no
`GET /{network}`. Regularity is not a guarantee.

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
