# VCF Automation 9.0 → 9.1 — VM Apps Delta

Scoped to VCF Automation, weighted toward **VM Apps** organizations. Provider-side and All Apps
items appear where they change what a VM Apps operator sees or where they would otherwise be
mistaken for VM Apps changes.

**Sources.** `DVCFA` = `research/vcf-automation.md` (its `[S##]` refs resolve to that file's
Source Inventory, all pages accessed 2026-07-31); `DAUTH` =
`research/foundation-auth-identity.md`.

**Evidence tags:** `[DOC-9.0]`, `[DOC-9.1]`, `[DOC-BOTH]`, `[UNVERIFIED]` — as defined in the
version files.

---

## The headline: the VM Apps API did not change

**No VM Apps API path changed between 9.0 and 9.1, and no VCF Automation feature deprecation
appears in any fetched 9.1 page** [DVCFA delta table footnote]. The single deprecation found
anywhere in the 9.1 VCF Automation research is the **`x-vcloud-authorization` header** on the
**provider / All-Apps** REST API [DVCFA `[S19]`] — not on the VM Apps surface.

Two caveats on that headline, and they cut in opposite directions:

- **It is a weak "no change".** There is **no OpenAPI specification for VCF Automation at either
  tag**, so nothing here is a machine-computed diff the way the sibling skills' deltas are. This is
  a comparison of prose pages, several of which could not be retrieved because Broadcom TechDocs
  rate-limited (HTTP 429) during research [DVCFA Gap 13]. Absence of a documented change is not
  evidence of no change.
- **The 9.1 leaf endpoint pages were never fetched.** The blueprint, catalog and deployment paths
  come from **9.0** tutorial pages. The 9.1 doc set carries the same guide under identical slugs
  [DVCFA `[S05]`, `[S28]`], so carry-over is the reasonable reading — but it is a reading.

---

## Delta table

| # | Area | 9.0 | 9.1 | Type | Ref |
|---|---|---|---|---|---|
| 1 | **VM Apps API paths** | `/blueprint/api/blueprints`, `/blueprint/api/blueprint-validation`, `/catalog/api/items/{id}/request`, `/catalog/api/items/{id}/versions`, `/deployment/api/deployments[/{id}]` `[DOC-9.0]` | **No change documented.** Same guide, identical slugs; 9.1 leaf pages not individually fetched | **No change** (weak evidence) | `[S23]` `[S24]` `[S05]` `[S28]` |
| 2 | **Auth — VM Apps tenant** | `POST /tm/oauth/tenant/{tenant}/token`, form-encoded `grant_type=refresh_token`; refresh 90 d, access 1 h | **Unchanged** — same page, same lifetimes, same three-step flow `[DOC-BOTH]` | **No change** | `[S12]` `[S13]` `[S14]` |
| 3 | **Auth — fleet-wide** | None documented in any fetched page | **New: VCF Identity Broker (VIDB) OAuth.** `POST https://{vidb.host}/acs/t/{role}/token` → `{"access_token": …}`; covers vCenter, NSX, VCF Operations, Orchestrator, HCX and **VCF Automation**; federates with Okta, Entra ID. `grant_type` literal **elided in source** `[UNVERIFIED]` | **New capability** | `[S30]` `[S15]`, Gap 1 |
| 4 | **Auth — token admin UI** | Provider portal **My Account > API Tokens > NEW**; **device-authorization grant** for provider accounts (with a manual GRANT step) | **Fleet Management > Identity & Access > VCF SSO Overview > API Access > API Clients > Create**, then **Generate API Token**. **API Token TTL default 30 days; Access Token TTL default 30 mins.** Token not retrievable after creation | **Restructured** | `[S16]` `[S17]` |
| 5 | **Two token systems** | One (tenant) plus the provider grant | **Two coexisting**: tenant `/tm/oauth/...` and fleet-wide VIDB `/acs/t/...`. **No page says the tenant flow is deprecated**; their relationship is undocumented `[UNVERIFIED]` | **New coexistence** | `[S13]` `[S30]`, Gap 14 |
| 6 | **Organization types** | All Apps and VM Apps, "different consumption mechanisms" | **Unchanged.** Both persist; All Apps documented in 9.1 through CRDs (`infrastructure.cci.vmware.com/v1alpha2`, `kubectl --context cci`) | **No change** | `[S06]` `[S32]` |
| 7 | **VM Apps UI tabs and terminology** | Nine tabs; nine defined terms | **Materially the same** nine tabs and terms | **No change** | `[S22]` `[S21]` |
| 8 | **Blueprint description** | "Templates developed using canvas and YAML editor" | Adds "VCF or AWS CloudFormation" templates that "administrators can import for reuse" — **wording; no import path documented** `[UNVERIFIED]` | **Wording/scope** | `[S22]` `[S21]` |
| 9 | **Provider REST API categories** | 13 categories, plus the note that ABX, Deployment, Deployment Metrics, Identity and Onboarding are **VM Apps only** | **Same 13 categories** | **No change** | `[S33]` `[S31]` |
| 10 | **Provider / All-Apps REST conventions** | Not separately fetched for 9.0 (portal is 9.1/latest only) | URN ids; `202` + `Location` for async; `application/json;version=9.1.0`, 5 major versions back; `Authorization` JWT recommended; **`x-vcloud-authorization` deprecated**; `X-VMWARE-VCLOUD-TENANT-CONTEXT`, `X-VMWARE-VCLOUD-AUTH-CONTEXT` `[DOC-9.1]` | **Documented in 9.1 only** — probably true of 9.0, unprovable | `[S19]` `[S20]`, Gap 11 |
| 11 | **Security (provider)** | — | **vDefend Distributed Firewall and Gateway Firewall** inside VCF Automation, delegable to orgs with RBAC and predefined security profiles | **New capability** | `[S09]` |
| 12 | **Load balancing** | — | **Full self-service Avi Load Balancer** with quota management, **for both All Apps and VM Apps orgs** — the one 9.1 headline that touches VM Apps directly | **New capability** | `[S09]` |
| 13 | **Networking (provider)** | IP spaces | **IP spaces renamed to external IP blocks**; multiple CIDRs, custom IP ranges, **Infoblox External IPAM**; default private VPC and Transit Gateway IP blocks | **Rename + new capability** | `[S09]` |
| 14 | **Networking (org)** | — | Multiple **NSX Transit Gateways** with NAT, IPsec VPN, vDefend Gateway Firewall; **shared NSX subnets** across namespaces; **shared VLAN extension subnets** across orgs; multiple external connections | **New capability** | `[S09]` |
| 15 | **Quota** | — | **Multi-supervisor region quota** across a region, with capacity sharing | **New capability** | `[S09]` |
| 16 | **Content** | — | **Project content libraries** (multi-project spanning) and **canonical content libraries** (subscribed, validated Ubuntu LTS images) | **New capability** | `[S09]` |
| 17 | **Namespaces** | — | Day-2 **namespace allocation changes**: resource limits, VM classes, storage classes, shared subnets | **New capability** | `[S09]` |
| 18 | **Org Management wording** | "organize and govern resources allocated to them among application teams" | "create and assign **projects and vSphere Namespaces** tailored for different application teams" | **Wording** | `[S10]` `[S11]` |
| 19 | **CLI** | VCF CLI **v9.0** | VCF CLI **v9.1** | **Version bump** | `[S06]` `[S34]` |
| 20 | **Terraform providers** | Three; Kubernetes provider covers projects, content libraries, VPCs, subnets | Same three, re-scoped: Kubernetes provider = "Organization UI resources exposed through the VCF Automation Kubernetes API layer, such as projects"; **Aria provider** = VM Apps orgs **and** All Apps resources not yet exposed through Kubernetes layers | **Re-scope** | `[S26]` `[S27]` |
| 21 | **Doc structure (SDK/API)** | No "VCF APIs and SDKs" or "VCF Programming Guide" parent | Adds **VMware Cloud Foundation APIs and SDKs** (hosting *OAuth Token Support for API and CLI Access*), **VMware Cloud Foundation Programming Guide**, **Help and Support for VCF SDKs, APIs and VCF PowerCLI** | **Restructure** | `[S05]` `[S28]` |
| 22 | **Building Cloud Apps doc tree** | `getting-started-with-the-tools-for-building-applications.html` exists | **404 under 9.1**; content restructured toward "VMware Cloud Foundation Consumption documentation" | **Restructure** | `[S03]` `[S34]` |
| 23 | **Workload types** | VMs, K8s clusters, vSphere Pods, persistent volumes, secret store, **Harbor container registry**, GPU/private AI | K8s clusters, VMs, vSphere Pods, secrets, persistent volumes, GPU/private AI, **databases via Data Services Manager** | **List change — LOW CONFIDENCE**, both lists are prose summaries | `[S03]` `[S34]`, Gap 10 |

---

## What did *not* change

- **Every documented VM Apps endpoint.** Blueprint CRUD and validation, catalog request and
  versions, deployment query and status.
- **The VM Apps tenant token flow**, including both lifetimes (90 days / 1 hour).
- **The two organization types**, their consumption split, and both UI surfaces
  (`/automation`, `/provider`).
- **The nine VM Apps portal tabs** and the nine defined terms.
- **The 15 VM Apps API services** and the 13 provider REST API categories.
- **The dual naming of "blueprints" and "cloud templates"** — both terms remain in active use.
- **The three Terraform providers** — same three, re-scoped descriptions.
- **The unverified areas.** Projects, cloud accounts, cloud zones, resource actions and ABX have
  no documented path in **either** version. The gap did not close in 9.1.

## Deltas the research could NOT establish

- **Whether the VM Apps endpoints actually changed.** No spec at either tag; no 9.1 leaf tutorial
  pages fetched. "No documented change" is the strongest available statement [DVCFA Gap 13].
- **Whether the tenant token flow is on a deprecation path** now that VIDB exists. No page says
  so, and no page says otherwise [DVCFA Gap 14].
- **The VIDB `grant_type` literal** — elided as `...` in the source page [DVCFA Gap 1].
- **The `/tm` prefix question in the 9.0 provider flow** — steps 2–4 use `/tm/oauth/...`, the
  refresh step does not. Unresolved, and therefore also unresolved as a delta [DVCFA Gap 2].
- **The access-token response field name** for the tenant flow, in either version [DAUTH Gap 4].
- **Paths for projects, cloud accounts, cloud zones, resource actions and ABX**, in either version
  — so no delta can be computed for any of them [DVCFA Gaps 4–7].
- **The All Apps access-token endpoint** — the documentation page 404s [DVCFA Gap 3].
- **Whether the provider/All-Apps REST conventions apply to 9.0** — the developer portal serves
  only "9.1 (latest)" and has no 9.0-pinned URL pattern [DVCFA Gap 11].
- **Pipelines / Code Stream** — absent from every fetched page in both versions. Whether it was
  dropped in the Aria→VCF transition or lives elsewhere is unresolved; do not assert either way
  [DVCFA Gap 8].

## One artifact to not repeat

A summarization pass over the 9.1 provider API categories annotated **"Custom Resource Types &
Actions"** and **"Instances"** as new in 9.1. **The 9.0 page already lists both** [DVCFA `[S33]`
vs `[S31]`, Gap 9]. It is a summarizer artifact, not a delta. If a user has been told those are
new in 9.1, correct it.
