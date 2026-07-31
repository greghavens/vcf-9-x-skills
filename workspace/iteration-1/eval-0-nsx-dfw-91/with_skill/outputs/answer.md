# Blocking RDP (tcp/3389) from app-tier to db-tier — NSX DFW on VCF 9.1

Version pinned to **VCF 9.1 / NSX 9.1.0.0** (build 25318225) as you stated. Everything below is
scoped to 9.1 only — do not reuse it on a 9.0 estate, where the evidence base is different.

Two things to get right before you paste anything:

1. **A firewall rule is not a top-level object.** There is no `POST /policy/api/v1/rules` and no
   `.../domains/default/rules`. A rule lives inside a **security policy**, which lives inside a
   **domain**. The only way to create one is a `PUT`/`PATCH` at
   `/infra/domains/{domain-id}/security-policies/{policy-id}/rules/{rule-id}`, or by embedding it in
   the policy's `rules` array.
2. **Everything goes through the Policy API (`/policy/api/v1`).** Beginning with VCF 9.0 the NSX
   Manager provides a single mode — Policy mode. The Manager API (`/api/v1`) from NSX 4.x and earlier
   is no longer supported for policy objects; it survives only for node/cluster/fabric admin, session
   lifecycle and OpenAPI spec retrieval. If you have an inherited script that creates DFW objects
   under `/api/v1`, or one that uses `communication-maps`, both are dead ends — `communication-maps`
   is present in the 9.1 spec but every operation on it is marked deprecated.

---

## Authentication

NSX uses a session-cookie flow, spec-confirmed for 9.1 as `CreateAuthenticatedSession`:

```
POST https://<nsx-manager>/api/session/create
Content-Type: application/x-www-form-urlencoded

j_username=<user>&j_password=<password>
```

Note the path is `/api/session/create` **verbatim** — it is declared as an absolute path and does
*not* sit under the `/api/v1` base path. Do not insert `v1`.

The response carries both a `Set-Cookie: JSESSIONID=...` and an `X-XSRF-TOKEN` header:

```
set-cookie: JSESSIONID=57021338F5FDB766121F51BB5E1B82C3; Path=/; Secure; HttpOnly; SameSite=Lax
x-xsrf-token: 8bf06253-c246-4e4b-a379-f218dd0a193c
```

**Both must be sent on every subsequent call.** Sending only the cookie is the single most common
mistake, and it fails in a way that reads like a permissions problem.

```
Cookie: JSESSIONID=<value>
X-XSRF-TOKEN: <value>
```

Three traps worth knowing before you debug anything:

- **Session expiry surfaces as HTTP 403, not 401.** Documented verbatim in the 9.1 admin guide.
  Default inactivity timeout is 1800 s (30 minutes) — that comes from the `ApiServiceConfig.session_timeout`
  schema default in the 9.1 spec. A client that only re-authenticates on 401 will spin on 403 forever.
  Re-authenticate on 403 and retry once; if the retry is also 403, it is a role problem, not expiry.
- **The session cookie is bound to a single manager node.** Behind a cluster VIP or load balancer, a
  cookie minted on node A fails on node B — again as a 403, indistinguishable from expiry. Pin your
  client to one node's address for the whole sequence.
- **URL-encode the password.** `+` and other special characters break the form encoding otherwise.

Alternatives, if the session flow does not suit you: **HTTP Basic** is supported and is in fact the
only security scheme declared in the 9.1 NSX policy spec (`BasicAuth`). For non-interactive service
accounts on 9.1, the preferred route is a **token-based principal identity** bound to a VIDB OIDC
identity (`POST /api/v1/trust-management/token-principal-identities`, after configuring a VIDB OIDC
endpoint). Be aware of an honest gap there: the configuration surface is spec-confirmed, but the
**wire format of the resulting authenticated request** — header name, token type, whether NSX still
demands `X-XSRF-TOKEN` alongside it — is not documented in either the 9.1 spec or the prose doc set.
Confirm it against your appliance before building on it. The session flow below is the one that can
be evidenced end to end.

On TLS: VCF appliances ship VMCA-signed certificates that no client trusts by default, so your first
call will likely fail chain validation. The documented fix is to trust or replace the certificate,
not to disable verification. The `-k` in the examples below is there so the commands run as-is while
you are prototyping — against a management plane holding infrastructure credentials, that is a
different risk from doing it against a test API, so drop `-k` and add the VMCA root to your trust
store before this goes anywhere near a pipeline.

---

## Prerequisites — check these first, they are most of the work

| # | Must be true | Non-destructive check |
|---|---|---|
| P1 | HTTPS reachability with a trusted chain | `curl -sS -o /dev/null -w '%{http_code}\n' https://<nsx>/api/v1/spec/openapi/nsx_policy_api.json` **without** `-k` |
| P2 | Cookie-based auth enabled on the API service | `GET /api/v1/cluster/api-service` → `cookie_based_authentication_enabled` (spec default `true`). If `false`, `/api/session/create` will not mint sessions — fall back to Basic or client cert |
| P3 | You hold **Enterprise Admin** (`enterprise_admin`) | `GET /api/v1/aaa/role-bindings` and read your binding. **Do not test write permission by attempting the production write** — that verifies a firewall permission by changing the firewall. Auditor (`auditor`) is read-only and will not do |
| P4 | The domain exists and you have the right id | `GET /policy/api/v1/infra/domains` — `default` is a convention, not a guarantee |
| P5 | Both groups exist, and you use their **server-returned `path`** | `GET /policy/api/v1/infra/domains/{domain}/groups/{group}` and record `.path` |
| P6 | You know your service representation | Inline `service_entries` (used below) avoids depending on a predefined RDP `Service` object existing |

P5 is the one that quietly bites. Rules reference groups by **policy path string**
(`/infra/domains/default/groups/app-tier`), not by name and not by UUID. A path that does not resolve
is not always a 400 at write time — it can be accepted and then simply never realise. Capture the
`path` the server returns rather than assembling the string yourself; project-scoped and Federation-scoped
groups have longer paths.

One more, worth stating plainly: **there is no authoritative published list of which NSX objects VCF
owns and which you may change directly.** DFW security policies, rules and groups are user-authored
security constructs and are the normal target of Policy API automation, so you are on solid ground
here — but that split is an inference, not a documented rule. If you want to check a specific object,
read it and inspect `_system_owned`, `_protection` and `_create_user`.

---

## The call sequence

```bash
NSX=https://nsx-mgr.example.com
DOMAIN=default          # verify in Step 1 — do NOT assume
SRC_GROUP=app-tier      # your group IDs, not display names
DST_GROUP=db-tier
POLICY=block-rdp-app-to-db
RULE=deny-rdp
```

Every path below is derived from `$DOMAIN` and from the group paths the server returns. Nothing
hard-codes `default`.

### Step 0 — Authenticate

```bash
curl -sS -k -c /tmp/nsx-session.txt -D /tmp/nsx-headers.txt \
  -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'j_username=svc-nsx-automation@example.com' \
  --data-urlencode 'j_password=<password>' \
  "$NSX/api/session/create"

XSRF=$(grep -i '^x-xsrf-token:' /tmp/nsx-headers.txt | tr -d '\r' | awk '{print $2}')

AUTH=(-k -b /tmp/nsx-session.txt -H "x-xsrf-token: $XSRF" -H 'Content-Type: application/json')
```

Keep every call below pointed at the **same manager node address**.

### Step 1 — Confirm the domain (P4)

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/domains/$DOMAIN"
```

`GET /policy/api/v1/infra/domains/{domain-id}` — operationId `ReadDomainForInfra`. Expect 200.

### Step 2 — Confirm both groups and capture their paths (P5)

```bash
SRC_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/groups/$SRC_GROUP" | jq -r '.path')
DST_PATH=$(curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/groups/$DST_GROUP" | jq -r '.path')

# Fail closed: an empty or null path means the group does not exist in THIS domain.
for v in SRC_PATH DST_PATH; do
  case "${!v}" in
    ''|null) echo "FATAL: $v unresolved in domain '$DOMAIN' — fix before continuing" >&2; exit 1 ;;
  esac
done

printf 'source: %s\ndest:   %s\n' "$SRC_PATH" "$DST_PATH"
```

`GET /policy/api/v1/infra/domains/{domain-id}/groups/{group-id}` — `ReadGroupForDomain`.
With `DOMAIN=default` this prints `/infra/domains/default/groups/app-tier` and
`/infra/domains/default/groups/db-tier`.

### Step 3 — Create the security policy (the container)

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

`PATCH /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}` —
`PatchSecurityPolicyForDomain`.

Why `PATCH` and not `PUT`: `PATCH` is create-or-update and does not require `_revision`. `PUT` also
works, but only if you **omit** `_revision` on the creating call and **supply** the current value on
every subsequent one — the API rejects a `PUT` whose `_revision` does not match.

Note the `jq -n --arg` construction. A single-quoted `-d '{...}'` would not expand `$DST_PATH` at
all, which is exactly how a domain-parameterised script ends up writing literal `default` paths.

### Step 4 — Create the rule inside that policy

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

`PATCH /policy/api/v1/infra/domains/{domain-id}/security-policies/{security-policy-id}/rules/{rule-id}`
— `PatchSecurityRule`.

Field notes:

- `action: "DROP"` silently discards, so RDP clients see a timeout. Use `"REJECT"` if you would
  rather they get an immediate RST — much kinder to whoever files the ticket. Both are valid
  `Rule.action` enum values (`ALLOW`, `DROP`, `REJECT`, `JUMP_TO_APPLICATION`).
- Inline `service_entries` avoids depending on a predefined RDP `Service` object existing. The
  alternative is `"services": ["/infra/services/RDP"]`, which requires you to first confirm that
  service id via `GET /policy/api/v1/infra/services`.
- `l4_protocol` is the only required field of `L4PortSetServiceEntry`; `destination_ports` is what
  makes it 3389.
- `scope` is the "Applied To" field. Scoping to db-tier limits which vNICs get the rule programmed,
  which matters for DFW rule-count scale. Omit it to inherit the policy's scope.
- `logged: true` gives you evidence the rule is matching. Turn it off later if volume is a problem.

**One-call alternative:** `SecurityPolicy.rules` is an array of `Rule`, so Steps 3 and 4 collapse
into a single `PATCH` on the security policy with the rule nested under `rules`. That is atomic at
the policy level and is the better choice when creating a policy and its rules together. It is *not*
a way to add one rule to an existing policy — a `PUT` with a partial `rules` array removes the rules
you left out.

### Step 5 — Verify realization

```bash
curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE"

curl -sS "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE/statistics"
```

`ReadSecurityRule` and `GetRuleStatistics`. A 200 on the read confirms the object exists; the
statistics endpoint confirms it is programmed in the data path and gives you hit counts — that is
your proof the block is actually working, not just configured.

### Step 6 — Position the rule, if order matters

```bash
curl -sS -X POST "${AUTH[@]}" \
  "$NSX/policy/api/v1/infra/domains/$DOMAIN/security-policies/$POLICY/rules/$RULE?action=revise&operation=insert_top" \
  -d '<the full Rule body from step 5>'
```

`ReviseSecurityRule`. The **body is mandatory** — `?action=revise` is a move-with-replace, not a pure
move, so read the rule first and post it back with the position parameters. `operation` accepts
`insert_top` (default), `insert_bottom`, `insert_after`, `insert_before`; the latter two need
`anchor_path`.

### Step 7 — Log out

```bash
curl -sS -X POST "${AUTH[@]}" "$NSX/api/session/destroy"
```

`DestroyAuthenticatedSession`. Send the cookie and the XSRF header on this call too.

---

## Ordering — why a correct rule can still never match

Three mechanisms stack, in this precedence order:

1. **Category** on the security policy. The five categories are Ethernet (L2), then for L3:
   **Emergency → Infrastructure → Environment → Application**. A policy with no category has the
   least precedence of all.
2. **`sequence_number` on the policy** — orders policies within a category.
3. **`sequence_number` on the rule** — orders rules within a policy.

The example uses `category: "Application"`, which is the normal home for app-to-app microsegmentation
but is also the **lowest-precedence** L3 category. If an existing Emergency, Infrastructure or
Environment policy already allows app-tier → db-tier broadly, your DROP will never be reached. Before
you conclude the rule is broken, check what else is in front of it:

```bash
curl -sS "${AUTH[@]}" "$NSX/policy/api/v1/infra/firewall/rules"
```

`GetFilteredRules` gives you a flat, filtered view across domains — much better than walking every
policy by hand.

---

## Worth considering: stage this as a draft

You are adding a DROP rule, which is comparatively safe — the blast radius of a mistake here is
"RDP still works" rather than "I severed my own management session". But NSX supports **firewall
drafts**, and they are cheap enough to be worth knowing about, especially if this rule is one of
several changes going in together:

| Verb | Path (append to `/policy/api/v1`) |
|---|---|
| GET/PUT/PATCH/DELETE | `/infra/drafts[/{draft-id}]` |
| GET | `/infra/drafts/{draft-id}/complete` |
| POST | `/infra/drafts/{draft-id}?action=publish` |

`/complete` is the pre-flight: it returns the configuration **as it would look after publish**, a dry
run that touches nothing. That is the closest thing to a safe impact check the API offers. For any
change large enough that unwinding it by hand would be unpleasant, stage it, read `/complete`, then
publish as a unit.

---

## If something goes wrong

| Symptom | Most likely cause |
|---|---|
| 403 on Step 1, right after a successful Step 0 | `X-XSRF-TOKEN` not sent |
| 403 mid-sequence after a pause | Session expired — it is 403, **not** 401. Re-auth, retry once |
| 403 that persists after re-auth | Role too low; you need Enterprise Admin to write |
| 403 on some calls, seemingly at random | Cookie used against a different cluster node behind a VIP |
| 404 on Step 3 | Wrong `{domain-id}`, or you are on a project-scoped deployment and need the `orgs/{org}/projects/{project}/infra/...` path family |
| 200 on Step 4 but traffic still flows | Groups are empty, `scope` excludes the workloads, or a higher-precedence policy already allows the flow |
| Rule accepted but never realizes | A group path in `source_groups`/`destination_groups` does not resolve — re-read the group `path` |
| 429 | Per-client rate limit. The exact ceiling is conflicted between the 9.1 spec and prose (100 vs 250 req/s), so read the live value from `GET /api/v1/cluster/api-service` rather than assuming |

---

## Provenance and caveats

Every endpoint and operationId cited above was confirmed against the NSX OpenAPI specification at the
`9.1.0.0` tag of Broadcom's spec repository (`nsx_policy_api.yaml`, `basePath: /policy/api/v1`,
3,729 operations), with the auth behaviours (403-on-expiry, node-bound cookies) coming from
version-pinned Broadcom prose. **None of it has been executed against a live NSX.**

Two caveats specific to this answer:

- If your deployment is **multi-tenant or federated**, the `/infra/...` paths above are the wrong
  family. Project-scoped objects live under `/orgs/{org-id}/projects/{project-id}/infra/...` and VPC
  policies under `.../vpcs/{vpc-id}/security-policies`; reading a project-scoped policy through
  `/infra/` returns 404. Federated (`global-infra`) DFW paths are **read-only** on a local manager —
  writing to a federated policy means talking to the Global Manager appliance
  (`/global-manager/api/v1`).
- Firewall changes are production-affecting. Verify against Broadcom's documentation for your exact
  build before executing, and confirm the rule with the `/statistics` endpoint rather than assuming
  a 200 on the write means traffic is actually being dropped.
