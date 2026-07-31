---
name: vsphere-content-tags-policies
description: "Manage vSphere content libraries (local, subscribed, published, library items, VM-template and OVF items), tags and tag categories, and storage policies including compliance, in VMware Cloud Foundation 9.0 and 9.1. Use this for \"create a content library\", \"publish or subscribe a library\", \"deploy from a library item\", \"create a category and tag a VM\", \"find everything tagged X\", \"check storage-policy compliance\", or \"attach a policy to a VM or disk\". It owns the surface split people get wrong: libraries and tags are on https://{host}/api, storage-policy read and compliance on /api/vcenter/storage/policies, but policy *authoring* exists only on the VI-JSON PBM surface at /sdk/vim25/{release}/pbm. Route VM provisioning, inventory traversal and vCenter 401/403 session failures to vsphere-inventory-vm-lifecycle; ESX host images, depots and cluster remediation to vsphere-lifecycle-vlcm."
compatibility: Requires network reachability to vCenter on 443 for live operations. Reference material works offline.
metadata:
  {
    "openclaw": {
      "requires": {
        "anyBins": [
          "curl",
          "jq",
          "git"
        ]
      }
    }
  }
---

# vSphere content library, tags and storage policies

Three features that look unrelated and are not: tags are how you express intent, storage
policies are how that intent becomes placement, and the content library is where the
templates that carry both live. The hard part is not any single call. It is that these
three sit on **four different path families across two API surfaces**, and one of them —
policy authoring — is not on `/api` at all.

> **Built from documentation, not from a live environment.** Everything traces to the
> published vSphere Automation OpenAPI specification (`vcenter.yaml`) or the VI-JSON
> specification (`vi-json.yaml`), git tags `9.0.0.0` and `9.1.0.0` of
> `github.com/vmware/vcf-api-specs`, captured **2026-07-31**. Nothing has been run against a
> live vCenter. **Deleting a library item removes content from the storage backing
> asynchronously, and changing a storage policy that is in use re-applies to every object
> bound to it** — resolve the target with a `GET` and check usage before executing either.

## Step 1 — settle the version

Use the `vcf-foundation` skill to resolve whether the target is VCF 9.0 or 9.1, then read
**only** that version's file.

| Target | Read |
|---|---|
| VCF 9.0 (vCenter 9.0.0.0) | `references/9.0/content-tags-policies.md` |
| VCF 9.1 (vCenter 9.1.0.0) | `references/9.1/content-tags-policies.md` |
| What changed between them | `references/deltas.md` |

Evidence is symmetric: both versions have a full machine-readable spec on both surfaces.
Every endpoint in the reference files carries the `operationId` it was matched on, and the
surface it belongs to. Hold any you add to the same standard.

## Four path families, two surfaces

| Concern | Surface | Base + path family | 9.0 ops | 9.1 ops |
|---|---|---|---|---|
| Content library | vSphere Automation | `https://{host}/api` + `/content/*` | 72 | 83 |
| Library items as VMs (deploy, check-out, OVF) | vSphere Automation | `/api/vcenter/vm-template/library-items/*`, `/api/vcenter/ovf/*` | 12 + 6 | 12 + 6 |
| Tags, categories, associations | vSphere Automation | `/api/cis/tagging/*` | 30 | 30 |
| Tag/category **lookup by name** | vSphere Automation | `/api/vcenter/tagging/*` | 3 | 4 |
| Storage policy **read + compliance** | vSphere Automation | `/api/vcenter/storage/policies*`, `/api/vcenter/vm/{vm}/storage/policy*` | 5 + 4 | 5 + 4 |
| Storage policy **authoring** | **VI-JSON** | `https://{host}/sdk/vim25/{release}` + `/pbm/*` | 33 | 33 |

All counts are machine-extracted from the ops inventories at each tag. Both surfaces take
the same session header, so this is a routing problem, not an auth problem.

## The three things people get wrong

**1. `/api/cis/tagging`, not `/api/cis-tagging`.** The Broadcom developer portal renders the
tagging group as `/api/cis-tagging/category`, `/api/cis-tagging/tag`,
`/api/cis-tagging/tag-association`, and the research dossier recorded those paths while
flagging the operation tables as unverified. **The specification declares them with a
slash**: `/cis/tagging/category`, `/cis/tagging/tag`, `/cis/tagging/tag-association`, under
`servers[0].url = https://{host}/api`, at both tags. `Cis.Tagging.Category` is the OpenAPI
tag, not a path segment. Where prose and spec disagree, follow the spec — and the dossier's
`UNVERIFIED` on the tag/category operation tables is now **resolved**: all 30 operations,
their verbs, their request bodies and their required fields are in the version files.

**2. You cannot create a storage policy on `/api`.** `/api/vcenter/storage/policies` has
exactly five operations and **none of them is a POST that creates a policy** — list,
check-compatibility, two compliance lists, and the per-policy VM list. Authoring is
`POST /sdk/vim25/{release}/pbm/PbmProfileProfileManager/{moId}/PbmCreate`, `PbmUpdate`,
`PbmDelete`. The PBM schemas even say so in their own descriptions: *"This structure may be
used only with operations rendered under `/pbm`."* If someone is hunting for
`POST /api/vcenter/storage/policies`, that is why they cannot find it.

**3. `/cis/tagging` list operations return bare identifiers.** `GET /api/cis/tagging/category`
and `GET /api/cis/tagging/tag` return, in the spec's own words, *"the list of resource
identifiers"* — a flat array of strings, with no names in it. To go from a display name to
an id, use `GET /api/vcenter/tagging/categories?names=…`
and `GET /api/vcenter/tagging/tags?names=…` (both *added in vSphere API 9.0.0.0*, so present
in both versions), which return `{category_id, info}` / `{tag, info}` pairs. Otherwise you
are listing every id and `GET`-ing each one.

## Prerequisites are the front half of the work

Each version file opens with a `## Prerequisites` block before any endpoint. Each item says
what must be true, **how to verify it non-destructively**, which version it applies to, and
whether it differs in the other. The ones that actually stop people:

- **A library needs a storage backing at create time.** `storage_backings` is *"must be
  provided for the `create` operation"*, and multiple backings raise `Unsupported`. A
  `DATASTORE` backing needs a resolved `datastore_id`; an `OTHER` backing needs a
  `storage_uri`. Nothing is created for you.
- **A tag needs its category first.** `Cis.Tagging.Tag.CreateSpec` requires `category_id`,
  and creating a tag against a category that does not exist is a **404**, not a 400.
- **Categories carry constraints that bite at attach time, not at create time.**
  `cardinality` (`SINGLE` | `MULTIPLE`) and `associable_types` are both *required* on
  category create, and the attach operation rejects a tag that *"does not meet the
  cardinality … and associability … criteria"* with a 400.
- **Publishing and subscribing are separate settings on separate endpoints.**
  `publish_info` is set on the local library; `subscription_info` on the subscribed one, and
  `subscription_url` plus credentials must be probed **before** you create, via
  `POST /api/content/subscribed-library?action=probe`.
- **Compliance is meaningless until a policy is attached.**
  `GET /api/vcenter/storage/policies/entities/compliance` states *"Entities without storage
  policy association are not returned"* — an empty result is ambiguous between "all clean"
  and "nothing attached". Check the binding with `GET /api/vcenter/vm/{vm}/storage/policy`
  first.

## Two compliance status enums, one letter apart

`Vcenter.Storage.Policies.Compliance.Status` is `COMPLIANT`, `NON_COMPLIANT`, **`UNKNOWN`**,
`NOT_APPLICABLE`, `OUT_OF_DATE`. `Vcenter.Storage.Policies.Compliance.VM.Status` and
`Vcenter.Vm.Storage.Policy.Compliance.Status` are the same list except the third value is
**`UNKNOWN_COMPLIANCE`**. Both `status` query parameters are **required**, and both are
validated — passing the wrong spelling gets you a 400 `InvalidArgument`, not an empty list.
The version files tag which enum belongs to which endpoint.

## Scope boundaries — where to send the question instead

| If the task is about | Use |
|---|---|
| Creating, cloning, powering, reconfiguring or deleting VMs; walking datacenters, clusters, hosts, datastores, networks, folders, resource pools | `vsphere-inventory-vm-lifecycle` |
| ESX host images, software drafts, depots, cluster remediation, configuration profiles (`/api/esx/settings/*`) | `vsphere-lifecycle-vlcm` |
| vSAN cluster configuration, disk groups, vSAN health, vSAN Data Protection | `vsan-storage` |
| Obtaining the credential itself — SSO, federation, token exchange | `vcf-foundation` |
| An operation none of these cover | `vcf-api-discovery` |

The boundary with `vsphere-inventory-vm-lifecycle` sits at one specific fork. Deploying from
a **content library VM template item** is
`POST /api/vcenter/vm-template/library-items/{templateLibraryItem}?action=deploy` — here.
Cloning a VM or template **already in inventory** is `POST /api/vcenter/vm?action=clone` —
there. And `GET·PATCH /api/vcenter/vm/{vm}/storage/policy` is documented in both: the
*binding* is a VM reconfigure, the *policy* is ours.

The boundary with `vsan-storage` is that vSAN storage policies **are** SPBM policies on the
same `/pbm` surface. That skill covers them from the vSAN side; this one covers the general
case. Neither invented a separate API.

## Auth, briefly — it belongs to `vcf-foundation`

Base is `https://{host}/api`. The session mechanism is a token sent as the
**`vmware-api-session-id`** header on every call; the VI-JSON `/pbm` surface takes the same
header. That is all this skill says about it — `vcf-foundation` owns credential acquisition,
federation and the 9.0 non-federated-login gate, and re-deriving it here would drift.

## When it isn't covered here

Confirm against the spec for the version in hand rather than extrapolating from a
neighbouring path. This area is *less* regular than it looks: `/content/library/{libraryId}`
has no `DELETE` at 9.0 but does at 9.1, `/content/local-library/{libraryId}` has one at
both, `/vcenter/tagging/*` is read-only at 9.0 and gains exactly one `PATCH` at 9.1, and the
tag-association operations are split across two path shapes depending on whether the tag id
is in the path or the body. An invented path here looks entirely plausible.

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
