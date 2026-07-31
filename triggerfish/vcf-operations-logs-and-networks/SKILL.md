---
name: vcf-operations-logs-and-networks
description: "Query and configure the three VCF Operations surfaces that are not /suite-api — log search, ingest and forwarding (VCF Operations for Logs in 9.0, replaced by Log Management in 9.1); VCF Operations for Networks on /api/ni (entities, search QL, flows, 40 data-source families, applications, micro-segmentation); and the 9.1-only real-time metrics PromQL API. Use this for running a log query, forwarding logs to syslog, listing NI entities or flows, adding a network data source, or a PromQL query against real-time vCenter metrics. Start here whenever the log API is involved, because the product was replaced between versions: 9.0 is a 136-operation appliance API on port 9543 authenticated by a session from /api/v2/sessions, 9.1 is a 23-operation service API authenticated by an X-JWT-Token from token exchange. Do NOT use it for /suite-api resources, stats, alerts, reports or custom groups — that is vcf-operations-monitoring. Do NOT use it for upgrades, depots or bundles — that is vcf-lifecycle-upgrade."
license: MIT-0
compatibility: Requires network reachability to a VCF Operations node, a Log Management / Operations for Logs endpoint, or an Operations for Networks node for live calls. Reference material works offline.
version: 1.0.0
classification_ceiling: CONFIDENTIAL
requires_tools: "[\"curl\", \"jq\", \"git\"]"
network_domains: "[\"techdocs.broadcom.com\", \"developer.broadcom.com\", \"github.com\"]"
---

# VCF Operations logs, networks and real-time metrics

Three products that share a brand and share nothing else. The risk here is not a destructive
mistake — it is **writing 9.0 code against a 9.1 deployment**, because the log product was
replaced between versions and nearly every fact about it changed: spec file, operation count,
port, header, query language.

> **Built from documentation, not from a live environment.** Every endpoint here was checked
> against the published OpenAPI inventories for its version, captured 2026-07-31. Nothing has
> been run against a live deployment. Most of this is read-only and cheap to try; the write
> paths — data-source create/delete/disable, log-forwarder changes, agent-secret revocation,
> `PUT .../metrics_config` — are not, and are flagged in the references.

## The thing to say first

**The log product is not the same product in 9.0 and 9.1.** Billed as the platform's sharpest
rename, it is not a rename but a replacement, and nothing carries over except the two ingest
paths — changing the hostname in a 9.0 log script will not make it work at 9.1.

| | 9.0 | 9.1 |
|---|---|---|
| Name | VCF Operations for **Logs** | **Log Management** |
| Spec | `vcf-operations-for-logs-openapi.json` | `log-management-openapi.json` — a *different file* |
| Operations | **136** | **23** |
| Where | `https://<host>:9543/api/v2` | address and port resolved from token exchange |
| Auth | `Authorization: Bearer <sessionId>` from `POST /api/v2/sessions` | `X-JWT-Token: <jwt>` from `/suite-api/api/auth/token/exchange` |
| Query | `GET /events/text/CONTAINS%20foo/timestamp/LAST%20360000` | `POST /api/v2/logs/search` with an Elasticsearch-style JSON DSL |

## What 136 → 23 actually means — the honest version

Do not repeat the number without the explanation. Diffing the inventories tag by tag:

- **99 of the 113 lost operations (88%) are scope transfer, not capability loss.** 9.0's log
  product was a standalone appliance whose API owned identity (40 ops), appliance lifecycle
  (40 ops: cluster VIPs, deployment, upgrades, NTP, certificates, salt) and vCenter registration
  (19 ops). At 9.1 the log service lives inside VCF Operations; none of that is its job now.
- **~24 operations are a genuine gap:** datasets (5), limits (3), notifications/webhooks (13),
  extracted-field update/delete, forwarder batch. Where they went is **UNVERIFIED** — plausible
  `/suite-api` homes exist, but no source states the mapping.
- **The query surface got *more* expressive, not less** — one `POST` with a nestable bool DSL
  and 15 aggregation types replaces two path-constrained `GET`s. And **10 are net-new**: agent
  groups (6) and agent secrets (4).

So: a re-scoping with a real capability gap around the edges — not a pure scope cut and not a
pure re-scoping. Arithmetic in `deltas.md`.

## The three token flows — the crux of this skill

General auth is `vcf-foundation`'s. These belong here: mutually incompatible, dominant failure mode.

| Product | Header | Token from |
|---|---|---|
| Log Management `[9.1]` | `X-JWT-Token: <jwt>` | ① OpsToken from `POST /suite-api/api/auth/token/acquire` → ② `POST /suite-api/api/auth/token/exchange` with `{"serviceKeys":["ops-li"]}` |
| Real-time metrics `[9.1]` | `Authorization: Bearer <jwt>` | ① OpsToken → ② find the key whose `type` is `VCF_VODAP` in `GET /suite-api/api/integrations/services` → ③ exchange that key |
| Ops for Networks `[9.0+9.1]` | `Authorization: NetworkInsight <token>` | `POST /api/ni/auth/token` — its own login, unrelated to VCF Operations |
| Ops for Logs `[9.0]` | `Authorization: Bearer <sessionId>` | `POST /api/v2/sessions` on the log appliance, port 9543 |

**The ordering is not optional.** Neither 9.1 product has a login endpoint of its own — no
`/sessions`, no `/auth`, no `/login` in either spec. You must hold an OpsToken *before* you can
obtain the JWT, and the 401 for skipping step one arrives from the *downstream* service, so it
reads as if the log service were broken. 9.1 also adds a second scheme to Networks (HTTP
bearer, VCF Ops JWT) that does **not** exist at 9.0.

## Step 1 — resolve the version, then read one file

Pin the version with `vcf-foundation`, or `GET /suite-api/api/versions/current`
(`getCurrentVersionOfServer`, in both).

| Target | Read |
|---|---|
| VCF 9.0 — Operations for Logs, Operations for Networks | `references/9.0/logs-and-networks.md` |
| VCF 9.1 — Log Management, real-time metrics, Operations for Networks | `references/9.1/logs-and-networks.md` |
| What changed between them | `references/deltas.md` |

Unlike the monitoring skill, **these version files are not near-identical** — the Logs half is a
different product. The Networks half is, so the 9.1 file points back to the 9.0 file rather than
repeating 632 operations.

## Step 2 — prerequisites, before any call

Each version file opens with a prerequisite block — what must be true, **how to verify it**, and
whether the other version differs. The ones that bite:

- **`[9.1]` Get the OpsToken first, then exchange** (T1/T2 in the 9.1 file). All else is downstream.
- **`[9.1]` Pass `?includeServiceDetails=true` on the exchange** — it defaults to `false`, and
  without it you have a token and no idea where to send it. The spec's `http://localhost:8787`
  is a *"Generated server url"* build artifact and the exchange example shows port **8000**;
  resolve address and port per deployment.
- **`[9.0+9.1]` Networks allows 100 valid tokens per user, then 401s** — `DELETE /auth/token`
  after use, or a CI job starts failing on the 101st run, looking like a credential problem.
  Entity lists default to `size: 10`, and `GET /metrics/v2` caps at **300 points per response**.
- **`[9.0]` Log queries default to events from one minute ago or newer**, limit 100, timeout
  30 s — the most common cause of "the API returned nothing." **`[9.1]`** auth failures on Log
  Management surface as **`403`, not `401`**.

## Step 3 — Operations for Networks barely moved; the deprecations are the story

632 → 636 operations, base `/api/ni` in both, **zero `operationId` changes** on any shared path.
5 added (2 inventory-tree, `getLicensesV2`, `getFipsModulesDetails`, a renamed migration wave),
1 removed (`GET /migration/{groupType}` → `GET /migration/wave/{groupType}`, still deprecated).
What matters is that **22 operations are newly deprecated at 9.1**: the complete AWS (7), Azure
(7) and NSX-ALB (7) data-source families, which get **no replacement path**, plus
`GET /settings/licensing/` superseded by `/settings/licensing/v2`. Enumerated in `deltas.md`.
Pinboards (12) and metrics v1 (2) get misreported as 9.1 changes and are not — 31 operations
were already deprecated at 9.0, and all 31 still are.

## Step 4 — evidence quality, and where it runs out

The dossier could not retrieve concrete paths for either Log Management or Operations for
Networks — the portal returned "Object Not Found" for both indexes, and it warned *"the
commonly-assumed legacy `/api/ni/...` prefix was not confirmed anywhere in this research — do
not assume it."* **The specs are this skill's evidence and they close that gap:** `/api/ni` is
the declared server URL in both versions, and all 23 Log Management paths are in the 9.1 spec.
Say so when it matters — someone writing a change record needs to know the source is the spec
repository, not the doc portal. Every endpoint is tagged **spec-confirmed (9.0)** or **(9.1)**
with its `operationId`; a few genuinely have none and are cited by method and path. Where the
specs are silent, the references mark it **UNVERIFIED** rather than filling it in from Log
Insight or vRNI habit — the largest being **queryable field names** for a 9.1 log search, which
you discover from `fields[].internalName` on a `match_all` result. For anything not covered, use
`vcf-api-discovery` or the on-appliance Swagger UI, held to the same standard rather than
inferred from a neighbouring path — which on an API where `cisco-asr-xr-switches` and
`cisco-asrxr-switches` are two different prefixes is not theoretical.

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
