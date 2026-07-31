---
name: nsx-network-services
description: Configure and troubleshoot NSX network services in VMware Cloud Foundation 9.0 and 9.1 via the Policy API — NAT (SNAT/DNAT/reflexive, scoped to a Tier-0 or Tier-1), load balancing (LB services, virtual servers, pools, monitors, and the Avi / NSX Advanced Load Balancer integration), IPSec and L2 VPN, IP pools, IP blocks and IPAM allocation, and VPC-scoped NAT, LB and VPN. Use it for "publish this VM to the internet", "why isn't my NAT rule translating", "stand up a load balancer VIP", or "build a site-to-site tunnel". Address exhaustion routes here only for NSX IP pools and blocks; a VCF *network pool* (the SDDC Manager object supplying vSAN/vMotion/host addressing) is vcf-domains-clusters. Distributed firewall, DFW rules, groups and microsegmentation are nsx-security-policy. Segments, Tier-0/Tier-1 creation, routing, BGP, transport zones and edge clusters are nsx-segments-routing — this skill assumes the gateway exists and attaches services to it.
license: MIT-0
compatibility: Requires network reachability to NSX Manager for live operations. Reference material works offline.
---

# NSX network services — NAT, load balancing, VPN and IPAM

Network services in NSX are all *attached* objects: a NAT rule hangs off a gateway, a virtual
server hangs off a load balancer service, a VPN session hangs off a VPN service. Almost every
failure in this area is a failure of the thing underneath, not of the object you wrote. That,
plus a sharp difference in evidence quality between 9.0 and 9.1, is what this skill is for.

> **Built from documentation, not from a live environment.** Everything traces to Broadcom
> documentation or the published NSX OpenAPI specification, captured 2026-07-31. Nothing has been
> run against live NSX. **NAT and VPN changes are production-affecting** — a SNAT rule with the
> wrong `source_network` can black-hole a subnet, and a VPN change drops an established tunnel.
> Verify against Broadcom's docs for the customer's build before executing, and have a rollback
> (usually `enabled: false`, not `DELETE`) ready first.

## Before anything: settle the version

Use the `vcf-foundation` skill to resolve whether the target is VCF 9.0 or 9.1, then read
**only** that version's reference file. Reading both is how contamination happens.

| Target | Read |
|---|---|
| VCF 9.1 | `references/9.1/services.md` |
| VCF 9.0 | `references/9.0/services.md` |
| What changed between them | `references/deltas.md` |

## The evidence asymmetry — and here it bites harder than usual

NSX **9.1** has three published OpenAPI specifications, so an endpoint can be confirmed to exist.
NSX **9.0 has no machine-readable spec** at the `9.0.0.0` tag of Broadcom's spec repository, so
9.0 endpoints rest on prose documentation only.

For this subject area the asymmetry is worse than it is for the firewall, and you should say so
plainly when a user asks a 9.0 question:

- **9.0 Policy NAT rule paths and 9.0 IPSec VPN service paths could not be verified at all.** The
  research explicitly records them as unretrievable for 9.0. They are almost certainly the same
  paths as 9.1 — but "almost certainly" is not what you hand someone changing production NAT.
- **9.0 load balancing** is confirmed for exactly one operation: reading a single LB service.
- **9.0 IP pools / allocations / subnets** are properly prose-verified. IP *blocks* are not.

So a 9.0 answer about IPAM can be given with reasonable confidence; a 9.0 answer about NAT or VPN
must come with the instruction to confirm against the appliance's own spec first
(`GET /api/v1/spec/openapi/nsx_policy_api.json` — the running manager serves the document for its
own build). Never present a 9.1 spec confirmation as evidence about 9.0.

## Authentication: defer it

Session auth is `POST /api/session/create` with form fields `j_username` / `j_password`; both the
returned `JSESSIONID` cookie **and** the `X-XSRF-TOKEN` header go on every subsequent call. The
create/destroy operations are spec-confirmed for 9.1 (`CreateAuthenticatedSession`,
`DestroyAuthenticatedSession`); there is **no NSX spec at the 9.0.0.0 tag**, so 9.0 rests on
documentation only. Two behaviors whose evidence differs by version — the version reference files
carry the grading: session expiry surfaces as **403, not 401** *(documented verbatim in the 9.1
docs; not stated on the 9.0-pinned page)*, and cookies are bound to a single manager node
*(documented verbatim in the 9.0 docs; not restated for 9.1)*.

That is the whole of it for this skill's purposes. **Auth belongs to `vcf-foundation`** — send the
user there for token flows, principal identities, role mapping and the full failure decode rather
than re-deriving it here. `nsx-security-policy` also carries the long-form version.

## Everything here is Policy API

All network-service objects live under `/policy/api/v1`. NSX 9.0 explicitly deprecated the
Manager-API NAT rule endpoint (`/api/v1/logical-routers/{id}/nat/rules/{id}` — *"deprecated as of
version 9.0"*). If a user has a script configuring NAT through `/api/v1`, say so early.

## Prerequisites are most of the work

Each version file opens with a `## Prerequisites` block before any endpoint. Read it. Each item
states what must be true, **how to verify it non-destructively**, and how it differs in the other
version. Verify a permission by reading your role binding — never by attempting the production
write you are trying to authorize.

The ones that actually bite:

- **NAT needs its gateway, and the gateway needs an edge.** A Tier-1 with no locale service (no
  `edge_cluster_path`) has nowhere to run NAT. And a Tier-1 that does not advertise `TIER1_NAT`
  will translate correctly and still be unreachable, because the translated address never reaches
  the Tier-0.
- **The `{nat-id}` path segment is not a UUID you invent.** It is a system-created NAT section —
  `USER`, `DEFAULT`, `INTERNAL` or `NAT64`. User rules go in `USER`.
- **Load balancing needs a service, a pool, an application profile and somewhere to run.** A
  virtual server requires `ip_address`, `ports` and `application_profile_path`; a Tier-1 hosting
  an LB needs `pool_allocation` set to an `LB_*` size, not the default `ROUTING`.
- **Avi / NSX ALB is reached through an enforcement point**, not through `/infra/lb-services` —
  the connection object is `AviConnectionInfo`. Getting this wrong means configuring the built-in
  NSX load balancer when the customer bought Avi.
- **VPN needs a local endpoint before a session**, and in 9.1 the gateway-scoped path is the one
  to use — the locale-service-scoped VPN paths are flagged deprecated in the spec.
- **IP allocation needs the block or pool to exist first**, and for a VPC the translated address
  has to come from the external block associated with that VPC.

## The licensing question you have to raise

VCF 9.0 narrowed the NSX load balancer entitlement: general-purpose LB was removed from the VCF
entitlement, Avi was made the recommendation, and NSX LB was retained only for VCF infrastructure
and vSphere Supervisor use cases. **This was not restated in the 9.1 support notes**, so its 9.1
status is unverified — not revoked, not confirmed. Either way
`/policy/api/v1/infra/lb-services` accepts the writes; entitlement is not enforced at the
endpoint. Raise it before building on NSX LB, and point at Avi.

## 9.1 additions worth knowing before you answer

`references/deltas.md` has the full table; these are the ones that change what you would say:

- **Distributed load balancing is decoupled from the DFW** in 9.1 per the release notes — though
  the 9.1 spec still lists Distributed Load Balancer among the services that
  `enable_firewall: false` turns off. Flagged in the reference files, not resolved.
- **The Virtual Network Appliance (VNA)** is new in 9.1 and is what makes VPC L4 load balancing
  and VPC IPSec VPN possible.
- **IPAM IP Blocks went from one CIDR / range to up to ten**, plus IP exclusions.
- **Locale-service-scoped VPN paths are deprecated** in favour of gateway-scoped ones.
- **Self-service Avi load balancing in the VCF Automation context**, alongside self-service NAT
  and VPN for tenants.

## Worked example

`references/9.1/services.md` carries a full **Tier-1 scoped SNAT rule** worked example — the
whole call sequence, with the real payload field names from the spec schema, the prerequisite
checks in order, and the rollback. Start from that rather than assembling calls from the tables;
it encodes the gateway/edge/NAT-section dependencies that the tables alone do not make obvious.

## When it isn't covered here

Fetch the appliance's own specification —
`GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json` — which is version-exact by
construction. Use `vcf-api-discovery` for the general case, and `nsx-security-policy`'s
`references/lookup.md` for the developer-portal navigation traps.

Do not extrapolate an endpoint from a pattern. `nat`, `nat-rules` and `{nat-id}` in particular are
easy to assemble into something plausible and wrong.

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
