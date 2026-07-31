# Certificates and credentials — VCF 9.0

Scope: doing certificate lifecycle and password rotation as operations. Authentication to
the appliances themselves is not covered here — see `vcf-foundation`.

## Contents

- [Evidence tags](#evidence-tags)
- [Prerequisites](#prerequisites)
- [The two API surfaces in 9.0](#the-two-api-surfaces-in-90)
  - [Trap: VCF Operations `/api/credentials` is not password rotation](#trap-vcf-operations-apicredentials-is-not-password-rotation)
- [Certificates — SDDC Manager, 9.0](#certificates--sddc-manager-90)
  - [Certificate authority configuration](#certificate-authority-configuration)
  - [CSR generation](#csr-generation)
  - [Issue and install (CA-signed, via configured CA)](#issue-and-install-ca-signed-via-configured-ca)
  - [Import an externally signed certificate](#import-an-externally-signed-certificate)
  - [Certificate inventory and auto-renewal](#certificate-inventory-and-auto-renewal)
  - [Trusted certificates (SDDC Manager's own trust store)](#trusted-certificates-sddc-managers-own-trust-store)
- [Credentials and password rotation — SDDC Manager, 9.0](#credentials-and-password-rotation--sddc-manager-90)
  - [Lookup](#lookup)
  - [Rotate, update, remediate](#rotate-update-remediate)
  - [Track, retry, cancel](#track-retry-cancel)
  - [Expiration checking](#expiration-checking)
- [What is absent in 9.0](#what-is-absent-in-90)
- [Known unknowns for 9.0](#known-unknowns-for-90)

## Evidence tags

- `[spec 9.0]` — VMware Cloud Foundation API Reference Guide, `sddc-manager-openapi.json`,
  `info.version` = `9.0.0.0` (git tag `9.0.0.0` of `vmware/vcf-api-specs`, cloned 2026-07-31).
  Operation IDs are quoted verbatim from that file.
- `[ops-spec 9.0]` — VMware Cloud Foundation Operations API, `vcf-operations-openapi.json`
  at the same tag. Note: this file carries an **empty** `info.version` string; it is
  identified as 9.0 only by the git tag it sits under.
- `[R-auth §3]` — `research/foundation-auth-identity.md` §3 Certificate Management, which
  cites Broadcom doc page S21 (`/9-0/fleet-management/certificate-management-9-0.html`).

Anything not carrying one of those tags and not marked UNVERIFIED is an error; report it.

---

## Prerequisites

Check these before writing any call. Each entry says what must be true, how to verify it,
and whether the same thing exists in 9.1.

| # | Must be true | How to verify | In 9.1? |
|---|---|---|---|
| 1 | You are authenticated to **SDDC Manager specifically**. SDDC Manager is excluded from VCF SSO; it has its own `/v1/tokens` flow. A fleet token does not open it. | `vcf-foundation`, `references/9.0/auth-and-identity.md`. `[R-auth §1]` | Yes — same exclusion |
| 2 | You have the **domain ID**. Every certificate operation except CA config and the trust store is scoped to a domain. | `GET /v1/domains` → `getDomains` `[spec 9.0]`. The path parameter accepts "Domain ID or Name" per the parameter description on `getCSRs`. `[spec 9.0]` | Yes — identical |
| 3 | A **Certificate Authority is configured** — required before you can have SDDC Manager issue certificates. The `generateCertificates` description states it verbatim: *"CA must be configured and CSR must be generated beforehand."* | `GET /v1/certificate-authorities` → `getCertificateAuthorities` `[spec 9.0]`. Empty result means step 3 of the issue sequence will fail. | Yes — identical |
| 4 | **CSRs exist for the resources you are about to issue for.** Same sentence as above. | `GET /v1/domains/{id}/csrs` → `getCSRs` `[spec 9.0]` | Yes — identical |
| 5 | **No conflicting certificate operation is in flight.** `PUT /v1/domains/{id}/csrs`, `PUT /v1/domains/{id}/certificates` and `PATCH /v1/domains/{id}/certificates` all declare a `409 Conflict` response. The spec labels it only `"Conflict"` and does not say what conflicts. | Poll the task returned by the previous certificate call to a terminal state before starting the next one — `GET /v1/tasks/{id}`. **The specific conflict condition is UNVERIFIED** — treat 409 as "something else is running or already exists" and read the `Error.message`. | Yes — identical response set |
| 6 | For credential work: the target component is **reachable and its current credential is valid**. `ExpirationDetails` carries `connectivityStatus` with example values `ACTIVE, ERROR, UNKNOWN` and `status` with `ACTIVE, EXPIRING, EXPIRED, UNKNOWN`. A credential whose `connectivityStatus` is `ERROR` will not rotate. | `GET /v1/credentials` → `getCredentials`, read `expiry.connectivityStatus` per credential; or `POST /v1/credentials/expirations` → `getPasswordExpiration` for a batch check. `[spec 9.0]` | Yes, and 9.1 adds `connectivityErrorDetails` to the same object |
| 7 | For credential work: **no in-flight credential task**. Credential operations are asynchronous (`202 Accepted` → `CredentialsTask`) and a task can sit in `PENDING`/`IN_PROGRESS`, or in `INCONSISTENT` after a partial failure. | `GET /v1/credentials/tasks` → `getCredentialsTasks` `[spec 9.0]`. Terminal-ish statuses per `CredentialsTask.status` example: `PENDING, IN_PROGRESS, SUCCESSFUL, FAILED, USER_CANCELLED, INCONSISTENT`. **Whether SDDC Manager itself rejects a second concurrent credential task is UNVERIFIED** — `PATCH /v1/credentials` declares no `409`. | Yes — identical |
| 8 | For trust-store work: the certificate is **PEM**. `TrustedCertificateSpec.certificate` is described as *"Certificate in PEM format"* with a `-----BEGIN CERTIFICATE-----` example. | Inspect the file. DER/PKCS#7 must be converted first. `[spec 9.0]` | Yes — identical |
| 9 | Password-expiration polling is **rate limited**. `POST /v1/credentials/expirations` declares a `429 Too many requests`. No published limit. | Back off on 429. Limit value is **UNVERIFIED**. `[spec 9.0]` | Yes — identical |
| 10 | The caller holds **whatever role certificate replacement and credential rotation require** — the writes: `PUT/PATCH /v1/domains/{id}/certificates`, `PUT /v1/domains/{id}/csrs`, `PATCH /v1/credentials`, and the trust-store mutators. **UNVERIFIED: the required role is not documented in any source consulted.** The 9.0 SDDC Manager spec declares no `securitySchemes` and no per-operation `security`, and 9.0 has no fleet-level VCF role model to appeal to `[R-auth §2]`. An under-privileged service account fails here mid-change-window, not at login. | Nothing authoritative to call. Determine empirically against a non-production domain before delegating these credentials to automation — issue one certificate and rotate one credential end to end and confirm both reach a terminal success. See "Known unknowns" below. | Yes — same gap in 9.1 |

**Not a prerequisite in 9.0, because it does not exist:** there is no fleet-wide
certificate or password API in VCF Operations 9.0. See "What is absent in 9.0" below.

---

## The two API surfaces in 9.0

1. **SDDC Manager `/v1/*`** — the certificate and credential operations. 31 operations
   across three tags. This is the whole programmatic surface for these tasks in 9.0.
2. **VCF Operations `/suite-api/api/*`** — carries a `Certificate` tag and a `Credentials`
   tag, but **neither does what you probably want** (see the trap below).

The Broadcom documentation directs certificate management to the VCF Operations *console*
in 9.0 `[R-auth §3]`. That is a UI statement. At the API level in 9.0 the operations live
in SDDC Manager.

### Trap: VCF Operations `/api/credentials` is not password rotation

`GET/POST/PUT/PATCH /suite-api/api/credentials`, `GET /api/credentialkinds`,
`GET /api/credentials/{id}/adapters`, `GET /api/credentials/{id}/resources` all exist in
9.0 `[ops-spec 9.0]`. They manage **monitoring adapter credential instances** — the
`credential` schema's fields are `adapterKindKey`, `credentialKindKey`, `fields`
(name/value pairs), and the operation description reads *"Gets all the Credential
Instances in the system. Optionally filter by adapter kind keys."* Rotating a vCenter
root password is not this API. Use SDDC Manager `PATCH /v1/credentials`.

Similarly `GET/POST/DELETE /suite-api/api/certificate` `[ops-spec 9.0]` is the VCF
Operations appliance's own **trust store** (import a CA it should trust; `POST` takes
`multipart/form-data`; `DELETE` takes a `thumbprint` query parameter and an optional
`force`). It does not replace a component's serving certificate.

---

## Certificates — SDDC Manager, 9.0

All 17 operations below are confirmed present at `info.version` `9.0.0.0` `[spec 9.0]`.

### Certificate authority configuration

| Method | Path | operationId | Notes |
|---|---|---|---|
| GET | `/v1/certificate-authorities` | `getCertificateAuthorities` | 200, 500 |
| GET | `/v1/certificate-authorities/{id}` | `getCertificateAuthorityById` | `{id}` is *"The CA type"*, not a UUID |
| PUT | `/v1/certificate-authorities` | `createCertificateAuthority` | *"Creates a certificate authority. This is required to generate signed certificates by supporting CAs."* |
| PATCH | `/v1/certificate-authorities` | `configureCertificateAuthority` | Update existing config |
| DELETE | `/v1/certificate-authorities/{id}` | `removeCertificateAuthority` | *"Deletes CA configuration file"*, 204 |

Body for PUT and PATCH is `CertificateAuthorityCreationSpec`:

```json
{
  "openSSLCertificateAuthoritySpec": {
    "commonName": "OpenSSL CA", "country": "IN", "state": "Karnataka",
    "locality": "Bengaluru", "organization": "VMware Inc.", "organizationUnit": "VCF"
  }
}
```

or

```json
{
  "microsoftCertificateAuthoritySpec": {
    "username": "Administrator", "secret": "********",
    "serverUrl": "https://sfo-ad.rainpole.io/certsrv", "templateName": "WebServer"
  }
}
```

The schema description says *"Either openSSLCertificateAuthoritySpec or
microsoftCertificateAuthoritySpec should be specified."* All six OpenSSL fields are
required; all four Microsoft fields are required. `country` is `minLength`/`maxLength` 2.
`CertificateAuthority.id` example is `One among: OpenSSL, Microsoft, VMCA` — so `VMCA` is
a readable CA identity even though the `id` field's own description says *"Only supports
Microsoft and OpenSSL CAs"*. That contradiction is in the spec text itself.

### CSR generation

| Method | Path | operationId | Notes |
|---|---|---|---|
| PUT | `/v1/domains/{id}/csrs` | `generatesCSRs` | 202 → `Task`. 409 possible. |
| GET | `/v1/domains/{id}/csrs` | `getCSRs` | JSON |
| GET | `/v1/domains/{id}/csrs/downloads` | `downloadCSR` | **`deprecated: true` in 9.0** — tar.gz download. Use `getCSRs`. |

Body `CsrsGenerationSpec`:

```json
{
  "csrGenerationSpec": {
    "country": "IN", "state": "Karnataka", "locality": "Bengaluru",
    "organization": "VMware Inc.", "organizationUnit": "VCF",
    "email": "admin@vmware.com",
    "keySize": "2048", "keyAlgorithm": "RSA"
  },
  "resources": [
    { "resourceId": "BE8A5E04-92A0-43F6-A166-AA041F4327CC", "type": "VCENTER",
      "fqdn": "sfo-vc01.rainpole.io", "sans": ["sfo-vc01.rainpole.io"] }
  ]
}
```

Required in `CsrGenerationSpec`: `country`, `state`, `locality`, `organization`,
`organizationUnit`, `keySize`, `keyAlgorithm`. `email` is optional. `keySize` example is
`One among: 2048, 3072, 4096`; `keyAlgorithm` example is `One among: RSA` — both are typed
`string`, not enums, so the spec does not enforce them.

`Resource` requires `resourceId` and `type`. `type` example in 9.0:
`One among: SDDC_MANAGER, PSC, VCENTER, NSXT_MANAGER, VXRAIL_MANAGER, NSX_ALB, ESXI`.
Note `VXRAIL_MANAGER` — present in 9.0, gone in 9.1.

The operation description carries Broadcom's own warning verbatim: *"Avoid using wildcard
certificates. Instead, use subdomain-specific certificates that are rotated often. A
compromised wildcard certificate can lead to security repercussions."*

### Issue and install (CA-signed, via configured CA)

| Method | Path | operationId | Notes |
|---|---|---|---|
| PUT | `/v1/domains/{id}/certificates` | `generateCertificates` | *"CA must be configured and CSR must be generated beforehand."* 202 → `Task` |
| GET | `/v1/domains/{id}/certificates` | `getDomainCertificates` | *"Get latest generated certificate(s) in a domain."* |
| PATCH | `/v1/domains/{id}/certificates` | `replaceCertificates` | Installs. 202 → `Task` |

`CertificatesGenerationSpec` (body of `generateCertificates`) requires `caType`:

```json
{ "caType": "OpenSSL", "resources": [ { "resourceId": "...", "type": "VCENTER" } ], "validity": 398 }
```

`caType` example: `One among: OpenSSL, Microsoft, VMCA`. `validity` is int32 days,
example 398.

`CertificateOperationSpec` (body of `replaceCertificates`) requires `operationType`:

```json
{ "operationType": "INSTALL", "resources": [ { "resourceId": "...", "type": "VCENTER" } ] }
```

`operationType` example is `One among: INSTALL` — a single documented value.

### Import an externally signed certificate

| Method | Path | operationId | Notes |
|---|---|---|---|
| PUT | `/v1/domains/{id}/resource-certificates/validations` | `validateResourceCertificates` | 201. Body is an **array** of `ResourceCertificateSpec` |
| GET | `/v1/domains/{id}/resource-certificates/validations/{validationId}` | `getResourceCertificatesValidationByID` | Poll the validation |
| PUT | `/v1/domains/{id}/resource-certificates` | `replaceResourceCertificates` | 202. Body is an **array** of `ResourceCertificateSpec` |

`ResourceCertificateSpec` — no fields are marked required, but the schema description
constrains it: *"Either resourceId or resourceFqdn should be provided. Either
certificateChain or both resourceCertificate and caCertificate should be provided."*

```json
[
  {
    "resourceFqdn": "sfo-vc01.rainpole.io",
    "certificateChain": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
  }
]
```

Validate first, then replace. The validation endpoint exists precisely so you find out the
chain is wrong before you install it on a running appliance.

### Certificate inventory and auto-renewal

| Method | Path | operationId | Notes |
|---|---|---|---|
| GET | `/v1/domains/{id}/resource-certificates` | `getCertificatesByDomain` | *"View detailed metadata about the certificate(s) of all the resources in a domain."* Returns `PageOfCertificate`. **In 9.0 this operation takes no query parameters at all** — no paging, no filtering. |
| PATCH | `/v1/domains/{id}/resource-certificates` | `setAutoRenewConfigurationForDomain` | Body `DomainResourceCertificatesUpdateSpec`: `{"autoRenew": "ENABLE"}` — `One among: ENABLE, DISABLE` |
| PATCH | `/v1/domains/resource-certificates` | `setAutoRenewConfiguration` | All domains at once. Body `ResourceCertificatesUpdateSpec`: `autoRenew` plus optional `autoRenewTriggerTimeWindow` — *"the starting time of the 1-hour time window during which auto-renewal triggers every day. Time should be given in 24-hour format as HH:mm."* |

Auto-renewal fires *at the specified time or up to an hour later*, per that same field
description — daylight saving is called out explicitly. Do not schedule change freezes
against the exact minute.

### Trusted certificates (SDDC Manager's own trust store)

| Method | Path | operationId | Notes |
|---|---|---|---|
| GET | `/v1/sddc-manager/trusted-certificates` | `getTrustedCertificates` | *"Retrieve all trusted certificates from the appliance."* |
| POST | `/v1/sddc-manager/trusted-certificates` | `addTrustedCertificate` | 200, **409 = "Trusted certificate already exists"** |
| DELETE | `/v1/sddc-manager/trusted-certificates/{alias}` | `deleteTrustedCertificate` | 204 |

Body `TrustedCertificateSpec`:

```json
{ "certificate": "-----BEGIN CERTIFICATE-----\nMIIFq...\n-----END CERTIFICATE-----" }
```

`certificate` is the only required field. There is a second field
`certificateUsageType` (`One among: TRUSTED_FOR_OUTBOUND, TRUSTED_FOR_INBOUND`) marked
**`deprecated: true` already in 9.0** — do not send it.

`TrustedCertificate.alias` example shows the shape SDDC Manager generates:
`vcf_59:24:D5:18:...:90` — a `vcf_` prefix plus a thumbprint. You need that alias for the
DELETE.

The **same three operations, same paths, same operationIds** also exist in the VCF
Installer API at 9.0 `[spec 9.0, vcf-installer-openapi.json]`. If you are working
pre-SDDC-Manager, that is where they live.

---

## Credentials and password rotation — SDDC Manager, 9.0

All 11 operations below are confirmed present at `9.0.0.0` `[spec 9.0]`.

### Lookup

| Method | Path | operationId |
|---|---|---|
| GET | `/v1/credentials` | `getCredentials` |
| GET | `/v1/credentials/{id}` | `getCredential` |

`getCredentials` query parameters in 9.0: `resourceName`, `resourceIp`, `resourceType`,
`domainName`, `pageNumber`, `pageSize`, `accountType`. The `resourceType` parameter
description enumerates: `ESXI, VCENTER, PSC, NSXT_MANAGER, NSXT_EDGE, NSX_ALB, BACKUP`.

`Credential` fields: `id`, `credentialType` (`One among: SSO, SSH, API, FTP, AUDIT`),
`accountType` (`One among: USER, SYSTEM, SERVICE`), `username`, `password`,
`creationTimestamp`, `modificationTimestamp`, `expiry` (`ExpirationDetails`), `resource`
(`AuthenticatedResource`), `autoRotatePolicy` (`AutoRotateCredentialPolicy`:
`frequencyInDays` int32, `nextSchedule`).

**`password` is a readable field on the `Credential` schema.** Anyone who can call
`GET /v1/credentials` with the right role can read infrastructure passwords in plaintext
from the response. Role scoping matters here more than almost anywhere else in the API;
see `vcf-foundation` for the 9.0 per-product role model.

### Rotate, update, remediate

| Method | Path | operationId | Notes |
|---|---|---|---|
| PATCH | `/v1/credentials` | `updateOrRotatePasswords` | *"Update passwords for given list of resources by supplying new passwords or rotate the passwords using system generated passwords."* 202 → `CredentialsTask` |

Body `CredentialsUpdateSpec` — `operationType` and `elements` are required:

```json
{
  "operationType": "ROTATE",
  "elements": [
    {
      "resourceName": "sfo-vc01.rainpole.io",
      "resourceType": "VCENTER",
      "credentials": [ { "credentialType": "SSH", "username": "root" } ]
    }
  ]
}
```

`operationType` example: `One among: UPDATE, ROTATE, REMEDIATE, UPDATE_AUTO_ROTATE_POLICY`.

- **ROTATE** — SDDC Manager generates the new password. Omit `password`.
- **UPDATE** — you supply `password` in each `BaseCredential`.
- **REMEDIATE** — the documented path when SDDC Manager's stored credential and the
  component's actual credential have diverged. The spec names the value; **what REMEDIATE
  does mechanically is UNVERIFIED** — no fetched source describes the semantics.
- **UPDATE_AUTO_ROTATE_POLICY** — pair with the `autoRotatePolicy` object
  (`AutoRotateCredentialPolicyInputSpec`: `enableAutoRotatePolicy` required boolean,
  `frequencyInDays` int32).

`ResourceCredentials` requires `resourceType` and `credentials`. `BaseCredential` requires
only `username`.

### Track, retry, cancel

| Method | Path | operationId | Notes |
|---|---|---|---|
| GET | `/v1/credentials/tasks` | `getCredentialsTasks` | Query param `limit` |
| GET | `/v1/credentials/tasks/{id}` | `getCredentialsTask` | |
| GET | `/v1/credentials/tasks/{id}/subtasks/{subtaskId}` | `getCredentialsSubTask` | |
| GET | `/v1/credentials/tasks/{id}/resource-credentials` | `getCredentialTaskByResourceID` | |
| PATCH | `/v1/credentials/tasks/{id}` | `retryCredentialsTask` | Body is a `CredentialsUpdateSpec` again |
| DELETE | `/v1/credentials/tasks/{id}` | `cancelCredentialsTask` | *"Cancel a failed credential task by its ID."* 202 |

`CredentialsTask.status` example: `PENDING, IN_PROGRESS, SUCCESSFUL, FAILED,
USER_CANCELLED, INCONSISTENT`. `CredentialsTask.type` mirrors `operationType`.
`isAutoRotate` boolean tells you whether a task came from the schedule or from you.

**`INCONSISTENT` is the status that matters.** `CredentialsSubTask` exposes `oldPassword`
and `newPassword` per subtask — that pair is your recovery information when a rotation
half-completes and the appliance now has a password SDDC Manager does not think it has.
Read the subtasks before you retry.

Note both `cancelCredentialsTask` and `retryCredentialsTask` are described as operating on
a **failed** task. Neither is documented as a way to stop a running one.

### Expiration checking

| Method | Path | operationId | Notes |
|---|---|---|---|
| POST | `/v1/credentials/expirations` | `getPasswordExpiration` | 202 → task. Declares **429 Too many requests** |
| GET | `/v1/credentials/expirations/{id}` | `getPasswordExpirationByTaskID` | *"The expiration fetch workflow ID"* |

Body `CredentialsExpirationSpec` — `resourceType` required:

```json
{ "resourceType": "VCENTER", "domainName": "sfo-m01", "credentialIds": ["<uuid>"] }
```

This is a live probe, not a cache read: it is asynchronous and rate limited, which is what
you would expect from something that goes and asks each appliance.

---

## What is absent in 9.0

Stated so you do not carry 9.1 material backwards:

- **No `/api/fleet-management/certificate-management/*` and no
  `/api/fleet-management/password-management/*` in VCF Operations 9.0.** Verified by
  diffing the full path set of `vcf-operations-openapi.json` between the `9.0.0.0` and
  `9.1.0.0` tags: every one of those paths appears in the added set, none in the removed
  set. `[ops-spec 9.0 vs 9.1]`
- **No `/api/integrations/services/{certificate,password}-management/*`** (the VVF
  component surface). Same evidence.
- **No collector / collector-group / agent certificate renewal endpoints** in VCF
  Operations 9.0. Same evidence.
- **No `POST /v1/vcf-management-components/passwords`** in SDDC Manager 9.0.
  `[spec 9.0]`
- **No `GET /api/workflows/requests/{requestId}`** in VCF Operations 9.0 — there is no
  `WorkflowRequest` tracking surface because there are no workflows to track.
- **No bulk / multi-certificate operation.** The 9.1 documentation says bulk CSR, renew,
  import and replace start with VCF Operations 9.1 `[R-auth §3]`; the 9.0 doc set makes no
  such claim. Note however that SDDC Manager's `resources` arrays in `CsrsGenerationSpec`,
  `CertificatesGenerationSpec` and `CertificateOperationSpec` already accept multiple
  resources in 9.0 — "bulk" in the 9.1 release note refers to the VCF Operations surface,
  not to SDDC Manager.
- **No paging or filtering on `getCertificatesByDomain`.** The three query parameters
  9.1 adds are absent. `[spec 9.0]`

## Known unknowns for 9.0

- **Required role per operation is UNVERIFIED.** The 9.0 SDDC Manager spec declares no
  `securitySchemes` and no per-operation `security` block. Several credential operations
  declare `401` and `403`, so authorization is enforced — the spec just does not say by
  what. 9.0 has no fleet-level VCF role model to appeal to either `[R-auth §2]`. Determine
  empirically or from Broadcom's docs for the exact build.
- **The 409 conflict condition on the certificate operations is UNVERIFIED** (see
  prerequisite 5).
- **`REMEDIATE` semantics are UNVERIFIED.**
- **The 429 rate limit on `getPasswordExpiration` is UNVERIFIED** — no number published.
- **Whether certificate replacement invalidates live API tokens is UNVERIFIED.** The
  research dossier flags this as an inference, not a documented fact `[R-auth §3, pitfall
  4]`. Behave as if it does: reload trust bundles and re-authenticate after a rotation.
- **Which OS/JVM trust store `addTrustedCertificate` writes to is UNVERIFIED**
  `[R-auth §3]`.
