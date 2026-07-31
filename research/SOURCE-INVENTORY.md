# Consolidated source inventory — VCF 9.0 / 9.1 agent-skills project

Every source below was fetched live on **2026-07-31**. Nothing in these dossiers
comes from model training memory; unverifiable items are marked UNVERIFIED in situ.

**301 unique source URLs** across 10 research dossiers, plus the
machine-readable OpenAPI corpus in `spec-inventory/` (git tags `9.0.0.0` and `9.1.0.0`
of https://github.com/vmware/vcf-api-specs, cloned 2026-07-31).


## From `foundation-auth-identity.md` — 18 source URLs

All accessed **2026-07-31**.

| ID | URL | Doc set / version | Covers |
|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | VCF 9.0 | Section index |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | Section index |
| S3 | .../9-0/administration-sdks-cli-and-tools.html | VCF 9.0 | SDK/API index |
| S4 | .../9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | SDK/API index |
| S5 | .../9-0/organization-management.html | VCF 9.0 | Org mgmt, IdP overview |
| S6 | .../9-1/organization-management.html | VCF 9.1 | Org mgmt, IdP overview |
| S7 | .../9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide.html | VCF 9.0 | Programming guide index |
| S8 | .../9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide.html | VCF 9.1 | Programming guide index |
| S9 | .../9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api.html | VCF 9.0 | VCF Ops API overview, HTTPS |
| S10 | .../9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api.html | VCF 9.0 | VCF Automation API index |
| S11 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/managing-api-tokens.html | VCF 9.1 | **API client + API token creation, TTL defaults** |
| S12 | .../9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html | VCF 9.0 | **VCF Ops token acquire, OpsToken header, 6 h** |
| S13 | .../9-1/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html | VCF 9.1 | **VCF Ops token acquire (identical to 9.0)** |
| S14 | .../9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token.html | VCF 9.0 | VCF Automation VM Apps token lifetimes |
| S15 | .../9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token/get-your-access-token-for-vra-8-x.html | VCF 9.0 | **VM Apps `/tm/oauth/tenant/{t}/token`** |
| S16 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on.html | VCF 9.1 | **9.1 SSO section structure, federated components** |
| S17 | .../9-0/fleet-management.html | VCF 9.0 | Fleet Management child list |
| S18 | .../9-0/fleet-management/what-is.html | VCF 9.0 | **9.0 SSO overview, identity broker, exclusions** |
| S19 | .../9-0/fleet-management/what-is/deployment-models-for-sso.html | VCF 9.0 | Embedded vs appliance broker modes |
| S20 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/vcf-built-in-roles.html | VCF 9.1 | **VCF built-in roles + component mappings** |
| S21 | .../9-0/fleet-management/certificate-management-9-0.html | VCF 9.0 | **Cert mgmt: CA types, rotation, coverage** |
| S22 | .../9-1/fleet-management/certificate-management-9-0.html | VCF 9.1 | **Cert mgmt 9.1 incl. bulk ops, tiers** |
| S23 | .../9-0/fleet-management/what-is/protocols-suported-for--sso.html | VCF 9.0 | **IdPs + SAML/OIDC/SCIM/JIT** |
| S24 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is.html | VCF 9.1 | 9.1 SSO overview, deployment modes |
| S25 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/migrating-vmware-identity-manager-to-vcf-identity-broker.html | VCF 9.1 | **vIDM→broker migration, OAuth client caveat** |
| S26 | .../9-1/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html | VCF 9.1 | **Outbound 443 URL allow-list** |
| S27 | .../9-1/planning-and-preparation/vcf-components-fqdns-and-ip-addresses.html | VCF 9.1 | **FQDN/DNS requirements, component list** |
| S28 | .../9-0/planning-and-preparation.html | VCF 9.0 | Points to ports.broadcom.com |
| S29 | .../9-1/planning-and-preparation.html | VCF 9.1 | Points to ports.broadcom.com |
| S30 | .../9-0/advanced-network-management/administration-guide/authentication-and-authorization.html | VCF 9.0 (NSX) | NSX auth page index, broker integration |
| S31 | .../9-0/advanced-network-management/administration-guide/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html | VCF 9.0 (NSX) | **NSX session create/destroy, JSESSIONID + x-xsrf-token, 1800 s** |
| S32 | .../9-0/advanced-network-management/administration-guide/authentication-and-authorization/role-based-access-control.html | VCF 9.0 (NSX) | **15 NSX built-in roles** |
| S33 | .../9-0/vsphere-supervisor-installation-and-configuration/vsphere-supervisor-concepts/vsphere-iaas-control-plane-concepts/understanding-authorization-in-supervisor.html | VCF 9.0 | Supervisor auth/authz, `vcf context create` |
| S34 | .../9-1/vsphere-supervisor-installation-and-configuration/vsphere-supervisor-concepts/vsphere-iaas-control-plane-concepts/understanding-authorization-in-supervisor.html | VCF 9.1 | **Supervisor auth incl. Pinniped, `--api-token`, `--ca-certificate`** |
| S35 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/ | vSphere Automation API 9.1 | Session id header, `POST /api/cis/session` |
| S36 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/api-security-schema/ | vSphere Automation API 9.1 | **basic / `vmware-api-session-id` / bearer** |
| S37 | https://developer.broadcom.com/xapis/vsphere-automation-api/9.0/api-security-schema/ | vSphere Automation API 9.0 | **Same three schemes, 9.0** |
| S38 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/cis-session/ | vSphere Automation API 9.1 | `POST /session`, `DELETE /session`, SAML exchange |
| S39 | https://developer.broadcom.com/xapis/vmware-identity-broker/latest/ | VMware Identity Broker 9.1 | Broker as "centralized authentication source for the VCF components" |
| S40 | https://developer.broadcom.com/xapis/vmware-identity-broker/latest/acs/t/tenant/token/post/ | VMware Identity Broker 9.1 | **`POST /acs/t/{tenant}/token`, grant types, `api_token`, `access_token`** |
| S41 | https://developer.broadcom.com/xapis/sddc-manager-api/latest/tokens/ | SDDC Manager API 9.1 | Three token operations by name |
| S42 | https://developer.broadcom.com/xapis/sddc-manager-api/9.0/tokens/ | SDDC Manager API 9.0 | **`/v1/tokens` create/refresh/revoke, payloads, `accessToken`** |
| S43 | https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/tokens/ | VMware Cloud Foundation API 5.2.4 | Corroborates paths + `Authorization: Bearer`. **Pre-9.x — corroboration only** |
| S44 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/ | VCF Operations API 9.1 | **`OpsToken` and `Bearer` (VCF SSO) schemes, 401 behavior** |
| S45 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/auth/ | VCF Operations API 9.1 | **Full `/auth/*` surface incl. token acquire/release/exchange, roles, privileges** |
| S46 | https://developer.broadcom.com/xapis/all-apps-org-access-control/latest/ (resolves to Provider Management API) | VCF Automation 9.1 | **JWT via `Authorization`; `x-vcloud-authorization` deprecated; tenant-context headers** |
| S47 | https://knowledge.broadcom.com/external/article/409715/how-to-authorize-vcf-operations-fleet-ma.html | Broadcom KB, VCF 9.0 | **Fleet Management API = HTTP Basic, base64 `admin@local:<pwd>`** |
| S48 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | VCF 9.1 | **9.1 API/SDK/PowerCLI deltas, VGFA, token params** |
| S49 | .../9-0/provider-management.html | VCF 9.0 | Provider portal, IdP integration levels |
| S50 | .../9-1/provider-management/managing-system-administrators-and-roles/managing-rights-and-roles.html | VCF 9.1 | **Rights/roles/bundles, provider vs global vs org roles** |
| S51 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens.html | VCF 9.1 | API client purpose, emergency access client |
| S52 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/view-and-manage-token-lifecycle-and-security.html | VCF 9.1 | **IAM maxima: 180 d / 480 min / 90 d, JIT inactivity** |
| S53 | .../9-0/fleet-management/what-is/managing-vmware-cloud-foundation-operations-sso.html | VCF 9.0 | **Negative evidence: no API client/token/role pages in 9.0** |
| S54 | .../9-0/fleet-management/what-is/setting-up-sso.html | VCF 9.0 | 7-step SSO configuration order |
| S55 | .../9-0/security-and-compliance.html | VCF 9.0 | Section contents (no cert/TLS/identity content) |
| S56 | .../9-1/design/design-library/single-sign-on-models.html | VCF 9.1 | **Three SSO topology models; split-SSO unsupported** |
| S57 | .../9-1/fleet-management/certificate-management-9-0/managing-certificates-in-vmware-vsphere-foundation/certificates/importing-ca-certificates.html | VCF 9.1 | **Trusted Certificates import, PEM-only, affected domains** |
| S58 | https://blogs.vmware.com/cloud-foundation/2025/11/19/unified-authentication-in-vmware-cloud-foundation-sdk-9-0-seamless-authentication-across-vsphere-and-vsan-apis/ | Broadcom/VMware blog, 2025-11-19, VCF SDK 9.0 | **Session reuse `/vim25` ↔ `/api` via `vmware-api-session-id`** |
| S59 | .../9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms.html | VCF 9.1 | **Basic vs token auth, JWT→SAML→session workflow, federation IdPs** |
| S60 | .../9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis.html | VCF 9.0 | Auth mechanisms pointer, SSO/external IdP statement |
| S61 | .../9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis.html | VCF 9.1 | Same, 9.1 |
| S62 | .../9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/categories-of-vcf-automation-hard-tenancy-apis.html | VCF 9.0 | **10 All Apps API categories (Access Control, Aggregator, …)** |
| S63 | .../9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-a-tkg-service-cluster-as-a-vcenter-single-sign-on-user-with-kubectl.html | VCF 9.0 | VKS connect prerequisites, kubeconfig |
| S64 | https://ports.broadcom.com/ | Broadcom tool (undated) | Ports portal description; **no static data extractable** |
| S65 | .../9-0/fleet-management/what-is/sso-architecture.html | VCF 9.0 | Stub — defers to design library |
| S66 | .../9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/what-is/sso-architecture.html | VCF 9.1 | Stub — defers to design library |
| S67 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter-authentication/vcenter-authentication-token/ | vSphere Automation API 9.1 | `POST /vcenter/authentication/token`, added 7.0.2.0 |
| S68 | .../9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/using-the-vsan-management-sdks.html | VCF 9.0 | **vSAN depends on vSphere Web Services API for login** |

### Retrieval failures (recorded for completeness)
| URL | Result |
|---|---|
| .../9-0/planning-and-preparation/public-urls-required-for-vmware-cloud-foundation.html | 404 |
| .../9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/generating-an-access-token.html | 404 (3 attempts) |
| .../9-1/advanced-network-management/authentication-and-authorization.html | HTTP 429 (repeated) |
| .../9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms.html | HTTP 429 (repeated) |
| .../9-1/.../managing-api-clients-and-tokens/... considerations-and-prerequisites-for-vcf-sso.html | 404 |
| .../9-0/fleet-management/what-is/points-to-consider-and-prerequisites-while-configuring-vcf-sso.html | 404 |
| .../9-0/design/design-library/single-sign-on-models/-fleet.html | 404 |
| .../9-0/deployment/.../installing-vcf-identity-broker.html | HTTP 403 |
| developer.broadcom.com/xapis/vmware-cloud-foundation-fleet-management-api/latest/ | 404 (API does not exist under that slug) |
| developer.broadcom.com/xapis/sddc-manager-api/latest/tokens/post-v1-tokens/ | Page rendered without operation detail |
| developer.broadcom.com/xapis/vcf-operations-api/latest/auth/token/acquire/post/ | Page rendered without operation detail |
| .../9-0/.../getting-your-authentication-token/get-your-refresh-token-for-the-vm-apps-tenant.html | 404 |

## From `nsx.md` — 56 source URLs

All accessed **2026-07-31**.

| ID | URL | Doc set version | Date accessed | Covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | VCF 9.0 | 2026-07-31 | 9.0 doc landing; NSX under "Advanced Network Management" |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | 2026-07-31 | 9.1 doc landing; NSX under "Advanced Network Management" |
| S3 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.0 | 2026-07-31 | 9.0 BOM: NSX 9.0.0.0 / 24733065 |
| S4 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.1 | 2026-07-31 | 9.1 BOM: NSX 9.1.0.0 / 25318225 |
| S5 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-nsx.html | VCF 9.1 | 2026-07-31 | What's New — NSX (9.1), full feature list |
| S6 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-nsx.html | VCF 9.0 | 2026-07-31 | What's New — NSX (9.0), full feature list |
| S7 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vcf-91-product-support-notes.html | VCF 9.1 | 2026-07-31 | 9.1 deprecations/removals; removed-operation counts |
| S8 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-nsx.html | VCF 9.0 | 2026-07-31 | 9.0 NSX deprecations/removals/constraints |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/advanced-network-management/administration-guide/nsx-manager.html | VCF 9.0 | 2026-07-31 | Policy-mode-only statement; `/policy/api`; partial patch |
| S10 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/advanced-network-management/nsx-manager.html | VCF 9.1 | 2026-07-31 | Same Policy-mode-only statement for 9.1 |
| S11 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/advanced-network-management/administration-guide/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html | VCF 9.0 | 2026-07-31 | 9.0 session-cookie auth procedure + curl |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/advanced-network-management/authentication-and-authorization/nsx-api-authentication-using-a-session-cookie.html | VCF 9.1 | 2026-07-31 | 9.1 session-cookie auth procedure + curl; 403 on expiry |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/advanced-network-management/administration-guide/authentication-and-authorization.html | VCF 9.0 | 2026-07-31 | 9.0 identity sources |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/advanced-network-management/authentication-and-authorization.html | VCF 9.1 | 2026-07-31 | 9.1 identity sources; audit logging |
| S15 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/ | NSX 9.0.0 | 2026-07-31 | 9.0.0 API reference root; nav taxonomy; version list |
| S16 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/ | NSX 9.1.0 | 2026-07-31 | 9.1.0 API reference root; nav taxonomy |
| S17 | https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.0.0/html/index.html | NSX 9.0.0.0 | 2026-07-31 | NSX API Guide 9.0: basic/session/X.509/VMC auth, OpenAPI endpoints, rate limits, pagination |
| S18 | https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/index.html | NSX 9.1.0.0 | 2026-07-31 | NSX API Guide 9.1: same sections, plus `_revision` verbatim |
| S19 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/api_usage_user_authentication.html | NSX 9.0.0 | 2026-07-31 | `/api/session/create` and `/api/session/destroy` descriptions verbatim |
| S20 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/advanced-network-management/administration-guide.html | VCF 9.0 | 2026-07-31 | 9.0 NSX admin guide TOC + subsection URLs |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/advanced-network-management.html | VCF 9.1 | 2026-07-31 | 9.1 NSX admin guide TOC + subsection URLs |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-1-release-notes/nsx-9-0-1-0000.html | VCF 9.0.1 | 2026-07-31 | Existence of per-patch NSX release notes (surfaced via search; not opened) |
| S23 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_GetNatRule.html | NSX 9.0.0 | 2026-07-31 | Manager-API NAT rule path; "deprecated as of version 9.0" |
| S24 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ListSegments.html | NSX 9.0.0 | 2026-07-31 | T1 segment list paths + query params |
| S25 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadTier1.html | NSX 9.0.0 | 2026-07-31 | Tier-1 read paths |
| S26 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadGroupForDomain.html | NSX 9.0.0 | 2026-07-31 | Group read paths |
| S27 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_CreateOrReplaceInfraSegment.html | NSX 9.0.0 | 2026-07-31 | Infra segment PUT paths |
| S28 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadTier0.html | NSX 9.0.0 | 2026-07-31 | Tier-0 read paths |
| S29 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/policy_security_east_west_security_distributed_firewall.html | NSX 9.0.0 | 2026-07-31 | Full 9.0 DFW method table: security policies, rules, drafts, IDFW, exclude list, communication-maps (deprecated) |
| S30 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadSecurityPolicyForDomain.html | NSX 9.0.0 | 2026-07-31 | Security policy read paths |
| S31 | (same as S26) | NSX 9.0.0 | 2026-07-31 | Group paths |
| S32 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/policy_networking.html | NSX 9.0.0 | 2026-07-31 | 9.0 IP pool / allocation / subnet paths |
| S33 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadLBService.html | NSX 9.0.0 | 2026-07-31 | LB service read path |
| S34 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadTransportZoneForEnforcementPoint.html | NSX 9.0.0 | 2026-07-31 | Transport zone read paths |
| S35 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.0.0/method_ReadEdgeClusterForEnforcementPoint.html | NSX 9.0.0 | 2026-07-31 | Edge cluster read paths |
| S36 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new.html | VCF 9.0 | 2026-07-31 | FIPS 140-2/140-3 statement; link to NSX What's New |
| S37 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_switching_segments.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 segment method table (46 entries) |
| S38 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_ReadTier1.html | NSX 9.1.0 | 2026-07-31 | Tier-1 read paths (9.1) |
| S39 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_routing_tier-1s.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 Tier-1 method table incl. `gateways/action/reallocate` |
| S40 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_CreateOrReplaceInfraSegment.html | NSX 9.1.0 | 2026-07-31 | Infra segment PUT paths (9.1) |
| S41 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_ListSegments.html | NSX 9.1.0 | 2026-07-31 | T1 segment list; note that flexible segments require the search API |
| S42 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_routing_tier-0s.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 Tier-0 method table |
| S43 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_ReadTier0.html | NSX 9.1.0 | 2026-07-31 | Tier-0 read paths (9.1) |
| S44 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/method_ReadSecurityPolicyForDomain.html | NSX 9.1.0 | 2026-07-31 | Security policy read paths (9.1) |
| S45 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/security_firewall.html | NSX 9.1.0 | 2026-07-31 | 9.1 firewall query endpoints + host-configuration-report |
| S46 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/inventory_groups.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 group method table incl. expression sub-resources |
| S47 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_ip_management_ip_pools.html | NSX 9.1.0 | 2026-07-31 | Full 9.1 IP pool / allocation / subnet / manager-ip-pool table |
| S48 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_nat_nat_rules_tier-0s.html | NSX 9.1.0 | 2026-07-31 | Tier-0 NAT method table |
| S49 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_nat_nat_rules_tier-1s.html | NSX 9.1.0 | 2026-07-31 | Tier-1 NAT method table incl. project-scoped |
| S50 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_load_balancing_lb_services.html | NSX 9.1.0 | 2026-07-31 | LB service method table |
| S51 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_vpn_ipsec_services.html | NSX 9.1.0 | 2026-07-31 | IPSec VPN service tables; locale-service paths deprecated |
| S52 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/networking_switching_transport_zones.html | NSX 9.1.0 | 2026-07-31 | Transport zone method table |
| S53 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/system_fabric_edge_clusters.html | NSX 9.1.0 | 2026-07-31 | Edge cluster + HA profile method tables |
| S54 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/system_fabric_host_transport_nodes.html · .../9.1.0/method_ListHostTransportNodesForEnforcementPoint.html · .../9.0.0/method_ListHostTransportNodesForEnforcementPoint.html | NSX 9.1.0 / 9.0.0 | 2026-07-31 | Negative result — no content returned (host transport nodes unresolved) |
| S55 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/deprecated_methods.html · .../removed_methods.html | NSX 9.1.0 | 2026-07-31 | Negative result — SPA shell only; removed/deprecated lists not retrievable |
| S56 | https://dp-downloads.broadcom.com/api-content/apis/API_NTDCRA_001/9.1.0/html/api_usage_user_authentication.html | NSX 9.1.0 | 2026-07-31 | Negative result — HTTP 404 (auth content is inside index.html) |
| S57 | https://developer.broadcom.com/xapis/nsx-t-data-center-rest-api/9.1.0/api_single_page.html | NSX 9.1.0 | 2026-07-31 | Negative result — fetch/server error |
| S58 | /root/.ccr/README.md + agent-proxy status endpoint (local) | n/a | 2026-07-31 | Egress policy: direct `curl` CONNECT to techdocs.broadcom.com returned 403; WebFetch used throughout |

## From `openclaw-marketplace.md` — 22 source URLs

| ID | URL | Date accessed | Covers |
|---|---|---|---|
| S1 | https://github.com/openclaw/openclaw | 2026-07-31 | What OpenClaw is, README description, maintainer, MIT license, star count |
| S2 | https://raw.githubusercontent.com/openclaw/openclaw/main/docs/tools/skills.md | 2026-07-31 | Canonical skills doc: AgentSkills conformance, load order/paths, frontmatter keys, gating, install specs, symlink containment, private zip archive installs, watcher config |
| S3 | https://docs.openclaw.ai/clawhub | 2026-07-31 | ClawHub overview, hosted families, CLI commands, upload gate, telemetry, slug regex, earlier text-allowlist description |
| S4 | https://clawhub.ai/ | 2026-07-31 | Registry is live; homepage counts, categories, inline publish commands, signed manifests / moderated releases / GitHub import claims |
| S5 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/skill-format.md | 2026-07-31 | **Authoritative skill format**: required/optional files, frontmatter reference, metadata.openclaw table, install specs, file rules, 50MB limit, symlink exclusion, slug rules, MIT-0, no paid skills, GitHub importer restrictions |
| S6 | https://raw.githubusercontent.com/openclaw/clawhub/main/README.md | 2026-07-31 | ClawHub definition, capabilities, CLI flows, metadata aliases (clawdbot/clawdis), nix/config/cliHelp metadata, delete permissions, architecture, telemetry |
| S7 | https://github.com/openclaw/clawhub — earlier rendered fetch of openclaw/openclaw docs/tools/skills.md | 2026-07-31 | Secondary rendering; source of the unverified `hidden`, `tool-name`, `alwaysInclude`, `platforms` keys and installer preference order |
| S8 | https://raw.githubusercontent.com/openclaw/openclaw/main/docs/plugins/manifest.md | 2026-07-31 | `openclaw.plugin.json` requirement and schema; foreign bundle manifests (.claude-plugin/.codex-plugin/.cursor-plugin) |
| S9 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/publishing.md | 2026-07-31 | Publish flow, owner model, validation-then-scan sequence, GitHub Action workflow, plugin scope rules, icon field, trusted publishing, namespace claims |
| S10 | https://docs.openclaw.ai/tools/creating-skills | 2026-07-31 | Skill authoring guide, required fields, gating, `{baseDir}`, publish via `clawhub skill publish` |
| S11 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/README.md and .../docs/clawhub.md | 2026-07-31 | Docs index and mirroring to docs.openclaw.ai; upload gate wording |
| S12 | https://en.wikipedia.org/wiki/OpenClaw (+ CNBC, Forbes coverage surfaced in same search) | 2026-07-31 | Rename history Clawdbot → Moltbot → OpenClaw |
| S13 | https://github.com/VoltAgent/awesome-openclaw-skills | 2026-07-31 | Third-party claim of 5,400+ skills in the official registry |
| S14 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/cli.md | 2026-07-31 | **Canonical CLI reference**: skill publish flags, sync, scan/scan download, pin/unpin, install (zip download + extract), package publish, plugin compat fields |
| S15 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/quickstart.md | 2026-07-31 | Install/login/publish quickstart, `--slug`/`--name`/`--changelog`, auto-versioning, GitHub workflow |
| S16 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/security-audits.md | 2026-07-31 | Audit statuses, risk levels, findings severities, SkillSpector + VirusTotal + ClawScan, OWASP Agentic Skills Top 10 |
| S17 | https://docs.openclaw.ai/clawhub/moderation | 2026-07-31 | Reports, moderation holds, hidden/quarantined listings, bans, appeals |
| S18 | https://raw.githubusercontent.com/openclaw/clawhub/main/docs/acceptable-usage.md | 2026-07-31 | Prohibited categories, bulk low-effort publishing, metric gaming, enforcement actions |
| S19 | https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/ | 2026-07-31 | External security critique of the skills marketplace as supply-chain risk (title/abstract from search) |
| S20 | https://www.certik.com/blog/skill-scanning-is-not-a-security-boundary | 2026-07-31 | External critique that scanning is not a security boundary (title from search) |
| S21 | https://github.com/openclaw/agent-skills | 2026-07-31 | Canonical shared-skills repo: `skills/<name>/SKILL.md` layout, `install-skills` (symlink or copy), `validate-skills` (checks YAML frontmatter + name/description) |
| S22 | https://claw-hub.net/ | 2026-07-31 | Third-party aggregator claiming 3,286 skills (conflicting count) |

## From `skill-ecosystems.md` — 14 source URLs

All accessed **2026-07-31**.

| ID | URL | Date accessed | Covers |
|---|---|---|---|
| S1 | https://agentskills.io/home.md | 2026-07-31 | Open standard overview; origin at Anthropic; progressive disclosure; 40+ conforming clients incl. all four targets; GitHub/Discord governance |
| S2 | https://agentskills.io/specification | 2026-07-31 | **Canonical spec**: full frontmatter table, name/description constraints, `license`/`compatibility`/`metadata`/`allowed-tools`, directory layout, progressive disclosure, file references, `skills-ref` validator |
| S3 | https://code.claude.com/docs/en/skills | 2026-07-31 | Claude Code: install paths & precedence, nested/`--add-dir`/symlink/live-reload behavior, **full 18-field frontmatter reference**, string substitutions, command naming, Cowork/cloud limits, share/distribution, `skillOverrides`, compaction budgets |
| S4 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | 2026-07-31 | Claude platform: required fields, name reserved words ("anthropic"/"claude"), 1024-char description, claude.ai **zip** upload via Settings > Features, `/v1/skills` API, absence of a `.skill` format |
| S5 | https://developers.openai.com/codex/skills/ | 2026-07-31 | **Codex**: `.agents/skills` search paths & precedence, symlink following, duplicate handling, required frontmatter, `agents/openai.yaml` schema, implicit/explicit invocation |
| S6 | https://docs.windsurf.com/windsurf/cascade/skills | 2026-07-31 | **Windsurf Skills**: `.windsurf/skills/`, `~/.codeium/windsurf/skills/`, enterprise system paths, **cross-agent paths `.agents/skills/` + `.claude/skills/`**, frontmatter, activation, open-standard conformance |
| S7 | https://docs.windsurf.com/windsurf/cascade/memories | 2026-07-31 | Windsurf **rules**: `.windsurf/rules/*.md`, `global_rules.md`, `trigger:` activation modes, `globs`, 12,000 / 6,000 char limits, AGENTS.md always-on |
| S8 | https://docs.windsurf.com/windsurf/cascade/workflows | 2026-07-31 | Windsurf **workflows**: `.windsurf/workflows/*.md`, global + enterprise paths, slash invocation, manual-only, 12,000-char limit, "use a Skill instead" guidance |
| S9 | https://trigger.fish/ and https://trigger.fish/features/ | 2026-07-31 | **Triggerfish** product identity: multi-channel, open-source, policy enforcement, classification levels, "Skills extend capabilities through simple folder conventions", The Reef, SPINE.md, TRIGGER.md |
| S10 | https://trigger.fish/integrations/skills (repo: `docs/integrations/skills.md`) | 2026-07-31 | **Triggerfish skills — primary source**: SKILL.md definition, frontmatter table, example, bundled/managed/workspace paths & precedence, discovery pipeline, self-authoring flow, The Reef (coming soon), CLI commands, security lifecycle |
| S11 | https://trigger.fish/reference/config-yaml.html | 2026-07-31 | `triggerfish.yaml` reference — confirms **no skills section**; plugins live in `~/.triggerfish/plugins/` (separate mechanism) |
| S12 | https://raw.githubusercontent.com/greghavens/triggerfish/master/README.md | 2026-07-31 | "Skills are folders with a `SKILL.md` file"; key-concepts table (SPINE.md, Skill, Trigger, The Reef _coming soon_); 10 bundled skills |
| S13 | `greghavens/triggerfish` @ `master`, `src/tools/skills/loader.ts` | 2026-07-31 | **Runtime loader source**: `buildSkillFromFrontmatter()` reads **top-level** `classification_ceiling`/`requires_tools`/`network_domains`; only `name` strictly required; `version` defaults `0.0.0`; **symlinked dirs skipped**; path jailing; content hashing; priority resolution |
| S14 | `greghavens/triggerfish` @ `master`, `src/skills/bundled/{pdf,deep-research}/SKILL.md` | 2026-07-31 | Real shipped skills confirming **top-level** security fields and no `metadata:` block |
| S15 | `greghavens/triggerfish` @ `master`, `docs/reef-registry/scripts/validate-skill.ts` | 2026-07-31 | Reef publish validation: `SKILL_REQUIRED_FIELDS` = name, version, description, author, tags, category, classification_ceiling; `tags` must be an array |
| S16 | https://agentskills.io/clients.md | 2026-07-31 | Client showcase with per-vendor setup-instruction URLs; confirms Claude Code, Claude, OpenAI Codex, Cursor, Copilot, VS Code et al.; **Triggerfish absent** |

**Access notes:** `docs.claude.com` 302-redirects to `platform.claude.com`. The GitHub API
and `github.com/tree/...` HTML were unavailable in this environment (session access
restriction and robots.txt respectively); Triggerfish source claims [S13][S14][S15] were
verified by shallow-cloning the repository over HTTPS and reading the files directly. The
repo's default branch is `master`, not `main`. `trigger.fish` serves docs under
`/integrations/` (extensionless URLs); `/guide/skills.html` and `/llms.txt` 404.

## From `tooling-powercli-vks-sdk.md` — 55 source URLs

All accessed **2026-07-31**.

| ID | URL | Doc set / version | Covers |
|---|---|---|---|
| S01 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-supervisor-installation-and-configuration.html | VCF 9.1 | Supervisor Platform section index; deployment topologies |
| S02 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-0/managing-vsphere-kuberenetes-service-clusters-and-workloads/provisioning-tkg-service-clusters/about-tkg-cluster-provisioning.html | VCF Service Admin & Dev 9.0 | VKS provisioning APIs, CAPI/CAPV, v1beta1/v1beta2, TKC deprecation |
| S03 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-0/managing-vsphere-kuberenetes-service-clusters-and-workloads/provisioning-tkg-service-clusters/workflow-for-provisioning-tkg-clusters-using-kubectl.html | VCF Service Admin & Dev 9.0 | kubectl provisioning workflow, verbatim commands |
| S04 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-vsphere-powercli-specific-concepts.html | VCF 9.1 | PowerCLI concepts; `$DefaultVIServers` / `$DefaultCIServers` |
| S05 | https://www.powershellgallery.com/packages/VCF.PowerCLI/9.0.0.24798382 | PS Gallery | VCF.PowerCLI 9.0 dependency list, publish date, install cmd |
| S06 | https://www.powershellgallery.com/packages/VCF.PowerCLI | PS Gallery | Version history (9.0.0.24798382, 9.1.0.25380678) |
| S07 | https://www.powershellgallery.com/packages/VCF.PowerCLI/9.1.0.25380678 | PS Gallery | VCF.PowerCLI 9.1 dependency list; Sso added / VCenter removed |
| S08 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | VCF 9.1 | 9.1 What's New: CLI/API/SDK, new cmdlets, new APIs |
| S09 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-powercli-changelog.html | VCF 9.1 | PowerCLI 9.1 changelog counts per module |
| S10 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-cloud-applications/provision-and-manage-virtual-machines/deploying-and-managing-virtual-machines-in-vsphere-iaas-control-plane.html | VCF 9.0 | VM Service; VM Operator v1alpha1 deprecation, v1alpha2/v1alpha3 |
| S11 | https://github.com/vmware/vcf-api-specs/blob/main/README.md | GitHub main | OpenAPI spec repo layout, components, OpenAPI 2.0 vs 3.0 |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html | VCF 9.0 | 9.0 What's New: VCF.PowerCLI rename, SDK builds, VCF CLI intro |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/configuring-vmware-vsphere-powercli.html | VCF 9.1 | Configuration topics: certs, timeout, scopes, Python, CEIP |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli.html | VCF 9.1 | PowerCLI section index; full child-page list |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli/install-powercli.html | VCF 9.1 | `Install-Module VCF.PowerCLI -Scope CurrentUser`, `Import-Module` |
| S16 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/installing-vmware-vsphere-powercli.html | VCF 9.1 | Install section index; offline-install existence |
| S17 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/vmware-powercli-compatibility-matrix.html | VCF 9.1 | PowerShell 7.x; 5.1 deprecated; OS & .NET prereqs; interop matrix pointer |
| S18 | https://developer.broadcom.com/powercli/all-powercli-modules | developer portal (latest) | Module → cmdlet-reference URL map |
| S19 | https://developer.broadcom.com/powercli/latest/vmware.vimautomation.core/commands/connect-viserver | developer portal (latest) | `Connect-VIServer` syntax and parameters |
| S20 | https://developer.broadcom.com/powercli/latest/vmware.sdk.vcf.sddcmanager/commands/connect-vcfsddcmanagerserver | developer portal (latest) | `Connect-VcfSddcManagerServer` full syntax |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/power-cli/latest/powercli/configuring-vmware-vsphere-powercli/configuring-powercli-invalid-server-certificate-actions/configure-invalid-server-certificate-action.html | PowerCLI doc set (latest) | `-InvalidCertificateAction` values, default, Linux/macOS limits |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vmware-vsphere-supervisor-release-notes.html | VCF Service Admin & Dev 9.1 | Supervisor 9.1.0.0 versions, Container Service, VM Service, NSX UI regression |
| S23 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes/vmware-tanzu-kubernetes-grid-service-36-release-notes.html | VCF Service Admin & Dev 9.1 | VKS 3.6.x versions/dates, K8s 1.35, ClusterClass, 9.1 features |
| S24 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html | VCF 9.0 | `vcf context create` login, env var, context commands |
| S25 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/connect-to-the-supervisor-cluster-as-a-vcenter-single-sign-on-user.html | VCF 9.1 | Same login flow, 9.1; no kubectl vsphere mention |
| S26 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes.html | VCF Service Admin & Dev 9.1 | VKS release-notes index: 3.3/3.4/3.5/3.6/3.7 |
| S27 | https://vm-operator.readthedocs.io/en/docs-stable/concepts/services-networking/vm-service/ | upstream OSS (docs-stable) | `vmoperator.vmware.com` group; v1alpha1–v1alpha5; kinds |
| S28 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/managing-vsphere-kubernetes-service/running-tkg-service-clusters/tkg-service-components.html | VCF Service Admin & Dev 9.1 | VKS components, controller layers, CNI/CSI/auth/LB |
| S29 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes/vks-release-notes/vmware-tanzu-kubernetes-grid-service-34-release-notes.html | VCF Service Admin & Dev 9.1 | VKS 3.4.x versions/dates, K8s 1.33, `builtin-generic-v3.4.0`, TKC cutoff |
| S30 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/download-and-install-the-kubernetes-cli-tools-for-vsphere.html | VCF 9.0 | VCF Consumption CLI download/install; `vcf-cli-{os}_{arch}` |
| S31 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters/download-and-install-the-kubernetes-cli-tools-for-vsphere.html | VCF 9.1 | Same, 9.1; confirms no kubectl/kubectl-vsphere in package |
| S32 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-consumption/latest/consumer-interfaces-in-vcf/installing-and-using-vcf-cli-v9.html | VCF Consumption (latest) | VCF CLI v9.1.0.0, capabilities, install modes |
| S33 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-consumption/latest/consumer-interfaces-in-vcf/installing-and-using-vcf-cli-v9/command-reference2.html | VCF Consumption (latest) | VCF CLI command groups and plugin list |
| S34 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/programming-language-support-in-the-vsphere-web-services-sdk.html | VCF 9.1 | Supported languages: Java, Python, OpenAPI 3.0.1, SOAP |
| S35 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi.html | VCF 9.0 | Spec download channels; openapi-generator; no on-appliance URLs |
| S36 | https://developer.broadcom.com/sdks | developer portal | Full SDK catalog incl. deprecated .NET/Perl/Ruby |
| S37 | https://developer.broadcom.com/vcf-python-sdk | developer portal | `vcf-sdk` PyPI, v9.1, Python 3.10–3.14, GitHub, coverage |
| S38 | https://developer.broadcom.com/vcf-java-sdk | developer portal | `com.vmware.sdk:vcf-sdk-bom`, v9.1, Java 11/17/21/25, GitHub |
| S39 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/getting-started-with-vsphere-apis-and-sdks/python-access-to-vsphere-apis.html | VCF 9.0 | pyVmomi install, SmartConnect, community samples |
| S40 | https://developer.broadcom.com/sdks/vcf-api-specification/latest | developer portal | `vcf-api-specs-9.1.0.0-25372366.zip`, 39.36 MB, 8 products |
| S41 | https://developer.broadcom.com/xapis/vmware-vsphere-kubernetes-service/latest/ | developer portal | VKS API reference; versions 3.6.0 / 3.4.1; api-docs.html |
| S43 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development.html | VCF 9.1 | VCF APIs & SDKs overview; API categories; explicit absence of explorer URLs |
| S43b | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-vmware-vsphere-powercli/microsoft-powershell-basics.html | VCF 9.1 | PowerShell basics; `Get-Help about_CommonParameters` |
| S44 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | "Administration SDKs, APIs, and CLI" section index (9 subsections) |
| S45 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | Top-level doc-set index |
| S46 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk.html | VCF 9.1 | SDK Developer's Setup Guide child-page list |
| S47 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-supervisor-installation-and-configuration/connecting-to-vsphere-with-tanzu-clusters.html | VCF 9.1 | "Connecting to Supervisor and VKS Clusters" index; VCF Consumption CLI framing |
| S48 | https://developer.broadcom.com/powercli | developer portal | PowerCLI landing: 9.1/9.0, install guide, changelog, reference URLs |
| S49 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-1/release-notes.html | VCF Service Admin & Dev 9.1 | Release-notes index (Supervisor, VKS, VKr, Standard Packages) |
| S50 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-service-administration-and-development/9-0/release-notes.html | VCF Service Admin & Dev 9.0 | 9.0 release-notes index |

**Search-only sources** (result listings used to locate URLs; not themselves fact sources):
`S26-search` (VCF CLI / consumption CLI query, surfaced `developer.broadcom.com/xapis/vcf-cli-api/latest/`),
`S42-search` (VCF Operations for Networks "Using API Explorer" page URL),
`S43-search` (vCenter Developer Center / API Explorer — vSphere 7.0 & 8.0 doc sets only).

**Retrieval failures encountered:**
- `https://developer.broadcom.com/powercli/latest/products/vcfsddcmanager/` — "PowerCLI Details Page is temporarily unavailable."
- `https://techdocs.broadcom.com/.../9-1/.../configuring-vmware-powercli-response-to-untrusted-certificates.html` — HTTP 404 (correct path is under `configuring-powercli-invalid-server-certificate-actions/`; the 9.0 variant returned HTTP 403, the `power-cli/latest` variant [S21] succeeded).
- `https://www.powershellgallery.com/api/v2/Packages(...)` — returns binary/unparseable content via fetch; `curl` blocked by agent proxy (`CONNECT tunnel failed, 403`).
- `https://techdocs.broadcom.com/.../vcf-service-administration-and-development/9-1.html` — JS-only shell, no navigable content.
- `https://techdocs.broadcom.com/.../vcf-service-administration-and-development/9-0/release-notes/vmware-tanzu-kubernetes-grid-service-release-notes.html` — redirect stub pointing to the 9.1 site.

## From `vcf-automation.md` — 40 source URLs

All accessed **2026-07-31**.

| ID | URL | Doc set version | Date accessed | Covers |
|---|---|---|---|---|
| S01 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | VCF 9.0 | 2026-07-31 | 9.0 landing; section URLs incl. Workload Orchestration |
| S02 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | 2026-07-31 | 9.1 landing; section URLs |
| S03 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-cloud-applications.html | VCF 9.0 | 2026-07-31 | VCF Automation consumption framing; workload types; child topics |
| S04 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/vcf-advanced-services.html | VCF 9.0 | 2026-07-31 | Advanced Services scope (not VCF Automation) |
| S05 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools.html | VCF 9.0 | 2026-07-31 | 9.0 SDK/API/CLI section structure |
| S06 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-cloud-applications/getting-started-with-the-tools-for-building-applications.html | VCF 9.0 | 2026-07-31 | All Apps vs VM Apps orgs; UI/catalog/CLI v9.0; IaaS Services Console |
| S07 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api.html | VCF 9.0 | 2026-07-31 | `/provider` and `/automation` UI surfaces |
| S08 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1.html | VCF 9.0 | 2026-07-31 | 15 VM Apps API services + descriptions; API Help Center; developer portal link |
| S09 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-automation.html | VCF 9.1 | 2026-07-31 | What's New — VCF Automation (primary delta source) |
| S10 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/overview-of-vmware-cloud-foundation-9/what-is-vmware-cloud-foundation-and-vmware-vsphere-foundation/vcf-automation-overview.html | VCF 9.0 | 2026-07-31 | 9.0 product definition; four components; Aria rename |
| S11 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/overview-of-vmware-cloud-foundation-9/what-is-vmware-cloud-foundation-and-vmware-vsphere-foundation/vcf-automation-overview.html | VCF 9.1 | 2026-07-31 | 9.1 product definition; four components |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token.html | VCF 9.0 | 2026-07-31 | Token types, lifespans, 3-step flow |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token.html | VCF 9.1 | 2026-07-31 | Same, confirming no change in 9.1 |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/getting-your-authentication-token/get-your-access-token-for-vra-8-x.html | VCF 9.0 | 2026-07-31 | **VM Apps token endpoint** `/tm/oauth/tenant/{tenant}/token` + curl |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access/token-exchange-architecture.html | VCF 9.1 | 2026-07-31 | VIDB 4-step token exchange architecture |
| S16 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/service-provider-portal/generating-provider-management-api-tokens.html | VCF 9.0 | 2026-07-31 | **Provider device-authorization grant flow** + curl |
| S17 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/fleet-management/managing-identity-and-access-using-vcf-single-sign-on/managing-api-clients-and-tokens/managing-api-tokens.html | VCF 9.1 | 2026-07-31 | VCF SSO API client/token creation UI; TTL defaults |
| S18 | https://developer.broadcom.com/xapis/vm-apps-org-catalog/latest/ | VCF Automation API 9.1 (latest) | 2026-07-31 | Catalog/Deployment/Requests categories; OData query params |
| S19 | https://developer.broadcom.com/xapis/provider-infrastructure-apis/latest/ | VCF Automation API 9.1 (latest) | 2026-07-31 | REST conventions, URNs, 202+Location, version header, auth headers |
| S20 | https://developer.broadcom.com/xapis/all-apps-org-access-control/latest/ | VCF Automation API 9.1 (latest) | 2026-07-31 | All Apps REST shape; URN IDs; version negotiation |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/organization-management/vcfa-overview.html | VCF 9.1 | 2026-07-31 | VM Apps org terminology + 9 UI tabs (9.1) |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/organization-management/vcfa-overview.html | VCF 9.0 | 2026-07-31 | VM Apps org terminology + 9 UI tabs (9.0) |
| S23 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/requesting-a-deployment-from-a-catalog-item/request-deployment.html | VCF 9.0 | 2026-07-31 | **`/catalog/api/items/{id}/request`, `/deployment/api/deployments`** |
| S24 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/working-with-blueprints-cloud-templates/create-and-update-a-cloud-template.html | VCF 9.0 | 2026-07-31 | **`/blueprint/api/blueprints`** CRUD + validation + curl |
| S25 | https://developer.broadcom.com/xapis/org-management-vm-apps-org/latest/ | VCF Automation API (latest) | 2026-07-31 | Master index of 15 VM Apps Org APIs |
| S26 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/provider-management/terraform-configurations-in-vcf-automation-provider-management.html | VCF 9.0 | 2026-07-31 | Three Terraform providers; `/automation/api-docs/#/terraform-provider` |
| S27 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/provider-management/terraform-configurations-in-vcf-automation-provider-management.html | VCF 9.1 | 2026-07-31 | Three Terraform providers, re-scoped; resources by role |
| S28 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | 2026-07-31 | 9.1 SDK/API/CLI restructure |
| S29 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-the-vcf-automation-api.html | VCF 9.1 | 2026-07-31 | 9.1 All Apps API child topics; UI surfaces |
| S30 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access.html | VCF 9.1 | 2026-07-31 | **VIDB `/acs/t/{role}/token`**; token model; covered components |
| S31 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-the-vcf-automation-api/categories-of-vcf-automation-hard-tenancy-apis.html | VCF 9.1 | 2026-07-31 | 13 provider REST API categories (9.1) |
| S32 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/about-the-vcf-automation-api/kubernetes-commands-for-devops.html | VCF 9.1 | 2026-07-31 | **All Apps CRDs**, `infrastructure.cci.vmware.com/v1alpha2`, `--context cci` |
| S33 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/categories-of-vcf-automation-hard-tenancy-apis.html | VCF 9.0 | 2026-07-31 | 13 provider REST API categories (9.0); VM-Apps-only exclusions |
| S34 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/building-your-cloud-applications.html | VCF 9.1 | 2026-07-31 | VCF CLI v9.1; 9.1 workload types; doc restructure |
| S35 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/working-with-blueprints-cloud-templates.html | VCF 9.0 | 2026-07-31 | Landing page; "Blueprints/Cloud Templates" dual naming |
| S36 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/requesting-a-deployment-from-a-catalog-item.html | VCF 9.0 | 2026-07-31 | Landing page; names Catalog + Deployment APIs |
| S37 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/managing-your-projects.html | VCF 9.0 | 2026-07-31 | Landing page; Project Service API named, no paths |
| S38 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-are-the-automation-apis-and-how-do-i-use-them_1/setting-up-cloud-assembly.html | VCF 9.0 | 2026-07-31 | Landing page; names IaaS APIs, no paths |

**Retrieval failures (recorded for completeness):**

| URL | Result |
|---|---|
| `.../9-1/building-your-cloud-applications/getting-started-with-the-tools-for-building-applications.html` | HTTP 404 — page does not exist in 9.1 (evidence for delta row 18) |
| `.../9-0/administration-sdks-cli-and-tools/about-the-vcf-automation-api/generating-an-access-token.html` | HTTP 404 on fetch despite appearing in search index |
| `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-1-and-later/9-1.html` | HTTP 404 — the 9.1 doc set lives under `vcf-9-0-and-later/9-1`, not `vcf-9-1-and-later` |
| `.../9-0/.../working-with-deployments-and-resources.html` | HTTP 429 on all attempts |
| `https://developer.broadcom.com/xapis/vm-apps-org-catalog/latest/catalog/api/items/` | "Object Not Found" — deep-linking into portal sub-paths does not work |

## From `vcf-core-9.0.md` — 36 source URLs

All accessed **2026-07-31**. "Doc set version" indicates the version scope of the URL subtree, not necessarily the version of every fact on the page.

| ID | URL | Doc set version | Date accessed | What it covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | 9.0 (family "9.0 and later") | 2026-07-31 | VCF 9.0 doc landing page; full 25-guide table of contents and URLs |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes.html | 9.0 | 2026-07-31 | 9.0 release date (17 JUN 2025) and build (24755599); RN subtree URLs; PDF link |
| S3 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes.html | 9.0 | 2026-07-31 | Release-notes index: 9.0, 9.0.1, 9.0.2, patch releases, async releases, Download Tool RN |
| S4 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | 9.0 | 2026-07-31 | Full 9.0.0.0 BOM incl. add-ons; vSphere Foundation inclusion column |
| S5 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new.html | 9.0 | 2026-07-31 | What's New themes; FIPS default; licensing simplification; 90-day eval |
| S6 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-1-release-notes.html | 9.0 (9.0.1 content) | 2026-07-31 | 9.0.1.0 release date 29 SEP 2025; maintenance-release characterization; child URLs |
| S7 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-1-release-notes/vmware-cloud-foundation-901-bill-of-materials.html | 9.0 (9.0.1 content) | 2026-07-31 | Full 9.0.1.0 BOM with versions and builds |
| S8 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-2-release-notes.html | 9.0 (9.0.2 content) | 2026-07-31 | 9.0.2.0 release date 20 JAN 2026; maintenance scope; BOM sub-page URL |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-2-release-notes/vmware-cloud-foundation-902-bill-of-materials.html | 9.0 (9.0.2 content) | 2026-07-31 | Full 9.0.2.0 BOM; SDDC Manager and VCF Installer share build 25151285 |
| S10 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes.html | 9.0 | 2026-07-31 | Deprecations and removals: SDDC Manager UI, ELM, Host Profiles, IWA, vLCM baselines, Cloud Builder, UMDS, precheck API move |
| S11 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/overview-of-vmware-cloud-foundation-9.html | 9.0 | 2026-07-31 | Overview landing; positioning statement; child page URLs (taxonomy, VVF, getting started) |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/overview-of-vmware-cloud-foundation-9/workload-domains-in-vmware-cloud-foundation.html | 9.0 | 2026-07-31 | VCF taxonomy: Private Cloud, Fleet, Instance, management domain, workload domain, domain composition |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment.html | 9.0 | 2026-07-31 | Deployment landing; three paths (new / converge / upgrade); child page URLs |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/what-is-the-vcf-installer-.html | 9.0 | 2026-07-31 | VCF Installer definition; `VCF-SDDC-Manager-Appliance-9.x.x.ova`; SDDC Manager mode switch; express-patch limitation; topologies |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/converging-your-existing-vsphere-infrastructure-to-a-vcf-or-vvf-platform-.html | 9.0 | 2026-07-31 | Convergence definition, phases, NSX gate (9.0.0 vs 9.0.1), storage/network/compute prereqs, unsupported configs |
| S16 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/upgrading-cloud-foundation.html | 9.0 | 2026-07-31 | Upgrade sources (VCF 5.0+), skip-level support, core vs management component ordering, SDDC Manager UI deprecation notice |
| S17 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/licensing.html | 9.0 | 2026-07-31 | Licensing landing; subscription license files replace 25-char keys; vCenter-level assignment; 20 child page URLs |
| S18 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/licensing/licensing-overview.html | 9.0 | 2026-07-31 | License types and units (cores/TiB), default license generation, connected vs disconnected, 180-day reporting, 90-day grace |
| S19 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/lifecycle-management.html | 9.0 | 2026-07-31 | LCM landing; VCF Operations as central LCM tool; five child page URLs |
| S20 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/lifecycle-management/lifecycle-management-of-vcf-core-components.html | 9.0 | 2026-07-31 | Maintenance-release upgrade sequencing (mgmt then core: SDDC Mgr → NSX → vCenter → ESX → vSAN); flexible BOM upgrade; child URLs |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/lifecycle-management/binary-management-for-vmware-cloud-foundation.html | 9.0 | 2026-07-31 | Binary ownership split (fleet mgmt vs SDDC Manager); VCF Download Tool as CLI; three child URLs |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools.html | 9.0 | 2026-07-31 | SDK/API/CLI guide index and child URLs |
| S23 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide.html | 9.0 | 2026-07-31 | VCF Programming Guide index; confirms no API detail at this level |
| S24 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/vcf-apis-and-scripts.html | 9.0 | 2026-07-31 | SDK GitHub repos (vcf-sdk-python, vcf-sdk-java) with SDDC Manager / VCF Import examples; pointers to API reference portals |
| S25 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html | 9.0 | 2026-07-31 | Java/Python SDK 9.0.0.0 details, PowerCLI→VCF PowerCLI rename and new Sddc cmdlets, VCF Consumption CLI, vCenter OpenAPI 3.0 |
| S26 | https://developer.broadcom.com/xapis/sddc-manager-api/latest/ | 9.1 ("latest"), 9.0 also selectable | 2026-07-31 | SDDC Manager API reference index; 58 resource categories |
| S27 | https://developer.broadcom.com/xapis/sddc-manager-api/9.0/ | 9.0 | 2026-07-31 | 9.0 SDDC Manager API: Bearer auth, 1h/24h token lifetimes, `/<version>/resource` pattern, 50+ resource categories, category URL pattern |
| S28 | https://developer.broadcom.com/xapis/sddc-manager-api/9.0/tokens/ | 9.0 | 2026-07-31 | Exact token endpoints: `POST /v1/tokens`, `PATCH /v1/tokens/access-token/refresh`, `DELETE /v1/tokens/refresh-token`; schemas and headers |
| S29 | https://developer.broadcom.com/xapis/sddc-manager-api/9.0/domains/ | 9.0 | 2026-07-31 | Full Domains endpoint inventory; example base URL `https://sfo-vcf01.rainpole.io/v1`; validations/tags/isolation-prechecks/query patterns |
| S30 | https://developer.broadcom.com/xapis/vcf-installer-api/latest/ | 9.1 ("latest"), 9.0 also available | 2026-07-31 | VCF Installer API reference; 11-12 resource categories; scope statement |
| S31 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-private-cloud-infrastructure.html | 9.0 | 2026-07-31 | Build-phase guide index; which UI performs which workflow; network pools, stretched clusters, VPCs |
| S32 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-private-cloud-infrastructure/sddc-manager-workflows.html | 9.0 | 2026-07-31 | **SDDC Manager UI deprecation statement**; mapping of former SDDC Manager workflows to their new locations |
| S33 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-private-cloud-infrastructure/working-with-workload-domains.html | 9.0 | 2026-07-31 | Domain operations: create, import, delete, expand, shrink, configuration drift; per-operation URLs and interfaces |
| S34 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi/opnapi-for-sddc-manager.html | 9.0 | 2026-07-31 | "~280 interfaces in the SDDC Manager API"; SDDC Manager appliance role; confirms absence of spec download URL on this page |
| S35 | https://developer.broadcom.com/sdks/vcf-api-specification/latest | 9.1 ("latest") | 2026-07-31 | VCF API Specification bundle: 8 component specs incl. SDDC Manager and VCF Installer; `vcf-api-specs-9.1.0.0-25372366.zip`; GitHub `vmware/vcf-api-specs` |
| S-search | WebSearch result sets (queries on developer.broadcom.com SDDC Manager API and OpenAPI spec) | mixed | 2026-07-31 | Used only for URL **discovery** (locating S26–S30, S34, S35 and the `/9-1/` subtree). No substantive facts sourced from search snippets alone. |

## From `vcf-core-9.1-and-deltas.md` — 16 source URLs

| ID | URL | Doc set / version | Date accessed | Covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | VCF 9.1 | 2026-07-31 | 9.1 doc tree / top-level guide slugs |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes.html | VCF 9.1 RN | 2026-07-31 | Release date 12 MAY 2026; RN section map; sub-page URLs |
| S3 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new.html | VCF 9.1 RN | 2026-07-31 | Headline 9.1 capabilities; per-component link map |
| S4 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-ops.html | VCF 9.1 RN | 2026-07-31 | **Fleet Management Appliance removal**; fleet lifecycle; SDDC Manager scale 5000 hosts; license server; Fleet Mgmt features; HCX; logs; health |
| S5 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsphere.html | VCF 9.1 RN | 2026-07-31 | vSphere/ESX/vCenter What's New; new APIs |
| S6 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | VCF 9.1 RN | 2026-07-31 | New APIs; Java/Python SDK coverage incl. Fleet+SDDC Lifecycle; PowerCLI 9.1 |
| S7 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-installer.html | VCF 9.1 RN | 2026-07-31 | Installer What's New; out-of-band ops; convergence scenarios; default mgmt services deployment |
| S8 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.1 RN | 2026-07-31 | **9.1 BOM**; VCF Installer/SDDC Manager merged row; row presence/absence checks |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/fleet-management.html | VCF 9.1 | 2026-07-31 | Fleet Management doc section scope; "Use VCF Operations as a VI administrator…" |
| S10 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vcf-91-product-support-notes.html | VCF 9.1 RN | 2026-07-31 | **All 9.1 deprecations/removals**: vCLS, port 514, 21 SDDC Mgr APIs, vStats, 369 provider ops, content packs |
| S11 | .../9-0/release-notes/vmware-cloud-foundation-90-release-notes.html | VCF 9.0 RN | 2026-07-31 | 9.0 release date 17 JUN 2025 (build 24755599); 9.0 RN URL map |
| S12 | .../9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.0 RN | 2026-07-31 | **9.0 BOM baseline** — separate SDDC Manager, fleet management, collector, for-logs, Identity Broker rows |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment/vcf-management-appliances.html | VCF 9.1 | 2026-07-31 | **Authoritative 9.1 component list**; SDDC Manager role; VCF Management Services table |
| S14 | .../9-1/lifecycle-management/lifecycle-management-in-vmware-cloud-foundation.html | VCF 9.1 | 2026-07-31 | "fleet lifecycle and SDDC lifecycle components now replace the VCF Operations fleet management appliance" |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment/upgrading-cloud-foundation.html | VCF 9.1 | 2026-07-31 | **9.0.x→9.1 ordered upgrade sequence**; **SDDC Manager UI deprecation quote**; LCM transition statement |
| S16 | https://developer.broadcom.com/sdks/vcf-api-specification/latest | VCF API Spec v9.1 | 2026-07-31 | v9.1 selector; `vcf-api-specs-9.1.0.0-25372366.zip`; includes SDDC Manager, SDDC Lifecycle, Fleet Lifecycle OpenAPI |
| S17 | .../9-1/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi/opnapi-for-sddc-manager.html | VCF 9.1 | 2026-07-31 | SDDC Manager ~280 REST interfaces; appliance description |
| S18 | https://knowledge.broadcom.com/external/article/440630/upgrade-sequence-and-related-issues-for.html | Broadcom KB 440630 (9.1) | 2026-07-31 | VCF Mgmt Services mandatory; "completely replaces the standalone Fleet Management Appliance"; license server required; 4 known upgrade issues |
| S19 | .../9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development/oauth-token-support-for-api-and-cli-access/token-exchange-architecture.html | VCF 9.1 | 2026-07-31 | **9.1 OAuth token exchange 4-step flow**; VIDB role; refresh vs access token |
| S20 | .../9-1/administration-sdks-cli-and-tools/about-vmware-cloud-foundation-development.html | VCF 9.1 | 2026-07-31 | "unified API and CLI access … OAuth standards-based token authentication, based on VCF Identity Broker (VIDB)" |
| S21 | https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/ | VCF API Ref — **5.2.4 "Latest"** | 2026-07-31 | Legacy SDDC Manager Tokens API auth (1 h / 24 h); `/v1/` `/v2/` prefixes; **stale, not 9.x** |
| S22 | https://blogs.vmware.com/cloud-foundation/2026/05/25/unlocking-the-full-potential-of-programmable-infrastructure-with-vmware-cloud-foundation-9-1-new-features-and-capabilities/ | VMware blog (9.1), 2026-05-25 | 2026-07-31 | Real-Time Metrics Prometheus/PromQL/Grafana; Utilization API URL; SDK distribution; spec shortlinks |
| S23 | https://news.broadcom.com/releases/broadcom-announces-vmware-cloud-foundation-9-1 | Broadcom press release, 2026-05-05 | 2026-07-31 | Announcement date; 5,000 hosts; 4x faster cluster upgrades; 40%/39%/46% claims; 2.6x K8s scale |
| S24 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsan.html | VCF 9.1 RN | 2026-07-31 | vSAN 9.1 What's New (18 items) |
| S25 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-nsx.html | VCF 9.1 RN | 2026-07-31 | NSX 9.1 What's New; Edge upgrade reordering; out-of-band SDDC Manager |
| S26 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-automation.html | VCF 9.1 RN | 2026-07-31 | VCF Automation 9.1; "Multiple External Connections (Formerly Provider Gateways)"; Supervisor deferral |
| S27 | .../9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/upgrade-sequence-to-91.html | VCF 9.1 RN | 2026-07-31 | Supported source versions (5.2.x / 9.0.x); "strict component upgrade sequence" |
| S28 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment.html | VCF 9.1 | 2026-07-31 | Deployment/convergence/upgrade sub-page map; four upgrade scenarios |
| S29 | .../9-1/deployment/upgrading-cloud-foundation/deploy-vcf-management-services.html | VCF 9.1 | 2026-07-31 | Mgmt Services deploy prerequisites; VCF Operations UI navigation path |
| S30 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/licensing.html | VCF 9.1 | 2026-07-31 | License server statements; VCF Business Services console; licensing sub-pages |
| S31 | .../9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new.html | VCF 9.0 RN | 2026-07-31 | 9.0 baseline What's New; "instead of 11 license keys, there are only two licenses" |
| S32 | .../9-1/overview-of-vmware-cloud-foundation-9.html | VCF 9.1 | 2026-07-31 | Navigation hub only — thin, see Gap 8.9 |
| S33 | .../9-1/overview-of-vmware-cloud-foundation-9/what-is-vmware-cloud-foundation-and-vmware-vsphere-foundation.html | VCF 9.1 | 2026-07-31 | VCF Operations / VCF Automation role statements; no SDDC Manager detail |
| S34 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | 2026-07-31 | SDK/API/CLI guide sub-page map |
| S35 | .../9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-ops.html | VCF 9.0 RN | 2026-07-31 | 9.0 Fleet Management feature baseline (license/IAM/cert/password/config/tag mgmt) |
| S36 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/lifecycle-management.html | VCF 9.1 | 2026-07-31 | Lifecycle Management section map; "Use VCF Operations … to manage the lifecycle" |

*(Paths shown with a leading `...` share the prefix `https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later`.)*

## From `vcf-operations.md` — 33 source URLs

| ID | URL | Doc set version | Date accessed | Covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-ops.html | 9.1 | 2026-07-31 | Full 9.1 VCF Ops What's New; Fleet Lifecycle replacing Fleet Mgmt Appliance (verbatim); SDDC Manager scale; Log Management; RTM; Networks; HCX; Orchestrator; deprecations |
| S2 | https://developer.broadcom.com/xapis | portal, undated | 2026-07-31 | Master list of VCF API references and their URLs |
| S3 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/ | 9.1 (latest), notes 9.0 | 2026-07-31 | VCF Operations API overview; auth schemes; 40+ category list |
| S4 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/fleet-management.html | 9.1 | 2026-07-31 | 9.1 Fleet Mgmt scope; "No dedicated Fleet Management Appliance exists"; SDDC Manager password role; sub-page list |
| S5 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/fleet-management.html | 9.0 | 2026-07-31 | 9.0 Fleet Mgmt scope and sub-page list; shared "For VCF, you use VCF Operations..." sentence |
| S6 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk/vcf-changelog.html | 9.1 | 2026-07-31 | VCF Operations API: 134 new / 0 deprecated / 0 deleted operations |
| S7 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-9-0-1-release-notes/vcf-operations-9-0-1-0000.html | 9.0.1 | 2026-07-31 | 9.0.1 component names, versions, builds incl. Fleet Management and Logs Agent |
| S8 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | 9.0 | 2026-07-31 | Full 9.0 BOM incl. SDDC Manager and all Operations components |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html | 9.1 | 2026-07-31 | Full 9.1 BOM incl. Fleet lifecycle, SDDC lifecycle, Log management, Cloud proxy, Real-time metrics |
| S10 | https://developer.broadcom.com/xapis/vcf-operations-api/9.1/changelog/ | 9.1 | 2026-07-31 | Concrete list of operations new in 9.1, grouped by category, with exact paths |
| S11 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/suite-api/api/resources/get/ | 9.1 (latest) | 2026-07-31 | GET /suite-api/api/resources params; sibling stats/groups/profiles operation names; host form |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/upgrading-cloud-foundation/preparing-your-vcf-9-management-components/upgrading-management-components/upgrade-to-vcf-operations.html | 9.0 | 2026-07-31 | Title only, via search: "Upgrade VMware Aria Operations to VCF Operations 9.0" |
| S12b | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/using-the-api-with-vrealize-operations-manager.html | 9.0 | 2026-07-31 | On-appliance swagger UI URL `/suite-api/doc/swagger-ui.html`; client bindings URL |
| S13 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/deployment/upgrading-cloud-foundation/preparing-your-vcf-9-management-components/preparing-to-upgrade-to-vmware-cloud-foundation/install-the-vcf-operations-fleet-management-appliance.html | 9.0 | 2026-07-31 | Title only, via search: "Deploy the VCF Operations fleet management Appliance". Body HTTP 403 on 2 attempts |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html | 9.0 | 2026-07-31 | 9.0 token acquire endpoint, payload, response, header formats, 6h TTL |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/understanding-the-vr-ops-api/getting-started-with-the-api/acquire-an-authentication-token.html | 9.1 | 2026-07-31 | 9.1 token acquire — identical to 9.0; auth sources; explicit 6h TTL quote |
| S16 | https://developer.broadcom.com/xapis/vcf-operations-api/9.0/ | 9.0 | 2026-07-31 | 9.0 API category list; absence of fleet-management, findings, salt, whatif |
| S17 | https://developer.broadcom.com/xapis/vcf-operations-for-networks-api/latest/api-security-schema/ | 9.1 (latest) | 2026-07-31 | Networks auth: `Authorization: NetworkInsight {token}` and Bearer JWT |
| S18 | https://developer.broadcom.com/xapis/log-management-api/latest/ | 9.1 (latest) | 2026-07-31 | Log Management API v2; X-JWT-Token via token/exchange with serviceKeys ["ops-li"]; categories |
| S19 | https://developer.broadcom.com/xapis/realtime-metrics-api/latest/ | 9.1 (latest) | 2026-07-31 | RTM Prometheus-compatible API; VCF_VODAP service key exchange; Bearer JWT; categories; `/suite-api/api/` host form |
| S20 | https://developer.broadcom.com/xapis/vcf-operations-for-networks-api/latest/operation-index/ | 9.1 latest + 9.0 selector | 2026-07-31 | Confirms 9.0 and 9.1 versions exist; category names; operation detail returned "Object Not Found" |
| S21 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/suite-api/api/alerts/get/ | 9.1 (latest) | 2026-07-31 | Alerts and alertdefinitions exact paths and params |
| S22 | https://developer.broadcom.com/xapis/vcf-fleet-lcm-service-apis/latest/api-security-schema/ + .../latest/ | 9.1 (latest) | 2026-07-31 | Fleet LCM auth schemes (Basic, Bearer JWT); category list |
| S23 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/suite-api/api/reports/get/ | 9.1 (latest) | 2026-07-31 | Reports and reportdefinitions exact paths incl. download and schedules |
| S24 | https://developer.broadcom.com/xapis/vcf-operations-api/latest/operation-index/ | 9.1 (latest) | 2026-07-31 | Category navigation; no dashboard endpoints found; Super Metrics / Resource / Resources category URLs |
| S25 | https://developer.broadcom.com/xapis/log-management-api/latest/operation-index/ | 9.1 (latest) | 2026-07-31 | Returned "Object Not Found"; yielded Query category URL only |
| S26 | https://developer.broadcom.com/xapis/log-management-api/latest/api/v2/events/query/post/ | 9.1 (latest) | 2026-07-31 | Returned "Object Not Found" — speculative path not confirmed |
| S27 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html | 9.0 | 2026-07-31 | 9.0 SDK component coverage (SDDC Manager, VCF Installer, vCenter, vSAN DP); SDK URLs |
| S28 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | 9.1 | 2026-07-31 | 9.1 SDK additions incl. VCF Operations, Log Management, Ops for Networks, Fleet LCM, SDDC LCM; PowerCLI modules |
| S29 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new.html | 9.0 | 2026-07-31 | 9.0 "new Operate Experience"; licensing/fleet licensing model; connected vs disconnected mode |
| S30 | https://github.com/vmware/vcf-api-specs | repo, undated | 2026-07-31 | OpenAPI spec product list incl. VCF Operations, Ops for networks, Log Management, Real-time metrics, Fleet lifecycle, SDDC lifecycle; `/specifications` layout |
| S31 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html | 9.1 | 2026-07-31 | 9.1 doc-set section URLs |
| S32 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html | 9.0 | 2026-07-31 | 9.0 doc-set section URLs incl. administration-sdks-cli-and-tools |

## From `vsphere-vcenter-vsan.md` — 48 source URLs

| ID | URL | Doc set version | Date accessed | Covers |
|---|---|---|---|---|
| S1 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsphere.html | VCF 9.1 | 2026-07-31 | What's new in vSphere 9.1: ESX ZTP, ULM, memory tiering, guest customization APIs; vCenter Quick Patch, vmx-17, Query/Utilization/VGFA APIs, Resumable Consolidation; ESX naming |
| S2 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes.html | VCF 9.0 | 2026-07-31 | 9.0 release-notes index; 9.0.1 / 9.0.2 / patch / async release-note URLs |
| S3 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.0 | 2026-07-31 | VCF 9.0 Bill of Materials (versions + builds) |
| S4 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vsphere.html | VCF 9.0 | 2026-07-31 | What's new in vSphere 9.0: HW v22, SEV-SNP/TDX, NVMe boot, Memory Tiering, GPU reservations, vGPU precopy |
| S5 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/product-support-notes-vsphere.html | VCF 9.0 | 2026-07-31 | vSphere 9.0 deprecations and removals incl. vLCM baselines removal, blocked non-federated logins, Auto Deploy, Host Profiles, ELM, vCLS, Patch Manager APIs |
| S6 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vcf-cli-api-sdk.html | VCF 9.0 | 2026-07-31 | 9.0 API/SDK/CLI what's new: OpenAPI 3.0, authorization package, Java/Python SDK 9.0.0.0, VCF.PowerCLI rename |
| S7 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-product-support-notes/vcf-sdks-apis-and-clis-product-support-notes.html | VCF 9.0 | 2026-07-31 | 9.0 SDK deprecations/removals: vSAN Ruby/Perl/C#, Java SDK deprecation, pyVmomi removals, PowerCLI changes |
| S8 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/understanding-the-vsphere-automation-rest-api.html | VCF 9.0 | 2026-07-31 | `/api` base path, deprecated `/rest`, port 443 / 5480, HTTP verb conventions |
| S9 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms.html | VCF 9.1 | 2026-07-31 | Auth mechanisms: session id, SAML, JWT, OAuth 2.0, basic auth discouraged, IdP support matrix, child page URLs |
| S10 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/ | vSphere Automation API 9.1 (latest); selector lists 9.0 | 2026-07-31 | Reference landing page: version list, `/api` base path, service categories, `POST /api/cis/session` + `vmware-api-session-id` |
| S11 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/ and .../cis/cis-session/ | 9.1 (latest) | 2026-07-31 | CIS group: session POST/GET/DELETE, `/api/cis/tasks`, `/api/cis-tagging/{category,tag,tag-association}`, error types |
| S12 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/release-notes/vmware-cloud-foundation-90-release-notes/platform-whats-new/whats-new-vsan.html | VCF 9.0 | 2026-07-31 | What's new in vSAN 9.0 |
| S13 | https://developer.broadcom.com/xapis/vsan-management-api/latest/ | vSAN Management API 9.1 (latest); selector lists 9.0.0.0 | 2026-07-31 | vSAN API protocol (SOAP/vmodl), endpoints `/vsan`, `/vsanHealth`, `/sdk`, managed objects, version list |
| S14 | https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/9-0/managing-host-and-cluster-lifecycle/about-vsphere-lifecycle-manager-new/vlcm-baselines-and-images.html | vSphere 9.0 (standalone doc set) | 2026-07-31 | Baselines deprecated in vSphere 9.0; residual 8.x-only patching use; images are primary |
| S15 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/managing-the-lifecycle-of-hosts-and-clusters.html | VCF 9.0 | 2026-07-31 | vLCM automation workflow, host requirements, standalone-host firmware limitation, sub-topic list |
| S16 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vmware-cloud-foundation-bill-of-materials.html | VCF 9.1 | 2026-07-31 | VCF 9.1 Bill of Materials (versions + builds) |
| S17 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes.html | VCF 9.1 | 2026-07-31 | 9.1 release-notes landing page, child URLs, "12 MAY 2026" currency note |
| S18 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/understanding-the-vsphere-automation-rest-api.html | VCF 9.1 | 2026-07-31 | 9.1 confirmation of `/api` base path, deprecated `/rest`, ports 443/5480, verb conventions |
| S19 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools/introduction-to-the-vcf-programming-guide/introduction-to-the-vsphere-automation-rest-apis/authentication-mechanisms/authenticate-to-vcenter-server-with-vcenter-single-sign-on-credentials.html | VCF 9.1 | 2026-07-31 | ATTEMPTED — HTTP 403 from fetch proxy on 2 attempts; content not retrieved |
| S20 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-cli-api-sdk.html | VCF 9.1 | 2026-07-31 | 9.1 API/SDK/CLI what's new: Utilization API, VGFA, Query API, Java/Python SDK scope, VCF PowerCLI 9.1 cmdlets, Python 3.7/3.8 deprecation |
| S21 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/vcf-91-product-support-notes.html | VCF 9.1 | 2026-07-31 | 9.1 deprecations for ESX/vCenter; vSAN section = "None" |
| S22 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vsan.html | VCF 9.1 | 2026-07-31 | What's new in vSAN 9.1: Auto RAID 6, Global Dedup, compression, cross-vCenter stretched storage, site maintenance mode, cyber recovery, shared ESA+OSA, CNS scale |
| S23 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsan-deployment-administration-and-monitoring/vsan-planning-and-deployment.html | VCF 9.1 | 2026-07-31 | vSAN planning TOC (incl. "Creating a vSAN ESA Storage Cluster for Cyber Recovery"); no ESA/OSA default statement retrieved |
| S24 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/lifecycle-management.html | VCF 9.1 | 2026-07-31 | VCF 9.1 lifecycle model, software depot, VCF Operations manages ESX components and vLCM images, 5.2 upgrade prerequisite |
| S25 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment/upgrading-cloud-foundation/upgrade-the-management-domain-to-vmware-cloud-foundation-5-2/vlcm-baseline-to-vlcm-image-cluster-transition-.html | VCF 9.1 | 2026-07-31 | URL only (surfaced via search): "Transitioning from vSphere Lifecycle Manager Baselines to vSphere Lifecycle Manager Images" — page body not fetched |
| S26 | https://developer.broadcom.com/xapis/vsphere-automation-api/9.0/vcenter/vcenter-cluster/ | vSphere Automation API 9.0 | 2026-07-31 | Confirms version-pinned URL pattern renders; `GET /api/vcenter/cluster/`, `GET /api/vcenter/cluster/{cluster}` under 9.0 |
| S27 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-vm/ | 9.1 (latest) | 2026-07-31 | VM CRUD + clone/instant-clone/relocate/register/unregister paths, `vmw-task=true` |
| S28 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-vm-power/ | 9.1 (latest) | 2026-07-31 | VM power get/start/stop/suspend/reset |
| S29 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-datacenter/ | 9.1 (latest) | 2026-07-31 | Datacenter list/create/get/delete |
| S30 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-cluster/ | 9.1 (latest) | 2026-07-31 | Cluster list/get |
| S31 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/ | 9.1 (latest) | 2026-07-31 | vCenter service group index: datacenter, cluster, host, datastore, network, folder, resource-pool, vm, vm-template library items, guest customization, storage policies, datastore default policy, authorization {permissions,roles,privileges} |
| S32 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-host/ | 9.1 (latest) | 2026-07-31 | Host list/create/delete/connect/disconnect |
| S33 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-datastore/ and .../vcenter-network/ | 9.1 (latest) | 2026-07-31 | Datastore list/get; network list |
| S34 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vcenter/vcenter-storage-policies/ | 9.1 (latest) | 2026-07-31 | Storage policies list, check-compatibility, compliance, compliance/vm, policies/vm |
| S35 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/content/ | 9.1 (latest) | 2026-07-31 | Content library service groups and `/api/content/...` paths |
| S36 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/content/content-local-library/ | 9.1 (latest) | 2026-07-31 | Local library full operation table incl. force-delete and publish actions |
| S37 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/esx/ | 9.1 (latest) | 2026-07-31 | ESX Settings group index (names of vLCM sub-groups); path list returned was not reproducible on re-fetch |
| S38 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/esx/esx-settings-clusters-software/ and .../esx-settings-clusters-software-drafts/ | 9.1 (latest) | 2026-07-31 | ATTEMPTED — pages returned navigation only ("NONE VISIBLE"); vLCM endpoint tables not retrieved |
| S39 | https://developer.broadcom.com/xapis/virtual-infrastructure-json-api/latest/ | VI/JSON API 9.1 (latest); selector lists 9.0 | 2026-07-31 | VI/JSON base path `/sdk/vim25/{version}/{moType}/{moId}/{operation}`, examples, version list, relationship to SOAP |
| S40 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/cis-tagging-tag/ | 9.1 (latest) | 2026-07-31 | ATTEMPTED — navigation only; tag operation table not retrieved |
| S41 | https://developer.broadcom.com/xapis/vsphere-automation-api/latest/cis/cis-tagging-category/ | 9.1 (latest) | 2026-07-31 | ATTEMPTED — navigation only; category operation table not retrieved |
| S42 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/administration-sdks-cli-and-tools/what-is-the-vsphere-web-services-sdk/setup-for-development-with-openapi/openapi-specifications-for-vsphere.html | VCF 9.0 | 2026-07-31 | OpenAPI spec locations (`specifications/vsphere` folder, `wsdl` folder) and the three specs (VI/JSON, vCenter vAPI, vSAN data protection) |
| S43 | Search results on techdocs.broadcom.com for "vSphere Developer Center / API Explorer" (only 7.0 and 8.0 doc-set pages returned, e.g. https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/8-0/retrieve-apis-using-api-explorer.html) | vSphere 7.0 / 8.0 | 2026-07-31 | Evidence that no 9.x API Explorer doc page was findable |
| S44 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/vsphere-in-vcf.html | VCF 9.1 | 2026-07-31 | vSphere-in-VCF landing page; reference to the `_jcr_content.toc.html` TOC endpoint |
| S45 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/vsan-deployment-administration-and-monitoring/vsan-planning-and-deployment.html | VCF 9.0 | 2026-07-31 | vSAN 9.0 planning landing page; no ESA/OSA default or deprecation statement present |
| S46 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0.html and .../9-1.html | VCF 9.0 / 9.1 | 2026-07-31 | Top-level doc-set section maps and section URLs (vSphere in VCF, vSAN, SDKs/APIs/CLI) |
| S47 | https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere-sdks-tools/8-0/vmware-vsphere-automation-rest-programming-guide-8-0/introduction-to-the-vsphere-automation-rest-apis/vsphere-automation-api-base-path.html | vSphere SDKs & Tools **8.0** (NOT 9.x) | 2026-07-31 | Background only: "/rest base path has been deprecated and will be removed in a future release" since vSphere 7.0 U2. Used only as corroboration; 9.x claims rest on S8/S18 |
| S48 | https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/administration-sdks-cli-and-tools.html | VCF 9.1 | 2026-07-31 | 9.1 SDK/API/CLI section index and child URLs (programming guide, PowerCLI, Web Services SDK setup) |
