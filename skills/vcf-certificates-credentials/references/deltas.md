# Certificates and credentials: what actually changed, 9.0 → 9.1

This file records a **machine diff**, not a summary of release notes. Everything in the
tables below was produced by comparing the OpenAPI documents at git tags `9.0.0.0` and
`9.1.0.0` of `vmware/vcf-api-specs` (cloned 2026-07-31), keyed on `(METHOD, path)` and on
`components.schemas` JSON. Where the published prose and the specs disagree, that is
recorded too — see [Where the docs and the specs disagree](#where-the-docs-and-the-specs-disagree).

## Contents

- [Headline](#headline)
- [SDDC Manager: operation set](#sddc-manager-operation-set)
- [SDDC Manager: field-level changes](#sddc-manager-field-level-changes)
- [VCF Operations: the actual change](#vcf-operations-the-actual-change)
- [Other specs](#other-specs)
- [Where the docs and the specs disagree](#where-the-docs-and-the-specs-disagree)
- [Migration checklist for existing 9.0 automation](#migration-checklist-for-existing-90-automation)

---

## Headline

**Nothing was added to or removed from the SDDC Manager `Certificates`, `Trusted
Certificates` or `Credentials` tags between 9.0 and 9.1.** Both versions carry the same 31
operations, with the same paths, the same methods and the same `operationId` values. The
one already-deprecated operation (`downloadCSR`) is still deprecated and still present.

The change is somewhere else entirely: **VCF Operations grew a fleet-wide certificate and
password API in 9.1 that did not exist in 9.0 at all.** If someone tells you "certificate
management changed in 9.1", this is what they mean, and it is not the API most people would
go looking at.

---

## SDDC Manager: operation set

| | 9.0.0.0 | 9.1.0.0 |
|---|---|---|
| Operations under `Certificates` | 17 | 17 |
| Operations under `Trusted Certificates` | 3 | 3 |
| Operations under `Credentials` | 11 | 11 |
| **Total** | **31** | **31** |
| Added | — | **0** |
| Removed | — | **0** |
| Newly deprecated | — | **0** (`downloadCSR` was already `deprecated: true` in 9.0) |

One related operation *was* added elsewhere in the SDDC Manager spec:

| Method | Path | operationId | Tag | Status |
|---|---|---|---|---|
| POST | `/v1/vcf-management-components/passwords` | `generatePassword` | `VCF Management Components` | **Added in 9.1** |

No request body; returns a bare JSON `string`; responses 200 / 403 / 500. Summary:
*"Generates a password that will be valid for all components."* It is a password
*generator*, not a rotation operation — it hands you a value, it does not apply one.

(For context: the SDDC Manager spec as a whole went 375 → 423 operations, 48 added, 0
removed, 21 newly deprecated. None of the 48 additions and none of the 21 deprecations fall
under the three tags in scope here, apart from `generatePassword` above. The deprecations
are edge clusters, DNS/NTP configuration and upgrade prechecks.)

---

## SDDC Manager: field-level changes

The operation set is frozen; the schemas are not. Diffing every schema transitively
reachable from the three tags (45 in 9.0, 48 in 9.1) turns up exactly this:

### Three schemas added

| Schema | Reached via | What it is |
|---|---|---|
| `ConnectivityErrorDetails` | `ExpirationDetails.connectivityErrorDetails` | `errorCode`, `arguments[]`, `errorMessage`, `remediationMessage`, `referenceToken`. Description: *"Detailed error information for connectivity failures"* |
| `ValidationNotification` | `Error.notifications[]` | `severity` (INFO/ERROR/WARNING), `message`, `impactMessage`, `remediations[]` |
| `Remediation` | `ValidationNotification.remediations[]` | `message` (*"Steps needed to perform remediation"*), `link` |

Practical effect: **failures became machine-readable in 9.1.** In 9.0, a credential whose
`connectivityStatus` was `ERROR` told you only that it was `ERROR`. In 9.1 the same object
carries a structured reason and a remediation string. Automation that classifies failures
should read `expiry.connectivityErrorDetails` and `Error.notifications[].remediations[]`
in 9.1 — neither field exists in 9.0, so a version check is needed before you dereference
them.

### Resource-type example values changed

Affects `Certificate.resourceType`, `Resource.type`, `AuthenticatedResource.resourceType`,
`ResourceCredentials.resourceType`, `CredentialsExpirationSpec.resourceType`, and the
`resourceType` query parameter on `getCredentials`.

| Family | 9.0 | 9.1 | Delta |
|---|---|---|---|
| Certificate resources | `SDDC_MANAGER, PSC, VCENTER, NSXT_MANAGER, VXRAIL_MANAGER, NSX_ALB, ESXI` | `SDDC_MANAGER, PSC, VCENTER, NSXT_MANAGER, NSX_ALB, ESXI, HCX_MANAGER, VSP` | **− `VXRAIL_MANAGER`**, **+ `HCX_MANAGER`**, **+ `VSP`** |
| Credential resources | `ESXI, VCENTER, PSC, NSXT_MANAGER, NSXT_EDGE, NSX_ALB, BACKUP` | `ESXI, VCENTER, PSC, NSXT_MANAGER, NSXT_EDGE, NSX_ALB, BACKUP, HCX_MANAGER, VSP` | **+ `HCX_MANAGER`**, **+ `VSP`** (nothing removed) |

These are OpenAPI `example` strings on `string`-typed fields, **not** `enum` constraints.
The spec will not reject a stale `VXRAIL_MANAGER` — the appliance may. `HCX_MANAGER`
tracks 9.1's absorption of HCX Manager deployment and upgrade into VCF Operations.
**`VSP` is not expanded anywhere in any fetched source — UNVERIFIED what it stands for.**

### Task status example values changed

Affects `Task.status` and the equivalent example on `Certificate`.

- 9.0: `PENDING, Pending, IN_PROGRESS, In Progress, SUCCESSFUL, Successful, FAILED, Failed, CANCELLED, Cancelled, COMPLETED_WITH_WARNING, SKIPPED`
- 9.1: same, **plus `QUEUED, TIMED_OUT, Queued, Timed Out`**

If you poll a certificate `Task` with a terminal-status allowlist built against 9.0, a 9.1
task that reaches `TIMED_OUT` will spin forever. `CredentialsTask.status` is a **separate**
enum and did **not** change: `PENDING, IN_PROGRESS, SUCCESSFUL, FAILED, USER_CANCELLED,
INCONSISTENT` in both versions.

### One operation gained query parameters

| Operation | 9.0 parameters | 9.1 parameters |
|---|---|---|
| `getCertificatesByDomain` — `GET /v1/domains/{id}/resource-certificates` | `id` (path) only | `id` (path), **`excludeResourceType`**, **`pageNumber`**, **`pageSize`** |

The response type was already `PageOfCertificate` in 9.0 — 9.0 just gave you no way to
drive the paging. `excludeResourceType` is described as *"Optional parameter to exclude a
specific resource type from the API response."* In a large estate the practical use is
`excludeResourceType=ESXI`, since ESX hosts dominate the certificate count.

### Everything else is unchanged

Byte-identical between the two tags: `CsrGenerationSpec`, `CsrsGenerationSpec`,
`CertificatesGenerationSpec`, `CertificateOperationSpec`, `ResourceCertificateSpec`,
`ResourceCertificatesUpdateSpec`, `DomainResourceCertificatesUpdateSpec`,
`CertificateAuthority`, `CertificateAuthorityCreationSpec`,
`OpenSSLCertificateAuthoritySpec`, `MicrosoftCertificateAuthoritySpec`,
`TrustedCertificate`, `TrustedCertificateSpec`, `Csr`, `Credential`, `BaseCredential`,
`CredentialsUpdateSpec`, `CredentialsTask`, `CredentialsSubTask`,
`AutoRotateCredentialPolicy`, `AutoRotateCredentialPolicyInputSpec`.

(The diff also surfaces cosmetic `readOnly` flag movements on the `PageOf*` wrappers,
`Csr` and `TrustedCertificate`. No field was added or removed by those; they are noise.)

---

## VCF Operations: the actual change

Spec-wide: 370 → 504 operations, **134 added, 0 removed**. Twenty-four of the additions
are certificate or password operations, and every one of them is genuinely new — none
appears in the 9.0 path set.

### New tags in 9.1

`Fleet Certificate Management`, `Fleet Password Management`, `Component Certificate
Management`, `Component Password Management`. None of the four exists in the 9.0 tag list.

### Added: fleet certificate management (7 operations)

| Method | Path | operationId |
|---|---|---|
| GET | `/api/fleet-management/certificate-management/certificate-authorities` | `getVcfCertificateAuthorities` |
| PUT | `/api/fleet-management/certificate-management/certificate-authorities` | `configureVcfCertificateAuthorities` |
| POST | `/api/fleet-management/certificate-management/certificates/query` | `getVcfCertificates` |
| GET | `/api/fleet-management/certificate-management/certificates/{certificateId}` | `getVcfCertificate` |
| PUT | `/api/fleet-management/certificate-management/certificates/{certificateId}` | `replaceCertificate` |
| GET | `/api/fleet-management/certificate-management/csrs` | `fetchCSRs` |
| POST | `/api/fleet-management/certificate-management/csrs` | `generateCsr` |

### Added: fleet password management (2 operations)

| Method | Path | operationId |
|---|---|---|
| POST | `/api/fleet-management/password-management/accounts/query` | `getVcfPasswordAccounts` |
| PUT | `/api/fleet-management/password-management/accounts/{passwordAccountKey}/password` | `updatePassword` |

### Added: component / VVF management (7 operations)

`getVVFCertificates`, `replaceVVFCertificate`, `getVVFCsrs`, `generateVVFCsr`,
`getVVFAccountList`, `updatePasswordSystem`, `getVvfTaskStatus` — all under
`/api/integrations/services/{certificate,password}-management/{serviceKey}/...`.

### Added: collector / agent certificate renewal (8 operations)

`renewClientsCertificate`, `getRenewClientsCertificateStatus`, `renewClientCertificate`,
`getRenewClientCertificateStatus`, `renewCollectorGroupCertificate`,
`getCollectorGroupCertificateRenewalStatus`, `renewCloudProxyCertificate`,
`getCollectorCertificateRenewStatus`.

### Added: workflow tracking

`GET /api/workflows/requests/{requestId}` → `getRequestById`, tag `Workflow Request`.
The fleet certificate and password operations return `WorkflowRequest` objects; before
9.1 there was no `WorkflowRequest` and nothing to track.

### The coverage widening this represents

The 9.1 `appliance` enums are the concrete evidence for what the fleet API reaches that
SDDC Manager's `Resource.type` does not:

`VCENTER, SDDC_MANAGER, NSXT_MANAGER, VCF_AUTOMATION, LOG_MANAGEMENT, VCF_OPERATIONS,
VCF_OPS_NETWORK, IDENTITY_BROKER, VCF_OPS_HCX, ESX, VCF_SERVICES_RUNTIME,
AVI_LOAD_BALANCER, UNKNOWN` (certificates; the password enum is the same plus `NSXT_EDGE`,
minus nothing).

**`IDENTITY_BROKER` in that list is the operationally significant one.** In 9.1 the VCF SSO
token issuer is itself a certificate-managed appliance. Every SSO-federated client trusts
it, so its certificate is a single TLS point of failure for fleet-wide authentication —
a concentration that 9.0's per-product auth did not have. The component coverage is
documented `[R-auth §3, S22]`; the "breaks every client at once" consequence is flagged
in the research as an **inference**, not a Broadcom statement `[R-auth §3, pitfall 5]`.
Say which is which.

### Unchanged in VCF Operations

`GET/POST/DELETE /api/certificate` (the appliance's own trust store) and the `/api/credentials`
family (monitoring adapter credential instances — **not** password rotation) are present and
identical in both versions.

---

## Other specs

| Spec | 9.0 | 9.1 | Relevant to this skill |
|---|---|---|---|
| `vcf-installer` | 52 ops | 57 ops (+5, −0) | The three `Trusted Certificates` operations are present and identical in both. None of the 5 additions is certificate- or credential-related. |
| `fleet-lcm` | **absent** | 51 ops | New spec. Contains `POST /v1/components/generated-passwords` → `generatePassword`, returning `GeneratedPasswordResponse` `{"generatedPassword": "..."}`. |
| `sddc-lcm` | **absent** | 26 ops | New spec. **No** certificate or credential operations. |
| `vcf-operations-for-logs` | 136 ops | **removed**; succeeded by `log-management` (23 ops) | The 9.0 spec had `/certificate`, `/certificates`, `/certificates/{thumbprint}`, `/trusted-certificates/{thumbprint}` and `PATCH /users/{userId}/password`. **The 9.1 `log-management` spec has none of them** — its 23 operations cover agent groups, agent secrets, ingest, extracted fields, log forwarders and query only. Log management certificates and passwords moved to the VCF Operations fleet API, where `LOG_MANAGEMENT` is an `appliance` enum value in both the certificate and password search requests. Its `Agent Secret` tag (`createAgentSecret`, `revokeAgentSecret`, `createAgentSession`) is agent enrolment, not appliance credential rotation. |
| `nsx-policy` / `nsx-manager` | absent as specs at 9.0 | present at 9.1 | NSX has its own large `trust-management` certificate surface (CSRs, CRLs, CA bundles, `BatchReplaceCertificates`, `RenewApplianceCertificates`). Out of scope here — go to the NSX skill. Their absence at the 9.0 tag is a spec-publication fact, not evidence that NSX 9.0 lacked the APIs. |

---

## Where the docs and the specs disagree

Two places. Both matter; do not paper over either.

### 1. "Bulk" certificate operations

Broadcom's 9.1 certificate management page states, verbatim: *"Starting with VCF
Operations 9.1, you can generate certificate signing requests, renew, import, and replace
multiple certificates simultaneously"* `[R-auth §3, S22]`.

The 9.1 OpenAPI does not carry a bulk certificate endpoint. `replaceCertificate` takes one
`certificateId`. `generateCsr` takes one `certificateId`. The only multi-target certificate
operations in the whole 9.1 VCF Operations spec are `renewClientsCertificate` and
`getRenewClientsCertificateStatus`, which take a `contextResourceIDs[]` array — and those
are for **agent** certificates, not appliance certificates.

Meanwhile SDDC Manager already accepted a `resources[]` array in `CsrsGenerationSpec`,
`CertificatesGenerationSpec` and `CertificateOperationSpec` **in 9.0**. So "multiple
certificates simultaneously" was not a new capability on that surface either.

Most likely reading: the bulk capability is a **VCF Operations UI feature**, and the
underlying REST surface is per-certificate. **This is not resolved.** If a user asks for a
bulk REST call, tell them the documentation claims the capability, the published spec does
not expose it, and point them at the UI or at SDDC Manager's `resources[]` arrays.

### 2. The `CertificateAuthority.id` description contradicts its own example

`CertificateAuthority.id` is described as *"CA type. Only supports Microsoft and OpenSSL
CAs"* while its example reads `One among: OpenSSL, Microsoft, VMCA`. Identical in both
versions. VMCA is the default signing CA at deployment `[R-auth §3]`, so it is plausibly
readable but not configurable. **Unresolved in the spec text itself.**

---

## Migration checklist for existing 9.0 automation

Ordered by how likely it is to bite.

1. **Terminal-status allowlists.** `Task.status` gained `QUEUED` and `TIMED_OUT` in 9.1.
   A poll loop that treats only the 9.0 values as terminal will hang on a timed-out
   certificate task. `CredentialsTask.status` is unaffected.
2. **`VXRAIL_MANAGER` no longer appears in 9.1 resource-type examples.** Audit any hard-
   coded resource type.
3. **New resource types exist.** If you enumerate resource types to build a work list,
   `HCX_MANAGER` and `VSP` will be missing from it.
4. **Paging on `getCertificatesByDomain`.** A 9.0 script reads the whole page. In 9.1 the
   parameters exist, and if anything upstream starts sending a default `pageSize` you will
   silently process a subset. Set it explicitly.
5. **New error detail is optional, not guaranteed.** `Error.notifications` and
   `ExpirationDetails.connectivityErrorDetails` are 9.1-only. Guard the dereference.
6. **Nothing in your 9.0 certificate or credential call sequence needs to change.**
   Paths, methods, operationIds and required fields are all identical. This is the rare
   API family where a 9.0 → 9.1 upgrade breaks nothing you already wrote.
7. **What you gain by rewriting** is fleet-wide visibility: one
   `POST /api/fleet-management/certificate-management/certificates/query` with
   `status: "EXPIRING_30"` replaces a loop over every domain, and it reaches appliances
   (VCF Operations, VCF Automation, the identity broker, the AVI load balancer) that the
   SDDC Manager API never covered.
