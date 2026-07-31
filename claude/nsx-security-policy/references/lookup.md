# Confirming an NSX endpoint that this skill does not cover

The version files (`9.0/dfw.md`, `9.1/dfw.md`) cover the distributed firewall surface. For anything
else — or for anything you need to be *certain* about — use this file. The methods are ordered by
reliability, best first.

**The governing rule:** never emit an NSX path you have not confirmed by one of methods A–C below.
Path-shape heuristics (method D) are for *forming a hypothesis to check*, not for producing a call.

---

## A. Ask the appliance for its own spec — best, and the only route that settles 9.0

```
GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.json    # Policy API — use this one
GET https://<nsx-manager>/api/v1/spec/openapi/nsx_policy_api.yaml
GET https://<nsx-manager>/api/v1/spec/openapi/nsx_api.json           # Manager API (node/cluster/fabric)
GET https://<nsx-manager>/api/v1/spec/openapi/nsx_api.yaml
GET https://<nsx-manager>/api/v1/spec/openapi/nsx_vmc_policy_api.{yaml,json}
GET https://<nsx-manager>/api/v1/spec/openapi/nsx_vmc_aws_integration_api.{yaml,json}
```

**Verified in both the NSX 9.0.0 and NSX 9.1.0 API Guides.** `[9.0+9.1]`

Why this is first:

- It is served by the **running** NSX Manager, so the document matches the deployed build exactly
  (9.0.0.0 / 24733065 or 9.1.0.0 / 25318225, or whatever patch is actually installed).
- It **eliminates version-contamination risk entirely** — there is no way to accidentally read a 9.1
  answer for a 9.0 question.
- **It is the only way to get spec-grade answers for NSX 9.0.** The public spec corpus
  (`github.com/vmware/vcf-api-specs`) publishes **no NSX specification at the `9.0.0.0` tag**:
  `nsx-policy`, `nsx-manager` and `nsx-global-policy` are absent there and appear only at `9.1.0.0`.
  If the target is 9.0 and the question is "does this endpoint exist," this call is the answer.

Authenticate first (session cookie + `X-XSRF-TOKEN`, or HTTP Basic). Note that the spec endpoints live
under `/api/v1`, which is one of the few surviving non-policy uses of the Manager API path.

Practical usage:

```bash
curl -sS -b session.txt -H "x-xsrf-token: $XSRF" \
  "https://$NSX/api/v1/spec/openapi/nsx_policy_api.json" -o nsx_policy_api.json

# does the endpoint exist, and with which verbs?
jq -r '.paths | to_entries[] | select(.key|test("security-policies")) |
       "\(.key)\t\(.value|keys|join(","))"' nsx_policy_api.json
```

Two shape notes when parsing:

- The document declares `basePath: /policy/api/v1` (Policy) or `/api/v1` (Manager). **Paths inside the
  document are relative to that base path** — `/infra/domains/...` means
  `/policy/api/v1/infra/domains/...`.
- A handful of Manager-API paths are declared **absolutely**, outside the base path — notably
  `/api/session/create` and `/api/session/destroy`. Do not prepend `/api/v1` to those.

---

## B. Version-pinned developer.broadcom.com URLs

Use when you have no appliance to query.

Roots — **always pin the version in the path**:

```
https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/
https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/
```

Doc sets also exist for `9.0.1` and `9.0.2`. Pick the one matching the deployed NSX build from the VCF
BOM — never an unpinned URL.

| Pattern | Example | What it gives you |
|---|---|---|
| `<root>/method_<OperationId>.html` | `.../9.1.0/method_ReadTier0.html` | **Highest-value page.** Verb, **all** path templates including `global-infra` and `orgs/projects` variants, and query parameters. |
| `<root>/<category>.html` | `.../9.1.0/security_firewall.html` | Every method in a functional area with verb + path. Best for bulk extraction. |
| `<root>/types_<TypeName>.html`, `<root>/schemas_<Name>.html` | | Request/response body schemas. |
| `<root>/api_single_page.html` | | Consolidated guide. Frequently too large to fetch, and returned a server error for 9.1.0 in practice. |

### Trap: category slugs differ between the two doc sets

This is a real failure mode, not a nicety.

- **9.1.0** slugs are **function-first**: `security_firewall.html`, `inventory_groups.html`,
  `networking_switching_segments.html`, `networking_routing_tier-0s.html`,
  `networking_routing_tier-1s.html`, `networking_nat_nat_rules_tier-0s.html`,
  `networking_load_balancing_lb_services.html`, `networking_vpn_ipsec_services.html`,
  `networking_ip_management_ip_pools.html`, `networking_switching_transport_zones.html`,
  `system_fabric_edge_clusters.html`.
- **9.0.0** slugs are **`policy_`-prefixed**: `policy_networking.html`, `policy_security.html`,
  `policy_security_east_west_security_distributed_firewall.html`,
  `management_plane_api_networking.html`.

**Adding or removing the `policy_` prefix is not a reliable translation.**
`policy_networking_switching_segments.html` does not exist for 9.0.0, and the 9.1 DFW page is *not*
`security_east_west_security_distributed_firewall.html`. **Navigate the left-hand nav tree from the
version root instead of guessing a slug.**

`method_<OperationId>.html` pages, by contrast, use the same naming in both doc sets — if you know the
operation ID, that pattern is the safer probe.

### Trap: a nonexistent page returns the SPA nav shell — this is NOT "endpoint absent"

developer.broadcom.com is a single-page application. **A URL that does not exist does not return a clean
404.** It returns the application shell: the navigation menu, sometimes the string "Object Not Found",
and no content.

**Failure signature:** if a fetch yields only category links and no verb/path table, **the URL is
wrong.** Do not record that as evidence that the endpoint does not exist. This produced false negatives
during research — the 9.1.0 "Removed Methods" / "Removed Types" pages could not be opened under any
guessed filename and returned the shell every time, which says nothing about whether those lists exist.

When you get the shell:
1. Re-derive the slug by navigating the nav tree from the version root, or
2. Switch to `method_<OperationId>.html`, or
3. Fall back to method A (the appliance's own spec), which cannot produce this failure mode.

### The prose mirror — for auth, pagination, rate limits, concurrency

```
https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.0.0/html/index.html
https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html
```

Pattern: `.../API_NTDCRA_001/<nsx-version>/html/index.html`. Each page self-identifies its version
("NSX API Guide", "NSX 9.1.0.0") — **use that string as a contamination check** before trusting anything
you read there.

Note: `.../<version>/html/api_usage_user_authentication.html` returns **404** on this host. The
authentication content lives inside `index.html`.

---

## C. Grep the machine-extracted spec corpus

Local, fast, and the strongest offline evidence — **for 9.1 only.**

### Extracted operation inventories

**All paths in this section are relative to this skill's own directory** (the one containing
`SKILL.md`), so they keep working wherever the skill is installed. From `references/`, that is one
level up.

Resolve the inventory directory in this order:

```bash
# 1. Bundled alongside the vcf-api-discovery skill — the normal case when both skills are installed.
INV=../../vcf-api-discovery/references/spec-inventory

# 2. Fallback: the research corpus in a checkout of this repo, if you are working in-tree.
[ -d "$INV" ] || INV=../../../research/spec-inventory

# 3. Last resort: regenerate from the upstream repo at the pinned tag —
#    github.com/vmware/vcf-api-specs @ 9.1.0.0, specifications/nsx/openapi-2.0/
[ -d "$INV" ] || { echo "no local inventory; use method A or clone the repo at tag 9.1.0.0" >&2; }
```

The three NSX inventories:

```
$INV/9.1__nsx-policy.ops.json          # 3,729 ops, basePath /policy/api/v1
$INV/9.1__nsx-manager.ops.json         # 1,453 ops, basePath /api/v1
$INV/9.1__nsx-global-policy.ops.json   # 1,009 ops, basePath /global-manager/api/v1
```

If none of the three locations resolves, **fall back to method A** (ask the live appliance for its own
spec) — that is always available and is authoritative for the build in front of you.

Each file is `{"meta": {...}, "operations": [...]}` where each operation is:

```json
{"method": "PATCH",
 "path": "/infra/domains/{domain-id}/security-policies/{security-policy-id}",
 "operationId": "PatchSecurityPolicyForDomain",
 "tags": ["Security", "..."],
 "deprecated": false}
```

Confirm an endpoint:

```bash
INV=${INV:-../../vcf-api-discovery/references/spec-inventory}
python3 - "$INV/9.1__nsx-policy.ops.json" <<'EOF'
import json, re, sys
d = json.load(open(sys.argv[1]))
pat = re.compile(r'security-policies/\{security-policy-id\}/rules')
for o in d['operations']:
    if pat.search(o['path']):
        print(o['method'], o['path'], o['operationId'], 'DEPRECATED' if o['deprecated'] else '')
EOF
```

**Always check the `deprecated` flag.** The 9.1 spec carries live-but-deprecated trees — e.g. all 12
`communication-maps` / `communication-entries` operations, and most of the `firewall-identity-stores`
CRUD. A path existing is not a reason to use it.

### The raw specification

The inventories carry only `method` / `path` / `operationId` / `tags` / `deprecated`. For **schemas**
you need the raw YAML, which is **not bundled with this skill** (it is ~15 MB per file). Obtain it by
cloning `github.com/vmware/vcf-api-specs` at tag **`9.1.0.0`** and pointing `SPECS` at the checkout:

```bash
SPECS=${SPECS:-/tmp/vcf-api-specs}/specifications/nsx/openapi-2.0
# $SPECS/nsx_policy_api.yaml    # ~15 MB — Policy API
# $SPECS/nsx_api.yaml           # Manager API (ApiServiceConfig, trust-management, aaa, …)
```

**15 MB — grep or slice it, never read it whole.** It is the place to go for what the inventories omit:
request/response **schemas**, field names, enums, defaults, required flags, and Broadcom's own
`x-vmw-nsx-example-request` / `x-vmw-nsx-example-response` blocks.

```bash
# locate a definition, then slice it
grep -n '^  SecurityPolicy:' "$SPECS/nsx_policy_api.yaml"
grep -n '^  /infra/domains/{domain-id}/security-policies:' "$SPECS/nsx_policy_api.yaml"

# schema defaults live in the definition; Broadcom's own examples live on the path item
grep -n 'x-vmw-nsx-example-response' "$SPECS/nsx_api.yaml"
```

**Read the example from the *same* path item as the endpoint you are documenting.** Several NSX models
share field names across different endpoints — e.g. `client_api_rate_limit` appears on both
`ApiServiceConfig` (`/api/v1/cluster/api-service`, default `250`) and the deprecated
`HttpServiceProperties` (`/api/v1/node/services/http`, default `100`). Quoting the wrong one produces a
confidently-wrong `[SPEC]` claim.

Definitions sit at two-space indent under `definitions:`; a definition block runs until the next line at
that indent level. Path items sit at two-space indent under `paths:`.

### The hard limit of method C

**There is no NSX spec at the `9.0.0.0` tag.** The inventory summary records `nsx-policy`,
`nsx-manager` and `nsx-global-policy` as `9.0 present: no`. Consequences:

- **A 9.1 spec hit is not evidence about 9.0.** Never carry a `[SPEC]` claim across the version boundary.
- **A 9.0-vs-9.1 NSX diff cannot be produced from this corpus.** If you need to know what changed, you
  need either (a) a live 9.0 appliance's own spec via method A, or (b) the prose release notes — which
  publish the removed-operation *counts* but **not the paths** (see `deltas.md`).
- For 9.0 the ordering is: **method A** (appliance spec) → **method B** (9.0.0-pinned prose) → stop.
  Method C does not apply.

---

## D. Path-shape heuristics — form a hypothesis, then confirm it

`[9.0+9.1 — same in both]`. **These generate candidates to check with A/B/C. They are not confirmation.**

```
/policy/api/v1/infra/<collection>                              # local, list
/policy/api/v1/infra/<collection>/{id}                         # local, CRUD
/policy/api/v1/global-infra/<collection>/{id}                  # Federation / Global Manager
/policy/api/v1/orgs/{org-id}/projects/{project-id}/infra/...   # multi-tenancy (projects)
/policy/api/v1/orgs/{org-id}/projects/{project-id}/vpcs/{vpc-id}/...   # VPC scope
/policy/api/v1/infra/tier-0s/{tier-0-id}/<service>             # T0-attached service
/policy/api/v1/infra/tier-1s/{tier-1-id}/<service>             # T1-attached service
/policy/api/v1/infra/domains/{domain-id}/<security-object>     # DFW: groups, security-policies
/policy/api/v1/infra/sites/{site-id}/enforcement-points/{enforcementpoint-id}/<fabric-object>
/policy/api/v1/infra/settings/<subsystem>/...                  # global settings
```

Verb conventions:

| Verb | Meaning |
|---|---|
| `GET` | list (on a collection) or read (on an id) |
| `PATCH` | create-or-update, **merge** semantics; does not require `_revision` |
| `PUT` | create-or-**replace**; `_revision` must be omitted on create and supplied on update |
| `DELETE` | remove |
| `POST …?action=<verb>` or `…/actions/<verb>` | imperative operations — `revise`, `reprocess`, `failover`, `publish`, `site_failover`, `filter` |

When a hierarchical list endpoint is known to omit objects (the 9.1 docs say this about flexible
segments under a Tier-1), use the **search API**: `GET /policy/api/v1/search/query` (`QuerySearch`) or
`GET /policy/api/v1/search/dsl` (`DslSearch`). **Spec-confirmed for 9.1**; unconfirmed for 9.0 — verify
via method A before using it on a 9.0 appliance.

---

## E. Runtime conventions to build into any client

`[9.0+9.1]` unless noted.

- **Pagination.** `ListResult` with `page_size` default and maximum **1000**. Follow `cursor` until it
  is absent. List endpoints also accept `included_fields`, `sort_by`, `sort_ascending`,
  `include_mark_for_delete_objects`.
- **Rate limits.** Back off on HTTP **429**. Per-client **100 req/s** and **40 concurrent**. The overall
  server limit is stated as **199** in the 9.0 prose but as `global_api_concurrency_limit` **`default:
  500`** (503 on exceed) in the 9.1 spec — an unresolved discrepancy; prefer the spec value for 9.1.
- **Optimistic concurrency.** Read `_revision`, echo it on `PUT`. **Omit `_revision` on a `PUT` that
  creates** a `/policy` resource. `PATCH` avoids the issue entirely.
- **Partial patch is off by default.** Enable with
  `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` `{"enable_partial_patch": "true"}`.
- **Session expiry surfaces as HTTP 403, not 401.** Re-authenticate on 403 and retry once; a second 403
  means insufficient role, not expiry. (Doc-verbatim for 9.1; treat identically in 9.0.)
- **Session affinity.** Session cookies are bound to a single NSX Manager node and cannot be reused
  across cluster members. Pin the client to one node, or re-authenticate per node. Behind a VIP that
  load-balances, this manifests as intermittent 403s. (Doc-verbatim for 9.0 only; not restated on a
  9.1-pinned page — assumed unchanged, not confirmed.)
- **Both auth headers are required.** `Cookie: JSESSIONID=…` **and** `X-XSRF-TOKEN: …` on every call
  after `/api/session/create`.
- **URL-encode passwords** in the `/api/session/create` form body — `+` and other special characters
  break it otherwise.
- **Check `deprecated`.** In the 9.1 spec, `communication-maps` (the pre-Policy DFW naming) and most of
  `firewall-identity-stores` are present but deprecated. Existence is not endorsement.

---

## F. What has no lookup route

Known dead ends. Do not burn time re-deriving them.

| Question | Status |
|---|---|
| **Paths of the 17 + 9 + 1 operations removed in 9.1** | **Broadcom does not publish them.** Counts and themes only. The portal's "Removed Methods" / "Removed Types" pages return the SPA shell. The only route is diffing a live 9.0 appliance's own spec (method A) against the 9.1 spec. |
| **Any NSX spec at the `9.0.0.0` corpus tag** | Does not exist. Method A only. |
| **Interactive API explorer / Swagger UI on the NSX Manager appliance** | Unverified for both 9.0 and 9.1. The VCF admin guides do not mention one; they direct readers to the external NSX API Guide. The practical substitutes are method A and method B. |
| **JWT / bearer-token auth against NSX Manager** | Not documented in either doc set. Only session, HTTP Basic, X.509 client certificate, and the VMC-specific token exchange appear. |
| **An authoritative list of which NSX objects VCF owns vs. which an operator may change directly** | Does not exist in either doc set. Evidence is indirect only. |
| **Host transport node endpoints** | Could not be resolved from the portal in either doc set. Use method A. |
| **9.0.1 / 9.0.2 NSX build numbers** | Not retrieved. Re-check the VCF BOM for the specific patch. |

---

## G. Decision procedure

```
Need to confirm an NSX endpoint
  │
  ├─ Do you have appliance access?
  │    └─ YES → METHOD A. GET /api/v1/spec/openapi/nsx_policy_api.json. Done. Version-exact.
  │
  ├─ NO, and the target is 9.1?
  │    └─ METHOD C (grep 9.1__nsx-*.ops.json, then the raw YAML for schemas)
  │       └─ not found? → METHOD B on the /9.1.0/ portal root
  │          └─ got the SPA nav shell? → wrong URL, NOT "absent". Re-derive the slug or try
  │             method_<OperationId>.html.
  │
  └─ NO, and the target is 9.0?
       └─ METHOD B on the /9.0.0/ (or /9.0.1/, /9.0.2/) portal root — prose only.
          Method C does NOT apply: there is no 9.0 NSX spec.
          └─ Still unresolved? → report it as unverified for 9.0 and say so.
             Do NOT substitute a 9.1 spec hit and call it confirmed.
```
