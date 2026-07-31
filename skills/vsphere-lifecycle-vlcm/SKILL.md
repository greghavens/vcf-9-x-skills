---
name: vsphere-lifecycle-vlcm
description: "Manage ESX host images at the vSphere cluster level with vSphere Lifecycle Manager (vLCM) in VCF 9.0 and 9.1 — cluster image drafts, base images, add-ons, components and firmware/Hardware Support Packages; online, offline and UMDS image depots plus depot sync; hardware compatibility (HCL) checks; and the scan / check / stage / apply remediation cycle with its maintenance-mode, Quick Boot and Live Patch policy. Use this for \"what image is this cluster running\", \"apply an image and remediate\", \"why is remediation blocked\", image compliance drift, depot configuration, or standalone-host image management — all on the vCenter `/api/esx/settings/...` surface. Route fleet-level work — upgrading SDDC Manager, fleet lifecycle, SDDC lifecycle, VCF bundles, the 9.0-to-9.1 upgrade — to `vcf-lifecycle-upgrade`: that skill upgrades the VCF fleet, this one manages ESX images inside one vCenter. Also use it whenever someone proposes automating vLCM baselines, which are not a 9.x path."
license: MIT-0
compatibility: Requires reachability to vCenter on 443 for live operations. Reference material works offline.
---

# vSphere Lifecycle Manager — cluster images

vLCM is a desired-state system wearing a lifecycle system's clothes. You do not "upgrade a
cluster"; you edit a draft image, commit it, then remediate hosts toward it. Most mistakes
come from skipping a step in that chain, or from remediating a cluster whose image
somebody else owns.

> **Built from documentation, not from a live environment.** Every endpoint below traces to
> the published vSphere Automation OpenAPI specification (`vcenter.yaml`, git tags `9.0.0.0`
> and `9.1.0.0` of `github.com/vmware/vcf-api-specs`) or to version-pinned Broadcom prose,
> captured 2026-07-31. Nothing has been run against a live vCenter.
> **Remediation reboots hosts.** `POST .../software?action=apply` enters maintenance mode,
> moves or powers off VMs per the cluster's apply policy, and reboots each host unless Quick
> Boot or Live Patch applies. It is production-affecting and not transactional — verify the
> cluster, the image and the policy before executing.

## The path separator: settled, use `/api/esx/settings/`

Earlier research could not read the rendered reference pages and left the separator open —
`/api/esx/settings/...` (slash) versus `/api/esx-settings/...` (hyphen). **The
specification settles it: slash.** In both the `9.0.0.0` and `9.1.0.0` `vcenter.yaml`, the
paths are under `/esx/settings/`, on base path `https://{host}/api`:

```
POST /api/esx/settings/clusters/{cluster}/software?action=apply&vmw-task=true
     operationId: Esx.Settings.Clusters.Software_apply$Task
GET  /api/esx/settings/depots/online
     operationId: Esx.Settings.Depots.Online_list
```

The string `esx-settings` appears in **zero** operations in either version's spec. The
hyphenated form is a doc-site URL slug, not an API path. Use the slash form.

## Step 1 — resolve the version

Use the `vcf-foundation` skill for version and for authentication — session handling,
`vmware-api-session-id`, and the 9.0 block on non-federated logins live there, not here.
Then read **only** the matching file:

| Target | Read |
|---|---|
| VCF 9.0 (vCenter 9.0.0.0) | `references/9.0/vlcm.md` |
| VCF 9.1 (vCenter 9.1.0.0) | `references/9.1/vlcm.md` |
| What changed between them | `references/deltas.md` |

Evidence quality is symmetric: both versions have a full spec, and the `/esx/*` surface is
nearly identical — **347 operations at 9.0, 352 at 9.1, none removed, none deprecated**.
Every endpoint in the reference files carries the `operationId` it was matched on.

## Step 2 — prerequisites, before any apply

The prerequisite block at the top of each version file earns its keep. Four items stop
remediation dead, and the fourth is the one people miss:

- **The depot must be configured and synced.** No depot, no base images to choose from.
- **The cluster must be image-managed, not baseline-managed.** A baseline-managed cluster
  has no desired image and every `software` call against it fails or returns nothing
  useful. There is a one-way enablement transition, and it has its own check.
- **Hardware compatibility must pass** — or you must have deliberately decided it should
  not gate you. `enforce_hcl_validation` in the cluster apply policy is what turns an HCL
  finding into a hard stop, and it defaults to *not* blocking.
- **In VCF, the cluster's image may not be yours to change.** SDDC Manager can commit a
  cluster's desired state as an *orchestrator*, and the spec is explicit that doing so
  "prevents other users from modifying the committed desired state." Check the owner before
  you touch a VCF-managed cluster. See the next section — the boundary is real but it is
  only partly documented.

## Step 3 — the chain, in order

**create draft → set base image / add-on / components / hardware support → validate →
commit → scan → check → stage (optional) → apply → verify compliance.**

`validate` checks the draft resolves against the depot. `check` is the pre-remediation
readiness gate against the live hosts — it catches maintenance-mode and VM-evacuation
problems. `stage` pre-downloads payloads so the disruptive window is shorter; it is
optional and reboots nothing. Only `apply` touches host state.

Commit, scan, check, stage and apply are all **asynchronous tasks** (`?vmw-task=true`,
returning a task id) polled at `GET /api/cis/tasks/{task}` — `Cis.Tasks_get`,
spec-confirmed in both versions. A worked example with real payload fields is in each
version file.

## Step 4 — where vLCM ends and VCF begins

This skill stops at the vCenter boundary. `vcf-lifecycle-upgrade` handles everything above
it: SDDC Manager, fleet lifecycle, SDDC lifecycle, bundles, the VCF-level depot, the
9.0→9.1 upgrade. The seam is `personalities` — SDDC Manager's name for a cluster image — and image
compliance, which SDDC Manager reports at cluster level in both versions and at domain
level in 9.1. The version files list those endpoints so you can tell whose image a cluster
is running. What the research **could not** establish is an authoritative, enumerated
statement of which vCenter objects VCF claims exclusive lifecycle ownership of. The
`OrchestratorSpec` field on commit is the strongest evidence there is, and it is a
mechanism, not a policy. Say that rather than inventing a rule.

## The baselines conflict — record it, do not resolve it

Two Broadcom sources disagree, and this skill does not pick a winner:

- VCF 9.0 release notes: managing clusters with vLCM **baselines and baseline groups**
  (legacy VUM workflows) is **"no longer supported in vCenter 9.0"** — listed under
  *removals*.
- The standalone vSphere 9.0 guide: baselines are **"deprecated"**, and remain usable to
  "Update and patch ESX hosts only of version 8.x" and to update third-party software.

Removed-for-cluster-management versus deprecated-with-8.x-residual-use is a real conflict,
not a wording difference, and neither source was superseded. What is *not* in dispute: the
spec exposes **no baseline endpoints at all** — zero matches for `baseline` in either
version of `vcenter.yaml`, and Patch Manager APIs were removed in 9.0. So the automation
answer is unambiguous even while the doc conflict stands: **build on images; there is no
baseline API to build on.** The support position for 8.x hosts is a question for Broadcom
against the customer's exact build.

## When it isn't covered here

Use `vcf-api-discovery` to confirm any operation not documented in the references. The
`/esx/*` tree is large and the version files cover the image, depot, HCL and remediation
surface rather than all of it. Configuration profiles
(`/esx/settings/clusters/{cluster}/configuration/...`) are a *different* desired-state
system that shares the prefix; do not answer image questions from configuration endpoints.

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
