# VCF 9.0 → 9.1 — Logs and Networks Delta

Scoped to three surfaces: the log product (**replaced**, not upgraded), VCF Operations for
Networks (**nearly unchanged, with 22 new deprecations**), and real-time metrics (**new**).
`/suite-api` monitoring is a different skill (`vcf-operations-monitoring`); appliance lifecycle
is `vcf-lifecycle-upgrade`.

**Source keys.**
- `SPECLOG9.0` = `research/spec-inventory/9.0__vcf-operations-for-logs.ops.json` — 136 ops,
  base `/api/v2`.
- `SPECLM9.1` = `research/spec-inventory/9.1__log-management.ops.json` — 23 ops.
- `SPECNI9.0` / `SPECNI9.1` = the two `vcf-operations-for-networks` inventories — 632 / 636 ops,
  base `/api/ni` in both.
- `SPECRTM9.1` = `research/spec-inventory/9.1__realtime-metrics.ops.json` — 4 ops.
- `RAWLOG9.0`, `RAWLM9.1`, `RAWNI9.0`, `RAWNI9.1`, `RAWRTM9.1`, `RAWOPS9.1` = the corresponding
  raw OpenAPI documents at git tags `9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`.
- `DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of the two tags).
- `DOPS` = `research/vcf-operations.md`.

Every count below comes from diffing the inventories on the key `(method, path)`, not from
prose. Where prose and spec disagree, the spec wins and the disagreement is recorded.

> **Documentation-derived, not live-validated.** Captured 2026-07-31. Nothing has been executed
> against a running deployment.

---

## Contents

- [Headline](#headline)
- [The 136 → 23 drop, characterised honestly](#the-136--23-drop-characterised-honestly)
  - [Step 1 — what the 136 actually were](#step-1--what-the-136-actually-were)
  - [Step 2 — what happened inside the log data plane](#step-2--what-happened-inside-the-log-data-plane)
  - [Step 3 — the honest verdict](#step-3--the-honest-verdict)
  - [Step 4 — the two facts that break scripts](#step-4--the-two-facts-that-break-scripts)
- [The three token flows](#the-three-token-flows)
- [VCF Operations for Networks — the full delta](#vcf-operations-for-networks--the-full-delta)
  - [Added in 9.1 (5)](#added-in-91-5)
  - [Removed in 9.1 (1)](#removed-in-91-1)
  - [Newly deprecated in 9.1 — all 22](#newly-deprecated-in-91--all-22)
  - [Already deprecated at 9.0, still deprecated at 9.1 (31)](#already-deprecated-at-90-still-deprecated-at-91-31)
  - [Security schemes](#security-schemes)
- [Real-time metrics — new at 9.1](#real-time-metrics--new-at-91)
- [Prose-vs-spec disagreements found while writing these files](#prose-vs-spec-disagreements-found-while-writing-these-files)
- [Still unverified after this diff](#still-unverified-after-this-diff)

---

## Headline

| | 9.0 | 9.1 |
|---|---|---|
| **Log product** | VCF Operations for Logs — **136 operations**, base `/api/v2`, **port 9543** | Log Management — **23 operations**, base `/api/v2`, **different spec file** |
| Log auth | `Authorization: Bearer <sessionId>` from `POST /api/v2/sessions` | `X-JWT-Token: <jwt>` from `/suite-api/api/auth/token/exchange` |
| Log query | `GET /events/{constraints}` — path-encoded | `POST /api/v2/logs/search` — Elasticsearch-style JSON DSL |
| **Ops for Networks** | 632 operations, base `/api/ni` | **636.** +5, −1, **+22 newly deprecated** |
| Networks auth schemes | `ApiKeyAuth` only, **no top-level `security`** | `ApiKeyAuth` **+ `OpsTokenAuth`** (HTTP bearer), with a top-level `security` block |
| **Real-time metrics** | Absent from the BOM and from the spec repo | **New — 4 operations**, PromQL, `Authorization: Bearer <jwt>` |

`DELTA` states it plainly: *"`vcf-operations-for-logs` — spec removed in 9.1 … Absent at
9.1.0.0. Check for a renamed successor spec"* and *"`log-management` — spec is new in 9.1 …
Not present at tag 9.0.0.0."*

---

## The 136 → 23 drop, characterised honestly

**Both descriptions in the brief are partly right, and the split is roughly 80/20 in favour of
"differently-scoped spec."** Here is the accounting, tag by tag, from `SPECLOG9.0` and
`SPECLM9.1`.

### Step 1 — what the 136 actually were

9.0's log product was a **standalone appliance**. Its API owned identity, cluster lifecycle,
upgrades, certificates and a vCenter integration in addition to logs. Grouping `SPECLOG9.0`'s
29 tags (counts sum to 136):

| Group | Tags | Ops | % |
|---|---|---|---|
| **A. Log data plane** | `events` 3, `aggregated-events` 1, `fields` 4, `datasets` 5, `log-forwarder` 8, `limits` 3, `notification` 13 | **37** | 27% |
| **B. Appliance / cluster lifecycle** | `appliance` 2, `cluster` 6, `deployment` 5, `upgrades` 5, `time` 4, `ui` 4, `ceip` 2, `certificate` 2, `certificates` 3, `trusted-certificates` 2, `licenses` 1, `version` 1, `salt` 3 | **40** | 29% |
| **C. Identity and access** | `sessions` 2, `users` 8, `user-groups` 6, `roles` 13, `ad` 3, `vidm` 4, `vidb` 3, `auth-providers` 1 | **40** | 29% |
| **D. vSphere data-source integration** | `vsphere` 19 | **19** | 14% |

**B + C + D = 99 operations, 73% of the API, are appliance-management and identity concerns,
not logging.** At 9.1 the log product is a *service inside VCF Operations*, so none of that is
its job any more: identity comes from the exchanged JWT, appliance lifecycle belongs to Fleet
LCM / SDDC LCM, and vCenter registration belongs to `/suite-api`. Those 99 operations did not
lose functionality — they lost *ownership*. That is the "differently-scoped spec" reading, and
it accounts for **99 of the 113**.

### Step 2 — what happened inside the log data plane

The remaining 37 log-plane operations became 13, and 10 genuinely new agent-management
operations were added:

| 9.0 (37) | 9.1 | Verdict |
|---|---|---|
| `events` — 2 ingest (`POST /events`, `POST /events/ingest/{agentId}`) | **2** — same paths, `ingestJsonEvents`, `ingestEvents` | **Preserved.** Paths byte-identical; payload limit tightened 4 MB → 1 MB |
| `events` — 1 query (`GET /events/{+path}`) | folded into `POST /api/v2/logs/search` | **Replaced**, different language |
| `aggregated-events` — 1 (`GET /aggregated-events/{+path}`) | folded into the `aggregations` block of the same operation | **Replaced**, and arguably more capable (nesting, `top_hits`, `composite`) |
| `log-forwarder` — 8 | **7** at `/logs/forwarders` | **Preserved**, minus `POST /log-forwarder/batch` |
| `fields` — 4 (create, get, patch, delete by `{internalName}`; **no list**) | **2** (list, create; **no get, patch or delete**) | **Reduced.** Net loss of update and delete |
| `datasets` — 5 | **0** | **No counterpart in the spec** |
| `limits` — 3 | **0** | **No counterpart in the spec** |
| `notification` — 13 (channels, email, retention threshold, webhooks) | **0** | **No counterpart in the spec** |
| — | **+6** agent groups, **+4** agent secrets | **New capability at 9.1** |

Query surface arithmetic: 2 + 2 + 7 + 2 = 13, plus 10 new agent operations = **23.** ✓

### Step 3 — the honest verdict

- **99 of the 113 lost operations (88%) are scope transfer, not capability loss.** The product
  stopped being an appliance. Those operations moved out of the log API, and in most cases their
  equivalents exist elsewhere — `/suite-api/api/auth/*` for identity, Fleet LCM for upgrades,
  `/suite-api/api/integrations` for vCenter registration.
- **21 operations (datasets 5, limits 3, notifications 13) are genuine log-plane capability with
  no visible successor**, plus 2 extracted-field mutators and the forwarder batch operation —
  **24 in total that a 9.0 script can do and a 9.1 script, per these specs, cannot.**
- **The query API is not smaller, it is different.** One `POST` with a nestable
  Elasticsearch-style DSL and 15 aggregation types replaces two path-constrained `GET`s. Nobody
  reading "136 → 23" would guess the query surface got *more* expressive, but on the evidence of
  the schemas it did.
- **10 operations are net-new**: agent groups and agent secrets did not exist at 9.0.

**So: neither a "massive scope cut" nor a pure re-scoping. It is a re-scoping (88%) with a real
capability gap around it (~24 operations).** Say that, rather than either simplification.

> **Where the 21 went is UNVERIFIED.** Log-side notifications map plausibly onto
> `/suite-api/api/notifications` (10 operations, present in **both** 9.0 and 9.1 `/suite-api`
> inventories) and dataset-scoped RBAC onto `/suite-api/api/auth` scopes — but **no source
> available here states either mapping**, and the schemas were not compared. Do not present the
> substitution as documented. If a user needs log-scoped RBAC or log retention thresholds at
> 9.1, the honest answer is "not in the Log Management API; check `/suite-api` and the appliance
> UI."

### Step 4 — the two facts that break scripts

| | 9.0 | 9.1 |
|---|---|---|
| **Where** | `https://<logs-fqdn>:9543/api/v2/...` — *"Use HTTPS on port `9543`"* [`RAWLOG9.0`] | Address and port from the token exchange's `ServiceDetails`. `RAWLM9.1` declares `http://localhost:8787` with the description *"Generated server url"* — a build artifact. `RAWOPS9.1`'s exchange example shows `port: 8000` for `VCF_OPS_LI`. **Resolve per deployment.** |
| **How you query** | `GET /api/v2/events/text/CONTAINS%20Test/timestamp/LAST%20360000` + `limit`, `timeout`, `view`, `order-by-direction`. Defaults: 100 events, 30 s, **events from one minute ago or newer** | `POST /api/v2/logs/search` with `{query:{bool:{must,must_not,should,filter}}, sort, size≤2000, from≤20000, trackTotalHits, aggregations}` |

`DOPS` §Gaps item 4 warned *"Do not assume the legacy Log Insight `/api/v2/events/{constraints}`
shape carries over without checking the live appliance."* **The specs settle it: real at 9.0,
gone at 9.1.**

---

## The three token flows

The crux of this skill. Three products, three headers. General auth is `vcf-foundation`'s
subject; these three belong here because getting them wrong is the dominant failure mode.

| Product | Version | Header | Obtained by |
|---|---|---|---|
| VCF Operations for Logs | 9.0 | `Authorization: Bearer <sessionId>` | `POST /api/v2/sessions` `{username*, password*, provider*}` on the log appliance itself, port 9543. Response `{userId, sessionId, ttl}`; documented example `ttl: 1800` |
| Log Management | 9.1 | `X-JWT-Token: <jwt>` | **① `POST /suite-api/api/auth/token/acquire` → OpsToken. ② `POST /suite-api/api/auth/token/exchange` with `Authorization: OpsToken` and `{"serviceKeys":["ops-li"]}` → `jwtToken`.** No direct login exists |
| Real-time metrics | 9.1 | `Authorization: Bearer <jwt>` | ① OpsToken. ② `GET /suite-api/api/integrations/services` — find the key whose `type` is `VCF_VODAP`. ③ exchange that key. No direct login exists |
| Ops for Networks | 9.0 + 9.1 | `Authorization: NetworkInsight <token>` | `POST /api/ni/auth/token` `{username, password, domain{domain_type: LDAP\|LOCAL, value}}` → `{token, expiry}`. **Limit: 100 valid tokens per user, then 401** — delete them |
| Ops for Networks (alt.) | **9.1 only** | `Authorization: Bearer <jwt>` | `OpsTokenAuth` scheme, *"VCF Ops JWT Token"*. Source **inferred** as the `ops-ni` exchange key — see below |

`POST /suite-api/api/auth/token/exchange` (`exchangeOpsTokenWithJwtToken`) is
**spec-confirmed (9.1)** and **absent at 9.0** — one of the 134 operations added to `/suite-api`
in 9.1. Body `TokenExchangeRequest {serviceKeys[]*}` (`minItems: 1`, `uniqueItems: true`);
response `TokenExchangeResponse {jwtToken, services[]}`; optional `?includeServiceDetails=true`
(default `false`) to get `address`, `port`, `basePath`, `certificates[]`, `version`.

**Service keys.** `ops-li` is documented verbatim in `RAWLM9.1`'s security-scheme description
and in `DOPS` [S18]. `ops-ni` appears **only in `RAWOPS9.1`'s request and response examples**
(`{"serviceKeys": ["ops-li","ops-ni"]}`; `{"type":"VCF_OPS_NI","key":"ops-ni"}`). The VODAP key
is not a literal anywhere — `RAWRTM9.1` says to look up the entry whose **`type`** is
`VCF_VODAP` and use its `key`.

> **UNVERIFIED:** that `ops-ni` is how you obtain the Networks `OpsTokenAuth` bearer token. The
> key exists and Networks accepts a VCF Ops JWT; no source connects the two. Inferred.

---

## VCF Operations for Networks — the full delta

632 → 636. Diffed on `(method, path)`; **zero `operationId` changes** on any of the 631 shared
operations.

### Added in 9.1 (5)

| Call | operationId | Tag | Note |
|---|---|---|---|
| `GET /inventory-trees` | `getInventoryTrees` | `Inventory Tree` (new tag) | *"List Available Views."* `tree_type` example `HOSTS_CLUSTER` |
| `GET /inventory-trees/{tree-type}/{node-id}/children` | `getChildren` | `Inventory Tree` | *"Get children of node"* |
| `GET /settings/licensing/v2` | `getLicensesV2` | `Settings` | Replaces the newly-deprecated `GET /settings/licensing/` |
| `GET /settings/fips/modules` | `getFipsModulesDetails` | `Settings` | *"Get details of fips modules"* |
| `GET /migration/wave/{groupType}` | `getMigrationWave` | `Migration` | The renamed form of the removed operation below — **and it arrives already deprecated** |

### Removed in 9.1 (1)

| Call | operationId | Replacement |
|---|---|---|
| `GET /migration/{groupType}` | `getMigrationWave` | `GET /migration/wave/{groupType}` — **same `operationId`**, still `deprecated: true`. A path rename inside an already-deprecated family; it does not restore anything |

### Newly deprecated in 9.1 — all 22

Not deprecated at 9.0, `deprecated: true` at 9.1. Three complete data-source families plus one
licensing operation. `DELTA` counts these as 22; a raw `(method, path)` diff of the
deprecated-flag sets yields 23, the extra being `GET /migration/wave/{groupType}` — which is
**not** newly deprecated in substance, because it is the renamed successor to
`GET /migration/{groupType}`, which was **already** deprecated at 9.0. 22 is the honest number.

**AWS data sources — 7 operations. No replacement offered.**

| Call | operationId | Spec summary |
|---|---|---|
| `GET /data-sources/aws-accounts` | `listAWSDataSources` | List AWS data sources |
| `POST /data-sources/aws-accounts` | `addAWSDatasource` | Create an AWS data source |
| `GET /data-sources/aws-accounts/{id}` | `getAWSDataSource` | Show AWS data source details |
| `PUT /data-sources/aws-accounts/{id}` | `updateAWSDataSource` | Update an AWS data source |
| `DELETE /data-sources/aws-accounts/{id}` | `deleteAWSDataSource` | Delete an AWS data source |
| `POST /data-sources/aws-accounts/{id}/enable` | `enableAWSDataSource` | Enable an AWS data source |
| `POST /data-sources/aws-accounts/{id}/disable` | `disableAWSDataSource` | Disable an AWS data source |

**Azure data sources — 7 operations. No replacement offered.**

| Call | operationId | Spec summary |
|---|---|---|
| `GET /data-sources/azure-subscriptions` | `listAzureSubscriptions` | List Azure Cloud data sources |
| `POST /data-sources/azure-subscriptions` | `addAzureDatasource` | Create an Azure Cloud data source |
| `GET /data-sources/azure-subscriptions/{id}` | `getAzureSubscriptions` | Show Azure Cloud data source details |
| `PUT /data-sources/azure-subscriptions/{id}` | `updateAzureSubscription` | Update an Azure Cloud data source |
| `DELETE /data-sources/azure-subscriptions/{id}` | `deleteAzureSubscription` | Delete an Azure Cloud data source |
| `POST /data-sources/azure-subscriptions/{id}/enable` | `enableAzureSubscription` | Enable an Azure Cloud data source |
| `POST /data-sources/azure-subscriptions/{id}/disable` | `disableAzureSubscription` | Disable an Azure Cloud data source |

**NSX Advanced Load Balancer data sources — 7 operations. No replacement offered.**

| Call | operationId | Spec summary |
|---|---|---|
| `GET /data-sources/nsxalb` | `listNSXALB` | List NSX Advanced Load Balancer data sources |
| `POST /data-sources/nsxalb` | `addNSXALBDatasource` | Create an NSX Advanced Load Balancer data source |
| `GET /data-sources/nsxalb/{id}` | `getNSXALB` | Show NSX Advanced Load Balancer data source details |
| `PUT /data-sources/nsxalb/{id}` | `updateNSXALB` | Update an NSX Advanced Load Balancer data source |
| `DELETE /data-sources/nsxalb/{id}` | `deleteNSXALB` | Delete an NSX Advanced Load Balancer data source |
| `POST /data-sources/nsxalb/{id}/enable` | `enableNSXALB` | Enable an NSX Advanced Load Balancer data source |
| `POST /data-sources/nsxalb/{id}/disable` | `disableNSXALB` | Disable an NSX Advanced Load Balancer data source |

**Licensing — 1 operation, with a replacement.**

| Call | operationId | Replacement |
|---|---|---|
| `GET /settings/licensing/` | `getLicenses` — *"Get current licensing and license usage information"* | **`GET /settings/licensing/v2`** (`getLicensesV2`, *"Get information for current licenses"*), new at 9.1. Note the v2 summary drops *"and license usage"* — **whether usage data is still returned is UNVERIFIED** |

**Note the entity endpoints were NOT deprecated.** `GET /entities/aws-account-managers`,
`/entities/azure-subscriptions` and their `{id}` forms remain undeprecated at 9.1, even though
the *data-source* families that populate them are deprecated. Reading existing cloud entities
still works; adding new cloud data sources is on a deprecation path.

### Already deprecated at 9.0, still deprecated at 9.1 (31)

Nothing was un-deprecated. Do not present any of these as a 9.1 change:

| Family | Ops | Replacement |
|---|---|---|
| Pinboards (`/pinboards*`) | 12 | Custom dashboards (12 operations, undeprecated, same shape) — **inferred**, not stated in the spec |
| User-defined events (`/settings/events/user-defined-events*`) | 7 | Search-based alerts (`/settings/alerts/search-based-alerts*`, 7 operations) — **inferred** |
| IP tags v1 (`getIpTagIds`, `getIpTag`, `addIpTag`, `removeIpTag`) | 4 | `/settings/ip-tags/v2/*` — `getTagIdsV2`, `getIpTagV2`, `addTagV2`, `removeTagV2` |
| Licensing v1 (`activateSerialNumber`, `deactivateSerialNumber`, `validateSerialNumber`) | 3 | Not stated. `getLicensesV2` covers reads only |
| Migration (`getMigrationWave`, `enableMigrationWave`, `disableMigrationWave`) | 3 | None. Path renamed at 9.1, deprecation retained |
| Metrics v1 (`getMetrics`, `fetchBulkMetrics`) | 2 | `GET /metrics/v2` (`getMetricsV2`), `POST /metrics/fetch/v2` (`fetchBulkMetricsV2`) |

Deprecated totals: **31 at 9.0 → 53 at 9.1.**

### Security schemes

| | 9.0 | 9.1 |
|---|---|---|
| Schemes declared | `ApiKeyAuth` only — `type: apiKey`, header `Authorization`, *"API Key - NetworkInsight {token}"* | `ApiKeyAuth` **plus** `OpsTokenAuth` — `type: http`, `scheme: bearer`, *"VCF Ops JWT Token - Bearer {token}"* |
| Top-level `security` | **Absent** | `[{ApiKeyAuth}, {OpsTokenAuth}]` |

This is the only auth-shaped change on the Networks API, and it breaks in the 9.1 → 9.0
direction: a bearer JWT has no spec support at 9.0.

> **Prose-vs-spec disagreement.** `DOPS` §"Other components' auth" tags both schemes
> `[9.0+9.1]`, but states the reason itself: *"the portal does not version-split these two
> schemes."* The specs do split them. **`OpsTokenAuth` is 9.1-only.**

---

## Real-time metrics — new at 9.1

No 9.0 counterpart: absent from the 9.0 BOM [`DOPS` §Delta table] and absent from the spec repo
at tag `9.0.0.0` [`DELTA`]. Four operations, all **spec-confirmed (9.1)**:
`GET /api/v1/query` (`query`), `GET /api/v1/query_range` (`queryRange`),
`GET /api/v1/metadata` (`queryMetricMetadata`),
`PUT /api/v1/vcenters/{vcId}/metrics_config` (`updateVcMetricsConfig`).

Prometheus-compatible response envelope (`status`, `data.resultType` ∈
`matrix|vector|scalar|string`), but **not** a full Prometheus API — no `/series`, `/labels`,
`/targets` or `/rules`. Two collection profiles, `STANDARD` and `VERBOSE`, plus per-host ESXi
Top MOID `ADD`/`REMOVE`.

`DOPS` records from the 9.1 What's New that default sampling is 20 seconds, configurable to
2 seconds for ESX, with TopN charts and saved PromQL dashboards. **None of that is configurable
through these four operations** — where it lives is **UNVERIFIED**.

---

## Prose-vs-spec disagreements found while writing these files

| Claim | Source | What the spec shows | Resolution |
|---|---|---|---|
| The `/api/ni` prefix could not be confirmed; *"do not assume it"* | `DOPS` §Gaps item 5 | `servers: [{"url": "/api/ni"}]` in **both** `RAWNI9.0` and `RAWNI9.1` | **Resolved.** `/api/ni` is correct in both versions |
| Log Management concrete endpoints unknown; portal returned "Object Not Found" | `DOPS` §Gaps item 4 [S25][S26] | `SPECLM9.1` + `RAWLM9.1` give all 23 paths, schemas and enums | **Resolved from the spec.** The speculative `/api/v2/events/query` tried in [S26] is **not** a real path — the real one is `POST /api/v2/logs/search` |
| Legacy Log Insight `/api/v2/events/{constraints}` might not carry over | `DOPS` §Gaps item 4 | Present at 9.0 (`GET /events/{+path}`), **absent at 9.1** | **Resolved.** The warning was right for 9.1 and wrong for 9.0 |
| Networks accepts both `NetworkInsight` and Bearer in 9.0 and 9.1 | `DOPS` §"Other components' auth" [S17], tagged `[9.0+9.1]` | `RAWNI9.0` declares one scheme; `RAWNI9.1` declares two | **Prose over-broad**, and it says why. `OpsTokenAuth` is 9.1-only |
| Networks token acquisition endpoint, payload and TTL unretrievable | `DOPS` §"Other components' auth" | `POST /auth/token` (`create`), body `UserCredential`, response `Token {token, expiry}` | **Partly resolved.** Endpoint and payload confirmed; **no fixed TTL** is declared — read `expiry` |
| A 9.0 "Log Management" category exists inside the VCF Operations API | `DOPS` §"Log Management API" [S16] | True but unrelated: `/suite-api/api/logs/*` is 7 appliance log-config operations at 9.0, tag `Log Management`, renamed tag `Logs Management` at 9.1 with 5 `queryconfigs` added | **Both true, easily confused.** `/suite-api/api/logs` configures *VCF Operations' own* logging and stores saved queries; it never executes a log search |

---

## Still unverified after this diff

- **Where 9.0's datasets, limits and notification operations went at 9.1.** Plausible
  `/suite-api` homes exist; no source states the mapping and no schemas were compared.
- **Whether extracted-field update and delete exist anywhere at 9.1** — 9.1 exposes list and
  create only.
- **Log Management's real address and port** per deployment; 8787 is a generated placeholder and
  the exchange example shows 8000.
- **The literal VODAP service key** — only its `type` is documented.
- **Whether `ops-ni` is the source of the Networks `OpsTokenAuth` JWT.**
- **Queryable field names and the default time window** for `POST /api/v2/logs/search`.
- **Whether an unauthenticated log-ingest path survives at 9.1.**
- **Whether any replacement exists for the AWS, Azure and NSX-ALB data-source families**, or
  whether the capability is simply being retired.
- **Whether `GET /settings/licensing/v2` still returns license *usage***, which the deprecated
  v1 summary explicitly mentioned.
- **The full set of Networks `tree_type` values** — only `HOSTS_CLUSTER` is exampled.
- **Role, privilege and capability names; retention; rate limits** on all products here.
