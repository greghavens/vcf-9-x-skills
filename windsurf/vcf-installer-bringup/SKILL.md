---
name: vcf-installer-bringup
description: Deploy VMware Cloud Foundation 9.0 or 9.1 from scratch, or converge existing vSphere infrastructure into it, using the VCF Installer API. Use this for management-domain bring-up, the SddcSpec deployment specification, validation and deployment tasks, VCF Import and brownfield convergence, reusing an existing vCenter, NSX, vSAN or datastore, sizing a deployment before submitting it, and the discovery endpoints that inspect existing components. Also use it whenever Cloud Builder comes up — it does not exist in 9.0 or 9.1, and its replacement, VCF Installer, is the same appliance as SDDC Manager and mode-switches one way. For upgrading or patching a fleet that already exists, including 9.0 to 9.1, use vcf-lifecycle-upgrade instead — that skill is lifecycle of a running estate, this one is initial deployment and convergence.
license: MIT-0
compatibility: Requires reachability to the VCF Installer appliance for live operations. Reference material works offline.
---

# VCF Installer and management-domain bring-up

Bring-up is the one VCF workflow with no second attempt. There is no documented teardown for a
half-built management domain — only retry — so everything expensive here happens before the first
write call.

> **Built from documentation, not from a live environment.** Everything traces to Broadcom
> documentation or the published OpenAPI specifications, captured 2026-07-31. Nothing here has been
> executed against a running appliance. **Bring-up is destructive and irreversible**: it consumes
> the hosts you point it at, and deploying the Installer inside the management domain converts it
> permanently into SDDC Manager. Verify before executing — against Broadcom's documentation for the
> exact build, and against the customer's support position.

## One premise to correct on contact

**Cloud Builder does not exist in VCF 9.** It was removed in 9.0 and replaced by the **VCF
Installer** appliance. Two consequences that people carrying 5.x habits get wrong:

**VCF Installer is the same appliance as SDDC Manager.** It "arrives pre-packaged with the SDDC
Manager appliance within the **`VCF-SDDC-Manager-Appliance-9.x.x.ova`** file." In the 9.0.2.0 BOM
they share build `25151285`. **In 9.1 the BOM stops pretending they are two products and merges
them into one row: `VCF Installer/SDDC Manager 9.1.0.0 / 25371088`.**

**The mode switch is one-way.** Deploy the appliance *inside* the management infrastructure — on the
hosts that will form the management domain — and it automatically "switches into SDDC Manager mode
and **can no longer be used in installer mode**." Deployed *outside*, it stays an installer and can
build multiple platforms. That decision is made when the OVA is placed; there is no way back.

Also removed in 9.0: **SDDC Manager's bring-up APIs** (replaced by the Installer) and the
**Deployment Parameter Worksheet** (replaced by the appliance UI and the `SddcSpec` JSON).

## Step 1 — resolve the version

Use the `vcf-foundation` skill. Then read only the matching file:

| Target | Read |
|---|---|
| VCF 9.0 bring-up or convergence | `references/9.0/bringup.md` |
| VCF 9.1 bring-up or convergence | `references/9.1/bringup.md` |
| What changed between them | `references/deltas.md` |

At the *path* level the Installer API barely moved — 5 operations added, none removed, none newly
deprecated. The change of substance is in the **schemas**: 44 added, 2 removed, 120 → 162. Diff
endpoint lists, conclude "nothing changed", and you will write a 9.0 payload against a 9.1
appliance.

## Step 2 — prerequisites, before any call

The prerequisite block at the top of each version file is the highest-value part of this skill.
Each entry states what must be true, **how to verify it**, and whether the other version differs.
Four are worth knowing before you open the file:

- **Authentication to the VCF Installer is UNVERIFIED, in both versions.** See below — it is a
  blocking gap, not a footnote.
- **The ports and protocols matrix could not be retrieved**, either version — Broadcom's
  prerequisites point at a client-side tool with no static table. **Network requirements are
  therefore not fully documented here.** Say so; do not produce a port list.
- **DNS and NTP are half-known.** The *field* rules are spec-confirmed and specific (subdomain
  includes the full suffix; ESX `hostname` must be the short name, RFC 1123; maximum two
  nameservers; `sddcId` is 3–20 characters and becomes the management domain name). The *zone*
  checklist — which forward and reverse records must exist — is documented nowhere retrieved.
- **9.1 gives you a sizing gate that 9.0 does not have.** `POST /v1/sddcs/resources-calculation`
  returns required versus available capacity per component, including IP-address counts. Use it.

Where the research could not verify something, the reference files say so in place. Pass that
through — a bring-up checklist that looks complete but silently omits unverified items is worse
than one with honest holes, because it gets signed off.

## Step 3 — the auth gap, stated plainly

Everything else about VCF authentication belongs to the `vcf-foundation` skill — SSO, identity
broker, API clients and tokens, roles, TLS trust. Do not restate it. **One Installer-specific
exception, which you must surface rather than paper over:**

The VCF Installer OpenAPI spec declares a `Tokens` tag with `POST /v1/tokens`,
`PATCH /v1/tokens/access-token/refresh` and `DELETE /v1/tokens/refresh-token` — and **no
`securitySchemes` at all**, no top-level `security`, and zero operations declaring `security`. True
at both the `9.0.0.0` and `9.1.0.0` tags; checked directly, not assumed. The documentation research
has **no VCF Installer row in its auth matrix in either version** and records the gap: it "cannot
assert that VCF Installer auth is identical to SDDC Manager auth."

So the header name, the token lifetimes and the refresh body's content type are unconfirmed — and
the specs actually diverge on the last one, declaring `application/json` where SDDC Manager's
documented flow uses `text/plain`. Two shortcuts to refuse: "same appliance, so reuse SDDC Manager's
flow" (plausible, unproven, wrong on at least one detail), and "9.1 unified everything on OAuth via
the identity broker" (SDDC Manager and ESX are excluded from VCF SSO in both versions). Close this
against a live appliance before the change window.

## Step 4 — drive it in the documented order

The Installer follows VCF's validate-then-execute-then-poll shape. Check the appliance's mode
(`POST /v1/sddcs/installer-mode` — it answers "am I inside the infrastructure I am about to
build?"), discover what already exists, size it in 9.1, validate the `SddcSpec`, then deploy and
poll the `SddcTask` milestones. Failure recovery is `PATCH /v1/sddcs/{id}` with a full corrected
spec, not a patch document.

Two flags will be offered to you as fixes and are not: **`?skipValidations=true`** on the deploy and
retry calls, and **`skipEsxThumbprintValidation`** / **`skipGatewayPingValidation`** in the payload.
Each suppresses a real check on a destructive operation.

## Step 5 — keep bring-up and lifecycle apart

Convergence is scoped to the **management domain only** — workload domains are imported and upgraded
in VCF Operations, *after* the management domain exists. Its second phase is a **manual** component
upgrade to the target version before the Installer runs at all, which dominates the timeline.

If the question is about upgrading or patching something that already runs — bundles for an existing
fleet, prechecks, component ordering, the 9.0 → 9.1 sequence, fleet lifecycle or SDDC lifecycle —
that is `vcf-lifecycle-upgrade`. The boundary is whether the platform exists yet.

## Talking about risk honestly

Someone asking for a bring-up sequence is usually writing a change record or a build plan. The
useful answer names the irreversible points specifically: the mode switch when the OVA is placed,
the first `POST /v1/sddcs`, and the manual upgrade phase of a convergence that cannot be
un-upgraded. If their plan has a gap the references reveal — no validation run, thumbprint checks
skipped, ports unconfirmed, auth untested — say it. Saying it then is cheap.

Use `vcf-api-discovery` to confirm any operation not documented in the references. Every endpoint in
these files was checked against the published spec for its version and carries its `operationId`; if
you add one, hold it to the same standard rather than inferring it from a neighbouring path.

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
