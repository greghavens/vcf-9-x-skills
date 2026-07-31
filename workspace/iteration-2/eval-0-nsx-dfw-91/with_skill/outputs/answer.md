# Block tcp/3389 from app-tier to db-tier — NSX 9.1 (VCF 9.1) Policy API

All calls are on the Policy API (`/policy/api/v1`). The Manager API (`/api/v1`) is not supported for DFW objects in VCF 9.x. Paths below are confirmed against the NSX 9.1.0.0 OpenAPI spec.

```bash
NSX=https://nsx-mgr.example.com   # pin to ONE manager node, not a VIP — see note 2
DOMAIN=default
SRC_GROUP=app-tier
DST_GROUP=db-tier
POLICY=block-rdp-app-to-db
RULE=deny-rdp
```

## 1. Authenticate (session cookie + XSRF token)

```bash
curl -sS -c /tmp/nsx-session.txt -D /tmp/nsx-headers.txt -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'j_username=svc-nsx-automation@example.com' \
  --data-urlencode 'j_password=<password>' \
  "$NSX/api/session/create"

XSRF=$(grep -i '^x-xsrf-token:' /tmp/nsx-headers.txt | tr -d '\r' | awk '{print $2}')
AUTH=(-b /tmp/nsx-session.txt -H "x-xsrf-token: $XSRF" -H 'Content-Type: application/json')
```

`/api/session/create` sits outside the `/api/v1` base path — don't add `v1`. Both the `JSESSIONID` cookie **and** the `x-xsrf-token` header must go on every subsequent call; cookie-only writes fail in a way that looks like a permissions problem.

## 2. Capture the real group paths

```bash
SRC_PATH=$(curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN/groups/$SRC_GROUP" | jq -r '.path')
DST_PATH=$(curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN/groups/$DST_GROUP" | jq -r '.path')
```

Use the server-returned `path`, don't hand-build it. A path that doesn't resolve is accepted at write time and then silently never realises. Empty or `null` here means the group isn't in this domain — stop.

## 3. Create the security policy (the container)

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY" \
  -d "$(jq -n --arg dst "$DST_PATH" '{
    display_name: "Block RDP app-tier to db-tier",
    category: "Application",
    sequence_number: 100,
    stateful: true,
    scope: [$dst]
  }')"
```

`PATCH` is create-or-update and needs no `_revision`. `PUT` works too, but only if you omit `_revision` on create and supply it on every update.

## 4. Create the rule inside that policy

```bash
curl -sS -X PATCH "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE" \
  -d "$(jq -n --arg src "$SRC_PATH" --arg dst "$DST_PATH" '{
    display_name: "Deny RDP 3389",
    action: "DROP",
    source_groups: [$src],
    destination_groups: [$dst],
    service_entries: [{
      resource_type: "L4PortSetServiceEntry",
      display_name: "tcp-3389",
      l4_protocol: "TCP",
      destination_ports: ["3389"]
    }],
    scope: [$dst],
    direction: "IN_OUT",
    ip_protocol: "IPV4_IPV6",
    sequence_number: 10,
    logged: true
  }')"
```

There is no top-level rule endpoint — a rule only exists under a security policy under a domain. Inline `service_entries` avoids depending on a predefined RDP service object. Use `REJECT` instead of `DROP` if you want clients to fail fast rather than time out.

## 5. Verify, then log out

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE"
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE/statistics"
curl -sS -X POST "${AUTH[@]}" "$NSX/api/session/destroy"
```

The statistics endpoint is the real confirmation — it shows the rule is programmed in the data path and gives hit counts.

## Three things that will actually bite

1. **You need Enterprise Admin.** Auditor is read-only and the write fails. Check with `GET /api/v1/aaa/role-bindings` rather than testing by writing.
2. **Session expiry returns 403, not 401** (default timeout 1800s), and session cookies are bound to a single manager node — behind a VIP a cookie minted on node A fails on node B, also as 403. Re-auth on 403, retry once; if it's still 403, it's the role.
3. **Rule ordering.** Category `Application` is the lowest of the four L3 categories, so an existing Emergency/Infrastructure/Environment policy that allows this flow will win. If that's a risk, check with `GET /policy/api/v1/infra/firewall/rules` first, or reposition using `POST .../rules/$RULE?action=revise&operation=insert_top` (body is mandatory — it's a move-with-replace).

Confirm `$DOMAIN` with `GET /policy/api/v1/infra/domains/$DOMAIN` if this is a multi-tenant or federated deployment; project-scoped objects live under `/orgs/{org}/projects/{project}/infra/...` and won't be found via `/infra/`.

This is a production firewall change and the above is derived from Broadcom documentation and the published 9.1 spec, not from a live run — if a mistake here would be hard to unwind, stage it as a draft (`PATCH /policy/api/v1/infra/drafts/{id}`, preview with `GET .../complete`, then `?action=publish`). Say the word and I'll write that variant.
