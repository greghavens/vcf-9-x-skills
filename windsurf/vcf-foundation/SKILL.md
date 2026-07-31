---
name: vcf-foundation
description: Authentication, API tokens, identity/SSO, roles, certificates, TLS trust and PowerCLI session setup for VMware Cloud Foundation 9.0 and 9.1 — plus the version router that determines whether an estate is 9.0 or 9.1. Use this when the task is about getting or refreshing an API token, setting up a service account or API client, choosing the right role or privilege, fixing certificate and TLS trust errors from a client (rotating certificates or passwords on the appliances is vcf-certificates-credentials), installing or connecting PowerCLI, or working out which VCF version an environment is running. Product-specific skills (NSX, lifecycle) cover their own operations and call back here for auth — consult this alongside them, not instead of them, and check here first whenever a VCF version has not yet been established.
license: MIT-0
compatibility: Requires network reachability to the target VCF appliances for live verification steps. Reference material and lookup patterns work offline.
---

# VCF foundation: version routing, prerequisites and authentication

VMware Cloud Foundation 9.0 and 9.1 are materially different platforms that share a
version number prefix and most of their vocabulary. That resemblance is the trap. An
auth flow, a role name, or a prerequisite that is correct for one is frequently absent
or renamed in the other, and the failure is silent — you get a plausible-looking answer
that fails against the customer's actual estate.

This skill exists to stop that. It does two jobs: it settles **which version you are
targeting** before anything else happens, and it holds the per-version prerequisites
and auth flows the other VCF skills defer to instead of repeating.

> **Built from documentation, not from a live environment.** Everything here traces to
> Broadcom documentation or to published OpenAPI specifications, captured 2026-07-31.
> None of it has been executed against a running VCF deployment. Treat destructive or
> state-changing operations as unverified until you have confirmed them against
> Broadcom's own docs for the customer's exact build.

## Step 1 — resolve the version. Do this before anything else.

Never answer a VCF question without knowing whether the target is 9.0 or 9.1, and never
default to "latest". Defaulting is how 9.1 facts end up in a 9.0 estate's runbook.

Resolve in this order:

1. **The user said so.** Take it, but stay alert — "VCF 9" alone is not an answer, and
   people say "9" when they mean either.
2. **Ask the environment.** If there is API reachability, query it rather than guessing.
   On SDDC Manager, `GET /v1/system/appliance-info` returns an `ApplianceInfo` carrying a
   `version` field — confirmed present in the SDDC Manager spec at both the `9.0.0.0` and
   `9.1.0.0` tags. `GET /v1/releases/system` (lowest deployed release) and
   `GET /v1/sddc-managers` also carry `version` and make good cross-checks.

   Do **not** use `GET /v1/system` for this. It exists in both versions and the name is
   inviting, but its `System` schema contains only `id`, `maxAllowedDomainsInSubscription`
   and (9.1) `vcfInstanceName` — no version field at all. It will appear to work and
   return nothing useful.

   See `references/<version>/auth-and-identity.md` for how to authenticate in order to
   make that call — a chicken-and-egg you resolve by trying the 9.0 flow first, since it
   is the narrower one.
3. **Ask the user.** One question, phrased so the answer is usable: "Is this a 9.0 or a
   9.1 fleet? If you're not sure, what does SDDC Manager report under About?"

If you genuinely cannot resolve it and the user needs an answer now, give the answer for
**both** versions with each clearly labelled, and say why you split it. Never blend them
into one set of instructions.

## Step 2 — check prerequisites before proposing a call

Most VCF automation failures are prerequisite failures, not syntax failures. The call
was right; something upstream of it was not true yet. Prerequisites also happen to be
where 9.0 and 9.1 diverge hardest, which makes them the highest-yield thing to check.

Read the `## Prerequisites` block at the top of the version-scoped reference file before
you write any call. Each entry says what must be true, how to verify it, and — critically
— whether it exists at all in the other version.

Three that catch people repeatedly, all detailed in the references:

- **SSO-issued, role-scoped API tokens are a 9.1 capability.** They do not exist in 9.0.
  If someone on 9.0 asks for a service account with a long-lived scoped token, the honest
  answer is that the 9.1 flow they have read about does not apply, followed by the 9.0
  route: per-product credentials, and NSX principal identities for NSX.
- **SDDC Manager is excluded from VCF SSO in both versions.** It authenticates through
  its own token endpoint. An agent that assumes one fleet-wide token opens every door
  will fail here specifically.
- **vCenter 9.0 blocks non-federated username/password logins.** A script that worked on
  8.x and fails on 9.0 with an auth error is usually hitting this, not a certificate
  problem.

## Step 3 — authenticate, per product

There is no single VCF token. Each product has its own flow, and several changed between
versions. Go to the reference file for the resolved version and use the exact method,
path, payload, token field and subsequent header documented there — including the header
*name*, which varies (`Authorization: Bearer`, `Authorization: OpsToken`,
`vmware-api-session-id`, cookie-plus-XSRF for NSX).

Read:

| You need | Read |
|---|---|
| Auth, identity, roles, certs for 9.0 | `references/9.0/auth-and-identity.md` |
| Auth, identity, roles, certs for 9.1 | `references/9.1/auth-and-identity.md` |
| What changed between the two | `references/deltas.md` |
| PowerCLI module, session and cert setup | `references/powercli-session.md` |

Load the version file for the resolved version only. Reading both invites bleed — if you
find yourself wanting both, that is a signal you have not actually resolved step 1.

## Certificates and TLS trust

VCF appliances ship VMCA-signed certificates that no client trusts by default, so the
first API call from a fresh script usually fails on TLS. The tempting fix is to disable
verification, and Broadcom's documentation does not prescribe that — it prescribes
replacing or trusting the certificate.

Say so when the user reaches for `-k` or `verify=False`. Not as a lecture: give them the
working command they asked for *and* the one-line path to doing it properly, and note
that disabling verification against a management plane that holds infrastructure
credentials is a different risk from doing it against a test API. If they are prototyping
and choose to skip verification anyway, that is a reasonable call for them to make with
the tradeoff visible — the failure mode is making it invisible.

The reference files carry the documented trust-import mechanisms per product. Two points
worth carrying in your head, both version-scoped: VCF Operations trust import is
documented as PEM-only **in the 9.1 doc set** — the 9.0 reference file explicitly declines
to assert this for 9.0, so do not carry it backwards. And **in 9.1** the identity broker
itself comes under certificate management, which makes it a single TLS point of failure
for every SSO-federated client.

## Roles and permissions

Read operations and write operations need different roles, and asking for a token without
asking what it will be used for produces a token that fails on the first write.

The VCF-level built-in roles (VCF Administrator, VCF Viewer, SDDC Administrator, SDDC
Viewer) and their mappings to component roles are documented **only in the 9.1 doc set**.
For 9.0, roles are per-product. The reference files carry both pictures; do not present
the 9.1 role model as the way 9.0 works.

## When something here does not cover the case

This skill covers prerequisites and getting authenticated. It deliberately does not
enumerate product APIs. When you need an operation it does not describe, use the
`vcf-api-discovery` skill, which teaches how to confirm an endpoint exists for a specific
version rather than guessing one. Guessing an endpoint that reads plausibly is the single
most damaging thing you can do here, because it is indistinguishable from a real one
until it fails in the customer's environment.

## Honest reporting

The research behind this skill could not verify everything, and the reference files mark
those places explicitly — the inbound ports matrix, NSX 9.1 auth specifics, the VCF
Automation All Apps token endpoint, VCF Installer auth in both versions, and others.

When you hit one of those, say so plainly and point at the lookup route. An agent that
says "the docs don't publish this; here's how to confirm it against your appliance" is
more useful than one that produces a confident-looking guess, and the difference only
becomes visible after someone has run the guess in production.

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
