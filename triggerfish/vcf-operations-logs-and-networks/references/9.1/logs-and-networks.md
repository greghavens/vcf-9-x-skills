# VCF 9.1 — Log Management, Real-Time Metrics and Operations for Networks Reference

**Scope:** VMware Cloud Foundation 9.1.x, three products: **Log Management** (23 operations,
base `/api/v2`), **Real-time metrics** (4 operations, PromQL, `/api/v1`), and **VCF Operations
for Networks** (636 operations, base `/api/ni`). Everything here is `[9.1]` unless tagged
otherwise. The `/suite-api` monitoring API is **out of scope** — see
`vcf-operations-monitoring`.

**Sources.**
- `SPECLM9.1` = `research/spec-inventory/9.1__log-management.ops.json` — **23 operations**,
  spec version `9.1.0.0`, title "Log Management API", from git tag `9.1.0.0` of
  `github.com/vmware/vcf-api-specs`.
- `RAWLM9.1` = `specifications/vcf-operations/log-management-openapi.json` at the same tag —
  OpenAPI 3.0.1. `servers: [{ "url": "http://localhost:8787", "description": "Generated server
  url" }]`; `security: [{ "OPSTokenAuthorization": [] }]`; one scheme,
  `OPSTokenAuthorization` (`type: apiKey`, `in: header`, `name: X-JWT-Token`).
- `SPECRTM9.1` = `research/spec-inventory/9.1__realtime-metrics.ops.json` — **4 operations**.
- `RAWRTM9.1` = `specifications/vcf-operations/realtime-metrics/realtime-metrics-openapi.yaml`
  (+ `-params.yaml`, `-defs.yaml`) at the same tag — OpenAPI 3.0.2.
  `servers: [{ "url": "http://localhost:8080/" }]`; `security: [{ "bearerAuth": [] }]`
  (`type: http`, `scheme: bearer`).
- `SPECNI9.1` = `research/spec-inventory/9.1__vcf-operations-for-networks.ops.json` —
  **636 operations**, base `/api/ni`, spec version `9.1.0.0`.
- `RAWNI9.1` = `specifications/vcf-operations/vcf-operations-for-networks-openapi.yaml` at the
  same tag. `servers: [{ "url": "/api/ni" }]`; `security: [{ ApiKeyAuth }, { OpsTokenAuth }]`;
  **two** schemes.
- `RAWOPS9.1` = `specifications/vcf-operations/vcf-operations-openapi.json` at the same tag —
  used only for the token-exchange and integrations-services schemas.
- `SPECLOG9.0` = the 9.0 `vcf-operations-for-logs` inventory, used to state what a 9.0
  operation's fate is.
- `DOPS` = `research/vcf-operations.md`. `DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md`.

Every path below was checked against its inventory and is marked **spec-confirmed (9.1)** with
its `operationId`, or noted where the spec supplies none.

> **The dossier could not confirm these paths from the doc portal.** `DOPS` §Gaps items 4 and 5
> record that the developer-portal indexes for Log Management and Operations for Networks both
> returned "Object Not Found", and that a speculative Log Management path
> (`/api/v2/events/query`) was tried and **not** confirmed [S26]. **The OpenAPI specs are the
> evidence for this file.** Where the specs are silent the fact is marked UNVERIFIED rather
> than filled in from Log Insight or vRNI habit.

> **Documentation-derived, not live-validated.** Captured 2026-07-31. Nothing here has been
> executed against a running deployment. Log search, PromQL queries and Networks reads are
> cheap to try; agent-secret revocation, log-forwarder changes, data-source mutation and
> `PUT .../metrics_config` are not, and are flagged where they appear.

---

## Contents

- [Prerequisites](#prerequisites)
  - **T1 — An OpsToken first. Everything else depends on this ordering**
  - T2 — Exchange the OpsToken for a service JWT
  - T3 — Log Management: send it as `X-JWT-Token`, not `Authorization`
  - T4 — Log Management: discover the real address and port; do not use 8787 blindly
  - T5 — Real-time metrics: find the `VCF_VODAP` service key, then send `Authorization: Bearer`
  - T6 — Real-time metrics: vCenter metrics collection must be enabled
  - N1 — Networks: a NetworkInsight token, or (new at 9.1) a VCF Ops JWT
  - N2 — Networks: 100 valid tokens per user, then 401
  - N3 — Networks: the data source must be registered, and three families are now deprecated
  - N4 — Networks: entity IDs, not names
  - P0 — Things this file could not verify
- [The three token flows, side by side](#the-three-token-flows-side-by-side)
- [Part 1 — Log Management (23 operations)](#part-1--log-management-23-operations)
  - [Query — the whole read surface, in two operations](#query--the-whole-read-surface-in-two-operations)
  - [The query DSL](#the-query-dsl)
  - [Aggregations](#aggregations)
  - [Ingest](#ingest)
  - [Agent secrets](#agent-secrets)
  - [Agent groups](#agent-groups)
  - [Extracted fields](#extracted-fields)
  - [Log forwarders](#log-forwarders)
  - [Saved queries live in `/suite-api`, not here](#saved-queries-live-in-suite-api-not-here)
  - [What is NOT in the 23](#what-is-not-in-the-23)
- [Worked example — run a log query on 9.1](#worked-example--run-a-log-query-on-91)
- [Part 2 — Real-time metrics (4 operations)](#part-2--real-time-metrics-4-operations)
- [Part 3 — VCF Operations for Networks (636 operations)](#part-3--vcf-operations-for-networks-636-operations)
  - [What changed from 9.0](#what-changed-from-90)
  - [Authentication](#authentication)
  - [Entities, search, metrics](#entities-search-metrics)
  - [Inventory trees — new at 9.1](#inventory-trees--new-at-91)
  - [Licensing v2 and FIPS — new at 9.1](#licensing-v2-and-fips--new-at-91)
  - [Data sources — 304 operations, 21 newly deprecated](#data-sources--304-operations-21-newly-deprecated)
  - [Everything else](#everything-else)
- [What is not here](#what-is-not-here)
- [Still unverified](#still-unverified)

---

## Prerequisites

Nothing below should be attempted until these hold. Each states what must be true, **how to
verify it**, and whether 9.0 differs. **T1 and T2 are the most important items in this skill**,
because two of the three products here cannot be reached at all without them, in that order.

### T1 — An OpsToken first. Everything else depends on this ordering `[9.1]`

**Must be true:** you already hold a VCF Operations token *before* you touch Log Management or
real-time metrics. The order is fixed and non-negotiable:

```
1. POST /suite-api/api/auth/token/acquire     -> OpsToken          (VCF Operations)
2. POST /suite-api/api/auth/token/exchange    -> jwtToken          (VCF Operations, authenticated with the OpsToken from step 1)
3. call Log Management with X-JWT-Token: <jwtToken>
   or  call real-time metrics with Authorization: Bearer <jwtToken>
```

There is **no direct login** to Log Management and **no direct login** to real-time metrics.
Neither spec contains an authentication operation of any kind — `SPECLM9.1`'s 23 operations
include no `/sessions`, no `/auth`, no `/login`; `SPECRTM9.1`'s 4 are query, query_range,
metadata and a config PUT. The only credential either accepts is a JWT minted by VCF
Operations. If step 1 fails, nothing downstream is reachable, and the error you will see is a
401 from the *downstream* service, which reads as if the log service were broken.

Step 1: `POST /suite-api/api/auth/token/acquire` — **spec-confirmed (9.1)**, `acquireToken`;
also present at 9.0. Body `{"username","password","authSource"}`; response `token`, `validity`,
`expiresAt`, `roles[]`; **six-hour TTL, no refresh** [`DOPS`]. Header on the exchange call:
`Authorization: OpsToken <token>`.

**How to verify step 1:** `GET /suite-api/api/auth/currentuser` (`getCurrentUser`) returns 200.

**9.0 difference:** the whole flow is absent. `POST /api/auth/token/exchange` **does not exist
at 9.0** — it is one of the 134 operations added in 9.1 [`DELTA`; both `/suite-api`
inventories]. At 9.0 the log product authenticated itself, on its own port, with its own
session (see `references/9.0/logs-and-networks.md` L2).

Acquisition beyond this — auth sources, VCF SSO, roles — is `vcf-foundation`'s subject.

### T2 — Exchange the OpsToken for a service JWT `[9.1]`

**Must be true:** you have called `POST /suite-api/api/auth/token/exchange` —
**spec-confirmed (9.1)**, `exchangeOpsTokenWithJwtToken`, **absent at 9.0** — with the right
service key, and kept the `jwtToken` from the response.

Request body `TokenExchangeRequest` [`RAWOPS9.1`]: `serviceKeys[]` — **required**, `minItems: 1`,
`uniqueItems: true`. The spec's own request example is:

```json
{ "serviceKeys": [ "ops-li", "ops-ni" ] }
```

Response `TokenExchangeResponse`: `jwtToken` (*"The JWT token received after a successful token
exchange"*) and `services[]` of `ServiceDetails` — `name`, `type`, `key`, `address`,
`addressType`, `port`, `basePath`, `certificates[]`, `version`.

Optional query parameter `includeServiceDetails` (boolean, **default `false`**) —
*"Set to true to fetch the requested service details, such as the address, port, etc."*
**Pass it.** Without it you get a token and no idea where to send it (T4).

The spec's response example, verbatim, is the best available evidence for what the keys mean:

```json
{ "jwtToken": "token",
  "services": [
    { "name": "VCF OPS LI", "type": "VCF_OPS_LI", "key": "ops-li",
      "address": "0.0.0.0", "port": 8000, "addressType": "IPV4",
      "certificates": [], "version": "9.1.0.0" },
    { "name": "VCF OPS NI", "type": "VCF_OPS_NI", "key": "ops-ni",
      "address": "0.0.0.0", "port": 8000, "addressType": "IPV4",
      "certificates": [], "basePath": "base-path", "version": "9.1.0.0" } ] }
```

**Known service keys:**

| Key | Service | Attested by |
|---|---|---|
| `ops-li` | Log Management | `RAWLM9.1` security-scheme description, verbatim; `DOPS` [S18]; `RAWOPS9.1` example |
| `ops-ni` | VCF Operations for Networks | `RAWOPS9.1` request and response examples only |
| *(discover)* | Real-time metrics — the key whose `type` is `VCF_VODAP` | `RAWRTM9.1` info description; `DOPS` [S19] |

> **`ops-ni` is spec-example evidence, not a documented instruction.** No source available here
> states that Networks' `OpsTokenAuth` bearer token is obtained this way — only that the key
> `ops-ni` exists and that Networks accepts a "VCF Ops JWT Token". The connection is
> **inferred**. The documented Networks path remains `POST /api/ni/auth/token` (N1).

**How to verify:** the response contains a non-empty `jwtToken`, and `services[]` contains an
entry whose `key` matches what you asked for. A bad key returns **400** — *"Invalid service key
provided"*.

**9.0 difference:** absent entirely.

### T3 — Log Management: send it as `X-JWT-Token`, not `Authorization` `[9.1]`

**Must be true:** the header is

```
X-JWT-Token: <jwtToken>
```

This is attested by the security scheme itself, not just prose: `RAWLM9.1`'s
`OPSTokenAuthorization` is `type: apiKey`, `in: header`, `name: X-JWT-Token`, and its
description reads, verbatim:

> Authenticated requests must include an X-JWT-Token header with a token retrieved with the
> following authenticated call to VCF Operation API : POST /suite-api/api/auth/token/exchange
> Request body {"serviceKeys": ["ops-li"]}. Access is allowed only to resources that the user
> is authorized to use.

The same text appears as the spec's `info.description`. `security` is applied globally, so it
covers **all 23 operations**, including ingest.

**Do not send `Authorization: Bearer`** — that is the *real-time metrics* form (T5) and the
*9.0 Operations-for-Logs* form. Three products, three different headers, and the JWT for one is
not interchangeable with the JWT for another (different `serviceKeys`).

**How to verify:** any read, e.g. `GET /api/v2/logs/forwarders` (`getAllLogForwarders`), should
return 200 rather than 403. The declared error responses across this spec are 400 / 403 / 404 /
500 / 502 — note **403, not 401**, is the auth-failure code on most operations.

**9.0 difference:** total. 9.0 used `Authorization: Bearer <sessionId>` where the session ID
came from `POST /api/v2/sessions` on the log appliance itself.

### T4 — Log Management: discover the real address and port; do not use 8787 blindly `[9.1]`

**Must be true:** you know where the service actually is. `RAWLM9.1` declares
`servers: [{"url": "http://localhost:8787", "description": "Generated server url"}]`. The
description string *"Generated server url"* is the Spring/springdoc default — this is a
**build-time artifact of the machine that generated the spec**, not a deployment fact. It tells
you the service listens on **8787** on its own host; it does not tell you the host, the scheme,
or whether a gateway fronts it. The token-exchange example in `RAWOPS9.1` shows `port: 8000`
for `VCF_OPS_LI`, which is a *different* number — so the two sources disagree, and the only
per-deployment truth is the one you fetch.

**How to verify / how to resolve:** call the exchange with `?includeServiceDetails=true` (T2)
and read `address`, `port` and `basePath` off the `services[]` entry whose `key` is `ops-li`.
Or list them first: `GET /suite-api/api/integrations/services` — **spec-confirmed (9.1)**,
`getIntegratedServices`, **absent at 9.0** — returns `servicesDetails[]` of the same
`ServiceDetails` shape.

> **UNVERIFIED:** whether Log Management is also reachable through the VCF Operations FQDN on a
> proxied path rather than directly on its own address and port. Nothing in the sources states
> one way or the other. Resolve it from `ServiceDetails` per deployment.

**9.0 difference:** 9.0 was unambiguous — *"Use HTTPS on port `9543`"*, stated in the spec's own
description. **9543 is not a 9.1 port.**

### T5 — Real-time metrics: find the `VCF_VODAP` service key, then send `Authorization: Bearer` `[9.1]`

**Must be true:** you have followed the three steps that `RAWRTM9.1`'s `info.description`
spells out verbatim:

1. `POST https://<vcf-operations-fqdn>/suite-api/api/auth/token/acquire` with
   `{"username","password"}` → an OpsToken.
2. `GET https://<vcf-operations-fqdn>/suite-api/api/integrations/services` with
   `Authorization: OpsToken <ops-token>` — *"find the key where type = VCF_VODAP"*.
3. `POST https://<vcf-operations-fqdn>/suite-api/api/auth/token/exchange` with
   `Authorization: OpsToken <ops-token>` and `{"serviceKeys": ["<vodap-service-key>"]}`.

Then: `Authorization: Bearer <jwt-token>`.

Note the extra step relative to Log Management: **the VODAP service key is not a literal.** The
docs give the `type` (`VCF_VODAP`) and tell you to look up the `key`, which means the key string
is deployment-supplied. Hard-coding `"VCF_VODAP"` as the *key* is a guess — it is documented as
the *type*. That distinction is the difference between a 200 and a 400.

**How to verify:** `GET /api/v1/metadata` (`queryMetricMetadata`) returns
`{"status": "success", "data": {...}}`. `401` means the JWT is wrong or expired; `403` means the
user is not authorized for the resource.

**9.0 difference:** the product does not exist at 9.0 — absent from the 9.0 BOM [`DOPS`], no
spec at tag `9.0.0.0` [`DELTA`].

### T6 — Real-time metrics: vCenter metrics collection must be enabled `[9.1]`

**Must be true:** the vCenter you are querying has metrics collection turned on. Real-time
metrics scrapes vCenter; a PromQL query against a vCenter that is not being collected returns
an empty result, not an error.

**How to verify:** `GET /api/v1/metadata` — *"Returns metadata about metrics currently scraped
from targets"* — optionally filtered by `metric` and `sourceId`. If a metric name does not
appear there, no query will return it. Confirm the metric name from metadata before writing
PromQL, the same discipline as stat keys on `/suite-api`.

**How to change it (write path):** `PUT /api/v1/vcenters/{vcId}/metrics_config` —
**spec-confirmed (9.1)**, `updateVcMetricsConfig`. Body `VcMetricsConfigRequestBody`:
`standard` (boolean, *"Enable/disable VC standard metrics"*), `verbose` (boolean), and
`esxTopHostMoids[]` of `{moid, operation}` where `operation` is `ADD | REMOVE`. The description
names the two collection profiles as **STANDARD** and **VERBOSE**.

> **This is a production collection-configuration change.** Enabling `verbose` across a large
> vCenter increases scrape volume; the sources do not quantify by how much. `DOPS` records from
> the 9.1 What's New that default sampling is 20 seconds, configurable to 2 seconds for ESX —
> but **the 2-second/20-second setting is not exposed by any of the four operations in this
> spec**, so where it is configured is **UNVERIFIED**.

**9.0 difference:** n/a.

### N1 — Networks: a NetworkInsight token, or (new at 9.1) a VCF Ops JWT `[9.1]`

**Must be true:** one of two headers is present. `RAWNI9.1` declares a top-level
`security: [{ApiKeyAuth}, {OpsTokenAuth}]` — either satisfies it:

```
Authorization: NetworkInsight {token}     # ApiKeyAuth — from POST /api/ni/auth/token
Authorization: Bearer {token}             # OpsTokenAuth — "VCF Ops JWT Token - Bearer {token}"
```

The documented acquisition path is still `POST /auth/token` — **spec-confirmed (9.1)**,
`create`; also at 9.0. Body `UserCredential { username, password, domain{domain_type: LDAP|LOCAL,
value} }`; response `Token { token, expiry }` where `expiry` is *"expiry epoch time in secs."*

**How to verify:** `GET /info/version` — **spec-confirmed (9.1)**, `getVersion`.

**9.0 difference — and it only breaks one way.** `RAWNI9.0` declares **one** scheme
(`ApiKeyAuth`) and **no top-level `security` block**. `OpsTokenAuth` is **9.1-only**. A script
that sends a VCF Ops bearer JWT to Networks will work at 9.1 and has no spec support at 9.0.
`DOPS` §"Other components' auth" tags both schemes `[9.0+9.1]` but explains why — *"the portal
does not version-split these two schemes"*. **The specs do split them; trust the specs.**

> Where the `OpsTokenAuth` JWT comes from is **not stated by any source here**. The `ops-ni`
> service key in the token-exchange examples (T2) is the obvious candidate and is **inferred**,
> not documented.

### N2 — Networks: 100 valid tokens per user, then 401 `[9.0+9.1]`

**Must be true:** you delete tokens after use. From `POST /auth/token`'s description
[`RAWNI9.1`], verbatim: *"There is limit of 100 valid tokens per user and further requests will
return 401-Unauthorized. So, users are advised to delete the tokens after use."*

**How to verify / fix:** `DELETE /auth/token` — **spec-confirmed (9.1)**, `delete`; deletes the
token in the header, returns `204`. Expired tokens are *"cleaned periodically by the system"*.

**9.0 difference:** none.

### N3 — Networks: the data source must be registered, and three families are now deprecated `[9.1]`

**Must be true:** the vCenter / NSX / switch / firewall you are querying is a registered data
source, and it is not one of the families deprecated at 9.1.

**How to verify:** `GET /data-sources/health` (`getDatasourceHealth`) — **spec-confirmed (9.1)**
— across all sources,
or the per-family list, e.g. `GET /data-sources/vcenters` (8 operations),
`GET /data-sources/nsxt-managers` (7).

**9.0 difference — this is the change that bites.** **21 operations across three families are
newly deprecated at 9.1**: `aws-accounts` (7), `azure-subscriptions` (7) and `nsxalb` (7). They
were **not** deprecated at 9.0. They still respond; the spec flags them `deprecated: true` and
offers **no replacement path**. Full enumeration in `deltas.md`.

### N4 — Networks: entity IDs, not names `[9.0+9.1]`

**Must be true:** you have `entity_id` values, which look like `18230:1:1158969162`
[`RAWNI9.1` `listVms` response example] — not UUIDs, not names.

**How to verify / get them:** `POST /search` (`searchEntities`) or `POST /search/ql` (`search`);
`POST /entities/names` (`getNames`) and `GET /entities/names/{id}` (`getName`) for ID → name;
`POST /entities/fetch` (**no `operationId` in the spec**) for bulk detail, *"Max batch size is
1000"*.

**9.0 difference:** none.

### P0 — Things this file could not verify

- **Where Log Management actually listens** in a real deployment (T4).
- **The literal VODAP service key** (T5) — only its `type` is documented.
- **Where the Networks `OpsTokenAuth` JWT comes from** (N1) — `ops-ni` is inferred.
- **Role, privilege and capability names** on any of the three products.
- **Log retention, metric retention and PromQL lookback limits.**
- **Rate limits** on any operation here.

---

## The three token flows, side by side

The crux of this skill. Three products, three headers, three token sources — and the JWTs are
not interchangeable, because each is minted for specific `serviceKeys`.

| Product | Header | Token from | New at 9.1? |
|---|---|---|---|
| **Log Management** | `X-JWT-Token: <jwt>` | `POST /suite-api/api/auth/token/exchange`, `{"serviceKeys":["ops-li"]}`, authenticated with an OpsToken | Yes — replaces 9.0's `Authorization: Bearer <sessionId>` from `POST /api/v2/sessions` |
| **Real-time metrics** | `Authorization: Bearer <jwt>` | Same exchange, with the service key whose `type` is `VCF_VODAP` (look it up via `GET /suite-api/api/integrations/services`) | Yes — no 9.0 product |
| **Operations for Networks** | `Authorization: NetworkInsight <token>` | `POST /api/ni/auth/token` — the product's own login | No, unchanged |
| **Operations for Networks (alt.)** | `Authorization: Bearer <jwt>` | `OpsTokenAuth`; source **inferred** as the `ops-ni` exchange | **Yes — 9.1 adds this scheme** |

General auth — acquisition, auth sources, SSO, roles — is `vcf-foundation`. What belongs here
is only the above: which header, which token, in which order.

---

## Part 1 — Log Management (23 operations)

**This is a different product from 9.0's VCF Operations for Logs, not a new version of it.** A
different spec file, a different operation set, a different base, a different port, a different
auth model, and a different query language. `DELTA` records it as
*"`vcf-operations-for-logs` — spec removed in 9.1"* and *"`log-management` — spec is new in
9.1."* Do not port a 9.0 log script by changing the hostname.

Tags and counts from `SPECLM9.1`, summing to 23: `Agent Groups` 6, `Log Forwarder` 7,
`Agent Secret` 4, `Ingest` 2, `Query` 2, `Extracted Fields` 2.

### Query — the whole read surface, in two operations

| Call | operationId | Status |
|---|---|---|
| `POST /api/v2/logs/search` | `executeLogSearchQuery_1` | **Current.** Use this one |
| `POST /api/v2/search` | `executeLogSearchQuery` | **`deprecated: true` in the 9.1 spec** |

Both **spec-confirmed (9.1)**, both take the same `QueryRequest` body and return the same
`QueryResponse`. The deprecated one is the shorter path. The `_1` suffix on the current
operation's `operationId` is a generator artifact of the duplicate — it is what the spec says,
so cite it as-is.

That is the **entire** read surface. There is no list-events endpoint, no dataset endpoint, no
`GET` query form. If you need logs out of a 9.1 deployment, it is `POST /api/v2/logs/search`.

### The query DSL

`QueryRequest` [`RAWLM9.1`] — no property is marked required:

| Field | Type | Constraint | Meaning |
|---|---|---|---|
| `query` | `Query` | — | The filter. See below |
| `aggregations` | map of name → `Aggregation` | — | Named aggregations |
| `sort` | array of `SortOptions` | — | Map of field → `{order: asc\|desc}` |
| `size` | integer | **maximum 2000** | Hits to return |
| `from` | integer | **maximum 20000** | Offset |
| `trackTotalHits` | boolean | — | Whether `events.total` is exact |
| `indices` | array of string | — | Indices to search |
| `scroll`, `scrollSize` | string, integer | — | Scroll cursor |

`Query` is an **Elasticsearch-shaped** object with these mutually-combinable clauses:

| Clause | Shape |
|---|---|
| `match_all` | `{}` (`MatchAllQuery` has no properties) |
| `term` | map field → `FieldValue {value, case_insensitive}` |
| `terms` | map field → array of `FieldValue` |
| `match_phrase` | map field → string |
| `prefix` | map field → string |
| `regexp` | map field → `FieldValue` |
| `range` | map field → `RangeQueryValue {gt, gte, lt, lte}` — **all four are `string`** |
| `exists` | `ExistsQuery {field}` — `field` **required**, `minLength: 1` |
| `bool` | `BoolQuery {must[], must_not[], should[], filter[]}`, each an array of `Query` |

`QueryResponse`: `events` (`EventsResult {hits[], total}`), `aggregations`
(`AggregationResult`), `timeTakenMillis`, `timedOut` (boolean), `failureMessage`,
`failureReason` — enum `SYSTEM | QUERY | DATA_AVAILABILITY | OTHER`.

Each hit is a `LogMessage` with one property, `msgContent` (`MessageContent`):

- `originalText` — the raw log line
- `logTimestamp` (`int64`) — the event's own timestamp
- `ingestTimestamp` (`int64`) — when it arrived
- `incomingAddress` — the sender
- `fields[]` of `Field`: `internalName`, `displayName`, `value`, `valueType`
  (`STRING | NUMBER | BOOLEAN | MESSAGE_TEXT | EVENT_TYPE | UNSUPPORTED`), `fieldCategory`
  (`INDEXED | EXTRACTED | NON_INDEXED`), `startPosition`, `length`.
  (`Field.fieldType` — `STATIC | EXTRACTED | NON_INDEX` — is itself marked `deprecated` in the
  schema; use `fieldCategory`.)

Two things the spec does **not** say and you should not assume:

> **UNVERIFIED — the field name for time.** `RAWLM9.1` gives no example query and names no
> timestamp field for the `range` clause. `MessageContent` has `logTimestamp` and
> `ingestTimestamp`, but whether those are the queryable field names is not stated. Enumerate
> real field names from a `match_all` result's `fields[].internalName`, or from
> `GET /api/v2/fields/extractedFields`, before writing a `range`.
>
> **UNVERIFIED — the default time window.** 9.0 defaulted to "one minute ago or newer" and said
> so. The 9.1 spec states no default range at all.

### Aggregations

`aggregations` is a map of your own names to `Aggregation` objects. Available sub-aggregations
[`RAWLM9.1`]:

- Bucket: `date_histogram` (`DateHistogramAggregation` — `field`* and `fixed_interval`* both
  **required**, plus `order`), `multi_terms` (`terms[]` of `MultiTermLookup {field*}`, `size`,
  `min_doc_count`, `shard_size`, `order[]`), `composite` (`sources[]`, `size`), `sample`,
  `top_hits` (`_source[]`, `from`, `size`, `sort[]`).
- Value: `avg`, `min`, `max`, `sum`, `cardinality` (`field`* required), `value_count`,
  `stddev`, `variance`.
- Nesting: `Aggregation.aggregations` is itself a map of `Aggregation` — sub-aggregations nest.
- `bucketAggregation` and `valueAggregation` are booleans on `Aggregation`; their semantics are
  **UNVERIFIED** (they read as generator-exposed internals).

`AggregationResult`: `buckets[]` of `AggregationBucket {key[], doc_count, field[] of
AggregationField{internalName, displayName}, values[] of AggregationValue{name, value}}`, plus
`total` and `truncated`. **Check `truncated`** — it is this API's equivalent of 9.0's
`complete` flag.

This replaces 9.0's entire `GET /aggregated-events/{+path}` operation with its
`aggregation-function` / `bin-width` / `group-by-field` query parameters. A `date_histogram`
with `fixed_interval` is the direct analogue of `bin-width` + `COUNT`.

### Ingest

| Call | operationId | Body |
|---|---|---|
| `POST /api/v2/events` | `ingestJsonEvents` | A **JSON array** of `JsonApiEvent {timestamp (int64), text, fields (map)}` |
| `POST /api/v2/events/ingest/{agentId}` | `ingestEvents` | `IngestRequest {events[] of CFApiEvent, messages[] of CFApiEvent, parserName}` |

Both **spec-confirmed (9.1)**. **Both paths are byte-identical to 9.0's** (`POST_events`,
`POST_events-ingest-agentId`) — ingest is the one part of the log API that survived the product
replacement unchanged in shape. The request *schemas* differ: 9.1's `CFApiEvent` uses
`fields[]` of `EventField {name, content, startPosition, length}`; 9.1 adds `messages[]` and
`parserName` alongside `events[]`.

Declared limits, from both operations' descriptions [`RAWLM9.1`], verbatim:

> The ingestion API has the following limits: JSON payload - 1MB, Log message size - 16KB,
> Field name size - 64 characters

Note **1 MB**, down from 9.0's documented 4 MB. The 16 KB message limit is unchanged. The
64-character field-name limit is new in the 9.1 text.

Response `IngestResponse {status, message, received}`.

> **Spec artifact, not a real parameter.** Both ingest operations declare a **required query
> parameter named `httpRequest`** whose schema is `ServerHttpRequest` — a Spring framework type
> (with `SslInfo`, `HttpCookie`, `DataBuffer` and friends dragged into `components.schemas`
> alongside it). This is the framework leaking into the generated document. Do not attempt to
> send it. The same applies to the `pageable` "query parameter" on the two list operations,
> which is really `?page=&size=&sort=` (schema `Pageable {page ≥0, size ≥1, sort[]}`).

> **9.0's unauthenticated-agent behavior is gone.** At 9.0, `POST /events/ingest/{agentId}` was
> explicitly *"a non-authenticated interface designed for use by collection agents"*, with
> timestamps clamped to ±10 minutes for unauthenticated submissions. At 9.1 the spec's global
> `security` covers every operation including ingest, and agent authentication has its own
> mechanism (below). **Whether an unauthenticated ingest path still exists is UNVERIFIED** —
> nothing in `SPECLM9.1` exempts it.

### Agent secrets

New at 9.1 — 4 operations, all **spec-confirmed (9.1)**, no 9.0 counterpart:

| Call | operationId | Notes |
|---|---|---|
| `POST /api/v2/agent/secrets` | `createAgentSecret` | Body `AgentSecretCreateRequest {name}`. Response `AgentSecretCreateResponse {id, name, secret, status}` — *"The returned secret value should be stored securely as it will only be displayed once."* `201` |
| `GET /api/v2/agent/secrets` | `listAgentSecrets` | Paginated. *"does not include the actual secret values"* |
| `POST /api/v2/agent/secrets/exchange` | `createAgentSession` | Body `AgentAuthenticationRequest {secret*, ttl}`. Response `AgentAuthenticationResponse {access_token*, name*, new_secret*, ttl*}` |
| `POST /api/v2/agent/secrets/{secretName}/revoke` | `revokeAgentSecret` | **Destructive and irreversible** |

`createAgentSession` TTL rules, verbatim: *"The Time-To-Live (TTL) is specified in
**milliseconds** and must be between a **minimum of 1 minute (60,000 ms)** and a **maximum of
180 days (15,552,000,000 ms)**. If not provided or zero, the system defaults to 30 minutes
(1,800,000 ms)."* Note the response returns a **`new_secret`** — the secret rotates on every
exchange, so an agent that does not persist `new_secret` will fail its next exchange.

`revokeAgentSecret`, verbatim: *"making it immediately invalid for authentication. Any agents
configured to use this secret will no longer be able to authenticate … This action cannot be
undone … This action does not invalidate any previously created token."* So revocation stops
future exchanges but leaves outstanding `access_token`s alive until their own TTL expires.

### Agent groups

New at 9.1 — 6 operations, all **spec-confirmed (9.1)**, no 9.0 counterpart:
`getAllAgentGroupConfig` (`GET /api/v2/agent/groups`, paginated), `createAgentGroupConfig`
(`POST`), `getAgentGroupConfigById`, `updateAgentGroupConfig` (`PUT`),
`patchUpdateAgentGroupConfig` (`PATCH`), `deleteAgentGroupConfig` (`DELETE`, `204`).

`AgentGroupRequest`: `name`* (`minLength: 1`), `constraints`* (**a `Query` object — the same DSL
as log search**), `agentConfig` (string), `autoUpdate` (boolean), `info`, `mpId`.
`AgentGroupResponse` adds `id`.

The reuse of `Query` as a membership predicate is the interesting part: agent-group membership
and log filtering share one grammar.

### Extracted fields

Two operations, both **spec-confirmed (9.1)**:

| Call | operationId |
|---|---|
| `GET /api/v2/fields/extractedFields` | `getExtractedFields` |
| `POST /api/v2/fields/extractedFields` | `createExtractedField` |

`ExtractedFieldsCreateRequest`: `name`* and `extractionRegex`* **required**; plus
`preContextRegex`, `postContextRegex`, `searchTerms`, `filterFieldName`, `filterOperator`,
`filterValue`, `info`, `adapterSource`, `solutionSource`, `nameKey`, and `internalName` with a
strict pattern — either a UUID or *"15+ alphanumeric characters containing at least one digit"*
(`^([0-9a-f]{8}-…|(?=.*[0-9])[a-zA-Z0-9]{15,})$`).

`ExtractedField` (the read model) documents `filterOperator`'s enum: `CONTAINS |
DOES_NOT_CONTAIN | STARTS_WITH | NOT_STARTS_WITH | MATCH | EXISTS | NOT_EXISTS | EQUAL |
NOT_EQUAL | GREATER_THAN | LESS_THAN | GREATER_OR_EQUAL | LESS_OR_EQUAL | IS | IS_NOT`. Note
`ExtractedFieldsCreateRequest.filterOperator` is typed as a bare `string` with no enum — the
enum is on the response model only.

**Versus 9.0:** 9.0 had four operations keyed by `{internalName}` — create, get, patch, delete
— and **no list**. 9.1 has list and create, and **no get-by-name, no update, no delete**. If you
need to remove or edit an extracted field at 9.1, this API does not expose it. **Where that
moved is UNVERIFIED.**

### Log forwarders

Seven operations, all **spec-confirmed (9.1)**, on `/api/v2/logs/forwarders`:

| Call | operationId |
|---|---|
| `GET /api/v2/logs/forwarders` | `getAllLogForwarders` |
| `POST /api/v2/logs/forwarders` | `createLogForwarder` (`201`) |
| `POST /api/v2/logs/forwarders/test` | `testLogForwarderConnection` |
| `GET /api/v2/logs/forwarders/{id}` | `getLogForwarderById` |
| `PUT /api/v2/logs/forwarders/{id}` | `updateLogForwarder` |
| `PATCH /api/v2/logs/forwarders/{id}` | `patchLogForwarder` |
| `DELETE /api/v2/logs/forwarders/{id}` | `deleteLogForwarder` (`204`) |

`LogForwarder`: `name`, `host`, `port`, `protocol` (`SYSLOG | RAW | RAWPLUS`),
`transportProtocol` (`TCP | UDP`), `sslEnabled`, `certificate`, `enabled`,
**`constraints` (a `Query` object)** — the same DSL again, here selecting *which* logs get
forwarded — `tags` (map), `workerCount`, `connectionRefreshInterval`, `forwardComplementaryFields`,
`id` (readOnly).

**Write path.** Creating or editing a forwarder redirects production log traffic. Call
`POST /api/v2/logs/forwarders/test` first — it takes the same `LogForwarder` body and returns
`200` with no content on success, `502` on a connection failure.

**Versus 9.0:** the path moves from `/log-forwarder` to `/logs/forwarders`, and
`POST /log-forwarder/batch` (`POST_log-forwarder-batch`) has **no 9.1 counterpart** — 8 → 7.

### Saved queries live in `/suite-api`, not here

A 9.1-only subtree on the **VCF Operations** API stores saved log-query *definitions*:
`GET|POST|PUT /suite-api/api/logs/queryconfigs` and `GET|DELETE
/suite-api/api/logs/queryconfigs/{queryConfigId}` — 5 operations, `getAllLIQueryConfigs`,
`createQueryConfig`, `updateQueryConfig`, `getLIQueryConfig`, `deleteLIQueryConfig`,
**spec-confirmed (9.1)**, absent at 9.0. `LogsQueryConfig` requires `name`, `queryText[]`
(`minItems: 1`) and `dateRange`, plus optional `queryFilters`, `description`, `id`,
`lastModifiedTime`, `modifiedBy`.

These **store** a query; they do not **run** one. Execution is `POST /api/v2/logs/search` on
Log Management, with a completely different body shape (`queryText[]` strings versus a `Query`
object). **How a stored `queryText` maps onto a Log Management `Query` is UNVERIFIED** — no
source connects the two schemas. That subtree belongs to `vcf-operations-monitoring`; it is
mentioned here only so it is not mistaken for a query API.

### What is NOT in the 23

Absent from `SPECLM9.1` entirely — do not offer these at 9.1:

| 9.0 capability | 9.0 ops | Status at 9.1 |
|---|---|---|
| Datasets (log-scoped RBAC objects) | 5 | **No counterpart in the spec** |
| Roles, users, user-groups, AD, vIDM, VIDB, auth-providers | 40 | **No counterpart.** Access comes from the exchanged JWT |
| Notification channels, email, webhooks, retention threshold | 13 | **No counterpart** |
| Limits | 3 | **No counterpart** |
| Cluster VIPs, deployment, upgrades, NTP, UI, CEIP, certificates, support bundles, salt, licenses, version | 40 | **No counterpart.** Appliance lifecycle is Fleet LCM / SDDC LCM (`vcf-lifecycle-upgrade`) |
| vSphere data-source registration and per-host log forwarding | 19 | **No counterpart** in this spec |
| `GET /events/{+path}` and `GET /aggregated-events/{+path}` | 2 | Replaced by `POST /api/v2/logs/search` with a different language |

`deltas.md` carries the arithmetic and the honest characterisation of what that drop means.

---

## Worked example — run a log query on 9.1

Find errors from a specific host in a time window, newest first, with a per-minute count
alongside. Three phases: **OpsToken → exchange → query.** Skipping or reordering the first two
is the single most common way this fails (T1).

```bash
OPS=vcf-ops.example.com
USER='admin@local'
PASS='Secret!'
```

**Step 1 — acquire an OpsToken (T1).** VCF Operations, not the log service.

```bash
OPSTOKEN=$(curl -sk -X POST "https://$OPS/suite-api/api/auth/token/acquire" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\",\"authSource\":\"LOCAL\"}" \
  | jq -r .token)          # response: {token, validity, expiresAt, roles[]}; 6-hour TTL
```

**Step 2 — exchange it for a Log Management JWT, and learn where the service is (T2, T4).**
`includeServiceDetails=true` is what gives you `address`/`port`/`basePath`.

```bash
EX=$(curl -sk -X POST \
  "https://$OPS/suite-api/api/auth/token/exchange?includeServiceDetails=true" \
  -H "Authorization: OpsToken $OPSTOKEN" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"serviceKeys":["ops-li"]}')

JWT=$(jq -r .jwtToken <<<"$EX")
LI=$(jq -r '.services[] | select(.key=="ops-li")' <<<"$EX")
LI_HOST=$(jq -r .address <<<"$LI")
LI_PORT=$(jq -r .port    <<<"$LI")
# A 400 here means the service key is wrong — "Invalid service key provided".
```

**Step 3 — search (T3).** `X-JWT-Token`, not `Authorization`. `POST /api/v2/logs/search`, not
the deprecated `POST /api/v2/search`.

```bash
curl -sk -X POST "https://$LI_HOST:$LI_PORT/api/v2/logs/search" \
  -H "X-JWT-Token: $JWT" \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{
    "query": {
      "bool": {
        "must": [
          { "match_phrase": { "text": "error" } }
        ],
        "filter": [
          { "term": { "hostname": { "value": "esx-01.example.com",
                                    "case_insensitive": true } } },
          { "range": { "logTimestamp": { "gte": "1753920000000",
                                         "lt":  "1753923600000" } } }
        ],
        "must_not": [
          { "term": { "appname": { "value": "vpxa" } } }
        ]
      }
    },
    "sort": [ { "logTimestamp": { "order": "desc" } } ],
    "size": 500,
    "trackTotalHits": true,
    "aggregations": {
      "per_minute": {
        "date_histogram": { "field": "logTimestamp", "fixed_interval": "1m" }
      }
    }
  }'
```

Reading the response:

- `events.hits[].msgContent.originalText` — the log line.
- `events.hits[].msgContent.logTimestamp` / `.ingestTimestamp` — event time vs arrival time.
- `events.hits[].msgContent.fields[]` — `{internalName, displayName, value, valueType,
  fieldCategory}`. **This is where you learn the real field names** for your next query.
- `events.total` — exact only because `trackTotalHits` was set.
- `aggregations.buckets[]` — `{key[], doc_count, values[]}` for the per-minute series; check
  `aggregations.truncated`.
- `timedOut`, `timeTakenMillis`, and `failureReason`
  (`SYSTEM | QUERY | DATA_AVAILABILITY | OTHER`) before trusting an empty result.

**Field names in this example are illustrative.** `text`, `hostname`, `appname` and
`logTimestamp` are *plausible* names carried over from the log-event model; `RAWLM9.1` provides
**no example query and names no queryable fields**. Run a `{"query":{"match_all":{}},"size":1}`
first and read `fields[].internalName` off the hit, then substitute. Treat the exact field names
above as **UNVERIFIED**.

Two constraints that will bite: `size` is capped at **2000** and `from` at **20000** — page with
`from`/`size` or use `scroll`/`scrollSize`; and the auth failure code on most of this API is
**403**, not 401, so a 403 usually means the JWT, not the permissions.

---

## Part 2 — Real-time metrics (4 operations)

New at 9.1; no 9.0 counterpart. *"The Real-time Metrics component provides Prometheus-compatible
APIs for querying real-time metrics collected from VMware vCenter environments"* [`RAWRTM9.1`].
Auth: `Authorization: Bearer <jwt>` from the VODAP exchange (T5).

| Call | operationId | Tag |
|---|---|---|
| `GET /api/v1/query` | `query` | `prometheus-expression` |
| `GET /api/v1/query_range` | `queryRange` | `prometheus-expression` |
| `GET /api/v1/metadata` | `queryMetricMetadata` | `metadata` |
| `PUT /api/v1/vcenters/{vcId}/metrics_config` | `updateVcMetricsConfig` | `vcMetricsConfig` |

All **spec-confirmed (9.1)**. The paths are deliberately Prometheus-shaped, but this is **not**
a full Prometheus API — there is no `/api/v1/series`, `/labels`, `/label/*/values`, `/targets`
or `/rules`. Four operations is the whole surface.

**`GET /api/v1/query`** — *"Executes a PromQL query and returns the result."*

| Parameter | Required | Notes |
|---|---|---|
| `query` | **yes** | The PromQL. Spec examples: `jvm_gc_collection_seconds_count{service="server"}`, `…[5m]`, `rate(jvm_gc_collection_seconds_count[5m])` |
| `sourceId` | no | *"Source Id against which we need to query data for, like VC Instance UUID, NSX Id etc."* |
| `time` | no | Unix epoch **seconds** or RFC3339. *"The current server time is used if the time parameter is unset."* |
| `timeout` | no | Duration string — `1s`, `4h` |
| `limit` | no | Max series. *"If not set, default limit is applied"* — **the default value is not stated; UNVERIFIED** |
| `externalTagsFilter` | no | Extra tag filters applied to the PromQL. Example: `{"host":"host-15", "vm"="vm-25"}` — note the spec's example mixes `:` and `=`; **its exact syntax is UNVERIFIED** |

**`GET /api/v1/query_range`** — same, minus `time`, plus **`start`, `end` and `step`, all three
required**. `start`/`end` are epoch seconds or RFC3339; `step` is a duration (`1s`, `4h`) or a
float number of seconds (`300.5`).

**`GET /api/v1/metadata`** — *"Returns metadata about metrics currently scraped from targets."*
Parameters `metric` (example `cpu.usage.HOST`), `limit`, `sourceId`. Response data is a map of
metric name → array of `{type, help, unit}` — e.g. `unit: "percentage"`. **Start here**; it is
how you find real metric names (T6).

**Response envelope** — `PrometheusResponse`, required `status` + `data`:
`status` (`success | error`), `data` (loose object — the spec deliberately types it as
`object` to sidestep an OpenAPI-generator `oneOf` limitation), plus `errorType`, `error`,
`warnings[]`, `infos[]`, and `pageInfo {nextPageToken, pageSize}` — *"Only present for
paginated APIs."* Inside `data`: `resultType` (`matrix | vector | scalar | string`) and
`result`. `matrix` gives `[{metric{...}, values: [[ts, "val"], …]}]`; `vector` gives
`[{metric{...}, value: [ts, "val"]}]`. Timestamps are floats, values are **strings** — standard
Prometheus.

**`PUT /api/v1/vcenters/{vcId}/metrics_config`** — see T6. `vcId` is a UUID.
Body `{standard: bool, verbose: bool, esxTopHostMoids: [{moid: "host-1", operation: "ADD"|"REMOVE"}]}`.
**Write path** — changes collection scope for a whole vCenter.

> **A `policy` parameter is defined in the spec but used by nothing.**
> `realtime-metrics-openapi-params.yaml` defines `policyQueryParam` (required, examples
> `TROUBLESHOOTING` and `MONITORING`, *"Name of the policy for which the aggregated or rolled-up
> data to be queried"*) — and **none of the four operations references it.** Whether policy-based
> roll-up querying is reachable is **UNVERIFIED**; do not send `policy` on the strength of the
> parameter file alone.

---

## Part 3 — VCF Operations for Networks (636 operations)

Base `/api/ni`, spec version `9.1.0.0`. **The 9.0 file documents this API in full**
(`references/9.0/logs-and-networks.md`, Part 2) — entities, search, metrics, the 304 data-source
operations, applications, micro-segmentation, settings — and every word of it holds at 9.1
except what is listed below. Read it there rather than duplicating; this section covers only
what differs.

### What changed from 9.0

632 → 636. **5 added, 1 removed, 22 newly deprecated, 0 `operationId` changes on any shared
path** (verified by diffing `SPECNI9.0` against `SPECNI9.1` on `(method, path)`). Tag counts are
identical family by family except `Settings` 98 → 100 and a new `Inventory Tree` tag with 2.

### Authentication

Four operations, unchanged: `POST /auth/token` (`create`), `DELETE /auth/token` (`delete`),
`POST /auth/token/vidm` (`createVidmUserToken`), `GET /auth/vidm/client-id`
(`getVidmOauthClienId`). All **spec-confirmed (9.1)**, all at 9.0.

**The change is in the security schemes, not the operations** — see N1. `OpsTokenAuth`
(HTTP bearer, *"VCF Ops JWT Token - Bearer {token}"*) is added, and 9.1 gains a top-level
`security` block listing both schemes where 9.0 had none.

### Entities, search, metrics

Identical to 9.0, operation for operation. `GET /entities/<kind>` list operations still default
to `size: 10` with a `cursor`; `GET /metrics/v2` (`getMetricsV2`) still requires all five of
`entity_id`, `metric`, `interval`, `start`, `end` and still caps at **300 points per response**;
`POST /search/ql` (`search`) still takes `{query, size, cursor, time_range}` with the spec
example `"VM where CPU Cores > 2"`. `GET /metrics` and `POST /metrics/fetch` remain deprecated
(they were already deprecated at 9.0 — not a 9.1 change).

### Inventory trees — new at 9.1

| Call | operationId | Notes |
|---|---|---|
| `GET /inventory-trees` | `getInventoryTrees` | *"List all available inventory tree views."* Response `InventoryTreeList {trees[]}` with `tree_type` (example **`HOSTS_CLUSTER`**), `name`, `children[]` |
| `GET /inventory-trees/{tree-type}/{node-id}/children` | `getChildren` | *"Get children of node"* |

Both **spec-confirmed (9.1)**, both **absent at 9.0**, tag `Inventory Tree` —
*"Inventory Tree view for VCenter entities APIs"*. This is a hierarchical browse surface over
vCenter entities, complementary to flat `/entities` lists. The full set of `tree_type` values
is **UNVERIFIED** — only `HOSTS_CLUSTER` appears as an example.

### Licensing v2 and FIPS — new at 9.1

| Call | operationId | Notes |
|---|---|---|
| `GET /settings/licensing/v2` | `getLicensesV2` | *"Get information for current licenses."* Response `LicensingResponseV2` → `VRNILicenseV2`. **Replaces the newly-deprecated `GET /settings/licensing/`** |
| `GET /settings/fips/modules` | `getFipsModulesDetails` | *"Get details of fips modules"* |

Both **spec-confirmed (9.1)**, both absent at 9.0.

### Data sources — 304 operations, 21 newly deprecated

The family list and per-family counts are **identical to 9.0** (see the 9.0 file). What changed
is deprecation:

- `aws-accounts` (7), `azure-subscriptions` (7), `nsxalb` (7) — **all 21 operations now
  `deprecated: true`**, and were not at 9.0. Every verb: list, get, create, update, delete,
  enable, disable. **No replacement path is offered by the spec.**
- Everything else — `vcenters`, `nsxt-managers`, `nsxv-managers`, the switch and firewall
  families, `kubernetes-clusters`, `openshift-clusters`, `pks`, `velocloud`, `hcx-connectors`,
  `loginsight`, `servicenow-instances` and the rest — is unchanged and undeprecated.

Full enumeration with operationIds in `deltas.md`.

### Everything else

Unchanged from 9.0, including the 31 operations that were **already** deprecated at 9.0
(pinboards 12, user-defined events 7, IP-tags v1 4, licensing activate/deactivate/validate 3,
migration 3, metrics v1 2) — all still deprecated, none removed. The single **removal** at 9.1
is `GET /migration/{groupType}`, replaced by `GET /migration/wave/{groupType}` (same
`operationId`, `getMigrationWave`) — which is itself still deprecated, so the rename does not
un-deprecate anything.

---

## What is not here

- **`/suite-api`** — resources, stats, alerts, reports, custom groups, policies, `logs/queryconfigs`,
  fleet management. That is `vcf-operations-monitoring` (and `vcf-foundation` for IAM).
- **Token acquisition beyond the three flows above** — auth sources, VCF SSO, OAuth 2.0 API
  tokens, roles. `vcf-foundation`.
- **Fleet LCM / SDDC LCM**, appliance upgrade, depots and bundles — `vcf-lifecycle-upgrade`.
- **The 9.0 log product** — `references/9.0/logs-and-networks.md`.
- **Acting on NSX rules** recommended by micro-segmentation — `nsx-security-policy`.

## Still unverified

- **Log Management's real address and port** per deployment (T4) — 8787 is a generated
  placeholder and the exchange example shows 8000.
- **The literal VODAP service key** (T5) — the docs give the `type`, not the key.
- **Where the Networks `OpsTokenAuth` bearer JWT is obtained** (N1) — `ops-ni` is inferred from
  spec examples.
- **Queryable field names in the Log Management DSL**, including the timestamp field — no
  example query exists in the spec. Discover from `fields[].internalName`.
- **The default time window** for `POST /api/v2/logs/search` — none is stated.
- **Whether an unauthenticated ingest path survives** at 9.1.
- **Where extracted-field update and delete went** — 9.1 exposes only list and create.
- **How `LogsQueryConfig.queryText[]` maps onto a Log Management `Query`.**
- **The default `limit`** on real-time metric queries, and the syntax of `externalTagsFilter`.
- **Whether the unused `policy` parameter is reachable.**
- **Where the 2-second/20-second real-time sampling interval is configured** — not in these four
  operations.
- **The full set of Networks `tree_type` values.**
- **Whether any replacement exists for the AWS / Azure / NSX-ALB data-source families.**
- **Role, privilege and capability names; retention; rate limits** on all three products.
