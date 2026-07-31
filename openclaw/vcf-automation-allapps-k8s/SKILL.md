---
name: vcf-automation-allapps-k8s
description: Work with VCF Automation "All Apps" organizations in VCF 9.0 and 9.1 — the Kubernetes/VCD-derived consumption surface — plus provider and organization administration. Covers CRDs under infrastructure.cci.vmware.com, the cci kubectl context, supervisor namespaces, projects, regions and quotas, and the provider REST conventions (URN ids, versioned media types, 202 plus Location). Use it when someone is creating or consuming supervisor namespaces with kubectl, asking which CCI CRD versions are served, or asking about 9.1 provider and org changes such as external IP blocks, vDefend delegation, self-service Avi, or multi-supervisor quota. Do not use it for blueprints, catalog items, deployments or cloud accounts — that is the VM Apps org type, a completely different API, covered by vcf-automation-vmapps. Do not use it for VKS cluster lifecycle, ClusterClass or Kubernetes releases — that is vks-supervisor. This product has no published OpenAPI spec, so the live cluster is the authority.
compatibility: Live discovery needs kubectl plus the VCF CLI and reachability to the VCF Automation endpoint. Reference material works offline, but is weaker evidence than the sibling skills — see below.
metadata:
  {
    "openclaw": {
      "requires": {
        "anyBins": [
          "curl",
          "kubectl",
          "vcf",
          "git"
        ]
      },
      "envVars": [
        {
          "name": "VCFA_ENDPOINT",
          "required": false,
          "description": "Optional: VCFA_ENDPOINT used in worked examples"
        },
        {
          "name": "VCF_CLI_VCFA_API_TOKEN",
          "required": false,
          "description": "Optional: VCF_CLI_VCFA_API_TOKEN used in worked examples"
        },
        {
          "name": "VCF_CLI_VSPHERE_PASSWORD",
          "required": false,
          "description": "Optional: VCF_CLI_VSPHERE_PASSWORD used in worked examples"
        }
      ]
    }
  }
---

# VCF Automation — All Apps organizations (Kubernetes surface)

This is the org type that is driven by Kubernetes custom resources rather than by
blueprints. If someone is talking about `kubectl`, supervisor namespaces, projects and
regions in VCF Automation, they are here. If they are talking about blueprints, catalog
items and deployments, they are in the *other* org type and belong in
`vcf-automation-vmapps` — the two share a product name and almost nothing else.

> **Built from documentation, not from a live environment.** Everything traces to
> Broadcom documentation captured 2026-07-31. Nothing has been executed against a running
> VCF deployment.

## Read this first — the evidence here is weaker than in the sibling skills

**There is no VCF Automation OpenAPI specification published at either the `9.0.0.0` or
the `9.1.0.0` tag of `github.com/vmware/vcf-api-specs`.** The machine-extracted spec
inventory used by `vcf-api-discovery` lists fifteen products across the two tags; VCF
Automation is not one of them. So the "check it against the spec" move that the other VCF
skills rely on is simply unavailable here.

Two consequences that shape every answer from this skill. **Every path, CRD and field in
the reference files is prose-sourced only**, and Broadcom TechDocs rate-limited (HTTP 429)
repeatedly during research, so several leaf pages were never retrieved — the gaps are
recorded as gaps, and should be passed through as gaps. And **the cluster is the
authority**: for anything CRD-shaped the running API server beats any document.

Every claim in the reference files carries one of these tags. Use them; do not upgrade a
claim's confidence in transit.

| Tag | Meaning |
|---|---|
| `[DOC-9.0]` | Read from a VCF 9.0 documentation page. |
| `[DOC-9.1]` | Read from a VCF 9.1 documentation page, or a developer-portal page that reported itself as 9.1/latest. |
| `[DOC-BOTH]` | Independently read in both doc sets. |
| `[UNVERIFIED]` | Not established by any retrieved page. Never present these as fact. |

## Step 1 — resolve the version, then read one file

Use the `vcf-foundation` skill to pin the version if you do not already know it.

| Target | Read |
|---|---|
| VCF 9.0 All Apps | `references/9.0/allapps.md` |
| VCF 9.1 All Apps | `references/9.1/allapps.md` |
| What changed between them | `references/deltas.md` |

The 9.0 file is thinner than the 9.1 file, and that asymmetry is real: the page
enumerating the CCI CRDs, the `cci` context and the permission matrix exists in the 9.1
doc set and was not retrieved for 9.0. Do not fill the 9.0 gap with 9.1 content.

## Step 2 — prerequisites, before any CRD or endpoint

Each version file opens with a prerequisite block, and here it does more work than usual
because the failure modes are structural rather than syntactic. Four in particular:

- **Which organization type you are in.** All Apps and VM Apps are different APIs. A
  request built for one returns nothing useful against the other, and the error will not
  say "wrong org type."
- **The supervisor namespace exists and is assigned** to the project you work in.
- **A region and a quota have been allocated** to the organization — without them a
  namespace creation has nowhere to land.
- **The `cci` kubectl context is established.** This is the login step, and in VCF 9.x it
  is not `kubectl vsphere login` — see the version files.

Each entry states what must be true, how to verify it, and whether the other version
differs.

## Step 3 — ask the cluster, don't trust the document

This is the one skill in the set where live discovery is the *primary* instruction rather
than a fallback. CRDs are self-describing and version-negotiated; documentation about them
goes stale silently.

```bash
kubectl --context cci api-resources --api-group=infrastructure.cci.vmware.com
kubectl --context cci get crd
kubectl --context cci explain supervisornamespace --recursive
kubectl --context cci get crd supervisornamespaces.infrastructure.cci.vmware.com \
  -o jsonpath='{.spec.versions[*].name}{"\n"}{.status.storedVersions}{"\n"}'
```

The last one is the point. **Check which versions are actually served and stored**, rather
than trusting a version string you read somewhere. `infrastructure.cci.vmware.com/v1alpha2`
is the documented group version `[DOC-9.1]`, with `v1alpha1` resources alongside it — but
"documented" and "served on this cluster" are different claims. There is a precedent for
exactly that gap elsewhere in the platform: VCF 9.0 docs put the VM Operator API at
`v1alpha2`/`v1alpha3` while the upstream project shows `v1alpha5`. Nobody is lying; the
document and the shipped cluster are on different clocks.

For the general method — and anything not in the reference files — use `vcf-api-discovery`.

## Step 4 — know which surface you are calling

Three surfaces, and they do not share conventions. Do not mix them: a URN is not a
Kubernetes name, and a CRD field is not a REST body field.

- **Kubernetes** — CRDs via `kubectl`, for projects, supervisor namespaces and regions.
- **Provider / All Apps REST** — URN identifiers, `application/json;version=9.1.0` content
  negotiation, `202` plus a `Location` header for async work, and a VMware Cloud Director
  header lineage (`x-vcloud-authorization`, now deprecated). `[DOC-9.1]`
- **Terraform** — treated as first-class by the docs: three providers, split by which
  surface owns the resource.

## The token endpoint gap — state it, do not close it

**The All Apps / provider token endpoint URL is not documented in anything retrieved.**
What *is* documented is the scheme: a JWT presented in the `Authorization` header, with
`x-vcloud-authorization` deprecated, plus the context headers
`X-VMWARE-VCLOUD-TENANT-CONTEXT` (org-scoped operations) and `X-VMWARE-VCLOUD-AUTH-CONTEXT`
(multisite). The Broadcom page titled "Generating an All Apps Access Token" returned 404
on every attempt.

So when someone asks how to authenticate to the All Apps API: give them the header
contract, say the issuing endpoint is not documented in the sources this skill was built
from, and point them at the in-product API Help Center on their own instance. **Do not
construct a plausible token URL.** The VM Apps flow uses a tenant-scoped OAuth path and
9.1 adds a fleet-wide identity-broker path; neither is confirmed as the issuer here, and
offering one as if it were is the likeliest way this skill produces a wrong answer that
looks right.

The same rule applies to base paths. The Aria-era IaaS base path people expect to find
here **was never confirmed on any 9.0 or 9.1 page**, and appears nowhere in these files.
If you are about to write one, you are guessing.

## A finding worth reporting: the provider API categories did not change

The 13 provider REST API categories are **identical in 9.0 and 9.1**. Worth stating for
two reasons. A research pass initially flagged two of them as "new in 9.1", and the claim
only died when someone diffed the 9.0 page against the 9.1 page and found both already
listed. And "we checked and nothing moved" is a genuinely useful answer for someone
planning an upgrade — the same class of finding as a delta, and worth saying rather than
dropping because it is dull.

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

### Version labeling stays, and stays short

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
