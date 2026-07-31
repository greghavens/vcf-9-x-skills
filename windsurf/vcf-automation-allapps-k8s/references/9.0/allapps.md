# VCF Automation — All Apps organizations, VCF 9.0

**Applies to:** VCF Automation as shipped in VMware Cloud Foundation **9.0**.
**Do not apply this file to 9.1.** Use `../9.1/allapps.md`, and `../deltas.md` for the change list.

**Sources.** `DAUTO` = `research/vcf-automation.md` (its own page refs carried through as `[S##]`);
`DAUTH` = `research/foundation-auth-identity.md`; `DTOOL` =
`research/tooling-powercli-vks-sdk.md`; `SPECINV` = `research/spec-inventory/`.

---

## READ THIS FIRST — 9.0 evidence is the weakest in this skill

Two separate problems compound here.

**1. There is no VCF Automation OpenAPI specification at either tag.** `SPECINV` covers fifteen
products across the `9.0.0.0` and `9.1.0.0` tags of `github.com/vmware/vcf-api-specs`; VCF Automation
is not one of them. Nothing in this file is spec-confirmed, because there is no spec.

**2. The 9.0 documentation for the All Apps Kubernetes surface was not retrieved.** The page that
enumerates the CCI CRDs, the `cci` kubectl context, the `SupervisorNamespace` manifest and the
role/verb matrix is a **9.1** page (DAUTO `[S32]`). No 9.0 counterpart was fetched. What the 9.0 doc
set *does* establish is that the All Apps organization exists and is the Kubernetes/VCD-derived
surface driven by CRDs and supervisor namespaces `[DOC-9.0]` (DAUTO `[S06]` `[S07]`) — the org type
is confirmed; its CRD inventory is not.

**Do not import the 9.1 CRD detail into a 9.0 answer as though it were verified for 9.0.** Where
9.0-specific evidence is missing this file says so and sends you to the cluster. That is not a
formality: on this surface the running API server is better evidence than any document, and for 9.0
it is very nearly the *only* evidence.

Additional context: Broadcom TechDocs returned **HTTP 429** repeatedly during research, which is why
several 9.0 leaf pages (projects, cloud accounts, day-2 resource actions, ABX) have no verified
paths at all.

| Tag | Meaning |
|---|---|
| `[DOC-9.0]` | Read from a VCF 9.0 documentation page. |
| `[DOC-BOTH]` | Independently read in both the 9.0 and 9.1 doc sets. |
| `[DOC-9.1]` | Read from a 9.1 page only. **Appears here solely where explicitly flagged as not verified for 9.0.** |
| `[UNVERIFIED]` | Not established by any retrieved page. Do not state as fact. |

---

## Contents

- [Prerequisites](#prerequisites) — **read before any CRD or call**
  - [P1 — you are in an All Apps organization, not a VM Apps organization](#p1--you-are-in-an-all-apps-organization-not-a-vm-apps-organization)
  - [P2 — a kubectl context to the All Apps surface is established](#p2--a-kubectl-context-to-the-all-apps-surface-is-established)
  - [P3 — a region is available to the organization](#p3--a-region-is-available-to-the-organization)
  - [P4 — region quota is allocated](#p4--region-quota-is-allocated)
  - [P5 — the project exists and the supervisor namespace is assigned to it](#p5--the-project-exists-and-the-supervisor-namespace-is-assigned-to-it)
  - [P6 — auth: the provider token flow, and the gap](#p6--auth-the-provider-token-flow-and-the-gap)
- [Ask the cluster — for 9.0 this is not optional](#ask-the-cluster--for-90-this-is-not-optional)
- [What the 9.0 docs establish about All Apps](#what-the-90-docs-establish-about-all-apps)
- [Provider API categories — 13](#provider-api-categories--13)
- [Provider and All Apps REST conventions — attribution warning](#provider-and-all-apps-rest-conventions--attribution-warning)
- [Terraform](#terraform)
- [Lookup routes](#lookup-routes)
- [Gaps](#gaps)

---

## Prerequisites

Each states what must be true, **how to verify it**, and whether 9.1 differs.

### P1 — you are in an All Apps organization, not a VM Apps organization

**Must be true:** the organization is an **All Apps** organization. VCF Automation 9.0 has two
organization types, "with different consumption mechanisms" `[DOC-9.0]` (DAUTO `[S06]`):

- **All Apps** — the Kubernetes/VCD-derived surface, driven by CRDs and supervisor namespaces
  `[DOC-9.0]` (DAUTO `[S06]` `[S07]`).
- **VM Apps** — the Aria-Automation-derived surface: blueprints, catalog, deployments, projects,
  cloud accounts, cloud zones, extensibility/ABX, Orchestrator `[DOC-9.0]` (DAUTO `[S22]`).

**This is the most expensive thing to get wrong on this page.** They are different APIs, not
different options on one API. If the question involves `/blueprint/api/blueprints`,
`/catalog/api/items/{id}/request` or `/deployment/api/deployments` — all verified 9.0 VM Apps paths
`[DOC-9.0]` (DAUTO `[S24]` `[S23]`) — you are in the wrong org type and the wrong skill; go to
`vcf-automation-vmapps`.

**How to verify:**
- Provider Management Portal at `https://<FQDN>/provider`; tenants at `https://<FQDN>/automation`.
  Both surfaces exist on the same FQDN in both versions `[DOC-BOTH]` (DAUTO `[S07]` `[S29]`).
- The 9.0 tenant tooling for All Apps is listed as: VCF Automation UI, the **self-service catalog**
  ("the catalog in VCF Automation for All Apps is the self-service interface where you can provision
  workloads from blueprints"), the **IaaS Services Console** (provision "VMs, Kubernetes, volumes,
  storage, load balancers and networking objects"), **VCF CLI v9.0**, and the **Local Consumption
  Interface** for environments without VCF Automation access `[DOC-9.0]` (DAUTO `[S06]`).
- Functionally: if a kubectl context into the CCI API group exists, you are on the All Apps surface.
  See P2.

**9.1 difference:** unchanged in substance. 9.1 rewords what org administrators do — "create and
assign projects and vSphere Namespaces tailored for different application teams" — and documents the
All Apps org management flow explicitly through CRDs and `kubectl` `[DOC-9.1]` (DAUTO `[S11]`
`[S32]`).

### P2 — a kubectl context to the All Apps surface is established

**Must be true:** you have a working kubeconfig context against the All Apps Kubernetes surface.

**How to establish it.** In VCF 9.x the login step is the **VCF CLI** (binary `vcf`), **not**
`kubectl vsphere login` — that command appears on no page in the VCF 9.x doc tree, confirmed by a
site-restricted search that returned no page containing the string `[DOC-BOTH]` (DTOOL). The 9.0 and
9.1 doc sets carry **identical** login text `[DOC-BOTH]` (DTOOL; DAUTH `[S33]` `[S63]`):

```bash
vcf context create --help

vcf context create --endpoint <ENDPOINT> \
                   --username <SSO-USER> \
                   --ca-certificate <PATH-TO-CA-CERT>

vcf context list
vcf context use <context-name>
```

The password can be supplied interactively or via `VCF_CLI_VSPHERE_PASSWORD` `[DOC-BOTH]` (DTOOL).
The CLI writes the kubeconfig context; `kubectl` consumes it `[DOC-BOTH]` (DTOOL).

> `[UNVERIFIED]` for 9.0: **the context name.** The literal context name `cci`, and the
> `kubectl --context cci ...` idiom, come from the **9.1** page (DAUTO `[S32]`). No 9.0 page naming
> the context was retrieved. Run `kubectl config get-contexts` and use what is actually there rather
> than assuming `cci`.
>
> `[UNVERIFIED]` for 9.0 as well: the `--api-token` / `--tenant-name` form of `vcf context create`
> for a VCF Automation endpoint is documented in the **9.1** doc set (DAUTH `[S34]`). The 9.0
> documented form is the `--username` one above.

**How to verify:**
```bash
vcf context list
kubectl config get-contexts
kubectl --context <ctx> api-resources --api-group=infrastructure.cci.vmware.com
```
An empty result on the third command means you are not on the All Apps surface — or that this
cluster serves a different group. Investigate before proceeding; do not assume the group name.

**9.1 difference:** VCF CLI is **v9.1** in 9.1 versus **v9.0** in 9.0 `[DOC-9.1]`/`[DOC-9.0]` (DAUTO
`[S34]` / `[S06]`), and 9.1 adds the documented API-token login form. The `vcf context create`
syntax is otherwise identical across versions `[DOC-BOTH]` (DTOOL).

### P3 — a region is available to the organization

**Must be true:** a region exists and the organization can consume it. Regions are provider-managed
in 9.0: the Terraform Provider for VCF Automation manages "organizations, regions, region quotas,
networking, content libraries, supervisor namespaces" for the Provider Management Portal
`[DOC-9.0]` (DAUTO `[S26]`). A supervisor namespace is created against a region.

**How to verify:** from the Provider Management Portal, or from the cluster:
```bash
kubectl --context <ctx> get regions
kubectl --context <ctx> explain supervisornamespace.spec
```
`[UNVERIFIED]` for 9.0 — the `Region` CRD, its permissions and the `spec.regionName` field are
documented only on the 9.1 page (DAUTO `[S32]`). The *concept* is 9.0-verified via the Terraform
resource list; the CRD shape is not.

**9.1 difference:** 9.1 documents `Region` as a read-only CRD for the org Admin role `[DOC-9.1]`
(DAUTO `[S32]`).

### P4 — region quota is allocated

**Must be true:** the organization holds quota in the target region. **Region quotas** are named as
a provider-managed Terraform resource in 9.0 `[DOC-9.0]` (DAUTO `[S26]`).

**How to verify:** Provider Management Portal, or `kubectl get` against whatever quota kinds
`api-resources` reveals on your cluster.

`[UNVERIFIED]` for 9.0 — the quota object model is not documented on any retrieved 9.0 page.
`RegionStorageClassQuotas` is named on the 9.1 page only (DAUTO `[S32]`).

**9.1 difference:** 9.1 adds **multi-supervisor region quota** — quota across multiple supervisors
in a region, with capacity sharing `[DOC-9.1]` (DAUTO `[S09]`). In 9.0 there is no documented
multi-supervisor quota capability; do not design for it here.

### P5 — the project exists and the supervisor namespace is assigned to it

**Must be true:** a project exists to own the namespace, and the namespace is assigned to it.
Projects are a 9.0 Kubernetes-layer resource: the Terraform Provider for Kubernetes performs CRUD
against Organization Portal resources **through the Kubernetes API**, covering "projects, content
libraries, virtual private clouds, subnets" `[DOC-9.0]` (DAUTO `[S26]`). Supervisor namespaces are
in the provider-administrator resource list `[DOC-9.0]` (DAUTO `[S26]`).

**How to verify:**
```bash
kubectl --context <ctx> get projects
kubectl --context <ctx> get supervisornamespaces -n <project>
```

`[UNVERIFIED]` for 9.0 — that the supervisor namespace is created *into the project as a Kubernetes
namespace* (`metadata.namespace: <project>`) is shown in the **9.1** example (DAUTO `[S32]`). It is
the natural reading of the 9.0 Terraform resource split, but it is not 9.0-documented.

**9.1 difference:** 9.1 documents the manifest, the `Project`/`SupervisorNamespace` CRDs and the
role/verb matrix, and adds project content libraries, canonical content libraries and day-2
namespace allocation changes `[DOC-9.1]` (DAUTO `[S32]` `[S09]`).

### P6 — auth: the provider token flow, and the gap

**Must be true:** you hold a credential the surface accepts.

**For the Kubernetes surface:** the kubeconfig from P2 carries it.

**For the provider management API, 9.0 documents a full device-authorization-grant flow**
`[DOC-9.0]` (DAUTO `[S16]`):

1. Create the refresh token in the UI: `https://<vcfa.url>/provider` → **My Account > API Tokens >
   NEW**, using the service administrator's username.
2. Request device authorization:
   ```bash
   curl -k 'https://<vcfa.url>/tm/oauth/tenant/<organization>/device_authorization' \
     --header 'Content-Type: application/x-www-form-urlencoded' \
     --data-urlencode 'client_id=<serviceAdminUserName>'
   ```
   The response includes `user_code` and `device_code`.
3. Approve: **Service Accounts** tab → **Review Access Requests** → paste `user_code` → **GRANT**.
4. Exchange for an access token:
   ```bash
   curl -k 'https://<vcfa.url>/tm/oauth/tenant/<organization>/token' \
     --header 'Content-Type: application/x-www-form-urlencoded' \
     --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:device_code' \
     --data-urlencode 'refresh_token=<refresh_token>' \
     --data-urlencode 'client_id=<username>' \
     --data-urlencode 'device_code=<device_code>'
   ```
   Returns `access_token`, valid **one hour**.
5. Refresh when expired — **note the path in the source omits `/tm`**:
   ```bash
   curl --location 'https://<vcfa.url>/oauth/tenant/<org>/token' \
     --header 'Content-Type: application/x-www-form-urlencoded' \
     --data-urlencode 'grant_type=refresh_token' \
     --data-urlencode 'refresh_token=<refreshToken>'
   ```

> The `/tm` vs no-`/tm` inconsistency between steps 2–4 and step 5 is **reproduced verbatim from the
> source page** and is not resolvable from it (DAUTO gap 2). Test both before depending on either.
> The `-k` in those examples is the doc's own; treat it as example-only — the documented remedy for
> TLS trust is to install the CA, not to disable verification `[DOC-BOTH]` (DAUTH).

**For the All Apps / provider REST surface**, the documented header contract is JWT via
`Authorization`, with `x-vcloud-authorization` **deprecated**, plus `X-VMWARE-VCLOUD-TENANT-CONTEXT`
(org-scoped) and `X-VMWARE-VCLOUD-AUTH-CONTEXT` (multisite) — see the attribution warning below,
because that reference page reports itself as 9.1/latest `[DOC-9.1]` (DAUTO `[S19]`; DAUTH `[S46]`).

> `[UNVERIFIED]` — **the All Apps token endpoint URL is not documented in anything retrieved, in
> either version.** The page titled "Generating an All Apps Access Token" at
> `.../about-the-vcf-automation-api/generating-an-access-token.html` returned **404 on three
> attempts** despite appearing in search results (DAUTO gap 3; DAUTH gap 5). The provider flow above
> is *documented*, but no page states that it issues the JWT the All Apps REST surface accepts.
> **Do not construct a token URL.** Get it from the in-product API Help Center.

**9.1 difference:** 9.1 adds the fleet-wide **VCF Identity Broker (VIDB)** OAuth flow covering VCF
Automation among other components, and moves token administration to **Fleet Management > Identity &
Access**, with API token TTL defaulting to **30 days** and access token TTL to **30 minutes**
`[DOC-9.1]` (DAUTO `[S30]` `[S17]`). **Neither exists in 9.0** — the 9.0 SSO tree contains no API
client, API token, OAuth client or role management pages at all `[DOC-9.0]` (DAUTH `[S53]`).

---

## Ask the cluster — for 9.0 this is not optional

Because the 9.0 CRD documentation was never retrieved, the API server is not a cross-check here; it
is the source.

```bash
kubectl --context <ctx> api-resources --api-group=infrastructure.cci.vmware.com
kubectl --context <ctx> api-versions | grep infrastructure.cci
kubectl --context <ctx> get crd | grep cci

# which versions are served / stored on THIS cluster
kubectl --context <ctx> get crd <name>.infrastructure.cci.vmware.com \
  -o jsonpath='{range .spec.versions[*]}{.name}{" served="}{.served}{" storage="}{.storage}{"\n"}{end}'

kubectl --context <ctx> explain supervisornamespace.spec
kubectl --context <ctx> explain supervisornamespace --recursive
kubectl --context <ctx> auth can-i --list -n <project>
```

`kubectl --context cci api-resources` is documented as the discovery command for this surface, on a
9.1 page `[DOC-9.1]` (DAUTO `[S32]`); the rest is standard kubectl and is the recommended generic
route in the tooling research, which notes the product docs do not present it (DTOOL).

**Do not assume `v1alpha2` for 9.0.** That version string is from the 9.1 page. The platform has a
documented precedent for exactly this kind of drift: VCF 9.0 docs state the VM Operator API is
`v1alpha2`/`v1alpha3` while the upstream project shows `v1alpha5`, and the tooling research's
instruction is to resolve it at runtime with `kubectl api-resources` / `kubectl explain` rather than
trusting either (DTOOL). Apply the same rule to the CCI group.

For the general method see `vcf-api-discovery`.

---

## What the 9.0 docs establish about All Apps

Verified 9.0 statements, and nothing beyond them.

- **Product identity.** "VMware Cloud Foundation Automation (formerly VMware Aria Automation) or VCF
  Automation enables IT teams and cloud service providers (CSPs) to deliver a self-service private
  cloud for AI, Kubernetes, and VM-based applications." The Aria rename is stated explicitly, so the
  lineage is confirmed rather than assumed `[DOC-9.0]` (DAUTO `[S10]`).
- **Four functional areas** `[DOC-9.0]` (DAUTO `[S10]`): **Cloud Services** (consumed via UI, CLI and
  API); **Provider Management** (infrastructure teams managing services "across multiple vCenter and
  VCF instances"); **Organization Management** (org admins "organize and govern resources allocated
  to them among application teams"); **vSphere Supervisor** ("running Kubernetes workloads directly
  on ESX hosts and creating upstream Kubernetes clusters within dedicated namespaces").
- **Consumption framing.** VCF Automation lets you "provision VMs, Kubernetes workloads and other
  Cloud Services by using self-service UI, API, and CLI" `[DOC-9.0]` (DAUTO `[S03]`).
- **Two org types**, All Apps and VM Apps, with different consumption mechanisms `[DOC-9.0]`
  (DAUTO `[S06]`).
- **Tooling** as listed in P1, including **VCF CLI v9.0** `[DOC-9.0]` (DAUTO `[S06]`).
- **UI surfaces** `/provider` and `/automation` `[DOC-BOTH]` (DAUTO `[S07]`).

What is **not** in the 9.0 evidence: the CRD inventory, the `SupervisorNamespace` manifest, the
`cci` context name, and the Admin/DevOps permission matrix. All four are 9.1-page facts.

One scope clarification that saves time in conversation: **"Advanced Services" in the 9.0 doc tree is
not a VCF Automation sub-feature.** It is a list of add-on products — VMware Live Recovery Suite,
Data Services Manager, Private AI Foundation with NVIDIA, vDefend, Avi Load Balancer, Tanzu Platform
& Tanzu Data, Network Observability `[DOC-9.0]` (DAUTO `[S04]`). Several of them become consumable
*through* VCF Automation in 9.1 (vDefend, Avi) — see `../deltas.md`.

---

## Provider API categories — 13

The 9.0 service-provider administration API has **13 categories** `[DOC-9.0]` (DAUTO `[S33]`):

Access Control · Aggregator · Approvals · Blueprint · Catalog · Content Gateway · Custom Forms ·
Custom Resource Types & Actions · Instances · Orchestrator Gateway · Policies · Projects ·
Provisioning Service

The 9.0 page also states which services are **excluded**: "ABX, Deployment, Deployment Metrics,
Identity, and Onboarding (available only in VCF Automation for VM Apps)" `[DOC-9.0]` (DAUTO
`[S33]`).

**The 9.1 page lists the same 13 with the same descriptions — a verified no-change** `[DOC-9.1]`
(DAUTO `[S31]`). Two of them, "Custom Resource Types & Actions" and "Instances", were at one point
flagged as *new in 9.1*; the 9.0 page above already lists both, and the claim was discarded as a
summarization artifact. If you meet that claim, correct it.

> `[UNVERIFIED]` — **count discrepancy between research dossiers.** The auth dossier's source
> inventory describes this same 9.0 page as listing "10 All Apps API categories" (DAUTH `[S62]`),
> while the automation dossier reads 13 from it with a full enumeration (DAUTO `[S33]`). Thirteen is
> the better-supported count and is what this file uses, but the discrepancy is unresolved. Confirm
> on the instance before putting a number in a document that matters.

`[UNVERIFIED]` — no concrete REST path for any of these 13 categories was retrieved for 9.0.

---

## Provider and All Apps REST conventions — attribution warning

The conventions documented for this surface are: URN identifiers rather than bare UUIDs; the
`GET/POST/GET/PUT/DELETE` collection shape with **201** on create and **204** on delete; **202 plus
a `Location` header** for async work; and `application/json;version=9.1.0` content negotiation with
up to five major versions back supported `[DOC-9.1]` (DAUTO `[S19]` `[S20]`).

**Every developer-portal page fetched during research reported itself as "9.1 (latest)", and no
9.0-pinned URL pattern was found** (DAUTO gap 11). So these conventions are recorded as `[DOC-9.1]`
even in this 9.0 file. Two practical consequences:

- The version-negotiation rule ("up to 5 major versions back") implies `version=9.0.0` remains
  callable **against a 9.1 system**. It says nothing about what a 9.0 system accepts.
- Treat the conventions as *probably* applicable to 9.0 — the VCD lineage is the same — but do not
  present them to a user as 9.0-verified. `[UNVERIFIED]` for 9.0.

> **No base path appears in this file, deliberately.** The Aria-era IaaS base path that people
> expect for VCF Automation **was never confirmed on any fetched 9.0 or 9.1 page** and must not be
> assumed (DAUTO gap 5). The concrete paths for projects, cloud accounts and zones, day-2 resource
> actions, and ABX were all rate-limited out of the research (DAUTO gaps 4–7). If you need a real
> provider path, get it from the API Help Center on the instance.

---

## Terraform

9.0 documents **three** open-source Terraform providers as required for end-to-end operations
`[DOC-9.0]` (DAUTO `[S26]`):

| Provider | 9.0 scope |
|---|---|
| **Terraform Provider for VCF Automation** | CRUD for Provider Management Portal and Organization Portal resources. On GitHub and the HashiCorp registry. Resources: **organizations, regions, region quotas, networking, content libraries, supervisor namespaces**. A "greenfield" folder holds provider and tenant configuration samples. |
| **Terraform Provider for Kubernetes** | CRUD against Organization Portal resources **through the Kubernetes API**. Resources: **projects, content libraries, virtual private clouds, subnets**. |
| **Terraform Provider for VMware Aria Automation** | VM Apps organizations and resources not exposed through the Kubernetes API. Resources: **blueprints, catalogs**. |

Usage examples: `https://<FQDN>/automation/api-docs/#/terraform-provider` `[DOC-BOTH]` (DAUTO
`[S26]` `[S27]`).

This table is also the best 9.0 evidence for *what the All Apps object model contains* — regions,
region quotas, supervisor namespaces, projects, VPCs and subnets — even though the CRD kinds behind
them are not 9.0-documented.

**9.1 difference:** same three providers, re-scoped rather than replaced. See `../deltas.md`.

---

## Lookup routes

1. **In-product API Help Center — authoritative, per-instance.** For the service-provider / All Apps
   side: sign in and select **admin > API Help Center > Automation APIs** in the upper right
   `[DOC-BOTH]` (DAUTO `[S33]` `[S31]`). This is the correct answer for anything marked
   `[UNVERIFIED]` here, including the token endpoint and every concrete REST path.
2. **In-product api-docs.** `https://<FQDN>/automation/api-docs/#/<section>` — verified for the
   `terraform-provider` section `[DOC-BOTH]` (DAUTO `[S26]`).
3. **Broadcom Developer Portal.** `https://developer.broadcom.com/xapis/<api-slug>/latest/`, with
   confirmed slugs `provider-infrastructure-apis`, `all-apps-org-access-control`,
   `org-management-vm-apps-org`, `vm-apps-org-catalog`. **Attribution warning:** every page fetched
   reported 9.1/latest, and no 9.0-pinned pattern was found — so the portal cannot be used as a 9.0
   source (DAUTO gap 11). Other slugs are extrapolated and unverified (DAUTO gap 12).
4. **The cluster.** See above. For 9.0 CRDs this is the primary route, not a cross-check.
5. **`vcf-api-discovery`** for the general method — which, for this product, confirms the absence of
   a spec rather than an endpoint.

---

## Gaps

State these as gaps.

- **The entire 9.0 CRD surface** — group versions, kinds, schemas, the context name, and the
  permission matrix are documented only on a 9.1 page. Resolve on the cluster.
- **All Apps token endpoint URL** — undocumented in both versions; the page that would carry it 404s
  (DAUTO gap 3; DAUTH gap 5).
- **`/tm` prefix inconsistency** in the 9.0 provider token flow, steps 2–4 versus step 5 — reproduced
  verbatim from the source, unresolvable from it (DAUTO gap 2).
- **Concrete REST paths for the 13 provider categories** — none retrieved for 9.0.
- **Projects, cloud accounts/zones, day-2 resource actions, ABX base paths** — all rate-limited out
  (DAUTO gaps 4–7). The Aria-era IaaS base path was never confirmed and must not be assumed
  (DAUTO gap 5).
- **9.0-pinned developer-portal content** — no URL pattern exists for it (DAUTO gap 11).
- **Category count discrepancy between dossiers** — 13 vs 10 for the same 9.0 page (see above).
- **Pipelines / Code Stream** — no VCF Automation pipelines component appeared on any fetched 9.0 or
  9.1 page. Whether it was dropped in the Aria→VCF transition or lives elsewhere is **unresolved**;
  do not assert either way (DAUTO gap 8).
