# VCF 9.0 — Operations for Logs and Operations for Networks Reference

**Scope:** VMware Cloud Foundation 9.0.x, two products: **VCF Operations for Logs**
(base `/api/v2`) and **VCF Operations for Networks** (base `/api/ni`). Everything here is
`[9.0]` unless explicitly tagged otherwise. The `/suite-api` monitoring API is **out of
scope** — see `vcf-operations-monitoring`. Real-time metrics does not exist at 9.0.

**Sources.**
- `SPECLOG9.0` = `research/spec-inventory/9.0__vcf-operations-for-logs.ops.json` —
  **136 operations**, base `/api/v2`, spec `version` field `v2`, title
  "VCF Operations for Logs", from git tag `9.0.0.0` of `github.com/vmware/vcf-api-specs`.
- `RAWLOG9.0` = `specifications/vcf-operations/vcf-operations-for-logs-openapi.json` at the
  same tag — OpenAPI 3.0.1, source of every field name, enum and query parameter in the Logs
  half below. `servers: [{ "url": "/api/v2" }]`; no top-level `security`; one scheme,
  `Bearer` (`type: http`, `scheme: Bearer`, header `Authorization`).
- `SPECNI9.0` = `research/spec-inventory/9.0__vcf-operations-for-networks.ops.json` —
  **632 operations**, base `/api/ni`, spec version `9.0.0.0`.
- `RAWNI9.0` = `specifications/vcf-operations/vcf-operations-for-networks-openapi.yaml` at the
  same tag — OpenAPI 3.0.1, `servers: [{ "url": "/api/ni" }]`, **no top-level `security`
  block**, one scheme `ApiKeyAuth` (`type: apiKey`, header `Authorization`, description
  "API Key - NetworkInsight {token}").
- `DOPS` = `research/vcf-operations.md`.
- `DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md`.

Every path below was checked against `SPECLOG9.0` or `SPECNI9.0` and is marked
**spec-confirmed (9.0)** with its `operationId`. Where the 9.0 spec has no `operationId` for
an operation that is stated too.

> **The dossier could not confirm these paths from the doc portal.** `DOPS` §Gaps items 4 and
> 5 record that the developer-portal operation indexes for both products returned "Object Not
> Found", and item 5 says explicitly *"The commonly-assumed legacy `/api/ni/...` prefix was
> not confirmed anywhere in this research — do not assume it."* **The OpenAPI specs are the
> evidence for this file, and they resolve that gap**: `/api/ni` is the declared server URL in
> both 9.0 and 9.1. Where the specs are silent, the fact is marked UNVERIFIED rather than
> filled in from the portal or from Log Insight / vRNI habit.

> **Documentation-derived, not live-validated.** Captured 2026-07-31. Nothing here has been
> executed against a running appliance. Reads are cheap; the write paths — data-source
> creation and deletion, cluster VIP changes, upgrade start, log-forwarder changes, role and
> user mutation, license activation — are not, and are flagged where they appear.

---

## Contents

- [Prerequisites](#prerequisites)
  - L1 — You are on 9.0, and the log product is "VCF Operations for Logs"
  - L2 — Logs: a session ID, sent as `Authorization: Bearer`
  - L3 — Port 9543, not 443
  - L4 — Query constraints go in the URL path, not a body
  - L5 — Default limits will silently truncate your answer
  - N1 — Networks: a NetworkInsight token
  - N2 — The header prefix is `NetworkInsight`, not `Bearer`
  - N3 — 100 valid tokens per user, then 401
  - N4 — The data source you want must be registered and collecting
  - N5 — Entity IDs, not names
  - P0 — Things this file could not verify
- [Part 1 — VCF Operations for Logs (136 operations)](#part-1--vcf-operations-for-logs-136-operations)
  - [Sessions and identity](#sessions-and-identity)
  - [Querying events](#querying-events)
  - [Aggregated (grouped) events](#aggregated-grouped-events)
  - [Ingesting events](#ingesting-events)
  - [Extracted fields](#extracted-fields)
  - [Datasets](#datasets)
  - [Log forwarding](#log-forwarding)
  - [Limits and notifications](#limits-and-notifications)
  - [Users, groups and roles](#users-groups-and-roles)
  - [Auth providers — AD, vIDM, VIDB](#auth-providers--ad-vidm-vidb)
  - [vSphere integration (19 operations, 7 deprecated)](#vsphere-integration-19-operations-7-deprecated)
  - [Appliance, cluster, upgrade and supporting surfaces](#appliance-cluster-upgrade-and-supporting-surfaces)
  - [Worked example — a log query on 9.0](#worked-example--a-log-query-on-90)
- [Part 2 — VCF Operations for Networks (632 operations)](#part-2--vcf-operations-for-networks-632-operations)
  - [Authentication](#authentication)
  - [Entities — the inventory read surface](#entities--the-inventory-read-surface)
  - [Search](#search)
  - [Metrics](#metrics)
  - [Data sources (304 operations)](#data-sources-304-operations)
  - [Applications and tiers](#applications-and-tiers)
  - [Micro-segmentation and path](#micro-segmentation-and-path)
  - [Alerts, intents and dashboards](#alerts-intents-and-dashboards)
  - [Settings, config and infrastructure](#settings-config-and-infrastructure)
  - [Deprecated at 9.0 (31 operations)](#deprecated-at-90-31-operations)
- [What is not here](#what-is-not-here)
- [Still unverified](#still-unverified)

---

## Prerequisites

Nothing below should be attempted until these hold. Each states what must be true, **how to
verify it**, and whether 9.1 differs — which for the Logs half is the whole point, because
**the log product is replaced at 9.1** and none of L1–L5 survives.

### L1 — You are on 9.0, and the log product is "VCF Operations for Logs" `[9.0]`

**Must be true:** the deployment is 9.0.x. At 9.1 this API does not exist; the spec is gone
from the repo entirely (`DELTA`: *"`vcf-operations-for-logs` — spec removed in 9.1"*) and is
replaced by a different product with a different spec, base, port and auth.

**How to verify:** `GET /api/v2/version` — **spec-confirmed (9.0)**, `GET_version`. Or from
the Operations side, `GET /suite-api/api/versions/current` (`getCurrentVersionOfServer`,
present in both `/suite-api` inventories).

**9.1 difference:** total. See `references/9.1/logs-and-networks.md` and `deltas.md`. Do not
port a 9.0 log script to 9.1 by changing the hostname.

### L2 — Logs: a session ID, sent as `Authorization: Bearer` `[9.0]`

**Must be true:** every authenticated call carries a session ID obtained from
`POST /api/v2/sessions` — **spec-confirmed (9.0)**, `POST_sessions`.

Request (`sessions.post.request`), **all three required** [`RAWLOG9.0`]:

```json
{ "username": "admin", "password": "Secret!", "provider": "Local" }
```

`provider` enum: `Local | ActiveDirectory | vIDM`.

Response (`sessions.post.response`), all three required: `userId` (UUID), `sessionId`
("An opaque session ID for use in the Authorization header"), `ttl` ("Number of seconds this
session is valid for"). The documented example returns `"ttl": 1800` — **30 minutes**
[`RAWLOG9.0`]. That is a documented *example value*, not a spec-declared constant; read `ttl`
off your own response rather than hard-coding 1800.

Header on subsequent calls [`RAWLOG9.0` info description]:

```
Authorization: Bearer <sessionId>
```

The security scheme is named `Bearer` and is `type: http`, `scheme: Bearer` — so the prefix is
attested by the scheme itself, not only by prose.

**How to verify:** `GET /api/v2/sessions/current` — **spec-confirmed (9.0)**,
`GET_sessions-current`. Returns `userId` and TTL. A `401` means bad credentials; note this API
also uses **`440`** as a session-expiry status on many operations [`RAWLOG9.0`].

**9.1 difference:** there is no `/sessions` endpoint at 9.1 and no session ID. 9.1 uses
`X-JWT-Token` from a token exchange performed against `/suite-api`. General auth is
`vcf-foundation`'s subject; the three token flows are summarized in `deltas.md`.

### L3 — Port 9543, not 443 `[9.0]`

**Must be true:** requests go to `https://<logs-fqdn>:9543/api/v2/...`.
`RAWLOG9.0`'s info description states: *"Use HTTPS on port `9543` with JSON payloads for all
API requests."* It also warns that a self-signed certificate on 9543 will block browser-based
calls until accepted, and suggests opening
`https://<your_host>:9543/api/v2/sessions/current` in a tab first.

**How to verify:** an unauthenticated `GET https://<host>:9543/api/v2/sessions/current`
should return 401 rather than a connection error.

**9.1 difference:** yes — see L3' in the 9.1 file. Do not carry 9543 forward.

### L4 — Query constraints go in the URL path, not a body `[9.0]`

**Must be true:** you understand that the 9.0 query API is `GET` with constraints encoded as
path segments — the Log Insight shape. From `RAWLOG9.0`'s info description, verbatim:

> Pass constraints within the URL, similar to `GET /api/v2/events/constraint1/constraint2/`

and the worked example given there:

```
GET /api/v2/events/text/CONTAINS%20Test/timestamp/LAST%20360000
```

The spec path itself is `/events/{+path}` where `+path` is *"Specifies constraints on the
events to retrieve"* — a single greedy path parameter.

**How to verify:** the query returns `{"complete": …, "duration": …, "events": [...]}`.

**9.1 difference:** total, and this is the sharpest single behavioral break in the pair.
9.1 replaces this with `POST /api/v2/logs/search` taking an Elasticsearch-style JSON query
DSL in the body. A path-constraint URL will not work at 9.1.

> `DOPS` §Gaps item 4 warned: *"Do not assume the legacy Log Insight `/api/v2/events/{constraints}`
> shape carries over without checking the live appliance."* The specs settle it: the shape is
> real at **9.0** and is **gone at 9.1**.

### L5 — Default limits will silently truncate your answer `[9.0]`

**Must be true:** you have set `limit`, `timeout` and a `timestamp` constraint deliberately.
From `RAWLOG9.0`'s "Defaults" section and the `/events/{+path}` and
`/aggregated-events/{+path}` parameter schemas:

| Default | Value | Raise to | Effect if unset |
|---|---|---|---|
| `limit` | `100` | 20,000 events / 2,000 bins | You get 100 rows and no error |
| `timeout` | `30000` ms | higher | Partial results returned; check the `complete` flag |
| time range | **events from one minute ago or newer** | any `timestamp` constraint | An empty result on a quiet system |

The one-minute default window is the most common cause of "the API returned nothing." The
`complete` flag on the response is what distinguishes a truncated answer from a real one —
note the two operations describe it in opposite senses in the spec (`/events`: *"partial
result is returned and the `complete` flag is set to `true`"*; `/aggregated-events`:
*"a partially result is returned and the `complete` flag is set to `false`"*). That
contradiction is in the source document; **which is correct is UNVERIFIED** — test before
relying on the flag's polarity.

**9.1 difference:** different mechanism entirely — `size` (max 2000), `from` (max 20000),
`trackTotalHits` and `timedOut` on the response.

### N1 — Networks: a NetworkInsight token `[9.0+9.1]`

**Must be true:** every Networks call carries a token from `POST /auth/token` —
**spec-confirmed (9.0)**, `create`; also at 9.1.

Request (`UserCredential`) [`RAWNI9.0`]: `username` (example `admin@vrni.com`), `password`,
`domain` (`Domain`: `domain_type` enum `LDAP | LOCAL`, uppercase; `value` — *"not required for
LOCAL domain"*). No property is marked required in the schema.

Response (`Token`): `token` (example `1rT7tm4riiACSfxrO2BvkA==`), `expiry` — *"expiry epoch
time in secs."* (`int64`). **Read `expiry` off the response**; no fixed TTL is declared.

**How to verify:** `GET /api/ni/info/version` — **spec-confirmed (9.0)**, `getVersion`.

**9.1 difference:** the endpoint is unchanged, but 9.1 adds a **second** accepted scheme
(HTTP bearer, VCF Ops JWT). See N2.

### N2 — The header prefix is `NetworkInsight`, not `Bearer` `[9.0]`

**Must be true:**

```
Authorization: NetworkInsight {token}
```

Attested twice: the `ApiKeyAuth` security scheme description in `RAWNI9.0` reads *"API Key -
NetworkInsight {token}"*, and the `POST /auth/token` description spells the header out. `DOPS`
[S17] agrees.

**How to verify:** any authenticated GET; an invalid or expired token returns *"401-Unauthorized"*
[`RAWNI9.0`].

**9.1 difference — and this one only works in one direction.** `RAWNI9.0` declares **one**
security scheme and **no top-level `security` block**. The 9.1 document declares **two**
(`ApiKeyAuth` plus `OpsTokenAuth`, `type: http`, `scheme: bearer`, *"VCF Ops JWT Token - Bearer
{token}"*) and a top-level `security: [ApiKeyAuth, OpsTokenAuth]`. Code that sends a VCF Ops
bearer JWT to a **9.0** Networks appliance has no spec support and should be expected to fail.

> `DOPS` §"Other components' auth" tags both schemes `[9.0+9.1]`, but says why: *"the portal
> does not version-split these two schemes."* The specs do split them. **Trust the specs:
> `OpsTokenAuth` is 9.1-only.**

### N3 — 100 valid tokens per user, then 401 `[9.0+9.1]`

**Must be true:** you are not leaking tokens. From the `POST /auth/token` description
[`RAWNI9.0`], verbatim: *"There is limit of 100 valid tokens per user and further requests will
return 401-Unauthorized. So, users are advised to delete the tokens after use."*

**How to verify / how to fix:** `DELETE /auth/token` — **spec-confirmed (9.0)**, `delete`;
deletes the token in the `Authorization` header, returns `204`. Deleting an expired or invalid
token returns 401. Expired tokens are also *"cleaned periodically by the system"*.

This is the failure mode that looks like a credential problem and is not: a CI job that
acquires a token per run and never deletes it will start 401-ing on the 101st run.

**9.1 difference:** none — same text, same operations.

### N4 — The data source you want must be registered and collecting `[9.0+9.1]`

**Must be true:** the vCenter / NSX / switch / firewall you are querying entities for has been
added as a data source. Networks returns nothing for infrastructure it does not collect from.

**How to verify:** list the relevant family, e.g. `GET /data-sources/vcenters`
(**spec-confirmed (9.0)**, 8 operations in that family) or `GET /data-sources/nsxt-managers`
(7 operations). `GET /data-sources/health` (`getDatasourceHealth`) is **spec-confirmed (9.0)**
and is the fastest
single check across sources.

**9.1 difference:** none for the families above. But three families are **newly deprecated at
9.1** — AWS, Azure and NSX-ALB. See `deltas.md`.

### N5 — Entity IDs, not names `[9.0+9.1]`

**Must be true:** you have `entity_id` values. Networks entity IDs look like
`18230:1:1158969162` (from the `GET /entities/vms` response example in `RAWNI9.0`) — not
UUIDs, not names.

**How to verify / how to get them:** `POST /search` (`searchEntities`) or `POST /search/ql`
(`search`) return lists of entity IDs; `POST /entities/names` (`getNames`) and
`GET /entities/names/{id}` (`getName`) go from ID to name. `POST /entities/fetch` bulk-fetches
details — *"Max batch size is 1000"* [`RAWNI9.0`]. All **spec-confirmed (9.0)**.

Note `POST /entities/fetch` has **no `operationId`** in either spec — cite it by method and
path.

**9.1 difference:** none.

### P0 — Things this file could not verify

- **The Networks token TTL as a fixed number.** The response carries `expiry`; no constant is
  declared. `DOPS` §"Other components' auth" also records the acquisition endpoint, payload and
  TTL as UNVERIFIED from the portal — the spec supplies endpoint and payload, but not a TTL.
- **Role and privilege names** on either product, and which role any operation requires.
- **The polarity of the Logs `complete` flag** (see L5).
- **Retention** on either product, and what a query older than retention returns.
- **Rate limits** on any operation here.

---

## Part 1 — VCF Operations for Logs (136 operations)

The 9.0 log product is a **standalone appliance API**: it owns its own identity system, its own
cluster lifecycle, its own certificates, its own upgrade path and its own vCenter integration,
in addition to log ingest, query and forwarding. That framing matters, because it is the whole
explanation for the 136 → 23 operation drop at 9.1. See `deltas.md`.

By tag, from `SPECLOG9.0` (counts sum to 136):

| Group | Tags | Ops |
|---|---|---|
| Log data plane | `events` 3, `aggregated-events` 1, `fields` 4, `datasets` 5, `log-forwarder` 8, `limits` 3, `notification` 13 | **37** |
| Appliance and cluster lifecycle | `appliance` 2, `cluster` 6, `deployment` 5, `upgrades` 5, `time` 4, `ui` 4, `ceip` 2, `certificate` 2, `certificates` 3, `trusted-certificates` 2, `licenses` 1, `version` 1, `salt` 3 | **40** |
| Identity and access | `sessions` 2, `users` 8, `user-groups` 6, `roles` 13, `ad` 3, `vidm` 4, `vidb` 3, `auth-providers` 1 | **40** |
| vSphere data-source integration | `vsphere` 19 | **19** |

### Sessions and identity

| Call | operationId | Notes |
|---|---|---|
| `POST /sessions` | `POST_sessions` | See L2. `username`*, `password`*, `provider`* |
| `GET /sessions/current` | `GET_sessions-current` | Returns `userId`; 401 / 440 on expiry |

All **spec-confirmed (9.0)**. There is no session-delete operation in the inventory —
**UNVERIFIED** whether one exists undocumented.

### Querying events

`GET /events/{+path}` — **spec-confirmed (9.0)**, `GET_events-+path`.

Path parameter `+path` (required): *"Specifies constraints on the events to retrieve."*
Constraints are `field/OPERATOR VALUE` pairs, URL-encoded, chained:

```
/events/text/CONTAINS%20Test/timestamp/LAST%20360000
```

Query parameters [`RAWLOG9.0`]:

| Name | Type | Default | Meaning |
|---|---|---|---|
| `limit` | integer | `100` | Max events. Raise to 20,000 |
| `timeout` | integer | `30000` | Milliseconds; partial results on expiry |
| `view` | enum | `DEFAULT` | `DEFAULT \| SIMPLE` |
| `content-pack-fields` | string | — | Repeatable; adds content-pack fields to the response |
| `order-by-direction` | enum | `DESC` | `ASC \| DESC` |

Response shape, from the documented example: `complete` (boolean), `duration` (ms), `events[]`
where each event has `text`, `timestamp` (ms since epoch) and `fields[]` of
`{name, content}`.

Responses declared: `200`, `401`, `440`.

> The full grammar of constraint operators beyond `CONTAINS` and `LAST` is **UNVERIFIED** —
> `RAWLOG9.0` documents the shape and two examples and refers to a prose "specifying constraints"
> section that is not in the spec.

### Aggregated (grouped) events

`GET /aggregated-events/{+path}` — **spec-confirmed (9.0)**,
`GET_aggregated-events-+path`. *"Queries VCF Operations for Logs for groups of events."*
This is the numeric/chart half of Interactive Analytics.

Query parameters beyond those above [`RAWLOG9.0`]:

| Name | Default | Constraint | Meaning |
|---|---|---|---|
| `bin-width` | `5000` | 1 … 2147483647 | Time-span of bins, milliseconds |
| `aggregation-function` | `COUNT` | enum | `COUNT \| SAMPLE \| UCOUNT \| MIN \| MAX \| SUM \| STDDEV \| VARIANCE` |
| `aggregation-field` | — | — | **Required for every function except `COUNT` and `SAMPLE`**, and *not supported* for those two |
| `group-by-field` | — | **required: true** | Repeatable. `bin-width=12345` for fixed bins, `bins=10,100,500` for explicit bins |
| `order-by-function` | — | enum | Same set minus `SAMPLE` |
| `order-by-field` | — | — | Field to sort by |
| `order-by-direction` | `DESC` | enum | `ASC \| DESC` |
| `limit` | `100` | 1 … 2147483647 | Bins, capped at 2,000 per the Defaults section |

The `aggregation-field` rule is a real 400 waiting to happen: sending it with `COUNT` is
documented as unsupported, and omitting it with `SUM` is documented as invalid.

`RAWLOG9.0`'s prose also lists `AVG` among the common aggregation functions, but **`AVG` is not
in the parameter's enum**. Treat the enum as authoritative; the prose mention is
**UNVERIFIED**.

### Ingesting events

Two operations, both **spec-confirmed (9.0)**:

| Call | operationId | Auth | Body |
|---|---|---|---|
| `POST /events` | `POST_events` | authenticated | A **JSON array** of objects with `timestamp` (int), `text` (string), plus arbitrary additional properties as fields |
| `POST /events/ingest/{agentId}` | `POST_events-ingest-agentId` | **non-authenticated interface designed for use by collection agents** | `{ "events": [ { "text": …, "timestamp": …, "fields": [ {name, content} ] } ] }`, `events` required |

Limits, from the spec descriptions:

- `POST /events`: max **4 MB** per submission, **16 KB** per `text` field. *"If a single error
  is detected in any of the logs, the entire request will be rejected."* An empty `timestamp`
  is filled with the current time.
- `POST /events/ingest/{agentId}`: max **4 MB**, **16 KB** per `text`. The info description
  says *"Submit 1-500 events together in a single batch."* `agentId` is *"a unique identifier
  for the event source … can be safely set to `0`"* if no stable identifier exists.
- **Unauthenticated submissions have their timestamps clamped** to within 10 minutes of server
  time (`config.api-server.max-tolerated-client-time-drift=600000`). Authenticated submissions
  have their `timestamp` trusted. This is why a backfill via the unauthenticated agent
  endpoint silently lands at "now".

Both paths survive verbatim at 9.1 — see `deltas.md`.

### Extracted fields

Four operations, all **spec-confirmed (9.0)**, keyed by `{internalName}`:

| Call | operationId |
|---|---|
| `POST /fields/extractedFields` | `POST_fields-extractedField` |
| `GET /fields/extractedFields/{internalName}` | `GET_fields-extractedField` |
| `PATCH /fields/extractedFields/{internalName}` | `PATCH_fields-extractedField` |
| `DELETE /fields/extractedFields/{internalName}` | `DELETE_fields-extractedField` |

Note there is **no list-all operation at 9.0** — you cannot enumerate extracted fields through
this API without already knowing each `internalName`. 9.1 inverts this exactly: it adds
`GET /api/v2/fields/extractedFields` (list) and drops get-by-name, patch and delete.

### Datasets

Five operations, all **spec-confirmed (9.0)**: `GET /datasets` (`GET_datasets`, *"Gets a list
of all data sets"*), `POST /datasets` (`POST_datasets`), `GET /datasets/{datasetId}`,
`PATCH /datasets/{datasetId}`, `DELETE /datasets/{datasetId}`.

Datasets are the log-side access-control primitive: they bind to roles through
`GET|PUT|PATCH /roles/{roleId}/datasets` (3 operations, all **spec-confirmed (9.0)**).

**There is no dataset operation in the 9.1 Log Management spec.** Where dataset-scoped access
control went at 9.1 is **UNVERIFIED** — see `deltas.md`.

### Log forwarding

Eight operations, all **spec-confirmed (9.0)**, on `/log-forwarder`:

| Call | operationId |
|---|---|
| `GET /log-forwarder` | `GET_log-forwarder` |
| `POST /log-forwarder` | `POST_log-forwarder` |
| `POST /log-forwarder/batch` | `POST_log-forwarder-batch` |
| `POST /log-forwarder/testconnection` | `POST_log-forwarder-testconnection` |
| `GET /log-forwarder/{id}` | `GET_log-forwarder-id` |
| `PUT /log-forwarder/{id}` | `PUT_log-forwarder-id` |
| `PATCH /log-forwarder/{id}` | `PATCH_log-forwarder-id` |
| `DELETE /log-forwarder/{id}` | `DELETE_log-forwarder-id` |

**Write path.** Changing a forwarder redirects production log traffic. Use
`POST /log-forwarder/testconnection` first.

At 9.1 the family moves to `/api/v2/logs/forwarders` and loses `/batch` — 8 → 7.

### Limits and notifications

- **Limits** — 3 operations: `GET /limits` (`GET_limits`, *"Retrieves the list of all
  limits"*), `GET /limits/{name}` (`GET_limits_by_name`),
  `PATCH /limits/{name}` (`PATCH_limits_by_name`). All **spec-confirmed (9.0)**.
- **Notifications** — 13 operations, all **spec-confirmed (9.0)**: notification channels
  (`GET|PUT /notification/channels` — *"the list includes SMTP server configuration used for
  sending alert emails"*), email (`GET|PUT /notification/email`), retention threshold
  (`GET|PUT /notification/config/retention-threshold`), and a webhook family
  (`GET|POST|PUT /notification/webhook`, `GET|PUT|DELETE /notification/webhook/{webhookId}`,
  `GET /notification/webhook/{webhookId}/alerts`).

**Neither family appears in the 9.1 Log Management spec.** 21 of the 37 log-plane operations at
9.0 have no successor in the 23-operation 9.1 spec; datasets, limits and notifications are
where that 21 comes from. See `deltas.md` for the honest accounting.

### Users, groups and roles

40 operations across `sessions` (2), `users` (8), `user-groups` (6), `roles` (13), `ad` (3),
`vidm` (4), `vidb` (3), `auth-providers` (1). All **spec-confirmed (9.0)**. Representative:

| Call | operationId |
|---|---|
| `GET /users`, `POST /users` | `GET_users`, `POST_users` |
| `GET|PATCH|DELETE /users/{userId}` | `GET_users-userId`, `PATCH_users-userId`, `DELETE_users-userId` |
| `PATCH /users/{userId}/password` | `PATCH_users-userId-password` |
| `GET|PATCH /users/self/settings` | `GET_users-self-settings`, `PATCH_users-self-settings` |
| `GET /roles`, `POST /roles` | `GET_roles`, `POST_roles` |
| `GET|PATCH|DELETE /roles/{roleId}` | `GET_roles-roleId`, … |
| `GET|PUT|PATCH /roles/{roleId}/capabilities` | `GET_roles-roleId-capabilities`, … |
| `GET|PUT|PATCH /roles/{roleId}/datasets` | `GET_roles-roleId-datasets`, … |
| `GET|PATCH /roles/{roleId}/users` | `GET_roles-roleId-users`, … |
| `GET /user-groups`, `POST /user-groups`, `GET /user-groups/{provider}` | `GET_user-groups`, … |
| `GET|PATCH|DELETE /user-groups/{provider}/{domain}/{name}` | `GET_user-groups-provider-domain-name`, … |
| `GET /auth-providers` | `GET_auth-providers` |

**This entire tree is absent from the 9.1 Log Management spec.** At 9.1 the log service has no
identity system of its own — access is carried in the exchanged JWT from `/suite-api`. That is
the single largest component of the operation-count drop.

The specific role names and capability strings are **UNVERIFIED**; enumerate with `GET /roles`
and `GET /roles/{roleId}/capabilities` per deployment.

### Auth providers — AD, vIDM, VIDB

| Call | operationId | Purpose |
|---|---|---|
| `GET /ad`, `POST /ad`, `POST /ad/test` | `GET_ad`, `POST_ad`, `POST_ad-test` | Active Directory |
| `GET /vidm`, `POST /vidm`, `GET /vidm/status`, `POST /vidm/test` | `GET_vidm`, … | VMware Identity Manager |
| `GET /vidb`, `POST /vidb`, `POST /vidb/test` | `GET_vidb`, … | VCF Identity Broker |

All **spec-confirmed (9.0)**. The `POST .../test` variants validate configuration without
committing it — use them before the `POST` that writes.

### vSphere integration (19 operations, 7 deprecated)

The log product registers vCenters directly and can toggle ESXi host log forwarding per host.

Current (non-deprecated), all **spec-confirmed (9.0)** — keyed by **`{UUID}`**:

| Call | operationId |
|---|---|
| `GET /vsphere`, `POST /vsphere`, `DELETE /vsphere` | `GET_vsphere`, `POST_vsphere`, `DELETE_vsphere` |
| `POST /vsphere/testconnection` | `POST_vsphere-testconnection` |
| `GET|PUT|DELETE /vsphere/{UUID}` | `GET_vsphere-UUID`, `PUT_vsphere-UUID`, `DELETE_vsphere-UUID` |
| `GET|PUT /vsphere/{UUID}/hosts` | `GET_vsphere-UUID-hosts`, `PUT_vsphere-UUID-hosts` |
| `PATCH /vsphere/{UUID}/hosts/batch` | `PATCH_vsphere-UUID-hosts-batch` |
| `GET|PUT /vsphere/{UUID}/hosts/{esxiHost}` | `GET_vsphere-UUID-hosts-esxiHost`, `PUT_vsphere-UUID-hosts-esxiHost` |

**Deprecated at 9.0** — the same seven operations keyed by **`{vcHostname}`** instead of
`{UUID}`: `GET|PUT|DELETE /vsphere/{vcHostname}`, `GET|PUT /vsphere/{vcHostname}/hosts`,
`GET|PUT /vsphere/{vcHostname}/hosts/{esxiHost}`. The replacement is the identically-shaped
`{UUID}` form above. Use UUID keys.

### Appliance, cluster, upgrade and supporting surfaces

All **spec-confirmed (9.0)**. These are appliance-management operations, and they are the
clearest evidence that 9.0's log product is a standalone appliance:

| Area | Ops | Paths |
|---|---|---|
| Cluster VIPs | 6 | `GET|POST /cluster/vips`, `GET|PUT|DELETE /cluster/vips/{uuid}`, `GET /cluster/vips/usage/{uuid}` |
| Deployment | 5 | `POST /deployment/new`, `/deployment/join`, `/deployment/approve`, `/deployment/waitUntilStarted`, `GET /deployment/token` (**no `operationId` in the spec**) |
| Upgrades | 5 | `GET|POST /upgrades`, `GET /upgrades/local`, `GET /upgrades/{version}`, `PUT /upgrades/{version}/eula` |
| Time / NTP | 4 | `GET /time`, `GET|PUT /time/config`, `POST /time/test` |
| UI prefs | 4 | `GET|PUT /ui/browser-session`, `GET|PUT /ui/language` |
| Certificates | 5 | `GET|POST /certificate`; `GET /certificates` (**deprecated**), `GET|DELETE /certificates/{thumbprint}` |
| Trusted certs | 2 | `GET|DELETE /trusted-certificates/{thumbprint}` |
| Support bundles | 2 | `POST /appliance/vm-support-bundles`, `GET /appliance/vm-support-bundles/manifests` |
| CEIP | 2 | `GET|PUT /ceip` |
| Salt minion | 3 | `GET|POST|DELETE /salt` — *"only aware of these specific fields"*: `master`, `master_type`, `retry_dns`, `retry_dns_count` |
| Licenses | 1 | `GET /licenses` |
| Version | 1 | `GET /version` |

**Destructive.** `POST /upgrades`, `POST /deployment/*`, `DELETE /cluster/vips/{uuid}` and
`DELETE /salt` change appliance state. At 9.1 none of this belongs to the log product any more
— appliance lifecycle moved to Fleet LCM / SDDC LCM (`vcf-lifecycle-upgrade`).

**Deprecated at 9.0, 8 total:** `GET /certificates` (`GET_certificates`) and the seven
`{vcHostname}` vSphere operations above.

### Worked example — a log query on 9.0

Shown here only for contrast with the 9.1 example in the sibling file. Three calls; note the
port, the `Bearer` prefix on a *session ID*, and the constraints in the path.

```bash
LOGS=logs.example.com

# 1. Session (L2). provider is required.
SID=$(curl -sk -X POST "https://$LOGS:9543/api/v2/sessions" \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Secret!","provider":"Local"}' \
  | jq -r .sessionId)

# 2. Verify it (L2). 200 => userId; 401/440 => re-authenticate.
curl -sk "https://$LOGS:9543/api/v2/sessions/current" -H "Authorization: Bearer $SID"

# 3. Query: text CONTAINS "error", last 6 minutes, 500 rows, newest first.
#    Constraints are URL-encoded path segments, not a body (L4).
curl -sk -G "https://$LOGS:9543/api/v2/events/text/CONTAINS%20error/timestamp/LAST%20360000" \
  -H "Authorization: Bearer $SID" \
  --data-urlencode 'limit=500' \
  --data-urlencode 'timeout=60000' \
  --data-urlencode 'order-by-direction=DESC'
```

Read `complete` on the response before trusting the row count (L5, including the caveat about
its polarity). For a count-per-minute series instead of raw rows, swap step 3 for
`GET /api/v2/aggregated-events/...` with `aggregation-function=COUNT`, `bin-width=60000` and a
`group-by-field`.

---

## Part 2 — VCF Operations for Networks (632 operations)

Base `/api/ni`. Unchanged in shape at 9.1 (636 operations); this section applies to both
except where noted, and `deltas.md` carries the differences.

Tag distribution from `SPECNI9.0` (sums to 632): `Data Sources` 304, `Entities` 114,
`Settings` 98, `Applications` 35, `Custom Dashboards` 12, `Pinboards` 12, `Config` 9,
`Infrastructure` 8, `Intents` 6, `Guided Network Troubleshooting` 5, `Metrics` 4,
`Microsegmentation` 4, `Search` 4, `Authentication` 4, `Customers` 3, `Migration` 3,
`Schema` 2, `Incomplete TCP flow Sessions` 2, `Logs` 1, `Info` 1, `Path` 1.

### Authentication

Four operations, all **spec-confirmed (9.0)**:

| Call | operationId | Notes |
|---|---|---|
| `POST /auth/token` | `create` | N1. Body `UserCredential`; response `Token {token, expiry}` |
| `DELETE /auth/token` | `delete` | N3. Deletes the header's token; `204` |
| `POST /auth/token/vidm` | `createVidmUserToken` | Token for a user mapped through vIDM |
| `GET /auth/vidm/client-id` | `getVidmOauthClienId` | OAuth client-id for the vIDM access-token request (spelling `ClienId` is the spec's) |

### Entities — the inventory read surface

114 operations, overwhelmingly `GET /entities/<kind>` + `GET /entities/<kind>/{id}` pairs, all
**spec-confirmed (9.0)**. Kinds present include: `vms`, `hosts`, `clusters`, `datastores`,
`folders`, `vc-datacenters`, `vcenter-managers`, `vnics`, `vmknics`, `switchports`,
`virtual-disk`, `distributed-virtual-switches`, `distributed-virtual-portgroups`,
`layer2-networks`, `logical-routers`, `routerinterfaces`, `flows`, `firewalls`,
`firewall-rules`, `firewall-managers`, `security-groups`, `security-tags`, `service-groups`,
`services`, `ip-sets`, `nsx-managers`, `nsxt-controllers`, `nsxt-edge-clusters`,
`nsxt-mp-nodes`, `nsxt-transport-nodes`, `nsxt-edge-node-cpu-cores`, `ipsec-vpn-sessions`,
`kubernetes-clusters`, `kubernetes-namespaces`, `kubernetes-nodes`, `kubernetes-pods`,
`kubernetes-services`, `hcx-*` (managers, sites, services, tunnels, service-meshes,
compute-profiles, network-profiles, l2extensions, appliances), `vmc-sddc`, `sddc-groups`,
`direct-connect`, `dx-tunnels`, `vmware-transit-gateways`, `aws-account-managers`,
`azure-subscriptions`, `problems`.

Standard list parameters on the `GET` list operations [`RAWNI9.0`, e.g. `listVms`]:
`size` (number, **default 10**), `cursor` (string, from the previous response),
`start_time` / `end_time` (epoch **seconds**).

Response `PagedListResponseWithTime`: `results[]` of `{entity_id, entity_type, time}`,
`cursor` (*"Cursor for the next page"*), `total_count`, `start_time`, `end_time`. The default
page size of **10** is the second-most-common "the API returned almost nothing" cause here
after N4.

Bulk and naming:

| Call | operationId | Notes |
|---|---|---|
| `POST /entities/fetch` | *(none in spec)* | Bulk detail by ID. *"Max batch size is 1000"* |
| `POST /entities/names` | `getNames` | IDs → names |
| `GET /entities/names/{id}` | `getName` | One ID → name |
| `POST /entities/vendor-infos/fetch` | `bulkFetchVendorInfo` | Vendor info in bulk |
| `GET /entities/problems`, `GET /entities/problems/{id}` | `listProblemEvents`, `getProblemEvent` | Problem events |
| `POST /entities/problems/fetch` | `bulkFetchProblemEvents` | Bulk problems |
| `GET /entities/problemDetails` | *(none in spec)* | *"List problems"* — distinct path from `/entities/problems` |

### Search

Four operations, all **spec-confirmed (9.0)**:

| Call | operationId | Body | Returns |
|---|---|---|---|
| `POST /search` | `searchEntities` | `SearchRequest` | `PagedListResponseWithTime` |
| `POST /search/ql` | `search` | `SearchQueryRequest` | `SearchQueryResponse` |
| `POST /search/aggregation` | `aggregateSearchResults` | — | Aggregations |
| `POST /search/groupby` | `groupSearchResults` | — | Groups |

`SearchRequest` [`RAWNI9.0`]: `entity_type` (`AllEntityType`), `filter` (*"query filter"* — a
predicate expression, *"similar to SQL where clause"*), `sort_by` (`SortByClause`), `size`,
`cursor`, `time_range` (`TimeRange`).

`SearchQueryRequest` is the UI's natural-language-ish search bar as an API. Spec example,
verbatim:

```json
{ "query": "VM where CPU Cores > 2", "size": 10,
  "time_range": { "start_time": 1534410000, "end_time": 1534410559 } }
```

The `query` property's own example is `"VMs group by Application"`. `SearchQueryResponse`
returns `search_response_total_hits` plus exactly one of `entity_list_response`,
`aggregation_response`, `groupby_response` — the description says a successful execution
returns *"1. List of entity ids … 2. List of aggregations … 3. List of groups"*.

> The **filter-expression grammar** is not in the spec — `RAWNI9.0` says *"Please refer to API
> Guide on details of how to construct filter expression."* That guide was not retrievable.
> **UNVERIFIED** beyond the two examples above.

### Metrics

Four operations. Two are **deprecated in both 9.0 and 9.1**, and the v2 pair is the
replacement — this is not a 9.1 change:

| Call | operationId | Status |
|---|---|---|
| `GET /metrics` | `getMetrics` | **deprecated (9.0 and 9.1)** → use `/metrics/v2` |
| `POST /metrics/fetch` | `fetchBulkMetrics` | **deprecated (9.0 and 9.1)** → use `/metrics/fetch/v2` |
| `GET /metrics/v2` | `getMetricsV2` | Current |
| `POST /metrics/fetch/v2` | `fetchBulkMetricsV2` | Current, bulk |

`GET /metrics/v2` parameters, **all five required** [`RAWNI9.0`]: `entity_id`, `metric`,
`interval`, `start`, `end` (epoch **seconds**, `int64`).

> *"Maximum number of metrics point returned by API is 300. In case the interval and time
> period combination have more than 300 metrics points, client should break the time period to
> multiple batches."* — the spec, verbatim. A 24-hour window at 60-second interval is 1,440
> points and will not come back whole.

Response `MetricResponseV2`: `pointlist[]` of `{timestamps[], values[]}` (parallel arrays,
not point objects), plus `MetricResponseBase`.

Metric names come from `GET /schema/{entity-type}/metrics` (`getMetricsSchema`) —
**spec-confirmed (9.0)**. Guessing a metric name is the equivalent of guessing a stat key on
`/suite-api`: you get nothing useful. `GET /schema/problems`
(`bulkFetchEventMetaInfo`) returns event meta-information.

### Data sources (304 operations)

By far the largest tag. ~40 families, each with roughly the same 7–12 operations
(`GET` list, `POST` create, `GET|PUT|DELETE /{id}`, `POST /{id}/enable`, `POST /{id}/disable`,
plus family-specific extras). Families present at 9.0, with operation counts:

`arista-switches` 10 · `aws-accounts` 7 · `azure-subscriptions` 7 · `brocade-switches` 10 ·
`checkpoint-firewalls` 8 · `cisco-aci` 10 · `cisco-asr-xr-switches` 3 ·
`cisco-asrxr-switches` 7 · `cisco-switches` 12 · `common-device` 11 · `dell-os10-switches` 10 ·
`dell-switches` 10 · `f5-bigip` 9 · `fortinet-firewalls` 8 · `generic-switches` 8 ·
`hcx-connectors` 7 · `hpe-switches` 10 · `hpov-managers` 7 · `hpvc-managers` 7 · `huawei` 10 ·
`infoblox-managers` 7 · `juniper-switches` 10 · `kubernetes-clusters` 7 · `loginsight` 7 ·
`mellanox-switches` 10 · `nsxalb` 7 · `nsxt-managers` 7 · `nsxv-managers` 9 ·
`openshift-clusters` 7 · `panorama-firewalls` 8 · `pks` 7 · `servicenow-instances` 7 ·
`ucs-managers` 9 · `vcenters` 8 · `velocloud` 7 · `vmc-nsxmanagers` 7

Plus cross-family: `PUT /data-sources/accept-certificate/{id}` (`acceptCertificate`),
`GET /data-sources/health` (`getDatasourceHealth`), `/data-sources/bulk` (3 —
`bulkDataSourceOperation`, `bulkDataSourceAddOperation`, `getBulkOperationDetails`) and
`/data-sources/migrate` (3 — `migrateCollectorDataSources`, `getMigrationStatus`,
`cancelBulkOperation`).

All **spec-confirmed (9.0)**. Note `cisco-asr-xr-switches` (3 ops) and `cisco-asrxr-switches`
(7 ops) are **two distinct path prefixes** in the same spec — not a typo in this file.

**Write path.** `POST`, `PUT`, `DELETE`, `/enable` and `/disable` on any data source change
what the product collects. Disabling a data source stops flow collection for everything behind
it.

**At 9.1, `aws-accounts`, `azure-subscriptions` and `nsxalb` — 21 operations — are all
deprecated.** They are not deprecated at 9.0. See `deltas.md`.

### Applications and tiers

35 operations under `/groups/*`, all **spec-confirmed (9.0)**. Core:

| Call | operationId |
|---|---|
| `GET|POST /groups/applications` | `listApplications`, `addApplication` |
| `POST /groups/applications/full/` | `addApplicationWithTiers` |
| `GET|DELETE /groups/applications/{id}` | `getApplicationById`, `deleteApplication` |
| `GET /groups/applications/{id}/flow-metrics` | `getAppFlowMetrics` |
| `GET /groups/applications/{id}/flow-summary` | `getApplicationFlowSummary` |
| `GET /groups/applications/{id}/top-talking-member` | `getAppTopTalkingMembers` |
| `GET /groups/applications/{id}/top-talking-pair` | `getAppTopTalkingPairs` |
| `GET /groups/applications/{id}/problems` | `getAppProblems` |
| `GET|POST /groups/applications/{id}/tiers` | `listApplicationTiers`, `addTier` |
| `GET|PUT|DELETE /groups/applications/{id}/tiers/{tier-id}` | `getApplicationTier`, `editApplicationTier`, `deleteTier` |
| `GET /groups/discovered-applications` | `getDiscoveredApplications` |
| `POST /groups/discovered-applications/save` | `saveDiscoveredApplications` |
| `GET /groups/task/progress/{requestId}` | `getBulkApplicationTaskProgress` |

Flow-based application discovery (FBAD) has its own CSV-driven config family under
`/groups/discovered-applications/custom-config/fbad*` (9 operations, incl.
`uploadFBADCSV`, `getFBADProgress`, `exportFBADCSVErrors`).

### Micro-segmentation and path

| Call | operationId |
|---|---|
| `POST /micro-seg/graph` | `getConnectionGraph` |
| `POST /micro-seg/entity/single` | `getEntityCommunicationSummary` |
| `POST /micro-seg/recommended-rules` | `listRecommendedRules` |
| `POST /micro-seg/recommended-rules/nsx` | `exportNsxRecommendedRules` |
| `POST /path/firewall-rules` | `pathFirewallRules` — *"Get firewall rules for specified client server ips and port/protocol"* |

All **spec-confirmed (9.0)**. `exportNsxRecommendedRules` produces NSX-consumable rules from
observed flows; applying them is NSX's job (`nsx-security-policy`).

### Alerts, intents and dashboards

- **Search-based alerts** — 7 operations, **spec-confirmed (9.0)**:
  `GET|POST /settings/alerts/search-based-alerts`,
  `GET|PUT|DELETE /settings/alerts/search-based-alerts/{id}`, plus `/enable` and `/disable`.
- **Intents** — 6 operations under `/alert-configs/intents/`: `createIntent`, `getIntent`,
  `updateIntent`, `deleteIntent`, and `POST /{id}/enable` and `/{id}/disable` (**both have no
  `operationId` in the spec**).
- **Custom dashboards** — 12 operations, **spec-confirmed (9.0)**: `getAllCustomDashboards`,
  `createCustomDashboard`, `getCustomDashboard`, `editCustomDashboard`,
  `deleteCustomDashboard`, `duplicateCustomDashboard`, `shareCustomDashboard`,
  `removeShareCustomDashboard`, `setCustomDashboardPreference`, and pin CRUD
  (`createCustomDashboardPin`, `updateCustomDashboardPin`, `deleteCustomDashboardPin`).
- **Pinboards** — 12 operations, **all deprecated at 9.0 and still deprecated at 9.1**. Custom
  dashboards is the same shape, not deprecated, and is the obvious successor — but no spec
  field states that mapping, so treat "pinboards → custom dashboards" as **inferred**.

### Settings, config and infrastructure

98 `Settings` operations. Highlights, all **spec-confirmed (9.0)**:

| Area | Ops | Notes |
|---|---|---|
| Users / user-groups / vIDM | 19 (7+5+7) | `getUsers`, `getAllUsers`, `getUser`, `deleteUser`, `addVidmUser`, `updateVidmUserRole`, `PUT /settings/users/password` (**no `operationId`**); `getUserGroups`, `addVidmUserGroup`, `updateVidmUserGroupRole`, `getUserGroup`, `deleteUserGroup`; vIDM config CRUD + `getCertificate` + `enableVidm`/`disableVidm` |
| Syslog | 9 | `getSyslogTargetList`, `addSyslogTarget`, `updateSyslogTarget`, `deleteSyslogTarget`, `getSyslogMapping`, `updateSyslogMapping`, `sendSyslogTestMessage`, `getSyslogStatus`, `updateSyslogStatus` |
| SNMP | 9 | engine ID `GET|PUT` (`getSNMPEngineId`, `updateSNMPEngineId`); seven `/settings/snmp/profiles*` operations that **have no `operationId`** in the spec |
| Web proxies | 9 | `getWebProxies`, `addWebProxy`, `getConnectedClientsToWebProxy`, `validateConnectionsViaWebProxy`, `validateWebProxyMigration` |
| Databus subscribers | 5 | `getAllSubscriber`, `createSubscriber`, `getSubscriber`, `updateSubscriber`, `deleteSubscriber` |
| Certificates | 4 | `getCertificatesDetails`, `updateCertificate`, and two status operations |
| Backup / restore | 9 | Both `/settings/backup*` **and** `/config/backup*` exist — two distinct trees (`getBackupConfig` vs `getBackupConfiguration`) |
| Subnet mappings | 4 | `getSubnetMappings`, `createSubnetMapping`, `updateSubnetMapping`, `deleteSubnetMapping` |
| Login banner | 4 | `getLoginBanner`, `addLoginBanner`, `updateLoginBanner`, `deleteLoginBanner` |
| IP tags | 4 current + 4 deprecated | `/settings/ip-tags/v2/*` (`getTagIdsV2`, `getIpTagV2`, `addTagV2`, `removeTagV2`) supersede the deprecated v1 set |
| Licensing | **4** | `getLicenses`, `activateSerialNumber`, `deactivateSerialNumber`, `validateSerialNumber` — the last three already deprecated at 9.0. **`getLicensesV2` does not exist at 9.0**; it is one of the five 9.1 additions |

Infrastructure (8): `listNodes`, `listExpandedNodes`, `getNode`, `deleteNode`, and the VCF
watermark family (`getVCFWatermark`, `saveVCFWatermark`, `updateVCFWatermark`,
`deleteVCFWatermark`). Customers (3): proxy data-encryption key details, rotation and rotation
status (`getProxyKeyDetails`, `rotateProxyKey`, `getProxyKeyRotationStatus`).

Other small trees: `POST /logs/audit` (`getAuditLogs`), `GET /info/version` (`getVersion`),
Guided Network Troubleshooting (5: `listTroubleshootingIncidents`, `createTroubleshootingIncident`,
`getTroubleshootingIncident`, `updateTroubleshootingIncident`, `deleteTroubleshootingIncident`),
Incomplete TCP flow sessions (2: `listIncompleteSessions`, `csvExportIncompleteSessions`),
Migration (3, all deprecated — see below).

### Deprecated at 9.0 (31 operations)

`deprecated: true` in `SPECNI9.0`. All 31 are **still deprecated at 9.1**; 9.1 adds 22 more.

| Family | Ops | Replacement |
|---|---|---|
| Pinboards | 12 | Custom dashboards (**inferred**, not stated in the spec) |
| User-defined events (`/settings/events/user-defined-events*`) | 7 | Search-based alerts (**inferred**) |
| IP tags v1 (`/settings/ip-tags/tag-ids`, `/{tag-id}`, `/{tag-id}/add`, `/{tag-id}/remove`) | 4 | `/settings/ip-tags/v2/*` — same shape, `V2` operationIds |
| Licensing v1 (`activateSerialNumber`, `deactivateSerialNumber`, `validateSerialNumber`) | 3 | Not stated. `getLicensesV2` is 9.1-only and covers reads only |
| Migration (`getMigrationWave` on `/migration/{groupType}`, `enableMigrationWave`, `disableMigrationWave`) | 3 | At 9.1 the path becomes `/migration/wave/{groupType}` — still deprecated |
| Metrics v1 (`getMetrics`, `fetchBulkMetrics`) | 2 | `/metrics/v2`, `/metrics/fetch/v2` |

---

## What is not here

- **`/suite-api`** — resources, stats, alerts, reports, custom groups, policies, fleet
  management. That is `vcf-operations-monitoring` (and `vcf-foundation` for IAM).
- **Real-time metrics.** No 9.0 counterpart exists: the product is absent from the 9.0 BOM
  [`DOPS` §Delta table] and there is no 9.0 spec in the repo [`DELTA`].
- **Log Management.** The 9.1 product. `references/9.1/logs-and-networks.md`.
- **Appliance upgrade orchestration** beyond the log appliance's own `/upgrades` tree —
  `vcf-lifecycle-upgrade`.
- **Acting on NSX rules** recommended by micro-segmentation — `nsx-security-policy`.

## Still unverified

- **The Logs constraint grammar** beyond `CONTAINS` and `LAST` (see "Querying events").
- **Whether `AVG` is a valid `aggregation-function`** — prose says yes, the enum says no.
- **The polarity of the `complete` flag** — the two query operations describe it oppositely.
- **The Networks filter-expression grammar** for `POST /search` — the referenced API Guide was
  not retrievable.
- **Networks token TTL** as a constant; only the per-response `expiry` field is documented.
- **Role, capability and privilege names** on both products.
- **Retention and roll-up** on both products.
- **Rate limits** on any operation here.
- **Whether "pinboards → custom dashboards" and "user-defined events → search-based alerts"
  are the intended replacements.** Both are inferred from shape, not stated.
