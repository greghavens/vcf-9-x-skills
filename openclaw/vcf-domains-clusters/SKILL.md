---
name: vcf-domains-clusters
description: Manage VMware Cloud Foundation topology in 9.0 and 9.1 through the SDDC Manager API — workload domains, vSphere clusters, ESX hosts and network pools. Use this for creating, expanding, contracting or deleting a domain or cluster; commissioning and decommissioning hosts; the free pool and host status; creating or editing network pools and IP pools; associating vCenter, NSX, NSX Edge, ALB or HCX with a domain; brownfield vCenter import into an existing fleet (importing during initial deployment is vcf-installer-bringup); cluster stretch and unstretch; configuration-drift remediation; and the validate → execute → poll-Tasks pattern these all share. This skill is about topology — what exists and how it is shaped. It is not about upgrading or patching it — bundles, depots, prechecks, component ordering and the 9.0 to 9.1 upgrade path belong to vcf-lifecycle-upgrade. Also use it whenever someone asserts SDDC Manager lost its domain and cluster APIs in 9.1 — it gained nineteen of them.
compatibility: Requires reachability to SDDC Manager for live operations. Reference material works offline.
metadata:
  {
    "openclaw": {
      "requires": {
        "anyBins": [
          "git"
        ]
      },
      "envVars": [
        {
          "name": "SDDC_NETWORKING_DATA_REMEDIATION",
          "required": false,
          "description": "Optional: SDDC_NETWORKING_DATA_REMEDIATION used in worked examples"
        }
      ]
    }
  }
---

# VCF workload domains, clusters and hosts

Topology is where the API is at its most literal — a domain either has a cluster or it does not,
a host is either in the free pool or it is not — and at its most unforgiving, because half of
these operations delete something that took hours to build.

> **Built from documentation, not from a live environment.** Everything traces to Broadcom
> documentation or the published OpenAPI specifications, captured 2026-07-31. Nothing has been
> executed against a running VCF deployment. **Destructive operations — domain deletion, cluster
> deletion, host decommissioning, forced host removal — must be verified against the customer's
> own environment and change process before execution.**

## The boundary with `vcf-lifecycle-upgrade`

Same appliance, same API, different question.

| Question | Skill |
|---|---|
| What domains/clusters/hosts exist, and how do I add or remove one? | **this one** |
| How do I move what exists onto a newer version? | `vcf-lifecycle-upgrade` |

Bundles, depots, prechecks, upgradables, component ordering, the 9.0→9.1 sequence: not here.
`GET /v1/version-drift` and `GET /v1/clusters/{id}/image-compliance` sit on the seam — the first
is lifecycle, the second is a topology prerequisite.

**Auth is neither skill's job.** Route token questions to `vcf-foundation`. Do not restate the
token flow in an answer; assume the caller has a bearer token and say so once.

## Step 1 — resolve the version, then read one file

Use `vcf-foundation` to establish whether the target is 9.0 or 9.1. Then:

| Target | Read |
|---|---|
| VCF 9.0 topology | `references/9.0/domains-clusters.md` |
| VCF 9.1 topology | `references/9.1/domains-clusters.md` |
| What changed between them | `references/deltas.md` |

Do not splice the two version files. Several things **invert** between versions — DNS/NTP moves
from system-scoped to domain-scoped, `computeSpec` moves from required to optional, network pools
go from near-immutable to editable — so a merged answer is wrong for both.

## Step 2 — prerequisites, before any call

The prerequisite block at the top of each version file is the highest-value part of this skill.
Each entry states what must be true, **how to verify it**, and whether the other version differs.
The ones that bite:

- **Hosts must already be commissioned and `UNASSIGNED_USEABLE`.** Cluster specs take a free-pool
  host *ID*, not an FQDN. A host in `UNASSIGNED_UNUSEABLE` is a blocker, not a candidate.
- **A network pool must exist before the first host is commissioned** — `networkPoolId` is a
  required field on `HostCommissionSpec`. In 9.0 that pool is then almost unchangeable.
- **A vLCM cluster image is effectively mandatory** — `clusterImageId` is documented as required
  for any cluster on vCenter 9.0 or above.
- **DNS and NTP live in different places in the two versions.** System-scoped in 9.0;
  domain- and cluster-scoped in 9.1, with the 9.0 surface deprecated.
- **The caller's role is UNVERIFIED in both versions.** No source consulted names the SDDC Manager
  role required for topology writes, and SDDC Manager sits outside VCF SSO in both. Pass that gap
  through rather than quoting a role name that looks plausible.

A checklist that looks complete but silently omits unverified items is worse than one with honest
holes, because it gets signed off.

## Step 3 — the pattern is always validate → execute → poll

Every create and update in this API is paired with a `validations` sub-resource, and long-running
work returns a `Task`:

```
POST <resource>/validations  →  GET <resource>/validations/{id}  →  POST|PATCH <resource>  →  GET /v1/tasks/{id}
```

Two failure modes are worth naming every time:

1. **A `COMPLETED` validation is not a passing validation.** Read `executionStatus` *and*
   `resultStatus`. `COMPLETED` + `resultStatus: FAILED` is the one people ship.
2. **`202` means accepted, not done.** Poll `/v1/tasks/{id}` to a terminal `status`, compared
   case-insensitively — the spec lists both `SUCCESSFUL` and `Successful`. 9.1 adds `QUEUED`
   (not terminal) and `TIMED_OUT` (terminal); a 9.0-era poller mishandles both.

The worked example — commission two hosts, then expand a cluster onto them, with real payload
fields — is at the end of each version file.

## Step 4 — know which door you are opening

`PATCH /v1/clusters/{id}` is a single endpoint that performs expansion, contraction, stretch,
unstretch, rename, vLCM transition and deletion-arming, selected purely by which field of
`ClusterUpdateSpec` you populate. Getting the field wrong does not 400 — it does something else.
The version files carry the field-to-intent table; use it rather than reasoning from the path.

**Deletion is two-phase for both clusters and domains.** `PATCH … { "markForDeletion": true }`
first, then `DELETE`. A `DELETE` without the arming step fails, and the arming step on its own is
a silent, easily-forgotten live grenade.

**Two force flags carry a data-loss warning in the spec itself** —
`ClusterCompactionSpec.forceByPassingSafeMinSize` and `.force`. Neither belongs in a runbook
without a named decision to use it. Quote the spec's own words when you surface them.

## Talking about risk honestly

When someone asks for a domain or cluster sequence they are usually building a change record. The
useful answer names what is irreversible: deleting a domain destroys its vCenter and NSX Manager;
forced host removal can lose data permanently; a 9.1 clusterless domain cannot be patched until a
cluster is added.

If the user's plan has a gap the references reveal — hosts not commissioned, no network pool, no
cluster image, a `DELETE` with no arming step — say so directly. That is the moment where saying
it is cheap.

## When it isn't covered here

Use `vcf-api-discovery` to confirm any operation not documented in the references. Every endpoint
in these files was checked against the published spec **for its own version** and cited by
`operationId`; if you add one, hold it to the same standard rather than inferring it from a
neighbouring path or from the other version.

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
