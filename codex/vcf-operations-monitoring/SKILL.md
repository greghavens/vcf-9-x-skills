---
name: vcf-operations-monitoring
description: Query and configure VMware Cloud Foundation Operations monitoring in 9.0 and 9.1 through the /suite-api REST API — resources and inventory, stat/metric queries, alerts and alert definitions, reports and report schedules, custom groups, and the 9.1-only diagnostics findings, Salt, what-if and fleet-management trees. Use this for pulling metrics or alerts out of VCF Operations, building a custom group, scheduling a report, or working out why a stats query returns an empty series. Do NOT use it for Log Management or VCF Operations for Logs log queries, VCF Operations for Networks, or the real-time metrics PromQL API — those are `vcf-operations-logs-and-networks`. Do NOT use it for upgrading or patching VCF Operations, depots, bundles or prechecks — that is `vcf-lifecycle-upgrade`. Also use it whenever someone assumes a `/suite-api/api/dashboards` endpoint exists; no dashboard API is documented in either version, and that premise needs correcting first.
license: MIT-0
compatibility: Requires network reachability to a VCF Operations node for live calls. Reference material works offline.
---

# VCF Operations monitoring via /suite-api

The monitoring surface is the opposite of lifecycle: almost nothing changed between 9.0 and
9.1, and the risk is not a destructive mistake but a *silently empty answer* — a stats query
that returns `200` with no samples because the resource was never collecting.

> **Built from documentation, not from a live environment.** Every endpoint here was checked
> against the published OpenAPI inventories for its version, captured 2026-07-31. Nothing has
> been executed against a running VCF Operations deployment. Most of this surface is read-only
> and cheap to try; the write paths (alert definitions, custom groups, report schedules,
> resource deletion, Salt enablement) are not, and are flagged in the reference files.

## The one auth fact that belongs here

Authentication is `vcf-foundation`'s subject, with one exception worth stating inline because
it trips people who assume every VCF API is bearer-token: **the header is
`Authorization: OpsToken <token>`, not `Bearer`.** The token comes from
`POST /suite-api/api/auth/token/acquire` and lives six hours. In 9.1 a VCF SSO
`Authorization: Bearer <token>` is *also* accepted; in 9.0 it is not. Everything else about
token acquisition, auth sources and identity — go to `vcf-foundation`.

## Step 1 — resolve the version, then read one file

Use `vcf-foundation` to pin the version if you don't have it, or call
`GET /suite-api/api/versions/current` (`getCurrentVersionOfServer`, present in both).

| Target | Read |
|---|---|
| VCF Operations 9.0 monitoring | `references/9.0/monitoring.md` |
| VCF Operations 9.1 monitoring | `references/9.1/monitoring.md` |
| What changed between them | `references/deltas.md` |

The version files are near-identical by design, because the API is. Read the one that matches;
don't splice.

## Step 2 — prerequisites, before any query

The prerequisite block at the top of each version file is the highest-value part of this skill,
because the dominant failure mode here is a well-formed request that returns nothing useful.
Each entry states what must be true, **how to verify it**, and whether the other version
differs. The ones that actually bite:

- **The token expires after six hours** and there is no refresh — you re-acquire. A long-running
  collector script that worked yesterday fails partway through today.
- **Stats only exist for resources that are collecting.** A resource can be present in inventory
  (`GET /api/resources` returns it) and still have no metrics. The check is
  `resourceStatusStates[].resourceStatus == DATA_RECEIVING` and `resourceState == STARTED`.
- **The adapter instance and its cloud proxy have to be up.** `adapter-instance.lastCollected`
  and `collector.state` (`UP`/`DOWN`, `type: CLOUD_PROXY`) are the two fields that explain an
  empty result faster than anything else.
- **Stat keys are per resource kind.** Guessing a key returns an empty series, not an error.
  Enumerate with `GET /api/resources/{id}/statkeys` first.
- **Time ranges are epoch milliseconds**, and a range older than retention returns nothing.

## Step 3 — know what is genuinely 9.1-only

This is where wrong lists circulate. Diffed from the two spec inventories, the trees with
**zero** operations at 9.0 and some at 9.1 are exactly:

`fleet-management/*` (79) · `diagnostics/findings/*` (2) · `salt/*` (5) · `whatif/*` (6) ·
`workflows/requests/{requestId}` (1)

Two commonly-repeated claims are wrong and should be corrected on contact:

- **Chargeback is not 9.1-only.** 14 operations exist at 9.0; 9.1 adds 6.
- **Optimization is not 9.1-only.** 10 operations exist at 9.0 (the whole
  `optimization/workloadplacement/*` family); 9.1 adds 11 under `datacenters`, `reclaim` and
  `rightsizing`.

Likewise `logs/queryconfigs` is a 9.1-only *subtree* — `/api/logs` itself has 7 operations at
9.0. And `whatif` includes `serverconfigs`, not just `scenarios`.

The core monitoring surface — resources (66), alerts (13), alert definitions (8), reports (5),
report definitions and schedules (7), super metrics (5), symptoms (7) — is **identical in both
versions, operation for operation.** If you are only doing metrics, alerts and reports, the
version genuinely does not matter, and saying so plainly is more useful than hedging.

## Step 4 — there is no dashboards API

No dashboard endpoint appears in the 9.0 inventory, the 9.1 inventory, or the 9.1 raw
OpenAPI document; `dashboard` occurs there only as a `contentType` enum value inside
content-management import/export payloads. Legacy vROps had `/suite-api/api/dashboards`.
Whether it survives undocumented in 9.x is **UNVERIFIED**.

Do not invent it, and do not quietly substitute something adjacent. Say it was not found, and
point at the on-appliance Swagger UI — `https://<ops-fqdn>/suite-api/doc/swagger-ui.html`, note
the singular `doc` — which is the authoritative surface for that deployment's build. Content
management (`/api/content/*`, 10 operations in both versions) can move dashboard *content* as an
opaque bundle, which is a different thing from a dashboard CRUD API and should not be offered
as if it were one.

## Reading the reference files

Every endpoint is tagged **spec-confirmed (9.0)** or **spec-confirmed (9.1)** with its
`operationId`, so any claim can be traced back to a line in the inventory. Payload *field*
names come from the 9.1 raw OpenAPI document — the 9.0 raw document was not available, so
9.0 field-level detail is marked as inherited and is called out where it matters. Anything
the research could not establish is marked **UNVERIFIED** in place rather than smoothed over.

## When it isn't covered here

Use `vcf-api-discovery` or the on-appliance Swagger UI to confirm any operation not documented
in the references. Every endpoint in these files was checked against the published spec for its
version; hold anything you add to the same standard rather than inferring it from a neighbouring
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
