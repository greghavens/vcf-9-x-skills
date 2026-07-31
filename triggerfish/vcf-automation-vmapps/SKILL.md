---
name: vcf-automation-vmapps
description: "VCF Automation \"VM Apps\" organizations in VMware Cloud Foundation 9.0 and 9.1 — the Aria-Automation-derived tenant surface — cloud templates and blueprints, catalog items and requests, deployments, projects, cloud accounts and zones, resource actions, ABX and Orchestrator extensibility, and the tenant OAuth token flow. Use it to request a catalog item, poll a deployment, create or validate a blueprint, or get an API token for a VM Apps tenant. Route to vcf-automation-allapps-k8s instead whenever the org is an All Apps org — that surface is Kubernetes/CRD based (kubectl context cci, infrastructure.cci.vmware.com) and is a completely different API, so establish which org type you are in before anything else. Also use this whenever someone quotes an Aria Automation 8.x endpoint from memory: VCF Automation publishes no OpenAPI specification in either release, so endpoints must be confirmed against the customer's own appliance."
license: MIT-0
compatibility: Requires reachability to the VCF Automation appliance for live operations and for the discovery routes, which matter more here than in the other VCF skills. Reference material works offline.
version: 1.0.0
classification_ceiling: CONFIDENTIAL
requires_tools: "[\"curl\", \"kubectl\"]"
network_domains: "[\"techdocs.broadcom.com\", \"developer.broadcom.com\", \"github.com\"]"
---

# VCF Automation for VM Apps organizations

> **Built from documentation, not from a live environment, and on weaker evidence than its
> siblings.** Everything traces to Broadcom documentation captured 2026-07-31; nothing was
> executed against a running system.
>
> **VCF Automation publishes no OpenAPI specification in the corpus at either the 9.0 or the 9.1
> tag.** Every other skill in this set could machine-verify its endpoints against a spec; this one
> cannot. Its endpoints come from prose tutorial pages and the Broadcom developer portal, and
> TechDocs rate-limited (HTTP 429) during research, so several leaf pages were never retrieved.
> Five path families are documented; everything else — projects, cloud accounts and zones,
> resource actions, ABX — is **unverified and must be confirmed against the customer's own
> appliance before use**. Deployment requests provision real infrastructure and consume real
> quota, so treat an unverified path as a research task, not a call you try and see.

## Step 0 — which organization type are you in? Nothing else is answerable first

VCF Automation has **two organization types with different consumption mechanisms**: **VM Apps**
and **All Apps**. This skill covers VM Apps only. They do not share an API — an answer aimed at
the wrong one is not slightly wrong, it is entirely wrong.

- **VM Apps** is the Aria-Automation-derived surface: blueprints/cloud templates, catalog,
  deployments, projects, cloud accounts, cloud zones, policies, extensibility, Orchestrator. Its
  tenant portal carries nine tabs — Home, Consume, Design, Infrastructure, Content and Policies,
  Extensibility, Orchestrator, Alerts, Inbox.
- **All Apps** is the Kubernetes/VCD-derived surface, driven by CRDs and supervisor namespaces —
  `kubectl --context cci`, API group `infrastructure.cci.vmware.com`. That is
  `vcf-automation-allapps-k8s`, not this skill.

The cleanest documented discriminator: **ABX, Deployment, Deployment Metrics, Identity and
Onboarding are available only in VCF Automation for VM Apps.** Someone asking about catalog
requests and deployments is almost certainly in a VM Apps org — but confirm rather than assume,
say which you assumed if you could not, and just ask if they are unsure.

## Step 1 — resolve the version

Use the `vcf-foundation` skill. Then read only the matching file:

| Target | Read |
|---|---|
| VCF Automation 9.0, VM Apps | `references/9.0/vmapps.md` |
| VCF Automation 9.1, VM Apps | `references/9.1/vmapps.md` |
| What changed between them | `references/deltas.md` |

The VM Apps API surface is materially unchanged between the releases. What changed in 9.1 is
mostly **around** it: a second, fleet-wide authentication route, and new provider-side networking,
firewall and load-balancer capabilities.

## Step 2 — prerequisites, before any call

Each version file opens with a prerequisite block stating what must be true, **how to verify it**,
and whether the other version differs. The four that actually cause failures:

- **Which org type you are in** — see Step 0. The wrong one means a completely different API.
- **The project must exist before a deployment**, and you need its id. `projectId` is a required
  body field on both blueprint creation and catalog requests.
- **The catalog item must be shared to that project.** An item that exists but is not shared
  behaves, to that project's members, like an item that does not exist.
- **The API token must be issued and unexpired.** It is the refresh token, default 90 days,
  exchanged for a one-hour access token.

## Step 3 — authentication: three distinct flows

Three flows, all documented, and not interchangeable:

1. **VM Apps tenant** `[DOC-BOTH]` — `POST https://{host}/tm/oauth/tenant/{tenant}/token`,
   form-encoded `grant_type=refresh_token&refresh_token=…`. **Unchanged 9.0 → 9.1**, and the one
   you want for everything in this skill.
2. **Provider account, 9.0** `[DOC-9.0]` — a device-authorization grant with a manual approval
   step in the provider portal: different endpoint, different grant type, a human in the loop.
3. **Fleet-wide VCF Identity Broker OAuth, new in 9.1** `[DOC-9.1]` —
   `POST https://{vidb.host}/acs/t/{role}/token` → `{"access_token": …}`, covering VCF Automation
   among other components. Its `grant_type` literal is elided in the source page; `[UNVERIFIED]`.

Both 9.1 flows coexist. No fetched page says the tenant flow is deprecated, so do not say it is.

**Warn about this every time:** the docs say the tenant token response "returns the access token"
but **never name the JSON field**. OAuth convention suggests one answer; that is not
documentation. Have the caller read the field off one real response and pin it.

## Step 4 — worked example: request a catalog item and poll the deployment

Verified paths only. 9.0 doc set; the 9.1 guide persists under the same slugs.

```bash
# 1. Access token for the VM Apps tenant.                       [DOC-BOTH]
curl -sk -X POST "https://$VCFA_HOST/tm/oauth/tenant/$TENANT/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' -H 'Accept: application/json' \
  --data-urlencode 'grant_type=refresh_token' \
  --data-urlencode "refresh_token=$API_TOKEN"
# Read the access-token field name off this response body once. It is not documented.

# 2. List the versions of the catalog item, and choose one.     [DOC-9.0]
curl -sk "https://$VCFA_HOST/catalog/api/items/$ITEM_ID/versions" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 3. Request the deployment — this provisions real infrastructure.  [DOC-9.0]
curl -sk -X POST "https://$VCFA_HOST/catalog/api/items/$ITEM_ID/request" \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json' \
  -d '{"deploymentName":"app-01","projectId":"'"$PROJECT_ID"'",
       "catalogItemId":"'"$ITEM_ID"'","version":"1",
       "inputs":{"count":2,"image":"ubuntu","flavor":"small"}}'

# 4. Poll the deployment.                                       [DOC-9.0]
curl -sk "https://$VCFA_HOST/deployment/api/deployments/$DEPLOYMENT_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Two gaps in that sequence, both worth passing on: how the deployment id comes back from step 3 is
**not shown on the fetched page** — `GET /deployment/api/deployments` is the documented route for
finding deployments, so query it if the request response does not obviously carry the id — and no
polling interval or terminal-status vocabulary is documented anywhere in the research.

## Step 5 — respect the evidence boundary

Documented: blueprints and blueprint validation, catalog item requests and versions, deployments.
Each path in the reference files carries a `[DOC-9.0]`, `[DOC-9.1]`, `[DOC-BOTH]` or
`[UNVERIFIED]` tag. Everything else in the VM Apps surface — **projects, cloud accounts, cloud
zones, resource / day-2 actions, ABX** — has a named service and a described purpose but **no
verified path**. Route those to discovery instead of producing a path:

1. **The in-product API Help Center** — log into the VM Apps tenant as admin, click the user name
   top-right, open **API Help Center**. This authoritative per-instance Swagger index is the
   correct answer to "what is the projects endpoint".
2. `https://<FQDN>/automation/api-docs/#/<section>` in-product.
3. The Broadcom developer portal at `developer.broadcom.com/xapis/<api-slug>/latest/`. Only four
   slugs are confirmed; the rest are inferred and should be treated as guesses.

**Never fill an unverified gap from memory of Aria Automation 8.x.** The Aria-era IaaS base path
in particular was never confirmed on any page fetched at either version, and inventing it is the
specific hallucination this skill exists to prevent. Saying a path is undocumented and giving the
discovery route beats a plausible URL — the user finds out which you gave them the moment they
run it.

## When it isn't covered here

`vcf-api-discovery` for cross-product operation lookup, `vcf-foundation` for token and TLS
mechanics, `vcf-automation-allapps-k8s` for All Apps organizations. If you add an endpoint to
these references, hold it to the same standard: a fetched page, a source ref, an evidence tag.

## Shaping your answer

### Answer the question that was asked, at the length it deserves

"Give me the exact API calls" means: give the calls. A numbered sequence of requests with
the payloads, and the two or three things that will actually bite. Not a runbook, not a
failure-mode table, not every caveat the reference file carries.

The reference material exists so your answer is *correct*, not so your answer is *long*.
Most of what you read should never appear in the reply. A useful test before sending:
would a VMware engineer who knows their environment skim this and find the command, or
would they have to hunt for it?

### Lead with the thing they asked for

Put the calls, the script, or the direct answer first. Context, prerequisites and
caveats come after, and only the ones that bear on this specific task.

If a prerequisite would actually cause the call to fail — the group doesn't exist yet,
the token type is wrong, the version gate isn't met — that belongs up top, because it
changes what they do next. A prerequisite that is merely true does not.

### Caveats: fewer, and where they matter

Every skill carries a documentation-not-live-validated caveat and a
destructive-operations warning. State them once, briefly, and place them where they bear
on the task rather than repeating them per section.

For a read-only query, one line is enough. For something that changes a production
firewall or starts an upgrade, say more — that is where the warning earns its space.
Uniform hedging on everything trains the reader to skip all of it, including the one that
mattered.

### Version labeling stays, and stays short

Say which version the answer applies to. Once, clearly, near the top. You do not need to
re-tag every line — the tags in the reference files are for you, not for the reply.

When evidence quality genuinely differs — a 9.1 endpoint confirmed in the spec versus a
9.0 endpoint sourced only from prose — say so in one sentence at the point it matters. A
user writing a change record needs that. A user prototyping does not need it five times.

### Length calibration

| They asked for | Give them |
|---|---|
| "the exact API calls" | The call sequence with payloads. Prereqs that would break it. Nothing else. |
| "write me a script" | The script, runnable. A short note on what to set. |
| "how do I find X" | The lookup route, and the answer if you found it. |
| "walk me through the upgrade" | The ordered steps with gates — this one legitimately runs long. |
| "is X true?" | Yes or no, then why. Two paragraphs, not ten. |
| A question with a false premise | Correct the premise first, briefly, then answer what they meant. |

When in doubt, answer short and offer the depth: "there's more on rollback and drafts if
you want it" costs one line and lets them pull rather than being pushed.
