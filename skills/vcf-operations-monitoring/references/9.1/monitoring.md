# VCF Operations 9.1 — Monitoring Reference

**Scope:** VMware Cloud Foundation Operations 9.1.x, `/suite-api` REST API. Everything here is
`[9.1]` unless explicitly tagged otherwise. Log Management, VCF Operations for Networks and the
real-time metrics API are **out of scope** — see the `vcf-operations-logs-and-networks` skill.

**Sources.**
- `SPEC9.1` = `research/spec-inventory/9.1__vcf-operations.ops.json` — **504 operations**, base
  path `/suite-api`, spec version `9.1.0.0`, from git tag `9.1.0.0` of
  `github.com/vmware/vcf-api-specs`.
- `RAW9.1` = `specifications/vcf-operations/vcf-operations-openapi.json` at the same tag — the
  full OpenAPI 3.0.1 document, source of every field name, enum and query parameter below.
  `servers: [{ "url": "/suite-api" }]`; `security: [{ "Token-based-authorization": [] }]`.
- `SPEC9.0` = `research/spec-inventory/9.0__vcf-operations.ops.json` — 370 operations. Used here
  to state whether an operation also exists at 9.0.
- `DOPS` = `research/vcf-operations.md`.
- `DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md`.

Every path below was checked against `SPEC9.1` and is marked **spec-confirmed (9.1)** with its
`operationId`. Where it also exists at 9.0 that is stated, because it usually does: **134
operations were added and zero removed**, so 9.1 is a strict superset of 9.0 on this API.

> **Documentation-derived, not live-validated.** Nothing here has been run against a VCF
> Operations appliance. Read paths are cheap to try; the write paths — alert definitions, custom
> groups, report schedules, resource deletion, Salt enablement, what-if commits — are not, and
> are flagged where they appear.

---

## Contents

- [Prerequisites](#prerequisites)
  - P1 — A valid token, less than six hours old
  - P2 — The Authorization header form: `OpsToken`, or `Bearer` from VCF SSO
  - P3 — The caller's role permits the operation — role names UNVERIFIED
  - P4 — The resource exists in inventory
  - P5 — The resource is actually collecting
  - P6 — The adapter instance and its cloud proxy are up
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
- [New in 9.1 — diagnostics findings](#new-in-91--diagnostics-findings)
- [New in 9.1 — Salt management](#new-in-91--salt-management)
- [New in 9.1 — what-if scenarios](#new-in-91--what-if-scenarios)
- [New in 9.1 — chargeback additions](#new-in-91--chargeback-additions)
- [New in 9.1 — optimization additions](#new-in-91--optimization-additions)
- [New in 9.1 — logs query configs](#new-in-91--logs-query-configs)
- [New in 9.1 — fleet management](#new-in-91--fleet-management)
- [Worked example — a resource's CPU metrics over a time range](#worked-example--a-resources-cpu-metrics-over-a-time-range)
- [What is not here](#what-is-not-here)
- [Deprecated operations in 9.1](#deprecated-operations-in-91)

---

## Prerequisites

Nothing below this block should be attempted until these are true. Each item states what must
hold, **how to verify it**, and whether 9.0 differs. The failure mode on this API is rarely a
4xx — it is a `200` with an empty payload — so these checks are what turns "the API is broken"
into "the adapter stopped collecting on Tuesday."

### P1 — A valid token, less than six hours old `[9.1]`

**Must be true:** every call carries a token from
`POST /suite-api/api/auth/token/acquire` — **spec-confirmed (9.1)**, `acquireToken`; also
present at 9.0.

Request body (`username-password`): `username` (required), `password` (required), `authSource`
(optional; `LOCAL` by default, or the name of an imported LDAP / Active Directory / vIDM / SSO
source) [`RAW9.1`; DOPS §"Token acquisition"].

Response (`auth-token`): `token` (required), `validity` (required, integer), `expiresAt`,
`roles[]`. Token format is `uuid::uuid` [DOPS].

**TTL is six hours** with no refresh — you re-acquire [DOPS]. `POST /api/auth/token/release`
(`releaseToken`) is **spec-confirmed (9.1)** and also present at 9.0. (`DOPS` says from the
prose pages that no release endpoint is documented; the spec inventory contradicts that prose —
trust the spec.)

**How to verify:** `GET /api/auth/currentuser` — **spec-confirmed (9.1)**, `getCurrentUser`,
also at 9.0.

**New at 9.1:** `POST /api/auth/token/exchange` — **spec-confirmed (9.1)**,
`exchangeOpsTokenWithJwtToken`, **absent at 9.0**. Body (`TokenExchangeRequest`):
`serviceKeys[]` (required). Optional `?includeServiceDetails=true` returns the service address
and port. This is how you obtain a downstream-service JWT — e.g. `{"serviceKeys": ["ops-li"]}`
for Log Management, sent onward as `X-JWT-Token`; or a `VCF_VODAP` service key for real-time
metrics, sent onward as `Authorization: Bearer <jwt>` [DOPS §"Token exchange"]. Those downstream
APIs are `vcf-operations-logs-and-networks`' subject, not this skill's.

Also new at 9.1: `GET /api/auth/sources/vidb/well-known-url` — **spec-confirmed (9.1)**,
`getVIDBWellKnownURL`, absent at 9.0 — the OIDC discovery URL for the VCF Identity Broker.

### P2 — The Authorization header form: `OpsToken`, or `Bearer` from VCF SSO `[9.1]`

**Must be true:** the header is one of

```
Authorization: OpsToken <token>            # from POST /api/auth/token/acquire
Authorization: Bearer <token>              # 9.1 only — from VCF SSO
Authorization: vRealizeOpsToken <token>    # legacy form, still supported
Authorization: SSO2Token <SSO_SAML_TOKEN>  # external SSO SAML token
```

[DOPS §"Token acquisition"]. The spec's security scheme is `Token-based-authorization`:
`type: apiKey`, `in: header`, `name: Authorization` — it confirms the header name, not the
prefix; prefixes come from the documentation [`RAW9.1`; DOPS].

**How to verify:** any authenticated GET; missing or invalid credentials return 401/403 [DOPS].

**9.0 difference — this one matters in reverse.** 9.0 accepts `OpsToken`, `vRealizeOpsToken` and
`SSO2Token`, but **not** `Bearer`. Code that relies on the 9.1 `Bearer` path will 401 against a
9.0 appliance.

Auth beyond this — identity sources, VCF SSO, role assignment — belongs to `vcf-foundation`.

### P3 — The caller's role permits the operation — role names UNVERIFIED `[9.1]`

**Must be true:** the account holds a role granting the operation's privileges. Reads need read
privileges; writes (alert definitions, custom groups, report schedules, resource deletion, Salt
enablement) need administrative privileges.

> **UNVERIFIED.** Neither `SPEC9.1`, `RAW9.1` nor `DOPS` enumerates built-in role names, and
> `RAW9.1` carries no role-name enum. The commonly-cited pair **Administrator** and **ReadOnly**
> is **not attested** by any source available here, and neither is the privilege required by any
> specific operation. Do not assert a role-to-operation mapping — determine it per deployment.

**How to verify (identical in both versions):**

| Call | operationId | Status |
|---|---|---|
| `GET /api/auth/roles` (optional `?roleName=`) | `getRoles` | **spec-confirmed (9.1)**, also 9.0 |
| `GET /api/auth/roles/{roleName}` | `getRoleByName` | **spec-confirmed (9.1)**, also 9.0 |
| `GET /api/auth/roles/{roleName}/privileges` | `getRolePrivileges` | **spec-confirmed (9.1)**, also 9.0 |
| `GET /api/auth/privileges` | `getAvailablePrivileges` | **spec-confirmed (9.1)**, also 9.0 |
| `GET /api/auth/privilegegroups` | `getAvailablePrivilegeGroups` | **spec-confirmed (9.1)**, also 9.0 |
| `GET /api/auth/currentuser/permissions` | `getAssignedRolePermissionsForCurrentUser` | **spec-confirmed (9.1)**, also 9.0 |
| `GET /api/auth/currentuser/roles/{roleName}/privileges` | `getCurrentUserRolePrivileges` | **spec-confirmed (9.1)**, also 9.0 |

> **Correction worth making on contact.** An earlier prose pass claimed `/auth/roles` and
> `/auth/privileges` were 9.1-only. **They are not.** `SPEC9.0` contains **57** operations under
> `/api/auth`, including every one in the table above. `SPEC9.1` contains **59** — the same 57
> plus `getVIDBWellKnownURL` and `exchangeOpsTokenWithJwtToken`. What 9.1 genuinely adds is a
> *separate, parallel* fleet-wide IAM tree at `/api/fleet-management/iam/*` (70 operations),
> which does not replace `/api/auth/*`.

### P4 — The resource exists in inventory `[9.1]`

**Must be true:** you have the resource's `identifier` (a UUID). Names are not identifiers, and
`GET /api/resources?name=` supports only a **single** element despite being an array parameter
[`RAW9.1`].

**How to verify:** `GET /api/resources?name=<exact-name>` (`getResources`) or
`POST /api/resources/query` (`getMatchingResources`) — both **spec-confirmed (9.1)**, both at
9.0. Read `identifier` off the returned `resource`.

**9.0 difference:** none.

### P5 — The resource is actually collecting `[9.1]`

**Must be true:** the resource is not merely discovered but receiving data. This is the single
most common cause of an empty stats response.

**How to verify:** `GET /api/resources/{id}` — **spec-confirmed (9.1)**, `getResource`, also at
9.0 — and inspect `resourceStatusStates[]` [`RAW9.1`]:

- `resourceState` — `STOPPED | STARTING | STARTED | STOPPING | UPDATING | FAILED | MAINTAINED |
  MAINTAINED_MANUAL | REMOVING | NOT_EXISTING | NONE | UNKNOWN`. You want `STARTED`.
- `resourceStatus` — `NONE | ERROR | UNKNOWN | DOWN | DATA_RECEIVING | OLD_DATA_RECEIVING |
  NO_DATA_RECEIVING | NO_PARENT_MONITORING | COLLECTOR_DOWN`. You want `DATA_RECEIVING`.
  `OLD_DATA_RECEIVING` means the series stops short of "now"; `COLLECTOR_DOWN` sends you to P6.
- `statusMessage` — free text, usually names the actual fault.
- `adapterInstanceId` — the adapter to check in P6.

Also on `resource`: `monitoringInterval` / `monitoringIntervalSeconds` (a 5-minute sampling
interval means a 10-minute window yields ~2 points — a legitimate reason a query "looks empty"),
and `badges[]` with `type` in `ANOMALY | CAPACITY_REMAINING | COMPLIANCE | DENSITY | EFFICIENCY |
FAULT | HEALTH | RISK | STRESS | TIME_REMAINING | TIME_REMAINING_WHATIF | RECLAIMABLE_CAPACITY |
WORKLOAD` and `color` in `GREEN | YELLOW | ORANGE | RED | GREY`.

A resource may also be deliberately excluded: `PUT /api/resources/{id}/maintained`
(`markResourceAsBeingMaintained`) and `PUT /api/resources/maintained`
(`markResourcesAsBeingMaintained`) — both **spec-confirmed (9.1)**, both at 9.0 — put it in
`MAINTAINED` and suppress alerting. Check that before concluding a collection fault.

**9.0 difference:** none.

### P6 — The adapter instance and its cloud proxy are up `[9.1]`

**Must be true:** the adapter instance owning the resource is collecting, and its **cloud proxy**
is reachable. (In 9.0 this component is called the *VCF Operations collector*; 9.1 renames it
**cloud proxy** [DOPS §"Renames"; DELTA]. The API path is `/api/collectors` in both, and the
type enum already reads `CLOUD_PROXY` in both.)

**How to verify** — all **spec-confirmed (9.1)**, all present at 9.0:

| Call | operationId | What to read |
|---|---|---|
| `GET /api/adapters?adapterKindKey=` | `enumerateAdapterInstances` | list of `adapter-instance` |
| `GET /api/adapters/{adapterId}` | `getAdapterInstance` | one instance |
| `GET /api/adapters/{adapterId}/resources` | `getResourcesOfAdapterInstance` | what it owns |
| `POST /api/adapters/testConnection` | `testConnection` | live connectivity probe |
| `GET /api/collectors?host=` | `getCollectors` | list of `collector` |
| `GET /api/collectors/{id}/adapters` | `getAdaptersOnCollector` | adapters per collector |

On `adapter-instance`: `lastCollected`, `lastHeartbeat` (epoch ms), `numberOfMetricsCollected`,
`numberOfResourcesCollected`, `messageFromAdapterInstance` (the human-readable failure),
`monitoringInterval`, `collectorId`, `collectorGroupId`, `credentialInstanceId`,
`adapter-certificates[]`.

On `collector`: `state` — `DOWN | UP`; `type` — `INTERNAL | CLOUD_PROXY | OTHER |
UNIFIED_CLOUD_PROXY`; `lastHeartbeat`; `local`; `dataPersistenceEnabled`; `hostName`;
`adapterInstanceIds[]`.

A stale `lastCollected`, a populated `messageFromAdapterInstance`, or a collector in `DOWN`
explains an empty stats result more often than the query being wrong.

**New at 9.1 — cloud proxy certificate renewal** (four operations, all **absent at 9.0**):

| Method | Path | operationId |
|---|---|---|
| POST | `/api/collectors/{id}/certificates/renew` | `renewCloudProxyCertificate` |
| GET | `/api/collectors/{id}/certificates/renew/status` | `getCollectorCertificateRenewStatus` |
| POST | `/api/collectorgroups/{id}/certificates/renew` | `renewCollectorGroupCertificate` |
| GET | `/api/collectorgroups/{id}/certificates/renew/status` | `getCollectorGroupCertificateRenewalStatus` |

> **Disruptive.** Certificate renewal on a cloud proxy interrupts collection for the resources
> behind it. Poll the matching `/status` operation; do not fire and forget.

An expired cloud-proxy certificate is a plausible cause of `COLLECTOR_DOWN` at 9.1 that has no
9.0 analogue in this API.

### P7 — The stat key exists for that resource kind `[9.1]`

**Must be true:** the `statKey` is one this resource actually publishes. A wrong key returns an
empty series, not an error — the highest-yield check in this file.

**How to verify** — all **spec-confirmed (9.1)**, all present at 9.0:

| Call | operationId | Scope |
|---|---|---|
| `GET /api/resources/{id}/statkeys` | `getStatKeys` | keys for one resource |
| `GET /api/resources/statkeys` | `getStatKeysOfResources` | keys across resources |
| `GET /api/adapterkinds/{adapterKindKey}/resourcekinds/{resourceKindKey}/statkeys` | `getResourceTypeAttributesForAdapterType` | keys for a whole resource kind |

Response is `stat-keys` → `stat-key[]` → `key` (string, required).

**New at 9.1:**
`GET /api/adapterkinds/{adapterKindKey}/resourcekinds/{resourceKindKey}/identifiers` —
**spec-confirmed (9.1)**, `getResourceIdentifiersDetails`, **absent at 9.0**. It returns the
resource *identifier* fields for a kind, which is what you need to construct a `resource-key`
when creating a resource or a custom group — not stat keys.

### P8 — The time range is epoch milliseconds and inside retention — retention UNVERIFIED `[9.1]`

**Must be true:** `begin` and `end` are integers, milliseconds since the Unix epoch, and the
window falls inside the deployment's retention.

**How to verify:** `RAW9.1` describes `begin` as "the beginning date as a long value" and `end`
correspondingly; both `integer`, both optional. Bucket granularity comes from `rollUpType`
(`SUM | AVG | MIN | MAX | NONE | LATEST | COUNT`), `intervalType`
(`HOURS | MINUTES | SECONDS | DAYS | WEEKS | MONTHS | YEARS`) and `intervalQuantifier`.

> **UNVERIFIED.** Neither `SPEC9.1`, `RAW9.1` nor `DOPS` states the default retention period,
> the roll-up tiering, or the behaviour when `begin` predates retention. Do not quote a
> retention figure. Check the deployment's policy settings, or start narrow and widen.

One call that isolates the problem: `GET /api/resources/{id}/stats/latest` (`getLatestStats`,
**spec-confirmed (9.1)**). Data there but not in the ranged query means the range is the fault.

**9.0 difference:** none.

### P9 — Things this file could not verify `[9.1]`

- **Built-in role names and the role required by each operation** (P3). **UNVERIFIED.**
- **Metric retention and roll-up tiering** (P8). **UNVERIFIED.**
- **Any dashboards API.** Absent from `SPEC9.0`, `SPEC9.1` and `RAW9.1`. See
  [What is not here](#what-is-not-here). **UNVERIFIED.**
- **Rate limits / throttling.** Nothing in the spec or dossier. **UNVERIFIED.**
- **A documented default for `pageSize`.** `DOPS` asserts "`pageSize` default 1000, `page`
  0-based"; `RAW9.1` documents both parameters and states no default. The 0-based `page` is
  confirmed by the parameter description; the 1000 default is **UNVERIFIED**. Pass it explicitly.
- **Request/response bodies for the fleet-management OAuth/API-token operations.** The
  operations are spec-confirmed; `DOPS` records that the payload shapes were not retrieved
  [DOPS §Gaps]. `RAW9.1` carries schemas for them, but they are `vcf-foundation`'s subject, not
  reproduced here. **Out of scope rather than unverified.**

---

## Inventory — resources

`/api/resources` carries **66 operations** at 9.1 — the identical count and set as 9.0. Nothing
in this tree changed.

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

All **spec-confirmed (9.1)**, all present at 9.0.

`GET /api/resources` query parameters [`RAW9.1`]: `name[]` (single element only), `regex[]`
(Java regex; mutually exclusive with `name`), `adapterKind[]`, `resourceKind[]`,
`collectorName[]`, `collectorId[]`, `maintenanceScheduleId[]`, `adapterInstanceId[]`,
`recentlyAdded` (seconds since epoch), `resourceState[]`, `resourceStatus[]`, `resourceHealth[]`,
`parentId[]`, `credentialId[]`, `resourceId[]`, `propertyName`, `propertyValue`, `statKey`,
`statKeyLowerBound`, `statKeyUpperBound`, `statKeyInclusive`, `includeRelated`
(`PARENT | CHILD`), `page` (0-based), `pageSize`.

`POST /api/resources/query` body (`resource-query`) takes the same filters as arrays plus
`statConditions` and `propertyConditions`, each a `stat-or-property-condition-query` with
`conditions[]` (required) and `conjunctionOperator` (`AND | OR`), and `resourceTag[]` with
`category` (required) and `name`. Pagination is `?page=` / `?pageSize=`, not in the body.

Use POST when you need more than one name, AND/OR over metric thresholds, or tag filtering.

### Properties

`getResourceProperties` (GET `/api/resources/{id}/properties`), `getResourcePropertiesList`
(GET `/api/resources/properties`), `queryLatestPropertiesOfResources`
(POST `/api/resources/properties/latest/query`), plus four `add*` push operations
(`addProperties`, `addResourcesProperties`, `addResourcesPropertiesUsingAdapterKind`,
`addPropertiesUsingPushAdapterKind`). All **spec-confirmed (9.1)**, all at 9.0.

Properties are string/categorical facts; stats are numeric time series. `propertyName` without
`propertyValue` on `getResources` checks existence.

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

All **spec-confirmed (9.1)**, all at 9.0.

> **Destructive.** `deleteResource` / `deleteResources` remove objects and their history from
> the Operations database. No undo in this API; the object returns only if the adapter
> rediscovers it, and the historical series does not come back. Treat a bulk delete as a change
> requiring approval.

**Deprecated at 9.1 — and already deprecated at 9.0:** the four monitoring-state operations
`PUT /api/resources/monitoringstate/{start,stop}` and
`PUT /api/resources/{id}/monitoringstate/{start,stop}`. Prefer the `maintained` operations.

---

## Stats and metrics

Fifteen operations have `/stats` in their path — **11 read** and **4 push** — all
**spec-confirmed (9.1)** and all present unchanged at 9.0. (Stat *keys* are a separate three
operations; see P7.)

### Reading

| Method | Path | operationId | Use for |
|---|---|---|---|
| GET | `/api/resources/{id}/stats` | `getStatsOfResource` | one resource, ranged, query params |
| POST | `/api/resources/{id}/stats/query` | `getStatsForResource` | one resource, ranged, body |
| GET | `/api/resources/stats` | `getStatsOfResources` | many resources, ranged, query |
| POST | `/api/resources/stats/query` | `getStatsForResources` | many resources, ranged, body |
| GET | `/api/resources/{id}/stats/latest` | `getLatestStats` | most recent sample(s), one |
| GET | `/api/resources/stats/latest` | `getLatestStatsOfResources` | most recent sample(s), many |
| POST | `/api/resources/stats/latest/query` | `queryLatestStatsOfResources` | last N samples, body |
| GET | `/api/resources/{id}/stats/topn` | `getTopNStatsOfResource` | ranking, one |
| GET | `/api/resources/stats/topn` | `getTopNStatsOfResources` | ranking, many |
| GET | `/api/resources/{id}/stats/dt` | `getDTStatsOfResource` | dynamic-threshold series |
| POST | `/api/resources/stats/dt/query` | `getStatsAndDTForResources` | stats + DT together |

**`stat-query` body** (`getStatsForResource`, `getStatsForResources`) [`RAW9.1`]:

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
| `metrics` | boolean | force keys to be treated as metrics |
| `currentOnly` | boolean | skip stats that have stopped updating |
| `wrapStatValues` | boolean | XML-response wrapping only |

The GET forms take exactly the same names as query parameters, plus the path `id`.

**`latest-stat-query` body** (`queryLatestStatsOfResources`): `resourceId[]`, `statKey[]`,
`maxSamples`, `metrics`, `currentOnly`, `wrapStatValues`. Note `maxSamples` here versus
`latestMaxSamples` in `stat-query` — mixing them up silently drops the cap.

**Top-N** (`getTopNStatsOfResources`) additionally requires `topN` (integer, **required**) and
takes `groupBy` (`RESOURCE | STATKEY`, default `RESOURCE`) and `sortOrder`
(`ASCENDING | DESCENDING`, default `ASCENDING`). Its response is `ResourceStatGroupList`, a
different shape from the other stat calls.

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

`timestamps[]` and `data[]` are parallel arrays. An empty `stat-list` with a `200` is the
empty-answer failure mode; walk P4 → P7.

### Writing (push adapter)

`addStats` (POST `/api/resources/{id}/stats`), `addStatsForResources`
(POST `/api/resources/stats`), `addStatsUsingPushAdapterKind`, and
`addStatsForResourcesUsingPushAdapterKind`. All **spec-confirmed (9.1)**, all at 9.0. These push
external metrics in; they are not read paths.

### Super metrics

`/api/supermetrics` — 5 operations, **spec-confirmed (9.1)**, unchanged from 9.0:
`getSuperMetrics`, `createSuperMetric`, `updateSuperMetric`, `getSuperMetric`,
`deleteSuperMetric`.

---

## Alerts

`/api/alerts` — 13 operations, **spec-confirmed (9.1)**, identical set at 9.0.

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

`GET /api/alerts` takes only `id[]`, `resourceId[]`, `page`, `pageSize`. For anything selective
use `POST /api/alerts/query` (`alert-query` body, [`RAW9.1`]):

`activeOnly`, `alertId[]`, `alertName`, `alertDefinitionId[]`, `alertCriticality[]`,
`alertStatus[]`, `alertControlState[]`, `alertImpact[]`,
`alertTypeSubtype[]` (`{ type (required, int), subtype[] (int) }`),
`startTimeRange` / `updateTimeRange` / `cancelTimeRange` (each `{ startTime, endTime }`, epoch
ms), `resourceKind`, `includeChildrenResources`, `resource-query` (the full `resource-query`
object), `groupId`, `groupingCondition` (`GROUP_BY_ALERT_DEFINITION | GROUP_BY_RESOURCE_KIND |
GROUP_BY_CRITICALITY | GROUP_BY_TIME | GROUP_BY_SCOPE`), `compositeOperator` (`AND | OR`),
`userId`, `userName`, `extractOwnerName`. Pagination via `?page=` / `?pageSize=`.

The embedded `resource-query` is the useful part: "all critical alerts on VMs in this cluster
whose CPU demand exceeded X" is one call, not two.

> **Destructive.** `DELETE /api/alerts/bulk` (`deleteCanceledAlerts`) permanently removes
> cancelled alert records. It is housekeeping, not a way to dismiss active alerts.

### Alert plugins and notification rules

`/api/alertplugins` — 11 operations; `/api/notifications` — 10. Both **spec-confirmed (9.1)**
and unchanged from 9.0. Outbound targets (email, SNMP, webhook, network share) and the rules
routing alerts to them: `getAlertPluginsOfType`, `createAlertPlugin`, `updateAlertPlugin`,
`patchAlertPlugin`, `deleteAlertPlugin`, `getAlertPluginInstance`, `getAlertPluginTypes`,
`getAlertPluginTypeWithId`, `modifyAlertPluginState`, `getRulesOfPlugin`, `testAlertPlugin`; and
`getAllNotificationRules`, `createNotificationPluginRule`, `updateNotificationPluginRule`,
`deleteNotificationPluginRules`, `getNotificationRule`, plus five
`/api/notifications/templates` operations.

`testAlertPlugin` before enabling a rule — it is the only pre-flight on this path.

Distinct from these, and **new at 9.1**: the five `/api/chargeback/notifications/rules`
operations — see [chargeback additions](#new-in-91--chargeback-additions).

---

## Alert definitions, symptoms and recommendations

### Alert definitions — 8 operations, **spec-confirmed (9.1)**, all at 9.0

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

The two suffixed operations act **in policies** — enabling a definition is policy-scoped, not a
global toggle. `/api/policies` (13 operations, **spec-confirmed (9.1)**, all at 9.0) is where
that scoping lives.

`alert-definition` body [`RAW9.1`]: `name` (required), `adapterKindKey` (required),
`resourceKindKey` (required), `states[]` (required), `description`, `id`, `type` (int),
`subType` (int), `waitCycles`, `cancelCycles`, `forVCDTenants`.

Each `alert-definition-state`: `base-symptom-set` (required, `OneOfSymptomSet`), `impact`
(required: `impactType` = `BADGE`, `detail` required), `severity` (required:
`UNKNOWN | NONE | INFORMATION | WARNING | IMMEDIATE | CRITICAL | AUTO`),
`recommendationPriorityMap`.

`alert-definition-query` body: `ids[]`, `adapterKinds[]`, `resourceKinds[]`; plus `?page=`,
`?pageSize=`.

> **Changes what the system alerts on.** Creating, updating or deleting an alert definition
> changes production alerting for every resource of that kind under the applicable policy, and a
> deleted definition takes its historical association with it. Verify scope via `/api/policies`
> before writing.

### Symptom definitions — 5, symptoms — 2. **Spec-confirmed (9.1)**, all at 9.0

`getSymptomDefinitions`, `createSymptomDefinition`, `updateSymptomDefinition`,
`getSymptomDefinitionByKey`, `deleteSymptomDefinition`; `getSymptoms`, `querySymptoms`.
Symptoms are what an alert definition's `base-symptom-set` composes — build them first.

### Recommendations — 5. **Spec-confirmed (9.1)**, all at 9.0

`getRecommendations`, `createRecommendation`, `updateRecommendation`, `getRecommendationById`,
`deleteRecommendation`. Referenced from an alert-definition state via
`recommendationPriorityMap`.

---

## Reports and report schedules

### Reports — 5 operations, **spec-confirmed (9.1)**, all at 9.0

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
(**required**), `name`, `description`, `subject[]`, `owner`, `publish`, `status`,
`completionTime`, `traversalSpec` (`{ name (required), rootAdapterKindKey,
rootResourceKindKey, adapterInstanceAssociation, description }`).

Generation is asynchronous: `POST` creates the job, poll `GET /api/reports/{id}` until `status`
is terminal, then `GET /api/reports/{id}/download`.

### Report definitions and schedules — 7 operations, **spec-confirmed (9.1)**, all at 9.0

| Method | Path | operationId |
|---|---|---|
| GET | `/api/reportdefinitions` | `getReportDefinitions` |
| GET | `/api/reportdefinitions/{id}` | `getReportDefinition` |
| GET | `/api/reportdefinitions/{id}/schedules` | `getReportSchedules` |
| POST | `/api/reportdefinitions/{id}/schedules` | `createReportSchedule` |
| PUT | `/api/reportdefinitions/{id}/schedules` | `updateReportSchedule` |
| GET | `/api/reportdefinitions/{id}/schedules/{scheduleId}` | `getReportSchedule` |
| DELETE | `/api/reportdefinitions/{id}/schedules/{scheduleId}` | `deleteSchedule` |

There is no create/update/delete for report *definitions* over this API — read only. Definitions
are authored in the product; the API generates and schedules against them.

`report-schedule` body [`RAW9.1`], required fields marked:

| Field | Type | Notes |
|---|---|---|
| `reportDefinitionId` | string | **required** |
| `startDate` | string | **required** |
| `recurrence` | integer | **required** |
| `dayOfTheMonth` | integer | **required** — per the schema, required even for non-monthly types |
| `relativePath` | `array<string>` | **required** — output path on the share target |
| `reportScheduleType` | enum | `UNKNOWN \| DAILY \| WEEKLY \| MONTHLY \| YEARLY` |
| `daysOfTheWeek` | `array<string>` | |
| `weekOfMonth` | enum | `UNKNOWNN \| FIRST \| SECOND \| THIRD \| FOURTH \| LAST` — the typo `UNKNOWNN` is how it appears in the spec |
| `startHour` / `startMinute` | integer | |
| `resourceId` | `array<string>` | |
| `emailAddresses` / `emailCcAddresses` / `emailBccAddresses` | `array<string>` | |
| `emailPluginId` | string | an `/api/alertplugins` instance |
| `networkSharePluginId` | string | an `/api/alertplugins` instance |
| `traversalSpec` | object | as on `report` |
| `id` | string | |

`POST` and `PUT` also accept the header **`X-Ops-API-Timezone`** — the timezone the schedule
times are interpreted in. Omitting it leaves interpretation to the server default, the usual
cause of a report landing at the wrong hour.

`emailPluginId` / `networkSharePluginId` must reference existing plugin instances
(`GET /api/alertplugins`), or the schedule is created but delivers nowhere.

**Chargeback has its own parallel schedule family**, present at 9.0 and unchanged at 9.1:
`GET|POST|PUT /api/chargeback/reportdefinitions/{id}/schedules` and
`GET|DELETE /api/chargeback/reportdefinitions/{id}/schedules/{scheduleId}`
(`getReportSchedulesById`, `createReportScheduleById`, `updateReportScheduleById`,
`getReportScheduleById`, `deleteScheduleById`). Do not confuse the two trees — the operationIds
differ by an `ById` suffix precisely because the paths collide conceptually.

---

## Custom groups

9 operations, **spec-confirmed (9.1)**, identical at 9.0. The dossier flagged the literal paths
as UNVERIFIED (expecting `/suite-api/api/resources/groups`); the spec inventories confirm them
exactly, in both versions.

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

`GET /api/resources/groups` takes `groupId[]` and `includePolicy` (boolean — the applied policy
id is *not* returned unless you ask).

`custom-group` body [`RAW9.1`]:

| Field | Type | Notes |
|---|---|---|
| `resourceKey` | `resource-key` | **required** — `name` (required), `adapterKindKey` (required), `resourceKindKey` (required), `resourceIdentifiers[]`, `extension` |
| `membershipDefinition` | `custom-group-membership` | **required** — `rules[]` (`membership-rule-group`), `includedResources[]`, `excludedResources[]`, `custom-group-properties[]` |
| `autoResolveMembership` | boolean | dynamic vs static membership |
| `policy` | string | policy id to apply |
| `id` | string | |

Two things to get right: the group's `resourceKindKey` must be a group type that exists
(`GET /api/resources/groups/types`, `addGroupType` if not), and `autoResolveMembership` decides
whether `rules[]` are re-evaluated or `includedResources[]` is the fixed roster. Verify with
`GET /api/resources/groups/{groupId}/members` (returns a `resources` payload) — a group whose
rules match nothing is created successfully and stays empty.

Custom **profiles** (`/api/resources/profiles`) and custom **datacenters**
(`/api/resources/customdatacenters`) are separate families, both **spec-confirmed (9.1)** and
both present at 9.0.

---

## Supporting surfaces

All **spec-confirmed (9.1)**; counts from `SPEC9.1`, with the 9.0 count where it differs.

| Tree | 9.1 ops | 9.0 ops | Key operations |
|---|---|---|---|
| `/api/adapterkinds` | 9 | 8 | `getAdapterTypes`, `getResourceTypesForAdapterType`, `getResourceTypeAttributesForAdapterType`; **+1 new**: `getResourceIdentifiersDetails` |
| `/api/adapters` | 13 | 13 | `enumerateAdapterInstances`, `createAdapterInstance`, `testConnection`, `getResourcesOfAdapterInstance` |
| `/api/collectors` | 6 | 4 | `getCollectors`, `getAdaptersOnCollector`, data-persistence toggles; **+2 new**: certificate renewal |
| `/api/collectorgroups` | 9 | 7 | `getCollectorGroups`, `createCollectorGroup`; **+2 new**: certificate renewal |
| `/api/credentials` | 8 | 8 | `getCredentials`, `getAdapterInstancesUsingCredential`, `getResourcesUsingCredential` |
| `/api/policies` | 13 | 13 | policy CRUD and assignment — scope for alert definitions and thresholds |
| `/api/tasks` | 2 | 2 | `getTasksStatus`, `getTaskStatus` |
| `/api/actions` + `/api/actiondefinitions` | 3 + 1 | 3 + 1 | `getAllActions`, `populateAction`, `performAction`, `getActionStatus` |
| `/api/events` | 4 | 4 | `pushEvent`, `pushEvents` (+ adapter-kind variants) |
| `/api/maintenanceschedules` | 4 | 4 | schedule-based alert suppression |
| `/api/deployment` | 8 | 8 | `getNodeStatus`, `getServicesInfo`, `getGlobalSettings`, `updateGlobalSettingValue` |
| `/api/versions` | 2 | 2 | `getSupportedApplicationVersions`, `getCurrentVersionOfServer` |
| `/api/content` | 10 | 10 | content import/export — 5 deprecated in both |
| `/api/audit` | 1 | 1 | `getSystemAudit` |
| `/api/solutions` | 3 | 3 | `getSolutions`, `getAdapterKindsForSolution` |
| `/api/costconfig` | 2 | 2 | cost configuration |
| `/api/integrations` | 27 | 19 | vCenter/VCF registration; **+8 new** under `integrations/services` |
| `/api/applications` | 29 | 25 | application monitoring; **+4 new**: agent certificate renewal |
| `/api/workflows/requests/{requestId}` | 1 | 0 | `getRequestById` — **new at 9.1**, workflow request status |

`/api/integrations/services` (new at 9.1) covers per-component certificate and password
management for integrated services: `getIntegratedServices`, `getVVFCertificates`,
`replaceVVFCertificate`, `getVVFCsrs`, `generateVVFCsr`, `getVVFAccountList`,
`updatePasswordSystem`, `getVvfTaskStatus`. Credential rotation, not monitoring —
`vcf-foundation` territory.

---

## New in 9.1 — diagnostics findings

**2 operations. `/api/diagnostics` has zero operations at 9.0** — this tree is genuinely
9.1-only.

| Method | Path | operationId |
|---|---|---|
| POST | `/api/diagnostics/findings/query` | `queryFindings` |
| POST | `/api/diagnostics/findings/{ruleUuid}/affectedobjects/query` | `queryAffectedObjects` |

Both **spec-confirmed (9.1)**, tag `Findings`. Read-only.

`queryFindings` — query parameters `page`, `pageSize`, `sortBy`
(`RULE_ID | SUBTYPE | SEVERITY | AFFECTED_OBJECTS_COUNT | RESOURCE_ID | RESOURCE_NAME |
CHECK_TIME | OCCURRENCE_TIME | COMPONENT`), `sortOrder` (`ASCENDING | DESCENDING`).
Body `FindingsQuery` → `filter` (`FindingsFilter`): `ruleUuids[]`, `severities[]`,
`categories[]`, `findingTypes[]`, `capabilities[]`, `refreshTypes[]`, `adapterKinds[]`,
`resourceKinds[]`, `resourceIds[]`, `fromOccurrenceTime` (integer, epoch ms).
Response `AuditFindingsResponse`.

`queryAffectedObjects` — path `ruleUuid`; query `page`, `pageSize`. Body `AffectedObjectsQuery`
→ `filter` (`AffectedObjectsFilter`): `resourceIds[]`, `fromOccurrenceTime`.
Response `AffectedObjectsResponse`.

The pattern is: query findings to get `ruleUuid`s, then expand each rule to the objects it
affects. There is no operation here to create, suppress or acknowledge a finding — this tree is
read-only in the spec.

---

## New in 9.1 — Salt management

**5 operations. `/api/salt` has zero operations at 9.0.** Tag `Salt Management`. The Salt master
and Salt RaaS are VCF Management Services components introduced at 9.1 [DOPS; DELTA].

| Method | Path | operationId |
|---|---|---|
| GET | `/api/salt/resources/statuses` | `getSaltResources` |
| GET | `/api/salt/resources/{id}/status` | `getSaltResourceById` |
| POST | `/api/salt/resources/{id}/enable` | `configureMinion` |
| POST | `/api/salt/resources/{id}/keys/rotate` | `rotateResourceKeys` |
| GET | `/api/salt/tasks/{taskId}` | `getTask` |

All **spec-confirmed (9.1)**.

`getSaltResources` — query `status` (`CONNECTED | DISCONNECTED | DISABLED | UNKNOWN`), `page`,
`pageSize`. Response `ResourceSaltStatuses`.

`configureMinion` — body `ConfigureSaltRequest`: `masterId` (string). Returns **202** with
`SaltTaskDetails`; poll `GET /api/salt/tasks/{taskId}` (`getTask`), which returns the same
`SaltTaskDetails` schema.

> **Changes the managed endpoint.** `configureMinion` installs and enables a Salt minion on the
> target resource; `rotateResourceKeys` rotates its keys. Both act on a running guest or
> appliance, both are asynchronous, and neither has an "undo" operation in this tree. Note that
> `getTask` here is Salt-specific — it is *not* the generic `/api/tasks/{id}` (`getTaskStatus`),
> and the two return different schemas.

---

## New in 9.1 — what-if scenarios

**6 operations. `/api/whatif` has zero operations at 9.0.** Tag `What If`. Note this covers both
`scenarios` **and** `serverconfigs` — a list of "`whatif/scenarios` only" is incomplete.

| Method | Path | operationId |
|---|---|---|
| GET | `/api/whatif/scenarios` | `getScenarios` |
| POST | `/api/whatif/scenarios` | `saveScenario` |
| PUT | `/api/whatif/scenarios` | `updateScenario` |
| POST | `/api/whatif/scenarios/run` | `runScenario` |
| DELETE | `/api/whatif/scenarios/{id}` | `deleteScenario` |
| GET | `/api/whatif/serverconfigs` | `getServerConfigs` |

All **spec-confirmed (9.1)**.

`getScenarios` — query `scenarioStatus` (`SAVED | COMMITTED`), `page`, `pageSize`.
Response `WhatIfScenarios`.

`saveScenario` body (`WhatIfScenario`), required fields marked: `name`*, `actionType`*
(`WhatIfScenarioActionType`), `contentType`* (`WhatIfScenarioContentType`),
`whatIfScenarioStatus`*, plus `scenarioContent` (`commonUtilizationGrowthRate`,
`cpuUtilizationGrowthRate`, `memoryUtilizationGrowthRate`, `storageUtilizationGrowthRate`,
`existingVmConfigs[]`, `customVmConfigs[]`, `manualVmConfig`, `vmStorageConfig`),
`workloadCapacityLocation` (`dataCenterId`*, `clusterId`, `hypotheticalNewClusterConfig`),
`serverDetail` (`serverConfig`*, `serverCount`*), `privateCloudMigrationDetails`,
`publicCloudMigrationDetails`, `startDate`, `endDate`, `creationDate`, `state`, `id`.
Returns **201**.

`runScenario` body is `uuid-values`: `uuids[]` (required). Response `RunWhatIfScenario`.

`getServerConfigs` — query `clusterId`, `isHci`, `page`, `pageSize`. Response
`WhatIfScenarioDetailedServerConfigs`. Call this first: `serverDetail.serverConfig` on a scenario
has to come from somewhere.

The `SAVED` vs `COMMITTED` status distinction is why this is not purely a modelling toy — a
committed scenario is a capacity decision of record. `runScenario` itself computes; the spec
exposes no separate "commit" operation, so how a scenario becomes `COMMITTED` is
**UNVERIFIED** here.

---

## New in 9.1 — chargeback additions

> **Chargeback is not new in 9.1.** `SPEC9.0` contains **14** chargeback operations; `SPEC9.1`
> contains **20**. Only the 6 below are new. Any claim that the chargeback tree is 9.1-only is
> wrong.

Present in **both** versions (14): `generateBills`, `getBillSummary`
(POST `/api/chargeback/bills/query`), `getBill`, `deleteBill`, `getChargeBackReports`,
`createChargeBackReport`, `getChargeBackReport`, `deleteChargeBackReport`,
`downloadChargeBackReport`, and the five `/api/chargeback/reportdefinitions/{id}/schedules`
operations.

**New at 9.1** — all **spec-confirmed (9.1)**, all absent from `SPEC9.0`:

| Method | Path | operationId | Tag |
|---|---|---|---|
| GET | `/api/chargeback/bills/{id}/download` | `downloadBill` | Tenant Billing |
| GET | `/api/chargeback/notifications/rules` | `getAllChargebackNotificationRules` | Tenant Notifications |
| POST | `/api/chargeback/notifications/rules` | `createChargebackNotificationRule` | Tenant Notifications |
| PUT | `/api/chargeback/notifications/rules` | `updateChargebackNotificationRule` | Tenant Notifications |
| GET | `/api/chargeback/notifications/rules/{id}` | `getChargebackNotificationRule` | Tenant Notifications |
| DELETE | `/api/chargeback/notifications/rules/{id}` | `deleteChargebackNotificationRule` | Tenant Notifications |

`downloadBill` returns `application/pdf`, not JSON — the only PDF response in the trees covered
by this file.

`chargeback-notification-rule` body: `name` (required), `enabled` (boolean),
`alertDefinitionIds[]`, `resourceIds[]`, `id`. Note it binds to **alert definitions** — this is a
tenant-scoped notification channel layered on the alerting model, distinct from
`/api/notifications/rules` (present in both versions).

The 9.1 tag list also renames the chargeback tags: 9.0 has `Chargeback Billing` and
`Chargeback Reports`; 9.1 has `Tenant Billing`, `Tenant Reports` and `Tenant Notifications`
[`SPEC9.0`/`SPEC9.1` `meta.tags`]. Same operations, different tag names — a documentation
reorganisation, not an API change.

---

## New in 9.1 — optimization additions

> **Optimization is not new in 9.1.** `SPEC9.0` contains **10** optimization operations — the
> entire `optimization/workloadplacement/*` family; `SPEC9.1` contains **21**. Only the 11 below
> are new. Any claim that the optimization tree is 9.1-only is wrong.

Present in **both** versions (10): `getWlpHistory`
(POST `/api/optimization/workloadplacement/history/query`), plus, under
`/api/optimization/workloadplacement/{dataCenterId}/`: `enableAutomation`, `disableAutomation`,
`getAutomationStatus`, `enableCrossDCMove`, `disableCrossDCMove`, `getCrossDCMoveStatus`,
`getPlacementSettings`, `setPlacementSettings`, `deletePlacementConfiguration`.

**New at 9.1** — all **spec-confirmed (9.1)**, all absent from `SPEC9.0`, tag `Optimization`:

| Method | Path | operationId |
|---|---|---|
| GET | `/api/optimization/datacenters/{id}/reclaim/resources` | `getReclaimData` |
| GET | `/api/optimization/datacenters/{id}/rightsize/resources` | `getRightsizeData` |
| GET | `/api/optimization/datacenters/{dataCenterId}/exclusion/tags` | `getDCOptimizationConfiguration` |
| PUT | `/api/optimization/datacenters/{dataCenterId}/exclusion/tags` | `putDCOptimizationConfiguration` |
| PATCH | `/api/optimization/datacenters/{dataCenterId}/exclusion/tags` | `patchDCOptimizationConfiguration` |
| POST | `/api/optimization/reclaim/vms/{id}/exclude` | `excludeReclaimVMs` |
| POST | `/api/optimization/reclaim/vms/{id}/include` | `includeReclaimVMs` |
| POST | `/api/optimization/reclaim/orphaneddisks/{id}/exclude` | `excludeOrphanedDisks` |
| POST | `/api/optimization/reclaim/orphaneddisks/{id}/include` | `includeOrphanedDisks` |
| POST | `/api/optimization/rightsizing/vms/{id}/exclude` | `excludeRightsizingVMs` |
| POST | `/api/optimization/rightsizing/vms/{id}/include` | `includeRightsizingVMs` |

`getReclaimData` — path `id` (datacenter), **required** query `reason`
(`POWERED_OFF | IDLE | SNAPSHOT | ORPHANED_DISK`), optional `showExcluded`, `page`, `pageSize`.
Response `ReclaimRightsizeResources`.

`getRightsizeData` — path `id`, **required** query `reason` (`OVERSIZED | UNDERSIZED`), optional
`showExcluded`, `page`, `pageSize`. Same response schema.

The `reason` parameter is required on both — omitting it is a 4xx, not a full listing.

The `exclude` / `include` operations toggle whether a VM or orphaned disk appears in reclamation
and rightsizing candidate lists. They change what the product *recommends*; they do not
themselves delete or resize anything.

---

## New in 9.1 — logs query configs

**5 operations. `/api/logs/queryconfigs` is absent at 9.0** — but `/api/logs` itself is **not**
new: `SPEC9.0` has 7 operations there (`getLogConfigurationsByType`,
`createOrUpdateLogConfigurations`, `deleteLogConfigurationSettings`,
`getLogForwardingConfiguration`, `updateLogForwardingConfiguration`, `enableLogForwarding`,
`disableLogForwarding`), all still present at 9.1. `SPEC9.1` has 12.

| Method | Path | operationId |
|---|---|---|
| GET | `/api/logs/queryconfigs` | `getAllLIQueryConfigs` |
| POST | `/api/logs/queryconfigs` | `createQueryConfig` |
| PUT | `/api/logs/queryconfigs` | `updateQueryConfig` |
| GET | `/api/logs/queryconfigs/{queryConfigId}` | `getLIQueryConfig` |
| DELETE | `/api/logs/queryconfigs/{queryConfigId}` | `deleteLIQueryConfig` |

All **spec-confirmed (9.1)**, tag `Logs Management` (renamed from 9.0's `Log Management`).

`LogsQueryConfig` body: `name` (required), `queryText[]` (required),
`dateRange` (required — `{ startTime, endTime, fixedRange }`), `queryFilters`
(`log-query-filters`: `logQueryFilterConditions[]`, `logQueryFiltersOperator`, `partitions[]`),
`description`, `id`, `lastModifiedTime`, `modifiedBy`. Returns **201**.

These are *saved query definitions* stored in VCF Operations. **Executing** a log query is the
Log Management API's job, not this one — see `vcf-operations-logs-and-networks`. Do not present
`createQueryConfig` as a way to search logs.

---

## New in 9.1 — fleet management

**79 operations. `/api/fleet-management` has zero operations at 9.0** — the largest single
addition, 59% of the 134 new operations.

| Subtree | Ops | Tags |
|---|---|---|
| `/api/fleet-management/iam/*` | 70 | `IAM APIs` |
| `/api/fleet-management/certificate-management/*` | 7 | `Fleet Certificate Management` |
| `/api/fleet-management/password-management/*` | 2 | `Fleet Password Management` |

All **spec-confirmed (9.1)**, all absent from `SPEC9.0`.

**This is identity, certificate and credential management, not monitoring.** It belongs to
`vcf-foundation`. It is listed here only so that "what is genuinely 9.1-only on `/suite-api`?"
has a complete answer and nobody concludes the monitoring surface grew by 134 operations.

Shape, for routing purposes only:

- **IAM** — `identity-providers` (incl. LDAP directories, sync profiles, sync logs, SCIM sync
  clients), `ssorealms` (`api-clients`, `api-tokens`, `emergency-clients`, `oauth-apps`, users,
  groups, principal role assignments), fleet `roles`, per-component `roles` with drift-check and
  retry, component `auth-sources`, `settings`, `vidbs`, `saml-metadata/validate`,
  `tasks/{taskId}`.
- **Certificate management** — `certificate-authorities` (GET/PUT), `certificates/query`,
  `certificates/{certificateId}` (GET/PUT `replaceCertificate`), `csrs` (GET/POST).
- **Password management** — `accounts/query` (`getVcfPasswordAccounts`),
  `accounts/{passwordAccountKey}/password` (PUT `updatePassword`).

> **High blast radius.** `replaceCertificate` and `updatePassword` change credentials for fleet
> components. Out of scope here; do not improvise against them from this file.

Note that this tree **does not replace `/api/auth/*`**, which retains all 57 of its 9.0
operations at 9.1. Both exist side by side.

---

## Worked example — a resource's CPU metrics over a time range

Goal: average CPU demand for the VM `web-prod-01`, hourly buckets, over the last 24 hours.
Every path, method and `operationId` is from `SPEC9.1`; every field name, parameter and enum is
from `RAW9.1`. Every operation used here is also present at 9.0, so the same sequence works
there — with one exception, called out at step 1.

**1 — Acquire a token.** `acquireToken`, **spec-confirmed (9.1)**, also at 9.0.

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

Six hours from now this stops working; there is no refresh. **The 9.0 exception:** on 9.1 you
may substitute `Authorization: Bearer <vcf-sso-token>` and skip step 1 entirely. On 9.0 you may
not — `Bearer` is rejected there.

**2 — Resolve the name to an identifier.** `getMatchingResources`, **spec-confirmed (9.1)**,
also at 9.0. The GET form handles one exact name; POST is used here because it also constrains
the resource kind, avoiding a same-named object of another kind.

```http
POST /suite-api/api/resources/query?page=0&pageSize=100 HTTP/1.1

{
  "name": ["web-prod-01"],
  "adapterKind": ["VMWARE"],
  "resourceKind": ["VirtualMachine"]
}
```

Take `identifier` from the returned `resource` — call it `$RID`.

**3 — Confirm it is collecting.** `getResource`, **spec-confirmed (9.1)**, also at 9.0. This is
P5, and it is the step people skip.

```http
GET /suite-api/api/resources/$RID HTTP/1.1
```

Require `resourceStatusStates[0].resourceState == "STARTED"` and
`resourceStatusStates[0].resourceStatus == "DATA_RECEIVING"`. If it reads `COLLECTOR_DOWN` or
`NO_DATA_RECEIVING`, stop and go to P6 with `adapterInstanceId` from the same object. Note
`monitoringInterval` — it sets the finest bucket that can return data.

**4 — Get the exact stat key.** `getStatKeys`, **spec-confirmed (9.1)**, also at 9.0. This is
P7; guessing here is the difference between data and an empty array.

```http
GET /suite-api/api/resources/$RID/statkeys HTTP/1.1
```

Response is `stat-keys` → `stat-key[].key`. Pick the CPU demand key exactly as returned — the
key namespace is adapter-specific and this file asserts no literal key string.

**5 — Query the range.** `getStatsForResource`, **spec-confirmed (9.1)**, also at 9.0. `begin`
and `end` are epoch **milliseconds**; the values below are the 24 hours ending
2026-07-31T00:00:00Z.

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

**6 — If `stat` comes back empty.** In order, one call each:

1. `GET /api/resources/$RID/stats/latest` (`getLatestStats`) — data here but not in step 5 means
   the *range* is at fault, not the resource.
2. Re-read `resourceStatus` from step 3.
3. `GET /api/adapters/{adapterId}` (`getAdapterInstance`) — the path parameter is `adapterId`;
   the value is the `adapterInstanceId` read in step 3. Check `lastCollected` and
   `messageFromAdapterInstance`.
4. `GET /api/collectors` (`getCollectors`) — check `state == "UP"` for the hosting cloud proxy.
   At 9.1 also consider an expired proxy certificate (P6).
5. Re-check the key against step 4's list, character for character.

**Same query for many resources:** `POST /api/resources/stats/query` (`getStatsForResources`,
**spec-confirmed (9.1)**, also at 9.0), same `stat-query` body, with `resourceId` holding the
list and no path id.

**Scale note.** All multi-resource stat operations take arrays; none documents a maximum. Batch
conservatively and paginate the resource lookup with an explicit `pageSize`.

---

## What is not here

**Dashboards.** No dashboard endpoint exists in `SPEC9.1` (504 operations), `SPEC9.0` (370), or
`RAW9.1`. Searching all three for `dashboard` in a path, `operationId` or summary returns
nothing; in `RAW9.1` the string appears only as the `contentType` value `DASHBOARDS` inside
content-management import/export **examples**. Legacy vROps exposed `/suite-api/api/dashboards`.

> **UNVERIFIED — whether a dashboards API exists undocumented in 9.x.** [DOPS §Gaps item 2]
> Do not construct a `/suite-api/api/dashboards` call. If a user needs one, tell them it is not
> in the published spec for either version and send them to the on-appliance Swagger UI at
> `https://<ops-fqdn>/suite-api/doc/swagger-ui.html` — note the singular `doc`, as printed in
> the source [DOPS §"On-appliance API discovery"] — which reflects that build.

`/api/content` (10 operations, **spec-confirmed (9.1)**, all at 9.0) can move dashboard content
as part of an opaque content bundle. That is content migration, not a dashboard API, and should
not be offered as a substitute.

**Log search, Networks, real-time metrics.** Out of scope — `vcf-operations-logs-and-networks`.
Note that `POST /api/auth/token/exchange` (P1) is the *bridge* to those APIs and does belong
here; what you do with the resulting JWT does not.

**Identity, certificates, passwords.** `/api/fleet-management/*` is listed above for
completeness of the 9.1-only answer, but belongs to `vcf-foundation`.

**Upgrading VCF Operations, depots, bundles, prechecks.** Out of scope — `vcf-lifecycle-upgrade`.

---

## Deprecated operations in 9.1

`SPEC9.1` flags **13** operations `deprecated: true` — the **same 13** as `SPEC9.0`. Nothing was
newly deprecated and nothing un-deprecated between the versions.

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
> and `DOPS` does not discuss them. The `maintained` recommendation is an inference from
> overlapping function, not a documented migration. Confirm against the appliance's Swagger UI
> before rewriting automation.
