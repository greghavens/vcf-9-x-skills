# Blocking TCP/3389 between two existing NSX groups (VCF 9.0)

Short version: this is a single distributed firewall (DFW) rule — source = group A, destination = group B, service = RDP (tcp/3389), action Drop or Reject, published into a category that sits above whatever allow rule currently matches. The concept is stable and I'm confident about it. The part I'd want you to verify before pasting anything into production is the **exact object paths in your environment** — see the confidence section at the end, which is the honest answer to your second question.

---

## 1. What I need from you to make this exact

I can't produce a copy-paste-ready call without these:

| Item | Why it matters |
|---|---|
| The two group IDs (not display names) | The rule references `/infra/domains/default/groups/<id>`; display names are not paths |
| Whether the groups live in the **default domain** or inside an **NSX Project / VPC** | Changes the whole path prefix (see below) |
| Whether this NSX is standalone or behind a **Global Manager** (Federation) | Federation uses `/global-infra/...`, not `/infra/...` |
| Existing DFW policy (section) you want the rule in, or "create a new one" | Determines whether you PATCH a rule into an existing policy or create the policy too |
| Direction intent: A→B only, or both ways | Two rules vs. one, or a rule pair |
| Drop vs. Reject | Drop = silent timeout; Reject = TCP RST, fails fast for legitimate users |

---

## 2. UI path (verified against the 9.0 documentation)

1. Log in to **NSX Manager** as Enterprise Admin.
2. **Security > Distributed Firewall**.
3. Pick the category — normally **Application** for workload-to-workload rules. (Categories evaluate in order: Ethernet, Emergency, Infrastructure, Environment, Application.)
4. **Add Policy**, name it, then **Add Rule** under it.
5. Fill in:
   - **Sources** → group A
   - **Destinations** → group B
   - **Services** → `RDP` (the built-in service, tcp/3389)
   - **Applied To** → set to the two groups rather than leaving it DFW-wide; this limits how far the rule is pushed
   - **Action** → Drop (or Reject)
   - Gear icon → enable **Logging**, leave **Direction** at In/Out unless you have a reason not to
6. **Publish**. Nothing takes effect until you publish.

In VCF 9.0 this feature is branded **vDefend Distributed Firewall**; the docs live under vDefend, but the NSX Manager UI navigation string is still `Security > Distributed Firewall`.

---

## 3. API path (Policy API)

Important for 9.0: **the old Manager API (`/api/v1/firewall/...`) is no longer supported in NSX 9.0.** Use the Policy API (`/policy/api/v1/...`) only. If you have automation left over from NSX 3.x that hits `/api/v1/firewall/sections`, that is the thing most likely to break on this platform.

### 3a. Verify first (do these GETs before any write)

```bash
NSX=https://<nsx-manager-fqdn>

# Confirm the two groups exist and grab their exact paths
curl -sk -u "$NSXUSER:$NSXPASS" "$NSX/policy/api/v1/infra/domains/default/groups" \
  | jq -r '.results[] | "\(.display_name)\t\(.path)"'

# Confirm the built-in RDP service and its port definition
curl -sk -u "$NSXUSER:$NSXPASS" "$NSX/policy/api/v1/infra/services/RDP" | jq .

# See existing policies so you can place the rule correctly in the ordering
curl -sk -u "$NSXUSER:$NSXPASS" \
  "$NSX/policy/api/v1/infra/domains/default/security-policies" \
  | jq -r '.results[] | "\(.category)\t\(.sequence_number)\t\(.display_name)\t\(.path)"'
```

If the first command returns nothing useful, your groups are almost certainly scoped to a Project/VPC — retry under `/policy/api/v1/orgs/default/projects/<project-id>/infra/domains/default/groups`.

### 3b. Create the rule (idempotent PATCH on a chosen rule ID)

```bash
curl -sk -u "$NSXUSER:$NSXPASS" -X PATCH \
  -H 'Content-Type: application/json' \
  "$NSX/policy/api/v1/infra/domains/default/security-policies/<policy-id>/rules/block-rdp-a-to-b" \
  -d '{
    "display_name": "Block RDP from GroupA to GroupB",
    "source_groups": ["/infra/domains/default/groups/<GROUP-A-ID>"],
    "destination_groups": ["/infra/domains/default/groups/<GROUP-B-ID>"],
    "services": ["/infra/services/RDP"],
    "scope": [
      "/infra/domains/default/groups/<GROUP-A-ID>",
      "/infra/domains/default/groups/<GROUP-B-ID>"
    ],
    "action": "DROP",
    "direction": "IN_OUT",
    "ip_protocol": "IPV4_IPV6",
    "logged": true,
    "sequence_number": 10
  }'
```

`scope` is the API name for **Applied To**. Including both groups is the safer default: it enforces at both vNIC sides while keeping the rule off every other host in the transport zone.

### 3c. If you'd rather not depend on the built-in service object

Define tcp/3389 inline on the rule instead. This removes one uncertainty (whether the built-in service ID is exactly `RDP` in your build) at the cost of a slightly less readable rule:

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

### 3d. If the policy section doesn't exist yet

```bash
curl -sk -u "$NSXUSER:$NSXPASS" -X PATCH \
  -H 'Content-Type: application/json' \
  "$NSX/policy/api/v1/infra/domains/default/security-policies/block-rdp-policy" \
  -d '{
    "display_name": "Block RDP",
    "category": "Application",
    "sequence_number": 100,
    "scope": ["ANY"],
    "rules": [ { ...the rule object from 3b... } ]
  }'
```

A PATCH on a security-policy with an embedded `rules` array creates policy and rules in one shot.

---

## 4. Things that will bite you

- **Ordering.** The rule only matters if it is evaluated before the allow rule that currently permits the traffic. Check category first, then `sequence_number` within category. A "block" rule sitting below a broad "allow any any" in the same category does nothing.
- **DFW exclusion list.** Any VM on the exclusion list is not filtered at all. Check `Security > Distributed Firewall > Actions > Exclusion List`.
- **Group overlap.** If a VM is a member of both groups, RDP between two such VMs matches this rule in both directions. Worth checking before you publish.
- **Only NSX-attached workloads are covered.** DFW enforces at the vNIC. Anything reaching those VMs from outside NSX-managed segments via a path the DFW doesn't see (physical, or a non-prepared host) isn't covered by this rule.
- **Reject vs Drop for RDP.** Reject gives a fast, unambiguous failure for a user who is supposed to be blocked. Drop looks like a network problem and generates helpdesk tickets. Drop is the right choice if you're trying not to advertise the control.
- **Logging.** Turn it on for at least the first few weeks, with a `tag`/log label, so you can prove what the rule caught.
- **Verify with the trace tools** rather than trusting the rule text: Traceflow, or DFW live traffic / rule hit counters.

---

## 5. How confident am I in the exact endpoints?

Splitting this honestly, because the confidence is very uneven:

**High confidence (I'd act on this without checking):**
- The Policy API is the correct and only supported surface on NSX 9.0 / VCF 9.0; the Manager API `/api/v1/firewall/...` is out. This is documented in the VCF 9.0 NSX support notes.
- The general shape `PATCH /policy/api/v1/infra/domains/default/security-policies/<policy-id>/rules/<rule-id>` with `source_groups` / `destination_groups` / `services` / `scope` / `action`. This shape has been stable across NSX 3.x, 4.x and 9.x.
- The UI navigation `Security > Distributed Firewall` and the field names (Sources, Destinations, Services, Applied To, Action, Publish) — I checked this against the 9.0 vDefend documentation.
- That the correct answer here is one DFW rule, not an edge/gateway firewall rule, given "between two groups."

**Medium confidence (verify with a GET, one command, 5 seconds):**
- `/infra/services/RDP` as the exact built-in service path. NSX ships a predefined RDP service on tcp/3389, but I would not swear to the object ID string in your specific 9.0 build. The inline `service_entries` variant in 3c sidesteps this entirely.
- `domain = default`. True for a normal single-domain deployment, and wrong the moment Projects/VPCs are in play — and VCF 9.0 pushes VPC constructs harder than earlier releases, so this is a live risk rather than a theoretical one.

**Low confidence (I am guessing about your environment, not about NSX):**
- **Which endpoints your two groups actually resolve to.** This is the biggest gap and I think it's the one worth your attention. I don't know their membership criteria, whether they're static VM lists or dynamic tag-based, whether they overlap, or whether they contain non-VM members (IP sets, AD groups). A tag-based group silently gains and loses members; the rule you write today may cover a different set of machines next week. Before publishing, pull effective membership for both groups and eyeball it.
- **The auth mechanism.** I've written the examples with basic auth to NSX Manager. VCF 9.0 environments frequently front this with VCF Operations / SSO identity or an API token, in which case you'd use a session or bearer token rather than `-u`. I don't know which applies to you.
- **Federation.** If a Global Manager is in the picture, every `/infra/` above becomes `/global-infra/` and the rule should be authored at the GM, not the local manager. Nothing in your question tells me either way.

Net: I'd give roughly 90%+ on the method and the API shape, ~75% on the literal paths as written, and I'm explicitly not claiming to know what the two groups contain. Send me the group IDs and the output of the three GETs in section 3a and I can turn this into something exact.

---

## Sources

- [VCF 9.0 NSX product support notes (Manager API no longer supported)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-nsx.html)
- [vDefend Firewall 9.0 — Add a Distributed Firewall Policy](https://techdocs.broadcom.com/us/en/vmware-security-load-balancing/vdefend/vdefend-firewall/9-0/vdefend-distributed-firewall/configuring-distributed-firewall/add-a-distributed-firewall-policy.html)
- [NSX REST API reference (version selector includes 9.0.0 / 9.0.1 / 9.0.2 / 9.1.0)](https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/latest/)
- [Patch Security Policy for Domain — Policy API reference](https://developer.broadcom.com/xapis/nsx-vmc-policy/latest/policy/api/v1/infra/domains/domain-id/security-policies/security-policy-id/patch/)
- [vDefend Distributed Firewall inactive rules (VCF 9.0 operations)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/infrastructure-operations/network-operationss/security/nsx-dfw-inactive-rules.html)
