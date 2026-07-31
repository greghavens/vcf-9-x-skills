---
name: vcf-lifecycle-upgrade
description: "Plan and execute VMware Cloud Foundation lifecycle operations in 9.0 and 9.1 — upgrades, patching, prechecks, bundles, depots, and component ordering — including the 9.0 to 9.1 upgrade path. Use this for any question about upgrading or patching VCF, SDDC Manager, vCenter, ESX, NSX or vSAN, about fleet lifecycle or SDDC lifecycle services, about what replaced the 9.0 fleet management appliance, about readiness or precheck failures, about depot and bundle configuration, or about what order components go in. Scope note: this skill upgrades ESX only as a component of a VCF domain or fleet upgrade — ESX host images at the vSphere cluster level (image drafts, base images, depots, action=check and action=apply remediation, image drift) belong to vsphere-lifecycle-vlcm. Also use it whenever someone asserts that SDDC Manager was removed or replaced in 9.1 — that premise is wrong and needs correcting before the rest of the answer."
compatibility: Requires reachability to SDDC Manager and VCF Operations for live operations. Reference material and runbook work offline.
metadata:
  {
    "openclaw": {
      "requires": {
        "anyBins": [
          "git"
        ]
      }
    }
  }
---

# VCF lifecycle and upgrades

Lifecycle is where 9.0 and 9.1 diverge most sharply, and where a wrong answer costs the
most — nobody re-runs a management-domain upgrade to see if the second attempt goes
better.

> **Built from documentation, not from a live environment.** Everything traces to
> Broadcom documentation or published OpenAPI specifications, captured 2026-07-31.
> Nothing has been executed against a running VCF deployment. Upgrades are high-impact
> and largely irreversible — every sequence here must be validated against Broadcom's
> documentation for the customer's exact build, and against their support position,
> before anyone runs it.

## Two premises to correct on contact

People arrive at this topic with two wrong beliefs, both picked up from partial reading
of 9.1 material. Correct them early, because everything downstream inherits the error.

**"VCF Fleet Manager" is not a product.** It does not appear anywhere in the 9.1
documentation. What actually happened: the 9.0 standalone *VCF Operations fleet
management appliance* was eliminated in 9.1 and replaced by two services — **fleet
lifecycle** and **SDDC lifecycle** — running natively inside VCF Management Services.
Use those names.

**SDDC Manager was not removed in 9.1.** It is in the 9.1 BOM, still owns workload-domain
deployment and component lifecycle, and drives the first half of the 9.0→9.1 upgrade
itself. What is deprecated is its **UI**, with VCF Operations becoming the lifecycle
interface. Its API grew: 375 operations at 9.0 to 423 at 9.1, with none removed.

The distinction matters practically. An engineer who believes SDDC Manager is gone will
architect around an API that is not only present but expanded.

## Step 1 — resolve the version

Use the `vcf-foundation` skill. Then read only the matching file:

| Target | Read |
|---|---|
| VCF 9.0 lifecycle | `references/9.0/lifecycle.md` |
| VCF 9.1 lifecycle | `references/9.1/lifecycle.md` |
| What changed between them | `references/deltas.md` |
| Doing a 9.0 → 9.1 upgrade | `references/upgrade-runbook.md` |

For a 9.0→9.1 upgrade specifically you are legitimately in both versions at once — you
start on 9.0 and finish on 9.1. That is what the runbook is for; use it rather than
splicing the two version files together yourself.

## Step 2 — prerequisites, before any sequence

Upgrade failures are overwhelmingly readiness failures discovered late. The prerequisite
block at the top of each version file is the highest-value part of this skill, and it is
what a change-control reviewer will actually want.

Each entry states what must be true, **how to verify it**, and whether it differs across
versions. The ones that most often go unnoticed:

- **Workload domains must meet a minimum version gate** before the 9.1 upgrade.
- **Prechecks are a gate, not a formality** — and the precheck surface moved between
  versions, so where you call it depends on the version.
- **Depot configuration and bundle availability** must be settled first, online or
  offline. An offline depot changes the sequence.
- **OAuth clients are not migrated** by the vIDM to identity-broker migration. They must
  be manually regenerated. Any 9.0-era OAuth client breaks on upgrade, and it breaks
  after the upgrade window, when nobody is looking for it.

Where the research could not verify a prerequisite, the reference files say so. Pass that
through — a checklist that looks complete but silently omits unverified items is worse
than one with honest holes, because it gets signed off.

## Step 3 — keep the two orderings apart

There is more than one component ordering, and conflating them is a named failure mode
for this skill:

- The **major upgrade** ordering (moving between releases).
- The **maintenance update** ordering for 9.0.x patches, which puts management components
  first.

They are not interchangeable, and the difference is not intuitive. The reference files
present them side by side precisely so they don't get merged in transit.

One 9.1 change worth flagging when it comes up: **NSX Edge clusters are upgraded at the
end** of the domain upgrade, which is a reordering from prior behavior.

## Step 4 — drive it through the right surface

In 9.0, lifecycle runs through SDDC Manager. In 9.1 it is split: SDDC Manager still does
component lifecycle for the workload-domain estate, while fleet lifecycle and SDDC
lifecycle handle the management components — with distinct API bases and separate task
namespaces.

Task polling differs accordingly. The version files carry the task endpoints per surface;
polling the wrong one returns nothing and reads like a stalled upgrade.

## Talking about risk honestly

When someone asks for an upgrade sequence, they are usually building a change record.
That means the useful answer includes what could go wrong and where the irreversible
points are — not as boilerplate, but specifically: which steps can be rolled back, which
cannot, and which ones will not surface a problem until well after they complete.

If the user's plan has a gap the references reveal — no precheck run, a depot not
configured, OAuth clients unaccounted for — say so directly. That is the moment where
saying it is cheap.

## When it isn't covered here

Use `vcf-api-discovery` to confirm any operation not documented in the references. Every
endpoint in these files was checked against the published spec for its version; if you
add one, hold it to the same standard rather than inferring it from a neighbouring path.

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
