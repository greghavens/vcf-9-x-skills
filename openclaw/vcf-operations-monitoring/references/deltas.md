# VCF Operations 9.0 → 9.1 — Monitoring Delta

Scoped to the VCF Operations `/suite-api` API: resources, stats, alerts, reports, custom groups,
and the trees that changed. Log Management, VCF Operations for Networks and real-time metrics
are a different skill (`vcf-operations-logs-and-networks`); lifecycle is `vcf-lifecycle-upgrade`.

**Source keys.**
- `SPEC9.0` = `research/spec-inventory/9.0__vcf-operations.ops.json` — 370 operations, base
  `/suite-api`, spec `version` field empty.
- `SPEC9.1` = `research/spec-inventory/9.1__vcf-operations.ops.json` — 504 operations, spec
  version `9.1.0.0`.
- `RAW9.1` = `specifications/vcf-operations/vcf-operations-openapi.json` at tag `9.1.0.0`.
- `DELTA` = `research/spec-inventory/DELTA-9.0-to-9.1.md` (machine-computed diff of git tags
  `9.0.0.0` and `9.1.0.0` of `github.com/vmware/vcf-api-specs`).
- `DOPS` = `research/vcf-operations.md`.

Every count and every "9.1-only" claim below comes from diffing `SPEC9.0` against `SPEC9.1` on
the key `(method, path)` — not from prose. Where prose and spec disagree, the spec wins and the
disagreement is recorded.

> **Documentation-derived, not live-validated.** Captured 2026-07-31. Nothing has been executed
> against a running deployment.

---

## Headline

| | 9.0 | 9.1 |
|---|---|---|
| Operations | **370** | **504** |
| Added | — | **134** |
| Removed | — | **0** |
| Newly deprecated | — | **0** (13 deprecated in both, same 13) |
| Base path | `/suite-api` | `/suite-api` — **unchanged** |
| Security scheme | `Token-based-authorization` (`apiKey`, header `Authorization`) | identical |

9.1 is a strict superset. Nothing that worked at 9.0 was withdrawn.

---

## Three corrections this file exists to enforce

1. **Chargeback and optimization are NOT 9.1-only.** Chargeback has **14** operations at 9.0
   (bills, reports, per-definition schedules); optimization has **10** at 9.0 (the entire
   `optimization/workloadplacement/*` family). 9.1 adds 6 and 11 respectively. Lists that put
   whole `chargeback/*` or `optimization/*` trees in the 9.1-only column are wrong.

2. **`/auth/roles` and `/auth/privileges` are NOT 9.1-only.** An earlier prose pass claimed they
   were. `SPEC9.0` contains **57** operations under `/api/auth`, including `getRoles`,
   `getRoleByName`, `getRolePrivileges`, `getAvailablePrivileges`,
   `getAvailablePrivilegeGroups`, `getAssignedRolePermissionsForCurrentUser` and
   `getCurrentUserRolePrivileges`. `SPEC9.1` contains **59** — the same 57 plus exactly two new
   ones (below). What 9.1 genuinely adds is a *parallel* `/api/fleet-management/iam/*` tree that
   sits alongside `/api/auth/*` rather than replacing it.

3. **The core monitoring surface did not change at all.** Resources 66→66, alerts 13→13, alert
   definitions 8→8, alert plugins 11→11, reports 5→5, report definitions and schedules 7→7,
   super metrics 5→5, symptoms 2→2, symptom definitions 5→5, policies 13→13, recommendations
   5→5, notifications 10→10, adapters 13→13, credentials 8→8, tasks 2→2, events 4→4,
   maintenance schedules 4→4, deployment 8→8, content 10→10. If the question is about metrics,
   alerts or reports, the version does not matter — say so rather than hedging.

---

## What is genuinely 9.1-only

Trees with **zero** operations at 9.0 and one or more at 9.1. This is the complete list, from
the diff:

| Tree | 9.1 ops | Tags | Covered in |
|---|---|---|---|
| `/api/fleet-management/*` | **79** | `IAM APIs` (70), `Fleet Certificate Management` (7), `Fleet Password Management` (2) | `9.1/monitoring.md` (routing only — this is `vcf-foundation`) |
| `/api/whatif/*` | **6** | `What If` | `9.1/monitoring.md` |
| `/api/salt/*` | **5** | `Salt Management` | `9.1/monitoring.md` |
| `/api/diagnostics/findings/*` | **2** | `Findings` | `9.1/monitoring.md` |
| `/api/workflows/requests/{requestId}` | **1** | `Workflow Request` | `9.1/monitoring.md` |

Two footnotes that commonly get lost:

- **`whatif` is not only `scenarios`.** It is 5 `scenarios` operations *plus*
  `GET /api/whatif/serverconfigs` (`getServerConfigs`).
- **`workflows/requests` is a real 9.1-only addition** and is usually missing from circulated
  lists. One operation: `GET /api/workflows/requests/{requestId}` (`getRequestById`).

### 9.1-only *subtrees* inside trees that already existed

These are new paths, but their parent tree is present at 9.0 — so they belong in a different
sentence from the table above.

| Subtree | New ops | Parent tree at 9.0 |
|---|---|---|
| `/api/logs/queryconfigs` | 5 | `/api/logs` has 7 operations at 9.0 |
| `/api/chargeback/notifications/rules` + `bills/{id}/download` | 6 | `/api/chargeback` has 14 at 9.0 |
| `/api/optimization/{datacenters,reclaim,rightsizing}` | 11 | `/api/optimization` has 10 at 9.0 |
| `/api/integrations/services` | 8 | `/api/integrations` has 19 at 9.0 |
| `/api/applications/agents/**/certificates/renew` | 4 | `/api/applications` has 25 at 9.0 |
| `/api/collectors/{id}/certificates/renew[/status]` | 2 | `/api/collectors` has 4 at 9.0 |
| `/api/collectorgroups/{id}/certificates/renew[/status]` | 2 | `/api/collectorgroups` has 7 at 9.0 |
| `/api/auth/{token/exchange, sources/vidb/well-known-url}` | 2 | `/api/auth` has 57 at 9.0 |
| `/api/adapterkinds/**/identifiers` | 1 | `/api/adapterkinds` has 8 at 9.0 |

134 total: 79 + 6 + 5 + 2 + 1 + 5 + 6 + 11 + 8 + 4 + 2 + 2 + 2 + 1 = 134. The arithmetic closes,
which is the point of doing it from the diff rather than from prose.

---

## Delta table

| Item | 9.0 | 9.1 | Source |
|---|---|---|---|
| **API size** | 370 operations. | **504 operations. 134 added, 0 removed, 0 newly deprecated.** | `DELTA`; `SPEC9.0`/`SPEC9.1` |
| **Base path** | `/suite-api`, with operations under `/api/...`. | **Unchanged.** `RAW9.1` declares `servers: [{ "url": "/suite-api" }]`. | `SPEC9.0`/`SPEC9.1` `meta.base_path`; `RAW9.1` |
| **Spec version string** | Empty in the 9.0 document. | `9.1.0.0`. Cosmetic, but it is how you tell the two documents apart if the filename is lost. | `SPEC9.0`/`SPEC9.1` `meta.spec_version` |
| **Token acquisition** | `POST /api/auth/token/acquire` (`acquireToken`); body `username`*, `password`*, `authSource`; response `token`*, `validity`*, `expiresAt`, `roles`; token format `uuid::uuid`; **six-hour TTL**, no refresh. `POST /api/auth/token/release` (`releaseToken`) present. | **Identical.** Same operationIds, same schema. | `SPEC9.0`/`SPEC9.1`; `RAW9.1`; `DOPS` |
| **Authorization header** | `Authorization: OpsToken <token>`; legacy `vRealizeOpsToken` still accepted; `SSO2Token <SAML>` for external SSO. **`Bearer` is not accepted.** | Same three, **plus `Authorization: Bearer <token>` issued by VCF SSO.** This is the one auth-shaped thing that actually differs, and it breaks in the 9.1→9.0 direction. | `DOPS` §"Token acquisition"; spec confirms the header *name* only |
| **Token exchange for downstream services** | Absent. | **New:** `POST /api/auth/token/exchange` (`exchangeOpsTokenWithJwtToken`), body `TokenExchangeRequest { serviceKeys[]* }`, optional `?includeServiceDetails`. Used to get a Log Management JWT (`{"serviceKeys":["ops-li"]}` → `X-JWT-Token`) or a real-time-metrics JWT (`VCF_VODAP` → `Bearer`). | `SPEC9.1`; `RAW9.1`; `DOPS` |
| **VIDB discovery** | Absent. | **New:** `GET /api/auth/sources/vidb/well-known-url` (`getVIDBWellKnownURL`) — OIDC discovery for the VCF Identity Broker. | `SPEC9.1`; `DOPS` |
| **Rest of `/api/auth`** | 57 operations: users, user groups, roles, privileges, scopes, sources, source types, traversal specs, current user. | **The same 57, unchanged**, plus the two above = 59. Nothing removed. | `SPEC9.0`/`SPEC9.1` |
| **Fleet-wide IAM** | Absent. | **New: 70 operations** under `/api/fleet-management/iam/*` — identity providers with LDAP directories and SCIM sync, SSO realms with `api-clients`, `api-tokens`, `emergency-clients`, `oauth-apps`, principal role assignments, fleet roles, per-component roles with drift-check/retry, IAM settings, `vidbs`, SAML metadata validation, IAM tasks. Sits **alongside** `/api/auth/*`, not in place of it. `vcf-foundation`'s subject. | `SPEC9.1`; `DOPS` §"OAuth 2.0 API tokens" |
| **Resources / inventory** | 66 operations under `/api/resources`. | **66. Byte-identical set.** | `SPEC9.0`/`SPEC9.1` |
| **Stats / metrics** | 15 operations with `/stats` in the path — 11 read (`getStatsOfResource`, `getStatsForResource`, latest, top-N, DT) and 4 push — plus 3 stat-key operations and `/api/supermetrics` (5). | **Identical.** No new stat operation, no changed path. The dossier flagged the literal stats paths as UNVERIFIED; both inventories confirm them at both versions. | `SPEC9.0`/`SPEC9.1`; `DOPS` §"Stats / metrics" |
| **Custom groups** | 9 operations under `/api/resources/groups` (6) and `/api/resources/groups/types` (3). | **Identical.** The dossier flagged these paths as UNVERIFIED too; both inventories confirm them. | `SPEC9.0`/`SPEC9.1`; `DOPS` §"Custom groups" |
| **Alerts** | 13 operations, incl. `queryAlert` with the embedded `resource-query`. | **Identical.** | `SPEC9.0`/`SPEC9.1` |
| **Alert definitions / symptoms / recommendations** | 8 / 7 / 5. | **Identical.** | `SPEC9.0`/`SPEC9.1` |
| **Reports and schedules** | 5 report + 7 report-definition/schedule operations; `X-Ops-API-Timezone` header on schedule POST/PUT. | **Identical.** | `SPEC9.0`/`SPEC9.1`; `RAW9.1` |
| **Cloud proxy / collector** | Component named **"VCF Operations collector."** 4 operations under `/api/collectors`, 7 under `/api/collectorgroups`. | Component **renamed "cloud proxy."** API paths unchanged; the `collector.type` enum already read `CLOUD_PROXY` at 9.0. **+2 operations each** for certificate renewal: `renewCloudProxyCertificate`, `getCollectorCertificateRenewStatus`, `renewCollectorGroupCertificate`, `getCollectorGroupCertificateRenewalStatus`. | `DOPS` §"Renames"; `DELTA`; `SPEC9.0`/`SPEC9.1` |
| **Diagnostics findings** | Absent. | **New: 2 operations**, tag `Findings` — `queryFindings` (POST `/api/diagnostics/findings/query`, with `sortBy` over 9 fields) and `queryAffectedObjects` (POST `/api/diagnostics/findings/{ruleUuid}/affectedobjects/query`). Read-only; no create/suppress/acknowledge in the spec. | `SPEC9.1`; `RAW9.1` |
| **Salt management** | Absent. | **New: 5 operations**, tag `Salt Management` — `getSaltResources`, `getSaltResourceById`, `configureMinion` (202 + `SaltTaskDetails`), `rotateResourceKeys`, `getTask`. Note `getTask` is Salt-specific and distinct from the generic `getTaskStatus` on `/api/tasks/{id}`. | `SPEC9.1`; `RAW9.1` |
| **What-if scenarios** | Absent. | **New: 6 operations**, tag `What If` — `getScenarios`, `saveScenario`, `updateScenario`, `runScenario`, `deleteScenario`, **and `getServerConfigs`** (`/api/whatif/serverconfigs`, usually omitted from circulated lists). `scenarioStatus` is `SAVED \| COMMITTED`; how a scenario becomes `COMMITTED` is **UNVERIFIED**. | `SPEC9.1`; `RAW9.1` |
| **Workflow requests** | Absent. | **New: 1 operation** — `GET /api/workflows/requests/{requestId}` (`getRequestById`), tag `Workflow Request`. | `SPEC9.1` |
| **Chargeback** | **14 operations** — `generateBills`, `getBillSummary`, `getBill`, `deleteBill`, 5 chargeback reports, 5 per-definition schedules. Tags `Chargeback Billing`, `Chargeback Reports`. | **20 operations. +6:** `downloadBill` (returns `application/pdf`) and the 5 `chargeback/notifications/rules` operations (`chargeback-notification-rule` binds `alertDefinitionIds[]` and `resourceIds[]`). Tags **renamed** to `Tenant Billing`, `Tenant Reports`, `Tenant Notifications`. | `SPEC9.0`/`SPEC9.1` `meta.tags` |
| **Optimization** | **10 operations**, all `optimization/workloadplacement/*` — placement settings, automation enable/disable, cross-DC move, history query. | **21 operations. +11:** `getReclaimData` and `getRightsizeData` (both with a **required** `reason` query parameter — `POWERED_OFF\|IDLE\|SNAPSHOT\|ORPHANED_DISK` and `OVERSIZED\|UNDERSIZED`), DC exclusion tags (GET/PUT/PATCH), and 6 include/exclude toggles for reclaim VMs, orphaned disks and rightsizing VMs. The 9.0 workloadplacement family is untouched. | `SPEC9.0`/`SPEC9.1`; `RAW9.1` |
| **Logs (appliance config)** | **7 operations** — log configuration by type, log forwarding get/update/enable/disable. Tag `Log Management`. | **12. +5:** `/api/logs/queryconfigs` CRUD (`LogsQueryConfig` with `name`*, `queryText[]`*, `dateRange`*). Tag renamed `Logs Management`. These store *saved query definitions*; **executing** a log query is the Log Management API, a different product. | `SPEC9.0`/`SPEC9.1`; `RAW9.1` |
| **Integrations** | 19 operations — vCenter and VCF integration registration. | **27. +8** under `/api/integrations/services`: `getIntegratedServices` plus per-service certificate (`getVVFCertificates`, `replaceVVFCertificate`, `getVVFCsrs`, `generateVVFCsr`) and password (`getVVFAccountList`, `updatePasswordSystem`, `getVvfTaskStatus`) management. Tags `Component Certificate Management`, `Component Password Management`. | `SPEC9.0`/`SPEC9.1` |
| **Applications / agents** | 25 operations. | **29. +4** agent certificate renewal: `renewClientsCertificate`, `getRenewClientsCertificateStatus`, `renewClientCertificate`, `getRenewClientCertificateStatus`. | `SPEC9.0`/`SPEC9.1` |
| **Adapter kinds** | 8 operations. | **9. +1:** `GET /api/adapterkinds/{adapterKindKey}/resourcekinds/{resourceKindKey}/identifiers` (`getResourceIdentifiersDetails`) — resource identifier fields for a kind, useful when constructing a `resource-key`. | `SPEC9.0`/`SPEC9.1` |
| **Deprecations** | 13 operations flagged `deprecated: true`. | **The same 13.** Nothing newly deprecated, nothing un-deprecated. The four `monitoringstate` operations are the ones that matter for monitoring work. | `SPEC9.0`/`SPEC9.1` |
| **Dashboards API** | Not present. | Not present. Not in `SPEC9.0`, `SPEC9.1` or `RAW9.1`; `dashboard` occurs in `RAW9.1` only as the `contentType` value `DASHBOARDS` inside content-management examples. **UNVERIFIED** whether one exists undocumented. | `DOPS` §Gaps item 2; both inventories; `RAW9.1` |

---

## The 9.1 tag list, diffed

Tag names are documentation grouping, not API surface, but they are what a reader sees in the
portal and they moved enough to cause confusion.

**Removed at 9.1:** `Chargeback Billing`, `Chargeback Reports`, `Log Management`.

**Added at 9.1:** `Component Certificate Management`, `Component Password Management`,
`Findings`, `Fleet Certificate Management`, `Fleet Password Management`, `IAM APIs`,
`Logs Management`, `Salt Management`, `Tenant Billing`, `Tenant Notifications`,
`Tenant Reports`, `What If`, `Workflow Request`.

`Chargeback Billing`/`Chargeback Reports` → `Tenant Billing`/`Tenant Reports` and
`Log Management` → `Logs Management` are **renames of existing groupings**, not removals of
functionality. All 14 chargeback operations and all 7 logs operations from 9.0 survive.

---

## Prose-vs-spec disagreements found while writing these files

| Claim | Source of claim | What the spec shows | Resolution |
|---|---|---|---|
| `/auth/roles` and `/auth/privileges` are 9.1-only | earlier prose pass | Both present at 9.0; all 57 `/api/auth` operations exist at 9.0 | **Prose wrong.** Corrected in both version files. |
| Whole `chargeback/*` tree is 9.1-only | circulated 9.1-only list | 14 chargeback operations at 9.0 | **List wrong.** Only 6 chargeback operations are new. |
| Whole `optimization/*` tree is 9.1-only | circulated 9.1-only list | 10 optimization operations at 9.0 | **List wrong.** Only 11 are new. |
| "No release/revoke endpoint is documented" | `DOPS` §"Token acquisition", from the prose doc pages | `POST /api/auth/token/release` (`releaseToken`) is present in **both** inventories | **Prose incomplete.** The endpoint exists; the doc pages simply did not mention it. |
| Custom group and stats literal paths not retrievable | `DOPS` — marked UNVERIFIED | `/api/resources/groups*` (9 ops) and `/api/resources/stats*` (15 ops) confirmed in both inventories, exactly as the dossier guessed | **Resolved.** No longer UNVERIFIED; the dossier's expected paths were right. |
| `pageSize` defaults to 1000 | `DOPS` | `RAW9.1` documents `page` (explicitly 0-based) and `pageSize` but states **no default** | **Partially resolved.** 0-based `page` confirmed; the 1000 default is **UNVERIFIED** — pass `pageSize` explicitly. |
| A `/suite-api/api/dashboards` path exists (legacy vROps habit) | assumption | Absent from all three sources | **UNVERIFIED / do not use.** Check the on-appliance Swagger UI. |

---

## Still unverified after this diff

- **Built-in role names** (Administrator, ReadOnly or otherwise) and the privilege required by
  any specific operation. No source available here enumerates them. Discover per deployment via
  `GET /api/auth/roles` and `GET /api/auth/currentuser/permissions`.
- **Metric retention period and roll-up tiering**, and the behavior of a `begin` that predates
  retention.
- **Rate limits or throttling** on any of these operations.
- **How a what-if scenario transitions from `SAVED` to `COMMITTED`.** The status enum exists;
  no commit operation appears in the spec.
- **9.0 field-level schemas.** The 9.0 *raw* OpenAPI document was not available — only the
  operation inventory. Field names and enums in `9.0/monitoring.md` are inherited from `RAW9.1`
  on the strength of identical operationIds. Paths, methods and operationIds at 9.0 are
  confirmed; field detail is not.
- **Whether a dashboards API exists undocumented in 9.x.**
