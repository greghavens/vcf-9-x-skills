# NSX Security / DFW — VCF 9.0 → 9.1 change table

Scope: **distributed firewall, security policies, rules, groups, and the auth surface that fronts
them.** General NSX networking deltas (Transit Gateway, VPN, IPAM, EDP, DPDK, edge platform) are out of
scope for this file.

Source classes, same convention as the version files:

| Tag | Meaning |
|---|---|
| **[DOC]** | Version-pinned Broadcom prose (release notes, product support notes, admin guide, developer portal). |
| **[SPEC-9.1]** | Confirmed in the machine-extracted 9.1 spec inventory (`9.1.0.0` tag of `github.com/vmware/vcf-api-specs`). |
| **[ASYMMETRIC]** | The 9.1 side is spec-confirmed; the 9.0 side is prose-only, because **no NSX spec is published at the `9.0.0.0` tag**. |

> **The structural asymmetry that governs this whole table.** The public spec corpus has **no NSX
> specification at `9.0.0.0`** — `nsx-policy`, `nsx-manager` and `nsx-global-policy` are all absent at
> that tag and present only at `9.1.0.0` (3,729 / 1,453 / 1,009 operations). Therefore a row saying
> "not observed in 9.0" almost never means "proven absent in 9.0." It means the 9.0 prose docs did not
> show it. Only the appliance's own OpenAPI document can settle a 9.0 question — see `lookup.md`.

---

## 1. Headline changes affecting security and DFW

| Area | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| **Distributed Load Balancer / DFW coupling** | Distributed LB coupled to the DFW | *"Distributed Load Balancer is now independently managed and decoupled from the Distributed Firewall (DFW)."* | **[DOC — VCF 9.1 What's New: NSX]** |
| **Port mirroring** | Manager-plane ("Logical MP") API | MP API **removed**: *"Logical MP API for port mirroring is no longer supported."* Replaced by a new **Port Mirroring Policy API** supporting *"Local SPAN as well RSPAN"* with centralized configuration | **[DOC — VCF 9.1 product support notes + What's New]**, **[SPEC-9.1]** for the replacement paths |
| **Removed operations (all three NSX APIs)** | — | **17 NSX Manager API + 9 NSX Policy API + 1 NSX Autonomous Edge API operations removed** | **[DOC — VCF 9.1 product support notes]** |
| **NSX version / build** | 9.0.0.0 / 24733065 | 9.1.0.0 / 25318225 | **[DOC — BOM pages]** |
| **Machine-readable spec availability** | **none published** at the `9.0.0.0` corpus tag | `nsx-policy` (3,729 ops), `nsx-manager` (1,453 ops), `nsx-global-policy` (1,009 ops) | **[ASYMMETRIC]** |

---

## 2. Removed operations — counts published, paths **not** published

The VCF 9.1 product support notes state the counts and the affected **themes**, but **Broadcom does not
publish the individual paths or operation IDs.** Stated plainly so no downstream consumer guesses:

**The paths of the removed operations are not published.** They are not "unknown to this file" —
they are absent from the vendor's own release documentation.

| API surface | Count removed in 9.1 | Themes named by Broadcom |
|---|---|---|
| **NSX Manager API** (`/api/v1`) | **17** | System Health Agent metrics/monitoring endpoints; port mirroring (SPAN) session management endpoints; node user enumeration |
| **NSX Policy API** (`/policy/api/v1`) | **9** | VPC Subnet Bridge Profiles lifecycle operations; **PMaaS firewall exclude-list management**; Infrastructure Policy Labels operations |
| **NSX Autonomous Edge API** | **1** | Edge node user enumeration |

**[DOC — VCF 9.1 product support notes]**

Notes for a DFW-focused agent:

- Only one of the three Policy-API removal themes touches security: **PMaaS firewall exclude-list
  management.** The *general* DFW exclude list is unaffected — `/policy/api/v1/infra/settings/firewall/
  security/exclude-list` (GET·PATCH·PUT) is present in the 9.1 spec, along with
  `/exclude-list/members-count`, `?action=filter`, and `?system_owned=true`. **[SPEC-9.1]**
- The removals do **not** touch security policies, rules, groups or drafts. The full DFW CRUD tree is
  present in the 9.1 spec (see `9.1/dfw.md`).
- **Do not attempt to reconstruct the removed paths by diffing a 9.0 spec against the 9.1 spec** — there
  is no 9.0 spec to diff against. A 9.0-vs-9.1 diff is not available for NSX in this corpus.
- **How to detect a removal against a live 9.0 appliance:** fetch that appliance's own
  `/api/v1/spec/openapi/nsx_policy_api.json` and `/api/v1/spec/openapi/nsx_api.json` and diff them
  against the published 9.1 specs. This is the only route to the actual list, and it requires access to
  a 9.0 appliance.
- Attempts to retrieve the developer portal's "Removed Methods" / "Removed Types" pages for 9.1.0
  returned the SPA navigation shell only — see the trap in `lookup.md`.

---

## 3. Port mirroring — MP API out, Policy API in

The Manager-plane port-mirroring API is **removed** in 9.1. The replacement is a Policy API with
centralized configuration and **Local SPAN and RSPAN** support. **[DOC]**

Policy-API port-mirroring operations present in the 9.1 spec **[SPEC-9.1]**:

| Verb | Path (append to `/policy/api/v1`) | operationId |
|---|---|---|
| GET | `/infra/port-mirroring-profiles` | `ListPortMirroringProfiles` |
| GET·PATCH·PUT·DELETE | `/infra/port-mirroring-profiles/{port-mirroring-profile-id}` | `ReadPortMirroringProfile`, `PatchPortMirroringProfile`, `CreateOrReplacePortMirroringProfile`, `DeletePortMirroringProfile` |
| GET | `/infra/domains/{domain-id}/groups/{group-id}/port-mirroring-instances` | `ListPortMirroringInstances` |
| GET·PATCH·PUT·DELETE | `/infra/domains/{domain-id}/groups/{group-id}/port-mirroring-instances/{port-mirroring-instance-id}` | `ReadPortMirroringInstance`, `PatchPortMirroringInstance`, `CreateOrReplacePortMirroringInstance`, `DeletePortMirroringInstance` |

Note the shape: a mirroring **profile** under `/infra`, bound to a mirroring **instance** scoped to a
**group under a domain** — the same domain/group addressing the DFW uses. Related realization checks
live at `.../mirror-stack-status` on the monitoring-profile binding maps.

The **9.0** equivalents are prose-only and the MP-API paths that were removed are not published, so this
section documents the 9.1 target state, not a path-for-path migration map.

---

## 4. Security / DFW API surface, item by item

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Policy API base path | `/policy/api/v1` | `/policy/api/v1` — unchanged, confirmed as the spec `basePath` | **[ASYMMETRIC]** |
| Policy-only statement | *"The Manager mode and Manager API provided by NSX 4.x and earlier are no longer supported."* | Same sentence repeated verbatim in the 9.1 admin guide | **[DOC]** |
| Security policy CRUD | GET·PATCH·PUT·DELETE `/infra/domains/{domain-id}/security-policies/{id}` | same, **spec-confirmed** (`ReadSecurityPolicyForDomain`, `PatchSecurityPolicyForDomain`, `UpdateSecurityPolicyForDomain`, `DeleteSecurityPolicyForDomain`) | **[ASYMMETRIC]** |
| Rule CRUD | GET·PATCH·PUT·DELETE `.../security-policies/{id}/rules/{rule-id}` | same, **spec-confirmed** | **[ASYMMETRIC]** |
| `?action=revise` (policy + rule) | present | present, **spec-confirmed** (`ReviseSecurityPolicies`, `ReviseSecurityRule`) with `operation` ∈ {`insert_top`, `insert_bottom`, `insert_after`, `insert_before`} and `anchor_path`, body required | **[ASYMMETRIC]** — the query parameters are 9.1-spec-confirmed only |
| Rule statistics | `.../rules/{rule-id}/statistics` | same, plus **policy-level** `.../security-policies/{id}/statistics` (`GetSecurityPolicyStatistics`) | 9.0 **[DOC]**; policy-level statistics **[SPEC-9.1]**, not observed on the 9.0 DFW page |
| Drafts | GET·PUT·PATCH·DELETE `/infra/drafts/{draft-id}`, POST `?action=publish` | same, plus `/infra/drafts` (list), `/complete`, `/aggregated`, `/aggregated_with_pagination` | 9.0 **[DOC]**; the extras **[SPEC-9.1]**, not observed for 9.0 |
| Group read | `/infra/domains/{domain-id}/groups/{group-id}` + global and project variants | same, **spec-confirmed** | **[ASYMMETRIC]** |
| Group list / write verbs | **not observed** on a 9.0-pinned page | `ListGroupForDomain`, `PatchGroupForDomain`, `UpdateGroupForDomain`, `DeleteGroup` | **[SPEC-9.1]** — 9.0 side unverified, not absent |
| Group incremental expression edits (`POST .../{type}-expressions/{expression-id}`) | **not observed** in 9.0 | `AddorRemoveGroupIPAddresses`, `AddorRemoveGroupMACAddresses`, `AddorRemoveGroupPathMembers`, `AddorRemoveGroupExternalIDMembers` | **[SPEC-9.1]** + **[DOC — 9.1 portal inventory_groups page]** |
| Flat filtered firewall queries | **not observed** in 9.0 | `GET /infra/firewall/policies` (`GetFilteredPolicies`), `GET /infra/firewall/rules` (`GetFilteredRules`), plus `global-infra` and project variants | **[SPEC-9.1]** + **[DOC — 9.1 portal security_firewall page]** |
| DFW host configuration report | **not observed** on the 9.0 DFW page | `POST /infra/settings/security/host-configuration-report` (`GenerateHostConfigReportInCsv`) — CSV | **[SPEC-9.1]** + **[DOC]** |
| DFW dependent services check | not observed | `GET /infra/settings/firewall/security/dependent-services` (`GetDistributedFirewallDependentServices`) | **[SPEC-9.1]** |
| VPC-scoped security policies | VPCs exist in 9.0; VPC-scoped **security-policy** paths not observed | `/orgs/{org}/projects/{proj}/vpcs/{vpc-id}/security-policies[/{id}[/rules[/{rule-id}]]]`, `?action=revise`, `/statistics`, `/realization-failures` | **[SPEC-9.1]** |
| `communication-maps` legacy tree | listed as **deprecated** on the 9.0 DFW page | still present; **all 12 operations flagged `deprecated: true` in the spec** | 9.0 **[DOC]**; 9.1 **[SPEC-9.1]** |
| `firewall-identity-stores` (IDFW identity source) | not characterized in 9.0 research | present but **largely `deprecated: true`** in the 9.1 spec (CRUD, event-log-servers, ldap-servers); the non-deprecated survivors are the query operations (`SearchFirewallIdentityGroups`, `ListFirewallIdentityStoreGroupMemberGroups`, `FetchFirewallIdentityStoreOrgUnitsForIdentityStore`, `GetFirewallIdentityStoreSyncStats`) | **[SPEC-9.1]** — a 9.1-observed deprecation not called out in the release notes |
| Search API | referenced in prose, **concrete path unresolvable** | `GET /policy/api/v1/search/query` (`QuerySearch`), `GET /policy/api/v1/search/dsl` (`DslSearch`), `POST /search/reconcile`, `GET /search/reconcile/status` | **[SPEC-9.1]** — resolves a gap the prose research could not close in either version |
| Federation write scope | `global-infra` paths documented | on the **local** manager's Policy API, `global-infra` DFW paths are **GET-only**; writes live on the **Global Manager** appliance spec (`basePath: /global-manager/api/v1`, `GlobalInfraPatchSecurityPolicyForDomain`, `GlobalInfraUpdateGroupForDomain`, …) | **[SPEC-9.1]** — this read/write split was not visible in the 9.0 prose |

---

## 5. Auth surface — no functional delta found

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Session create / destroy | `POST /api/session/create`, `POST /api/session/destroy` | identical; **spec-confirmed** as absolute paths outside the `/api/v1` basePath (`CreateAuthenticatedSession`, `DestroyAuthenticatedSession`) | **[ASYMMETRIC]** |
| Form fields | `j_username`, `j_password` | identical; the 9.1 spec's own example request shows `j_username=admin&j_password=my-password` | **[ASYMMETRIC]** |
| Response headers | `Set-Cookie` (`JSESSIONID`) + `X-XSRF-TOKEN`, both required on subsequent calls | identical; the 9.1 spec's example response shows `set-cookie: JSESSIONID=…; Path=/; Secure; HttpOnly; SameSite=Lax` and `x-xsrf-token: …` | **[ASYMMETRIC]** |
| Session timeout default | 1800 s | 1800 s — `ApiServiceConfig.session_timeout` has `default: 1800` in the spec | **[ASYMMETRIC]** |
| Expiry status code | **not stated** on the 9.0-pinned page | *"NSX Manager responds with a 403 Forbidden HTTP response."* | **[DOC — 9.1 page only]**. Treat 403 as re-auth in both versions; only 9.1 states it. |
| Cookie node affinity | *"session cookies are manager-node-specific and cannot be reused across cluster nodes"* | not restated on a 9.1-pinned page; assumed unchanged | **[DOC — 9.0 page only]** |
| Cookie-auth kill switch | not characterized | `ApiServiceConfig.cookie_based_authentication_enabled`, `default: true`; *"When cookie-based authentication is disabled, new sessions cannot be created via /api/session/create."* | **[SPEC-9.1]** |
| HTTP Basic | supported | supported; the 9.1 policy spec declares exactly one security scheme: `BasicAuth` (`type: basic`) | **[ASYMMETRIC]** |
| X.509 client cert (principal identity) | supported | supported | **[DOC]** |
| JWT / bearer against NSX Manager | not documented, **and not confirmable either way** (no NSX spec at the `9.0.0.0` tag) | **a token route exists** — `POST·GET·DELETE /api/v1/trust-management/token-principal-identities` (`RegisterTokenBasedPrincipalIdentity`, `ListTokenBasedPrincipalIdentities`, `GetTokenBasedPrincipalIdentity`, `DeleteTokenBasedPrincipalIdentity`) | **[SPEC-9.1]**. The earlier "not documented in both" verdict was **wrong for 9.1** and is withdrawn. The *wire format* of the authenticated request is still undocumented — **[INFERRED]**. See `9.1/dfw.md` § A7. |
| OIDC endpoint config (the prerequisite for the above) | OIDC narrowed to **one** endpoint, must be VMware Identity Broker **[DOC-9.0]**; no spec | `POST /api/v1/trust-management/oidc-uris/action/configure-vidb-oidc-endpoint` (`ConfigureVidbAndAddOidcEndPoint`), plus `ListOidcEndPoints`, `GetOidcEndPoint`, `CheckOidcEndPointHealth`, `TestVidbConnection` | **[SPEC-9.1]**. Whether 9.1 still caps OIDC endpoints at one is **unverified** — the 9.1 support notes do not restate the 9.0 limit. |
| Non-interactive VCF-SSO API token | not available; per-product credentials are the documented route | **VCF SSO can issue a role-scoped non-interactive API token**, and NSX has a spec-confirmed binding surface for it (row above) — a 9.1 capability | **[DOC + SPEC-9.1]** |
| Rate limit (per client) | 100 req/s, 40 concurrent | 100 req/s, 40 concurrent **in prose**; the 9.1 **spec** says **250 req/s, 100 concurrent** for `/api/v1/cluster/api-service` | **[DOC — prose only for the 100/40 figures]** + **unresolved spec-vs-prose conflict — see the note below.** Not `[ASYMMETRIC]`. |
| **Global concurrency limit** | prose says **199** overall | spec `ApiServiceConfig.global_api_concurrency_limit`, **`default: 500`**, 503 on exceed | **Unresolved discrepancy** — see the note below. |
| Pagination default | 1000 | 1000 | **[DOC]** |
| Identity sources | local, vIDM, LDAP/AD/OpenLDAP, VCF Identity Broker; OIDC narrowed to **one** endpoint (VMware Identity Broker); vIDM **deprecated** | same list plus *"Starting in NSX 4.1.2, you can use vCenter server as an external identity provider"*; audit logging on by default and cannot be disabled | **[DOC]** |
| Principal identities | the **only** documented NSX-native service-account mechanism, but flagged *"planned for deprecation in an upcoming release"* → migrate to Federated Users via VCF SSO | deprecation notice **not restated** in the 9.1 support notes; status unverified. No longer the only route: the **token-based** principal identity (rows above) is spec-confirmed and not deprecation-flagged — prefer it for new automation | **[DOC — 9.0 only]** for the deprecation; **[SPEC-9.1]** for the alternative |
| `_revision` on `/policy` PUT | 9.0 guide: `/policy` URIs *"have slightly different behavior"* | 9.1 guide, verbatim: *"the _revision property must not be set when PUT is used to create a new resource. Once the resource is created, however, the _revision property must be provided with PUT operations."* | **[DOC]** — a documentation-precision delta, not a behavior delta |
| Partial patch enablement | `PATCH /policy/api/v1/system-config/nsx-partial-patch-config` `{"enable_partial_patch":"true"}` | identical | **[DOC]** |

### Note — the rate-limit figures are a spec-vs-prose conflict, not a delta

An earlier revision of this table graded "100 req/s / 40 concurrent" as **[SPEC]**, citing the 9.1
spec's `api-service` example. **That attribution was wrong.** Re-checked against
`specifications/nsx/openapi-2.0/nsx_api.yaml` at the `9.1.0.0` tag:

| Source | rate limit | client concurrency | global concurrency |
|---|---|---|---|
| 9.0 / 9.1 **prose** | 100 req/s | 40 | 199 |
| **[SPEC]** `ApiServiceConfig` defaults — `GET·PUT /api/v1/cluster/api-service` | **250** | **100** | **500** |
| **[SPEC]** `api-service` `x-vmw-nsx-example-response` | **250** | **100** | **500** |
| **[SPEC]** `HttpServiceProperties` defaults — `/api/v1/node/services/http`, **`x-deprecated: true`** | 100 | 40 | 100 |
| **[SPEC]** `/api/v1/node/services/http` example response | 100 | 40 | 199 |

The 100 / 40 / 199 figures **do** appear in the 9.1 spec — but on the **deprecated**
`HttpServiceProperties` model for `/api/v1/node/services/http`, a *different endpoint* from the
`ApiServiceConfig` model on `/api/v1/cluster/api-service` that both version files tell you to read.
The prose figures happen to match the deprecated model; that is not the same as the spec confirming
them for the API service.

**Resolution: none. Recorded, not resolved.** Do not treat either pair as a spec-confirmed fact about
the API service in either version. Read the live values with `GET /api/v1/cluster/api-service`
(**[SPEC — `GetApiServiceConfig`]**, 9.1) and honour what the appliance returns. If you must assume
before you can read, assume the **lower** (prose) figures — over-backing-off is safe.

**Bottom line on auth: no functional change was found between 9.0 and 9.1.** The same endpoints, form
fields, header names, cookie name and 1800 s default. What changed is documentation precision (403 on
expiry now stated) and the surrounding identity platform (VCF SSO API tokens, vCenter as IdP).

---

## 6. VCF-integration constraints affecting a security agent

| Item | VCF 9.0 | VCF 9.1 | Evidence |
|---|---|---|---|
| Standalone NSX install/upgrade | *"Starting with NSX 9.0, a standalone NSX installation or upgrade is not supported."* | not restated | **[DOC — 9.0 only]** |
| NSX per vCenter | *"VMware supports only one NSX instance for the same vCenter instance."* | not restated | **[DOC — 9.0 only]** |
| NSX Manager sharing | not stated | *"VCF Management Domain can now share NSX Managers with other VCF workload domains."* Does **not** contradict one-NSX-per-vCenter — it is one NSX Manager serving multiple workload domains | **[DOC — 9.1]** |
| Out-of-band NSX edits | no reconciliation statement | **SDDC Manager network sync** reconciles *"network configuration changes done directly in vCenter or NSX Manager"* | **[DOC — 9.1]** |
| Authoritative VCF-owned-object list | **does not exist** | **does not exist**; the 9.1 support notes contain no statement distinguishing VCF-managed from directly-managed NSX objects | **[DOC — negative result in both]** |
| Gateway Firewall default | *"Gateway Firewall automatically disabled by default for all greenfield deployments"* | not restated | **[DOC — 9.0]** |
| FIPS | *"Components including NSX operate in FIPS-enabled mode by default and cannot be deactivated"* | not restated | **[DOC — 9.0]** |
| NSXe (NSX embedded in vCenter) | **removed in 9.0** | (removed) | **[DOC — 9.0]** |
| NSX Migration Coordinator | **removed in 9.0** | (removed) | **[DOC — 9.0]** |
| NSX Load Balancer entitlement | general-purpose LB removed from VCF entitlement; Avi recommended; NSX LB retained only for VCF infrastructure and vSphere Supervisor | not restated | **[DOC — 9.0]** |
| Appliance OS | not stated | *"All NSX appliances have been upgraded to Ubuntu 24.04"* with chiseled containers | **[DOC — 9.1]** |
| ESXi accounts created by NSX | creates `mux_user`, `da-user`, `nsx-user`, `lldpVim-user` | **no longer creates** those accounts | **[DOC — 9.1]** |

> **Caution on the "not restated" rows.** The 9.0 constraints above were sourced from the **9.0**
> product support notes and were not re-verified in the 9.1 doc set. "Not restated" is not "revoked."
> Do not assert them for 9.1 without re-checking, and do not assume they lapsed.

---

## 7. Documentation-structure deltas (traps, not API changes)

| Item | VCF 9.0 | VCF 9.1 |
|---|---|---|
| Developer portal root | `https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/` (also `9.0.1`, `9.0.2`) | `.../9.1.0/` |
| Portal nav taxonomy | grouped by *Federation / Management Plane API / NSX Application Platform / Policy / System Administration* | regrouped by function: *Certificates, Enforcement Points, Federation, Inventory, Monitoring, Multi-Tenancy, Networking, Policy, Search, Security, System, Troubleshooting, User Management, VPC Networking* — **no "Management Plane API" top-level group** |
| DFW category page slug | `policy_security_east_west_security_distributed_firewall.html` | `security_firewall.html` |
| Groups category page slug | (under `policy_security…`) | `inventory_groups.html` |
| Product doc URL shape | `.../9-0/advanced-network-management/administration-guide/<topic>.html` | `.../9-1/advanced-network-management/<topic>.html` (**no `administration-guide/` segment**) |

The slug change is a real trap: **adding or removing the `policy_` prefix is not a reliable translation
between the doc sets.** `policy_networking_switching_segments.html` does not exist for 9.0.0, and the 9.1
DFW page is not `security_east_west_security_distributed_firewall.html`. Navigate the left-hand tree
rather than guessing a slug. See `lookup.md`.

The nav-taxonomy change is an **observation about documentation structure**, based on rendered navigation
menus — **not** proof that the Management Plane API surface was removed.
