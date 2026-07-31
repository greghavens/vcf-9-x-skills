# Broadcom doc portals — navigating without guessing URLs

Use this **after** the spec corpus (`spec-corpus.md`) and live discovery (`live-discovery.md`). The
portals are the right source for *prose* — auth flows, pagination, rate limits, concurrency rules,
deprecation statements, "what's new" — and for products the corpus does not cover at a given version
(notably NSX at 9.0).

The single most important rule is at the bottom of §4 and it is worth stating first:

> **Never construct a deep page URL by guessing the slug. Fetch the guide landing page and read its
> children.**

Broadcom's slugs are semantic but frequently stale, occasionally misspelled, and inconsistent between
the 9.0 and 9.1 subtrees. Guessing produces 404s that are easy to misread as "the feature doesn't
exist."

---

## Contents

- [1. Two portals, two jobs](#1-two-portals-two-jobs)
- [2. developer.broadcom.com — version-pinned API references](#2-developerbroadcomcom--version-pinned-api-references) (root pattern · verified slugs · the stale `vmware-cloud-foundation-api` trap · sub-page patterns · NSX category-slug divergence · static NSX mirror)
- [3. techdocs.broadcom.com — product documentation trees](#3-techdocsbroadcomcom--product-documentation-trees) (canonical grammar · top-level guide slugs · release-notes path traps · 5.2-era slugs · `opnapi` typo · legacy `vr-ops` slugs · other deep links)
- [4. The method: fetch the landing page, read its children](#4-the-method-fetch-the-landing-page-read-its-children)
- [5. Failure signatures — do not misread these as "it doesn't exist"](#5-failure-signatures--do-not-misread-these-as-it-doesnt-exist) (SPA shell · HTTP 429 · HTTP 403)

---

## 1. Two portals, two jobs

| Host | Holds | Version pinning |
|---|---|---|
| `developer.broadcom.com` | API references (per-operation pages, category tables), SDK downloads, spec ZIPs | path segment: `/9.0/`, `/9.1/`, `/9.0.0/`, `/9.1.0/`, or `/latest/` |
| `techdocs.broadcom.com` | Product documentation: admin guides, release notes, upgrade procedures, SDK setup | path segment: `/9-0/`, `/9-1/` (hyphen, not dot) |

---

## 2. developer.broadcom.com — version-pinned API references

### Root pattern

```
https://developer.broadcom.com/xapis/<api-slug>/<version>/
```

`<version>` is `latest` or a pinned value. **Prefer the pinned value.** `latest` currently resolves to
9.1 for most slugs, which silently contaminates a 9.0 answer.

### Verified slugs

```
https://developer.broadcom.com/xapis/sddc-manager-api/{9.0|latest}/
https://developer.broadcom.com/xapis/vcf-installer-api/{9.0|latest}/
https://developer.broadcom.com/xapis/vcf-operations-api/{9.0|9.1|latest}/
https://developer.broadcom.com/xapis/vcf-operations-for-networks-api/{9.0|9.1|latest}/
https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/{9.0.0|9.0.1|9.0.2|9.1.0}/
https://developer.broadcom.com/xapis/log-management-api/latest/
https://developer.broadcom.com/xapis/realtime-metrics-api/latest/
https://developer.broadcom.com/xapis/vcf-operations-orchestrator-api/latest/
https://developer.broadcom.com/xapis/vcf-fleet-lcm-service-apis/latest/
https://developer.broadcom.com/xapis/vcf-sddc-lcm-service-apis/latest/
https://developer.broadcom.com/xapis/hcx-manager-appliance-management-apis/latest/
https://developer.broadcom.com/xapis/hcx-workload-migration-apis/latest/
https://developer.broadcom.com/xapis/vcf-business-services-console-apis/latest/
https://developer.broadcom.com/xapis/vmware-vsphere-kubernetes-service/latest/   (+ /api-docs.html)
https://developer.broadcom.com/xapis/vcf-cli-api/latest/
https://developer.broadcom.com/sdks/vcf-api-specification/latest    # spec ZIP downloads
https://developer.broadcom.com/powercli/all-powercli-modules
```

Note the NSX slug is still `nsx-t-data-center-rest-api` — the "NSX-T Data Center" product name is
long gone but the slug survives.

### Trap: `vmware-cloud-foundation-api` is stale

```
https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/   <-- serves 5.2.4
```

It is linked from techdocs as "the main VMware Cloud Foundation API reference", but `latest` there
serves **5.2.4**, not 9.x. For 9.x SDDC Manager use `sddc-manager-api`. If you land on a page whose
content looks like 5.2, you are on this slug.

### Sub-page patterns

**SDDC Manager / VCF Operations style** (category directories):
```
https://developer.broadcom.com/xapis/sddc-manager-api/9.0/<category>/      e.g. /domains/, /tokens/
https://developer.broadcom.com/xapis/vcf-operations-api/<version>/operation-index/
https://developer.broadcom.com/xapis/vcf-operations-api/<version>/changelog/
https://developer.broadcom.com/xapis/vcf-operations-api/latest/api-security-schema/
https://developer.broadcom.com/xapis/vcf-operations-api/latest/suite-api/api/<path>/<method>/
```
The last form is a per-operation deep link — `.../suite-api/api/alerts/get/` and
`.../suite-api/api/reports/get/` both resolve. `operation-index/` and `changelog/` are the two
highest-value pages for discovery and for version deltas respectively.

**NSX style** (flat HTML files):
```
<root>/method_<OperationId>.html      e.g. .../9.1.0/method_ReadTier0.html
<root>/<category>.html                e.g. .../9.1.0/networking_switching_segments.html
<root>/types_<TypeName>.html · <root>/schemas_<Name>.html
<root>/api_single_page.html           # consolidated; usually too large to fetch reliably
```
`method_<OperationId>.html` is the highest-value NSX page: it gives the verb and **all** applicable
path templates side by side, including the `global-infra` (Federation) and `orgs/{org}/projects/{p}`
(multi-tenancy) variants, plus query parameters. The category page is the best bulk-extraction page.

**NSX category slugs differ between 9.0 and 9.1 — a real trap:**

- **9.1 is function-first:** `networking_switching_segments.html`, `networking_routing_tier-0s.html`,
  `networking_routing_tier-1s.html`, `networking_nat_nat_rules_tier-0s.html`,
  `networking_load_balancing_lb_services.html`, `networking_vpn_ipsec_services.html`,
  `networking_ip_management_ip_pools.html`, `system_fabric_edge_clusters.html`,
  `inventory_groups.html`, `security_firewall.html`
- **9.0 is `policy_`-prefixed:** `policy_networking.html`, `policy_security.html`,
  `policy_security_east_west_security_distributed_firewall.html`, `management_plane_api_networking.html`

Adding or removing the `policy_` prefix is **not** a valid translation between the two:
`policy_networking_switching_segments.html` does not exist at 9.0.0, and the 9.1 DFW page is not
`security_east_west_security_distributed_firewall.html`. The nav taxonomy itself was regrouped — 9.0
groups by *Federation / Management Plane API / NSX Application Platform / Policy / System
Administration*; 9.1 regroups by function (Certificates, Enforcement Points, Federation, Inventory,
Monitoring, Multi-Tenancy, Networking, Policy, Search, Security, System, Troubleshooting, User
Management, VPC Networking) with **no** "Management Plane API" top-level group. **Navigate the
left-hand tree; do not translate slugs across versions.**

### Static mirror of the NSX API guide (best for prose)

```
https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.0.0/html/index.html
https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html
Pattern: .../API_NTDCRA_001/<nsx-version>/html/index.html
```
Each page self-identifies its version ("NSX API Guide", "NSX 9.1.0.0") — a useful contamination
check. Note `.../<version>/html/api_usage_user_authentication.html` returns **404** on this host; the
auth content lives inside `index.html`.

---

## 3. techdocs.broadcom.com — product documentation trees

### Canonical grammar

```
https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/{VERSION}/{GUIDE}[/{PAGE}[/{SUBPAGE}…]].html
    {VERSION} ∈ { "9-0", "9-1" }        # hyphen, not dot
```

The doc-set segment is literally `vcf-9-0-and-later`, and it holds **both** 9.0 and 9.1 as sibling
subtrees. Version landing page: `.../vcf-9-0-and-later/9-0.html`. Guide landing page:
`.../9-0/{guide}.html`; its children live at `.../9-0/{guide}/{page}.html`.

### Top-level guide slugs (present in both `9-0` and `9-1`)

`release-notes.html` · `overview-of-vmware-cloud-foundation-9.html` · `design.html` ·
`planning-and-preparation.html` · `deployment.html` (= "Deployment, Convergence, and Upgrade") ·
`licensing.html` · `building-your-private-cloud-infrastructure.html` · `vsphere-in-vcf.html` ·
`vsan-deployment-administration-and-monitoring.html` · `advanced-network-management.html` (= NSX) ·
`lifecycle-management.html` · `fleet-management.html` · `infrastructure-operations.html` ·
`workload-monitoring-and-observability.html` · `cost-and-capacity-management.html` ·
`workload-mobility.html` · `security-and-compliance.html` ·
`vsphere-supervisor-installation-and-configuration.html` · `provider-management.html` ·
`organization-management.html` ·
`configuration-of-vmware-cloud-foundation-operations-orchestrator.html` ·
`building-your-cloud-applications.html` · `private-ai.html` ·
`administration-sdks-cli-and-tools.html` · `vcf-advanced-services.html`

These top-level slugs are stable and safe to use directly. **Everything below them is not.**

### Trap: release-notes paths differ non-obviously between 9.0 and 9.1

|  | 9.0 | 9.1 |
|---|---|---|
| RN root | `.../9-0/release-notes/vmware-cloud-foundation-**90**-release-notes.html` | `.../9-1/release-notes/vmware-cloud-foundation-**9-1-0-0**-release-notes.html` |
| What's New | `.../vmware-cloud-foundation-90-release-notes/**platform-whats-new**.html` | `.../vmware-cloud-foundation-9-1-0-0-release-notes/**what-s-new**.html` |
| Per-component | `.../platform-whats-new/whats-new-{comp}.html` | `.../what-s-new/whats-new-{comp}.html` |
| BOM | `.../vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html` | `.../vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html` |
| Support notes | `.../platform-product-support-notes.html` | `.../vcf-91-product-support-notes.html` |
| Known issues | `.../component-specific.html` | `.../known-issues.html` |

`{comp}` (both versions): `vsphere`, `vsan`, `nsx`, `installer`, `vcf-ops`, `vcf-automation`,
`vcf-cli-api-sdk`.

Three separate things change: the RN **folder** slug (`90` vs `9-1-0-0`), the What's New **page**
slug (`platform-whats-new` vs `what-s-new`), and the support-notes/known-issues slugs. There is no
rule that maps one to the other. Observed 404s from naive pattern-matching:

- `.../9-1/…/vmware-cloud-foundation-9-1-0-0-release-notes/bill-of-materials.html` → 404
  (correct: `vmware-cloud-foundation-bill-of-materials.html`)
- `.../9-1/…/upgrade-sequence-to-9-1.html` → 404 (correct: `upgrade-sequence-to-91.html`)
- `.../9-0/release-notes/vmware-cloud-foundation-9-0-0-0-release-notes/what-s-new.html` → 404
  (9.0 uses the `90` folder and `platform-whats-new`)

### Trap: 9.1 pages that retain 5.2-era slugs

Titles say 9.1; the slugs do not. All of these are live 9.1 pages:

```
.../9-1/lifecycle-management/upgrade-workload-domains-to-vcf-5-2.html
.../9-1/…/apply-cloud-foundation-5-2-update-bundle.html
.../9-1/…/upgrade-the-management-domain-to-vmware-cloud-foundation-5-2.html
.../9-1/…/phase-3-import-and-upgrade-aria-automation-8-to-vcf-automation-9.html
```

The same pattern exists at 9.0 (`.../deployment/upgrading-cloud-foundation/upgrade-the-management-domain-to-vmware-cloud-foundation-5-2.html`,
`.../lifecycle-management/upgrade-workload-domains-to-vcf-5-2.html`). Other semantically surprising
slugs: LCM of VCF management components lives at `using-the-depot-configuration-tab.html`; the SDK
setup guide is `what-is-the-vsphere-web-services-sdk.html`; shrinking a workload domain is
`reduce-a-workload-domain-1.html`.

### Trap: `opnapi-for-sddc-manager.html` is misspelled upstream

```
.../{9-0|9-1}/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/
    setup-for-development-with-openapi/opnapi-for-sddc-manager.html
```

Note **`opnapi`**, not `openapi`. The typo is in the real published URL in both doc sets. Spelling it
correctly gives a 404. (Content: SDDC Manager exposes ~280 REST interfaces; the page does **not**
provide a spec download URL.)

### Trap: legacy `vr-ops` slugs in the VCF Operations API topics

```
.../{9-0|9-1}/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/
    getting-started-with-the-api/acquire-an-authentication-token.html
    client-workflow-overview/vrealize-operations-manager-api-rest-requests.html
    using-the-api-with-vrealize-operations-manager.html
```
The `vr-ops` / `vrealize-operations-manager` slugs persist in **9.1** URLs even though the product is
now called VCF Operations.

### Other useful deep links (verified, but still prefer landing-page navigation)

```
.../9-1/deployment/vcf-management-appliances.html          # THE component/architecture page
.../9-1/deployment/upgrading-cloud-foundation.html         # 9.0.x -> 9.1 sequence
.../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/upgrade-sequence-to-91.html
.../9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development.html
```

PDFs (note both live under `.../vcf/vcf-90/`):
```
https://techdocs.broadcom.com/content/dam/broadcom/techdocs/us/en/pdf/vmware/vcf/vcf-90/vmware-cloud-foundation-9-1.pdf
https://techdocs.broadcom.com/content/dam/broadcom/techdocs/us/en/pdf/vmware/vcf/vcf-90/vmware-cloud-foundation-9-0.pdf
```

---

## 4. The method: fetch the landing page, read its children

Because slugs are stale, misspelled and version-divergent, **URL construction is not a viable
strategy** below the top level. The reliable procedure:

1. Start at the **version landing page** (`.../vcf-9-0-and-later/9-1.html`) or the **guide landing
   page** (`.../9-1/lifecycle-management.html`). These are stable and enumerate their children.
2. **Read the child links out of the fetched page.** Landing pages reliably list their sub-pages.
3. Follow one hop at a time. Do not skip levels by assembling a three-segment path from guesses.
4. For API references, start at the pinned reference root
   (`https://developer.broadcom.com/xapis/<slug>/<version>/`) and use its category index or
   `operation-index/`; for NSX, use the left-hand nav tree.
5. Only reuse a deep URL verbatim if you have seen it succeed — including the ones in this file.

If you need a specific slug and cannot find it by navigation, a site-restricted web search
(`site:techdocs.broadcom.com …`) is a legitimate way to *discover* the URL. Use search for URL
discovery only; source the actual facts from the fetched page.

---

## 5. Failure signatures — do not misread these as "it doesn't exist"

### The developer-portal SPA shell

`developer.broadcom.com` is a single-page app. **A nonexistent page returns HTTP 200 with the nav
shell** — the left-hand category menu and nothing else, sometimes with "Object Not Found". It does
**not** return a clean 404.

**Signature:** the fetch yields only category links, with no verb/path table, no parameter table and
no operation description.

**Meaning:** *your URL is wrong.* It does **not** mean the endpoint is absent from that version.
Go back to the reference root and navigate. Observed instances: `9.1.0/deprecated_methods.html` and
`9.1.0/removed_methods.html` returned the shell only; `9.1.0/api_single_page.html` returned a
fetch/server error. Those pages may well exist under different names — the shell response is not
evidence either way.

Never write "this operation does not exist in <version>" on the strength of a shell response. Either
confirm the absence in the spec corpus (which *is* dispositive when the product is present at that
version — see `spec-corpus.md` §4) or say the page could not be retrieved.

### HTTP 429 — rate limiting

Both `techdocs.broadcom.com` and `developer.broadcom.com` **rate-limit and return HTTP 429** under
sequential fetching. This was hit repeatedly during research; at least one page
(`.../setup-for-development-with-openapi.html`) was lost to a 429 and never retried.

**Back off. Do not conclude the page is missing.** Practically:

- Pause a few seconds between fetches; do not fire a burst of parallel fetches at either host.
- On 429, wait and retry the **same** URL at least once before trying anything else.
- Distinguish the three outcomes explicitly in your notes: **429** (retry), **404** (wrong slug —
  navigate from the landing page), **200 + SPA shell** (wrong URL on developer.broadcom.com).
- Budget accordingly: if a question needs many pages, prefer the spec corpus, which requires zero
  fetches.

### 403 from the fetch layer

Some techdocs pages returned **HTTP 403** to the research fetch proxy on repeated attempts (e.g. the
9.0 "Deploy the VCF Operations fleet management Appliance" page). Like 429, this is a transport
outcome, not a statement about content. Report it as "could not retrieve", never as "does not exist".
