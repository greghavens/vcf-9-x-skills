---
name: vcf-certificates-credentials
description: "Certificate lifecycle and credential/password rotation as operational tasks in VMware Cloud Foundation 9.0 and 9.1 — generating CSRs, issuing, replacing and importing certificates, configuring a certificate authority and auto-renewal, managing trusted-CA trust stores, and looking up, rotating, updating or remediating passwords across managed components. Use this when the task is to perform the change: the SDDC Manager Certificates, Trusted Certificates and Credentials APIs, and the VCF Operations fleet certificate and password APIs that are new in 9.1. If instead a client is failing TLS verification and the question is how to trust a VCF certificate, or how to get a token at all, that is vcf-foundation — go there first and come back here once the task is changing a certificate or a password rather than trusting one."
compatibility: Requires network reachability to SDDC Manager and/or VCF Operations for live verification steps. Reference material, payload schemas and endpoint lookups work offline.
metadata:
  {
    "openclaw": {
      "requires": {
        "anyBins": [
          "git"
        ]
      },
      "envVars": [
        {
          "name": "SDDC_MANAGER",
          "required": false,
          "description": "Optional: SDDC_MANAGER used in worked examples"
        },
        {
          "name": "VCF_AUTOMATION",
          "required": false,
          "description": "Optional: VCF_AUTOMATION used in worked examples"
        },
        {
          "name": "VCF_CERTIFICATE_MANAGEMENT",
          "required": false,
          "description": "Optional: VCF_CERTIFICATE_MANAGEMENT used in worked examples"
        },
        {
          "name": "VCF_IAM",
          "required": false,
          "description": "Optional: VCF_IAM used in worked examples"
        },
        {
          "name": "VCF_OPERATIONS",
          "required": false,
          "description": "Optional: VCF_OPERATIONS used in worked examples"
        },
        {
          "name": "VCF_OPS_HCX",
          "required": false,
          "description": "Optional: VCF_OPS_HCX used in worked examples"
        },
        {
          "name": "VCF_OPS_NETWORK",
          "required": false,
          "description": "Optional: VCF_OPS_NETWORK used in worked examples"
        },
        {
          "name": "VCF_PASSWORD_MANAGEMENT",
          "required": false,
          "description": "Optional: VCF_PASSWORD_MANAGEMENT used in worked examples"
        },
        {
          "name": "VCF_SERVICES_RUNTIME",
          "required": false,
          "description": "Optional: VCF_SERVICES_RUNTIME used in worked examples"
        }
      ]
    }
  }
---

# VCF certificates and credentials: rotation as an operation

These are the highest-blast-radius APIs in VMware Cloud Foundation. A certificate
replacement or a password rotation touches the appliance you are authenticated to, and a
failed one can leave that appliance holding a credential the management plane does not
know about — locking you out of the thing you were maintaining. The recovery information
exists (`CredentialsSubTask` exposes `oldPassword` and `newPassword` per subtask), but it
only helps if you knew to look for it before you started.

> **Built from documentation and published OpenAPI specifications, not from a live
> environment.** Everything here traces to Broadcom documentation or to the
> `vmware/vcf-api-specs` repository at tags `9.0.0.0` and `9.1.0.0`, captured 2026-07-31.
> None of it has been executed against a running VCF deployment.

> **Before you propose a rotation or a replacement, say what it can break.** Rotating a
> credential invalidates the old one everywhere it is embedded — backup jobs, monitoring
> adapters, CI pipelines, other people's scripts. Replacing a certificate breaks every
> client that pinned the old one until it reloads. And in 9.1 the identity broker is
> itself under certificate management, which makes its certificate a single TLS point of
> failure for every SSO-federated client in the fleet. These are not reasons not to do it.
> They are reasons to have a route back in before you start.

## What this skill is not

Authentication itself belongs to `vcf-foundation`: token flows, header names, service
accounts, roles, and the fact that SDDC Manager is excluded from VCF SSO and needs its own
`/v1/tokens`. Do not restate any of that here — go get the token there, come back here to
use it.

The dividing line with `vcf-foundation` on certificates specifically:

| Question | Skill |
|---|---|
| "My script fails TLS verification against vCenter" | `vcf-foundation` |
| "How do I trust the VMCA root so my client stops erroring?" | `vcf-foundation` |
| "How do I replace vCenter's certificate with our enterprise CA's?" | **here** |
| "How do I rotate the ESX root passwords?" | **here** |
| "Which certificates expire in the next 30 days?" | **here** |
| "What role do I need to call the credentials API?" | `vcf-foundation` for the role model; UNVERIFIED per-operation here |

NSX has its own large `trust-management` certificate surface (CSRs, CRLs, CA bundles,
batch replace, appliance renewal). That is the NSX skill's, not this one's.

## Step 1 — resolve the version, then resolve the surface

Version first, always, via `vcf-foundation`. Then a second question that only exists in
this domain:

**9.0 has one surface. 9.1 has two.**

- **9.0** — SDDC Manager `/v1/*`. 31 operations across `Certificates`,
  `Trusted Certificates` and `Credentials`. That is the entire programmatic surface.
- **9.1** — the same 31 SDDC Manager operations, unchanged, *plus* a fleet certificate and
  password API in VCF Operations under `/suite-api/api/fleet-management/*` that did not
  exist in 9.0 at all.

Picking the wrong surface in 9.1 is the common failure. The rule of thumb:

- Appliances **inside a workload domain** — vCenter, NSX Manager, SDDC Manager, ESX —
  either surface works; SDDC Manager is the mature path.
- Appliances **outside** one — VCF Operations, VCF Automation, log management, VCF
  Operations for Networks, the identity broker, the AVI load balancer — **the 9.1 fleet API
  only**. SDDC Manager's resource types do not name them.
- **Rotation with a system-generated password** — SDDC Manager only. The fleet password API
  requires you to supply both `currentPassword` and `newPassword`; it will not invent one.

The version files carry the full decision table.

## Step 2 — check prerequisites before you write the call

Read the `## Prerequisites` block at the top of the version file. Each entry says what must
be true, how to verify it, and whether it exists in the other version. Four that decide
whether the call succeeds at all:

- **A CA must be configured and CSRs must exist** before issuance. The spec says so in the
  operation description itself: *"CA must be configured and CSR must be generated
  beforehand."* Verify with `GET /v1/certificate-authorities` and `GET /v1/domains/{id}/csrs`.
- **The target must be reachable and its current credential valid.** `ExpirationDetails`
  carries `connectivityStatus` (`ACTIVE`/`ERROR`/`UNKNOWN`). A credential in `ERROR` will
  not rotate. In 9.1 the same object gains `connectivityErrorDetails` telling you why —
  that field does not exist in 9.0.
- **No credential task in flight, and none sitting in `INCONSISTENT`.** Check
  `GET /v1/credentials/tasks` first. `INCONSISTENT` means a previous rotation
  half-completed; deal with that before starting another.
- **No conflicting certificate operation.** The three mutating certificate operations all
  declare `409 Conflict`. What exactly conflicts is not documented — treat 409 as "poll the
  previous task to completion first".

## Step 3 — read the version file, not both

| You need | Read |
|---|---|
| Certificates and credentials on 9.0 | `references/9.0/certs-and-credentials.md` |
| Certificates and credentials on 9.1 | `references/9.1/certs-and-credentials.md` |
| What actually changed between them | `references/deltas.md` |

Load one version file. Wanting both is a signal that step 1 is unfinished.

## What actually changed in 9.1 — and what did not

This one is worth carrying in your head, because the intuitive answer is wrong.

**The SDDC Manager certificate and credential APIs did not change.** Diffing the two specs
operation by operation: 31 operations in 9.0, 31 in 9.1, same paths, same methods, same
`operationId` values, nothing added, nothing removed, nothing newly deprecated. A 9.0
rotation script runs unmodified on 9.1.

What did change:

- **VCF Operations grew a fleet-wide certificate and password API.** 24 new operations
  across four new tags, none of which exist in 9.0. This is the change people mean when
  they say "certificate management changed in 9.1".
- **Failures became machine-readable.** 9.1 adds `ExpirationDetails.connectivityErrorDetails`
  and `Error.notifications[]` (severity, impact, remediation steps with links). Neither
  exists in 9.0, so guard the dereference.
- **`Task.status` gained `QUEUED` and `TIMED_OUT`.** A poll loop with a 9.0 terminal-status
  allowlist hangs on a timed-out 9.1 certificate task. `CredentialsTask.status` is a
  separate enum and did not change.
- **Resource types shifted**: `VXRAIL_MANAGER` dropped, `HCX_MANAGER` and `VSP` added.
- **`getCertificatesByDomain` gained paging** (`pageNumber`, `pageSize`) and
  `excludeResourceType`.
- **Two password *generator* endpoints appeared**, one in SDDC Manager and one in Fleet
  LCM. They hand you a compliant password; they do not apply it.

Full evidence, including the field-level diff and a migration checklist, is in
`references/deltas.md`.

## Where the documentation and the specs disagree

Broadcom's 9.1 page says you can *"generate certificate signing requests, renew, import,
and replace multiple certificates simultaneously"*. The 9.1 OpenAPI does not expose a bulk
certificate endpoint — `replaceCertificate` and `generateCsr` each take a single
`certificateId`. The only multi-target certificate operations in the spec are for *agent*
certificates.

Most likely the bulk capability is UI-only. It is not resolved. If someone asks for the
bulk REST call, tell them the doc claims it, the published spec does not carry it, and
point them at the UI or at SDDC Manager's `resources[]` arrays — which already accepted
multiple resources in 9.0.

Do not invent the endpoint. A plausible-looking certificate endpoint that does not exist is
indistinguishable from a real one until it fails in someone's change window.

## Honest reporting

Several things could not be verified from the sources and are marked UNVERIFIED in the
reference files: the required role per operation (neither spec declares security schemes),
what triggers the `409 Conflict`, what `REMEDIATE` does mechanically, the rate limit behind
the `429` on password-expiration checks, whether certificate replacement invalidates live
tokens, which trust store the import endpoints write to, whether the fleet API and the SDDC
Manager API write to the same state for the appliances both cover, and what `VSP` stands
for.

When you hit one, say so and give the lookup route. For this API family in particular,
"the docs don't publish this; here's how to confirm it against your appliance" is a much
better answer than a confident guess — the guess only reveals itself as wrong after
someone has run it against production credentials.

## When something here does not cover the case

Use `vcf-api-discovery` to confirm whether an endpoint exists for a specific version
rather than guessing one.

## Shaping your answer

### Answer the question that was asked, at the length it deserves

"Give me the exact API calls" means: give the calls. A numbered sequence of requests with
the payloads, and the two or three things that will actually bite. Not a runbook, not a
failure-mode table, not every caveat the reference file carries.

The reference material exists so your answer is *correct*, not so your answer is *long*.
Most of what you read should never appear in the reply. A useful test before sending:
would a VMware engineer who knows their environment skim this and find the command, or
would they have to hunt for it?

### Lead with the thing they asked for

Put the calls, the script, or the direct answer first. Context, prerequisites and
caveats come after, and only the ones that bear on this specific task.

If a prerequisite would actually cause the call to fail — the group doesn't exist yet,
the token type is wrong, the version gate isn't met — that belongs up top, because it
changes what they do next. A prerequisite that is merely true does not.

### Caveats: fewer, and where they matter

Every skill carries a documentation-not-live-validated caveat and a
destructive-operations warning. State them once, briefly, and place them where they bear
on the task rather than repeating them per section.

For a read-only query, one line is enough. For something that changes a production
firewall or starts an upgrade, say more — that is where the warning earns its space.
Uniform hedging on everything trains the reader to skip all of it, including the one that
mattered.

### Version labelling stays, and stays short

Say which version the answer applies to. Once, clearly, near the top. You do not need to
re-tag every line — the tags in the reference files are for you, not for the reply.

When evidence quality genuinely differs — a 9.1 endpoint confirmed in the spec versus a
9.0 endpoint sourced only from prose — say so in one sentence at the point it matters. A
user writing a change record needs that. A user prototyping does not need it five times.

### Length calibration

| They asked for | Give them |
|---|---|
| "the exact API calls" | The call sequence with payloads. Prereqs that would break it. Nothing else. |
| "write me a script" | The script, runnable. A short note on what to set. |
| "how do I find X" | The lookup route, and the answer if you found it. |
| "walk me through the upgrade" | The ordered steps with gates — this one legitimately runs long. |
| "is X true?" | Yes or no, then why. Two paragraphs, not ten. |
| A question with a false premise | Correct the premise first, briefly, then answer what they meant. |

When in doubt, answer short and offer the depth: "there's more on rollback and drafts if
you want it" costs one line and lets them pull rather than being pushed.
