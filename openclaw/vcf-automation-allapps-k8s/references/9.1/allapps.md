# VCF Automation — All Apps organisations, VCF 9.1

**Applies to:** VCF Automation as shipped in VMware Cloud Foundation **9.1**.
**Do not apply this file to 9.0.** Use `../9.0/allapps.md`, and `../deltas.md` for the change list.

**Sources.** `DAUTO` = `research/vcf-automation.md` (its own page refs are carried through as
`[S##]`); `DAUTH` = `research/foundation-auth-identity.md`; `DTOOL` =
`research/tooling-powercli-vks-sdk.md`; `SPECINV` = `research/spec-inventory/` (machine-extracted
from the git tags of `github.com/vmware/vcf-api-specs`).

---

## READ THIS FIRST — there is no spec, so nothing here is spec-confirmed

`SPECINV` covers fifteen products across the `9.0.0.0` and `9.1.0.0` tags. **VCF Automation is not
among them at either tag.** There is no machine-readable API description to check paths, payloads or
CRD schemas against, in either direction.

What that means in practice:

1. Every claim below is **prose-sourced**. No path, field or CRD version in this file has been
   confirmed against a specification, because none exists to confirm it against.
2. Broadcom TechDocs returned **HTTP 429 repeatedly** during research, forcing ~90 s pauses and
   leaving several leaf pages unfetched. Those are recorded in *Gaps* rather than papered over.
3. **The live cluster outranks this file** for anything under `infrastructure.cci.vmware.com`. The
   discovery commands in *Ask the cluster first* are not a fallback; they are the primary route.

| Tag | Meaning |
|---|---|
| `[DOC-9.1]` | Read from a VCF 9.1 documentation page, or a developer-portal page reporting itself as 9.1/latest. |
| `[DOC-BOTH]` | Independently read in both the 9.0 and 9.1 doc sets. |
| `[UNVERIFIED]` | Not established by any retrieved page. Do not state as fact. |

---

## Contents

- [Prerequisites](#prerequisites) — **read before any CRD or call**
  - [P1 — you are in an All Apps organisation, not a VM Apps organisation](#p1--you-are-in-an-all-apps-organisation-not-a-vm-apps-organisation)
  - [P2 — the `cci` kubectl context is established](#p2--the-cci-kubectl-context-is-established)
  - [P3 — a region is available to the organisation](#p3--a-region-is-available-to-the-organisation)
  - [P4 — quota is allocated, including across supervisors](#p4--quota-is-allocated-including-across-supervisors)
  - [P5 — the project exists and the supervisor namespace is assigned to it](#p5--the-project-exists-and-the-supervisor-namespace-is-assigned-to-it)
  - [P6 — your role covers the verb you are about to use](#p6--your-role-covers-the-verb-you-are-about-to-use)
  - [P7 — auth: what is known and what is not](#p7--auth-what-is-known-and-what-is-not)
- [Ask the cluster first](#ask-the-cluster-first)
- [The CCI CRD surface](#the-cci-crd-surface)
- [Worked example — create a supervisor namespace, discovery-first](#worked-example--create-a-supervisor-namespace-discovery-first)
- [Provider and All Apps REST conventions](#provider-and-all-apps-rest-conventions)
- [Provider API categories — 13, unchanged from 9.0](#provider-api-categories--13-unchanged-from-90)
- [What 9.1 added on the provider and organisation side](#what-91-added-on-the-provider-and-organisation-side)
- [Terraform](#terraform)
- [Lookup routes](#lookup-routes)
- [Gaps](#gaps)

---

## Prerequisites

Nothing below this block should be attempted until these hold. Each states what must be true, **how
to verify it**, and whether 9.0 differs.

### P1 — you are in an All Apps organisation, not a VM Apps organisation

**Must be true:** the organisation you are working in is an **All Apps** organisation. Two
organisation types exist, "with different consumption mechanisms" `[DOC-BOTH]` (DAUTO `[S06]`). All
Apps is the Kubernetes/VCD-derived surface driven by CRDs and supervisor namespaces; VM Apps is the
Aria-Automation-derived surface of blueprints, catalog, deployments, cloud accounts and cloud zones
`[DOC-BOTH]` (DAUTO `[S06]` `[S32]` `[S21]`).

**This is the highest-cost prerequisite on the page.** The wrong org type is not a parameter
mistake; it is a different API with a different object model. In 9.1 the two are also described
differently at the top level: org management for All Apps is documented through Kubernetes CRDs and
`kubectl` `[DOC-9.1]` (DAUTO `[S32]`), while the VM Apps org portal carries Design, Extensibility
and Orchestrator tabs and a blueprint/catalog API family `[DOC-9.1]` (DAUTO `[S21]`).

**How to verify:**
- In the Provider Management Portal at `https://<FQDN>/provider`, inspect the organisation. The
  provider and tenant surfaces are `https://<FQDN>/provider` and `https://<FQDN>/automation` in both
  versions `[DOC-BOTH]` (DAUTO `[S07]` `[S29]`).
- Functionally, from the CLI: if `kubectl --context cci api-resources --api-group=infrastructure.cci.vmware.com`
  returns resources, you are on the All Apps surface. If there is no such context and no such group,
  you are not — stop and switch skills. *(The command is documented `[DOC-9.1]` (DAUTO `[S32]`);
  using its output as an org-type test is a practical inference, not a documented test.)*

**9.0 difference:** the same two org types exist in 9.0 `[DOC-9.0]` (DAUTO `[S06]`), but the 9.0 doc
set page enumerating the CCI CRDs and the `cci` context was not retrieved — see `../9.0/allapps.md`.

### P2 — the `cci` kubectl context is established

**Must be true:** a kubeconfig context named `cci` exists and is usable. All the documented All Apps
kubectl commands are written as `kubectl --context cci ...` `[DOC-9.1]` (DAUTO `[S32]`).

**How to establish it.** The login step in VCF 9.x is the **VCF CLI** (`vcf`), not
`kubectl vsphere login` — that command "appears nowhere in the VCF 9.x docs" and a site-restricted
search across the whole doc tree returned no page containing the string `[DOC-BOTH]` (DTOOL). For a
VCF Automation endpoint the documented 9.1 form is `[DOC-9.1]` (DAUTH `[S34]`):

```bash
export VCF_CLI_VCFA_API_TOKEN=<api_token>          # from VCF Automation: My Account > API Tokens
vcf context create vcfa_ctx \
  --endpoint $VCFA_ENDPOINT \
  --api-token $VCF_CLI_VCFA_API_TOKEN \
  --tenant-name $TENANT_NAME \
  --ca-certificate vcfa.cert
```

The VCF CLI writes the kubeconfig context; `kubectl` consumes it `[DOC-BOTH]` (DTOOL). `--ca-certificate`
is the documented way to pin a private CA for a VCF client `[DOC-9.1]` (DAUTH).

> `[UNVERIFIED]` **The join between these two facts is not documented.** No retrieved page states
> that `vcf context create` against a VCF Automation endpoint is what produces the context literally
> named `cci`. The context name comes from one page (DAUTO `[S32]`); the login command comes from
> another (DAUTH `[S34]`). Verify with `kubectl config get-contexts` and use whatever name is
> actually written.

**How to verify:**
```bash
vcf context list
kubectl config get-contexts
kubectl --context cci api-resources --api-group=infrastructure.cci.vmware.com
```

**9.0 difference:** `vcf context create --endpoint … --username … --ca-certificate …` is documented
identically in both doc sets `[DOC-BOTH]` (DTOOL); the `--api-token`/`--tenant-name` VCF Automation
form is from the 9.1 doc set `[DOC-9.1]` (DAUTH `[S34]`). VCF CLI is **v9.1** in the 9.1 docs and
**v9.0** in the 9.0 docs `[DOC-9.1]`/`[DOC-9.0]` (DAUTO `[S34]` / `[S06]`).

### P3 — a region is available to the organisation

**Must be true:** a region exists and is consumable by your organisation. `Region` is one of the
listed API resources, **read-only to the org Admin role and not listed for DevOps** `[DOC-9.1]`
(DAUTO `[S32]`) — meaning regions are allocated *to* you by the provider, not created by you. The
documented `SupervisorNamespace` example carries `spec.regionName` `[DOC-9.1]` (DAUTO `[S32]`).

**How to verify:**
```bash
kubectl --context cci get regions
kubectl --context cci explain supervisornamespace.spec.regionName
```
On the provider side, regions are among the resources the Terraform provider manages for provider
administrators `[DOC-9.1]` (DAUTO `[S27]`).

**9.0 difference:** regions exist as a provider-managed resource in 9.0 too — the 9.0 Terraform
provider covers "organizations, regions, region quotas, networking, content libraries, supervisor
namespaces" `[DOC-9.0]` (DAUTO `[S26]`). The `Region` CRD and its permissions are documented only in
the 9.1 page.

### P4 — quota is allocated, including across supervisors

**Must be true:** the organisation holds quota in the region you are targeting. Region quotas are a
provider-managed resource in both versions `[DOC-BOTH]` (DAUTO `[S26]` `[S27]`), and
`RegionStorageClassQuotas` appears in the CCI resource list `[DOC-9.1]` (DAUTO `[S32]`).

**New in 9.1:** **multi-supervisor region quota** — "Grant organizations quota across multiple
supervisors in any given region," with capacity sharing options `[DOC-9.1]` (DAUTO `[S09]`). If you
carry a 9.0 mental model of one supervisor per region quota, correct it.

**How to verify:**
```bash
kubectl --context cci get regionstorageclassquotas
kubectl --context cci explain regionstorageclassquota
```
`[UNVERIFIED]` — the exact quota object model (CPU/memory as well as storage, which object carries
it, and how the multi-supervisor sharing option is represented) is not documented on any retrieved
page. Read the live schema.

### P5 — the project exists and the supervisor namespace is assigned to it

**Must be true:** a project exists to hold the namespace. In the documented example the
`SupervisorNamespace` is created **into a project namespace** — `metadata.namespace: default-project`
`[DOC-9.1]` (DAUTO `[S32]`). `Project` is full CRUD for Admin and read-only for DevOps `[DOC-9.1]`
(DAUTO `[S32]`).

Note the 9.1 rewording of what organisation administrators do: they "create and assign projects and
vSphere Namespaces tailored for different application teams" — 9.0 said only that they "organize and
govern resources allocated to them among application teams" `[DOC-9.1]` vs `[DOC-9.0]` (DAUTO
`[S11]` / `[S10]`). The 9.1 phrasing is the accurate description of this workflow.

**How to verify:**
```bash
kubectl --context cci get projects
kubectl --context cci get supervisornamespaces -n <project-namespace>
```

**9.0 difference:** projects exist in 9.0 as a Terraform-managed Kubernetes resource `[DOC-9.0]`
(DAUTO `[S26]`); the CRD-level detail is 9.1-documented only.

### P6 — your role covers the verb you are about to use

**Must be true:** your role permits the operation. The documented All Apps permission matrix
`[DOC-9.1]` (DAUTO `[S32]`):

| Resource | Admin | DevOps |
|---|---|---|
| `Project` | Full CRUD | Read-only |
| `SupervisorNamespace` | Create, get, delete, list | Read-only |
| `ProjectRole` | Read-only | Read-only |
| `Region` | Read-only | (none listed) |

Note what this table does *not* say: **`SupervisorNamespace` has no update verb for either role.**
Day-2 changes to a namespace are documented as a 9.1 capability (see *What 9.1 added*), so either
they flow through a different object or through a verb this table omits. `[UNVERIFIED]` — do not
assume `kubectl edit supervisornamespace` will be accepted; check with `kubectl auth can-i`.

Above the org, the provider role model applies: rights are per-object-type; roles are sets of
rights; **provider roles** are exclusive to the provider organisation; **global roles** are
published by System Administrators and org admins cannot modify them; **organisation-specific roles**
are created locally from a subset of org rights; **System Administrator** exists only in the provider
org and holds all VCF Automation rights `[DOC-9.1]` (DAUTH `[S50]`).

**How to verify:**
```bash
kubectl --context cci auth can-i create supervisornamespaces -n <project-namespace>
kubectl --context cci auth can-i --list -n <project-namespace>
kubectl --context cci get projectrolebindings -n <project-namespace>
```

**9.0 difference:** the matrix is from the 9.1 page; no 9.0 equivalent was retrieved.

### P7 — auth: what is known and what is not

**Must be true:** you hold a credential the surface accepts.

**For the Kubernetes surface:** the kubeconfig context handles it (P2). Bearer credentials are
kubeconfig-managed `[DOC-9.1]` (DAUTH `[S34]`).

**For the provider / All Apps REST surface**, the documented contract `[DOC-9.1]` (DAUTO `[S19]`;
DAUTH `[S46]`):

| Header | Status |
|---|---|
| `Authorization` | **JWT — the recommended scheme.** |
| `x-vcloud-authorization` | Session header, **deprecated**. |
| `X-VMWARE-VCLOUD-TENANT-CONTEXT` | Context header for org-scoped operations. |
| `X-VMWARE-VCLOUD-AUTH-CONTEXT` | Context header for multisite. |

The `x-vcloud-*` family confirms the VMware Cloud Director lineage of this surface `[DOC-9.1]`
(DAUTO `[S19]`).

> `[UNVERIFIED]` — **the token endpoint URL for this surface is not documented anywhere retrieved.**
> The reference states the header schemes and nothing about issuance (DAUTH `[S46]`), and the
> Broadcom page "Generating an All Apps Access Token" at
> `.../about-the-vcf-automation-api/generating-an-access-token.html` returned **404 on three
> attempts** despite appearing in the search index (DAUTO gap 3; DAUTH gap 5). **Do not construct a
> URL.** Get the endpoint from the in-product API Help Center on the target instance
> (see *Lookup routes*).

Two adjacent, *documented* token flows exist. Neither is confirmed to issue the JWT this surface
accepts, so treat any use of them here as an experiment, not a plan:

- **Provider management API tokens, 9.0-documented device-authorization grant** — created at
  `https://<vcfa.url>/provider` → My Account > API Tokens > NEW, then a device-code exchange
  `[DOC-9.0]` (DAUTO `[S16]`). See `../9.0/allapps.md`.
- **Fleet-wide VCF SSO / identity broker (VIDB), new in 9.1** — "As of VCF 9.1, VMware offers
  unified API and CLI access across most VCF components with OAuth standards-based token
  authentication, based on VCF Identity Broker (VIDB)", and **VCF Automation is named among the
  covered components** `[DOC-9.1]` (DAUTO `[S30]`). Exchange is
  `POST https://{vidb.host}/acs/t/{role}/token`, form-encoded, returning `{"access_token": …}` for
  use as `Authorization: Bearer …` `[DOC-9.1]` (DAUTO `[S30]`). The token model is a durable API
  refresh token plus a short-lived bearer access token `[DOC-9.1]` (DAUTO `[S30]` `[S15]`).
  - Token administration moved in 9.1 to **Fleet Management > Identity & Access > VCF SSO Overview**
    → select identity broker → **API Access > API Clients > Create**, then the vertical ellipsis →
    **Generate API Token**. **API Token TTL defaults to 30 days; Access Token TTL defaults to 30
    minutes.** "After you click Continue, you cannot retrieve the API token that was generated."
    `[DOC-9.1]` (DAUTO `[S17]`; DAUTH `[S11]`). IAM ceilings: API token expiry max 180 days, access
    token expiry max 480 minutes `[DOC-9.1]` (DAUTH `[S52]`).
  - `[UNVERIFIED]` — the `grant_type` value is elided as `...` in the source page as rendered
    (DAUTO gap 1).

**9.0 difference:** the VIDB flow and the Fleet Management token-administration UI are **9.1 only**.
In 9.0 the documented route is the per-product provider token flow `[DOC-9.0]` (DAUTO `[S16]`), and
the 9.0 SSO tree contains no API-client or API-token pages at all `[DOC-9.0]` (DAUTH `[S53]`).

---

## Ask the cluster first

The CRD surface is self-describing. Prefer it over this file.

```bash
# What exists, and in which group versions
kubectl --context cci api-resources --api-group=infrastructure.cci.vmware.com
kubectl --context cci api-versions | grep infrastructure.cci
kubectl --context cci get crd | grep cci

# Which versions are SERVED and which is STORED — not the same as "documented"
kubectl --context cci get crd supervisornamespaces.infrastructure.cci.vmware.com \
  -o jsonpath='{range .spec.versions[*]}{.name}{" served="}{.served}{" storage="}{.storage}{"\n"}{end}'
kubectl --context cci get crd supervisornamespaces.infrastructure.cci.vmware.com \
  -o jsonpath='{.status.storedVersions}{"\n"}'

# Field-level schema, straight from the API server
kubectl --context cci explain supervisornamespace.spec
kubectl --context cci explain supervisornamespace --recursive
```

`kubectl --context cci api-resources` is the documented discovery command for this surface
`[DOC-9.1]` (DAUTO `[S32]`); the `get crd` / `explain` / served-version checks are standard kubectl
and are the recommended generic route in the tooling research, which notes the docs do not present
them `[DOC-9.1]` (DTOOL).

**Why this ordering matters.** The platform has a live example of documentation and cluster
disagreeing: VCF 9.0 docs say the VM Operator API is `v1alpha2`/`v1alpha3`, while the upstream
project's docs show `v1alpha5`, and what the shipped 9.1 Supervisor serves is recorded as
`[UNVERIFIED]` with the explicit instruction to resolve it at runtime (DTOOL). The same discipline
applies to `infrastructure.cci.vmware.com`: `v1alpha2` is what the 9.1 page shows, not necessarily
what your cluster serves.

For the general discovery method, see the `vcf-api-discovery` skill.

---

## The CCI CRD surface

**API group:** `infrastructure.cci.vmware.com`, version `v1alpha2` in the documented example
`[DOC-9.1]` (DAUTO `[S32]`). Resources are documented "across `v1alpha1` / `v1alpha2`" `[DOC-9.1]`
(DAUTO `[S32]`) — which version a given kind serves is a per-cluster question.

**Kinds named in the documentation** `[DOC-9.1]` (DAUTO `[S32]`):

| Kind | Notes |
|---|---|
| `Project` | Org unit holding namespaces. Full CRUD for Admin. |
| `SupervisorNamespace` | The unit of consumption. Create/get/delete/list for Admin. |
| `Region` | Provider-allocated. Read-only. |
| `ProjectRole` | Read-only for both roles. |
| `ProjectRoleBindings` | Listed as an available API resource. |
| `RegionStorageClassQuotas` | Listed as an available API resource. |
| `VirtualMachineRemoteConsoleRequests` | Listed as an available API resource. |
| `Zone` | Listed as an available API resource. |

This list is what the documentation names. **It is not guaranteed complete** — treat
`kubectl api-resources` output as the real list.

**Documented `SupervisorNamespace` manifest** `[DOC-9.1]` (DAUTO `[S32]`), reproduced verbatim:

```yaml
apiVersion: infrastructure.cci.vmware.com/v1alpha2
kind: SupervisorNamespace
metadata:
  generateName: test
  namespace: default-project
spec:
  regionName: e2e-region
  className: e2e-small
  vpcName: e2e-region-default-vpc
```

Three things about it worth carrying into an answer:

- `metadata.namespace` is the **project**, not a Kubernetes namespace you chose.
- `generateName` rather than `name` — the server assigns the suffix.
- `regionName`, `className` and `vpcName` are **environment-specific values from that example**, not
  defaults. Discover the real ones before writing a manifest.

`[UNVERIFIED]` — the full `spec` schema, status conditions, and which fields are mutable after
creation are not documented on any retrieved page. `kubectl explain` answers all three.

---

## Worked example — create a supervisor namespace, discovery-first

The point of this example is the order. Four discovery steps before one write.

```bash
# 0. Log in and confirm the context (P2). Do not assume the context is named 'cci'.
export VCF_CLI_VCFA_API_TOKEN=<api_token>
vcf context create vcfa_ctx --endpoint $VCFA_ENDPOINT \
  --api-token $VCF_CLI_VCFA_API_TOKEN --tenant-name $TENANT_NAME --ca-certificate vcfa.cert
kubectl config get-contexts
CTX=cci     # replace with the name kubectl actually reports

# 1. Confirm you are on the All Apps surface at all (P1).
kubectl --context $CTX api-resources --api-group=infrastructure.cci.vmware.com
#    No group -> wrong org type or wrong context. Stop here.

# 2. Find the served version rather than trusting v1alpha2.
kubectl --context $CTX get crd supervisornamespaces.infrastructure.cci.vmware.com \
  -o jsonpath='{range .spec.versions[*]}{.name}{" served="}{.served}{" storage="}{.storage}{"\n"}{end}'

# 3. Read the schema from the API server, not from a document.
kubectl --context $CTX explain supervisornamespace.spec

# 4. Resolve the three environment-specific inputs (P3, P4, P5).
kubectl --context $CTX get projects                       # -> the project to create into
kubectl --context $CTX get regions                        # -> spec.regionName
kubectl --context $CTX get regionstorageclassquotas       # -> is there quota to land on?
#    className and vpcName: enumerate whatever kinds step 1 revealed for classes and VPCs,
#    and cross-check with `kubectl explain supervisornamespace.spec.className`.

# 5. Confirm you are allowed to do it (P6).
kubectl --context $CTX auth can-i create supervisornamespaces -n <project>

# 6. Write the manifest using the values you just discovered.
cat > ns.yaml <<'YAML'
apiVersion: infrastructure.cci.vmware.com/v1alpha2   # <- replace with the served version from step 2
kind: SupervisorNamespace
metadata:
  generateName: team-a-
  namespace: <project>                               # <- from step 4
spec:
  regionName: <region>                               # <- from step 4
  className: <class>
  vpcName: <vpc>
YAML

# 7. Apply and watch.
kubectl --context $CTX apply -f ns.yaml
kubectl --context $CTX get supervisornamespaces -n <project> -w
kubectl --context $CTX describe supervisornamespace <generated-name> -n <project>
```

**Caveats specific to step 7.** This is a write against a production consumption surface. There is no
documented dry-run guidance for this CRD; `kubectl apply --dry-run=server -f ns.yaml` is standard
kubectl and will at least run the admission chain without persisting. Deletion is a `SupervisorNamespace`
verb held by Admin `[DOC-9.1]` (DAUTO `[S32]`) — and deleting a namespace takes its workloads with it.

**If it fails**, the ordering above tells you where: a rejected `regionName` means P3/P4, a rejected
`namespace` means P5, a 403 means P6, and an unrecognised `apiVersion` means step 2 was skipped.

---

## Provider and All Apps REST conventions

From the Broadcom Developer Portal, pages self-reporting as 9.1/latest `[DOC-9.1]` (DAUTO `[S19]`
`[S20]`):

| Convention | Detail |
|---|---|
| Collection shape | `GET /items`, `POST /items` (**201**), `GET /items/{urn}`, `PUT /items/{urn}`, `DELETE /items/{urn}` (**204**). |
| Identifiers | **Full URNs**, not bare UUIDs. |
| Async | **202** with a `Location` header carrying the tracking task URI. |
| Version negotiation | `application/json;version=9.1.0` on `Accept` and/or `Content-Type`. "Each feature has a version in the path element present in its URL." Up to **5 major versions back** are supported, so `version=9.0.0` should remain callable against a 9.1 system. |
| Auth headers | See P7. |

`/items` here is the portal's generic illustration of the collection shape, not a literal path.

> **No base path is stated in this file, deliberately.** The Aria-era IaaS base path that people
> expect for VCF Automation **was never confirmed on any fetched 9.0 or 9.1 page** and must not be
> assumed (DAUTO gap 5). Neither were the concrete paths for projects, cloud accounts/zones, day-2
> resource actions, or ABX — all rate-limited out of the research (DAUTO gaps 4–7). If you need a
> concrete provider path, get it from the API Help Center on the instance.

---

## Provider API categories — 13, unchanged from 9.0

The service-provider administration API has **13 categories** in 9.1 `[DOC-9.1]` (DAUTO `[S31]`):

Access Control · Aggregator · Approvals · Blueprint · Catalog · Content Gateway · Custom Forms ·
Custom Resource Types & Actions · Instances · Orchestrator Gateway · Policies · Projects ·
Provisioning Service

**The 9.0 page lists the same 13 with the same descriptions** `[DOC-9.0]` (DAUTO `[S33]`). This is a
verified **no-change** between versions, and it is worth stating as a finding rather than omitting as
a non-event.

It is also a worked example of catching a false delta. A summarisation pass over the 9.1 page
annotated **"Custom Resource Types & Actions"** and **"Instances"** as *new in VCF 9.1*. Diffing
against the 9.0 page showed both were already listed there. The annotation was discarded as an
artifact (DAUTO `[S31]` vs `[S33]`). If you see that claim anywhere, it is wrong.

The 9.0 page additionally states which services are **excluded** from this set: "ABX, Deployment,
Deployment Metrics, Identity, and Onboarding (available only in VCF Automation for VM Apps)"
`[DOC-9.0]` (DAUTO `[S33]`). No equivalent exclusion sentence was captured from the 9.1 page — a
retrieval gap, not evidence of change.

> `[UNVERIFIED]` — **an unresolved count discrepancy between research dossiers.** The auth dossier's
> source inventory describes the *same* 9.0 page as listing "10 All Apps API categories" (DAUTH
> `[S62]`), while the automation dossier reads 13 from it (DAUTO `[S33]`). Both refer to the same
> URL. Thirteen is the count with the full enumeration behind it, so it is what this file uses, but
> the discrepancy is not resolved. Confirm on the instance before quoting a number in a document
> that matters.

---

## What 9.1 added on the provider and organisation side

All from the 9.1 What's New page for VCF Automation `[DOC-9.1]` (DAUTO `[S09]`).

**Provider management (cloud administration)**

1. **vDefend firewall delegation** — vDefend Distributed Firewall and Gateway Firewall support
   directly within VCF Automation, allowing firewall services to be delegated to organisations with
   RBAC and predefined security profiles.
2. **Default IP block configuration** — providers configure default private VPC and private Transit
   Gateway IP blocks in the Provider Management UI, overridable per organisation.
3. **Self-service Avi Load Balancer** — "Full self-service support for Avi Load Balancer" with quota
   management, for **both All Apps and VM Apps** organisations.
4. **Multiple external connections** — multiple exit points for external traffic, via centralised
   connections and distributed VLAN connections.
5. **Shared VLAN extension subnets** — VLAN extension NSX subnets shareable across multiple
   organisations for direct device connectivity.
6. **External IP blocks** — **"IP spaces" renamed to "external IP blocks"**, with multiple CIDRs,
   custom IP ranges, and **Infoblox External IPAM** integration. This is a rename *and* a capability
   change; if a runbook says "IP spaces", it is 9.0-era vocabulary.
7. **Multi-supervisor region quota** — quota across multiple supervisors in a region, with capacity
   sharing options.

**Organisation management**

1. **Day-2 namespace allocation changes** — modify resource limits, VM classes, storage classes and
   shared subnets after creation. (See the P6 note: the documented permission matrix shows no update
   verb on `SupervisorNamespace`, so how this is expressed at the CRD level is `[UNVERIFIED]`.)
2. **Project content libraries** — projects can hold dedicated content libraries, spanning multiple
   projects.
3. **Canonical content libraries** — subscribed libraries providing validated Ubuntu LTS images.
4. **Shared NSX subnets** — org-wide NSX subnets shareable across multiple namespaces.
5. **Transit Gateway configurations** — multiple NSX Transit Gateways with NAT, IPsec VPN and
   vDefend Gateway Firewall support.

**No VCF Automation feature deprecations** were found on any fetched 9.1 page. The only deprecation
anywhere in this area is the `x-vcloud-authorization` header `[DOC-9.1]` (DAUTO `[S09]` `[S19]`).

---

## Terraform

The documentation treats Terraform as a first-class route and names **three** providers `[DOC-9.1]`
(DAUTO `[S27]`):

| Provider | 9.1 scope |
|---|---|
| **Terraform Provider for VCF Automation** | Provider Management UI **and a subset of the Organization UI**; "greenfield" examples for fresh installations. |
| **Terraform Provider for Kubernetes** | Organization UI resources exposed through the **VCF Automation Kubernetes API layer**, such as projects. |
| **Terraform Provider for VMware Aria Automation** | VM Apps organisations **and All Apps resources not yet exposed through Kubernetes API layers**, including blueprints. |

Resources by role `[DOC-9.1]` (DAUTO `[S27]`): provider administrators get organisations, regions,
quotas, networking, content libraries and supervisor namespaces; All Apps organisation administrators
get VCF services projects, content libraries, Virtual Private Clouds, subnets, blueprints and
catalogs; organisation users provision IaaS services and deploy catalogs.

Usage examples are documented at `https://<FQDN>/automation/api-docs/#/terraform-provider`
`[DOC-BOTH]` (DAUTO `[S26]` `[S27]`).

The third row is the one to remember: **not everything in an All Apps org is reachable through the
Kubernetes layer**, and the docs say so explicitly.

---

## Lookup routes

1. **In-product API Help Center — authoritative, per-instance.** Sign in to the VCF Automation
   interface and select **admin > API Help Center > Automation APIs** in the upper right
   `[DOC-BOTH]` (DAUTO `[S33]` `[S31]`). This is the correct answer for anything this file marks
   `[UNVERIFIED]`, including the token endpoint.
2. **In-product api-docs.** `https://<FQDN>/automation/api-docs/#/<section>` — verified for the
   `terraform-provider` section in both versions `[DOC-BOTH]` (DAUTO `[S26]` `[S27]`).
3. **Broadcom Developer Portal.** `https://developer.broadcom.com/xapis/<api-slug>/latest/`.
   Confirmed slugs: `provider-infrastructure-apis`, `all-apps-org-access-control`,
   `org-management-vm-apps-org`, `vm-apps-org-catalog` `[DOC-9.1]` (DAUTO `[S19]` `[S20]` `[S25]`
   `[S18]`). Each API page carries a **REST API Index** and an **API ChangeLog** — the ChangeLog is
   the right place to diff versions. `[UNVERIFIED]` — other slugs are extrapolated from those four
   and were not fetched; every portal page fetched reported "9.1 (latest)" and **no 9.0-pinned URL
   pattern was found**, so portal content cannot be attributed to 9.0.
4. **The cluster.** See *Ask the cluster first*. For CRDs this outranks 1–3.
5. **`vcf-api-discovery`** for the general method, including the spec corpus — which, for this
   product, will confirm the absence rather than an endpoint.

---

## Gaps

Carried forward from the research; state these as gaps rather than filling them.

- **All Apps / provider token endpoint URL** — undocumented; the page that would carry it 404s
  (DAUTO gap 3; DAUTH gap 5).
- **`grant_type` value for the VIDB token exchange** — elided as `...` in the source (DAUTO gap 1).
- **Whether the VIDB bearer token is accepted by the All Apps / provider REST surface** — VCF
  Automation is listed among covered components, but no page ties the token to this API's
  `Authorization` JWT requirement. Inference only.
- **Whether `vcf context create` against a VCF Automation endpoint yields the context named `cci`** —
  the two facts come from different pages.
- **Full CRD schemas, status conditions, mutability** — not documented; use `kubectl explain`.
- **How day-2 namespace allocation changes are expressed at the CRD level**, given no update verb in
  the documented permission matrix.
- **Quota object model beyond `RegionStorageClassQuotas`**, and how multi-supervisor capacity sharing
  is represented.
- **Concrete REST paths** for projects, cloud accounts/zones, day-2 resource actions and ABX — all
  rate-limited out of the research (DAUTO gaps 4–7). The Aria-era IaaS base path was never confirmed
  and must not be assumed (DAUTO gap 5).
- **9.0-pinned developer-portal content** — no 9.0 URL pattern was discovered (DAUTO gap 11).
- **Category count discrepancy between dossiers** for the 9.0 categories page — 13 vs 10 (see above).
- **Whether the VM Apps tenant-local token service is deprecated in 9.1** in favour of VIDB — the two
  coexist and no fetched page states a precedence or migration (DAUTO gap 14).
