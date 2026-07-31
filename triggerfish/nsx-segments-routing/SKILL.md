---
name: nsx-segments-routing
description: Build, debug and manage NSX logical networking in VMware Cloud Foundation 9.0 and 9.1 via the Policy API — segments (logical switches), Tier-0 and Tier-1 gateways, transport zones, host and edge transport nodes, edge clusters and edge nodes, BGP peering, static routes, gateway uplinks and route advertisement, plus the Federation, project and VPC path families. Use this whenever the task involves creating or attaching a segment, wiring a Tier-1 to a Tier-0, north-south routing, "why can't this VM reach anything", uplink interfaces, transport zone or edge cluster design, or NSX fabric state — including casual phrasings like "add a new network for the app tier" or "our BGP session is down". For distributed firewall, microsegmentation, security policies and groups use nsx-security-policy instead; that skill also owns NSX auth and 401/403 debugging. For NAT, load balancing, VPN and IPAM use nsx-network-services.
license: MIT-0
compatibility: Requires network reachability to NSX Manager for live operations. Reference material works offline.
version: 1.0.0
classification_ceiling: CONFIDENTIAL
requires_tools: "[\"curl\", \"jq\"]"
network_domains: "[\"techdocs.broadcom.com\", \"developer.broadcom.com\", \"github.com\"]"
---

# NSX segments, gateways and routing

Logical networking in NSX has three characteristics that make it worth slowing down for: the objects
have a dependency order that the API will happily let you violate, the fabric layer underneath them is
usually owned by VCF rather than by you, and — most consequentially here — the evidence quality for
9.0 and 9.1 is not the same.

> **Built from documentation, not from a live environment.** Everything traces to Broadcom
> documentation or the published NSX OpenAPI specification, captured 2026-07-31. Nothing has been run
> against live NSX. **Routing and transport-node changes can sever management connectivity** — a
> Tier-0 uplink, an HA mode flip, a transport zone edit or an edge cluster change can black-hole the
> path you are using to reach NSX Manager. Verify against Broadcom's docs for the customer's build,
> capture the current object with a `GET` first, and know your rollback before executing.

## Before anything: settle the version

Use the `vcf-foundation` skill to resolve whether the target is VCF 9.0 or 9.1, then read **only**
that version's reference file. Reading both is how contamination happens.

| Target | Read |
|---|---|
| VCF 9.1 | `references/9.1/networking.md` |
| VCF 9.0 | `references/9.0/networking.md` |
| What changed between them | `references/deltas.md` |

For confirming anything not covered, the `nsx-security-policy` skill's `references/lookup.md` teaches
the NSX-specific lookup routes, and `vcf-api-discovery` handles the general case.

## The evidence asymmetry — say it out loud

NSX **9.1** has three published OpenAPI specifications, so an endpoint can be confirmed to exist. NSX
**9.0 has no machine-readable spec** at the `9.0.0.0` tag of Broadcom's spec repository, so 9.0
endpoints rest on prose documentation only.

This is not a footnote. It changes what you are entitled to claim, and it is **worse here than for the
firewall**, because the 9.0 prose covered networking unevenly. Segment, Tier-0 and Tier-1 *reads* are
solid for 9.0. Transport zones and edge clusters were confirmed for the read verb only. **Locale
services, gateway interfaces, static routes and BGP have no 9.0-pinned documentation page at all** —
which is precisely the area where a wrong guess takes down north-south traffic.

The 9.0 reference file tags every line with its evidence grade, and a path confirmed in the 9.1 spec is
**not** thereby confirmed for 9.0. When you answer a 9.0 question, state the grade, and for anything in
the routing area push the user toward the one call that settles it: `GET /api/v1/spec/openapi/nsx_policy_api.json`
on the appliance itself, which serves the spec matching its own build.

## Policy API only

All segments, gateways, transport zones and edge objects live under `/policy/api/v1`. The Manager API
and Manager mode from NSX 4.x and earlier are no longer supported for policy objects — `/api/v1`
survives only for node, cluster and fabric *administration*, RBAC introspection, and the OpenAPI spec
endpoints.

In 9.1 the spec backs the product statement in a way it does not for the firewall: the classic
Manager-API fabric lifecycle operations — `/api/v1/transport-nodes`, `/transport-node-profiles`,
`/host-switch-profiles`, `?action=redeploy` — are flagged `deprecated: true`. Their *status* reads are
not. If a user has inherited a script that builds transport nodes through `/api/v1/transport-nodes`,
say so early; the failure when it stops working will not obviously point at the API surface.

## Authentication

Session auth is `POST /api/session/create` with `j_username` / `j_password`; both the returned
`JSESSIONID` cookie **and** the `X-XSRF-TOKEN` header must be sent on every subsequent call. The
create/destroy operations are spec-confirmed for 9.1 (`CreateAuthenticatedSession`,
`DestroyAuthenticatedSession`); there is **no NSX spec at the 9.0.0.0 tag**, so 9.0 rests on
documentation only. Two behaviors whose evidence differs by version — the version reference files
carry the grading: expiry surfaces as **403, not 401** *(documented verbatim in the 9.1 docs; not
stated on the 9.0-pinned page)*, and the cookie is bound to a single manager node and fails behind
a VIP *(documented verbatim in the 9.0 docs; not restated for 9.1)*.

That is the whole flow at the depth this skill needs. **Do not re-derive it.** The `nsx-security-policy`
skill owns NSX auth in depth and is the skill to route any NSX 401/403 question to; `vcf-foundation`
owns VCF-wide identity and SSO.

## Getting the dependency order right

The single most common structural error is creating things in the wrong order and reading the 200 as
success. The API accepts a segment whose `connectivity_path` points at a gateway that does not exist;
it just never realises.

The order that actually holds:

1. **Transport zone** exists (and is the right type — VLAN segments *require* the path; overlay
   segments only auto-assign when exactly one TZ exists on the enforcement point).
2. **Tier-0** exists, before any Tier-1 that needs to route north.
3. **Tier-1** exists, before any segment that attaches to it.
4. **Edge cluster** exists — assembled from *already-prepared* transport nodes — before any gateway
   that needs a service router, which means before NAT, load balancing, VPN or standby relocation.
5. The edge cluster binds to a gateway through `edge_cluster_path` on the gateway's **locale service**,
   **not** through a field on the gateway itself. This trips people up every time.

Each reference file opens with a `## Prerequisites` block covering these, and each item says what must
be true, **how to verify it non-destructively**, and how it differs in the other version. Verify a role
with a read (`GET /api/v1/aaa/role-bindings` is spec-confirmed for 9.1) — **never** by attempting the
production write to see whether it is refused. If the write succeeds, you have already changed
production routing.

Two prerequisites bite hardest and are worth surfacing unprompted:

- **`route_advertisement_types` on a Tier-1 defaults to advertising almost nothing.** A Tier-1 created
  without it does not advertise `TIER1_CONNECTED`, so a correctly-created segment on a correctly-wired
  gateway is simply unreachable. This is the number-one "the segment exists and nothing works".
- **`gateway_address` in a segment subnet is CIDR**, e.g. `10.10.20.1/24` — the gateway's own address
  with a prefix, not a bare IP and not the network address.

## Segments: fixed versus flexible

A segment can exist in two shapes with **different URLs**: flexible (`/infra/segments/{id}`, attached
via `connectivity_path`) and fixed (`/infra/tier-1s/{t1}/segments/{id}`, attached by its parent in the
URL). Prefer flexible — it is what VCF workflows produce and it is the only one you can re-parent.

The trap worth knowing before anyone asks: **`GET /infra/tier-1s/{t1}/segments` does not return the
flexible segments attached to that Tier-1.** The spec says so verbatim. An empty result there is not
"no segments attached", and answering "there are none" from that call alone is wrong. Use the search
API instead.

## Path families

Objects exist under `infra/`, `global-infra/` (Federation) and
`orgs/{org}/projects/{proj}/infra/` (multi-tenancy), plus a separate VPC model — a VPC subnet is not a
`Segment`. They are not interchangeable; reading a project-scoped segment through `/infra/` returns
404. Three asymmetries that people assume wrongly:

- On the local manager, `global-infra` **segments and gateways are read-only**; writes go to the Global
  Manager appliance. But some `global-infra` *sub-objects* — Tier-0 BGP, interfaces, static routes,
  segment ports — **do** take writes locally. Do not generalise; check the path.
- Projects can own Tier-1s and segments. Projects **cannot** own a Tier-0 — the only project-scoped
  Tier-0 operation is a failover trigger.
- **The fabric is not tenant-scoped at all.** There are no project-scoped transport zones or edge
  clusters.

## The fabric is probably not yours

No authoritative list exists of which NSX objects VCF owns and therefore should not be modified
directly in NSX. The research could not find one, in either version. That gap matters more here than
in any other skill, because transport zones, transport nodes and edge clusters are exactly where VCF's
lifecycle ownership sits.

Working rule, **inferred** rather than doc-stated: segments, Tier-1s and routing on a Tier-0 you own
are normal automation targets; fabric objects should be created and deleted through SDDC Manager.
Before touching anything, read it and check its origin markers — `_system_owned`, `_protection`,
`_create_user`, and on fabric objects `origin_id` and `password_managed_by_vcf`. If a user is about to
change something VCF may consider its own, flag the uncertainty rather than asserting either way. Note
also that there is **no draft-and-publish preview for networking objects** the way there is for the
distributed firewall; `/infra/drafts` is a firewall construct. Your rollback is the `GET` you took
first.

## Worked example

Both version files include a **worked example** that creates an overlay segment attached to an existing
Tier-1, with the full call sequence, real payload fields from the spec schema, and guards that fail
closed when a path does not resolve. Start from that rather than assembling calls from the tables. The
9.0 version has an extra first step — fetching the appliance's own OpenAPI document — because in 9.0
that is the only way to know which of these endpoints your build actually has.

## When it isn't covered here

Do not extrapolate an endpoint from a pattern. NSX paths are regular enough to make invented ones look
convincing, which is exactly what makes it dangerous here. One live example: **dynamic BGP peering is a
documented 9.1 feature whose configuration API could not be located in the 9.1 spec** — the only trace
is a read-only field on a status schema. Say that, rather than inventing a plausible `neighbor-groups`
path.

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
