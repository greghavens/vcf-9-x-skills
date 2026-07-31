# Blocking RDP (tcp/3389) app-tier → db-tier with the NSX Policy API (VCF 9.1)

Short version: this is a Distributed Firewall (DFW) rule. You'll create a **Security Policy** (the section) containing one **Rule** with `action: DROP` (or `REJECT`), source = your app-tier group, destination = your db-tier group, service = RDP. In the Policy API you can do the whole thing in a single `PATCH`.

Throughout, `NSX=https://<nsx-manager-vip-or-fqdn>`. In VCF 9.1 you should target the **NSX Manager cluster VIP**, not an individual node.

---

## 1. Authentication

NSX Manager supports three approaches. Pick one.

### Option A — Session-based auth (recommended for scripting)

This is the most portable and is what I'd use. Note the session endpoint lives under `/api/session/`, **not** `/policy/api/v1/`, and it takes form-encoded data, not JSON.

```bash
NSX="https://nsx-mgr.example.local"
NSX_USER='admin'
NSX_PASS='<password>'

# Log in; capture the session cookie and the XSRF token
curl -sS -k -c /tmp/nsx-cookies.txt -D /tmp/nsx-headers.txt \
  -X POST "$NSX/api/session/create" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "j_username=$NSX_USER" \
  --data-urlencode "j_password=$NSX_PASS"

# Pull the XSRF token out of the response headers
XSRF=$(awk 'BEGIN{IGNORECASE=1}/^x-xsrf-token:/{print $2}' /tmp/nsx-headers.txt | tr -d '\r')
echo "XSRF token: $XSRF"
```

Every subsequent call then needs **both** the cookie and the token:

```bash
curl -sS -k -b /tmp/nsx-cookies.txt \
  -H "X-XSRF-TOKEN: $XSRF" \
  -H 'Content-Type: application/json' \
  "$NSX/policy/api/v1/infra/domains/default/groups"
```

Clean up when you're done:

```bash
curl -sS -k -b /tmp/nsx-cookies.txt -H "X-XSRF-TOKEN: $XSRF" \
  -X POST "$NSX/api/session/destroy"
```

The XSRF token is only required for state-changing verbs (POST/PUT/PATCH/DELETE), but sending it on GETs too is harmless and keeps your script uniform.

### Option B — HTTP Basic auth (quickest for one-off / interactive work)

```bash
curl -sS -k -u "$NSX_USER:$NSX_PASS" \
  -H 'Content-Type: application/json' \
  "$NSX/policy/api/v1/infra/domains/default/groups"
```

Two caveats worth knowing before you build anything on this:

- Basic auth creates a fresh authentication context on **every** request, which is measurably slower and puts more load on the manager. VMware's own guidance is to prefer session auth for anything loop-y or automated.
- Hardened / recent NSX builds increasingly restrict or disable basic auth for non-local accounts, and it interacts poorly with SSO-backed users. If Basic returns 403 while the same credentials work in the UI, that's your answer — switch to Option A or C.

### Option C — SSO / bearer token

If your NSX is integrated with vCenter SSO or the VCF identity provider (typical in a VCF 9.1 deployment, and required if you're using an AD/LDAP or federated account rather than the local `admin`), you exchange an identity token and then present it as a bearer token:

```bash
curl -sS -k -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  "$NSX/policy/api/v1/infra/domains/default/groups"
```

I'd verify the exact token-acquisition endpoint for your specific 9.1 build and IdP configuration against your deployment's docs rather than taking a generic snippet from me — this is the part of the auth story that has moved the most across VCF 9.x, and the right endpoint depends on whether you're fronted by vCenter SSO, VCF Operations, or a direct OIDC provider. The session and basic paths above are stable and will get you working immediately.

### Permissions

Whichever account you use needs **Enterprise Admin** or **Security Admin**. A Network Admin or Auditor role will authenticate fine and then hand you a 403 on the write.

### TLS

I've used `-k` above so you can get moving. For anything that runs unattended, drop `-k` and pin the CA properly:

```bash
curl --cacert /path/to/nsx-ca.pem ...
```

---

## 2. Find the exact paths of your two groups

Don't guess the group IDs — the display name you see in the UI is usually **not** the ID. Look them up:

```bash
curl -sS -k -b /tmp/nsx-cookies.txt -H "X-XSRF-TOKEN: $XSRF" \
  "$NSX/policy/api/v1/infra/domains/default/groups" \
  | jq -r '.results[] | "\(.display_name)\t\(.path)"'
```

You're looking for the `path` field, which will look like:

```
/infra/domains/default/groups/app-tier
/infra/domains/default/groups/db-tier
```

Two things to watch for:

- **Domain.** `default` is the standard domain, but if your environment uses multiple domains (or Global Manager / federation), enumerate with `GET /policy/api/v1/infra/domains` first and substitute the right one everywhere below.
- **Group scope.** Groups created under a VPC in VCF 9.x live at a different path (`/orgs/.../projects/.../vpcs/...`) and are not directly usable in a default-domain DFW policy. If your `jq` above doesn't list the groups, that's likely why.

Set them as variables:

```bash
APP="/infra/domains/default/groups/app-tier"
DB="/infra/domains/default/groups/db-tier"
```

---

## 3. Decide how to express "tcp/3389"

Two valid ways.

**(a) Use the built-in RDP service.** NSX ships with a predefined service for RDP. Confirm its path before you reference it:

```bash
curl -sS -k -b /tmp/nsx-cookies.txt -H "X-XSRF-TOKEN: $XSRF" \
  "$NSX/policy/api/v1/infra/services?include_mark_for_delete_objects=false" \
  | jq -r '.results[] | select(.display_name|test("RDP";"i")) | "\(.display_name)\t\(.path)"'
```

You'll typically get `/infra/services/RDP`. Verify that it's actually TCP/3389 only and hasn't been edited locally — predefined services are editable and I've seen environments where someone widened one.

**(b) Define the ports inline on the rule.** This is self-contained and removes any dependency on what a shared service object happens to contain today. I lean toward this for a targeted block rule. It's the form I'll use below.

```json
"services": ["ANY"],
"service_entries": [
  {
    "resource_type": "L4PortSetServiceEntry",
    "display_name": "tcp-3389",
    "l4_protocol": "TCP",
    "destination_ports": ["3389"]
  }
]
```

Note that when you supply `service_entries`, you set `services` to `["ANY"]` — the inline entries are what actually match. Also note only `destination_ports` is constrained; leaving source ports unset matches any ephemeral source port, which is what you want.

---

## 4. Create the policy and rule (one call)

A `PATCH` against the security policy path creates the section and its rule together, and is idempotent — re-running it updates in place rather than creating duplicates. This is the call you actually want.

```bash
curl -sS -k -b /tmp/nsx-cookies.txt \
  -H "X-XSRF-TOKEN: $XSRF" \
  -H 'Content-Type: application/json' \
  -X PATCH \
  "$NSX/policy/api/v1/infra/domains/default/security-policies/block-rdp-app-to-db" \
  -d @- <<EOF
{
  "display_name": "Block RDP app-tier to db-tier",
  "description": "Deny tcp/3389 from app-tier to db-tier",
  "category": "Application",
  "stateful": true,
  "sequence_number": 100000,
  "scope": [ "$DB" ],
  "rules": [
    {
      "id": "block-rdp-app-to-db",
      "display_name": "Block RDP app-tier to db-tier",
      "sequence_number": 10,
      "source_groups": [ "$APP" ],
      "destination_groups": [ "$DB" ],
      "services": [ "ANY" ],
      "service_entries": [
        {
          "resource_type": "L4PortSetServiceEntry",
          "display_name": "tcp-3389",
          "l4_protocol": "TCP",
          "destination_ports": [ "3389" ]
        }
      ],
      "scope": [ "$DB" ],
      "action": "DROP",
      "direction": "IN_OUT",
      "ip_protocol": "IPV4_IPV6",
      "logged": true,
      "tag": "BLOCK-RDP"
    }
  ]
}
EOF
```

A 200 with the policy body back means the intent was accepted. That is **not** the same as it being enforced — see step 5.

### Why each field is set the way it is

- **`category: "Application"`** — DFW categories are evaluated in a fixed order: Ethernet → Emergency → Infrastructure → Environment → Application. Application is the right home for a workload-to-workload rule like this. Putting it in Emergency would let it pre-empt everything, which is overkill here and a habit that causes trouble later.
- **`sequence_number` (policy: 100000)** — controls where this section sits relative to other sections in the same category. Lower numbers evaluate first. If you already have an Application-category section that permits broad app→db traffic, **this section must sort before it** or the permit wins and your block never fires. Check what's there:
  ```bash
  curl -sS -k -b /tmp/nsx-cookies.txt -H "X-XSRF-TOKEN: $XSRF" \
    "$NSX/policy/api/v1/infra/domains/default/security-policies" \
    | jq -r '.results[] | "\(.sequence_number)\t\(.category)\t\(.display_name)"' | sort -n
  ```
  This is the single most common reason a correctly-written block rule appears to do nothing.
- **`scope` (applied-to)** — set on both the policy and the rule to the db-tier group. This is the important optimisation: without it, `scope` defaults to DFW-wide and the rule gets pushed to the vNIC of **every** VM in the environment. Scoping to db-tier means only those VMs carry the rule. On a large estate this is the difference between a cheap change and a meaningful hit to rule-table size on every host.
- **`action: "DROP"`** — silently discards. The RDP client hangs until it times out (~20s). Use **`"REJECT"`** instead if you'd rather the client fail fast with a TCP RST; that's friendlier for troubleshooting and for anyone who legitimately hits the rule, at the cost of confirming to a prospective attacker that something is filtering. For an internal tiering control I'd usually pick `REJECT`; for anything internet-facing, `DROP`.
- **`direction: "IN_OUT"`** — with an applied-to of db-tier, this catches the traffic as it arrives at the destination vNIC. Safe default.
- **`ip_protocol: "IPV4_IPV6"`** — covers both. Worth being explicit: if your db-tier VMs have IPv6 addresses and you scope to IPv4 only, RDP over v6 sails straight through.
- **`logged: true`** — turn this on at least initially so you can confirm the rule is matching. Logs land in the ESXi host `dfwpktlogs.log` and in whatever you're forwarding syslog to. Consider turning it off once you've validated, if the volume is high.
- **`stateful: true`** — normal for TCP; return traffic is handled automatically by connection tracking.

---

## 5. Verify

**Read the rule back:**

```bash
curl -sS -k -b /tmp/nsx-cookies.txt -H "X-XSRF-TOKEN: $XSRF" \
  "$NSX/policy/api/v1/infra/domains/default/security-policies/block-rdp-app-to-db" | jq .
```

**Check realization — this is the step people skip.** A 200 on the PATCH only means NSX accepted your *intent*. Realization onto the hosts is asynchronous and can fail independently:

```bash
curl -sS -k -b /tmp/nsx-cookies.txt -H "X-XSRF-TOKEN: $XSRF" \
  "$NSX/policy/api/v1/infra/realized-state/status?intent_path=/infra/domains/default/security-policies/block-rdp-app-to-db" | jq .
```

You want `"consolidated_status": "SUCCESS"`. Anything else (`IN_PROGRESS`, `ERROR`) means it isn't enforced yet. Poll until it settles.

**Confirm group membership is what you think it is.** A block rule against an empty or stale group is a no-op that looks like success:

```bash
curl -sS -k -b /tmp/nsx-cookies.txt -H "X-XSRF-TOKEN: $XSRF" \
  "$NSX/policy/api/v1/infra/domains/default/groups/db-tier/members/virtual-machines" | jq -r '.results[].display_name'
```

Do the same for `app-tier`. If these are tag-based dynamic groups, verify a representative VM actually carries the tag.

**Then test for real** — from a VM in app-tier, `Test-NetConnection -ComputerName <db-vm> -Port 3389` (or `nc -zv <db-vm> 3389`). Confirm it fails, and equally importantly confirm that some *other* app→db port you rely on still works, so you know you haven't over-blocked.

---

## Things that will bite you

- **Existing permit rules earlier in the order.** Covered above, but it's worth repeating because it's the number one cause of "I made the rule and nothing changed." Order beats intent, every time.
- **Existing sessions aren't torn down.** DFW is stateful. An RDP session established *before* you applied the rule will keep flowing until it's closed, because it already has a conntrack entry. If you need existing sessions killed, you have to clear the relevant connection state — plan for that if this is an incident response action rather than a hardening change.
- **Jump hosts and management paths.** Confirm that whatever you or your admins use to reach db-tier VMs isn't sourced from something inside app-tier. If your bastion happens to be a member of the app-tier group, you're about to lock yourself out of RDP to the database servers. Check group membership *before* you apply, not after.
- **`PATCH` vs `PUT`.** `PATCH` merges and leaves rules you didn't mention alone. `PUT` replaces the whole policy — any rules in that section not present in your body get **deleted**. If you're editing a section that already has rules in it, use `PATCH`.
- **`id` vs `display_name`.** The `id` I set (`block-rdp-app-to-db`) is the immutable path key. Choose it deliberately; renaming later means delete-and-recreate.
- **Do this in a change window with a rollback ready.** Deleting is a single call if you need to back out:
  ```bash
  curl -sS -k -b /tmp/nsx-cookies.txt -H "X-XSRF-TOKEN: $XSRF" \
    -X DELETE \
    "$NSX/policy/api/v1/infra/domains/default/security-policies/block-rdp-app-to-db"
  ```
  If you only want to disable rather than remove, `PATCH` the rule with `"disabled": true` — that preserves the object and its history.

---

## One note on scope of this answer

The Policy API surface used above (`/policy/api/v1/infra/domains/{domain}/security-policies/...`) has been stable across NSX 3.x through the NSX bundled with VCF 9.x, so these calls should work as written on 9.1. The area I'd double-check against your own deployment's documentation is **Option C, the SSO/bearer token flow** — federated auth is the piece that has genuinely changed across VCF 9.x releases and depends on your identity provider setup. If you're using the local `admin` account, Option A works today and you can ignore that caveat entirely.

Also, if your db-tier workloads live inside a **VPC** rather than the default domain, the object paths differ and the DFW model is VPC-scoped; tell me if that's the case and the calls change accordingly.
