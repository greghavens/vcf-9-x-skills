# VCF Automation All Apps — 9.0 → 9.1 delta

Scoped to the All Apps organisation type: the Kubernetes/CCI surface, and provider and organisation
administration. For the VM Apps org type (blueprints, catalog, deployments) see
`vcf-automation-vmapps`.

**Sources.** `DAUTO` = `research/vcf-automation.md` (page refs carried through as `[S##]`);
`DAUTH` = `research/foundation-auth-identity.md`; `DTOOL` =
`research/tooling-powercli-vks-sdk.md`; `SPECINV` = `research/spec-inventory/`.

Evidence tags: `[DOC-9.0]`, `[DOC-9.1]`, `[DOC-BOTH]`, `[UNVERIFIED]`.

---

## The delta itself is weaker evidence than usual — say so

There is **no VCF Automation OpenAPI specification at either the `9.0.0.0` or the `9.1.0.0` tag** of
`github.com/vmware/vcf-api-specs` (`SPECINV`, fifteen products, VCF Automation absent from both). So
unlike the other VCF skills, **this delta cannot be machine-computed**. Nothing here is a diff of two
specs; it is a diff of two doc sets, one of which was partly unreachable behind HTTP 429.

Two consequences worth passing to a user planning an upgrade:

1. **Absence of a delta row is not evidence of no change.** Several areas — concrete REST paths, CRD
   schemas, the quota object model — have no verified 9.0 baseline to diff against.
2. **Where a fact appears only in the 9.1 doc set, that is a documentation delta, not necessarily a
   product delta.** The clearest case is the whole CCI CRD surface: documented in 9.1, not retrieved
   for 9.0, but the All Apps org type — described as CRD- and supervisor-namespace-driven — exists in
   both `[DOC-BOTH]` (DAUTO `[S06]` `[S07]` `[S32]`). Rows below distinguish the two.

---

## Delta table

| # | Area | 9.0 | 9.1 | Type | Evidence |
|---|---|---|---|---|---|
| 1 | **External IP blocks** | Feature vocabulary is **"IP spaces"**. | **"IP spaces" renamed to "external IP blocks"**, with support for multiple CIDRs, custom IP ranges, and **Infoblox External IPAM** integration. | **Rename + new capability** | `[DOC-9.1]` (DAUTO `[S09]`) |
| 2 | **vDefend firewall** | Not delegable through VCF Automation. | **vDefend Distributed Firewall and Gateway Firewall support directly within VCF Automation**, enabling delegation of firewall services to organisations with RBAC and predefined security profiles. | **New capability** | `[DOC-9.1]` (DAUTO `[S09]`) |
| 3 | **Avi Load Balancer** | Not self-service through VCF Automation. | **"Full self-service support for Avi Load Balancer"** with quota management, for **both All Apps and VM Apps** organisations. | **New capability** | `[DOC-9.1]` (DAUTO `[S09]`) |
| 4 | **Transit Gateways** | Single/unstated. | **Multiple NSX Transit Gateways** with NAT, IPsec VPN and vDefend Gateway Firewall support. Providers also configure **default private VPC and private Transit Gateway IP blocks**, overridable per organisation. | **New capability** | `[DOC-9.1]` (DAUTO `[S09]`) |
| 5 | **Shared subnets** | — | **Shared NSX subnets** org-wide, shareable across multiple namespaces; **shared VLAN extension subnets** shareable across multiple organisations for direct device connectivity; **multiple external connections** (centralised + distributed VLAN) for external traffic exits. | **New capability** | `[DOC-9.1]` (DAUTO `[S09]`) |
| 6 | **Region quota** | Region quotas exist as a provider-managed resource. | **Multi-supervisor region quota** — "Grant organizations quota across multiple supervisors in any given region," with capacity sharing options. | **New capability** | 9.0: `[DOC-9.0]` (DAUTO `[S26]`) · 9.1: `[DOC-9.1]` (DAUTO `[S09]`) |
| 7 | **Content libraries** | Content libraries exist as provider- and Kubernetes-layer resources. | **Project content libraries** (dedicated to a project, spanning multiple projects) and **canonical content libraries** (subscribed, providing validated Ubuntu LTS images). | **New capability** | 9.0: `[DOC-9.0]` (DAUTO `[S26]`) · 9.1: `[DOC-9.1]` (DAUTO `[S09]`) |
| 8 | **Namespace day-2** | — | **Namespace allocation changes as day-2 operations**: modify resource limits, VM classes, storage classes and shared subnets after creation. | **New capability** | `[DOC-9.1]` (DAUTO `[S09]`) |
| 9 | **VCF CLI** | **v9.0** — "CLI for VCF Consumption services". | **v9.1**. `vcf context create` syntax is documented **identically** in both doc sets. | **Version bump** | `[DOC-9.0]` (DAUTO `[S06]`) · `[DOC-9.1]` (DAUTO `[S34]`) · syntax: `[DOC-BOTH]` (DTOOL) |
| 10 | **Token administration** | Provider portal → **My Account > API Tokens > NEW**, then a device-authorization grant. The 9.0 SSO tree has **no** API-client, API-token, OAuth-client or role-management pages at all. | Moves to **Fleet Management > Identity & Access > VCF SSO Overview** → identity broker → **API Access > API Clients > Create**, then ellipsis → **Generate API Token**. **API Token TTL default 30 days; Access Token TTL default 30 minutes.** The token cannot be retrieved after Continue. | **New/restructured** | 9.0: `[DOC-9.0]` (DAUTO `[S16]`; DAUTH `[S53]`) · 9.1: `[DOC-9.1]` (DAUTO `[S17]`; DAUTH `[S11]`) |
| 11 | **Fleet-wide OAuth** | No unified VCF OAuth in any fetched 9.0 page. | **VCF Identity Broker (VIDB)** unified OAuth: `POST https://{vidb.host}/acs/t/{role}/token` → `{"access_token": …}`, used as `Authorization: Bearer …`. Covers vCenter, NSX, VCF Operations, Orchestrator, HCX and **VCF Automation**. Durable API refresh token + short-lived bearer access token. | **New capability** | `[DOC-9.1]` (DAUTO `[S30]` `[S15]`) |
| 12 | **Organization Management wording** | Org admins "organize and govern resources allocated to them among application teams." | Org admins "create and assign projects and vSphere Namespaces tailored for different application teams." | **Wording — but the 9.1 phrasing describes the actual workflow** | `[DOC-9.0]` (DAUTO `[S10]`) vs `[DOC-9.1]` (DAUTO `[S11]`) |
| 13 | **CCI CRD documentation** | The All Apps org exists and is described as CRD- and supervisor-namespace-driven, but **no 9.0 page enumerating the CRDs, the `cci` context, the manifest or the permission matrix was retrieved.** | Documented: API group `infrastructure.cci.vmware.com/v1alpha2`, `kubectl --context cci api-resources`, a `SupervisorNamespace` manifest, an Admin/DevOps permission matrix, and resources across `v1alpha1`/`v1alpha2`. | **Documentation delta — product delta UNVERIFIED** | 9.0: `[DOC-9.0]` (DAUTO `[S06]` `[S07]`) · 9.1: `[DOC-9.1]` (DAUTO `[S32]`) |
| 14 | **Terraform providers** | Three providers. Kubernetes provider covers projects, content libraries, VPCs, subnets. | Same three, re-scoped: VCF Automation provider covers Provider Management **and a subset of the Organization UI**; Kubernetes provider scoped to "Organization UI resources exposed through the VCF Automation Kubernetes API layer, such as projects"; Aria provider explicitly covers **"All Apps resources not yet exposed through Kubernetes API layers."** | **Re-scope** | `[DOC-9.0]` (DAUTO `[S26]`) · `[DOC-9.1]` (DAUTO `[S27]`) |
| 15 | **Doc-set structure** | No "VCF APIs and SDKs" or "VCF Programming Guide" parent in the SDK/API/CLI section. | Adds **VMware Cloud Foundation APIs and SDKs** (hosting *OAuth Token Support for API and CLI Access*), **VMware Cloud Foundation Programming Guide**, and **Help and Support for VCF SDKs, APIs, and VCF PowerCLI**. Both the VM Apps programming guide and the **VCF Automation and All Apps API** page persist under identical slugs. | **Restructure** | `[DOC-9.0]` (DAUTO `[S05]`) · `[DOC-9.1]` (DAUTO `[S28]`) |
| 16 | **Building Cloud Applications doc tree** | Child pages include *Getting Started with the Tools for Building Applications*. | That page **404s under 9.1**; the tree points at "VMware Cloud Foundation Consumption documentation". Workload types listed in 9.1: Kubernetes clusters, VMs, containers as vSphere Pods, secrets, persistent volumes, GPU-enabled private AI workloads, and **databases via Data Services Manager**. | **Restructure** | `[DOC-9.0]` (DAUTO `[S03]`) · `[DOC-9.1]` (DAUTO `[S34]`) |

---

## What did **not** change — and one of these is a finding

### Provider API categories: 13 in 9.0, the same 13 in 9.1

Access Control · Aggregator · Approvals · Blueprint · Catalog · Content Gateway · Custom Forms ·
Custom Resource Types & Actions · Instances · Orchestrator Gateway · Policies · Projects ·
Provisioning Service

Same list, same descriptions, both versions `[DOC-9.0]` (DAUTO `[S33]`) and `[DOC-9.1]` (DAUTO
`[S31]`). The 9.0 page additionally names the exclusions — ABX, Deployment, Deployment Metrics,
Identity and Onboarding are VM-Apps-only.

**This row exists because a false delta was caught here.** A summarisation pass over the 9.1 page
annotated **"Custom Resource Types & Actions"** and **"Instances"** as *new in VCF 9.1*. Diffing
against the 9.0 page showed both were already listed there, with the same descriptions, and the
annotation was discarded as an artifact (DAUTO `[S31]` vs `[S33]`).

Two things follow. First, if anyone tells you those two categories are new in 9.1, they are wrong,
and the 9.0 page is the disproof. Second — the general lesson — **a summariser's "new in X" is a
claim about a document, not about a product**, and the only way to turn it into a claim about the
product is to read the other version's page. A verified no-change is worth as much to someone
planning an upgrade as a verified change, and it costs the same diff to establish.

> `[UNVERIFIED]` — one residual wrinkle. The auth dossier's source inventory describes the same 9.0
> categories page as listing **"10 All Apps API categories"** (DAUTH `[S62]`), against the
> automation dossier's 13 with a full enumeration (DAUTO `[S33]`). Thirteen is the better-supported
> count and is used throughout this skill, but the two dossiers disagree and the disagreement is not
> resolved. Confirm on the instance before quoting a number.

### Other stable items

- **Product definition.** The one-sentence definition is **verbatim identical** in both versions
  `[DOC-BOTH]` (DAUTO `[S10]` `[S11]`). 9.1 adds value-proposition wording about simplifying
  provisioning and scaling a multi-tenant private cloud with out-of-the-box IaaS and policy-based
  governance `[DOC-9.1]` (DAUTO `[S11]`).
- **Four functional areas** — Cloud Services, Provider Management, Organization Management, vSphere
  Supervisor — in both `[DOC-BOTH]` (DAUTO `[S10]` `[S11]`). Only the Organization Management
  wording changed (row 12).
- **UI surfaces.** `https://<FQDN>/provider` and `https://<FQDN>/automation`, unchanged
  `[DOC-BOTH]` (DAUTO `[S07]` `[S29]`).
- **Two organisation types**, All Apps and VM Apps, with different consumption mechanisms
  `[DOC-BOTH]` (DAUTO `[S06]`).
- **`vcf context create` syntax** — identical text in both doc sets, and `kubectl vsphere login`
  appears in neither `[DOC-BOTH]` (DTOOL).
- **Terraform examples URL** — `https://<FQDN>/automation/api-docs/#/terraform-provider` in both
  `[DOC-BOTH]` (DAUTO `[S26]` `[S27]`).
- **API Help Center** as the per-instance authoritative route, both versions `[DOC-BOTH]`
  (DAUTO `[S33]` `[S31]`).
- **No VCF Automation feature deprecations** were found on any fetched 9.1 page. The only
  deprecation in this area is the `x-vcloud-authorization` header on the provider/All Apps REST API
  `[DOC-9.1]` (DAUTO `[S19]`).

---

## Deltas this research could **not** establish

- **Whether the CCI CRD surface itself changed** — group versions, kinds, or schemas — because there
  is no 9.0 baseline. Row 13 is a documentation delta only. Resolve on the two clusters with
  `kubectl api-resources` and `kubectl get crd -o jsonpath='{.spec.versions[*].name}'`.
- **Whether the All Apps token endpoint changed**, since it is undocumented in *both* versions
  (DAUTO gap 3; DAUTH gap 5). No endpoint appears anywhere in this skill, by design.
- **Whether the VIDB bearer token is accepted by the All Apps / provider REST surface.** VCF
  Automation is named among the covered components `[DOC-9.1]` (DAUTO `[S30]`), but no page ties
  that token to this API's `Authorization` JWT requirement. Inference only.
- **Whether the 9.0-era tenant-local OAuth token flow is deprecated in 9.1** in favour of VIDB. The
  two coexist and no fetched page states precedence or a migration path (DAUTO gap 14).
- **REST path-level deltas** for the 13 categories — no concrete paths were retrieved for either
  version (DAUTO gaps 4–7).
- **Whether the 9.1 categories page repeats the VM-Apps-only exclusion sentence** — captured from
  the 9.0 page only. A retrieval gap, not evidence of change.
- **How day-2 namespace allocation changes (row 8) are expressed at the CRD level**, given that the
  documented permission matrix shows no update verb on `SupervisorNamespace` `[DOC-9.1]`
  (DAUTO `[S32]`).
- **The 9.0-side baseline for the networking rows (1–5)** — the What's New page describes the 9.1
  end state, not the 9.0 starting point, so "—" in those rows means *not described*, not *absent*.
- **Workload-type list changes** — both the 9.0 and 9.1 lists are summaries of prose rather than
  verbatim enumerations, so the apparent drop of Harbor container registry and addition of databases
  via Data Services Manager is **low confidence** (DAUTO gap 10).
- **Pipelines / Code Stream** — absent from every fetched page in both versions; whether it was
  dropped in the Aria→VCF transition or lives elsewhere is unresolved. Do not assert either way
  (DAUTO gap 8).
