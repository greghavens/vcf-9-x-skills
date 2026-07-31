# Certificates and credentials — VCF 9.1

Scope: doing certificate lifecycle and password rotation as operations. Authentication to
the appliances themselves is not covered here — see `vcf-foundation`.

## Contents

- [Evidence tags](#evidence-tags)
- [Prerequisites](#prerequisites)
- [Which surface do I use?](#which-surface-do-i-use)
- [Surface A — VCF Operations fleet management (new in 9.1)](#surface-a--vcf-operations-fleet-management-new-in-91)
  - [Fleet Certificate Management](#fleet-certificate-management)
  - [Fleet Password Management](#fleet-password-management)
  - [Component (VVF) certificate and password management](#component-vvf-certificate-and-password-management)
  - [Collector, collector-group and agent certificate renewal](#collector-collector-group-and-agent-certificate-renewal)
  - [Tracking a WorkflowRequest](#tracking-a-workflowrequest)
  - [The identity broker is now under certificate management](#the-identity-broker-is-now-under-certificate-management)
- [Surface B — SDDC Manager (carried over from 9.0)](#surface-b--sddc-manager-carried-over-from-90)
  - [Certificate authority configuration](#certificate-authority-configuration)
  - [CSR generation](#csr-generation)
  - [Issue and install](#issue-and-install)
  - [Import an externally signed certificate](#import-an-externally-signed-certificate)
  - [Certificate inventory and auto-renewal](#certificate-inventory-and-auto-renewal)
  - [Trusted certificates](#trusted-certificates)
  - [Credentials and password rotation](#credentials-and-password-rotation)
  - [Password generation helpers](#password-generation-helpers)
- [Traps](#traps)
- [Known unknowns for 9.1](#known-unknowns-for-91)

## Evidence tags

- `[spec 9.1]` — VMware Cloud Foundation API Reference Guide,
  `sddc-manager-openapi.json`, `info.version` = `9.1.0.0` (git tag `9.1.0.0` of
  `vmware/vcf-api-specs`, cloned 2026-07-31). Operation IDs quoted verbatim.
- `[ops-spec 9.1]` — VMware Cloud Foundation Operations API,
  `vcf-operations-openapi.json`, `info.version` = `9.1.0.0`, base path `/suite-api`.
- `[lcm-spec 9.1]` — `fleet-lcm-openapi.yaml`, `info.version` = `9.1.0.0`.
- `[R-auth §3]` — `research/foundation-auth-identity.md` §3, citing Broadcom doc page S22
  (`/9-1/fleet-management/certificate-management-9-0.html`) and S57 (trusted-cert import).

Anything not carrying one of those tags and not marked UNVERIFIED is an error; report it.

---

## Prerequisites

Check these before writing any call. Each entry says what must be true, how to verify it,
and whether the same thing exists in 9.0.

| # | Must be true | How to verify | In 9.0? |
|---|---|---|---|
| 1 | You know **which of the two surfaces** the task belongs to — VCF Operations fleet management, or SDDC Manager. They are separate APIs, on separate hosts, with separate auth. | See [Which surface do I use?](#which-surface-do-i-use) | **No** — 9.0 has only the SDDC Manager surface |
| 2 | You are authenticated to the **right appliance**. VCF Operations accepts `Authorization: OpsToken <t>` and, in 9.1 only, `Authorization: Bearer <t>` from VCF SSO. SDDC Manager is excluded from VCF SSO and uses its own `/v1/tokens`. There is no one token for both. | `vcf-foundation`, `references/9.1/auth-and-identity.md` `[R-auth §1]` | Partly — the SSO Bearer option is 9.1-only |
| 3 | For SDDC Manager work: you have the **domain ID**. | `GET /v1/domains` → `getDomains` `[spec 9.1]` | Yes |
| 4 | For SDDC Manager issuance: a **CA is configured and CSRs exist**. The `generateCertificates` description states it verbatim: *"CA must be configured and CSR must be generated beforehand."* | `GET /v1/certificate-authorities` → `getCertificateAuthorities`; `GET /v1/domains/{id}/csrs` → `getCSRs` `[spec 9.1]` | Yes — identical |
| 5 | For fleet certificate work: a **fleet CA is configured**. Separate configuration from the SDDC Manager one. | `GET /api/fleet-management/certificate-management/certificate-authorities` → `getVcfCertificateAuthorities` `[ops-spec 9.1]` | **No** — endpoint does not exist in 9.0 |
| 6 | You have the **certificate ID**, which in the fleet API is opaque and must be looked up, not constructed. `VcfCertificate` exposes `certificateResourceKey`; `replaceCertificate` and `generateCsr` both key off `certificateId`. | `POST /api/fleet-management/certificate-management/certificates/query` → `getVcfCertificates` `[ops-spec 9.1]` | **No** |
| 7 | **No conflicting certificate operation is in flight.** `PUT /v1/domains/{id}/csrs`, `PUT /v1/domains/{id}/certificates` and `PATCH /v1/domains/{id}/certificates` all declare `409 Conflict`, labelled only `"Conflict"`. | Poll the previous `Task` to a terminal state. **The specific conflict condition is UNVERIFIED** — read `Error.message`. In 9.1 `Error` additionally carries `notifications[]` of `ValidationNotification` (`severity` INFO/ERROR/WARNING, `message`, `impactMessage`, `remediations[]` with `message` and `link`) — read those, they are the machine-readable remediation hints and they do not exist in 9.0. `[spec 9.1]` | Same 409s; **`notifications` is 9.1-only** |
| 8 | For credential work: the target component is **reachable and its current credential is valid**. `ExpirationDetails.connectivityStatus` example `ACTIVE, ERROR, UNKNOWN`; `status` example `ACTIVE, EXPIRING, EXPIRED, UNKNOWN`. | `GET /v1/credentials` → `getCredentials`, read `expiry`. In 9.1 `ExpirationDetails` gains **`connectivityErrorDetails`** (`ConnectivityErrorDetails`: `errorCode`, `arguments[]`, `errorMessage`, `remediationMessage`, `referenceToken`) — this is the field that tells you *why* it is unreachable rather than just that it is. `[spec 9.1]` | Field present, **`connectivityErrorDetails` is 9.1-only** |
| 9 | For credential work: **no in-flight credential task**, and no task sitting in `INCONSISTENT`. | `GET /v1/credentials/tasks` → `getCredentialsTasks` `[spec 9.1]`. **Whether SDDC Manager rejects a concurrent credential task is UNVERIFIED** — `PATCH /v1/credentials` declares no 409. | Yes — identical |
| 10 | For fleet password update: you know the **current password**. `VcfUpdatePasswordSpec` requires both `currentPassword` and `newPassword`. This is an update, not a system-generated rotate. | Nothing to call — you either have it or the operation is not available to you `[ops-spec 9.1]` | **No** |
| 11 | For trust-store work: the certificate is **PEM**. `TrustedCertificateSpec.certificate` is *"Certificate in PEM format"*. Broadcom's 9.1 trusted-certificate import page states PEM-only explicitly `[R-auth §3, S57]`. | Inspect the file | Schema identical; **the PEM-only doc statement is asserted for 9.1 only** — the 9.0 reference declines to carry it backwards |
| 12 | Password-expiration polling is **rate limited** — `POST /v1/credentials/expirations` declares `429`. No published limit. | Back off. Limit value **UNVERIFIED** `[spec 9.1]` | Yes — identical |
| 13 | The caller holds **whatever role certificate replacement and credential rotation require** — on both surfaces: `replaceCertificate` / `generateCsr` on the fleet API, and `PUT/PATCH /v1/domains/{id}/certificates`, `PUT /v1/domains/{id}/csrs`, `PATCH /v1/credentials` on SDDC Manager. **UNVERIFIED: the required role is not documented in any source consulted.** Neither the SDDC Manager 9.1 spec (no `securitySchemes`, no per-operation `security`) nor the VCF Operations 9.1 spec pins a role to an operation; the documented VCF Administrator / VCF Viewer / SDDC Administrator / SDDC Viewer scope hierarchy is itself marked unverified `[R-auth §2]`. An under-privileged service account fails here mid-change-window, not at login. | Nothing authoritative to call. Determine empirically against a non-production domain before delegating these credentials to automation — issue one certificate and rotate one credential end to end on each surface you intend to use and confirm both reach a terminal success. See [Known unknowns for 9.1](#known-unknowns-for-91). | Yes — same gap in 9.0 |

---

## Which surface do I use?

9.1 has two, and picking the wrong one is the most common way to waste a change window.

| Task | Surface | Why |
|---|---|---|
| Replace a cert on vCenter / NSX Manager / SDDC Manager / ESX inside a workload domain | Either. SDDC Manager `/v1/domains/{id}/...` is the mature path; the fleet API covers the same appliances | `VcfCertificateSearchRequest.appliance` enum includes `VCENTER, SDDC_MANAGER, NSXT_MANAGER, ESX` `[ops-spec 9.1]` |
| Replace a cert on **VCF Operations, VCF Automation, log management, VCF Operations for Networks, VCF Operations HCX, the identity broker, VCF services runtime, or the AVI load balancer** | **VCF Operations fleet API only** | Those appliance types appear only in the fleet enum. SDDC Manager's `Resource.type` does not name them `[spec 9.1]` vs `[ops-spec 9.1]` |
| Rotate a vCenter / ESX / NSX infrastructure password with a system-generated value | **SDDC Manager** `PATCH /v1/credentials` with `operationType: ROTATE` | The fleet password API takes an explicit `newPassword`; it does not generate one `[ops-spec 9.1]` |
| Update a fleet-component password where you already have both old and new | **VCF Operations fleet API** | `PUT /api/fleet-management/password-management/accounts/{passwordAccountKey}/password` |
| Add a CA to an appliance's trust store | Per-appliance. SDDC Manager: `POST /v1/sddc-manager/trusted-certificates`. VCF Operations: `POST /suite-api/api/certificate` (multipart) | Trust stores are not fleet-managed |
| Renew a cloud proxy / collector / agent certificate | **VCF Operations only**, and 9.1 only | `POST /api/collectors/{id}/certificates/renew` etc. |

---

## Surface A — VCF Operations fleet management (new in 9.1)

Base path `/suite-api`. All confirmed at `info.version` `9.1.0.0` `[ops-spec 9.1]`, and all
confirmed **absent** from the 9.0 spec by full path-set diff.

### Fleet Certificate Management

Tag: `Fleet Certificate Management`.

| Method | Path | operationId |
|---|---|---|
| GET | `/api/fleet-management/certificate-management/certificate-authorities` | `getVcfCertificateAuthorities` |
| PUT | `/api/fleet-management/certificate-management/certificate-authorities` | `configureVcfCertificateAuthorities` |
| POST | `/api/fleet-management/certificate-management/certificates/query` | `getVcfCertificates` |
| GET | `/api/fleet-management/certificate-management/certificates/{certificateId}` | `getVcfCertificate` |
| PUT | `/api/fleet-management/certificate-management/certificates/{certificateId}` | `replaceCertificate` |
| GET | `/api/fleet-management/certificate-management/csrs` | `fetchCSRs` |
| POST | `/api/fleet-management/certificate-management/csrs` | `generateCsr` |

**Query certificates.** `POST .../certificates/query` is a POST because the filter is a
body, not because it changes anything. Query parameters: `page`, `pageSize`, `sortBy`,
`sortOrder`. Body `VcfCertificateSearchRequest` — all fields optional, all real enums:

- `appliance`: `VCENTER, SDDC_MANAGER, NSXT_MANAGER, VCF_AUTOMATION, LOG_MANAGEMENT,
  VCF_OPERATIONS, VCF_OPS_NETWORK, IDENTITY_BROKER, VCF_OPS_HCX, ESX,
  VCF_SERVICES_RUNTIME, AVI_LOAD_BALANCER, UNKNOWN`
- `applianceFqdn`: string
- `category`: `TLS_CERT, ROOT_CERT, INTERMEDIATE_CERT, UNKNOWN`
- `status`: `EXPIRED, EXPIRING_30, EXPIRING_60, NORMAL, UNKNOWN`
- `type`: `VMCA, OPENSSL_CA, MSCA, EXTERNAL_CA, UNKNOWN`

`status: "EXPIRING_30"` with no other filter is the one call that answers "what breaks
next month" across the whole fleet. That question has no single-call answer in 9.0.

Response `VcfCertificatesResponse`: `vcfCertificateModels[]`, `pageInfo`
(`page, pageSize, sortBy, sortOrder, totalCount`), `links[]`.

`VcfCertificate` (from `getVcfCertificate`) carries `certificateResourceKey`, `appliance`,
`applianceIp`, `domainId`, `issuedBy`, `issuedTo`, `issuedToCommonName`, `expiryDate`
(integer), `daysToExpire`, `status`, `type`, `category`, `subjectAlternativeNames`
(`dns[]`, `ip[]`), `vcfComponent`, `vcfEndpoint`, and an `autoRenewInfo`
(`AutoRenewInfoGroup`: `autoRenewStatus`, `autoRenewOperationStatus`,
`autoRenewFailureReason`).

**Configure the fleet CA.** `PUT .../certificate-authorities`, body `VcfConfigureCASpec`:

```json
{
  "certificateAuthorityType": "OPENSSL",
  "certificateAuthoritiesSpec": {
    "openSSLCertificateAuthoritySpec": {
      "commonName": "OpenSSL CA", "country": "IN", "state": "Karnataka",
      "locality": "Bengaluru", "organization": "VMware Inc.", "organizationUnit": "VCF"
    }
  },
  "vcfComponentSpec": {
    "vcfComponentType": "SDDC",
    "vcfDomainId": "...", "vcfDomainName": "...", "vcfHostName": "..."
  }
}
```

`certificateAuthorityType`: `MICROSOFT, OPENSSL`. `vcfComponentType`: `ARIA, SDDC,
STANDALONE_VC`. Note `ARIA` — a legacy name still in the 9.1 enum.

**Generate a CSR.** `POST .../csrs`, body `GenerateCsrData` (`certificateId` and
`generateCsrSpec` both required):

```json
{
  "certificateId": "<certificateResourceKey from the query>",
  "generateCsrSpec": {
    "commonName": "vcfops01.rainpole.io",
    "organization": "VMware Inc.", "orgUnit": "VCF",
    "keySize": "KEY_2048",
    "country": "IN", "state": "Karnataka", "locality": "Bengaluru",
    "email": "admin@vmware.com", "keyAlgorithm": "RSA",
    "subjectAltNames": { "dns": ["vcfops01.rainpole.io"], "ip": [] }
  }
}
```

Required inside `GenerateCsrSpec`: `keySize`, `orgUnit`, `organization`. `keySize` is a
real enum: `UNKNOWN, KEY_2048, KEY_3072, KEY_4096` — **note the `KEY_` prefix**, which is
different from SDDC Manager's bare `"2048"` string. Sending `"2048"` here will fail
validation. The operation also accepts `application/xml`.

Returns `WorkflowRequest` (200 or 202). `fetchCSRs` lists them, with query parameters
`commonName`, `applianceType`, `applianceFqdn`, `page`, `pageSize`.

**Replace a certificate.** `PUT .../certificates/{certificateId}`, body
`CertificateReplaceData`, `caType` required:

```json
{ "caType": "EXTERNAL_CA", "certificateChain": "-----BEGIN CERTIFICATE-----\n...\n" }
```

`caType`: `VMCA, OPENSSL_CA, MSCA, EXTERNAL_CA, UNKNOWN`. Returns `202` +
`WorkflowRequest`.

### Fleet Password Management

Tag: `Fleet Password Management`.

| Method | Path | operationId |
|---|---|---|
| POST | `/api/fleet-management/password-management/accounts/query` | `getVcfPasswordAccounts` |
| PUT | `/api/fleet-management/password-management/accounts/{passwordAccountKey}/password` | `updatePassword` |

Query body `VcfPasswordAccountSearchRequest`: `appliance` (`VCENTER, SDDC_MANAGER,
NSXT_MANAGER, NSXT_EDGE, VCF_AUTOMATION, LOG_MANAGEMENT, VCF_OPERATIONS, VCF_OPS_NETWORK,
IDENTITY_BROKER, VCF_OPS_HCX, ESX, VCF_SERVICES_RUNTIME, AVI_LOAD_BALANCER, UNKNOWN`),
`applianceFqdn`, `username`, `vcfDomainId`, `status` (`ACTIVE, EXPIRING, EXPIRED,
UNKNOWN`). Query parameters `page`, `pageSize`, `sortBy`, `sortOrder`.

Update body `VcfUpdatePasswordSpec` — **`currentPassword` and `newPassword` both
required**, `userName` optional:

```json
{ "currentPassword": "...", "newPassword": "...", "userName": "root" }
```

Returns `WorkflowRequest`. This surface has **no rotate-with-generated-password mode** and
no auto-rotate policy. If you want SDDC Manager to invent the password, use
`PATCH /v1/credentials` with `operationType: ROTATE` on Surface B, or generate one first
(see [Password generation helpers](#password-generation-helpers)).

### Component (VVF) certificate and password management

Tags: `Component Certificate Management`, `Component Password Management`. Keyed by
`serviceKey`, not by domain or certificate ID. `GET /api/integrations/services` (also new
in 9.1) returns registered services.

| Method | Path | operationId |
|---|---|---|
| GET | `/api/integrations/services/certificate-management/{serviceKey}/certificates` | `getVVFCertificates` |
| PUT | `/api/integrations/services/certificate-management/{serviceKey}/certificates` | `replaceVVFCertificate` |
| GET | `/api/integrations/services/certificate-management/{serviceKey}/csrs` | `getVVFCsrs` |
| POST | `/api/integrations/services/certificate-management/{serviceKey}/csrs` | `generateVVFCsr` |
| GET | `/api/integrations/services/password-management/{serviceKey}/accounts` | `getVVFAccountList` |
| PUT | `/api/integrations/services/password-management/{serviceKey}/accounts/password` | `updatePasswordSystem` |
| GET | `/api/integrations/services/password-management/{serviceKey}/tasks/{taskId}` | `getVvfTaskStatus` |

`replaceVVFCertificate` body `VvfCertificateReplacementSpec`: `certificateFullChain`,
`ingressType`. `generateVVFCsr` body is a bare `GenerateCsrSpec` (same `KEY_2048` enum
as the fleet CSR). `updatePasswordSystem` body `VvfChangePasswordSpec`:
`currentPassword` and `newPassword` required, `userName` optional.

These return `VvfTaskStatusResponse`, **not** `WorkflowRequest`, with `status` enum
`SUCCEEDED, PENDING, QUEUED, RUNNING, CANCELLED, ERROR, UNKNOWN, FAILED`. Poll them with
`getVvfTaskStatus` — the workflow-request endpoint will not find them.

### Collector, collector-group and agent certificate renewal

Tags: `Applications`, `Collectors`, `Collector Groups`. All 9.1-only.

| Method | Path | operationId |
|---|---|---|
| POST | `/api/applications/agents/certificates/renew` | `renewClientsCertificate` |
| POST | `/api/applications/agents/certificates/renew/status` | `getRenewClientsCertificateStatus` |
| POST | `/api/applications/agents/{id}/certificates/renew` | `renewClientCertificate` |
| GET | `/api/applications/agents/{id}/certificates/renew/status` | `getRenewClientCertificateStatus` |
| POST | `/api/collectorgroups/{id}/certificates/renew` | `renewCollectorGroupCertificate` |
| GET | `/api/collectorgroups/{id}/certificates/renew/status` | `getCollectorGroupCertificateRenewalStatus` |
| POST | `/api/collectors/{id}/certificates/renew` | `renewCloudProxyCertificate` |
| GET | `/api/collectors/{id}/certificates/renew/status` | `getCollectorCertificateRenewStatus` |

The two CA-renewal operations carry Broadcom's own warning in the operation description,
verbatim: *"Communication between Endpoint - Cloud Proxy will be broken post Renewal of CA
Certificate. Will attempt to renew Client Certificate on Endpoint."* Read "will attempt"
literally — endpoints that miss the follow-up need
`POST /api/applications/agents/{id}/certificates/renew` individually.

`renewClientsCertificate` and `getRenewClientsCertificateStatus` take
`{"contextResourceIDs": ["..."]}` and act on a set — that is the closest thing to a bulk
operation in the certificate family.

### Tracking a WorkflowRequest

`GET /api/workflows/requests/{requestId}` → `getRequestById`, tag `Workflow Request`.
**9.1 only** — absent from the 9.0 path set `[ops-spec 9.0 vs 9.1]`.

`WorkflowRequest`: `requestId`, `requestName` (required), `requestType` (required),
`category` (required), `state`, `duration`, `requestReason`, `errorCause[]`.

`category` enum: `INVENTORY, PASSWORD, CERTIFICATE, LCM_MIGRATION,
VCF_PASSWORD_MANAGEMENT, VCF_CERTIFICATE_MANAGEMENT, SERVICE_REGISTRY_ROTATION,
SOLUTIONS_CATALOG, SALT_RAAS_CONFIGURATION, VIDB_MIGRATION, VCF_IAM`.

Three async result types now coexist in 9.1 and they are not interchangeable:

| Surface | Returns | Poll with |
|---|---|---|
| VCF Operations fleet cert/password | `WorkflowRequest` | `GET /api/workflows/requests/{requestId}` |
| VCF Operations component (VVF) | `VvfTaskStatusResponse` | `GET /api/integrations/services/password-management/{serviceKey}/tasks/{taskId}` |
| SDDC Manager certificates | `Task` | `GET /v1/tasks/{id}` |
| SDDC Manager credentials | `CredentialsTask` | `GET /v1/credentials/tasks/{id}` |

### The identity broker is now under certificate management

`IDENTITY_BROKER` is a value in **both** the 9.1 fleet certificate `appliance` enum and
the 9.1 fleet password `appliance` enum `[ops-spec 9.1]`. Broadcom's 9.1 certificate
management page independently lists the identity broker in the VCF Management tier of
covered components `[R-auth §3, S22]`.

The consequence, and it is the single most important operational fact in this file: **the
identity broker is the VCF SSO token issuer.** Every SSO-federated client — vCenter, VCF
Operations, VCF Automation, NSX, log management, VCF Operations for Networks, the
orchestrator, HCX `[R-auth §1]` — trusts it. A broker certificate replacement is therefore
a single TLS point of failure for the entire fleet's authentication, in a way 9.0's
per-product auth was not.

The research dossier flags the "breaks every SSO client at once" consequence as an
**inference** drawn from the cited component list, not as a documented Broadcom statement
`[R-auth §3, pitfall 5]`. The component coverage is documented; the blast radius is
reasoning. Present it that way. Plan a broker certificate replacement with a
tested out-of-band route back in — in 9.1 the Emergency Access Client is the documented
break-glass mechanism, described as providing *"high-privilege and long-lived access
tokens to critical systems when standard methods fail"* `[R-auth §1, S51]`.

---

## Surface B — SDDC Manager (carried over from 9.0)

All 31 operations under the `Certificates`, `Trusted Certificates` and `Credentials` tags
exist in 9.1 with **identical paths, methods and operationIds** to 9.0 `[spec 9.0 vs
9.1]`. What follows records the 9.1 details; see `references/deltas.md` for the field-level
differences.

### Certificate authority configuration

| Method | Path | operationId |
|---|---|---|
| GET | `/v1/certificate-authorities` | `getCertificateAuthorities` |
| GET | `/v1/certificate-authorities/{id}` | `getCertificateAuthorityById` |
| PUT | `/v1/certificate-authorities` | `createCertificateAuthority` |
| PATCH | `/v1/certificate-authorities` | `configureCertificateAuthority` |
| DELETE | `/v1/certificate-authorities/{id}` | `removeCertificateAuthority` |

`{id}` is *"The CA type"*, not a UUID. Body for PUT/PATCH is
`CertificateAuthorityCreationSpec`, containing exactly one of
`openSSLCertificateAuthoritySpec` (requires `commonName`, `country`, `state`, `locality`,
`organization`, `organizationUnit`) or `microsoftCertificateAuthoritySpec` (requires
`username`, `secret`, `serverUrl`, `templateName`). Schemas are byte-identical to 9.0.

### CSR generation

| Method | Path | operationId | Notes |
|---|---|---|---|
| PUT | `/v1/domains/{id}/csrs` | `generatesCSRs` | 202 → `Task`; 409 possible |
| GET | `/v1/domains/{id}/csrs` | `getCSRs` | |
| GET | `/v1/domains/{id}/csrs/downloads` | `downloadCSR` | **still `deprecated: true`** in 9.1 |

Body `CsrsGenerationSpec` — `csrGenerationSpec` required, `resources[]` optional:

```json
{
  "csrGenerationSpec": {
    "country": "IN", "state": "Karnataka", "locality": "Bengaluru",
    "organization": "VMware Inc.", "organizationUnit": "VCF",
    "email": "admin@vmware.com", "keySize": "2048", "keyAlgorithm": "RSA"
  },
  "resources": [
    { "resourceId": "BE8A5E04-92A0-43F6-A166-AA041F4327CC", "type": "VCENTER",
      "fqdn": "sfo-vc01.rainpole.io", "sans": ["sfo-vc01.rainpole.io"] }
  ]
}
```

`keySize` here is a bare string `"2048"` — **not** the fleet API's `KEY_2048`.

`Resource.type` example in 9.1: `SDDC_MANAGER, PSC, VCENTER, NSXT_MANAGER, NSX_ALB, ESXI,
HCX_MANAGER, VSP`. Compared with 9.0: **`VXRAIL_MANAGER` removed, `HCX_MANAGER` and `VSP`
added.** A 9.0 script that passes `VXRAIL_MANAGER` is passing a value 9.1 no longer
documents. (These are `example` strings on a `string`-typed field, not enums — the spec
does not enforce them, so a stale value may be accepted and then fail downstream.)

Same verbatim warning as 9.0 against wildcard certificates.

### Issue and install

| Method | Path | operationId |
|---|---|---|
| PUT | `/v1/domains/{id}/certificates` | `generateCertificates` |
| GET | `/v1/domains/{id}/certificates` | `getDomainCertificates` |
| PATCH | `/v1/domains/{id}/certificates` | `replaceCertificates` |

`CertificatesGenerationSpec` requires `caType` (`One among: OpenSSL, Microsoft, VMCA`),
optional `resources[]` and `validity` (int32 days, example 398).
`CertificateOperationSpec` requires `operationType` (`One among: INSTALL`), optional
`resources[]`. Both unchanged from 9.0.

### Import an externally signed certificate

| Method | Path | operationId |
|---|---|---|
| PUT | `/v1/domains/{id}/resource-certificates/validations` | `validateResourceCertificates` |
| GET | `/v1/domains/{id}/resource-certificates/validations/{validationId}` | `getResourceCertificatesValidationByID` |
| PUT | `/v1/domains/{id}/resource-certificates` | `replaceResourceCertificates` |

Both PUTs take an **array** of `ResourceCertificateSpec`. Description constrains it:
*"Either resourceId or resourceFqdn should be provided. Either certificateChain or both
resourceCertificate and caCertificate should be provided."* Validate first, then replace.

### Certificate inventory and auto-renewal

| Method | Path | operationId | Notes |
|---|---|---|---|
| GET | `/v1/domains/{id}/resource-certificates` | `getCertificatesByDomain` | **9.1 adds three query parameters absent in 9.0**: `excludeResourceType` (*"exclude a specific resource type from the API response"*), `pageNumber`, `pageSize`. Response type is `PageOfCertificate` in both versions — 9.0 simply had no way to drive the paging. |
| PATCH | `/v1/domains/{id}/resource-certificates` | `setAutoRenewConfigurationForDomain` | `{"autoRenew": "ENABLE"}` |
| PATCH | `/v1/domains/resource-certificates` | `setAutoRenewConfiguration` | Adds optional `autoRenewTriggerTimeWindow`, `HH:mm` 24-hour |

Auto-renewal triggers *"at the specified time or up to an hour later, considering factors
such as daylight saving time"* — the field description says so. Do not build a change
freeze around an exact minute.

`Certificate.resourceType` example in 9.1: `SDDC_MANAGER, PSC, VCENTER, NSXT_MANAGER,
NSX_ALB, ESXI, HCX_MANAGER, VSP` — same drop of `VXRAIL_MANAGER`, same additions.

### Trusted certificates

| Method | Path | operationId | Notes |
|---|---|---|---|
| GET | `/v1/sddc-manager/trusted-certificates` | `getTrustedCertificates` | |
| POST | `/v1/sddc-manager/trusted-certificates` | `addTrustedCertificate` | 409 = *"Trusted certificate already exists"* |
| DELETE | `/v1/sddc-manager/trusted-certificates/{alias}` | `deleteTrustedCertificate` | 204 |

Body `TrustedCertificateSpec`: `certificate` (PEM) required; `certificateUsageType`
(`TRUSTED_FOR_OUTBOUND, TRUSTED_FOR_INBOUND`) is **`deprecated: true`** — do not send it.
Alias shape is `vcf_<thumbprint>`.

The same three operations, same paths and operationIds, also exist in the **VCF Installer**
API at 9.1 `[spec 9.1, vcf-installer-openapi.json]`.

For the VCF Operations appliance's own trust store, use
`POST /suite-api/api/certificate` (`importCertificate`, `multipart/form-data`),
`GET /suite-api/api/certificate` (`getAllCertificates`), `DELETE /suite-api/api/certificate`
(`deleteCertificate`, query `thumbprint` required, `force` optional). Present in both
versions, unchanged `[ops-spec 9.0 vs 9.1]`. Broadcom's 9.1 page states imports must be
PEM `[R-auth §3, S57]` and does not state which OS/JVM trust store is modified.

### Credentials and password rotation

| Method | Path | operationId |
|---|---|---|
| GET | `/v1/credentials` | `getCredentials` |
| GET | `/v1/credentials/{id}` | `getCredential` |
| PATCH | `/v1/credentials` | `updateOrRotatePasswords` |
| POST | `/v1/credentials/expirations` | `getPasswordExpiration` |
| GET | `/v1/credentials/expirations/{id}` | `getPasswordExpirationByTaskID` |
| GET | `/v1/credentials/tasks` | `getCredentialsTasks` |
| GET | `/v1/credentials/tasks/{id}` | `getCredentialsTask` |
| PATCH | `/v1/credentials/tasks/{id}` | `retryCredentialsTask` |
| DELETE | `/v1/credentials/tasks/{id}` | `cancelCredentialsTask` |
| GET | `/v1/credentials/tasks/{id}/subtasks/{subtaskId}` | `getCredentialsSubTask` |
| GET | `/v1/credentials/tasks/{id}/resource-credentials` | `getCredentialTaskByResourceID` |

`getCredentials` query parameters: `resourceName`, `resourceIp`, `resourceType`,
`domainName`, `pageNumber`, `pageSize`, `accountType`. The `resourceType` parameter
description in 9.1 reads `ESXI, VCENTER, PSC, NSXT_MANAGER, NSXT_EDGE, NSX_ALB, BACKUP,
HCX_MANAGER, VSP` — **`HCX_MANAGER` and `VSP` are the 9.1 additions**; nothing was removed.

`Credential` schema is byte-identical to 9.0: `id`, `credentialType` (`SSO, SSH, API, FTP,
AUDIT`), `accountType` (`USER, SYSTEM, SERVICE`), `username`, **`password`**,
`creationTimestamp`, `modificationTimestamp`, `expiry`, `resource`, `autoRotatePolicy`.

**`password` is readable on this response in both versions.** Role scoping matters more
here than almost anywhere else in the API. In 9.1 you have a fleet role model to scope it
with — VCF Administrator / VCF Viewer / SDDC Administrator / SDDC Viewer, documented only
in the 9.1 doc set `[R-auth §2]` — but see the "required role per operation" gap below.

Body of `updateOrRotatePasswords`, `CredentialsUpdateSpec` (`operationType` and `elements`
required):

```json
{
  "operationType": "ROTATE",
  "elements": [
    { "resourceName": "sfo-vc01.rainpole.io", "resourceType": "VCENTER",
      "credentials": [ { "credentialType": "SSH", "username": "root" } ] }
  ]
}
```

`operationType`: `UPDATE, ROTATE, REMEDIATE, UPDATE_AUTO_ROTATE_POLICY`.

- **ROTATE** — SDDC Manager generates the password. Omit `password`.
- **UPDATE** — supply `password` per `BaseCredential`.
- **REMEDIATE** — named in the enum; **mechanics UNVERIFIED**, no fetched source describes
  them.
- **UPDATE_AUTO_ROTATE_POLICY** — pair with `autoRotatePolicy`
  (`AutoRotateCredentialPolicyInputSpec`: `enableAutoRotatePolicy` required boolean,
  `frequencyInDays` int32).

`CredentialsTask.status`: `PENDING, IN_PROGRESS, SUCCESSFUL, FAILED, USER_CANCELLED,
INCONSISTENT`. `isAutoRotate` distinguishes scheduled from manual.

**`INCONSISTENT` is the status that matters.** `CredentialsSubTask` exposes `oldPassword`
and `newPassword` per subtask — that pair is your recovery information when a rotation
half-completes and the appliance now holds a password SDDC Manager does not think it has.
Read the subtasks before you retry. Both `retryCredentialsTask` and `cancelCredentialsTask`
are described as operating on a **failed** task; neither is documented as a way to stop a
running one.

`getPasswordExpiration` body `CredentialsExpirationSpec`, `resourceType` required:
`{"resourceType": "VCENTER", "domainName": "sfo-m01", "credentialIds": ["<uuid>"]}`.
Asynchronous (202), rate limited (429).

### Password generation helpers

Two, both 9.1-only, both returning a password rather than applying one:

| Method | Path | operationId | Source | Response |
|---|---|---|---|---|
| POST | `/v1/vcf-management-components/passwords` | `generatePassword` | SDDC Manager, tag `VCF Management Components` `[spec 9.1]` | bare JSON `string`; responses 200/403/500. **No request body.** Summary: *"Generates a password that will be valid for all components."* |
| POST | `/v1/components/generated-passwords` | `generatePassword` | Fleet LCM `[lcm-spec 9.1]`, tag `Components` | `GeneratedPasswordResponse` `{"generatedPassword": "..."}`; responses 200/401/500. Description: *"Generates a password meeting the password complexity requirements for all components."* |

Neither exists in 9.0 — the `fleet-lcm` spec itself is new in 9.1, and
`/v1/vcf-management-components/passwords` is in the 9.1 added-operations set for SDDC
Manager `[spec 9.0 vs 9.1]`.

Use these to satisfy `newPassword` on the fleet password API, which requires an explicit
value and will not invent one for you.

---

## Traps

1. **`KEY_2048` vs `"2048"`.** The fleet CSR API uses an enum with a `KEY_` prefix; SDDC
   Manager uses a bare numeric string. One script cannot use the same constant for both.
2. **VCF Operations `/api/credentials` is not password rotation.** It manages monitoring
   adapter credential instances — `adapterKindKey`, `credentialKindKey`, `fields` — in
   both versions `[ops-spec 9.0 vs 9.1]`. Rotating a vCenter root password is
   `PATCH /v1/credentials` on SDDC Manager.
3. **Four different async result types.** See the table in
   [Tracking a WorkflowRequest](#tracking-a-workflowrequest). Polling a `WorkflowRequest`
   ID against `/v1/tasks/{id}` will 404 and tell you nothing useful.
4. **`replaceResourceCertificates` and `validateResourceCertificates` take a bare JSON
   array**, not a wrapped object. Easy to get wrong from the operation name alone.
5. **`VXRAIL_MANAGER` is gone from the 9.1 resource-type examples.** Carried-over 9.0
   automation may still send it.
6. **The fleet password API cannot generate a password.** It requires
   `currentPassword` and `newPassword`. Combine with a generator endpoint or use SDDC
   Manager's `ROTATE`.

---

## Known unknowns for 9.1

- **Required role per operation is UNVERIFIED.** Neither the SDDC Manager 9.1 spec (no
  `securitySchemes`, no per-operation `security`) nor the VCF Operations 9.1 spec pins a
  role to an operation. The 9.1 doc set documents VCF Administrator / VCF Viewer / SDDC
  Administrator / SDDC Viewer with component mappings, but the scope hierarchy is itself
  marked unverified in the research `[R-auth §2]`. Determine empirically.
- **The 409 conflict condition on the SDDC Manager certificate operations is
  UNVERIFIED.**
- **`REMEDIATE` semantics are UNVERIFIED.**
- **The 429 rate limit on `getPasswordExpiration` is UNVERIFIED** — no number published.
- **Whether certificate replacement invalidates live tokens is UNVERIFIED.** Flagged as
  inference in the research `[R-auth §3, pitfall 4]`. Behave as if it does.
- **Which trust store `addTrustedCertificate` / `importCertificate` writes to is
  UNVERIFIED** `[R-auth §3, S57]`.
- **Whether the fleet certificate API and the SDDC Manager certificate API write to the
  same underlying state is UNVERIFIED.** Both cover `VCENTER`, `SDDC_MANAGER`,
  `NSXT_MANAGER` and `ESX`. No fetched source says what happens if you drive the same
  appliance from both, or whether one supersedes the other. Pick one surface per appliance
  and stay on it.
- **`VSP` is not expanded anywhere in the specs.** It appears as a resource-type example
  value in 9.1 with no definition in any fetched source.
- **Bulk certificate operations.** Broadcom's 9.1 page says verbatim: *"Starting with VCF
  Operations 9.1, you can generate certificate signing requests, renew, import, and replace
  multiple certificates simultaneously"* `[R-auth §3, S22]`. In the 9.1 OpenAPI the fleet
  certificate operations are **single-certificate**: `replaceCertificate` and `generateCsr`
  each take one `certificateId`. The only multi-target certificate operations in the spec
  are `renewClientsCertificate` / `getRenewClientsCertificateStatus`, which take a
  `contextResourceIDs[]` array for agent certificates. Either the documented bulk
  capability is UI-only, or it is exposed by an endpoint not present in this spec.
  **Unresolved — do not promise a bulk REST call.** If a user needs it, say the doc claims
  it, the spec does not carry it, and point them at the VCF Operations UI.
