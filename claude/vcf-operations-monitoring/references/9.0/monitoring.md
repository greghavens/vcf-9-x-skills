# VCF Operations 9.0 — Monitoring Reference

**Scope:** VMware Cloud Foundation Operations 9.0.x, `/suite-api` REST API. Everything here is
`[9.0]` unless explicitly tagged otherwise. Log Management / VCF Operations for Logs, VCF
Operations for Networks and the real-time metrics API are **out of scope** — see the
`vcf-operations-logs-and-networks` skill.

**Sources.**
- `SPEC9.0` = `research/spec-inventory/9.0__vcf-operations.ops.json` — **370 operations**, base
  path `/suite-api`, from git tag `9.0.0.0` of `github.com/vmware/vcf-api-specs`. The spec
  `version` field is empty in the 9.0 document.
- `SPEC9.1` = `research/spec-inventory/9.1__vcf-operations.ops.json` — 504 operations, spec
  version `9.1.0.0`. Used here only to state whether an operation also exists at 9.1.
- `RAW9.1` = `specifications/vcf-operations/vcf-operations-openapi.json` at tag `9.1.0.0`.
- `DOPS` = `research/vcf-operations.md`.
- `DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md`.

Every path below was checked against `SPEC9.0` and is marked **spec-confirmed (9.0)** with its
`operationId`.

> **Field-level schemas are inherited from 9.1.** The 9.0 *raw* OpenAPI document was not
> available when this file was written — only the operation inventory (`method`, `path`,
> `operationId`, `summary`, `tags`, `deprecated`). Request/response **field names, enum values
> and query-parameter lists** below are read from `RAW9.1`. For every operation shown here the
> `operationId` is byte-identical across the two inventories, so the schema is very likely
> identical too — but at 9.0, field-level detail is **UNVERIFIED**. Before writing a body
> against a 9.0 appliance, confirm the schema in its own Swagger UI:
> `https://<ops-fqdn>/suite-api/doc/swagger-ui.html` (singular `doc`) [DOPS §"On-appliance API
> discovery"]. Paths, methods and operationIds are *not* inherited — those are confirmed at 9.0.

> **Documentation-derived, not live-validated.** Nothing here has been run against a VCF
> Operations appliance. The read paths are cheap to try; the write paths are not.

---

## Contents

- [Prerequisites](#prerequisites)
  - P1 — A valid token, less than six hours old
  - P2 — The Authorization header form is `OpsToken`, not `Bearer`
  - P3 — The caller's role permits the operation — role names UNVERIFIED
  - P4 — The resource exists in inventory
  - P5 — The resource is actually collecting
  - P6 — The adapter instance and its collector / cloud proxy are up
  - P7 — The stat key exists for that resource kind
  - P8 — The time range is epoch milliseconds and inside retention — retention UNVERIFIED
  - P9 — Things this file could not verify
- [Inventory — resources](#inventory--resources)
- [Stats and metrics](#stats-and-metrics)
- [Alerts](#alerts)
- [Alert definitions, symptoms and recommendations](#alert-definitions-symptoms-and-recommendations)
- [Reports and report schedules](#reports-and-report-schedules)
- [Custom groups](#custom-groups)
- [Supporting surfaces](#supporting-surfaces)
- [Worked example — a resource's CPU metrics over a time range](#worked-example--a-resources-cpu-metrics-over-a-time-range)
- [What is not here](#what-is-not-here)
- [Deprecated operations in 9.0](#deprecated-operations-in-90)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what must
hold, **how to verify it**, the version it applies to, and whether 9.1 differs. The failure mode
on this API is rarely a 4xx — it is a `200` with an empty payload — so these checks are what
turns "the API is broken" into "the adapter stopped collecting on Tuesday."

### P1 — A valid token, less than six hours old `[9.0]`

**Must be true:** every call carries a token from
`POST /suite-api/api/auth/token/acquire` — **spec-confirmed (9.0)**, `acquireToken`.
Request body (`username-password`): `username` (required), `password` (required),
`authSource` (optional; `LOCAL` is the default, or the name of an imported LDAP / Active
Directory / vIDM / SSO source) [DOPS §"Token acquisition"].

Response (`auth-token`): `token` (required), `validity` (required, integer),
`expiresAt`, `roles`. The token format is `uuid::uuid`, e.g.
`8f868cca-27cc-43d6-a838-c5467e73ec45::77cea9b2-1e87-490e-b626-e878beeaa23b` [DOPS].

**TTL is six hours** and there is no refresh operation — you re-acquire [DOPS: "a re-usable ops
authorization token that expires after six hours"]. A release operation does exist:
`POST /api/auth/token/release` — **spec-confirmed (9.0)**, `releaseToken`. (Note the dossier
states "no release/revoke endpoint is documented" from the prose pages; the spec inventory
contradicts that prose — trust the spec.)

**How to verify:** `GET /api/auth/currentuser` — **spec-confirmed (9.0)**, `getCurrentUser`.
A `401`/`403` means the token is expired, malformed, or the header form is wrong (see P2)
[DOPS].

**9.1 difference:** none for acquisition. 9.1 *adds* `POST /api/auth/token/exchange`
(`exchangeOpsTokenWithJwtToken`) for obtaining downstream-service JWTs — absent at 9.0.

### P2 — The Authorization header form is `OpsToken`, not `Bearer` `[9.0]`

**Must be true:** the header is

```
Authorization: OpsToken <token>
```

Accepted alternatives at 9.0 [DOPS §"Token acquisition"]:

```
Authorization: vRealizeOpsToken <token>    # legacy form, still supported
Authorization: SSO2Token <SSO_SAML_TOKEN>  # external SSO SAML token
```

The spec's security scheme is `Token-based-authorization`: `type: apiKey`, `in: header`,
`name: Authorization` — i.e. the scheme confirms the header name but not the prefix; the prefix
comes from the documentation [SPEC9.0 `meta.security_schemes`; DOPS].

**How to verify:** any authenticated GET. A `Bearer`-prefixed token that works against SDDC
Manager will fail here.

**9.1 difference — this one matters.** 9.1 additionally accepts
`Authorization: Bearer <token>` issued by VCF SSO [DOPS §"Token acquisition"]. **9.0 does not.**
Code written against a 9.1 lab using `Bearer` will 401 against a 9.0 appliance.

Auth beyond this — identity sources, SSO, role assignment — belongs to `vcf-foundation`.

### P3 — The caller's role permits the operation — role names UNVERIFIED `[9.0]`

**Must be true:** the account has a role granting the privileges the operation needs. Reads
(resources, stats, alerts, reports) need only read privileges; writes (create alert definition,
create custom group, create report schedule, delete resource) need administrative privileges.

> **UNVERIFIED.** Neither `SPEC9.0` nor `DOPS` enumerates the built-in role names, and the raw
> spec carries no role-name enum. The commonly-cited pair **Administrator** and **ReadOnly**
> is *not* attested by any source available here, and neither is the privilege required by any
> specific operation. Do not assert a role-to-operation mapping. Determine it per deployment.

**How to verify (this is the reliable route, and it works identically in both versions):**

| Call | operationId | Status |
|---|---|---|
| `GET /api/auth/roles` (optional `?roleName=`) | `getRoles` | **spec-confirmed (9.0)** |
| `GET /api/auth/roles/{roleName}` | `getRoleByName` | **spec-confirmed (9.0)** |
| `GET /api/auth/roles/{roleName}/privileges` | `getRolePrivileges` | **spec-confirmed (9.0)** |
| `GET /api/auth/privileges` | `getAvailablePrivileges` | **spec-confirmed (9.0)** |
| `GET /api/auth/privilegegroups` | `getAvailablePrivilegeGroups` | **spec-confirmed (9.0)** |
| `GET /api/auth/currentuser/permissions` | `getAssignedRolePermissionsForCurrentUser` | **spec-confirmed (9.0)** |
| `GET /api/auth/currentuser/roles/{roleName}/privileges` | `getCurrentUserRolePrivileges` | **spec-confirmed (9.0)** |

The `roles` array on the `auth-token` response also reports what the token was issued with.

**9.1 difference:** none for these. `SPEC9.0` contains **57** operations under `/api/auth`;
`SPEC9.1` contains **59** — the same 57 plus `GET /api/auth/sources/vidb/well-known-url` and
`POST /api/auth/token/exchange`. An earlier prose pass claimed `/auth/roles` and
`/auth/privileges` were 9.1-only; **that is wrong** — both are present at 9.0, as the table
above shows. 9.1 adds a *parallel* fleet-wide IAM tree (`/api/fleet-management/iam/*`, 70
operations) which does not replace these.

### P4 — The resource exists in inventory `[9.0]`

**Must be true:** you have the resource's `identifier` (a UUID). Names are not identifiers, and
`GET /api/resources?name=` supports only a **single** element despite being an array parameter
[`RAW9.1` parameter note on `getResources`].

**How to verify:** `GET /api/resources?name=<exact-name>` — **spec-confirmed (9.0)**,
`getResources` — or `POST /api/resources/query` — **spec-confirmed (9.0)**,
`getMatchingResources` — for anything richer. Read `identifier` off the `resource` object.

**9.1 difference:** none. Both operations are present and identical at 9.1.

### P5 — The resource is actually collecting `[9.0]`

**Must be true:** the resource is not merely discovered but receiving data. This is the single
most common cause of an empty stats response.

**How to verify:** `GET /api/resources/{id}` — **spec-confirmed (9.0)**, `getResource` — and
inspect `resourceStatusStates[]`:

- `resourceState` — enum `STOPPED | STARTING | STARTED | STOPPING | UPDATING | FAILED |
  MAINTAINED | MAINTAINED_MANUAL | REMOVING | NOT_EXISTING | NONE | UNKNOWN`.
  You want `STARTED`.
- `resourceStatus` — enum `NONE | ERROR | UNKNOWN | DOWN | DATA_RECEIVING |
  OLD_DATA_RECEIVING | NO_DATA_RECEIVING | NO_PARENT_MONITORING | COLLECTOR_DOWN`.
  You want `DATA_RECEIVING`. `OLD_DATA_RECEIVING` means the series exists but stops before
  "now"; `COLLECTOR_DOWN` sends you straight to P6.
- `statusMessage` — free text, usually names the actual fault.
- `adapterInstanceId` — the adapter to check in P6.

Also on the `resource` object: `monitoringInterval` / `monitoringIntervalSeconds` (the sampling
period — a 5-minute interval means a 10-minute window yields ~2 points, which is a legitimate
reason a query "looks empty"), and `badges[]` with `type` in `ANOMALY | CAPACITY_REMAINING |
COMPLIANCE | DENSITY | EFFICIENCY | FAULT | HEALTH | RISK | STRESS | TIME_REMAINING |
TIME_REMAINING_WHATIF | RECLAIMABLE_CAPACITY | WORKLOAD` and `color` in
`GREEN | YELLOW | ORANGE | RED | GREY`.

A resource can also be deliberately excluded: `PUT /api/resources/{id}/maintained`
(`markResourceAsBeingMaintained`) and `PUT /api/resources/maintained`
(`markResourcesAsBeingMaintained`) — both **spec-confirmed (9.0)** — put it in `MAINTAINED`,
which suppresses alerting. Check that before concluding a collection fault.

**9.1 difference:** none — same operations, same enums (enums read from `RAW9.1`; see the
inheritance note above).

### P6 — The adapter instance and its collector / cloud proxy are up `[9.0]`

**Must be true:** the adapter instance that owns the resource is collecting, and the collector
(cloud proxy) hosting it is reachable.

**How to verify:**

| Call | operationId | What to read |
|---|---|---|
| `GET /api/adapters?adapterKindKey=` | `enumerateAdapterInstances` | list of `adapter-instance` |
| `GET /api/adapters/{adapterId}` | `getAdapterInstance` | one instance |
| `GET /api/adapters/{adapterId}/resources` | `getResourcesOfAdapterInstance` | what it owns |
| `POST /api/adapters/testConnection` | `testConnection` | live connectivity probe |
| `GET /api/collectors?host=` | `getCollectors` | list of `collector` |
| `GET /api/collectors/{id}/adapters` | `getAdaptersOnCollector` | adapters per collector |

All **spec-confirmed (9.0)**.

On `adapter-instance`: `lastCollected` and `lastHeartbeat` (epoch ms), `numberOfMetricsCollected`,
`numberOfResourcesCollected`, `messageFromAdapterInstance` (the human-readable failure),
`monitoringInterval`, `collectorId`, `collectorGroupId`, `credentialInstanceId`.

On `collector`: `state` — enum `DOWN | UP`; `type` — enum
`INTERNAL | CLOUD_PROXY | OTHER | UNIFIED_CLOUD_PROXY`; `lastHeartbeat`; `local`;
`dataPersistenceEnabled`; `hostName`; `adapterInstanceIds[]`.

A stale `lastCollected`, a `messageFromAdapterInstance`, or a collector in `DOWN` explains an
empty stats result more often than the query being wrong.

Terminology: in 9.0 this component is called the **VCF Operations collector**; in 9.1 it is
renamed **cloud proxy** [DOPS §"Renames"; DELTA]. The API type enum already says `CLOUD_PROXY`
in both. Use the 9.0 name when talking about a 9.0 deployment.

**9.1 difference:** the operations above are identical. 9.1 *adds* four certificate-renewal
operations on collectors and collector groups (see `../deltas.md`); none of them affect
collection status checks.

### P7 — The stat key exists for that resource kind `[9.0]`

**Must be true:** the `statKey` you pass is one this resource actually publishes. A wrong key
returns an empty series, not an error — the highest-yield check in this file.

**How to verify:**

| Call | operationId | Scope |
|---|---|---|
| `GET /api/resources/{id}/statkeys` | `getStatKeys` | keys for one resource |
| `GET /api/resources/statkeys` | `getStatKeysOfResources` | keys across resources |
| `GET /api/adapterkinds/{adapterKindKey}/resourcekinds/{resourceKindKey}/statkeys` | `getResourceTypeAttributesForAdapterType` | keys for a whole resource kind |

All **spec-confirmed (9.0)**. The response is `stat-keys` → `stat-key[]` → `key` (string,
required).

**9.1 difference:** none for these three. 9.1 adds
`GET /api/adapterkinds/{adapterKindKey}/resourcekinds/{resourceKindKey}/identifiers`
(`getResourceIdentifiersDetails`), which is about resource *identifiers*, not stat keys.

### P8 — The time range is epoch milliseconds and inside retention — retention UNVERIFIED `[9.0]`

**Must be true:** `begin` and `end` are integers, milliseconds since the Unix epoch, and the
window falls inside the deployment's retention.

**How to verify:** `RAW9.1` describes `begin` as "the beginning date as a long value" and `end`
correspondingly; both are `integer`, both optional. Roll-up granularity is set by `rollUpType`
(`SUM | AVG | MIN | MAX | NONE | LATEST | COUNT`), `intervalType`
(`HOURS | MINUTES | SECONDS | DAYS | WEEKS | MONTHS | YEARS`) and `intervalQuantifier`
(integer).

> **UNVERIFIED.** Neither `SPEC9.0` nor `DOPS` states the default retention period, the
> roll-up tiering, or what happens when `begin` predates retention. Do not quote a retention
> figure. Check the deployment's policy settings, or start with a narrow recent window and widen.

Sanity check that isolates the problem in one call: `GET /api/resources/{id}/stats/latest`
(`getLatestStats`, **spec-confirmed (9.0)**). If latest returns data and your ranged query does
not, the range is the fault, not the resource.

**9.1 difference:** none.

### P9 — Things this file could not verify `[9.0]`

- **Built-in role names and the role required by each operation** (P3). **UNVERIFIED.**
- **Metric retention and roll-up tiering** (P8). **UNVERIFIED.**
- **9.0 request/response field names, enums and query parameters.** Inherited from `RAW9.1`;
  the 9.0 raw document was not available. Paths, methods and operationIds *are* confirmed at
  9.0. **UNVERIFIED at field level.**
- **Any dashboards API.** Not present in `SPEC9.0`, `SPEC9.1` or `RAW9.1`. See
  [What is not here](#what-is-not-here). **UNVERIFIED.**
- **Rate limits / throttling.** Nothing in the inventory or dossier. **UNVERIFIED.**
- **Whether `pageSize` has a documented default of 1000.** `DOPS` asserts "`pageSize` default
  1000, `page` 0-based" for `GET /api/resources`; `RAW9.1` documents both parameters but states
  no default. The 0-based `page` is confirmed by the parameter description; the 1000 default is
  **UNVERIFIED**. Pass `pageSize` explicitly.

---

## Inventory — resources

`/api/resources` carries **66 operations** at 9.0 — identical count and set at 9.1.

### Lookup

| Method | Path | operationId |
|---|---|---|
| GET | `/api/resources` | `getResources` |
| POST | `/api/resources/query` | `getMatchingResources` |
| GET | `/api/resources/{id}` | `getResource` |
| GET | `/api/resources/{id}/relationships` | `getRelationships` |
| GET | `/api/resources/{id}/relationships/{relationshipType}` | `getRelationship` |
| POST | `/api/resources/bulk/relationships` | `getResourcesRelationships` |
| GET | `/api/adapterkinds/{adapterKindKey}/resources` | `getResourcesWithAdapterKind` |
| GET | `/api/adapterkinds/{adapterKindKey}/resourcekinds/{resourceKindKey}/resources` | `getResourcesWithAdapterAndResourceKind` |

All **spec-confirmed (9.0)**.

`GET /api/resources` query parameters (from `RAW9.1`): `name[]` (single element only),
`regex[]` (Java regex; mutually exclusive with `name`), `adapterKind[]`, `resourceKind[]`,
`collectorName[]`, `collectorId[]`, `maintenanceScheduleId[]`, `adapterInstanceId[]`,
`recentlyAdded` (seconds since epoch), `resourceState[]`, `resourceStatus[]`, `resourceHealth[]`,
`parentId[]`, `credentialId[]`, `resourceId[]`, `propertyName`, `propertyValue`, `statKey`,
`statKeyLowerBound`, `statKeyUpperBound`, `statKeyInclusive`, `includeRelated`
(`PARENT | CHILD`), `page` (0-based), `pageSize`.

`POST /api/resources/query` body (`resource-query`) takes the same filters as arrays plus two
richer ones: `statConditions` and `propertyConditions`, each a
`stat-or-property-condition-query` with `conditions[]` (required) and `conjunctionOperator`
(`AND | OR`); and `resourceTag[]` with `category` (required) and `name`. Pagination is via
`?page=` and `?pageSize=` query parameters, not the body.

Use the POST form when you need more than one name, an AND/OR over metric thresholds, or tag
filtering. Use the GET form for a single well-known name.

### Properties

| Method | Path | operationId |
|---|---|---|
| GET | `/api/resources/{id}/properties` | `getResourceProperties` |
| GET | `/api/resources/properties` | `getResourcePropertiesList` |
| POST | `/api/resources/properties/latest/query` | `queryLatestPropertiesOfResources` |
| POST | `/api/resources/{id}/properties` | `addProperties` |
| POST | `/api/resources/properties` | `addResourcesProperties` |
| POST | `/api/resources/properties/adapterkinds/{adapterKind}` | `addResourcesPropertiesUsingAdapterKind` |
| POST | `/api/resources/{id}/properties/adapterkinds/{adapterKind}` | `addPropertiesUsingPushAdapterKind` |

All **spec-confirmed (9.0)**. Properties are string/categorical facts about a resource; stats
are numeric time series. Filtering by `propertyName` + `propertyValue` on `getResources` checks
existence when the value is omitted.

### Lifecycle and monitoring state — write operations

| Method | Path | operationId | Note |
|---|---|---|---|
| PUT | `/api/resources` | `updateResource` | |
| POST | `/api/resources/adapterkinds/{adapterKindKey}` | `createResourceUsingAdapterKind` | |
| POST | `/api/resources/adapters/{adapterInstanceId}` | `createResourceUsingAdapterInstance` | |
| DELETE | `/api/resources/{id}` | `deleteResource` | **destructive** |
| DELETE | `/api/resources/bulk` | `deleteResources` | **destructive, bulk** |
| PUT / DELETE | `/api/resources/{id}/maintained` | `markResourceAsBeingMaintained` / `unmarkResourceAsBeingMaintained` | suppresses alerting |
| PUT / DELETE | `/api/resources/maintained` | `markResourcesAsBeingMaintained` / `unmarkResourcesAsBeingMaintained` | bulk |
| PUT | `/api/resources/{id}/geolocation` | `updateGeoLocationOfResource` | |

All **spec-confirmed (9.0)**.

> **Destructive.** `deleteResource` and `deleteResources` remove objects and their history from
> the Operations database. There is no undo in this API; the object returns only if the adapter
> rediscovers it, and its historical series does not come back. Treat a bulk delete as a change
> requiring approval.

**Deprecated in 9.0 — and still deprecated in 9.1:** the four monitoring-state operations
`PUT /api/resources/monitoringstate/{start,stop}` (`startMonitoringResources` /
`stopMonitoringResources`) and `PUT /api/resources/{id}/monitoringstate/{start,stop}`
(`startMonitoringResource` / `stopMonitoringResource`). They are flagged `deprecated: true` in
both inventories. Prefer the `maintained` operations. Do not build new automation on them.

---

## Stats and metrics

Fifteen operations have `/stats` in their path — **11 read** and **4 push** — all
**spec-confirmed (9.0)** and all present unchanged at 9.1. (Stat *keys* are a separate three
operations; see P7.)

### Reading

| Method | Path | operationId | Use for |
|---|---|---|---|
| GET | `/api/resources/{id}/stats` | `getStatsOfResource` | one resource, ranged, params in query |
| POST | `/api/resources/{id}/stats/query` | `getStatsForResource` | one resource, ranged, body |
| GET | `/api/resources/stats` | `getStatsOfResources` | many resources, ranged, query |
| POST | `/api/resources/stats/query` | `getStatsForResources` | many resources, ranged, body |
| GET | `/api/resources/{id}/stats/latest` | `getLatestStats` | most recent sample(s), one resource |
| GET | `/api/resources/stats/latest` | `getLatestStatsOfResources` | most recent sample(s), many |
| POST | `/api/resources/stats/latest/query` | `queryLatestStatsOfResources` | last N samples, body |
| GET | `/api/resources/{id}/stats/topn` | `getTopNStatsOfResource` | ranking, one resource |
| GET | `/api/resources/stats/topn` | `getTopNStatsOfResources` | ranking, many |
| GET | `/api/resources/{id}/stats/dt` | `getDTStatsOfResource` | dynamic-threshold series |
| POST | `/api/resources/stats/dt/query` | `getStatsAndDTForResources` | stats + DT together |

**`stat-query` body** (used by `getStatsForResource` and `getStatsForResources`) — from `RAW9.1`:

| Field | Type | Meaning |
|---|---|---|
| `resourceId` | `array<string>` | resource identifiers (redundant when the id is in the path) |
| `statKey` | `array<string>` | metric keys |
| `begin` | integer | window start, epoch ms |
| `end` | integer | window end, epoch ms |
| `rollUpType` | enum | `SUM \| AVG \| MIN \| MAX \| NONE \| LATEST \| COUNT` |
| `intervalType` | enum | `HOURS \| MINUTES \| SECONDS \| DAYS \| WEEKS \| MONTHS \| YEARS` |
| `intervalQuantifier` | integer | count of `intervalType` per bucket |
| `dt` | boolean | return dynamic-threshold-based stats |
| `latestMaxSamples` | integer | cap when querying latest |
| `metrics` | boolean | force the keys to be treated as metrics |
| `currentOnly` | boolean | skip stats that have stopped updating |
| `wrapStatValues` | boolean | XML-response wrapping only |

The GET forms take exactly the same names as query parameters, plus the path `id`.

**`latest-stat-query` body** (`queryLatestStatsOfResources`): `resourceId[]`, `statKey[]`,
`maxSamples`, `metrics`, `currentOnly`, `wrapStatValues`. Note `maxSamples` here versus
`latestMaxSamples` in `stat-query` — the names differ, and mixing them up silently drops the cap.

**Top-N** (`getTopNStatsOfResources`) additionally requires `topN` (integer, **required**) and
takes `groupBy` (`RESOURCE | STATKEY`, default `RESOURCE`) and `sortOrder`
(`ASCENDING | DESCENDING`, default `ASCENDING`). Response schema is `ResourceStatGroupList`, not
`stats-of-resources` — a different shape from the other stat calls.

**Response shape** (`stats-of-resources`) for everything except top-N:

```
stats-of-resources
└─ values[]  (stats-of-resource)
   ├─ resourceId : string
   └─ stat-list.stat[]  (stats)
      ├─ statKey.key    : string   (required)
      ├─ timestamps[]   : integer  (required, epoch ms)
      ├─ data[]         : number
      ├─ values[]       : string
      ├─ statValues[]   : string
      ├─ rollUpType     : enum
      ├─ intervalUnit   : { intervalType, quantifier }
      ├─ minThresholdData[] / maxThresholdData[] : number
      ├─ smoothValues[] : number
      └─ dtTimestamps[] : integer
```

`timestamps[]` and `data[]` are parallel arrays — index *i* of one pairs with index *i* of the
other. An empty `stat-list` with a `200` is the empty-answer failure mode; walk P4 → P7.

### Writing (push adapter)

| Method | Path | operationId |
|---|---|---|
| POST | `/api/resources/{id}/stats` | `addStats` |
| POST | `/api/resources/stats` | `addStatsForResources` |
| POST | `/api/resources/{id}/stats/adapterkinds/{adapterKind}` | `addStatsUsingPushAdapterKind` |
| POST | `/api/resources/stats/adapterkinds/{adapterKind}` | `addStatsForResourcesUsingPushAdapterKind` |

All **spec-confirmed (9.0)**. These are for pushing external metrics in, not for reading.

### Super metrics

`/api/supermetrics` — 5 operations, **spec-confirmed (9.0)**, unchanged at 9.1:
`getSuperMetrics` (GET), `createSuperMetric` (POST), `updateSuperMetric` (PUT),
`getSuperMetric` (GET `/{id}`), `deleteSuperMetric` (DELETE `/{id}`).

---

## Alerts

`/api/alerts` — 13 operations, **spec-confirmed (9.0)**, identical set at 9.1.

| Method | Path | operationId |
|---|---|---|
| GET | `/api/alerts` | `getAlerts` |
| POST | `/api/alerts/query` | `queryAlert` |
| GET | `/api/alerts/{id}` | `getAlert` |
| POST | `/api/alerts` | `modifyAlerts` |
| POST | `/api/alerts/group/{groupingCondition}/query` | `queryAlertGroups` |
| GET | `/api/alerts/types` | `getAlertTypes` |
| GET | `/api/alerts/contributingsymptoms` | `getAlertContributingSymptoms` |
| DELETE | `/api/alerts/bulk` | `deleteCanceledAlerts` |
| GET / POST | `/api/alerts/{id}/notes` | `getAlertNotes` / `addAlertNote` |
| GET / DELETE | `/api/alerts/{id}/notes/{noteId}` | `getAlertNote` / `deleteAlertNote` |
| POST | `/api/alerts/notes/query` | `queryAlertNotes` |

`GET /api/alerts` takes `id[]`, `resourceId[]`, `page`, `pageSize` — deliberately thin. For
anything selective use `POST /api/alerts/query` (`alert-query` body, from `RAW9.1`):

`activeOnly`, `alertId[]`, `alertName`, `alertDefinitionId[]`, `alertCriticality[]`,
`alertStatus[]`, `alertControlState[]`, `alertImpact[]`,
`alertTypeSubtype[]` (`{ type (required, int), subtype[] (int) }`),
`startTimeRange` / `updateTimeRange` / `cancelTimeRange` (each `{ startTime, endTime }`, epoch
ms), `resourceKind`, `includeChildrenResources`, `resource-query` (the full `resource-query`
object — you can scope alerts by any resource filter), `groupId`,
`groupingCondition` (`GROUP_BY_ALERT_DEFINITION | GROUP_BY_RESOURCE_KIND |
GROUP_BY_CRITICALITY | GROUP_BY_TIME | GROUP_BY_SCOPE`), `compositeOperator` (`AND | OR`),
`userId`, `userName`, `extractOwnerName`. Pagination via `?page=` / `?pageSize=`.

That embedded `resource-query` is the useful part: "all critical alerts on VMs in this cluster
whose CPU demand exceeded X" is one call, not two.

> **Destructive.** `DELETE /api/alerts/bulk` (`deleteCanceledAlerts`) removes cancelled alert
> records permanently. It is a housekeeping operation, not a way to dismiss active alerts.

### Alert plugins and notification rules

`/api/alertplugins` — 11 operations, `/api/notifications` — 10 operations, both
**spec-confirmed (9.0)** and unchanged at 9.1. These are the outbound side (email, SNMP,
webhook, network share targets and the rules that route alerts to them):
`getAlertPluginsOfType`, `createAlertPlugin`, `updateAlertPlugin`, `patchAlertPlugin`,
`deleteAlertPlugin`, `getAlertPluginInstance`, `getAlertPluginTypes`,
`getAlertPluginTypeWithId`, `modifyAlertPluginState` (PUT `/{pluginId}/enable/{enabled}`),
`getRulesOfPlugin`, `testAlertPlugin`; and `getAllNotificationRules`,
`createNotificationPluginRule`, `updateNotificationPluginRule`, `deleteNotificationPluginRules`,
`getNotificationRule`, plus the five `/api/notifications/templates` operations.

`testAlertPlugin` before enabling a rule — it is the only pre-flight on this path.

---

## Alert definitions, symptoms and recommendations

### Alert definitions — 8 operations, **spec-confirmed (9.0)**

| Method | Path | operationId |
|---|---|---|
| GET | `/api/alertdefinitions` | `getAlertDefinitions` |
| POST | `/api/alertdefinitions` | `createAlertDefinition` |
| PUT | `/api/alertdefinitions` | `updateAlertDefinition` |
| POST | `/api/alertdefinitions/query` | `queryAlertDefinitions` |
| GET | `/api/alertdefinitions/{id}` | `getAlertDefinitionById` |
| DELETE | `/api/alertdefinitions/{id}` | `deleteAlertDefinition` |
| PUT | `/api/alertdefinitions/{id}/enable` | `enableAlertDefinitionInPolicies` |
| PUT | `/api/alertdefinitions/{id}/disable` | `disableAlertDefinitionInPolicies` |

Note the two suffixed operations act **in policies** — enabling a definition is a policy-scoped
act, not a global toggle. `/api/policies` (13 operations, **spec-confirmed (9.0)**) is where
that scoping lives.

`alert-definition` body (`RAW9.1`): `name` (required), `adapterKindKey` (required),
`resourceKindKey` (required), `states[]` (required), `description`, `id`, `type` (int),
`subType` (int), `waitCycles`, `cancelCycles`, `forVCDTenants`.

Each `alert-definition-state`: `base-symptom-set` (required, `OneOfSymptomSet`),
`impact` (required: `impactType` = `BADGE`, `detail` required),
`severity` (required: `UNKNOWN | NONE | INFORMATION | WARNING | IMMEDIATE | CRITICAL | AUTO`),
`recommendationPriorityMap`.

`alert-definition-query` body: `ids[]`, `adapterKinds[]`, `resourceKinds[]`. Plus `?page=`,
`?pageSize=`.

> **Changes what the system alerts on.** Creating, updating or deleting an alert definition
> changes production alerting for every resource of that kind under the applicable policy. A
> deleted definition takes its historical association with it. Verify scope via `/api/policies`
> before writing.

### Symptom definitions — 5, symptoms — 2. **Spec-confirmed (9.0)**

`getSymptomDefinitions`, `createSymptomDefinition`, `updateSymptomDefinition`,
`getSymptomDefinitionByKey`, `deleteSymptomDefinition`; `getSymptoms`, `querySymptoms`
(`POST /api/symptoms/query`).

Symptoms are the conditions an alert definition's `base-symptom-set` composes. Build the symptom
definition first; a definition referencing a nonexistent symptom set will not behave.

### Recommendations — 5. **Spec-confirmed (9.0)**

`getRecommendations`, `createRecommendation`, `updateRecommendation`, `getRecommendationById`,
`deleteRecommendation`. Referenced from an alert-definition state via
`recommendationPriorityMap`.

---

## Reports and report schedules

### Reports — 5 operations, **spec-confirmed (9.0)**

| Method | Path | operationId |
|---|---|---|
| GET | `/api/reports` | `getReports` |
| POST | `/api/reports` | `createReport` |
| GET | `/api/reports/{id}` | `getReport` |
| DELETE | `/api/reports/{id}` | `deleteReport` |
| GET | `/api/reports/{id}/download` | `downloadReport` |

`GET /api/reports` filters: `name[]`, `subject[]`, `status[]`, `resourceId[]`, `page`,
`pageSize`.

`POST /api/reports` body (`report`): `reportDefinitionId` (**required**), `resourceId`
(**required**), `name`, `description`, `subject[]`, `owner`, `publish` (boolean), `status`,
`completionTime`, `traversalSpec` (`{ name (required), rootAdapterKindKey,
rootResourceKindKey, adapterInstanceAssociation, description }`).

Generation is asynchronous: `POST` creates the job, then poll `GET /api/reports/{id}` until
`status` is terminal, then `GET /api/reports/{id}/download`. You cannot download before the
report completes.

### Report definitions and schedules — 7 operations, **spec-confirmed (9.0)**

| Method | Path | operationId |
|---|---|---|
| GET | `/api/reportdefinitions` | `getReportDefinitions` |
| GET | `/api/reportdefinitions/{id}` | `getReportDefinition` |
| GET | `/api/reportdefinitions/{id}/schedules` | `getReportSchedules` |
| POST | `/api/reportdefinitions/{id}/schedules` | `createReportSchedule` |
| PUT | `/api/reportdefinitions/{id}/schedules` | `updateReportSchedule` |
| GET | `/api/reportdefinitions/{id}/schedules/{scheduleId}` | `getReportSchedule` |
| DELETE | `/api/reportdefinitions/{id}/schedules/{scheduleId}` | `deleteSchedule` |

There is no create/update/delete for report *definitions* over this API — only read. Definitions
are authored in the product; the API generates and schedules against them.

`report-schedule` body (`RAW9.1`), required fields marked:

| Field | Type | Notes |
|---|---|---|
| `reportDefinitionId` | string | **required** |
| `startDate` | string | **required** |
| `recurrence` | integer | **required** |
| `dayOfTheMonth` | integer | **required** — required even for non-monthly schedules per the schema |
| `relativePath` | `array<string>` | **required** — output path on the share target |
| `reportScheduleType` | enum | `UNKNOWN \| DAILY \| WEEKLY \| MONTHLY \| YEARLY` |
| `daysOfTheWeek` | `array<string>` | |
| `weekOfMonth` | enum | `UNKNOWNN \| FIRST \| SECOND \| THIRD \| FOURTH \| LAST` — note the typo `UNKNOWNN`, which is how it appears in the spec |
| `startHour` / `startMinute` | integer | |
| `resourceId` | `array<string>` | |
| `emailAddresses` / `emailCcAddresses` / `emailBccAddresses` | `array<string>` | |
| `emailPluginId` | string | an `/api/alertplugins` instance |
| `networkSharePluginId` | string | an `/api/alertplugins` instance |
| `traversalSpec` | object | as on `report` |
| `id` | string | |

`POST` and `PUT` also accept a header **`X-Ops-API-Timezone`** — a custom header for the
timezone the schedule times are interpreted in. Omitting it leaves the interpretation to the
server default, which is the usual cause of a report arriving at the wrong hour.

The `emailPluginId` / `networkSharePluginId` must reference plugin instances that already exist
(P-check: `GET /api/alertplugins`), otherwise the schedule is created but delivers nowhere.

---

## Custom groups

9 operations, **spec-confirmed (9.0)**, identical at 9.1. The dossier flagged the literal paths
as UNVERIFIED (expecting `/suite-api/api/resources/groups`); `SPEC9.0` confirms them exactly.

| Method | Path | operationId |
|---|---|---|
| GET | `/api/resources/groups` | `getCustomGroups` |
| POST | `/api/resources/groups` | `createCustomGroup` |
| PUT | `/api/resources/groups` | `modifyCustomGroup` |
| GET | `/api/resources/groups/{groupId}` | `getCustomGroup` |
| DELETE | `/api/resources/groups/{groupId}` | `deleteCustomGroup` |
| GET | `/api/resources/groups/{groupId}/members` | `getCustomGroupMembers` |
| GET | `/api/resources/groups/types` | `getGroupTypes` |
| POST | `/api/resources/groups/types` | `addGroupType` |
| DELETE | `/api/resources/groups/types/{key}` | `deleteGroupType` |

`GET /api/resources/groups` takes `groupId[]` and `includePolicy` (boolean — the policy id
applied to the group is *not* returned unless you ask).

`custom-group` body:

| Field | Type | Notes |
|---|---|---|
| `resourceKey` | `resource-key` | **required** — `name` (required), `adapterKindKey` (required), `resourceKindKey` (required), `resourceIdentifiers[]`, `extension` |
| `membershipDefinition` | `custom-group-membership` | **required** — `rules[]` (`membership-rule-group`), `includedResources[]`, `excludedResources[]`, `custom-group-properties[]` |
| `autoResolveMembership` | boolean | dynamic vs static membership |
| `policy` | string | policy id to apply |
| `id` | string | |

Two things to get right: the group's `resourceKindKey` must be a group type that exists
(`GET /api/resources/groups/types` first — `addGroupType` if not), and `autoResolveMembership`
decides whether `rules[]` are re-evaluated or `includedResources[]` is the fixed roster.
Verify the outcome with `GET /api/resources/groups/{groupId}/members`, which returns a
`resources` payload — a group whose rules match nothing is created successfully and stays empty.

Custom **profiles** are a separate family, also **spec-confirmed (9.0)**: `getCustomProfiles`,
`createCustomProfile`, `modifyCustomProfile`, `getCustomProfile`, `deleteCustomProfile` under
`/api/resources/profiles`. Custom **datacenters** likewise under `/api/resources/customdatacenters`
(`getCustomDatacenters`, `createCustomDatacenter`, `updateCustomDatacenter`,
`getCustomDatacenter`, `deleteCustomDatacenters`).

---

## Supporting surfaces

All **spec-confirmed (9.0)**; counts from `SPEC9.0`. Each is unchanged at 9.1 unless noted in
`../deltas.md`.

| Tree | Ops | Key operations |
|---|---|---|
| `/api/adapterkinds` | 8 | `getAdapterTypes`, `getResourceTypesForAdapterType`, `getResourceTypeForAdapterType`, `getResourceTypeAttributesForAdapterType`, `getResourceTypePropertiesForAdapterType` |
| `/api/adapters` | 13 | `enumerateAdapterInstances`, `createAdapterInstance`, `testConnection`, `getResourcesOfAdapterInstance`, `startMonitoringResourcesOfAdapterInstance` |
| `/api/collectors` | 4 | `getCollectors`, `getAdaptersOnCollector`, `enableDataPersistence`, `disableDataPersistence` |
| `/api/collectorgroups` | 7 | `getCollectorGroups`, `createCollectorGroup`, `addCollectorToCollectorGroup` |
| `/api/credentials` | 8 | `getCredentials`, `createCredential`, `getAdapterInstancesUsingCredential`, `getResourcesUsingCredential` |
| `/api/policies` | 13 | policy CRUD and assignment — the scope for alert definitions and thresholds |
| `/api/tasks` | 2 | `getTasksStatus`, `getTaskStatus` — generic async task polling |
| `/api/actions`, `/api/actiondefinitions` | 3 + 1 | `getAllActions`, `populateAction`, `performAction`, `getActionStatus` — remediation actions |
| `/api/events` | 4 | `pushEvent`, `pushEvents` (+ adapter-kind variants) — inbound events |
| `/api/maintenanceschedules` | 4 | schedule-based alert suppression |
| `/api/deployment` | 8 | `getNodeStatus`, `getServicesInfo`, `getGlobalSettings`, `updateGlobalSettingValue` |
| `/api/versions` | 2 | `getSupportedApplicationVersions`, `getCurrentVersionOfServer` |
| `/api/content` | 10 | content import/export — 5 of the 10 are deprecated (see below) |
| `/api/audit` | 1 | `getSystemAudit` |
| `/api/solutions` | 3 | `getSolutions`, `getSolution`, `getAdapterKindsForSolution` |
| `/api/costconfig` | 2 | cost configuration |
| `/api/chargeback` | 14 | bills (`generateBills`, `getBillSummary`, `getBill`, `deleteBill`), reports, and per-definition schedules — **present at 9.0**, contrary to a common claim |
| `/api/optimization` | 10 | the whole `optimization/workloadplacement/*` family — **present at 9.0** |
| `/api/logs` | 7 | `getLogConfigurationsByType`, `createOrUpdateLogConfigurations`, log forwarding enable/disable — appliance log config, *not* log search |
| `/api/integrations` | 19 | vCenter and VCF integration registration |
| `/api/applications` | 25 | application monitoring / agents |

`/api/logs` here is VCF Operations' own log configuration and forwarding. Log *search and query*
is a different product — see `vcf-operations-logs-and-networks`.

---

## Worked example — a resource's CPU metrics over a time range

Goal: average CPU demand for the VM `web-prod-01`, hourly buckets, over the last 24 hours,
against a 9.0 appliance. Every field below is from `SPEC9.0` (paths, methods, operationIds) and
`RAW9.1` (field names — see the inheritance note at the top).

**1 — Acquire a token.** `acquireToken`, **spec-confirmed (9.0)**.

```http
POST /suite-api/api/auth/token/acquire HTTP/1.1
Host: ops.example.com
Content-Type: application/json
Accept: application/json

{
  "username": "svc-metrics",
  "password": "<password>",
  "authSource": "LOCAL"
}
```

```json
{
  "token": "8f868cca-27cc-43d6-a838-c5467e73ec45::77cea9b2-1e87-490e-b626-e878beeaa23b",
  "validity": 1470421325035,
  "expiresAt": "Friday, August 5, 2016 6:22:05 PM UTC",
  "roles": []
}
```

Every subsequent call carries:

```
Authorization: OpsToken 8f868cca-27cc-43d6-a838-c5467e73ec45::77cea9b2-1e87-490e-b626-e878beeaa23b
Accept: application/json
```

Six hours from now this stops working. On a 9.1 appliance `Authorization: Bearer <vcf-sso-token>`
would also be accepted; on 9.0 it is not.

**2 — Resolve the name to an identifier.** `getMatchingResources`, **spec-confirmed (9.0)**.
The GET form would work for one exact name; the POST form is used here because it also lets you
constrain the resource kind, which avoids matching a same-named object of another kind.

```http
POST /suite-api/api/resources/query?page=0&pageSize=100 HTTP/1.1

{
  "name": ["web-prod-01"],
  "adapterKind": ["VMWARE"],
  "resourceKind": ["VirtualMachine"]
}
```

Take `identifier` from the returned `resource` — call it `$RID`.

**3 — Confirm it is collecting.** `getResource`, **spec-confirmed (9.0)**. This is P5, and it
is the step people skip.

```http
GET /suite-api/api/resources/$RID HTTP/1.1
```

Require `resourceStatusStates[0].resourceState == "STARTED"` and
`resourceStatusStates[0].resourceStatus == "DATA_RECEIVING"`. If it says `COLLECTOR_DOWN` or
`NO_DATA_RECEIVING`, stop and go to P6 with the `adapterInstanceId` from the same object; note
`monitoringInterval` too, because it sets the finest bucket that can return data.

**4 — Get the exact stat key.** `getStatKeys`, **spec-confirmed (9.0)**. This is P7. Guessing
here is the difference between data and an empty array.

```http
GET /suite-api/api/resources/$RID/statkeys HTTP/1.1
```

Response is `stat-keys` → `stat-key[].key`. Pick the CPU demand key exactly as it appears — the
key namespace is adapter-specific and this file does not assert any literal key string.

**5 — Query the range.** `getStatsForResource`, **spec-confirmed (9.0)**. `begin` and `end` are
epoch **milliseconds**; the values below are the 24 hours ending 2026-07-31T00:00:00Z.

```http
POST /suite-api/api/resources/$RID/stats/query HTTP/1.1
Content-Type: application/json

{
  "statKey": ["<key-from-step-4>"],
  "begin": 1785110400000,
  "end": 1785196800000,
  "rollUpType": "AVG",
  "intervalType": "HOURS",
  "intervalQuantifier": 1,
  "currentOnly": false,
  "dt": false
}
```

Response (`stats-of-resources`):

```json
{
  "values": [
    {
      "resourceId": "$RID",
      "stat-list": {
        "stat": [
          {
            "statKey": { "key": "<key-from-step-4>" },
            "timestamps": [1785114000000, 1785117600000],
            "data": [42.7, 39.1],
            "rollUpType": "AVG",
            "intervalUnit": { "intervalType": "HOURS", "quantifier": 1 }
          }
        ]
      }
    }
  ]
}
```

`timestamps[i]` pairs with `data[i]`.

**6 — If `stat` comes back empty.** In order, and each is one call:

1. `GET /api/resources/$RID/stats/latest` (`getLatestStats`) — data here but not in step 5 means
   the *range* is the problem, not the resource.
2. Re-read `resourceStatus` from step 3.
3. `GET /api/adapters/{adapterId}` (`getAdapterInstance`) — the path parameter is `adapterId`;
   the value is the `adapterInstanceId` read in step 3. Check `lastCollected` and
   `messageFromAdapterInstance`.
4. `GET /api/collectors` (`getCollectors`) — check `state == "UP"` for the collector hosting it.
5. Re-check the key against step 4's list, character for character.

**Same query for many resources at once:** `POST /api/resources/stats/query`
(`getStatsForResources`, **spec-confirmed (9.0)**), same `stat-query` body, with `resourceId`
holding the list and no path id.

**Scale note.** All of the multi-resource stat operations take arrays; none of them documents a
maximum. Batch conservatively and paginate the resource lookup with explicit `pageSize`.

---

## What is not here

**Dashboards.** No dashboard endpoint exists in `SPEC9.0` (370 operations), `SPEC9.1` (504), or
`RAW9.1`. Searching those three for `dashboard` in a path, `operationId` or summary returns
nothing; in `RAW9.1` the string occurs only as the `contentType` value `DASHBOARDS` inside
content-management import/export **examples**. Legacy vROps exposed `/suite-api/api/dashboards`.

> **UNVERIFIED — whether a dashboards API exists undocumented in 9.x.** [DOPS §Gaps item 2]
> Do not construct a `/suite-api/api/dashboards` call. If a user needs one, tell them it is not
> in the published spec for either version and send them to the on-appliance Swagger UI at
> `https://<ops-fqdn>/suite-api/doc/swagger-ui.html` — note the singular `doc`, which is how it
> is printed in the source [DOPS §"On-appliance API discovery"] — which reflects that build.

`/api/content` (10 operations, **spec-confirmed (9.0)**) can move dashboard content as part of
an opaque content bundle. That is content migration, not a dashboard API, and it should not be
offered as a substitute.

**Log search, Networks, real-time metrics.** Out of scope — `vcf-operations-logs-and-networks`.

**Upgrading VCF Operations, depots, bundles, prechecks.** Out of scope — `vcf-lifecycle-upgrade`.

---

## Deprecated operations in 9.0

`SPEC9.0` flags **13** operations `deprecated: true`. `SPEC9.1` flags the **same 13** — nothing
was newly deprecated and nothing un-deprecated between the versions.

| Method | Path | operationId |
|---|---|---|
| PUT | `/api/resources/monitoringstate/start` | `startMonitoringResources` |
| PUT | `/api/resources/monitoringstate/stop` | `stopMonitoringResources` |
| PUT | `/api/resources/{id}/monitoringstate/start` | `startMonitoringResource` |
| PUT | `/api/resources/{id}/monitoringstate/stop` | `stopMonitoringResource` |
| POST | `/api/content/backup` | `backupContent` |
| GET | `/api/content/backup/result` | `downloadBackupContentData` |
| POST | `/api/content/restore` | `restoreContent` |
| GET | `/api/content/restore/result` | `getRestoreContentData` |
| GET | `/api/content/progress` | `getContentProgress` |
| PUT | `/api/applications/vcenter/add` | `addVcenterToConfiguration` |
| PUT | `/api/applications/vcenter/remove` | `removeVcenterFromConfiguration` |
| PUT | `/api/auth/users/{userId}/traversalspecs` | `assignTraversalSpecToUser` |
| PUT | `/api/auth/usergroups/{groupId}/traversalspecs` | `assignTraversalSpecToUserGroup` |

The four monitoring-state operations are the ones most likely to be reached for in monitoring
work. Use the `maintained` operations instead.

> **UNVERIFIED — replacements.** The inventory marks these deprecated but names no successor,
> and `DOPS` does not discuss them. The `maintained` recommendation above is an inference from
> overlapping function, not a documented migration. Confirm against the appliance's own Swagger
> before rewriting automation.
