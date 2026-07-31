# Blocking tcp/3389 between two existing NSX groups — on VCF 9.0

Short version of your confidence question first, because it changes how you should use the rest:

**The paths and verbs are solid. The request bodies are not.** For 9.0 I can give you
documentation-grade confidence on every URL in the sequence below, and only *inferred* confidence on
the JSON field names inside them. There is one call that removes the uncertainty entirely, and it's
in Step 0b.

---

## Why 9.0 is a weaker evidence position than 9.1

This isn't hedging boilerplate — it's structural. **Broadcom publishes no NSX OpenAPI specification at
the `9.0.0.0` tag** of `github.com/vmware/vcf-api-specs`. `nsx-policy`, `nsx-manager` and
`nsx-global-policy` all first appear at `9.1.0.0` (3,729 / 1,453 / 1,009 operations respectively).

So for 9.1 I can say "this operation exists, here is its operationId, here are its parameters and its
schema" and point at a machine-readable file. For 9.0 the best available evidence is version-pinned
prose on `developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/` and the VCF 9.0 product docs.

And critically: **a path being confirmed in the 9.1 spec is not evidence about 9.0.** It's very often
the same path — the DFW tree looks unchanged across the two — but "almost certainly identical" and
"verified" are different things to hand someone who is about to change a production firewall. Below,
every line is tagged so you can see which one you're getting.

| Tag | Meaning |
|---|---|
| **[DOC-9.0]** | Read from a 9.0.0-pinned Broadcom page. Strongest evidence that exists for 9.0. |
| **[9.1-ONLY]** | Known only from the 9.1 doc set or 9.1 spec. Confirm on your appliance before relying on it. |
| **[INFERRED]** | A shape or convention carried over, not a verified 9.0 fact. |

---

## Confidence, endpoint by endpoint

| Call used below | Confidence |
|---|---|
| `POST /api/session/create`, `/api/session/destroy` | **[DOC-9.0]** — verbatim in the NSX 9.0.0 API Guide *and* the VCF 9.0 NSX admin guide. High. |
| `GET /policy/api/v1/infra/domains/{domain-id}/security-policies` | **[DOC-9.0]** |
| `GET /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` | **[DOC-9.0]** (single-group **read** only — see the gap note) |
| `PATCH /policy/api/v1/infra/domains/{domain-id}/security-policies/{policy-id}` | **[DOC-9.0]** |
| `PATCH …/security-policies/{policy-id}/rules/{rule-id}` | **[DOC-9.0]** |
| `GET …/rules/{rule-id}` and `…/rules/{rule-id}/statistics` | **[DOC-9.0]** |
| `POST …/rules/{rule-id}?action=revise` | Endpoint **[DOC-9.0]**; its `operation` / `anchor_path` parameters and the "body is mandatory" fact are **[9.1-ONLY]** |
| **Every JSON field name in the bodies** (`action`, `source_groups`, `destination_groups`, `service_entries`, `L4PortSetServiceEntry`, `l4_protocol`, `destination_ports`, `scope`, `category`, `sequence_number`, …) | **[INFERRED]** — read from the 9.1 spec's schemas. The 9.0 research captured DFW *paths* but never DFW *schemas*. This is the weakest link in the whole answer. |

The good news: the policy + rule CRUD sub-tree, `?action=revise` and `/statistics` were all listed
together on a single 9.0.0-pinned distributed-firewall reference page. That is the strongest part of
the 9.0 evidence, and it's exactly the part this task needs.

Gaps that specifically shape the runbook below, all "not observed on a 9.0 page" rather than "proven
absent":

- `GET /infra/domains` (domain **list**) — **[9.1-ONLY]**. So don't smoke-test with it.
- `GET /infra/domains/{domain-id}/groups` (group **list**) and the group **write** verbs — **[9.1-ONLY]**.
  Single-group read is fine, which is all we need.
- `/policy/api/v1/infra/services` — **[9.1-ONLY]**, not covered by the 9.0 prose at all. **This is why
  the rule below uses inline `service_entries` instead of `"services": ["/infra/services/RDP"]`.** If
  your 9.1 runbook referenced a predefined RDP service object, that's the one substantive change.
- Draft list / `/complete` / `/aggregated` — **[9.1-ONLY]**. `GET·PUT·PATCH·DELETE /infra/drafts/{draft-id}`
  and `POST /infra/drafts/{draft-id}?action=publish` *are* **[DOC-9.0]**, so drafts remain available to
  you as a staging mechanism if you want the change published atomically.

---

## Step 0b — the one call that converts all of this into verified fact

```bash
curl -sS -b session.txt -H "x-xsrf-token: $XSRF" \
  "https://$NSX/api/v1/spec/openapi/nsx_policy_api.json" -o nsx_policy_api.json

jq -r '.paths | to_entries[] | select(.key|test("security-policies")) |
       "\(.key)\t\(.value|keys|join(","))"' nsx_policy_api.json
```

The running NSX Manager serves the OpenAPI document **for its own deployed build**. It is the only
route to spec-grade answers on 9.0, it cannot be contaminated by 9.1 material, and it also settles the
schema question (the definitions are in the same document). This endpoint is itself verified in both
the 9.0.0 and 9.1.0 API Guides. Note it lives under `/api/v1` — one of the few surviving non-policy
uses of the Manager API path.

If you run that one call before Step 3, my confidence in the whole sequence goes from "documented
paths, inferred bodies" to "verified against your appliance."

---

## Before you touch anything

1. **Confirm the domain id.** `default` is a convention, not a guarantee.
2. **Both groups must already exist, and you must use their server-returned `path` strings** — not
   names, not UUIDs, not hand-assembled paths. A rule whose group path doesn't resolve is accepted at
   write time and then silently never realises.
3. **Role: Enterprise Admin** (`enterprise_admin`) for writes; Auditor is read-only. Verify it with a
   harmless read, not by attempting the production write.
4. **Service account:** on 9.0 the documented mechanism is an NSX **principal identity** with an X.509
   client certificate. The SSO-issued, role-scoped API token you may have read about is a **9.1**
   capability and does not exist in 9.0. Be aware the 9.0 support notes also flag principal identities
   as *"planned for deprecation in an upcoming release"* — use it, but plan the migration.
5. **Patch line:** this is pinned to NSX **9.0.0.0 (build 24733065)** from the VCF 9.0 BOM. Separate
   NSX API doc sets exist for 9.0.1 and 9.0.2, and those build numbers are unverified here. If you're
   on a 9.0.x patch, re-check the BOM.
6. **Ownership:** there is **no authoritative published list** of which NSX objects VCF owns and which
   an operator may change directly — in either version. DFW policies, rules and groups are normal
   targets for direct Policy API automation, but that split is inference, not a documented statement.
   9.0 also has no SDDC Manager network-sync reconciliation (that's a 9.1 addition), so out-of-band NSX
   edits are *less* clearly supported on 9.0 than on 9.1.

---

## The sequence

```bash
NSX=https://nsx-mgr.example.com
DOMAIN=default          # verify in Step 1 — do not assume
SRC_GROUP=app-tier
DST_GROUP=db-tier
POLICY=block-rdp-app-to-db
RULE=deny-rdp
```

### Step 0 — authenticate

```bash
curl -sS -c /tmp/nsx-session.txt -D /tmp/nsx-headers.txt \
  -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'j_username=svc-nsx-automation@example.com' \
  --data-urlencode 'j_password=<password>' \
  "$NSX/api/session/create"

XSRF=$(grep -i '^x-xsrf-token:' /tmp/nsx-headers.txt | tr -d '\r' | awk '{print $2}')
AUTH=(-b /tmp/nsx-session.txt -H "x-xsrf-token: $XSRF" -H 'Content-Type: application/json')
```

**[DOC-9.0].** Both the `JSESSIONID` cookie **and** the `X-XSRF-TOKEN` header are required on every
subsequent call — cookie alone fails in a way that reads like a permissions problem. URL-encode the
password (`+` and other specials break the form body).

Two traps, and note their evidence differs:

- **Session expiry surfaces as 403, not 401.** That sentence is verbatim on the **9.1** page and is
  *not* on the 9.0 page — so for 9.0 it's **[9.1-ONLY]** as a documented claim. Handle it anyway:
  re-authenticate on 403 and retry once; a second 403 means role, not expiry. Harmless if 9.0 differs.
- **Session cookies are bound to a single manager node** and cannot be reused across cluster members.
  This one **is [DOC-9.0]** — verbatim on the 9.0-pinned page. Behind a VIP it presents as random
  intermittent auth failures. Pin the client to one node's address.

Default inactivity timeout is 1800 s. Rate limits per 9.0 prose: 100 req/s, 40 concurrent per client
(429 on exceed).

### Step 1 — confirm the domain resolves

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies"
```

**[DOC-9.0].** A 200 (even with an empty result list) proves the domain resolves; 404 means the id is
wrong. Deliberately **not** `GET /infra/domains` — that list endpoint is **[9.1-ONLY]**, so it's the
wrong smoke test on 9.0.

### Step 2 — capture the group paths from the server

```bash
SRC_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/groups/$SRC_GROUP" | jq -r '.path')
DST_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/groups/$DST_GROUP" | jq -r '.path')

for v in SRC_PATH DST_PATH; do
  case "${!v}" in
    ''|null) echo "FATAL: $v unresolved in domain '$DOMAIN'" >&2; exit 1 ;;
  esac
done
```

**[DOC-9.0].** Use the returned `path` literally. Don't build these strings yourself — project-scoped
and Federation-scoped groups have longer paths, and a hand-built path is the most common cause of a
rule that writes successfully and never realises.

### Step 2b — while you're here, steal a schema

```bash
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies" | jq '.results[0]'
```

If your appliance has any existing security policy or rule, reading one and mirroring its field names
is a one-call fix for the only genuinely inferred part of this answer.

### Step 3 — create the security policy (the container)

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY" \
  -d "$(jq -n --arg dst "$DST_PATH" '{
    display_name:    "Block RDP app-tier to db-tier",
    description:     "Managed by automation",
    category:        "Application",
    sequence_number: 100,
    stateful:        true,
    scope:           [$dst]
  }')"
```

Path and verb **[DOC-9.0]**; body field names **[INFERRED]**. `PATCH` rather than `PUT` on purpose:
`PATCH` is create-or-update and needs no `_revision`. The exact `_revision`-on-create-vs-update rule is
stated verbatim only in the **9.1** guide — the 9.0 guide only says `/policy` URIs "have slightly
different behavior." `PATCH` sidesteps the question entirely.

If this returns 400, it's a field-name mismatch — `GET` an existing policy and mirror it.

### Step 4 — create the rule *inside* the policy

The nesting is the whole point: **a rule lives under a security policy, which lives under a domain.**
There is no `POST /policy/api/v1/rules` and no `POST /infra/domains/default/rules`.

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE" \
  -d "$(jq -n --arg src "$SRC_PATH" --arg dst "$DST_PATH" '{
    display_name:       "Deny RDP 3389",
    action:             "DROP",
    source_groups:      [$src],
    destination_groups: [$dst],
    service_entries: [
      {
        resource_type:     "L4PortSetServiceEntry",
        display_name:      "tcp-3389",
        l4_protocol:       "TCP",
        destination_ports: ["3389"]
      }
    ],
    scope:           [$dst],
    direction:       "IN_OUT",
    ip_protocol:     "IPV4_IPV6",
    sequence_number: 10,
    logged:          true
  }')"
```

Path and verb **[DOC-9.0]**; body **[INFERRED]**.

- **Inline `service_entries` is a deliberate 9.0 choice** — `/infra/services` isn't verified for 9.0,
  so inlining keeps the service definition inside the rule and removes the dependency.
- `DROP` discards silently; `REJECT` sends RST / ICMP unreachable. For RDP, `DROP` is usually what you
  want unless you need fast client-side failure.
- `scope` is "Applied To" — scoping to the destination group limits which vNICs get the rule
  programmed, which matters for DFW rule-count scale.

### Step 5 — verify realization

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE"
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE/statistics"
```

Both **[DOC-9.0]**. The read confirms the object exists; statistics confirms it's programmed in the
data path and gives you hit counts.

### Step 6 — position it, only if order matters

```bash
curl -sS -X POST "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE?action=revise&operation=insert_top" \
  -d '<the full Rule body from Step 5>'
```

Endpoint **[DOC-9.0]**; the `operation` / `anchor_path` parameter names and the mandatory-body
requirement are **[9.1-ONLY]**. If the parameters are rejected, fall back to setting `sequence_number`
explicitly via `PATCH`.

Ordering has three stacked levels: policy **category** (Emergency > Infrastructure > Environment >
Application; uncategorized is least) → policy `sequence_number` → rule `sequence_number`. A correct
rule sequenced after a broader allow simply never matches.

### Step 7 — log out

```bash
curl -sS -X POST "${AUTH[@]}" "$NSX/api/session/destroy"
```

**[DOC-9.0]** — send both the cookie and the token header.

---

## If something fails

| Symptom | Most likely cause |
|---|---|
| 403 on Step 1 right after a successful Step 0 | `X-XSRF-TOKEN` not sent |
| 403 mid-sequence after a pause | Session expired — re-auth and retry (9.1-doc'd behaviour, applied here defensively) |
| 403 that persists after re-auth | Role too low; Enterprise Admin required for writes |
| 403 on some calls, apparently at random | Cookie used against a different cluster node behind a VIP — **this one is 9.0-doc-verified** |
| 404 on Step 1 | Wrong `{domain-id}` |
| **400 on Step 3 or 4** | **Body field-name mismatch — the expected failure mode given the schemas are inferred. `GET` an existing object and mirror it.** |
| 200 on Step 4 but no traffic effect | Groups empty, `scope` excludes the workloads, or a higher-precedence policy already allows the flow |
| Rule accepted but never realises | A group path that doesn't resolve — re-read the `path` from Step 2 |
| 429 | Rate limit, 100 req/s per 9.0 prose. Back off. |

---

## One more thing worth raising

Since this rule could sever a management path if the groups are broader than you expect: 9.0 supports
firewall **drafts** — `GET·PUT·PATCH·DELETE /policy/api/v1/infra/drafts/{draft-id}` and
`POST /infra/drafts/{draft-id}?action=publish`, both **[DOC-9.0]** — so you can stage and publish as a
unit rather than writing live objects one at a time. The draft *list* and *preview* endpoints are
9.1-only, but the core stage-and-publish pair is documented for 9.0.

Also: everything here is Policy API (`/policy/api/v1`). If you have an inherited script reaching for
`/api/v1` to create policy objects, it needs rewriting — the Manager API and Manager mode from NSX 4.x
are no longer supported for policy objects in 9.0. `/api/v1` survives only for session lifecycle, node
and cluster admin, fabric admin, and the OpenAPI spec retrieval in Step 0b. Don't emit
`communication-maps` paths either; that tree is flagged deprecated on the 9.0 DFW page.

---

## Bottom line on your question

**High confidence** in every URL and HTTP verb in Steps 0–7 — those came off 9.0.0-pinned Broadcom
pages, and the policy/rule CRUD tree in particular was documented as a block on a single page.

**Low confidence** in the JSON field names, enum values and defaults. Those were carried over from the
9.1 specification because no 9.0 source publishes them. They are very likely identical — the Policy
API schema model is long-standing — but I can't evidence that, and I'd rather you know than find out
via a 400 during a change window.

**Not confident, and flagged inline:** the `?action=revise` query parameters, the 403-on-expiry
behaviour, and anything I marked **[9.1-ONLY]**.

Run the Step 0b spec fetch and all three of those categories collapse into verified fact for *your*
build. It costs one call.
