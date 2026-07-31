---
name: nsx-security-policy
description: Build, debug and manage NSX distributed firewall rules, security policies, groups and drafts in VMware Cloud Foundation 9.0 and 9.1 via the Policy API. Use this whenever the task involves NSX microsegmentation, DFW rules, east-west firewalling, security policies, security groups, allow/deny rules between workloads, firewall exclusion lists, context profiles, or NSX firewall drafts and rollback — including casual phrasings like "block RDP between these two app tiers", "why is this traffic being dropped", or "set up microsegmentation". Use it for any auth, 401 or 403 error encountered specifically while calling NSX, since NSX session handling has failure modes that read like permission problems but are not. Also use it when someone is about to call the deprecated NSX Manager API for policy objects.
license: MIT-0
compatibility: Requires network reachability to NSX Manager for live operations. Reference material works offline.
---

# NSX distributed firewall and security policy

Distributed firewall work in NSX has three characteristics that make it worth slowing
down for: the objects nest in a specific way that is easy to get wrong, the auth flow has
two failure modes that look like something else, and — most consequentially here — the
evidence quality for 9.0 and 9.1 is not the same.

> **Built from documentation, not from a live environment.** Everything traces to
> Broadcom documentation or the published NSX OpenAPI specification, captured 2026-07-31.
> Nothing has been run against live NSX. Firewall changes are production-affecting by
> nature — verify against Broadcom's docs for the customer's build before executing, and
> treat any rule that could block management traffic as needing a rollback plan first.

## Before anything: settle the version

Use the `vcf-foundation` skill to resolve whether the target is VCF 9.0 or 9.1, then read
**only** that version's reference file. Reading both is how contamination happens.

Then read:

| Target | Read |
|---|---|
| VCF 9.1 | `references/9.1/dfw.md` |
| VCF 9.0 | `references/9.0/dfw.md` |
| What changed between them | `references/deltas.md` |
| Confirming anything not covered | `references/lookup.md` |

## The evidence asymmetry — say it out loud

NSX **9.1** has a published OpenAPI specification, so an endpoint can be confirmed to
exist. NSX **9.0 has no machine-readable spec** at the `9.0.0.0` tag of Broadcom's spec
repository, so 9.0 endpoints rest on prose documentation only.

This is not a footnote. It changes what you are entitled to claim. The 9.0 reference file
tags every line with its evidence grade, and a path confirmed in the 9.1 spec is **not**
thereby confirmed for 9.0 — it may well be identical, but "probably the same" and
"verified" are different things to hand someone who is about to change a production
firewall.

When you answer a 9.0 question, state the evidence grade. Users making change-control
decisions need to know whether they are acting on a spec or on an inference.

## Policy API only

All firewall and security objects live under `/policy/api/v1`. The Manager API and
Manager mode from NSX 4.x and earlier are no longer supported for policy objects — `/api/v1`
survives only for node, cluster and fabric administration and for the OpenAPI spec
endpoints.

If a user is reaching for `/api/v1` to create policy objects, or has inherited a script
that does, say so early. That script worked once, and the failure when it stops working
will not obviously point at the API surface.

## Authentication, and its two disguised failures

Session auth is `POST /api/session/create` with form fields `j_username` and
`j_password` — verified in **both** 9.0 and 9.1, and present as `CreateAuthenticatedSession`
in all three 9.1 NSX specs. Both the returned `JSESSIONID` cookie **and** the
`X-XSRF-TOKEN` header must be sent on every subsequent call. Sending only the cookie is
the most common mistake, and it fails in a way that reads like a permissions problem.

Two behaviours worth knowing before you debug anything. Note their evidence differs by
version — the version reference files carry the grading:

- **Session expiry surfaces as HTTP 403, not 401** *(documented verbatim in the 9.1 docs;
  not separately verified for 9.0)*. An expired session looks exactly like an
  authorisation failure, so people go chase roles that were fine all along.
- **The session cookie is bound to a single manager node** *(documented verbatim in the
  9.0 docs)*. Behind a load balancer, a session that works on one call fails on the next
  with no obvious pattern.

Exact payloads, timeouts and the destroy call are in the version reference files. One
path note: `/api/session/create` is declared outside the `/api/v1` base path — do not
prepend `v1` to it.

## Getting the object nesting right

The single most common structural error is treating a firewall rule as a top-level
object. It is not. A rule lives inside a security policy, which lives inside a domain
(usually `default`). Groups are referenced by policy path, not by name or by ID alone.

Rule ordering within a policy, and policy ordering relative to other policies, both
matter for evaluation — and a rule that is correct but sequenced after a broader allow
will simply never match. The reference files carry the ordering and revise mechanisms.

Both version files include a **worked example** that creates a security policy and a rule
blocking tcp/3389 between two existing groups, with the full call sequence including
auth. Start from that rather than assembling calls from the tables — it encodes the
nesting and the ordering decisions that the tables alone don't make obvious.

## Prerequisites are most of the work

Each reference file opens with a `## Prerequisites` block before any endpoint. Read it.
Each item says what must be true, how to verify it, and how it differs in the other
version.

The ones that bite: groups must already exist and be referenced by path; the domain must
exist; write operations need the Enterprise Admin role while Auditor is read-only; and
principal identities are the documented mechanism for service-account style access rather
than sharing a human's credentials.

There is one honest gap worth surfacing to users: **no authoritative list exists of which
NSX objects VCF owns and therefore should not be modified directly in NSX.** The research
could not find one. If a user is about to change something that VCF may consider its own,
flag the uncertainty rather than asserting either way.

## Drafts and rollback

NSX supports firewall drafts — staging changes and publishing them as a unit. For any
change big enough that a mistake would be hard to unwind, drafts are worth raising even
if the user didn't ask, because the alternative is discovering the problem through a
severed connection. The draft operations are in the version reference files.

## When it isn't covered here

`references/lookup.md` teaches how to confirm an endpoint against the appliance's own
spec (`GET /api/v1/spec/openapi/nsx_policy_api.json`, verified in both versions) or
against the spec corpus. Use the `vcf-api-discovery` skill for the general case.

Do not extrapolate an endpoint from a pattern. NSX paths are regular enough to make
invented ones look convincing, which is exactly what makes it dangerous here.

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
